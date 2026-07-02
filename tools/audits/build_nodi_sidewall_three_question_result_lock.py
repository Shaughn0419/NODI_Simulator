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


DATE_STAMP = "20260703"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_THREE_QUESTION_RESULT_LOCK"
ARTIFACT_ID = "NODI_SIDEWALL_THREE_QUESTION_RESULT_LOCK_20260703"
SYNTHESIS_VERSION = "sidewall_three_question_result_lock_v1"
DISPOSITION = "NODI_SIDEWALL_THREE_QUESTION_RESULT_LOCK_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_THREE_QUESTION_RESULT_LOCK_FAIL_CLOSED"
CLAIM_BOUNDARY = "three_question_result_context_not_probability_not_selection"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

SOURCE_FILES = {
    "closein_status_602": OUTPUT_DIR
    / "NODI_SIDEWALL_THREE_QUESTION_CLOSEIN_SYNTHESIS_STATUS_20260703.json",
    "closein_route_rows_602": OUTPUT_DIR
    / "NODI_SIDEWALL_THREE_QUESTION_CLOSEIN_SYNTHESIS_ROUTE_CLOSEIN_ROWS_20260703.csv",
    "followup_status_603": OUTPUT_DIR
    / "NODI_SIDEWALL_FOLLOWUP_WINDOW_HIGHER_EVENT_SWEEP_STATUS_20260703.json",
    "followup_route_closein_603": OUTPUT_DIR
    / "NODI_SIDEWALL_FOLLOWUP_WINDOW_HIGHER_EVENT_SWEEP_ROUTE_CLOSEIN_ROWS_20260703.csv",
    "followup_route_window_summary_603": OUTPUT_DIR
    / "NODI_SIDEWALL_FOLLOWUP_WINDOW_HIGHER_EVENT_SWEEP_ROUTE_WINDOW_SUMMARY_ROWS_20260703.csv",
    "result_lock_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_three_question_result_lock.py",
    "result_lock_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_three_question_result_lock.py",
}

