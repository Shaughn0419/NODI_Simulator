#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.cross_section_geometry import (  # noqa: E402
    TrapezoidCrossSection,
    comsol_sidewall_deg_to_nodi_taper_deg,
)
from nodi_simulator.nodi_comsol_next_artifacts import (  # noqa: E402
    PRS_APPROVED_DIAMETERS_NM,
    PRS_APPROVED_ROUTE_MATRIX,
)
from nodi_simulator.realism_v2_io import (  # noqa: E402
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)
from tools.audits.build_nodi_sidewall_bounded_event_shards import (  # noqa: E402
    execute_shard_row,
    m_to_nm,
    nm_to_m,
)


DATE_STAMP = "20260702"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_PRIMARY85_FULL_BOUNDED_EVENT_EXPANSION"
ARTIFACT_ID = "NODI_SIDEWALL_PRIMARY85_FULL_BOUNDED_EVENT_EXPANSION_20260702"
EXPANSION_VERSION = "sidewall_primary85_full_bounded_event_expansion_v1"
DISPOSITION_EXECUTED = "NODI_SIDEWALL_PRIMARY85_FULL_BOUNDED_EVENT_EXPANSION_EXECUTED_READY"
DISPOSITION_PLAN = "NODI_SIDEWALL_PRIMARY85_FULL_BOUNDED_EVENT_EXPANSION_PLAN_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_PRIMARY85_FULL_BOUNDED_EVENT_EXPANSION_FAIL_CLOSED"
CLAIM_BOUNDARY = "full_primary85_bounded_event_context_not_probability_not_selection"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
THETA_PAIR_DEG_COMSOL = (90.0, 85.0)
DEFAULT_N_EVENTS = 2
DEFAULT_RANDOM_SEED = 59500

SOURCE_FILES = {
    "dimension_update_status_594": OUTPUT_DIR
    / "NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET_STATUS_20260702.json",
    "dimension_update_rows_594": OUTPUT_DIR
    / "NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET_ROUTE_DIAMETER_UPDATE_ROWS_20260702.csv",
    "base_bounded_runner_591": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_bounded_event_shards.py",
    "full_bounded_expansion_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_primary85_full_bounded_event_expansion.py",
    "full_bounded_expansion_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_primary85_full_bounded_event_expansion.py",
}

ALLOWED_USE = (
    "execute sparse full-coverage NODI bounded event context for PRS-approved "
    "routes and diameters under rectangle/85deg sidewall pairing"
)
BLOCKED_USE = (
    "production PRS, route winner, scalar score, final detection probability, "
    "yield, wet claim, fabrication release, q_ch weighting, true W_eff, or "
    "production runtime ingestion"
)
FORBIDDEN_PRIMARY_COLUMNS = {
    "winner",
    "route_score",
    "rank",
    "detection_probability",
    "yield",
    "W_eff",
    "q_ch_eta",
    "rank_under_surrogate",
    "not_route_score",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build/execute full primary-85 sidewall bounded event expansion."
    )
    parser.add_argument(
        "--confirm-sidewall-primary85-full-bounded-event-expansion",
        action="store_true",
    )
    parser.add_argument("--execute-nodi", action="store_true")
    parser.add_argument("--n-events", type=int, default=DEFAULT_N_EVENTS)
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_SEED)
    return parser


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={PROJECT_ROOT.as_posix()}", *args],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def git_head() -> str:
    return run_git(["rev-parse", "HEAD"])


def git_branch() -> str:
    return run_git(["branch", "--show-current"])


def git_status_lines() -> list[str]:
    out = run_git(["status", "--short"])
    return [line for line in out.splitlines() if line.strip()]


def git_path_from_status_line(line: str) -> str:
    return line[2:].strip().replace("\\", "/") if len(line) > 2 else line


def display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def route_id(lambda_nm: int, width_nm: int, depth_nm: int) -> str:
    return f"{int(lambda_nm)}/W{int(width_nm)}/D{int(depth_nm)}"


def route_case_id(lambda_nm: int, width_nm: int, depth_nm: int) -> str:
    return route_id(lambda_nm, width_nm, depth_nm).replace("/", "_")


