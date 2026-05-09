from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from nodi_simulator import realism_v2 as rv2


R7_1_DIR = rv2.DEFAULT_R7_1_OPERATOR_ARTIFACT_VALIDATION_DIR


def _csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_R7_1_protocol_requires_exact_self_authorization(tmp_path):
    with pytest.raises(ValueError, match="exact self authorization"):
        rv2.run_R7_1_operator_artifact_validation_protocol_generation(
            output_dir=tmp_path,
            self_authorization="PASS_R7_1_PLAN_ONLY",
            write_root_manifest=False,
        )


def test_R7_1_protocol_outputs_required_files_only_and_do_not_execute():
    assert R7_1_DIR.exists()
    files = {
        p.name
        for p in R7_1_DIR.iterdir()
        if p.is_file() and not p.name.startswith("._")
    }
    assert files == rv2.R7_1_REQUIRED_OUTPUTS_IF_AUTHORIZED

    manifest = _csv_rows(R7_1_DIR / "R7_1_operator_artifact_validation_manifest.csv")[0]
    assert manifest["R7_1_operator_artifact_validation_protocol_generation_run"] == (
        "True"
    )
    assert manifest["generation_type"] == (
        "protocol_artifact_requirements_only_no_measurement"
    )
    assert int(manifest["evidence_module_count"]) == 6
    assert int(manifest["required_artifact_field_count"]) == 30
    assert int(manifest["new_case_rows_added"]) == 0
    assert int(manifest["new_solver_cases_added"]) == 0
    assert int(manifest["new_experiments_started"]) == 0
    assert manifest["operator_artifact_acquisition_started"] == "False"
    assert manifest["experimental_validation_started"] == "False"
    assert manifest["R8_plan_preparation_authorized"] == "False"
    assert manifest["R8_execution_authorized"] == "False"


def test_R7_1_protocol_files_are_requirements_not_measurements():
    protocol_files = [
        "R7_1_reference_operating_band_artifact_protocol.csv",
        "R7_1_BFP_slit_ROI_alignment_operator_artifact_protocol.csv",
        "R7_1_fabrication_metrology_margin_artifact_protocol.csv",
        "R7_1_wall_PEG_transport_proxy_validation_protocol.csv",
        "R7_1_particle_stratum_residual_validation_protocol.csv",
        "R7_1_optional_900_governance_protocol.csv",
    ]
    total_rows = 0
    for filename in protocol_files:
        rows = _csv_rows(R7_1_DIR / filename)
        assert rows
        total_rows += len(rows)
        for row in rows:
            assert row["field_required_before_physical_prior_use"] == "True"
            assert row["field_required_before_post_v2_validation_program"] == "True"
            assert row["authorizes_measurement"] == "False"
            assert row["authorizes_experiment"] == "False"
            assert row["authorizes_solver_case"] == "False"
            assert row["authorizes_route_promotion"] == "False"
            assert row["authorizes_main_660_redefinition"] == "False"
            assert row["uses_source_v1_relative_score_as_physical_input"] == "False"
            assert row["allows_route_specific_multiplier"] == "False"
            assert row["allows_particle_specific_fit"] == "False"
            assert row["protocol_status"] == "requirement_defined_not_executed"
    assert total_rows == 30


def test_R7_1_protocol_next_stage_is_plan_only():
    matrix = _csv_rows(R7_1_DIR / "R7_1_next_stage_recommendation_matrix.csv")
    selected = [
        row for row in matrix if row["R7_1_recommendation"] == "selected_for_future_review"
    ]
    assert len(selected) == 1
    assert selected[0]["future_recommendation_class"] == (
        "prepare_operator_artifact_gap_register_plan_only"
    )
    for row in matrix:
        assert row["authorizes_execution"] == "False"
        assert row["authorizes_R8"] == "False"
        assert row["authorizes_experiment"] == "False"
        assert row["authorizes_solver_case"] == "False"
        assert row["authorizes_route_promotion"] == "False"
        assert row["authorizes_main_660_redefinition"] == "False"


def test_R7_1_protocol_manifest_and_run_manifest_preserve_guardrails():
    manifest = _csv_rows(R7_1_DIR / "R7_1_operator_artifact_validation_manifest.csv")[0]
    run_manifest = json.loads((R7_1_DIR / "run_manifest.json").read_text(encoding="utf-8"))

    assert manifest["selected_future_recommendation_class"] == (
        "prepare_operator_artifact_gap_register_plan_only"
    )
    assert manifest["protocol_decision"] == (
        "operator_artifact_requirements_defined_prepare_gap_register_only"
    )
    for key in (
        "R8_plan_preparation_authorized",
        "R8_execution_authorized",
        "context_route_promotion_authorized",
        "main_660_redefinition_authorized",
    ):
        assert manifest[key] == "False"
        assert run_manifest[key] is False
    assert run_manifest["run_id"] == (
        "EV_NODI_realism_v2_R7_1_operator_artifact_validation_protocol_generation"
    )
    assert run_manifest[
        "R7_1_operator_artifact_validation_protocol_generation_run"
    ] is True
    assert run_manifest["operator_artifact_acquisition_started"] is False
    assert run_manifest["experimental_validation_started"] is False


def test_R7_1_protocol_claims_stops_and_headers_are_clean():
    claims = _csv_rows(R7_1_DIR / "R7_1_claim_boundary_guardrail_summary.csv")
    stops = _csv_rows(R7_1_DIR / "R7_1_stop_gate_summary.csv")

    claim_status = {row["guardrail"]: row for row in claims}
    assert claim_status["SNR_claim_level"]["value"] == "absolute_blocked"
    assert claim_status["event_probability_claim_level"]["value"] == "absolute_blocked"
    assert claim_status["p_detect_mapping_claim_level"]["value"] == "relative_with_priors"
    assert all(row["status"] == "pass" for row in claims)
    assert {row["triggered"] for row in stops} == {"False"}
    assert {row["status"] for row in stops} == {"pass"}

    for path in R7_1_DIR.glob("*.csv"):
        if path.name.startswith("._"):
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            header = next(csv.reader(handle))
        assert "detector_SNR" not in header
        assert "calibrated_detector_SNR" not in header
