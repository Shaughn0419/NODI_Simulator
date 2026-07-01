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

from nodi_simulator.qch_sidecar import (  # noqa: E402
    QCH_SIDECAR_CLAIM_BOUNDARY,
    QCH_SIDECAR_VERSION,
    build_qch_sidecar_candidates,
)
from nodi_simulator.realism_v2_io import sha256_file, write_csv_rows, write_json_atomic  # noqa: E402


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE"
ARTIFACT_ID = "PACKAGE_C_QCH_SIDECAR_CANDIDATE_20260701"
DISPOSITION = "NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_READY_NOT_ROUTE"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
PRESSURE_DROP_PA = 1000.0

ALLOWED_USE = (
    "candidate q_ch sidecar evidence;fixed-pressure flow split preflight;"
    "route/yield/detection promotion contract input"
)
BLOCKED_USE = (
    "formal route_score;winner;JRC;yield;detection_probability;wet pass claim;"
    "fabrication release;production ingestion;COMSOL validation claim without comparison hash"
)

FLOW_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_STATUS_20260701.json"
FLOW_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_SOLVER_ROWS_20260701.csv"

SOURCE_FILES = {
    "flow_solver_candidate_status": FLOW_STATUS,
    "flow_solver_candidate_rows": FLOW_ROWS,
    "qch_sidecar_source": PROJECT_ROOT / "nodi_simulator/qch_sidecar.py",
    "qch_sidecar_tests": PROJECT_ROOT / "tests/test_qch_sidecar.py",
    "qch_sidecar_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_qch_sidecar_candidate.py",
    "qch_sidecar_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_qch_sidecar_candidate.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/qch_sidecar.py",
    "tests/test_qch_sidecar.py",
    "tools/audits/build_nodi_package_c_qch_sidecar_candidate.py",
    "tests/test_nodi_package_c_qch_sidecar_candidate.py",
    "reports/100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
}

STALE_POST_RC2_PATHS = {
    "reports/517_NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_20260701.md",
    "reports/joint_interface_20260701/NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.md",
    "tests/test_nodi_package_c_post_rc2_delta_release.py",
    "tools/audits/build_nodi_package_c_post_rc2_delta_release.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build q_ch sidecar candidate packet.")
    parser.add_argument("--confirm-qch-sidecar-candidate", action="store_true")
    parser.add_argument("--pressure-drop-Pa", type=float, default=PRESSURE_DROP_PA)
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
        or path.startswith("reports/joint_interface_20260701/NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_")
        or path == "reports/522_NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "qch_sidecar_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith("reports/joint_interface_20260701/NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_") or path == "reports/522_NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_20260701.md":
            classification = "qch_sidecar_candidate_output"
            release_decision = "included_or_rewritten_by_qch_sidecar_candidate"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_qch_sidecar_candidate"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_qch_sidecar_candidate_not_source_locked"
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
                "claim_boundary": QCH_SIDECAR_CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def qch_rows(pressure_drop_Pa: float) -> list[dict[str, str]]:
    source_sha = sha256_file(FLOW_ROWS) if FLOW_ROWS.exists() else ""
    source_rows = read_csv_rows(FLOW_ROWS)
    candidates = build_qch_sidecar_candidates(
        source_rows,
        pressure_drop_Pa=pressure_drop_Pa,
    )
    rows: list[dict[str, str]] = []
    for candidate in candidates:
        row = candidate.to_dict()
        row["source_artifact"] = display_path(FLOW_ROWS)
        row["source_sha256"] = source_sha
        row["source_row_count"] = str(len(source_rows))
        rows.append(_stringify_row(row))
    return rows


def promotion_contract_rows() -> list[dict[str, str]]:
    contracts = [
        (
            "formal_gate2_qch_sidecar",
            "candidate q_ch rows exist with units, source hash, geometry hash, pressure drop, and normalization basis",
            "pressure-flow calibration or COMSOL comparison evidence hash reviewed",
        ),
        (
            "route_score",
            "accepted q_ch sidecar plus sidewall PRS/EAS Package D precheck",
            "route score formula contract and no-borrowing audit hash",
        ),
        (
            "winner_or_JRC",
            "route_score evidence plus independent route audit",
            "winner/JRC decision ledger with false-positive negative fixtures",
        ),
        (
            "yield_detection_probability",
            "wet/EV evidence contract plus optical/detection calibration",
            "experiment/control evidence hash and assay metadata",
        ),
    ]
    return [
        {
            "promotion_target": target,
            "candidate_evidence_now": "true",
            "current_value": "false",
            "authorization_to_implement": "true",
            "minimum_evidence_before_true": minimum,
            "required_next_evidence": required,
            "hard_fail_if": f"{target}_true_without_required_evidence",
        }
        for target, minimum, required in contracts
    ]


