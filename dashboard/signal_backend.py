"""
dashboard/signal_backend.py — Signal-chain helpers for explanatory dashboard pages

Provides focused backend summaries for:
    - Interference Explorer: intrinsic scattering -> reference field -> clean signal
    - Noise & Detection Explorer: clean trace -> noisy trace -> threshold -> detection
"""

from __future__ import annotations

from copy import deepcopy

import numpy as np
import pandas as pd

from nodi_simulator import (
    BASELINE_CHANNEL,
    Channel,
    build_case_decision_summary,
    classify_design_recommendation,
    classify_engineering_gate_explanation,
    classify_delta_phi_gouy_geometry_validity,
    classify_interference_overlap_freeze,
    classify_observation_freeze,
    classify_projection_freeze,
    compute_baseline_normalization,
    compute_baseline_normalization_per_wavelength,
    compute_detected_scattering_field,
    build_interference_overlap_diagnostics,
    compute_illumination_envelope,
    compute_intrinsic_scattering,
    compute_reference_field,
    compute_reference_field_trace,
    compute_scattering_field_trace,
    generate_interferometric_trace,
    interpolate_at_theta,
    resolve_collection_theta_rad,
    run_single_case_batch,
    simulate_particle_trajectory,
    validate_simulation_config,
    resolve_projection_basis,
)
from nodi_simulator.dashboard.config import (
    BASELINE_PARTICLE,
    DEFAULT_SIM_CFG,
    MEDIUM,
    OPTICAL_TEMPLATE,
    THETA_GRID_RAD,
    make_particle,
    medium_for_material,
)


REFERENCE_CONSISTENCY_THRESHOLD_DEFAULTS = {
    "min_rank_corr": 0.85,
    "max_mean_abs_A_ref_rel_error": 0.25,
    "max_mean_abs_phi_ref_delta_rad": 0.75,
}

INTERFERENCE_OVERLAP_THRESHOLD_DEFAULTS = {
    "aligned_max_abs_factor_deviation": 0.15,
    "aligned_max_abs_phase_rad": 0.15,
    "aligned_max_peak_rel_error": 0.15,
    "caution_max_abs_factor_deviation": 0.75,
    "caution_max_abs_phase_rad": 0.50,
    "caution_max_peak_rel_error": 0.75,
}

PATH_OPD_FREEZE_THRESHOLD_DEFAULTS = {
    "aligned_max_peak_clean_rel_delta": 0.20,
    "aligned_max_peak_delta_phi_ref_delta_rad": 0.35,
    "aligned_max_peak_phi_sca_path_z_delta_rad": 0.75,
    "caution_max_peak_clean_rel_delta": 0.75,
    "caution_max_peak_delta_phi_ref_delta_rad": 1.00,
    "caution_max_peak_phi_sca_path_z_delta_rad": 2.50,
}

DELTA_PHI_GOUY_FREEZE_THRESHOLD_DEFAULTS = {
    "aligned_max_peak_delta_phi_gouy_delta_rad": 0.05,
    "aligned_max_peak_phi_gouy_ref_delta_rad": 0.05,
    "aligned_max_peak_phi_gouy_sca_delta_rad": 0.05,
    "caution_max_peak_delta_phi_gouy_delta_rad": 0.20,
    "caution_max_peak_phi_gouy_ref_delta_rad": 0.20,
    "caution_max_peak_phi_gouy_sca_delta_rad": 0.20,
}

RHO_SENSITIVITY_THRESHOLD_DEFAULTS = {
    "robust_max_abs_detection_rate_delta": 0.10,
    "robust_max_abs_stable_detection_rate_delta": 0.10,
    "robust_max_abs_peak_clean_rel_delta": 0.35,
    "caution_max_abs_detection_rate_delta": 0.30,
    "caution_max_abs_stable_detection_rate_delta": 0.25,
    "caution_max_abs_peak_clean_rel_delta": 1.00,
}
FREEZE_LABELS = {
    "default_ready_for_result_freeze": "结果冻结已就绪",
    "caution_probe_before_result_freeze": "结果冻结需谨慎复核",
    "review_required_before_result_freeze": "结果冻结需先复核",
    "legacy_phase_path_not_freezable": "当前观测链不适合结果冻结",
}


def _resolve_projection_basis(mode: str) -> str:
    """Collapse a projection mode into the audit basis vocabulary."""
    return resolve_projection_basis(str(mode))


def _wrapped_phase_delta_rad(a_rad: float, b_rad: float) -> float:
    """Return the wrapped phase difference a-b in [-pi, pi]."""
    return float(np.angle(np.exp(1j * (float(a_rad) - float(b_rad)))))


def _resolve_report_sim_cfg(sim_cfg, *, n_events: int | None = None) -> tuple[object, str]:
    """
    Build a deterministic per-report config without changing the global defaults.

    The single-case dashboard reports are explanatory comparisons. When the UI
    does not pin `random_seed`, force a stable fallback seed so current-vs-probe
    differences come from the scanned physics parameter rather than from a fresh
    RNG draw on every helper call.
    """
    cfg = deepcopy(sim_cfg or DEFAULT_SIM_CFG)
    if n_events is not None:
        cfg.n_events = int(n_events)
    if cfg.random_seed is None:
        cfg.random_seed = 0
        return cfg, "report_default_seed_0"
    return cfg, "sim_cfg_random_seed"


def _stage_reading(*, key: str, judgment: str, caution: str) -> dict[str, str]:
    return {
        "key": key,
        "judgment": judgment,
        "caution": caution,
    }


def _ensure_decision_fields(
    noise_summary: dict[str, object],
    *,
    gate_passed: bool,
    gate_reason: str,
    gate_failed_count: int,
    observation_freeze_status: str,
) -> None:
    gate_keys = (
        "engineering_gate_status_label",
        "engineering_gate_primary_blocker",
        "engineering_gate_primary_blocker_label",
        "engineering_gate_blocker_summary",
        "engineering_gate_guidance",
    )
    if any(noise_summary.get(key) is None for key in gate_keys):
        noise_summary.update(
            classify_engineering_gate_explanation(
                engineering_gate_passed=gate_passed,
                engineering_gate_reason=gate_reason,
                engineering_gate_failed_count=gate_failed_count,
            )
        )

    recommendation_keys = (
        "design_recommendation_status",
        "design_recommendation_label",
        "design_recommendation_rank",
        "design_recommendation_guidance",
    )
    if any(noise_summary.get(key) is None for key in recommendation_keys):
        noise_summary.update(
            classify_design_recommendation(
                engineering_gate_passed=gate_passed,
                observation_freeze_status=observation_freeze_status,
            )
        )


def _resolve_human_headline(recommendation_status: str) -> str:
    if recommendation_status == "recommended_default":
        return "当前案例可作为默认推荐候选"
    if recommendation_status == "recommended_with_caution":
        return "当前案例可作为候选，但建议先复核"
    if recommendation_status == "physics_ready_gate_blocked":
        return "当前案例物理链已就绪，但工程门槛未过"
    if recommendation_status == "not_recommended_freeze_blocked":
        return "当前案例暂不建议作为默认候选"
    return "当前案例更适合作为观察或对照对象"


def _classify_rho_sensitivity(summary: dict[str, object]) -> dict[str, object]:
    """Convert rho-envelope probe deltas into an audit-friendly stability label."""
    det_delta = summary.get("rho_sensitivity_max_abs_detection_rate_delta_vs_anchor")
    stable_delta = summary.get("rho_sensitivity_max_abs_stable_detection_rate_delta_vs_anchor")
    peak_delta = summary.get("rho_sensitivity_max_abs_peak_clean_rel_delta_vs_anchor")
    requested_status = str(summary.get("rho_requested_envelope_status", "unavailable"))
    gate_change_count = int(summary.get("rho_sensitivity_gate_change_count", 0))
    recommendation_change_count = int(
        summary.get("rho_sensitivity_recommendation_change_count", 0)
    )

    if any(
        value is None or not np.isfinite(float(value))
        for value in (det_delta, stable_delta, peak_delta)
    ):
        return {
            "rho_sensitivity_status": "unavailable",
            "rho_sensitivity_label": "包络不可用",
            "rho_sensitivity_guidance": (
                "当前 case 没有足够的 rho 包络诊断，先不要把绝对 detection rate "
                "当成已定标结论。"
            ),
        }

    det_delta = float(det_delta)
    stable_delta = float(stable_delta)
    peak_delta = float(peak_delta)

    robust = (
        det_delta <= RHO_SENSITIVITY_THRESHOLD_DEFAULTS["robust_max_abs_detection_rate_delta"]
        and stable_delta
        <= RHO_SENSITIVITY_THRESHOLD_DEFAULTS[
            "robust_max_abs_stable_detection_rate_delta"
        ]
        and peak_delta
        <= RHO_SENSITIVITY_THRESHOLD_DEFAULTS["robust_max_abs_peak_clean_rel_delta"]
        and gate_change_count == 0
        and recommendation_change_count == 0
    )
    caution = (
        det_delta <= RHO_SENSITIVITY_THRESHOLD_DEFAULTS["caution_max_abs_detection_rate_delta"]
        and stable_delta
        <= RHO_SENSITIVITY_THRESHOLD_DEFAULTS[
            "caution_max_abs_stable_detection_rate_delta"
        ]
        and peak_delta
        <= RHO_SENSITIVITY_THRESHOLD_DEFAULTS["caution_max_abs_peak_clean_rel_delta"]
    )

    if requested_status != "within_envelope":
        if robust:
            return {
                "rho_sensitivity_status": "out_of_envelope_but_locally_robust",
                "rho_sensitivity_label": "包络外但局部稳",
                "rho_sensitivity_guidance": (
                    "当前 rho 已落在 reference-side 建议区间外，但 lower / nominal / "
                    "upper probe 还没有引起明显结论翻转；绝对量仍要保守解释。"
                ),
            }
        return {
            "rho_sensitivity_status": "out_of_envelope_and_sensitive",
            "rho_sensitivity_label": "包络外且敏感",
            "rho_sensitivity_guidance": (
                "当前 rho 不仅落在 reference-side 建议区间外，而且 probe 后检测率 / "
                "clean peak / gate 结论已经明显变化；绝对预测不宜直接采信。"
            ),
        }

    if robust:
        return {
            "rho_sensitivity_status": "within_envelope_and_robust",
            "rho_sensitivity_label": "包络内且稳",
            "rho_sensitivity_guidance": (
                "当前 rho 位于建议区间内，且 lower / nominal / upper probe 没有导致明显结论翻转，"
                "说明这条 case 的 absolute readout 对 rho 不是过度脆弱。"
            ),
        }
    if caution:
        return {
            "rho_sensitivity_status": "within_envelope_but_sensitive",
            "rho_sensitivity_label": "包络内但敏感",
            "rho_sensitivity_guidance": (
                "当前 rho 仍在建议区间内，但 probe 后 detection / clean peak 已出现可见漂移；"
                "后面报告绝对量时仍应把 rho 当作主要不确定源。"
            ),
        }
    return {
        "rho_sensitivity_status": "high_sensitivity",
        "rho_sensitivity_label": "对 rho 高敏感",
        "rho_sensitivity_guidance": (
            "即使在建议区间内，rho 的 probe 也已经足以改变这一 case 的工程读法；"
            "后续更适合先做 blank-channel 标定，再讨论绝对 detection rate。"
        ),
    }


def _rank_correlation(values_a: np.ndarray, values_b: np.ndarray) -> float:
    """Compute a simple rank correlation without requiring scipy."""
    a = np.asarray(values_a, dtype=float)
    b = np.asarray(values_b, dtype=float)
    finite = np.isfinite(a) & np.isfinite(b)
    if np.count_nonzero(finite) < 2:
        return float("nan")
    a_f = a[finite]
    b_f = b[finite]
    if np.allclose(a_f, a_f[0]) or np.allclose(b_f, b_f[0]):
        return float("nan")
    a_rank = pd.Series(a_f).rank(method="average").to_numpy(dtype=float)
    b_rank = pd.Series(b_f).rank(method="average").to_numpy(dtype=float)
    return float(np.corrcoef(a_rank, b_rank)[0, 1])


def _classify_reference_consistency(summary: dict[str, float | int]) -> dict[str, object]:
    """
    Convert overlap-region consistency metrics into an explicit freeze recommendation.

    Freeze rule:
        - whenever a calibration table exists, calibrated_lookup remains the primary path
        - surrogate may remain the default no-table fallback only if the overlap-region
          trend agreement and mean errors stay within the configured thresholds
    """
    min_rank_corr = float(REFERENCE_CONSISTENCY_THRESHOLD_DEFAULTS["min_rank_corr"])
    max_rel_error = float(
        REFERENCE_CONSISTENCY_THRESHOLD_DEFAULTS["max_mean_abs_A_ref_rel_error"]
    )
    max_phi_error = float(
        REFERENCE_CONSISTENCY_THRESHOLD_DEFAULTS["max_mean_abs_phi_ref_delta_rad"]
    )

    n_points = int(summary.get("n_non_extrapolated_points", 0))
    rank_corr = float(summary.get("A_ref_rank_corr", np.nan))
    mean_rel_error = float(summary.get("mean_abs_A_ref_rel_error", np.nan))
    mean_phi_error = float(summary.get("mean_abs_phi_ref_delta_rad", np.nan))

    enough_points = n_points >= 3
    rank_ok = np.isfinite(rank_corr) and rank_corr >= min_rank_corr
    rel_ok = np.isfinite(mean_rel_error) and mean_rel_error <= max_rel_error
    phi_ok = np.isfinite(mean_phi_error) and mean_phi_error <= max_phi_error
    surrogate_fallback_accepted = bool(enough_points and rank_ok and rel_ok and phi_ok)

    if surrogate_fallback_accepted:
        agreement_status = "aligned"
        surrogate_role = "accepted_fallback"
        guidance = (
            "calibrated_lookup 保持主路径；channel_angular_surrogate 可继续作为"
            " 无标定时的默认 fallback。"
        )
    elif enough_points and rank_ok:
        agreement_status = "caution"
        surrogate_role = "caution_fallback"
        guidance = (
            "趋势排序大体仍一致，但幅值或相位偏差偏大；应优先信任 calibrated_lookup，"
            " surrogate 只适合作为定性 fallback。"
        )
    else:
        agreement_status = "mismatch"
        surrogate_role = "rejected_fallback"
        guidance = (
            "重叠区排序或误差已经脱钩；这段参数区间不应再把 surrogate 当成可靠 fallback，"
            " 应明确优先使用 calibrated_lookup。"
        )

    return {
        "reference_consistency_threshold_min_rank_corr": min_rank_corr,
        "reference_consistency_threshold_max_mean_abs_A_ref_rel_error": max_rel_error,
        "reference_consistency_threshold_max_mean_abs_phi_ref_delta_rad": max_phi_error,
        "reference_consistency_enough_points": enough_points,
        "reference_consistency_rank_ok": rank_ok,
        "reference_consistency_rel_error_ok": rel_ok,
        "reference_consistency_phi_error_ok": phi_ok,
        "reference_consistency_agreement_status": agreement_status,
        "reference_consistency_surrogate_role": surrogate_role,
        "reference_consistency_surrogate_fallback_accepted": surrogate_fallback_accepted,
        "reference_consistency_primary_model": "calibrated_lookup",
        "reference_consistency_default_freeze_rule": (
            "prefer_calibrated_lookup_when_available__allow_surrogate_only_if_overlap_metrics_pass"
        ),
        "reference_consistency_guidance": guidance,
    }


