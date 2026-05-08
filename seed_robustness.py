"""Seed-replicate robustness diagnostics for candidate design refinement."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import replace
from typing import Any

import numpy as np

from .data_objects import Channel, Medium, OpticalSystem, Particle, SimulationConfig
from .parameter_sweep import evaluate_engineering_gate, run_single_case_batch


SEED_ROBUSTNESS_DIAGNOSTIC_FIELDS = (
    "seed_score_mean",
    "seed_score_std",
    "seed_score_p10",
    "seed_rank_stability",
    "seed_gate_pass_fraction",
    "seed_replicate_count",
    "seed_values",
    "seed_scores",
    "seed_gate_passes",
    "seed_robustness_status",
    "seed_robustness_claim_level",
)

_SEED_GATE_PASS_FRACTION_FIELD = "seed_gate_pass_fraction"


def run_seed_replicates(
    case: Mapping[str, Any],
    seeds: Sequence[int] = (1, 2, 3, 4, 5),
    *,
    retain_event_traces: bool = False,
) -> dict[str, Any]:
    """Run seed replicates for one candidate case and summarize robustness."""
    particle = _require_case_item(case, "particle", Particle)
    medium = _require_case_item(case, "medium", Medium)
    channel = _require_case_item(case, "channel", Channel)
    optical = _require_case_item(case, "optical", OpticalSystem)
    sim_cfg = _require_case_item(case, "sim_cfg", SimulationConfig)
    E_sca_ref = float(case["E_sca_ref"])
    theta_grid_rad = np.asarray(case["theta_grid_rad"], dtype=float)
    if theta_grid_rad.ndim != 1 or theta_grid_rad.size == 0:
        raise ValueError("theta_grid_rad must be a non-empty 1-D array")

    replicates: list[dict[str, Any]] = []
    for seed in seeds:
        seed_int = int(seed)
        seed_cfg = replace(sim_cfg, random_seed=seed_int)
        batch = run_single_case_batch(
            particle,
            medium,
            channel,
            optical,
            seed_cfg,
            E_sca_ref,
            theta_grid_rad,
            retain_event_traces=retain_event_traces,
            stream_summary_only=not retain_event_traces,
        )
        summary = batch["summary"]
        gate = evaluate_engineering_gate(summary, seed_cfg)
        seed_score = compute_seed_detectability_score(summary, gate)
        replicates.append(
            {
                "seed": seed_int,
                "seed_score": seed_score,
                "engineering_gate_passed": bool(gate["engineering_gate_passed"]),
                "engineering_gate_reason": gate["engineering_gate_reason"],
                "mean_peak_margin_z": summary.get("mean_peak_margin_z"),
                "stable_detection_rate": summary.get("stable_detection_rate"),
                "phase_flip_fraction": summary.get("phase_flip_fraction"),
            }
        )
    return summarize_seed_replicate_metrics(replicates)


def compute_seed_detectability_score(
    summary: Mapping[str, Any],
    gate: Mapping[str, Any],
) -> float:
    """Compute a bounded per-seed diagnostic score from existing summary fields."""
    detection_lb = _clamp01(_float_or_zero(summary.get("detection_rate_wilson_lb")))
    stable_lb = _clamp01(
        _float_or_zero(summary.get("stable_detection_rate_wilson_lb"))
    )
    margin_z = max(_float_or_zero(summary.get("mean_peak_margin_z")), 0.0)
    margin_score = margin_z / (margin_z + 1.0) if margin_z > 0.0 else 0.0
    phase_flip_ub = _clamp01(
        _float_or_zero(summary.get("phase_flip_fraction_wilson_ub"))
    )
    base_score = _clamp01(
        0.30 * detection_lb
        + 0.35 * stable_lb
        + 0.30 * margin_score
        - 0.15 * phase_flip_ub
    )
    if bool(gate.get("engineering_gate_passed", False)):
        return base_score
    failed_count = max(int(gate.get("engineering_gate_failed_count", 1) or 1), 1)
    return float(base_score / (1.0 + failed_count))


def summarize_seed_replicate_metrics(
    replicates: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Summarize already-computed seed replicate records."""
    if not replicates:
        return {
            "seed_score_mean": None,
            "seed_score_std": None,
            "seed_score_p10": None,
            "seed_rank_stability": None,
            "seed_replicate_count": 0,
            "seed_values": [],
            "seed_scores": [],
            "seed_gate_passes": [],
            "seed_robustness_status": "not_run_no_seed_replicates",
            "seed_robustness_claim_level": "not_evaluated",
        } | {_SEED_GATE_PASS_FRACTION_FIELD: None}

    scores = np.asarray(
        [_clamp01(_float_or_zero(item.get("seed_score"))) for item in replicates],
        dtype=float,
    )
    gate_passes = [bool(item.get("engineering_gate_passed", False)) for item in replicates]
    mean_score = float(np.mean(scores))
    std_score = float(np.std(scores))
    rank_stability = _clamp01(1.0 - std_score / max(abs(mean_score), 1e-12))
    gate_pass_fraction = float(np.mean(gate_passes)) if gate_passes else 0.0
    return {
        "seed_score_mean": mean_score,
        "seed_score_std": std_score,
        "seed_score_p10": float(np.percentile(scores, 10)),
        "seed_rank_stability": rank_stability,
        "seed_gate_pass_fraction": gate_pass_fraction,
        "seed_replicate_count": len(replicates),
        "seed_values": [int(item.get("seed", idx)) for idx, item in enumerate(replicates)],
        "seed_scores": [float(score) for score in scores],
        "seed_gate_passes": gate_passes,
        "seed_robustness_status": "candidate_seed_replicates_evaluated",
        "seed_robustness_claim_level": (
            "candidate_refinement_diagnostic_not_full_grid_default"
        ),
    }


def _require_case_item(
    case: Mapping[str, Any],
    key: str,
    expected_type: type,
) -> Any:
    value = case.get(key)
    if not isinstance(value, expected_type):
        raise TypeError(f"case['{key}'] must be {expected_type.__name__}")
    return value


def _float_or_zero(value: Any) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0
    return parsed if np.isfinite(parsed) else 0.0


def _clamp01(value: float) -> float:
    return float(min(1.0, max(0.0, value)))
