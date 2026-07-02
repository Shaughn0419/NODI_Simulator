from __future__ import annotations

from nodi_simulator.sidewall_detector_wet_evidence_activation_runner import (
    build_detector_wet_evidence_activation_runner,
)
from tests.test_sidewall_detector_blank_transfer_intake import (
    _complete_transfer_row,
    _panel_rows,
)
from tests.test_sidewall_wet_surface_observation_intake import (
    _accepted_observations_for_route,
    _contract_rows,
)


def test_activation_runner_defaults_to_detector_wet_blocked() -> None:
    rows, contracts = build_detector_wet_evidence_activation_runner(
        detector_panel_matrix_rows=_panel_rows(),
        wet_contract_rows=_contract_rows(),
    )

    assert len(rows) == 2
    assert len(contracts) == 2
    assert {row.detector_branch_ready_for_formula for row in rows} == {False}
    assert {row.wet_branch_ready_for_formula for row in rows} == {False}
    assert {row.combined_detector_wet_ready_for_formula for row in rows} == {False}
    assert {row.route_score_current for row in rows} == {False}
    assert {row.yield_current for row in rows} == {False}
    assert {row.detection_probability_current for row in rows} == {False}


def test_activation_runner_accepts_complete_detector_and_wet_inputs_for_one_route() -> None:
    rows, _contracts = build_detector_wet_evidence_activation_runner(
        detector_panel_matrix_rows=_panel_rows(),
        wet_contract_rows=_contract_rows(),
        detector_transfer_input_rows=[_complete_transfer_row(route_candidate_id="ROUTE-CAND-002")],
        wet_observation_input_rows=_accepted_observations_for_route("ROUTE-CAND-002"),
        detector_input_present=True,
        wet_input_present=True,
    )

    by_route = {row.route_candidate_id: row for row in rows}
    assert by_route["ROUTE-CAND-002"].detector_branch_ready_for_formula is True
    assert by_route["ROUTE-CAND-002"].wet_branch_ready_for_formula is True
    assert by_route["ROUTE-CAND-002"].combined_detector_wet_ready_for_formula is True
    assert by_route["ROUTE-CAND-002"].route_score_current is False
    assert by_route["ROUTE-CAND-002"].yield_current is False
    assert by_route["ROUTE-CAND-002"].detection_probability_current is False
    assert by_route["ROUTE-CAND-001"].combined_detector_wet_ready_for_formula is False
