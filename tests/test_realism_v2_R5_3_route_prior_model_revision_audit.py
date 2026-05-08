from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


R5_3_DIR = rv2.DEFAULT_R5_3_ROUTE_PRIOR_MODEL_REVISION_AUDIT_DIR


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_R5_3_audit_requires_exact_external_authorization(tmp_path):
    with pytest.raises(ValueError, match="exact external authorization"):
        rv2.run_R5_3_route_prior_model_revision_audit(
            output_dir=tmp_path,
            external_authorization="PASS_R5_3_PLAN_ONLY",
            write_root_manifest=False,
        )


def test_R5_3_outputs_required_files_only_and_respect_cap():
    assert R5_3_DIR.exists()
    files = {p.name for p in R5_3_DIR.iterdir() if p.is_file()}
    assert files == rv2.R5_3_REQUIRED_OUTPUTS_IF_AUTHORIZED

    manifest = _csv_rows(R5_3_DIR / "R5_3_route_prior_revision_manifest.csv")[0]
    assert manifest["R5_3_route_prior_model_revision_audit_run"] == "True"
    assert manifest["audit_execution_type"] == (
        "bounded_existing_R5_artifact_prior_model_audit_only"
    )
    assert int(manifest["existing_R5_rows_audited"]) == 14784
    assert int(manifest["audit_route_id_count"]) == 33
    assert int(manifest["scenario_bundle_count"]) == 8
    assert int(manifest["stochastic_seed_count"]) == 0
    assert int(manifest["new_case_rows_added"]) == 0


def test_R5_3_score_decomposition_is_exact_existing_R5_scope():
    rows = _csv_rows(R5_3_DIR / "R5_3_score_term_decomposition.csv")
    assert len(rows) == rv2.R5_3_ROUTE_PRIOR_SOURCE_ROW_CAP
    assert {row["route_id"] for row in rows} == rv2.R5_2_AUDIT_ROUTE_IDS
    assert {row["scenario_bundle"] for row in rows} == (
        rv2.R5_REQUIRED_SCENARIO_BUNDLE_IDS
    )
    assert len({row["particle_name"] for row in rows}) == (
        rv2.R5_V1_SOURCE_PARTICLE_NAME_COUNT
    )
    assert {row["claim_level"] for row in rows} == {"relative_with_priors"}
    assert {
        "reference_prior_term",
        "BFP_slit_pinhole_prior_term",
        "near_wall_PEG_transport_prior_term",
        "detector_blank_prior_term",
        "thermal_404_sidecar_exclusion_term",
        "route_width_depth_prior_term",
        "particle_size_stratum_term",
        "scenario_bundle_sensitivity_term",
    }.issubset(rows[0])
    assert {row["selected_candidate_prior_id"] for row in rows} == {
        "global_width_quadratic_regularization"
    }


def test_R5_3_selected_candidate_is_family_level_and_explains_warning():
    candidates = _csv_rows(R5_3_DIR / "R5_3_candidate_prior_revision_registry.csv")
    selected = [
        row for row in candidates if row["selected_candidate_for_future_review"] == "True"
    ]
    assert len(candidates) == 8
    assert len(selected) == 1
    candidate = selected[0]
    assert candidate["candidate_prior_id"] == "global_width_quadratic_regularization"
    assert candidate["candidate_prior_family"] == (
        "global_width_depth_regularization_family"
    )
    assert candidate["dof_count"] == "1"
    assert candidate["allowed_by_R5_3_plan"] == "True"
    assert candidate["uses_route_specific_multiplier"] == "False"
    assert candidate["uses_scenario_specific_per_route_fit"] == "False"
    assert candidate["uses_particle_specific_empirical_fit"] == "False"
    assert candidate["authorizes_route_promotion"] == "False"
    assert candidate["changes_main_660_definition"] == "False"
    assert candidate["warning_resolved_by_allowed_family_terms"] == "True"
    assert float(candidate["weak_reference_delta_explained_fraction"]) >= 0.7
    assert float(candidate["context_family_delta_explained_fraction"]) >= 0.7


def test_R5_3_context_and_weak_reference_warnings_are_exhaustively_reported():
    context = _csv_rows(R5_3_DIR / "R5_3_context_route_prior_driver_table.csv")
    weak = _csv_rows(R5_3_DIR / "R5_3_weak_reference_control_prior_driver_table.csv")[0]
    assert len(context) == len(rv2.R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS)
    assert {row["route_id"] for row in context} == rv2.R5_2_ABOVE_MAIN_CONTEXT_ROUTE_IDS
    assert all(row["route_promotion_authorized"] == "False" for row in context)
    assert all(row["main_660_redefinition_authorized"] == "False" for row in context)
    assert all(
        row["interpretation"]
        == "context_warning_explained_by_family_level_width_depth_prior"
        for row in context
    )
    assert all(float(row["fraction_of_warning_delta_explained"]) >= 0.7 for row in context)

    assert weak["route_id"] == "660_700x1500"
    assert weak["route_promotion_authorized"] == "False"
    assert weak["R6_plan_preparation_authorized"] == "False"
    assert float(weak["fraction_of_warning_delta_explained"]) >= 0.7


