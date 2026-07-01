from __future__ import annotations

from functools import lru_cache
import json
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import (
    build_nodi_comsol_package_c_substep_fail_policy_hardening as hardening,
)


@lru_cache(maxsize=1)
def _payload() -> dict:
    return hardening.build_payload()


def test_substep_fail_policy_payload_hardens_proof_pass_without_promotion() -> None:
    payload = _payload()
    failures = hardening.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == hardening.DISPOSITION
    assert summary["timeseries_disposition"] == hardening.EXPECTED_TIMESERIES_DISPOSITION
    assert summary["policy_rows"] > 0
    assert summary["triggered_policy_rows"] == summary["policy_rows"]
    assert summary["proof_field_requirement_rows"] == len(hardening.PROOF_FIELD_REQUIREMENTS)
    assert summary["substep_trigger_metric"] == hardening.SUBSTEP_TRIGGER_METRIC
    assert summary["substep_trigger_threshold"] == hardening.SUBSTEP_TRIGGER_THRESHOLD
    assert summary["substep_max_observed_trigger_value"] > hardening.SUBSTEP_TRIGGER_THRESHOLD
    assert summary["substep_triggered_scenario_count"] == summary["triggered_policy_rows"]
    assert summary["substep_policy_bound_trigger_count"] == summary["triggered_policy_rows"]
    assert summary["substep_policy_scope"] == hardening.SUBSTEP_POLICY_SCOPE
    assert summary["github_visibility_status"] == hardening.GITHUB_VISIBILITY_STATUS
    assert summary["validator_hardening_status"] == hardening.VALIDATOR_HARDENING_STATUS
    assert summary["proof_readiness_impact"] == (
        "future_package_c_proof_pass_hard_fails_without_substep_policy_evidence"
    )
    assert summary["substep_review_required_for_current_candidate"] is True
    assert summary["proof_registration_authorized"] is False
    assert summary["package_c_validation_status_pass_authorized"] is False
    assert summary["runtime_allowed"] is False
    assert summary["numeric_prs_eas_allowed"] is False
    assert summary["comsol_launch_allowed"] is False
    assert summary["mph_load_allowed"] is False


def test_substep_fail_policy_rows_require_fail_or_reduce_dt() -> None:
    rows = _payload()["substep_fail_policy"]

    assert len(rows) > 0
    assert {row["substep_trigger_metric"] for row in rows} == {
        hardening.SUBSTEP_TRIGGER_METRIC
    }
    assert {row["substep_trigger_threshold"] for row in rows} == {
        str(hardening.SUBSTEP_TRIGGER_THRESHOLD)
    }
    assert {row["substep_triggered"] for row in rows} == {"true"}
    assert {row["required_future_policy"] for row in rows} == {
        "fail_or_reduce_dt_before_proof_pass_or_runtime"
    }
    assert {row["proof_pass_binding_status"] for row in rows} == {
        "hard_fail_until_fail_or_reduce_dt_policy_bound"
    }
    assert {row["runtime_policy_authorized"] for row in rows} == {"false"}
    assert all("runtime configuration" in row["blocked_use"] for row in rows)


def test_substep_proof_field_requirements_are_machine_readable() -> None:
    rows = _payload()["proof_field_requirements"]
    fields = {row["field"] for row in rows}

    assert {
        "substep_policy_evidence_sha256",
        "substep_policy_status",
        "substep_policy_scope",
        "substep_trigger_metric",
        "substep_trigger_threshold",
        "substep_max_observed_trigger_value",
        "substep_triggered_scenario_count",
        "substep_policy_bound_trigger_count",
        "substep_review_required",
        "substep_runtime_policy_authorized",
    } <= fields
    assert {row["validator_issue_id"] for row in rows} == {"SIDEWALL-D-PRECHECK-V03"}
    assert all(row["hard_fail_if"] for row in rows)


def test_substep_fail_policy_firewall_keeps_authorization_false() -> None:
    firewall = hardening.no_proof_firewall_rows()[0]

    assert firewall["firewall_status"] == (
        "PASS_PACKAGE_C_SUBSTEP_FAIL_POLICY_HARDENING_NO_PROOF_REGISTRATION"
    )
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
        }:
            assert value == "false", key


def test_substep_fail_policy_written_outputs_manifest_is_tmp_isolated(tmp_path) -> None:
    outputs = hardening.write_outputs(
        _payload(),
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    manifest_rows = read_csv_rows(outputs["manifest"])
    artifacts = {row["artifact"] for row in manifest_rows}
    by_artifact = {row["artifact"]: row for row in manifest_rows}

    assert "NODI_COMSOL_PACKAGE_C_SUBSTEP_FAIL_POLICY_ROWS_20260701.csv" in artifacts
    assert (
        "NODI_COMSOL_PACKAGE_C_SUBSTEP_PROOF_FIELD_REQUIREMENTS_20260701.csv"
        in artifacts
    )
    assert (
        "NODI_COMSOL_PACKAGE_C_SUBSTEP_FAIL_POLICY_STATUS_20260701.json"
        in artifacts
    )
    assert (
        "506_NODI_COMSOL_PACKAGE_C_SUBSTEP_FAIL_POLICY_HARDENING_20260701.md"
        in artifacts
    )
    report_payload = json.loads(outputs["report"].read_text(encoding="utf-8"))
    assert (
        "NODI_COMSOL_PACKAGE_C_SUBSTEP_FAIL_POLICY_MANIFEST_20260701.csv"
        in report_payload["outputs"]
    )
    assert by_artifact[
        "NODI_COMSOL_PACKAGE_C_SUBSTEP_FAIL_POLICY_MANIFEST_20260701.csv"
    ]["sha256"] == hardening.SELF_MANIFEST_SHA256


def test_substep_fail_policy_main_does_not_write_ready_outputs_on_validation_failure(
    monkeypatch,
    capsys,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        hardening,
        "build_payload",
        lambda: {"summary": {}, "no_proof_firewall": [{}]},
    )
    monkeypatch.setattr(hardening, "validate_payload", lambda payload: ["synthetic failure"])

    def _write_outputs_should_not_run(*args, **kwargs):
        calls.append("write_outputs")
        raise AssertionError("write_outputs should not run after validation failure")

    monkeypatch.setattr(hardening, "write_outputs", _write_outputs_should_not_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_nodi_comsol_package_c_substep_fail_policy_hardening.py",
            "--confirm-package-c-substep-fail-policy-hardening",
        ],
    )

    assert hardening.main() == 1
    captured = capsys.readouterr()
    assert "BLOCKED_PACKAGE_C_SUBSTEP_FAIL_POLICY_HARDENING" in captured.out
    assert "FAIL: synthetic failure" in captured.out
    assert calls == []


def test_substep_fail_policy_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_package_c_substep_fail_policy_hardening.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-package-c-substep-fail-policy-hardening is required" in result.stderr
