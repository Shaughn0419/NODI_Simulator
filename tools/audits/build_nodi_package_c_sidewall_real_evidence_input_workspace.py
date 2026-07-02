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
    read_csv_headers,
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)
from nodi_simulator.sidewall_real_evidence_input_workspace import (  # noqa: E402
    SIDEWALL_REAL_EVIDENCE_INPUT_WORKSPACE_CLAIM_BOUNDARY,
    SIDEWALL_REAL_EVIDENCE_INPUT_WORKSPACE_VERSION,
    TARGET_HEADER_ONLY_STATUS,
    TARGET_REAL_ROWS_PRESENT_STATUS,
    SidewallRealEvidenceInputWorkspaceSpec,
    build_real_evidence_input_workspace,
)
from nodi_simulator.sidewall_wet_surface_observation_manifest_import import (  # noqa: E402
    REQUIRED_MANIFEST_FIELDS as WET_SOURCE_MANIFEST_HEADERS,
)
from nodi_simulator.sidewall_yield_detection_claim_value_review import (  # noqa: E402
    DETECTION_REQUIRED_FIELDS,
    YIELD_REQUIRED_FIELDS,
)
from nodi_simulator.sidewall_yield_detection_claim_value_manifest_import import (  # noqa: E402
    SIMULATION_PROVENANCE_FIELDS as CLAIM_VALUE_PROVENANCE_FIELDS,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
PREFIX = "NODI_PACKAGE_C_SIDEWALL_REAL_EVIDENCE_INPUT_WORKSPACE"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_SIMULATION_EVIDENCE_INPUT_WORKSPACE_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_SIMULATION_EVIDENCE_INPUT_WORKSPACE_READY_HEADER_ONLY"
REAL_ROWS_DISPOSITION = (
    "NODI_PACKAGE_C_SIDEWALL_SIMULATION_EVIDENCE_INPUT_WORKSPACE_SIMULATION_ROWS_PRESENT_RERUN_REQUIRED"
)
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_SIMULATION_EVIDENCE_INPUT_WORKSPACE_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_REAL_EVIDENCE_INPUT_WORKSPACE_CLAIM_BOUNDARY

DETECTOR_TEMPLATE_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_TEMPLATE_ROWS_20260701.csv"
WET_TEMPLATE_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_OBSERVATION_TEMPLATE_ROWS_20260701.csv"
DETECTION_VALUE_TEMPLATE_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_DETECTION_VALUE_TEMPLATE_ROWS_20260701.csv"
YIELD_VALUE_TEMPLATE_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_YIELD_VALUE_TEMPLATE_ROWS_20260701.csv"

DETECTOR_TARGET_INPUT_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INPUT_ROWS_20260701.csv"
WET_TARGET_INPUT_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INPUT_ROWS_20260701.csv"
DETECTION_VALUE_TARGET_INPUT_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_DETECTION_PROBABILITY_VALUE_INPUT_ROWS_20260701.csv"
YIELD_VALUE_TARGET_INPUT_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_YIELD_WET_VALUE_INPUT_ROWS_20260701.csv"
WET_SOURCE_MANIFEST = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_SOURCE_MANIFEST_20260701.csv"
CLAIM_VALUE_SOURCE_MANIFEST = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_SOURCE_MANIFEST_20260701.csv"

ALLOWED_USE = (
    "create/audit header-only simulation/assumption evidence target CSVs for "
    "the sidewall route decision chain"
)
BLOCKED_USE = "template-as-evidence;unreviewed assumptions as claims;production ingestion"

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_real_evidence_input_workspace.py",
    "tools/audits/build_nodi_package_c_sidewall_real_evidence_input_workspace.py",
    "tests/test_sidewall_real_evidence_input_workspace.py",
    "tests/test_nodi_package_c_sidewall_real_evidence_input_workspace.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create/audit sidewall real-evidence input CSV workspace."
    )
    parser.add_argument(
        "--confirm-sidewall-real-evidence-input-workspace",
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


def workspace_specs() -> list[SidewallRealEvidenceInputWorkspaceSpec]:
    return [
        SidewallRealEvidenceInputWorkspaceSpec(
            input_branch="detector_blank_transfer",
            template_artifact_path=str(DETECTOR_TEMPLATE_ROWS),
            target_input_path=str(DETECTOR_TARGET_INPUT_ROWS),
            accepted_status_required=(
                "detector_blank_transfer_bundle_candidate_ready_requires_policy_review"
            ),
        ),
        SidewallRealEvidenceInputWorkspaceSpec(
            input_branch="wet_surface_observation",
            template_artifact_path=str(WET_TEMPLATE_ROWS),
            target_input_path=str(WET_TARGET_INPUT_ROWS),
            accepted_status_required=(
                "wet_surface_observation_bundle_candidate_ready_requires_policy_review"
            ),
        ),
        SidewallRealEvidenceInputWorkspaceSpec(
            input_branch="detection_probability_value",
            template_artifact_path=str(DETECTION_VALUE_TEMPLATE_ROWS),
            target_input_path=str(DETECTION_VALUE_TARGET_INPUT_ROWS),
            accepted_status_required="detection_probability_value_accepted",
        ),
        SidewallRealEvidenceInputWorkspaceSpec(
            input_branch="yield_wet_value",
            template_artifact_path=str(YIELD_VALUE_TEMPLATE_ROWS),
            target_input_path=str(YIELD_VALUE_TARGET_INPUT_ROWS),
            accepted_status_required="yield_wet_value_bundle_accepted",
        ),
    ]


def source_files() -> dict[str, Path]:
    return {
        "detector_template_rows": DETECTOR_TEMPLATE_ROWS,
        "wet_template_rows": WET_TEMPLATE_ROWS,
        "detection_value_template_rows": DETECTION_VALUE_TEMPLATE_ROWS,
        "yield_value_template_rows": YIELD_VALUE_TEMPLATE_ROWS,
        "workspace_source": PROJECT_ROOT / "nodi_simulator/sidewall_real_evidence_input_workspace.py",
        "workspace_builder": PROJECT_ROOT
        / "tools/audits/build_nodi_package_c_sidewall_real_evidence_input_workspace.py",
        "workspace_tests": PROJECT_ROOT / "tests/test_sidewall_real_evidence_input_workspace.py",
        "workspace_builder_tests": PROJECT_ROOT
        / "tests/test_nodi_package_c_sidewall_real_evidence_input_workspace.py",
    }


def target_files() -> dict[str, Path]:
    return {
        "target_detector_input_rows": DETECTOR_TARGET_INPUT_ROWS,
        "target_wet_input_rows": WET_TARGET_INPUT_ROWS,
        "target_detection_value_input_rows": DETECTION_VALUE_TARGET_INPUT_ROWS,
        "target_yield_value_input_rows": YIELD_VALUE_TARGET_INPUT_ROWS,
        "target_wet_source_manifest": WET_SOURCE_MANIFEST,
        "target_claim_value_source_manifest": CLAIM_VALUE_SOURCE_MANIFEST,
    }


def source_manifest_specs() -> list[dict[str, Any]]:
    claim_value_headers = ["claim_value_branch", *CLAIM_VALUE_PROVENANCE_FIELDS]
    for field in (*DETECTION_REQUIRED_FIELDS, *YIELD_REQUIRED_FIELDS):
        if field == "source_artifact_sha256":
            continue
        if field not in claim_value_headers:
            claim_value_headers.append(field)
    return [
        {
            "source_manifest_branch": "wet_surface_observation",
            "source_manifest_path": WET_SOURCE_MANIFEST,
            "headers": list(WET_SOURCE_MANIFEST_HEADERS),
            "downstream_importer": "wet_surface_observation_manifest_import",
        },
        {
            "source_manifest_branch": "yield_detection_claim_value",
            "source_manifest_path": CLAIM_VALUE_SOURCE_MANIFEST,
            "headers": claim_value_headers,
            "downstream_importer": "yield_detection_claim_value_manifest_import",
        },
    ]


def dirty_context_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    output_prefix = f"reports/joint_interface_20260701/{PREFIX}_"
    output_report = f"reports/577_{PREFIX}_20260701.md"
    target_paths = {display_path(path) for path in target_files().values()}
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in BUILD_EDIT_PATHS:
            classification = "simulation_evidence_input_workspace_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path in target_paths:
            classification = "simulation_evidence_target_input_csv"
            release_decision = "source_locked_header_only_or_simulation_input"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "simulation_evidence_input_workspace_output"
            release_decision = "included_or_rewritten_by_workspace_builder"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_simulation_evidence_input_workspace"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def source_lock_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_id, path in {**source_files(), **target_files()}.items():
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


def _display_workspace_row_paths(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    for key in ("template_artifact_path", "target_input_path"):
        output[key] = display_path(Path(str(output[key])))
    return output


def _source_manifest_workspace_rows(*, create_missing_targets: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in source_manifest_specs():
        path = Path(spec["source_manifest_path"])
        headers = list(spec["headers"])
        preexisting = path.exists()
        created_now = False
        refreshed_now = False
        data_rows = 0
        header_matches = False
        if create_missing_targets and not preexisting:
            _write_header_only_csv(path, headers)
            created_now = True
        if path.exists():
            current_headers = read_csv_headers(path)
            current_rows = read_csv_rows(path)
            header_matches = current_headers == headers
            data_rows = len(current_rows)
            if create_missing_targets and not header_matches and not data_rows:
                _write_header_only_csv(path, headers)
                refreshed_now = True
                header_matches = True
                data_rows = 0
        if not path.exists():
            status = "source_manifest_missing"
        elif not header_matches:
            status = "source_manifest_header_mismatch_blocked"
        elif data_rows:
            status = "source_manifest_simulation_rows_present_not_rewritten_by_workspace"
        else:
            status = "source_manifest_header_only_ready_no_evidence_rows"
        rows.append(
            {
                "workspace_row_id": f"SIMULATION-EVIDENCE-SOURCE-MANIFEST-{spec['source_manifest_branch']}",
                "workspace_version": SIDEWALL_REAL_EVIDENCE_INPUT_WORKSPACE_VERSION,
                "source_manifest_branch": spec["source_manifest_branch"],
                "source_manifest_path": display_path(path),
                "source_manifest_columns": ";".join(headers),
                "target_preexisting": preexisting,
                "target_created_now": created_now,
                "target_header_refreshed_now": refreshed_now,
                "target_data_rows": data_rows,
                "target_header_matches_template": header_matches,
                "target_validation_status": status,
                "downstream_importer": spec["downstream_importer"],
                "evidence_current": False,
                "required_next_action": (
                    "fill source manifest rows with simulation/assumption source artifact "
                    "paths, model controls, uncertainty, and pre-registration fields; "
                    "run the downstream importer"
                ),
                "hard_fail_if": "source_manifest_header_only_rows_counted_as_claim_evidence",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def _write_header_only_csv(path: Path, headers: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(",".join(headers) + "\n", encoding="utf-8", newline="")


def semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "workspace_rows": payload["workspace_rows"],
                "source_manifest_workspace_rows": payload[
                    "source_manifest_workspace_rows"
                ],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload(*, create_missing_targets: bool) -> dict[str, Any]:
    rows = build_real_evidence_input_workspace(
        workspace_specs(),
        create_missing_targets=create_missing_targets,
    )
    row_dicts = [_display_workspace_row_paths(row.to_dict()) for row in rows]
    source_manifest_rows = _source_manifest_workspace_rows(
        create_missing_targets=create_missing_targets
    )
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    target_blocked = sum(
        row["target_validation_status"]
        not in {TARGET_HEADER_ONLY_STATUS, TARGET_REAL_ROWS_PRESENT_STATUS}
        for row in row_dicts
    )
    target_data_rows = sum(int(row["target_data_rows"]) for row in row_dicts)
    source_manifest_blocked = sum(
        row["target_validation_status"]
        not in {
            "source_manifest_header_only_ready_no_evidence_rows",
            "source_manifest_simulation_rows_present_not_rewritten_by_workspace",
        }
        for row in source_manifest_rows
    )
    source_manifest_data_rows = sum(
        int(row["target_data_rows"]) for row in source_manifest_rows
    )
    disposition = (
        REAL_ROWS_DISPOSITION
        if target_data_rows or source_manifest_data_rows
        else DISPOSITION
    )
    if source_missing or target_blocked or source_manifest_blocked or len(row_dicts) != 4:
        disposition = BLOCKED_DISPOSITION
    summary: dict[str, Any] = {
        "disposition": disposition,
        "artifact_id": ARTIFACT_ID,
        "workspace_version": SIDEWALL_REAL_EVIDENCE_INPUT_WORKSPACE_VERSION,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "workspace_rows": len(row_dicts),
        "source_manifest_workspace_rows": len(source_manifest_rows),
        "target_created_now_rows": sum(row["target_created_now"] for row in row_dicts),
        "target_header_refreshed_now_rows": sum(
            row["target_header_refreshed_now"] for row in row_dicts
        ),
        "target_header_only_rows": sum(
            row["target_validation_status"] == TARGET_HEADER_ONLY_STATUS
            for row in row_dicts
        ),
        "target_real_data_rows_total": target_data_rows,
        "target_simulation_data_rows_total": target_data_rows,
        "target_blocked_rows": target_blocked,
        "source_manifest_created_now_rows": sum(
            row["target_created_now"] for row in source_manifest_rows
        ),
        "source_manifest_header_only_rows": sum(
            row["target_validation_status"]
            == "source_manifest_header_only_ready_no_evidence_rows"
            for row in source_manifest_rows
        ),
        "source_manifest_real_data_rows_total": source_manifest_data_rows,
        "source_manifest_simulation_data_rows_total": source_manifest_data_rows,
        "source_manifest_blocked_rows": source_manifest_blocked,
        "evidence_current_rows": sum(row["evidence_current"] for row in row_dicts),
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
            "fill source manifests or target CSV rows with simulation/assumption artifacts, "
            "then run the eleven-step route evidence command chain"
        ),
    }
    payload = {
        "summary": summary,
        "workspace_rows": row_dicts,
        "source_manifest_workspace_rows": source_manifest_rows,
        "source_lock_rows": source_lock,
        "dirty_context_rows": dirty_context,
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    failures: list[str] = []
    if s["disposition"] not in {DISPOSITION, REAL_ROWS_DISPOSITION}:
        failures.append("disposition_not_ready")
    if s["workspace_rows"] != 4:
        failures.append("expected_four_workspace_rows")
    if s["source_manifest_workspace_rows"] != 2:
        failures.append("expected_two_source_manifest_workspace_rows")
    if s["source_missing_rows"] != 0:
        failures.append("source_missing")
    if s["target_blocked_rows"] != 0:
        failures.append("target_blocked")
    if s["source_manifest_blocked_rows"] != 0:
        failures.append("source_manifest_blocked")
    if s["evidence_current_rows"] != 0:
        failures.append("workspace_must_not_mark_evidence_current")
    return failures


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json",
        "workspace_rows": OUTPUT_DIR / f"{PREFIX}_WORKSPACE_ROWS_20260701.csv",
        "source_manifest_workspace_rows": OUTPUT_DIR / f"{PREFIX}_SOURCE_MANIFEST_WORKSPACE_ROWS_20260701.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json",
        "master_report": REPORT_DIR / f"577_{PREFIX}_20260701.md",
        "manifest": OUTPUT_DIR / f"{PREFIX}_MANIFEST_20260701.csv",
    }
    write_json_atomic(
        outputs["status"],
        {"disposition": payload["summary"]["disposition"], "summary": payload["summary"]},
        sort_keys=True,
    )
    write_csv_rows(outputs["workspace_rows"], payload["workspace_rows"])
    write_csv_rows(
        outputs["source_manifest_workspace_rows"],
        payload["source_manifest_workspace_rows"],
    )
    write_csv_rows(outputs["source_lock"], payload["source_lock_rows"])
    write_csv_rows(outputs["dirty_context"], payload["dirty_context_rows"])
    write_json_atomic(outputs["report_json"], payload, sort_keys=True)
    outputs["master_report"].write_text(render_markdown(payload), encoding="utf-8")
    write_csv_rows(outputs["manifest"], manifest_rows(outputs))
    return list(outputs.values())


def manifest_rows(outputs: dict[str, Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact_id, path in {**outputs, **target_files()}.items():
        rows.append(
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
        )
    return rows


def render_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    return "\n".join(
        [
            "# NODI Package C Sidewall Simulation Evidence Input Workspace",
            "",
            f"Disposition: `{s['disposition']}`",
            f"Artifact ID: `{s['artifact_id']}`",
            f"Claim boundary: `{s['claim_boundary']}`",
            "",
            f"Workspace rows: `{s['workspace_rows']}`.",
            f"Source manifest workspace rows: `{s['source_manifest_workspace_rows']}`.",
            f"Header-only target rows: `{s['target_header_only_rows']}`.",
            f"Header-only source manifests: `{s['source_manifest_header_only_rows']}`.",
            f"Headers refreshed now: `{s['target_header_refreshed_now_rows']}`.",
            f"Simulation target data rows total: `{s['target_simulation_data_rows_total']}`.",
            f"Simulation source manifest data rows total: `{s['source_manifest_simulation_data_rows_total']}`.",
            f"Targets created now: `{s['target_created_now_rows']}`.",
            f"Source manifests created now: `{s['source_manifest_created_now_rows']}`.",
            "",
            "The target CSV and source manifest files are fillable inputs for simulation/assumption-bound detector, wet, detection-probability, and yield/wet-pass evidence. Header-only files are not evidence.",
            "",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_sidewall_real_evidence_input_workspace:
        parser.error("--confirm-sidewall-real-evidence-input-workspace is required")
    payload = build_payload(create_missing_targets=True)
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_NODI_PACKAGE_C_SIDEWALL_REAL_EVIDENCE_INPUT_WORKSPACE")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
