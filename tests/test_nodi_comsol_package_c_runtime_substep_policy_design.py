from __future__ import annotations

from functools import lru_cache
import json
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import (
    build_nodi_comsol_package_c_runtime_substep_policy_design as policy,
)


@lru_cache(maxsize=1)
def _payload() -> dict:
    return policy.build_payload()


def test_runtime_substep_policy_payload_designs_without_authorizing_runtime() -> None:
    payload = _payload()
    failures = policy.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == policy.DISPOSITION
    assert summary["policy_rows"] == 6
    assert summary["field_requirement_rows"] >= 8
    assert summary["max_required_substeps_to_meet_threshold"] == 526
    assert summary["prohibitive_substep_cost_rows"] == 1
    assert summary["runtime_substep_policy_design_status"] == (
        "policy_design_bound_not_runtime_authorized"
    )
    assert summary["runtime_policy_authorization_status"] == "missing_not_authorized"
    assert summary["proof_registration_authorized"] is False
    assert summary["package_c_validation_status_pass_authorized"] is False
    assert summary["runtime_allowed"] is False
    assert summary["numeric_prs_eas_allowed"] is False
    assert summary["comsol_launch_allowed"] is False
    assert summary["mph_load_allowed"] is False


def test_runtime_substep_policy_rows_classify_cost_without_reusing_as_runtime_config() -> None:
    rows = _payload()["runtime_substep_policy_rows"]
    by_scenario = {row["scenario_id"]: row for row in rows}

    assert by_scenario["narrow_tail_theta70_D900_r150"]["substep_policy_class"] == (
        "prohibitive_substep_cost_manual_runtime_authorization_required"
    )
    assert by_scenario["narrow_tail_theta70_D900_r150"][
        "required_substeps_to_meet_threshold"
    ] == "526"
    assert by_scenario["deep_tail_theta85_D1200_r150"]["substep_policy_class"] == (
        "moderate_substep_cost_design_review"
    )
    assert {
        row["runtime_policy_authorized"] for row in rows
    } == {"false"}
    assert all(
        row["proof_pass_binding_status"]
        == "runtime_policy_design_bound_but_not_authorized_not_proof_registered"
        for row in rows
    )
    assert all(row["claim_boundary"] == policy.CLAIM_BOUNDARY for row in rows)


def test_runtime_substep_policy_field_requirements_are_machine_readable() -> None:
    fields = _payload()["field_requirements"]
    by_field = {row["field"]: row for row in fields}

    assert "runtime_substep_policy_evidence_sha256" in by_field
    assert "runtime_substep_policy_authorized" in by_field
    assert "required_substeps_to_meet_threshold" in by_field
    assert "substep_implementation_test_status" in by_field
    assert by_field["runtime_substep_policy_authorized"]["hard_fail_if"] == (
        "true_without_manual_authorization_ledger"
    )
    assert all(row["allowed_use"] == policy.ALLOWED_USE for row in fields)
    assert all(row["blocked_use"] == policy.BLOCKED_USE for row in fields)


def test_runtime_substep_policy_firewall_keeps_authorization_false() -> None:
    firewall = policy.no_proof_firewall_rows()[0]

    assert firewall["firewall_status"] == (
        "PASS_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_NO_RUNTIME_AUTHORIZATION"
    )
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
        }:
            assert value == "false", key


def test_runtime_substep_policy_written_outputs_manifest_is_tmp_isolated(tmp_path) -> None:
    outputs = policy.write_outputs(
        _payload(),
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    manifest_rows = read_csv_rows(outputs["manifest"])
    artifacts = {row["artifact"] for row in manifest_rows}
    by_artifact = {row["artifact"]: row for row in manifest_rows}

    assert (
        "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_ROWS_20260701.csv"
        in artifacts
    )
    assert (
        "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_FIELD_REQUIREMENTS_20260701.csv"
        in artifacts
    )
    assert (
        "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_STATUS_20260701.json"
        in artifacts
    )
    assert "514_NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_20260701.md" in artifacts
    report_payload = json.loads(outputs["report"].read_text(encoding="utf-8"))
    assert (
        "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_MANIFEST_20260701.csv"
        in report_payload["outputs"]
    )
    assert by_artifact[
        "NODI_COMSOL_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN_MANIFEST_20260701.csv"
    ]["sha256"] == policy.SELF_MANIFEST_SHA256


def test_runtime_substep_policy_main_does_not_write_ready_outputs_on_validation_failure(
    monkeypatch,
    capsys,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        policy,
        "build_payload",
        lambda: {"summary": {}, "no_proof_firewall": [{}], "runtime_substep_policy_rows": []},
    )
    monkeypatch.setattr(policy, "validate_payload", lambda payload: ["synthetic failure"])

    def _write_outputs_should_not_run(*args, **kwargs):
        calls.append("write_outputs")
        raise AssertionError("write_outputs should not run after validation failure")

    monkeypatch.setattr(policy, "write_outputs", _write_outputs_should_not_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_nodi_comsol_package_c_runtime_substep_policy_design.py",
            "--confirm-package-c-runtime-substep-policy-design",
        ],
    )

    assert policy.main() == 1
    captured = capsys.readouterr()
    assert "BLOCKED_PACKAGE_C_RUNTIME_SUBSTEP_POLICY_DESIGN" in captured.out
    assert "FAIL: synthetic failure" in captured.out
    assert calls == []


def test_runtime_substep_policy_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_package_c_runtime_substep_policy_design.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-package-c-runtime-substep-policy-design is required" in result.stderr
