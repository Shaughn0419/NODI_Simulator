from __future__ import annotations

from functools import lru_cache
import json
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import (
    build_nodi_comsol_package_c_one_wall_wall_pileup_refinement as refinement,
)


@lru_cache(maxsize=1)
def _payload() -> dict:
    return refinement.build_payload()


def test_one_wall_wall_pileup_payload_closes_numeric_threshold_gaps_without_promotion() -> None:
    payload = _payload()
    failures = refinement.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == refinement.DISPOSITION
    assert summary["one_wall_rows"] == 6
    assert summary["wall_pileup_rows"] >= 10
    assert summary["max_one_wall_positive_control_ks"] <= (
        refinement.ONE_WALL_PROOF_KS_HARD_LINE
    )
    assert summary["max_wall_pileup_ratio"] <= (
        refinement.WALL_PILEUP_PROOF_RATIO_HARD_LINE
    )
    assert summary["max_wall_pileup_ratio_ci95_high"] <= (
        refinement.WALL_PILEUP_PROOF_RATIO_HARD_LINE
    )
    assert summary["one_wall_wall_pileup_status"] == (
        "candidate_numeric_thresholds_met_not_proof_registered"
    )
    assert summary["proof_registration_authorized"] is False
    assert summary["package_c_validation_status_pass_authorized"] is False
    assert summary["runtime_allowed"] is False
    assert summary["numeric_prs_eas_allowed"] is False
    assert summary["comsol_launch_allowed"] is False
    assert summary["mph_load_allowed"] is False


def test_one_wall_rows_meet_ks_proof_line() -> None:
    rows = _payload()["one_wall_rows"]
    assert {row["method"] for row in rows} == {
        "folded_normal_mirror_positive_control"
    }

    for row in rows:
        assert float(row["ks_distance_to_reflecting_kernel"]) <= (
            refinement.ONE_WALL_PROOF_KS_HARD_LINE
        )
        assert float(row["exact_boundary_atom_fraction"]) == 0.0
        assert row["candidate_status"] == (
            "candidate_and_proof_threshold_met_not_registered"
        )
        assert row["claim_boundary"] == refinement.CLAIM_BOUNDARY


def test_wall_pileup_rows_meet_ratio_and_ci_lines() -> None:
    rows = _payload()["wall_pileup_rows"]
    assert len(rows) >= 10

    for row in rows:
        assert float(row["first_vs_adjacent_gap_band_smoothed_ratio"]) <= (
            refinement.WALL_PILEUP_PROOF_RATIO_HARD_LINE
        )
        assert float(row["ratio_ci95_high"]) <= refinement.WALL_PILEUP_PROOF_RATIO_HARD_LINE
        assert row["candidate_status"] == (
            "candidate_and_proof_threshold_met_not_registered"
        )
        assert row["claim_boundary"] == refinement.CLAIM_BOUNDARY


def test_one_wall_wall_pileup_firewall_keeps_authorization_false() -> None:
    firewall = refinement.no_proof_firewall_rows()[0]

    assert firewall["firewall_status"] == (
        "PASS_PACKAGE_C_ONE_WALL_WALL_PILEUP_NO_PROOF_REGISTRATION"
    )
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
        }:
            assert value == "false", key


def test_one_wall_wall_pileup_written_outputs_manifest_is_tmp_isolated(tmp_path) -> None:
    outputs = refinement.write_outputs(
        _payload(),
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    manifest_rows = read_csv_rows(outputs["manifest"])
    artifacts = {row["artifact"] for row in manifest_rows}
    by_artifact = {row["artifact"]: row for row in manifest_rows}

    assert "NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_ONE_WALL_20260701.csv" in artifacts
    assert (
        "NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_WALL_PILEUP_20260701.csv"
        in artifacts
    )
    assert "NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_STATUS_20260701.json" in artifacts
    assert "512_NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_REFINEMENT_20260701.md" in artifacts
    report_payload = json.loads(outputs["report"].read_text(encoding="utf-8"))
    assert (
        "NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_MANIFEST_20260701.csv"
        in report_payload["outputs"]
    )
    assert by_artifact["NODI_COMSOL_PACKAGE_C_ONE_WALL_WALL_PILEUP_MANIFEST_20260701.csv"][
        "sha256"
    ] == refinement.SELF_MANIFEST_SHA256


def test_one_wall_wall_pileup_main_does_not_write_ready_outputs_on_validation_failure(
    monkeypatch,
    capsys,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        refinement,
        "build_payload",
        lambda: {"summary": {}, "no_proof_firewall": [{}]},
    )
    monkeypatch.setattr(refinement, "validate_payload", lambda payload: ["synthetic failure"])

    def _write_outputs_should_not_run(*args, **kwargs):
        calls.append("write_outputs")
        raise AssertionError("write_outputs should not run after validation failure")

    monkeypatch.setattr(refinement, "write_outputs", _write_outputs_should_not_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_nodi_comsol_package_c_one_wall_wall_pileup_refinement.py",
            "--confirm-package-c-one-wall-wall-pileup-refinement",
        ],
    )

    assert refinement.main() == 1
    captured = capsys.readouterr()
    assert "BLOCKED_PACKAGE_C_ONE_WALL_WALL_PILEUP_REFINEMENT" in captured.out
    assert "FAIL: synthetic failure" in captured.out
    assert calls == []


def test_one_wall_wall_pileup_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_package_c_one_wall_wall_pileup_refinement.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-package-c-one-wall-wall-pileup-refinement is required" in result.stderr
