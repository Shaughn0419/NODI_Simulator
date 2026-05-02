"""
dashboard/panels/noise_detection_explorer.py — Noise & Detection Explorer page

Explains how clean signals become detectable or missed after noise and thresholding.
"""

from __future__ import annotations

from copy import deepcopy
import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from nodi_simulator.dashboard.config import (
    DASHBOARD_DIAMETER_STEP_NM,
    DEFAULT_SIM_CFG,
    DIAMETER_RANGE_NM,
    FULL_SWEEP_WAVELENGTHS_NM,
    MATERIAL_OPTIONS,
    MATERIAL_PHYSICS_LABELS,
    OPTICAL_TEMPLATE,
    REFERENCE_MODEL_OPTIONS,
    format_particle_label,
)
from nodi_simulator.dashboard.backend import (
    load_workflow_case_anchor,
)
from nodi_simulator.dashboard.panels.common import (
    render_page_header_hub,
    render_workflow_case_source_panel,
    resolve_shared_case_parameter_defaults,
)
from nodi_simulator.dashboard.signal_backend import (
    build_detection_scan_dataframe,
    build_event_trace_dataframe,
    compute_noise_detection_case,
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
        "noise_std": float(sim_cfg.noise_std),
        "shot_noise_scale": float(sim_cfg.shot_noise_scale),
        "noise_model": sim_cfg.noise_model,
        "drift_slope": float(sim_cfg.drift_slope),
        "post_readout_noise_std": float(sim_cfg.post_readout_noise_std),
        "post_readout_drift_slope": float(sim_cfg.post_readout_drift_slope),
        "threshold_sigma": float(sim_cfg.threshold_sigma),
        "velocity_mm_s": float(sim_cfg.mean_flow_velocity_m_s * 1e3),
        "include_diffusion": bool(sim_cfg.include_diffusion),
        "rho": float(sim_cfg.rho),
        "phase_model": sim_cfg.phase_model,
        "reference_model": sim_cfg.reference_model,
        "collection_angle_model": sim_cfg.collection_angle_model,
        "collection_integration_mode": sim_cfg.collection_integration_mode,
        "collection_sigma_deg": float(np.degrees(sim_cfg.collection_sigma_rad)),
        "scattering_projection_mode": sim_cfg.scattering_projection_mode,
        "pulse_detection_mode": sim_cfg.pulse_detection_mode,
        "detection_decision_mode": sim_cfg.detection_decision_mode,
        "readout_model": sim_cfg.readout_model,
        "readout_observable_mode": sim_cfg.readout_observable_mode,
        "lockin_time_constant_ms": float(sim_cfg.lockin_time_constant_s * 1e3),
        "pod_lockin_frequency_Hz": float(sim_cfg.pod_lockin_frequency_Hz),
        "nodi_lockin_frequency_Hz": float(sim_cfg.nodi_lockin_frequency_Hz),
        "pod_reference_phase_deg": float(np.degrees(sim_cfg.pod_reference_phase_rad)),
        "nodi_reference_phase_deg": float(np.degrees(sim_cfg.nodi_reference_phase_rad)),
        "pod_to_nodi_crosstalk": float(sim_cfg.pod_to_nodi_crosstalk),
        "nodi_to_pod_crosstalk": float(sim_cfg.nodi_to_pod_crosstalk),
        "ref_alpha": float(sim_cfg.ref_alpha),
        "ref_beta": float(sim_cfg.ref_beta),
        "ref_gamma": float(sim_cfg.ref_gamma),
        "coupling_model": sim_cfg.coupling_model,
        "normalization_mode": sim_cfg.normalization_mode,
        "beam_waist_y_nm": int(round(float(optical.beam_waist_y_m * 1e9))),
    }


def _apply_defaults(force: bool = False) -> dict[str, object]:
    defaults = _resolve_defaults()
    key_defaults = {
        "nd_material": defaults["material"],
        "nd_diameter_nm": defaults["diameter_nm"],
        "nd_wavelength_nm": defaults["wavelength_nm"],
        "nd_width_nm": defaults["width_nm"],
        "nd_depth_nm": defaults["depth_nm"],
        "nd_noise_std": defaults["noise_std"],
        "nd_shot_noise_scale": defaults["shot_noise_scale"],
        "nd_noise_model": defaults["noise_model"],
        "nd_drift_slope": defaults["drift_slope"],
        "nd_post_readout_noise_std": defaults["post_readout_noise_std"],
        "nd_post_readout_drift_slope": defaults["post_readout_drift_slope"],
        "nd_threshold_sigma": defaults["threshold_sigma"],
        "nd_velocity_mm_s": defaults["velocity_mm_s"],
        "nd_include_diffusion": defaults["include_diffusion"],
        "nd_n_events": 16,
        "nd_rho": defaults["rho"],
        "nd_reference_model": defaults["reference_model"],
        "nd_ref_alpha": defaults["ref_alpha"],
        "nd_ref_beta": defaults["ref_beta"],
        "nd_ref_gamma": defaults["ref_gamma"],
        "nd_coupling_model": defaults["coupling_model"],
        "nd_detection_decision_mode": defaults["detection_decision_mode"],
        "nd_readout_model": defaults["readout_model"],
        "nd_readout_observable_mode": defaults["readout_observable_mode"],
        "nd_lockin_time_constant_ms": defaults["lockin_time_constant_ms"],
        "nd_pod_lockin_frequency_Hz": defaults["pod_lockin_frequency_Hz"],
        "nd_nodi_lockin_frequency_Hz": defaults["nodi_lockin_frequency_Hz"],
        "nd_pod_reference_phase_deg": defaults["pod_reference_phase_deg"],
        "nd_nodi_reference_phase_deg": defaults["nodi_reference_phase_deg"],
        "nd_pod_to_nodi_crosstalk": defaults["pod_to_nodi_crosstalk"],
        "nd_nodi_to_pod_crosstalk": defaults["nodi_to_pod_crosstalk"],
        "nd_beam_waist_y_nm": defaults["beam_waist_y_nm"],
        "nd_scan_variable": "noise_std",
    }
    for key, value in key_defaults.items():
        if force or key not in st.session_state:
            st.session_state[key] = value
    return defaults


