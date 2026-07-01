from __future__ import annotations

from functools import lru_cache
import hashlib
import json
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_package_c_user_authorization_ledger as ledger


@lru_cache(maxsize=1)
def _payload() -> dict:
    return ledger.build_payload()


def test_user_authorization_ledger_accepts_all_four_paths_without_result_promotion() -> None:
    payload = _payload()
    failures = ledger.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == ledger.DISPOSITION
    assert len(summary["authorization_text_sha256"]) == 64
    assert summary["authorization_text_sha256"] == hashlib.sha256(
        ledger.USER_AUTHORIZATION_TEXT.encode("utf-8")
    ).hexdigest()
    assert summary["authorization_text_sha256"] != hashlib.sha256(
        b"test"
    ).hexdigest()
    assert summary["authorization_scope_rows"] == 4
    assert summary["authorized_scope_rows"] == 4
    assert summary["package_c_proof_registration_path_authorized"] is True
    assert summary["runtime_substep_policy_authorized"] is True
    assert summary["solver_branch_authorized"] is True
    assert summary["wet_branch_authorized"] is True
    assert summary["package_c_proof_artifact_registered"] is False
    assert summary["package_c_validation_status_pass_current"] is False
    assert summary["runtime_execution_started"] is False
    assert summary["sidewall_prs_eas_numeric_output_current"] is False
    assert summary["comsol_launch_started"] is False
    assert summary["mph_load_started"] is False


def test_user_authorization_scopes_are_explicit_and_source_bound() -> None:
    rows = _payload()["authorization_scopes"]
    by_scope = {row["scope_id"]: row for row in rows}

    assert set(by_scope) == {
        "package_c_proof_registration_path",
        "runtime_substep_policy_path",
        "solver_branch_path",
        "wet_branch_path",
    }
    assert {row["authorization_status"] for row in rows} == {"authorized"}
    assert all(
        row["authorization_source"] == "user_explicit_message_current_thread_20260701"
        for row in rows
    )
    assert all(row["claim_boundary"] == ledger.CLAIM_BOUNDARY for row in rows)


def test_user_authorization_result_guards_remain_false() -> None:
    guards = _payload()["result_promotion_guards"]
    by_field = {row["guard_field"]: row for row in guards}

    assert by_field["package_c_proof_artifact_registered"]["guard_value"] == "false"
    assert by_field["runtime_execution_started"]["guard_value"] == "false"
    assert by_field["comsol_launch_started"]["guard_value"] == "false"
    assert by_field["wet_claim_current"]["guard_value"] == "false"
    assert by_field["route_yield_detection_claim_current"]["guard_value"] == "false"
    assert {row["guard_value"] for row in guards} == {"false"}


def test_user_authorization_written_outputs_manifest_is_tmp_isolated(tmp_path) -> None:
    outputs = ledger.write_outputs(
        _payload(),
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    manifest_rows = read_csv_rows(outputs["manifest"])
    artifacts = {row["artifact"] for row in manifest_rows}
    by_artifact = {row["artifact"]: row for row in manifest_rows}

    assert "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_SCOPES_20260701.csv" in artifacts
    assert (
        "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_RESULT_GUARDS_20260701.csv"
        in artifacts
    )
    assert "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_STATUS_20260701.json" in artifacts
    assert "516_NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_20260701.md" in artifacts
    report_payload = json.loads(outputs["report"].read_text(encoding="utf-8"))
    assert (
        "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_MANIFEST_20260701.csv"
        in report_payload["outputs"]
    )
    assert by_artifact[
        "NODI_COMSOL_PACKAGE_C_USER_AUTHORIZATION_LEDGER_MANIFEST_20260701.csv"
    ]["sha256"] == ledger.SELF_MANIFEST_SHA256


def test_user_authorization_main_does_not_write_ready_outputs_on_validation_failure(
    monkeypatch,
    capsys,
) -> None:
    calls: list[str] = []
    monkeypatch.setattr(
        ledger,
        "build_payload",
        lambda: {"summary": {}, "result_promotion_guards": []},
    )
    monkeypatch.setattr(ledger, "validate_payload", lambda payload: ["synthetic failure"])

    def _write_outputs_should_not_run(*args, **kwargs):
        calls.append("write_outputs")
        raise AssertionError("write_outputs should not run after validation failure")

    monkeypatch.setattr(ledger, "write_outputs", _write_outputs_should_not_run)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_nodi_comsol_package_c_user_authorization_ledger.py",
            "--confirm-package-c-user-authorization-ledger",
        ],
    )

    assert ledger.main() == 1
    captured = capsys.readouterr()
    assert "BLOCKED_PACKAGE_C_USER_AUTHORIZATION_LEDGER" in captured.out
    assert "FAIL: synthetic failure" in captured.out
    assert calls == []


def test_user_authorization_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_package_c_user_authorization_ledger.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-package-c-user-authorization-ledger is required" in result.stderr
