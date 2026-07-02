#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
from nodi_simulator.sidewall_wet_observation_execution_packet import (  # noqa: E402
    SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_CLAIM_BOUNDARY,
    WET_OBSERVATION_EXECUTION_PACKET_READY_STATUS,
    build_wet_observation_execution_packet,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_READY_OBSERVATIONS_REQUIRED"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_CLAIM_BOUNDARY

CONTRACT_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_STATUS_20260701.json"
)
INTAKE_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_STATUS_20260701.json"
)
VALIDATION_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_VALIDATION_HARDENING_STATUS_20260701.json"
)
PROMOTION_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_WET_OBSERVATION_REFRESH_STATUS_20260701.json"
)
WET_OPTICAL_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_STATUS_20260701.json"
)
READINESS_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_STATUS_20260701.json"
)

ALLOWED_USE = (
    "wet observation execution blocker closure;contract/fixture/context inventory;"
    "future accepted wet evidence requirements"
)
BLOCKED_USE = (
    "wet_pass_probability;clogging_rate;time_to_clog;recovery;yield;"
    "detection_probability;route_score;winner;JRC;production ingestion;fabrication release"
)

SOURCE_FILES = {
    "wet_surface_contract_status": CONTRACT_STATUS,
    "wet_observation_intake_status": INTAKE_STATUS,
    "wet_observation_validation_status": VALIDATION_STATUS,
    "integrated_promotion_wet_observation_status": PROMOTION_STATUS,
    "wet_optical_context_status": WET_OPTICAL_STATUS,
    "route_readiness_board_status": READINESS_STATUS,
    "wet_observation_execution_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_wet_observation_execution_packet.py",
    "wet_observation_execution_tests": PROJECT_ROOT
    / "tests/test_sidewall_wet_observation_execution_packet.py",
    "wet_observation_execution_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_wet_observation_execution_packet.py",
    "wet_observation_execution_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_wet_observation_execution_packet.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_wet_observation_execution_packet.py",
    "tests/test_sidewall_wet_observation_execution_packet.py",
    "tools/audits/build_nodi_package_c_sidewall_wet_observation_execution_packet.py",
    "tests/test_nodi_package_c_sidewall_wet_observation_execution_packet.py",
}

STALE_POST_RC2_PATHS = {
    "reports/517_NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_20260701.md",
    "reports/joint_interface_20260701/NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.md",
    "tests/test_nodi_package_c_post_rc2_delta_release.py",
    "tools/audits/build_nodi_package_c_post_rc2_delta_release.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build wet observation execution packet.")
    parser.add_argument(
        "--confirm-sidewall-wet-observation-execution-packet",
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
            "NODI_PACKAGE_C_SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_"
        )
        or path
        == "reports/560_NODI_PACKAGE_C_SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_20260701.md"
    )


