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
from nodi_simulator.sidewall_optical_calibration_bridge import (  # noqa: E402
    SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_CLAIM_BOUNDARY,
    SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_VERSION,
    build_calibration_seed_manifest,
    build_sidewall_optical_calibration_readiness_rows,
    build_sidewall_optical_calibration_seed_rows,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_READY_SEED_ONLY"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

REFERENCE_SMOKE_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_SMOKE_STATUS_20260701.json"
)
REFERENCE_SMOKE_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_SMOKE_SMOKE_ROWS_20260701.csv"
)

SEED_TABLE_NAME = f"{PREFIX}_SEED_TABLE_20260701.csv"
SEED_MANIFEST_NAME = f"{SEED_TABLE_NAME}.manifest.json"

ALLOWED_USE = (
    "synthetic sidewall optical calibration seed;calibration readiness planning;"
    "future solver or blank-channel calibration scaffold"
)
BLOCKED_USE = (
    "measured blank-channel calibration;full-wave optical solver;true W_eff;"
    "detector response validation;detection_probability;yield;route_score;winner;"
    "JRC;wet pass claim;production ingestion"
)

SOURCE_FILES = {
    "sidewall_reference_surrogate_smoke_status": REFERENCE_SMOKE_STATUS,
    "sidewall_reference_surrogate_smoke_rows": REFERENCE_SMOKE_ROWS,
    "sidewall_optical_calibration_bridge_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_optical_calibration_bridge.py",
    "sidewall_optical_calibration_bridge_tests": PROJECT_ROOT
    / "tests/test_sidewall_optical_calibration_bridge.py",
    "sidewall_optical_calibration_bridge_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_optical_calibration_bridge.py",
    "sidewall_optical_calibration_bridge_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_optical_calibration_bridge.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/sidewall_optical_calibration_bridge.py",
    "tests/test_sidewall_optical_calibration_bridge.py",
    "tools/audits/build_nodi_package_c_sidewall_optical_calibration_bridge.py",
    "tests/test_nodi_package_c_sidewall_optical_calibration_bridge.py",
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
        description="Build Package C sidewall optical calibration bridge packet."
    )
    parser.add_argument("--confirm-sidewall-optical-calibration-bridge", action="store_true")
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
            "NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_"
        )
        or path == "reports/529_NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "sidewall_optical_calibration_bridge_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_"
        ) or path == "reports/529_NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_20260701.md":
            classification = "sidewall_optical_calibration_bridge_output"
            release_decision = "included_or_rewritten_by_sidewall_optical_calibration_bridge"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_sidewall_optical_calibration_bridge"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_sidewall_optical_calibration_bridge_not_source_locked"
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
                "claim_boundary": SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def seed_rows() -> list[dict[str, str]]:
    return [_stringify_row(row.to_dict()) for row in build_sidewall_optical_calibration_seed_rows()]


def readiness_rows() -> list[dict[str, str]]:
    return [
        _stringify_row(row.to_dict())
        for row in build_sidewall_optical_calibration_readiness_rows()
    ]


def self_review_rows() -> list[dict[str, str]]:
    topics = [
        "synthetic seed table is schema-valid but not experimental calibration",
        "calibrated_lookup misuse is blocked by synthetic fixture role",
        "readiness rows cover optical, detector, blank, wet, and route lanes",
        "true W_eff, detection probability, yield, and route winner remain unresolved",
    ]
    return [
        {
            "review_id": f"SWCAL-SELF-{index:02d}",
            "dimension": topic,
            "verdict": "PASS_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_SEED_ONLY",
            "notes": "Bridge advances calibration structure while preventing synthetic seed promotion.",
        }
        for index, topic in enumerate(topics, start=1)
    ]