def _build_detection_scan_notes(df: pd.DataFrame, scan_variable: str) -> list[str]:
    if df.empty or len(df) < 2:
        return ["当前扫描点太少，还不足以判断稳定趋势。"]

    ordered = df.sort_values(scan_variable).reset_index(drop=True)
    start = ordered.iloc[0]
    end = ordered.iloc[-1]

    def _finite(row: pd.Series, key: str) -> float | None:
        try:
            value = float(row.get(key, np.nan))
        except (TypeError, ValueError):
            return None
        return value if np.isfinite(value) else None

    start_det = _finite(start, "detection_rate")
    end_det = _finite(end, "detection_rate")
    start_peak = _finite(start, "mean_peak_height")
    end_peak = _finite(end, "mean_peak_height")
    start_thr = _finite(start, "mean_threshold")
    end_thr = _finite(end, "mean_threshold")
    end_cv = _finite(end, "CV")

    lines: list[str] = []
    if None not in (start_det, end_det):
        if end_det > start_det + 0.10:
            lines.append("总体趋势：扫描末端的检出率更高，说明当前变量往这个方向推会让更多事件稳定越过阈值。")
        elif end_det < start_det - 0.10:
            lines.append("总体趋势：扫描末端的检出率明显更低，说明这个方向正在把当前点拖出可检测区。")
        else:
            lines.append("总体趋势：检出率变化不算大，说明当前变量在这段范围里不是唯一主导瓶颈。")

    if None not in (start_peak, end_peak, start_thr, end_thr):
        start_margin = start_peak - start_thr
        end_margin = end_peak - end_thr
        if end_margin > start_margin + max(abs(start_margin), 1e-12) * 0.10:
            lines.append("余量判断：扫描末端的“峰高减阈值”余量更大，说明改善来自可检测余量真正变宽，而不只是阈值口径碰巧变化。")
        elif end_margin < start_margin - max(abs(start_margin), 1e-12) * 0.10:
            lines.append("余量判断：扫描末端的“峰高减阈值”余量更差，说明问题在于 clean peak 与阈值之间的安全距离被压缩了。")
        else:
            lines.append("余量判断：峰高和阈值在一起变，当前更需要看单事件 trace 判断是噪声上升还是峰值被削弱。")

    if scan_variable == "noise_std":
        lines.append("什么算变好：噪声扫描里，理想趋势是噪声降低后检出率升高，同时平均阈值也一起下降。")
    elif scan_variable == "threshold_sigma":
        lines.append("什么算变好：阈值扫描里，理想趋势是阈值放宽时检出率回升，但不要只靠极端低阈值撑结果；要一起看假设余量是否仍合理。")
    else:
        lines.append("什么算变好：流速扫描里，理想趋势是流速降低后检出率回升；如果一加速就掉点，说明当前点更像被 transit time 和带宽吃掉。")

    if end_cv is not None:
        if end_cv <= 0.35:
            lines.append("当前扫描末端的事件间波动不大，说明 detect/miss 更像由整体强弱决定，而不是少数边缘事件掉队。")
        elif end_cv >= 0.70:
            lines.append("当前扫描末端的事件间波动已经偏大，说明后面要重点怀疑位置波动、扩散或 paired 判决不稳定。")

    return lines[:4]


def _build_detection_verdict_frame(
    detection_rate: float,
    peak_to_threshold: float,
    bandwidth_limited: float,
) -> tuple[str, str, str]:
    if detection_rate >= 0.8 and peak_to_threshold >= 1.5:
        better = "真正变好：检出率继续上升，同时峰高/阈值比保持在 1 以上并继续拉开。"
    elif peak_to_threshold < 1.0:
        better = "真正变好：先把峰高/阈值比拉回 1 以上，再谈 single/paired 或更细的分类差异。"
    else:
        better = "真正变好：检出率上升时，最好伴随余量变宽，而不是只靠偶发峰值越线。"

    if bandwidth_limited >= 0.4:
        fake = "假变好：只看平均峰高，不看 transit/bandwidth 限制；这种情况下脉冲可能还没进读出就被时间常数吃掉。"
    else:
        fake = "假变好：只看单个事件过阈值，却不看批量检出率和余量，容易把边缘点误当稳健点。"

    trust = "先信 `检出率 + 峰高/阈值比 + 带宽受限占比` 这三项的组合，不要只盯任何一个单独数字。"
    return better, fake, trust


