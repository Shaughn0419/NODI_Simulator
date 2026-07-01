"""Integrated sidewall promotion preflight ledger.

The ledger joins existing Package C candidate/context packets at route grain.
It records which evidence lanes still block promotion to calibrated optical,
detection probability, yield, route score, or winner claims. It does not
compute route scores or choose winners.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


SIDEWALL_INTEGRATED_PROMOTION_LEDGER_VERSION = (
    "sidewall_integrated_promotion_preflight_ledger_v1"
)
SIDEWALL_INTEGRATED_PROMOTION_LEDGER_CLAIM_BOUNDARY = (
    "promotion_preflight_not_route_score_not_winner_not_yield_not_detection_probability"
)


@dataclass(frozen=True)
class SidewallIntegratedPromotionLedgerRow:
    ledger_row_id: str
    ledger_version: str
    route_candidate_id: str
    route_key: str
    source_case_id: str
    qch_sidecar_id: str
    qch_sidecar_status: str
    candidate_flow_split_fraction: float
    formal_qch_weighting_current: bool
    pressure_flow_validation_status: str
    wet_context_status: str
    selected_annulus_context_status: str
    sidewall_specific_wet_evidence_current: bool
    optical_calibration_bridge_status: str
    calibrated_lookup_unlock_status: str
    sidewall_reference_surrogate_smoke_current: bool
    full_wave_or_calibrated_optical_solver_current: bool
    true_W_eff_current: bool
    detector_response_validation_current: bool
    detection_probability_current: bool
    yield_current: bool
    route_score_current: bool
    winner_current: bool
    JRC_current: bool
    blocker_count: int
    blocker_ids: str
    promotion_preflight_status: str
    next_evidence_focus: str
    not_route_score: bool
    not_winner: bool
    not_yield: bool
    not_detection_probability: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallIntegratedPromotionBlockerRow:
    blocker_id: str
    ledger_version: str
    evidence_lane: str
    current_status: str
    required_before_promotion: str
    blocks_target_claims: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallIntegratedPromotionLaneRow:
    lane_row_id: str
    ledger_version: str
    route_candidate_id: str
    route_key: str
    source_case_id: str
    qch_sidecar_id: str
    evidence_lane: str
    source_artifact: str
    source_sha256: str
    source_disposition: str
    current_status: str
    claim_boundary: str
    target_claim: str
    target_claim_current: bool
    required_before_promotion: str
    hard_fail_if_promoted_without: str
    allowed_use: str
    blocked_use: str
    next_required_evidence: str
    not_route_score: bool
    not_winner: bool
    not_yield: bool
    not_detection_probability: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_blocker_catalog_rows(
    *,
    calibration_readiness_rows: list[dict[str, str]],
) -> list[SidewallIntegratedPromotionBlockerRow]:
    rows = [
        SidewallIntegratedPromotionBlockerRow(
            blocker_id="formal_qch_sidecar_not_accepted",
            ledger_version=SIDEWALL_INTEGRATED_PROMOTION_LEDGER_VERSION,
            evidence_lane="flow_split_qch",
            current_status="candidate_qch_sidecar_not_formal_weighting",
            required_before_promotion="formal q_ch sidecar authorization and pressure-flow validation at route grain",
            blocks_target_claims="route_score;winner;detection_probability",
            claim_boundary=SIDEWALL_INTEGRATED_PROMOTION_LEDGER_CLAIM_BOUNDARY,
        ),
        SidewallIntegratedPromotionBlockerRow(
            blocker_id="pressure_flow_context_only_not_formal_validation",
            ledger_version=SIDEWALL_INTEGRATED_PROMOTION_LEDGER_VERSION,
            evidence_lane="pressure_flow_validation",
            current_status="context_only_not_formal_validation",
            required_before_promotion="sidewall-matched COMSOL/measurement or accepted pressure-flow validation",
            blocks_target_claims="route_score;winner;q_ch_weighting",
            claim_boundary=SIDEWALL_INTEGRATED_PROMOTION_LEDGER_CLAIM_BOUNDARY,
        ),
        SidewallIntegratedPromotionBlockerRow(
            blocker_id="selected_annulus_context_missing",
            ledger_version=SIDEWALL_INTEGRATED_PROMOTION_LEDGER_VERSION,
            evidence_lane="selected_annulus_detection_context",
            current_status="selected_annulus_context_missing_rerun_required",
            required_before_promotion="rerun or validate selected-annulus detection context at the route grain",
            blocks_target_claims="detection_probability;route_score;winner",
            claim_boundary=SIDEWALL_INTEGRATED_PROMOTION_LEDGER_CLAIM_BOUNDARY,
        ),
    ]
    for row in calibration_readiness_rows:
        rows.append(
            SidewallIntegratedPromotionBlockerRow(
                blocker_id=str(row.get("hard_fail_if_promoted_without", "")),
                ledger_version=SIDEWALL_INTEGRATED_PROMOTION_LEDGER_VERSION,
                evidence_lane=str(row.get("evidence_lane", "")),
                current_status=str(row.get("current_status", "")),
                required_before_promotion=str(row.get("required_before_promotion", "")),
                blocks_target_claims=str(row.get("target_claim", "")),
                claim_boundary=SIDEWALL_INTEGRATED_PROMOTION_LEDGER_CLAIM_BOUNDARY,
            )
        )
    return rows


def build_integrated_promotion_lane_rows(
    *,
    ledger_rows: list[SidewallIntegratedPromotionLedgerRow],
    blocker_catalog_rows: list[SidewallIntegratedPromotionBlockerRow],
    source_artifact_by_lane: dict[str, tuple[str, str, str]] | None = None,
) -> list[SidewallIntegratedPromotionLaneRow]:
    """Expand route summaries into route x evidence-lane preflight rows."""
    source_artifact_by_lane = source_artifact_by_lane or {}
    rows: list[SidewallIntegratedPromotionLaneRow] = []
    for ledger in ledger_rows:
        for blocker in blocker_catalog_rows:
            source_artifact, source_sha256, source_disposition = source_artifact_by_lane.get(
                blocker.evidence_lane,
                ("integrated_source_lock", "", "source_locked_context"),
            )
            rows.append(
                SidewallIntegratedPromotionLaneRow(
                    lane_row_id=f"{ledger.ledger_row_id}-{blocker.blocker_id}",
                    ledger_version=SIDEWALL_INTEGRATED_PROMOTION_LEDGER_VERSION,
                    route_candidate_id=ledger.route_candidate_id,
                    route_key=ledger.route_key,
                    source_case_id=ledger.source_case_id,
                    qch_sidecar_id=ledger.qch_sidecar_id,
                    evidence_lane=blocker.evidence_lane,
                    source_artifact=source_artifact,
                    source_sha256=source_sha256,
                    source_disposition=source_disposition,
                    current_status=blocker.current_status,
                    claim_boundary=SIDEWALL_INTEGRATED_PROMOTION_LEDGER_CLAIM_BOUNDARY,
                    target_claim=blocker.blocks_target_claims,
                    target_claim_current=False,
                    required_before_promotion=blocker.required_before_promotion,
                    hard_fail_if_promoted_without=blocker.blocker_id,
                    allowed_use="promotion preflight blocker tracking",
                    blocked_use=(
                        "route_score;winner;JRC;q_ch_weighting;yield;"
                        "detection_probability;wet pass;production ingestion"
                    ),
                    next_required_evidence=blocker.required_before_promotion,
                    not_route_score=True,
                    not_winner=True,
                    not_yield=True,
                    not_detection_probability=True,
                )
            )
    return rows


def build_integrated_promotion_ledger_rows(
    *,
    route_candidate_rows: list[dict[str, str]],
    wet_context_rows: list[dict[str, str]],
    qch_rows: list[dict[str, str]],
    pressure_rows: list[dict[str, str]],
    calibration_bridge_summary: dict[str, Any],
    blocker_catalog_rows: list[SidewallIntegratedPromotionBlockerRow],
) -> list[SidewallIntegratedPromotionLedgerRow]:
    wet_by_route = {row["route_candidate_id"]: row for row in wet_context_rows}
    qch_by_id = {row["qch_sidecar_id"]: row for row in qch_rows}
    pressure_by_qch = {row["qch_sidecar_id"]: row for row in pressure_rows}
    catalog_ids = [row.blocker_id for row in blocker_catalog_rows if row.blocker_id]
    rows: list[SidewallIntegratedPromotionLedgerRow] = []
    for route in route_candidate_rows:
        route_id = route["route_candidate_id"]
        qch_id = route["qch_sidecar_id"]
        wet = wet_by_route.get(route_id, {})
        qch = qch_by_id.get(qch_id, {})
        pressure = pressure_by_qch.get(qch_id, {})
        blockers = list(catalog_ids)
        sidewall_reference_smoke_current = (
            str(calibration_bridge_summary.get("source_reference_smoke_disposition", ""))
            == "NODI_PACKAGE_C_SIDEWALL_REFERENCE_SURROGATE_SMOKE_READY_NOT_OPTICAL_SOLVER"
        )
        rows.append(
            SidewallIntegratedPromotionLedgerRow(
                ledger_row_id=f"PROMO-{route_id}",
                ledger_version=SIDEWALL_INTEGRATED_PROMOTION_LEDGER_VERSION,
                route_candidate_id=route_id,
                route_key=route["route_key"],
                source_case_id=route["source_case_id"],
                qch_sidecar_id=qch_id,
                qch_sidecar_status=route.get("qch_sidecar_status", ""),
                candidate_flow_split_fraction=_float_value(
                    route.get("candidate_flow_split_fraction")
                    or qch.get("candidate_flow_split_fraction")
                ),
                formal_qch_weighting_current=_bool_value(
                    qch.get("formal_qch_weighting_current")
                ),
                pressure_flow_validation_status=pressure.get(
                    "validation_status",
                    route.get("pressure_flow_validation_status", ""),
                ),
                wet_context_status=wet.get(
                    "wet_context_status",
                    route.get("wet_evidence_status", ""),
                ),
                selected_annulus_context_status=wet.get(
                    "selected_annulus_context_status",
                    "missing",
                ),
                sidewall_specific_wet_evidence_current=_bool_value(
                    wet.get("sidewall_specific_wet_evidence_current")
                ),
                optical_calibration_bridge_status=str(
                    calibration_bridge_summary.get("disposition", "")
                ),
                calibrated_lookup_unlock_status=str(
                    calibration_bridge_summary.get("calibrated_lookup_unlock_status", "")
                ),
                sidewall_reference_surrogate_smoke_current=sidewall_reference_smoke_current,
                full_wave_or_calibrated_optical_solver_current=_bool_value(
                    calibration_bridge_summary.get(
                        "full_wave_or_calibrated_optical_solver_current"
                    )
                ),
                true_W_eff_current=_bool_value(
                    calibration_bridge_summary.get("true_W_eff_current")
                ),
                detector_response_validation_current=_bool_value(
                    calibration_bridge_summary.get(
                        "detector_response_validation_current"
                    )
                ),
                detection_probability_current=False,
                yield_current=False,
                route_score_current=False,
                winner_current=False,
                JRC_current=False,
                blocker_count=len(blockers),
                blocker_ids=";".join(blockers),
                promotion_preflight_status="blocked_missing_calibrated_optical_wet_route_evidence",
                next_evidence_focus=(
                    "replace synthetic optical seed with measured/solver calibration; "
                    "validate pressure-flow/q_ch; collect sidewall wet and blank-trace evidence; "
                    "then bind an explicit route selection policy"
                ),
                not_route_score=True,
                not_winner=True,
                not_yield=True,
                not_detection_probability=True,
                claim_boundary=SIDEWALL_INTEGRATED_PROMOTION_LEDGER_CLAIM_BOUNDARY,
            )
        )
    return rows


def _float_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes"}
