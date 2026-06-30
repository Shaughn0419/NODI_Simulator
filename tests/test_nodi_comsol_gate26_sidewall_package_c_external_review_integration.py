from __future__ import annotations

import csv
import json
import subprocess
import sys

from tools.audits import build_nodi_comsol_gate26_sidewall_package_c_external_review_integration as gate26


def test_gate26_payload_passes_external_review_integration_validation() -> None:
    payload = gate26.build_payload()

    assert gate26.validate_payload(payload) == []
    assert payload["summary"]["disposition"] == gate26.DISPOSITION
    assert payload["summary"]["external_review_verdict"] == gate26.EXTERNAL_VERDICT
    assert payload["summary"]["gate25_head_is_ancestor_of_current"] is True
    assert payload["summary"]["gate25_disposition"] == gate26.EXPECTED_GATE25_DISPOSITION
    assert payload["summary"]["gate25_no_auth"] is True
    assert payload["summary"]["gate25_review_only"] is True


def test_gate26_locks_gate25_and_external_feedback_sources() -> None:
    payload = gate26.build_payload()
    source_labels = {row["source_label"] for row in payload["gate25_source_locks"]}

    assert payload["summary"]["gate25_source_lock_rows"] >= 8
    assert payload["summary"]["gate25_source_drift"] == 0
    assert payload["summary"]["gate25_missing_sources"] == 0
    assert {row["lock_status"] for row in payload["gate25_source_locks"]} == {"MATCH"}
    assert {
        "status",
        "manifest",
        "design_scope",
        "external_prompt",
        "master_report",
        "gate24_auth_ledger",
        "roadmap",
        "audit_packet",
        "external_ai_feedback_capture",
    } <= source_labels


def test_gate26_external_review_intake_is_design_only_not_authorization() -> None:
    payload = gate26.build_payload()
    intake = payload["external_review_intake"][0]

    assert intake["external_feedback_artifact_id"] == gate26.EXTERNAL_FEEDBACK_ARTIFACT_ID
    assert intake["external_feedback_sha256"] == gate26.sha256_text(gate26.external_feedback_capture_text())
    assert intake["external_feedback_visibility_status"] == "user_pasted_chat_feedback_captured_by_gate26"
    assert intake["external_review_verdict"] == "READY_FOR_IMPLEMENTATION_DESIGN_ONLY"
    assert intake["implementation_authorized"] == "false"
    assert intake["runtime_allowed"] == "false"
    assert intake["projection_as_validated_reflection_allowed"] == "false"
    assert payload["summary"]["implementation_authorized_rows"] == 0
    assert payload["summary"]["runtime_allowed_rows"] == 0


def test_gate26_brownian_requirements_preserve_projection_as_surrogate() -> None:
    payload = gate26.build_payload()
    rows = {row["requirement_family"]: row for row in payload["brownian_reflection_requirements"]}

    assert rows["target_model"]["required_value"] == "skorokhod_normal_reflection_convex_offset_trapezoid_v1"
    assert rows["target_model"]["allowed_claim_level_now"] == "design_requirement_only"
    assert rows["current_projection_claim"]["current_state"] == "trapezoid_center_support_projection_boundary_v1"
    assert rows["current_projection_claim"]["required_value"] == "sidewall_projection_boundary_surrogate_not_specular_reflection"
    assert "validated reflection" in rows["current_projection_claim"]["fail_condition"]
    assert rows["corner_active_set"]["required_value"] == "convex_polygon_normal_cone_active_set_v1"
    assert rows["uniform_equilibrium"]["required_field_or_model"] == "equilibrium_uniformity_check_status"
    assert rows["dt_halving"]["required_field_or_model"] == "dt_halving_convergence_status"
    assert rows["closed_geometry_guard"]["required_value"] == "geometry_closed_or_near_closed_blocks_or_substeps_runtime"
    assert all(row["implementation_authorized"] == "false" for row in rows.values())


def test_gate26_required_tests_capture_external_review_hard_requirements() -> None:
    payload = gate26.build_payload()
    tests = {row["test_name"]: row for row in payload["required_test_matrix"]}

    required = {
        "test_trapezoid_skorokhod_normals_match_wall_distance_gradients",
        "test_single_wall_reflection_matches_folded_normal_limit",
        "test_projection_boundary_has_no_validated_reflection_claim",
        "test_reflected_trajectory_all_points_inside_center_support",
        "test_reflected_trajectory_has_no_boundary_atom_spike",
        "test_pure_brownian_equilibrium_uniform_over_accessible_area",
        "test_corner_active_set_no_corner_pileup",
        "test_dt_halving_converges_wall_distance_distribution",
        "test_hindered_diffusion_blocked_under_trapezoid_unless_solver_or_surrogate_label",
        "test_parabolic_rect_and_rect_series_blocked_under_trapezoid",
        "test_boltzmann_wall_exclusion_blocked_until_trapezoid_grid_exists",
        "test_reference_field_under_trapezoid_remains_proxy_not_solver",
        "test_no_forbidden_claim_columns_in_package_c_artifacts",
    }

    assert required <= set(tests)
    for row in tests.values():
        assert row["required_before_package_c_pass"] == "true"
        assert row["implementation_authorized"] == "false"
        assert row["runtime_allowed"] == "false"
        assert row["output_numeric_prs_eas_allowed"] == "false"


