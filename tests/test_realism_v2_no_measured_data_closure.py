from __future__ import annotations

import copy
import csv
import json
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


V2_CLOSURE_DIR = rv2.DEFAULT_V2_NO_MEASURED_DATA_CLOSURE_DIR
R7_2_DIR = rv2.DEFAULT_R7_2_OPERATOR_ARTIFACT_GAP_REGISTER_DIR


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_v2_closure_plan_is_no_measured_data_plan_only():
    plan = rv2.validate_v2_no_measured_data_closure_plan()

    assert plan["schema_version"] == rv2.V2_NO_MEASURED_DATA_CLOSURE_SCHEMA_VERSION
    assert plan["stage"] == "V2_no_measured_data_closure_plan_only"
    assert plan["prior_gate"] == (
        "PASS_R7_2_RESULTS_PREPARE_V2_NO_MEASURED_DATA_CLOSURE_ONLY"
    )
    assert plan["selected_next_stage_lane"] == "v2_no_measured_data_closure_only"

    boundary = plan["authorization_boundary"]
    assert boundary["v2_is_no_measured_data_lane"] is True
    for key in (
        "operator_artifact_acquisition_authorized",
        "bench_measurement_authorized",
        "experimental_validation_execution_authorized",
        "R8_plan_preparation_authorized",
        "R8_execution_authorized",
        "new_experiment_authorized",
        "new_solver_case_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
        "calibrated_event_probability_authorized",
    ):
        assert boundary[key] is False


def test_v2_closure_plan_carries_R7_2_gap_register_without_acquisition():
    plan = rv2.validate_v2_no_measured_data_closure_plan()
    carry = plan["R7_2_evidence_carryforward"]
    r7_2_manifest = _csv_rows(R7_2_DIR / "R7_2_operator_artifact_gap_manifest.csv")[0]

    assert carry["R7_2_operator_artifact_gap_register_generation_run"] is True
    assert carry["generation_type"] == "artifact_gap_register_only_no_acquisition"
    assert carry["artifact_id_count"] == int(r7_2_manifest["artifact_id_count"])
    assert carry["required_artifact_field_count"] == int(
        r7_2_manifest["required_artifact_field_count"]
    )
    assert carry["selected_future_recommendation_class"] == (
        "prepare_v2_no_measured_data_closure_only"
    )
    for key in (
        "operator_artifact_acquisition_started",
        "bench_measurement_started",
        "experimental_validation_started",
        "R8_plan_preparation_authorized",
        "R8_execution_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
    ):
        assert carry[key] is False


