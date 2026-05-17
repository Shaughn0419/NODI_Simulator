from __future__ import annotations

import argparse
import contextlib
import json
import re
import shutil
import statistics
import sys
import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
for candidate in (str(PROJECT_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from nodi_simulator.dashboard.precompute import (  # noqa: E402
    build_precompute_sim_cfg,
    precompute_sweep,
)
from nodi_simulator.dashboard.config import (  # noqa: E402
    GRID_CONFIGS,
    get_precompute_particles,
)
from nodi_simulator.data_objects import EVENT_BLOCK_RNG_ORDER_OPTIONS  # noqa: E402
from tools._common import write_csv_records, write_json_file  # noqa: E402

CASE_KEY_COLUMNS = (
    "particle_name",
    "wavelength_nm",
    "width_nm",
    "depth_nm",
)
GRID_DIMENSION_KEYS = (
    "wavelength_list_m",
    "width_list_m",
    "depth_list_m",
)
GRID_SAMPLE_PRIORITY = (
    "wavelength_list_m",
    "width_list_m",
    "depth_list_m",
)
BIAS_METRICS = (
    "detection_rate",
    "stable_detection_rate",
    "mean_peak_height",
    "mean_peak_width_s",
)
METRIC_COLUMN_ALIASES = {
    "mean_peak_width_s": (
        ("mean_peak_width_s", 1.0),
        ("mean_peak_width_ms", 1.0e-3),
    ),
}
RATE_TOLERANCE = 0.05
HEIGHT_REL_TOLERANCE = 0.10
WIDTH_REL_TOLERANCE = 0.10
MIN_RELATIVE_IMPROVEMENT_TO_CHANGE_DEFAULT = 0.05
EPS = 1e-15


@dataclass(frozen=True)
class BenchmarkVariant:
    name: str
    vectorized_event_engine: str
    event_block_size: int
    event_block_rng_order: str = "event_loop_order"


@dataclass(frozen=True)
class BenchmarkGridPlan:
    base_grid: str
    run_grid: str
    events_per_case: int
    sample_case_limit: int | None
    actual_cases: int
    particle_count: int
    selected_counts: dict[str, int]


def _safe_tag(raw_tag: str) -> str:
    tag = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(raw_tag)).strip("._-")
    return tag or "event_engine_benchmark"


def _variant_tag(tag: str, variant: BenchmarkVariant) -> str:
    rng_suffix = (
        ""
        if variant.event_block_rng_order == "event_loop_order"
        else f"_rng_{variant.event_block_rng_order}"
    )
    return _safe_tag(
        f"{tag}_{variant.vectorized_event_engine}_b{variant.event_block_size}"
        f"{rng_suffix}"
    )


def _artifact_prefix(grid: str, variant_tag: str) -> str:
    return f"{grid}_{variant_tag}"


def _relative_delta(candidate: float, baseline: float) -> float:
    if abs(baseline) <= EPS:
        return 0.0 if abs(candidate) <= EPS else float("inf")
    return float((candidate - baseline) / abs(baseline))


def _metric_series(df: pd.DataFrame, metric: str) -> pd.Series:
    suffix = ""
    logical_metric = metric
    for candidate_suffix in ("_baseline", "_candidate"):
        if metric.endswith(candidate_suffix):
            logical_metric = metric[: -len(candidate_suffix)]
            suffix = candidate_suffix
            break
    aliases = METRIC_COLUMN_ALIASES.get(logical_metric, ((logical_metric, 1.0),))
    for column, scale in aliases:
        resolved_column = f"{column}{suffix}"
        if resolved_column in df.columns:
            return df[resolved_column].fillna(0.0).astype(float) * float(scale)
    raise KeyError(f"Missing benchmark metric column for {metric}: {aliases}")


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _value_counts(series: pd.Series) -> dict[str, int]:
    counts = series.fillna("<none>").astype(str).value_counts(dropna=False)
    return {str(key): int(value) for key, value in counts.items()}


def _spread_indices(length: int, count: int) -> list[int]:
    """Pick stable, evenly spread indices while preserving endpoints when possible."""
    length = int(length)
    count = int(count)
    if length <= 0:
        raise ValueError("Cannot sample from an empty benchmark dimension")
    if count <= 0:
        raise ValueError("Benchmark sample counts must be positive")
    if count >= length:
        return list(range(length))
    if count == 1:
        return [length // 2]

    raw_indices = [
        int(round(idx * (length - 1) / (count - 1)))
        for idx in range(count)
    ]
    selected: list[int] = []
    for raw_idx in raw_indices:
        clamped = min(max(raw_idx, 0), length - 1)
        if clamped not in selected:
            selected.append(clamped)
    if len(selected) < count:
        for idx in range(length):
            if idx not in selected:
                selected.append(idx)
            if len(selected) == count:
                break
    return sorted(selected[:count])


def _select_spread_values(values: Any, count: int) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    indices = _spread_indices(len(arr), count)
    return np.asarray([arr[idx] for idx in indices], dtype=float)


def _product(values: Mapping[str, int]) -> int:
    product = 1
    for value in values.values():
        product *= int(value)
    return product


def _resolve_sampled_dimension_counts(
    *,
    base_grid: Mapping[str, Any],
    particle_count: int,
    sample_case_limit: int | None,
) -> dict[str, int]:
    full_counts = {
        key: int(len(base_grid[key]))
        for key in GRID_DIMENSION_KEYS
    }
    if sample_case_limit is None:
        return dict(full_counts)

    budget_per_particle = max(1, int(sample_case_limit) // max(1, int(particle_count)))
    selected_counts = dict.fromkeys(GRID_DIMENSION_KEYS, 1)
    for key in GRID_SAMPLE_PRIORITY:
        while selected_counts[key] < full_counts[key]:
            proposed_counts = dict(selected_counts)
            proposed_counts[key] += 1
            if _product(proposed_counts) > budget_per_particle:
                break
            selected_counts[key] += 1
    return selected_counts


def _build_benchmark_grid_config(
    *,
    base_grid: Mapping[str, Any],
    events_per_case: int,
    particle_count: int,
    sample_case_limit: int | None,
) -> tuple[dict[str, Any], int, dict[str, int]]:
    if int(events_per_case) <= 0:
        raise ValueError(f"events_per_case must be positive, got {events_per_case}")
    if sample_case_limit is not None and int(sample_case_limit) <= 0:
        raise ValueError(f"sample_case_limit must be positive, got {sample_case_limit}")

    selected_counts = _resolve_sampled_dimension_counts(
        base_grid=base_grid,
        particle_count=particle_count,
        sample_case_limit=sample_case_limit,
    )
    grid_config = {
        **dict(base_grid),
        "n_events": int(events_per_case),
    }
    for key, count in selected_counts.items():
        grid_config[key] = _select_spread_values(base_grid[key], count)
    actual_cases = int(max(1, particle_count) * _product(selected_counts))
    return grid_config, actual_cases, selected_counts


def _install_benchmark_grid(
    *,
    base_grid_name: str,
    particle_profile: str,
    tag: str,
    events_per_case: int | None,
    sample_case_limit: int | None,
) -> BenchmarkGridPlan:
    if base_grid_name not in GRID_CONFIGS:
        raise ValueError(
            f"Unknown grid: {base_grid_name}. Available: {sorted(GRID_CONFIGS)}"
        )
    base_grid = GRID_CONFIGS[base_grid_name]
    particle_count = len(get_precompute_particles(particle_profile))
    resolved_events_per_case = int(
        base_grid["n_events"] if events_per_case is None else events_per_case
    )
    needs_benchmark_grid = (
        events_per_case is not None
        or sample_case_limit is not None
    )
    if not needs_benchmark_grid:
        selected_counts = {
            key: int(len(base_grid[key]))
            for key in GRID_DIMENSION_KEYS
        }
        return BenchmarkGridPlan(
            base_grid=base_grid_name,
            run_grid=base_grid_name,
            events_per_case=resolved_events_per_case,
            sample_case_limit=None,
            actual_cases=int(max(1, particle_count) * _product(selected_counts)),
            particle_count=particle_count,
            selected_counts=selected_counts,
        )

    grid_config, actual_cases, selected_counts = _build_benchmark_grid_config(
        base_grid=base_grid,
        events_per_case=resolved_events_per_case,
        particle_count=particle_count,
        sample_case_limit=sample_case_limit,
    )
    run_grid = _safe_tag(f"{base_grid_name}_benchmark_{tag}")
    GRID_CONFIGS[run_grid] = grid_config
    return BenchmarkGridPlan(
        base_grid=base_grid_name,
        run_grid=run_grid,
        events_per_case=resolved_events_per_case,
        sample_case_limit=sample_case_limit,
        actual_cases=actual_cases,
        particle_count=particle_count,
        selected_counts=selected_counts,
    )


def _load_variant_outputs(
    *,
    output_dir: Path,
    grid: str,
    variant_tag: str,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    prefix = _artifact_prefix(grid, variant_tag)
    summary_csv = output_dir / f"{prefix}_summary.csv"
    meta_json = output_dir / f"{prefix}_meta.json"
    if not summary_csv.exists():
        raise FileNotFoundError(f"Missing benchmark summary CSV: {summary_csv}")
    if not meta_json.exists():
        raise FileNotFoundError(f"Missing benchmark metadata JSON: {meta_json}")
    return pd.read_csv(summary_csv), _read_json(meta_json)


def _run_variant(
    *,
    variant: BenchmarkVariant,
    tag: str,
    grid: str,
    particle_profile: str,
    output_dir: Path,
    workers: int,
    progress_interval_s: float,
) -> dict[str, Any]:
    variant_tag = _variant_tag(tag, variant)
    log_path = output_dir / f"{_artifact_prefix(grid, variant_tag)}.log"
    output_dir.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    with (
        log_path.open("w", encoding="utf-8") as log_handle,
        contextlib.redirect_stdout(log_handle),
        contextlib.redirect_stderr(log_handle),
    ):
        precompute_sweep(
            grid_name=grid,
            config_tag=variant_tag,
            particle_profile=particle_profile,
            output_dir=str(output_dir),
            n_workers=workers,
            save_freeze_probe_report=False,
            progress_interval_s=progress_interval_s,
            resume=False,
            checkpoint_enabled=True,
            checkpoint_batch_size=32,
            checkpoint_flush_interval_s=30.0,
            artifact_profile="minimal",
            vectorized_event_engine=variant.vectorized_event_engine,
            event_block_size=variant.event_block_size,
            event_block_rng_order=variant.event_block_rng_order,
            include_diffusion=True,
        )
    wall_time_s = float(time.perf_counter() - start)
    df, meta = _load_variant_outputs(
        output_dir=output_dir,
        grid=grid,
        variant_tag=variant_tag,
    )
    row_count = int(len(df))
    completion = meta.get("sweep_completion_policy", {})
    engine_counts = _value_counts(df["vectorized_event_engine_used"])
    fallback_counts = _value_counts(df["vectorized_event_engine_fallback_reason"])
    return {
        "name": variant.name,
        "variant_tag": variant_tag,
        "vectorized_event_engine": variant.vectorized_event_engine,
        "event_block_size": int(variant.event_block_size),
        "event_block_rng_order": variant.event_block_rng_order,
        "wall_time_s": wall_time_s,
        "cases": row_count,
        "cases_per_second": float(row_count / wall_time_s) if wall_time_s > 0 else None,
        "completion_status": completion.get("completion_status"),
        "expected_total_cases": completion.get("expected_total_cases"),
        "saved_case_count": completion.get("saved_case_count"),
        "engine_used_counts": engine_counts,
        "fallback_counts": fallback_counts,
        "log_path": str(log_path),
    }


def _compare_to_baseline(
    *,
    baseline_df: pd.DataFrame,
    candidate_df: pd.DataFrame,
) -> dict[str, Any]:
    merged = baseline_df.merge(
        candidate_df,
        on=list(CASE_KEY_COLUMNS),
        suffixes=("_baseline", "_candidate"),
        how="inner",
        validate="one_to_one",
    )
    if len(merged) != len(baseline_df) or len(merged) != len(candidate_df):
        raise ValueError(
            "Benchmark variants do not have matching case keys: "
            f"baseline={len(baseline_df)}, candidate={len(candidate_df)}, "
            f"matched={len(merged)}"
        )
    payload: dict[str, Any] = {"matched_cases": int(len(merged))}
    for metric in BIAS_METRICS:
        base = _metric_series(merged, f"{metric}_baseline")
        cand = _metric_series(merged, f"{metric}_candidate")
        delta = cand - base
        rel_delta = [
            _relative_delta(float(cand_value), float(base_value))
            for cand_value, base_value in zip(cand, base)
        ]
        finite_rel = [abs(value) for value in rel_delta if pd.notna(value)]
        finite_rel = [value for value in finite_rel if value != float("inf")]
        payload[f"mean_abs_delta_{metric}"] = float(delta.abs().mean())
        payload[f"max_abs_delta_{metric}"] = float(delta.abs().max())
        payload[f"max_abs_relative_delta_{metric}"] = (
            float(max(finite_rel)) if finite_rel else 0.0
        )
    gate_base = merged["engineering_gate_passed_baseline"].fillna(False).astype(bool)
    gate_cand = merged["engineering_gate_passed_candidate"].fillna(False).astype(bool)
    payload["engineering_gate_agreement_rate"] = float((gate_base == gate_cand).mean())
    return payload


def _passes_bias_gate(comparison: dict[str, Any]) -> bool:
    return bool(
        comparison["max_abs_delta_detection_rate"] <= RATE_TOLERANCE
        and comparison["max_abs_delta_stable_detection_rate"] <= RATE_TOLERANCE
        and comparison["max_abs_relative_delta_mean_peak_height"] <= HEIGHT_REL_TOLERANCE
        and comparison["max_abs_relative_delta_mean_peak_width_s"] <= WIDTH_REL_TOLERANCE
        and comparison["engineering_gate_agreement_rate"] >= 1.0
    )


def _select_recommendation(
    records: list[dict[str, Any]],
    comparisons: dict[str, dict[str, Any]],
    *,
    baseline_name: str,
    current_default_engine: str,
    current_default_block_size: int,
    current_default_rng_order: str,
) -> dict[str, Any]:
    baseline = next(record for record in records if record["name"] == baseline_name)
    eligible: list[dict[str, Any]] = []
    for record in records:
        if record["name"] == baseline_name:
            continue
        comparison = comparisons.get(record["name"], {})
        if record.get("completion_status") != "complete":
            continue
        if not _passes_bias_gate(comparison):
            continue
        fallback_counts = dict(record.get("fallback_counts") or {})
        if any(key != "<none>" for key in fallback_counts):
            continue
        speedup = float(baseline["wall_time_s"]) / float(record["wall_time_s"])
        candidate = {**record, "speedup_vs_scalar": speedup}
        eligible.append(candidate)

    if not eligible:
        return {
            "recommended_engine": None,
            "recommended_block_size": None,
            "decision": "no_candidate_passed",
        }

    fastest = min(eligible, key=lambda item: float(item["wall_time_s"]))
    current_default = next(
        (
            item
            for item in eligible
            if item["vectorized_event_engine"] == current_default_engine
            and int(item["event_block_size"]) == current_default_block_size
            and item.get("event_block_rng_order", "event_loop_order")
            == current_default_rng_order
        ),
        None,
    )
    decision = "keep_current_default"
    recommended = current_default
    if current_default is None:
        decision = "adopt_fastest_candidate"
        recommended = fastest
    else:
        current_time = float(current_default["wall_time_s"])
        improvement = (current_time - float(fastest["wall_time_s"])) / max(
            current_time,
            EPS,
        )
        if improvement >= MIN_RELATIVE_IMPROVEMENT_TO_CHANGE_DEFAULT:
            decision = "adopt_fastest_candidate"
            recommended = fastest

    return {
        "recommended_engine": (
            None if recommended is None else recommended["vectorized_event_engine"]
        ),
        "recommended_block_size": (
            None if recommended is None else int(recommended["event_block_size"])
        ),
        "recommended_event_block_rng_order": (
            None
            if recommended is None
            else recommended.get("event_block_rng_order", "event_loop_order")
        ),
        "decision": decision,
        "fastest_passing_engine": fastest["vectorized_event_engine"],
        "fastest_passing_block_size": int(fastest["event_block_size"]),
        "fastest_passing_event_block_rng_order": fastest.get(
            "event_block_rng_order",
            "event_loop_order",
        ),
        "fastest_passing_wall_time_s": float(fastest["wall_time_s"]),
        "fastest_passing_speedup_vs_scalar": float(fastest["speedup_vs_scalar"]),
        "current_default_engine": current_default_engine,
        "current_default_block_size": int(current_default_block_size),
        "current_default_event_block_rng_order": current_default_rng_order,
        "min_relative_improvement_to_change_default": (
            MIN_RELATIVE_IMPROVEMENT_TO_CHANGE_DEFAULT
        ),
    }


def _aggregate_count_dict(records: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        for item_key, item_count in dict(record.get(key) or {}).items():
            counts[str(item_key)] = counts.get(str(item_key), 0) + int(item_count)
    return counts


def _aggregate_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        by_name.setdefault(str(record["name"]), []).append(record)

    aggregate: list[dict[str, Any]] = []
    for name, group in by_name.items():
        first = group[0]
        wall_times = [float(item["wall_time_s"]) for item in group]
        cases_values = [int(item["cases"]) for item in group]
        median_wall_time = float(statistics.median(wall_times))
        median_cases = int(statistics.median(cases_values))
        completion_statuses = {str(item.get("completion_status")) for item in group}
        completion_status = (
            "complete" if completion_statuses == {"complete"} else "mixed_or_incomplete"
        )
        aggregate.append(
            {
                "name": name,
                "variant_tag": str(first["variant_tag"]),
                "vectorized_event_engine": str(first["vectorized_event_engine"]),
                "event_block_size": int(first["event_block_size"]),
                "event_block_rng_order": str(
                    first.get("event_block_rng_order", "event_loop_order")
                ),
                "wall_time_s": median_wall_time,
                "wall_time_s_values": wall_times,
                "wall_time_s_min": float(min(wall_times)),
                "wall_time_s_max": float(max(wall_times)),
                "repeat_count": len(group),
                "cases": median_cases,
                "cases_per_second": (
                    float(median_cases / median_wall_time)
                    if median_wall_time > 0 else None
                ),
                "completion_status": completion_status,
                "expected_total_cases": int(first["expected_total_cases"]),
                "saved_case_count": median_cases,
                "engine_used_counts": _aggregate_count_dict(
                    group,
                    "engine_used_counts",
                ),
                "fallback_counts": _aggregate_count_dict(group, "fallback_counts"),
                "log_path": str(first["log_path"]),
            }
        )
    return aggregate


def _aggregate_comparisons(
    comparisons_by_repeat: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, dict[str, Any]]:
    by_candidate: dict[str, list[dict[str, Any]]] = {}
    for repeat_comparisons in comparisons_by_repeat.values():
        for name, comparison in repeat_comparisons.items():
            by_candidate.setdefault(name, []).append(comparison)

    aggregate: dict[str, dict[str, Any]] = {}
    for name, group in by_candidate.items():
        payload: dict[str, Any] = {"repeat_count": len(group)}
        metric_keys = set().union(*(comparison.keys() for comparison in group))
        for key in sorted(metric_keys):
            values = [comparison[key] for comparison in group if key in comparison]
            if not values:
                continue
            if key == "matched_cases":
                payload[key] = int(min(values))
            elif key == "engineering_gate_agreement_rate":
                payload[key] = float(min(values))
            elif all(isinstance(value, (int, float)) for value in values):
                payload[key] = float(max(values))
            else:
                payload[key] = values[0]
        aggregate[name] = payload
    return aggregate


def _default_variants(
    block_sizes: list[int],
    *,
    variant_set: str,
    current_default_engine: str,
    current_default_block_size: int,
    current_default_rng_order: str,
    event_block_rng_order_override: str | None = None,
) -> list[BenchmarkVariant]:
    def _variant_name(engine: str, block_size: int, rng_order: str) -> str:
        rng_suffix = "" if rng_order == "event_loop_order" else f"_rng_{rng_order}"
        return f"{engine}_b{block_size}{rng_suffix}"

    if variant_set == "current-default":
        rng_order = event_block_rng_order_override or current_default_rng_order
        return [
            BenchmarkVariant("scalar_off_b32", "off", 32),
            BenchmarkVariant(
                _variant_name(
                    current_default_engine,
                    current_default_block_size,
                    rng_order,
                ),
                current_default_engine,
                current_default_block_size,
                rng_order,
            ),
        ]

    if variant_set == "rng-orders":
        block_size = current_default_block_size
        return [
            BenchmarkVariant("scalar_off_b32", "off", 32),
            BenchmarkVariant(
                _variant_name("event_block_v3", block_size, "event_loop_order"),
                "event_block_v3",
                block_size,
                "event_loop_order",
            ),
            BenchmarkVariant(
                _variant_name("event_block_v3", block_size, "block_lane_order"),
                "event_block_v3",
                block_size,
                "block_lane_order",
            ),
        ]

    rng_order = event_block_rng_order_override or "event_loop_order"
    if variant_set == "v3-blocks":
        return [
            BenchmarkVariant("scalar_off_b32", "off", 32),
            *[
                BenchmarkVariant(
                    _variant_name("event_block_v3", block_size, rng_order),
                    "event_block_v3",
                    block_size,
                    rng_order,
                )
                for block_size in block_sizes
            ],
        ]

    if variant_set != "full":
        raise ValueError(f"Unknown variant set: {variant_set}")

    variants = [
        BenchmarkVariant("scalar_off_b32", "off", 32),
        BenchmarkVariant(
            _variant_name("event_block_v2", 32, rng_order),
            "event_block_v2",
            32,
            rng_order,
        ),
    ]
    variants.extend(
        BenchmarkVariant(
            _variant_name("event_block_v3", block_size, rng_order),
            "event_block_v3",
            block_size,
            rng_order,
        )
        for block_size in block_sizes
    )
    return variants


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a short 8-worker precompute benchmark for event engines."
    )
    parser.add_argument("--grid", default="coarse")
    parser.add_argument("--particle-profile", default="quick")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument(
        "--repeats",
        type=int,
        default=1,
        help=(
            "Repeat the whole variant matrix and recommend from median runtimes. "
            "Use 2-3 for noisy block-size decisions."
        ),
    )
    parser.add_argument(
        "--events",
        type=int,
        default=None,
        help=(
            "Override events per case by installing a temporary benchmark grid. "
            "Omit to use the selected grid default."
        ),
    )
    parser.add_argument(
        "--sample-cases",
        type=int,
        default=None,
        help=(
            "Install a temporary benchmark grid with an evenly spread case subset "
            "no larger than this target when the grid/product shape permits."
        ),
    )
    parser.add_argument(
        "--variant-set",
        choices=("full", "v3-blocks", "current-default", "rng-orders"),
        default="full",
        help=(
            "Variant matrix to run. Use current-default for long-event probes "
            "where scalar-vs-default is the main question; rng-orders compares "
            "event_loop_order and block_lane_order for the current v3 block size."
        ),
    )
    parser.add_argument("--block-sizes", type=int, nargs="+", default=[16, 32, 64, 128])
    parser.add_argument(
        "--event-block-rng-order",
        choices=EVENT_BLOCK_RNG_ORDER_OPTIONS,
        default=None,
        help=(
            "Override the RNG draw order for event_block_v2/v3 variants. "
            "Use block_lane_order to evaluate the faster statistical RNG path."
        ),
    )
    parser.add_argument("--tag", default="codex_event_engine_benchmark_20260426")
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=PROJECT_ROOT / "tmp" / "event_engine_benchmark_runs",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=PROJECT_ROOT / "reports" / "event_engine_benchmark",
    )
    parser.add_argument("--progress-interval", type=float, default=60.0)
    parser.add_argument("--keep-run-dir", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    tag = _safe_tag(args.tag)
    grid_plan = _install_benchmark_grid(
        base_grid_name=str(args.grid),
        particle_profile=str(args.particle_profile),
        tag=tag,
        events_per_case=args.events,
        sample_case_limit=args.sample_cases,
    )
    run_dir = args.run_dir / tag
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    current_default_cfg = build_precompute_sim_cfg(grid_plan.run_grid)
    variants = _default_variants(
        [int(value) for value in args.block_sizes],
        variant_set=str(args.variant_set),
        current_default_engine=str(current_default_cfg.vectorized_event_engine),
        current_default_block_size=int(current_default_cfg.event_block_size),
        current_default_rng_order=str(current_default_cfg.event_block_rng_order),
        event_block_rng_order_override=args.event_block_rng_order,
    )
    records: list[dict[str, Any]] = []
    comparisons_by_repeat: dict[str, dict[str, dict[str, Any]]] = {}
    repeat_count = max(1, int(args.repeats))
    for repeat_idx in range(repeat_count):
        repeat_tag = tag if repeat_count == 1 else _safe_tag(
            f"{tag}_r{repeat_idx + 1:02d}"
        )
        baseline_df: pd.DataFrame | None = None
        variant_frames: dict[str, pd.DataFrame] = {}
        for variant in variants:
            record = _run_variant(
                variant=variant,
                tag=repeat_tag,
                grid=grid_plan.run_grid,
                particle_profile=str(args.particle_profile),
                output_dir=run_dir,
                workers=int(args.workers),
                progress_interval_s=float(args.progress_interval),
            )
            record["repeat_index"] = repeat_idx + 1
            records.append(record)
            df, _ = _load_variant_outputs(
                output_dir=run_dir,
                grid=grid_plan.run_grid,
                variant_tag=str(record["variant_tag"]),
            )
            variant_frames[variant.name] = df
            if variant.name == "scalar_off_b32":
                baseline_df = df

        if baseline_df is None:
            raise RuntimeError("Missing scalar baseline variant")

        comparisons_by_repeat[f"r{repeat_idx + 1:02d}"] = {
            name: _compare_to_baseline(
                baseline_df=baseline_df,
                candidate_df=df,
            )
            for name, df in variant_frames.items()
            if name != "scalar_off_b32"
        }

    aggregate_records = _aggregate_records(records)
    comparisons = _aggregate_comparisons(comparisons_by_repeat)
    recommendation = _select_recommendation(
        aggregate_records,
        comparisons,
        baseline_name="scalar_off_b32",
        current_default_engine=str(current_default_cfg.vectorized_event_engine),
        current_default_block_size=int(current_default_cfg.event_block_size),
        current_default_rng_order=str(current_default_cfg.event_block_rng_order),
    )

    report = {
        "benchmark": {
            "tag": tag,
            "base_grid": grid_plan.base_grid,
            "run_grid": grid_plan.run_grid,
            "particle_profile": str(args.particle_profile),
            "workers": int(args.workers),
            "repeats": repeat_count,
            "events_per_case": int(grid_plan.events_per_case),
            "sample_case_limit": grid_plan.sample_case_limit,
            "actual_cases": int(grid_plan.actual_cases),
            "particle_count": int(grid_plan.particle_count),
            "selected_counts": grid_plan.selected_counts,
            "variant_set": str(args.variant_set),
            "block_sizes": [int(value) for value in args.block_sizes],
            "event_block_rng_order_override": args.event_block_rng_order,
            "current_default_event_block_rng_order": str(
                current_default_cfg.event_block_rng_order
            ),
            "run_dir": str(run_dir),
        },
        "records": records,
        "aggregate_records": aggregate_records,
        "comparisons_by_repeat": comparisons_by_repeat,
        "comparisons_vs_scalar": comparisons,
        "recommendation": recommendation,
        "tolerances": {
            "max_abs_delta_detection_rate": RATE_TOLERANCE,
            "max_abs_delta_stable_detection_rate": RATE_TOLERANCE,
            "max_abs_relative_delta_mean_peak_height": HEIGHT_REL_TOLERANCE,
            "max_abs_relative_delta_mean_peak_width_s": WIDTH_REL_TOLERANCE,
            "engineering_gate_agreement_rate": 1.0,
            "min_relative_improvement_to_change_default": (
                MIN_RELATIVE_IMPROVEMENT_TO_CHANGE_DEFAULT
            ),
        },
    }
    args.report_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.report_dir / f"{tag}_summary.json"
    records_path = args.report_dir / f"{tag}_runs.csv"
    write_json_file(summary_path, report)
    write_csv_records(records_path, records)
    print(
        json.dumps(
            {
                "records": records,
                "aggregate_records": aggregate_records,
                "recommendation": recommendation,
                "summary_path": str(summary_path),
                "records_path": str(records_path),
            },
            indent=2,
        )
    )

    if not args.keep_run_dir:
        # Keep compact report artifacts; remove full per-run precompute outputs.
        shutil.rmtree(run_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
