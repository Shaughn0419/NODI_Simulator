"""Combined detector/blank and wet evidence activation runner."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping

from nodi_simulator.sidewall_detector_blank_transfer_intake import (
    ROUTE_MATRIX_ACCEPTED_STATUS as DETECTOR_TRANSFER_ACCEPTED_STATUS,
    build_detector_blank_transfer_intake,
)
from nodi_simulator.sidewall_wet_surface_observation_intake import (
    ROUTE_MATRIX_ACCEPTED_STATUS as WET_OBSERVATION_ACCEPTED_STATUS,
    build_wet_surface_observation_intake,
)


SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_VERSION = (
    "sidewall_detector_wet_evidence_activation_runner_v1"
)
SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_CLAIM_BOUNDARY = (
    "detector_wet_evidence_activation_runner_not_route_score_not_yield_not_detection"
)
SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_STATUS = (
    "detector_wet_evidence_activation_runner_ready_input_bound_no_current_claims"
)


@dataclass(frozen=True)
class SidewallDetectorWetEvidenceActivationRouteRow:
    activation_row_id: str
    activation_version: str
    route_candidate_id: str
    route_key: str
    source_case_id: str
    qch_sidecar_id: str
    detector_transfer_matrix_status: str
    detector_accepted_transfer_rows: int
    detector_branch_ready_for_formula: bool
    wet_observation_matrix_status: str
    wet_accepted_endpoint_count: int
    wet_required_endpoint_count: int
    wet_branch_ready_for_formula: bool
    combined_detector_wet_ready_for_formula: bool
    route_formula_blocker_status: str
    route_score_current: bool
    winner_current: bool
    JRC_current: bool
    yield_current: bool
    detection_probability_current: bool
    wet_pass_probability_current: bool
    production_ingestion_current: bool
    next_required_evidence: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallDetectorWetEvidenceActivationInputContractRow:
    contract_row_id: str
    activation_version: str
    input_name: str
    input_path: str
    input_present: bool
    required_for_branch: str
    accepted_status_required: str
    current_accepted_rows: int
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_detector_wet_evidence_activation_runner(
    *,
    detector_panel_matrix_rows: list[Mapping[str, Any]],
    wet_contract_rows: list[Mapping[str, Any]],
    detector_transfer_input_rows: list[Mapping[str, Any]] | None = None,
    wet_observation_input_rows: list[Mapping[str, Any]] | None = None,
    detector_input_present: bool = False,
    wet_input_present: bool = False,
    detector_input_path: str = "",
    wet_input_path: str = "",
    detector_artifact_root: str | Path | None = None,
    wet_artifact_root: str | Path | None = None,
) -> tuple[
    list[SidewallDetectorWetEvidenceActivationRouteRow],
    list[SidewallDetectorWetEvidenceActivationInputContractRow],
]:
    _detector_intake, detector_matrix = build_detector_blank_transfer_intake(
        panel_matrix_rows=detector_panel_matrix_rows,
        transfer_input_rows=detector_transfer_input_rows or [],
        artifact_root=detector_artifact_root,
    )
    _wet_intake, wet_matrix = build_wet_surface_observation_intake(
        contract_rows=wet_contract_rows,
        observation_rows=wet_observation_input_rows or [],
        artifact_root=wet_artifact_root,
    )
    detector_by_route = {
        row.route_candidate_id: row for row in detector_matrix
    }
    wet_by_route = {
        row.route_candidate_id: row for row in wet_matrix
    }
    route_ids = sorted(set(detector_by_route) | set(wet_by_route))
    rows = [
        _route_row(
            route_id=route_id,
            detector=detector_by_route.get(route_id),
            wet=wet_by_route.get(route_id),
        )
        for route_id in route_ids
    ]
    contracts = _input_contract_rows(
        detector_input_present=detector_input_present,
        wet_input_present=wet_input_present,
        detector_input_path=detector_input_path,
        wet_input_path=wet_input_path,
        detector_accepted=sum(row.detector_accepted_transfer_rows for row in rows),
        wet_accepted=sum(row.wet_accepted_endpoint_count for row in rows),
    )
    return rows, contracts


def _route_row(
    *,
    route_id: str,
    detector: Any,
    wet: Any,
) -> SidewallDetectorWetEvidenceActivationRouteRow:
    detector_status = (
        detector.route_transfer_matrix_status
        if detector is not None
        else "detector_blank_transfer_missing"
    )
    wet_status = (
        wet.route_wet_observation_matrix_status
        if wet is not None
        else "wet_observation_missing"
    )
    detector_accepted = (
        detector.accepted_transfer_count if detector is not None else 0
    )
    wet_accepted = wet.accepted_endpoint_count if wet is not None else 0
    wet_required = wet.endpoint_count if wet is not None else 0
    detector_ready = detector_status == DETECTOR_TRANSFER_ACCEPTED_STATUS
    wet_ready = wet_status == WET_OBSERVATION_ACCEPTED_STATUS
    combined_ready = detector_ready and wet_ready
    return SidewallDetectorWetEvidenceActivationRouteRow(
        activation_row_id=f"DETECTOR-WET-ACTIVATION-{route_id}",
        activation_version=SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_VERSION,
        route_candidate_id=route_id,
        route_key=str(
            (detector.route_key if detector is not None else "")
            or (wet.route_key if wet is not None else "")
        ),
        source_case_id=str(
            (detector.source_case_id if detector is not None else "")
            or (wet.source_case_id if wet is not None else "")
        ),
        qch_sidecar_id=str(
            (detector.qch_sidecar_id if detector is not None else "")
            or (wet.qch_sidecar_id if wet is not None else "")
        ),
        detector_transfer_matrix_status=detector_status,
        detector_accepted_transfer_rows=detector_accepted,
        detector_branch_ready_for_formula=detector_ready,
        wet_observation_matrix_status=wet_status,
        wet_accepted_endpoint_count=wet_accepted,
        wet_required_endpoint_count=wet_required,
        wet_branch_ready_for_formula=wet_ready,
        combined_detector_wet_ready_for_formula=combined_ready,
        route_formula_blocker_status=(
            "detector_wet_branches_ready_for_formula_review"
            if combined_ready
            else "blocked_detector_blank_or_wet_accepted_evidence_missing"
        ),
        route_score_current=False,
        winner_current=False,
        JRC_current=False,
        yield_current=False,
        detection_probability_current=False,
        wet_pass_probability_current=False,
        production_ingestion_current=False,
        next_required_evidence=(
            "accepted detector/blank transfer row plus accepted wet endpoint bundle"
        ),
        hard_fail_if=(
            "detector_wet_activation_runner_emits_route_score_yield_detection_or_production"
        ),
        claim_boundary=SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_CLAIM_BOUNDARY,
    )


def _input_contract_rows(
    *,
    detector_input_present: bool,
    wet_input_present: bool,
    detector_input_path: str,
    wet_input_path: str,
    detector_accepted: int,
    wet_accepted: int,
) -> list[SidewallDetectorWetEvidenceActivationInputContractRow]:
    return [
        SidewallDetectorWetEvidenceActivationInputContractRow(
            contract_row_id="DETECTOR-WET-ACTIVATION-INPUT-detector_blank_transfer",
            activation_version=SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_VERSION,
            input_name="detector_blank_transfer_input_rows",
            input_path=detector_input_path,
            input_present=detector_input_present,
            required_for_branch="detector_blank_transfer",
            accepted_status_required=DETECTOR_TRANSFER_ACCEPTED_STATUS,
            current_accepted_rows=detector_accepted,
            hard_fail_if="detector_fixture_or_context_counted_as_accepted_transfer",
            claim_boundary=SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_CLAIM_BOUNDARY,
        ),
        SidewallDetectorWetEvidenceActivationInputContractRow(
            contract_row_id="DETECTOR-WET-ACTIVATION-INPUT-wet_observation",
            activation_version=SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_VERSION,
            input_name="wet_observation_input_rows",
            input_path=wet_input_path,
            input_present=wet_input_present,
            required_for_branch="wet_observation",
            accepted_status_required=WET_OBSERVATION_ACCEPTED_STATUS,
            current_accepted_rows=wet_accepted,
            hard_fail_if="wet_fixture_or_context_counted_as_accepted_observation",
            claim_boundary=SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_CLAIM_BOUNDARY,
        ),
    ]
