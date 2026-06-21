#!/usr/bin/env python3
from __future__ import annotations

import argparse
from copy import copy
from datetime import datetime
from pathlib import Path
import sys
import time
from typing import Any

import pandas as pd

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
    PRS_RUNNER_SLICE_SOURCE_EXPORT_BLOCKED_STATUS,
    PRS_RUNNER_SLICE_SOURCE_EXPORT_EVENTS_FILENAME,
    PRS_RUNNER_SLICE_SOURCE_EXPORT_PASS_STATUS,
    PRS_RUNNER_SLICE_SOURCE_EXPORT_REPORT_FILENAME,
    PRS_RUNNER_SLICE_SOURCE_EXPORT_SOURCE_FILENAME,
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


ROUTE_SOURCE_REQUIRED_COLUMNS = (
    "particle_name",
    "particle_material",
    "wavelength_nm",
    "width_nm",
    "depth_nm",
)


def _default_output_dir() -> Path:
    stamp = datetime.now().strftime("%Y%m%d")
    return Path("results/audits") / f"nodi_position_response_runner_slice_source_{stamp}"


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
            "refusing to overwrite existing runner-slice source outputs; pass "
            "--overwrite-output only after confirming this is intentional:\n  - "
            + joined
        )
    for path in paths:
        if path.exists():
            path.unlink()


def _coerce_int_column(frame: pd.DataFrame, column: str) -> None:
    frame[column] = [int(float(value)) for value in frame[column].tolist()]


