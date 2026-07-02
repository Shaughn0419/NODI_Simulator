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


DATE_STAMP = "20260703"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_ANNULUS_WINDOW_FOLLOWUP_SYNTHESIS"
ARTIFACT_ID = "NODI_SIDEWALL_ANNULUS_WINDOW_FOLLOWUP_SYNTHESIS_20260703"
SYNTHESIS_VERSION = "sidewall_annulus_window_followup_synthesis_v1"
DISPOSITION = "NODI_SIDEWALL_ANNULUS_WINDOW_FOLLOWUP_SYNTHESIS_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_ANNULUS_WINDOW_FOLLOWUP_SYNTHESIS_FAIL_CLOSED"
CLAIM_BOUNDARY = "annulus_window_followup_context_not_probability_not_selection"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CANONICAL_WINDOW_ID = "0p5_0p8"

SOURCE_FILES = {
    "annulus_window_status_600": OUTPUT_DIR
    / "NODI_SIDEWALL_CANDIDATE_ENVELOPE_ANNULUS_WINDOW_SWEEP_STATUS_20260703.json",
    "annulus_window_summary_600": OUTPUT_DIR
    / "NODI_SIDEWALL_CANDIDATE_ENVELOPE_ANNULUS_WINDOW_SWEEP_ROUTE_WINDOW_SUMMARY_ROWS_20260703.csv",
    "annulus_window_comparison_600": OUTPUT_DIR
    / "NODI_SIDEWALL_CANDIDATE_ENVELOPE_ANNULUS_WINDOW_SWEEP_WINDOW_COMPARISON_ROWS_20260703.csv",
    "annulus_followup_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_annulus_window_followup_synthesis.py",
    "annulus_followup_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_annulus_window_followup_synthesis.py",
}

