#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.backend import CURRENT_SCHEMA_VERSION
from dashboard.safe_pickle import dump_dashboard_pickle
from nodi_simulator.utils import (
    classify_design_recommendation,
    classify_engineering_gate_explanation,
)
from tools._common import write_json_file


DEFAULT_STAGE_B7_DIR = (
    PROJECT_ROOT
    / "results"
    / "stage_b7_fixed660_tau1ms_ev_gold_fullgrid_1000e_seed42_22worker_restart_20260515"
)
DEFAULT_PREFIX = "lens_b_fixed660_tau1ms_ev_gold_fullgrid_1000e_seed42"
REFERENCE_USEFUL_BAND = "electronics_noise_limited_useful"
RECOMMENDATION_WAVELENGTHS_NM = {404, 660}


def _normalize(series: pd.Series, *, inverse: bool = False) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").astype(float)
    finite = np.isfinite(values)
    out = pd.Series(0.0, index=series.index, dtype=float)
    if not bool(finite.any()):
        return out
    lo = float(values[finite].min())
    hi = float(values[finite].max())
    if math.isclose(lo, hi):
        out.loc[finite] = 1.0
        return out
    scaled = (values - lo) / (hi - lo)
    if inverse:
        scaled = 1.0 - scaled
    out.loc[finite] = scaled.loc[finite].clip(0.0, 1.0)
    return out


def _freeze_status(row: pd.Series) -> str:
    material = str(row.get("particle_material", ""))
    wavelength_nm = int(row.get("wavelength_nm", 0))
    gate_passed = bool(row.get("engineering_gate_passed", False))
    within_envelope = str(row.get("rho_physical_envelope_status", "")) == "within_envelope"
    reference_useful = str(row.get("reference_operating_band", "")) == REFERENCE_USEFUL_BAND

    if material != "exosome":
        return "diagnostic_anchor_only"
    if gate_passed and within_envelope and reference_useful and wavelength_nm in RECOMMENDATION_WAVELENGTHS_NM:
        return "default_ready_for_result_freeze"
    if gate_passed and within_envelope:
        return "caution_probe_before_result_freeze"
    return "review_required_before_result_freeze"


def _add_dashboard_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    numeric_columns = [
        "particle_diameter_nm",
        "wavelength_nm",
        "width_nm",
        "depth_nm",
        "n_events",
        "n_detected",
        "random_seed",
        "detection_rate",
        "detection_rate_wilson_lb",
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
        "phase_flip_fraction",
        "score",
        "final_engineering_score",
        "A_ref",
        "g_ref",
        "E_sca_normalized",
    ]
    for column in numeric_columns:
        if column in out.columns:
            out[column] = pd.to_numeric(out[column], errors="coerce")

    out["wavelength_m"] = out["wavelength_nm"].astype(float) * 1e-9
    out["width_m"] = out["width_nm"].astype(float) * 1e-9
    out["depth_m"] = out["depth_nm"].astype(float) * 1e-9
    out["engineering_score"] = pd.to_numeric(
        out.get("engineering_score", out["final_engineering_score"]),
        errors="coerce",
    ).fillna(out["final_engineering_score"])
    out["robust_score"] = (
        out["stable_detection_rate"].fillna(0.0)
        * np.maximum(out["mean_peak_margin_z"].fillna(0.0), 0.0)
    )
    out["engineering_gate_passed"] = out["engineering_gate_passed"].astype(bool)
    out["engineering_gate_failed_count"] = np.where(out["engineering_gate_passed"], 0, 1)
    out["engineering_gate_reason"] = np.where(
        out["engineering_gate_passed"],
        "passed",
        out["engineering_gate_primary_blocker"].fillna("gate_blocked"),
    )
    explanations = out.apply(
        lambda row: classify_engineering_gate_explanation(
            engineering_gate_passed=bool(row["engineering_gate_passed"]),
            engineering_gate_reason=str(row["engineering_gate_reason"]),
            engineering_gate_failed_count=int(row["engineering_gate_failed_count"]),
        ),
        axis=1,
        result_type="expand",
    )
    for column in explanations.columns:
        out[column] = explanations[column]

    out["observation_freeze_status"] = out.apply(_freeze_status, axis=1)
    out["observation_freeze_guidance"] = np.select(
        [
            out["observation_freeze_status"].eq("default_ready_for_result_freeze"),
            out["observation_freeze_status"].eq("caution_probe_before_result_freeze"),
            out["observation_freeze_status"].eq("diagnostic_anchor_only"),
        ],
        [
            "Lens B Stage B7 recommendation-eligible EV row.",
            "Lens B Stage B7 control or caution EV row.",
            "Gold anchor diagnostic only; not an EV recommendation row.",
        ],
        default="Review before promoting this row to a frozen recommendation.",
    )
    recommendations = out.apply(
        lambda row: classify_design_recommendation(
            engineering_gate_passed=bool(row["engineering_gate_passed"]),
            observation_freeze_status=str(row["observation_freeze_status"]),
        ),
        axis=1,
        result_type="expand",
    )
    for column in recommendations.columns:
        out[column] = recommendations[column]

    out["paired_detection_rate"] = out.get(
        "paired_detection_rate",
        out.get("paired_channel_detection_rate", np.nan),
    )
    out["engineering_basis_detection_rate"] = out[
        "selected_detector_mode_annulus_detection_rate"
    ].fillna(out["detection_rate"])
    out["engineering_basis_stable_detection_rate"] = out["stable_detection_rate"]
    out["engineering_basis_stable_detection_rate_wilson_lb"] = out[
        "stable_detection_rate_wilson_lb"
    ]
    out["engineering_basis_phase_flip_fraction_wilson_ub"] = out["phase_flip_fraction"]
    out["engineering_basis_mean_peak_margin_z"] = out["mean_peak_margin_z"]
    out["engineering_gate_required_detected_events"] = 1
    out["engineering_gate_detected_fraction_lb"] = out["detection_rate_wilson_lb"]
    out["engineering_gate_stable_detection_rate_lb"] = out["stable_detection_rate_wilson_lb"]
    out["engineering_gate_phase_flip_fraction_ub"] = out["phase_flip_fraction"]
    out["engineering_gate_mean_peak_margin_z"] = out["mean_peak_margin_z"]
    out["engineering_gate_strict_paired_rate_lb"] = out.get(
        "selected_detector_mode_annulus_detection_rate_wilson_lb",
        out["detection_rate_wilson_lb"],
    )
    out["engineering_gate_required_strict_paired_detection_rate"] = 0.0

    local_snr = pd.to_numeric(out["mean_local_snr"], errors="coerce").astype(float)
    out["CV"] = (1.0 / local_snr.replace(0.0, np.nan)).replace([np.inf, -np.inf], np.nan)
    out["CV"] = out["CV"].fillna(out["CV"].median()).fillna(1.0)
    out["std_peak_height"] = out["mean_peak_height"].fillna(0.0) * out["CV"]
    out["robust_cv_peak_height"] = out["CV"]
    out["mean_peak_to_threshold_ratio"] = out["mean_peak_margin_z"]
    out["H_norm"] = _normalize(out["mean_peak_height"])
    out["R_norm"] = _normalize(out["detection_rate"])
    out["CV_norm"] = _normalize(out["CV"], inverse=False)
    out["stable_rate_norm"] = _normalize(out["stable_detection_rate"])
    out["threshold_margin_norm"] = _normalize(out["mean_peak_margin_z"])
    out["local_snr_norm"] = _normalize(out["mean_local_snr"])
    out["auc_norm"] = 0.0
    out["hit_rate_norm"] = _normalize(out["detection_rate"])
    out["d_prime_norm"] = _normalize(out["mean_peak_margin_z"])
    return out


