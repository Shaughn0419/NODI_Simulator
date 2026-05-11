#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from dataclasses import replace
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
for candidate in (str(PROJECT_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from tools.audits import tsuyama_detection_rate_calibration as rate_calib
from tools.audits import tsuyama_gold_aligned_detection_lane as lane
from nodi_simulator.data_objects import PBS_1X
from nodi_simulator.design_claim_governance import (
    CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS,
    PAPER_ALIGNMENT_TARGETS,
    PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1,
    assert_paper_alignment_target_metadata,
    governance_to_jsonable,
    require_claim_level,
    require_paper_alignment_target,
)
from nodi_simulator.intrinsic_scattering import compute_intrinsic_scattering

OUTPUT_DIR = PROJECT_ROOT / "results" / "tsuyama_selected_annulus_joint_fit"
TARGET_SCHEMA_ID = "tsuyama_2022_selected_annulus_joint_fit_v2"
JOINT_FIT_SCORE_INTERPRETATION = (
    "loss_style_sum_of_penalties_lower_is_better"
)
RAW_FILENAME = "selected_annulus_joint_fit_raw_v2.csv"
SUMMARY_FILENAME = "selected_annulus_joint_fit_summary_v2.csv"
META_FILENAME = "selected_annulus_joint_fit_meta_v2.json"
JOINT_CASES: tuple[tuple[int, int, int], ...] = (
    (488, 800, 550),
    (532, 800, 550),
    (660, 800, 550),
    (488, 1200, 550),
    (532, 1200, 550),
    (660, 1200, 550),
)
JOINT_WAVELENGTHS_NM = tuple(dict.fromkeys(wavelength_nm for wavelength_nm, _, _ in JOINT_CASES))
JOINT_GEOMETRIES_NM = tuple(dict.fromkeys((width_nm, depth_nm) for _, width_nm, depth_nm in JOINT_CASES))
GOLD_DIAMETERS_NM = (20, 30, 40, 60)
SILVER_DIAMETERS_NM = (40, 60)
# Guardrail for selected-annulus fit quality: a candidate can be paper-aligned
# only if the annulus subset remains large enough to be interpretable. Keep this
# tied to the annulus sensitivity decision before changing it.
MIN_ANNULUS_FRACTION = 0.25
SELECTED_DETECTOR_MODE_EDGE_NORM_MIN = 0.5
SELECTED_DETECTOR_MODE_EDGE_NORM_MAX = 0.8
MIN_SIGNAL_TRANSFER_GAIN = 0.25
MAX_SIGNAL_TRANSFER_GAIN = 4.0
MIN_SIZE_RESPONSE_EXPONENT_DELTA = -1.5
MAX_SIZE_RESPONSE_EXPONENT_DELTA = 1.5
AU_SIZE_EXPONENT_TARGET = 2.3
AU30_TO_AU20_SNR_RATIO_TARGET = 33.0 / 12.0
SIZE_SIGNAL_OBSERVABLES = (
    "peak_height",
    "local_snr",
    "peak_margin_z",
    "peak_height_times_width",
)
DETECTION_RATE_TARGETS: dict[int, dict[str, float]] = {
    20: {"low": 0.15, "target": 0.30, "high": 0.45},
    30: {"low": 0.45, "target": 0.60, "high": 0.75},
    40: {"low": 0.65, "target": 0.78, "high": 0.90},
    60: {"low": 0.85, "target": 0.92, "high": 0.98},
}
TABLE_S1_SCATTERING_CROSS_SECTION: dict[str, dict[int, float]] = {
    "gold": {488: 0.20, 532: 0.46, 660: 0.10},
    "silver": {488: 0.72, 532: 0.37, 660: 0.07},
}
SIGNAL_RATIO_TARGET_MODES = (
    "interferometric_column_ratio",
    "sqrt_scattering_column_ratio",
    "recomputed_mie_sqrt_csca_ratio",
)
DEFAULT_SIGNAL_RATIO_TARGET_MODE = "interferometric_column_ratio"
DEFAULT_JOINT_CANDIDATES = (
    "baseline_current_estimates",
    "velocity_0p15mmps_low_noise_stack_fluxmix_0p10",
    "velocity_0p15mmps_low_noise_stack_uniform_accessible",
    "low_noise_stack_uniform_accessible",
    "logger_0p5ms_blank_edge_low_noise_stack_fluxmix_0p25",
    "velocity_0p15mmps_fluxmix_0p10_flowparabolic_rho_0p45_noise_0p008",
)


@lru_cache(maxsize=16)
def recomputed_table_s1_csca_m2(material_key: str, wavelength_nm: int) -> float:
    particle = lane.make_tsuyama_2022_table_s1_particle(
        material_key,
        40,
        int(wavelength_nm),
    )
    theta_grid = np.linspace(0.0, np.pi, 361)
    intrinsic = compute_intrinsic_scattering(
        particle,
        PBS_1X,
        float(wavelength_nm) * 1e-9,
        theta_grid,
    )
    return float(intrinsic["Csca_m2"])


def table_s1_signal_ratio_target(wavelength_nm: int, target_mode: str) -> float:
    wavelength = int(wavelength_nm)
    if target_mode == "interferometric_column_ratio":
        return float(
            lane.TSUYAMA_2022_TABLE_S1_INTERFEROMETRIC_SCATTERING["silver"][wavelength]
            / lane.TSUYAMA_2022_TABLE_S1_INTERFEROMETRIC_SCATTERING["gold"][wavelength]
        )
    if target_mode == "sqrt_scattering_column_ratio":
        return float(
            np.sqrt(
                TABLE_S1_SCATTERING_CROSS_SECTION["silver"][wavelength]
                / TABLE_S1_SCATTERING_CROSS_SECTION["gold"][wavelength]
            )
        )
    if target_mode == "recomputed_mie_sqrt_csca_ratio":
        return float(
            np.sqrt(
                recomputed_table_s1_csca_m2("silver", wavelength)
                / recomputed_table_s1_csca_m2("gold", wavelength)
            )
        )
    raise ValueError(f"Unknown Table S1 signal-ratio target mode: {target_mode}")


def table_s1_signal_ratio_targets(wavelength_nm: int) -> dict[str, float]:
    return {
        mode: table_s1_signal_ratio_target(wavelength_nm, mode)
        for mode in SIGNAL_RATIO_TARGET_MODES
    }
JOINT_EXTRA_CFG_OVERRIDES: dict[str, dict[str, Any]] = {
    "paper_10sigma": {},
    "paper_5sigma_sensitivity": {"threshold_sigma": 5.0},
    "paper_refphase_flat": {"reference_spatial_phase_strength_rad": 0.0},
    "paper_refphase_wide": {"reference_spatial_phase_strength_rad": 1.2},
    "paper_inphase_absolute": {
        "readout_observable_mode": "in_phase",
        "pulse_detection_mode": "absolute",
    },
    "paper_signal_transfer_fit": {},
    "paper_5sigma_signal_transfer_fit": {"threshold_sigma": 5.0},
    "paper_5sigma_size_response_fit": {"threshold_sigma": 5.0},
    "paper_signal_size_transfer_fit": {},
    "paper_5sigma_signal_size_transfer_fit": {"threshold_sigma": 5.0},
    "paper_inphase_signal_transfer_fit": {
        "readout_observable_mode": "in_phase",
        "pulse_detection_mode": "absolute",
    },
}
PAPER_TARGET_INCOMPATIBLE_JOINT_VARIANTS = {
    "paper_inphase_absolute",
    "paper_inphase_signal_transfer_fit",
}
PAPER_TARGET_COMPATIBLE_JOINT_VARIANTS = tuple(
    variant_id
    for variant_id in JOINT_EXTRA_CFG_OVERRIDES
    if variant_id not in PAPER_TARGET_INCOMPATIBLE_JOINT_VARIANTS
)
JOINT_SIGNAL_TRANSFER_MODES: dict[str, str] = {
    "paper_signal_transfer_fit": "fit_required_silver_by_wavelength",
    "paper_5sigma_signal_transfer_fit": "fit_required_silver_by_wavelength",
    "paper_signal_size_transfer_fit": "fit_required_silver_by_wavelength",
    "paper_5sigma_signal_size_transfer_fit": "fit_required_silver_by_wavelength",
    "paper_inphase_signal_transfer_fit": "fit_required_silver_by_wavelength",
}
JOINT_SIZE_RESPONSE_MODES: dict[str, str] = {
    "paper_5sigma_size_response_fit": "fit_required_au_power_law",
    "paper_signal_size_transfer_fit": "fit_required_au_power_law",
    "paper_5sigma_signal_size_transfer_fit": "fit_required_au_power_law",
}


@dataclass(frozen=True)
class JointFitCandidate:
    candidate_id: str
    base_candidate_id: str
    cfg_overrides: dict[str, Any]
    rationale: str
    signal_transfer_mode: str = "none"
    size_response_mode: str = "none"


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _case_key(wavelength_nm: int, width_nm: int, depth_nm: int) -> str:
    return f"{int(wavelength_nm)}_{int(width_nm)}x{int(depth_nm)}"


def _geometry_key(width_nm: int, depth_nm: int) -> str:
    return f"{int(width_nm)}x{int(depth_nm)}"


def _make_joint_candidate(
    base_candidate_id: str,
    variant_id: str,
    *,
    cfg_overrides: dict[str, Any] | None = None,
) -> JointFitCandidate:
    base = rate_calib.candidate_by_id()[base_candidate_id]
    overrides = dict(cfg_overrides or {})
    suffix = "" if variant_id == "paper_10sigma" else f"__{variant_id}"
    return JointFitCandidate(
        candidate_id=f"{base_candidate_id}{suffix}",
        base_candidate_id=base_candidate_id,
        cfg_overrides=overrides,
        rationale=f"{base.rationale} Joint selected-annulus variant: {variant_id}.",
        signal_transfer_mode=JOINT_SIGNAL_TRANSFER_MODES.get(variant_id, "none"),
        size_response_mode=JOINT_SIZE_RESPONSE_MODES.get(variant_id, "none"),
    )


def build_joint_candidates(
    *,
    base_candidate_ids: list[str] | None = None,
    variant_ids: list[str] | None = None,
) -> list[JointFitCandidate]:
    catalog = rate_calib.candidate_by_id()
    selected_base_ids = base_candidate_ids or list(DEFAULT_JOINT_CANDIDATES)
    selected_variant_ids = variant_ids or ["paper_10sigma"]
    candidates: list[JointFitCandidate] = []
    for base_id in selected_base_ids:
        if base_id not in catalog:
            raise ValueError(f"Unknown base candidate ID: {base_id}")
        for variant_id in selected_variant_ids:
            if variant_id not in JOINT_EXTRA_CFG_OVERRIDES:
                raise ValueError(f"Unknown joint variant ID: {variant_id}")
            if variant_id in PAPER_TARGET_INCOMPATIBLE_JOINT_VARIANTS:
                raise ValueError(
                    f"Joint variant ID {variant_id!r} is diagnostic-only and "
                    "incompatible with the tsuyama_2022_nodi_table_s1 paper "
                    "target metadata guard. Paper-aligned joint fit requires "
                    'readout_observable_mode="magnitude" and '
                    'pulse_detection_mode="positive". Use one of: '
                    f"{', '.join(PAPER_TARGET_COMPATIBLE_JOINT_VARIANTS)}."
                )
            candidates.append(
                _make_joint_candidate(
                    base_id,
                    variant_id,
                    cfg_overrides=JOINT_EXTRA_CFG_OVERRIDES[variant_id],
                )
            )
    return candidates


def build_joint_cfg(
    candidate: JointFitCandidate,
    *,
    n_events: int,
    random_seed: int,
    scenario_id: str,
) -> lane.SimulationConfig:
    base = rate_calib.candidate_by_id()[candidate.base_candidate_id]
    cfg = rate_calib.build_candidate_cfg(
        base,
        n_events=n_events,
        random_seed=random_seed,
        scenario_id=scenario_id,
    )
    if candidate.cfg_overrides:
        cfg = replace(cfg, **candidate.cfg_overrides)
    return replace(cfg, random_seed=int(random_seed))


def run_joint_candidate_sweep(
    candidate: JointFitCandidate,
    *,
    n_events: int,
    random_seed: int,
    n_workers: int,
    scenario_id: str,
    cases: tuple[tuple[int, int, int], ...] = JOINT_CASES,
) -> pd.DataFrame:
    cfg = build_joint_cfg(
        candidate,
        n_events=n_events,
        random_seed=random_seed,
        scenario_id=scenario_id,
    )
    optical_template = rate_calib.build_candidate_optical_template(
        rate_calib.candidate_by_id()[candidate.base_candidate_id]
    )
    frames: list[pd.DataFrame] = []
    for wavelength_nm, width_nm, depth_nm in cases:
        particles = [
            lane.make_tsuyama_2022_table_s1_particle("gold", diameter_nm, wavelength_nm)
            for diameter_nm in GOLD_DIAMETERS_NM
        ]
        particles.extend(
            lane.make_tsuyama_2022_table_s1_particle("silver", diameter_nm, wavelength_nm)
            for diameter_nm in SILVER_DIAMETERS_NM
        )
        results = lane.run_parameter_sweep(
            particle_types=particles,
            medium=lane.WATER,
            width_list_m=np.array([float(width_nm) * 1e-9], dtype=float),
            depth_list_m=np.array([float(depth_nm) * 1e-9], dtype=float),
            wavelength_list_m=np.array([float(wavelength_nm) * 1e-9], dtype=float),
            optical_template=optical_template,
            sim_cfg=cfg,
            theta_grid_rad=lane.THETA_GRID_RAD,
            baseline_particle=lane.make_tsuyama_2022_table_s1_particle(
                "gold",
                40,
                wavelength_nm,
            ),
            baseline_channel=lane.case_baseline_channel(width_nm, depth_nm),
            verbose=False,
            n_workers=n_workers,
        )
        part = lane.flatten_sweep_results(
            results,
            scenario_config_id=scenario_id,
            cfg=cfg,
            n_events=n_events,
            random_seed=random_seed,
            claim_level=require_claim_level(
                CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS
            ),
        )
        part["case_role"] = lane.case_role((wavelength_nm, width_nm, depth_nm))
        frames.append(part)
    raw = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    raw.insert(0, "candidate_id", candidate.candidate_id)
    raw.insert(1, "target_schema_id", TARGET_SCHEMA_ID)
    for record in raw.to_dict(orient="records"):
        assert_paper_alignment_target_metadata(
            PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1,
            record,
        )
    raw["base_candidate_id"] = candidate.base_candidate_id
    raw["joint_cfg_overrides_json"] = _json_dumps(candidate.cfg_overrides)
    raw["joint_signal_transfer_mode"] = candidate.signal_transfer_mode
    raw["joint_size_response_mode"] = candidate.size_response_mode
    raw["joint_candidate_rationale"] = candidate.rationale
    return raw


def _first_row(
    rows: pd.DataFrame,
    *,
    material: str,
    diameter_nm: int,
    wavelength_nm: int,
    width_nm: int | None = None,
    depth_nm: int | None = None,
) -> pd.Series | None:
    sub = rows[
        (rows["particle_material"].astype(str) == material)
        & (rows["particle_diameter_nm"].astype(int) == int(diameter_nm))
        & (rows["wavelength_nm"].astype(int) == int(wavelength_nm))
    ]
    if width_nm is not None and "width_nm" in sub.columns:
        sub = sub[sub["width_nm"].astype(int) == int(width_nm)]
    if depth_nm is not None and "depth_nm" in sub.columns:
        sub = sub[sub["depth_nm"].astype(int) == int(depth_nm)]
    if sub.empty:
        return None
    return sub.iloc[0]


def _row_float(row: pd.Series | None, column: str) -> float:
    if row is None or column not in row:
        return float("nan")
    try:
        return float(row[column])
    except (TypeError, ValueError):
        return float("nan")


def _band_penalty(value: float, *, low: float, target: float, high: float) -> tuple[float, bool]:
    if not np.isfinite(value):
        return 10.0, False
    span = max(high - low, 1e-9)
    if value < low:
        return ((low - value) / span) ** 2 + 0.05 * ((target - value) / span) ** 2, False
    if value > high:
        return ((value - high) / span) ** 2 + 0.05 * ((target - value) / span) ** 2, False
    return 0.05 * ((target - value) / span) ** 2, True


def _log_ratio_penalty(observed: float, target: float) -> float:
    if not np.isfinite(observed) or observed <= 0 or target <= 0:
        return 10.0
    return float(np.log(observed / target) ** 2)


def _slope_from_positive_points(x_values: list[float], y_values: list[float]) -> float:
    x = np.asarray(x_values, dtype=float)
    y = np.asarray(y_values, dtype=float)
    mask = np.isfinite(x) & np.isfinite(y) & (x > 0) & (y > 0)
    if int(mask.sum()) < 2:
        return float("nan")
    slope, _ = np.polyfit(np.log(x[mask]), np.log(y[mask]), 1)
    return float(slope)


def _size_observable_value(
    summary: dict[str, Any],
    *,
    diameter_nm: int,
    case_key: str,
    observable: str,
) -> float:
    if observable == "peak_height":
        return float(summary.get(f"au{diameter_nm}_{case_key}_mean_peak_height", float("nan")))
    if observable == "local_snr":
        return float(summary.get(f"au{diameter_nm}_{case_key}_mean_local_snr", float("nan")))
    if observable == "peak_margin_z":
        return float(summary.get(f"au{diameter_nm}_{case_key}_mean_peak_margin_z", float("nan")))
    if observable == "peak_height_times_width":
        height = float(summary.get(f"au{diameter_nm}_{case_key}_mean_peak_height", float("nan")))
        width_s = float(summary.get(f"au{diameter_nm}_{case_key}_mean_peak_width_s", float("nan")))
        return float(height * width_s) if np.isfinite(height) and np.isfinite(width_s) else float("nan")
    raise ValueError(f"Unknown size signal observable: {observable}")


def summarize_joint_candidate(
    rows: pd.DataFrame,
    candidate: JointFitCandidate,
    *,
    n_events: int,
    random_seed: int,
    n_workers: int,
    scenario_id: str,
) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "candidate_id": candidate.candidate_id,
        "target_schema_id": TARGET_SCHEMA_ID,
        "scenario_config_id": scenario_id,
        "base_candidate_id": candidate.base_candidate_id,
        "joint_cfg_overrides_json": _json_dumps(candidate.cfg_overrides),
        "joint_signal_transfer_mode": candidate.signal_transfer_mode,
        "joint_size_response_mode": candidate.size_response_mode,
        "signal_ratio_target_mode": DEFAULT_SIGNAL_RATIO_TARGET_MODE,
        "joint_candidate_rationale": candidate.rationale,
        "n_events": int(n_events),
        "n_workers": int(n_workers),
        "random_seed": int(random_seed),
    }

    rate_penalties: list[float] = []
    rate_hits: list[bool] = []
    annulus_fractions: list[float] = []
    for wavelength_nm, width_nm, depth_nm in JOINT_CASES:
        case_key = _case_key(wavelength_nm, width_nm, depth_nm)
        previous_rate = -np.inf
        for diameter_nm in GOLD_DIAMETERS_NM:
            row = _first_row(
                rows,
                material="gold",
                diameter_nm=diameter_nm,
                wavelength_nm=wavelength_nm,
                width_nm=width_nm,
                depth_nm=depth_nm,
            )
            rate = _row_float(row, "selected_detector_mode_annulus_detection_rate")
            fraction = _row_float(row, "selected_detector_mode_annulus_fraction")
            peak = _row_float(row, "mean_peak_height")
            peak_width_s = _row_float(row, "mean_peak_width_s")
            peak_margin_z = _row_float(row, "mean_peak_margin_z")
            snr = _row_float(row, "mean_local_snr")
            summary[f"au{diameter_nm}_{case_key}_selected_annulus_rate"] = rate
            summary[f"au{diameter_nm}_{case_key}_selected_annulus_fraction"] = fraction
            summary[f"au{diameter_nm}_{case_key}_mean_peak_height"] = peak
            summary[f"au{diameter_nm}_{case_key}_mean_peak_width_s"] = peak_width_s
            summary[f"au{diameter_nm}_{case_key}_mean_peak_margin_z"] = peak_margin_z
            summary[f"au{diameter_nm}_{case_key}_mean_local_snr"] = snr
            summary[f"au{diameter_nm}_{case_key}_mean_peak_height_times_width"] = (
                float(peak * peak_width_s)
                if np.isfinite(peak) and np.isfinite(peak_width_s)
                else float("nan")
            )
            if (width_nm, depth_nm) == JOINT_GEOMETRIES_NM[0]:
                summary[f"au{diameter_nm}_{wavelength_nm}_selected_annulus_rate"] = rate
                summary[f"au{diameter_nm}_{wavelength_nm}_selected_annulus_fraction"] = fraction
                summary[f"au{diameter_nm}_{wavelength_nm}_mean_peak_height"] = peak
                summary[f"au{diameter_nm}_{wavelength_nm}_mean_peak_width_s"] = peak_width_s
                summary[f"au{diameter_nm}_{wavelength_nm}_mean_peak_margin_z"] = peak_margin_z
                summary[f"au{diameter_nm}_{wavelength_nm}_mean_local_snr"] = snr
            penalty, hit = _band_penalty(rate, **DETECTION_RATE_TARGETS[diameter_nm])
            rate_penalties.append(penalty)
            rate_hits.append(hit)
            if np.isfinite(fraction):
                annulus_fractions.append(fraction)
            if np.isfinite(rate) and previous_rate > rate + 1e-12:
                rate_penalties.append((previous_rate - rate + 0.01) * 5.0)
                rate_hits.append(False)
            if np.isfinite(rate):
                previous_rate = rate

    signal_penalties: list[float] = []
    signal_penalties_by_mode: dict[str, list[float]] = {
        mode: [] for mode in SIGNAL_RATIO_TARGET_MODES
    }
    raw_signal_penalties_by_mode: dict[str, list[float]] = {
        mode: [] for mode in SIGNAL_RATIO_TARGET_MODES
    }
    transfer_gain_penalties: list[float] = []
    transfer_gain_guardrail_penalty = 0.0
    signal_observed_by_wavelength: dict[int, list[tuple[str, float]]] = {
        int(wavelength_nm): [] for wavelength_nm in JOINT_WAVELENGTHS_NM
    }
    for wavelength_nm, width_nm, depth_nm in JOINT_CASES:
        case_key = _case_key(wavelength_nm, width_nm, depth_nm)
        gold40 = _first_row(
            rows,
            material="gold",
            diameter_nm=40,
            wavelength_nm=wavelength_nm,
            width_nm=width_nm,
            depth_nm=depth_nm,
        )
        silver40 = _first_row(
            rows,
            material="silver",
            diameter_nm=40,
            wavelength_nm=wavelength_nm,
            width_nm=width_nm,
            depth_nm=depth_nm,
        )
        observed = _row_float(silver40, "mean_peak_height") / max(
            _row_float(gold40, "mean_peak_height"),
            1e-12,
        )
        summary[f"ag40_to_au40_peak_ratio_{case_key}"] = float(observed)
        if np.isfinite(observed) and observed > 0:
            signal_observed_by_wavelength[int(wavelength_nm)].append((case_key, float(observed)))

    for wavelength_nm in JOINT_WAVELENGTHS_NM:
        observed_values = [observed for _, observed in signal_observed_by_wavelength[int(wavelength_nm)]]
        observed_median = float(np.median(observed_values)) if observed_values else float("nan")
        targets = table_s1_signal_ratio_targets(int(wavelength_nm))
        target = targets[DEFAULT_SIGNAL_RATIO_TARGET_MODE]
        required_gain = (
            float(target / observed_median)
            if np.isfinite(observed_median) and observed_median > 0
            else float("nan")
        )
        applied_gain = (
            required_gain
            if candidate.signal_transfer_mode == "fit_required_silver_by_wavelength"
            else 1.0
        )
        calibrated_median = (
            float(observed_median * applied_gain)
            if np.isfinite(observed_median) and np.isfinite(applied_gain)
            else float("nan")
        )
        summary[f"ag40_to_au40_peak_ratio_{wavelength_nm}"] = observed_median
        summary[f"ag40_to_au40_calibrated_peak_ratio_{wavelength_nm}"] = calibrated_median
        summary[f"ag40_to_au40_target_ratio_{wavelength_nm}"] = float(target)
        for target_mode, target_value in targets.items():
            summary[f"ag40_to_au40_target_ratio_{target_mode}_{wavelength_nm}"] = float(
                target_value
            )
            summary[f"raw_signal_ratio_score_{target_mode}_{wavelength_nm}"] = (
                _log_ratio_penalty(observed_median, target_value)
            )
        summary[f"required_silver_transfer_gain_{wavelength_nm}"] = required_gain
        summary[f"applied_silver_transfer_gain_{wavelength_nm}"] = applied_gain
        for case_key, observed in signal_observed_by_wavelength[int(wavelength_nm)]:
            calibrated_observed = (
                float(observed * applied_gain)
                if np.isfinite(observed) and np.isfinite(applied_gain)
                else float("nan")
            )
            summary[f"ag40_to_au40_calibrated_peak_ratio_{case_key}"] = calibrated_observed
            for target_mode, target_value in targets.items():
                raw_signal_penalties_by_mode[target_mode].append(
                    _log_ratio_penalty(observed, target_value)
                )
                signal_penalties_by_mode[target_mode].append(
                    _log_ratio_penalty(calibrated_observed, target_value)
                )
            signal_penalties.append(_log_ratio_penalty(calibrated_observed, target))
        if candidate.signal_transfer_mode != "none" and np.isfinite(applied_gain) and applied_gain > 0:
            transfer_gain_penalties.append(float(np.log(applied_gain) ** 2))
            if applied_gain < MIN_SIGNAL_TRANSFER_GAIN:
                transfer_gain_guardrail_penalty += (
                    (MIN_SIGNAL_TRANSFER_GAIN / applied_gain - 1.0) ** 2
                )
            if applied_gain > MAX_SIGNAL_TRANSFER_GAIN:
                transfer_gain_guardrail_penalty += (
                    (applied_gain / MAX_SIGNAL_TRANSFER_GAIN - 1.0) ** 2
                )

    observable_case_exponents: dict[str, list[float]] = {
        observable: [] for observable in SIZE_SIGNAL_OBSERVABLES
    }
    observable_geometry_exponents: dict[str, dict[str, list[float]]] = {
        observable: {
            _geometry_key(width_nm, depth_nm): [] for width_nm, depth_nm in JOINT_GEOMETRIES_NM
        }
        for observable in SIZE_SIGNAL_OBSERVABLES
    }
    observable_wavelength_exponents: dict[str, dict[int, list[float]]] = {
        observable: {int(wavelength_nm): [] for wavelength_nm in JOINT_WAVELENGTHS_NM}
        for observable in SIZE_SIGNAL_OBSERVABLES
    }
    geometry_exponents: dict[str, list[float]] = {
        _geometry_key(width_nm, depth_nm): [] for width_nm, depth_nm in JOINT_GEOMETRIES_NM
    }
    wavelength_exponents_by_wavelength: dict[int, list[float]] = {
        int(wavelength_nm): [] for wavelength_nm in JOINT_WAVELENGTHS_NM
    }
    for wavelength_nm, width_nm, depth_nm in JOINT_CASES:
        case_key = _case_key(wavelength_nm, width_nm, depth_nm)
        geometry_key = _geometry_key(width_nm, depth_nm)
        for observable in SIZE_SIGNAL_OBSERVABLES:
            values = [
                _size_observable_value(
                    summary,
                    diameter_nm=diameter_nm,
                    case_key=case_key,
                    observable=observable,
                )
                for diameter_nm in GOLD_DIAMETERS_NM
            ]
            exponent = _slope_from_positive_points(list(GOLD_DIAMETERS_NM), values)
            summary[f"au_size_exponent_{observable}_{case_key}"] = exponent
            if np.isfinite(exponent):
                observable_case_exponents[observable].append(exponent)
                observable_geometry_exponents[observable][geometry_key].append(exponent)
                observable_wavelength_exponents[observable][int(wavelength_nm)].append(exponent)
                if observable == "peak_height":
                    geometry_exponents[geometry_key].append(exponent)
                    wavelength_exponents_by_wavelength[int(wavelength_nm)].append(exponent)
        summary[f"au_size_exponent_{case_key}"] = summary[
            f"au_size_exponent_peak_height_{case_key}"
        ]
    for wavelength_nm, exponents in wavelength_exponents_by_wavelength.items():
        summary[f"au_size_exponent_{wavelength_nm}"] = (
            float(np.median(exponents)) if exponents else float("nan")
        )
    for geometry_key, exponents in geometry_exponents.items():
        summary[f"au_size_exponent_{geometry_key}_median"] = (
            float(np.median(exponents)) if exponents else float("nan")
        )
    observable_medians: dict[str, float] = {}
    for observable in SIZE_SIGNAL_OBSERVABLES:
        exponents = observable_case_exponents[observable]
        median_exponent = float(np.median(exponents)) if exponents else float("nan")
        observable_medians[observable] = median_exponent
        summary[f"au_size_exponent_{observable}_median"] = median_exponent
        for geometry_key, geometry_values in observable_geometry_exponents[observable].items():
            summary[f"au_size_exponent_{observable}_{geometry_key}_median"] = (
                float(np.median(geometry_values)) if geometry_values else float("nan")
            )
    finite_observable_errors: dict[str, float] = {
        observable: abs(float(value) - AU_SIZE_EXPONENT_TARGET)
        for observable, value in observable_medians.items()
        if np.isfinite(value)
    }
    if finite_observable_errors:
        best_observable, _ = min(
            finite_observable_errors.items(),
            key=lambda item: item[1],
        )
    else:
        best_observable = "unavailable"
    raw_size_exponent = observable_medians.get("peak_height", float("nan"))
    required_size_delta = (
        float(AU_SIZE_EXPONENT_TARGET - raw_size_exponent)
        if np.isfinite(raw_size_exponent)
        else float("nan")
    )
    if (
        candidate.size_response_mode == "fit_required_au_power_law"
        and np.isfinite(required_size_delta)
    ):
        applied_size_delta = float(
            np.clip(
                required_size_delta,
                MIN_SIZE_RESPONSE_EXPONENT_DELTA,
                MAX_SIZE_RESPONSE_EXPONENT_DELTA,
            )
        )
    elif candidate.size_response_mode == "fit_required_au_power_law":
        applied_size_delta = float("nan")
    else:
        applied_size_delta = 0.0
    calibrated_size_exponent = (
        float(raw_size_exponent + applied_size_delta)
        if np.isfinite(raw_size_exponent) and np.isfinite(applied_size_delta)
        else float("nan")
    )
    size_response_guardrail_penalty = 0.0
    size_response_regularization_score = 0.0
    if candidate.size_response_mode != "none" and np.isfinite(applied_size_delta):
        size_response_regularization_score = 0.25 * float(applied_size_delta**2)
        if required_size_delta < MIN_SIZE_RESPONSE_EXPONENT_DELTA:
            size_response_guardrail_penalty += (
                (MIN_SIZE_RESPONSE_EXPONENT_DELTA - required_size_delta) ** 2
            )
        if required_size_delta > MAX_SIZE_RESPONSE_EXPONENT_DELTA:
            size_response_guardrail_penalty += (
                (required_size_delta - MAX_SIZE_RESPONSE_EXPONENT_DELTA) ** 2
            )
    size_exponent = calibrated_size_exponent
    size_exponent_score = (
        ((size_exponent - AU_SIZE_EXPONENT_TARGET) / 0.7) ** 2
        if np.isfinite(size_exponent)
        else 10.0
    )
    summary["au_size_exponent_raw_median"] = raw_size_exponent
    summary["au_size_exponent_calibrated_median"] = calibrated_size_exponent
    summary["required_au_size_response_exponent_delta"] = required_size_delta
    summary["applied_au_size_response_exponent_delta"] = applied_size_delta
    summary["size_response_regularization_score"] = size_response_regularization_score
    summary["size_response_guardrail_penalty"] = size_response_guardrail_penalty
    summary["au_size_exponent_median"] = size_exponent
    summary["au_size_exponent_scored_observable"] = "peak_height"
    summary["au_size_exponent_best_observable"] = best_observable
    summary["au_size_exponent_best_observable_error"] = (
        float(finite_observable_errors[best_observable])
        if best_observable in finite_observable_errors
        else float("nan")
    )
    summary["au_size_exponent_diagnostic_status"] = (
        "bounded_power_law_size_response_fit_applied"
        if candidate.size_response_mode == "fit_required_au_power_law"
        and np.isfinite(applied_size_delta)
        and size_response_guardrail_penalty <= 1e-12
        else "size_response_required_delta_outside_guardrail"
        if candidate.size_response_mode == "fit_required_au_power_law"
        and np.isfinite(applied_size_delta)
        else "size_response_fit_unavailable"
        if candidate.size_response_mode == "fit_required_au_power_law"
        else "alternate_observable_closer_to_paper_target"
        if best_observable not in {"unavailable", "peak_height"}
        else "scored_peak_height_is_closest_available_observable"
        if best_observable == "peak_height"
        else "no_finite_size_observable_exponent"
    )

    snr_ratios: list[float] = []
    for wavelength_nm, width_nm, depth_nm in JOINT_CASES:
        case_key = _case_key(wavelength_nm, width_nm, depth_nm)
        snr20 = summary.get(f"au20_{case_key}_mean_local_snr", float("nan"))
        snr30 = summary.get(f"au30_{case_key}_mean_local_snr", float("nan"))
        case_snr_ratio = (
            float(snr30 / snr20)
            if np.isfinite(snr20) and snr20 > 0 and np.isfinite(snr30)
            else float("nan")
        )
        summary[f"au30_to_au20_snr_ratio_{case_key}"] = case_snr_ratio
        if np.isfinite(snr20) and snr20 > 0 and np.isfinite(snr30):
            snr_ratios.append(case_snr_ratio)
    snr_ratio = float(np.median(snr_ratios)) if snr_ratios else float("nan")
    snr_ratio_score = _log_ratio_penalty(snr_ratio, AU30_TO_AU20_SNR_RATIO_TARGET)
    summary["au30_to_au20_snr_ratio_median"] = snr_ratio

    annulus_fraction_min = float(np.min(annulus_fractions)) if annulus_fractions else float("nan")
    annulus_guardrail_penalty = (
        max(0.0, MIN_ANNULUS_FRACTION - annulus_fraction_min) * 20.0
        if np.isfinite(annulus_fraction_min)
        else 10.0
    )
    reference_bad = bool(
        (rows["reference_operating_band"].astype(str) == "reference_too_weak").any()
    )
    rho_bad = bool((rows["rho_physical_envelope_status"].astype(str) != "within_envelope").any())
    na_bad = bool(rows["na_cutoff_active"].astype(bool).any())
    hard_guardrail_penalty = annulus_guardrail_penalty
    if reference_bad:
        hard_guardrail_penalty += 5.0
    if rho_bad:
        hard_guardrail_penalty += 5.0
    if na_bad:
        hard_guardrail_penalty += 5.0

    selected_rate_score = float(np.mean(rate_penalties)) if rate_penalties else 10.0
    signal_ratio_score = float(np.mean(signal_penalties)) if signal_penalties else 10.0
    signal_ratio_scores_by_mode = {
        mode: float(np.mean(values)) if values else 10.0
        for mode, values in signal_penalties_by_mode.items()
    }
    raw_signal_ratio_scores_by_mode = {
        mode: float(np.mean(values)) if values else 10.0
        for mode, values in raw_signal_penalties_by_mode.items()
    }
    transfer_gain_regularization_score = (
        0.25 * float(np.mean(transfer_gain_penalties))
        if transfer_gain_penalties
        else 0.0
    )
    hard_guardrail_penalty += float(transfer_gain_guardrail_penalty)
    hard_guardrail_penalty += float(size_response_guardrail_penalty)
    signal_aligned = signal_ratio_score <= 0.05
    transfer_within_guardrail = transfer_gain_guardrail_penalty <= 1e-12
    size_response_within_guardrail = (
        candidate.size_response_mode == "none" or size_response_guardrail_penalty <= 1e-12
    )

    def joint_score_for_signal(signal_score: float) -> float:
        return (
            selected_rate_score
            + 2.0 * float(signal_score)
            + 0.5 * float(size_exponent_score)
            + 0.5 * float(snr_ratio_score)
            + transfer_gain_regularization_score
            + size_response_regularization_score
            + hard_guardrail_penalty
        )

    joint_fit_score = joint_score_for_signal(signal_ratio_score)
    joint_fit_scores_by_mode = {
        mode: joint_score_for_signal(score)
        for mode, score in signal_ratio_scores_by_mode.items()
    }
    summary.update(
        {
            "joint_fit_score": float(joint_fit_score),
            "joint_fit_score_strict": float(
                joint_fit_scores_by_mode["interferometric_column_ratio"]
            ),
            "joint_fit_score_formula": float(
                joint_fit_scores_by_mode["sqrt_scattering_column_ratio"]
            ),
            "joint_fit_score_recomputed_mie": float(
                joint_fit_scores_by_mode["recomputed_mie_sqrt_csca_ratio"]
            ),
            "joint_fit_score_interpretation": JOINT_FIT_SCORE_INTERPRETATION,
            "selected_rate_score": selected_rate_score,
            "signal_ratio_score": signal_ratio_score,
            "signal_ratio_score_interferometric_column_ratio": float(
                signal_ratio_scores_by_mode["interferometric_column_ratio"]
            ),
            "signal_ratio_score_sqrt_scattering_column_ratio": float(
                signal_ratio_scores_by_mode["sqrt_scattering_column_ratio"]
            ),
            "signal_ratio_score_recomputed_mie_sqrt_csca_ratio": float(
                signal_ratio_scores_by_mode["recomputed_mie_sqrt_csca_ratio"]
            ),
            "raw_signal_ratio_score_interferometric_column_ratio": float(
                raw_signal_ratio_scores_by_mode["interferometric_column_ratio"]
            ),
            "raw_signal_ratio_score_sqrt_scattering_column_ratio": float(
                raw_signal_ratio_scores_by_mode["sqrt_scattering_column_ratio"]
            ),
            "raw_signal_ratio_score_recomputed_mie_sqrt_csca_ratio": float(
                raw_signal_ratio_scores_by_mode["recomputed_mie_sqrt_csca_ratio"]
            ),
            "transfer_gain_regularization_score": transfer_gain_regularization_score,
            "transfer_gain_guardrail_penalty": float(transfer_gain_guardrail_penalty),
            "size_response_regularization_score": float(size_response_regularization_score),
            "size_response_guardrail_penalty": float(size_response_guardrail_penalty),
            "size_exponent_score": float(size_exponent_score),
            "snr_ratio_score": float(snr_ratio_score),
            "hard_guardrail_penalty": float(hard_guardrail_penalty),
            "annulus_fraction_min": annulus_fraction_min,
            "selected_rate_all_bands_hit": bool(all(rate_hits)),
            "reference_bad": reference_bad,
            "rho_bad": rho_bad,
            "na_cutoff_active": na_bad,
            "paper_fit_status": (
                "candidate_joint_fit_with_paper_transfer"
                if signal_aligned
                and candidate.signal_transfer_mode != "none"
                and transfer_within_guardrail
                and size_response_within_guardrail
                else "candidate_fit_guardrail_violation"
                if signal_aligned
                and (
                    not transfer_within_guardrail
                    or not size_response_within_guardrail
                )
                else "candidate_joint_fit_plausible"
                if signal_aligned
                else "candidate_needs_signal_transfer_or_phase_fit"
            ),
        }
    )
    return summary


def run_joint_fit(
    *,
    candidates: list[JointFitCandidate],
    n_events: int,
    random_seed: int,
    n_workers: int,
    scenario_id: str,
    output_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_frames: list[pd.DataFrame] = []
    summary_rows: list[dict[str, Any]] = []
    start = time.time()
    for index, candidate in enumerate(candidates, start=1):
        print(f"[joint-fit] {index}/{len(candidates)} {candidate.candidate_id}", flush=True)
        rows = run_joint_candidate_sweep(
            candidate,
            n_events=n_events,
            random_seed=random_seed,
            n_workers=n_workers,
            scenario_id=scenario_id,
        )
        raw_frames.append(rows)
        summary_rows.append(
            summarize_joint_candidate(
                rows,
                candidate,
                n_events=n_events,
                random_seed=random_seed,
                n_workers=n_workers,
                scenario_id=scenario_id,
            )
    )
    raw = pd.concat(raw_frames, ignore_index=True) if raw_frames else pd.DataFrame()
    for record in raw.to_dict(orient="records"):
        assert_paper_alignment_target_metadata(
            PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1,
            record,
        )
    summary = pd.DataFrame(summary_rows).sort_values(
        ["joint_fit_score", "candidate_id"],
        ignore_index=True,
    )
    raw_path = output_dir / RAW_FILENAME
    summary_path = output_dir / SUMMARY_FILENAME
    raw.to_csv(raw_path, index=False)
    summary.to_csv(summary_path, index=False)
    meta = {
        "schema": TARGET_SCHEMA_ID,
        "analysis_lane": "selected_annulus",
        "claim_level": require_claim_level(
            CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS
        ),
        "paper_alignment_target": require_paper_alignment_target(
            PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1
        ),
        "paper_alignment_target_metadata_status": "validated_per_raw_row",
        "paper_alignment_target_required_metadata_fields": governance_to_jsonable(
            PAPER_ALIGNMENT_TARGETS[
                PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1
            ]["required_metadata_fields"]
        ),
        "selected_annulus_source": "initial_position_edge_norm_annulus",
        "scenario_config_id": scenario_id,
        "cases": [list(case) for case in JOINT_CASES],
        "n_events": int(n_events),
        "n_workers": int(n_workers),
        "random_seed": int(random_seed),
        "candidate_count": int(len(candidates)),
        "raw_rows": int(len(raw)),
        "summary_rows": int(len(summary)),
        "runtime_s": time.time() - start,
        "raw_path": str(raw_path),
        "summary_path": str(summary_path),
        "selected_annulus_edge_norm_min": float(
            raw["selected_detector_mode_annulus_edge_norm_min"].dropna().iloc[0]
            if "selected_detector_mode_annulus_edge_norm_min" in raw
            and raw["selected_detector_mode_annulus_edge_norm_min"].notna().any()
            else SELECTED_DETECTOR_MODE_EDGE_NORM_MIN
        ),
        "selected_annulus_edge_norm_max": float(
            raw["selected_detector_mode_annulus_edge_norm_max"].dropna().iloc[0]
            if "selected_detector_mode_annulus_edge_norm_max" in raw
            and raw["selected_detector_mode_annulus_edge_norm_max"].notna().any()
            else SELECTED_DETECTOR_MODE_EDGE_NORM_MAX
        ),
        "target_notes": {
            "joint_fit_score_interpretation": JOINT_FIT_SCORE_INTERPRETATION,
            "joint_fit_score_components": (
                "selected_rate_score + 2*signal_ratio_score + "
                "0.5*size_exponent_score + 0.5*snr_ratio_score + "
                "transfer_gain_regularization_score + "
                "size_response_regularization_score + hard_guardrail_penalty"
            ),
            "selected_annulus_detection_rate_targets": DETECTION_RATE_TARGETS,
            "signal_ratio_target_mode": DEFAULT_SIGNAL_RATIO_TARGET_MODE,
            "ag_au_peak_ratio_target_modes": {
                str(wavelength_nm): table_s1_signal_ratio_targets(wavelength_nm)
                for wavelength_nm in JOINT_WAVELENGTHS_NM
            },
            "ag_au_peak_ratio_targets": {
                str(wavelength_nm): (
                    lane.TSUYAMA_2022_TABLE_S1_INTERFEROMETRIC_SCATTERING["silver"][
                        wavelength_nm
                    ]
                    / lane.TSUYAMA_2022_TABLE_S1_INTERFEROMETRIC_SCATTERING["gold"][
                        wavelength_nm
                    ]
                )
                for wavelength_nm in JOINT_WAVELENGTHS_NM
            },
            "au_size_exponent_target": AU_SIZE_EXPONENT_TARGET,
            "au30_to_au20_snr_ratio_target": AU30_TO_AU20_SNR_RATIO_TARGET,
            "minimum_annulus_fraction": MIN_ANNULUS_FRACTION,
            "signal_transfer_gain_bounds": {
                "min": MIN_SIGNAL_TRANSFER_GAIN,
                "max": MAX_SIGNAL_TRANSFER_GAIN,
            },
            "size_response_exponent_delta_bounds": {
                "min": MIN_SIZE_RESPONSE_EXPONENT_DELTA,
                "max": MAX_SIZE_RESPONSE_EXPONENT_DELTA,
            },
        },
    }
    rate_calib.write_json(output_dir / META_FILENAME, meta)
    write_report(output_dir, summary=summary, meta=meta)
    return raw, summary, meta


def write_report(output_dir: Path, *, summary: pd.DataFrame, meta: dict[str, Any]) -> Path:
    report_path = output_dir / "selected_annulus_joint_fit_report.md"
    top_cols = [
        "candidate_id",
        "joint_fit_score",
        "joint_fit_score_strict",
        "joint_fit_score_formula",
        "joint_fit_score_recomputed_mie",
        "selected_rate_score",
        "signal_ratio_score",
        "signal_ratio_score_sqrt_scattering_column_ratio",
        "raw_signal_ratio_score_sqrt_scattering_column_ratio",
        "size_exponent_score",
        "snr_ratio_score",
        "transfer_gain_regularization_score",
        "transfer_gain_guardrail_penalty",
        "size_response_regularization_score",
        "size_response_guardrail_penalty",
        "paper_fit_status",
        "joint_signal_transfer_mode",
        "joint_size_response_mode",
        "au20_660_800x550_selected_annulus_rate",
        "au30_660_800x550_selected_annulus_rate",
        "au40_660_800x550_selected_annulus_rate",
        "au60_660_800x550_selected_annulus_rate",
        "au20_660_1200x550_selected_annulus_rate",
        "au30_660_1200x550_selected_annulus_rate",
        "au40_660_1200x550_selected_annulus_rate",
        "au60_660_1200x550_selected_annulus_rate",
        "ag40_to_au40_peak_ratio_488",
        "ag40_to_au40_peak_ratio_532",
        "ag40_to_au40_peak_ratio_660",
        "ag40_to_au40_calibrated_peak_ratio_488",
        "ag40_to_au40_calibrated_peak_ratio_532",
        "ag40_to_au40_calibrated_peak_ratio_660",
        "required_silver_transfer_gain_488",
        "required_silver_transfer_gain_532",
        "required_silver_transfer_gain_660",
        "applied_silver_transfer_gain_488",
        "applied_silver_transfer_gain_532",
        "applied_silver_transfer_gain_660",
        "au_size_exponent_median",
        "au_size_exponent_raw_median",
        "au_size_exponent_calibrated_median",
        "required_au_size_response_exponent_delta",
        "applied_au_size_response_exponent_delta",
        "au_size_exponent_peak_height_median",
        "au_size_exponent_local_snr_median",
        "au_size_exponent_peak_margin_z_median",
        "au_size_exponent_peak_height_times_width_median",
        "au_size_exponent_800x550_median",
        "au_size_exponent_1200x550_median",
        "au_size_exponent_best_observable",
        "au_size_exponent_diagnostic_status",
        "au30_to_au20_snr_ratio_median",
        "annulus_fraction_min",
        "joint_cfg_overrides_json",
    ]
    top_cols = [column for column in top_cols if column in summary.columns]
    top = summary.head(12)[top_cols] if not summary.empty else pd.DataFrame()
    lines = [
        "# Tsuyama Selected-Annulus Joint Fit",
        "",
        "## Scope",
        "",
        "- This is a paper-fitted selected-annulus calibration lane.",
        "- It does not change global simulator defaults or EV route ranking by itself.",
        "- The score uses 800x550 and 1200x550 selected-annulus detection rates, Ag/Au peak ratios, Au size scaling, and Au30/Au20 SNR ratio.",
        "- Ag/Au transfer-fit variants use one residual transfer gain per wavelength, then score both paper geometries under that same gain.",
        "- Au size-scaling is still scored on peak height, while alternate observables are exported as diagnostics only.",
        "- Size-response fit variants apply a bounded Au power-law correction inside the paper-fit score only.",
        "- `required_silver_transfer_gain_*` reports the residual wavelength/material gain needed to match Table S1 ratios after the simulated trace output.",
        "- Variants ending in `signal_transfer_fit` explicitly apply that residual gain inside the paper-fit score, with a gain regularization and guardrail.",
        "- The transfer-fit variants do not alter simulated detection rates or global material defaults; they only calibrate the paper-fit signal-ratio lens.",
        "",
        "## Run Metadata",
        "",
        f"- schema: `{meta['schema']}`",
        f"- scenario: `{meta['scenario_config_id']}`",
        f"- n_events: `{meta['n_events']}`",
        f"- workers: `{meta['n_workers']}`",
        f"- random_seed: `{meta['random_seed']}`",
        f"- candidates: `{meta['candidate_count']}`",
        "",
        "## Top Candidates",
        "",
        rate_calib.dataframe_to_markdown(top),
        "",
        "## Output Files",
        "",
        f"- `{RAW_FILENAME}`",
        f"- `{SUMMARY_FILENAME}`",
        f"- `{META_FILENAME}`",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def _split_csv_arg(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Joint selected-annulus fit against Tsuyama 2022 detection and signal-ratio conclusions."
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--n-events", type=int, default=1000)
    parser.add_argument("--scenario-id", default="nodi_2022_10sigma_single")
    parser.add_argument(
        "--candidate-ids",
        default="",
        help="Comma-separated base candidate IDs; empty uses a curated default subset.",
    )
    parser.add_argument(
        "--variant-ids",
        default="paper_10sigma",
        help=(
            "Comma-separated paper-target-compatible joint variants. Available: "
            f"{', '.join(PAPER_TARGET_COMPATIBLE_JOINT_VARIANTS)}"
        ),
    )
    parser.add_argument(
        "--list-candidates",
        action="store_true",
        help="Print available curated candidate/variant IDs and exit.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_candidates:
        payload = {
            "default_base_candidate_ids": list(DEFAULT_JOINT_CANDIDATES),
            "paper_target_compatible_variant_ids": list(
                PAPER_TARGET_COMPATIBLE_JOINT_VARIANTS
            ),
            "diagnostic_only_incompatible_variant_ids": sorted(
                PAPER_TARGET_INCOMPATIBLE_JOINT_VARIANTS
            ),
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    base_candidate_ids = _split_csv_arg(args.candidate_ids) or None
    variant_ids = _split_csv_arg(args.variant_ids) or ["paper_10sigma"]
    candidates = build_joint_candidates(
        base_candidate_ids=base_candidate_ids,
        variant_ids=variant_ids,
    )
    run_joint_fit(
        candidates=candidates,
        n_events=args.n_events,
        random_seed=args.random_seed,
        n_workers=args.workers,
        scenario_id=str(args.scenario_id),
        output_dir=Path(args.output_dir),
    )


if __name__ == "__main__":
    main()
