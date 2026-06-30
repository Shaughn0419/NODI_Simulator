from __future__ import annotations

import json
import subprocess
import sys

from tools.audits import build_nodi_comsol_sidewall_static_interop_rc1_final_closure as rc1f


def test_rc1_final_payload_closes_old_source_lock_blocker() -> None:
    payload = rc1f.build_payload()

    assert rc1f.validate_payload(payload) == []
    assert payload["summary"]["disposition"] == rc1f.DISPOSITION
    assert payload["summary"]["source_lock_blocker_count"] == 0
    assert payload["summary"]["dirty_blocker_count"] == 0
    assert {row["closure_status"] for row in payload["source_lock_closure"]} == {
        "CLOSED_CLEAN_SUCCESSOR_REVIEW_ONLY_NO_AUTH",
        "CLOSED_AS_RC2_BACKLOG_NO_AUTH",
    }


def test_rc1_final_preserves_semantic_digest_and_no_auth_locks() -> None:
    payload = rc1f.build_payload()
    lock = payload["final_version_lock"]

    assert lock["semantic_digest"] == rc1f.semantic_digest()
    assert lock["source_lock_blocker_count"] == 0
    assert lock["dirty_blocker_count"] == 0
    assert lock["no_auth_locks"]["gate2d_rows"] == "4"
    assert lock["no_auth_locks"]["edge_state"] == "NOT_APPROVED_PREAUTH_ONLY"
    assert lock["no_auth_locks"]["qch_state"] == "ABSENT"
    assert lock["no_auth_locks"]["binding_state"] == "FAIL_CLOSED"


def test_gate25_is_bound_to_rc2_backlog_not_permission() -> None:
    payload = rc1f.build_payload()

    assert payload["summary"]["gate25_backlog_rows"] == 1
    assert payload["final_version_lock"]["gate25_backlog_binding"] == (
        "RC2_BACKLOG_DESIGN_REVIEW_ONLY_NO_IMPLEMENTATION_PERMISSION"
    )
    assert any(row["category"] == "PACKAGE_C_PHYSICS_AUTHORIZATION_DISCUSSION_ONLY" for row in payload["rc2_backlog"])
    assert all(not row["status"].startswith("AUTHORIZED") for row in payload["rc2_backlog"])


def test_comsol_ack_is_time_delta_context_not_rejected() -> None:
    payload = rc1f.build_payload()

    assert payload["summary"]["comsol_reintake_pointer_rows"] == 4
    assert {
        row["context_status"]
        for row in payload["comsol_reintake_pointer"]
    } == {"PRODUCER_ACK_CONTEXT_PARTIAL_DUE_PRIOR_NODI_RC1_ABSENCE_OR_TIME_DELTA"}
    assert all("no-run no-auth" in row["allowed_use"] for row in payload["comsol_reintake_pointer"])


def test_package_c_remains_blocked_and_no_runtime_or_production() -> None:
    payload = rc1f.build_payload()

    assert payload["summary"]["gate2d_rows"] == 4
    assert payload["summary"]["edge_state"] == "NOT_APPROVED_PREAUTH_ONLY"
    assert payload["summary"]["qch_state"] == "ABSENT"
    assert payload["summary"]["binding_state"] == "FAIL_CLOSED"
    assert payload["summary"]["static_fixture_unknown_rows"] == 0
    assert payload["final_version_lock"]["package_c_status"] == "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION"
    assert {row["positive_authorized_count"] for row in payload["no_auth_firewall"]} == {"0"}


def test_rc2_backlog_contains_required_future_categories() -> None:
    payload = rc1f.build_payload()
    categories = {row["category"] for row in payload["rc2_backlog"]}

    assert categories == {
        "DESCRIPTOR_RECEIPT_DRYRUN_ONLY",
        "BINDING_POLICY_REVIEW",
        "PACKAGE_C_PHYSICS_AUTHORIZATION_DISCUSSION_ONLY",
        "COMSOL_PRODUCER_FINAL_ACK_REINTAKE",
    }


def test_rc1_final_cli_requires_confirmation() -> None:
    result = subprocess.run(
        [sys.executable, "tools/audits/build_nodi_comsol_sidewall_static_interop_rc1_final_closure.py"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-sidewall-static-interop-rc1-final is required" in result.stderr


def test_rc1_final_cli_writes_machine_readable_outputs() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_sidewall_static_interop_rc1_final_closure.py",
            "--confirm-sidewall-static-interop-rc1-final",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert rc1f.DISPOSITION in result.stdout
    status_path = rc1f.OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_FINAL_STATUS_20260630.json"
    manifest_path = rc1f.OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC1_FINAL_MANIFEST_20260630.csv"
    backlog_path = rc1f.OUTPUT_DIR / "SIDEWALL_STATIC_INTEROP_RC2_BACKLOG_20260630.csv"

    status = json.loads(status_path.read_text(encoding="utf-8"))
    assert status["disposition"] == rc1f.DISPOSITION
    assert manifest_path.exists()
    assert backlog_path.exists()
