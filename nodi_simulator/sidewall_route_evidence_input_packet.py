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
    claim_value_summary: Mapping[str, Any] | None = None,
    closure_rows: list[Mapping[str, Any]],
    detector_template_path: str,
    wet_template_path: str,
    detection_value_template_path: str,
    yield_value_template_path: str,
    detector_target_input_path: str,
    wet_target_input_path: str,
    detection_value_target_input_path: str,
    yield_value_target_input_path: str,
) -> tuple[
    list[SidewallRouteEvidenceInputRow],
    list[SidewallRouteEvidenceCommandRow],
    list[SidewallRouteEvidenceFormulaRow],
]:
    claim_value_summary = claim_value_summary or {}
    detector_accepted = _int(
        activation_summary.get("detector_accepted_transfer_rows_total")
    )
    wet_accepted = _int(activation_summary.get("wet_accepted_endpoint_count_total"))
    detection_accepted = _int(
        claim_value_summary.get("detection_probability_current_rows")
    )
    yield_accepted = _int(claim_value_summary.get("yield_current_rows"))
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
            current_accepted_rows=detector_accepted,
            accepted_status_required=(
                "detector_blank_transfer_bundle_candidate_ready_requires_policy_review"
            ),
            ready_to_rerun_chain=True,
            required_action=_input_required_action(
                accepted_rows=detector_accepted,
                ready_text=(
                    "detector blank transfer already has accepted candidate rows; "
                    "rerun only when replacing detector evidence"
                ),
                missing_text=(
                    "populate detector blank transfer input rows with accepted hashes, "
                    "controls, sample counts, uncertainty model, and pre-registered "
                    "rule status"
                ),
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
            current_accepted_rows=wet_accepted,
            accepted_status_required=(
                "wet_surface_observation_bundle_candidate_ready_requires_policy_review"
            ),
            ready_to_rerun_chain=True,
            required_action=_input_required_action(
                accepted_rows=wet_accepted,
                ready_text=(
                    "wet endpoint observation bundle already accepted; rerun only "
                    "when replacing wet evidence"
                ),
                missing_text=(
                    "populate wet source manifest rows and run the wet observation "
                    "manifest importer so source hashes, required fields, controls, "
                    "replicate counts, uncertainty intervals, and pre-registration "
                    "status are bound before wet intake"
                ),
            ),
            hard_fail_if="wet_template_or_context_rows_counted_as_wet_claim",
            claim_boundary=SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_CLAIM_BOUNDARY,
        ),
        SidewallRouteEvidenceInputRow(
            input_row_id="ROUTE-EVIDENCE-INPUT-detection_probability_value",
            input_packet_version=SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_VERSION,
            input_branch="detection_probability_value",
            template_artifact_path=detection_value_template_path,
            target_input_path=detection_value_target_input_path,
            template_rows=_int(claim_value_summary.get("detection_template_rows")),
            current_input_present=_bool(
                claim_value_summary.get("detection_input_present")
            ),
            current_accepted_rows=detection_accepted,
            accepted_status_required="detection_probability_value_accepted",
            ready_to_rerun_chain=True,
            required_action=_input_required_action(
                accepted_rows=detection_accepted,
                ready_text=(
                    "detection probability value rows already accepted; rerun only "
                    "when replacing value evidence"
                ),
                missing_text=(
                    "populate detection probability value rows with estimates, "
                    "confidence intervals, positive-control counts, threshold "
                    "policy, controls, uncertainty model, source hash, and "
                    "pre-registration status"
                ),
            ),
            hard_fail_if=(
                "detection_probability_template_rows_counted_as_probability_claim"
            ),
            claim_boundary=SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_CLAIM_BOUNDARY,
        ),
        SidewallRouteEvidenceInputRow(
            input_row_id="ROUTE-EVIDENCE-INPUT-yield_wet_value",
            input_packet_version=SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_VERSION,
            input_branch="yield_wet_value",
            template_artifact_path=yield_value_template_path,
            target_input_path=yield_value_target_input_path,
            template_rows=_int(claim_value_summary.get("yield_template_rows")),
            current_input_present=_bool(claim_value_summary.get("yield_input_present")),
            current_accepted_rows=yield_accepted,
            accepted_status_required="yield_wet_value_bundle_accepted",
            ready_to_rerun_chain=True,
            required_action=_input_required_action(
                accepted_rows=yield_accepted,
                ready_text=(
                    "yield and wet-pass value rows already accepted; rerun only "
                    "when replacing value evidence"
                ),
                missing_text=(
                    "populate yield and wet-pass value rows with estimates, "
                    "confidence intervals, wet trial counts, model id, controls, "
                    "uncertainty model, source hash, and pre-registration status"
                ),
            ),
            hard_fail_if="yield_template_rows_counted_as_yield_or_wet_pass_claim",
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
                else _formula_next_required_action(
                    detector_ready=_bool(row.get("detector_branch_ready")),
                    wet_ready=_bool(row.get("wet_branch_ready")),
                )
            ),
            claim_boundary=SIDEWALL_ROUTE_EVIDENCE_INPUT_PACKET_CLAIM_BOUNDARY,
        )
        for row in sorted(closure_rows, key=lambda item: str(item.get("route_candidate_id", "")))
    ]
    return input_rows, command_rows, formula_rows


