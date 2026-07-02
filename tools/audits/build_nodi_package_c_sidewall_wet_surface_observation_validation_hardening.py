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
from nodi_simulator.sidewall_wet_surface_observation_intake import (  # noqa: E402
    OBSERVATION_ACCEPTED_STATUS,
    OBSERVATION_REJECTED_STATUS,
    ROUTE_MATRIX_ACCEPTED_STATUS,
    ROUTE_MATRIX_NO_OBSERVATIONS_STATUS,
    SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_CLAIM_BOUNDARY,
    build_wet_surface_observation_intake,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_VALIDATION_HARDENING"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_VALIDATION_HARDENING_20260701"
DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_VALIDATION_HARDENING_READY_NOT_YIELD"
)
BLOCKED_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_VALIDATION_HARDENING_FAIL_CLOSED"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_CLAIM_BOUNDARY

FORMAL_QCH_BRIDGE_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_FORMAL_QCH_RECEIPT_BRIDGE_STATUS_20260701.json"
)
WET_INTAKE_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_STATUS_20260701.json"
)
WET_INTAKE_MATRIX_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_ROUTE_OBSERVATION_MATRIX_ROWS_20260701.csv"
)
WET_CONTRACT_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_CONTRACT_ROWS_20260701.csv"
)

ALLOWED_USE = (
    "wet/surface observation validator hardening;accepted/rejected wet endpoint fixture checks;"
    "future yield/wet evidence gate"
)
BLOCKED_USE = (
    "wet_pass_probability;clogging_rate;time_to_clog;recovery;yield;"
    "detection_probability;route_score;winner;JRC;production ingestion"
)

SOURCE_FILES = {
    "formal_qch_receipt_bridge_status": FORMAL_QCH_BRIDGE_STATUS,
    "wet_surface_observation_intake_status": WET_INTAKE_STATUS,
    "wet_surface_observation_intake_matrix_rows": WET_INTAKE_MATRIX_ROWS,
    "wet_surface_contract_rows": WET_CONTRACT_ROWS,
    "wet_surface_observation_intake_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_wet_surface_observation_intake.py",
    "wet_surface_observation_intake_tests": PROJECT_ROOT
    / "tests/test_sidewall_wet_surface_observation_intake.py",
    "wet_surface_observation_validation_hardening_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_wet_surface_observation_validation_hardening.py",
    "wet_surface_observation_validation_hardening_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_wet_surface_observation_validation_hardening.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/sidewall_wet_surface_observation_intake.py",
    "tests/test_sidewall_wet_surface_observation_intake.py",
    "tools/audits/build_nodi_package_c_sidewall_wet_surface_observation_validation_hardening.py",
    "tests/test_nodi_package_c_sidewall_wet_surface_observation_validation_hardening.py",
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
        description="Build wet/surface observation validation hardening packet."
    )
    parser.add_argument(
        "--confirm-sidewall-wet-surface-observation-validation-hardening",
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


def read_csv_rows(path: Path) -> list[dict[str, str]]:
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
            "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_VALIDATION_HARDENING_"
        )
        or path
        == "reports/553_NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_VALIDATION_HARDENING_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "wet_surface_observation_validation_hardening_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_VALIDATION_HARDENING_"
        ) or path == (
            "reports/553_NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_VALIDATION_HARDENING_20260701.md"
        ):
            classification = "wet_surface_observation_validation_hardening_output"
            release_decision = "included_or_rewritten_by_wet_surface_observation_validation_hardening"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_wet_surface_observation_validation_hardening"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_wet_surface_observation_validation_hardening_not_source_locked"
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


def _accepted_observation(contract: dict[str, str]) -> dict[str, str]:
    endpoint = contract["endpoint_id"]
    prereg = (
        "pre_registered"
        if endpoint in {"wet_pass_probability", "yield_bridge", "clogging_time_series"}
        else "not_required_for_endpoint"
    )
    replicate_count = (
        "1" if endpoint in {"material_surface_identity", "ev_sample_panel"} else "3"
    )
    uncertainty = (
        "uncertainty_interval_missing"
        if endpoint in {"material_surface_identity", "ev_sample_panel"}
        else "uncertainty_interval_present"
    )
    return {
        "route_candidate_id": contract["route_candidate_id"],
        "endpoint_id": endpoint,
        "observation_artifact_id": f"fixture-wet-{contract['route_candidate_id']}-{endpoint}",
        "observation_artifact_class": contract["required_artifact_class"],
        "observation_source_artifact": f"wet_fixture/{contract['route_candidate_id']}/{endpoint}.csv",
        "observation_source_sha256": "c" * 64,
        "source_geometry_match_level": "sidewall_specific",
        "provided_fields": contract["required_fields"],
        "controls_status": "controls_pass",
        "replicate_count": replicate_count,
        "uncertainty_interval_status": uncertainty,
        "pre_registered_rule_status": prereg,
    }


