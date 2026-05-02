"""
dashboard/panels/mie_explorer.py — Pure Mie scattering explorer

Focuses on intrinsic Mie scattering only:
    - Integrated cross sections / efficiencies vs diameter
    - Angular distributions dCsca/dOmega, |S1|, |S2|
    - Single-case physics readout
"""

from __future__ import annotations

import os

import numpy as np
import plotly.graph_objects as go
import streamlit as st

from nodi_simulator.dashboard.backend import (
    load_workflow_case_anchor,
)
from nodi_simulator.dashboard.config import (
    DASHBOARD_DIAMETER_STEP_NM,
    DASHBOARD_DIAMETER_VALUES_NM,
    DEFAULT_DASHBOARD_DIAMETER_NM,
    DIAMETER_RANGE_NM,
    FULL_SWEEP_WAVELENGTHS_NM,
    MATERIAL_OPTIONS,
    MATERIAL_PHYSICS_LABELS,
    diameter_values_between,
    format_particle_label,
    infer_particle_diameter_nm,
    infer_particle_material,
    snap_diameter_nm,
)
from nodi_simulator.dashboard.mie_backend import (
    build_mie_single_variable_scan_dataframe,
    build_mie_summary_dataframe,
    compute_mie_case,
)
from nodi_simulator.dashboard.panels.common import (
    render_workflow_case_source_panel,
    render_page_header_hub,
)


MIE_METRIC_LABELS = {
    "Csca_m2": "散射截面 (Csca, m^2)",
    "Cext_m2": "消光截面 (Cext, m^2)",
    "Cabs_m2": "吸收截面 (Cabs, m^2)",
    "Qsca": "散射效率 (Qsca)",
    "Qext": "消光效率 (Qext)",
    "Qabs": "吸收效率 (Qabs)",
    "dCsca_dOmega_at_theta_m2_sr": "固定角散射截面 (dCsca/dOmega @ theta_fixed, m^2/sr)",
    "Esca_unit_amp_at_theta_m": "固定角散射场幅值 (Esca @ theta_fixed, m)",
    "size_parameter": "尺寸参数 x",
}
MIE_WAVELENGTH_OPTIONS = list(FULL_SWEEP_WAVELENGTHS_NM)
RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "results",
)


@st.cache_data(show_spinner=False)
def _summary_df_cached(
    materials: tuple[str, ...],
    diameters_nm: tuple[int, ...],
    wavelengths_nm: tuple[int, ...],
    summary_theta_deg: float,
):
    return build_mie_summary_dataframe(
        list(materials),
        list(diameters_nm),
        list(wavelengths_nm),
        summary_theta_deg=summary_theta_deg,
    )


def _metric_label(metric: str, summary_theta_deg: float) -> str:
    label = MIE_METRIC_LABELS[metric]
    if "theta_fixed" in label:
        return label.replace("theta_fixed", f"{summary_theta_deg:.1f} deg")
    return label


def _build_line_figure(
    df,
    metric: str,
    title: str,
    log_y: bool,
    summary_theta_deg: float,
) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        return fig

    for (material, wavelength_nm), sub_df in df.groupby(["material", "wavelength_nm"]):
        fig.add_trace(go.Scatter(
            x=sub_df["diameter_nm"],
            y=sub_df[metric],
            mode="lines",
            name=f"{material}, {int(round(wavelength_nm))} nm",
        ))

    fig.update_layout(
        title=title,
        xaxis_title="粒径 (nm)",
        yaxis_title=_metric_label(metric, summary_theta_deg),
        yaxis_type="log" if log_y else "linear",
        height=420,
    )
    return fig


def _build_single_variable_scan_figure(
    df,
    x_col: str,
    y_col: str,
    title: str,
    log_y: bool,
    summary_theta_deg: float,
) -> go.Figure:
    fig = go.Figure()
    if df.empty:
        return fig

    fig.add_trace(go.Scatter(
        x=df[x_col],
        y=df[y_col],
        mode="lines+markers",
        name=title,
    ))
    axis_title_map = {
        "wavelength_nm": "波长 (nm)",
        "diameter_nm": "粒径 (nm)",
        "relative_index_real": "相对折射率实部",
    }
    axis_title = axis_title_map.get(x_col, x_col)
    fig.update_layout(
        title=title,
        xaxis_title=axis_title,
        yaxis_title=_metric_label(y_col, summary_theta_deg),
        yaxis_type="log" if log_y else "linear",
        height=380,
    )
    return fig