def _compact_record(row: pd.Series) -> dict[str, Any]:
    summary_keys = [
        "n_events",
        "n_detected",
        "detection_rate",
        "detection_rate_wilson_lb",
        "stable_detection_rate",
        "stable_detection_rate_wilson_lb",
        "single_channel_detection_rate",
        "paired_channel_detection_rate",
        "paired_detection_rate",
        "selected_detector_mode_annulus_detection_rate",
        "selected_detector_mode_annulus_detection_rate_wilson_lb",
        "mean_peak_height",
        "std_peak_height",
        "mean_peak_width_s",
        "mean_peak_margin_z",
        "mean_local_snr",
        "mean_transit_time_ms",
        "mean_nodi_transit_bandwidth_gain",
        "phase_flip_fraction",
        "rho_physical_envelope_status",
        "observation_freeze_status",
        "observation_freeze_guidance",
        "engineering_gate_required_detected_events",
        "engineering_gate_detected_fraction_lb",
        "engineering_gate_stable_detection_rate_lb",
        "engineering_gate_phase_flip_fraction_ub",
        "engineering_gate_mean_peak_margin_z",
        "engineering_gate_strict_paired_rate_lb",
        "engineering_gate_required_strict_paired_detection_rate",
    ]
    physics_keys = [
        "A_ref",
        "g_ref",
        "E_sca_normalized",
        "reference_operating_band",
        "rho_physical_envelope_status",
        "na_cutoff_active",
        "readout_preset",
        "readout_observable_mode",
        "normalization_lane",
        "normalization_mode",
        "normalization_reference_wavelength_nm",
        "normalization_reference_particle",
    ]
    summary = {key: row.get(key) for key in summary_keys if key in row}
    summary["all_heights"] = []
    summary["all_widths"] = []
    physics = {key: row.get(key) for key in physics_keys if key in row}
    physics["E_sca_at_det"] = row.get("E_sca_normalized")
    physics["E_sca_ref"] = 1.0
    record = {
        "particle_name": row["particle_name"],
        "particle_material": row["particle_material"],
        "particle_diameter_nm": row["particle_diameter_nm"],
        "wavelength_m": row["wavelength_m"],
        "width_m": row["width_m"],
        "depth_m": row["depth_m"],
        "summary": summary,
        "physics": physics,
    }
    for key in [
        "score",
        "final_engineering_score",
        "engineering_score",
        "robust_score",
        "engineering_gate_passed",
        "engineering_gate_failed_count",
        "engineering_gate_reason",
        "engineering_gate_status_label",
        "engineering_gate_primary_blocker",
        "engineering_gate_primary_blocker_label",
        "engineering_gate_blocker_summary",
        "engineering_gate_guidance",
        "design_recommendation_status",
        "design_recommendation_label",
        "design_recommendation_rank",
        "design_recommendation_guidance",
        "H_norm",
        "R_norm",
        "CV_norm",
        "stable_rate_norm",
        "threshold_margin_norm",
        "local_snr_norm",
        "auc_norm",
        "hit_rate_norm",
        "d_prime_norm",
    ]:
        record[key] = row.get(key)
    return record


