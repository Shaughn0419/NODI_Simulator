from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


R5_2_DIR = rv2.DEFAULT_R5_2_BOUNDED_SCENARIO_PRIOR_AUDIT_DIR


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _csv_headers(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return set(next(csv.reader(handle)))


def test_R5_2_audit_requires_exact_external_authorization(tmp_path):
    with pytest.raises(ValueError, match="exact external authorization"):
        rv2.run_R5_2_bounded_scenario_prior_audit(
            tmp_path,
            external_authorization="PASS_R5_2_PLAN_ONLY",
            write_root_manifest=False,
        )


def test_R5_2_outputs_required_files_only_and_respect_cap():
    assert R5_2_DIR.exists()
    files = {p.name for p in R5_2_DIR.iterdir() if p.is_file()}

    assert files == rv2.R5_2_REQUIRED_OUTPUTS_IF_AUTHORIZED

    manifest = _csv_rows(R5_2_DIR / "R5_2_scenario_prior_audit_manifest.csv")[0]
    assert manifest["external_authorization"] == "PASS_TO_BOUNDED_SCENARIO_PRIOR_AUDIT_ONLY"
    assert manifest["R5_2_bounded_scenario_prior_audit_run"] == "True"
    assert manifest["audit_execution_type"] == "posthoc_existing_R5_artifact_audit_only"
    assert manifest["existing_R5_rows_audited"] == "14784"
    assert manifest["audit_route_id_count"] == "33"
    assert manifest["scenario_bundle_count"] == "8"
    assert manifest["stochastic_seed_count"] == "0"
    assert manifest["new_case_rows_added"] == "0"
    assert manifest["new_scenario_bundles_added"] == "0"
    assert manifest["new_stochastic_seeds_added"] == "0"
    assert manifest["new_solver_cases_added"] == "0"
    assert manifest["new_experiments_started"] == "0"


def test_R5_2_traceability_is_exact_14784_existing_R5_rows():
    rows = _csv_rows(R5_2_DIR / "R5_2_audit_route_set_traceability.csv")

    assert len(rows) == rv2.R5_2_EXISTING_R5_AUDIT_ROW_CAP
    assert {row["route_id"] for row in rows} == rv2.R5_2_AUDIT_ROUTE_IDS
    assert {row["scenario_bundle"] for row in rows} == rv2.R5_REQUIRED_SCENARIO_BUNDLE_IDS
    assert {row["stochastic_seed"] for row in rows} == {""}
    assert len({row["particle_name"] for row in rows}) == rv2.R5_V1_SOURCE_PARTICLE_NAME_COUNT
    assert all(row["SNR_claim_level"] == "absolute_blocked" for row in rows)
    assert all(row["event_probability_claim_level"] == "absolute_blocked" for row in rows)
    assert all(row["p_detect_mapping_claim_level"] == "relative_with_priors" for row in rows)
    assert all(row["context_route_promotion_authorized"] == "False" for row in rows)
    assert all(row["main_660_redefinition_authorized"] == "False" for row in rows)
    assert all(row["route_specific_manual_sign_flip_applied"] == "False" for row in rows)


def test_R5_2_context_routes_are_all_audited_and_non_promoting():
    rows = _csv_rows(R5_2_DIR / "R5_2_context_route_above_main_audit.csv")

    assert len(rows) == 20
    assert {row["route_id"] for row in rows} == rv2.R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS
    assert rows[0]["route_id"] == "660_500x1500"
    assert all(row["scenario_bundle_count_above_main_660"] == "8" for row in rows)
    assert all(row["context_route_promotion_authorized"] == "False" for row in rows)
    assert all(row["route_promotion_eligible"] == "False" for row in rows)
    assert all(
        row["interpretation"] == "systematic_above_main_context_warning_not_route_promotion"
        for row in rows
    )


def test_R5_2_weak_reference_and_scenario_contributions_are_systematic_warnings():
    weak = _csv_rows(R5_2_DIR / "R5_2_weak_reference_control_audit.csv")[0]
    scenarios = _csv_rows(R5_2_DIR / "R5_2_scenario_bundle_contribution_audit.csv")

    assert weak["route_id"] == "660_700x1500"
    assert weak["scenario_bundle_count_exceeding_main_660"] == "8"
    assert weak["route_promotion_authorized"] == "False"
    assert weak["R6_plan_preparation_authorized"] == "False"
    assert float(weak["ratio_vs_main_660_mean"]) > 1.0

    assert len(scenarios) == 8
    assert {row["scenario_bundle"] for row in scenarios} == rv2.R5_REQUIRED_SCENARIO_BUNDLE_IDS
    assert all(row["weak_reference_exceeds_main_660"] == "True" for row in scenarios)
    assert all(row["context_route_family_exceeds_main_660"] == "True" for row in scenarios)
    assert all(row["new_scenario_bundle_authorized"] == "False" for row in scenarios)
    assert all(row["calibrated_probability_claim_authorized"] == "False" for row in scenarios)


def test_R5_2_decision_blocks_R6_and_selects_route_prior_revision_plan_only():
    decisions = _csv_rows(R5_2_DIR / "R5_2_audit_decision_table.csv")
    by_subject = {row["decision_subject"]: row for row in decisions}
    matrix = _csv_rows(R5_2_DIR / "R5_2_next_stage_recommendation_matrix.csv")
    selected = [
        row for row in matrix if row["R5_2_recommendation"] == "selected_for_future_review"
    ]

    assert set(by_subject) == {
        "weak_reference_control",
        "above_main_context_routes",
        "main_660_locked_anchor",
        "selected_annulus_and_404_sidecars",
    }
    assert by_subject["weak_reference_control"]["recommended_next_class"] == (
        "prepare_route_prior_model_revision_plan_only"
    )
    assert by_subject["above_main_context_routes"]["R6_plan_preparation_authorized"] == "False"
    assert all(row["route_promotion_authorized"] == "False" for row in decisions)
    assert all(row["main_660_redefinition_authorized"] == "False" for row in decisions)

    assert len(selected) == 1
    assert selected[0]["future_recommendation_class"] == (
        "prepare_route_prior_model_revision_plan_only"
    )
    assert all(row["authorizes_execution"] == "False" for row in matrix)
    assert all(row["authorizes_R6_plan"] == "False" for row in matrix)
    assert all(row["authorizes_route_promotion"] == "False" for row in matrix)


def test_R5_2_main_selected_annulus_and_claim_guardrails_are_closed():
    main_rows = _csv_rows(R5_2_DIR / "R5_2_main_660_locked_comparator_summary.csv")
    sidecars = _csv_rows(
        R5_2_DIR / "R5_2_selected_annulus_and_404_sidecar_guardrail_summary.csv"
    )
    guardrails = {
        row["guardrail"]: row
        for row in _csv_rows(R5_2_DIR / "R5_2_claim_boundary_guardrail_summary.csv")
    }

    assert {row["route_id"] for row in main_rows} == {"660_800x1400", "660_800x1500"}
    assert all(row["main_660_route_role_locked"] == "True" for row in main_rows)
    assert all(row["main_660_redefinition_authorized"] == "False" for row in main_rows)
    assert all(row["route_promotion_authorized"] == "False" for row in main_rows)

    assert {row["route_id"] for row in sidecars} == {
        "404_600x1300",
        "404_800x550",
        "404_800x600",
        "404_800x700",
        "660_800x550",
        "660_800x600",
        "660_800x700",
    }
    assert all(
        row["selected_annulus_replaces_all_crossing_ranking"] == "False"
        for row in sidecars
    )
    assert all(row["selected_annulus_bound_change_authorized"] == "False" for row in sidecars)
    assert all(
        row["thermal_sidecar_used_to_increase_NODI_score"] == "False"
        for row in sidecars
    )

    assert guardrails["SNR_claim_level"]["value"] == "absolute_blocked"
    assert guardrails["event_probability_claim_level"]["value"] == "absolute_blocked"
    assert guardrails["p_detect_mapping_claim_level"]["value"] == "relative_with_priors"
    assert guardrails["legacy_detector_SNR_output_header_emitted"]["status"] == "pass"
    assert guardrails["legacy_calibrated_detector_SNR_output_header_emitted"]["status"] == "pass"
    assert guardrails["thermal_sidecar_used_to_increase_NODI_score"]["status"] == "pass"


def test_R5_2_manifest_is_fail_closed():
    manifest = json.loads((R5_2_DIR / "run_manifest.json").read_text(encoding="utf-8"))

    assert manifest["run_id"] == "EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit"
    assert manifest["R5_2_bounded_scenario_prior_audit_run"] is True
    assert manifest["R5_2_selected_future_recommendation_class"] == (
        "prepare_route_prior_model_revision_plan_only"
    )
    assert manifest["new_case_rows_authorized"] == 0
    assert manifest["new_scenario_bundle_authorized"] is False
    assert manifest["new_stochastic_seed_authorized"] is False
    assert manifest["new_solver_case_authorized"] is False
    assert manifest["new_experiment_authorized"] is False
    assert manifest["R6_plan_preparation_authorized"] is False
    assert manifest["R6_execution_authorized"] is False
    assert manifest["R5_followup_expansion_authorized"] is False
    assert manifest["context_route_promotion_authorized"] is False
    assert manifest["main_660_redefinition_authorized"] is False
    assert manifest["calibrated_event_probability_claim_emitted"] is False
    assert manifest["absolute_LOD_or_true_concentration_claim_emitted"] is False
    assert manifest["biological_specificity_claim_emitted"] is False
    assert manifest["selected_annulus_replaces_all_crossing_ranking"] is False
    assert manifest["thermal_sidecar_used_to_increase_NODI_score"] is False
    assert manifest["finite_zero_event_blank_safety_claim_emitted"] is False


def test_R5_2_headers_do_not_emit_legacy_SNR_output_names():
    for path in R5_2_DIR.glob("*.csv"):
        headers = _csv_headers(path)
        assert "detector_SNR" not in headers
        assert "calibrated_detector_SNR" not in headers
