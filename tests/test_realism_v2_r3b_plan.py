from __future__ import annotations

import json
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


def test_R3b_cost_cap_blocks_over_cap_uncertainty_design():
    cost = rv2.estimate_uncertainty_R3b_cost(n_routes=rv2.MAX_R3B_ROUTES + 1)

    assert cost["under_R3b_review_cap"] is False
    assert cost["case_row_count"] > rv2.MAX_R3B_CASE_ROWS_BEFORE_REVIEW


def test_R3b_prior_table_has_numeric_bounds_correlations_and_formulas():
    table = rv2.validate_uncertainty_R3b_prior_table()
    rows = table["factor_priors"]

    assert table["uncertainty_method"] == "latin_hypercube_named_groups"
    assert table["max_prior_samples"] == rv2.MAX_R3B_PRIOR_SAMPLES
    assert len(rows) == 24
    assert {row["factor_group"] for row in rows} == set(rv2.R3B_REQUIRED_FACTOR_GROUPS)
    for row in rows:
        assert row["unit"]
        assert row["correlation_group"]
        assert row["correlation_transform"] in rv2.R3B_ALLOWED_CORRELATION_TRANSFORMS
        assert row["route_sensitive_formula"] in rv2.R3B_ALLOWED_ROUTE_SENSITIVE_FORMULAS
        assert row["physical_rationale"]
        assert float(row["min"]) <= float(row["nominal"]) <= float(row["max"])
        if row["distribution"] == "log_uniform":
            assert float(row["min"]) > 0.0
        assert row["claim_level"] in rv2.CLAIM_LEVELS


def test_R3b_prior_table_requires_correlation_transform_for_grouped_factors():
    table = rv2.load_uncertainty_R3b_prior_table()
    rows = table["factor_priors"]
    group_counts: dict[str, int] = {}
    for row in rows:
        group_counts[row["correlation_group"]] = group_counts.get(row["correlation_group"], 0) + 1
    grouped_rows = [
        row for row in rows if group_counts[row["correlation_group"]] > 1
    ]
    broken = {
        **table,
        "factor_priors": [dict(row) for row in rows],
    }
    first_grouped_index = rows.index(grouped_rows[0])
    broken["factor_priors"][first_grouped_index].pop("correlation_transform")

    assert grouped_rows
    with pytest.raises(ValueError, match="missing fields"):
        rv2.validate_uncertainty_R3b_prior_table(broken)


def test_R3b_prior_correlation_transforms_are_physically_coherent():
    table = rv2.validate_uncertainty_R3b_prior_table()
    by_name = {row["factor_name"]: row["correlation_transform"] for row in table["factor_priors"]}

    assert by_name["peg_survival_factor"] == "inverse"
    assert by_name["near_wall_event_fraction"] == "direct"
    assert by_name["adsorption_loss_factor"] == "direct"
    assert by_name["independent_samples_per_s"] == "inverse"
    assert by_name["colored_noise_correlation_time_s"] == "direct"
    assert by_name["roi_shift_uv"] == "direct"
    assert by_name["slit_width_scale"] == "inverse"


def test_R3b_route_panel_includes_532_800x1500_and_respects_cap():
    routes = rv2.validate_uncertainty_R3b_route_panel()
    route_keys = {
        (row["wavelength_nm"], row["width_nm"], row["depth_nm"], row["route_role"])
        for row in routes
    }

    assert len(routes) == rv2.MAX_R3B_ROUTES == 19
    assert rv2.MAX_R3B_CASE_ROWS_BEFORE_REVIEW == 19 * 23 * 24 * 3
    assert (532, 800, 1500, "reduced_grid_context_route") in route_keys
    assert (660, 900, 1300, "reduced_grid_context_route") in route_keys


def test_R3b_context_routes_cannot_be_promoted_and_roles_remain_locked():
    routes = rv2.validate_uncertainty_R3b_route_panel()
    optional = [
        row
        for row in routes
        if row["wavelength_nm"] == 660
        and row["width_nm"] == 900
        and row["depth_nm"] == 1400
    ][0]
    contexts = [row for row in routes if row["route_role"] == "reduced_grid_context_route"]

    assert optional["route_role"] == "optional_robustness_probe"
    assert all(row["route_role_locked"] is True for row in routes)
    assert all(row["route_role_source"] == rv2.R3B_ROUTE_ROLE_SOURCE for row in routes)
    assert all(row["context_route_promotion_authorized"] is False for row in contexts)


