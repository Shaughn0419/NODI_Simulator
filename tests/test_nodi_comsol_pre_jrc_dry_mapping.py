from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from nodi_simulator.realism_v2_io import write_csv_rows
from tools.audits.build_nodi_comsol_pre_jrc_dry_mapping import (
    PASS_STATUS,
    build_pre_jrc_dry_mapping_payload,
    validate_pre_jrc_dry_mapping_payload,
    validate_pre_jrc_dry_mapping_rows,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _write_placeholder(path: Path) -> Path:
    path.write_text("placeholder\n", encoding="utf-8")
    return path


def test_pre_jrc_dry_mapping_payload_is_no_output_jrc(tmp_path: Path) -> None:
    prs_path = _write_placeholder(tmp_path / "prs.csv")
    eas_path = _write_placeholder(tmp_path / "eas.csv")
    geometry_path = _write_placeholder(tmp_path / "geometry.csv")
    prs_rows = [
        {
            "route_id_nodi": "404/W500/D900",
            "lambda_nm": "404",
            "W_nominal_nm": "500",
            "D_nm": "900",
            "NODI_view": "fixed_660_gold",
            "diameter_nm": "40",
            "aggregate_source_type": "edge_norm_primary",
        }
    ]
    eas_rows = [
        {
            "route_id_nodi": "404/W500/D900",
            "lambda_nm": "404",
            "W_nominal_nm": "500",
            "D_nm": "900",
            "NODI_view": "fixed_660_gold",
            "aperture_surrogate_mode": "nominal_width",
        }
    ]
    geometry_rows = [
        {
            "W_nominal_nm": "500.0",
            "D_nm": "900.0",
            "process_state": "nominal_smooth_geometry",
            "sidewall_deg": "85.0",
        }
    ]

    payload = build_pre_jrc_dry_mapping_payload(
        prs_rows=prs_rows,
        eas_rows=eas_rows,
        geometry_rows=geometry_rows,
        prs_path=prs_path,
        eas_path=eas_path,
        geometry_descriptor_path=geometry_path,
    )

    assert payload["status"] == PASS_STATUS
    assert payload["joint_route_class_generated"] is False
    assert payload["q_ch_weighting_performed"] is False
    assert payload["yield_computed"] is False
    assert payload["winner_selected"] is False
    assert payload["dry_mapping_row_count"] == 1
    dry_row = payload["dry_mapping_rows"][0]
    assert dry_row["future_joint_route_class_id"] == ""
    assert dry_row["future_joint_route_class_status"] == "BLOCKED_NOT_GENERATED_GATE1"
    assert dry_row["q_ch_weight"] == ""
    assert dry_row["yield"] == ""
    assert dry_row["winner"] == ""
    assert validate_pre_jrc_dry_mapping_payload(payload) == []


def test_pre_jrc_validator_rejects_generated_jrc_or_weighted_values() -> None:
    issues = validate_pre_jrc_dry_mapping_rows(
        coverage_rows=[
            {
                "gate1_mapping_status": "dry_map_keys_available",
            }
        ],
        mapping_rows=[
            {
                "future_joint_route_class_id": "JRC-001",
                "future_joint_route_class_status": "generated",
                "q_ch_weight": "0.1",
                "transported_position_distribution": "",
                "weighted_response": "",
                "yield": "",
                "winner": "",
                "detection_probability": "",
            }
        ],
        missing_rows=[
            {
                "scope": "future_jrc_field",
                "blocked_field": "joint_route_class_id",
            }
        ],
    )

    assert any("JRC id must be blank" in issue for issue in issues)
    assert any("JRC status drifted" in issue for issue in issues)
    assert any("q_ch_weight must remain blank" in issue for issue in issues)


def test_pre_jrc_cli_requires_confirm(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools/audits/build_nodi_comsol_pre_jrc_dry_mapping.py"),
            "--output-dir",
            str(tmp_path / "out"),
        ],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--confirm-dry-mapping-report" in result.stderr
    assert not (tmp_path / "out").exists()


def test_pre_jrc_writer_outputs_sidecars_only(tmp_path: Path) -> None:
    from tools.audits.build_nodi_comsol_pre_jrc_dry_mapping import (
        COVERAGE_FILENAME,
        MAPPING_ROWS_FILENAME,
        MISSING_REGISTER_FILENAME,
        REPORT_FILENAME,
        write_pre_jrc_dry_mapping_bundle,
    )

    prs_path = tmp_path / "prs.csv"
    eas_path = tmp_path / "eas.csv"
    geometry_path = tmp_path / "geometry.csv"
    write_csv_rows(
        prs_path,
        [
            {
                "response_surface_artifact_version": "NODI_POSITION_RESPONSE_SURFACE_V1",
                "row_scope": "response_surface_bin",
                "route_id_nodi": "404/W500/D900",
                "lambda_nm": 404,
                "W_nominal_nm": 500,
                "D_nm": 900,
                "NODI_view": "fixed_660_gold",
                "diameter_nm": 40,
                "particle_kind": "exosome_synthetic",
                "distribution_type": "edge_norm_1d",
                "row_kind": "base_bin",
                "aggregate_id": "",
                "bin_id": "edge_00",
                "edge_norm_min": 0,
                "edge_norm_max": 0.05,
                "x_norm_min": "",
                "x_norm_max": "",
                "z_norm_min": "",
                "z_norm_max": "",
                "aggregate_source_type": "edge_norm_primary",
                "n_seeds": 3,
                "n_events_total": 100,
                "n_events_bin": 100,
                "n_events_bin_per_seed_min": 33,
                "response_count_source_only_not_probability": 50,
                "sparse_bin_flag": "false",
                "sparse_bin_policy": "edge_primary_requires_min_100_events_per_bin",
                "bin_sample_status": "adequate",
                "decision_use_allowed": "true",
                "guardrail_status": "recommendation_eligible",
                "position_distribution_basis": "nodi_synthetic_initial_position",
                "flow_condition_id": "nodi_position_response_surface_v1_not_comsol_transport",
                "flow_condition_version": "none",
                "flow_condition_source_sha": "0" * 64,
                "flow_condition_scope": "nodi_response_surface_not_transport_distribution",
                "flow_condition_claim_boundary": "nodi_synthetic_position_response_not_transport_occupancy",
                "view_physical_independence_flag": "false",
                "not_comsol_transport_distribution": "true",
                "not_qch_weighted": "true",
                "not_yield": "true",
                "not_detection_probability": "true",
                "claim_boundary": "nodi_position_response_surface_conditional_optical_response_only",
                "source_artifact": "source.csv",
                "source_sha256": "a" * 64,
            }
        ],
    )
    write_csv_rows(
        eas_path,
        [
            {
                "aperture_artifact_version": "NODI_EFFECTIVE_APERTURE_SURROGATE_V1",
                "route_id_nodi": "404/W500/D900",
                "lambda_nm": 404,
                "W_nominal_nm": 500,
                "D_nm": 900,
                "NODI_view": "fixed_660_gold",
                "weighting_basis": "fullgrid_recommendation_eligible_rank_contract",
                "aperture_surrogate_mode": "nominal_width",
                "W_eff_surrogate_nm": 500,
                "delta_W_eff_surrogate_nm": 0,
                "source_geometry_descriptor_id": "descriptor",
                "source_geometry_descriptor_sha": "b" * 64,
                "descriptor_evidence_class": "nominal_surrogate_geometry_descriptor_not_measured_not_optical_solver",
                "rank_source": "rank.csv",
                "recommendation_eligible_rank_source": "recommendation_eligible_rank",
                "guardrail_status": "recommendation_eligible",
                "eta_selected_proxy_under_surrogate": 1,
                "eta_all_proxy_under_surrogate": 1,
                "rank_under_surrogate": 1,
                "rank_flip_flag": "false",
                "candidate_family_flip_flag": "false",
                "eta_selected_relative_change": 0,
                "eta_all_relative_change": 0,
                "guardrail_status_change_flag": "false",
                "W_eff_mode_sensitivity_class": "nominal_reference",
                "solver_contract_trigger_flag": "false",
                "solver_contract_trigger_reason": "",
                "not_true_W_eff": "true",
                "not_measured_geometry": "true",
                "not_optical_solver_output": "true",
                "not_fabrication_release": "true",
                "not_yield": "true",
                "not_winner": "true",
                "claim_boundary": "effective_aperture_surrogate_sensitivity_only",
                "source_artifact": "eas.csv",
                "source_sha256": "c" * 64,
            }
        ],
    )
    write_csv_rows(
        geometry_path,
        [
            {
                "W_nominal_nm": "500.0",
                "D_nm": "900.0",
                "process_state": "nominal_smooth_geometry",
                "sidewall_deg": "85.0",
            }
        ],
    )

    payload = write_pre_jrc_dry_mapping_bundle(
        prs_path=prs_path,
        eas_path=eas_path,
        geometry_descriptor_path=geometry_path,
        output_dir=tmp_path / "out",
    )

    assert payload["joint_route_class_generated"] is False
    assert (tmp_path / "out" / REPORT_FILENAME).exists()
    assert (tmp_path / "out" / COVERAGE_FILENAME).exists()
    assert (tmp_path / "out" / MAPPING_ROWS_FILENAME).exists()
    assert (tmp_path / "out" / MISSING_REGISTER_FILENAME).exists()
    assert not (tmp_path / "out" / "JOINT_ROUTE_CLASS.csv").exists()