def _input_required_action(
    *,
    accepted_rows: int,
    ready_text: str,
    missing_text: str,
) -> str:
    return ready_text if accepted_rows > 0 else missing_text


def _formula_next_required_action(*, detector_ready: bool, wet_ready: bool) -> str:
    if detector_ready and not wet_ready:
        return "complete accepted wet evidence inputs, then rerun the command chain"
    if wet_ready and not detector_ready:
        return "complete accepted detector evidence inputs, then rerun the command chain"
    return "complete accepted detector and wet evidence inputs, then rerun the command chain"


def _command_rows() -> list[SidewallRouteEvidenceCommandRow]:
    commands = [
        (
            "detector_blank_transfer_intake",
            "python tools\\audits\\build_nodi_package_c_sidewall_detector_blank_transfer_intake.py --confirm-sidewall-detector-blank-transfer-intake",
            "NODI_PACKAGE_C_SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_STATUS_20260701.json",
            "detector blank transfer intake accepts or rejects detector input rows",
        ),
        (
            "wet_surface_observation_manifest_import",
            "python tools\\audits\\build_nodi_package_c_sidewall_wet_surface_observation_manifest_import.py --confirm-sidewall-wet-surface-observation-manifest-import",
            "NODI_PACKAGE_C_SIDEWALL_WET_SURFACE_OBSERVATION_MANIFEST_IMPORT_STATUS_20260701.json",
            "imports source-manifest-bound wet observation rows and hashes before wet intake",
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
        (
            "route_formula_review_dry_run",
            "python tools\\audits\\build_nodi_package_c_sidewall_route_formula_review_dry_run.py --confirm-sidewall-route-formula-review-dry-run",
            "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_REVIEW_DRY_RUN_STATUS_20260701.json",
            "computes review-only route formula components",
        ),
        (
            "route_formula_policy_review",
            "python tools\\audits\\build_nodi_package_c_sidewall_route_formula_policy_review.py --confirm-sidewall-route-formula-policy-review",
            "NODI_PACKAGE_C_SIDEWALL_ROUTE_FORMULA_POLICY_REVIEW_STATUS_20260701.json",
            "activates route-score candidates only after real accepted evidence",
        ),
        (
            "winner_jrc_policy_review",
            "python tools\\audits\\build_nodi_package_c_sidewall_winner_jrc_policy_review.py --confirm-sidewall-winner-jrc-policy-review",
            "NODI_PACKAGE_C_SIDEWALL_WINNER_JRC_POLICY_REVIEW_STATUS_20260701.json",
            "activates winner/JRC only after current route scores and unique top",
        ),
        (
            "yield_detection_claim_value_manifest_import",
            "python tools\\audits\\build_nodi_package_c_sidewall_yield_detection_claim_value_manifest_import.py --confirm-sidewall-yield-detection-claim-value-manifest-import",
            "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_MANIFEST_IMPORT_STATUS_20260701.json",
            "imports source-manifest-bound yield/detection value rows and hashes before claim-value review",
        ),
        (
            "yield_detection_claim_value_review",
            "python tools\\audits\\build_nodi_package_c_sidewall_yield_detection_claim_value_review.py --confirm-sidewall-yield-detection-claim-value-review",
            "NODI_PACKAGE_C_SIDEWALL_YIELD_DETECTION_CLAIM_VALUE_REVIEW_STATUS_20260701.json",
            "accepts real numeric yield/detection/wet-pass value rows",
        ),
        (
            "route_decision_execution_readiness",
            "python tools\\audits\\build_nodi_package_c_sidewall_route_decision_execution_readiness.py --confirm-sidewall-route-decision-execution-readiness",
            "NODI_PACKAGE_C_SIDEWALL_ROUTE_DECISION_EXECUTION_READINESS_STATUS_20260701.json",
            "integrates route score, winner/JRC, yield, and detection value status",
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
