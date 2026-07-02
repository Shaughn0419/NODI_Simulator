#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
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
from tools.audits.build_nodi_sidewall_distribution_weighted_width_sweep import (  # noqa: E402
    fnum,
    inum,
)


DATE_STAMP = "20260703"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_MAINLINE_SYNTHESIS"
ARTIFACT_ID = "NODI_SIDEWALL_MAINLINE_SYNTHESIS_20260703"
SYNTHESIS_VERSION = "sidewall_mainline_synthesis_v1"
DISPOSITION = "NODI_SIDEWALL_MAINLINE_SYNTHESIS_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_MAINLINE_SYNTHESIS_FAIL_CLOSED"
CLAIM_BOUNDARY = "mainline_synthesis_context_not_route_selection"

SOURCE_FILES = {
    "dimension_objective_rows_612": OUTPUT_DIR
    / "NODI_SIDEWALL_DIMENSION_OBJECTIVE_PACKET_DIMENSION_OBJECTIVE_ROWS_20260703.csv",
    "objective_summary_rows_612": OUTPUT_DIR
    / "NODI_SIDEWALL_DIMENSION_OBJECTIVE_PACKET_OBJECTIVE_SUMMARY_ROWS_20260703.csv",
    "question_rows_612": OUTPUT_DIR
    / "NODI_SIDEWALL_DIMENSION_OBJECTIVE_PACKET_QUESTION_ROWS_20260703.csv",
    "mainline_synthesis_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_mainline_synthesis.py",
    "mainline_synthesis_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_mainline_synthesis.py",
}

