from __future__ import annotations

from functools import lru_cache
import json
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import (
    build_nodi_comsol_package_c_substep_dt_refinement_requirements as dt_refine,
)


@lru_cache(maxsize=1)
def _payload() -> dict:
    return dt_refine.build_payload()


def test_dt_refinement_payload_quantifies_substep_requirements_without_promotion() -> None:
    payload = _payload()
    failures = dt_refine.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == dt_refine.DISPOSITION
    assert (
        summary["substep_hardening_disposition"]
        == dt_refine.EXPECTED_SUBSTEP_HARDENING_DISPOSITION
    )
    assert summary["refinement_rows"] == 6
    assert summary["substep_trigger_metric"] == dt_refine.SUBSTEP_TRIGGER_METRIC
    assert summary["substep_trigger_threshold"] == dt_refine.SUBSTEP_TRIGGER_THRESHOLD
    assert summary["current_dt_s"] == dt_refine.CURRENT_DT_S
    assert summary["max_required_substeps_to_meet_threshold"] == 526
    assert summary["min_required_substeps_to_meet_threshold"] == 4
    assert summary["min_required_dt_s_to_meet_threshold"] < dt_refine.CURRENT_DT_S
    assert summary["max_projected_trigger_value_after_required_substeps"] <= 1.0
    assert summary["dt_refinement_candidate_status"] == (
        "requirements_complete_not_runtime_policy_not_proof"
    )
    assert summary["github_visibility_status"] == dt_refine.GITHUB_VISIBILITY_STATUS
    assert summary["proof_registration_authorized"] is False
    assert summary["package_c_validation_status_pass_authorized"] is False
    assert summary["runtime_allowed"] is False
    assert summary["numeric_prs_eas_allowed"] is False
    assert summary["comsol_launch_allowed"] is False
    assert summary["mph_load_allowed"] is False


def test_dt_refinement_rows_project_trigger_to_threshold() -> None:
    rows = _payload()["dt_refinement_requirements"]
    by_scenario = {row["scenario_id"]: row for row in rows}

    assert set(by_scenario) == {
        "rect_limit_theta90_D900_r20",
        "moderate_theta85_D900_r110",
        "deep_tail_theta85_D1200_r150",
        "steep_theta80_D900_r75",
        "stress_theta70_D900_r20",
        "narrow_tail_theta70_D900_r150",
    }
    assert by_scenario["rect_limit_theta90_D900_r20"][
        "required_substeps_to_meet_threshold"
    ] == "4"
    assert by_scenario["deep_tail_theta85_D1200_r150"][
        "required_substeps_to_meet_threshold"
    ] == "49"
    assert by_scenario["narrow_tail_theta70_D900_r150"][
        "required_substeps_to_meet_threshold"
    ] == "526"
    assert all(
        float(row["projected_trigger_value_after_required_substeps"]) <= 1.0
        for row in rows
    )
    assert {row["runtime_policy_authorized"] for row in rows} == {"false"}
    assert all("runtime configuration" in row["blocked_use"] for row in rows)


def test_dt_refinement_firewall_keeps_authorization_false() -> None:
    firewall = dt_refine.no_proof_firewall_rows()[0]

    assert firewall["firewall_status"] == (
        "PASS_PACKAGE_C_SUBSTEP_DT_REFINEMENT_REQUIREMENTS_NO_PROOF_REGISTRATION"
    )
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
        }:
            assert value == "false", key


def test_dt_refinement_written_outputs_manifest_is_tmp_isolated(tmp_path) -> None:
    outputs = dt_refine.write_outputs(
        _payload(),
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    manifest_rows = read_csv_rows(outputs["manifest"])
    artifacts = {row["artifact"] for row in manifest_rows}
    by_artifact = {row["artifact"]: row for row in manifest_rows}

    assert (
        "NODI_COMSOL_PACKAGE_C_SUBSTEP_DT_REFINEMENT_REQUIREMENTS_20260701.csv"
        in artifacts
    )
    assert (
        "NODI_COMSOL_PACKAGE_C_SUBSTEP_DT_REFINEMENT_STATUS_20260701.json"
        in artifacts
    )
    assert (
        "507_NODI_COMSOL_PACKAGE_C_SUBSTEP_DT_REFINEMENT_REQUIREMENTS_20260701.md"
        in artifacts
    )
    report_payload = json.loads(outputs["report"].read_text(encoding="utf-8"))
    assert (
        "NODI_COMSOL_PACKAGE_C_SUBSTEP_DT_REFINEMENT_MANIFEST_20260701.csv"
        in report_payload["outputs"]
    )
    assert by_artifact[
        "NODI_COMSOL_PACKAGE_C_SUBSTEP_DT_REFINEMENT_MANIFEST_20260701.csv"
    ]["sha256"] == dt_refine.SELF_MANIFEST_SHA256


def test_dt_refinement_main_does_not_write_ready_outputs_on_validation_failure(
    monkeypatch,
    capsys,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        dt_refine,
        "build_payload",
        lambda: {"summary": {}, "no_proof_firewall": [{}]},
    )
    monkeypatch.setattr(dt_refine, "validate_payload", lambda payload: ["synthetic failure"])

    def _write_outputs_should_not_run(*args, **kwargs):
        calls.append("write_outputs")
        raise AssertionError("write_outputs should not run after validation failure")

    monkeypatch.setattr(dt_refine, "write_outputs", _write_outputs_should_not_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_nodi_comsol_package_c_substep_dt_refinement_requirements.py",
            "--confirm-package-c-substep-dt-refinement-requirements",
        ],
    )

    assert dt_refine.main() == 1
    captured = capsys.readouterr()
    assert "BLOCKED_PACKAGE_C_SUBSTEP_DT_REFINEMENT_REQUIREMENTS" in captured.out
    assert "FAIL: synthetic failure" in captured.out
    assert calls == []


def test_dt_refinement_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_package_c_substep_dt_refinement_requirements.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert (
        "--confirm-package-c-substep-dt-refinement-requirements is required"
        in result.stderr
    )