def _classify_interference_overlap(
    *,
    overlap_factor_abs: float,
    overlap_factor_phase_rad: float,
    peak_cross_term_collapsed: float,
    peak_cross_term_joint: float,
    joint_available: bool,
    default_model: str,
) -> dict[str, object]:
    """Convert overlap diagnostics into an explicit freeze recommendation."""
    return classify_interference_overlap_freeze(
        overlap_factor_abs=overlap_factor_abs,
        overlap_factor_phase_rad=overlap_factor_phase_rad,
        collapsed_cross_term_scalar=peak_cross_term_collapsed,
        joint_cross_term_scalar=peak_cross_term_joint,
        joint_available=joint_available,
        default_model=default_model,
        aligned_max_abs_factor_deviation=float(
            INTERFERENCE_OVERLAP_THRESHOLD_DEFAULTS["aligned_max_abs_factor_deviation"]
        ),
        aligned_max_abs_phase_rad=float(
            INTERFERENCE_OVERLAP_THRESHOLD_DEFAULTS["aligned_max_abs_phase_rad"]
        ),
        aligned_max_peak_rel_error=float(
            INTERFERENCE_OVERLAP_THRESHOLD_DEFAULTS["aligned_max_peak_rel_error"]
        ),
        caution_max_abs_factor_deviation=float(
            INTERFERENCE_OVERLAP_THRESHOLD_DEFAULTS["caution_max_abs_factor_deviation"]
        ),
        caution_max_abs_phase_rad=float(
            INTERFERENCE_OVERLAP_THRESHOLD_DEFAULTS["caution_max_abs_phase_rad"]
        ),
        caution_max_peak_rel_error=float(
            INTERFERENCE_OVERLAP_THRESHOLD_DEFAULTS["caution_max_peak_rel_error"]
        ),
    )


def _classify_path_opd_and_gouy_freeze(
    summary: dict[str, float | int],
    *,
    gouy_geometry: dict[str, object] | None = None,
) -> dict[str, object]:
    """Convert path-OPD and differential-Gouy comparison metrics into freeze guidance."""
    path_aligned_clean = float(
        PATH_OPD_FREEZE_THRESHOLD_DEFAULTS["aligned_max_peak_clean_rel_delta"]
    )
    path_aligned_phi_ref = float(
        PATH_OPD_FREEZE_THRESHOLD_DEFAULTS["aligned_max_peak_delta_phi_ref_delta_rad"]
    )
    path_aligned_path_z = float(
        PATH_OPD_FREEZE_THRESHOLD_DEFAULTS["aligned_max_peak_phi_sca_path_z_delta_rad"]
    )
    path_caution_clean = float(
        PATH_OPD_FREEZE_THRESHOLD_DEFAULTS["caution_max_peak_clean_rel_delta"]
    )
    path_caution_phi_ref = float(
        PATH_OPD_FREEZE_THRESHOLD_DEFAULTS["caution_max_peak_delta_phi_ref_delta_rad"]
    )
    path_caution_path_z = float(
        PATH_OPD_FREEZE_THRESHOLD_DEFAULTS["caution_max_peak_phi_sca_path_z_delta_rad"]
    )

    gouy_aligned_delta = float(
        DELTA_PHI_GOUY_FREEZE_THRESHOLD_DEFAULTS["aligned_max_peak_delta_phi_gouy_delta_rad"]
    )
    gouy_aligned_ref = float(
        DELTA_PHI_GOUY_FREEZE_THRESHOLD_DEFAULTS["aligned_max_peak_phi_gouy_ref_delta_rad"]
    )
    gouy_aligned_sca = float(
        DELTA_PHI_GOUY_FREEZE_THRESHOLD_DEFAULTS["aligned_max_peak_phi_gouy_sca_delta_rad"]
    )
    gouy_caution_delta = float(
        DELTA_PHI_GOUY_FREEZE_THRESHOLD_DEFAULTS["caution_max_peak_delta_phi_gouy_delta_rad"]
    )
    gouy_caution_ref = float(
        DELTA_PHI_GOUY_FREEZE_THRESHOLD_DEFAULTS["caution_max_peak_phi_gouy_ref_delta_rad"]
    )
    gouy_caution_sca = float(
        DELTA_PHI_GOUY_FREEZE_THRESHOLD_DEFAULTS["caution_max_peak_phi_gouy_sca_delta_rad"]
    )

    max_peak_clean_rel_delta = float(summary.get("path_opd_freeze_max_peak_clean_rel_delta", np.nan))
    max_peak_delta_phi_ref_delta = float(
        summary.get("path_opd_freeze_max_peak_delta_phi_ref_delta_rad", np.nan)
    )
    max_peak_phi_sca_path_z_delta = float(
        summary.get("path_opd_freeze_max_peak_phi_sca_path_z_delta_rad", np.nan)
    )
    n_path_alternatives = int(summary.get("path_opd_freeze_n_alternative_models", 0))
    path_available = n_path_alternatives > 0

    path_aligned = bool(
        path_available
        and max_peak_clean_rel_delta <= path_aligned_clean
        and max_peak_delta_phi_ref_delta <= path_aligned_phi_ref
        and max_peak_phi_sca_path_z_delta <= path_aligned_path_z
    )
    path_caution = bool(
        path_available
        and not path_aligned
        and max_peak_clean_rel_delta <= path_caution_clean
        and max_peak_delta_phi_ref_delta <= path_caution_phi_ref
        and max_peak_phi_sca_path_z_delta <= path_caution_path_z
    )

    if not path_available:
        path_status = "unavailable"
        path_default_frozen = False
        path_freeze_status = "freeze_unavailable"
        path_guidance = "当前缺少 OPD 对照路径，暂时无法对 single_pass 主线做 freeze judgement。"
    elif path_aligned:
        path_status = "aligned"
        path_default_frozen = True
        path_freeze_status = "default_frozen_active"
        path_guidance = (
            "single_pass 与两条 OPD 诊断路径差异有限；当前可继续接受 single_pass 作为默认主线，"
            " roundtrip / wall-referenced 保留为诊断对照。"
        )
    elif path_caution:
        path_status = "caution"
        path_default_frozen = False
        path_freeze_status = "warning_review_before_freeze"
        path_guidance = (
            "single_pass 与对照 OPD 口径已经出现可见偏差；当前仍可保留工作主线，"
            " 但冻结结果库前应复核 wall-referenced 和 roundtrip 对 clean signal 与 Δφ_ref 的影响。"
        )
    else:
        path_status = "mismatch"
        path_default_frozen = False
        path_freeze_status = "review_required_before_freeze"
        path_guidance = (
            "single_pass 与备选 OPD 口径显著脱钩；当前不应直接把 OPD 默认语义视为最终冻结，"
            " 需要先完成更明确的几何判断。"
        )

    max_peak_delta_phi_gouy_delta = float(
        summary.get("delta_phi_gouy_freeze_max_peak_delta_phi_gouy_delta_rad", np.nan)
    )
    max_peak_phi_gouy_ref_delta = float(
        summary.get("delta_phi_gouy_freeze_max_peak_phi_gouy_ref_delta_rad", np.nan)
    )
    max_peak_phi_gouy_sca_delta = float(
        summary.get("delta_phi_gouy_freeze_max_peak_phi_gouy_sca_delta_rad", np.nan)
    )
    gouy_available = n_path_alternatives > 0
    gouy_aligned = bool(
        gouy_available
        and max_peak_delta_phi_gouy_delta <= gouy_aligned_delta
        and max_peak_phi_gouy_ref_delta <= gouy_aligned_ref
        and max_peak_phi_gouy_sca_delta <= gouy_aligned_sca
    )
    gouy_caution = bool(
        gouy_available
        and not gouy_aligned
        and max_peak_delta_phi_gouy_delta <= gouy_caution_delta
        and max_peak_phi_gouy_ref_delta <= gouy_caution_ref
        and max_peak_phi_gouy_sca_delta <= gouy_caution_sca
    )

    if not gouy_available:
        gouy_status = "unavailable"
        gouy_default_frozen = False
        gouy_freeze_status = "freeze_unavailable"
        gouy_guidance = "当前缺少 OPD 对照路径，暂时无法对 delta_phi_gouy 主线做 freeze judgement。"
    elif gouy_aligned:
        gouy_status = "aligned"
        gouy_default_frozen = True
        gouy_freeze_status = "default_frozen_active"
        gouy_guidance = (
            "shared-beam + focus-crossing 的 delta_phi_gouy 语义在各 OPD 对照路径下保持稳定，"
            " 当前可以继续作为默认审计主线。"
        )
    elif gouy_caution:
        gouy_status = "caution"
        gouy_default_frozen = False
        gouy_freeze_status = "warning_review_before_freeze"
        gouy_guidance = (
            "delta_phi_gouy 对 OPD 参考面选择已有轻度敏感性；冻结前应复核 reference-side Gouy 几何修正。"
        )
    else:
        gouy_status = "mismatch"
        gouy_default_frozen = False
        gouy_freeze_status = "review_required_before_freeze"
        gouy_guidance = (
            "delta_phi_gouy 在不同 OPD 参考面下已明显变化；当前不应把 shared-beam Gouy 语义视为已冻结默认。"
        )

    gouy_geometry = dict(gouy_geometry or {})
    gouy_validity = str(gouy_geometry.get("delta_phi_gouy_validity", "unavailable"))
    if gouy_validity == "shared_beam_caution" and gouy_freeze_status == "default_frozen_active":
        gouy_status = "caution"
        gouy_default_frozen = False
        gouy_freeze_status = "warning_review_before_freeze"
        gouy_guidance = (
            "数值上 delta_phi_gouy 在 OPD 对照路径间仍较稳定，但通道尺度与 beam waist 仍属同量级；"
            " 当前 shared-beam Gouy 语义保留为 caution。"
        )
    elif gouy_validity == "not_applicable_legacy_phase_model" and gouy_freeze_status != "freeze_unavailable":
        gouy_default_frozen = False
        gouy_freeze_status = "legacy_phase_model_not_freezable"
        gouy_guidance = (
            "当前主相位链不是 relative_surrogate；delta_phi_gouy 只保留为兼容审计量，"
            " 不应进入冻结默认。"
        )

    return {
        "path_opd_freeze_threshold_aligned_max_peak_clean_rel_delta": path_aligned_clean,
        "path_opd_freeze_threshold_aligned_max_peak_delta_phi_ref_delta_rad": path_aligned_phi_ref,
        "path_opd_freeze_threshold_aligned_max_peak_phi_sca_path_z_delta_rad": path_aligned_path_z,
        "path_opd_freeze_threshold_caution_max_peak_clean_rel_delta": path_caution_clean,
        "path_opd_freeze_threshold_caution_max_peak_delta_phi_ref_delta_rad": path_caution_phi_ref,
        "path_opd_freeze_threshold_caution_max_peak_phi_sca_path_z_delta_rad": path_caution_path_z,
        "path_opd_freeze_agreement_status": path_status,
        "path_opd_freeze_default_model": "single_pass",
        "path_opd_freeze_default_role": "default_frozen_mainline",
        "path_opd_freeze_default_frozen": path_default_frozen,
        "path_opd_freeze_default_freeze_status": path_freeze_status,
        "path_opd_freeze_guidance": path_guidance,
        "delta_phi_gouy_freeze_threshold_aligned_max_peak_delta_phi_gouy_delta_rad": gouy_aligned_delta,
        "delta_phi_gouy_freeze_threshold_aligned_max_peak_phi_gouy_ref_delta_rad": gouy_aligned_ref,
        "delta_phi_gouy_freeze_threshold_aligned_max_peak_phi_gouy_sca_delta_rad": gouy_aligned_sca,
        "delta_phi_gouy_freeze_threshold_caution_max_peak_delta_phi_gouy_delta_rad": gouy_caution_delta,
        "delta_phi_gouy_freeze_threshold_caution_max_peak_phi_gouy_ref_delta_rad": gouy_caution_ref,
        "delta_phi_gouy_freeze_threshold_caution_max_peak_phi_gouy_sca_delta_rad": gouy_caution_sca,
        "delta_phi_gouy_freeze_agreement_status": gouy_status,
        "delta_phi_gouy_default_model": "illumination_beam_focus_crossing_surrogate",
        "delta_phi_gouy_default_role": "default_frozen_mainline",
        "delta_phi_gouy_default_frozen": gouy_default_frozen,
        "delta_phi_gouy_default_freeze_status": gouy_freeze_status,
        "delta_phi_gouy_guidance": gouy_guidance,
        **gouy_geometry,
    }


def _summarize_reference_consistency_subset(df: pd.DataFrame) -> dict[str, object]:
    """Summarize one overlap-region subset and attach the freeze classification."""
    valid_df = df.loc[~df["calibration_extrapolated"].to_numpy(dtype=bool)].copy()
    summary: dict[str, object] = {
        "n_points": int(len(df)),
        "n_non_extrapolated_points": int(len(valid_df)),
        "mean_abs_A_ref_rel_error": float(np.nanmean(np.abs(valid_df["A_ref_rel_error"])))
        if not valid_df.empty
        else float("nan"),
        "max_abs_A_ref_rel_error": float(np.nanmax(np.abs(valid_df["A_ref_rel_error"])))
        if not valid_df.empty
        else float("nan"),
        "mean_abs_phi_ref_delta_rad": float(
            np.nanmean(np.abs(valid_df["phi_ref_delta_wrapped_rad"]))
        )
        if not valid_df.empty
        else float("nan"),
        "max_abs_phi_ref_delta_rad": float(
            np.nanmax(np.abs(valid_df["phi_ref_delta_wrapped_rad"]))
        )
        if not valid_df.empty
        else float("nan"),
        "A_ref_rank_corr": _rank_correlation(
            valid_df["A_ref_surrogate"].to_numpy(dtype=float),
            valid_df["A_ref_calibrated"].to_numpy(dtype=float),
        )
        if not valid_df.empty
        else float("nan"),
        "g_ref_rank_corr": _rank_correlation(
            valid_df["g_ref_surrogate"].to_numpy(dtype=float),
            valid_df["g_ref_calibrated"].to_numpy(dtype=float),
        )
        if not valid_df.empty
        else float("nan"),
    }
    summary.update(_classify_reference_consistency(summary))
    return summary


def _projection_mode_semantics(mode: str) -> dict[str, object]:
    """Classify projection modes by intended physics role."""
    if mode == "parallel":
        return {
            "projection_mode_role": "primary_phase_aware",
            "phase_aware": True,
            "material_phase_source": "arg(S2/k_m)",
        }
    if mode == "perpendicular":
        return {
            "projection_mode_role": "secondary_phase_aware",
            "phase_aware": True,
            "material_phase_source": "arg(S1/k_m)",
        }
    if mode == "intensity_proxy":
        return {
            "projection_mode_role": "legacy_compatibility",
            "phase_aware": False,
            "material_phase_source": "disabled",
        }
    raise ValueError(f"Unsupported scattering_projection_mode: {mode}")


