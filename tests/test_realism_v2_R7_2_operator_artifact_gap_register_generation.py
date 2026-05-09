from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


R7_2_DIR = rv2.DEFAULT_R7_2_OPERATOR_ARTIFACT_GAP_REGISTER_DIR


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_R7_2_generation_requires_exact_self_authorization(tmp_path):
    with pytest.raises(ValueError, match="exact self authorization"):
        rv2.run_R7_2_operator_artifact_gap_register_generation(
            output_dir=tmp_path,
            self_authorization="PASS_R7_2_PLAN_ONLY",
            write_root_manifest=False,
        )


def test_R7_2_outputs_required_files_only_and_do_not_acquire():
    assert R7_2_DIR.exists()
    files = {
        p.name
        for p in R7_2_DIR.iterdir()
        if p.is_file() and not p.name.startswith("._")
    }
    assert files == rv2.R7_2_REQUIRED_OUTPUTS_IF_AUTHORIZED

    manifest = _csv_rows(R7_2_DIR / "R7_2_operator_artifact_gap_manifest.csv")[0]
    assert manifest["R7_2_operator_artifact_gap_register_generation_run"] == "True"
    assert manifest["generation_type"] == (
        "artifact_gap_register_only_no_acquisition"
    )
    assert int(manifest["artifact_id_count"]) == 6
    assert int(manifest["required_artifact_field_count"]) == 30
    assert int(manifest["new_case_rows_added"]) == 0
    assert int(manifest["new_solver_cases_added"]) == 0
    assert int(manifest["new_experiments_started"]) == 0
    assert manifest["operator_artifact_acquisition_started"] == "False"
    assert manifest["bench_measurement_started"] == "False"
    assert manifest["experimental_validation_started"] == "False"
    assert manifest["R8_plan_preparation_authorized"] == "False"
    assert manifest["R8_execution_authorized"] == "False"


def test_R7_2_registry_and_per_artifact_files_are_plan_only():
    registry = _csv_rows(R7_2_DIR / "R7_2_artifact_gap_registry.csv")
    assert {row["artifact_id"] for row in registry} == rv2.R7_2_REQUIRED_ARTIFACT_IDS
    assert sum(int(row["required_field_count"]) for row in registry) == 30
    for row in registry:
        assert row["artifact_acceptance_criteria_defined"] == "True"
        assert row["artifact_failure_criteria_defined"] == "True"
        assert row["chain_of_custody_required"] == "True"
        assert row["post_v2_dependency_requires_separate_program_review"] == "True"
        assert row["gap_status"] == "registered_no_acquisition"
        assert row["gap_resolution_authorized"] == "False"
        assert row["bench_measurement_authorized"] == "False"
        assert row["experiment_authorized"] == "False"
        assert row["solver_case_authorized"] == "False"
        assert row["route_promotion_authorized"] == "False"
        assert row["main_660_redefinition_authorized"] == "False"
        assert row["uses_source_v1_relative_score_as_physical_input"] == "False"
        assert row["allows_route_specific_multiplier"] == "False"
        assert row["allows_particle_specific_fit"] == "False"

    artifact_files = [
        "R7_2_reference_operating_band_gap_register.csv",
        "R7_2_BFP_slit_ROI_alignment_gap_register.csv",
        "R7_2_fabrication_metrology_margin_gap_register.csv",
        "R7_2_wall_PEG_transport_proxy_gap_register.csv",
        "R7_2_particle_stratum_residual_gap_register.csv",
        "R7_2_optional_900_governance_gap_register.csv",
    ]
    total_rows = 0
    for filename in artifact_files:
        rows = _csv_rows(R7_2_DIR / filename)
        assert rows
        total_rows += len(rows)
        for row in rows:
            assert row["acceptance_criterion"] == (
                "field_defined_with_units_or_categorical_enum_and_provenance"
            )
            assert row["failure_criterion"] == (
                "missing_field_or_score_derived_substitute_or_unreviewed_manual_value"
            )
            assert row["chain_of_custody_required"] == "True"
            assert row["post_v2_dependency_requires_separate_program_review"] == "True"
            assert row["gap_status"] == "registered_no_acquisition"
            assert row["gap_resolution_authorized"] == "False"
            assert row["bench_measurement_authorized"] == "False"
            assert row["experiment_authorized"] == "False"
            assert row["solver_case_authorized"] == "False"
            assert row["route_promotion_authorized"] == "False"
            assert row["main_660_redefinition_authorized"] == "False"
            assert row["uses_source_v1_relative_score_as_physical_input"] == "False"
            assert row["allows_route_specific_multiplier"] == "False"
            assert row["allows_particle_specific_fit"] == "False"
    assert total_rows == 30


