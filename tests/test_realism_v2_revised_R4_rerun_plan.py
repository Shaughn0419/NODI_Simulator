from __future__ import annotations

import copy
import csv
from collections import Counter

import pytest

from nodi_simulator import realism_v2 as rv2


def test_R4_revised_rerun_plan_is_plan_only_and_blocks_R5():
    plan = rv2.validate_R4_revised_rerun_plan()
    boundary = plan["authorization_boundary"]

    assert plan["stage"] == "R4_revised_rerun_plan_only"
    assert boundary["revised_R4_rerun_execution_authorized"] is False
    assert boundary["R5_plan_preparation_authorized"] is False
    assert boundary["R5_full_grid_v2_authorized"] is False
    assert boundary["context_route_promotion_authorized"] is False
    assert boundary["main_660_redefinition_authorized"] is False


def test_R4_revised_rerun_consumes_accepted_audit_without_recovering_main_660():
    plan = rv2.validate_R4_revised_rerun_plan()
    evidence = plan["input_evidence"]

    assert evidence["accepted_gate"] == (
        "PASS_ROUTE_MODEL_AUDIT_PREPARE_REVISED_R4_RERUN_PLAN_ONLY"
    )
    assert evidence["best_allowed_convention_id"] == (
        "global_full_wave_cross_term_sign_flip"
    )
    assert evidence["all_nonblank_sign_preserved_after_global_flip"] > 0.86
    assert evidence["main_660_nonblank_sign_preserved_after_global_flip"] == 0.75
    assert evidence["main_660_recovery_threshold"] == 0.8
    assert evidence["main_660_recovery_gate_met"] is False


def test_R4_revised_rerun_cost_cap_is_same_representative_R4_panel():
    plan = rv2.validate_R4_revised_rerun_plan()
    cap = plan["cost_cap"]
    cost = rv2.estimate_R4_revised_rerun_cost()

    assert cap["max_R4_revised_rerun_routes"] == rv2.MAX_R4_REPRESENTATIVE_ROUTES
    assert cap["max_R4_revised_rerun_particles"] == rv2.MAX_R4_REPRESENTATIVE_PARTICLES
    assert cap["max_R4_revised_rerun_solver_cases_before_review"] == 432
    assert cost["solver_case_count"] == 432
    assert cost["under_R4_revised_rerun_review_cap"] is True
    over = rv2.estimate_R4_revised_rerun_cost(n_routes=10)
    assert over["under_R4_revised_rerun_review_cap"] is False


def test_R4_revised_rerun_route_and_particle_panels_are_locked():
    plan = rv2.validate_R4_revised_rerun_plan()
    route_keys = {
        (row["wavelength_nm"], row["width_nm"], row["depth_nm"])
        for row in plan["route_panel"]
    }

    assert route_keys == rv2.R4_REQUIRED_ROUTES
    assert all(row["route_role_locked"] is True for row in plan["route_panel"])
    assert all(
        row["context_route_promotion_authorized"] is False
        for row in plan["route_panel"]
    )
    assert all(
        row["main_660_redefinition_authorized"] is False
        for row in plan["route_panel"]
    )
    assert {row["particle_id"] for row in plan["particle_panel"]} == (
        rv2.R4_REQUIRED_PARTICLES
    )


def test_R4_revised_rerun_main_660_failure_cluster_matches_R4_csv():
    plan = rv2.validate_R4_revised_rerun_plan()
    diagnostic = plan["main_660_near_wall_coarse_screen_diagnostic"]
    expected = {
        (row["route_id"], row["interface_state"], row["mesh_level"]): row[
            "failed_rows_after_global_flip"
        ]
        for row in diagnostic["failure_cluster"]
    }

    actual: Counter[tuple[str, str, str]] = Counter()
    with (
        rv2.DEFAULT_REPRESENTATIVE_FULL_WAVE_R4_DIR
        / "full_wave_observable_summary.csv"
    ).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row["route_role"] != "main_660" or row["particle_id"] == "blank":
                continue
            full_wave = float(row["full_wave_cross_term_signed_W"])
            surrogate = float(row["surrogate_cross_term_signed_W"])
            sign_preserved_after_flip = (full_wave < 0) == (surrogate > 0)
            if not sign_preserved_after_flip:
                actual[(row["route_id"], row["interface_state"], row["mesh_level"])] += 1

    assert diagnostic["main_660_nonblank_rows"] == 80
    assert diagnostic["failed_rows_after_global_flip"] == 20
    assert expected == {
        ("660_800x1400", "near_wall_stress", "coarse_screen"): 10,
        ("660_800x1500", "near_wall_stress", "coarse_screen"): 10,
    }
    assert dict(actual) == expected


def test_R4_revised_rerun_sign_convention_and_reliability_are_preregistered():
    plan = rv2.validate_R4_revised_rerun_plan()
    convention = plan["cross_term_convention_contract"]
    reliability = plan["sign_reliability_policy"]

    assert convention["canonical_delta_P_NODI_identity"] == (
        "Delta_P_NODI = |E_ref + E_sca|^2 - |E_ref|^2 = "
        "|E_sca|^2 + 2*Re(E_ref*conj(E_sca))"
    )
    assert convention["global_flip_is_not_recovery_by_itself"] is True
    assert convention["route_specific_manual_sign_flips_allowed"] is False
    assert "full_wave_cross_term_signed_W convention mismatch" in convention[
        "polarity_mapping_questions"
    ]
    assert reliability["absolute_floor_W"] > 0.0
    assert 0.0 < reliability["relative_floor"] < 1.0
    assert reliability["retroactive_reinterpretation_of_current_audit_allowed"] is False


