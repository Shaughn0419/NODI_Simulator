#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main"
GITHUB_BLOB_BASE = "https://github.com/Shaughn0419/NODI_Simulator/blob/main"

DISPOSITION = "NODI_PACKAGE_C_PROOF_REGISTRATION_ARTIFACT_REGISTERED_NO_RUNTIME"
ARTIFACT_ID = "PACKAGE_C_PROOF_REGISTRATION_ARTIFACT_20260701"
CLAIM_BOUNDARY = (
    "package_c_finite_step_reflection_surrogate_proof_registered_"
    "not_runtime_not_solver_not_wet"
)
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
GITHUB_VISIBILITY_STATUS = "local_worktree_pre_commit_urls_valid_after_publish"

ALLOWED_USE = (
    "Package C finite-step reflection surrogate proof registration;"
    "source/evidence-hash binding;Package C reflection-surrogate validation status"
)
BLOCKED_USE = (
    "runtime configuration;sidewall PRS/EAS numeric output;NODI runtime recomputation;"
    "COMSOL launch;.mph load;validated Brownian solver output beyond finite-step surrogate;"
    "validated hindered diffusion;trapezoid Poiseuille solver output;fixed-pressure q_ch output;"
    "flux-weighted sampling;electrokinetic grid output;optical solver output;true W_eff;"
    "reference strength claim;detector response claim;sidewall scattering claim;route_score;"
    "winner;JRC;q_ch weighting;yield;detection_probability;wet pass probability;"
    "clogging rate;time-to-clog;recovery;fabrication release;production ingestion"
)

STATUS_FILES = {
    "metric_hardening_status": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_STATUS_20260701.json",
    "timeseries_ess_status": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_STATUS_20260701.json",
    "stationarity_ensemble_status": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_STATUS_20260701.json",
    "one_wall_wall_pileup_status": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_STATUS_20260701.json",
    "near_boundary_expected_band_status": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_STATUS_20260701.json",
    "substep_fail_policy_status": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_SUBSTEP_FAIL_POLICY_STATUS_20260701.json",
    "substep_dt_refinement_status": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_SUBSTEP_DT_REFINEMENT_STATUS_20260701.json",
    "runtime_substep_policy_design_status": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_STATUS_20260701.json",
    "proof_threshold_status": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_STATUS_20260701.json",
    "proof_readiness_status": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_STATUS_20260701.json",
    "user_authorization_ledger_status": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_STATUS_20260701.json",
}

EVIDENCE_FILES = {
    **STATUS_FILES,
    "proof_threshold_table": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_TABLE_20260701.csv",
    "proof_readiness_index": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_INDEX_20260701.csv",
    "proof_readiness_blockers": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_BLOCKERS_20260701.csv",
    "user_authorization_ledger_scopes": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_SCOPES_20260701.csv",
    "user_authorization_ledger_guards": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_RESULT_GUARDS_20260701.csv",
    "stationarity_histograms": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_HISTOGRAMS_20260701.csv",
    "stationarity_confidence_intervals": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_CONFIDENCE_INTERVALS_20260701.csv",
    "one_wall_rows": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_ONE_WALL_20260701.csv",
    "wall_pileup_rows": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_WALL_PILEUP_20260701.csv",
    "near_boundary_rows": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_ROWS_20260701.csv",
    "substep_policy_rows": OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_ROWS_20260701.csv",
    "cross_section_geometry_source": PROJECT_ROOT / "nodi_simulator/cross_section_geometry.py",
    "trajectory_source": PROJECT_ROOT / "nodi_simulator/trajectory.py",
    "proof_registration_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_package_c_proof_registration_artifact.py",
    "proof_registration_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_package_c_proof_registration_artifact.py",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Register Package C finite-step reflection surrogate proof evidence."
    )
    parser.add_argument(
        "--confirm-package-c-proof-registration-artifact",
        action="store_true",
    )
    return parser


def safe_git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN_GIT_HEAD"


def read_json_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and isinstance(data.get("summary"), dict):
        return data["summary"]
    if isinstance(data, dict):
        return data
    return {}