def test_gate26_required_schema_fields_cover_brownian_flow_ek_optical_guards() -> None:
    payload = gate26.build_payload()
    fields = {row["field_name"]: row for row in payload["required_schema_fields"]}

    required = {
        "brownian_boundary_target_model",
        "brownian_boundary_numerical_scheme",
        "brownian_boundary_claim_level",
        "not_ballistic_specular_collision_claim",
        "projection_boundary_surrogate_used",
        "reflection_update_rule_id",
        "wall_constraint_formula_id",
        "active_wall_set",
        "corner_handling_model",
        "boundary_atom_fraction",
        "equilibrium_uniformity_check_status",
        "rectangle_limit_check_status",
        "one_wall_neumann_kernel_check_status",
        "diffusion_hindrance_claim_level",
        "hindered_diffusion_solver_required_reason",
        "trapezoid_flow_solver_status",
        "fixed_pressure_hydraulic_resistance_status",
        "not_qch_weighted",
        "electrokinetic_grid_geometry_model",
        "electrokinetic_solver_status",
        "optical_solver_status",
        "optical_solver_required_reason",
        "not_true_W_eff",
        "not_detector_response_claim",
        "not_sidewall_scattering_claim",
    }

    assert required <= set(fields)
    assert fields["brownian_boundary_target_model"]["field_group"] == "brownian_reflection"
    assert fields["not_qch_weighted"]["field_group"] == "flow"
    assert fields["not_true_W_eff"]["field_group"] == "optical_reference"
    assert all(row["allowed_now"] == "design_requirement_only" for row in fields.values())


def test_gate26_blocked_model_ledger_keeps_physics_and_claims_closed() -> None:
    payload = gate26.build_payload()
    blockers = {row["model_scope"]: row for row in payload["blocked_model_ledger"]}

    assert blockers["hindered_diffusion_trapezoid"]["current_status"] == "blocked"
    assert blockers["single_wall_hindrance_optional_future"]["allowed_claim_level"] == "surrogate_sensitivity_only"
    assert blockers["fixed_velocity_plug_flow_audit"]["current_status"] == "allowed_design_only"
    assert "q_ch" in blockers["fixed_velocity_plug_flow_audit"]["forbidden_claims"]
    assert blockers["trapezoid_velocity_field"]["current_status"] == "blocked_future_solver"
    assert blockers["fixed_pressure_hydraulic_resistance"]["allowed_claim_level"] == "solver_required_or_context_only"
    assert blockers["electrokinetic_trapezoid"]["current_status"] == "blocked"
    assert "true_W_eff" in blockers["reference_field_optical"]["forbidden_claims"]
    assert "fabrication_release" in blockers["route_and_production_claims"]["forbidden_claims"]
    assert all(row["implementation_authorized"] == "false" for row in blockers.values())
    assert all(row["runtime_allowed"] == "false" for row in blockers.values())


def test_gate26_no_auth_firewall_remains_closed() -> None:
    payload = gate26.build_payload()
    firewall = payload["no_auth_firewall"][0]

    assert firewall["firewall_status"] == "PASS_GATE26_DESIGN_ONLY_NO_AUTH"
    for key, value in firewall.items():
        if key.endswith("_authorized"):
            assert value == "false", key
    assert firewall["projection_boundary_validated_reflection_authorized"] == "false"
    assert firewall["hindered_diffusion_trapezoid_authorized"] == "false"
    assert firewall["trapezoid_poiseuille_authorized"] == "false"
    assert firewall["electrokinetic_trapezoid_solver_authorized"] == "false"
    assert firewall["optical_solver_output_authorized"] == "false"


def test_gate26_does_not_register_package_c_proof_or_pass_status() -> None:
    payload = gate26.build_payload()
    firewall = payload["no_auth_firewall"][0]
    intake = payload["external_review_intake"][0]

    assert firewall["package_c_proof_registry_pass_authorized"] == "false"
    assert firewall["proof_registry_update_authorized"] == "false"
    assert intake["claim_boundary"] == "design_only_no_auth_not_runtime_not_numeric_prs_eas"
    assert "proof registry pass" in gate26.BLOCKED_USE
    assert "Package C physics implementation" in gate26.BLOCKED_USE


def test_gate26_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate26_sidewall_package_c_external_review_integration.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate26-package-c-external-review-integration is required" in result.stderr


def test_gate26_cli_confirmed_write_outputs_remain_design_only() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate26_sidewall_package_c_external_review_integration.py",
            "--confirm-gate26-package-c-external-review-integration",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert gate26.DISPOSITION in result.stdout

    output_dir = gate26.OUTPUT_DIR
    status_path = output_dir / "NODI_COMSOL_GATE26_SIDEWALL_STATUS_20260630.json"
    manifest_path = output_dir / "NODI_COMSOL_GATE26_SIDEWALL_MANIFEST_20260630.csv"
    brownian_path = output_dir / "NODI_COMSOL_GATE26_SIDEWALL_BROWNIAN_REFLECTION_REQUIREMENTS_20260630.csv"
    feedback_path = output_dir / "NODI_COMSOL_GATE26_SIDEWALL_EXTERNAL_AI_FEEDBACK_CAPTURE_20260630.md"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        manifest = list(csv.DictReader(handle))

    assert status["disposition"] == gate26.DISPOSITION
    assert status["review_only"] is True
    assert status["no_auth"] is True
    assert status["summary"]["implementation_authorized_rows"] == 0
    assert status["summary"]["runtime_allowed_rows"] == 0
    assert status["summary"]["no_auth_firewall_failures"] == 0
    assert brownian_path.exists()
    assert feedback_path.exists()
    assert gate26.EXTERNAL_VERDICT in feedback_path.read_text(encoding="utf-8")
    assert "skorokhod_normal_reflection_convex_offset_trapezoid_v1" in brownian_path.read_text(encoding="utf-8")
    assert len(manifest) >= 10
    assert all((gate26.PROJECT_ROOT / row["path"]).exists() for row in manifest)
    assert all(row["policy_impact"] == "none_no_auth" for row in manifest)
