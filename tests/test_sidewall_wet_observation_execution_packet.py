from __future__ import annotations

from nodi_simulator.sidewall_wet_observation_execution_packet import (
    SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_CLAIM_BOUNDARY,
    build_wet_observation_execution_packet,
)


def _build():
    return build_wet_observation_execution_packet(
        contract_status={"artifact_id": "CONTRACT", "contract_rows": 14},
        intake_status={"artifact_id": "INTAKE", "template_rows": 14, "accepted_observation_rows": 0},
        validation_status={"artifact_id": "VALIDATION", "accepted_fixture_rows": 14},
        promotion_status={"artifact_id": "PROMOTION", "refreshed_promotion_lane_rows": 18},
        wet_optical_status={"artifact_id": "CONTEXT", "evidence_context_rows": 2},
        readiness_status={"artifact_id": "READY", "board_rows": 2},
    )


def test_wet_execution_packet_summarizes_contract_fixture_context_lanes() -> None:
    rows, guards = _build()

    assert len(rows) == 6
    assert len(guards) == 5
    assert {row.claim_boundary for row in rows} == {
        SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_CLAIM_BOUNDARY
    }
    assert sum(row.contract_or_fixture_rows for row in rows) == 64


def test_contract_schema_and_fixtures_do_not_count_as_current_wet_observations() -> None:
    rows, _guards = _build()

    assert {row.current_accepted_observation_rows for row in rows} == {0}
    assert {row.wet_pass_probability_current for row in rows} == {False}
    assert {row.clogging_rate_current for row in rows} == {False}
    assert {row.time_to_clog_current for row in rows} == {False}
    assert {row.recovery_current for row in rows} == {False}
    assert {row.yield_current for row in rows} == {False}


def test_claim_guards_require_accepted_wet_evidence_before_promotion() -> None:
    _rows, guards = _build()
    by_target = {row.promotion_target: row for row in guards}

    assert "accepted sidewall wet observations" in by_target[
        "wet_pass_probability"
    ].required_evidence_before_true
    assert by_target["yield"].hard_fail_if_missing_evidence == (
        "yield_true_without_wet_and_detector_blank_evidence"
    )
    for guard in guards:
        assert guard.implementation_authorized is True
        assert guard.fixture_or_contract_available is True
        assert guard.claim_promoted_current is False
        assert guard.claim_promotion_allowed_now is False
