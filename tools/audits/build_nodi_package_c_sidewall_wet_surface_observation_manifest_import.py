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

from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)
from nodi_simulator.sidewall_wet_surface_observation_manifest_import import (  # noqa: E402
    SIDEWALL_WET_SURFACE_OBSERVATION_MANIFEST_IMPORT_CLAIM_BOUNDARY,
    SIDEWALL_WET_SURFACE_OBSERVATION_MANIFEST_IMPORT_VERSION,
    build_wet_observation_rows_from_manifest,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_MANIFEST_IMPORT"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_MANIFEST_IMPORT_20260701"
READY_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_MANIFEST_IMPORT_READY_FOR_INTAKE"
)
MANIFEST_REQUIRED_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_MANIFEST_IMPORT_READY_MANIFEST_REQUIRED"
)
BLOCKED_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_MANIFEST_IMPORT_FAIL_CLOSED"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_WET_SURFACE_OBSERVATION_MANIFEST_IMPORT_CLAIM_BOUNDARY

WET_CONTRACT_ROWS = (
    OUTPUT_DIR
    / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_EVIDENCE_CONTRACT_CONTRACT_ROWS_20260701.csv"
)
DEFAULT_SOURCE_MANIFEST = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_SOURCE_MANIFEST_20260701.csv"
)
CANONICAL_WET_INPUT_ROWS = (
    OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INPUT_ROWS_20260701.csv"
)

ALLOWED_USE = "manifest-bound wet observation input import;source artifact hash binding"
BLOCKED_USE = (
    "template-as-evidence;wet_pass_probability;clogging_rate;time_to_clog;"
    "recovery;yield;detection_probability;route_score;winner;JRC;production ingestion"
)

