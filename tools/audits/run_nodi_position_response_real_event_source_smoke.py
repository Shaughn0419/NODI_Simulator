#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import copy
from datetime import datetime
from pathlib import Path
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.config import (  # noqa: E402
    THETA_GRID_RAD,
    infer_particle_diameter_nm,
    medium_for_particle,
    particle_from_name,
)
from nodi_simulator.nodi_comsol_next_artifacts import (  # noqa: E402
    POSITION_RESPONSE_BIN_SOURCE_ARTIFACT,
    PRS_REAL_EVENT_SOURCE_SMOKE_EVENTS_FILENAME,
    PRS_REAL_EVENT_SOURCE_SMOKE_PASS_STATUS,
    PRS_REAL_EVENT_SOURCE_SMOKE_REPORT_FILENAME,
    PRS_REAL_EVENT_SOURCE_SMOKE_SOURCE_FILENAME,
    PRS_REAL_EVENT_SOURCE_SMOKE_BLOCKED_STATUS,
    PRS_SOURCE_PREFLIGHT_PASS_STATUS,
    PRS_SOURCE_PRODUCTION_SCOPE,
    build_position_response_bin_source_rows_from_events,
    build_position_response_event_rows_from_nodi_events,
    validate_position_response_bin_source_event_rows,
    validate_position_response_bin_source_rows,
    write_position_response_source_preflight_bundle,
)
from nodi_simulator.parameter_sweep import run_single_case_batch  # noqa: E402
from nodi_simulator.realism_v2_io import (  # noqa: E402
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)
from tools.audits import tsuyama_gold_aligned_detection_lane as lane  # noqa: E402
from tools.lens_b_ev_gold_fullgrid_runner import (  # noqa: E402
    SINGLE_NORMALIZATION_LANES,
    build_frozen_b_cfg,
    _cfg_for_normalization_lane,
    _fixed_660_e_sca_ref,
    _per_wavelength_e_sca_ref,
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return Path("results/audits") / f"nodi_position_response_real_event_source_smoke_{stamp}"


def _parse_route(value: str) -> tuple[int, int, int]:
    try:
        wavelength_part, width_part, depth_part = value.split("/")
        return (
            int(wavelength_part),
            int(width_part.removeprefix("W")),
            int(depth_part.removeprefix("D")),
        )
    except Exception as exc:
        raise argparse.ArgumentTypeError(
            "route must look like 404/W500/D900"
        ) from exc


def _guard_output_paths(paths: list[Path], *, allow_overwrite: bool) -> None:
    existing = [str(path) for path in paths if path.exists()]
    if existing and not allow_overwrite:
        joined = "\n  - ".join(existing)
        raise FileExistsError(
            "refusing to overwrite existing real-event source smoke outputs; "
            "pass --overwrite-output only after confirming this is intentional:\n  - "
            + joined
        )
    for path in paths:
        if path.exists():
            path.unlink()


def _resolve_e_sca_ref(
    *,
    view: str,
    route: tuple[int, int, int],
    particle: Any,
    cfg: Any,
    optical_template: Any,
) -> float:
    wavelength_nm, width_nm, depth_nm = route
    if view == "fixed_660_gold":
        return _fixed_660_e_sca_ref(
            width_nm=width_nm,
            depth_nm=depth_nm,
            cfg=cfg,
            optical_template=optical_template,
        )
    if view == "per_wavelength_gold":
        return _per_wavelength_e_sca_ref(
            wavelength_nm=wavelength_nm,
            width_nm=width_nm,
            depth_nm=depth_nm,
            medium=medium_for_particle(particle),
            cfg=cfg,
            optical_template=optical_template,
        )
    raise ValueError(f"unsupported NODI view for real-event source smoke: {view}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a bounded real NODI single-case event export smoke, convert the "
            "slim event payload to PRS event rows, build a bin-conditioned source "
            "candidate, and run source preflight only. This never generates "
            "production NODI_POSITION_RESPONSE_SURFACE rows, runs COMSOL, or "
            "regenerates JOINT_ROUTE_CLASS."
        ),
        epilog=(
            "Sidecars: "
            f"{PRS_REAL_EVENT_SOURCE_SMOKE_EVENTS_FILENAME}, "
            f"{PRS_REAL_EVENT_SOURCE_SMOKE_SOURCE_FILENAME}, "
            f"{PRS_REAL_EVENT_SOURCE_SMOKE_REPORT_FILENAME}."
        ),
    )
    parser.add_argument(
        "--confirm-real-event-source-smoke",
        action="store_true",
        help="Confirm running a bounded NODI event-source smoke and writing sidecars.",
    )
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    parser.add_argument("--route", type=_parse_route, default=_parse_route("404/W500/D900"))
    parser.add_argument("--particle-name", default="exosome_150nm")
    parser.add_argument("--n-events", type=int, default=6)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument(
        "--NODI-view",
        choices=SINGLE_NORMALIZATION_LANES,
        default="fixed_660_gold",
    )
    parser.add_argument(
        "--overwrite-output",
        action="store_true",
        help="Allow replacing existing smoke sidecars in the output directory.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_real_event_source_smoke:
        parser.error(
            "refusing real-event source smoke without "
            "--confirm-real-event-source-smoke"
        )
    if int(args.n_events) <= 0:
        parser.error("--n-events must be positive")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    event_path = output_dir / PRS_REAL_EVENT_SOURCE_SMOKE_EVENTS_FILENAME
    source_path = output_dir / PRS_REAL_EVENT_SOURCE_SMOKE_SOURCE_FILENAME
    report_path = output_dir / PRS_REAL_EVENT_SOURCE_SMOKE_REPORT_FILENAME
    _guard_output_paths(
        [event_path, source_path, report_path],
        allow_overwrite=bool(args.overwrite_output),
    )

    route = tuple(args.route)
    wavelength_nm, width_nm, depth_nm = route
    particle = particle_from_name(str(args.particle_name))
    diameter_nm = infer_particle_diameter_nm(str(args.particle_name))
    if diameter_nm is None:
        raise ValueError(f"cannot infer diameter_nm from {args.particle_name}")

    started = time.perf_counter()
    base_cfg, optical_template = build_frozen_b_cfg(args.n_events, args.seed)
    cfg = _cfg_for_normalization_lane(base_cfg, str(args.NODI_view))
    optical = copy(optical_template)
    optical.wavelength_m = float(wavelength_nm) * 1e-9
    channel = lane.case_baseline_channel(width_nm, depth_nm)
    e_sca_ref = _resolve_e_sca_ref(
        view=str(args.NODI_view),
        route=route,
        particle=particle,
        cfg=cfg,
        optical_template=optical_template,
    )

    batch = run_single_case_batch(
        particle,
        medium_for_particle(particle),
        channel,
        optical,
        cfg,
        e_sca_ref,
        THETA_GRID_RAD,
        retain_event_traces=False,
        stream_summary_only=False,
    )
    event_rows = build_position_response_event_rows_from_nodi_events(
        batch["events"],
        route=route,
        diameter_nm=int(diameter_nm),
        view=str(args.NODI_view),
        seed=int(args.seed),
        particle_kind=str(args.particle_name),
        source_scope=PRS_SOURCE_PRODUCTION_SCOPE,
        event_id_prefix=(
            f"nodi_{wavelength_nm}_W{width_nm}_D{depth_nm}_"
            f"D{int(diameter_nm)}_{args.NODI_view}_seed{int(args.seed)}"
        ),
    )
    event_issues = validate_position_response_bin_source_event_rows(event_rows)
    write_csv_rows(event_path, event_rows)
    source_rows = build_position_response_bin_source_rows_from_events(
        event_rows,
        source_scope=PRS_SOURCE_PRODUCTION_SCOPE,
        source_artifact=str(event_path),
        source_sha256=sha256_file(event_path),
    )
    source_issues = validate_position_response_bin_source_rows(source_rows)
    write_csv_rows(source_path, source_rows)
    preflight = write_position_response_source_preflight_bundle(
        candidate_paths=[source_path],
        output_dir=output_dir,
    )

    status = (
        PRS_REAL_EVENT_SOURCE_SMOKE_PASS_STATUS
        if (
            not event_issues
            and not source_issues
            and preflight["status"] == PRS_SOURCE_PREFLIGHT_PASS_STATUS
        )
        else PRS_REAL_EVENT_SOURCE_SMOKE_BLOCKED_STATUS
    )
    report = {
        "schema_version": "nodi_position_response_real_event_source_smoke_v1",
        "status": status,
        "artifact": POSITION_RESPONSE_BIN_SOURCE_ARTIFACT,
        "route_id_nodi": f"{wavelength_nm}/W{width_nm}/D{depth_nm}",
        "diameter_nm": int(diameter_nm),
        "NODI_view": str(args.NODI_view),
        "seed": int(args.seed),
        "particle_kind": str(args.particle_name),
        "nodi_event_rows": len(event_rows),
        "bin_source_rows": len(source_rows),
        "source_scope": PRS_SOURCE_PRODUCTION_SCOPE,
        "event_source_path": str(event_path),
        "event_source_sha256": sha256_file(event_path),
        "bin_source_path": str(source_path),
        "bin_source_sha256": sha256_file(source_path),
        "source_preflight_status": preflight["status"],
        "source_preflight_report_path": preflight["report_path"],
        "source_preflight_report_sha256": preflight["report_sha256"],
        "source_available_candidate_count": preflight[
            "source_available_candidate_count"
        ],
        "event_issues": event_issues,
        "source_issues": source_issues,
        "preflight_issues": preflight["issues"],
        "preflight_only": True,
        "bounded_nodi_single_case_smoke_performed": True,
        "full_runner_execution_performed": False,
        "position_response_surface_production_generated": False,
        "production_generation_performed": False,
        "comsol_run_performed": False,
        "joint_route_class_regenerated": False,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_winner": True,
        "not_detection_probability": True,
        "elapsed_s": time.perf_counter() - started,
    }
    write_json_atomic(report_path, report, sort_keys=True)
    report["report_path"] = str(report_path)
    report["report_sha256"] = sha256_file(report_path)

    print(f"NODI_POSITION_RESPONSE_REAL_EVENT_SOURCE_SMOKE: {report['status']}")
    print(f"event_rows: {report['nodi_event_rows']}")
    print(f"bin_source_rows: {report['bin_source_rows']}")
    print(f"source_scope: {report['source_scope']}")
    print(f"source_preflight_status: {report['source_preflight_status']}")
    print(
        "source_available_candidate_count: "
        f"{report['source_available_candidate_count']}"
    )
    print(f"event_source_path: {report['event_source_path']}")
    print(f"event_source_sha256: {report['event_source_sha256']}")
    print(f"bin_source_path: {report['bin_source_path']}")
    print(f"bin_source_sha256: {report['bin_source_sha256']}")
    print(f"report_path: {report['report_path']}")
    print(f"report_sha256: {report['report_sha256']}")
    print(f"source_preflight_report_path: {report['source_preflight_report_path']}")
    print(f"source_preflight_report_sha256: {report['source_preflight_report_sha256']}")
    for issue in [*event_issues, *source_issues, *preflight["issues"]]:
        print(f"- issue: {issue}")
    return 0 if status == PRS_REAL_EVENT_SOURCE_SMOKE_PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
