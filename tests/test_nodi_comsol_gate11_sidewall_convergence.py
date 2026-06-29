from __future__ import annotations

import json
from pathlib import Path

from nodi_simulator.realism_v2_io import read_csv_rows
from tools.audits import build_nodi_comsol_gate11_sidewall_convergence as gate11


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "joint_interface_20260629"


def test_gate11_payload_passes_and_preserves_no_auth_boundaries() -> None:
    payload = gate11.build_payload(gate11.DEFAULT_COMSOL_ROOT)

    assert gate11.validate_payload(payload) == []
    assert payload["summary"]["disposition"] == gate11.DISPOSITION
    assert payload["summary"]["worktree_target_status"] in {
        "CLEAN_ALREADY_COMMITTED",
        "SELF_CONSISTENT_SIDEWALL_GUARD_PATCH_INCLUDED",
    }
    assert payload["summary"]["comsol_descriptor_rows"] == 11
    assert payload["summary"]["descriptor_validation_failures"] == 0
    assert payload["summary"]["descriptor_ledger_rows"] == 11
    assert payload["summary"]["addendum_field_rows"] == len(gate11.ADDENDUM_FIELDS)
    assert payload["summary"]["coverage_gaps"] == 0
    assert payload["summary"]["mutation_fixture_rows"] == 360
    assert payload["summary"]["unexpected_pass_count"] == 0
    assert payload["summary"]["forbidden_promotion_count"] == 0
    assert payload["summary"]["semantic_conflict_count"] == 0
    assert payload["summary"]["no_auth_sweep_failures"] == 0
    assert payload["summary"]["gate2d_rows"] == 4
    assert payload["summary"]["edge_state"] == "NOT_APPROVED_PREAUTH_ONLY"
    assert payload["summary"]["qch_state"] == "ABSENT"
    assert payload["summary"]["binding_state"] == "FAIL_CLOSED"


def test_comsol_gate10_descriptor_rows_validate_formula_hash_and_auth_flags() -> None:
    descriptor_checks, descriptor_ledger = gate11.descriptor_validation(
        gate11.DEFAULT_COMSOL_ROOT
    )

    assert len(descriptor_checks) == 11
    assert all(row["validation_status"] == "PASS" for row in descriptor_checks)
    assert all(row["angle_conversion_status"] == "PASS" for row in descriptor_checks)
    assert all(row["bottom_width_formula_status"] == "PASS" for row in descriptor_checks)
    assert all(row["descriptor_hash_status"] == "PASS" for row in descriptor_checks)
    assert all(row["authorization_flags_status"] == "PASS" for row in descriptor_checks)
    assert {row["receiver_lane"] for row in descriptor_ledger} == {
        "descriptor_review_only_quarantine",
    }
    assert all(row["can_enter_prs_eas_ingestion"] == "false" for row in descriptor_ledger)
    assert all(row["can_enter_edge"] == "false" for row in descriptor_ledger)
    assert all(row["can_enter_qch"] == "false" for row in descriptor_ledger)
    assert all(row["can_enter_jrc"] == "false" for row in descriptor_ledger)


def test_rc51_sidewall_addendum_is_review_only_and_contains_binding_fields() -> None:
    payload = gate11.build_payload(gate11.DEFAULT_COMSOL_ROOT)
    field_names = {row["field_name"] for row in payload["addendum_field_dictionary"]}
    lockfile = payload["addendum_lockfile"]

    assert lockfile["lock_name"] == gate11.ADDENDUM_VERSION
    assert lockfile["review_only"] is True
    assert lockfile["authorization"] == "closed"
    assert lockfile["historical_rc51_rewrite"] is False
    assert lockfile["runtime_contract"] is False
    assert lockfile["production_contract"] is False
    assert {
        "geometry_descriptor_id",
        "geometry_descriptor_sha256",
        "sidewall_deg_comsol",
        "sidewall_taper_angle_deg_nodi",
        "W_bottom_unclipped_nm",
        "W_bottom_runtime_clipped_nm",
        "runtime_guard_status",
        "sidewall_prs_v2_requires_descriptor_binding",
        "sidewall_eas_v2_requires_descriptor_binding",
        "optical_solver_triggered",
        "optical_geometry_claim_level",
    } <= field_names
    assert all(row["review_only"] == "true" for row in payload["addendum_field_dictionary"])
    assert all(row["runtime_contract"] == "false" for row in payload["addendum_field_dictionary"])
    assert all(row["production_contract"] == "false" for row in payload["addendum_field_dictionary"])


