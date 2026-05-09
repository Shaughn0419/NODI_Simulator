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
SELECTED_ANNULUS_CONTRIBUTION_COLUMN = "selected_detector_mode_annulus_contribution"
SELECTED_ANNULUS_UPLIFT_COLUMN = "selected_detector_mode_annulus_uplift"
REFERENCE_USEFUL_BAND = "electronics_noise_limited_useful"
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
            selected_annulus_lens_source=(
                "selected_annulus_lens_source",
                _aggregate_selected_annulus_source,
            ),
            reference_operating_band=(
                "reference_operating_band",
                _aggregate_reference_operating_band,
            ),
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
            raw_min_selected_annulus_fraction=(
                SELECTED_ANNULUS_FRACTION_COLUMN,
                "min",
            ),
            raw_mean_selected_annulus_contribution=(
                SELECTED_ANNULUS_CONTRIBUTION_COLUMN,
                "mean",
            ),
            raw_mean_selected_annulus_uplift=(
                SELECTED_ANNULUS_UPLIFT_COLUMN,
                "mean",
            ),
            raw_mean_stable=("stable_detection_rate", "mean"),
            raw_mean_final=("final_engineering_score", "mean"),
        )
        .reset_index()
    )
    _add_selected_annulus_route_status_columns(out)

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
                        f"{prior_name}_weighted_selected_annulus_contribution": (
                            _weighted_sum_or_nan(
                                x[SELECTED_ANNULUS_CONTRIBUTION_COLUMN],
                                x["weight"],
                            )
                        ),
                        f"{prior_name}_weighted_selected_annulus_uplift": (
                            _weighted_selected_uplift(x, "weight")
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
    if "reference_operating_band" not in out:
        out["reference_operating_band"] = "unknown_reference_band"
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
    selected_valid = (
        _selected_annulus_valid_rows(selected_rate, selected_fraction)
        if has_selected_columns
        else pd.Series(False, index=out.index)
    )
    selected_available = bool(selected_valid.any())
    out["selected_annulus_lens_available"] = selected_valid.astype(bool)
    if has_selected_columns:
        selected_source = pd.Series(
            "selected_detector_mode_annulus_empty_or_no_valid_denominator",
            index=out.index,
        )
        selected_source.loc[selected_valid] = "selected_detector_mode_annulus"
    else:
        selected_source = pd.Series(
            "missing_selected_annulus_columns_rerun_source_summary",
            index=out.index,
        )
    out["selected_annulus_lens_source"] = selected_source
    if not selected_available:
        out[SELECTED_ANNULUS_RATE_COLUMN] = float("nan")
        out[SELECTED_ANNULUS_FRACTION_COLUMN] = float("nan")
    else:
        out[SELECTED_ANNULUS_RATE_COLUMN] = selected_rate.where(selected_valid)
        out[SELECTED_ANNULUS_FRACTION_COLUMN] = selected_fraction.where(
            selected_valid
        )
    out[SELECTED_ANNULUS_CONTRIBUTION_COLUMN] = (
        out[SELECTED_ANNULUS_RATE_COLUMN] * out[SELECTED_ANNULUS_FRACTION_COLUMN]
    )
    all_crossing = pd.to_numeric(out[ALL_CROSSING_RATE_COLUMN], errors="coerce")
    out[SELECTED_ANNULUS_UPLIFT_COLUMN] = (
        out[SELECTED_ANNULUS_RATE_COLUMN] / all_crossing.where(all_crossing.gt(0.0))
    )
    return out


def _selected_annulus_valid_rows(
    selected_rate: pd.Series,
    selected_fraction: pd.Series,
) -> pd.Series:
    return (
        selected_rate.notna()
        & selected_fraction.notna()
        & selected_fraction.gt(0.0)
    )


def _aggregate_selected_annulus_source(values: pd.Series) -> str:
    text = values.dropna().astype(str)
    if text.empty:
        return "missing_selected_annulus_columns_rerun_source_summary"
    if (text == "selected_detector_mode_annulus").any():
        return "selected_detector_mode_annulus"
    return str(text.iloc[0])


def _aggregate_reference_operating_band(values: pd.Series) -> str:
    text = values.dropna().astype(str)
    if text.empty:
        return "unknown_reference_band"
    unique = sorted(set(text))
    if len(unique) == 1:
        return unique[0]
    if REFERENCE_USEFUL_BAND in unique and "reference_too_weak" in unique:
        return "mixed_reference_useful_and_too_weak"
    return "mixed_reference_operating_band"


def _add_selected_annulus_route_status_columns(routes: pd.DataFrame) -> None:
    routes["selected_annulus_fraction_guardrail_status"] = routes[
        "raw_min_selected_annulus_fraction"
    ].map(_selected_annulus_fraction_guardrail_status)
    routes["selected_annulus_uplift_warning_status"] = routes[
        "raw_mean_selected_annulus_uplift"
    ].map(_selected_annulus_uplift_warning_status)
    routes["selected_annulus_reference_interpretation"] = routes.apply(
        _selected_annulus_reference_interpretation,
        axis=1,
    )


def _selected_annulus_fraction_guardrail_status(value: float) -> str:
    if pd.isna(value):
        return "selected_annulus_unavailable"
    if float(value) < 0.25:
        return "selected_annulus_fraction_fail_below_0p25"
    if float(value) < 0.35:
        return "selected_annulus_fraction_warning_low"
    return "selected_annulus_fraction_ok"


def _selected_annulus_uplift_warning_status(value: float) -> str:
    if pd.isna(value):
        return "selected_annulus_unavailable"
    if float(value) > 1.6:
        return "selected_annulus_uplift_warning_high"
    return "selected_annulus_uplift_ok"


def _selected_annulus_reference_interpretation(row: pd.Series) -> str:
    if not bool(row.get("selected_annulus_lens_available", False)):
        return "selected_annulus_unavailable"
    reference_band = str(row.get("reference_operating_band", "unknown_reference_band"))
    if reference_band == REFERENCE_USEFUL_BAND:
        return "reference_useful_selected_cross_check"
    if reference_band == "reference_too_weak":
        return "weak_reference_boundary_selected_only"
    return "selected_annulus_reference_status_requires_review"


def _weighted_sum_or_nan(values: pd.Series, weights: pd.Series) -> float:
    product = pd.to_numeric(values, errors="coerce") * pd.to_numeric(
        weights,
        errors="coerce",
    )
    result = product.sum(min_count=1)
    return float(result) if pd.notna(result) else float("nan")


def _weighted_selected_uplift(rows: pd.DataFrame, weight_column: str) -> float:
    selected_detection = _weighted_sum_or_nan(
        rows[SELECTED_ANNULUS_RATE_COLUMN],
        rows[weight_column],
    )
    all_crossing = _weighted_sum_or_nan(
        rows[ALL_CROSSING_RATE_COLUMN],
        rows[weight_column],
    )
    if pd.isna(selected_detection) or pd.isna(all_crossing) or all_crossing <= 0:
        return float("nan")
    return float(selected_detection / all_crossing)


def build_selected_annulus_ranking_comparison(
    routes: pd.DataFrame,
    priors: dict[str, dict[int, float]],
    *,
    top_n: int = 3,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    selected_route_mask = (
        routes.get(
            "selected_annulus_lens_available",
            pd.Series(False, index=routes.index),
        )
        .reindex(routes.index, fill_value=False)
        .astype(bool)
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
        selected_rate_col = f"{prior_name}_weighted_selected_annulus_detection"
        selected_rankable = routes[selected_route_mask].copy()
        if selected_rate_col in selected_rankable:
            selected_rankable = selected_rankable[
                pd.to_numeric(selected_rankable[selected_rate_col], errors="coerce")
                .notna()
            ]
        else:
            selected_rankable = selected_rankable.iloc[0:0]
        selected_boundary_rankable = routes.iloc[0:0]
        selected_rank_scope = "all_routes_no_reference_filter_available"
        if "reference_operating_band" in selected_rankable:
            useful_mask = selected_rankable["reference_operating_band"].astype(str).eq(
                REFERENCE_USEFUL_BAND
            )
            boundary_mask = selected_rankable["reference_operating_band"].astype(str).ne(
                REFERENCE_USEFUL_BAND
            )
            selected_boundary_rankable = selected_rankable[boundary_mask].copy()
            if useful_mask.any():
                selected_rankable = selected_rankable[useful_mask].copy()
                selected_rank_scope = "reference_useful_only"
        selected_available = not selected_rankable.empty
        primary_ranked = _rank_routes(routes, primary_sort)
        primary_top = _route_records(primary_ranked.head(top_n))
        selected_ranked = (
            _rank_routes(selected_rankable, selected_sort)
            if selected_available
            else routes.iloc[0:0]
        )
        selected_top = (
            _route_records(selected_ranked.head(top_n)) if selected_available else []
        )
        boundary_ranked = (
            _rank_routes(selected_boundary_rankable, selected_sort)
            if not selected_boundary_rankable.empty
            else routes.iloc[0:0]
        )
        boundary_top = _route_records(boundary_ranked.head(top_n))
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
                    "selected_annulus_detection_reference_useful_then_stable_then_final"
                ),
                "selected_annulus_rank_scope": selected_rank_scope,
                "top_n": int(top_n),
                "primary_top_routes": json.dumps(primary_top),
                "selected_annulus_top_routes": json.dumps(selected_top),
                "selected_annulus_boundary_top_routes": json.dumps(boundary_top),
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
            "reference_operating_band",
            f"{prior_name}_weighted_selected_annulus_detection",
            f"{prior_name}_weighted_selected_annulus_fraction",
            f"{prior_name}_weighted_selected_annulus_contribution",
            f"{prior_name}_weighted_selected_annulus_uplift",
            "selected_annulus_reference_interpretation",
            f"{prior_name}_weighted_stable",
            f"{prior_name}_weighted_final",
        ]
        selected_rankable = routes.copy()
        if "reference_operating_band" in selected_rankable:
            reference_useful = selected_rankable[
                selected_rankable["reference_operating_band"].astype(str).eq(
                    REFERENCE_USEFUL_BAND
                )
            ]
            if not reference_useful.empty:
                selected_rankable = reference_useful
        selected_ranked = selected_rankable.sort_values(
            [
                f"{prior_name}_weighted_selected_annulus_detection",
                f"{prior_name}_weighted_stable",
                f"{prior_name}_weighted_final",
            ],
            ascending=False,
        )
        print(
            f"\nTOP {top_n} reference-useful selected-annulus routes "
            f"under prior: {prior_name}"
        )
        print(selected_ranked[selected_cols].head(top_n).round(4).to_string(index=False))
        if "reference_operating_band" in routes:
            boundary_ranked = routes[
                routes["reference_operating_band"].astype(str).ne(REFERENCE_USEFUL_BAND)
            ].sort_values(
                [
                    f"{prior_name}_weighted_selected_annulus_detection",
                    f"{prior_name}_weighted_stable",
                    f"{prior_name}_weighted_final",
                ],
                ascending=False,
            )
            if not boundary_ranked.empty:
                print(
                    f"\nTOP {top_n} weak/unknown-reference selected-annulus "
                    f"boundary routes under prior: {prior_name}"
                )
                print(
                    boundary_ranked[selected_cols]
                    .head(top_n)
                    .round(4)
                    .to_string(index=False)
                )


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

    df = pd.read_csv(args.summary_csv, low_memory=False)
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
