"""Route formula binding preflight for Package C sidewall candidates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_ROUTE_FORMULA_BINDING_PREFLIGHT_VERSION = (
    "sidewall_route_formula_binding_preflight_v1"
)
SIDEWALL_ROUTE_FORMULA_BINDING_PREFLIGHT_CLAIM_BOUNDARY = (
    "route_formula_binding_preflight_not_route_score_not_winner_not_yield_not_detection"
)
SIDEWALL_ROUTE_FORMULA_BINDING_PREFLIGHT_STATUS = (
    "route_formula_binding_preflight_formal_qch_ready_detector_wet_blocked"
)


@dataclass(frozen=True)
class SidewallRouteFormulaBindingPreflightRow:
    preflight_row_id: str
    preflight_version: str
    route_candidate_id: str
    route_geometry_family: str
    qch_sidecar_id: str
    source_case_id: str
    route_key: str
    q_ch_m3_s: float
    formal_flow_split_fraction: float
    candidate_metric_current: float
    candidate_sort_index_under_context: int
    qch_branch_ready: bool
    exact_pressure_flow_branch_ready: bool
    selected_annulus_context_ready: bool
    runtime_substep_guard_ready: bool
    detector_validator_hardened: bool
    wet_validator_hardened: bool
    detector_accepted_transfer_rows: int
    wet_accepted_observation_rows: int
    detector_branch_ready: bool
    wet_branch_ready: bool
    route_formula_input_ready_count: int
    route_formula_required_input_count: int
    route_formula_input_completeness_fraction: float
    route_formula_binding_status: str
    route_score_current: bool
    winner_current: bool
    JRC_current: bool
    yield_current: bool
    detection_probability_current: bool
    production_ingestion_current: bool
    next_required_evidence: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallRouteFormulaBindingBranchRow:
    branch_row_id: str
    preflight_version: str
    route_candidate_id: str
    branch_name: str
    branch_status: str
    evidence_class: str
    accepted_evidence_rows: int
    branch_ready_for_formula: bool
    target_claim: str
    target_claim_current: bool
    next_required_evidence: str
    hard_fail_if: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallRouteFormulaBindingGuardRow:
    guard_row_id: str
    preflight_version: str
    activation_target: str
    implementation_authorized: bool
    preflight_branch_ready: bool
    activation_allowed_now: bool
    required_evidence_before_activation: str
    hard_fail_if_activated_early: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_route_formula_binding_preflight(
    *,
    qch_delta_rows: list[Mapping[str, Any]],
    route_candidate_rows: list[Mapping[str, Any]],
    detector_wet_closure_rows: list[Mapping[str, Any]],
) -> tuple[
    list[SidewallRouteFormulaBindingPreflightRow],
    list[SidewallRouteFormulaBindingBranchRow],
    list[SidewallRouteFormulaBindingGuardRow],
]:
    qch_by_route = {
        str(row.get("route_candidate_id", "")): row for row in qch_delta_rows
    }
    candidate_by_route = {
        str(row.get("route_candidate_id", "")): row for row in route_candidate_rows
    }
    closure_by_route = {
        str(row.get("route_candidate_id", "")): row for row in detector_wet_closure_rows
    }
    route_ids = sorted(set(qch_by_route) | set(candidate_by_route) | set(closure_by_route))
    preflight_rows: list[SidewallRouteFormulaBindingPreflightRow] = []
    branch_rows: list[SidewallRouteFormulaBindingBranchRow] = []
    for route_id in route_ids:
        qch = qch_by_route.get(route_id, {})
        candidate = candidate_by_route.get(route_id, {})
        closure = closure_by_route.get(route_id, {})
        qch_ready = _bool(qch.get("may_satisfy_route_formula_qch_branch_now"))
        pressure_ready = qch_ready and str(qch.get("evidence_class", "")) == (
            "accepted_exact_pressure_flow_for_formal_qch_sidecar"
        )
        selected_ready = _bool(closure.get("selected_annulus_context_ready"))
        runtime_ready = _bool(closure.get("runtime_substep_guard_ready"))
        detector_accepted = _int(closure.get("detector_accepted_transfer_rows"))
        wet_accepted = _int(closure.get("wet_accepted_observation_rows"))
        detector_ready = detector_accepted > 0
        wet_ready = wet_accepted > 0
        ready_count = sum(
            [
                qch_ready,
                pressure_ready,
                selected_ready,
                runtime_ready,
                detector_ready,
                wet_ready,
            ]
        )
        required_count = 6
        formula_ready = ready_count == required_count
        preflight_rows.append(
            SidewallRouteFormulaBindingPreflightRow(
                preflight_row_id=f"ROUTE-FORMULA-PREFLIGHT-{route_id}",
                preflight_version=SIDEWALL_ROUTE_FORMULA_BINDING_PREFLIGHT_VERSION,
                route_candidate_id=route_id,
                route_geometry_family=str(
                    qch.get("route_geometry_family")
                    or closure.get("route_geometry_family")
                    or _geometry_from_candidate(candidate)
                ),
                qch_sidecar_id=str(candidate.get("qch_sidecar_id", "")),
                source_case_id=str(candidate.get("source_case_id", "")),
                route_key=str(candidate.get("route_key", "")),
                q_ch_m3_s=_float(qch.get("q_ch_m3_s")),
                formal_flow_split_fraction=_float(
                    qch.get("formal_flow_split_fraction")
                ),
                candidate_metric_current=_float(
                    candidate.get("route_decision_candidate_metric")
                ),
                candidate_sort_index_under_context=_int(
                    candidate.get("candidate_sort_index_under_context")
                ),
                qch_branch_ready=qch_ready,
                exact_pressure_flow_branch_ready=pressure_ready,
                selected_annulus_context_ready=selected_ready,
                runtime_substep_guard_ready=runtime_ready,
                detector_validator_hardened=_bool(
                    closure.get("detector_validator_hardened")
                ),
                wet_validator_hardened=_bool(closure.get("wet_validator_hardened")),
                detector_accepted_transfer_rows=detector_accepted,
                wet_accepted_observation_rows=wet_accepted,
                detector_branch_ready=detector_ready,
                wet_branch_ready=wet_ready,
                route_formula_input_ready_count=ready_count,
                route_formula_required_input_count=required_count,
                route_formula_input_completeness_fraction=round(
                    ready_count / required_count, 6
                ),
                route_formula_binding_status=(
                    "route_formula_inputs_ready_for_claim_activation_review"
                    if formula_ready
                    else "blocked_detector_blank_and_wet_accepted_evidence_required"
                ),
                route_score_current=False,
                winner_current=False,
                JRC_current=False,
                yield_current=False,
                detection_probability_current=False,
                production_ingestion_current=False,
                next_required_evidence=(
                    "accepted detector/blank transfer rows and accepted wet observation rows"
                ),
                hard_fail_if=(
                    "route_formula_preflight_emits_route_score_winner_yield_detection_or_production_before_all_required_inputs_ready"
                ),
                claim_boundary=SIDEWALL_ROUTE_FORMULA_BINDING_PREFLIGHT_CLAIM_BOUNDARY,
            )
        )
        branch_rows.extend(
            _branch_rows(
                route_id=route_id,
                qch_ready=qch_ready,
                pressure_ready=pressure_ready,
                selected_ready=selected_ready,
                runtime_ready=runtime_ready,
                detector_ready=detector_ready,
                wet_ready=wet_ready,
                detector_accepted=detector_accepted,
                wet_accepted=wet_accepted,
            )
        )
    return preflight_rows, branch_rows, _guard_rows(preflight_rows)


def _branch_rows(
    *,
    route_id: str,
    qch_ready: bool,
    pressure_ready: bool,
    selected_ready: bool,
    runtime_ready: bool,
    detector_ready: bool,
    wet_ready: bool,
    detector_accepted: int,
    wet_accepted: int,
) -> list[SidewallRouteFormulaBindingBranchRow]:
    specs = [
        (
            "formal_qch",
            qch_ready,
            "accepted_exact_pressure_flow_for_formal_qch_sidecar",
            int(qch_ready),
            "route_formula_input",
            "route formula packet",
            "formal_qch_missing_from_566_delta",
        ),
        (
            "exact_pressure_flow",
            pressure_ready,
            "accepted_exact_pressure_flow_for_formal_qch_sidecar",
            int(pressure_ready),
            "route_formula_input",
            "pressure-flow result binder",
            "pressure_flow_missing_or_not_exact",
        ),
        (
            "selected_annulus_context",
            selected_ready,
            "ready_route_input",
            int(selected_ready),
            "route_formula_input",
            "selected annulus context rows",
            "selected_annulus_context_missing",
        ),
        (
            "runtime_substep_guard",
            runtime_ready,
            "guarded_runtime_smoke_evidence",
            int(runtime_ready),
            "route_formula_input",
            "runtime/substep guard smoke",
            "runtime_substep_guard_missing",
        ),
        (
            "detector_blank_transfer",
            detector_ready,
            "accepted_detector_blank_transfer",
            detector_accepted,
            "detection_probability",
            "accepted detector/blank transfer rows",
            "detector_blank_transfer_missing",
        ),
        (
            "wet_observation",
            wet_ready,
            "accepted_wet_observation",
            wet_accepted,
            "yield",
            "accepted wet observation rows",
            "wet_observation_missing",
        ),
    ]
    rows: list[SidewallRouteFormulaBindingBranchRow] = []
    for name, ready, evidence_class, accepted, target, required, hard_fail in specs:
        rows.append(
            SidewallRouteFormulaBindingBranchRow(
                branch_row_id=f"ROUTE-FORMULA-BRANCH-{route_id}-{name}",
                preflight_version=SIDEWALL_ROUTE_FORMULA_BINDING_PREFLIGHT_VERSION,
                route_candidate_id=route_id,
                branch_name=name,
                branch_status="ready_for_formula_input" if ready else "blocked_missing_required_evidence",
                evidence_class=evidence_class,
                accepted_evidence_rows=accepted,
                branch_ready_for_formula=ready,
                target_claim=target,
                target_claim_current=False,
                next_required_evidence=required,
                hard_fail_if=hard_fail,
                claim_boundary=SIDEWALL_ROUTE_FORMULA_BINDING_PREFLIGHT_CLAIM_BOUNDARY,
            )
        )
    return rows


def _guard_rows(
    rows: list[SidewallRouteFormulaBindingPreflightRow],
) -> list[SidewallRouteFormulaBindingGuardRow]:
    all_formula_ready = bool(rows) and all(
        row.route_formula_binding_status
        == "route_formula_inputs_ready_for_claim_activation_review"
        for row in rows
    )
    specs = [
        (
            "route_score",
            all_formula_ready,
            "all route formula branches ready plus route-score policy review",
            "route_score_true_before_preflight_all_routes_ready",
        ),
        (
            "winner_JRC",
            False,
            "route_score packet and JRC policy after preflight readiness",
            "winner_or_JRC_true_from_preflight_only",
        ),
        (
            "yield",
            all_formula_ready,
            "accepted wet rows and yield model packet",
            "yield_true_before_wet_branch_ready",
        ),
        (
            "detection_probability",
            all_formula_ready,
            "accepted detector rows and detection model packet",
            "detection_probability_true_before_detector_branch_ready",
        ),
        (
            "production_ingestion",
            False,
            "separate production closeout after candidate values and review",
            "production_ingestion_true_from_formula_preflight",
        ),
    ]
    return [
        SidewallRouteFormulaBindingGuardRow(
            guard_row_id=f"ROUTE-FORMULA-GUARD-{target}",
            preflight_version=SIDEWALL_ROUTE_FORMULA_BINDING_PREFLIGHT_VERSION,
            activation_target=target,
            implementation_authorized=True,
            preflight_branch_ready=ready,
            activation_allowed_now=False,
            required_evidence_before_activation=required,
            hard_fail_if_activated_early=hard_fail,
            claim_boundary=SIDEWALL_ROUTE_FORMULA_BINDING_PREFLIGHT_CLAIM_BOUNDARY,
        )
        for target, ready, required, hard_fail in specs
    ]


def _geometry_from_candidate(row: Mapping[str, Any]) -> str:
    text = f"{row.get('route_key', '')} {row.get('source_case_id', '')}"
    if "rectangle" in text or "theta90" in text:
        return "ideal_rectangle"
    if "taper" in text or "theta85" in text:
        return "trapezoid_tapered_sidewalls"
    return "geometry_family_unspecified"


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
