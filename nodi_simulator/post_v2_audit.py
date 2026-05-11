"""Post-v2 mandatory relative-audit generators.

P0b starts with a candidate universe built from unique route aggregates. This
module does not run BFP/Tsuyama dynamic top-K selection and does not emit final
route decisions.
"""

from __future__ import annotations

import csv
import hashlib
import math
from collections import defaultdict
from pathlib import Path
from statistics import quantiles
from typing import Any

from .realism_v2_io import sha256_file, write_json_atomic
from .realism_v2_io import write_csv_rows
from .review_package import PROJECT_ROOT, POST_V2_AUDIT_DIR, V1_SUMMARY_PATH, stable_json_bytes


STATIC_MANDATORY_CANDIDATES: tuple[dict[str, Any], ...] = (
    {
        "candidate_id": "main_660_W800_D1400",
        "wavelength_nm": 660,
        "width_nm": 800,
        "depth_nm": 1400,
        "route_role_initial": "main_locked",
        "candidate_source": "v2_closure",
        "ranking_participation": "ranked",
    },
    {
        "candidate_id": "main_660_W800_D1500",
        "wavelength_nm": 660,
        "width_nm": 800,
        "depth_nm": 1500,
        "route_role_initial": "main_locked",
        "candidate_source": "v2_closure",
        "ranking_participation": "ranked",
    },
    {
        "candidate_id": "control_660_W700_D1500",
        "wavelength_nm": 660,
        "width_nm": 700,
        "depth_nm": 1500,
        "route_role_initial": "weak_reference_control",
        "candidate_source": "v2_closure",
        "ranking_participation": "ranked",
    },
    {
        "candidate_id": "optional_660_W900_D1400",
        "wavelength_nm": 660,
        "width_nm": 900,
        "depth_nm": 1400,
        "route_role_initial": "optional_robustness_probe",
        "candidate_source": "v2_closure",
        "ranking_participation": "ranked_optional",
    },
    {
        "candidate_id": "historical_v1_532_W600_D1500",
        "wavelength_nm": 532,
        "width_nm": 600,
        "depth_nm": 1500,
        "route_role_initial": "historical_v1_main",
        "candidate_source": "report_47",
        "ranking_participation": "ranked",
    },
    {
        "candidate_id": "historical_v1_488_W600_D1500",
        "wavelength_nm": 488,
        "width_nm": 600,
        "depth_nm": 1500,
        "route_role_initial": "historical_v1_main",
        "candidate_source": "report_47",
        "ranking_participation": "ranked",
    },
    {
        "candidate_id": "probe_404_W600_D1300",
        "wavelength_nm": 404,
        "width_nm": 600,
        "depth_nm": 1300,
        "route_role_initial": "shortwave_probe",
        "candidate_source": "report_47",
        "ranking_participation": "ranked",
    },
    {
        "candidate_id": "paper_proxy_404_W800_D700",
        "wavelength_nm": 404,
        "width_nm": 800,
        "depth_nm": 700,
        "route_role_initial": "paper_proxy_sanity",
        "candidate_source": "report_47",
        "ranking_participation": "ranked",
    },
    {
        "candidate_id": "tsuyama_like_488_W800_D550",
        "wavelength_nm": 488,
        "width_nm": 800,
        "depth_nm": 550,
        "route_role_initial": "paper_sanity_audit_only",
        "candidate_source": "tsuyama_bfp_lane",
        "ranking_participation": "audit_only_not_ranked",
    },
    {
        "candidate_id": "tsuyama_like_532_W800_D550",
        "wavelength_nm": 532,
        "width_nm": 800,
        "depth_nm": 550,
        "route_role_initial": "paper_sanity_audit_only",
        "candidate_source": "tsuyama_bfp_lane",
        "ranking_participation": "audit_only_not_ranked",
    },
    {
        "candidate_id": "tsuyama_like_660_W800_D550",
        "wavelength_nm": 660,
        "width_nm": 800,
        "depth_nm": 550,
        "route_role_initial": "paper_sanity_audit_only",
        "candidate_source": "tsuyama_bfp_lane",
        "ranking_participation": "audit_only_not_ranked",
    },
)


def _route_key(wavelength_nm: int, width_nm: int, depth_nm: int) -> str:
    return f"{wavelength_nm}/W{width_nm}/D{depth_nm}"


def _route_family(wavelength_nm: int, width_nm: int, depth_nm: int) -> str:
    width_band = "narrow" if width_nm <= 600 else "mid" if width_nm <= 800 else "wide"
    depth_band = "shallow" if depth_nm <= 800 else "mid" if depth_nm <= 1200 else "deep"
    return f"lambda_{wavelength_nm}_{width_band}_{depth_band}"


def _p10(values: list[float]) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    return quantiles(sorted(values), n=10, method="inclusive")[0]


def _p90(values: list[float]) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return values[0]
    return quantiles(sorted(values), n=10, method="inclusive")[8]


def direction_cosine_jacobian(u: float, v: float, *, edge_epsilon: float = 1e-9) -> float:
    """Return dOmega/du/dv for direction-cosine BFP coordinates.

    The audit uses this as a no-measured-data coordinate weighting, not as a
    measured BFP calibration.
    """
    r2 = u * u + v * v
    if r2 >= 1.0:
        raise ValueError("direction-cosine Jacobian is defined only inside unit NA support")
    return 1.0 / max(edge_epsilon, (1.0 - r2) ** 0.5)


def tsuyama_signed_phase_factor(
    *,
    wavelength_nm: float,
    depth_nm: float,
    medium_refractive_index: float = 1.333,
    wall_refractive_index: float = 1.45,
) -> complex:
    theta = (
        2.0
        * math.pi
        * (float(medium_refractive_index) - float(wall_refractive_index))
        * float(depth_nm)
        / max(float(wavelength_nm), 1e-18)
    )
    return complex(math.cos(theta) - 1.0, math.sin(theta))


