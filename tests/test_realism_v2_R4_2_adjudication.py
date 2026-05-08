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
def r4_2_output(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("r4_2_adjudication")
    rv2.run_R4_2_main660_nearwall_mesh_adjudication(
        output,
        write_root_manifest=False,
    )
    return output


def test_R4_2_requires_exact_external_authorization(tmp_path: Path):
    with pytest.raises(ValueError, match="exact external authorization"):
        rv2.run_R4_2_main660_nearwall_mesh_adjudication(
            tmp_path,
            external_authorization="PASS_TO_R5_PLAN",
            write_root_manifest=False,
        )


def test_R4_2_outputs_required_files_only_and_respect_cap(r4_2_output: Path):
    produced = {path.name for path in r4_2_output.iterdir() if path.is_file()}
    case_rows = _read_csv(r4_2_output / "R4_2_case_manifest.csv")
    cost = _read_csv(r4_2_output / "R4_2_cost_estimate.csv")[0]

    assert produced == rv2.R4_2_ADJUDICATION_REQUIRED_OUTPUTS_IF_EXECUTED
    assert len(case_rows) == 48
    assert int(cost["actual_case_rows"]) == 48
    assert int(cost["solver_case_count"]) == 48
    assert int(cost["max_R4_2_solver_cases_before_review"]) == 64
    assert cost["under_R4_2_review_cap"] == "True"
    assert cost["R5_plan_preparation_authorized"] == "False"


def test_R4_2_case_panel_is_only_main_660_fine_confirm(r4_2_output: Path):
    rows = _read_csv(r4_2_output / "R4_2_case_manifest.csv")
    routes = {
        (int(row["wavelength_nm"]), int(row["width_nm"]), int(row["depth_nm"]))
        for row in rows
    }
    particles = {row["particle_id"] for row in rows}
    interface_states = {row["interface_state"] for row in rows}
    polarization_states = {row["polarization_state"] for row in rows}
    mesh_levels = {row["mesh_level"] for row in rows}

    assert routes == {(660, 800, 1400), (660, 800, 1500)}
    assert particles == rv2.R4_2_ADJUDICATION_PARTICLES_REQUIRED | {"blank"}
    assert interface_states == {"near_wall_stress", "centerline_nominal"}
    assert polarization_states == {"nominal_linear", "orthogonal_sensitivity"}
    assert mesh_levels == {"fine_confirm"}
    assert {row["mesh_level_role"] for row in rows} == {
        "validation_grade_confirmation"
    }
    assert all(row["route_role"] == "main_660" for row in rows)
    assert all(row["R5_full_grid_v2_run"] == "False" for row in rows)
    assert all(row["main_660_redefinition_authorized"] == "False" for row in rows)


def test_R4_2_observables_have_required_sign_lobe_and_claim_fields(
    r4_2_output: Path,
):
    rows = _read_csv(r4_2_output / "R4_2_observable_summary.csv")
    required = {
        "canonical_full_wave_cross_term_signed_W",
        "surrogate_cross_term_signed_W",
        "sign_reliability_threshold_W",
        "sign_reliability_threshold_source",
        "sign_reliability_band",
        "sign_preserved_after_global_flip",
        "review_refined_agreement",
        "fine_confirm_agreement",
        "coarse_screen_conflict",
    } | rv2.R4_2_ADJUDICATION_REQUIRED_MODE_LOBE_FIELDS

    assert len(rows) == 48
    assert required.issubset(rows[0])
    assert all(row["SNR_claim_level"] == "absolute_blocked" for row in rows)
    assert all(row["event_probability_claim_level"] == "absolute_blocked" for row in rows)
    assert all(row["p_detect_mapping_claim_level"] == "relative_with_priors" for row in rows)
    assert all(row["route_specific_manual_sign_flip_applied"] == "False" for row in rows)
    assert all("detector_SNR" not in row for row in rows)
    assert all("calibrated_detector_SNR" not in row for row in rows)
    for row in rows[:20]:
        rv2.validate_required_output_fields(row)


def test_R4_2_main660_summary_recovers_only_for_future_R5_plan_review(
    r4_2_output: Path,
):
    rows = _read_csv(r4_2_output / "main660_fine_confirm_sign_summary.csv")
    overall = {row["route_id"]: row for row in rows}["ALL_MAIN_660"]

    assert len(rows) == 3
    assert overall["fine_confirm_nonblank_rows"] == "40"
    assert overall["fine_confirm_main660_fraction"] == "1.0"
    assert overall["fine_confirm_sign_reliable_subset_fraction"] == "1.0"
    assert overall["review_refined_main660_fraction"] == "1.0"
    assert overall["fine_confirm_agrees_with_review_refined"] == "1.0"
    assert overall["R4_2_route_gate_met"] == "True"
    assert overall["R4_2_recovery_decision"] == (
        "validation_grade_main660_recovered_prepare_R5_plan_review_only"
    )
    assert overall["R5_plan_preparation_authorized"] == "False"
    assert overall["possible_future_gate_after_success"] == (
        "PASS_R4_2_RESULTS_PREPARE_R5_PLAN_ONLY"
    )


def test_R4_2_mesh_adjudication_demotes_coarse_to_screening_only(
    r4_2_output: Path,
):
    rows = _read_csv(r4_2_output / "mesh_level_role_adjudication_summary.csv")
    by_mesh = {row["mesh_level"]: row for row in rows}

    assert by_mesh["coarse_screen"]["mesh_level_role"] == "screening_only"
    assert by_mesh["coarse_screen"]["included_in_validation_grade_fraction"] == "False"
    assert by_mesh["coarse_screen"]["can_confirm_or_demote_routes"] == "False"
    assert by_mesh["coarse_screen"]["sign_preserved_fraction"] == "0.5"
    assert by_mesh["review_refined"]["mesh_level_role"] == "validation_grade"
    assert by_mesh["review_refined"]["sign_preserved_fraction"] == "1.0"
    assert by_mesh["fine_confirm"]["mesh_level_role"] == (
        "validation_grade_confirmation"
    )
    assert by_mesh["fine_confirm"]["sign_preserved_fraction"] == "1.0"


def test_R4_2_lobe_mode_and_parity_outputs_are_diagnostic_only(r4_2_output: Path):
    lobe_rows = _read_csv(r4_2_output / "BFP_lobe_resolved_cross_term_summary.csv")
    mode_rows = _read_csv(r4_2_output / "mode_overlap_phase_summary.csv")
    parity_rows = _read_csv(r4_2_output / "ROI_parity_sanity_summary.csv")

    assert len(lobe_rows) == 48
    assert len(mode_rows) == 48
    assert len(parity_rows) == 48
    assert all(row["claim_level"] == "diagnostic_only" for row in lobe_rows)
    assert all(row["phase_diagnostic_only_not_gate_replacement"] == "True" for row in mode_rows)
    assert all(row["route_specific_manual_sign_flip_required"] == "False" for row in parity_rows)
    assert all(row["same_ROI_operator_applied_to_reference_and_scattering"] == "True" for row in parity_rows)


def test_R4_2_coarse_conflict_summary_is_warning_only(r4_2_output: Path):
    rows = _read_csv(r4_2_output / "coarse_screen_conflict_summary.csv")

    assert {row["route_id"] for row in rows} == {"660_800x1400", "660_800x1500"}
    assert all(row["coarse_screen_role"] == "screening_only" for row in rows)
    assert all(row["coarse_screen_can_confirm_or_demote_routes"] == "False" for row in rows)
    assert all(row["coarse_screen_disagreement_warning_only"] == "True" for row in rows)
    assert all(row["fine_confirm_agrees_with_review_refined"] == "1.0" for row in rows)
    assert all(row["coarse_screen_adjudication_outcome"] == "coarse_screen_screening_artifact_warning" for row in rows)


def test_R4_2_guardrails_and_manifest_keep_forbidden_scope_false(r4_2_output: Path):
    guardrails = _read_csv(r4_2_output / "R4_2_guardrail_summary.csv")
    by_guardrail = {row["guardrail"]: row for row in guardrails}
    manifest = json.loads((r4_2_output / "run_manifest.json").read_text())

    assert by_guardrail["R5_plan_or_full_grid_v2_started"]["value"] == "False"
    assert by_guardrail["context_route_promotion_attempted"]["value"] == "False"
    assert by_guardrail["main_660_redefinition_attempted"]["value"] == "False"
    assert by_guardrail["route_specific_manual_sign_flip_attempted"]["value"] == "False"
    assert by_guardrail["legacy_detector_SNR_output_header_emitted"]["value"] == "False"
    assert by_guardrail["legacy_calibrated_detector_SNR_output_header_emitted"]["value"] == "False"
    assert manifest["R4_2_main660_nearwall_mesh_adjudication_run"] is True
    assert manifest["R5_plan_preparation_authorized"] is False
    assert manifest["R5_full_grid_v2_run"] is False
    assert manifest["context_route_promotion_authorized"] is False
    assert manifest["main_660_redefinition_authorized"] is False
    assert manifest["route_specific_manual_sign_flips_authorized"] is False
    assert manifest["event_budget"]["solver_case_rows"] == 48
    assert manifest["scenario_budget"]["R4_2_gate_met"] is True
    assert manifest["scenario_budget"]["fine_confirm_main660_fraction"] == 1.0
    assert manifest["scenario_budget"]["review_refined_main660_fraction"] == 1.0
    assert len(manifest["source_revised_R4_observable_summary_checksum"]) == 64

