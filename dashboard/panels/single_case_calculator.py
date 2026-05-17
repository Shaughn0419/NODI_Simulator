"""
dashboard/panels/single_case_calculator.py — Standalone single-case calculator
"""

from __future__ import annotations

from copy import deepcopy

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from nodi_simulator.dashboard.config import (
    DEFAULT_SIM_CFG,
    FULL_DIAMETER_VALUES_NM,
    FULL_SWEEP_WAVELENGTHS_NM,
    DEFAULT_REFERENCE_MODEL,
    OPTICAL_TEMPLATE,
    format_particle_label,
    infer_particle_diameter_nm,
    infer_particle_material,
)
from nodi_simulator.dashboard.panels.common import (
    get_selected_case_context,
    render_auxiliary_page_header,
)
from nodi_simulator.dashboard.signal_backend import build_single_case_stage_report


_SINGLE_CASE_WAVELENGTH_OPTIONS = list(FULL_SWEEP_WAVELENGTHS_NM)


def _render_page_style() -> None:
    st.markdown(
        """
<style>
.single-case-metric-card {
  border: 1px solid rgba(49, 51, 63, 0.14);
  border-radius: 0.7rem;
  padding: 0.65rem 0.8rem;
  margin-bottom: 0.5rem;
  background: rgba(250, 250, 252, 0.85);
}
.single-case-metric-label {
  font-size: 0.76rem;
  line-height: 1.2;
  color: rgb(90, 96, 110);
  margin-bottom: 0.25rem;
  word-break: break-word;
}
.single-case-metric-value {
  font-size: 0.92rem;
  line-height: 1.25;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  color: rgb(25, 28, 36);
  word-break: break-word;
}
.single-case-reading-card {
  border-left: 3px solid rgba(59, 130, 246, 0.65);
  padding: 0.35rem 0.6rem 0.35rem 0.75rem;
  margin: 0.2rem 0 0.45rem 0;
  background: rgba(239, 246, 255, 0.55);
  border-radius: 0.4rem;
}
.single-case-reading-title {
  font-size: 0.74rem;
  font-weight: 600;
  color: rgb(55, 65, 81);
  margin-bottom: 0.12rem;
}
.single-case-reading-body {
  font-size: 0.78rem;
  line-height: 1.35;
  color: rgb(31, 41, 55);
}
.single-case-stage-badge {
  display: inline-block;
  margin-left: 0.45rem;
  padding: 0.08rem 0.45rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  vertical-align: middle;
}
.single-case-stage-badge.primary {
  background: rgba(37, 99, 235, 0.12);
  color: rgb(29, 78, 216);
}
.single-case-stage-badge.secondary {
  background: rgba(107, 114, 128, 0.12);
  color: rgb(75, 85, 99);
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _default_diameter_for_material(material: str) -> int:
    return 100 if material == "exosome" else 80


def _seed_single_case_state(*, force_from_workflow: bool = False) -> None:
    """Seed tool-specific state from the workflow selection without mutating it back."""
    selected_particle = st.session_state.get("selected_particle")
    inferred_material = (
        infer_particle_material(selected_particle) if selected_particle else None
    )
    inferred_diameter = (
        infer_particle_diameter_nm(selected_particle) if selected_particle else None
    )
    default_material = (
        inferred_material if inferred_material in {"gold", "exosome"} else "exosome"
    )
    default_diameter = (
        int(inferred_diameter)
        if inferred_material == default_material and inferred_diameter is not None
        else _default_diameter_for_material(default_material)
    )
    defaults = {
        "single_case_material": default_material,
        "single_case_diameter_nm": default_diameter,
        "single_case_wavelength_nm": int(
            st.session_state.get("selected_wavelength_nm") or 660
        ),
        "single_case_width_nm": int(st.session_state.get("selected_W_nm") or 1000),
        "single_case_depth_nm": int(st.session_state.get("selected_H_nm") or 550),
        "single_case_n_events": int(st.session_state.get("single_case_n_events") or 12),
        "single_case_rho": (
            float(st.session_state["single_case_rho"])
            if st.session_state.get("single_case_rho") is not None
            else float(DEFAULT_SIM_CFG.rho)
        ),
        "single_case_include_diffusion": (
            bool(st.session_state["single_case_include_diffusion"])
            if st.session_state.get("single_case_include_diffusion") is not None
            else bool(DEFAULT_SIM_CFG.include_diffusion)
        ),
        "single_case_noise_std": (
            float(st.session_state["single_case_noise_std"])
            if st.session_state.get("single_case_noise_std") is not None
            else float(DEFAULT_SIM_CFG.noise_std)
        ),
        "single_case_threshold_sigma": (
            float(st.session_state["single_case_threshold_sigma"])
            if st.session_state.get("single_case_threshold_sigma") is not None
            else float(DEFAULT_SIM_CFG.threshold_sigma)
        ),
        "single_case_velocity_mm_s": (
            float(st.session_state["single_case_velocity_mm_s"])
            if st.session_state.get("single_case_velocity_mm_s") is not None
            else float(DEFAULT_SIM_CFG.mean_flow_velocity_m_s * 1e3)
        ),
    }
    for key, value in defaults.items():
        if force_from_workflow or st.session_state.get(key) is None:
            st.session_state[key] = value

    # Clamp persisted values into the widget ranges used on this page so
    # old session state does not trigger widget-range errors.
    st.session_state["single_case_rho"] = min(
        30.0, max(1.0, float(st.session_state["single_case_rho"]))
    )
    st.session_state["single_case_noise_std"] = min(
        0.1, max(0.0, float(st.session_state["single_case_noise_std"]))
    )
    st.session_state["single_case_threshold_sigma"] = min(
        10.0, max(3.0, float(st.session_state["single_case_threshold_sigma"]))
    )
    st.session_state["single_case_velocity_mm_s"] = min(
        1.0, max(0.05, float(st.session_state["single_case_velocity_mm_s"]))
    )


def _build_single_case_report_from_state() -> dict[str, object]:
    """Build one single-case report using tool-local session state only."""
    sim_cfg = deepcopy(DEFAULT_SIM_CFG)
    sim_cfg.rho = float(st.session_state["single_case_rho"])
    sim_cfg.noise_std = float(st.session_state["single_case_noise_std"])
    sim_cfg.threshold_sigma = float(st.session_state["single_case_threshold_sigma"])
    sim_cfg.include_diffusion = bool(st.session_state["single_case_include_diffusion"])
    sim_cfg.mean_flow_velocity_m_s = (
        float(st.session_state["single_case_velocity_mm_s"]) * 1e-3
    )
    sim_cfg.n_events = int(st.session_state["single_case_n_events"])
    optical = deepcopy(OPTICAL_TEMPLATE)
    optical.wavelength_m = float(st.session_state["single_case_wavelength_nm"]) * 1e-9
    return build_single_case_stage_report(
        material=str(st.session_state["single_case_material"]),
        diameter_nm=int(st.session_state["single_case_diameter_nm"]),
        wavelength_nm=int(st.session_state["single_case_wavelength_nm"]),
        width_nm=int(st.session_state["single_case_width_nm"]),
        depth_nm=int(st.session_state["single_case_depth_nm"]),
        sim_cfg=sim_cfg,
        optical_template=optical,
        n_events=int(st.session_state["single_case_n_events"]),
    )


def _build_trace_figure(df, *, y_columns: list[tuple[str, str]], title: str, yaxis_title: str):
    fig = go.Figure()
    for column, name in y_columns:
        if column in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df["time_ms"],
                    y=df[column],
                    mode="lines",
                    name=name,
                )
            )
    fig.update_layout(
        title=title,
        xaxis_title="时间 (ms)",
        yaxis_title=yaxis_title,
        height=320,
        margin={"l": 20, "r": 20, "t": 50, "b": 20},
    )
    return fig


def _add_trace_marker(fig: go.Figure, x_value: float | None) -> go.Figure:
    if x_value is not None and np.isfinite(float(x_value)):
        fig.add_vline(
            x=float(x_value),
            line_dash="dash",
            line_color="#ef4444",
        )
    return fig


def _render_trace_stage_chart(
    df: pd.DataFrame,
    *,
    y_columns: list[tuple[str, str]],
    title: str,
    yaxis_title: str,
    vline_x: float | None = None,
) -> None:
    fig = _build_trace_figure(
        df,
        y_columns=y_columns,
        title=title,
        yaxis_title=yaxis_title,
    )
    st.plotly_chart(_add_trace_marker(fig, vline_x), width="stretch")


def _looks_numeric_text(value: str) -> bool:
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def _format_scientific_value(value: object) -> str:
    if isinstance(value, (int, np.integer)):
        return f"{int(value)}"
    if isinstance(value, (float, np.floating)):
        value_f = float(value)
        if not np.isfinite(value_f):
            return str(value)
        abs_value = abs(value_f)
        if abs_value == 0.0:
            return "0"
        if abs_value >= 1e3 or abs_value < 1e-2:
            return f"{value_f:.3e}"
        return f"{value_f:.4f}".rstrip("0").rstrip(".")
    text = str(value)
    stripped = text.strip()
    if stripped.endswith("%"):
        try:
            number = float(stripped[:-1])
        except ValueError:
            return text
        return f"{number:.1f}%"
    if any(unit in stripped for unit in (" rad", " deg", " nm", " ms", " m²", " m/s")):
        number_text, unit = stripped.split(" ", 1)
        if _looks_numeric_text(number_text):
            return f"{_format_scientific_value(float(number_text))} {unit}"
        return text
    if _looks_numeric_text(stripped):
        return _format_scientific_value(float(stripped))
    return text


def _render_metric_grid(metrics: dict[str, object]) -> None:
    items = list(metrics.items())
    if not items:
        return
    n_cols = min(3, max(1, len(items)))
    cols = st.columns(n_cols)
    for idx, (label, value) in enumerate(items):
        with cols[idx % n_cols]:
            st.markdown(
                (
                    '<div class="single-case-metric-card">'
                    f'<div class="single-case-metric-label">{label}</div>'
                    f'<div class="single-case-metric-value">{_format_scientific_value(value)}</div>'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )


def _render_stage_reading(reading: dict[str, str] | None) -> None:
    if not reading:
        return
    mapping = [
        ("关键看什么", reading.get("key", "")),
        ("当前怎么判断", reading.get("judgment", "")),
        ("先警惕什么", reading.get("caution", "")),
    ]
    for title, body in mapping:
        if not body:
            continue
        st.markdown(
            (
                '<div class="single-case-reading-card">'
                f'<div class="single-case-reading-title">{title}</div>'
                f'<div class="single-case-reading-body">{body}</div>'
                "</div>"
            ),
            unsafe_allow_html=True,
        )


def _format_dataframe_for_display(df):
    if df.empty:
        return df
    styled = df.copy()
    for column in styled.columns:
        if np.issubdtype(styled[column].dtype, np.floating):
            max_abs = float(np.nanmax(np.abs(styled[column].to_numpy(dtype=float)))) if styled[column].notna().any() else 0.0
            if max_abs >= 1e3 or (0.0 < max_abs < 1e-2):
                styled[column] = styled[column].map(
                    lambda x: "" if pd.isna(x) else f"{float(x):.3e}"
                )
            else:
                styled[column] = styled[column].map(
                    lambda x: "" if pd.isna(x) else f"{float(x):.4f}".rstrip("0").rstrip(".")
                )
        elif np.issubdtype(styled[column].dtype, np.integer):
            styled[column] = styled[column].map(lambda x: "" if pd.isna(x) else str(int(x)))
    return styled


def _render_stage(stage: dict[str, object], *, right_render=None) -> None:
    badge_class = "primary" if stage.get("priority") == "primary" else "secondary"
    badge_label = stage.get("priority_label", "主线")
    st.markdown(
        (
            f"### {stage['title']}"
            f"<span class='single-case-stage-badge {badge_class}'>{badge_label}</span>"
        ),
        unsafe_allow_html=True,
    )
    left, right = st.columns([0.42, 0.58])
    with left:
        st.markdown("**这个阶段在算什么**")
        principle = stage.get("principle")
        if isinstance(principle, (list, tuple)):
            for line in principle:
                st.caption(f"- {line}")
    with right:
        st.markdown("**当前计算结果**")
        metrics = stage.get("metrics")
        if isinstance(metrics, dict):
            metrics_str = {str(key): value for key, value in metrics.items() if isinstance(key, str)}
            if metrics_str:
                _render_metric_grid(metrics_str)
        reading = stage.get("reading")
        if isinstance(reading, dict):
            str_reading = {
                str(key): str(value)
                for key, value in reading.items()
                if isinstance(key, str)
            }
            _render_stage_reading(str_reading if str_reading else None)
        if callable(right_render):
            right_render()
        st.info(str(stage["conclusion"]))


def render_single_case_calculator() -> None:
    """Render the standalone tool page without mutating workflow selections."""
    _render_page_style()
    st.header("Single-Case Calculator — 单案例全链路计算")
    st.caption("这是一页独立计算页：输入一个具体 case，直接看从本征散射到 detect/miss 与最终判断的完整现场重算链。")
    _seed_single_case_state()
    render_auxiliary_page_header(
        summary_message="它不会改变科研展示主线围绕标准 biomimetic full-range 主结果库的分析叙事。",
        detail_message="如果科研展示或证据页已经选中了一个 case，本页可以把它当作默认值或导入参考，但不会自动回写主线选中 case。",
    )

    workflow_context = get_selected_case_context()
    if workflow_context is not None:
        cols = st.columns([0.72, 0.28])
        with cols[0]:
            st.caption("如果你想复盘科研展示里的某个 case，可以先导入它作为本页默认值，再单独改参数做现场重算。")
        with cols[1]:
            if st.button("导入科研展示选中 case", width="stretch"):
                _seed_single_case_state(force_from_workflow=True)
                st.session_state["single_case_stage_report"] = None
                st.rerun()

    with st.form("single_case_calculator_form"):
        st.markdown("## 输入参数")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.selectbox(
                "粒子类型",
                ["exosome", "gold"],
                key="single_case_material",
            )
            st.selectbox(
                "粒径 (nm)",
                FULL_DIAMETER_VALUES_NM,
                key="single_case_diameter_nm",
            )
        with c2:
            st.selectbox(
                "激光波长 (nm)",
                _SINGLE_CASE_WAVELENGTH_OPTIONS,
                key="single_case_wavelength_nm",
            )
            st.number_input(
                "通道宽度 W (nm)",
                min_value=300,
                max_value=3000,
                step=100,
                key="single_case_width_nm",
            )
        with c3:
            st.number_input(
                "通道深度 H (nm)",
                min_value=300,
                max_value=3000,
                step=100,
                key="single_case_depth_nm",
            )
            st.number_input(
                "batch 事件数",
                min_value=4,
                max_value=60,
                step=2,
                key="single_case_n_events",
            )
        st.markdown("## 关键计算参数")
        a1, a2, a3 = st.columns(3)
        with a1:
            st.slider(
                "rho",
                1.0,
                30.0,
                step=0.5,
                key="single_case_rho",
            )
            st.checkbox(
                "启用扩散/布朗运动",
                key="single_case_include_diffusion",
            )
        with a2:
            st.slider(
                "噪声标准差 (noise_std)",
                0.0,
                0.1,
                step=0.005,
                key="single_case_noise_std",
            )
            st.slider(
                "阈值 sigma",
                3.0,
                10.0,
                step=0.5,
                key="single_case_threshold_sigma",
            )
        with a3:
            st.slider(
                "平均流速 (mm/s)",
                0.05,
                1.0,
                step=0.05,
                key="single_case_velocity_mm_s",
            )
            st.caption(f"reference model: `{DEFAULT_REFERENCE_MODEL}`")

        submitted = st.form_submit_button("计算单案例", width="stretch")

    if submitted:
        with st.spinner("正在执行单案例计算..."):
            st.session_state["single_case_stage_report"] = _build_single_case_report_from_state()

    report = st.session_state.get("single_case_stage_report")
    if not report:
        st.info("先填写一个具体 case，再点击“计算单案例”查看完整链路。")
        return

    meta = report["meta"]
    particle_label = format_particle_label(meta["material"], meta["diameter_nm"])
    headline = report["headline"]
    tone_map = {
        "success": st.success,
        "warning": st.warning,
        "error": st.error,
        "info": st.info,
    }

    st.markdown("## 本页结论")
    tone_map.get(headline["tone"], st.info)(
        f"{headline['headline']}：{headline['primary_message']}"
    )
    if headline.get("badge"):
        st.caption(f"当前状态：{headline['badge']}")
    ordered_stages = report["stages"]
    stages = {stage["id"]: stage for stage in ordered_stages}
    interference_trace_df = report["interference_trace_df"]
    event_trace_df = report["event_trace_df"]
    event_table_df = report["event_table_df"]
    interference_case = report["interference_case"]
    selected_event_index = int(report["selected_event_index"])

    st.caption(
        f"当前计算：{particle_label} | λ={meta['wavelength_nm']} nm | "
        f"W={meta['width_nm']} nm | H={meta['depth_nm']} nm | "
        f"batch={meta['n_events']} events | 下一步建议：{headline['next_step']}"
    )
    st.markdown("## 主要阶段")

    _render_stage(stages["input"])

    def render_mie_plot():
        theta_deg = np.degrees(interference_case["inputs"]["intrinsic"]["theta_grid_rad"])
        dcs = interference_case["inputs"]["intrinsic"]["dCsca_dOmega_m2_sr"]
        theta_det_deg = float(interference_case["summary"].get("theta_det_deg", np.nan))
        theta_center_deg = float(interference_case["summary"].get("theta_center_deg", np.nan))
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=theta_deg, y=dcs, mode="lines", name="角分布散射截面"))
        if np.isfinite(theta_det_deg):
            fig.add_vline(x=theta_det_deg, line_dash="dash", line_color="#2563eb")
            fig.add_annotation(
                x=theta_det_deg,
                y=float(np.nanmax(dcs)),
                text="theta_det",
                showarrow=False,
                yshift=-12,
                font={"size": 10, "color": "#2563eb"},
            )
        if np.isfinite(theta_center_deg) and abs(theta_center_deg - theta_det_deg) > 1e-6:
            fig.add_vline(x=theta_center_deg, line_dash="dot", line_color="#6b7280")
            fig.add_annotation(
                x=theta_center_deg,
                y=float(np.nanmax(dcs)),
                text="theta_center",
                showarrow=False,
                yshift=12,
                font={"size": 10, "color": "#6b7280"},
            )
        fig.update_layout(
            height=280,
            margin={"l": 20, "r": 20, "t": 30, "b": 20},
            xaxis_title="散射角 theta (deg)",
            yaxis_title="dCsca/dΩ (m²/sr)",
        )
        st.plotly_chart(fig, width="stretch")

    _render_stage(stages["mie"], right_render=render_mie_plot)
    _render_stage(stages["reference"])

    _render_stage(
        stages["interference"],
        right_render=lambda: _render_trace_stage_chart(
            interference_trace_df,
            y_columns=[
                ("clean_signal", "clean signal"),
                ("cross_term", "cross-term"),
                ("sca_only_term", "|E_sca|^2"),
            ],
            title="干涉 clean trace",
            yaxis_title="signal (a.u.)",
            vline_x=float(interference_case["summary"].get("peak_time_ms", np.nan)),
        ),
    )

    noisy_peak_time_ms = None
    if not event_trace_df.empty and "signal_noisy" in event_trace_df.columns:
        noisy_peak_time_ms = float(
            event_trace_df.loc[
                event_trace_df["signal_noisy"].abs().idxmax(),
                "time_ms",
            ]
        )

    _render_stage(
        stages["readout"],
        right_render=lambda: _render_trace_stage_chart(
            event_trace_df,
            y_columns=[
                ("clean_signal", "clean"),
                ("signal_noisy", "noisy"),
                ("threshold", "threshold"),
            ],
            title=f"事件 {selected_event_index} 的读出轨迹",
            yaxis_title="signal (a.u.)",
            vline_x=noisy_peak_time_ms,
        ),
    )

    def render_batch_summary():
        st.caption("这里展示 batch 统计和前几个事件的代表性读数。")
        preferred_columns = [
            col
            for col in [
                "event_index",
                "detected",
                "peak_height",
                "peak_height_abs",
                "local_snr",
                "peak_margin_z",
                "phase_flip",
            ]
            if col in event_table_df.columns
        ]
        st.dataframe(
            _format_dataframe_for_display(event_table_df[preferred_columns].head(8)),
            width="stretch",
            hide_index=True,
        )

    _render_stage(stages["batch"], right_render=render_batch_summary)
    _render_stage(stages["decision"])