def accepted_fixture_rows(contract_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    observations = [_accepted_observation(row) for row in contract_rows]
    intake_rows, matrix_rows = build_wet_surface_observation_intake(
        contract_rows=contract_rows,
        observation_rows=observations,
    )
    matrix_by_route = {row.route_candidate_id: row for row in matrix_rows}
    return [
        {
            "fixture_id": f"ACCEPTED-WET-{row.route_candidate_id}-{row.endpoint_id}",
            "route_candidate_id": row.route_candidate_id,
            "endpoint_id": row.endpoint_id,
            "observation_validation_status": row.observation_validation_status,
            "observation_rejection_reason": row.observation_rejection_reason,
            "route_wet_observation_matrix_status": matrix_by_route[
                row.route_candidate_id
            ].route_wet_observation_matrix_status,
            "accepted_observation_current": row.accepted_observation_current,
            "target_claim_current": row.target_claim_current,
            "wet_pass_probability_current": row.wet_pass_probability_current,
            "yield_current": row.yield_current,
            "detection_probability_current": row.detection_probability_current,
            "route_score_current": row.route_score_current,
            "claim_boundary": row.claim_boundary,
        }
        for row in intake_rows
    ]


def negative_control_rows(contract_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    contract_by_endpoint = {row["endpoint_id"]: row for row in contract_rows}
    controls = [
        (
            "bad_sha",
            contract_by_endpoint["material_surface_identity"],
            {"observation_source_sha256": "not-a-sha"},
        ),
        (
            "missing_fields",
            contract_by_endpoint["ev_sample_panel"],
            {"provided_fields": "particle_size_distribution;concentration"},
        ),
        (
            "low_replicate_count",
            contract_by_endpoint["adhesion_wall_interaction"],
            {"replicate_count": "2"},
        ),
        (
            "controls_missing",
            contract_by_endpoint["wet_pass_probability"],
            {"controls_status": "controls_missing"},
        ),
    ]
    rows: list[dict[str, Any]] = []
    for control_id, contract, overrides in controls:
        observation = _accepted_observation(contract)
        observation.update(overrides)
        intake_rows, matrix_rows = build_wet_surface_observation_intake(
            contract_rows=[contract],
            observation_rows=[observation],
        )
        intake = intake_rows[0]
        matrix = matrix_rows[0]
        rows.append(
            {
                "negative_control_id": control_id,
                "route_candidate_id": intake.route_candidate_id,
                "endpoint_id": intake.endpoint_id,
                "observation_validation_status": intake.observation_validation_status,
                "observation_rejection_reason": intake.observation_rejection_reason,
                "route_wet_observation_matrix_status": matrix.route_wet_observation_matrix_status,
                "accepted_observation_current": intake.accepted_observation_current,
                "target_claim_current": intake.target_claim_current,
                "yield_current": intake.yield_current,
                "wet_pass_probability_current": intake.wet_pass_probability_current,
                "route_score_current": intake.route_score_current,
                "claim_boundary": intake.claim_boundary,
            }
        )
    return rows


def current_intake_audit_rows() -> list[dict[str, Any]]:
    return [
        {
            "audit_row_id": f"CURRENT-WET-{row['route_candidate_id']}",
            "route_candidate_id": row["route_candidate_id"],
            "route_wet_observation_matrix_status": row[
                "route_wet_observation_matrix_status"
            ],
            "accepted_endpoint_count": row["accepted_endpoint_count"],
            "missing_endpoint_count": row["missing_endpoint_count"],
            "yield_current": row["yield_current"],
            "wet_pass_probability_current": row["wet_pass_probability_current"],
            "detection_probability_current": row["detection_probability_current"],
            "route_score_current": row["route_score_current"],
            "claim_boundary": row["claim_boundary"],
        }
        for row in read_csv_rows(WET_INTAKE_MATRIX_ROWS)
    ]


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "accepted_fixture_rows": payload["accepted_fixture_rows"],
        "negative_control_rows": payload["negative_control_rows"],
        "current_intake_audit_rows": payload["current_intake_audit_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    qch_bridge_status = load_json(FORMAL_QCH_BRIDGE_STATUS)
    wet_intake_status = load_json(WET_INTAKE_STATUS)
    contract_rows = read_csv_rows(WET_CONTRACT_ROWS)
    accepted_rows = accepted_fixture_rows(contract_rows)
    negative_rows = negative_control_rows(
        [row for row in contract_rows if row["route_candidate_id"] == "ROUTE-CAND-002"]
    )
    current_rows = current_intake_audit_rows()
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
        and qch_bridge_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_FORMAL_QCH_RECEIPT_BRIDGE_READY_ROUTE_INPUT_NOT_SCORE"
        and wet_intake_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_READY_SCHEMA_NO_OBSERVATIONS"
        and len(accepted_rows) == 14
        and all(row["observation_validation_status"] == OBSERVATION_ACCEPTED_STATUS for row in accepted_rows)
        and all(row["route_wet_observation_matrix_status"] == ROUTE_MATRIX_ACCEPTED_STATUS for row in accepted_rows)
        and all(row["target_claim_current"] is False for row in accepted_rows)
        and len(negative_rows) == 4
        and all(row["observation_validation_status"] == OBSERVATION_REJECTED_STATUS for row in negative_rows)
        and len(current_rows) == 2
        and all(row["route_wet_observation_matrix_status"] == ROUTE_MATRIX_NO_OBSERVATIONS_STATUS for row in current_rows)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_formal_qch_bridge_disposition": qch_bridge_status.get("disposition", ""),
        "source_wet_intake_disposition": wet_intake_status.get("disposition", ""),
        "accepted_fixture_rows": len(accepted_rows),
        "negative_control_rows": len(negative_rows),
        "current_intake_audit_rows": len(current_rows),
        "current_no_observation_rows": sum(
            row["route_wet_observation_matrix_status"] == ROUTE_MATRIX_NO_OBSERVATIONS_STATUS
            for row in current_rows
        ),
        "fixture_target_claim_current_rows": sum(
            row["target_claim_current"] for row in accepted_rows
        ),
        "fixture_yield_current_rows": sum(row["yield_current"] for row in accepted_rows),
        "fixture_wet_pass_probability_current_rows": sum(
            row["wet_pass_probability_current"] for row in accepted_rows
        ),
        "fixture_route_score_current_rows": sum(
            row["route_score_current"] for row in accepted_rows
        ),
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
        "accepted_fixture_rows": accepted_rows,
        "negative_control_rows": negative_rows,
        "current_intake_audit_rows": current_rows,
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
        "accepted fixture rows": s["accepted_fixture_rows"] == 14,
        "negative controls": s["negative_control_rows"] == 4,
        "current audit rows": s["current_intake_audit_rows"] == 2,
        "current no observations": s["current_no_observation_rows"] == 2,
        "fixture no target claim": s["fixture_target_claim_current_rows"] == 0,
        "fixture no yield": s["fixture_yield_current_rows"] == 0,
        "fixture no wet pass": s["fixture_wet_pass_probability_current_rows"] == 0,
        "fixture no route score": s["fixture_route_score_current_rows"] == 0,
    }
    expected_reasons = {
        "controls_not_pass",
        "insufficient_replicate_count",
        "invalid_observation_source_sha256",
        "missing_required_fields",
    }
    checks["negative reasons complete"] = {
        row["observation_rejection_reason"] for row in payload["negative_control_rows"]
    } == expected_reasons
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    csv_payloads = {
        f"{PREFIX}_ACCEPTED_FIXTURE_ROWS_20260701.csv": payload["accepted_fixture_rows"],
        f"{PREFIX}_NEGATIVE_CONTROL_ROWS_20260701.csv": payload["negative_control_rows"],
        f"{PREFIX}_CURRENT_INTAKE_AUDIT_ROWS_20260701.csv": payload[
            "current_intake_audit_rows"
        ],
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
        REPORT_DIR
        / "553_NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_VALIDATION_HARDENING_20260701.md"
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
            "# NODI Package C Sidewall Wet/Surface Observation Validation Hardening",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Accepted wet fixture rows: `{s['accepted_fixture_rows']}`.",
            f"- Negative control rows: `{s['negative_control_rows']}`.",
            f"- Current no-observation audit rows: `{s['current_no_observation_rows']}`.",
            "- Accepted fixtures prove validator behavior only; current simulation wet observations remain absent.",
            "- Yield, wet pass probability, clogging, recovery, detection probability, and route score remain false.",
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
                "policy_impact": "wet_surface_observation_validation_hardening_not_claim",
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
    if not args.confirm_sidewall_wet_surface_observation_validation_hardening:
        parser.error(
            "--confirm-sidewall-wet-surface-observation-validation-hardening is required"
        )
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_VALIDATION_HARDENING")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
