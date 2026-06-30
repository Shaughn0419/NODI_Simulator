from __future__ import annotations

import subprocess
import sys

from tools.audits import build_nodi_comsol_gate23_sidewall_static_fixture_execution as gate23


def test_gate23_payload_passes_static_fixture_execution_validation() -> None:
    payload = gate23.build_payload()

    assert gate23.validate_payload(payload) == []
    assert payload["summary"]["disposition"] == gate23.DISPOSITION
    assert payload["summary"]["gate22_head_is_ancestor_of_current"] is True
    assert payload["summary"]["gate22_disposition"] == gate23.EXPECTED_GATE22_DISPOSITION
    assert payload["summary"]["gate22_no_auth"] is True
    assert payload["summary"]["gate22_review_only"] is True


def test_gate23_locks_gate22_sources_without_drift() -> None:
    payload = gate23.build_payload()

    assert payload["summary"]["gate22_source_lock_rows"] >= 10
    assert payload["summary"]["gate22_source_drift"] == 0
    assert payload["summary"]["gate22_missing_sources"] == 0
    assert {row["lock_status"] for row in payload["gate22_source_locks"]} == {"MATCH"}


def test_gate23_static_fixture_execution_covers_gate22_bindings() -> None:
    payload = gate23.build_payload()
    hard_fail_codes = {row["hard_fail_code"] for row in payload["static_fixture_execution"]}

    assert payload["summary"]["static_fixture_execution_rows"] >= 29
    assert payload["summary"]["static_fixture_execution_blocked"] == 0
    assert {
        "missing_angle_convention",
        "rectangular_sampler_under_trapezoid",
        "blocked_bin_has_response",
        "edge4_to_edge20_direct_mapping",
        "bare_W_eff",
        "old_rectangular_cache_reuse",
    } <= hard_fail_codes
    for row in payload["static_fixture_execution"]:
        assert row["execution_status"] == "PASS_STATIC_FIXTURE_EXECUTABLE_NO_RUNTIME"
        assert row["execution_mode"] == "static_pytest_or_validator_function_only"
        assert row["static_command"].startswith("python -m pytest ")
        assert row["runtime_allowed"] == "false"
        assert row["production_allowed"] == "false"
        assert row["sidewall_numeric_output_allowed"] == "false"


def test_gate23_validator_cli_boundaries_are_context_only_not_production() -> None:
    payload = gate23.build_payload()

    assert payload["summary"]["cli_boundary_rows"] == 3
    assert payload["summary"]["cli_boundary_failures"] == 0
    for row in payload["cli_boundary"]:
        assert row["success_status_contract"] == "PASS_CONTEXT_ONLY_NOT_PRODUCTION"
        assert row["bare_PASS_allowed"] == "false"
        assert row["runtime_allowed"] == "false"
        assert row["production_allowed"] == "false"


def test_gate23_package_c_proof_registry_is_fail_closed() -> None:
    payload = gate23.build_payload()

    assert payload["summary"]["package_c_proof_lock_rows"] == 2
    assert payload["summary"]["package_c_proof_lock_failures"] == 0
    proof_lock = payload["package_c_proof_locks"][0]
    scope_lock = payload["package_c_proof_locks"][1]
    assert proof_lock["proof_registry_entries"] == "0"
    assert proof_lock["package_C_validation_status_pass_allowed"] == "false"
    assert proof_lock["lock_status"] == "PASS_FAIL_CLOSED_NO_AUTH"
    assert scope_lock["lock_status"] == "PASS_PACKAGE_B_CENTER_SUPPORT_ONLY"


def test_gate23_keeps_no_auth_firewall_closed() -> None:
    payload = gate23.build_payload()
    firewall = payload["no_auth_firewall"][0]

    assert firewall["firewall_status"] == "PASS_NO_AUTH_LOCKS_PRESERVED"
    assert firewall["comsol_launch_authorized"] == "false"
    assert firewall["mph_load_authorized"] == "false"
    assert firewall["nodi_runtime_recompute_authorized"] == "false"
    assert firewall["qch_weighting_authorized"] == "false"
    assert firewall["jrc_authorized"] == "false"
    assert firewall["route_score_authorized"] == "false"
    assert firewall["yield_authorized"] == "false"
    assert firewall["detection_probability_authorized"] == "false"
    assert firewall["fabrication_release_authorized"] == "false"
    assert firewall["package_c_physics_authorized"] == "false"


def test_gate23_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate23_sidewall_static_fixture_execution.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate23-static-fixture-execution is required" in result.stderr
