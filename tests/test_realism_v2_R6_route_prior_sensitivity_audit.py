from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


R6_DIR = rv2.DEFAULT_R6_ROUTE_PRIOR_SENSITIVITY_AUDIT_DIR


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_R6_audit_requires_exact_external_authorization(tmp_path):
    with pytest.raises(ValueError, match="exact external authorization"):
        rv2.run_R6_route_prior_sensitivity_audit(
            output_dir=tmp_path,
            external_authorization="PASS_R6_PLAN_ONLY",
            write_root_manifest=False,
        )


def test_R6_outputs_required_files_only_and_respect_caps():
    assert R6_DIR.exists()
    files = {
        p.name
        for p in R6_DIR.iterdir()
        if p.is_file() and not p.name.startswith("._")
    }
    assert files == rv2.R6_REQUIRED_OUTPUTS_IF_AUTHORIZED

    manifest = _csv_rows(R6_DIR / "R6_route_prior_sensitivity_manifest.csv")[0]
    assert manifest["R6_route_prior_sensitivity_audit_run"] == "True"
    assert manifest["audit_execution_type"] == (
        "bounded_existing_R5_artifact_route_prior_sensitivity_audit_only"
    )
    assert int(manifest["existing_R5_rows_audited"]) == 14784
    assert int(manifest["candidate_prior_count"]) == 12
    assert int(manifest["derived_candidate_rows_evaluated"]) == 177408
    assert int(manifest["max_R6_derived_candidate_rows"]) == 177408
    assert int(manifest["audit_route_id_count"]) == 33
    assert int(manifest["scenario_bundle_count"]) == 8
    assert int(manifest["stochastic_seed_count"]) == 0
    assert int(manifest["new_case_rows_added"]) == 0
    assert manifest["main660_comparator_policy"] == (
        "candidate_adjusted_locked_main_660"
    )
    assert manifest["secondary_main660_comparator_policy"] == (
        "unadjusted_locked_main_660"
    )


def test_R6_sensitivity_matrix_is_exact_bounded_existing_R5_scope():
    rows = _csv_rows(R6_DIR / "R6_candidate_prior_sensitivity_matrix.csv")
    assert len(rows) == rv2.R6_DERIVED_CANDIDATE_ROW_CAP
    assert {row["candidate_prior_id"] for row in rows} == (
        rv2.R6_REQUIRED_CANDIDATE_PRIOR_IDS
    )
    assert {row["route_id"] for row in rows} == rv2.R5_2_AUDIT_ROUTE_IDS
    assert {row["scenario_bundle"] for row in rows} == (
        rv2.R5_REQUIRED_SCENARIO_BUNDLE_IDS
    )
    assert len({row["particle_name"] for row in rows}) == (
        rv2.R5_V1_SOURCE_PARTICLE_NAME_COUNT
    )
    assert {row["claim_level"] for row in rows} == {"relative_with_priors"}
    assert set(rows[0]).issuperset(rv2.R6_REQUIRED_SENSITIVITY_FIELDS)
    assert {row["changes_main_660_definition"] for row in rows} == {"False"}
    assert {row["authorizes_route_promotion"] for row in rows} == {"False"}
    assert {row["uses_route_specific_multiplier"] for row in rows} == {"False"}
    assert {row["uses_scenario_specific_per_route_fit"] for row in rows} == {"False"}
    assert {row["uses_particle_specific_empirical_fit"] for row in rows} == {"False"}


def test_R6_candidate_registry_shows_nearby_width_sensitivity_and_main_retention():
    rows = _csv_rows(R6_DIR / "R6_candidate_prior_registry.csv")
    by_id = {row["candidate_prior_id"]: row for row in rows}

    assert len(rows) == 12
    assert set(by_id) == rv2.R6_REQUIRED_CANDIDATE_PRIOR_IDS
    assert by_id["global_width_quadratic_regularization"][
        "nearby_width_family_confirmation_candidate"
    ] == "True"
    assert by_id["global_width_quadratic_regularization"][
        "warning_resolved_by_candidate"
    ] == "True"
    assert by_id["width_exp1p5_800"]["warning_resolved_by_candidate"] == "True"
    assert by_id["width_quad_850"]["warning_resolved_by_candidate"] == "True"
    assert by_id["width_linear_800"]["warning_resolved_by_candidate"] == "False"
    assert by_id["width_quad_750"]["warning_resolved_by_candidate"] == "False"
    assert by_id["width_quad_900"]["main660_retention_warning"] == "True"
    assert float(by_id["width_quad_900"]["main660_score_retention_fraction"]) < 0.85
    assert by_id["reference_band_penalty"]["warning_resolved_by_candidate"] == "False"
    assert by_id["BFP_alignment_risk"]["warning_resolved_by_candidate"] == "False"
    assert all(row["authorizes_route_promotion"] == "False" for row in rows)
    assert all(row["changes_main_660_definition"] == "False" for row in rows)