def test_v2_closure_plan_route_claim_and_provenance_boundaries():
    plan = rv2.validate_v2_no_measured_data_closure_plan()

    assert set(plan["required_outputs_if_self_review_authorizes"]) == (
        rv2.V2_CLOSURE_REQUIRED_OUTPUTS
    )
    assert set(plan["stop_gates"]) >= rv2.V2_CLOSURE_FORBIDDEN_ACTIONS
    assert set(plan["closure_design"]["forbidden_actions"]) == (
        rv2.V2_CLOSURE_FORBIDDEN_ACTIONS
    )

    route = plan["route_governance_closure"]
    assert set(route["locked_main_660_route_ids"]) == {
        "660_800x1400",
        "660_800x1500",
    }
    assert route["context_route_promotion_authorized"] is False
    assert route["main_660_redefinition_authorized"] is False
    assert route["optional_660_900x1400_redefines_main_660"] is False
    assert route["selected_annulus_replaces_all_crossing_ranking"] is False

    claims = plan["claim_boundaries"]
    assert claims["SNR_claim_level"] == "absolute_blocked"
    assert claims["event_probability_claim_level"] == "absolute_blocked"
    assert claims["p_detect_mapping_claim_level"] == "relative_with_priors"
    assert claims["primary_metric"] == "detectability_relative_prior_score"
    assert claims["calibrated_SNR_claim_authorized"] is False
    assert claims["calibrated_event_probability_claim_authorized"] is False
    assert claims["absolute_LOD_claim_authorized"] is False
    assert claims["true_EV_concentration_claim_authorized"] is False
    assert claims["biological_specificity_claim_authorized"] is False

    forbidden_tokens = {
        "calibrated_SNR_or_event_probability_claim",
        "absolute_LOD_or_true_concentration_claim",
        "biological_specificity_claim",
    }
    assert forbidden_tokens <= set(plan["stop_gates"])
    assert forbidden_tokens <= set(plan["closure_design"]["forbidden_actions"])

    provenance = plan["provenance_freeze"]
    assert set(provenance["required_checksum_fields"]) == (
        rv2.V2_CLOSURE_REQUIRED_PROVENANCE_FIELDS
    )
    expected = {
        "R7_2_manifest_checksum": rv2.sha256_file(
            R7_2_DIR / "R7_2_operator_artifact_gap_manifest.csv"
        ),
        "R7_2_artifact_gap_registry_checksum": rv2.sha256_file(
            R7_2_DIR / "R7_2_artifact_gap_registry.csv"
        ),
        "R7_2_claim_guardrail_checksum": rv2.sha256_file(
            R7_2_DIR / "R7_2_claim_boundary_guardrail_summary.csv"
        ),
        "R7_2_stop_gate_checksum": rv2.sha256_file(
            R7_2_DIR / "R7_2_stop_gate_summary.csv"
        ),
        "R7_2_next_stage_matrix_checksum": rv2.sha256_file(
            R7_2_DIR / "R7_2_next_stage_recommendation_matrix.csv"
        ),
        "R7_2_run_manifest_checksum": rv2.run_manifest_provenance_checksum(
            R7_2_DIR / "run_manifest.json"
        ),
        "v2_consolidated_roadmap_checksum": rv2.sha256_file(
            rv2.PROJECT_ROOT
            / "reports"
            / "84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md"
        ),
        "v2_target_alignment_self_review_checksum": rv2.sha256_file(
            rv2.PROJECT_ROOT
            / "reports"
            / "85_EV_NODI_realism_v2_target_alignment_self_review.md"
        ),
    }
    for key, value in expected.items():
        assert provenance[key] == value

    scientific = plan["scientific_closure"]
    assert scientific["v2_role"] == "instrument_aware_realism_simulation_supplement"
    assert set(scientific["supplements_original_result_lanes"]) == {
        "engineering_logic",
        "baseline_simulation_outputs",
    }
    assert scientific["credibility_function"] == (
        "adds_reality_biased_instrument_route_prior_constraints_without_measured_data"
    )


def test_v2_closure_validation_fails_closed_for_forbidden_drift():
    broken = copy.deepcopy(rv2.load_v2_no_measured_data_closure_plan())
    broken["authorization_boundary"]["operator_artifact_acquisition_authorized"] = True
    with pytest.raises(ValueError):
        rv2.validate_v2_no_measured_data_closure_plan(broken)

    broken = copy.deepcopy(rv2.load_v2_no_measured_data_closure_plan())
    broken["route_governance_closure"]["main_660_redefinition_authorized"] = True
    with pytest.raises(ValueError):
        rv2.validate_v2_no_measured_data_closure_plan(broken)

    broken = copy.deepcopy(rv2.load_v2_no_measured_data_closure_plan())
    broken["claim_boundaries"]["event_probability_claim_level"] = "calibrated_absolute"
    with pytest.raises(ValueError):
        rv2.validate_v2_no_measured_data_closure_plan(broken)

    broken = copy.deepcopy(rv2.load_v2_no_measured_data_closure_plan())
    broken["closure_design"]["forbidden_actions"].remove("route_promotion")
    with pytest.raises(ValueError):
        rv2.validate_v2_no_measured_data_closure_plan(broken)


def test_v2_closure_generation_requires_exact_self_authorization(tmp_path):
    with pytest.raises(ValueError, match="exact self authorization"):
        rv2.run_v2_no_measured_data_closure(
            output_dir=tmp_path,
            self_authorization="PASS_TO_R8",
            write_root_manifest=False,
        )


def test_v2_closure_outputs_required_files_and_final_decision():
    assert V2_CLOSURE_DIR.exists()
    files = {
        p.name
        for p in V2_CLOSURE_DIR.iterdir()
        if p.is_file() and not p.name.startswith("._")
    }
    assert files == rv2.V2_CLOSURE_REQUIRED_OUTPUTS

    manifest = _csv_rows(V2_CLOSURE_DIR / "v2_no_measured_data_closure_manifest.csv")[0]
    assert manifest["v2_no_measured_data_closure_run"] == "True"
    assert manifest["closure_decision"] == (
        "V2_CLOSED_NO_MEASURED_DATA_SYNTHETIC_PRIOR_MODEL_ONLY"
    )
    assert manifest["selected_future_recommendation_class"] == (
        "hold_v2_closed_pending_separate_post_v2_validation_program"
    )
    assert int(manifest["new_case_rows_added"]) == 0
    assert int(manifest["new_experiments_started"]) == 0
    assert manifest["operator_artifact_acquisition_started"] == "False"
    assert manifest["R8_plan_preparation_authorized"] == "False"
    assert manifest["R8_execution_authorized"] == "False"