ALLOWED_USE = (
    "synthesize sidewall candidate-envelope annulus-window follow-up context "
    "for next simulation planning"
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
        description="Build sidewall annulus-window follow-up synthesis."
    )
    parser.add_argument(
        "--confirm-sidewall-annulus-window-followup-synthesis",
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
    output_report = f"reports/601_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_annulus_window_followup_synthesis.py",
        "tests/test_nodi_sidewall_annulus_window_followup_synthesis.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "annulus_followup_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "annulus_followup_output"
            release_decision = "included_or_rewritten_by_annulus_followup_builder"
        else:
            classification = "non_annulus_followup_dirty_context"
            release_decision = "ignored_for_annulus_followup"
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


def route_window_rows() -> list[dict[str, str]]:
    return load_rows("annulus_window_summary_600")


def grouped_route_windows() -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in route_window_rows():
        grouped[row.get("source_route_id_nodi", "")].append(row)
    return grouped


def window_followup_class(row: dict[str, str]) -> str:
    if row.get("annulus_window_id") == CANONICAL_WINDOW_ID:
        return "canonical_reference_window"
    peak_delta = fnum(row.get("mean_peak_height_delta_vs_canonical"))
    ann_delta = fnum(row.get("mean_annulus_fraction_delta_vs_canonical"))
    if peak_delta > 0 and ann_delta > 0:
        return "response_and_annulus_positive_context"
    if peak_delta > 0 and ann_delta <= 0:
        return "response_positive_annulus_tradeoff_context"
    if peak_delta <= 0 and ann_delta > 0:
        return "annulus_positive_response_tradeoff_context"
    return "tradeoff_or_negative_context"


def route_followup_rows() -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for source_route, rows in sorted(grouped_route_windows().items()):
        candidate_route = rows[0].get("candidate_envelope_route_id_nodi", "")
        contexts = {row["annulus_window_id"]: window_followup_class(row) for row in rows}
        followup_windows = [CANONICAL_WINDOW_ID]
        for row in rows:
            window_id = row["annulus_window_id"]
            if window_id == CANONICAL_WINDOW_ID:
                continue
            context = contexts[window_id]
            if context in {
                "response_and_annulus_positive_context",
                "response_positive_annulus_tradeoff_context",
                "annulus_positive_response_tradeoff_context",
            }:
                followup_windows.append(window_id)
        outer = contexts.get("0p6_0p9", "")
        inner = contexts.get("0p4_0p7", "")
        if "positive" in outer and "positive" in inner:
            policy = "sweep_inner_canonical_outer_windows"
        elif "positive" in outer:
            policy = "sweep_canonical_plus_outer_shift"
        elif "positive" in inner:
            policy = "sweep_canonical_plus_inner_shift"
        else:
            policy = "retain_canonical_with_tradeoff_monitor"
        output.append(
            {
                **common_guard_fields(f"ANN-FOLLOW-{source_route.replace('/', '_')}"),
                "source_route_id_nodi": source_route,
                "candidate_envelope_route_id_nodi": candidate_route,
                "route_id_role": "annulus_followup_context_not_selection",
                "followup_window_set_json": json.dumps(sorted(set(followup_windows))),
                "inner_window_context": inner,
                "canonical_window_context": contexts.get(CANONICAL_WINDOW_ID, ""),
                "outer_window_context": outer,
                "annulus_window_followup_policy_context": policy,
                "windows_with_positive_response_context": sum(
                    fnum(row.get("mean_peak_height_delta_vs_canonical")) > 0
                    for row in rows
                    if row.get("annulus_window_id") != CANONICAL_WINDOW_ID
                ),
                "windows_with_positive_annulus_fraction_context": sum(
                    fnum(row.get("mean_annulus_fraction_delta_vs_canonical")) > 0
                    for row in rows
                    if row.get("annulus_window_id") != CANONICAL_WINDOW_ID
                ),
                "annulus_window_context_is_sparse": True,
            }
        )
    return output


def window_family_rows() -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in route_window_rows():
        grouped[row.get("annulus_window_id", "")].append(row)
    output: list[dict[str, Any]] = []
    for window_id, rows in sorted(grouped.items()):
        output.append(
            {
                **common_guard_fields(f"ANN-FAMILY-{window_id}"),
                "annulus_window_id": window_id,
                "window_family_role": "context_family_not_selection",
                "route_window_rows": len(rows),
                "routes_with_positive_response_context": sum(
                    fnum(row.get("mean_peak_height_delta_vs_canonical")) > 0
                    for row in rows
                ),
                "routes_with_positive_annulus_fraction_context": sum(
                    fnum(row.get("mean_annulus_fraction_delta_vs_canonical")) > 0
                    for row in rows
                ),
                "mean_peak_height_delta_vs_canonical_mean": sum(
                    fnum(row.get("mean_peak_height_delta_vs_canonical"))
                    for row in rows
                )
                / len(rows),
                "mean_annulus_fraction_delta_vs_canonical_mean": sum(
                    fnum(row.get("mean_annulus_fraction_delta_vs_canonical"))
                    for row in rows
                )
                / len(rows),
                "window_family_context": (
                    "canonical_reference_family"
                    if window_id == CANONICAL_WINDOW_ID
                    else "noncanonical_followup_family"
                ),
            }
        )
    return output


def answer_axis_rows(route_rows: list[dict[str, Any]], family_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **common_guard_fields("ANN-FOLLOW-AXIS-ANNULUS"),
            "answer_axis": "selected_annulus_range",
            "answer": "annulus_range_requires_window_set_followup",
            "affected_rows": len(route_rows),
            "window_family_rows": len(family_rows),
            "mainline_interpretation": (
                "sidewall-aware candidate dimensions should carry an annulus "
                "window set into the next sweep rather than freezing only 0.5-0.8"
            ),
        },
        {
            **common_guard_fields("ANN-FOLLOW-AXIS-RESPONSE"),
            "answer_axis": "interference_response",
            "answer": "annulus_window_choice_changes_response_context",
            "affected_rows": sum(
                row["windows_with_positive_response_context"] > 0 for row in route_rows
            ),
            "window_family_rows": len(family_rows),
            "mainline_interpretation": (
                "annulus-window movement changes peak-height response context, so "
                "interference enhancement analysis must keep annulus explicit"
            ),
        },
        {
            **common_guard_fields("ANN-FOLLOW-AXIS-DIMENSION"),
            "answer_axis": "candidate_dimension_envelope",
            "answer": "candidate_dimensions_remain_fixed_during_annulus_followup",
            "affected_rows": len(route_rows),
            "window_family_rows": len(family_rows),
            "mainline_interpretation": (
                "the 598/599 candidate dimensions remain the envelope basis while "
                "annulus window is varied as an independent detector/context axis"
            ),
        },
    ]


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    table_names = ("route_followup_rows", "window_family_rows", "answer_axis_rows")
    columns: set[str] = set()
    for table_name in table_names:
        if payload[table_name]:
            columns |= set().union(*(set(row) for row in payload[table_name]))
    forbidden = sorted(columns & FORBIDDEN_PRIMARY_COLUMNS)
    if forbidden:
        failures.append(f"forbidden columns present: {forbidden}")
    if payload["summary"]["route_followup_rows"] != 6:
        failures.append("route followup rows must cover six candidate routes")
    if payload["summary"]["window_family_rows"] != 3:
        failures.append("window family rows must cover three annulus windows")
    if payload["summary"]["source_missing_rows"] != 0:
        failures.append("source artifacts missing")
    return failures


