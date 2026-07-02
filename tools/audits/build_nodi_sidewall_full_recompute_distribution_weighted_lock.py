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
from tools.audits.build_nodi_sidewall_candidate_envelope_annulus_window_sweep import (  # noqa: E402
    execute_annulus_row,
)
from tools.audits.build_nodi_sidewall_distribution_weighted_response_surface import (  # noqa: E402
    WEIGHTING_MODES,
    nearest_comsol_profile_diameter,
    window_weight_lookup,
)
from tools.audits.build_nodi_sidewall_followup_window_higher_event_sweep import (  # noqa: E402
    plan_rows as followup_plan_rows,
)


DATE_STAMP = "20260703"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_SIDEWALL_FULL_RECOMPUTE_DISTRIBUTION_WEIGHTED_LOCK"
ARTIFACT_ID = "NODI_SIDEWALL_FULL_RECOMPUTE_DISTRIBUTION_WEIGHTED_LOCK_20260703"
SYNTHESIS_VERSION = "sidewall_full_recompute_distribution_weighted_lock_v1"
DISPOSITION_PLAN = "NODI_SIDEWALL_FULL_RECOMPUTE_DISTRIBUTION_WEIGHTED_LOCK_PLAN_READY"
DISPOSITION_EXECUTED = "NODI_SIDEWALL_FULL_RECOMPUTE_DISTRIBUTION_WEIGHTED_LOCK_EXECUTED_READY"
BLOCKED_DISPOSITION = "NODI_SIDEWALL_FULL_RECOMPUTE_DISTRIBUTION_WEIGHTED_LOCK_FAIL_CLOSED"
CLAIM_BOUNDARY = "full_nodi_recompute_distribution_weighted_context_not_exact_pxu"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
DEFAULT_N_EVENTS = 32
DEFAULT_RANDOM_SEED = 60700
CANONICAL_WINDOW_ID = "0p5_0p8"

SOURCE_FILES = {
    "weighted_status_606": OUTPUT_DIR
    / "NODI_SIDEWALL_DISTRIBUTION_WEIGHTED_RESPONSE_SURFACE_STATUS_20260703.json",
    "weighted_route_rows_606": OUTPUT_DIR
    / "NODI_SIDEWALL_DISTRIBUTION_WEIGHTED_RESPONSE_SURFACE_ROUTE_WEIGHTED_SYNTHESIS_ROWS_20260703.csv",
    "weighted_window_rows_606": OUTPUT_DIR
    / "NODI_SIDEWALL_DISTRIBUTION_WEIGHTED_RESPONSE_SURFACE_WINDOW_WEIGHT_ROWS_20260703.csv",
    "bridge_recompute_queue_605": OUTPUT_DIR
    / "NODI_SIDEWALL_COMSOL_CROSS_SECTION_DISTRIBUTION_BRIDGE_RECOMPUTE_QUEUE_ROWS_20260703.csv",
    "followup_builder_603": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_followup_window_higher_event_sweep.py",
    "execute_reference_600": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_candidate_envelope_annulus_window_sweep.py",
    "full_recompute_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_sidewall_full_recompute_distribution_weighted_lock.py",
    "full_recompute_tests": PROJECT_ROOT
    / "tests/test_nodi_sidewall_full_recompute_distribution_weighted_lock.py",
}

