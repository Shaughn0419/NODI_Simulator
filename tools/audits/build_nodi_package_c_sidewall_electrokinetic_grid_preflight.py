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
from nodi_simulator.sidewall_electrokinetic_grid_preflight import (  # noqa: E402
    ELECTROKINETIC_GRID_PREFLIGHT_READY_STATUS,
    SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_CLAIM_BOUNDARY,
    build_electrokinetic_grid_preflight,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_20260701"
DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_READY_PROFILE_GRID_REQUIRED"
)
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_CLAIM_BOUNDARY

SOLVER_PACKET_STATUS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_STATUS_20260701.json"
)
SOLVER_BRANCH_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_BRANCH_ROWS_20260701.csv"
)

ALLOWED_USE = (
    "electrokinetic profile-aware grid preflight;rectangle baseline preservation;"
    "sidewall electrokinetic solver requirements and hard-fail checks"
)
BLOCKED_USE = (
    "electrokinetic solver output;electrokinetic weighting;route_score;winner;JRC;"
    "yield;detection_probability;wet_pass_probability;production ingestion;"
    "fabrication release"
)

SOURCE_FILES = {
    "solver_branch_packet_status": SOLVER_PACKET_STATUS,
    "solver_branch_packet_branch_rows": SOLVER_BRANCH_ROWS,
    "electrokinetic_transport_source": PROJECT_ROOT
    / "nodi_simulator/electrokinetic_transport.py",
    "electrokinetic_contract_tests": PROJECT_ROOT / "tests/test_cross_section_geometry.py",
    "electrokinetic_grid_preflight_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_electrokinetic_grid_preflight.py",
    "electrokinetic_grid_preflight_tests": PROJECT_ROOT
    / "tests/test_sidewall_electrokinetic_grid_preflight.py",
    "electrokinetic_grid_preflight_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_electrokinetic_grid_preflight.py",
    "electrokinetic_grid_preflight_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_electrokinetic_grid_preflight.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_electrokinetic_grid_preflight.py",
    "tests/test_sidewall_electrokinetic_grid_preflight.py",
    "tools/audits/build_nodi_package_c_sidewall_electrokinetic_grid_preflight.py",
    "tests/test_nodi_package_c_sidewall_electrokinetic_grid_preflight.py",
}