@st.cache_data(show_spinner=False)
def _detection_case_cached(
    material: str,
    diameter_nm: int,
    wavelength_nm: int,
    width_nm: int,
    depth_nm: int,
    n_events: int,
    noise_std: float,
    shot_noise_scale: float,
    noise_model: str,
    drift_slope: float,
    post_readout_noise_std: float,
    post_readout_drift_slope: float,
    threshold_sigma: float,
    velocity_mm_s: float,
    include_diffusion: bool,
    rho: float,
    reference_model: str,
    ref_alpha: float,
    ref_beta: float,
    ref_gamma: float,
    coupling_model: str,
    detection_decision_mode: str,
    readout_model: str,
    readout_observable_mode: str,
    lockin_time_constant_ms: float,
    pod_lockin_frequency_Hz: float,
    nodi_lockin_frequency_Hz: float,
    pod_reference_phase_deg: float,
    nodi_reference_phase_deg: float,
    pod_to_nodi_crosstalk: float,
    nodi_to_pod_crosstalk: float,
    beam_waist_y_nm: int,
    normalization_mode: str,
):
    sim_cfg = deepcopy(DEFAULT_SIM_CFG)
    sim_cfg.n_events = n_events
    sim_cfg.noise_std = noise_std
    sim_cfg.shot_noise_scale = shot_noise_scale
    sim_cfg.noise_model = noise_model
    sim_cfg.drift_slope = drift_slope
    sim_cfg.post_readout_noise_std = post_readout_noise_std
    sim_cfg.post_readout_drift_slope = post_readout_drift_slope
    sim_cfg.threshold_sigma = threshold_sigma
    sim_cfg.mean_flow_velocity_m_s = velocity_mm_s * 1e-3
    sim_cfg.include_diffusion = include_diffusion
    sim_cfg.rho = rho
    sim_cfg.reference_model = reference_model
    sim_cfg.ref_alpha = ref_alpha
    sim_cfg.ref_beta = ref_beta
    sim_cfg.ref_gamma = ref_gamma
    sim_cfg.coupling_model = coupling_model
    sim_cfg.detection_decision_mode = detection_decision_mode
    sim_cfg.readout_model = readout_model
    sim_cfg.readout_observable_mode = readout_observable_mode
    sim_cfg.lockin_time_constant_s = lockin_time_constant_ms * 1e-3
    sim_cfg.pod_lockin_frequency_Hz = pod_lockin_frequency_Hz
    sim_cfg.nodi_lockin_frequency_Hz = nodi_lockin_frequency_Hz
    sim_cfg.pod_reference_phase_rad = np.deg2rad(pod_reference_phase_deg)
    sim_cfg.nodi_reference_phase_rad = np.deg2rad(nodi_reference_phase_deg)
    sim_cfg.pod_to_nodi_crosstalk = pod_to_nodi_crosstalk
    sim_cfg.nodi_to_pod_crosstalk = nodi_to_pod_crosstalk
    sim_cfg.normalization_mode = normalization_mode

    optical = deepcopy(OPTICAL_TEMPLATE)
    optical.beam_waist_y_m = beam_waist_y_nm * 1e-9

    return compute_noise_detection_case(
        material=material,
        diameter_nm=diameter_nm,
        wavelength_nm=wavelength_nm,
        width_nm=width_nm,
        depth_nm=depth_nm,
        sim_cfg=sim_cfg,
        optical_template=optical,
        n_events=n_events,
    )


