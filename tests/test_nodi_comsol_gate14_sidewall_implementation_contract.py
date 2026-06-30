from __future__ import annotations

import json
from pathlib import Path

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_gate14_sidewall_implementation_contract as gate14


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "joint_interface_20260630"


def test_gate14_payload_passes_release_contract_thresholds() -> None:
    payload = gate14.build_payload(gate14.DEFAULT_COMSOL_ROOT)

    assert gate14.validate_payload(payload) == []
    assert payload["summary"]["disposition"] == gate14.DISPOSITION
    assert payload["summary"]["worktree_clean"] is True
    assert payload["summary"]["implementation_guard_rows"] >= 26
    assert payload["summary"]["implementation_guard_blocked_rows"] == 2
    assert payload["summary"]["comsol_gate13_receipt_rows"] == 16
    assert payload["summary"]["comsol_gate13_blocking_drift"] == 0
    assert payload["summary"]["comsol_gate13_missing_required"] == 0
    assert payload["summary"]["comsol_gate13_package_head_expected"] == gate14.EXPECTED_COMSOL_GATE13_HEAD
    assert payload["summary"]["comsol_head_actual"] in gate14.ALLOWED_COMSOL_CURRENT_HEADS
    assert payload["summary"]["comsol_head_advanced_after_gate13"] is True
    assert payload["summary"]["stale_intake_closed"] is True
    assert payload["summary"]["mutation_rows"] == 50000
    assert payload["summary"]["mutation_unexpected_pass"] == 0
    assert payload["summary"]["mutation_forbidden_promotion"] == 0
    assert payload["summary"]["gate2d_rows"] == 4
    assert payload["summary"]["edge_state"] == "NOT_APPROVED_PREAUTH_ONLY"
    assert payload["summary"]["qch_state"] == "ABSENT"
    assert payload["summary"]["binding_state"] == "FAIL_CLOSED"


def test_post_gate13_delta_ledger_classifies_sidewall_guard_hardening() -> None:
    payload = gate14.build_payload(gate14.DEFAULT_COMSOL_ROOT)
    rows = payload["post_gate13_delta_ledger"]

    assert len(rows) >= 25
    categories = {row["guard_category"] for row in rows}
    assert "flow_alias_or_proxy_guard" in categories
    assert "decision_alias_denylist_guard" in categories
    assert "blocked_bin_or_grain_precheck_guard" in categories
    assert "profile_signature_source_hash_guard" in categories
    assert all(row["interface_impact"] == "additive_or_tightening_contract_guard" for row in rows)
    assert all(row["claim_risk"] == "no_auth_guard_prevents_promotion" for row in rows)


def test_implementation_guard_release_ledger_preserves_blocked_optical_and_wet_claims() -> None:
    payload = gate14.build_payload(gate14.DEFAULT_COMSOL_ROOT)
    rows = {row["gate_id"]: row for row in payload["implementation_guard_release_ledger"]}

    assert rows["optical_reference_solver"]["release_status"] == "BLOCKED_AS_EXPECTED"
    assert rows["wet_transport_claims"]["release_status"] == "BLOCKED_AS_EXPECTED"
    assert rows["comsol_descriptor_profile_hash_binding"]["release_status"] == "RELEASED_CLEAN_GUARD_PASS"
    assert rows["blocked_bin_response_guard"]["release_status"] == "RELEASED_CLEAN_GUARD_PASS"
    assert all(row["no_auth"] == "true" for row in rows.values())
    assert not any("model validation pass" in row["comsol_implication"].lower() for row in rows.values())


