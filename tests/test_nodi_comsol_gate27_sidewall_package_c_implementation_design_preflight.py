from __future__ import annotations

import csv
import json
import subprocess
import sys

from tools.audits import build_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight as gate27


def test_gate27_payload_passes_design_preflight_validation() -> None:
    payload = gate27.build_payload()

    assert gate27.validate_payload(payload) == []
    assert payload["summary"]["disposition"] == gate27.DISPOSITION
    assert payload["summary"]["gate26_head_is_ancestor_of_current"] is True
    assert payload["summary"]["gate26_disposition"] == gate27.EXPECTED_GATE26_DISPOSITION
    assert payload["summary"]["gate26_no_auth"] is True
    assert payload["summary"]["gate26_review_only"] is True


def test_gate27_locks_gate26_sources_without_missing_inputs() -> None:
    payload = gate27.build_payload()
    labels = {row["source_label"] for row in payload["gate26_source_locks"]}

    assert payload["summary"]["gate26_source_lock_rows"] >= 10
    assert payload["summary"]["gate26_source_missing"] == 0
    assert {row["lock_status"] for row in payload["gate26_source_locks"]} == {"MATCH"}
    assert {
        "status",
        "manifest",
        "external_feedback_capture",
        "brownian_requirements",
        "required_tests",
        "required_schema_fields",
        "blocked_model_ledger",
        "no_auth_firewall",
        "master_report",
    } <= labels


def test_gate27_backlog_maps_gate26_constraints_to_future_work_without_implementation() -> None:
    payload = gate27.build_payload()
    backlog = {row["package_c_component"]: row for row in payload["implementation_design_backlog"]}

    assert backlog["brownian_boundary_core"]["recommended_future_model"] == "skorokhod_normal_reflection_convex_offset_trapezoid_v1"
    assert "test_single_wall_reflection_matches_folded_normal_limit" in backlog["brownian_boundary_core"]["required_tests"]
    assert backlog["corner_active_set"]["recommended_future_model"] == "convex_polygon_normal_cone_active_set_v1"
    assert "test_dt_halving_converges_wall_distance_distribution" in backlog["brownian_equilibrium_and_dt_qa"]["required_tests"]
    assert backlog["hindered_diffusion_guard"]["current_status"] == "blocked_until_future_solver_or_surrogate_authorization"
    assert backlog["flow_guard"]["recommended_future_model"] == "fixed_velocity_plug_audit_only_no_qch"
    assert backlog["electrokinetic_guard"]["current_status"] == "blocked_until_future_grid_solver_authorization"
    assert backlog["optical_reference_guard"]["recommended_future_model"] == "proxy_only_not_solver_not_true_W_eff"
    assert all(row["implementation_authorized"] == "false" for row in backlog.values())
    assert all(row["runtime_allowed"] == "false" for row in backlog.values())
    assert all(row["proof_artifact_registered"] == "false" for row in backlog.values())


def test_gate27_proof_artifact_contract_requires_real_future_evidence() -> None:
    payload = gate27.build_payload()
    contract = {row["required_field"]: row for row in payload["proof_artifact_contract"]}

    required = {
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

    assert required <= set(contract)
    for row in contract.values():
        assert row["required_before_package_c_pass"] == "true"
        assert row["current_value"] == ""
        assert row["current_registration_status"] == "not_registered_fail_closed"
        assert row["accept_fixture_hash"] == "false"
        assert row["accept_row_local_id_without_source"] == "false"
        assert row["implementation_authorized"] == "false"
        assert row["runtime_allowed"] == "false"


def test_gate27_fail_closed_matrix_blocks_current_pass_and_claim_promotion() -> None:
    payload = gate27.build_payload()
    matrix = {row["trigger_condition"]: row for row in payload["fail_closed_matrix"]}

    assert matrix["missing_real_proof_artifact"]["affected_field_or_surface"] == "package_C_validation_status=pass"
    assert matrix["row_local_id_hash_only"]["required_response"] == "hard_fail_current_gate"
    assert matrix["projection_named_validated_reflection"]["affected_field_or_surface"] == "trajectory_boundary_claim_level"
    assert matrix["missing_dt_halving_evidence"]["required_response"] == "hard_fail_future_gate"
    assert matrix["boundary_atom_spike_detected"]["required_response"] == "hard_fail_future_gate"
    assert matrix["fixed_pressure_trapezoid_flow_without_solver"]["required_response"] == "hard_fail_current_gate"
    assert matrix["optical_true_W_eff_without_solver"]["affected_field_or_surface"] == "W_eff"
    assert matrix["any_runtime_or_comsol_authorization_flag_true"]["affected_field_or_surface"] == "no_auth_firewall"
    assert all(row["can_emit_sidewall_runtime_result"] == "false" for row in matrix.values())
    assert all(row["can_emit_numeric_prs_eas"] == "false" for row in matrix.values())
    assert all(row["can_update_proof_registry"] == "false" for row in matrix.values())


def test_gate27_no_auth_firewall_remains_closed() -> None:
    payload = gate27.build_payload()
    firewall = payload["no_auth_firewall"][0]

    assert firewall["firewall_status"] == "PASS_GATE27_DESIGN_PREFLIGHT_NO_AUTH"
    for key, value in firewall.items():
        if key.endswith("_authorized") or key == "package_c_proof_artifact_registered":
            assert value == "false", key
    assert firewall["package_c_validation_status_pass_authorized"] == "false"
    assert firewall["sidewall_prs_eas_numeric_output_authorized"] == "false"
    assert firewall["comsol_launch_authorized"] == "false"
    assert firewall["mph_load_authorized"] == "false"


def test_gate27_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate27-package-c-implementation-design-preflight is required" in result.stderr


def test_gate27_cli_confirmed_write_outputs_remain_no_auth() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight.py",
            "--confirm-gate27-package-c-implementation-design-preflight",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert gate27.DISPOSITION in result.stdout

    output_dir = gate27.OUTPUT_DIR
    status_path = output_dir / "NODI_COMSOL_GATE27_SIDEWALL_STATUS_20260630.json"
    manifest_path = output_dir / "NODI_COMSOL_GATE27_SIDEWALL_MANIFEST_20260630.csv"
    contract_path = output_dir / "NODI_COMSOL_GATE27_SIDEWALL_PROOF_ARTIFACT_CONTRACT_20260630.csv"
    status = json.loads(status_path.read_text(encoding="utf-8"))
    with manifest_path.open(newline="", encoding="utf-8") as handle:
        manifest = list(csv.DictReader(handle))

    assert status["disposition"] == gate27.DISPOSITION
    assert status["review_only"] is True
    assert status["no_auth"] is True
    assert status["summary"]["implementation_authorized_rows"] == 0
    assert status["summary"]["runtime_allowed_rows"] == 0
    assert status["summary"]["proof_artifact_registered_rows"] == 0
    assert status["summary"]["can_update_proof_registry_rows"] == 0
    assert contract_path.exists()
    assert "package_C_proof_artifact_id" in contract_path.read_text(encoding="utf-8")
    assert len(manifest) >= 8
    assert all((gate27.PROJECT_ROOT / row["path"]).exists() for row in manifest)
    assert all(row["policy_impact"] == "none_no_auth" for row in manifest)