@st.cache_data(show_spinner=False)
def _detection_scan_cached(
    scan_variable: str,
    scan_values: tuple[float, ...],
    material: str,
    diameter_nm: int,
    wavelength_nm: int,
    width_nm: int,
    depth_nm: int,
    noise_std: float,
    shot_noise_scale: float,
    noise_model: str,
    drift_slope: float,
    post_readout_noise_std: float,
    post_readout_drift_slope: float,
    threshold_sigma: float,
    velocity_mm_s: float,
    include_diffusion: bool,
    rho: float,
    reference_model: str,
    ref_alpha: float,
    ref_beta: float,
    ref_gamma: float,
    coupling_model: str,
    detection_decision_mode: str,
    readout_model: str,
    readout_observable_mode: str,
    lockin_time_constant_ms: float,
    pod_lockin_frequency_Hz: float,
    nodi_lockin_frequency_Hz: float,
    pod_reference_phase_deg: float,
    nodi_reference_phase_deg: float,
    pod_to_nodi_crosstalk: float,
    nodi_to_pod_crosstalk: float,
    beam_waist_y_nm: int,
    normalization_mode: str,
):
    sim_cfg = deepcopy(DEFAULT_SIM_CFG)
    sim_cfg.noise_std = noise_std
    sim_cfg.shot_noise_scale = shot_noise_scale
    sim_cfg.noise_model = noise_model
    sim_cfg.drift_slope = drift_slope
    sim_cfg.post_readout_noise_std = post_readout_noise_std
    sim_cfg.post_readout_drift_slope = post_readout_drift_slope
    sim_cfg.threshold_sigma = threshold_sigma
    sim_cfg.mean_flow_velocity_m_s = velocity_mm_s * 1e-3
    sim_cfg.include_diffusion = include_diffusion
    sim_cfg.rho = rho
    sim_cfg.reference_model = reference_model
    sim_cfg.ref_alpha = ref_alpha
    sim_cfg.ref_beta = ref_beta
    sim_cfg.ref_gamma = ref_gamma
    sim_cfg.coupling_model = coupling_model
    sim_cfg.detection_decision_mode = detection_decision_mode
    sim_cfg.readout_model = readout_model
    sim_cfg.readout_observable_mode = readout_observable_mode
    sim_cfg.lockin_time_constant_s = lockin_time_constant_ms * 1e-3
    sim_cfg.pod_lockin_frequency_Hz = pod_lockin_frequency_Hz
    sim_cfg.nodi_lockin_frequency_Hz = nodi_lockin_frequency_Hz
    sim_cfg.pod_reference_phase_rad = np.deg2rad(pod_reference_phase_deg)
    sim_cfg.nodi_reference_phase_rad = np.deg2rad(nodi_reference_phase_deg)
    sim_cfg.pod_to_nodi_crosstalk = pod_to_nodi_crosstalk
    sim_cfg.nodi_to_pod_crosstalk = nodi_to_pod_crosstalk
    sim_cfg.normalization_mode = normalization_mode

    optical = deepcopy(OPTICAL_TEMPLATE)
    optical.beam_waist_y_m = beam_waist_y_nm * 1e-9

    return build_detection_scan_dataframe(
        scan_variable=scan_variable,
        scan_values=list(scan_values),
        material=material,
        diameter_nm=diameter_nm,
        wavelength_nm=wavelength_nm,
        width_nm=width_nm,
        depth_nm=depth_nm,
        sim_cfg=sim_cfg,
        optical_template=optical,
        n_events=8,
    )


def _build_trace_figure(trace_df) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=trace_df["time_ms"], y=trace_df["clean_signal"], name="clean signal"))
    if "signal_raw_noisy" in trace_df:
        fig.add_trace(go.Scatter(x=trace_df["time_ms"], y=trace_df["signal_raw_noisy"], name="原始含噪信号"))
    if "shot_noise" in trace_df and not np.allclose(trace_df["shot_noise"], 0.0):
        fig.add_trace(
            go.Scatter(
                x=trace_df["time_ms"],
                y=trace_df["shot_noise"],
                name="shot-noise surrogate",
                line=dict(dash="dot"),
            )
        )
    if "signal_detect_pre_post" in trace_df:
        fig.add_trace(go.Scatter(x=trace_df["time_ms"], y=trace_df["signal_detect_pre_post"], name="读出后、阈值前"))
    if "signal_pod" in trace_df and not np.allclose(trace_df["signal_pod"], 0.0):
        fig.add_trace(go.Scatter(x=trace_df["time_ms"], y=trace_df["signal_pod"], name="POD surrogate"))
    if "signal_nodi_q" in trace_df and not np.allclose(trace_df["signal_nodi_q"], 0.0):
        fig.add_trace(go.Scatter(x=trace_df["time_ms"], y=trace_df["signal_nodi_q"], name="NODI Q", line=dict(dash="dot")))
    if "signal_nodi_mag" in trace_df and not np.allclose(trace_df["signal_nodi_mag"], trace_df["signal_noisy"]):
        fig.add_trace(go.Scatter(x=trace_df["time_ms"], y=trace_df["signal_nodi_mag"], name="NODI magnitude", line=dict(dash="dash")))
    fig.add_trace(go.Scatter(x=trace_df["time_ms"], y=trace_df["signal_noisy"], name="NODI 读出"))
    fig.add_trace(
        go.Scatter(
            x=trace_df["time_ms"],
            y=trace_df["threshold"],
            name="阈值",
            line=dict(dash="dash"),
        )
    )
    fig.update_layout(
        height=420,
        xaxis_title="时间 (ms)",
        yaxis_title="信号 (a.u.)",
        title="单事件轨迹：clean / raw / readout / 阈值 对照",
    )
    return fig


def _build_detection_outcome_figure(event_df: pd.DataFrame) -> go.Figure:
    detected_count = int(event_df["detected"].sum())
    missed_count = int((~event_df["detected"]).sum())

    fig = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("检出 / 漏检数量", "已检出事件的最佳峰高分布"),
    )
    fig.add_trace(
        go.Bar(x=["已检出", "未检出"], y=[detected_count, missed_count], name="事件数"),
        row=1,
        col=1,
    )
    detected_heights = event_df.loc[event_df["detected"], "best_peak_height"]
    fig.add_trace(
        go.Histogram(x=detected_heights, nbinsx=20, name="最佳峰高"),
        row=1,
        col=2,
    )
    fig.update_layout(height=360, showlegend=False)
    fig.update_yaxes(title_text="数量", row=1, col=1)
    fig.update_xaxes(title_text="峰高", row=1, col=2)
    return fig


