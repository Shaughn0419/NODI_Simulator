from __future__ import annotations

import json
from pathlib import Path

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_gate13_sidewall_guard_convergence as gate13


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "joint_interface_20260629"


def test_gate13_payload_passes_guard_convergence_thresholds() -> None:
    payload = gate13.build_payload(gate13.DEFAULT_COMSOL_ROOT)

    assert gate13.validate_payload(payload) == []
    assert payload["summary"]["disposition"] == gate13.DISPOSITION
    assert payload["summary"]["comsol_gate12_commit_expected"] == gate13.COMSOL_GATE12_COMMIT
    assert payload["summary"]["comsol_gate13_commit_expected"] == gate13.COMSOL_GATE13_COMMIT
    assert payload["summary"]["comsol_project_head_actual"] in gate13.COMSOL_ALLOWED_CURRENT_HEADS
    assert payload["summary"]["unknown_dirty_blockers"] == 0
    assert payload["summary"]["comsol_gate12_receipt_rows"] == 11
    assert payload["summary"]["comsol_gate13_receipt_rows"] == 16
    assert payload["summary"]["comsol_receipt_rows"] == 16
    assert payload["summary"]["comsol_receipt_blocking_drift"] == 0
    assert payload["summary"]["comsol_receipt_missing_required"] == 0
    assert payload["summary"]["provenance_semantic_conflicts"] == 0
    assert payload["summary"]["provenance_dirty_open"] == 0
    assert payload["summary"]["mutation_rows"] == 12000
    assert payload["summary"]["mutation_unexpected_pass"] == 0
    assert payload["summary"]["mutation_forbidden_promotion"] == 0
    assert payload["summary"]["gate2d_rows"] == 4
    assert payload["summary"]["edge_state"] == "NOT_APPROVED_PREAUTH_ONLY"
    assert payload["summary"]["qch_state"] == "ABSENT"
    assert payload["summary"]["binding_state"] == "FAIL_CLOSED"


def test_worktree_reconciliation_has_no_unknown_dirty_blockers() -> None:
    payload = gate13.build_payload(gate13.DEFAULT_COMSOL_ROOT)

    assert payload["worktree_reconciliation"]
    assert all(row["unknown_blocker"] == "false" for row in payload["worktree_reconciliation"])
    assert {
        row["classification"] for row in payload["worktree_reconciliation"]
    } <= {
        "NO_DIRTY_WORKTREE",
        "LEGIT_GATE13_GENERATED_OUTPUT_PENDING_COMMIT",
        "LEGIT_SIDEWALL_HARDENING_CODE",
        "LEGIT_GATE11_GATE12_REPORT_REFRESH",
        "LEGIT_COMSOL_GATE12_PROVENANCE_SYNC",
        "LEGIT_GATE14_GENERATED_OUTPUT_PENDING_COMMIT",
    }


def test_comsol_gate12_receipt_and_provenance_repair_are_closed() -> None:
    payload = gate13.build_payload(gate13.DEFAULT_COMSOL_ROOT)

    assert all(
        row["receipt_status"]
        in {
            "MATCH",
            "READABLE_NOT_IN_MANIFEST_NON_BLOCKING_OPTIONAL",
            "SELF_REFERENTIAL_METADATA_DRIFT_NON_POLICY",
        }
        for row in payload["comsol_gate12_receipt"]
    )
    assert not any(row["receipt_status"] == "BLOCKING_DATA_DRIFT" for row in payload["comsol_gate12_receipt"])
    assert not any(row["receipt_status"] == "MISSING_REQUIRED_ARTIFACT" for row in payload["comsol_gate12_receipt"])
    repair = {row["field"]: row for row in payload["provenance_repair"]}
    assert repair["comsol_gate11_commit_expected"]["actual_value"] == gate13.COMSOL_GATE11_COMMIT
    assert repair["comsol_project_head_actual"]["actual_value"] in gate13.COMSOL_ALLOWED_CURRENT_HEADS
    assert repair["comsol_project_head_actual"]["repair_status"] in {
        "MATCH",
        "HEAD_ADVANCED_TO_KNOWN_GATE14_SUCCESSOR",
    }
    assert repair["comsol_gate12_commit_expected"]["actual_value"] == gate13.COMSOL_GATE12_COMMIT
    assert repair["comsol_gate13_commit_expected"]["actual_value"] in gate13.COMSOL_ALLOWED_CURRENT_HEADS
    assert repair["comsol_gate13_commit_expected"]["repair_status"] in {
        "MATCH",
        "HEAD_ADVANCED_TO_KNOWN_GATE14_SUCCESSOR",
    }
    assert all(row["semantic_conflict"] == "false" for row in payload["provenance_repair"])
    assert all(row["dirty_open"] == "false" for row in payload["provenance_repair"])


