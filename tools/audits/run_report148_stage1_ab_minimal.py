#!/usr/bin/env python3
# pyright: reportAttributeAccessIssue=false, reportCallIssue=false, reportArgumentType=false, reportGeneralTypeIssues=false
from __future__ import annotations

import argparse
import hashlib
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.config import THETA_GRID_RAD, medium_for_particle, particle_from_name  # noqa: E402
from nodi_simulator.bfp_detector_operator import compute_projected_detector_terms  # noqa: E402
from nodi_simulator.detector_route_assembly import compute_r_self  # noqa: E402
from nodi_simulator.intrinsic_scattering import compute_intrinsic_scattering  # noqa: E402
from nodi_simulator.parameter_sweep import run_single_case_batch_shared_event_normalization_views  # noqa: E402
from nodi_simulator.reference_field import compute_reference_field  # noqa: E402
from nodi_simulator.utils import build_collection_operator, compute_detected_scattering_field  # noqa: E402
from tools._common import write_json_file  # noqa: E402
from tools.audits import ev_size_weighted_route_analysis as route_analysis  # noqa: E402
from tools.audits import tsuyama_gold_aligned_detection_lane as lane  # noqa: E402
from tools.lens_b_ev_gold_fullgrid_runner import (  # noqa: E402
    _cfg_for_normalization_lane,
    _fixed_660_e_sca_ref,
    _per_wavelength_e_sca_ref,
    build_frozen_b_cfg,
)


SOURCE_SUMMARY = Path("results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv")
NORMALIZATION_VIEWS = ("fixed_660_gold", "per_wavelength_gold")
ROUTE_MODEL_CATALOG = {
    "A_hybrid": "joint_overlap_coherent_surrogate",
    "B_roi_intensity": "roi_intensity_integral",
    "C_collapsed_coherent": "collapsed_scalar_surrogate",
    "D_cross_only": "cross_only_joint_overlap_diagnostic",
}
SEEDS = (11, 22, 33)
EV_SUBSET_DIAMETERS_NM = (60, 80, 100, 120, 140, 160)
GOLD_ANCHOR_DIAMETERS_NM = (20, 40, 60)
PRIOR_NAME = "sharp_msc_sev_empirical"
READOUT_POLICY = "R2_absolute"
GAUGE_MODES = ("V1_gauge_locked", "V2_raw_angular")
RAW_REFERENCE_NORMALIZATION_MODE = "rho_g_reference_amplitude"
RAW_SCATTERING_NORMALIZATION_MODE = "per_case_au20_sca_baseline"
NOISE_POLICY = "common_noise_control"
CLAIM_LEVEL = "candidate_families_under_detector_surrogates"
ROUTE_SCOPE_LABELS = {
    "A_hybrid": "A",
    "B_roi_intensity": "B",
    "C_collapsed_coherent": "C",
    "D_cross_only": "D",
}
GAUGE_SCOPE_LABELS = {
    "V1_gauge_locked": "V1",
    "V2_raw_angular": "V2",
}


@dataclass(frozen=True)
class PanelRoute:
    wavelength_nm: int
    width_nm: int
    depth_nm: int
    route_family_id: str
    route_family_note: str


@dataclass(frozen=True)
class CaseTask:
    route: PanelRoute
    particle_name: str
    seed: int
    detector_route_id: str
    detector_forward_model: str
    gauge_mode: str
    n_events: int


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _detector_route_flip_flag_404_660(
    fixed_view_winner_wavelength: int,
    per_wavelength_view_winner_wavelength: int,
) -> bool:
    """Return whether the two normalization views select different wavelengths."""
    return int(fixed_view_winner_wavelength) != int(per_wavelength_view_winner_wavelength)


def _run_scope_statement(
    detector_route_ids: tuple[str, ...],
    gauge_modes: tuple[str, ...],
) -> str:
    route_scope = "/".join(ROUTE_SCOPE_LABELS[route_id] for route_id in detector_route_ids)
    gauge_scope = "+".join(GAUGE_SCOPE_LABELS[gauge_mode] for gauge_mode in gauge_modes)
    return f"{route_scope}: {gauge_scope}; R2 only"


def _event_accounting(
    *,
    case_row_count: int,
    n_events: int,
    normalization_view_count: int,
) -> dict[str, int | str]:
    if normalization_view_count <= 0:
        raise ValueError("normalization_view_count must be positive")
    if case_row_count % normalization_view_count:
        raise ValueError("case rows must divide evenly across shared normalization views")
    distinct_physical_case_count = case_row_count // normalization_view_count
    return {
        "event_accounting_contract": "normalization_views_share_one_physical_event_stream",
        "case_row_count": int(case_row_count),
        "case_row_events": int(case_row_count * n_events),
        "distinct_physical_case_count": int(distinct_physical_case_count),
        "distinct_physical_events": int(distinct_physical_case_count * n_events),
    }


