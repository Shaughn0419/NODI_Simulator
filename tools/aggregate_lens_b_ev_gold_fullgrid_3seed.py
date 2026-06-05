#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools._common import dataframe_to_markdown_table, write_json_file  # noqa: E402
from tools.audits import ev_size_weighted_route_analysis as route_analysis  # noqa: E402


ROUTE_COLUMNS = ["wavelength_nm", "width_nm", "depth_nm"]
FORMAL_FULL_GRID_SEEDS = (11, 22, 33)
RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM = (
    route_analysis.RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM
)
CONTROL_ONLY_WAVELENGTHS_NM = route_analysis.CONTROL_ONLY_WAVELENGTHS_NM


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"required JSON missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _load_seed_derived_dir(path: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    precheck = _read_json(path / "lens_b_fullgrid_data_precheck.json")
    if precheck.get("status") != "passed":
        raise ValueError(f"precheck did not pass for {path}: {precheck.get('failures')}")
    seeds = [int(value) for value in precheck.get("random_seed_values", [])]
    if len(seeds) != 1:
        raise ValueError(f"derived dir must represent exactly one seed: {path} -> {seeds}")
    lanes = [str(value) for value in precheck.get("normalization_lane_values", [])]
    if len(lanes) > 1:
        raise ValueError(
            f"derived dir must represent at most one normalization view: {path} -> {lanes}"
        )
    normalization_lane = lanes[0] if lanes else "unknown_normalization_lane"

    route_path = path / "lens_b_ev_fullgrid_route_ranking.csv"
    if not route_path.exists():
        raise FileNotFoundError(f"route ranking CSV missing: {route_path}")
    frame = pd.read_csv(route_path, low_memory=False)
    frame.insert(0, "derived_dir", str(path))
    frame.insert(1, "random_seed", seeds[0])
    frame.insert(2, "normalization_lane", normalization_lane)
    return frame, precheck


def _metric_columns(frame: pd.DataFrame) -> list[str]:
    wanted_prefixes = (
        "raw_mean_",
        "raw_min_",
        "uniform_weighted_",
        "small_ev_literature_weighted_",
        "broad_ev_literature_weighted_",
        "sharp_msc_sev_empirical_weighted_",
    )
    wanted_fragments = ("_selected_rank_",)
    columns: list[str] = []
    for column in frame.columns:
        if column in {"random_seed", "normalization_lane", *ROUTE_COLUMNS}:
            continue
        if column.startswith(wanted_prefixes) or any(fragment in column for fragment in wanted_fragments):
            if pd.api.types.is_numeric_dtype(frame[column]):
                columns.append(column)
    return columns


def _flatten_columns(frame: pd.DataFrame) -> pd.DataFrame:
    flattened = []
    for column in frame.columns:
        if isinstance(column, tuple):
            parts = [str(part) for part in column if str(part)]
            flattened.append("_".join(parts))
        else:
            flattened.append(str(column))
    out = frame.copy()
    out.columns = flattened
    return out


def aggregate_route_stability(frames: list[pd.DataFrame]) -> pd.DataFrame:
    combined = pd.concat(frames, ignore_index=True)
    metrics = _metric_columns(combined)
    if not metrics:
        raise ValueError("no numeric route metric columns found to aggregate")
    grouped = combined.groupby(["normalization_lane", *ROUTE_COLUMNS], dropna=False)
    agg = grouped[metrics].agg(["mean", "std", "min", "max"]).reset_index()
    agg = _flatten_columns(agg)
    seed_count = grouped["random_seed"].nunique().rename("seed_count").reset_index()
    out = agg.merge(seed_count, on=["normalization_lane", *ROUTE_COLUMNS], how="left")
    out["wavelength_role"] = "unexpected_wavelength"
    eligible = out["wavelength_nm"].astype(int).isin(RECOMMENDATION_ELIGIBLE_WAVELENGTHS_NM)
    control = out["wavelength_nm"].astype(int).isin(CONTROL_ONLY_WAVELENGTHS_NM)
    out.loc[eligible, "wavelength_role"] = "recommendation_eligible_404_660"
    out.loc[control, "wavelength_role"] = "control_only_488_532"
    return out


def build_top_routes(stability: pd.DataFrame, *, top_n: int) -> pd.DataFrame:
    preferred_cols = [
        "uniform_weighted_selected_annulus_detection_mean",
        "uniform_weighted_stable_mean",
        "uniform_weighted_final_mean",
    ]
    sort_cols = [col for col in preferred_cols if col in stability.columns]
    if not sort_cols:
        sort_cols = [
            col
            for col in stability.columns
            if col.endswith("_mean") and col not in {"wavelength_nm_mean", "width_nm_mean", "depth_nm_mean"}
        ][:3]
    if not sort_cols:
        raise ValueError("no sortable mean metric columns found")
    pieces = []
    for lane, sub in stability.groupby("normalization_lane", dropna=False):
        ranked = sub.sort_values(sort_cols, ascending=[False] * len(sort_cols)).head(top_n)
        pieces.append(ranked)
    return pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()