def test_contract_v3_schema_delta_contains_required_new_field_families_and_denylists() -> None:
    payload = gate14.build_payload(gate14.DEFAULT_COMSOL_ROOT)
    rows = payload["interface_contract_v3_schema_delta"]
    fields = {row["field_or_family"]: row for row in rows}

    for required in {
        "geometry_profile_source",
        "geometry_profile_sha256",
        "source_geometry_descriptor_sha",
        "runtime_top_aperture_nm",
        "top_cd_bias_nm",
        "measured_profile_lookup_status",
        "particle_center_support_status",
        "nearest_wall_distance_nm",
        "bin_accessible",
        "blocked_reason",
        "flow_rate",
        "Q",
        "q_ch",
        "route_score",
        "rank",
        "JRC",
        "chi_selected",
        "sidewall_aware",
    }:
        assert required in fields
    assert fields["flow_rate"]["forbidden_positive"] == "true"
    assert fields["q_ch"]["forbidden_positive"] == "true"
    assert fields["route_score"]["forbidden_positive"] == "true"
    assert fields["sidewall_aware"]["forbidden_positive"] == "true"
    assert all(row["change_type"] == "additive_or_clarifying_v3_delta" for row in rows)
    assert all(row["auth_impact"] == "none_no_auth" for row in rows)


def test_comsol_gate13_receipt_valid_and_stale_intake_closed() -> None:
    payload = gate14.build_payload(gate14.DEFAULT_COMSOL_ROOT)

    assert all(
        row["receipt_status"]
        in {"MATCH", "SELF_REFERENTIAL_METADATA_DRIFT_NON_POLICY", "READABLE_NOT_IN_MANIFEST_NON_BLOCKING"}
        for row in payload["comsol_gate13_receipt"]
    )
    assert not any(row["receipt_status"] == "BLOCKING_DATA_DRIFT" for row in payload["comsol_gate13_receipt"])
    closure = payload["stale_intake_closure"][0]
    assert closure["closure_status"] == "CLOSED_BY_NODI_GATE14_RELEASED_CLEAN"
    assert closure["closure_label"] == "SUPERSEDED_BY_NODI_GATE14_RELEASED_CLEAN_A9AB0C4_OR_LATER"
    assert closure["semantic_conflict"] == "false"
    assert closure["auth_promotion"] == "false"


def test_receiver_harness_v3_has_no_missing_required_and_no_outputs() -> None:
    payload = gate14.build_payload(gate14.DEFAULT_COMSOL_ROOT)
    rows = payload["receiver_harness_v3_coverage"]

    assert len(rows) == len(payload["interface_contract_v3_schema_delta"])
    assert not any(row["coverage_status"] == "MISSING_REQUIRED_FOR_V3" for row in rows)
    assert any(row["coverage_status"] == "FUTURE_COMSOL_EXPORT_REQUIRED" for row in rows)
    assert any(row["coverage_status"] == "BLOCKED_AS_EXPECTED" for row in rows)
    assert all(row["prs_eas_numeric_response_generated"] == "false" for row in rows)
    assert all(row["edge_jrc_qch_authorized"] == "false" for row in rows)
    assert all(row["yield_winner_detection_probability_authorized"] == "false" for row in rows)


def test_comsol_producer_request_v3_is_no_run_and_split_by_lane() -> None:
    payload = gate14.build_payload(gate14.DEFAULT_COMSOL_ROOT)
    rows = payload["comsol_producer_request_v3"]

    assert len(rows) == 8
    assert any(row["request_lane"] == "no-run descriptor/profile metadata export" for row in rows)
    assert any(row["request_lane"] == "review-only dry-run fixture export" for row in rows)
    assert any(row["request_lane"] == "binding blocker closure evidence" for row in rows)
    assert any("future-only" in row["request_lane"] for row in rows)
    assert all(row["comsol_run_authorized_now"] == "false" for row in rows)
    assert all(row["claim_boundary"] == "review-only/no-auth" for row in rows)


def test_package_readiness_board_keeps_package_c_blocked_and_no_validation_claim() -> None:
    payload = gate14.build_payload(gate14.DEFAULT_COMSOL_ROOT)
    rows = {row["package"]: row for row in payload["package_readiness_board"]}

    assert rows["Package A"]["go_no_go"] == "GO_STATIC_PREFLIGHT_ONLY"
    assert rows["Package B"]["go_no_go"] == "GO_STATIC_PREFLIGHT_ONLY"
    assert rows["Package C"]["go_no_go"] == "NO_GO_BLOCKED_FOR_PHYSICS"
    assert rows["Package D"]["go_no_go"] == "GO_CONTRACT_PREFLIGHT_ONLY"
    assert all(row["guard_pass_is_model_validation_pass"] == "false" for row in rows.values())
    assert all(row["runtime_or_production_allowed"] == "false" for row in rows.values())