STALE_POST_RC2_PATHS = {
    "reports/517_NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_20260701.md",
    "reports/joint_interface_20260701/NODI_PACKAGE_C_POST_RC2_DELTA_RELEASE_V1_COMSOL_CLEAN_MIRROR_REQUEST_20260701.md",
    "tests/test_nodi_package_c_post_rc2_delta_release.py",
    "tools/audits/build_nodi_package_c_post_rc2_delta_release.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build sidewall electrokinetic grid preflight packet."
    )
    parser.add_argument(
        "--confirm-sidewall-electrokinetic-grid-preflight",
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
            "NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_"
        )
        or path == "reports/557_NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_20260701.md"
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
            classification = "electrokinetic_grid_preflight_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_"
        ) or path == (
            "reports/557_NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_20260701.md"
        ):
            classification = "electrokinetic_grid_preflight_output"
            release_decision = "included_or_rewritten_by_electrokinetic_grid_preflight"
        elif source_locked_path(path):
            classification = "source_locked_upstream_dirty_context"
            release_decision = "source_locked_current_workspace_not_in_commit_scope"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_electrokinetic_grid_preflight"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_electrokinetic_grid_preflight_not_source_locked"
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
        "preflight_rows": payload["preflight_rows"],
        "claim_guard_rows": payload["claim_guard_rows"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def build_payload() -> dict[str, Any]:
    solver_status = load_json(SOLVER_PACKET_STATUS)
    preflight_rows, guard_rows = build_electrokinetic_grid_preflight(
        solver_branch_rows=read_csv_rows(SOLVER_BRANCH_ROWS),
    )
    preflight_dicts = [row.to_dict() for row in preflight_rows]
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
        and solver_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_SOLVER_BRANCH_EXECUTION_PACKET_READY_BRANCHES_GUARDED"
        and len(preflight_dicts) == 4
        and len(guard_dicts) == 6
        and sum(row["channel_cross_section_model"] == "ideal_rectangle" for row in preflight_dicts) == 1
        and sum(row["channel_cross_section_model"] == "trapezoid_tapered_sidewalls" for row in preflight_dicts) == 3
        and all(row["rectangle_baseline_preserved"] is True for row in preflight_dicts)
        and sum(row["legacy_rectangle_path_allowed"] for row in preflight_dicts) == 1
        and all(row["electrokinetic_solver_output_current"] is False for row in preflight_dicts)
        and all(row["electrokinetic_weight_current"] is False for row in preflight_dicts)
        and all(row["route_score_current"] is False for row in preflight_dicts)
        and all(row["detection_probability_current"] is False for row in preflight_dicts)
        and all(row["claim_promotion_allowed_now"] is False for row in guard_dicts)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "preflight_status": ELECTROKINETIC_GRID_PREFLIGHT_READY_STATUS,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_solver_branch_packet_disposition": solver_status.get("disposition", ""),
        "preflight_rows": len(preflight_dicts),
        "claim_guard_rows": len(guard_dicts),
        "rectangle_baseline_rows": sum(
            row["channel_cross_section_model"] == "ideal_rectangle"
            for row in preflight_dicts
        ),
        "trapezoid_preflight_rows": sum(
            row["channel_cross_section_model"] == "trapezoid_tapered_sidewalls"
            for row in preflight_dicts
        ),
        "legacy_rectangle_path_allowed_rows": sum(
            row["legacy_rectangle_path_allowed"] for row in preflight_dicts
        ),
        "profile_aware_grid_current_rows": sum(
            row["profile_aware_grid_current"] for row in preflight_dicts
        ),
        "electrokinetic_solver_output_current_rows": sum(
            row["electrokinetic_solver_output_current"] for row in preflight_dicts
        ),
        "electrokinetic_weight_current_rows": sum(
            row["electrokinetic_weight_current"] for row in preflight_dicts
        ),
        "route_score_current_rows": sum(row["route_score_current"] for row in preflight_dicts),
        "detection_probability_current_rows": sum(
            row["detection_probability_current"] for row in preflight_dicts
        ),
        "claim_promotion_allowed_guard_rows": sum(
            row["claim_promotion_allowed_now"] for row in guard_dicts
        ),
        "required_metadata_rows": sum(
            row["zeta_wall_model_required"]
            and row["zeta_particle_model_required"]
            and row["ionic_strength_required"]
            and row["debye_length_required"]
            for row in preflight_dicts
        ),
        "required_mutation_test_rows": sum(
            row["rectangle_limit_test_required"]
            and row["theta_mutation_test_required"]
            and row["zeta_sign_mutation_test_required"]
            and row["ionic_strength_mutation_test_required"]
            for row in preflight_dicts
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
        "preflight_rows": preflight_dicts,
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
        "four preflight rows": s["preflight_rows"] == 4,
        "six guard rows": s["claim_guard_rows"] == 6,
        "rectangle baseline preserved": s["rectangle_baseline_rows"] == 1,
        "three trapezoid rows": s["trapezoid_preflight_rows"] == 3,
        "only rectangle legacy path allowed": s["legacy_rectangle_path_allowed_rows"] == 1,
        "no profile grid current": s["profile_aware_grid_current_rows"] == 0,
        "no solver output": s["electrokinetic_solver_output_current_rows"] == 0,
        "no electrokinetic weight": s["electrokinetic_weight_current_rows"] == 0,
        "no route score": s["route_score_current_rows"] == 0,
        "no detection": s["detection_probability_current_rows"] == 0,
        "no guard promotion": s["claim_promotion_allowed_guard_rows"] == 0,
        "metadata required all rows": s["required_metadata_rows"] == 4,
        "mutation tests required all rows": s["required_mutation_test_rows"] == 4,
    }
    for row in payload["preflight_rows"]:
        checks[f"preflight row guarded {row['preflight_row_id']}"] = (
            row["claim_boundary"] == CLAIM_BOUNDARY
            and row["electrokinetic_solver_output_current"] is False
            and row["electrokinetic_weight_current"] is False
            and row["route_score_current"] is False
            and row["detection_probability_current"] is False
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
        f"{PREFIX}_PREFLIGHT_ROWS_20260701.csv": payload["preflight_rows"],
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
        REPORT_DIR
        / "557_NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT_20260701.md"
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
            "# NODI Package C Sidewall Electrokinetic Grid Preflight",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Preflight rows: `{s['preflight_rows']}`.",
            f"- Rectangle baseline rows: `{s['rectangle_baseline_rows']}`.",
            f"- Trapezoid preflight rows: `{s['trapezoid_preflight_rows']}`.",
            f"- Legacy rectangle path allowed rows: `{s['legacy_rectangle_path_allowed_rows']}`.",
            f"- Profile-aware grid current rows: `{s['profile_aware_grid_current_rows']}`.",
            f"- Electrokinetic solver output current rows: `{s['electrokinetic_solver_output_current_rows']}`.",
            f"- Electrokinetic weighting current rows: `{s['electrokinetic_weight_current_rows']}`.",
            f"- Route/detection current rows: `{s['route_score_current_rows']}` / `{s['detection_probability_current_rows']}`.",
            "- The ideal-rectangle diagnostic path is preserved as a baseline.",
            "- Trapezoid electrokinetic analysis requires profile-aware grid, signed wall distance, zeta metadata, ionic strength, Debye length, blocked-bin exclusion, rectangle-limit, theta-mutation, zeta-sign, and ionic-strength tests before any solver/weight/route/detection claim.",
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
                "policy_impact": "electrokinetic_grid_preflight_not_solver_claim",
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
    if not args.confirm_sidewall_electrokinetic_grid_preflight:
        parser.error("--confirm-sidewall-electrokinetic-grid-preflight is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_ELECTROKINETIC_GRID_PREFLIGHT")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
