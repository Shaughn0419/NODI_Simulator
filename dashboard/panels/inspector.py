"""
dashboard/panels/inspector.py — Case Inspector 页面

剖析单个 case：摘要卡片 + 物理分解 + 直方图 + 按需重算 trace
科研展示优先围绕标准结果库；工程调试重算只保留为验证口径
"""

import os

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from nodi_simulator.dashboard.backend import (
    get_case_summary,
    build_physics_breakdown,
    is_standard_dashboard_dataset_prefix,
    load_dashboard_data_bundle,
    run_case_on_demand,
)
from nodi_simulator.dashboard.config import (
    get_score_explanation,
    infer_particle_material, infer_particle_diameter_nm, format_particle_label,
)
from nodi_simulator.dashboard.panels.common import (
    format_case_verdict_caption,
    get_active_data_source_tag,
    render_page_header_hub,
)

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "results",
)


def _coerce_float(value: object) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _build_case_trend_notes(score_info: dict, outcome: dict) -> list[str]:
    lines: list[str] = []

    stable_rate = outcome.get("stable_detection_rate")
    robust_cv = outcome.get("robust_cv_peak_height")
    z_margin = outcome.get("mean_peak_margin_z")
    ratio = float(score_info.get("E_sca_E_ref_ratio", np.nan))
    dominant_factor = str(score_info.get("dominant_factor", "balanced"))

    if stable_rate is not None:
        stable_rate = float(stable_rate)
        if stable_rate >= 0.7:
            lines.append("趋势判断：当前点的稳定检出率已经不低，说明这不是靠少数幸运事件撑起来的高分。")
        elif stable_rate <= 0.3:
            lines.append("趋势判断：当前点的稳定检出率偏低，说明平均分数即使不差，也更像边缘事件在勉强托底。")
        else:
            lines.append("趋势判断：当前点仍在过渡区，后续更应该看分布宽度和单事件 trace，而不是只看均值。")

    if robust_cv is not None and np.isfinite(robust_cv):
        robust_cv = float(robust_cv)
        if robust_cv <= 0.35:
            lines.append("什么算更可信：稳健 CV 越低越好；当前波动不算大，说明参数稍微扰动时结果更可能保持住。")
        elif robust_cv >= 0.70:
            lines.append("什么算更可信：稳健 CV 现在偏高，说明这个点对位置、扩散或噪声更敏感，不能只看高分本身。")

    if z_margin is not None:
        z_margin = float(z_margin)
        if z_margin >= 1.0:
            lines.append("检测余量：当前峰高 z-margin 已经拉开，趋势上更像‘阈值上方的稳定点’，而不是刚刚压线。")
        elif z_margin <= 0.2:
            lines.append("检测余量：当前峰高 z-margin 仍然很薄，后面最该警惕的是阈值、噪声或相位波动把它重新压回边缘。")

    if np.isfinite(ratio):
        if dominant_factor == "reference" and ratio < 0.05:
            lines.append("机制解释：当前更像 reference 放大在主导，高分可以成立，但解读时要更重视 freeze 与可信度边界。")
        elif dominant_factor == "scattering" and ratio >= 0.10:
            lines.append("机制解释：当前更像粒子本征散射已经足够强，趋势上通常比“全靠参考场撑起来”更直接、更稳。")
        else:
            lines.append("机制解释：当前点处在散射、reference 或耦合共同作用区，最好把机制和统计稳定性一起看。")

    return lines[:4]


def _build_inspector_verdict_frame(case: dict, score_info: dict) -> tuple[str, str, str]:
    gate_passed = bool(case.get("engineering_gate_passed"))
    trust_level = str(score_info.get("trust_level", "medium"))
    dominant_factor = str(score_info.get("dominant_factor", "balanced"))

    if gate_passed and trust_level == "high":
        better = "更值得信：工程门槛已过，而且可信度高，这种点更适合拿来当默认候选。"
    elif gate_passed:
        better = "更值得信：虽然门槛已过，但还要看 reference 依赖和波动宽度；只有这些也稳，才算真正可靠。"
    else:
        better = "更值得信：先把门槛卡点解决，再谈是不是推荐设计。当前更适合把它当边界点来诊断。"

    if dominant_factor == "reference":
        fake = "假好点：分数不低，但主要靠 reference 放大撑住，同时统计稳定性并没有跟上。"
    elif dominant_factor == "scattering":
        fake = "假好点：只看本征散射很强，却忽略检出率、CV 或 gate 仍然不够稳。"
    else:
        fake = "假好点：多个因素都在推高分数，但没有哪一条证据链足够稳，容易出现‘均值好看、单事件吃力’。"

    trust = "先信 verdict、稳定检出率、稳健 CV 和峰高 z-margin 这四项，再回头看机制解释为什么成立。"
    return better, fake, trust


