#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
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

from nodi_simulator.nodi_comsol_next_artifacts import (  # noqa: E402
    COMSOL_V4_ASSUMPTION_SET_ID,
    COMSOL_V4_ASSUMPTION_SET_SHA256,
    COMSOL_V4_ASSUMPTION_SET_VERSION,
)
from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260702"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_CANDIDATE_DIMENSION_RECOMMENDATION_SYNTHESIS"
ARTIFACT_ID = "NODI_SIDEWALL_CANDIDATE_DIMENSION_RECOMMENDATION_SYNTHESIS_20260702"
SYNTHESIS_VERSION = "sidewall_candidate_dimension_recommendation_synthesis_v1"
DISPOSITION = "NODI_SIDEWALL_CANDIDATE_DIMENSION_RECOMMENDATION_SYNTHESIS_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_CANDIDATE_DIMENSION_RECOMMENDATION_SYNTHESIS_FAIL_CLOSED"
CLAIM_BOUNDARY = "candidate_dimension_recommendation_context_not_selection_not_probability"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

SOURCE_FILES = {
    "integrated_status_596": OUTPUT_DIR
    / "NODI_SIDEWALL_FULL_EVENT_INTEGRATED_UPDATE_PACKET_STATUS_20260702.json",
    "integrated_rows_596": OUTPUT_DIR
    / "NODI_SIDEWALL_FULL_EVENT_INTEGRATED_UPDATE_PACKET_INTEGRATED_ROUTE_DIAMETER_ROWS_20260702.csv",
    "compensated_status_597": OUTPUT_DIR
    / "NODI_SIDEWALL_COMPENSATED_WIDTH_FOLLOWUP_BOUNDED_EVENTS_STATUS_20260702.json",
    "compensated_delta_rows_597": OUTPUT_DIR
    / "NODI_SIDEWALL_COMPENSATED_WIDTH_FOLLOWUP_BOUNDED_EVENTS_CANDIDATE_DELTA_ROWS_20260702.csv",
    "compensated_route_envelopes_597": OUTPUT_DIR
    / "NODI_SIDEWALL_COMPENSATED_WIDTH_FOLLOWUP_BOUNDED_EVENTS_ROUTE_ENVELOPE_ROWS_20260702.csv",
    "candidate_recommendation_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_candidate_dimension_recommendation_synthesis.py",
    "candidate_recommendation_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_candidate_dimension_recommendation_synthesis.py",
}

ALLOWED_USE = (
    "synthesize candidate sidewall-aware dimension changes, selected-annulus "
    "tradeoffs, and interference-response context for next simulation planning"
)
BLOCKED_USE = (
    "route winner, scalar score, final detection probability, yield, wet "
    "experimental claim, fabrication release, q_ch weighting, true W_eff, or "
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
        description="Build sidewall candidate dimension recommendation synthesis."
    )
    parser.add_argument(
        "--confirm-sidewall-candidate-dimension-recommendation-synthesis",
        action="store_true",
    )
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


