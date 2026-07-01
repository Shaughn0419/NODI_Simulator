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
from nodi_simulator.sidewall_optical_reference_smoke import (  # noqa: E402
    SIDEWALL_OPTICAL_REFERENCE_SMOKE_CLAIM_BOUNDARY,
    SIDEWALL_OPTICAL_REFERENCE_SMOKE_VERSION,
    run_sidewall_optical_reference_smoke,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_OPTICAL_REFERENCE_SMOKE"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_OPTICAL_REFERENCE_SMOKE_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_OPTICAL_REFERENCE_SMOKE_READY_NOT_OPTICAL_SOLVER"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_OPTICAL_REFERENCE_SMOKE_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

WET_OPTICAL_CONTEXT_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_STATUS_20260701.json"
)
WET_OPTICAL_CONTEXT_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_EVIDENCE_CONTEXT_ROWS_20260701.csv"
)

ALLOWED_USE = (
    "sidewall optical/reference NODI smoke evidence;synthetic detection context;"
    "optical solver gap prioritization"
)
BLOCKED_USE = (
    "true W_eff;sidewall optical solver output;detector response validation;"
    "detection_probability;yield;route_score;winner;JRC;wet pass claim;production ingestion"
)

SOURCE_FILES = {
    "wet_optical_detection_context_status": WET_OPTICAL_CONTEXT_STATUS,
    "wet_optical_detection_context_rows": WET_OPTICAL_CONTEXT_ROWS,
    "sidewall_optical_reference_smoke_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_optical_reference_smoke.py",
    "sidewall_optical_reference_smoke_tests": PROJECT_ROOT
    / "tests/test_sidewall_optical_reference_smoke.py",
    "sidewall_optical_reference_smoke_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_optical_reference_smoke.py",
    "sidewall_optical_reference_smoke_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_optical_reference_smoke.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/sidewall_optical_reference_smoke.py",
    "tests/test_sidewall_optical_reference_smoke.py",
    "tools/audits/build_nodi_package_c_sidewall_optical_reference_smoke.py",
    "tests/test_nodi_package_c_sidewall_optical_reference_smoke.py",
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
        description="Build Package C sidewall optical/reference smoke packet."
    )
    parser.add_argument("--confirm-sidewall-optical-reference-smoke", action="store_true")
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
            "NODI_PACKAGE_C_SIDEWALL_OPTICAL_REFERENCE_SMOKE_"
        )
        or path == "reports/526_NODI_PACKAGE_C_SIDEWALL_OPTICAL_REFERENCE_SMOKE_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "sidewall_optical_reference_smoke_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_OPTICAL_REFERENCE_SMOKE_"
        ) or path == "reports/526_NODI_PACKAGE_C_SIDEWALL_OPTICAL_REFERENCE_SMOKE_20260701.md":
            classification = "sidewall_optical_reference_smoke_output"
            release_decision = "included_or_rewritten_by_sidewall_optical_reference_smoke"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_sidewall_optical_reference_smoke"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_sidewall_optical_reference_smoke_not_source_locked"
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
                "claim_boundary": SIDEWALL_OPTICAL_REFERENCE_SMOKE_CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def smoke_rows() -> list[dict[str, str]]:
    return [_stringify_row(row.to_dict()) for row in run_sidewall_optical_reference_smoke()]


def promotion_gap_rows() -> list[dict[str, str]]:
    return [
        {
            "target": "sidewall_optical_solver_output",
            "current_value": "false",
            "smoke_context_available": "true",
            "required_before_true": (
                "reference/optical solver or calibration consuming trapezoid geometry "
                "instead of rectangular width-depth surrogate"
            ),
            "hard_fail_if": "optical_solver_true_from_smoke_detection_context",
        },
        {
            "target": "detection_probability",
            "current_value": "false",
            "smoke_context_available": "true",
            "required_before_true": (
                "sidewall optical solver plus detector-response calibration and blank trace validation"
            ),
            "hard_fail_if": "detection_probability_true_from_synthetic_smoke",
        },
        {
            "target": "true_W_eff",
            "current_value": "false",
            "smoke_context_available": "true",
            "required_before_true": "optical-field solution or calibrated lookup for sidewall geometry",
            "hard_fail_if": "true_W_eff_true_from_reference_proxy",
        },
    ]


