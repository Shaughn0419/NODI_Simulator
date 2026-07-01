from __future__ import annotations

import pytest

from nodi_simulator.sidewall_pressure_flow_result_binder import (
    SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_CLAIM_BOUNDARY,
    bind_pressure_flow_external_results,
    build_external_result_template_rows,
    build_formal_qch_sidecar_rows,
    pressure_flow_result_promotion_update_rows,
)


def _request_rows() -> list[dict[str, str]]:
    return [
        {
            "validation_request_id": "PFV-REQUEST-ROUTE-CAND-001",
            "route_candidate_id": "ROUTE-CAND-001",
            "qch_sidecar_id": "QCH-CAND-001",
            "case_id": "rectangle_limit_theta90_D900_W500",
            "source_geometry_hash": "geom-rect",
            "required_validation_source": (
                "exact W500/D900 sidewall COMSOL pressure-flow run or matched measurement"
            ),
            "pressure_drop_Pa": "1000",
            "candidate_q_grid_m3_s": "6.0e-16",
            "candidate_flow_split_fraction": "0.6",
            "acceptance_ratio_min": "0.5",
            "acceptance_ratio_max": "2.0",
            "split_abs_delta_max": "0.05",
        },
        {
            "validation_request_id": "PFV-REQUEST-ROUTE-CAND-002",
            "route_candidate_id": "ROUTE-CAND-002",
            "qch_sidecar_id": "QCH-CAND-002",
            "case_id": "taper_theta85_D900_W500",
            "source_geometry_hash": "geom-taper",
            "required_validation_source": (
                "exact W500/D900 sidewall COMSOL pressure-flow run or matched measurement"
            ),
            "pressure_drop_Pa": "1000",
            "candidate_q_grid_m3_s": "4.0e-16",
            "candidate_flow_split_fraction": "0.4",
            "acceptance_ratio_min": "0.5",
            "acceptance_ratio_max": "2.0",
            "split_abs_delta_max": "0.05",
        },
    ]


def _external_results() -> list[dict[str, str]]:
    return [
        {
            "external_result_id": "PFV-EXT-001",
            "source_type": "comsol_pressure_flow",
            "validation_request_id": "PFV-REQUEST-ROUTE-CAND-001",
            "route_candidate_id": "ROUTE-CAND-001",
            "qch_sidecar_id": "QCH-CAND-001",
            "case_id": "rectangle_limit_theta90_D900_W500",
            "geometry_descriptor_sha256": "geom-rect",
            "model_or_measurement_id": "comsol_exact_w500_d900_rect",
            "mesh_or_instrument_resolution": "mesh4",
            "fluid_viscosity_Pa_s": "0.001",
            "channel_length_m": "0.001",
            "boundary_condition_id": "fixed_pressure_1000Pa",
            "pressure_drop_Pa": "1000",
            "q_total_m3_s": "6.0e-16",
            "q_upper_ports_m3_s": "3.0e-16",
            "q_lower_ports_m3_s": "3.0e-16",
            "port_balance_rel": "0.001",
            "quality_gate": "pass",
            "result_artifact_sha256": "result-sha-rect",
        },
        {
            "external_result_id": "PFV-EXT-002",
            "source_type": "comsol_pressure_flow",
            "validation_request_id": "PFV-REQUEST-ROUTE-CAND-002",
            "route_candidate_id": "ROUTE-CAND-002",
            "qch_sidecar_id": "QCH-CAND-002",
            "case_id": "taper_theta85_D900_W500",
            "geometry_descriptor_sha256": "geom-taper",
            "model_or_measurement_id": "comsol_exact_w500_d900_taper85",
            "mesh_or_instrument_resolution": "mesh4",
            "fluid_viscosity_Pa_s": "0.001",
            "channel_length_m": "0.001",
            "boundary_condition_id": "fixed_pressure_1000Pa",
            "pressure_drop_Pa": "1000",
            "q_total_m3_s": "4.0e-16",
            "q_upper_ports_m3_s": "2.0e-16",
            "q_lower_ports_m3_s": "2.0e-16",
            "port_balance_rel": "0.001",
            "quality_gate": "pass",
            "result_artifact_sha256": "result-sha-taper",
        },
    ]


