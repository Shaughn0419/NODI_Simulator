"""Wet/surface evidence contract rows for sidewall route promotion.

The contract defines what must exist before wet pass, clogging, recovery, yield,
or detection-related route claims can be promoted. It is intentionally an
evidence contract, not a wet-performance model.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any, Mapping


SIDEWALL_WET_SURFACE_CONTRACT_VERSION = "sidewall_wet_surface_evidence_contract_v1"
SIDEWALL_WET_SURFACE_CONTRACT_CLAIM_BOUNDARY = (
    "wet_surface_contract_not_wet_validation_not_yield_not_detection_probability"
)

WET_SURFACE_ENDPOINTS: tuple[dict[str, str], ...] = (
    {
        "endpoint_id": "material_surface_identity",
        "target_claim": "wet_surface_transferability",
        "required_artifact_class": "surface_material_metrology_or_process_record",
        "required_fields": (
            "substrate_material;surface_treatment;oxide_or_coating_state;"
            "surface_charge_or_zeta_context;roughness_rms_nm;contact_angle_or_wetting_context"
        ),
        "minimum_controls": "matched rectangle or accepted reference surface;process lot traceability",
        "acceptance_basis": "source-locked metrology/process context before wet evidence transfer",
        "hard_fail_if_missing": "wet_context_transferred_without_surface_identity",
    },
    {
        "endpoint_id": "ev_sample_panel",
        "target_claim": "ev_panel_representativeness",
        "required_artifact_class": "ev_characterization_panel",
        "required_fields": (
            "particle_size_distribution;concentration;buffer;ionic_strength;pH;"
            "protein_or_contaminant_context;sample_storage_and_handling"
        ),
        "minimum_controls": "blank buffer;size/control particle;EV prep provenance",
        "acceptance_basis": "EV panel metadata sufficient to interpret pass/recovery and detection",
        "hard_fail_if_missing": "yield_claim_without_ev_panel_metadata",
    },
    {
        "endpoint_id": "adhesion_wall_interaction",
        "target_claim": "adhesion_or_wall_loss",
        "required_artifact_class": "wet_wall_interaction_assay",
        "required_fields": (
            "input_count;output_count;wall_exposure_time_s;flow_condition;"
            "surface_condition;replicate_id;uncertainty_interval"
        ),
        "minimum_controls": "no-EV blank;reference-channel comparison;replicates",
        "acceptance_basis": "sidewall-specific adhesion or loss assay before wall-loss model",
        "hard_fail_if_missing": "adhesion_probability_from_geometry_or_nearest_wall_distance",
    },
    {
        "endpoint_id": "clogging_time_series",
        "target_claim": "clogging_rate_or_time_to_clog",
        "required_artifact_class": "flow_or_event_time_series",
        "required_fields": (
            "time_s;pressure_or_flow_condition;event_rate_or_current_trace;"
            "blockage_definition;reset_or_flush_state;right_censoring_policy"
        ),
        "minimum_controls": "blank run;particle-free buffer;repeat run;open-channel baseline",
        "acceptance_basis": "time-resolved evidence before clogging rate or time-to-clog",
        "hard_fail_if_missing": "clogging_rate_from_static_throat_margin",
    },
    {
        "endpoint_id": "recovery_flush",
        "target_claim": "recovery_or_reusable_operation",
        "required_artifact_class": "flush_recovery_protocol_result",
        "required_fields": (
            "clog_or_loss_trigger;flush_protocol;post_flush_flow_or_event_recovery;"
            "cycle_index;failure_definition;replicate_id"
        ),
        "minimum_controls": "pre/post baseline;blank/control channel;cycle repeat",
        "acceptance_basis": "protocol-bound recovery evidence before recovery claims",
        "hard_fail_if_missing": "recovery_claim_without_flush_protocol",
    },
    {
        "endpoint_id": "wet_pass_probability",
        "target_claim": "wet_pass_probability",
        "required_artifact_class": "pre_registered_wet_pass_fail_table",
        "required_fields": (
            "pass_fail_rule;route_geometry_id;run_id;sample_id;replicate_id;"
            "censoring_policy;confidence_interval;failure_reason"
        ),
        "minimum_controls": "pre-registered threshold;negative control;positive/control particle",
        "acceptance_basis": "binary or probabilistic pass/fail evidence with uncertainty",
        "hard_fail_if_missing": "wet_pass_probability_from_descriptor_or_surrogate",
    },
    {
        "endpoint_id": "yield_bridge",
        "target_claim": "yield",
        "required_artifact_class": "input_output_mass_or_count_balance",
        "required_fields": (
            "input_amount;output_amount;collection_window;loss_budget;"
            "normalization_basis;uncertainty_interval;replicate_id"
        ),
        "minimum_controls": "blank correction;collection efficiency control;mass/count calibration",
        "acceptance_basis": "input-output balance before yield claim",
        "hard_fail_if_missing": "yield_from_detection_or_geometry_surrogate",
    },
)


@dataclass(frozen=True)
class SidewallWetSurfaceContractRow:
    contract_id: str
    contract_version: str
    route_candidate_id: str
    route_key: str
    source_case_id: str
    source_width_nm: int
    source_depth_nm: int
    sidewall_deg_comsol: float
    qch_sidecar_id: str
    endpoint_id: str
    evidence_lane: str
    target_claim: str
    target_claim_current: bool
    current_wet_lane_status: str
    nearest_wet_context_status: str
    required_artifact_class: str
    required_fields: str
    minimum_controls: str
    acceptance_basis: str
    hard_fail_if_missing: str
    contract_status: str
    next_required_evidence: str
    not_wet_pass_probability: bool
    not_clogging_rate: bool
    not_time_to_clog: bool
    not_recovery: bool
    not_yield: bool
    not_detection_probability: bool
    not_route_score: bool
    not_winner: bool
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_wet_surface_contract_rows(
    promotion_lane_rows: list[Mapping[str, Any]],
    wet_context_rows: list[Mapping[str, Any]],
) -> list[SidewallWetSurfaceContractRow]:
    """Build one contract row per route candidate and wet/surface endpoint."""
    wet_lane_by_route = {
        str(row.get("route_candidate_id", "")): row
        for row in promotion_lane_rows
        if str(row.get("evidence_lane", "")) == "wet_wall_interaction"
    }
    wet_context_by_route = {
        str(row.get("route_candidate_id", "")): row for row in wet_context_rows
    }
    output: list[SidewallWetSurfaceContractRow] = []
    for route_id, lane in sorted(wet_lane_by_route.items()):
        source_case_id = str(lane.get("source_case_id", ""))
        wet_context = wet_context_by_route.get(route_id, {})
        nearest_context = str(
            wet_context.get("wet_context_status", "nearest_wet_context_missing")
        )
        for endpoint in WET_SURFACE_ENDPOINTS:
            output.append(
                SidewallWetSurfaceContractRow(
                    contract_id=f"WET-SURFACE-CONTRACT-{route_id}-{endpoint['endpoint_id']}",
                    contract_version=SIDEWALL_WET_SURFACE_CONTRACT_VERSION,
                    route_candidate_id=route_id,
                    route_key=str(lane.get("route_key", "")),
                    source_case_id=source_case_id,
                    source_width_nm=_parse_named_int(source_case_id, "W"),
                    source_depth_nm=_parse_named_int(source_case_id, "D"),
                    sidewall_deg_comsol=_parse_theta(source_case_id),
                    qch_sidecar_id=str(lane.get("qch_sidecar_id", "")),
                    endpoint_id=endpoint["endpoint_id"],
                    evidence_lane="wet_wall_interaction",
                    target_claim=endpoint["target_claim"],
                    target_claim_current=False,
                    current_wet_lane_status=str(
                        lane.get("current_status", "wet_wall_interaction_status_missing")
                    ),
                    nearest_wet_context_status=nearest_context,
                    required_artifact_class=endpoint["required_artifact_class"],
                    required_fields=endpoint["required_fields"],
                    minimum_controls=endpoint["minimum_controls"],
                    acceptance_basis=endpoint["acceptance_basis"],
                    hard_fail_if_missing=endpoint["hard_fail_if_missing"],
                    contract_status=(
                        "wet_surface_contract_defined_no_wet_validation"
                    ),
                    next_required_evidence=(
                        "sidewall-specific or validated-transfer wet/surface evidence bundle"
                    ),
                    not_wet_pass_probability=True,
                    not_clogging_rate=True,
                    not_time_to_clog=True,
                    not_recovery=True,
                    not_yield=True,
                    not_detection_probability=True,
                    not_route_score=True,
                    not_winner=True,
                    claim_boundary=SIDEWALL_WET_SURFACE_CONTRACT_CLAIM_BOUNDARY,
                )
            )
    return output


def wet_surface_promotion_update_rows(
    rows: list[SidewallWetSurfaceContractRow],
) -> list[dict[str, str]]:
    route_ids = sorted({row.route_candidate_id for row in rows})
    return [
        {
            "target_ledger_lane": "wet_wall_interaction",
            "covered_route_candidate_ids": ";".join(route_ids),
            "previous_status": "wet_sidewall_evidence_missing",
            "new_context_status": "wet_surface_evidence_contract_defined_no_wet_validation",
            "target_claim_current": "false",
            "blocked_promotion": (
                "wet_pass_probability;clogging_rate;time_to_clog;recovery;yield;"
                "route_score;winner;detection_probability"
            ),
            "hard_fail_if": (
                "wet_surface_contract_or_context_promoted_without_experiment_or_validated_transfer"
            ),
            "next_required_evidence": (
                "sidewall-specific wet EV evidence bundle with material/surface identity, "
                "EV characterization, controls, time-series clogging, recovery/flush, and yield balance"
            ),
            "claim_boundary": SIDEWALL_WET_SURFACE_CONTRACT_CLAIM_BOUNDARY,
        }
    ]


def _parse_named_int(source_case_id: str, name: str) -> int:
    match = re.search(rf"{re.escape(name)}(\d+)", source_case_id)
    return int(match.group(1)) if match else 0


def _parse_theta(source_case_id: str) -> float:
    match = re.search(r"theta(\d+(?:p\d+)?)", source_case_id)
    if not match:
        return 0.0
    return float(match.group(1).replace("p", "."))