def _build_overview_trend_note(df, metric: str, summary_theta_deg: float) -> list[str]:
    if df.empty:
        return ["当前没有可用数据，无法生成趋势解读。"]

    group_increase_flags = []
    for _, sub_df in df.groupby(["material", "wavelength_nm"]):
        sub_df = sub_df.sort_values("diameter_nm")
        if len(sub_df) < 2:
            continue
        start = float(sub_df.iloc[0][metric])
        end = float(sub_df.iloc[-1][metric])
        if np.isfinite(start) and np.isfinite(end):
            group_increase_flags.append(end > start)

    trend_line = "当前筛选范围太窄，还看不出稳定的粒径趋势。"
    if group_increase_flags:
        increase_fraction = sum(group_increase_flags) / len(group_increase_flags)
        if increase_fraction >= 0.8:
            trend_line = "总体趋势：大多数材料-波长组合下，曲线都会随粒径增大而上升。也就是说，变大的粒子通常先天更容易产生更强散射。"
        elif increase_fraction <= 0.2:
            trend_line = "总体趋势：大多数材料-波长组合下，曲线会随粒径增大而下降。说明你现在看的更像效率指标，而不是绝对散射量。"
        else:
            trend_line = "总体趋势：不同材料或波长的曲线会交叉，说明“粒径越大越好”并不是在所有组合下都成立。"

    if metric in {"Csca_m2", "Cext_m2", "Cabs_m2"}:
        metric_line = (
            "怎么读：这张图的纵轴是总截面。曲线越高，表示粒子整体把更多光散出去或消光掉；"
            "看同一粒径处哪条曲线更高，就表示哪种材料/波长的本征总响应更强。横向沿着一条曲线看，"
            "是在回答‘粒径继续变大时，总散射量会不会继续上升’。"
        )
    elif metric in {"Qsca", "Qext", "Qabs"}:
        metric_line = (
            "怎么读：这张图的纵轴是效率因子，也就是“单位几何面积有多会散射/吸收”。"
            "它适合比较材料或尺寸是不是进入了更高效的散射区。纵向比高低是在看谁更高效，"
            "横向看斜率是在看粒径变大后效率是在继续爬升、开始饱和，还是已经回落。"
        )
    else:
        metric_line = (
            f"怎么读：这张图已经是固定角度 `{summary_theta_deg:.1f} deg` 的方向性量。"
            "曲线越高，表示该检测方向实际收到的散射越强，因此比总截面更贴近后续系统检测。"
            "同一粒径下看哪条更高，是在比较哪个材料/波长更适合当前检测方向。"
        )

    good_trend_line = (
        "什么趋势更好：如果你的目标是后续 NODI 检测，优先关注“同一粒径下固定角度方向量更高”的曲线；"
        "如果只是想比较粒子本征总散射能力，再看总截面曲线。"
    )
    compare_line = (
        "读图顺序：先纵向比较同一粒径处谁更高，再横向看单条曲线随粒径怎么变。"
        "前者回答‘谁更强’，后者回答‘变大之后会不会继续变好’。"
    )
    return [trend_line, metric_line, compare_line, good_trend_line]


def _build_overview_reading_frame(metric: str, summary_theta_deg: float) -> tuple[str, str, str]:
    if metric in {"Csca_m2", "Cext_m2", "Cabs_m2"}:
        return (
            "先回答什么",
            "先回答粒子本征总响应谁更强。",
            "对后续检测的直接性较弱；如果下一步是看系统检出，记得再去看固定角度量。",
        )
    if metric in {"Qsca", "Qext", "Qabs"}:
        return (
            "先回答什么",
            "先回答哪组材料/粒径更高效，而不是谁的绝对散射量最大。",
            "效率高不等于探测器收到的信号一定最大，后面仍要看方向量。",
        )
    return (
        "先回答什么",
        f"先回答固定检测角 `{summary_theta_deg:.1f}°` 方向上谁更强，这最接近后续系统真的会收到什么。",
        "如果这里和总截面结论不一致，优先相信方向量，因为系统不是收全空间散射。",
    )


def _closest_wavelength_option(wavelength_nm: int | float | None) -> int:
    if wavelength_nm is None:
        return 660
    wavelength_nm = float(wavelength_nm)
    return min(MIE_WAVELENGTH_OPTIONS, key=lambda value: abs(value - wavelength_nm))


