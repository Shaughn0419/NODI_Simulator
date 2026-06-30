from __future__ import annotations

import subprocess
import sys

from tools.audits import build_nodi_comsol_gate17_sidewall_current_release_anchor as gate17


def test_gate17_payload_passes_anchor_validation() -> None:
    payload = gate17.build_payload(gate17.DEFAULT_COMSOL_ROOT)

    assert gate17.validate_payload(payload) == []
    assert payload["summary"]["disposition"] == gate17.DISPOSITION
    assert payload["summary"]["current_state"] == "NODI_ANCHOR_READY_FOR_COMSOL_REINTAKE"
    assert payload["summary"]["clean_current_reintake_accepted"] is False


def test_gate17_release_anchor_excludes_self_referential_package_commit() -> None:
    payload = gate17.build_payload(gate17.DEFAULT_COMSOL_ROOT)
    anchor = payload["release_anchor"]
    digest_without_manifest = gate17.release_anchor(anchor["semantic_base_head"])["semantic_digest_sha256"]

    assert anchor["semantic_digest_sha256"] == digest_without_manifest
    assert anchor["self_referential_commit_hash_excluded_from_semantic_digest"] is True
    assert anchor["anchor_manifest_sha256"].startswith("SELF_REFERENTIAL_MANIFEST_SHA_EXCLUDED")
    assert anchor["clean_successor_allowed"] is True
    assert "do not require build_head to equal package commit head" in anchor["comsol_consumption_rule"]


def test_gate17_dirty_classifier_blocks_unknown_but_allows_gate17_outputs() -> None:
    allowed_class, allowed_action = gate17.classify_dirty_path(
        "reports/joint_interface_20260630/NODI_COMSOL_GATE17_SIDEWALL_STATUS_20260630.json"
    )
    successor_class, successor_action = gate17.classify_dirty_path(
        "tools/audits/build_nodi_comsol_gate16_sidewall_clean_reintake_receipt.py"
    )
    gate18_class, gate18_action = gate17.classify_dirty_path(
        "reports/joint_interface_20260630/NODI_COMSOL_GATE18_SIDEWALL_STATUS_20260630.json"
    )
    gate19_class, gate19_action = gate17.classify_dirty_path(
        "reports/joint_interface_20260630/NODI_COMSOL_GATE19_SIDEWALL_STATUS_20260630.json"
    )
    gate20_class, gate20_action = gate17.classify_dirty_path(
        "reports/joint_interface_20260630/NODI_COMSOL_GATE20_SIDEWALL_STATUS_20260630.json"
    )
    gate21_class, gate21_action = gate17.classify_dirty_path(
        "reports/joint_interface_20260630/NODI_COMSOL_GATE21_SIDEWALL_STATUS_20260630.json"
    )
    unknown_class, unknown_action = gate17.classify_dirty_path("notes/unrelated.txt")

    assert allowed_class == "GATE17_GENERATED_OR_TEST"
    assert allowed_action == "allowed_for_gate17_build"
    assert successor_class == "GATE17_KNOWN_GATE16_SUCCESSOR_HEAD_COMPATIBILITY_UPDATE"
    assert successor_action == "allowed_for_gate17_build"
    assert gate18_class == "GATE18_GENERATED_OR_TEST"
    assert gate18_action == "allowed_for_gate17_build"
    assert gate19_class == "GATE19_GENERATED_OR_TEST"
    assert gate19_action == "allowed_for_gate17_build"
    assert gate20_class == "GATE20_GENERATED_OR_TEST"
    assert gate20_action == "allowed_for_gate17_build"
    assert gate21_class == "GATE21_GENERATED_OR_TEST"
    assert gate21_action == "allowed_for_gate17_build"
    assert unknown_class == "UNKNOWN_DIRTY_BLOCKER"
    assert unknown_action == "blocks_release_anchor"


def test_gate17_comsol_gate15_partial_is_not_clean_reintake_acceptance() -> None:
    payload = gate17.build_payload(gate17.DEFAULT_COMSOL_ROOT)

    assert payload["summary"]["comsol_gate15_receipt_rows"] >= 14
    assert payload["summary"]["comsol_gate15_blocking_drift"] == 0
    assert payload["summary"]["comsol_gate15_missing_required"] == 0
    assert payload["summary"]["clean_current_reintake_accepted"] is False
    assert payload["summary"]["comsol_gate15_status"].startswith("PARTIAL_COMSOL_GATE15")


def test_gate17_state_machine_keeps_static_preflight_pending_until_clean_comsol_reintake() -> None:
    payload = gate17.build_payload(gate17.DEFAULT_COMSOL_ROOT)
    states = {row["state"]: row for row in payload["state_machine"]}

    assert states["NODI_ANCHOR_READY_FOR_COMSOL_REINTAKE"]["current_or_future"] == "current"
    assert states["COMSOL_REINTAKE_CLEAN_ACCEPTED"]["current_or_future"] == "future"
    assert states["STATIC_PREFLIGHT_RECEIPT_ALLOWED"]["current_or_future"] == "future"
    for row in states.values():
        assert row["runtime_allowed"] == "false"
        assert row["production_allowed"] == "false"
        assert row["package_c"] == "blocked_requires_explicit_physics_authorization"


def test_gate17_comsol_instruction_targets_anchor_not_naked_head() -> None:
    payload = gate17.build_payload(gate17.DEFAULT_COMSOL_ROOT)
    actions = {row["action"]: row for row in payload["comsol_gate16_instruction_package"]}

    assert {
        "read_anchor",
        "verify_semantic_digest",
        "apply_clean_successor_policy",
        "close_old_stale_states",
        "preserve_no_auth_locks",
        "emit_gate16_clean_reintake",
        "hard_fail_forbidden_claims",
    } <= actions.keys()
    assert "naked latest HEAD" in actions["read_anchor"]["instruction"]
    for row in actions.values():
        assert row["comsol_run_allowed"] == "false"
        assert row["mph_load_allowed"] == "false"
        assert row["authorization_promotion_allowed"] == "false"


def test_gate17_mutation_and_no_auth_locks_remain_closed() -> None:
    payload = gate17.build_payload(gate17.DEFAULT_COMSOL_ROOT)
    firewall = payload["no_auth_firewall"][0]

    assert payload["summary"]["mutation_rows"] >= 120000
    assert payload["summary"]["mutation_unexpected_pass"] == 0
    assert payload["summary"]["mutation_forbidden_promotion"] == 0
    assert firewall["gate2d_rows"] == "4"
    assert firewall["edge_state"] == "NOT_APPROVED_PREAUTH_ONLY"
    assert firewall["qch_state"] == "ABSENT"
    assert firewall["binding_state"] == "FAIL_CLOSED"
    assert firewall["positive_runtime_or_production_count"] == "0"


def test_gate17_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate17_sidewall_current_release_anchor.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate17-sidewall-current-release-anchor is required" in result.stderr