def test_external_result_template_rows_preserve_required_contract() -> None:
    rows = build_external_result_template_rows(_request_rows())

    assert len(rows) == 2
    assert rows[0].external_result_status == "template_waiting_for_exact_external_result"
    assert "q_total_m3_s" in rows[0].required_external_result_fields
    assert "quality_gate" in rows[0].required_external_result_fields
    assert rows[0].claim_boundary == SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_CLAIM_BOUNDARY
    assert rows[0].port_balance_threshold_max == 0.01
    assert rows[0].q_total_reconciliation_threshold_max == 0.05


def test_missing_external_results_fail_closed_without_formal_qch() -> None:
    binding_rows = bind_pressure_flow_external_results(_request_rows(), [])
    formal_rows = build_formal_qch_sidecar_rows(binding_rows)
    updates = pressure_flow_result_promotion_update_rows(binding_rows, formal_rows)

    assert len(binding_rows) == 2
    assert {row.per_route_acceptance_status for row in binding_rows} == {
        "missing_external_result"
    }
    assert all(row.formal_qch_sidecar_current is False for row in binding_rows)
    assert formal_rows == []
    assert updates[0]["new_context_status"] == "exact_w500_d900_pressure_flow_result_missing_or_failed"
    assert updates[0]["formal_qch_sidecar_current"] == "false"


def test_exact_external_results_emit_formal_qch_sidecar_without_route_claims() -> None:
    binding_rows = bind_pressure_flow_external_results(_request_rows(), _external_results())
    formal_rows = build_formal_qch_sidecar_rows(binding_rows)
    updates = pressure_flow_result_promotion_update_rows(binding_rows, formal_rows)

    assert {row.per_route_acceptance_status for row in binding_rows} == {
        "accepted_exact_pressure_flow_for_formal_qch_sidecar"
    }
    assert len(formal_rows) == 2
    assert sum(row.formal_flow_split_fraction for row in formal_rows) == pytest.approx(1.0)
    assert formal_rows[0].q_ch_m3_s == pytest.approx(6.0e-16)
    assert formal_rows[0].formal_qch_sidecar_current is True
    assert formal_rows[0].formal_qch_weighting_current is False
    assert formal_rows[0].route_score_current is False
    assert formal_rows[0].winner_current is False
    assert formal_rows[0].yield_current is False
    assert formal_rows[0].detection_probability_current is False
    assert updates[0]["new_context_status"] == (
        "exact_w500_d900_pressure_flow_result_accepted_formal_qch_sidecar_ready"
    )
    assert updates[0]["target_claim_current"] == "false"


def test_geometry_mismatch_blocks_formal_qch() -> None:
    bad = _external_results()
    bad[0] = {**bad[0], "geometry_descriptor_sha256": "wrong"}
    binding_rows = bind_pressure_flow_external_results(_request_rows(), bad)

    assert binding_rows[0].per_route_acceptance_status == "mismatch_geometry_descriptor_sha256"
    assert build_formal_qch_sidecar_rows(binding_rows) == []


def test_single_accepted_binding_is_not_enough_for_formal_qch() -> None:
    binding_rows = bind_pressure_flow_external_results(_request_rows(), _external_results())
    single_binding = [binding_rows[0]]

    assert len(single_binding) == 1
    assert (
        single_binding[0].per_route_acceptance_status
        == "accepted_exact_pressure_flow_for_formal_qch_sidecar"
    )
    assert build_formal_qch_sidecar_rows(single_binding) == []


def test_quality_or_ratio_failures_block_formal_qch() -> None:
    quality_bad = _external_results()
    quality_bad[0] = {**quality_bad[0], "quality_gate": "fail"}
    quality_rows = bind_pressure_flow_external_results(_request_rows(), quality_bad)
    assert quality_rows[0].per_route_acceptance_status == "quality_gate_not_pass"

    ratio_bad = _external_results()
    ratio_bad[0] = {
        **ratio_bad[0],
        "q_total_m3_s": "6.0e-18",
        "q_upper_ports_m3_s": "3.0e-18",
        "q_lower_ports_m3_s": "3.0e-18",
    }
    ratio_rows = bind_pressure_flow_external_results(_request_rows(), ratio_bad)
    assert ratio_rows[0].per_route_acceptance_status == (
        "external_to_candidate_flow_ratio_failed"
    )
    assert build_formal_qch_sidecar_rows(ratio_rows) == []