def _resolve_linked_mie_defaults(
    particle_name: str | None,
    wavelength_nm: int | float | None,
) -> dict[str, object]:
    material = infer_particle_material(particle_name) if particle_name else "gold"
    if material not in MATERIAL_OPTIONS:
        material = "gold"

    diameter_nm = infer_particle_diameter_nm(particle_name) if particle_name else None
    if diameter_nm is None:
        diameter_nm = DEFAULT_DASHBOARD_DIAMETER_NM
    diameter_nm = snap_diameter_nm(diameter_nm)

    wavelength_option = _closest_wavelength_option(wavelength_nm)
    return {
        "material": material,
        "diameter_nm": diameter_nm,
        "wavelength_nm": wavelength_option,
    }


def _apply_linked_defaults(force: bool = False) -> dict[str, object]:
    linked_defaults = _resolve_linked_mie_defaults(
        st.session_state.get("selected_particle"),
        st.session_state.get("selected_wavelength_nm"),
    )
    key_defaults = {
        "mie_materials": [linked_defaults["material"]],
        "mie_overview_wavelengths": [linked_defaults["wavelength_nm"]],
        "mie_angular_materials": [linked_defaults["material"]],
        "mie_angular_diameters": [linked_defaults["diameter_nm"]],
        "mie_angular_wavelengths": [linked_defaults["wavelength_nm"]],
        "mie_scan_material": linked_defaults["material"],
        "mie_scan_fixed_diameter": linked_defaults["diameter_nm"],
        "mie_scan_fixed_wavelength": linked_defaults["wavelength_nm"],
        "mie_detail_material": linked_defaults["material"],
        "mie_detail_diameter": linked_defaults["diameter_nm"],
        "mie_detail_wavelength": linked_defaults["wavelength_nm"],
    }
    for key, value in key_defaults.items():
        if force or key not in st.session_state:
            st.session_state[key] = value
    return linked_defaults