ALLOWED_USE = (
    "execute or plan full NODI recompute coverage for the sidewall branch, then "
    "lock distribution-weighted dimension, annulus, and interference-response context"
)
BLOCKED_USE = (
    "exact P(x,u) probability claim, route winner, scalar score, final yield, "
    "final detection probability, wet experimental claim, q_ch weighting, true "
    "W_eff, or production runtime ingestion"
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
        description="Build full NODI sidewall recompute distribution-weighted lock."
    )
    parser.add_argument(
        "--confirm-sidewall-full-recompute-distribution-weighted-lock",
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
    output_report = f"reports/607_{PREFIX}_{DATE_STAMP}.md"
    build_edit_paths = {
        "tools/audits/build_nodi_sidewall_full_recompute_distribution_weighted_lock.py",
        "tests/test_nodi_sidewall_full_recompute_distribution_weighted_lock.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "full_recompute_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "full_recompute_output"
            release_decision = "included_or_rewritten_by_full_recompute_builder"
        else:
            classification = "non_full_recompute_dirty_context"
            release_decision = "ignored_for_full_recompute"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def recompute_plan_rows(
    *,
    n_events: int = DEFAULT_N_EVENTS,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in followup_plan_rows(n_events=n_events, random_seed=random_seed):
        source_row_id = row["row_id"]
        recompute_row_id = f"FULL-{source_row_id}"
        item = dict(row)
        item.update(common_guard_fields(recompute_row_id))
        item["source_plan_row_id_603"] = source_row_id
        item["full_recompute_scope"] = (
            "route_window_diameter_trapezoid_sidewall_recompute"
        )
        item["rectangle_baseline_status"] = "preserved_not_overwritten"
        item["distribution_weighting_applied_after_nodi_execution"] = True
        item["weighting_modes_json"] = json.dumps(list(WEIGHTING_MODES), ensure_ascii=True)
        item["execution_status"] = "planned_full_recompute_not_executed"
        rows.append(item)
    return rows


def execute_recompute_rows(plan_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    executed: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for row in plan_rows:
        try:
            result = execute_annulus_row(row)
            result["execution_status"] = "executed_full_nodi_recompute"
            result["full_recompute_scope"] = row["full_recompute_scope"]
            result["rectangle_baseline_status"] = row["rectangle_baseline_status"]
            result["distribution_weighting_applied_after_nodi_execution"] = True
            result["weighting_modes_json"] = row["weighting_modes_json"]
            executed.append(result)
        except Exception as exc:  # pragma: no cover - exercised by integration failures
            failed = dict(row)
            failed["execution_status"] = "failed_full_nodi_recompute"
            failed["failure_type"] = type(exc).__name__
            failed["failure_message"] = str(exc)
            executed.append(failed)
            failures.append(failed)
    return executed, failures


def weighted_recompute_rows(event_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    weights = window_weight_lookup()
    rows: list[dict[str, Any]] = []
    for event in event_rows:
        diameter_nm = fnum(event.get("diameter_nm"))
        profile_diameter = nearest_comsol_profile_diameter(diameter_nm)
        for mode in WEIGHTING_MODES:
            weight = weights[(profile_diameter, event["annulus_window_id"], mode)]
            peak = fnum(event.get("mean_peak_height"))
            snr = fnum(event.get("mean_local_snr"))
            selected_fraction = fnum(event.get("selected_annulus_fraction"))
            rows.append(
                {
                    **common_guard_fields(f"WEIGHTED-{event['row_id']}-{mode}"),
                    "source_full_recompute_row_id": event["row_id"],
                    "source_route_id_nodi": event["source_route_id_nodi"],
                    "candidate_envelope_route_id_nodi": event[
                        "candidate_envelope_route_id_nodi"
                    ],
                    "route_id_role": "full_recompute_weighted_context_not_selection",
                    "annulus_window_id": event["annulus_window_id"],
                    "diameter_nm": event["diameter_nm"],
                    "n_events_requested": event.get("n_events_requested", ""),
                    "n_events_observed": event.get("n_events_observed", ""),
                    "full_recompute_execution_status": event["execution_status"],
                    "weighting_mode": mode,
                    "comsol_weight_profile_diameter_nm": profile_diameter,
                    "window_probability_mass_surrogate": weight,
                    "selected_annulus_fraction": selected_fraction,
                    "weighted_selected_annulus_fraction_surrogate": (
                        selected_fraction * weight
                    ),
                    "mean_peak_height": peak,
                    "mean_local_snr": snr,
                    "weighted_peak_height_contribution": peak * weight,
                    "weighted_local_snr_contribution": snr * weight,
                    "weight_claim_level": (
                        "uniform_surrogate"
                        if mode == "uniform_edge_mass"
                        else "comsol_transport_bin_surrogate_not_exact_pxu"
                    ),
                }
            )
    return rows


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def route_lock_rows(weighted_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in weighted_rows:
        grouped[(row["source_route_id_nodi"], row["weighting_mode"])].append(row)

    rows: list[dict[str, Any]] = []
    for (route_id, mode), group in sorted(grouped.items()):
        by_window: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in group:
            by_window[row["annulus_window_id"]].append(row)
        summaries = []
        for window_id, window_rows in sorted(by_window.items()):
            summaries.append(
                {
                    "window_id": window_id,
                    "mass": mean(
                        [fnum(row["window_probability_mass_surrogate"]) for row in window_rows]
                    ),
                    "peak_contribution": mean(
                        [fnum(row["weighted_peak_height_contribution"]) for row in window_rows]
                    ),
                    "snr_contribution": mean(
                        [fnum(row["weighted_local_snr_contribution"]) for row in window_rows]
                    ),
                }
            )
        canonical = next(
            (item for item in summaries if item["window_id"] == CANONICAL_WINDOW_ID),
            None,
        )
        canonical_mass = canonical["mass"] if canonical else 0.0
        canonical_peak = canonical["peak_contribution"] if canonical else 0.0
        canonical_snr = canonical["snr_contribution"] if canonical else 0.0
        leading_mass = max(summaries, key=lambda item: item["mass"])
        leading_peak = max(summaries, key=lambda item: item["peak_contribution"])
        leading_snr = max(summaries, key=lambda item: item["snr_contribution"])
        executed_count = sum(
            row["full_recompute_execution_status"] == "executed_full_nodi_recompute"
            for row in group
        )
        rows.append(
            {
                **common_guard_fields(f"ROUTE-607-{route_id.replace('/', '_')}-{mode}"),
                "source_route_id_nodi": route_id,
                "weighting_mode": mode,
                "route_id_role": "full_recompute_route_context_not_selection",
                "full_recompute_rows_observed": len(group),
                "full_recompute_rows_executed": executed_count,
                "canonical_window_id": CANONICAL_WINDOW_ID,
                "canonical_window_present": canonical is not None,
                "leading_mass_window_context": leading_mass["window_id"],
                "leading_mass_minus_canonical": leading_mass["mass"] - canonical_mass,
                "leading_peak_contribution_window_context": leading_peak["window_id"],
                "leading_peak_contribution_minus_canonical": (
                    leading_peak["peak_contribution"] - canonical_peak
                ),
                "leading_snr_contribution_window_context": leading_snr["window_id"],
                "leading_snr_contribution_minus_canonical": (
                    leading_snr["snr_contribution"] - canonical_snr
                ),
                "annulus_context_after_full_recompute": (
                    "canonical_window_retained"
                    if leading_mass["window_id"] == CANONICAL_WINDOW_ID
                    else "weighted_mass_context_shifts_from_canonical"
                ),
                "interference_context_after_full_recompute": (
                    "noncanonical_response_contribution_exceeds_canonical"
                    if leading_peak["window_id"] != CANONICAL_WINDOW_ID
                    or leading_snr["window_id"] != CANONICAL_WINDOW_ID
                    else "canonical_response_contribution_retained"
                ),
                "dimension_context_after_full_recompute": (
                    "candidate_envelope_width_context_retained_pending_next_width_sweep"
                ),
                "window_summary_json": json.dumps(summaries, ensure_ascii=True),
            }
        )
    return rows


def question_rows(route_rows: list[dict[str, Any]], *, execute_nodi: bool) -> list[dict[str, Any]]:
    comsol_rows = [
        row for row in route_rows if row["weighting_mode"] != "uniform_edge_mass"
    ]
    annulus_shift = sum(
        row["annulus_context_after_full_recompute"]
        == "weighted_mass_context_shifts_from_canonical"
        for row in comsol_rows
    )
    response_shift = sum(
        row["interference_context_after_full_recompute"]
        == "noncanonical_response_contribution_exceeds_canonical"
        for row in comsol_rows
    )
    mode_text = "executed" if execute_nodi else "planned"
    return [
        {
            **common_guard_fields("QUESTION-607-DIMENSION"),
            "question_id": "size_recommendation_delta_after_sidewall",
            "answer_context": (
                f"full NODI recompute branch {mode_text}; candidate envelope widths "
                "remain the active sidewall dimensions until the next width sweep"
            ),
            "rectangle_baseline_status": "preserved_not_overwritten",
            "next_action": "608_width_sweep_with_distribution_weights",
        },
        {
            **common_guard_fields("QUESTION-607-ANNULUS"),
            "question_id": "selected_annulus_range_delta_after_sidewall",
            "answer_context": (
                "COMSOL transport-bin weighting keeps annulus context active after full recompute"
            ),
            "comsol_weighted_route_mode_rows_with_annulus_shift": annulus_shift,
            "next_action": "608_width_sweep_keep_annulus_weight_modes",
        },
        {
            **common_guard_fields("QUESTION-607-INTERFERENCE"),
            "question_id": "interference_response_delta_after_sidewall",
            "answer_context": (
                "weighted peak/local-SNR contribution remains active after full recompute"
            ),
            "comsol_weighted_route_mode_rows_with_response_shift": response_shift,
            "next_action": "608_compare_weighted_response_against_width_sweep",
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

    event_rows = payload["full_recompute_event_rows"]
    weighted_rows = payload["weighted_recompute_rows"]
    route_rows = payload["route_lock_rows"]
    execute_nodi = payload["execute_nodi"]
    expected_event_rows = 208
    expected_weighted_rows = expected_event_rows * len(WEIGHTING_MODES)
    executed_rows = sum(
        row["execution_status"] == "executed_full_nodi_recompute" for row in event_rows
    )

    add(
        "full_recompute_covers_route_window_diameter_grid",
        len(event_rows) == expected_event_rows,
        f"full_recompute_event_rows={len(event_rows)}",
    )
    add(
        "weighted_rows_cover_three_modes",
        len(weighted_rows) == expected_weighted_rows
        and {row["weighting_mode"] for row in weighted_rows} == set(WEIGHTING_MODES),
        f"weighted_recompute_rows={len(weighted_rows)}",
    )
    add(
        "route_lock_covers_six_routes_times_three_modes",
        len(route_rows) == 6 * len(WEIGHTING_MODES),
        f"route_lock_rows={len(route_rows)}",
    )
    add(
        "execution_status_matches_mode",
        (executed_rows == expected_event_rows if execute_nodi else executed_rows == 0),
        f"execute_nodi={execute_nodi}; executed_rows={executed_rows}",
    )
    add(
        "rectangle_baseline_preserved",
        all(
            row.get("rectangle_baseline_status") == "preserved_not_overwritten"
            for row in event_rows
        ),
        "rectangle branch is not overwritten by sidewall recompute",
    )
    add(
        "v4_assumption_hash_bound",
        all(
            row["comsol_v4_assumption_set_sha256"] == COMSOL_V4_ASSUMPTION_SET_SHA256
            for table in (event_rows, weighted_rows, route_rows)
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
    for table_name in (
        "full_recompute_event_rows",
        "weighted_recompute_rows",
        "route_lock_rows",
        "question_rows",
    ):
        rows = payload[table_name]
        columns = set().union(*(set(row) for row in rows)) if rows else set()
        if FORBIDDEN_PRIMARY_COLUMNS.intersection(columns):
            return False
    return True


def manifest_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.append(
            {
                "artifact_id": ARTIFACT_ID,
                "path": display_path(path),
                "sha256": sha256_file(path) if path.exists() else "",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def build_payload(
    *,
    execute_nodi: bool = False,
    n_events: int = DEFAULT_N_EVENTS,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> dict[str, Any]:
    plan = recompute_plan_rows(n_events=n_events, random_seed=random_seed)
    failures: list[dict[str, Any]] = []
    if execute_nodi:
        event_rows, failures = execute_recompute_rows(plan)
        disposition = DISPOSITION_EXECUTED
    else:
        event_rows = plan
        disposition = DISPOSITION_PLAN
    weighted_rows = weighted_recompute_rows(event_rows)
    route_rows = route_lock_rows(weighted_rows)
    q_rows = question_rows(route_rows, execute_nodi=execute_nodi)
    source_rows = source_lock_rows()
    dirty_rows = dirty_context_rows()
    payload: dict[str, Any] = {
        "artifact_id": ARTIFACT_ID,
        "synthesis_version": SYNTHESIS_VERSION,
        "date_stamp": DATE_STAMP,
        "disposition": disposition,
        "claim_boundary": CLAIM_BOUNDARY,
        "git_head": git_head(),
        "git_branch": git_branch(),
        "execute_nodi": execute_nodi,
        "n_events": n_events,
        "random_seed": random_seed,
        "comsol_v4_assumption_set_id": COMSOL_V4_ASSUMPTION_SET_ID,
        "comsol_v4_assumption_set_version": COMSOL_V4_ASSUMPTION_SET_VERSION,
        "comsol_v4_assumption_set_sha256": COMSOL_V4_ASSUMPTION_SET_SHA256,
        "summary": {
            "full_recompute_event_rows": len(event_rows),
            "full_recompute_failures": len(failures),
            "full_recompute_executed_rows": sum(
                row["execution_status"] == "executed_full_nodi_recompute"
                for row in event_rows
            ),
            "weighted_recompute_rows": len(weighted_rows),
            "route_lock_rows": len(route_rows),
            "question_rows": len(q_rows),
            "rectangle_baseline_status": "preserved_not_overwritten",
            "exact_pxu_probability_grid_available_now": False,
            "next_executable_block": "608_width_sweep_with_distribution_weights",
        },
        "full_recompute_event_rows": event_rows,
        "weighted_recompute_rows": weighted_rows,
        "route_lock_rows": route_rows,
        "question_rows": q_rows,
        "failure_rows": failures
        or [
            {
                "row_id": "NO_FAILURES",
                "execution_status": "no_failures",
                "failure_type": "",
                "failure_message": "",
            }
        ],
        "source_lock_rows": source_rows,
        "dirty_context_rows": dirty_rows,
    }
    validation = validation_rows(payload)
    payload["validation_rows"] = validation
    payload["summary"]["failed_validation_rows"] = sum(
        1 for row in validation if row["status"] != "pass"
    )
    if failures or payload["summary"]["failed_validation_rows"]:
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
    failures: list[str] = []
    for row in payload["validation_rows"]:
        if row["status"] != "pass":
            failures.append(f"{row['check_id']}: {row['detail']}")
    return failures


def render_report(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# NODI sidewall full recompute distribution-weighted lock",
        "",
        "## Mainline",
        "",
        (
            "This artifact turns the 605/606 bridge into full route-window-diameter "
            "NODI recompute coverage for the trapezoid sidewall branch, then applies "
            "uniform and COMSOL transport-bin weights to the recomputed response rows."
        ),
        "",
        "## Counts",
        "",
        f"- execution mode: {'executed' if payload['execute_nodi'] else 'plan-only'}",
        f"- NODI recompute rows: {summary['full_recompute_event_rows']}",
        f"- executed rows: {summary['full_recompute_executed_rows']}",
        f"- weighted rows: {summary['weighted_recompute_rows']}",
        f"- route lock rows: {summary['route_lock_rows']}",
        f"- failed validation rows: {summary['failed_validation_rows']}",
        "",
        "## Route",
        "",
        (
            "The rectangle baseline is preserved, the trapezoid branch is recomputed, "
            "and the next block is a width sweep with the same distribution-weighted "
            "annulus and interference-response context."
        ),
        "",
    ]
    return "\n".join(lines)


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_{DATE_STAMP}.json"
    report_json_path = OUTPUT_DIR / f"{PREFIX}_REPORT_{DATE_STAMP}.json"
    event_path = OUTPUT_DIR / f"{PREFIX}_FULL_RECOMPUTE_EVENT_ROWS_{DATE_STAMP}.csv"
    weighted_path = OUTPUT_DIR / f"{PREFIX}_WEIGHTED_RECOMPUTE_ROWS_{DATE_STAMP}.csv"
    route_path = OUTPUT_DIR / f"{PREFIX}_ROUTE_LOCK_ROWS_{DATE_STAMP}.csv"
    question_path = OUTPUT_DIR / f"{PREFIX}_QUESTION_ROWS_{DATE_STAMP}.csv"
    failure_path = OUTPUT_DIR / f"{PREFIX}_FAILURE_ROWS_{DATE_STAMP}.csv"
    validation_path = OUTPUT_DIR / f"{PREFIX}_VALIDATION_ROWS_{DATE_STAMP}.csv"
    source_lock_path = OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_{DATE_STAMP}.csv"
    dirty_path = OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_{DATE_STAMP}.csv"
    manifest_path = OUTPUT_DIR / f"{PREFIX}_MANIFEST_{DATE_STAMP}.csv"
    report_md_path = REPORT_DIR / f"607_{PREFIX}_{DATE_STAMP}.md"

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
            "execute_nodi",
            "n_events",
            "random_seed",
            "comsol_v4_assumption_set_id",
            "comsol_v4_assumption_set_version",
            "comsol_v4_assumption_set_sha256",
            "summary",
            "payload_sha256",
        )
    }
    write_json_atomic(status_path, status_payload, sort_keys=True)
    write_json_atomic(report_json_path, payload, sort_keys=True)
    write_csv_rows(event_path, payload["full_recompute_event_rows"])
    write_csv_rows(weighted_path, payload["weighted_recompute_rows"])
    write_csv_rows(route_path, payload["route_lock_rows"])
    write_csv_rows(question_path, payload["question_rows"])
    write_csv_rows(failure_path, payload["failure_rows"])
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
        event_path,
        weighted_path,
        route_path,
        question_path,
        failure_path,
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
    if not args.confirm_sidewall_full_recompute_distribution_weighted_lock:
        print(
            "--confirm-sidewall-full-recompute-distribution-weighted-lock is required",
            file=sys.stderr,
        )
        return 2
    payload = build_payload(
        execute_nodi=args.execute_nodi,
        n_events=args.n_events,
        random_seed=args.random_seed,
    )
    failures = validate_payload(payload)
    paths = write_outputs(payload)
    print(json.dumps(payload["summary"], sort_keys=True))
    for path in paths:
        print(display_path(path))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
