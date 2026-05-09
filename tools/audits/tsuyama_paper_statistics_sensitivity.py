#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
for candidate in (str(PROJECT_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from tools.audits import tsuyama_detection_rate_calibration as rate_calib
from nodi_simulator.type_coerce import finite_float_or_nan as _safe_float

DEFAULT_INPUT_DECOMPOSITION = (
    PROJECT_ROOT
    / "results"
    / "tsuyama_phase2p10_size_response_decomposition_d2p1_v1"
    / "paper_reproduction_size_response_case_decomposition_v1.csv"
)
OUTPUT_DIR = PROJECT_ROOT / "results" / "tsuyama_paper_statistics_sensitivity_v1"
SCHEMA_ID = "tsuyama_paper_statistics_sensitivity_v1"
RAW_FILENAME = "paper_statistics_sensitivity_rows_v1.csv"
SUMMARY_FILENAME = "paper_statistics_sensitivity_summary_v1.csv"
JSON_FILENAME = "paper_statistics_sensitivity_summary_v1.json"
REPORT_FILENAME = "paper_statistics_sensitivity_report_v1.md"
TARGET_EXPONENT = 2.3

def _pair_bounds(pair: str) -> tuple[int, int]:
    left, right = str(pair).split("-", maxsplit=1)
    return int(left), int(right)


def _status_from_multiplier(required_high_signal_multiplier: float) -> str:
    if not np.isfinite(required_high_signal_multiplier):
        return "not_evaluated"
    if required_high_signal_multiplier > 1.0:
        return "already_flatter_than_target_or_requires_amplification"
    suppression_fraction = 1.0 - required_high_signal_multiplier
    if suppression_fraction <= 0.15:
        return "paper_statistics_plausible_small_effect"
    if suppression_fraction <= 0.30:
        return "paper_statistics_borderline"
    return "paper_statistics_unlikely_alone"


def _interpretation_from_multiplier(required_high_signal_multiplier: float) -> str:
    if required_high_signal_multiplier > 1.0:
        return "raw_pair_is_already_flatter_than_target_or_needs_high_signal_amplification"
    suppression_fraction = 1.0 - required_high_signal_multiplier
    if suppression_fraction <= 0.30:
        return "finite_count_iqr_or_vendor_size_distribution_could_contribute"
    return "would_require_large_high_diameter_signal_suppression"


def sensitivity_rows(
    decomposition: pd.DataFrame,
    *,
    target_exponent: float = TARGET_EXPONENT,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for _, row in decomposition.iterrows():
        limiting_pair = str(row.get("limiting_pair", ""))
        if "-" not in limiting_pair:
            continue
        low_nm, high_nm = _pair_bounds(limiting_pair)
        raw_pair_slope = _safe_float(row.get("limiting_pair_slope"))
        if not np.isfinite(raw_pair_slope):
            continue
        log_diameter_ratio = math.log(high_nm / low_nm)
        required_high_signal_multiplier = math.exp(
            (target_exponent - raw_pair_slope) * log_diameter_ratio
        )
        suppression_fraction = max(0.0, 1.0 - required_high_signal_multiplier)
        amplification_fraction = max(0.0, required_high_signal_multiplier - 1.0)
        required_response_gamma_pair = (
            target_exponent / raw_pair_slope if raw_pair_slope > 0 else float("nan")
        )
        low_value = _safe_float(row.get(f"au{low_nm}_value"))
        high_value = _safe_float(row.get(f"au{high_nm}_value"))
        required_high_value = (
            high_value * required_high_signal_multiplier
            if np.isfinite(high_value)
            else float("nan")
        )
        rows.append(
            {
                "schema_id": SCHEMA_ID,
                "claim_level": "read_only_paper_statistics_boundary_not_event_resample",
                "candidate_id": row.get("candidate_id"),
                "family_id": row.get("family_id"),
                "observable": row.get("observable"),
                "wavelength_nm": int(row.get("wavelength_nm")),
                "geometry": row.get("geometry"),
                "limiting_pair": limiting_pair,
                "low_diameter_nm": low_nm,
                "high_diameter_nm": high_nm,
                "raw_pair_slope": raw_pair_slope,
                "target_exponent": float(target_exponent),
                "raw_pair_residual_vs_target": raw_pair_slope - target_exponent,
                "required_high_signal_multiplier": required_high_signal_multiplier,
                "required_high_signal_suppression_fraction": suppression_fraction,
                "required_high_signal_suppression_percent": (
                    100.0 * suppression_fraction
                ),
                "required_high_signal_amplification_fraction": amplification_fraction,
                "required_high_signal_amplification_percent": (
                    100.0 * amplification_fraction
                ),
                "required_response_gamma_pair": required_response_gamma_pair,
                "low_pair_value": low_value,
                "high_pair_value": high_value,
                "required_high_pair_value_after_statistics": required_high_value,
                "paper_statistics_status": _status_from_multiplier(
                    required_high_signal_multiplier
                ),
                "interpretation": _interpretation_from_multiplier(
                    required_high_signal_multiplier
                ),
            }
        )
    return pd.DataFrame(rows)


def summarize_rows(rows: pd.DataFrame) -> pd.DataFrame:
    if rows.empty:
        return pd.DataFrame()
    grouped = rows.groupby(["candidate_id", "observable"], dropna=False)
    summary = grouped.agg(
        case_count=("candidate_id", "size"),
        median_required_high_signal_suppression_percent=(
            "required_high_signal_suppression_percent",
            "median",
        ),
        min_required_high_signal_suppression_percent=(
            "required_high_signal_suppression_percent",
            "min",
        ),
        max_required_high_signal_suppression_percent=(
            "required_high_signal_suppression_percent",
            "max",
        ),
        median_required_response_gamma_pair=(
            "required_response_gamma_pair",
            "median",
        ),
        cases_unlikely_alone=(
            "paper_statistics_status",
            lambda values: int(
                (values == "paper_statistics_unlikely_alone").sum()
            ),
        ),
        cases_borderline=(
            "paper_statistics_status",
            lambda values: int((values == "paper_statistics_borderline").sum()),
        ),
        cases_plausible_small=(
            "paper_statistics_status",
            lambda values: int(
                (values == "paper_statistics_plausible_small_effect").sum()
            ),
        ),
        cases_already_flatter_or_amplification=(
            "paper_statistics_status",
            lambda values: int(
                (
                    values
                    == "already_flatter_than_target_or_requires_amplification"
                ).sum()
            ),
        ),
    ).reset_index()
    summary["paper_statistics_overall_status"] = np.where(
        summary["cases_unlikely_alone"].gt(0),
        "unlikely_alone",
        np.where(
            summary["cases_borderline"].gt(0),
            "borderline_contributor",
            np.where(
                summary["cases_already_flatter_or_amplification"].gt(0),
                "already_flatter_than_target_or_requires_amplification",
                "plausible_small_contributor",
            ),
        ),
    )
    return summary.sort_values(
        [
            "paper_statistics_overall_status",
            "median_required_high_signal_suppression_percent",
            "candidate_id",
            "observable",
        ],
        ignore_index=True,
    )


def write_outputs(
    *,
    input_path: Path,
    output_dir: Path,
    target_exponent: float = TARGET_EXPONENT,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    decomposition = pd.read_csv(input_path)
    rows = sensitivity_rows(decomposition, target_exponent=target_exponent)
    summary = summarize_rows(rows)
    raw_path = output_dir / RAW_FILENAME
    summary_path = output_dir / SUMMARY_FILENAME
    json_path = output_dir / JSON_FILENAME
    report_path = output_dir / REPORT_FILENAME
    rows.to_csv(raw_path, index=False)
    summary.to_csv(summary_path, index=False)
    payload = {
        "schema_id": SCHEMA_ID,
        "generated_at_unix": time.time(),
        "input_path": str(input_path),
        "target_exponent": float(target_exponent),
        "claim_level": "read_only_paper_statistics_boundary_not_event_resample",
        "event_level_distribution_available": False,
        "ev_full_grid_writeback": False,
        "selected_annulus_changed": False,
        "global_material_defaults_changed": False,
        "row_count": int(len(rows)),
        "summary_row_count": int(len(summary)),
        "status_counts": rows["paper_statistics_status"].value_counts().to_dict()
        if not rows.empty
        else {},
        "conclusion": (
            "paper_statistics_or_vendor_size_distribution_can_contribute_but_"
            "cannot_be_signed_without_event_level_pulses_or_measured_size_distribution"
        ),
    }
    rate_calib.write_json(json_path, payload)
    display_cols = [
        "candidate_id",
        "observable",
        "case_count",
        "median_required_high_signal_suppression_percent",
        "max_required_high_signal_suppression_percent",
        "median_required_response_gamma_pair",
        "cases_unlikely_alone",
        "paper_statistics_overall_status",
    ]
    lines = [
        "# Tsuyama Paper-Statistics Sensitivity Boundary",
        "",
        "## Boundary",
        "",
        "- This is a read-only boundary calculation over Phase 2.10 size-response decomposition.",
        "- It does not resample event-level pulses; those distributions are not present in the summary CSV.",
        "- It estimates how much the high-diameter member of the limiting pair would need to be suppressed to match the target exponent.",
        "- It does not modify EV full-grid, selected-annulus bounds, or material defaults.",
        "",
        "## Summary",
        "",
        f"- Status counts: `{json.dumps(payload['status_counts'], ensure_ascii=False)}`.",
        f"- Conclusion: `{payload['conclusion']}`.",
        "",
        rate_calib.dataframe_to_markdown(summary.loc[:, display_cols].head(24)),
        "",
        "## Output Files",
        "",
        f"- `{raw_path}`",
        f"- `{summary_path}`",
        f"- `{json_path}`",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows, summary, payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bound paper-statistics/IQR contribution to Tsuyama size-response."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help=(
            "Phase 2.10 size-response case decomposition CSV. "
            f"Known D2.1 path: {DEFAULT_INPUT_DECOMPOSITION}"
        ),
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--target-exponent", type=float, default=TARGET_EXPONENT)
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    rows, _, payload = write_outputs(
        input_path=args.input,
        output_dir=args.output_dir,
        target_exponent=args.target_exponent,
    )
    print(
        f"Wrote {len(rows)} paper-statistics sensitivity rows to {args.output_dir} "
        f"({payload['claim_level']})"
    )


if __name__ == "__main__":
    main()
