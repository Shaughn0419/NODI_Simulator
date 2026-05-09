#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
for candidate in (str(PROJECT_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from nodi_simulator import BASELINE_PARTICLE, PBS_1X, WATER, run_parameter_sweep
from nodi_simulator.dashboard.config import (
    DEFAULT_SIM_CFG,
    OPTICAL_TEMPLATE,
    THETA_GRID_RAD,
    build_biomimetic_exosome_ensemble_family,
    infer_biomimetic_exosome_preset_name,
    infer_particle_diameter_nm,
    make_particle,
    medium_for_particle,
)
from nodi_simulator.data_objects import (
    Channel,
    Particle,
    READOUT_PRESET_CONFIG_OVERRIDES,
    SimulationConfig,
    make_ev_nodi_design_sweep_config,
)
from nodi_simulator.paper_aligned_profiles import (
    PAPER_ALIGNED_PROFILES,
    apply_paper_aligned_profile,
)
from nodi_simulator.parameter_sweep import wilson_upper_bound
from tools._common import write_json_file
from nodi_simulator.pulse_analysis import (
    build_pulse_extraction_context,
    estimate_threshold_stats_robust,
    extract_pulse_features,
)
from nodi_simulator.type_coerce import finite_float as _as_float

OUTPUT_DIR = PROJECT_ROOT / "results" / "tsuyama_gold_aligned_detection_lane"
REPORT_INPUT_DIR = PROJECT_ROOT / "reports" / "current" / "47_ev_design_full_grid_analysis"
FULL_SUMMARY_PATH = (
    PROJECT_ROOT
    / "results"
    / "ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv"
)

CANDIDATE_CASE_TRIPLES: tuple[tuple[int, int, int], ...] = (
    (404, 600, 1300),
    (404, 800, 700),
    (488, 600, 1500),
    (488, 800, 700),
    (532, 600, 1500),
    (532, 800, 700),
    (660, 800, 1400),
    (660, 800, 1500),
    (660, 900, 1400),
    (660, 900, 1500),
)
WEAK_REFERENCE_CONTROL: tuple[int, int, int] = (660, 700, 1500)
TSUYAMA_2022_NODI_PAPER_GEOMETRY: tuple[tuple[int, int, int], ...] = (
    (488, 800, 550),
    (488, 1200, 550),
    (532, 800, 550),
    (532, 1200, 550),
    (660, 800, 550),
    (660, 1200, 550),
)
TSUYAMA_2020_POD_GEOMETRY_BRIDGE: tuple[tuple[int, int, int], ...] = (
    (488, 800, 710),
    (532, 800, 710),
    (660, 800, 710),
)
PRIMARY_TSUYAMA_LIKE_CASES = {
    (488, 800, 550),
    (532, 800, 550),
    (488, 800, 700),
    (532, 800, 700),
}
GOLD_DIAMETERS_NM = (20, 30, 40, 60)
EV_DIAMETERS_NM = (70, 100, 120, 150)
EV_WEIGHT_PROFILE_IDS = (
    "equal_current",
    "sEV_small_70nm_gsd1p45",
    "sEV_mid_100nm_gsd1p5",
    "large_tail_150nm_gsd1p6",
)
TSUYAMA_2022_TABLE_S1_NK: dict[str, dict[int, tuple[float, float]]] = {
    "gold": {
        488: (1.04, 1.833),
        532: (0.62, 2.081),
        660: (0.14, 3.697),
    },
    "silver": {
        488: (0.05, 3.093),
        532: (0.05, 3.324),
        660: (0.05, 4.483),
    },
}
TSUYAMA_2022_TABLE_S1_INTERFEROMETRIC_SCATTERING: dict[str, dict[int, float]] = {
    "gold": {488: 0.45, 532: 0.68, 660: 0.32},
    "silver": {488: 1.90, 532: 0.89, 660: 0.85},
}
GOLD_OUTPUT_COLUMNS = (
    "scenario_config_id",
    "scenario_kind",
    "claim_level",
    "particle_name",
    "particle_material",
    "particle_diameter_nm",
    "wavelength_nm",
    "width_nm",
    "depth_nm",
    "n_events",
    "n_detected",
    "random_seed",
    "readout_profile",
    "readout_preset",
    "threshold_sigma",
    "threshold_tail",
    "threshold_calibration_source",
    "min_peak_width_s",
    "min_peak_interval_s",
    "pulse_width_measure_mode",
    "pulse_duration_estimation_policy",
    "pulse_extraction_sampling_interval_s",
    "flow_profile_model",
    "initial_position_distribution_mode",
    "initial_position_flux_weighted_mixture_fraction",
    "colored_noise_false_alarm_model",
    "post_readout_colored_noise_std",
    "post_readout_colored_noise_tau_s",
    "lockin_time_constant_s",
    "nodi_lockin_frequency_Hz",
    "pulse_detection_mode",
    "detection_decision_mode",
    "readout_observable_mode",
    "detection_rate",
    "detection_rate_wilson_lb",
    "all_crossing_detection_rate",
    "all_crossing_detection_rate_wilson_lb",
    "selected_detector_mode_candidate_n_events",
    "selected_detector_mode_candidate_fraction",
    "selected_detector_mode_candidate_detection_rate",
    "selected_detector_mode_candidate_detection_rate_wilson_lb",
    "selected_detector_mode_annulus_edge_norm_min",
    "selected_detector_mode_annulus_edge_norm_max",
    "selected_detector_mode_annulus_n_events",
    "selected_detector_mode_annulus_fraction",
    "selected_detector_mode_annulus_detection_rate",
    "selected_detector_mode_annulus_detection_rate_wilson_lb",
    "stable_detection_rate",
    "stable_detection_rate_wilson_lb",
    "single_channel_detection_rate",
    "paired_channel_detection_rate",
    "mean_peak_height",
    "mean_peak_width_s",
    "mean_peak_margin_z",
    "mean_local_snr",
    "mean_transit_time_ms",
    "mean_nodi_transit_bandwidth_gain",
    "phase_flip_fraction",
    "reference_operating_band",
    "na_cutoff_active",
    "rho_physical_envelope_status",
    "engineering_gate_passed",
    "engineering_gate_primary_blocker",
    "gold_anchor_component_status",
    "gold_anchor_pass",
    "gold_anchor_primary_blocker",
    "config_hash",
)

SCENARIO_ORDER = (
    "nodi_2022_10sigma_single",
    "nodi_2022_5sigma_single_sensitivity",
    "ev_nodi_5sigma_single_current_design",
    "paired_2024_5sigma_diag",
    "paired_2024_10sigma_diag",
)
SCENARIO_KIND = {
    "nodi_2022_10sigma_single": "nodi_single",
    "nodi_2022_5sigma_single_sensitivity": "nodi_single",
    "ev_nodi_5sigma_single_current_design": "nodi_single",
    "paired_2024_5sigma_diag": "paired_diag",
    "paired_2024_10sigma_diag": "paired_diag",
}
SCENARIO_ROLE = {
    "nodi_2022_10sigma_single": "primary gold anchor",
    "nodi_2022_5sigma_single_sensitivity": "sensitivity; needs blank pass",
    "ev_nodi_5sigma_single_current_design": "EV/NODI current-design bridge",
    "paired_2024_5sigma_diag": "paired diagnostic",
    "paired_2024_10sigma_diag": "paired diagnostic",
}


def ensure_output_dir(path: Path = OUTPUT_DIR) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def all_case_triples() -> list[tuple[int, int, int]]:
    cases = [
        *CANDIDATE_CASE_TRIPLES,
        WEAK_REFERENCE_CONTROL,
        *TSUYAMA_2022_NODI_PAPER_GEOMETRY,
        *TSUYAMA_2020_POD_GEOMETRY_BRIDGE,
    ]
    seen: set[tuple[int, int, int]] = set()
    out: list[tuple[int, int, int]] = []
    for case in cases:
        if case not in seen:
            out.append(case)
            seen.add(case)
    return out


def case_role(case: tuple[int, int, int]) -> str:
    if case == WEAK_REFERENCE_CONTROL:
        return "weak_reference_control"
    if case in TSUYAMA_2022_NODI_PAPER_GEOMETRY:
        return "tsuyama_2022_nodi_paper_geometry"
    if case in TSUYAMA_2020_POD_GEOMETRY_BRIDGE:
        return "tsuyama_2020_pod_geometry_bridge"
    if case in PRIMARY_TSUYAMA_LIKE_CASES:
        return "tsuyama_like_candidate"
    return "candidate"


def make_tsuyama_2022_table_s1_particle(
    material_key: str,
    diameter_nm: int,
    wavelength_nm: int,
) -> Particle:
    """Build a fixed-index particle using Tsuyama 2022 Supplementary Table S1."""
    material = str(material_key).lower()
    wavelength = int(wavelength_nm)
    if material not in TSUYAMA_2022_TABLE_S1_NK:
        raise ValueError(f"Unsupported Tsuyama 2022 Table S1 material: {material_key}")
    if wavelength not in TSUYAMA_2022_TABLE_S1_NK[material]:
        raise ValueError(f"Unsupported Tsuyama 2022 Table S1 wavelength: {wavelength_nm}")
    n_real, n_imag = TSUYAMA_2022_TABLE_S1_NK[material][wavelength]
    return Particle(
        name=f"{material}_{int(diameter_nm)}nm_tsuyama2022s1_{wavelength}nm",
        radius_m=float(diameter_nm) * 1e-9 / 2.0,
        n_real=float(n_real),
        n_imag=float(n_imag),
        material_key=material,
        use_material_model=False,
    )


def build_base_cfg() -> SimulationConfig:
    return make_ev_nodi_design_sweep_config(deepcopy(DEFAULT_SIM_CFG))


def build_scenario_cfg(scenario_config_id: str, *, n_events: int | None = None) -> SimulationConfig:
    cfg = build_base_cfg()
    if scenario_config_id == "nodi_2022_10sigma_single":
        cfg = apply_paper_aligned_profile(cfg, "nodi_2022")
    elif scenario_config_id == "nodi_2022_5sigma_single_sensitivity":
        cfg = apply_paper_aligned_profile(cfg, "nodi_2022")
        cfg = replace(
            cfg,
            threshold_sigma=5.0,
            engineering_min_detected_fraction=0.05,
            engineering_min_stable_detection_rate=0.05,
        )
    elif scenario_config_id == "ev_nodi_5sigma_single_current_design":
        cfg = make_ev_nodi_design_sweep_config(deepcopy(DEFAULT_SIM_CFG))
        cfg = replace(
            cfg,
            engineering_min_detected_fraction=0.05,
            engineering_min_stable_detection_rate=0.05,
        )
    elif scenario_config_id == "paired_2024_5sigma_diag":
        cfg = apply_paper_aligned_profile(cfg, "paired_2024")
    elif scenario_config_id == "paired_2024_10sigma_diag":
        cfg = apply_paper_aligned_profile(cfg, "paired_2024_10sigma")
    else:
        raise ValueError(f"Unknown scenario_config_id: {scenario_config_id}")

    if SCENARIO_KIND[scenario_config_id] == "nodi_single":
        cfg = replace(
            cfg,
            readout_observable_mode="magnitude",
            pulse_detection_mode="positive",
            threshold_tail="one_sided",
            min_peak_width_s=2.5e-3,
            min_peak_interval_s=0.1,
            engineering_max_phase_flip_fraction=1.0,
            detection_decision_mode="single_channel",
            engineering_decision_basis="single_channel",
        )
    cfg = replace(
        cfg,
        score_mode="single",
        adaptive_event_budget_mode="fixed",
        pulse_width_measure_mode="duration_above_threshold",
    )
    if n_events is not None:
        cfg = replace(cfg, n_events=int(n_events))
    return cfg


def config_hash(cfg: SimulationConfig) -> str:
    fields = {
        "readout_preset": cfg.readout_preset,
        "threshold_sigma": cfg.threshold_sigma,
        "threshold_tail": cfg.threshold_tail,
        "threshold_calibration_source": cfg.threshold_calibration_source,
        "min_peak_width_s": cfg.min_peak_width_s,
        "min_peak_interval_s": cfg.min_peak_interval_s,
        "pulse_width_measure_mode": cfg.pulse_width_measure_mode,
        "pulse_duration_estimation_policy": cfg.pulse_duration_estimation_policy,
        "pulse_extraction_sampling_interval_s": cfg.pulse_extraction_sampling_interval_s,
        "readout_observable_mode": cfg.readout_observable_mode,
        "pulse_detection_mode": cfg.pulse_detection_mode,
        "detection_decision_mode": cfg.detection_decision_mode,
        "engineering_decision_basis": cfg.engineering_decision_basis,
        "engineering_min_detected_fraction": cfg.engineering_min_detected_fraction,
        "engineering_min_stable_detection_rate": cfg.engineering_min_stable_detection_rate,
        "engineering_max_phase_flip_fraction": cfg.engineering_max_phase_flip_fraction,
        "lockin_time_constant_s": cfg.lockin_time_constant_s,
        "nodi_lockin_frequency_Hz": cfg.nodi_lockin_frequency_Hz,
        "reference_model": cfg.reference_model,
        "reference_route": cfg.reference_route,
        "illumination_mode": cfg.illumination_mode,
        "flow_profile_model": cfg.flow_profile_model,
        "initial_position_distribution_mode": cfg.initial_position_distribution_mode,
        "initial_position_flux_weighted_mixture_fraction": (
            cfg.initial_position_flux_weighted_mixture_fraction
        ),
        "colored_noise_false_alarm_model": cfg.colored_noise_false_alarm_model,
        "post_readout_colored_noise_std": cfg.post_readout_colored_noise_std,
        "post_readout_colored_noise_tau_s": cfg.post_readout_colored_noise_tau_s,
    }
    payload = json.dumps(fields, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def scenario_manifest_records() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for scenario_id in SCENARIO_ORDER:
        cfg = build_scenario_cfg(scenario_id)
        for wavelength_nm, width_nm, depth_nm in all_case_triples():
            records.append(
                {
                    "scenario_config_id": scenario_id,
                    "scenario_kind": SCENARIO_KIND[scenario_id],
                    "role": SCENARIO_ROLE[scenario_id],
                    "case_triple": [wavelength_nm, width_nm, depth_nm],
                    "case_role": case_role((wavelength_nm, width_nm, depth_nm)),
                    "particle_sets": ["gold_ladder", "ev_panel"],
                    "gold_smoke_events": 1000,
                    "gold_final_events": 10000,
                    "config_hash": config_hash(cfg),
                    "readout_preset": cfg.readout_preset,
                    "threshold_sigma": float(cfg.threshold_sigma),
                    "threshold_tail": cfg.threshold_tail,
                    "min_peak_width_s": float(cfg.min_peak_width_s),
                    "min_peak_interval_s": float(cfg.min_peak_interval_s),
                    "pulse_width_measure_mode": cfg.pulse_width_measure_mode,
                    "readout_observable_mode": cfg.readout_observable_mode,
                    "pulse_detection_mode": cfg.pulse_detection_mode,
                    "detection_decision_mode": cfg.detection_decision_mode,
                }
            )
    return records


def write_json(path: Path, payload: Any) -> None:
    write_json_file(path, payload, sort_keys=False, allow_nan=True)


def case_baseline_channel(width_nm: int, depth_nm: int) -> Channel:
    """Build the geometry-aware baseline channel for one explicit lane case."""
    return Channel(width_m=float(width_nm) * 1e-9, depth_m=float(depth_nm) * 1e-9)

def _as_int(value: Any, default: int = 0) -> int:
    return int(round(_as_float(value, float(default))))


def _nested_get(*sources: dict[str, Any], key: str, default: Any = None) -> Any:
    for source in sources:
        if key in source and source[key] is not None:
            return source[key]
    return default


def _particle_material_from_name(name: str, particle: Any) -> str:
    material_key = getattr(particle, "material_key", None)
    if material_key == "gold" or name.startswith("gold_"):
        return "gold"
    if material_key == "silver" or name.startswith("silver_"):
        return "silver"
    if str(material_key or "").startswith("exosome") or name.startswith("exosome_"):
        return "exosome"
    return str(material_key or "unknown")


def flatten_sweep_results(
    results: list[dict[str, Any]],
    *,
    scenario_config_id: str,
    cfg: SimulationConfig,
    n_events: int,
    random_seed: int,
    claim_level: str,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for result in results:
        summary = dict(result.get("summary", {}))
        reference = dict(result.get("reference", {}))
        intrinsic = dict(result.get("intrinsic", {}))
        particle = result.get("particle")
        particle_name = str(result.get("particle_name") or getattr(particle, "name", "unknown"))
        diameter_nm = infer_particle_diameter_nm(particle_name)
        if diameter_nm is None and particle is not None:
            diameter_nm = int(round(float(particle.radius_m) * 2e9))
        row = {
            "scenario_config_id": scenario_config_id,
            "scenario_kind": SCENARIO_KIND[scenario_config_id],
            "claim_level": claim_level,
            "particle_name": particle_name,
            "particle_material": _particle_material_from_name(particle_name, particle),
            "particle_diameter_nm": diameter_nm,
            "wavelength_nm": int(round(float(result["wavelength_m"]) * 1e9)),
            "width_nm": int(round(float(result["width_m"]) * 1e9)),
            "depth_nm": int(round(float(result["depth_m"]) * 1e9)),
            "n_events": int(_nested_get(summary, key="n_events", default=n_events)),
            "n_detected": int(_nested_get(summary, key="n_detected", default=0)),
            "random_seed": int(random_seed),
            "readout_profile": scenario_config_id,
            "readout_preset": cfg.readout_preset,
            "threshold_sigma": float(cfg.threshold_sigma),
            "threshold_tail": cfg.threshold_tail,
            "threshold_calibration_source": cfg.threshold_calibration_source,
            "min_peak_width_s": float(cfg.min_peak_width_s),
            "min_peak_interval_s": float(cfg.min_peak_interval_s),
            "pulse_width_measure_mode": cfg.pulse_width_measure_mode,
            "pulse_duration_estimation_policy": cfg.pulse_duration_estimation_policy,
            "pulse_extraction_sampling_interval_s": cfg.pulse_extraction_sampling_interval_s,
            "flow_profile_model": cfg.flow_profile_model,
            "initial_position_distribution_mode": cfg.initial_position_distribution_mode,
            "initial_position_flux_weighted_mixture_fraction": (
                float(cfg.initial_position_flux_weighted_mixture_fraction)
            ),
            "colored_noise_false_alarm_model": cfg.colored_noise_false_alarm_model,
            "post_readout_colored_noise_std": float(cfg.post_readout_colored_noise_std),
            "post_readout_colored_noise_tau_s": float(cfg.post_readout_colored_noise_tau_s),
            "lockin_time_constant_s": float(cfg.lockin_time_constant_s),
            "nodi_lockin_frequency_Hz": float(cfg.nodi_lockin_frequency_Hz),
            "pulse_detection_mode": cfg.pulse_detection_mode,
            "detection_decision_mode": cfg.detection_decision_mode,
            "readout_observable_mode": cfg.readout_observable_mode,
            "detection_rate": _as_float(summary.get("detection_rate")),
            "detection_rate_wilson_lb": _as_float(summary.get("detection_rate_wilson_lb")),
            "all_crossing_detection_rate": _as_float(
                summary.get("all_crossing_detection_rate"),
                _as_float(summary.get("detection_rate")),
            ),
            "all_crossing_detection_rate_wilson_lb": _as_float(
                summary.get("all_crossing_detection_rate_wilson_lb"),
                _as_float(summary.get("detection_rate_wilson_lb")),
            ),
            "selected_detector_mode_candidate_n_events": _as_int(
                summary.get("selected_detector_mode_candidate_n_events")
            ),
            "selected_detector_mode_candidate_fraction": _as_float(
                summary.get("selected_detector_mode_candidate_fraction")
            ),
            "selected_detector_mode_candidate_detection_rate": _as_float(
                summary.get("selected_detector_mode_candidate_detection_rate")
            ),
            "selected_detector_mode_candidate_detection_rate_wilson_lb": _as_float(
                summary.get(
                    "selected_detector_mode_candidate_detection_rate_wilson_lb"
                )
            ),
            "selected_detector_mode_annulus_edge_norm_min": _as_float(
                summary.get("selected_detector_mode_annulus_edge_norm_min")
            ),
            "selected_detector_mode_annulus_edge_norm_max": _as_float(
                summary.get("selected_detector_mode_annulus_edge_norm_max")
            ),
            "selected_detector_mode_annulus_n_events": _as_int(
                summary.get("selected_detector_mode_annulus_n_events")
            ),
            "selected_detector_mode_annulus_fraction": _as_float(
                summary.get("selected_detector_mode_annulus_fraction")
            ),
            "selected_detector_mode_annulus_detection_rate": _as_float(
                summary.get("selected_detector_mode_annulus_detection_rate"),
                float("nan"),
            ),
            "selected_detector_mode_annulus_detection_rate_wilson_lb": _as_float(
                summary.get(
                    "selected_detector_mode_annulus_detection_rate_wilson_lb"
                ),
                float("nan"),
            ),
            "stable_detection_rate": _as_float(summary.get("stable_detection_rate")),
            "stable_detection_rate_wilson_lb": _as_float(
                summary.get("stable_detection_rate_wilson_lb")
            ),
            "single_channel_detection_rate": _as_float(
                summary.get("single_channel_detection_rate")
            ),
            "paired_channel_detection_rate": _as_float(
                summary.get("paired_channel_detection_rate")
            ),
            "mean_peak_height": _as_float(summary.get("mean_peak_height")),
            "mean_peak_width_s": _as_float(summary.get("mean_peak_width_s")),
            "mean_peak_margin_z": _as_float(summary.get("mean_peak_margin_z")),
            "mean_local_snr": _as_float(summary.get("mean_local_snr")),
            "mean_transit_time_ms": _as_float(summary.get("mean_transit_time_s")) * 1e3,
            "mean_nodi_transit_bandwidth_gain": _as_float(
                summary.get("mean_nodi_transit_bandwidth_gain"), 1.0
            ),
            "phase_flip_fraction": _as_float(summary.get("phase_flip_fraction")),
            "reference_operating_band": _nested_get(
                result, summary, reference, key="reference_operating_band", default="unknown"
            ),
            "na_cutoff_active": bool(
                _nested_get(result, summary, reference, key="na_cutoff_active", default=False)
            ),
            "rho_physical_envelope_status": _nested_get(
                result,
                summary,
                reference,
                key="rho_physical_envelope_status",
                default="unknown",
            ),
            "engineering_gate_passed": bool(result.get("engineering_gate_passed", False)),
            "engineering_gate_primary_blocker": result.get(
                "engineering_gate_primary_blocker",
                result.get("engineering_gate_reason", "unknown"),
            ),
            "score": _as_float(result.get("score")),
            "final_engineering_score": _as_float(result.get("final_engineering_score")),
            "A_ref": _as_float(reference.get("A_ref")),
            "g_ref": _as_float(reference.get("g_ref")),
            "E_sca_normalized": _as_float(intrinsic.get("E_sca_unit_normalized")),
            "config_hash": config_hash(cfg),
        }
        rows.append(row)
    return pd.DataFrame(rows)


def evaluate_gold_anchor(df: pd.DataFrame, *, final_stage: bool) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if df.empty:
        return out
    for scenario_id, sub in df.groupby("scenario_config_id", dropna=False):
        primary = sub[
            [
                (int(r.wavelength_nm), int(r.width_nm), int(r.depth_nm))
                in PRIMARY_TSUYAMA_LIKE_CASES
                for r in sub.itertuples(index=False)
            ]
        ].copy()
        if primary.empty:
            primary = sub.copy()
        au20 = primary[primary["particle_diameter_nm"] == 20]
        au30 = primary[primary["particle_diameter_nm"] == 30]
        component: dict[str, bool] = {}
        component["au20_smoke_detectability"] = (
            not au20.empty and int(au20["n_detected"].min()) >= 3
        )
        component["au20_final_lb_positive"] = (
            not final_stage
            or (not au20.empty and float(au20["detection_rate_wilson_lb"].min()) > 0.0)
        )
        joined = au20.merge(
            au30,
            on=["wavelength_nm", "width_nm", "depth_nm"],
            suffixes=("_au20", "_au30"),
        )
        component["au30_gt_au20_snr"] = bool(
            not joined.empty
            and (
                joined["mean_local_snr_au30"] > joined["mean_local_snr_au20"]
            ).all()
        )
        component["au30_gt_au20_peak"] = bool(
            not joined.empty
            and (
                joined["mean_peak_height_au30"] > joined["mean_peak_height_au20"]
            ).all()
        )
        ladder = (
            primary.groupby("particle_diameter_nm", dropna=False)
            .agg(
                mean_peak_height=("mean_peak_height", "median"),
                mean_local_snr=("mean_local_snr", "median"),
            )
            .reindex(list(GOLD_DIAMETERS_NM))
        )
        component["ladder_monotonic_peak"] = _nondecreasing_with_minor_inversion(
            ladder["mean_peak_height"].tolist()
        )
        component["ladder_monotonic_snr"] = _nondecreasing_with_minor_inversion(
            ladder["mean_local_snr"].tolist()
        )
        threshold_values = sorted({float(v) for v in primary["threshold_sigma"].dropna().unique()})
        component["threshold_realism"] = all(v in {5.0, 10.0} for v in threshold_values)
        reference_bands = set(primary["reference_operating_band"].fillna("unknown").astype(str))
        component["reference_sanity"] = "reference_too_weak" not in reference_bands

        pass_status = all(component.values())
        blocker = "pass"
        if not pass_status:
            blocker = next(name for name, value in component.items() if not value)
        out[str(scenario_id)] = {
            "gold_anchor_component_status": component,
            "gold_anchor_pass": bool(pass_status),
            "gold_anchor_primary_blocker": blocker,
        }
    return out


def _nondecreasing_with_minor_inversion(values: list[Any]) -> bool:
    finite = [float(v) for v in values if v is not None and not pd.isna(v)]
    if len(finite) < len(GOLD_DIAMETERS_NM):
        return False
    inversions = 0
    for left, right in zip(finite, finite[1:]):
        if right + 1e-15 < left:
            denom = max(abs(left), 1e-15)
            if abs(right - left) / denom > 0.10:
                return False
            inversions += 1
    return inversions <= 1


def attach_gold_status(df: pd.DataFrame, *, final_stage: bool) -> pd.DataFrame:
    statuses = evaluate_gold_anchor(df, final_stage=final_stage)
    if df.empty:
        return df
    out = df.copy()
    out["gold_anchor_component_status"] = out["scenario_config_id"].map(
        lambda sid: json.dumps(
            statuses.get(str(sid), {}).get("gold_anchor_component_status", {}),
            sort_keys=True,
        )
    )
    out["gold_anchor_pass"] = out["scenario_config_id"].map(
        lambda sid: bool(statuses.get(str(sid), {}).get("gold_anchor_pass", False))
    )
    out["gold_anchor_primary_blocker"] = out["scenario_config_id"].map(
        lambda sid: str(statuses.get(str(sid), {}).get("gold_anchor_primary_blocker", "missing"))
    )
    return out


def run_explicit_sweep(
    *,
    scenario_config_id: str,
    particles: list[Any],
    n_events: int,
    random_seed: int,
    n_workers: int,
    claim_level: str,
) -> pd.DataFrame:
    cfg = build_scenario_cfg(scenario_config_id, n_events=n_events)
    cfg = replace(cfg, random_seed=int(random_seed))
    rows: list[pd.DataFrame] = []
    for wavelength_nm, width_nm, depth_nm in all_case_triples():
        baseline_channel = case_baseline_channel(width_nm, depth_nm)
        results = run_parameter_sweep(
            particle_types=particles,
            medium=WATER,
            width_list_m=np.array([width_nm * 1e-9], dtype=float),
            depth_list_m=np.array([depth_nm * 1e-9], dtype=float),
            wavelength_list_m=np.array([wavelength_nm * 1e-9], dtype=float),
            optical_template=OPTICAL_TEMPLATE,
            sim_cfg=cfg,
            theta_grid_rad=THETA_GRID_RAD,
            baseline_particle=BASELINE_PARTICLE,
            baseline_channel=baseline_channel,
            verbose=False,
            n_workers=n_workers,
            medium_resolver=medium_for_particle if particles and particles[0].name.startswith("exosome_") else None,
        )
        part = flatten_sweep_results(
            results,
            scenario_config_id=scenario_config_id,
            cfg=cfg,
            n_events=n_events,
            random_seed=random_seed,
            claim_level=claim_level,
        )
        rows.append(part)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def run_baseline_gate_report(output_dir: Path) -> None:
    ensure_output_dir(output_dir)
    candidate_path = REPORT_INPUT_DIR / "candidate_gate_sensitivity_if_gold_matched.csv"
    scenario_path = REPORT_INPUT_DIR / "gold_matched_gate_scenario_summary.csv"
    weighted_path = REPORT_INPUT_DIR / "candidate_size_distribution_weighted_summary.csv"
    candidate = pd.read_csv(candidate_path)
    scenario = pd.read_csv(scenario_path)
    weighted = pd.read_csv(weighted_path)
    candidate_out = candidate.copy()
    for col in ("current_pass_count", "relaxed10_pass_count", "relaxed05_pass_count", "anypulse_pass_count"):
        if col not in candidate_out:
            candidate_out[col] = 0
    candidate_out["relaxed10_delta_vs_current"] = (
        candidate_out["relaxed10_pass_count"] - candidate_out["current_pass_count"]
    )
    candidate_out["relaxed05_delta_vs_current"] = (
        candidate_out["relaxed05_pass_count"] - candidate_out["current_pass_count"]
    )
    candidate_out["anypulse_delta_vs_current"] = (
        candidate_out["anypulse_pass_count"] - candidate_out["current_pass_count"]
    )
    candidate_out["simulation_status"] = "existing_csv_gate_only_no_new_simulation"
    candidate_out.to_csv(output_dir / "gate_only_existing_report_v1.csv", index=False)
    summary = {
        "input_files": {
            "candidate_gate_sensitivity": str(candidate_path),
            "gold_matched_gate_scenario_summary": str(scenario_path),
            "candidate_size_distribution_weighted_summary": str(weighted_path),
        },
        "simulation_status": "no_simulation_read_existing_csvs_only",
        "candidate_rows": int(len(candidate)),
        "current_pass_count_total": int(candidate_out["current_pass_count"].sum()),
        "relaxed10_pass_count_total": int(candidate_out["relaxed10_pass_count"].sum()),
        "relaxed05_pass_count_total": int(candidate_out["relaxed05_pass_count"].sum()),
        "anypulse_pass_count_total": int(candidate_out["anypulse_pass_count"].sum()),
        "weighted_profile_ids": sorted(weighted["profile"].dropna().astype(str).unique().tolist()),
        "scenario_summary_rows": scenario.to_dict(orient="records"),
    }
    write_json(output_dir / "gate_only_existing_report_v1.json", summary)


def run_build_manifest(output_dir: Path, *, dry_run: bool) -> None:
    manifest = {
        "schema": "tsuyama_gold_aligned_detection_lane_manifest_v1",
        "generated_at_unix": time.time(),
        "scenario_count": len(SCENARIO_ORDER),
        "case_count": len(all_case_triples()),
        "records": scenario_manifest_records(),
        "protected_globals": {
            "readout_presets": sorted(READOUT_PRESET_CONFIG_OVERRIDES),
            "paper_profiles": sorted(PAPER_ALIGNED_PROFILES),
        },
    }
    if dry_run:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return
    ensure_output_dir(output_dir)
    write_json(output_dir / "scenario_manifest_v1.json", manifest)


def run_sweep_gold(
    output_dir: Path,
    *,
    stage: str,
    n_workers: int,
    random_seed: int,
    include_paired: bool,
) -> None:
    ensure_output_dir(output_dir)
    n_events = 1000 if stage == "smoke" else 10000
    scenario_ids = list(SCENARIO_ORDER if include_paired else SCENARIO_ORDER[:3])
    if stage == "final":
        scenario_ids = _final_gold_scenario_ids(output_dir, scenario_ids)
    particles = [make_particle("gold", d) for d in GOLD_DIAMETERS_NM]
    claim_level_by_kind = {
        "nodi_single": "paper_aligned_relative_only",
        "paired_diag": "diagnostic_only",
    }
    frames: list[pd.DataFrame] = []
    t0 = time.time()
    for scenario_id in scenario_ids:
        claim_level = claim_level_by_kind[SCENARIO_KIND[scenario_id]]
        frames.append(
            run_explicit_sweep(
                scenario_config_id=scenario_id,
                particles=particles,
                n_events=n_events,
                random_seed=random_seed,
                n_workers=n_workers,
                claim_level=claim_level,
            )
        )
    df = (
        pd.concat(frames, ignore_index=True)
        if frames
        else pd.DataFrame(columns=list(GOLD_OUTPUT_COLUMNS))
    )
    df = attach_gold_status(df, final_stage=(stage == "final"))
    csv_name = f"gold_targeted_sweep_{stage}_v1.csv"
    meta_name = f"gold_targeted_sweep_{stage}_v1_meta.json"
    df.to_csv(output_dir / csv_name, index=False)
    meta = {
        "stage": stage,
        "n_events": n_events,
        "n_workers": int(n_workers),
        "random_seed": int(random_seed),
        "include_paired": bool(include_paired),
        "scenario_ids": scenario_ids,
        "rows": int(len(df)),
        "runtime_s": time.time() - t0,
        "gold_status": evaluate_gold_anchor(df, final_stage=(stage == "final")),
    }
    write_json(output_dir / meta_name, meta)


def _final_gold_scenario_ids(output_dir: Path, candidates: list[str]) -> list[str]:
    smoke_path = output_dir / "gold_targeted_sweep_smoke_v1.csv"
    blank_path = output_dir / "blank_fpr_sweep_v1.csv"
    if not smoke_path.exists() or not blank_path.exists():
        return candidates
    smoke = pd.read_csv(smoke_path)
    smoke_status = evaluate_gold_anchor(smoke, final_stage=False)
    blank = pd.read_csv(blank_path)
    final_blank = blank[blank["blank_stage"].isin(["final", "empirical_summary"])].copy()
    blank_pass = set(
        final_blank.loc[final_blank["blank_gate_pass"].astype(bool), "scenario_config_id"].astype(str)
    )
    selected = [
        sid
        for sid in candidates
        if bool(smoke_status.get(sid, {}).get("gold_anchor_pass", False)) and sid in blank_pass
    ]
    return selected


def run_synthetic_blank(
    cfg: SimulationConfig,
    *,
    n_blank_traces: int,
    random_seed: int,
    scenario_kind: str,
) -> dict[str, Any]:
    rng = np.random.default_rng(int(random_seed))
    n_samples = int(cfg.n_samples)
    time_s = np.arange(n_samples, dtype=float) / float(cfg.sampling_rate_Hz)
    n_bg = max(1, int(0.2 * n_samples))
    context = build_pulse_extraction_context(
        time_s,
        cfg.min_peak_width_s,
        cfg.min_peak_interval_s,
    )
    detected = 0
    for _ in range(int(n_blank_traces)):
        trace = rng.normal(0.0, 1.0, size=n_samples)
        threshold = estimate_threshold_stats_robust(
            trace[:n_bg],
            sigma_multiplier=float(cfg.threshold_sigma),
        )["threshold"]
        features = extract_pulse_features(
            time_s,
            trace,
            threshold,
            cfg.min_peak_width_s,
            cfg.min_peak_interval_s,
            detection_mode=cfg.pulse_detection_mode,
            context=context,
            include_area_prominence=False,
            width_measure_mode=cfg.pulse_width_measure_mode,
        )
        if int(features["n_peaks"]) > 0:
            detected += 1
    per_trace = detected / float(n_blank_traces) if n_blank_traces else 0.0
    ub_trace = wilson_upper_bound(detected, int(n_blank_traces))
    return {
        "n_blank_traces": int(n_blank_traces),
        "n_blank_detected": int(detected),
        "blank_false_positive_rate_per_trace": float(per_trace),
        "blank_false_positive_wilson_ub_per_trace": float(ub_trace),
        "blank_false_positive_rate_per_s": float(per_trace / cfg.total_time_s),
        "blank_false_positive_wilson_ub_per_s": float(ub_trace / cfg.total_time_s),
        "paired_false_alarm_status": (
            "synthetic_independent_lanes_not_primary_feasibility"
            if scenario_kind == "paired_diag"
            else "not_applicable_single_lane"
        ),
    }


def run_sweep_blank(
    output_dir: Path,
    *,
    stage: str,
    n_workers: int,
    random_seed: int,
    blank_summary: Path | None,
    include_paired: bool,
) -> None:
    ensure_output_dir(output_dir)
    scenario_ids = list(SCENARIO_ORDER if include_paired else SCENARIO_ORDER[:3])
    rows: list[dict[str, Any]] = []
    t0 = time.time()
    if blank_summary is not None and blank_summary.exists():
        empirical = pd.read_csv(blank_summary)
        for scenario_id in scenario_ids:
            cfg = build_scenario_cfg(scenario_id)
            rate = float(empirical.get("empirical_peak_false_alarm_rate_per_minute", pd.Series([0.0])).iloc[0])
            per_s = rate / 60.0
            row = _blank_row_base(scenario_id, cfg, "empirical_summary")
            row.update(
                {
                    "blank_model_source": "empirical_blank_summary",
                    "blank_claim_level": "empirical_summary_guardrail",
                    "n_blank_traces": 0,
                    "n_blank_detected": 0,
                    "blank_false_positive_rate_per_trace": 0.0,
                    "blank_false_positive_wilson_ub_per_trace": 0.0,
                    "blank_false_positive_rate_per_s": per_s,
                    "blank_false_positive_wilson_ub_per_s": per_s,
                    "paired_false_alarm_status": "empirical_summary",
                }
            )
            row.update(_blank_gate(row))
            rows.append(row)
    else:
        n_blank_traces = 1000 if stage == "smoke" else 10000
        if stage == "final":
            scenario_ids = _final_blank_scenario_ids(output_dir, scenario_ids)
        for scenario_id in scenario_ids:
            cfg = build_scenario_cfg(scenario_id)
            stats = run_synthetic_blank(
                cfg,
                n_blank_traces=n_blank_traces,
                random_seed=random_seed + SCENARIO_ORDER.index(scenario_id) * 1009,
                scenario_kind=SCENARIO_KIND[scenario_id],
            )
            row = _blank_row_base(scenario_id, cfg, stage)
            row.update(
                {
                    "blank_model_source": "synthetic_iid_zero_signal",
                    "blank_claim_level": "synthetic_guardrail_not_empirical_calibration",
                    **stats,
                }
            )
            row.update(_blank_gate(row))
            rows.append(row)
    df = pd.DataFrame(rows)
    csv_path = output_dir / "blank_fpr_sweep_v1.csv"
    if csv_path.exists() and stage == "final":
        previous = pd.read_csv(csv_path)
        previous = previous[previous["blank_stage"] != "final"]
        df = pd.concat([previous, df], ignore_index=True)
    df.to_csv(csv_path, index=False)
    write_json(
        output_dir / "blank_fpr_sweep_v1_meta.json",
        {
            "stage": stage,
            "n_workers": int(n_workers),
            "blank_summary": str(blank_summary) if blank_summary else None,
            "include_paired": bool(include_paired),
            "rows": int(len(df)),
            "runtime_s": time.time() - t0,
        },
    )


def _blank_row_base(scenario_id: str, cfg: SimulationConfig, stage: str) -> dict[str, Any]:
    return {
        "scenario_config_id": scenario_id,
        "scenario_kind": SCENARIO_KIND[scenario_id],
        "blank_stage": stage,
        "threshold_sigma": float(cfg.threshold_sigma),
        "threshold_tail": cfg.threshold_tail,
        "min_peak_width_s": float(cfg.min_peak_width_s),
        "min_peak_interval_s": float(cfg.min_peak_interval_s),
        "pulse_width_measure_mode": cfg.pulse_width_measure_mode,
        "pulse_detection_mode": cfg.pulse_detection_mode,
        "detection_decision_mode": cfg.detection_decision_mode,
    }


def _blank_gate(row: dict[str, Any]) -> dict[str, Any]:
    ub_trace = _as_float(row.get("blank_false_positive_wilson_ub_per_trace"), 1.0)
    ub_s = _as_float(row.get("blank_false_positive_wilson_ub_per_s"), 1.0)
    pass_gate = bool(ub_trace <= 1e-3 or ub_s <= 1e-2)
    return {
        "blank_gate_pass": pass_gate,
        "blank_gate_primary_blocker": "pass" if pass_gate else "blank_fpr_wilson_ub",
    }


def _final_blank_scenario_ids(output_dir: Path, candidates: list[str]) -> list[str]:
    smoke_path = output_dir / "gold_targeted_sweep_smoke_v1.csv"
    if not smoke_path.exists():
        return candidates
    smoke = pd.read_csv(smoke_path)
    status = evaluate_gold_anchor(smoke, final_stage=False)
    selected = [
        sid
        for sid in candidates
        if bool(status.get(sid, {}).get("gold_anchor_pass", False))
    ]
    return selected or candidates


def run_select_feasible(output_dir: Path) -> None:
    ensure_output_dir(output_dir)
    final_gold_path = output_dir / "gold_targeted_sweep_final_v1.csv"
    smoke_gold_path = output_dir / "gold_targeted_sweep_smoke_v1.csv"
    gold_path = final_gold_path if final_gold_path.exists() else smoke_gold_path
    blank_path = output_dir / "blank_fpr_sweep_v1.csv"
    if not gold_path.exists() or not blank_path.exists():
        raise SystemExit("gold sweep and blank FPR outputs are required before select-feasible")
    gold = pd.read_csv(gold_path)
    if gold.empty and gold_path == final_gold_path and smoke_gold_path.exists():
        gold_path = smoke_gold_path
        gold = pd.read_csv(gold_path)
    final_stage = gold_path.name.endswith("final_v1.csv")
    gold_status = evaluate_gold_anchor(gold, final_stage=final_stage)
    blank = pd.read_csv(blank_path)
    usable_blank = blank[blank["blank_stage"].isin(["final", "empirical_summary"])].copy()
    if usable_blank.empty:
        usable_blank = blank.copy()
    blank_status = (
        usable_blank.sort_values("blank_stage")
        .drop_duplicates("scenario_config_id", keep="last")
        .set_index("scenario_config_id")
        .to_dict(orient="index")
    )
    rows = compute_feasible_rows(gold, gold_status, blank_status)
    df = pd.DataFrame(rows, columns=list(FEASIBLE_OUTPUT_COLUMNS))
    df.to_csv(output_dir / "feasible_scenarios_v1.csv", index=False)
    payload = {
        "gold_source": str(gold_path),
        "blank_source": str(blank_path),
        "scenario_status": _scenario_feasible_summary(df),
        "rows": rows,
    }
    write_json(output_dir / "feasible_scenarios_v1.json", payload)


def compute_feasible_rows(
    gold: pd.DataFrame,
    gold_status: dict[str, dict[str, Any]],
    blank_status: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    case_cols = ["scenario_config_id", "wavelength_nm", "width_nm", "depth_nm"]
    for keys, sub in gold.groupby(case_cols, dropna=False):
        scenario_id = str(keys[0])
        case = (int(keys[1]), int(keys[2]), int(keys[3]))
        gstat = gold_status.get(scenario_id, {})
        bstat = blank_status.get(scenario_id, {})
        scenario_kind = SCENARIO_KIND.get(scenario_id, str(sub["scenario_kind"].iloc[0]))
        gold_pass = bool(gstat.get("gold_anchor_pass", False))
        blank_pass = bool(bstat.get("blank_gate_pass", False))
        scenario_config_feasible = bool(
            gold_pass and blank_pass and scenario_kind == "nodi_single"
        )
        reference_ok = not (sub["reference_operating_band"].astype(str) == "reference_too_weak").any()
        rho_ok = (
            sub["rho_physical_envelope_status"].astype(str) == "within_envelope"
        ).all()
        na_hard_block = bool(sub["na_cutoff_active"].astype(bool).any())
        case_feasible = bool(
            scenario_config_feasible and reference_ok and rho_ok and not na_hard_block
        )
        paired_diag_pass = bool(gold_pass and blank_pass and scenario_kind == "paired_diag")
        rows.append(
            {
                "scenario_config_id": scenario_id,
                "scenario_kind": scenario_kind,
                "wavelength_nm": case[0],
                "width_nm": case[1],
                "depth_nm": case[2],
                "case_role": case_role(case),
                "gold_anchor_pass": gold_pass,
                "gold_anchor_primary_blocker": gstat.get("gold_anchor_primary_blocker", "missing"),
                "blank_gate_pass": blank_pass,
                "blank_gate_primary_blocker": bstat.get("blank_gate_primary_blocker", "missing"),
                "scenario_config_feasible": scenario_config_feasible,
                "case_feasible": case_feasible,
                "paired_diag_pass": paired_diag_pass,
                "reference_operating_band": (
                    "reference_too_weak" if not reference_ok else str(sub["reference_operating_band"].mode().iat[0])
                ),
                "rho_physical_envelope_status": (
                    "blocked" if not rho_ok else str(sub["rho_physical_envelope_status"].mode().iat[0])
                ),
                "na_cutoff_active": na_hard_block,
            }
        )
    return rows


FEASIBLE_OUTPUT_COLUMNS = (
    "scenario_config_id",
    "scenario_kind",
    "wavelength_nm",
    "width_nm",
    "depth_nm",
    "case_role",
    "gold_anchor_pass",
    "gold_anchor_primary_blocker",
    "blank_gate_pass",
    "blank_gate_primary_blocker",
    "scenario_config_feasible",
    "case_feasible",
    "paired_diag_pass",
    "reference_operating_band",
    "rho_physical_envelope_status",
    "na_cutoff_active",
)

EV_OUTPUT_COLUMNS = (
    "scenario_config_id",
    "EV_ensemble_name",
    "EV_ensemble_member_preset",
    "EV_size_distribution_profile",
    "particle_diameter_nm",
    "wavelength_nm",
    "width_nm",
    "depth_nm",
    "detection_rate",
    "stable_detection_rate",
    "all_crossing_detection_rate",
    "selected_detector_mode_candidate_fraction",
    "selected_detector_mode_candidate_detection_rate",
    "selected_detector_mode_annulus_edge_norm_min",
    "selected_detector_mode_annulus_edge_norm_max",
    "selected_detector_mode_annulus_fraction",
    "selected_detector_mode_annulus_detection_rate",
    "weighted_detection_rate",
    "weighted_stable_detection_rate",
    "weighted_gate_pass_fraction",
    "weighted_selected_detector_mode_candidate_detection_rate",
    "weighted_selected_detector_mode_candidate_fraction",
    "weighted_selected_detector_mode_annulus_detection_rate",
    "weighted_selected_detector_mode_annulus_fraction",
    "reference_operating_band",
    "case_feasible",
    "ranking_within_scenario",
    "ranking_within_scenario_all_crossing",
    "ranking_within_scenario_selected_annulus",
    "selected_annulus_lens_status",
    "ranking_stability_band",
    "comparison_support_status",
)

COMPARISON_OUTPUT_COLUMNS = (
    "scenario_config_id",
    "EV_size_distribution_profile",
    "comparison_support_status",
    "old_top3_routes",
    "new_top3_routes",
    "new_all_crossing_top3_routes",
    "selected_annulus_lens_available",
    "selected_annulus_lens_status",
    "selected_annulus_top3_routes",
    "top3_changed",
    "selected_annulus_top3_changed_vs_all_crossing",
    "current_532_600x1500_rank",
    "current_532_600x1500_weighted_stable_detection_rate",
    "current_532_600x1500_selected_annulus_rank",
    "current_532_600x1500_weighted_selected_annulus_detection_rate",
    "current_532_600x1500_weighted_selected_annulus_fraction",
)


def _scenario_feasible_summary(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty:
        return []
    grouped = (
        df.groupby(["scenario_config_id", "scenario_kind"], dropna=False)
        .agg(
            scenario_config_feasible=("scenario_config_feasible", "max"),
            feasible_case_count=("case_feasible", "sum"),
            paired_diag_pass=("paired_diag_pass", "max"),
        )
        .reset_index()
    )
    return grouped.to_dict(orient="records")


def build_ev_weight_profiles() -> dict[str, Any]:
    weights = {
        "equal_current": {str(d): 1.0 for d in EV_DIAMETERS_NM},
        "sEV_small_70nm_gsd1p45": _lognormal_discrete_weights(70.0, 1.45),
        "sEV_mid_100nm_gsd1p5": _lognormal_discrete_weights(100.0, 1.5),
        "large_tail_150nm_gsd1p6": _lognormal_discrete_weights(150.0, 1.6),
    }
    normalized = {name: _normalize_weights(raw) for name, raw in weights.items()}
    return {
        "size_support_nm": list(EV_DIAMETERS_NM),
        "weight_profile_source": "explicit_v1_reconstruction",
        "profiles": normalized,
    }


def _lognormal_discrete_weights(median_nm: float, gsd: float) -> dict[str, float]:
    sigma = math.log(gsd)
    mu = math.log(median_nm)
    out: dict[str, float] = {}
    for diameter_nm in EV_DIAMETERS_NM:
        x = float(diameter_nm)
        out[str(diameter_nm)] = math.exp(-((math.log(x) - mu) ** 2) / (2.0 * sigma**2)) / x
    return out


def _normalize_weights(raw: dict[str, float]) -> dict[str, float]:
    total = sum(float(v) for v in raw.values())
    return {str(k): float(v) / total for k, v in raw.items()}


def run_sweep_ev_panel(output_dir: Path, *, n_events: int, n_workers: int, random_seed: int) -> None:
    ensure_output_dir(output_dir)
    feasible_path = output_dir / "feasible_scenarios_v1.csv"
    if not feasible_path.exists():
        raise SystemExit("feasible_scenarios_v1.csv is required before sweep-ev-panel")
    feasible = pd.read_csv(feasible_path)
    cases = feasible[
        feasible["scenario_config_feasible"].astype(bool)
        & feasible["case_feasible"].astype(bool)
        & (feasible["scenario_kind"] == "nodi_single")
    ].copy()
    if cases.empty:
        pd.DataFrame(columns=list(EV_OUTPUT_COLUMNS)).to_csv(
            output_dir / "ev_targeted_panel_v1.csv",
            index=False,
        )
        weights = build_ev_weight_profiles()
        write_json(output_dir / "ev_size_weight_profiles_v1.json", weights)
        write_json(
            output_dir / "ev_targeted_panel_v1_meta.json",
            {
                "completion_status": "skipped_no_feasible_nodi_single_scenario",
                "n_events": int(n_events),
                "n_workers": int(n_workers),
                "random_seed": int(random_seed),
                "rows": 0,
                "weight_profile_source": weights["weight_profile_source"],
            },
        )
        raise SystemExit("No NODI single-channel feasible scenario exists; refusing EV panel")
    particles = build_biomimetic_exosome_ensemble_family(list(EV_DIAMETERS_NM))
    frames: list[pd.DataFrame] = []
    t0 = time.time()
    for scenario_id, sub in cases.groupby("scenario_config_id", dropna=False):
        cfg = build_scenario_cfg(str(scenario_id), n_events=n_events)
        cfg = replace(cfg, random_seed=int(random_seed))
        scenario_frames: list[pd.DataFrame] = []
        for row in sub.itertuples(index=False):
            width_nm = int(row.width_nm)
            depth_nm = int(row.depth_nm)
            wavelength_nm = int(row.wavelength_nm)
            baseline_channel = case_baseline_channel(width_nm, depth_nm)
            results = run_parameter_sweep(
                particle_types=particles,
                medium=PBS_1X,
                width_list_m=np.array([width_nm * 1e-9], dtype=float),
                depth_list_m=np.array([depth_nm * 1e-9], dtype=float),
                wavelength_list_m=np.array([wavelength_nm * 1e-9], dtype=float),
                optical_template=OPTICAL_TEMPLATE,
                sim_cfg=cfg,
                theta_grid_rad=THETA_GRID_RAD,
                baseline_particle=BASELINE_PARTICLE,
                baseline_channel=baseline_channel,
                verbose=False,
                n_workers=n_workers,
                medium_resolver=medium_for_particle,
            )
            scenario_frames.append(
                flatten_sweep_results(
                    results,
                    scenario_config_id=str(scenario_id),
                    cfg=cfg,
                    n_events=n_events,
                    random_seed=random_seed,
                    claim_level="ev_targeted_transfer_under_feasible_gold_blank_lane",
                )
            )
        frames.extend(scenario_frames)
    raw = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    ev = _ev_rows_from_raw(raw)
    ev.to_csv(output_dir / "ev_targeted_panel_v1.csv", index=False)
    weights = build_ev_weight_profiles()
    write_json(output_dir / "ev_size_weight_profiles_v1.json", weights)
    write_json(
        output_dir / "ev_targeted_panel_v1_meta.json",
        {
            "n_events": int(n_events),
            "n_workers": int(n_workers),
            "random_seed": int(random_seed),
            "rows": int(len(ev)),
            "runtime_s": time.time() - t0,
            "weight_profile_source": weights["weight_profile_source"],
        },
    )


def _ev_rows_from_raw(raw: pd.DataFrame) -> pd.DataFrame:
    weights = build_ev_weight_profiles()["profiles"]
    rows: list[pd.DataFrame] = []
    for profile_id, profile_weights in weights.items():
        part = raw.copy()
        part["EV_size_distribution_profile"] = profile_id
        part["EV_ensemble_name"] = "literature_bounds_2021"
        part["EV_ensemble_member_preset"] = part["particle_name"].map(
            lambda name: infer_biomimetic_exosome_preset_name(str(name)) or "unknown"
        )
        part["weight"] = part["particle_diameter_nm"].map(
            lambda d: float(profile_weights.get(str(int(d)), 0.0)) / 4.0
        )
        group_cols = [
            "scenario_config_id",
            "EV_size_distribution_profile",
            "wavelength_nm",
            "width_nm",
            "depth_nm",
        ]
        agg = (
            part.groupby(group_cols, dropna=False)
            .apply(
                lambda x: pd.Series(
                    {
                        "weighted_detection_rate": float((x["detection_rate"] * x["weight"]).sum()),
                        "weighted_stable_detection_rate": float(
                            (x["stable_detection_rate"] * x["weight"]).sum()
                        ),
                        "weighted_gate_pass_fraction": float(
                            (x["engineering_gate_passed"].astype(float) * x["weight"]).sum()
                        ),
                        "weighted_selected_detector_mode_candidate_detection_rate": (
                            _weighted_sum_metric(
                                x,
                                "selected_detector_mode_candidate_detection_rate",
                            )
                        ),
                        "weighted_selected_detector_mode_candidate_fraction": (
                            _weighted_sum_metric(
                                x,
                                "selected_detector_mode_candidate_fraction",
                            )
                        ),
                        "weighted_selected_detector_mode_annulus_detection_rate": (
                            _weighted_sum_metric(
                                x,
                                "selected_detector_mode_annulus_detection_rate",
                            )
                        ),
                        "weighted_selected_detector_mode_annulus_fraction": (
                            _weighted_sum_metric(
                                x,
                                "selected_detector_mode_annulus_fraction",
                            )
                        ),
                    }
                ),
                include_groups=False,
            )
            .reset_index()
        )
        part = part.merge(agg, on=group_cols, how="left")
        part["case_feasible"] = True
        part["comparison_support_status"] = "targeted_support_not_bitwise"
        part["ranking_stability_band"] = "targeted_v1"
        part["selected_annulus_lens_status"] = "selected_annulus_parallel_lens_v1"
        all_crossing_rank_frame = _rank_ev_routes(
            agg,
            sort_cols=[
                "weighted_stable_detection_rate",
                "weighted_detection_rate",
            ],
            rank_col="ranking_within_scenario_all_crossing",
        )
        selected_annulus_rank_frame = _rank_ev_routes(
            agg,
            sort_cols=[
                "weighted_selected_detector_mode_annulus_detection_rate",
                "weighted_stable_detection_rate",
            ],
            rank_col="ranking_within_scenario_selected_annulus",
        )
        part = part.merge(
            all_crossing_rank_frame[
                [
                    "scenario_config_id",
                    "EV_size_distribution_profile",
                    "wavelength_nm",
                    "width_nm",
                    "depth_nm",
                    "ranking_within_scenario_all_crossing",
                ]
            ],
            on=group_cols,
            how="left",
        )
        part = part.merge(
            selected_annulus_rank_frame[
                [
                    "scenario_config_id",
                    "EV_size_distribution_profile",
                    "wavelength_nm",
                    "width_nm",
                    "depth_nm",
                    "ranking_within_scenario_selected_annulus",
                ]
            ],
            on=group_cols,
            how="left",
        )
        part["ranking_within_scenario"] = part["ranking_within_scenario_all_crossing"]
        rows.append(part)
    ev = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    for column in EV_OUTPUT_COLUMNS:
        if column not in ev.columns:
            ev[column] = 0.0 if _is_ev_numeric_diagnostic_column(column) else None
    return ev[list(EV_OUTPUT_COLUMNS)]


def _weighted_sum_metric(frame: pd.DataFrame, column: str) -> float:
    if column not in frame.columns:
        return 0.0
    values = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
    weights = pd.to_numeric(frame["weight"], errors="coerce").fillna(0.0)
    return float((values * weights).sum())


def _rank_ev_routes(
    routes: pd.DataFrame,
    *,
    sort_cols: list[str],
    rank_col: str,
) -> pd.DataFrame:
    if routes.empty:
        out = routes.copy()
        out[rank_col] = pd.Series(dtype=float)
        return out
    ranked = routes.sort_values(
        [
            "scenario_config_id",
            "EV_size_distribution_profile",
            *sort_cols,
        ],
        ascending=[True, True, *([False] * len(sort_cols))],
    ).copy()
    ranked[rank_col] = (
        ranked.groupby(["scenario_config_id", "EV_size_distribution_profile"])
        .cumcount()
        .add(1)
    )
    return ranked


def _is_ev_numeric_diagnostic_column(column: str) -> bool:
    return (
        column.startswith("selected_detector_mode_")
        or column.startswith("weighted_selected_detector_mode_")
        or column == "all_crossing_detection_rate"
        or column.startswith("ranking_within_scenario")
    )


def run_compare_ranking(output_dir: Path) -> None:
    ensure_output_dir(output_dir)
    ev_path = output_dir / "ev_targeted_panel_v1.csv"
    old_path = REPORT_INPUT_DIR / "candidate_size_distribution_weighted_summary.csv"
    if not ev_path.exists():
        raise SystemExit("ev_targeted_panel_v1.csv is required before compare-ranking")
    ev = pd.read_csv(ev_path)
    old = pd.read_csv(old_path)
    comparison = compare_ranking_frames(ev, old)
    if comparison.empty:
        comparison = pd.DataFrame(columns=list(COMPARISON_OUTPUT_COLUMNS))
    comparison.to_csv(output_dir / "ev_ranking_comparison_v1.csv", index=False)
    payload = {
        "comparison_support_status": "targeted_support_not_bitwise",
        "ranking_change_profile_count": int(comparison["top3_changed"].sum())
        if not comparison.empty
        else 0,
        "selected_annulus_top3_diff_profile_count": int(
            comparison["selected_annulus_top3_changed_vs_all_crossing"].sum()
        )
        if not comparison.empty
        and "selected_annulus_top3_changed_vs_all_crossing" in comparison
        else 0,
        "rows": comparison.to_dict(orient="records"),
    }
    write_json(output_dir / "ev_ranking_comparison_v1.json", payload)


def compare_ranking_frames(ev: pd.DataFrame, old: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    route_cols = ["wavelength_nm", "width_nm", "depth_nm"]
    selected_annulus_missing_columns = [
        column
        for column in (
            "weighted_selected_detector_mode_annulus_detection_rate",
            "weighted_selected_detector_mode_annulus_fraction",
        )
        if column not in ev.columns
    ]
    ev = _ensure_ev_comparison_lens_columns(
        ev,
        selected_annulus_missing_columns=selected_annulus_missing_columns,
    )
    new_routes = (
        ev.groupby(["scenario_config_id", "EV_size_distribution_profile", *route_cols], dropna=False)
        .agg(
            weighted_detection_rate=("weighted_detection_rate", "max"),
            weighted_stable_detection_rate=("weighted_stable_detection_rate", "max"),
            weighted_gate_pass_fraction=("weighted_gate_pass_fraction", "max"),
            weighted_selected_detector_mode_annulus_detection_rate=(
                "weighted_selected_detector_mode_annulus_detection_rate",
                "max",
            ),
            weighted_selected_detector_mode_annulus_fraction=(
                "weighted_selected_detector_mode_annulus_fraction",
                "max",
            ),
        )
        .reset_index()
    )
    for scenario_id, scenario_sub in new_routes.groupby("scenario_config_id", dropna=False):
        for profile_id, new_sub in scenario_sub.groupby("EV_size_distribution_profile", dropna=False):
            old_sub = old[old["profile"] == profile_id].copy()
            selected_annulus_available = _selected_annulus_lens_available_for_profile(
                new_sub,
                selected_annulus_missing_columns=selected_annulus_missing_columns,
            )
            selected_annulus_status = _selected_annulus_lens_status(
                selected_annulus_available,
                selected_annulus_missing_columns=selected_annulus_missing_columns,
            )
            selected_annulus_valid = _selected_annulus_valid_rows(new_sub)
            selected_annulus_sub = new_sub[selected_annulus_valid].copy()
            new_top3 = _top_route_set(
                new_sub,
                ["weighted_stable_detection_rate", "weighted_detection_rate"],
                route_cols,
            )
            old_top3 = _top_route_set(
                old_sub,
                ["weighted_stable_per_10000", "weighted_detected_per_10000"],
                route_cols,
            )
            selected_annulus_top3 = (
                _top_route_set(
                    selected_annulus_sub,
                    [
                        "weighted_selected_detector_mode_annulus_detection_rate",
                        "weighted_stable_detection_rate",
                    ],
                    route_cols,
                )
                if selected_annulus_available
                else set()
            )
            current_532 = new_sub[
                (new_sub["wavelength_nm"] == 532)
                & (new_sub["width_nm"] == 600)
                & (new_sub["depth_nm"] == 1500)
            ]
            current_532_selected_annulus = current_532[
                _selected_annulus_valid_rows(current_532)
            ]
            current_532_rank = _route_rank(
                new_sub,
                route=(532, 600, 1500),
                sort_cols=["weighted_stable_detection_rate", "weighted_detection_rate"],
            )
            current_532_selected_annulus_rank = (
                _route_rank(
                    selected_annulus_sub,
                    route=(532, 600, 1500),
                    sort_cols=[
                        "weighted_selected_detector_mode_annulus_detection_rate",
                        "weighted_stable_detection_rate",
                    ],
                )
                if selected_annulus_available
                else None
            )
            current_532_selected_annulus_detection_rate = (
                _max_or_none(
                    current_532_selected_annulus[
                        "weighted_selected_detector_mode_annulus_detection_rate"
                    ]
                )
                if selected_annulus_available and not current_532_selected_annulus.empty
                else None
            )
            current_532_selected_annulus_fraction = (
                _max_or_none(
                    current_532_selected_annulus[
                        "weighted_selected_detector_mode_annulus_fraction"
                    ]
                )
                if selected_annulus_available and not current_532_selected_annulus.empty
                else None
            )
            rows.append(
                {
                    "scenario_config_id": scenario_id,
                    "EV_size_distribution_profile": profile_id,
                    "comparison_support_status": "targeted_support_not_bitwise",
                    "old_top3_routes": json.dumps(sorted(old_top3)),
                    "new_top3_routes": json.dumps(sorted(new_top3)),
                    "new_all_crossing_top3_routes": json.dumps(sorted(new_top3)),
                    "selected_annulus_lens_available": selected_annulus_available,
                    "selected_annulus_lens_status": selected_annulus_status,
                    "selected_annulus_top3_routes": json.dumps(
                        sorted(selected_annulus_top3)
                    ),
                    "top3_changed": old_top3 != new_top3,
                    "selected_annulus_top3_changed_vs_all_crossing": (
                        selected_annulus_available
                        and selected_annulus_top3 != new_top3
                    ),
                    "current_532_600x1500_rank": current_532_rank,
                    "current_532_600x1500_weighted_stable_detection_rate": (
                        float(current_532["weighted_stable_detection_rate"].max())
                        if not current_532.empty
                        else None
                    ),
                    "current_532_600x1500_selected_annulus_rank": (
                        current_532_selected_annulus_rank
                    ),
                    "current_532_600x1500_weighted_selected_annulus_detection_rate": (
                        current_532_selected_annulus_detection_rate
                    ),
                    "current_532_600x1500_weighted_selected_annulus_fraction": (
                        current_532_selected_annulus_fraction
                    ),
                }
            )
    return pd.DataFrame(rows)


def _ensure_ev_comparison_lens_columns(
    ev: pd.DataFrame,
    *,
    selected_annulus_missing_columns: list[str],
) -> pd.DataFrame:
    out = ev.copy()
    defaults = {
        "weighted_detection_rate": 0.0,
        "weighted_stable_detection_rate": 0.0,
        "weighted_gate_" + "pass_fraction": 0.0,
    }
    for column, default in defaults.items():
        if column not in out.columns:
            out[column] = default
        else:
            out[column] = pd.to_numeric(out[column], errors="coerce").fillna(default)
    for column in (
        "weighted_selected_detector_mode_annulus_detection_rate",
        "weighted_selected_detector_mode_annulus_fraction",
    ):
        if column not in out.columns:
            out[column] = float("nan")
        else:
            values = pd.to_numeric(out[column], errors="coerce")
            out[column] = values
    return out


def _selected_annulus_lens_available_for_profile(
    profile_routes: pd.DataFrame,
    *,
    selected_annulus_missing_columns: list[str],
) -> bool:
    if selected_annulus_missing_columns:
        return False
    return bool(_selected_annulus_valid_rows(profile_routes).any())


def _selected_annulus_valid_rows(profile_routes: pd.DataFrame) -> pd.Series:
    rate = pd.to_numeric(
        profile_routes["weighted_selected_detector_mode_annulus_detection_rate"],
        errors="coerce",
    )
    fraction = pd.to_numeric(
        profile_routes["weighted_selected_detector_mode_annulus_fraction"],
        errors="coerce",
    )
    return rate.notna() & fraction.notna() & fraction.gt(0.0)


def _selected_annulus_lens_status(
    selected_annulus_available: bool,
    *,
    selected_annulus_missing_columns: list[str],
) -> str:
    if selected_annulus_available:
        return "selected_annulus_parallel_lens_v1"
    if selected_annulus_missing_columns:
        return "missing_selected_annulus_columns_rerun_ev_panel_required"
    return "selected_annulus_columns_empty_or_non_numeric"


def _max_or_none(values: pd.Series) -> float | None:
    numeric = pd.to_numeric(values, errors="coerce")
    if numeric.notna().any():
        return float(numeric.max())
    return None


def _top_route_set(df: pd.DataFrame, sort_cols: list[str], route_cols: list[str]) -> set[tuple[int, int, int]]:
    if df.empty or any(col not in df for col in sort_cols):
        return set()
    ranked = df.sort_values(sort_cols, ascending=False).head(3)
    return {
        (int(row.wavelength_nm), int(row.width_nm), int(row.depth_nm))
        for row in ranked.itertuples(index=False)
    }


def _route_rank(df: pd.DataFrame, *, route: tuple[int, int, int], sort_cols: list[str]) -> int | None:
    if df.empty or any(col not in df for col in sort_cols):
        return None
    ranked = df.sort_values(sort_cols, ascending=False).reset_index(drop=True)
    matches = ranked[
        (ranked["wavelength_nm"] == route[0])
        & (ranked["width_nm"] == route[1])
        & (ranked["depth_nm"] == route[2])
    ]
    if matches.empty:
        return None
    return int(matches.index[0]) + 1


def determine_full_grid_decision(output_dir: Path) -> dict[str, Any]:
    feasible_path = output_dir / "feasible_scenarios_v1.csv"
    ranking_path = output_dir / "ev_ranking_comparison_v1.csv"
    if not feasible_path.exists():
        return {
            "full_grid_decision": "no_go_missing_feasible_scenarios",
            "full_grid_allowed": False,
            "blockers": ["feasible_scenarios_v1_missing"],
        }
    feasible = pd.read_csv(feasible_path)
    feasible_single = feasible[
        (feasible["scenario_kind"] == "nodi_single")
        & feasible["scenario_config_feasible"].astype(bool)
    ]
    blockers: list[str] = []
    if feasible_single.empty:
        blockers.append("no_feasible_gold_blank_scenario")
    weak_dominate = False
    ranking_change = False
    if ranking_path.exists():
        ranking = pd.read_csv(ranking_path)
        ranking_change = int(ranking.get("top3_changed", pd.Series(dtype=bool)).sum()) >= 2
        for value in ranking.get("new_top3_routes", pd.Series(dtype=str)).dropna().astype(str):
            if str(list(WEAK_REFERENCE_CONTROL)) in value or str(tuple(WEAK_REFERENCE_CONTROL)) in value:
                weak_dominate = True
    else:
        blockers.append("ev_ranking_comparison_missing")
    if not ranking_change:
        blockers.append("candidate_ranking_change_not_demonstrated")
    if weak_dominate:
        blockers.append("weak_reference_control_dominates_recommendation")
    allowed = not blockers
    if allowed:
        decision = "go_full_grid"
    elif "no_feasible_gold_blank_scenario" in blockers:
        decision = "no_go_no_feasible_gold_blank_scenario"
    else:
        decision = "no_go_targeted_report_sufficient"
    return {
        "full_grid_decision": decision,
        "full_grid_allowed": allowed,
        "blockers": blockers,
        "scenario_config_feasible_count": int(
            feasible_single["scenario_config_id"].nunique() if not feasible_single.empty else 0
        ),
        "ranking_change": bool(ranking_change),
        "weak_reference_dominates": bool(weak_dominate),
    }


def run_write_report(output_dir: Path) -> None:
    ensure_output_dir(output_dir)
    decision = determine_full_grid_decision(output_dir)
    baseline = _load_json(output_dir / "gate_only_existing_report_v1.json")
    gold_smoke = _load_json(output_dir / "gold_targeted_sweep_smoke_v1_meta.json")
    gold_final = _load_json(output_dir / "gold_targeted_sweep_final_v1_meta.json")
    blank = _load_json(output_dir / "blank_fpr_sweep_v1_meta.json")
    feasible_summary: list[dict[str, Any]] = []
    feasible_path = output_dir / "feasible_scenarios_v1.json"
    if feasible_path.exists():
        feasible_payload = _load_json(feasible_path)
        feasible_summary = feasible_payload.get("scenario_status", [])
    ranking_payload = _load_json(output_dir / "ev_ranking_comparison_v1.json")
    ranking_rows = ranking_payload.get("rows", [])
    selected_annulus_available_count = sum(
        1
        for row in ranking_rows
        if isinstance(row, dict) and bool(row.get("selected_annulus_lens_available", False))
    )
    selected_annulus_statuses = sorted(
        {
            str(row.get("selected_annulus_lens_status", "missing"))
            for row in ranking_rows
            if isinstance(row, dict)
        }
    )
    lines = [
        "# Tsuyama gold-aligned NODI detection lane report",
        "",
        "## One-page conclusion",
        "",
        f"- full_grid_decision: `{decision['full_grid_decision']}`",
        f"- full_grid_allowed: `{decision['full_grid_allowed']}`",
        f"- blockers: `{', '.join(decision['blockers']) if decision['blockers'] else 'none'}`",
        "",
        "## Method boundary",
        "",
        "- Lane A only: NODI 2022/2024 gold-aligned relative detection lane.",
        "- Lane B POD 2020 is a claim boundary only; it is not used as NODI calibration.",
        "- Synthetic blank, when used, is a guardrail and not empirical blank calibration.",
        "",
        "## Existing gate-only baseline",
        "",
        f"- simulation_status: `{baseline.get('simulation_status', 'missing')}`",
        f"- current_pass_count_total: `{baseline.get('current_pass_count_total', 'missing')}`",
        f"- relaxed10_pass_count_total: `{baseline.get('relaxed10_pass_count_total', 'missing')}`",
        f"- relaxed05_pass_count_total: `{baseline.get('relaxed05_pass_count_total', 'missing')}`",
        "",
        "## Gold targeted sweep",
        "",
        f"- smoke rows: `{gold_smoke.get('rows', 'missing')}`, scenarios: `{gold_smoke.get('scenario_ids', [])}`",
        f"- final rows: `{gold_final.get('rows', 'missing')}`, scenarios: `{gold_final.get('scenario_ids', [])}`",
        "",
        "## Blank FPR guardrail",
        "",
        f"- blank rows/meta rows: `{blank.get('rows', 'missing')}`",
        f"- source blank_summary: `{blank.get('blank_summary', None)}`",
        "",
        "## Feasible scenarios",
        "",
    ]
    if feasible_summary:
        for row in feasible_summary:
            lines.append(
                "- "
                f"{row.get('scenario_config_id')}: "
                f"scenario_config_feasible={row.get('scenario_config_feasible')}, "
                f"feasible_case_count={row.get('feasible_case_count')}, "
                f"paired_diag_pass={row.get('paired_diag_pass')}"
            )
    else:
        lines.append("- missing or empty feasible scenario summary")
    lines.extend(
        [
            "",
            "## EV targeted transfer and ranking",
            "",
            f"- ranking_change_profile_count: `{ranking_payload.get('ranking_change_profile_count', 'missing')}`",
            "- primary ranking lens: `all_crossing_weighted_stable_then_detection`",
            "- selected-annulus ranking lens: "
            "`weighted_selected_detector_mode_annulus_detection_rate_then_stable`",
            "- selected_annulus_lens_available_profile_count: "
            f"`{selected_annulus_available_count}`",
            "- selected_annulus_lens_statuses: "
            f"`{selected_annulus_statuses}`",
            "- selected_annulus_top3_diff_profile_count: "
            f"`{ranking_payload.get('selected_annulus_top3_diff_profile_count', 'missing')}`",
            f"- comparison_support_status: `{ranking_payload.get('comparison_support_status', 'missing')}`",
            "",
            "## Full-grid decision",
            "",
            "Full-grid is not run by this v1 tool. It is allowed only when the targeted lane satisfies the explicit go/no-go gate. Selected-annulus ranking is a parallel analysis lens and does not replace the primary go/no-go gate.",
            "",
            "## Claim boundaries",
            "",
            "- no calibrated SNR",
            "- no absolute LOD",
            "- no absolute EV concentration",
            "- no biological EV specificity",
            "- synthetic blank is not empirical blank calibration",
        ]
    )
    (output_dir / "44_Tsuyama_gold_aligned_detection_lane_report.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return payload if isinstance(payload, dict) else {}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tsuyama gold-aligned NODI detection lane targeted runner."
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("baseline-gate-report")

    manifest = sub.add_parser("build-manifest")
    manifest.add_argument("--dry-run", action="store_true")

    gold = sub.add_parser("sweep-gold")
    gold.add_argument("--stage", choices=["smoke", "final"], required=True)
    gold.add_argument("--workers", type=int, default=8)
    gold.add_argument("--random-seed", type=int, default=42)
    gold.add_argument("--include-paired", action="store_true")

    blank = sub.add_parser("sweep-blank")
    blank.add_argument("--stage", choices=["smoke", "final"], required=True)
    blank.add_argument("--workers", type=int, default=8)
    blank.add_argument("--random-seed", type=int, default=42)
    blank.add_argument("--blank-summary", type=Path, default=None)
    blank.add_argument("--include-paired", action="store_true")

    sub.add_parser("select-feasible")

    ev = sub.add_parser("sweep-ev-panel")
    ev.add_argument("--n-events", type=int, default=10000)
    ev.add_argument("--workers", type=int, default=8)
    ev.add_argument("--random-seed", type=int, default=42)

    sub.add_parser("compare-ranking")
    sub.add_parser("write-report")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir)
    if args.command == "baseline-gate-report":
        run_baseline_gate_report(output_dir)
    elif args.command == "build-manifest":
        run_build_manifest(output_dir, dry_run=bool(args.dry_run))
    elif args.command == "sweep-gold":
        run_sweep_gold(
            output_dir,
            stage=args.stage,
            n_workers=int(args.workers),
            random_seed=int(args.random_seed),
            include_paired=bool(args.include_paired),
        )
    elif args.command == "sweep-blank":
        run_sweep_blank(
            output_dir,
            stage=args.stage,
            n_workers=int(args.workers),
            random_seed=int(args.random_seed),
            blank_summary=args.blank_summary,
            include_paired=bool(args.include_paired),
        )
    elif args.command == "select-feasible":
        run_select_feasible(output_dir)
    elif args.command == "sweep-ev-panel":
        run_sweep_ev_panel(
            output_dir,
            n_events=int(args.n_events),
            n_workers=int(args.workers),
            random_seed=int(args.random_seed),
        )
    elif args.command == "compare-ranking":
        run_compare_ranking(output_dir)
    elif args.command == "write-report":
        run_write_report(output_dir)
    else:
        raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    main()
