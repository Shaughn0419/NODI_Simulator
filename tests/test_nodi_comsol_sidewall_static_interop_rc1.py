from __future__ import annotations

import json
import subprocess
import sys

from tools.audits import build_nodi_comsol_sidewall_static_interop_rc1 as rc1


def test_rc1_payload_disposition_matches_source_lock_cleanliness() -> None:
    payload = rc1.build_payload()
    issues = rc1.validate_payload(payload)

    assert issues == []
    dirty_blockers = payload["summary"]["dirty_blocker_count"]
    source_lock_blockers = payload["summary"]["source_lock_blocker_count"]
    missing_sources = payload["summary"]["missing_required_source_count"]
    if dirty_blockers or source_lock_blockers or missing_sources:
        assert payload["summary"]["disposition"] == rc1.PARTIAL_DISPOSITION
    else:
        assert payload["summary"]["disposition"] == rc1.PASS_DISPOSITION


def test_rc1_source_lock_blockers_force_partial_disposition() -> None:
    payload = rc1.build_payload()
    blocker_rows = [row for row in payload["source_lock"] if row["policy_impact"] == "BLOCKS_RC1_FREEZE_PASS"]

    if blocker_rows:
        assert payload["summary"]["source_lock_blocker_count"] == len(blocker_rows)
        assert payload["summary"]["disposition"] == rc1.PARTIAL_DISPOSITION
    else:
        assert payload["summary"]["source_lock_blocker_count"] == 0


def test_rc1_version_lock_digest_is_stable_for_semantic_basis() -> None:
    first = rc1.build_payload()["version_lock"]
    second = rc1.build_payload()["version_lock"]

    assert first["semantic_digest"] == second["semantic_digest"]
    assert first["semantic_basis"]["validator_families"] == 29
    assert first["semantic_basis"]["no_auth_locks"]["gate2d_rows"] == "4"
    assert first["semantic_basis"]["no_auth_locks"]["edge_state"] == "NOT_APPROVED_PREAUTH_ONLY"
    assert first["semantic_basis"]["no_auth_locks"]["qch_state"] == "ABSENT"
    assert first["semantic_basis"]["no_auth_locks"]["binding_state"] == "FAIL_CLOSED"


def test_rc1_static_fixture_rollup_covers_all_hard_fail_families() -> None:
    payload = rc1.build_payload()

    assert payload["summary"]["static_fixture_replay_rows"] == 29
    assert payload["summary"]["static_fixture_unknown_rows"] == 0
    assert {row["runtime_allowed"] for row in payload["fixture_rollup"]} == {"false"}
    assert {row["production_allowed"] for row in payload["fixture_rollup"]} == {"false"}
    assert {row["coverage_status"] for row in payload["fixture_rollup"]} == {
        "COVERED_STATIC_NO_RUNTIME"
    }


def test_rc1_comsol_gate16_ack_aligns_with_package_boundaries() -> None:
    payload = rc1.build_payload()
    by_package = {row["package"]: row for row in payload["comsol_ack"]}

    assert payload["summary"]["comsol_ack_rows"] == 4
    assert payload["summary"]["comsol_ack_misaligned_rows"] == 0
    assert by_package["Package A"]["alignment_status"] == "ACK_ALIGNED_NO_AUTH"
    assert by_package["Package B"]["alignment_status"] == "ACK_ALIGNED_NO_AUTH"
    assert by_package["Package D"]["alignment_status"] == "ACK_ALIGNED_NO_AUTH"
    assert by_package["Package C"]["comsol_ack_status"] == "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION"
    assert by_package["Package C"]["runtime_allowed"] == "false"
    assert by_package["Package C"]["production_allowed"] == "false"


def test_rc1_package_c_phrase_gate_does_not_authorize() -> None:
    payload = rc1.build_payload()

    assert payload["summary"]["package_c_auth_lock_rows"] >= 2
    assert {row["authorized_now"] for row in payload["package_c_lock"]} == {"false"}
    assert {row["package_c_physics_authorized"] for row in payload["package_c_lock"]} == {"false"}
    assert any(row["phrase_exact_match"] == "true" for row in payload["package_c_lock"])
    assert any(row["case"] == "generic_continue" for row in payload["package_c_lock"])


def test_rc1_decision_dossier_defaults_to_awaiting_user_decision() -> None:
    payload = rc1.build_payload()

    assert len(payload["decision_dossier"]) == 5
    assert {row["default_status"] for row in payload["decision_dossier"]} == {
        "AWAITING_USER_DECISION"
    }
    assert any(row["decision_id"] == "FREEZE_SIDEWALL_STATIC_INTEROP_RC1_NO_AUTH" for row in payload["decision_dossier"])
    assert any(row["decision_id"] == "OPEN_PACKAGE_C_PHYSICS_AUTHORIZATION_DISCUSSION_ONLY" for row in payload["decision_dossier"])


def test_rc1_no_auth_firewall_preserves_locked_states() -> None:
    payload = rc1.build_payload()

    forbidden = [
        row
        for row in payload["no_auth"]
        if row["field"] in rc1.FORBIDDEN_POSITIVE_FIELDS
    ]
    assert forbidden
    assert {row["positive_authorized_count"] for row in forbidden} == {"0"}
    assert payload["summary"]["gate2d_rows"] == 4
    assert payload["summary"]["edge_state"] == "NOT_APPROVED_PREAUTH_ONLY"
    assert payload["summary"]["qch_state"] == "ABSENT"
    assert payload["summary"]["binding_state"] == "FAIL_CLOSED"


def test_rc1_cli_requires_explicit_confirmation() -> None:
    result = subprocess.run(
        [sys.executable, "tools/audits/build_nodi_comsol_sidewall_static_interop_rc1.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-static-interop-rc1 is required" in result.stderr


def test_rc1_cli_writes_outputs_without_gate25_namespace() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_sidewall_static_interop_rc1.py",
            "--confirm-sidewall-static-interop-rc1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "SIDEWALL_STATIC_INTEROP_RC1" in result.stdout

    status_path = rc1.OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_STATUS_20260630.json"
    manifest_path = rc1.OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_MANIFEST_20260630.csv"
    report_path = rc1.REPORT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_NODI_MASTER_REPORT_20260630.md"

    status = json.loads(status_path.read_text(encoding="utf-8"))
    assert status["rc_id"] == rc1.RC_ID
    assert "GATE25" not in status_path.name
    assert "GATE25" not in manifest_path.name
    assert "GATE25" not in report_path.name
    assert manifest_path.exists()
    assert report_path.exists()
