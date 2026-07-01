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
from nodi_simulator.sidewall_reference_surrogate_candidate import (  # noqa: E402
    SIDEWALL_REFERENCE_SURROGATE_CLAIM_BOUNDARY,
    SIDEWALL_REFERENCE_SURROGATE_VERSION,
    build_sidewall_reference_surrogate_rows,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_CANDIDATE"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_CANDIDATE_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_CANDIDATE_READY_NOT_OPTICAL_SOLVER"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_CANDIDATE_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

OPTICAL_SMOKE_STATUS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_OPTICAL_REFERENCE_SMOKE_STATUS_20260701.json"
)
OPTICAL_SMOKE_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_OPTICAL_REFERENCE_SMOKE_SMOKE_ROWS_20260701.csv"
)

ALLOWED_USE = (
    "sidewall-aware reference surrogate candidate;effective aperture sensitivity;"
    "optical solver gap reduction"
)
BLOCKED_USE = (
    "full-wave optical solver;true W_eff;detector response validation;"
    "detection_probability;yield;route_score;winner;JRC;wet pass claim;production ingestion"
)

SOURCE_FILES = {
    "sidewall_optical_reference_smoke_status": OPTICAL_SMOKE_STATUS,
    "sidewall_optical_reference_smoke_rows": OPTICAL_SMOKE_ROWS,
    "reference_field_source": PROJECT_ROOT / "nodi_simulator/reference_field.py",
    "data_objects_source": PROJECT_ROOT / "nodi_simulator/data_objects.py",
    "sidewall_reference_surrogate_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_reference_surrogate_candidate.py",
    "reference_field_tests": PROJECT_ROOT / "tests/test_reference_field.py",
    "sidewall_reference_surrogate_tests": PROJECT_ROOT
    / "tests/test_sidewall_reference_surrogate_candidate.py",
    "sidewall_reference_surrogate_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_reference_surrogate_candidate.py",
    "sidewall_reference_surrogate_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_reference_surrogate_candidate.py",
}

BUILD_EDIT_PATHS = {
    ".gitignore",
    "nodi_simulator/reference_field.py",
    "nodi_simulator/data_objects.py",
    "nodi_simulator/sidewall_reference_surrogate_candidate.py",
    "tests/test_reference_field.py",
    "tests/test_sidewall_reference_surrogate_candidate.py",
    "tools/audits/build_nodi_package_c_sidewall_reference_surrogate_candidate.py",
    "tests/test_nodi_package_c_sidewall_reference_surrogate_candidate.py",
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
        description="Build Package C sidewall reference surrogate candidate packet."
    )
    parser.add_argument("--confirm-sidewall-reference-surrogate", action="store_true")
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
            "NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_CANDIDATE_"
        )
        or path == "reports/527_NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_CANDIDATE_20260701.md"
    )


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in STALE_POST_RC2_PATHS:
            classification = "superseded_post_rc2_context"
            release_decision = "excluded_from_source_lock"
        elif path in BUILD_EDIT_PATHS:
            classification = "sidewall_reference_surrogate_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(
            "reports/joint_interface_20260701/"
            "NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_CANDIDATE_"
        ) or path == "reports/527_NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_CANDIDATE_20260701.md":
            classification = "sidewall_reference_surrogate_output"
            release_decision = "included_or_rewritten_by_sidewall_reference_surrogate"
        elif release_scoped_path(path):
            classification = "release_scoped_dirty_blocker"
            release_decision = "blocks_sidewall_reference_surrogate"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_sidewall_reference_surrogate_not_source_locked"
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
                "claim_boundary": SIDEWALL_REFERENCE_SURROGATE_CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def surrogate_rows() -> list[dict[str, str]]:
    return [_stringify_row(row.to_dict()) for row in build_sidewall_reference_surrogate_rows()]


def promotion_gap_rows() -> list[dict[str, str]]:
    return [
        {
            "target": "full_wave_or_calibrated_sidewall_optical_solver",
            "current_value": "false",
            "surrogate_available": "true",
            "required_before_true": (
                "field solver or blank-channel calibration consuming sidewall/trapezoid geometry"
            ),
            "hard_fail_if": "optical_solver_true_from_effective_aperture_surrogate",
        },
        {
            "target": "true_W_eff",
            "current_value": "false",
            "surrogate_available": "true",
            "required_before_true": "calibrated optical/electromagnetic definition of effective width",
            "hard_fail_if": "true_W_eff_true_from_aperture_factor",
        },
        {
            "target": "detection_probability",
            "current_value": "false",
            "surrogate_available": "true",
            "required_before_true": "detector-response calibration plus blank trace validation",
            "hard_fail_if": "detection_probability_true_from_reference_surrogate",
        },
    ]