ALLOWED_USE = (
    "provide a compact mainline synthesis of sidewall-induced dimension, annulus, "
    "and response-context changes from 605-612 artifacts"
)
BLOCKED_USE = (
    "route winner, scalar route score, exact P(x,u) probability claim, final yield, "
    "final detection probability, wet experimental claim, q_ch weighting, true W_eff, "
    "or production runtime ingestion"
)
FORBIDDEN_PRIMARY_COLUMNS = {
    "winner",
    "route_score",
    "rank",
    "recommended_candidate",
    "detection_probability",
    "yield",
    "W_eff",
    "q_ch_eta",
    "rank_under_surrogate",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build sidewall mainline synthesis packet.")
    parser.add_argument("--confirm-sidewall-mainline-synthesis", action="store_true")
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
    return run_git(["rev-parse", "--abbrev-ref", "HEAD"])


def git_status_lines() -> list[str]:
    output = run_git(["status", "--short"])
    return [line for line in output.splitlines() if line.strip()]


def git_path_from_status_line(line: str) -> str:
    return line[3:] if len(line) > 3 else line


def display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def deterministic_sha256(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def common_guard_fields(row_id: str) -> dict[str, Any]:
    return {
        "synthesis_version": SYNTHESIS_VERSION,
        "row_id": row_id,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "claim_boundary": CLAIM_BOUNDARY,
        "not_exact_pxu_probability_grid": True,
        "not_detection_probability": True,
        "not_yield": True,
        "not_selection_metric_claim": True,
        "not_winner": True,
        "not_qch_weighted": True,
        "not_true_W_eff": True,
        "not_production_recommendation": True,
        "decision_use_allowed": False,
        "comsol_v4_assumption_set_id": COMSOL_V4_ASSUMPTION_SET_ID,
        "comsol_v4_assumption_set_version": COMSOL_V4_ASSUMPTION_SET_VERSION,
        "comsol_v4_assumption_set_sha256": COMSOL_V4_ASSUMPTION_SET_SHA256,
    }


def load_rows(source_id: str) -> list[dict[str, str]]:
    path = SOURCE_FILES[source_id]
    return read_csv_rows(path) if path.exists() else []


def source_lock_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id, path in SOURCE_FILES.items():
        rows.append(
            {
                **common_guard_fields(f"SOURCE-{source_id}"),
                "source_id": source_id,
                "path": display_path(path),
                "exists": path.exists(),
                "sha256": sha256_file(path) if path.exists() else "",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    tracked_prefixes = (
        "tools/audits/build_nodi_sidewall_mainline_synthesis.py",
        "tests/test_nodi_sidewall_mainline_synthesis.py",
        "reports/613_NODI_SIDEWALL_MAINLINE_SYNTHESIS_20260703.md",
        "reports/joint_interface_20260703/NODI_SIDEWALL_MAINLINE_SYNTHESIS_",
    )
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path.startswith(tracked_prefixes):
            classification = "this_artifact_scope"
            release_decision = "include_or_review_before_commit"
        else:
            classification = "pre_existing_or_unrelated_dirty_context"
            release_decision = "ignored_by_this_artifact"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def route_synthesis_rows() -> list[dict[str, Any]]:
    objective_rows = [
        row
        for row in load_rows("dimension_objective_rows_612")
        if row["weighting_mode"] != "uniform_edge_mass"
    ]
    grouped: dict[str, list[dict[str, str]]] = {}
    for row in objective_rows:
        grouped.setdefault(row["source_route_id_nodi"], []).append(row)

    rows: list[dict[str, Any]] = []
    for source_route, group in sorted(grouped.items()):
        objective_widths = [inum(row["objective_W_top_nm"]) for row in group]
        deltas = [inum(row["objective_delta_vs_candidate_nm"]) for row in group]
        peak_retentions = [fnum(row["peak_retention_at_objective"]) for row in group]
        snr_retentions = [fnum(row["snr_retention_at_objective"]) for row in group]
        annulus_contexts = sorted({row["annulus_policy_context_611"] for row in group})
        candidate_w = inum(group[0]["candidate_envelope_W_top_nm"])
        if min(deltas) > 0:
            dimension_context = "sidewall_objective_width_above_candidate"
        elif max(deltas) == 0:
            dimension_context = "sidewall_objective_width_retains_candidate"
        else:
            dimension_context = "sidewall_objective_width_mixed_context"
        rows.append(
            {
                **common_guard_fields(f"MAIN-{source_route.replace('/', '_')}"),
                "source_route_id_nodi": source_route,
                "candidate_envelope_W_top_nm": candidate_w,
                "comsol_objective_width_min_nm": min(objective_widths),
                "comsol_objective_width_max_nm": max(objective_widths),
                "comsol_delta_vs_candidate_min_nm": min(deltas),
                "comsol_delta_vs_candidate_max_nm": max(deltas),
                "dimension_context": dimension_context,
                "annulus_contexts_json": json.dumps(annulus_contexts, ensure_ascii=True),
                "annulus_context": (
                    "sidewall_annulus_context_shifted_from_canonical"
                    if "sidewall_annulus_context_shifted_from_canonical" in annulus_contexts
                    else "sidewall_annulus_context_retains_canonical_window"
                ),
                "min_peak_retention_at_objective": min(peak_retentions),
                "min_snr_retention_at_objective": min(snr_retentions),
                "objective_function_id": group[0]["objective_function_id"],
                "objective_version": group[0]["objective_version"],
                "objective_claim_level": group[0]["objective_claim_level"],
                "mainline_interpretation": (
                    "sidewall_changes_dimension_envelope_and_annulus_context"
                    if dimension_context == "sidewall_objective_width_above_candidate"
                    else "sidewall_retains_dimension_envelope_under_current_objective"
                ),
                "not_final_design_release": True,
            }
        )
    return rows


def aggregate_answer_rows(route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dimension_counts = Counter(row["dimension_context"] for row in route_rows)
    annulus_counts = Counter(row["annulus_context"] for row in route_rows)
    return [
        {
            **common_guard_fields("ANSWER-DIMENSION"),
            "question_id": "size_recommendation_delta_after_sidewall",
            "answer": (
                "sidewall changes the assumption-driven top-width envelope for 5 of 6 "
                "source routes under COMSOL-weighted v4 context; one route retains candidate"
            ),
            "routes_above_candidate": dimension_counts[
                "sidewall_objective_width_above_candidate"
            ],
            "routes_retaining_candidate": dimension_counts[
                "sidewall_objective_width_retains_candidate"
            ],
        },
        {
            **common_guard_fields("ANSWER-ANNULUS"),
            "question_id": "selected_annulus_range_delta_after_sidewall",
            "answer": (
                "sidewall plus COMSOL weighting shifts annulus context for 4 of 6 routes "
                "and retains canonical context for 2 of 6 routes"
            ),
            "routes_shifted_annulus_context": annulus_counts[
                "sidewall_annulus_context_shifted_from_canonical"
            ],
            "routes_retaining_canonical_annulus_context": annulus_counts[
                "sidewall_annulus_context_retains_canonical_window"
            ],
        },
        {
            **common_guard_fields("ANSWER-RESPONSE"),
            "question_id": "interference_response_delta_after_sidewall",
            "answer": (
                "the sidewall-aware response surrogate remains width-sensitive; the 612 "
                "objective preserves at least 95% peak and SNR response without converting "
                "that response context into detection probability"
            ),
            "min_route_peak_retention": min(
                fnum(row["min_peak_retention_at_objective"]) for row in route_rows
            ),
            "min_route_snr_retention": min(
                fnum(row["min_snr_retention_at_objective"]) for row in route_rows
            ),
        },
    ]


def validation_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    def add(check_id: str, passed: bool, detail: str) -> None:
        rows.append(
            {
                "check_id": check_id,
                "status": "pass" if passed else "fail",
                "detail": detail,
            }
        )

    routes = payload["route_synthesis_rows"]
    answers = payload["aggregate_answer_rows"]
    add("route_synthesis_rows_cover_six_routes", len(routes) == 6, f"route_synthesis_rows={len(routes)}")
    add("aggregate_answer_rows_cover_three_questions", len(answers) == 3, f"aggregate_answer_rows={len(answers)}")
    add(
        "dimension_context_has_five_above_one_retained",
        sum(row["dimension_context"] == "sidewall_objective_width_above_candidate" for row in routes) == 5
        and sum(row["dimension_context"] == "sidewall_objective_width_retains_candidate" for row in routes) == 1,
        "expected 5 routes above candidate and 1 retained under 612 objective",
    )
    add(
        "annulus_context_has_four_shifted_two_retained",
        sum(row["annulus_context"] == "sidewall_annulus_context_shifted_from_canonical" for row in routes) == 4
        and sum(row["annulus_context"] == "sidewall_annulus_context_retains_canonical_window" for row in routes) == 2,
        "expected 4 shifted annulus contexts and 2 retained canonical contexts",
    )
    add(
        "v4_assumption_hash_bound",
        all(
            row["comsol_v4_assumption_set_sha256"] == COMSOL_V4_ASSUMPTION_SET_SHA256
            for table in (routes, answers)
            for row in table
        ),
        COMSOL_V4_ASSUMPTION_SET_SHA256,
    )
    add(
        "no_forbidden_primary_columns",
        no_forbidden_primary_columns(payload),
        "outputs avoid score/winner/yield/detection/W_eff/q_ch primary columns",
    )
    return rows


def no_forbidden_primary_columns(payload: dict[str, Any]) -> bool:
    for table_name in ("route_synthesis_rows", "aggregate_answer_rows"):
        rows = payload[table_name]
        columns = set().union(*(set(row) for row in rows)) if rows else set()
        if FORBIDDEN_PRIMARY_COLUMNS.intersection(columns):
            return False
    return True


def manifest_rows(paths: list[Path]) -> list[dict[str, Any]]:
    return [
        {
            "artifact_id": ARTIFACT_ID,
            "path": display_path(path),
            "sha256": sha256_file(path) if path.exists() else "",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for path in paths
    ]


def build_payload() -> dict[str, Any]:
    routes = route_synthesis_rows()
    answers = aggregate_answer_rows(routes)
    payload: dict[str, Any] = {
        "artifact_id": ARTIFACT_ID,
        "synthesis_version": SYNTHESIS_VERSION,
        "date_stamp": DATE_STAMP,
        "disposition": DISPOSITION,
        "claim_boundary": CLAIM_BOUNDARY,
        "git_head": git_head(),
        "git_branch": git_branch(),
        "comsol_v4_assumption_set_id": COMSOL_V4_ASSUMPTION_SET_ID,
        "comsol_v4_assumption_set_version": COMSOL_V4_ASSUMPTION_SET_VERSION,
        "comsol_v4_assumption_set_sha256": COMSOL_V4_ASSUMPTION_SET_SHA256,
        "summary": {
            "route_synthesis_rows": len(routes),
            "aggregate_answer_rows": len(answers),
            "routes_above_candidate": sum(
                row["dimension_context"] == "sidewall_objective_width_above_candidate"
                for row in routes
            ),
            "routes_retaining_candidate": sum(
                row["dimension_context"] == "sidewall_objective_width_retains_candidate"
                for row in routes
            ),
            "routes_shifted_annulus_context": sum(
                row["annulus_context"] == "sidewall_annulus_context_shifted_from_canonical"
                for row in routes
            ),
            "routes_retaining_canonical_annulus_context": sum(
                row["annulus_context"] == "sidewall_annulus_context_retains_canonical_window"
                for row in routes
            ),
            "exact_pxu_probability_grid_available_now": False,
            "next_executable_block": "propagate_objective_envelope_to_runtime_or_report_layer",
        },
        "route_synthesis_rows": routes,
        "aggregate_answer_rows": answers,
        "source_lock_rows": source_lock_rows(),
        "dirty_context_rows": dirty_context_rows(),
    }
    validation = validation_rows(payload)
    payload["validation_rows"] = validation
    payload["summary"]["failed_validation_rows"] = sum(
        1 for row in validation if row["status"] != "pass"
    )
    if payload["summary"]["failed_validation_rows"]:
        payload["disposition"] = BLOCKED_DISPOSITION
    payload["payload_sha256"] = deterministic_sha256(
        {
            key: value
            for key, value in payload.items()
            if key not in {"payload_sha256", "dirty_context_rows"}
        }
    )
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    return [
        f"{row['check_id']}: {row['detail']}"
        for row in payload["validation_rows"]
        if row["status"] != "pass"
    ]


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    routes = sorted(payload["route_synthesis_rows"], key=lambda row: row["source_route_id_nodi"])
    answers = payload["aggregate_answer_rows"]
    lines = [
        "# NODI sidewall mainline synthesis",
        "",
        "## Mainline Answer",
        "",
    ]
    for row in answers:
        lines.append(f"- {row['question_id']}: {row['answer']}")
    lines.extend(
        [
            "",
            "## Counts",
            "",
            f"- routes above candidate: {summary['routes_above_candidate']}",
            f"- routes retaining candidate: {summary['routes_retaining_candidate']}",
            f"- routes with shifted annulus context: {summary['routes_shifted_annulus_context']}",
            f"- routes retaining canonical annulus context: {summary['routes_retaining_canonical_annulus_context']}",
            f"- failed validation rows: {summary['failed_validation_rows']}",
            "",
            "## Route Synthesis",
            "",
            (
                "| source route | candidate W_top nm | objective W_top nm | delta nm | "
                "dimension context | annulus context | min peak retention | min SNR retention |"
            ),
            "| --- | ---: | ---: | ---: | --- | --- | ---: | ---: |",
        ]
    )
    for row in routes:
        lines.append(
            "| {source} | {candidate} | {objective} | {delta} | {dim} | {ann} | {peak:.3f} | {snr:.3f} |".format(
                source=row["source_route_id_nodi"],
                candidate=row["candidate_envelope_W_top_nm"],
                objective=row["comsol_objective_width_min_nm"],
                delta=row["comsol_delta_vs_candidate_min_nm"],
                dim=row["dimension_context"],
                ann=row["annulus_context"],
                peak=fnum(row["min_peak_retention_at_objective"]),
                snr=fnum(row["min_snr_retention_at_objective"]),
            )
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            (
                "This packet is a synthesis and handoff interface. It is not a route "
                "winner, production design release, detection probability, yield claim, "
                "q_ch weighting, or true W_eff result."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_{DATE_STAMP}.json"
    report_json_path = OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json"
    route_path = OUTPUT_DIR / f"{PREFIX}_ROUTE_SYNTHESIS_ROWS_{DATE_STAMP}.csv"
    answer_path = OUTPUT_DIR / f"{PREFIX}_AGGREGATE_ANSWER_ROWS_{DATE_STAMP}.csv"
    validation_path = OUTPUT_DIR / f"{PREFIX}_VALIDATION_ROWS_{DATE_STAMP}.csv"
    source_lock_path = OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv"
    dirty_path = OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv"
    manifest_path = OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv"
    report_md_path = REPORT_DIR / f"613_{PREFIX}_{DATE_STAMP}.md"

    status_payload = {
        key: payload[key]
        for key in (
            "artifact_id",
            "synthesis_version",
            "date_stamp",
            "disposition",
            "claim_boundary",
            "git_head",
            "git_branch",
            "comsol_v4_assumption_set_id",
            "comsol_v4_assumption_set_version",
            "comsol_v4_assumption_set_sha256",
            "summary",
            "payload_sha256",
        )
    }
    write_json_atomic(status_path, status_payload, sort_keys=True)
    write_json_atomic(report_json_path, payload, sort_keys=True)
    write_csv_rows(route_path, payload["route_synthesis_rows"])
    write_csv_rows(answer_path, payload["aggregate_answer_rows"])
    write_csv_rows(validation_path, payload["validation_rows"])
    write_csv_rows(source_lock_path, payload["source_lock_rows"])
    write_csv_rows(
        dirty_path,
        payload["dirty_context_rows"]
        or [{"path": "", "git_status": "", "classification": "clean", "release_decision": "none"}],
    )
    paths = [
        status_path,
        report_json_path,
        route_path,
        answer_path,
        validation_path,
        source_lock_path,
        dirty_path,
        report_md_path,
    ]
    report_md_path.write_text(render_report(payload), encoding="utf-8", newline="\n")
    write_csv_rows(manifest_path, manifest_rows(paths))
    paths.append(manifest_path)
    return paths


def main() -> int:
    args = build_parser().parse_args()
    if not args.confirm_sidewall_mainline_synthesis:
        print("--confirm-sidewall-mainline-synthesis is required", file=sys.stderr)
        return 2
    payload = build_payload()
    failures = validate_payload(payload)
    paths = write_outputs(payload)
    print(json.dumps(payload["summary"], sort_keys=True))
    for path in paths:
        print(display_path(path))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
