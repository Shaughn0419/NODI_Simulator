"""Detector/blank transfer intake for sidewall Package C routes.

This module validates future sidewall-specific blank traces or detector-response
transfer rows against the current detector/blank calibration panel. The default
state remains no-transfer-evidence/no-claim when no input rows are provided.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from pathlib import Path
from typing import Any, Mapping

from nodi_simulator.realism_v2_io import sha256_file


SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_VERSION = (
    "sidewall_detector_blank_transfer_intake_v1"
)
SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_CLAIM_BOUNDARY = (
    "detector_blank_transfer_intake_not_detection_probability_not_route_score"
)
TRANSFER_MISSING_STATUS = "detector_blank_transfer_missing_panel_ready"
TRANSFER_ACCEPTED_STATUS = (
    "detector_blank_transfer_accepted_candidate_not_detection_probability"
)
TRANSFER_REJECTED_STATUS = "detector_blank_transfer_rejected_missing_required_evidence"
ROUTE_MATRIX_NO_TRANSFER_STATUS = (
    "detector_blank_transfer_intake_ready_no_transfer_evidence"
)
ROUTE_MATRIX_ACCEPTED_STATUS = (
    "detector_blank_transfer_bundle_candidate_ready_requires_policy_review"
)

REQUIRED_TRANSFER_FIELDS: tuple[str, ...] = (
    "blank_trace_artifact_id",
    "blank_trace_artifact_path",
    "blank_trace_sha256",
    "detector_response_artifact_id",
    "detector_response_artifact_path",
    "detector_response_sha256",
    "blank_trace_geometry_match_level",
    "detector_response_model_id",
    "false_positive_rate_estimate",
    "false_positive_rate_ci_low",
    "false_positive_rate_ci_high",
    "n_blank_traces",
    "n_detector_calibration_runs",
    "controls_status",
    "uncertainty_model",
    "pre_registered_rule_status",
)


@dataclass(frozen=True)
class SidewallDetectorBlankTransferIntakeRow:
    intake_row_id: str
    intake_version: str
    route_candidate_id: str
    route_key: str
    source_case_id: str
    qch_sidecar_id: str
    source_panel_matrix_row_id: str
    route_evidence_matrix_status: str
    panel_selected_annulus_events: int
    panel_blank_guard_status: str
    panel_detector_response_context_status: str
    transfer_artifact_id: str
    blank_trace_artifact_id: str
    blank_trace_artifact_path: str
    blank_trace_sha256: str
    detector_response_artifact_id: str
    detector_response_artifact_path: str
    detector_response_sha256: str
    blank_trace_geometry_match_level: str
    detector_response_model_id: str
    false_positive_rate_estimate: str
    false_positive_rate_ci_low: str
    false_positive_rate_ci_high: str
    n_blank_traces: int
    n_detector_calibration_runs: int
    controls_status: str
    uncertainty_model: str
    pre_registered_rule_status: str
    missing_required_fields: str
    transfer_rejection_reason: str
    transfer_validation_status: str
    accepted_transfer_current: bool
    sidewall_specific_blank_trace_current: bool
    detector_response_validation_current: bool
    detection_probability_current: bool
    route_score_current: bool
    winner_current: bool
    yield_current: bool
    next_required_evidence: str
    hard_fail_if_promoted_without: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallDetectorBlankTransferRouteMatrixRow:
    matrix_row_id: str
    intake_version: str
    route_candidate_id: str
    route_key: str
    source_case_id: str
    qch_sidecar_id: str
    accepted_transfer_count: int
    missing_transfer_count: int
    rejected_transfer_count: int
    route_transfer_matrix_status: str
    blank_transfer_claim_readiness: str
    sidewall_specific_blank_trace_current: bool
    detector_response_validation_current: bool
    detection_probability_current: bool
    route_score_current: bool
    winner_current: bool
    yield_current: bool
    next_required_evidence: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_detector_blank_transfer_intake(
    *,
    panel_matrix_rows: list[Mapping[str, Any]],
    transfer_input_rows: list[Mapping[str, Any]] | None = None,
    artifact_root: str | Path | None = None,
) -> tuple[
    list[SidewallDetectorBlankTransferIntakeRow],
    list[SidewallDetectorBlankTransferRouteMatrixRow],
]:
    transfer_rows = transfer_input_rows or []
    transfer_by_route = {
        str(row.get("route_candidate_id", "")): row for row in transfer_rows
    }
    intake_rows = [
        _build_intake_row(
            panel,
            transfer_by_route.get(str(panel.get("route_candidate_id", "")), {}),
            artifact_root=artifact_root,
        )
        for panel in panel_matrix_rows
    ]
    return intake_rows, _route_matrix_rows(intake_rows)


def detector_blank_transfer_template_rows(
    panel_matrix_rows: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for panel in panel_matrix_rows:
        rows.append(
            {
                "route_candidate_id": str(panel.get("route_candidate_id", "")),
                "route_key": str(panel.get("route_key", "")),
                "source_case_id": str(panel.get("source_case_id", "")),
                "qch_sidecar_id": str(panel.get("qch_sidecar_id", "")),
                "source_panel_matrix_row_id": str(panel.get("matrix_row_id", "")),
                "transfer_artifact_id": "",
                "blank_trace_artifact_id": "",
                "blank_trace_artifact_path": "",
                "blank_trace_sha256": "",
                "detector_response_artifact_id": "",
                "detector_response_artifact_path": "",
                "detector_response_sha256": "",
                "blank_trace_geometry_match_level": "sidewall_specific | validated_transfer",
                "detector_response_model_id": "",
                "false_positive_rate_estimate": "",
                "false_positive_rate_ci_low": "",
                "false_positive_rate_ci_high": "",
                "n_blank_traces": "",
                "n_detector_calibration_runs": "",
                "controls_status": "controls_pass | controls_missing",
                "uncertainty_model": "",
                "pre_registered_rule_status": "pre_registered | missing",
            }
        )
    return rows


def detector_blank_transfer_promotion_update_rows(
    matrix_rows: list[SidewallDetectorBlankTransferRouteMatrixRow],
) -> list[dict[str, Any]]:
    route_ids = ";".join(sorted({row.route_candidate_id for row in matrix_rows}))
    all_accepted = bool(matrix_rows) and all(
        row.route_transfer_matrix_status == ROUTE_MATRIX_ACCEPTED_STATUS
        for row in matrix_rows
    )
    new_status = (
        ROUTE_MATRIX_ACCEPTED_STATUS if all_accepted else ROUTE_MATRIX_NO_TRANSFER_STATUS
    )
    return [
        {
            "target_ledger_lane": "detector_response_bridge",
            "covered_route_candidate_ids": route_ids,
            "previous_status": "detector_response_panel_candidate_not_sidewall_calibrated",
            "new_context_status": new_status,
            "target_claim_current": False,
            "blocked_promotion": "detection_probability;route_score;winner;yield",
            "hard_fail_if": "detector_transfer_intake_promoted_to_probability_without_policy_review",
            "next_required_evidence": (
                "sidewall-specific detector response calibration or validated transfer model"
            ),
            "claim_boundary": SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_CLAIM_BOUNDARY,
        },
        {
            "target_ledger_lane": "blank_false_positive_trace",
            "covered_route_candidate_ids": route_ids,
            "previous_status": "nearest_blank_guard_bound_to_panel_not_sidewall_specific",
            "new_context_status": new_status,
            "target_claim_current": False,
            "blocked_promotion": "detection_probability;route_score;winner;yield",
            "hard_fail_if": "blank_transfer_intake_promoted_to_fpr_without_policy_review",
            "next_required_evidence": (
                "sidewall-specific blank traces or validated blank false-positive transfer model"
            ),
            "claim_boundary": SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_CLAIM_BOUNDARY,
        },
    ]


def _build_intake_row(
    panel: Mapping[str, Any],
    transfer: Mapping[str, Any],
    *,
    artifact_root: str | Path | None,
) -> SidewallDetectorBlankTransferIntakeRow:
    missing = [
        field for field in REQUIRED_TRANSFER_FIELDS if not str(transfer.get(field, "")).strip()
    ]
    rejection_reason = _transfer_rejection_reason(
        transfer,
        missing,
        artifact_root=artifact_root,
    )
    validation_status = _transfer_validation_status(transfer, rejection_reason)
    accepted = validation_status == TRANSFER_ACCEPTED_STATUS
    return SidewallDetectorBlankTransferIntakeRow(
        intake_row_id=f"DB-TRANSFER-{panel.get('route_candidate_id', '')}",
        intake_version=SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_VERSION,
        route_candidate_id=str(panel.get("route_candidate_id", "")),
        route_key=str(panel.get("route_key", "")),
        source_case_id=str(panel.get("source_case_id", "")),
        qch_sidecar_id=str(panel.get("qch_sidecar_id", "")),
        source_panel_matrix_row_id=str(panel.get("matrix_row_id", "")),
        route_evidence_matrix_status=str(panel.get("route_evidence_matrix_status", "")),
        panel_selected_annulus_events=_int_value(panel.get("total_selected_annulus_events")),
        panel_blank_guard_status=str(panel.get("blank_guard_status", "")),
        panel_detector_response_context_status=str(
            panel.get("detector_response_context_status", "")
        ),
        transfer_artifact_id=str(transfer.get("transfer_artifact_id", "")),
        blank_trace_artifact_id=str(transfer.get("blank_trace_artifact_id", "")),
        blank_trace_artifact_path=str(transfer.get("blank_trace_artifact_path", "")),
        blank_trace_sha256=str(transfer.get("blank_trace_sha256", "")),
        detector_response_artifact_id=str(transfer.get("detector_response_artifact_id", "")),
        detector_response_artifact_path=str(
            transfer.get("detector_response_artifact_path", "")
        ),
        detector_response_sha256=str(transfer.get("detector_response_sha256", "")),
        blank_trace_geometry_match_level=str(
            transfer.get("blank_trace_geometry_match_level", "")
        ),
        detector_response_model_id=str(transfer.get("detector_response_model_id", "")),
        false_positive_rate_estimate=str(transfer.get("false_positive_rate_estimate", "")),
        false_positive_rate_ci_low=str(transfer.get("false_positive_rate_ci_low", "")),
        false_positive_rate_ci_high=str(transfer.get("false_positive_rate_ci_high", "")),
        n_blank_traces=_int_value(transfer.get("n_blank_traces")),
        n_detector_calibration_runs=_int_value(
            transfer.get("n_detector_calibration_runs")
        ),
        controls_status=str(transfer.get("controls_status", "")),
        uncertainty_model=str(transfer.get("uncertainty_model", "")),
        pre_registered_rule_status=str(transfer.get("pre_registered_rule_status", "")),
        missing_required_fields=";".join(missing),
        transfer_rejection_reason=rejection_reason,
        transfer_validation_status=validation_status,
        accepted_transfer_current=accepted,
        sidewall_specific_blank_trace_current=(
            accepted
            and str(transfer.get("blank_trace_geometry_match_level", ""))
            == "sidewall_specific"
        ),
        detector_response_validation_current=accepted,
        detection_probability_current=False,
        route_score_current=False,
        winner_current=False,
        yield_current=False,
        next_required_evidence=(
            "sidewall-specific blank traces, detector response calibration, "
            "controls, uncertainty, source artifact paths/hashes, and policy review"
        ),
        hard_fail_if_promoted_without=(
            "detector_blank_transfer_promoted_without_accepted_transfer_bundle"
        ),
        claim_boundary=SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_CLAIM_BOUNDARY,
    )


def _transfer_validation_status(
    transfer: Mapping[str, Any],
    rejection_reason: str,
) -> str:
    if not transfer:
        return TRANSFER_MISSING_STATUS
    if rejection_reason != "accepted_transfer_candidate":
        return TRANSFER_REJECTED_STATUS
    return TRANSFER_ACCEPTED_STATUS


def _transfer_rejection_reason(
    transfer: Mapping[str, Any],
    missing_fields: list[str],
    *,
    artifact_root: str | Path | None,
) -> str:
    if not transfer:
        return "missing_transfer_input"
    if missing_fields:
        return "missing_required_fields"
    geometry_match = str(transfer.get("blank_trace_geometry_match_level", ""))
    if geometry_match not in {"sidewall_specific", "validated_transfer"}:
        return "invalid_blank_trace_geometry_match_level"
    if artifact_root is None:
        if not _valid_sha256(transfer.get("blank_trace_sha256")):
            return "invalid_blank_trace_sha256"
        if not _valid_sha256(transfer.get("detector_response_sha256")):
            return "invalid_detector_response_sha256"
    else:
        if not _artifact_hash_ok(
            transfer,
            path_field="blank_trace_artifact_path",
            sha_field="blank_trace_sha256",
            artifact_root=artifact_root,
        ):
            return "invalid_blank_trace_artifact_or_sha256"
        if not _artifact_hash_ok(
            transfer,
            path_field="detector_response_artifact_path",
            sha_field="detector_response_sha256",
            artifact_root=artifact_root,
        ):
            return "invalid_detector_response_artifact_or_sha256"
    fpr = _float_value(transfer.get("false_positive_rate_estimate"))
    fpr_low = _float_value(transfer.get("false_positive_rate_ci_low"))
    fpr_high = _float_value(transfer.get("false_positive_rate_ci_high"))
    if not (_bounded_probability(fpr) and _bounded_probability(fpr_low) and _bounded_probability(fpr_high)):
        return "invalid_false_positive_probability_values"
    if not (fpr_low <= fpr <= fpr_high):
        return "invalid_false_positive_ci_order"
    if _int_value(transfer.get("n_blank_traces")) < 3:
        return "insufficient_blank_trace_count"
    if _int_value(transfer.get("n_detector_calibration_runs")) < 3:
        return "insufficient_detector_calibration_runs"
    if str(transfer.get("controls_status", "")) not in {
        "controls_pass",
        "candidate_controls_pass",
    }:
        return "controls_not_pass"
    if str(transfer.get("pre_registered_rule_status", "")) not in {
        "pre_registered",
        "candidate_rule_pre_registered",
    }:
        return "pre_registered_rule_missing"
    return "accepted_transfer_candidate"


def _valid_sha256(value: Any) -> bool:
    text = str(value or "").strip()
    if len(text) != 64:
        return False
    return all(char in "0123456789abcdefABCDEF" for char in text)


def _artifact_hash_ok(
    transfer: Mapping[str, Any],
    *,
    path_field: str,
    sha_field: str,
    artifact_root: str | Path,
) -> bool:
    expected = str(transfer.get(sha_field, "")).strip().lower()
    if not _valid_sha256(expected):
        return False
    artifact_path_text = str(transfer.get(path_field, "")).strip()
    if not artifact_path_text:
        return False
    artifact_path = Path(artifact_path_text)
    if not artifact_path.is_absolute():
        artifact_path = Path(artifact_root) / artifact_path
    if not artifact_path.exists() or not artifact_path.is_file():
        return False
    return sha256_file(artifact_path).lower() == expected


def _bounded_probability(value: float) -> bool:
    return math.isfinite(value) and 0.0 <= value <= 1.0


def _route_matrix_rows(
    rows: list[SidewallDetectorBlankTransferIntakeRow],
) -> list[SidewallDetectorBlankTransferRouteMatrixRow]:
    output: list[SidewallDetectorBlankTransferRouteMatrixRow] = []
    for row in sorted(rows, key=lambda item: item.route_candidate_id):
        accepted = int(row.transfer_validation_status == TRANSFER_ACCEPTED_STATUS)
        missing = int(row.transfer_validation_status == TRANSFER_MISSING_STATUS)
        rejected = int(row.transfer_validation_status == TRANSFER_REJECTED_STATUS)
        matrix_status = (
            ROUTE_MATRIX_ACCEPTED_STATUS if accepted else ROUTE_MATRIX_NO_TRANSFER_STATUS
        )
        output.append(
            SidewallDetectorBlankTransferRouteMatrixRow(
                matrix_row_id=f"DB-TRANSFER-MATRIX-{row.route_candidate_id}",
                intake_version=SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_VERSION,
                route_candidate_id=row.route_candidate_id,
                route_key=row.route_key,
                source_case_id=row.source_case_id,
                qch_sidecar_id=row.qch_sidecar_id,
                accepted_transfer_count=accepted,
                missing_transfer_count=missing,
                rejected_transfer_count=rejected,
                route_transfer_matrix_status=matrix_status,
                blank_transfer_claim_readiness=(
                    "candidate_ready_requires_policy_review"
                    if accepted
                    else "not_ready_no_sidewall_transfer_evidence"
                ),
                sidewall_specific_blank_trace_current=row.sidewall_specific_blank_trace_current,
                detector_response_validation_current=row.detector_response_validation_current,
                detection_probability_current=False,
                route_score_current=False,
                winner_current=False,
                yield_current=False,
                next_required_evidence=row.next_required_evidence,
                claim_boundary=SIDEWALL_DETECTOR_BLANK_TRANSFER_INTAKE_CLAIM_BOUNDARY,
            )
        )
    return output


def _int_value(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return math.nan