def common_fields(row_id: str) -> dict[str, Any]:
    return {
        "expansion_version": EXPANSION_VERSION,
        "row_id": row_id,
        "source_artifacts_json": json.dumps(
            [
                "594_NODI_SIDEWALL_RECOMMENDED_DIMENSION_UPDATE_PACKET_20260702",
                "591_bounded_event_runner",
                "PRS_APPROVED_ROUTE_MATRIX",
                "PRS_APPROVED_DIAMETERS_NM",
            ],
            sort_keys=True,
        ),
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "not_detection_probability": True,
        "not_yield": True,
        "not_selection_metric_claim": True,
        "not_winner": True,
        "not_qch_weighted": True,
        "not_true_W_eff": True,
        "not_production_prs": True,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def source_lock_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id, path in SOURCE_FILES.items():
        exists = path.exists()
        rows.append(
            {
                "source_id": source_id,
                "path": display_path(path) if exists else str(path),
                "exists": str(exists).lower(),
                "sha256": sha256_file(path) if exists else "",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def dirty_context_rows() -> list[dict[str, str]]:
    output_prefix = f"reports/joint_interface_{DATE_STAMP}/{PREFIX}_"
    output_report = f"reports/595_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_primary85_full_bounded_event_expansion.py",
        "tests/test_nodi_sidewall_primary85_full_bounded_event_expansion.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "primary85_full_bounded_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "primary85_full_bounded_output"
            release_decision = "included_or_rewritten_by_primary85_full_bounded_builder"
        else:
            classification = "non_primary85_full_bounded_dirty_context"
            release_decision = "ignored_for_primary85_full_bounded"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def plan_rows(
    *,
    n_events: int = DEFAULT_N_EVENTS,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    routes = sorted(PRS_APPROVED_ROUTE_MATRIX)
    diameters = sorted(PRS_APPROVED_DIAMETERS_NM)
    for route_index, (lambda_nm, width_nm, depth_nm) in enumerate(routes):
        for theta in THETA_PAIR_DEG_COMSOL:
            geometry = TrapezoidCrossSection(
                top_width_m=nm_to_m(width_nm),
                depth_m=nm_to_m(depth_nm),
                sidewall_taper_angle_deg=comsol_sidewall_deg_to_nodi_taper_deg(theta),
            )
            for diameter_nm in diameters:
                seed = int(
                    random_seed
                    + route_index * 1000
                    + int(theta) * 10
                    + int(diameter_nm)
                )
                row_id = (
                    f"FULL-{route_case_id(lambda_nm, width_nm, depth_nm)}-"
                    f"TH{theta:g}-P{diameter_nm}"
                )
                rows.append(
                    {
                        **common_fields(row_id),
                        "shard_case_id": row_id,
                        "route_id_nodi": route_id(lambda_nm, width_nm, depth_nm),
                        "route_id_nodi_role": "join_key_only_not_selection",
                        "lambda_nm": int(lambda_nm),
                        "W_nominal_nm": int(width_nm),
                        "W_top_nm": int(width_nm),
                        "W_top_semantics": "runtime_top_aperture_surrogate",
                        "D_nm": int(depth_nm),
                        "depth_nm": int(depth_nm),
                        "diameter_nm": int(diameter_nm),
                        "particle_model": "gold_baseline_material_model",
                        "channel_cross_section_model": "ideal_rectangle"
                        if math.isclose(theta, 90.0)
                        else "trapezoid_tapered_sidewalls",
                        "sidewall_angle_convention": "comsol_from_horizontal",
                        "sidewall_deg_comsol": float(theta),
                        "sidewall_taper_angle_deg_nodi": (
                            comsol_sidewall_deg_to_nodi_taper_deg(theta)
                        ),
                        "W_bottom_unclipped_nm": m_to_nm(
                            geometry.bottom_width_unclipped_m
                        ),
                        "W_bottom_runtime_clipped_nm": m_to_nm(
                            geometry.bottom_width_runtime_clipped_m
                        ),
                        "closure_status": geometry.closure_status,
                        "n_events_requested": int(n_events),
                        "random_seed": seed,
                        "reference_model": "trapezoid_effective_aperture_surrogate",
                        "reference_spatial_mode": "cross_section_surrogate",
                        "flow_profile_model": "plug",
                        "diffusion_hindrance_model": "none",
                        "readout_preset": "tsuyama_2022_counting_10sigma",
                        "execution_status": "planned_not_executed",
                    }
                )
    return rows


def event_rows(*, execute_nodi: bool, n_events: int, random_seed: int) -> list[dict[str, Any]]:
    rows = plan_rows(n_events=n_events, random_seed=random_seed)
    if not execute_nodi:
        return rows
    executed_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        print(f"[primary85-full] {index}/{len(rows)} {row['shard_case_id']}", flush=True)
        executed_rows.append(execute_shard_row(row))
    return executed_rows


def paired_delta_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lookup = {
        (
            row["route_id_nodi"],
            int(row["diameter_nm"]),
            float(row["sidewall_deg_comsol"]),
        ): row
        for row in rows
    }
    deltas: list[dict[str, Any]] = []
    for route, diameter_nm, theta in sorted(lookup):
        if not math.isclose(theta, 85.0):
            continue
        rectangle = lookup.get((route, diameter_nm, 90.0))
        sidewall = lookup[(route, diameter_nm, theta)]
        if rectangle is None:
            continue
        row_id = f"FULL-DELTA-{route.replace('/', '_')}-P{diameter_nm}-TH85_vs_TH90"

        def delta(field: str) -> float | str:
            left = rectangle.get(field)
            right = sidewall.get(field)
            if left in {"", None} or right in {"", None}:
                return ""
            try:
                return float(right) - float(left)
            except (TypeError, ValueError):
                return ""

        deltas.append(
            {
                **common_fields(row_id),
                "delta_case_id": row_id,
                "route_id_nodi": route,
                "route_id_nodi_role": "join_key_only_not_selection",
                "diameter_nm": int(diameter_nm),
                "baseline_sidewall_deg_comsol": 90.0,
                "sidewall_deg_comsol": 85.0,
                "synthetic_counting_context_rate_delta": delta(
                    "synthetic_counting_context_rate"
                ),
                "mean_peak_height_delta": delta("mean_peak_height"),
                "mean_local_snr_delta": delta("mean_local_snr"),
                "selected_annulus_fraction_delta": delta(
                    "selected_annulus_fraction"
                ),
                "selected_annulus_mean_edge_norm_delta": delta(
                    "selected_annulus_mean_edge_norm"
                ),
                "delta_status": "executed_delta_context"
                if sidewall.get("execution_status") == "executed_bounded_nodi_shard"
                else "planned_delta_context",
            }
        )
    return deltas


def axis_summary_rows(rows: list[dict[str, Any]], deltas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    executed = [row for row in rows if row["execution_status"] == "executed_bounded_nodi_shard"]
    peak_delta_values = [
        abs(float(row["mean_peak_height_delta"]))
        for row in deltas
        if row.get("mean_peak_height_delta") not in {"", None}
    ]
    annulus_delta_values = [
        abs(float(row["selected_annulus_fraction_delta"]))
        for row in deltas
        if row.get("selected_annulus_fraction_delta") not in {"", None}
    ]
    return [
        {
            "axis": "route_diameter_coverage",
            "axis_status": "executed" if executed else "planned",
            "event_rows": len(rows),
            "executed_rows": len(executed),
            "delta_rows": len(deltas),
            "key_observation": "all PRS-approved routes and diameters are represented as sparse paired event context",
        },
        {
            "axis": "selected_annulus_event_context",
            "axis_status": "delta_available" if annulus_delta_values else "planned",
            "event_rows": len(rows),
            "executed_rows": len(executed),
            "delta_rows": len(deltas),
            "max_abs_delta": max(annulus_delta_values) if annulus_delta_values else "",
            "key_observation": "selected annulus fraction shifts are context only, not probability",
        },
        {
            "axis": "interference_response_event_context",
            "axis_status": "delta_available" if peak_delta_values else "planned",
            "event_rows": len(rows),
            "executed_rows": len(executed),
            "delta_rows": len(deltas),
            "max_abs_delta": max(peak_delta_values) if peak_delta_values else "",
            "key_observation": "peak-height and local-SNR deltas extend the interference-response context",
        },
    ]


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    event_columns = set().union(*(set(row) for row in payload["event_rows"]))
    delta_columns = set().union(*(set(row) for row in payload["paired_delta_rows"]))
    forbidden = sorted((event_columns | delta_columns) & FORBIDDEN_PRIMARY_COLUMNS)
    if forbidden:
        failures.append(f"forbidden columns present: {forbidden}")
    if payload["summary"]["event_rows"] != 156:
        failures.append("event row coverage must be 6 routes x 13 diameters x 2 angles")
    if payload["summary"]["paired_delta_rows"] != 78:
        failures.append("paired delta coverage must be 6 routes x 13 diameters")
    if payload["summary"]["source_missing_rows"] != 0:
        failures.append("source artifacts missing")
    for table_name in ("event_rows", "paired_delta_rows"):
        for index, row in enumerate(payload[table_name], start=1):
            for field in (
                "not_detection_probability",
                "not_yield",
                "not_selection_metric_claim",
                "not_qch_weighted",
                "not_true_W_eff",
                "not_production_prs",
            ):
                if row.get(field) is not True:
                    failures.append(f"{table_name} row {index} {field} must be true")
    return failures


def alignment_check_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    failures = validate_payload(payload)
    return [
        {
            "check_name": "full_route_diameter_angle_coverage",
            "check_pass": payload["summary"]["event_rows"] == 156,
            "observed": payload["summary"]["event_rows"],
            "expected": 156,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "paired_delta_coverage",
            "check_pass": payload["summary"]["paired_delta_rows"] == 78,
            "observed": payload["summary"]["paired_delta_rows"],
            "expected": 78,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "no_forbidden_primary_columns",
            "check_pass": not failures,
            "observed": "pass" if not failures else "; ".join(failures),
            "expected": "pass",
            "hard_fail_if_false": True,
        },
        {
            "check_name": "source_artifacts_present",
            "check_pass": payload["summary"]["source_missing_rows"] == 0,
            "observed": payload["summary"]["source_missing_rows"],
            "expected": 0,
            "hard_fail_if_false": True,
        },
    ]


def semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "event_rows": payload["event_rows"],
                "paired_delta_rows": payload["paired_delta_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload(*, execute_nodi: bool, n_events: int, random_seed: int) -> dict[str, Any]:
    rows = event_rows(
        execute_nodi=execute_nodi,
        n_events=n_events,
        random_seed=random_seed,
    )
    deltas = paired_delta_rows(rows)
    sources = source_lock_rows()
    dirty = dirty_context_rows()
    summary = {
        "artifact_id": ARTIFACT_ID,
        "disposition": DISPOSITION_EXECUTED if execute_nodi else DISPOSITION_PLAN,
        "expansion_version": EXPANSION_VERSION,
        "branch": git_branch(),
        "current_head": git_head(),
        "execute_nodi": bool(execute_nodi),
        "n_events_requested_per_shard": int(n_events),
        "route_count": len(PRS_APPROVED_ROUTE_MATRIX),
        "diameter_count": len(PRS_APPROVED_DIAMETERS_NM),
        "sidewall_angle_pair_count": len(THETA_PAIR_DEG_COMSOL),
        "event_rows": len(rows),
        "executed_event_rows": sum(
            row["execution_status"] == "executed_bounded_nodi_shard"
            for row in rows
        ),
        "paired_delta_rows": len(deltas),
        "executed_delta_rows": sum(
            row["delta_status"] == "executed_delta_context" for row in deltas
        ),
        "axis_summary_rows": 3,
        "source_lock_rows": len(sources),
        "source_missing_rows": sum(1 for row in sources if row["exists"] == "false"),
        "dirty_context_rows": len(dirty),
        "non_primary85_full_bounded_dirty_context_rows": sum(
            1
            for row in dirty
            if row["classification"] == "non_primary85_full_bounded_dirty_context"
        ),
        "primary_answer_frame": "full_sparse_bounded_event_context_for_sidewall_dimension_annulus_response",
        "not_primary_answer_frame": "probability_or_route_selection",
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    payload = {
        "summary": summary,
        "event_rows": rows,
        "paired_delta_rows": deltas,
        "axis_summary_rows": axis_summary_rows(rows, deltas),
        "source_lock_rows": sources,
        "dirty_context_rows": dirty,
        "alignment_check_rows": [],
        "failure_rows": [{"failure_index": "", "failure": "none"}],
    }
    failures = validate_payload(payload)
    if failures:
        summary["disposition"] = BLOCKED_DISPOSITION
        payload["failure_rows"] = [
            {"failure_index": index, "failure": failure}
            for index, failure in enumerate(failures, start=1)
        ]
    payload["alignment_check_rows"] = alignment_check_rows(payload)
    summary["alignment_check_rows"] = len(payload["alignment_check_rows"])
    summary["failed_alignment_check_rows"] = sum(
        1 for row in payload["alignment_check_rows"] if row["check_pass"] is not True
    )
    summary["semantic_digest"] = semantic_digest(payload)
    return payload


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_{DATE_STAMP}.json",
        "event_rows": OUTPUT_DIR / f"{PREFIX}_EVENT_ROWS_{DATE_STAMP}.csv",
        "paired_delta_rows": OUTPUT_DIR / f"{PREFIX}_PAIRED_DELTA_ROWS_{DATE_STAMP}.csv",
        "axis_summary": OUTPUT_DIR / f"{PREFIX}_AXIS_SUMMARY_ROWS_{DATE_STAMP}.csv",
        "alignment_checks": OUTPUT_DIR / f"{PREFIX}_ALIGNMENT_CHECKS_{DATE_STAMP}.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv",
        "failures": OUTPUT_DIR / f"{PREFIX}_FAILURES_{DATE_STAMP}.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv",
        "master_report": REPORT_DIR / f"595_{PREFIX}_{DATE_STAMP}.md",
    }
    write_json_atomic(outputs["status"], payload["summary"], sort_keys=True)
    write_csv_rows(outputs["event_rows"], payload["event_rows"])
    write_csv_rows(outputs["paired_delta_rows"], payload["paired_delta_rows"])
    write_csv_rows(outputs["axis_summary"], payload["axis_summary_rows"])
    write_csv_rows(outputs["alignment_checks"], payload["alignment_check_rows"])
    write_csv_rows(outputs["source_lock"], payload["source_lock_rows"])
    write_csv_rows(outputs["dirty_context"], payload["dirty_context_rows"])
    write_csv_rows(outputs["failures"], payload["failure_rows"])
    write_json_atomic(
        outputs["report_json"],
        {
            "summary": payload["summary"],
            "axis_summary_rows": payload["axis_summary_rows"],
            "alignment_check_rows": payload["alignment_check_rows"],
        },
        indent=None,
        sort_keys=True,
    )
    outputs["master_report"].write_text(render_markdown(payload), encoding="utf-8")
    write_csv_rows(outputs["manifest"], manifest_rows(outputs))
    return list(outputs.values())


def manifest_rows(outputs: dict[str, Path]) -> list[dict[str, Any]]:
    return [
        {
            "artifact_id": artifact_id,
            "path": display_path(path),
            "sha256": SELF_MANIFEST_SHA256
            if artifact_id == "manifest"
            else sha256_file(path),
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for artifact_id, path in outputs.items()
    ]


def render_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    return "\n".join(
        [
            "# NODI Sidewall Primary-85 Full Bounded Event Expansion",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Execute NODI: `{s['execute_nodi']}`",
            f"Event rows: `{s['event_rows']}`",
            f"Executed event rows: `{s['executed_event_rows']}`",
            f"Paired delta rows: `{s['paired_delta_rows']}`",
            f"Failed alignment checks: `{s['failed_alignment_check_rows']}`",
            "",
            "This package expands bounded NODI event context from the small 591 "
            "subset to all PRS-approved routes and diameters for the 90/85 degree "
            "pair. Outputs remain sparse event context and are not probability, "
            "yield, route selection, or production PRS artifacts.",
            "",
        ]
    )


def main() -> int:
    args = build_parser().parse_args()
    if not args.confirm_sidewall_primary85_full_bounded_event_expansion:
        print(
            "--confirm-sidewall-primary85-full-bounded-event-expansion is required",
            file=sys.stderr,
        )
        return 2
    payload = build_payload(
        execute_nodi=bool(args.execute_nodi),
        n_events=int(args.n_events),
        random_seed=int(args.random_seed),
    )
    write_outputs(payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0 if payload["summary"]["disposition"] != BLOCKED_DISPOSITION else 1


if __name__ == "__main__":
    raise SystemExit(main())
