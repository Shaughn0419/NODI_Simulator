from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


R5_1_DIR = rv2.DEFAULT_R5_1_INTERPRETATION_DIR


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _csv_headers(path: Path) -> set[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return set(next(csv.reader(handle)))


def test_R5_1_interpretation_requires_exact_external_authorization(tmp_path):
    with pytest.raises(ValueError, match="exact external authorization"):
        rv2.run_R5_1_route_role_stability_interpretation(
            tmp_path,
            external_authorization="PASS_R5_1_PLAN_ONLY",
            write_root_manifest=False,
        )


def test_R5_1_outputs_required_files_only_and_use_no_new_compute():
    assert R5_1_DIR.exists()
    files = {p.name for p in R5_1_DIR.iterdir() if p.is_file() and not p.name.startswith("._")}

    assert files == rv2.R5_1_REQUIRED_OUTPUTS_IF_AUTHORIZED

    manifest_row = _csv_rows(
        R5_1_DIR / "R5_1_route_role_stability_interpretation_manifest.csv"
    )[0]
    assert manifest_row["external_authorization"] == (
        "PASS_TO_R5_1_ROUTE_ROLE_STABILITY_INTERPRETATION_ONLY"
    )
    assert manifest_row["R5_1_interpretation_run"] == "True"
    assert manifest_row["R5_case_rows_interpreted"] == "256256"
    assert manifest_row["new_case_rows_added"] == "0"
    assert manifest_row["new_scenario_bundles_added"] == "0"
    assert manifest_row["new_stochastic_seeds_added"] == "0"
    assert manifest_row["new_solver_cases_added"] == "0"
    assert manifest_row["new_experiments_started"] == "0"


def test_R5_1_decision_table_selects_bounded_prior_audit_without_R6_or_promotion():
    rows = _csv_rows(R5_1_DIR / "R5_1_route_role_stability_decision_table.csv")
    by_subject = {row["decision_subject"]: row for row in rows}

    assert set(by_subject) == {
        "main_660_locked_routes",
        "weak_reference_control",
        "context_route_high_score_warnings",
        "optional_660_900x1400",
    }
    for row in rows:
        assert row["recommended_next_class"] == (
            "prepare_bounded_additional_scenario_prior_audit_plan_only"
        )
        assert row["R6_plan_preparation_authorized"] == "False"
        assert row["route_promotion_authorized"] == "False"
        assert row["main_660_redefinition_authorized"] == "False"
        assert row["claim_level"] == "relative_with_priors"

    assert "exceeds main_660" in by_subject["weak_reference_control"]["evidence_summary"]
    assert "20 context routes exceed main_660" in by_subject[
        "context_route_high_score_warnings"
    ]["evidence_summary"]


def test_R5_1_context_and_weak_reference_outputs_are_warnings_only():
    context_rows = _csv_rows(R5_1_DIR / "R5_1_context_route_high_score_warning_table.csv")
    weak = _csv_rows(R5_1_DIR / "R5_1_weak_reference_control_interpretation.csv")[0]

    assert len(context_rows) == 10
    assert context_rows[0]["route_id"] == "660_500x1500"
    assert all(row["exceeds_main_660_mean"] == "True" for row in context_rows)
    assert all(row["context_route_promotion_authorized"] == "False" for row in context_rows)
    assert all(row["route_promotion_eligible"] == "False" for row in context_rows)
    assert weak["weak_reference_exceeds_main_660"] == "True"
    assert weak["route_promotion_authorized"] == "False"
    assert weak["R6_plan_preparation_authorized"] == "False"


def test_R5_1_main660_and_selected_annulus_governance_stay_locked():
    main_rows = _csv_rows(R5_1_DIR / "R5_1_main_660_robustness_interpretation.csv")
    selected_rows = _csv_rows(R5_1_DIR / "R5_1_selected_annulus_nonpromotion_summary.csv")

    assert {
        (int(row["wavelength_nm"]), int(row["width_nm"]), int(row["depth_nm"]))
        for row in main_rows
    } == rv2.R5_MAIN_660_LOCKED_ROUTES
    assert all(row["main_660_route_role_locked"] == "True" for row in main_rows)
    assert all(row["main_660_redefinition_authorized"] == "False" for row in main_rows)
    assert all(row["R6_plan_preparation_authorized"] == "False" for row in main_rows)

    assert selected_rows
    assert all(
        row["selected_annulus_boundary_policy"]
        == "unchanged_v1_0p5_0p8_parallel_lens_only"
        for row in selected_rows
    )
    assert all(
        row["selected_annulus_replaces_all_crossing_ranking"] == "False"
        for row in selected_rows
    )
    assert all(
        row["selected_annulus_bound_change_authorized"] == "False"
        for row in selected_rows
    )


def test_R5_1_claim_guardrails_and_manifest_are_fail_closed():
    guardrails = {
        row["guardrail"]: row
        for row in _csv_rows(R5_1_DIR / "R5_1_claim_boundary_guardrail_summary.csv")
    }
    manifest = json.loads((R5_1_DIR / "run_manifest.json").read_text(encoding="utf-8"))

    assert guardrails["SNR_claim_level"]["value"] == "absolute_blocked"
    assert guardrails["event_probability_claim_level"]["value"] == "absolute_blocked"
    assert guardrails["p_detect_mapping_claim_level"]["value"] == "relative_with_priors"
    assert guardrails["legacy_detector_SNR_output_header_emitted"]["status"] == "pass"
    assert guardrails["legacy_calibrated_detector_SNR_output_header_emitted"]["status"] == "pass"
    assert guardrails["thermal_sidecar_used_to_increase_NODI_score"]["status"] == "pass"

    assert manifest["R5_1_route_role_stability_interpretation_run"] is True
    assert manifest["R5_1_selected_future_recommendation_class"] == (
        "prepare_bounded_additional_scenario_prior_audit_plan_only"
    )
    assert manifest["new_case_rows_authorized"] == 0
    assert manifest["R6_plan_preparation_authorized"] is False
    assert manifest["R6_execution_authorized"] is False
    assert manifest["R5_followup_expansion_authorized"] is False
    assert manifest["context_route_promotion_authorized"] is False
    assert manifest["main_660_redefinition_authorized"] is False
    assert manifest["calibrated_SNR_claim_emitted"] is False
    assert manifest["calibrated_event_probability_claim_emitted"] is False
    assert manifest["absolute_LOD_or_true_concentration_claim_emitted"] is False
    assert manifest["biological_specificity_claim_emitted"] is False


def test_R5_1_headers_do_not_emit_legacy_SNR_output_names():
    for path in R5_1_DIR.glob("*.csv"):
        if path.name.startswith("._"):
            continue
        headers = _csv_headers(path)
        assert "detector_SNR" not in headers
        assert "calibrated_detector_SNR" not in headers


def test_R5_1_next_stage_options_are_recommendations_not_authorizations():
    rows = _csv_rows(R5_1_DIR / "R5_1_next_stage_options_matrix.csv")
    selected = [row for row in rows if row["R5_1_recommendation"] == "selected_for_future_review"]

    assert len(selected) == 1
    assert selected[0]["future_recommendation_class"] == (
        "prepare_bounded_additional_scenario_prior_audit_plan_only"
    )
    assert all(row["authorizes_execution"] == "False" for row in rows)