def _dominant_clean_peak_summary(trace_df: pd.DataFrame) -> dict[str, object]:
    """Extract the dominant clean-signal extremum using absolute amplitude."""
    clean = np.asarray(trace_df["clean_signal"], dtype=float)
    idx = int(np.argmax(np.abs(clean)))
    signed = float(clean[idx])
    abs_value = float(abs(signed))
    if signed > 0:
        polarity = "positive"
    elif signed < 0:
        polarity = "negative"
    else:
        polarity = "zero"
    return {
        "dominant_peak_idx": idx,
        "dominant_peak_clean_signal": signed,
        "dominant_peak_abs_clean_signal": abs_value,
        "dominant_peak_polarity": polarity,
    }


def _resolve_esca_reference(sim_cfg, optical, medium) -> float:
    """Resolve the scattering normalization anchor used by the main simulator."""
    if sim_cfg.normalization_mode == "per_wavelength":
        ref_map = compute_baseline_normalization_per_wavelength(
            BASELINE_PARTICLE,
            medium,
            OPTICAL_TEMPLATE,
            np.array([optical.wavelength_m]),
            THETA_GRID_RAD,
            channel=BASELINE_CHANNEL,
            sim_cfg=sim_cfg,
        )
        return float(ref_map[float(optical.wavelength_m)])

    baseline = compute_baseline_normalization(
        BASELINE_PARTICLE,
        medium,
        optical,
        THETA_GRID_RAD,
        channel=BASELINE_CHANNEL,
        sim_cfg=sim_cfg,
    )
    return float(baseline["E_sca_ref"])


def build_case_inputs(
    *,
    material: str,
    diameter_nm: int | float,
    wavelength_nm: int | float,
    width_nm: int | float,
    depth_nm: int | float,
    sim_cfg=None,
    optical_template=None,
) -> dict[str, object]:
    """Build the core particle / channel / optical objects for one dashboard case."""
    particle = make_particle(material, diameter_nm)
    case_medium = medium_for_material(material)
    channel = Channel(width_m=float(width_nm) * 1e-9, depth_m=float(depth_nm) * 1e-9)

    optical = deepcopy(optical_template or OPTICAL_TEMPLATE)
    optical.wavelength_m = float(wavelength_nm) * 1e-9

    sim_cfg_case = deepcopy(sim_cfg or DEFAULT_SIM_CFG)
    validate_simulation_config(sim_cfg_case, optical)

    intrinsic = compute_intrinsic_scattering(
        particle,
        case_medium,
        optical.wavelength_m,
        THETA_GRID_RAD,
    )
    collection = compute_detected_scattering_field(
        intrinsic, channel, optical, sim_cfg_case
    )
    theta_det = float(collection["theta_effective_rad"])
    e_sca_at_det = float(collection["E_sca_detected_abs"])
    e_sca_at_det_complex = complex(collection["E_sca_detected_complex"])
    e_sca_ref = _resolve_esca_reference(sim_cfg_case, optical, case_medium)
    e_sca_normalized_complex = e_sca_at_det_complex / e_sca_ref
    e_sca_normalized = float(abs(e_sca_normalized_complex))
    reference = compute_reference_field(
        channel,
        optical,
        sim_cfg_case,
        medium_refractive_index=case_medium.refractive_index_at(optical.wavelength_m),
    )
    overlap_diagnostics = {
        "interference_overlap_mode": str(sim_cfg_case.interference_overlap_mode),
        "interference_cross_term_model_default": str(sim_cfg_case.interference_overlap_mode),
        "interference_cross_term_joint_available": False,
        "interference_overlap_status": "unavailable_no_reference_angular_field",
    }
    if (
        sim_cfg_case.reference_model in {"channel_angular_surrogate", "paper_aligned_phase_filter"}
        and "reference_angular_field" in reference
        and "angular_field_theta" in collection
    ):
        overlap_diagnostics = build_interference_overlap_diagnostics(
            np.asarray(reference["reference_theta_grid_rad"], dtype=float),
            np.asarray(reference["reference_angular_field"], dtype=complex),
            np.asarray(collection["angular_field_theta"], dtype=complex),
            collection["collection_operator"],
            sim_cfg_case,
            phi_grid_rad=np.asarray(reference["reference_phi_grid_rad"], dtype=float),
            scattering_theta_grid_rad=np.asarray(collection["theta_grid_rad"], dtype=float),
        )
    reference.update(overlap_diagnostics)

    return {
        "particle": particle,
        "medium": case_medium,
        "channel": channel,
        "optical": optical,
        "sim_cfg": sim_cfg_case,
        "intrinsic": intrinsic,
        "reference": reference,
        "E_sca_at_det": float(e_sca_at_det),
        "E_sca_at_det_complex": complex(e_sca_at_det_complex),
        "E_sca_ref": float(e_sca_ref),
        "E_sca_normalized": e_sca_normalized,
        "E_sca_normalized_complex": complex(e_sca_normalized_complex),
        "phi_projection_rad": float(collection.get("phi_projection_rad", 0.0)),
        "phi_sca_material_rad": float(collection.get("phi_sca_material_rad", 0.0)),
        "phi_sca_material_parallel_rad": float(
            collection.get("phi_sca_material_parallel_rad", 0.0)
        ),
        "phi_sca_material_perpendicular_rad": float(
            collection.get("phi_sca_material_perpendicular_rad", 0.0)
        ),
        "theta_det_rad": float(theta_det),
        "theta_center_rad": float(collection["theta_center_rad"]),
        "sigma_effective_rad": float(collection.get("sigma_effective_rad", sim_cfg_case.collection_sigma_rad)),
        "interference_overlap_mode": reference.get("interference_overlap_mode"),
        "interference_overlap_status": reference.get("interference_overlap_status"),
        "interference_overlap_factor_abs": float(
            abs(reference.get("interference_overlap_factor_complex", 1.0 + 0.0j))
        ),
        "interference_overlap_factor_phase_rad": float(
            np.angle(reference.get("interference_overlap_factor_complex", 1.0 + 0.0j))
        ),
    }