def _seed_coverage_rows(
    case_df: pd.DataFrame,
    *,
    expected_seeds: tuple[int, ...] = SEEDS,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    group_columns = ["detector_route_id", "readout_policy", "gauge_mode"]
    expected = sorted(int(seed) for seed in expected_seeds)
    for keys, group in case_df.groupby(group_columns, sort=True):
        detector_route_id, readout_policy, gauge_mode = keys
        observed = sorted(pd.to_numeric(group["seed"], errors="raise").astype(int).unique().tolist())
        missing = sorted(set(expected) - set(observed))
        rows.append(
            {
                "detector_route_id": str(detector_route_id),
                "readout_policy": str(readout_policy),
                "gauge_mode": str(gauge_mode),
                "expected_seeds": ",".join(str(seed) for seed in expected),
                "observed_seeds": ",".join(str(seed) for seed in observed),
                "expected_seed_count": len(expected),
                "observed_seed_count": len(observed),
                "missing_seeds": ",".join(str(seed) for seed in missing),
                "seed_coverage_status": "complete" if not missing else "incomplete",
                "normalization_views": ",".join(
                    sorted(group["normalization_view"].astype(str).unique().tolist())
                ),
                "case_row_count": int(len(group)),
            }
        )
    return pd.DataFrame(rows)


def default_route_panel() -> list[PanelRoute]:
    return [
        PanelRoute(404, 500, 700, "lambda404_w500_middeep", "404 width-500 mid/deep family"),
        PanelRoute(404, 500, 1300, "lambda404_w500_middeep", "404 width-500 mid/deep family"),
        PanelRoute(404, 600, 700, "lambda404_w600_middeep", "404 width-600 mid/deep family"),
        PanelRoute(404, 600, 1300, "lambda404_w600_middeep", "404 width-600 mid/deep family"),
        PanelRoute(404, 700, 700, "lambda404_w700_middeep", "404 width-700 mid/deep family"),
        PanelRoute(404, 700, 1300, "lambda404_w700_middeep", "404 width-700 mid/deep family"),
        PanelRoute(660, 700, 900, "lambda660_w700_middeep", "660 width-700 mid/deep family"),
        PanelRoute(660, 700, 1300, "lambda660_w700_middeep", "660 width-700 mid/deep family"),
        PanelRoute(660, 800, 900, "lambda660_w800_middeep", "660 width-800 mid/deep family"),
        PanelRoute(660, 800, 1300, "lambda660_w800_middeep", "660 width-800 mid/deep family"),
    ]


def _load_source(path: Path) -> pd.DataFrame:
    required = [
        "particle_name",
        "particle_material",
        "particle_family",
        "particle_diameter_nm",
        "wavelength_nm",
        "width_nm",
        "depth_nm",
    ]
    if not path.exists():
        raise FileNotFoundError(f"source summary does not exist: {path}")
    return pd.read_csv(path, usecols=required, low_memory=False)


def _particle_names_from_diameters(
    frame: pd.DataFrame,
    *,
    material: str,
    diameters_nm: tuple[int, ...],
) -> list[str]:
    subset = frame[frame["particle_material"].astype(str).str.lower().eq(material)].copy()
    subset["particle_diameter_nm"] = pd.to_numeric(subset["particle_diameter_nm"], errors="raise").astype(int)
    subset["particle_name"] = subset["particle_name"].astype(str)
    names: list[str] = []
    missing: list[int] = []
    for diameter in diameters_nm:
        matched = subset[subset["particle_diameter_nm"].eq(int(diameter))]["particle_name"].unique().tolist()
        if not matched:
            missing.append(int(diameter))
            continue
        if len(matched) != 1:
            raise ValueError(f"expected one particle for {material} {diameter}nm, got {matched}")
        names.append(str(matched[0]))
    if missing:
        raise ValueError(f"missing {material} particles for diameters: {missing}")
    return names


def build_scope(source: pd.DataFrame) -> dict[str, Any]:
    routes = default_route_panel()
    available_routes = {
        (int(row.wavelength_nm), int(row.width_nm), int(row.depth_nm))
        for row in source[["wavelength_nm", "width_nm", "depth_nm"]].drop_duplicates().itertuples(index=False)
    }
    missing_routes = [route for route in routes if (route.wavelength_nm, route.width_nm, route.depth_nm) not in available_routes]
    if missing_routes:
        raise ValueError(f"panel routes missing from source: {missing_routes}")

    ev_names = _particle_names_from_diameters(
        source,
        material="exosome",
        diameters_nm=EV_SUBSET_DIAMETERS_NM,
    )
    gold_names = _particle_names_from_diameters(
        source,
        material="gold",
        diameters_nm=GOLD_ANCHOR_DIAMETERS_NM,
    )
    return {
        "routes": routes,
        "ev_particle_names": ev_names,
        "gold_anchor_names": gold_names,
        "particle_names": ev_names + gold_names,
        "ev_subset_selection_status": "inferred_from_sharp_msc_sev_prior_concentration_no_explicit_repo_list",
    }


def _build_v2_view_payload_overrides(
    *,
    particle: Any,
    medium: Any,
    channel: Any,
    optical: Any,
    cfg: Any,
    e_sca_ref: float,
) -> dict[str, dict[str, object]]:
    medium_refractive_index = float(medium.refractive_index_at(optical.wavelength_m))
    intrinsic = compute_intrinsic_scattering(
        particle,
        medium,
        optical.wavelength_m,
        THETA_GRID_RAD,
    )
    collection_medium_refractive_index = (
        float(intrinsic["k_m"]) * float(optical.wavelength_m) / (2.0 * np.pi)
    )
    collection_operator = build_collection_operator(
        intrinsic["theta_grid_rad"],
        channel,
        optical,
        cfg,
        medium_refractive_index=collection_medium_refractive_index,
    )
    collection = compute_detected_scattering_field(
        intrinsic,
        channel,
        optical,
        cfg,
        collection_operator=collection_operator,
    )
    reference = compute_reference_field(
        channel,
        optical,
        cfg,
        medium_refractive_index=medium_refractive_index,
    )
    projected = compute_projected_detector_terms(
        np.asarray(reference["reference_theta_grid_rad"], dtype=float),
        np.asarray(reference["reference_angular_field"], dtype=complex),
        np.asarray(collection["angular_field_theta"], dtype=complex),
        collection["collection_operator"],
        cfg,
        phi_grid_rad=np.asarray(reference["reference_phi_grid_rad"], dtype=float),
        scattering_theta_grid_rad=np.asarray(collection["theta_grid_rad"], dtype=float),
        rescale_to_collapsed_target=False,
    )

    sca_norm = float(e_sca_ref)
    sca_collapsed_norm = complex(projected["scattering_collapsed_raw"]) / sca_norm
    sca_self_collapsed = float(abs(sca_collapsed_norm) ** 2)
    self_roi_raw_norm = float(projected["self_scattering_intensity_roi"]) / max(sca_norm**2, 1e-30)

    ref_target = complex(reference.get("E_ref_complex", 0.0 + 0.0j))
    ref_collapsed_raw = complex(projected["reference_collapsed_raw"])
    if abs(ref_target) > 1e-30 and abs(ref_collapsed_raw) > 1e-30:
        ref_norm = float(abs(ref_collapsed_raw) / abs(ref_target))
    else:
        ref_norm = 1.0
    ref_collapsed_norm = ref_collapsed_raw / max(ref_norm, 1e-30)
    ref_intensity_norm = float(projected["reference_intensity_roi"]) / max(ref_norm**2, 1e-30)
    joint_norm = complex(projected["joint_overlap_complex"]) / max(ref_norm * sca_norm, 1e-30)
    cross_norm = float(2.0 * np.real(joint_norm))
    overlap_denominator = complex(ref_collapsed_norm * np.conj(sca_collapsed_norm))
    overlap_factor = (
        joint_norm / overlap_denominator
        if abs(overlap_denominator) > 1e-30
        else 1.0 + 0.0j
    )
    signal_detector_integrated = float(self_roi_raw_norm + cross_norm)
    scalar_signal = float(sca_self_collapsed + 2.0 * np.real(overlap_denominator))
    ratio = float(abs(signal_detector_integrated) / max(abs(scalar_signal), 1e-30))
    phase_disagreement = float(
        (np.angle(joint_norm) - np.angle(overlap_denominator) + np.pi) % (2.0 * np.pi) - np.pi
    )
    route_r_self = float(self_roi_raw_norm / max(sca_self_collapsed, 1e-30))

    return {
        "reference": {
            "A_ref": float(abs(ref_collapsed_norm)),
            "phi_ref_rad": float(np.angle(ref_collapsed_norm)),
            "E_ref_complex": complex(ref_collapsed_norm),
            "I_ref_detector_integrated": float(ref_intensity_norm),
            "self_sca_detector_integrated": float(self_roi_raw_norm),
            "signal_detector_integrated": float(signal_detector_integrated),
            "cross_term_detector_integrated": float(cross_norm),
            "roi_vs_scalar_signal_ratio": float(ratio),
            "roi_vs_scalar_phase_disagreement_rad": float(phase_disagreement),
            "interference_overlap_factor_complex": complex(overlap_factor),
            "interference_overlap_factor_abs": float(abs(overlap_factor)),
            "interference_overlap_factor_phase_rad": float(np.angle(overlap_factor)),
            "interference_overlap_status": (
                "aligned"
                if np.isclose(abs(overlap_factor - 1.0), 0.0, atol=1e-3)
                else "mismatch_auditable"
            ),
            "raw_reference_normalization_mode": RAW_REFERENCE_NORMALIZATION_MODE,
            "raw_scattering_normalization_mode": RAW_SCATTERING_NORMALIZATION_MODE,
            "n_ref_raw": float(ref_norm),
            "n_sca_raw": float(sca_norm),
            "gauge_mode_status": "v2_raw_angular_case_override",
            "v2_cross_raw_detector_integrated": float(cross_norm),
            "v2_self_roi_raw_detector": float(self_roi_raw_norm),
            "v2_reference_collapsed_raw_normalized_abs": float(abs(ref_collapsed_norm)),
        },
        "intrinsic": {
            "E_sca_unit_normalized_complex": complex(sca_collapsed_norm),
            "E_sca_unit_normalized": float(abs(sca_collapsed_norm)),
            "v2_collapsed_sca_raw_normalized_abs": float(abs(sca_collapsed_norm)),
            "v2_self_collapsed_detector": float(sca_self_collapsed),
            "v2_r_self": float(route_r_self),
            "raw_reference_normalization_mode": RAW_REFERENCE_NORMALIZATION_MODE,
            "raw_scattering_normalization_mode": RAW_SCATTERING_NORMALIZATION_MODE,
            "n_ref_raw": float(ref_norm),
            "n_sca_raw": float(sca_norm),
        },
    }


def _build_route_cfg(
    *,
    n_events: int,
    seed: int,
    detector_route_id: str,
    detector_forward_model: str,
    normalization_lane: str,
) -> tuple[Any, Any]:
    base_cfg, optical_template = build_frozen_b_cfg(n_events, seed)
    cfg = _cfg_for_normalization_lane(
        base_cfg,
        normalization_lane,
    )
    from dataclasses import replace

    cfg = replace(
        cfg,
        vectorized_event_engine="off",
        adaptive_event_budget_mode="fixed",
        pulse_detection_mode="absolute",
        detector_route_id=detector_route_id,
        detector_forward_model=detector_forward_model,
    )
    return cfg, optical_template


def _run_case_task(task: CaseTask) -> list[dict[str, Any]]:
    particle = particle_from_name(task.particle_name)
    medium = medium_for_particle(particle)
    channel = lane.case_baseline_channel(task.route.width_nm, task.route.depth_nm)
    _, optical_template = build_frozen_b_cfg(task.n_events, task.seed)
    optical = replace(optical_template, wavelength_m=float(task.route.wavelength_nm) * 1e-9)

    view_configs: dict[str, Any] = {}
    e_sca_refs: dict[str, float] = {}
    view_payload_overrides: dict[str, dict[str, dict[str, object]]] = {}
    for normalization_view in NORMALIZATION_VIEWS:
        cfg, optical_template_for_lane = _build_route_cfg(
            n_events=task.n_events,
            seed=task.seed,
            detector_route_id=task.detector_route_id,
            detector_forward_model=task.detector_forward_model,
            normalization_lane=normalization_view,
        )
        view_configs[normalization_view] = cfg
        if normalization_view == "fixed_660_gold":
            e_sca_refs[normalization_view] = _fixed_660_e_sca_ref(
                width_nm=task.route.width_nm,
                depth_nm=task.route.depth_nm,
                cfg=cfg,
                optical_template=optical_template_for_lane,
            )
        else:
            e_sca_refs[normalization_view] = _per_wavelength_e_sca_ref(
                width_nm=task.route.width_nm,
                depth_nm=task.route.depth_nm,
                wavelength_nm=task.route.wavelength_nm,
                medium=medium,
                cfg=cfg,
                optical_template=optical_template_for_lane,
            )
        if task.gauge_mode == "V2_raw_angular":
            view_payload_overrides[normalization_view] = _build_v2_view_payload_overrides(
                particle=particle,
                medium=medium,
                channel=channel,
                optical=optical,
                cfg=cfg,
                e_sca_ref=e_sca_refs[normalization_view],
            )

    outputs = run_single_case_batch_shared_event_normalization_views(
        particle,
        medium,
        channel,
        optical,
        view_configs,
        e_sca_refs,
        THETA_GRID_RAD,
        view_payload_overrides=(view_payload_overrides or None),
    )
    signed_d_outputs: dict[str, dict] | None = None
    if task.detector_route_id == "D_cross_only":
        signed_view_configs = {
            name: replace(
                cfg,
                readout_observable_mode="in_phase",
                pulse_detection_mode="positive",
            )
            for name, cfg in view_configs.items()
        }
        signed_d_outputs = run_single_case_batch_shared_event_normalization_views(
            particle,
            medium,
            channel,
            optical,
            signed_view_configs,
            e_sca_refs,
            THETA_GRID_RAD,
            view_payload_overrides=(view_payload_overrides or None),
        )

    rows: list[dict[str, Any]] = []
    for normalization_view, payload in outputs.items():
        cfg = view_configs[normalization_view]
        summary = payload["summary"]
        reference = payload["reference"]
        intrinsic = payload["intrinsic"]
        e_sca_complex = intrinsic["E_sca_unit_normalized_complex"]
        r_self = compute_r_self(reference, e_sca_complex)
        signed_summary = (
            signed_d_outputs[normalization_view]["summary"]
            if signed_d_outputs is not None
            else None
        )
        rows.append(
            {
                "particle_name": task.particle_name,
                "particle_material": particle.material_key or particle.name.split("_", 1)[0],
                "particle_family": "gold" if "gold" in task.particle_name else "EV_sEV",
                "particle_diameter_nm": float(particle.radius_m * 2.0e9),
                "wavelength_nm": task.route.wavelength_nm,
                "width_nm": task.route.width_nm,
                "depth_nm": task.route.depth_nm,
                "route_family_id": task.route.route_family_id,
                "route_family_note": task.route.route_family_note,
                "seed": task.seed,
                "detector_route_id": task.detector_route_id,
                "detector_forward_model": task.detector_forward_model,
                "readout_policy": READOUT_POLICY,
                "gauge_mode": task.gauge_mode,
                "noise_policy": NOISE_POLICY,
                "normalization_view": normalization_view,
                "prior_name": PRIOR_NAME,
                "r_self": float(r_self),
                "self_collapsed_detector": float(abs(complex(e_sca_complex)) ** 2),
                "self_roi_detector": float(reference["self_sca_detector_integrated"]),
                "detection_rate": float(summary["detection_rate"]),
                "stable_detection_rate": float(summary["stable_detection_rate"]),
                "detection_rate_wilson_lb": float(summary["detection_rate_wilson_lb"]),
                "stable_detection_rate_wilson_lb": float(summary["stable_detection_rate_wilson_lb"]),
                "mean_peak_margin_z": float(summary["mean_peak_margin_z"]),
                "selected_detector_mode_annulus_detection_rate": float(
                    summary["selected_detector_mode_annulus_detection_rate"]
                ),
                "selected_detector_mode_annulus_detection_rate_wilson_lb": float(
                    summary["selected_detector_mode_annulus_detection_rate_wilson_lb"]
                ),
                "selected_detector_mode_annulus_fraction": float(
                    summary["selected_detector_mode_annulus_fraction"]
                ),
                "selected_detector_mode_annulus_mean_edge_norm": float(
                    summary["selected_detector_mode_annulus_mean_edge_norm"]
                ),
                "selected_detector_mode_annulus_n_events": int(
                    summary["selected_detector_mode_annulus_n_events"]
                ),
                "selected_detector_mode_annulus_n_detected": int(
                    summary["selected_detector_mode_annulus_n_detected"]
                ),
                "absolute_cross_route_detection_rate": (
                    float(summary["detection_rate"])
                    if task.detector_route_id == "D_cross_only"
                    else float("nan")
                ),
                "absolute_cross_route_detection_rate_wilson_lb": (
                    float(summary["detection_rate_wilson_lb"])
                    if task.detector_route_id == "D_cross_only"
                    else float("nan")
                ),
                "signed_cross_route_detection_rate": (
                    float(signed_summary["detection_rate"])
                    if signed_summary is not None
                    else float("nan")
                ),
                "signed_cross_route_stable_detection_rate": (
                    float(signed_summary["stable_detection_rate"])
                    if signed_summary is not None
                    else float("nan")
                ),
                "signed_cross_route_detection_rate_wilson_lb": (
                    float(signed_summary["detection_rate_wilson_lb"])
                    if signed_summary is not None
                    else float("nan")
                ),
                "signed_cross_route_mean_peak_margin_z": (
                    float(signed_summary["mean_peak_margin_z"])
                    if signed_summary is not None
                    else float("nan")
                ),
                "reference_operating_band": str(summary.get("reference_operating_band")),
                "engineering_gate_passed": bool(summary.get("engineering_gate_passed")),
                "strict_ok": bool(
                    bool(summary.get("engineering_gate_passed"))
                    and not bool(summary.get("na_cutoff_active"))
                    and str(summary.get("rho_physical_envelope_status")) == "within_envelope"
                ),
                "all_crossing_detection_rate": float(summary["all_crossing_detection_rate"]),
                "final_engineering_score": float(summary["mean_peak_margin_z"]),
                "reference_model": str(reference.get("reference_model") or cfg.reference_model),
                "reference_route": str(reference.get("reference_route") or cfg.reference_route),
                "interference_overlap_mode": str(reference.get("interference_overlap_mode")),
                "interference_overlap_status": str(
                    summary.get("interference_overlap_status")
                    or reference.get("interference_overlap_status")
                    or "unavailable"
                ),
                "output_claim_level": str(
                    summary.get("output_claim_level_resolved")
                    or summary.get("output_claim_level")
                    or "unavailable"
                ),
                "detector_forward_claim_level": str(summary.get("detector_forward_claim_level")),
                "route_screening_claim_level": CLAIM_LEVEL,
                "route_screening_scope": _run_scope_statement(
                    (task.detector_route_id,),
                    (task.gauge_mode,),
                ),
                "route_screening_status": "stage1_minimal_screening",
                "route_noise_consistency_status": "common_noise_control",
                "vectorized_event_engine_used": str(summary.get("vectorized_event_engine_used")),
                "case_runtime_seconds": float(summary.get("case_runtime_seconds", float("nan"))),
                "raw_reference_normalization_mode": str(
                    reference.get("raw_reference_normalization_mode", "not_applicable_v1_gauge_locked")
                ),
                "raw_scattering_normalization_mode": str(
                    reference.get("raw_scattering_normalization_mode", "not_applicable_v1_gauge_locked")
                ),
                "n_ref_raw": float(reference.get("n_ref_raw", float("nan"))),
                "n_sca_raw": float(reference.get("n_sca_raw", float("nan"))),
            }
        )
    return rows


def _rank_routes_for_group(group: pd.DataFrame) -> pd.DataFrame:
    diameters = sorted(pd.to_numeric(group["particle_diameter_nm"], errors="coerce").dropna().astype(int).unique().tolist())
    priors = route_analysis.build_priors(diameters)
    routes = route_analysis.aggregate_routes(group, {PRIOR_NAME: priors[PRIOR_NAME]})
    family_lookup = (
        group[
            ["wavelength_nm", "width_nm", "depth_nm", "route_family_id", "route_family_note"]
        ]
        .drop_duplicates()
        .copy()
    )
    routes = routes.merge(
        family_lookup,
        on=["wavelength_nm", "width_nm", "depth_nm"],
        how="left",
    )
    selected_col = f"{PRIOR_NAME}_weighted_selected_annulus_detection"
    stable_col = f"{PRIOR_NAME}_weighted_stable"
    final_col = f"{PRIOR_NAME}_weighted_final"
    mask = routes["selected_annulus_lens_available"].astype(bool) & routes["reference_operating_band"].astype(str).eq(
        route_analysis.REFERENCE_USEFUL_BAND
    )
    if not bool(mask.any()):
        mask = routes["selected_annulus_lens_available"].astype(bool)
    ranked = routes.loc[mask].sort_values(
        [selected_col, stable_col, final_col],
        ascending=[False, False, False],
    ).copy()
    ranked["selected_annulus_rank"] = np.arange(1, len(ranked) + 1, dtype=int)
    return ranked


def _build_flip_summaries(
    case_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ev_df = case_df[case_df["particle_family"].astype(str).eq("EV_sEV")].copy()
    route_rank_rows: list[dict[str, Any]] = []
    top_rows: list[dict[str, Any]] = []
    for (
        detector_route_id,
        gauge_mode,
        normalization_view,
        raw_reference_normalization_mode,
        raw_scattering_normalization_mode,
        seed,
        wavelength_nm,
    ), group in ev_df.groupby(
        [
            "detector_route_id",
            "gauge_mode",
            "normalization_view",
            "raw_reference_normalization_mode",
            "raw_scattering_normalization_mode",
            "seed",
            "wavelength_nm",
        ],
        sort=True,
    ):
        ranked = _rank_routes_for_group(group)
        for row in ranked.to_dict("records"):
            row["detector_route_id"] = detector_route_id
            row["gauge_mode"] = gauge_mode
            row["normalization_view"] = normalization_view
            row["raw_reference_normalization_mode"] = raw_reference_normalization_mode
            row["raw_scattering_normalization_mode"] = raw_scattering_normalization_mode
            row["seed"] = seed
            row["wavelength_nm"] = int(wavelength_nm)
            top_rows.append(row if int(row["selected_annulus_rank"]) == 1 else None)
            route_rank_rows.append(row)
    route_rank_rows = [row for row in route_rank_rows if row is not None]
    top_route_rows = [row for row in top_rows if row is not None]
    route_rank_df = pd.DataFrame(route_rank_rows)
    top_route_df = pd.DataFrame(top_route_rows)
    if route_rank_df.empty:
        raise ValueError("no ranked EV routes were produced for Stage 1 screening")

    rank_join = route_rank_df[
        [
            "detector_route_id",
            "gauge_mode",
            "normalization_view",
            "raw_reference_normalization_mode",
            "raw_scattering_normalization_mode",
            "seed",
            "wavelength_nm",
            "width_nm",
            "depth_nm",
            "selected_annulus_rank",
            f"{PRIOR_NAME}_weighted_selected_annulus_detection",
            f"{PRIOR_NAME}_weighted_stable",
            f"{PRIOR_NAME}_weighted_final",
        ]
    ].copy()
    case_df = case_df.merge(
        rank_join,
        on=[
            "detector_route_id",
            "gauge_mode",
            "normalization_view",
            "raw_reference_normalization_mode",
            "raw_scattering_normalization_mode",
            "seed",
            "wavelength_nm",
            "width_nm",
            "depth_nm",
        ],
        how="left",
    )

    per_seed_rows: list[dict[str, Any]] = []
    for (detector_route_id, gauge_mode, seed), group in top_route_df.groupby(
        ["detector_route_id", "gauge_mode", "seed"],
        sort=True,
    ):
        winners = {
            (row["normalization_view"], int(row["wavelength_nm"])): row
            for row in group.to_dict("records")
        }
        required = {
            ("fixed_660_gold", 404),
            ("fixed_660_gold", 660),
            ("per_wavelength_gold", 404),
            ("per_wavelength_gold", 660),
        }
        if set(winners) != required:
            continue
        fixed_404 = winners[("fixed_660_gold", 404)]
        fixed_660 = winners[("fixed_660_gold", 660)]
        per_404 = winners[("per_wavelength_gold", 404)]
        per_660 = winners[("per_wavelength_gold", 660)]
        fixed_winner = (
            fixed_404
            if fixed_404[f"{PRIOR_NAME}_weighted_selected_annulus_detection"]
            >= fixed_660[f"{PRIOR_NAME}_weighted_selected_annulus_detection"]
            else fixed_660
        )
        per_winner = (
            per_404
            if per_404[f"{PRIOR_NAME}_weighted_selected_annulus_detection"]
            >= per_660[f"{PRIOR_NAME}_weighted_selected_annulus_detection"]
            else per_660
        )
        per_seed_rows.append(
            {
                "detector_route_id": detector_route_id,
                "gauge_mode": gauge_mode,
                "seed": int(seed),
                "fixed_660_gold_selected_family_id_404": fixed_404["route_family_id"],
                "fixed_660_gold_selected_route_404": f"{int(fixed_404['wavelength_nm'])}/{int(fixed_404['width_nm'])}x{int(fixed_404['depth_nm'])}",
                "fixed_660_gold_selected_family_id_660": fixed_660["route_family_id"],
                "fixed_660_gold_selected_route_660": f"{int(fixed_660['wavelength_nm'])}/{int(fixed_660['width_nm'])}x{int(fixed_660['depth_nm'])}",
                "fixed_660_gold_winner_wavelength": int(fixed_winner["wavelength_nm"]),
                "fixed_660_gold_winner_family_id": fixed_winner["route_family_id"],
                "fixed_660_gold_winner_route": f"{int(fixed_winner['wavelength_nm'])}/{int(fixed_winner['width_nm'])}x{int(fixed_winner['depth_nm'])}",
                "per_wavelength_gold_selected_family_id_404": per_404["route_family_id"],
                "per_wavelength_gold_selected_route_404": f"{int(per_404['wavelength_nm'])}/{int(per_404['width_nm'])}x{int(per_404['depth_nm'])}",
                "per_wavelength_gold_selected_family_id_660": per_660["route_family_id"],
                "per_wavelength_gold_selected_route_660": f"{int(per_660['wavelength_nm'])}/{int(per_660['width_nm'])}x{int(per_660['depth_nm'])}",
                "per_wavelength_gold_winner_wavelength": int(per_winner["wavelength_nm"]),
                "per_wavelength_gold_winner_family_id": per_winner["route_family_id"],
                "per_wavelength_gold_winner_route": f"{int(per_winner['wavelength_nm'])}/{int(per_winner['width_nm'])}x{int(per_winner['depth_nm'])}",
                "detector_route_flip_flag_404_660": _detector_route_flip_flag_404_660(
                    int(fixed_winner["wavelength_nm"]),
                    int(per_winner["wavelength_nm"]),
                ),
            }
        )
    per_seed_df = pd.DataFrame(per_seed_rows)

    cross_model_rows: list[dict[str, Any]] = []
    for (gauge_mode, normalization_view, seed), group in top_route_df.groupby(
        ["gauge_mode", "normalization_view", "seed"],
        sort=True,
    ):
        winners = {
            (row["detector_route_id"], int(row["wavelength_nm"])): row
            for row in group.to_dict("records")
        }
        required = {
            ("A_hybrid", 404),
            ("A_hybrid", 660),
            ("B_roi_intensity", 404),
            ("B_roi_intensity", 660),
        }
        if set(winners) != required:
            continue
        a_404 = winners[("A_hybrid", 404)]
        a_660 = winners[("A_hybrid", 660)]
        b_404 = winners[("B_roi_intensity", 404)]
        b_660 = winners[("B_roi_intensity", 660)]
        a_winner = (
            a_404
            if a_404[f"{PRIOR_NAME}_weighted_selected_annulus_detection"]
            >= a_660[f"{PRIOR_NAME}_weighted_selected_annulus_detection"]
            else a_660
        )
        b_winner = (
            b_404
            if b_404[f"{PRIOR_NAME}_weighted_selected_annulus_detection"]
            >= b_660[f"{PRIOR_NAME}_weighted_selected_annulus_detection"]
            else b_660
        )
        changed = (
            a_404["route_family_id"] != b_404["route_family_id"]
            or a_660["route_family_id"] != b_660["route_family_id"]
            or a_winner["route_family_id"] != b_winner["route_family_id"]
            or int(a_winner["wavelength_nm"]) != int(b_winner["wavelength_nm"])
        )
        cross_model_rows.append(
            {
                "gauge_mode": gauge_mode,
                "normalization_view": normalization_view,
                "seed": int(seed),
                "A_hybrid_selected_family_id_404": a_404["route_family_id"],
                "A_hybrid_selected_route_404": f"{int(a_404['wavelength_nm'])}/{int(a_404['width_nm'])}x{int(a_404['depth_nm'])}",
                "A_hybrid_selected_family_id_660": a_660["route_family_id"],
                "A_hybrid_selected_route_660": f"{int(a_660['wavelength_nm'])}/{int(a_660['width_nm'])}x{int(a_660['depth_nm'])}",
                "A_hybrid_winner_wavelength": int(a_winner["wavelength_nm"]),
                "A_hybrid_winner_family_id": a_winner["route_family_id"],
                "A_hybrid_winner_route": f"{int(a_winner['wavelength_nm'])}/{int(a_winner['width_nm'])}x{int(a_winner['depth_nm'])}",
                "B_roi_intensity_selected_family_id_404": b_404["route_family_id"],
                "B_roi_intensity_selected_route_404": f"{int(b_404['wavelength_nm'])}/{int(b_404['width_nm'])}x{int(b_404['depth_nm'])}",
                "B_roi_intensity_selected_family_id_660": b_660["route_family_id"],
                "B_roi_intensity_selected_route_660": f"{int(b_660['wavelength_nm'])}/{int(b_660['width_nm'])}x{int(b_660['depth_nm'])}",
                "B_roi_intensity_winner_wavelength": int(b_winner["wavelength_nm"]),
                "B_roi_intensity_winner_family_id": b_winner["route_family_id"],
                "B_roi_intensity_winner_route": f"{int(b_winner['wavelength_nm'])}/{int(b_winner['width_nm'])}x{int(b_winner['depth_nm'])}",
                "detector_route_rank_stability_class": (
                    "model_sensitive_family_change" if changed else "model_stable_same_family"
                ),
                "model_change_flag": changed,
            }
        )
    cross_model_df = pd.DataFrame(cross_model_rows)

    gauge_rows: list[dict[str, Any]] = []
    for (detector_route_id, normalization_view, seed), group in top_route_df.groupby(
        ["detector_route_id", "normalization_view", "seed"],
        sort=True,
    ):
        winners = {
            (row["gauge_mode"], int(row["wavelength_nm"])): row
            for row in group.to_dict("records")
        }
        required = {
            ("V1_gauge_locked", 404),
            ("V1_gauge_locked", 660),
            ("V2_raw_angular", 404),
            ("V2_raw_angular", 660),
        }
        if set(winners) != required:
            continue
        v1_404 = winners[("V1_gauge_locked", 404)]
        v1_660 = winners[("V1_gauge_locked", 660)]
        v2_404 = winners[("V2_raw_angular", 404)]
        v2_660 = winners[("V2_raw_angular", 660)]
        v1_winner = (
            v1_404
            if v1_404[f"{PRIOR_NAME}_weighted_selected_annulus_detection"]
            >= v1_660[f"{PRIOR_NAME}_weighted_selected_annulus_detection"]
            else v1_660
        )
        v2_winner = (
            v2_404
            if v2_404[f"{PRIOR_NAME}_weighted_selected_annulus_detection"]
            >= v2_660[f"{PRIOR_NAME}_weighted_selected_annulus_detection"]
            else v2_660
        )
        changed = (
            v1_404["route_family_id"] != v2_404["route_family_id"]
            or v1_660["route_family_id"] != v2_660["route_family_id"]
            or v1_winner["route_family_id"] != v2_winner["route_family_id"]
            or int(v1_winner["wavelength_nm"]) != int(v2_winner["wavelength_nm"])
        )
        gauge_rows.append(
            {
                "detector_route_id": detector_route_id,
                "normalization_view": normalization_view,
                "seed": int(seed),
                "V1_selected_family_id_404": v1_404["route_family_id"],
                "V1_selected_route_404": f"{int(v1_404['wavelength_nm'])}/{int(v1_404['width_nm'])}x{int(v1_404['depth_nm'])}",
                "V1_selected_family_id_660": v1_660["route_family_id"],
                "V1_selected_route_660": f"{int(v1_660['wavelength_nm'])}/{int(v1_660['width_nm'])}x{int(v1_660['depth_nm'])}",
                "V1_winner_wavelength": int(v1_winner["wavelength_nm"]),
                "V1_winner_family_id": v1_winner["route_family_id"],
                "V1_winner_route": f"{int(v1_winner['wavelength_nm'])}/{int(v1_winner['width_nm'])}x{int(v1_winner['depth_nm'])}",
                "V2_selected_family_id_404": v2_404["route_family_id"],
                "V2_selected_route_404": f"{int(v2_404['wavelength_nm'])}/{int(v2_404['width_nm'])}x{int(v2_404['depth_nm'])}",
                "V2_selected_family_id_660": v2_660["route_family_id"],
                "V2_selected_route_660": f"{int(v2_660['wavelength_nm'])}/{int(v2_660['width_nm'])}x{int(v2_660['depth_nm'])}",
                "V2_winner_wavelength": int(v2_winner["wavelength_nm"]),
                "V2_winner_family_id": v2_winner["route_family_id"],
                "V2_winner_route": f"{int(v2_winner['wavelength_nm'])}/{int(v2_winner['width_nm'])}x{int(v2_winner['depth_nm'])}",
                "gauge_route_flip_flag_404_660": changed,
                "gauge_rank_stability_class": (
                    "gauge_sensitive_family_change" if changed else "gauge_stable_same_family"
                ),
            }
        )
    gauge_df = pd.DataFrame(gauge_rows)
    return case_df, per_seed_df, cross_model_df, gauge_df


def _consensus_rows(
    per_seed_df: pd.DataFrame,
    cross_model_df: pd.DataFrame,
    gauge_df: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    if not per_seed_df.empty:
        for (detector_route_id, gauge_mode), group in per_seed_df.groupby(
            ["detector_route_id", "gauge_mode"],
            sort=True,
        ):
            fixed_counts = group["fixed_660_gold_winner_family_id"].value_counts().to_dict()
            per_counts = group["per_wavelength_gold_winner_family_id"].value_counts().to_dict()
            flip_true_seed_count = int(group["detector_route_flip_flag_404_660"].astype(bool).sum())
            flip_false_seed_count = int(len(group) - flip_true_seed_count)
            if flip_true_seed_count == len(group):
                flip_consensus_status = "unanimous_true"
            elif flip_false_seed_count == len(group):
                flip_consensus_status = "unanimous_false"
            else:
                flip_consensus_status = "mixed"
            rows.append(
                {
                    "summary_kind": "view_flip_consensus",
                    "group_key": f"{detector_route_id}|{gauge_mode}",
                    "fixed_660_gold_winner_family_mode": max(fixed_counts, key=fixed_counts.get),
                    "per_wavelength_gold_winner_family_mode": max(per_counts, key=per_counts.get),
                    "detector_route_flip_flag_404_660_consensus": bool(group["detector_route_flip_flag_404_660"].all()),
                    "flip_true_seed_count": flip_true_seed_count,
                    "flip_false_seed_count": flip_false_seed_count,
                    "flip_consensus_status": flip_consensus_status,
                    "seed_count": int(len(group)),
                }
            )
    if not cross_model_df.empty:
        for (gauge_mode, normalization_view), group in cross_model_df.groupby(
            ["gauge_mode", "normalization_view"],
            sort=True,
        ):
            stability_counts = group["detector_route_rank_stability_class"].value_counts().to_dict()
            rows.append(
                {
                    "summary_kind": "cross_model_consensus",
                    "group_key": f"{gauge_mode}|{normalization_view}",
                    "stability_class_mode": max(stability_counts, key=stability_counts.get),
                    "model_change_any_seed": bool(group["model_change_flag"].any()),
                    "seed_count": int(len(group)),
                }
            )
    if not gauge_df.empty:
        for (detector_route_id, normalization_view), group in gauge_df.groupby(
            ["detector_route_id", "normalization_view"],
            sort=True,
        ):
            stability_counts = group["gauge_rank_stability_class"].value_counts().to_dict()
            rows.append(
                {
                    "summary_kind": "gauge_consensus",
                    "group_key": f"{detector_route_id}|{normalization_view}",
                    "stability_class_mode": max(stability_counts, key=stability_counts.get),
                    "model_change_any_seed": bool(group["gauge_route_flip_flag_404_660"].any()),
                    "seed_count": int(len(group)),
                }
            )
    return pd.DataFrame(rows)


def _gold_anchor_diagnostic(case_df: pd.DataFrame) -> pd.DataFrame:
    gold = case_df[
        case_df["particle_family"].astype(str).eq("gold")
        & case_df["detector_route_id"].astype(str).eq("D_cross_only")
    ].copy()
    if gold.empty:
        return pd.DataFrame()
    columns = [
        "detector_route_id",
        "gauge_mode",
        "normalization_view",
        "seed",
        "particle_name",
        "particle_diameter_nm",
        "wavelength_nm",
        "width_nm",
        "depth_nm",
        "detection_rate",
        "stable_detection_rate",
        "detection_rate_wilson_lb",
        "stable_detection_rate_wilson_lb",
        "mean_peak_margin_z",
        "absolute_cross_route_detection_rate",
        "absolute_cross_route_detection_rate_wilson_lb",
        "signed_cross_route_detection_rate",
        "signed_cross_route_stable_detection_rate",
        "signed_cross_route_detection_rate_wilson_lb",
        "signed_cross_route_mean_peak_margin_z",
    ]
    return gold[columns].sort_values(
        ["gauge_mode", "normalization_view", "seed", "wavelength_nm", "particle_diameter_nm"]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run report 148 Stage 1 minimal route screening with shared dual normalization views."
    )
    parser.add_argument("--source-summary", type=Path, default=SOURCE_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=Path("results/audits") / f"report148_stage1_ab_minimal_{datetime.now().strftime('%Y%m%d')}")  # noqa: E501
    parser.add_argument("--n-events", type=int, default=2000)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument(
        "--detector-route-ids",
        default="A_hybrid,B_roi_intensity",
        help="Comma-separated detector route ids to run.",
    )
    parser.add_argument(
        "--gauge-modes",
        default="V1_gauge_locked,V2_raw_angular",
        help="Comma-separated gauge modes to run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    source = _load_source(args.source_summary)
    scope = build_scope(source)
    detector_route_ids = tuple(
        item.strip() for item in str(args.detector_route_ids).split(",") if item.strip()
    )
    gauge_modes = tuple(
        item.strip() for item in str(args.gauge_modes).split(",") if item.strip()
    )
    unknown_routes = [item for item in detector_route_ids if item not in ROUTE_MODEL_CATALOG]
    if unknown_routes:
        raise ValueError(f"unknown detector route ids: {unknown_routes}")
    unknown_gauges = [item for item in gauge_modes if item not in GAUGE_MODES]
    if unknown_gauges:
        raise ValueError(f"unknown gauge modes: {unknown_gauges}")
    tasks = [
        CaseTask(
            route=route,
            particle_name=particle_name,
            seed=seed,
            detector_route_id=detector_route_id,
            detector_forward_model=ROUTE_MODEL_CATALOG[detector_route_id],
            gauge_mode=gauge_mode,
            n_events=int(args.n_events),
        )
        for detector_route_id in detector_route_ids
        for gauge_mode in gauge_modes
        for seed in SEEDS
        for route in scope["routes"]
        for particle_name in scope["particle_names"]
    ]

    rows: list[dict[str, Any]] = []
    if int(args.workers) > 1:
        with ProcessPoolExecutor(max_workers=int(args.workers)) as executor:
            for batch_rows in executor.map(_run_case_task, tasks):
                rows.extend(batch_rows)
    else:
        for task in tasks:
            rows.extend(_run_case_task(task))

    case_df = pd.DataFrame(rows)
    run_scope_statement = _run_scope_statement(detector_route_ids, gauge_modes)
    case_df["stage1_run_scope"] = run_scope_statement
    case_df, per_seed_df, cross_model_df, gauge_df = _build_flip_summaries(case_df)
    consensus_df = _consensus_rows(per_seed_df, cross_model_df, gauge_df)
    gold_anchor_df = _gold_anchor_diagnostic(case_df)
    seed_coverage_df = _seed_coverage_rows(case_df)

    case_df.sort_values(
        [
            "detector_route_id",
            "gauge_mode",
            "normalization_view",
            "raw_reference_normalization_mode",
            "raw_scattering_normalization_mode",
            "seed",
            "wavelength_nm",
            "width_nm",
            "depth_nm",
            "particle_material",
            "particle_diameter_nm",
        ]
    ).to_csv(output_dir / "report148_stage1_case_rows.csv", index=False)
    per_seed_df.to_csv(output_dir / "report148_stage1_view_flip_by_seed.csv", index=False)
    if not cross_model_df.empty:
        cross_model_df.to_csv(output_dir / "report148_stage1_model_sensitivity_by_seed.csv", index=False)
    if not gauge_df.empty:
        gauge_df.to_csv(output_dir / "report148_stage1_gauge_sensitivity_by_seed.csv", index=False)
    consensus_df.to_csv(output_dir / "report148_stage1_consensus_summary.csv", index=False)
    if not gold_anchor_df.empty:
        gold_anchor_df.to_csv(output_dir / "report148_stage1_gold_anchor_diagnostic.csv", index=False)
    seed_coverage_df.to_csv(output_dir / "report148_stage1_seed_coverage.csv", index=False)

    event_accounting = _event_accounting(
        case_row_count=len(case_df),
        n_events=int(args.n_events),
        normalization_view_count=len(NORMALIZATION_VIEWS),
    )
    manifest = {
        "generated_at": _utc_now_iso(),
        "source_summary": str(args.source_summary),
        "source_summary_sha256": _sha256_file(args.source_summary),
        "output_dir": str(output_dir),
        "n_events": int(args.n_events),
        "workers": int(args.workers),
        "readout_policies": [READOUT_POLICY],
        "gauge_modes": list(gauge_modes),
        "route_scope": list(detector_route_ids),
        "run_scope_statement": run_scope_statement,
        "detector_route_models": [
            {
                "detector_route_id": route_id,
                "detector_forward_model": ROUTE_MODEL_CATALOG[route_id],
            }
            for route_id in detector_route_ids
        ],
        "normalization_views": list(NORMALIZATION_VIEWS),
        "seeds": list(SEEDS),
        "routes": [asdict(route) for route in scope["routes"]],
        "ev_particle_names": list(scope["ev_particle_names"]),
        "gold_anchor_names": list(scope["gold_anchor_names"]),
        "ev_subset_selection_status": scope["ev_subset_selection_status"],
        "claim_level": CLAIM_LEVEL,
        "status": "stage1_minimal_subset_complete_for_declared_run_scope",
        "seed_coverage_complete": bool(
            seed_coverage_df["seed_coverage_status"].astype(str).eq("complete").all()
        ),
        "seed_coverage_file": "report148_stage1_seed_coverage.csv",
        **event_accounting,
        "artifact_files": {
            "case_rows": "report148_stage1_case_rows.csv",
            "view_flip_by_seed": "report148_stage1_view_flip_by_seed.csv",
            "model_sensitivity_by_seed": (
                "report148_stage1_model_sensitivity_by_seed.csv"
                if not cross_model_df.empty
                else None
            ),
            "gauge_sensitivity_by_seed": (
                "report148_stage1_gauge_sensitivity_by_seed.csv"
                if not gauge_df.empty
                else None
            ),
            "consensus_summary": "report148_stage1_consensus_summary.csv",
            "gold_anchor_diagnostic": (
                "report148_stage1_gold_anchor_diagnostic.csv"
                if not gold_anchor_df.empty
                else None
            ),
            "seed_coverage": "report148_stage1_seed_coverage.csv",
        },
        "repro_command": (
            ".venv/bin/python tools/audits/run_report148_stage1_ab_minimal.py "
            f"--source-summary {args.source_summary} --output-dir {output_dir} "
            f"--n-events {int(args.n_events)} --workers {int(args.workers)} "
            f"--detector-route-ids {','.join(detector_route_ids)} "
            f"--gauge-modes {','.join(gauge_modes)}"
        ),
    }
    write_json_file(output_dir / "report148_stage1_manifest.json", manifest)


if __name__ == "__main__":
    main()
