#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows, write_json_atomic  # noqa: E402
from nodi_simulator.sidewall_qch_grid_validation import (  # noqa: E402
    SIDEWALL_QCH_GRID_VALIDATION_CLAIM_BOUNDARY,
    SIDEWALL_QCH_GRID_VALIDATION_VERSION,
    build_sidewall_qch_convergence_rows,
    build_sidewall_qch_grid_rows,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH_READY_CANDIDATE_ONLY"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
PRESSURE_DROP_PA = 1000.0

ALLOWED_USE = (
    "W500/D900 qch grid-refinement evidence;flow-split promotion planning;"
    "integrated ledger lane update input"
)
BLOCKED_USE = (
    "formal_qch_weighting;route_score;winner;JRC;yield;detection_probability;"
    "absolute calibrated q_ch;wet pass;fabrication release;production ingestion"
)

FLOW_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_STATUS_20260701.json"
QCH_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_STATUS_20260701.json"
LEDGER_REFRESH_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_REFRESH_STATUS_20260701.json"
)

SOURCE_FILES = {
    "flow_solver_candidate_status": FLOW_STATUS,
    "qch_sidecar_candidate_status": QCH_STATUS,
    "integrated_promotion_ledger_refresh_status": LEDGER_REFRESH_STATUS,
    "sidewall_qch_grid_validation_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_qch_grid_validation.py",
    "sidewall_qch_grid_validation_tests": PROJECT_ROOT
    / "tests/test_sidewall_qch_grid_validation.py",
    "sidewall_qch_grid_validation_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_qch_grid_validation_refresh.py",
    "sidewall_qch_grid_validation_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_qch_grid_validation_refresh.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/sidewall_qch_grid_validation.py",
    "tests/test_sidewall_qch_grid_validation.py",
    "tools/audits/build_nodi_package_c_sidewall_qch_grid_validation_refresh.py",
    "tests/test_nodi_package_c_sidewall_qch_grid_validation_refresh.py",
    "reports/100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
}

