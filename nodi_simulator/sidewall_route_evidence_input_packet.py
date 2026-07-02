"""Unified evidence-input packet for sidewall route formula activation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_VERSION = (
    "sidewall_route_evidence_input_packet_v1"
)
SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_CLAIM_BOUNDARY = (
    "route_evidence_input_packet_implementation_authorized_evidence_gated"
)


@dataclass(frozen=True)
class SidewallRouteEvidenceInputRow:
    input_row_id: str
    input_packet_version: str
    input_branch: str
    template_artifact_path: str
    target_input_path: str
    template_rows: int
    current_input_present: bool
    current_accepted_rows: int
    accepted_status_required: str
    ready_to_rerun_chain: bool
    required_action: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallRouteEvidenceCommandRow:
    command_row_id: str
    input_packet_version: str
    sequence_index: int
    command_id: str
    command: str
    expected_artifact: str
    success_disposition_hint: str
    purpose: str
    hard_fail_if_previous_step_failed: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallRouteEvidenceFormulaRow:
    formula_row_id: str
    input_packet_version: str
    route_candidate_id: str
    route_geometry_family: str
    qch_status: str
    detector_branch_ready: bool
    wet_branch_ready: bool
    route_formula_ready_for_claim_review: bool
    route_formula_activation_status: str
    route_score_current: bool
    winner_current: bool
    yield_current: bool
    detection_probability_current: bool
    next_required_action: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_route_evidence_input_packet(
    *,
    detector_intake_summary: Mapping[str, Any],
    wet_intake_summary: Mapping[str, Any],
    activation_summary: Mapping[str, Any],
    closure_rows: list[Mapping[str, Any]],
    detector_template_path: str,
    wet_template_path: str,
    detector_target_input_path: str,
    wet_target_input_path: str,
) -> tuple[
    list[SidewallRouteEvidenceInputRow],
    list[SidewallRouteEvidenceCommandRow],
    list[SidewallRouteEvidenceFormulaRow],
]:
    input_rows = [
        SidewallRouteEvidenceInputRow(
            input_row_id="ROUTE-EVIDENCE-INPUT-detector_blank_transfer",
            input_packet_version=SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_VERSION,
            input_branch="detector_blank_transfer",
            template_artifact_path=detector_template_path,
            target_input_path=detector_target_input_path,
            template_rows=_int(detector_intake_summary.get("template_rows")),
            current_input_present=_bool(
                activation_summary.get("detector_input_present")
            ),
            current_accepted_rows=_int(
                activation_summary.get("detector_accepted_transfer_rows_total")
            ),
            accepted_status_required=(
                "detector_blank_transfer_bundle_candidate_ready_requires_policy_review"
            ),
            ready_to_rerun_chain=True,
            required_action=(
                "populate detector blank transfer input rows with accepted hashes, controls, "
                "sample counts, uncertainty model, and pre-registered rule status"
            ),
            hard_fail_if=(
                "detector_template_rows_counted_as_evidence_or_probability_claim"
            ),
            claim_boundary=SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_CLAIM_BOUNDARY,
        ),
        SidewallRouteEvidenceInputRow(
            input_row_id="ROUTE-EVIDENCE-INPUT-wet_surface_observation",
            input_packet_version=SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_VERSION,
            input_branch="wet_surface_observation",
            template_artifact_path=wet_template_path,
            target_input_path=wet_target_input_path,
            template_rows=_int(wet_intake_summary.get("template_rows")),
            current_input_present=_bool(activation_summary.get("wet_input_present")),
            current_accepted_rows=_int(
                activation_summary.get("wet_accepted_endpoint_count_total")
            ),
            accepted_status_required=(
                "wet_surface_observation_bundle_candidate_ready_requires_policy_review"
            ),
            ready_to_rerun_chain=True,
            required_action=(
                "populate all wet endpoint observation rows with source hashes, "
                "required fields, controls, replicate counts, uncertainty intervals, "
                "and pre-registration status where required"
            ),
            hard_fail_if="wet_template_or_context_rows_counted_as_wet_claim",
            claim_boundary=SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_CLAIM_BOUNDARY,
        ),
    ]
    command_rows = _command_rows()
    formula_rows = [
        SidewallRouteEvidenceFormulaRow(
            formula_row_id=f"ROUTE-EVIDENCE-FORMULA-{row.get('route_candidate_id', '')}",
            input_packet_version=SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_VERSION,
            route_candidate_id=str(row.get("route_candidate_id", "")),
            route_geometry_family=str(row.get("route_geometry_family", "")),
            qch_status=str(row.get("qch_status", "")),
            detector_branch_ready=_bool(row.get("detector_branch_ready")),
            wet_branch_ready=_bool(row.get("wet_branch_ready")),
            route_formula_ready_for_claim_review=_bool(
                row.get("route_formula_ready_for_claim_review")
            ),
            route_formula_activation_status=str(
                row.get("route_formula_activation_status", "")
            ),
            route_score_current=_bool(row.get("route_score_current")),
            winner_current=_bool(row.get("winner_current")),
            yield_current=_bool(row.get("yield_current")),
            detection_probability_current=_bool(
                row.get("detection_probability_current")
            ),
            next_required_action=(
                "route formula policy/review packet can run after q_ch, detector, and wet branches are all ready"
                if _bool(row.get("route_formula_ready_for_claim_review"))
                else "complete accepted detector and wet evidence inputs, then rerun the command chain"
            ),
            claim_boundary=SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_CLAIM_BOUNDARY,
        )
        for row in sorted(closure_rows, key=lambda item: str(item.get("route_candidate_id", "")))
    ]
    return input_rows, command_rows, formula_rows


def _command_rows() -> list[SidewallRouteEvidenceCommandRow]:
    commands = [
        (
            "detector_blank_transfer_intake",
            "python tools\\audits\\build_nodi_package_c_sidewall_detector_blank_transfer_intake.py --confirm-sidewall-detector-blank-transfer-intake",
            "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_STATUS_20260701.json",
            "detector blank transfer intake accepts or rejects detector input rows",
        ),
        (
            "wet_surface_observation_intake",
            "python tools\\audits\\build_nodi_package_c_sidewall_wet_surface_observation_intake.py --confirm-sidewall-wet-surface-observation-intake",
            "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_STATUS_20260701.json",
            "wet observation intake accepts or rejects endpoint rows",
        ),
        (
            "detector_wet_activation_runner",
            "python tools\\audits\\build_nodi_package_c_sidewall_detector_wet_evidence_activation_runner.py --confirm-sidewall-detector-wet-evidence-activation-runner",
            "NODI_PACKAGE_C_SIDEWALL_DETECTOR_WET_EVIDENCE_ACTIVATION_RUNNER_STATUS_20260701.json",
            "combines detector and wet accepted-evidence branches",
        ),
        (
            "route_formula_activation_closure",
            "python tools\\audits\\build_nodi_package_c_sidewall_route_formula_activation_closure.py --confirm-sidewall-route-formula-activation-closure",
            "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_ACTIVATION_CLOSURE_STATUS_20260701.json",
            "joins q_ch readiness with detector/wet activation for route formula review",
        ),
    ]
    return [
        SidewallRouteEvidenceCommandRow(
            command_row_id=f"ROUTE-EVIDENCE-COMMAND-{index:02d}-{command_id}",
            input_packet_version=SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_VERSION,
            sequence_index=index,
            command_id=command_id,
            command=command,
            expected_artifact=artifact,
            success_disposition_hint="READY or ACCEPTED disposition; fail closed otherwise",
            purpose=purpose,
            hard_fail_if_previous_step_failed=index > 1,
            claim_boundary=SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_CLAIM_BOUNDARY,
        )
        for index, (command_id, command, artifact, purpose) in enumerate(commands, start=1)
    ]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0
