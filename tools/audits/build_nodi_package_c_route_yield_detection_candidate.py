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
from nodi_simulator.route_yield_detection_candidate import (  # noqa: E402
    ROUTE_YIELD_DETECTION_CANDIDATE_VERSION,
    ROUTE_YIELD_DETECTION_CLAIM_BOUNDARY,
    build_route_yield_detection_candidates,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE"
ARTIFACT_ID = "PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_20260701"
DISPOSITION = "NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_READY_NOT_FINAL"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

QCH_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_STATUS_20260701.json"
QCH_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_QCH_ROWS_20260701.csv"
PF_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_PRESSURE_FLOW_VALIDATION_CONTEXT_STATUS_20260701.json"
PF_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_PRESSURE_FLOW_VALIDATION_CONTEXT_COMPARISON_ROWS_20260701.csv"

ALLOWED_USE = (
    "route/yield/detection candidate metric evidence;candidate ordering preflight;"
    "wet/optical evidence gap binding"
)
BLOCKED_USE = (
    "formal route_score;winner;JRC;yield;detection_probability;wet pass claim;"
    "fabrication release;production ingestion"
)

SOURCE_FILES = {
    "qch_sidecar_status": QCH_STATUS,
    "qch_sidecar_rows": QCH_ROWS,
    "pressure_flow_status": PF_STATUS,
    "pressure_flow_comparison_rows": PF_ROWS,
    "route_yield_detection_source": PROJECT_ROOT
    / "nodi_simulator/route_yield_detection_candidate.py",
    "route_yield_detection_tests": PROJECT_ROOT
    / "tests/test_route_yield_detection_candidate.py",
    "route_yield_detection_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_route_yield_detection_candidate.py",
    "route_yield_detection_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_route_yield_detection_candidate.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/route_yield_detection_candidate.py",
    "tests/test_route_yield_detection_candidate.py",
    "tools/audits/build_nodi_package_c_route_yield_detection_candidate.py",
    "tests/test_nodi_package_c_route_yield_detection_candidate.py",
    "reports/100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
}

STALE_POST_RC2_PATHS = {
    "reports/517_NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_20260701.md",
    "reports/joint_interface_20260701/NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.md",
    "tests/test_nodi_package_c_post_rc2_delta_release.py",
    "tools/audits/build_nodi_package_c_post_rc2_delta_release.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build route/yield/detection candidate packet.")
    parser.add_argument("--confirm-route-yield-detection-candidate", action="store_true")
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
        or path.startswith("reports/joint_interface_20260701/NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_")
        or path == "reports/524_NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "route_yield_detection_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith("reports/joint_interface_20260701/NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_") or path == "reports/524_NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_20260701.md":
            classification = "route_yield_detection_output"
            release_decision = "included_or_rewritten_by_route_yield_detection_candidate"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_route_yield_detection_candidate"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_route_yield_detection_candidate_not_source_locked"
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
                "claim_boundary": ROUTE_YIELD_DETECTION_CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def candidate_rows() -> list[dict[str, str]]:
    qch_rows = read_csv_rows(QCH_ROWS)
    pf_rows = read_csv_rows(PF_ROWS)
    rows = build_route_yield_detection_candidates(qch_rows, pf_rows)
    return [_stringify_row(row.to_dict()) for row in rows]


def evidence_gap_rows() -> list[dict[str, str]]:
    gaps = [
        (
            "formal_route_score",
            "accepted formal q_ch sidecar plus exact pressure-flow validation",
        ),
        ("winner_or_JRC", "route-score decision ledger and independent route audit"),
        ("yield", "wet EV pass/recovery controls and sample handling evidence"),
        (
            "detection_probability",
            "optical/reference calibration plus detector response evidence",
        ),
    ]
    return [
        {
            "target": target,
            "current_value": "false",
            "candidate_metric_available": "true",
            "required_evidence_before_true": evidence,
            "hard_fail_if": f"{target}_true_from_candidate_metric_only",
        }
        for target, evidence in gaps
    ]


def self_review_rows() -> list[dict[str, str]]:
    topics = [
        "candidate route metric computed from q_ch flow split and pressure-flow context",
        "candidate sort index is not winner/JRC",
        "wet evidence gap remains explicit",
        "optical detection evidence gap remains explicit",
        "route/yield/detection final claims remain false",
    ]
    return [
        {
            "review_id": f"RYD-SELF-{index:02d}",
            "dimension": topic,
            "verdict": "PASS_ROUTE_YIELD_DETECTION_CANDIDATE_NOT_FINAL",
            "notes": "Candidate metric advances route branch while preserving formal claim boundaries.",
        }
        for index, topic in enumerate(topics, start=1)
    ]


def build_payload() -> dict[str, Any]:
    qch_status = load_json(QCH_STATUS)
    pf_status = load_json(PF_STATUS)
    rows = candidate_rows()
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and qch_status.get("disposition")
        == "NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_READY_NOT_ROUTE"
        and pf_status.get("disposition")
        == "NODI_PACKAGE_C_PRESSURE_FLOW_VALIDATION_CONTEXT_READY_NOT_FORMAL_QCH"
        and len(rows) >= 2
        and all(row["route_score_current"] == "false" for row in rows)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": ROUTE_YIELD_DETECTION_CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "candidate_version": ROUTE_YIELD_DETECTION_CANDIDATE_VERSION,
        "source_qch_sidecar_disposition": qch_status.get("disposition", ""),
        "source_pressure_flow_disposition": pf_status.get("disposition", ""),
        "route_candidate_rows": len(rows),
        "candidate_metric_rows": sum(
            float(row["route_decision_candidate_metric"]) > 0.0 for row in rows
        ),
        "route_score_current": False,
        "winner_current": False,
        "JRC_current": False,
        "yield_current": False,
        "detection_probability_current": False,
        "wet_evidence_current": False,
        "optical_detection_calibration_current": False,
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
        "route_candidate_rows": rows,
        "evidence_gaps": evidence_gap_rows(),
        "source_lock": source_lock,
        "dirty_context": dirty_context,
        "self_review": self_review_rows(),
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "route_candidate_rows": payload["route_candidate_rows"],
        "evidence_gaps": payload["evidence_gaps"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    failures: list[str] = []
    checks = {
        "disposition pass": summary["disposition"] == DISPOSITION,
        "source lock complete": summary["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": summary["release_scoped_dirty_blocker_rows"] == 0,
        "route candidate rows present": summary["route_candidate_rows"] >= 2,
        "candidate metric rows present": summary["candidate_metric_rows"] >= 2,
        "route score false": summary["route_score_current"] is False,
        "winner false": summary["winner_current"] is False,
        "JRC false": summary["JRC_current"] is False,
        "yield false": summary["yield_current"] is False,
        "detection false": summary["detection_probability_current"] is False,
    }
    for row in payload["route_candidate_rows"]:
        checks[f"row not final {row['route_candidate_id']}"] = (
            row["route_score_current"] == "false"
            and row["winner_current"] == "false"
            and row["yield_current"] == "false"
            and row["detection_probability_current"] == "false"
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        f"{PREFIX}_ROUTE_CANDIDATE_ROWS_20260701.csv": payload["route_candidate_rows"],
        f"{PREFIX}_EVIDENCE_GAPS_20260701.csv": payload["evidence_gaps"],
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

    report_path = OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json"
    write_json_atomic(report_path, payload)
    paths.append(report_path)

    public_report = REPORT_DIR / "524_NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_20260701.md"
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
            "# NODI Package C Route/Yield/Detection Candidate",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Candidate version: `{s['candidate_version']}`.",
            f"- Route candidate rows: `{s['route_candidate_rows']}`.",
            f"- Candidate metric rows: `{s['candidate_metric_rows']}`.",
            "- Candidate route metrics are computed from q_ch flow split and pressure-flow context weight. They are not formal route_score, winner/JRC, yield, or detection probability.",
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
                "policy_impact": "route_yield_detection_candidate_not_final",
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
    if not args.confirm_route_yield_detection_candidate:
        parser.error("--confirm-route-yield-detection-candidate is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
