from __future__ import annotations

from nodi_simulator.sidewall_wet_surface_contract import WET_SURFACE_ENDPOINTS
from nodi_simulator.sidewall_wet_surface_observation_intake import (
    OBSERVATION_ACCEPTED_STATUS,
    OBSERVATION_MISSING_STATUS,
    ROUTE_MATRIX_ACCEPTED_STATUS,
    ROUTE_MATRIX_NO_OBSERVATIONS_STATUS,
    SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_CLAIM_BOUNDARY,
    build_wet_surface_observation_intake,
    wet_surface_observation_promotion_update_rows,
    wet_surface_observation_template_rows,
)


def _contract_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for route_id, case_id, qch_id in (
        ("ROUTE-CAND-001", "rectangle_limit_theta90_D900_W500", "QCH-CAND-001"),
        ("ROUTE-CAND-002", "taper_theta85_D900_W500", "QCH-CAND-002"),
    ):
        for endpoint in WET_SURFACE_ENDPOINTS:
            rows.append(
                {
                    "route_candidate_id": route_id,
                    "route_key": f"route_{case_id}",
                    "source_case_id": case_id,
                    "qch_sidecar_id": qch_id,
                    "endpoint_id": endpoint["endpoint_id"],
                    "target_claim": endpoint["target_claim"],
                    "required_artifact_class": endpoint["required_artifact_class"],
                    "required_fields": endpoint["required_fields"],
                    "minimum_controls": endpoint["minimum_controls"],
                    "hard_fail_if_missing": endpoint["hard_fail_if_missing"],
                }
            )
    return rows


def _accepted_observations_for_route(route_id: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for contract in _contract_rows():
        if contract["route_candidate_id"] != route_id:
            continue
        endpoint_id = contract["endpoint_id"]
        prereg = (
            "pre_registered"
            if endpoint_id in {"wet_pass_probability", "yield_bridge", "clogging_time_series"}
            else "not_required_for_endpoint"
        )
        replicate_count = "1" if endpoint_id in {"material_surface_identity", "ev_sample_panel"} else "3"
        uncertainty = (
            "uncertainty_interval_missing"
            if endpoint_id in {"material_surface_identity", "ev_sample_panel"}
            else "uncertainty_interval_present"
        )
        rows.append(
            {
                "route_candidate_id": route_id,
                "endpoint_id": endpoint_id,
                "observation_artifact_id": f"OBS-{route_id}-{endpoint_id}",
                "observation_artifact_class": contract["required_artifact_class"],
                "observation_source_artifact": f"wet/{route_id}/{endpoint_id}.csv",
                "observation_source_sha256": "a" * 64,
                "source_geometry_match_level": "sidewall_specific",
                "provided_fields": contract["required_fields"],
                "controls_status": "controls_pass",
                "replicate_count": replicate_count,
                "uncertainty_interval_status": uncertainty,
                "pre_registered_rule_status": prereg,
            }
        )
    return rows


def test_wet_surface_observation_intake_defaults_to_missing_no_claims() -> None:
    intake_rows, matrix_rows = build_wet_surface_observation_intake(
        contract_rows=_contract_rows()
    )

    assert len(intake_rows) == 14
    assert len(matrix_rows) == 2
    assert {row.observation_validation_status for row in intake_rows} == {
        OBSERVATION_MISSING_STATUS
    }
    assert {row.route_wet_observation_matrix_status for row in matrix_rows} == {
        ROUTE_MATRIX_NO_OBSERVATIONS_STATUS
    }
    for row in intake_rows:
        assert row.accepted_observation_current is False
        assert row.target_claim_current is False
        assert row.yield_current is False
        assert row.detection_probability_current is False
        assert row.claim_boundary == SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_CLAIM_BOUNDARY


def test_wet_surface_observation_intake_can_accept_complete_sidewall_bundle() -> None:
    intake_rows, matrix_rows = build_wet_surface_observation_intake(
        contract_rows=[
            row for row in _contract_rows() if row["route_candidate_id"] == "ROUTE-CAND-002"
        ],
        observation_rows=_accepted_observations_for_route("ROUTE-CAND-002"),
    )

    assert len(intake_rows) == len(WET_SURFACE_ENDPOINTS)
    assert {row.observation_validation_status for row in intake_rows} == {
        OBSERVATION_ACCEPTED_STATUS
    }
    assert len(matrix_rows) == 1
    matrix = matrix_rows[0]
    assert matrix.route_wet_observation_matrix_status == ROUTE_MATRIX_ACCEPTED_STATUS
    assert matrix.accepted_endpoint_count == len(WET_SURFACE_ENDPOINTS)
    assert matrix.yield_current is False
    assert matrix.route_score_current is False
    assert matrix.detection_probability_current is False


def test_wet_surface_template_and_promotion_update_are_non_claim() -> None:
    templates = wet_surface_observation_template_rows(_contract_rows())
    _intake_rows, matrix_rows = build_wet_surface_observation_intake(
        contract_rows=_contract_rows()
    )
    updates = wet_surface_observation_promotion_update_rows(matrix_rows)

    assert len(templates) == 14
    assert templates[0]["observation_artifact_id"] == ""
    assert len(updates) == 1
    update = updates[0]
    assert update["target_ledger_lane"] == "wet_wall_interaction"
    assert update["target_claim_current"] is False
    assert "yield" in update["blocked_promotion"]
    assert "detection_probability" in update["blocked_promotion"]
    assert update["claim_boundary"] == SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_CLAIM_BOUNDARY