def test_R7_2_next_stage_is_bounded_run_plan_only():
    matrix = _csv_rows(R7_2_DIR / "R7_2_next_stage_recommendation_matrix.csv")
    selected = [
        row for row in matrix if row["R7_2_recommendation"] == "selected_for_future_review"
    ]
    assert len(selected) == 1
    assert selected[0]["future_recommendation_class"] == (
        "prepare_v2_no_measured_data_closure_only"
    )
    for row in matrix:
        assert row["authorizes_execution"] == "False"
        assert row["authorizes_acquisition"] == "False"
        assert row["authorizes_R8"] == "False"
        assert row["authorizes_experiment"] == "False"
        assert row["authorizes_solver_case"] == "False"
        assert row["authorizes_route_promotion"] == "False"
        assert row["authorizes_main_660_redefinition"] == "False"


def test_R7_2_run_manifest_preserves_no_execution_boundary():
    manifest = _csv_rows(R7_2_DIR / "R7_2_operator_artifact_gap_manifest.csv")[0]
    run_manifest = json.loads((R7_2_DIR / "run_manifest.json").read_text(encoding="utf-8"))

    assert manifest["selected_future_recommendation_class"] == (
        "prepare_v2_no_measured_data_closure_only"
    )
    assert manifest["plan_decision"] == (
        "operator_artifact_gaps_registered_prepare_v2_no_measured_data_closure_only"
    )
    assert run_manifest["run_id"] == (
        "EV_NODI_realism_v2_R7_2_operator_artifact_gap_register_generation"
    )
    assert run_manifest["R7_2_operator_artifact_gap_register_generation_run"] is True
    assert run_manifest["operator_artifact_acquisition_started"] is False
    assert run_manifest["bench_measurement_started"] is False
    assert run_manifest["experimental_validation_started"] is False
    assert run_manifest["R8_plan_preparation_authorized"] is False
    assert run_manifest["R8_execution_authorized"] is False
    assert run_manifest["context_route_promotion_authorized"] is False
    assert run_manifest["main_660_redefinition_authorized"] is False


def test_R7_2_claims_stops_and_headers_are_clean():
    claims = _csv_rows(R7_2_DIR / "R7_2_claim_boundary_guardrail_summary.csv")
    stops = _csv_rows(R7_2_DIR / "R7_2_stop_gate_summary.csv")

    claim_status = {row["guardrail"]: row for row in claims}
    assert claim_status["SNR_claim_level"]["value"] == "absolute_blocked"
    assert claim_status["event_probability_claim_level"]["value"] == "absolute_blocked"
    assert claim_status["p_detect_mapping_claim_level"]["value"] == "relative_with_priors"
    assert all(row["status"] == "pass" for row in claims)
    assert {row["triggered"] for row in stops} == {"False"}
    assert {row["status"] for row in stops} == {"pass"}

    for path in R7_2_DIR.glob("*.csv"):
        if path.name.startswith("._"):
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            header = next(csv.reader(handle))
        assert "detector_SNR" not in header
        assert "calibrated_detector_SNR" not in header