ALLOWED_USE = (
    "lock the current sidewall-angle simulation answer for dimension envelope "
    "changes, selected-annulus window changes, and peak/local-SNR response "
    "changes"
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
        description="Build sidewall three-question result lock."
    )
    parser.add_argument(
        "--confirm-sidewall-three-question-result-lock",
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
    output_report = f"reports/604_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_three_question_result_lock.py",
        "tests/test_nodi_sidewall_three_question_result_lock.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "three_question_result_lock_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "three_question_result_lock_output"
            release_decision = "included_or_rewritten_by_three_question_result_lock_builder"
        else:
            classification = "non_three_question_result_lock_dirty_context"
            release_decision = "ignored_for_three_question_result_lock"
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


def rows_by_route(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["source_route_id_nodi"]: row for row in rows}


def route_window_summary_by_route() -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in load_rows("followup_route_window_summary_603"):
        grouped.setdefault(row["source_route_id_nodi"], []).append(row)
    return grouped


def route_result_rows() -> list[dict[str, Any]]:
    closein_602 = rows_by_route(load_rows("closein_route_rows_602"))
    followup_603 = rows_by_route(load_rows("followup_route_closein_603"))
    window_groups = route_window_summary_by_route()
    output: list[dict[str, Any]] = []
    for source_route in sorted(closein_602):
        c602 = closein_602[source_route]
        f603 = followup_603[source_route]
        windows = window_groups.get(source_route, [])
        positive_response_windows = [
            row["annulus_window_id"]
            for row in windows
            if row.get("is_canonical_annulus_window") != "True"
            and (
                fnum(row.get("mean_peak_height_delta_vs_canonical")) > 0
                or fnum(row.get("mean_local_snr_delta_vs_canonical")) > 0
            )
        ]
        annulus_changed_windows = [
            row["annulus_window_id"]
            for row in windows
            if row.get("is_canonical_annulus_window") != "True"
            and fnum(row.get("mean_annulus_fraction_delta_vs_canonical")) != 0
        ]
        response_count = inum(
            f603["noncanonical_windows_with_response_positive_context"]
        )
        annulus_count = inum(
            f603["noncanonical_windows_with_annulus_change_context"]
        )
        if response_count >= 2:
            route_result_context = "full_window_response_context_retained"
            next_action = "keep_inner_canonical_outer_windows_for_diameter_resolution"
        elif annulus_count > 0:
            route_result_context = "outer_window_annulus_context_retained"
            next_action = "keep_canonical_outer_windows_for_annulus_monitoring"
        else:
            route_result_context = "canonical_only_review_context"
            next_action = "review_before_more_events"
        output.append(
            {
                **common_guard_fields(f"RESULT-{source_route.replace('/', '_')}"),
                "source_route_id_nodi": source_route,
                "candidate_envelope_route_id_nodi": c602[
                    "candidate_envelope_route_id_nodi"
                ],
                "route_id_role": "three_question_result_context_not_selection",
                "source_W_nominal_nm": c602["source_W_nominal_nm"],
                "candidate_envelope_W_top_nm": c602["candidate_envelope_W_top_nm"],
                "candidate_envelope_top_width_delta_nm": c602[
                    "candidate_envelope_top_width_delta_nm"
                ],
                "dimension_result_context": (
                    "candidate_top_width_envelope_changed_under_sidewall"
                ),
                "followup_window_set_json": f603["followup_window_set_json"],
                "noncanonical_windows_with_response_positive_context": response_count,
                "noncanonical_windows_with_annulus_change_context": annulus_count,
                "positive_response_window_ids_json": json.dumps(
                    positive_response_windows, ensure_ascii=True
                ),
                "annulus_changed_window_ids_json": json.dumps(
                    annulus_changed_windows, ensure_ascii=True
                ),
                "route_result_context": route_result_context,
                "next_action_context": next_action,
                "evidence_sources": "602_three_question_closein;603_followup_window_higher_event",
            }
        )
    return output


def question_result_rows(route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    width_deltas = [inum(row["candidate_envelope_top_width_delta_nm"]) for row in route_rows]
    response_context_routes = sum(
        inum(row["noncanonical_windows_with_response_positive_context"]) > 0
        for row in route_rows
    )
    annulus_context_routes = sum(
        inum(row["noncanonical_windows_with_annulus_change_context"]) > 0
        for row in route_rows
    )
    status_603 = json.loads(SOURCE_FILES["followup_status_603"].read_text(encoding="utf-8"))
    return [
        {
            **common_guard_fields("QUESTION-RESULT-DIMENSION"),
            "axis_order": 1,
            "question_id": "size_recommendation_delta_after_sidewall",
            "result_status": "candidate_top_width_envelope_changed_for_6_of_6_routes",
            "route_count": len(route_rows),
            "routes_with_result_context": sum(1 for delta in width_deltas if delta > 0),
            "min_candidate_top_width_delta_nm": min(width_deltas),
            "max_candidate_top_width_delta_nm": max(width_deltas),
            "result_interpretation": (
                "sidewall angle changes the simulation candidate top-width envelope; "
                "these are NODI candidate envelope dimensions, not fabrication release"
            ),
        },
        {
            **common_guard_fields("QUESTION-RESULT-ANNULUS"),
            "axis_order": 2,
            "question_id": "selected_annulus_range_delta_after_sidewall",
            "result_status": "annulus_context_changed_for_6_of_6_routes",
            "route_count": len(route_rows),
            "routes_with_result_context": annulus_context_routes,
            "noncanonical_rows_with_annulus_fraction_change": status_603[
                "noncanonical_rows_with_annulus_fraction_change"
            ],
            "result_interpretation": (
                "annulus should remain route-specific; 0.5-0.8 is a reference "
                "window, not the only active sidewall context"
            ),
        },
        {
            **common_guard_fields("QUESTION-RESULT-RESPONSE"),
            "axis_order": 3,
            "question_id": "interference_response_delta_after_sidewall",
            "result_status": "peak_or_local_snr_context_changed_in_noncanonical_windows",
            "route_count": len(route_rows),
            "routes_with_result_context": response_context_routes,
            "noncanonical_rows_with_peak_height_change": status_603[
                "noncanonical_rows_with_peak_height_change"
            ],
            "noncanonical_rows_with_local_snr_change": status_603[
                "noncanonical_rows_with_local_snr_change"
            ],
            "result_interpretation": (
                "annulus-window choice changes peak-height/local-SNR sparse context "
                "after sidewall compensation; this is not detection probability"
            ),
        },
    ]


def next_action_rows(route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in route_rows:
        action = row["next_action_context"]
        if action == "keep_inner_canonical_outer_windows_for_diameter_resolution":
            event_hint = "increase_events_or_seed_replicates_on_three_windows"
        elif action == "keep_canonical_outer_windows_for_annulus_monitoring":
            event_hint = "increase_events_or_seed_replicates_on_canonical_outer_windows"
        else:
            event_hint = "review_route_context_before_next_execution"
        output.append(
            {
                **common_guard_fields(
                    f"NEXT-{row['source_route_id_nodi'].replace('/', '_')}"
                ),
                "source_route_id_nodi": row["source_route_id_nodi"],
                "candidate_envelope_route_id_nodi": row[
                    "candidate_envelope_route_id_nodi"
                ],
                "route_id_role": "next_action_context_not_selection",
                "followup_window_set_json": row["followup_window_set_json"],
                "next_action_context": action,
                "next_execution_hint": event_hint,
                "simulation_axis_to_hold_fixed": "candidate_envelope_top_width",
                "simulation_axis_to_vary_next": "annulus_window_and_particle_diameter",
            }
        )
    return output


def table_has_forbidden_columns(rows: list[dict[str, Any]]) -> bool:
    columns = set().union(*(set(row) for row in rows)) if rows else set()
    return bool(columns & FORBIDDEN_PRIMARY_COLUMNS)


def validation_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    route_rows = payload["route_result_rows"]
    question_rows = payload["question_result_rows"]
    next_rows = payload["next_action_rows"]
    source_missing = payload["summary"]["source_missing_rows"]
    checks = [
        (
            "source_artifacts_present",
            source_missing == 0,
            source_missing,
            0,
        ),
        (
            "three_question_result_rows_present",
            len(question_rows) == 3,
            len(question_rows),
            3,
        ),
        (
            "route_result_coverage",
            len(route_rows) == 6,
            len(route_rows),
            6,
        ),
        (
            "all_routes_have_dimension_delta_context",
            all(inum(row["candidate_envelope_top_width_delta_nm"]) > 0 for row in route_rows),
            sum(1 for row in route_rows if inum(row["candidate_envelope_top_width_delta_nm"]) > 0),
            6,
        ),
        (
            "all_routes_have_annulus_change_context",
            all(
                inum(row["noncanonical_windows_with_annulus_change_context"]) > 0
                for row in route_rows
            ),
            sum(
                1
                for row in route_rows
                if inum(row["noncanonical_windows_with_annulus_change_context"]) > 0
            ),
            6,
        ),
        (
            "response_positive_route_context_present",
            sum(
                1
                for row in route_rows
                if inum(row["noncanonical_windows_with_response_positive_context"]) > 0
            )
            == 4,
            sum(
                1
                for row in route_rows
                if inum(row["noncanonical_windows_with_response_positive_context"]) > 0
            ),
            4,
        ),
        (
            "next_action_coverage",
            len(next_rows) == 6,
            len(next_rows),
            6,
        ),
        (
            "no_forbidden_primary_columns",
            not any(
                table_has_forbidden_columns(rows)
                for rows in (route_rows, question_rows, next_rows)
            ),
            "pass",
            "pass",
        ),
    ]
    return [
        {
            "check_name": name,
            "check_pass": passed,
            "observed": observed,
            "expected": expected,
            "hard_fail_if_false": True,
        }
        for name, passed, observed, expected in checks
    ]


def validate_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row
        for row in validation_rows(payload)
        if str(row["check_pass"]).lower() != "true"
    ]


def build_payload() -> dict[str, Any]:
    sources = source_lock_rows()
    dirty = dirty_context_rows()
    routes = route_result_rows()
    questions = question_result_rows(routes)
    next_actions = next_action_rows(routes)
    status_603 = json.loads(SOURCE_FILES["followup_status_603"].read_text(encoding="utf-8"))
    summary = {
        "artifact_id": ARTIFACT_ID,
        "synthesis_version": SYNTHESIS_VERSION,
        "disposition": DISPOSITION,
        "branch": git_branch(),
        "current_head": git_head(),
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "claim_boundary": CLAIM_BOUNDARY,
        "primary_answer_frame": "sidewall_three_question_result_lock",
        "not_primary_answer_frame": "route_winner_or_final_probability",
        "route_result_rows": len(routes),
        "question_result_rows": len(questions),
        "next_action_rows": len(next_actions),
        "routes_with_dimension_delta_context": sum(
            1 for row in routes if inum(row["candidate_envelope_top_width_delta_nm"]) > 0
        ),
        "routes_with_annulus_change_context": sum(
            1
            for row in routes
            if inum(row["noncanonical_windows_with_annulus_change_context"]) > 0
        ),
        "routes_with_response_positive_context": sum(
            1
            for row in routes
            if inum(row["noncanonical_windows_with_response_positive_context"]) > 0
        ),
        "source_603_event_rows": status_603["event_rows"],
        "source_603_executed_event_rows": status_603["executed_event_rows"],
        "source_603_noncanonical_rows_with_annulus_fraction_change": status_603[
            "noncanonical_rows_with_annulus_fraction_change"
        ],
        "source_603_noncanonical_rows_with_peak_height_change": status_603[
            "noncanonical_rows_with_peak_height_change"
        ],
        "source_603_noncanonical_rows_with_local_snr_change": status_603[
            "noncanonical_rows_with_local_snr_change"
        ],
        "source_lock_rows": len(sources),
        "source_missing_rows": sum(1 for row in sources if row["exists"] != "true"),
        "dirty_context_rows": len(dirty),
        "non_three_question_result_lock_dirty_context_rows": sum(
            1
            for row in dirty
            if row["classification"] == "non_three_question_result_lock_dirty_context"
        ),
    }
    payload: dict[str, Any] = {
        "summary": summary,
        "route_result_rows": routes,
        "question_result_rows": questions,
        "next_action_rows": next_actions,
        "source_lock_rows": sources,
        "dirty_context_rows": dirty,
        "disposition": DISPOSITION,
    }
    failures = validate_payload(payload)
    summary["failed_validation_rows"] = len(failures)
    payload["validation_rows"] = validation_rows(payload)
    payload["failures"] = failures
    if failures:
        payload["disposition"] = BLOCKED_DISPOSITION
        summary["disposition"] = BLOCKED_DISPOSITION
    summary["semantic_digest"] = deterministic_sha256(
        {
            "route_result_rows": routes,
            "question_result_rows": questions,
            "next_action_rows": next_actions,
            "validation_rows": payload["validation_rows"],
        }
    )
    return payload


def manifest_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        exists = path.exists()
        rows.append(
            {
                "artifact_id": ARTIFACT_ID,
                "path": display_path(path),
                "exists": str(exists).lower(),
                "sha256": sha256_file(path) if exists else "",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    rows.append(
        {
            "artifact_id": ARTIFACT_ID,
            "path": f"reports/joint_interface_{DATE_STAMP}/{PREFIX}_MANIFEST_{DATE_STAMP}.csv",
            "exists": "true",
            "sha256": SELF_MANIFEST_SHA256,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
            "claim_boundary": CLAIM_BOUNDARY,
        }
    )
    return rows


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_{DATE_STAMP}.json"
    report_json_path = OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json"
    route_path = OUTPUT_DIR / f"{PREFIX}_ROUTE_RESULT_ROWS_{DATE_STAMP}.csv"
    question_path = OUTPUT_DIR / f"{PREFIX}_QUESTION_RESULT_ROWS_{DATE_STAMP}.csv"
    next_path = OUTPUT_DIR / f"{PREFIX}_NEXT_ACTION_ROWS_{DATE_STAMP}.csv"
    source_path = OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv"
    dirty_path = OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv"
    validation_path = OUTPUT_DIR / f"{PREFIX}_VALIDATION_ROWS_{DATE_STAMP}.csv"
    failure_path = OUTPUT_DIR / f"{PREFIX}_FAILURES_{DATE_STAMP}.csv"
    manifest_path = OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv"
    md_path = REPORT_DIR / f"604_{PREFIX}_{DATE_STAMP}.md"

    write_json_atomic(status_path, payload["summary"])
    write_json_atomic(
        report_json_path,
        {
            "summary": payload["summary"],
            "route_result_rows": payload["route_result_rows"],
            "question_result_rows": payload["question_result_rows"],
            "next_action_rows": payload["next_action_rows"],
            "validation_rows": payload["validation_rows"],
            "failures": payload["failures"],
        },
    )
    write_csv_rows(route_path, payload["route_result_rows"])
    write_csv_rows(question_path, payload["question_result_rows"])
    write_csv_rows(next_path, payload["next_action_rows"])
    write_csv_rows(source_path, payload["source_lock_rows"])
    write_csv_rows(dirty_path, payload["dirty_context_rows"])
    write_csv_rows(validation_path, payload["validation_rows"])
    write_csv_rows(failure_path, payload["failures"] or [{"failure": "none"}])
    md_path.write_text(render_markdown(payload), encoding="utf-8", newline="\n")
    outputs.extend(
        [
            status_path,
            report_json_path,
            route_path,
            question_path,
            next_path,
            source_path,
            dirty_path,
            validation_path,
            failure_path,
            md_path,
        ]
    )
    write_csv_rows(manifest_path, manifest_rows(outputs))
    outputs.append(manifest_path)
    return outputs


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    q_lines = [
        f"- `{row['question_id']}`: `{row['result_status']}`"
        for row in payload["question_result_rows"]
    ]
    r_lines = [
        "- `{source}` -> `{candidate}`; width delta `{delta}` nm; windows `{windows}`; context `{context}`".format(
            source=row["source_route_id_nodi"],
            candidate=row["candidate_envelope_route_id_nodi"],
            delta=row["candidate_envelope_top_width_delta_nm"],
            windows=row["followup_window_set_json"],
            context=row["route_result_context"],
        )
        for row in payload["route_result_rows"]
    ]
    return "\n".join(
        [
            "# NODI Sidewall Three-Question Result Lock",
            "",
            f"Disposition: `{summary['disposition']}`",
            f"Artifact ID: `{summary['artifact_id']}`",
            f"Route result rows: `{summary['route_result_rows']}`",
            f"Question result rows: `{summary['question_result_rows']}`",
            f"603 executed event rows: `{summary['source_603_executed_event_rows']}`",
            f"Failed validation rows: `{summary['failed_validation_rows']}`",
            "",
            "This result lock keeps the sidewall-angle mainline on the three user questions: candidate dimension envelope change, selected-annulus window change, and peak/local-SNR response change. It is simulation context only, not route selection, final probability, yield, wet, fabrication, q_ch weighting, true W_eff, or production evidence.",
            "",
            "## Question Results",
            *q_lines,
            "",
            "## Route Results",
            *r_lines,
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_sidewall_three_question_result_lock:
        raise SystemExit("--confirm-sidewall-three-question-result-lock is required")
    payload = build_payload()
    paths = write_outputs(payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    print("wrote:")
    for path in paths:
        print(f"- {display_path(path)}")
    return 0 if payload["disposition"] == DISPOSITION else 2


if __name__ == "__main__":
    raise SystemExit(main())
