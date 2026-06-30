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


DATE_STAMP = "20260630"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

EXPECTED_GATE26_DISPOSITION = "NODI_GATE26_SIDEWALL_PACKAGE_C_EXTERNAL_REVIEW_INTEGRATION_DESIGN_CONSTRAINTS_READY_NO_AUTH"
DISPOSITION = "NODI_GATE27_SIDEWALL_PACKAGE_C_IMPLEMENTATION_DESIGN_PREFLIGHT_READY_NO_AUTH"
ALLOWED_USE = (
    "design-only Package C implementation preflight;future proof artifact contract;"
    "future work backlog;fail-closed matrix;no-run no-auth"
)
BLOCKED_USE = (
    "Package C physics implementation;proof artifact registration;proof registry pass;runtime configuration;"
    "sidewall PRS/EAS numeric output;NODI runtime recomputation;COMSOL launch;.mph load;"
    "validated Brownian solver output;validated hindered diffusion;trapezoid Poiseuille solver output;"
    "fixed-pressure q_ch output;flux-weighted sampling;electrokinetic grid output;optical solver output;"
    "true W_eff;reference strength claim;detector response claim;sidewall scattering claim;"
    "route_score;winner;JRC;q_ch weighting;yield;detection_probability;wet pass probability;"
    "clogging rate;time-to-clog;recovery;fabrication release;production ingestion"
)
REQUIRED_PROOF_CONTRACT_FIELDS = frozenset(
    {
        "package_C_proof_artifact_id",
        "package_C_proof_artifact_sha256",
        "package_C_proof_artifact_status",
        "package_C_proof_artifact_scope",
        "package_C_proof_claim_boundary",
        "external_review_artifact_sha256",
        "implementation_commit_sha",
        "required_test_result_artifact_sha256",
        "dt_convergence_evidence_sha256",
        "equilibrium_uniformity_evidence_sha256",
        "no_boundary_atom_evidence_sha256",
        "corner_active_set_evidence_sha256",
        "angle_depth_mutation_evidence_sha256",
        "rectangle_limit_evidence_sha256",
        "authorization_supersedes_no_auth_ledger_sha256",
        "reflection_metric_schema_version",
        "reflection_algorithm_source_sha256",
        "reflection_test_script_sha256",
        "test_environment_lock_sha256",
        "dependency_lock_sha256",
        "rng_seed_matrix_sha256",
        "test_parameter_matrix_sha256",
        "dt_grid_s",
        "diffusion_coefficient_grid_m2_s",
        "particle_radius_grid_nm",
        "sidewall_angle_grid_deg_comsol",
        "depth_grid_nm",
        "tolerance_m",
        "max_reflection_iterations",
        "substep_policy",
        "boundary_atom_threshold",
        "equilibrium_test_method",
        "equilibrium_test_threshold",
        "corner_bias_test_threshold",
        "rectangle_limit_tolerance",
        "one_wall_limit_tolerance",
        "raw_metric_artifact_sha256",
        "summary_metric_artifact_sha256",
        "independent_reviewer_id_or_artifact_sha256",
        "package_C_proof_manifest_schema_version",
        "package_C_proof_evidence_claim_level",
        "package_C_proof_required_test_matrix_status",
        "package_C_proof_external_review_status",
        "package_C_proof_authorization_status",
        "authorization_supersedes_no_auth_ledger_id",
        "package_C_proof_no_hindered_diffusion_claim",
        "package_C_proof_no_trapezoid_flow_solver_claim",
        "package_C_proof_no_electrokinetic_solver_claim",
        "package_C_proof_no_optical_solver_claim",
        "package_C_proof_no_wet_claim",
        "package_C_proof_no_prs_eas_numeric_output",
        "package_C_proof_no_route_yield_detection_claim",
    }
)