def compute_interference_case(
    *,
    material: str,
    diameter_nm: int | float,
    wavelength_nm: int | float,
    width_nm: int | float,
    depth_nm: int | float,
    initial_x_fraction: float = 0.0,
    initial_z_fraction: float = 0.0,
    sim_cfg=None,
    optical_template=None,
) -> dict[str, object]:
    """
    Build a deterministic clean-signal case for the Interference Explorer.

    Uses a fixed particle path rather than a random batch so the page can clearly
    explain how E_sca becomes the clean interferometric pulse.
    """
    inputs = build_case_inputs(
        material=material,
        diameter_nm=diameter_nm,
        wavelength_nm=wavelength_nm,
        width_nm=width_nm,
        depth_nm=depth_nm,
        sim_cfg=sim_cfg,
        optical_template=optical_template,
    )

    channel = inputs["channel"]
    optical = inputs["optical"]
    base_cfg = inputs["sim_cfg"]
    sim_cfg_clean = deepcopy(base_cfg)
    sim_cfg_clean.include_diffusion = False

    x0_m = float(np.clip(initial_x_fraction, -1.0, 1.0)) * channel.width_m / 2.0
    z0_m = float(np.clip(initial_z_fraction, -1.0, 1.0)) * channel.depth_m / 2.0

    trajectory = simulate_particle_trajectory(
        channel,
        optical,
        sim_cfg_clean,
        x0_m,
        z0_m,
    )
    illumination = compute_illumination_envelope(
        trajectory["x_m"],
        trajectory["y_m"],
        trajectory["z_m"],
        optical,
        medium_refractive_index=inputs["medium"].refractive_index_at(optical.wavelength_m),
        sim_cfg=sim_cfg_clean,
    )
    reference_trace = compute_reference_field_trace(
        trajectory,
        inputs["reference"],
        channel,
        optical,
        sim_cfg_clean,
        initial_x_m=x0_m,
        initial_z_m=z0_m,
    )
    scattering_trace = compute_scattering_field_trace(
        trajectory,
        inputs["E_sca_normalized_complex"],
        optical,
        illumination,
        channel,
        x0_m,
        z0_m,
        sim_cfg_clean.phase_model,
        coupling_model=sim_cfg_clean.coupling_model,
        path_opd_model=sim_cfg_clean.path_opd_model,
        detection_theta_rad=float(inputs["theta_det_rad"]),
        medium_refractive_index=inputs["medium"].refractive_index_at(optical.wavelength_m),
        reference_phase_rad=reference_trace["phi_ref_trace_rad"],
        scattering_phase_diagnostics={
            "phi_sca_material_rad": inputs.get("phi_sca_material_rad"),
            "phi_sca_material_parallel_rad": inputs.get("phi_sca_material_parallel_rad"),
            "phi_sca_material_perpendicular_rad": inputs.get(
                "phi_sca_material_perpendicular_rad"
            ),
            "phi_projection_rad": inputs.get("phi_projection_rad"),
        },
    )
    interferometric = generate_interferometric_trace(
        trajectory,
        {**inputs["reference"], **reference_trace},
        scattering_trace,
        sim_cfg_clean,
    )

    e_sca = scattering_trace["E_sca_complex"]
    sca_only = np.abs(e_sca) ** 2
    cross_term = np.asarray(interferometric["interference_cross_term"], dtype=float)
    cross_term_collapsed = np.asarray(
        interferometric.get("interference_cross_term_collapsed", cross_term),
        dtype=float,
    )
    cross_term_joint = np.asarray(
        interferometric.get("interference_cross_term_joint", cross_term),
        dtype=float,
    )
    signal_clean = interferometric["signal_trace"]

    peak_idx = int(np.argmax(signal_clean))
    dominant_peak = _dominant_clean_peak_summary(trace_df=pd.DataFrame({"clean_signal": signal_clean}))
    dominant_idx = int(dominant_peak["dominant_peak_idx"])
    peak_sca_only = float(sca_only[peak_idx])
    peak_cross_term = float(cross_term[peak_idx])
    peak_cross_term_collapsed = float(cross_term_collapsed[peak_idx])
    peak_cross_term_joint = float(cross_term_joint[peak_idx])
    peak_signal = float(signal_clean[peak_idx])
    overlap_freeze = _classify_interference_overlap(
        overlap_factor_abs=float(interferometric.get("interference_overlap_factor_abs", 1.0)),
        overlap_factor_phase_rad=float(
            interferometric.get("interference_overlap_factor_phase_rad", 0.0)
        ),
        peak_cross_term_collapsed=peak_cross_term_collapsed,
        peak_cross_term_joint=peak_cross_term_joint,
        joint_available=bool(
            inputs["reference"].get("interference_cross_term_joint_available", False)
        ),
        default_model=str(sim_cfg_clean.interference_overlap_mode),
    )
    scattering_projection_basis = _resolve_projection_basis(
        sim_cfg_clean.scattering_projection_mode
    )
    illumination_projection_basis = str(
        illumination.get("illumination_projection_basis", "intensity_proxy")
    )
    reference_projection_basis = str(
        inputs["reference"].get("reference_projection_basis", "intensity_proxy")
    )
    projection_freeze = classify_projection_freeze(
        scattering_projection_basis=scattering_projection_basis,
        illumination_projection_coupling_status=str(
            illumination.get("illumination_projection_coupling_status", "legacy_basisless")
        ),
        reference_projection_coupling_status=str(
            inputs["reference"].get("reference_projection_coupling_status", "legacy_basisless")
        ),
        interference_projection_coupling_status=str(
            inputs["reference"].get("reference_projection_coupling_status", "legacy_basisless")
        ),
    )
    gouy_geometry = classify_delta_phi_gouy_geometry_validity(
        channel=inputs["channel"],
        optical=inputs["optical"],
        phase_model=str(sim_cfg_clean.phase_model),
    )
    observation_freeze = classify_observation_freeze(
        path_opd_freeze_status=str(scattering_trace.get("path_opd_freeze_status", "unknown")),
        interference_overlap_default_freeze_status=str(
            overlap_freeze.get("interference_overlap_default_freeze_status", "freeze_unavailable")
        ),
        projection_default_freeze_status=str(
            projection_freeze.get("projection_default_freeze_status", "freeze_unavailable")
        ),
        delta_phi_gouy_validity=str(gouy_geometry.get("delta_phi_gouy_validity", "unavailable")),
    )

    heterodyne_gain = np.inf
    if abs(peak_sca_only) > 1e-30:
        heterodyne_gain = float(abs(peak_cross_term) / abs(peak_sca_only))

    trace_df = pd.DataFrame(
        {
            "time_ms": trajectory["time_s"] * 1e3,
            "A_env": illumination["A_env"],
            "A_env_scalar": illumination.get("A_env_scalar"),
            "A_sca": scattering_trace["A_sca"],
            "A_ref_local": reference_trace["A_ref_trace"],
            "phi_ref_rad": reference_trace["phi_ref_trace_rad"],
            "reference_amplitude_scale": reference_trace["reference_amplitude_scale"],
            "reference_spatial_phase_rad": reference_trace["reference_spatial_phase_rad"],
            "delta_phi_ref_rad": scattering_trace["delta_phi_ref_rad"],
            "phi_material_rad": scattering_trace.get("phi_material_rad"),
            "phi_projection_rad": scattering_trace.get("phi_projection_rad"),
            "phi_material_parallel_rad": scattering_trace.get("phi_material_parallel_rad"),
            "phi_material_perpendicular_rad": scattering_trace.get(
                "phi_material_perpendicular_rad"
            ),
            "phi_beam_rad": scattering_trace.get("phi_beam_rad"),
            "phi_beam_gouy_rad": scattering_trace.get("phi_beam_gouy_rad"),
            "phi_beam_curv_rad": scattering_trace.get("phi_beam_curv_rad"),
            "phi_focus_crossing_rad": scattering_trace.get("phi_focus_crossing_rad"),
            "phi_gouy_ref_rad": scattering_trace.get("phi_gouy_ref_rad"),
            "phi_gouy_sca_rad": scattering_trace.get("phi_gouy_sca_rad"),
            "delta_phi_gouy_rad": scattering_trace.get("delta_phi_gouy_rad"),
            "gouy_dedup_active": scattering_trace.get("gouy_dedup_active"),
            "phi_gouy_reference_status": scattering_trace.get("phi_gouy_reference_status"),
            "phi_gouy_scattering_status": scattering_trace.get("phi_gouy_scattering_status"),
            "phi_gouy_semantics_status": scattering_trace.get("phi_gouy_semantics_status"),
            "phi_sca_path_x_rad": scattering_trace.get("phi_sca_path_x_rad"),
            "phi_sca_path_z_rad": scattering_trace.get("phi_sca_path_z_rad"),
            "phi_ref_trace_rad": scattering_trace.get("phi_ref_rad"),
            "phi_sca_path_rad": scattering_trace.get("phi_sca_path_rad"),
            "phi_extra_rad": scattering_trace.get("phi_extra_rad"),
            "f_coupling": scattering_trace["f_coupling"],
            "illumination_polarization_amplitude_factor": scattering_trace.get(
                "illumination_polarization_amplitude_factor"
            ),
            "sca_only_term": sca_only,
            "cross_term": cross_term,
            "cross_term_collapsed": cross_term_collapsed,
            "cross_term_joint": cross_term_joint,
            "clean_signal": signal_clean,
            "I_det": interferometric["I_det"],
        }
    )

    return {
        "trace_df": trace_df,
        "inputs": inputs,
        "summary": {
            "Csca_m2": float(inputs["intrinsic"]["Csca_m2"]),
            "E_sca_at_det": float(inputs["E_sca_at_det"]),
            "E_sca_ref": float(inputs["E_sca_ref"]),
            "E_sca_normalized": float(inputs["E_sca_normalized"]),
            "phi_projection_rad": float(inputs.get("phi_projection_rad", 0.0)),
            "phi_sca_material_rad": float(inputs.get("phi_sca_material_rad", 0.0)),
            "phi_sca_material_parallel_rad": float(
                inputs.get("phi_sca_material_parallel_rad", 0.0)
            ),
            "phi_sca_material_perpendicular_rad": float(
                inputs.get("phi_sca_material_perpendicular_rad", 0.0)
            ),
            "A_ref": float(inputs["reference"]["A_ref"]),
            "A_ref_unprojected": float(
                inputs["reference"].get("A_ref_unprojected", inputs["reference"]["A_ref"])
            ),
            "g_ref": float(inputs["reference"]["g_ref"]),
            "g_ref_geometry": float(
                inputs["reference"].get("g_ref_geometry", inputs["reference"]["g_ref"])
            ),
            "theta_det_deg": float(np.degrees(inputs["theta_det_rad"])),
            "theta_center_deg": float(np.degrees(inputs["theta_center_rad"])),
            "sigma_effective_deg": float(np.degrees(inputs["sigma_effective_rad"])),
            "peak_time_ms": float(trace_df.loc[peak_idx, "time_ms"]),
            "peak_A_env": float(illumination["A_env"][peak_idx]),
            "peak_A_env_scalar": float(
                illumination.get("A_env_scalar", illumination["A_env"])[peak_idx]
            ),
            "peak_A_sca": float(scattering_trace["A_sca"][peak_idx]),
            "peak_A_ref_local": float(reference_trace["A_ref_trace"][peak_idx]),
            "peak_phi_ref_rad": float(reference_trace["phi_ref_trace_rad"][peak_idx]),
            "peak_reference_spatial_phase_rad": float(reference_trace["reference_spatial_phase_rad"][peak_idx]),
            "peak_delta_phi_ref_rad": float(scattering_trace["delta_phi_ref_rad"][peak_idx]),
            "peak_phi_material_rad": float(scattering_trace["phi_material_rad"][peak_idx]),
            "peak_phi_projection_rad": float(scattering_trace["phi_projection_rad"][peak_idx]),
            "peak_phi_material_parallel_rad": float(
                scattering_trace["phi_material_parallel_rad"][peak_idx]
            ),
            "peak_phi_material_perpendicular_rad": float(
                scattering_trace["phi_material_perpendicular_rad"][peak_idx]
            ),
            "peak_phi_beam_rad": float(scattering_trace["phi_beam_rad"][peak_idx]),
            "peak_phi_beam_gouy_rad": float(scattering_trace["phi_beam_gouy_rad"][peak_idx]),
            "peak_phi_beam_curv_rad": float(scattering_trace["phi_beam_curv_rad"][peak_idx]),
            "peak_phi_focus_crossing_rad": float(
                scattering_trace.get("phi_focus_crossing_rad", np.zeros_like(scattering_trace["phi_beam_rad"]))[peak_idx]
            ),
            "peak_phi_gouy_ref_rad": float(
                scattering_trace.get("phi_gouy_ref_rad", scattering_trace["phi_beam_gouy_rad"])[peak_idx]
            ),
            "peak_phi_gouy_sca_rad": float(
                scattering_trace.get("phi_gouy_sca_rad", scattering_trace["phi_beam_gouy_rad"])[peak_idx]
            ),
            "peak_delta_phi_gouy_rad": float(
                scattering_trace.get("delta_phi_gouy_rad", np.zeros_like(scattering_trace["phi_beam_rad"]))[peak_idx]
            ),
            "gouy_dedup_active": bool(scattering_trace.get("gouy_dedup_active", False)),
            "phi_gouy_reference_status": str(
                scattering_trace.get("phi_gouy_reference_status", "unavailable")
            ),
            "phi_gouy_scattering_status": str(
                scattering_trace.get("phi_gouy_scattering_status", "unavailable")
            ),
            "phi_gouy_semantics_status": str(
                scattering_trace.get("phi_gouy_semantics_status", "legacy_unavailable")
            ),
            "peak_phi_sca_path_x_rad": float(scattering_trace["phi_sca_path_x_rad"][peak_idx]),
            "peak_phi_sca_path_z_rad": float(scattering_trace["phi_sca_path_z_rad"][peak_idx]),
            "peak_phi_sca_path_rad": float(scattering_trace["phi_sca_path_rad"][peak_idx]),
            "path_opd_freeze_status": str(
                scattering_trace.get("path_opd_freeze_status", "unknown")
            ),
            "peak_sca_only": peak_sca_only,
            "peak_cross_term": peak_cross_term,
            "peak_cross_term_collapsed": peak_cross_term_collapsed,
            "peak_cross_term_joint": peak_cross_term_joint,
            "peak_clean_signal": peak_signal,
            "dominant_peak_clean_signal": float(dominant_peak["dominant_peak_clean_signal"]),
            "dominant_peak_abs_clean_signal": float(dominant_peak["dominant_peak_abs_clean_signal"]),
            "dominant_peak_polarity": str(dominant_peak["dominant_peak_polarity"]),
            "dominant_peak_phi_material_rad": float(scattering_trace["phi_material_rad"][dominant_idx]),
            "dominant_peak_phi_projection_rad": float(scattering_trace["phi_projection_rad"][dominant_idx]),
            "dominant_peak_phi_material_parallel_rad": float(
                scattering_trace["phi_material_parallel_rad"][dominant_idx]
            ),
            "dominant_peak_phi_material_perpendicular_rad": float(
                scattering_trace["phi_material_perpendicular_rad"][dominant_idx]
            ),
            "dominant_peak_phi_ref_rad": float(reference_trace["phi_ref_trace_rad"][dominant_idx]),
            "dominant_peak_delta_phi_ref_rad": float(scattering_trace["delta_phi_ref_rad"][dominant_idx]),
            "dominant_peak_phi_sca_path_x_rad": float(
                scattering_trace["phi_sca_path_x_rad"][dominant_idx]
            ),
            "dominant_peak_phi_sca_path_z_rad": float(
                scattering_trace["phi_sca_path_z_rad"][dominant_idx]
            ),
            "heterodyne_gain": heterodyne_gain,
            "coupling_factor": float(np.asarray(scattering_trace["f_coupling"])[peak_idx]),
            "initial_x_nm": x0_m * 1e9,
            "initial_z_nm": z0_m * 1e9,
            "reference_spatial_mode": reference_trace["reference_spatial_mode"],
            "illumination_polarization_mode": str(
                illumination.get("illumination_polarization_mode", "legacy_scalar")
            ),
            "illumination_polarization_effective_mode": str(
                illumination.get(
                    "illumination_polarization_effective_mode",
                    "intensity_proxy",
                )
            ),
            "illumination_polarization_alignment_status": str(
                illumination.get(
                    "illumination_polarization_alignment_status",
                    "legacy_scalar",
                )
            ),
            "illumination_polarization_amplitude_factor": float(
                illumination.get("illumination_polarization_amplitude_factor", 1.0)
            ),
            "illumination_projection_basis": illumination_projection_basis,
            "illumination_effective_basis": str(
                illumination.get("illumination_effective_basis", "intensity_proxy")
            ),
            "illumination_projection_basis_match": bool(
                illumination.get("illumination_projection_basis_match", False)
            ),
            "illumination_projection_coupling_status": str(
                illumination.get(
                    "illumination_projection_coupling_status",
                    "legacy_basisless",
                )
            ),
            "reference_projection_mode": str(
                inputs["reference"].get("reference_projection_mode", "match_scattering")
            ),
            "reference_projection_effective_mode": str(
                inputs["reference"].get(
                    "reference_projection_effective_mode",
                    "intensity_proxy",
                )
            ),
            "reference_projection_alignment_status": str(
                inputs["reference"].get(
                    "reference_projection_alignment_status",
                    "legacy_basisless",
                )
            ),
            "reference_projection_amplitude_factor": float(
                inputs["reference"].get("reference_projection_amplitude_factor", 1.0)
            ),
            "reference_projection_basis": reference_projection_basis,
            "reference_effective_basis": str(
                inputs["reference"].get("reference_effective_basis", "intensity_proxy")
            ),
            "reference_projection_basis_match": bool(
                inputs["reference"].get("reference_projection_basis_match", False)
            ),
            "reference_projection_coupling_status": str(
                inputs["reference"].get(
                    "reference_projection_coupling_status",
                    "legacy_basisless",
                )
            ),
            "interference_projection_basis": reference_projection_basis,
            "interference_projection_basis_match": bool(
                inputs["reference"].get("reference_projection_basis_match", False)
            ),
            "interference_projection_coupling_status": str(
                inputs["reference"].get(
                    "reference_projection_coupling_status",
                    "legacy_basisless",
                )
            ),
            "interference_phase_aware_shared_basis": bool(
                inputs["reference"].get("reference_phase_aware_shared_basis", False)
            ),
            "interference_cross_term_mode": str(
                interferometric.get("interference_cross_term_mode", "collapsed_then_multiplied")
            ),
            "interference_overlap_mode": str(
                inputs.get("interference_overlap_mode", "collapsed_then_multiplied")
            ),
            "interference_overlap_status": str(
                interferometric.get("interference_overlap_status", "unavailable_no_reference_angular_field")
            ),
            "interference_overlap_factor_abs": float(
                interferometric.get("interference_overlap_factor_abs", 1.0)
            ),
            "interference_overlap_factor_phase_rad": float(
                interferometric.get("interference_overlap_factor_phase_rad", 0.0)
            ),
            **overlap_freeze,
            "scattering_projection_basis": scattering_projection_basis,
            **_projection_mode_semantics(sim_cfg_clean.scattering_projection_mode),
            **projection_freeze,
            **gouy_geometry,
            **observation_freeze,
        },
        "intrinsic": {
            "Csca_m2": float(inputs["intrinsic"]["Csca_m2"]),
            "Cext_m2": float(inputs["intrinsic"]["Cext_m2"]),
            "size_parameter": float(inputs["intrinsic"]["size_parameter"]),
            "path_opd_model": str(scattering_trace.get("path_opd_model", "single_pass")),
            "path_opd_reference_plane": str(
                scattering_trace.get("path_opd_reference_plane", "unknown")
            ),
            "path_opd_z_geometry_factor": float(
                scattering_trace.get("path_opd_z_geometry_factor", 1.0)
            ),
            "path_opd_z_reference_mode": str(
                scattering_trace.get("path_opd_z_reference_mode", "unknown")
            ),
            "path_opd_default_model": str(
                scattering_trace.get("path_opd_default_model", "single_pass")
            ),
            "path_opd_model_role": str(
                scattering_trace.get("path_opd_model_role", "unknown")
            ),
            "path_opd_default_frozen": bool(
                scattering_trace.get("path_opd_default_frozen", True)
            ),
            "path_opd_freeze_status": str(
                scattering_trace.get("path_opd_freeze_status", "unknown")
            ),
        },
        "reference": {
            "A_ref": float(inputs["reference"]["A_ref"]),
            "A_ref_unprojected": float(
                inputs["reference"].get("A_ref_unprojected", inputs["reference"]["A_ref"])
            ),
            "g_ref": float(inputs["reference"]["g_ref"]),
            "g_ref_geometry": float(
                inputs["reference"].get("g_ref_geometry", inputs["reference"]["g_ref"])
            ),
            "phi_ref_rad": float(inputs["reference"]["phi_ref_rad"]),
            "reference_spatial_mode": reference_trace["reference_spatial_mode"],
            "reference_projection_mode": str(
                inputs["reference"].get("reference_projection_mode", "match_scattering")
            ),
            "reference_projection_effective_mode": str(
                inputs["reference"].get(
                    "reference_projection_effective_mode",
                    "intensity_proxy",
                )
            ),
            "reference_projection_alignment_status": str(
                inputs["reference"].get(
                    "reference_projection_alignment_status",
                    "legacy_basisless",
                )
            ),
            "reference_projection_amplitude_factor": float(
                inputs["reference"].get("reference_projection_amplitude_factor", 1.0)
            ),
            "reference_projection_basis": reference_projection_basis,
            "reference_effective_basis": str(
                inputs["reference"].get("reference_effective_basis", "intensity_proxy")
            ),
            "reference_projection_basis_match": bool(
                inputs["reference"].get("reference_projection_basis_match", False)
            ),
            "reference_projection_coupling_status": str(
                inputs["reference"].get(
                    "reference_projection_coupling_status",
                    "legacy_basisless",
                )
            ),
            "reference_spatial_amplitude_strength": float(
                reference_trace["reference_spatial_amplitude_strength"]
            ),
            "reference_spatial_phase_strength_rad": float(
                reference_trace["reference_spatial_phase_strength_rad"]
            ),
            "calibration_extrapolated": bool(inputs["reference"].get("calibration_extrapolated", False)),
        },
        "meta": {
            "material": material,
            "diameter_nm": int(round(float(diameter_nm))),
            "wavelength_nm": int(round(float(wavelength_nm))),
            "width_nm": int(round(float(width_nm))),
            "depth_nm": int(round(float(depth_nm))),
        },
    }


def build_interference_scan_dataframe(
    *,
    scan_variable: str,
    scan_values: list[float] | np.ndarray,
    material: str,
    diameter_nm: int | float,
    wavelength_nm: int | float,
    width_nm: int | float,
    depth_nm: int | float,
    initial_x_fraction: float = 0.0,
    initial_z_fraction: float = 0.0,
    sim_cfg=None,
    optical_template=None,
) -> pd.DataFrame:
    """Build a compact scan showing how clean-signal terms change with one variable."""
    rows: list[dict[str, object]] = []
    for value in scan_values:
        case_kwargs = {
            "material": material,
            "diameter_nm": diameter_nm,
            "wavelength_nm": wavelength_nm,
            "width_nm": width_nm,
            "depth_nm": depth_nm,
            "initial_x_fraction": initial_x_fraction,
            "initial_z_fraction": initial_z_fraction,
            "sim_cfg": sim_cfg,
            "optical_template": optical_template,
        }
        sim_cfg_case = deepcopy(sim_cfg or DEFAULT_SIM_CFG)
        if scan_variable == "width_nm":
            case_kwargs["width_nm"] = value
        elif scan_variable == "depth_nm":
            case_kwargs["depth_nm"] = value
        elif scan_variable == "wavelength_nm":
            case_kwargs["wavelength_nm"] = value
        elif scan_variable == "rho":
            sim_cfg_case.rho = float(value)
            case_kwargs["sim_cfg"] = sim_cfg_case
        else:
            raise ValueError(f"Unsupported interference scan variable: {scan_variable}")

        try:
            case = compute_interference_case(**case_kwargs)
            summary = case["summary"]
            rows.append(
                {
                    scan_variable: float(value),
                    "valid": True,
                    "A_ref": summary["A_ref"],
                    "E_sca_normalized": summary["E_sca_normalized"],
                    "peak_clean_signal": summary["peak_clean_signal"],
                    "peak_cross_term": summary["peak_cross_term"],
                    "peak_sca_only": summary["peak_sca_only"],
                    "heterodyne_gain": summary["heterodyne_gain"],
                    "peak_delta_phi_ref_rad": summary.get("peak_delta_phi_ref_rad"),
                    "peak_phi_material_rad": summary.get("peak_phi_material_rad"),
                    "peak_phi_projection_rad": summary.get("peak_phi_projection_rad"),
                }
            )
        except ValueError as exc:
            rows.append(
                {
                    scan_variable: float(value),
                    "valid": False,
                    "A_ref": np.nan,
                    "E_sca_normalized": np.nan,
                    "peak_clean_signal": np.nan,
                    "peak_cross_term": np.nan,
                    "peak_sca_only": np.nan,
                    "heterodyne_gain": np.nan,
                    "error": str(exc),
                }
            )

    return pd.DataFrame(rows)


