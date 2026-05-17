#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
for candidate in (str(PROJECT_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from tools.audits import tsuyama_detection_rate_calibration as calib
from tools.audits import tsuyama_gold_aligned_detection_lane as lane

OUTPUT_DIR = PROJECT_ROOT / "results" / "tsuyama_detection_rule_sensitivity"
BASE_ESTIMATE_ID = "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_noise_0p0065"
BASE_ESTIMATE_OVERRIDES: dict[str, Any] = {
    "mean_flow_velocity_m_s": 1.5e-4,
    "noise_std": 0.0065,
    "shot_noise_scale": 0.0005,
    "post_readout_noise_std": 0.001,
    "initial_position_distribution_mode": "flux_uniform_mixture_surrogate",
    "initial_position_flux_weighted_mixture_fraction": 0.10,
}
RULE_FIELDS = ("threshold_sigma", "min_peak_width_s")


def _format_rule_value(value: float, *, unit: str = "") -> str:
    scaled = value * 1e3 if unit == "ms" else value
    text = f"{scaled:.6g}".replace("-", "m").replace(".", "p")
    return text.replace("+", "")


def detection_rule_candidate_catalog() -> list[calib.CalibrationCandidate]:
    threshold_sigmas = (5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0)
    min_peak_widths_s = (0.5e-3, 1.0e-3, 1.5e-3, 2.0e-3, 2.5e-3, 3.0e-3)
    candidates: list[calib.CalibrationCandidate] = []
    for sigma in threshold_sigmas:
        for min_width_s in min_peak_widths_s:
            overrides = {
                **BASE_ESTIMATE_OVERRIDES,
                "threshold_sigma": sigma,
                "min_peak_width_s": min_width_s,
            }
            candidate_id = (
                f"rule_sigma_{_format_rule_value(sigma)}"
                f"_width_{_format_rule_value(min_width_s, unit='ms')}ms"
                f"__{BASE_ESTIMATE_ID}"
            )
            rationale = (
                "Detection-rule sensitivity around the best estimated-parameter "
                f"candidate: threshold_sigma={sigma:g}, "
                f"min_peak_width_ms={min_width_s * 1e3:g}."
            )
            candidates.append(
                calib.CalibrationCandidate(
                    candidate_id=candidate_id,
                    overrides=overrides,
                    rationale=rationale,
                )
            )
    return candidates


def candidate_by_id() -> dict[str, calib.CalibrationCandidate]:
    return {candidate.candidate_id: candidate for candidate in detection_rule_candidate_catalog()}


def attach_rule_target_score(summary: pd.DataFrame) -> pd.DataFrame:
    """Remove the paper-baseline threshold-realism penalty for this rule lane."""
    out = summary.copy()
    if "rule_target_score" in out.columns:
        return out
    out["rule_target_score"] = out["calibration_score"]
    if {"gold_anchor_pass", "gold_anchor_primary_blocker"} <= set(out.columns):
        threshold_realism = (
            (~out["gold_anchor_pass"].astype(bool))
            & (out["gold_anchor_primary_blocker"].astype(str) == "threshold_realism")
        )
        out.loc[threshold_realism, "rule_target_score"] = (
            out.loc[threshold_realism, "rule_target_score"] - 2.0
        )
    out["rule_score_note"] = (
        "calibration_score minus threshold_realism penalty for intentional "
        "detection-rule sensitivity when applicable"
    )
    return out


def select_top_candidates(
    summary: pd.DataFrame,
    *,
    candidates: list[calib.CalibrationCandidate],
    top_k: int,
) -> list[calib.CalibrationCandidate]:
    catalog = {candidate.candidate_id: candidate for candidate in candidates}
    ranked = attach_rule_target_score(summary).sort_values(
        ["rule_target_score", "candidate_id"],
        ignore_index=True,
    )
    anchor_id = (
        f"rule_sigma_10_width_2p5ms__{BASE_ESTIMATE_ID}"
    )
    selected_ids: list[str] = []
    if anchor_id in catalog:
        selected_ids.append(anchor_id)
    for candidate_id in ranked["candidate_id"].astype(str).tolist():
        if candidate_id not in selected_ids:
            selected_ids.append(candidate_id)
        if len(selected_ids) >= top_k:
            break
    return [catalog[candidate_id] for candidate_id in selected_ids[:top_k]]


def _blank_gate(row: dict[str, Any]) -> dict[str, Any]:
    ub_trace = float(row.get("blank_false_positive_wilson_ub_per_trace", 1.0))
    ub_s = float(row.get("blank_false_positive_wilson_ub_per_s", 1.0))
    pass_gate = bool(ub_trace <= 1e-3 or ub_s <= 1e-2)
    return {
        "blank_gate_pass": pass_gate,
        "blank_gate_primary_blocker": "pass" if pass_gate else "blank_fpr_wilson_ub",
    }


def run_candidate_blank_checks(
    candidates: list[calib.CalibrationCandidate],
    *,
    n_blank_traces: int,
    random_seed: int,
    output_dir: Path,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    t0 = time.time()
    for index, candidate in enumerate(candidates, start=1):
        print(
            f"[blank] {index}/{len(candidates)} {candidate.candidate_id}",
            flush=True,
        )
        cfg = calib.build_candidate_cfg(
            candidate,
            n_events=1,
            random_seed=random_seed,
        )
        stats = lane.run_synthetic_blank(
            cfg,
            n_blank_traces=n_blank_traces,
            random_seed=random_seed + index * 1009,
            scenario_kind="nodi_single",
        )
        row: dict[str, Any] = {
            "candidate_id": candidate.candidate_id,
            "target_schema_id": calib.TARGET_SCHEMA_ID,
            "scenario_config_id": calib.CALIBRATION_SCENARIO_ID,
            "base_estimate_id": BASE_ESTIMATE_ID,
            "blank_model_source": "synthetic_iid_zero_signal",
            "blank_claim_level": "synthetic_guardrail_not_empirical_calibration",
            "threshold_sigma": float(cfg.threshold_sigma),
            "min_peak_width_s": float(cfg.min_peak_width_s),
            "min_peak_width_ms": float(cfg.min_peak_width_s * 1e3),
            "min_peak_interval_s": float(cfg.min_peak_interval_s),
            "threshold_tail": cfg.threshold_tail,
            "pulse_width_measure_mode": cfg.pulse_width_measure_mode,
            **stats,
        }
        row.update(_blank_gate(row))
        rows.append(row)
    df = pd.DataFrame(rows)
    path = output_dir / "verify_blank_synthetic_v1.csv"
    df.to_csv(path, index=False)
    calib.write_json(
        output_dir / "verify_blank_synthetic_meta_v1.json",
        {
            "n_blank_traces": int(n_blank_traces),
            "random_seed": int(random_seed),
            "candidate_count": int(len(candidates)),
            "rows": int(len(df)),
            "runtime_s": time.time() - t0,
            "path": str(path),
        },
    )
    return df


def write_rule_report(
    output_dir: Path,
    *,
    verify_summary: pd.DataFrame,
    screen_meta: dict[str, Any],
    verify_meta: dict[str, Any],
    blank_summary: pd.DataFrame | None,
) -> Path:
    report_path = output_dir / "tsuyama_detection_rule_sensitivity_report.md"
    verify_for_report = attach_rule_target_score(verify_summary).sort_values(
        ["rule_target_score", "candidate_id"],
        ignore_index=True,
    )
    for field in RULE_FIELDS:
        protected_name = f"protected_{field}"
        if field not in verify_for_report.columns and protected_name in verify_for_report.columns:
            verify_for_report[field] = verify_for_report[protected_name]
    selected_candidate_rate_cols = [
        f"au{diameter_nm}_median_selected_detector_mode_candidate_detection_rate"
        for diameter_nm in lane.GOLD_DIAMETERS_NM
    ]
    selected_candidate_fraction_cols = [
        f"au{diameter_nm}_median_selected_detector_mode_candidate_fraction"
        for diameter_nm in lane.GOLD_DIAMETERS_NM
    ]
    selected_annulus_rate_cols = [
        f"au{diameter_nm}_median_selected_detector_mode_annulus_detection_rate"
        for diameter_nm in lane.GOLD_DIAMETERS_NM
    ]
    selected_annulus_fraction_cols = [
        f"au{diameter_nm}_median_selected_detector_mode_annulus_fraction"
        for diameter_nm in lane.GOLD_DIAMETERS_NM
    ]
    top_cols = [
        "candidate_id",
        "calibration_score",
        "rule_target_score",
        "target_fit_status",
        "au20_median_detection_rate",
        "au30_median_detection_rate",
        "au40_median_detection_rate",
        "au60_median_detection_rate",
        *selected_candidate_rate_cols,
        *selected_candidate_fraction_cols,
        *selected_annulus_rate_cols,
        *selected_annulus_fraction_cols,
        "threshold_sigma",
        "min_peak_width_s",
        "mean_flow_velocity_m_s",
        "noise_std",
        "shot_noise_scale",
        "post_readout_noise_std",
        "initial_position_distribution_mode",
        "initial_position_flux_weighted_mixture_fraction",
    ]
    top_cols = [column for column in top_cols if column in verify_for_report.columns]
    top_markdown = calib.dataframe_to_markdown(verify_for_report.head(12)[top_cols])
    best = verify_for_report.iloc[0].to_dict() if not verify_for_report.empty else {}
    blank_markdown = "_Not run._"
    if blank_summary is not None and not blank_summary.empty:
        blank_cols = [
            "candidate_id",
            "threshold_sigma",
            "min_peak_width_ms",
            "n_blank_traces",
            "n_blank_detected",
            "blank_false_positive_wilson_ub_per_trace",
            "blank_gate_pass",
            "blank_gate_primary_blocker",
        ]
        blank_markdown = calib.dataframe_to_markdown(blank_summary[blank_cols])
    lines = [
        "# Tsuyama Detection-Rule Sensitivity",
        "",
        "## Boundary",
        "",
        "- This lane intentionally changes detection rules.",
        "- It is not the paper-protected `10 sigma / 2.5 ms` baseline.",
        "- Estimated physical/surrogate parameters are fixed to the current best calibration candidate.",
        f"- base_estimate_id: `{BASE_ESTIMATE_ID}`",
        f"- base_estimate_overrides: `{json.dumps(BASE_ESTIMATE_OVERRIDES, sort_keys=True, separators=(',', ':'))}`",
        "- Particle-size distribution is unchanged.",
        "",
        "## Rule Grid",
        "",
        "- `threshold_sigma`: `5, 6, 7, 8, 9, 10, 11, 12`",
        "- `min_peak_width_s`: `0.5, 1.0, 1.5, 2.0, 2.5, 3.0 ms`",
        "",
        "## Target Bands",
        "",
        *[
            (
                f"- Au{diameter_nm}: `{target['low']:.2f}-{target['high']:.2f}` "
                f"(target `{target['target']:.2f}`) - {target['basis']}"
            )
            for diameter_nm, target in calib.TARGET_BANDS.items()
        ],
        "",
        "## Run Metadata",
        "",
        f"- screen_events: `{screen_meta['n_events']}`",
        f"- verify_events: `{verify_meta['n_events']}`",
        f"- workers: `{verify_meta['n_workers']}`",
        f"- scenario: `{calib.CALIBRATION_SCENARIO_ID}`",
        f"- cases: `{calib.CALIBRATION_CASES}`",
        "",
        "## Best Verified Candidate",
        "",
        f"- candidate_id: `{best.get('candidate_id', 'none')}`",
        f"- calibration_score: `{best.get('calibration_score', float('nan'))}`",
        f"- target_fit_status: `{best.get('target_fit_status', 'none')}`",
        f"- threshold_sigma: `{best.get('threshold_sigma', float('nan'))}`",
        f"- min_peak_width_s: `{best.get('min_peak_width_s', float('nan'))}`",
        f"- overrides: `{best.get('candidate_overrides_json', '{}')}`",
        "",
        "## Top Verified Candidates",
        "",
        top_markdown,
        "",
        "## Synthetic Blank Guardrail",
        "",
        blank_markdown,
        "",
        "## Output Files",
        "",
        "- `screen_gold_rows_v1.csv`",
        "- `screen_candidate_summary_v1.csv`",
        "- `verify_gold_rows_v1.csv`",
        "- `verify_candidate_summary_v1.csv`",
        "- `verify_blank_synthetic_v1.csv`",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sweep Tsuyama detection-rule sensitivity around the best estimated-parameter candidate."
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--screen-events", type=int, default=1000)
    parser.add_argument("--verify-events", type=int, default=10000)
    parser.add_argument("--top-k", type=int, default=12)
    parser.add_argument("--blank-traces", type=int, default=5000)
    parser.add_argument(
        "--candidate-ids",
        default="",
        help="Comma-separated candidate IDs to run; empty means the full rule grid.",
    )
    parser.add_argument(
        "--screen-only",
        action="store_true",
        help="Run rule-grid screening only and skip top-candidate verification.",
    )
    parser.add_argument(
        "--skip-blank",
        action="store_true",
        help="Skip synthetic blank guardrail for verified candidates.",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Write the report from existing CSV and JSON outputs.",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    output_dir = Path(args.output_dir)
    if args.report_only:
        verify_summary = pd.read_csv(output_dir / "verify_candidate_summary_v1.csv")
        blank_path = output_dir / "verify_blank_synthetic_v1.csv"
        blank_summary = pd.read_csv(blank_path) if blank_path.exists() else None
        with (output_dir / "screen_meta_v1.json").open("r", encoding="utf-8") as fh:
            screen_meta = json.load(fh)
        with (output_dir / "verify_meta_v1.json").open("r", encoding="utf-8") as fh:
            verify_meta = json.load(fh)
        report_path = write_rule_report(
            output_dir,
            verify_summary=verify_summary,
            screen_meta=screen_meta,
            verify_meta=verify_meta,
            blank_summary=blank_summary,
        )
        print(json.dumps({"report_path": str(report_path)}, ensure_ascii=False, indent=2))
        return

    candidates = detection_rule_candidate_catalog()
    if str(args.candidate_ids).strip():
        catalog = candidate_by_id()
        selected_ids = [
            item.strip()
            for item in str(args.candidate_ids).split(",")
            if item.strip()
        ]
        unknown = [candidate_id for candidate_id in selected_ids if candidate_id not in catalog]
        if unknown:
            raise ValueError(f"Unknown candidate IDs: {unknown}")
        candidates = [catalog[candidate_id] for candidate_id in selected_ids]

    screen_raw, screen_summary, screen_meta = calib.run_stage(
        candidates=candidates,
        n_events=int(args.screen_events),
        random_seed=int(args.random_seed),
        n_workers=int(args.workers),
        output_dir=output_dir,
        stage_name="screen",
    )
    _ = screen_raw
    screen_summary = attach_rule_target_score(screen_summary).sort_values(
        ["rule_target_score", "candidate_id"],
        ignore_index=True,
    )
    screen_summary.to_csv(output_dir / "screen_candidate_summary_v1.csv", index=False)
    if args.screen_only:
        print(json.dumps(screen_meta, ensure_ascii=False, indent=2))
        return

    verify_candidates = select_top_candidates(
        screen_summary,
        candidates=candidates,
        top_k=int(args.top_k),
    )
    verify_raw, verify_summary, verify_meta = calib.run_stage(
        candidates=verify_candidates,
        n_events=int(args.verify_events),
        random_seed=int(args.random_seed),
        n_workers=int(args.workers),
        output_dir=output_dir,
        stage_name="verify",
    )
    _ = verify_raw
    verify_summary = attach_rule_target_score(verify_summary).sort_values(
        ["rule_target_score", "candidate_id"],
        ignore_index=True,
    )
    verify_summary.to_csv(output_dir / "verify_candidate_summary_v1.csv", index=False)

    blank_summary = None
    if not bool(args.skip_blank):
        blank_summary = run_candidate_blank_checks(
            verify_candidates,
            n_blank_traces=int(args.blank_traces),
            random_seed=int(args.random_seed),
            output_dir=output_dir,
        )

    report_path = write_rule_report(
        output_dir,
        verify_summary=verify_summary,
        screen_meta=screen_meta,
        verify_meta=verify_meta,
        blank_summary=blank_summary,
    )
    print(
        json.dumps(
            {
                "screen_meta": screen_meta,
                "verify_meta": verify_meta,
                "report_path": str(report_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
