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
from nodi_simulator.sidewall_integrated_promotion_ledger import (  # noqa: E402
    SIDEWALL_INTEGRATED_PROMOTION_LEDGER_CLAIM_BOUNDARY,
    SIDEWALL_INTEGRATED_PROMOTION_LEDGER_VERSION,
    build_blocker_catalog_rows,
    build_integrated_promotion_lane_rows,
    build_integrated_promotion_ledger_rows,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_READY_PREFLIGHT_ONLY"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

QCH_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_QCH_SIDECAR_CANDIDATE_QCH_ROWS_20260701.csv"
PRESSURE_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_PRESSURE_FLOW_VALIDATION_CONTEXT_COMPARISON_ROWS_20260701.csv"
)
ROUTE_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_ROUTE_YIELD_DETECTION_CANDIDATE_ROUTE_CANDIDATE_ROWS_20260701.csv"
)
WET_CONTEXT_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_EVIDENCE_CONTEXT_ROWS_20260701.csv"
)
CALIBRATION_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_STATUS_20260701.json"
)
CALIBRATION_READINESS_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_OPTICAL_CALIBRATION_BRIDGE_READINESS_ROWS_20260701.csv"
)

ALLOWED_USE = (
    "route-level promotion preflight;integrated evidence blocker ledger;"
    "next-evidence prioritization"
)
BLOCKED_USE = (
    "route_score;winner;JRC;q_ch_weighting;detection_probability;yield;wet pass;"
    "clogging rate;time-to-clog;recovery;fabrication release;production ingestion"
)

SOURCE_FILES = {
    "qch_sidecar_rows": QCH_ROWS,
    "pressure_flow_validation_rows": PRESSURE_ROWS,
    "route_candidate_rows": ROUTE_ROWS,
    "wet_optical_detection_context_rows": WET_CONTEXT_ROWS,
    "sidewall_optical_calibration_bridge_status": CALIBRATION_STATUS,
    "sidewall_optical_calibration_bridge_readiness_rows": CALIBRATION_READINESS_ROWS,
    "integrated_promotion_ledger_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_integrated_promotion_ledger.py",
    "integrated_promotion_ledger_tests": PROJECT_ROOT
    / "tests/test_sidewall_integrated_promotion_ledger.py",
    "integrated_promotion_ledger_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_integrated_promotion_ledger.py",
    "integrated_promotion_ledger_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_integrated_promotion_ledger.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/sidewall_integrated_promotion_ledger.py",
    "tests/test_sidewall_integrated_promotion_ledger.py",
    "tools/audits/build_nodi_package_c_sidewall_integrated_promotion_ledger.py",
    "tests/test_nodi_package_c_sidewall_integrated_promotion_ledger.py",
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
        description="Build Package C sidewall integrated promotion ledger packet."
    )
    parser.add_argument("--confirm-sidewall-integrated-promotion-ledger", action="store_true")
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
            "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_"
        )
        or path == "reports/530_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "integrated_promotion_ledger_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_"
        ) or path == "reports/530_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_20260701.md":
            classification = "integrated_promotion_ledger_output"
            release_decision = "included_or_rewritten_by_integrated_promotion_ledger"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_integrated_promotion_ledger"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_integrated_promotion_ledger_not_source_locked"
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
                "claim_boundary": SIDEWALL_INTEGRATED_PROMOTION_LEDGER_CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def lane_source_artifact_map() -> dict[str, tuple[str, str, str]]:
    return {
        "flow_split_qch": (
            display_path(QCH_ROWS),
            sha256_file(QCH_ROWS),
            "candidate_qch_sidecar_not_formal_weighting",
        ),
        "pressure_flow_validation": (
            display_path(PRESSURE_ROWS),
            sha256_file(PRESSURE_ROWS),
            "context_only_not_formal_validation",
        ),
        "selected_annulus_detection_context": (
            display_path(WET_CONTEXT_ROWS),
            sha256_file(WET_CONTEXT_ROWS),
            "selected_annulus_context_missing_rerun_required",
        ),
        "blank_channel_reference_amplitude_phase": (
            display_path(CALIBRATION_READINESS_ROWS),
            sha256_file(CALIBRATION_READINESS_ROWS),
            "synthetic_seed_available_not_experimental",
        ),
        "sidewall_geometry_coverage": (
            display_path(CALIBRATION_READINESS_ROWS),
            sha256_file(CALIBRATION_READINESS_ROWS),
            "single_W500_D900_theta85_and_rectangle_seed_only",
        ),
        "detector_response_bridge": (
            display_path(CALIBRATION_READINESS_ROWS),
            sha256_file(CALIBRATION_READINESS_ROWS),
            "not_detector_response_validation",
        ),
        "blank_false_positive_trace": (
            display_path(CALIBRATION_READINESS_ROWS),
            sha256_file(CALIBRATION_READINESS_ROWS),
            "blank_trace_validation_missing_for_sidewall_geometry",
        ),
        "wet_wall_interaction": (
            display_path(WET_CONTEXT_ROWS),
            sha256_file(WET_CONTEXT_ROWS),
            "wet_sidewall_evidence_missing",
        ),
        "integrated_route_ledger": (
            display_path(ROUTE_ROWS),
            sha256_file(ROUTE_ROWS),
            "route_score_not_authorized_from_seed",
        ),
    }