def build_projection_mode_validation_dataframe(
    *,
    material: str,
    diameter_nm: int | float,
    wavelength_values_nm: list[float] | np.ndarray,
    width_nm: int | float,
    depth_nm: int | float,
    initial_x_fraction: float = 0.0,
    initial_z_fraction: float = 0.0,
    projection_modes: tuple[str, ...] = ("parallel", "perpendicular", "intensity_proxy"),
    sim_cfg=None,
    optical_template=None,
) -> pd.DataFrame:
    """
    Build a fixed-position wavelength validation table across projection modes.

    This is used to audit whether polarity and phase trends come from the
    material Mie phase, the downstream projection operator, or the legacy
    intensity-only path.
    """
    rows: list[dict[str, object]] = []
    for mode in projection_modes:
        mode_cfg = deepcopy(sim_cfg or DEFAULT_SIM_CFG)
        mode_cfg.scattering_projection_mode = mode
        mode_meta = _projection_mode_semantics(mode)
        for wavelength_nm in wavelength_values_nm:
            case = compute_interference_case(
                material=material,
                diameter_nm=diameter_nm,
                wavelength_nm=wavelength_nm,
                width_nm=width_nm,
                depth_nm=depth_nm,
                initial_x_fraction=initial_x_fraction,
                initial_z_fraction=initial_z_fraction,
                sim_cfg=mode_cfg,
                optical_template=optical_template,
            )
            summary = case["summary"]
            rows.append(
                {
                    "scattering_projection_mode": mode,
                    "projection_mode_role": mode_meta["projection_mode_role"],
                    "phase_aware": bool(mode_meta["phase_aware"]),
                    "material_phase_source": mode_meta["material_phase_source"],
                    "wavelength_nm": float(wavelength_nm),
                    "dominant_peak_clean_signal": summary["dominant_peak_clean_signal"],
                    "dominant_peak_abs_clean_signal": summary["dominant_peak_abs_clean_signal"],
                    "dominant_peak_polarity": summary["dominant_peak_polarity"],
                    "dominant_peak_phi_material_rad": summary["dominant_peak_phi_material_rad"],
                    "dominant_peak_phi_projection_rad": summary["dominant_peak_phi_projection_rad"],
                    "dominant_peak_delta_phi_ref_rad": summary["dominant_peak_delta_phi_ref_rad"],
                    "peak_clean_signal": summary["peak_clean_signal"],
                    "peak_phi_material_rad": summary["peak_phi_material_rad"],
                    "peak_phi_projection_rad": summary["peak_phi_projection_rad"],
                    "peak_delta_phi_ref_rad": summary["peak_delta_phi_ref_rad"],
                    "A_ref": summary["A_ref"],
                    "E_sca_normalized": summary["E_sca_normalized"],
                    "heterodyne_gain": summary["heterodyne_gain"],
                    "theta_det_deg": summary["theta_det_deg"],
                }
            )
    return pd.DataFrame(rows)