def test_prs_eas_sidewall_contract_coverage_is_closed() -> None:
    coverage = gate11.coverage_matrix()

    assert len(coverage) == 15
    assert all(row["implemented_status"] == "PASS" for row in coverage)
    assert all(row["test_status"] == "PASS" for row in coverage)
    assert {row["required_guard"] for row in coverage} >= {
        "sidewall artifact metadata",
        "descriptor provenance and source binding",
        "source grain borrowing rejection",
        "normalized coordinates",
        "particle radius / steric support",
        "runtime geometry propagation fields",
        "PRS blocked-bin numeric response rejection",
        "EAS runtime geometry context",
        "EAS reference context",
        "EAS optical trigger fields",
        "EAS optical claim-level consistency",
        "forbidden claim columns",
        "closed geometry propagation rejection",
    }


def test_quarantine_state_machine_blocks_direct_ingestion_and_runtime() -> None:
    rows = gate11.state_machine_rows()
    blocked = [row for row in rows if "PRS_EAS_ACCEPTED" in row["to_state"]]

    assert len(rows) == 6
    assert {row["to_state"] for row in blocked} == {"PRS_EAS_ACCEPTED_OR_RUNTIME"}
    assert all(row["current_execution_allowed"] == "false" for row in rows)
    assert all(
        row["forbidden_transition"] == "true"
        or "runtime;production" in row["forbidden_transition"]
        for row in rows
    )
    assert all(
        row["forbidden_transition"] == "true"
        or "EDGE;QCH;JRC" in row["forbidden_transition"]
        for row in rows
    )


def test_mutation_suite_has_zero_unexpected_pass_and_zero_promotion() -> None:
    fixtures = gate11.mutation_catalog()
    results, unexpected = gate11.mutation_results(fixtures)

    assert len(fixtures) == 360
    assert len(results) == 360
    assert len(unexpected) == 1
    assert unexpected[0]["unexpected_pass_count"] == "0"
    assert unexpected[0]["forbidden_promotion_count"] == "0"
    assert all(row["observed_result"] == row["expected_result"] for row in results)
    assert all(row["forbidden_promotion"] == "false" for row in results)


def test_no_auth_sweep_and_cross_project_convergence_are_clean() -> None:
    payload = gate11.build_payload(gate11.DEFAULT_COMSOL_ROOT)

    assert all(row["sweep_status"] == "PASS_NO_AUTH" for row in payload["no_auth_sweep"])
    assert all(
        row["convergence_status"] != "SEMANTIC_CONFLICT"
        for row in payload["convergence_matrix"]
    )
    assert any(row["convergence_status"] == "EXACT_MATCH" for row in payload["convergence_matrix"])
    assert any(
        row["convergence_status"] == "COMSOL_PRODUCER_EXTRA_REVIEW_ONLY"
        for row in payload["convergence_matrix"]
    )


def test_sidewall_package_d_dirty_patch_is_self_consistent_when_present() -> None:
    rows = gate11.target_worktree_status()

    assert rows
    if any(row["git_status"] != "clean" for row in rows):
        assert gate11.current_dirty_sidewall_patch_is_self_consistent()
        assert {
            row["disposition"] for row in rows
        } == {"SELF_CONSISTENT_SIDEWALL_GUARD_PATCH_INCLUDED"}


def test_gate11_written_outputs_have_expected_shape_after_builder_run() -> None:
    report_json = OUT / "NODI_COMSOL_GATE11_SIDEWALL_REPORT_20260629.json"
    if not report_json.exists():
        return

    report = json.loads(report_json.read_text(encoding="utf-8"))
    manifest = read_csv_rows(OUT / "NODI_COMSOL_GATE11_SIDEWALL_MANIFEST_20260629.csv")
    descriptor = read_csv_rows(
        OUT / "NODI_COMSOL_GATE11_SIDEWALL_COMSOL_DESCRIPTOR_ROW_VALIDATION_20260629.csv"
    )
    mutation = read_csv_rows(
        OUT / "NODI_COMSOL_GATE11_SIDEWALL_MUTATION_RESULTS_20260629.csv"
    )

    assert report["summary"]["comsol_descriptor_rows"] == 11
    assert len(manifest) == 35
    assert len(descriptor) == 11
    assert len(mutation) == 360
    assert all(row["not_evidence"] == "true" for row in manifest)
    assert all(row["no_auth"] == "true" for row in manifest)
