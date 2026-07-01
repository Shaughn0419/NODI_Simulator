from __future__ import annotations

from nodi_simulator.route_yield_detection_candidate import (
    ROUTE_YIELD_DETECTION_CLAIM_BOUNDARY,
    build_route_yield_detection_candidates,
)


def _qch_rows() -> list[dict[str, str]]:
    return [
        {
            "qch_sidecar_id": "QCH-CAND-001",
            "qch_sidecar_status": "candidate_qch_sidecar_row",
            "route_key": "route_rectangle",
            "source_case_id": "rectangle_limit_theta90_D900_W500",
            "candidate_flow_split_fraction": "0.6",
        },
        {
            "qch_sidecar_id": "QCH-CAND-002",
            "qch_sidecar_status": "candidate_qch_sidecar_row",
            "route_key": "route_taper",
            "source_case_id": "taper_theta85_D900_W500",
            "candidate_flow_split_fraction": "0.4",
        },
    ]


def _pressure_rows(status: str = "context_only_not_formal_validation") -> list[dict[str, str]]:
    return [
        {"qch_sidecar_id": "QCH-CAND-001", "validation_status": status},
        {"qch_sidecar_id": "QCH-CAND-002", "validation_status": status},
    ]


def _formal_qch_rows() -> list[dict[str, str]]:
    return [
        {
            "qch_sidecar_id": "QCH-CAND-001",
            "qch_sidecar_status": "formal_qch_sidecar_from_exact_pressure_flow",
            "route_candidate_id": "ROUTE-CAND-001",
            "case_id": "rectangle_limit_theta90_D900_W500",
            "formal_flow_split_fraction": "0.61",
            "formal_qch_sidecar_current": "true",
        },
        {
            "qch_sidecar_id": "QCH-CAND-002",
            "qch_sidecar_status": "formal_qch_sidecar_from_exact_pressure_flow",
            "route_candidate_id": "ROUTE-CAND-002",
            "case_id": "taper_theta85_D900_W500",
            "formal_flow_split_fraction": "0.39",
            "formal_qch_sidecar_current": "true",
        },
    ]


def _binding_rows() -> list[dict[str, str]]:
    return [
        {
            "qch_sidecar_id": "QCH-CAND-001",
            "per_route_acceptance_status": "accepted_exact_pressure_flow_for_formal_qch_sidecar",
        },
        {
            "qch_sidecar_id": "QCH-CAND-002",
            "per_route_acceptance_status": "accepted_exact_pressure_flow_for_formal_qch_sidecar",
        },
    ]


def test_route_candidate_metric_uses_flow_split_and_context_weight() -> None:
    rows = build_route_yield_detection_candidates(_qch_rows(), _pressure_rows())

    assert [row.qch_sidecar_id for row in rows] == ["QCH-CAND-001", "QCH-CAND-002"]
    assert rows[0].pressure_flow_context_weight == 0.25
    assert rows[0].route_decision_candidate_metric == 0.15
    assert rows[1].route_decision_candidate_metric == 0.1
    assert rows[0].candidate_sort_index_under_context == 1
    assert rows[1].candidate_sort_index_under_context == 2


def test_formal_validation_candidate_uses_full_context_weight_without_claim_promotion() -> None:
    rows = build_route_yield_detection_candidates(
        _qch_rows(),
        _pressure_rows("formal_validation_candidate"),
    )

    assert rows[0].pressure_flow_context_weight == 1.0
    assert rows[0].route_decision_candidate_metric == 0.6
    assert rows[0].route_score_current is False
    assert rows[0].winner_current is False
    assert rows[0].JRC_current is False
    assert rows[0].yield_current is False
    assert rows[0].detection_probability_current is False


def test_formal_qch_sidecar_uses_exact_pressure_flow_weight_without_claim_promotion() -> None:
    rows = build_route_yield_detection_candidates(_formal_qch_rows(), _binding_rows())

    assert [row.route_candidate_id for row in rows] == ["ROUTE-CAND-001", "ROUTE-CAND-002"]
    assert rows[0].qch_sidecar_status == "formal_qch_sidecar_from_exact_pressure_flow"
    assert rows[0].pressure_flow_validation_status == (
        "exact_pressure_flow_formal_qch_sidecar_accepted"
    )
    assert rows[0].pressure_flow_context_weight == 1.0
    assert rows[0].candidate_flow_split_fraction == 0.61
    assert rows[0].route_decision_candidate_metric == 0.61
    assert rows[0].route_score_current is False
    assert rows[0].winner_current is False
    assert rows[0].JRC_current is False
    assert rows[0].yield_current is False
    assert rows[0].detection_probability_current is False


def test_route_candidate_rows_keep_wet_and_optical_evidence_explicit() -> None:
    rows = build_route_yield_detection_candidates(_qch_rows(), _pressure_rows())

    for row in rows:
        assert row.wet_evidence_status == "wet_ev_evidence_contract_missing"
        assert row.optical_detection_status == "optical_detection_calibration_missing"
        assert row.claim_boundary == ROUTE_YIELD_DETECTION_CLAIM_BOUNDARY
