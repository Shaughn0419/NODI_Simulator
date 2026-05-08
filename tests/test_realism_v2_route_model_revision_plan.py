from __future__ import annotations

import csv
import copy

import pytest

from nodi_simulator import realism_v2 as rv2


def test_R4_route_model_revision_plan_is_plan_only_and_blocks_R5():
    plan = rv2.validate_R4_route_model_revision_plan()
    boundary = plan["authorization_boundary"]

    assert plan["stage"] == "R4_route_model_revision_plan_only"
    assert boundary["route_model_revision_execution_authorized"] is False
    assert boundary["R5_plan_preparation_authorized"] is False
    assert boundary["R5_full_grid_v2_authorized"] is False
    assert boundary["context_route_promotion_authorized"] is False
    assert boundary["main_660_redefinition_authorized"] is False
    assert boundary["selected_annulus_bound_change_authorized"] is False


def test_R4_route_model_revision_consumes_all_demoted_R4_routes():
    plan = rv2.validate_R4_route_model_revision_plan()
    evidence = plan["input_evidence"]
    routes = plan["demoted_route_panel"]
    route_keys = {
        (row["wavelength_nm"], row["width_nm"], row["depth_nm"]) for row in routes
    }

    assert evidence["accepted_gate"] == (
        "PASS_R4_NUMERICAL_RERUN_HALT_R5_PLAN_ROUTE_MODEL_REVISION_ONLY"
    )
    assert evidence["all_representative_routes_demoted"] is True
    assert evidence["main_660_validated"] is False
    assert evidence["route_decision_counts"]["demote_from_R4_candidate"] == 9
    assert route_keys == rv2.R4_REQUIRED_ROUTES
    assert all(
        row["R4_final_route_validation_decision"] == "demote_from_R4_candidate"
        for row in routes
    )
    assert all(row["route_role_locked"] is True for row in routes)


def test_R4_route_model_revision_focuses_on_sign_phase_not_R5():
    plan = rv2.validate_R4_route_model_revision_plan()
    focus_areas = set(plan["revision_focus_areas"])

    assert rv2.R4_ROUTE_MODEL_REVISION_REQUIRED_FOCUS_AREAS.issubset(focus_areas)
    assert "cross_term_sign_convention" in focus_areas
    assert "reference_phase_convention" in focus_areas
    assert "surrogate_scalar_vs_modal_sign_mapping" in focus_areas
    assert "R5_full_grid_v2" not in focus_areas


def test_R4_route_model_revision_sign_phase_contract_is_explicit():
    plan = rv2.validate_R4_route_model_revision_plan()
    contract = plan["sign_phase_audit_contract"]

    assert contract["delta_intensity_identity"] == (
        "|E_ref + E_sca|^2 - |E_ref|^2 = "
        "2*Re(E_ref*conj(E_sca)) + |E_sca|^2"
    )
    assert contract["cross_term_operator"].startswith("2*Re(")
    assert "convention_mismatch" in contract["allowed_hypotheses"]
    assert "true_physical_phase_reversal" in contract["allowed_hypotheses"]
    assert "posthoc_route_promotion" in contract["forbidden_hypotheses"]
    assert "main_660_redefinition" in contract["forbidden_hypotheses"]


def test_R4_route_model_revision_recovery_gate_requires_future_R4_review():
    plan = rv2.validate_R4_route_model_revision_plan()
    recovery = plan["recovery_decision_gates"]

    assert recovery["R5_plan_remains_blocked_until_external_review"] is True
    assert recovery["future_R4_rerun_required_before_R5_plan"] is True
    assert recovery["context_route_promotion_authorized"] is False
    assert recovery["main_660_redefinition_authorized"] is False
    assert (
        recovery["min_main_660_nonblank_sign_preserved_fraction_for_recovery"]
        >= 0.8
    )
    assert "single_pre_registered_cross_term_convention" in recovery[
        "confirm_convention_mismatch_if"
    ]


def test_R4_route_model_revision_required_outputs_are_review_scoped():
    plan = rv2.validate_R4_route_model_revision_plan()
    outputs = set(plan["required_outputs_if_executed_after_review"])

    assert outputs == rv2.R4_ROUTE_MODEL_REVISION_REQUIRED_OUTPUTS_IF_EXECUTED
    assert "route_model_revision_decision_table.csv" in outputs
    assert "run_manifest.json" in outputs
    assert not any("full_grid" in output for output in outputs)


