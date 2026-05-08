from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


R7_DIR = rv2.DEFAULT_R7_ROUTE_PRIOR_MECHANISTIC_DECOMPOSITION_DIR


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_R7_audit_requires_exact_external_authorization(tmp_path):
    with pytest.raises(ValueError, match="exact external authorization"):
        rv2.run_R7_route_prior_mechanistic_decomposition_audit(
            output_dir=tmp_path,
            external_authorization="PASS_R7_PLAN_ONLY",
            write_root_manifest=False,
        )


def test_R7_outputs_required_files_only_and_respect_caps():
    assert R7_DIR.exists()
    files = {
        p.name
        for p in R7_DIR.iterdir()
        if p.is_file() and not p.name.startswith("._")
    }
    assert files == rv2.R7_REQUIRED_OUTPUTS_IF_AUTHORIZED

    manifest = _csv_rows(R7_DIR / "R7_mechanistic_decomposition_manifest.csv")[0]
    assert manifest["R7_route_prior_mechanistic_decomposition_audit_run"] == "True"
    assert manifest["audit_execution_type"] == (
        "bounded_existing_R5_artifact_route_prior_mechanistic_decomposition_audit_only"
    )
    assert int(manifest["existing_R5_rows_interpreted"]) == 14784
    assert int(manifest["mechanistic_candidate_count"]) == 6
    assert int(manifest["max_mechanistic_candidate_count"]) == 12
    assert int(manifest["derived_mechanistic_candidate_rows_evaluated"]) == 0
    assert int(manifest["max_R7_derived_candidate_rows"]) == 177408
    assert int(manifest["audit_route_id_count"]) == 33
    assert int(manifest["scenario_bundle_count"]) == 8
    assert int(manifest["stochastic_seed_count"]) == 0
    assert int(manifest["new_case_rows_added"]) == 0
    assert int(manifest["new_solver_cases_added"]) == 0
    assert int(manifest["new_experiments_started"]) == 0


def test_R7_registry_and_factor_schema_are_mechanistic_not_score_fit():
    registry = _csv_rows(R7_DIR / "R7_candidate_mechanistic_prior_registry.csv")
    factor_schema = _csv_rows(R7_DIR / "R7_mechanistic_prior_factor_schema.csv")

    assert len(registry) == 6
    assert {row["candidate_prior_family"] for row in registry} == (
        rv2.R7_ALLOWED_MECHANISTIC_PRIOR_FAMILIES
    )
    assert all(row["uses_route_specific_multiplier"] == "False" for row in registry)
    assert all(row["uses_scenario_specific_per_route_fit"] == "False" for row in registry)
    assert all(row["uses_particle_specific_empirical_fit"] == "False" for row in registry)
    assert all(
        row["uses_source_v1_relative_score_as_physical_input"] == "False"
        for row in registry
    )
    assert all(row["changes_main_660_definition"] == "False" for row in registry)
    assert all(row["authorizes_route_promotion"] == "False" for row in registry)
    assert all(
        row["uses_source_v1_relative_score_as_physical_input"] == "False"
        for row in factor_schema
    )
    executable = [
        row
        for row in registry
        if row["candidate_can_be_executed_without_new_artifact"] == "True"
    ]
    gaps = [
        row
        for row in registry
        if row["candidate_can_be_executed_without_new_artifact"] == "False"
    ]
    assert len(executable) >= 2
    assert len(gaps) >= 2


def test_R7_accepted_band_and_width_900_caution_are_preserved():
    band = _csv_rows(R7_DIR / "R7_accepted_width_prior_band_summary.csv")
    caution = _csv_rows(R7_DIR / "R7_width_quad_900_over_severe_caution_summary.csv")[0]
    by_id = {row["candidate_prior_id"]: row for row in band}

    assert set(by_id) == {
        "width_exp1p5_800",
        "global_width_quadratic_regularization",
        "width_quad_850",
    }
    assert by_id["width_exp1p5_800"]["candidate_interpretation_class"] == (
        "accepted_explanatory"
    )
    assert by_id["width_quad_850"]["candidate_interpretation_class"] == (
        "accepted_but_caution"
    )
    assert all(
        float(row["main660_score_retention_fraction"]) >= 0.85 for row in band
    )
    assert all(row["route_promotion_authorized"] == "False" for row in band)
    assert all(row["main_660_redefinition_authorized"] == "False" for row in band)

    assert caution["candidate_prior_id"] == "width_quad_900"
    assert caution["candidate_interpretation_class"] == "over_severe_prior_caution"
    assert caution["warning_resolved_by_candidate"] == "True"
    assert caution["main660_retention_warning"] == "True"
    assert float(caution["main660_score_retention_fraction"]) < 0.85
    assert caution["accepted_width_prior_band_member"] == "False"
    assert caution["route_promotion_authorized"] == "False"
    assert caution["main_660_redefinition_authorized"] == "False"