def test_R3b_route_sensitive_formula_separates_global_scalar_from_route_effects():
    global_scalar = {
        "660_800x1400": 0.12,
        "660_800x1500": 0.12,
        "532_900x1500": 0.12,
        "404_600x1300": 0.12,
    }
    route_sensitive = {
        "660_800x1400": 0.02,
        "660_800x1500": 0.08,
        "532_900x1500": 0.22,
        "404_600x1300": -0.03,
    }

    assert rv2.route_sensitive_index(global_scalar) < 0.01
    assert rv2.global_multiplier_dominance_index(global_scalar) > 0.99
    assert rv2.route_sensitive_index(route_sensitive) >= 0.25
    assert rv2.global_multiplier_dominance_index(route_sensitive) <= 0.8


def test_R3b_effect_delta_uses_fixed_median_log_score_ratio_convention():
    nominal = {
        "660_800x1400": [0.10, 0.11, 0.12],
        "532_900x1500": [0.20, 0.20, 0.21],
    }
    with_effect = {
        "660_800x1400": [0.05, 0.055, 0.06],
        "532_900x1500": [0.30, 0.30, 0.315],
    }

    deltas = rv2.R3b_effect_delta_log_score_ratio(with_effect, nominal)

    assert rv2.R3B_EFFECT_DELTA_CONVENTION == (
        "median_log_score_ratio_over_particles_seeds_prior_samples"
    )
    assert deltas["660_800x1400"] == pytest.approx(-0.69314718055)
    assert deltas["532_900x1500"] == pytest.approx(0.40546510811)
    assert rv2.route_sensitive_index(deltas) > 0.9


def test_R3b_global_multiplier_dominance_blocks_progression():
    status = rv2.classify_R3b_route_sensitive_prior_status(
        {"BFP_slit_alignment": 0.02, "detector_readout": 0.04},
        global_multiplier_dominance=0.91,
    )
    passing = rv2.classify_R3b_route_sensitive_prior_status(
        {"BFP_slit_alignment": 0.31, "detector_readout": 0.18},
        global_multiplier_dominance=0.62,
    )

    assert status["route_sensitive_prior_status"] == "global_scalar_dominated"
    assert status["blocks_R3b_progression"] is True
    assert passing["route_sensitive_prior_status"] == "route_sensitive"
    assert passing["blocks_R3b_progression"] is False


def test_R3b_detectability_contract_is_not_event_probability():
    plan = rv2.validate_R3b_pre_run_plan()
    prior_table = plan["prior_table"]

    assert prior_table["claim_boundary"] == (
        "relative_with_priors_only_absolute_event_probability_blocked"
    )
    assert plan["R3b_execution_authorized"] is False
    assert plan["cost"]["under_R3b_review_cap"] is True


def test_R3b_manifest_plan_keeps_R4_R5_false_and_hardening_flags_false(tmp_path: Path):
    manifest = rv2.build_run_manifest(
        output_directory=tmp_path,
        event_budget={
            "stage": "R3b_plan_pre_run_validation_only",
            "case_rows": rv2.MAX_R3B_CASE_ROWS_BEFORE_REVIEW,
            "R3b_uncertainty_expansion_started": False,
        },
        scenario_budget={
            "max_R3b_routes": rv2.MAX_R3B_ROUTES,
            "max_R3b_prior_samples": rv2.MAX_R3B_PRIOR_SAMPLES,
            "R3b_execution_authorized": False,
        },
        run_id="EV_NODI_realism_v2_R3b_plan_pre_run_validation_only",
        R2_anchor_smoke_run=True,
        R3_reduced_grid_run=True,
        R3a_reduced_grid_named_bundle_survey_run=True,
        R3b_uncertainty_expansion_run=False,
        R4_representative_full_wave_validation_run=False,
        R5_full_grid_v2_run=False,
    )

    rv2.validate_run_manifest(manifest)
    assert manifest["R3b_uncertainty_expansion_run"] is False
    assert manifest["R4_representative_full_wave_validation_run"] is False
    assert manifest["R5_full_grid_v2_run"] is False
    assert manifest["v1_full_grid_overwritten"] is False
    assert manifest["Tsuyama_paper_fit_continued"] is False
    assert manifest["selected_annulus_bounds_changed"] is False
    assert manifest["calibrated_SNR_claim_emitted"] is False
    assert manifest["ET2030_direct_current_input_unlocked"] is False
    json.dumps(manifest)


def test_R3b_missing_prior_field_fails_closed():
    table = rv2.load_uncertainty_R3b_prior_table()
    broken = {
        **table,
        "factor_priors": [dict(row) for row in table["factor_priors"]],
    }
    broken["factor_priors"][0].pop("max")

    with pytest.raises(ValueError, match="missing fields"):
        rv2.validate_uncertainty_R3b_prior_table(broken)
