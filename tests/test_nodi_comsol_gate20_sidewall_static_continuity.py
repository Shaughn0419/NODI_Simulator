from __future__ import annotations

import subprocess
import sys

from tools.audits import build_nodi_comsol_gate20_sidewall_static_continuity as gate20


def test_gate20_payload_passes_static_continuity_validation() -> None:
    payload = gate20.build_payload(gate20.DEFAULT_COMSOL_ROOT)

    assert gate20.validate_payload(payload) == []
    assert payload["summary"]["disposition"] == gate20.DISPOSITION
    assert payload["summary"]["gate19_head_is_ancestor_of_current"] is True
    assert payload["summary"]["comsol_head_actual"] == gate20.EXPECTED_COMSOL_GATE16_HEAD
    assert payload["summary"]["comsol_anchor_digest"] == gate20.EXPECTED_COMSOL_ANCHOR_DIGEST


def test_gate20_locks_gate19_sources_without_reopening_stale_head_loop() -> None:
    payload = gate20.build_payload(gate20.DEFAULT_COMSOL_ROOT)

    assert payload["summary"]["gate19_manifest_rows"] >= 6
    assert payload["summary"]["gate19_source_drift"] == 0
    assert payload["summary"]["gate19_missing_sources"] == 0
    assert payload["summary"]["comsol_consumed_nodi_head_is_ancestor_of_gate19"] is True
    head_rows = {row["advance_id"]: row for row in payload["post_gate16_head_advance"]}
    assert head_rows["G20E-HEAD-ADVANCE-003"]["stale_head_risk"] == "pass"


def test_gate20_hard_fail_surface_keeps_abd_static_and_package_c_blocked() -> None:
    payload = gate20.build_payload(gate20.DEFAULT_COMSOL_ROOT)
    hard_fail_codes = {row["hard_fail_code"] for row in payload["validator_surface"]}

    assert {
        "missing_angle_convention",
        "bare_W_top_runtime_binding",
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
    assert len(payload["validator_surface"]) >= 29
    for row in payload["validator_surface"] + payload["package_c_blocked"]:
        assert row["runtime_allowed"] == "false"
        assert row["production_allowed"] == "false"
    assert payload["package_c_blocked"][0]["blocked_status"] == "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION"


def test_gate20_no_auth_firewall_blocks_runtime_and_claim_promotion() -> None:
    payload = gate20.build_payload(gate20.DEFAULT_COMSOL_ROOT)
    firewall = payload["no_auth_firewall"][0]

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
    assert firewall["package_c_authorized"] == "false"


def test_gate20_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate20_sidewall_static_continuity.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate20-static-continuity is required" in result.stderr
