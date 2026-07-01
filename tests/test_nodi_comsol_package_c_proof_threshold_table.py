from __future__ import annotations

from functools import lru_cache
import json
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_package_c_proof_threshold_table as thresholds


@lru_cache(maxsize=1)
def _payload() -> dict:
    return thresholds.build_payload()


def test_threshold_table_payload_separates_candidate_pass_from_proof_gaps() -> None:
    payload = _payload()
    failures = thresholds.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == thresholds.DISPOSITION
    assert summary["threshold_rows"] >= 10
    assert summary["candidate_pass_rows"] > 0
    assert summary["proof_gap_rows"] == 0
    assert summary["proof_method_gap_rows"] > 0
    assert summary["runtime_policy_gap_rows"] > 0
    assert summary["threshold_table_status"] == (
        "candidate_threshold_table_ready_not_proof_registered"
    )
    assert summary["proof_readiness_impact"] == (
        "numeric_proof_threshold_gaps_reduced_to_method_authorization_and_runtime_policy_gaps"
    )
    assert summary["proof_registration_authorized"] is False
    assert summary["package_c_validation_status_pass_authorized"] is False
    assert summary["runtime_allowed"] is False
    assert summary["numeric_prs_eas_allowed"] is False
    assert summary["comsol_launch_allowed"] is False
    assert summary["mph_load_allowed"] is False


def test_threshold_rows_cover_key_package_c_metrics() -> None:
    rows = _payload()["threshold_rows"]
    by_metric = {row["metric_id"]: row for row in rows}

    assert "support_violation_rows" in by_metric
    assert "max_exact_boundary_atom_fraction" in by_metric
    assert "max_one_wall_positive_control_ks" in by_metric
    assert "max_u_accessible_cdf_l1_to_uniform" in by_metric
    assert "substep_policy_bound_trigger_count" in by_metric
    assert "max_required_substeps_to_meet_threshold" in by_metric
    assert by_metric["max_required_substeps_to_meet_threshold"]["observed_value"] == "526"
    assert (
        by_metric["max_required_substeps_to_meet_threshold"]["current_status"]
        == "candidate_sized_runtime_policy_gap"
    )
    assert by_metric["min_effective_sample_size"]["source_artifact"] == (
        "stationarity_ensemble_refinement"
    )
    assert float(by_metric["min_effective_sample_size"]["observed_value"]) >= 32768.0
    assert by_metric["max_u_accessible_cdf_l1_to_uniform"]["current_status"] == (
        "candidate_and_proof_threshold_met_not_registered"
    )
    assert float(by_metric["max_u_accessible_cdf_l1_to_uniform"]["observed_value"]) <= 0.04
    assert by_metric["max_x_local_norm_l1_to_uniform"]["current_status"] == (
        "candidate_and_proof_threshold_met_not_registered"
    )
    assert float(by_metric["max_x_local_norm_l1_to_uniform"]["observed_value"]) <= 0.04
    assert by_metric["max_one_wall_positive_control_ks"]["source_artifact"] == (
        "one_wall_wall_pileup_refinement"
    )
    assert by_metric["max_one_wall_positive_control_ks"]["current_status"] == (
        "candidate_and_proof_threshold_met_not_registered"
    )
    assert float(by_metric["max_one_wall_positive_control_ks"]["observed_value"]) <= 0.01
    assert by_metric["max_expanded_wall_pileup_ratio"]["source_artifact"] == (
        "one_wall_wall_pileup_refinement"
    )
    assert by_metric["max_expanded_wall_pileup_ratio"]["current_status"] == (
        "candidate_and_proof_threshold_met_not_registered"
    )
    assert float(by_metric["max_expanded_wall_pileup_ratio"]["observed_value"]) <= 1.25
    assert all(row["claim_boundary"] == thresholds.CLAIM_BOUNDARY for row in rows)


def test_threshold_firewall_keeps_authorization_false() -> None:
    firewall = thresholds.no_proof_firewall_rows()[0]

    assert firewall["firewall_status"] == (
        "PASS_PACKAGE_C_PROOF_THRESHOLD_TABLE_NO_PROOF_REGISTRATION"
    )
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
        }:
            assert value == "false", key


def test_threshold_written_outputs_manifest_is_tmp_isolated(tmp_path) -> None:
    outputs = thresholds.write_outputs(
        _payload(),
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    manifest_rows = read_csv_rows(outputs["manifest"])
    artifacts = {row["artifact"] for row in manifest_rows}
    by_artifact = {row["artifact"]: row for row in manifest_rows}

    assert "NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_TABLE_20260701.csv" in artifacts
    assert "NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_STATUS_20260701.json" in artifacts
    assert "508_NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_TABLE_20260701.md" in artifacts
    report_payload = json.loads(outputs["report"].read_text(encoding="utf-8"))
    assert (
        "NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_MANIFEST_20260701.csv"
        in report_payload["outputs"]
    )
    assert by_artifact["NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_MANIFEST_20260701.csv"][
        "sha256"
    ] == thresholds.SELF_MANIFEST_SHA256


def test_threshold_main_does_not_write_ready_outputs_on_validation_failure(
    monkeypatch,
    capsys,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        thresholds,
        "build_payload",
        lambda: {"summary": {}, "no_proof_firewall": [{}]},
    )
    monkeypatch.setattr(thresholds, "validate_payload", lambda payload: ["synthetic failure"])

    def _write_outputs_should_not_run(*args, **kwargs):
        calls.append("write_outputs")
        raise AssertionError("write_outputs should not run after validation failure")

    monkeypatch.setattr(thresholds, "write_outputs", _write_outputs_should_not_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_nodi_comsol_package_c_proof_threshold_table.py",
            "--confirm-package-c-proof-threshold-table",
        ],
    )

    assert thresholds.main() == 1
    captured = capsys.readouterr()
    assert "BLOCKED_PACKAGE_C_PROOF_THRESHOLD_TABLE" in captured.out
    assert "FAIL: synthetic failure" in captured.out
    assert calls == []


def test_threshold_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_package_c_proof_threshold_table.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-package-c-proof-threshold-table is required" in result.stderr