def _build_meta(df: pd.DataFrame, *, source_dir: Path, input_csv: Path, prefix: str) -> dict[str, Any]:
    particle_models = (
        df[["particle_name", "particle_material", "particle_diameter_nm"]]
        .drop_duplicates()
        .sort_values(["particle_material", "particle_diameter_nm", "particle_name"])
        .to_dict("records")
    )
    run_manifest_path = source_dir / "run_manifest.json"
    run_summary_path = source_dir / "seed_42_run_summary.json"
    run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8")) if run_manifest_path.exists() else {}
    run_summary = json.loads(run_summary_path.read_text(encoding="utf-8")) if run_summary_path.exists() else {}
    return {
        "dashboard_schema_version": CURRENT_SCHEMA_VERSION,
        "grid": "lens_b_fixed660_tau1ms_stage_b7_fullgrid",
        "config_tag": "fixed660_tau1ms_ev_gold_1000e_seed42",
        "data_prefix": prefix,
        "particle_profile": "lens_b_ev_gold_full_range",
        "source_stage": "stage_b7_fixed660_tau1ms_ev_gold_fullgrid",
        "source_raw_csv": str(input_csv.relative_to(PROJECT_ROOT)),
        "source_run_manifest": str(run_manifest_path.relative_to(PROJECT_ROOT)) if run_manifest_path.exists() else None,
        "n_cases": int(len(df)),
        "n_events_per_case": int(pd.to_numeric(df["n_events"], errors="coerce").dropna().iloc[0]),
        "random_seed_values": sorted(pd.to_numeric(df["random_seed"], errors="coerce").dropna().astype(int).unique().tolist()),
        "wavelengths_nm": sorted(pd.to_numeric(df["wavelength_nm"], errors="coerce").dropna().astype(int).unique().tolist()),
        "widths_nm": sorted(pd.to_numeric(df["width_nm"], errors="coerce").dropna().astype(int).unique().tolist()),
        "depths_nm": sorted(pd.to_numeric(df["depth_nm"], errors="coerce").dropna().astype(int).unique().tolist()),
        "particle_models": particle_models,
        "run_manifest_digest": run_manifest.get("source_summary_sha256") or run_manifest.get("output_sha256"),
        "run_summary": run_summary,
        "dashboard_export_notes": [
            "Exported from the completed Stage B7 Lens B fixed-660/tau-1ms EV+gold full-grid run.",
            "Gold rows are retained for anchor diagnostics only.",
            "EV recommendation rows are limited to 404/660 nm and reference-useful rows.",
            "The dashboard compatibility columns are deterministic projections of the raw Stage B7 table.",
        ],
    }


def export_dashboard_dataset(args: argparse.Namespace) -> None:
    input_csv = Path(args.input_csv).resolve()
    source_dir = Path(args.source_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = str(args.prefix)

    raw = pd.read_csv(input_csv, low_memory=False)
    df = _add_dashboard_columns(raw)

    summary_path = output_dir / f"{prefix}_summary.csv"
    compact_path = output_dir / f"{prefix}_compact.pkl"
    meta_path = output_dir / f"{prefix}_meta.json"
    health_path = output_dir / f"{prefix}_result_health.json"

    df.to_csv(summary_path, index=False)
    with compact_path.open("wb") as handle:
        dump_dashboard_pickle(handle, [_compact_record(row) for _, row in df.iterrows()])
    write_json_file(meta_path, _build_meta(df, source_dir=source_dir, input_csv=input_csv, prefix=prefix))

    from dashboard.precompute import build_result_health_report

    health = build_result_health_report(df)
    health["source_stage"] = "stage_b7_fixed660_tau1ms_ev_gold_fullgrid"
    health["source_raw_csv"] = str(input_csv.relative_to(PROJECT_ROOT))
    write_json_file(health_path, health)

    print(f"wrote {summary_path}")
    print(f"wrote {compact_path}")
    print(f"wrote {meta_path}")
    print(f"wrote {health_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", default=str(DEFAULT_STAGE_B7_DIR))
    parser.add_argument("--input-csv", default=str(DEFAULT_STAGE_B7_DIR / "seed_42_raw_rows.csv"))
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "results"))
    parser.add_argument("--prefix", default=DEFAULT_PREFIX)
    export_dashboard_dataset(parser.parse_args())


if __name__ == "__main__":
    main()