def build_payload() -> dict[str, Any]:
    source_status = load_json(REFERENCE_SMOKE_STATUS)
    seeds = seed_rows()
    readiness = readiness_rows()
    seed_manifest = build_calibration_seed_manifest()
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    synthetic_seed_rows = sum(
        row["calibration_data_role"] == "synthetic_fixture_not_experimental"
        and row["not_experimental_blank_channel_calibration"] == "true"
        for row in seeds
    )
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and source_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_SMOKE_READY_NOT_OPTICAL_SOLVER"
        and len(seeds) == 4
        and len(readiness) == 6
        and synthetic_seed_rows == 4
        and seed_manifest.get("synthetic_fixture") is True
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "bridge_version": SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_VERSION,
        "source_reference_smoke_disposition": source_status.get("disposition", ""),
        "seed_rows": len(seeds),
        "readiness_rows": len(readiness),
        "synthetic_seed_rows": synthetic_seed_rows,
        "calibration_seed_table_validation_status": "valid_minimal_schema_by_contract",
        "calibration_seed_manifest_validation_status": "valid_minimal_manifest_by_contract",
        "calibrated_lookup_unlock_status": "blocked_synthetic_fixture_not_experimental",
        "full_wave_or_calibrated_optical_solver_current": False,
        "true_W_eff_current": False,
        "detector_response_validation_current": False,
        "detection_probability_current": False,
        "yield_current": False,
        "route_score_current": False,
        "winner_current": False,
        "JRC_current": False,
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
        "seed_rows": seeds,
        "seed_manifest": seed_manifest,
        "readiness_rows": readiness,
        "source_lock": source_lock,
        "dirty_context": dirty_context,
        "self_review": self_review_rows(),
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "seed_rows": payload["seed_rows"],
        "seed_manifest": payload["seed_manifest"],
        "readiness_rows": payload["readiness_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    checks = {
        "disposition pass": summary["disposition"] == DISPOSITION,
        "source lock complete": summary["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": summary["release_scoped_dirty_blocker_rows"] == 0,
        "four seed rows": summary["seed_rows"] == 4,
        "six readiness rows": summary["readiness_rows"] == 6,
        "all synthetic seed rows": summary["synthetic_seed_rows"] == 4,
        "lookup remains blocked": summary["calibrated_lookup_unlock_status"]
        == "blocked_synthetic_fixture_not_experimental",
        "true W_eff false": summary["true_W_eff_current"] is False,
        "detection false": summary["detection_probability_current"] is False,
        "route false": summary["route_score_current"] is False,
    }
    for row in payload["seed_rows"]:
        checks[f"seed row not final {row['calibration_row_id']}"] = (
            row["not_experimental_blank_channel_calibration"] == "true"
            and row["not_full_wave_optical_solver"] == "true"
            and row["not_true_W_eff"] == "true"
            and row["not_detection_probability"] == "true"
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        SEED_TABLE_NAME: payload["seed_rows"],
        f"{PREFIX}_READINESS_ROWS_20260701.csv": payload["readiness_rows"],
        f"{PREFIX}_SOURCE_LOCK_20260701.csv": payload["source_lock"],
        f"{PREFIX}_DIRTY_CONTEXT_20260701.csv": payload["dirty_context"],
        f"{PREFIX}_SELF_REVIEW_20260701.csv": payload["self_review"],
    }
    for filename, rows in csv_payloads.items():
        path = OUTPUT_DIR / filename
        write_csv_rows(path, rows)
        paths.append(path)

    seed_manifest_path = OUTPUT_DIR / SEED_MANIFEST_NAME
    write_json_atomic(seed_manifest_path, payload["seed_manifest"])
    paths.append(seed_manifest_path)

    status_path = OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json"
    write_json_atomic(status_path, {"disposition": DISPOSITION, "summary": payload["summary"]})
    paths.append(status_path)

    report_path = OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json"
    write_json_atomic(report_path, payload)
    paths.append(report_path)

    public_report = REPORT_DIR / "529_NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_20260701.md"
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
            "# NODI Package C Sidewall Optical Calibration Bridge",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Bridge version: `{s['bridge_version']}`.",
            f"- Synthetic seed rows: `{s['seed_rows']}`.",
            f"- Readiness rows: `{s['readiness_rows']}`.",
            f"- Calibrated lookup unlock status: `{s['calibrated_lookup_unlock_status']}`.",
            "- The seed table is a replaceable scaffold for future measured blank-channel or solver calibration.",
            "- It is marked synthetic and must not unlock true W_eff, detector response validation, detection probability, yield, route score, winner/JRC, wet pass, or production ingestion.",
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
                "policy_impact": "sidewall_optical_calibration_bridge_seed_only",
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
            if value != value:
                out[key] = "nan"
            else:
                out[key] = f"{value:.12g}"
        else:
            out[key] = str(value)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_sidewall_optical_calibration_bridge:
        parser.error("--confirm-sidewall-optical-calibration-bridge is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
