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
from nodi_simulator.sidewall_comsol_target_binding_qch_integration import (  # noqa: E402
    SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION_CLAIM_BOUNDARY,
    SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION_STATUS,
    build_comsol_target_binding_qch_integration,
)


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
COMSOL_REPO = PROJECT_ROOT.parent / "comsol test/comsol_ev_pbs_bonded_cross_junction"
COMSOL_DWG = COMSOL_REPO / "full_chip/dwg_analysis"

PREFIX = "NODI_PACKAGE_C_SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION"
ARTIFACT_ID = "PACKAGE_C_SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION_20260701"
DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_COMSOL_TARGET_BOUND_FORMAL_QCH_INPUT_INTEGRATED"
BLOCKED_DISPOSITION = "NODI_PACKAGE_C_SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION_FAIL_CLOSED"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
CLAIM_BOUNDARY = SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION_CLAIM_BOUNDARY

REQUEST_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_VALIDATION_HARNESS_REQUEST_ROWS_20260701.csv"
BINDING_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_BINDING_ROWS_20260701.csv"
SIDECAR_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_FORMAL_QCH_SIDECAR_ROWS_20260701.csv"
BINDER_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_STATUS_20260701.json"
EXTERNAL_RESULT_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_EXTERNAL_RESULT_ROWS_20260701.csv"
TEMPLATE_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_EXTERNAL_RESULT_TEMPLATE_ROWS_20260701.csv"
STATE_UPDATE_ROWS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_MAINLINE_EXECUTION_STATE_UPDATE_ROUTE_EVIDENCE_STATE_ROWS_20260701.csv"
LAUNCH_PRECONDITION_STATUS = OUTPUT_DIR / "NODI_PACKAGE_C_SIDEWALL_COMSOL_LAUNCH_PRECONDITION_STATUS_20260701.json"

COMSOL_LAUNCHER = COMSOL_DWG / "run_package_c_sidewall_pressure_flow_w500_d900.py"
COMSOL_BUILD_SCAFFOLD = COMSOL_DWG / "build_stage11_explicit_nano_full_chip_scaffold.py"
COMSOL_PRESSURE_RUNNER = COMSOL_DWG / "run_stage11_explicit_nano_pressure_only_comsol.py"
COMSOL_CONNECTIONS = COMSOL_DWG / "full_chip_stage3_lumped_connections.csv"
COMSOL_LAUNCHER_TEST = (
    COMSOL_REPO
    / "p0_model_package/tests/test_package_c_sidewall_pressure_flow_w500_d900_launcher.py"
)

SOURCE_FILES = {
    "request_rows": REQUEST_ROWS,
    "binding_rows": BINDING_ROWS,
    "sidecar_rows": SIDECAR_ROWS,
    "binder_status": BINDER_STATUS,
    "external_result_rows": EXTERNAL_RESULT_ROWS,
    "template_rows": TEMPLATE_ROWS,
    "mainline_state_update_rows": STATE_UPDATE_ROWS,
    "comsol_launch_precondition_status": LAUNCH_PRECONDITION_STATUS,
    "comsol_launcher": COMSOL_LAUNCHER,
    "comsol_launcher_test": COMSOL_LAUNCHER_TEST,
    "comsol_build_scaffold": COMSOL_BUILD_SCAFFOLD,
    "comsol_pressure_runner": COMSOL_PRESSURE_RUNNER,
    "comsol_connections": COMSOL_CONNECTIONS,
    "integration_source": PROJECT_ROOT
    / "nodi_simulator/sidewall_comsol_target_binding_qch_integration.py",
    "integration_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_package_c_sidewall_comsol_target_binding_qch_integration.py",
    "integration_tests": PROJECT_ROOT
    / "tests/test_sidewall_comsol_target_binding_qch_integration.py",
    "integration_builder_tests": PROJECT_ROOT
    / "tests/test_nodi_package_c_sidewall_comsol_target_binding_qch_integration.py",
}