def self_review_rows() -> list[dict[str, str]]:
    topics = [
        "trapezoid effective-aperture reference model is available",
        "404 nm rows show sidewall aperture sensitivity without NA hard zero",
        "660 nm rows record NA cutoff context for W500",
        "candidate remains surrogate and not full optical solver output",
    ]
    return [
        {
            "review_id": f"REFSUR-SELF-{index:02d}",
            "dimension": topic,
            "verdict": "PASS_SIDEWALL_REFERENCE_SURROGATE_CANDIDATE_NOT_SOLVER",
            "notes": "Candidate advances sidewall reference propagation while preserving solver and detection prerequisites.",
        }
        for index, topic in enumerate(topics, start=1)
    ]


def build_payload() -> dict[str, Any]:
    source_status = load_json(OPTICAL_SMOKE_STATUS)
    rows = surrogate_rows()
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_dirty_blockers = sum(
        row["classification"] == "release_scoped_dirty_blocker" for row in dirty_context
    )
    row_by_key = {(row["case_id"], row["wavelength_nm"]): row for row in rows}
    theta85_404 = row_by_key.get(("taper_theta85_D900_W500", "404"), {})
    rect_404 = row_by_key.get(("rectangle_limit_theta90_D900_W500", "404"), {})
    theta85_factor = float(theta85_404.get("trapezoid_effective_aperture_factor", "nan"))
    rect_factor = float(rect_404.get("trapezoid_effective_aperture_factor", "nan"))
    status = (
        DISPOSITION
        if source_missing == 0
        and release_dirty_blockers == 0
        and source_status.get("disposition")
        == "NODI_PACKAGE_C_SIDEWALL_OPTICAL_REFERENCE_SMOKE_READY_NOT_OPTICAL_SOLVER"
        and len(rows) == 4
        and 0.0 < theta85_factor < rect_factor
        and all(row["geometry_not_propagated_to_reference_field"] == "false" for row in rows)
        and all(row["not_optical_solver_output"] == "true" for row in rows)
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": SIDEWALL_REFERENCE_SURROGATE_CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "surrogate_version": SIDEWALL_REFERENCE_SURROGATE_VERSION,
        "source_optical_smoke_disposition": source_status.get("disposition", ""),
        "surrogate_rows": len(rows),
        "theta85_404_effective_aperture_factor": theta85_factor,
        "rectangle_404_effective_aperture_factor": rect_factor,
        "sidewall_reference_surrogate_current": True,
        "full_wave_or_calibrated_optical_solver_current": False,
        "true_W_eff_current": False,
        "detection_probability_current": False,
        "route_score_current": False,
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
        "surrogate_rows": rows,
        "promotion_gaps": promotion_gap_rows(),
        "source_lock": source_lock,
        "dirty_context": dirty_context,
        "self_review": self_review_rows(),
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def semantic_digest(payload: dict[str, Any]) -> str:
    digest_input = {
        "surrogate_rows": payload["surrogate_rows"],
        "promotion_gaps": payload["promotion_gaps"],
    }
    return hashlib.sha256(json.dumps(digest_input, sort_keys=True).encode("utf-8")).hexdigest()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    checks = {
        "disposition pass": summary["disposition"] == DISPOSITION,
        "source lock complete": summary["source_missing_rows"] == 0,
        "release scoped dirty blockers absent": summary["release_scoped_dirty_blocker_rows"] == 0,
        "four surrogate rows": summary["surrogate_rows"] == 4,
        "theta85 404 lower than rectangle": (
            0.0
            < summary["theta85_404_effective_aperture_factor"]
            < summary["rectangle_404_effective_aperture_factor"]
        ),
        "full optical solver false": summary["full_wave_or_calibrated_optical_solver_current"] is False,
        "true W_eff false": summary["true_W_eff_current"] is False,
        "detection false": summary["detection_probability_current"] is False,
    }
    for row in payload["surrogate_rows"]:
        checks[f"row not final {row['row_id']}"] = (
            row["not_optical_solver_output"] == "true"
            and row["true_W_eff_current"] == "false"
            and row["detection_probability_current"] == "false"
        )
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        f"{PREFIX}_SURROGATE_ROWS_20260701.csv": payload["surrogate_rows"],
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

    public_report = REPORT_DIR / "527_NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_CANDIDATE_20260701.md"
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
            "# NODI Package C Sidewall Reference Surrogate Candidate",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Current head: `{s['current_head']}` on `{s['branch']}`.",
            f"- Surrogate version: `{s['surrogate_version']}`.",
            f"- Surrogate rows: `{s['surrogate_rows']}`.",
            f"- 404 nm theta85 effective-aperture factor: `{s['theta85_404_effective_aperture_factor']}`.",
            "- This packet adds a trapezoid effective-aperture reference surrogate that consumes sidewall geometry.",
            "- It reduces the reference-geometry propagation gap but remains a surrogate, not full-wave optical solver output, true W_eff, detector-response validation, or detection probability.",
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
                "policy_impact": "sidewall_reference_surrogate_candidate_not_solver",
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
    if not args.confirm_sidewall_reference_surrogate:
        parser.error("--confirm-sidewall-reference-surrogate is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_CANDIDATE")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
