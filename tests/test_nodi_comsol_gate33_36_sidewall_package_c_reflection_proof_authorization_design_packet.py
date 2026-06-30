from __future__ import annotations

import subprocess
import sys

from tools.audits import (
    build_nodi_comsol_gate33_36_sidewall_package_c_reflection_proof_authorization_design_packet as gate33_36,
)


def test_gate33_36_payload_is_authorization_design_only() -> None:
    payload = gate33_36.build_payload()
    failures = gate33_36.validate_payload(payload)
    summary = payload["summary"]

    assert failures == []
    assert summary["disposition"] == gate33_36.DISPOSITION
    assert summary["external_verdict"] == gate33_36.EXTERNAL_VERDICT
    assert summary["packet_output_status"] == "authorization_required_no_proof_registration"
    assert summary["gate32_disposition"] == gate33_36.EXPECTED_GATE32_DISPOSITION
    assert summary["gate30_31_disposition"] == gate33_36.EXPECTED_GATE30_31_DISPOSITION
    assert summary["rc2_disposition"] == gate33_36.EXPECTED_RC2_DISPOSITION
    assert summary["scenario_metric_rows"] >= 200
    assert summary["support_violation_count"] == 0
    assert summary["proof_registration_authorized"] is False
    assert summary["package_c_validation_status_pass_authorized"] is False
    assert summary["runtime_allowed"] is False
    assert summary["numeric_prs_eas_allowed"] is False
    assert summary["comsol_launch_allowed"] is False
    assert summary["mph_load_allowed"] is False


def test_gate33_36_backlog_captures_external_ai_next_evidence() -> None:
    rows = gate33_36.proof_hardening_backlog_rows()
    work_items = {row["work_item"] for row in rows}

    assert "clean_reviewed_commit_binding" in work_items
    assert "exact_vs_near_boundary_atom_split" in work_items
    assert "raw_histogram_artifact" in work_items
    assert "ess_autocorrelation_burnin_stride" in work_items
    assert "one_wall_folded_normal_suite" in work_items
    assert "projection_clamp_negative_control" in work_items
    assert "rejection_resampling_negative_control" in work_items
    assert "worst_case_dt_refinement" in work_items
    assert "corner_area_normalized_heatmap" in work_items
    assert all(row["can_register_proof_now"] == "false" for row in rows)
    assert all("Package C proof/pass registration" in row["blocked_use"] for row in rows)


def test_gate33_36_threshold_matrix_has_candidate_and_future_proof_lines() -> None:
    rows = gate33_36.threshold_matrix_rows()
    by_metric = {row["metric_name"]: row for row in rows}

    assert by_metric["dt_halving_distribution_delta"]["candidate_threshold"] == "<= 0.10"
    assert "<= 0.075" in by_metric["dt_halving_distribution_delta"][
        "future_proof_level_threshold"
    ]
    assert by_metric["equilibrium_uniformity_distance"]["candidate_threshold"] == "<= 0.06"
    assert "<= 0.04" in by_metric["equilibrium_uniformity_distance"][
        "future_proof_level_threshold"
    ]
    assert "0 exact atoms" in by_metric["exact_boundary_atom"][
        "future_proof_level_threshold"
    ]
    assert "d/sigma grid" in by_metric["one_wall_kernel_distance"]["hard_fail_note"]
    assert "distinct cache/signature" in by_metric["rectangle_limit"]["candidate_threshold"]


def test_gate33_36_authorization_placeholder_cannot_register_proof() -> None:
    rows = gate33_36.authorization_ledger_placeholder_rows()
    by_field = {row["field_name"]: row for row in rows}

    assert by_field["external_review_verdict"]["current_value"] == gate33_36.EXTERNAL_VERDICT
    assert by_field["external_review_artifact_sha256"]["current_value"] == ""
    assert by_field["manual_authorization_ledger_sha256"]["current_value"] == ""
    assert by_field["proof_registration_authorized"]["current_value"] == "false"
    assert by_field["package_C_validation_status_pass_authorized"]["current_value"] == "false"
    assert all(row["can_register_proof_now"] == "false" for row in rows)
    assert all(row["can_mark_package_c_pass_now"] == "false" for row in rows)


