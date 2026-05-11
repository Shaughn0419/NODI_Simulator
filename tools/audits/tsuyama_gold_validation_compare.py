from __future__ import annotations

import argparse
import sys
import time
from copy import deepcopy
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
for candidate in (str(PROJECT_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from nodi_simulator import BASELINE_PARTICLE, WATER, run_parameter_sweep
from nodi_simulator.dashboard.config import (
    DEFAULT_SIM_CFG,
    FULL_SWEEP_WAVELENGTHS_NM,
    OPTICAL_TEMPLATE,
    THETA_GRID_RAD,
    make_particle,
)
from nodi_simulator.data_objects import make_ev_nodi_design_sweep_config
from tools._common import write_json_file


RESULTS_DIR = PROJECT_ROOT / "results"
FULL_SUMMARY_PATH = (
    RESULTS_DIR / "ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv"
)
DEFAULT_OUTPUT_PREFIX = "tsuyama_gold_validation_tau1ms_1000e"

GEOMETRIES_NM = [
    (800, 500),
    (800, 600),
    (1200, 500),
    (1200, 600),
]
WAVELENGTHS_NM = list(FULL_SWEEP_WAVELENGTHS_NM)
DIAMETERS_NM = [20, 30, 40, 50, 60]
DEFAULT_N_EVENTS = 1000
DEFAULT_N_WORKERS = 8
DEFAULT_LOCKIN_TAU_MS = 1.0
DEFAULT_RANDOM_SEED = 42
VALIDATION_PROFILES = {
    "paper_aligned": {
        "readout_observable_mode": "magnitude",
        "engineering_max_phase_flip_fraction": 1.0,
        "description": (
            "Use a phase-insensitive lock-in magnitude readout and keep "
            "phase-flip as a diagnostic rather than a hard gate."
        ),
    },
    "legacy_mainline": {
        "readout_observable_mode": "in_phase",
        "engineering_max_phase_flip_fraction": 0.5,
        "description": (
            "Match the legacy live dashboard defaults for historical "
            "comparison."
        ),
    },
}


def _flatten_results(results: list[dict]) -> pd.DataFrame:
    rows: list[dict] = []
    for result in results:
        summary = dict(result.get("summary", {}))
        reference = dict(result.get("reference", {}))
        intrinsic = dict(result.get("intrinsic", {}))
        particle = result.get("particle")
        diameter_nm = (
            int(round(float(particle.radius_m) * 2e9))
            if particle is not None
            else None
        )
        rows.append(
            {
                "particle_name": result.get("particle_name"),
                "particle_material": "gold",
                "particle_diameter_nm": diameter_nm,
                "wavelength_nm": int(round(float(result["wavelength_m"]) * 1e9)),
                "width_nm": int(round(float(result["width_m"]) * 1e9)),
                "depth_nm": int(round(float(result["depth_m"]) * 1e9)),
                "score": float(result.get("score", 0.0) or 0.0),
                "final_engineering_score": float(
                    result.get("final_engineering_score", result.get("engineering_score", 0.0))
                    or 0.0
                ),
                "engineering_gate_passed": bool(result.get("engineering_gate_passed", False)),
                "design_recommendation_status": result.get("design_recommendation_status"),
                "engineering_gate_primary_blocker": result.get(
                    "engineering_gate_primary_blocker"
                ),
                "detection_rate": float(summary.get("detection_rate", 0.0) or 0.0),
                "stable_detection_rate": float(
                    summary.get("stable_detection_rate", 0.0) or 0.0
                ),
                "single_channel_detection_rate": float(
                    summary.get("single_channel_detection_rate", 0.0) or 0.0
                ),
                "paired_channel_detection_rate": float(
                    summary.get("paired_channel_detection_rate", 0.0) or 0.0
                ),
                "phase_flip_fraction": float(
                    summary.get("phase_flip_fraction", 0.0) or 0.0
                ),
                "mean_peak_height": float(summary.get("mean_peak_height", 0.0) or 0.0),
                "mean_peak_margin_z": float(summary.get("mean_peak_margin_z", 0.0) or 0.0),
                "mean_local_snr": float(summary.get("mean_local_snr", 0.0) or 0.0),
                "mean_transit_time_ms": float(
                    summary.get("mean_transit_time_s", 0.0) or 0.0
                )
                * 1e3,
                "mean_nodi_transit_bandwidth_gain": float(
                    summary.get("mean_nodi_transit_bandwidth_gain", 0.0) or 0.0
                ),
                "mean_nodi_bandwidth_limited_fraction": float(
                    summary.get("mean_nodi_bandwidth_limited_fraction", 0.0) or 0.0
                ),
                "A_ref": float(reference.get("A_ref", 0.0) or 0.0),
                "g_ref": float(reference.get("g_ref", 0.0) or 0.0),
                "E_sca_normalized": float(
                    intrinsic.get("E_sca_unit_normalized", 0.0) or 0.0
                ),
                "Csca_m2": float(intrinsic.get("Csca_m2", 0.0) or 0.0),
                "na_cutoff_active": bool(reference.get("na_cutoff_active", False)),
                "rho_physical_envelope_status": summary.get(
                    "rho_physical_envelope_status"
                ),
            }
        )

    df = pd.DataFrame(rows)
    if df["particle_diameter_nm"].isna().any():
        df["particle_diameter_nm"] = (
            df["particle_name"].str.extract(r"_(\d+)nm").astype(float).fillna(0).astype(int)
        )
    return df


def _spearman_detection(df: pd.DataFrame) -> dict[str, float]:
    metrics = [
        "mean_local_snr",
        "mean_peak_margin_z",
        "E_sca_normalized",
        "A_ref",
        "mean_transit_time_ms",
        "mean_nodi_transit_bandwidth_gain",
    ]
    corr = df[metrics + ["detection_rate"]].corr(method="spearman")["detection_rate"]
    return {metric: float(corr.get(metric, np.nan)) for metric in metrics}


def _aggregate_case_table(df: pd.DataFrame) -> list[dict]:
    records: list[dict] = []
    group_cols = ["wavelength_nm", "width_nm", "depth_nm", "particle_diameter_nm"]
    keep_cols = [
        "detection_rate",
        "stable_detection_rate",
        "mean_peak_height",
        "mean_local_snr",
        "mean_peak_margin_z",
        "mean_transit_time_ms",
        "mean_nodi_transit_bandwidth_gain",
        "A_ref",
        "E_sca_normalized",
        "phase_flip_fraction",
        "final_engineering_score",
    ]
    for keys, sub in df.groupby(group_cols, dropna=False):
        row = {col: float(sub[col].mean()) for col in keep_cols}
        row.update(
            {
                "wavelength_nm": int(keys[0]),
                "width_nm": int(keys[1]),
                "depth_nm": int(keys[2]),
                "particle_diameter_nm": int(keys[3]),
                "engineering_gate_passed": bool(sub["engineering_gate_passed"].mean() >= 0.5),
                "design_recommendation_status": sub["design_recommendation_status"].mode().iat[0],
                "engineering_gate_primary_blocker": sub["engineering_gate_primary_blocker"].mode().iat[0],
            }
        )
        records.append(row)
    return sorted(
        records,
        key=lambda item: (
            item["wavelength_nm"],
            item["width_nm"],
            item["depth_nm"],
            item["particle_diameter_nm"],
        ),
    )


def _best_geometry_by_wavelength_and_diameter(df: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    for (wl, diameter_nm), sub in df.groupby(["wavelength_nm", "particle_diameter_nm"], dropna=False):
        best = sub.sort_values(
            ["final_engineering_score", "detection_rate", "stable_detection_rate"],
            ascending=False,
        ).iloc[0]
        rows.append(
            {
                "wavelength_nm": int(wl),
                "particle_diameter_nm": int(diameter_nm),
                "width_nm": int(best["width_nm"]),
                "depth_nm": int(best["depth_nm"]),
                "detection_rate": float(best["detection_rate"]),
                "stable_detection_rate": float(best["stable_detection_rate"]),
                "mean_peak_height": float(best["mean_peak_height"]),
                "mean_local_snr": float(best["mean_local_snr"]),
                "mean_peak_margin_z": float(best["mean_peak_margin_z"]),
                "mean_transit_time_ms": float(best["mean_transit_time_ms"]),
                "mean_nodi_transit_bandwidth_gain": float(
                    best["mean_nodi_transit_bandwidth_gain"]
                ),
                "A_ref": float(best["A_ref"]),
                "E_sca_normalized": float(best["E_sca_normalized"]),
                "phase_flip_fraction": float(best["phase_flip_fraction"]),
                "engineering_gate_passed": bool(best["engineering_gate_passed"]),
                "engineering_gate_primary_blocker": best["engineering_gate_primary_blocker"],
                "final_engineering_score": float(best["final_engineering_score"]),
            }
        )
    return sorted(rows, key=lambda item: (item["wavelength_nm"], item["particle_diameter_nm"]))


def _fit_power_law_exponents(df: pd.DataFrame) -> list[dict]:
    out: list[dict] = []
    for (wl, width_nm, depth_nm), sub in df.groupby(["wavelength_nm", "width_nm", "depth_nm"], dropna=False):
        x = sub["particle_diameter_nm"].to_numpy(dtype=float)
        peak = sub["mean_peak_height"].to_numpy(dtype=float)
        sca = sub["E_sca_normalized"].to_numpy(dtype=float)
        valid_peak = (x > 0) & (peak > 0)
        valid_sca = (x > 0) & (sca > 0)
        peak_exp = (
            float(np.polyfit(np.log(x[valid_peak]), np.log(peak[valid_peak]), 1)[0])
            if int(valid_peak.sum()) >= 2
            else float("nan")
        )
        sca_exp = (
            float(np.polyfit(np.log(x[valid_sca]), np.log(sca[valid_sca]), 1)[0])
            if int(valid_sca.sum()) >= 2
            else float("nan")
        )
        out.append(
            {
                "wavelength_nm": int(wl),
                "width_nm": int(width_nm),
                "depth_nm": int(depth_nm),
                "peak_height_power_law_exponent": peak_exp,
                "E_sca_power_law_exponent": sca_exp,
            }
        )
    return sorted(out, key=lambda item: (item["wavelength_nm"], item["width_nm"], item["depth_nm"]))


def _wavelength_geometry_folds(df: pd.DataFrame) -> dict[str, list[dict]]:
    wavelength_rows: list[dict] = []
    for (width_nm, depth_nm), sub in df.groupby(["width_nm", "depth_nm"], dropna=False):
        base = sub[sub["wavelength_nm"] == 488].set_index("particle_diameter_nm")
        for wl in WAVELENGTHS_NM:
            cur = sub[sub["wavelength_nm"] == wl].set_index("particle_diameter_nm")
            if len(cur) != len(base):
                continue
            merged = cur.join(
                base[["mean_peak_height", "detection_rate"]],
                rsuffix="_488",
                how="inner",
            )
            wavelength_rows.append(
                {
                    "width_nm": int(width_nm),
                    "depth_nm": int(depth_nm),
                    "wavelength_nm": int(wl),
                    "mean_peak_height_fold_vs_488": float(
                        (merged["mean_peak_height"] / merged["mean_peak_height_488"]).mean()
                    ),
                    "mean_detection_fold_vs_488": float(
                        (
                            (merged["detection_rate"] + 1e-12)
                            / (merged["detection_rate_488"] + 1e-12)
                        ).mean()
                    ),
                }
            )

    geometry_rows: list[dict] = []
    baseline = df[(df["width_nm"] == 800) & (df["depth_nm"] == 500)].copy()
    baseline = baseline.set_index(["wavelength_nm", "particle_diameter_nm"])
    for (width_nm, depth_nm), sub in df.groupby(["width_nm", "depth_nm"], dropna=False):
        cur = sub.set_index(["wavelength_nm", "particle_diameter_nm"])
        merged = cur.join(
            baseline[["mean_peak_height", "detection_rate"]],
            rsuffix="_800x500",
            how="inner",
        )
        geometry_rows.append(
            {
                "width_nm": int(width_nm),
                "depth_nm": int(depth_nm),
                "mean_peak_height_fold_vs_800x500": float(
                    (
                        merged["mean_peak_height"] / merged["mean_peak_height_800x500"]
                    ).mean()
                ),
                "mean_detection_fold_vs_800x500": float(
                    (
                        (merged["detection_rate"] + 1e-12)
                        / (merged["detection_rate_800x500"] + 1e-12)
                    ).mean()
                ),
            }
        )
    return {
        "wavelength_folds": sorted(
            wavelength_rows, key=lambda item: (item["width_nm"], item["depth_nm"], item["wavelength_nm"])
        ),
        "geometry_folds": sorted(geometry_rows, key=lambda item: (item["width_nm"], item["depth_nm"])),
    }


def _full_library_tsuyama_overlap() -> dict[str, object]:
    if not FULL_SUMMARY_PATH.exists():
        return {"available": False}
    df = pd.read_csv(FULL_SUMMARY_PATH)
    gold = df[df["particle_material"] == "gold"].copy()
    gold_tsuyama = gold[
        gold["width_nm"].between(800, 1200) & gold["depth_nm"].isin([500, 600])
    ].copy()
    gold_20_60 = gold_tsuyama[gold_tsuyama["particle_diameter_nm"].between(20, 60)].copy()

    by_wavelength = (
        gold_20_60.groupby("wavelength_nm", dropna=False)
        .agg(
            gate_rate=("engineering_gate_passed", "mean"),
            mean_detection=("detection_rate", "mean"),
            mean_stable=("stable_detection_rate", "mean"),
            mean_final=("final_engineering_score", "mean"),
            mean_peak_height=("mean_peak_height", "mean"),
            mean_local_snr=("mean_local_snr", "mean"),
            mean_A_ref=("A_ref", "mean"),
            mean_E_sca=("E_sca_normalized", "mean"),
        )
        .reset_index()
    )
    blocker_rows = []
    for wl, sub in gold_20_60.groupby("wavelength_nm", dropna=False):
        counts = (
            sub["engineering_gate_primary_blocker"]
            .fillna("unknown")
            .value_counts()
            .to_dict()
        )
        blocker_rows.append({"wavelength_nm": int(wl), "blocker_counts": counts})

    top_cases = (
        gold_20_60.sort_values(
            ["final_engineering_score", "detection_rate", "stable_detection_rate"],
            ascending=False,
        )[
            [
                "particle_diameter_nm",
                "wavelength_nm",
                "width_nm",
                "depth_nm",
                "detection_rate",
                "stable_detection_rate",
                "mean_peak_height",
                "mean_local_snr",
                "A_ref",
                "E_sca_normalized",
                "engineering_gate_passed",
                "engineering_gate_primary_blocker",
                "design_recommendation_status",
                "final_engineering_score",
            ]
        ]
        .head(20)
        .to_dict(orient="records")
    )
    return {
        "available": True,
        "source": str(FULL_SUMMARY_PATH),
        "scope": {
            "particle_material": "gold",
            "diameter_nm_range": [20, 60],
            "width_nm_range": [800, 1200],
            "depth_nm_options": [500, 600],
            "events_per_case": 10000,
            "lockin_tau_ms_note": "current_ev_design_library_uses_tau1ms_preset",
        },
        "by_wavelength": by_wavelength.to_dict(orient="records"),
        "blockers_by_wavelength": blocker_rows,
        "top_cases": top_cases,
    }


def _run_targeted_gold_sweep(
    *,
    n_events: int,
    n_workers: int,
    lockin_tau_ms: float,
    random_seed: int,
    readout_observable_mode: str,
    engineering_max_phase_flip_fraction: float,
) -> pd.DataFrame:
    sim_cfg = make_ev_nodi_design_sweep_config(deepcopy(DEFAULT_SIM_CFG))
    sim_cfg.n_events = n_events
    sim_cfg.score_mode = "single"
    sim_cfg.lockin_time_constant_s = lockin_tau_ms * 1e-3
    sim_cfg.random_seed = random_seed
    sim_cfg.readout_observable_mode = readout_observable_mode
    sim_cfg.engineering_max_phase_flip_fraction = engineering_max_phase_flip_fraction

    particles = [make_particle("gold", diameter_nm) for diameter_nm in DIAMETERS_NM]
    wavelength_list_m = np.array([wl * 1e-9 for wl in WAVELENGTHS_NM], dtype=float)

    t0 = time.time()
    results: list[dict] = []
    for index, (width_nm, depth_nm) in enumerate(GEOMETRIES_NM, start=1):
        print(
            f"[gold] geometry {index}/{len(GEOMETRIES_NM)}: {width_nm}x{depth_nm} nm",
            flush=True,
        )
        results.extend(
            run_parameter_sweep(
                particle_types=particles,
                medium=WATER,
                width_list_m=np.array([width_nm * 1e-9], dtype=float),
                depth_list_m=np.array([depth_nm * 1e-9], dtype=float),
                wavelength_list_m=wavelength_list_m,
                optical_template=OPTICAL_TEMPLATE,
                sim_cfg=sim_cfg,
                theta_grid_rad=THETA_GRID_RAD,
                baseline_particle=BASELINE_PARTICLE,
                verbose=False,
                n_workers=n_workers,
            )
        )
    df = _flatten_results(results)
    df["runtime_s"] = time.time() - t0
    df["readout_observable_mode"] = readout_observable_mode
    df["engineering_max_phase_flip_fraction"] = engineering_max_phase_flip_fraction
    return df


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run targeted Tsuyama gold validation sweeps with overrideable readout/gate settings."
    )
    parser.add_argument(
        "--validation-profile",
        choices=sorted(VALIDATION_PROFILES),
        default="paper_aligned",
        help=(
            "Preset validation profile. "
            "'paper_aligned' keeps the Tsuyama gold validation closer to the "
            "paper's pulse-height / maximum-signal readout semantics."
        ),
    )
    parser.add_argument(
        "--output-prefix",
        default=None,
        help=(
            "Prefix for the CSV/JSON files written under results/. "
            "Defaults to the canonical prefix for paper_aligned, or a "
            "profile-suffixed prefix for other profiles."
        ),
    )
    parser.add_argument(
        "--n-events",
        type=int,
        default=DEFAULT_N_EVENTS,
        help="Number of simulated events per case.",
    )
    parser.add_argument(
        "--n-workers",
        type=int,
        default=DEFAULT_N_WORKERS,
        help="Worker count passed to run_parameter_sweep.",
    )
    parser.add_argument(
        "--lockin-tau-ms",
        type=float,
        default=DEFAULT_LOCKIN_TAU_MS,
        help="Lock-in time constant in ms.",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=DEFAULT_RANDOM_SEED,
        help="Random seed for the targeted sweep.",
    )
    parser.add_argument(
        "--readout-observable-mode",
        choices=["in_phase", "magnitude"],
        default=None,
        help=(
            "Which lock-in observable is exported to downstream detection. "
            "When omitted, inherits from --validation-profile."
        ),
    )
    parser.add_argument(
        "--engineering-max-phase-flip-fraction",
        type=float,
        default=None,
        help=(
            "Engineering gate upper bound for phase_flip_fraction. "
            "When omitted, inherits from --validation-profile."
        ),
    )
    return parser


def main() -> None:
    args = _build_arg_parser().parse_args()
    profile = VALIDATION_PROFILES[args.validation_profile]
    readout_observable_mode = cast(
        str,
        (
            args.readout_observable_mode
            if args.readout_observable_mode is not None
            else profile["readout_observable_mode"]
        ),
    )
    engineering_max_phase_flip_fraction = (
        cast(float, args.engineering_max_phase_flip_fraction)
        if args.engineering_max_phase_flip_fraction is not None
        else cast(float, profile["engineering_max_phase_flip_fraction"])
    )
    output_prefix = args.output_prefix
    if output_prefix is None:
        if args.validation_profile == "paper_aligned":
            output_prefix = DEFAULT_OUTPUT_PREFIX
        else:
            output_prefix = (
                f"{DEFAULT_OUTPUT_PREFIX}_{args.validation_profile}"
            )
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    full_library = _full_library_tsuyama_overlap()
    targeted_df = _run_targeted_gold_sweep(
        n_events=args.n_events,
        n_workers=args.n_workers,
        lockin_tau_ms=args.lockin_tau_ms,
        random_seed=args.random_seed,
        readout_observable_mode=readout_observable_mode,
        engineering_max_phase_flip_fraction=engineering_max_phase_flip_fraction,
    )
    csv_path = RESULTS_DIR / f"{output_prefix}_cases.csv"
    targeted_df.to_csv(csv_path, index=False)

    case_table = _aggregate_case_table(targeted_df)
    best_by_wl_diameter = _best_geometry_by_wavelength_and_diameter(targeted_df)
    power_laws = _fit_power_law_exponents(targeted_df)
    fold_tables = _wavelength_geometry_folds(targeted_df)
    spearman_detection = _spearman_detection(targeted_df)

    report = {
        "scope": {
            "wavelengths_nm": WAVELENGTHS_NM,
            "geometries_nm": GEOMETRIES_NM,
            "diameters_nm": DIAMETERS_NM,
            "n_events_per_case": args.n_events,
            "n_workers": args.n_workers,
            "lockin_tau_ms": args.lockin_tau_ms,
            "random_seed": args.random_seed,
            "validation_profile": args.validation_profile,
            "validation_profile_description": profile["description"],
            "readout_observable_mode": readout_observable_mode,
            "engineering_max_phase_flip_fraction": (
                engineering_max_phase_flip_fraction
            ),
        },
        "full_library_tsuyama_overlap": full_library,
        "targeted_tau1ms": {
            "spearman_detection": spearman_detection,
            "case_table": case_table,
            "best_by_wavelength_and_diameter": best_by_wl_diameter,
            "power_law_exponents": power_laws,
            **fold_tables,
        },
    }

    json_path = RESULTS_DIR / f"{output_prefix}_report.json"
    write_json_file(json_path, report, sort_keys=False, allow_nan=True)

    print(f"saved: {csv_path}")
    print(f"saved: {json_path}")


if __name__ == "__main__":
    main()