def ledger_rows() -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    readiness = read_csv_rows(CALIBRATION_READINESS_ROWS)
    blocker_catalog = build_blocker_catalog_rows(calibration_readiness_rows=readiness)
    rows = build_integrated_promotion_ledger_rows(
        route_candidate_rows=read_csv_rows(ROUTE_ROWS),
        wet_context_rows=read_csv_rows(WET_CONTEXT_ROWS),
        qch_rows=read_csv_rows(QCH_ROWS),
        pressure_rows=read_csv_rows(PRESSURE_ROWS),
        calibration_bridge_summary=load_json(CALIBRATION_STATUS),
        blocker_catalog_rows=blocker_catalog,
    )
    lane_rows = build_integrated_promotion_lane_rows(
        ledger_rows=rows,
        blocker_catalog_rows=blocker_catalog,
        source_artifact_by_lane=lane_source_artifact_map(),
    )
    return (
        [_stringify_row(row.to_dict()) for row in rows],
        [_stringify_row(row.to_dict()) for row in blocker_catalog],
        [_stringify_row(row.to_dict()) for row in lane_rows],
    )


def self_review_rows() -> list[dict[str, str]]:
    topics = [
        "route-level ledger rows do not contain route_score or winner values",
        "q_ch remains candidate and not formal weighting",
        "optical calibration bridge remains synthetic seed only",
        "wet, blank-trace, selected-annulus, and detector-response blockers remain explicit",
    ]
    return [
        {
            "review_id": f"PROMO-SELF-{index:02d}",
            "dimension": topic,
            "verdict": "PASS_INTEGRATED_PROMOTION_LEDGER_PREFLIGHT_ONLY",
            "notes": "Ledger consolidates blockers without promoting route/yield/detection claims.",
        }
        for index, topic in enumerate(topics, start=1)
    ]


def build_payload() -> dict[str, Any]:
    rows, blockers, lanes = ledger_rows()
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    blocked_rows = sum(
        row["promotion_preflight_status"]
        == "blocked_missing_calibrated_optical_wet_route_evidence"
        for row in rows
    )
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and len(rows) == 2
        and len(blockers) >= 9
        and len(lanes) == len(rows) * len(blockers)
        and blocked_rows == len(rows)
        and all(row["not_route_score"] == "true" for row in rows)
        and all(row["not_detection_probability"] == "true" for row in rows)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": SIDEWALL_INTEGRATED_PROMOTION_LEDGER_CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "ledger_version": SIDEWALL_INTEGRATED_PROMOTION_LEDGER_VERSION,
        "ledger_rows": len(rows),
        "blocker_catalog_rows": len(blockers),
        "promotion_lane_rows": len(lanes),
        "blocked_promotion_rows": blocked_rows,
        "max_blocker_count": max(int(row["blocker_count"]) for row in rows),
        "formal_qch_weighting_current": False,
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
        "ledger_rows": rows,
        "blocker_catalog": blockers,
        "promotion_lane_rows": lanes,
        "source_lock": source_lock,
        "dirty_context": dirty_context,
        "self_review": self_review_rows(),
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "ledger_rows": payload["ledger_rows"],
        "blocker_catalog": payload["blocker_catalog"],
        "promotion_lane_rows": payload["promotion_lane_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    checks = {
        "disposition pass": summary["disposition"] == DISPOSITION,
        "source lock complete": summary["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": summary["release_scoped_dirty_blocker_rows"] == 0,
        "two ledger rows": summary["ledger_rows"] == 2,
        "blocker catalog populated": summary["blocker_catalog_rows"] >= 9,
        "promotion lane rows populated": summary["promotion_lane_rows"]
        == summary["ledger_rows"] * summary["blocker_catalog_rows"],
        "all rows blocked": summary["blocked_promotion_rows"] == summary["ledger_rows"],
        "route score false": summary["route_score_current"] is False,
        "winner false": summary["winner_current"] is False,
        "detection false": summary["detection_probability_current"] is False,
        "yield false": summary["yield_current"] is False,
    }
    for row in payload["ledger_rows"]:
        checks[f"ledger row not claim {row['ledger_row_id']}"] = (
            row["not_route_score"] == "true"
            and row["not_winner"] == "true"
            and row["not_yield"] == "true"
            and row["not_detection_probability"] == "true"
            and row["route_score_current"] == "false"
            and row["winner_current"] == "false"
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        f"{PREFIX}_LEDGER_ROWS_20260701.csv": payload["ledger_rows"],
        f"{PREFIX}_BLOCKER_CATALOG_20260701.csv": payload["blocker_catalog"],
        f"{PREFIX}_PROMOTION_LANE_ROWS_20260701.csv": payload["promotion_lane_rows"],
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

    public_report = REPORT_DIR / "530_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER_20260701.md"
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
            "# NODI Package C Sidewall Integrated Promotion Ledger",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Ledger version: `{s['ledger_version']}`.",
            f"- Ledger rows: `{s['ledger_rows']}`.",
            f"- Blocker catalog rows: `{s['blocker_catalog_rows']}`.",
            f"- Promotion lane rows: `{s['promotion_lane_rows']}`.",
            f"- Blocked promotion rows: `{s['blocked_promotion_rows']}`.",
            "- The ledger joins q_ch, pressure-flow, optical calibration, wet/detection, and route candidate context at route grain.",
            "- It records blockers and next evidence focus only; it does not emit route_score, winner/JRC, yield, wet pass, or detection probability.",
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
                "policy_impact": "sidewall_integrated_promotion_preflight_only",
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
    if not args.confirm_sidewall_integrated_promotion_ledger:
        parser.error("--confirm-sidewall-integrated-promotion-ledger is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_INTEGRATED_PROMOTION_LEDGER")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