STALE_POST_RC2_PATHS = {
    "reports/517_NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_20260701.md",
    "reports/joint_interface_20260701/NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.md",
    "tests/test_nodi_package_c_post_rc2_delta_release.py",
    "tools/audits/build_nodi_package_c_post_rc2_delta_release.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build W500/D900 sidewall qch grid-validation refresh packet."
    )
    parser.add_argument("--confirm-sidewall-qch-grid-validation-refresh", action="store_true")
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
    if path.is_relative_to(PROJECT_ROOT):
        return path.relative_to(PROJECT_ROOT).as_posix()
    return str(path)


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def release_scoped_path(path: str) -> bool:
    source_paths = {
        display_path(source_path)
        for source_path in SOURCE_FILES.values()
        if source_path.exists()
    }
    return (
        path in source_paths
        or path in BUILD_EDIT_PATHS
        or path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH_"
        )
        or path
        == "reports/533_NODI_PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "sidewall_qch_grid_validation_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH_"
        ) or path == "reports/533_NODI_PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH_20260701.md":
            classification = "sidewall_qch_grid_validation_output"
            release_decision = "included_or_rewritten_by_sidewall_qch_grid_validation"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_sidewall_qch_grid_validation"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_sidewall_qch_grid_validation_not_source_locked"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source_id, path in SOURCE_FILES.items():
        exists = path.exists()
        rows.append(
            {
                "source_id": source_id,
                "path": display_path(path) if exists else str(path),
                "exists": str(exists).lower(),
                "sha256": sha256_file(path) if exists else "",
                "claim_boundary": SIDEWALL_QCH_GRID_VALIDATION_CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def _stringify_row(row: dict[str, Any]) -> dict[str, str]:
    return {key: _stringify(value) for key, value in row.items()}


def _stringify(value: Any) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.12g}"
    return str(value)


def grid_rows() -> list[dict[str, str]]:
    rows = build_sidewall_qch_grid_rows(pressure_drop_Pa=PRESSURE_DROP_PA)
    return [_stringify_row(row.to_dict()) for row in rows]


def convergence_rows() -> list[dict[str, str]]:
    rows = build_sidewall_qch_grid_rows(pressure_drop_Pa=PRESSURE_DROP_PA)
    convergence = build_sidewall_qch_convergence_rows(rows, reference_grid_nx=41)
    return [_stringify_row(row.to_dict()) for row in convergence]


def promotion_update_rows() -> list[dict[str, str]]:
    return [
        {
            "target_ledger_lane": "flow_split_qch",
            "previous_status": "candidate_flow_split_not_formal_qch_weighting",
            "new_context_status": (
                "w500_d900_grid_refined_split_candidate_absolute_q_requires_validation"
            ),
            "source_artifact": (
                "reports/joint_interface_20260701/"
                f"{PREFIX}_CONVERGENCE_ROWS_20260701.csv"
            ),
            "target_claim_current": "false",
            "blocked_promotion": "formal_qch_weighting;route_score;winner;yield;detection_probability",
            "hard_fail_if": "grid_refined_split_candidate_promoted_to_formal_qch_or_route_score",
            "next_required_evidence": (
                "exact COMSOL or measurement pressure-flow validation and route policy audit"
            ),
            "claim_boundary": SIDEWALL_QCH_GRID_VALIDATION_CLAIM_BOUNDARY,
        }
    ]


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "grid_rows": payload["grid_rows"],
        "convergence_rows": payload["convergence_rows"],
        "promotion_update_rows": payload["promotion_update_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    flow_status = load_json(FLOW_STATUS)
    qch_status = load_json(QCH_STATUS)
    ledger_refresh_status = load_json(LEDGER_REFRESH_STATUS)
    rows = grid_rows()
    conv = convergence_rows()
    updates = promotion_update_rows()
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    max_split_delta = max(
        float(row["split_fraction_abs_delta_vs_reference"]) for row in conv
    )
    max_q_delta = max(float(row["q_ch_relative_delta_vs_reference"]) for row in conv)
    split_pass_rows = sum(
        row["split_candidate_convergence_status"] == "candidate_pass" for row in conv
    )
    q_review_rows = sum(
        row["absolute_q_convergence_status"] == "candidate_review_required" for row in conv
    )
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and flow_status.get("disposition")
        == "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_READY_NOT_QCH"
        and qch_status.get("disposition")
        == "NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_READY_NOT_ROUTE"
        and ledger_refresh_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_REFRESH_READY_PREFLIGHT_ONLY"
        and len(rows) == 9
        and len(conv) == 6
        and split_pass_rows == 6
        and max_split_delta <= 0.01
        and q_review_rows >= 1
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": SIDEWALL_QCH_GRID_VALIDATION_CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "qch_grid_validation_version": SIDEWALL_QCH_GRID_VALIDATION_VERSION,
        "source_flow_disposition": flow_status.get("disposition", ""),
        "source_qch_disposition": qch_status.get("disposition", ""),
        "source_ledger_refresh_disposition": ledger_refresh_status.get("disposition", ""),
        "grid_rows": len(rows),
        "convergence_rows": len(conv),
        "promotion_update_rows": len(updates),
        "split_candidate_pass_rows": split_pass_rows,
        "absolute_q_review_rows": q_review_rows,
        "max_split_fraction_abs_delta_vs_reference": max_split_delta,
        "max_q_ch_relative_delta_vs_reference": max_q_delta,
        "split_candidate_current": True,
        "absolute_qch_calibration_current": False,
        "formal_qch_weighting_current": False,
        "route_score_current": False,
        "winner_current": False,
        "yield_detection_probability_current": False,
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context" for row in dirty_context
        ),
        "release_scoped_dirty_blocker_rows": release_dirty_blockers,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "grid_rows": rows,
        "convergence_rows": conv,
        "promotion_update_rows": updates,
        "source_lock": source_lock,
        "dirty_context": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    checks = {
        "disposition pass": summary["disposition"] == DISPOSITION,
        "source lock complete": summary["source_missing_rows"] == 0,
        "release dirty blockers absent": summary["release_scoped_dirty_blocker_rows"] == 0,
        "grid rows": summary["grid_rows"] == 9,
        "convergence rows": summary["convergence_rows"] == 6,
        "split pass": summary["split_candidate_pass_rows"] == 6,
        "q review retained": summary["absolute_q_review_rows"] >= 1,
        "formal qch false": summary["formal_qch_weighting_current"] is False,
        "route false": summary["route_score_current"] is False,
        "detection false": summary["yield_detection_probability_current"] is False,
    }
    for row in payload["promotion_update_rows"]:
        checks[f"promotion update remains false {row['target_ledger_lane']}"] = (
            row["target_claim_current"] == "false"
            and "route_score" in row["blocked_promotion"]
            and "detection_probability" in row["blocked_promotion"]
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    grid_path = OUTPUT_DIR / f"{PREFIX}_GRID_ROWS_20260701.csv"
    write_csv_rows(grid_path, payload["grid_rows"])
    paths.append(grid_path)

    convergence_path = OUTPUT_DIR / f"{PREFIX}_CONVERGENCE_ROWS_20260701.csv"
    write_csv_rows(convergence_path, payload["convergence_rows"])
    paths.append(convergence_path)

    update_path = OUTPUT_DIR / f"{PREFIX}_PROMOTION_UPDATE_ROWS_20260701.csv"
    write_csv_rows(update_path, payload["promotion_update_rows"])
    paths.append(update_path)

    source_lock_path = OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv"
    write_csv_rows(source_lock_path, payload["source_lock"])
    paths.append(source_lock_path)

    dirty_path = OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv"
    write_csv_rows(dirty_path, payload["dirty_context"])
    paths.append(dirty_path)

    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json"
    write_json_atomic(status_path, {"disposition": DISPOSITION, "summary": payload["summary"]})
    paths.append(status_path)

    report_path = OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json"
    write_json_atomic(report_path, payload)
    paths.append(report_path)

    public_report = REPORT_DIR / "533_NODI_PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH_20260701.md"
    public_report.write_text(report_markdown(payload), encoding="utf-8", newline="\n")
    paths.append(public_report)

    manifest_path = OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv"
    write_csv_rows(manifest_path, manifest_rows(paths, manifest_path))
    paths.append(manifest_path)
    return paths


def report_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    return "\n".join(
        [
            "# NODI Package C Sidewall QCH Grid Validation Refresh",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Grid rows: `{s['grid_rows']}`.",
            f"- Convergence rows: `{s['convergence_rows']}`.",
            f"- Max split-fraction delta vs 41-grid reference: `{s['max_split_fraction_abs_delta_vs_reference']}`.",
            f"- Max absolute q_ch delta vs 41-grid reference: `{s['max_q_ch_relative_delta_vs_reference']}`.",
            "- Flow split is candidate-stable for W500/D900, but absolute calibrated q_ch remains false.",
            "- Formal q_ch weighting, route score, winner/JRC, yield, and detection probability remain false.",
            "",
        ]
    )


def manifest_rows(paths: list[Path], manifest_path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        rows.append(
            {
                "artifact": path.name,
                "path": display_path(path),
                "sha256": sha256_file(path),
                "disposition": DISPOSITION,
                "policy_impact": "w500_d900_qch_grid_validation_candidate_not_promotion",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    rows.append(
        {
            "artifact": manifest_path.name,
            "path": display_path(manifest_path),
            "sha256": SELF_MANIFEST_SHA256,
            "disposition": DISPOSITION,
            "policy_impact": "manifest_self_row_no_recursive_sha",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_sidewall_qch_grid_validation_refresh:
        parser.error("--confirm-sidewall-qch-grid-validation-refresh is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_QCH_GRID_VALIDATION_REFRESH")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
