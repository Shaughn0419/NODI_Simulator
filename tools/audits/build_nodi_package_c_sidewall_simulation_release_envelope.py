#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_PACKAGE_C_SIDEWALL_SIMULATION_RELEASE_ENVELOPE"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_SIMULATION_RELEASE_ENVELOPE_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_SIMULATION_RELEASE_ENVELOPE_READY"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_SIMULATION_RELEASE_ENVELOPE_FAIL_CLOSED"
CLAIM_BOUNDARY = "simulation_release_candidate_not_actual_fabrication_or_production"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"

INTEGRATED_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_SIMULATION_ROUTE_REVIEW_STATUS_20260701.json"
INTEGRATED_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_SIMULATION_ROUTE_REVIEW_REVIEW_ROWS_20260701.csv"

ALLOWED_USE = (
    "assumption-bound simulation release envelope after integrated route review"
)
BLOCKED_USE = (
    "actual fabrication release;actual production ingestion;experimental release;"
    "unqualified route winner outside simulation context"
)

SOURCE_FILES = {
    "integrated_review_status": INTEGRATED_STATUS,
    "integrated_review_rows": INTEGRATED_ROWS,
    "simulation_release_envelope_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_simulation_release_envelope.py",
    "simulation_release_envelope_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_simulation_release_envelope.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build sidewall simulation release envelope."
    )
    parser.add_argument(
        "--confirm-sidewall-simulation-release-envelope",
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
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(path)


def load_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def source_lock_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id, path in SOURCE_FILES.items():
        exists = path.exists()
        rows.append(
            {
                "source_id": source_id,
                "path": display_path(path) if exists else str(path),
                "exists": str(exists).lower(),
                "sha256": sha256_file(path) if exists else "",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def dirty_context_rows() -> list[dict[str, str]]:
    output_prefix = f"reports/joint_interface_20260701/{PREFIX}_"
    output_report = f"reports/585_{PREFIX}_20260701.md"
    build_edit_paths = {
        "tools/audits/build_nodi_package_c_sidewall_simulation_release_envelope.py",
        "tests/test_nodi_package_c_sidewall_simulation_release_envelope.py",
    }
    rows: list[dict[str, str]] = []
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_edit_paths:
            classification = "simulation_release_envelope_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "simulation_release_envelope_output"
            release_decision = "included_or_rewritten_by_release_envelope_builder"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_simulation_release_envelope"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def build_envelope_rows() -> list[dict[str, Any]]:
    rows = read_csv_rows(INTEGRATED_ROWS)
    output: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: _int(item.get("simulation_rank_index"))):
        winner = _bool(row.get("simulation_winner_current"))
        output.append(
            {
                "release_envelope_row_id": f"SIM-RELEASE-ENVELOPE-{row['route_candidate_id']}",
                "release_envelope_version": "sidewall_simulation_release_envelope_v1",
                "route_candidate_id": row["route_candidate_id"],
                "route_geometry_family": row["route_geometry_family"],
                "simulation_rank_index": _int(row.get("simulation_rank_index")),
                "simulation_route_score_value": _float(
                    row.get("simulation_route_score_value")
                ),
                "simulation_yield_value": _float(row.get("simulation_yield_value")),
                "simulation_detection_probability_value": _float(
                    row.get("simulation_detection_probability_value")
                ),
                "simulation_wet_pass_probability_value": _float(
                    row.get("simulation_wet_pass_probability_value")
                ),
                "simulation_release_candidate_current": winner,
                "simulation_fabrication_readiness_current": winner,
                "simulation_production_ingestion_candidate_current": winner,
                "simulation_release_label": (
                    "SIMULATION_RELEASE_CANDIDATE"
                    if winner
                    else "SIMULATION_BACKUP_ROUTE"
                ),
                "actual_fabrication_release_current": False,
                "actual_production_ingestion_current": False,
                "experimental_release_current": False,
                "release_envelope_status": (
                    "simulation_release_candidate_ready"
                    if winner
                    else "simulation_backup_route_retained"
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return output


def semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps({"envelope_rows": payload["envelope_rows"]}, sort_keys=True).encode(
            "utf-8"
        )
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    integrated = load_summary(INTEGRATED_STATUS)
    rows = build_envelope_rows()
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    release_candidate_rows = sum(row["simulation_release_candidate_current"] for row in rows)
    actual_release_rows = sum(
        row["actual_fabrication_release_current"]
        or row["actual_production_ingestion_current"]
        or row["experimental_release_current"]
        for row in rows
    )
    disposition = DISPOSITION
    if (
        integrated.get("disposition")
        != "NODI_PACKAGE_C_SIDEWALL_INTEGRATED_SIMULATION_ROUTE_REVIEW_READY"
        or source_missing
        or len(rows) != 2
        or release_candidate_rows != 1
        or actual_release_rows != 0
    ):
        disposition = BLOCKED_DISPOSITION
    top = next((row for row in rows if row["simulation_release_candidate_current"]), {})
    summary: dict[str, Any] = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_integrated_review_disposition": str(
            integrated.get("disposition", "")
        ),
        "envelope_rows": len(rows),
        "simulation_release_candidate_rows": release_candidate_rows,
        "simulation_fabrication_readiness_rows": sum(
            row["simulation_fabrication_readiness_current"] for row in rows
        ),
        "simulation_production_ingestion_candidate_rows": sum(
            row["simulation_production_ingestion_candidate_current"] for row in rows
        ),
        "actual_release_current_rows": actual_release_rows,
        "top_route_candidate_id": top.get("route_candidate_id", ""),
        "top_route_geometry_family": top.get("route_geometry_family", ""),
        "top_route_score_value": top.get("simulation_route_score_value", 0.0),
        "top_yield_value": top.get("simulation_yield_value", 0.0),
        "top_detection_probability_value": top.get(
            "simulation_detection_probability_value", 0.0
        ),
        "top_wet_pass_probability_value": top.get(
            "simulation_wet_pass_probability_value", 0.0
        ),
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context"
            for row in dirty_context
        ),
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
        "next_high_leverage_step": (
            "use the simulation release candidate for downstream narrative, figures, "
            "and optional separate actual-production planning"
        ),
    }
    payload = {
        "summary": summary,
        "envelope_rows": rows,
        "source_lock_rows": source_lock,
        "dirty_context_rows": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    failures: list[str] = []
    if summary["disposition"] != DISPOSITION:
        failures.append("release_envelope_not_ready")
    if summary["envelope_rows"] != 2:
        failures.append("expected_two_envelope_rows")
    if summary["simulation_release_candidate_rows"] != 1:
        failures.append("expected_one_simulation_release_candidate")
    if summary["actual_release_current_rows"] != 0:
        failures.append("actual_release_rows_present")
    if summary["source_missing_rows"] != 0:
        failures.append("source_missing")
    return failures


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json",
        "envelope_rows": OUTPUT_DIR / f"{PREFIX}_ENVELOPE_ROWS_20260701.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json",
        "master_report": REPORT_DIR / f"585_{PREFIX}_20260701.md",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv",
    }
    write_json_atomic(
        outputs["status"],
        {
            "disposition": payload["summary"]["disposition"],
            "summary": payload["summary"],
        },
        sort_keys=True,
    )
    write_csv_rows(outputs["envelope_rows"], payload["envelope_rows"])
    write_csv_rows(outputs["source_lock"], payload["source_lock_rows"])
    write_csv_rows(outputs["dirty_context"], payload["dirty_context_rows"])
    write_json_atomic(outputs["report_json"], payload, sort_keys=True)
    outputs["master_report"].write_text(render_markdown(payload), encoding="utf-8")
    write_csv_rows(outputs["manifest"], manifest_rows(outputs))
    return list(outputs.values())


def manifest_rows(outputs: dict[str, Path]) -> list[dict[str, Any]]:
    return [
        {
            "artifact_id": artifact_id,
            "path": display_path(path),
            "sha256": SELF_MANIFEST_SHA256
            if artifact_id == "manifest"
            else sha256_file(path),
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        for artifact_id, path in outputs.items()
    ]


def render_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    return "\n".join(
        [
            "# NODI Package C Sidewall Simulation Release Envelope",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Claim boundary: `{s['claim_boundary']}`",
            "",
            f"Simulation release candidate: `{s['top_route_candidate_id']}` (`{s['top_route_geometry_family']}`).",
            f"Route score: `{s['top_route_score_value']}`.",
            f"Yield: `{s['top_yield_value']}`.",
            f"Detection probability: `{s['top_detection_probability_value']}`.",
            f"Wet-pass probability: `{s['top_wet_pass_probability_value']}`.",
            "",
            (
                "This envelope is an assumption-bound simulation release candidate, "
                "not an actual fabrication release or production ingestion."
            ),
            "",
        ]
    )


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if value is None or str(value).strip() == "":
        return 0
    return int(float(str(value)))


def _float(value: Any) -> float:
    if value is None or str(value).strip() == "":
        return 0.0
    return float(str(value))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_sidewall_simulation_release_envelope:
        raise SystemExit("--confirm-sidewall-simulation-release-envelope is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        raise SystemExit(f"Validation failed: {failures}")
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
