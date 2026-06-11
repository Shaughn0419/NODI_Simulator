#!/usr/bin/env python3
# pyright: reportAttributeAccessIssue=false, reportCallIssue=false, reportArgumentType=false, reportGeneralTypeIssues=false
from __future__ import annotations

import argparse
import hashlib
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.config import THETA_GRID_RAD, medium_for_particle, particle_from_name  # noqa: E402
from nodi_simulator.parameter_sweep import (  # noqa: E402
    _estimate_runtime_threshold_stats_1d,
    _resample_traces_for_pulse_extraction,
    add_detector_noise,
    add_post_readout_noise,
    apply_readout_chain,
    build_pulse_extraction_context,
    extract_pulse_features,
    run_single_case_batch,
)
from nodi_simulator.reference_field import compute_reference_field  # noqa: E402
from tools._common import write_json_file  # noqa: E402
from tools.audits import tsuyama_gold_aligned_detection_lane as lane  # noqa: E402
from tools.audits.run_report148_stage1_ab_minimal import (  # noqa: E402
    _build_route_cfg,
    _build_v2_view_payload_overrides,
)
from tools.lens_b_ev_gold_fullgrid_runner import _fixed_660_e_sca_ref, _per_wavelength_e_sca_ref  # noqa: E402


OUTPUT_DIR_DEFAULT = Path("results/audits") / f"report148_scale_shape_diagnostics_{datetime.now().strftime('%Y%m%d')}"
SCALE_FACTORS = (0.5, 1.0, 2.0, 10.0)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _case_cfg(
    *,
    seed: int,
    normalization_view: str,
    detector_route_id: str,
    detector_forward_model: str,
    gauge_mode: str,
) -> tuple[Any, Any]:
    cfg, optical_template = _build_route_cfg(
        n_events=500,
        seed=seed,
        detector_route_id=detector_route_id,
        detector_forward_model=detector_forward_model,
        normalization_lane=normalization_view,
    )
    return cfg, optical_template


def _run_case_with_events(
    *,
    particle_name: str,
    route_key: tuple[int, int, int],
    seed: int,
    normalization_view: str,
) -> dict[str, Any]:
    particle = particle_from_name(particle_name)
    medium = medium_for_particle(particle)
    wavelength_nm, width_nm, depth_nm = route_key
    cfg, optical_template = _case_cfg(
        seed=seed,
        normalization_view=normalization_view,
        detector_route_id="A_hybrid",
        detector_forward_model="joint_overlap_coherent_surrogate",
        gauge_mode="V1_gauge_locked",
    )
    optical = replace(optical_template, wavelength_m=float(wavelength_nm) * 1e-9)
    channel = lane.case_baseline_channel(width_nm, depth_nm)
    if normalization_view == "fixed_660_gold":
        e_sca_ref = _fixed_660_e_sca_ref(
            width_nm=width_nm,
            depth_nm=depth_nm,
            cfg=cfg,
            optical_template=optical_template,
        )
    else:
        e_sca_ref = _per_wavelength_e_sca_ref(
            wavelength_nm=wavelength_nm,
            width_nm=width_nm,
            depth_nm=depth_nm,
            medium=medium,
            cfg=cfg,
            optical_template=optical_template,
        )
    return run_single_case_batch(
        particle=particle,
        medium=medium,
        channel=channel,
        optical=optical,
        sim_cfg=cfg,
        E_sca_ref=e_sca_ref,
        theta_grid_rad=THETA_GRID_RAD,
        retain_event_traces=True,
        stream_summary_only=False,
    )


