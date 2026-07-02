"""Execution packet for closing the detector/blank transfer evidence blocker."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_DETECTOR_BLANK_TRANSFER_EXECUTION_PACKET_VERSION = (
    "sidewall_detector_blank_transfer_execution_packet_v1"
)
SIDEWALL_DETECTOR_BLANK_TRANSFER_EXECUTION_PACKET_CLAIM_BOUNDARY = (
    "detector_blank_transfer_execution_packet_not_detection_probability_not_route_score"
)
DETECTOR_BLANK_TRANSFER_EXECUTION_PACKET_READY_STATUS = (
    "detector_blank_transfer_execution_packet_ready_evidence_rows_required"
)


@dataclass(frozen=True)
class SidewallDetectorBlankTransferExecutionRow:
    execution_row_id: str
    packet_version: str
    lane: str
    source_artifact_id: str
    source_disposition: str
    source_head: str
    current_status: str
    candidate_or_fixture_rows: int
    current_accepted_transfer_rows: int
    sidewall_specific_blank_trace_current: bool
    detector_response_validation_current: bool
    validated_transfer_current: bool
    detection_probability_current: bool
    route_score_current: bool
    yield_current: bool
    next_required_evidence: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallDetectorBlankTransferClaimGuardRow:
    guard_row_id: str
    packet_version: str
    promotion_target: str
    implementation_authorized: bool
    fixture_or_context_available: bool
    claim_promoted_current: bool
    claim_promotion_allowed_now: bool
    required_evidence_before_true: str
    hard_fail_if_missing_evidence: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_detector_blank_transfer_execution_packet(
    *,
    intake_status: Mapping[str, Any],
    validation_status: Mapping[str, Any],
    calibration_panel_status: Mapping[str, Any],
    promotion_ledger_status: Mapping[str, Any],
    readiness_board_status: Mapping[str, Any],
) -> tuple[
    list[SidewallDetectorBlankTransferExecutionRow],
    list[SidewallDetectorBlankTransferClaimGuardRow],
]:
    accepted_transfer_rows = _int(intake_status.get("accepted_transfer_rows"))
    rows = [
        _row(
            lane="transfer_intake",
            status=intake_status,
            current_status=(
                "accepted_detector_blank_transfer_candidate_ready_not_probability"
                if accepted_transfer_rows > 0
                else "schema_ready_no_current_transfer_evidence"
            ),
            candidate_or_fixture_rows=_int(intake_status.get("template_rows")),
            current_accepted_transfer_rows=accepted_transfer_rows,
            sidewall_specific_blank_trace_current=_bool(
                intake_status.get("sidewall_specific_blank_trace_current_rows")
            ),
            detector_response_validation_current=_bool(
                intake_status.get("detector_response_validation_current_rows")
            ),
            validated_transfer_current=_bool(
                intake_status.get("validated_transfer_current_rows")
            ),
            next_required_evidence=(
                "sidewall-specific or validated-transfer detector/blank rows with "
                "readout_path_id, ROI_policy_id, BFP_phase_policy, threshold_policy_id, "
                "blank denominator, uncertainty, and hashes"
            ),
            hard_fail_if="detection_probability_true_from_transfer_schema_only",
        ),
        _row(
            lane="validator_hardening",
            status=validation_status,
            current_status="validator_ready_fixture_only_not_current_transfer_evidence",
            candidate_or_fixture_rows=_int(validation_status.get("accepted_fixture_rows")),
            current_accepted_transfer_rows=0,
            sidewall_specific_blank_trace_current=False,
            detector_response_validation_current=False,
            validated_transfer_current=False,
            next_required_evidence=(
                "run real or validated-transfer rows through hardened validator; "
                "fixtures cannot satisfy route claims"
            ),
            hard_fail_if="fixture_row_promoted_as_current_detector_blank_transfer",
        ),
        _row(
            lane="calibration_panel",
            status=calibration_panel_status,
            current_status="candidate_panel_ready_not_sidewall_blank_or_detector_response",
            candidate_or_fixture_rows=_int(calibration_panel_status.get("panel_rows")),
            current_accepted_transfer_rows=0,
            sidewall_specific_blank_trace_current=_bool(
                calibration_panel_status.get("sidewall_specific_blank_trace_current")
            ),
            detector_response_validation_current=_bool(
                calibration_panel_status.get("detector_response_validation_current")
            ),
            validated_transfer_current=False,
            next_required_evidence=(
                "measured blank trace or validated transfer plus detector response "
                "operator consuming sidewall reference"
            ),
            hard_fail_if="panel_candidate_promoted_to_detector_response_validation",
        ),
        _row(
            lane="integrated_promotion_ledger",
            status=promotion_ledger_status,
            current_status="promotion_ledger_refreshed_but_detector_claim_false",
            candidate_or_fixture_rows=_int(
                promotion_ledger_status.get("refreshed_promotion_lane_rows")
            ),
            current_accepted_transfer_rows=0,
            sidewall_specific_blank_trace_current=False,
            detector_response_validation_current=False,
            validated_transfer_current=False,
            next_required_evidence=(
                "promotion lane update after accepted detector/blank transfer evidence"
            ),
            hard_fail_if="promotion_ledger_sets_detection_probability_without_accepted_transfer",
        ),
        _row(
            lane="route_readiness_blocker",
            status=readiness_board_status,
            current_status="route_readiness_primary_blocker_still_detector_blank_transfer",
            candidate_or_fixture_rows=_int(readiness_board_status.get("board_rows")),
            current_accepted_transfer_rows=0,
            sidewall_specific_blank_trace_current=False,
            detector_response_validation_current=False,
            validated_transfer_current=False,
            next_required_evidence=(
                "resolve detector_blank_transfer blocker for both rectangle and trapezoid routes"
            ),
            hard_fail_if="route_score_true_while_detector_blank_transfer_blocker_present",
        ),
    ]
    return rows, _claim_guard_rows(rows)


def _row(
    *,
    lane: str,
    status: Mapping[str, Any],
    current_status: str,
    candidate_or_fixture_rows: int,
    current_accepted_transfer_rows: int,
    sidewall_specific_blank_trace_current: bool,
    detector_response_validation_current: bool,
    validated_transfer_current: bool,
    next_required_evidence: str,
    hard_fail_if: str,
) -> SidewallDetectorBlankTransferExecutionRow:
    return SidewallDetectorBlankTransferExecutionRow(
        execution_row_id=f"DETECTOR-BLANK-EXEC-{lane}",
        packet_version=SIDEWALL_DETECTOR_BLANK_TRANSFER_EXECUTION_PACKET_VERSION,
        lane=lane,
        source_artifact_id=str(status.get("artifact_id", "")),
        source_disposition=str(status.get("disposition", "")),
        source_head=str(status.get("current_head", "")),
        current_status=current_status,
        candidate_or_fixture_rows=candidate_or_fixture_rows,
        current_accepted_transfer_rows=current_accepted_transfer_rows,
        sidewall_specific_blank_trace_current=sidewall_specific_blank_trace_current,
        detector_response_validation_current=detector_response_validation_current,
        validated_transfer_current=validated_transfer_current,
        detection_probability_current=False,
        route_score_current=False,
        yield_current=False,
        next_required_evidence=next_required_evidence,
        hard_fail_if=hard_fail_if,
        claim_boundary=SIDEWALL_DETECTOR_BLANK_TRANSFER_EXECUTION_PACKET_CLAIM_BOUNDARY,
    )


def _claim_guard_rows(
    rows: list[SidewallDetectorBlankTransferExecutionRow],
) -> list[SidewallDetectorBlankTransferClaimGuardRow]:
    fixture_available = any(row.candidate_or_fixture_rows > 0 for row in rows)
    specs = [
        (
            "sidewall_blank_false_positive_rate",
            "sidewall-specific blank traces or validated transferable blank model with blank denominator",
            "blank_fpr_true_without_sidewall_blank_or_validated_transfer",
        ),
        (
            "detector_response_validation",
            "detector operator, ROI/slit throughput, standard-particle calibration, and hashes",
            "detector_response_validation_true_without_calibration_packet",
        ),
        (
            "detection_probability",
            "accepted detector/blank transfer rows plus threshold policy and uncertainty",
            "detection_probability_true_without_accepted_detector_blank_transfer",
        ),
        (
            "route_score_winner_JRC",
            "detector/blank, wet, flow/q_ch, and route formula packets",
            "route_score_true_without_detector_blank_and_wet_evidence",
        ),
        (
            "yield_or_wet_pass",
            "wet observation bundle plus detector/blank transfer where detection is used",
            "yield_true_from_detector_blank_transfer_only",
        ),
    ]
    return [
        SidewallDetectorBlankTransferClaimGuardRow(
            guard_row_id=f"DETECTOR-BLANK-GUARD-{target}",
            packet_version=SIDEWALL_DETECTOR_BLANK_TRANSFER_EXECUTION_PACKET_VERSION,
            promotion_target=target,
            implementation_authorized=True,
            fixture_or_context_available=fixture_available,
            claim_promoted_current=False,
            claim_promotion_allowed_now=False,
            required_evidence_before_true=required,
            hard_fail_if_missing_evidence=hard_fail,
            claim_boundary=SIDEWALL_DETECTOR_BLANK_TRANSFER_EXECUTION_PACKET_CLAIM_BOUNDARY,
        )
        for target, required, hard_fail in specs
    ]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value > 0
    return str(value).strip().lower() in {"1", "true", "yes"}


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if value is None or str(value).strip() == "":
        return 0
    return int(float(str(value)))
