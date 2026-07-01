from __future__ import annotations

from functools import lru_cache
import json
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_package_c_authorization_preflight as preflight


@lru_cache(maxsize=1)
def _payload() -> dict:
    return preflight.build_payload()


def test_authorization_preflight_identifies_candidate_commit_without_authorizing() -> None:
    payload = _payload()
    failures = preflight.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == preflight.DISPOSITION
    assert summary["target_reviewed_commit_sha"]
    assert summary["origin_main_sha"]
    assert summary["head_matches_origin_main"] is True
    assert summary["authorization_preflight_status"] == (
        "candidate_commit_identified_authorization_missing_no_proof_registration"
    )
    assert summary["manual_authorization_ledger_status"] == "missing_fail_closed"
    assert summary["proof_registration_authorized"] is False
    assert summary["package_c_validation_status_pass_authorized"] is False
    assert summary["runtime_allowed"] is False
    assert summary["numeric_prs_eas_allowed"] is False
    assert summary["comsol_launch_allowed"] is False
    assert summary["mph_load_allowed"] is False


def test_authorization_preflight_ledger_placeholder_is_fail_closed() -> None:
    rows = _payload()["authorization_ledger_placeholder"]
    by_field = {row["ledger_field"]: row for row in rows}

    assert by_field["manual_authorization_ledger_id"]["ledger_value"] == ""
    assert by_field["manual_authorization_ledger_sha256"]["ledger_value"] == ""
    assert by_field["proof_registration_authorized"]["ledger_value"] == "false"
    assert by_field["runtime_allowed"]["ledger_value"] == "false"
    assert all(row["claim_boundary"] == preflight.CLAIM_BOUNDARY for row in rows)


def test_authorization_preflight_hard_fail_checklist_blocks_claim_promotion() -> None:
    rows = _payload()["hard_fail_checklist"]
    rules = {row["hard_fail_rule"] for row in rows}

    assert "manual_authorization_ledger_missing" in rules
    assert "proof_registration_authorized_true_without_ledger" in rules
    assert "runtime_allowed_true_without_runtime_ledger" in rules
    assert "route_yield_detection_wet_claim_from_package_c_preflight" in rules
    assert all(row["allowed_use"] == preflight.ALLOWED_USE for row in rows)
    assert all(row["blocked_use"] == preflight.BLOCKED_USE for row in rows)


def test_authorization_preflight_firewall_keeps_authorization_false() -> None:
    firewall = preflight.no_proof_firewall_rows()[0]

    assert firewall["firewall_status"] == (
        "PASS_PACKAGE_C_AUTHORIZATION_PREFLIGHT_NO_AUTHORIZATION"
    )
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
        }:
            assert value == "false", key


def test_authorization_preflight_written_outputs_manifest_is_tmp_isolated(tmp_path) -> None:
    outputs = preflight.write_outputs(
        _payload(),
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    manifest_rows = read_csv_rows(outputs["manifest"])
    artifacts = {row["artifact"] for row in manifest_rows}
    by_artifact = {row["artifact"]: row for row in manifest_rows}

    assert (
        "NODI_COMSOL_PACKAGE_C_AUTHORIZATION_PREFLIGHT_CLEAN_COMMIT_BINDING_20260701.csv"
        in artifacts
    )
    assert (
        "NODI_COMSOL_PACKAGE_C_AUTHORIZATION_PREFLIGHT_LEDGER_PLACEHOLDER_20260701.csv"
        in artifacts
    )
    assert (
        "NODI_COMSOL_PACKAGE_C_AUTHORIZATION_PREFLIGHT_HARD_FAIL_CHECKLIST_20260701.csv"
        in artifacts
    )
    assert "NODI_COMSOL_PACKAGE_C_AUTHORIZATION_PREFLIGHT_STATUS_20260701.json" in artifacts
    assert "515_NODI_COMSOL_PACKAGE_C_AUTHORIZATION_PREFLIGHT_20260701.md" in artifacts
    report_payload = json.loads(outputs["report"].read_text(encoding="utf-8"))
    assert (
        "NODI_COMSOL_PACKAGE_C_AUTHORIZATION_PREFLIGHT_MANIFEST_20260701.csv"
        in report_payload["outputs"]
    )
    assert by_artifact[
        "NODI_COMSOL_PACKAGE_C_AUTHORIZATION_PREFLIGHT_MANIFEST_20260701.csv"
    ]["sha256"] == preflight.SELF_MANIFEST_SHA256


def test_authorization_preflight_main_does_not_write_ready_outputs_on_validation_failure(
    monkeypatch,
    capsys,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        preflight,
        "build_payload",
        lambda: {"summary": {}, "no_proof_firewall": [{}]},
    )
    monkeypatch.setattr(preflight, "validate_payload", lambda payload: ["synthetic failure"])

    def _write_outputs_should_not_run(*args, **kwargs):
        calls.append("write_outputs")
        raise AssertionError("write_outputs should not run after validation failure")

    monkeypatch.setattr(preflight, "write_outputs", _write_outputs_should_not_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_nodi_comsol_package_c_authorization_preflight.py",
            "--confirm-package-c-authorization-preflight",
        ],
    )

    assert preflight.main() == 1
    captured = capsys.readouterr()
    assert "BLOCKED_PACKAGE_C_AUTHORIZATION_PREFLIGHT" in captured.out
    assert "FAIL: synthetic failure" in captured.out
    assert calls == []


def test_authorization_preflight_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_package_c_authorization_preflight.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-package-c-authorization-preflight is required" in result.stderr
