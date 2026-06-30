from __future__ import annotations

import subprocess
import sys

from tools.audits import build_nodi_comsol_gate29_sidewall_package_c_external_proof_review_integration as gate29


def test_gate29_payload_integrates_external_review_without_proof_registration() -> None:
    payload = gate29.build_payload()
    failures = gate29.validate_payload(payload)

    assert failures == []
    assert payload["summary"]["disposition"] == gate29.DISPOSITION
    assert payload["summary"]["external_verdict"] == gate29.EXTERNAL_VERDICT
    assert payload["summary"]["gate28_disposition"] == gate29.EXPECTED_GATE28_DISPOSITION
    assert payload["summary"]["gate28_evidence_pass_rows"] >= 6
    assert payload["summary"]["gate28_evidence_fail_rows"] == 0
    assert payload["summary"]["gate28_no_auth"] is True
    assert payload["summary"]["gate28_proof_registration_authorized"] is False
    assert payload["summary"]["gate27_proof_contract_field_rows"] == len(
        gate29.REQUIRED_PROOF_CONTRACT_FIELDS
    )
    assert payload["summary"]["gate27_missing_required_proof_contract_fields"] == []
    assert payload["summary"]["gate27_extra_proof_contract_fields"] == []
    assert payload["summary"]["proof_registration_authorized"] is False
    assert payload["summary"]["runtime_allowed"] is False
    assert payload["summary"]["numeric_prs_eas_allowed"] is False
    assert payload["summary"]["comsol_launch_allowed"] is False
    assert payload["summary"]["mph_load_allowed"] is False


def test_gate29_future_hard_gates_include_external_review_requirements() -> None:
    payload = gate29.build_payload()
    gates = {row["future_required_gate"] for row in payload["future_hard_gates"]}

    assert set(gate29.FUTURE_HARD_GATES) == gates
    assert "dt_convergence_evidence_sha256" in gates
    assert "equilibrium_uniformity_evidence_sha256" in gates
    assert "no_boundary_atom_evidence_sha256" in gates
    assert "corner_active_set_evidence_sha256" in gates
    assert "authorization_supersedes_no_auth_ledger_sha256" in gates
    assert "package_C_proof_no_wet_claim" in gates
    assert all(row["can_register_package_c_proof_now"] == "false" for row in payload["future_hard_gates"])


def test_gate29_telemetry_fields_include_reproducibility_matrix() -> None:
    payload = gate29.build_payload()
    fields = {row["required_future_field"] for row in payload["telemetry_fields"]}

    assert set(gate29.TELEMETRY_FIELDS) == fields
    assert "raw_metric_artifact_sha256" in fields
    assert "summary_metric_artifact_sha256" in fields
    assert "dt_grid_s" in fields
    assert "one_wall_limit_tolerance" in fields
    assert "independent_reviewer_id_or_artifact_sha256" in fields


def test_gate29_firewall_keeps_all_authorization_flags_false() -> None:
    payload = gate29.build_payload()
    firewall = payload["no_proof_firewall"][0]

    assert firewall["firewall_status"] == "PASS_GATE29_EXTERNAL_REVIEW_INTEGRATED_NO_PROOF_REGISTRATION"
    assert firewall["wet_claim_authorized"] == "false"
    assert firewall["wet_pass_probability_authorized"] == "false"
    assert firewall["clogging_rate_authorized"] == "false"
    assert firewall["time_to_clog_authorized"] == "false"
    assert firewall["recovery_authorized"] == "false"
    for key, value in firewall.items():
        if key.endswith("_authorized") or key == "package_c_proof_artifact_registered":
            assert value == "false", key


def test_gate29_external_review_capture_preserves_narrow_verdict() -> None:
    text = gate29.external_review_capture_text()

    assert gate29.EXTERNAL_VERDICT in text
    assert "This is not Package C proof/pass registration" in text
    assert "This is not runtime authorization" in text
    assert "finite_step_reflection_surrogate_validated_by_required_tests" in text


def test_gate29_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate29_sidewall_package_c_external_proof_review_integration.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate29-package-c-external-proof-review-integration is required" in result.stderr
