from __future__ import annotations

import subprocess
import sys

from tools.audits import build_nodi_sidewall_package_c_candidate_exchange_rc2 as rc2


def test_rc2_payload_closes_gate32_clean_successor_and_pccr_stale_fail() -> None:
    payload = rc2.build_payload()
    failures = rc2.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == rc2.DISPOSITION
    assert summary["current_nodi_head"] == rc2.CURRENT_EXPECTED_HEAD
    assert summary["source_lock_closed"] is True
    assert summary["gate32_clean_successor_verdict"] == (
        "CLOSED_BY_GATE32_CLEAN_SUCCESSOR_A4757D6"
    )
    assert summary["comsol_pccr_status"] == rc2.EXPECTED_PCCR_STATUS
    assert summary["comsol_pccr_stale_fail_closed"] is True


def test_rc2_metric_qa_preserves_candidate_only_and_blocked_split() -> None:
    payload = rc2.build_payload()
    summary = payload["summary"]
    metric_rows = payload["metric_qa"]
    by_group = {row["metric_group"]: row for row in metric_rows}

    assert summary["scenario_metric_rows"] == 216
    assert summary["open_candidate_metric_rows"] == 198
    assert summary["blocked_candidate_rows"] == 18
    assert summary["dt_halving_rows"] == 66
    assert by_group["summary"]["candidate_status_normalized"] == "candidate_pass_not_proof"
    assert by_group["runtime_split:candidate_open"]["open_candidate_rows"] == 198
    assert by_group["runtime_split:blocked_geometry_closed"]["blocked_candidate_rows"] == 12
    assert by_group["runtime_split:blocked_near_closed_resource_guard"][
        "blocked_candidate_rows"
    ] == 6
    assert all(
        row["candidate_status_normalized"] != "candidate_pass"
        for row in metric_rows
    )


def test_rc2_registration_gap_keeps_authorization_fields_closed() -> None:
    rows = rc2.registration_gap_rows()
    by_field = {row["required_field"]: row for row in rows}

    for field in {
        "authorization_supersedes_no_auth_ledger_id",
        "authorization_supersedes_no_auth_ledger_sha256",
        "external_review_artifact_sha256",
        "implementation_commit_sha",
        "independent_reviewer_id_or_artifact_sha256",
    }:
        assert field in by_field
        assert by_field[field]["can_register_proof_now"] == "false"
        assert by_field[field]["can_mark_package_c_pass_now"] == "false"
        assert by_field[field]["draft_signoff_wording_status"] == "DRAFT_NOT_AUTHORIZATION"


def test_rc2_comsol_review_request_is_no_run_only() -> None:
    rows = rc2.review_request_rows()
    enums = {row["expected_output_enum"] for row in rows}

    assert "RECEIPT_VALIDATE_NOW_NO_RUN" in enums
    assert "CONTEXT_REVIEW_NOW_NO_RUN" in enums
    assert "FUTURE_COMSOL_RUN_REQUIRED_NOT_AUTHORIZED" in enums
    assert "FUTURE_MPH_LOAD_REQUIRED_NOT_AUTHORIZED" in enums
    assert "BLOCKED_AS_EXPECTED" in enums
    assert all(row["required_comsol_action"] == "no_run_review_only" for row in rows)
    assert all("COMSOL launch" in row["forbidden_action"] for row in rows)


def test_rc2_firewall_and_mutations_have_zero_promotions() -> None:
    payload = rc2.build_payload()
    firewall = payload["firewall"]
    mutations = payload["mutation"]

    assert len(firewall) >= 10
    assert sum(int(row["row_equivalent_count"]) for row in mutations) >= 300000
    assert all(row["proof_registration_authorized"] == "false" for row in firewall)
    assert all(row["package_c_validation_status_pass_authorized"] == "false" for row in firewall)
    assert all(row["runtime_allowed"] == "false" for row in firewall)
    assert all(row["observed_unexpected_pass"] == 0 for row in mutations)
    assert all(row["authorization_promotion"] == 0 for row in mutations)
    assert all(row["forbidden_promotion"] == 0 for row in mutations)


def test_rc2_written_outputs_manifest(tmp_path) -> None:
    payload = rc2.build_payload()
    outputs = rc2.write_outputs(
        payload,
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    manifest_rows = rc2.read_csv_rows(outputs["manifest"])
    artifacts = {row["artifact"] for row in manifest_rows}

    assert "NODI_SIDEWALL_PACKAGE_C_CANDIDATE_EXCHANGE_RC2_STATUS_20260630.json" in artifacts
    assert "NODI_SIDEWALL_PACKAGE_C_CANDIDATE_EXCHANGE_RC2_METRIC_QA_20260630.csv" in artifacts
    assert "NODI_SIDEWALL_PACKAGE_C_CANDIDATE_EXCHANGE_RC2_COMSOL_PCCR_FEEDBACK_CLOSURE_20260630.csv" in artifacts
    assert "490_NODI_SIDEWALL_PACKAGE_C_CANDIDATE_EXCHANGE_RC2_MASTER_REPORT_20260630.md" in artifacts
    assert outputs["manifest"].exists()


def test_rc2_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_sidewall_package_c_candidate_exchange_rc2.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-package-c-candidate-exchange-rc2 is required" in result.stderr
