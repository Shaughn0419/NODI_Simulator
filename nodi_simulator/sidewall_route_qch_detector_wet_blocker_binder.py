"""Canonical q_ch / detector / wet blocker binder for sidewall route work."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_VERSION = (
    "sidewall_route_qch_detector_wet_blocker_binder_v1"
)
SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_CLAIM_BOUNDARY = (
    "route_qch_detector_wet_blocker_binder_not_route_score_not_yield_not_detection"
)
SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_STATUS = (
    "route_qch_ready_detector_wet_blocker_binder_current"
)


@dataclass(frozen=True)
class SidewallRouteQchDetectorWetBlockerBinderRow:
    binder_row_id: str
    binder_version: str
    route_candidate_id: str
    route_geometry_family: str
    qch_sidecar_id: str
    q_ch_m3_s: float
    formal_flow_split_fraction: float
    qch_status: str
    route_formula_qch_branch_status: str
    selected_annulus_status: str
    runtime_substep_status: str
    detector_blank_status: str
    wet_observation_status: str
    route_formula_input_ready_count: int
    route_formula_required_input_count: int
    formula_input_completeness_fraction: float
    detector_accepted_transfer_rows: int
    wet_accepted_observation_rows: int
    route_score_current: bool
    winner_current: bool
    JRC_current: bool
    yield_current: bool
    detection_probability_current: bool
    wet_pass_probability_current: bool
    production_ingestion_current: bool
    canonical_next_block: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallRouteQchDetectorWetSupersessionRow:
    supersession_row_id: str
    binder_version: str
    superseded_builder_or_artifact: str
    superseded_current_status: str
    superseded_reason: str
    replacement_artifact_id: str
    replacement_status: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_route_qch_detector_wet_blocker_binder(
    *,
    preflight_rows: list[Mapping[str, Any]],
    source_statuses: Mapping[str, Mapping[str, Any]],
) -> tuple[
    list[SidewallRouteQchDetectorWetBlockerBinderRow],
    list[SidewallRouteQchDetectorWetSupersessionRow],
]:
    binder_rows = [
        _binder_row(row)
        for row in sorted(
            preflight_rows,
            key=lambda item: str(item.get("route_candidate_id", "")),
        )
    ]
    return binder_rows, _supersession_rows(source_statuses)


def _binder_row(
    row: Mapping[str, Any],
) -> SidewallRouteQchDetectorWetBlockerBinderRow:
    detector_accepted = _int(row.get("detector_accepted_transfer_rows"))
    wet_accepted = _int(row.get("wet_accepted_observation_rows"))
    return SidewallRouteQchDetectorWetBlockerBinderRow(
        binder_row_id=f"ROUTE-QCH-DETECTOR-WET-BINDER-{row.get('route_candidate_id', '')}",
        binder_version=SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_VERSION,
        route_candidate_id=str(row.get("route_candidate_id", "")),
        route_geometry_family=str(row.get("route_geometry_family", "")),
        qch_sidecar_id=str(row.get("qch_sidecar_id", "")),
        q_ch_m3_s=_float(row.get("q_ch_m3_s")),
        formal_flow_split_fraction=_float(row.get("formal_flow_split_fraction")),
        qch_status=(
            "formal_qch_input_ready_not_route_score"
            if _bool(row.get("qch_branch_ready"))
            else "formal_qch_input_missing"
        ),
        route_formula_qch_branch_status=(
            "ready"
            if _bool(row.get("qch_branch_ready"))
            and _bool(row.get("exact_pressure_flow_branch_ready"))
            else "blocked"
        ),
        selected_annulus_status=(
            "ready_input_not_probability"
            if _bool(row.get("selected_annulus_context_ready"))
            else "blocked_missing_selected_annulus_context"
        ),
        runtime_substep_status=(
            "guard_ready"
            if _bool(row.get("runtime_substep_guard_ready"))
            else "blocked_missing_runtime_guard"
        ),
        detector_blank_status=(
            "accepted_detector_blank_transfer_ready"
            if detector_accepted > 0
            else "blocker_not_accepted_evidence"
        ),
        wet_observation_status=(
            "accepted_wet_observation_ready"
            if wet_accepted > 0
            else "blocker_not_accepted_evidence"
        ),
        route_formula_input_ready_count=_int(row.get("route_formula_input_ready_count")),
        route_formula_required_input_count=_int(row.get("route_formula_required_input_count")),
        formula_input_completeness_fraction=_float(
            row.get("route_formula_input_completeness_fraction")
        ),
        detector_accepted_transfer_rows=detector_accepted,
        wet_accepted_observation_rows=wet_accepted,
        route_score_current=False,
        winner_current=False,
        JRC_current=False,
        yield_current=False,
        detection_probability_current=False,
        wet_pass_probability_current=False,
        production_ingestion_current=False,
        canonical_next_block="detector_blank_transfer_then_wet_observation",
        hard_fail_if=(
            "fixture_context_or_qch_ready_input_emits_route_score_yield_detection_or_production"
        ),
        claim_boundary=SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_CLAIM_BOUNDARY,
    )


def _supersession_rows(
    source_statuses: Mapping[str, Mapping[str, Any]],
) -> list[SidewallRouteQchDetectorWetSupersessionRow]:
    specs = [
        (
            "build_nodi_package_c_sidewall_integrated_promotion_ledger_formal_qch_refresh.py",
            "formal q_ch lineage should now bind through 566 route evidence delta",
        ),
        (
            "build_nodi_package_c_sidewall_route_yield_detection_policy.py",
            "older policy rows are superseded by 567 formula preflight plus this binder",
        ),
        (
            "build_nodi_package_c_sidewall_route_yield_detection_policy_wet_observation_refresh.py",
            "status semantics remain useful but source lock should be refreshed through 566/567",
        ),
        (
            "build_nodi_package_c_sidewall_route_yield_detection_assembly_v2.py",
            "assembly should consume canonical q_ch/detector/wet blocker rows from 568",
        ),
        (
            "build_nodi_package_c_sidewall_route_yield_detection_readiness_board.py",
            "user-facing readiness board should now display 566/567 current evidence",
        ),
    ]
    return [
        SidewallRouteQchDetectorWetSupersessionRow(
            supersession_row_id=f"ROUTE-QCH-DETECTOR-WET-SUPERSEDE-{idx:03d}",
            binder_version=SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_VERSION,
            superseded_builder_or_artifact=name,
            superseded_current_status=str(
                source_statuses.get(name, {}).get("disposition", "")
            ),
            superseded_reason=reason,
            replacement_artifact_id="PACKAGE_C_SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_20260701",
            replacement_status=SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_STATUS,
            claim_boundary=SIDEWALL_ROUTE_QCH_DETECTOR_WET_BLOCKER_BINDER_CLAIM_BOUNDARY,
        )
        for idx, (name, reason) in enumerate(specs, start=1)
    ]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if value is None or str(value).strip() == "":
        return 0
    return int(float(str(value)))


def _float(value: Any) -> float:
    if value is None or str(value).strip() == "":
        return 0.0
    return float(str(value))