def test_closure_authority_contract_marks_trajectory_scope_and_forbidden_fields() -> None:
    payload = gate13.build_payload(gate13.DEFAULT_COMSOL_ROOT)
    rows = {row["field"]: row for row in payload["closure_authority_contract_v2"]}

    assert rows["trajectory_geometry_diagnostics_scope"]["semantics"] == (
        "config_only_not_closure_or_passability_verdict"
    )
    assert rows["trajectory_closure_authority"]["semantics"] == (
        "channel_geometry_runtime_guards_and_prs_eas_validators"
    )
    assert rows["fluidic_network_hydraulic_resistance_claim_level"]["field_class"] == (
        "review-only proxy field"
    )
    assert rows["q_ch_weighting_authorized"]["field_class"] == "forbidden evidence field"
    assert rows["JRC_authorized"]["authorization_flag_must_be_false"] == "true"
    assert all(row["runtime_or_production_contract"] == "false" for row in rows.values())


def test_closed_sidewall_harness_fails_or_quarantines_without_propagation() -> None:
    payload = gate13.build_payload(gate13.DEFAULT_COMSOL_ROOT)
    rows = payload["closed_sidewall_harness"]

    assert len(rows) >= 8
    assert all(row["runtime_propagation_allowed"] == "false" for row in rows)
    assert all(row["production_ingestion_allowed"] == "false" for row in rows)
    assert all(row["prs_eas_evidence_allowed"] == "false" for row in rows)
    assert all(row["comsol_context_accepted"] == "false" for row in rows)
    assert all(row["unexpected_pass"] == "false" for row in rows)
    assert {row["case_family"] for row in rows} >= {
        "closed_trapezoid",
        "near_closed_tiny_aperture",
        "clipped_to_zero",
        "negative_bottom_width",
        "micro_as_nano_spoof",
    }


def test_fluidic_network_proxy_firewall_blocks_qch_and_decision_fields() -> None:
    payload = gate13.build_payload(gate13.DEFAULT_COMSOL_ROOT)
    rows = payload["fluidic_proxy_firewall"]

    assert rows
    assert all(row["classification"] == "REVIEW_ONLY_PROXY_NOT_QCH_SIDECAR" for row in rows)
    assert all(row["can_be_qch"] == "false" for row in rows)
    assert all(row["can_enter_qch_weighting"] == "false" for row in rows)
    assert all(row["can_enter_route_score"] == "false" for row in rows)
    assert all(row["can_enter_jrc"] == "false" for row in rows)
    assert all(row["can_enter_yield"] == "false" for row in rows)
    assert all(row["can_enter_winner"] == "false" for row in rows)
    assert all(row["can_enter_detection_probability"] == "false" for row in rows)
    assert all(row["promotion_status"] == "BLOCKED" for row in rows)


def test_dryrun_harness_v2_is_review_or_quarantine_only() -> None:
    payload = gate13.build_payload(gate13.DEFAULT_COMSOL_ROOT)
    rows = payload["dryrun_harness_v2"]

    assert len(rows) == 25
    assert all(row["closure_authority_verdict"] == "PASS_DESCRIPTOR_FORMULA_REVIEW_ONLY" for row in rows)
    assert all(row["proxy_firewall_verdict"] == "PASS_PROXY_NOT_QCH" for row in rows)
    assert all(row["prs_eas_numeric_response_output"] == "false" for row in rows)
    assert all(row["edge_authorized"] == "false" for row in rows)
    assert all(row["qch_authorized"] == "false" for row in rows)
    assert all(row["jrc_authorized"] == "false" for row in rows)
    assert all(row["runtime_production_authorized"] == "false" for row in rows)
    assert {row["receipt_verdict"] for row in rows} <= {
        "QUARANTINE_UNBOUND_REVIEW_ONLY",
        "REVIEW_ONLY_DESCRIPTOR_RECEIPT_CANDIDATE",
    }


