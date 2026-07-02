"""Wet/surface observation intake for sidewall Package C routes.

The intake turns the wet/surface evidence contract into machine-checkable rows.
It can validate future sidewall-specific or transfer-validated wet observations,
but the default package remains no-observation/no-claim when no wet evidence is
present.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_VERSION = (
    "sidewall_wet_surface_observation_intake_v1"
)
SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_CLAIM_BOUNDARY = (
    "wet_surface_observation_intake_not_yield_not_wet_pass_not_detection_probability"
)
OBSERVATION_MISSING_STATUS = "wet_observation_missing_contract_ready"
OBSERVATION_ACCEPTED_STATUS = (
    "wet_observation_accepted_candidate_not_route_or_detection_claim"
)
OBSERVATION_REJECTED_STATUS = "wet_observation_rejected_missing_required_evidence"
ROUTE_MATRIX_NO_OBSERVATIONS_STATUS = "wet_surface_observation_intake_ready_no_observations"
ROUTE_MATRIX_PARTIAL_STATUS = "wet_surface_observation_intake_partial_observations_not_claim_ready"
ROUTE_MATRIX_ACCEPTED_STATUS = (
    "wet_surface_observation_bundle_candidate_ready_requires_policy_review"
)


@dataclass(frozen=True)
class SidewallWetSurfaceObservationIntakeRow:
    intake_row_id: str
    intake_version: str
    route_candidate_id: str
    route_key: str
    source_case_id: str
    qch_sidecar_id: str
    endpoint_id: str
    target_claim: str
    required_artifact_class: str
    required_fields: str
    minimum_controls: str
    observation_artifact_id: str
    observation_artifact_class: str
    observation_source_artifact: str
    observation_source_sha256: str
    source_geometry_match_level: str
    provided_fields: str
    missing_required_fields: str
    controls_status: str
    replicate_count: int
    uncertainty_interval_status: str
    pre_registered_rule_status: str
    observation_validation_status: str
    accepted_observation_current: bool
    target_claim_current: bool
    wet_pass_probability_current: bool
    clogging_rate_current: bool
    time_to_clog_current: bool
    recovery_current: bool
    yield_current: bool
    detection_probability_current: bool
    route_score_current: bool
    winner_current: bool
    hard_fail_if_promoted_without: str
    next_required_evidence: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SidewallWetSurfaceRouteObservationMatrixRow:
    matrix_row_id: str
    intake_version: str
    route_candidate_id: str
    route_key: str
    source_case_id: str
    qch_sidecar_id: str
    endpoint_count: int
    accepted_endpoint_count: int
    missing_endpoint_count: int
    rejected_endpoint_count: int
    accepted_endpoint_ids: str
    missing_endpoint_ids: str
    rejected_endpoint_ids: str
    route_wet_observation_matrix_status: str
    wet_claim_readiness: str
    wet_pass_probability_current: bool
    clogging_rate_current: bool
    time_to_clog_current: bool
    recovery_current: bool
    yield_current: bool
    detection_probability_current: bool
    route_score_current: bool
    winner_current: bool
    next_required_evidence: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_wet_surface_observation_intake(
    *,
    contract_rows: list[Mapping[str, Any]],
    observation_rows: list[Mapping[str, Any]] | None = None,
) -> tuple[
    list[SidewallWetSurfaceObservationIntakeRow],
    list[SidewallWetSurfaceRouteObservationMatrixRow],
]:
    observations = observation_rows or []
    observation_by_key = {
        (
            str(row.get("route_candidate_id", "")),
            str(row.get("endpoint_id", "")),
        ): row
        for row in observations
    }
    intake_rows = [
        _build_intake_row(contract, observation_by_key.get(_contract_key(contract), {}))
        for contract in contract_rows
    ]
    matrix_rows = _route_matrix_rows(intake_rows)
    return intake_rows, matrix_rows


def wet_surface_observation_template_rows(
    contract_rows: list[Mapping[str, Any]],
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for contract in contract_rows:
        rows.append(
            {
                "route_candidate_id": str(contract.get("route_candidate_id", "")),
                "route_key": str(contract.get("route_key", "")),
                "source_case_id": str(contract.get("source_case_id", "")),
                "qch_sidecar_id": str(contract.get("qch_sidecar_id", "")),
                "endpoint_id": str(contract.get("endpoint_id", "")),
                "target_claim": str(contract.get("target_claim", "")),
                "required_artifact_class": str(contract.get("required_artifact_class", "")),
                "required_fields": str(contract.get("required_fields", "")),
                "minimum_controls": str(contract.get("minimum_controls", "")),
                "observation_artifact_id": "",
                "observation_artifact_class": "",
                "observation_source_artifact": "",
                "observation_source_sha256": "",
                "source_geometry_match_level": "sidewall_specific | validated_transfer",
                "provided_fields": "",
                "controls_status": "controls_pass | controls_missing",
                "replicate_count": "",
                "uncertainty_interval_status": (
                    "uncertainty_interval_present | uncertainty_interval_missing"
                ),
                "pre_registered_rule_status": (
                    "pre_registered | not_required_for_endpoint | missing"
                ),
            }
        )
    return rows


def wet_surface_observation_promotion_update_rows(
    matrix_rows: list[SidewallWetSurfaceRouteObservationMatrixRow],
) -> list[dict[str, Any]]:
    route_ids = ";".join(sorted({row.route_candidate_id for row in matrix_rows}))
    all_accepted = bool(matrix_rows) and all(
        row.route_wet_observation_matrix_status == ROUTE_MATRIX_ACCEPTED_STATUS
        for row in matrix_rows
    )
    return [
        {
            "target_ledger_lane": "wet_wall_interaction",
            "covered_route_candidate_ids": route_ids,
            "previous_status": "wet_surface_evidence_contract_defined_no_wet_validation",
            "new_context_status": (
                ROUTE_MATRIX_ACCEPTED_STATUS
                if all_accepted
                else ROUTE_MATRIX_NO_OBSERVATIONS_STATUS
            ),
            "target_claim_current": False,
            "blocked_promotion": (
                "wet_pass_probability;clogging_rate;time_to_clog;recovery;yield;"
                "route_score;winner;detection_probability"
            ),
            "hard_fail_if": (
                "wet_observation_intake_promoted_without_accepted_endpoint_bundle_and_policy_review"
            ),
            "next_required_evidence": (
                "sidewall-specific or validated-transfer wet observation rows for all endpoints"
            ),
            "claim_boundary": SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_CLAIM_BOUNDARY,
        }
    ]


def _build_intake_row(
    contract: Mapping[str, Any],
    observation: Mapping[str, Any],
) -> SidewallWetSurfaceObservationIntakeRow:
    required_fields = _split_semicolon(contract.get("required_fields"))
    provided_fields = _split_semicolon(observation.get("provided_fields"))
    missing_fields = [field for field in required_fields if field not in provided_fields]
    validation_status = _observation_validation_status(
        contract=contract,
        observation=observation,
        missing_fields=missing_fields,
    )
    accepted = validation_status == OBSERVATION_ACCEPTED_STATUS
    return SidewallWetSurfaceObservationIntakeRow(
        intake_row_id=(
            f"WET-OBS-{contract.get('route_candidate_id', '')}-"
            f"{contract.get('endpoint_id', '')}"
        ),
        intake_version=SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_VERSION,
        route_candidate_id=str(contract.get("route_candidate_id", "")),
        route_key=str(contract.get("route_key", "")),
        source_case_id=str(contract.get("source_case_id", "")),
        qch_sidecar_id=str(contract.get("qch_sidecar_id", "")),
        endpoint_id=str(contract.get("endpoint_id", "")),
        target_claim=str(contract.get("target_claim", "")),
        required_artifact_class=str(contract.get("required_artifact_class", "")),
        required_fields=str(contract.get("required_fields", "")),
        minimum_controls=str(contract.get("minimum_controls", "")),
        observation_artifact_id=str(observation.get("observation_artifact_id", "")),
        observation_artifact_class=str(observation.get("observation_artifact_class", "")),
        observation_source_artifact=str(observation.get("observation_source_artifact", "")),
        observation_source_sha256=str(observation.get("observation_source_sha256", "")),
        source_geometry_match_level=str(observation.get("source_geometry_match_level", "")),
        provided_fields=str(observation.get("provided_fields", "")),
        missing_required_fields=";".join(missing_fields),
        controls_status=str(observation.get("controls_status", "")),
        replicate_count=_int_value(observation.get("replicate_count")),
        uncertainty_interval_status=str(
            observation.get("uncertainty_interval_status", "")
        ),
        pre_registered_rule_status=str(
            observation.get("pre_registered_rule_status", "")
        ),
        observation_validation_status=validation_status,
        accepted_observation_current=accepted,
        target_claim_current=accepted,
        wet_pass_probability_current=False,
        clogging_rate_current=False,
        time_to_clog_current=False,
        recovery_current=False,
        yield_current=False,
        detection_probability_current=False,
        route_score_current=False,
        winner_current=False,
        hard_fail_if_promoted_without=str(contract.get("hard_fail_if_missing", "")),
        next_required_evidence=_next_required_evidence(
            contract=contract,
            observation=observation,
            missing_fields=missing_fields,
            validation_status=validation_status,
        ),
        claim_boundary=SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_CLAIM_BOUNDARY,
    )


def _contract_key(contract: Mapping[str, Any]) -> tuple[str, str]:
    return (
        str(contract.get("route_candidate_id", "")),
        str(contract.get("endpoint_id", "")),
    )


def _observation_validation_status(
    *,
    contract: Mapping[str, Any],
    observation: Mapping[str, Any],
    missing_fields: list[str],
) -> str:
    if not observation:
        return OBSERVATION_MISSING_STATUS
    if str(observation.get("observation_artifact_class", "")) != str(
        contract.get("required_artifact_class", "")
    ):
        return OBSERVATION_REJECTED_STATUS
    if missing_fields:
        return OBSERVATION_REJECTED_STATUS
    if str(observation.get("observation_source_sha256", "")) == "":
        return OBSERVATION_REJECTED_STATUS
    if str(observation.get("controls_status", "")) != "controls_pass":
        return OBSERVATION_REJECTED_STATUS
    if str(observation.get("source_geometry_match_level", "")) not in {
        "sidewall_specific",
        "validated_transfer",
    }:
        return OBSERVATION_REJECTED_STATUS
    if _int_value(observation.get("replicate_count")) < _minimum_replicates(
        str(contract.get("endpoint_id", ""))
    ):
        return OBSERVATION_REJECTED_STATUS
    if _requires_uncertainty(str(contract.get("endpoint_id", ""))) and str(
        observation.get("uncertainty_interval_status", "")
    ) != "uncertainty_interval_present":
        return OBSERVATION_REJECTED_STATUS
    if _requires_preregistration(str(contract.get("endpoint_id", ""))) and str(
        observation.get("pre_registered_rule_status", "")
    ) != "pre_registered":
        return OBSERVATION_REJECTED_STATUS
    return OBSERVATION_ACCEPTED_STATUS


def _route_matrix_rows(
    intake_rows: list[SidewallWetSurfaceObservationIntakeRow],
) -> list[SidewallWetSurfaceRouteObservationMatrixRow]:
    route_ids = sorted({row.route_candidate_id for row in intake_rows})
    rows: list[SidewallWetSurfaceRouteObservationMatrixRow] = []
    for route_id in route_ids:
        group = [row for row in intake_rows if row.route_candidate_id == route_id]
        accepted = [row.endpoint_id for row in group if row.accepted_observation_current]
        missing = [
            row.endpoint_id
            for row in group
            if row.observation_validation_status == OBSERVATION_MISSING_STATUS
        ]
        rejected = [
            row.endpoint_id
            for row in group
            if row.observation_validation_status == OBSERVATION_REJECTED_STATUS
        ]
        status = _route_status(group, accepted, missing, rejected)
        first = group[0]
        rows.append(
            SidewallWetSurfaceRouteObservationMatrixRow(
                matrix_row_id=f"WET-OBS-MATRIX-{route_id}",
                intake_version=SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_VERSION,
                route_candidate_id=route_id,
                route_key=first.route_key,
                source_case_id=first.source_case_id,
                qch_sidecar_id=first.qch_sidecar_id,
                endpoint_count=len(group),
                accepted_endpoint_count=len(accepted),
                missing_endpoint_count=len(missing),
                rejected_endpoint_count=len(rejected),
                accepted_endpoint_ids=";".join(accepted),
                missing_endpoint_ids=";".join(missing),
                rejected_endpoint_ids=";".join(rejected),
                route_wet_observation_matrix_status=status,
                wet_claim_readiness=(
                    "wet_endpoint_bundle_candidate_ready_policy_review_required"
                    if status == ROUTE_MATRIX_ACCEPTED_STATUS
                    else "wet_endpoint_bundle_not_claim_ready"
                ),
                wet_pass_probability_current=False,
                clogging_rate_current=False,
                time_to_clog_current=False,
                recovery_current=False,
                yield_current=False,
                detection_probability_current=False,
                route_score_current=False,
                winner_current=False,
                next_required_evidence=(
                    "accepted sidewall-specific or validated-transfer observations for missing/rejected endpoints"
                ),
                claim_boundary=SIDEWALL_WET_SURFACE_OBSERVATION_INTAKE_CLAIM_BOUNDARY,
            )
        )
    return rows


def _route_status(
    group: list[SidewallWetSurfaceObservationIntakeRow],
    accepted: list[str],
    missing: list[str],
    rejected: list[str],
) -> str:
    if accepted and len(accepted) == len(group):
        return ROUTE_MATRIX_ACCEPTED_STATUS
    if accepted or rejected:
        return ROUTE_MATRIX_PARTIAL_STATUS
    if missing:
        return ROUTE_MATRIX_NO_OBSERVATIONS_STATUS
    return ROUTE_MATRIX_PARTIAL_STATUS


def _next_required_evidence(
    *,
    contract: Mapping[str, Any],
    observation: Mapping[str, Any],
    missing_fields: list[str],
    validation_status: str,
) -> str:
    if validation_status == OBSERVATION_ACCEPTED_STATUS:
        return "policy review before target claim promotion"
    if not observation:
        return str(contract.get("required_artifact_class", ""))
    if missing_fields:
        return f"missing fields: {';'.join(missing_fields)}"
    return str(contract.get("minimum_controls", ""))


def _split_semicolon(value: Any) -> list[str]:
    return [
        part.strip()
        for part in str(value or "").split(";")
        if part.strip()
    ]


def _minimum_replicates(endpoint_id: str) -> int:
    if endpoint_id in {"material_surface_identity", "ev_sample_panel"}:
        return 1
    return 3


def _requires_uncertainty(endpoint_id: str) -> bool:
    return endpoint_id not in {"material_surface_identity", "ev_sample_panel"}


def _requires_preregistration(endpoint_id: str) -> bool:
    return endpoint_id in {"wet_pass_probability", "yield_bridge", "clogging_time_series"}


def _int_value(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0