def _parse_expected_seeds(text: str) -> list[int]:
    return [int(piece.strip()) for piece in text.split(",") if piece.strip()]


def _parse_expected_lanes(text: str | None) -> list[str] | None:
    if text is None or not text.strip():
        return None
    return [piece.strip() for piece in text.split(",") if piece.strip()]


def _validate_coverage(
    prechecks: list[dict[str, Any]],
    *,
    expected_seeds: list[int],
    expected_lanes: list[str] | None,
) -> dict[str, Any]:
    rows = []
    for precheck in prechecks:
        seed_values = [int(value) for value in precheck.get("random_seed_values", [])]
        lane_values = [str(value) for value in precheck.get("normalization_lane_values", [])]
        rows.append(
            {
                "source_csv": precheck.get("source_csv"),
                "seed": seed_values[0] if len(seed_values) == 1 else None,
                "normalization_lane": lane_values[0] if len(lane_values) == 1 else "unknown_normalization_lane",
                "row_count": int(precheck.get("row_count", 0)),
                "n_events_values": precheck.get("n_events_values", []),
            }
        )
    coverage = pd.DataFrame(rows)
    failures: list[str] = []
    if coverage.empty:
        failures.append("no derived directories supplied")
    lanes = sorted(coverage["normalization_lane"].dropna().astype(str).unique().tolist())
    if expected_lanes is not None and lanes != sorted(expected_lanes):
        failures.append(f"normalization lanes expected {sorted(expected_lanes)}, got {lanes}")
    for lane, sub in coverage.groupby("normalization_lane", dropna=False):
        observed = sorted(int(value) for value in sub["seed"].dropna().unique().tolist())
        if observed != sorted(expected_seeds):
            failures.append(f"lane {lane} seeds expected {sorted(expected_seeds)}, got {observed}")
    return {
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "expected_seeds": expected_seeds,
        "expected_normalization_lanes": expected_lanes,
        "observed_normalization_lanes": lanes,
        "inputs": rows,
    }


def write_report(path: Path, summary: dict[str, Any], top_routes: pd.DataFrame) -> None:
    top_preview = top_routes.head(20)
    text = f"""# Lens B EV+Gold Full-Grid 3-Seed Aggregation

## Coverage

- Status: {summary['coverage']['status']}
- Expected seeds: {summary['coverage']['expected_seeds']}
- Observed normalization lanes: {summary['coverage']['observed_normalization_lanes']}
- Failures: {summary['coverage']['failures']}

## Scope Guard

This aggregation reads per-seed derived route-ranking outputs. It does not rerun
raw event simulation and does not merge normalization views into a single claim.
Final wording must remain Level-1 no-measured-data relative/proxy design
selection.

## Top Routes Preview

{dataframe_to_markdown_table(top_preview, empty_message='No top routes available.')}
"""
    path.write_text(text, encoding="utf-8")


def run(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    frames: list[pd.DataFrame] = []
    prechecks: list[dict[str, Any]] = []
    for raw_dir in args.derived_dir:
        frame, precheck = _load_seed_derived_dir(Path(raw_dir))
        frames.append(frame)
        prechecks.append(precheck)
    expected_seeds = _parse_expected_seeds(args.expected_seeds)
    expected_lanes = _parse_expected_lanes(args.expected_normalization_lanes)
    coverage = _validate_coverage(
        prechecks,
        expected_seeds=expected_seeds,
        expected_lanes=expected_lanes,
    )
    write_json_file(output_dir / "lens_b_fullgrid_3seed_coverage_precheck.json", coverage)
    if coverage["status"] != "passed":
        raise SystemExit("Coverage precheck failed; see lens_b_fullgrid_3seed_coverage_precheck.json")
    if args.check_only:
        return

    stability = aggregate_route_stability(frames)
    stability.to_csv(output_dir / "lens_b_ev_fullgrid_3seed_route_stability.csv", index=False)
    top_routes = build_top_routes(stability, top_n=int(args.top_n))
    top_routes.to_csv(output_dir / "lens_b_ev_fullgrid_3seed_top_routes.csv", index=False)
    summary = {
        "coverage": coverage,
        "route_count": int(len(stability)),
        "top_route_count": int(len(top_routes)),
        "claim_boundary": (
            "Level-1 no-measured-data relative/proxy design selection only; "
            "normalization views and seeds remain separate."
        ),
    }
    write_json_file(output_dir / "lens_b_fullgrid_3seed_aggregation_summary.json", summary)
    write_report(
        output_dir / "lens_b_fullgrid_3seed_aggregation_report.md",
        summary,
        top_routes,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate per-seed Lens-B EV+gold full-grid derived outputs."
    )
    parser.add_argument("--derived-dir", action="append", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--expected-seeds",
        default=",".join(str(seed) for seed in FORMAL_FULL_GRID_SEEDS),
    )
    parser.add_argument(
        "--expected-normalization-lanes",
        default=None,
        help="Comma-separated lane list, e.g. fixed_660_gold or fixed_660_gold,per_wavelength_gold.",
    )
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--check-only", action="store_true")
    run(parser.parse_args())


if __name__ == "__main__":
    main()