def test_mutation_expansion_is_50000_and_clean() -> None:
    payload = gate14.build_payload(gate14.DEFAULT_COMSOL_ROOT)
    catalog = payload["mutation_catalog"]
    results = payload["mutation_results"]

    assert len(catalog) == 50000
    assert len(results) == 50000
    assert len({row["family"] for row in catalog}) >= 16
    assert all(row["not_evidence"] == "true" for row in catalog)
    assert all(row["match_status"] == "MATCH_EXPECTED" for row in results)
    assert all(row["unexpected_pass"] == "false" for row in results)
    assert all(row["forbidden_promotion"] == "false" for row in results)
    assert all(row["gate2d_row_count_drift"] == "false" for row in results)


def test_decision_dossier_and_no_auth_sweep_are_closed() -> None:
    payload = gate14.build_payload(gate14.DEFAULT_COMSOL_ROOT)

    assert len(payload["decision_dossier"]) == 5
    assert all(row["default_state"] == "AWAITING_USER_DECISION" for row in payload["decision_dossier"])
    assert all(row["approved_now"] == "false" for row in payload["decision_dossier"])
    assert all(row["sweep_status"] == "PASS_NO_AUTH" for row in payload["no_auth_sweep"])
    assert payload["no_auth_sweep"][0]["gate2d_rows"] == "4"
    assert payload["no_auth_sweep"][0]["edge_state"] == "NOT_APPROVED_PREAUTH_ONLY"
    assert payload["no_auth_sweep"][0]["qch_state"] == "ABSENT"
    assert payload["no_auth_sweep"][0]["binding_state"] == "FAIL_CLOSED"


def test_self_review_has_required_dimensions() -> None:
    payload = gate14.build_payload(gate14.DEFAULT_COMSOL_ROOT)
    topics = {row["focus"] for row in payload["self_review"]}

    assert len(payload["self_review"]) >= 14
    for required in {
        "post-Gate13 delta",
        "git cleanliness",
        "implementation audit",
        "schema v3 completeness",
        "COMSOL Gate13 stale-intake closure",
        "Package A boundary",
        "Package B boundary",
        "Package C boundary",
        "Package D boundary",
        "profile hash guard",
        "measured profile guard",
        "blocked-bin guard",
        "alias denylist",
        "mutation strength",
        "no-auth leakage",
        "test sufficiency",
        "Git scope",
    }:
        assert required in topics
    assert all(row["finding"] == "PASS_NO_P0_P1" for row in payload["self_review"])


def test_written_gate14_outputs_have_expected_shape_after_builder_run() -> None:
    report_json = OUT / "NODI_COMSOL_GATE14_SIDEWALL_REPORT_20260630.json"
    if not report_json.exists():
        return

    report = json.loads(report_json.read_text(encoding="utf-8"))
    manifest = read_csv_rows(OUT / "NODI_COMSOL_GATE14_SIDEWALL_MANIFEST_20260630.csv")
    guard = read_csv_rows(OUT / "NODI_COMSOL_GATE14_SIDEWALL_IMPLEMENTATION_GUARD_RELEASE_LEDGER_20260630.csv")
    mutations = read_csv_rows(OUT / "NODI_COMSOL_GATE14_SIDEWALL_MUTATION_RESULTS_20260630.csv")

    assert report["summary"]["disposition"] == gate14.DISPOSITION
    assert report["summary"]["implementation_guard_rows"] == 27
    assert report["summary"]["mutation_rows"] == 50000
    assert len(manifest) >= 18
    assert len(guard) >= 26
    assert len(mutations) == 50000