def test_R4_route_model_revision_stop_gates_are_fail_closed():
    plan = rv2.validate_R4_route_model_revision_plan()
    stop_gates = set(plan["stop_gates"])

    assert rv2.R4_ROUTE_MODEL_REVISION_REQUIRED_STOP_GATES.issubset(stop_gates)
    assert "R5_plan_or_full_grid_v2_started" in stop_gates
    assert "context_route_promotion_attempted" in stop_gates
    assert "main_660_redefinition_attempted" in stop_gates
    assert "legacy_detector_SNR_output_header_emitted" in stop_gates
    assert "legacy_calibrated_detector_SNR_output_header_emitted" in stop_gates


def test_R4_route_model_revision_manifest_expectations_keep_forbidden_flags_false():
    plan = rv2.validate_R4_route_model_revision_plan()
    manifest = plan["manifest_expectations"]

    assert manifest["R4_representative_full_wave_validation_run"] is True
    assert manifest["R5_full_grid_v2_run"] is False
    assert manifest["v1_full_grid_overwritten"] is False
    assert manifest["Tsuyama_paper_fit_continued"] is False
    assert manifest["selected_annulus_bounds_changed"] is False
    assert manifest["calibrated_SNR_claim_emitted"] is False
    assert manifest["ET2030_direct_current_input_unlocked"] is False


def test_R4_route_model_revision_demoted_routes_match_actual_R4_csv():
    plan = rv2.validate_R4_route_model_revision_plan()
    decision_path = (
        rv2.DEFAULT_REPRESENTATIVE_FULL_WAVE_R4_DIR
        / "route_validation_decision_table.csv"
    )
    with decision_path.open(newline="", encoding="utf-8") as handle:
        csv_rows = list(csv.DictReader(handle))

    csv_demoted = {
        (
            int(row["wavelength_nm"]),
            int(row["width_nm"]),
            int(row["depth_nm"]),
            row["route_role"],
            row["final_route_validation_decision"],
        )
        for row in csv_rows
        if row["final_route_validation_decision"] == "demote_from_R4_candidate"
    }
    yaml_demoted = {
        (
            int(row["wavelength_nm"]),
            int(row["width_nm"]),
            int(row["depth_nm"]),
            row["route_role"],
            row["R4_final_route_validation_decision"],
        )
        for row in plan["demoted_route_panel"]
    }

    assert len(csv_rows) == rv2.MAX_R4_REPRESENTATIVE_ROUTES
    assert len(csv_demoted) == rv2.MAX_R4_REPRESENTATIVE_ROUTES
    assert yaml_demoted == csv_demoted


@pytest.mark.parametrize(
    ("path", "value", "match"),
    [
        (
            ("authorization_boundary", "R5_plan_preparation_authorized"),
            True,
            "R5_plan_preparation_authorized=false",
        ),
        (
            ("input_evidence", "all_representative_routes_demoted"),
            False,
            "all-route demotion evidence",
        ),
        (
            ("recovery_decision_gates", "future_R4_rerun_required_before_R5_plan"),
            False,
            "future R4 evidence",
        ),
    ],
)
def test_R4_route_model_revision_validation_fails_closed(path, value, match):
    plan = rv2.load_R4_route_model_revision_plan()
    broken = copy.deepcopy(plan)
    section, key = path
    broken[section][key] = value

    with pytest.raises(ValueError, match=match):
        rv2.validate_R4_route_model_revision_plan(broken)


def test_R4_route_model_revision_missing_stop_gate_fails_closed():
    plan = rv2.load_R4_route_model_revision_plan()
    for gate in rv2.R4_ROUTE_MODEL_REVISION_REQUIRED_STOP_GATES:
        broken = copy.deepcopy(plan)
        broken["stop_gates"] = [
            existing for existing in broken["stop_gates"] if existing != gate
        ]

        with pytest.raises(ValueError, match="stop gates are incomplete"):
            rv2.validate_R4_route_model_revision_plan(broken)
