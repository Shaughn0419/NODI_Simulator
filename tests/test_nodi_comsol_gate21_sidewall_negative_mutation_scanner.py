from __future__ import annotations

import subprocess
import sys

from tools.audits import build_nodi_comsol_gate21_sidewall_negative_mutation_scanner as gate21


def test_gate21_payload_passes_negative_mutation_scanner_validation() -> None:
    payload = gate21.build_payload()

    assert gate21.validate_payload(payload) == []
    assert payload["summary"]["disposition"] == gate21.DISPOSITION
    assert payload["summary"]["gate20_head_is_ancestor_of_current"] is True
    assert payload["summary"]["gate20_disposition"] == gate21.EXPECTED_GATE20_DISPOSITION
    assert payload["summary"]["gate20_no_auth"] is True
    assert payload["summary"]["gate20_review_only"] is True


def test_gate21_locks_gate20_sources_without_drift() -> None:
    payload = gate21.build_payload()

    assert payload["summary"]["gate20_source_lock_rows"] >= 10
    assert payload["summary"]["gate20_source_drift"] == 0
    assert payload["summary"]["gate20_missing_sources"] == 0
    assert {row["lock_status"] for row in payload["gate20_source_locks"]} == {"MATCH"}


def test_gate21_negative_fixture_catalog_covers_gate20_hard_fail_surface() -> None:
    payload = gate21.build_payload()
    hard_fail_codes = {row["hard_fail_code"] for row in payload["mutation_families"]}
    fixture_codes = {row["hard_fail_code"] for row in payload["fixture_catalog"]}

    assert payload["summary"]["mutation_families"] >= 29
    assert payload["summary"]["negative_fixtures"] == payload["summary"]["mutation_families"] * len(gate21.FIXTURE_VARIANTS)
    assert hard_fail_codes == fixture_codes
    assert {
        "missing_angle_convention",
        "silent_bottom_clip",
        "rectangular_sampler_under_trapezoid",
        "blocked_bin_has_response",
        "edge4_to_edge20_direct_mapping",
        "D900_to_D1200_borrowing",
        "auto_admit_220_or_300nm",
        "bare_W_eff",
        "rank_or_score_field_present",
        "old_rectangular_cache_reuse",
    } <= hard_fail_codes


def test_gate21_scanner_rows_all_fail_closed_without_claim_promotion() -> None:
    payload = gate21.build_payload()

    assert payload["summary"]["scanner_rows"] == payload["summary"]["negative_fixtures"]
    assert payload["summary"]["scanner_unexpected_pass"] == 0
    assert payload["summary"]["scanner_forbidden_promotion"] == 0
    for row in payload["scanner_results"]:
        assert row["scanner_status"] == "PASS_EXPECTED_FAIL_CLOSED"
        assert row["observed_result"] == "FAIL_CLOSED_OR_BLOCKED_AUDIT"
        assert row["unexpected_pass"] == "false"
        assert row["forbidden_promotion"] == "false"


def test_gate21_keeps_package_c_and_no_auth_firewall_closed() -> None:
    payload = gate21.build_payload()
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


def test_gate21_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate21_sidewall_negative_mutation_scanner.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate21-negative-mutation-scanner is required" in result.stderr