def test_R6_residual_dashboards_and_comparator_policy_are_explicit():
    route_factor_rows = _csv_rows(R6_DIR / "R6_route_prior_factor_by_route.csv")
    family_rows = _csv_rows(R6_DIR / "R6_route_family_residual_warning_table.csv")
    scenario_rows = _csv_rows(R6_DIR / "R6_scenario_residual_warning_table.csv")
    particle_rows = _csv_rows(R6_DIR / "R6_particle_stratum_residual_warning_table.csv")
    main_rows = _csv_rows(R6_DIR / "R6_main660_locked_comparator_summary.csv")

    assert len(route_factor_rows) == 12 * 33
    assert len(family_rows) == 12 * 6
    assert len(scenario_rows) == 12 * 8
    assert len(particle_rows) == 12 * 56
    assert len(main_rows) == 12 * 2

    optional = [
        row
        for row in route_factor_rows
        if row["candidate_prior_id"] == "width_quad_900"
        and row["route_id"] == "660_900x1400"
    ][0]
    assert "candidate_adjusted_delta_vs_main" in optional
    assert "unadjusted_main_delta" in optional

    main_900 = [
        row
        for row in main_rows
        if row["candidate_prior_id"] == "width_quad_900"
    ]
    assert len(main_900) == 2
    assert all(row["main660_retention_warning"] == "True" for row in main_900)
    assert all(row["main_660_redefinition_authorized"] == "False" for row in main_rows)
    assert all(row["route_promotion_authorized"] == "False" for row in main_rows)


def test_R6_decision_and_manifest_authorize_no_next_execution_or_promotion():
    manifest = _csv_rows(R6_DIR / "R6_route_prior_sensitivity_manifest.csv")[0]
    matrix = _csv_rows(R6_DIR / "R6_next_stage_recommendation_matrix.csv")
    selected = [
        row for row in matrix if row["R6_recommendation"] == "selected_for_future_review"
    ]
    run_manifest = json.loads((R6_DIR / "run_manifest.json").read_text(encoding="utf-8"))

    assert manifest["selected_future_recommendation_class"] == (
        "prepare_next_stage_plan_for_external_review_only"
    )
    assert manifest["audit_decision"] == (
        "low_dimensional_width_prior_sensitivity_stable_prepare_next_stage_plan_only"
    )
    assert manifest["at_least_two_nearby_low_dimensional_candidates_explain_warning"] == (
        "True"
    )
    assert int(manifest["nearby_warning_resolved_candidate_count"]) >= 2
    assert manifest["R7_plan_preparation_authorized"] == "False"
    assert manifest["R7_execution_authorized"] == "False"
    assert manifest["R5_followup_expansion_authorized"] == "False"
    assert manifest["context_route_promotion_authorized"] == "False"
    assert manifest["main_660_redefinition_authorized"] == "False"

    assert len(selected) == 1
    assert selected[0]["future_recommendation_class"] == (
        "prepare_next_stage_plan_for_external_review_only"
    )
    assert selected[0]["authorizes_execution"] == "False"
    assert selected[0]["authorizes_R7"] == "False"
    assert selected[0]["authorizes_route_promotion"] == "False"
    assert selected[0]["authorizes_main_660_redefinition"] == "False"

    assert run_manifest["run_id"] == "EV_NODI_realism_v2_R6_route_prior_sensitivity_audit"
    assert run_manifest["R6_route_prior_sensitivity_audit_run"] is True
    assert run_manifest["R7_plan_preparation_authorized"] is False
    assert run_manifest["R7_execution_authorized"] is False
    assert run_manifest["context_route_promotion_authorized"] is False
    assert run_manifest["main_660_redefinition_authorized"] is False
    assert run_manifest["calibrated_event_probability_claim_emitted"] is False
    assert run_manifest["absolute_LOD_or_true_concentration_claim_emitted"] is False


def test_R6_guardrail_summaries_and_headers_are_clean():
    claims = _csv_rows(R6_DIR / "R6_claim_boundary_guardrail_summary.csv")
    stops = _csv_rows(R6_DIR / "R6_stop_gate_summary.csv")
    sidecars = _csv_rows(R6_DIR / "R6_selected_annulus_and_404_sidecar_guardrail_summary.csv")

    claim_status = {row["guardrail"]: row for row in claims}
    assert claim_status["SNR_claim_level"]["value"] == "absolute_blocked"
    assert claim_status["event_probability_claim_level"]["value"] == "absolute_blocked"
    assert claim_status["p_detect_mapping_claim_level"]["value"] == "relative_with_priors"
    assert all(row["status"] == "pass" for row in claims)
    assert {row["triggered"] for row in stops} == {"False"}
    assert {row["status"] for row in stops} == {"pass"}
    assert all(
        row["selected_annulus_replaces_all_crossing_ranking"] == "False"
        for row in sidecars
    )
    assert all(row["thermal_sidecar_used_to_increase_NODI_score"] == "False" for row in sidecars)

    for path in R6_DIR.glob("*.csv"):
        if path.name.startswith("._"):
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            header = next(csv.reader(handle))
        assert "detector_SNR" not in header
        assert "calibrated_detector_SNR" not in header
