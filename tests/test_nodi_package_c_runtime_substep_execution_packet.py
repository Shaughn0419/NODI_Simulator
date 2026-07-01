from __future__ import annotations

from functools import lru_cache
import subprocess
import sys

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_package_c_runtime_substep_execution_packet as packet


@lru_cache(maxsize=1)
def _payload() -> dict:
    return packet.build_payload()


def test_runtime_execution_packet_passes_with_guarded_smoke() -> None:
    payload = _payload()
    failures = packet.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == packet.DISPOSITION
    assert summary["package_c_proof_artifact_registered"] is True
    assert summary["runtime_execution_packet_built"] is True
    assert summary["guarded_runtime_smoke_executed"] is True
    assert summary["low_cost_smoke_support_violation_count"] == 0
    assert summary["low_cost_smoke_sample_count"] > 1
    assert summary["stress_required_substeps"] == 526
    assert summary["stress_blocked_as_expected"] is True


def test_runtime_execution_packet_does_not_promote_prs_comsol_solver_wet_route() -> None:
    summary = _payload()["summary"]

    for key in [
        "production_runtime_execution_started",
        "nodi_runtime_recomputation_started",
        "sidewall_prs_eas_numeric_output_current",
        "comsol_launch_started",
        "mph_load_started",
        "solver_output_current",
        "wet_claim_current",
        "route_yield_detection_claim_current",
    ]:
        assert summary[key] is False


def test_case_results_include_smoke_and_blocked_stress_roles() -> None:
    rows = _payload()["case_results"]
    by_case = {row["case_id"]: row for row in rows}

    smoke = by_case["low_cost_theta90_D900_r20_seed31031"]
    stress = by_case["narrow_tail_theta70_D900_r150"]

    assert smoke["case_role"] == "guarded_runtime_smoke_executed"
    assert smoke["runtime_smoke_executed"] == "true"
    assert smoke["runtime_policy_status"] == "runtime_allowed_with_low_cost_substeps"
    assert smoke["sidewall_prs_eas_numeric_allowed"] == "false"
    assert stress["case_role"] == "prohibitive_substep_stress_blocked"
    assert stress["runtime_smoke_executed"] == "false"
    assert stress["runtime_policy_status"] == "blocked_prohibitive_substep_cost"
    assert stress["sidewall_prs_eas_numeric_allowed"] == "false"


def test_trajectory_smoke_summary_has_zero_support_violations() -> None:
    row = _payload()["trajectory_smoke_summary"][0]

    assert row["runtime_smoke_executed"] == "true"
    assert row["support_violation_count"] == "0"
    assert int(row["trajectory_sample_count"]) > 1
    assert float(row["min_surface_gap_nm"]) >= 0.0
    assert row["random_seed"] == "31031"


def test_stress_blocker_is_fail_closed_not_waived() -> None:
    row = _payload()["stress_blockers"][0]

    assert row["runtime_policy_status"] == "blocked_prohibitive_substep_cost"
    assert row["runtime_allowed_by_guard"] == "false"
    assert row["execution_packet_required"] == "true"
    assert row["required_substeps_to_meet_threshold"] == "526"
    assert row["stress_blocker_status"] == "blocked_as_expected_no_manual_waiver"


def test_written_outputs_manifest_contains_runtime_execution_packet(tmp_path) -> None:
    payload = _payload()
    outputs = packet.write_outputs(
        payload,
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    artifacts = {path.name for path in outputs}

    assert "NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_STATUS_20260701.json" in artifacts
    assert "NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_CASE_RESULTS_20260701.csv" in artifacts
    assert "NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_TRAJECTORY_SMOKE_SUMMARY_20260701.csv" in artifacts
    assert "NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_STRESS_BLOCKERS_20260701.csv" in artifacts
    assert "520_NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_20260701.md" in artifacts

    manifest_rows = read_csv_rows(
        tmp_path
        / "joint_interface"
        / "NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_MANIFEST_20260701.csv"
    )
    by_artifact = {row["artifact"]: row for row in manifest_rows}
    assert by_artifact[
        "NODI_PACKAGE_C_RUNTIME_SUBSTEP_EXECUTION_PACKET_MANIFEST_20260701.csv"
    ]["sha256"] == packet.SELF_MANIFEST_SHA256


def test_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_package_c_runtime_substep_execution_packet.py",
        ],
        cwd=packet.PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-runtime-substep-execution-packet is required" in result.stderr