def validate_route_source_slice(
    route_source: Path,
    *,
    route: tuple[int, int, int],
    particle_name: str,
    particle_scope: str,
) -> dict[str, Any]:
    """Validate that a runner-compatible route-source contains the requested slice."""
    if particle_scope != "ev_gold":
        raise ValueError("only particle_scope=ev_gold is supported")
    if not route_source.exists():
        raise FileNotFoundError(f"route source does not exist: {route_source}")
    header = pd.read_csv(route_source, nrows=0)
    columns = set(str(column) for column in header.columns)
    missing = [column for column in ROUTE_SOURCE_REQUIRED_COLUMNS if column not in columns]
    if missing:
        raise ValueError(f"route source missing required columns: {missing}")
    optional_columns = ["particle_family"] if "particle_family" in columns else []
    frame = pd.read_csv(
        route_source,
        usecols=[*ROUTE_SOURCE_REQUIRED_COLUMNS, *optional_columns],
        low_memory=False,
    )
    for column in ("wavelength_nm", "width_nm", "depth_nm"):
        _coerce_int_column(frame, column)
    frame["particle_name"] = frame["particle_name"].astype(str)
    frame["particle_material"] = frame["particle_material"].astype(str)
    if "particle_family" in frame.columns:
        frame["particle_family"] = frame["particle_family"].astype(str)
    else:
        frame["particle_family"] = ""

    material_text = (
        frame["particle_material"].str.lower()
        + " "
        + frame["particle_name"].str.lower()
    )
    if material_text.str.contains("silver|\\bag\\b", regex=True).any():
        raise ValueError("Ag/silver rows are present, but source scope is EV + gold only")

    wavelength_nm, width_nm, depth_nm = route
    route_mask = (
        (frame["wavelength_nm"] == int(wavelength_nm))
        & (frame["width_nm"] == int(width_nm))
        & (frame["depth_nm"] == int(depth_nm))
    )
    if not bool(route_mask.any()):
        raise ValueError(f"route not found in route source: {wavelength_nm}/W{width_nm}/D{depth_nm}")
    particle_mask = frame["particle_name"] == str(particle_name)
    if not bool(particle_mask.any()):
        raise ValueError(f"particle not found in route source: {particle_name}")
    selected = frame[route_mask & particle_mask]
    if selected.empty:
        raise ValueError(
            f"route source lacks exact route/particle slice: "
            f"{wavelength_nm}/W{width_nm}/D{depth_nm} x {particle_name}"
        )
    selected_row = selected.iloc[0].to_dict()
    route_count = len(
        {
            (int(row[0]), int(row[1]), int(row[2]))
            for row in frame[["wavelength_nm", "width_nm", "depth_nm"]].itertuples(
                index=False,
                name=None,
            )
        }
    )
    particle_count = len(set(str(value) for value in frame["particle_name"].tolist()))
    return {
        "route_source_path": str(route_source),
        "route_source_sha256": sha256_file(route_source),
        "route_source_row_count": int(len(frame)),
        "route_source_unique_route_count": int(route_count),
        "route_source_unique_particle_count": int(particle_count),
        "route_source_exact_slice_row_count": int(len(selected)),
        "selected_particle_material": str(selected_row.get("particle_material", "")),
        "selected_particle_family": str(selected_row.get("particle_family", "")),
        "route_source_schema": "runner_compatible_slice_source_v1",
        "route_source_scope": (
            "selected_route_particle_slice_validated_no_fullgrid_coverage_claim"
        ),
    }


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
    raise ValueError(f"unsupported NODI view for runner-slice source export: {view}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export a bounded runner-compatible route/particle slice into PRS "
            "event rows and a bin-conditioned source candidate, then run source "
            "preflight only. This never generates production "
            "NODI_POSITION_RESPONSE_SURFACE rows, runs COMSOL, or regenerates "
            "JOINT_ROUTE_CLASS."
        ),
        epilog=(
            "Sidecars: "
            f"{PRS_RUNNER_SLICE_SOURCE_EXPORT_EVENTS_FILENAME}, "
            f"{PRS_RUNNER_SLICE_SOURCE_EXPORT_SOURCE_FILENAME}, "
            f"{PRS_RUNNER_SLICE_SOURCE_EXPORT_REPORT_FILENAME}."
        ),
    )
    parser.add_argument(
        "--confirm-runner-slice-event-source",
        action="store_true",
        help="Confirm running a bounded runner-slice event-source export.",
    )
    parser.add_argument("--route-source", type=Path, required=True)
    parser.add_argument("--particle-scope", choices=["ev_gold"], default="ev_gold")
    parser.add_argument("--output-dir", type=Path, default=_default_output_dir())
    parser.add_argument("--route", type=_parse_route, default=_parse_route("404/W500/D900"))
    parser.add_argument("--particle-name", default="exosome_biomimetic_corona_nominal_150nm")
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
        help="Allow replacing existing sidecars in the output directory.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_runner_slice_event_source:
        parser.error(
            "refusing runner-slice event-source export without "
            "--confirm-runner-slice-event-source"
        )
    if int(args.n_events) <= 0:
        parser.error("--n-events must be positive")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    event_path = output_dir / PRS_RUNNER_SLICE_SOURCE_EXPORT_EVENTS_FILENAME
    source_path = output_dir / PRS_RUNNER_SLICE_SOURCE_EXPORT_SOURCE_FILENAME
    report_path = output_dir / PRS_RUNNER_SLICE_SOURCE_EXPORT_REPORT_FILENAME
    _guard_output_paths(
        [event_path, source_path, report_path],
        allow_overwrite=bool(args.overwrite_output),
    )

    route = tuple(args.route)
    route_source_metadata = validate_route_source_slice(
        Path(args.route_source),
        route=route,
        particle_name=str(args.particle_name),
        particle_scope=str(args.particle_scope),
    )
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
            f"runner_slice_{wavelength_nm}_W{width_nm}_D{depth_nm}_"
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
        PRS_RUNNER_SLICE_SOURCE_EXPORT_PASS_STATUS
        if (
            not event_issues
            and not source_issues
            and preflight["status"] == PRS_SOURCE_PREFLIGHT_PASS_STATUS
        )
        else PRS_RUNNER_SLICE_SOURCE_EXPORT_BLOCKED_STATUS
    )
    decision_use_values = sorted({str(row["decision_use_allowed"]) for row in source_rows})
    sample_status_values = sorted({str(row["bin_sample_status"]) for row in source_rows})
    report = {
        "schema_version": "nodi_position_response_runner_slice_source_export_v1",
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
        **route_source_metadata,
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
        "decision_use_allowed_values": decision_use_values,
        "bin_sample_status_values": sample_status_values,
        "event_issues": event_issues,
        "source_issues": source_issues,
        "preflight_issues": preflight["issues"],
        "preflight_only": True,
        "bounded_nodi_runner_slice_source_export_performed": True,
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

    print(f"NODI_POSITION_RESPONSE_RUNNER_SLICE_SOURCE_EXPORT: {report['status']}")
    print(f"event_rows: {report['nodi_event_rows']}")
    print(f"bin_source_rows: {report['bin_source_rows']}")
    print(f"source_scope: {report['source_scope']}")
    print(f"route_source_path: {report['route_source_path']}")
    print(f"route_source_sha256: {report['route_source_sha256']}")
    print(f"route_source_exact_slice_row_count: {report['route_source_exact_slice_row_count']}")
    print(f"source_preflight_status: {report['source_preflight_status']}")
    print(
        "source_available_candidate_count: "
        f"{report['source_available_candidate_count']}"
    )
    print(f"decision_use_allowed_values: {','.join(report['decision_use_allowed_values'])}")
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
    return 0 if status == PRS_RUNNER_SLICE_SOURCE_EXPORT_PASS_STATUS else 1


if __name__ == "__main__":
    raise SystemExit(main())
