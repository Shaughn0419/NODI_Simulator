from __future__ import annotations

from nodi_simulator.sidewall_route_accepted_evidence_smoke import (
    build_route_accepted_evidence_smoke,
)
from tests.test_sidewall_detector_blank_transfer_intake import _panel_rows
from tests.test_sidewall_wet_surface_observation_intake import _contract_rows


def _binder_rows() -> list[dict[str, str]]:
    return [
        {
            "route_candidate_id": "ROUTE-CAND-001",
            "route_geometry_family": "ideal_rectangle",
            "qch_sidecar_id": "QCH-CAND-001",
            "qch_status": "formal_qch_input_ready_not_route_score",
            "q_ch_m3_s": "1.2e-16",
            "formal_flow_split_fraction": "0.6",
        },
        {
            "route_candidate_id": "ROUTE-CAND-002",
            "route_geometry_family": "trapezoid_tapered_sidewalls",
            "qch_sidecar_id": "QCH-CAND-002",
            "qch_status": "formal_qch_input_ready_not_route_score",
            "q_ch_m3_s": "8e-17",
            "formal_flow_split_fraction": "0.4",
        },
    ]


def test_accepted_evidence_smoke_opens_formula_component_vector_without_claims() -> None:
    detector_fixture, wet_fixture, smoke_rows, dry_run_rows = build_route_accepted_evidence_smoke(
        detector_panel_matrix_rows=_panel_rows(),
        wet_contract_rows=_contract_rows(),
        qch_detector_wet_binder_rows=_binder_rows(),
    )

    assert len(detector_fixture) == 2
    assert len(wet_fixture) == 14
    assert len(smoke_rows) == 2
    assert len(dry_run_rows) == 2
    assert {row.fixture_not_evidence for row in smoke_rows} == {True}
    assert {row.route_formula_ready_for_claim_review for row in smoke_rows} == {True}
    assert {row.component_vector_ready_for_policy_review for row in smoke_rows} == {True}
    assert {row.route_score_current for row in smoke_rows} == {False}
    assert {row.yield_current for row in smoke_rows} == {False}
    assert {row.detection_probability_current for row in smoke_rows} == {False}
    assert {row["route_formula_review_dry_run_status"] for row in dry_run_rows} == {
        "route_formula_component_vector_ready_for_policy_review_not_scored"
    }


def test_smoke_fixture_rows_are_explicitly_not_evidence() -> None:
    detector_fixture, wet_fixture, smoke_rows, _dry = build_route_accepted_evidence_smoke(
        detector_panel_matrix_rows=_panel_rows(),
        wet_contract_rows=_contract_rows(),
        qch_detector_wet_binder_rows=_binder_rows(),
    )

    assert {row["fixture_not_evidence"] for row in detector_fixture} == {"true"}
    assert {row["fixture_not_evidence"] for row in wet_fixture} == {"true"}
    assert all("fixture_not_evidence" in row.hard_fail_if for row in smoke_rows)
