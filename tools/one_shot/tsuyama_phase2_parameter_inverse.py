#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
for candidate in (str(PROJECT_ROOT),):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from tools.audits import tsuyama_detection_rate_calibration as rate_calib
from tools.audits import tsuyama_selected_annulus_joint_fit as joint_fit

OUTPUT_DIR = PROJECT_ROOT / "results" / "tsuyama_phase2_parameter_inverse_v1"
SCHEMA_ID = "tsuyama_phase2_family_ladder_parameter_inverse_v1"
RAW_FILENAME = "phase2_parameter_inverse_raw_v1.csv"
SUMMARY_FILENAME = "phase2_parameter_inverse_summary_v1.csv"
BEST_FILENAME = "phase2_best_candidates_v1.csv"
GUARDRAIL_FILENAME = "phase2_guardrail_failures_v1.csv"
META_FILENAME = "phase2_parameter_inverse_meta_v1.json"
REPORT_FILENAME = "phase2_parameter_inverse_report_v1.md"
PLAN_FILENAME = "phase2_family_ladder_plan_v1.csv"


@dataclass(frozen=True)
class FamilySpec:
    family_id: str
    family_order: int
    description: str
    base_candidate_ids: tuple[str, ...]
    variant_ids: tuple[str, ...]


def family_specs() -> tuple[FamilySpec, ...]:
    return (
        FamilySpec(
            family_id="A_blank_threshold_noise",
            family_order=1,
            description="blank, threshold, colored noise, and post-readout noise",
            base_candidate_ids=(
                "baseline_current_estimates",
                "low_noise_stack",
                "blank_edge_low_noise_stack_uniform_accessible",
                "colored_ar1_0p0005_tau_1ms_low_noise_stack_uniform_accessible",
                "colored_ar1_0p001_tau_1ms_low_noise_stack_uniform_accessible",
            ),
            variant_ids=("paper_10sigma", "paper_5sigma_sensitivity"),
        ),
        FamilySpec(
            family_id="B_logger_lockin_pulse_width",
            family_order=2,
            description="logger, lock-in, and pulse-width policy",
            base_candidate_ids=(
                "logger_0p5ms_baseline_current",
                "logger_0p5ms_blank_edge_low_noise_stack_uniform_accessible",
                "logger_0p5ms_conservative_low_noise_stack_uniform_accessible",
                "tau_2ms",
                "tau_2ms_velocity_0p15mmps",
            ),
            variant_ids=("paper_10sigma", "paper_5sigma_sensitivity"),
        ),
        FamilySpec(
            family_id="C_transport_event_shape_fluxmix",
            family_order=3,
            description="transport, event shape, and fluxmix",
            base_candidate_ids=(
                "low_noise_stack_fluxmix_0p10",
                "low_noise_stack_fluxmix_0p25",
                "velocity_0p15mmps_low_noise_stack_fluxmix_0p10",
                "velocity_0p15mmps_low_noise_stack_fluxmix_0p25",
                "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_flowparabolic",
            ),
            variant_ids=("paper_10sigma", "paper_5sigma_sensitivity"),
        ),
        FamilySpec(
            family_id="D_reference_collection_rho_bfp",
            family_order=4,
            description="reference, collection, rho, and BFP source status",
            base_candidate_ids=(
                "rho_0p65",
                "rho_0p80",
                "refspace_0p25",
                "refspace_0p45",
                "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_rho_0p45",
                "velocity_0p15mmps_low_noise_stack_fluxmix_0p10_refspace_0p40",
            ),
            variant_ids=("paper_10sigma", "paper_5sigma_sensitivity"),
        ),
        FamilySpec(
            family_id="D2_operator_phase_bfp_raw",
            family_order=5,
            description="raw paper-aligned reference phase, BFP ROI, and collection operator",
            base_candidate_ids=(
                "tau_2ms_control",
                "tau_2ms_paper_aligned_phase_filter",
                "tau_2ms_refphase_flat",
                "tau_2ms_refphase_wide",
                "tau_2ms_global_refphi_plus_0p2",
                "tau_2ms_global_refphi_plus",
                "tau_2ms_global_refphi_plus_0p6",
                "tau_2ms_global_refphi_minus",
                "tau_2ms_collection_narrow",
                "tau_2ms_global_refphi_plus_collection_narrow",
                "tau_2ms_collection_wide",
                "tau_2ms_bfp_lobe_045",
                "tau_2ms_bfp_lobe_065",
            ),
            variant_ids=("paper_10sigma", "paper_5sigma_sensitivity"),
        ),
        FamilySpec(
            family_id="E_local_transfer_size_response",
            family_order=6,
            description="bounded local Ag transfer and Au size-response correction",
            base_candidate_ids=(
                "baseline_current_estimates",
                "low_noise_stack_uniform_accessible",
                "logger_0p5ms_blank_edge_low_noise_stack_fluxmix_0p25",
                "velocity_0p15mmps_low_noise_stack_fluxmix_0p10",
                "velocity_0p15mmps_fluxmix_0p10_flowparabolic_rho_0p45_noise_0p008",
            ),
            variant_ids=(
                "paper_5sigma_signal_transfer_fit",
                "paper_5sigma_signal_size_transfer_fit",
            ),
        ),
        FamilySpec(
            family_id="F_paper_reproduction_fit",
            family_order=7,
            description=(
                "paper reproduction-only size-response fit using declared global "
                "Au power-law correction without Ag transfer"
            ),
            base_candidate_ids=(
                "tau_2ms",
                "tau_2ms_control",
                "tau_2ms_global_refphi_plus",
                "tau_2ms_global_refphi_plus_0p6",
                "tau_2ms_global_refphi_plus_collection_narrow",
            ),
            variant_ids=("paper_5sigma_size_response_fit",),
        ),
    )