def test_v2_closure_outputs_preserve_claims_routes_and_gaps():
    claims = _csv_rows(V2_CLOSURE_DIR / "v2_final_claim_boundary_summary.csv")
    claim_map = {row["claim_boundary"]: row for row in claims}
    assert claim_map["v2_role"]["value"] == (
        "instrument_aware_realism_simulation_supplement"
    )
    assert claim_map["model_class"]["value"] == "synthetic_relative_prior_model"
    assert claim_map["measured_data_used"]["value"] == "False"
    assert claim_map["SNR_claim_level"]["value"] == "absolute_blocked"
    assert claim_map["event_probability_claim_level"]["value"] == "absolute_blocked"
    assert claim_map["p_detect_mapping_claim_level"]["value"] == "relative_with_priors"
    assert claim_map["calibrated_or_absolute_claims"]["authorized"] == "False"

    route_rows = _csv_rows(V2_CLOSURE_DIR / "v2_route_governance_closure_summary.csv")
    route_map = {row["closure_item"]: row for row in route_rows}
    assert route_map["locked_main_660_routes"]["value"] == (
        "660_800x1400;660_800x1500"
    )
    assert route_map["context_routes"]["authorized_change"] == "False"
    assert route_map["optional_660_900x1400"]["status"] == (
        "closed_no_main_redefinition"
    )
    assert route_map["selected_annulus"]["authorized_change"] == "False"

    gaps = _csv_rows(V2_CLOSURE_DIR / "v2_artifact_gap_closure_register.csv")
    assert {row["artifact_id"] for row in gaps} == rv2.R7_2_REQUIRED_ARTIFACT_IDS
    for row in gaps:
        assert row["v2_gap_status"] == (
            "registered_post_v2_dependency_not_resolved_in_v2"
        )
        assert row["gap_resolution_authorized_in_v2"] == "False"
        assert row["operator_artifact_acquisition_started"] == "False"
        assert row["bench_measurement_started"] == "False"
        assert row["experiment_started"] == "False"
        assert row["solver_case_started"] == "False"


def test_v2_closure_manifest_guardrails_and_headers_are_clean():
    run_manifest = json.loads(
        (V2_CLOSURE_DIR / "run_manifest.json").read_text(encoding="utf-8")
    )
    assert run_manifest["run_id"] == "EV_NODI_realism_v2_no_measured_data_closure"
    assert run_manifest["v2_no_measured_data_closure_run"] is True
    assert run_manifest["closure_decision"] == (
        "V2_CLOSED_NO_MEASURED_DATA_SYNTHETIC_PRIOR_MODEL_ONLY"
    )
    assert run_manifest["operator_artifact_acquisition_started"] is False
    assert run_manifest["bench_measurement_started"] is False
    assert run_manifest["experimental_validation_started"] is False
    assert run_manifest["R8_plan_preparation_authorized"] is False
    assert run_manifest["R8_execution_authorized"] is False
    assert run_manifest["context_route_promotion_authorized"] is False
    assert run_manifest["main_660_redefinition_authorized"] is False
    assert run_manifest["calibrated_SNR_claim_emitted"] is False
    assert run_manifest["calibrated_event_probability_claim_emitted"] is False
    assert run_manifest["absolute_LOD_or_true_concentration_claim_emitted"] is False
    assert run_manifest["biological_specificity_claim_emitted"] is False

    guards = _csv_rows(V2_CLOSURE_DIR / "v2_forbidden_scope_guardrail_summary.csv")
    assert {row["triggered"] for row in guards} == {"False"}
    assert {row["status"] for row in guards} == {"pass"}
    guard_tokens = {row["guardrail"] for row in guards}
    assert {
        "calibrated_SNR_or_event_probability_claim",
        "absolute_LOD_or_true_concentration_claim",
        "biological_specificity_claim",
    } <= guard_tokens

    for path in V2_CLOSURE_DIR.glob("*.csv"):
        if path.name.startswith("._"):
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            header = next(csv.reader(handle))
        assert "detector_SNR" not in header
        assert "calibrated_detector_SNR" not in header
