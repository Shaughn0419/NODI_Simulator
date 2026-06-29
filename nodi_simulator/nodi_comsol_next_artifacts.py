"""Executable contracts for the next NODI/COMSOL handoff artifacts.

The constants in this module mirror the Report 156 patched CSV contracts.
They intentionally validate claim boundaries and provenance semantics before
any future runner is allowed to promote an artifact.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re
from typing import Any

from nodi_simulator.realism_v2_io import read_csv_rows, sha256_file, write_csv_rows, write_json_atomic


POSITION_RESPONSE_ARTIFACT = "NODI_POSITION_RESPONSE_SURFACE"
POSITION_RESPONSE_VERSION = "NODI_POSITION_RESPONSE_SURFACE_V1"
POSITION_RESPONSE_BIN_SOURCE_ARTIFACT = "NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE"
POSITION_RESPONSE_BIN_SOURCE_VERSION = (
    "NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_V1"
)

APERTURE_SURROGATE_ARTIFACT = "NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY"
APERTURE_SURROGATE_VERSION = "NODI_EFFECTIVE_APERTURE_SURROGATE_V1"

GEOMETRY_DESCRIPTOR_SHA256 = (
    "1198055754C41710A4821894ECB749660E5EF4A14B2E0FC647789BA31A0B38A2"
)
GEOMETRY_DESCRIPTOR_VERSION = "route_geometry_id_comsol_v1_contract_20260616"
GEOMETRY_DESCRIPTOR_CLAIM_BOUNDARY = (
    "nominal_surrogate_geometry_descriptor_not_measured_not_optical_solver"
)

PRS_NEUTRAL_FLOW_CONDITION_ID = "nodi_position_response_surface_v1_not_comsol_transport"
PRS_FLOW_CONDITION_SCOPE = "nodi_response_surface_not_transport_distribution"
PRS_FLOW_CONDITION_CLAIM_BOUNDARY = (
    "nodi_synthetic_position_response_not_transport_occupancy"
)
PRS_CLAIM_BOUNDARY = "nodi_position_response_surface_conditional_optical_response_only"
PRS_POSITION_DISTRIBUTION_BASIS = "nodi_synthetic_initial_position"
QCH_FLOW_CONDITION_ID = "p1b_w800_qch_splitmid_20260617"

EAS_CLAIM_BOUNDARY = "effective_aperture_surrogate_sensitivity_only"
EAS_WEIGHTING_BASIS = "fullgrid_recommendation_eligible_rank_contract"
EAS_RANK_SOURCE = (
    "exports/nodi_comsol_handoff_v1/"
    "NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv"
)
EAS_RECOMMENDATION_RANK_SOURCE = "recommendation_eligible_rank"

PENDING_FLOW_SHA = "pending_until_artifact_generation"

ROWS_PER_ROUTE_DIAMETER_VIEW = 467
EDGE_BASE_BIN_COUNT = 20
XZ_BASE_BIN_COUNT = 441
SPECIAL_AGGREGATE_COUNT_PER_DISTRIBUTION = 3
PRS_MIN_EVENTS_PER_BIN_FOR_PRODUCTION = 100

PRS_SMOKE_MANIFEST_FILENAME = "NODI_POSITION_RESPONSE_SURFACE_SMOKE_MANIFEST_20260617.csv"
EAS_SMOKE_MANIFEST_FILENAME = (
    "NODI_EFFECTIVE_APERTURE_SURROGATE_SMOKE_MANIFEST_20260617.csv"
)
NEXT_ARTIFACTS_SMOKE_INDEX_FILENAME = "NODI_NEXT_ARTIFACTS_SMOKE_MANIFEST_INDEX_20260617.csv"
NEXT_ARTIFACTS_SMOKE_METADATA_FILENAME = (
    "NODI_NEXT_ARTIFACTS_SMOKE_MANIFEST_METADATA_20260617.json"
)
NEXT_ARTIFACTS_RUNNER_PREFLIGHT_REPORT_FILENAME = (
    "NODI_NEXT_ARTIFACTS_NO_EXECUTION_PREFLIGHT_REPORT_20260617.json"
)
NEXT_ARTIFACTS_RUNNER_PREFLIGHT_ISSUES_FILENAME = (
    "NODI_NEXT_ARTIFACTS_NO_EXECUTION_PREFLIGHT_ISSUES_20260617.csv"
)
PRS_PLAN_BLUEPRINT_FILENAME = "NODI_POSITION_RESPONSE_SURFACE_PLAN_BLUEPRINT_20260617.csv"
EAS_PLAN_BLUEPRINT_FILENAME = (
    "NODI_EFFECTIVE_APERTURE_SURROGATE_PLAN_BLUEPRINT_20260617.csv"
)
NEXT_ARTIFACTS_PLAN_BLUEPRINT_INDEX_FILENAME = (
    "NODI_NEXT_ARTIFACTS_PLAN_BLUEPRINT_INDEX_20260617.csv"
)
NEXT_ARTIFACTS_PLAN_BLUEPRINT_METADATA_FILENAME = (
    "NODI_NEXT_ARTIFACTS_PLAN_BLUEPRINT_METADATA_20260617.json"
)
NEXT_ARTIFACTS_AUTHORIZATION_GATE_RECORD_FILENAME = (
    "NODI_NEXT_ARTIFACTS_RUNNER_AUTHORIZATION_GATE_RECORD_20260617.json"
)
NEXT_ARTIFACTS_AUTHORIZATION_GATE_ISSUES_FILENAME = (
    "NODI_NEXT_ARTIFACTS_RUNNER_AUTHORIZATION_GATE_ISSUES_20260617.csv"
)
PRS_RUNNER_LAUNCH_PLAN_FILENAME = (
    "NODI_POSITION_RESPONSE_SURFACE_RUNNER_LAUNCH_PLAN_20260618.json"
)
EAS_RUNNER_LAUNCH_PLAN_FILENAME = (
    "NODI_EFFECTIVE_APERTURE_SURROGATE_RUNNER_LAUNCH_PLAN_20260618.json"
)
NEXT_ARTIFACTS_BOUNDED_SMOKE_READINESS_REPORT_FILENAME = (
    "NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_READINESS_REPORT_20260618.json"
)
NEXT_ARTIFACTS_BOUNDED_SMOKE_READINESS_ISSUES_FILENAME = (
    "NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_READINESS_ISSUES_20260618.csv"
)
PRS_BOUNDED_SMOKE_EXECUTION_MANIFEST_FILENAME = (
    "NODI_POSITION_RESPONSE_SURFACE_BOUNDED_SMOKE_EXECUTION_MANIFEST_20260618.csv"
)
EAS_BOUNDED_SMOKE_EXECUTION_MANIFEST_FILENAME = (
    "NODI_EFFECTIVE_APERTURE_SURROGATE_BOUNDED_SMOKE_EXECUTION_MANIFEST_20260618.csv"
)
NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_REPORT_FILENAME = (
    "NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_REPORT_20260618.json"
)
NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_ISSUES_FILENAME = (
    "NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_ISSUES_20260618.csv"
)
NEXT_ARTIFACTS_PRODUCTION_GENERATION_REPORT_FILENAME = (
    "NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_REPORT_20260618.json"
)
NEXT_ARTIFACTS_PRODUCTION_GENERATION_ISSUES_FILENAME = (
    "NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_ISSUES_20260618.csv"
)
NEXT_ARTIFACTS_PRODUCTION_GENERATION_BLOCKERS_FILENAME = (
    "NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_BLOCKERS_20260618.csv"
)
PRS_SOURCE_PREFLIGHT_REPORT_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_AVAILABILITY_PREFLIGHT_REPORT_20260618.json"
)
PRS_SOURCE_PREFLIGHT_CANDIDATES_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_AVAILABILITY_PREFLIGHT_CANDIDATES_20260618.csv"
)
PRS_SOURCE_PREFLIGHT_BLOCKERS_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_AVAILABILITY_PREFLIGHT_BLOCKERS_20260618.csv"
)
PRS_SOURCE_PREFLIGHT_ISSUES_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_AVAILABILITY_PREFLIGHT_ISSUES_20260618.csv"
)
PRS_SOURCE_SUFFICIENCY_REPORT_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_NUMERIC_SUFFICIENCY_REPORT_20260618.json"
)
PRS_SOURCE_SUFFICIENCY_CANDIDATES_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_NUMERIC_SUFFICIENCY_CANDIDATES_20260618.csv"
)
PRS_SOURCE_SUFFICIENCY_BLOCKERS_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_NUMERIC_SUFFICIENCY_BLOCKERS_20260618.csv"
)
PRS_SOURCE_SUFFICIENCY_JOB_PLAN_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_NUMERIC_SUFFICIENCY_JOB_PLAN_20260618.csv"
)
PRS_SOURCE_SUFFICIENCY_ISSUES_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_NUMERIC_SUFFICIENCY_ISSUES_20260618.csv"
)
PRS_SOURCE_PRODUCTION_ELIGIBILITY_REPORT_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_PRODUCTION_ELIGIBILITY_REPORT_20260618.json"
)
PRS_SOURCE_PRODUCTION_ELIGIBILITY_CANDIDATES_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_PRODUCTION_ELIGIBILITY_CANDIDATES_20260618.csv"
)
PRS_SOURCE_PRODUCTION_ELIGIBILITY_GROUPS_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_PRODUCTION_ELIGIBILITY_GROUPS_20260618.csv"
)
PRS_SOURCE_PRODUCTION_ELIGIBILITY_BLOCKERS_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_PRODUCTION_ELIGIBILITY_BLOCKERS_20260618.csv"
)
PRS_SOURCE_PRODUCTION_ELIGIBILITY_ISSUES_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_PRODUCTION_ELIGIBILITY_ISSUES_20260618.csv"
)
PRS_EDGE_PRIMARY_CANDIDATE_FILENAME = (
    "NODI_POSITION_RESPONSE_SURFACE_EDGE_PRIMARY_CANDIDATE_20260618.csv"
)
PRS_EDGE_PRIMARY_CANDIDATE_REPORT_FILENAME = (
    "NODI_POSITION_RESPONSE_SURFACE_EDGE_PRIMARY_CANDIDATE_REPORT_20260618.json"
)
PRS_EDGE_PRIMARY_CANDIDATE_ISSUES_FILENAME = (
    "NODI_POSITION_RESPONSE_SURFACE_EDGE_PRIMARY_CANDIDATE_ISSUES_20260618.csv"
)
PRS_SOURCE_ACCUMULATION_REPORT_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_JOB_PLAN_REPORT_20260618.json"
)
PRS_SOURCE_ACCUMULATION_JOB_PLAN_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_JOB_PLAN_20260618.csv"
)
PRS_SOURCE_ACCUMULATION_BLOCKERS_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_JOB_PLAN_BLOCKERS_20260618.csv"
)
PRS_SOURCE_ACCUMULATION_ISSUES_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_JOB_PLAN_ISSUES_20260618.csv"
)
PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_REPORT_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_BOUNDED_SHARD_REPORT_20260618.json"
)
PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_EVENTS_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_BOUNDED_SHARD_EVENTS_20260618.csv"
)
PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_SOURCE_FILENAME = (
    "NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_ACCUMULATION_BOUNDED_SHARD_20260618.csv"
)
PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MANIFEST_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_BOUNDED_SHARD_EXECUTION_MANIFEST_20260618.csv"
)
PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_ISSUES_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_BOUNDED_SHARD_ISSUES_20260618.csv"
)
PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_REPORT_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_REPORT_20260618.json"
)
PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARDS_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARDS_20260618.csv"
)
PRS_SOURCE_ACCUMULATION_CAMPAIGN_JOB_SCHEDULE_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_JOB_SCHEDULE_20260618.csv"
)
PRS_SOURCE_ACCUMULATION_CAMPAIGN_ISSUES_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_ISSUES_20260618.csv"
)
PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_REPORT_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_REPORT_20260618.json"
)
PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_SHARD_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_SHARD_20260618.csv"
)
PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_ISSUES_FILENAME = (
    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_ISSUES_20260618.csv"
)
PRS_BIN_SOURCE_SMOKE_EVENTS_FILENAME = (
    "NODI_POSITION_RESPONSE_BIN_SOURCE_SMOKE_EVENTS_20260618.csv"
)
PRS_BIN_SOURCE_SMOKE_SOURCE_FILENAME = (
    "NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_SMOKE_20260618.csv"
)
PRS_BIN_SOURCE_SMOKE_REPORT_FILENAME = (
    "NODI_POSITION_RESPONSE_BIN_SOURCE_SMOKE_REPORT_20260618.json"
)
PRS_REAL_EVENT_SOURCE_SMOKE_EVENTS_FILENAME = (
    "NODI_POSITION_RESPONSE_REAL_EVENT_SOURCE_SMOKE_EVENTS_20260618.csv"
)
PRS_REAL_EVENT_SOURCE_SMOKE_SOURCE_FILENAME = (
    "NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_REAL_EVENT_SMOKE_20260618.csv"
)
PRS_REAL_EVENT_SOURCE_SMOKE_REPORT_FILENAME = (
    "NODI_POSITION_RESPONSE_REAL_EVENT_SOURCE_SMOKE_REPORT_20260618.json"
)
PRS_RUNNER_SLICE_SOURCE_EXPORT_EVENTS_FILENAME = (
    "NODI_POSITION_RESPONSE_RUNNER_SLICE_SOURCE_EVENTS_20260618.csv"
)
PRS_RUNNER_SLICE_SOURCE_EXPORT_SOURCE_FILENAME = (
    "NODI_POSITION_RESPONSE_BIN_CONDITIONED_SOURCE_RUNNER_SLICE_20260618.csv"
)
PRS_RUNNER_SLICE_SOURCE_EXPORT_REPORT_FILENAME = (
    "NODI_POSITION_RESPONSE_RUNNER_SLICE_SOURCE_EXPORT_REPORT_20260618.json"
)
EAS_PRODUCTION_FILENAME = "NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY.csv"
EAS_SELECTOR_POLICY_METADATA_FILENAME = (
    "NODI_EFFECTIVE_APERTURE_SURROGATE_SELECTOR_POLICY_20260618.json"
)
PRS_PRODUCTION_FILENAME = "NODI_POSITION_RESPONSE_SURFACE.csv"
PLAN_ONLY_EXECUTION_STATUS = "PLAN_ONLY_NOT_EXECUTED"
AUTHORIZATION_GATE_PASS_STATUS = "PASS_AUTHORIZATION_GATE_RECORD_NOT_AUTHORIZED"
AUTHORIZATION_GATE_BLOCKED_STATUS = "BLOCKED_AUTHORIZATION_GATE_INPUTS"
RUNNER_IMPLEMENTATION_READY_STATUS = "RUNNER_IMPLEMENTATION_READY_NOT_EXECUTED"
RUNNER_IMPLEMENTATION_BLOCKED_STATUS = "RUNNER_IMPLEMENTATION_BLOCKED_NOT_EXECUTED"
BOUNDED_SMOKE_READINESS_PASS_STATUS = (
    "PASS_BOUNDED_SMOKE_READINESS_PREFLIGHT_NOT_AUTHORIZED"
)
BOUNDED_SMOKE_READINESS_BLOCKED_STATUS = (
    "BLOCKED_BOUNDED_SMOKE_READINESS_PREFLIGHT_NOT_AUTHORIZED"
)
BOUNDED_SMOKE_EXECUTION_PASS_STATUS = "PASS_BOUNDED_SMOKE_EXECUTION_CONTRACT_ONLY"
BOUNDED_SMOKE_EXECUTION_BLOCKED_STATUS = "BLOCKED_BOUNDED_SMOKE_EXECUTION_CONTRACT_ONLY"
BOUNDED_SMOKE_EXECUTION_ROW_STATUS = "BOUNDED_SMOKE_EXECUTED_CONTRACT_ONLY"
PRODUCTION_GENERATION_BLOCKED_STATUS = "BLOCKED_PRODUCTION_GENERATION_INPUTS"
PRODUCTION_GENERATION_PARTIAL_STATUS = "PARTIAL_PRODUCTION_GENERATION_EAS_WRITTEN_PRS_BLOCKED"
PRODUCTION_GENERATION_PASS_STATUS = "PASS_PRODUCTION_GENERATION"
PRS_SOURCE_PREFLIGHT_BLOCKED_STATUS = "BLOCKED_PRS_SOURCE_AVAILABILITY_PREFLIGHT"
PRS_SOURCE_PREFLIGHT_PASS_STATUS = (
    "PASS_PRS_SOURCE_AVAILABILITY_PREFLIGHT_NOT_PRODUCTION"
)
PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS = (
    "BLOCKED_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT"
)
PRS_SOURCE_SUFFICIENCY_PASS_STATUS = (
    "PASS_PRS_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT_NOT_PRODUCTION"
)
PRS_SOURCE_PRODUCTION_ELIGIBILITY_BLOCKED_STATUS = (
    "BLOCKED_PRS_SOURCE_PRODUCTION_ELIGIBILITY_PREFLIGHT"
)
PRS_SOURCE_PRODUCTION_ELIGIBILITY_PASS_STATUS = (
    "PASS_PRS_SOURCE_PRODUCTION_ELIGIBILITY_EDGE_PRIMARY_NOT_PRODUCTION"
)
PRS_EDGE_PRIMARY_CANDIDATE_PASS_STATUS = (
    "PASS_PRS_EDGE_PRIMARY_CANDIDATE_VALIDATED_NOT_PROMOTED"
)
PRS_EDGE_PRIMARY_CANDIDATE_BLOCKED_STATUS = (
    "BLOCKED_PRS_EDGE_PRIMARY_CANDIDATE_NOT_PROMOTED"
)
PRS_SOURCE_ACCUMULATION_PASS_STATUS = (
    "PASS_PRS_SOURCE_ACCUMULATION_JOB_PLAN_NOT_EXECUTED"
)
PRS_SOURCE_ACCUMULATION_BLOCKED_STATUS = (
    "BLOCKED_PRS_SOURCE_ACCUMULATION_JOB_PLAN_INPUTS"
)
PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_PASS_STATUS = (
    "PASS_PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_EXECUTION_NOT_PRODUCTION"
)
PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_BLOCKED_STATUS = (
    "BLOCKED_PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_EXECUTION_NOT_PRODUCTION"
)
PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_PASS_STATUS = (
    "PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_NOT_EXECUTED"
)
PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_BLOCKED_STATUS = (
    "BLOCKED_PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_INPUTS"
)
PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_PASS_STATUS = (
    "PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_NOT_EXECUTED"
)
PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_BLOCKED_STATUS = (
    "BLOCKED_PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_INPUTS"
)
PRS_BIN_SOURCE_SMOKE_PASS_STATUS = "PASS_PRS_BIN_SOURCE_SMOKE_NOT_PRODUCTION"
PRS_BIN_SOURCE_SMOKE_BLOCKED_STATUS = "BLOCKED_PRS_BIN_SOURCE_SMOKE_NOT_PRODUCTION"
PRS_REAL_EVENT_SOURCE_SMOKE_PASS_STATUS = (
    "PASS_PRS_REAL_EVENT_SOURCE_SMOKE_PREFLIGHT_ONLY_NOT_PRS_PRODUCTION"
)
PRS_REAL_EVENT_SOURCE_SMOKE_BLOCKED_STATUS = (
    "BLOCKED_PRS_REAL_EVENT_SOURCE_SMOKE_PREFLIGHT_ONLY_NOT_PRS_PRODUCTION"
)
PRS_RUNNER_SLICE_SOURCE_EXPORT_PASS_STATUS = (
    "PASS_PRS_RUNNER_SLICE_SOURCE_EXPORT_PREFLIGHT_ONLY_NOT_PRS_PRODUCTION"
)
PRS_RUNNER_SLICE_SOURCE_EXPORT_BLOCKED_STATUS = (
    "BLOCKED_PRS_RUNNER_SLICE_SOURCE_EXPORT_PREFLIGHT_ONLY_NOT_PRS_PRODUCTION"
)
RUNNER_IMPLEMENTATION_AUTHORIZATION_PHRASE = (
    "authorize NODI next-artifacts runner implementation"
)
BOUNDED_SMOKE_AUTHORIZATION_PHRASE = (
    "authorize NODI next-artifacts bounded smoke execution"
)
PRODUCTION_GENERATION_AUTHORIZATION_PHRASE = (
    "authorize NODI next-artifacts production generation"
)
PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_AUTHORIZATION_PHRASE = (
    "authorize NODI PRS source accumulation bounded shard execution"
)
FUTURE_AUTHORIZATION_PHRASE_MATCH_RUNNER_IMPLEMENTATION = (
    "PHRASE_MATCH_RUNNER_IMPLEMENTATION_ONLY_NO_EXECUTION"
)
FUTURE_AUTHORIZATION_PHRASE_MATCH_BLOCKED_NO_EXECUTION = (
    "PHRASE_MATCH_BUT_PREREQUISITES_BLOCKED_NO_EXECUTION"
)
FUTURE_AUTHORIZATION_PHRASE_MISMATCH = "PHRASE_MISMATCH_NOT_AUTHORIZED"
FUTURE_AUTHORIZATION_ACTION_INVALID = "INVALID_FUTURE_AUTHORIZATION_ACTION"

SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
ROUTE_RE = re.compile(r"^(?P<lambda_nm>\d+)/W(?P<W_nominal_nm>\d+)/D(?P<D_nm>\d+)$")

NEGATIVE_BOUNDARY_FIELD_NAMES = frozenset(
    {
        "not_comsol_transport_distribution",
        "not_qch_weighted",
        "not_yield",
        "not_detection_probability",
        "not_true_w_eff",
        "not_measured_geometry",
        "not_optical_solver_output",
        "not_fabrication_release",
        "not_winner",
        "not_clogging_rate",
        "not_time_to_clog",
        "not_p3_solver_conclusion",
    }
)

FORBIDDEN_POSITIVE_FIELD_FRAGMENTS = (
    "q_ch_eta",
    "qch_eta",
    "q_ch_times_eta",
    "qch_times_eta",
    "q_ch_chi_selected_eta",
    "chi_selected_eta",
    "yield",
    "winner",
    "true_w_eff",
    "w_eff_nm",
    "delta_w_eff_nm",
    "measured_geometry",
    "optical_solver_output",
    "solver_output",
    "fabrication_release",
    "calibrated_detector_claim",
    "ev_detection_probability",
    "detection_probability",
    "throughput_detection",
    "scalar_joint_score",
    "joint_score",
    "p3_conclusion",
    "p3_solver_conclusion",
    "p3_solver_execution",
    "solver_execution",
    "event_rate",
    "wet_event_rate",
    "pass_probability",
    "wet_pass_probability",
    "clogging_probability",
    "clogging_rate",
    "time_to_clog",
    "recovery_yield",
    "production_ingestion_payload",
    "event_generation_payload",
    "count_prediction_update",
    "optical_geometry_update",
    "runtime_configuration",
)

SIDEWALL_ROADMAP_FORBIDDEN_EXACT_COLUMNS = frozenset(
    {
        "w_eff",
        "score",
        "route_score",
        "sidewall_score",
        "winner",
        "chi_selected",
        "jrc",
        "q_ch",
        "q_ch_eta",
        "q_ch_chi_eta",
        "yield",
        "detection_probability",
        "wet_pass_probability",
        "clogging_rate",
        "time_to_clog",
        "recovery",
    }
)

COMSOL_V4_CONTEXT_SCHEMA_VERSION = "nodi_comsol_v4_readonly_context_v1"
COMSOL_V4_ASSUMPTION_SET_ID = "EV_PBS_SAMPLE_SURFACE_ASSUMPTION_SET_V4_20260627"
COMSOL_V4_ASSUMPTION_SET_VERSION = "4.0.0"
COMSOL_V4_ASSUMPTION_SET_SHA256 = (
    "2bd97d7684a582343da05bc519f47d598baf29efa5e0157ea8330e9fae223d92"
)
COMSOL_V4_CLAIM_BOUNDARY = (
    "literature_derived_descriptor_closure_scenario_only_not_project_measurement_or_calibration"
)
COMSOL_V4_SCOPE_WET_SURFACE_CONTEXT = "wet_surface_context"
COMSOL_V4_SCOPE_OUT_OF_SCOPE_DRY_OPTICAL_SURROGATE = (
    "out_of_scope_dry_optical_surrogate"
)
COMSOL_V4_REVIEW_LOADER_MODE = "review_only_no_production_ingestion"
COMSOL_V4_AUTHORIZED_USE = "claim_boundary_and_future_joint_gate_context_only"
COMSOL_V4_UNBOUND_REQUIRED = "UNBOUND_REQUIRED"
COMSOL_V4_OUT_OF_SCOPE = "OUT_OF_SCOPE_DRY_OPTICAL_SURROGATE"

COMSOL_V4_REQUIRED_CONTEXT_FIELDS: tuple[str, ...] = (
    "schema_version",
    "v4_assumption_set_id",
    "v4_assumption_set_version",
    "v4_assumption_set_sha256",
    "v4_scope",
    "scenario_id",
    "sample_input_id",
    "surface_chemistry_state_id",
    "surface_state_contract",
    "wall_state_id",
    "roughness_state_id",
    "geometry_root",
    "hydraulic_anchor",
    "vesicle_model_level",
    "review_loader_mode",
    "authorized_use",
    "claim_boundary",
    "nodi_production_ingestion_allowed",
    "nodi_count_prediction_allowed",
    "nodi_optical_update_allowed",
    "nodi_runtime_configuration_allowed",
    "comsol_launch_authorized_now",
    "mph_load_authorized_now",
    "wet_pass_probability_allowed",
    "wet_event_rate_allowed",
    "clogging_probability_allowed",
    "yield_or_winner_allowed",
)

COMSOL_V4_FORBIDDEN_TRUE_FLAGS: tuple[str, ...] = (
    "nodi_production_ingestion_allowed",
    "nodi_count_prediction_allowed",
    "nodi_optical_update_allowed",
    "nodi_runtime_configuration_allowed",
    "comsol_launch_authorized_now",
    "mph_load_authorized_now",
    "wet_pass_probability_allowed",
    "wet_event_rate_allowed",
    "clogging_probability_allowed",
    "yield_or_winner_allowed",
)

COMSOL_V4_WET_IDENTITY_FIELDS: tuple[str, ...] = (
    "scenario_id",
    "sample_input_id",
    "surface_chemistry_state_id",
    "surface_state_contract",
    "wall_state_id",
    "roughness_state_id",
    "geometry_root",
    "hydraulic_anchor",
    "vesicle_model_level",
)


@dataclass(frozen=True)
class CanonicalContract:
    relpath: str
    sha256: str


CANONICAL_REPORT156_CONTRACTS: tuple[CanonicalContract, ...] = (
    CanonicalContract(
        "reports/156_NODI_NEXT_ARTIFACTS_COMSOL_READONLY_REVIEW_INTEGRATION_20260617.md",
        "ccd8d7c455f6db72311c44ed0919cefeaaec26ad98c5714cb861c5740174168a",
    ),
    CanonicalContract(
        "reports/NODI_POSITION_RESPONSE_SURFACE_SCHEMA_CONTRACT_20260617.csv",
        "eaba370120897370582451ae52ed6e61268061c777996e257d35941c8344335c",
    ),
    CanonicalContract(
        "reports/NODI_POSITION_RESPONSE_SURFACE_VALIDATOR_RULES_20260617.csv",
        "c06c8e3f6e979599ea5b3ebe153e5f2f6ed3741c00ed9479905a901ccaabd479",
    ),
    CanonicalContract(
        "reports/NODI_EFFECTIVE_APERTURE_SURROGATE_SCHEMA_CONTRACT_20260617.csv",
        "d2edaf3e6f7ce13d260f5f2c0baf0645ff7d6fed0c7efe985de81b66fe8b61f6",
    ),
    CanonicalContract(
        "reports/NODI_EFFECTIVE_APERTURE_SURROGATE_VALIDATOR_RULES_20260617.csv",
        "026e1f120c29ef817410273c522aa5b63cb7d35013f356db1162b51485a212ad",
    ),
)


def default_comsol_v4_readonly_context(
    *,
    v4_scope: str = COMSOL_V4_SCOPE_OUT_OF_SCOPE_DRY_OPTICAL_SURROGATE,
    source_artifact: str = (
        "comsol test/comsol_ev_pbs_bonded_cross_junction/roadmap/"
        "EV_PBS_SAMPLE_SURFACE_CANONICAL_CONTRACT_V4_20260627.json"
    ),
) -> dict[str, Any]:
    """Return a NODI-side read-only V4 context block for future joint gates."""
    if v4_scope == COMSOL_V4_SCOPE_WET_SURFACE_CONTEXT:
        identity_placeholder = COMSOL_V4_UNBOUND_REQUIRED
    else:
        identity_placeholder = COMSOL_V4_OUT_OF_SCOPE
    return {
        "schema_version": COMSOL_V4_CONTEXT_SCHEMA_VERSION,
        "v4_assumption_set_id": COMSOL_V4_ASSUMPTION_SET_ID,
        "v4_assumption_set_version": COMSOL_V4_ASSUMPTION_SET_VERSION,
        "v4_assumption_set_sha256": COMSOL_V4_ASSUMPTION_SET_SHA256,
        "v4_scope": v4_scope,
        "scenario_id": identity_placeholder,
        "sample_input_id": identity_placeholder,
        "surface_chemistry_state_id": identity_placeholder,
        "surface_state_contract": identity_placeholder,
        "wall_state_id": identity_placeholder,
        "roughness_state_id": identity_placeholder,
        "geometry_root": identity_placeholder,
        "hydraulic_anchor": identity_placeholder,
        "vesicle_model_level": identity_placeholder,
        "source_artifact": source_artifact,
        "source_row_key": "",
        "review_loader_mode": COMSOL_V4_REVIEW_LOADER_MODE,
        "authorized_use": COMSOL_V4_AUTHORIZED_USE,
        "claim_boundary": COMSOL_V4_CLAIM_BOUNDARY,
        "nodi_production_ingestion_allowed": False,
        "nodi_count_prediction_allowed": False,
        "nodi_optical_update_allowed": False,
        "nodi_runtime_configuration_allowed": False,
        "comsol_launch_authorized_now": False,
        "mph_load_authorized_now": False,
        "wet_pass_probability_allowed": False,
        "wet_event_rate_allowed": False,
        "clogging_probability_allowed": False,
        "yield_or_winner_allowed": False,
    }


def validate_comsol_v4_readonly_context(context: Mapping[str, Any]) -> list[str]:
    """Validate that COMSOL V4 context remains review-only on the NODI side."""
    issues: list[str] = []
    for field in COMSOL_V4_REQUIRED_CONTEXT_FIELDS:
        if field not in context:
            issues.append(f"COMSOL-V4: missing {field}")
    if context.get("schema_version") != COMSOL_V4_CONTEXT_SCHEMA_VERSION:
        issues.append("COMSOL-V4: schema_version drifted")
    if context.get("v4_assumption_set_id") != COMSOL_V4_ASSUMPTION_SET_ID:
        issues.append("COMSOL-V4: assumption set id drifted")
    if context.get("v4_assumption_set_version") != COMSOL_V4_ASSUMPTION_SET_VERSION:
        issues.append("COMSOL-V4: assumption set version drifted")
    if str(context.get("v4_assumption_set_sha256", "")).lower() != COMSOL_V4_ASSUMPTION_SET_SHA256:
        issues.append("COMSOL-V4: assumption set sha256 drifted")
    if context.get("claim_boundary") != COMSOL_V4_CLAIM_BOUNDARY:
        issues.append("COMSOL-V4: claim boundary drifted")
    if context.get("review_loader_mode") != COMSOL_V4_REVIEW_LOADER_MODE:
        issues.append("COMSOL-V4: review loader mode drifted")
    if context.get("authorized_use") != COMSOL_V4_AUTHORIZED_USE:
        issues.append("COMSOL-V4: authorized use drifted")

    scope = context.get("v4_scope")
    if scope not in {
        COMSOL_V4_SCOPE_WET_SURFACE_CONTEXT,
        COMSOL_V4_SCOPE_OUT_OF_SCOPE_DRY_OPTICAL_SURROGATE,
    }:
        issues.append("COMSOL-V4: invalid v4_scope")
    for field in COMSOL_V4_FORBIDDEN_TRUE_FLAGS:
        if context.get(field) is not False:
            issues.append(f"COMSOL-V4: {field} must remain false")
    for field in COMSOL_V4_WET_IDENTITY_FIELDS:
        value = context.get(field)
        if not value:
            issues.append(f"COMSOL-V4: {field} is blank")
        if scope == COMSOL_V4_SCOPE_WET_SURFACE_CONTEXT and value == COMSOL_V4_OUT_OF_SCOPE:
            issues.append(f"COMSOL-V4: {field} cannot be out-of-scope for wet context")
        if (
            scope == COMSOL_V4_SCOPE_OUT_OF_SCOPE_DRY_OPTICAL_SURROGATE
            and value != COMSOL_V4_OUT_OF_SCOPE
        ):
            issues.append(f"COMSOL-V4: {field} must stay out-of-scope for dry optical surrogate")
    return issues

PRS_REQUIRED_FIELDS: tuple[str, ...] = (
    "response_surface_artifact_version",
    "row_scope",
    "route_id_nodi",
    "lambda_nm",
    "W_nominal_nm",
    "D_nm",
    "NODI_view",
    "diameter_nm",
    "particle_kind",
    "distribution_type",
    "bin_id",
    "edge_norm_min",
    "edge_norm_max",
    "x_norm_min",
    "x_norm_max",
    "z_norm_min",
    "z_norm_max",
    "aggregate_source_type",
    "n_seeds",
    "n_events_total",
    "n_events_bin",
    "n_events_bin_per_seed_min",
    "sparse_bin_flag",
    "sparse_bin_policy",
    "bin_sample_status",
    "decision_use_allowed",
    "guardrail_status",
    "position_distribution_basis",
    "flow_condition_id",
    "flow_condition_version",
    "flow_condition_source_sha",
    "flow_condition_scope",
    "flow_condition_claim_boundary",
    "view_physical_independence_flag",
    "not_comsol_transport_distribution",
    "not_qch_weighted",
    "not_yield",
    "not_detection_probability",
    "claim_boundary",
    "source_artifact",
    "source_sha256",
)
SIDEWALL_V2_RUNTIME_PROPAGATION_GUARD_REQUIRED_FIELDS: tuple[str, ...] = (
    "reference_geometry_propagation_status",
    "geometry_not_propagated_to_reference_field",
    "not_optical_solver_output",
    "fluidic_clogging_risk_band_claim_level",
    "not_clogging_rate",
    "not_time_to_clog",
    "fluidic_geometry_model",
    "hydraulic_resistance_model",
    "hydraulic_resistance_claim_level",
    "fluidic_geometry_propagation_status",
    "geometry_not_propagated_to_fluidic_resistance",
    "fluidic_network_geometry_model",
    "fluidic_network_hydraulic_resistance_model",
    "fluidic_network_hydraulic_resistance_claim_level",
    "fluidic_network_geometry_propagation_status",
    "geometry_not_propagated_to_fluidic_network",
    "fluidic_network_not_qch_weighted",
    "electrokinetic_transport_geometry_model",
    "electrokinetic_wall_distance_model",
    "electrokinetic_geometry_propagation_status",
    "geometry_not_propagated_to_electrokinetic_transport",
    "surface_charge_transport_claim_level",
    "electrokinetic_diagnostic_gate_passed",
)
SIDEWALL_V2_TRUE_RUNTIME_GUARD_FIELDS: tuple[str, ...] = (
    "not_optical_solver_output",
    "not_clogging_rate",
    "not_time_to_clog",
    "fluidic_network_not_qch_weighted",
)
SIDEWALL_V2_BOOL_RUNTIME_GUARD_FIELDS: tuple[str, ...] = (
    "geometry_not_propagated_to_reference_field",
    "geometry_not_propagated_to_fluidic_resistance",
    "geometry_not_propagated_to_fluidic_network",
    "geometry_not_propagated_to_electrokinetic_transport",
    "electrokinetic_diagnostic_gate_passed",
)
SIDEWALL_V2_PACKAGE_D_PRECHECK_REQUIRED_FIELDS: tuple[str, ...] = (
    "sidewall_package_d_precheck_version",
    "target_artifact_family",
    "includes_trajectory_near_wall_metrics",
    "package_A_validation_status",
    "package_B_validation_status",
    "package_C_validation_status",
    "no_forbidden_claim_columns",
    "no_rectangular_cache_reuse",
    "no_comsol_context_grain_promotion",
    "no_edge4_to_edge20_direct_mapping",
    "no_D900_to_D1200_borrowing",
    "no_auto_220_300nm_admission",
    "package_d_precheck_status",
)
SIDEWALL_V2_SOURCE_GRAIN_REQUIRED_FIELDS: tuple[str, ...] = (
    "source_route_id_nodi",
    "source_D_nm",
)
SIDEWALL_V2_GEOMETRY_PROPAGATION_SCOPE_REQUIRED_FIELDS: tuple[str, ...] = (
    "geometry_propagation_scope",
)
SIDEWALL_V2_GEOMETRY_PROPAGATION_SCOPES = frozenset(
    {
        "particle_center_support_only_not_reference_fluidic_electrokinetic",
        "aperture_surrogate_only_not_true_runtime",
        "blocked_non_propagated_audit",
        "rectangle_native_or_non_sidewall_geometry",
    }
)
PRS_SIDEWALL_V2_PROPAGATED_SCOPE = (
    "particle_center_support_only_not_reference_fluidic_electrokinetic"
)
EAS_SIDEWALL_V2_PROPAGATED_SCOPE = "aperture_surrogate_only_not_true_runtime"
PRS_SIDEWALL_V2_SOURCE_BIN_REQUIRED_FIELDS: tuple[str, ...] = (
    "source_distribution_type",
    "source_bin_basis",
    "source_bin_id",
)
PRS_SIDEWALL_V2_TRAJECTORY_GUARD_REQUIRED_FIELDS: tuple[str, ...] = (
    "trajectory_boundary_model_version",
    "trajectory_boundary_claim_level",
    "wall_distance_model_version",
    "wall_distance_claim_level",
    "flow_profile_geometry_model",
    "flow_profile_geometry_claim_level",
    "geometry_not_propagated_to_flow_model",
    "geometry_not_propagated_to_near_wall_metrics",
    "geometry_not_propagated_to_trajectory_boundary",
    "sidewall_aware_runtime_status",
)
PRS_SIDEWALL_V2_MARKER_FIELDS = frozenset(
    {
        "channel_cross_section_model",
        "cross_section_geometry_version",
        "geometry_propagation_status",
        "sampler_geometry_model",
        "sampler_support_model",
        "particle_radius_nm",
        "tail_particle_auto_admitted",
        "steric_support_source",
        "coordinate_basis",
        "bin_accessible",
        "bin_particle_center_support_status",
        "neighbor_fill_used",
    }
)
PRS_SIDEWALL_V2_EXPLICIT_MARKER_FIELDS = frozenset(
    {
        "artifact_version",
        "geometry_runtime_binding_version",
        "geometry_propagation_scope",
        "tail_particle_auto_admitted",
        "steric_support_source",
        "coordinate_basis",
        "bin_particle_center_support_status",
        "trajectory_boundary_model_version",
        "wall_distance_model_version",
        "sidewall_aware_runtime_status",
    }
)
PRS_SIDEWALL_V2_REQUIRED_FIELDS: tuple[str, ...] = (
    "channel_cross_section_model",
    "cross_section_geometry_version",
    "geometry_runtime_binding_version",
    "geometry_propagation_status",
    "geometry_not_propagated_reasons",
    "sampler_geometry_model",
    "sampler_support_model",
    "particle_radius_nm",
    "coordinate_basis",
    "coordinate_conversion_formula_id",
    "x_nm",
    "u_nm",
    "z_nm",
    "x_left_nm",
    "x_right_nm",
    "x_center_nm",
    "local_width_nm",
    "local_half_width_nm",
    "x_local_norm",
    "u_norm",
    "d_top_nm",
    "d_bottom_nm",
    "d_side_left_nm",
    "d_side_right_nm",
    "d_nearest_wall_nm",
    "nearest_wall_id",
    "surface_gap_for_particle_nm",
    "bin_basis",
    "bin_accessible",
    "bin_accessible_area_fraction",
    "bin_particle_center_support_status",
    "blocked_reason",
    "sparse_reason",
    "neighbor_fill_used",
    "trajectory_boundary_model",
    "wall_distance_model",
    "flow_profile_model",
    "flow_control_mode",
    "reference_field_model",
    "reference_spatial_mode",
    *SIDEWALL_V2_GEOMETRY_PROPAGATION_SCOPE_REQUIRED_FIELDS,
    *SIDEWALL_V2_SOURCE_GRAIN_REQUIRED_FIELDS,
    *PRS_SIDEWALL_V2_SOURCE_BIN_REQUIRED_FIELDS,
    *PRS_SIDEWALL_V2_TRAJECTORY_GUARD_REQUIRED_FIELDS,
    *SIDEWALL_V2_PACKAGE_D_PRECHECK_REQUIRED_FIELDS,
    *SIDEWALL_V2_RUNTIME_PROPAGATION_GUARD_REQUIRED_FIELDS,
)
PRS_SIDEWALL_V2_BLOCKED_RESPONSE_VALUE_FIELDS: tuple[str, ...] = (
    "response_value",
    "response_proxy_value",
    "detector_response_proxy",
    "signal_response_proxy",
    "response_rate_bin",
)
PRS_SIDEWALL_V2_PARTICLE_SUPPORT_STATUS = frozenset({"open", "narrow", "blocked"})
PRS_SIDEWALL_V2_STERIC_SUPPORT_SOURCE = frozenset(
    {"exact_geometry_primitive", "not_available"}
)
PRS_SIDEWALL_V2_NEAREST_WALL_IDS = frozenset(
    {"top", "bottom", "left_side", "right_side"}
)
PRS_SIDEWALL_V2_GEOMETRY_STATUS_ALLOWED = frozenset(
    {
        "propagated",
        "blocked",
        "not_propagated",
        "blocked_trapezoid_geometry_not_propagated",
        "blocked_rectangular_geometry_leakage",
    }
)
SIDEWALL_V2_DESCRIPTOR_CONTEXT_REQUIRED_FIELDS: tuple[str, ...] = (
    "geometry_profile_source",
    "geometry_profile_sha256",
    "geometry_claim_level",
    "metrology_status",
    "sidewall_angle_convention",
    "sidewall_deg_comsol",
    "sidewall_taper_angle_deg_nodi",
    "angle_conversion_formula_id",
    "W_top_nm",
    "W_top_semantics",
    "W_bottom_unclipped_nm",
    "W_bottom_runtime_clipped_nm",
    "closure_status",
    "closure_policy",
    "runtime_guard_status",
)
SIDEWALL_V2_GEOMETRY_CLAIM_LEVEL_ALLOWED = frozenset(
    {
        "descriptor_only",
        "surrogate_sensitivity",
        "surrogate_sensitivity_only",
        "parameterized_geometry_descriptor_not_measured",
    }
)
SIDEWALL_V2_METROLOGY_STATUS_ALLOWED = frozenset(
    {"not_measured", "pending", "measured_unvalidated"}
)
SIDEWALL_V2_RUNTIME_GUARD_STATUS_ALLOWED = frozenset(
    {"none", "solver_guard", "validation_guard", "resource_guard"}
)
SIDEWALL_V2_OBSERVATION_SIGNATURE_VERSION = "sidewall_observation_signature_v1"
SIDEWALL_V2_OBSERVATION_CACHE_REQUIRED_FIELDS: tuple[str, ...] = (
    "observation_signature",
    "observation_signature_version",
    "cache_geometry_match_status",
)
SIDEWALL_V2_TRAPEZOID_SIGNATURE_REQUIRED_FRAGMENTS: tuple[str, ...] = (
    "cross_section_geometry_version=",
    "geometry_profile_sha256=",
    "geometry_propagation_scope=",
    "particle_radius_m=",
    "center_accessible_support_model=",
    "sampler_geometry_model=",
    "trajectory_boundary_model=",
    "wall_distance_model=",
    "flow_profile_geometry_model=",
    "geometry_propagation_status=",
    "reference_geometry_propagation_status=",
    "geometry_not_propagated_to_reference_field=",
    "not_optical_solver_output=True",
    "fluidic_clogging_risk_band_claim_level=",
    "not_clogging_rate=True",
    "not_time_to_clog=True",
    "fluidic_geometry_model=",
    "hydraulic_resistance_model=",
    "hydraulic_resistance_claim_level=",
    "fluidic_geometry_propagation_status=",
    "geometry_not_propagated_to_fluidic_resistance=",
    "fluidic_network_geometry_model=",
    "fluidic_network_hydraulic_resistance_model=",
    "fluidic_network_hydraulic_resistance_claim_level=",
    "fluidic_network_geometry_propagation_status=",
    "geometry_not_propagated_to_fluidic_network=",
    "fluidic_network_not_qch_weighted=True",
    "electrokinetic_transport_geometry_model=",
    "electrokinetic_wall_distance_model=",
    "electrokinetic_geometry_propagation_status=",
    "geometry_not_propagated_to_electrokinetic_transport=",
    "surface_charge_transport_claim_level=",
    "electrokinetic_diagnostic_gate_passed=",
)
PRS_SIDEWALL_V2_INITIAL_POSITION_SIGNATURE_REQUIRED_FRAGMENTS: tuple[str, ...] = (
    "initial_position_sampler_support_model=",
    "initial_position_particle_center_support_status=",
    "initial_position_steric_block_reason=",
)
SIDEWALL_V2_ACCEPTANCE_GUARD_REQUIRED_FIELDS: tuple[str, ...] = (
    "roadmap_status",
    "not_accepted_for_formula_use",
    "not_accepted_for_runtime_config",
    "not_accepted_for_production",
)
SIDEWALL_V2_ROADMAP_STATUS_ALLOWED = frozenset(
    {"roadmap_only", "surrogate_sensitivity_only", "descriptor_only", "context-only"}
)
PRS_SIDEWALL_V2_ARTIFACT_VERSION = "NODI_POSITION_RESPONSE_SIDEWALL_V2"
EAS_SIDEWALL_V2_ARTIFACT_VERSION = "NODI_EFFECTIVE_APERTURE_SIDEWALL_V2"
SIDEWALL_V2_ARTIFACT_METADATA_REQUIRED_FIELDS: tuple[str, ...] = (
    "artifact_id",
    "artifact_version",
    "artifact_created_utc",
)
SIDEWALL_V2_CACHE_GEOMETRY_MATCH_STATUS_ALLOWED = frozenset(
    {
        "matched_current_geometry",
        "no_cache_lookup_performed",
        "not_cacheable_audit",
        "blocked_old_rectangular_cache",
    }
)
SIDEWALL_PACKAGE_D_PRECHECK_VERSION = "sidewall_package_d_precheck_v1"
SIDEWALL_PACKAGE_D_PRECHECK_REQUIRED_FIELDS = SIDEWALL_V2_PACKAGE_D_PRECHECK_REQUIRED_FIELDS
SIDEWALL_PACKAGE_D_TARGET_ARTIFACT_FAMILY_ALLOWED = frozenset({"prs", "eas", "prs_eas"})
SIDEWALL_PACKAGE_D_PACKAGE_C_STATUS_ALLOWED = frozenset(
    {"pass", "not_applicable_for_this_artifact"}
)
SIDEWALL_PACKAGE_D_PRECHECK_STATUS_ALLOWED = frozenset({"pass", "blocked"})
SIDEWALL_PACKAGE_D_PRECHECK_TRUE_FIELDS: tuple[str, ...] = (
    "no_forbidden_claim_columns",
    "no_rectangular_cache_reuse",
    "no_comsol_context_grain_promotion",
    "no_edge4_to_edge20_direct_mapping",
    "no_D900_to_D1200_borrowing",
    "no_auto_220_300nm_admission",
)

EAS_REQUIRED_FIELDS: tuple[str, ...] = (
    "aperture_artifact_version",
    "route_id_nodi",
    "lambda_nm",
    "W_nominal_nm",
    "D_nm",
    "NODI_view",
    "weighting_basis",
    "aperture_surrogate_mode",
    "W_eff_surrogate_nm",
    "delta_W_eff_surrogate_nm",
    "source_geometry_descriptor_id",
    "source_geometry_descriptor_sha",
    "descriptor_evidence_class",
    "rank_source",
    "recommendation_eligible_rank_source",
    "guardrail_status",
    "eta_selected_proxy_under_surrogate",
    "eta_all_proxy_under_surrogate",
    "rank_under_surrogate",
    "rank_flip_flag",
    "candidate_family_flip_flag",
    "eta_selected_relative_change",
    "eta_all_relative_change",
    "guardrail_status_change_flag",
    "W_eff_mode_sensitivity_class",
    "solver_contract_trigger_flag",
    "solver_contract_trigger_reason",
    "not_true_W_eff",
    "not_measured_geometry",
    "not_optical_solver_output",
    "not_fabrication_release",
    "not_yield",
    "not_winner",
    "claim_boundary",
    "source_artifact",
    "source_sha256",
)
EAS_SIDEWALL_V2_MARKER_FIELDS = frozenset(
    {
        "channel_cross_section_model",
        "cross_section_geometry_version",
        "geometry_runtime_binding_version",
        "geometry_propagation_status",
        "eas_mode",
        "aperture_surrogate_basis",
        "aperture_surrogate_claim_level",
        "W_eff_optical_surrogate_nm",
        "W_eff_transport_surrogate_nm",
        "W_eff_accessible_surrogate_nm",
        "optical_solver_trigger_is_result",
    }
)
EAS_SIDEWALL_V2_EXPLICIT_MARKER_FIELDS = frozenset(
    {
        "artifact_version",
        "geometry_runtime_binding_version",
        "geometry_propagation_scope",
        "eas_mode",
        "aperture_surrogate_basis",
        "aperture_surrogate_claim_level",
        "W_eff_optical_surrogate_nm",
        "W_eff_transport_surrogate_nm",
        "W_eff_accessible_surrogate_nm",
        "optical_solver_trigger_is_result",
    }
)
EAS_SIDEWALL_V2_REQUIRED_FIELDS: tuple[str, ...] = (
    "eas_mode",
    "aperture_surrogate_basis",
    "aperture_surrogate_claim_level",
    "channel_cross_section_model",
    "cross_section_geometry_version",
    "geometry_runtime_binding_version",
    "geometry_propagation_status",
    "geometry_not_propagated_reasons",
    "optical_solver_triggered",
    "optical_solver_trigger_reason",
    "optical_solver_trigger_is_result",
    "optical_geometry_claim_level",
    "reference_field_model",
    "reference_spatial_mode",
    "reference_route",
    "illumination_mode",
    "detector_operator_id",
    "not_true_W_eff",
    "not_measured_geometry",
    "not_optical_solver_output",
    "not_qch_weighted",
    "not_detection_probability",
    *SIDEWALL_V2_GEOMETRY_PROPAGATION_SCOPE_REQUIRED_FIELDS,
    *SIDEWALL_V2_SOURCE_GRAIN_REQUIRED_FIELDS,
    *SIDEWALL_V2_PACKAGE_D_PRECHECK_REQUIRED_FIELDS,
    *SIDEWALL_V2_RUNTIME_PROPAGATION_GUARD_REQUIRED_FIELDS,
)
EAS_SIDEWALL_V2_SURROGATE_WIDTH_FIELDS: tuple[str, ...] = (
    "W_eff_optical_surrogate_nm",
    "W_eff_transport_surrogate_nm",
    "W_eff_accessible_surrogate_nm",
    "W_bottom_conservative_nm",
    "top_bottom_average_heuristic_nm",
    "center_accessible_aperture_surrogate_nm",
    "min_aperture_conservative_nm",
)
EAS_SIDEWALL_V2_OPTICAL_GEOMETRY_CLAIM_LEVEL_ALLOWED = frozenset(
    {"surrogate", "solver_required"}
)

PRS_APPROVED_ROUTE_MATRIX = frozenset(
    {
        (404, 500, 900),
        (404, 500, 1200),
        (660, 800, 900),
        (660, 800, 1200),
        (404, 600, 900),
        (660, 500, 1500),
    }
)
PRS_P2_DIAGNOSTIC_TRAP_ROUTE = (660, 500, 1500)
PRS_APPROVED_DIAMETERS_NM = frozenset(
    {40, 60, 100, 150, 220, 230, 240, 250, 260, 270, 280, 290, 300}
)
PRS_APPROVED_VIEWS = frozenset({"fixed_660_gold", "per_wavelength_gold"})
PRS_APPROVED_ROW_SCOPES = frozenset({"response_surface_bin", "qch_provenance_reference"})
PRS_APPROVED_DISTRIBUTIONS = frozenset({"edge_norm_1d", "xz_norm_2d"})
PRS_APPROVED_ROW_KINDS = frozenset({"base_bin", "special_aggregate"})
PRS_APPROVED_AGGREGATES = frozenset(
    {"near_center_0p0_0p5", "selected_annulus_0p5_0p8", "near_wall_0p8_1p0"}
)
PRS_APPROVED_AGGREGATE_SOURCE_TYPES = frozenset(
    {"edge_norm_primary", "xz_norm_diagnostic", "xz_norm_primary_if_adequate"}
)
PRS_APPROVED_SAMPLE_STATUS = frozenset({"adequate", "sparse", "empty"})
PRS_APPROVED_SPARSE_POLICIES = frozenset(
    {
        "sparse_individual_bins_context_only",
        "empty_bins_never_decision_use",
        "aggregate_level_explicit_only",
    }
)
PRS_APPROVED_GUARDRAIL_STATUS = frozenset(
    {
        "recommendation_eligible",
        "reference_too_weak",
        "out_of_particle_library_scope",
        "other_guardrail_state",
    }
)

EAS_APPROVED_ROUTE_MATRIX = frozenset(
    {
        (404, 500, 900),
        (404, 500, 1200),
        (660, 800, 900),
        (660, 800, 1200),
    }
)
EAS_APPROVED_MODES = frozenset(
    {
        "nominal_width",
        "W_bottom_conservative",
        "min_aperture_conservative",
        "top_bottom_average_heuristic",
        "COMSOL_descriptor_if_available",
    }
)
EAS_FIRST_PRODUCTION_MODES: tuple[str, ...] = (
    "nominal_width",
    "W_bottom_conservative",
    "min_aperture_conservative",
    "top_bottom_average_heuristic",
)
EAS_DESCRIPTOR_SELECTOR_POLICY: dict[str, str] = {
    "process_state": "nominal_smooth_geometry",
    "angle_convention": "sidewall_angle_from_substrate_plane_90deg_vertical",
    "sidewall_deg": "85.0",
    "route_geometry_id_comsol_version": GEOMETRY_DESCRIPTOR_VERSION,
    "claim_boundary": GEOMETRY_DESCRIPTOR_CLAIM_BOUNDARY,
}
EAS_APPROVED_DESCRIPTOR_EVIDENCE_CLASSES = frozenset(
    {"nominal/design-state", "surrogate/simulated geometry rule", "unavailable_v1"}
)
EAS_APPROVED_GUARDRAIL_STATUS = frozenset(
    {"recommendation_eligible", "reference_too_weak", "other_guardrail_state"}
)
EAS_APPROVED_SENSITIVITY_CLASSES = frozenset(
    {"stable", "watch", "decision_changing", "solver_required", "blocked_by_guardrail"}
)
EAS_APPROVED_SOLVER_TRIGGER_REASONS = frozenset(
    {
        "none",
        "candidate_family_flip",
        "W500_threshold_dependency",
        "selected_response_gt10pct",
        "guardrail_ambiguity",
        "report_dependency",
        "geometry_complexity",
        "nonpositive_surrogate_aperture",
    }
)

PRS_SOURCE_MINIMUM_GRAIN = (
    "route_id_nodi x diameter_nm x NODI_view x seed x distribution/bin"
)
PRS_SOURCE_AVAILABLE_CANDIDATE_STATUS = "source_available_preflight_only"
PRS_SOURCE_SHAPE_ONLY_CANDIDATE_STATUS = (
    "source_shape_available_not_production_eligible"
)
PRS_SOURCE_BLOCKED_CANDIDATE_STATUS = "blocked_missing_minimum_prs_source_grain"
PRS_SOURCE_MISSING_CANDIDATE_STATUS = "missing_candidate_file"
PRS_SOURCE_PRODUCTION_SCOPE = "production_candidate_from_real_nodi_event_export"
PRS_SOURCE_BOUNDED_SMOKE_SCOPE = "bounded_smoke_fixture_not_production"
PRS_SOURCE_APPROVED_SCOPES = frozenset(
    {PRS_SOURCE_PRODUCTION_SCOPE, PRS_SOURCE_BOUNDED_SMOKE_SCOPE}
)
PRS_BIN_SOURCE_CLAIM_BOUNDARY = (
    "prs_bin_conditioned_source_preflight_only_not_production_prs"
)
PRS_SOURCE_NUMERIC_SUFFICIENCY_POLICY = (
    "all_bin_source_rows_adequate_decision_use_allowed_true_min_100_events_per_bin"
)
PRS_SOURCE_PRODUCTION_ELIGIBILITY_POLICY = (
    "edge_norm_1d_primary_xz_norm_2d_diagnostic_no_auto_promotion"
)
PRS_SOURCE_NUMERIC_SUFFICIENT_CANDIDATE_STATUS = (
    "production_source_numeric_sufficient_preflight_only"
)
PRS_SOURCE_NUMERIC_INSUFFICIENT_CANDIDATE_STATUS = (
    "blocked_numeric_insufficient_for_production_prs"
)
PRS_SOURCE_NUMERIC_INVALID_CANDIDATE_STATUS = (
    "blocked_invalid_bin_conditioned_source"
)
PRS_SOURCE_NUMERIC_MISSING_CANDIDATE_STATUS = "missing_candidate_file"
PRS_SOURCE_PRODUCTION_ELIGIBLE_CANDIDATE_STATUS = (
    "edge_primary_source_eligible_xz_diagnostic_preflight_only"
)
PRS_SOURCE_PRODUCTION_INELIGIBLE_CANDIDATE_STATUS = (
    "blocked_edge_primary_source_production_eligibility"
)
PRS_SOURCE_PRODUCTION_INVALID_CANDIDATE_STATUS = (
    "blocked_invalid_bin_conditioned_source_for_production_eligibility"
)
PRS_SOURCE_PRODUCTION_MISSING_CANDIDATE_STATUS = "missing_candidate_file"
PRS_SOURCE_ACCUMULATION_SEEDS = (11, 22, 33)
PRS_SOURCE_ACCUMULATION_TARGET_EVENTS_PER_SEED = (
    PRS_MIN_EVENTS_PER_BIN_FOR_PRODUCTION * XZ_BASE_BIN_COUNT
)
PRS_SOURCE_ACCUMULATION_APPROVED_ROUTE_SCOPES = frozenset(
    {"all_approved", "p1_preferred_only"}
)
PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_DEFAULT_MAX_JOBS = 1
PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MAX_JOBS = 3
PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_DEFAULT_EVENTS_PER_JOB = 6
PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MAX_EVENTS_PER_JOB = 12
PRS_SOURCE_ACCUMULATION_CAMPAIGN_DEFAULT_JOBS_PER_SHARD = 12
PRS_SOURCE_ACCUMULATION_CAMPAIGN_MAX_JOBS_PER_SHARD = 24
PRS_SOURCE_ACCUMULATION_CAMPAIGN_DEFAULT_MAX_PARALLEL_SHARDS = 1

PRS_BIN_SOURCE_EVENT_REQUIRED_FIELDS: tuple[str, ...] = (
    "route_id_nodi",
    "lambda_nm",
    "W_nominal_nm",
    "D_nm",
    "diameter_nm",
    "NODI_view",
    "seed",
    "event_id",
    "x_norm",
    "z_norm",
    "response_detected",
)

PRS_BIN_SOURCE_REQUIRED_FIELDS: tuple[str, ...] = (
    "bin_source_artifact_version",
    "source_scope",
    "route_id_nodi",
    "lambda_nm",
    "W_nominal_nm",
    "D_nm",
    "diameter_nm",
    "NODI_view",
    "seed",
    "particle_kind",
    "distribution_type",
    "row_kind",
    "aggregate_id",
    "bin_id",
    "edge_norm_min",
    "edge_norm_max",
    "x_norm_min",
    "x_norm_max",
    "z_norm_min",
    "z_norm_max",
    "n_events_total_seed",
    "n_events_bin",
    "response_count_bin",
    "response_rate_bin",
    "bin_sample_status",
    "sparse_bin_flag",
    "decision_use_allowed",
    "source_event_rows",
    "preflight_only",
    "production_prs_generated",
    "not_qch_weighted",
    "not_yield",
    "not_detection_probability",
    "claim_boundary",
    "source_artifact",
    "source_sha256",
)

DESCRIPTOR_REQUIRED_FIELDS: tuple[str, ...] = (
    "route_geometry_id_comsol",
    "route_geometry_id_comsol_version",
    "process_state",
    "W_nominal_nm",
    "width_group_um",
    "D_nm",
    "W_top_um",
    "W_bottom_um",
    "bottom_width_nm",
    "D_inscribed_nm",
    "min_aperture_nm",
    "bottom_cd_bias_nm",
    "edge_lip_nm_per_side",
    "residue_thickness_nm",
    "roughness_rms_nm",
    "scallop_amplitude_nm",
    "rounded_corner_radius_nm",
    "claim_boundary",
)
DESCRIPTOR_V2_MARKER_FIELDS = frozenset(
    {
        "sidewall_angle_convention",
        "sidewall_deg_comsol",
        "sidewall_taper_angle_deg_nodi",
        "angle_conversion_formula_id",
        "W_top_nm",
        "W_top_semantics",
        "W_bottom_unclipped_nm",
        "W_bottom_runtime_clipped_nm",
        "closure_status",
        "closure_policy",
        "runtime_guard_status",
        "min_aperture_descriptor_nm",
    }
)
DESCRIPTOR_V2_REQUIRED_FIELDS: tuple[str, ...] = (
    "sidewall_angle_convention",
    "sidewall_deg_comsol",
    "sidewall_taper_angle_deg_nodi",
    "angle_conversion_formula_id",
    "W_top_nm",
    "W_top_semantics",
    "W_bottom_unclipped_nm",
    "W_bottom_runtime_clipped_nm",
    "closure_status",
    "closure_policy",
    "runtime_guard_status",
    "min_aperture_descriptor_nm",
)
DESCRIPTOR_V2_SIDEWALL_ANGLE_CONVENTIONS = frozenset(
    {
        "sidewall_angle_from_substrate_plane_90deg_vertical",
        "comsol_from_horizontal_90deg_vertical",
    }
)
DESCRIPTOR_V2_ANGLE_CONVERSION_FORMULA_ID = (
    "sidewall_from_horizontal_to_taper_from_vertical_v1"
)
DESCRIPTOR_V2_W_TOP_SEMANTICS = frozenset(
    {
        "runtime_top_aperture",
        "mask_width",
        "top_cd",
        "post_bias_top_cd",
        "comsol_descriptor",
    }
)
DESCRIPTOR_V2_CLOSURE_STATUS = frozenset({"open", "near_closed", "geometry_closed"})
DESCRIPTOR_V2_CLOSURE_POLICY = frozenset(
    {
        "preserve_unclipped_descriptor",
        "closure_clamped_runtime",
        "blocked_runtime",
    }
)
DESCRIPTOR_V2_PASSABILITY_EVIDENCE_FIELDS = frozenset(
    {
        "min_aperture_passability_evidence",
        "min_aperture_descriptor_passability_evidence",
        "ev_passability_evidence",
        "particle_passability_evidence",
        "particle_admission_status",
    }
)
DESCRIPTOR_V2_NON_MEASURED_PROFILE_SOURCES = frozenset(
    {
        "parameterized",
        "comsol_descriptor",
        "descriptor_only",
        "nominal",
        "design",
    }
)
DESCRIPTOR_UNAVAILABLE_FIELDS = frozenset(
    {
        "bottom_cd_bias_nm",
        "edge_lip_nm_per_side",
        "residue_thickness_nm",
        "roughness_rms_nm",
        "scallop_amplitude_nm",
        "rounded_corner_radius_nm",
    }
)


class ContractValidationError(ValueError):
    """Raised when an artifact violates the executable handoff contract."""

    def __init__(self, artifact: str, issues: Sequence[str]):
        self.artifact = artifact
        self.issues = tuple(issues)
        super().__init__(f"{artifact} validation failed with {len(self.issues)} issue(s)")


def validate_canonical_contract_files(project_root: Path) -> list[str]:
    """Validate that local Report 156 contract files still match pinned hashes."""
    issues: list[str] = []
    for contract in CANONICAL_REPORT156_CONTRACTS:
        path = project_root / contract.relpath
        if not path.exists():
            issues.append(f"CONTRACT-PIN: missing canonical contract {contract.relpath}")
            continue
        actual = sha256_file(path).lower()
        if actual != contract.sha256.lower():
            issues.append(
                "CONTRACT-PIN: sha256 mismatch for "
                f"{contract.relpath}: expected {contract.sha256}, got {actual}"
            )
    return issues


def validate_position_response_surface_csv(
    csv_path: Path,
    *,
    production_table: bool = True,
    allow_pending_source_hash: bool = False,
    require_complete_row_arithmetic: bool = False,
) -> list[str]:
    rows = read_csv_rows(csv_path)
    return validate_position_response_surface_rows(
        rows,
        production_table=production_table,
        allow_pending_source_hash=allow_pending_source_hash,
        require_complete_row_arithmetic=require_complete_row_arithmetic,
    )


def assert_valid_position_response_surface_csv(csv_path: Path, **kwargs: Any) -> None:
    issues = validate_position_response_surface_csv(csv_path, **kwargs)
    if issues:
        raise ContractValidationError(POSITION_RESPONSE_ARTIFACT, issues)


def validate_position_response_surface_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    production_table: bool = True,
    allow_pending_source_hash: bool = False,
    require_complete_row_arithmetic: bool = False,
) -> list[str]:
    issues: list[str] = []
    if not rows:
        return ["PRS-V01: no rows supplied"]

    for row_index, row in enumerate(rows, start=1):
        _require_fields(row, PRS_REQUIRED_FIELDS, "PRS-V01", row_index, issues)
        _reject_forbidden_positive_fields(
            row,
            allowed_negative_fields={"not_qch_weighted", "not_yield"},
            row_index=row_index,
            rule_id="PRS-V41",
            issues=issues,
        )

        if _value(row, "response_surface_artifact_version") != POSITION_RESPONSE_VERSION:
            _issue(issues, row_index, "PRS-V01", "invalid response_surface_artifact_version")

        route_tuple = _validate_route_fields(
            row,
            approved_routes=PRS_APPROVED_ROUTE_MATRIX,
            row_index=row_index,
            issues=issues,
            rule_id="PRS-V02",
        )
        if route_tuple == PRS_P2_DIAGNOSTIC_TRAP_ROUTE:
            if _value(row, "guardrail_status") == "recommendation_eligible":
                _issue(
                    issues,
                    row_index,
                    "PRS-V03",
                    "P2 diagnostic trap marked recommendation_eligible",
                )

        diameter = _int_field(row, "diameter_nm", row_index, "PRS-V04", issues)
        if diameter is not None and diameter not in PRS_APPROVED_DIAMETERS_NM:
            rule_id = "PRS-V05" if diameter == 500 else "PRS-V04"
            _issue(issues, row_index, rule_id, f"unapproved diameter_nm={diameter}")

        _validate_enum(row, "NODI_view", PRS_APPROVED_VIEWS, row_index, "PRS-V06", issues)
        _validate_bool_equals(
            row,
            "view_physical_independence_flag",
            False,
            row_index,
            "PRS-V07",
            issues,
        )
        _validate_enum(row, "distribution_type", PRS_APPROVED_DISTRIBUTIONS, row_index, "PRS-V08", issues)
        _validate_optional_enum(row, "row_kind", PRS_APPROVED_ROW_KINDS, row_index, "PRS-V08", issues)
        _validate_position_bin(row, row_index, issues)
        _validate_position_response_sidewall_v2_fields(row, row_index, issues)

        _validate_int_equals(row, "n_seeds", 3, row_index, "PRS-V14", issues)
        _validate_nonnegative_int(row, "n_events_total", row_index, "PRS-V15", issues)
        n_events_bin = _validate_nonnegative_int(row, "n_events_bin", row_index, "PRS-V15", issues)
        _validate_nonnegative_int(row, "n_events_bin_per_seed_min", row_index, "PRS-V15", issues)
        _validate_sample_status(row, n_events_bin, row_index, issues)

        _validate_enum(
            row,
            "aggregate_source_type",
            PRS_APPROVED_AGGREGATE_SOURCE_TYPES,
            row_index,
            "PRS-V25",
            issues,
        )
        _validate_xz_promotion_policy(row, row_index, issues)
        _validate_enum(
            row,
            "sparse_bin_policy",
            PRS_APPROVED_SPARSE_POLICIES,
            row_index,
            "PRS-V21",
            issues,
        )
        _validate_enum(
            row,
            "guardrail_status",
            PRS_APPROVED_GUARDRAIL_STATUS,
            row_index,
            "PRS-V23",
            issues,
        )

        _validate_position_flow_semantics(row, row_index, production_table, issues)
        _validate_source_hash(
            row,
            field="source_sha256",
            row_index=row_index,
            rule_id="PRS-V40",
            issues=issues,
            allow_pending=allow_pending_source_hash,
        )
        if not _value(row, "source_artifact"):
            _issue(issues, row_index, "PRS-V40", "source_artifact is blank")

    _validate_position_response_grain(rows, issues)
    if require_complete_row_arithmetic:
        _validate_position_response_row_arithmetic(rows, issues)
    return issues


def validate_effective_aperture_surrogate_csv(
    csv_path: Path,
    *,
    allow_pending_source_hash: bool = False,
) -> list[str]:
    rows = read_csv_rows(csv_path)
    return validate_effective_aperture_surrogate_rows(
        rows,
        allow_pending_source_hash=allow_pending_source_hash,
    )


def assert_valid_effective_aperture_surrogate_csv(csv_path: Path, **kwargs: Any) -> None:
    issues = validate_effective_aperture_surrogate_csv(csv_path, **kwargs)
    if issues:
        raise ContractValidationError(APERTURE_SURROGATE_ARTIFACT, issues)


def validate_sidewall_package_d_precheck_rows(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not rows:
        return ["SIDEWALL-D-PRECHECK-V01: no rows supplied"]

    for row_index, row in enumerate(rows, start=1):
        _require_fields(
            row,
            SIDEWALL_PACKAGE_D_PRECHECK_REQUIRED_FIELDS,
            "SIDEWALL-D-PRECHECK-V01",
            row_index,
            issues,
        )
        _reject_forbidden_positive_fields(
            row,
            allowed_negative_fields=set(SIDEWALL_PACKAGE_D_PRECHECK_TRUE_FIELDS),
            row_index=row_index,
            rule_id="SIDEWALL-D-PRECHECK-V06",
            issues=issues,
        )
        _validate_constant(
            row,
            "sidewall_package_d_precheck_version",
            SIDEWALL_PACKAGE_D_PRECHECK_VERSION,
            row_index,
            "SIDEWALL-D-PRECHECK-V01",
            issues,
        )
        _validate_enum(
            row,
            "target_artifact_family",
            SIDEWALL_PACKAGE_D_TARGET_ARTIFACT_FAMILY_ALLOWED,
            row_index,
            "SIDEWALL-D-PRECHECK-V01",
            issues,
        )
        includes_near_wall = _bool_field(
            row,
            "includes_trajectory_near_wall_metrics",
            row_index,
            "SIDEWALL-D-PRECHECK-V01",
            issues,
        )

        package_a_ok = _value(row, "package_A_validation_status") == "pass"
        package_b_ok = _value(row, "package_B_validation_status") == "pass"
        if not package_a_ok:
            _issue(
                issues,
                row_index,
                "SIDEWALL-D-PRECHECK-V02",
                "Package D requires package_A_validation_status=pass",
            )
        if not package_b_ok:
            _issue(
                issues,
                row_index,
                "SIDEWALL-D-PRECHECK-V02",
                "Package D requires package_B_validation_status=pass",
            )

        package_c_status = _value(row, "package_C_validation_status")
        if package_c_status not in SIDEWALL_PACKAGE_D_PACKAGE_C_STATUS_ALLOWED:
            _issue(
                issues,
                row_index,
                "SIDEWALL-D-PRECHECK-V03",
                f"invalid package_C_validation_status={package_c_status}",
            )
        if includes_near_wall is True and package_c_status != "pass":
            _issue(
                issues,
                row_index,
                "SIDEWALL-D-PRECHECK-V03",
                "trajectory/near-wall Package D artifacts require package_C_validation_status=pass",
            )

        true_fields_ok = True
        for field in SIDEWALL_PACKAGE_D_PRECHECK_TRUE_FIELDS:
            _validate_bool_equals(
                row,
                field,
                True,
                row_index,
                "SIDEWALL-D-PRECHECK-V04",
                issues,
            )
            true_fields_ok = true_fields_ok and _value(row, field).lower() in {"true", "1", "yes"}

        precheck_status = _value(row, "package_d_precheck_status")
        if precheck_status not in SIDEWALL_PACKAGE_D_PRECHECK_STATUS_ALLOWED:
            _issue(
                issues,
                row_index,
                "SIDEWALL-D-PRECHECK-V05",
                f"invalid package_d_precheck_status={precheck_status}",
            )
        package_c_ok = package_c_status == "pass" or includes_near_wall is False
        if precheck_status == "pass" and not (package_a_ok and package_b_ok and package_c_ok and true_fields_ok):
            _issue(
                issues,
                row_index,
                "SIDEWALL-D-PRECHECK-V05",
                "package_d_precheck_status=pass with unmet Package D prerequisite",
            )
        if precheck_status == "blocked" and package_a_ok and package_b_ok and package_c_ok and true_fields_ok:
            _issue(
                issues,
                row_index,
                "SIDEWALL-D-PRECHECK-V05",
                "package_d_precheck_status=blocked despite all Package D prerequisites passing",
            )

    return issues


def validate_effective_aperture_surrogate_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    allow_pending_source_hash: bool = False,
) -> list[str]:
    issues: list[str] = []
    if not rows:
        return ["EAS-V01: no rows supplied"]

    for row_index, row in enumerate(rows, start=1):
        _require_fields(row, EAS_REQUIRED_FIELDS, "EAS-V01", row_index, issues)
        if "W_eff_nm" in row or "delta_W_eff_nm" in row:
            _issue(issues, row_index, "EAS-V03", "old W_eff_nm field name is forbidden")
        _reject_forbidden_positive_fields(
            row,
            allowed_negative_fields={"not_true_W_eff", "not_yield", "not_winner"},
            row_index=row_index,
            rule_id="EAS-V26",
            issues=issues,
        )

        if _value(row, "aperture_artifact_version") != APERTURE_SURROGATE_VERSION:
            _issue(issues, row_index, "EAS-V01", "invalid aperture_artifact_version")

        _validate_route_fields(
            row,
            approved_routes=EAS_APPROVED_ROUTE_MATRIX,
            row_index=row_index,
            issues=issues,
            rule_id="EAS-V13",
        )
        _validate_enum(row, "NODI_view", PRS_APPROVED_VIEWS, row_index, "EAS-V01", issues)
        _validate_constant(row, "weighting_basis", EAS_WEIGHTING_BASIS, row_index, "EAS-V13", issues)
        _validate_enum(row, "aperture_surrogate_mode", EAS_APPROVED_MODES, row_index, "EAS-V02", issues)
        _validate_constant(
            row,
            "source_geometry_descriptor_sha",
            GEOMETRY_DESCRIPTOR_SHA256,
            row_index,
            "EAS-V12",
            issues,
            case_sensitive=False,
        )
        _validate_enum(
            row,
            "descriptor_evidence_class",
            EAS_APPROVED_DESCRIPTOR_EVIDENCE_CLASSES,
            row_index,
            "EAS-V06",
            issues,
        )
        _validate_constant(row, "rank_source", EAS_RANK_SOURCE, row_index, "EAS-V13", issues)
        _validate_constant(
            row,
            "recommendation_eligible_rank_source",
            EAS_RECOMMENDATION_RANK_SOURCE,
            row_index,
            "EAS-V14",
            issues,
        )
        _validate_no_stage1_rank_source(row, row_index, issues)
        _validate_enum(
            row,
            "guardrail_status",
            EAS_APPROVED_GUARDRAIL_STATUS,
            row_index,
            "EAS-V16",
            issues,
        )
        _validate_effective_aperture_numeric_fields(row, row_index, issues)
        _validate_aperture_flags_and_boundary(row, row_index, issues)
        _validate_effective_aperture_sidewall_v2_fields(row, row_index, issues)
        _validate_enum(
            row,
            "W_eff_mode_sensitivity_class",
            EAS_APPROVED_SENSITIVITY_CLASSES,
            row_index,
            "EAS-V03",
            issues,
        )
        _validate_solver_trigger_contract(row, row_index, issues)
        _validate_source_hash(
            row,
            field="source_sha256",
            row_index=row_index,
            rule_id="EAS-V27",
            issues=issues,
            allow_pending=allow_pending_source_hash,
        )
        if not _value(row, "source_artifact"):
            _issue(issues, row_index, "EAS-V27", "source_artifact is blank")

    _validate_effective_aperture_grain(rows, issues)
    return issues


def validate_geometry_descriptor_csv(csv_path: Path) -> list[str]:
    return validate_geometry_descriptor_rows(read_csv_rows(csv_path))


def validate_geometry_descriptor_rows(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    issues: list[str] = []
    if not rows:
        return ["EAS-V06: no descriptor rows supplied"]
    grain_counter: Counter[tuple[str, str]] = Counter()
    for row_index, row in enumerate(rows, start=1):
        _require_fields(row, DESCRIPTOR_REQUIRED_FIELDS, "EAS-V06", row_index, issues)
        _reject_forbidden_positive_fields(
            row,
            allowed_negative_fields=set(),
            row_index=row_index,
            rule_id="EAS-V06",
            issues=issues,
        )
        grain_counter[(_value(row, "route_geometry_id_comsol"), _value(row, "process_state"))] += 1
        _validate_constant(
            row,
            "route_geometry_id_comsol_version",
            GEOMETRY_DESCRIPTOR_VERSION,
            row_index,
            "EAS-V06",
            issues,
        )
        _validate_constant(
            row,
            "claim_boundary",
            GEOMETRY_DESCRIPTOR_CLAIM_BOUNDARY,
            row_index,
            "EAS-V06",
            issues,
        )
        _validate_geometry_descriptor_v2_sidewall_fields(row, row_index, issues)
        width_group_um = _float_field(row, "width_group_um", row_index, "EAS-V07", issues)
        w_top_um = _float_field(row, "W_top_um", row_index, "EAS-V07", issues)
        if width_group_um is not None and w_top_um is not None:
            _validate_close(w_top_um, width_group_um, row_index, "EAS-V07", "W_top_um", issues)

        bottom_width_nm = _float_field(row, "bottom_width_nm", row_index, "EAS-V08", issues)
        w_bottom_um = _float_field(row, "W_bottom_um", row_index, "EAS-V08", issues)
        if bottom_width_nm is not None and w_bottom_um is not None:
            _validate_close(
                w_bottom_um,
                bottom_width_nm / 1000.0,
                row_index,
                "EAS-V08",
                "W_bottom_um",
                issues,
            )

        d_inscribed_nm = _float_field(row, "D_inscribed_nm", row_index, "EAS-V09", issues)
        min_aperture_nm = _float_field(row, "min_aperture_nm", row_index, "EAS-V09", issues)
        if (
            bottom_width_nm is not None
            and d_inscribed_nm is not None
            and min_aperture_nm is not None
        ):
            expected = min(bottom_width_nm, d_inscribed_nm)
            _validate_close(
                min_aperture_nm,
                expected,
                row_index,
                "EAS-V09",
                "min_aperture_nm",
                issues,
            )
            if expected < 0 and min_aperture_nm >= 0:
                _issue(issues, row_index, "EAS-V10", "negative min_aperture_nm was clipped")

        for field in DESCRIPTOR_UNAVAILABLE_FIELDS:
            if _value(row, field) not in {"", "unavailable_v1"}:
                _issue(issues, row_index, "EAS-V11", f"{field} is not blank/unavailable_v1")

    for grain, count in grain_counter.items():
        if count > 1:
            issues.append(f"EAS-V06: duplicate descriptor grain {grain}")
    return issues


def _validate_geometry_descriptor_v2_sidewall_fields(
    row: Mapping[str, Any],
    row_index: int,
    issues: list[str],
) -> None:
    if not any(field in row for field in DESCRIPTOR_V2_MARKER_FIELDS):
        return

    _require_fields(row, DESCRIPTOR_V2_REQUIRED_FIELDS, "DESC-V2", row_index, issues)
    _validate_enum(
        row,
        "sidewall_angle_convention",
        DESCRIPTOR_V2_SIDEWALL_ANGLE_CONVENTIONS,
        row_index,
        "DESC-V2",
        issues,
    )
    _validate_constant(
        row,
        "angle_conversion_formula_id",
        DESCRIPTOR_V2_ANGLE_CONVERSION_FORMULA_ID,
        row_index,
        "DESC-V2",
        issues,
    )
    _validate_enum(
        row,
        "W_top_semantics",
        DESCRIPTOR_V2_W_TOP_SEMANTICS,
        row_index,
        "DESC-V2",
        issues,
    )
    _validate_enum(
        row,
        "closure_status",
        DESCRIPTOR_V2_CLOSURE_STATUS,
        row_index,
        "DESC-V2",
        issues,
    )
    _validate_enum(
        row,
        "closure_policy",
        DESCRIPTOR_V2_CLOSURE_POLICY,
        row_index,
        "DESC-V2",
        issues,
    )

    sidewall_deg = _float_field(row, "sidewall_deg_comsol", row_index, "DESC-V2", issues)
    taper_deg = _float_field(
        row,
        "sidewall_taper_angle_deg_nodi",
        row_index,
        "DESC-V2",
        issues,
    )
    if sidewall_deg is not None and taper_deg is not None:
        if not math.isclose(sidewall_deg + taper_deg, 90.0, abs_tol=1.0e-6):
            _issue(
                issues,
                row_index,
                "DESC-V2",
                "sidewall_deg_comsol and sidewall_taper_angle_deg_nodi are not complementary",
            )

    w_top_nm = _float_field(row, "W_top_nm", row_index, "DESC-V2", issues)
    _validate_descriptor_v2_runtime_top_binding(
        row,
        row_index,
        w_top_nm,
        issues,
    )
    depth_nm = _float_field(row, "D_nm", row_index, "DESC-V2", issues)
    w_bottom_unclipped_nm = _float_field(
        row,
        "W_bottom_unclipped_nm",
        row_index,
        "DESC-V2",
        issues,
    )
    w_bottom_runtime_clipped_nm = _float_field(
        row,
        "W_bottom_runtime_clipped_nm",
        row_index,
        "DESC-V2",
        issues,
    )
    min_aperture_descriptor_nm = _float_field(
        row,
        "min_aperture_descriptor_nm",
        row_index,
        "DESC-V2",
        issues,
    )
    d_inscribed_nm = _float_field(row, "D_inscribed_nm", row_index, "DESC-V2", issues)
    if (
        sidewall_deg is not None
        and w_top_nm is not None
        and depth_nm is not None
        and w_bottom_unclipped_nm is not None
    ):
        tan_theta = math.tan(math.radians(sidewall_deg))
        if abs(tan_theta) <= 1.0e-12:
            _issue(issues, row_index, "DESC-V2", "sidewall_deg_comsol has zero tangent")
        else:
            expected_bottom = w_top_nm - 2.0 * depth_nm / tan_theta
            if not math.isclose(
                w_bottom_unclipped_nm,
                expected_bottom,
                rel_tol=1.0e-9,
                abs_tol=5.0e-2,
            ):
                _issue(
                    issues,
                    row_index,
                    "DESC-V2",
                    "W_bottom_unclipped_nm does not match sidewall formula",
                )

    if w_bottom_runtime_clipped_nm is not None and w_bottom_runtime_clipped_nm < 0.0:
        _issue(issues, row_index, "DESC-V2", "W_bottom_runtime_clipped_nm is negative")
    if (
        w_bottom_unclipped_nm is not None
        and w_bottom_runtime_clipped_nm is not None
    ):
        expected_runtime_bottom = max(w_bottom_unclipped_nm, 0.0)
        if not math.isclose(
            w_bottom_runtime_clipped_nm,
            expected_runtime_bottom,
            rel_tol=1.0e-9,
            abs_tol=5.0e-2,
        ):
            _issue(
                issues,
                row_index,
                "DESC-V2",
                "W_bottom_runtime_clipped_nm does not match clipped bottom width",
            )
    if w_bottom_unclipped_nm is not None and w_bottom_unclipped_nm <= 0.0:
        if _value(row, "closure_status") == "open":
            _issue(
                issues,
                row_index,
                "DESC-V2",
                "nonpositive W_bottom_unclipped_nm marked closure_status=open",
            )
        if not _value(row, "closure_policy"):
            _issue(issues, row_index, "DESC-V2", "nonpositive bottom width lacks closure_policy")
    if (
        w_bottom_unclipped_nm is not None
        and d_inscribed_nm is not None
        and min_aperture_descriptor_nm is not None
    ):
        expected_min_aperture = min(w_bottom_unclipped_nm, d_inscribed_nm)
        if not math.isclose(
            min_aperture_descriptor_nm,
            expected_min_aperture,
            rel_tol=1.0e-9,
            abs_tol=5.0e-2,
        ):
            _issue(
                issues,
                row_index,
                "DESC-V2",
                "min_aperture_descriptor_nm does not match unclipped descriptor aperture",
            )
        if expected_min_aperture < 0.0 and min_aperture_descriptor_nm >= 0.0:
            _issue(
                issues,
                row_index,
                "DESC-V2",
                "negative min_aperture_descriptor_nm was clipped",
            )
    for field in DESCRIPTOR_V2_PASSABILITY_EVIDENCE_FIELDS:
        if field in row and _value(row, field):
            _issue(
                issues,
                row_index,
                "DESC-V2",
                f"{field} cannot be used with descriptor min aperture",
            )
    _validate_descriptor_v2_measured_geometry_claim(row, row_index, issues)


def _validate_descriptor_v2_runtime_top_binding(
    row: Mapping[str, Any],
    row_index: int,
    w_top_nm: float | None,
    issues: list[str],
    rule_id: str = "DESC-V2",
) -> None:
    if _value(row, "W_top_semantics") != "runtime_top_aperture":
        return
    runtime_top_aperture_nm = _float_field(
        row,
        "runtime_top_aperture_nm",
        row_index,
        rule_id,
        issues,
    )
    if w_top_nm is not None and runtime_top_aperture_nm is not None:
        _validate_close(
            runtime_top_aperture_nm,
            w_top_nm,
            row_index,
            rule_id,
            "runtime_top_aperture_nm",
            issues,
        )


def _validate_descriptor_v2_measured_geometry_claim(
    row: Mapping[str, Any],
    row_index: int,
    issues: list[str],
) -> None:
    geometry_claim_level = _value(row, "geometry_claim_level").lower()
    metrology_status = _value(row, "metrology_status").lower()
    not_measured_geometry: bool | None = None
    if "not_measured_geometry" in row:
        not_measured_geometry = _bool_field(
            row,
            "not_measured_geometry",
            row_index,
            "DESC-V2",
            issues,
        )

    measured_claim_requested = (
        geometry_claim_level == "measured_geometry"
        or metrology_status == "validated"
        or not_measured_geometry is False
    )
    if not measured_claim_requested:
        return

    if geometry_claim_level != "measured_geometry":
        _issue(
            issues,
            row_index,
            "DESC-V2",
            "validated/measured profile metadata lacks geometry_claim_level=measured_geometry",
        )
    if metrology_status != "validated":
        _issue(
            issues,
            row_index,
            "DESC-V2",
            "measured geometry claim lacks metrology_status=validated",
        )
    if not_measured_geometry is True:
        _issue(
            issues,
            row_index,
            "DESC-V2",
            "measured geometry claim carries not_measured_geometry=true",
        )

    geometry_profile_source = _value(row, "geometry_profile_source")
    geometry_profile_sha256 = _value(row, "geometry_profile_sha256")
    measured_profile_path = _value(row, "measured_profile_path")
    if not geometry_profile_source:
        _issue(issues, row_index, "DESC-V2", "measured geometry lacks geometry_profile_source")
    elif geometry_profile_source.lower() in DESCRIPTOR_V2_NON_MEASURED_PROFILE_SOURCES:
        _issue(
            issues,
            row_index,
            "DESC-V2",
            "measured geometry uses non-measured geometry_profile_source",
        )
    if not geometry_profile_sha256:
        _issue(issues, row_index, "DESC-V2", "measured geometry lacks geometry_profile_sha256")
    elif not SHA256_RE.fullmatch(geometry_profile_sha256):
        _issue(
            issues,
            row_index,
            "DESC-V2",
            "measured geometry_profile_sha256 is not a sha256",
        )
    if not measured_profile_path:
        _issue(issues, row_index, "DESC-V2", "measured geometry lacks measured_profile_path")


def position_response_smoke_manifest_rows() -> list[dict[str, str]]:
    """Return the Report 156 design-only PRS smoke manifest rows."""
    return [
        {
            "smoke_id": "PRS-SMOKE-DEFAULT",
            "artifact": POSITION_RESPONSE_ARTIFACT,
            "smoke_role": "default_schema_and_row_arithmetic_smoke",
            "route_scope": "404/W500/D900;660/W800/D900;404/W600/D900",
            "diameter_scope": "40;150;220;270;300",
            "view_scope": "fixed_660_gold;per_wavelength_gold",
            "distribution_scope": (
                "edge_norm_1d 20 bins plus xz_norm_2d 21x21 plus "
                "3 special aggregates each"
            ),
            "seed_scope": "11;22;33",
            "event_budget": "small smoke budget preserving sparse-bin logic",
            "row_arithmetic": "3 routes * 5 diameters * 2 views * 467 = 14010 planned rows",
            "execution_status": "DESIGN_ONLY_NOT_EXECUTED",
            "allowed_output_status": "smoke_only_not_production",
            "claim_boundary": PRS_FLOW_CONDITION_CLAIM_BOUNDARY,
        },
        {
            "smoke_id": "PRS-SMOKE-CORE",
            "artifact": POSITION_RESPONSE_ARTIFACT,
            "smoke_role": "core_route_schema_smoke",
            "route_scope": "404/W500/D900;660/W800/D900",
            "diameter_scope": "40;150;220;270;300",
            "view_scope": "fixed_660_gold;per_wavelength_gold",
            "distribution_scope": (
                "edge_norm_1d 20 bins plus xz_norm_2d 21x21 plus "
                "3 special aggregates each"
            ),
            "seed_scope": "11;22;33",
            "event_budget": "small smoke budget preserving sparse-bin logic",
            "row_arithmetic": "2 routes * 5 diameters * 2 views * 467 = 9340 planned rows",
            "execution_status": "DESIGN_ONLY_NOT_EXECUTED",
            "allowed_output_status": "smoke_only_not_production",
            "claim_boundary": PRS_FLOW_CONDITION_CLAIM_BOUNDARY,
        },
        {
            "smoke_id": "PRS-SMOKE-ONEVIEW-FALLBACK",
            "artifact": POSITION_RESPONSE_ARTIFACT,
            "smoke_role": "cost_fallback_schema_smoke_only",
            "route_scope": "404/W500/D900;660/W800/D900",
            "diameter_scope": "40;150;220;270;300",
            "view_scope": "fixed_660_gold only unless separately revised",
            "distribution_scope": (
                "edge_norm_1d 20 bins plus xz_norm_2d 21x21 plus "
                "3 special aggregates each"
            ),
            "seed_scope": "11;22;33",
            "event_budget": "small smoke budget preserving sparse-bin logic",
            "row_arithmetic": "2 routes * 5 diameters * 1 view * 467 = 4670 planned rows",
            "execution_status": "DESIGN_ONLY_NOT_EXECUTED",
            "allowed_output_status": "one_view_schema_smoke_only_not_production",
            "claim_boundary": PRS_FLOW_CONDITION_CLAIM_BOUNDARY,
        },
        {
            "smoke_id": "PRS-SMOKE-500NM-NEGATIVE",
            "artifact": POSITION_RESPONSE_ARTIFACT,
            "smoke_role": "validator_negative_fixture_design",
            "route_scope": "404/W500/D900",
            "diameter_scope": "500",
            "view_scope": "fixed_660_gold",
            "distribution_scope": "not applicable",
            "seed_scope": "not applicable",
            "event_budget": "no simulation",
            "row_arithmetic": "gap row or validator fixture only; eta blank",
            "execution_status": "DESIGN_ONLY_NOT_EXECUTED",
            "allowed_output_status": "no_eta_no_interpolation_no_zero_proxy",
            "claim_boundary": "out_of_particle_library_scope_RC13_only",
        },
        {
            "smoke_id": "PRS-SMOKE-QCH-NEGATIVE",
            "artifact": POSITION_RESPONSE_ARTIFACT,
            "smoke_role": "validator_negative_fixture_design",
            "route_scope": "660/W800/D900",
            "diameter_scope": "220",
            "view_scope": "fixed_660_gold",
            "distribution_scope": "not applicable",
            "seed_scope": "not applicable",
            "event_budget": "no simulation",
            "row_arithmetic": f"reject {QCH_FLOW_CONDITION_ID} on NODI-only row",
            "execution_status": "DESIGN_ONLY_NOT_EXECUTED",
            "allowed_output_status": "validator_fixture_only_not_production",
            "claim_boundary": "q_ch_descriptive_only_not_qch_eta",
        },
    ]


def effective_aperture_smoke_manifest_rows() -> list[dict[str, str]]:
    """Return the Report 156 design-only EAS smoke manifest rows."""
    return [
        {
            "smoke_id": "EAS-SMOKE-DEFAULT",
            "artifact": APERTURE_SURROGATE_ARTIFACT,
            "smoke_role": "default_schema_guardrail_descriptor_smoke",
            "route_scope": "404/W500/D900;404/W500/D1200;660/W800/D900;660/W800/D1200",
            "view_scope": "fixed_660_gold;per_wavelength_gold",
            "mode_scope": "nominal_width;W_bottom_conservative;min_aperture_conservative",
            "rank_source_scope": "fullgrid recommendation-eligible rank only",
            "descriptor_scope": f"COMSOL_GEOMETRY_DESCRIPTOR_V1 SHA {GEOMETRY_DESCRIPTOR_SHA256}",
            "row_arithmetic": (
                "4 routes * 2 views * 3 modes = 24 planned rows; "
                "no weighting splits authorized"
            ),
            "execution_status": "DESIGN_ONLY_NOT_EXECUTED",
            "allowed_output_status": "smoke_only_not_final_route_decision",
            "claim_boundary": EAS_CLAIM_BOUNDARY,
        },
        {
            "smoke_id": "EAS-SMOKE-RANK-GUARDRAIL",
            "artifact": APERTURE_SURROGATE_ARTIFACT,
            "smoke_role": "rank_source_and_guardrail_validator_design",
            "route_scope": "404/W500/D900;660/W800/D900",
            "view_scope": "fixed_660_gold;per_wavelength_gold",
            "mode_scope": "nominal_width;W_bottom_conservative;min_aperture_conservative",
            "rank_source_scope": (
                f"{EAS_RANK_SOURCE} plus "
                "exports/nodi_comsol_handoff_v1/NODI_REFERENCE_GUARDRAIL_TABLE.csv"
            ),
            "descriptor_scope": "COMSOL roadmap/JPI source-of-truth",
            "row_arithmetic": "validator fixture rows only",
            "execution_status": "DESIGN_ONLY_NOT_EXECUTED",
            "allowed_output_status": "validator_fixture_only_not_production",
            "claim_boundary": "rank_source_fullgrid_recommendation_eligible_only",
        },
        {
            "smoke_id": "EAS-SMOKE-NEGATIVE-APERTURE",
            "artifact": APERTURE_SURROGATE_ARTIFACT,
            "smoke_role": "negative_min_aperture_preservation_design",
            "route_scope": "descriptor rows with negative min_aperture if present",
            "view_scope": "not applicable",
            "mode_scope": "min_aperture_conservative",
            "rank_source_scope": "not applicable",
            "descriptor_scope": "negative min_aperture values preserved not clipped",
            "row_arithmetic": "validator fixture rows only",
            "execution_status": "DESIGN_ONLY_NOT_EXECUTED",
            "allowed_output_status": "no_clipping_no_low_proxy",
            "claim_boundary": GEOMETRY_DESCRIPTOR_CLAIM_BOUNDARY,
        },
        {
            "smoke_id": "EAS-SMOKE-P3-FLAG",
            "artifact": APERTURE_SURROGATE_ARTIFACT,
            "smoke_role": "P3_trigger_flag_contract_design",
            "route_scope": "404/W500/D900;660/W800/D900",
            "view_scope": "fixed_660_gold;per_wavelength_gold",
            "mode_scope": "W_bottom_conservative;min_aperture_conservative",
            "rank_source_scope": "fullgrid recommendation-eligible rank only",
            "descriptor_scope": "COMSOL descriptor only",
            "row_arithmetic": "validator fixture rows only",
            "execution_status": "DESIGN_ONLY_NOT_EXECUTED",
            "allowed_output_status": "solver_contract_trigger_only_not_solver_execution",
            "claim_boundary": "P3_contract_trigger_not_solver_conclusion",
        },
    ]


def write_design_only_smoke_manifest_bundle(output_dir: Path) -> dict[str, Any]:
    """Write Report 156 design-only smoke manifests without executing smoke."""
    output_dir.mkdir(parents=True, exist_ok=True)
    prs_rows = position_response_smoke_manifest_rows()
    eas_rows = effective_aperture_smoke_manifest_rows()
    prs_path = output_dir / PRS_SMOKE_MANIFEST_FILENAME
    eas_path = output_dir / EAS_SMOKE_MANIFEST_FILENAME
    index_path = output_dir / NEXT_ARTIFACTS_SMOKE_INDEX_FILENAME
    metadata_path = output_dir / NEXT_ARTIFACTS_SMOKE_METADATA_FILENAME

    write_csv_rows(prs_path, prs_rows)
    write_csv_rows(eas_path, eas_rows)
    index_rows = [
        {
            "artifact": POSITION_RESPONSE_ARTIFACT,
            "filename": PRS_SMOKE_MANIFEST_FILENAME,
            "row_count": len(prs_rows),
            "execution_status": "DESIGN_ONLY_NOT_EXECUTED",
            "artifact_status": "smoke_manifest_design_only_not_production",
            "claim_boundary": PRS_FLOW_CONDITION_CLAIM_BOUNDARY,
        },
        {
            "artifact": APERTURE_SURROGATE_ARTIFACT,
            "filename": EAS_SMOKE_MANIFEST_FILENAME,
            "row_count": len(eas_rows),
            "execution_status": "DESIGN_ONLY_NOT_EXECUTED",
            "artifact_status": "smoke_manifest_design_only_not_final_route_decision",
            "claim_boundary": EAS_CLAIM_BOUNDARY,
        },
    ]
    write_csv_rows(index_path, index_rows)

    file_entries = [
        {
            "artifact": POSITION_RESPONSE_ARTIFACT,
            "path": str(prs_path),
            "sha256": sha256_file(prs_path),
            "rows": len(prs_rows),
        },
        {
            "artifact": APERTURE_SURROGATE_ARTIFACT,
            "path": str(eas_path),
            "sha256": sha256_file(eas_path),
            "rows": len(eas_rows),
        },
        {
            "artifact": "NODI_NEXT_ARTIFACTS_SMOKE_MANIFEST_INDEX",
            "path": str(index_path),
            "sha256": sha256_file(index_path),
            "rows": len(index_rows),
        },
    ]
    metadata: dict[str, Any] = {
        "status": "design_only_smoke_manifest_bundle_written",
        "source_contract": "Report 156 patched CSV contracts",
        "no_runner_implementation": True,
        "no_runner_execution": True,
        "no_smoke_execution": True,
        "no_nodi_run": True,
        "no_comsol_run": True,
        "no_production_artifact": True,
        "no_joint_route_class_regeneration": True,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_winner": True,
        "not_true_W_eff": True,
        "not_measured_geometry": True,
        "not_optical_solver_output": True,
        "not_fabrication_release": True,
        "not_P3_solver_conclusion": True,
        "files": file_entries,
        "canonical_contracts": [
            {"path": contract.relpath, "sha256": contract.sha256}
            for contract in CANONICAL_REPORT156_CONTRACTS
        ],
    }
    write_json_atomic(metadata_path, metadata, sort_keys=True)
    metadata["files"].append(
        {
            "artifact": "NODI_NEXT_ARTIFACTS_SMOKE_MANIFEST_METADATA",
            "path": str(metadata_path),
            "sha256": sha256_file(metadata_path),
            "rows": "",
        }
    )
    return metadata


def validate_design_only_smoke_manifest_bundle(bundle_dir: Path) -> list[str]:
    """Validate the design-only smoke manifest bundle without executing it."""
    issues: list[str] = []
    expected_files = (
        PRS_SMOKE_MANIFEST_FILENAME,
        EAS_SMOKE_MANIFEST_FILENAME,
        NEXT_ARTIFACTS_SMOKE_INDEX_FILENAME,
        NEXT_ARTIFACTS_SMOKE_METADATA_FILENAME,
    )
    for filename in expected_files:
        if not (bundle_dir / filename).exists():
            issues.append(f"PREFLIGHT-SMOKE: missing {filename}")
    if issues:
        return issues

    prs_rows = read_csv_rows(bundle_dir / PRS_SMOKE_MANIFEST_FILENAME)
    eas_rows = read_csv_rows(bundle_dir / EAS_SMOKE_MANIFEST_FILENAME)
    index_rows = read_csv_rows(bundle_dir / NEXT_ARTIFACTS_SMOKE_INDEX_FILENAME)
    _validate_exact_smoke_rows(
        prs_rows,
        position_response_smoke_manifest_rows(),
        "PREFLIGHT-PRS-SMOKE",
        issues,
    )
    _validate_exact_smoke_rows(
        eas_rows,
        effective_aperture_smoke_manifest_rows(),
        "PREFLIGHT-EAS-SMOKE",
        issues,
    )
    for label, rows in (
        ("PREFLIGHT-PRS-SMOKE", prs_rows),
        ("PREFLIGHT-EAS-SMOKE", eas_rows),
        ("PREFLIGHT-SMOKE-INDEX", index_rows),
    ):
        statuses = {_value(row, "execution_status") for row in rows}
        if statuses != {"DESIGN_ONLY_NOT_EXECUTED"}:
            issues.append(f"{label}: execution_status drift {sorted(statuses)}")
    metadata_path = bundle_dir / NEXT_ARTIFACTS_SMOKE_METADATA_FILENAME
    try:
        import json

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except Exception as exc:
        issues.append(f"PREFLIGHT-SMOKE-METADATA: unreadable metadata JSON: {exc}")
        return issues
    for field in (
        "no_runner_implementation",
        "no_runner_execution",
        "no_smoke_execution",
        "no_nodi_run",
        "no_comsol_run",
        "no_production_artifact",
        "no_joint_route_class_regeneration",
        "not_qch_weighted",
        "not_yield",
        "not_winner",
        "not_true_W_eff",
        "not_measured_geometry",
        "not_optical_solver_output",
        "not_fabrication_release",
        "not_P3_solver_conclusion",
    ):
        if metadata.get(field) is not True:
            issues.append(f"PREFLIGHT-SMOKE-METADATA: {field} is not true")
    return issues


def write_no_execution_runner_preflight_report(
    *,
    project_root: Path,
    smoke_manifest_dir: Path,
    output_dir: Path,
    geometry_descriptor_path: Path | None = None,
) -> dict[str, Any]:
    """Write a no-execution preflight report before any future implementation."""
    issues: list[str] = []
    issues.extend(validate_canonical_contract_files(project_root))
    issues.extend(validate_design_only_smoke_manifest_bundle(smoke_manifest_dir))
    descriptor_status = "not_checked"
    descriptor_sha256 = ""
    if geometry_descriptor_path is not None:
        descriptor_status = "checked"
        issues.extend(validate_geometry_descriptor_csv(geometry_descriptor_path))
        if geometry_descriptor_path.exists():
            descriptor_sha256 = sha256_file(geometry_descriptor_path)
    status = (
        "PASS_NO_EXECUTION_IMPLEMENTATION_PREFLIGHT"
        if not issues
        else "BLOCKED_BEFORE_IMPLEMENTATION"
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    issue_rows = [
        {"issue_index": index, "issue": issue}
        for index, issue in enumerate(issues, start=1)
    ] or [{"issue_index": "", "issue": "none"}]
    issue_path = output_dir / NEXT_ARTIFACTS_RUNNER_PREFLIGHT_ISSUES_FILENAME
    report_path = output_dir / NEXT_ARTIFACTS_RUNNER_PREFLIGHT_REPORT_FILENAME
    write_csv_rows(issue_path, issue_rows)
    report: dict[str, Any] = {
        "status": status,
        "issues": issues,
        "smoke_manifest_dir": str(smoke_manifest_dir),
        "geometry_descriptor_path": "" if geometry_descriptor_path is None else str(geometry_descriptor_path),
        "geometry_descriptor_status": descriptor_status,
        "geometry_descriptor_sha256": descriptor_sha256,
        "issue_csv": str(issue_path),
        "no_runner_implementation": True,
        "no_runner_execution": True,
        "no_smoke_execution": True,
        "no_nodi_run": True,
        "no_comsol_run": True,
        "no_production_artifact": True,
        "no_joint_route_class_regeneration": True,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_winner": True,
        "not_true_W_eff": True,
        "not_measured_geometry": True,
        "not_optical_solver_output": True,
        "not_fabrication_release": True,
        "not_P3_solver_conclusion": True,
        "canonical_contracts": [
            {"path": contract.relpath, "sha256": contract.sha256}
            for contract in CANONICAL_REPORT156_CONTRACTS
        ],
    }
    write_json_atomic(report_path, report, sort_keys=True)
    report["report_path"] = str(report_path)
    report["report_sha256"] = sha256_file(report_path)
    report["issue_csv_sha256"] = sha256_file(issue_path)
    return report


def position_response_plan_blueprint_rows() -> list[dict[str, str]]:
    """Expand PRS smoke scopes into compact plan-only route/view/diameter rows."""
    rows: list[dict[str, str]] = []
    for smoke in position_response_smoke_manifest_rows():
        routes = _split_scope_values(smoke["route_scope"])
        diameters = _split_scope_values(smoke["diameter_scope"])
        views = _split_scope_values(smoke["view_scope"])
        if smoke["smoke_role"] == "validator_negative_fixture_design":
            rows.append(
                {
                    "blueprint_artifact_version": "NODI_NEXT_ARTIFACTS_PLAN_BLUEPRINT_V1",
                    "blueprint_artifact": POSITION_RESPONSE_ARTIFACT,
                    "source_smoke_id": smoke["smoke_id"],
                    "plan_scope": "validator_negative_fixture_plan_only",
                    "route_id_nodi": smoke["route_scope"],
                    "diameter_nm": smoke["diameter_scope"],
                    "NODI_view": smoke["view_scope"],
                    "distribution_contract": smoke["distribution_scope"],
                    "planned_route_diameter_view_rows": "0",
                    "planned_execution_status": PLAN_ONLY_EXECUTION_STATUS,
                    "allowed_output_status": smoke["allowed_output_status"],
                    "claim_boundary": smoke["claim_boundary"],
                    "no_runner_execution": "true",
                    "no_smoke_execution": "true",
                    "no_production_artifact": "true",
                }
            )
            continue
        for route in routes:
            for diameter in diameters:
                for view in views:
                    rows.append(
                        {
                            "blueprint_artifact_version": "NODI_NEXT_ARTIFACTS_PLAN_BLUEPRINT_V1",
                            "blueprint_artifact": POSITION_RESPONSE_ARTIFACT,
                            "source_smoke_id": smoke["smoke_id"],
                            "plan_scope": "route_diameter_view_plan_only",
                            "route_id_nodi": route,
                            "diameter_nm": diameter,
                            "NODI_view": view,
                            "distribution_contract": smoke["distribution_scope"],
                            "planned_route_diameter_view_rows": str(ROWS_PER_ROUTE_DIAMETER_VIEW),
                            "planned_execution_status": PLAN_ONLY_EXECUTION_STATUS,
                            "allowed_output_status": smoke["allowed_output_status"],
                            "claim_boundary": smoke["claim_boundary"],
                            "no_runner_execution": "true",
                            "no_smoke_execution": "true",
                            "no_production_artifact": "true",
                        }
                    )
    return rows


def effective_aperture_plan_blueprint_rows() -> list[dict[str, str]]:
    """Expand EAS smoke scopes into compact plan-only route/view/mode rows."""
    rows: list[dict[str, str]] = []
    for smoke in effective_aperture_smoke_manifest_rows():
        routes = _split_scope_values(smoke["route_scope"])
        views = _split_scope_values(smoke["view_scope"])
        modes = _split_scope_values(smoke["mode_scope"])
        if not routes or not views or not modes:
            rows.append(
                {
                    "blueprint_artifact_version": "NODI_NEXT_ARTIFACTS_PLAN_BLUEPRINT_V1",
                    "blueprint_artifact": APERTURE_SURROGATE_ARTIFACT,
                    "source_smoke_id": smoke["smoke_id"],
                    "plan_scope": "validator_fixture_plan_only",
                    "route_id_nodi": smoke["route_scope"],
                    "NODI_view": smoke["view_scope"],
                    "aperture_surrogate_mode": smoke["mode_scope"],
                    "rank_source_scope": smoke["rank_source_scope"],
                    "descriptor_scope": smoke["descriptor_scope"],
                    "planned_route_view_mode_rows": "0",
                    "planned_execution_status": PLAN_ONLY_EXECUTION_STATUS,
                    "allowed_output_status": smoke["allowed_output_status"],
                    "claim_boundary": smoke["claim_boundary"],
                    "no_runner_execution": "true",
                    "no_smoke_execution": "true",
                    "no_production_artifact": "true",
                    "not_true_W_eff": "true",
                    "not_optical_solver_output": "true",
                }
            )
            continue
        for route in routes:
            for view in views:
                for mode in modes:
                    rows.append(
                        {
                            "blueprint_artifact_version": "NODI_NEXT_ARTIFACTS_PLAN_BLUEPRINT_V1",
                            "blueprint_artifact": APERTURE_SURROGATE_ARTIFACT,
                            "source_smoke_id": smoke["smoke_id"],
                            "plan_scope": "route_view_mode_plan_only",
                            "route_id_nodi": route,
                            "NODI_view": view,
                            "aperture_surrogate_mode": mode,
                            "rank_source_scope": smoke["rank_source_scope"],
                            "descriptor_scope": smoke["descriptor_scope"],
                            "planned_route_view_mode_rows": "1",
                            "planned_execution_status": PLAN_ONLY_EXECUTION_STATUS,
                            "allowed_output_status": smoke["allowed_output_status"],
                            "claim_boundary": smoke["claim_boundary"],
                            "no_runner_execution": "true",
                            "no_smoke_execution": "true",
                            "no_production_artifact": "true",
                            "not_true_W_eff": "true",
                            "not_optical_solver_output": "true",
                        }
                    )
    return rows


def write_plan_only_blueprint_bundle(
    *,
    smoke_manifest_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Write compact plan-only blueprints from a validated smoke manifest bundle."""
    issues = validate_design_only_smoke_manifest_bundle(smoke_manifest_dir)
    if issues:
        raise ContractValidationError("NODI_NEXT_ARTIFACTS_PLAN_BLUEPRINT", issues)
    output_dir.mkdir(parents=True, exist_ok=True)
    prs_rows = position_response_plan_blueprint_rows()
    eas_rows = effective_aperture_plan_blueprint_rows()
    prs_path = output_dir / PRS_PLAN_BLUEPRINT_FILENAME
    eas_path = output_dir / EAS_PLAN_BLUEPRINT_FILENAME
    index_path = output_dir / NEXT_ARTIFACTS_PLAN_BLUEPRINT_INDEX_FILENAME
    metadata_path = output_dir / NEXT_ARTIFACTS_PLAN_BLUEPRINT_METADATA_FILENAME
    write_csv_rows(prs_path, prs_rows)
    write_csv_rows(eas_path, eas_rows)
    index_rows = [
        {
            "artifact": POSITION_RESPONSE_ARTIFACT,
            "filename": PRS_PLAN_BLUEPRINT_FILENAME,
            "row_count": len(prs_rows),
            "planned_execution_status": PLAN_ONLY_EXECUTION_STATUS,
            "artifact_status": "plan_only_blueprint_not_smoke_not_production",
            "claim_boundary": PRS_FLOW_CONDITION_CLAIM_BOUNDARY,
        },
        {
            "artifact": APERTURE_SURROGATE_ARTIFACT,
            "filename": EAS_PLAN_BLUEPRINT_FILENAME,
            "row_count": len(eas_rows),
            "planned_execution_status": PLAN_ONLY_EXECUTION_STATUS,
            "artifact_status": "plan_only_blueprint_not_final_route_decision",
            "claim_boundary": EAS_CLAIM_BOUNDARY,
        },
    ]
    write_csv_rows(index_path, index_rows)
    metadata: dict[str, Any] = {
        "status": "plan_only_blueprint_bundle_written",
        "smoke_manifest_dir": str(smoke_manifest_dir),
        "no_runner_implementation": True,
        "no_runner_execution": True,
        "no_smoke_execution": True,
        "no_nodi_run": True,
        "no_comsol_run": True,
        "no_production_artifact": True,
        "no_joint_route_class_regeneration": True,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_winner": True,
        "not_true_W_eff": True,
        "not_measured_geometry": True,
        "not_optical_solver_output": True,
        "not_fabrication_release": True,
        "not_P3_solver_conclusion": True,
        "files": [
            {
                "artifact": POSITION_RESPONSE_ARTIFACT,
                "path": str(prs_path),
                "sha256": sha256_file(prs_path),
                "rows": len(prs_rows),
            },
            {
                "artifact": APERTURE_SURROGATE_ARTIFACT,
                "path": str(eas_path),
                "sha256": sha256_file(eas_path),
                "rows": len(eas_rows),
            },
            {
                "artifact": "NODI_NEXT_ARTIFACTS_PLAN_BLUEPRINT_INDEX",
                "path": str(index_path),
                "sha256": sha256_file(index_path),
                "rows": len(index_rows),
            },
        ],
    }
    write_json_atomic(metadata_path, metadata, sort_keys=True)
    metadata["files"].append(
        {
            "artifact": "NODI_NEXT_ARTIFACTS_PLAN_BLUEPRINT_METADATA",
            "path": str(metadata_path),
            "sha256": sha256_file(metadata_path),
            "rows": "",
        }
    )
    return metadata


def validate_plan_only_blueprint_bundle(bundle_dir: Path) -> list[str]:
    """Validate a compact plan-only blueprint bundle without executing it."""
    issues: list[str] = []
    expected_files = (
        PRS_PLAN_BLUEPRINT_FILENAME,
        EAS_PLAN_BLUEPRINT_FILENAME,
        NEXT_ARTIFACTS_PLAN_BLUEPRINT_INDEX_FILENAME,
        NEXT_ARTIFACTS_PLAN_BLUEPRINT_METADATA_FILENAME,
    )
    for filename in expected_files:
        if not (bundle_dir / filename).exists():
            issues.append(f"GATE-BLUEPRINT: missing {filename}")
    if issues:
        return issues

    prs_rows = read_csv_rows(bundle_dir / PRS_PLAN_BLUEPRINT_FILENAME)
    eas_rows = read_csv_rows(bundle_dir / EAS_PLAN_BLUEPRINT_FILENAME)
    index_rows = read_csv_rows(bundle_dir / NEXT_ARTIFACTS_PLAN_BLUEPRINT_INDEX_FILENAME)
    _validate_exact_smoke_rows(
        prs_rows,
        position_response_plan_blueprint_rows(),
        "GATE-PRS-BLUEPRINT",
        issues,
    )
    _validate_exact_smoke_rows(
        eas_rows,
        effective_aperture_plan_blueprint_rows(),
        "GATE-EAS-BLUEPRINT",
        issues,
    )
    if len(index_rows) != 2:
        issues.append(f"GATE-BLUEPRINT-INDEX: expected 2 rows, got {len(index_rows)}")
    for label, rows in (
        ("GATE-PRS-BLUEPRINT", prs_rows),
        ("GATE-EAS-BLUEPRINT", eas_rows),
        ("GATE-BLUEPRINT-INDEX", index_rows),
    ):
        statuses = {_value(row, "planned_execution_status") for row in rows}
        if statuses != {PLAN_ONLY_EXECUTION_STATUS}:
            issues.append(f"{label}: planned_execution_status drift {sorted(statuses)}")
    try:
        metadata = json.loads(
            (bundle_dir / NEXT_ARTIFACTS_PLAN_BLUEPRINT_METADATA_FILENAME).read_text(
                encoding="utf-8"
            )
        )
    except Exception as exc:
        issues.append(f"GATE-BLUEPRINT-METADATA: unreadable metadata JSON: {exc}")
        return issues
    if metadata.get("status") != "plan_only_blueprint_bundle_written":
        issues.append("GATE-BLUEPRINT-METADATA: unexpected status")
    for field in _NO_EXECUTION_TRUE_FIELDS:
        if metadata.get(field) is not True:
            issues.append(f"GATE-BLUEPRINT-METADATA: {field} is not true")
    return issues


def build_next_artifacts_runner_authorization_gate_record(
    *,
    project_root: Path,
    smoke_manifest_dir: Path,
    plan_blueprint_dir: Path,
    preflight_report_path: Path | None = None,
) -> dict[str, Any]:
    """Build the future authorization gate record without opening the gate."""
    issues: list[str] = []
    issues.extend(validate_canonical_contract_files(project_root))
    issues.extend(validate_design_only_smoke_manifest_bundle(smoke_manifest_dir))
    issues.extend(validate_plan_only_blueprint_bundle(plan_blueprint_dir))

    preflight_status = "not_checked"
    preflight_sha256 = ""
    if preflight_report_path is not None:
        try:
            preflight = json.loads(preflight_report_path.read_text(encoding="utf-8"))
        except Exception as exc:
            issues.append(f"GATE-PREFLIGHT: unreadable preflight report: {exc}")
        else:
            preflight_status = str(preflight.get("status", "missing_status"))
            if preflight_status != "PASS_NO_EXECUTION_IMPLEMENTATION_PREFLIGHT":
                issues.append(f"GATE-PREFLIGHT: unexpected status {preflight_status}")
            for field in _NO_EXECUTION_TRUE_FIELDS:
                if preflight.get(field) is not True:
                    issues.append(f"GATE-PREFLIGHT: {field} is not true")
            preflight_sha256 = sha256_file(preflight_report_path)

    status = AUTHORIZATION_GATE_PASS_STATUS if not issues else AUTHORIZATION_GATE_BLOCKED_STATUS
    record: dict[str, Any] = {
        "schema_version": "nodi_comsol_next_artifacts_runner_authorization_gate_v1",
        "record_role": "future_authorization_gate_no_runner_no_smoke_no_production",
        "status": status,
        "issues": issues,
        "authorization_gate_decision": "not_authorized_pending_explicit_future_request",
        "runner_implementation_authorized": False,
        "runner_execution_authorized": False,
        "bounded_smoke_execution_authorized": False,
        "production_generation_authorized": False,
        "nodi_run_authorized": False,
        "comsol_run_authorized": False,
        "joint_route_class_regeneration_authorized": False,
        "qch_eta_authorized": False,
        "yield_authorized": False,
        "winner_authorized": False,
        "true_w_eff_claim_authorized": False,
        "measured_geometry_claim_authorized": False,
        "optical_solver_output_claim_authorized": False,
        "fabrication_release_authorized": False,
        "p3_solver_conclusion_authorized": False,
        "contract_sidecar_writing_authorized": True,
        "validator_contract_current": not validate_canonical_contract_files(project_root),
        "smoke_manifest_design_only_current": not validate_design_only_smoke_manifest_bundle(
            smoke_manifest_dir
        ),
        "plan_only_blueprint_current": not validate_plan_only_blueprint_bundle(
            plan_blueprint_dir
        ),
        "explicit_future_authorization_required": True,
        "required_future_authorization_phrases": {
            "runner_implementation": RUNNER_IMPLEMENTATION_AUTHORIZATION_PHRASE,
            "bounded_smoke_execution": BOUNDED_SMOKE_AUTHORIZATION_PHRASE,
            "production_generation": PRODUCTION_GENERATION_AUTHORIZATION_PHRASE,
        },
        "authorization_phrase_already_received": False,
        "no_runner_implementation": True,
        "no_runner_execution": True,
        "no_smoke_execution": True,
        "no_nodi_run": True,
        "no_comsol_run": True,
        "no_production_artifact": True,
        "no_joint_route_class_regeneration": True,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_winner": True,
        "not_true_W_eff": True,
        "not_measured_geometry": True,
        "not_optical_solver_output": True,
        "not_fabrication_release": True,
        "not_P3_solver_conclusion": True,
        "claim_boundary": (
            "future_authorization_gate_only_no_runner_no_smoke_no_production"
        ),
        "source_contract": "Report 156 patched CSV contracts plus Reports 159-161",
        "smoke_manifest_dir": str(smoke_manifest_dir),
        "plan_blueprint_dir": str(plan_blueprint_dir),
        "preflight_report_path": "" if preflight_report_path is None else str(preflight_report_path),
        "preflight_status": preflight_status,
        "preflight_sha256": preflight_sha256,
        "source_files": _authorization_gate_source_files(
            smoke_manifest_dir=smoke_manifest_dir,
            plan_blueprint_dir=plan_blueprint_dir,
            preflight_report_path=preflight_report_path,
        ),
    }
    gate_issues = validate_next_artifacts_runner_authorization_gate_record(record)
    if gate_issues:
        record["status"] = AUTHORIZATION_GATE_BLOCKED_STATUS
        record["issues"] = [*issues, *gate_issues]
    return record


def validate_next_artifacts_runner_authorization_gate_record(
    record: Mapping[str, Any],
) -> list[str]:
    """Validate that the future gate record still denies execution."""
    issues: list[str] = []
    if (
        record.get("schema_version")
        != "nodi_comsol_next_artifacts_runner_authorization_gate_v1"
    ):
        issues.append("GATE-RECORD: unexpected schema_version")
    if (
        record.get("record_role")
        != "future_authorization_gate_no_runner_no_smoke_no_production"
    ):
        issues.append("GATE-RECORD: record_role drifted")
    if record.get("status") not in {
        AUTHORIZATION_GATE_PASS_STATUS,
        AUTHORIZATION_GATE_BLOCKED_STATUS,
    }:
        issues.append("GATE-RECORD: invalid status")
    if record.get("authorization_gate_decision") != "not_authorized_pending_explicit_future_request":
        issues.append("GATE-RECORD: authorization_gate_decision drifted")
    phrases = record.get("required_future_authorization_phrases")
    if not isinstance(phrases, Mapping):
        issues.append("GATE-RECORD: required_future_authorization_phrases missing")
    else:
        expected = {
            "runner_implementation": RUNNER_IMPLEMENTATION_AUTHORIZATION_PHRASE,
            "bounded_smoke_execution": BOUNDED_SMOKE_AUTHORIZATION_PHRASE,
            "production_generation": PRODUCTION_GENERATION_AUTHORIZATION_PHRASE,
        }
        if dict(phrases) != expected:
            issues.append("GATE-RECORD: future authorization phrases drifted")
    for field in _AUTHORIZATION_GATE_FALSE_FIELDS:
        if record.get(field) is not False:
            issues.append(f"GATE-RECORD: {field} must remain false")
    for field in _AUTHORIZATION_GATE_TRUE_FIELDS:
        if record.get(field) is not True:
            issues.append(f"GATE-RECORD: {field} must remain true")
    return issues


def write_next_artifacts_runner_authorization_gate_record(
    *,
    project_root: Path,
    smoke_manifest_dir: Path,
    plan_blueprint_dir: Path,
    output_dir: Path,
    preflight_report_path: Path | None = None,
) -> dict[str, Any]:
    """Write a no-execution future authorization gate record."""
    output_dir.mkdir(parents=True, exist_ok=True)
    record = build_next_artifacts_runner_authorization_gate_record(
        project_root=project_root,
        smoke_manifest_dir=smoke_manifest_dir,
        plan_blueprint_dir=plan_blueprint_dir,
        preflight_report_path=preflight_report_path,
    )
    issue_path = output_dir / NEXT_ARTIFACTS_AUTHORIZATION_GATE_ISSUES_FILENAME
    issue_rows = [
        {"issue_index": index, "issue": issue}
        for index, issue in enumerate(record["issues"], start=1)
    ] or [{"issue_index": "", "issue": "none"}]
    write_csv_rows(issue_path, issue_rows)

    record["issue_csv"] = str(issue_path)
    record["issue_csv_sha256"] = sha256_file(issue_path)
    record_path = output_dir / NEXT_ARTIFACTS_AUTHORIZATION_GATE_RECORD_FILENAME
    write_json_atomic(record_path, record, sort_keys=True)
    record["record_path"] = str(record_path)
    record["record_sha256"] = sha256_file(record_path)
    return record


def evaluate_next_artifacts_future_authorization_request(
    *,
    requested_action: str,
    supplied_phrase: str,
    gate_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate a future authorization phrase without changing execution state."""
    required_phrases = {
        "runner_implementation": RUNNER_IMPLEMENTATION_AUTHORIZATION_PHRASE,
        "bounded_smoke_execution": BOUNDED_SMOKE_AUTHORIZATION_PHRASE,
        "production_generation": PRODUCTION_GENERATION_AUTHORIZATION_PHRASE,
    }
    issues: list[str] = []
    required_phrase = required_phrases.get(requested_action, "")
    if not required_phrase:
        issues.append(f"AUTH-PHRASE: unsupported requested_action={requested_action}")

    gate_status = "not_supplied"
    if gate_record is not None:
        gate_status = str(gate_record.get("status", "missing_status"))
        gate_issues = validate_next_artifacts_runner_authorization_gate_record(gate_record)
        issues.extend(f"AUTH-PHRASE-GATE: {issue}" for issue in gate_issues)

    phrase_exact_match = bool(required_phrase) and supplied_phrase == required_phrase
    if not required_phrase:
        status = FUTURE_AUTHORIZATION_ACTION_INVALID
    elif not phrase_exact_match:
        status = FUTURE_AUTHORIZATION_PHRASE_MISMATCH
    elif requested_action == "runner_implementation":
        status = FUTURE_AUTHORIZATION_PHRASE_MATCH_RUNNER_IMPLEMENTATION
    else:
        status = FUTURE_AUTHORIZATION_PHRASE_MATCH_BLOCKED_NO_EXECUTION

    if issues and phrase_exact_match:
        status = FUTURE_AUTHORIZATION_PHRASE_MATCH_BLOCKED_NO_EXECUTION

    return {
        "schema_version": "nodi_comsol_next_artifacts_future_authorization_phrase_check_v1",
        "requested_action": requested_action,
        "authorization_request_status": status,
        "required_phrase": required_phrase,
        "supplied_phrase_sha256": hashlib.sha256(
            supplied_phrase.encode("utf-8")
        ).hexdigest(),
        "phrase_exact_match": phrase_exact_match,
        "gate_status": gate_status,
        "issues": issues,
        "this_check_authorizes_runner_implementation": False,
        "this_check_authorizes_runner_execution": False,
        "this_check_authorizes_bounded_smoke_execution": False,
        "this_check_authorizes_production_generation": False,
        "this_check_authorizes_nodi_run": False,
        "this_check_authorizes_comsol_run": False,
        "this_check_authorizes_joint_route_class_regeneration": False,
        "this_check_authorizes_qch_eta": False,
        "this_check_authorizes_yield": False,
        "this_check_authorizes_winner": False,
        "this_check_authorizes_true_w_eff_claim": False,
        "this_check_authorizes_measured_geometry_claim": False,
        "this_check_authorizes_optical_solver_output_claim": False,
        "this_check_authorizes_fabrication_release": False,
        "this_check_authorizes_p3_solver_conclusion": False,
        "no_runner_execution": True,
        "no_smoke_execution": True,
        "no_nodi_run": True,
        "no_comsol_run": True,
        "no_production_artifact": True,
        "no_joint_route_class_regeneration": True,
        "claim_boundary": "future_authorization_phrase_check_only_no_execution_state_change",
    }


def build_position_response_runner_launch_plan() -> dict[str, Any]:
    """Build the PRS runner implementation launch plan without executing it."""
    p1_routes = sorted(
        route for route in PRS_APPROVED_ROUTE_MATRIX if route != PRS_P2_DIAGNOSTIC_TRAP_ROUTE
    )
    p2_routes = [PRS_P2_DIAGNOSTIC_TRAP_ROUTE]
    view_count = len(PRS_APPROVED_VIEWS)
    diameter_count = len(PRS_APPROVED_DIAMETERS_NM)
    p1_rows = len(p1_routes) * diameter_count * view_count * ROWS_PER_ROUTE_DIAMETER_VIEW
    p2_rows = len(p2_routes) * diameter_count * view_count * ROWS_PER_ROUTE_DIAMETER_VIEW
    plan = {
        "schema_version": "nodi_position_response_surface_runner_launch_plan_v1",
        "artifact": POSITION_RESPONSE_ARTIFACT,
        "artifact_version": POSITION_RESPONSE_VERSION,
        "runner_entrypoint": "tools/audits/build_nodi_position_response_surface.py",
        "runner_implementation_status": RUNNER_IMPLEMENTATION_READY_STATUS,
        "runner_execution_status": "NOT_EXECUTED",
        "allowed_current_action": "write_runner_launch_plan_sidecar_only",
        "route_scope_p1_preferred": [_route_id_from_tuple(route) for route in p1_routes],
        "route_scope_p2_diagnostic_trap": [_route_id_from_tuple(route) for route in p2_routes],
        "diameter_scope_nm": [str(value) for value in sorted(PRS_APPROVED_DIAMETERS_NM)],
        "view_scope": sorted(PRS_APPROVED_VIEWS),
        "distribution_contract": {
            "edge_norm_1d_bins": EDGE_BASE_BIN_COUNT,
            "xz_norm_2d_bins": XZ_BASE_BIN_COUNT,
            "special_aggregates_per_distribution": SPECIAL_AGGREGATE_COUNT_PER_DISTRIBUTION,
            "rows_per_route_diameter_view": ROWS_PER_ROUTE_DIAMETER_VIEW,
        },
        "planned_row_arithmetic": {
            "p1_preferred_expected_rows": p1_rows,
            "p2_diagnostic_trap_expected_rows": p2_rows,
            "total_if_all_approved_routes_expected_rows": p1_rows + p2_rows,
        },
        "runner_phases_implemented_as_contract": [
            "load_route_diameter_view_manifest",
            "generate_edge_and_xz_bin_definitions",
            "prepare_event_accumulation_contract",
            "prepare_post_seed_aggregation_contract",
            "prepare_per_seed_diagnostic_sidecar_contract",
            "join_guardrail_state_contract",
            "attach_neutral_nodi_flow_condition_contract",
            "run_validator_before_release_candidate_write",
        ],
        "future_execution_prerequisites": {
            "bounded_smoke_phrase": BOUNDED_SMOKE_AUTHORIZATION_PHRASE,
            "production_generation_phrase": PRODUCTION_GENERATION_AUTHORIZATION_PHRASE,
            "requires_separate_future_authorization": True,
        },
        "claim_boundary": PRS_CLAIM_BOUNDARY,
        **_runner_implementation_no_execution_flags(),
    }
    return plan


def build_effective_aperture_runner_launch_plan() -> dict[str, Any]:
    """Build the EAS runner implementation launch plan without executing it."""
    route_count = len(EAS_APPROVED_ROUTE_MATRIX)
    view_count = len(PRS_APPROVED_VIEWS)
    mode_count = len(EAS_APPROVED_MODES)
    plan = {
        "schema_version": "nodi_effective_aperture_surrogate_runner_launch_plan_v1",
        "artifact": APERTURE_SURROGATE_ARTIFACT,
        "artifact_version": APERTURE_SURROGATE_VERSION,
        "runner_entrypoint": (
            "tools/audits/build_nodi_effective_aperture_surrogate_sensitivity.py"
        ),
        "runner_implementation_status": RUNNER_IMPLEMENTATION_READY_STATUS,
        "runner_execution_status": "NOT_EXECUTED",
        "allowed_current_action": "write_runner_launch_plan_sidecar_only",
        "route_scope": [
            _route_id_from_tuple(route) for route in sorted(EAS_APPROVED_ROUTE_MATRIX)
        ],
        "view_scope": sorted(PRS_APPROVED_VIEWS),
        "aperture_surrogate_modes": sorted(EAS_APPROVED_MODES),
        "planned_row_arithmetic": {
            "route_count": route_count,
            "view_count": view_count,
            "mode_count": mode_count,
            "total_route_view_mode_rows_if_all_modes": route_count * view_count * mode_count,
        },
        "descriptor_contract": {
            "source_geometry_descriptor_sha": GEOMETRY_DESCRIPTOR_SHA256,
            "route_geometry_id_comsol_version": GEOMETRY_DESCRIPTOR_VERSION,
            "claim_boundary": GEOMETRY_DESCRIPTOR_CLAIM_BOUNDARY,
            "descriptor_is_not_measured_geometry": True,
            "descriptor_is_not_true_optical_w_eff": True,
            "descriptor_is_not_optical_solver_output": True,
        },
        "runner_phases_implemented_as_contract": [
            "load_rank_and_guardrail_sources",
            "load_comsol_geometry_descriptor",
            "derive_surrogate_aperture_modes",
            "preserve_nonpositive_min_aperture_as_blocking_evidence",
            "prepare_relative_eta_proxy_contract",
            "prepare_rank_flip_and_candidate_family_flip_contract",
            "prepare_solver_contract_trigger_flags",
            "run_validator_before_release_candidate_write",
        ],
        "future_execution_prerequisites": {
            "bounded_smoke_phrase": BOUNDED_SMOKE_AUTHORIZATION_PHRASE,
            "production_generation_phrase": PRODUCTION_GENERATION_AUTHORIZATION_PHRASE,
            "requires_separate_future_authorization": True,
        },
        "claim_boundary": EAS_CLAIM_BOUNDARY,
        **_runner_implementation_no_execution_flags(),
    }
    return plan


def write_position_response_runner_launch_plan(output_dir: Path) -> dict[str, Any]:
    """Write the PRS runner launch-plan sidecar without executing the runner."""
    return _write_runner_launch_plan(
        output_dir=output_dir,
        filename=PRS_RUNNER_LAUNCH_PLAN_FILENAME,
        plan=build_position_response_runner_launch_plan(),
    )


def write_effective_aperture_runner_launch_plan(output_dir: Path) -> dict[str, Any]:
    """Write the EAS runner launch-plan sidecar without executing the runner."""
    return _write_runner_launch_plan(
        output_dir=output_dir,
        filename=EAS_RUNNER_LAUNCH_PLAN_FILENAME,
        plan=build_effective_aperture_runner_launch_plan(),
    )


def validate_runner_launch_plan(plan: Mapping[str, Any]) -> list[str]:
    """Validate that a runner launch plan is implementation-only."""
    issues: list[str] = []
    if plan.get("runner_implementation_status") != RUNNER_IMPLEMENTATION_READY_STATUS:
        issues.append("RUNNER-LAUNCH: runner_implementation_status drifted")
    if plan.get("runner_execution_status") != "NOT_EXECUTED":
        issues.append("RUNNER-LAUNCH: runner_execution_status must remain NOT_EXECUTED")
    for field in _RUNNER_IMPLEMENTATION_FALSE_FIELDS:
        if plan.get(field) is not False:
            issues.append(f"RUNNER-LAUNCH: {field} must remain false")
    for field in _RUNNER_IMPLEMENTATION_TRUE_FIELDS:
        if plan.get(field) is not True:
            issues.append(f"RUNNER-LAUNCH: {field} must remain true")
    if plan.get("allowed_current_action") != "write_runner_launch_plan_sidecar_only":
        issues.append("RUNNER-LAUNCH: allowed_current_action drifted")
    return issues


def build_position_response_source_accumulation_job_plan(
    *,
    route_source_path: Path,
    route_scope: str = "all_approved",
    seeds: Sequence[int] = PRS_SOURCE_ACCUMULATION_SEEDS,
    n_events_per_seed: int = PRS_SOURCE_ACCUMULATION_TARGET_EVENTS_PER_SEED,
) -> dict[str, Any]:
    """Plan PRS source accumulation jobs without executing NODI."""
    issues: list[str] = []
    blockers: list[dict[str, str]] = []
    if route_scope not in PRS_SOURCE_ACCUMULATION_APPROVED_ROUTE_SCOPES:
        issues.append(f"PRS-ACCUM: unsupported route_scope={route_scope}")
    if int(n_events_per_seed) < PRS_SOURCE_ACCUMULATION_TARGET_EVENTS_PER_SEED:
        issues.append(
            "PRS-ACCUM: n_events_per_seed below diagnostic floor "
            f"{PRS_SOURCE_ACCUMULATION_TARGET_EVENTS_PER_SEED}"
        )
    if not seeds:
        issues.append("PRS-ACCUM: at least one seed is required")

    route_source_rows: list[dict[str, str]] = []
    route_source_sha = ""
    if route_source_path.exists():
        route_source_rows = read_csv_rows(route_source_path)
        route_source_sha = sha256_file(route_source_path)
    else:
        blockers.append(
            _prs_source_accumulation_blocker(
                blocker_id="PRS-ACCUM-B01",
                status="blocked_missing_route_source",
                current_evidence=f"missing route source: {route_source_path}",
                unblock_action="provide a runner-compatible EV/gold route-source CSV",
            )
        )

    route_source_issues = _validate_prs_accumulation_route_source(route_source_rows)
    issues.extend(route_source_issues)
    particle_by_diameter = _prs_accumulation_particle_by_diameter(route_source_rows)
    missing_diameters = [
        diameter
        for diameter in sorted(PRS_APPROVED_DIAMETERS_NM)
        if diameter not in particle_by_diameter
    ]
    if missing_diameters:
        blockers.append(
            _prs_source_accumulation_blocker(
                blocker_id="PRS-ACCUM-B02",
                status="blocked_missing_particle_binding_for_diameter",
                current_evidence="missing diameters: "
                + ",".join(str(value) for value in missing_diameters),
                unblock_action="provide EV/exosome particle rows for every approved PRS diameter",
            )
        )

    selected_routes = _prs_accumulation_selected_routes(route_scope)
    missing_slices = _prs_accumulation_missing_slices(
        route_source_rows=route_source_rows,
        selected_routes=selected_routes,
        particle_by_diameter=particle_by_diameter,
    )
    if missing_slices:
        blockers.append(
            _prs_source_accumulation_blocker(
                blocker_id="PRS-ACCUM-B03",
                status="blocked_missing_route_particle_slices",
                current_evidence=f"missing slice count: {len(missing_slices)}",
                unblock_action=(
                    "provide route-source rows for every approved "
                    "route/diameter particle binding"
                ),
            )
        )

    job_rows = _prs_source_accumulation_job_rows(
        route_source_path=route_source_path,
        route_source_sha=route_source_sha,
        selected_routes=selected_routes,
        particle_by_diameter=particle_by_diameter,
        route_source_rows=route_source_rows,
        seeds=seeds,
        n_events_per_seed=int(n_events_per_seed),
    )
    status = (
        PRS_SOURCE_ACCUMULATION_BLOCKED_STATUS
        if issues or blockers
        else PRS_SOURCE_ACCUMULATION_PASS_STATUS
    )
    p1_job_count = sum(
        1 for row in job_rows if row["route_scope_class"] == "p1_preferred"
    )
    p2_job_count = sum(
        1 for row in job_rows if row["route_scope_class"] == "p2_diagnostic_trap"
    )
    report: dict[str, Any] = {
        "schema_version": "nodi_position_response_source_accumulation_job_plan_v1",
        "status": status,
        "artifact": POSITION_RESPONSE_BIN_SOURCE_ARTIFACT,
        "downstream_artifact": POSITION_RESPONSE_ARTIFACT,
        "gate_role": "source_accumulation_job_plan_only",
        "allowed_current_action": "write_source_accumulation_job_plan_sidecars_only",
        "route_scope": route_scope,
        "route_source_path": str(route_source_path),
        "route_source_sha256": route_source_sha,
        "route_source_row_count": len(route_source_rows),
        "approved_route_count": len(selected_routes),
        "approved_diameter_count": len(PRS_APPROVED_DIAMETERS_NM),
        "view_count": len(PRS_APPROVED_VIEWS),
        "seed_count": len(seeds),
        "seeds": [int(seed) for seed in seeds],
        "target_n_events_per_seed": int(n_events_per_seed),
        "target_n_events_floor_basis": (
            "xz_441_bins_times_min_100_per_bin_floor_not_sufficiency_guarantee"
        ),
        "post_run_required_gate": PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
        "planned_job_count": len(job_rows),
        "p1_preferred_job_count": p1_job_count,
        "p2_diagnostic_trap_job_count": p2_job_count,
        "planned_requested_event_count": len(job_rows) * int(n_events_per_seed),
        "expected_bin_source_rows_per_job": ROWS_PER_ROUTE_DIAMETER_VIEW,
        "expected_bin_source_rows_if_all_jobs_complete": (
            len(job_rows) * ROWS_PER_ROUTE_DIAMETER_VIEW
        ),
        "particle_binding_count": len(particle_by_diameter),
        "missing_diameters": missing_diameters,
        "missing_route_particle_slice_count": len(missing_slices),
        "job_plan_rows": job_rows,
        "blockers": blockers,
        "issues": issues,
        "runner_execution_authorized": False,
        "job_plan_execution_authorized": False,
        "nodi_run_performed": False,
        "full_runner_execution_performed": False,
        "position_response_surface_production_generated": False,
        "production_generation_performed": False,
        "comsol_run_performed": False,
        "joint_route_class_regenerated": False,
        "no_prs_production_artifact": True,
        "no_comsol_run": True,
        "no_joint_route_class_regeneration": True,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_winner": True,
        "not_detection_probability": True,
        "not_true_W_eff": True,
        "not_measured_geometry": True,
        "not_optical_solver_output": True,
        "not_fabrication_release": True,
        "not_P3_solver_conclusion": True,
        "claim_boundary": PRS_CLAIM_BOUNDARY,
        "stop_reason": "source_accumulation_job_plan_written_not_executed"
        if status == PRS_SOURCE_ACCUMULATION_PASS_STATUS
        else "source_accumulation_job_plan_inputs_blocked",
    }
    validation_issues = validate_position_response_source_accumulation_job_plan_report(report)
    if validation_issues:
        report["status"] = PRS_SOURCE_ACCUMULATION_BLOCKED_STATUS
        report["issues"] = [*issues, *validation_issues]
    return report


def write_position_response_source_accumulation_job_plan_bundle(
    *,
    route_source_path: Path,
    output_dir: Path,
    route_scope: str = "all_approved",
    seeds: Sequence[int] = PRS_SOURCE_ACCUMULATION_SEEDS,
    n_events_per_seed: int = PRS_SOURCE_ACCUMULATION_TARGET_EVENTS_PER_SEED,
) -> dict[str, Any]:
    """Write PRS source accumulation job-plan sidecars without execution."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_position_response_source_accumulation_job_plan(
        route_source_path=route_source_path,
        route_scope=route_scope,
        seeds=seeds,
        n_events_per_seed=n_events_per_seed,
    )
    job_plan_path = output_dir / PRS_SOURCE_ACCUMULATION_JOB_PLAN_FILENAME
    write_csv_rows(job_plan_path, report["job_plan_rows"] or _empty_accumulation_job_rows())
    blocker_rows = report["blockers"] or [
        {
            "artifact": "none",
            "blocker_id": "none",
            "status": "not_blocked",
            "required_input_or_policy": "route_source_particle_binding_and_slices",
            "current_evidence": "",
            "unblock_action": "",
            "claim_boundary": PRS_CLAIM_BOUNDARY,
        }
    ]
    blocker_path = output_dir / PRS_SOURCE_ACCUMULATION_BLOCKERS_FILENAME
    write_csv_rows(blocker_path, blocker_rows)
    issue_rows = [
        {"issue_index": index, "issue": issue}
        for index, issue in enumerate(report["issues"], start=1)
    ] or [{"issue_index": "", "issue": "none"}]
    issue_path = output_dir / PRS_SOURCE_ACCUMULATION_ISSUES_FILENAME
    write_csv_rows(issue_path, issue_rows)
    report["job_plan_csv"] = str(job_plan_path)
    report["job_plan_csv_sha256"] = sha256_file(job_plan_path)
    report["blocker_csv"] = str(blocker_path)
    report["blocker_csv_sha256"] = sha256_file(blocker_path)
    report["issue_csv"] = str(issue_path)
    report["issue_csv_sha256"] = sha256_file(issue_path)
    report_path = output_dir / PRS_SOURCE_ACCUMULATION_REPORT_FILENAME
    write_json_atomic(report_path, report, sort_keys=True)
    report["report_path"] = str(report_path)
    report["report_sha256"] = sha256_file(report_path)
    return report


def validate_position_response_source_accumulation_job_plan_report(
    report: Mapping[str, Any],
) -> list[str]:
    """Validate PRS source accumulation job-plan boundaries."""
    issues: list[str] = []
    if (
        report.get("schema_version")
        != "nodi_position_response_source_accumulation_job_plan_v1"
    ):
        issues.append("PRS-ACCUM: schema_version drifted")
    if report.get("status") not in {
        PRS_SOURCE_ACCUMULATION_PASS_STATUS,
        PRS_SOURCE_ACCUMULATION_BLOCKED_STATUS,
    }:
        issues.append("PRS-ACCUM: invalid status")
    if report.get("allowed_current_action") != "write_source_accumulation_job_plan_sidecars_only":
        issues.append("PRS-ACCUM: allowed_current_action drifted")
    if report.get("post_run_required_gate") != PRS_SOURCE_SUFFICIENCY_PASS_STATUS:
        issues.append("PRS-ACCUM: post_run_required_gate drifted")
    job_rows = report.get("job_plan_rows")
    if not isinstance(job_rows, list):
        issues.append("PRS-ACCUM: job_plan_rows must be a list")
        job_rows = []
    if report.get("status") == PRS_SOURCE_ACCUMULATION_PASS_STATUS and not job_rows:
        issues.append("PRS-ACCUM: pass status requires job_plan_rows")
    for field in (
        "runner_execution_authorized",
        "job_plan_execution_authorized",
        "nodi_run_performed",
        "full_runner_execution_performed",
        "position_response_surface_production_generated",
        "production_generation_performed",
        "comsol_run_performed",
        "joint_route_class_regenerated",
    ):
        if report.get(field) is not False:
            issues.append(f"PRS-ACCUM: {field} must remain false")
    for field in (
        "no_prs_production_artifact",
        "no_comsol_run",
        "no_joint_route_class_regeneration",
        "not_qch_weighted",
        "not_yield",
        "not_winner",
        "not_detection_probability",
        "not_true_W_eff",
        "not_measured_geometry",
        "not_optical_solver_output",
        "not_fabrication_release",
        "not_P3_solver_conclusion",
    ):
        if report.get(field) is not True:
            issues.append(f"PRS-ACCUM: {field} must remain true")
    for row_index, row in enumerate(job_rows, start=1):
        if _value(row, "execution_authorized") != "false":
            _issue(issues, row_index, "PRS-ACCUM-J01", "job execution authorized")
        if _value(row, "preflight_only") != "true":
            _issue(issues, row_index, "PRS-ACCUM-J02", "job row not preflight_only")
        if _value(row, "production_prs_generated") != "false":
            _issue(issues, row_index, "PRS-ACCUM-J03", "job row generated production PRS")
        if _value(row, "post_run_required_gate") != PRS_SOURCE_SUFFICIENCY_PASS_STATUS:
            _issue(issues, row_index, "PRS-ACCUM-J04", "post-run gate drifted")
        if (
            report.get("status") == PRS_SOURCE_ACCUMULATION_PASS_STATUS
            and _value(row, "route_source_binding_status") != "available"
        ):
            _issue(issues, row_index, "PRS-ACCUM-J05", "route source binding unavailable")
        if (
            _value(row, "target_event_floor_basis")
            != "xz_441_bins_times_min_100_per_bin_floor_not_sufficiency_guarantee"
        ):
            _issue(issues, row_index, "PRS-ACCUM-J06", "target event floor basis drifted")
    return issues


def select_position_response_source_accumulation_bounded_shard_jobs(
    job_rows: Sequence[Mapping[str, Any]],
    *,
    max_jobs: int = PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_DEFAULT_MAX_JOBS,
) -> list[dict[str, Any]]:
    """Select a tiny executable PRS source-accumulation shard from a job plan."""
    issues: list[str] = []
    if int(max_jobs) < 1:
        issues.append("PRS-ACCUM-SHARD: max_jobs must be positive")
    if int(max_jobs) > PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MAX_JOBS:
        issues.append(
            "PRS-ACCUM-SHARD: max_jobs exceeds bounded-shard ceiling "
            f"{PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MAX_JOBS}"
        )
    selected: list[dict[str, Any]] = []
    for row_index, row in enumerate(job_rows, start=1):
        row_issues = _validate_prs_accumulation_bounded_shard_job_row(row, row_index)
        if row_issues:
            issues.extend(row_issues)
            continue
        selected.append(dict(row))
        if len(selected) >= int(max_jobs):
            break
    if not selected:
        issues.append("PRS-ACCUM-SHARD: no executable bounded-shard job rows found")
    if issues:
        raise ContractValidationError(POSITION_RESPONSE_BIN_SOURCE_ARTIFACT, issues)
    return selected


def position_response_source_accumulation_bounded_shard_manifest_rows(
    *,
    selected_job_rows: Sequence[Mapping[str, Any]],
    n_events_per_job: int,
    event_source_path: Path,
    event_source_sha256: str,
    bin_source_path: Path,
    bin_source_sha256: str,
    source_availability_status: str,
    source_numeric_sufficiency_status: str,
) -> list[dict[str, str]]:
    """Build execution-manifest rows for a bounded source-accumulation shard."""
    rows: list[dict[str, str]] = []
    for index, job in enumerate(selected_job_rows, start=1):
        rows.append(
            {
                "bounded_shard_execution_artifact_version": (
                    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_BOUNDED_SHARD_V1"
                ),
                "execution_id": f"PRS_ACCUM_SHARD_{index:06d}",
                "source_job_id": _value(job, "job_id"),
                "route_scope_class": _value(job, "route_scope_class"),
                "route_id_nodi": _value(job, "route_id_nodi"),
                "lambda_nm": _value(job, "lambda_nm"),
                "W_nominal_nm": _value(job, "W_nominal_nm"),
                "D_nm": _value(job, "D_nm"),
                "diameter_nm": _value(job, "diameter_nm"),
                "particle_name": _value(job, "particle_name"),
                "NODI_view": _value(job, "NODI_view"),
                "seed": _value(job, "seed"),
                "source_scope": PRS_SOURCE_PRODUCTION_SCOPE,
                "n_events_requested_per_seed_plan": _value(
                    job,
                    "n_events_requested_per_seed",
                ),
                "n_events_executed_for_bounded_shard": str(int(n_events_per_job)),
                "target_event_floor_basis": _value(job, "target_event_floor_basis"),
                "post_run_required_gate": PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
                "source_availability_status": source_availability_status,
                "source_numeric_sufficiency_status": source_numeric_sufficiency_status,
                "event_source_path": str(event_source_path),
                "event_source_sha256": event_source_sha256,
                "bin_source_path": str(bin_source_path),
                "bin_source_sha256": bin_source_sha256,
                "bounded_shard_only": "true",
                "bounded_shard_execution_authorized": "true",
                "selected_job_execution_authorized": "true",
                "bounded_shard_execution_performed": "true",
                "full_job_plan_execution_authorized": "false",
                "full_runner_execution_authorized": "false",
                "full_runner_execution_performed": "false",
                "position_response_surface_production_generated": "false",
                "production_generation_performed": "false",
                "comsol_run_performed": "false",
                "joint_route_class_regenerated": "false",
                "preflight_only": "true",
                "production_prs_generated": "false",
                "not_qch_weighted": "true",
                "not_yield": "true",
                "not_winner": "true",
                "not_detection_probability": "true",
                "not_true_W_eff": "true",
                "not_measured_geometry": "true",
                "not_optical_solver_output": "true",
                "not_fabrication_release": "true",
                "not_P3_solver_conclusion": "true",
                "claim_boundary": PRS_BIN_SOURCE_CLAIM_BOUNDARY,
                "downstream_claim_boundary": PRS_CLAIM_BOUNDARY,
            }
        )
    return rows


def validate_position_response_source_accumulation_bounded_shard_report(
    report: Mapping[str, Any],
) -> list[str]:
    """Validate bounded source-accumulation execution without PRS production."""
    issues: list[str] = []
    if (
        report.get("schema_version")
        != "nodi_position_response_source_accumulation_bounded_shard_execution_v1"
    ):
        issues.append("PRS-ACCUM-SHARD: schema_version drifted")
    if report.get("status") not in {
        PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_PASS_STATUS,
        PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_BLOCKED_STATUS,
    }:
        issues.append("PRS-ACCUM-SHARD: invalid status")
    if report.get("artifact") != POSITION_RESPONSE_BIN_SOURCE_ARTIFACT:
        issues.append("PRS-ACCUM-SHARD: artifact drifted")
    if report.get("downstream_artifact") != POSITION_RESPONSE_ARTIFACT:
        issues.append("PRS-ACCUM-SHARD: downstream artifact drifted")
    if (
        report.get("allowed_current_action")
        != "execute_bounded_source_accumulation_shard_sidecars_only"
    ):
        issues.append("PRS-ACCUM-SHARD: allowed_current_action drifted")
    selected_job_count = _int_report_value(report, "selected_job_count")
    n_events_per_job = _int_report_value(report, "n_events_per_job")
    if selected_job_count is None or selected_job_count < 0:
        issues.append("PRS-ACCUM-SHARD: selected_job_count invalid")
    elif selected_job_count > PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MAX_JOBS:
        issues.append("PRS-ACCUM-SHARD: selected_job_count exceeds shard ceiling")
    if n_events_per_job is None or n_events_per_job < 1:
        issues.append("PRS-ACCUM-SHARD: n_events_per_job invalid")
    elif n_events_per_job > PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MAX_EVENTS_PER_JOB:
        issues.append("PRS-ACCUM-SHARD: n_events_per_job exceeds shard ceiling")
    if report.get("post_run_required_gate") != PRS_SOURCE_SUFFICIENCY_PASS_STATUS:
        issues.append("PRS-ACCUM-SHARD: post_run_required_gate drifted")
    if report.get("source_availability_status") != PRS_SOURCE_PREFLIGHT_PASS_STATUS:
        issues.append("PRS-ACCUM-SHARD: source availability must pass before review")
    if (
        report.get("source_numeric_sufficiency_status")
        != PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS
    ):
        issues.append(
            "PRS-ACCUM-SHARD: bounded shard must remain numeric-sufficiency blocked"
        )
    for field in (
        "full_job_plan_execution_authorized",
        "full_runner_execution_authorized",
        "full_runner_execution_performed",
        "position_response_surface_production_generated",
        "production_generation_performed",
        "comsol_run_performed",
        "joint_route_class_regenerated",
    ):
        if report.get(field) is not False:
            issues.append(f"PRS-ACCUM-SHARD: {field} must remain false")
    for field in (
        "no_prs_production_artifact",
        "no_comsol_run",
        "no_joint_route_class_regeneration",
        "not_qch_weighted",
        "not_yield",
        "not_winner",
        "not_detection_probability",
        "not_true_W_eff",
        "not_measured_geometry",
        "not_optical_solver_output",
        "not_fabrication_release",
        "not_P3_solver_conclusion",
        "source_numeric_sufficiency_expected_blocked_due_to_bounded_shard",
    ):
        if report.get(field) is not True:
            issues.append(f"PRS-ACCUM-SHARD: {field} must remain true")
    if report.get("status") == PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_PASS_STATUS:
        for field in (
            "bounded_shard_execution_authorized",
            "selected_job_execution_authorized",
            "bounded_shard_execution_performed",
            "nodi_bounded_shard_run_performed",
        ):
            if report.get(field) is not True:
                issues.append(f"PRS-ACCUM-SHARD: {field} must be true on PASS")
        if report.get("bin_source_rows") != (
            (selected_job_count or 0) * ROWS_PER_ROUTE_DIAMETER_VIEW
        ):
            issues.append("PRS-ACCUM-SHARD: bin source row arithmetic drifted")
    manifest_rows = report.get("execution_manifest_rows")
    if not isinstance(manifest_rows, list):
        issues.append("PRS-ACCUM-SHARD: execution_manifest_rows must be a list")
        manifest_rows = []
    for row_index, row in enumerate(manifest_rows, start=1):
        _validate_prs_accumulation_bounded_shard_manifest_row(row, row_index, issues)
    if report.get("claim_boundary") != PRS_BIN_SOURCE_CLAIM_BOUNDARY:
        issues.append("PRS-ACCUM-SHARD: source claim boundary drifted")
    if report.get("downstream_claim_boundary") != PRS_CLAIM_BOUNDARY:
        issues.append("PRS-ACCUM-SHARD: downstream claim boundary drifted")
    return issues


def build_position_response_source_accumulation_bounded_shard_report(
    *,
    authorization_phrase: str,
    job_plan_path: Path,
    job_plan_sha256: str,
    selected_job_rows: Sequence[Mapping[str, Any]],
    n_events_per_job: int,
    event_source_path: Path,
    event_source_sha256: str,
    event_row_count: int,
    bin_source_path: Path,
    bin_source_sha256: str,
    bin_source_row_count: int,
    source_availability_report: Mapping[str, Any],
    source_numeric_sufficiency_report: Mapping[str, Any],
    elapsed_s: float = 0.0,
) -> dict[str, Any]:
    """Build a bounded source-accumulation shard execution report."""
    phrase_match = authorization_phrase == (
        PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_AUTHORIZATION_PHRASE
    )
    source_availability_status = str(source_availability_report.get("status", ""))
    source_numeric_sufficiency_status = str(
        source_numeric_sufficiency_report.get("status", "")
    )
    manifest_rows = position_response_source_accumulation_bounded_shard_manifest_rows(
        selected_job_rows=selected_job_rows,
        n_events_per_job=int(n_events_per_job),
        event_source_path=event_source_path,
        event_source_sha256=event_source_sha256,
        bin_source_path=bin_source_path,
        bin_source_sha256=bin_source_sha256,
        source_availability_status=source_availability_status,
        source_numeric_sufficiency_status=source_numeric_sufficiency_status,
    )
    issues: list[str] = []
    if not phrase_match:
        issues.append("PRS-ACCUM-SHARD: authorization phrase mismatch")
    if source_availability_status != PRS_SOURCE_PREFLIGHT_PASS_STATUS:
        issues.append("PRS-ACCUM-SHARD: source availability preflight did not pass")
    if source_numeric_sufficiency_status != PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS:
        issues.append(
            "PRS-ACCUM-SHARD: bounded shard unexpectedly passed numeric sufficiency"
        )
    expected_source_rows = len(selected_job_rows) * ROWS_PER_ROUTE_DIAMETER_VIEW
    if int(bin_source_row_count) != expected_source_rows:
        issues.append("PRS-ACCUM-SHARD: bin source row count mismatch")
    if int(n_events_per_job) > PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MAX_EVENTS_PER_JOB:
        issues.append("PRS-ACCUM-SHARD: n_events_per_job exceeds bounded ceiling")

    status = (
        PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_PASS_STATUS
        if not issues
        else PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_BLOCKED_STATUS
    )
    report: dict[str, Any] = {
        "schema_version": (
            "nodi_position_response_source_accumulation_bounded_shard_execution_v1"
        ),
        "status": status,
        "artifact": POSITION_RESPONSE_BIN_SOURCE_ARTIFACT,
        "downstream_artifact": POSITION_RESPONSE_ARTIFACT,
        "gate_role": "source_accumulation_bounded_shard_execution_not_production",
        "allowed_current_action": (
            "execute_bounded_source_accumulation_shard_sidecars_only"
        ),
        "required_authorization_phrase": (
            PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_AUTHORIZATION_PHRASE
        ),
        "authorization_phrase_exact_match": phrase_match,
        "job_plan_path": str(job_plan_path),
        "job_plan_sha256": job_plan_sha256,
        "selected_job_count": len(selected_job_rows),
        "n_events_per_job": int(n_events_per_job),
        "bounded_shard_max_jobs": PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MAX_JOBS,
        "bounded_shard_max_events_per_job": (
            PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MAX_EVENTS_PER_JOB
        ),
        "event_rows": int(event_row_count),
        "bin_source_rows": int(bin_source_row_count),
        "expected_bin_source_rows_per_job": ROWS_PER_ROUTE_DIAMETER_VIEW,
        "target_event_floor_basis": (
            "xz_441_bins_times_min_100_per_bin_floor_not_sufficiency_guarantee"
        ),
        "target_event_floor_is_not_sufficiency_evidence": True,
        "post_run_required_gate": PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
        "source_availability_status": source_availability_status,
        "source_availability_report_path": str(
            source_availability_report.get("report_path", "")
        ),
        "source_availability_report_sha256": str(
            source_availability_report.get("report_sha256", "")
        ),
        "source_available_candidate_count": source_availability_report.get(
            "source_available_candidate_count",
            0,
        ),
        "source_numeric_sufficiency_status": source_numeric_sufficiency_status,
        "source_numeric_sufficiency_report_path": str(
            source_numeric_sufficiency_report.get("report_path", "")
        ),
        "source_numeric_sufficiency_report_sha256": str(
            source_numeric_sufficiency_report.get("report_sha256", "")
        ),
        "numeric_sufficient_candidate_count": source_numeric_sufficiency_report.get(
            "numeric_sufficient_candidate_count",
            0,
        ),
        "source_numeric_sufficiency_expected_blocked_due_to_bounded_shard": True,
        "event_source_path": str(event_source_path),
        "event_source_sha256": event_source_sha256,
        "bin_source_path": str(bin_source_path),
        "bin_source_sha256": bin_source_sha256,
        "execution_manifest_rows": manifest_rows,
        "issues": issues,
        "bounded_shard_execution_authorized": phrase_match,
        "selected_job_execution_authorized": phrase_match,
        "bounded_shard_execution_performed": status
        == PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_PASS_STATUS,
        "nodi_bounded_shard_run_performed": status
        == PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_PASS_STATUS,
        "full_job_plan_execution_authorized": False,
        "full_runner_execution_authorized": False,
        "full_runner_execution_performed": False,
        "position_response_surface_production_generated": False,
        "production_generation_performed": False,
        "comsol_run_performed": False,
        "joint_route_class_regenerated": False,
        "no_prs_production_artifact": True,
        "no_comsol_run": True,
        "no_joint_route_class_regeneration": True,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_winner": True,
        "not_detection_probability": True,
        "not_true_W_eff": True,
        "not_measured_geometry": True,
        "not_optical_solver_output": True,
        "not_fabrication_release": True,
        "not_P3_solver_conclusion": True,
        "claim_boundary": PRS_BIN_SOURCE_CLAIM_BOUNDARY,
        "downstream_claim_boundary": PRS_CLAIM_BOUNDARY,
        "stop_reason": "bounded_shard_source_sidecars_written_numeric_sufficiency_blocked",
        "elapsed_s": elapsed_s,
    }
    validation_issues = validate_position_response_source_accumulation_bounded_shard_report(
        report
    )
    if validation_issues:
        report["status"] = PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_BLOCKED_STATUS
        report["issues"] = [*issues, *validation_issues]
        report["bounded_shard_execution_performed"] = False
        report["nodi_bounded_shard_run_performed"] = False
    return report


def write_position_response_source_accumulation_bounded_shard_sidecars(
    *,
    output_dir: Path,
    report: dict[str, Any],
) -> dict[str, Any]:
    """Write bounded source-accumulation shard manifest/report sidecars."""
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = (
        output_dir / PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_MANIFEST_FILENAME
    )
    write_csv_rows(
        manifest_path,
        report["execution_manifest_rows"]
        or _empty_accumulation_bounded_shard_manifest_rows(),
    )
    issue_rows = [
        {"issue_index": index, "issue": issue}
        for index, issue in enumerate(report["issues"], start=1)
    ] or [{"issue_index": "", "issue": "none"}]
    issue_path = output_dir / PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_ISSUES_FILENAME
    write_csv_rows(issue_path, issue_rows)
    report["execution_manifest_csv"] = str(manifest_path)
    report["execution_manifest_csv_sha256"] = sha256_file(manifest_path)
    report["issue_csv"] = str(issue_path)
    report["issue_csv_sha256"] = sha256_file(issue_path)
    report_path = output_dir / PRS_SOURCE_ACCUMULATION_BOUNDED_SHARD_REPORT_FILENAME
    write_json_atomic(report_path, report, sort_keys=True)
    report["report_path"] = str(report_path)
    report["report_sha256"] = sha256_file(report_path)
    return report


def build_position_response_source_accumulation_campaign_policy(
    *,
    job_plan_path: Path,
    jobs_per_shard: int = PRS_SOURCE_ACCUMULATION_CAMPAIGN_DEFAULT_JOBS_PER_SHARD,
    max_parallel_shards: int = PRS_SOURCE_ACCUMULATION_CAMPAIGN_DEFAULT_MAX_PARALLEL_SHARDS,
) -> dict[str, Any]:
    """Build a no-execution accumulation campaign policy from a job plan."""
    issues: list[str] = []
    job_plan_rows: list[dict[str, str]] = []
    job_plan_sha = ""
    if job_plan_path.exists():
        job_plan_rows = read_csv_rows(job_plan_path)
        job_plan_sha = sha256_file(job_plan_path)
    else:
        issues.append(f"PRS-ACCUM-CAMPAIGN: missing job plan {job_plan_path}")
    if int(jobs_per_shard) < 1:
        issues.append("PRS-ACCUM-CAMPAIGN: jobs_per_shard must be positive")
    if int(jobs_per_shard) > PRS_SOURCE_ACCUMULATION_CAMPAIGN_MAX_JOBS_PER_SHARD:
        issues.append(
            "PRS-ACCUM-CAMPAIGN: jobs_per_shard exceeds campaign policy ceiling "
            f"{PRS_SOURCE_ACCUMULATION_CAMPAIGN_MAX_JOBS_PER_SHARD}"
        )
    if int(max_parallel_shards) != 1:
        issues.append("PRS-ACCUM-CAMPAIGN: max_parallel_shards must remain 1")

    valid_job_rows: list[dict[str, str]] = []
    for row_index, row in enumerate(job_plan_rows, start=1):
        row_issues = _validate_prs_accumulation_bounded_shard_job_row(row, row_index)
        if row_issues:
            issues.extend(row_issues)
        else:
            valid_job_rows.append(dict(row))
    if not valid_job_rows:
        issues.append("PRS-ACCUM-CAMPAIGN: no valid job-plan rows")

    shard_rows, schedule_rows = _prs_source_accumulation_campaign_rows(
        job_rows=valid_job_rows,
        job_plan_path=job_plan_path,
        job_plan_sha=job_plan_sha,
        jobs_per_shard=int(jobs_per_shard),
    )
    planned_requested_event_count = sum(
        _row_int_value(row, "n_events_requested_per_seed") or 0
        for row in valid_job_rows
    )
    status = (
        PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_BLOCKED_STATUS
        if issues
        else PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_PASS_STATUS
    )
    report: dict[str, Any] = {
        "schema_version": "nodi_position_response_source_accumulation_campaign_policy_v1",
        "status": status,
        "artifact": POSITION_RESPONSE_BIN_SOURCE_ARTIFACT,
        "downstream_artifact": POSITION_RESPONSE_ARTIFACT,
        "gate_role": "source_accumulation_campaign_policy_only",
        "allowed_current_action": "write_campaign_policy_sidecars_only",
        "job_plan_path": str(job_plan_path),
        "job_plan_sha256": job_plan_sha,
        "job_plan_row_count": len(job_plan_rows),
        "valid_job_count": len(valid_job_rows),
        "jobs_per_shard": int(jobs_per_shard),
        "planned_shard_count": len(shard_rows),
        "max_parallel_shards": int(max_parallel_shards),
        "resume_strategy": (
            "sequential_shard_resume_by_job_plan_sha256_and_shard_completion_marker"
        ),
        "resume_requires_matching_job_plan_sha256": True,
        "skip_completed_shards_without_hash_match": False,
        "shard_completion_marker": (
            "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_SHARD_DONE.json"
        ),
        "post_shard_required_gate": (
            "source_availability_preflight_then_numeric_sufficiency_preflight"
        ),
        "post_shard_numeric_sufficiency_gate": PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
        "numeric_sufficiency_pass_action": (
            "stop_for_review_not_auto_production_prs"
        ),
        "numeric_sufficiency_blocked_action": (
            "continue_campaign_only_if_resource_budget_and_operator_policy_allow"
        ),
        "planned_requested_event_count": planned_requested_event_count,
        "expected_bin_source_rows_if_all_jobs_complete": (
            len(valid_job_rows) * ROWS_PER_ROUTE_DIAMETER_VIEW
        ),
        "campaign_shard_rows": shard_rows,
        "campaign_job_schedule_rows": schedule_rows,
        "issues": issues,
        "campaign_execution_authorized": False,
        "shard_execution_authorized": False,
        "full_runner_execution_authorized": False,
        "full_runner_execution_performed": False,
        "nodi_run_performed": False,
        "position_response_surface_production_generated": False,
        "production_generation_performed": False,
        "comsol_run_performed": False,
        "joint_route_class_regenerated": False,
        "no_prs_production_artifact": True,
        "no_comsol_run": True,
        "no_joint_route_class_regeneration": True,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_winner": True,
        "not_detection_probability": True,
        "not_true_W_eff": True,
        "not_measured_geometry": True,
        "not_optical_solver_output": True,
        "not_fabrication_release": True,
        "not_P3_solver_conclusion": True,
        "claim_boundary": PRS_BIN_SOURCE_CLAIM_BOUNDARY,
        "downstream_claim_boundary": PRS_CLAIM_BOUNDARY,
        "stop_reason": "campaign_policy_written_not_executed",
    }
    validation_issues = validate_position_response_source_accumulation_campaign_policy_report(
        report
    )
    if validation_issues:
        report["status"] = PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_BLOCKED_STATUS
        report["issues"] = [*issues, *validation_issues]
    return report


def write_position_response_source_accumulation_campaign_policy_bundle(
    *,
    job_plan_path: Path,
    output_dir: Path,
    jobs_per_shard: int = PRS_SOURCE_ACCUMULATION_CAMPAIGN_DEFAULT_JOBS_PER_SHARD,
    max_parallel_shards: int = PRS_SOURCE_ACCUMULATION_CAMPAIGN_DEFAULT_MAX_PARALLEL_SHARDS,
) -> dict[str, Any]:
    """Write a no-execution PRS source accumulation campaign policy bundle."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_position_response_source_accumulation_campaign_policy(
        job_plan_path=job_plan_path,
        jobs_per_shard=jobs_per_shard,
        max_parallel_shards=max_parallel_shards,
    )
    shard_path = output_dir / PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARDS_FILENAME
    write_csv_rows(
        shard_path,
        report["campaign_shard_rows"] or _empty_accumulation_campaign_shard_rows(),
    )
    schedule_path = output_dir / PRS_SOURCE_ACCUMULATION_CAMPAIGN_JOB_SCHEDULE_FILENAME
    write_csv_rows(
        schedule_path,
        report["campaign_job_schedule_rows"]
        or _empty_accumulation_campaign_schedule_rows(),
    )
    issue_rows = [
        {"issue_index": index, "issue": issue}
        for index, issue in enumerate(report["issues"], start=1)
    ] or [{"issue_index": "", "issue": "none"}]
    issue_path = output_dir / PRS_SOURCE_ACCUMULATION_CAMPAIGN_ISSUES_FILENAME
    write_csv_rows(issue_path, issue_rows)
    report["campaign_shards_csv"] = str(shard_path)
    report["campaign_shards_csv_sha256"] = sha256_file(shard_path)
    report["campaign_job_schedule_csv"] = str(schedule_path)
    report["campaign_job_schedule_csv_sha256"] = sha256_file(schedule_path)
    report["issue_csv"] = str(issue_path)
    report["issue_csv_sha256"] = sha256_file(issue_path)
    report_path = output_dir / PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_REPORT_FILENAME
    write_json_atomic(report_path, report, sort_keys=True)
    report["report_path"] = str(report_path)
    report["report_sha256"] = sha256_file(report_path)
    return report


def build_position_response_source_accumulation_campaign_runner_readiness(
    *,
    campaign_report_path: Path,
    campaign_shard_id: str | None = None,
) -> dict[str, Any]:
    """Build a no-execution readiness gate for the next campaign shard."""
    issues: list[str] = []
    campaign_report: dict[str, Any] = {}
    campaign_report_sha = ""
    if campaign_report_path.exists():
        campaign_report_sha = sha256_file(campaign_report_path)
        loaded = json.loads(campaign_report_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            campaign_report = dict(loaded)
        else:
            issues.append("PRS-ACCUM-RUNNER-READY: campaign report must be a JSON object")
    else:
        issues.append(
            f"PRS-ACCUM-RUNNER-READY: missing campaign report {campaign_report_path}"
        )

    if campaign_report:
        policy_issues = validate_position_response_source_accumulation_campaign_policy_report(
            campaign_report
        )
        issues.extend(
            f"PRS-ACCUM-RUNNER-READY: campaign policy validation issue: {issue}"
            for issue in policy_issues
        )
        if campaign_report.get("status") != PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_PASS_STATUS:
            issues.append("PRS-ACCUM-RUNNER-READY: campaign policy status is not PASS")

    shard_rows_raw = campaign_report.get("campaign_shard_rows", [])
    schedule_rows_raw = campaign_report.get("campaign_job_schedule_rows", [])
    shard_rows = list(shard_rows_raw) if isinstance(shard_rows_raw, list) else []
    schedule_rows = list(schedule_rows_raw) if isinstance(schedule_rows_raw, list) else []
    if not shard_rows:
        issues.append("PRS-ACCUM-RUNNER-READY: no campaign shard rows available")
    if not schedule_rows:
        issues.append("PRS-ACCUM-RUNNER-READY: no campaign schedule rows available")

    selected_shard_id = campaign_shard_id or (
        _value(shard_rows[0], "campaign_shard_id") if shard_rows else ""
    )
    selected_shard_rows = [
        dict(row)
        for row in shard_rows
        if _value(row, "campaign_shard_id") == selected_shard_id
    ]
    selected_schedule_rows = [
        dict(row)
        for row in schedule_rows
        if _value(row, "campaign_shard_id") == selected_shard_id
    ]
    if not selected_shard_id:
        issues.append("PRS-ACCUM-RUNNER-READY: selected campaign shard id is blank")
    if len(selected_shard_rows) != 1:
        issues.append(
            "PRS-ACCUM-RUNNER-READY: selected campaign shard id must match exactly one shard"
        )

    selected_shard_row = selected_shard_rows[0] if selected_shard_rows else {}
    selected_job_count = len(selected_schedule_rows)
    expected_job_count = _row_int_value(selected_shard_row, "job_count") or 0
    selected_requested_events = sum(
        _row_int_value(row, "n_events_requested_per_seed") or 0
        for row in selected_schedule_rows
    )
    selected_expected_bin_rows = sum(
        _row_int_value(row, "expected_bin_source_rows") or 0
        for row in selected_schedule_rows
    )
    if selected_shard_row and selected_job_count != expected_job_count:
        issues.append("PRS-ACCUM-RUNNER-READY: selected shard job count mismatch")
    if selected_shard_row and selected_requested_events != (
        _row_int_value(selected_shard_row, "planned_requested_event_count") or 0
    ):
        issues.append("PRS-ACCUM-RUNNER-READY: selected shard requested events mismatch")
    if selected_shard_row and selected_expected_bin_rows != (
        _row_int_value(selected_shard_row, "expected_bin_source_rows") or 0
    ):
        issues.append("PRS-ACCUM-RUNNER-READY: selected shard expected bin rows mismatch")

    status = (
        PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_BLOCKED_STATUS
        if issues
        else PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_PASS_STATUS
    )
    report: dict[str, Any] = {
        "schema_version": (
            "nodi_position_response_source_accumulation_campaign_runner_readiness_v1"
        ),
        "status": status,
        "artifact": POSITION_RESPONSE_BIN_SOURCE_ARTIFACT,
        "downstream_artifact": POSITION_RESPONSE_ARTIFACT,
        "gate_role": "source_accumulation_campaign_runner_readiness_only",
        "allowed_current_action": "write_campaign_runner_readiness_sidecars_only",
        "campaign_report_path": str(campaign_report_path),
        "campaign_report_sha256": campaign_report_sha,
        "campaign_policy_status": campaign_report.get("status", ""),
        "campaign_valid_job_count": campaign_report.get("valid_job_count", 0),
        "campaign_planned_shard_count": campaign_report.get("planned_shard_count", 0),
        "selected_campaign_shard_id": selected_shard_id,
        "selected_shard_sequence": _value(selected_shard_row, "shard_sequence"),
        "selected_job_count": selected_job_count,
        "selected_expected_job_count": expected_job_count,
        "selected_first_source_job_id": _value(selected_shard_row, "first_source_job_id"),
        "selected_last_source_job_id": _value(selected_shard_row, "last_source_job_id"),
        "selected_planned_requested_event_count": selected_requested_events,
        "selected_expected_bin_source_rows": selected_expected_bin_rows,
        "selected_campaign_shard_rows": selected_shard_rows,
        "selected_campaign_job_schedule_rows": selected_schedule_rows,
        "issues": issues,
        "runner_readiness_authorized": False,
        "shard_execution_authorized": False,
        "full_runner_execution_authorized": False,
        "full_runner_execution_performed": False,
        "nodi_run_performed": False,
        "position_response_surface_production_generated": False,
        "production_generation_performed": False,
        "comsol_run_performed": False,
        "joint_route_class_regenerated": False,
        "post_shard_required_gate": (
            "source_availability_preflight_then_numeric_sufficiency_preflight"
        ),
        "post_shard_numeric_sufficiency_gate": PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
        "numeric_sufficiency_pass_action": "stop_for_review_not_auto_production_prs",
        "next_required_authorization_phrase": (
            "authorize NODI PRS source accumulation campaign shard execution"
        ),
        "no_prs_production_artifact": True,
        "no_comsol_run": True,
        "no_joint_route_class_regeneration": True,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_winner": True,
        "not_detection_probability": True,
        "not_true_W_eff": True,
        "not_measured_geometry": True,
        "not_optical_solver_output": True,
        "not_fabrication_release": True,
        "not_P3_solver_conclusion": True,
        "claim_boundary": PRS_BIN_SOURCE_CLAIM_BOUNDARY,
        "downstream_claim_boundary": PRS_CLAIM_BOUNDARY,
        "stop_reason": "runner_readiness_written_not_executed",
    }
    validation_issues = (
        validate_position_response_source_accumulation_campaign_runner_readiness_report(
            report
        )
    )
    if validation_issues:
        report["status"] = (
            PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_BLOCKED_STATUS
        )
        report["issues"] = [*issues, *validation_issues]
    return report


def write_position_response_source_accumulation_campaign_runner_readiness_bundle(
    *,
    campaign_report_path: Path,
    output_dir: Path,
    campaign_shard_id: str | None = None,
) -> dict[str, Any]:
    """Write a no-execution runner-readiness bundle for one campaign shard."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_position_response_source_accumulation_campaign_runner_readiness(
        campaign_report_path=campaign_report_path,
        campaign_shard_id=campaign_shard_id,
    )
    shard_path = (
        output_dir / PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_SHARD_FILENAME
    )
    write_csv_rows(
        shard_path,
        report["selected_campaign_job_schedule_rows"]
        or _empty_accumulation_campaign_schedule_rows(),
    )
    issue_rows = [
        {"issue_index": index, "issue": issue}
        for index, issue in enumerate(report["issues"], start=1)
    ] or [{"issue_index": "", "issue": "none"}]
    issue_path = (
        output_dir / PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_ISSUES_FILENAME
    )
    write_csv_rows(issue_path, issue_rows)
    report["selected_shard_schedule_csv"] = str(shard_path)
    report["selected_shard_schedule_csv_sha256"] = sha256_file(shard_path)
    report["issue_csv"] = str(issue_path)
    report["issue_csv_sha256"] = sha256_file(issue_path)
    report_path = (
        output_dir / PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_REPORT_FILENAME
    )
    write_json_atomic(report_path, report, sort_keys=True)
    report["report_path"] = str(report_path)
    report["report_sha256"] = sha256_file(report_path)
    return report


def validate_position_response_source_accumulation_campaign_runner_readiness_report(
    report: Mapping[str, Any],
) -> list[str]:
    """Validate a runner-readiness report without authorizing shard execution."""
    issues: list[str] = []
    if (
        report.get("schema_version")
        != "nodi_position_response_source_accumulation_campaign_runner_readiness_v1"
    ):
        issues.append("PRS-ACCUM-RUNNER-READY: schema_version drifted")
    if report.get("status") not in {
        PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_PASS_STATUS,
        PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_BLOCKED_STATUS,
    }:
        issues.append("PRS-ACCUM-RUNNER-READY: invalid status")
    if (
        report.get("allowed_current_action")
        != "write_campaign_runner_readiness_sidecars_only"
    ):
        issues.append("PRS-ACCUM-RUNNER-READY: allowed_current_action drifted")
    if report.get("artifact") != POSITION_RESPONSE_BIN_SOURCE_ARTIFACT:
        issues.append("PRS-ACCUM-RUNNER-READY: artifact drifted")
    if report.get("downstream_artifact") != POSITION_RESPONSE_ARTIFACT:
        issues.append("PRS-ACCUM-RUNNER-READY: downstream artifact drifted")
    if report.get("campaign_policy_status") != PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_PASS_STATUS:
        issues.append("PRS-ACCUM-RUNNER-READY: campaign policy status must be PASS")
    if report.get("post_shard_numeric_sufficiency_gate") != PRS_SOURCE_SUFFICIENCY_PASS_STATUS:
        issues.append("PRS-ACCUM-RUNNER-READY: post shard numeric sufficiency gate drifted")
    if report.get("numeric_sufficiency_pass_action") != "stop_for_review_not_auto_production_prs":
        issues.append("PRS-ACCUM-RUNNER-READY: numeric sufficiency pass action drifted")
    if (
        report.get("next_required_authorization_phrase")
        != "authorize NODI PRS source accumulation campaign shard execution"
    ):
        issues.append("PRS-ACCUM-RUNNER-READY: next authorization phrase drifted")

    shard_rows = report.get("selected_campaign_shard_rows")
    schedule_rows = report.get("selected_campaign_job_schedule_rows")
    if not isinstance(shard_rows, list):
        issues.append("PRS-ACCUM-RUNNER-READY: selected shard rows must be a list")
        shard_rows = []
    if not isinstance(schedule_rows, list):
        issues.append("PRS-ACCUM-RUNNER-READY: selected schedule rows must be a list")
        schedule_rows = []
    if report.get("status") == PRS_SOURCE_ACCUMULATION_CAMPAIGN_RUNNER_READINESS_PASS_STATUS:
        if len(shard_rows) != 1:
            issues.append("PRS-ACCUM-RUNNER-READY: pass status requires one shard")
        if not schedule_rows:
            issues.append("PRS-ACCUM-RUNNER-READY: pass status requires schedule rows")
        if not report.get("selected_campaign_shard_id"):
            issues.append("PRS-ACCUM-RUNNER-READY: pass status requires shard id")
    for field in (
        "runner_readiness_authorized",
        "shard_execution_authorized",
        "full_runner_execution_authorized",
        "full_runner_execution_performed",
        "nodi_run_performed",
        "position_response_surface_production_generated",
        "production_generation_performed",
        "comsol_run_performed",
        "joint_route_class_regenerated",
    ):
        if report.get(field) is not False:
            issues.append(f"PRS-ACCUM-RUNNER-READY: {field} must remain false")
    for field in (
        "no_prs_production_artifact",
        "no_comsol_run",
        "no_joint_route_class_regeneration",
        "not_qch_weighted",
        "not_yield",
        "not_winner",
        "not_detection_probability",
        "not_true_W_eff",
        "not_measured_geometry",
        "not_optical_solver_output",
        "not_fabrication_release",
        "not_P3_solver_conclusion",
    ):
        if report.get(field) is not True:
            issues.append(f"PRS-ACCUM-RUNNER-READY: {field} must remain true")

    selected_shard_id = str(report.get("selected_campaign_shard_id") or "")
    for row_index, row in enumerate(shard_rows, start=1):
        _validate_prs_accumulation_campaign_shard_row(row, row_index, issues)
        if _value(row, "campaign_shard_id") != selected_shard_id:
            _issue(issues, row_index, "PRS-ACCUM-RUNNER-READY-H01", "selected shard id mismatch")
    for row_index, row in enumerate(schedule_rows, start=1):
        _validate_prs_accumulation_campaign_schedule_row(row, row_index, issues)
        if _value(row, "campaign_shard_id") != selected_shard_id:
            _issue(issues, row_index, "PRS-ACCUM-RUNNER-READY-S01", "selected shard id mismatch")
    if report.get("selected_job_count") != len(schedule_rows):
        issues.append("PRS-ACCUM-RUNNER-READY: selected job count drifted")
    expected_job_count = report.get("selected_expected_job_count")
    if shard_rows:
        shard_job_count = _row_int_value(shard_rows[0], "job_count") or 0
        if expected_job_count != shard_job_count:
            issues.append("PRS-ACCUM-RUNNER-READY: expected job count drifted")
        if report.get("selected_job_count") != shard_job_count:
            issues.append("PRS-ACCUM-RUNNER-READY: selected job count mismatch")
        if report.get("selected_planned_requested_event_count") != (
            _row_int_value(shard_rows[0], "planned_requested_event_count") or 0
        ):
            issues.append("PRS-ACCUM-RUNNER-READY: selected requested event count drifted")
        if report.get("selected_expected_bin_source_rows") != (
            _row_int_value(shard_rows[0], "expected_bin_source_rows") or 0
        ):
            issues.append("PRS-ACCUM-RUNNER-READY: selected bin source row count drifted")
    schedule_expected_rows = sum(
        _row_int_value(row, "expected_bin_source_rows") or 0 for row in schedule_rows
    )
    if report.get("selected_expected_bin_source_rows") != schedule_expected_rows:
        issues.append("PRS-ACCUM-RUNNER-READY: selected schedule bin source sum drifted")
    if report.get("claim_boundary") != PRS_BIN_SOURCE_CLAIM_BOUNDARY:
        issues.append("PRS-ACCUM-RUNNER-READY: claim boundary drifted")
    if report.get("downstream_claim_boundary") != PRS_CLAIM_BOUNDARY:
        issues.append("PRS-ACCUM-RUNNER-READY: downstream claim boundary drifted")
    return issues


def validate_position_response_source_accumulation_campaign_policy_report(
    report: Mapping[str, Any],
) -> list[str]:
    """Validate campaign policy sidecars without authorizing execution."""
    issues: list[str] = []
    if (
        report.get("schema_version")
        != "nodi_position_response_source_accumulation_campaign_policy_v1"
    ):
        issues.append("PRS-ACCUM-CAMPAIGN: schema_version drifted")
    if report.get("status") not in {
        PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_PASS_STATUS,
        PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_BLOCKED_STATUS,
    }:
        issues.append("PRS-ACCUM-CAMPAIGN: invalid status")
    if report.get("allowed_current_action") != "write_campaign_policy_sidecars_only":
        issues.append("PRS-ACCUM-CAMPAIGN: allowed_current_action drifted")
    if report.get("artifact") != POSITION_RESPONSE_BIN_SOURCE_ARTIFACT:
        issues.append("PRS-ACCUM-CAMPAIGN: artifact drifted")
    if report.get("downstream_artifact") != POSITION_RESPONSE_ARTIFACT:
        issues.append("PRS-ACCUM-CAMPAIGN: downstream artifact drifted")
    if report.get("max_parallel_shards") != 1:
        issues.append("PRS-ACCUM-CAMPAIGN: max_parallel_shards must remain 1")
    if report.get("post_shard_numeric_sufficiency_gate") != PRS_SOURCE_SUFFICIENCY_PASS_STATUS:
        issues.append("PRS-ACCUM-CAMPAIGN: post shard numeric sufficiency gate drifted")
    if report.get("numeric_sufficiency_pass_action") != "stop_for_review_not_auto_production_prs":
        issues.append("PRS-ACCUM-CAMPAIGN: numeric sufficiency pass action drifted")
    shard_rows = report.get("campaign_shard_rows")
    schedule_rows = report.get("campaign_job_schedule_rows")
    if not isinstance(shard_rows, list):
        issues.append("PRS-ACCUM-CAMPAIGN: campaign_shard_rows must be a list")
        shard_rows = []
    if not isinstance(schedule_rows, list):
        issues.append("PRS-ACCUM-CAMPAIGN: campaign_job_schedule_rows must be a list")
        schedule_rows = []
    if report.get("status") == PRS_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_PASS_STATUS:
        if not shard_rows or not schedule_rows:
            issues.append("PRS-ACCUM-CAMPAIGN: pass status requires schedule rows")
        if report.get("valid_job_count") != len(schedule_rows):
            issues.append("PRS-ACCUM-CAMPAIGN: valid_job_count does not match schedule")
        if report.get("planned_shard_count") != len(shard_rows):
            issues.append("PRS-ACCUM-CAMPAIGN: planned_shard_count does not match shards")
    for field in (
        "campaign_execution_authorized",
        "shard_execution_authorized",
        "full_runner_execution_authorized",
        "full_runner_execution_performed",
        "nodi_run_performed",
        "position_response_surface_production_generated",
        "production_generation_performed",
        "comsol_run_performed",
        "joint_route_class_regenerated",
    ):
        if report.get(field) is not False:
            issues.append(f"PRS-ACCUM-CAMPAIGN: {field} must remain false")
    for field in (
        "resume_requires_matching_job_plan_sha256",
        "no_prs_production_artifact",
        "no_comsol_run",
        "no_joint_route_class_regeneration",
        "not_qch_weighted",
        "not_yield",
        "not_winner",
        "not_detection_probability",
        "not_true_W_eff",
        "not_measured_geometry",
        "not_optical_solver_output",
        "not_fabrication_release",
        "not_P3_solver_conclusion",
    ):
        if report.get(field) is not True:
            issues.append(f"PRS-ACCUM-CAMPAIGN: {field} must remain true")
    if report.get("skip_completed_shards_without_hash_match") is not False:
        issues.append("PRS-ACCUM-CAMPAIGN: hash-mismatched resume must be forbidden")

    shard_ids = {_value(row, "campaign_shard_id") for row in shard_rows}
    scheduled_job_ids: list[str] = []
    shard_job_count_sum = 0
    for row_index, row in enumerate(shard_rows, start=1):
        _validate_prs_accumulation_campaign_shard_row(row, row_index, issues)
        shard_job_count_sum += _row_int_value(row, "job_count") or 0
    for row_index, row in enumerate(schedule_rows, start=1):
        _validate_prs_accumulation_campaign_schedule_row(row, row_index, issues)
        shard_id = _value(row, "campaign_shard_id")
        if shard_id not in shard_ids:
            _issue(issues, row_index, "PRS-ACCUM-CAMPAIGN-S20", "unknown shard id")
        scheduled_job_ids.append(_value(row, "source_job_id"))
    if len(scheduled_job_ids) != len(set(scheduled_job_ids)):
        issues.append("PRS-ACCUM-CAMPAIGN: duplicate scheduled source_job_id")
    if shard_job_count_sum != len(schedule_rows):
        issues.append("PRS-ACCUM-CAMPAIGN: shard job count sum mismatch")
    expected_events = sum(
        _row_int_value(row, "n_events_requested_per_seed") or 0
        for row in schedule_rows
    )
    if report.get("planned_requested_event_count") != expected_events:
        issues.append("PRS-ACCUM-CAMPAIGN: planned requested event count drifted")
    if report.get("expected_bin_source_rows_if_all_jobs_complete") != (
        len(schedule_rows) * ROWS_PER_ROUTE_DIAMETER_VIEW
    ):
        issues.append("PRS-ACCUM-CAMPAIGN: expected bin-source row count drifted")
    if report.get("claim_boundary") != PRS_BIN_SOURCE_CLAIM_BOUNDARY:
        issues.append("PRS-ACCUM-CAMPAIGN: claim boundary drifted")
    if report.get("downstream_claim_boundary") != PRS_CLAIM_BOUNDARY:
        issues.append("PRS-ACCUM-CAMPAIGN: downstream claim boundary drifted")
    return issues


def _prs_source_accumulation_campaign_rows(
    *,
    job_rows: Sequence[Mapping[str, Any]],
    job_plan_path: Path,
    job_plan_sha: str,
    jobs_per_shard: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    shard_rows: list[dict[str, Any]] = []
    schedule_rows: list[dict[str, Any]] = []
    for shard_index, start in enumerate(range(0, len(job_rows), jobs_per_shard), start=1):
        shard_jobs = list(job_rows[start : start + jobs_per_shard])
        shard_id = f"PRS_ACCUM_CAMPAIGN_SHARD_{shard_index:04d}"
        requested_events = sum(
            _row_int_value(row, "n_events_requested_per_seed") or 0
            for row in shard_jobs
        )
        first_job_id = _value(shard_jobs[0], "job_id") if shard_jobs else ""
        last_job_id = _value(shard_jobs[-1], "job_id") if shard_jobs else ""
        route_ids = sorted({_value(row, "route_id_nodi") for row in shard_jobs})
        diameters = sorted({_value(row, "diameter_nm") for row in shard_jobs}, key=lambda x: int(float(x)))
        views = sorted({_value(row, "NODI_view") for row in shard_jobs})
        seeds = sorted({_value(row, "seed") for row in shard_jobs}, key=lambda x: int(float(x)))
        shard_rows.append(
            {
                "campaign_policy_artifact_version": (
                    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_V1"
                ),
                "campaign_shard_id": shard_id,
                "shard_sequence": shard_index,
                "job_count": len(shard_jobs),
                "first_source_job_id": first_job_id,
                "last_source_job_id": last_job_id,
                "route_id_nodi_values": ";".join(route_ids),
                "diameter_nm_values": ";".join(diameters),
                "NODI_view_values": ";".join(views),
                "seed_values": ";".join(seeds),
                "planned_requested_event_count": requested_events,
                "expected_bin_source_rows": len(shard_jobs) * ROWS_PER_ROUTE_DIAMETER_VIEW,
                "job_plan_path": str(job_plan_path),
                "job_plan_sha256": job_plan_sha,
                "resume_cursor": f"{job_plan_sha}:{shard_id}:{first_job_id}:{last_job_id}",
                "shard_completion_marker": (
                    "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_SHARD_DONE.json"
                ),
                "post_shard_required_gate": (
                    "source_availability_preflight_then_numeric_sufficiency_preflight"
                ),
                "post_shard_numeric_sufficiency_gate": PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
                "policy_only_not_executed": "true",
                "execution_authorized": "false",
                "shard_execution_performed": "false",
                "production_prs_generated": "false",
                "comsol_run_performed": "false",
                "joint_route_class_regenerated": "false",
                "not_qch_weighted": "true",
                "not_yield": "true",
                "not_winner": "true",
                "not_detection_probability": "true",
                "not_true_W_eff": "true",
                "not_measured_geometry": "true",
                "not_optical_solver_output": "true",
                "not_fabrication_release": "true",
                "not_P3_solver_conclusion": "true",
                "claim_boundary": PRS_BIN_SOURCE_CLAIM_BOUNDARY,
                "downstream_claim_boundary": PRS_CLAIM_BOUNDARY,
            }
        )
        for job_sequence, job in enumerate(shard_jobs, start=1):
            campaign_job_sequence = start + job_sequence
            schedule_rows.append(
                {
                    "campaign_policy_artifact_version": (
                        "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_V1"
                    ),
                    "campaign_shard_id": shard_id,
                    "shard_sequence": shard_index,
                    "job_sequence_in_shard": job_sequence,
                    "campaign_job_sequence": campaign_job_sequence,
                    "source_job_id": _value(job, "job_id"),
                    "route_scope_class": _value(job, "route_scope_class"),
                    "route_id_nodi": _value(job, "route_id_nodi"),
                    "lambda_nm": _value(job, "lambda_nm"),
                    "W_nominal_nm": _value(job, "W_nominal_nm"),
                    "D_nm": _value(job, "D_nm"),
                    "diameter_nm": _value(job, "diameter_nm"),
                    "particle_name": _value(job, "particle_name"),
                    "NODI_view": _value(job, "NODI_view"),
                    "seed": _value(job, "seed"),
                    "n_events_requested_per_seed": _value(
                        job,
                        "n_events_requested_per_seed",
                    ),
                    "expected_bin_source_rows": ROWS_PER_ROUTE_DIAMETER_VIEW,
                    "route_source_binding_status": _value(
                        job,
                        "route_source_binding_status",
                    ),
                    "source_scope": PRS_SOURCE_PRODUCTION_SCOPE,
                    "job_plan_path": str(job_plan_path),
                    "job_plan_sha256": job_plan_sha,
                    "resume_cursor": (
                        f"{job_plan_sha}:{shard_id}:{_value(job, 'job_id')}"
                    ),
                    "post_shard_required_gate": (
                        "source_availability_preflight_then_numeric_sufficiency_preflight"
                    ),
                    "post_shard_numeric_sufficiency_gate": PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
                    "policy_only_not_executed": "true",
                    "execution_authorized": "false",
                    "shard_execution_performed": "false",
                    "production_prs_generated": "false",
                    "comsol_run_performed": "false",
                    "joint_route_class_regenerated": "false",
                    "not_qch_weighted": "true",
                    "not_yield": "true",
                    "not_winner": "true",
                    "not_detection_probability": "true",
                    "not_true_W_eff": "true",
                    "not_measured_geometry": "true",
                    "not_optical_solver_output": "true",
                    "not_fabrication_release": "true",
                    "not_P3_solver_conclusion": "true",
                    "claim_boundary": PRS_BIN_SOURCE_CLAIM_BOUNDARY,
                    "downstream_claim_boundary": PRS_CLAIM_BOUNDARY,
                }
            )
    return shard_rows, schedule_rows


def _validate_prs_accumulation_campaign_shard_row(
    row: Mapping[str, Any],
    row_index: int,
    issues: list[str],
) -> None:
    _validate_constant(
        row,
        "campaign_policy_artifact_version",
        "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_V1",
        row_index,
        "PRS-ACCUM-CAMPAIGN-H01",
        issues,
    )
    _validate_positive_int(row, "shard_sequence", row_index, "PRS-ACCUM-CAMPAIGN-H02", issues)
    _validate_positive_int(row, "job_count", row_index, "PRS-ACCUM-CAMPAIGN-H03", issues)
    _validate_nonnegative_int(row, "planned_requested_event_count", row_index, "PRS-ACCUM-CAMPAIGN-H04", issues)
    _validate_nonnegative_int(row, "expected_bin_source_rows", row_index, "PRS-ACCUM-CAMPAIGN-H05", issues)
    if _value(row, "post_shard_numeric_sufficiency_gate") != PRS_SOURCE_SUFFICIENCY_PASS_STATUS:
        _issue(issues, row_index, "PRS-ACCUM-CAMPAIGN-H06", "post shard gate drifted")
    if not _value(row, "resume_cursor"):
        _issue(issues, row_index, "PRS-ACCUM-CAMPAIGN-H07", "resume cursor blank")
    for field in (
        "policy_only_not_executed",
        "not_qch_weighted",
        "not_yield",
        "not_winner",
        "not_detection_probability",
        "not_true_W_eff",
        "not_measured_geometry",
        "not_optical_solver_output",
        "not_fabrication_release",
        "not_P3_solver_conclusion",
    ):
        _validate_bool_equals(
            row,
            field,
            True,
            row_index,
            "PRS-ACCUM-CAMPAIGN-H08",
            issues,
        )
    for field in (
        "execution_authorized",
        "shard_execution_performed",
        "production_prs_generated",
        "comsol_run_performed",
        "joint_route_class_regenerated",
    ):
        _validate_bool_equals(
            row,
            field,
            False,
            row_index,
            "PRS-ACCUM-CAMPAIGN-H09",
            issues,
        )
    _validate_constant(
        row,
        "claim_boundary",
        PRS_BIN_SOURCE_CLAIM_BOUNDARY,
        row_index,
        "PRS-ACCUM-CAMPAIGN-H10",
        issues,
    )
    _validate_constant(
        row,
        "downstream_claim_boundary",
        PRS_CLAIM_BOUNDARY,
        row_index,
        "PRS-ACCUM-CAMPAIGN-H11",
        issues,
    )


def _validate_prs_accumulation_campaign_schedule_row(
    row: Mapping[str, Any],
    row_index: int,
    issues: list[str],
) -> None:
    _validate_constant(
        row,
        "campaign_policy_artifact_version",
        "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_V1",
        row_index,
        "PRS-ACCUM-CAMPAIGN-S01",
        issues,
    )
    _validate_route_fields(
        row,
        approved_routes=PRS_APPROVED_ROUTE_MATRIX,
        row_index=row_index,
        issues=issues,
        rule_id="PRS-ACCUM-CAMPAIGN-S02",
    )
    diameter = _int_field(row, "diameter_nm", row_index, "PRS-ACCUM-CAMPAIGN-S03", issues)
    if diameter is not None and diameter not in PRS_APPROVED_DIAMETERS_NM:
        _issue(issues, row_index, "PRS-ACCUM-CAMPAIGN-S03", f"unapproved diameter={diameter}")
    _validate_enum(row, "NODI_view", PRS_APPROVED_VIEWS, row_index, "PRS-ACCUM-CAMPAIGN-S04", issues)
    _validate_positive_int(row, "seed", row_index, "PRS-ACCUM-CAMPAIGN-S05", issues)
    _validate_positive_int(row, "shard_sequence", row_index, "PRS-ACCUM-CAMPAIGN-S06", issues)
    _validate_positive_int(row, "job_sequence_in_shard", row_index, "PRS-ACCUM-CAMPAIGN-S07", issues)
    _validate_positive_int(row, "campaign_job_sequence", row_index, "PRS-ACCUM-CAMPAIGN-S08", issues)
    _validate_positive_int(row, "n_events_requested_per_seed", row_index, "PRS-ACCUM-CAMPAIGN-S09", issues)
    if _value(row, "route_source_binding_status") != "available":
        _issue(issues, row_index, "PRS-ACCUM-CAMPAIGN-S10", "route binding unavailable")
    if _value(row, "source_scope") != PRS_SOURCE_PRODUCTION_SCOPE:
        _issue(issues, row_index, "PRS-ACCUM-CAMPAIGN-S11", "source scope drifted")
    if _value(row, "post_shard_numeric_sufficiency_gate") != PRS_SOURCE_SUFFICIENCY_PASS_STATUS:
        _issue(issues, row_index, "PRS-ACCUM-CAMPAIGN-S12", "post shard gate drifted")
    if not _value(row, "resume_cursor"):
        _issue(issues, row_index, "PRS-ACCUM-CAMPAIGN-S13", "resume cursor blank")
    for field in (
        "policy_only_not_executed",
        "not_qch_weighted",
        "not_yield",
        "not_winner",
        "not_detection_probability",
        "not_true_W_eff",
        "not_measured_geometry",
        "not_optical_solver_output",
        "not_fabrication_release",
        "not_P3_solver_conclusion",
    ):
        _validate_bool_equals(
            row,
            field,
            True,
            row_index,
            "PRS-ACCUM-CAMPAIGN-S14",
            issues,
        )
    for field in (
        "execution_authorized",
        "shard_execution_performed",
        "production_prs_generated",
        "comsol_run_performed",
        "joint_route_class_regenerated",
    ):
        _validate_bool_equals(
            row,
            field,
            False,
            row_index,
            "PRS-ACCUM-CAMPAIGN-S15",
            issues,
        )
    _validate_constant(
        row,
        "claim_boundary",
        PRS_BIN_SOURCE_CLAIM_BOUNDARY,
        row_index,
        "PRS-ACCUM-CAMPAIGN-S16",
        issues,
    )
    _validate_constant(
        row,
        "downstream_claim_boundary",
        PRS_CLAIM_BOUNDARY,
        row_index,
        "PRS-ACCUM-CAMPAIGN-S17",
        issues,
    )


def _empty_accumulation_campaign_shard_rows() -> list[dict[str, str]]:
    return [
        {
            "campaign_policy_artifact_version": (
                "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_V1"
            ),
            "campaign_shard_id": "",
            "shard_sequence": "",
            "job_count": "",
            "first_source_job_id": "",
            "last_source_job_id": "",
            "route_id_nodi_values": "",
            "diameter_nm_values": "",
            "NODI_view_values": "",
            "seed_values": "",
            "planned_requested_event_count": "",
            "expected_bin_source_rows": "",
            "job_plan_path": "",
            "job_plan_sha256": "",
            "resume_cursor": "",
            "shard_completion_marker": (
                "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_SHARD_DONE.json"
            ),
            "post_shard_required_gate": (
                "source_availability_preflight_then_numeric_sufficiency_preflight"
            ),
            "post_shard_numeric_sufficiency_gate": PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
            "policy_only_not_executed": "true",
            "execution_authorized": "false",
            "shard_execution_performed": "false",
            "production_prs_generated": "false",
            "comsol_run_performed": "false",
            "joint_route_class_regenerated": "false",
            "not_qch_weighted": "true",
            "not_yield": "true",
            "not_winner": "true",
            "not_detection_probability": "true",
            "not_true_W_eff": "true",
            "not_measured_geometry": "true",
            "not_optical_solver_output": "true",
            "not_fabrication_release": "true",
            "not_P3_solver_conclusion": "true",
            "claim_boundary": PRS_BIN_SOURCE_CLAIM_BOUNDARY,
            "downstream_claim_boundary": PRS_CLAIM_BOUNDARY,
        }
    ]


def _empty_accumulation_campaign_schedule_rows() -> list[dict[str, str]]:
    return [
        {
            "campaign_policy_artifact_version": (
                "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_POLICY_V1"
            ),
            "campaign_shard_id": "",
            "shard_sequence": "",
            "job_sequence_in_shard": "",
            "campaign_job_sequence": "",
            "source_job_id": "",
            "route_scope_class": "",
            "route_id_nodi": "",
            "lambda_nm": "",
            "W_nominal_nm": "",
            "D_nm": "",
            "diameter_nm": "",
            "particle_name": "",
            "NODI_view": "",
            "seed": "",
            "n_events_requested_per_seed": "",
            "expected_bin_source_rows": str(ROWS_PER_ROUTE_DIAMETER_VIEW),
            "route_source_binding_status": "",
            "source_scope": PRS_SOURCE_PRODUCTION_SCOPE,
            "job_plan_path": "",
            "job_plan_sha256": "",
            "resume_cursor": "",
            "post_shard_required_gate": (
                "source_availability_preflight_then_numeric_sufficiency_preflight"
            ),
            "post_shard_numeric_sufficiency_gate": PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
            "policy_only_not_executed": "true",
            "execution_authorized": "false",
            "shard_execution_performed": "false",
            "production_prs_generated": "false",
            "comsol_run_performed": "false",
            "joint_route_class_regenerated": "false",
            "not_qch_weighted": "true",
            "not_yield": "true",
            "not_winner": "true",
            "not_detection_probability": "true",
            "not_true_W_eff": "true",
            "not_measured_geometry": "true",
            "not_optical_solver_output": "true",
            "not_fabrication_release": "true",
            "not_P3_solver_conclusion": "true",
            "claim_boundary": PRS_BIN_SOURCE_CLAIM_BOUNDARY,
            "downstream_claim_boundary": PRS_CLAIM_BOUNDARY,
        }
    ]


def _validate_prs_accumulation_bounded_shard_job_row(
    row: Mapping[str, Any],
    row_index: int,
) -> list[str]:
    issues: list[str] = []
    _validate_route_fields(
        row,
        approved_routes=PRS_APPROVED_ROUTE_MATRIX,
        row_index=row_index,
        issues=issues,
        rule_id="PRS-ACCUM-SHARD-J01",
    )
    diameter = _int_field(
        row,
        "diameter_nm",
        row_index,
        "PRS-ACCUM-SHARD-J02",
        issues,
    )
    if diameter is not None and diameter not in PRS_APPROVED_DIAMETERS_NM:
        _issue(
            issues,
            row_index,
            "PRS-ACCUM-SHARD-J02",
            f"unapproved diameter={diameter}",
        )
    _validate_enum(
        row,
        "NODI_view",
        PRS_APPROVED_VIEWS,
        row_index,
        "PRS-ACCUM-SHARD-J03",
        issues,
    )
    if _value(row, "route_source_binding_status") != "available":
        _issue(
            issues,
            row_index,
            "PRS-ACCUM-SHARD-J04",
            "route source binding is unavailable",
        )
    if _value(row, "source_scope") != PRS_SOURCE_PRODUCTION_SCOPE:
        _issue(
            issues,
            row_index,
            "PRS-ACCUM-SHARD-J05",
            "source_scope must remain production candidate",
        )
    if _value(row, "post_run_required_gate") != PRS_SOURCE_SUFFICIENCY_PASS_STATUS:
        _issue(
            issues,
            row_index,
            "PRS-ACCUM-SHARD-J06",
            "post-run required gate drifted",
        )
    if _value(row, "execution_authorized") != "false":
        _issue(
            issues,
            row_index,
            "PRS-ACCUM-SHARD-J07",
            "job-plan row must not pre-authorize execution",
        )
    if _value(row, "preflight_only") != "true":
        _issue(issues, row_index, "PRS-ACCUM-SHARD-J08", "row not preflight only")
    if _value(row, "production_prs_generated") != "false":
        _issue(
            issues,
            row_index,
            "PRS-ACCUM-SHARD-J09",
            "job row generated production PRS",
        )
    if (
        _value(row, "target_event_floor_basis")
        != "xz_441_bins_times_min_100_per_bin_floor_not_sufficiency_guarantee"
    ):
        _issue(
            issues,
            row_index,
            "PRS-ACCUM-SHARD-J10",
            "target event floor basis drifted",
        )
    return issues


def _validate_prs_accumulation_bounded_shard_manifest_row(
    row: Mapping[str, Any],
    row_index: int,
    issues: list[str],
) -> None:
    _validate_constant(
        row,
        "bounded_shard_execution_artifact_version",
        "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_BOUNDED_SHARD_V1",
        row_index,
        "PRS-ACCUM-SHARD-M01",
        issues,
    )
    _validate_route_fields(
        row,
        approved_routes=PRS_APPROVED_ROUTE_MATRIX,
        row_index=row_index,
        issues=issues,
        rule_id="PRS-ACCUM-SHARD-M02",
    )
    diameter = _int_field(
        row,
        "diameter_nm",
        row_index,
        "PRS-ACCUM-SHARD-M03",
        issues,
    )
    if diameter is not None and diameter not in PRS_APPROVED_DIAMETERS_NM:
        _issue(
            issues,
            row_index,
            "PRS-ACCUM-SHARD-M03",
            f"unapproved diameter={diameter}",
        )
    _validate_enum(
        row,
        "NODI_view",
        PRS_APPROVED_VIEWS,
        row_index,
        "PRS-ACCUM-SHARD-M04",
        issues,
    )
    if _value(row, "source_scope") != PRS_SOURCE_PRODUCTION_SCOPE:
        _issue(
            issues,
            row_index,
            "PRS-ACCUM-SHARD-M05",
            "source_scope drifted",
        )
    if _value(row, "post_run_required_gate") != PRS_SOURCE_SUFFICIENCY_PASS_STATUS:
        _issue(
            issues,
            row_index,
            "PRS-ACCUM-SHARD-M06",
            "post-run gate drifted",
        )
    if _value(row, "source_availability_status") != PRS_SOURCE_PREFLIGHT_PASS_STATUS:
        _issue(
            issues,
            row_index,
            "PRS-ACCUM-SHARD-M07",
            "source availability status must pass",
        )
    if (
        _value(row, "source_numeric_sufficiency_status")
        != PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS
    ):
        _issue(
            issues,
            row_index,
            "PRS-ACCUM-SHARD-M08",
            "bounded shard must remain numeric-sufficiency blocked",
        )
    for field in (
        "bounded_shard_only",
        "bounded_shard_execution_authorized",
        "selected_job_execution_authorized",
        "bounded_shard_execution_performed",
        "preflight_only",
        "not_qch_weighted",
        "not_yield",
        "not_winner",
        "not_detection_probability",
        "not_true_W_eff",
        "not_measured_geometry",
        "not_optical_solver_output",
        "not_fabrication_release",
        "not_P3_solver_conclusion",
    ):
        _validate_bool_equals(
            row,
            field,
            True,
            row_index,
            "PRS-ACCUM-SHARD-M09",
            issues,
        )
    for field in (
        "full_job_plan_execution_authorized",
        "full_runner_execution_authorized",
        "full_runner_execution_performed",
        "position_response_surface_production_generated",
        "production_generation_performed",
        "comsol_run_performed",
        "joint_route_class_regenerated",
        "production_prs_generated",
    ):
        _validate_bool_equals(
            row,
            field,
            False,
            row_index,
            "PRS-ACCUM-SHARD-M10",
            issues,
        )
    _validate_source_hash(
        row,
        field="event_source_sha256",
        row_index=row_index,
        rule_id="PRS-ACCUM-SHARD-M11",
        issues=issues,
        allow_pending=False,
    )
    _validate_source_hash(
        row,
        field="bin_source_sha256",
        row_index=row_index,
        rule_id="PRS-ACCUM-SHARD-M12",
        issues=issues,
        allow_pending=False,
    )
    _validate_constant(
        row,
        "claim_boundary",
        PRS_BIN_SOURCE_CLAIM_BOUNDARY,
        row_index,
        "PRS-ACCUM-SHARD-M13",
        issues,
    )
    _validate_constant(
        row,
        "downstream_claim_boundary",
        PRS_CLAIM_BOUNDARY,
        row_index,
        "PRS-ACCUM-SHARD-M14",
        issues,
    )


def _int_report_value(report: Mapping[str, Any], field: str) -> int | None:
    value = report.get(field)
    try:
        numeric = float(str(value))
    except (TypeError, ValueError):
        return None
    if not numeric.is_integer():
        return None
    return int(numeric)


def _empty_accumulation_bounded_shard_manifest_rows() -> list[dict[str, str]]:
    return [
        {
            "bounded_shard_execution_artifact_version": (
                "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_BOUNDED_SHARD_V1"
            ),
            "execution_id": "",
            "source_job_id": "",
            "route_scope_class": "",
            "route_id_nodi": "",
            "lambda_nm": "",
            "W_nominal_nm": "",
            "D_nm": "",
            "diameter_nm": "",
            "particle_name": "",
            "NODI_view": "",
            "seed": "",
            "source_scope": PRS_SOURCE_PRODUCTION_SCOPE,
            "n_events_requested_per_seed_plan": "",
            "n_events_executed_for_bounded_shard": "",
            "target_event_floor_basis": (
                "xz_441_bins_times_min_100_per_bin_floor_not_sufficiency_guarantee"
            ),
            "post_run_required_gate": PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
            "source_availability_status": "",
            "source_numeric_sufficiency_status": "",
            "event_source_path": "",
            "event_source_sha256": "",
            "bin_source_path": "",
            "bin_source_sha256": "",
            "bounded_shard_only": "true",
            "bounded_shard_execution_authorized": "false",
            "selected_job_execution_authorized": "false",
            "bounded_shard_execution_performed": "false",
            "full_job_plan_execution_authorized": "false",
            "full_runner_execution_authorized": "false",
            "full_runner_execution_performed": "false",
            "position_response_surface_production_generated": "false",
            "production_generation_performed": "false",
            "comsol_run_performed": "false",
            "joint_route_class_regenerated": "false",
            "preflight_only": "true",
            "production_prs_generated": "false",
            "not_qch_weighted": "true",
            "not_yield": "true",
            "not_winner": "true",
            "not_detection_probability": "true",
            "not_true_W_eff": "true",
            "not_measured_geometry": "true",
            "not_optical_solver_output": "true",
            "not_fabrication_release": "true",
            "not_P3_solver_conclusion": "true",
            "claim_boundary": PRS_BIN_SOURCE_CLAIM_BOUNDARY,
            "downstream_claim_boundary": PRS_CLAIM_BOUNDARY,
        }
    ]


def build_bounded_smoke_readiness_report(
    *,
    prs_launch_plan_path: Path,
    eas_launch_plan_path: Path,
) -> dict[str, Any]:
    """Build a no-execution bounded-smoke readiness report."""
    issues: list[str] = []
    prs_plan = _read_json_mapping(prs_launch_plan_path, "SMOKE-READY-PRS", issues)
    eas_plan = _read_json_mapping(eas_launch_plan_path, "SMOKE-READY-EAS", issues)

    if prs_plan is not None:
        issues.extend(f"SMOKE-READY-PRS: {issue}" for issue in validate_runner_launch_plan(prs_plan))
        if prs_plan.get("artifact") != POSITION_RESPONSE_ARTIFACT:
            issues.append("SMOKE-READY-PRS: artifact drifted")
        if prs_plan.get("runner_entrypoint") != "tools/audits/build_nodi_position_response_surface.py":
            issues.append("SMOKE-READY-PRS: runner_entrypoint drifted")
    if eas_plan is not None:
        issues.extend(f"SMOKE-READY-EAS: {issue}" for issue in validate_runner_launch_plan(eas_plan))
        if eas_plan.get("artifact") != APERTURE_SURROGATE_ARTIFACT:
            issues.append("SMOKE-READY-EAS: artifact drifted")
        if (
            eas_plan.get("runner_entrypoint")
            != "tools/audits/build_nodi_effective_aperture_surrogate_sensitivity.py"
        ):
            issues.append("SMOKE-READY-EAS: runner_entrypoint drifted")

    status = (
        BOUNDED_SMOKE_READINESS_PASS_STATUS
        if not issues
        else BOUNDED_SMOKE_READINESS_BLOCKED_STATUS
    )
    report: dict[str, Any] = {
        "schema_version": "nodi_comsol_next_artifacts_bounded_smoke_readiness_v1",
        "status": status,
        "issues": issues,
        "readiness_role": "bounded_smoke_preflight_no_execution",
        "allowed_current_action": "write_bounded_smoke_readiness_sidecar_only",
        "required_future_authorization_phrase": BOUNDED_SMOKE_AUTHORIZATION_PHRASE,
        "authorization_phrase_already_received": False,
        "bounded_smoke_execution_authorized": False,
        "runner_execution_authorized": False,
        "production_generation_authorized": False,
        "nodi_run_authorized": False,
        "comsol_run_authorized": False,
        "joint_route_class_regeneration_authorized": False,
        "qch_eta_authorized": False,
        "yield_authorized": False,
        "winner_authorized": False,
        "true_w_eff_claim_authorized": False,
        "measured_geometry_claim_authorized": False,
        "optical_solver_output_claim_authorized": False,
        "fabrication_release_authorized": False,
        "p3_solver_conclusion_authorized": False,
        "no_runner_execution": True,
        "no_smoke_execution": True,
        "no_nodi_run": True,
        "no_comsol_run": True,
        "no_production_artifact": True,
        "no_joint_route_class_regeneration": True,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_winner": True,
        "not_true_W_eff": True,
        "not_measured_geometry": True,
        "not_optical_solver_output": True,
        "not_fabrication_release": True,
        "not_P3_solver_conclusion": True,
        "claim_boundary": "bounded_smoke_readiness_preflight_only_no_execution",
        "source_files": [
            _source_file_entry("PRS runner launch plan", prs_launch_plan_path),
            _source_file_entry("EAS runner launch plan", eas_launch_plan_path),
        ],
        "readiness_summary": {
            "prs_runner_implementation_status": ""
            if prs_plan is None
            else str(prs_plan.get("runner_implementation_status", "")),
            "prs_runner_execution_status": ""
            if prs_plan is None
            else str(prs_plan.get("runner_execution_status", "")),
            "prs_planned_rows": ""
            if prs_plan is None
            else str(
                prs_plan.get("planned_row_arithmetic", {}).get(
                    "total_if_all_approved_routes_expected_rows", ""
                )
            ),
            "eas_runner_implementation_status": ""
            if eas_plan is None
            else str(eas_plan.get("runner_implementation_status", "")),
            "eas_runner_execution_status": ""
            if eas_plan is None
            else str(eas_plan.get("runner_execution_status", "")),
            "eas_planned_rows": ""
            if eas_plan is None
            else str(
                eas_plan.get("planned_row_arithmetic", {}).get(
                    "total_route_view_mode_rows_if_all_modes", ""
                )
            ),
        },
    }
    validation_issues = validate_bounded_smoke_readiness_report(report)
    if validation_issues:
        report["status"] = BOUNDED_SMOKE_READINESS_BLOCKED_STATUS
        report["issues"] = [*issues, *validation_issues]
    return report


def validate_bounded_smoke_readiness_report(report: Mapping[str, Any]) -> list[str]:
    """Validate that bounded-smoke readiness remains no-execution."""
    issues: list[str] = []
    if (
        report.get("schema_version")
        != "nodi_comsol_next_artifacts_bounded_smoke_readiness_v1"
    ):
        issues.append("SMOKE-READY: schema_version drifted")
    if report.get("status") not in {
        BOUNDED_SMOKE_READINESS_PASS_STATUS,
        BOUNDED_SMOKE_READINESS_BLOCKED_STATUS,
    }:
        issues.append("SMOKE-READY: invalid status")
    if report.get("allowed_current_action") != "write_bounded_smoke_readiness_sidecar_only":
        issues.append("SMOKE-READY: allowed_current_action drifted")
    if report.get("required_future_authorization_phrase") != BOUNDED_SMOKE_AUTHORIZATION_PHRASE:
        issues.append("SMOKE-READY: future smoke phrase drifted")
    for field in _BOUNDED_SMOKE_READINESS_FALSE_FIELDS:
        if report.get(field) is not False:
            issues.append(f"SMOKE-READY: {field} must remain false")
    for field in _BOUNDED_SMOKE_READINESS_TRUE_FIELDS:
        if report.get(field) is not True:
            issues.append(f"SMOKE-READY: {field} must remain true")
    return issues


def write_bounded_smoke_readiness_report(
    *,
    prs_launch_plan_path: Path,
    eas_launch_plan_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Write the bounded-smoke readiness sidecar without executing smoke."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_bounded_smoke_readiness_report(
        prs_launch_plan_path=prs_launch_plan_path,
        eas_launch_plan_path=eas_launch_plan_path,
    )
    issue_rows = [
        {"issue_index": index, "issue": issue}
        for index, issue in enumerate(report["issues"], start=1)
    ] or [{"issue_index": "", "issue": "none"}]
    issue_path = output_dir / NEXT_ARTIFACTS_BOUNDED_SMOKE_READINESS_ISSUES_FILENAME
    write_csv_rows(issue_path, issue_rows)

    report["issue_csv"] = str(issue_path)
    report["issue_csv_sha256"] = sha256_file(issue_path)
    report_path = output_dir / NEXT_ARTIFACTS_BOUNDED_SMOKE_READINESS_REPORT_FILENAME
    write_json_atomic(report_path, report, sort_keys=True)
    report["report_path"] = str(report_path)
    report["report_sha256"] = sha256_file(report_path)
    return report


def position_response_bounded_smoke_execution_manifest_rows() -> list[dict[str, str]]:
    """Return bounded-smoke execution evidence rows for the PRS contract path."""
    return _bounded_smoke_execution_rows_from_smoke_manifest(
        position_response_smoke_manifest_rows(),
        artifact_version=POSITION_RESPONSE_VERSION,
    )


def effective_aperture_bounded_smoke_execution_manifest_rows() -> list[dict[str, str]]:
    """Return bounded-smoke execution evidence rows for the EAS contract path."""
    return _bounded_smoke_execution_rows_from_smoke_manifest(
        effective_aperture_smoke_manifest_rows(),
        artifact_version=APERTURE_SURROGATE_VERSION,
    )


def build_bounded_smoke_execution_report(
    *,
    readiness_report_path: Path,
    authorization_phrase: str,
) -> dict[str, Any]:
    """Build a bounded-smoke execution report without production generation."""
    issues: list[str] = []
    readiness_report = _read_json_mapping(
        readiness_report_path,
        "SMOKE-EXEC-READY",
        issues,
    )
    if readiness_report is not None:
        readiness_issues = validate_bounded_smoke_readiness_report(readiness_report)
        issues.extend(f"SMOKE-EXEC-READY: {issue}" for issue in readiness_issues)
        if readiness_report.get("status") != BOUNDED_SMOKE_READINESS_PASS_STATUS:
            issues.append("SMOKE-EXEC-READY: readiness status is not pass")

    phrase_exact_match = authorization_phrase == BOUNDED_SMOKE_AUTHORIZATION_PHRASE
    if not phrase_exact_match:
        issues.append("SMOKE-EXEC-AUTH: authorization phrase does not exactly match")

    status = (
        BOUNDED_SMOKE_EXECUTION_PASS_STATUS
        if not issues
        else BOUNDED_SMOKE_EXECUTION_BLOCKED_STATUS
    )
    performed = status == BOUNDED_SMOKE_EXECUTION_PASS_STATUS
    report: dict[str, Any] = {
        "schema_version": "nodi_comsol_next_artifacts_bounded_smoke_execution_v1",
        "status": status,
        "issues": issues,
        "execution_role": "bounded_smoke_contract_sidecar_only",
        "allowed_current_action": "run_bounded_smoke_execution_sidecar_only",
        "required_authorization_phrase": BOUNDED_SMOKE_AUTHORIZATION_PHRASE,
        "authorization_phrase_supplied_sha256": hashlib.sha256(
            authorization_phrase.encode("utf-8")
        ).hexdigest(),
        "authorization_phrase_exact_match": phrase_exact_match,
        "readiness_report_path": str(readiness_report_path),
        "readiness_report_sha256": sha256_file(readiness_report_path)
        if readiness_report_path.exists()
        else "",
        "readiness_status": ""
        if readiness_report is None
        else str(readiness_report.get("status", "")),
        "runner_execution_scope": "bounded_smoke_contract_sidecar_only",
        "bounded_smoke_execution_authorized_by_phrase": performed,
        "bounded_smoke_execution_performed": performed,
        "bounded_smoke_runner_execution_authorized": performed,
        "bounded_smoke_sidecar_only": True,
        "production_generation_authorized": False,
        "production_generation_performed": False,
        "full_runner_execution_authorized": False,
        "full_runner_execution_performed": False,
        "nodi_run_authorized": False,
        "nodi_run_performed": False,
        "comsol_run_authorized": False,
        "comsol_run_performed": False,
        "joint_route_class_regeneration_authorized": False,
        "joint_route_class_regenerated": False,
        "no_nodi_run": True,
        "no_comsol_run": True,
        "no_production_artifact": True,
        "no_joint_route_class_regeneration": True,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_winner": True,
        "not_true_W_eff": True,
        "not_measured_geometry": True,
        "not_optical_solver_output": True,
        "not_fabrication_release": True,
        "not_P3_solver_conclusion": True,
        "claim_boundary": "bounded_smoke_execution_contract_sidecar_only_no_production",
        "planned_manifest_rows": {
            "position_response_surface": len(
                position_response_bounded_smoke_execution_manifest_rows()
            ),
            "effective_aperture_surrogate_sensitivity": len(
                effective_aperture_bounded_smoke_execution_manifest_rows()
            ),
        },
        "production_artifact_filenames": [],
        "forbidden_claims_absent": [
            "q_ch*eta",
            "q_ch*chi_selected*eta",
            "yield",
            "winner",
            "true_W_eff",
            "measured_geometry",
            "optical_solver_output",
            "fabrication_release",
            "P3_solver_conclusion",
        ],
    }
    validation_issues = validate_bounded_smoke_execution_report(report)
    if validation_issues:
        report["status"] = BOUNDED_SMOKE_EXECUTION_BLOCKED_STATUS
        report["issues"] = [*issues, *validation_issues]
        report["bounded_smoke_execution_authorized_by_phrase"] = False
        report["bounded_smoke_execution_performed"] = False
        report["bounded_smoke_runner_execution_authorized"] = False
    return report


def validate_bounded_smoke_execution_report(report: Mapping[str, Any]) -> list[str]:
    """Validate that bounded-smoke execution stays inside the smoke boundary."""
    issues: list[str] = []
    status = report.get("status")
    if (
        report.get("schema_version")
        != "nodi_comsol_next_artifacts_bounded_smoke_execution_v1"
    ):
        issues.append("SMOKE-EXEC: schema_version drifted")
    if status not in {
        BOUNDED_SMOKE_EXECUTION_PASS_STATUS,
        BOUNDED_SMOKE_EXECUTION_BLOCKED_STATUS,
    }:
        issues.append("SMOKE-EXEC: invalid status")
    if report.get("allowed_current_action") != "run_bounded_smoke_execution_sidecar_only":
        issues.append("SMOKE-EXEC: allowed_current_action drifted")
    if report.get("runner_execution_scope") != "bounded_smoke_contract_sidecar_only":
        issues.append("SMOKE-EXEC: runner_execution_scope drifted")
    if report.get("required_authorization_phrase") != BOUNDED_SMOKE_AUTHORIZATION_PHRASE:
        issues.append("SMOKE-EXEC: required authorization phrase drifted")
    if status == BOUNDED_SMOKE_EXECUTION_PASS_STATUS:
        for field in (
            "authorization_phrase_exact_match",
            "bounded_smoke_execution_authorized_by_phrase",
            "bounded_smoke_execution_performed",
            "bounded_smoke_runner_execution_authorized",
            "bounded_smoke_sidecar_only",
        ):
            if report.get(field) is not True:
                issues.append(f"SMOKE-EXEC: {field} must be true for pass")
    if status == BOUNDED_SMOKE_EXECUTION_BLOCKED_STATUS:
        for field in (
            "bounded_smoke_execution_authorized_by_phrase",
            "bounded_smoke_execution_performed",
            "bounded_smoke_runner_execution_authorized",
        ):
            if report.get(field) is not False:
                issues.append(f"SMOKE-EXEC: {field} must be false when blocked")
    for field in _BOUNDED_SMOKE_EXECUTION_FALSE_FIELDS:
        if report.get(field) is not False:
            issues.append(f"SMOKE-EXEC: {field} must remain false")
    for field in _BOUNDED_SMOKE_EXECUTION_TRUE_FIELDS:
        if report.get(field) is not True:
            issues.append(f"SMOKE-EXEC: {field} must remain true")
    if report.get("production_artifact_filenames") != []:
        issues.append("SMOKE-EXEC: production_artifact_filenames must stay empty")
    planned_rows = report.get("planned_manifest_rows", {})
    if not isinstance(planned_rows, Mapping):
        issues.append("SMOKE-EXEC: planned_manifest_rows must be an object")
    else:
        if planned_rows.get("position_response_surface") != len(
            position_response_bounded_smoke_execution_manifest_rows()
        ):
            issues.append("SMOKE-EXEC: PRS planned manifest row count drifted")
        if planned_rows.get("effective_aperture_surrogate_sensitivity") != len(
            effective_aperture_bounded_smoke_execution_manifest_rows()
        ):
            issues.append("SMOKE-EXEC: EAS planned manifest row count drifted")
    return issues


def validate_bounded_smoke_execution_manifest_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    artifact: str,
) -> list[str]:
    """Validate bounded-smoke execution manifest evidence rows."""
    issues: list[str] = []
    if not rows:
        issues.append(f"SMOKE-EXEC-MANIFEST-{artifact}: no rows")
    for row_index, row in enumerate(rows, start=1):
        if _value(row, "artifact") != artifact:
            _issue(issues, row_index, "SMOKE-EXEC-MANIFEST", "artifact drifted")
        if _value(row, "bounded_smoke_execution_status") != BOUNDED_SMOKE_EXECUTION_ROW_STATUS:
            _issue(
                issues,
                row_index,
                "SMOKE-EXEC-MANIFEST",
                "bounded_smoke_execution_status drifted",
            )
        if _value(row, "runner_execution_scope") != "bounded_smoke_contract_sidecar_only":
            _issue(issues, row_index, "SMOKE-EXEC-MANIFEST", "runner scope drifted")
        for field in _BOUNDED_SMOKE_MANIFEST_FALSE_FIELDS:
            if _value(row, field) != "false":
                _issue(issues, row_index, "SMOKE-EXEC-MANIFEST", f"{field} must be false")
        for field in _BOUNDED_SMOKE_MANIFEST_TRUE_FIELDS:
            if _value(row, field) != "true":
                _issue(issues, row_index, "SMOKE-EXEC-MANIFEST", f"{field} must be true")
    return issues


def write_bounded_smoke_execution_bundle(
    *,
    readiness_report_path: Path,
    authorization_phrase: str,
    output_dir: Path,
) -> dict[str, Any]:
    """Run bounded-smoke sidecar execution without production generation."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_bounded_smoke_execution_report(
        readiness_report_path=readiness_report_path,
        authorization_phrase=authorization_phrase,
    )

    files: list[dict[str, Any]] = []
    if report["status"] == BOUNDED_SMOKE_EXECUTION_PASS_STATUS:
        prs_rows = position_response_bounded_smoke_execution_manifest_rows()
        eas_rows = effective_aperture_bounded_smoke_execution_manifest_rows()
        manifest_issues = [
            *validate_bounded_smoke_execution_manifest_rows(
                prs_rows,
                artifact=POSITION_RESPONSE_ARTIFACT,
            ),
            *validate_bounded_smoke_execution_manifest_rows(
                eas_rows,
                artifact=APERTURE_SURROGATE_ARTIFACT,
            ),
        ]
        if manifest_issues:
            report["status"] = BOUNDED_SMOKE_EXECUTION_BLOCKED_STATUS
            report["issues"] = [*report["issues"], *manifest_issues]
            report["bounded_smoke_execution_authorized_by_phrase"] = False
            report["bounded_smoke_execution_performed"] = False
            report["bounded_smoke_runner_execution_authorized"] = False
        else:
            prs_path = output_dir / PRS_BOUNDED_SMOKE_EXECUTION_MANIFEST_FILENAME
            eas_path = output_dir / EAS_BOUNDED_SMOKE_EXECUTION_MANIFEST_FILENAME
            write_csv_rows(prs_path, prs_rows)
            write_csv_rows(eas_path, eas_rows)
            files.extend(
                [
                    {
                        "artifact": POSITION_RESPONSE_ARTIFACT,
                        "path": str(prs_path),
                        "sha256": sha256_file(prs_path),
                        "rows": len(prs_rows),
                        "artifact_status": "bounded_smoke_execution_sidecar_only",
                    },
                    {
                        "artifact": APERTURE_SURROGATE_ARTIFACT,
                        "path": str(eas_path),
                        "sha256": sha256_file(eas_path),
                        "rows": len(eas_rows),
                        "artifact_status": "bounded_smoke_execution_sidecar_only",
                    },
                ]
            )

    issue_rows = [
        {"issue_index": index, "issue": issue}
        for index, issue in enumerate(report["issues"], start=1)
    ] or [{"issue_index": "", "issue": "none"}]
    issue_path = output_dir / NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_ISSUES_FILENAME
    write_csv_rows(issue_path, issue_rows)
    files.append(
        {
            "artifact": "NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_ISSUES",
            "path": str(issue_path),
            "sha256": sha256_file(issue_path),
            "rows": len(issue_rows),
            "artifact_status": "bounded_smoke_execution_issue_sidecar",
        }
    )

    report["issue_csv"] = str(issue_path)
    report["issue_csv_sha256"] = sha256_file(issue_path)
    report["files"] = files
    report_path = output_dir / NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_REPORT_FILENAME
    write_json_atomic(report_path, report, sort_keys=True)
    report["report_path"] = str(report_path)
    report["report_sha256"] = sha256_file(report_path)
    return report


def build_production_generation_report(
    *,
    smoke_execution_report_path: Path,
    geometry_descriptor_path: Path,
    rank_source_path: Path,
    guardrail_table_path: Path,
    position_response_candidate_path: Path | None = None,
    authorization_phrase: str,
) -> dict[str, Any]:
    """Build the production-generation gate report without fabricating inputs."""
    issues: list[str] = []
    blockers: list[dict[str, str]] = []
    phrase_exact_match = authorization_phrase == PRODUCTION_GENERATION_AUTHORIZATION_PHRASE
    if not phrase_exact_match:
        issues.append("PROD-AUTH: authorization phrase does not exactly match")

    smoke_report = _read_json_mapping(
        smoke_execution_report_path,
        "PROD-SMOKE",
        issues,
    )
    if smoke_report is not None:
        smoke_issues = validate_bounded_smoke_execution_report(smoke_report)
        issues.extend(f"PROD-SMOKE: {issue}" for issue in smoke_issues)
        if smoke_report.get("status") != BOUNDED_SMOKE_EXECUTION_PASS_STATUS:
            issues.append("PROD-SMOKE: bounded-smoke execution status is not pass")

    descriptor_rows: list[dict[str, str]] = []
    geometry_descriptor_sha = ""
    if geometry_descriptor_path.exists():
        geometry_descriptor_sha = sha256_file(geometry_descriptor_path)
        if geometry_descriptor_sha.lower() != GEOMETRY_DESCRIPTOR_SHA256.lower():
            issues.append(
                "PROD-EAS-DESCRIPTOR: COMSOL_GEOMETRY_DESCRIPTOR_V1 SHA does not "
                "match the approved descriptor handoff"
            )
        descriptor_rows = read_csv_rows(geometry_descriptor_path)
        issues.extend(
            f"PROD-EAS-DESCRIPTOR: {issue}"
            for issue in validate_geometry_descriptor_rows(descriptor_rows)
        )
    else:
        issues.append(f"PROD-EAS-DESCRIPTOR: missing {geometry_descriptor_path}")

    rank_rows: list[dict[str, str]] = []
    if rank_source_path.exists():
        rank_rows = read_csv_rows(rank_source_path)
    else:
        issues.append(f"PROD-EAS-RANK: missing {rank_source_path}")

    guardrail_rows: list[dict[str, str]] = []
    if guardrail_table_path.exists():
        guardrail_rows = read_csv_rows(guardrail_table_path)
    else:
        issues.append(f"PROD-EAS-GUARDRAIL: missing {guardrail_table_path}")

    prs_candidate_rows: list[dict[str, str]] = []
    prs_candidate_sha = ""
    prs_candidate_issues: list[str] = []
    if position_response_candidate_path is not None:
        if position_response_candidate_path.exists():
            prs_candidate_sha = sha256_file(position_response_candidate_path)
            prs_candidate_rows = read_csv_rows(position_response_candidate_path)
            prs_candidate_issues = validate_position_response_surface_rows(
                prs_candidate_rows,
                production_table=True,
                require_complete_row_arithmetic=True,
            )
            issues.extend(
                f"PROD-PRS-CANDIDATE: {issue}" for issue in prs_candidate_issues
            )
        else:
            missing_issue = f"missing {position_response_candidate_path}"
            prs_candidate_issues.append(missing_issue)
            issues.append(f"PROD-PRS-CANDIDATE: {missing_issue}")
    prs_candidate_ready = (
        position_response_candidate_path is not None
        and position_response_candidate_path.exists()
        and not prs_candidate_issues
    )
    if position_response_candidate_path is None or not prs_candidate_ready:
        blockers.extend(
            _production_position_response_blockers(
                candidate_path=position_response_candidate_path,
                candidate_issue_count=len(prs_candidate_issues),
            )
        )
    eas_blockers = _production_effective_aperture_blockers(
        descriptor_rows=descriptor_rows,
        rank_rows=rank_rows,
        guardrail_rows=guardrail_rows,
    )
    blockers.extend(eas_blockers)

    if issues or not phrase_exact_match or eas_blockers:
        status = PRODUCTION_GENERATION_BLOCKED_STATUS
    elif blockers:
        status = PRODUCTION_GENERATION_PARTIAL_STATUS
    else:
        status = PRODUCTION_GENERATION_PASS_STATUS
    performed = status in {PRODUCTION_GENERATION_PARTIAL_STATUS, PRODUCTION_GENERATION_PASS_STATUS}
    report: dict[str, Any] = {
        "schema_version": "nodi_comsol_next_artifacts_production_generation_gate_v1",
        "status": status,
        "issues": issues,
        "blockers": blockers,
        "gate_role": "production_generation_input_and_policy_gate",
        "allowed_current_action": "evaluate_production_generation_and_write_blockers_or_artifacts",
        "required_authorization_phrase": PRODUCTION_GENERATION_AUTHORIZATION_PHRASE,
        "authorization_phrase_supplied_sha256": hashlib.sha256(
            authorization_phrase.encode("utf-8")
        ).hexdigest(),
        "authorization_phrase_exact_match": phrase_exact_match,
        "production_generation_authorized_by_phrase": phrase_exact_match,
        "production_generation_performed": performed,
        "production_artifacts_generated": [],
        "position_response_surface_status": (
            "ready_to_write_edge_primary_candidate_prs"
            if prs_candidate_ready
            else "blocked_missing_position_response_event_source"
        ),
        "effective_aperture_surrogate_status": "ready_to_write_first_production_eas"
        if status == PRODUCTION_GENERATION_PARTIAL_STATUS
        else (
            "blocked_before_eas_write"
            if eas_blockers or issues or not phrase_exact_match
            else "ready_to_write"
        ),
        "smoke_execution_report_path": str(smoke_execution_report_path),
        "smoke_execution_report_sha256": sha256_file(smoke_execution_report_path)
        if smoke_execution_report_path.exists()
        else "",
        "geometry_descriptor_path": str(geometry_descriptor_path),
        "geometry_descriptor_sha256": geometry_descriptor_sha,
        "rank_source_path": str(rank_source_path),
        "rank_source_sha256": sha256_file(rank_source_path)
        if rank_source_path.exists()
        else "",
        "guardrail_table_path": str(guardrail_table_path),
        "guardrail_table_sha256": sha256_file(guardrail_table_path)
        if guardrail_table_path.exists()
        else "",
        "position_response_candidate_path": str(position_response_candidate_path or ""),
        "position_response_candidate_sha256": prs_candidate_sha,
        "position_response_candidate_row_count": len(prs_candidate_rows),
        "position_response_candidate_validation_issue_count": len(prs_candidate_issues),
        "position_response_candidate_policy": PRS_SOURCE_PRODUCTION_ELIGIBILITY_POLICY
        if position_response_candidate_path is not None
        else "",
        "rank_source_filter_policy": "uniform_weighting_only_for_single_grain",
        "geometry_selector_policy": dict(EAS_DESCRIPTOR_SELECTOR_POLICY),
        "excluded_first_production_eas_modes": ["COMSOL_descriptor_if_available"],
        "effective_aperture_surrogate_production_generated": False,
        "position_response_surface_production_generated": False,
        "nodi_run_performed": False,
        "comsol_run_performed": False,
        "joint_route_class_regenerated": False,
        "full_runner_execution_performed": False,
        "no_comsol_run": True,
        "no_joint_route_class_regeneration": True,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_winner": True,
        "not_true_W_eff": True,
        "not_measured_geometry": True,
        "not_optical_solver_output": True,
        "not_fabrication_release": True,
        "not_P3_solver_conclusion": True,
        "comsol_v4_context": default_comsol_v4_readonly_context(),
        "claim_boundary": "production_generation_gate_no_fabricated_rows",
        "stop_reason": "production_inputs_ready"
        if status == PRODUCTION_GENERATION_PASS_STATUS
        else "prs_source_blocked_after_eas_selector_policy_unblocked"
        if status == PRODUCTION_GENERATION_PARTIAL_STATUS
        else "production_inputs_or_selector_policy_blocked",
    }
    validation_issues = validate_production_generation_report(report)
    if validation_issues:
        report["status"] = PRODUCTION_GENERATION_BLOCKED_STATUS
        report["issues"] = [*issues, *validation_issues]
        report["production_generation_performed"] = False
        report["production_artifacts_generated"] = []
    return report


def validate_production_generation_report(report: Mapping[str, Any]) -> list[str]:
    """Validate production-generation gate boundaries."""
    issues: list[str] = []
    if (
        report.get("schema_version")
        != "nodi_comsol_next_artifacts_production_generation_gate_v1"
    ):
        issues.append("PROD-GATE: schema_version drifted")
    if report.get("status") not in {
        PRODUCTION_GENERATION_BLOCKED_STATUS,
        PRODUCTION_GENERATION_PARTIAL_STATUS,
        PRODUCTION_GENERATION_PASS_STATUS,
    }:
        issues.append("PROD-GATE: invalid status")
    if (
        report.get("allowed_current_action")
        != "evaluate_production_generation_and_write_blockers_or_artifacts"
    ):
        issues.append("PROD-GATE: allowed_current_action drifted")
    v4_context = report.get("comsol_v4_context")
    if not isinstance(v4_context, Mapping):
        issues.append("PROD-GATE: missing COMSOL V4 read-only context")
    else:
        issues.extend(f"PROD-GATE: {issue}" for issue in validate_comsol_v4_readonly_context(v4_context))
    if report.get("required_authorization_phrase") != PRODUCTION_GENERATION_AUTHORIZATION_PHRASE:
        issues.append("PROD-GATE: required authorization phrase drifted")
    if report.get("status") == PRODUCTION_GENERATION_BLOCKED_STATUS:
        if report.get("production_generation_performed") is not False:
            issues.append("PROD-GATE: blocked report cannot perform production generation")
        if report.get("production_artifacts_generated") != []:
            issues.append("PROD-GATE: blocked report cannot list production artifacts")
        blockers = report.get("blockers")
        if not isinstance(blockers, list) or not blockers:
            issues.append("PROD-GATE: blocked report must carry blockers")
    if report.get("status") == PRODUCTION_GENERATION_PARTIAL_STATUS:
        if report.get("production_generation_performed") is not True:
            issues.append("PROD-GATE: partial report must perform bounded production generation")
        if report.get("position_response_surface_production_generated") is not False:
            issues.append("PROD-GATE: partial report cannot generate PRS production")
        if report.get("effective_aperture_surrogate_status") not in {
            "ready_to_write_first_production_eas",
            "production_artifact_written",
        }:
            issues.append("PROD-GATE: partial report EAS status drifted")
        blockers = report.get("blockers")
        if not isinstance(blockers, list) or not blockers:
            issues.append("PROD-GATE: partial report must retain PRS blocker")
    if report.get("status") == PRODUCTION_GENERATION_PASS_STATUS:
        if report.get("production_generation_performed") is not True:
            issues.append("PROD-GATE: pass report must perform production generation")
        if report.get("position_response_surface_status") not in {
            "ready_to_write_edge_primary_candidate_prs",
            "production_artifact_written",
        }:
            issues.append("PROD-GATE: pass report PRS status drifted")
        if report.get("effective_aperture_surrogate_status") not in {
            "ready_to_write",
            "production_artifact_written",
        }:
            issues.append("PROD-GATE: pass report EAS status drifted")
        artifacts = report.get("production_artifacts_generated")
        if artifacts:
            if report.get("position_response_surface_production_generated") is not True:
                issues.append("PROD-GATE: written pass report must generate PRS production")
            if report.get("effective_aperture_surrogate_production_generated") is not True:
                issues.append("PROD-GATE: written pass report must generate EAS production")
        blockers = report.get("blockers")
        if blockers:
            issues.append("PROD-GATE: pass report cannot retain blockers")
    for field in _PRODUCTION_GENERATION_FALSE_FIELDS:
        if report.get(field) is not False:
            issues.append(f"PROD-GATE: {field} must remain false")
    for field in _PRODUCTION_GENERATION_TRUE_FIELDS:
        if report.get(field) is not True:
            issues.append(f"PROD-GATE: {field} must remain true")
    return issues


def write_production_generation_bundle(
    *,
    smoke_execution_report_path: Path,
    geometry_descriptor_path: Path,
    rank_source_path: Path,
    guardrail_table_path: Path,
    position_response_candidate_path: Path | None = None,
    authorization_phrase: str,
    output_dir: Path,
) -> dict[str, Any]:
    """Write the production-generation gate bundle."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_production_generation_report(
        smoke_execution_report_path=smoke_execution_report_path,
        geometry_descriptor_path=geometry_descriptor_path,
        rank_source_path=rank_source_path,
        guardrail_table_path=guardrail_table_path,
        position_response_candidate_path=position_response_candidate_path,
        authorization_phrase=authorization_phrase,
    )

    if report["status"] in {
        PRODUCTION_GENERATION_PARTIAL_STATUS,
        PRODUCTION_GENERATION_PASS_STATUS,
    }:
        try:
            eas_rows = build_effective_aperture_first_production_rows(
                geometry_descriptor_path=geometry_descriptor_path,
                rank_source_path=rank_source_path,
                guardrail_table_path=guardrail_table_path,
            )
        except ContractValidationError as exc:
            report["status"] = PRODUCTION_GENERATION_BLOCKED_STATUS
            report["issues"] = [
                *report["issues"],
                *(f"PROD-EAS-WRITE: {issue}" for issue in exc.issues),
            ]
            report["blockers"] = [
                *report["blockers"],
                {
                    "artifact": APERTURE_SURROGATE_ARTIFACT,
                    "blocker_id": "EAS-PROD-B04",
                    "status": "blocked_eas_production_row_validation_failed",
                    "required_input_or_policy": (
                        "first-production EAS rows must validate against Report 156 "
                        "surrogate-only contract and COMSOL selector policy"
                    ),
                    "current_evidence": "; ".join(exc.issues),
                    "unblock_action": "repair EAS production row builder before writing CSV",
                    "claim_boundary": EAS_CLAIM_BOUNDARY,
                },
            ]
            report["production_generation_performed"] = False
            report["production_artifacts_generated"] = []
            report["effective_aperture_surrogate_status"] = "blocked_before_eas_write"
            report["effective_aperture_surrogate_production_generated"] = False
        else:
            eas_path = output_dir / EAS_PRODUCTION_FILENAME
            write_csv_rows(eas_path, eas_rows)
            selector_metadata = _build_eas_selector_policy_metadata(
                eas_rows=eas_rows,
                eas_path=eas_path,
                geometry_descriptor_path=geometry_descriptor_path,
                rank_source_path=rank_source_path,
                guardrail_table_path=guardrail_table_path,
            )
            selector_path = output_dir / EAS_SELECTOR_POLICY_METADATA_FILENAME
            write_json_atomic(selector_path, selector_metadata, sort_keys=True)
            eas_sha = sha256_file(eas_path)
            selector_sha = sha256_file(selector_path)
            report["effective_aperture_surrogate_status"] = "production_artifact_written"
            report["effective_aperture_surrogate_production_generated"] = True
            report["effective_aperture_surrogate_production_row_count"] = len(eas_rows)
            report["effective_aperture_surrogate_production_modes"] = list(
                EAS_FIRST_PRODUCTION_MODES
            )
            report["effective_aperture_surrogate_production_csv"] = str(eas_path)
            report["effective_aperture_surrogate_production_csv_sha256"] = eas_sha
            report["effective_aperture_surrogate_selector_policy_metadata"] = str(
                selector_path
            )
            report[
                "effective_aperture_surrogate_selector_policy_metadata_sha256"
            ] = selector_sha
            report["production_artifacts_generated"] = [
                {
                    "artifact": APERTURE_SURROGATE_ARTIFACT,
                    "path": str(eas_path),
                    "sha256": eas_sha,
                    "rows": len(eas_rows),
                    "claim_boundary": EAS_CLAIM_BOUNDARY,
                },
                {
                    "artifact": "NODI_EFFECTIVE_APERTURE_SURROGATE_SELECTOR_POLICY",
                    "path": str(selector_path),
                    "sha256": selector_sha,
                    "rows": 1,
                    "claim_boundary": EAS_CLAIM_BOUNDARY,
                },
            ]
            if report["status"] == PRODUCTION_GENERATION_PASS_STATUS:
                if position_response_candidate_path is None:
                    raise ContractValidationError(
                        "NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION",
                        ["PROD-PRS-WRITE: pass status missing PRS candidate path"],
                    )
                prs_rows = read_csv_rows(position_response_candidate_path)
                prs_issues = validate_position_response_surface_rows(
                    prs_rows,
                    production_table=True,
                    require_complete_row_arithmetic=True,
                )
                if prs_issues:
                    raise ContractValidationError(
                        "NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION",
                        [f"PROD-PRS-WRITE: {issue}" for issue in prs_issues],
                    )
                prs_path = output_dir / PRS_PRODUCTION_FILENAME
                write_csv_rows(prs_path, prs_rows)
                prs_sha = sha256_file(prs_path)
                report["position_response_surface_status"] = "production_artifact_written"
                report["position_response_surface_production_generated"] = True
                report["position_response_surface_production_row_count"] = len(prs_rows)
                report["position_response_surface_production_csv"] = str(prs_path)
                report["position_response_surface_production_csv_sha256"] = prs_sha
                report["production_artifacts_generated"].append(
                    {
                        "artifact": POSITION_RESPONSE_ARTIFACT,
                        "path": str(prs_path),
                        "sha256": prs_sha,
                        "rows": len(prs_rows),
                        "claim_boundary": PRS_CLAIM_BOUNDARY,
                    }
                )

    validation_issues = validate_production_generation_report(report)
    if validation_issues:
        raise ContractValidationError("NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION", validation_issues)

    blocker_rows = report["blockers"] or [
        {
            "artifact": "none",
            "blocker_id": "none",
            "status": "not_blocked",
            "required_input_or_policy": "",
            "current_evidence": "",
            "unblock_action": "",
            "claim_boundary": report["claim_boundary"],
        }
    ]
    blocker_path = output_dir / NEXT_ARTIFACTS_PRODUCTION_GENERATION_BLOCKERS_FILENAME
    write_csv_rows(blocker_path, blocker_rows)
    issue_rows = [
        {"issue_index": index, "issue": issue}
        for index, issue in enumerate(report["issues"], start=1)
    ] or [{"issue_index": "", "issue": "none"}]
    issue_path = output_dir / NEXT_ARTIFACTS_PRODUCTION_GENERATION_ISSUES_FILENAME
    write_csv_rows(issue_path, issue_rows)

    report["blocker_csv"] = str(blocker_path)
    report["blocker_csv_sha256"] = sha256_file(blocker_path)
    report["issue_csv"] = str(issue_path)
    report["issue_csv_sha256"] = sha256_file(issue_path)
    report_path = output_dir / NEXT_ARTIFACTS_PRODUCTION_GENERATION_REPORT_FILENAME
    write_json_atomic(report_path, report, sort_keys=True)
    report["report_path"] = str(report_path)
    report["report_sha256"] = sha256_file(report_path)
    return report


def _build_eas_selector_policy_metadata(
    *,
    eas_rows: Sequence[Mapping[str, Any]],
    eas_path: Path,
    geometry_descriptor_path: Path,
    rank_source_path: Path,
    guardrail_table_path: Path,
) -> dict[str, Any]:
    """Record the first-production EAS descriptor selector and source hashes."""
    return {
        "schema_version": "nodi_effective_aperture_surrogate_selector_policy_v1",
        "selector_role": "first_production_eas_single_descriptor_per_width_depth",
        "selector_policy": dict(EAS_DESCRIPTOR_SELECTOR_POLICY),
        "selector_policy_enforcement": "exactly_one_descriptor_row_per_W_D_no_fallback",
        "first_production_modes": list(EAS_FIRST_PRODUCTION_MODES),
        "excluded_first_production_modes": ["COMSOL_descriptor_if_available"],
        "production_artifact_path": str(eas_path),
        "production_artifact_rows": len(eas_rows),
        "geometry_descriptor_path": str(geometry_descriptor_path),
        "geometry_descriptor_sha256": sha256_file(geometry_descriptor_path),
        "rank_source_path": str(rank_source_path),
        "rank_source_sha256": sha256_file(rank_source_path),
        "guardrail_table_path": str(guardrail_table_path),
        "guardrail_table_sha256": sha256_file(guardrail_table_path),
        "rank_source_filter_policy": "uniform_weighting_only_for_single_grain",
        "claim_boundary": EAS_CLAIM_BOUNDARY,
        "descriptor_claim_boundary": GEOMETRY_DESCRIPTOR_CLAIM_BOUNDARY,
        "not_true_W_eff": True,
        "not_measured_geometry": True,
        "not_optical_solver_output": True,
        "not_fabrication_release": True,
        "not_yield": True,
        "not_winner": True,
        "no_comsol_run": True,
        "no_joint_route_class_regeneration": True,
    }


def default_position_response_source_candidate_paths(project_root: Path) -> list[Path]:
    """Return known local candidates worth checking for PRS source availability."""
    candidates = sorted(
        project_root.glob(
            "results/exhaustive_ev_gold_fullgrid_shared_dual_10000e_seed*_16worker_20260518/"
            "seed_*_*_raw_rows.csv"
        )
    )
    rank_source = (
        project_root
        / "exports/nodi_comsol_handoff_v1/NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv"
    )
    if rank_source.exists():
        candidates.append(rank_source)
    return candidates


def build_position_response_source_preflight_report(
    *,
    candidate_paths: Sequence[Path],
) -> dict[str, Any]:
    """Build a PRS source-availability preflight report without producing PRS rows."""
    candidate_rows = [
        _evaluate_position_response_source_candidate(path) for path in candidate_paths
    ]
    valid_candidates = [
        row
        for row in candidate_rows
        if row["candidate_status"] == PRS_SOURCE_AVAILABLE_CANDIDATE_STATUS
    ]
    blockers: list[dict[str, Any]] = []
    if not valid_candidates:
        blockers.append(
            {
                "artifact": POSITION_RESPONSE_ARTIFACT,
                "blocker_id": "PRS-SOURCE-B01",
                "status": "blocked_no_real_bin_conditioned_source",
                "required_source_grain": PRS_SOURCE_MINIMUM_GRAIN,
                "current_evidence": (
                    "no candidate source contains the minimum route/diameter/view/"
                    "seed/distribution-bin grain with response counts"
                ),
                "unblock_action": (
                    "provide or regenerate a real bin-conditioned source; smoke, "
                    "bounded-smoke, PLAN_ONLY, route-rank, and route-level raw rows "
                    "must not be promoted"
                ),
                "claim_boundary": PRS_CLAIM_BOUNDARY,
            }
        )
    status = (
        PRS_SOURCE_PREFLIGHT_PASS_STATUS
        if valid_candidates
        else PRS_SOURCE_PREFLIGHT_BLOCKED_STATUS
    )
    report: dict[str, Any] = {
        "schema_version": "nodi_position_response_source_availability_preflight_v1",
        "status": status,
        "artifact": POSITION_RESPONSE_ARTIFACT,
        "gate_role": "source_availability_preflight_only",
        "allowed_current_action": "evaluate_candidate_sources_no_prs_generation",
        "minimum_required_source_grain": PRS_SOURCE_MINIMUM_GRAIN,
        "candidate_count": len(candidate_rows),
        "source_available_candidate_count": len(valid_candidates),
        "source_available_candidates": [
            row["candidate_path"] for row in valid_candidates
        ],
        "candidate_rows": candidate_rows,
        "blockers": blockers,
        "issues": [],
        "position_response_surface_production_generated": False,
        "production_generation_performed": False,
        "full_runner_execution_performed": False,
        "nodi_run_performed": False,
        "comsol_run_performed": False,
        "joint_route_class_regenerated": False,
        "no_prs_production_artifact": True,
        "no_comsol_run": True,
        "no_joint_route_class_regeneration": True,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_winner": True,
        "not_detection_probability": True,
        "claim_boundary": PRS_CLAIM_BOUNDARY,
        "stop_reason": "real_prs_source_available_preflight_only"
        if valid_candidates
        else "real_prs_source_not_available",
    }
    validation_issues = validate_position_response_source_preflight_report(report)
    if validation_issues:
        report["status"] = PRS_SOURCE_PREFLIGHT_BLOCKED_STATUS
        report["issues"] = validation_issues
    return report


def write_position_response_source_preflight_bundle(
    *,
    candidate_paths: Sequence[Path],
    output_dir: Path,
) -> dict[str, Any]:
    """Write PRS source-availability preflight sidecars without production rows."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_position_response_source_preflight_report(
        candidate_paths=candidate_paths
    )
    candidate_path = output_dir / PRS_SOURCE_PREFLIGHT_CANDIDATES_FILENAME
    write_csv_rows(candidate_path, report["candidate_rows"])
    blocker_rows = report["blockers"] or [
        {
            "artifact": "none",
            "blocker_id": "none",
            "status": "not_blocked",
            "required_source_grain": PRS_SOURCE_MINIMUM_GRAIN,
            "current_evidence": "",
            "unblock_action": "",
            "claim_boundary": PRS_CLAIM_BOUNDARY,
        }
    ]
    blocker_path = output_dir / PRS_SOURCE_PREFLIGHT_BLOCKERS_FILENAME
    write_csv_rows(blocker_path, blocker_rows)
    issue_rows = [
        {"issue_index": index, "issue": issue}
        for index, issue in enumerate(report["issues"], start=1)
    ] or [{"issue_index": "", "issue": "none"}]
    issue_path = output_dir / PRS_SOURCE_PREFLIGHT_ISSUES_FILENAME
    write_csv_rows(issue_path, issue_rows)
    report["candidate_csv"] = str(candidate_path)
    report["candidate_csv_sha256"] = sha256_file(candidate_path)
    report["blocker_csv"] = str(blocker_path)
    report["blocker_csv_sha256"] = sha256_file(blocker_path)
    report["issue_csv"] = str(issue_path)
    report["issue_csv_sha256"] = sha256_file(issue_path)
    report_path = output_dir / PRS_SOURCE_PREFLIGHT_REPORT_FILENAME
    write_json_atomic(report_path, report, sort_keys=True)
    report["report_path"] = str(report_path)
    report["report_sha256"] = sha256_file(report_path)
    return report


def validate_position_response_source_preflight_report(
    report: Mapping[str, Any],
) -> list[str]:
    """Validate PRS source-availability preflight boundaries."""
    issues: list[str] = []
    if (
        report.get("schema_version")
        != "nodi_position_response_source_availability_preflight_v1"
    ):
        issues.append("PRS-SOURCE: schema_version drifted")
    if report.get("status") not in {
        PRS_SOURCE_PREFLIGHT_BLOCKED_STATUS,
        PRS_SOURCE_PREFLIGHT_PASS_STATUS,
    }:
        issues.append("PRS-SOURCE: invalid status")
    if report.get("artifact") != POSITION_RESPONSE_ARTIFACT:
        issues.append("PRS-SOURCE: artifact drifted")
    if report.get("minimum_required_source_grain") != PRS_SOURCE_MINIMUM_GRAIN:
        issues.append("PRS-SOURCE: minimum source grain drifted")
    candidate_rows = report.get("candidate_rows")
    if not isinstance(candidate_rows, list):
        issues.append("PRS-SOURCE: candidate_rows must be a list")
    if report.get("status") == PRS_SOURCE_PREFLIGHT_PASS_STATUS:
        if not report.get("source_available_candidates"):
            issues.append("PRS-SOURCE: pass status lacks source_available_candidates")
    if report.get("status") == PRS_SOURCE_PREFLIGHT_BLOCKED_STATUS:
        blockers = report.get("blockers")
        if not isinstance(blockers, list) or not blockers:
            issues.append("PRS-SOURCE: blocked status must carry a blocker")
    for field in (
        "position_response_surface_production_generated",
        "production_generation_performed",
        "full_runner_execution_performed",
        "nodi_run_performed",
        "comsol_run_performed",
        "joint_route_class_regenerated",
    ):
        if report.get(field) is not False:
            issues.append(f"PRS-SOURCE: {field} must remain false")
    for field in (
        "no_prs_production_artifact",
        "no_comsol_run",
        "no_joint_route_class_regeneration",
        "not_qch_weighted",
        "not_yield",
        "not_winner",
        "not_detection_probability",
    ):
        if report.get(field) is not True:
            issues.append(f"PRS-SOURCE: {field} must remain true")
    return issues


def build_position_response_source_sufficiency_report(
    *,
    candidate_paths: Sequence[Path],
) -> dict[str, Any]:
    """Evaluate numeric PRS source sufficiency without producing PRS rows."""
    candidate_rows: list[dict[str, str]] = []
    job_plan_rows: list[dict[str, str]] = []
    for path in candidate_paths:
        candidate_row, candidate_job_rows = _evaluate_prs_source_sufficiency_candidate(path)
        candidate_rows.append(candidate_row)
        job_plan_rows.extend(candidate_job_rows)

    valid_candidates = [
        row
        for row in candidate_rows
        if row["candidate_status"] == PRS_SOURCE_NUMERIC_SUFFICIENT_CANDIDATE_STATUS
    ]
    blockers: list[dict[str, str]] = []
    if not valid_candidates:
        blockers.append(
            {
                "artifact": POSITION_RESPONSE_ARTIFACT,
                "blocker_id": "PRS-SUFF-B01",
                "status": "blocked_no_numeric_sufficient_prs_source",
                "required_policy": PRS_SOURCE_NUMERIC_SUFFICIENCY_POLICY,
                "current_evidence": (
                    "candidate bin-conditioned sources are missing, invalid, "
                    "non-production-scope, or contain sparse/empty bins"
                ),
                "unblock_action": (
                    "regenerate real NODI event/bin sources until every source row "
                    f"has bin_sample_status=adequate, decision_use_allowed=true, "
                    f"sparse_bin_flag=false, and n_events_bin>="
                    f"{PRS_MIN_EVENTS_PER_BIN_FOR_PRODUCTION}"
                ),
                "claim_boundary": PRS_CLAIM_BOUNDARY,
            }
        )

    status = (
        PRS_SOURCE_SUFFICIENCY_PASS_STATUS
        if valid_candidates
        else PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS
    )
    report: dict[str, Any] = {
        "schema_version": "nodi_position_response_source_numeric_sufficiency_preflight_v1",
        "status": status,
        "artifact": POSITION_RESPONSE_ARTIFACT,
        "gate_role": "source_numeric_sufficiency_preflight_only",
        "allowed_current_action": "evaluate_candidate_source_numeric_sufficiency_no_prs_generation",
        "minimum_required_source_grain": PRS_SOURCE_MINIMUM_GRAIN,
        "numeric_sufficiency_policy": PRS_SOURCE_NUMERIC_SUFFICIENCY_POLICY,
        "min_events_per_bin_for_production": PRS_MIN_EVENTS_PER_BIN_FOR_PRODUCTION,
        "rows_per_route_diameter_view_seed": ROWS_PER_ROUTE_DIAMETER_VIEW,
        "xz_base_bins_per_route_diameter_view_seed": XZ_BASE_BIN_COUNT,
        "edge_base_bins_per_route_diameter_view_seed": EDGE_BASE_BIN_COUNT,
        "candidate_count": len(candidate_rows),
        "numeric_sufficient_candidate_count": len(valid_candidates),
        "numeric_sufficient_candidates": [
            row["candidate_path"] for row in valid_candidates
        ],
        "candidate_rows": candidate_rows,
        "blockers": blockers,
        "job_plan_rows": job_plan_rows,
        "issues": [],
        "position_response_surface_production_generated": False,
        "production_generation_performed": False,
        "full_runner_execution_performed": False,
        "nodi_run_performed": False,
        "comsol_run_performed": False,
        "joint_route_class_regenerated": False,
        "no_prs_production_artifact": True,
        "no_comsol_run": True,
        "no_joint_route_class_regeneration": True,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_winner": True,
        "not_detection_probability": True,
        "not_true_W_eff": True,
        "not_measured_geometry": True,
        "not_optical_solver_output": True,
        "not_fabrication_release": True,
        "not_P3_solver_conclusion": True,
        "job_plan_execution_authorized": False,
        "job_plan_shortfall_fields_are_diagnostic_not_event_counts": True,
        "claim_boundary": PRS_CLAIM_BOUNDARY,
        "stop_reason": "prs_source_numeric_sufficiency_preflight_only"
        if valid_candidates
        else "prs_source_numeric_sufficiency_blocked",
    }
    validation_issues = validate_position_response_source_sufficiency_report(report)
    if validation_issues:
        report["status"] = PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS
        report["issues"] = validation_issues
    return report


def write_position_response_source_sufficiency_bundle(
    *,
    candidate_paths: Sequence[Path],
    output_dir: Path,
) -> dict[str, Any]:
    """Write PRS source numeric-sufficiency sidecars without production rows."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_position_response_source_sufficiency_report(
        candidate_paths=candidate_paths
    )
    candidate_path = output_dir / PRS_SOURCE_SUFFICIENCY_CANDIDATES_FILENAME
    write_csv_rows(candidate_path, report["candidate_rows"])
    blocker_rows = report["blockers"] or [
        {
            "artifact": "none",
            "blocker_id": "none",
            "status": "not_blocked",
            "required_policy": PRS_SOURCE_NUMERIC_SUFFICIENCY_POLICY,
            "current_evidence": "",
            "unblock_action": "",
            "claim_boundary": PRS_CLAIM_BOUNDARY,
        }
    ]
    blocker_path = output_dir / PRS_SOURCE_SUFFICIENCY_BLOCKERS_FILENAME
    write_csv_rows(blocker_path, blocker_rows)
    job_plan_rows = report["job_plan_rows"] or [
        {
            "candidate_path": "none",
            "candidate_sha256": "",
            "route_id_nodi": "",
            "diameter_nm": "",
            "NODI_view": "",
            "seed": "",
            "current_total_events_seed": "",
            "minimum_n_events_bin": "",
            "insufficient_row_count": "0",
            "summed_bin_row_shortfall_not_event_count": "",
            "min_events_per_bin_for_production": str(PRS_MIN_EVENTS_PER_BIN_FOR_PRODUCTION),
            "recommended_min_total_events_floor": str(
                PRS_MIN_EVENTS_PER_BIN_FOR_PRODUCTION * XZ_BASE_BIN_COUNT
            ),
            "recommended_min_total_events_floor_basis": (
                "xz_441_bins_times_min_100_per_bin_floor_not_requested_n_events"
            ),
            "recommended_action": "none",
            "execution_authorized": "false",
            "shortfall_fields_are_diagnostic_not_event_counts": "true",
            "preflight_only": "true",
            "production_prs_generated": "false",
            "claim_boundary": PRS_CLAIM_BOUNDARY,
        }
    ]
    job_plan_path = output_dir / PRS_SOURCE_SUFFICIENCY_JOB_PLAN_FILENAME
    write_csv_rows(job_plan_path, job_plan_rows)
    issue_rows = [
        {"issue_index": index, "issue": issue}
        for index, issue in enumerate(report["issues"], start=1)
    ] or [{"issue_index": "", "issue": "none"}]
    issue_path = output_dir / PRS_SOURCE_SUFFICIENCY_ISSUES_FILENAME
    write_csv_rows(issue_path, issue_rows)
    report["candidate_csv"] = str(candidate_path)
    report["candidate_csv_sha256"] = sha256_file(candidate_path)
    report["blocker_csv"] = str(blocker_path)
    report["blocker_csv_sha256"] = sha256_file(blocker_path)
    report["job_plan_csv"] = str(job_plan_path)
    report["job_plan_csv_sha256"] = sha256_file(job_plan_path)
    report["issue_csv"] = str(issue_path)
    report["issue_csv_sha256"] = sha256_file(issue_path)
    report_path = output_dir / PRS_SOURCE_SUFFICIENCY_REPORT_FILENAME
    write_json_atomic(report_path, report, sort_keys=True)
    report["report_path"] = str(report_path)
    report["report_sha256"] = sha256_file(report_path)
    return report


def build_position_response_source_production_eligibility_report(
    *,
    candidate_paths: Sequence[Path],
) -> dict[str, Any]:
    """Evaluate edge-primary PRS source eligibility without producing PRS rows."""
    candidate_rows: list[dict[str, str]] = []
    group_rows: list[dict[str, str]] = []
    for path in candidate_paths:
        candidate_row, candidate_group_rows = (
            _evaluate_prs_source_production_eligibility_candidate(path)
        )
        candidate_rows.append(candidate_row)
        group_rows.extend(candidate_group_rows)

    eligible_candidates = [
        row
        for row in candidate_rows
        if row["candidate_status"] == PRS_SOURCE_PRODUCTION_ELIGIBLE_CANDIDATE_STATUS
    ]
    blockers: list[dict[str, str]] = []
    if not eligible_candidates:
        blockers.append(
            {
                "artifact": POSITION_RESPONSE_ARTIFACT,
                "blocker_id": "PRS-ELIG-B01",
                "status": "blocked_no_edge_primary_eligible_prs_source",
                "required_policy": PRS_SOURCE_PRODUCTION_ELIGIBILITY_POLICY,
                "current_evidence": (
                    "no candidate source has production scope, valid 467-row "
                    "route/diameter/view/seed groups, and adequate edge_norm_1d "
                    "primary rows while keeping xz_norm_2d diagnostic-only"
                ),
                "unblock_action": (
                    "repair or regenerate the bin-conditioned source; do not "
                    "promote xz_norm_2d sparse/empty rows to primary response bins"
                ),
                "claim_boundary": PRS_CLAIM_BOUNDARY,
            }
        )

    status = (
        PRS_SOURCE_PRODUCTION_ELIGIBILITY_PASS_STATUS
        if eligible_candidates
        else PRS_SOURCE_PRODUCTION_ELIGIBILITY_BLOCKED_STATUS
    )
    report: dict[str, Any] = {
        "schema_version": "nodi_position_response_source_production_eligibility_preflight_v1",
        "status": status,
        "artifact": POSITION_RESPONSE_ARTIFACT,
        "gate_role": "source_production_eligibility_preflight_only",
        "allowed_current_action": "evaluate_edge_primary_source_eligibility_no_prs_generation",
        "minimum_required_source_grain": PRS_SOURCE_MINIMUM_GRAIN,
        "production_eligibility_policy": PRS_SOURCE_PRODUCTION_ELIGIBILITY_POLICY,
        "strict_numeric_sufficiency_policy_retained": PRS_SOURCE_NUMERIC_SUFFICIENCY_POLICY,
        "edge_primary_distribution": "edge_norm_1d",
        "xz_distribution_role": "xz_norm_2d_diagnostic_only_no_auto_promotion",
        "min_events_per_edge_primary_bin": PRS_MIN_EVENTS_PER_BIN_FOR_PRODUCTION,
        "rows_per_route_diameter_view_seed": ROWS_PER_ROUTE_DIAMETER_VIEW,
        "edge_rows_per_route_diameter_view_seed": (
            EDGE_BASE_BIN_COUNT + SPECIAL_AGGREGATE_COUNT_PER_DISTRIBUTION
        ),
        "xz_rows_per_route_diameter_view_seed": (
            XZ_BASE_BIN_COUNT + SPECIAL_AGGREGATE_COUNT_PER_DISTRIBUTION
        ),
        "candidate_count": len(candidate_rows),
        "eligible_candidate_count": len(eligible_candidates),
        "eligible_candidates": [
            row["candidate_path"] for row in eligible_candidates
        ],
        "candidate_rows": candidate_rows,
        "group_rows": group_rows,
        "blockers": blockers,
        "issues": [],
        "position_response_surface_production_generated": False,
        "production_generation_performed": False,
        "full_runner_execution_performed": False,
        "nodi_run_performed": False,
        "comsol_run_performed": False,
        "joint_route_class_regenerated": False,
        "no_prs_production_artifact": True,
        "no_comsol_run": True,
        "no_joint_route_class_regeneration": True,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_winner": True,
        "not_detection_probability": True,
        "not_true_W_eff": True,
        "not_measured_geometry": True,
        "not_optical_solver_output": True,
        "not_fabrication_release": True,
        "not_P3_solver_conclusion": True,
        "xz_sparse_rows_are_diagnostic_not_blocking_edge_primary": True,
        "xz_primary_promotion_authorized": False,
        "claim_boundary": PRS_CLAIM_BOUNDARY,
        "stop_reason": "edge_primary_source_eligible_prs_generation_not_performed"
        if eligible_candidates
        else "edge_primary_source_eligibility_blocked",
    }
    validation_issues = validate_position_response_source_production_eligibility_report(
        report
    )
    if validation_issues:
        report["status"] = PRS_SOURCE_PRODUCTION_ELIGIBILITY_BLOCKED_STATUS
        report["issues"] = validation_issues
    return report


def write_position_response_source_production_eligibility_bundle(
    *,
    candidate_paths: Sequence[Path],
    output_dir: Path,
) -> dict[str, Any]:
    """Write PRS source production-eligibility sidecars without PRS production."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report = build_position_response_source_production_eligibility_report(
        candidate_paths=candidate_paths
    )
    candidate_path = output_dir / PRS_SOURCE_PRODUCTION_ELIGIBILITY_CANDIDATES_FILENAME
    write_csv_rows(candidate_path, report["candidate_rows"])
    group_path = output_dir / PRS_SOURCE_PRODUCTION_ELIGIBILITY_GROUPS_FILENAME
    write_csv_rows(
        group_path,
        report["group_rows"]
        or [
            {
                "candidate_path": "none",
                "candidate_sha256": "",
                "route_id_nodi": "",
                "diameter_nm": "",
                "NODI_view": "",
                "seed": "",
                "group_status": "no_groups",
                "issue_summary": "",
                "claim_boundary": PRS_CLAIM_BOUNDARY,
            }
        ],
    )
    blocker_rows = report["blockers"] or [
        {
            "artifact": "none",
            "blocker_id": "none",
            "status": "not_blocked",
            "required_policy": PRS_SOURCE_PRODUCTION_ELIGIBILITY_POLICY,
            "current_evidence": "",
            "unblock_action": "",
            "claim_boundary": PRS_CLAIM_BOUNDARY,
        }
    ]
    blocker_path = output_dir / PRS_SOURCE_PRODUCTION_ELIGIBILITY_BLOCKERS_FILENAME
    write_csv_rows(blocker_path, blocker_rows)
    issue_rows = [
        {"issue_index": index, "issue": issue}
        for index, issue in enumerate(report["issues"], start=1)
    ] or [{"issue_index": "", "issue": "none"}]
    issue_path = output_dir / PRS_SOURCE_PRODUCTION_ELIGIBILITY_ISSUES_FILENAME
    write_csv_rows(issue_path, issue_rows)
    report["candidate_csv"] = str(candidate_path)
    report["candidate_csv_sha256"] = sha256_file(candidate_path)
    report["group_csv"] = str(group_path)
    report["group_csv_sha256"] = sha256_file(group_path)
    report["blocker_csv"] = str(blocker_path)
    report["blocker_csv_sha256"] = sha256_file(blocker_path)
    report["issue_csv"] = str(issue_path)
    report["issue_csv_sha256"] = sha256_file(issue_path)
    report_path = output_dir / PRS_SOURCE_PRODUCTION_ELIGIBILITY_REPORT_FILENAME
    write_json_atomic(report_path, report, sort_keys=True)
    report["report_path"] = str(report_path)
    report["report_sha256"] = sha256_file(report_path)
    return report


def validate_position_response_source_production_eligibility_report(
    report: Mapping[str, Any],
) -> list[str]:
    """Validate PRS edge-primary source eligibility boundaries."""
    issues: list[str] = []
    if (
        report.get("schema_version")
        != "nodi_position_response_source_production_eligibility_preflight_v1"
    ):
        issues.append("PRS-ELIG: schema_version drifted")
    if report.get("status") not in {
        PRS_SOURCE_PRODUCTION_ELIGIBILITY_BLOCKED_STATUS,
        PRS_SOURCE_PRODUCTION_ELIGIBILITY_PASS_STATUS,
    }:
        issues.append("PRS-ELIG: invalid status")
    if report.get("artifact") != POSITION_RESPONSE_ARTIFACT:
        issues.append("PRS-ELIG: artifact drifted")
    if report.get("minimum_required_source_grain") != PRS_SOURCE_MINIMUM_GRAIN:
        issues.append("PRS-ELIG: minimum source grain drifted")
    if (
        report.get("production_eligibility_policy")
        != PRS_SOURCE_PRODUCTION_ELIGIBILITY_POLICY
    ):
        issues.append("PRS-ELIG: production eligibility policy drifted")
    if (
        report.get("strict_numeric_sufficiency_policy_retained")
        != PRS_SOURCE_NUMERIC_SUFFICIENCY_POLICY
    ):
        issues.append("PRS-ELIG: strict numeric sufficiency policy not retained")
    if report.get("xz_primary_promotion_authorized") is not False:
        issues.append("PRS-ELIG: xz_primary_promotion_authorized must remain false")
    candidate_rows = report.get("candidate_rows")
    if not isinstance(candidate_rows, list):
        issues.append("PRS-ELIG: candidate_rows must be a list")
    group_rows = report.get("group_rows")
    if not isinstance(group_rows, list):
        issues.append("PRS-ELIG: group_rows must be a list")
    if report.get("status") == PRS_SOURCE_PRODUCTION_ELIGIBILITY_PASS_STATUS:
        if not report.get("eligible_candidates"):
            issues.append("PRS-ELIG: pass status lacks eligible_candidates")
        if isinstance(group_rows, list):
            bad_groups = [
                row
                for row in group_rows
                if _value(row, "group_status")
                != "edge_primary_group_eligible_xz_diagnostic_only"
            ]
            if bad_groups:
                issues.append("PRS-ELIG: pass status contains ineligible group rows")
    if report.get("status") == PRS_SOURCE_PRODUCTION_ELIGIBILITY_BLOCKED_STATUS:
        blockers = report.get("blockers")
        if not isinstance(blockers, list) or not blockers:
            issues.append("PRS-ELIG: blocked status must carry a blocker")
    for field in (
        "position_response_surface_production_generated",
        "production_generation_performed",
        "full_runner_execution_performed",
        "nodi_run_performed",
        "comsol_run_performed",
        "joint_route_class_regenerated",
    ):
        if report.get(field) is not False:
            issues.append(f"PRS-ELIG: {field} must remain false")
    for field in (
        "no_prs_production_artifact",
        "no_comsol_run",
        "no_joint_route_class_regeneration",
        "not_qch_weighted",
        "not_yield",
        "not_winner",
        "not_detection_probability",
        "not_true_W_eff",
        "not_measured_geometry",
        "not_optical_solver_output",
        "not_fabrication_release",
        "not_P3_solver_conclusion",
        "xz_sparse_rows_are_diagnostic_not_blocking_edge_primary",
    ):
        if report.get(field) is not True:
            issues.append(f"PRS-ELIG: {field} must remain true")
    return issues


def build_position_response_edge_primary_candidate_rows(
    *,
    source_path: Path,
) -> list[dict[str, Any]]:
    """Build production-shaped PRS candidate rows from an edge-primary source."""
    eligibility_report = build_position_response_source_production_eligibility_report(
        candidate_paths=[source_path]
    )
    if eligibility_report["status"] != PRS_SOURCE_PRODUCTION_ELIGIBILITY_PASS_STATUS:
        raise ContractValidationError(
            POSITION_RESPONSE_ARTIFACT,
            [
                "PRS-EDGE-CAND: source failed edge-primary production eligibility "
                f"with status={eligibility_report['status']}"
            ],
        )

    source_rows = read_csv_rows(source_path)
    source_sha = sha256_file(source_path)
    grouped: dict[tuple[str, str, str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in source_rows:
        grouped[
            (
                _value(row, "route_id_nodi"),
                _value(row, "diameter_nm"),
                _value(row, "NODI_view"),
                _value(row, "distribution_type"),
                _value(row, "bin_id"),
            )
        ].append(row)

    candidate_rows = [
        _position_response_edge_primary_candidate_row(
            source_path=source_path,
            source_sha=source_sha,
            group_rows=group_rows,
        )
        for _, group_rows in sorted(grouped.items())
    ]
    issues = validate_position_response_surface_rows(
        candidate_rows,
        production_table=True,
        require_complete_row_arithmetic=True,
    )
    if issues:
        raise ContractValidationError(POSITION_RESPONSE_ARTIFACT, issues)
    return candidate_rows


def write_position_response_edge_primary_candidate_bundle(
    *,
    source_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Write production-shaped edge-primary PRS candidate rows without promotion."""
    output_dir.mkdir(parents=True, exist_ok=True)
    issues: list[str] = []
    rows: list[dict[str, Any]] = []
    candidate_path = output_dir / PRS_EDGE_PRIMARY_CANDIDATE_FILENAME
    try:
        rows = build_position_response_edge_primary_candidate_rows(
            source_path=source_path
        )
    except ContractValidationError as exc:
        issues.extend(exc.issues)
    if rows:
        write_csv_rows(candidate_path, rows)
        row_validation_issues = validate_position_response_surface_rows(
            rows,
            production_table=True,
            require_complete_row_arithmetic=True,
        )
        issues.extend(row_validation_issues)

    status = (
        PRS_EDGE_PRIMARY_CANDIDATE_PASS_STATUS
        if rows and not issues
        else PRS_EDGE_PRIMARY_CANDIDATE_BLOCKED_STATUS
    )
    issue_rows = [
        {"issue_index": index, "issue": issue}
        for index, issue in enumerate(issues, start=1)
    ] or [{"issue_index": "", "issue": "none"}]
    issue_path = output_dir / PRS_EDGE_PRIMARY_CANDIDATE_ISSUES_FILENAME
    write_csv_rows(issue_path, issue_rows)
    report: dict[str, Any] = {
        "schema_version": "nodi_position_response_edge_primary_candidate_v1",
        "status": status,
        "artifact": POSITION_RESPONSE_ARTIFACT,
        "gate_role": "edge_primary_candidate_generation_not_promoted",
        "allowed_current_action": "write_validated_candidate_rows_no_production_gate_promotion",
        "source_path": str(source_path),
        "source_sha256": sha256_file(source_path) if source_path.exists() else "",
        "source_production_eligibility_policy": PRS_SOURCE_PRODUCTION_ELIGIBILITY_POLICY,
        "strict_numeric_sufficiency_policy_retained": PRS_SOURCE_NUMERIC_SUFFICIENCY_POLICY,
        "candidate_csv": str(candidate_path) if rows else "",
        "candidate_csv_sha256": sha256_file(candidate_path) if rows else "",
        "candidate_row_count": len(rows),
        "expected_rows_per_route_diameter_view": ROWS_PER_ROUTE_DIAMETER_VIEW,
        "route_diameter_view_count": len(
            {
                (
                    _value(row, "route_id_nodi"),
                    _value(row, "diameter_nm"),
                    _value(row, "NODI_view"),
                )
                for row in rows
            }
        ),
        "edge_primary_row_count": sum(
            1 for row in rows if _value(row, "distribution_type") == "edge_norm_1d"
        ),
        "xz_diagnostic_row_count": sum(
            1 for row in rows if _value(row, "distribution_type") == "xz_norm_2d"
        ),
        "xz_primary_promoted_row_count": sum(
            1
            for row in rows
            if _value(row, "aggregate_source_type") == "xz_norm_primary_if_adequate"
        ),
        "issues": issues,
        "issue_csv": str(issue_path),
        "issue_csv_sha256": sha256_file(issue_path),
        "candidate_promoted_to_production_gate": False,
        "production_generation_performed": False,
        "nodi_run_performed": False,
        "comsol_run_performed": False,
        "joint_route_class_regenerated": False,
        "no_comsol_run": True,
        "no_joint_route_class_regeneration": True,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_winner": True,
        "not_detection_probability": True,
        "not_true_W_eff": True,
        "not_measured_geometry": True,
        "not_optical_solver_output": True,
        "not_fabrication_release": True,
        "not_P3_solver_conclusion": True,
        "claim_boundary": PRS_CLAIM_BOUNDARY,
    }
    report_path = output_dir / PRS_EDGE_PRIMARY_CANDIDATE_REPORT_FILENAME
    write_json_atomic(report_path, report, sort_keys=True)
    report["report_path"] = str(report_path)
    report["report_sha256"] = sha256_file(report_path)
    return report


def validate_position_response_source_sufficiency_report(
    report: Mapping[str, Any],
) -> list[str]:
    """Validate PRS source numeric-sufficiency preflight boundaries."""
    issues: list[str] = []
    if (
        report.get("schema_version")
        != "nodi_position_response_source_numeric_sufficiency_preflight_v1"
    ):
        issues.append("PRS-SUFF: schema_version drifted")
    if report.get("status") not in {
        PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS,
        PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
    }:
        issues.append("PRS-SUFF: invalid status")
    if report.get("artifact") != POSITION_RESPONSE_ARTIFACT:
        issues.append("PRS-SUFF: artifact drifted")
    if report.get("minimum_required_source_grain") != PRS_SOURCE_MINIMUM_GRAIN:
        issues.append("PRS-SUFF: minimum source grain drifted")
    if report.get("numeric_sufficiency_policy") != PRS_SOURCE_NUMERIC_SUFFICIENCY_POLICY:
        issues.append("PRS-SUFF: numeric sufficiency policy drifted")
    if report.get("min_events_per_bin_for_production") != PRS_MIN_EVENTS_PER_BIN_FOR_PRODUCTION:
        issues.append("PRS-SUFF: min_events_per_bin_for_production drifted")
    candidate_rows = report.get("candidate_rows")
    if not isinstance(candidate_rows, list):
        issues.append("PRS-SUFF: candidate_rows must be a list")
    job_plan_rows = report.get("job_plan_rows")
    if not isinstance(job_plan_rows, list):
        issues.append("PRS-SUFF: job_plan_rows must be a list")
    if report.get("status") == PRS_SOURCE_SUFFICIENCY_PASS_STATUS:
        if not report.get("numeric_sufficient_candidates"):
            issues.append("PRS-SUFF: pass status lacks numeric_sufficient_candidates")
    if report.get("status") == PRS_SOURCE_SUFFICIENCY_BLOCKED_STATUS:
        blockers = report.get("blockers")
        if not isinstance(blockers, list) or not blockers:
            issues.append("PRS-SUFF: blocked status must carry a blocker")
    for field in (
        "position_response_surface_production_generated",
        "production_generation_performed",
        "full_runner_execution_performed",
        "nodi_run_performed",
        "comsol_run_performed",
        "joint_route_class_regenerated",
    ):
        if report.get(field) is not False:
            issues.append(f"PRS-SUFF: {field} must remain false")
    for field in (
        "no_prs_production_artifact",
        "no_comsol_run",
        "no_joint_route_class_regeneration",
        "not_qch_weighted",
        "not_yield",
        "not_winner",
        "not_detection_probability",
        "not_true_W_eff",
        "not_measured_geometry",
        "not_optical_solver_output",
        "not_fabrication_release",
        "not_P3_solver_conclusion",
        "job_plan_shortfall_fields_are_diagnostic_not_event_counts",
    ):
        if report.get(field) is not True:
            issues.append(f"PRS-SUFF: {field} must remain true")
    if report.get("job_plan_execution_authorized") is not False:
        issues.append("PRS-SUFF: job_plan_execution_authorized must remain false")
    return issues


def _evaluate_prs_source_sufficiency_candidate(
    path: Path,
) -> tuple[dict[str, str], list[dict[str, str]]]:
    if not path.exists():
        return (
            _prs_source_sufficiency_candidate_row(
                path=path,
                candidate_status=PRS_SOURCE_NUMERIC_MISSING_CANDIDATE_STATUS,
                issue_summary="candidate_file_missing",
            ),
            [],
        )
    rows = read_csv_rows(path)
    candidate_sha256 = sha256_file(path)
    if not rows:
        return (
            _prs_source_sufficiency_candidate_row(
                path=path,
                candidate_status=PRS_SOURCE_NUMERIC_INVALID_CANDIDATE_STATUS,
                candidate_sha256=candidate_sha256,
                issue_summary="no_source_rows",
            ),
            [],
        )
    validation_issues = validate_position_response_bin_source_rows(rows)
    source_scope_status = _prs_source_scope_status(rows, set(rows[0].keys()))
    groups = _prs_source_sufficiency_groups(rows)
    inadequate_rows = [
        row
        for row in rows
        if not _prs_source_row_numeric_sufficient(row)
    ]
    minimum_n_events_bin = _minimum_row_int(rows, "n_events_bin")
    minimum_total_events_seed = _minimum_row_int(rows, "n_events_total_seed")
    if validation_issues:
        candidate_status = PRS_SOURCE_NUMERIC_INVALID_CANDIDATE_STATUS
        issue_summary = "validation_issues"
    elif source_scope_status != "production_candidate_scope":
        candidate_status = PRS_SOURCE_NUMERIC_INSUFFICIENT_CANDIDATE_STATUS
        issue_summary = source_scope_status
    elif inadequate_rows:
        candidate_status = PRS_SOURCE_NUMERIC_INSUFFICIENT_CANDIDATE_STATUS
        issue_summary = "sparse_or_empty_bins_present"
    else:
        candidate_status = PRS_SOURCE_NUMERIC_SUFFICIENT_CANDIDATE_STATUS
        issue_summary = "none"

    job_plan_rows = _prs_source_sufficiency_job_plan_rows(
        path=path,
        candidate_sha256=candidate_sha256,
        rows=rows,
        groups=groups,
    )
    return (
        _prs_source_sufficiency_candidate_row(
            path=path,
            candidate_status=candidate_status,
            candidate_sha256=candidate_sha256,
            row_count=len(rows),
            group_count=len(groups),
            validation_issue_count=len(validation_issues),
            source_scope_status=source_scope_status,
            adequate_row_count=len(rows) - len(inadequate_rows),
            inadequate_row_count=len(inadequate_rows),
            decision_use_disallowed_row_count=sum(
                1 for row in rows if _value(row, "decision_use_allowed") != "true"
            ),
            sparse_or_empty_row_count=sum(
                1
                for row in rows
                if _value(row, "bin_sample_status") in {"sparse", "empty"}
            ),
            minimum_n_events_bin=minimum_n_events_bin,
            minimum_total_events_seed=minimum_total_events_seed,
            issue_summary=issue_summary,
        ),
        job_plan_rows,
    )


def _evaluate_prs_source_production_eligibility_candidate(
    path: Path,
) -> tuple[dict[str, str], list[dict[str, str]]]:
    if not path.exists():
        return (
            _prs_source_production_eligibility_candidate_row(
                path=path,
                candidate_status=PRS_SOURCE_PRODUCTION_MISSING_CANDIDATE_STATUS,
                issue_summary="candidate_file_missing",
            ),
            [],
        )
    rows = read_csv_rows(path)
    candidate_sha256 = sha256_file(path)
    if not rows:
        return (
            _prs_source_production_eligibility_candidate_row(
                path=path,
                candidate_status=PRS_SOURCE_PRODUCTION_INVALID_CANDIDATE_STATUS,
                candidate_sha256=candidate_sha256,
                issue_summary="no_source_rows",
            ),
            [],
        )

    validation_issues = validate_position_response_bin_source_rows(rows)
    source_scope_status = _prs_source_scope_status(rows, set(rows[0].keys()))
    groups = _prs_source_sufficiency_groups(rows)
    group_rows = [
        _prs_source_production_eligibility_group_row(
            path=path,
            candidate_sha256=candidate_sha256,
            route_id=route_id,
            diameter_nm=diameter_nm,
            view=view,
            seed=seed,
            group_rows=group_rows_for_seed,
        )
        for (route_id, diameter_nm, view, seed), group_rows_for_seed in sorted(groups.items())
    ]
    ineligible_groups = [
        row
        for row in group_rows
        if row["group_status"] != "edge_primary_group_eligible_xz_diagnostic_only"
    ]
    edge_rows = [
        row for row in rows if _value(row, "distribution_type") == "edge_norm_1d"
    ]
    xz_rows = [
        row for row in rows if _value(row, "distribution_type") == "xz_norm_2d"
    ]
    edge_inadequate = [
        row for row in edge_rows if not _prs_source_row_numeric_sufficient(row)
    ]
    xz_sparse_or_empty = [
        row for row in xz_rows if _value(row, "bin_sample_status") in {"sparse", "empty"}
    ]

    if validation_issues:
        candidate_status = PRS_SOURCE_PRODUCTION_INVALID_CANDIDATE_STATUS
        issue_summary = "validation_issues"
    elif source_scope_status != "production_candidate_scope":
        candidate_status = PRS_SOURCE_PRODUCTION_INELIGIBLE_CANDIDATE_STATUS
        issue_summary = source_scope_status
    elif ineligible_groups:
        candidate_status = PRS_SOURCE_PRODUCTION_INELIGIBLE_CANDIDATE_STATUS
        issue_summary = "edge_primary_group_ineligible"
    else:
        candidate_status = PRS_SOURCE_PRODUCTION_ELIGIBLE_CANDIDATE_STATUS
        issue_summary = "none"

    return (
        _prs_source_production_eligibility_candidate_row(
            path=path,
            candidate_status=candidate_status,
            candidate_sha256=candidate_sha256,
            row_count=len(rows),
            group_count=len(groups),
            validation_issue_count=len(validation_issues),
            source_scope_status=source_scope_status,
            edge_primary_row_count=len(edge_rows),
            edge_primary_eligible_row_count=len(edge_rows) - len(edge_inadequate),
            edge_primary_ineligible_row_count=len(edge_inadequate),
            xz_diagnostic_row_count=len(xz_rows),
            xz_sparse_or_empty_diagnostic_row_count=len(xz_sparse_or_empty),
            ineligible_group_count=len(ineligible_groups),
            issue_summary=issue_summary,
        ),
        group_rows,
    )


def _prs_source_production_eligibility_candidate_row(
    *,
    path: Path,
    candidate_status: str,
    candidate_sha256: str = "",
    row_count: int = 0,
    group_count: int = 0,
    validation_issue_count: int = 0,
    source_scope_status: str = "missing",
    edge_primary_row_count: int = 0,
    edge_primary_eligible_row_count: int = 0,
    edge_primary_ineligible_row_count: int = 0,
    xz_diagnostic_row_count: int = 0,
    xz_sparse_or_empty_diagnostic_row_count: int = 0,
    ineligible_group_count: int = 0,
    issue_summary: str = "",
) -> dict[str, str]:
    return {
        "source_production_eligibility_artifact_version": (
            "NODI_POSITION_RESPONSE_SOURCE_PRODUCTION_ELIGIBILITY_PREFLIGHT_V1"
        ),
        "candidate_path": str(path),
        "candidate_exists": str(path.exists()).lower(),
        "candidate_sha256": candidate_sha256,
        "candidate_status": candidate_status,
        "production_eligibility_policy": PRS_SOURCE_PRODUCTION_ELIGIBILITY_POLICY,
        "strict_numeric_sufficiency_policy_retained": PRS_SOURCE_NUMERIC_SUFFICIENCY_POLICY,
        "minimum_required_source_grain": PRS_SOURCE_MINIMUM_GRAIN,
        "candidate_row_count": str(row_count),
        "route_diameter_view_seed_group_count": str(group_count),
        "validation_issue_count": str(validation_issue_count),
        "source_scope_status": source_scope_status,
        "edge_primary_row_count": str(edge_primary_row_count),
        "edge_primary_eligible_row_count": str(edge_primary_eligible_row_count),
        "edge_primary_ineligible_row_count": str(edge_primary_ineligible_row_count),
        "xz_diagnostic_row_count": str(xz_diagnostic_row_count),
        "xz_sparse_or_empty_diagnostic_row_count": str(
            xz_sparse_or_empty_diagnostic_row_count
        ),
        "ineligible_group_count": str(ineligible_group_count),
        "xz_primary_promotion_authorized": "false",
        "preflight_only": "true",
        "production_prs_generated": "false",
        "not_qch_weighted": "true",
        "not_yield": "true",
        "not_detection_probability": "true",
        "issue_summary": issue_summary,
        "claim_boundary": PRS_CLAIM_BOUNDARY,
    }


def _prs_source_production_eligibility_group_row(
    *,
    path: Path,
    candidate_sha256: str,
    route_id: str,
    diameter_nm: str,
    view: str,
    seed: str,
    group_rows: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    edge_rows = [
        row for row in group_rows if _value(row, "distribution_type") == "edge_norm_1d"
    ]
    edge_base_rows = [
        row for row in edge_rows if _value(row, "row_kind") == "base_bin"
    ]
    edge_special_rows = [
        row for row in edge_rows if _value(row, "row_kind") == "special_aggregate"
    ]
    xz_rows = [
        row for row in group_rows if _value(row, "distribution_type") == "xz_norm_2d"
    ]
    xz_base_rows = [
        row for row in xz_rows if _value(row, "row_kind") == "base_bin"
    ]
    xz_special_rows = [
        row for row in xz_rows if _value(row, "row_kind") == "special_aggregate"
    ]
    edge_inadequate = [
        row for row in edge_rows if not _prs_source_row_numeric_sufficient(row)
    ]
    xz_sparse_or_empty = [
        row for row in xz_rows if _value(row, "bin_sample_status") in {"sparse", "empty"}
    ]
    issues: list[str] = []
    if len(group_rows) != ROWS_PER_ROUTE_DIAMETER_VIEW:
        issues.append("row_count_mismatch")
    if len(edge_base_rows) != EDGE_BASE_BIN_COUNT:
        issues.append("edge_base_count_mismatch")
    if len(edge_special_rows) != SPECIAL_AGGREGATE_COUNT_PER_DISTRIBUTION:
        issues.append("edge_special_count_mismatch")
    if len(xz_base_rows) != XZ_BASE_BIN_COUNT:
        issues.append("xz_base_count_mismatch")
    if len(xz_special_rows) != SPECIAL_AGGREGATE_COUNT_PER_DISTRIBUTION:
        issues.append("xz_special_count_mismatch")
    if edge_inadequate:
        issues.append("edge_primary_sparse_or_empty")
    group_status = (
        "edge_primary_group_eligible_xz_diagnostic_only"
        if not issues
        else "blocked_edge_primary_group_ineligible"
    )
    return {
        "candidate_path": str(path),
        "candidate_sha256": candidate_sha256,
        "route_id_nodi": route_id,
        "diameter_nm": diameter_nm,
        "NODI_view": view,
        "seed": seed,
        "group_status": group_status,
        "row_count": str(len(group_rows)),
        "edge_base_row_count": str(len(edge_base_rows)),
        "edge_special_row_count": str(len(edge_special_rows)),
        "edge_primary_ineligible_row_count": str(len(edge_inadequate)),
        "edge_primary_min_n_events_bin": _format_optional_int(
            _minimum_row_int(edge_rows, "n_events_bin")
        ),
        "xz_base_row_count": str(len(xz_base_rows)),
        "xz_special_row_count": str(len(xz_special_rows)),
        "xz_sparse_or_empty_diagnostic_row_count": str(len(xz_sparse_or_empty)),
        "xz_primary_promotion_authorized": "false",
        "production_prs_generated": "false",
        "issue_summary": "none" if not issues else ";".join(issues),
        "claim_boundary": PRS_CLAIM_BOUNDARY,
    }


def _position_response_edge_primary_candidate_row(
    *,
    source_path: Path,
    source_sha: str,
    group_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    first = group_rows[0]
    distribution = _value(first, "distribution_type")
    n_events_by_seed = [
        _row_int_value(row, "n_events_bin") or 0 for row in group_rows
    ]
    n_events_bin = sum(n_events_by_seed)
    response_count = sum(
        _row_int_value(row, "response_count_bin") or 0 for row in group_rows
    )
    sample_status = (
        "empty"
        if n_events_bin == 0
        else "sparse"
        if n_events_bin < PRS_MIN_EVENTS_PER_BIN_FOR_PRODUCTION
        else "adequate"
    )
    is_edge_primary = distribution == "edge_norm_1d"
    decision_use_allowed = is_edge_primary and sample_status == "adequate"
    aggregate_source_type = (
        "edge_norm_primary" if is_edge_primary else "xz_norm_diagnostic"
    )
    sparse_policy = (
        "aggregate_level_explicit_only"
        if is_edge_primary
        else "empty_bins_never_decision_use"
        if sample_status == "empty"
        else "sparse_individual_bins_context_only"
    )
    source_artifact = (
        f"{source_path};policy={PRS_SOURCE_PRODUCTION_ELIGIBILITY_POLICY};"
        "candidate_not_promoted"
    )
    return {
        "response_surface_artifact_version": POSITION_RESPONSE_VERSION,
        "row_scope": "response_surface_bin",
        "route_id_nodi": _value(first, "route_id_nodi"),
        "lambda_nm": _value(first, "lambda_nm"),
        "W_nominal_nm": _value(first, "W_nominal_nm"),
        "D_nm": _value(first, "D_nm"),
        "NODI_view": _value(first, "NODI_view"),
        "diameter_nm": _value(first, "diameter_nm"),
        "particle_kind": _value(first, "particle_kind"),
        "distribution_type": distribution,
        "row_kind": _value(first, "row_kind"),
        "aggregate_id": _value(first, "aggregate_id"),
        "bin_id": _value(first, "bin_id"),
        "edge_norm_min": _value(first, "edge_norm_min"),
        "edge_norm_max": _value(first, "edge_norm_max"),
        "x_norm_min": _value(first, "x_norm_min"),
        "x_norm_max": _value(first, "x_norm_max"),
        "z_norm_min": _value(first, "z_norm_min"),
        "z_norm_max": _value(first, "z_norm_max"),
        "aggregate_source_type": aggregate_source_type,
        "n_seeds": len({_value(row, "seed") for row in group_rows}),
        "n_events_total": sum(
            _row_int_value(row, "n_events_total_seed") or 0 for row in group_rows
        ),
        "n_events_bin": n_events_bin,
        "n_events_bin_per_seed_min": min(n_events_by_seed) if n_events_by_seed else 0,
        "response_count_source_only_not_probability": response_count,
        "sparse_bin_flag": str(sample_status != "adequate").lower(),
        "sparse_bin_policy": sparse_policy,
        "bin_sample_status": sample_status,
        "decision_use_allowed": str(decision_use_allowed).lower(),
        "guardrail_status": "recommendation_eligible"
        if decision_use_allowed
        else "reference_too_weak",
        "position_distribution_basis": PRS_POSITION_DISTRIBUTION_BASIS,
        "flow_condition_id": PRS_NEUTRAL_FLOW_CONDITION_ID,
        "flow_condition_version": "V1",
        "flow_condition_source_sha": source_sha,
        "flow_condition_scope": PRS_FLOW_CONDITION_SCOPE,
        "flow_condition_claim_boundary": PRS_FLOW_CONDITION_CLAIM_BOUNDARY,
        "view_physical_independence_flag": "false",
        "not_comsol_transport_distribution": "true",
        "not_qch_weighted": "true",
        "not_yield": "true",
        "not_detection_probability": "true",
        "claim_boundary": PRS_CLAIM_BOUNDARY,
        "source_artifact": source_artifact,
        "source_sha256": source_sha,
    }


def _prs_source_sufficiency_candidate_row(
    *,
    path: Path,
    candidate_status: str,
    candidate_sha256: str = "",
    row_count: int = 0,
    group_count: int = 0,
    validation_issue_count: int = 0,
    source_scope_status: str = "missing",
    adequate_row_count: int = 0,
    inadequate_row_count: int = 0,
    decision_use_disallowed_row_count: int = 0,
    sparse_or_empty_row_count: int = 0,
    minimum_n_events_bin: int | None = None,
    minimum_total_events_seed: int | None = None,
    issue_summary: str = "",
) -> dict[str, str]:
    return {
        "source_numeric_sufficiency_artifact_version": (
            "NODI_POSITION_RESPONSE_SOURCE_NUMERIC_SUFFICIENCY_PREFLIGHT_V1"
        ),
        "candidate_path": str(path),
        "candidate_exists": str(path.exists()).lower(),
        "candidate_sha256": candidate_sha256,
        "candidate_status": candidate_status,
        "numeric_sufficiency_policy": PRS_SOURCE_NUMERIC_SUFFICIENCY_POLICY,
        "minimum_required_source_grain": PRS_SOURCE_MINIMUM_GRAIN,
        "min_events_per_bin_for_production": str(
            PRS_MIN_EVENTS_PER_BIN_FOR_PRODUCTION
        ),
        "candidate_row_count": str(row_count),
        "route_diameter_view_seed_group_count": str(group_count),
        "validation_issue_count": str(validation_issue_count),
        "source_scope_status": source_scope_status,
        "adequate_row_count": str(adequate_row_count),
        "inadequate_row_count": str(inadequate_row_count),
        "decision_use_disallowed_row_count": str(decision_use_disallowed_row_count),
        "sparse_or_empty_row_count": str(sparse_or_empty_row_count),
        "minimum_n_events_bin": "" if minimum_n_events_bin is None else str(minimum_n_events_bin),
        "minimum_total_events_seed": ""
        if minimum_total_events_seed is None
        else str(minimum_total_events_seed),
        "issue_summary": issue_summary,
        "preflight_only": "true",
        "production_prs_generated": "false",
        "not_qch_weighted": "true",
        "not_yield": "true",
        "not_detection_probability": "true",
        "claim_boundary": PRS_CLAIM_BOUNDARY,
    }


def _prs_source_sufficiency_groups(
    rows: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, str, str, str], list[Mapping[str, Any]]]:
    groups: dict[tuple[str, str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[
            (
                _value(row, "route_id_nodi"),
                _value(row, "diameter_nm"),
                _value(row, "NODI_view"),
                _value(row, "seed"),
            )
        ].append(row)
    return groups


def _prs_source_row_numeric_sufficient(row: Mapping[str, Any]) -> bool:
    n_events_bin = _row_int_value(row, "n_events_bin")
    return (
        _value(row, "bin_sample_status") == "adequate"
        and _value(row, "decision_use_allowed") == "true"
        and _value(row, "sparse_bin_flag") == "false"
        and n_events_bin is not None
        and n_events_bin >= PRS_MIN_EVENTS_PER_BIN_FOR_PRODUCTION
    )


def _minimum_row_int(
    rows: Sequence[Mapping[str, Any]],
    field: str,
) -> int | None:
    values = [
        value
        for row in rows
        if (value := _row_int_value(row, field)) is not None
    ]
    return min(values) if values else None


def _row_int_value(row: Mapping[str, Any], field: str) -> int | None:
    value = _value(row, field)
    if value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _format_optional_int(value: int | None) -> str:
    return "" if value is None else str(value)


def _prs_source_sufficiency_job_plan_rows(
    *,
    path: Path,
    candidate_sha256: str,
    rows: Sequence[Mapping[str, Any]],
    groups: Mapping[tuple[str, str, str, str], Sequence[Mapping[str, Any]]],
) -> list[dict[str, str]]:
    job_rows: list[dict[str, str]] = []
    for (route_id, diameter_nm, view, seed), group_rows in sorted(groups.items()):
        insufficient_rows = [
            row
            for row in group_rows
            if not _prs_source_row_numeric_sufficient(row)
        ]
        if not insufficient_rows:
            continue
        min_n_events_bin = _minimum_row_int(insufficient_rows, "n_events_bin")
        current_total = max(
            [
                value
                for row in group_rows
                if (value := _row_int_value(row, "n_events_total_seed")) is not None
            ]
            or [0]
        )
        summed_bin_row_shortfall = sum(
            max(
                0,
                PRS_MIN_EVENTS_PER_BIN_FOR_PRODUCTION
                - (_row_int_value(row, "n_events_bin") or 0),
            )
            for row in insufficient_rows
        )
        job_rows.append(
            {
                "candidate_path": str(path),
                "candidate_sha256": candidate_sha256,
                "route_id_nodi": route_id,
                "diameter_nm": diameter_nm,
                "NODI_view": view,
                "seed": seed,
                "current_total_events_seed": str(current_total),
                "minimum_n_events_bin": ""
                if min_n_events_bin is None
                else str(min_n_events_bin),
                "insufficient_row_count": str(len(insufficient_rows)),
                "summed_bin_row_shortfall_not_event_count": str(
                    summed_bin_row_shortfall
                ),
                "min_events_per_bin_for_production": str(
                    PRS_MIN_EVENTS_PER_BIN_FOR_PRODUCTION
                ),
                "recommended_min_total_events_floor": str(
                    PRS_MIN_EVENTS_PER_BIN_FOR_PRODUCTION * XZ_BASE_BIN_COUNT
                ),
                "recommended_min_total_events_floor_basis": (
                    "xz_441_bins_times_min_100_per_bin_floor_not_requested_n_events"
                ),
                "recommended_action": (
                    "regenerate_real_nodi_source_until_all_bins_adequate_before_"
                    "production_prs"
                ),
                "execution_authorized": "false",
                "shortfall_fields_are_diagnostic_not_event_counts": "true",
                "preflight_only": "true",
                "production_prs_generated": "false",
                "not_qch_weighted": "true",
                "not_yield": "true",
                "not_detection_probability": "true",
                "claim_boundary": PRS_CLAIM_BOUNDARY,
            }
        )
    if not rows:
        job_rows.append(
            {
                "candidate_path": str(path),
                "candidate_sha256": candidate_sha256,
                "route_id_nodi": "",
                "diameter_nm": "",
                "NODI_view": "",
                "seed": "",
                "current_total_events_seed": "0",
                "minimum_n_events_bin": "",
                "insufficient_row_count": "0",
                "summed_bin_row_shortfall_not_event_count": "",
                "min_events_per_bin_for_production": str(
                    PRS_MIN_EVENTS_PER_BIN_FOR_PRODUCTION
                ),
                "recommended_min_total_events_floor": str(
                    PRS_MIN_EVENTS_PER_BIN_FOR_PRODUCTION * XZ_BASE_BIN_COUNT
                ),
                "recommended_min_total_events_floor_basis": (
                    "xz_441_bins_times_min_100_per_bin_floor_not_requested_n_events"
                ),
                "recommended_action": "provide_candidate_bin_conditioned_source",
                "execution_authorized": "false",
                "shortfall_fields_are_diagnostic_not_event_counts": "true",
                "preflight_only": "true",
                "production_prs_generated": "false",
                "not_qch_weighted": "true",
                "not_yield": "true",
                "not_detection_probability": "true",
                "claim_boundary": PRS_CLAIM_BOUNDARY,
            }
        )
    return job_rows


def _validate_prs_accumulation_route_source(
    rows: Sequence[Mapping[str, Any]],
) -> list[str]:
    if not rows:
        return ["PRS-ACCUM-SOURCE: route source is empty or missing"]
    columns = set(rows[0].keys())
    required = {
        "particle_name",
        "particle_material",
        "wavelength_nm",
        "width_nm",
        "depth_nm",
    }
    missing = sorted(required - columns)
    return [f"PRS-ACCUM-SOURCE: missing columns {missing}"] if missing else []


def _prs_accumulation_particle_by_diameter(
    rows: Sequence[Mapping[str, Any]],
) -> dict[int, str]:
    candidates: dict[int, set[str]] = defaultdict(set)
    for row in rows:
        material = _value(row, "particle_material").lower()
        name = _value(row, "particle_name")
        if material != "exosome" and "exosome" not in name.lower():
            continue
        diameter = _infer_diameter_nm_from_particle_name(name)
        if diameter is not None and diameter in PRS_APPROVED_DIAMETERS_NM:
            candidates[int(diameter)].add(name)
    return {
        diameter: sorted(names)[0]
        for diameter, names in candidates.items()
        if names
    }


def _infer_diameter_nm_from_particle_name(name: str) -> int | None:
    match = re.search(r"(?P<diameter>\d+(?:\.\d+)?)\s*nm", str(name).lower())
    if not match:
        return None
    try:
        return int(round(float(match.group("diameter"))))
    except ValueError:
        return None


def _prs_accumulation_selected_routes(route_scope: str) -> list[tuple[int, int, int]]:
    routes = sorted(PRS_APPROVED_ROUTE_MATRIX)
    if route_scope == "p1_preferred_only":
        return [route for route in routes if route != PRS_P2_DIAGNOSTIC_TRAP_ROUTE]
    return routes


def _prs_accumulation_missing_slices(
    *,
    route_source_rows: Sequence[Mapping[str, Any]],
    selected_routes: Sequence[tuple[int, int, int]],
    particle_by_diameter: Mapping[int, str],
) -> list[tuple[str, int, str]]:
    available = {
        (
            _row_int_value(row, "wavelength_nm"),
            _row_int_value(row, "width_nm"),
            _row_int_value(row, "depth_nm"),
            _value(row, "particle_name"),
        )
        for row in route_source_rows
    }
    missing: list[tuple[str, int, str]] = []
    for route in selected_routes:
        for diameter in sorted(PRS_APPROVED_DIAMETERS_NM):
            particle_name = particle_by_diameter.get(diameter, "")
            if not particle_name:
                continue
            key = (route[0], route[1], route[2], particle_name)
            if key not in available:
                missing.append((_route_id_from_tuple(route), diameter, particle_name))
    return missing


def _prs_source_accumulation_job_rows(
    *,
    route_source_path: Path,
    route_source_sha: str,
    selected_routes: Sequence[tuple[int, int, int]],
    particle_by_diameter: Mapping[int, str],
    route_source_rows: Sequence[Mapping[str, Any]],
    seeds: Sequence[int],
    n_events_per_seed: int,
) -> list[dict[str, Any]]:
    slice_counts = _prs_accumulation_slice_counts(route_source_rows)
    rows: list[dict[str, Any]] = []
    job_index = 0
    for route in selected_routes:
        route_id = _route_id_from_tuple(route)
        route_scope_class = (
            "p2_diagnostic_trap"
            if route == PRS_P2_DIAGNOSTIC_TRAP_ROUTE
            else "p1_preferred"
        )
        for diameter in sorted(PRS_APPROVED_DIAMETERS_NM):
            particle_name = particle_by_diameter.get(diameter, "")
            for view in sorted(PRS_APPROVED_VIEWS):
                for seed in seeds:
                    job_index += 1
                    slice_count = slice_counts.get((route, particle_name), 0)
                    rows.append(
                        {
                            "source_accumulation_job_plan_version": (
                                "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_JOB_PLAN_V1"
                            ),
                            "job_id": f"PRS_ACCUM_{job_index:06d}",
                            "route_scope_class": route_scope_class,
                            "route_id_nodi": route_id,
                            "lambda_nm": route[0],
                            "W_nominal_nm": route[1],
                            "D_nm": route[2],
                            "diameter_nm": diameter,
                            "particle_name": particle_name,
                            "NODI_view": view,
                            "seed": int(seed),
                            "n_events_requested_per_seed": int(n_events_per_seed),
                            "min_events_per_bin_for_production": (
                                PRS_MIN_EVENTS_PER_BIN_FOR_PRODUCTION
                            ),
                            "target_event_floor_basis": (
                                "xz_441_bins_times_min_100_per_bin_floor_not_"
                                "sufficiency_guarantee"
                            ),
                            "expected_bin_source_rows": ROWS_PER_ROUTE_DIAMETER_VIEW,
                            "route_source_slice_rows": slice_count,
                            "route_source_binding_status": (
                                "available" if slice_count > 0 else "missing"
                            ),
                            "source_scope": PRS_SOURCE_PRODUCTION_SCOPE,
                            "post_run_required_gate": PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
                            "route_source_path": str(route_source_path),
                            "route_source_sha256": route_source_sha,
                            "execution_authorized": "false",
                            "preflight_only": "true",
                            "nodi_run_performed": "false",
                            "full_runner_execution_performed": "false",
                            "production_prs_generated": "false",
                            "comsol_run_performed": "false",
                            "joint_route_class_regenerated": "false",
                            "not_qch_weighted": "true",
                            "not_yield": "true",
                            "not_winner": "true",
                            "not_detection_probability": "true",
                            "claim_boundary": PRS_CLAIM_BOUNDARY,
                        }
                    )
    return rows


def _prs_accumulation_slice_counts(
    rows: Sequence[Mapping[str, Any]],
) -> dict[tuple[tuple[int, int, int], str], int]:
    counts: Counter[tuple[tuple[int, int, int], str]] = Counter()
    for row in rows:
        wavelength_nm = _row_int_value(row, "wavelength_nm")
        width_nm = _row_int_value(row, "width_nm")
        depth_nm = _row_int_value(row, "depth_nm")
        if wavelength_nm is None or width_nm is None or depth_nm is None:
            continue
        counts[
            (
                (wavelength_nm, width_nm, depth_nm),
                _value(row, "particle_name"),
            )
        ] += 1
    return dict(counts)


def _prs_source_accumulation_blocker(
    *,
    blocker_id: str,
    status: str,
    current_evidence: str,
    unblock_action: str,
) -> dict[str, str]:
    return {
        "artifact": POSITION_RESPONSE_BIN_SOURCE_ARTIFACT,
        "blocker_id": blocker_id,
        "status": status,
        "required_input_or_policy": "route_source_particle_binding_and_slices",
        "current_evidence": current_evidence,
        "unblock_action": unblock_action,
        "claim_boundary": PRS_CLAIM_BOUNDARY,
    }


def _empty_accumulation_job_rows() -> list[dict[str, str]]:
    return [
        {
            "source_accumulation_job_plan_version": (
                "NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_JOB_PLAN_V1"
            ),
            "job_id": "",
            "route_scope_class": "",
            "route_id_nodi": "",
            "lambda_nm": "",
            "W_nominal_nm": "",
            "D_nm": "",
            "diameter_nm": "",
            "particle_name": "",
            "NODI_view": "",
            "seed": "",
            "n_events_requested_per_seed": "",
            "min_events_per_bin_for_production": str(
                PRS_MIN_EVENTS_PER_BIN_FOR_PRODUCTION
            ),
            "target_event_floor_basis": (
                "xz_441_bins_times_min_100_per_bin_floor_not_sufficiency_guarantee"
            ),
            "expected_bin_source_rows": str(ROWS_PER_ROUTE_DIAMETER_VIEW),
            "route_source_slice_rows": "",
            "route_source_binding_status": "missing",
            "source_scope": PRS_SOURCE_PRODUCTION_SCOPE,
            "post_run_required_gate": PRS_SOURCE_SUFFICIENCY_PASS_STATUS,
            "route_source_path": "",
            "route_source_sha256": "",
            "execution_authorized": "false",
            "preflight_only": "true",
            "nodi_run_performed": "false",
            "full_runner_execution_performed": "false",
            "production_prs_generated": "false",
            "comsol_run_performed": "false",
            "joint_route_class_regenerated": "false",
            "not_qch_weighted": "true",
            "not_yield": "true",
            "not_winner": "true",
            "not_detection_probability": "true",
            "claim_boundary": PRS_CLAIM_BOUNDARY,
        }
    ]


def _evaluate_position_response_source_candidate(path: Path) -> dict[str, str]:
    if not path.exists():
        return _prs_source_candidate_row(
            path=path,
            candidate_status=PRS_SOURCE_MISSING_CANDIDATE_STATUS,
            missing_requirements=["candidate_file"],
        )
    rows = read_csv_rows(path)
    columns = set(rows[0].keys()) if rows else set()
    route_status = _prs_source_route_status(columns)
    diameter_status = _prs_source_column_status(
        columns,
        ("diameter_nm", "particle_diameter_nm"),
    )
    view_status = _prs_source_view_status(path, columns)
    seed_status = _prs_source_seed_status(path, columns)
    distribution_bin_status = _prs_source_distribution_bin_status(columns)
    response_count_status = _prs_source_response_count_status(columns)
    source_scope_status = _prs_source_scope_status(rows, columns)
    requirement_statuses = {
        "route_id_nodi_or_lambda_width_depth": route_status,
        "diameter_nm": diameter_status,
        "NODI_view": view_status,
        "seed": seed_status,
        "distribution_or_bin": distribution_bin_status,
        "per_bin_response_count": response_count_status,
    }
    missing = [
        requirement
        for requirement, status in requirement_statuses.items()
        if status.startswith("missing")
    ]
    if missing:
        candidate_status = PRS_SOURCE_BLOCKED_CANDIDATE_STATUS
    elif source_scope_status == "production_candidate_scope":
        candidate_status = PRS_SOURCE_AVAILABLE_CANDIDATE_STATUS
    else:
        candidate_status = PRS_SOURCE_SHAPE_ONLY_CANDIDATE_STATUS
    return _prs_source_candidate_row(
        path=path,
        candidate_status=candidate_status,
        missing_requirements=missing,
        row_count=len(rows),
        column_count=len(columns),
        candidate_sha256=sha256_file(path),
        route_status=route_status,
        diameter_status=diameter_status,
        view_status=view_status,
        seed_status=seed_status,
        distribution_bin_status=distribution_bin_status,
        response_count_status=response_count_status,
        source_scope_status=source_scope_status,
        columns=columns,
    )


def _prs_source_candidate_row(
    *,
    path: Path,
    candidate_status: str,
    missing_requirements: Sequence[str],
    row_count: int = 0,
    column_count: int = 0,
    candidate_sha256: str = "",
    route_status: str = "missing",
    diameter_status: str = "missing",
    view_status: str = "missing",
    seed_status: str = "missing",
    distribution_bin_status: str = "missing",
    response_count_status: str = "missing",
    source_scope_status: str = "missing",
    columns: set[str] | None = None,
) -> dict[str, str]:
    column_sample = ",".join(sorted(columns or set())[:40])
    return {
        "source_preflight_artifact_version": (
            "NODI_POSITION_RESPONSE_SOURCE_AVAILABILITY_PREFLIGHT_V1"
        ),
        "candidate_path": str(path),
        "candidate_exists": str(path.exists()).lower(),
        "candidate_sha256": candidate_sha256,
        "candidate_row_count": str(row_count),
        "candidate_column_count": str(column_count),
        "candidate_status": candidate_status,
        "minimum_required_source_grain": PRS_SOURCE_MINIMUM_GRAIN,
        "route_grain_status": route_status,
        "diameter_grain_status": diameter_status,
        "view_grain_status": view_status,
        "seed_grain_status": seed_status,
        "distribution_bin_status": distribution_bin_status,
        "response_count_status": response_count_status,
        "source_scope_status": source_scope_status,
        "missing_requirements": ";".join(missing_requirements),
        "column_sample": column_sample,
        "preflight_only": "true",
        "production_prs_generated": "false",
        "not_qch_weighted": "true",
        "not_yield": "true",
        "not_detection_probability": "true",
        "claim_boundary": PRS_CLAIM_BOUNDARY,
    }


def _prs_source_route_status(columns: set[str]) -> str:
    if "route_id_nodi" in columns or "route_id" in columns:
        return "available_column"
    has_lambda = bool({"lambda_nm", "wavelength_nm"} & columns)
    has_width = bool({"W_nominal_nm", "width_nm"} & columns)
    has_depth = bool({"D_nm", "depth_nm"} & columns)
    if has_lambda and has_width and has_depth:
        return "available_composite_columns"
    return "missing_route"


def _prs_source_column_status(columns: set[str], aliases: Sequence[str]) -> str:
    return "available_column" if any(alias in columns for alias in aliases) else "missing_column"


def _prs_source_view_status(path: Path, columns: set[str]) -> str:
    if "NODI_view" in columns:
        return "available_column"
    if "fixed_660_gold" in str(path):
        return "available_file_scope_fixed_660_gold"
    if "per_wavelength_gold" in str(path):
        return "available_file_scope_per_wavelength_gold"
    return "missing_view"


def _prs_source_seed_status(path: Path, columns: set[str]) -> str:
    if {"seed", "random_seed"} & columns:
        return "available_column"
    if re.search(r"seed[_-]\d+", str(path)):
        return "available_file_scope_seed"
    return "missing_seed"


def _prs_source_distribution_bin_status(columns: set[str]) -> str:
    has_distribution = bool({"distribution_type", "position_distribution"} & columns)
    has_bin = bool(
        {
            "bin_id",
            "edge_norm_bin",
            "x_norm_bin",
            "z_norm_bin",
            "edge_norm_min",
            "edge_norm_max",
            "x_norm_min",
            "x_norm_max",
            "z_norm_min",
            "z_norm_max",
        }
        & columns
    )
    has_event_position = "edge_norm" in columns or {"x_norm", "z_norm"} <= columns
    if has_distribution and has_bin:
        return "available_distribution_bin_columns"
    if has_event_position:
        return "available_event_position_columns"
    return "missing_distribution_bin"


def _prs_source_response_count_status(columns: set[str]) -> str:
    if {"response_count_bin", "n_detected_bin"} & columns:
        return "available_bin_count_columns"
    if "event_id" in columns or "event_index" in columns:
        return "available_event_level_rows"
    return "missing_per_bin_response_count"


def _prs_source_scope_status(
    rows: Sequence[Mapping[str, Any]],
    columns: set[str],
) -> str:
    if "source_scope" not in columns:
        return "source_scope_absent_not_production_eligible"
    scopes = {_value(row, "source_scope") for row in rows if _value(row, "source_scope")}
    if scopes == {PRS_SOURCE_PRODUCTION_SCOPE}:
        return "production_candidate_scope"
    if scopes == {PRS_SOURCE_BOUNDED_SMOKE_SCOPE}:
        return "bounded_smoke_scope_not_production_eligible"
    if not scopes:
        return "source_scope_blank_not_production_eligible"
    return "mixed_or_unknown_source_scope_not_production_eligible"


def build_position_response_event_rows_from_nodi_events(
    events: Sequence[Mapping[str, Any]],
    *,
    route: tuple[int, int, int],
    diameter_nm: int,
    view: str,
    seed: int,
    particle_kind: str,
    source_scope: str = PRS_SOURCE_PRODUCTION_SCOPE,
    event_id_prefix: str = "nodi_real_event",
) -> list[dict[str, Any]]:
    """Convert NODI slim event payloads into PRS event-row source input."""
    lambda_nm, width_nm, depth_nm = route
    route_id = _route_id_from_tuple(route)
    rows: list[dict[str, Any]] = []
    issues: list[str] = []
    if source_scope not in PRS_SOURCE_APPROVED_SCOPES:
        issues.append(f"PRS-EVENTSRC-SCOPE: invalid source_scope={source_scope}")
    for index, event in enumerate(events):
        row_index = index + 1
        x_norm = _nodi_event_float(event, "initial_position_x_norm")
        z_norm = _nodi_event_float(event, "initial_position_z_norm")
        if x_norm is None:
            issues.append(
                f"PRS-EVENTSRC-E01 row {row_index}: missing initial_position_x_norm"
            )
            x_value: float | str = ""
        else:
            x_value = x_norm
        if z_norm is None:
            issues.append(
                f"PRS-EVENTSRC-E01 row {row_index}: missing initial_position_z_norm"
            )
            z_value: float | str = ""
        else:
            z_value = z_norm
        rows.append(
            {
                "route_id_nodi": route_id,
                "lambda_nm": int(lambda_nm),
                "W_nominal_nm": int(width_nm),
                "D_nm": int(depth_nm),
                "diameter_nm": int(diameter_nm),
                "NODI_view": view,
                "seed": int(seed),
                "event_id": f"{event_id_prefix}_{index:06d}",
                "x_norm": x_value,
                "z_norm": z_value,
                "response_detected": str(
                    _nodi_event_response_detected(event)
                ).lower(),
                "particle_kind": particle_kind,
                "source_scope": source_scope,
                "source_event_kind": "nodi_run_single_case_batch_slim_event",
                "response_detected_basis": "final_features_n_peaks_gt_0",
            }
        )
    issues.extend(validate_position_response_bin_source_event_rows(rows))
    if issues:
        raise ContractValidationError(POSITION_RESPONSE_BIN_SOURCE_ARTIFACT, issues)
    return rows


def position_response_bin_source_smoke_event_rows() -> list[dict[str, Any]]:
    """Small deterministic event fixture for the PRS bin-source builder."""
    base = {
        "route_id_nodi": "404/W500/D900",
        "lambda_nm": "404",
        "W_nominal_nm": "500",
        "D_nm": "900",
        "diameter_nm": "150",
        "NODI_view": "fixed_660_gold",
        "seed": "11",
        "particle_kind": "exosome_synthetic",
    }
    samples = [
        ("evt_000", -0.92, -0.25, "false"),
        ("evt_001", -0.52, 0.11, "true"),
        ("evt_002", -0.12, 0.18, "false"),
        ("evt_003", 0.08, -0.04, "true"),
        ("evt_004", 0.44, 0.72, "true"),
        ("evt_005", 0.88, -0.88, "false"),
    ]
    return [
        {
            **base,
            "event_id": event_id,
            "x_norm": x_norm,
            "z_norm": z_norm,
            "response_detected": detected,
        }
        for event_id, x_norm, z_norm, detected in samples
    ]


def build_position_response_bin_source_rows_from_events(
    event_rows: Sequence[Mapping[str, Any]],
    *,
    source_scope: str,
    source_artifact: str,
    source_sha256: str,
) -> list[dict[str, Any]]:
    """Aggregate event-level rows into bin-conditioned source rows."""
    issues = validate_position_response_bin_source_event_rows(event_rows)
    if issues:
        raise ContractValidationError(POSITION_RESPONSE_BIN_SOURCE_ARTIFACT, issues)
    if source_scope not in PRS_SOURCE_APPROVED_SCOPES:
        raise ContractValidationError(
            POSITION_RESPONSE_BIN_SOURCE_ARTIFACT,
            [f"PRS-BINSRC-SCOPE: invalid source_scope={source_scope}"],
        )

    grouped: dict[tuple[str, int, str, int], list[Mapping[str, Any]]] = defaultdict(list)
    route_meta: dict[str, tuple[int, int, int]] = {}
    particle_kind_by_group: dict[tuple[str, int, str, int], str] = {}
    for row in event_rows:
        route = _route_tuple_from_row(row, route_field="route_id_nodi")
        if route is None:
            route = _route_tuple_from_row(row)
        if route is None:
            continue
        route_id = _route_id_from_tuple(route)
        route_meta[route_id] = route
        diameter = int(float(_value(row, "diameter_nm")))
        view = _value(row, "NODI_view")
        seed = int(float(_value(row, "seed")))
        group_key = (route_id, diameter, view, seed)
        grouped[group_key].append(row)
        particle_kind_by_group[group_key] = _value(row, "particle_kind") or "unknown"

    rows: list[dict[str, Any]] = []
    for group_key in sorted(grouped):
        route_id, diameter, view, seed = group_key
        route = route_meta[route_id]
        events = grouped[group_key]
        rows.extend(
            _position_response_bin_source_rows_for_group(
                events=events,
                route=route,
                route_id=route_id,
                diameter_nm=diameter,
                view=view,
                seed=seed,
                particle_kind=particle_kind_by_group[group_key],
                source_scope=source_scope,
                source_artifact=source_artifact,
                source_sha256=source_sha256,
            )
        )

    source_issues = validate_position_response_bin_source_rows(rows)
    if source_issues:
        raise ContractValidationError(POSITION_RESPONSE_BIN_SOURCE_ARTIFACT, source_issues)
    return rows


def write_position_response_bin_source_smoke_bundle(output_dir: Path) -> dict[str, Any]:
    """Write a bounded fixture exercising the PRS bin-conditioned source builder."""
    output_dir.mkdir(parents=True, exist_ok=True)
    event_path = output_dir / PRS_BIN_SOURCE_SMOKE_EVENTS_FILENAME
    event_rows = position_response_bin_source_smoke_event_rows()
    write_csv_rows(event_path, event_rows)
    source_rows = build_position_response_bin_source_rows_from_events(
        event_rows,
        source_scope=PRS_SOURCE_BOUNDED_SMOKE_SCOPE,
        source_artifact=str(event_path),
        source_sha256=sha256_file(event_path),
    )
    source_path = output_dir / PRS_BIN_SOURCE_SMOKE_SOURCE_FILENAME
    write_csv_rows(source_path, source_rows)
    source_issues = validate_position_response_bin_source_rows(source_rows)
    report: dict[str, Any] = {
        "schema_version": "nodi_position_response_bin_source_smoke_report_v1",
        "status": (
            PRS_BIN_SOURCE_SMOKE_PASS_STATUS
            if not source_issues
            else PRS_BIN_SOURCE_SMOKE_BLOCKED_STATUS
        ),
        "artifact": POSITION_RESPONSE_BIN_SOURCE_ARTIFACT,
        "source_scope": PRS_SOURCE_BOUNDED_SMOKE_SCOPE,
        "event_rows": len(event_rows),
        "bin_source_rows": len(source_rows),
        "expected_rows_per_route_diameter_view_seed": ROWS_PER_ROUTE_DIAMETER_VIEW,
        "issues": source_issues,
        "event_fixture_path": str(event_path),
        "event_fixture_sha256": sha256_file(event_path),
        "bin_source_path": str(source_path),
        "bin_source_sha256": sha256_file(source_path),
        "preflight_only": True,
        "position_response_surface_production_generated": False,
        "production_generation_performed": False,
        "nodi_full_runner_execution_performed": False,
        "comsol_run_performed": False,
        "joint_route_class_regenerated": False,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_detection_probability": True,
        "claim_boundary": PRS_BIN_SOURCE_CLAIM_BOUNDARY,
    }
    report_path = output_dir / PRS_BIN_SOURCE_SMOKE_REPORT_FILENAME
    write_json_atomic(report_path, report, sort_keys=True)
    report["report_path"] = str(report_path)
    report["report_sha256"] = sha256_file(report_path)
    return report


def validate_position_response_bin_source_event_rows(
    rows: Sequence[Mapping[str, Any]],
) -> list[str]:
    issues: list[str] = []
    if not rows:
        return ["PRS-BINSRC-E01: no event rows supplied"]
    for row_index, row in enumerate(rows, start=1):
        _require_fields(
            row,
            PRS_BIN_SOURCE_EVENT_REQUIRED_FIELDS,
            "PRS-BINSRC-E01",
            row_index,
            issues,
        )
        _reject_forbidden_positive_fields(
            row,
            allowed_negative_fields={
                "not_qch_weighted",
                "not_yield",
                "not_winner",
                "not_detection_probability",
                "not_true_W_eff",
                "not_measured_geometry",
                "not_optical_solver_output",
                "not_fabrication_release",
                "not_P3_solver_conclusion",
            },
            row_index=row_index,
            rule_id="PRS-BINSRC-E08",
            issues=issues,
        )
        route = _route_tuple_from_row(row, route_field="route_id_nodi")
        if route is None:
            route = _route_tuple_from_row(row)
        if route not in PRS_APPROVED_ROUTE_MATRIX:
            _issue(issues, row_index, "PRS-BINSRC-E02", f"unapproved route={route}")
        diameter = _int_field(row, "diameter_nm", row_index, "PRS-BINSRC-E03", issues)
        if diameter is not None and diameter not in PRS_APPROVED_DIAMETERS_NM:
            _issue(issues, row_index, "PRS-BINSRC-E03", f"unapproved diameter={diameter}")
        _validate_enum(row, "NODI_view", PRS_APPROVED_VIEWS, row_index, "PRS-BINSRC-E04", issues)
        _validate_nonnegative_int(row, "seed", row_index, "PRS-BINSRC-E05", issues)
        x_norm = _float_field(row, "x_norm", row_index, "PRS-BINSRC-E06", issues)
        z_norm = _float_field(row, "z_norm", row_index, "PRS-BINSRC-E06", issues)
        if x_norm is not None and not (-1.0 <= x_norm <= 1.0):
            _issue(issues, row_index, "PRS-BINSRC-E06", "x_norm outside [-1,1]")
        if z_norm is not None and not (-1.0 <= z_norm <= 1.0):
            _issue(issues, row_index, "PRS-BINSRC-E06", "z_norm outside [-1,1]")
        if _event_response_bool(row) is None:
            _issue(issues, row_index, "PRS-BINSRC-E07", "invalid response_detected")
    return issues


def validate_position_response_bin_source_rows(
    rows: Sequence[Mapping[str, Any]],
) -> list[str]:
    issues: list[str] = []
    if not rows:
        return ["PRS-BINSRC-V01: no source rows supplied"]
    for row_index, row in enumerate(rows, start=1):
        _require_fields(
            row,
            PRS_BIN_SOURCE_REQUIRED_FIELDS,
            "PRS-BINSRC-V01",
            row_index,
            issues,
        )
        _reject_forbidden_positive_fields(
            row,
            allowed_negative_fields={
                "not_qch_weighted",
                "not_yield",
                "not_winner",
                "not_detection_probability",
                "not_true_W_eff",
                "not_measured_geometry",
                "not_optical_solver_output",
                "not_fabrication_release",
                "not_P3_solver_conclusion",
            },
            row_index=row_index,
            rule_id="PRS-BINSRC-V14",
            issues=issues,
        )
        _validate_constant(
            row,
            "bin_source_artifact_version",
            POSITION_RESPONSE_BIN_SOURCE_VERSION,
            row_index,
            "PRS-BINSRC-V01",
            issues,
        )
        _validate_enum(
            row,
            "source_scope",
            PRS_SOURCE_APPROVED_SCOPES,
            row_index,
            "PRS-BINSRC-V02",
            issues,
        )
        _validate_route_fields(
            row,
            approved_routes=PRS_APPROVED_ROUTE_MATRIX,
            row_index=row_index,
            issues=issues,
            rule_id="PRS-BINSRC-V03",
        )
        diameter = _int_field(row, "diameter_nm", row_index, "PRS-BINSRC-V04", issues)
        if diameter is not None and diameter not in PRS_APPROVED_DIAMETERS_NM:
            _issue(issues, row_index, "PRS-BINSRC-V04", f"unapproved diameter={diameter}")
        _validate_enum(row, "NODI_view", PRS_APPROVED_VIEWS, row_index, "PRS-BINSRC-V05", issues)
        _validate_nonnegative_int(row, "seed", row_index, "PRS-BINSRC-V06", issues)
        _validate_enum(row, "distribution_type", PRS_APPROVED_DISTRIBUTIONS, row_index, "PRS-BINSRC-V07", issues)
        _validate_optional_enum(row, "row_kind", PRS_APPROVED_ROW_KINDS, row_index, "PRS-BINSRC-V07", issues)
        _validate_position_bin(row, row_index, issues)
        total = _validate_nonnegative_int(row, "n_events_total_seed", row_index, "PRS-BINSRC-V08", issues)
        n_events_bin = _validate_nonnegative_int(row, "n_events_bin", row_index, "PRS-BINSRC-V08", issues)
        response_count = _validate_nonnegative_int(row, "response_count_bin", row_index, "PRS-BINSRC-V08", issues)
        if (
            total is not None
            and n_events_bin is not None
            and response_count is not None
        ):
            if n_events_bin > total:
                _issue(issues, row_index, "PRS-BINSRC-V08", "n_events_bin exceeds total")
            if response_count > n_events_bin:
                _issue(issues, row_index, "PRS-BINSRC-V08", "response_count_bin exceeds n_events_bin")
        _validate_sample_status(row, n_events_bin, row_index, issues)
        for field in (
            "preflight_only",
            "production_prs_generated",
            "not_qch_weighted",
            "not_yield",
            "not_detection_probability",
        ):
            _validate_bool_field(row, field, row_index, "PRS-BINSRC-V09", issues)
        if _value(row, "production_prs_generated") != "false":
            _issue(issues, row_index, "PRS-BINSRC-V09", "production_prs_generated must be false")
        _validate_constant(
            row,
            "claim_boundary",
            PRS_BIN_SOURCE_CLAIM_BOUNDARY,
            row_index,
            "PRS-BINSRC-V10",
            issues,
        )
        _validate_source_hash(
            row,
            field="source_sha256",
            row_index=row_index,
            rule_id="PRS-BINSRC-V11",
            issues=issues,
            allow_pending=False,
        )
    _validate_position_response_bin_source_grain(rows, issues)
    _validate_position_response_bin_source_row_arithmetic(rows, issues)
    return issues


def _position_response_bin_source_rows_for_group(
    *,
    events: Sequence[Mapping[str, Any]],
    route: tuple[int, int, int],
    route_id: str,
    diameter_nm: int,
    view: str,
    seed: int,
    particle_kind: str,
    source_scope: str,
    source_artifact: str,
    source_sha256: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    total = len(events)
    parsed = [_parse_position_response_event(row) for row in events]
    for index in range(EDGE_BASE_BIN_COUNT):
        edge_min = index / EDGE_BASE_BIN_COUNT
        edge_max = (index + 1) / EDGE_BASE_BIN_COUNT
        members = [
            event
            for event in parsed
            if edge_min <= event["edge_norm"] < edge_max
            or (index == EDGE_BASE_BIN_COUNT - 1 and event["edge_norm"] <= edge_max)
        ]
        rows.append(
            _position_response_bin_source_row(
                route=route,
                route_id=route_id,
                diameter_nm=diameter_nm,
                view=view,
                seed=seed,
                particle_kind=particle_kind,
                distribution_type="edge_norm_1d",
                row_kind="base_bin",
                aggregate_id="",
                bin_id=f"edge_{index:02d}",
                edge_norm_min=edge_min,
                edge_norm_max=edge_max,
                x_norm_min="",
                x_norm_max="",
                z_norm_min="",
                z_norm_max="",
                members=members,
                total=total,
                source_scope=source_scope,
                source_artifact=source_artifact,
                source_sha256=source_sha256,
            )
        )
    x_edges = _uniform_edges(-1.0, 1.0, 21)
    z_edges = _uniform_edges(-1.0, 1.0, 21)
    for x_index in range(21):
        for z_index in range(21):
            x_min = x_edges[x_index]
            x_max = x_edges[x_index + 1]
            z_min = z_edges[z_index]
            z_max = z_edges[z_index + 1]
            members = [
                event
                for event in parsed
                if _in_bin(event["x_norm"], x_min, x_max, x_index == 20)
                and _in_bin(event["z_norm"], z_min, z_max, z_index == 20)
            ]
            rows.append(
                _position_response_bin_source_row(
                    route=route,
                    route_id=route_id,
                    diameter_nm=diameter_nm,
                    view=view,
                    seed=seed,
                    particle_kind=particle_kind,
                    distribution_type="xz_norm_2d",
                    row_kind="base_bin",
                    aggregate_id="",
                    bin_id=f"x{x_index:02d}_z{z_index:02d}",
                    edge_norm_min="",
                    edge_norm_max="",
                    x_norm_min=x_min,
                    x_norm_max=x_max,
                    z_norm_min=z_min,
                    z_norm_max=z_max,
                    members=members,
                    total=total,
                    source_scope=source_scope,
                    source_artifact=source_artifact,
                    source_sha256=source_sha256,
                )
            )
    aggregate_specs = (
        ("near_center_0p0_0p5", 0.0, 0.5),
        ("selected_annulus_0p5_0p8", 0.5, 0.8),
        ("near_wall_0p8_1p0", 0.8, 1.0),
    )
    for distribution_type in ("edge_norm_1d", "xz_norm_2d"):
        for aggregate_id, edge_min, edge_max in aggregate_specs:
            members = [
                event
                for event in parsed
                if edge_min <= event["edge_norm"] < edge_max
                or (edge_max == 1.0 and event["edge_norm"] <= edge_max)
            ]
            rows.append(
                _position_response_bin_source_row(
                    route=route,
                    route_id=route_id,
                    diameter_nm=diameter_nm,
                    view=view,
                    seed=seed,
                    particle_kind=particle_kind,
                    distribution_type=distribution_type,
                    row_kind="special_aggregate",
                    aggregate_id=aggregate_id,
                    bin_id=aggregate_id,
                    edge_norm_min=edge_min,
                    edge_norm_max=edge_max,
                    x_norm_min="",
                    x_norm_max="",
                    z_norm_min="",
                    z_norm_max="",
                    members=members,
                    total=total,
                    source_scope=source_scope,
                    source_artifact=source_artifact,
                    source_sha256=source_sha256,
                )
            )
    return rows


def _position_response_bin_source_row(
    *,
    route: tuple[int, int, int],
    route_id: str,
    diameter_nm: int,
    view: str,
    seed: int,
    particle_kind: str,
    distribution_type: str,
    row_kind: str,
    aggregate_id: str,
    bin_id: str,
    edge_norm_min: float | str,
    edge_norm_max: float | str,
    x_norm_min: float | str,
    x_norm_max: float | str,
    z_norm_min: float | str,
    z_norm_max: float | str,
    members: Sequence[Mapping[str, Any]],
    total: int,
    source_scope: str,
    source_artifact: str,
    source_sha256: str,
) -> dict[str, Any]:
    n_events_bin = len(members)
    response_count = sum(1 for event in members if bool(event["response_detected"]))
    sample_status = "empty" if n_events_bin == 0 else "sparse" if n_events_bin < 100 else "adequate"
    return {
        "bin_source_artifact_version": POSITION_RESPONSE_BIN_SOURCE_VERSION,
        "source_scope": source_scope,
        "route_id_nodi": route_id,
        "lambda_nm": route[0],
        "W_nominal_nm": route[1],
        "D_nm": route[2],
        "diameter_nm": diameter_nm,
        "NODI_view": view,
        "seed": seed,
        "particle_kind": particle_kind,
        "distribution_type": distribution_type,
        "row_kind": row_kind,
        "aggregate_id": aggregate_id,
        "bin_id": bin_id,
        "edge_norm_min": _format_optional_number(edge_norm_min),
        "edge_norm_max": _format_optional_number(edge_norm_max),
        "x_norm_min": _format_optional_number(x_norm_min),
        "x_norm_max": _format_optional_number(x_norm_max),
        "z_norm_min": _format_optional_number(z_norm_min),
        "z_norm_max": _format_optional_number(z_norm_max),
        "n_events_total_seed": total,
        "n_events_bin": n_events_bin,
        "response_count_bin": response_count,
        "response_rate_bin": _format_number(response_count / n_events_bin)
        if n_events_bin
        else "",
        "bin_sample_status": sample_status,
        "sparse_bin_flag": str(n_events_bin < 100).lower(),
        "decision_use_allowed": str(sample_status == "adequate").lower(),
        "source_event_rows": ";".join(_value(event, "event_id") for event in members),
        "preflight_only": "true",
        "production_prs_generated": "false",
        "not_qch_weighted": "true",
        "not_yield": "true",
        "not_detection_probability": "true",
        "claim_boundary": PRS_BIN_SOURCE_CLAIM_BOUNDARY,
        "source_artifact": source_artifact,
        "source_sha256": source_sha256,
    }


def _parse_position_response_event(row: Mapping[str, Any]) -> dict[str, Any]:
    x_norm = float(_value(row, "x_norm"))
    z_norm = float(_value(row, "z_norm"))
    return {
        "event_id": _value(row, "event_id"),
        "x_norm": x_norm,
        "z_norm": z_norm,
        "edge_norm": max(abs(x_norm), abs(z_norm)),
        "response_detected": bool(_event_response_bool(row)),
    }


def _nodi_event_float(event: Mapping[str, Any], field: str) -> float | None:
    value = event.get(field)
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _nodi_event_response_detected(event: Mapping[str, Any]) -> bool:
    features = event.get("features")
    if isinstance(features, Mapping):
        try:
            return int(features.get("n_peaks", 0) or 0) > 0
        except (TypeError, ValueError):
            return False
    response = event.get("response_detected")
    if response not in (None, ""):
        parsed = _event_response_bool({"response_detected": response})
        if parsed is not None:
            return parsed
    return bool(event.get("detected_single_channel", False))


def _event_response_bool(row: Mapping[str, Any]) -> bool | None:
    value = _value(row, "response_detected").lower()
    if value in {"true", "1", "yes"}:
        return True
    if value in {"false", "0", "no"}:
        return False
    return None


def _uniform_edges(start: float, stop: float, bins: int) -> list[float]:
    step = (stop - start) / bins
    return [start + step * index for index in range(bins + 1)]


def _in_bin(value: float, low: float, high: float, include_high: bool) -> bool:
    return low <= value <= high if include_high else low <= value < high


def _validate_position_response_bin_source_grain(
    rows: Sequence[Mapping[str, Any]],
    issues: list[str],
) -> None:
    counter: Counter[tuple[str, str, str, str, str, str]] = Counter()
    for row in rows:
        counter[
            (
                _value(row, "route_id_nodi"),
                _value(row, "diameter_nm"),
                _value(row, "NODI_view"),
                _value(row, "seed"),
                _value(row, "distribution_type"),
                _value(row, "bin_id"),
            )
        ] += 1
    for grain, count in counter.items():
        if count > 1:
            issues.append(f"PRS-BINSRC-V12: duplicate bin-source grain {grain}")


def _validate_position_response_bin_source_row_arithmetic(
    rows: Sequence[Mapping[str, Any]],
    issues: list[str],
) -> None:
    groups: dict[tuple[str, str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[
            (
                _value(row, "route_id_nodi"),
                _value(row, "diameter_nm"),
                _value(row, "NODI_view"),
                _value(row, "seed"),
            )
        ].append(row)
    for grain, group_rows in groups.items():
        if len(group_rows) != ROWS_PER_ROUTE_DIAMETER_VIEW:
            issues.append(
                "PRS-BINSRC-V13: rows_per_route_diameter_view_seed mismatch "
                f"for {grain}: expected {ROWS_PER_ROUTE_DIAMETER_VIEW}, got {len(group_rows)}"
            )
            continue
        edge_base = sum(
            1
            for row in group_rows
            if _value(row, "distribution_type") == "edge_norm_1d"
            and _value(row, "row_kind") == "base_bin"
        )
        xz_base = sum(
            1
            for row in group_rows
            if _value(row, "distribution_type") == "xz_norm_2d"
            and _value(row, "row_kind") == "base_bin"
        )
        special = sum(1 for row in group_rows if _value(row, "row_kind") == "special_aggregate")
        expected_special = SPECIAL_AGGREGATE_COUNT_PER_DISTRIBUTION * 2
        if edge_base != EDGE_BASE_BIN_COUNT or xz_base != XZ_BASE_BIN_COUNT or special != expected_special:
            issues.append(
                "PRS-BINSRC-V13: bin arithmetic mismatch for "
                f"{grain}: edge={edge_base}, xz={xz_base}, special={special}"
            )


def _write_runner_launch_plan(
    *,
    output_dir: Path,
    filename: str,
    plan: dict[str, Any],
) -> dict[str, Any]:
    issues = validate_runner_launch_plan(plan)
    if issues:
        raise ContractValidationError("NODI_NEXT_ARTIFACTS_RUNNER_IMPLEMENTATION", issues)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    write_json_atomic(output_path, plan, sort_keys=True)
    result = dict(plan)
    result["launch_plan_path"] = str(output_path)
    result["launch_plan_sha256"] = sha256_file(output_path)
    return result


_RUNNER_IMPLEMENTATION_FALSE_FIELDS: tuple[str, ...] = (
    "runner_execution_authorized",
    "bounded_smoke_execution_authorized",
    "production_generation_authorized",
    "nodi_run_authorized",
    "comsol_run_authorized",
    "joint_route_class_regeneration_authorized",
    "qch_eta_authorized",
    "yield_authorized",
    "winner_authorized",
    "true_w_eff_claim_authorized",
    "measured_geometry_claim_authorized",
    "optical_solver_output_claim_authorized",
    "fabrication_release_authorized",
    "p3_solver_conclusion_authorized",
)

_RUNNER_IMPLEMENTATION_TRUE_FIELDS: tuple[str, ...] = (
    "runner_implementation_authorized_by_phrase",
    "no_runner_execution",
    "no_smoke_execution",
    "no_nodi_run",
    "no_comsol_run",
    "no_production_artifact",
    "no_joint_route_class_regeneration",
    "not_qch_weighted",
    "not_yield",
    "not_winner",
    "not_true_W_eff",
    "not_measured_geometry",
    "not_optical_solver_output",
    "not_fabrication_release",
    "not_P3_solver_conclusion",
)


def _runner_implementation_no_execution_flags() -> dict[str, Any]:
    return {
        "runner_implementation_authorized_by_phrase": True,
        "runner_execution_authorized": False,
        "bounded_smoke_execution_authorized": False,
        "production_generation_authorized": False,
        "nodi_run_authorized": False,
        "comsol_run_authorized": False,
        "joint_route_class_regeneration_authorized": False,
        "qch_eta_authorized": False,
        "yield_authorized": False,
        "winner_authorized": False,
        "true_w_eff_claim_authorized": False,
        "measured_geometry_claim_authorized": False,
        "optical_solver_output_claim_authorized": False,
        "fabrication_release_authorized": False,
        "p3_solver_conclusion_authorized": False,
        "no_runner_execution": True,
        "no_smoke_execution": True,
        "no_nodi_run": True,
        "no_comsol_run": True,
        "no_production_artifact": True,
        "no_joint_route_class_regeneration": True,
        "not_qch_weighted": True,
        "not_yield": True,
        "not_winner": True,
        "not_true_W_eff": True,
        "not_measured_geometry": True,
        "not_optical_solver_output": True,
        "not_fabrication_release": True,
        "not_P3_solver_conclusion": True,
    }


def _bounded_smoke_execution_rows_from_smoke_manifest(
    smoke_rows: Sequence[Mapping[str, str]],
    *,
    artifact_version: str,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for smoke in smoke_rows:
        rows.append(
            {
                "bounded_smoke_execution_artifact_version": (
                    "NODI_NEXT_ARTIFACTS_BOUNDED_SMOKE_EXECUTION_V1"
                ),
                "source_artifact_version": artifact_version,
                "source_smoke_id": smoke["smoke_id"],
                "artifact": smoke["artifact"],
                "smoke_role": smoke["smoke_role"],
                "route_scope": smoke["route_scope"],
                "view_scope": smoke["view_scope"],
                "row_arithmetic": smoke["row_arithmetic"],
                "source_manifest_execution_status": smoke["execution_status"],
                "bounded_smoke_execution_status": BOUNDED_SMOKE_EXECUTION_ROW_STATUS,
                "runner_execution_scope": "bounded_smoke_contract_sidecar_only",
                "allowed_output_status": smoke["allowed_output_status"],
                "claim_boundary": smoke["claim_boundary"],
                "smoke_sidecar_generated": "true",
                "production_artifact_generated": "false",
                "production_generation_performed": "false",
                "full_runner_execution_performed": "false",
                "nodi_run_performed": "false",
                "comsol_run_performed": "false",
                "joint_route_class_regenerated": "false",
                "no_nodi_run": "true",
                "no_comsol_run": "true",
                "no_production_artifact": "true",
                "no_joint_route_class_regeneration": "true",
                "not_qch_weighted": "true",
                "not_yield": "true",
                "not_winner": "true",
                "not_true_W_eff": "true",
                "not_measured_geometry": "true",
                "not_optical_solver_output": "true",
                "not_fabrication_release": "true",
                "not_P3_solver_conclusion": "true",
            }
        )
    return rows


def _production_position_response_blockers(
    *,
    candidate_path: Path | None = None,
    candidate_issue_count: int = 0,
) -> list[dict[str, str]]:
    if candidate_path is not None and candidate_issue_count:
        status = "blocked_invalid_position_response_candidate"
        current_evidence = (
            f"candidate {candidate_path} failed production PRS validation with "
            f"{candidate_issue_count} issue(s)"
        )
        unblock_action = (
            "repair the edge-primary candidate until it passes "
            "validate_position_response_surface_rows with production_table=True "
            "and complete row arithmetic"
        )
    else:
        status = "blocked_missing_numeric_sufficient_position_response_source"
        current_evidence = (
            "smoke, selected-slice, and PLAN_ONLY sources exist, but sparse "
            "or preflight-only rows must not be promoted to production PRS"
        )
        unblock_action = (
            "provide or implement a real PRS event/bin accumulator source, "
            "validate 467 rows per route/diameter/view/seed, then pass the "
            "numeric sufficiency gate or provide a validated edge-primary candidate"
        )
    return [
        {
            "artifact": POSITION_RESPONSE_ARTIFACT,
            "blocker_id": "PRS-PROD-B01",
            "status": status,
            "required_input_or_policy": (
                "event-level or bin-conditioned position-response source with "
                "route/diameter/view/seed/bin response counts and numeric "
                "sufficiency for production PRS, or a separately validated "
                "edge-primary/xz-diagnostic PRS candidate"
            ),
            "current_evidence": current_evidence,
            "unblock_action": unblock_action,
            "claim_boundary": PRS_CLAIM_BOUNDARY,
        }
    ]


def _production_effective_aperture_blockers(
    *,
    descriptor_rows: Sequence[Mapping[str, Any]],
    rank_rows: Sequence[Mapping[str, Any]],
    guardrail_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    selector_counts = _selected_eas_descriptor_counts(descriptor_rows)
    selector_mismatches = {
        f"W{width}/D{depth}": selector_counts[(width, depth)]
        for width, depth in sorted({(width, depth) for _, width, depth in EAS_APPROVED_ROUTE_MATRIX})
        if selector_counts[(width, depth)] != 1
    }
    if selector_mismatches:
        blockers.append(
            {
                "artifact": APERTURE_SURROGATE_ARTIFACT,
                "blocker_id": "EAS-PROD-B01",
                "status": "blocked_selector_policy_not_unique",
                "required_input_or_policy": (
                    "COMSOL-approved selector must choose exactly one descriptor row per W/D"
                ),
                "current_evidence": (
                    "selector matches per W/D: "
                    + "; ".join(f"{key}={count}" for key, count in selector_mismatches.items())
                ),
                "unblock_action": (
                    "repair descriptor inputs or revise selector policy; do not silently fallback"
                ),
                "claim_boundary": EAS_CLAIM_BOUNDARY,
            }
        )

    uniform_rank_grains = {
        (_value(row, "route_id"), _value(row, "NODI_view"))
        for row in rank_rows
        if _value(row, "weighting") == "uniform"
        and _route_tuple_from_row(row, route_field="route_id") in EAS_APPROVED_ROUTE_MATRIX
    }
    expected_rank_grains = {
        (_route_id_from_tuple(route), view)
        for route in EAS_APPROVED_ROUTE_MATRIX
        for view in PRS_APPROVED_VIEWS
    }
    missing_rank = sorted(expected_rank_grains - uniform_rank_grains)
    if missing_rank:
        blockers.append(
            {
                "artifact": APERTURE_SURROGATE_ARTIFACT,
                "blocker_id": "EAS-PROD-B02",
                "status": "blocked_missing_uniform_rank_source_rows",
                "required_input_or_policy": (
                    "uniform weighting rank/proxy rows for every EAS route/view grain"
                ),
                "current_evidence": "; ".join(f"{route}|{view}" for route, view in missing_rank),
                "unblock_action": "refresh or repair NODI_EVIDENCE_CONNECTOR_fullgrid_route_stability.csv",
                "claim_boundary": EAS_CLAIM_BOUNDARY,
            }
        )

    guardrail_grains = {
        _route_tuple_from_row(row)
        for row in guardrail_rows
        if _route_tuple_from_row(row) in EAS_APPROVED_ROUTE_MATRIX
    }
    missing_guardrail = sorted(EAS_APPROVED_ROUTE_MATRIX - guardrail_grains)
    if missing_guardrail:
        blockers.append(
            {
                "artifact": APERTURE_SURROGATE_ARTIFACT,
                "blocker_id": "EAS-PROD-B03",
                "status": "blocked_missing_guardrail_rows",
                "required_input_or_policy": "guardrail row for every EAS route grain",
                "current_evidence": "; ".join(_route_id_from_tuple(route) for route in missing_guardrail),
                "unblock_action": "refresh or repair NODI_REFERENCE_GUARDRAIL_TABLE.csv",
                "claim_boundary": EAS_CLAIM_BOUNDARY,
            }
        )
    return blockers


def build_effective_aperture_first_production_rows(
    *,
    geometry_descriptor_path: Path,
    rank_source_path: Path,
    guardrail_table_path: Path,
) -> list[dict[str, Any]]:
    """Build first-production EAS rows using the COMSOL-approved selector policy."""
    descriptor_rows = read_csv_rows(geometry_descriptor_path)
    rank_rows = read_csv_rows(rank_source_path)
    guardrail_rows = read_csv_rows(guardrail_table_path)
    blockers = _production_effective_aperture_blockers(
        descriptor_rows=descriptor_rows,
        rank_rows=rank_rows,
        guardrail_rows=guardrail_rows,
    )
    if blockers:
        raise ContractValidationError(APERTURE_SURROGATE_ARTIFACT, [b["status"] for b in blockers])

    descriptor_by_width_depth = _selected_eas_descriptors(descriptor_rows)
    rank_by_route_view = _uniform_rank_rows(rank_rows)
    guardrail_by_route = _guardrail_rows_by_route(guardrail_rows)
    source_hash = _combined_source_sha256(
        [
            sha256_file(geometry_descriptor_path),
            sha256_file(rank_source_path),
            sha256_file(guardrail_table_path),
            json.dumps(EAS_DESCRIPTOR_SELECTOR_POLICY, sort_keys=True),
            ",".join(EAS_FIRST_PRODUCTION_MODES),
        ]
    )
    source_artifact = (
        f"{rank_source_path};{geometry_descriptor_path};{guardrail_table_path};"
        "selector_policy=process_state:nominal_smooth_geometry,"
        "angle_convention:sidewall_angle_from_substrate_plane_90deg_vertical,"
        "sidewall_deg:85.0"
    )

    rows: list[dict[str, Any]] = []
    for route in sorted(EAS_APPROVED_ROUTE_MATRIX):
        route_id = _route_id_from_tuple(route)
        descriptor = descriptor_by_width_depth[(route[1], route[2])]
        guardrail = guardrail_by_route[route]
        for view in sorted(PRS_APPROVED_VIEWS):
            rank_row = rank_by_route_view[(route_id, view)]
            for mode in EAS_FIRST_PRODUCTION_MODES:
                w_eff = _eas_w_eff_for_mode(descriptor, mode)
                is_nominal = mode == "nominal_width"
                nonpositive = w_eff <= 0
                eta_selected = _value(rank_row, "eta_selected_proxy") if is_nominal else ""
                eta_all = _value(rank_row, "eta_all_proxy") if is_nominal else ""
                rows.append(
                    {
                        "aperture_artifact_version": APERTURE_SURROGATE_VERSION,
                        "route_id_nodi": route_id,
                        "lambda_nm": route[0],
                        "W_nominal_nm": route[1],
                        "D_nm": route[2],
                        "NODI_view": view,
                        "weighting_basis": EAS_WEIGHTING_BASIS,
                        "aperture_surrogate_mode": mode,
                        "W_eff_surrogate_nm": _format_number(w_eff),
                        "delta_W_eff_surrogate_nm": _format_number(w_eff - route[1]),
                        "source_geometry_descriptor_id": _value(
                            descriptor,
                            "route_geometry_id_comsol",
                        ),
                        "source_geometry_descriptor_sha": GEOMETRY_DESCRIPTOR_SHA256,
                        "descriptor_evidence_class": "nominal/design-state"
                        if is_nominal
                        else "surrogate/simulated geometry rule",
                        "rank_source": EAS_RANK_SOURCE,
                        "recommendation_eligible_rank_source": EAS_RECOMMENDATION_RANK_SOURCE,
                        "guardrail_status": _value(guardrail, "guardrail_status"),
                        "eta_selected_proxy_under_surrogate": eta_selected,
                        "eta_all_proxy_under_surrogate": eta_all,
                        "rank_under_surrogate": "",
                        "rank_flip_flag": "false",
                        "candidate_family_flip_flag": "false",
                        "eta_selected_relative_change": "0" if is_nominal and eta_selected else "",
                        "eta_all_relative_change": "0" if is_nominal and eta_all else "",
                        "guardrail_status_change_flag": "false",
                        "W_eff_mode_sensitivity_class": "stable"
                        if is_nominal
                        else "solver_required",
                        "solver_contract_trigger_flag": "false" if is_nominal else "true",
                        "solver_contract_trigger_reason": "none"
                        if is_nominal
                        else (
                            "nonpositive_surrogate_aperture"
                            if nonpositive
                            else "geometry_complexity"
                        ),
                        "not_true_W_eff": "true",
                        "not_measured_geometry": "true",
                        "not_optical_solver_output": "true",
                        "not_fabrication_release": "true",
                        "not_yield": "true",
                        "not_winner": "true",
                        "claim_boundary": EAS_CLAIM_BOUNDARY,
                        "source_artifact": source_artifact,
                        "source_sha256": source_hash,
                    }
                )
    issues = validate_effective_aperture_surrogate_rows(rows)
    if issues:
        raise ContractValidationError(APERTURE_SURROGATE_ARTIFACT, issues)
    return rows


def _selected_eas_descriptor_counts(
    descriptor_rows: Sequence[Mapping[str, Any]],
) -> Counter[tuple[int, int]]:
    counts: Counter[tuple[int, int]] = Counter()
    for row in descriptor_rows:
        if _matches_eas_descriptor_selector(row):
            width = _int_like(row, "W_nominal_nm")
            depth = _int_like(row, "D_nm")
            if width is not None and depth is not None:
                counts[(width, depth)] += 1
    return counts


def _selected_eas_descriptors(
    descriptor_rows: Sequence[Mapping[str, Any]],
) -> dict[tuple[int, int], Mapping[str, Any]]:
    selected: dict[tuple[int, int], Mapping[str, Any]] = {}
    for row in descriptor_rows:
        if not _matches_eas_descriptor_selector(row):
            continue
        width = _int_like(row, "W_nominal_nm")
        depth = _int_like(row, "D_nm")
        if width is not None and depth is not None:
            selected[(width, depth)] = row
    return selected


def _matches_eas_descriptor_selector(row: Mapping[str, Any]) -> bool:
    if _value(row, "process_state") != EAS_DESCRIPTOR_SELECTOR_POLICY["process_state"]:
        return False
    if _value(row, "angle_convention") != EAS_DESCRIPTOR_SELECTOR_POLICY["angle_convention"]:
        return False
    if _value(row, "route_geometry_id_comsol_version") != GEOMETRY_DESCRIPTOR_VERSION:
        return False
    if _value(row, "claim_boundary") != GEOMETRY_DESCRIPTOR_CLAIM_BOUNDARY:
        return False
    sidewall = _float_field_for_selection(row, "sidewall_deg")
    return sidewall == 85.0


def _uniform_rank_rows(
    rank_rows: Sequence[Mapping[str, Any]],
) -> dict[tuple[str, str], Mapping[str, Any]]:
    return {
        (_value(row, "route_id"), _value(row, "NODI_view")): row
        for row in rank_rows
        if _value(row, "weighting") == "uniform"
        and _route_tuple_from_row(row, route_field="route_id") in EAS_APPROVED_ROUTE_MATRIX
    }


def _guardrail_rows_by_route(
    guardrail_rows: Sequence[Mapping[str, Any]],
) -> dict[tuple[int, int, int], Mapping[str, Any]]:
    return {
        route: row
        for row in guardrail_rows
        if (route := _route_tuple_from_row(row)) in EAS_APPROVED_ROUTE_MATRIX
    }


def _eas_w_eff_for_mode(descriptor: Mapping[str, Any], mode: str) -> float:
    if mode == "nominal_width":
        return float(_value(descriptor, "W_nominal_nm"))
    if mode == "W_bottom_conservative":
        return float(_value(descriptor, "W_bottom_um")) * 1000.0
    if mode == "min_aperture_conservative":
        return float(_value(descriptor, "min_aperture_nm"))
    if mode == "top_bottom_average_heuristic":
        return (
            (float(_value(descriptor, "W_top_um")) + float(_value(descriptor, "W_bottom_um")))
            / 2.0
            * 1000.0
        )
    raise ValueError(f"unsupported first-production EAS mode: {mode}")


def _combined_source_sha256(parts: Sequence[str]) -> str:
    h = hashlib.sha256()
    for part in parts:
        h.update(part.encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def _format_number(value: float) -> str:
    return f"{value:.12g}"


def _format_optional_number(value: float | str) -> str:
    if value == "":
        return ""
    return _format_number(float(value))


def _float_field_for_selection(row: Mapping[str, Any], field: str) -> float | None:
    try:
        return float(_value(row, field))
    except ValueError:
        return None


def _int_like(row: Mapping[str, Any], field: str) -> int | None:
    value = _value(row, field)
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def _route_tuple_from_row(
    row: Mapping[str, Any],
    *,
    route_field: str | None = None,
) -> tuple[int, int, int] | None:
    if route_field is not None:
        match = ROUTE_RE.match(_value(row, route_field))
        if not match:
            return None
        return (
            int(match.group("lambda_nm")),
            int(match.group("W_nominal_nm")),
            int(match.group("D_nm")),
        )
    lambda_nm = _int_like(row, "lambda_nm")
    width_nm = _int_like(row, "W_nominal_nm")
    depth_nm = _int_like(row, "D_nm")
    if lambda_nm is None or width_nm is None or depth_nm is None:
        return None
    return (lambda_nm, width_nm, depth_nm)


def _route_id_from_tuple(route: tuple[int, int, int]) -> str:
    return f"{route[0]}/W{route[1]}/D{route[2]}"


_PRODUCTION_GENERATION_FALSE_FIELDS: tuple[str, ...] = (
    "nodi_run_performed",
    "comsol_run_performed",
    "joint_route_class_regenerated",
    "full_runner_execution_performed",
)

_PRODUCTION_GENERATION_TRUE_FIELDS: tuple[str, ...] = (
    "no_comsol_run",
    "no_joint_route_class_regeneration",
    "not_qch_weighted",
    "not_yield",
    "not_winner",
    "not_true_W_eff",
    "not_measured_geometry",
    "not_optical_solver_output",
    "not_fabrication_release",
    "not_P3_solver_conclusion",
)


_BOUNDED_SMOKE_EXECUTION_FALSE_FIELDS: tuple[str, ...] = (
    "production_generation_authorized",
    "production_generation_performed",
    "full_runner_execution_authorized",
    "full_runner_execution_performed",
    "nodi_run_authorized",
    "nodi_run_performed",
    "comsol_run_authorized",
    "comsol_run_performed",
    "joint_route_class_regeneration_authorized",
    "joint_route_class_regenerated",
)

_BOUNDED_SMOKE_EXECUTION_TRUE_FIELDS: tuple[str, ...] = (
    "bounded_smoke_sidecar_only",
    "no_nodi_run",
    "no_comsol_run",
    "no_production_artifact",
    "no_joint_route_class_regeneration",
    "not_qch_weighted",
    "not_yield",
    "not_winner",
    "not_true_W_eff",
    "not_measured_geometry",
    "not_optical_solver_output",
    "not_fabrication_release",
    "not_P3_solver_conclusion",
)

_BOUNDED_SMOKE_MANIFEST_FALSE_FIELDS: tuple[str, ...] = (
    "production_artifact_generated",
    "production_generation_performed",
    "full_runner_execution_performed",
    "nodi_run_performed",
    "comsol_run_performed",
    "joint_route_class_regenerated",
)

_BOUNDED_SMOKE_MANIFEST_TRUE_FIELDS: tuple[str, ...] = (
    "smoke_sidecar_generated",
    "no_nodi_run",
    "no_comsol_run",
    "no_production_artifact",
    "no_joint_route_class_regeneration",
    "not_qch_weighted",
    "not_yield",
    "not_winner",
    "not_true_W_eff",
    "not_measured_geometry",
    "not_optical_solver_output",
    "not_fabrication_release",
    "not_P3_solver_conclusion",
)


_BOUNDED_SMOKE_READINESS_FALSE_FIELDS: tuple[str, ...] = (
    "authorization_phrase_already_received",
    "bounded_smoke_execution_authorized",
    "runner_execution_authorized",
    "production_generation_authorized",
    "nodi_run_authorized",
    "comsol_run_authorized",
    "joint_route_class_regeneration_authorized",
    "qch_eta_authorized",
    "yield_authorized",
    "winner_authorized",
    "true_w_eff_claim_authorized",
    "measured_geometry_claim_authorized",
    "optical_solver_output_claim_authorized",
    "fabrication_release_authorized",
    "p3_solver_conclusion_authorized",
)

_BOUNDED_SMOKE_READINESS_TRUE_FIELDS: tuple[str, ...] = (
    "no_runner_execution",
    "no_smoke_execution",
    "no_nodi_run",
    "no_comsol_run",
    "no_production_artifact",
    "no_joint_route_class_regeneration",
    "not_qch_weighted",
    "not_yield",
    "not_winner",
    "not_true_W_eff",
    "not_measured_geometry",
    "not_optical_solver_output",
    "not_fabrication_release",
    "not_P3_solver_conclusion",
)


def _read_json_mapping(path: Path, label: str, issues: list[str]) -> dict[str, Any] | None:
    if not path.exists():
        issues.append(f"{label}: missing {path}")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        issues.append(f"{label}: unreadable JSON: {exc}")
        return None
    if not isinstance(payload, dict):
        issues.append(f"{label}: JSON payload is not an object")
        return None
    return payload


def _source_file_entry(label: str, path: Path) -> dict[str, str]:
    return {
        "label": label,
        "path": str(path),
        "exists": str(path.exists()).lower(),
        "sha256": sha256_file(path) if path.exists() else "",
    }


_NO_EXECUTION_TRUE_FIELDS: tuple[str, ...] = (
    "no_runner_implementation",
    "no_runner_execution",
    "no_smoke_execution",
    "no_nodi_run",
    "no_comsol_run",
    "no_production_artifact",
    "no_joint_route_class_regeneration",
    "not_qch_weighted",
    "not_yield",
    "not_winner",
    "not_true_W_eff",
    "not_measured_geometry",
    "not_optical_solver_output",
    "not_fabrication_release",
    "not_P3_solver_conclusion",
)

_AUTHORIZATION_GATE_FALSE_FIELDS: tuple[str, ...] = (
    "runner_implementation_authorized",
    "runner_execution_authorized",
    "bounded_smoke_execution_authorized",
    "production_generation_authorized",
    "nodi_run_authorized",
    "comsol_run_authorized",
    "joint_route_class_regeneration_authorized",
    "qch_eta_authorized",
    "yield_authorized",
    "winner_authorized",
    "true_w_eff_claim_authorized",
    "measured_geometry_claim_authorized",
    "optical_solver_output_claim_authorized",
    "fabrication_release_authorized",
    "p3_solver_conclusion_authorized",
    "authorization_phrase_already_received",
)

_AUTHORIZATION_GATE_TRUE_FIELDS: tuple[str, ...] = (
    "contract_sidecar_writing_authorized",
    "explicit_future_authorization_required",
    *_NO_EXECUTION_TRUE_FIELDS,
)


def _authorization_gate_source_files(
    *,
    smoke_manifest_dir: Path,
    plan_blueprint_dir: Path,
    preflight_report_path: Path | None,
) -> list[dict[str, str]]:
    paths = [
        smoke_manifest_dir / PRS_SMOKE_MANIFEST_FILENAME,
        smoke_manifest_dir / EAS_SMOKE_MANIFEST_FILENAME,
        smoke_manifest_dir / NEXT_ARTIFACTS_SMOKE_INDEX_FILENAME,
        smoke_manifest_dir / NEXT_ARTIFACTS_SMOKE_METADATA_FILENAME,
        plan_blueprint_dir / PRS_PLAN_BLUEPRINT_FILENAME,
        plan_blueprint_dir / EAS_PLAN_BLUEPRINT_FILENAME,
        plan_blueprint_dir / NEXT_ARTIFACTS_PLAN_BLUEPRINT_INDEX_FILENAME,
        plan_blueprint_dir / NEXT_ARTIFACTS_PLAN_BLUEPRINT_METADATA_FILENAME,
    ]
    if preflight_report_path is not None:
        paths.append(preflight_report_path)
    rows: list[dict[str, str]] = []
    for path in paths:
        rows.append(
            {
                "path": str(path),
                "exists": str(path.exists()).lower(),
                "sha256": sha256_file(path) if path.exists() else "",
            }
        )
    return rows


def _split_scope_values(scope: str) -> list[str]:
    if "not applicable" in scope or "descriptor rows" in scope:
        return []
    if " only" in scope:
        scope = scope.split(" only", 1)[0]
    return [part.strip() for part in scope.split(";") if part.strip()]


def _validate_exact_smoke_rows(
    actual_rows: Sequence[Mapping[str, Any]],
    expected_rows: Sequence[Mapping[str, Any]],
    label: str,
    issues: list[str],
) -> None:
    if len(actual_rows) != len(expected_rows):
        issues.append(f"{label}: row count mismatch expected {len(expected_rows)} got {len(actual_rows)}")
        return
    for index, (actual, expected) in enumerate(zip(actual_rows, expected_rows), start=1):
        actual_fields = set(actual)
        expected_fields = set(expected)
        if actual_fields != expected_fields:
            issues.append(
                f"{label}: row {index} field set differs from canonical design-only manifest"
            )
            continue
        actual_dict = {key: _value(actual, key) for key in expected}
        expected_dict = {key: _value(expected, key) for key in expected}
        if actual_dict != expected_dict:
            issues.append(f"{label}: row {index} differs from canonical design-only manifest")


def _require_fields(
    row: Mapping[str, Any],
    required_fields: Sequence[str],
    rule_id: str,
    row_index: int,
    issues: list[str],
) -> None:
    for field in required_fields:
        if field not in row:
            _issue(issues, row_index, rule_id, f"missing required field {field}")


def _validate_position_bin(
    row: Mapping[str, Any],
    row_index: int,
    issues: list[str],
) -> None:
    distribution = _value(row, "distribution_type")
    row_kind = _value(row, "row_kind")
    aggregate_id = _value(row, "aggregate_id")
    if row_kind == "special_aggregate":
        if aggregate_id not in PRS_APPROVED_AGGREGATES:
            _issue(issues, row_index, "PRS-V10", "invalid special aggregate_id")
        return
    if row_kind == "base_bin" and aggregate_id not in {"", "blank"}:
        _issue(issues, row_index, "PRS-V10", "base_bin aggregate_id must be blank")

    if distribution == "edge_norm_1d":
        edge_min = _float_field(row, "edge_norm_min", row_index, "PRS-V08", issues)
        edge_max = _float_field(row, "edge_norm_max", row_index, "PRS-V08", issues)
        if edge_min is not None and edge_max is not None:
            if not (0.0 <= edge_min < edge_max <= 1.0):
                _issue(issues, row_index, "PRS-V08", "edge_norm_1d bounds outside [0,1]")
    elif distribution == "xz_norm_2d":
        for low_field, high_field in (("x_norm_min", "x_norm_max"), ("z_norm_min", "z_norm_max")):
            low = _float_field(row, low_field, row_index, "PRS-V09", issues)
            high = _float_field(row, high_field, row_index, "PRS-V09", issues)
            if low is not None and high is not None:
                if not (-1.0 <= low < high <= 1.0):
                    _issue(issues, row_index, "PRS-V09", f"{low_field}/{high_field} outside [-1,1]")


def _sidewall_v2_marker_active(
    row: Mapping[str, Any],
    *,
    explicit_marker_fields: frozenset[str],
    expected_artifact_version: str,
) -> bool:
    if _value(row, "channel_cross_section_model") == "trapezoid_tapered_sidewalls":
        return True
    if _value(row, "artifact_version") == expected_artifact_version:
        return True
    return any(field in row for field in explicit_marker_fields if field != "artifact_version")


def _validate_position_response_sidewall_v2_fields(
    row: Mapping[str, Any],
    row_index: int,
    issues: list[str],
) -> None:
    if not _sidewall_v2_marker_active(
        row,
        explicit_marker_fields=PRS_SIDEWALL_V2_EXPLICIT_MARKER_FIELDS,
        expected_artifact_version=PRS_SIDEWALL_V2_ARTIFACT_VERSION,
    ):
        return

    _require_fields(row, PRS_SIDEWALL_V2_REQUIRED_FIELDS, "PRS-SIDEWALL-V2", row_index, issues)
    _validate_sidewall_v2_source_geometry_descriptor_binding(
        row,
        row_index,
        "PRS-SIDEWALL-V2",
        issues,
    )
    _validate_sidewall_v2_source_grain_binding(
        row,
        row_index,
        "PRS-SIDEWALL-V2",
        issues,
        check_prs_bin_fields=True,
    )
    _validate_sidewall_v2_acceptance_guards(row, row_index, "PRS-SIDEWALL-V2", issues)
    _validate_sidewall_v2_package_d_precheck_binding(
        row,
        row_index,
        "PRS-SIDEWALL-V2",
        issues,
        expected_family="prs",
    )
    _validate_sidewall_v2_artifact_metadata(
        row,
        row_index,
        "PRS-SIDEWALL-V2",
        issues,
        expected_artifact_version=PRS_SIDEWALL_V2_ARTIFACT_VERSION,
    )
    channel_model = _value(row, "channel_cross_section_model")
    if channel_model not in {"ideal_rectangle", "trapezoid_tapered_sidewalls"}:
        _issue(
            issues,
            row_index,
            "PRS-SIDEWALL-V2",
            f"invalid channel_cross_section_model={channel_model}",
        )
    if _value(row, "rank_under_surrogate"):
        _issue(
            issues,
            row_index,
            "PRS-SIDEWALL-V2",
            "sidewall PRS v2 row must not use rank_under_surrogate",
        )
    _validate_sidewall_v2_observation_cache_context(
        row,
        row_index,
        "PRS-SIDEWALL-V2",
        issues,
        require_trapezoid_signature=channel_model == "trapezoid_tapered_sidewalls",
    )
    _validate_prs_sidewall_v2_initial_position_signature_context(
        row,
        row_index,
        issues,
    )
    _validate_sidewall_v2_runtime_propagation_guards(
        row,
        row_index,
        "PRS-SIDEWALL-V2",
        issues,
    )
    _validate_sidewall_v2_geometry_propagation_scope(
        row,
        row_index,
        "PRS-SIDEWALL-V2",
        issues,
        expected_propagated_scope=PRS_SIDEWALL_V2_PROPAGATED_SCOPE,
    )
    _validate_sidewall_v2_trajectory_guards(row, row_index, "PRS-SIDEWALL-V2", issues)
    geometry_status = _value(row, "geometry_propagation_status")
    if geometry_status not in PRS_SIDEWALL_V2_GEOMETRY_STATUS_ALLOWED:
        _issue(
            issues,
            row_index,
            "PRS-SIDEWALL-V2",
            f"invalid geometry_propagation_status={geometry_status}",
        )
    if channel_model == "trapezoid_tapered_sidewalls":
        _validate_sidewall_v2_descriptor_context(row, row_index, "PRS-SIDEWALL-V2", issues)
        if not _value(row, "cross_section_geometry_version"):
            _issue(
                issues,
                row_index,
                "PRS-SIDEWALL-V2",
                "trapezoid row missing cross_section_geometry_version",
            )
        sampler_model = _value(row, "sampler_geometry_model").lower()
        if "rect" in sampler_model and "trapezoid" not in sampler_model:
            _issue(
                issues,
                row_index,
                "PRS-SIDEWALL-V2",
                "trapezoid row uses rectangular sampler geometry",
            )
        flow_profile_model = _value(row, "flow_profile_model")
        if flow_profile_model in {"rect_series", "parabolic_rect"}:
            _issue(
                issues,
                row_index,
                "PRS-SIDEWALL-V2",
                f"trapezoid row uses rectangular flow_profile_model={flow_profile_model}",
            )
        for field in ("trajectory_boundary_model", "wall_distance_model"):
            value = _value(row, field).lower()
            if "rect" in value and "trapezoid" not in value:
                _issue(
                    issues,
                    row_index,
                    "PRS-SIDEWALL-V2",
                    f"trapezoid row uses rectangular {field}",
                )

    diameter_nm = _float_field(row, "diameter_nm", row_index, "PRS-SIDEWALL-V2", issues)
    particle_radius_nm = _float_field(
        row,
        "particle_radius_nm",
        row_index,
        "PRS-SIDEWALL-V2",
        issues,
    )
    if diameter_nm is not None and particle_radius_nm is not None:
        _validate_close(
            particle_radius_nm,
            0.5 * diameter_nm,
            row_index,
            "PRS-SIDEWALL-V2",
            "particle_radius_nm",
            issues,
        )
    _validate_sidewall_tail_particle_support_guard(
        row,
        row_index,
        diameter_nm=diameter_nm,
        particle_radius_nm=particle_radius_nm,
        issues=issues,
    )
    local_geometry: dict[str, float] = {}
    for field in (
        "x_nm",
        "u_nm",
        "z_nm",
        "x_left_nm",
        "x_right_nm",
        "x_center_nm",
        "local_width_nm",
        "local_half_width_nm",
        "x_local_norm",
        "u_norm",
        "d_top_nm",
        "d_bottom_nm",
        "d_side_left_nm",
        "d_side_right_nm",
        "d_nearest_wall_nm",
        "surface_gap_for_particle_nm",
        "bin_accessible_area_fraction",
    ):
        value = _float_field(row, field, row_index, "PRS-SIDEWALL-V2", issues)
        if value is not None:
            local_geometry[field] = value
    depth_nm = _float_field(row, "D_nm", row_index, "PRS-SIDEWALL-V2", issues)
    if depth_nm is not None:
        local_geometry["D_nm"] = depth_nm
    for field in ("W_top_nm", "sidewall_deg_comsol"):
        if _value(row, field):
            value = _float_field(row, field, row_index, "PRS-SIDEWALL-V2", issues)
            if value is not None:
                local_geometry[field] = value
    _validate_enum(
        row,
        "nearest_wall_id",
        PRS_SIDEWALL_V2_NEAREST_WALL_IDS,
        row_index,
        "PRS-SIDEWALL-V2",
        issues,
    )
    nearest_wall_id = _value(row, "nearest_wall_id")
    _validate_sidewall_local_geometry(
        row_index,
        local_geometry,
        nearest_wall_id=nearest_wall_id,
        particle_radius_nm=particle_radius_nm,
        issues=issues,
    )

    bin_accessible = _bool_field(row, "bin_accessible", row_index, "PRS-SIDEWALL-V2", issues)
    neighbor_fill_used = _bool_field(
        row,
        "neighbor_fill_used",
        row_index,
        "PRS-SIDEWALL-V2",
        issues,
    )
    if neighbor_fill_used:
        _issue(
            issues,
            row_index,
            "PRS-SIDEWALL-V2",
            "sidewall PRS row uses neighbor fill",
        )
    support_status = _value(row, "bin_particle_center_support_status")
    if support_status not in PRS_SIDEWALL_V2_PARTICLE_SUPPORT_STATUS:
        _issue(
            issues,
            row_index,
            "PRS-SIDEWALL-V2",
            f"invalid bin_particle_center_support_status={support_status}",
        )
    decision_allowed = _bool_field(
        row,
        "decision_use_allowed",
        row_index,
        "PRS-SIDEWALL-V2",
        issues,
    )
    if (bin_accessible is False or support_status == "blocked") and decision_allowed:
        _issue(
            issues,
            row_index,
            "PRS-SIDEWALL-V2",
            "blocked sidewall bin is decision-use allowed",
        )
    if bin_accessible is False and not _value(row, "blocked_reason"):
        _issue(
            issues,
            row_index,
            "PRS-SIDEWALL-V2",
            "inaccessible sidewall bin lacks blocked_reason",
        )
    _validate_sidewall_blocked_bin_response_values(
        row,
        row_index,
        bin_accessible=bin_accessible,
        support_status=support_status,
        issues=issues,
    )
    _validate_sidewall_propagation_status_usage(
        row,
        row_index,
        channel_model=channel_model,
        geometry_status=geometry_status,
        bin_accessible=bin_accessible,
        support_status=support_status,
        decision_allowed=decision_allowed,
        issues=issues,
    )


def _validate_sidewall_v2_source_geometry_descriptor_binding(
    row: Mapping[str, Any],
    row_index: int,
    rule_id: str,
    issues: list[str],
) -> None:
    if not _value(row, "source_geometry_descriptor_id"):
        _issue(issues, row_index, rule_id, "source_geometry_descriptor_id is blank")
    _validate_source_hash(
        row,
        field="source_geometry_descriptor_sha",
        row_index=row_index,
        rule_id=rule_id,
        issues=issues,
        allow_pending=False,
    )


def _validate_sidewall_v2_source_grain_binding(
    row: Mapping[str, Any],
    row_index: int,
    rule_id: str,
    issues: list[str],
    *,
    check_prs_bin_fields: bool,
) -> None:
    _require_fields(
        row,
        SIDEWALL_V2_SOURCE_GRAIN_REQUIRED_FIELDS,
        rule_id,
        row_index,
        issues,
    )
    for field in SIDEWALL_V2_SOURCE_GRAIN_REQUIRED_FIELDS:
        if not _value(row, field):
            _issue(issues, row_index, rule_id, f"{field} is blank")
    if check_prs_bin_fields:
        _require_fields(
            row,
            PRS_SIDEWALL_V2_SOURCE_BIN_REQUIRED_FIELDS,
            rule_id,
            row_index,
            issues,
        )
        for field in PRS_SIDEWALL_V2_SOURCE_BIN_REQUIRED_FIELDS:
            if not _value(row, field):
                _issue(issues, row_index, rule_id, f"{field} is blank")
    _validate_optional_exact_source_field(
        row,
        row_index,
        rule_id,
        issues,
        source_field="source_route_id_nodi",
        target_field="route_id_nodi",
    )
    for source_field in ("source_D_nm", "source_depth_nm"):
        _validate_optional_numeric_source_field(
            row,
            row_index,
            rule_id,
            issues,
            source_field=source_field,
            target_field="D_nm",
        )
    if not check_prs_bin_fields:
        return
    for source_field, target_field in (
        ("source_distribution_type", "distribution_type"),
        ("source_bin_basis", "bin_basis"),
        ("source_bin_id", "bin_id"),
    ):
        _validate_optional_exact_source_field(
            row,
            row_index,
            rule_id,
            issues,
            source_field=source_field,
            target_field=target_field,
        )


def _validate_optional_exact_source_field(
    row: Mapping[str, Any],
    row_index: int,
    rule_id: str,
    issues: list[str],
    *,
    source_field: str,
    target_field: str,
) -> None:
    source_value = _value(row, source_field)
    if not source_value:
        return
    target_value = _value(row, target_field)
    if source_value != target_value:
        _issue(
            issues,
            row_index,
            rule_id,
            f"{source_field}={source_value} does not match {target_field}={target_value}",
        )


def _validate_optional_numeric_source_field(
    row: Mapping[str, Any],
    row_index: int,
    rule_id: str,
    issues: list[str],
    *,
    source_field: str,
    target_field: str,
) -> None:
    source_value = _value(row, source_field)
    if not source_value:
        return
    target_value = _value(row, target_field)
    try:
        source_float = float(source_value)
        target_float = float(target_value)
    except ValueError:
        _issue(
            issues,
            row_index,
            rule_id,
            f"{source_field} or {target_field} is not numeric for source grain binding",
        )
        return
    if not math.isclose(source_float, target_float, rel_tol=1.0e-9, abs_tol=1.0e-6):
        _issue(
            issues,
            row_index,
            rule_id,
            f"{source_field}={source_value} does not match {target_field}={target_value}",
        )


def _validate_sidewall_v2_descriptor_context(
    row: Mapping[str, Any],
    row_index: int,
    rule_id: str,
    issues: list[str],
) -> None:
    _require_fields(
        row,
        SIDEWALL_V2_DESCRIPTOR_CONTEXT_REQUIRED_FIELDS,
        rule_id,
        row_index,
        issues,
    )
    _validate_enum(
        row,
        "sidewall_angle_convention",
        DESCRIPTOR_V2_SIDEWALL_ANGLE_CONVENTIONS,
        row_index,
        rule_id,
        issues,
    )
    _validate_constant(
        row,
        "angle_conversion_formula_id",
        DESCRIPTOR_V2_ANGLE_CONVERSION_FORMULA_ID,
        row_index,
        rule_id,
        issues,
    )
    _validate_enum(row, "W_top_semantics", DESCRIPTOR_V2_W_TOP_SEMANTICS, row_index, rule_id, issues)
    _validate_enum(row, "closure_status", DESCRIPTOR_V2_CLOSURE_STATUS, row_index, rule_id, issues)
    _validate_enum(row, "closure_policy", DESCRIPTOR_V2_CLOSURE_POLICY, row_index, rule_id, issues)
    _validate_enum(
        row,
        "runtime_guard_status",
        SIDEWALL_V2_RUNTIME_GUARD_STATUS_ALLOWED,
        row_index,
        rule_id,
        issues,
    )
    _validate_enum(
        row,
        "geometry_claim_level",
        SIDEWALL_V2_GEOMETRY_CLAIM_LEVEL_ALLOWED,
        row_index,
        rule_id,
        issues,
    )
    _validate_enum(
        row,
        "metrology_status",
        SIDEWALL_V2_METROLOGY_STATUS_ALLOWED,
        row_index,
        rule_id,
        issues,
    )
    _validate_source_hash(
        row,
        field="geometry_profile_sha256",
        row_index=row_index,
        rule_id=rule_id,
        issues=issues,
        allow_pending=False,
    )
    if not _value(row, "geometry_profile_source"):
        _issue(issues, row_index, rule_id, "geometry_profile_source is blank")

    sidewall_deg = _float_field(row, "sidewall_deg_comsol", row_index, rule_id, issues)
    taper_deg = _float_field(row, "sidewall_taper_angle_deg_nodi", row_index, rule_id, issues)
    if sidewall_deg is not None and taper_deg is not None:
        if not math.isclose(sidewall_deg + taper_deg, 90.0, abs_tol=1.0e-6):
            _issue(
                issues,
                row_index,
                rule_id,
                "sidewall_deg_comsol and sidewall_taper_angle_deg_nodi are not complementary",
            )

    w_top_nm = _float_field(row, "W_top_nm", row_index, rule_id, issues)
    _validate_descriptor_v2_runtime_top_binding(
        row,
        row_index,
        w_top_nm,
        issues,
        rule_id,
    )
    depth_nm = _float_field(row, "D_nm", row_index, rule_id, issues)
    w_bottom_unclipped_nm = _float_field(
        row,
        "W_bottom_unclipped_nm",
        row_index,
        rule_id,
        issues,
    )
    w_bottom_runtime_clipped_nm = _float_field(
        row,
        "W_bottom_runtime_clipped_nm",
        row_index,
        rule_id,
        issues,
    )
    if (
        sidewall_deg is not None
        and w_top_nm is not None
        and depth_nm is not None
        and w_bottom_unclipped_nm is not None
    ):
        tan_theta = math.tan(math.radians(sidewall_deg))
        if abs(tan_theta) <= 1.0e-12:
            _issue(issues, row_index, rule_id, "sidewall_deg_comsol has zero tangent")
        else:
            expected_bottom = w_top_nm - 2.0 * depth_nm / tan_theta
            if not math.isclose(
                w_bottom_unclipped_nm,
                expected_bottom,
                rel_tol=1.0e-9,
                abs_tol=5.0e-2,
            ):
                _issue(
                    issues,
                    row_index,
                    rule_id,
                    "W_bottom_unclipped_nm does not match sidewall formula",
                )
    if (
        w_bottom_unclipped_nm is not None
        and w_bottom_runtime_clipped_nm is not None
    ):
        expected_runtime_bottom = max(w_bottom_unclipped_nm, 0.0)
        if not math.isclose(
            w_bottom_runtime_clipped_nm,
            expected_runtime_bottom,
            rel_tol=1.0e-9,
            abs_tol=5.0e-2,
        ):
            _issue(
                issues,
                row_index,
                rule_id,
                "W_bottom_runtime_clipped_nm does not match clipped bottom width",
            )
    if w_bottom_unclipped_nm is not None and w_bottom_unclipped_nm <= 0.0:
        if _value(row, "closure_status") == "open":
            _issue(
                issues,
                row_index,
                rule_id,
                "nonpositive W_bottom_unclipped_nm marked closure_status=open",
            )
    expected_runtime_guard_by_closure = {
        "open": "none",
        "near_closed": "solver_guard",
        "geometry_closed": "validation_guard",
    }
    closure_status = _value(row, "closure_status")
    runtime_guard_status = _value(row, "runtime_guard_status")
    expected_runtime_guard = expected_runtime_guard_by_closure.get(closure_status)
    if expected_runtime_guard is not None and runtime_guard_status != expected_runtime_guard:
        _issue(
            issues,
            row_index,
            rule_id,
            f"runtime_guard_status={runtime_guard_status} inconsistent with closure_status={closure_status}",
        )
    if (
        closure_status == "geometry_closed"
        and _value(row, "geometry_propagation_status") == "propagated"
    ):
        _issue(
            issues,
            row_index,
            rule_id,
            "geometry_closed sidewall row cannot be marked geometry_propagation_status=propagated",
        )


def _validate_sidewall_v2_observation_cache_context(
    row: Mapping[str, Any],
    row_index: int,
    rule_id: str,
    issues: list[str],
    *,
    require_trapezoid_signature: bool,
) -> None:
    _require_fields(
        row,
        SIDEWALL_V2_OBSERVATION_CACHE_REQUIRED_FIELDS,
        rule_id,
        row_index,
        issues,
    )
    observation_signature = _value(row, "observation_signature")
    if not observation_signature:
        _issue(issues, row_index, rule_id, "observation_signature is blank")
    _validate_constant(
        row,
        "observation_signature_version",
        SIDEWALL_V2_OBSERVATION_SIGNATURE_VERSION,
        row_index,
        rule_id,
        issues,
    )
    _validate_enum(
        row,
        "cache_geometry_match_status",
        SIDEWALL_V2_CACHE_GEOMETRY_MATCH_STATUS_ALLOWED,
        row_index,
        rule_id,
        issues,
    )
    if _value(row, "cache_geometry_match_status") == "blocked_old_rectangular_cache":
        if (
            _value(row, "geometry_propagation_status") == "propagated"
            or _value(row, "geometry_propagation_scope") != "blocked_non_propagated_audit"
        ):
            _issue(
                issues,
                row_index,
                rule_id,
                "blocked_old_rectangular_cache cannot satisfy propagated sidewall row",
            )
    if not observation_signature:
        return
    for field in (
        "channel_cross_section_model",
        "cross_section_geometry_version",
        "geometry_profile_sha256",
        "geometry_propagation_status",
        "geometry_propagation_scope",
        "sampler_geometry_model",
        "trajectory_boundary_model",
        "wall_distance_model",
        "flow_profile_geometry_model",
        "reference_geometry_propagation_status",
        "fluidic_clogging_risk_band_claim_level",
        "fluidic_geometry_model",
        "hydraulic_resistance_model",
        "hydraulic_resistance_claim_level",
        "fluidic_geometry_propagation_status",
        "fluidic_network_geometry_model",
        "fluidic_network_hydraulic_resistance_model",
        "fluidic_network_hydraulic_resistance_claim_level",
        "fluidic_network_geometry_propagation_status",
        "electrokinetic_transport_geometry_model",
        "electrokinetic_wall_distance_model",
        "electrokinetic_geometry_propagation_status",
        "surface_charge_transport_claim_level",
    ):
        _validate_observation_signature_field_binding(
            row,
            observation_signature,
            field=field,
            row_index=row_index,
            rule_id=rule_id,
            issues=issues,
        )
    _validate_observation_signature_field_binding(
        row,
        observation_signature,
        field="sampler_support_model",
        signature_key="center_accessible_support_model",
        row_index=row_index,
        rule_id=rule_id,
        issues=issues,
    )
    for field in (
        "geometry_not_propagated_to_reference_field",
        "not_optical_solver_output",
        "not_clogging_rate",
        "not_time_to_clog",
        "geometry_not_propagated_to_fluidic_resistance",
        "geometry_not_propagated_to_fluidic_network",
        "fluidic_network_not_qch_weighted",
        "geometry_not_propagated_to_electrokinetic_transport",
        "electrokinetic_diagnostic_gate_passed",
    ):
        _validate_observation_signature_bool_binding(
            row,
            observation_signature,
            field=field,
            row_index=row_index,
            rule_id=rule_id,
            issues=issues,
        )
    _validate_observation_signature_float_binding(
        row,
        observation_signature,
        field="sidewall_taper_angle_deg_nodi",
        signature_key="sidewall_taper_angle_deg",
        row_index=row_index,
        rule_id=rule_id,
        issues=issues,
    )
    _validate_observation_signature_float_binding(
        row,
        observation_signature,
        field="particle_radius_nm",
        signature_key="particle_radius_m",
        multiplier=1.0e-9,
        abs_tol=1.0e-15,
        row_index=row_index,
        rule_id=rule_id,
        issues=issues,
    )
    if require_trapezoid_signature:
        if "channel_cross_section_model=ideal_rectangle" in observation_signature:
            _issue(
                issues,
                row_index,
                rule_id,
                "trapezoid sidewall row uses old rectangular observation signature",
            )
        if (
            "channel_cross_section_model=trapezoid_tapered_sidewalls"
            not in observation_signature
        ):
            _issue(
                issues,
                row_index,
                rule_id,
                "trapezoid sidewall row observation_signature lacks trapezoid geometry",
            )
        for fragment in SIDEWALL_V2_TRAPEZOID_SIGNATURE_REQUIRED_FRAGMENTS:
            if fragment not in observation_signature:
                _issue(
                    issues,
                    row_index,
                    rule_id,
                    f"trapezoid sidewall row observation_signature lacks {fragment}",
                )


def _validate_prs_sidewall_v2_initial_position_signature_context(
    row: Mapping[str, Any],
    row_index: int,
    issues: list[str],
) -> None:
    if _value(row, "channel_cross_section_model") != "trapezoid_tapered_sidewalls":
        return
    observation_signature = _value(row, "observation_signature")
    if not observation_signature:
        return
    for fragment in PRS_SIDEWALL_V2_INITIAL_POSITION_SIGNATURE_REQUIRED_FRAGMENTS:
        if fragment not in observation_signature:
            _issue(
                issues,
                row_index,
                "PRS-SIDEWALL-V2",
                f"trapezoid PRS row observation_signature lacks {fragment}",
            )
    _validate_observation_signature_field_binding(
        row,
        observation_signature,
        field="sampler_support_model",
        signature_key="initial_position_sampler_support_model",
        row_index=row_index,
        rule_id="PRS-SIDEWALL-V2",
        issues=issues,
    )


def _observation_signature_value(observation_signature: str, key: str) -> str:
    prefix = f"{key}="
    for part in observation_signature.split("|"):
        if part.startswith(prefix):
            return part[len(prefix) :]
    return ""


def _validate_observation_signature_field_binding(
    row: Mapping[str, Any],
    observation_signature: str,
    *,
    field: str,
    row_index: int,
    rule_id: str,
    issues: list[str],
    signature_key: str | None = None,
) -> None:
    value = _value(row, field)
    if not value:
        return
    key = signature_key or field
    signature_value = _observation_signature_value(observation_signature, key)
    if signature_value != value:
        _issue(
            issues,
            row_index,
            rule_id,
            f"observation_signature does not bind {key}={value}",
        )


def _validate_observation_signature_float_binding(
    row: Mapping[str, Any],
    observation_signature: str,
    *,
    field: str,
    signature_key: str,
    row_index: int,
    rule_id: str,
    issues: list[str],
    multiplier: float = 1.0,
    rel_tol: float = 1.0e-9,
    abs_tol: float = 1.0e-9,
) -> None:
    value = _value(row, field)
    if not value:
        return
    signature_value = _observation_signature_value(observation_signature, signature_key)
    if not signature_value:
        _issue(
            issues,
            row_index,
            rule_id,
            f"observation_signature does not bind {signature_key} from {field}",
        )
        return
    try:
        expected = float(value) * multiplier
        actual = float(signature_value)
    except ValueError:
        _issue(
            issues,
            row_index,
            rule_id,
            f"observation_signature has nonnumeric {signature_key}",
        )
        return
    if not math.isclose(actual, expected, rel_tol=rel_tol, abs_tol=abs_tol):
        _issue(
            issues,
            row_index,
            rule_id,
            f"observation_signature {signature_key}={actual}, expected {expected}",
        )


def _validate_observation_signature_bool_binding(
    row: Mapping[str, Any],
    observation_signature: str,
    *,
    field: str,
    row_index: int,
    rule_id: str,
    issues: list[str],
    signature_key: str | None = None,
) -> None:
    value = _value(row, field)
    if not value:
        return
    key = signature_key or field
    signature_value = _observation_signature_value(observation_signature, key)
    if signature_value.lower() != value.lower():
        _issue(
            issues,
            row_index,
            rule_id,
            f"observation_signature does not bind {key}={value}",
        )


def _validate_sidewall_v2_acceptance_guards(
    row: Mapping[str, Any],
    row_index: int,
    rule_id: str,
    issues: list[str],
) -> None:
    _require_fields(
        row,
        SIDEWALL_V2_ACCEPTANCE_GUARD_REQUIRED_FIELDS,
        rule_id,
        row_index,
        issues,
    )
    _validate_enum(row, "roadmap_status", SIDEWALL_V2_ROADMAP_STATUS_ALLOWED, row_index, rule_id, issues)
    for field in SIDEWALL_V2_ACCEPTANCE_GUARD_REQUIRED_FIELDS:
        if field == "roadmap_status":
            continue
        _validate_bool_equals(row, field, True, row_index, rule_id, issues)


def _validate_sidewall_v2_package_d_precheck_binding(
    row: Mapping[str, Any],
    row_index: int,
    rule_id: str,
    issues: list[str],
    *,
    expected_family: str,
) -> None:
    allowed_target_families = {
        "prs": {"prs", "prs_eas"},
        "eas": {"eas", "prs_eas"},
    }[expected_family]
    target_family = _value(row, "target_artifact_family")
    if target_family and target_family not in allowed_target_families:
        _issue(
            issues,
            row_index,
            rule_id,
            f"target_artifact_family={target_family} incompatible with {expected_family} row",
        )
    if _value(row, "package_d_precheck_status") != "pass":
        _issue(
            issues,
            row_index,
            rule_id,
            "sidewall PRS/EAS row requires package_d_precheck_status=pass",
        )
    for precheck_issue in validate_sidewall_package_d_precheck_rows([row]):
        _issue(
            issues,
            row_index,
            rule_id,
            f"Package D precheck binding failed: {precheck_issue}",
        )


def _validate_sidewall_v2_runtime_propagation_guards(
    row: Mapping[str, Any],
    row_index: int,
    rule_id: str,
    issues: list[str],
) -> None:
    _require_fields(
        row,
        SIDEWALL_V2_RUNTIME_PROPAGATION_GUARD_REQUIRED_FIELDS,
        rule_id,
        row_index,
        issues,
    )
    for field in SIDEWALL_V2_TRUE_RUNTIME_GUARD_FIELDS:
        _validate_bool_equals(row, field, True, row_index, rule_id, issues)
    for field in SIDEWALL_V2_BOOL_RUNTIME_GUARD_FIELDS:
        _validate_bool_field(row, field, row_index, rule_id, issues)

    nonblank_fields = (
        "reference_geometry_propagation_status",
        "fluidic_clogging_risk_band_claim_level",
        "fluidic_geometry_model",
        "hydraulic_resistance_model",
        "hydraulic_resistance_claim_level",
        "fluidic_geometry_propagation_status",
        "fluidic_network_geometry_model",
        "fluidic_network_hydraulic_resistance_model",
        "fluidic_network_hydraulic_resistance_claim_level",
        "fluidic_network_geometry_propagation_status",
        "electrokinetic_transport_geometry_model",
        "electrokinetic_wall_distance_model",
        "electrokinetic_geometry_propagation_status",
        "surface_charge_transport_claim_level",
    )
    for field in nonblank_fields:
        if not _value(row, field):
            _issue(issues, row_index, rule_id, f"{field} is blank")

    reference_not_propagated = _bool_field(
        row,
        "geometry_not_propagated_to_reference_field",
        row_index,
        rule_id,
        issues,
    )
    if reference_not_propagated and "not_propagated" not in _value(
        row,
        "reference_geometry_propagation_status",
    ).lower():
        _issue(
            issues,
            row_index,
            rule_id,
            "reference not-propagated flag lacks matching reference propagation status",
        )

    fluidic_not_propagated = _bool_field(
        row,
        "geometry_not_propagated_to_fluidic_resistance",
        row_index,
        rule_id,
        issues,
    )
    if fluidic_not_propagated:
        hydraulic_claim = _value(row, "hydraulic_resistance_claim_level").lower()
        if "proxy" not in hydraulic_claim or "trapezoid_poiseuille" not in hydraulic_claim:
            _issue(
                issues,
                row_index,
                rule_id,
                "fluidic resistance not-propagated flag lacks proxy/not-trapezoid-Poiseuille claim",
            )

    network_not_propagated = _bool_field(
        row,
        "geometry_not_propagated_to_fluidic_network",
        row_index,
        rule_id,
        issues,
    )
    if network_not_propagated:
        network_claim = _value(
            row,
            "fluidic_network_hydraulic_resistance_claim_level",
        ).lower()
        if "not_qch" not in network_claim:
            _issue(
                issues,
                row_index,
                rule_id,
                "fluidic network not-propagated flag lacks not_qch claim",
            )

    electrokinetic_not_propagated = _bool_field(
        row,
        "geometry_not_propagated_to_electrokinetic_transport",
        row_index,
        rule_id,
        issues,
    )
    if electrokinetic_not_propagated:
        surface_charge_claim = _value(row, "surface_charge_transport_claim_level").lower()
        if "blocked" not in surface_charge_claim and "not_propagated" not in surface_charge_claim:
            _issue(
                issues,
                row_index,
                rule_id,
                "electrokinetic not-propagated flag lacks blocked/not-propagated claim",
            )


def _validate_sidewall_v2_trajectory_guards(
    row: Mapping[str, Any],
    row_index: int,
    rule_id: str,
    issues: list[str],
) -> None:
    _require_fields(
        row,
        PRS_SIDEWALL_V2_TRAJECTORY_GUARD_REQUIRED_FIELDS,
        rule_id,
        row_index,
        issues,
    )
    for field in (
        "trajectory_boundary_model_version",
        "trajectory_boundary_claim_level",
        "wall_distance_model_version",
        "wall_distance_claim_level",
        "flow_profile_geometry_model",
        "flow_profile_geometry_claim_level",
        "sidewall_aware_runtime_status",
    ):
        if not _value(row, field):
            _issue(issues, row_index, rule_id, f"{field} is blank")
    for field in (
        "geometry_not_propagated_to_flow_model",
        "geometry_not_propagated_to_near_wall_metrics",
        "geometry_not_propagated_to_trajectory_boundary",
    ):
        _validate_bool_field(row, field, row_index, rule_id, issues)

    boundary_model = _value(row, "trajectory_boundary_model")
    boundary_claim = _value(row, "trajectory_boundary_claim_level").lower()
    if boundary_model == "trapezoid_center_support_projection_boundary_v1":
        if "surrogate" not in boundary_claim or "not_specular_reflection" not in boundary_claim:
            _issue(
                issues,
                row_index,
                rule_id,
                "trapezoid projection boundary lacks surrogate/not-specular claim level",
            )
    elif "specular_reflection" in boundary_claim and "not_specular_reflection" not in boundary_claim:
        _issue(
            issues,
            row_index,
            rule_id,
            "sidewall trajectory boundary claims specular reflection",
        )

    flow_not_propagated = _bool_field(
        row,
        "geometry_not_propagated_to_flow_model",
        row_index,
        rule_id,
        issues,
    )
    if flow_not_propagated:
        flow_claim = _value(row, "flow_profile_geometry_claim_level").lower()
        if "rectangular" not in flow_claim and "not_propagated" not in flow_claim:
            _issue(
                issues,
                row_index,
                rule_id,
                "flow not-propagated flag lacks rectangular/not-propagated claim level",
            )

    near_wall_not_propagated = _bool_field(
        row,
        "geometry_not_propagated_to_near_wall_metrics",
        row_index,
        rule_id,
        issues,
    )
    if near_wall_not_propagated:
        wall_claim = _value(row, "wall_distance_claim_level").lower()
        if "rectangular" not in wall_claim and "not_propagated" not in wall_claim:
            _issue(
                issues,
                row_index,
                rule_id,
                "near-wall not-propagated flag lacks rectangular/not-propagated claim level",
            )


def _validate_sidewall_v2_geometry_propagation_scope(
    row: Mapping[str, Any],
    row_index: int,
    rule_id: str,
    issues: list[str],
    *,
    expected_propagated_scope: str,
) -> None:
    _require_fields(
        row,
        SIDEWALL_V2_GEOMETRY_PROPAGATION_SCOPE_REQUIRED_FIELDS,
        rule_id,
        row_index,
        issues,
    )
    _validate_enum(
        row,
        "geometry_propagation_scope",
        SIDEWALL_V2_GEOMETRY_PROPAGATION_SCOPES,
        row_index,
        rule_id,
        issues,
    )
    channel_model = _value(row, "channel_cross_section_model")
    scope = _value(row, "geometry_propagation_scope")
    if channel_model != "trapezoid_tapered_sidewalls":
        if scope != "rectangle_native_or_non_sidewall_geometry":
            _issue(
                issues,
                row_index,
                rule_id,
                "non-trapezoid row has sidewall propagation scope",
            )
        return

    geometry_status = _value(row, "geometry_propagation_status")
    if geometry_status == "propagated":
        if scope != expected_propagated_scope:
            _issue(
                issues,
                row_index,
                rule_id,
                "propagated trapezoid row has ambiguous geometry_propagation_scope",
            )
        return
    if scope != "blocked_non_propagated_audit":
        _issue(
            issues,
            row_index,
            rule_id,
            "non-propagated trapezoid row lacks blocked audit propagation scope",
        )


def _validate_sidewall_v2_artifact_metadata(
    row: Mapping[str, Any],
    row_index: int,
    rule_id: str,
    issues: list[str],
    *,
    expected_artifact_version: str,
) -> None:
    _require_fields(
        row,
        SIDEWALL_V2_ARTIFACT_METADATA_REQUIRED_FIELDS,
        rule_id,
        row_index,
        issues,
    )
    if not _value(row, "artifact_id"):
        _issue(issues, row_index, rule_id, "artifact_id is blank")
    _validate_constant(
        row,
        "artifact_version",
        expected_artifact_version,
        row_index,
        rule_id,
        issues,
    )
    if not _value(row, "artifact_created_utc"):
        _issue(issues, row_index, rule_id, "artifact_created_utc is blank")


def _validate_sidewall_local_geometry(
    row_index: int,
    values: Mapping[str, float],
    *,
    nearest_wall_id: str,
    particle_radius_nm: float | None,
    issues: list[str],
) -> None:
    w_top = values.get("W_top_nm")
    sidewall_deg = values.get("sidewall_deg_comsol")
    x_left = values.get("x_left_nm")
    x_right = values.get("x_right_nm")
    x_center = values.get("x_center_nm")
    local_width = values.get("local_width_nm")
    local_half_width = values.get("local_half_width_nm")
    x = values.get("x_nm")
    u = values.get("u_nm")
    depth = values.get("D_nm")
    x_local_norm = values.get("x_local_norm")
    u_norm = values.get("u_norm")

    if x_left is not None and x_right is not None:
        if x_left >= x_right:
            _issue(
                issues,
                row_index,
                "PRS-SIDEWALL-V2",
                "x_left_nm must be less than x_right_nm",
            )
        if local_width is not None:
            _validate_close(
                local_width,
                x_right - x_left,
                row_index,
                "PRS-SIDEWALL-V2",
                "local_width_nm",
                issues,
            )
        if x_center is not None:
            _validate_close(
                x_center,
                0.5 * (x_left + x_right),
                row_index,
                "PRS-SIDEWALL-V2",
                "x_center_nm",
                issues,
            )
    if local_width is not None and local_half_width is not None:
        _validate_close(
            local_half_width,
            0.5 * local_width,
            row_index,
            "PRS-SIDEWALL-V2",
            "local_half_width_nm",
            issues,
        )
    if (
        x_local_norm is not None
        and x is not None
        and x_center is not None
        and local_half_width is not None
        and local_half_width > 0.0
    ):
        expected_x_local_norm = (x - x_center) / local_half_width
        _validate_close(
            x_local_norm,
            expected_x_local_norm,
            row_index,
            "PRS-SIDEWALL-V2",
            "x_local_norm",
            issues,
        )
    if x_local_norm is not None and not (-1.0 <= x_local_norm <= 1.0):
        _issue(
            issues,
            row_index,
            "PRS-SIDEWALL-V2",
            "x_local_norm outside [-1, 1]",
        )
    if u_norm is not None and u is not None and depth is not None and depth > 0.0:
        _validate_close(
            u_norm,
            u / depth,
            row_index,
            "PRS-SIDEWALL-V2",
            "u_norm",
            issues,
        )
    if u_norm is not None and not (0.0 <= u_norm <= 1.0):
        _issue(
            issues,
            row_index,
            "PRS-SIDEWALL-V2",
            "u_norm outside [0, 1]",
        )
    if u is not None:
        d_top = values.get("d_top_nm")
        if d_top is not None and not math.isclose(
            d_top,
            u,
            rel_tol=1.0e-9,
            abs_tol=5.0e-2,
        ):
            _issue(
                issues,
                row_index,
                "PRS-SIDEWALL-V2",
                "d_top_nm does not match u_nm",
            )
        d_bottom = values.get("d_bottom_nm")
        if d_bottom is not None and depth is not None and not math.isclose(
            d_bottom,
            depth - u,
            rel_tol=1.0e-9,
            abs_tol=5.0e-2,
        ):
            _issue(
                issues,
                row_index,
                "PRS-SIDEWALL-V2",
                "d_bottom_nm does not match D_nm - u_nm",
            )
    if (
        w_top is not None
        and sidewall_deg is not None
        and u is not None
        and local_width is not None
    ):
        tan_theta = math.tan(math.radians(sidewall_deg))
        if abs(tan_theta) <= 1.0e-12:
            _issue(
                issues,
                row_index,
                "PRS-SIDEWALL-V2",
                "sidewall_deg_comsol has zero tangent",
            )
        else:
            expected_local_width = w_top - 2.0 * u / tan_theta
            if not math.isclose(
                local_width,
                expected_local_width,
                rel_tol=1.0e-9,
                abs_tol=5.0e-2,
            ):
                _issue(
                    issues,
                    row_index,
                    "PRS-SIDEWALL-V2",
                    "local_width_nm does not match trapezoid width formula",
                )
            if x_left is not None and not math.isclose(
                x_left,
                -0.5 * expected_local_width,
                rel_tol=1.0e-9,
                abs_tol=5.0e-2,
            ):
                _issue(
                    issues,
                    row_index,
                    "PRS-SIDEWALL-V2",
                    "x_left_nm does not match trapezoid width formula",
                )
            if x_right is not None and not math.isclose(
                x_right,
                0.5 * expected_local_width,
                rel_tol=1.0e-9,
                abs_tol=5.0e-2,
            ):
                _issue(
                    issues,
                    row_index,
                    "PRS-SIDEWALL-V2",
                    "x_right_nm does not match trapezoid width formula",
                )
    if local_width is not None and local_width < 0.0:
        _issue(
            issues,
            row_index,
            "PRS-SIDEWALL-V2",
            "local_width_nm is negative",
        )
    for field in (
        "d_top_nm",
        "d_bottom_nm",
        "d_side_left_nm",
        "d_side_right_nm",
        "d_nearest_wall_nm",
    ):
        distance = values.get(field)
        if distance is not None and distance < 0.0:
            _issue(issues, row_index, "PRS-SIDEWALL-V2", f"{field} is negative")
    wall_distances = {
        "top": values.get("d_top_nm"),
        "bottom": values.get("d_bottom_nm"),
        "left_side": values.get("d_side_left_nm"),
        "right_side": values.get("d_side_right_nm"),
    }
    d_nearest = values.get("d_nearest_wall_nm")
    if d_nearest is not None and all(value is not None for value in wall_distances.values()):
        expected_nearest = min(value for value in wall_distances.values() if value is not None)
        if not math.isclose(d_nearest, expected_nearest, rel_tol=1.0e-9, abs_tol=1.0e-6):
            _issue(
                issues,
                row_index,
                "PRS-SIDEWALL-V2",
                "d_nearest_wall_nm does not match nearest wall distance",
            )
        selected_distance = wall_distances.get(nearest_wall_id)
        if selected_distance is not None and not math.isclose(
            selected_distance,
            expected_nearest,
            rel_tol=1.0e-9,
            abs_tol=1.0e-6,
        ):
            _issue(
                issues,
                row_index,
                "PRS-SIDEWALL-V2",
                "nearest_wall_id does not identify a nearest wall",
            )
    if (
        sidewall_deg is not None
        and x is not None
        and x_left is not None
        and x_right is not None
    ):
        taper = math.tan(math.radians(90.0 - sidewall_deg))
        side_norm = math.sqrt(1.0 + taper**2)
        expected_left = (x - x_left) / side_norm
        expected_right = (x_right - x) / side_norm
        d_left = values.get("d_side_left_nm")
        d_right = values.get("d_side_right_nm")
        if d_left is not None and not math.isclose(
            d_left,
            expected_left,
            rel_tol=1.0e-9,
            abs_tol=5.0e-2,
        ):
            _issue(
                issues,
                row_index,
                "PRS-SIDEWALL-V2",
                "d_side_left_nm does not match trapezoid wall-normal distance",
            )
        if d_right is not None and not math.isclose(
            d_right,
            expected_right,
            rel_tol=1.0e-9,
            abs_tol=5.0e-2,
        ):
            _issue(
                issues,
                row_index,
                "PRS-SIDEWALL-V2",
                "d_side_right_nm does not match trapezoid wall-normal distance",
            )
    surface_gap = values.get("surface_gap_for_particle_nm")
    if (
        surface_gap is not None
        and d_nearest is not None
        and particle_radius_nm is not None
    ):
        expected_gap = d_nearest - particle_radius_nm
        if not math.isclose(surface_gap, expected_gap, rel_tol=1.0e-9, abs_tol=1.0e-6):
            _issue(
                issues,
                row_index,
                "PRS-SIDEWALL-V2",
                "surface_gap_for_particle_nm does not match nearest wall minus particle radius",
            )


def _validate_sidewall_propagation_status_usage(
    row: Mapping[str, Any],
    row_index: int,
    *,
    channel_model: str,
    geometry_status: str,
    bin_accessible: bool | None,
    support_status: str,
    decision_allowed: bool | None,
    issues: list[str],
) -> None:
    if channel_model != "trapezoid_tapered_sidewalls":
        return

    reasons = _value(row, "geometry_not_propagated_reasons")
    if geometry_status == "propagated":
        if reasons:
            _issue(
                issues,
                row_index,
                "PRS-SIDEWALL-V2",
                "propagated trapezoid row carries geometry_not_propagated_reasons",
            )
        return

    if not reasons:
        _issue(
            issues,
            row_index,
            "PRS-SIDEWALL-V2",
            "non-propagated trapezoid row lacks geometry_not_propagated_reasons",
        )
    if bin_accessible is not False:
        _issue(
            issues,
            row_index,
            "PRS-SIDEWALL-V2",
            "non-propagated trapezoid row is not blocked at bin_accessible",
        )
    if support_status != "blocked":
        _issue(
            issues,
            row_index,
            "PRS-SIDEWALL-V2",
            "non-propagated trapezoid row is not blocked at particle support",
        )
    if decision_allowed is not False:
        _issue(
            issues,
            row_index,
            "PRS-SIDEWALL-V2",
            "non-propagated trapezoid row is decision-use allowed",
        )


def _validate_sidewall_tail_particle_support_guard(
    row: Mapping[str, Any],
    row_index: int,
    *,
    diameter_nm: float | None,
    particle_radius_nm: float | None,
    issues: list[str],
) -> None:
    large_tail = bool(
        (diameter_nm is not None and diameter_nm >= 220.0)
        or (particle_radius_nm is not None and particle_radius_nm >= 110.0)
    )
    if not large_tail:
        return

    if "tail_particle_auto_admitted" not in row:
        _issue(
            issues,
            row_index,
            "PRS-SIDEWALL-V2",
            "large-tail sidewall row lacks tail_particle_auto_admitted",
        )
    else:
        tail_auto_admitted = _bool_field(
            row,
            "tail_particle_auto_admitted",
            row_index,
            "PRS-SIDEWALL-V2",
            issues,
        )
        if tail_auto_admitted is not False:
            _issue(
                issues,
                row_index,
                "PRS-SIDEWALL-V2",
                "large-tail sidewall row auto-admits particle support",
            )

    steric_support_source = _value(row, "steric_support_source")
    if not steric_support_source:
        _issue(
            issues,
            row_index,
            "PRS-SIDEWALL-V2",
            "large-tail sidewall row lacks steric_support_source",
        )
        return
    if steric_support_source not in PRS_SIDEWALL_V2_STERIC_SUPPORT_SOURCE:
        _issue(
            issues,
            row_index,
            "PRS-SIDEWALL-V2",
            f"invalid steric_support_source={steric_support_source}",
        )

    support_status = _value(row, "bin_particle_center_support_status")
    if (
        support_status in {"open", "narrow"}
        and steric_support_source != "exact_geometry_primitive"
    ):
        _issue(
            issues,
            row_index,
            "PRS-SIDEWALL-V2",
            "large-tail open/narrow support lacks exact geometry primitive source",
        )


def _validate_sidewall_blocked_bin_response_values(
    row: Mapping[str, Any],
    row_index: int,
    *,
    bin_accessible: bool | None,
    support_status: str,
    issues: list[str],
) -> None:
    if bin_accessible is not False and support_status != "blocked":
        return
    for field in PRS_SIDEWALL_V2_BLOCKED_RESPONSE_VALUE_FIELDS:
        value = _value(row, field)
        if not value or value.lower() in {"blocked", "none", "null", "na", "n/a"}:
            continue
        try:
            numeric_value = float(value)
        except ValueError:
            continue
        if math.isfinite(numeric_value):
            _issue(
                issues,
                row_index,
                "PRS-SIDEWALL-V2",
                f"blocked sidewall bin has numeric {field}",
            )


def _validate_sample_status(
    row: Mapping[str, Any],
    n_events_bin: int | None,
    row_index: int,
    issues: list[str],
) -> None:
    _validate_enum(row, "bin_sample_status", PRS_APPROVED_SAMPLE_STATUS, row_index, "PRS-V16", issues)
    if _value(row, "bin_sample_status") == "guardrail_blocked":
        _issue(issues, row_index, "PRS-V24", "guardrail_blocked used as bin_sample_status")
    if n_events_bin is None:
        return
    expected = "empty" if n_events_bin == 0 else "sparse" if n_events_bin < 100 else "adequate"
    actual = _value(row, "bin_sample_status")
    rule_id = {"empty": "PRS-V17", "sparse": "PRS-V18", "adequate": "PRS-V19"}[expected]
    if actual != expected:
        _issue(issues, row_index, rule_id, f"bin_sample_status={actual}, expected {expected}")
    sparse_flag = _bool_field(row, "sparse_bin_flag", row_index, "PRS-V20", issues)
    if sparse_flag is not None and sparse_flag != (n_events_bin < 100):
        _issue(issues, row_index, "PRS-V20", "sparse_bin_flag mismatch")
    decision_allowed = _bool_field(row, "decision_use_allowed", row_index, "PRS-V21", issues)
    if decision_allowed and expected == "sparse":
        _issue(issues, row_index, "PRS-V21", "sparse individual bin is decision-use allowed")
    if decision_allowed and expected == "empty":
        _issue(issues, row_index, "PRS-V22", "empty bin is decision-use allowed")


def _validate_xz_promotion_policy(
    row: Mapping[str, Any],
    row_index: int,
    issues: list[str],
) -> None:
    if _value(row, "distribution_type") != "xz_norm_2d":
        return
    aggregate_source_type = _value(row, "aggregate_source_type")
    if aggregate_source_type == "edge_norm_primary":
        _issue(issues, row_index, "PRS-V25", "xz_norm_2d row cannot use edge_norm_primary")
    if aggregate_source_type == "xz_norm_primary_if_adequate":
        if _value(row, "bin_sample_status") != "adequate":
            _issue(issues, row_index, "PRS-V26", "xz row promoted without adequate support")


def _validate_position_flow_semantics(
    row: Mapping[str, Any],
    row_index: int,
    production_table: bool,
    issues: list[str],
) -> None:
    row_scope = _value(row, "row_scope")
    if row_scope not in PRS_APPROVED_ROW_SCOPES:
        _issue(issues, row_index, "PRS-V27", f"invalid row_scope={row_scope}")
    if production_table and row_scope != "response_surface_bin":
        rule_id = "PRS-V28" if row_scope == "qch_provenance_reference" else "PRS-V27"
        _issue(issues, row_index, rule_id, "production rows must use response_surface_bin")
    if row_scope == "response_surface_bin":
        flow_condition_id = _value(row, "flow_condition_id")
        if flow_condition_id == QCH_FLOW_CONDITION_ID:
            _issue(issues, row_index, "PRS-V29", "q_ch flow condition applied to response row")
        if flow_condition_id != PRS_NEUTRAL_FLOW_CONDITION_ID:
            _issue(issues, row_index, "PRS-V30", "missing neutral NODI flow condition")
        _validate_constant(
            row,
            "position_distribution_basis",
            PRS_POSITION_DISTRIBUTION_BASIS,
            row_index,
            "PRS-V32",
            issues,
        )
    if _value(row, "position_distribution_basis") == "comsol_transported_distribution":
        _issue(issues, row_index, "PRS-V39", "unauthorized COMSOL transported distribution row")
    _validate_constant(row, "flow_condition_version", "V1", row_index, "PRS-V30", issues)
    _validate_flow_sha(row, row_index, issues)
    _validate_constant(
        row,
        "flow_condition_scope",
        PRS_FLOW_CONDITION_SCOPE,
        row_index,
        "PRS-V30",
        issues,
    )
    _validate_constant(
        row,
        "flow_condition_claim_boundary",
        PRS_FLOW_CONDITION_CLAIM_BOUNDARY,
        row_index,
        "PRS-V30",
        issues,
    )
    _validate_bool_equals(row, "not_comsol_transport_distribution", True, row_index, "PRS-V33", issues)
    _validate_bool_equals(row, "not_qch_weighted", True, row_index, "PRS-V34", issues)
    _validate_bool_equals(row, "not_yield", True, row_index, "PRS-V35", issues)
    _validate_bool_equals(row, "not_detection_probability", True, row_index, "PRS-V36", issues)
    _validate_constant(row, "claim_boundary", PRS_CLAIM_BOUNDARY, row_index, "PRS-V41", issues)


def _validate_flow_sha(row: Mapping[str, Any], row_index: int, issues: list[str]) -> None:
    value = _value(row, "flow_condition_source_sha")
    if value == PENDING_FLOW_SHA:
        return
    if not SHA256_RE.match(value):
        _issue(issues, row_index, "PRS-V40", "flow_condition_source_sha is not sha256/pending")


def _validate_position_response_grain(
    rows: Sequence[Mapping[str, Any]],
    issues: list[str],
) -> None:
    counter: Counter[tuple[str, str, str, str, str]] = Counter()
    for row in rows:
        counter[
            (
                _value(row, "route_id_nodi"),
                _value(row, "diameter_nm"),
                _value(row, "NODI_view"),
                _value(row, "distribution_type"),
                _value(row, "bin_id"),
            )
        ] += 1
    for grain, count in counter.items():
        if count > 1:
            issues.append(f"PRS-V11: duplicate response-surface grain {grain}")


def _validate_position_response_row_arithmetic(
    rows: Sequence[Mapping[str, Any]],
    issues: list[str],
) -> None:
    groups: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(_value(row, "route_id_nodi"), _value(row, "diameter_nm"), _value(row, "NODI_view"))].append(row)
    for grain, group_rows in groups.items():
        if len(group_rows) != ROWS_PER_ROUTE_DIAMETER_VIEW:
            issues.append(
                "PRS-V11: rows_per_route_diameter_view mismatch for "
                f"{grain}: expected {ROWS_PER_ROUTE_DIAMETER_VIEW}, got {len(group_rows)}"
            )
            continue
        edge_base = sum(
            1
            for row in group_rows
            if _value(row, "distribution_type") == "edge_norm_1d"
            and _value(row, "row_kind") == "base_bin"
        )
        xz_base = sum(
            1
            for row in group_rows
            if _value(row, "distribution_type") == "xz_norm_2d"
            and _value(row, "row_kind") == "base_bin"
        )
        special = sum(1 for row in group_rows if _value(row, "row_kind") == "special_aggregate")
        expected_special = SPECIAL_AGGREGATE_COUNT_PER_DISTRIBUTION * 2
        if edge_base != EDGE_BASE_BIN_COUNT or xz_base != XZ_BASE_BIN_COUNT or special != expected_special:
            issues.append(
                "PRS-V08/PRS-V09/PRS-V10: bin arithmetic mismatch for "
                f"{grain}: edge={edge_base}, xz={xz_base}, special={special}"
            )


def _validate_effective_aperture_numeric_fields(
    row: Mapping[str, Any],
    row_index: int,
    issues: list[str],
) -> None:
    w_nominal = _float_field(row, "W_nominal_nm", row_index, "EAS-V03", issues)
    w_eff = _float_field(row, "W_eff_surrogate_nm", row_index, "EAS-V03", issues)
    delta = _float_field(row, "delta_W_eff_surrogate_nm", row_index, "EAS-V03", issues)
    if w_nominal is not None and w_eff is not None and delta is not None:
        _validate_close(delta, w_eff - w_nominal, row_index, "EAS-V03", "delta_W_eff_surrogate_nm", issues)
    for field in (
        "eta_selected_proxy_under_surrogate",
        "eta_all_proxy_under_surrogate",
        "eta_selected_relative_change",
        "eta_all_relative_change",
    ):
        _validate_number_or_blank(row, field, row_index, "EAS-V03", issues)
    _validate_positive_int_or_blank(row, "rank_under_surrogate", row_index, "EAS-V03", issues)
    if _value(row, "aperture_surrogate_mode") == "min_aperture_conservative" and w_eff is not None:
        if w_eff <= 0:
            for field in (
                "eta_selected_proxy_under_surrogate",
                "eta_all_proxy_under_surrogate",
                "rank_under_surrogate",
            ):
                if _value(row, field):
                    _issue(
                        issues,
                        row_index,
                        "EAS-V10",
                        f"nonpositive surrogate aperture has nonblank {field}",
                    )


def _validate_aperture_flags_and_boundary(
    row: Mapping[str, Any],
    row_index: int,
    issues: list[str],
) -> None:
    _validate_bool_equals(row, "not_true_W_eff", True, row_index, "EAS-V19", issues)
    _validate_bool_equals(row, "not_measured_geometry", True, row_index, "EAS-V20", issues)
    _validate_bool_equals(row, "not_optical_solver_output", True, row_index, "EAS-V21", issues)
    _validate_bool_equals(row, "not_fabrication_release", True, row_index, "EAS-V22", issues)
    _validate_bool_equals(row, "not_yield", True, row_index, "EAS-V23", issues)
    _validate_bool_equals(row, "not_winner", True, row_index, "EAS-V23", issues)
    _validate_constant(row, "claim_boundary", EAS_CLAIM_BOUNDARY, row_index, "EAS-V03", issues)
    _validate_bool_field(row, "rank_flip_flag", row_index, "EAS-V03", issues)
    _validate_bool_field(row, "candidate_family_flip_flag", row_index, "EAS-V03", issues)
    _validate_bool_field(row, "guardrail_status_change_flag", row_index, "EAS-V16", issues)


def _validate_effective_aperture_sidewall_v2_fields(
    row: Mapping[str, Any],
    row_index: int,
    issues: list[str],
) -> None:
    if not _sidewall_v2_marker_active(
        row,
        explicit_marker_fields=EAS_SIDEWALL_V2_EXPLICIT_MARKER_FIELDS,
        expected_artifact_version=EAS_SIDEWALL_V2_ARTIFACT_VERSION,
    ):
        return

    _require_fields(row, EAS_SIDEWALL_V2_REQUIRED_FIELDS, "EAS-SIDEWALL-V2", row_index, issues)
    _validate_sidewall_v2_source_geometry_descriptor_binding(
        row,
        row_index,
        "EAS-SIDEWALL-V2",
        issues,
    )
    _validate_sidewall_v2_source_grain_binding(
        row,
        row_index,
        "EAS-SIDEWALL-V2",
        issues,
        check_prs_bin_fields=False,
    )
    _validate_sidewall_v2_acceptance_guards(row, row_index, "EAS-SIDEWALL-V2", issues)
    _validate_sidewall_v2_package_d_precheck_binding(
        row,
        row_index,
        "EAS-SIDEWALL-V2",
        issues,
        expected_family="eas",
    )
    _validate_sidewall_v2_artifact_metadata(
        row,
        row_index,
        "EAS-SIDEWALL-V2",
        issues,
        expected_artifact_version=EAS_SIDEWALL_V2_ARTIFACT_VERSION,
    )
    _validate_sidewall_v2_observation_cache_context(
        row,
        row_index,
        "EAS-SIDEWALL-V2",
        issues,
        require_trapezoid_signature=True,
    )
    _validate_sidewall_v2_runtime_propagation_guards(
        row,
        row_index,
        "EAS-SIDEWALL-V2",
        issues,
    )
    _validate_sidewall_v2_geometry_propagation_scope(
        row,
        row_index,
        "EAS-SIDEWALL-V2",
        issues,
        expected_propagated_scope=EAS_SIDEWALL_V2_PROPAGATED_SCOPE,
    )
    _validate_sidewall_v2_eas_runtime_geometry_context(row, row_index, issues)
    _validate_sidewall_v2_descriptor_context(row, row_index, "EAS-SIDEWALL-V2", issues)
    _validate_constant(
        row,
        "aperture_surrogate_claim_level",
        "surrogate_sensitivity_only",
        row_index,
        "EAS-SIDEWALL-V2",
        issues,
    )
    _validate_bool_equals(
        row,
        "optical_solver_trigger_is_result",
        False,
        row_index,
        "EAS-SIDEWALL-V2",
        issues,
    )
    _validate_sidewall_v2_eas_optical_solver_trigger(row, row_index, issues)
    _validate_enum(
        row,
        "optical_geometry_claim_level",
        EAS_SIDEWALL_V2_OPTICAL_GEOMETRY_CLAIM_LEVEL_ALLOWED,
        row_index,
        "EAS-SIDEWALL-V2",
        issues,
    )
    for field in (
        "reference_field_model",
        "reference_spatial_mode",
        "reference_route",
        "illumination_mode",
        "detector_operator_id",
    ):
        if not _value(row, field):
            _issue(issues, row_index, "EAS-SIDEWALL-V2", f"{field} is blank")
    _validate_bool_equals(
        row,
        "not_qch_weighted",
        True,
        row_index,
        "EAS-SIDEWALL-V2",
        issues,
    )
    _validate_bool_equals(
        row,
        "not_detection_probability",
        True,
        row_index,
        "EAS-SIDEWALL-V2",
        issues,
    )
    if _value(row, "rank_under_surrogate"):
        _issue(
            issues,
            row_index,
            "EAS-SIDEWALL-V2",
            "sidewall EAS v2 row must not use rank_under_surrogate",
        )
    if not any(_value(row, field) for field in EAS_SIDEWALL_V2_SURROGATE_WIDTH_FIELDS):
        _issue(
            issues,
            row_index,
            "EAS-SIDEWALL-V2",
            "sidewall EAS v2 row lacks a specific surrogate width field",
        )
    for field in EAS_SIDEWALL_V2_SURROGATE_WIDTH_FIELDS:
        if _value(row, field):
            _validate_number_or_blank(row, field, row_index, "EAS-SIDEWALL-V2", issues)


def _validate_sidewall_v2_eas_optical_solver_trigger(
    row: Mapping[str, Any],
    row_index: int,
    issues: list[str],
) -> None:
    triggered = _bool_field(
        row,
        "optical_solver_triggered",
        row_index,
        "EAS-SIDEWALL-V2",
        issues,
    )
    reason = _value(row, "optical_solver_trigger_reason")
    if reason not in EAS_APPROVED_SOLVER_TRIGGER_REASONS:
        _issue(
            issues,
            row_index,
            "EAS-SIDEWALL-V2",
            f"invalid optical_solver_trigger_reason={reason}",
        )
    if triggered is False and reason != "none":
        _issue(
            issues,
            row_index,
            "EAS-SIDEWALL-V2",
            "optical_solver_trigger_reason present without optical_solver_triggered",
        )
    if triggered is True and reason == "none":
        _issue(
            issues,
            row_index,
            "EAS-SIDEWALL-V2",
            "optical_solver_triggered lacks optical_solver_trigger_reason",
        )
    claim_level = _value(row, "optical_geometry_claim_level")
    if claim_level in EAS_SIDEWALL_V2_OPTICAL_GEOMETRY_CLAIM_LEVEL_ALLOWED:
        expected_claim_level = "solver_required" if triggered is True else "surrogate"
        if claim_level != expected_claim_level:
            _issue(
                issues,
                row_index,
                "EAS-SIDEWALL-V2",
                "optical_solver_triggered is inconsistent with optical_geometry_claim_level",
            )


def _validate_sidewall_v2_eas_runtime_geometry_context(
    row: Mapping[str, Any],
    row_index: int,
    issues: list[str],
) -> None:
    channel_model = _value(row, "channel_cross_section_model")
    if channel_model != "trapezoid_tapered_sidewalls":
        _issue(
            issues,
            row_index,
            "EAS-SIDEWALL-V2",
            f"sidewall EAS v2 requires trapezoid_tapered_sidewalls, got {channel_model}",
        )
    if not _value(row, "cross_section_geometry_version"):
        _issue(
            issues,
            row_index,
            "EAS-SIDEWALL-V2",
            "sidewall EAS v2 row missing cross_section_geometry_version",
        )
    if not _value(row, "geometry_runtime_binding_version"):
        _issue(
            issues,
            row_index,
            "EAS-SIDEWALL-V2",
            "sidewall EAS v2 row missing geometry_runtime_binding_version",
        )
    geometry_status = _value(row, "geometry_propagation_status")
    if geometry_status not in PRS_SIDEWALL_V2_GEOMETRY_STATUS_ALLOWED:
        _issue(
            issues,
            row_index,
            "EAS-SIDEWALL-V2",
            f"invalid geometry_propagation_status={geometry_status}",
        )
    if geometry_status != "propagated" and not _value(row, "geometry_not_propagated_reasons"):
        _issue(
            issues,
            row_index,
            "EAS-SIDEWALL-V2",
            "non-propagated sidewall EAS row lacks geometry_not_propagated_reasons",
        )


def _validate_solver_trigger_contract(
    row: Mapping[str, Any],
    row_index: int,
    issues: list[str],
) -> None:
    trigger = _bool_field(row, "solver_contract_trigger_flag", row_index, "EAS-V25", issues)
    reason = _value(row, "solver_contract_trigger_reason")
    if reason not in EAS_APPROVED_SOLVER_TRIGGER_REASONS:
        _issue(issues, row_index, "EAS-V25", f"invalid solver_contract_trigger_reason={reason}")
    if trigger is False and reason != "none":
        _issue(issues, row_index, "EAS-V25", "solver reason present without trigger flag")
    if trigger is True and reason == "none":
        _issue(issues, row_index, "EAS-V25", "solver trigger flag lacks reason")


def _validate_no_stage1_rank_source(
    row: Mapping[str, Any],
    row_index: int,
    issues: list[str],
) -> None:
    for field in ("rank_source", "recommendation_eligible_rank_source"):
        value = _value(row, field).lower().replace("-", "_")
        if "stage_1" in value or "stage1" in value or "detector_identity" in value:
            _issue(issues, row_index, "EAS-V15", f"Stage-1 detector identity used in {field}")


def _validate_effective_aperture_grain(
    rows: Sequence[Mapping[str, Any]],
    issues: list[str],
) -> None:
    counter: Counter[tuple[str, str, str]] = Counter()
    for row in rows:
        counter[
            (
                _value(row, "route_id_nodi"),
                _value(row, "NODI_view"),
                _value(row, "aperture_surrogate_mode"),
            )
        ] += 1
    for grain, count in counter.items():
        if count > 1:
            issues.append(f"EAS-V01: duplicate aperture-surrogate grain {grain}")


def _validate_route_fields(
    row: Mapping[str, Any],
    *,
    approved_routes: frozenset[tuple[int, int, int]],
    row_index: int,
    issues: list[str],
    rule_id: str,
) -> tuple[int, int, int] | None:
    lambda_nm = _int_field(row, "lambda_nm", row_index, rule_id, issues)
    width_nm = _int_field(row, "W_nominal_nm", row_index, rule_id, issues)
    depth_nm = _int_field(row, "D_nm", row_index, rule_id, issues)
    if lambda_nm is None or width_nm is None or depth_nm is None:
        return None
    route_tuple = (lambda_nm, width_nm, depth_nm)
    if route_tuple not in approved_routes:
        _issue(issues, row_index, rule_id, f"unapproved route {route_tuple}")
    match = ROUTE_RE.match(_value(row, "route_id_nodi"))
    if not match:
        _issue(issues, row_index, rule_id, "route_id_nodi does not match lambda/W/D pattern")
        return route_tuple
    route_from_id = (
        int(match.group("lambda_nm")),
        int(match.group("W_nominal_nm")),
        int(match.group("D_nm")),
    )
    if route_from_id != route_tuple:
        _issue(issues, row_index, rule_id, f"route_id_nodi mismatch: {route_from_id} != {route_tuple}")
    return route_tuple


def _reject_forbidden_positive_fields(
    row: Mapping[str, Any],
    *,
    allowed_negative_fields: set[str],
    row_index: int,
    rule_id: str,
    issues: list[str],
) -> None:
    for field in row:
        normalized = field.lower()
        if field in allowed_negative_fields or normalized in NEGATIVE_BOUNDARY_FIELD_NAMES:
            continue
        if normalized in SIDEWALL_ROADMAP_FORBIDDEN_EXACT_COLUMNS:
            _issue(issues, row_index, rule_id, f"forbidden sidewall roadmap claim column {field}")
            continue
        for fragment in FORBIDDEN_POSITIVE_FIELD_FRAGMENTS:
            if fragment in normalized:
                _issue(issues, row_index, rule_id, f"forbidden positive claim field {field}")
                break


def _validate_constant(
    row: Mapping[str, Any],
    field: str,
    expected: str,
    row_index: int,
    rule_id: str,
    issues: list[str],
    *,
    case_sensitive: bool = True,
) -> None:
    actual = _value(row, field)
    if case_sensitive:
        ok = actual == expected
    else:
        ok = actual.lower() == expected.lower()
    if not ok:
        _issue(issues, row_index, rule_id, f"{field}={actual}, expected {expected}")


def _validate_enum(
    row: Mapping[str, Any],
    field: str,
    allowed: frozenset[str],
    row_index: int,
    rule_id: str,
    issues: list[str],
) -> None:
    value = _value(row, field)
    if value not in allowed:
        _issue(issues, row_index, rule_id, f"{field}={value} outside {sorted(allowed)}")


def _validate_optional_enum(
    row: Mapping[str, Any],
    field: str,
    allowed: frozenset[str],
    row_index: int,
    rule_id: str,
    issues: list[str],
) -> None:
    value = _value(row, field)
    if value and value not in allowed:
        _issue(issues, row_index, rule_id, f"{field}={value} outside {sorted(allowed)}")


def _validate_int_equals(
    row: Mapping[str, Any],
    field: str,
    expected: int,
    row_index: int,
    rule_id: str,
    issues: list[str],
) -> None:
    actual = _int_field(row, field, row_index, rule_id, issues)
    if actual is not None and actual != expected:
        _issue(issues, row_index, rule_id, f"{field}={actual}, expected {expected}")


def _validate_nonnegative_int(
    row: Mapping[str, Any],
    field: str,
    row_index: int,
    rule_id: str,
    issues: list[str],
) -> int | None:
    value = _int_field(row, field, row_index, rule_id, issues)
    if value is not None and value < 0:
        _issue(issues, row_index, rule_id, f"{field} is negative")
    return value


def _validate_positive_int(
    row: Mapping[str, Any],
    field: str,
    row_index: int,
    rule_id: str,
    issues: list[str],
) -> int | None:
    value = _int_field(row, field, row_index, rule_id, issues)
    if value is not None and value <= 0:
        _issue(issues, row_index, rule_id, f"{field} is not positive")
    return value


def _validate_bool_equals(
    row: Mapping[str, Any],
    field: str,
    expected: bool,
    row_index: int,
    rule_id: str,
    issues: list[str],
) -> None:
    actual = _bool_field(row, field, row_index, rule_id, issues)
    if actual is not None and actual is not expected:
        _issue(issues, row_index, rule_id, f"{field}={actual}, expected {expected}")


def _validate_bool_field(
    row: Mapping[str, Any],
    field: str,
    row_index: int,
    rule_id: str,
    issues: list[str],
) -> None:
    _bool_field(row, field, row_index, rule_id, issues)


def _validate_source_hash(
    row: Mapping[str, Any],
    *,
    field: str,
    row_index: int,
    rule_id: str,
    issues: list[str],
    allow_pending: bool,
) -> None:
    value = _value(row, field)
    if allow_pending and value == PENDING_FLOW_SHA:
        return
    if not SHA256_RE.match(value):
        _issue(issues, row_index, rule_id, f"{field} is not a sha256")


def _validate_number_or_blank(
    row: Mapping[str, Any],
    field: str,
    row_index: int,
    rule_id: str,
    issues: list[str],
) -> None:
    if _value(row, field) == "":
        return
    _float_field(row, field, row_index, rule_id, issues)


def _validate_positive_int_or_blank(
    row: Mapping[str, Any],
    field: str,
    row_index: int,
    rule_id: str,
    issues: list[str],
) -> None:
    if _value(row, field) == "":
        return
    value = _int_field(row, field, row_index, rule_id, issues)
    if value is not None and value <= 0:
        _issue(issues, row_index, rule_id, f"{field} must be positive or blank")


def _validate_close(
    actual: float,
    expected: float,
    row_index: int,
    rule_id: str,
    field: str,
    issues: list[str],
) -> None:
    if not math.isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-9):
        _issue(issues, row_index, rule_id, f"{field}={actual}, expected {expected}")


def _int_field(
    row: Mapping[str, Any],
    field: str,
    row_index: int,
    rule_id: str,
    issues: list[str],
) -> int | None:
    text = _value(row, field)
    try:
        numeric = float(text)
    except ValueError:
        _issue(issues, row_index, rule_id, f"{field} is not an integer")
        return None
    if not numeric.is_integer():
        _issue(issues, row_index, rule_id, f"{field} is not an integer")
        return None
    return int(numeric)


def _float_field(
    row: Mapping[str, Any],
    field: str,
    row_index: int,
    rule_id: str,
    issues: list[str],
) -> float | None:
    text = _value(row, field)
    if text == "":
        _issue(issues, row_index, rule_id, f"{field} is blank")
        return None
    try:
        value = float(text)
    except ValueError:
        _issue(issues, row_index, rule_id, f"{field} is not numeric")
        return None
    if not math.isfinite(value):
        _issue(issues, row_index, rule_id, f"{field} is not finite")
        return None
    return value


def _bool_field(
    row: Mapping[str, Any],
    field: str,
    row_index: int,
    rule_id: str,
    issues: list[str],
) -> bool | None:
    text = _value(row, field).lower()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    _issue(issues, row_index, rule_id, f"{field} is not boolean")
    return None


def _value(row: Mapping[str, Any], field: str) -> str:
    value = row.get(field, "")
    if value is None:
        return ""
    return str(value).strip()


def _issue(issues: list[str], row_index: int, rule_id: str, message: str) -> None:
    issues.append(f"row {row_index} {rule_id}: {message}")
