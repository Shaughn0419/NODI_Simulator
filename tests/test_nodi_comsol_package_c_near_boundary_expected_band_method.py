from __future__ import annotations

from functools import lru_cache
import json
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_package_c_near_boundary_expected_band_method as method


@lru_cache(maxsize=1)
def _payload() -> dict:
    return method.build_payload()


def test_near_boundary_expected_band_payload_binds_method_without_promotion() -> None:
    payload = _payload()
    failures = method.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == method.DISPOSITION
    assert summary["expected_band_rows"] == 24
    assert summary["legacy_sparse_context_rows"] == 1
    assert summary["max_abs_z_to_expected"] <= method.Z_HARD_LINE
    assert summary["near_boundary_expected_band_method_status"] == (
        "candidate_method_bound_not_proof_registered"
    )
    assert summary["proof_registration_authorized"] is False
    assert summary["package_c_validation_status_pass_authorized"] is False
    assert summary["runtime_allowed"] is False
    assert summary["numeric_prs_eas_allowed"] is False
    assert summary["comsol_launch_allowed"] is False
    assert summary["mph_load_allowed"] is False


def test_expected_band_rows_have_area_formula_and_confidence_fields() -> None:
    rows = _payload()["expected_band_rows"]
    assert len(rows) == 24
    assert {row["band_low_nm"] for row in rows} == {"0.0", "1.0"}
    assert {row["band_high_nm"] for row in rows} == {"1.0", "2.0"}
    for row in rows:
        assert row["method_formula"] == (
            "expected_fraction=(area(radius+a)-area(radius+b))/area(radius)"
        )
        assert float(row["expected_area_band_fraction"]) > 0.0
        assert float(row["observed_ci95_low"]) <= float(row["observed_band_fraction"])
        assert float(row["observed_ci95_high"]) >= float(row["observed_band_fraction"])
        assert float(row["abs_z_to_expected"]) <= method.Z_HARD_LINE
        assert row["candidate_status"] == (
            "candidate_expected_band_method_bound_not_proof_registered"
        )
        assert row["claim_boundary"] == method.CLAIM_BOUNDARY


def test_legacy_sparse_context_is_not_used_as_failure_or_proof() -> None:
    legacy = _payload()["legacy_sparse_context_rows"][0]

    assert legacy["legacy_source"] == "GATE37_BOUNDARY_ATOM_SPLIT_20260630"
    assert legacy["interpretation"] == (
        "underpowered_sparse_context_superseded_by_65536_sample_expected_band_method"
    )
    assert float(legacy["expected_count"]) < 1.0
    assert legacy["claim_boundary"] == method.CLAIM_BOUNDARY


def test_near_boundary_expected_band_firewall_keeps_authorization_false() -> None:
    firewall = method.no_proof_firewall_rows()[0]

    assert firewall["firewall_status"] == (
        "PASS_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_METHOD_NO_PROOF_REGISTRATION"
    )
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
        }:
            assert value == "false", key


def test_near_boundary_expected_band_written_outputs_manifest_is_tmp_isolated(tmp_path) -> None:
    outputs = method.write_outputs(
        _payload(),
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    manifest_rows = read_csv_rows(outputs["manifest"])
    artifacts = {row["artifact"] for row in manifest_rows}
    by_artifact = {row["artifact"]: row for row in manifest_rows}

    assert "NODI_COMSOL_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_ROWS_20260701.csv" in artifacts
    assert (
        "NODI_COMSOL_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_LEGACY_CONTEXT_20260701.csv"
        in artifacts
    )
    assert (
        "NODI_COMSOL_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_STATUS_20260701.json"
        in artifacts
    )
    assert "513_NODI_COMSOL_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_METHOD_20260701.md" in artifacts
    report_payload = json.loads(outputs["report"].read_text(encoding="utf-8"))
    assert (
        "NODI_COMSOL_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_MANIFEST_20260701.csv"
        in report_payload["outputs"]
    )
    assert by_artifact[
        "NODI_COMSOL_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_MANIFEST_20260701.csv"
    ]["sha256"] == method.SELF_MANIFEST_SHA256


def test_near_boundary_expected_band_main_does_not_write_outputs_on_validation_failure(
    monkeypatch,
    capsys,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        method,
        "build_payload",
        lambda: {"summary": {}, "no_proof_firewall": [{}]},
    )
    monkeypatch.setattr(method, "validate_payload", lambda payload: ["synthetic failure"])

    def _write_outputs_should_not_run(*args, **kwargs):
        calls.append("write_outputs")
        raise AssertionError("write_outputs should not run after validation failure")

    monkeypatch.setattr(method, "write_outputs", _write_outputs_should_not_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_nodi_comsol_package_c_near_boundary_expected_band_method.py",
            "--confirm-package-c-near-boundary-expected-band-method",
        ],
    )

    assert method.main() == 1
    captured = capsys.readouterr()
    assert "BLOCKED_PACKAGE_C_NEAR_BOUNDARY_EXPECTED_BAND_METHOD" in captured.out
    assert "FAIL: synthetic failure" in captured.out
    assert calls == []


def test_near_boundary_expected_band_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_package_c_near_boundary_expected_band_method.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-package-c-near-boundary-expected-band-method is required" in result.stderr
