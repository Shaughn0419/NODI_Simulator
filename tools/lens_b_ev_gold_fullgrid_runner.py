#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from contextlib import suppress
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from copy import copy
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for candidate in (str(PROJECT_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from dashboard.config import (  # noqa: E402
    BASELINE_PARTICLE,
    THETA_GRID_RAD,
    medium_for_particle,
    particle_from_name,
)
from nodi_simulator._exports import WATER, run_parameter_sweep  # noqa: E402
from nodi_simulator.config_trace import build_minimal_config_trace  # noqa: E402
from nodi_simulator.parameter_sweep import (  # noqa: E402
    build_sweep_case_key,
    run_single_case_batch_shared_event_normalization_views,
)
from nodi_simulator.utils import compute_baseline_normalization_per_wavelength  # noqa: E402
from tools._common import json_safe, write_json_file  # noqa: E402
from tools.audits import tsuyama_detection_rate_calibration as rate_calib  # noqa: E402
from tools.audits import tsuyama_gold_aligned_detection_lane as lane  # noqa: E402


EXPECTED_ROUTES = 572
EXPECTED_PARTICLES = 56
EXPECTED_EV_PARTICLES = 27
EXPECTED_GOLD_PARTICLES = 29
EXPECTED_ROWS_PER_SEED = 32032
FORMAL_FULL_GRID_SEEDS = (11, 22, 33)
FORMAL_FULL_GRID_EVENTS_PER_CASE = 10_000
INNER_SWEEP_WORKERS_PER_ROUTE = 1
_BLAS_THREAD_ENV_VARS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
_ROUTE_WORKER_CONTEXT: dict[str, Any] | None = None
_CSV_SCALAR_TYPES = (
    str,
    int,
    float,
    bool,
    type(None),
    np.integer,
    np.floating,
    np.bool_,
)
RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM = (404, 660)
CONTROL_ONLY_WAVELENGTHS_NM = (488, 532)
SINGLE_NORMALIZATION_LANES = ("per_wavelength_gold", "fixed_660_gold")
SHARED_DUAL_NORMALIZATION_LANE = "shared_dual_gold"
NORMALIZATION_LANES = (*SINGLE_NORMALIZATION_LANES, SHARED_DUAL_NORMALIZATION_LANE)
FIXED_660_NORMALIZATION_REFERENCE_WAVELENGTH_NM = 660
FIXED_660_NORMALIZATION_REFERENCE_WAVELENGTH_M = (
    FIXED_660_NORMALIZATION_REFERENCE_WAVELENGTH_NM * 1e-9
)
FROZEN_B_OPERATOR_SOURCE_CANDIDATE_ID = "tau_1ms_global_refphi_plus_collection_narrow"
FROZEN_B_CANDIDATE_ID = (
    "tau_1ms_global_refphi_plus_collection_narrow__paper_5sigma_sensitivity"
)
FROZEN_B_SCENARIO_ID = "nodi_2022_5sigma_single_sensitivity"
FROZEN_B_LOCKIN_TIME_CONSTANT_S = 1.0e-3
FROZEN_B_METADATA = {
    "operator_family": (
        "Criterion B 1 ms refphase/collection operator; lock-in fixed to 1 ms. "
        "Legacy tau_2ms_global_refphi_plus_collection_narrow is provenance only."
    ),
    "candidate_id": FROZEN_B_CANDIDATE_ID,
    "operator_source_candidate_id": FROZEN_B_OPERATOR_SOURCE_CANDIDATE_ID,
    "gamma": 0.736502,
    "snr_scale": 0.890700,
    "snr_response_exp": 0.810281,
    "raw_global_snr_scale": 0.293130,
    "legacy_2ms_gamma": 0.749,
    "legacy_2ms_snr_scale": 0.728,
    "legacy_2ms_snr_response_exp": 0.812,
    "selected_annulus_edge_norm_min": 0.5,
    "selected_annulus_edge_norm_max": 0.8,
    "lockin_tau": "fixed 1 ms by Criterion B runtime requirement",
    "scenario_baseline": FROZEN_B_SCENARIO_ID,
    "n_events": "set per run from CLI --n-events",
    "recommendation_eligible_wavelengths_nm": RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM,
    "control_only_wavelengths_nm": CONTROL_ONLY_WAVELENGTHS_NM,
}
FROZEN_B_IMPLEMENTATION_STATUS = {
    "implemented_in_runtime_config": {
        "scenario_baseline": FROZEN_B_SCENARIO_ID,
        "candidate_id": FROZEN_B_CANDIDATE_ID,
        "operator_source_candidate_id": FROZEN_B_OPERATOR_SOURCE_CANDIDATE_ID,
        "lockin_time_constant_s": FROZEN_B_LOCKIN_TIME_CONSTANT_S,
        "ref_phi0_rad": 0.4,
        "collection_sigma_rad": 0.08,
        "collection_phi_sigma_rad": 0.16,
        "slit_phi_limit_rad": 0.25,
        "selected_annulus_edge_norm_min": 0.5,
        "selected_annulus_edge_norm_max": 0.8,
        "n_events": "set per run from CLI --n-events",
    },
    "metadata_only_in_this_runner": {
        "operator_family": "Criterion B 1 ms refphase/collection operator; 2 ms lineage is provenance only.",
        "gamma": "1 ms B4 descriptive response-compression scalar; no SimulationConfig field.",
        "snr_scale": "1 ms B4 descriptive SNR rescore scalar; no SimulationConfig field.",
        "snr_response_exp": "1 ms B4 descriptive SNR exponent; no SimulationConfig field.",
        "raw_global_snr_scale": "1 ms B4 descriptive raw global SNR scale; no SimulationConfig field.",
        "lockin_tau": "Runtime lock-in is fixed to 1 ms; existing 2 ms runs are legacy sensitivity/reference outputs.",
    },
    "requires_code_change_before_full_run_if_active_transform_required": [
        "Applying gamma=0.736502 to raw EV/gold runtime outputs.",
        "Applying snr_scale=0.890700 to raw EV/gold runtime outputs.",
        "Applying snr_response_exp=0.810281 to raw EV/gold runtime outputs.",
        "Applying raw_global_snr_scale=0.293130 to raw EV/gold runtime outputs.",
    ],
}


@dataclass(frozen=True)
class SourceScope:
    routes: list[tuple[int, int, int]]
    particle_names: list[str]
    ev_particle_names: list[str]
    gold_particle_names: list[str]
    route_particle_rows_per_seed: int


class RouteJobError(RuntimeError):
    def __init__(
        self,
        *,
        route_index: int,
        route: tuple[int, int, int],
        original: BaseException,
    ) -> None:
        super().__init__(str(original))
        self.route_index = int(route_index)
        self.route = tuple(route)
        self.original = original


def _read_source(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"route source does not exist: {path}")
    required = [
        "particle_name",
        "particle_material",
        "particle_family",
        "wavelength_nm",
        "width_nm",
        "depth_nm",
    ]
    return pd.read_csv(path, usecols=required, low_memory=False)


def load_and_validate_source(path: Path, *, particle_scope: str) -> SourceScope:
    if particle_scope != "ev_gold":
        raise ValueError("Only --particle-scope ev_gold is supported by this handoff runner.")
    df = _read_source(path)
    df["wavelength_nm"] = pd.to_numeric(df["wavelength_nm"], errors="raise").astype(int)
    df["width_nm"] = pd.to_numeric(df["width_nm"], errors="raise").astype(int)
    df["depth_nm"] = pd.to_numeric(df["depth_nm"], errors="raise").astype(int)
    df["particle_name"] = df["particle_name"].astype(str)
    df["particle_material"] = df["particle_material"].astype(str)
    df["particle_family"] = df["particle_family"].astype(str)

    silver = df[
        df["particle_material"].str.lower().str.contains("silver|ag", regex=True)
        | df["particle_name"].str.lower().str.contains("silver|ag", regex=True)
    ]
    if not silver.empty:
        raise ValueError("Ag/silver rows are present, but the handoff scope is EV + gold only.")

    routes = sorted(
        {
            (int(row.wavelength_nm), int(row.width_nm), int(row.depth_nm))
            for row in df[["wavelength_nm", "width_nm", "depth_nm"]]
            .drop_duplicates()
            .itertuples(index=False)
        }
    )
    particles = (
        df[["particle_name", "particle_material", "particle_family"]]
        .drop_duplicates()
        .sort_values(["particle_material", "particle_name"])
    )
    ev = particles[
        (particles["particle_material"].str.lower() == "exosome")
        | particles["particle_family"].str.lower().str.contains("ev|exosome|sev", regex=True)
        | particles["particle_name"].str.lower().str.startswith("exosome_")
    ]
    gold = particles[
        (particles["particle_material"].str.lower() == "gold")
        | particles["particle_name"].str.lower().str.startswith("gold_")
    ]
    row_count = len(routes) * len(particles)

    print("Preflight validation:")
    print(f"unique routes: {len(routes)}")
    print(f"unique particles: {len(particles)}")
    print(f"EV/exosome particle count: {len(ev)}")
    print(f"gold particle count: {len(gold)}")
    print(f"route-particle rows per seed: {row_count}")

    expected = {
        "routes": (len(routes), EXPECTED_ROUTES),
        "particles": (len(particles), EXPECTED_PARTICLES),
        "EV/exosome particles": (len(ev), EXPECTED_EV_PARTICLES),
        "gold particles": (len(gold), EXPECTED_GOLD_PARTICLES),
        "route-particle rows per seed": (row_count, EXPECTED_ROWS_PER_SEED),
    }
    mismatches = {
        name: {"actual": actual, "expected": exp}
        for name, (actual, exp) in expected.items()
        if actual != exp
    }
    if mismatches:
        raise ValueError(f"Source preflight differs from handoff expectations: {mismatches}")

    return SourceScope(
        routes=routes,
        particle_names=list(particles["particle_name"]),
        ev_particle_names=list(ev["particle_name"]),
        gold_particle_names=list(gold["particle_name"]),
        route_particle_rows_per_seed=row_count,
    )


def build_frozen_b_cfg(n_events: int, seed: int):
    catalog = rate_calib.candidate_by_id()
    candidate = catalog[FROZEN_B_OPERATOR_SOURCE_CANDIDATE_ID]
    cfg = rate_calib.build_candidate_cfg(
        candidate,
        n_events=int(n_events),
        random_seed=int(seed),
        scenario_id=FROZEN_B_SCENARIO_ID,
    )
    cfg = replace(
        cfg,
        lockin_time_constant_s=FROZEN_B_LOCKIN_TIME_CONSTANT_S,
        selected_annulus_edge_norm_min=0.5,
        selected_annulus_edge_norm_max=0.8,
        adaptive_event_budget_mode="fixed",
        random_sequence_policy="case_keyed_independent",
    )
    optical_template = rate_calib.build_candidate_optical_template(candidate)
    return cfg, optical_template


def _readable_duration(seconds: float | None) -> str:
    if seconds is None or not math.isfinite(seconds):
        return "unavailable"
    seconds = max(0.0, float(seconds))
    hours = seconds / 3600.0
    if hours >= 48.0:
        return f"{hours / 24.0:.2f} days"
    if hours >= 1.0:
        return f"{hours:.2f} h"
    minutes = seconds / 60.0
    return f"{minutes:.2f} min"


def _directory_size_bytes(path: Path) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for filename in files:
            full = Path(root) / filename
            with suppress(FileNotFoundError):
                total += full.stat().st_size
    return total


def _resolve_route_worker_count(workers: int | None) -> int:
    if workers is None:
        return 1
    if workers < 0:
        raise ValueError("--workers must be >= 0")
    if workers == 0:
        return max(1, os.cpu_count() or 1)
    return int(workers)


def _configure_route_worker_env() -> dict[str, str]:
    updated = {}
    for env_var in _BLAS_THREAD_ENV_VARS:
        if env_var not in os.environ:
            os.environ[env_var] = "1"
            updated[env_var] = "1"
    return updated


def _write_manifest(
    *,
    output_dir: Path,
    args: argparse.Namespace,
    scope: SourceScope,
    cfg: Any,
    run_kind: str,
    optical_template: Any | None = None,
) -> None:
    frozen_metadata = dict(FROZEN_B_METADATA)
    frozen_metadata["n_events"] = int(args.n_events)
    implementation_status = {
        key: (dict(value) if isinstance(value, dict) else value)
        for key, value in FROZEN_B_IMPLEMENTATION_STATUS.items()
    }
    implementation_status["implemented_in_runtime_config"] = dict(
        implementation_status["implemented_in_runtime_config"]
    )
    implementation_status["implemented_in_runtime_config"]["n_events"] = int(args.n_events)
    normalization_metadata = _normalization_metadata(args.normalization_lane, cfg)
    config_trace = build_minimal_config_trace(
        cfg=cfg,
        optical_template=optical_template,
        normalization_view=args.normalization_lane,
        config_trace_status="original_runtime_record",
    )
    manifest = {
        "run_kind": run_kind,
        "workers": int(args.workers),
        "overwrite_output": bool(args.overwrite_output),
        "one_lane_primitive_acknowledged": bool(args.accept_one_lane_primitive),
        "full_grid_scope_guard": {
            "canonical_full_grid_seeds": list(FORMAL_FULL_GRID_SEEDS),
            "canonical_events_per_case": FORMAL_FULL_GRID_EVENTS_PER_CASE,
            "this_runner_scope": (
                "one_seed_shared_event_dual_normalization"
                if args.normalization_lane == SHARED_DUAL_NORMALIZATION_LANE
                else "one_seed_one_normalization_lane_primitive"
            ),
            "not_shared_event_dual_normalization": bool(
                args.normalization_lane != SHARED_DUAL_NORMALIZATION_LANE
            ),
            "shared_event_dual_normalization_used": bool(
                args.normalization_lane == SHARED_DUAL_NORMALIZATION_LANE
            ),
            "dual_view_requirement": (
                "fixed_660_gold and per_wavelength_gold are analysis views; "
                "do not treat separate one-lane runs as scientifically required "
                "event doubling unless an explicit recompute workaround is accepted."
            ),
        },
        "route_parallelism": {
            "strategy": "route_level_process_pool",
            "route_workers": int(_resolve_route_worker_count(args.workers)),
            "inner_sweep_workers_per_route": INNER_SWEEP_WORKERS_PER_ROUTE,
            "csv_write_policy": "append_completed_routes_in_route_index_order",
        },
        "n_events": int(args.n_events),
        "seed": int(args.seed),
        "benchmark_seconds": (
            float(args.benchmark_seconds) if args.benchmark_seconds is not None else None
        ),
        "particle_scope": args.particle_scope,
        "route_source": str(Path(args.route_source)),
        **normalization_metadata,
        "source_scope": asdict(scope),
        "frozen_b_metadata": frozen_metadata,
        "frozen_b_implementation_status": implementation_status,
        "recommendation_rule": {
            "raw_control_wavelengths_kept_nm": [404, 488, 532, 660],
            "final_recommendation_conclusions_use_only_nm": list(
                RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM
            ),
            "control_only_wavelengths_nm": list(CONTROL_ONLY_WAVELENGTHS_NM),
            "EV_recommendation_uses": "EV rows only",
            "gold_rows_role": "anchor / Tsuyama consistency diagnostics",
        },
        "runtime_config_subset": {
            "lockin_time_constant_s": cfg.lockin_time_constant_s,
            "threshold_sigma": cfg.threshold_sigma,
            "threshold_tail": cfg.threshold_tail,
            "readout_preset": cfg.readout_preset,
            "readout_observable_mode": cfg.readout_observable_mode,
            "pulse_detection_mode": cfg.pulse_detection_mode,
            "detection_decision_mode": cfg.detection_decision_mode,
            "selected_annulus_edge_norm_min": cfg.selected_annulus_edge_norm_min,
            "selected_annulus_edge_norm_max": cfg.selected_annulus_edge_norm_max,
            "random_sequence_policy": cfg.random_sequence_policy,
            "adaptive_event_budget_mode": cfg.adaptive_event_budget_mode,
            **config_trace.runtime_config_subset,
        },
    }
    write_json_file(output_dir / "run_manifest.json", manifest)


def _normalization_metadata(normalization_lane: str, cfg: Any) -> dict[str, Any]:
    if normalization_lane == SHARED_DUAL_NORMALIZATION_LANE:
        return {
            "normalization_lane": SHARED_DUAL_NORMALIZATION_LANE,
            "normalization_views": list(SINGLE_NORMALIZATION_LANES[::-1]),
            "normalization_mode": "shared_event_dual_view",
            "normalization_reference_wavelength_nm": None,
            "normalization_reference_particle": BASELINE_PARTICLE.name,
            "normalization_reference_scope": (
                "fixed_660_gold plus per_wavelength_gold from one physical event stream"
            ),
            "tsuyama_reproduction_lane": True,
            "ev_cross_wavelength_decision_lane": True,
            "runtime_cfg_normalization_mode": str(cfg.normalization_mode),
            "shared_event_dual_normalization_used": True,
        }
    if normalization_lane == "fixed_660_gold":
        return {
            "normalization_lane": "fixed_660_gold",
            "normalization_mode": "global_single_lambda",
            "normalization_reference_wavelength_nm": (
                FIXED_660_NORMALIZATION_REFERENCE_WAVELENGTH_NM
            ),
            "normalization_reference_particle": BASELINE_PARTICLE.name,
            "normalization_reference_scope": "per_width_depth_channel",
            "tsuyama_reproduction_lane": False,
            "ev_cross_wavelength_decision_lane": True,
            "runtime_cfg_normalization_mode": str(cfg.normalization_mode),
        }
    if normalization_lane == "per_wavelength_gold":
        return {
            "normalization_lane": "per_wavelength_gold",
            "normalization_mode": "per_wavelength",
            "normalization_reference_wavelength_nm": None,
            "normalization_reference_particle": BASELINE_PARTICLE.name,
            "normalization_reference_scope": "per_width_depth_channel_and_wavelength",
            "tsuyama_reproduction_lane": True,
            "ev_cross_wavelength_decision_lane": False,
            "runtime_cfg_normalization_mode": str(cfg.normalization_mode),
        }
    raise ValueError(f"Unsupported normalization lane: {normalization_lane}")


def _cfg_for_normalization_lane(cfg: Any, normalization_lane: str) -> Any:
    if normalization_lane == SHARED_DUAL_NORMALIZATION_LANE:
        return cfg
    if normalization_lane == "fixed_660_gold":
        return replace(cfg, normalization_mode="global_single_lambda")
    if normalization_lane == "per_wavelength_gold":
        return replace(cfg, normalization_mode="per_wavelength")
    raise ValueError(f"Unsupported normalization lane: {normalization_lane}")


def _fixed_660_e_sca_ref(
    *,
    width_nm: int,
    depth_nm: int,
    cfg: Any,
    optical_template: Any,
) -> float:
    baseline_channel = lane.case_baseline_channel(width_nm, depth_nm)
    refs = compute_baseline_normalization_per_wavelength(
        BASELINE_PARTICLE,
        WATER,
        optical_template,
        np.array([FIXED_660_NORMALIZATION_REFERENCE_WAVELENGTH_M], dtype=float),
        THETA_GRID_RAD,
        channel=baseline_channel,
        sim_cfg=cfg,
    )
    return float(refs[FIXED_660_NORMALIZATION_REFERENCE_WAVELENGTH_M])


def _per_wavelength_e_sca_ref(
    *,
    wavelength_nm: int,
    width_nm: int,
    depth_nm: int,
    medium: Any,
    cfg: Any,
    optical_template: Any,
) -> float:
    optical = copy(optical_template)
    optical.wavelength_m = float(wavelength_nm) * 1e-9
    baseline_channel = lane.case_baseline_channel(width_nm, depth_nm)
    refs = compute_baseline_normalization_per_wavelength(
        BASELINE_PARTICLE,
        medium,
        optical,
        np.array([float(wavelength_nm) * 1e-9], dtype=float),
        THETA_GRID_RAD,
        channel=baseline_channel,
        sim_cfg=cfg,
    )
    return float(refs[float(wavelength_nm) * 1e-9])


def _add_normalization_columns(
    frame: pd.DataFrame,
    *,
    normalization_lane: str,
    cfg: Any,
) -> pd.DataFrame:
    metadata = _normalization_metadata(normalization_lane, cfg)
    for key, value in metadata.items():
        frame[key] = value
    return frame


def _add_shared_event_dual_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame["shared_event_dual_normalization_used"] = True
    frame["shared_event_normalization_view_count"] = len(SINGLE_NORMALIZATION_LANES)
    frame["shared_event_normalization_views"] = ",".join(SINGLE_NORMALIZATION_LANES)
    return frame


def _add_shared_event_dual_progress_fields(payload: dict[str, Any]) -> dict[str, Any]:
    payload["normalization_lane"] = SHARED_DUAL_NORMALIZATION_LANE
    payload["normalization_views"] = list(SINGLE_NORMALIZATION_LANES)
    payload["shared_event_dual_normalization_used"] = True
    payload["analysis_view_row_total_per_seed"] = (
        EXPECTED_ROWS_PER_SEED * len(SINGLE_NORMALIZATION_LANES)
    )
    return payload


def _is_csv_scalar(value: Any) -> bool:
    return isinstance(value, _CSV_SCALAR_TYPES) or isinstance(value, complex)


def _csv_scalar(value: Any) -> Any:
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, complex):
        return str(value)
    return value


def _diagnostic_scalar_frame(results: list[dict[str, Any]]) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for result in results:
        record: dict[str, Any] = {}
        for key, value in result.items():
            if key == "summary":
                continue
            if _is_csv_scalar(value):
                record[str(key)] = _csv_scalar(value)
        summary = result.get("summary")
        if isinstance(summary, dict):
            for key, value in summary.items():
                if not _is_csv_scalar(value):
                    continue
                output_key = str(key)
                if output_key in record:
                    output_key = f"summary__{output_key}"
                record[output_key] = _csv_scalar(value)
        records.append(record)
    return pd.DataFrame(records)


def _progress_payload(
    *,
    start: float,
    completed: int,
    total: int,
    seed: int,
    workers: int,
    n_events: int,
    current_route_index: int,
    current_route: tuple[int, int, int] | None,
    status: str,
) -> dict[str, Any]:
    elapsed = max(time.perf_counter() - start, 1e-12)
    rows_per_second = completed / elapsed if completed else 0.0
    remaining_rows = max(0, int(total) - int(completed))
    estimated_remaining_s = (
        remaining_rows / rows_per_second if rows_per_second > 0 else None
    )
    estimated_total_s = (
        elapsed + estimated_remaining_s if estimated_remaining_s is not None else None
    )
    return {
        "status": status,
        "seed": int(seed),
        "workers": int(workers),
        "n_events": int(n_events),
        "completed_route_particle_rows": int(completed),
        "route_particle_rows_per_seed": int(total),
        "remaining_route_particle_rows": int(remaining_rows),
        "current_route_index": int(current_route_index),
        "current_route": list(current_route) if current_route is not None else None,
        "elapsed_s": float(elapsed),
        "rows_per_second": float(rows_per_second),
        "particle_events_per_second": float(rows_per_second * int(n_events)),
        "estimated_remaining_s": (
            float(estimated_remaining_s)
            if estimated_remaining_s is not None and math.isfinite(estimated_remaining_s)
            else None
        ),
        "estimated_total_s": (
            float(estimated_total_s)
            if estimated_total_s is not None and math.isfinite(estimated_total_s)
            else None
        ),
        "estimated_remaining_readable": _readable_duration(estimated_remaining_s),
        "estimated_total_readable": _readable_duration(estimated_total_s),
    }


def _run_one_route(
    *,
    route: tuple[int, int, int],
    particles: list[Any],
    cfg: Any,
    optical_template: Any,
    workers: int,
    normalization_lane: str,
) -> list[dict[str, Any]]:
    wavelength_nm, width_nm, depth_nm = route
    baseline_channel = lane.case_baseline_channel(width_nm, depth_nm)
    e_sca_ref = None
    baseline_particle = BASELINE_PARTICLE
    if normalization_lane == "fixed_660_gold":
        e_sca_ref = _fixed_660_e_sca_ref(
            width_nm=width_nm,
            depth_nm=depth_nm,
            cfg=cfg,
            optical_template=optical_template,
        )
        baseline_particle = None
    return run_parameter_sweep(
        particle_types=particles,
        medium=WATER,
        width_list_m=np.array([float(width_nm) * 1e-9], dtype=float),
        depth_list_m=np.array([float(depth_nm) * 1e-9], dtype=float),
        wavelength_list_m=np.array([float(wavelength_nm) * 1e-9], dtype=float),
        optical_template=optical_template,
        sim_cfg=cfg,
        E_sca_ref=e_sca_ref,
        theta_grid_rad=THETA_GRID_RAD,
        baseline_particle=baseline_particle,
        baseline_channel=baseline_channel,
        verbose=False,
        n_workers=int(workers),
        medium_resolver=medium_for_particle,
        allow_partial=False,
    )


def _score_precomputed_route_results(
    *,
    route: tuple[int, int, int],
    particles: list[Any],
    cfg: Any,
    optical_template: Any,
    normalization_lane: str,
    raw_results: list[dict[str, Any]],
    fixed_e_sca_ref: float | None,
) -> list[dict[str, Any]]:
    wavelength_nm, width_nm, depth_nm = route
    skip_keys = {
        build_sweep_case_key(
            particle.name,
            float(wavelength_nm) * 1e-9,
            float(width_nm) * 1e-9,
            float(depth_nm) * 1e-9,
        )
        for particle in particles
    }
    baseline_particle = BASELINE_PARTICLE
    e_sca_ref = None
    if normalization_lane == "fixed_660_gold":
        baseline_particle = None
        e_sca_ref = fixed_e_sca_ref
    return run_parameter_sweep(
        particle_types=particles,
        medium=WATER,
        width_list_m=np.array([float(width_nm) * 1e-9], dtype=float),
        depth_list_m=np.array([float(depth_nm) * 1e-9], dtype=float),
        wavelength_list_m=np.array([float(wavelength_nm) * 1e-9], dtype=float),
        optical_template=optical_template,
        sim_cfg=cfg,
        E_sca_ref=e_sca_ref,
        theta_grid_rad=THETA_GRID_RAD,
        baseline_particle=baseline_particle,
        baseline_channel=lane.case_baseline_channel(width_nm, depth_nm),
        verbose=False,
        n_workers=1,
        medium_resolver=medium_for_particle,
        allow_partial=False,
        resume_results=raw_results,
        skip_case_keys=skip_keys,
    )


def _run_shared_dual_one_route(
    *,
    route: tuple[int, int, int],
    particles: list[Any],
    base_cfg: Any,
    optical_template: Any,
) -> dict[str, list[dict[str, Any]]]:
    wavelength_nm, width_nm, depth_nm = route
    optical = copy(optical_template)
    optical.wavelength_m = float(wavelength_nm) * 1e-9
    channel = lane.case_baseline_channel(width_nm, depth_nm)
    cfg_by_lane = {
        lane_name: _cfg_for_normalization_lane(base_cfg, lane_name)
        for lane_name in SINGLE_NORMALIZATION_LANES
    }
    fixed_e_sca_ref = _fixed_660_e_sca_ref(
        width_nm=width_nm,
        depth_nm=depth_nm,
        cfg=cfg_by_lane["fixed_660_gold"],
        optical_template=optical_template,
    )
    raw_by_lane: dict[str, list[dict[str, Any]]] = {
        lane_name: [] for lane_name in SINGLE_NORMALIZATION_LANES
    }
    intrinsic_cache: dict[Any, Any] = {}
    reference_cache: dict[Any, Any] = {}
    collection_operator_cache: dict[Any, Any] = {}
    for particle in particles:
        medium = medium_for_particle(particle)
        per_ref = _per_wavelength_e_sca_ref(
            wavelength_nm=wavelength_nm,
            width_nm=width_nm,
            depth_nm=depth_nm,
            medium=medium,
            cfg=cfg_by_lane["per_wavelength_gold"],
            optical_template=optical_template,
        )
        started = time.perf_counter()
        batches = run_single_case_batch_shared_event_normalization_views(
            particle,
            medium,
            channel,
            optical,
            cfg_by_lane,
            {
                "fixed_660_gold": fixed_e_sca_ref,
                "per_wavelength_gold": per_ref,
            },
            THETA_GRID_RAD,
            intrinsic_cache=intrinsic_cache,
            reference_cache=reference_cache,
            collection_operator_cache=collection_operator_cache,
        )
        elapsed = time.perf_counter() - started
        case_key = build_sweep_case_key(
            particle.name,
            optical.wavelength_m,
            channel.width_m,
            channel.depth_m,
        )
        for lane_name, batch in batches.items():
            raw_by_lane[lane_name].append(
                {
                    "case_key": case_key,
                    "particle_name": particle.name,
                    "wavelength_m": optical.wavelength_m,
                    "width_m": channel.width_m,
                    "depth_m": channel.depth_m,
                    "summary": batch["summary"],
                    "intrinsic": batch.get("intrinsic", {}),
                    "reference": batch.get("reference", {}),
                    "case_runtime_seconds": elapsed,
                }
            )
    return {
        lane_name: _score_precomputed_route_results(
            route=route,
            particles=particles,
            cfg=cfg_by_lane[lane_name],
            optical_template=optical_template,
            normalization_lane=lane_name,
            raw_results=raw_results,
            fixed_e_sca_ref=fixed_e_sca_ref,
        )
        for lane_name, raw_results in raw_by_lane.items()
    }


def _init_route_worker(
    particle_names: tuple[str, ...],
    cfg: Any,
    optical_template: Any,
    normalization_lane: str,
) -> None:
    global _ROUTE_WORKER_CONTEXT
    _configure_route_worker_env()
    _ROUTE_WORKER_CONTEXT = {
        "particles": [particle_from_name(name) for name in particle_names],
        "cfg": cfg,
        "optical_template": optical_template,
        "normalization_lane": normalization_lane,
    }


def _run_route_worker(
    route_index: int,
    route: tuple[int, int, int],
    *,
    n_events: int,
    seed: int,
    claim_level: str,
) -> dict[str, Any]:
    if _ROUTE_WORKER_CONTEXT is None:
        raise RuntimeError("route worker context has not been initialized")
    route_started = time.perf_counter()
    cfg = _ROUTE_WORKER_CONTEXT["cfg"]
    normalization_lane = str(_ROUTE_WORKER_CONTEXT["normalization_lane"])
    results = _run_one_route(
        route=route,
        particles=_ROUTE_WORKER_CONTEXT["particles"],
        cfg=cfg,
        optical_template=_ROUTE_WORKER_CONTEXT["optical_template"],
        workers=INNER_SWEEP_WORKERS_PER_ROUTE,
        normalization_lane=normalization_lane,
    )
    frame = lane.flatten_sweep_results(
        results,
        scenario_config_id=FROZEN_B_SCENARIO_ID,
        cfg=cfg,
        n_events=int(n_events),
        random_seed=int(seed),
        claim_level=claim_level,
    )
    frame = _add_normalization_columns(
        frame,
        normalization_lane=normalization_lane,
        cfg=cfg,
    )
    frame.insert(0, "route_index", int(route_index))
    diagnostic_frame = _diagnostic_scalar_frame(results)
    diagnostic_frame = _add_normalization_columns(
        diagnostic_frame,
        normalization_lane=normalization_lane,
        cfg=cfg,
    )
    diagnostic_frame.insert(0, "route_index", int(route_index))
    return {
        "route_index": int(route_index),
        "route": tuple(route),
        "frame": frame,
        "diagnostic_frame": diagnostic_frame,
        "route_elapsed_s": float(time.perf_counter() - route_started),
    }


def _run_shared_dual_route_worker(
    route_index: int,
    route: tuple[int, int, int],
    *,
    n_events: int,
    seed: int,
    claim_level: str,
) -> dict[str, Any]:
    if _ROUTE_WORKER_CONTEXT is None:
        raise RuntimeError("route worker context has not been initialized")
    route_started = time.perf_counter()
    cfg = _ROUTE_WORKER_CONTEXT["cfg"]
    results_by_lane = _run_shared_dual_one_route(
        route=route,
        particles=_ROUTE_WORKER_CONTEXT["particles"],
        base_cfg=cfg,
        optical_template=_ROUTE_WORKER_CONTEXT["optical_template"],
    )
    frames: dict[str, pd.DataFrame] = {}
    diagnostic_frames: dict[str, pd.DataFrame] = {}
    for lane_name, results in results_by_lane.items():
        lane_cfg = _cfg_for_normalization_lane(cfg, lane_name)
        frame = lane.flatten_sweep_results(
            results,
            scenario_config_id=FROZEN_B_SCENARIO_ID,
            cfg=lane_cfg,
            n_events=int(n_events),
            random_seed=int(seed),
            claim_level=claim_level,
        )
        frame = _add_normalization_columns(
            frame,
            normalization_lane=lane_name,
            cfg=lane_cfg,
        )
        frame = _add_shared_event_dual_columns(frame)
        frame.insert(0, "route_index", int(route_index))
        diagnostic_frame = _diagnostic_scalar_frame(results)
        diagnostic_frame = _add_normalization_columns(
            diagnostic_frame,
            normalization_lane=lane_name,
            cfg=lane_cfg,
        )
        diagnostic_frame = _add_shared_event_dual_columns(diagnostic_frame)
        diagnostic_frame.insert(0, "route_index", int(route_index))
        frames[lane_name] = frame
        diagnostic_frames[lane_name] = diagnostic_frame
    return {
        "route_index": int(route_index),
        "route": tuple(route),
        "frames": frames,
        "diagnostic_frames": diagnostic_frames,
        "route_elapsed_s": float(time.perf_counter() - route_started),
    }


def _append_frame_csv(path: Path, frame: pd.DataFrame, *, header: bool) -> None:
    frame.to_csv(path, mode="a", header=header, index=False)


def _run_route_jobs(
    *,
    routes: list[tuple[int, int, int]],
    particle_names: list[str],
    cfg: Any,
    optical_template: Any,
    route_workers: int,
    n_events: int,
    seed: int,
    claim_level: str,
    normalization_lane: str,
    max_pending_multiplier: int = 2,
):
    _configure_route_worker_env()
    particle_names_tuple = tuple(particle_names)
    if route_workers <= 1:
        _init_route_worker(
            particle_names_tuple,
            cfg,
            optical_template,
            normalization_lane,
        )
        for route_index, route in enumerate(routes, start=1):
            yield _run_route_worker(
                route_index,
                route,
                n_events=n_events,
                seed=seed,
                claim_level=claim_level,
            )
        return

    max_pending = max(1, int(route_workers) * max(1, int(max_pending_multiplier)))
    route_iter = iter(enumerate(routes, start=1))
    with ProcessPoolExecutor(
        max_workers=int(route_workers),
        initializer=_init_route_worker,
        initargs=(particle_names_tuple, cfg, optical_template, normalization_lane),
    ) as executor:
        pending = {}

        def _submit_next() -> bool:
            try:
                route_index, route = next(route_iter)
            except StopIteration:
                return False
            future = executor.submit(
                _run_route_worker,
                route_index,
                route,
                n_events=n_events,
                seed=seed,
                claim_level=claim_level,
            )
            pending[future] = (route_index, route)
            return True

        for _ in range(max_pending):
            if not _submit_next():
                break

        while pending:
            done, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                route_index, route = pending.pop(future)
                try:
                    yield future.result()
                except Exception as exc:  # pragma: no cover - operational path
                    raise RouteJobError(
                        route_index=route_index,
                        route=route,
                        original=exc,
                    ) from exc
                _submit_next()


def _run_shared_dual_route_jobs(
    *,
    routes: list[tuple[int, int, int]],
    particle_names: list[str],
    cfg: Any,
    optical_template: Any,
    route_workers: int,
    n_events: int,
    seed: int,
    claim_level: str,
    max_pending_multiplier: int = 2,
):
    _configure_route_worker_env()
    particle_names_tuple = tuple(particle_names)
    if route_workers <= 1:
        _init_route_worker(
            particle_names_tuple,
            cfg,
            optical_template,
            SHARED_DUAL_NORMALIZATION_LANE,
        )
        for route_index, route in enumerate(routes, start=1):
            yield _run_shared_dual_route_worker(
                route_index,
                route,
                n_events=n_events,
                seed=seed,
                claim_level=claim_level,
            )
        return

    max_pending = max(1, int(route_workers) * max(1, int(max_pending_multiplier)))
    route_iter = iter(enumerate(routes, start=1))
    with ProcessPoolExecutor(
        max_workers=int(route_workers),
        initializer=_init_route_worker,
        initargs=(
            particle_names_tuple,
            cfg,
            optical_template,
            SHARED_DUAL_NORMALIZATION_LANE,
        ),
    ) as executor:
        pending = {}

        def _submit_next() -> bool:
            try:
                route_index, route = next(route_iter)
            except StopIteration:
                return False
            future = executor.submit(
                _run_shared_dual_route_worker,
                route_index,
                route,
                n_events=n_events,
                seed=seed,
                claim_level=claim_level,
            )
            pending[future] = (route_index, route)
            return True

        for _ in range(max_pending):
            if not _submit_next():
                break

        while pending:
            done, _ = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                route_index, route = pending.pop(future)
                try:
                    yield future.result()
                except Exception as exc:  # pragma: no cover - operational path
                    raise RouteJobError(
                        route_index=route_index,
                        route=route,
                        original=exc,
                    ) from exc
                _submit_next()


def _run_routes_to_csv(
    *,
    routes: list[tuple[int, int, int]],
    particle_names: list[str],
    cfg: Any,
    optical_template: Any,
    route_workers: int,
    n_events: int,
    seed: int,
    claim_level: str,
    normalization_lane: str,
    elapsed_column: str,
    raw_path: Path,
    diagnostic_path: Path | None,
    start: float,
    total_rows: int,
    progress_path: Path | None = None,
    benchmark_seconds: float | None = None,
    allow_overwrite: bool = False,
) -> dict[str, Any]:
    if raw_path.exists() and not allow_overwrite:
        raise FileExistsError(
            f"refusing to overwrite existing raw output: {raw_path}; "
            "use --overwrite-output only after confirming this is intentional"
        )
    if raw_path.exists():
        raw_path.unlink()

    completed = 0
    completed_routes = 0
    next_route_to_flush = 1
    csv_header_needed = True
    diagnostic_header_needed = True
    buffered: dict[int, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []

    try:
        route_outputs = _run_route_jobs(
            routes=routes,
            particle_names=particle_names,
            cfg=cfg,
            optical_template=optical_template,
            route_workers=route_workers,
            n_events=n_events,
            seed=seed,
            claim_level=claim_level,
            normalization_lane=normalization_lane,
            max_pending_multiplier=1 if benchmark_seconds is not None else 2,
        )
        for route_output in route_outputs:
            route_index = int(route_output["route_index"])
            buffered[route_index] = route_output

            while next_route_to_flush in buffered:
                part = buffered.pop(next_route_to_flush)
                route = tuple(part["route"])
                frame = part["frame"].copy()
                frame[elapsed_column] = time.perf_counter() - start
                _append_frame_csv(raw_path, frame, header=csv_header_needed)
                csv_header_needed = False
                if diagnostic_path is not None:
                    diagnostic_frame = part["diagnostic_frame"].copy()
                    diagnostic_frame[elapsed_column] = time.perf_counter() - start
                    _append_frame_csv(
                        diagnostic_path,
                        diagnostic_frame,
                        header=diagnostic_header_needed,
                    )
                    diagnostic_header_needed = False
                completed += int(len(frame))
                completed_routes = int(next_route_to_flush)
                if progress_path is not None:
                    write_json_file(
                        progress_path,
                        _progress_payload(
                            start=start,
                            completed=completed,
                            total=total_rows,
                            seed=seed,
                            workers=route_workers,
                            n_events=n_events,
                            current_route_index=completed_routes,
                            current_route=route,
                            status="running",
                        ),
                    )
                print(
                    "completed route "
                    f"{completed_routes}/{len(routes)} {route}: "
                    f"{completed} rows in {time.perf_counter() - start:.1f}s "
                    f"(route worker {part['route_elapsed_s']:.1f}s)",
                    flush=True,
                )
                next_route_to_flush += 1

            if (
                benchmark_seconds is not None
                and completed > 0
                and time.perf_counter() - start >= float(benchmark_seconds)
            ):
                route_outputs.close()
                break
    except RouteJobError as exc:  # pragma: no cover - operational path
        failures.append(
            {
                "route_index": int(exc.route_index),
                "route": list(exc.route),
                "error_type": type(exc.original).__name__,
                "error": str(exc.original),
                "elapsed_s": time.perf_counter() - start,
            }
        )
        print(
            "route failed "
            f"{exc.route_index}/{len(routes)} {exc.route}: {exc.original}",
            flush=True,
        )
    except Exception as exc:  # pragma: no cover - operational path
        route = (
            routes[next_route_to_flush - 1]
            if next_route_to_flush - 1 < len(routes)
            else None
        )
        failures.append(
            {
                "route_index": int(next_route_to_flush),
                "route": list(route) if route is not None else None,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "elapsed_s": time.perf_counter() - start,
            }
        )
        print(
            "route failed "
            f"{next_route_to_flush}/{len(routes)} {route}: {exc}",
            flush=True,
        )

    return {
        "completed": int(completed),
        "completed_routes": int(completed_routes),
        "failures": failures,
    }


def _run_shared_dual_routes_to_csv(
    *,
    routes: list[tuple[int, int, int]],
    particle_names: list[str],
    cfg: Any,
    optical_template: Any,
    route_workers: int,
    n_events: int,
    seed: int,
    claim_level: str,
    elapsed_column: str,
    raw_paths: dict[str, Path],
    diagnostic_paths: dict[str, Path],
    start: float,
    total_rows: int,
    progress_path: Path | None = None,
    benchmark_seconds: float | None = None,
    allow_overwrite: bool = False,
) -> dict[str, Any]:
    for path in [*raw_paths.values(), *diagnostic_paths.values()]:
        if path.exists() and not allow_overwrite:
            raise FileExistsError(
                f"refusing to overwrite existing shared-dual output: {path}; "
                "use --overwrite-output only after confirming this is intentional"
            )
        if path.exists():
            path.unlink()

    completed = 0
    completed_routes = 0
    next_route_to_flush = 1
    csv_header_needed = {lane_name: True for lane_name in SINGLE_NORMALIZATION_LANES}
    diagnostic_header_needed = {
        lane_name: True for lane_name in SINGLE_NORMALIZATION_LANES
    }
    buffered: dict[int, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []

    try:
        route_outputs = _run_shared_dual_route_jobs(
            routes=routes,
            particle_names=particle_names,
            cfg=cfg,
            optical_template=optical_template,
            route_workers=route_workers,
            n_events=n_events,
            seed=seed,
            claim_level=claim_level,
        )
        for part in route_outputs:
            buffered[int(part["route_index"])] = part
            while next_route_to_flush in buffered:
                pending = buffered.pop(next_route_to_flush)
                route_elapsed = float(pending["route_elapsed_s"])
                for lane_name in SINGLE_NORMALIZATION_LANES:
                    frame = pending["frames"][lane_name].copy()
                    frame[elapsed_column] = time.perf_counter() - start
                    _append_frame_csv(
                        raw_paths[lane_name],
                        frame,
                        header=csv_header_needed[lane_name],
                    )
                    csv_header_needed[lane_name] = False
                    diagnostic_frame = pending["diagnostic_frames"][lane_name].copy()
                    diagnostic_frame[elapsed_column] = time.perf_counter() - start
                    _append_frame_csv(
                        diagnostic_paths[lane_name],
                        diagnostic_frame,
                        header=diagnostic_header_needed[lane_name],
                    )
                    diagnostic_header_needed[lane_name] = False
                completed += int(len(pending["frames"][SINGLE_NORMALIZATION_LANES[0]]))
                completed_routes = int(next_route_to_flush)
                if progress_path is not None:
                    progress = _progress_payload(
                        start=start,
                        completed=completed,
                        total=total_rows,
                        seed=seed,
                        workers=route_workers,
                        n_events=n_events,
                        current_route_index=int(pending["route_index"]),
                        current_route=tuple(pending["route"]),
                        status="running_shared_dual",
                    )
                    progress = _add_shared_event_dual_progress_fields(progress)
                    write_json_file(progress_path, progress)
                print(
                    "completed shared-dual route "
                    f"{pending['route_index']}/{len(routes)} {pending['route']}: "
                    f"{len(pending['frames'][SINGLE_NORMALIZATION_LANES[0]])} physical rows "
                    f"x {len(SINGLE_NORMALIZATION_LANES)} views in {route_elapsed:.1f}s "
                    f"(route worker {route_elapsed:.1f}s)",
                    flush=True,
                )
                next_route_to_flush += 1
                if (
                    benchmark_seconds is not None
                    and (time.perf_counter() - start) >= benchmark_seconds
                ):
                    raise TimeoutError("benchmark_seconds reached")
    except TimeoutError:
        pass
    except RouteJobError as exc:
        failures.append(
            {
                "route_index": exc.route_index,
                "route": list(exc.route),
                "error": str(exc.original),
            }
        )

    if progress_path is not None:
        status = "failed" if failures else "completed"
        if completed < total_rows and not failures:
            status = "partial"
        progress = _progress_payload(
            start=start,
            completed=completed,
            total=total_rows,
            seed=seed,
            workers=route_workers,
            n_events=n_events,
            current_route_index=completed_routes,
            current_route=routes[completed_routes - 1] if completed_routes else None,
            status=status,
        )
        progress = _add_shared_event_dual_progress_fields(progress)
        write_json_file(progress_path, progress)

    return {
        "completed": completed,
        "completed_routes": completed_routes,
        "failures": failures,
        "raw_paths": {lane: str(path) for lane, path in raw_paths.items()},
        "diagnostic_paths": {
            lane: str(path) for lane, path in diagnostic_paths.items()
        },
        "normalization_lane": SHARED_DUAL_NORMALIZATION_LANE,
        "normalization_views": list(SINGLE_NORMALIZATION_LANES),
        "shared_event_dual_normalization_used": True,
    }


def _guard_output_paths(paths: list[Path], *, allow_overwrite: bool) -> None:
    existing = [str(path) for path in paths if path.exists()]
    if existing and not allow_overwrite:
        joined = "\n  - ".join(existing)
        raise FileExistsError(
            "refusing to overwrite existing output files; use --overwrite-output "
            "only after confirming this is intentional:\n  - " + joined
        )


def _full_launch_arg_errors(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    if int(args.n_events) != FORMAL_FULL_GRID_EVENTS_PER_CASE:
        errors.append(
            f"full mode requires --n-events {FORMAL_FULL_GRID_EVENTS_PER_CASE}, "
            f"got {args.n_events}"
        )
    if int(args.seed) not in FORMAL_FULL_GRID_SEEDS:
        errors.append(
            f"full mode seed must be one of {list(FORMAL_FULL_GRID_SEEDS)}, "
            f"got {args.seed}"
        )
    if args.benchmark_seconds is not None:
        errors.append("--benchmark-seconds is trial-only and must not be used in full mode")
    if (
        args.normalization_lane != SHARED_DUAL_NORMALIZATION_LANE
        and not bool(args.accept_one_lane_primitive)
    ):
        errors.append(
            "full mode with a single normalization lane is a guarded fallback; "
            "use --normalization-lane shared_dual_gold for the canonical "
            "shared-event dual-view launch, or pass --accept-one-lane-primitive "
            "only after an explicit separate-lane recomputation decision"
        )
    return errors


def run_trial(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.normalization_lane == SHARED_DUAL_NORMALIZATION_LANE:
        raw_paths = {
            lane_name: output_dir / f"seed_{int(args.seed)}_trial_{lane_name}_rows.csv"
            for lane_name in SINGLE_NORMALIZATION_LANES
        }
        diagnostic_paths = {
            lane_name: output_dir
            / f"seed_{int(args.seed)}_trial_{lane_name}_diagnostic_rows.csv"
            for lane_name in SINGLE_NORMALIZATION_LANES
        }
        guard_paths = [
            output_dir / "run_manifest.json",
            output_dir / "runtime_estimate.json",
            *raw_paths.values(),
            *diagnostic_paths.values(),
        ]
    else:
        raw_path = output_dir / f"seed_{int(args.seed)}_trial_completed_rows.csv"
        diagnostic_path = output_dir / f"seed_{int(args.seed)}_trial_diagnostic_rows.csv"
        guard_paths = [
            output_dir / "run_manifest.json",
            output_dir / "runtime_estimate.json",
            raw_path,
            diagnostic_path,
        ]
    _guard_output_paths(
        guard_paths,
        allow_overwrite=bool(args.overwrite_output),
    )
    scope = load_and_validate_source(Path(args.route_source), particle_scope=args.particle_scope)
    base_cfg, optical_template = build_frozen_b_cfg(args.n_events, args.seed)
    cfg = _cfg_for_normalization_lane(base_cfg, args.normalization_lane)
    _write_manifest(
        output_dir=output_dir,
        args=args,
        scope=scope,
        cfg=cfg,
        run_kind="lens_b_ev_gold_fullgrid_trial",
        optical_template=optical_template,
    )

    start = time.perf_counter()
    route_workers = _resolve_route_worker_count(args.workers)
    if args.normalization_lane == SHARED_DUAL_NORMALIZATION_LANE:
        run_state = _run_shared_dual_routes_to_csv(
            routes=scope.routes,
            particle_names=scope.particle_names,
            cfg=cfg,
            optical_template=optical_template,
            route_workers=route_workers,
            n_events=int(args.n_events),
            seed=int(args.seed),
            claim_level="paper_reproduction_lens_b_frozen_parameter_trial_shared_dual",
            elapsed_column="benchmark_elapsed_s_at_route_complete",
            raw_paths=raw_paths,
            diagnostic_paths=diagnostic_paths,
            start=start,
            total_rows=scope.route_particle_rows_per_seed,
            benchmark_seconds=float(args.benchmark_seconds),
            allow_overwrite=bool(args.overwrite_output),
        )
    else:
        run_state = _run_routes_to_csv(
            routes=scope.routes,
            particle_names=scope.particle_names,
            cfg=cfg,
            optical_template=optical_template,
            route_workers=route_workers,
            n_events=int(args.n_events),
            seed=int(args.seed),
            claim_level="paper_reproduction_lens_b_frozen_parameter_trial",
            normalization_lane=args.normalization_lane,
            elapsed_column="benchmark_elapsed_s_at_route_complete",
            raw_path=raw_path,
            diagnostic_path=diagnostic_path,
            start=start,
            total_rows=scope.route_particle_rows_per_seed,
            benchmark_seconds=float(args.benchmark_seconds),
            allow_overwrite=bool(args.overwrite_output),
        )

    elapsed = time.perf_counter() - start
    completed = int(run_state["completed"])
    completed_particle_events = int(completed * int(args.n_events))
    rows_per_second = completed / elapsed if elapsed > 0 else 0.0
    events_per_second = completed_particle_events / elapsed if elapsed > 0 else 0.0
    est_1 = (
        scope.route_particle_rows_per_seed / rows_per_second
        if rows_per_second > 0
        else 0.0
    )
    est_3 = 3.0 * est_1 if est_1 > 0 else 0.0
    output_bytes = _directory_size_bytes(output_dir)
    bytes_per_row = output_bytes / completed if completed > 0 else None
    disk_1_gb = (
        bytes_per_row * scope.route_particle_rows_per_seed / (1024.0**3)
        if bytes_per_row is not None
        else None
    )
    disk_3_gb = disk_1_gb * 3.0 if disk_1_gb is not None else None
    notes: list[str] = []
    if completed < 5:
        notes.append(
            "unreliable_estimate_fewer_than_5_route_particle_rows_completed_in_trial"
        )
    if run_state["failures"]:
        notes.append("trial_stopped_after_failure")
    notes.append(
        "gamma/snr_scale/snr_response_exp preserved as metadata-only; see run_manifest.json"
    )

    estimate = {
        "workers": int(route_workers),
        "inner_sweep_workers_per_route": INNER_SWEEP_WORKERS_PER_ROUTE,
        "n_events": int(args.n_events),
        "trial_seed": int(args.seed),
        "trial_elapsed_s": float(elapsed),
        "completed_route_particle_rows": completed,
        "completed_routes": int(run_state["completed_routes"]),
        "completed_particle_events": completed_particle_events,
        "route_particle_rows_per_seed": int(scope.route_particle_rows_per_seed),
        "rows_per_second": float(rows_per_second),
        "particle_events_per_second": float(events_per_second),
        "estimated_seconds_1_seed": float(est_1),
        "estimated_seconds_3_seeds": float(est_3),
        "estimated_readable_1_seed": _readable_duration(est_1),
        "estimated_readable_3_seeds": _readable_duration(est_3),
        "estimated_disk_gb_1_seed": disk_1_gb,
        "estimated_disk_gb_3_seeds": disk_3_gb,
        "safety_factor": 1.15,
        "safety_estimated_seconds_1_seed": float(est_1 * 1.15) if est_1 else 0.0,
        "safety_estimated_seconds_3_seeds": float(est_3 * 1.15) if est_3 else 0.0,
        "safety_estimated_readable_1_seed": _readable_duration(est_1 * 1.15),
        "safety_estimated_readable_3_seeds": _readable_duration(est_3 * 1.15),
        "safety_estimated_disk_gb_1_seed": (
            disk_1_gb * 1.15 if disk_1_gb is not None else None
        ),
        "safety_estimated_disk_gb_3_seeds": (
            disk_3_gb * 1.15 if disk_3_gb is not None else None
        ),
        "trial_output_bytes": int(output_bytes),
        "bytes_per_completed_row": bytes_per_row,
        "failures": run_state["failures"],
        "notes": notes,
    }
    write_json_file(output_dir / "runtime_estimate.json", estimate)
    print(json.dumps(json_safe(estimate), indent=2, sort_keys=True), flush=True)
    return estimate


def run_full(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    progress_path = output_dir / f"seed_{int(args.seed)}_progress.json"
    summary_path = output_dir / f"seed_{int(args.seed)}_run_summary.json"
    if args.normalization_lane == SHARED_DUAL_NORMALIZATION_LANE:
        raw_paths = {
            lane_name: output_dir / f"seed_{int(args.seed)}_{lane_name}_raw_rows.csv"
            for lane_name in SINGLE_NORMALIZATION_LANES
        }
        diagnostic_paths = {
            lane_name: output_dir
            / f"seed_{int(args.seed)}_{lane_name}_diagnostic_rows.csv"
            for lane_name in SINGLE_NORMALIZATION_LANES
        }
        guard_paths = [
            output_dir / "run_manifest.json",
            *raw_paths.values(),
            *diagnostic_paths.values(),
            progress_path,
            summary_path,
        ]
    else:
        raw_path = output_dir / f"seed_{int(args.seed)}_raw_rows.csv"
        diagnostic_path = output_dir / f"seed_{int(args.seed)}_diagnostic_rows.csv"
        guard_paths = [
            output_dir / "run_manifest.json",
            raw_path,
            diagnostic_path,
            progress_path,
            summary_path,
        ]
    _guard_output_paths(
        guard_paths,
        allow_overwrite=bool(args.overwrite_output),
    )
    scope = load_and_validate_source(Path(args.route_source), particle_scope=args.particle_scope)
    base_cfg, optical_template = build_frozen_b_cfg(args.n_events, args.seed)
    cfg = _cfg_for_normalization_lane(base_cfg, args.normalization_lane)
    _write_manifest(
        output_dir=output_dir,
        args=args,
        scope=scope,
        cfg=cfg,
        run_kind="lens_b_ev_gold_fullgrid_full_1seed",
        optical_template=optical_template,
    )

    start = time.perf_counter()
    route_workers = _resolve_route_worker_count(args.workers)

    initial_progress = _progress_payload(
        start=start,
        completed=0,
        total=scope.route_particle_rows_per_seed,
        seed=args.seed,
        workers=route_workers,
        n_events=args.n_events,
        current_route_index=0,
        current_route=None,
        status=(
            "running_shared_dual"
            if args.normalization_lane == SHARED_DUAL_NORMALIZATION_LANE
            else "running"
        ),
    )
    if args.normalization_lane == SHARED_DUAL_NORMALIZATION_LANE:
        initial_progress = _add_shared_event_dual_progress_fields(initial_progress)
    write_json_file(progress_path, initial_progress)

    if args.normalization_lane == SHARED_DUAL_NORMALIZATION_LANE:
        run_state = _run_shared_dual_routes_to_csv(
            routes=scope.routes,
            particle_names=scope.particle_names,
            cfg=cfg,
            optical_template=optical_template,
            route_workers=route_workers,
            n_events=int(args.n_events),
            seed=int(args.seed),
            claim_level="paper_reproduction_lens_b_frozen_parameter_full_1seed_shared_dual",
            elapsed_column="run_elapsed_s_at_route_complete",
            raw_paths=raw_paths,
            diagnostic_paths=diagnostic_paths,
            start=start,
            total_rows=scope.route_particle_rows_per_seed,
            progress_path=progress_path,
            allow_overwrite=bool(args.overwrite_output),
        )
    else:
        run_state = _run_routes_to_csv(
            routes=scope.routes,
            particle_names=scope.particle_names,
            cfg=cfg,
            optical_template=optical_template,
            route_workers=route_workers,
            n_events=int(args.n_events),
            seed=int(args.seed),
            claim_level="paper_reproduction_lens_b_frozen_parameter_full_1seed",
            normalization_lane=args.normalization_lane,
            elapsed_column="run_elapsed_s_at_route_complete",
            raw_path=raw_path,
            diagnostic_path=diagnostic_path,
            start=start,
            total_rows=scope.route_particle_rows_per_seed,
            progress_path=progress_path,
            allow_overwrite=bool(args.overwrite_output),
        )

    completed = int(run_state["completed"])
    completed_routes = int(run_state["completed_routes"])
    fully_complete = (
        not run_state["failures"]
        and completed == int(scope.route_particle_rows_per_seed)
        and completed_routes == len(scope.routes)
    )
    status = "completed" if fully_complete else "failed_incomplete"
    progress = _progress_payload(
        start=start,
        completed=completed,
        total=scope.route_particle_rows_per_seed,
        seed=args.seed,
        workers=route_workers,
        n_events=args.n_events,
        current_route_index=completed_routes,
        current_route=scope.routes[completed_routes - 1] if completed_routes else None,
        status=status,
    )
    if args.normalization_lane == SHARED_DUAL_NORMALIZATION_LANE:
        progress = _add_shared_event_dual_progress_fields(progress)
    output_bytes = _directory_size_bytes(output_dir)
    summary = {
        **progress,
        "inner_sweep_workers_per_route": INNER_SWEEP_WORKERS_PER_ROUTE,
        "completed_particle_events": int(completed * int(args.n_events)),
        "expected_route_particle_rows_per_seed": int(scope.route_particle_rows_per_seed),
        "expected_route_count": int(len(scope.routes)),
        "completion_check_passed": bool(fully_complete),
        "raw_rows_path": (
            {lane: str(path) for lane, path in raw_paths.items()}
            if args.normalization_lane == SHARED_DUAL_NORMALIZATION_LANE
            else str(raw_path)
        ),
        "diagnostic_rows_path": (
            {lane: str(path) for lane, path in diagnostic_paths.items()}
            if args.normalization_lane == SHARED_DUAL_NORMALIZATION_LANE
            else str(diagnostic_path)
        ),
        "shared_event_dual_normalization_used": bool(
            args.normalization_lane == SHARED_DUAL_NORMALIZATION_LANE
        ),
        "output_bytes": int(output_bytes),
        "output_gb": float(output_bytes / (1024.0**3)),
        "failures": run_state["failures"],
        "notes": [
            f"Full run primitive is 1 seed only: {int(args.seed)}.",
            "Canonical 3-seed campaign requires seeds 11, 22, and 33.",
            (
                "This run emits both normalization views from one shared physical "
                "event stream."
                if args.normalization_lane == SHARED_DUAL_NORMALIZATION_LANE
                else "This runner executes one normalization lane per invocation; dual normalization views require shared-event handling or an explicitly accepted separate-lane recomputation workaround."
            ),
            "Workers run route-level jobs; each route uses a serial inner sweep to avoid nested process pools.",
            "Raw CSV is appended in route-index order instead of rewritten after every route.",
            "488/532 retained in raw/control outputs; final recommendation conclusions must use 404/660 only.",
            "EV recommendation must use EV rows only; gold rows are anchor / Tsuyama consistency diagnostics.",
            "gamma/snr_scale/snr_response_exp preserved as metadata-only; see run_manifest.json.",
            f"normalization_lane={args.normalization_lane}.",
        ],
    }
    write_json_file(progress_path, progress)
    write_json_file(summary_path, summary)
    print(json.dumps(json_safe(summary), indent=2, sort_keys=True), flush=True)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Lens-B frozen-parameter EV+gold full-grid runner."
    )
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--n-events", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--benchmark-seconds", type=float, default=None)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--overwrite-output",
        action="store_true",
        help="Allow replacing existing output files in --output-dir.",
    )
    parser.add_argument("--particle-scope", required=True, choices=["ev_gold"])
    parser.add_argument("--route-source", required=True)
    parser.add_argument(
        "--normalization-lane",
        required=True,
        choices=NORMALIZATION_LANES,
        help=(
            "per_wavelength_gold keeps the Stage B6 Tsuyama/gold diagnostic lane; "
            "fixed_660_gold runs the Stage B7 EV cross-wavelength decision lane; "
            "shared_dual_gold emits both views from one shared physical event stream."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=["trial", "full"],
        default="trial",
        help=(
            "trial runs a small bounded rehearsal; full runs one formal seed and "
            "either one guarded normalization lane or the shared_dual_gold dual-view path."
        ),
    )
    parser.add_argument(
        "--accept-one-lane-primitive",
        action="store_true",
        help=(
            "Required for --mode full when using fixed_660_gold or "
            "per_wavelength_gold. Not required for shared_dual_gold."
        ),
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.mode == "trial" and args.benchmark_seconds is None:
        parser.error("--benchmark-seconds is required in trial mode")
    if args.mode == "full":
        errors = _full_launch_arg_errors(args)
        if errors:
            parser.error("; ".join(errors))
    if args.mode == "trial":
        run_trial(args)
        return
    if args.mode == "full":
        summary = run_full(args)
        if summary.get("status") != "completed":
            raise SystemExit(
                "Full run did not complete cleanly; see seed run summary JSON"
            )
        return
    raise AssertionError(f"Unhandled mode: {args.mode}")


if __name__ == "__main__":
    main()
