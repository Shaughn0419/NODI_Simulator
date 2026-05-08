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
def r4_output(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("r4_representative_full_wave")
    rv2.run_representative_full_wave_R4(output, write_root_manifest=False)
    return output


def test_R4_execution_requires_exact_external_authorization(tmp_path: Path):
    with pytest.raises(ValueError, match="external authorization"):
        rv2.run_representative_full_wave_R4(
            tmp_path,
            external_authorization="PASS_R3B_RESULTS_PREPARE_R4_PLAN_ONLY",
            write_root_manifest=False,
        )


def test_R4_outputs_required_files_only_and_respect_cap(r4_output: Path):
    produced = {path.name for path in r4_output.iterdir() if path.is_file()}

    assert produced == rv2.R4_REQUIRED_OUTPUTS_IF_EXECUTED

    case_rows = _read_csv(r4_output / "full_wave_case_manifest.csv")
    cost = _read_csv(r4_output / "full_wave_cost_estimate.csv")[0]

    assert len(case_rows) == rv2.MAX_R4_SOLVER_CASES_BEFORE_REVIEW
    assert int(cost["actual_case_rows"]) == rv2.MAX_R4_SOLVER_CASES_BEFORE_REVIEW
    assert cost["under_R4_review_cap"] == "True"
    assert int(cost["solver_case_count"]) == rv2.MAX_R4_SOLVER_CASES_BEFORE_REVIEW


def test_R4_case_panel_matches_authorized_contract(r4_output: Path):
    rows = _read_csv(r4_output / "full_wave_case_manifest.csv")

    routes = {
        (row["wavelength_nm"], row["width_nm"], row["depth_nm"]) for row in rows
    }
    particles = {row["particle_id"] for row in rows}
    interface_states = {row["interface_state"] for row in rows}
    polarization_states = {row["polarization_state"] for row in rows}
    mesh_levels = {row["mesh_level"] for row in rows}

    assert len(routes) == rv2.MAX_R4_REPRESENTATIVE_ROUTES
    assert particles == rv2.R4_REQUIRED_PARTICLES
    assert interface_states == {"centerline_nominal", "near_wall_stress"}
    assert polarization_states == {"nominal_linear", "orthogonal_sensitivity"}
    assert mesh_levels == {"coarse_screen", "review_refined"}
    assert all(row["route_role_locked"] == "True" for row in rows)
    assert all(row["route_role_source"] == rv2.R4_ROUTE_ROLE_SOURCE for row in rows)
    assert all(row["context_route_promotion_authorized"] == "False" for row in rows)
    assert all(row["biological_specificity_claim_allowed"] == "False" for row in rows)


def test_R4_observables_preserve_signed_terms_and_claim_boundaries(r4_output: Path):
    rows = _read_csv(r4_output / "full_wave_observable_summary.csv")

    assert rows
    for name in (
        "full_wave_cross_term_signed_W",
        "surrogate_cross_term_signed_W",
        "full_wave_ROI_signal_signed_W",
        "full_wave_ROI_signal_abs_W",
        "surrogate_ROI_signal_signed_W",
        "surrogate_ROI_signal_abs_W",
        "surrogate_delta_log",
        "sign_preserved",
    ):
        assert name in rows[0]

    assert all(row["SNR_claim_level"] == "absolute_blocked" for row in rows)
    assert all(row["event_probability_claim_level"] == "absolute_blocked" for row in rows)
    assert all(row["p_detect_mapping_claim_level"] == "relative_with_priors" for row in rows)
    assert all(row["route_promotion_eligible"] == "False" for row in rows)
    assert all(row["solver_case_completed"] == "True" for row in rows)
    assert all(row["full_wave_value_source"] == "channel_modal_green_numerical_solver_output" for row in rows)
    assert all(
        row["proxy_only_values_excluded_from_route_decision"] == "True" for row in rows
    )
    assert all("detector_SNR" not in row for row in rows)
    assert all("calibrated_detector_SNR" not in row for row in rows)


def test_R4_outputs_have_required_v2_provenance(r4_output: Path):
    rows = _read_csv(r4_output / "full_wave_observable_summary.csv")

    for row in rows[:50]:
        rv2.validate_required_output_fields(row)
        assert row["scenario_id"] in row["scenario_identity"]
        assert row["scenario_id"] not in row["base_route_key"]
        assert row["claim_level"] == "relative_with_priors"
        assert row["module_status"] == "bounded_prior"


def test_R4_manifest_marks_R4_true_and_keeps_forbidden_stages_false(r4_output: Path):
    manifest = json.loads((r4_output / "run_manifest.json").read_text(encoding="utf-8"))

    assert manifest["R2_anchor_smoke_run"] is True
    assert manifest["R3_reduced_grid_run"] is True
    assert manifest["R3a_reduced_grid_named_bundle_survey_run"] is True
    assert manifest["R3b_uncertainty_expansion_run"] is True
    assert manifest["R4_representative_full_wave_validation_run"] is True
    assert manifest["R5_full_grid_v2_run"] is False
    assert manifest["event_budget"]["solver_case_rows"] == rv2.MAX_R4_SOLVER_CASES_BEFORE_REVIEW
    assert manifest["scenario_budget"]["context_route_promotion_authorized"] is False
    assert manifest["v1_full_grid_overwritten"] is False
    assert manifest["Tsuyama_paper_fit_continued"] is False
    assert manifest["selected_annulus_bounds_changed"] is False
    assert manifest["calibrated_SNR_claim_emitted"] is False
    assert manifest["ET2030_direct_current_input_unlocked"] is False


def test_R4_route_decisions_do_not_promote_context_or_redefine_main_660(r4_output: Path):
    rows = _read_csv(r4_output / "route_validation_decision_table.csv")
    allowed = {
        "confirm_for_future_review",
        "demote_from_R4_candidate",
        "reclassify_requires_external_review",
        "inconclusive_requires_plan_revision",
    }

    assert len(rows) == rv2.MAX_R4_REPRESENTATIVE_ROUTES
    assert {row["final_route_validation_decision"] for row in rows}.issubset(allowed)
    assert all(row["context_route_promotion_authorized"] == "False" for row in rows)
    assert all(row["route_promotion_eligible"] == "False" for row in rows)
    assert all(row["main_660_redefinition_authorized"] == "False" for row in rows)
    assert all(
        row["selected_annulus_replaces_all_crossing_ranking"] == "False" for row in rows
    )


def test_R4_numerical_solver_backend_records_completed_cases(r4_output: Path):
    cost = _read_csv(r4_output / "full_wave_cost_estimate.csv")[0]
    decisions = _read_csv(r4_output / "route_validation_decision_table.csv")
    manifest_rows = _read_csv(r4_output / "full_wave_case_manifest.csv")

    assert {row["solver_execution_mode"] for row in manifest_rows} == {
        cost["solver_execution_mode"]
    }
    assert cost["solver_backend_available"] == "True"
    assert cost["solver_execution_mode"] == "numerical_full_wave_backend"
    assert cost["solver_backend_name"] == rv2.R4_INTERNAL_NUMERICAL_SOLVER_BACKEND
    assert cost["solver_call_path"] == "_R4_channel_modal_green_solver_case"
    assert all(row["solver_case_completed"] == "True" for row in manifest_rows)
    assert all(row["solver_call_path"] == cost["solver_call_path"] for row in manifest_rows)
    assert all(len(row["solver_output_checksum"]) == 64 for row in manifest_rows)
    assert all(
        row["full_wave_value_source"] == "channel_modal_green_numerical_solver_output"
        for row in manifest_rows
    )
    assert all(row["solver_case_completed_all"] == "True" for row in decisions)
    assert all(row["decision_source"] == "solver_confirmed_rows" for row in decisions)


def test_R4_guardrail_summaries_block_invalid_claims(r4_output: Path):
    detector_blank = _read_csv(r4_output / "detector_blank_claim_guardrail_summary.csv")
    thermal = _read_csv(r4_output / "thermal_404_full_wave_gate_summary.csv")
    bfp = _read_csv(r4_output / "BFP_slit_pinhole_observable_comparison.csv")

    assert any(
        row["guardrail"] == "ET2030_BNC_direct_to_LI5640_current_input"
        and row["connection_physical_validity"] == "forbidden"
        for row in detector_blank
    )
    assert any(
        row["guardrail"] == "blank_rare_tail"
        and row["finite_monte_carlo_zero_event_inferred"] == "False"
        and row["false_positive_per_min_claim"] == "analytic_prior_only"
        for row in detector_blank
    )
    assert any(
        row["guardrail"] == "legacy_SNR_headers"
        and row["legacy_detector_SNR_output_header_emitted"] == "False"
        and row["legacy_calibrated_detector_SNR_output_header_emitted"] == "False"
        for row in detector_blank
    )
    assert all(
        row["thermal_sidecar_does_not_increase_nodi_score"] == "True"
        for row in thermal
    )
    assert all(
        row["same_operator_applied_to_reference_and_scattering"] == "True"
        for row in bfp
    )
