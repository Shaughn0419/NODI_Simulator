from __future__ import annotations

import subprocess
import sys

from tools.audits import build_nodi_comsol_gate22_sidewall_validator_binding as gate22


def test_gate22_payload_passes_validator_binding_validation() -> None:
    payload = gate22.build_payload()

    assert gate22.validate_payload(payload) == []
    assert payload["summary"]["disposition"] == gate22.DISPOSITION
    assert payload["summary"]["gate21_head_is_ancestor_of_current"] is True
    assert payload["summary"]["gate21_disposition"] == gate22.EXPECTED_GATE21_DISPOSITION
    assert payload["summary"]["gate21_no_auth"] is True
    assert payload["summary"]["gate21_review_only"] is True


def test_gate22_locks_gate21_sources_without_drift() -> None:
    payload = gate22.build_payload()

    assert payload["summary"]["gate21_source_lock_rows"] >= 9
    assert payload["summary"]["gate21_source_drift"] == 0
    assert payload["summary"]["gate21_missing_sources"] == 0
    assert {row["lock_status"] for row in payload["gate21_source_locks"]} == {"MATCH"}


def test_gate22_binds_every_gate21_family_to_static_validator_surface() -> None:
    payload = gate22.build_payload()
    hard_fail_codes = {row["hard_fail_code"] for row in payload["validator_bindings"]}

    assert payload["summary"]["validator_bindings"] >= 29
    assert payload["summary"]["binding_failures"] == 0
    assert {
        "missing_angle_convention",
        "rectangular_sampler_under_trapezoid",
        "blocked_bin_has_response",
        "edge4_to_edge20_direct_mapping",
        "bare_W_eff",
        "old_rectangular_cache_reuse",
    } <= hard_fail_codes
    for row in payload["validator_bindings"]:
        assert row["validator_entrypoint"]
        assert row["expected_rule_family"]
        assert row["binding_status"] == "PASS_CALLABLE_STATIC_BINDING"
        assert row["runtime_allowed"] == "false"
        assert row["production_allowed"] == "false"


def test_gate22_pytest_coverage_markers_are_present() -> None:
    payload = gate22.build_payload()

    assert payload["summary"]["pytest_coverage_rows"] == payload["summary"]["validator_bindings"]
    assert payload["summary"]["pytest_missing_markers"] == 0
    for row in payload["pytest_coverage"]:
        assert row["pytest_file_exists"] == "true"
        assert row["pytest_marker_present"] == "true"
        assert row["coverage_status"] == "PASS_PYTEST_MARKER_PRESENT"


def test_gate22_patch_queue_is_ready_for_gate23_static_fixture_plan() -> None:
    payload = gate22.build_payload()

    assert payload["summary"]["patches_required_before_static_fixture_execution"] == 0
    assert payload["summary"]["readiness_blocked_scopes"] == 0
    for row in payload["contract_patch_queue"]:
        assert row["patch_required_before_static_fixture_execution"] == "false"
        assert row["ready_for_gate23_fixture_execution_plan"] == "true"
        assert row["runtime_allowed"] == "false"
        assert row["production_allowed"] == "false"
    for row in payload["fixture_execution_readiness"]:
        assert row["readiness_status"] == "PASS_READY_FOR_GATE23_STATIC_FIXTURE_EXECUTION_PLAN"


def test_gate22_keeps_package_c_and_no_auth_firewall_closed() -> None:
    payload = gate22.build_payload()
    firewall = payload["package_c_and_firewall"][0]

    assert firewall["package_c_state"] == "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION"
    assert firewall["firewall_status"] == "PASS_NO_AUTH_LOCKS_PRESERVED"
    assert firewall["positive_authorization_count"] == "0"
    assert firewall["comsol_launch_authorized"] == "false"
    assert firewall["mph_load_authorized"] == "false"
    assert firewall["nodi_runtime_recompute_authorized"] == "false"
    assert firewall["qch_weighting_authorized"] == "false"
    assert firewall["jrc_authorized"] == "false"
    assert firewall["route_score_authorized"] == "false"
    assert firewall["yield_authorized"] == "false"
    assert firewall["detection_probability_authorized"] == "false"
    assert firewall["fabrication_release_authorized"] == "false"


def test_gate22_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate22_sidewall_validator_binding.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate22-validator-binding is required" in result.stderr
