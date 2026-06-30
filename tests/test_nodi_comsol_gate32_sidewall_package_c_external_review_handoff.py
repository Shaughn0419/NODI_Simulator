from __future__ import annotations

import subprocess
import sys

from tools.audits import (
    build_nodi_comsol_gate32_sidewall_package_c_external_review_handoff as gate32,
)


def test_gate32_payload_is_external_review_handoff_only() -> None:
    payload = gate32.build_payload()
    failures = gate32.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == gate32.DISPOSITION
    assert summary["gate30_31_disposition"] == gate32.EXPECTED_GATE30_31_DISPOSITION
    assert summary["gate30_31_candidate_only"] is True
    assert summary["gate30_31_no_auth"] is True
    assert summary["gate30_31_metric_statuses_pass"] is True
    assert summary["research_synthesis_question_rows"] == len(
        gate32.RESEARCH_SYNTHESIS_QUESTIONS
    )
    assert summary["external_review_received"] is False
    assert summary["authorization_supersedes_no_auth_ledger"] is False
    assert summary["proof_registration_authorized"] is False
    assert summary["package_c_validation_status_pass_authorized"] is False
    assert summary["runtime_allowed"] is False
    assert summary["numeric_prs_eas_allowed"] is False
    assert summary["comsol_launch_allowed"] is False
    assert summary["mph_load_allowed"] is False


def test_gate32_github_path_map_is_raw_url_self_contained() -> None:
    rows = gate32.github_path_map_rows()
    labels = {row["review_label"] for row in rows}

    assert len(rows) >= 12
    assert "start_here_prompt" in labels
    assert "gate30_31_status" in labels
    assert "gate30_31_candidate_manifest" in labels
    assert "geometry_implementation" in labels
    assert "trajectory_integration" in labels
    for row in rows:
        assert row["github_raw_url"].startswith(gate32.GITHUB_RAW_BASE)
        assert row["github_blob_url"].startswith(gate32.GITHUB_BLOB_BASE)
        assert row["sha256"]
        assert "Package C proof/pass registration" in row["blocked_use"]


def test_gate32_handoff_prompt_contains_required_external_ai_context() -> None:
    payload = gate32.build_payload()
    text = payload["handoff_prompt_text"]

    assert "You can only rely on GitHub-visible files" in text
    assert "This is not a narrow audit request" in text
    assert "use your ability to search and" in text
    assert "## Research synthesis questions" in text
    assert gate32.DISPOSITION in text
    assert "READY_FOR_PROOF_REGISTRATION_AUTHORIZATION_DESIGN_REVIEW_ONLY" in text
    assert "NEEDS_MORE_CANDIDATE_EVIDENCE" in text
    assert "BLOCKED_CLAIM_PROMOTION" in text
    assert "`proof_registration_authorized=false`" in text
    assert "`package_c_validation_status_pass_authorized=false`" in text
    assert gate32.GITHUB_RAW_BASE in text


def test_gate32_research_synthesis_agenda_asks_for_broad_methodology_work() -> None:
    rows = gate32.research_synthesis_rows()
    topics = {row["topic"] for row in rows}

    assert len(rows) == len(gate32.RESEARCH_SYNTHESIS_QUESTIONS)
    assert "brownian_reflection_target" in topics
    assert "finite_step_algorithms" in topics
    assert "dt_convergence_thresholds" in topics
    assert "blocked_physics_boundaries" in topics
    assert all("literature/technical search" in row["expected_external_ai_action"] for row in rows)
    assert all("several future implementation gates" in row["required_output_style"] for row in rows)


def test_gate32_authorization_supersession_preflight_is_fail_closed() -> None:
    rows = gate32.authorization_supersession_rows()
    fields = {row["required_field"] for row in rows}

    assert fields == set(gate32.AUTHORIZATION_SUPERSESSION_FIELDS)
    assert "external_review_artifact_sha256" in fields
    assert "authorization_supersedes_no_auth_ledger_sha256" in fields
    assert "proof_registry_update_plan_sha256" in fields
    assert "package_C_proof_no_wet_claim" in fields
    assert all(row["can_register_proof_now"] == "false" for row in rows)
    assert all(row["can_mark_package_c_pass_now"] == "false" for row in rows)


def test_gate32_firewall_keeps_all_authorization_flags_false() -> None:
    firewall = gate32.firewall_rows()[0]

    assert firewall["firewall_status"] == "PASS_GATE32_EXTERNAL_HANDOFF_NO_PROOF_REGISTRATION"
    assert firewall["external_review_received"] == "false"
    assert firewall["authorization_supersedes_no_auth_ledger"] == "false"
    assert firewall["validated_brownian_solver_output_authorized"] == "false"
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
            "authorization_supersedes_no_auth_ledger",
            "external_review_received",
        }:
            assert value == "false", key


def test_gate32_written_outputs_manifest_includes_top_reports(tmp_path) -> None:
    payload = gate32.build_payload()
    outputs = gate32.write_outputs(
        payload,
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    manifest_rows = gate32.read_csv_rows(outputs["manifest"])
    artifacts = {row["artifact"] for row in manifest_rows}
    by_artifact = {row["artifact"]: row for row in manifest_rows}

    assert "NODI_COMSOL_GATE32_SIDEWALL_EXTERNAL_REVIEW_HANDOFF_PROMPT_20260630.md" in artifacts
    assert "NODI_COMSOL_GATE32_SIDEWALL_EXTERNAL_RESEARCH_SYNTHESIS_AGENDA_20260630.csv" in artifacts
    assert "NODI_COMSOL_GATE32_SIDEWALL_GITHUB_PATH_MAP_20260630.csv" in artifacts
    assert "485_NODI_COMSOL_GATE32A_EXTERNAL_REVIEW_HANDOFF_20260630.md" in artifacts
    assert "486_NODI_COMSOL_GATE32B_GITHUB_VISIBLE_ARTIFACT_MAP_20260630.md" in artifacts
    assert "487_NODI_COMSOL_GATE32C_AUTHORIZATION_SUPERSESSION_PREFLIGHT_20260630.md" in artifacts
    assert "488_NODI_COMSOL_GATE32D_NO_PROOF_REGISTRATION_FIREWALL_20260630.md" in artifacts
    assert "489_NODI_COMSOL_GATE32_SIDEWALL_PACKAGE_C_EXTERNAL_REVIEW_HANDOFF_MASTER_REPORT_20260630.md" in artifacts
    assert "NODI_COMSOL_GATE32_SIDEWALL_MANIFEST_20260630.csv" in artifacts
    assert by_artifact["NODI_COMSOL_GATE32_SIDEWALL_MANIFEST_20260630.csv"]["sha256"] == gate32.SELF_MANIFEST_SHA256


def test_gate32_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate32_sidewall_package_c_external_review_handoff.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate32-package-c-external-review-handoff is required" in result.stderr