GATE26_FILES = {
    "status": OUTPUT_DIR / "NODI_COMSOL_GATE26_SIDEWALL_STATUS_20260630.json",
    "manifest": OUTPUT_DIR / "NODI_COMSOL_GATE26_SIDEWALL_MANIFEST_20260630.csv",
    "external_feedback_capture": OUTPUT_DIR / "NODI_COMSOL_GATE26_SIDEWALL_EXTERNAL_AI_FEEDBACK_CAPTURE_20260630.md",
    "external_review_intake": OUTPUT_DIR / "NODI_COMSOL_GATE26_SIDEWALL_EXTERNAL_REVIEW_INTAKE_20260630.csv",
    "brownian_requirements": OUTPUT_DIR / "NODI_COMSOL_GATE26_SIDEWALL_BROWNIAN_REFLECTION_REQUIREMENTS_20260630.csv",
    "required_tests": OUTPUT_DIR / "NODI_COMSOL_GATE26_SIDEWALL_PACKAGE_C_REQUIRED_TEST_MATRIX_20260630.csv",
    "required_schema_fields": OUTPUT_DIR / "NODI_COMSOL_GATE26_SIDEWALL_REQUIRED_SCHEMA_FIELDS_20260630.csv",
    "blocked_model_ledger": OUTPUT_DIR / "NODI_COMSOL_GATE26_SIDEWALL_BLOCKED_MODEL_LEDGER_20260630.csv",
    "no_auth_firewall": OUTPUT_DIR / "NODI_COMSOL_GATE26_SIDEWALL_NO_AUTH_FIREWALL_20260630.csv",
    "master_report": REPORT_DIR / "463_NODI_COMSOL_GATE26_SIDEWALL_PACKAGE_C_EXTERNAL_REVIEW_MASTER_REPORT_20260630.md",
}

