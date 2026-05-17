"""
dashboard/panels/interference_explorer.py — Interference Explorer page

Bridges intrinsic Mie scattering to the clean interferometric signal.
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from nodi_simulator.dashboard.config import (
    DASHBOARD_DIAMETER_STEP_NM,
    DIAMETER_RANGE_NM,
    FULL_SWEEP_WAVELENGTHS_NM,
    MATERIAL_OPTIONS,
    MATERIAL_PHYSICS_LABELS,
    REFERENCE_MODEL_OPTIONS,
    format_particle_label,
)
from nodi_simulator.dashboard.backend import (
    load_workflow_case_anchor,
)
from nodi_simulator.dashboard.panels.common import (
    render_page_header_hub,
    render_workflow_case_source_panel,
    resolve_active_system_defaults,
    resolve_shared_case_parameter_defaults,
)
from nodi_simulator.dashboard.signal_backend import (
    build_interference_scan_dataframe,
    compute_interference_case,
)


WAVELENGTH_OPTIONS_NM = list(FULL_SWEEP_WAVELENGTHS_NM)
GEOMETRY_RANGE_NM = (500, 2000)
RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "results",
)


def _resolve_defaults() -> dict[str, object]:
    defaults, sim_cfg, optical = resolve_shared_case_parameter_defaults()
    return {
        **defaults,
        "rho": float(sim_cfg.rho),
        "pulse_detection_mode": sim_cfg.pulse_detection_mode,
        "collection_integration_mode": sim_cfg.collection_integration_mode,
        "collection_sigma_deg": float(np.degrees(sim_cfg.collection_sigma_rad)),
        "scattering_projection_mode": sim_cfg.scattering_projection_mode,
        "reference_model": sim_cfg.reference_model,
        "ref_alpha": float(sim_cfg.ref_alpha),
        "ref_beta": float(sim_cfg.ref_beta),
        "ref_gamma": float(sim_cfg.ref_gamma),
        "coupling_model": sim_cfg.coupling_model,
        "beam_waist_y_nm": int(round(float(optical.beam_waist_y_m * 1e9))),
        "velocity_mm_s": float(sim_cfg.mean_flow_velocity_m_s * 1e3),
        "normalization_mode": sim_cfg.normalization_mode,
    }


def _apply_defaults(force: bool = False) -> dict[str, object]:
    defaults = _resolve_defaults()
    key_defaults = {
        "intf_material": defaults["material"],
        "intf_diameter_nm": defaults["diameter_nm"],
        "intf_wavelength_nm": defaults["wavelength_nm"],
        "intf_width_nm": defaults["width_nm"],
        "intf_depth_nm": defaults["depth_nm"],
        "intf_rho": defaults["rho"],
        "intf_reference_model": defaults["reference_model"],
        "intf_ref_alpha": defaults["ref_alpha"],
        "intf_ref_beta": defaults["ref_beta"],
        "intf_ref_gamma": defaults["ref_gamma"],
        "intf_coupling_model": defaults["coupling_model"],
        "intf_beam_waist_y_nm": defaults["beam_waist_y_nm"],
        "intf_x_fraction": 0.0,
        "intf_z_fraction": 0.0,
        "intf_scan_variable": "rho",
    }
    for key, value in key_defaults.items():
        if force or key not in st.session_state:
            st.session_state[key] = value
    return defaults


def _build_trace_figure(trace_df) -> go.Figure:
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.10,
        subplot_titles=("场包络 / 散射场", "Clean signal 分解"),
    )
    fig.add_trace(
        go.Scatter(x=trace_df["time_ms"], y=trace_df["A_env"], name="A_env"),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=trace_df["time_ms"], y=trace_df["A_sca"], name="A_sca(t)"),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=trace_df["time_ms"], y=trace_df["cross_term"], name="2Re(E_ref·E_sca*)"),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=trace_df["time_ms"], y=trace_df["sca_only_term"], name="|E_sca|^2"),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=trace_df["time_ms"], y=trace_df["clean_signal"], name="clean signal"),
        row=2,
        col=1,
    )
    fig.update_layout(height=620, xaxis2_title="时间 (ms)")
    fig.update_yaxes(title_text="幅值", row=1, col=1)
    fig.update_yaxes(title_text="信号 (a.u.)", row=2, col=1)
    return fig


def _build_peak_figure(summary: dict[str, float]) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=["Peak composition"],
            y=[summary["peak_cross_term"]],
            name="干涉交叉项",
        )
    )
    fig.add_trace(
        go.Bar(
            x=["Peak composition"],
            y=[summary["peak_sca_only"]],
            name="纯散射项",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=["Peak composition"],
            y=[summary["peak_clean_signal"]],
            mode="markers+text",
            name="总 clean 峰值",
            text=[f"{summary['peak_clean_signal']:.3e}"],
            textposition="top center",
        )
    )
    fig.update_layout(
        barmode="stack",
        height=360,
        yaxis_title="信号贡献 (a.u.)",
        title="脉冲峰值处的组成分解",
    )
    return fig


def _build_scan_figure(df, scan_variable: str) -> go.Figure:
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.10,
        subplot_titles=("参考场 / 散射场相关量", "Clean signal 输出"),
    )
    x = df[scan_variable]
    fig.add_trace(go.Scatter(x=x, y=df["A_ref"], mode="lines+markers", name="A_ref"), row=1, col=1)
    fig.add_trace(
        go.Scatter(x=x, y=df["E_sca_normalized"], mode="lines+markers", name="E_sca 归一化幅值"),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=x, y=df["peak_clean_signal"], mode="lines+markers", name="clean 峰值"),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=x, y=df["heterodyne_gain"], mode="lines+markers", name="异频增益"),
        row=2,
        col=1,
    )

    axis_titles = {
        "rho": "rho",
        "width_nm": "通道宽度 W (nm)",
        "depth_nm": "通道深度 H (nm)",
        "wavelength_nm": "波长 (nm)",
    }
    fig.update_layout(height=600)
    fig.update_yaxes(title_text="幅值 / 归一化场", row=1, col=1)
    fig.update_yaxes(title_text="信号 / 增益", row=2, col=1)
    fig.update_xaxes(title_text=axis_titles.get(scan_variable, scan_variable), row=2, col=1)
    return fig


def _build_interference_scan_notes(df: pd.DataFrame, scan_variable: str) -> list[str]:
    if df.empty or len(df) < 2:
        return ["当前扫描点太少，还不足以判断稳定趋势。"]

    ordered = df.sort_values(scan_variable).reset_index(drop=True)
    start = ordered.iloc[0]
    end = ordered.iloc[-1]

    def _finite(value: object) -> float | None:
        if not isinstance(value, (int, float, str, np.integer, np.floating)):
            return None
        try:
            converted = float(value)
        except (TypeError, ValueError):
            return None
        return converted if np.isfinite(converted) else None

    start_clean = _finite(start.get("peak_clean_signal"))
    end_clean = _finite(end.get("peak_clean_signal"))
    start_ref = _finite(start.get("A_ref"))
    end_ref = _finite(end.get("A_ref"))
    start_cross = _finite(start.get("peak_cross_term"))
    end_cross = _finite(end.get("peak_cross_term"))
    start_sca = _finite(start.get("peak_sca_only"))
    end_sca = _finite(end.get("peak_sca_only"))
    end_gain = _finite(end.get("heterodyne_gain"))

    lines: list[str] = []
    if start_clean is not None and end_clean is not None:
        if abs(end_clean) > abs(start_clean) * 1.10:
            lines.append("总体趋势：扫描末端的 clean 峰值更强，说明当前变量继续往这个方向推，系统输出仍在上升。")
        elif abs(end_clean) < abs(start_clean) * 0.90:
            lines.append("总体趋势：扫描末端的 clean 峰值反而更弱，说明这个变量继续往这个方向推并不会持续改善输出。")
        else:
            lines.append("总体趋势：clean 峰值变化不大，说明当前变量在这个区间里更像二阶影响，而不是主驱动。")

    if (
        start_ref is not None
        and end_ref is not None
        and start_cross is not None
        and end_cross is not None
        and start_sca is not None
        and end_sca is not None
    ):
        start_sca_mag = abs(start_sca)
        if abs(end_cross) >= max(abs(end_sca) * 1.2, 1e-30) and end_ref > start_ref * 1.05:
            lines.append("机制判断：`A_ref` 与干涉交叉项在一起升高，说明这条扫描更像是在改善 reference 放大。")
        elif abs(end_sca) > max(abs(end_cross), start_sca_mag) * 1.05:
            lines.append("机制判断：clean 峰值增强更多来自 `|E_sca|^2` 抬头，这更像粒子本征散射在变强，而不是 heterodyne 条件在变好。")
        else:
            lines.append("机制判断：reference 与粒子散射两条链都在变，解读时要同时看 `A_ref`、cross-term 和 `|E_sca|^2`。")

    if scan_variable == "rho":
        lines.append("什么算变好：`rho` 增大时，理想趋势是 `A_ref` 与 cross-term 一起升高，而异频增益不要明显塌掉。")
    elif scan_variable in {"width_nm", "depth_nm"}:
        lines.append("什么算变好：改几何时，最好看到 clean 峰值在上升，同时交叉项仍然主导；如果只是 `|E_sca|^2` 变大，就不算 reference 设计真的更优。")
    else:
        sign_changes = 0
        valid_signs = np.sign(ordered["peak_clean_signal"].to_numpy(dtype=float))
        valid_signs = valid_signs[np.isfinite(valid_signs) & (valid_signs != 0)]
        if len(valid_signs) >= 2:
            sign_changes = int(np.sum(valid_signs[1:] != valid_signs[:-1]))
        if sign_changes > 0:
            lines.append("什么算变好：扫波长时如果峰值极性发生翻转，不代表信号坏了，而是要回头区分这是材料相位翻转还是 reference 相位条件变了。")
        else:
            lines.append("什么算变好：扫波长时如果强度上升且极性稳定，说明这组波长更像是在同一干涉口径下持续增强，而不是靠相位翻面碰巧变亮。")

    if end_gain is not None:
        if end_gain >= 5.0:
            lines.append("当前扫描末端仍处在明显的 heterodyne 主导区，可以把 reference 放大解释得更积极一些。")
        elif end_gain <= 1.0:
            lines.append("当前扫描末端的异频增益已经不高，说明系统开始接近“纯散射也不可忽略”的区域。")

    return lines[:4]


def _build_interference_verdict_frame(summary: dict[str, float]) -> tuple[str, str, str]:
    cross_term = abs(float(summary.get("peak_cross_term", 0.0)))
    sca_only = abs(float(summary.get("peak_sca_only", 0.0)))
    a_ref = float(summary.get("A_ref", 0.0))
    overlap_status = str(summary.get("interference_overlap_agreement_status", "unavailable"))

    if cross_term > 5 * max(sca_only, 1e-30):
        better = "真正变好：`A_ref` 上升时，cross-term 也一起上升，而且仍明显压住 `|E_sca|^2`。"
        fake = "假变好：clean 峰值变大，但主要是 `|E_sca|^2` 抬头。"
    elif sca_only > cross_term:
        better = "真正变好：如果想回到典型 heterodyne 区，需要让交叉项重新成为主导，而不是继续堆高纯散射项。"
        fake = "假变好：只看 clean 峰值变大，却忽略系统已经越来越像纯散射检测。"
    else:
        better = "真正变好：理想趋势是继续把交叉项拉成主导，同时保留 clean 峰值上升。"
        fake = "假变好：reference 和散射项一起乱跳，导致峰值偶尔抬头但机制并不稳定。"

    trust = (
        f"当前更该先信 `{overlap_status}` 这条解释边界，再结合 A_ref={a_ref:.3e} 判断 reference 放大是否可信。"
    )
    return better, fake, trust


def render_interference_explorer() -> None:
    """Render the Interference Explorer page."""
    defaults = _apply_defaults(force=False)
    anchor_row, anchor_prefix = load_workflow_case_anchor(RESULTS_DIR, st.session_state)
    selected_case_exists = st.session_state.get("selected_particle") is not None

    st.header("Interference Explorer \u2014 \u4ece\u672c\u5f81\u6563\u5c04\u5230 clean signal \u8f93\u51fa")
    st.caption("这一页把标准结果库当前 case 的 Mie 本征散射接到 reference 上，解释 clean interferometric pulse 为什么会变强或变弱。")
    render_page_header_hub()
    linked_label = format_particle_label(defaults["material"], defaults["diameter_nm"])
    render_workflow_case_source_panel(
        anchor_row=anchor_row,
        anchor_prefix=anchor_prefix,
        selected_case_exists=selected_case_exists,
        selected_case_caption=(
            f"跨页联动：当前默认沿用最近选中的 case，即 {linked_label}, "
            f"λ≈{defaults['wavelength_nm']} nm, W={defaults['width_nm']} nm, H={defaults['depth_nm']} nm。"
        ),
        empty_case_caption="当前还没有跨页选中的 case。若你想沿主流程继续解释，请先回 `Design Explorer` 选点。",
        primary_metric_label="检出率",
        primary_metric_value=f"{float(anchor_row.get('detection_rate', 0.0)):.0%}" if anchor_row is not None else "N/A",
        explanation="这页负责解释标准结果库中当前 case 的本征散射，为什么在 reference 放大后会变成 clean interferometric signal。",
        missing_anchor_warning="当前 session 有跨页选点，但标准结果库里还没定位到对应 case；建议先回 `Design Explorer / Case Inspector` 重新确认。",
        no_selection_info="当前还没有跨页选中的 case。若你想沿主流程继续解释，请先去 `Design Explorer` 选一个 case。",
        is_live=bool(st.session_state.get("using_live_data")),
        live_tag=st.session_state.get("live_tag"),
        data_prefix=st.session_state.get("data_prefix"),
        standard_message="当前主流程正在围绕标准 biomimetic full-range 主结果库解释 clean signal 的来源。",
        live_message="当前 session 带有工程调试 live 参数；这里更适合拿来排查 reference 放大，而不是替换主流程结论。",
    )

    with st.sidebar:
        st.header("干涉系统参数")
        st.caption(defaults["source_label"])
        st.caption("这里只保留会直接改变 clean signal 判断的核心参数；其余系统细节固定沿用当前口径。")
        if st.session_state.get("selected_particle") is not None and st.button(
            "同步当前选点到本页参数",
            key="intf_sync_from_selected",
        ):
            _apply_defaults(force=True)
            st.rerun()
        st.selectbox(
            "材料",
            MATERIAL_OPTIONS,
            format_func=lambda x: MATERIAL_PHYSICS_LABELS.get(x, x),
            key="intf_material",
        )
        st.slider(
            "粒径 (nm)",
            DIAMETER_RANGE_NM[0],
            DIAMETER_RANGE_NM[1],
            value=st.session_state["intf_diameter_nm"],
            step=DASHBOARD_DIAMETER_STEP_NM,
            key="intf_diameter_nm",
        )
        st.selectbox("波长 (nm)", WAVELENGTH_OPTIONS_NM, key="intf_wavelength_nm")
        st.slider("W (nm)", GEOMETRY_RANGE_NM[0], GEOMETRY_RANGE_NM[1], value=st.session_state["intf_width_nm"], key="intf_width_nm")
        st.slider("H (nm)", GEOMETRY_RANGE_NM[0], GEOMETRY_RANGE_NM[1], value=st.session_state["intf_depth_nm"], key="intf_depth_nm")
        st.slider("粒子相对位置 x/(W/2)", -1.0, 1.0, value=float(st.session_state["intf_x_fraction"]), key="intf_x_fraction", step=0.05)
        st.slider("粒子相对位置 z/(H/2)", -1.0, 1.0, value=float(st.session_state["intf_z_fraction"]), key="intf_z_fraction", step=0.05)
        st.slider("rho", 0.5, 30.0, value=float(st.session_state["intf_rho"]), key="intf_rho", step=0.5)
        st.selectbox("参考场模型", REFERENCE_MODEL_OPTIONS, key="intf_reference_model")
        st.selectbox("位置耦合模型", ["constant", "gaussian_xy"], key="intf_coupling_model")

    sim_cfg, optical, source_label = resolve_active_system_defaults()
    sim_cfg.rho = st.session_state["intf_rho"]
    sim_cfg.reference_model = st.session_state["intf_reference_model"]
    sim_cfg.coupling_model = st.session_state["intf_coupling_model"]

    st.caption(
        f"{source_label} | rho={sim_cfg.rho:.1f} | 参考场模型={sim_cfg.reference_model} "
        f"| 参考场空间模式={sim_cfg.reference_spatial_mode} "
        f"耦合模型={sim_cfg.coupling_model} | 相位模型={sim_cfg.phase_model} | "
        f"收集角模型={sim_cfg.collection_angle_model} | 积分模式={sim_cfg.collection_integration_mode} "
        f"(σ={np.degrees(sim_cfg.collection_sigma_rad):.1f} deg) | "
        f"散射投影={sim_cfg.scattering_projection_mode} | "
        f"照明偏振={sim_cfg.illumination_polarization_mode} | "
        f"参考投影={sim_cfg.reference_projection_mode} | "
        f"脉冲检测={sim_cfg.pulse_detection_mode}"
    )

    case = compute_interference_case(
        material=st.session_state["intf_material"],
        diameter_nm=st.session_state["intf_diameter_nm"],
        wavelength_nm=st.session_state["intf_wavelength_nm"],
        width_nm=st.session_state["intf_width_nm"],
        depth_nm=st.session_state["intf_depth_nm"],
        initial_x_fraction=st.session_state["intf_x_fraction"],
        initial_z_fraction=st.session_state["intf_z_fraction"],
        sim_cfg=sim_cfg,
        optical_template=optical,
    )
    summary = case["summary"]
    trace_df = case["trace_df"]

    cols = st.columns(7)
    cols[0].metric("散射截面 (Csca)", f"{summary['Csca_m2']:.3e}")
    cols[1].metric("归一化散射场幅值 (E_sca)", f"{summary['E_sca_normalized']:.3e}")
    cols[2].metric("参考场幅值 (A_ref)", f"{summary['A_ref']:.3e}")
    cols[3].metric("干净信号峰值 (clean peak)", f"{summary['peak_clean_signal']:.3e}")
    heterodyne_display = "inf" if not np.isfinite(summary["heterodyne_gain"]) else f"{summary['heterodyne_gain']:.2f}"
    cols[4].metric("干涉放大倍数 (heterodyne gain)", heterodyne_display)
    cols[5].metric("耦合因子 (coupling)", f"{summary['coupling_factor']:.3f}")
    cols[6].metric("等效检测角 (theta_det)", f"{summary['theta_det_deg']:.1f}°")
    cols[0].caption(f"角谱中心角 (theta_center) = {summary.get('theta_center_deg', summary['theta_det_deg']):.1f}°")
    # --- Modal overlap diagnostic ---
    _overlap_abs = float(summary.get("interference_overlap_factor_abs", np.nan))
    _overlap_phase = float(summary.get("interference_overlap_factor_phase_rad", np.nan))
    _overlap_status = str(summary.get("interference_overlap_agreement_status", "unavailable"))
    overlap_cols = st.columns(4)
    overlap_cols[0].metric(
        "模式重叠因子幅值 |η|",
        f"{_overlap_abs:.3f}" if np.isfinite(_overlap_abs) else "N/A",
    )
    overlap_cols[1].metric(
        "重叠因子相位 ∠η (rad)",
        f"{_overlap_phase:.3f}" if np.isfinite(_overlap_phase) else "N/A",
    )
    overlap_cols[2].metric("干涉重叠一致性", _overlap_status)
    _eff = _overlap_abs if np.isfinite(_overlap_abs) else 0.0
    overlap_cols[3].metric(
        "有效 heterodyne 效率",
        f"{min(_eff, 1.0):.1%}" if np.isfinite(_overlap_abs) else "N/A",
    )
    if np.isfinite(_overlap_abs):
        if abs(_overlap_abs - 1.0) <= 0.10 and abs(_overlap_phase) <= 0.15:
            st.caption(
                f"模式重叠诊断：|η|={_overlap_abs:.3f}，∠η={_overlap_phase:.3f} rad，"
                "重叠良好（接近理想 heterodyne 条件）；当前 E_ref 与 E_sca 的空间模式基本匹配，"
                "干涉交叉项接近理论最大值。"
            )
        elif abs(_overlap_abs - 1.0) <= 0.30:
            st.caption(
                f"模式重叠诊断：|η|={_overlap_abs:.3f}，∠η={_overlap_phase:.3f} rad，"
                "重叠中等；实际 heterodyne 效率低于理想值，干涉增益有一定折损。"
                "这可能来自采集角偏离散射主瓣或参考场空间模式与散射场不完全匹配。"
            )
        else:
            st.warning(
                f"模式重叠诊断：|η|={_overlap_abs:.3f} 偏离 1.0 较远，"
                "说明参考场与散射场之间空间模式匹配较差；"
                "实际干涉增益将显著低于 A_ref × E_sca 的简单乘积估计。"
                "建议检查采集角、参考场模型与 rho 设置。"
            )

    st.caption(
        f"峰值时刻约 {summary['peak_time_ms']:.1f} ms；"
        f"干涉交叉项峰值 (peak cross-term)={summary['peak_cross_term']:.3e}，"
        f"散射平方项峰值 (peak |E_sca|^2)={summary['peak_sca_only']:.3e}。当前 clean trace 不再是单角取样，"
        f"而是围绕 {summary.get('theta_center_deg', summary['theta_det_deg']):.1f}° 的角谱带权收集后得到的等效响应；"
        f"本轮还把参考场推进到了 {summary.get('reference_spatial_mode', 'uniform')} 的位置相关 surrogate。"
    )
    overlap_status = str(summary.get("interference_overlap_agreement_status", "unavailable"))
    overlap_guidance = str(summary.get("interference_overlap_guidance", ""))
    st.markdown("### 本页结论")
    if abs(summary["peak_cross_term"]) > 5 * max(abs(summary["peak_sca_only"]), 1e-30):
        st.success("当前 clean signal 明显由干涉交叉项主导，说明 reference 放大而不是纯散射本身，才是这组参数变强的主要原因。")
    elif abs(summary["peak_sca_only"]) > abs(summary["peak_cross_term"]):
        st.warning("当前 clean signal 已经不再是典型弱散射 heterodyne 区，粒子本身散射项贡献已经超过交叉项。")
    else:
        st.info("当前 case 处在交叉项和纯散射项都不可忽略的过渡区，后续解读应同时参考 reference 与粒子本征散射。")
    st.caption(
        f"当前点的核心判断：overlap=`{overlap_status}`，参考场模式=`{summary.get('reference_spatial_mode', 'uniform')}`，"
        f"投影模式=`{summary.get('scattering_projection_mode', 'parallel')}`。先看这三项，再去读下面的分解图，结论会更稳。"
    )
    trend_cols = st.columns(3)
    trend_cols[0].metric(
        "当前放大机制",
        "cross-term 主导" if abs(summary["peak_cross_term"]) > abs(summary["peak_sca_only"]) else "散射项抬头",
    )
    trend_cols[1].metric("解释可信度", overlap_status)
    trend_cols[2].metric(
        "看趋势先盯",
        "A_ref 与 cross-term"
        if abs(summary["peak_cross_term"]) >= abs(summary["peak_sca_only"])
        else "E_sca 本身",
    )
    better_line, fake_line, trust_line = _build_interference_verdict_frame(summary)
    frame_cols = st.columns(3)
    frame_cols[0].markdown("**什么算真变好**")
    frame_cols[0].caption(better_line)
    frame_cols[1].markdown("**什么是假变好**")
    frame_cols[1].caption(fake_line)
    frame_cols[2].markdown("**先信什么证据**")
    frame_cols[2].caption(trust_line)
    st.caption(
        "什么趋势更好：如果扫描某个变量时 `参考场幅值 (A_ref)` 提升，同时 `干涉交叉项峰值 (peak cross-term)` 继续压住 `散射平方项 (|E_sca|^2)`，"
        "说明系统还在健康的 heterodyne 放大区；如果 clean peak 变强主要是因为 `散射平方项 (|E_sca|^2)` 抬头，"
        "那更像粒子本身够强，而不是 reference 放大变好了。"
    )
    st.caption(f"overlap 解释边界：{overlap_guidance}")

    st.subheader("Clean Trace 分解")
    st.caption(
        "看什么：把 `照明包络 (A_env)`、`时变散射场幅值 (A_sca(t))`、`干涉交叉项 (2Re(E_ref·E_sca*))` 和总 clean signal 输出放在同一条链上看。"
    )
    st.plotly_chart(_build_trace_figure(trace_df), width="stretch")

    c_left, c_right = st.columns([0.48, 0.52])
    with c_left:
        st.markdown("**峰值构成**")
        st.caption(
            "怎么看：如果堆叠图里主要是 `干涉交叉项 (Interference cross-term)`，说明这个系统处在典型的参考场放大工作区。"
        )
        st.plotly_chart(_build_peak_figure(summary), width="stretch")
    with c_right:
        st.markdown("**当前点怎么理解**")
        if abs(summary["peak_cross_term"]) > 5 * max(abs(summary["peak_sca_only"]), 1e-30):
            st.success("当前 pulse 明显由干涉交叉项主导。这说明系统看到的增强主要来自 reference 放大，而不是纯散射强度本身。")
        elif abs(summary["peak_sca_only"]) > abs(summary["peak_cross_term"]):
            st.warning("当前 pulse 里纯散射项已经不小，说明这个 case 更接近“散射本身够强”，而不是典型的弱散射 heterodyne 放大。")
        else:
            st.info("当前 case 处在散射项和交叉项都不可忽略的过渡区，既要看粒子本征散射，也要看 reference 参数。")

        st.caption(
            "关键机制补充："
            f"材料散射相位 (phi_material)={summary.get('peak_phi_material_rad', np.nan):.3f} rad | "
            f"投影后相位 (phi_projection)={summary.get('peak_phi_projection_rad', np.nan):.3f} rad | "
            f"横向路径相位 (phi_path_x)={summary.get('peak_phi_sca_path_x_rad', np.nan):.3f} rad | "
            f"深度路径相位 (phi_path_z)={summary.get('peak_phi_sca_path_z_rad', np.nan):.3f} rad"
        )

    st.subheader("单变量扫描：谁在放大 clean signal 输出")
    st.caption(
        "看什么：当只改一个变量时，`参考场幅值 (A_ref)`、`归一化散射场幅值 (E_sca)` 和 `干净信号峰值 (Peak clean signal)` 分别怎么变。"
    )
    scan_variable = st.selectbox(
        "扫描变量",
        ["rho", "width_nm", "depth_nm", "wavelength_nm"],
        format_func=lambda x: {
            "rho": "参考场比例因子 (rho)",
            "width_nm": "W（通道宽度）",
            "depth_nm": "H（通道深度）",
            "wavelength_nm": "波长",
        }[x],
        key="intf_scan_variable",
    )
    if scan_variable == "rho":
        scan_values = np.linspace(1.0, 30.0, 10)
    elif scan_variable == "width_nm" or scan_variable == "depth_nm":
        scan_values = np.arange(500, 2001, 150, dtype=float)
    else:
        scan_values = np.array(WAVELENGTH_OPTIONS_NM, dtype=float)

    scan_df = build_interference_scan_dataframe(
        scan_variable=scan_variable,
        scan_values=scan_values,
        material=st.session_state["intf_material"],
        diameter_nm=st.session_state["intf_diameter_nm"],
        wavelength_nm=st.session_state["intf_wavelength_nm"],
        width_nm=st.session_state["intf_width_nm"],
        depth_nm=st.session_state["intf_depth_nm"],
        initial_x_fraction=st.session_state["intf_x_fraction"],
        initial_z_fraction=st.session_state["intf_z_fraction"],
        sim_cfg=sim_cfg,
        optical_template=optical,
    )
    valid_scan_df = scan_df[scan_df["valid"]].copy()
    st.plotly_chart(_build_scan_figure(valid_scan_df, scan_variable), width="stretch")
    st.markdown("**怎么看这条扫描趋势**")
    for note in _build_interference_scan_notes(valid_scan_df, scan_variable):
        st.caption(note)