def test_interface_contract_v2_has_no_semantic_conflict_or_promotion() -> None:
    payload = gate13.build_payload(gate13.DEFAULT_COMSOL_ROOT)
    rows = payload["interface_contract_v2"]

    assert len(rows) >= 1
    assert all(row["semantic_conflict"] == "false" for row in rows)
    assert all(row["closed_sidewall_propagation"] == "false" for row in rows)
    assert all(row["fluidic_proxy_promotion"] == "false" for row in rows)
    assert all(row["auth_impact"] == "none_no_auth" for row in rows)


def test_mutation_expansion_is_large_deterministic_and_clean() -> None:
    payload = gate13.build_payload(gate13.DEFAULT_COMSOL_ROOT)
    catalog = payload["mutation_catalog"]
    results = payload["mutation_results"]

    assert len(catalog) == 12000
    assert len(results) == 12000
    assert len({row["family"] for row in catalog}) >= 16
    assert all(row["not_evidence"] == "true" for row in catalog)
    assert all(row["match_status"] == "MATCH_EXPECTED" for row in results)
    assert all(row["unexpected_pass"] == "false" for row in results)
    assert all(row["forbidden_promotion"] == "false" for row in results)
    assert all(row["gate2d_row_count_drift"] == "false" for row in results)


def test_release_signoff_choices_are_closed_and_mutually_exclusive() -> None:
    payload = gate13.build_payload(gate13.DEFAULT_COMSOL_ROOT)
    decisions = payload["decision_dossier"]

    assert {row["choice_id"] for row in decisions} == {
        "FREEZE_RC51_SIDEWALL_ADDENDUM_V1_NO_EVIDENCE_AUTH",
        "AUTHORIZE_NODI_DESCRIPTOR_RECEIPT_DRYRUN_V2_ONLY",
        "AUTHORIZE_STATIC_SIDEWALL_GUARD_RUNTIME_PREFLIGHT_ONLY_NO_PRS_EAS_RERUN",
        "DEFER_SIDEWALL_ADDENDUM_AND_KEEP_GATE12",
    }
    assert all(row["default_state"] == "AWAITING_USER_DECISION" for row in decisions)
    assert all(row["approved_now"] == "false" for row in decisions)
    assert all(row["mutually_exclusive"] == "true" for row in decisions)


def test_no_auth_sweep_and_self_review_are_clean() -> None:
    payload = gate13.build_payload(gate13.DEFAULT_COMSOL_ROOT)

    assert all(row["sweep_status"] == "PASS_NO_AUTH" for row in payload["no_auth_sweep"])
    assert len(payload["self_review"]) == 12
    assert all(row["finding"] == "PASS_NO_P0_P1" for row in payload["self_review"])


def test_written_gate13_outputs_have_expected_shape_after_builder_run() -> None:
    report_json = OUT / "NODI_COMSOL_GATE13_SIDEWALL_REPORT_20260629.json"
    if not report_json.exists():
        return

    report = json.loads(report_json.read_text(encoding="utf-8"))
    manifest = read_csv_rows(OUT / "NODI_COMSOL_GATE13_SIDEWALL_MANIFEST_20260629.csv")
    dryrun = read_csv_rows(OUT / "NODI_COMSOL_GATE13_SIDEWALL_DESCRIPTOR_DRYRUN_HARNESS_V2_20260629.csv")
    mutations = read_csv_rows(OUT / "NODI_COMSOL_GATE13_SIDEWALL_MUTATION_RESULTS_20260629.csv")

    assert report["summary"]["disposition"] == gate13.DISPOSITION
    assert report["summary"]["dryrun_v2_rows"] == 25
    assert report["summary"]["mutation_rows"] == 12000
    assert len(manifest) >= 18
    assert len(dryrun) == 25
    assert len(mutations) == 12000
    assert all(row["not_evidence"] == "true" for row in manifest)
    assert all(row["no_auth"] == "true" for row in manifest)
