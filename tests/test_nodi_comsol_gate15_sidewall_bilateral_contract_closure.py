from __future__ import annotations

import subprocess
import sys

from tools.audits import build_nodi_comsol_gate15_sidewall_bilateral_contract_closure as gate15


def test_gate15_payload_passes_bilateral_contract_closure_thresholds() -> None:
    payload = gate15.build_payload(gate15.DEFAULT_COMSOL_ROOT)

    assert gate15.validate_payload(payload) == []


def test_gate15_keeps_comsol_gate14_partial_as_clean_reintake_requirement() -> None:
    payload = gate15.build_payload(gate15.DEFAULT_COMSOL_ROOT)
    partial = payload["comsol_partial_reason"][0]

    assert partial["treat_as_full_pass_now"] == "false"
    assert partial["nodi_verdict"] == "RACE_TIME_DELTA_REQUIRES_COMSOL_GATE15_CLEAN_REINTAKE"
    assert payload["summary"]["comsol_gate14_partial_is_time_delta"] is True


def test_gate15_no_auth_firewall_preserves_route_locks() -> None:
    payload = gate15.build_payload(gate15.DEFAULT_COMSOL_ROOT)
    firewall = payload["no_auth_firewall"][0]

    assert firewall["positive_authorization_count"] == "0"
    assert firewall["positive_runtime_or_production_count"] == "0"
    assert firewall["gate2d_rows"] == "4"
    assert firewall["edge_state"] == "NOT_APPROVED_PREAUTH_ONLY"
    assert firewall["qch_state"] == "ABSENT"
    assert firewall["binding_state"] == "FAIL_CLOSED"


def test_gate15_mutation_rows_are_fail_closed_and_above_threshold() -> None:
    payload = gate15.build_payload(gate15.DEFAULT_COMSOL_ROOT)

    assert payload["summary"]["mutation_rows"] >= 100000
    assert payload["summary"]["mutation_unexpected_pass"] == 0
    assert payload["summary"]["mutation_forbidden_promotion"] == 0
    assert {row["unexpected_pass"] for row in payload["mutation_results"]} == {"false"}


def test_gate15_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate15_sidewall_bilateral_contract_closure.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate15-sidewall-bilateral-closure is required" in result.stderr