BUILD_EDIT_PATHS = {
    "nodi_simulator/sidewall_comsol_target_binding_qch_integration.py",
    "tools/audits/build_nodi_package_c_sidewall_comsol_target_binding_qch_integration.py",
    "tests/test_sidewall_comsol_target_binding_qch_integration.py",
    "tests/test_nodi_package_c_sidewall_comsol_target_binding_qch_integration.py",
}

BLOCKED_USE = (
    "route_score;winner;JRC;yield;detection_probability;wet_pass_probability;"
    "clogging_rate;time_to_clog;recovery;production ingestion"
)
ALLOWED_USE = (
    "COMSOL launcher target binding;existing exact pressure-flow result provenance;"
    "formal q_ch sidecar route-formula input"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build COMSOL target binding and formal q_ch integration receipt."
    )
    parser.add_argument(
        "--confirm-sidewall-comsol-target-binding-qch-integration",
        action="store_true",
    )
    return parser


def run_git(args: list[str], cwd: Path = PROJECT_ROOT, *, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={cwd.as_posix()}", *args],
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if check:
        return result.stdout.strip()
    return result.stdout.strip() if result.returncode == 0 else ""


def git_head(cwd: Path = PROJECT_ROOT) -> str:
    return run_git(["rev-parse", "HEAD"], cwd, check=False) or "HEAD_UNKNOWN"


def git_branch() -> str:
    return run_git(["branch", "--show-current"])


def git_status_lines(cwd: Path = PROJECT_ROOT) -> list[str]:
    out = run_git(["status", "--short"], cwd, check=False)
    return [line for line in out.splitlines() if line.strip()]


def git_path_from_status_line(line: str) -> str:
    return line[2:].strip().replace("\\", "/") if len(line) > 2 else line


def display_path(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        try:
            return "COMSOL_REPO/" + path.relative_to(COMSOL_REPO).as_posix()
        except ValueError:
            return str(path)


def load_status(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    return data if isinstance(data, dict) else {}


def command_template() -> str:
    parts = [
        sys.executable,
        display_path(COMSOL_LAUNCHER),
        "--run",
        "--allow-comsol-run",
        "--ack-historical-comsol-run",
        "--allow-mph-load",
        "--ack-stage11-legacy-reference-only",
        "--ack-package-c-w500-d900-pressure-flow",
        "--write-nodi-external-result",
        "--hmax-um",
        "0.5",
        "--mesh-size",
        "9",
        "--nano-sweep-elements",
        "30",
        "--comsol-np",
        "24",
    ]
    return " ".join(parts)


def command_sha256(command: str) -> str:
    return hashlib.sha256(command.encode("utf-8")).hexdigest()


def source_hashes() -> dict[str, str]:
    mapping = {
        "launcher": COMSOL_LAUNCHER,
        "build_scaffold": COMSOL_BUILD_SCAFFOLD,
        "pressure_runner": COMSOL_PRESSURE_RUNNER,
        "connections": COMSOL_CONNECTIONS,
        "nodi_template": TEMPLATE_ROWS,
    }
    return {
        name: sha256_file(path) if path.exists() else ""
        for name, path in mapping.items()
    }


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
    rows: list[dict[str, str]] = []
    output_prefix = f"reports/joint_interface_20260701/{PREFIX}_"
    output_report = f"reports/566_{PREFIX}_20260701.md"
    for line in git_status_lines():
        path = git_path_from_status_line(line)
        if path in BUILD_EDIT_PATHS:
            classification = "comsol_target_qch_integration_build_edit"
            release_decision = "included_in_commit_scope_before_publish"
        elif path.startswith(output_prefix) or path == output_report:
            classification = "comsol_target_qch_integration_output"
            release_decision = "included_or_rewritten_by_integration_builder"
        else:
            classification = "non_release_dirty_context"
            release_decision = "ignored_for_comsol_target_qch_integration"
        rows.append(
            {
                "path": path,
                "git_status": line[:2],
                "classification": classification,
                "release_decision": release_decision,
            }
        )
    return rows


def route_evidence_delta_rows(integration_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in integration_rows:
        rows.append(
            {
                "evidence_delta_row_id": f"ROUTE-EVIDENCE-DELTA-{row['route_candidate_id']}-COMSOL-QCH",
                "source_integration_version": row["integration_version"],
                "route_candidate_id": row["route_candidate_id"],
                "route_geometry_family": row["route_geometry_family"],
                "evidence_lane": "comsol_pressure_flow_exact_qch",
                "evidence_class": "accepted_exact_pressure_flow_for_formal_qch_sidecar",
                "source_artifact_id": ARTIFACT_ID,
                "source_external_result_id": row["external_result_id"],
                "evidence_rows": 1,
                "accepted_claim_evidence_rows": 1 if row["formal_qch_sidecar_current"] else 0,
                "may_satisfy_route_formula_qch_branch_now": row[
                    "may_satisfy_route_formula_qch_branch_now"
                ],
                "may_satisfy_yield_now": False,
                "may_satisfy_detection_now": False,
                "q_ch_m3_s": row["q_ch_m3_s"],
                "formal_flow_split_fraction": row["formal_flow_split_fraction"],
                "route_score_current": False,
                "yield_current": False,
                "detection_probability_current": False,
                "current_state": "formal_qch_input_ready_not_route_score",
                "hard_fail_if": (
                    "formal_qch_exact_pressure_flow_input_used_as_route_score_yield_or_detection_without_formula_detector_wet_evidence"
                ),
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def semantic_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(
            {
                "integration_rows": payload["integration_rows"],
                "guard_rows": payload["guard_rows"],
                "route_evidence_delta_rows": payload["route_evidence_delta_rows"],
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


def build_payload() -> dict[str, Any]:
    command = command_template()
    rows, guards = build_comsol_target_binding_qch_integration(
        request_rows=read_csv_rows(REQUEST_ROWS),
        binding_rows=read_csv_rows(BINDING_ROWS),
        sidecar_rows=read_csv_rows(SIDECAR_ROWS),
        source_hashes=source_hashes(),
        launcher_path=display_path(COMSOL_LAUNCHER),
        launch_command_template=command,
        launch_command_template_sha256=command_sha256(command),
        comsol_repo_head=git_head(COMSOL_REPO),
        comsol_repo_dirty_count=len(git_status_lines(COMSOL_REPO)),
    )
    integration_rows = [row.to_dict() for row in rows]
    guard_rows = [row.to_dict() for row in guards]
    delta_rows = route_evidence_delta_rows(integration_rows)
    source_lock = source_lock_rows()
    dirty_context = dirty_context_rows()
    source_missing = sum(row["exists"] != "true" for row in source_lock)
    accepted_rows = sum(row["formal_qch_sidecar_current"] for row in integration_rows)
    qch_delta_ready = sum(
        row["may_satisfy_route_formula_qch_branch_now"] for row in delta_rows
    )
    status = (
        DISPOSITION
        if source_missing == 0
        and len(integration_rows) == 2
        and len(guard_rows) == 5
        and accepted_rows == 2
        and qch_delta_ready == 2
        and sum(row["route_score_current"] for row in integration_rows) == 0
        else BLOCKED_DISPOSITION
    )
    summary: dict[str, Any] = {
        "disposition": status,
        "artifact_id": ARTIFACT_ID,
        "integration_status": SIDEWALL_COMSOL_TARGET_BINDING_QCH_INTEGRATION_STATUS,
        "claim_boundary": CLAIM_BOUNDARY,
        "current_head": git_head(),
        "branch": git_branch(),
        "comsol_repo_head": git_head(COMSOL_REPO),
        "comsol_repo_dirty_count": len(git_status_lines(COMSOL_REPO)),
        "binder_disposition": str(load_status(BINDER_STATUS).get("disposition", "")),
        "launch_precondition_disposition": str(
            load_status(LAUNCH_PRECONDITION_STATUS).get("disposition", "")
        ),
        "integration_rows": len(integration_rows),
        "guard_rows": len(guard_rows),
        "route_evidence_delta_rows": len(delta_rows),
        "accepted_exact_pressure_flow_rows": accepted_rows,
        "formal_qch_sidecar_current_rows": accepted_rows,
        "route_formula_qch_branch_ready_rows": qch_delta_ready,
        "rectangle_rows": sum(
            row["route_geometry_family"] == "ideal_rectangle"
            for row in integration_rows
        ),
        "trapezoid_rows": sum(
            row["route_geometry_family"] == "trapezoid_tapered_sidewalls"
            for row in integration_rows
        ),
        "comsol_launch_required_for_current_qch_rows": sum(
            row["comsol_launch_required_for_current_qch"] for row in integration_rows
        ),
        "comsol_rerun_allowed_rows": sum(
            row["comsol_rerun_allowed_by_user_authorization"]
            for row in integration_rows
        ),
        "comsol_rerun_recommended_rows": sum(
            row["comsol_rerun_recommended_now"] for row in integration_rows
        ),
        "formal_qch_weighting_current": False,
        "route_score_current": False,
        "winner_current": False,
        "yield_current": False,
        "detection_probability_current": False,
        "production_ingestion_current": False,
        "source_lock_rows": len(source_lock),
        "source_missing_rows": source_missing,
        "dirty_context_rows": len(dirty_context),
        "non_release_dirty_context_rows": sum(
            row["classification"] == "non_release_dirty_context"
            for row in dirty_context
        ),
        "launch_command_template_sha256": command_sha256(command),
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    payload = {
        "summary": summary,
        "integration_rows": integration_rows,
        "guard_rows": guard_rows,
        "route_evidence_delta_rows": delta_rows,
        "source_lock_rows": source_lock,
        "dirty_context_rows": dirty_context,
        "command_rows": [
            {
                "command_id": "COMSOL-PACKAGE-C-W500-D900-RERUN-COMMAND",
                "command_template": command,
                "command_template_sha256": command_sha256(command),
                "launcher_path": display_path(COMSOL_LAUNCHER),
                "allowed_use": "authorized rerun only when a fresh COMSOL pressure-flow receipt is needed",
                "blocked_use": BLOCKED_USE,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        ],
    }
    payload["summary"]["semantic_digest"] = semantic_digest(payload)
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    summary = payload["summary"]
    if summary["disposition"] != DISPOSITION:
        failures.append("disposition_not_ready")
    if summary["integration_rows"] != 2:
        failures.append("expected_two_integration_rows")
    if summary["accepted_exact_pressure_flow_rows"] != 2:
        failures.append("expected_two_accepted_exact_pressure_flow_rows")
    if summary["route_formula_qch_branch_ready_rows"] != 2:
        failures.append("qch_branch_not_ready_for_both_routes")
    if summary["rectangle_rows"] != 1 or summary["trapezoid_rows"] != 1:
        failures.append("rectangle_and_trapezoid_parallelism_missing")
    for key in (
        "formal_qch_weighting_current",
        "route_score_current",
        "winner_current",
        "yield_current",
        "detection_probability_current",
        "production_ingestion_current",
    ):
        if summary[key] is not False:
            failures.append(f"{key}_unexpectedly_true")
    return failures


def write_outputs(payload: dict[str, Any]) -> list[Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "status": OUTPUT_DIR / f"{PREFIX}_STATUS_20260701.json",
        "integration_rows": OUTPUT_DIR / f"{PREFIX}_INTEGRATION_ROWS_20260701.csv",
        "guard_rows": OUTPUT_DIR / f"{PREFIX}_GUARD_ROWS_20260701.csv",
        "route_evidence_delta": OUTPUT_DIR
        / f"{PREFIX}_ROUTE_EVIDENCE_DELTA_ROWS_20260701.csv",
        "source_lock": OUTPUT_DIR / f"{PREFIX}_SOURCE_LOCK_20260701.csv",
        "dirty_context": OUTPUT_DIR / f"{PREFIX}_DIRTY_CONTEXT_20260701.csv",
        "command_lock": OUTPUT_DIR / f"{PREFIX}_COMMAND_LOCK_20260701.csv",
        "report_json": OUTPUT_DIR / f"{PREFIX}_REPORT_20260701.json",
        "master_report": REPORT_DIR / f"566_{PREFIX}_20260701.md",
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
    write_csv_rows(outputs["integration_rows"], payload["integration_rows"])
    write_csv_rows(outputs["guard_rows"], payload["guard_rows"])
    write_csv_rows(outputs["route_evidence_delta"], payload["route_evidence_delta_rows"])
    write_csv_rows(outputs["source_lock"], payload["source_lock_rows"])
    write_csv_rows(outputs["dirty_context"], payload["dirty_context_rows"])
    write_csv_rows(outputs["command_lock"], payload["command_rows"])
    write_json_atomic(outputs["report_json"], payload, sort_keys=True)
    outputs["master_report"].write_text(render_markdown(payload), encoding="utf-8")
    manifest = manifest_rows(outputs)
    write_csv_rows(outputs["manifest"], manifest)
    return list(outputs.values())


def manifest_rows(outputs: dict[str, Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for artifact_id, path in outputs.items():
        if artifact_id == "manifest":
            sha = SELF_MANIFEST_SHA256
        else:
            sha = sha256_file(path) if path.exists() else ""
        rows.append(
            {
                "artifact_id": artifact_id,
                "path": display_path(path),
                "sha256": sha,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        )
    return rows


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# NODI Package C Sidewall COMSOL Target Binding QCH Integration",
        "",
        f"Disposition: `{summary['disposition']}`",
        f"Artifact ID: `{summary['artifact_id']}`",
        f"Claim boundary: `{summary['claim_boundary']}`",
        "",
        "## What changed",
        "",
        "- Bound the W500/D900 COMSOL launcher, scaffold, pressure runner, connection map, and NODI template by sha256.",
        "- Confirmed the tracked exact pressure-flow result binder has two accepted rows: rectangle limit and theta85 trapezoid.",
        "- Promoted only the formal `q_ch` sidecar input branch into route-formula readiness; route score, winner, yield, detection probability, and production remain false here.",
        "- Recorded the rerun command template for future authorized COMSOL refreshes; no rerun is required for the current formal `q_ch` values.",
        "",
        "## Summary",
        "",
        f"- Accepted exact pressure-flow rows: `{summary['accepted_exact_pressure_flow_rows']}`",
        f"- Formal q_ch sidecar current rows: `{summary['formal_qch_sidecar_current_rows']}`",
        f"- Route formula q_ch branch ready rows: `{summary['route_formula_qch_branch_ready_rows']}`",
        f"- Rectangle rows: `{summary['rectangle_rows']}`",
        f"- Trapezoid rows: `{summary['trapezoid_rows']}`",
        f"- COMSOL rerun recommended rows: `{summary['comsol_rerun_recommended_rows']}`",
        f"- Route score current: `{summary['route_score_current']}`",
        f"- Yield current: `{summary['yield_current']}`",
        f"- Detection probability current: `{summary['detection_probability_current']}`",
        "",
        "## Next Use",
        "",
        "Downstream route/yield/detection work should consume `ROUTE_EVIDENCE_DELTA_ROWS` as the current pressure-flow/q_ch branch state. It still must join detector/blank transfer, wet observation, and route formula packets before any route score or yield/detection number is emitted.",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_sidewall_comsol_target_binding_qch_integration:
        raise SystemExit(
            "--confirm-sidewall-comsol-target-binding-qch-integration is required"
        )
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        raise SystemExit(f"Validation failed: {failures}")
    write_outputs(payload)
    print(payload["summary"]["disposition"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
