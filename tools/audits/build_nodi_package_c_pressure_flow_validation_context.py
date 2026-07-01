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
WORKSPACE_ROOT = PROJECT_ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.pressure_flow_validation import (  # noqa: E402
    PRESSURE_FLOW_CONTEXT_CLAIM_BOUNDARY,
    PRESSURE_FLOW_VALIDATION_VERSION,
    build_pressure_flow_comparison_rows,
    context_row_from_comsol_summary,
)
from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows, write_json_atomic  # noqa: E402


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_PRESSURE_FLOW_VALIDATION_CONTEXT"
ARTIFACT_ID = "PACKAGE_C_PRESSURE_FLOW_VALIDATION_CONTEXT_20260701"
DISPOSITION = "NODI_PACKAGE_C_PRESSURE_FLOW_VALIDATION_CONTEXT_READY_NOT_FORMAL_QCH"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_PRESSURE_FLOW_VALIDATION_CONTEXT_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

QCH_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_STATUS_20260701.json"
QCH_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_QCH_ROWS_20260701.csv"
COMSOL_SUMMARY = (
    WORKSPACE_ROOT
    / "comsol test/comsol_ev_pbs_bonded_cross_junction/full_chip/dwg_analysis/"
    "stage11_explicit_nano_pressure_only_p1b_w800_qch_01_sw85_d0p9_hmax0p5_summary.csv"
)

ALLOWED_USE = (
    "COMSOL pressure-flow context comparison;formal q_ch sidecar validation preflight;"
    "route/yield/detection promotion planning"
)
BLOCKED_USE = (
    "formal q_ch acceptance without exact geometry/route match;route_score;winner;JRC;"
    "yield;detection_probability;wet pass claim;fabrication release;production ingestion"
)

SOURCE_FILES = {
    "qch_sidecar_candidate_status": QCH_STATUS,
    "qch_sidecar_candidate_rows": QCH_ROWS,
    "comsol_pressure_flow_summary_context": COMSOL_SUMMARY,
    "pressure_flow_validation_source": PROJECT_ROOT / "nodi_simulator/pressure_flow_validation.py",
    "pressure_flow_validation_tests": PROJECT_ROOT / "tests/test_pressure_flow_validation.py",
    "pressure_flow_validation_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_pressure_flow_validation_context.py",
    "pressure_flow_validation_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_pressure_flow_validation_context.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/pressure_flow_validation.py",
    "tests/test_pressure_flow_validation.py",
    "tools/audits/build_nodi_package_c_pressure_flow_validation_context.py",
    "tests/test_nodi_package_c_pressure_flow_validation_context.py",
    "reports/100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
}