def self_review_rows() -> list[dict[str, str]]:
    topics = [
        "rectangle and trapezoid W500/D900 NODI smoke cases executed",
        "trapezoid row records reference geometry not propagated",
        "synthetic detection context is not final detection probability",
        "true W_eff and optical solver output remain false",
    ]
    return [
        {
            "review_id": f"SOR-SELF-{index:02d}",
            "dimension": topic,
            "verdict": "PASS_SIDEWALL_OPTICAL_REFERENCE_SMOKE_NOT_SOLVER",
            "notes": "Smoke advances optical/reference branch while preserving solver and detection claim prerequisites.",
        }
        for index, topic in enumerate(topics, start=1)
    ]


def build_payload() -> dict[str, Any]:
    source_status = load_json(WET_OPTICAL_CONTEXT_STATUS)
    rows = smoke_rows()
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    trapezoid_blocked_rows = sum(
        row["channel_cross_section_model"] == "trapezoid_tapered_sidewalls"
        and row["geometry_not_propagated_to_reference_field"] == "true"
        for row in rows
    )
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and source_status.get("disposition")
        == "NODI_PACKAGE_C_WET_OPTICAL_DETECTION_EVIDENCE_CONTEXT_READY_NOT_FINAL"
        and len(rows) == 2
        and trapezoid_blocked_rows == 1
        and all(row["detection_probability_current"] == "false" for row in rows)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": SIDEWALL_OPTICAL_REFERENCE_SMOKE_CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "smoke_version": SIDEWALL_OPTICAL_REFERENCE_SMOKE_VERSION,
        "source_wet_optical_context_disposition": source_status.get("disposition", ""),
        "smoke_rows": len(rows),
        "trapezoid_reference_not_propagated_rows": trapezoid_blocked_rows,
        "rectangle_native_reference_rows": sum(
            row["reference_geometry_propagation_status"]
            == "rectangle_native_or_non_sidewall_geometry"
            for row in rows
        ),
        "optical_solver_current": False,
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
        "smoke_rows": rows,
        "promotion_gaps": promotion_gap_rows(),
        "source_lock": source_lock,
        "dirty_context": dirty_context,
        "self_review": self_review_rows(),
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "smoke_rows": payload["smoke_rows"],
        "promotion_gaps": payload["promotion_gaps"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    failures: list[str] = []
    checks = {
        "disposition pass": summary["disposition"] == DISPOSITION,
        "source lock complete": summary["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": summary["release_scoped_dirty_blocker_rows"] == 0,
        "two smoke rows": summary["smoke_rows"] == 2,
        "one trapezoid reference blocker": summary["trapezoid_reference_not_propagated_rows"] == 1,
        "one rectangle native row": summary["rectangle_native_reference_rows"] == 1,
        "optical solver false": summary["optical_solver_current"] is False,
        "detection probability false": summary["detection_probability_current"] is False,
        "route score false": summary["route_score_current"] is False,
    }
    for row in payload["smoke_rows"]:
        checks[f"row not final {row['case_id']}"] = (
            row["not_optical_solver_output"] == "true"
            and row["detection_probability_current"] == "false"
            and row["route_score_current"] == "false"
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        f"{PREFIX}_SMOKE_ROWS_20260701.csv": payload["smoke_rows"],
        f"{PREFIX}_PROMOTION_GAPS_20260701.csv": payload["promotion_gaps"],
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

    public_report = REPORT_DIR / "526_NODI_PACKAGE_C_SIDEWALL_OPTICAL_REFERENCE_SMOKE_20260701.md"
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
            "# NODI Package C Sidewall Optical/Reference Smoke",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Smoke version: `{s['smoke_version']}`.",
            f"- Smoke rows: `{s['smoke_rows']}`.",
            f"- Trapezoid reference-not-propagated rows: `{s['trapezoid_reference_not_propagated_rows']}`.",
            "- This packet executes small NODI W500/D900 rectangle-limit and theta85 trapezoid batches.",
            "- The trapezoid row records that rectangular reference geometry is still used as a proxy and sidewall geometry is not propagated to a true optical/reference solver.",
            "- Synthetic detection context is recorded only as branch evidence, not as final detection probability, route score, winner/JRC, yield, or true W_eff.",
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
                "policy_impact": "sidewall_optical_reference_smoke_not_solver",
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
    if not args.confirm_sidewall_optical_reference_smoke:
        parser.error("--confirm-sidewall-optical-reference-smoke is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_OPTICAL_REFERENCE_SMOKE")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
