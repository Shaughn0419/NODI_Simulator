from __future__ import annotations

from functools import lru_cache
import json
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_package_c_timeseries_ess_candidate as timeseries


@lru_cache(maxsize=1)
def _payload() -> dict:
    return timeseries.build_payload()


def test_timeseries_payload_reduces_ess_gap_without_proof_promotion() -> None:
    payload = _payload()
    failures = timeseries.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == timeseries.DISPOSITION
    assert summary["consolidation_disposition"] == timeseries.EXPECTED_CONSOLIDATION_DISPOSITION
    assert summary["scenario_rows"] == len(timeseries.SCENARIOS)
    assert summary["observable_ess_rows"] == len(timeseries.SCENARIOS) * 3
    assert summary["autocorrelation_rows"] == len(timeseries.SCENARIOS) * 3 * len(
        timeseries.AUTOCORR_LAGS
    )
    assert summary["substep_policy_rows"] == len(timeseries.SCENARIOS)
    assert summary["support_violation_rows"] == 0
    assert summary["nonconverged_reflection_rows"] == 0
    assert summary["max_exact_boundary_atom_fraction_all_steps"] == 0.0
    assert summary["min_effective_sample_size"] >= timeseries.MIN_ESS_CANDIDATE_FLOOR
    assert summary["timeseries_ess_candidate_status"] == "candidate_artifact_complete_not_proof"
    assert summary["proof_readiness_impact"] == (
        "timeseries_ess_gap_reduced_but_not_proof_registered"
    )
    assert summary["stationarity_review_required"] is True
    assert summary["substep_policy_review_required"] is True
    assert summary["reviewed_commit_binding_status"] == (
        "pending_future_authorization_not_clean_head_bound"
    )
    assert summary["github_visibility_status"] == "artifact_generated_from_local_worktree_pre_commit"
    assert summary["proof_registration_authorized"] is False
    assert summary["package_c_validation_status_pass_authorized"] is False
    assert summary["runtime_allowed"] is False
    assert summary["numeric_prs_eas_allowed"] is False
    assert summary["comsol_launch_allowed"] is False
    assert summary["mph_load_allowed"] is False


def test_timeseries_scenario_rows_have_stationarity_and_support_metrics() -> None:
    rows = _payload()["scenario_summary"]
    first = rows[0]

    assert {row["scenario_id"] for row in rows} == {
        scenario["scenario_id"] for scenario in timeseries.SCENARIOS
    }
    assert first["n_steps"] == str(timeseries.N_STEPS)
    assert first["burn_in_steps"] == str(timeseries.BURN_IN_STEPS)
    assert first["sample_stride"] == str(timeseries.SAMPLE_STRIDE)
    assert all(row["support_violation_count"] == "0" for row in rows)
    assert all(row["nonconverged_reflection_count"] == "0" for row in rows)
    assert all(
        float(row["u_accessible_cdf_l1_to_uniform"])
        <= timeseries.EQUILIBRIUM_L1_CANDIDATE_THRESHOLD
        for row in rows
    )
    assert all(
        float(row["x_local_norm_l1_to_uniform"])
        <= timeseries.EQUILIBRIUM_L1_CANDIDATE_THRESHOLD
        for row in rows
    )
    assert all(row["claim_boundary"] == timeseries.CLAIM_BOUNDARY for row in rows)


def test_timeseries_observable_ess_and_autocorrelation_are_reviewer_friendly() -> None:
    ess_rows = _payload()["observable_ess"]
    autocorr_rows = _payload()["autocorrelation"]

    assert {row["observable"] for row in ess_rows} == {
        "u_accessible_cdf",
        "x_local_norm",
        "surface_gap_nm",
    }
    assert min(float(row["effective_sample_size"]) for row in ess_rows) >= (
        timeseries.MIN_ESS_CANDIDATE_FLOOR
    )
    assert {row["lag"] for row in autocorr_rows} == {str(lag) for lag in timeseries.AUTOCORR_LAGS}
    assert all(row["autocorrelation_status"] == "timeseries_candidate_metric_not_proof" for row in ess_rows)
    assert all(row["claim_boundary"] == timeseries.CLAIM_BOUNDARY for row in autocorr_rows)


def test_timeseries_substep_policy_is_design_guard_only() -> None:
    rows = _payload()["substep_policy"]

    assert len(rows) == len(timeseries.SCENARIOS)
    assert {row["runtime_policy_authorized"] for row in rows} == {"false"}
    assert {row["substep_policy_scope"] for row in rows} == {
        "design_guard_only_not_runtime"
    }
    assert all("runtime configuration" in row["blocked_use"] for row in rows)


def test_timeseries_firewall_keeps_authorization_false() -> None:
    firewall = timeseries.no_proof_firewall_rows()[0]

    assert firewall["firewall_status"] == (
        "PASS_PACKAGE_C_TIMESERIES_ESS_CANDIDATE_NO_PROOF_REGISTRATION"
    )
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
        }:
            assert value == "false", key


def test_timeseries_written_outputs_manifest_is_tmp_isolated(tmp_path) -> None:
    outputs = timeseries.write_outputs(
        _payload(),
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    manifest_rows = read_csv_rows(outputs["manifest"])
    artifacts = {row["artifact"] for row in manifest_rows}
    by_artifact = {row["artifact"]: row for row in manifest_rows}

    assert "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_SCENARIO_SUMMARY_20260701.csv" in artifacts
    assert "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_OBSERVABLE_ESS_20260701.csv" in artifacts
    assert "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_AUTOCORRELATION_20260701.csv" in artifacts
    assert "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_SUBSTEP_POLICY_20260701.csv" in artifacts
    assert "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_STATUS_20260701.json" in artifacts
    assert "505_NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_CANDIDATE_20260701.md" in artifacts
    report_payload = json.loads(outputs["report"].read_text(encoding="utf-8"))
    assert "NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_MANIFEST_20260701.csv" in report_payload[
        "outputs"
    ]
    assert by_artifact["NODI_COMSOL_PACKAGE_C_TIMESERIES_ESS_MANIFEST_20260701.csv"][
        "sha256"
    ] == timeseries.SELF_MANIFEST_SHA256


def test_timeseries_main_does_not_write_ready_outputs_on_validation_failure(
    monkeypatch,
    capsys,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(timeseries, "build_payload", lambda: {"summary": {}, "no_proof_firewall": [{}]})
    monkeypatch.setattr(timeseries, "validate_payload", lambda payload: ["synthetic failure"])

    def _write_outputs_should_not_run(*args, **kwargs):
        calls.append("write_outputs")
        raise AssertionError("write_outputs should not run after validation failure")

    monkeypatch.setattr(timeseries, "write_outputs", _write_outputs_should_not_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_nodi_comsol_package_c_timeseries_ess_candidate.py",
            "--confirm-package-c-timeseries-ess-candidate",
        ],
    )

    assert timeseries.main() == 1
    captured = capsys.readouterr()
    assert "BLOCKED_PACKAGE_C_TIMESERIES_ESS_CANDIDATE" in captured.out
    assert "FAIL: synthetic failure" in captured.out
    assert calls == []


def test_timeseries_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_package_c_timeseries_ess_candidate.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-package-c-timeseries-ess-candidate is required" in result.stderr
