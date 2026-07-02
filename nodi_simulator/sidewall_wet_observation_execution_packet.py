"""Execution packet for closing sidewall wet observation evidence blockers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_VERSION = (
    "sidewall_wet_observation_execution_packet_v1"
)
SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_CLAIM_BOUNDARY = (
    "wet_observation_execution_packet_not_yield_not_wet_pass_not_detection"
)
WET_OBSERVATION_EXECUTION_PACKET_READY_STATUS = (
    "wet_observation_execution_packet_ready_observation_rows_required"
)


@dataclass(frozen=True)
class SidewallWetObservationExecutionRow:
    execution_row_id: str
    packet_version: str
    lane: str
    source_artifact_id: str
    source_disposition: str
    source_head: str
    current_status: str
    contract_or_fixture_rows: int
    current_accepted_observation_rows: int
    wet_pass_probability_current: bool
    clogging_rate_current: bool
    time_to_clog_current: bool
    recovery_current: bool
    yield_current: bool
    detection_probability_current: bool
    route_score_current: bool
    next_required_evidence: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallWetObservationClaimGuardRow:
    guard_row_id: str
    packet_version: str
    promotion_target: str
    implementation_authorized: bool
    fixture_or_contract_available: bool
    claim_promoted_current: bool
    claim_promotion_allowed_now: bool
    required_evidence_before_true: str
    hard_fail_if_missing_evidence: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_wet_observation_execution_packet(
    *,
    contract_status: Mapping[str, Any],
    intake_status: Mapping[str, Any],
    validation_status: Mapping[str, Any],
    promotion_status: Mapping[str, Any],
    wet_optical_status: Mapping[str, Any],
    readiness_status: Mapping[str, Any],
) -> tuple[list[SidewallWetObservationExecutionRow], list[SidewallWetObservationClaimGuardRow]]:
    rows = [
        _row(
            lane="wet_surface_contract",
            status=contract_status,
            current_status="contract_ready_no_wet_validation",
            contract_or_fixture_rows=_int(contract_status.get("contract_rows")),
            accepted_rows=0,
            next_required_evidence=(
                "route-bound wet endpoint observations for passability, clogging, "
                "time-to-clog, recovery, yield, controls, uncertainty, and hashes"
            ),
            hard_fail_if="wet_claim_true_from_contract_only",
        ),
        _row(
            lane="wet_observation_intake",
            status=intake_status,
            current_status="intake_schema_ready_no_observations",
            contract_or_fixture_rows=_int(intake_status.get("template_rows")),
            accepted_rows=_int(intake_status.get("accepted_observation_rows")),
            next_required_evidence=(
                "accepted observation rows with geometry match, controls, replicates, "
                "uncertainty, preregistration, and source hashes"
            ),
            hard_fail_if="yield_or_wet_pass_true_from_intake_schema_only",
        ),
        _row(
            lane="validator_hardening",
            status=validation_status,
            current_status="validator_ready_fixture_only_not_current_observations",
            contract_or_fixture_rows=_int(validation_status.get("accepted_fixture_rows")),
            accepted_rows=0,
            next_required_evidence=(
                "run real sidewall wet observations through hardened validator; "
                "fixtures cannot satisfy yield or wet pass"
            ),
            hard_fail_if="fixture_observation_promoted_as_current_wet_evidence",
        ),
        _row(
            lane="integrated_promotion_ledger",
            status=promotion_status,
            current_status="promotion_ledger_refreshed_but_wet_claim_false",
            contract_or_fixture_rows=_int(promotion_status.get("refreshed_promotion_lane_rows")),
            accepted_rows=0,
            next_required_evidence="promotion lane update after accepted wet observations",
            hard_fail_if="promotion_ledger_sets_yield_without_accepted_wet_observation",
        ),
        _row(
            lane="wet_optical_detection_context",
            status=wet_optical_status,
            current_status="nearest_geometry_context_available_not_sidewall_specific_wet",
            contract_or_fixture_rows=_int(wet_optical_status.get("evidence_context_rows")),
            accepted_rows=0,
            next_required_evidence=(
                "sidewall-specific or validated-transfer wet evidence for both "
                "rectangle and trapezoid route candidates"
            ),
            hard_fail_if="wet_context_promoted_as_sidewall_specific_observation",
        ),
        _row(
            lane="route_readiness_blocker",
            status=readiness_status,
            current_status="route_readiness_secondary_blocker_still_wet_observation",
            contract_or_fixture_rows=_int(readiness_status.get("board_rows")),
            accepted_rows=0,
            next_required_evidence="resolve wet_observation blocker for route/yield/detection board",
            hard_fail_if="route_score_or_yield_true_while_wet_observation_blocker_present",
        ),
    ]
    return rows, _claim_guard_rows(rows)


def _row(
    *,
    lane: str,
    status: Mapping[str, Any],
    current_status: str,
    contract_or_fixture_rows: int,
    accepted_rows: int,
    next_required_evidence: str,
    hard_fail_if: str,
) -> SidewallWetObservationExecutionRow:
    return SidewallWetObservationExecutionRow(
        execution_row_id=f"WET-OBS-EXEC-{lane}",
        packet_version=SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_VERSION,
        lane=lane,
        source_artifact_id=str(status.get("artifact_id", "")),
        source_disposition=str(status.get("disposition", "")),
        source_head=str(status.get("current_head", "")),
        current_status=current_status,
        contract_or_fixture_rows=contract_or_fixture_rows,
        current_accepted_observation_rows=accepted_rows,
        wet_pass_probability_current=False,
        clogging_rate_current=False,
        time_to_clog_current=False,
        recovery_current=False,
        yield_current=False,
        detection_probability_current=False,
        route_score_current=False,
        next_required_evidence=next_required_evidence,
        hard_fail_if=hard_fail_if,
        claim_boundary=SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_CLAIM_BOUNDARY,
    )


def _claim_guard_rows(
    rows: list[SidewallWetObservationExecutionRow],
) -> list[SidewallWetObservationClaimGuardRow]:
    fixture_or_contract_available = any(row.contract_or_fixture_rows > 0 for row in rows)
    specs = [
        (
            "wet_pass_probability",
            "accepted sidewall wet observations with controls, replicates, and uncertainty",
            "wet_pass_probability_true_without_accepted_wet_observations",
        ),
        (
            "clogging_rate_time_to_clog_recovery",
            "time-resolved wet observations or validated transfer model with denominators",
            "clogging_or_recovery_true_without_time_resolved_wet_evidence",
        ),
        (
            "yield",
            "accepted wet evidence plus detector/blank and route policy packets",
            "yield_true_without_wet_and_detector_blank_evidence",
        ),
        (
            "detection_probability",
            "wet evidence may inform detection only after detector/blank packet passes",
            "detection_probability_true_from_wet_observation_only",
        ),
        (
            "route_score_winner_JRC",
            "wet, detector/blank, flow/q_ch, and route formula packets",
            "route_score_true_without_wet_observation_packet",
        ),
    ]
    return [
        SidewallWetObservationClaimGuardRow(
            guard_row_id=f"WET-OBS-GUARD-{target}",
            packet_version=SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_VERSION,
            promotion_target=target,
            implementation_authorized=True,
            fixture_or_contract_available=fixture_or_contract_available,
            claim_promoted_current=False,
            claim_promotion_allowed_now=False,
            required_evidence_before_true=required,
            hard_fail_if_missing_evidence=hard_fail,
            claim_boundary=SIDEWALL_WET_OBSERVATION_EXECUTION_PACKET_CLAIM_BOUNDARY,
        )
        for target, required, hard_fail in specs
    ]


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if value is None or str(value).strip() == "":
        return 0
    return int(float(str(value)))
