from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_PARENT = PROJECT_ROOT.parent
for candidate in (str(PROJECT_ROOT), str(PROJECT_PARENT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from nodi_simulator import SimulationConfig, WATER, run_parameter_sweep
from nodi_simulator.dashboard.config import (
    BASELINE_PARTICLE,
    DEFAULT_SIM_CFG,
    OPTICAL_TEMPLATE,
    THETA_GRID_RAD,
    particle_from_name,
)


RESULTS_DIR = PROJECT_ROOT / "results"
CURRENT_LIBRARY_PREFIX = "ev_design_full_range_biomimetic_exosome_with_anchors_10000e"
SUMMARY_PATH = RESULTS_DIR / f"{CURRENT_LIBRARY_PREFIX}_summary.csv"
META_PATH = RESULTS_DIR / f"{CURRENT_LIBRARY_PREFIX}_meta.json"
SELECTED_CASES_PATH = RESULTS_DIR / "phase_gate_cross_scope_sensitivity_selected_cases.csv"
OUTPUT_PREFIX = "mainline_consistency_audit"
MAX_WORKERS = 8


def _missing_required_inputs() -> list[str]:
    """Return required result-library inputs that are not available yet."""
    required_paths = [
        SUMMARY_PATH,
        META_PATH,
        SELECTED_CASES_PATH,
    ]
    return [str(path) for path in required_paths if not path.exists()]


def _build_profiles(meta_cfg: SimulationConfig) -> dict[str, SimulationConfig]:
    current_cfg = deepcopy(DEFAULT_SIM_CFG)
    current_cfg.n_events = meta_cfg.n_events
    current_cfg.random_seed = meta_cfg.random_seed
    # Single-case replay cannot use joint score mode because run_parameter_sweep
    # requires exactly two particle types in that path. The engineering gate and
    # raw detection statistics we audit here do not depend on joint ranking.
    current_cfg.score_mode = "single"
    return {
        "stored_meta_exact": deepcopy(meta_cfg),
        "current_dashboard_replay_10000e": current_cfg,
    }


def _select_cases() -> pd.DataFrame:
    selected = pd.read_csv(SELECTED_CASES_PATH)
    selected = selected[
        selected["cohort"] == "exosome_mainline_representative"
    ].copy()
    selected = selected.sort_values(
        ["wavelength_nm", "particle_name", "width_nm", "depth_nm"]
    ).reset_index(drop=True)
    return selected


def _load_summary_lookup() -> pd.DataFrame:
    summary = pd.read_csv(SUMMARY_PATH)
    return summary[
        [
            "particle_name",
            "wavelength_nm",
            "width_nm",
            "depth_nm",
            "detection_rate",
            "stable_detection_rate",
            "phase_flip_fraction",
            "mean_peak_height",
            "engineering_gate_passed",
            "engineering_gate_primary_blocker",
            "final_engineering_score",
        ]
    ].copy()


def _flatten_result(result: dict) -> dict:
    summary = dict(result.get("summary", {}))
    return {
        "rerun_detection_rate": float(summary.get("detection_rate", 0.0) or 0.0),
        "rerun_stable_detection_rate": float(
            summary.get("stable_detection_rate", 0.0) or 0.0
        ),
        "rerun_phase_flip_fraction": float(
            summary.get("phase_flip_fraction", 0.0) or 0.0
        ),
        "rerun_mean_peak_height": float(summary.get("mean_peak_height", 0.0) or 0.0),
        "rerun_engineering_gate_passed": bool(
            result.get("engineering_gate_passed", False)
        ),
        "rerun_engineering_gate_primary_blocker": result.get(
            "engineering_gate_primary_blocker"
        ),
        "rerun_final_engineering_score": float(
            result.get(
                "final_engineering_score",
                result.get("engineering_score", 0.0),
            )
            or 0.0
        ),
    }


def _run_one(task: dict) -> dict:
    case_row = task["case_row"]
    profile_name = task["profile_name"]
    cfg_payload = task["cfg_payload"]

    sim_cfg = SimulationConfig(**cfg_payload)
    particle_name = str(case_row["particle_name"])
    wavelength_nm = int(case_row["wavelength_nm"])
    width_nm = int(case_row["width_nm"])
    depth_nm = int(case_row["depth_nm"])

    particle = particle_from_name(particle_name)
    results = run_parameter_sweep(
        particle_types=[particle],
        medium=WATER,
        width_list_m=np.array([width_nm * 1e-9], dtype=float),
        depth_list_m=np.array([depth_nm * 1e-9], dtype=float),
        wavelength_list_m=np.array([wavelength_nm * 1e-9], dtype=float),
        optical_template=OPTICAL_TEMPLATE,
        sim_cfg=sim_cfg,
        theta_grid_rad=THETA_GRID_RAD,
        baseline_particle=BASELINE_PARTICLE,
        verbose=False,
        n_workers=1,
    )
    if len(results) != 1:
        raise RuntimeError(f"Expected exactly one result, got {len(results)}")

    return {
        "profile_name": profile_name,
        "particle_name": particle_name,
        "wavelength_nm": wavelength_nm,
        "width_nm": width_nm,
        "depth_nm": depth_nm,
        "lockin_time_constant_s": float(sim_cfg.lockin_time_constant_s),
        "n_events": int(sim_cfg.n_events),
        "score_mode": str(sim_cfg.score_mode),
        **_flatten_result(results[0]),
    }


def _profile_summary(merged: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    for profile_name, sub in merged.groupby("profile_name", dropna=False):
        gate_match = (
            sub["engineering_gate_passed"].astype(bool)
            == sub["rerun_engineering_gate_passed"].astype(bool)
        )
        blocker_match = (
            sub["engineering_gate_primary_blocker"].fillna("")
            == sub["rerun_engineering_gate_primary_blocker"].fillna("")
        )
        rows.append(
            {
                "profile_name": str(profile_name),
                "n_cases": int(len(sub)),
                "gate_match_count": int(gate_match.sum()),
                "blocker_match_count": int(blocker_match.sum()),
                "max_abs_detection_delta": float(
                    (sub["rerun_detection_rate"] - sub["detection_rate"]).abs().max()
                ),
                "mean_abs_detection_delta": float(
                    (sub["rerun_detection_rate"] - sub["detection_rate"]).abs().mean()
                ),
                "max_abs_stable_delta": float(
                    (
                        sub["rerun_stable_detection_rate"]
                        - sub["stable_detection_rate"]
                    )
                    .abs()
                    .max()
                ),
                "mean_abs_stable_delta": float(
                    (
                        sub["rerun_stable_detection_rate"]
                        - sub["stable_detection_rate"]
                    )
                    .abs()
                    .mean()
                ),
                "max_abs_phase_flip_delta": float(
                    (
                        sub["rerun_phase_flip_fraction"] - sub["phase_flip_fraction"]
                    )
                    .abs()
                    .max()
                ),
                "mean_abs_phase_flip_delta": float(
                    (
                        sub["rerun_phase_flip_fraction"] - sub["phase_flip_fraction"]
                    )
                    .abs()
                    .mean()
                ),
                "max_abs_peak_delta": float(
                    (sub["rerun_mean_peak_height"] - sub["mean_peak_height"])
                    .abs()
                    .max()
                ),
                "mean_abs_peak_delta": float(
                    (sub["rerun_mean_peak_height"] - sub["mean_peak_height"])
                    .abs()
                    .mean()
                ),
            }
        )
    return rows


def main() -> None:
    missing_inputs = _missing_required_inputs()
    if missing_inputs:
        print(
            json.dumps(
                {
                    "audit_scope": "mainline_consistency_replay",
                    "status": "skipped_missing_inputs",
                    "missing_inputs": missing_inputs,
                    "next_step": (
                        "Run the formal full-grid recompute first, then rerun "
                        "this audit against the generated result library."
                    ),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    meta_payload = json.loads(META_PATH.read_text(encoding="utf-8"))
    meta_cfg = SimulationConfig(**meta_payload["sim_cfg"])
    profiles = _build_profiles(meta_cfg)
    summary_lookup = _load_summary_lookup()
    selected_cases = _select_cases()

    tasks: list[dict] = []
    for _, case_row in selected_cases.iterrows():
        case_payload = case_row.to_dict()
        for profile_name, profile_cfg in profiles.items():
            tasks.append(
                {
                    "case_row": case_payload,
                    "profile_name": profile_name,
                    "cfg_payload": asdict(profile_cfg),
                }
            )

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
        rerun_rows = list(pool.map(_run_one, tasks))

    rerun_df = pd.DataFrame(rerun_rows).sort_values(
        ["profile_name", "wavelength_nm", "particle_name", "width_nm", "depth_nm"]
    )
    merged = summary_lookup.merge(
        rerun_df,
        on=["particle_name", "wavelength_nm", "width_nm", "depth_nm"],
        how="inner",
    ).copy()

    merged["abs_detection_delta"] = (
        merged["rerun_detection_rate"] - merged["detection_rate"]
    ).abs()
    merged["abs_stable_delta"] = (
        merged["rerun_stable_detection_rate"] - merged["stable_detection_rate"]
    ).abs()
    merged["abs_phase_flip_delta"] = (
        merged["rerun_phase_flip_fraction"] - merged["phase_flip_fraction"]
    ).abs()
    merged["abs_peak_delta"] = (
        merged["rerun_mean_peak_height"] - merged["mean_peak_height"]
    ).abs()
    merged["gate_match"] = (
        merged["engineering_gate_passed"].astype(bool)
        == merged["rerun_engineering_gate_passed"].astype(bool)
    )
    merged["primary_blocker_match"] = (
        merged["engineering_gate_primary_blocker"].fillna("")
        == merged["rerun_engineering_gate_primary_blocker"].fillna("")
    )

    profile_rows = _profile_summary(merged)
    current_vs_meta_cfg = []
    current_cfg = asdict(profiles["current_dashboard_replay_10000e"])
    meta_cfg_payload = asdict(profiles["stored_meta_exact"])
    for key in sorted(set(current_cfg) | set(meta_cfg_payload)):
        meta_value = meta_cfg_payload.get(key)
        current_value = current_cfg.get(key)
        if meta_value != current_value:
            current_vs_meta_cfg.append(
                {
                    "field": key,
                    "stored_meta_exact": meta_value,
                    "current_dashboard_replay_10000e": current_value,
                }
            )

    report = {
        "audit_scope": "mainline_consistency_replay",
        "selected_case_count": int(len(selected_cases)),
        "max_workers": int(MAX_WORKERS),
        "profiles": {
            name: {
                "lockin_time_constant_s": float(cfg.lockin_time_constant_s),
                "n_events": int(cfg.n_events),
                "score_mode": str(cfg.score_mode),
            }
            for name, cfg in profiles.items()
        },
        "profile_notes": {
            "stored_meta_exact": (
                "Direct replay of the frozen full-library meta.json configuration."
            ),
            "current_dashboard_replay_10000e": (
                "Current dashboard physical defaults with n_events aligned to 10000; "
                "score_mode is coerced to single only because one-case replay cannot "
                "execute the joint-ranking path."
            ),
        },
        "current_vs_meta_config_differences": current_vs_meta_cfg,
        "profile_summary": profile_rows,
    }

    selected_cases.to_csv(
        RESULTS_DIR / f"{OUTPUT_PREFIX}_selected_cases.csv",
        index=False,
    )
    merged.to_csv(
        RESULTS_DIR / f"{OUTPUT_PREFIX}_cases.csv",
        index=False,
    )
    (RESULTS_DIR / f"{OUTPUT_PREFIX}_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print()
    print(
        merged[
            [
                "profile_name",
                "particle_name",
                "wavelength_nm",
                "width_nm",
                "depth_nm",
                "detection_rate",
                "rerun_detection_rate",
                "stable_detection_rate",
                "rerun_stable_detection_rate",
                "phase_flip_fraction",
                "rerun_phase_flip_fraction",
                "engineering_gate_passed",
                "rerun_engineering_gate_passed",
                "engineering_gate_primary_blocker",
                "rerun_engineering_gate_primary_blocker",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    main()
