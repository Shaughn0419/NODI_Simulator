from __future__ import annotations

from functools import lru_cache
import json
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_package_c_metric_hardening_consolidation as consolidation


@lru_cache(maxsize=1)
def _payload() -> dict:
    return consolidation.build_payload()


def test_consolidation_payload_absorbs_gate37_and_gate38_without_promotion() -> None:
    payload = _payload()
    failures = consolidation.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == consolidation.DISPOSITION
    assert summary["gate37_disposition"] == consolidation.EXPECTED_GATE37_DISPOSITION
    assert summary["gate38_disposition"] == consolidation.EXPECTED_GATE38_DISPOSITION
    assert summary["evidence_index_rows"] == 10
    assert summary["readiness_criteria_rows"] == 9
    assert summary["boundary_atom_split_rows"] >= 100
    assert summary["raw_histogram_rows"] >= 300
    assert summary["ess_proxy_rows"] >= 100
    assert summary["one_wall_suite_rows"] == 18
    assert summary["wall_pileup_refinement_rows"] == 12
    assert summary["max_exact_boundary_atom_fraction"] == 0.0
    assert summary["projection_negative_control_status"] == "expected_fail_observed"
    assert summary["algorithmic_pileup_signal_rows"] == 0
    assert summary["proof_readiness_status"] == (
        "not_ready_missing_timeseries_ess_clean_commit_and_authorization"
    )
    assert summary["proof_registration_authorized"] is False
    assert summary["package_c_validation_status_pass_authorized"] is False
    assert summary["runtime_allowed"] is False
    assert summary["numeric_prs_eas_allowed"] is False
    assert summary["comsol_launch_allowed"] is False
    assert summary["mph_load_allowed"] is False


def test_consolidation_evidence_index_is_single_review_entrypoint() -> None:
    rows = _payload()["evidence_index"]
    by_id = {row["evidence_id"]: row for row in rows}

    assert set(by_id) == {
        "exact_boundary_atom_split",
        "near_boundary_band_split",
        "raw_histograms",
        "ess_proxy",
        "one_wall_folded_normal_positive_control",
        "projection_clamp_negative_control",
        "rejection_resampling_negative_control",
        "worst_case_dt_refinement",
        "corner_heatmap",
        "wall_pileup_refinement",
    }
    assert by_id["exact_boundary_atom_split"]["status"] == "candidate_satisfied_not_proof"
    assert by_id["ess_proxy"]["status"] == "candidate_caveat_not_proof_ready"
    assert by_id["projection_clamp_negative_control"]["status"] == "expected_fail_observed"
    assert by_id["wall_pileup_refinement"]["primary_metric"] == "algorithmic_pileup_signal_rows"
    assert by_id["wall_pileup_refinement"]["primary_value"] == "0"
    assert all(row["claim_boundary"] == consolidation.CLAIM_BOUNDARY for row in rows)
    assert all("Package C proof/pass registration" in row["blocked_use"] for row in rows)


def test_consolidation_readiness_criteria_keep_proof_gaps_explicit() -> None:
    rows = _payload()["readiness_criteria"]
    by_id = {row["criterion_id"]: row for row in rows}

    assert by_id["exact_boundary_atoms_zero"]["candidate_status"] == "satisfied"
    assert by_id["wall_pileup_sparse_proxy_resolved"]["candidate_status"] == "satisfied"
    assert by_id["timeseries_ess"]["proof_status"] == "missing"
    assert by_id["timeseries_ess"]["candidate_status"] == "not_satisfied_for_proof"
    assert by_id["reviewed_clean_commit_binding"]["proof_status"] == "missing"
    assert by_id["manual_authorization_ledger"]["current_value"] == (
        "proof_registration_authorized=false"
    )


def test_consolidation_firewall_keeps_authorization_false() -> None:
    firewall = consolidation.no_proof_firewall_rows()[0]

    assert firewall["firewall_status"] == (
        "PASS_PACKAGE_C_METRIC_HARDENING_CONSOLIDATION_NO_PROOF_REGISTRATION"
    )
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
        }:
            assert value == "false", key


def test_consolidation_written_outputs_manifest_is_tmp_isolated(tmp_path) -> None:
    outputs = consolidation.write_outputs(
        _payload(),
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    manifest_rows = read_csv_rows(outputs["manifest"])
    artifacts = {row["artifact"] for row in manifest_rows}
    by_artifact = {row["artifact"]: row for row in manifest_rows}

    assert (
        "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_EVIDENCE_INDEX_20260701.csv"
        in artifacts
    )
    assert (
        "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_READINESS_CRITERIA_20260701.csv"
        in artifacts
    )
    assert (
        "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_STATUS_20260701.json"
        in artifacts
    )
    assert (
        "504_NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATION_20260701.md"
        in artifacts
    )
    report_payload = json.loads(outputs["report"].read_text(encoding="utf-8"))
    assert (
        "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_STATUS_20260701.json"
        in report_payload["outputs"]
    )
    assert (
        "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_MANIFEST_20260701.csv"
        in report_payload["outputs"]
    )
    assert (
        "504_NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATION_20260701.md"
        in report_payload["outputs"]
    )
    assert by_artifact[
        "NODI_COMSOL_PACKAGE_C_METRIC_HARDENING_CONSOLIDATED_MANIFEST_20260701.csv"
    ]["sha256"] == consolidation.SELF_MANIFEST_SHA256


def test_consolidation_main_does_not_write_ready_outputs_on_validation_failure(
    monkeypatch,
    capsys,
) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        consolidation,
        "build_payload",
        lambda: {"summary": {}, "no_proof_firewall": [{}]},
    )
    monkeypatch.setattr(
        consolidation,
        "validate_payload",
        lambda payload: ["synthetic failure"],
    )

    def _write_outputs_should_not_run(*args, **kwargs):
        calls.append("write_outputs")
        raise AssertionError("write_outputs should not run after validation failure")

    monkeypatch.setattr(consolidation, "write_outputs", _write_outputs_should_not_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_nodi_comsol_package_c_metric_hardening_consolidation.py",
            "--confirm-package-c-metric-hardening-consolidation",
        ],
    )

    assert consolidation.main() == 1
    captured = capsys.readouterr()
    assert "BLOCKED_PACKAGE_C_METRIC_HARDENING_CONSOLIDATION" in captured.out
    assert "FAIL: synthetic failure" in captured.out
    assert calls == []


def test_consolidation_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_package_c_metric_hardening_consolidation.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-package-c-metric-hardening-consolidation is required" in result.stderr