STALE_POST_RC2_PATHS = {
    "reports/517_NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_20260701.md",
    "reports/joint_interface_20260701/NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.md",
    "tests/test_nodi_package_c_post_rc2_delta_release.py",
    "tools/audits/build_nodi_package_c_post_rc2_delta_release.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build pressure-flow validation context packet.")
    parser.add_argument("--confirm-pressure-flow-validation-context", action="store_true")
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
        if path.is_relative_to(PROJECT_ROOT):
            return path.relative_to(PROJECT_ROOT).as_posix()
        if path.is_relative_to(WORKSPACE_ROOT):
            return path.relative_to(WORKSPACE_ROOT).as_posix()
    except ValueError:
        pass
    return str(path)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def release_scoped_path(path: str) -> bool:
    source_paths = {
        display_path(source_path)
        for source_path in SOURCE_FILES.values()
        if source_path.exists()
    }
    return (
        path in source_paths
        or path in BUILD_EDIT_PATHS
        or path.startswith("reports/joint_interface_20260701/NODI_PACKAGE_C_PRESSURE_FLOW_VALIDATION_CONTEXT_")
        or path == "reports/523_NODI_PACKAGE_C_PRESSURE_FLOW_VALIDATION_CONTEXT_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "pressure_flow_validation_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith("reports/joint_interface_20260701/NODI_PACKAGE_C_PRESSURE_FLOW_VALIDATION_CONTEXT_") or path == "reports/523_NODI_PACKAGE_C_PRESSURE_FLOW_VALIDATION_CONTEXT_20260701.md":
            classification = "pressure_flow_validation_output"
            release_decision = "included_or_rewritten_by_pressure_flow_validation_context"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_pressure_flow_validation_context"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_pressure_flow_validation_context_not_source_locked"
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
                "claim_boundary": PRESSURE_FLOW_CONTEXT_CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def comsol_context_rows() -> list[dict[str, str]]:
    rows = read_csv_rows(COMSOL_SUMMARY)
    if not rows:
        return []
    context = context_row_from_comsol_summary(
        rows[0],
        comsol_context_id="COMSOL-P1B-W800-SW85-D900-QCH-20260617",
        source_match_level="geometry_family_context_only",
        sidewall_deg_comsol=85.0,
        depth_nm=900.0,
        top_width_nm=800.0,
        route_family="p1b_w800_qch_sw85_d0p9_hmax0p5",
    )
    context["source_artifact"] = display_path(COMSOL_SUMMARY)
    context["source_sha256"] = sha256_file(COMSOL_SUMMARY)
    context["source_row_count"] = str(len(rows))
    return [_stringify_row(context)]


def comparison_rows() -> list[dict[str, str]]:
    qch_rows = read_csv_rows(QCH_ROWS)
    context = comsol_context_rows()
    comparisons = build_pressure_flow_comparison_rows(qch_rows, context)
    return [_stringify_row(row.to_dict()) for row in comparisons]


def promotion_blockers() -> list[dict[str, str]]:
    blockers = [
        (
            "formal_gate2_qch_sidecar",
            "exact_geometry_and_route_match plus accepted pressure-flow comparison",
        ),
        ("route_score", "formal q_ch sidecar plus Package D route precheck"),
        ("winner_or_JRC", "route score audit plus independent decision ledger"),
        (
            "yield_detection_probability",
            "wet/EV evidence contract plus optical/detection calibration",
        ),
    ]
    return [
        {
            "promotion_target": target,
            "current_value": "false",
            "implementation_authorized": "true",
            "context_evidence_available": "true",
            "required_evidence_before_true": evidence,
            "hard_fail_if": f"{target}_true_from_context_only_comparison",
        }
        for target, evidence in blockers
    ]


def self_review_rows() -> list[dict[str, str]]:
    topics = [
        "COMSOL pressure-flow context file exists and is source locked",
        "q_ch candidate rows are compared at COMSOL pressure drop",
        "geometry-family context is not promoted to formal q_ch",
        "route/yield/detection remain promotion targets",
        "no COMSOL launch or mph load was required for existing context ingestion",
    ]
    return [
        {
            "review_id": f"PRESSURE-FLOW-SELF-{index:02d}",
            "dimension": topic,
            "verdict": "PASS_PRESSURE_FLOW_CONTEXT_NOT_FORMAL_QCH",
            "notes": "Existing COMSOL context advances validation but does not replace exact geometry/route evidence.",
        }
        for index, topic in enumerate(topics, start=1)
    ]


def build_payload() -> dict[str, Any]:
    qch_status = load_json(QCH_STATUS)
    context = comsol_context_rows()
    comparisons = comparison_rows()
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    context_only_rows = sum(
        row["validation_status"] == "context_only_not_formal_validation"
        for row in comparisons
    )
    formal_candidate_rows = sum(
        row["validation_status"] == "formal_validation_candidate"
        for row in comparisons
    )
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and qch_status.get("disposition")
        == "NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_READY_NOT_ROUTE"
        and len(context) == 1
        and len(comparisons) >= 2
        and context_only_rows == len(comparisons)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": PRESSURE_FLOW_CONTEXT_CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "validation_version": PRESSURE_FLOW_VALIDATION_VERSION,
        "source_qch_sidecar_disposition": qch_status.get("disposition", ""),
        "comsol_context_rows": len(context),
        "comparison_rows": len(comparisons),
        "context_only_comparison_rows": context_only_rows,
        "formal_validation_candidate_rows": formal_candidate_rows,
        "formal_gate2_qch_sidecar_current": False,
        "route_score_current": False,
        "winner_current": False,
        "yield_detection_probability_current": False,
        "comsol_launch_started": False,
        "mph_load_started": False,
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
        "comsol_context": context,
        "comparison_rows": comparisons,
        "promotion_blockers": promotion_blockers(),
        "source_lock": source_lock,
        "dirty_context": dirty_context,
        "self_review": self_review_rows(),
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "comsol_context": payload["comsol_context"],
        "comparison_rows": payload["comparison_rows"],
        "promotion_blockers": payload["promotion_blockers"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    failures: list[str] = []
    checks = {
        "disposition pass": summary["disposition"] == DISPOSITION,
        "source lock complete": summary["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": summary["release_scoped_dirty_blocker_rows"] == 0,
        "context row present": summary["comsol_context_rows"] == 1,
        "comparison rows present": summary["comparison_rows"] >= 2,
        "context only not promoted": summary["formal_validation_candidate_rows"] == 0,
        "formal qch not current": summary["formal_gate2_qch_sidecar_current"] is False,
        "route score not current": summary["route_score_current"] is False,
        "no COMSOL launch": summary["comsol_launch_started"] is False,
        "no MPH load": summary["mph_load_started"] is False,
    }
    for row in payload["comparison_rows"]:
        checks[f"context only row {row['comparison_id']}"] = (
            row["validation_status"] == "context_only_not_formal_validation"
            and row["formal_qch_sidecar_current"] == "false"
            and row["route_score_current"] == "false"
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        f"{PREFIX}_COMSOL_CONTEXT_20260701.csv": payload["comsol_context"],
        f"{PREFIX}_COMPARISON_ROWS_20260701.csv": payload["comparison_rows"],
        f"{PREFIX}_PROMOTION_BLOCKERS_20260701.csv": payload["promotion_blockers"],
        f"{PREFIX}_SOURCE_LOCK_20260701.csv": payload["source_lock"],
        f"{PREFIX}_DIRTY_CONTEXT_20260701.csv": payload["dirty_context"],
        f"{PREFIX}_SELF_REVIEW_20260701.csv": payload["self_review"],
    }
    for filename, rows in csv_payloads.items():
        path = OUTPUT_DIR / filename
        write_csv_rows(path, rows)
        paths.append(path)

    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json"
    write_json_atomic(status_path, {"disposition": DISPOSITION, "summary": payload["summary"]})
    paths.append(status_path)

    report_json = OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json"
    write_json_atomic(report_json, payload)
    paths.append(report_json)

    public_report = REPORT_DIR / "523_NODI_PACKAGE_C_PRESSURE_FLOW_VALIDATION_CONTEXT_20260701.md"
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
            "# NODI Package C Pressure-Flow Validation Context",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Validation version: `{s['validation_version']}`.",
            f"- Source q_ch sidecar disposition: `{s['source_qch_sidecar_disposition']}`.",
            f"- COMSOL context rows: `{s['comsol_context_rows']}`.",
            f"- Comparison rows: `{s['comparison_rows']}`.",
            f"- Context-only rows: `{s['context_only_comparison_rows']}`.",
            "- Existing COMSOL sw85/d0.9 pressure-flow evidence is ingested as geometry-family context, not exact formal q_ch validation for the W500 candidate rows.",
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
                "policy_impact": "pressure_flow_context_not_formal_qch",
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


def _stringify_row(row: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in row.items():
        if isinstance(value, bool):
            out[key] = str(value).lower()
        elif isinstance(value, float):
            out[key] = f"{value:.12g}"
        else:
            out[key] = str(value)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_pressure_flow_validation_context:
        parser.error("--confirm-pressure-flow-validation-context is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_PRESSURE_FLOW_VALIDATION_CONTEXT")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