def render_inspector():
    """Render the Case Inspector page."""
    st.header("Case Inspector — 看成因、看波动、看单事件")
    st.caption("这是整个链路的最终复盘页：回答“为什么这个点分高/分低”，以及“它在单事件层面到底是不是好测”。")
    render_page_header_hub()

    particle = st.session_state.get("selected_particle")
    wavelength = st.session_state.get("selected_wavelength_nm")
    sel_W = st.session_state.get("selected_W_nm")
    sel_H = st.session_state.get("selected_H_nm")

    if any(v is None for v in [particle, wavelength, sel_W, sel_H]):
        st.info("请先在 Design Explorer 页面选择一个参数点。建议先在热图里找平台型高分区，再回来这里看成因和单事件可检测性。")
        st.caption("当前页不再提供跨页跳转按钮；请直接用侧边栏切到 Design Explorer 先选候选点。")
        return
    wavelength_value = _coerce_float(wavelength)
    if wavelength_value is None:
        st.error(f"当前波长值异常：{wavelength}")
        return
    wavelength_int = int(wavelength_value)

    try:
        data_bundle = load_dashboard_data_bundle(
            RESULTS_DIR,
            st.session_state,
            include_compact=True,
        )
    except (FileNotFoundError, ValueError) as error:
        st.error(str(error))
        return
    source = data_bundle.source
    standard_workflow_active = (
        not source.is_live
        and is_standard_dashboard_dataset_prefix(source.prefix)
    )

    # ==== Live parameter summary ====
    if source.is_live:
        cfg = st.session_state.live_sim_cfg
        st.warning(
            f"当前查看的是工程调试重算数据 [{st.session_state.live_tag}]，不属于科研展示默认结果库。"
        )
        st.caption(
            f"调试摘要：ρ={cfg.rho}  α={cfg.ref_alpha}  β={cfg.ref_beta}  γ={cfg.ref_gamma}  |  "
            f"噪声={cfg.noise_std}  参考场={cfg.reference_model}  "
            f"耦合={cfg.coupling_model}"
        )
    elif standard_workflow_active:
        st.success("当前查看的是标准 biomimetic full-range 主结果库中的单个 case。")
    else:
        st.warning(f"当前查看的是 `{st.session_state.data_prefix}`，不是标准 biomimetic full-range 主结果库。")

    compact = data_bundle.compact or []
    health_report = data_bundle.health_report

    case = get_case_summary(compact, particle, wavelength, sel_W, sel_H)
    if case is None:
        st.warning(f"未找到: {particle}, λ={wavelength}nm, W={sel_W}nm, H={sel_H}nm")
        return

    particle_label = format_particle_label(
        case.get("particle_material", infer_particle_material(particle)),
        case.get("particle_diameter_nm", infer_particle_diameter_nm(particle)),
    )

    # ==== Summary cards ====
    st.subheader(f"{particle_label}, λ={wavelength}nm, W={sel_W}nm, H={sel_H}nm")
    st.caption(source.summary_caption)
    summary = case["summary"]
    cols = st.columns(7)
    cols[0].metric("评分", f"{case['score']:.3f}")
    cols[1].metric(
        "最终工程评分",
        f"{case.get('final_engineering_score', case.get('engineering_score', 0.0)):.3f}",
    )
    cols[2].metric(
        "工程评分",
        f"{case.get('engineering_score', 0.0):.3f}",
    )
    cols[3].metric("检出率", f"{summary['detection_rate']:.0%}")
    cols[4].metric(
        "稳定检出率",
        f"{summary.get('stable_detection_rate', 0.0):.0%}",
    )
    if any(
        case.get(key) is not None
        for key in ["design_recommendation_label", "engineering_gate_status_label", "observation_freeze_status"]
    ):
        st.caption(format_case_verdict_caption(case))
    if isinstance(case.get("engineering_gate_blocker_summary"), str):
        st.caption(
            "Gate 解释："
            f"{case.get('engineering_gate_blocker_summary')} | "
            f"{case.get('engineering_gate_guidance', 'N/A')}"
        )
    wavelength_rows = []
    material_rows = []
    if health_report:
        monitoring = health_report.get("monitoring_summary", {})
        st.caption(
            "当前结果库健康："
            f"ready={monitoring.get('default_ready_fraction', 0.0):.1%} | "
            f"shared-beam caution={monitoring.get('shared_beam_caution_fraction', 0.0):.1%} | "
            f"rho 包络外={monitoring.get('rho_out_of_envelope_count', 0)}"
        )
        health_slices = health_report.get("health_slices", {})
        wavelength_rows = health_slices.get("by_wavelength_nm", [])
        material_rows = health_slices.get("by_particle_material", [])
    wavelength_row = next(
        (
            row for row in wavelength_rows
            if (row_wavelength := _coerce_float(row.get("wavelength_nm", -1))) is not None
            and int(round(row_wavelength)) == wavelength_int
        ),
        None,
    )
    material_name = case.get("particle_material", infer_particle_material(particle))
    material_row = next(
        (
            row for row in material_rows
            if str(row.get("particle_material", "")) == str(material_name)
        ),
        None,
    )
    subgroup_bits = []
    if wavelength_row:
        default_ready_fraction = _coerce_float(wavelength_row.get("default_ready_fraction"))
        gate_pass_fraction = _coerce_float(wavelength_row.get("engineering_gate_pass_fraction"))
        if default_ready_fraction is not None and gate_pass_fraction is not None:
            subgroup_bits.append(
                f"波长 {wavelength_int}nm: ready={default_ready_fraction:.1%}, "
                f"gate通过={gate_pass_fraction:.1%}"
            )
    if material_row:
        mat_ready_fraction = _coerce_float(material_row.get("default_ready_fraction"))
        shared_beam_caution_fraction = _coerce_float(material_row.get("shared_beam_caution_fraction"))
        if mat_ready_fraction is not None and shared_beam_caution_fraction is not None:
            subgroup_bits.append(
                f"材料 {material_name}: ready={mat_ready_fraction:.1%}, "
                f"shared-beam caution={shared_beam_caution_fraction:.1%}"
            )
    if subgroup_bits:
        st.caption("当前子组健康：" + " | ".join(subgroup_bits))

    # ==== Score auto-explanation + Trust indicator ====
    score_info = get_score_explanation(case)
    breakdown = build_physics_breakdown(case)
    phys = breakdown["case_physics"]
    outcome = breakdown["batch_outcome"]
    phys_rows = []
    for k, v in phys.items():
        if v is None:
            phys_rows.append({"量": k, "值": "N/A"})
        elif isinstance(v, float) and abs(v) < 0.01:
            phys_rows.append({"量": k, "值": f"{v:.4e}"})
        elif isinstance(v, float):
            phys_rows.append({"量": k, "值": f"{v:.4f}"})
        else:
            phys_rows.append({"量": k, "值": str(v)})

    factor_labels = {
        "scattering": "散射主导",
        "reference": "参考场主导",
        "coupling": "耦合主导",
        "balanced": "均衡",
    }
    phys_rows.append({
        "量": "散射场/参考场比值 (E_sca / E_ref)",
        "值": f"{score_info['E_sca_E_ref_ratio']:.4f}",
    })
    phys_rows.append({
        "量": "信号主导因素",
        "值": factor_labels.get(score_info["dominant_factor"], "—"),
    })

    trust_labels = {"high": "高", "medium": "中", "low": "低"}
    trust_label = trust_labels[score_info["trust_level"]]
    st.subheader("Verdict")
    if bool(case.get("engineering_gate_passed")) and score_info["trust_level"] == "high":
        st.success("当前 case 同时满足工程门槛且可信度较高，可以把下面证据当作“为什么它值得优先考虑”的主证据链。")
    elif bool(case.get("engineering_gate_passed")):
        st.warning("当前 case 已过工程门槛，但可信度还不是最高；这里最该先看 reference 依赖、波动宽度和单事件 trace。")
    else:
        st.error("当前 case 还没有过工程门槛。这里先回答它卡在哪里，以及它是‘真差点’还是‘假好点’。")
    st.caption(f"{format_case_verdict_caption(case)} | 可信度={trust_label}")
    st.info(score_info["explanation"])
    st.caption(score_info["trust_reason"])
    st.caption(f"散射场/参考场比值 (E_sca / E_ref) = {score_info['E_sca_E_ref_ratio']:.4f}")
    better_line, fake_line, trust_line = _build_inspector_verdict_frame(case, score_info)
    frame_cols = st.columns(3)
    frame_cols[0].markdown("**什么样的点更值得信**")
    frame_cols[0].caption(better_line)
    frame_cols[1].markdown("**什么样的点是假好点**")
    frame_cols[1].caption(fake_line)
    frame_cols[2].markdown("**先信什么证据**")
    frame_cols[2].caption(trust_line)

    quick_cols = st.columns(3)
    quick_cols[0].metric(
        "稳定检出率",
        f"{outcome['stable_detection_rate']:.0%}"
        if outcome.get("stable_detection_rate") is not None
        else "N/A",
    )
    quick_cols[1].metric(
        "稳健 CV",
        (
            f"{outcome['robust_cv_peak_height']:.3f}"
            if outcome.get("robust_cv_peak_height") is not None
            and np.isfinite(outcome["robust_cv_peak_height"])
            else "N/A"
        ),
    )
    quick_cols[2].metric(
        "峰高 z-margin",
        f"{outcome['mean_peak_margin_z']:.2f}"
        if outcome.get("mean_peak_margin_z") is not None
        else "N/A",
    )
    for note in _build_case_trend_notes(score_info, outcome):
        st.caption(note)

    required_detected = outcome.get("engineering_gate_required_detected_events")
    n_detected_val = int(outcome.get("n_detected") or outcome.get("n_peaks_detected") or 0)
    det_frac_lb = outcome.get("engineering_gate_detected_fraction_lb")
    stable_lb = outcome.get("engineering_gate_stable_detection_rate_lb")
    phase_flip_ub = outcome.get("engineering_gate_phase_flip_fraction_ub")
    margin_z = outcome.get("engineering_gate_mean_peak_margin_z")
    strict_lb = outcome.get("engineering_gate_strict_paired_rate_lb")
    strict_req = outcome.get("engineering_gate_required_strict_paired_detection_rate", 0.0) or 0.0

    def _pass_icon(cond: bool) -> str:
        return "OK" if cond else "NO"

    gate_rows = []
    if required_detected is not None:
        gate_rows.append({"条件": "最小检出事件数", "要求": f"≥ {required_detected}", "当前值": str(n_detected_val), "通过": _pass_icon(n_detected_val >= required_detected)})
    if det_frac_lb is not None:
        gate_rows.append({"条件": "检出率 Wilson LB", "要求": "≥ 10%", "当前值": f"{float(det_frac_lb):.1%}", "通过": _pass_icon(float(det_frac_lb) >= 0.10)})
    if stable_lb is not None:
        gate_rows.append({"条件": "稳定检出率 Wilson LB", "要求": "≥ 20%", "当前值": f"{float(stable_lb):.1%}", "通过": _pass_icon(float(stable_lb) >= 0.20)})
    if phase_flip_ub is not None:
        gate_rows.append({"条件": "相位翻转占比 Wilson UB", "要求": "≤ 50%", "当前值": f"{float(phase_flip_ub):.1%}", "通过": _pass_icon(float(phase_flip_ub) <= 0.50)})
    if margin_z is not None:
        gate_rows.append({"条件": "峰高 z-margin (均值)", "要求": "≥ 0.5", "当前值": f"{float(margin_z):.3f}", "通过": _pass_icon(float(margin_z) >= 0.50)})
    if strict_req > 0 and strict_lb is not None:
        gate_rows.append({"条件": "strict 双通道检出率 Wilson LB", "要求": f"≥ {strict_req:.1%}", "当前值": f"{float(strict_lb):.1%}", "通过": _pass_icon(float(strict_lb) >= strict_req)})
    if gate_rows:
        st.dataframe(pd.DataFrame(gate_rows), width="stretch", hide_index=True)

    st.subheader("机制与统计")
    col_phys, col_hist = st.columns(2)
    with col_phys:
        quick_cols = st.columns(3)
        quick_cols[0].metric("散射截面 (Csca)", f"{phys.get('Csca_m2', 0.0):.3e}" if phys.get("Csca_m2") is not None else "N/A")
        quick_cols[1].metric("散射场/参考场比值 (E_sca/E_ref)", f"{score_info['E_sca_E_ref_ratio']:.4f}")
        quick_cols[2].metric("主导因素", factor_labels.get(score_info["dominant_factor"], "—"))
        extra_cols = st.columns(4)
        extra_cols[0].metric("固定误报率命中率", f"{outcome['hit_rate_at_fixed_false_alarm']:.0%}" if outcome.get("hit_rate_at_fixed_false_alarm") is not None else "N/A")
        extra_cols[1].metric("ROC-AUC", f"{outcome['roc_auc_event_vs_background']:.3f}" if outcome.get("roc_auc_event_vs_background") is not None else "N/A")
        extra_cols[2].metric("局部 SNR", f"{outcome['mean_local_snr']:.2f}" if outcome.get("mean_local_snr") is not None else "N/A")
        extra_cols[3].metric("双通道配对率", f"{outcome['paired_detection_rate']:.0%}" if outcome.get("paired_detection_rate") is not None else "N/A")
        st.dataframe(pd.DataFrame(phys_rows), width="stretch", hide_index=True)

    with col_hist:
        heights = summary.get("all_heights", [])
        widths = summary.get("all_widths", [])
        if heights:
            st.markdown("**峰高分布**")
            fig_h = go.Figure(go.Histogram(x=heights, nbinsx=20, marker_color="steelblue"))
            fig_h.update_layout(xaxis_title="峰高", yaxis_title="数量", height=250, margin={"t": 10})
            st.plotly_chart(fig_h, width="stretch")
        if widths:
            st.markdown("**峰宽分布**")
            fig_w = go.Figure(go.Histogram(x=[w * 1e3 for w in widths], nbinsx=20, marker_color="coral"))
            fig_w.update_layout(xaxis_title="峰宽 (ms)", yaxis_title="数量", height=250, margin={"t": 10})
            st.plotly_chart(fig_w, width="stretch")

    st.subheader("单事件 Trace")
    data_tag = get_active_data_source_tag()
    cache_key = (particle, wavelength, sel_W, sel_H, data_tag)
    detail_button_label = (
        "重算此 Case 详情（工程调试口径）"
        if source.is_live
        else "重算此 Case 详情（当前结果库口径）"
    )
    if st.button(detail_button_label, key="recompute_btn"):
        with st.spinner("正在运行模拟..."):
            detail = run_case_on_demand(particle, wavelength, sel_W, sel_H)
            st.session_state.case_cache[cache_key] = detail

    detail = st.session_state.case_cache.get(cache_key)
    if detail is None:
        st.info("点击上方按钮可按当前结果库口径重算 detail trace。")
        return

    st.caption(f"📌 Detail 来源：{source.detail_caption}")
    events = detail["events"]
    idx = st.slider("事件索引", 0, len(events) - 1, 0, key="event_slider")
    evt = events[idx]
    t_ms = evt["trajectory"]["time_s"] * 1e3
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t_ms, y=evt["signal_trace"], mode="lines", name="干净信号 (clean signal)", line={"color": "blue"}))
    fig.add_trace(go.Scatter(x=t_ms, y=evt["signal_noisy"], mode="lines", name="加噪读出 (noisy signal)", line={"color": "gray", "width": 0.5}, opacity=0.6))
    fig.add_hline(y=evt["threshold"], line_dash="dash", line_color="red", annotation_text=f"检测阈值 (threshold)={evt['threshold']:.4f}")
    fig.update_layout(
        xaxis_title="时间 (ms)",
        yaxis_title="信号 (a.u.)",
        title=(f"事件 {idx}: x₀={evt['initial_position'][0]*1e9:.0f}nm, z₀={evt['initial_position'][1]*1e9:.0f}nm"),
        height=350,
    )
    st.plotly_chart(fig, width="stretch")

    det = evt["features"]["n_peaks"] > 0
    event_cols = st.columns(6)
    event_cols[0].metric("是否检出", "是" if det else "否")
    if det:
        best_evt = max(evt["features"]["peaks"], key=lambda p: p["peak_height"])
        event_cols[1].metric("最高峰高", f"{best_evt['peak_height']:.3e}")
        event_cols[2].metric("峰宽", f"{best_evt['peak_width_s'] * 1e3:.1f} ms")
    else:
        event_cols[1].metric("最高峰高", "N/A")
        event_cols[2].metric("峰宽", "N/A")
    event_cols[3].metric("检测阈值", f"{evt['threshold']:.4f}")
    local_ref = np.asarray(evt.get("A_ref_trace", []), dtype=float)
    local_delta_phi = np.asarray(evt.get("delta_phi_ref_rad", []), dtype=float)
    event_cols[4].metric("局部参考场幅值 (A_ref)", f"{np.max(local_ref):.3e}" if local_ref.size > 0 else "N/A")
    event_cols[5].metric("参考相位差范围 (Δφ_ref)", f"{np.ptp(local_delta_phi):.2f} rad" if local_delta_phi.size > 0 else "N/A")

    rows = []
    for i, e in enumerate(events):
        hit = e["features"]["n_peaks"] > 0
        h, w = 0, 0
        if hit:
            best = max(e["features"]["peaks"], key=lambda p: p["peak_height"])
            h, w = best["peak_height"], best["peak_width_s"] * 1e3
        rows.append({
            "idx": i,
            "x₀(nm)": f"{e['initial_position'][0]*1e9:.0f}",
            "z₀(nm)": f"{e['initial_position'][1]*1e9:.0f}",
            "det": "✓" if hit else "✗",
            "height": f"{h:.3e}" if hit else "-",
            "width(ms)": f"{w:.1f}" if hit else "-",
        })
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True, height=260)