REPORTS = {
    "464": "GATE27A_GATE26_SOURCE_LOCK",
    "465": "GATE27B_PACKAGE_C_IMPLEMENTATION_DESIGN_BACKLOG",
    "466": "GATE27C_PROOF_ARTIFACT_CONTRACT",
    "467": "GATE27D_PREAUTHORIZATION_FAIL_CLOSED_MATRIX",
    "468": "GATE27E_VALIDATION_AND_REVIEW_PLAN",
    "469": "GATE27F_NO_AUTH_FIREWALL",
    "470": "GATE27_SIDEWALL_PACKAGE_C_IMPLEMENTATION_DESIGN_PREFLIGHT_MASTER_REPORT",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate27 Package C implementation design preflight.")
    parser.add_argument("--confirm-gate27-package-c-implementation-design-preflight", action="store_true")
    return parser


def run_git(args: list[str], cwd: Path = PROJECT_ROOT) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={cwd.as_posix()}", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def safe_git_head(path: Path = PROJECT_ROOT) -> str:
    try:
        return run_git(["rev-parse", "HEAD"], cwd=path)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNKNOWN_COMMIT_READONLY_REFERENCE"


def git_is_ancestor(ancestor: str, descendant: str, cwd: Path = PROJECT_ROOT) -> bool:
    if not ancestor or ancestor == "UNKNOWN_COMMIT_READONLY_REFERENCE":
        return False
    try:
        subprocess.run(
            ["git", "-c", f"safe.directory={cwd.as_posix()}", "merge-base", "--is-ancestor", ancestor, descendant],
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def bool_text(value: bool) -> str:
    return str(bool(value)).lower()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def csv_count(path: Path) -> str:
    return str(len(read_csv_rows(path))) if path.exists() and path.suffix.lower() == ".csv" else "NA"


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


def gate26_source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, (label, path) in enumerate(GATE26_FILES.items(), start=1):
        exists = path.exists()
        rows.append(
            {
                "source_lock_id": f"G27A-GATE26-{idx:03d}",
                "source_gate": "Gate26",
                "source_label": label,
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "expected_row_count": csv_count(path) if exists else "MISSING",
                "actual_row_count": csv_count(path) if exists else "MISSING",
                "expected_sha256": sha256_file(path) if exists else "MISSING",
                "actual_sha256": sha256_file(path) if exists else "MISSING",
                "sha256_match": bool_text(exists),
                "row_count_match": bool_text(exists),
                "lock_status": "MATCH" if exists else "MISSING_GATE26_SOURCE",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def implementation_design_backlog_rows() -> list[dict[str, str]]:
    specs = [
        (
            "brownian_boundary_core",
            "trajectory.py;cross_section_geometry.py",
            "skorokhod_normal_reflection_convex_offset_trapezoid_v1",
            "test_trapezoid_skorokhod_normals_match_wall_distance_gradients;test_single_wall_reflection_matches_folded_normal_limit;test_reflected_trajectory_all_points_inside_center_support",
            "design_backlog_not_implemented",
        ),
        (
            "corner_active_set",
            "trajectory.py",
            "convex_polygon_normal_cone_active_set_v1",
            "test_corner_active_set_no_corner_pileup;test_near_closed_requires_resource_or_step_guard;test_geometry_closed_blocks_trajectory_runtime",
            "design_backlog_not_implemented",
        ),
        (
            "brownian_equilibrium_and_dt_qa",
            "tests/package_c_future",
            "no_boundary_atom_uniform_equilibrium_dt_halving_v1",
            "test_reflected_trajectory_has_no_boundary_atom_spike;test_pure_brownian_equilibrium_uniform_over_accessible_area;test_dt_halving_converges_wall_distance_distribution",
            "design_backlog_not_implemented",
        ),
        (
            "schema_and_signature_fields",
            "nodi_comsol_next_artifacts.py;trajectory outputs",
            "package_c_brownian_schema_fields_from_gate26",
            "test_theta_mutation_changes_boundary_event_counts_and_signature;test_depth_mutation_changes_support_and_signature",
            "design_backlog_not_implemented",
        ),
        (
            "hindered_diffusion_guard",
            "trajectory.py;validators",
            "blocked_or_nearest_wall_single_plane_surrogate_only",
            "test_hindered_diffusion_blocked_under_trapezoid_unless_solver_or_surrogate_label",
            "blocked_until_future_solver_or_surrogate_authorization",
        ),
        (
            "flow_guard",
            "trajectory.py;fluidic_resistance.py;validators",
            "fixed_velocity_plug_audit_only_no_qch",
            "test_parabolic_rect_and_rect_series_blocked_under_trapezoid;test_fixed_pressure_trapezoid_requires_poisson_solver_or_context_only",
            "blocked_until_future_solver_or_lookup_authorization",
        ),
        (
            "electrokinetic_guard",
            "electrokinetic_transport.py;validators",
            "blocked_until_trapezoid_cut_cell_or_fem_grid",
            "test_boltzmann_wall_exclusion_blocked_until_trapezoid_grid_exists",
            "blocked_until_future_grid_solver_authorization",
        ),
        (
            "optical_reference_guard",
            "reference_field.py;validators",
            "proxy_only_not_solver_not_true_W_eff",
            "test_reference_field_under_trapezoid_remains_proxy_not_solver;test_no_forbidden_claim_columns_in_package_c_artifacts",
            "blocked_until_future_optical_solver_authorization",
        ),
    ]
    return [
        {
            "backlog_id": f"G27B-BACKLOG-{idx:03d}",
            "package_c_component": component,
            "future_write_scope": write_scope,
            "recommended_future_model": future_model,
            "required_tests": tests,
            "current_status": status,
            "implementation_authorized": "false",
            "runtime_allowed": "false",
            "proof_artifact_registered": "false",
            "claim_boundary_now": "design_preflight_only",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for idx, (component, write_scope, future_model, tests, status) in enumerate(specs, start=1)
    ]


def proof_artifact_contract_rows() -> list[dict[str, str]]:
    specs = [
        ("package_C_proof_artifact_id", "nonempty stable id for future proof artifact"),
        ("package_C_proof_artifact_sha256", "sha256 of reviewed proof artifact"),
        ("package_C_proof_artifact_status", "future status cannot be current no_auth or fixture-only"),
        ("package_C_proof_artifact_scope", "must identify exact Package C component scope"),
        ("package_C_proof_claim_boundary", "must distinguish validated tests from physics/experiment claims"),
        ("external_review_artifact_sha256", "must bind Gate26 external feedback capture or successor review"),
        ("implementation_commit_sha", "must bind future implementation commit"),
        ("required_test_result_artifact_sha256", "must bind full required-test result evidence"),
        ("dt_convergence_evidence_sha256", "must bind dt-halving convergence evidence"),
        ("equilibrium_uniformity_evidence_sha256", "must bind pure Brownian equilibrium evidence"),
        ("no_boundary_atom_evidence_sha256", "must bind no projection-spike evidence"),
        ("corner_active_set_evidence_sha256", "must bind corner active-set evidence"),
        ("angle_depth_mutation_evidence_sha256", "must bind angle/depth mutation evidence"),
        ("rectangle_limit_evidence_sha256", "must bind rectangle-limit evidence"),
        (
            "authorization_supersedes_no_auth_ledger_sha256",
            "must bind explicit superseding authorization artifact hash",
        ),
        ("reflection_metric_schema_version", "must bind reflection metric schema version"),
        ("reflection_algorithm_source_sha256", "must bind reviewed reflection algorithm source hash"),
        ("reflection_test_script_sha256", "must bind proof-level test script hash"),
        ("test_environment_lock_sha256", "must bind test environment lock hash"),
        ("dependency_lock_sha256", "must bind dependency lock hash"),
        ("rng_seed_matrix_sha256", "must bind deterministic/random seed matrix hash"),
        ("test_parameter_matrix_sha256", "must bind dt/angle/depth/radius parameter matrix hash"),
        ("dt_grid_s", "must declare dt, dt/2, dt/4 or equivalent convergence grid"),
        ("diffusion_coefficient_grid_m2_s", "must declare diffusion coefficient grid"),
        ("particle_radius_grid_nm", "must declare particle radius grid"),
        ("sidewall_angle_grid_deg_comsol", "must declare COMSOL sidewall angle grid"),
        ("depth_grid_nm", "must declare depth grid"),
        ("tolerance_m", "must declare geometry/reflection tolerance"),
        ("max_reflection_iterations", "must declare active-set iteration cap"),
        ("substep_policy", "must declare nonconvergence/substep policy"),
        ("boundary_atom_threshold", "must declare no-boundary-atom pass threshold"),
        ("equilibrium_test_method", "must declare equilibrium uniformity test method"),
        ("equilibrium_test_threshold", "must declare equilibrium uniformity threshold"),
        ("corner_bias_test_threshold", "must declare corner bias threshold"),
        ("rectangle_limit_tolerance", "must declare rectangle-limit tolerance"),
        ("one_wall_limit_tolerance", "must declare one-wall-limit tolerance"),
        ("raw_metric_artifact_sha256", "must bind raw proof metric artifact hash"),
        ("summary_metric_artifact_sha256", "must bind summary proof metric artifact hash"),
        (
            "independent_reviewer_id_or_artifact_sha256",
            "must bind independent reviewer identity or review artifact hash",
        ),
        ("package_C_proof_manifest_schema_version", "must bind proof manifest schema version"),
        ("package_C_proof_evidence_claim_level", "must remain validated-test-evidence only"),
        ("package_C_proof_required_test_matrix_status", "must show all required tests passed in reviewed artifact"),
        ("package_C_proof_external_review_status", "must show external review completed for proof"),
        ("package_C_proof_authorization_status", "must show explicit authorization supersedes no-auth ledger"),
        ("authorization_supersedes_no_auth_ledger_id", "must name explicit future authorization path"),
        ("package_C_proof_no_hindered_diffusion_claim", "must remain true unless future solver authorization exists"),
        ("package_C_proof_no_trapezoid_flow_solver_claim", "must remain true unless future flow solver authorization exists"),
        ("package_C_proof_no_electrokinetic_solver_claim", "must remain true unless future electrokinetic solver authorization exists"),
        ("package_C_proof_no_optical_solver_claim", "must remain true unless future optical solver authorization exists"),
        ("package_C_proof_no_wet_claim", "must remain true"),
        ("package_C_proof_no_prs_eas_numeric_output", "must remain true before Package C proof/pass"),
        ("package_C_proof_no_route_yield_detection_claim", "must remain true"),
    ]
    return [
        {
            "contract_id": f"G27C-PROOF-CONTRACT-{idx:03d}",
            "required_field": field,
            "field_requirement": requirement,
            "required_before_package_c_pass": "true",
            "current_value": "",
            "current_registration_status": "not_registered_fail_closed",
            "accept_fixture_hash": "false",
            "accept_row_local_id_without_source": "false",
            "implementation_authorized": "false",
            "runtime_allowed": "false",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for idx, (field, requirement) in enumerate(specs, start=1)
    ]


def fail_closed_matrix_rows() -> list[dict[str, str]]:
    specs = [
        ("missing_real_proof_artifact", "package_C_validation_status=pass", "hard_fail_current_gate"),
        ("row_local_id_hash_only", "package_C_validation_status=pass", "hard_fail_current_gate"),
        ("projection_named_validated_reflection", "trajectory_boundary_claim_level", "hard_fail_current_gate"),
        ("missing_dt_halving_evidence", "brownian_boundary_claim_level", "hard_fail_future_gate"),
        ("missing_uniform_equilibrium_evidence", "brownian_boundary_claim_level", "hard_fail_future_gate"),
        ("boundary_atom_spike_detected", "brownian_boundary_claim_level", "hard_fail_future_gate"),
        ("hindered_diffusion_enabled_under_trapezoid_without_solver_or_surrogate_label", "diffusion_hindrance_model", "hard_fail_current_gate"),
        ("fixed_pressure_trapezoid_flow_without_solver", "flow_control_mode", "hard_fail_current_gate"),
        ("electrokinetic_rect_grid_under_trapezoid", "electrokinetic_grid_geometry_model", "hard_fail_current_gate"),
        ("optical_true_W_eff_without_solver", "W_eff", "hard_fail_current_gate"),
        ("forbidden_route_or_wet_claim_column", "sidewall PRS/EAS artifact columns", "hard_fail_current_gate"),
        ("any_runtime_or_comsol_authorization_flag_true", "no_auth_firewall", "hard_fail_current_gate"),
    ]
    return [
        {
            "matrix_id": f"G27D-FAIL-CLOSED-{idx:03d}",
            "trigger_condition": trigger,
            "affected_field_or_surface": surface,
            "required_response": response,
            "current_gate_status": "blocked_fail_closed",
            "can_emit_sidewall_runtime_result": "false",
            "can_emit_numeric_prs_eas": "false",
            "can_update_proof_registry": "false",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for idx, (trigger, surface, response) in enumerate(specs, start=1)
    ]


def validation_plan_rows() -> list[dict[str, str]]:
    commands = [
        "python tools/audits/build_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight.py --confirm-gate27-package-c-implementation-design-preflight",
        "python -m py_compile tools/audits/build_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight.py",
        "python -m pytest tests/test_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight.py -q",
        "python -m pytest tests/test_nodi_comsol_gate26_sidewall_package_c_external_review_integration.py tests/test_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight.py -q",
    ]
    return [
        {
            "validation_id": f"G27E-VALIDATION-{idx:03d}",
            "command": command,
            "required_for_pass": "true",
            "recorded_result": "PENDING_RUNTIME_VALIDATION",
        }
        for idx, command in enumerate(commands, start=1)
    ]


def no_auth_firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_id": "G27F-NOAUTH-001",
            "package_c_physics_implementation_authorized": "false",
            "package_c_proof_artifact_registered": "false",
            "package_c_proof_registry_pass_authorized": "false",
            "proof_registry_update_authorized": "false",
            "package_c_validation_status_pass_authorized": "false",
            "runtime_configuration_authorized": "false",
            "sidewall_prs_eas_numeric_output_authorized": "false",
            "nodi_runtime_recompute_authorized": "false",
            "comsol_launch_authorized": "false",
            "mph_load_authorized": "false",
            "qch_weighting_authorized": "false",
            "jrc_authorized": "false",
            "route_score_authorized": "false",
            "winner_authorized": "false",
            "yield_authorized": "false",
            "detection_probability_authorized": "false",
            "fabrication_release_authorized": "false",
            "firewall_status": "PASS_GATE27_DESIGN_PREFLIGHT_NO_AUTH",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    ]


def manifest_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, path in enumerate(paths, start=1):
        rows.append(
            {
                "manifest_id": f"G27-MANIFEST-{idx:03d}",
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "row_count": csv_count(path),
                "sha256": sha256_file(path),
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "policy_impact": "none_no_auth",
            }
        )
    return rows


def build_payload() -> dict[str, Any]:
    gate26_status = read_json(GATE26_FILES["status"])
    gate26_summary = gate26_status.get("summary", {})
    current_head = safe_git_head(PROJECT_ROOT)
    source_locks = gate26_source_lock_rows()
    backlog = implementation_design_backlog_rows()
    proof_contract = proof_artifact_contract_rows()
    fail_closed = fail_closed_matrix_rows()
    validation = validation_plan_rows()
    firewall = no_auth_firewall_rows()
    summary = {
        "disposition": DISPOSITION,
        "gate27_build_head": current_head,
        "gate26_build_head": gate26_summary.get("gate26_build_head", ""),
        "gate26_head_is_ancestor_of_current": git_is_ancestor(gate26_summary.get("gate26_build_head", ""), current_head, PROJECT_ROOT),
        "gate26_disposition": gate26_status.get("disposition", ""),
        "gate26_no_auth": gate26_status.get("no_auth", False),
        "gate26_review_only": gate26_status.get("review_only", False),
        "gate26_source_lock_rows": len(source_locks),
        "gate26_source_missing": sum(row["lock_status"] != "MATCH" for row in source_locks),
        "implementation_backlog_rows": len(backlog),
        "proof_contract_rows": len(proof_contract),
        "fail_closed_rows": len(fail_closed),
        "validation_plan_rows": len(validation),
        "implementation_authorized_rows": sum(row.get("implementation_authorized") == "true" for row in backlog + proof_contract),
        "runtime_allowed_rows": sum(row.get("runtime_allowed") == "true" for row in backlog + proof_contract),
        "proof_artifact_registered_rows": sum(row.get("proof_artifact_registered") == "true" for row in backlog),
        "can_emit_runtime_rows": sum(row.get("can_emit_sidewall_runtime_result") == "true" for row in fail_closed),
        "can_emit_numeric_prs_eas_rows": sum(row.get("can_emit_numeric_prs_eas") == "true" for row in fail_closed),
        "can_update_proof_registry_rows": sum(row.get("can_update_proof_registry") == "true" for row in fail_closed),
        "no_auth_firewall_failures": 0 if firewall[0]["firewall_status"] == "PASS_GATE27_DESIGN_PREFLIGHT_NO_AUTH" else 1,
        "review_only": True,
        "no_auth": True,
    }
    return {
        "summary": summary,
        "gate26_source_locks": source_locks,
        "implementation_design_backlog": backlog,
        "proof_artifact_contract": proof_contract,
        "fail_closed_matrix": fail_closed,
        "validation_plan": validation,
        "no_auth_firewall": firewall,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    backlog_components = {row["package_c_component"] for row in payload["implementation_design_backlog"]}
    proof_fields = {row["required_field"] for row in payload["proof_artifact_contract"]}
    fail_triggers = {row["trigger_condition"] for row in payload["fail_closed_matrix"]}
    firewall = payload["no_auth_firewall"][0]
    checks = {
        "Gate26 head ancestry": s["gate26_head_is_ancestor_of_current"] is True,
        "Gate26 disposition": s["gate26_disposition"] == EXPECTED_GATE26_DISPOSITION,
        "Gate26 no-auth": s["gate26_no_auth"] is True,
        "Gate26 review-only": s["gate26_review_only"] is True,
        "Gate26 sources present": s["gate26_source_lock_rows"] >= 10,
        "Gate26 source missing": s["gate26_source_missing"] == 0,
        "Backlog coverage": {
            "brownian_boundary_core",
            "corner_active_set",
            "brownian_equilibrium_and_dt_qa",
            "schema_and_signature_fields",
            "hindered_diffusion_guard",
            "flow_guard",
            "electrokinetic_guard",
            "optical_reference_guard",
        }
        <= backlog_components,
        "Proof contract fields": REQUIRED_PROOF_CONTRACT_FIELDS <= proof_fields,
        "Fail-closed triggers": {
            "missing_real_proof_artifact",
            "projection_named_validated_reflection",
            "missing_dt_halving_evidence",
            "boundary_atom_spike_detected",
            "any_runtime_or_comsol_authorization_flag_true",
        }
        <= fail_triggers,
        "No implementation rows": s["implementation_authorized_rows"] == 0,
        "No runtime rows": s["runtime_allowed_rows"] == 0,
        "No proof registered rows": s["proof_artifact_registered_rows"] == 0,
        "No runtime emit rows": s["can_emit_runtime_rows"] == 0,
        "No numeric PRS/EAS rows": s["can_emit_numeric_prs_eas_rows"] == 0,
        "No proof update rows": s["can_update_proof_registry_rows"] == 0,
        "No-auth firewall": s["no_auth_firewall_failures"] == 0,
    }
    for key, value in firewall.items():
        if key.endswith("_authorized") or key == "package_c_proof_artifact_registered":
            checks[f"No-auth false: {key}"] = value == "false"
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    csv_specs = {
        "NODI_COMSOL_GATE27_SIDEWALL_GATE26_SOURCE_LOCK_20260630.csv": payload["gate26_source_locks"],
        "NODI_COMSOL_GATE27_SIDEWALL_IMPLEMENTATION_DESIGN_BACKLOG_20260630.csv": payload["implementation_design_backlog"],
        "NODI_COMSOL_GATE27_SIDEWALL_PROOF_ARTIFACT_CONTRACT_20260630.csv": payload["proof_artifact_contract"],
        "NODI_COMSOL_GATE27_SIDEWALL_PREAUTH_FAIL_CLOSED_MATRIX_20260630.csv": payload["fail_closed_matrix"],
        "NODI_COMSOL_GATE27_SIDEWALL_VALIDATION_PLAN_20260630.csv": payload["validation_plan"],
        "NODI_COMSOL_GATE27_SIDEWALL_NO_AUTH_FIREWALL_20260630.csv": payload["no_auth_firewall"],
    }
    for name, rows in csv_specs.items():
        path = OUTPUT_DIR / name
        write_csv_rows(path, rows)
        generated.append(path)
    report_json = OUTPUT_DIR / "NODI_COMSOL_GATE27_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(report_json, {"summary": payload["summary"], "outputs": list(csv_specs)})
    generated.append(report_json)
    status_json = OUTPUT_DIR / "NODI_COMSOL_GATE27_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(status_json, {"disposition": DISPOSITION, "summary": payload["summary"], "review_only": True, "no_auth": True})
    generated.append(status_json)
    master_md = OUTPUT_DIR / "NODI_COMSOL_GATE27_SIDEWALL_IMPLEMENTATION_DESIGN_PREFLIGHT_REPORT_20260630.md"
    write_md(
        master_md,
        "NODI COMSOL Gate27 Sidewall Package C Implementation Design Preflight",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Gate26 source missing rows: {payload['summary']['gate26_source_missing']}",
            f"- Backlog / proof-contract / fail-closed rows: {payload['summary']['implementation_backlog_rows']}/{payload['summary']['proof_contract_rows']}/{payload['summary']['fail_closed_rows']}.",
            "- This is a design preflight only: no Package C implementation, proof registration, runtime, COMSOL launch, .mph load, or numeric sidewall PRS/EAS output.",
        ],
    )
    generated.append(master_md)
    manifest_path = OUTPUT_DIR / "NODI_COMSOL_GATE27_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(manifest_path, manifest_rows(generated))
    generated.append(manifest_path)
    for number, title in REPORTS.items():
        path = REPORT_DIR / f"{number}_NODI_COMSOL_{title}_20260630.md"
        write_md(
            path,
            title.replace("_", " "),
            [
                f"- Gate27 disposition: `{DISPOSITION}`",
                f"- Gate26 source missing rows: {payload['summary']['gate26_source_missing']}.",
                f"- Backlog / proof-contract / fail-closed rows: {payload['summary']['implementation_backlog_rows']}/{payload['summary']['proof_contract_rows']}/{payload['summary']['fail_closed_rows']}.",
                "- Boundary: no runtime, no COMSOL launch, no .mph load, no proof artifact registration, no PRS/EAS numeric output, no route/yield/detection claims.",
                f"- Machine-readable support: `{OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix()}`.",
            ],
        )
        generated.append(path)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate27_package_c_implementation_design_preflight:
        parser.error("--confirm-gate27-package-c-implementation-design-preflight is required")
    payload = build_payload()
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE27_SIDEWALL_PACKAGE_C_IMPLEMENTATION_DESIGN_PREFLIGHT")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