def self_review_rows() -> list[dict[str, str]]:
    topics = [
        "q_ch candidate rows computed from flow solver source hash",
        "open-row flow split normalizes to one",
        "closed geometry remains blocked",
        "formal q_ch sidecar still requires calibration/comparison evidence",
        "route/winner/yield/detection remain separate promotion targets",
    ]
    return [
        {
            "review_id": f"QCH-SIDECAR-SELF-{index:02d}",
            "dimension": topic,
            "verdict": "PASS_QCH_SIDECAR_CANDIDATE_NOT_ROUTE",
            "notes": "Candidate q_ch evidence is present, but route/yield/detection require promotion evidence.",
        }
        for index, topic in enumerate(topics, start=1)
    ]


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "qch_rows": payload["qch_rows"],
        "promotion_contract": payload["promotion_contract"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload(pressure_drop_Pa: float) -> dict[str, Any]:
    flow_status = load_json(FLOW_STATUS)
    rows = qch_rows(pressure_drop_Pa)
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    open_rows = [row for row in rows if row["qch_sidecar_status"] == "candidate_qch_sidecar_row"]
    split_sum = sum(float(row["candidate_flow_split_fraction"]) for row in rows)
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and flow_status.get("disposition")
        == "NODI_PACKAGE_C_TRAPEZOID_FLOW_SOLVER_CANDIDATE_READY_NOT_QCH"
        and len(open_rows) >= 2
        and abs(split_sum - 1.0) <= 1.0e-9
        and all(row["route_score_current"] == "false" for row in rows)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": QCH_SIDECAR_CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "qch_sidecar_version": QCH_SIDECAR_VERSION,
        "source_flow_solver_disposition": flow_status.get("disposition", ""),
        "pressure_drop_Pa": pressure_drop_Pa,
        "qch_candidate_row_count": len(rows),
        "candidate_qch_open_rows": len(open_rows),
        "blocked_qch_rows": len(rows) - len(open_rows),
        "candidate_flow_split_sum": split_sum,
        "candidate_qch_sidecar_current": True,
        "formal_gate2_qch_sidecar_current": False,
        "formal_qch_weighting_current": False,
        "route_score_current": False,
        "winner_current": False,
        "yield_detection_probability_current": False,
        "comsol_validation_claim_current": False,
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
        "qch_rows": rows,
        "promotion_contract": promotion_contract_rows(),
        "source_lock": source_lock,
        "dirty_context": dirty_context,
        "self_review": self_review_rows(),
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    failures: list[str] = []
    checks = {
        "disposition pass": summary["disposition"] == DISPOSITION,
        "source lock complete": summary["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": summary["release_scoped_dirty_blocker_rows"] == 0,
        "open qch rows present": summary["candidate_qch_open_rows"] >= 2,
        "split sum normalized": abs(summary["candidate_flow_split_sum"] - 1.0) <= 1.0e-9,
        "formal qch not promoted": summary["formal_gate2_qch_sidecar_current"] is False,
        "route score not promoted": summary["route_score_current"] is False,
        "yield detection not promoted": summary["yield_detection_probability_current"] is False,
    }
    for row in payload["qch_rows"]:
        checks[f"row has source hash {row['qch_sidecar_id']}"] = bool(row["source_sha256"])
        checks[f"row route false {row['qch_sidecar_id']}"] = row["route_score_current"] == "false"
        checks[f"row winner false {row['qch_sidecar_id']}"] = row["winner_current"] == "false"
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        f"{PREFIX}_QCH_ROWS_20260701.csv": payload["qch_rows"],
        f"{PREFIX}_PROMOTION_CONTRACT_20260701.csv": payload["promotion_contract"],
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

    public_report = REPORT_DIR / "522_NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_20260701.md"
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
            "# NODI Package C q_ch Sidecar Candidate",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Sidecar version: `{s['qch_sidecar_version']}`.",
            f"- Source flow solver disposition: `{s['source_flow_solver_disposition']}`.",
            f"- Pressure drop: `{s['pressure_drop_Pa']}` Pa.",
            f"- Candidate q_ch rows: `{s['candidate_qch_open_rows']}` open, `{s['blocked_qch_rows']}` blocked.",
            f"- Candidate flow split sum: `{s['candidate_flow_split_sum']}`.",
            "- This is candidate q_ch sidecar evidence from the local trapezoid flow solver. Route score, winner/JRC, yield, detection probability, wet-pass, fabrication, and production claims remain promotion-contract targets, not current conclusions.",
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
                "policy_impact": "qch_sidecar_candidate_not_route",
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
    if not args.confirm_qch_sidecar_candidate:
        parser.error("--confirm-qch-sidecar-candidate is required")
    payload = build_payload(float(args.pressure_drop_Pa))
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