def test_R5_3_forbidden_fits_and_sidecars_are_fail_closed():
    forbidden = _csv_rows(R5_3_DIR / "R5_3_forbidden_fit_guardrail_summary.csv")
    sidecars = _csv_rows(
        R5_3_DIR / "R5_3_selected_annulus_and_404_sidecar_guardrail_summary.csv"
    )
    assert {row["forbidden_prior_family"] for row in forbidden} == (
        rv2.R5_3_FORBIDDEN_PRIOR_FAMILIES
    )
    assert all(row["attempted"] == "False" for row in forbidden)
    assert all(row["status"] == "pass" for row in forbidden)
    assert all(
        row["selected_annulus_replaces_all_crossing_ranking"] == "False"
        for row in sidecars
    )
    assert all(row["selected_annulus_bound_change_authorized"] == "False" for row in sidecars)
    assert all(row["thermal_sidecar_used_to_increase_NODI_score"] == "False" for row in sidecars)


def test_R5_3_decision_recommends_R6_plan_review_only_without_authorizing_it():
    decisions = _csv_rows(R5_3_DIR / "R5_3_route_prior_revision_decision_table.csv")
    matrix = _csv_rows(R5_3_DIR / "R5_3_next_stage_recommendation_matrix.csv")
    selected = [
        row for row in matrix if row["R5_3_recommendation"] == "selected_for_future_review"
    ]
    assert len(selected) == 1
    assert selected[0]["future_recommendation_class"] == (
        "prepare_R6_plan_for_external_review_only"
    )
    assert selected[0]["authorizes_execution"] == "False"
    assert selected[0]["authorizes_R6_plan"] == "False"
    assert selected[0]["authorizes_route_promotion"] == "False"

    assert {row["recommended_next_class"] for row in decisions} == {
        "prepare_R6_plan_for_external_review_only"
    }
    assert all(row["R6_plan_preparation_authorized"] == "False" for row in decisions)
    assert all(row["route_promotion_authorized"] == "False" for row in decisions)
    assert all(row["main_660_redefinition_authorized"] == "False" for row in decisions)


def test_R5_3_claim_boundaries_and_manifest_are_closed():
    claims = _csv_rows(R5_3_DIR / "R5_3_claim_boundary_guardrail_summary.csv")
    claim_status = {row["guardrail"]: row for row in claims}
    manifest = json.loads((R5_3_DIR / "run_manifest.json").read_text(encoding="utf-8"))

    assert claim_status["SNR_claim_level"]["value"] == "absolute_blocked"
    assert claim_status["event_probability_claim_level"]["value"] == "absolute_blocked"
    assert claim_status["p_detect_mapping_claim_level"]["value"] == "relative_with_priors"
    assert claim_status["legacy_detector_SNR_output_header_emitted"]["value"] == "False"
    assert claim_status["legacy_calibrated_detector_SNR_output_header_emitted"][
        "value"
    ] == "False"
    assert all(row["status"] == "pass" for row in claims)

    assert manifest["run_id"] == "EV_NODI_realism_v2_R5_3_route_prior_model_revision_audit"
    assert manifest["R5_3_route_prior_model_revision_audit_run"] is True
    assert manifest["R5_3_selected_candidate_prior_id"] == (
        "global_width_quadratic_regularization"
    )
    assert manifest["R6_plan_preparation_authorized"] is False
    assert manifest["R6_execution_authorized"] is False
    assert manifest["R5_followup_expansion_authorized"] is False
    assert manifest["context_route_promotion_authorized"] is False
    assert manifest["main_660_redefinition_authorized"] is False
    assert manifest["route_specific_manual_prior_multipliers_authorized"] is False
    assert manifest["scenario_specific_per_route_fit_authorized"] is False
    assert manifest["particle_specific_empirical_fit_authorized"] is False
    assert manifest["calibrated_event_probability_claim_emitted"] is False
    assert manifest["absolute_LOD_or_true_concentration_claim_emitted"] is False


def test_R5_3_headers_do_not_emit_legacy_SNR_output_names():
    for path in R5_3_DIR.glob("*.csv"):
        with path.open(newline="", encoding="utf-8") as handle:
            header = next(csv.reader(handle))
        assert "detector_SNR" not in header
        assert "calibrated_detector_SNR" not in header
