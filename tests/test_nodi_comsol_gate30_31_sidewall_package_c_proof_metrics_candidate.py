from __future__ import annotations

import subprocess
import sys

from tools.audits import (
    build_nodi_comsol_gate30_31_sidewall_package_c_proof_metrics_candidate as gate3031,
)


def test_gate30_31_metric_payload_is_candidate_only_and_inside_support() -> None:
    payload = gate3031.build_metric_payload()
    failures = gate3031.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == gate3031.DISPOSITION
    assert summary["candidate_only"] is True
    assert summary["no_auth"] is True
    assert summary["proof_registration_authorized"] is False
    assert summary["package_c_validation_status_pass_authorized"] is False
    assert summary["runtime_allowed"] is False
    assert summary["numeric_prs_eas_allowed"] is False
    assert summary["comsol_launch_allowed"] is False
    assert summary["mph_load_allowed"] is False
    assert summary["support_invariance_status"] == "candidate_pass"
    assert summary["boundary_atom_status"] == "candidate_pass"
    assert summary["one_wall_limit_status"] == "candidate_pass"
    assert summary["rectangle_limit_status"] == "candidate_pass"
    assert summary["corner_active_set_status"] == "candidate_pass"
    assert summary["angle_depth_mutation_status"] == "candidate_pass"
    assert summary["closed_geometry_guard_rows"] > 0
    assert "gate30_31_build_base_commit_sha" in summary
    assert "gate30_31_build_head" not in summary
    assert summary["gate30_31_candidate_worktree_state"] == (
        "candidate_may_include_uncommitted_changes_not_reviewed_commit_binding"
    )


def test_gate30_31_parameter_and_seed_matrices_cover_required_grids() -> None:
    parameter_rows = gate3031._parameter_matrix_rows()
    seed_rows = gate3031._seed_matrix_rows()

    expected_parameter_rows = (
        len(gate3031.SIDEWALL_ANGLE_GRID_DEG_COMSOL)
        * len(gate3031.DEPTH_GRID_NM)
        * len(gate3031.PARTICLE_RADIUS_GRID_NM)
        * len(gate3031.DT_GRID_S)
    )
    assert len(parameter_rows) == expected_parameter_rows
    assert {row["sidewall_angle_deg_comsol"] for row in parameter_rows} >= {
        "90.0",
        "85.0",
        "70.0",
    }
    assert {row["particle_radius_nm"] for row in parameter_rows} >= {"110.0", "150.0"}
    assert len(seed_rows) == len(gate3031.RNG_SEEDS)
    assert all(row["claim_boundary"] == gate3031.CLAIM_BOUNDARY for row in seed_rows)


def test_gate30_31_candidate_manifest_has_all_contract_fields_not_registered() -> None:
    values = {field: "candidate_value" for field in gate3031.REQUIRED_PROOF_CONTRACT_FIELDS}
    rows = gate3031._candidate_manifest_rows(values)

    assert {row["required_field"] for row in rows} == gate3031.REQUIRED_PROOF_CONTRACT_FIELDS
    assert all(row["candidate_value_status"] == "candidate_only_not_registered" for row in rows)
    assert all(row["registration_status"] == "not_registered" for row in rows)
    assert all("Package C proof/pass registration" in row["blocked_use"] for row in rows)


def test_gate30_31_written_outputs_keep_future_bindings_pending_and_manifest_full() -> None:
    payload = gate3031.build_metric_payload()
    outputs = gate3031.write_outputs(payload)

    candidate_rows = gate3031.read_csv_rows(outputs["candidate_manifest"])
    by_field = {row["required_field"]: row for row in candidate_rows}
    for field in {
        "implementation_commit_sha",
        "external_review_artifact_sha256",
        "authorization_supersedes_no_auth_ledger_sha256",
        "independent_reviewer_id_or_artifact_sha256",
    }:
        assert by_field[field]["candidate_value"] == ""
        assert by_field[field]["candidate_value_status"] == "candidate_only_not_registered"
        assert by_field[field]["registration_status"] == "not_registered"

    manifest_rows = gate3031.read_csv_rows(outputs["manifest"])
    artifacts = {row["artifact"] for row in manifest_rows}
    assert len(manifest_rows) == 18
    assert "480_NODI_COMSOL_GATE30_31A_PACKAGE_C_REFLECTION_RAW_METRICS_CANDIDATE_20260630.md" in artifacts
    assert "481_NODI_COMSOL_GATE30_31B_PACKAGE_C_REFLECTION_SUMMARY_METRICS_CANDIDATE_20260630.md" in artifacts
    assert "482_NODI_COMSOL_GATE30_31C_PACKAGE_C_PROOF_CANDIDATE_MANIFEST_20260630.md" in artifacts
    assert "483_NODI_COMSOL_GATE30_31D_NO_PROOF_REGISTRATION_FIREWALL_20260630.md" in artifacts
    assert "484_NODI_COMSOL_GATE30_31_SIDEWALL_PACKAGE_C_PROOF_METRICS_CANDIDATE_MASTER_REPORT_20260630.md" in artifacts


def test_gate30_31_firewall_keeps_all_authorization_flags_false() -> None:
    firewall = gate3031._firewall_rows()[0]

    assert firewall["firewall_status"] == "PASS_GATE30_31_CANDIDATE_GENERATED_NO_PROOF_REGISTRATION"
    assert firewall["validated_brownian_solver_output_authorized"] == "false"
    assert firewall["wet_claim_authorized"] == "false"
    for key, value in firewall.items():
        if key.endswith("_authorized") or key == "package_c_proof_artifact_registered":
            assert value == "false", key


def test_gate30_31_external_review_prompt_preserves_narrow_candidate_boundary() -> None:
    payload = gate3031.build_metric_payload()
    text = gate3031._external_review_prompt_text(payload["summary"])

    assert gate3031.DISPOSITION in text
    assert "It is not Package C proof/pass registration" in text
    assert "It is not runtime authorization" in text
    assert "BLOCKED_CLAIM_PROMOTION" in text


def test_gate30_31_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate30_31_sidewall_package_c_proof_metrics_candidate.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate30-31-package-c-proof-metrics-candidate is required" in result.stderr