def evaluate_signal_scale_diagnostic(
    *,
    case_result: dict[str, Any],
    sim_cfg: Any,
    scale_factors: tuple[float, ...] = SCALE_FACTORS,
) -> list[dict[str, Any]]:
    pulse_context_cache: dict[int, Any] = {}
    rows: list[dict[str, Any]] = []
    for scale_factor in scale_factors:
        detected = 0
        stable = 0
        peak_margins: list[float] = []
        for event_idx, event in enumerate(case_result["events"]):
            time_s = np.asarray(event["trajectory"]["time_s"], dtype=float)
            signal = np.asarray(event["signal_trace_default_production"], dtype=float) * float(scale_factor)
            baseline_trace = np.asarray(event["I_baseline_trace"], dtype=float)
            detected_intensity = baseline_trace + signal
            rng = np.random.default_rng(910000 + event_idx)
            noisy = add_detector_noise(
                signal,
                time_s,
                sim_cfg,
                rng,
                detected_intensity=detected_intensity,
                baseline_intensity=float(event["I_baseline"]),
            )
            readout = apply_readout_chain(
                noisy["signal_noisy"],
                time_s,
                sim_cfg,
                transit_time_s=float(event["transit_time_s"]),
                export_full_diagnostics=False,
            )
            if (
                sim_cfg.post_readout_noise_std > 0
                or sim_cfg.post_readout_colored_noise_std > 0
                or sim_cfg.post_readout_drift_slope != 0
            ):
                post = add_post_readout_noise(
                    readout["signal_detect"],
                    time_s,
                    sim_cfg,
                    rng,
                )
                signal_post = np.asarray(post["signal_post_readout"], dtype=float)
            else:
                signal_post = np.asarray(readout["signal_detect"], dtype=float)
            pulse_time_s, pulse_traces, _ = _resample_traces_for_pulse_extraction(
                time_s,
                (signal_post, np.zeros_like(signal_post)),
                sim_cfg,
            )
            pulse_signal = np.asarray(pulse_traces[0], dtype=float)
            context = pulse_context_cache.get(len(pulse_time_s))
            if context is None:
                context = build_pulse_extraction_context(
                    pulse_time_s,
                    sim_cfg.min_peak_width_s,
                    sim_cfg.min_peak_interval_s,
                )
                pulse_context_cache[len(pulse_time_s)] = context
            threshold_stats, _, _ = _estimate_runtime_threshold_stats_1d(pulse_signal, sim_cfg)
            threshold = float(threshold_stats["threshold"])
            robust_std = max(float(threshold_stats["robust_std"]), 1e-15)
            features = extract_pulse_features(
                pulse_time_s,
                pulse_signal,
                threshold,
                sim_cfg.min_peak_width_s,
                sim_cfg.min_peak_interval_s,
                detection_mode=sim_cfg.pulse_detection_mode,
                context=context,
                include_area_prominence=False,
                width_measure_mode=sim_cfg.pulse_width_measure_mode,
                duration_estimation_policy=sim_cfg.pulse_duration_estimation_policy,
            )
            if int(features["n_peaks"]) > 0:
                detected += 1
                margins = [
                    max(float(peak["peak_height"]) - threshold, 0.0) / robust_std
                    for peak in features["peaks"]
                ]
                best_margin = float(max(margins))
                peak_margins.append(best_margin)
                if best_margin >= float(sim_cfg.stable_detection_margin_z_min):
                    stable += 1
        detection_rate = float(detected / max(len(case_result["events"]), 1))
        stable_rate = float(stable / max(len(case_result["events"]), 1))
        rows.append(
            {
                "scale_factor": float(scale_factor),
                "detection_rate": detection_rate,
                "stable_detection_rate": stable_rate,
                "mean_peak_margin_z": (
                    float(np.mean(peak_margins)) if peak_margins else 0.0
                ),
                "noise_std": float(sim_cfg.noise_std),
                "shot_noise_scale": float(sim_cfg.shot_noise_scale),
                "post_readout_noise_std": float(sim_cfg.post_readout_noise_std),
                "scale_invariance_status": (
                    "strict_expected"
                    if float(sim_cfg.noise_std) == 0.0 and float(sim_cfg.post_readout_noise_std) == 0.0
                    else "approximate_expected_absolute_noise_present"
                ),
            }
        )
    return rows