def fnum(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        numeric = float(text)
    except ValueError:
        return default
    return numeric if math.isfinite(numeric) else default


def inum(value: Any, default: int = 0) -> int:
    return int(round(fnum(value, float(default))))


def deterministic_sha256(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
    output_report = f"reports/598_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_candidate_dimension_recommendation_synthesis.py",
        "tests/test_nodi_sidewall_candidate_dimension_recommendation_synthesis.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "candidate_recommendation_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "candidate_recommendation_output"
            release_decision = "included_or_rewritten_by_candidate_recommendation_builder"
        else:
            classification = "non_candidate_recommendation_dirty_context"
            release_decision = "ignored_for_candidate_recommendation"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def load_rows(source_id: str) -> list[dict[str, str]]:
    path = SOURCE_FILES[source_id]
    return read_csv_rows(path) if path.exists() else []


def common_guard_fields(row_id: str) -> dict[str, Any]:
    return {
        "synthesis_version": SYNTHESIS_VERSION,
        "row_id": row_id,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "not_detection_probability": True,
        "not_yield": True,
        "not_selection_metric_claim": True,
        "not_winner": True,
        "not_qch_weighted": True,
        "not_true_W_eff": True,
        "not_production_recommendation": True,
        "claim_boundary": CLAIM_BOUNDARY,
        "comsol_v4_assumption_set_id": COMSOL_V4_ASSUMPTION_SET_ID,
        "comsol_v4_assumption_set_version": COMSOL_V4_ASSUMPTION_SET_VERSION,
        "comsol_v4_assumption_set_sha256": COMSOL_V4_ASSUMPTION_SET_SHA256,
    }


def integrated_index() -> dict[tuple[str, int], dict[str, str]]:
    rows = load_rows("integrated_rows_596")
    return {(row.get("route_id_nodi", ""), inum(row.get("diameter_nm"))): row for row in rows}


def delta_rows_597() -> list[dict[str, str]]:
    return load_rows("compensated_delta_rows_597")


def route_envelope_index() -> dict[str, dict[str, str]]:
    return {
        row.get("source_route_id_nodi", ""): row
        for row in load_rows("compensated_route_envelopes_597")
    }


def candidate_row_context(delta: dict[str, str]) -> str:
    ann_delta = fnum(delta.get("candidate_minus_original_selected_annulus_fraction_delta"))
    peak_delta = fnum(delta.get("candidate_minus_original_mean_peak_height_delta"))
    if peak_delta > 0 and ann_delta >= 0:
        return "candidate_width_improves_response_without_annulus_loss"
    if peak_delta > 0 and ann_delta < 0:
        return "candidate_width_improves_response_with_annulus_tradeoff"
    if ann_delta > 0:
        return "candidate_width_improves_annulus_with_response_tradeoff"
    return "candidate_width_needs_refinement_context"


def candidate_dimension_rows() -> list[dict[str, Any]]:
    integrated = integrated_index()
    rows: list[dict[str, Any]] = []
    for delta in delta_rows_597():
        source_route = delta.get("source_route_id_nodi", "")
        diameter_nm = inum(delta.get("diameter_nm"))
        integrated_row = integrated.get((source_route, diameter_nm), {})
        ann_delta = fnum(delta.get("candidate_minus_original_selected_annulus_fraction_delta"))
        peak_delta = fnum(delta.get("candidate_minus_original_mean_peak_height_delta"))
        rows.append(
            {
                **common_guard_fields(
                    f"REC-{source_route.replace('/', '_')}-P{diameter_nm}"
                ),
                "source_route_id_nodi": source_route,
                "candidate_route_id_nodi": delta.get("candidate_route_id_nodi", ""),
                "route_id_role": "candidate_dimension_context_not_selection",
                "diameter_nm": diameter_nm,
                "source_W_nominal_nm": inum(delta.get("source_W_nominal_nm")),
                "candidate_W_top_nm": inum(delta.get("candidate_W_top_nm")),
                "candidate_top_width_delta_nm": inum(
                    delta.get("candidate_top_width_delta_nm")
                ),
                "dimension_context_band_596": integrated_row.get(
                    "dimension_context_band", ""
                ),
                "original_85_vs_90_peak_height_delta_596": fnum(
                    integrated_row.get("mean_peak_height_delta")
                ),
                "candidate_minus_original_mean_peak_height_delta_597": peak_delta,
                "candidate_minus_original_selected_annulus_fraction_delta_597": ann_delta,
                "candidate_minus_original_mean_local_snr_delta_597": fnum(
                    delta.get("candidate_minus_original_mean_local_snr_delta")
                ),
                "candidate_recovery_context_597": delta.get(
                    "candidate_recovery_context", ""
                ),
                "candidate_dimension_context": candidate_row_context(delta),
                "recommended_next_simulation_action": (
                    "carry_candidate_width_into_wider_event_sweep"
                    if peak_delta > 0 or ann_delta > 0
                    else "refine_candidate_width_or_annulus_window"
                ),
                "sparse_event_context_only": True,
                "n_events_per_candidate_context": 2,
            }
        )
    return rows


def route_recommendation_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    envelopes = route_envelope_index()
    for row in rows:
        grouped[row["source_route_id_nodi"]].append(row)
    output: list[dict[str, Any]] = []
    for source_route, group in sorted(grouped.items()):
        envelope = envelopes.get(source_route, {})
        response_improved = sum(
            fnum(row["candidate_minus_original_mean_peak_height_delta_597"]) > 0
            for row in group
        )
        annulus_improved = sum(
            fnum(row["candidate_minus_original_selected_annulus_fraction_delta_597"]) > 0
            for row in group
        )
        annulus_worse = sum(
            fnum(row["candidate_minus_original_selected_annulus_fraction_delta_597"]) < 0
            for row in group
        )
        if response_improved and annulus_worse:
            context = "advance_candidate_envelope_with_annulus_tradeoff_review"
        elif response_improved or annulus_improved:
            context = "advance_candidate_envelope_for_next_simulation_sweep"
        else:
            context = "refine_width_or_annulus_candidate_before_next_sweep"
        output.append(
            {
                **common_guard_fields(f"REC-ROUTE-{source_route.replace('/', '_')}"),
                "source_route_id_nodi": source_route,
                "candidate_envelope_route_id_nodi": envelope.get(
                    "candidate_envelope_route_id_nodi", ""
                ),
                "route_id_role": "candidate_envelope_not_selection",
                "route_diameter_rows": len(group),
                "source_W_nominal_nm": inum(envelope.get("source_W_nominal_nm")),
                "candidate_envelope_W_top_nm": inum(
                    envelope.get("candidate_envelope_W_top_nm")
                ),
                "candidate_envelope_top_width_delta_nm": inum(
                    envelope.get("candidate_envelope_top_width_delta_nm")
                ),
                "candidate_rows_with_response_improvement": response_improved,
                "candidate_rows_with_annulus_improvement": annulus_improved,
                "candidate_rows_with_annulus_tradeoff": annulus_worse,
                "max_candidate_minus_original_mean_peak_height_delta": max(
                    fnum(row["candidate_minus_original_mean_peak_height_delta_597"])
                    for row in group
                ),
                "max_candidate_minus_original_selected_annulus_fraction_delta": max(
                    fnum(
                        row[
                            "candidate_minus_original_selected_annulus_fraction_delta_597"
                        ]
                    )
                    for row in group
                ),
                "candidate_dimension_recommendation_context": context,
                "recommended_next_simulation_action": (
                    "run_higher_event_count_candidate_envelope_sweep"
                    if context
                    != "refine_width_or_annulus_candidate_before_next_sweep"
                    else "refine_before_higher_event_count_sweep"
                ),
                "sparse_event_context_only": True,
            }
        )
    return output


def answer_axis_rows(
    candidate_rows: list[dict[str, Any]],
    route_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    route_text = "; ".join(
        f"{row['source_route_id_nodi']}->{row['candidate_envelope_route_id_nodi']}"
        for row in route_rows
    )
    return [
        {
            **common_guard_fields("REC-AXIS-DIMENSION"),
            "answer_axis": "recommended_dimension_window",
            "answer": "yes_candidate_sidewall_dimensions_shift_upward",
            "affected_rows": len(candidate_rows),
            "route_rows": len(route_rows),
            "route_candidate_envelopes": route_text,
            "mainline_interpretation": (
                "85deg sidewalls move the candidate top-width envelope upward for "
                "affected routes; these are simulation candidates, not unique "
                "manufacturing dimensions"
            ),
        },
        {
            **common_guard_fields("REC-AXIS-ANNULUS"),
            "answer_axis": "selected_annulus_range",
            "answer": "candidate_width_changes_annulus_context_with_tradeoffs",
            "affected_rows": sum(
                fnum(
                    row[
                        "candidate_minus_original_selected_annulus_fraction_delta_597"
                    ]
                )
                != 0
                for row in candidate_rows
            ),
            "route_rows": len(route_rows),
            "route_candidate_envelopes": route_text,
            "mainline_interpretation": (
                "compensated widths can recover selected-annulus event fraction in "
                "some rows while worsening it in others, so annulus windowing must "
                "stay explicit in the next sweep"
            ),
        },
        {
            **common_guard_fields("REC-AXIS-INTERFERENCE"),
            "answer_axis": "interference_response",
            "answer": "candidate_width_changes_interference_response_context",
            "affected_rows": sum(
                fnum(row["candidate_minus_original_mean_peak_height_delta_597"]) > 0
                for row in candidate_rows
            ),
            "route_rows": len(route_rows),
            "route_candidate_envelopes": route_text,
            "mainline_interpretation": (
                "most compensated-width sparse event rows improve peak-height "
                "context relative to the original 85deg width, but this remains "
                "sparse context that should feed a higher-event sweep"
            ),
        },
    ]


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    table_names = (
        "candidate_dimension_rows",
        "route_recommendation_rows",
        "answer_axis_rows",
    )
    columns: set[str] = set()
    for table_name in table_names:
        if payload[table_name]:
            columns |= set().union(*(set(row) for row in payload[table_name]))
    forbidden = sorted(columns & FORBIDDEN_PRIMARY_COLUMNS)
    if forbidden:
        failures.append(f"forbidden columns present: {forbidden}")
    if payload["summary"]["candidate_dimension_rows"] != 66:
        failures.append("candidate dimension rows must cover 597 candidate deltas")
    if payload["summary"]["route_recommendation_rows"] != 6:
        failures.append("route recommendation rows must cover six source routes")
    if payload["summary"]["answer_axis_rows"] != 3:
        failures.append("answer axis rows must cover dimension, annulus, response")
    if payload["summary"]["source_missing_rows"] != 0:
        failures.append("source artifacts missing")
    for table_name in table_names:
        for index, row in enumerate(payload[table_name], start=1):
            for field in (
                "not_detection_probability",
                "not_yield",
                "not_selection_metric_claim",
                "not_qch_weighted",
                "not_production_recommendation",
            ):
                if row.get(field) is not True:
                    failures.append(f"{table_name} row {index} {field} must be true")
    return failures


def validation_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    failures = validate_payload(payload)
    return [
        {
            "check_name": "candidate_dimension_row_coverage",
            "check_pass": payload["summary"]["candidate_dimension_rows"] == 66,
            "observed": payload["summary"]["candidate_dimension_rows"],
            "expected": 66,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "route_recommendation_row_coverage",
            "check_pass": payload["summary"]["route_recommendation_rows"] == 6,
            "observed": payload["summary"]["route_recommendation_rows"],
            "expected": 6,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "source_artifacts_present",
            "check_pass": payload["summary"]["source_missing_rows"] == 0,
            "observed": payload["summary"]["source_missing_rows"],
            "expected": 0,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "no_forbidden_primary_columns",
            "check_pass": not failures,
            "observed": "pass" if not failures else "; ".join(failures),
            "expected": "pass",
            "hard_fail_if_false": True,
        },
    ]


def semantic_digest(payload: dict[str, Any]) -> str:
    return deterministic_sha256(
        {
            "candidate_dimension_rows": payload["candidate_dimension_rows"],
            "route_recommendation_rows": payload["route_recommendation_rows"],
            "answer_axis_rows": payload["answer_axis_rows"],
        }
    )


def build_payload() -> dict[str, Any]:
    rows = candidate_dimension_rows()
    route_rows = route_recommendation_rows(rows)
    axes = answer_axis_rows(rows, route_rows)
    sources = source_lock_rows()
    dirty = dirty_context_rows()
    summary = {
        "artifact_id": ARTIFACT_ID,
        "disposition": DISPOSITION,
        "synthesis_version": SYNTHESIS_VERSION,
        "branch": git_branch(),
        "current_head": git_head(),
        "candidate_dimension_rows": len(rows),
        "route_recommendation_rows": len(route_rows),
        "answer_axis_rows": len(axes),
        "candidate_rows_with_response_improvement": sum(
            fnum(row["candidate_minus_original_mean_peak_height_delta_597"]) > 0
            for row in rows
        ),
        "candidate_rows_with_annulus_improvement": sum(
            fnum(
                row["candidate_minus_original_selected_annulus_fraction_delta_597"]
            )
            > 0
            for row in rows
        ),
        "candidate_rows_with_annulus_tradeoff": sum(
            fnum(
                row["candidate_minus_original_selected_annulus_fraction_delta_597"]
            )
            < 0
            for row in rows
        ),
        "route_candidate_envelopes_json": json.dumps(
            {
                row["source_route_id_nodi"]: row[
                    "candidate_envelope_route_id_nodi"
                ]
                for row in route_rows
            },
            sort_keys=True,
        ),
        "source_lock_rows": len(sources),
        "source_missing_rows": sum(1 for row in sources if row["exists"] == "false"),
        "dirty_context_rows": len(dirty),
        "non_candidate_recommendation_dirty_context_rows": sum(
            1
            for row in dirty
            if row["classification"] == "non_candidate_recommendation_dirty_context"
        ),
        "primary_answer_frame": "sidewall_candidate_dimensions_annulus_response_synthesis",
        "not_primary_answer_frame": "route_winner_or_final_probability",
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    payload = {
        "summary": summary,
        "candidate_dimension_rows": rows,
        "route_recommendation_rows": route_rows,
        "answer_axis_rows": axes,
        "source_lock_rows": sources,
        "dirty_context_rows": dirty,
        "validation_rows": [],
        "failure_rows": [{"failure_index": "", "failure": "none"}],
        "disposition": DISPOSITION,
    }
    failures = validate_payload(payload)
    if failures:
        summary["disposition"] = BLOCKED_DISPOSITION
        payload["disposition"] = BLOCKED_DISPOSITION
        payload["failure_rows"] = [
            {"failure_index": index, "failure": failure}
            for index, failure in enumerate(failures, start=1)
        ]
    payload["validation_rows"] = validation_rows(payload)
    summary["validation_rows"] = len(payload["validation_rows"])
    summary["failed_validation_rows"] = sum(
        1 for row in payload["validation_rows"] if row["check_pass"] is not True
    )
    summary["semantic_digest"] = semantic_digest(payload)
    return payload


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_{DATE_STAMP}.json",
        "candidate_dimensions": OUTPUT_DIR / f"{PREFIX}_CANDIDATE_DIMENSION_ROWS_{DATE_STAMP}.csv",
        "route_recommendations": OUTPUT_DIR / f"{PREFIX}_ROUTE_RECOMMENDATION_ROWS_{DATE_STAMP}.csv",
        "answer_axis": OUTPUT_DIR / f"{PREFIX}_ANSWER_AXIS_ROWS_{DATE_STAMP}.csv",
        "validation": OUTPUT_DIR / f"{PREFIX}_VALIDATION_ROWS_{DATE_STAMP}.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv",
        "failures": OUTPUT_DIR / f"{PREFIX}_FAILURES_{DATE_STAMP}.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv",
        "master_report": REPORT_DIR / f"598_{PREFIX}_{DATE_STAMP}.md",
    }
    write_json_atomic(outputs["status"], payload["summary"], sort_keys=True)
    write_csv_rows(outputs["candidate_dimensions"], payload["candidate_dimension_rows"])
    write_csv_rows(outputs["route_recommendations"], payload["route_recommendation_rows"])
    write_csv_rows(outputs["answer_axis"], payload["answer_axis_rows"])
    write_csv_rows(outputs["validation"], payload["validation_rows"])
    write_csv_rows(outputs["source_lock"], payload["source_lock_rows"])
    write_csv_rows(outputs["dirty_context"], payload["dirty_context_rows"])
    write_csv_rows(outputs["failures"], payload["failure_rows"])
    write_json_atomic(
        outputs["report_json"],
        {
            "summary": payload["summary"],
            "answer_axis_rows": payload["answer_axis_rows"],
            "route_recommendation_rows": payload["route_recommendation_rows"],
            "validation_rows": payload["validation_rows"],
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
            "# NODI Sidewall Candidate Dimension Recommendation Synthesis",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Candidate dimension rows: `{s['candidate_dimension_rows']}`",
            f"Route recommendation rows: `{s['route_recommendation_rows']}`",
            f"Answer axis rows: `{s['answer_axis_rows']}`",
            f"Failed validation rows: `{s['failed_validation_rows']}`",
            "",
            "This synthesis combines the 596 original-dimension sidewall impact "
            "and the 597 compensated-width follow-up. It reports candidate "
            "sidewall-aware top-width envelopes and annulus/response tradeoffs "
            "for the next simulation sweep. It is not a route winner, probability, "
            "yield, wet, fabrication, or production recommendation.",
            "",
        ]
    )


def main() -> int:
    args = build_parser().parse_args()
    if not args.confirm_sidewall_candidate_dimension_recommendation_synthesis:
        print(
            "--confirm-sidewall-candidate-dimension-recommendation-synthesis is required",
            file=sys.stderr,
        )
        return 2
    payload = build_payload()
    write_outputs(payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0 if payload["disposition"] != BLOCKED_DISPOSITION else 1


if __name__ == "__main__":
    raise SystemExit(main())
