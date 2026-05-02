#!/usr/bin/env python3

"""Scan selected-annulus edge-norm windows on Tsuyama 2022 NODI cases."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_PARENT = PROJECT_ROOT.parent
for candidate_path in (str(PROJECT_ROOT), str(PROJECT_PARENT)):
    if candidate_path not in sys.path:
        sys.path.insert(0, candidate_path)

from nodi_simulator.design_claim_governance import (
    CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS,
    PAPER_ALIGNMENT_TARGETS,
    PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1,
    assert_paper_alignment_target_metadata,
    require_claim_level,
    require_paper_alignment_target,
)
from tools import tsuyama_selected_annulus_joint_fit as joint


OUTPUT_DIR = PROJECT_ROOT / "results" / "tsuyama_annulus_ratio_sensitivity"
TARGET_SCHEMA_ID = "tsuyama_2022_selected_annulus_ratio_sensitivity_v1"
ANNULUS_WINDOWS: tuple[tuple[float, float], ...] = (
    (0.3, 0.7),
    (0.4, 0.7),
    (0.4, 0.8),
    (0.5, 0.8),
    (0.5, 0.9),
    (0.6, 0.9),
    (0.0, 1.0),
)
RAW_FILENAME = "annulus_ratio_sensitivity_raw_v1.csv"
SUMMARY_FILENAME = "annulus_ratio_sensitivity_summary_v1.csv"
AGGREGATE_FILENAME = "annulus_ratio_sensitivity_aggregate_v1.csv"
META_FILENAME = "annulus_ratio_sensitivity_meta_v1.json"
DECISION_FILENAME = "annulus_ratio_sensitivity_decision_v1.md"


def annulus_window_id(inner: float, outer: float) -> str:
    def _part(value: float) -> str:
        return f"{value:.2f}".rstrip("0").rstrip(".").replace(".", "p")

    return f"{_part(inner)}_{_part(outer)}"


def candidate_with_annulus_window(
    candidate: joint.JointFitCandidate,
    *,
    inner: float,
    outer: float,
) -> joint.JointFitCandidate:
    overrides = dict(candidate.cfg_overrides)
    overrides["selected_annulus_edge_norm_min"] = float(inner)
    overrides["selected_annulus_edge_norm_max"] = float(outer)
    return replace(
        candidate,
        candidate_id=(
            f"{candidate.candidate_id}__annulus_{annulus_window_id(inner, outer)}"
        ),
        cfg_overrides=overrides,
    )


def _parse_csv_arg(value: str | None) -> list[str] | None:
    if value is None:
        return None
    parsed = [part.strip() for part in value.split(",") if part.strip()]
    return parsed or None


def _window_payload(inner: float, outer: float) -> dict[str, float | str]:
    return {
        "annulus_window_id": annulus_window_id(inner, outer),
        "selected_annulus_edge_norm_min": float(inner),
        "selected_annulus_edge_norm_max": float(outer),
    }


def run_ratio_sensitivity(
    *,
    base_candidate_ids: list[str] | None,
    variant_ids: list[str] | None,
    annulus_windows: tuple[tuple[float, float], ...],
    n_events: int,
    random_seed: int | None = None,
    random_seeds: list[int] | None = None,
    n_workers: int,
    scenario_id: str,
    output_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    seeds = list(random_seeds or ([random_seed] if random_seed is not None else [42]))
    base_candidates = joint.build_joint_candidates(
        base_candidate_ids=base_candidate_ids,
        variant_ids=variant_ids,
    )
    raw_frames: list[pd.DataFrame] = []
    summary_rows: list[dict[str, Any]] = []
    start = time.time()
    for inner, outer in annulus_windows:
        for base_candidate in base_candidates:
            for seed in seeds:
                candidate = candidate_with_annulus_window(
                    base_candidate,
                    inner=inner,
                    outer=outer,
                )
                print(
                    "[annulus-sensitivity] "
                    f"{candidate.candidate_id} ({inner:.2f}, {outer:.2f}) "
                    f"seed={seed}",
                    flush=True,
                )
                rows = joint.run_joint_candidate_sweep(
                    candidate,
                    n_events=n_events,
                    random_seed=seed,
                    n_workers=n_workers,
                    scenario_id=scenario_id,
                )
                rows = rows.assign(**_window_payload(inner, outer), random_seed=int(seed))
                raw_frames.append(rows)
                summary = joint.summarize_joint_candidate(
                    rows,
                    candidate,
                    n_events=n_events,
                    random_seed=seed,
                    n_workers=n_workers,
                    scenario_id=scenario_id,
                )
                summary.setdefault("base_candidate_id", candidate.base_candidate_id)
                summary.setdefault("random_seed", int(seed))
                summary.update(_window_payload(inner, outer))
                summary_rows.append(summary)

    raw = pd.concat(raw_frames, ignore_index=True) if raw_frames else pd.DataFrame()
    for record in raw.to_dict(orient="records"):
        assert_paper_alignment_target_metadata(
            PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1,
            record,
        )
    summary = pd.DataFrame(summary_rows).sort_values(
        ["joint_fit_score", "candidate_id"],
        ignore_index=True,
    )
    aggregate = _aggregate_summary(summary)
    raw_path = output_dir / RAW_FILENAME
    summary_path = output_dir / SUMMARY_FILENAME
    aggregate_path = output_dir / AGGREGATE_FILENAME
    raw.to_csv(raw_path, index=False)
    summary.to_csv(summary_path, index=False)
    aggregate.to_csv(aggregate_path, index=False)

    top = aggregate.iloc[0].to_dict() if not aggregate.empty else {}
    meta = {
        "schema": TARGET_SCHEMA_ID,
        "analysis_lane": "selected_annulus",
        "claim_level": require_claim_level(
            CLAIM_LEVEL_PAPER_ALIGNED_2022_NODI_PROXY_LENS
        ),
        "paper_alignment_target": require_paper_alignment_target(
            PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1
        ),
        "paper_alignment_target_metadata_status": "validated_per_raw_row",
        "paper_alignment_target_required_metadata_fields": PAPER_ALIGNMENT_TARGETS[
            PAPER_ALIGNMENT_TARGET_TSUYAMA_2022_NODI_TABLE_S1
        ]["required_metadata_fields"],
        "joint_fit_score_interpretation": joint.JOINT_FIT_SCORE_INTERPRETATION,
        "joint_fit_score_direction": "lower_is_better",
        "signal_strength_threshold": {
            "metric": "absolute_mean_delta_over_pooled_std",
            "threshold": 1.5,
            "canonical_change_rule": (
                "Consider changing the canonical annulus window only when the "
                "candidate window beats the current 0.5-0.8 window by this "
                "threshold and the direction is consistent across candidates."
            ),
        },
        "cases": [list(case) for case in joint.JOINT_CASES],
        "gold_diameters_nm": list(joint.GOLD_DIAMETERS_NM),
        "silver_diameters_nm": list(joint.SILVER_DIAMETERS_NM),
        "annulus_windows": [
            _window_payload(inner, outer) for inner, outer in annulus_windows
        ],
        "base_candidate_ids": base_candidate_ids or list(joint.DEFAULT_JOINT_CANDIDATES),
        "variant_ids": variant_ids or ["paper_10sigma"],
        "n_events": int(n_events),
        "n_workers": int(n_workers),
        "random_seeds": [int(seed) for seed in seeds],
        "scenario_config_id": scenario_id,
        "raw_rows": int(len(raw)),
        "summary_rows": int(len(summary)),
        "aggregate_rows": int(len(aggregate)),
        "runtime_s": time.time() - start,
        "raw_path": str(raw_path),
        "summary_path": str(summary_path),
        "aggregate_path": str(aggregate_path),
        "suggested_canonical_by_mean_joint_fit_score": {
            key: top.get(key)
            for key in (
                "annulus_window_id",
                "selected_annulus_edge_norm_min",
                "selected_annulus_edge_norm_max",
                "candidate_id",
                "joint_fit_score_mean",
                "joint_fit_score_std",
                "seed_count",
            )
        },
        "decision_caveat": (
            "This diagnostic ranks annulus windows against the existing "
            "selected-annulus joint-fit score, which is a loss-style sum of "
            "penalties where lower is better. A canonical change still needs "
            "human review of detection-rate, signal-ratio, size-response, and "
            "EV-route stability effects before full-grid recompute."
        ),
    }
    _write_json(output_dir / META_FILENAME, meta)
    _write_decision(output_dir / DECISION_FILENAME, meta=meta, summary=summary)
    return raw, summary, meta


def _aggregate_summary(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()
    grouped = (
        summary.groupby(
            [
                "annulus_window_id",
                "selected_annulus_edge_norm_min",
                "selected_annulus_edge_norm_max",
                "candidate_id",
                "base_candidate_id",
            ],
            dropna=False,
        )
        .agg(
            joint_fit_score_mean=("joint_fit_score", "mean"),
            joint_fit_score_std=("joint_fit_score", "std"),
            joint_fit_score_min=("joint_fit_score", "min"),
            joint_fit_score_max=("joint_fit_score", "max"),
            seed_count=("random_seed", "nunique"),
            paper_fit_statuses=("paper_fit_status", lambda values: ",".join(sorted(set(map(str, values))))),
        )
        .reset_index()
        .sort_values(["joint_fit_score_mean", "candidate_id"], ignore_index=True)
    )
    return grouped


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_decision(path: Path, *, meta: dict[str, Any], summary: pd.DataFrame) -> None:
    display_columns = [
        column
        for column in (
            "annulus_window_id",
            "selected_annulus_edge_norm_min",
            "selected_annulus_edge_norm_max",
            "candidate_id",
            "random_seed",
            "joint_fit_score",
            "selected_rate_score",
            "signal_ratio_score",
            "size_exponent_score",
            "annulus_fraction_min",
            "paper_fit_status",
        )
        if column in summary
    ]
    display_summary = summary[display_columns] if display_columns else summary
    lines = [
        "# Tsuyama selected-annulus ratio sensitivity",
        "",
        f"- schema: `{meta['schema']}`",
        f"- target: `{meta['paper_alignment_target']}`",
        f"- score direction: `{meta['joint_fit_score_direction']}`",
        f"- cases: `{meta['cases']}`",
        f"- gold diameters nm: `{meta['gold_diameters_nm']}`",
        f"- silver diameters nm: `{meta['silver_diameters_nm']}`",
        f"- scenario: `{meta['scenario_config_id']}`",
        f"- n_events: `{meta['n_events']}`",
        f"- n_workers: `{meta['n_workers']}`",
        "",
        "## Score Direction",
        "",
        (
            "**Lower is better.** `joint_fit_score` is a loss-style sum of "
            "penalties; lower mean penalty is closer to the Tsuyama 2022 NODI "
            "Table S1 target under this surrogate lane."
        ),
        "",
        "Sub-scores: `selected_rate_score` tracks detection-rate target bands; "
        "`signal_ratio_score` tracks Ag/Au signal-ratio residuals; "
        "`size_exponent_score` tracks Au size-response residuals; "
        "`snr_ratio_score` tracks the Au30/Au20 SNR-ratio diagnostic; "
        "transfer/size regularization and hard guardrail penalties discourage "
        "overfitted paper-transfer corrections.",
        "",
        "Canonical-change signal rule: compare candidate windows against the "
        "current `0.5-0.8` default using "
        "`abs(mean_delta) / pooled_std > 1.5` and require directionally "
        "consistent improvement across candidate families before changing the "
        "default.",
        "",
        "## Suggested canonical by mean joint-fit penalty",
        "",
    ]
    suggested = meta["suggested_canonical_by_mean_joint_fit_score"]
    for key, value in suggested.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Top rows",
            "",
            "```text",
            display_summary.head(10).to_string(index=False)
            if not display_summary.empty
            else "No rows.",
            "```",
            "",
            "## Seed-Aggregated Ranking",
            "",
            f"Aggregate CSV: `{meta['aggregate_path']}`",
            "",
            "## Caveat",
            "",
            str(meta["decision_caveat"]),
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Scan selected-annulus edge-norm windows on Tsuyama 2022 NODI cases."
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--n-events", type=int, default=3000)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument(
        "--random-seeds",
        default=None,
        help="Comma-separated random seeds. Overrides --random-seed when set.",
    )
    parser.add_argument("--scenario-id", default="nodi_2022_10sigma_single")
    parser.add_argument(
        "--base-candidate-ids",
        default="baseline_current_estimates",
        help="Comma-separated base candidate IDs.",
    )
    parser.add_argument(
        "--variant-ids",
        default="paper_10sigma",
        help="Comma-separated joint-fit variant IDs.",
    )
    args = parser.parse_args(argv)
    run_ratio_sensitivity(
        base_candidate_ids=_parse_csv_arg(args.base_candidate_ids),
        variant_ids=_parse_csv_arg(args.variant_ids),
        annulus_windows=ANNULUS_WINDOWS,
        n_events=args.n_events,
        random_seed=args.random_seed,
        random_seeds=(
            [int(part) for part in _parse_csv_arg(args.random_seeds) or []] or None
        ),
        n_workers=args.workers,
        scenario_id=str(args.scenario_id),
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