def build_reference_model_consistency_report(
    *,
    width_values_nm: list[float] | np.ndarray,
    depth_values_nm: list[float] | np.ndarray,
    wavelength_values_nm: list[float] | np.ndarray,
    sim_cfg=None,
    optical_template=None,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """
    Compare calibrated_lookup and channel_angular_surrogate on the same W/H/lambda grid.

    The goal is not to force equality. It is to audit whether the surrogate
    preserves the same broad ranking / trend structure on points where the
    calibration table is defined.
    """
    base_cfg = deepcopy(sim_cfg or DEFAULT_SIM_CFG)
    if not base_cfg.reference_calibration_path:
        raise ValueError("Reference consistency report requires a calibration table path.")

    surrogate_cfg = deepcopy(base_cfg)
    surrogate_cfg.reference_model = "channel_angular_surrogate"
    calibrated_cfg = deepcopy(base_cfg)
    calibrated_cfg.reference_model = "calibrated_lookup"

    rows: list[dict[str, object]] = []
    point_index = 0
    for width_nm in width_values_nm:
        for depth_nm in depth_values_nm:
            channel = Channel(width_m=float(width_nm) * 1e-9, depth_m=float(depth_nm) * 1e-9)
            for wavelength_nm in wavelength_values_nm:
                optical = deepcopy(optical_template or OPTICAL_TEMPLATE)
                optical.wavelength_m = float(wavelength_nm) * 1e-9
                n_medium = MEDIUM.refractive_index_at(optical.wavelength_m)
                ref_surrogate = compute_reference_field(
                    channel,
                    optical,
                    surrogate_cfg,
                    medium_refractive_index=n_medium,
                )
                ref_calibrated = compute_reference_field(
                    channel,
                    optical,
                    calibrated_cfg,
                    medium_refractive_index=n_medium,
                )
                a_cal = float(ref_calibrated["A_ref"])
                g_cal = float(ref_calibrated["g_ref"])
                a_sur = float(ref_surrogate["A_ref"])
                g_sur = float(ref_surrogate["g_ref"])
                phi_delta = _wrapped_phase_delta_rad(
                    ref_surrogate["phi_ref_rad"],
                    ref_calibrated["phi_ref_rad"],
                )
                rows.append(
                    {
                        "point_index": point_index,
                        "point_label": (
                            f"W={int(round(float(width_nm)))} | "
                            f"H={int(round(float(depth_nm)))} | "
                            f"λ={int(round(float(wavelength_nm)))}"
                        ),
                        "width_nm": float(width_nm),
                        "depth_nm": float(depth_nm),
                        "wavelength_nm": float(wavelength_nm),
                        "A_ref_surrogate": a_sur,
                        "A_ref_calibrated": a_cal,
                        "A_ref_delta": a_sur - a_cal,
                        "A_ref_rel_error": (
                            (a_sur - a_cal) / a_cal if abs(a_cal) > 1e-12 else np.nan
                        ),
                        "g_ref_surrogate": g_sur,
                        "g_ref_calibrated": g_cal,
                        "g_ref_delta": g_sur - g_cal,
                        "g_ref_rel_error": (
                            (g_sur - g_cal) / g_cal if abs(g_cal) > 1e-12 else np.nan
                        ),
                        "phi_ref_surrogate_rad": float(ref_surrogate["phi_ref_rad"]),
                        "phi_ref_calibrated_rad": float(ref_calibrated["phi_ref_rad"]),
                        "phi_ref_delta_wrapped_rad": phi_delta,
                        "calibration_extrapolated": bool(
                            ref_calibrated.get("calibration_extrapolated", False)
                        ),
                    }
                )
                point_index += 1

    df = pd.DataFrame(rows)
    summary = _summarize_reference_consistency_subset(df)
    by_wavelength: list[dict[str, object]] = []
    for wavelength_nm, sub_df in df.groupby("wavelength_nm", sort=True):
        sub_summary = _summarize_reference_consistency_subset(sub_df)
        sub_summary["wavelength_nm"] = float(wavelength_nm)
        by_wavelength.append(sub_summary)
    summary["reference_consistency_split_dimension"] = "wavelength_nm"
    summary["reference_consistency_material_split_applicable"] = False
    summary["reference_consistency_split_note"] = (
        "reference field depends on channel geometry / wavelength / wall-medium optics; "
        "particle material does not enter this layer, so wavelength stratification is meaningful "
        "but material stratification is not."
    )
    summary["reference_consistency_by_wavelength"] = by_wavelength
    return df, summary


def build_path_opd_freeze_report(
    *,
    material: str,
    diameter_nm: int | float,
    wavelength_nm: int | float,
    width_nm: int | float,
    depth_nm: int | float,
    initial_x_fraction: float = 0.0,
    initial_z_fraction: float = 0.0,
    sim_cfg=None,
    optical_template=None,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """
    Compare the current OPD variants on one live case and emit freeze guidance.

    This report is intentionally local and diagnostic. It does not alter the
    main computation path; it exists to make the current single_pass freeze
    decision auditable against the retained roundtrip / wall-referenced
    alternatives.
    """
    base_cfg = deepcopy(sim_cfg or DEFAULT_SIM_CFG)
    optical = deepcopy(optical_template or OPTICAL_TEMPLATE)
    channel = Channel(float(width_nm) * 1e-9, float(depth_nm) * 1e-9)
    gouy_geometry = classify_delta_phi_gouy_geometry_validity(
        channel=channel,
        optical=optical,
        phase_model=str(base_cfg.phase_model),
    )
    comparison_models = [
        "single_pass",
        "reference_plane_roundtrip_surrogate",
        "wall_referenced_gap_surrogate",
    ]

    rows: list[dict[str, object]] = []
    for model in comparison_models:
        model_cfg = deepcopy(base_cfg)
        model_cfg.path_opd_model = model
        case = compute_interference_case(
            material=material,
            diameter_nm=diameter_nm,
            wavelength_nm=wavelength_nm,
            width_nm=width_nm,
            depth_nm=depth_nm,
            initial_x_fraction=initial_x_fraction,
            initial_z_fraction=initial_z_fraction,
            sim_cfg=model_cfg,
            optical_template=optical,
        )
        summary = case["summary"]
        intrinsic = case.get("intrinsic", {})
        rows.append(
            {
                "path_opd_model": intrinsic.get("path_opd_model", model),
                "path_opd_reference_plane": intrinsic.get("path_opd_reference_plane"),
                "path_opd_z_geometry_factor": float(
                    intrinsic.get("path_opd_z_geometry_factor", np.nan)
                ),
                "path_opd_z_reference_mode": intrinsic.get("path_opd_z_reference_mode"),
                "path_opd_model_role": intrinsic.get("path_opd_model_role"),
                "path_opd_default_frozen": bool(
                    intrinsic.get("path_opd_default_frozen", False)
                ),
                "path_opd_freeze_status": summary.get("path_opd_freeze_status"),
                "peak_clean_signal": float(summary.get("peak_clean_signal", np.nan)),
                "dominant_peak_clean_signal": float(
                    summary.get("dominant_peak_clean_signal", np.nan)
                ),
                "peak_delta_phi_ref_rad": float(
                    summary.get("peak_delta_phi_ref_rad", np.nan)
                ),
                "peak_phi_sca_path_z_rad": float(
                    summary.get("peak_phi_sca_path_z_rad", np.nan)
                ),
                "peak_phi_focus_crossing_rad": float(
                    summary.get("peak_phi_focus_crossing_rad", np.nan)
                ),
                "peak_phi_gouy_ref_rad": float(
                    summary.get("peak_phi_gouy_ref_rad", np.nan)
                ),
                "peak_phi_gouy_sca_rad": float(
                    summary.get("peak_phi_gouy_sca_rad", np.nan)
                ),
                "peak_delta_phi_gouy_rad": float(
                    summary.get("peak_delta_phi_gouy_rad", np.nan)
                ),
                "heterodyne_gain": float(summary.get("heterodyne_gain", np.nan)),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        summary = {
            "path_opd_freeze_n_alternative_models": 0,
            "path_opd_freeze_comparison_models": [],
            "path_opd_freeze_default_model": "single_pass",
        }
        summary.update(_classify_path_opd_and_gouy_freeze(summary, gouy_geometry=gouy_geometry))
        return df, summary

    default_row = df[df["path_opd_model"] == "single_pass"].iloc[0]
    default_peak_clean = max(abs(float(default_row["peak_clean_signal"])), 1e-12)
    default_peak_delta_phi_ref = float(default_row["peak_delta_phi_ref_rad"])
    default_peak_phi_sca_path_z = float(default_row["peak_phi_sca_path_z_rad"])
    default_peak_phi_gouy_ref = float(default_row["peak_phi_gouy_ref_rad"])
    default_peak_phi_gouy_sca = float(default_row["peak_phi_gouy_sca_rad"])
    default_peak_delta_phi_gouy = float(default_row["peak_delta_phi_gouy_rad"])

    df["peak_clean_rel_delta_vs_single_pass"] = (
        np.abs(df["peak_clean_signal"] - float(default_row["peak_clean_signal"]))
        / default_peak_clean
    )
    df["peak_delta_phi_ref_delta_vs_single_pass_rad"] = df["peak_delta_phi_ref_rad"].apply(
        lambda v: abs(_wrapped_phase_delta_rad(v, default_peak_delta_phi_ref))
    )
    df["peak_phi_sca_path_z_delta_vs_single_pass_rad"] = df[
        "peak_phi_sca_path_z_rad"
    ].apply(lambda v: abs(_wrapped_phase_delta_rad(v, default_peak_phi_sca_path_z)))
    df["peak_phi_gouy_ref_delta_vs_single_pass_rad"] = df["peak_phi_gouy_ref_rad"].apply(
        lambda v: abs(_wrapped_phase_delta_rad(v, default_peak_phi_gouy_ref))
    )
    df["peak_phi_gouy_sca_delta_vs_single_pass_rad"] = df["peak_phi_gouy_sca_rad"].apply(
        lambda v: abs(_wrapped_phase_delta_rad(v, default_peak_phi_gouy_sca))
    )
    df["peak_delta_phi_gouy_delta_vs_single_pass_rad"] = df[
        "peak_delta_phi_gouy_rad"
    ].apply(lambda v: abs(_wrapped_phase_delta_rad(v, default_peak_delta_phi_gouy)))

    alt_df = df[df["path_opd_model"] != "single_pass"].copy()
    summary = {
        "path_opd_freeze_n_models": int(len(df)),
        "path_opd_freeze_n_alternative_models": int(len(alt_df)),
        "path_opd_freeze_comparison_models": alt_df["path_opd_model"].tolist(),
        "path_opd_freeze_max_peak_clean_rel_delta": float(
            alt_df["peak_clean_rel_delta_vs_single_pass"].max()
            if not alt_df.empty
            else 0.0
        ),
        "path_opd_freeze_max_peak_delta_phi_ref_delta_rad": float(
            alt_df["peak_delta_phi_ref_delta_vs_single_pass_rad"].max()
            if not alt_df.empty
            else 0.0
        ),
        "path_opd_freeze_max_peak_phi_sca_path_z_delta_rad": float(
            alt_df["peak_phi_sca_path_z_delta_vs_single_pass_rad"].max()
            if not alt_df.empty
            else 0.0
        ),
        "delta_phi_gouy_freeze_max_peak_phi_gouy_ref_delta_rad": float(
            alt_df["peak_phi_gouy_ref_delta_vs_single_pass_rad"].max()
            if not alt_df.empty
            else 0.0
        ),
        "delta_phi_gouy_freeze_max_peak_phi_gouy_sca_delta_rad": float(
            alt_df["peak_phi_gouy_sca_delta_vs_single_pass_rad"].max()
            if not alt_df.empty
            else 0.0
        ),
        "delta_phi_gouy_freeze_max_peak_delta_phi_gouy_delta_rad": float(
            alt_df["peak_delta_phi_gouy_delta_vs_single_pass_rad"].max()
            if not alt_df.empty
            else 0.0
        ),
    }
    summary.update(_classify_path_opd_and_gouy_freeze(summary, gouy_geometry=gouy_geometry))
    return df, summary


def compute_noise_detection_case(
    *,
    material: str,
    diameter_nm: int | float,
    wavelength_nm: int | float,
    width_nm: int | float,
    depth_nm: int | float,
    sim_cfg=None,
    optical_template=None,
    n_events: int | None = None,
) -> dict[str, object]:
    """Run a batch case and reshape it for the Noise & Detection Explorer."""
    inputs = build_case_inputs(
        material=material,
        diameter_nm=diameter_nm,
        wavelength_nm=wavelength_nm,
        width_nm=width_nm,
        depth_nm=depth_nm,
        sim_cfg=sim_cfg,
        optical_template=optical_template,
    )

    sim_cfg_run = deepcopy(inputs["sim_cfg"])
    if n_events is not None:
        sim_cfg_run.n_events = int(n_events)

    result = run_single_case_batch(
        inputs["particle"],
        inputs["medium"],
        inputs["channel"],
        inputs["optical"],
        sim_cfg_run,
        inputs["E_sca_ref"],
        THETA_GRID_RAD,
    )

    event_rows: list[dict[str, object]] = []
    thresholds = []
    for idx, event in enumerate(result["events"]):
        features = event["features"]
        features_nodi = event.get("features_nodi", features)
        features_paired = event.get("features_paired", features)
        detected = features["n_peaks"] > 0
        detected_single_channel = bool(
            event.get("detected_single_channel", features_nodi["n_peaks"] > 0)
        )
        detected_paired_channel = bool(
            event.get("detected_paired_channel", features_paired["n_peaks"] > 0)
        )
        thresholds.append(float(event["threshold"]))
        best_peak_height = 0.0
        best_peak_width_ms = np.nan
        best_peak_height_single_channel = 0.0
        best_peak_height_paired_channel = 0.0
        if detected:
            best_peak = max(features["peaks"], key=lambda peak: peak["peak_height"])
            best_peak_height = float(best_peak["peak_height"])
            best_peak_width_ms = float(best_peak["peak_width_s"] * 1e3)
        if detected_single_channel:
            best_peak_single = max(
                features_nodi["peaks"], key=lambda peak: peak["peak_height"]
            )
            best_peak_height_single_channel = float(best_peak_single["peak_height"])
        if detected_paired_channel:
            best_peak_paired = max(
                features_paired["peaks"], key=lambda peak: peak["peak_height"]
            )
            best_peak_height_paired_channel = float(best_peak_paired["peak_height"])
        event_rows.append(
            {
                "event_index": idx,
                "detected": detected,
                "detected_single_channel": detected_single_channel,
                "detected_paired_channel": detected_paired_channel,
                "strict_paired_detected": bool(
                    event.get("strict_paired_detected", detected_paired_channel)
                ),
                "detection_decision_mode": event.get(
                    "detection_decision_mode", sim_cfg_run.detection_decision_mode
                ),
                "threshold": float(event["threshold"]),
                "clean_peak_max": float(np.max(event["signal_trace"])),
                "raw_peak_max": float(np.max(event.get("signal_raw_noisy", event["signal_noisy"]))),
                "noisy_peak_max": float(np.max(event["signal_noisy"])),
                "best_peak_height": best_peak_height,
                "best_peak_width_ms": best_peak_width_ms,
                "best_peak_height_single_channel": best_peak_height_single_channel,
                "best_peak_height_paired_channel": best_peak_height_paired_channel,
                "paired_pulse_count": int(event.get("paired_pulse_count", 0)),
                "best_peak_paired": bool(event.get("best_peak_paired", False)),
            }
        )

    event_df = pd.DataFrame(event_rows)

    return {
        "events": result["events"],
        "event_df": event_df,
        "summary": {
            **result["summary"],
            "mean_threshold": float(np.mean(thresholds)) if thresholds else 0.0,
            "miss_rate": 1.0 - float(result["summary"]["detection_rate"]),
            "E_sca_normalized": float(result["intrinsic"]["E_sca_unit_normalized"]),
            "A_ref": float(result["reference"]["A_ref"]),
            "g_ref": float(result["reference"]["g_ref"]),
            "reference_model_precision_tier": str(
                result["reference"].get("reference_model_precision_tier", "unknown")
            ),
            "reference_model_role": str(
                result["reference"].get("reference_model_role", "unknown")
            ),
            "reference_geometry_depth_exponent": float(
                result["reference"].get("reference_geometry_depth_exponent", np.nan)
            ),
            "reference_geometry_depth_scaling_class": str(
                result["reference"].get("reference_geometry_depth_scaling_class", "n/a")
            ),
            "theta_det_deg": float(np.degrees(result["intrinsic"]["theta_det_rad"])),
            "theta_center_deg": float(np.degrees(result["intrinsic"].get("theta_center_rad", result["intrinsic"]["theta_det_rad"]))),
            "sigma_effective_deg": float(np.degrees(result["intrinsic"].get("sigma_effective_rad", sim_cfg_run.collection_sigma_rad))),
            "readout_model": sim_cfg_run.readout_model,
            "readout_observable_mode": sim_cfg_run.readout_observable_mode,
            "lockin_time_constant_ms": float(sim_cfg_run.lockin_time_constant_s * 1e3),
            "pod_lockin_frequency_Hz": float(sim_cfg_run.pod_lockin_frequency_Hz),
            "nodi_lockin_frequency_Hz": float(sim_cfg_run.nodi_lockin_frequency_Hz),
            "pod_frequency_response_model": str(sim_cfg_run.pod_frequency_response_model),
            "pod_frequency_response_reference_Hz": float(
                sim_cfg_run.pod_frequency_response_reference_Hz
            ),
            "pod_frequency_response_exponent": float(
                sim_cfg_run.pod_frequency_response_exponent
            ),
            "pod_reference_phase_deg": float(np.degrees(sim_cfg_run.pod_reference_phase_rad)),
            "nodi_reference_phase_deg": float(np.degrees(sim_cfg_run.nodi_reference_phase_rad)),
            "pod_to_nodi_crosstalk": float(sim_cfg_run.pod_to_nodi_crosstalk),
            "nodi_to_pod_crosstalk": float(sim_cfg_run.nodi_to_pod_crosstalk),
            "pre_readout_noise_std": float(sim_cfg_run.noise_std),
            "shot_noise_scale": float(sim_cfg_run.shot_noise_scale),
            "pre_readout_drift_slope": float(sim_cfg_run.drift_slope),
            "post_readout_noise_std": float(sim_cfg_run.post_readout_noise_std),
            "post_readout_drift_slope": float(sim_cfg_run.post_readout_drift_slope),
            "mean_I_baseline": float(result["summary"].get("mean_I_baseline", 0.0)),
            "mean_shot_noise_std": float(result["summary"].get("mean_shot_noise_std", 0.0)),
            "mean_A_ref_local": float(result["summary"].get("mean_A_ref_local", 0.0)),
            "mean_A_sca_local": float(result["summary"].get("mean_A_sca_local", 0.0)),
            "mean_reference_to_scattering_amplitude_ratio": float(
                result["summary"].get("mean_reference_to_scattering_amplitude_ratio", 0.0)
            ),
            "rho_requested": float(result["summary"].get("rho_requested", sim_cfg_run.rho)),
            "rho_physical_envelope_nominal": result["summary"].get(
                "rho_physical_envelope_nominal"
            ),
            "rho_physical_envelope_status": result["summary"].get(
                "rho_physical_envelope_status",
                "unavailable",
            ),
            "reference_width_saturation_status": result["reference"].get(
                "reference_width_saturation_status"
            ),
            "reference_width_saturation_factor": result["reference"].get(
                "reference_width_saturation_factor"
            ),
            "single_channel_detection_rate": float(
                result["summary"].get("single_channel_detection_rate", 0.0)
            ),
            "paired_channel_detection_rate": float(
                result["summary"].get("paired_channel_detection_rate", 0.0)
            ),
            "strict_paired_detection_rate": float(
                result["summary"].get("strict_paired_detection_rate", 0.0)
            ),
            "detection_decision_mode": sim_cfg_run.detection_decision_mode,
            "engineering_decision_basis": sim_cfg_run.engineering_decision_basis,
        },
        "intrinsic": result["intrinsic"],
        "reference": result["reference"],
        "meta": {
            "material": material,
            "diameter_nm": int(round(float(diameter_nm))),
            "wavelength_nm": int(round(float(wavelength_nm))),
            "width_nm": int(round(float(width_nm))),
            "depth_nm": int(round(float(depth_nm))),
        },
    }


def build_event_trace_dataframe(case_result: dict[str, object], event_index: int) -> pd.DataFrame:
    """Extract a plotting dataframe for one event from a noise/detection batch case."""
    events = case_result["events"]
    if event_index < 0 or event_index >= len(events):
        raise IndexError(f"event_index out of range: {event_index}")
    event = events[event_index]
    return pd.DataFrame(
        {
            "time_ms": event["trajectory"]["time_s"] * 1e3,
            "clean_signal": event["signal_trace"],
            "signal_raw_noisy": event.get("signal_raw_noisy", event["signal_noisy"]),
            "shot_noise": event.get("shot_noise", np.zeros_like(event["signal_noisy"])),
            "signal_detect_pre_post": event.get("signal_detect_pre_post", event["signal_noisy"]),
            "signal_noisy": event["signal_noisy"],
            "signal_nodi": event.get("signal_nodi", event["signal_noisy"]),
            "signal_nodi_pre_post": event.get("signal_nodi_pre_post", event.get("signal_nodi", event["signal_noisy"])),
            "signal_nodi_i": event.get("signal_nodi_i", event.get("signal_nodi", event["signal_noisy"])),
            "signal_nodi_q": event.get("signal_nodi_q", np.zeros_like(event["signal_noisy"])),
            "signal_nodi_mag": event.get("signal_nodi_mag", np.abs(event.get("signal_nodi", event["signal_noisy"]))),
            "signal_pod": event.get("signal_pod", np.zeros_like(event["signal_noisy"])),
            "signal_pod_pre_post": event.get("signal_pod_pre_post", event.get("signal_pod", np.zeros_like(event["signal_noisy"]))),
            "signal_pod_i": event.get("signal_pod_i", event.get("signal_pod", np.zeros_like(event["signal_noisy"]))),
            "signal_pod_q": event.get("signal_pod_q", np.zeros_like(event["signal_noisy"])),
            "signal_pod_mag": event.get("signal_pod_mag", np.abs(event.get("signal_pod", np.zeros_like(event["signal_noisy"])))),
            "threshold": np.full_like(event["signal_trace"], event["threshold"], dtype=float),
            "A_ref_local": event.get("A_ref_trace", np.full_like(event["signal_trace"], np.nan)),
            "phi_ref_rad": event.get("phi_ref_rad", np.full_like(event["signal_trace"], np.nan)),
            "reference_amplitude_scale": event.get(
                "reference_amplitude_scale",
                np.full_like(event["signal_trace"], np.nan),
            ),
            "reference_spatial_phase_rad": event.get(
                "reference_spatial_phase_rad",
                np.full_like(event["signal_trace"], np.nan),
            ),
            "delta_phi_ref_rad": event.get("delta_phi_ref_rad", np.full_like(event["signal_trace"], np.nan)),
            "phi_material_rad": event.get("phi_material_rad", np.full_like(event["signal_trace"], np.nan)),
            "phi_projection_rad": event.get("phi_projection_rad", np.full_like(event["signal_trace"], np.nan)),
            "phi_material_parallel_rad": event.get(
                "phi_material_parallel_rad",
                np.full_like(event["signal_trace"], np.nan),
            ),
            "phi_material_perpendicular_rad": event.get(
                "phi_material_perpendicular_rad",
                np.full_like(event["signal_trace"], np.nan),
            ),
            "phi_beam_rad": event.get("phi_beam_rad", np.full_like(event["signal_trace"], np.nan)),
            "phi_beam_gouy_rad": event.get("phi_beam_gouy_rad", np.full_like(event["signal_trace"], np.nan)),
            "phi_beam_curv_rad": event.get("phi_beam_curv_rad", np.full_like(event["signal_trace"], np.nan)),
            "phi_sca_path_x_rad": event.get("phi_sca_path_x_rad", np.full_like(event["signal_trace"], np.nan)),
            "phi_sca_path_z_rad": event.get("phi_sca_path_z_rad", np.full_like(event["signal_trace"], np.nan)),
            "phi_sca_path_rad": event.get("phi_sca_path_rad", np.full_like(event["signal_trace"], np.nan)),
            "phi_extra_rad": event.get("phi_extra_rad", np.full_like(event["signal_trace"], np.nan)),
        }
    )


def build_rho_sensitivity_report(
    *,
    material: str,
    diameter_nm: int | float,
    wavelength_nm: int | float,
    width_nm: int | float,
    depth_nm: int | float,
    sim_cfg=None,
    optical_template=None,
    n_events: int | None = None,
    requested_interference_case: dict[str, object] | None = None,
    requested_noise_case: dict[str, object] | None = None,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """
    Probe one case at requested/lower/nominal/upper rho anchors.

    This stays diagnostic-only: it does not overwrite `sim_cfg.rho`. The goal is
    to make the existing rho-envelope diagnostic actionable by showing whether
    lower / nominal / upper rho values materially change clean-signal and batch
    conclusions for the current case.
    """
    report_cfg, seed_source = _resolve_report_sim_cfg(sim_cfg, n_events=n_events)
    optical = deepcopy(optical_template or OPTICAL_TEMPLATE)

    if requested_noise_case is None:
        requested_noise_case = compute_noise_detection_case(
            material=material,
            diameter_nm=diameter_nm,
            wavelength_nm=wavelength_nm,
            width_nm=width_nm,
            depth_nm=depth_nm,
            sim_cfg=report_cfg,
            optical_template=optical,
            n_events=int(report_cfg.n_events),
        )
    if requested_interference_case is None:
        requested_interference_case = compute_interference_case(
            material=material,
            diameter_nm=diameter_nm,
            wavelength_nm=wavelength_nm,
            width_nm=width_nm,
            depth_nm=depth_nm,
            sim_cfg=report_cfg,
            optical_template=optical,
        )

    requested_noise_summary = requested_noise_case["summary"]
    requested_reference = requested_noise_case["reference"]
    requested_rho = float(requested_noise_summary.get("rho_requested", report_cfg.rho))
    rho_lower = requested_reference.get("rho_physical_envelope_lower")
    rho_nominal = requested_reference.get("rho_physical_envelope_nominal")
    rho_upper = requested_reference.get("rho_physical_envelope_upper")

    candidates: list[dict[str, object]] = []

    def _register_candidate(role: str, value: object) -> None:
        if value is None:
            return
        rho_value = float(value)
        if (not np.isfinite(rho_value)) or rho_value <= 0.0:
            return
        for item in candidates:
            if np.isclose(float(item["rho"]), rho_value, rtol=1e-9, atol=1e-12):
                item["roles"].append(role)
                return
        candidates.append({"rho": rho_value, "roles": [role]})

    _register_candidate("requested", requested_rho)
    _register_candidate("rho_physical_envelope_lower", rho_lower)
    _register_candidate("rho_physical_envelope_nominal", rho_nominal)
    _register_candidate("rho_physical_envelope_upper", rho_upper)
    candidates.sort(key=lambda item: float(item["rho"]))

    rows: list[dict[str, object]] = []
    for candidate in candidates:
        rho_value = float(candidate["rho"])
        roles = list(candidate["roles"])

        if np.isclose(rho_value, requested_rho, rtol=1e-9, atol=1e-12):
            intf_case = requested_interference_case
            noise_case = requested_noise_case
        else:
            candidate_cfg = deepcopy(report_cfg)
            candidate_cfg.rho = rho_value
            intf_case = compute_interference_case(
                material=material,
                diameter_nm=diameter_nm,
                wavelength_nm=wavelength_nm,
                width_nm=width_nm,
                depth_nm=depth_nm,
                sim_cfg=candidate_cfg,
                optical_template=optical,
            )
            noise_case = compute_noise_detection_case(
                material=material,
                diameter_nm=diameter_nm,
                wavelength_nm=wavelength_nm,
                width_nm=width_nm,
                depth_nm=depth_nm,
                sim_cfg=candidate_cfg,
                optical_template=optical,
                n_events=int(candidate_cfg.n_events),
            )

        intf_summary = intf_case["summary"]
        noise_summary = noise_case["summary"]
        rows.append(
            {
                "rho": rho_value,
                "rho_candidate_roles": "|".join(roles),
                "rho_candidate_primary_role": roles[0],
                "rho_candidate_is_requested": "requested" in roles,
                "rho_candidate_is_lower": "rho_physical_envelope_lower" in roles,
                "rho_candidate_is_nominal": "rho_physical_envelope_nominal" in roles,
                "rho_candidate_is_upper": "rho_physical_envelope_upper" in roles,
                "A_ref": float(intf_summary.get("A_ref", np.nan)),
                "g_ref": float(intf_summary.get("g_ref", np.nan)),
                "peak_clean_signal": float(intf_summary.get("peak_clean_signal", np.nan)),
                "peak_cross_term": float(intf_summary.get("peak_cross_term", np.nan)),
                "peak_sca_only": float(intf_summary.get("peak_sca_only", np.nan)),
                "heterodyne_gain": float(intf_summary.get("heterodyne_gain", np.nan)),
                "detection_rate": float(noise_summary.get("detection_rate", np.nan)),
                "stable_detection_rate": float(
                    noise_summary.get("stable_detection_rate", np.nan)
                ),
                "mean_peak_margin_z": float(
                    noise_summary.get("mean_peak_margin_z", np.nan)
                ),
                "mean_local_snr": float(noise_summary.get("mean_local_snr", np.nan)),
                "phase_flip_fraction": float(
                    noise_summary.get("phase_flip_fraction", np.nan)
                ),
                "engineering_gate_passed": bool(
                    noise_summary.get("engineering_gate_passed", False)
                ),
                "engineering_gate_status_label": str(
                    noise_summary.get("engineering_gate_status_label", "unknown")
                ),
                "design_recommendation_status": str(
                    noise_summary.get("design_recommendation_status", "unknown")
                ),
                "design_recommendation_label": str(
                    noise_summary.get("design_recommendation_label", "unknown")
                ),
                "rho_physical_envelope_status": str(
                    noise_summary.get("rho_physical_envelope_status", "unavailable")
                ),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        summary = {
            "rho_requested": requested_rho,
            "rho_requested_envelope_status": "unavailable",
            "rho_physical_envelope_source": requested_reference.get(
                "rho_physical_envelope_source", "unavailable"
            ),
            "rho_physical_envelope_nominal": rho_nominal,
            "rho_physical_envelope_lower": rho_lower,
            "rho_physical_envelope_upper": rho_upper,
            "rho_sensitivity_candidate_count": 0,
            "rho_sensitivity_anchor_role": "requested",
            "rho_sensitivity_anchor_rho": requested_rho,
            "rho_sensitivity_report_random_seed": int(report_cfg.random_seed),
            "rho_sensitivity_report_random_seed_source": seed_source,
            "rho_sensitivity_max_abs_detection_rate_delta_vs_anchor": None,
            "rho_sensitivity_max_abs_stable_detection_rate_delta_vs_anchor": None,
            "rho_sensitivity_max_abs_peak_clean_rel_delta_vs_anchor": None,
            "rho_sensitivity_gate_change_count": 0,
            "rho_sensitivity_recommendation_change_count": 0,
        }
        summary.update(_classify_rho_sensitivity(summary))
        return df, summary

    anchor_mask = df["rho_candidate_is_nominal"].to_numpy(dtype=bool)
    if bool(anchor_mask.any()):
        anchor_row = df.loc[anchor_mask].iloc[0]
        anchor_role = "rho_physical_envelope_nominal"
    else:
        anchor_row = df.loc[df["rho_candidate_is_requested"]].iloc[0]
        anchor_role = "requested"

    anchor_peak_clean = max(abs(float(anchor_row["peak_clean_signal"])), 1e-12)
    anchor_detection_rate = float(anchor_row["detection_rate"])
    anchor_stable_rate = float(anchor_row["stable_detection_rate"])
    anchor_gate = bool(anchor_row["engineering_gate_passed"])
    anchor_recommendation = str(anchor_row["design_recommendation_status"])

    df["peak_clean_rel_delta_vs_anchor"] = (
        np.abs(df["peak_clean_signal"] - float(anchor_row["peak_clean_signal"]))
        / anchor_peak_clean
    )
    df["detection_rate_delta_vs_anchor"] = (
        df["detection_rate"] - anchor_detection_rate
    )
    df["stable_detection_rate_delta_vs_anchor"] = (
        df["stable_detection_rate"] - anchor_stable_rate
    )
    df["engineering_gate_changed_vs_anchor"] = (
        df["engineering_gate_passed"] != anchor_gate
    )
    df["design_recommendation_changed_vs_anchor"] = (
        df["design_recommendation_status"] != anchor_recommendation
    )

    requested_row = df.loc[df["rho_candidate_is_requested"]].iloc[0]
    summary = {
        "rho_requested": requested_rho,
        "rho_requested_envelope_status": str(
            requested_noise_summary.get("rho_physical_envelope_status", "unavailable")
        ),
        "rho_physical_envelope_source": requested_reference.get(
            "rho_physical_envelope_source", "unavailable"
        ),
        "rho_physical_envelope_nominal": (
            float(rho_nominal) if rho_nominal is not None else None
        ),
        "rho_physical_envelope_lower": (
            float(rho_lower) if rho_lower is not None else None
        ),
        "rho_physical_envelope_upper": (
            float(rho_upper) if rho_upper is not None else None
        ),
        "rho_sensitivity_candidate_count": int(len(df)),
        "rho_sensitivity_candidate_roles": df["rho_candidate_roles"].tolist(),
        "rho_sensitivity_anchor_role": anchor_role,
        "rho_sensitivity_anchor_rho": float(anchor_row["rho"]),
        "rho_sensitivity_report_random_seed": int(report_cfg.random_seed),
        "rho_sensitivity_report_random_seed_source": seed_source,
        "rho_sensitivity_requested_vs_anchor_detection_rate_delta": float(
            requested_row["detection_rate_delta_vs_anchor"]
        ),
        "rho_sensitivity_requested_vs_anchor_stable_detection_rate_delta": float(
            requested_row["stable_detection_rate_delta_vs_anchor"]
        ),
        "rho_sensitivity_requested_vs_anchor_peak_clean_rel_delta": float(
            requested_row["peak_clean_rel_delta_vs_anchor"]
        ),
        "rho_sensitivity_max_abs_detection_rate_delta_vs_anchor": float(
            np.max(np.abs(df["detection_rate_delta_vs_anchor"].to_numpy(dtype=float)))
        ),
        "rho_sensitivity_max_abs_stable_detection_rate_delta_vs_anchor": float(
            np.max(
                np.abs(df["stable_detection_rate_delta_vs_anchor"].to_numpy(dtype=float))
            )
        ),
        "rho_sensitivity_max_abs_peak_clean_rel_delta_vs_anchor": float(
            np.max(np.abs(df["peak_clean_rel_delta_vs_anchor"].to_numpy(dtype=float)))
        ),
        "rho_sensitivity_gate_change_count": int(
            df["engineering_gate_changed_vs_anchor"].sum()
        ),
        "rho_sensitivity_recommendation_change_count": int(
            df["design_recommendation_changed_vs_anchor"].sum()
        ),
    }
    summary.update(_classify_rho_sensitivity(summary))
    return df, summary


def build_single_case_stage_report(
    *,
    material: str,
    diameter_nm: int | float,
    wavelength_nm: int | float,
    width_nm: int | float,
    depth_nm: int | float,
    sim_cfg=None,
    optical_template=None,
    n_events: int = 12,
) -> dict[str, object]:
    """
    Build a sequential, stage-by-stage report for one concrete case.

    This is intentionally not a ranking report. It is a single-case explanatory
    report that follows the same physics chain used by the rest of the
    simulator:
        Mie -> collection -> reference -> trajectory/illumination ->
        scattering phase -> interference -> noise/readout -> batch judgement
    """
    report_cfg, report_seed_source = _resolve_report_sim_cfg(sim_cfg, n_events=n_events)
    base_inputs = build_case_inputs(
        material=material,
        diameter_nm=diameter_nm,
        wavelength_nm=wavelength_nm,
        width_nm=width_nm,
        depth_nm=depth_nm,
        sim_cfg=report_cfg,
        optical_template=optical_template,
    )
    interference_case = compute_interference_case(
        material=material,
        diameter_nm=diameter_nm,
        wavelength_nm=wavelength_nm,
        width_nm=width_nm,
        depth_nm=depth_nm,
        sim_cfg=report_cfg,
        optical_template=optical_template,
    )
    noise_case = compute_noise_detection_case(
        material=material,
        diameter_nm=diameter_nm,
        wavelength_nm=wavelength_nm,
        width_nm=width_nm,
        depth_nm=depth_nm,
        sim_cfg=report_cfg,
        optical_template=optical_template,
        n_events=n_events,
    )
    rho_probe_df, rho_probe_summary = build_rho_sensitivity_report(
        material=material,
        diameter_nm=diameter_nm,
        wavelength_nm=wavelength_nm,
        width_nm=width_nm,
        depth_nm=depth_nm,
        sim_cfg=report_cfg,
        optical_template=optical_template,
        n_events=n_events,
        requested_interference_case=interference_case,
        requested_noise_case=noise_case,
    )

    trace_df = interference_case["trace_df"]
    intf_summary = interference_case["summary"]
    noise_summary = noise_case["summary"]
    event_df = noise_case["event_df"]
    selected_event_index = 0
    if not event_df.empty and "detected" in event_df.columns and bool(event_df["detected"].any()):
        selected_event_index = int(event_df.loc[event_df["detected"], "event_index"].iloc[0])
    event_trace_df = build_event_trace_dataframe(noise_case, selected_event_index)

    size_parameter = float(base_inputs["intrinsic"]["size_parameter"])
    csca = float(base_inputs["intrinsic"]["Csca_m2"])
    e_sca_norm = float(base_inputs["E_sca_normalized"])
    a_ref = float(base_inputs["reference"]["A_ref"])
    heterodyne_gain = float(intf_summary.get("heterodyne_gain", np.nan))
    overlap_abs = float(intf_summary.get("interference_overlap_factor_abs", np.nan))
    detection_rate = float(noise_summary.get("detection_rate", 0.0))
    stable_rate = float(noise_summary.get("stable_detection_rate", 0.0))
    phase_flip_fraction = float(noise_summary.get("phase_flip_fraction", 0.0))
    gate_passed = bool(noise_summary.get("engineering_gate_passed", False))
    gate_reason = str(noise_summary.get("engineering_gate_reason", "N/A"))
    gate_failed_count = int(noise_summary.get("engineering_gate_failed_count", 0))
    observation_freeze_status = str(
        noise_summary.get("observation_freeze_status", "review_required_before_result_freeze")
    )

    _ensure_decision_fields(
        noise_summary,
        gate_passed=gate_passed,
        gate_reason=gate_reason,
        gate_failed_count=gate_failed_count,
        observation_freeze_status=observation_freeze_status,
    )

    recommendation_status = str(noise_summary.get("design_recommendation_status", "monitor_only"))
    recommendation_label = str(noise_summary.get("design_recommendation_label", "观察（暂不推荐）"))
    gate_label = str(
        noise_summary.get(
            "engineering_gate_status_label",
            "工程门槛通过" if gate_passed else "工程门槛未通过",
        )
    )

    freeze_label = FREEZE_LABELS.get(observation_freeze_status, observation_freeze_status)
    material_role_line = (
        "当前按最终 exosome 选型口径解释。"
        if str(material) == "exosome"
        else "当前更适合作为强散射体验证 case，不应直接替代 exosome 最终选型。"
    )

    if e_sca_norm > 0 and a_ref / max(e_sca_norm, 1e-12) > 3.0:
        reference_regime_line = "当前参考场显著强于散射场，仍处于更接近 heterodyne 放大的工作区。"
    elif e_sca_norm > 0 and a_ref / max(e_sca_norm, 1e-12) > 1.0:
        reference_regime_line = "当前参考场与散射场同量级，仍有干涉放大，但已经不算特别宽裕。"
    else:
        reference_regime_line = "当前参考场不再明显强于散射场，更应警惕信号提升只是来自粒子本身变强。"

    rho_sensitivity_line = str(
        rho_probe_summary.get(
            "rho_sensitivity_guidance",
            "当前还没有足够的 rho probe 结果，绝对 detection rate 仍应保守解释。",
        )
    )

    if np.isfinite(heterodyne_gain) and heterodyne_gain >= 3.0:
        interference_line = "clean peak 主要由交叉项驱动，说明当前放大更像健康的 heterodyne 干涉。"
    elif np.isfinite(heterodyne_gain) and heterodyne_gain >= 1.0:
        interference_line = "clean peak 同时受交叉项和本征散射项影响，已经进入混合区。"
    else:
        interference_line = "clean peak 不再由交叉项主导，更像本征散射项在抬头。"

    if detection_rate >= 0.5 and stable_rate >= 0.3:
        readout_line = "加噪与阈值之后仍保留了较稳定的检出，说明当前读出链没有把信号明显吃掉。"
    elif float(noise_summary.get("mean_nodi_bandwidth_limited_fraction", 0.0)) >= 0.5:
        readout_line = "当前读出链的主要风险是 transit-bandwidth 限制，而不只是阈值本身。"
    else:
        readout_line = "当前主要还是峰值余量不足或事件波动较大，读出链没有提供足够稳的检出余量。"

    decision_summary = build_case_decision_summary(
        design_recommendation_label=recommendation_label,
        design_recommendation_status=recommendation_status,
        design_recommendation_guidance=noise_summary.get("design_recommendation_guidance"),
        engineering_gate_passed=gate_passed,
        engineering_gate_status_label=gate_label,
        engineering_gate_primary_blocker_label=noise_summary.get(
            "engineering_gate_primary_blocker_label"
        ),
        engineering_gate_blocker_summary=noise_summary.get("engineering_gate_blocker_summary"),
        engineering_gate_guidance=noise_summary.get("engineering_gate_guidance"),
        observation_freeze_status=observation_freeze_status,
        observation_freeze_guidance=noise_summary.get("observation_freeze_guidance"),
    )

    human_headline = _resolve_human_headline(recommendation_status)

    human_badge = " | ".join(
        [recommendation_label, gate_label, freeze_label]
    )

    stages = [
        {
            "id": "input",
            "title": "Stage 0. 输入与当前假设",
            "priority": "primary",
            "priority_label": "主线",
            "principle": [
                "这一步只定义当前 case，而不做排名。",
                "当前模型直接使用的几何自由度是通道宽度 W 和通道深度 H。",
                "这里记录当前使用的是哪套主链默认假设。"
            ],
            "metrics": {
                "粒子": f"{material}_{int(round(float(diameter_nm)))}nm",
                "激光波长 (lambda)": f"{int(round(float(wavelength_nm)))} nm",
                "通道宽度 (W)": f"{int(round(float(width_nm)))} nm",
                "通道深度 (H)": f"{int(round(float(depth_nm)))} nm",
                "参考场模型": str(base_inputs['sim_cfg'].reference_model),
                "读出模型": str(base_inputs['sim_cfg'].readout_model),
            },
            "reading": _stage_reading(
                key="先确认当前 case 的材料、波长和 W/H 是否就是你想审查的对象。",
                judgment=material_role_line,
                caution="这一页不做全局最优筛选；如果输入 case 本身就不是目标对象，后面所有结论都会被带偏。",
            ),
            "conclusion": material_role_line,
        },
        {
            "id": "mie",
            "title": "Stage 1. 粒子与 Mie 本征散射",
            "priority": "primary",
            "priority_label": "主线",
            "principle": [
                "这一步只回答粒子本身会散射成什么样，还没有参考场和噪声。",
                "关键量是尺寸参数 x、本征散射截面 Csca、以及主投影通道的复场相位。"
            ],
            "metrics": {
                "尺寸参数 (x)": f"{size_parameter:.3f}",
                "本征散射截面 (Csca)": f"{csca:.3e} m²",
                "归一化散射场幅值 (E_sca,norm)": f"{e_sca_norm:.4f}",
                "材料散射相位 (phi_material)": f"{float(intf_summary.get('phi_sca_material_rad', 0.0)):.3f} rad",
            },
            "reading": _stage_reading(
                key="先看本征散射截面 (Csca) 和归一化散射场幅值 (E_sca,norm)，它们决定粒子本征上限，再看材料散射相位 (phi_material) 判断极性来源。",
                judgment=(
                    "当前 case 的本征散射底子已经不算弱。"
                    if csca > 1e-18
                    else "当前 case 的本征散射底子偏弱，后续必须靠参考场和读出链托住。"
                ),
                caution="如果这里只是很强，并不自动代表最终 detect 一定稳；后面仍可能被 overlap、阈值或带宽吃掉。",
            ),
            "conclusion": (
                "当前粒子本征散射已经不弱。"
                if csca > 1e-18
                else "当前粒子本征散射本身不强，后续更依赖参考场与读出链。"
            ),
        },
        {
            "id": "reference",
            "title": "Stage 3. 参考场",
            "priority": "primary",
            "priority_label": "主线",
            "principle": [
                "这一步回答参考场有多强，以及它是否仍处在物理上可接受的包络内。",
                "关键量是 A_ref、g_ref、rho 包络状态与窄通道 width saturation 状态。"
            ],
            "metrics": {
                "参考场幅值 (A_ref)": f"{a_ref:.4f}",
                "参考场几何缩放 (g_ref)": f"{float(intf_summary.get('g_ref', 0.0)):.4f}",
                "参考场包络状态 (rho status)": str(noise_summary.get("rho_physical_envelope_status", "unknown")),
                "窄通道饱和状态 (width saturation)": str(noise_summary.get("reference_width_saturation_status", "unknown")),
                "当前 rho / nominal rho": (
                    f"{float(rho_probe_summary.get('rho_requested', report_cfg.rho)):.3g} / "
                    f"{float(rho_probe_summary.get('rho_physical_envelope_nominal')):.3g}"
                    if rho_probe_summary.get("rho_physical_envelope_nominal") is not None
                    else f"{float(rho_probe_summary.get('rho_requested', report_cfg.rho)):.3g} / n/a"
                ),
                "rho probe 结论": str(
                    rho_probe_summary.get("rho_sensitivity_label", "包络不可用")
                ),
                "包络内检出率漂移": (
                    f"{float(rho_probe_summary.get('rho_sensitivity_max_abs_detection_rate_delta_vs_anchor', np.nan)):.1%}"
                    if rho_probe_summary.get(
                        "rho_sensitivity_max_abs_detection_rate_delta_vs_anchor"
                    )
                    is not None
                    else "n/a"
                ),
            },
            "reading": _stage_reading(
                key="先看参考场幅值 (A_ref) 和 rho / width saturation 状态，判断参考场是在健康放大区还是已经失真。",
                judgment=f"{reference_regime_line}{rho_sensitivity_line}",
                caution=(
                    "参考场幅值 (A_ref) 变大不一定是真变好；如果同时依赖异常 rho 或窄通道饱和，"
                    "就要把 rho probe 和 freeze 一起读，不能只看当前一个点。"
                ),
            ),
            "conclusion": f"{reference_regime_line}{rho_sensitivity_line}",
        },
        {
            "id": "interference",
            "title": "Stage 6. 干涉 clean signal",
            "priority": "primary",
            "priority_label": "主线",
            "principle": [
                "这一步把参考场与散射场合起来，回答 clean peak 为什么会变强。",
                "真正要看的是交叉项和 |E_sca|² 谁在主导，而不是只看峰值大小。"
            ],
            "metrics": {
                "clean 峰值 (peak clean)": f"{float(intf_summary.get('peak_clean_signal', 0.0)):.4e}",
                "干涉交叉项峰值 (peak cross-term)": f"{float(intf_summary.get('peak_cross_term', 0.0)):.4e}",
                "散射平方项峰值 (peak |E_sca|^2)": f"{float(intf_summary.get('peak_sca_only', 0.0)):.4e}",
                "干涉放大倍数 (heterodyne gain)": f"{heterodyne_gain:.3f}",
                "角谱重叠因子 (overlap)": f"{overlap_abs:.3f}",
            },
            "reading": _stage_reading(
                key="先看干涉交叉项峰值 (peak cross-term)、散射平方项峰值 (peak |E_sca|^2) 和干涉放大倍数 (heterodyne gain)，判断 clean peak 增强到底来自哪里。",
                judgment=interference_line,
                caution="如果 clean peak 变大主要靠散射平方项峰值 (peak |E_sca|^2) 抬头，而不是交叉项增强，就不能简单解读成参考放大更好了。",
            ),
            "conclusion": interference_line,
        },
        {
            "id": "readout",
            "title": "Stage 7. 噪声、读出与阈值",
            "priority": "primary",
            "priority_label": "主线",
            "principle": [
                "这一步回答 signal 在加噪、读出和阈值之后还能不能留下足够余量。",
                "重点不是 clean peak 本身，而是 threshold、local SNR 和 bandwidth 限制。"
            ],
            "metrics": {
                "平均检测阈值 (threshold)": f"{float(noise_summary.get('mean_threshold', 0.0)):.4e}",
                "平均局部信噪比 (local SNR)": f"{float(noise_summary.get('mean_local_snr', 0.0)):.3f}",
                "带宽保留系数 (bandwidth gain)": f"{float(noise_summary.get('mean_nodi_transit_bandwidth_gain', 0.0)):.3f}",
                "带宽受限占比 (bandwidth limited)": f"{float(noise_summary.get('mean_nodi_bandwidth_limited_fraction', 0.0)):.1%}",
            },
            "reading": _stage_reading(
                key="先同时看平均检测阈值 (threshold)、平均局部信噪比 (local SNR) 和带宽受限占比 (bandwidth limited)，而不是只看 clean peak。",
                judgment=readout_line,
                caution="如果检出变差，这里要先区分是检测阈值 (threshold) 吃掉了信号，还是 transit-bandwidth 在压低读出幅值。",
            ),
            "conclusion": readout_line,
        },
        {
            "id": "batch",
            "title": "Stage 8. 批量统计",
            "priority": "primary",
            "priority_label": "主线",
            "principle": [
                "单事件强不代表 batch 一定稳，因此这里必须同时看 detection、stable detection 和 phase flip。",
                "paired detection 只是在需要时补充判定，不替代主线物理理解。"
            ],
            "metrics": {
                "检出率 (detection rate)": f"{detection_rate:.1%}",
                "稳定检出率 (stable rate)": f"{stable_rate:.1%}",
                "相位翻转占比 (phase flip)": f"{phase_flip_fraction:.1%}",
                "双通道配对率 (paired rate)": f"{float(noise_summary.get('paired_channel_detection_rate', 0.0)):.1%}",
                "平均峰高 (mean peak)": f"{float(noise_summary.get('mean_peak_height', 0.0)):.3e}",
            },
            "reading": _stage_reading(
                key="先看检出率 (detection rate)、稳定检出率 (stable rate) 和相位翻转占比 (phase flip)，这三项比单个最强事件更能代表能不能稳定工作。",
                judgment=(
                    "当前 batch 层已经出现了可用检出。"
                    if detection_rate >= 0.3
                    else "当前 batch 层仍然偏弱，说明问题不是单事件巧合能解决的。"
                ),
                caution="如果单事件看起来很好，但 batch rate 还是低，那说明系统还不够稳，不能直接作为设计结论。",
            ),
            "conclusion": (
                "当前 batch 层已经具备可用检出。"
                if detection_rate >= 0.3
                else "当前 batch 层检出仍偏弱，后续工程判断会主要受 detection / stable rate 拖累。"
            ),
        },
        {
            "id": "decision",
            "title": "Stage 9. 工程解释与最终结论",
            "priority": "primary",
            "priority_label": "主线",
            "principle": [
                "最后一段不是重新算物理，而是把 physics、readout、freeze 和 gate 汇总成工程判断。",
                "这一步回答的是“当前 case 适合作为最终候选、验证 case，还是边界 case”。"
            ],
            "metrics": {
                "设计推荐标签 (recommendation)": str(recommendation_label),
                "工程门槛状态 (gate)": str(gate_label),
                "主要卡点 (blocker)": str(noise_summary.get("engineering_gate_primary_blocker_label", "已通过")),
                "结果冻结状态 (freeze)": freeze_label,
            },
            "reading": _stage_reading(
                key="最后同时看 recommendation、gate blocker 和 freeze，它们决定这个 case 是不是值得继续信。",
                judgment=str(decision_summary["decision_summary_primary_message"]),
                caution="即使数值看上去不差，只要 freeze 还是 caution，解释层也应该保留复核意识，不直接当成最终最优点。",
            ),
            "conclusion": (
                f"{human_headline}；"
                f"{decision_summary['decision_summary_primary_message']}"
            ),
        },
    ]

    return {
        "meta": {
            "material": material,
            "diameter_nm": int(round(float(diameter_nm))),
            "wavelength_nm": int(round(float(wavelength_nm))),
            "width_nm": int(round(float(width_nm))),
            "depth_nm": int(round(float(depth_nm))),
            "n_events": int(n_events),
        },
        "headline": {
            "tone": str(decision_summary["decision_summary_tone"]),
            "headline": human_headline,
            "badge": human_badge,
            "primary_message": str(decision_summary["decision_summary_primary_message"]),
            "next_step": str(decision_summary["decision_summary_next_step"]),
        },
        "diagnostics": {
            "report_random_seed": int(report_cfg.random_seed),
            "report_random_seed_source": report_seed_source,
        },
        "stages": stages,
        "interference_case": interference_case,
        "noise_case": noise_case,
        "rho_sensitivity_df": rho_probe_df,
        "rho_sensitivity_summary": rho_probe_summary,
        "interference_trace_df": trace_df,
        "event_table_df": event_df,
        "event_trace_df": event_trace_df,
        "selected_event_index": int(selected_event_index),
    }


def build_detection_scan_dataframe(
    *,
    scan_variable: str,
    scan_values: list[float] | np.ndarray,
    material: str,
    diameter_nm: int | float,
    wavelength_nm: int | float,
    width_nm: int | float,
    depth_nm: int | float,
    sim_cfg=None,
    optical_template=None,
    n_events: int = 12,
) -> pd.DataFrame:
    """Build a compact detection scan over noise / threshold / velocity."""
    rows: list[dict[str, object]] = []
    for value in scan_values:
        sim_cfg_case = deepcopy(sim_cfg or DEFAULT_SIM_CFG)
        if scan_variable == "noise_std":
            sim_cfg_case.noise_std = float(value)
        elif scan_variable == "threshold_sigma":
            sim_cfg_case.threshold_sigma = float(value)
        elif scan_variable == "velocity_mm_s":
            sim_cfg_case.mean_flow_velocity_m_s = float(value) * 1e-3
        else:
            raise ValueError(f"Unsupported detection scan variable: {scan_variable}")

        try:
            case = compute_noise_detection_case(
                material=material,
                diameter_nm=diameter_nm,
                wavelength_nm=wavelength_nm,
                width_nm=width_nm,
                depth_nm=depth_nm,
                sim_cfg=sim_cfg_case,
                optical_template=optical_template,
                n_events=n_events,
            )
            summary = case["summary"]
            rows.append(
                {
                    scan_variable: float(value),
                    "valid": True,
                    "detection_rate": float(summary["detection_rate"]),
                    "single_channel_detection_rate": float(
                        summary.get("single_channel_detection_rate", summary["detection_rate"])
                    ),
                    "paired_channel_detection_rate": float(
                        summary.get("paired_channel_detection_rate", 0.0)
                    ),
                    "mean_peak_height": float(summary["mean_peak_height"]),
                    "CV": (
                        float(summary["std_peak_height"] / summary["mean_peak_height"])
                        if summary["mean_peak_height"] > 0
                        else np.nan
                    ),
                    "mean_threshold": float(summary["mean_threshold"]),
                }
            )
        except ValueError as exc:
            rows.append(
                {
                    scan_variable: float(value),
                    "valid": False,
                    "detection_rate": np.nan,
                    "mean_peak_height": np.nan,
                    "CV": np.nan,
                    "mean_threshold": np.nan,
                    "error": str(exc),
                }
            )

    return pd.DataFrame(rows)