def source_locked_path(path: str) -> bool:
    return path in {
        display_path(source_path)
        for source_path in SOURCE_FILES.values()
        if source_path.exists()
    }


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "wet_observation_execution_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_"
        ) or path == (
            "reports/560_NODI_PACKAGE_C_SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_20260701.md"
        ):
            classification = "wet_observation_execution_output"
            release_decision = "included_or_rewritten_by_wet_observation_execution"
        elif source_locked_path(path):
            classification = "source_locked_upstream_dirty_context"
            release_decision = "source_locked_current_workspace_not_in_commit_scope"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_wet_observation_execution"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_wet_observation_execution"
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
                "claim_boundary": CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "execution_rows": payload["execution_rows"],
        "claim_guard_rows": payload["claim_guard_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    contract = load_json(CONTRACT_STATUS)
    intake = load_json(INTAKE_STATUS)
    validation = load_json(VALIDATION_STATUS)
    promotion = load_json(PROMOTION_STATUS)
    wet_optical = load_json(WET_OPTICAL_STATUS)
    readiness = load_json(READINESS_STATUS)
    execution_rows, guard_rows = build_wet_observation_execution_packet(
        contract_status=contract,
        intake_status=intake,
        validation_status=validation,
        promotion_status=promotion,
        wet_optical_status=wet_optical,
        readiness_status=readiness,
    )
    execution_dicts = [row.to_dict() for row in execution_rows]
    guard_dicts = [row.to_dict() for row in guard_rows]
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
        and contract.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_READY_CONTRACT_ONLY"
        and intake.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_READY_SCHEMA_NO_OBSERVATIONS"
        and validation.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_VALIDATION_HARDENING_READY_NOT_YIELD"
        and promotion.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_WET_OBSERVATION_REFRESH_READY_PREFLIGHT_ONLY"
        and wet_optical.get("disposition")
        == "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_READY_NOT_FINAL"
        and readiness.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_ROUTE_YIELD_DETECTION_READINESS_BOARD_READY_INPUTS_NOT_CLAIMS"
        and len(execution_dicts) == 6
        and len(guard_dicts) == 5
        and all(row["yield_current"] is False for row in execution_dicts)
        and all(row["wet_pass_probability_current"] is False for row in execution_dicts)
        and all(row["claim_promotion_allowed_now"] is False for row in guard_dicts)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "execution_status": WET_OBSERVATION_EXECUTION_PACKET_READY_STATUS,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_contract_disposition": contract.get("disposition", ""),
        "source_intake_disposition": intake.get("disposition", ""),
        "source_validation_disposition": validation.get("disposition", ""),
        "source_promotion_disposition": promotion.get("disposition", ""),
        "source_wet_optical_disposition": wet_optical.get("disposition", ""),
        "source_readiness_disposition": readiness.get("disposition", ""),
        "execution_rows": len(execution_dicts),
        "claim_guard_rows": len(guard_dicts),
        "contract_or_fixture_rows_total": sum(
            row["contract_or_fixture_rows"] for row in execution_dicts
        ),
        "current_accepted_observation_rows_total": sum(
            row["current_accepted_observation_rows"] for row in execution_dicts
        ),
        "wet_pass_probability_current_rows": sum(
            row["wet_pass_probability_current"] for row in execution_dicts
        ),
        "clogging_rate_current_rows": sum(
            row["clogging_rate_current"] for row in execution_dicts
        ),
        "time_to_clog_current_rows": sum(
            row["time_to_clog_current"] for row in execution_dicts
        ),
        "recovery_current_rows": sum(row["recovery_current"] for row in execution_dicts),
        "yield_current_rows": sum(row["yield_current"] for row in execution_dicts),
        "detection_probability_current_rows": sum(
            row["detection_probability_current"] for row in execution_dicts
        ),
        "route_score_current_rows": sum(row["route_score_current"] for row in execution_dicts),
        "claim_promotion_allowed_guard_rows": sum(
            row["claim_promotion_allowed_now"] for row in guard_dicts
        ),
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "source_locked_upstream_dirty_context_rows": sum(
            row["classification"] == "source_locked_upstream_dirty_context"
            for row in dirty_context
        ),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context" for row in dirty_context
        ),
        "release_scoped_dirty_blocker_rows": release_dirty_blockers,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "execution_rows": execution_dicts,
        "claim_guard_rows": guard_dicts,
        "source_lock": source_lock,
        "dirty_context": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    checks = {
        "disposition pass": s["disposition"] == DISPOSITION,
        "source lock complete": s["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": s["release_scoped_dirty_blocker_rows"] == 0,
        "six execution rows": s["execution_rows"] == 6,
        "five guard rows": s["claim_guard_rows"] == 5,
        "contract or fixture present": s["contract_or_fixture_rows_total"] > 0,
        "no accepted observations": s["current_accepted_observation_rows_total"] == 0,
        "no wet pass": s["wet_pass_probability_current_rows"] == 0,
        "no clogging": s["clogging_rate_current_rows"] == 0,
        "no time to clog": s["time_to_clog_current_rows"] == 0,
        "no recovery": s["recovery_current_rows"] == 0,
        "no yield": s["yield_current_rows"] == 0,
        "no detection": s["detection_probability_current_rows"] == 0,
        "no route score": s["route_score_current_rows"] == 0,
        "no guard promotion": s["claim_promotion_allowed_guard_rows"] == 0,
    }
    for row in payload["execution_rows"]:
        checks[f"execution row guarded {row['execution_row_id']}"] = (
            row["claim_boundary"] == CLAIM_BOUNDARY
            and row["yield_current"] is False
            and row["wet_pass_probability_current"] is False
            and row["route_score_current"] is False
            and bool(row["next_required_evidence"])
            and bool(row["hard_fail_if"])
        )
    for row in payload["claim_guard_rows"]:
        checks[f"claim guard false {row['guard_row_id']}"] = (
            row["claim_promoted_current"] is False
            and row["claim_promotion_allowed_now"] is False
            and row["claim_boundary"] == CLAIM_BOUNDARY
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    csv_payloads = {
        f"{PREFIX}_EXECUTION_ROWS_20260701.csv": payload["execution_rows"],
        f"{PREFIX}_CLAIM_GUARD_ROWS_20260701.csv": payload["claim_guard_rows"],
        f"{PREFIX}_SOURCE_LOCK_20260701.csv": payload["source_lock"],
        f"{PREFIX}_DIRTY_CONTEXT_20260701.csv": payload["dirty_context"],
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

    public_report = (
        REPORT_DIR / "560_NODI_PACKAGE_C_SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_20260701.md"
    )
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
            "# NODI Package C Sidewall Wet Observation Execution Packet",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Execution rows: `{s['execution_rows']}`.",
            f"- Contract/fixture/context rows total: `{s['contract_or_fixture_rows_total']}`.",
            f"- Current accepted observation rows: `{s['current_accepted_observation_rows_total']}`.",
            f"- Wet pass / yield current rows: `{s['wet_pass_probability_current_rows']}` / `{s['yield_current_rows']}`.",
            f"- Clogging/time-to-clog/recovery current rows: `{s['clogging_rate_current_rows']}` / `{s['time_to_clog_current_rows']}` / `{s['recovery_current_rows']}`.",
            f"- Detection probability / route score current rows: `{s['detection_probability_current_rows']}` / `{s['route_score_current_rows']}`.",
            "- Existing wet assets are contract, schema, fixture, context, and promotion-ledger preflight evidence.",
            "- The next real blocker is accepted sidewall-specific or validated-transfer wet observation rows with controls, replicates, uncertainty, preregistration, and hashes.",
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
                "policy_impact": "wet_observation_execution_packet_not_claim",
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
    if not args.confirm_sidewall_wet_observation_execution_packet:
        parser.error("--confirm-sidewall-wet-observation-execution-packet is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
