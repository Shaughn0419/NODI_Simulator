"""Post-v2 audit schema manifest generation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .realism_v2_io import write_json_atomic
from .review_package_v1 import V1_SUMMARY_PATH


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POST_V2_AUDIT_DIR = Path("results/post_v2_mandatory_audit")

POST_V2_GENERATED_ROLES: tuple[tuple[str, str, str], ...] = (
    (
        "candidate_universe_manifest",
        "results/post_v2_mandatory_audit/candidate_universe_manifest.json",
        "P0b.candidate_universe",
    ),
    (
        "top_candidate_mandatory_audit",
        "results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv",
        "P0b.candidate_universe",
    ),
    (
        "top_candidate_particle_panel_audit",
        "results/post_v2_mandatory_audit/top_candidate_particle_panel_audit.csv",
        "P0b.ev_prior_contaminant_audit",
    ),
    (
        "top_candidate_pairwise_rank_inversion",
        "results/post_v2_mandatory_audit/top_candidate_pairwise_rank_inversion.csv",
        "P0b.pairwise_rank_audit",
    ),
    (
        "bfp_roi_operator_summary",
        "results/post_v2_mandatory_audit/bfp_roi_operator_summary.csv",
        "P0b.bfp_roi_audit",
    ),
    (
        "tsuyama_bfp_reference_summary",
        "results/post_v2_mandatory_audit/tsuyama_bfp_reference_summary.csv",
        "P0b.tsuyama_bfp_audit",
    ),
    (
        "ev_prior_contaminant_summary",
        "results/post_v2_mandatory_audit/ev_prior_contaminant_summary.csv",
        "P0b.ev_prior_contaminant_audit",
    ),
    (
        "noise_readout_scenario_bundle",
        "results/post_v2_mandatory_audit/noise_readout_scenario_bundle.csv",
        "P0b.noise_readout_audit",
    ),
    (
        "noise_readout_route_sensitivity",
        "results/post_v2_mandatory_audit/noise_readout_route_sensitivity.csv",
        "P0b.noise_readout_audit",
    ),
    (
        "top_candidate_mandatory_audit_readme",
        "results/post_v2_mandatory_audit/top_candidate_mandatory_audit_readme.md",
        "P0b.pairwise_rank_audit",
    ),
)

V1_SOURCE_FIELD_MAPPING: tuple[dict[str, str], ...] = (
    {"audit_field": "v1_scalar_score", "source_column": "score", "derivation_rule": "direct_copy"},
    {
        "audit_field": "v1_engineering_score",
        "source_column": "engineering_score",
        "derivation_rule": "direct_copy",
    },
    {
        "audit_field": "v1_stable_detection_rate_proxy",
        "source_column": "engineering_basis_stable_detection_rate",
        "derivation_rule": "direct_copy_relative_proxy_only",
    },
    {
        "audit_field": "v1_mean_peak_margin_z_proxy",
        "source_column": "engineering_basis_mean_peak_margin_z",
        "derivation_rule": "direct_copy_relative_proxy_not_calibrated_snr",
    },
    {
        "audit_field": "v1_mean_peak_height_proxy",
        "source_column": "mean_peak_height",
        "derivation_rule": "direct_copy_arbitrary_relative_units_only",
    },
    {
        "audit_field": "v1_output_claim_level",
        "source_column": "output_claim_level_resolved",
        "derivation_rule": "direct_copy_expected_engineering_ranking",
    },
    {
        "audit_field": "v1_field_coordinate_measure",
        "source_column": "field_coordinate_measure",
        "derivation_rule": "direct_copy_expected_theta_phi_surrogate",
    },
    {
        "audit_field": "v1_operator_route",
        "source_column": "operator_route",
        "derivation_rule": "direct_copy_expected_pupil_slit_surrogate",
    },
    {
        "audit_field": "v1_detector_field_units",
        "source_column": "detector_field_units",
        "derivation_rule": "direct_copy_expected_arbitrary_relative_field_units",
    },
    {
        "audit_field": "v1_bfp_to_angle_jacobian_applied",
        "source_column": "bfp_to_angle_jacobian_applied",
        "derivation_rule": "rename_on_ingest_expected_false_unprefixed_forbidden",
    },
    {
        "audit_field": "v1_reference_operating_point_status",
        "source_column": "reference_operating_point_status",
        "derivation_rule": "direct_copy_relative_reference_status_only",
    },
    {
        "audit_field": "v1_reference_route_consensus_status",
        "source_column": "reference_route_consensus_status",
        "derivation_rule": "direct_copy",
    },
    {
        "audit_field": "v1_reference_solver_status",
        "source_column": "reference_solver_status",
        "derivation_rule": "direct_copy_expected_engineering_surrogate_language",
    },
    {
        "audit_field": "v1_reference_design_validity",
        "source_column": "reference_design_validity",
        "derivation_rule": "direct_copy",
    },
)

AUDIT_SCHEMA_COLUMNS: tuple[str, ...] = (
    "audit_schema_version",
    "audit_run_id",
    "audit_generated_at",
    "source_v1_library_id",
    "source_v1_library_path",
    "source_v1_library_sha256",
    "source_v2_closure_id",
    "candidate_id",
    "candidate_source",
    "route_role_initial",
    "route_role_final",
    "wavelength_nm",
    "width_nm",
    "depth_nm",
    "comparison_stratum",
    "ranking_participation",
    "particle_panel_summary_id",
    "missing_v1_reason",
    "aggregation_scope",
    "aggregation_particle_family",
    "aggregation_particle_filter_id",
    "aggregation_weighting_id",
    "aggregation_metric_id",
    "aggregation_quantile",
    "anchor_particles_included",
    "contaminants_included_in_route_score",
)


def build_audit_schema_manifest() -> dict[str, Any]:
    return {
        "audit_manifest_schema": "ev_nodi_post_v2_mandatory_audit_manifest_v1",
        "milestone": "P0a_schema_scaffold",
        "claim_scope": "no_measured_data_relative_audit_only",
        "calibrated_claim_allowed": False,
        "source_v1_library_path": V1_SUMMARY_PATH,
        "v1_source_field_mapping": list(V1_SOURCE_FIELD_MAPPING),
        "unprefixed_forbidden_audit_columns": ["bfp_to_angle_jacobian_applied"],
        "required_core_columns": list(AUDIT_SCHEMA_COLUMNS),
        "required_aggregation_fields": [
            "aggregation_scope",
            "aggregation_particle_family",
            "aggregation_particle_filter_id",
            "aggregation_weighting_id",
            "aggregation_metric_id",
            "aggregation_quantile",
        ],
        "rank_policy": {
            "rank_direction": "higher_score_better",
            "rank_method": "average_tie_rank",
            "rank_percentile_definition": "1.0_best_0.0_worst",
            "primary_inversion_stratum": "all_ranked_routes",
            "raw_magnitude_final_gate_allowed": False,
        },
        "v1_bfp_to_angle_jacobian_applied_expected": False,
        "audit_bfp_jacobian_applied_layer": "post_v2_audit_sidecar_not_v1_fact",
        "p0b_artifacts_produced_from_evidence_chain": [
            {"role": role, "path": path, "generation_task_id": task}
            for role, path, task in POST_V2_GENERATED_ROLES
        ],
    }


def write_audit_schema_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    output = project_root / POST_V2_AUDIT_DIR / "top_candidate_mandatory_audit_manifest.json"
    write_json_atomic(output, build_audit_schema_manifest(), sort_keys=True)
    return output
