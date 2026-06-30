from __future__ import annotations

import subprocess
import sys

from tools.audits import build_nodi_comsol_gate19_sidewall_static_preflight as gate19


def test_gate19_payload_passes_static_preflight_thresholds() -> None:
    payload = gate19.build_payload()

    assert gate19.validate_payload(payload) == []
    assert payload["summary"]["disposition"] == gate19.DISPOSITION
    assert payload["summary"]["gate18_unblocked"] is True
    assert payload["summary"]["package_a_status"] == "PASS_STATIC_PREFLIGHT_NO_RUNTIME"
    assert payload["summary"]["package_b_status"] == "PASS_STATIC_PREFLIGHT_NO_RUNTIME"
    assert payload["summary"]["package_d_status"] == "PASS_CONTRACT_PREFLIGHT_NO_RUNTIME"


def test_gate19_keeps_package_c_blocked_and_no_runtime_claims() -> None:
    payload = gate19.build_payload()
    rows = {row["package"]: row for row in payload["package_preflight"]}

    assert rows["Package C"]["preflight_status"] == "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION"
    for row in rows.values():
        assert row["runtime_allowed"] == "false"
        assert row["production_allowed"] == "false"
        assert row["validated_physics_claim"] == "false"


def test_gate19_no_auth_firewall_blocks_forbidden_promotions() -> None:
    payload = gate19.build_payload()
    firewall = payload["no_auth_firewall"][0]

    assert firewall["firewall_status"] == "PASS_NO_AUTH_LOCKS_PRESERVED"
    assert firewall["positive_authorization_count"] == "0"
    assert firewall["runtime_configuration_authorized"] == "false"
    assert firewall["production_ingestion_authorized"] == "false"
    assert firewall["qch_weighting_authorized"] == "false"
    assert firewall["jrc_authorized"] == "false"
    assert firewall["route_score_authorized"] == "false"
    assert firewall["yield_authorized"] == "false"
    assert firewall["detection_probability_authorized"] == "false"


def test_gate19_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate19_sidewall_static_preflight.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate19-sidewall-static-preflight is required" in result.stderr