def test_R7_particle_residual_outputs_are_warning_only():
    top = _csv_rows(R7_DIR / "R7_particle_stratum_residual_top_routes.csv")
    by_family = _csv_rows(R7_DIR / "R7_particle_stratum_residual_by_family.csv")
    comparison = _csv_rows(R7_DIR / "R7_gold_anchor_vs_EV_residual_comparison.csv")

    assert top
    assert by_family
    assert {row["comparison_group"] for row in comparison} == {"gold_anchor", "EV_like"}
    assert all(row["particle_specific_empirical_fit_authorized"] == "False" for row in top)
    assert all(
        row["particle_specific_empirical_fit_authorized"] == "False"
        for row in by_family
    )
    assert all(
        row["interpretation"] == "particle_stratum_residual_warning_not_fit_target"
        for row in top
    )
    assert max(int(row["residual_above_main_row_count"]) for row in top) > 0


def test_R7_optional_900_and_non_width_policies_stay_non_promoting():
    optional = _csv_rows(R7_DIR / "R7_optional_900_governance_diagnostic.csv")
    non_width = _csv_rows(R7_DIR / "R7_non_width_prior_input_requirement_summary.csv")

    assert {row["route_id"] for row in optional} == {"660_900x1400"}
    assert {row["optional_900_role_after_prior"] for row in optional} == {
        "optional_robustness_probe"
    }
    assert all(row["main_660_redefinition_authorized"] == "False" for row in optional)
    assert all(row["route_promotion_authorized"] == "False" for row in optional)
    width_900 = [row for row in optional if row["candidate_prior_id"] == "width_quad_900"][0]
    assert width_900["optional_900_positive_vs_candidate_adjusted_main"] == "True"

    by_id = {row["candidate_prior_id"]: row for row in non_width}
    assert set(by_id) == {"reference_band_penalty", "BFP_alignment_risk"}
    assert by_id["reference_band_penalty"][
        "source_v1_relative_score_as_physical_prior_authorized"
    ] == "False"
    assert by_id["reference_band_penalty"]["R6_warning_resolved_by_candidate"] == "False"
    assert by_id["BFP_alignment_risk"]["R6_warning_resolved_by_candidate"] == "False"
    assert all(row["requires_physical_operator_columns"] == "True" for row in non_width)


def test_R7_recommendation_and_manifest_authorize_no_execution_or_promotion():
    manifest = _csv_rows(R7_DIR / "R7_mechanistic_decomposition_manifest.csv")[0]
    matrix = _csv_rows(R7_DIR / "R7_next_stage_recommendation_matrix.csv")
    selected = [
        row for row in matrix if row["R7_recommendation"] == "selected_for_future_review"
    ]
    run_manifest = json.loads((R7_DIR / "run_manifest.json").read_text(encoding="utf-8"))

    assert manifest["selected_future_recommendation_class"] == (
        "prepare_operator_artifact_gap_register_plan_only"
    )
    assert manifest["audit_decision"] == (
        "mechanistic_width_prior_supported_prepare_artifact_gap_register_only"
    )
    assert manifest["R8_plan_preparation_authorized"] == "False"
    assert manifest["R8_execution_authorized"] == "False"
    assert manifest["new_experiment_authorized"] == "False"
    assert manifest["context_route_promotion_authorized"] == "False"
    assert manifest["main_660_redefinition_authorized"] == "False"
    assert manifest["score_derived_physical_prior_attempted"] == "False"

    assert len(selected) == 1
    assert selected[0]["future_recommendation_class"] == (
        "prepare_operator_artifact_gap_register_plan_only"
    )
    assert selected[0]["authorizes_execution"] == "False"
    assert selected[0]["authorizes_R8"] == "False"
    assert selected[0]["authorizes_experiment"] == "False"
    assert selected[0]["authorizes_route_promotion"] == "False"
    assert selected[0]["authorizes_main_660_redefinition"] == "False"

    assert run_manifest["run_id"] == (
        "EV_NODI_realism_v2_R7_route_prior_mechanistic_decomposition_audit"
    )
    assert run_manifest["R7_route_prior_mechanistic_decomposition_audit_run"] is True
    assert run_manifest["R8_plan_preparation_authorized"] is False
    assert run_manifest["R8_execution_authorized"] is False
    assert run_manifest["new_experiment_authorized"] is False
    assert run_manifest["context_route_promotion_authorized"] is False
    assert run_manifest["main_660_redefinition_authorized"] is False


def test_R7_guardrails_and_headers_are_clean():
    claims = _csv_rows(R7_DIR / "R7_claim_boundary_guardrail_summary.csv")
    stops = _csv_rows(R7_DIR / "R7_stop_gate_summary.csv")

    claim_status = {row["guardrail"]: row for row in claims}
    assert claim_status["SNR_claim_level"]["value"] == "absolute_blocked"
    assert claim_status["event_probability_claim_level"]["value"] == "absolute_blocked"
    assert claim_status["p_detect_mapping_claim_level"]["value"] == "relative_with_priors"
    assert all(row["status"] == "pass" for row in claims)
    assert {row["triggered"] for row in stops} == {"False"}
    assert {row["status"] for row in stops} == {"pass"}

    for path in R7_DIR.glob("*.csv"):
        if path.name.startswith("._"):
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            header = next(csv.reader(handle))
        assert "detector_SNR" not in header
        assert "calibrated_detector_SNR" not in header
