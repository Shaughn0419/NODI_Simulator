"""Bind exact sidewall pressure-flow results into formal q_ch sidecar candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Mapping


SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_VERSION = (
    "sidewall_pressure_flow_result_binder_w500_d900_v1"
)
SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_CLAIM_BOUNDARY = (
    "pressure_flow_result_binder_not_route_score_not_yield_not_detection"
)
SIDECAR_STATUS_FORMAL = "formal_qch_sidecar_from_exact_pressure_flow"
SIDECAR_STATUS_BLOCKED = "blocked_missing_or_failed_exact_pressure_flow"
PORT_BALANCE_THRESHOLD_DEFAULT = 0.01
Q_TOTAL_RECONCILIATION_THRESHOLD_DEFAULT = 0.05

REQUIRED_EXTERNAL_RESULT_FIELDS = (
    "external_result_id",
    "source_type",
    "validation_request_id",
    "route_candidate_id",
    "qch_sidecar_id",
    "case_id",
    "geometry_descriptor_sha256",
    "model_or_measurement_id",
    "mesh_or_instrument_resolution",
    "fluid_viscosity_Pa_s",
    "channel_length_m",
    "boundary_condition_id",
    "pressure_drop_Pa",
    "q_total_m3_s",
    "q_upper_ports_m3_s",
    "q_lower_ports_m3_s",
    "port_balance_rel",
    "quality_gate",
    "result_artifact_sha256",
)


@dataclass(frozen=True)
class SidewallPressureFlowExternalResultTemplateRow:
    external_result_template_id: str
    binder_version: str
    validation_request_id: str
    route_candidate_id: str
    qch_sidecar_id: str
    case_id: str
    source_geometry_hash: str
    required_validation_source: str
    pressure_drop_Pa_required: float
    candidate_q_grid_m3_s: float
    candidate_flow_split_fraction: float
    acceptance_ratio_min: float
    acceptance_ratio_max: float
    port_balance_threshold_max: float
    q_total_reconciliation_threshold_max: float
    split_abs_delta_max: float
    required_external_result_fields: str
    external_result_status: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallPressureFlowBindingRow:
    binding_id: str
    binder_version: str
    validation_request_id: str
    route_candidate_id: str
    qch_sidecar_id: str
    case_id: str
    external_result_id: str
    source_type: str
    source_match_status: str
    pressure_drop_Pa: float
    candidate_q_scaled_m3_s: float
    q_total_m3_s: float
    q_upper_ports_m3_s: float
    q_lower_ports_m3_s: float
    port_balance_rel: float
    quality_gate: str
    flow_ratio_external_to_candidate: float
    candidate_flow_split_fraction: float
    external_flow_split_fraction: float
    split_abs_delta: float
    per_route_acceptance_status: str
    formal_qch_sidecar_current: bool
    formal_qch_weighting_current: bool
    route_score_current: bool
    winner_current: bool
    yield_current: bool
    detection_probability_current: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallFormalQchSidecarRow:
    formal_qch_sidecar_id: str
    formal_qch_sidecar_version: str
    qch_sidecar_status: str
    route_candidate_id: str
    qch_sidecar_id: str
    case_id: str
    source_validation_request_id: str
    source_external_result_id: str
    pressure_drop_Pa: float
    q_ch_m3_s: float
    q_ch_units: str
    formal_flow_split_fraction: float
    calibration_status: str
    source_match_status: str
    integration_definition: str
    formal_qch_sidecar_current: bool
    formal_qch_weighting_current: bool
    route_score_current: bool
    winner_current: bool
    yield_current: bool
    detection_probability_current: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_external_result_template_rows(
    request_rows: list[Mapping[str, Any]],
) -> list[SidewallPressureFlowExternalResultTemplateRow]:
    rows: list[SidewallPressureFlowExternalResultTemplateRow] = []
    for index, request in enumerate(request_rows, start=1):
        rows.append(
            SidewallPressureFlowExternalResultTemplateRow(
                external_result_template_id=f"PFV-EXTERNAL-TEMPLATE-{index:03d}",
                binder_version=SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_VERSION,
                validation_request_id=str(request.get("validation_request_id", "")),
                route_candidate_id=str(request.get("route_candidate_id", "")),
                qch_sidecar_id=str(request.get("qch_sidecar_id", "")),
                case_id=str(request.get("case_id", "")),
                source_geometry_hash=str(request.get("source_geometry_hash", "")),
                required_validation_source=str(request.get("required_validation_source", "")),
                pressure_drop_Pa_required=_float_value(request.get("pressure_drop_Pa")),
                candidate_q_grid_m3_s=_float_value(request.get("candidate_q_grid_m3_s")),
                candidate_flow_split_fraction=_float_value(
                    request.get("candidate_flow_split_fraction")
                ),
                acceptance_ratio_min=_float_value(request.get("acceptance_ratio_min")),
                acceptance_ratio_max=_float_value(request.get("acceptance_ratio_max")),
                port_balance_threshold_max=PORT_BALANCE_THRESHOLD_DEFAULT,
                q_total_reconciliation_threshold_max=Q_TOTAL_RECONCILIATION_THRESHOLD_DEFAULT,
                split_abs_delta_max=_float_value(request.get("split_abs_delta_max")),
                required_external_result_fields=";".join(REQUIRED_EXTERNAL_RESULT_FIELDS),
                external_result_status="template_waiting_for_exact_external_result",
                claim_boundary=SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_CLAIM_BOUNDARY,
            )
        )
    return rows


def bind_pressure_flow_external_results(
    request_rows: list[Mapping[str, Any]],
    external_result_rows: list[Mapping[str, Any]],
    *,
    port_balance_threshold: float = PORT_BALANCE_THRESHOLD_DEFAULT,
    q_total_reconciliation_threshold: float = Q_TOTAL_RECONCILIATION_THRESHOLD_DEFAULT,
) -> list[SidewallPressureFlowBindingRow]:
    """Bind external pressure-flow results to requests and fail closed on gaps."""
    result_by_request = {
        str(row.get("validation_request_id", "")): row for row in external_result_rows
    }
    preliminary: list[dict[str, Any]] = []
    for request in request_rows:
        result = result_by_request.get(str(request.get("validation_request_id", "")), {})
        preliminary.append(
            _build_preliminary_binding(
                request,
                result,
                port_balance_threshold=port_balance_threshold,
                q_total_reconciliation_threshold=q_total_reconciliation_threshold,
            )
        )

    accepted_q_total = sum(
        row["q_total_m3_s"]
        for row in preliminary
        if row["base_acceptance_status"] == "base_acceptance_pass"
    )
    all_base_pass = (
        len(preliminary) > 0
        and all(row["base_acceptance_status"] == "base_acceptance_pass" for row in preliminary)
        and accepted_q_total > 0.0
    )

    bound_rows: list[SidewallPressureFlowBindingRow] = []
    for index, row in enumerate(preliminary, start=1):
        external_split = (
            row["q_total_m3_s"] / accepted_q_total
            if all_base_pass and accepted_q_total > 0.0
            else 0.0
        )
        split_abs_delta = (
            abs(external_split - row["candidate_flow_split_fraction"])
            if all_base_pass
            else 0.0
        )
        split_limit = row["split_abs_delta_max"]
        final_status = row["base_acceptance_status"]
        if final_status == "base_acceptance_pass":
            if not all_base_pass:
                final_status = "blocked_until_all_route_results_pass_base_acceptance"
            elif split_abs_delta > split_limit:
                final_status = "split_delta_failed"
            else:
                final_status = "accepted_exact_pressure_flow_for_formal_qch_sidecar"
        formal = final_status == "accepted_exact_pressure_flow_for_formal_qch_sidecar"
        bound_rows.append(
            SidewallPressureFlowBindingRow(
                binding_id=f"PFV-BIND-{index:03d}",
                binder_version=SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_VERSION,
                validation_request_id=row["validation_request_id"],
                route_candidate_id=row["route_candidate_id"],
                qch_sidecar_id=row["qch_sidecar_id"],
                case_id=row["case_id"],
                external_result_id=row["external_result_id"],
                source_type=row["source_type"],
                source_match_status=row["source_match_status"],
                pressure_drop_Pa=_finite_or_zero(row["pressure_drop_Pa"]),
                candidate_q_scaled_m3_s=_finite_or_zero(row["candidate_q_scaled_m3_s"]),
                q_total_m3_s=_finite_or_zero(row["q_total_m3_s"]),
                q_upper_ports_m3_s=_finite_or_zero(row["q_upper_ports_m3_s"]),
                q_lower_ports_m3_s=_finite_or_zero(row["q_lower_ports_m3_s"]),
                port_balance_rel=_finite_or_zero(row["port_balance_rel"]),
                quality_gate=row["quality_gate"],
                flow_ratio_external_to_candidate=_finite_or_zero(
                    row["flow_ratio_external_to_candidate"]
                ),
                candidate_flow_split_fraction=_finite_or_zero(
                    row["candidate_flow_split_fraction"]
                ),
                external_flow_split_fraction=_finite_or_zero(external_split),
                split_abs_delta=_finite_or_zero(split_abs_delta),
                per_route_acceptance_status=final_status,
                formal_qch_sidecar_current=formal,
                formal_qch_weighting_current=False,
                route_score_current=False,
                winner_current=False,
                yield_current=False,
                detection_probability_current=False,
                claim_boundary=SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_CLAIM_BOUNDARY,
            )
        )
    return bound_rows


def build_formal_qch_sidecar_rows(
    binding_rows: list[SidewallPressureFlowBindingRow],
) -> list[SidewallFormalQchSidecarRow]:
    if len(binding_rows) != 2 or any(
        row.per_route_acceptance_status != "accepted_exact_pressure_flow_for_formal_qch_sidecar"
        for row in binding_rows
    ):
        return []
    rows: list[SidewallFormalQchSidecarRow] = []
    for index, row in enumerate(binding_rows, start=1):
        rows.append(
            SidewallFormalQchSidecarRow(
                formal_qch_sidecar_id=f"FORMAL-QCH-W500-D900-{index:03d}",
                formal_qch_sidecar_version=SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_VERSION,
                qch_sidecar_status=SIDECAR_STATUS_FORMAL,
                route_candidate_id=row.route_candidate_id,
                qch_sidecar_id=row.qch_sidecar_id,
                case_id=row.case_id,
                source_validation_request_id=row.validation_request_id,
                source_external_result_id=row.external_result_id,
                pressure_drop_Pa=row.pressure_drop_Pa,
                q_ch_m3_s=row.q_total_m3_s,
                q_ch_units="m3/s",
                formal_flow_split_fraction=row.external_flow_split_fraction,
                calibration_status="accepted_exact_w500_d900_pressure_flow_result",
                source_match_status=row.source_match_status,
                integration_definition=(
                    "q_ch_m3_s=q_total_m3_s from exact W500/D900 pressure-flow result; "
                    "formal_flow_split_fraction=q_ch_i/sum(q_ch_i)"
                ),
                formal_qch_sidecar_current=True,
                formal_qch_weighting_current=False,
                route_score_current=False,
                winner_current=False,
                yield_current=False,
                detection_probability_current=False,
                claim_boundary=SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_CLAIM_BOUNDARY,
            )
        )
    return rows


def pressure_flow_result_promotion_update_rows(
    binding_rows: list[SidewallPressureFlowBindingRow],
    formal_rows: list[SidewallFormalQchSidecarRow],
) -> list[dict[str, str]]:
    formal_ready = len(formal_rows) == len(binding_rows) and len(formal_rows) > 0
    return [
        {
            "target_ledger_lane": "pressure_flow_validation",
            "covered_route_candidate_ids": ";".join(row.route_candidate_id for row in binding_rows),
            "previous_status": (
                "exact_w500_d900_pressure_flow_validation_harness_ready_missing_external_result"
            ),
            "new_context_status": (
                "exact_w500_d900_pressure_flow_result_accepted_formal_qch_sidecar_ready"
                if formal_ready
                else "exact_w500_d900_pressure_flow_result_missing_or_failed"
            ),
            "target_claim_current": "false",
            "formal_qch_sidecar_current": str(formal_ready).lower(),
            "blocked_promotion": "route_score;winner;yield;detection_probability",
            "hard_fail_if": (
                "formal_qch_sidecar_promoted_to_route_score_without_route_policy_and_detection_yield_evidence"
                if formal_ready
                else "pressure_flow_result_missing_or_failed_promoted_to_formal_qch"
            ),
            "next_required_evidence": (
                "route policy plus calibrated detector/wet/yield evidence"
                if formal_ready
                else "bind exact W500/D900 pressure-flow external results that satisfy acceptance checks"
            ),
            "claim_boundary": SIDEWALL_PRESSURE_FLOW_RESULT_BINDER_CLAIM_BOUNDARY,
        }
    ]


def _build_preliminary_binding(
    request: Mapping[str, Any],
    result: Mapping[str, Any],
    *,
    port_balance_threshold: float,
    q_total_reconciliation_threshold: float,
) -> dict[str, Any]:
    validation_request_id = str(request.get("validation_request_id", ""))
    route_candidate_id = str(request.get("route_candidate_id", ""))
    qch_sidecar_id = str(request.get("qch_sidecar_id", ""))
    case_id = str(request.get("case_id", ""))
    request_pressure = _float_value(request.get("pressure_drop_Pa"))
    candidate_q = _float_value(request.get("candidate_q_grid_m3_s"))
    result_pressure = _float_value(result.get("pressure_drop_Pa"))
    q_total = _float_value(result.get("q_total_m3_s"))
    q_upper = _float_value(result.get("q_upper_ports_m3_s"))
    q_lower = _float_value(result.get("q_lower_ports_m3_s"))
    port_balance = _float_value(result.get("port_balance_rel"))
    scaled_candidate = (
        candidate_q * result_pressure / request_pressure
        if candidate_q > 0.0 and result_pressure > 0.0 and request_pressure > 0.0
        else math.inf
    )
    ratio = q_total / scaled_candidate if scaled_candidate > 0.0 else math.inf
    source_match = _source_match_status(request, result)
    base_status = _base_acceptance_status(
        request,
        result,
        source_match=source_match,
        q_total=q_total,
        q_upper=q_upper,
        q_lower=q_lower,
        port_balance=port_balance,
        ratio=ratio,
        port_balance_threshold=port_balance_threshold,
        q_total_reconciliation_threshold=q_total_reconciliation_threshold,
    )
    return {
        "validation_request_id": validation_request_id,
        "route_candidate_id": route_candidate_id,
        "qch_sidecar_id": qch_sidecar_id,
        "case_id": case_id,
        "external_result_id": str(result.get("external_result_id", "")),
        "source_type": str(result.get("source_type", "")),
        "source_match_status": source_match,
        "pressure_drop_Pa": _finite_or_zero(result_pressure),
        "candidate_q_scaled_m3_s": _finite_or_zero(scaled_candidate),
        "q_total_m3_s": _finite_or_zero(q_total),
        "q_upper_ports_m3_s": _finite_or_zero(q_upper),
        "q_lower_ports_m3_s": _finite_or_zero(q_lower),
        "port_balance_rel": _finite_or_zero(port_balance),
        "quality_gate": str(result.get("quality_gate", "")),
        "flow_ratio_external_to_candidate": _finite_or_zero(ratio),
        "candidate_flow_split_fraction": _float_value(
            request.get("candidate_flow_split_fraction")
        ),
        "split_abs_delta_max": _float_value(request.get("split_abs_delta_max")),
        "base_acceptance_status": base_status,
    }


def _source_match_status(request: Mapping[str, Any], result: Mapping[str, Any]) -> str:
    if not result:
        return "missing_external_result"
    for key in ("validation_request_id", "route_candidate_id", "qch_sidecar_id", "case_id"):
        if str(request.get(key, "")) != str(result.get(key, "")):
            return f"mismatch_{key}"
    if str(request.get("source_geometry_hash", "")) != str(
        result.get("geometry_descriptor_sha256", "")
    ):
        return "mismatch_geometry_descriptor_sha256"
    return "exact_request_and_geometry_match"


def _base_acceptance_status(
    request: Mapping[str, Any],
    result: Mapping[str, Any],
    *,
    source_match: str,
    q_total: float,
    q_upper: float,
    q_lower: float,
    port_balance: float,
    ratio: float,
    port_balance_threshold: float,
    q_total_reconciliation_threshold: float,
) -> str:
    if not result:
        return "missing_external_result"
    missing = [field for field in REQUIRED_EXTERNAL_RESULT_FIELDS if not str(result.get(field, ""))]
    if missing:
        return "missing_required_external_result_fields"
    if source_match != "exact_request_and_geometry_match":
        return source_match
    if str(result.get("source_type", "")) not in {"comsol_pressure_flow", "pressure_flow_measurement"}:
        return "invalid_source_type"
    if str(result.get("quality_gate", "")).lower() != "pass":
        return "quality_gate_not_pass"
    if not _positive_finite(q_total):
        return "nonpositive_q_total"
    if not _positive_finite(_float_value(result.get("pressure_drop_Pa"))):
        return "nonpositive_pressure_drop"
    if not math.isfinite(port_balance) or port_balance > port_balance_threshold:
        return "port_balance_failed"
    upper_lower_total = abs(q_upper) + abs(q_lower)
    if upper_lower_total <= 0.0 or not math.isfinite(upper_lower_total):
        return "upper_lower_flow_missing"
    if abs(q_total - upper_lower_total) / q_total > q_total_reconciliation_threshold:
        return "q_total_upper_lower_reconciliation_failed"
    ratio_min = _float_value(request.get("acceptance_ratio_min"))
    ratio_max = _float_value(request.get("acceptance_ratio_max"))
    if not math.isfinite(ratio) or ratio < ratio_min or ratio > ratio_max:
        return "external_to_candidate_flow_ratio_failed"
    return "base_acceptance_pass"


def _positive_finite(value: float) -> bool:
    return math.isfinite(value) and value > 0.0


def _finite_or_zero(value: float) -> float:
    return value if math.isfinite(value) else 0.0


def _float_value(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return math.inf
    return numeric
