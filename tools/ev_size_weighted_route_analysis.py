#!/usr/bin/env python3

"""
Literature-informed EV size-weighted route analysis.

This script adds an application-layer weighting on top of the existing
uniform-diameter analysis. The goal is not to replace the raw physics
capability map, but to answer a different question:

"If the target sample is mostly small EV / exosome-like, which routes are
better for the particle sizes that are actually more common?"

The script keeps three priors:

1. uniform
   Flat weight over the configured diameter range. This reproduces the
   current "every diameter point counts equally" view.

2. small_ev_literature
   Literature-informed prior for MSC-sEV / exosome-heavy samples:
   concentrated in the 60-200 nm region, peaking around 100-120 nm, with
   only a tiny tail above 200 nm.

3. broad_ev_literature
   Broader EV prior that still prefers smaller vesicles, but keeps a
   meaningful tail out to 300 nm.

4. sharp_msc_sev_empirical
   A sharper sensitivity scenario for therapeutic MSC-sEV-like samples,
   motivated by reports where the detected sEV population is heavily
   concentrated around roughly 50-120 nm with only a very weak tail above
   150-200 nm.

These priors are scenario priors, not universal truths. They are intended
to be used alongside the raw unweighted results.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


ALL_CROSSING_RATE_COLUMN = "all_crossing_detection_rate"
SELECTED_ANNULUS_RATE_COLUMN = "selected_detector_mode_annulus_detection_rate"
SELECTED_ANNULUS_FRACTION_COLUMN = "selected_detector_mode_annulus_fraction"
ROUTE_COLUMNS = ["wavelength_nm", "width_nm", "depth_nm"]


def build_priors(diameters: list[int]) -> dict[str, dict[int, float]]:
    priors: dict[str, dict[int, float]] = {}

    priors["uniform"] = {d: 1.0 for d in diameters}

    small_ev = {}
    for d in diameters:
        if d <= 110:
            small_ev[d] = 1.0 + (d - 60) / 50.0 * 1.5
        elif d <= 200:
            small_ev[d] = 2.5 - (d - 110) / 90.0 * 2.0
        else:
            # Keep only a weak large-EV tail instead of forcing it to zero.
            small_ev[d] = 0.08 * max(0.0, (300 - d) / 100.0)
    priors["small_ev_literature"] = small_ev

    broad_ev = {}
    for d in diameters:
        if d <= 120:
            broad_ev[d] = 1.0 + (d - 60) / 60.0 * 1.0
        else:
            broad_ev[d] = max(2.0 - (d - 120) / 180.0 * 1.4, 0.2)
    priors["broad_ev_literature"] = broad_ev

    sharp_msc = {}
    for d in diameters:
        if d <= 80:
            sharp_msc[d] = 1.3
        elif d <= 100:
            sharp_msc[d] = 2.2
        elif d <= 120:
            sharp_msc[d] = 2.4
        elif d <= 140:
            sharp_msc[d] = 0.7
        elif d <= 160:
            sharp_msc[d] = 0.25
        else:
            sharp_msc[d] = 0.02
    priors["sharp_msc_sev_empirical"] = sharp_msc

    return priors


def normalize_prior(prior: dict[int, float]) -> dict[int, float]:
    total = sum(prior.values())
    return {k: v / total for k, v in prior.items()}


def aggregate_routes(df: pd.DataFrame, priors: dict[str, dict[int, float]]) -> pd.DataFrame:
    df = _with_parallel_detection_lenses(df)
    out = (
        df.groupby(ROUTE_COLUMNS)
        .agg(
            raw_strict_count=("strict_ok", "sum"),
            selected_annulus_lens_available=(
                "selected_annulus_lens_available",
                "max",
            ),
            selected_annulus_lens_source=("selected_annulus_lens_source", "first"),
            raw_mean_detection=("detection_rate", "mean"),
            raw_mean_all_crossing_detection=("all_crossing_detection_rate", "mean"),
            raw_mean_selected_annulus_detection=(
                SELECTED_ANNULUS_RATE_COLUMN,
                "mean",
            ),
            raw_mean_selected_annulus_fraction=(
                SELECTED_ANNULUS_FRACTION_COLUMN,
                "mean",
            ),
            raw_mean_stable=("stable_detection_rate", "mean"),
            raw_mean_final=("final_engineering_score", "mean"),
        )
        .reset_index()
    )

    for prior_name, prior in priors.items():
        wmap = normalize_prior(prior)
        weighted = df.copy()
        weighted["weight"] = weighted["particle_diameter_nm"].map(wmap)
        agg = (
            weighted.groupby(ROUTE_COLUMNS)
            .apply(
                lambda x, prior_name=prior_name: pd.Series(
                    {
                        f"{prior_name}_weighted_detection": (
                            x["detection_rate"] * x["weight"]
                        ).sum(),
                        f"{prior_name}_weighted_all_crossing_detection": (
                            x["all_crossing_detection_rate"] * x["weight"]
                        ).sum(),
                        f"{prior_name}_weighted_selected_annulus_detection": (
                            _weighted_sum_or_nan(
                                x[SELECTED_ANNULUS_RATE_COLUMN],
                                x["weight"],
                            )
                        ),
                        f"{prior_name}_weighted_selected_annulus_fraction": (
                            _weighted_sum_or_nan(
                                x[SELECTED_ANNULUS_FRACTION_COLUMN],
                                x["weight"],
                            )
                        ),
                        f"{prior_name}_weighted_stable": (
                            x["stable_detection_rate"] * x["weight"]
                        ).sum(),
                        f"{prior_name}_weighted_final": (
                            x["final_engineering_score"] * x["weight"]
                        ).sum(),
                        f"{prior_name}_weighted_strict_pass": (
                            x["strict_ok"].astype(float) * x["weight"]
                        ).sum(),
                    }
                ),
                include_groups=False,
            )
            .reset_index()
        )
        out = out.merge(agg, on=ROUTE_COLUMNS, how="left")

    return out


def _with_parallel_detection_lenses(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "strict_ok" not in out:
        engineering_gate = (
            out["engineering_gate_passed"].astype(bool)
            if "engineering_gate_passed" in out
            else pd.Series(False, index=out.index)
        )
        na_cutoff = (
            out["na_cutoff_active"].astype(bool)
            if "na_cutoff_active" in out
            else pd.Series(False, index=out.index)
        )
        rho_status = (
            out["rho_physical_envelope_status"].astype(str)
            if "rho_physical_envelope_status" in out
            else pd.Series("within_envelope", index=out.index)
        )
        out["strict_ok"] = engineering_gate & (~na_cutoff) & (
            rho_status == "within_envelope"
        )
    if ALL_CROSSING_RATE_COLUMN not in out:
        out[ALL_CROSSING_RATE_COLUMN] = out["detection_rate"]
    else:
        out[ALL_CROSSING_RATE_COLUMN] = pd.to_numeric(
            out[ALL_CROSSING_RATE_COLUMN],
            errors="coerce",
        ).fillna(out["detection_rate"])
    has_selected_columns = (
        SELECTED_ANNULUS_RATE_COLUMN in out
        and SELECTED_ANNULUS_FRACTION_COLUMN in out
    )
    selected_rate = (
        pd.to_numeric(out[SELECTED_ANNULUS_RATE_COLUMN], errors="coerce")
        if has_selected_columns
        else pd.Series(dtype=float)
    )
    selected_fraction = (
        pd.to_numeric(out[SELECTED_ANNULUS_FRACTION_COLUMN], errors="coerce")
        if has_selected_columns
        else pd.Series(dtype=float)
    )
    selected_available = bool(
        has_selected_columns
        and selected_rate.notna().any()
        and selected_fraction.notna().any()
    )
    out["selected_annulus_lens_available"] = bool(selected_available)
    if selected_available:
        selected_source = "selected_detector_mode_annulus"
    elif has_selected_columns:
        selected_source = "selected_detector_mode_annulus_empty_or_no_valid_denominator"
    else:
        selected_source = "missing_selected_annulus_columns_rerun_source_summary"
    out["selected_annulus_lens_source"] = selected_source
    if not selected_available:
        out[SELECTED_ANNULUS_RATE_COLUMN] = float("nan")
        out[SELECTED_ANNULUS_FRACTION_COLUMN] = float("nan")
    else:
        out[SELECTED_ANNULUS_RATE_COLUMN] = selected_rate
        out[SELECTED_ANNULUS_FRACTION_COLUMN] = selected_fraction
    return out


def _weighted_sum_or_nan(values: pd.Series, weights: pd.Series) -> float:
    product = pd.to_numeric(values, errors="coerce") * pd.to_numeric(
        weights,
        errors="coerce",
    )
    result = product.sum(min_count=1)
    return float(result) if pd.notna(result) else float("nan")


def build_selected_annulus_ranking_comparison(
    routes: pd.DataFrame,
    priors: dict[str, dict[int, float]],
    *,
    top_n: int = 3,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    selected_available = bool(
        routes.get("selected_annulus_lens_available", pd.Series([False]))
        .astype(bool)
        .any()
    )
    for prior_name in priors:
        primary_sort = [
            f"{prior_name}_weighted_strict_pass",
            f"{prior_name}_weighted_stable",
            f"{prior_name}_weighted_final",
        ]
        selected_sort = [
            f"{prior_name}_weighted_selected_annulus_detection",
            f"{prior_name}_weighted_stable",
            f"{prior_name}_weighted_final",
        ]
        primary_ranked = _rank_routes(routes, primary_sort)
        primary_top = _route_records(primary_ranked.head(top_n))
        selected_ranked = _rank_routes(routes, selected_sort) if selected_available else routes
        selected_top = (
            _route_records(selected_ranked.head(top_n)) if selected_available else []
        )
        primary_set = {tuple(record.values()) for record in primary_top}
        selected_set = {tuple(record.values()) for record in selected_top}
        primary_top1 = primary_top[0] if primary_top else None
        selected_top1 = selected_top[0] if selected_top else None
        rows.append(
            {
                "profile": prior_name,
                "selected_annulus_lens_available": selected_available,
                "primary_lens": "strict_pass_then_stable_then_final",
                "selected_annulus_lens": (
                    "selected_annulus_detection_then_stable_then_final"
                ),
                "top_n": int(top_n),
                "primary_top_routes": json.dumps(primary_top),
                "selected_annulus_top_routes": json.dumps(selected_top),
                "selected_annulus_top1_route_changed": (
                    selected_available and primary_top1 != selected_top1
                ),
                "selected_annulus_top_routes_order_changed": (
                    selected_available and primary_top != selected_top
                ),
                "selected_annulus_top_routes_changed": (
                    selected_available and primary_set != selected_set
                ),
            }
        )
    return pd.DataFrame(rows)


def _rank_routes(routes: pd.DataFrame, sort_cols: list[str]) -> pd.DataFrame:
    available = [column for column in sort_cols if column in routes]
    if not available:
        return routes.copy()
    return routes.sort_values(available, ascending=[False] * len(available)).copy()


def _route_records(routes: pd.DataFrame) -> list[dict[str, int]]:
    records: list[dict[str, int]] = []
    for row in routes.itertuples(index=False):
        records.append(
            {
                "wavelength_nm": int(row.wavelength_nm),
                "width_nm": int(row.width_nm),
                "depth_nm": int(row.depth_nm),
            }
        )
    return records


def print_top_routes(routes: pd.DataFrame, prior_name: str, top_n: int) -> None:
    cols = [
        "wavelength_nm",
        "width_nm",
        "depth_nm",
        "raw_strict_count",
        f"{prior_name}_weighted_strict_pass",
        f"{prior_name}_weighted_stable",
        f"{prior_name}_weighted_final",
    ]
    ranked = routes.sort_values(
        [
            f"{prior_name}_weighted_strict_pass",
            f"{prior_name}_weighted_stable",
            f"{prior_name}_weighted_final",
        ],
        ascending=False,
    )
    print(f"\nTOP {top_n} routes under prior: {prior_name}")
    print(ranked[cols].head(top_n).round(4).to_string(index=False))

    selected_col = f"{prior_name}_weighted_selected_annulus_detection"
    if selected_col in routes:
        selected_available = bool(
            routes.get(
                "selected_annulus_lens_available",
                pd.Series([False]),
            )
            .astype(bool)
            .any()
        )
        if not selected_available:
            print(
                "\nSelected-annulus columns were not present; "
                "skipping selected-annulus route ranking for this input."
            )
            return
        selected_cols = [
            "wavelength_nm",
            "width_nm",
            "depth_nm",
            f"{prior_name}_weighted_selected_annulus_detection",
            f"{prior_name}_weighted_selected_annulus_fraction",
            f"{prior_name}_weighted_stable",
            f"{prior_name}_weighted_final",
        ]
        selected_ranked = routes.sort_values(
            [
                f"{prior_name}_weighted_selected_annulus_detection",
                f"{prior_name}_weighted_stable",
                f"{prior_name}_weighted_final",
            ],
            ascending=False,
        )
        print(f"\nTOP {top_n} selected-annulus routes under prior: {prior_name}")
        print(selected_ranked[selected_cols].head(top_n).round(4).to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--summary-csv",
        default=(
            "results/"
            "ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv"
        ),
        help="Path to the current EV design summary CSV",
    )
    parser.add_argument(
        "--output-csv",
        default="results/ev_size_weighted_route_analysis.csv",
        help="Path to write the weighted route table",
    )
    parser.add_argument(
        "--selected-ranking-csv",
        default="results/ev_size_weighted_route_analysis_selected_annulus_ranking.csv",
        help="Path to write primary-vs-selected-annulus route comparison",
    )
    parser.add_argument("--particle-material", default="exosome")
    parser.add_argument("--diameter-min", type=int, default=60)
    parser.add_argument("--diameter-max", type=int, default=300)
    parser.add_argument("--top-n", type=int, default=8)
    args = parser.parse_args()

    df = pd.read_csv(args.summary_csv)
    df = df[df["particle_material"] == args.particle_material].copy()
    df = df[
        df["particle_diameter_nm"].between(args.diameter_min, args.diameter_max)
    ].copy()

    df["strict_ok"] = (
        df["engineering_gate_passed"]
        & (~df["na_cutoff_active"])
        & (df["rho_physical_envelope_status"] == "within_envelope")
    )

    diameters = sorted(df["particle_diameter_nm"].unique().tolist())
    priors = build_priors(diameters)
    routes = aggregate_routes(df, priors)
    ranking_comparison = build_selected_annulus_ranking_comparison(
        routes,
        priors,
        top_n=args.top_n,
    )

    output_path = Path(args.output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    routes.to_csv(output_path, index=False)
    selected_ranking_path = Path(args.selected_ranking_csv)
    selected_ranking_path.parent.mkdir(parents=True, exist_ok=True)
    ranking_comparison.to_csv(selected_ranking_path, index=False)

    print(f"Wrote weighted route table to: {output_path}")
    print(f"Wrote selected-annulus ranking comparison to: {selected_ranking_path}")
    for prior_name in priors:
        print_top_routes(routes, prior_name, args.top_n)


if __name__ == "__main__":
    main()
