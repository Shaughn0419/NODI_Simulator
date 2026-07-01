from __future__ import annotations

from functools import lru_cache
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import (
    build_nodi_comsol_package_c_proof_registration_artifact as registration,
)


@lru_cache(maxsize=1)
def _payload() -> dict:
    return registration.build_payload()


def test_proof_registration_registers_only_finite_step_surrogate_scope() -> None:
    payload = _payload()
    failures = registration.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == registration.DISPOSITION
    assert summary["proof_registration_authorized"] is True
    assert summary["package_c_proof_artifact_registered"] is True
    assert summary["package_c_validation_status_pass_current"] is True
    assert (
        summary["package_c_validation_status_pass_scope"]
        == "finite_step_reflection_surrogate_evidence_only"
    )
    assert summary["validated_brownian_solver_output_current"] is False
    assert summary["runtime_allowed"] is False
    assert summary["numeric_prs_eas_allowed"] is False
    assert summary["comsol_launch_allowed"] is False
    assert summary["mph_load_allowed"] is False


def test_proof_registration_binds_authorization_and_threshold_evidence() -> None:
    summary = _payload()["summary"]

    assert summary["authorization_scope_rows"] == 4
    assert summary["readiness_path_authorization_accepted"] is True
    assert summary["proof_threshold_rows"] >= 16
    assert summary["proof_gap_rows"] == 0
    assert summary["proof_method_gap_rows"] == 0
    assert summary["source_missing_rows"] == 0
    assert len(summary["reviewed_evidence_commit_sha"]) == 40


def test_proof_registration_keeps_runtime_solver_wet_guards_false() -> None:
    payload = _payload()
    guard_rows = payload["post_registration_guards"]
    by_guard = {row["guard_field"]: row for row in guard_rows}

    expected_false = {
        "runtime_allowed",
        "runtime_execution_started",
        "nodi_runtime_recomputation_started",
        "sidewall_prs_eas_numeric_output_current",
        "comsol_launch_started",
        "mph_load_started",
        "validated_brownian_solver_output_current",
        "validated_hindered_diffusion_claim_current",
        "trapezoid_flow_solver_output_current",
        "electrokinetic_solver_output_current",
        "optical_solver_output_current",
        "wet_claim_current",
        "route_yield_detection_claim_current",
        "fabrication_or_production_release_current",
    }
    assert set(by_guard) == expected_false
    assert {row["guard_value"] for row in guard_rows} == {"false"}
    assert all("hard_fail_if" in row and row["hard_fail_if"] for row in guard_rows)


def test_runtime_gaps_remain_blockers_after_proof_registration() -> None:
    payload = _payload()
    summary = payload["summary"]
    blocker_rows = payload["runtime_blockers"]
    by_blocker = {row["blocker_id"]: row for row in blocker_rows}

    assert summary["runtime_policy_gap_rows"] > 0
    assert by_blocker["runtime_policy_gap_rows"]["current_value"] == str(
        summary["runtime_policy_gap_rows"]
    )
    assert by_blocker["runtime_allowed"]["current_value"] == "false"
    assert by_blocker["solver_wet_claims"]["current_value"] == "false"


def test_proof_registration_written_outputs_manifest_is_tmp_isolated(tmp_path) -> None:
    payload = _payload()
    paths = registration.write_outputs(payload, output_dir=tmp_path, report_dir=tmp_path)
    artifacts = {path.name for path in paths}

    assert "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_DECISIONS_20260701.csv" in artifacts
    assert "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_POST_GUARDS_20260701.csv" in artifacts
    assert "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_RUNTIME_BLOCKERS_20260701.csv" in artifacts
    assert "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_SOURCE_LOCK_20260701.csv" in artifacts
    assert "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_STATUS_20260701.json" in artifacts
    assert "517_NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_ARTIFACT_20260701.md" in artifacts
    assert "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_MANIFEST_20260701.csv" in artifacts

    manifest_rows = read_csv_rows(
        tmp_path / "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_MANIFEST_20260701.csv"
    )
    by_artifact = {row["artifact"]: row for row in manifest_rows}
    assert by_artifact[
        "NODI_COMSOL_PACKAGE_C_PROOF_REGISTRATION_MANIFEST_20260701.csv"
    ]["sha256"] == registration.SELF_MANIFEST_SHA256


def test_proof_registration_main_does_not_write_ready_outputs_on_validation_failure(
    monkeypatch,
    tmp_path,
    capsys,
) -> None:
    payload = _payload()
    broken = {
        **payload,
        "summary": {
            **payload["summary"],
            "proof_gap_rows": 1,
        },
    }
    monkeypatch.setattr(registration, "build_payload", lambda: broken)

    def fail_if_called(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("write_outputs should not be called on validation failure")

    monkeypatch.setattr(registration, "write_outputs", fail_if_called)
    code = registration.main(["--confirm-package-c-proof-registration-artifact"])
    captured = capsys.readouterr()

    assert code == 1
    assert "BLOCKED_PACKAGE_C_PROOF_REGISTRATION_ARTIFACT" in captured.out
    assert not list(tmp_path.iterdir())


def test_proof_registration_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_package_c_proof_registration_artifact.py",
        ],
        cwd=registration.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-package-c-proof-registration-artifact is required" in result.stderr