def test_R4_revised_rerun_required_diagnostic_fields_are_explicit():
    plan = rv2.validate_R4_revised_rerun_plan()
    fields = set(
        plan["main_660_near_wall_coarse_screen_diagnostic"][
            "required_output_fields"
        ]
    )

    assert rv2.R4_REVISED_RERUN_REQUIRED_DIAGNOSTIC_FIELDS.issubset(fields)
    assert "sign_reliability_band" in fields
    assert "sign_ambiguous_due_to_near_zero" in fields
    assert "mesh_refined_agreement" in fields


def test_R4_revised_rerun_recovery_requires_all_three_main_660_gates():
    plan = rv2.validate_R4_revised_rerun_plan()
    recovery = plan["recovery_criteria"]

    assert recovery["main_660_nonblank_after_global_convention_min"] >= 0.8
    assert recovery["main_660_sign_reliable_subset_min"] >= 0.8
    assert recovery["main_660_review_refined_mesh_min"] >= 0.8
    assert recovery["no_route_role_change_required"] is True
    assert recovery["no_context_route_promotion_required"] is True
    assert recovery["future_external_review_required_before_R5_plan"] is True
    assert recovery["possible_future_gate_after_success"] == (
        "PASS_REVISED_R4_RESULTS_PREPARE_R5_PLAN_ONLY"
    )


def test_R4_revised_rerun_required_outputs_are_not_R5_outputs():
    plan = rv2.validate_R4_revised_rerun_plan()
    outputs = set(plan["required_outputs_if_executed_after_review"])

    assert outputs == rv2.R4_REVISED_RERUN_REQUIRED_OUTPUTS_IF_EXECUTED
    assert "main_660_near_wall_coarse_sign_ambiguity_check.csv" in outputs
    assert "sign_reliability_band_summary.csv" in outputs
    assert not any("full_grid" in output for output in outputs)
    assert not any("R5" in output for output in outputs)


def test_R4_revised_rerun_stop_gates_include_both_legacy_snr_names():
    plan = rv2.validate_R4_revised_rerun_plan()
    stop_gates = set(plan["stop_gates"])

    assert rv2.R4_REVISED_RERUN_REQUIRED_STOP_GATES.issubset(stop_gates)
    assert "legacy_detector_SNR_output_header_emitted" in stop_gates
    assert "legacy_calibrated_detector_SNR_output_header_emitted" in stop_gates
    assert "R5_plan_or_full_grid_v2_started" in stop_gates
    assert "main_660_redefinition_attempted" in stop_gates


def test_R4_revised_rerun_manifest_expectations_keep_forbidden_flags_false():
    plan = rv2.validate_R4_revised_rerun_plan()
    manifest = plan["manifest_expectations"]

    assert manifest["R4_representative_full_wave_validation_run"] is True
    assert manifest["R4_revised_rerun_run"] is False
    assert manifest["R5_full_grid_v2_run"] is False
    assert manifest["v1_full_grid_overwritten"] is False
    assert manifest["Tsuyama_paper_fit_continued"] is False
    assert manifest["selected_annulus_bounds_changed"] is False
    assert manifest["calibrated_SNR_claim_emitted"] is False
    assert manifest["ET2030_direct_current_input_unlocked"] is False


@pytest.mark.parametrize(
    ("section", "key", "value", "match"),
    [
        (
            "authorization_boundary",
            "R5_plan_preparation_authorized",
            True,
            "R5_plan_preparation_authorized=false",
        ),
        (
            "input_evidence",
            "main_660_recovery_gate_met",
            True,
            "cannot treat main_660 as recovered",
        ),
        (
            "cross_term_convention_contract",
            "global_flip_is_not_recovery_by_itself",
            False,
            "global flip as recovery",
        ),
        (
            "sign_reliability_policy",
            "retroactive_reinterpretation_of_current_audit_allowed",
            True,
            "cannot rewrite the audit",
        ),
    ],
)
def test_R4_revised_rerun_validation_fails_closed(section, key, value, match):
    broken = copy.deepcopy(rv2.load_R4_revised_rerun_plan())
    broken[section][key] = value

    with pytest.raises(ValueError, match=match):
        rv2.validate_R4_revised_rerun_plan(broken)


def test_R4_revised_rerun_missing_stop_gate_fails_closed():
    for gate in rv2.R4_REVISED_RERUN_REQUIRED_STOP_GATES:
        broken = copy.deepcopy(rv2.load_R4_revised_rerun_plan())
        broken["stop_gates"] = [
            existing for existing in broken["stop_gates"] if existing != gate
        ]

        with pytest.raises(ValueError, match="stop gates are incomplete"):
            rv2.validate_R4_revised_rerun_plan(broken)
