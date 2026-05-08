from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


@pytest.fixture(scope="module")
def revised_r4_output(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("revised_r4_rerun")
    rv2.run_revised_R4_rerun(output, write_root_manifest=False)
    return output


def test_revised_R4_rerun_requires_exact_external_authorization(tmp_path: Path):
    with pytest.raises(ValueError, match="exact external authorization"):
        rv2.run_revised_R4_rerun(
            tmp_path,
            external_authorization="PASS_TO_R5_PLAN",
            write_root_manifest=False,
        )


def test_revised_R4_outputs_required_files_only_and_respect_cap(
    revised_r4_output: Path,
):
    produced = {path.name for path in revised_r4_output.iterdir() if path.is_file()}

    assert produced == rv2.R4_REVISED_RERUN_REQUIRED_OUTPUTS_IF_EXECUTED

    case_rows = _read_csv(revised_r4_output / "revised_full_wave_case_manifest.csv")
    cost = _read_csv(revised_r4_output / "full_wave_cost_estimate.csv")[0]

    assert len(case_rows) == rv2.MAX_R4_REVISED_RERUN_SOLVER_CASES_BEFORE_REVIEW
    assert int(cost["actual_case_rows"]) == rv2.MAX_R4_REVISED_RERUN_SOLVER_CASES_BEFORE_REVIEW
    assert cost["under_R4_revised_rerun_review_cap"] == "True"
    assert int(cost["solver_case_count"]) == rv2.MAX_R4_REVISED_RERUN_SOLVER_CASES_BEFORE_REVIEW


def test_revised_R4_case_panel_matches_authorized_plan(revised_r4_output: Path):
    rows = _read_csv(revised_r4_output / "revised_full_wave_case_manifest.csv")

    routes = {
        (int(row["wavelength_nm"]), int(row["width_nm"]), int(row["depth_nm"]))
        for row in rows
    }
    particles = {row["particle_id"] for row in rows}
    interface_states = {row["interface_state"] for row in rows}
    polarization_states = {row["polarization_state"] for row in rows}
    mesh_levels = {row["mesh_level"] for row in rows}

    assert routes == rv2.R4_REQUIRED_ROUTES
    assert particles == rv2.R4_REQUIRED_PARTICLES
    assert interface_states == {"centerline_nominal", "near_wall_stress"}
    assert polarization_states == {"nominal_linear", "orthogonal_sensitivity"}
    assert mesh_levels == {"coarse_screen", "review_refined"}
    assert all(row["R4_revised_rerun_run"] == "True" for row in rows)
    assert all(row["R5_full_grid_v2_run"] == "False" for row in rows)
    assert all(row["context_route_promotion_authorized"] == "False" for row in rows)
    assert all(row["main_660_redefinition_authorized"] == "False" for row in rows)


def test_revised_R4_observables_record_canonical_sign_and_reliability(
    revised_r4_output: Path,
):
    rows = _read_csv(revised_r4_output / "revised_full_wave_observable_summary.csv")

    assert len(rows) == rv2.MAX_R4_REVISED_RERUN_SOLVER_CASES_BEFORE_REVIEW
    required = {
        "canonical_cross_term_convention_id",
        "canonical_delta_P_NODI_identity",
        "raw_full_wave_cross_term_signed_W",
        "canonical_full_wave_cross_term_signed_W",
        "canonical_surrogate_cross_term_signed_W",
        "median_abs_full_wave_cross_term_for_route_particle",
        "sign_reliability_threshold_W",
        "sign_reliability_threshold_source",
        "sign_reliability_band",
        "sign_preserved_raw",
        "sign_preserved_after_global_flip",
        "sign_ambiguous_due_to_near_zero",
        "mesh_refined_agreement",
        "near_wall_stress_agreement",
    }
    assert required.issubset(rows[0])
    assert {
        row["canonical_cross_term_convention_id"] for row in rows
    } == {"global_full_wave_cross_term_sign_flip"}
    assert all(row["SNR_claim_level"] == "absolute_blocked" for row in rows)
    assert all(row["event_probability_claim_level"] == "absolute_blocked" for row in rows)
    assert all("detector_SNR" not in row for row in rows)
    assert all("calibrated_detector_SNR" not in row for row in rows)
    for row in rows[:50]:
        rv2.validate_required_output_fields(row)
        assert row["scenario_id"] == "R4_revised_rerun"
        assert row["scenario_id"] not in row["base_route_key"]


def test_revised_R4_convention_summary_blocks_R5(revised_r4_output: Path):
    rows = _read_csv(
        revised_r4_output / "cross_term_convention_resolution_summary.csv"
    )
    by_id = {row["convention_id"]: row for row in rows}
    canonical = by_id["global_full_wave_cross_term_sign_flip"]

    assert by_id["as_recorded_cross_term"][
        "sign_preserved_fraction_nonblank"
    ] == "0.1388888888888889"
    assert canonical["sign_preserved_fraction_nonblank"] == "0.8611111111111112"
    assert canonical["main_660_sign_preserved_fraction"] == "0.75"
    assert canonical["main_660_reliable_subset_fraction"] == "0.7567567567567568"
    assert canonical["main_660_review_refined_mesh_fraction"] == "1.0"
    assert canonical["main_660_recovery_gate_met"] == "False"
    assert canonical["revised_R4_recovery_decision"] == (
        "main_660_recovery_gate_not_met_R5_blocked"
    )
    assert all(row["R5_plan_preparation_authorized"] == "False" for row in rows)


def test_revised_R4_main_660_near_wall_coarse_cluster_is_explicit(
    revised_r4_output: Path,
):
    rows = _read_csv(
        revised_r4_output / "main_660_near_wall_coarse_sign_ambiguity_check.csv"
    )
    failures: Counter[tuple[str, str, str]] = Counter()
    near_zero = Counter()

    assert len(rows) == 80
    for row in rows:
        if row["sign_preserved_after_global_flip"] == "False":
            failures[(row["route_id"], row["interface_state"], row["mesh_level"])] += 1
        if row["sign_reliability_band"] == "near_zero_ambiguous":
            near_zero[row["route_id"]] += 1
        assert row["main_660_recovery_gate_met"] == "False"
        assert row["R5_plan_preparation_authorized"] == "False"
        assert "sign_reliability_threshold_W" in row
        assert "sign_reliability_threshold_source" in row

    assert dict(failures) == {
        ("660_800x1400", "near_wall_stress", "coarse_screen"): 10,
        ("660_800x1500", "near_wall_stress", "coarse_screen"): 10,
    }
    assert dict(near_zero) == {"660_800x1400": 2, "660_800x1500": 4}


def test_revised_R4_route_decisions_keep_governance_locked(revised_r4_output: Path):
    rows = _read_csv(revised_r4_output / "route_validation_decision_table.csv")
    main_rows = [row for row in rows if row["route_role"] == "main_660"]

    assert len(rows) == rv2.MAX_R4_REPRESENTATIVE_ROUTES
    assert len(main_rows) == 2
    assert all(row["main_660_recovery_gate_met"] == "False" for row in main_rows)
    assert all(
        row["final_route_validation_decision"] == "inconclusive_requires_plan_revision"
        for row in main_rows
    )
    assert all(row["R5_plan_preparation_authorized"] == "False" for row in rows)
    assert all(row["context_route_promotion_authorized"] == "False" for row in rows)
    assert all(row["route_promotion_eligible"] == "False" for row in rows)
    assert all(row["main_660_redefinition_authorized"] == "False" for row in rows)
    assert all(
        row["selected_annulus_replaces_all_crossing_ranking"] == "False"
        for row in rows
    )


def test_revised_R4_guardrails_include_legacy_snr_blocks(revised_r4_output: Path):
    rows = _read_csv(revised_r4_output / "revised_R4_guardrail_summary.csv")
    by_guardrail = {row["guardrail"]: row for row in rows}

    assert by_guardrail["R5_plan_or_full_grid_v2_started"]["value"] == "False"
    assert by_guardrail["context_route_promotion_attempted"]["value"] == "False"
    assert by_guardrail["main_660_redefinition_attempted"]["value"] == "False"
    assert by_guardrail["thermal_sidecar_used_to_increase_NODI_score"][
        "value"
    ] == "False"
    assert by_guardrail["finite_zero_event_blank_safety_claim_emitted"][
        "value"
    ] == "False"
    assert by_guardrail["legacy_detector_SNR_output_header_emitted"]["value"] == "False"
    assert by_guardrail["legacy_calibrated_detector_SNR_output_header_emitted"][
        "value"
    ] == "False"


def test_revised_R4_manifest_marks_revised_R4_true_and_R5_false(
    revised_r4_output: Path,
):
    manifest = json.loads((revised_r4_output / "run_manifest.json").read_text())

    assert manifest["R4_representative_full_wave_validation_run"] is True
    assert manifest["R4_revised_rerun_run"] is True
    assert manifest["R5_plan_preparation_authorized"] is False
    assert manifest["R5_full_grid_v2_run"] is False
    assert manifest["event_budget"]["solver_case_rows"] == 432
    assert manifest["scenario_budget"]["main_660_recovery_gate_met"] is False
    assert manifest["scenario_budget"]["main_660_nonblank_after_global_convention"] == 0.75
    assert manifest["scenario_budget"]["main_660_review_refined_mesh"] == 1.0
    assert manifest["v1_full_grid_overwritten"] is False
    assert manifest["Tsuyama_paper_fit_continued"] is False
    assert manifest["selected_annulus_bounds_changed"] is False
    assert manifest["calibrated_SNR_claim_emitted"] is False
    assert manifest["ET2030_direct_current_input_unlocked"] is False