def _build_scan_figure(df: pd.DataFrame, scan_variable: str) -> go.Figure:
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.10,
        subplot_titles=("检出率与阈值", "峰高与 CV"),
    )
    x = df[scan_variable]
    fig.add_trace(
        go.Scatter(x=x, y=df["detection_rate"], mode="lines+markers", name="检出率"),
        row=1,
        col=1,
    )
    if "single_channel_detection_rate" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=x,
                y=df["single_channel_detection_rate"],
                mode="lines+markers",
                name="单通道检出率",
                line=dict(dash="dot"),
            ),
            row=1,
            col=1,
        )
    if "paired_channel_detection_rate" in df.columns:
        fig.add_trace(
            go.Scatter(
                x=x,
                y=df["paired_channel_detection_rate"],
                mode="lines+markers",
                name="双通道检出率",
                line=dict(dash="dash"),
            ),
            row=1,
            col=1,
        )
    fig.add_trace(
        go.Scatter(x=x, y=df["mean_threshold"], mode="lines+markers", name="平均阈值"),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=x, y=df["mean_peak_height"], mode="lines+markers", name="平均峰高"),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(x=x, y=df["CV"], mode="lines+markers", name="CV"),
        row=2,
        col=1,
    )
    axis_titles = {
        "noise_std": "噪声标准差",
        "threshold_sigma": "阈值倍数",
        "velocity_mm_s": "流速 (mm/s)",
    }
    fig.update_layout(height=600)
    fig.update_yaxes(title_text="检出率 / 阈值", row=1, col=1)
    fig.update_yaxes(title_text="峰高 / CV", row=2, col=1)
    fig.update_xaxes(title_text=axis_titles.get(scan_variable, scan_variable), row=2, col=1)
    return fig