def source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source_id, path in EVIDENCE_FILES.items():
        exists = path.exists()
        rows.append(
            {
                "source_id": source_id,
                "path": str(path.relative_to(PROJECT_ROOT)) if exists else str(path),
                "exists": str(exists).lower(),
                "sha256": sha256_file(path) if exists else "",
                "claim_boundary": CLAIM_BOUNDARY,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def threshold_rows() -> list[dict[str, str]]:
    threshold_path = EVIDENCE_FILES["proof_threshold_table"]
    if not threshold_path.exists():
        return []
    return read_csv_rows(threshold_path)


def registration_decision_rows() -> list[dict[str, str]]:
    threshold = read_json_summary(STATUS_FILES["proof_threshold_status"])
    readiness = read_json_summary(STATUS_FILES["proof_readiness_status"])
    auth = read_json_summary(STATUS_FILES["user_authorization_ledger_status"])
    decisions = [
        (
            "manual_authorization_bound",
            str(auth.get("package_c_proof_registration_path_authorized") is True).lower(),
            "user_authorization_ledger_accepts_proof_registration_path",
        ),
        (
            "proof_threshold_gaps_absent",
            str(threshold.get("proof_gap_rows") == 0).lower(),
            "proof_threshold_table_has_no_proof_gap_rows",
        ),
        (
            "proof_method_gaps_absent",
            str(threshold.get("proof_method_gap_rows") == 0).lower(),
            "proof_threshold_table_has_no_proof_method_gap_rows",
        ),
        (
            "path_authorization_accepted",
            str(readiness.get("path_authorization_accepted") is True).lower(),
            "readiness_index_records_path_authorization_without_runtime_result",
        ),
        (
            "package_c_proof_artifact_registered",
            "true",
            "finite_step_reflection_surrogate_evidence_registered",
        ),
        (
            "package_c_validation_status_pass_current",
            "true",
            "pass_scope_is_finite_step_reflection_surrogate_evidence_only",
        ),
    ]
    return [
        {
            "decision_id": decision_id,
            "decision_value": decision_value,
            "evidence_basis": evidence_basis,
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for decision_id, decision_value, evidence_basis in decisions
    ]


def post_registration_guard_rows() -> list[dict[str, str]]:
    guards = [
        ("runtime_allowed", "false", "runtime_execution_packet_still_required"),
        ("runtime_execution_started", "false", "no_runtime_started_by_registration"),
        ("nodi_runtime_recomputation_started", "false", "no_nodi_recompute_started"),
        ("sidewall_prs_eas_numeric_output_current", "false", "package_d_precheck_still_required"),
        ("comsol_launch_started", "false", "no_comsol_launch_started"),
        ("mph_load_started", "false", "no_mph_load_started"),
        ("validated_brownian_solver_output_current", "false", "finite_step_surrogate_not_exact_solver"),
        ("validated_hindered_diffusion_claim_current", "false", "hindered_diffusion_solver_evidence_required"),
        ("trapezoid_flow_solver_output_current", "false", "flow_solver_branch_evidence_required"),
        ("electrokinetic_solver_output_current", "false", "electrokinetic_solver_branch_evidence_required"),
        ("optical_solver_output_current", "false", "optical_solver_branch_evidence_required"),
        ("wet_claim_current", "false", "wet_experiment_evidence_required"),
        ("route_yield_detection_claim_current", "false", "route_yield_detection_claims_blocked"),
        ("fabrication_or_production_release_current", "false", "production_ingestion_blocked"),
    ]
    return [
        {
            "guard_field": field,
            "guard_value": value,
            "guard_status": status,
            "hard_fail_if": f"{field}_true_without_separate_execution_or_solver_wet_packet",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for field, value, status in guards
    ]


def runtime_blocker_rows() -> list[dict[str, str]]:
    threshold = read_json_summary(STATUS_FILES["proof_threshold_status"])
    rows = [
        (
            "runtime_policy_gap_rows",
            str(threshold.get("runtime_policy_gap_rows", "")),
            "runtime/substep implementation evidence remains required before runtime use",
        ),
        (
            "runtime_allowed",
            "false",
            "proof registration does not authorize runtime output",
        ),
        (
            "solver_wet_claims",
            "false",
            "solver/wet branches require separate evidence packets before claims",
        ),
    ]
    return [
        {
            "blocker_id": blocker_id,
            "current_value": current_value,
            "required_resolution": required_resolution,
            "blocker_status": "open_for_runtime_or_solver_wet_not_for_reflection_proof_registration",
            "claim_boundary": CLAIM_BOUNDARY,
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for blocker_id, current_value, required_resolution in rows
    ]


def build_payload() -> dict[str, Any]:
    threshold = read_json_summary(STATUS_FILES["proof_threshold_status"])
    readiness = read_json_summary(STATUS_FILES["proof_readiness_status"])
    auth = read_json_summary(STATUS_FILES["user_authorization_ledger_status"])
    locks = source_lock_rows()
    threshold_table_rows = threshold_rows()
    guards = post_registration_guard_rows()
    decisions = registration_decision_rows()
    runtime_blockers = runtime_blocker_rows()
    runtime_gap_rows = int(threshold.get("runtime_policy_gap_rows", 0) or 0)
    summary = {
        "disposition": DISPOSITION,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "registration_commit_sha": safe_git_head(),
        "reviewed_evidence_commit_sha": safe_git_head(),
        "proof_registration_authorized": True,
        "proof_registration_authorization_source": auth.get("artifact_id", ""),
        "package_c_proof_artifact_registered": True,
        "package_c_validation_status_pass_current": True,
        "package_c_validation_status_pass_scope": (
            "finite_step_reflection_surrogate_evidence_only"
        ),
        "validated_brownian_solver_output_current": False,
        "runtime_allowed": False,
        "numeric_prs_eas_allowed": False,
        "comsol_launch_allowed": False,
        "mph_load_allowed": False,
        "sidewall_prs_eas_numeric_output_current": False,
        "runtime_execution_started": False,
        "nodi_runtime_recomputation_started": False,
        "comsol_launch_started": False,
        "mph_load_started": False,
        "validated_hindered_diffusion_claim_current": False,
        "trapezoid_flow_solver_output_current": False,
        "electrokinetic_solver_output_current": False,
        "optical_solver_output_current": False,
        "wet_claim_current": False,
        "route_yield_detection_claim_current": False,
        "fabrication_or_production_release_current": False,
        "proof_threshold_rows": threshold.get("threshold_rows", len(threshold_table_rows)),
        "proof_gap_rows": threshold.get("proof_gap_rows", ""),
        "proof_method_gap_rows": threshold.get("proof_method_gap_rows", ""),
        "runtime_policy_gap_rows": runtime_gap_rows,
        "readiness_path_authorization_accepted": readiness.get(
            "path_authorization_accepted"
        ),
        "authorization_scope_rows": auth.get("authorized_scope_rows", ""),
        "source_lock_rows": len(locks),
        "source_missing_rows": sum(row["exists"] != "true" for row in locks),
        "registration_decision_rows": len(decisions),
        "post_registration_guard_rows": len(guards),
        "runtime_blocker_rows": len(runtime_blockers),
        "github_visibility_status": GITHUB_VISIBILITY_STATUS,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    return {
        "summary": summary,
        "registration_decisions": decisions,
        "source_locks": locks,
        "post_registration_guards": guards,
        "runtime_blockers": runtime_blockers,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    checks = {
        "Source lock complete": s["source_missing_rows"] == 0,
        "Manual authorization bound": s["authorization_scope_rows"] == 4,
        "Path authorization accepted": s["readiness_path_authorization_accepted"] is True,
        "Proof gaps absent": s["proof_gap_rows"] == 0,
        "Proof method gaps absent": s["proof_method_gap_rows"] == 0,
        "Threshold rows present": int(s["proof_threshold_rows"]) >= 16,
        "Proof registration authorized": s["proof_registration_authorized"] is True,
        "Proof artifact registered": s["package_c_proof_artifact_registered"] is True,
        "Package C finite-step pass current": (
            s["package_c_validation_status_pass_current"] is True
        ),
        "Scope is finite-step surrogate only": (
            s["package_c_validation_status_pass_scope"]
            == "finite_step_reflection_surrogate_evidence_only"
        ),
        "Runtime still blocked": s["runtime_allowed"] is False,
        "Numeric PRS/EAS still blocked": s["numeric_prs_eas_allowed"] is False,
        "COMSOL still blocked": s["comsol_launch_allowed"] is False,
        "MPH still blocked": s["mph_load_allowed"] is False,
        "Runtime gaps remain explicit": s["runtime_policy_gap_rows"] > 0,
    }
    for row in payload["post_registration_guards"]:
        checks[f"Guard false: {row['guard_field']}"] = row["guard_value"] == "false"
    return [label for label, ok in checks.items() if not ok]


def artifact_manifest_rows(
    paths: list[Path],
    *,
    output_dir: Path,
    report_dir: Path,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in paths:
        rows.append(
            {
                "artifact": path.name,
                "path": str(path.relative_to(PROJECT_ROOT))
                if path.is_relative_to(PROJECT_ROOT)
                else str(path),
                "sha256": sha256_file(path),
                "disposition": DISPOSITION,
                "policy_impact": "proof_registered_no_runtime",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    rows.append(
        {
            "artifact": "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_MANIFEST_20260701.csv",
            "path": str(
                (
                    output_dir
                    / "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_MANIFEST_20260701.csv"
                ).relative_to(PROJECT_ROOT)
            )
            if output_dir.is_relative_to(PROJECT_ROOT)
            else str(output_dir / "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_MANIFEST_20260701.csv"),
            "sha256": SELF_MANIFEST_SHA256,
            "disposition": DISPOSITION,
            "policy_impact": "manifest_self_row_no_recursive_sha",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    )
    return rows


def report_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    return "\n".join(
        [
            "# Package C Proof Registration Artifact",
            "",
            f"- Disposition: `{s['disposition']}`.",
            f"- Reviewed evidence commit: `{s['reviewed_evidence_commit_sha']}`.",
            "- Registered scope: finite-step reflection surrogate evidence only.",
            "- Package C proof artifact registered: `true`.",
            "- Package C validation status pass current: `true`, narrowly scoped to reflection-surrogate evidence.",
            "- Runtime allowed: `false`.",
            "- NODI recomputation, COMSOL launch, `.mph` load, numeric PRS/EAS, solver/wet, route/yield/detection, fabrication, and production claims remain blocked.",
            f"- Source lock rows: `{s['source_lock_rows']}`.",
            f"- Proof gap rows: `{s['proof_gap_rows']}`.",
            f"- Proof method gap rows: `{s['proof_method_gap_rows']}`.",
            f"- Runtime policy gap rows retained after proof registration: `{s['runtime_policy_gap_rows']}`.",
            "",
        ]
    )


def write_outputs(
    payload: dict[str, Any],
    *,
    output_dir: Path = OUTPUT_DIR,
    report_dir: Path = REPORT_DIR,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    csv_payloads = {
        "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_DECISIONS_20260701.csv": payload[
            "registration_decisions"
        ],
        "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_SOURCE_LOCK_20260701.csv": payload[
            "source_locks"
        ],
        "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_POST_GUARDS_20260701.csv": payload[
            "post_registration_guards"
        ],
        "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_RUNTIME_BLOCKERS_20260701.csv": payload[
            "runtime_blockers"
        ],
    }
    for filename, rows in csv_payloads.items():
        path = output_dir / filename
        write_csv_rows(path, rows)
        paths.append(path)

    status_path = output_dir / "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_STATUS_20260701.json"
    write_json_atomic(
        status_path,
        {
            "disposition": DISPOSITION,
            "summary": payload["summary"],
        },
    )
    paths.append(status_path)

    report_md_path = output_dir / "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_REPORT_20260701.md"
    report_md_path.write_text(report_markdown(payload), encoding="utf-8", newline="\n")
    paths.append(report_md_path)

    public_report_path = report_dir / "517_NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_ARTIFACT_20260701.md"
    public_report_path.write_text(
        report_markdown(payload),
        encoding="utf-8",
        newline="\n",
    )
    paths.append(public_report_path)

    report_json_path = output_dir / "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_REPORT_20260701.json"
    write_json_atomic(report_json_path, payload)
    paths.append(report_json_path)

    manifest_path = output_dir / "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_MANIFEST_20260701.csv"
    write_csv_rows(
        manifest_path,
        artifact_manifest_rows(paths, output_dir=output_dir, report_dir=report_dir),
    )
    paths.append(manifest_path)
    return paths


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.confirm_package_c_proof_registration_artifact:
        parser.error("--confirm-package-c-proof-registration-artifact is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_PACKAGE_C_PROOF_REGISTRATION_ARTIFACT")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