def test_gate33_36_hard_fail_checklist_blocks_promotion_paths() -> None:
    rows = gate33_36.hard_fail_checklist_rows()
    conditions = {row["condition"] for row in rows}

    assert "worktree_dirty_or_unreviewed_commit" in conditions
    assert "external_review_artifact_missing" in conditions
    assert "manual_authorization_ledger_missing" in conditions
    assert "exact_atom_split_missing" in conditions
    assert "one_wall_suite_missing" in conditions
    assert "negative_controls_missing" in conditions
    assert "runtime_or_numeric_flag_true" in conditions
    assert "forbidden_claim_column_present" in conditions
    assert all(row["effect"] == "block_proof_registration_and_package_c_pass" for row in rows)


def test_gate33_36_firewall_keeps_authorization_flags_false() -> None:
    firewall = gate33_36.no_proof_firewall_rows()[0]

    assert firewall["firewall_status"] == "PASS_GATE33_36_AUTHORIZATION_DESIGN_NO_PROOF_REGISTRATION"
    assert firewall["external_research_synthesis_received"] == "true"
    assert firewall["external_verdict"] == gate33_36.EXTERNAL_VERDICT
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
        }:
            assert value == "false", key


def test_gate33_36_written_outputs_manifest_is_complete_and_tmp_isolated(tmp_path) -> None:
    payload = gate33_36.build_payload()
    outputs = gate33_36.write_outputs(
        payload,
        output_dir=tmp_path / "joint_interface",
        report_dir=tmp_path / "reports",
    )
    manifest_rows = gate33_36.read_csv_rows(outputs["manifest"])
    artifacts = {row["artifact"] for row in manifest_rows}
    by_artifact = {row["artifact"]: row for row in manifest_rows}

    assert "NODI_COMSOL_GATE33_36_SIDEWALL_EXTERNAL_RESEARCH_SYNTHESIS_CAPTURE_20260630.md" in artifacts
    assert "NODI_COMSOL_GATE33_36_SIDEWALL_EVIDENCE_CHAIN_20260630.csv" in artifacts
    assert "NODI_COMSOL_GATE33_36_SIDEWALL_PROOF_HARDENING_BACKLOG_20260630.csv" in artifacts
    assert "NODI_COMSOL_GATE33_36_SIDEWALL_THRESHOLD_MATRIX_20260630.csv" in artifacts
    assert "NODI_COMSOL_GATE33_36_SIDEWALL_AUTHORIZATION_LEDGER_PLACEHOLDER_20260630.csv" in artifacts
    assert "NODI_COMSOL_GATE33_36_SIDEWALL_HARD_FAIL_CHECKLIST_20260630.csv" in artifacts
    assert "NODI_COMSOL_GATE33_36_SIDEWALL_REVIEW_REQUEST_20260630.md" in artifacts
    assert "491_NODI_COMSOL_GATE33_36A_EXTERNAL_RESEARCH_SYNTHESIS_INTAKE_20260630.md" in artifacts
    assert "495_NODI_COMSOL_GATE33_36_REFLECTION_PROOF_AUTHORIZATION_DESIGN_MASTER_REPORT_20260630.md" in artifacts
    assert by_artifact["NODI_COMSOL_GATE33_36_SIDEWALL_MANIFEST_20260630.csv"][
        "sha256"
    ] == gate33_36.SELF_MANIFEST_SHA256


def test_gate33_36_cli_requires_explicit_confirm() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "tools/audits/build_nodi_comsol_gate33_36_sidewall_package_c_reflection_proof_authorization_design_packet.py",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "--confirm-gate33-36-package-c-proof-authorization-design is required" in result.stderr
