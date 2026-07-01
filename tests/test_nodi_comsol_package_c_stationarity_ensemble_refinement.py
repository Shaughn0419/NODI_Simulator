from __future__ import annotations

from functools import lru_cache
import json
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import (
    build_nodi_comsol_package_c_stationarity_ensemble_refinement as stationarity,
)


@lru_cache(maxsize=1)
def _payload() -> dict:
    return stationarity.build_payload()


def test_stationarity_ensemble_payload_reduces_uniformity_gap_without_promotion() -> None:
    payload = _payload()
    failures = stationarity.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == stationarity.DISPOSITION
    assert summary["scenario_seed_rows"] == 18
    assert summary["histogram_rows"] == 720
    assert summary["confidence_interval_rows"] == 12
    assert summary["min_independent_ensemble_ess"] >= 32768
    assert summary["max_final_u_accessible_cdf_l1_to_uniform"] <= (
        stationarity.PROOF_L1_HARD_LINE
    )
    assert summary["max_final_x_local_norm_l1_to_uniform"] <= (
        stationarity.PROOF_L1_HARD_LINE
    )
    assert summary["support_violation_count"] == 0
    assert summary["exact_boundary_atom_count"] == 0
    assert summary["nonconverged_reflection_count"] == 0
    assert summary["stationarity_ensemble_status"] == (
        "candidate_numeric_stationarity_lines_met_not_proof_registered"
    )
    assert summary["proof_registration_authorized"] is False
    assert summary["package_c_validation_status_pass_authorized"] is False
    assert summary["runtime_allowed"] is False
    assert summary["numeric_prs_eas_allowed"] is False
    assert summary["comsol_launch_allowed"] is False
    assert summary["mph_load_allowed"] is False


def test_stationarity_scenario_rows_have_transition_invariance_fields() -> None:
    rows = _payload()["scenario_seed_rows"]
    assert len(rows) == 18

    for row in rows:
        assert row["ess_method"] == "independent_uniform_initial_ensemble_no_autocorrelation"
        assert row["transition_invariance_status"] == (
            "candidate_transition_invariance_not_proof"
        )
        assert int(row["support_violation_count"]) == 0
        assert int(row["nonconverged_reflection_count"]) == 0
        assert float(row["final_u_accessible_cdf_l1_to_uniform"]) <= (
            stationarity.PROOF_L1_HARD_LINE
        )
        assert float(row["final_x_local_norm_l1_to_uniform"]) <= (
            stationarity.PROOF_L1_HARD_LINE
        )
        assert row["claim_boundary"] == stationarity.CLAIM_BOUNDARY


def test_stationarity_histograms_cover_initial_and_final_bases() -> None:
    rows = _payload()["histogram_rows"]
    stages = {row["stage"] for row in rows}
    bases = {row["basis"] for row in rows}

    assert stages == {"initial", "final_after_one_reflected_step"}
    assert bases == {"u_accessible_cdf", "x_local_norm"}
    assert all(row["claim_boundary"] == stationarity.CLAIM_BOUNDARY for row in rows)


def test_stationarity_confidence_intervals_are_not_proof_claims() -> None:
    rows = _payload()["confidence_interval_rows"]

    assert rows
    assert all(
        row["ci_status"]
        == "candidate_ci_upper_within_current_proof_line_not_registered"
        for row in rows
    )
    assert all(row["claim_boundary"] == stationarity.CLAIM_BOUNDARY for row in rows)


def test_stationarity_firewall_keeps_authorization_false() -> None:
    firewall = stationarity.no_proof_firewall_rows()[0]

    assert firewall["firewall_status"] == (
        "PASS_PACKAGE_C_STATIONARITY_ENSEMBLE_NO_PROOF_REGISTRATION"
    )
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
        }:
            assert value == "false", key


def test_stationarity_written_outputs_manifest_is_tmp_isolated(tmp_path) -> None:
    outputs = stationarity.write_outputs(
        _payload(),
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    manifest_rows = read_csv_rows(outputs["manifest"])
    artifacts = {row["artifact"] for row in manifest_rows}
    by_artifact = {row["artifact"]: row for row in manifest_rows}

    assert "NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_SCENARIO_METRICS_20260701.csv" in artifacts
    assert "NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_HISTOGRAMS_20260701.csv" in artifacts
    assert (
        "NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_CONFIDENCE_INTERVALS_20260701.csv"
        in artifacts
    )
    assert "NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_STATUS_20260701.json" in artifacts
    assert "511_NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_REFINEMENT_20260701.md" in artifacts
    report_payload = json.loads(outputs["report"].read_text(encoding="utf-8"))
    assert (
        "NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_MANIFEST_20260701.csv"
        in report_payload["outputs"]
    )
    assert by_artifact["NODI_COMSOL_PACKAGE_C_STATIONARITY_ENSEMBLE_MANIFEST_20260701.csv"][
        "sha256"
    ] == stationarity.SELF_MANIFEST_SHA256


def test_stationarity_main_does_not_write_ready_outputs_on_validation_failure(
    monkeypatch,
    capsys,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        stationarity,
        "build_payload",
        lambda: {"summary": {}, "no_proof_firewall": [{}]},
    )
    monkeypatch.setattr(
        stationarity,
        "validate_payload",
        lambda payload: ["synthetic failure"],
    )

    def _write_outputs_should_not_run(*args, **kwargs):
        calls.append("write_outputs")
        raise AssertionError("write_outputs should not run after validation failure")

    monkeypatch.setattr(stationarity, "write_outputs", _write_outputs_should_not_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_nodi_comsol_package_c_stationarity_ensemble_refinement.py",
            "--confirm-package-c-stationarity-ensemble-refinement",
        ],
    )

    assert stationarity.main() == 1
    captured = capsys.readouterr()
    assert "BLOCKED_PACKAGE_C_STATIONARITY_ENSEMBLE_REFINEMENT" in captured.out
    assert "FAIL: synthetic failure" in captured.out
    assert calls == []


def test_stationarity_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_package_c_stationarity_ensemble_refinement.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-package-c-stationarity-ensemble-refinement is required" in result.stderr