def validation_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    failures = validate_payload(payload)
    return [
        {
            "check_name": "route_followup_coverage",
            "check_pass": payload["summary"]["route_followup_rows"] == 6,
            "observed": payload["summary"]["route_followup_rows"],
            "expected": 6,
            "hard_fail_if_false": True,
        },
        {
            "check_name": "window_family_coverage",
            "check_pass": payload["summary"]["window_family_rows"] == 3,
            "observed": payload["summary"]["window_family_rows"],
            "expected": 3,
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
            "route_followup_rows": payload["route_followup_rows"],
            "window_family_rows": payload["window_family_rows"],
            "answer_axis_rows": payload["answer_axis_rows"],
        }
    )


def build_payload() -> dict[str, Any]:
    route_rows = route_followup_rows()
    family_rows = window_family_rows()
    axes = answer_axis_rows(route_rows, family_rows)
    sources = source_lock_rows()
    dirty = dirty_context_rows()
    summary = {
        "artifact_id": ARTIFACT_ID,
        "disposition": DISPOSITION,
        "synthesis_version": SYNTHESIS_VERSION,
        "branch": git_branch(),
        "current_head": git_head(),
        "route_followup_rows": len(route_rows),
        "window_family_rows": len(family_rows),
        "answer_axis_rows": len(axes),
        "routes_with_noncanonical_followup_windows": sum(
            len(json.loads(row["followup_window_set_json"])) > 1 for row in route_rows
        ),
        "source_lock_rows": len(sources),
        "source_missing_rows": sum(1 for row in sources if row["exists"] == "false"),
        "dirty_context_rows": len(dirty),
        "non_annulus_followup_dirty_context_rows": sum(
            1
            for row in dirty
            if row["classification"] == "non_annulus_followup_dirty_context"
        ),
        "primary_answer_frame": "annulus_window_followup_for_sidewall_candidate_dimensions",
        "not_primary_answer_frame": "route_winner_or_final_probability",
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    payload = {
        "summary": summary,
        "route_followup_rows": route_rows,
        "window_family_rows": family_rows,
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
        "route_followup": OUTPUT_DIR / f"{PREFIX}_ROUTE_FOLLOWUP_ROWS_{DATE_STAMP}.csv",
        "window_family": OUTPUT_DIR / f"{PREFIX}_WINDOW_FAMILY_ROWS_{DATE_STAMP}.csv",
        "answer_axis": OUTPUT_DIR / f"{PREFIX}_ANSWER_AXIS_ROWS_{DATE_STAMP}.csv",
        "validation": OUTPUT_DIR / f"{PREFIX}_VALIDATION_ROWS_{DATE_STAMP}.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv",
        "failures": OUTPUT_DIR / f"{PREFIX}_FAILURES_{DATE_STAMP}.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv",
        "master_report": REPORT_DIR / f"601_{PREFIX}_{DATE_STAMP}.md",
    }
    write_json_atomic(outputs["status"], payload["summary"], sort_keys=True)
    write_csv_rows(outputs["route_followup"], payload["route_followup_rows"])
    write_csv_rows(outputs["window_family"], payload["window_family_rows"])
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
            "route_followup_rows": payload["route_followup_rows"],
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
            "# NODI Sidewall Annulus Window Follow-Up Synthesis",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Route follow-up rows: `{s['route_followup_rows']}`",
            f"Window family rows: `{s['window_family_rows']}`",
            f"Routes with noncanonical follow-up windows: `{s['routes_with_noncanonical_followup_windows']}`",
            f"Failed validation rows: `{s['failed_validation_rows']}`",
            "",
            "This synthesis converts the 600 annulus-window sweep into route-level "
            "follow-up window sets. It keeps candidate dimensions fixed and treats "
            "annulus windows as an explicit simulation axis, not as route selection, "
            "probability, yield, wet, fabrication, or production evidence.",
            "",
        ]
    )


def main() -> int:
    args = build_parser().parse_args()
    if not args.confirm_sidewall_annulus_window_followup_synthesis:
        print(
            "--confirm-sidewall-annulus-window-followup-synthesis is required",
            file=sys.stderr,
        )
        return 2
    payload = build_payload()
    write_outputs(payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0 if payload["disposition"] != BLOCKED_DISPOSITION else 1


if __name__ == "__main__":
    raise SystemExit(main())
