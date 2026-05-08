from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def r3b_output(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("r3b_uncertainty")
    rv2.run_uncertainty_R3b(output, write_root_manifest=False)
    return output


def test_R3b_cost_cap_blocks_over_cap_execution():
    cost = rv2.estimate_uncertainty_R3b_cost(n_prior_samples=rv2.MAX_R3B_PRIOR_SAMPLES + 1)

    assert cost["under_R3b_review_cap"] is False
    assert cost["case_row_count"] > rv2.MAX_R3B_CASE_ROWS_BEFORE_REVIEW


def test_R3b_outputs_required_files_and_cap(r3b_output: Path):
    for name in (
        "uncertainty_expansion_summary.csv",
        "route_role_stability_summary.csv",
        "context_route_robustness_summary.csv",
        "main_660_stability_summary.csv",
        "optional_660_governance_summary.csv",
        "scenario_factor_sensitivity.csv",
        "route_sensitive_prior_diagnostics.csv",
        "global_multiplier_dominance_check.csv",
        "uncertainty_band_overlap_matrix.csv",
        "scenario_SNR_spread_by_route_family.csv",
        "thermal_404_uncertainty_gate_summary.csv",
        "detector_connection_state_machine_summary.csv",
        "blank_rare_tail_check.csv",
        "unit_guardrail_summary.csv",
        "uncertainty_cost_estimate.csv",
        "run_manifest.json",
        "R3b_uncertainty_expansion_report.md",
    ):
        assert (r3b_output / name).exists(), name

    rows = _read_csv(r3b_output / "uncertainty_expansion_summary.csv")
    cost = _read_csv(r3b_output / "uncertainty_cost_estimate.csv")[0]

    assert len(rows) == rv2.MAX_R3B_CASE_ROWS_BEFORE_REVIEW
    assert int(cost["case_row_count"]) == rv2.MAX_R3B_CASE_ROWS_BEFORE_REVIEW
    assert cost["under_R3b_review_cap"] == "True"


def test_R3b_manifest_marks_only_R3b_true_and_keeps_R4_R5_false(r3b_output: Path):
    manifest = json.loads((r3b_output / "run_manifest.json").read_text(encoding="utf-8"))

    assert manifest["R2_anchor_smoke_run"] is True
    assert manifest["R3_reduced_grid_run"] is True
    assert manifest["R3a_reduced_grid_named_bundle_survey_run"] is True
    assert manifest["R3b_uncertainty_expansion_run"] is True
    assert manifest["R4_representative_full_wave_validation_run"] is False
    assert manifest["R5_full_grid_v2_run"] is False
    assert manifest["event_budget"]["case_rows"] == rv2.MAX_R3B_CASE_ROWS_BEFORE_REVIEW
    assert manifest["scenario_budget"]["under_R3b_review_cap"] is True
    assert manifest["scenario_budget"]["context_route_promotion_authorized"] is False
    assert manifest["v1_full_grid_overwritten"] is False
    assert manifest["Tsuyama_paper_fit_continued"] is False
    assert manifest["selected_annulus_bounds_changed"] is False
    assert manifest["calibrated_SNR_claim_emitted"] is False
    assert manifest["ET2030_direct_current_input_unlocked"] is False


def test_R3b_output_guardrails_and_claim_boundaries(r3b_output: Path):
    rows = _read_csv(r3b_output / "uncertainty_expansion_summary.csv")

    assert rows
    assert all(row["SNR_claim_level"] == "absolute_blocked" for row in rows)
    assert all(row["event_probability_claim_level"] == "absolute_blocked" for row in rows)
    assert all(row["p_detect_mapping_claim_level"] == "relative_with_priors" for row in rows)
    assert all(row["primary_metric"] == "detectability_relative_prior_score" for row in rows)
    assert all(
        row["p_detect_scenario_interpretation"]
        == "legacy_named_relative_prior_score_not_event_probability"
        for row in rows
    )
    assert all(row["route_role_locked"] == "True" for row in rows)
    assert all(row["route_role_source"] == rv2.R3B_ROUTE_ROLE_SOURCE for row in rows)
    assert all(row["context_route_promotion_authorized"] == "False" for row in rows)
    assert all(row["R3b_uncertainty_expansion_run"] == "True" for row in rows)
    assert all(row["R4_representative_full_wave_validation_run"] == "False" for row in rows)
    assert all(row["R5_full_grid_v2_run"] == "False" for row in rows)
    assert all("detector_SNR" not in row for row in rows)
    assert all("calibrated_detector_SNR" not in row for row in rows)


def test_R3b_outputs_have_required_v2_provenance(r3b_output: Path):
    rows = _read_csv(r3b_output / "uncertainty_expansion_summary.csv")

    for row in rows[:100]:
        rv2.validate_required_output_fields(row)
        assert row["scenario_id"] in row["scenario_identity"]
        assert row["scenario_id"] not in row["base_route_key"]
        assert row["claim_level"] == "absolute_blocked"
        assert row["module_status"] == "bounded_prior"


def test_R3b_route_sensitive_diagnostics_are_not_global_scalar_dominated(
    r3b_output: Path,
):
    diagnostics = _read_csv(r3b_output / "route_sensitive_prior_diagnostics.csv")
    global_rows = _read_csv(r3b_output / "global_multiplier_dominance_check.csv")

    assert {row["factor_group"] for row in diagnostics} == set(rv2.R3B_REQUIRED_FACTOR_GROUPS)
    assert all(
        row["effect_delta_convention"] == rv2.R3B_EFFECT_DELTA_CONVENTION
        for row in diagnostics
    )
    assert all(float(row["route_sensitive_index"]) >= 0.25 for row in diagnostics)
    assert global_rows[0]["route_sensitive_prior_status"] == "route_sensitive"
    assert global_rows[0]["global_scalar_dominated_stop_gate"] == "False"
    assert float(global_rows[0]["global_multiplier_dominance_index"]) <= 0.8


def test_R3b_context_and_optional_routes_are_not_promoted(r3b_output: Path):
    context = _read_csv(r3b_output / "context_route_robustness_summary.csv")
    optional = _read_csv(r3b_output / "optional_660_governance_summary.csv")
    main = _read_csv(r3b_output / "main_660_stability_summary.csv")

    assert context
    assert optional
    assert main
    assert any(
        row["wavelength_nm"] == "532"
        and row["width_nm"] == "800"
        and row["depth_nm"] == "1500"
        for row in context
    )
    assert all(row["eligible_for_route_promotion"] == "False" for row in context)
    assert all(
        row["optional_660_900x1400_eligible_for_main_660_redefinition"] == "False"
        for row in optional
    )
    assert all(row["main_660_role_locked"] == "True" for row in main)


def test_R3b_uncertainty_band_overlap_matrix_is_reported(r3b_output: Path):
    rows = _read_csv(r3b_output / "uncertainty_band_overlap_matrix.csv")

    assert rows
    assert len(rows) == rv2.MAX_R3B_ROUTES * rv2.MAX_R3B_ROUTES
    assert any(row["bands_overlap"] == "True" for row in rows)
    assert any(row["left_route_id"] != row["right_route_id"] for row in rows)


def test_R3b_detector_blank_and_thermal_guards_remain_intact(r3b_output: Path):
    state_rows = _read_csv(r3b_output / "detector_connection_state_machine_summary.csv")
    blank_rows = _read_csv(r3b_output / "blank_rare_tail_check.csv")
    thermal_rows = _read_csv(r3b_output / "thermal_404_uncertainty_gate_summary.csv")

    assert any(
        row["connection_state_id"] == "ET2030_BNC_direct_to_LI5640_current_input"
        and row["connection_physical_validity"] == "forbidden"
        for row in state_rows
    )
    assert all(
        row["finite_monte_carlo_zero_event_inferred"] == "False" for row in blank_rows
    )
    assert all(
        row["false_positive_per_min_claim"] == "analytic_prior_only"
        for row in blank_rows
    )
    assert all(
        row["thermal_sidecar_does_not_increase_nodi_score"] == "True"
        for row in thermal_rows
    )
    assert all(float(row["max_thermal_404_log_multiplier"]) <= 0.0 for row in thermal_rows)