def evaluate_norm_repin_cases() -> list[dict[str, Any]]:
    diagnostics = [
        ("exosome_biomimetic_corona_nominal_100nm", (404, 500, 700), "fixed_660_gold"),
        ("exosome_biomimetic_corona_nominal_100nm", (660, 800, 1300), "per_wavelength_gold"),
        ("gold_20nm", (404, 500, 700), "fixed_660_gold"),
    ]
    rows: list[dict[str, Any]] = []
    for particle_name, route_key, normalization_view in diagnostics:
        particle = particle_from_name(particle_name)
        medium = medium_for_particle(particle)
        wavelength_nm, width_nm, depth_nm = route_key
        cfg, optical_template = _case_cfg(
            seed=11,
            normalization_view=normalization_view,
            detector_route_id="A_hybrid",
            detector_forward_model="joint_overlap_coherent_surrogate",
            gauge_mode="V1_gauge_locked",
        )
        optical = replace(optical_template, wavelength_m=float(wavelength_nm) * 1e-9)
        channel = lane.case_baseline_channel(width_nm, depth_nm)
        if normalization_view == "fixed_660_gold":
            e_sca_ref = _fixed_660_e_sca_ref(
                width_nm=width_nm,
                depth_nm=depth_nm,
                cfg=cfg,
                optical_template=optical_template,
            )
        else:
            e_sca_ref = _per_wavelength_e_sca_ref(
                wavelength_nm=wavelength_nm,
                width_nm=width_nm,
                depth_nm=depth_nm,
                medium=medium,
                cfg=cfg,
                optical_template=optical_template,
            )
        v1_case = run_single_case_batch(
            particle=particle,
            medium=medium,
            channel=channel,
            optical=optical,
            sim_cfg=cfg,
            E_sca_ref=e_sca_ref,
            theta_grid_rad=THETA_GRID_RAD,
            retain_event_traces=False,
            stream_summary_only=True,
        )
        v2_override = _build_v2_view_payload_overrides(
            particle=particle,
            medium=medium,
            channel=channel,
            optical=optical,
            cfg=cfg,
            e_sca_ref=e_sca_ref,
        )
        v1_sca = complex(v1_case["intrinsic"]["E_sca_unit_normalized_complex"])
        v2_sca = complex(v2_override["intrinsic"]["E_sca_unit_normalized_complex"])
        v1_reference = compute_reference_field(
            channel,
            optical,
            cfg,
            medium_refractive_index=float(medium.refractive_index_at(optical.wavelength_m)),
        )
        v1_ref = complex(v1_reference["E_ref_complex"])
        v2_ref = complex(v2_override["reference"]["E_ref_complex"])
        rows.append(
            {
                "particle_name": particle_name,
                "normalization_view": normalization_view,
                "wavelength_nm": wavelength_nm,
                "width_nm": width_nm,
                "depth_nm": depth_nm,
                "v1_sca_abs": abs(v1_sca),
                "v2_sca_abs": abs(v2_sca),
                "sca_abs_delta": abs(abs(v1_sca) - abs(v2_sca)),
                "v1_ref_abs": abs(v1_ref),
                "v2_ref_abs": abs(v2_ref),
                "ref_abs_delta": abs(abs(v1_ref) - abs(v2_ref)),
                "n_ref_raw": float(v2_override["reference"]["n_ref_raw"]),
                "n_sca_raw": float(v2_override["reference"]["n_sca_raw"]),
            }
        )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run report 148 scale-vs-shape diagnostics.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR_DEFAULT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    scale_case = _run_case_with_events(
        particle_name="exosome_biomimetic_corona_nominal_100nm",
        route_key=(404, 500, 700),
        seed=11,
        normalization_view="fixed_660_gold",
    )
    scale_cfg, _ = _case_cfg(
        seed=11,
        normalization_view="fixed_660_gold",
        detector_route_id="A_hybrid",
        detector_forward_model="joint_overlap_coherent_surrogate",
        gauge_mode="V1_gauge_locked",
    )
    scale_rows = evaluate_signal_scale_diagnostic(case_result=scale_case, sim_cfg=scale_cfg)
    scale_df = pd.DataFrame(scale_rows)
    scale_df.to_csv(output_dir / "report148_scale_invariance_diagnostic.csv", index=False)

    repin_rows = evaluate_norm_repin_cases()
    repin_df = pd.DataFrame(repin_rows)
    repin_df.to_csv(output_dir / "report148_v1_v2_norm_repin_diagnostic.csv", index=False)

    summary = {
        "generated_at": _utc_now_iso(),
        "scale_case": {
            "particle_name": "exosome_biomimetic_corona_nominal_100nm",
            "route_key": [404, 500, 700],
            "normalization_view": "fixed_660_gold",
            "seed": 11,
        },
        "scale_factors": list(SCALE_FACTORS),
        "scale_invariance_detection_rate_span": float(
            scale_df["detection_rate"].max() - scale_df["detection_rate"].min()
        ),
        "scale_invariance_margin_span": float(
            scale_df["mean_peak_margin_z"].max() - scale_df["mean_peak_margin_z"].min()
        ),
        "norm_repin_max_sca_abs_delta": float(repin_df["sca_abs_delta"].max()),
        "norm_repin_max_ref_abs_delta": float(repin_df["ref_abs_delta"].max()),
    }
    write_json_file(output_dir / "report148_scale_shape_summary.json", summary)


if __name__ == "__main__":
    main()