def render_mie_explorer():
    """Render the pure Mie scattering page."""
    linked_defaults = _apply_linked_defaults(force=False)
    anchor_row, anchor_prefix = load_workflow_case_anchor(RESULTS_DIR, st.session_state)
    selected_case_exists = st.session_state.get("selected_particle") is not None

    st.header("Mie Explorer — 纯 Mie 散射结果")
    st.caption("这一页只解释标准结果库当前 case 的本征散射起点，不把 reference、noise 和 gate 混在一起。")
    render_page_header_hub("Mie Explorer", geometry_is_context_only=True)
    linked_label = format_particle_label(
        linked_defaults["material"],
        linked_defaults["diameter_nm"],
    )
    render_workflow_case_source_panel(
        anchor_row=anchor_row,
        anchor_prefix=anchor_prefix,
        selected_case_exists=selected_case_exists,
        selected_case_caption=(
            f"跨页联动：当前默认沿用最近选中的 case，即 {linked_label}, "
            f"λ≈{linked_defaults['wavelength_nm']} nm。"
        ),
        empty_case_caption="当前还没有跨页选点记录；Mie 页面会先使用自己的默认参数。",
        primary_metric_label="检出率",
        primary_metric_value=f"{float(anchor_row.get('detection_rate', 0.0)):.0%}" if anchor_row is not None else "N/A",
        explanation="这页负责解释标准结果库中当前 case 的本征散射起点，再把结论交给 reference、noise 和 gate 页面继续接力。",
        missing_anchor_warning="当前 session 有跨页选点，但标准结果库里还没定位到对应 case；建议先回 `Design Explorer / Case Inspector` 重新确认。",
        no_selection_info="当前还没有跨页选中的 case。若你想沿主流程看，请先去 `Design Explorer` 选一个 case 再回来。",
        is_live=bool(st.session_state.get("using_live_data")),
        live_tag=st.session_state.get("live_tag"),
        data_prefix=st.session_state.get("data_prefix"),
        standard_message="当前主流程正在围绕标准 biomimetic full-range 主结果库解释本征散射。",
        live_message="当前 session 带有工程调试 live 参数；这里仍建议把它当成排查辅助，而不是新的主流程结论。",
    )

    with st.sidebar:
        st.header("Mie 参数")
        if st.session_state.get("selected_particle") is not None:
            st.caption(f"最近来自 Explorer / Inspector 的选点：{linked_label}, λ≈{linked_defaults['wavelength_nm']} nm")
            if st.button("同步当前选点到 Mie 参数", key="mie_sync_from_selected"):
                _apply_linked_defaults(force=True)
                st.rerun()
        else:
            st.caption("当前还没有跨页选点记录；Mie 页面会先使用自己的默认参数。")
        st.caption("这里只保留主流程最常用的本征散射阅读控件；角分布、折射率和偏振细查先整体退场。")
        overview_materials = st.multiselect(
            "材料类型",
            MATERIAL_OPTIONS,
            format_func=lambda x: MATERIAL_PHYSICS_LABELS.get(x, x),
            key="mie_materials",
        )
        diameter_min, diameter_max = st.slider(
            "粒径范围 (nm)",
            DIAMETER_RANGE_NM[0],
            DIAMETER_RANGE_NM[1],
            DIAMETER_RANGE_NM,
            step=DASHBOARD_DIAMETER_STEP_NM,
            key="mie_diameter_range",
        )
        overview_wavelengths = st.multiselect(
            "波长 (nm)",
            MIE_WAVELENGTH_OPTIONS,
            key="mie_overview_wavelengths",
        )
        summary_theta_deg = st.slider(
            "总览固定角度 theta (deg)",
            0.5,
            179.5,
            90.0,
            0.5,
            key="mie_summary_theta_deg",
        )
        overview_metric = st.selectbox(
            "总览指标",
            list(MIE_METRIC_LABELS.keys()),
            index=0,
            format_func=lambda x: _metric_label(x, summary_theta_deg),
            key="mie_metric",
        )
        log_y = st.checkbox("Y 轴使用对数尺度", value=True, key="mie_log_y")

        st.divider()
        scan_material = st.selectbox(
            "扫描材料",
            MATERIAL_OPTIONS,
            index=0,
            format_func=lambda x: MATERIAL_PHYSICS_LABELS.get(x, x),
            key="mie_scan_material",
        )
        scan_variable = st.selectbox(
            "扫描变量",
            ["wavelength_nm", "diameter_nm"],
            index=0,
            format_func=lambda x: "波长 (nm)" if x == "wavelength_nm" else "粒径 (nm)",
            key="mie_scan_variable",
        )
        scan_theta_deg = st.slider(
            "扫描固定角度 theta (deg)",
            0.5,
            179.5,
            90.0,
            0.5,
            key="mie_scan_theta_deg",
        )
        scan_fixed_diameter = st.slider(
            "扫描固定粒径 (nm)",
            DIAMETER_RANGE_NM[0],
            DIAMETER_RANGE_NM[1],
            value=int(st.session_state["mie_scan_fixed_diameter"]),
            step=DASHBOARD_DIAMETER_STEP_NM,
            key="mie_scan_fixed_diameter",
        )
        scan_fixed_wavelength = st.slider(
            "扫描固定波长 (nm)",
            400,
            700,
            532,
            1,
            key="mie_scan_fixed_wavelength",
        )
        scan_metric = st.selectbox(
            "扫描指标",
            ["dCsca_dOmega_at_theta_m2_sr", "Esca_unit_amp_at_theta_m", "Csca_m2", "Qsca"],
            index=0,
            format_func=lambda x: _metric_label(x, scan_theta_deg),
            key="mie_scan_metric",
        )

        st.divider()
        detail_material = st.selectbox(
            "明细材料",
            MATERIAL_OPTIONS,
            index=0,
            format_func=lambda x: MATERIAL_PHYSICS_LABELS.get(x, x),
            key="mie_detail_material",
        )
        detail_diameter = st.slider(
            "明细粒径 (nm)",
            DIAMETER_RANGE_NM[0],
            DIAMETER_RANGE_NM[1],
            value=int(st.session_state["mie_detail_diameter"]),
            step=DASHBOARD_DIAMETER_STEP_NM,
            key="mie_detail_diameter",
        )
        detail_wavelength = st.selectbox(
            "明细波长 (nm)",
            MIE_WAVELENGTH_OPTIONS,
            index=2,
            key="mie_detail_wavelength",
        )

    if not overview_materials:
        st.info("请至少选择一种材料。")
        return
    if not overview_wavelengths:
        st.info("请至少选择一种波长。")
        return

    diameters_nm = tuple(diameter_values_between(diameter_min, diameter_max))
    summary_df = _summary_df_cached(
        tuple(overview_materials),
        diameters_nm,
        tuple(overview_wavelengths),
        summary_theta_deg,
    )

    metric_higher_is_better = overview_metric not in {"CV"}
    ordered_summary_df = summary_df.sort_values(
        overview_metric,
        ascending=not metric_higher_is_better,
    ).reset_index(drop=True)
    best_row = ordered_summary_df.iloc[0]
    worst_row = ordered_summary_df.iloc[-1]
    best_value = float(best_row[overview_metric])
    worst_value = float(worst_row[overview_metric])
    spread_ratio = (
        best_value / worst_value if abs(worst_value) > 1e-30 and metric_higher_is_better
        else (worst_value / best_value if abs(best_value) > 1e-30 else np.inf)
    )

    st.markdown("### 本页结论")
    if metric_higher_is_better:
        st.info(
            f"在当前筛选范围内，`{best_row['material']}` 在 λ={int(best_row['wavelength_nm'])} nm、"
            f"粒径={int(best_row['diameter_nm'])} nm 时的 `{_metric_label(overview_metric, summary_theta_deg)}` 最高。"
        )
    else:
        st.info(
            f"在当前筛选范围内，`{best_row['material']}` 在 λ={int(best_row['wavelength_nm'])} nm、"
            f"粒径={int(best_row['diameter_nm'])} nm 时的 `{_metric_label(overview_metric, summary_theta_deg)}` 最低。"
        )
    st.caption(
        f"这一轮筛选里最优与最弱 case 的量级差约为 {spread_ratio:.2f}×；"
        "如果后面系统页的结论和这里不一致，要优先怀疑 reference / noise / threshold，而不是先怀疑 Mie 本征散射。"
    )

    st.subheader("总览趋势图")
    st.caption("先看同一材料随粒径怎么变，再看同一粒径下不同材料/波长谁更强。这里负责回答“本征散射起点够不够强”。")
    fig_overview = _build_line_figure(
        summary_df,
        overview_metric,
        f"{_metric_label(overview_metric, summary_theta_deg)} 随粒径变化",
        log_y=log_y,
        summary_theta_deg=summary_theta_deg,
    )
    st.plotly_chart(fig_overview, width="stretch")
    _, frame_main, frame_warning = _build_overview_reading_frame(
        overview_metric, summary_theta_deg
    )
    frame_cols = st.columns(3)
    frame_cols[0].markdown("**这张图先回答什么**")
    frame_cols[0].caption(frame_main)
    frame_cols[1].markdown("**先看哪种比较**")
    frame_cols[1].caption("先纵向比同一粒径下谁更高，再横向看单条曲线随粒径怎么变。")
    frame_cols[2].markdown("**最容易误读什么**")
    frame_cols[2].caption(frame_warning)
    for note in _build_overview_trend_note(summary_df, overview_metric, summary_theta_deg):
        st.caption(note)
    st.markdown("**当前范围内的前 6 个 Mie 点**")
    st.dataframe(
        ordered_summary_df[["material", "diameter_nm", "wavelength_nm", overview_metric]].head(6),
        width="stretch",
        hide_index=True,
    )

    st.subheader("单变量固定角度扫描")
    st.caption("固定检测角后只改一个变量，这一块比总览更接近实验调参。")
    if scan_variable == "wavelength_nm":
        scan_values = np.arange(400, 701, 5, dtype=float)
        scan_df = build_mie_single_variable_scan_dataframe(
            scan_variable=scan_variable,
            material=scan_material,
            scan_values=scan_values,
            fixed_diameter_nm=scan_fixed_diameter,
            fixed_wavelength_nm=scan_fixed_wavelength,
            theta_deg=scan_theta_deg,
        )
        x_col = "wavelength_nm"
        scan_caption = (
            f"{scan_material}, 固定粒径 {scan_fixed_diameter} nm, "
            f"固定角度 {scan_theta_deg:.1f} deg, 扫描 400–700 nm"
        )
    else:
        scan_values = np.asarray(DASHBOARD_DIAMETER_VALUES_NM, dtype=float)
        scan_df = build_mie_single_variable_scan_dataframe(
            scan_variable=scan_variable,
            material=scan_material,
            scan_values=scan_values,
            fixed_diameter_nm=scan_fixed_diameter,
            fixed_wavelength_nm=scan_fixed_wavelength,
            theta_deg=scan_theta_deg,
        )
        x_col = "diameter_nm"
        scan_caption = (
            f"{scan_material}, 固定波长 {scan_fixed_wavelength} nm, "
            f"固定角度 {scan_theta_deg:.1f} deg, 扫描 {DIAMETER_RANGE_NM[0]}–{DIAMETER_RANGE_NM[1]} nm（10 nm 步进）"
        )
    st.caption(scan_caption)
    st.plotly_chart(
        _build_single_variable_scan_figure(
            scan_df,
            x_col=x_col,
            y_col=scan_metric,
            title=f"{_metric_label(scan_metric, scan_theta_deg)} 随 {'波长' if x_col == 'wavelength_nm' else '粒径'} 变化",
            log_y=scan_metric != "Qsca",
            summary_theta_deg=scan_theta_deg,
        ),
        width="stretch",
    )
    st.dataframe(
        scan_df[[
            x_col,
            "theta_deg",
            "size_parameter",
            "Csca_m2",
            "Qsca",
            "dCsca_dOmega_at_theta_m2_sr",
            "Esca_unit_amp_at_theta_m",
        ]],
        width="stretch",
        hide_index=True,
    )

    st.subheader("单点明细")
    st.caption("当你已经选定一个 case，这里只做数值核对，不再挂更多高级图。")
    detail_case = compute_mie_case(
        detail_material,
        detail_diameter,
        detail_wavelength,
    )
    detail_probe_case = compute_mie_case(
        detail_material,
        detail_diameter,
        detail_wavelength,
        theta_grid_deg=np.array([summary_theta_deg]),
    )
    detail_label = format_particle_label(detail_material, detail_diameter)
    st.caption(f"{detail_label}, λ={detail_wavelength} nm")
    cols = st.columns(6)
    cols[0].metric("尺寸参数 (x)", f"{detail_case['size_parameter']:.3f}")
    cols[1].metric("散射截面 (Csca)", f"{detail_case['Csca_m2']:.3e}")
    cols[2].metric("消光截面 (Cext)", f"{detail_case['Cext_m2']:.3e}")
    cols[3].metric("吸收截面 (Cabs)", f"{detail_case['Cabs_m2']:.3e}")
    cols[4].metric("散射效率 (Qsca)", f"{detail_case['Qsca']:.3f}")
    cols[5].metric("消光效率 (Qext)", f"{detail_case['Qext']:.3f}")
    detail_albedo = (
        detail_case["Qsca"] / detail_case["Qext"]
        if detail_case["Qext"] > 1e-30
        else 0.0
    )
    peak_idx = int(np.argmax(detail_case["dCsca_dOmega_m2_sr"]))
    peak_angle_deg = float(detail_case["theta_deg"][peak_idx])
    albedo_cols = st.columns(4)
    albedo_cols[0].metric("散射反照率 ω", f"{detail_albedo:.3f}")
    albedo_cols[1].metric("吸收效率 (Qabs)", f"{detail_case['Qabs']:.3f}")
    albedo_cols[2].metric("最强散射方向 θ_peak", f"{peak_angle_deg:.1f}°")
    albedo_cols[3].metric("当前固定采集角 θ_fixed", f"{summary_theta_deg:.1f}°")
    if abs(peak_angle_deg - summary_theta_deg) > 20.0:
        st.warning(
            f"当前固定采集角 {summary_theta_deg:.1f}° 与该粒子最强散射方向 {peak_angle_deg:.1f}° 偏离较大，"
            "这意味着系统页里的实际收光可能比总散射量看起来更吃亏。"
        )
    st.dataframe(
        [
            {
                "material": detail_case["material"],
                "diameter_nm": detail_case["diameter_nm"],
                "wavelength_nm": detail_case["wavelength_nm"],
                "n_particle_real": detail_case["n_particle_real"],
                "n_particle_imag": detail_case["n_particle_imag"],
                "n_medium": detail_case["n_medium"],
                "relative_index_real": detail_case["relative_index_real"],
                "relative_index_imag": detail_case["relative_index_imag"],
                "geo_cross_m2": detail_case["geo_cross_m2"],
                "Csca_m2": detail_case["Csca_m2"],
                "Cext_m2": detail_case["Cext_m2"],
                "Cabs_m2": detail_case["Cabs_m2"],
                "Qsca": detail_case["Qsca"],
                "Qext": detail_case["Qext"],
                "Qabs": detail_case["Qabs"],
                "summary_theta_deg": summary_theta_deg,
                "dCsca_dOmega_at_theta_m2_sr": float(detail_probe_case["dCsca_dOmega_m2_sr"][0]),
                "Esca_unit_amp_at_theta_m": float(detail_probe_case["Esca_unit_amp"][0]),
            }
        ],
        width="stretch",
        hide_index=True,
    )