def render_noise_detection_explorer() -> None:
    """Render the Noise & Detection Explorer page."""
    defaults = _apply_defaults(force=False)
    anchor_row, anchor_prefix = load_workflow_case_anchor(RESULTS_DIR, st.session_state)
    selected_case_exists = st.session_state.get("selected_particle") is not None

    st.header("Noise & Detection Explorer \u2014 \u4ece clean signal \u5230\u80fd\u5426\u68c0\u51fa")
    st.caption("这一页解释标准结果库当前 case 的 clean signal，为什么最后会走向稳定检出、边缘可检，或者直接 miss。")
    render_page_header_hub("Noise & Detection Explorer")
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
        primary_metric_label="稳定检出率",
        primary_metric_value=f"{float(anchor_row.get('stable_detection_rate', 0.0)):.0%}" if anchor_row is not None else "N/A",
        explanation="这页负责解释标准结果库中当前 case 的 clean signal，为什么最后会落到 detection / gate / freeze 这些实验结论上。",
        missing_anchor_warning="当前 session 有跨页选点，但标准结果库里还没定位到对应 case；建议先回 `Design Explorer / Case Inspector` 重新确认。",
        no_selection_info="当前还没有跨页选中的 case。若你想沿主流程继续解释，请先去 `Design Explorer` 选一个 case。",
        is_live=bool(st.session_state.get("using_live_data")),
        live_tag=st.session_state.get("live_tag"),
        data_prefix=st.session_state.get("data_prefix"),
        standard_message="当前主流程正在围绕标准 biomimetic full-range 主结果库解释检出与漏检。",
        live_message="当前 session 带有工程调试 live 参数；这里更适合拿来排查 detection 边界，而不是替换主流程结论。",
    )

    with st.sidebar:
        st.header("噪声与检测参数")
        st.caption(defaults["source_label"])
        st.caption("这里只保留最常用的检出边界控制；相位、串扰和后级细节默认固定，避免页面重新膨胀。")
        if st.session_state.get("selected_particle") is not None:
            if st.button("同步当前选点到本页参数", key="nd_sync_from_selected"):
                _apply_defaults(force=True)
                st.rerun()
        st.selectbox(
            "材料",
            MATERIAL_OPTIONS,
            format_func=lambda x: MATERIAL_PHYSICS_LABELS.get(x, x),
            key="nd_material",
        )
        st.slider(
            "粒径 (nm)",
            DIAMETER_RANGE_NM[0],
            DIAMETER_RANGE_NM[1],
            value=st.session_state["nd_diameter_nm"],
            step=DASHBOARD_DIAMETER_STEP_NM,
            key="nd_diameter_nm",
        )
        st.selectbox("波长 (nm)", WAVELENGTH_OPTIONS_NM, key="nd_wavelength_nm")
        st.slider("W (nm)", GEOMETRY_RANGE_NM[0], GEOMETRY_RANGE_NM[1], value=st.session_state["nd_width_nm"], key="nd_width_nm")
        st.slider("H (nm)", GEOMETRY_RANGE_NM[0], GEOMETRY_RANGE_NM[1], value=st.session_state["nd_depth_nm"], key="nd_depth_nm")
        st.slider("噪声标准差", 0.0, 0.10, value=float(st.session_state["nd_noise_std"]), step=0.002, key="nd_noise_std")
        st.slider("shot-noise 系数", 0.0, 0.01, value=float(st.session_state["nd_shot_noise_scale"]), step=0.0002, key="nd_shot_noise_scale")
        st.selectbox("噪声模型", ["gaussian", "gaussian_plus_drift"], key="nd_noise_model")
        st.slider("漂移斜率", 0.0, 0.02, value=float(st.session_state["nd_drift_slope"]), step=0.0005, key="nd_drift_slope")
        st.slider("阈值倍数", 1.0, 10.0, value=float(st.session_state["nd_threshold_sigma"]), step=0.2, key="nd_threshold_sigma")
        st.slider("流速 (mm/s)", 0.05, 1.00, value=float(st.session_state["nd_velocity_mm_s"]), step=0.05, key="nd_velocity_mm_s")
        st.checkbox("启用布朗扩散", key="nd_include_diffusion")
        st.slider("批量事件数", 8, 60, value=int(st.session_state["nd_n_events"]), step=4, key="nd_n_events")
        st.slider("rho", 0.5, 30.0, value=float(st.session_state["nd_rho"]), step=0.5, key="nd_rho")
        st.selectbox("参考场模型", REFERENCE_MODEL_OPTIONS, key="nd_reference_model")
        st.selectbox("位置耦合模型", ["constant", "gaussian_xy"], key="nd_coupling_model")
        st.selectbox(
            "最终判决模式",
            ["single_channel", "paired_channel"],
            format_func=lambda x: {
                "single_channel": "single_channel（只看 NODI）",
                "paired_channel": "paired_channel（要求 NODI/POD 配对）",
            }[x],
            key="nd_detection_decision_mode",
        )
        st.selectbox("读出模型", ["raw", "lockin_surrogate"], key="nd_readout_model")
        st.slider("lock-in 时间常数 (ms)", 0.2, 5.0, value=float(st.session_state["nd_lockin_time_constant_ms"]), step=0.1, key="nd_lockin_time_constant_ms")

    case = _detection_case_cached(
        st.session_state["nd_material"],
        int(st.session_state["nd_diameter_nm"]),
        int(st.session_state["nd_wavelength_nm"]),
        int(st.session_state["nd_width_nm"]),
        int(st.session_state["nd_depth_nm"]),
        int(st.session_state["nd_n_events"]),
        float(st.session_state["nd_noise_std"]),
        float(st.session_state["nd_shot_noise_scale"]),
        st.session_state["nd_noise_model"],
        float(st.session_state["nd_drift_slope"]),
        float(st.session_state["nd_post_readout_noise_std"]),
        float(st.session_state["nd_post_readout_drift_slope"]),
        float(st.session_state["nd_threshold_sigma"]),
        float(st.session_state["nd_velocity_mm_s"]),
        bool(st.session_state["nd_include_diffusion"]),
        float(st.session_state["nd_rho"]),
        st.session_state["nd_reference_model"],
        float(st.session_state["nd_ref_alpha"]),
        float(st.session_state["nd_ref_beta"]),
        float(st.session_state["nd_ref_gamma"]),
        st.session_state["nd_coupling_model"],
        st.session_state["nd_detection_decision_mode"],
        st.session_state["nd_readout_model"],
        st.session_state["nd_readout_observable_mode"],
        float(st.session_state["nd_lockin_time_constant_ms"]),
        float(st.session_state["nd_pod_lockin_frequency_Hz"]),
        float(st.session_state["nd_nodi_lockin_frequency_Hz"]),
        float(st.session_state["nd_pod_reference_phase_deg"]),
        float(st.session_state["nd_nodi_reference_phase_deg"]),
        float(st.session_state["nd_pod_to_nodi_crosstalk"]),
        float(st.session_state["nd_nodi_to_pod_crosstalk"]),
        int(st.session_state["nd_beam_waist_y_nm"]),
        defaults["normalization_mode"],
    )
    summary = case["summary"]
    event_df = case["event_df"]

    st.caption(
        f"{defaults['source_label']} | raw噪声={st.session_state['nd_noise_std']:.3f} "
        f"| shot={st.session_state['nd_shot_noise_scale']:.4f} ({st.session_state['nd_noise_model']}) "
        f"| 阈值={st.session_state['nd_threshold_sigma']:.1f} sigma | 流速={st.session_state['nd_velocity_mm_s']:.2f} mm/s "
        f"| 扩散={'开启' if st.session_state['nd_include_diffusion'] else '关闭'} "
        f"| 相位模型={defaults['phase_model']} | 检测角模型={defaults['collection_angle_model']} "
        f"| 角谱收集={defaults['collection_integration_mode']} (σ={defaults['collection_sigma_deg']:.1f}°) "
        f"| 散射投影={defaults['scattering_projection_mode']} | 脉冲检测={defaults['pulse_detection_mode']} "
        f"| 判决={st.session_state['nd_detection_decision_mode']} "
        f"| 读出={st.session_state['nd_readout_model']} (tau={st.session_state['nd_lockin_time_constant_ms']:.1f} ms)"
    )

    cv_value = summary["std_peak_height"] / summary["mean_peak_height"] if summary["mean_peak_height"] > 0 else np.nan
    peak_to_threshold = float(summary.get("mean_peak_to_threshold_ratio", 0.0) or 0.0)
    bandwidth_limited = float(summary.get("mean_nodi_bandwidth_limited_fraction", 0.0) or 0.0)
    cols = st.columns(6)
    cols[0].metric("检出率", f"{summary['detection_rate']:.0%}")
    cols[1].metric("峰高/阈值比", f"{peak_to_threshold:.2f}")
    cols[2].metric("平均阈值", f"{summary['mean_threshold']:.3e}")
    cols[3].metric("平均峰高", f"{summary['mean_peak_height']:.3e}")
    cols[4].metric("双通道检出率", f"{summary.get('paired_channel_detection_rate', 0.0):.0%}")
    cols[5].metric("带宽受限占比", f"{bandwidth_limited:.0%}")
    st.caption(
        f"等效检测角={summary['theta_det_deg']:.1f}°（角谱中心 {summary.get('theta_center_deg', summary['theta_det_deg']):.1f}°） | "
        f"CV={'N/A' if np.isnan(cv_value) else f'{cv_value:.3f}'} | "
        f"基线={summary.get('mean_I_baseline', 0.0):.2e} | "
        f"shot={summary.get('mean_shot_noise_std', 0.0):.2e} | "
        f"判决={summary.get('detection_decision_mode', 'single_channel')} | "
        f"best peak 配对率={summary.get('best_peak_pairing_rate', 0.0):.0%}"
    )
    st.markdown("### 本页结论")
    if summary["detection_rate"] >= 0.8 and peak_to_threshold >= 1.5:
        st.success("当前参数下，大多数事件都能稳定越过阈值；这说明 clean signal 与检测设置之间仍有比较充足的余量。")
    elif bandwidth_limited >= 0.4:
        st.warning("当前参数下，NODI 读出已经明显受 transit-bandwidth 限制；如果想继续提检出率，优先复核时间常数、流速和 beam waist。")
    elif peak_to_threshold < 1.0:
        st.error("当前平均峰值还压不过阈值，主要问题不是分类策略，而是 clean signal 与噪声/阈值之间余量不足。")
    else:
        st.info("当前参数处在边缘可检测区，检出结果会明显依赖噪声、阈值和位置波动。")
    st.caption(
        f"最值得优先盯的三个量是：峰高/阈值比={peak_to_threshold:.2f}，"
        f"shared 检出率={summary['detection_rate']:.0%}，"
        f"NODI 带宽受限占比={bandwidth_limited:.0%}。"
    )
    if bandwidth_limited >= 0.4:
        primary_bottleneck = "读出带宽限制"
        next_adjustment = "优先调 `lockin tau / 流速 / beam waist`，先确认脉冲没有被时间常数吃掉。"
    elif peak_to_threshold < 1.0:
        primary_bottleneck = "峰值余量不足"
        next_adjustment = "优先看 `rho / 耦合 / reference / 阈值`，先把 clean peak 拉到阈值上方。"
    elif summary["detection_rate"] < 0.8:
        primary_bottleneck = "事件间波动过大"
        next_adjustment = "优先看扩散、位置波动和 paired/single 判决差异，判断是不是边缘事件在掉队。"
    else:
        primary_bottleneck = "当前没有单一硬瓶颈"
        next_adjustment = "可以开始看参数扫描，确认这不是只在当前点成立的局部最优。"

    if summary["detection_rate"] >= 0.8 and peak_to_threshold >= 1.5:
        detect_regime = "稳健可检测区"
    elif peak_to_threshold < 1.0:
        detect_regime = "阈值下方"
    else:
        detect_regime = "边缘可检测区"

    diag_cols = st.columns(3)
    diag_cols[0].metric("当前检测区间", detect_regime)
    diag_cols[1].metric("主要瓶颈", primary_bottleneck)
    diag_cols[2].metric(
        "优先比较",
        "single vs paired"
        if summary.get("paired_channel_detection_rate", 0.0) + 1e-12 < summary.get("detection_rate", 0.0)
        else "noise/threshold scan",
    )
    better_line, fake_line, trust_line = _build_detection_verdict_frame(
        float(summary["detection_rate"]),
        peak_to_threshold,
        bandwidth_limited,
    )
    frame_cols = st.columns(3)
    frame_cols[0].markdown("**什么算真变好**")
    frame_cols[0].caption(better_line)
    frame_cols[1].markdown("**什么是假变好**")
    frame_cols[1].caption(fake_line)
    frame_cols[2].markdown("**先信什么证据**")
    frame_cols[2].caption(trust_line)
    st.caption(f"建议下一步：{next_adjustment}")

    st.subheader("1. 单事件 trace：看 detect / miss 背后的单次脉冲")
    st.caption("看什么：同一个事件的 clean、含噪和阈值关系；先判断脉冲是被噪声淹没，还是本来就贴着阈值。")

    event_options = list(range(len(event_df)))
    selected_event = st.selectbox(
        "查看事件",
        event_options,
        index=0,
        format_func=lambda idx: (
            f"事件 {idx + 1} | "
            f"{'已检出' if bool(event_df.loc[idx, 'detected']) else '未检出'} | "
            f"单通道={'是' if bool(event_df.loc[idx, 'detected_single_channel']) else '否'} | "
            f"双通道={'是' if bool(event_df.loc[idx, 'detected_paired_channel']) else '否'} | "
            f"最佳峰高={event_df.loc[idx, 'best_peak_height']:.3e}"
        ),
        key="nd_selected_event",
    )
    trace_df = build_event_trace_dataframe(case, selected_event)

    event_row = event_df.loc[selected_event]
    quick_cols = st.columns(6)
    quick_cols[0].metric("当前事件", f"{selected_event + 1}")
    quick_cols[1].metric("是否检出", "是" if bool(event_row["detected"]) else "否")
    quick_cols[2].metric("检测阈值 (threshold)", f"{event_row['threshold']:.3e}")
    quick_cols[3].metric("最佳峰高 (peak)", f"{event_row['best_peak_height']:.3e}")
    quick_cols[4].metric("单通道判定", "是" if bool(event_row["detected_single_channel"]) else "否")
    quick_cols[5].metric("双通道判定", "是" if bool(event_row["detected_paired_channel"]) else "否")
    st.plotly_chart(_build_trace_figure(trace_df), width="stretch")

    st.subheader("2. 批量结果：到底是整体弱，还是一部分事件掉队")
    st.caption("看什么：先看检出/漏检数量，再看已检出事件的峰高分布。这里主要回答‘问题是普遍存在，还是只发生在边缘事件’。")
    st.plotly_chart(_build_detection_outcome_figure(event_df), width="stretch")
    st.caption(
        "检测上下文："
        f"参考场幅值 (A_ref)={summary['A_ref']:.3e} | "
        f"归一化散射场幅值 (E_sca)={summary['E_sca_normalized']:.3e} | "
        f"单通道检出率={summary.get('single_channel_detection_rate', 0.0):.0%} | "
        f"双通道检出率={summary.get('paired_channel_detection_rate', 0.0):.0%}"
    )

    st.subheader("3. 参数扫描：什么最容易把当前点拖出可检测区")
    st.caption("看什么：固定其余条件，只改一个变量，判断当前 case 最先是被噪声、阈值还是流速拖出可检测区。")
    scan_variable = st.selectbox(
        "扫描变量",
        ["noise_std", "threshold_sigma", "velocity_mm_s"],
        format_func=lambda x: {
            "noise_std": "读出噪声标准差 (noise_std)",
            "threshold_sigma": "阈值倍数 (threshold_sigma)",
            "velocity_mm_s": "流速 (mm/s)",
        }[x],
        key="nd_scan_variable",
    )
    if scan_variable == "noise_std":
        scan_values = tuple(np.round(np.linspace(0.0, 0.08, 9), 4))
    elif scan_variable == "threshold_sigma":
        scan_values = tuple(np.round(np.linspace(2.0, 8.0, 9), 2))
    else:
        scan_values = tuple(np.round(np.linspace(0.05, 0.80, 8), 2))

    scan_df = _detection_scan_cached(
        scan_variable,
        scan_values,
        st.session_state["nd_material"],
        int(st.session_state["nd_diameter_nm"]),
        int(st.session_state["nd_wavelength_nm"]),
        int(st.session_state["nd_width_nm"]),
        int(st.session_state["nd_depth_nm"]),
        float(st.session_state["nd_noise_std"]),
        float(st.session_state["nd_shot_noise_scale"]),
        st.session_state["nd_noise_model"],
        float(st.session_state["nd_drift_slope"]),
        float(st.session_state["nd_post_readout_noise_std"]),
        float(st.session_state["nd_post_readout_drift_slope"]),
        float(st.session_state["nd_threshold_sigma"]),
        float(st.session_state["nd_velocity_mm_s"]),
        bool(st.session_state["nd_include_diffusion"]),
        float(st.session_state["nd_rho"]),
        st.session_state["nd_reference_model"],
        float(st.session_state["nd_ref_alpha"]),
        float(st.session_state["nd_ref_beta"]),
        float(st.session_state["nd_ref_gamma"]),
        st.session_state["nd_coupling_model"],
        st.session_state["nd_detection_decision_mode"],
        st.session_state["nd_readout_model"],
        st.session_state["nd_readout_observable_mode"],
        float(st.session_state["nd_lockin_time_constant_ms"]),
        float(st.session_state["nd_pod_lockin_frequency_Hz"]),
        float(st.session_state["nd_nodi_lockin_frequency_Hz"]),
        float(st.session_state["nd_pod_reference_phase_deg"]),
        float(st.session_state["nd_nodi_reference_phase_deg"]),
        float(st.session_state["nd_pod_to_nodi_crosstalk"]),
        float(st.session_state["nd_nodi_to_pod_crosstalk"]),
        int(st.session_state["nd_beam_waist_y_nm"]),
        defaults["normalization_mode"],
    )
    valid_scan_df = scan_df[scan_df["valid"]].copy()
    st.plotly_chart(_build_scan_figure(valid_scan_df, scan_variable), width="stretch")
    st.markdown("**怎么看这条扫描趋势**")
    for note in _build_detection_scan_notes(valid_scan_df, scan_variable):
        st.caption(note)