SOURCE_FILES = {
    "wet_contract_rows": WET_CONTRACT_ROWS,
    "manifest_import_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_wet_surface_observation_manifest_import.py",
    "manifest_import_module": PROJECT_ROOT
    / "nodi_simulator/sidewall_wet_surface_observation_manifest_import.py",
    "manifest_import_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_wet_surface_observation_manifest_import.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import manifest-bound wet observation source artifacts."
    )
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    parser.add_argument("--artifact-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument(
        "--confirm-sidewall-wet-surface-observation-manifest-import",
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


def source_lock_rows(source_manifest: Path) -> list[dict[str, str]]:
    sources = {**SOURCE_FILES, "source_manifest": source_manifest}
    rows: list[dict[str, str]] = []
    for source_id, path in sources.items():
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
    rows: list[dict[str, str]] = []
    output_prefix = f"reports/joint_interface_20260701/{PREFIX}_"
    output_report = f"reports/578_{PREFIX}_20260701.md"
    build_paths = {
        "nodi_simulator/sidewall_wet_surface_observation_manifest_import.py",
        "tools/audits/build_nodi_package_c_sidewall_wet_surface_observation_manifest_import.py",
        "tests/test_sidewall_wet_surface_observation_manifest_import.py",
        "tests/test_nodi_package_c_sidewall_wet_surface_observation_manifest_import.py",
    }
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in build_paths:
            classification = "wet_surface_observation_manifest_import_build_edit"
            release_decision = "included_in_code_commit_scope"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "wet_surface_observation_manifest_import_output"
            release_decision = "included_or_rewritten_by_manifest_import_builder"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_wet_surface_observation_manifest_import"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def build_payload(
    *,
    source_manifest: Path = DEFAULT_SOURCE_MANIFEST,
    artifact_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    contract_rows = read_csv_rows(WET_CONTRACT_ROWS) if WET_CONTRACT_ROWS.exists() else []
    manifest_rows = read_csv_rows(source_manifest) if source_manifest.exists() else []
    imported_rows, audit_rows = build_wet_observation_rows_from_manifest(
        contract_rows=contract_rows,
        manifest_rows=manifest_rows,
        artifact_root=artifact_root,
    )
    audit_dicts = [row.to_dict() for row in audit_rows]
    if not source_manifest.exists():
        audit_dicts.append(
            {
                "import_row_id": "WET-OBS-MANIFEST-IMPORT-source-manifest",
                "import_version": SIDEWALL_WET_SURFACE_OBSERVATION_MANIFEST_IMPORT_VERSION,
                "route_candidate_id": "",
                "endpoint_id": "",
                "observation_source_artifact": display_path(source_manifest),
                "observation_source_sha256": "",
                "import_status": "wet_observation_source_manifest_missing",
                "import_rejection_reason": "source_manifest_missing",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    elif not manifest_rows:
        audit_dicts.append(
            {
                "import_row_id": "WET-OBS-MANIFEST-IMPORT-source-manifest",
                "import_version": SIDEWALL_WET_SURFACE_OBSERVATION_MANIFEST_IMPORT_VERSION,
                "route_candidate_id": "",
                "endpoint_id": "",
                "observation_source_artifact": display_path(source_manifest),
                "observation_source_sha256": sha256_file(source_manifest),
                "import_status": "wet_observation_source_manifest_header_only_no_rows",
                "import_rejection_reason": "source_manifest_rows_missing",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    source_lock = source_lock_rows(source_manifest)
    dirty_context = dirty_context_rows()
    required_source_missing = sum(
        row["source_id"] != "source_manifest" and row["exists"] != "true"
        for row in source_lock
    )
    rejected_rows = sum(
        row["import_status"].endswith("rejected") for row in audit_dicts
    )
    if required_source_missing:
        disposition = BLOCKED_DISPOSITION
    elif not source_manifest.exists() or not manifest_rows:
        disposition = MANIFEST_REQUIRED_DISPOSITION
    elif imported_rows and rejected_rows == 0:
        disposition = READY_DISPOSITION
    else:
        disposition = BLOCKED_DISPOSITION
    summary = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "import_version": SIDEWALL_WET_SURFACE_OBSERVATION_MANIFEST_IMPORT_VERSION,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "source_manifest_path": display_path(source_manifest),
        "source_manifest_present": source_manifest.exists(),
        "artifact_root": display_path(artifact_root),
        "contract_rows": len(contract_rows),
        "source_manifest_rows": len(manifest_rows),
        "imported_observation_rows": len(imported_rows),
        "import_audit_rows": len(audit_dicts),
        "rejected_import_rows": rejected_rows,
        "canonical_wet_input_written": bool(imported_rows) and rejected_rows == 0,
        "wet_pass_probability_current": False,
        "clogging_rate_current": False,
        "time_to_clog_current": False,
        "recovery_current": False,
        "yield_current": False,
        "detection_probability_current": False,
        "route_score_current": False,
        "winner_current": False,
        "JRC_current": False,
        "source_lock_rows": len(source_lock),
        "required_source_missing_rows": required_source_missing,
        "dirty_context_rows": len(dirty_context),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context"
            for row in dirty_context
        ),
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "imported_observation_rows": imported_rows,
        "import_audit_rows": audit_dicts,
        "source_lock_rows": source_lock,
        "dirty_context_rows": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "imported_observation_rows": payload["imported_observation_rows"],
                "import_audit_rows": payload["import_audit_rows"],
                "claim_boundary": CLAIM_BOUNDARY,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def validate_payload(payload: dict[str, Any]) -> list[str]:
    summary = payload["summary"]
    allowed = {READY_DISPOSITION, MANIFEST_REQUIRED_DISPOSITION}
    failures: list[str] = []
    if summary["disposition"] not in allowed:
        failures.append("disposition_not_ready")
    if summary["required_source_missing_rows"] != 0:
        failures.append("required_source_missing")
    if any(row["route_score_current"] for row in [summary]):
        failures.append("route_score_unexpectedly_current")
    if summary["yield_current"] or summary["detection_probability_current"]:
        failures.append("claim_unexpectedly_current")
    return failures


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json",
        "audit_rows": OUTPUT_DIR / f"{PREFIX}_AUDIT_ROWS_20260701.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json",
        "master_report": REPORT_DIR / f"578_{PREFIX}_20260701.md",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv",
    }
    write_json_atomic(outputs["status"], {"disposition": payload["summary"]["disposition"], "summary": payload["summary"]}, sort_keys=True)
    if payload["imported_observation_rows"]:
        outputs["imported_rows"] = OUTPUT_DIR / f"{PREFIX}_IMPORTED_OBSERVATION_ROWS_20260701.csv"
        write_csv_rows(outputs["imported_rows"], payload["imported_observation_rows"])
    write_csv_rows(outputs["audit_rows"], payload["import_audit_rows"])
    if payload["summary"]["canonical_wet_input_written"]:
        write_csv_rows(CANONICAL_WET_INPUT_ROWS, payload["imported_observation_rows"])
        outputs["canonical_wet_input_rows"] = CANONICAL_WET_INPUT_ROWS
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
            "sha256": SELF_MANIFEST_SHA256 if artifact_id == "manifest" else sha256_file(path),
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
            "# NODI Package C Sidewall Wet Surface Observation Manifest Import",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Imported observation rows: `{s['imported_observation_rows']}`",
            f"Rejected import rows: `{s['rejected_import_rows']}`",
            f"Canonical wet input written: `{s['canonical_wet_input_written']}`",
            f"Claim boundary: `{s['claim_boundary']}`",
            "",
            "This importer binds wet observation rows to source artifact hashes. It does not create wet-pass, clogging, recovery, yield, detection-probability, route-score, winner, JRC, or production claims.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_sidewall_wet_surface_observation_manifest_import:
        raise SystemExit(
            "--confirm-sidewall-wet-surface-observation-manifest-import is required"
        )
    payload = build_payload(source_manifest=args.source_manifest, artifact_root=args.artifact_root)
    failures = validate_payload(payload)
    if failures:
        raise SystemExit(f"Validation failed: {failures}")
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