def select_family_specs(family_ids: list[str] | None) -> list[FamilySpec]:
    specs = list(family_specs())
    if not family_ids:
        return specs
    selected = set(family_ids)
    unknown = sorted(selected - {spec.family_id for spec in specs})
    if unknown:
        raise ValueError(f"Unknown Phase 2 family id(s): {unknown}")
    return [spec for spec in specs if spec.family_id in selected]


def build_family_plan(
    *,
    family_ids: list[str] | None = None,
    max_candidates_per_family: int | None = None,
    candidate_ids: list[str] | None = None,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    selected_candidates = set(candidate_ids or [])
    for spec in select_family_specs(family_ids):
        candidates = joint_fit.build_joint_candidates(
            base_candidate_ids=list(spec.base_candidate_ids),
            variant_ids=list(spec.variant_ids),
        )
        if selected_candidates:
            candidates = [
                candidate
                for candidate in candidates
                if candidate.candidate_id in selected_candidates
                or candidate.base_candidate_id in selected_candidates
            ]
        if max_candidates_per_family is not None:
            candidates = candidates[:max_candidates_per_family]
        for candidate in candidates:
            rows.append(
                {
                    "schema_id": SCHEMA_ID,
                    "family_id": spec.family_id,
                    "family_order": spec.family_order,
                    "family_description": spec.description,
                    "candidate_id": candidate.candidate_id,
                    "base_candidate_id": candidate.base_candidate_id,
                    "variant_signal_transfer_mode": candidate.signal_transfer_mode,
                    "variant_size_response_mode": candidate.size_response_mode,
                    "cfg_overrides_json": json.dumps(
                        candidate.cfg_overrides,
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                }
            )
    return pd.DataFrame(rows)


def _candidate_by_id(candidates: list[joint_fit.JointFitCandidate]) -> dict[str, joint_fit.JointFitCandidate]:
    return {candidate.candidate_id: candidate for candidate in candidates}


def _candidate_catalog_for_specs(specs: list[FamilySpec]) -> dict[str, joint_fit.JointFitCandidate]:
    out: dict[str, joint_fit.JointFitCandidate] = {}
    for spec in specs:
        for candidate in joint_fit.build_joint_candidates(
            base_candidate_ids=list(spec.base_candidate_ids),
            variant_ids=list(spec.variant_ids),
        ):
            out[candidate.candidate_id] = candidate
    return out


def summarize_best_candidates(summary: pd.DataFrame, *, expected_seed_count: int) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()
    group_cols = ["family_id", "candidate_id"]
    rows: list[dict[str, Any]] = []

    def median_or_nan(group: pd.DataFrame, column: str) -> float:
        if column not in group:
            return float("nan")
        values = pd.to_numeric(group[column], errors="coerce")
        return float(values.median()) if values.notna().any() else float("nan")

    for (family_id, candidate_id), group in summary.groupby(group_cols, dropna=False):
        guardrail_failures = int(
            (
                (pd.to_numeric(group["hard_guardrail_penalty"], errors="coerce") > 1e-12)
                | group["reference_bad"].astype(bool)
                | group["rho_bad"].astype(bool)
                | group["na_cutoff_active"].astype(bool)
            ).sum()
        )
        status_values = sorted(set(group["paper_fit_status"].astype(str)))
        seed_count = int(group["random_seed"].nunique())
        stable = (
            seed_count >= expected_seed_count
            and guardrail_failures == 0
            and len(status_values) == 1
        )
        rows.append(
            {
                "family_id": family_id,
                "candidate_id": candidate_id,
                "seed_count": seed_count,
                "joint_fit_score_median": float(group["joint_fit_score"].median()),
                "joint_fit_score_std": float(group["joint_fit_score"].std(ddof=0)),
                "joint_fit_score_formula_median": median_or_nan(
                    group,
                    "joint_fit_score_formula",
                ),
                "joint_fit_score_recomputed_mie_median": median_or_nan(
                    group,
                    "joint_fit_score_recomputed_mie",
                ),
                "selected_rate_score_median": float(group["selected_rate_score"].median()),
                "signal_ratio_score_median": float(group["signal_ratio_score"].median()),
                "signal_ratio_score_formula_median": median_or_nan(
                    group,
                    "signal_ratio_score_sqrt_scattering_column_ratio",
                ),
                "raw_signal_ratio_score_formula_median": median_or_nan(
                    group,
                    "raw_signal_ratio_score_sqrt_scattering_column_ratio",
                ),
                "signal_ratio_score_recomputed_mie_median": median_or_nan(
                    group,
                    "signal_ratio_score_recomputed_mie_sqrt_csca_ratio",
                ),
                "raw_signal_ratio_score_recomputed_mie_median": median_or_nan(
                    group,
                    "raw_signal_ratio_score_recomputed_mie_sqrt_csca_ratio",
                ),
                "size_exponent_score_median": float(group["size_exponent_score"].median()),
                "snr_ratio_score_median": float(group["snr_ratio_score"].median()),
                "guardrail_failure_count": guardrail_failures,
                "paper_fit_status_values": ",".join(status_values),
                "family_stability_status": (
                    "stable_family_candidate" if stable else "requires_review_or_negative"
                ),
            }
        )
    best = pd.DataFrame(rows).sort_values(
        ["family_id", "joint_fit_score_median", "candidate_id"],
        ignore_index=True,
    )
    return add_operator_variant_diagnostics(best)


def _d2_variant_suffix(candidate_id: str) -> str:
    return candidate_id.split("__", 1)[1] if "__" in candidate_id else "paper_10sigma"


def _d2_control_candidate_id(candidate_id: str) -> str:
    suffix = _d2_variant_suffix(candidate_id)
    return "tau_2ms_control" if suffix == "paper_10sigma" else f"tau_2ms_control__{suffix}"


def add_operator_variant_diagnostics(best: pd.DataFrame) -> pd.DataFrame:
    if best.empty or "family_id" not in best or "candidate_id" not in best:
        return best
    best = best.copy()
    best["operator_variant_delta_from_control"] = float("nan")
    best["operator_variant_diagnostic_status"] = "not_applicable"
    d2_mask = best["family_id"].astype(str).eq("D2_operator_phase_bfp_raw")
    d2 = best[d2_mask]
    if d2.empty:
        return best
    comparison_columns = [
        "joint_fit_score_median",
        "selected_rate_score_median",
        "signal_ratio_score_median",
        "signal_ratio_score_formula_median",
        "size_exponent_score_median",
        "snr_ratio_score_median",
    ]
    by_candidate = {str(row["candidate_id"]): row for _, row in d2.iterrows()}
    for index, row in d2.iterrows():
        candidate_id = str(row["candidate_id"])
        control_id = _d2_control_candidate_id(candidate_id)
        if candidate_id == control_id:
            best.at[index, "operator_variant_delta_from_control"] = 0.0
            best.at[index, "operator_variant_diagnostic_status"] = "operator_control_reference"
            continue
        control = by_candidate.get(control_id)
        if control is None:
            best.at[index, "operator_variant_diagnostic_status"] = "operator_control_missing"
            continue
        deltas: list[float] = []
        for column in comparison_columns:
            candidate_value = pd.to_numeric(pd.Series([row.get(column)]), errors="coerce").iloc[0]
            control_value = pd.to_numeric(pd.Series([control.get(column)]), errors="coerce").iloc[0]
            if pd.notna(candidate_value) and pd.notna(control_value):
                deltas.append(abs(float(candidate_value) - float(control_value)))
        max_delta = max(deltas) if deltas else float("nan")
        best.at[index, "operator_variant_delta_from_control"] = max_delta
        best.at[index, "operator_variant_diagnostic_status"] = (
            "operator_variant_numerically_inert_vs_control"
            if pd.notna(max_delta) and max_delta <= 1e-9
            else "operator_variant_changes_summary_vs_control"
            if pd.notna(max_delta)
            else "operator_variant_delta_unavailable"
        )
    return best


def guardrail_failures(summary: pd.DataFrame) -> pd.DataFrame:
    if summary.empty:
        return pd.DataFrame()
    mask = (
        (pd.to_numeric(summary["hard_guardrail_penalty"], errors="coerce") > 1e-12)
        | summary["reference_bad"].astype(bool)
        | summary["rho_bad"].astype(bool)
        | summary["na_cutoff_active"].astype(bool)
        | (pd.to_numeric(summary["transfer_gain_guardrail_penalty"], errors="coerce") > 1e-12)
        | (pd.to_numeric(summary["size_response_guardrail_penalty"], errors="coerce") > 1e-12)
    )
    columns = [
        "family_id",
        "candidate_id",
        "random_seed",
        "joint_fit_score",
        "hard_guardrail_penalty",
        "transfer_gain_guardrail_penalty",
        "size_response_guardrail_penalty",
        "reference_bad",
        "rho_bad",
        "na_cutoff_active",
        "paper_fit_status",
    ]
    columns = [column for column in columns if column in summary]
    return summary.loc[mask, columns].reset_index(drop=True)


def run_phase2_inverse(
    *,
    output_dir: Path,
    n_events: int,
    seeds: list[int],
    n_workers: int,
    scenario_id: str,
    family_ids: list[str] | None = None,
    max_candidates_per_family: int | None = None,
    candidate_ids: list[str] | None = None,
    dry_run: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    specs = select_family_specs(family_ids)
    plan = build_family_plan(
        family_ids=family_ids,
        max_candidates_per_family=max_candidates_per_family,
        candidate_ids=candidate_ids,
    )
    plan.to_csv(output_dir / PLAN_FILENAME, index=False)
    catalog = _candidate_catalog_for_specs(specs)
    raw_frames: list[pd.DataFrame] = []
    summary_rows: list[dict[str, Any]] = []
    start = time.time()
    if not dry_run:
        for _, plan_row in plan.iterrows():
            candidate = catalog[str(plan_row["candidate_id"])]
            for seed in seeds:
                print(
                    "[phase2-inverse] "
                    f"{plan_row['family_id']} {candidate.candidate_id} seed={seed}",
                    flush=True,
                )
                rows = joint_fit.run_joint_candidate_sweep(
                    candidate,
                    n_events=n_events,
                    random_seed=int(seed),
                    n_workers=n_workers,
                    scenario_id=scenario_id,
                )
                rows.insert(0, "phase2_family_id", plan_row["family_id"])
                rows.insert(1, "phase2_family_order", int(plan_row["family_order"]))
                raw_frames.append(rows)
                summary = joint_fit.summarize_joint_candidate(
                    rows,
                    candidate,
                    n_events=n_events,
                    random_seed=int(seed),
                    n_workers=n_workers,
                    scenario_id=scenario_id,
                )
                summary["family_id"] = plan_row["family_id"]
                summary["family_order"] = int(plan_row["family_order"])
                summary["family_description"] = plan_row["family_description"]
                summary_rows.append(summary)
    raw = pd.concat(raw_frames, ignore_index=True) if raw_frames else pd.DataFrame()
    summary = pd.DataFrame(summary_rows)
    if not summary.empty:
        summary = summary.sort_values(
            ["family_order", "joint_fit_score", "candidate_id", "random_seed"],
            ignore_index=True,
        )
    best = summarize_best_candidates(summary, expected_seed_count=len(seeds))
    failures = guardrail_failures(summary)
    raw.to_csv(output_dir / RAW_FILENAME, index=False)
    summary.to_csv(output_dir / SUMMARY_FILENAME, index=False)
    best.to_csv(output_dir / BEST_FILENAME, index=False)
    failures.to_csv(output_dir / GUARDRAIL_FILENAME, index=False)
    meta = {
        "schema_id": SCHEMA_ID,
        "generated_at_unix": time.time(),
        "n_events": int(n_events),
        "n_workers": int(n_workers),
        "seeds": [int(seed) for seed in seeds],
        "scenario_id": scenario_id,
        "family_ids": [spec.family_id for spec in specs],
        "candidate_ids": list(candidate_ids or []),
        "planned_candidate_rows": int(len(plan)),
        "dry_run": bool(dry_run),
        "raw_rows": int(len(raw)),
        "summary_rows": int(len(summary)),
        "best_rows": int(len(best)),
        "guardrail_failure_rows": int(len(failures)),
        "runtime_s": time.time() - start,
        "no_go_policy": (
            "candidate signing requires target audit, guardrails, multi-seed "
            "stability, shadow all-crossing sanity, and raw/calibrated residual "
            "separation"
        ),
    }
    rate_calib.write_json(output_dir / META_FILENAME, meta)
    write_report(output_dir, plan=plan, best=best, failures=failures, meta=meta)
    return summary, best, failures, meta


def write_report(
    output_dir: Path,
    *,
    plan: pd.DataFrame,
    best: pd.DataFrame,
    failures: pd.DataFrame,
    meta: dict[str, Any],
) -> Path:
    report_path = output_dir / REPORT_FILENAME
    best_view = best.head(20) if not best.empty else best
    lines = [
        "# Tsuyama Phase 2 Family-Ladder Parameter Inverse",
        "",
        "## Boundary",
        "",
        "- This is a bounded paper-audit inverse lane, not an EV full-grid rewrite.",
        "- Families are searched in ladder order to reduce parameter degeneracy.",
        "- Family E local transfer/size-response is a paper-fit lens and cannot mutate global defaults.",
        "- Dry runs write the family plan only and cannot sign candidates.",
        "",
        "## Metadata",
        "",
        f"- schema: `{meta['schema_id']}`",
        f"- n_events: `{meta['n_events']}`",
        f"- workers: `{meta['n_workers']}`",
        f"- seeds: `{meta['seeds']}`",
        f"- dry_run: `{meta['dry_run']}`",
        "",
        "## Family Plan",
        "",
        rate_calib.dataframe_to_markdown(plan),
        "",
        "## Best Candidate Summary",
        "",
        rate_calib.dataframe_to_markdown(best_view),
        "",
        "## Guardrail Failures",
        "",
        rate_calib.dataframe_to_markdown(failures.head(20)),
        "",
        "## Output Files",
        "",
        f"- `{PLAN_FILENAME}`",
        f"- `{RAW_FILENAME}`",
        f"- `{SUMMARY_FILENAME}`",
        f"- `{BEST_FILENAME}`",
        f"- `{GUARDRAIL_FILENAME}`",
        f"- `{META_FILENAME}`",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run bounded Phase 2 family-ladder inverse search."
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--n-events", type=int, default=10000)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--seeds", type=int, nargs="+", default=[42, 43, 44])
    parser.add_argument("--scenario-id", default="nodi_2022_10sigma_single")
    parser.add_argument("--families", nargs="+", default=None)
    parser.add_argument("--candidate-ids", nargs="+", default=None)
    parser.add_argument("--max-candidates-per-family", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    _, best, failures, meta = run_phase2_inverse(
        output_dir=args.output_dir,
        n_events=args.n_events,
        seeds=args.seeds,
        n_workers=args.workers,
        scenario_id=args.scenario_id,
        family_ids=args.families,
        max_candidates_per_family=args.max_candidates_per_family,
        candidate_ids=args.candidate_ids,
        dry_run=args.dry_run,
    )
    print(
        "Wrote Phase 2 parameter inverse outputs to "
        f"{args.output_dir} (dry_run={meta['dry_run']}, best_rows={len(best)}, "
        f"guardrail_failures={len(failures)})"
    )
    if not best.empty:
        print(rate_calib.dataframe_to_markdown(best.head(12)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