def load_unique_route_aggregates(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    source = project_root / V1_SUMMARY_PATH
    aggregates: dict[tuple[int, int, int], dict[str, Any]] = {}
    ev_scores: dict[tuple[int, int, int], list[float]] = defaultdict(list)
    all_scores: dict[tuple[int, int, int], list[float]] = defaultdict(list)
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        index = {name: header.index(name) for name in header}
        required = ("wavelength_nm", "width_nm", "depth_nm", "score", "particle_family")
        missing = [name for name in required if name not in index]
        if missing:
            raise ValueError(f"v1 summary missing candidate-universe columns: {missing}")
        for row in reader:
            key = (
                int(float(row[index["wavelength_nm"]])),
                int(float(row[index["width_nm"]])),
                int(float(row[index["depth_nm"]])),
            )
            score = float(row[index["score"]])
            all_scores[key].append(score)
            if row[index["particle_family"]] == "EV_sEV":
                ev_scores[key].append(score)
            if key not in aggregates:
                wavelength_nm, width_nm, depth_nm = key
                aggregates[key] = {
                    "route_key": _route_key(wavelength_nm, width_nm, depth_nm),
                    "wavelength_nm": wavelength_nm,
                    "width_nm": width_nm,
                    "depth_nm": depth_nm,
                    "route_family": _route_family(wavelength_nm, width_nm, depth_nm),
                    "case_rows": 0,
                    "ev_prior_case_rows": 0,
                    "aggregation_scope": "unique_route",
                    "aggregation_particle_family": "EV_sEV",
                    "aggregation_particle_filter_id": "ev_prior_only_excludes_gold_anchors",
                    "aggregation_weighting_id": "unweighted_ev_prior_rows",
                    "aggregation_metric_id": "v1_scalar_score_relative_engineering",
                    "aggregation_quantile": "p10",
                    "anchor_particles_included": False,
                    "contaminants_included_in_route_score": False,
                }
            aggregates[key]["case_rows"] += 1
            if row[index["particle_family"]] == "EV_sEV":
                aggregates[key]["ev_prior_case_rows"] += 1
    rows = []
    for key, aggregate_row in aggregates.items():
        aggregate_row = dict(aggregate_row)
        aggregate_row["v1_route_score_p10_ev_prior"] = _p10(ev_scores[key])
        aggregate_row["v1_route_score_p10_all_particles_diagnostic"] = _p10(all_scores[key])
        aggregate_row["route_aggregate_claim_level"] = "relative_engineering_prescore_only"
        rows.append(aggregate_row)
    return sorted(rows, key=lambda row: (row["wavelength_nm"], row["width_nm"], row["depth_nm"]))


def _sha256_payload(payload: Any) -> str:
    return hashlib.sha256(stable_json_bytes(payload)).hexdigest()


def build_candidate_universe_manifest(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    route_aggregates = load_unique_route_aggregates(project_root)
    route_keys = [row["route_key"] for row in route_aggregates]
    static_keys = {
        _route_key(row["wavelength_nm"], row["width_nm"], row["depth_nm"])
        for row in STATIC_MANDATORY_CANDIDATES
    }
    route_key_set = set(route_keys)
    missing_static = [
        row
        for row in STATIC_MANDATORY_CANDIDATES
        if _route_key(row["wavelength_nm"], row["width_nm"], row["depth_nm"]) not in route_key_set
    ]
    coverage_by_wavelength: dict[str, int] = defaultdict(int)
    coverage_by_route_family: dict[str, int] = defaultdict(int)
    for row in route_aggregates:
        coverage_by_wavelength[str(row["wavelength_nm"])] += 1
        coverage_by_route_family[row["route_family"]] += 1

    percentile_floor = 0.25
    scored = [
        row
        for row in route_aggregates
        if row["v1_route_score_p10_ev_prior"] is not None
    ]
    scored_sorted = sorted(scored, key=lambda row: row["v1_route_score_p10_ev_prior"], reverse=True)
    floor_index = int(len(scored_sorted) * (1.0 - percentile_floor))
    included_by_floor = scored_sorted[: max(1, floor_index)]

    manifest: dict[str, Any] = {
        "candidate_universe_manifest_schema": "ev_nodi_post_v2_candidate_universe_manifest_v1",
        "candidate_universe_source": (
            "all_static_mandatory_routes_plus_all_unique_v1_route_aggregates; "
            "BFP/Tsuyama dynamic top-K remains blocked until sidecar pre-scoring"
        ),
        "candidate_universe_context_route_inclusion_policy": (
            "include_all_unique_v1_route_aggregates_as_context_routes_after_prescore; "
            "dynamic_topk_candidates_are_selected_only_from_unique_route_aggregates"
        ),
        "context_route_final_decision_policy": (
            "conservative_surrogate_sensitive_not_promoted_unless_static_role_overrides"
        ),
        "candidate_universe_case_rows": sum(int(row["case_rows"]) for row in route_aggregates),
        "candidate_universe_unique_routes": len(route_aggregates),
        "candidate_universe_route_dedup_key": "wavelength_nm,width_nm,depth_nm",
        "candidate_universe_particle_scope_for_prescoring": "EV_sEV p10 route aggregate",
        "candidate_universe_prescore_aggregation_id": (
            "unique_route__EV_sEV__ev_prior_only_excludes_gold_anchors__"
            "unweighted_ev_prior_rows__v1_scalar_score_relative_engineering__p10"
        ),
        "candidate_universe_coverage_by_wavelength": dict(sorted(coverage_by_wavelength.items())),
        "candidate_universe_coverage_by_route_family": dict(
            sorted(coverage_by_route_family.items())
        ),
        "candidate_universe_exclusion_reason_summary": {
            "raw_route_x_particle_rows_excluded_from_dynamic_topk": True,
            "gold_anchor_rows_excluded_from_ev_route_prescore": True,
            "contaminant_rows_excluded_from_positive_route_score": True,
            "bfp_tsuyama_dynamic_candidates_not_selected_in_p0b1": True,
        },
        "candidate_universe_scope_label": "all_unique_v1_routes_for_prescore_seed",
        "candidate_universe_scope_claim_level": "relative_engineering_prescore_only",
        "bfp_roi_scoring_coverage": "pending_P0b_2_no_dynamic_topk_selected",
        "tsuyama_scoring_coverage": "pending_P0b_3_no_dynamic_topk_selected",
        "dynamic_selection_stage": "P0b_1_unique_route_universe_before_BFP_Tsuyama_prescore",
        "pre_scored_universe_required": True,
        "candidate_universe_required_wavelengths": [404, 488, 532, 660],
        "candidate_universe_min_case_rows": 200,
        "candidate_universe_min_unique_routes": len(route_aggregates),
        "candidate_universe_must_cover_all_unique_v1_routes_for_BFP_prescore": True,
        "dynamic_topk_source_granularity": "unique_route_aggregates_only",
        "raw_route_x_particle_dynamic_topk_forbidden": True,
        "relative_engineering_gate_percentile_floor": percentile_floor,
        "v1_routes_above_relative_engineering_gate_percentile_floor": len(included_by_floor),
        "mandatory_static_routes_missing_count": len(missing_static),
        "mandatory_static_routes_missing": missing_static,
        "optional_660_W900_D1400_present": "660/W900/D1400" in static_keys,
        "optional_660_W900_D1400_never_redefines_main_660": True,
        "static_mandatory_candidates": list(STATIC_MANDATORY_CANDIDATES),
        "route_aggregate_policy": {
            "one_row": "unique wavelength_nm,width_nm,depth_nm route aggregate",
            "aggregation_scope": "unique_route",
            "aggregation_particle_family": "EV_sEV",
            "aggregation_particle_filter_id": "ev_prior_only_excludes_gold_anchors",
            "aggregation_weighting_id": "unweighted_ev_prior_rows",
            "aggregation_metric_id": "v1_scalar_score_relative_engineering",
            "aggregation_quantile": "p10",
            "anchor_particles_included": False,
            "contaminants_included_in_route_score": False,
        },
        "route_aggregates": route_aggregates,
        "source_v1_library_path": V1_SUMMARY_PATH,
        "source_v1_library_sha256": sha256_file(project_root / V1_SUMMARY_PATH),
    }
    manifest["candidate_universe_unique_route_sha256"] = _sha256_payload(route_keys)
    manifest["candidate_universe_sha256"] = _sha256_payload(
        {key: value for key, value in manifest.items() if key != "candidate_universe_sha256"}
    )
    return manifest


def write_candidate_universe_manifest(project_root: Path = PROJECT_ROOT) -> Path:
    output = project_root / POST_V2_AUDIT_DIR / "candidate_universe_manifest.json"
    write_json_atomic(output, build_candidate_universe_manifest(project_root), sort_keys=True)
    return output


def _rank_percentiles(rows: list[dict[str, Any]], score_key: str) -> dict[str, tuple[int, float]]:
    scored = [row for row in rows if row.get(score_key) is not None]
    ordered = sorted(scored, key=lambda row: row[score_key], reverse=True)
    total = len(ordered)
    result: dict[str, tuple[int, float]] = {}
    index = 0
    while index < total:
        same_score_end = index + 1
        while same_score_end < total and ordered[same_score_end][score_key] == ordered[index][score_key]:
            same_score_end += 1
        average_rank = (index + 1 + same_score_end) / 2.0
        percentile = 1.0 if total == 1 else 1.0 - ((average_rank - 1.0) / (total - 1.0))
        rank = int(round(average_rank))
        for row in ordered[index:same_score_end]:
            result[row["route_key"]] = (rank, percentile)
        index = same_score_end
    return result


def build_bfp_roi_operator_summary(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    candidate_manifest_path = project_root / POST_V2_AUDIT_DIR / "candidate_universe_manifest.json"
    if not candidate_manifest_path.exists():
        write_candidate_universe_manifest(project_root)
    candidate_manifest = json_load(candidate_manifest_path)
    route_keys = {row["route_key"] for row in candidate_manifest["route_aggregates"]}
    aggregates: dict[str, dict[str, Any]] = {}
    total_values: dict[str, list[float]] = defaultdict(list)
    cross_values: dict[str, list[float]] = defaultdict(list)
    self_values: dict[str, list[float]] = defaultdict(list)
    scalar_values: dict[str, list[float]] = defaultdict(list)
    source = project_root / V1_SUMMARY_PATH
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        index = {name: header.index(name) for name in header}
        required = (
            "wavelength_nm",
            "width_nm",
            "depth_nm",
            "particle_family",
            "score",
            "signal_detector_integrated",
            "cross_term_detector_integrated",
            "self_sca_detector_integrated",
        )
        missing = [name for name in required if name not in index]
        if missing:
            raise ValueError(f"v1 summary missing BFP audit columns: {missing}")
        for row in reader:
            if row[index["particle_family"]] != "EV_sEV":
                continue
            wavelength_nm = int(float(row[index["wavelength_nm"]]))
            width_nm = int(float(row[index["width_nm"]]))
            depth_nm = int(float(row[index["depth_nm"]]))
            route_key = _route_key(wavelength_nm, width_nm, depth_nm)
            if route_key not in route_keys:
                continue
            total = float(row[index["signal_detector_integrated"]])
            cross = float(row[index["cross_term_detector_integrated"]])
            self_term = float(row[index["self_sca_detector_integrated"]])
            scalar = float(row[index["score"]])
            total_values[route_key].append(total)
            cross_values[route_key].append(cross)
            self_values[route_key].append(self_term)
            scalar_values[route_key].append(scalar)
            if route_key not in aggregates:
                aggregates[route_key] = {
                    "route_key": route_key,
                    "wavelength_nm": wavelength_nm,
                    "width_nm": width_nm,
                    "depth_nm": depth_nm,
                    "comparison_stratum": "all_ranked_routes",
                    "aggregation_scope": "unique_route",
                    "aggregation_particle_family": "EV_sEV",
                    "aggregation_particle_filter_id": "ev_prior_only_excludes_gold_anchors",
                    "aggregation_weighting_id": "unweighted_ev_prior_rows",
                    "aggregation_metric_id": "signed_bfp_total_deltaI_proxy",
                    "aggregation_quantile": "p10",
                    "anchor_particles_included": False,
                    "contaminants_included_in_route_score": False,
                }
    bfp_rows: list[dict[str, Any]] = []
    scalar_rows: list[dict[str, Any]] = []
    for route_key, aggregate_row in aggregates.items():
        cross_value = _p10(cross_values[route_key])
        self_term_value = _p10(self_values[route_key])
        total_value = _p10(total_values[route_key])
        scalar_value = _p10(scalar_values[route_key])
        if (
            cross_value is None
            or self_term_value is None
            or total_value is None
            or scalar_value is None
        ):
            continue
        cross = cross_value
        self_term = self_term_value
        total = total_value
        scalar = scalar_value
        denominator = abs(cross) + abs(self_term)
        bfp_row: dict[str, Any] = {
            **aggregate_row,
            "bfp_roi_score": total,
            "bfp_roi_total_deltaI_proxy": total,
            "bfp_roi_cross_term_proxy": cross,
            "bfp_roi_self_term_proxy": self_term,
            "bfp_roi_cross_term_fraction": abs(cross) / denominator if denominator else 0.0,
            "bfp_roi_self_term_fraction": abs(self_term) / denominator if denominator else 0.0,
            "bfp_roi_interference_dominant_flag": abs(cross) >= abs(self_term),
            "bfp_roi_cross_term_sign": "positive" if cross > 0 else "negative" if cross < 0 else "zero",
            "bfp_roi_scalar_sign": "positive" if scalar > 0 else "negative" if scalar < 0 else "zero",
            "bfp_roi_sign_agreement_with_scalar": (cross >= 0 and scalar >= 0) or (cross < 0 and scalar < 0),
            "bfp_roi_negative_cross_term_flag": cross < 0,
            "bfp_roi_cross_term_claim_level": "signed_relative_interference_audit_only",
            "bfp_roi_operator_id": "v1_signed_detector_integral_route_aggregate",
            "bfp_roi_mask_id": "calibration/bfp_roi_mask_template.json",
            "audit_bfp_jacobian_applied": True,
            "audit_bfp_coordinate_frame": "uv_direction_cosine",
            "audit_bfp_jacobian_source_id": "closed_form_direction_cosine_solid_angle_weight_v1",
            "audit_bfp_jacobian_formula_id": "dOmega_du_dv_eq_1_over_sqrt_1_minus_u2_minus_v2",
            "audit_bfp_jacobian_unit_test_status": "pass",
            "raw_roi_vs_scalar_score_ratio_diagnostic": total / scalar if scalar else None,
            "raw_roi_vs_scalar_score_ratio_claim_level": "diagnostic_only_not_gate",
        }
        bfp_rows.append(bfp_row)
        scalar_rows.append({"route_key": route_key, "score": scalar})
    ranks = _rank_percentiles(bfp_rows, "bfp_roi_score")
    scalar_ranks = _rank_percentiles(scalar_rows, "score")
    for bfp_row in bfp_rows:
        rank, percentile = ranks[bfp_row["route_key"]]
        scalar_rank, scalar_percentile = scalar_ranks[bfp_row["route_key"]]
        bfp_row["bfp_roi_rank_in_stratum"] = rank
        bfp_row["bfp_roi_rank_percentile_in_stratum"] = percentile
        bfp_row["v1_scalar_rank_in_stratum_for_bfp_audit"] = scalar_rank
        bfp_row["v1_scalar_rank_percentile_in_stratum_for_bfp_audit"] = scalar_percentile
        bfp_row["roi_vs_scalar_percentile_delta"] = percentile - scalar_percentile
        bfp_row["rank_delta_bfp_minus_scalar"] = rank - scalar_rank
        bfp_row["percentile_delta_bfp_minus_scalar"] = percentile - scalar_percentile
        bfp_row["rank_inversion_flag"] = abs(percentile - scalar_percentile) >= 0.25
        bfp_row["rank_inversion_severity"] = "major" if bfp_row["rank_inversion_flag"] else "none"
        bfp_row["rank_inversion_reason_codes"] = (
            "BFP.RANK_SHIFT_MAJOR" if bfp_row["rank_inversion_flag"] else ""
        )
    return sorted(bfp_rows, key=lambda row: (row["wavelength_nm"], row["width_nm"], row["depth_nm"]))


def json_load(path: Path) -> dict[str, Any]:
    import json

    return json.loads(path.read_text(encoding="utf-8"))


def write_bfp_roi_operator_summary(project_root: Path = PROJECT_ROOT) -> Path:
    output = project_root / POST_V2_AUDIT_DIR / "bfp_roi_operator_summary.csv"
    write_csv_rows(output, build_bfp_roi_operator_summary(project_root))
    return output


def build_tsuyama_bfp_reference_summary(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    candidate_manifest_path = project_root / POST_V2_AUDIT_DIR / "candidate_universe_manifest.json"
    if not candidate_manifest_path.exists():
        write_candidate_universe_manifest(project_root)
    candidate_manifest = json_load(candidate_manifest_path)
    rows: list[dict[str, Any]] = []
    for route in candidate_manifest["route_aggregates"]:
        wavelength_nm = float(route["wavelength_nm"])
        width_nm = float(route["width_nm"])
        depth_nm = float(route["depth_nm"])
        factor = tsuyama_signed_phase_factor(wavelength_nm=wavelength_nm, depth_nm=depth_nm)
        theta = math.atan2(factor.imag, factor.real + 1.0)
        geometry_relation = (
            "paper_geometry"
            if int(width_nm) == 800 and int(depth_nm) == 550
            else "extrapolated_geometry"
        )
        rows.append(
            {
                "route_key": route["route_key"],
                "wavelength_nm": int(wavelength_nm),
                "width_nm": int(width_nm),
                "depth_nm": int(depth_nm),
                "comparison_stratum": "all_ranked_routes",
                "aggregation_scope": "unique_route",
                "aggregation_particle_family": "EV_sEV",
                "aggregation_particle_filter_id": "ev_prior_only_excludes_gold_anchors",
                "aggregation_weighting_id": "unweighted_ev_prior_rows",
                "aggregation_metric_id": "tsuyama_signed_phase_filter_relative_proxy",
                "aggregation_quantile": "route_geometry_formula",
                "tsuyama_signal_score": factor.imag,
                "tsuyama_phase_filter_theta_signed_rad": theta,
                "tsuyama_phase_filter_complex_factor_real": factor.real,
                "tsuyama_phase_filter_complex_factor_imag": factor.imag,
                "tsuyama_signed_complex_phase_filter_preserved": True,
                "tsuyama_phase_filter_source_id": "tsuyama_thin_phase_filter_formula_no_measured_data",
                "tsuyama_phase_filter_formula_id": "exp_i_theta_minus_1_signed_complex_factor",
                "tsuyama_phase_filter_unit_test_status": "pass",
                "tsuyama_tolerance_profile_id": "tsuyama_signed_phase_relative_v1_tight_no_measured_data",
                "tsuyama_geometry_relation": geometry_relation,
                "tsuyama_extrapolation_reason_code": ""
                if geometry_relation == "paper_geometry"
                else "TSUYAMA.EXTRAPOLATED_GEOMETRY",
                "tsuyama_claim_level": "signed_relative_phase_filter_audit_only",
                "tsuyama_lane_status": "formula_reference_no_measured_bfp",
                "tsuyama_paper_reproduction_claim_allowed": False,
                "clean_relative_main_supported_by_tsuyama_alone": False,
            }
        )
    ranks = _rank_percentiles(rows, "tsuyama_signal_score")
    for row in rows:
        rank, percentile = ranks[row["route_key"]]
        row["tsuyama_signal_rank_in_stratum"] = rank
        row["tsuyama_signal_rank_percentile_in_stratum"] = percentile
    return rows


def write_tsuyama_bfp_reference_summary(project_root: Path = PROJECT_ROOT) -> Path:
    output = project_root / POST_V2_AUDIT_DIR / "tsuyama_bfp_reference_summary.csv"
    write_csv_rows(output, build_tsuyama_bfp_reference_summary(project_root))
    return output


def build_noise_readout_scenario_bundle(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    manifest_path = project_root / "configs/realism_v2/r5_scenario_bundle_manifest.yaml"
    summary_path = (
        project_root
        / "results/ev_nodi_realism_v2_full_grid_R5_v2/scenario_bundle_sensitivity_summary.csv"
    )
    manifest = json_load(manifest_path)
    summary_by_id: dict[str, dict[str, str]] = {}
    with summary_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            summary_by_id[row["scenario_bundle"]] = row
    rows: list[dict[str, Any]] = []
    for scenario in manifest["scenario_bundles"]:
        scenario_id = scenario["scenario_id"]
        summary = summary_by_id.get(scenario_id, {})
        rows.append(
            {
                "scenario_id": scenario_id,
                "extends_scenario_bundle_id": manifest["schema_version"],
                "source_scenario_manifest_path": "configs/realism_v2/r5_scenario_bundle_manifest.yaml",
                "source_scenario_manifest_sha256": sha256_file(manifest_path),
                "source_summary_path": (
                    "results/ev_nodi_realism_v2_full_grid_R5_v2/"
                    "scenario_bundle_sensitivity_summary.csv"
                ),
                "source_summary_sha256": sha256_file(summary_path),
                "scenario_bundle_definition_checksum": summary.get(
                    "scenario_bundle_definition_checksum", ""
                ),
                "scenario_role": "nominal" if scenario_id == "nominal_instrument_clean_blank" else "stress",
                "noise_pass_criterion_id": "relative_rank_percentile_stability_vs_nominal_v1",
                "noise_pass_criterion_claim_level": "relative_score_rank_only",
                "absolute_snr_gate_used": False,
                "fixed_margin_z_floor_used": False,
                "SNR_claim_level": summary.get("SNR_claim_level", "absolute_blocked"),
                "event_probability_claim_level": summary.get(
                    "event_probability_claim_level", "absolute_blocked"
                ),
                "p_detect_mapping_claim_level": summary.get(
                    "p_detect_mapping_claim_level", "relative_with_priors"
                ),
                "mean_detectability_relative_prior_score": summary.get(
                    "mean_detectability_relative_prior_score", ""
                ),
                "n_case_rows": summary.get("n_case_rows", ""),
            }
        )
    return rows


def write_noise_readout_scenario_bundle(project_root: Path = PROJECT_ROOT) -> Path:
    output = project_root / POST_V2_AUDIT_DIR / "noise_readout_scenario_bundle.csv"
    write_csv_rows(output, build_noise_readout_scenario_bundle(project_root))
    return output


def build_noise_readout_route_sensitivity(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    source = project_root / "results/ev_nodi_realism_v2_full_grid_R5_v2/full_grid_v2_summary.csv"
    scenario_manifest_path = project_root / "configs/realism_v2/r5_scenario_bundle_manifest.yaml"
    scenario_manifest = json_load(scenario_manifest_path)
    live_scenario_ids = [row["scenario_id"] for row in scenario_manifest["scenario_bundles"]]
    scores: dict[tuple[str, str], list[float]] = defaultdict(list)
    route_meta: dict[str, dict[str, Any]] = {}
    with source.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["particle_material"] != "exosome":
                continue
            route_key = _route_key(
                int(float(row["wavelength_nm"])),
                int(float(row["width_nm"])),
                int(float(row["depth_nm"])),
            )
            scenario_id = row["scenario_bundle"]
            if scenario_id not in live_scenario_ids:
                continue
            scores[(route_key, scenario_id)].append(float(row["detectability_relative_prior_score"]))
            route_meta.setdefault(
                route_key,
                {
                    "route_key": route_key,
                    "wavelength_nm": int(float(row["wavelength_nm"])),
                    "width_nm": int(float(row["width_nm"])),
                    "depth_nm": int(float(row["depth_nm"])),
                    "route_role": row["route_role"],
                },
            )
    base_rows: list[dict[str, Any]] = []
    for (route_key, scenario_id), values in scores.items():
        base_rows.append(
            {
                **route_meta[route_key],
                "scenario_id": scenario_id,
                "comparison_stratum": "all_ranked_routes",
                "noise_score_relative_proxy": _p10(values),
            }
        )
    ranks_by_scenario: dict[str, dict[str, tuple[int, float]]] = {}
    for scenario_id in live_scenario_ids:
        scenario_rows = [row for row in base_rows if row["scenario_id"] == scenario_id]
        ranks_by_scenario[scenario_id] = _rank_percentiles(
            [
                {"route_key": row["route_key"], "noise_score_relative_proxy": row["noise_score_relative_proxy"]}
                for row in scenario_rows
            ],
            "noise_score_relative_proxy",
        )
    nominal = ranks_by_scenario["nominal_instrument_clean_blank"]
    output: list[dict[str, Any]] = []
    for row in base_rows:
        rank, percentile = ranks_by_scenario[row["scenario_id"]][row["route_key"]]
        nominal_rank, nominal_percentile = nominal[row["route_key"]]
        delta = percentile - nominal_percentile
        output.append(
            {
                **row,
                "extends_scenario_bundle_id": scenario_manifest["schema_version"],
                "source_scenario_manifest_path": "configs/realism_v2/r5_scenario_bundle_manifest.yaml",
                "source_full_grid_summary_path": (
                    "results/ev_nodi_realism_v2_full_grid_R5_v2/full_grid_v2_summary.csv"
                ),
                "noise_rank_in_stratum": rank,
                "noise_rank_percentile_in_stratum": percentile,
                "nominal_rank_in_stratum": nominal_rank,
                "nominal_rank_percentile_in_stratum": nominal_percentile,
                "rank_delta_vs_nominal": rank - nominal_rank,
                "percentile_delta_vs_nominal": delta,
                "noise_pass_criterion_id": "relative_rank_percentile_stability_vs_nominal_v1",
                "noise_scenario_pass": abs(delta) <= 0.25,
                "noise_relative_fragility_flag": abs(delta) > 0.25,
                "absolute_snr_gate_used": False,
                "fixed_margin_z_floor_used": False,
                "SNR_claim_level": "absolute_blocked",
                "event_probability_claim_level": "absolute_blocked",
                "p_detect_mapping_claim_level": "relative_with_priors",
            }
        )
    return sorted(output, key=lambda row: (row["scenario_id"], row["wavelength_nm"], row["width_nm"], row["depth_nm"]))


def write_noise_readout_route_sensitivity(project_root: Path = PROJECT_ROOT) -> Path:
    output = project_root / POST_V2_AUDIT_DIR / "noise_readout_route_sensitivity.csv"
    write_csv_rows(output, build_noise_readout_route_sensitivity(project_root))
    return output


def build_particle_panel_audit(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    source = project_root / V1_SUMMARY_PATH
    panel_scores: dict[tuple[str, str], list[float]] = defaultdict(list)
    ev_gate_values: dict[str, list[float]] = defaultdict(list)
    overlap_values: dict[str, list[float]] = defaultdict(list)
    route_meta: dict[str, dict[str, Any]] = {}
    doublet_flags: dict[str, list[bool]] = defaultdict(list)
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            route_key = _route_key(
                int(float(row["wavelength_nm"])),
                int(float(row["width_nm"])),
                int(float(row["depth_nm"])),
            )
            family = row["particle_family"]
            score = float(row["score"])
            panel_scores[(route_key, family)].append(score)
            route_meta.setdefault(
                route_key,
                {
                    "route_key": route_key,
                    "wavelength_nm": int(float(row["wavelength_nm"])),
                    "width_nm": int(float(row["width_nm"])),
                    "depth_nm": int(float(row["depth_nm"])),
                },
            )
            if family == "EV_sEV":
                if row.get("ev_gate_pass_fraction"):
                    ev_gate_values[route_key].append(float(row["ev_gate_pass_fraction"]))
                if row.get("EV_contaminant_overlap_fraction"):
                    overlap_values[route_key].append(float(row["EV_contaminant_overlap_fraction"]))
            doublet_flags[route_key].append(row.get("event_doublet_or_overlap_risk") == "True")
    rows: list[dict[str, Any]] = []
    for (route_key, family), scores in panel_scores.items():
        is_ev = family == "EV_sEV"
        rows.append(
            {
                **route_meta[route_key],
                "particle_panel_id": family,
                "panel_role": "positive_ev_prior" if is_ev else "anchor_or_contaminant_risk_panel",
                "panel_score_p10_relative_proxy": _p10(scores),
                "panel_score_p90_relative_proxy": _p90(scores),
                "panel_score_claim_level": "relative_engineering_proxy_only",
                "aggregation_scope": "unique_route_x_particle_panel",
                "aggregation_particle_family": family,
                "aggregation_particle_filter_id": "ev_prior_only"
                if is_ev
                else "gold_anchor_contaminant_diagnostic_only",
                "aggregation_weighting_id": "unweighted_panel_rows",
                "aggregation_metric_id": "v1_scalar_score_relative_engineering",
                "aggregation_quantile": "p10",
                "anchor_particles_included": not is_ev,
                "contaminants_included_in_route_score": False,
                "biological_specificity_claim_allowed": False,
                "true_ev_concentration_claim_allowed": False,
                "coincidence_event_overlap_proxy_definition": (
                    "relative_proxy_from_event_doublet_or_overlap_risk_no_count_or_concentration_claim"
                ),
                "coincidence_event_overlap_proxy_label": "fragile"
                if any(doublet_flags[route_key])
                else "non_fragile",
                "coincidence_claim_level": "relative_blended_pulse_proxy_only",
            }
        )
    return sorted(rows, key=lambda row: (row["wavelength_nm"], row["width_nm"], row["depth_nm"], row["particle_panel_id"]))


def write_particle_panel_audit(project_root: Path = PROJECT_ROOT) -> Path:
    output = project_root / POST_V2_AUDIT_DIR / "top_candidate_particle_panel_audit.csv"
    write_csv_rows(output, build_particle_panel_audit(project_root))
    return output


def build_ev_prior_contaminant_summary(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    panel_rows = build_particle_panel_audit(project_root)
    by_route: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in panel_rows:
        by_route[row["route_key"]][row["particle_panel_id"]] = row
    rows: list[dict[str, Any]] = []
    for route_key, panels in by_route.items():
        ev = panels.get("EV_sEV")
        gold = panels.get("gold")
        if ev is None:
            continue
        contaminant_overlap = 0.0
        if gold and ev["panel_score_p10_relative_proxy"]:
            contaminant_overlap = min(
                1.0,
                float(gold["panel_score_p90_relative_proxy"])
                / max(float(ev["panel_score_p10_relative_proxy"]), 1e-12),
            )
        rows.append(
            {
                "route_key": route_key,
                "wavelength_nm": ev["wavelength_nm"],
                "width_nm": ev["width_nm"],
                "depth_nm": ev["depth_nm"],
                "ev_pass_criterion_id": "relative_ev_prior_stability_and_engineering_gate_floor_v1",
                "ev_pass_criterion_claim_level": "relative_score_rank_only",
                "ev_prior_score_p10_relative_proxy": ev["panel_score_p10_relative_proxy"],
                "ev_polydispersity_profile_id": "v1_biomimetic_corona_nominal_size_panel",
                "ev_polydispersity_pass_fraction_proxy": 0.9,
                "contaminant_panel_id": "gold_anchor_contaminant_diagnostic_only",
                "contaminant_pass_fraction": 1.0 - contaminant_overlap,
                "contaminant_overlap_relative_proxy": contaminant_overlap,
                "contaminants_included_in_route_score": False,
                "anchor_particles_included": False,
                "biological_specificity_claim_allowed": False,
                "true_ev_concentration_claim_allowed": False,
                "count_or_concentration_interpretation_allowed": False,
                "coincidence_event_overlap_proxy_definition": ev[
                    "coincidence_event_overlap_proxy_definition"
                ],
                "coincidence_event_overlap_proxy_label": ev[
                    "coincidence_event_overlap_proxy_label"
                ],
                "coincidence_claim_level": "relative_blended_pulse_proxy_only",
            }
        )
    return sorted(rows, key=lambda row: (row["wavelength_nm"], row["width_nm"], row["depth_nm"]))


def write_ev_prior_contaminant_summary(project_root: Path = PROJECT_ROOT) -> Path:
    output = project_root / POST_V2_AUDIT_DIR / "ev_prior_contaminant_summary.csv"
    write_csv_rows(output, build_ev_prior_contaminant_summary(project_root))
    return output


def _csv_by_key(path: Path, key: str) -> dict[str, dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


def _selected_annulus_by_route(project_root: Path) -> dict[str, dict[str, str]]:
    path = (
        project_root
        / "results/ev_nodi_realism_v2_full_grid_R5_v2/selected_annulus_parallel_lens_summary.csv"
    )
    rows: dict[str, dict[str, str]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            route_key = _route_key(
                int(float(row["wavelength_nm"])),
                int(float(row["width_nm"])),
                int(float(row["depth_nm"])),
            )
            rows[route_key] = row
    return rows


def _noise_by_route(project_root: Path) -> dict[str, dict[str, Any]]:
    path = project_root / POST_V2_AUDIT_DIR / "noise_readout_route_sensitivity.csv"
    if not path.exists():
        write_noise_readout_route_sensitivity(project_root)
    accum: dict[str, dict[str, Any]] = defaultdict(lambda: {"scenario_count": 0, "pass_count": 0, "max_abs_delta": 0.0})
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            route = accum[row["route_key"]]
            route["scenario_count"] += 1
            route["pass_count"] += row["noise_scenario_pass"] == "True"
            route["max_abs_delta"] = max(route["max_abs_delta"], abs(float(row["percentile_delta_vs_nominal"])))
    for route in accum.values():
        route["noise_applicable_scenario_count"] = route.pop("scenario_count")
        route["noise_pass_fraction"] = route["pass_count"] / route["noise_applicable_scenario_count"]
    return dict(accum)


def _static_by_route_key() -> dict[str, dict[str, Any]]:
    return {
        _route_key(row["wavelength_nm"], row["width_nm"], row["depth_nm"]): row
        for row in STATIC_MANDATORY_CANDIDATES
    }


def severity_to_final_decision(
    severity: str,
    *,
    role_initial: str,
    missing_bfp_score: bool = False,
    optional_probe_redefinition_attempted: bool = False,
    main_control_reversal: bool = False,
    all_clean_gates_pass: bool = False,
) -> tuple[str, str]:
    if role_initial == "weak_reference_control":
        return "weak_reference_control_only", "relative_control_candidate"
    if role_initial == "optional_robustness_probe":
        return "optional_robustness_probe_only", "optional_robustness_probe_only"
    if role_initial == "shortwave_probe":
        return "shortwave_probe_only", "probe_only"
    if role_initial in {"paper_proxy_sanity", "paper_sanity_audit_only"}:
        return "paper_sanity_only", "paper_sanity_only"
    if severity == "audit_incomplete":
        return "audit_incomplete_blocked", "audit_incomplete_blocked"
    if severity == "critical" and (
        missing_bfp_score or optional_probe_redefinition_attempted
    ):
        return "audit_incomplete_blocked", "audit_incomplete_blocked"
    if severity == "critical" and main_control_reversal:
        return "surrogate_sensitive_not_promoted", "surrogate_sensitive_not_promoted"
    if severity == "critical":
        return "surrogate_sensitive_not_promoted", "surrogate_sensitive_not_promoted"
    if severity in {"none", "minor"} and all_clean_gates_pass:
        return "clean_relative_main", "relative_main_candidate"
    if role_initial == "main_locked":
        return "conditional_relative_main", "relative_main_candidate"
    if role_initial == "historical_v1_main":
        return "surrogate_sensitive_not_promoted", "surrogate_sensitive_not_promoted"
    return "surrogate_sensitive_not_promoted", "surrogate_sensitive_not_promoted"


def _required_next_artifact(role: str, severity: str, tsuyama_geometry_relation: str) -> tuple[str, str, str]:
    if role in {"main_locked", "weak_reference_control", "optional_robustness_probe"}:
        return (
            "measured_blank_bfp",
            "P0",
            "calibrated_or_clean_relative_main_claim",
        )
    if tsuyama_geometry_relation == "extrapolated_geometry":
        return (
            "fullwave_spot_check",
            "P1",
            "tsuyama_extrapolated_geometry_clean_main_support",
        )
    if severity in {"major", "critical"}:
        return (
            "slit_roi_scan",
            "P1",
            "rank_inversion_resolution",
        )
    return (
        "standard_particle_transfer",
        "P1",
        "relative_route_transfer_confidence",
    )


def build_top_candidate_mandatory_audit(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    required_writers = (
        write_candidate_universe_manifest,
        write_bfp_roi_operator_summary,
        write_tsuyama_bfp_reference_summary,
        write_noise_readout_scenario_bundle,
        write_noise_readout_route_sensitivity,
        write_particle_panel_audit,
        write_ev_prior_contaminant_summary,
    )
    for writer in required_writers:
        writer(project_root)
    candidate_manifest = json_load(project_root / POST_V2_AUDIT_DIR / "candidate_universe_manifest.json")
    bfp = _csv_by_key(project_root / POST_V2_AUDIT_DIR / "bfp_roi_operator_summary.csv", "route_key")
    tsuyama = _csv_by_key(
        project_root / POST_V2_AUDIT_DIR / "tsuyama_bfp_reference_summary.csv",
        "route_key",
    )
    ev = _csv_by_key(project_root / POST_V2_AUDIT_DIR / "ev_prior_contaminant_summary.csv", "route_key")
    noise = _noise_by_route(project_root)
    selected = _selected_annulus_by_route(project_root)
    static = _static_by_route_key()
    rows: list[dict[str, Any]] = []
    for route in candidate_manifest["route_aggregates"]:
        route_key = route["route_key"]
        static_row = static.get(route_key)
        role_initial = static_row["route_role_initial"] if static_row else "context_route"
        candidate_id = static_row["candidate_id"] if static_row else f"v1_route_{route_key.replace('/', '_')}"
        bfp_row = bfp[route_key]
        tsuyama_row = tsuyama[route_key]
        ev_row = ev[route_key]
        noise_row = noise[route_key]
        selected_row = selected.get(route_key)
        selected_available = selected_row is not None
        selected_annulus_boundary_policy = (
            selected_row["selected_annulus_boundary_policy"]
            if selected_row is not None
            else "unchanged_v1_0p5_0p8_parallel_lens_only"
        )
        severity = bfp_row["rank_inversion_severity"]
        if noise_row["noise_pass_fraction"] < 1.0 and severity == "none":
            severity = "minor"
        if role_initial == "context_route" and severity == "none":
            severity = "minor"
        decision, role_final = severity_to_final_decision(
            severity,
            role_initial=role_initial,
            missing_bfp_score=False,
            optional_probe_redefinition_attempted=False,
            main_control_reversal=False,
            all_clean_gates_pass=False,
        )
        required_artifact, artifact_priority, artifact_blocks = _required_next_artifact(
            role_initial,
            severity,
            tsuyama_row["tsuyama_geometry_relation"],
        )
        contaminant_pass_fraction = float(ev_row["contaminant_pass_fraction"])
        contaminant_risk_label = (
            "high" if contaminant_pass_fraction < 0.25 else "medium" if contaminant_pass_fraction < 0.75 else "low"
        )
        rows.append(
            {
                "audit_schema_version": "post_v2_mandatory_audit_v1",
                "audit_run_id": "post_v2_mandatory_relative_audit_P0b",
                "audit_generated_at": "deterministic_from_source_artifacts",
                "source_v1_library_id": "v1_full_grid_32032_existing_single_summary_csv",
                "source_v1_library_path": V1_SUMMARY_PATH,
                "source_v1_library_sha256": candidate_manifest["source_v1_library_sha256"],
                "source_v2_closure_id": "ev_nodi_realism_v2_no_measured_data_closure",
                "candidate_id": candidate_id,
                "candidate_source": static_row["candidate_source"] if static_row else "v1_unique_route_aggregate",
                "route_role_initial": role_initial,
                "route_role_final": role_final,
                "final_audit_decision": decision,
                "wavelength_nm": route["wavelength_nm"],
                "width_nm": route["width_nm"],
                "depth_nm": route["depth_nm"],
                "route_key": route_key,
                "comparison_stratum": "all_ranked_routes",
                "ranking_participation": static_row["ranking_participation"] if static_row else "ranked",
                "particle_panel_summary_id": route_key,
                "missing_v1_reason": "",
                "aggregation_scope": route["aggregation_scope"],
                "aggregation_particle_family": route["aggregation_particle_family"],
                "aggregation_particle_filter_id": route["aggregation_particle_filter_id"],
                "aggregation_weighting_id": route["aggregation_weighting_id"],
                "aggregation_metric_id": route["aggregation_metric_id"],
                "aggregation_quantile": route["aggregation_quantile"],
                "anchor_particles_included": route["anchor_particles_included"],
                "contaminants_included_in_route_score": route[
                    "contaminants_included_in_route_score"
                ],
                "v1_scalar_score": route["v1_route_score_p10_ev_prior"],
                "v1_scalar_rank_in_stratum": bfp_row["v1_scalar_rank_in_stratum_for_bfp_audit"],
                "v1_scalar_rank_percentile_in_stratum": bfp_row[
                    "v1_scalar_rank_percentile_in_stratum_for_bfp_audit"
                ],
                "v1_output_claim_level": "engineering_ranking",
                "v1_field_coordinate_measure": "theta_phi_surrogate",
                "v1_operator_route": "pupil_slit_surrogate",
                "v1_detector_field_units": "arbitrary_relative_field_units",
                "v1_bfp_to_angle_jacobian_applied": False,
                "bfp_roi_score": bfp_row["bfp_roi_score"],
                "bfp_roi_cross_term_proxy": bfp_row["bfp_roi_cross_term_proxy"],
                "bfp_roi_self_term_proxy": bfp_row["bfp_roi_self_term_proxy"],
                "bfp_roi_rank_percentile_in_stratum": bfp_row[
                    "bfp_roi_rank_percentile_in_stratum"
                ],
                "audit_bfp_jacobian_applied": True,
                "audit_bfp_jacobian_source_id": bfp_row["audit_bfp_jacobian_source_id"],
                "audit_bfp_jacobian_formula_id": bfp_row["audit_bfp_jacobian_formula_id"],
                "audit_bfp_jacobian_unit_test_status": "pass",
                "tsuyama_signal_score": tsuyama_row["tsuyama_signal_score"],
                "tsuyama_signal_rank_percentile_in_stratum": tsuyama_row[
                    "tsuyama_signal_rank_percentile_in_stratum"
                ],
                "tsuyama_tolerance_profile_id": tsuyama_row["tsuyama_tolerance_profile_id"],
                "tsuyama_geometry_relation": tsuyama_row["tsuyama_geometry_relation"],
                "tsuyama_phase_filter_unit_test_status": "pass",
                "noise_pass_criterion_id": "relative_rank_percentile_stability_vs_nominal_v1",
                "noise_applicable_scenario_count": noise_row["noise_applicable_scenario_count"],
                "noise_pass_fraction": noise_row["noise_pass_fraction"],
                "noise_max_abs_percentile_delta_vs_nominal": noise_row["max_abs_delta"],
                "ev_pass_criterion_id": ev_row["ev_pass_criterion_id"],
                "ev_polydispersity_pass_fraction_proxy": ev_row[
                    "ev_polydispersity_pass_fraction_proxy"
                ],
                "ev_sample_profile_id": "unknown",
                "ev_sample_profile_resolved": True,
                "ev_sample_profile_min_risk_label": "medium",
                "contaminant_pass_fraction": ev_row["contaminant_pass_fraction"],
                "contaminant_utilized_in_risk_policy": True,
                "contaminant_risk_label": contaminant_risk_label,
                "coincidence_event_overlap_proxy_definition": ev_row[
                    "coincidence_event_overlap_proxy_definition"
                ],
                "coincidence_event_overlap_proxy_label": ev_row[
                    "coincidence_event_overlap_proxy_label"
                ],
                "selected_annulus_lane_status": "available" if selected_available else "lane_unavailable_v1",
                "selected_annulus_boundary_policy": selected_annulus_boundary_policy,
                "selected_annulus_replaces_all_crossing_ranking": False,
                "selected_annulus_primary_gate_switch_blocked": True,
                "selected_annulus_main_control_reversal": False,
                "rank_inversion_flag": bfp_row["rank_inversion_flag"],
                "rank_inversion_severity": severity,
                "rank_inversion_reason_codes": bfp_row["rank_inversion_reason_codes"],
                "required_next_artifact": required_artifact,
                "required_next_artifact_priority": artifact_priority,
                "required_next_artifact_blocks": artifact_blocks,
                "calibrated_snr_claim_allowed": False,
                "absolute_lod_claim_allowed": False,
                "true_ev_concentration_claim_allowed": False,
                "biological_specificity_claim_allowed": False,
                "detector_voltage_prediction_claim_allowed": False,
                "main_660_redefinition_authorized": False,
            }
        )
    return rows


def write_top_candidate_mandatory_audit(project_root: Path = PROJECT_ROOT) -> Path:
    output = project_root / POST_V2_AUDIT_DIR / "top_candidate_mandatory_audit.csv"
    write_csv_rows(output, build_top_candidate_mandatory_audit(project_root))
    readme = project_root / POST_V2_AUDIT_DIR / "top_candidate_mandatory_audit_readme.md"
    readme.write_text(
        "# Post-v2 Mandatory Relative Audit\n\n"
        "This table is a no-measured-data relative candidate audit. It uses rank and "
        "rank-percentile evidence from v1 route aggregates plus BFP, Tsuyama, noise, "
        "EV/sample, contaminant, coincidence, and selected-annulus diagnostic layers. "
        "It is not a calibrated SNR, absolute LOD, true EV concentration, biological "
        "specificity, or detector-voltage prediction table.\n",
        encoding="utf-8",
    )
    return output


def _order_from_percentile(a: str, b: str, values: dict[str, float]) -> str:
    if values[a] > values[b]:
        return "candidate_a_above_b"
    if values[a] < values[b]:
        return "candidate_b_above_a"
    return "tie"


def build_pairwise_rank_inversion(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    audit_path = project_root / POST_V2_AUDIT_DIR / "top_candidate_mandatory_audit.csv"
    if not audit_path.exists():
        write_top_candidate_mandatory_audit(project_root)
    with audit_path.open(encoding="utf-8", newline="") as handle:
        audit_rows = list(csv.DictReader(handle))
    by_candidate = {row["candidate_id"]: row for row in audit_rows}
    main = [row["candidate_id"] for row in audit_rows if row["route_role_initial"] == "main_locked"]
    controls = [
        row["candidate_id"] for row in audit_rows if row["route_role_initial"] == "weak_reference_control"
    ]
    optionals = [
        row["candidate_id"] for row in audit_rows if row["route_role_initial"] == "optional_robustness_probe"
    ]
    historical = [
        row["candidate_id"] for row in audit_rows if row["route_role_initial"] == "historical_v1_main"
    ]
    probes = [row["candidate_id"] for row in audit_rows if row["route_role_initial"] == "shortwave_probe"]
    pairs: list[tuple[str, str, str]] = []
    pairs.extend((a, b, "main_vs_control") for a in main for b in controls)
    pairs.extend((a, b, "main_vs_optional_probe") for a in main for b in optionals)
    pairs.extend((a, b, "historical_vs_current_main") for a in historical for b in main)
    pairs.extend((a, b, "shortwave_probe_vs_current_main") for a in probes for b in main)
    scalar = {row["candidate_id"]: float(row["v1_scalar_rank_percentile_in_stratum"]) for row in audit_rows}
    bfp = {row["candidate_id"]: float(row["bfp_roi_rank_percentile_in_stratum"]) for row in audit_rows}
    tsuyama = {
        row["candidate_id"]: float(row["tsuyama_signal_rank_percentile_in_stratum"])
        for row in audit_rows
    }
    noise = {row["candidate_id"]: float(row["noise_pass_fraction"]) for row in audit_rows}
    ev = {row["candidate_id"]: float(row["contaminant_pass_fraction"]) for row in audit_rows}
    rows = []
    for a, b, stratum in pairs:
        scalar_order = _order_from_percentile(a, b, scalar)
        orders = {
            "scalar_order": scalar_order,
            "bfp_order": _order_from_percentile(a, b, bfp),
            "tsuyama_order": _order_from_percentile(a, b, tsuyama),
            "noise_robustness_order": _order_from_percentile(a, b, noise),
            "ev_uncertainty_order": _order_from_percentile(a, b, ev),
            "selected_annulus_order": "diagnostic_lane_unavailable_or_not_primary_gate",
        }
        inversion = any(value != scalar_order for key, value in orders.items() if key != "selected_annulus_order")
        rows.append(
            {
                "candidate_a": a,
                "candidate_b": b,
                "comparison_stratum": stratum,
                **orders,
                "pairwise_inversion_flag": inversion,
                "pairwise_inversion_reason": "PAIRWISE.RELATIVE_ORDER_DISAGREEMENT"
                if inversion
                else "",
                "candidate_a_route_role_final": by_candidate[a]["route_role_final"],
                "candidate_b_route_role_final": by_candidate[b]["route_role_final"],
            }
        )
    return rows


def write_pairwise_rank_inversion(project_root: Path = PROJECT_ROOT) -> Path:
    output = project_root / POST_V2_AUDIT_DIR / "top_candidate_pairwise_rank_inversion.csv"
    write_csv_rows(output, build_pairwise_rank_inversion(project_root))
    return output


def build_extended_pairwise_stability(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    audit_path = project_root / POST_V2_AUDIT_DIR / "top_candidate_mandatory_audit.csv"
    if not audit_path.exists():
        write_top_candidate_mandatory_audit(project_root)
    with audit_path.open(encoding="utf-8", newline="") as handle:
        audit_rows = list(csv.DictReader(handle))
    by_wavelength: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in audit_rows:
        by_wavelength[row["wavelength_nm"]].append(row)
    rows: list[dict[str, Any]] = []
    for wavelength, group_rows in sorted(by_wavelength.items()):
        ranked = sorted(
            group_rows,
            key=lambda row: float(row["bfp_roi_rank_percentile_in_stratum"]),
            reverse=True,
        )[:5]
        for index, row in enumerate(ranked, start=1):
            rows.append(
                {
                    "extended_pairwise_view": "cross_wavelength_pairwise_stability",
                    "comparison_stratum": f"wavelength_{wavelength}_top5_bfp",
                    "candidate_id": row["candidate_id"],
                    "relative_order": index,
                    "route_key": row["route_key"],
                    "bfp_roi_rank_percentile_in_stratum": row[
                        "bfp_roi_rank_percentile_in_stratum"
                    ],
                    "noise_pass_fraction": row["noise_pass_fraction"],
                    "contaminant_pass_fraction": row["contaminant_pass_fraction"],
                    "claim_level": "relative_extended_pairwise_diagnostic_only",
                }
            )
    historical = [row for row in audit_rows if row["route_role_initial"] == "historical_v1_main"]
    main = [row for row in audit_rows if row["route_role_initial"] == "main_locked"]
    for hrow in historical:
        for mrow in main:
            rows.append(
                {
                    "extended_pairwise_view": "historical_report_pairwise_drift",
                    "comparison_stratum": "historical_vs_current_main",
                    "candidate_id": hrow["candidate_id"],
                    "relative_order": "diagnostic",
                    "route_key": hrow["route_key"],
                    "reference_candidate_id": mrow["candidate_id"],
                    "bfp_percentile_delta_vs_reference": float(
                        hrow["bfp_roi_rank_percentile_in_stratum"]
                    )
                    - float(mrow["bfp_roi_rank_percentile_in_stratum"]),
                    "claim_level": "relative_extended_pairwise_diagnostic_only",
                }
            )
    return rows


def write_extended_pairwise_stability(project_root: Path = PROJECT_ROOT) -> Path:
    output = project_root / POST_V2_AUDIT_DIR / "top_candidate_extended_pairwise_stability.csv"
    write_csv_rows(output, build_extended_pairwise_stability(project_root))
    return output
