"""
dashboard/panels/explorer.py — Design Explorer 页面

以标准结果库为主线：热图 + 排名 + 切片 + 候选筛选；
工程调试重算 sweep 仅保留为验证入口
"""

import os

import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd

from nodi_simulator.utils import build_case_decision_summary
from nodi_simulator.dashboard.backend import (
    list_available_datasets,
    build_heatmap_matrix,
    build_slice_data,
    recompute_scores,
    build_sim_cfg_from_ui,
    build_optical_from_ui,
    build_live_tag,
    build_local_fine_grid,
    is_standard_dashboard_dataset_prefix,
    load_dashboard_data_bundle,
    resolve_preferred_dataset_prefix,
    run_live_sweep,
    run_live_sweep_custom,
    sync_dashboard_data_prefix,
)
from nodi_simulator.dashboard.config import (
    GRID_CONFIGS, MATERIAL_OPTIONS,
    PARAM_HELP, PARAM_HELP_FULL,
    REFERENCE_MODEL_OPTIONS, DEFAULT_REFERENCE_MODEL_INDEX,
    MATERIAL_PHYSICS_LABELS, compute_particle_physics_status,
    infer_particle_material, infer_particle_diameter_nm,
    format_particle_label, make_particle,
)
from nodi_simulator.dashboard.panels.common import (
    render_display_banner,
    set_selected_case_context,
    render_page_header_hub,
)

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "results",
)

EXPLORER_METRIC_LABELS = {
    "score": "评分",
    "score_display": "评分",
    "final_engineering_score": "最终工程评分",
    "engineering_score": "工程评分",
    "robust_score": "稳健评分",
    "detection_rate": "检出率",
    "stable_detection_rate": "稳定检出率",
    "hit_rate_at_fixed_false_alarm": "固定误报率命中率",
    "roc_auc_event_vs_background": "ROC-AUC",
    "d_prime_event_vs_background": "d′",
    "mean_peak_height": "平均峰高",
    "mean_peak_to_threshold_ratio": "峰高/阈值比",
    "mean_peak_margin_z": "峰高 z-margin",
    "mean_local_snr": "局部 SNR",
    "mean_transit_time_ms": "平均 transit time",
    "paired_detection_rate": "双通道配对率",
    "robust_cv_peak_height": "稳健 CV",
    "phase_flip_fraction": "相位翻转占比",
    "CV": "CV",
}
LOW_IS_BETTER_METRICS = {"CV", "robust_cv_peak_height", "phase_flip_fraction"}


def _metric_label(metric: str) -> str:
    return EXPLORER_METRIC_LABELS.get(metric, metric)


def _format_metric_value(metric: str, value: object) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return str(value)

    if not np.isfinite(numeric):
        return "N/A"
    if metric in {
        "detection_rate",
        "stable_detection_rate",
        "hit_rate_at_fixed_false_alarm",
        "paired_detection_rate",
    }:
        return f"{numeric:.1%}"
    if metric in {"mean_peak_height"}:
        return f"{numeric:.3e}"
    if metric in {"mean_transit_time_ms"}:
        return f"{numeric:.2f} ms"
    if metric in {"CV", "robust_cv_peak_height", "phase_flip_fraction"}:
        return f"{numeric:.3f}"
    return f"{numeric:.4f}"


def _style_candidate_table(df: pd.DataFrame, metric_column_header: str, display_metric: str):
    format_map: dict[str, object] = {}
    for column in df.columns:
        if column in {"width_nm", "depth_nm"}:
            format_map[column] = "{:.0f}"
        elif column == metric_column_header:
            format_map[column] = lambda value, _col=metric_column_header: _format_metric_value(
                display_metric, value
            )
        elif column in {
            "score",
            "final_engineering_score",
            "engineering_score",
            "robust_score",
        }:
            format_map[column] = lambda value, _col=column: _format_metric_value(_col, value)
        elif column in {
            "detection_rate",
            "stable_detection_rate",
            "paired_detection_rate",
        }:
            format_map[column] = lambda value, _col=column: _format_metric_value(_col, value)
        elif column == "mean_peak_height":
            format_map[column] = lambda value, _col=column: _format_metric_value(_col, value)
        elif column == "CV":
            format_map[column] = lambda value, _col=column: _format_metric_value(_col, value)
    return df.style.format(format_map)


def _resolve_default_design_material(materials: list[str], current_particle: str | None) -> str:
    inferred = infer_particle_material(current_particle) if current_particle else None
    if inferred in materials:
        return str(inferred)
    if "exosome" in materials:
        return "exosome"
    return materials[0]


def _sort_cases_by_metric(
    df: "np.ndarray | object",
    metric: str,
    metric_higher_is_better: bool,
):
    """
    Sort cases for ranking displays.

    `final_engineering_score` remains a useful scalar for heatmaps, but the
    ranking view uses the explicit lexicographic intent:
      1. gate-passing cases first
      2. fewer failed gate conditions
      3. higher engineering_score
    """
    if metric == "final_engineering_score" and "engineering_gate_passed" in df.columns:
        return df.sort_values(
            by=[
                "engineering_gate_passed",
                "engineering_gate_failed_count",
                "engineering_score",
            ],
            ascending=[False, True, False],
        ).reset_index(drop=True)
    return df.sort_values(metric, ascending=not metric_higher_is_better).reset_index(drop=True)


def render_explorer():
    """Render the Design Explorer page."""
    st.header("Design Explorer — 在结果空间里找平台、定代表点")
    st.caption("这页把前面的结论带回全局设计空间：先找稳定平台，再定代表点，再决定是否进入 `Case Inspector` 做最终复核。")
    render_page_header_hub("Design Explorer")
    render_display_banner(
        eyebrow="Evidence Tool",
        title="先读方向，再筛平台，再定代表点",
        body="这页保留完整筛选能力，但阅读顺序已经改成先看结论、再看证据、最后才做选点和局部细扫。",
        tone="info",
    )

    with st.expander("这页怎么用", expanded=False):
        st.markdown(
            """
**什么时候先来这页**

- 你要先决定通道宽度 `W`、深度 `H` 和波长 `λ` 的大致设计区间
- 你想知道高分是大片稳定区域，还是只有几个尖峰点
- 你想先做粗筛，再把候选点送去 Inspector 深看

**推荐顺序**

1. 先看热图，找连续高分区而不是单个最高点
2. 再看 Top 10，确认高分是不是集中在同一片区域
3. 最后看切片图，判断该区域是平台还是尖峰

**怎么判断值不值得信**

- 平台型高分：更适合真实实验，因为参数稍有偏差也不容易失效
- 尖峰型高分：更像“理论最优点”，对制造误差和模型误差更敏感
- 如果切换权重、噪声或经验参数后结论剧变，优先怀疑稳健性而不是盲信分数
            """
        )

    available_prefixes = list_available_datasets(RESULTS_DIR)
    sync_dashboard_data_prefix(st.session_state, available_prefixes)
    workflow_standard_prefix = resolve_preferred_dataset_prefix(available_prefixes)

    # ==== Load data: live or precomputed ====
    try:
        data_bundle = load_dashboard_data_bundle(RESULTS_DIR, st.session_state)
    except (FileNotFoundError, ValueError) as e:
        st.error(str(e))
        st.stop()
    df = data_bundle.df.copy()
    meta = data_bundle.meta
    source = data_bundle.source
    standard_workflow_active = (
        not source.is_live
        and is_standard_dashboard_dataset_prefix(source.prefix)
    )

    def _run_local_fine_from_candidate(center_W_nm: int, center_H_nm: int) -> None:
        """Run a local 100 nm refinement sweep around a candidate point."""
        local_half_window_nm = st.session_state.get("ui_local_fine_half_window_nm", 300)
        local_n_events = st.session_state.get("ui_local_fine_n_events", 60)
        sim_cfg = build_sim_cfg_from_ui(
            ui_rho, ui_ref_alpha, ui_ref_beta, ui_ref_gamma,
            ui_noise_std, ui_drift_slope, ui_threshold_sigma,
            ui_velocity, ui_diffusion,
            ui_ref_model, ui_coupling, ui_norm_mode, ui_noise_model,
        )
        optical = build_optical_from_ui(ui_beam_waist_y)
        live_particle = make_particle(particle_material, particle_diameter)
        local_grid = build_local_fine_grid(
            center_W_nm,
            center_H_nm,
            half_window_nm=local_half_window_nm,
            step_nm=100.0,
            n_events=local_n_events,
        )

        with st.spinner(f"围绕 W={center_W_nm} nm, H={center_H_nm} nm 运行 local_fine..."):
            df_live, compact_live = run_live_sweep_custom(
                sim_cfg, optical, live_particle, local_grid
            )

        st.session_state.sweep_df_live = df_live
        st.session_state.sweep_compact_live = compact_live
        st.session_state.live_sim_cfg = sim_cfg
        st.session_state.live_optical = optical
        st.session_state.live_tag = build_live_tag(sim_cfg)
        st.session_state.live_grid_name = (
            f"local_fine(W={int(center_W_nm)},H={int(center_H_nm)},"
            f"±{int(local_half_window_nm)})"
        )
        st.session_state.using_live_data = True
        st.session_state.case_cache = {}
        set_selected_case_context(
            particle_name=live_particle.name,
            wavelength_nm=st.session_state.get("selected_wavelength_nm"),
            width_nm=int(center_W_nm),
            depth_nm=int(center_H_nm),
        )
        st.success(f"完成，{len(df_live)} 个 case")
        st.rerun()

    # ==== Sidebar — Level 1: filter & display ====
    with st.sidebar:
        if st.session_state.get("using_live_data"):
            st.warning(
                "当前处于工程调试重算 sweep 模式。"
                "科研展示建议切回标准 biomimetic full-range 主结果库。"
            )
            if st.button("切回标准结果库", key="restore_standard_btn", width="stretch"):
                st.session_state.using_live_data = False
                st.session_state.live_grid_name = None
                st.session_state.case_cache = {}
                if workflow_standard_prefix is not None:
                    st.session_state.data_prefix = workflow_standard_prefix
                st.rerun()
        elif meta:
            if available_prefixes:
                selected_prefix = st.selectbox(
                    "科研展示结果库",
                    available_prefixes,
                    index=available_prefixes.index(st.session_state.data_prefix),
                    key="exp_dataset_prefix",
                )
                if selected_prefix != st.session_state.data_prefix:
                    st.session_state.data_prefix = selected_prefix
                    st.session_state.using_live_data = False
                    st.rerun()
            st.caption(
                f"📁 结果库: {meta['grid']}/{meta['config_tag']} "
                f"({meta['n_cases']} cases, {meta['n_events_per_case']} events/case)"
            )
            if standard_workflow_active:
                st.success("当前科研展示正在使用标准 biomimetic full-range 主结果库。")
            elif meta.get("particle_profile") == "full_range":
                st.warning("当前查看的是 full-range 结果库，但不是标准主结果库。")
            else:
                st.warning("当前查看的不是标准 biomimetic full-range 主结果库；建议切回默认主库。")

        st.caption("侧边栏分成两层：左侧只做标准结果库判读；右侧工程调试重算入口用于验证假设，不属于科研展示主线。")
        browse_tab, tune_tab = st.tabs(["结果库筛选", "工程调试"])

        with browse_tab:
            st.caption("这部分服务标准结果库阅读：先筛选，再看热图、排名和平台宽度，不需要重跑。")
            st.markdown("**核心筛选**")

            materials = sorted(df["particle_material"].dropna().unique())
            wavelengths = sorted(df["wavelength_nm"].unique())
            current_particle = st.session_state.get("selected_particle")
            default_material = _resolve_default_design_material(materials, current_particle)

            particle_material = st.selectbox(
                "粒子类型",
                materials,
                index=materials.index(default_material),
                key="exp_particle_material",
                help=PARAM_HELP["particle_material"],
            )
            diameter_options = sorted(
                int(d) for d in df.loc[
                    df["particle_material"] == particle_material, "particle_diameter_nm"
                ].dropna().unique()
            )
            default_diameter = infer_particle_diameter_nm(current_particle) if current_particle else diameter_options[0]
            if default_diameter not in diameter_options:
                default_diameter = diameter_options[0]
            particle_diameter = st.selectbox(
                "粒径 (nm)",
                diameter_options,
                index=diameter_options.index(default_diameter),
                key="exp_particle_diameter",
                help=PARAM_HELP["particle_diameter"],
            )
            wavelength = st.selectbox("波长 (nm)", wavelengths, key="exp_wavelength")
            metric_options = [
                option
                for option in [
                    "score",
                    "final_engineering_score",
                    "engineering_score",
                    "robust_score",
                    "detection_rate",
                    "stable_detection_rate",
                    "hit_rate_at_fixed_false_alarm",
                    "roc_auc_event_vs_background",
                    "d_prime_event_vs_background",
                    "mean_peak_height",
                    "mean_peak_to_threshold_ratio",
                    "mean_peak_margin_z",
                    "mean_local_snr",
                    "mean_transit_time_ms",
                    "paired_detection_rate",
                    "CV",
                    "phase_flip_fraction",
                ]
                if option in df.columns or option in {"score", "robust_score", "detection_rate", "mean_peak_height", "CV"}
            ]
            metric = st.selectbox(
                "热图指标",
                metric_options,
                index=(
                    metric_options.index("engineering_score")
                    if "engineering_score" in metric_options
                    else metric_options.index("final_engineering_score")
                    if "final_engineering_score" in metric_options
                    else 0
                ),
                key="exp_metric",
            )
            with st.expander("三种主评分含义与选用指南", expanded=False):
                st.markdown(
                    "**评分体系速查**\n\n"
                    "| 评分 | 核心逻辑 | 推荐场景 |\n"
                    "|------|---------|----------|\n"
                    "| `score` | `峰高 × 检出率 / CV`（权重可调） | 快速排序；侧边栏可拖动权重 |\n"
                    "| `engineering_score` | 多指标加权连续分（检出率＋稳健性＋余量＋配对率） | 在**已过门槛**的候选里比谁更好 |\n"
                    "| `final_engineering_score` | 先按 gate 过/未过分层，再按 `engineering_score` 排序 | **日常推荐**：直接反映「先保底再择优」的完整选型逻辑 |\n\n"
                    "**决策树：热图该选哪个指标？**\n\n"
                    "- 想快速找「工程门槛通过区域」 → **`final_engineering_score`**（门槛分层已编码）\n"
                    "- 在「已过 gate 的候选里」比谁更有优势 → **`engineering_score`**\n"
                    "- 想调整峰高 / 检出率 / CV 权重快速重排 → **`score`**（侧边栏可拖权重）\n"
                    "- 想单独看某一个维度 → 直接选 `detection_rate` / `stable_detection_rate` / `mean_peak_margin_z` 等\n\n"
                    "⚠️ `score` 和 `engineering_score` 不进行门槛过滤；"
                    "未通过 gate 的点在这两个指标下仍可能得分不低，不代表工程可行。"
                )
            filtered_particles = sorted(
                df[
                    (df["particle_material"] == particle_material)
                    & (df["particle_diameter_nm"] == particle_diameter)
                ]["particle_name"].unique()
            )
            particle = filtered_particles[0]
            particle_label = format_particle_label(particle_material, particle_diameter)
            with st.expander("高级设置：数据覆盖与重排权重", expanded=False):
                coverage_parts = []
                for material_name, sub_df in df.dropna(subset=["particle_material", "particle_diameter_nm"]).groupby("particle_material"):
                    diameters = sorted(int(d) for d in sub_df["particle_diameter_nm"].unique())
                    if not diameters:
                        continue
                    coverage_parts.append(
                        f"{material_name}: {diameters[0]}–{diameters[-1]} nm（{len(diameters)} 个粒径点）"
                    )
                if coverage_parts:
                    st.caption("当前数据集粒径覆盖：" + " / ".join(coverage_parts))
                if standard_workflow_active:
                    st.caption("当前科研展示口径：标准 biomimetic full-range 主库已覆盖 gold / biomimetic exosome 的 40–300 nm 完整粒径范围。")
                elif meta and meta.get("particle_profile") != "full_range":
                    st.caption("提示：当前预计算数据不是完整粒径范围；科研展示建议切回标准 biomimetic 主库。")

                st.markdown("**评分权重**")
                st.caption("这里只重排当前结果库里的点；不会触发新的 physics 重算。")
                w_height = st.slider("峰高权重", 0.0, 3.0, 1.0, 0.1, key="w_h")
                w_rate = st.slider("检出率权重", 0.0, 3.0, 1.0, 0.1, key="w_r")
                w_cv = st.slider("CV 惩罚权重", 0.0, 3.0, 1.0, 0.1, key="w_cv")

        with tune_tab:
            st.caption("这部分只用于工程调试和局部验证，不属于标准结果库科研展示主线。修改后会重跑工程调试 sweep。")

            # ---- Global toggle: parameter explanation mode ----
            explain_mode = st.toggle("参数解释模式", value=False, key="explain_mode",
                                     help="开启后在每个参数下方显示完整物理解释")

            # ---- Particle selection (physics-oriented grouping) ----
            with st.expander("粒子选择", expanded=True):
                st.markdown("**材料**")
                ui_material = st.selectbox(
                    "材料类型", MATERIAL_OPTIONS,
                    format_func=lambda x: MATERIAL_PHYSICS_LABELS.get(x, x),
                    help=PARAM_HELP["particle_material"],
                    key="ui_material",
                )
                if explain_mode:
                    st.markdown(PARAM_HELP_FULL["particle_material"], unsafe_allow_html=True)

                st.markdown("**粒径**")
                ui_diameter = st.slider(
                    "粒径 (nm)", 40, 300, 100, 10,
                    help=PARAM_HELP["particle_diameter"],
                    key="ui_diameter",
                )
                if explain_mode:
                    st.markdown(PARAM_HELP_FULL["particle_diameter"], unsafe_allow_html=True)

                phys_status = compute_particle_physics_status(
                    ui_material, ui_diameter,
                    wavelength_nm=wavelength if wavelength else 660.0,
                )
                st.markdown("---")
                st.markdown("**当前粒子物理状态**")
                st.code(
                    f"尺寸参数 x = {phys_status['size_parameter']:.3f}\n"
                    f"  → {phys_status['scattering_regime']}\n\n"
                    f"散射缩放关系:\n"
                    f"  {phys_status['scattering_scaling']}\n\n"
                    f"材料特性:\n"
                    f"  {phys_status['material_type']}",
                    language=None,
                )

            with st.expander("干涉系统参数"):
                ui_ref_model = st.selectbox(
                    "参考场模型",
                    REFERENCE_MODEL_OPTIONS,
                    index=DEFAULT_REFERENCE_MODEL_INDEX,
                    help=PARAM_HELP["reference_model"],
                    key="ui_ref_model",
                )
                if explain_mode:
                    st.markdown(PARAM_HELP_FULL["reference_model"], unsafe_allow_html=True)

                ui_rho = st.slider("参考场比例因子 (rho)",
                                   1.0, 50.0, 10.0, 0.5,
                                   help=PARAM_HELP["rho"],
                                   key="ui_rho")
                if explain_mode:
                    st.markdown(PARAM_HELP_FULL["rho"], unsafe_allow_html=True)

                if ui_ref_model == "geometry_scaled":
                    ui_ref_alpha = st.slider("ref_alpha (W 依赖)",
                                             0.0, 2.0, 0.5, 0.1,
                                             help=PARAM_HELP["ref_alpha"],
                                             key="ui_ref_alpha")
                    if explain_mode:
                        st.markdown(PARAM_HELP_FULL["ref_alpha"], unsafe_allow_html=True)
                    ui_ref_beta = st.slider("ref_beta (H 依赖)",
                                            0.0, 2.0, 0.3, 0.1,
                                            help=PARAM_HELP["ref_beta"],
                                            key="ui_ref_beta")
                    if explain_mode:
                        st.markdown(PARAM_HELP_FULL["ref_beta"], unsafe_allow_html=True)
                    ui_ref_gamma = st.slider("ref_gamma (λ 依赖)",
                                             0.0, 3.0, 1.0, 0.1,
                                             help=PARAM_HELP["ref_gamma"],
                                             key="ui_ref_gamma")
                    if explain_mode:
                        st.markdown(PARAM_HELP_FULL["ref_gamma"], unsafe_allow_html=True)
                else:
                    st.caption("constant 模式下 α/β/γ 无效")
                    ui_ref_alpha, ui_ref_beta, ui_ref_gamma = 0.0, 0.0, 0.0

            with st.expander("噪声与检测参数"):
                ui_noise_model = st.selectbox(
                    "噪声模型",
                    ["gaussian", "gaussian_plus_drift"], index=1,
                    help=PARAM_HELP["noise_model"],
                    key="ui_noise_model",
                )
                if explain_mode:
                    st.markdown(PARAM_HELP_FULL["noise_model"], unsafe_allow_html=True)

                ui_noise_std = st.slider("噪声标准差",
                                         0.0, 0.2, 0.01, 0.005,
                                         help=PARAM_HELP["noise_std"],
                                         key="ui_noise_std")
                if explain_mode:
                    st.markdown(PARAM_HELP_FULL["noise_std"], unsafe_allow_html=True)

                if ui_noise_model == "gaussian_plus_drift":
                    ui_drift_slope = st.slider("漂移斜率",
                                               0.0, 0.01, 0.001, 0.0005,
                                               help=PARAM_HELP["drift_slope"],
                                               key="ui_drift_slope")
                    if explain_mode:
                        st.markdown(PARAM_HELP_FULL["drift_slope"], unsafe_allow_html=True)
                else:
                    st.caption("纯高斯噪声模式下不使用漂移斜率")
                    ui_drift_slope = 0.0
                ui_threshold_sigma = st.slider("阈值倍数",
                                               3.0, 10.0, 5.0, 0.5,
                                               help=PARAM_HELP["threshold_sigma"],
                                               key="ui_threshold_sigma")
                if explain_mode:
                    st.markdown(PARAM_HELP_FULL["threshold_sigma"], unsafe_allow_html=True)

            with st.expander("流动参数"):
                ui_velocity = st.slider("流速 (mm/s)",
                                        0.05, 1.0, 0.2, 0.05,
                                        help=PARAM_HELP["velocity"],
                                        key="ui_velocity")
                if explain_mode:
                    st.markdown(PARAM_HELP_FULL["velocity"], unsafe_allow_html=True)

                ui_beam_waist_y = st.slider("y 向光束腰斑 (nm)",
                                            300, 2000, 700, 50,
                                            help=PARAM_HELP["beam_waist_y"],
                                            key="ui_beam_waist_y")
                if explain_mode:
                    st.markdown(PARAM_HELP_FULL["beam_waist_y"], unsafe_allow_html=True)

                ui_diffusion = st.checkbox("启用布朗扩散", value=True,
                                           help=PARAM_HELP["include_diffusion"],
                                           key="ui_diffusion")
                if explain_mode:
                    st.markdown(PARAM_HELP_FULL["include_diffusion"], unsafe_allow_html=True)

            with st.expander("归一化与耦合"):
                ui_norm_mode = st.selectbox(
                    "归一化方式",
                    ["global_single_lambda", "per_wavelength"], index=1,
                    help=PARAM_HELP["normalization_mode"],
                    key="ui_norm_mode",
                )
                if explain_mode:
                    st.markdown(PARAM_HELP_FULL["normalization_mode"], unsafe_allow_html=True)
                elif ui_norm_mode == "global_single_lambda":
                    st.caption("所有波长共用 baseline λ 的 E_sca_ref，跨波长比较受锚定影响")
                else:
                    st.caption("每个波长独立归一化，跨波长比较更公平")
                ui_coupling = st.selectbox(
                    "位置耦合模型",
                    ["constant", "gaussian_xy"], index=1,
                    help=PARAM_HELP["coupling_model"],
                    key="ui_coupling",
                )
                if explain_mode:
                    st.markdown(PARAM_HELP_FULL["coupling_model"], unsafe_allow_html=True)

            st.markdown("**扫参网格**")
            local_center_W = st.session_state.get("selected_W_nm") or 800
            local_center_H = st.session_state.get("selected_H_nm") or 550
            ui_grid_name = st.selectbox(
                "W/H 扫描分辨率",
                ["coarse", "fine", "local_fine"],
                index=0,
                format_func=lambda x: {
                    "coarse": "coarse（500 nm 步长，先找大致区域）",
                    "fine": "fine（100 nm 步长，全范围认真比较宽深差异）",
                    "local_fine": "local_fine（围绕当前选点做 100 nm 局部细扫）",
                }[x],
                key="ui_grid_name",
            )

            grid_for_display = None
            if ui_grid_name == "local_fine":
                local_half_window_nm = st.slider(
                    "局部细扫半窗口 (nm)",
                    100,
                    600,
                    300,
                    100,
                    key="ui_local_fine_half_window_nm",
                )
                local_n_events = st.slider(
                    "局部细扫每 case 事件数",
                    20,
                    100,
                    60,
                    10,
                    key="ui_local_fine_n_events",
                )
                st.caption(
                    f"当前局部细扫将围绕已选点中心：W={int(local_center_W)} nm, H={int(local_center_H)} nm"
                )
                grid_for_display = build_local_fine_grid(
                    local_center_W,
                    local_center_H,
                    half_window_nm=local_half_window_nm,
                    step_nm=100.0,
                    n_events=local_n_events,
                )
            else:
                grid_for_display = GRID_CONFIGS[ui_grid_name]

            n_cases = (len(grid_for_display["width_list_m"])
                       * len(grid_for_display["depth_list_m"])
                       * len(grid_for_display["wavelength_list_m"]))
            width_arr = grid_for_display["width_list_m"]
            step_nm = int(round((width_arr[1] - width_arr[0]) * 1e9)) if len(width_arr) > 1 else 0
            st.caption(
                f"当前将以 `{ui_grid_name}` 网格运行：W/H 步长约 {step_nm} nm，"
                f"{n_cases} cases × {grid_for_display['n_events']} events"
            )
            if ui_grid_name == "coarse":
                st.caption("适合第一轮找大致平台区。优点是快；缺点是对峰位和局部平台边界看得比较粗。")
            elif ui_grid_name == "fine":
                st.caption("适合第二轮认真比较不同宽深。100 nm 分辨率更适合判断平台宽度、峰位偏移和局部最优区，但会明显更慢。")
            else:
                st.caption("最适合先用 coarse 找到候选区后，再围绕当前选点做局部细扫。它比全范围 fine 更快，也更贴近真实分析流程。")

            if st.button("工程调试：重跑 Sweep", key="run_live_btn"):
                sim_cfg = build_sim_cfg_from_ui(
                    ui_rho, ui_ref_alpha, ui_ref_beta, ui_ref_gamma,
                    ui_noise_std, ui_drift_slope, ui_threshold_sigma,
                    ui_velocity, ui_diffusion,
                    ui_ref_model, ui_coupling, ui_norm_mode, ui_noise_model,
                )
                optical = build_optical_from_ui(ui_beam_waist_y)
                live_particle = make_particle(ui_material, ui_diameter)
                try:
                    with st.spinner("重跑中..."):
                        if ui_grid_name == "local_fine":
                            local_grid = build_local_fine_grid(
                                local_center_W,
                                local_center_H,
                                half_window_nm=st.session_state["ui_local_fine_half_window_nm"],
                                step_nm=100.0,
                                n_events=st.session_state["ui_local_fine_n_events"],
                            )
                            df_live, compact_live = run_live_sweep_custom(
                                sim_cfg, optical, live_particle, local_grid
                            )
                            grid_label = (
                                f"local_fine(W={int(local_center_W)},H={int(local_center_H)},"
                                f"±{int(st.session_state['ui_local_fine_half_window_nm'])})"
                            )
                        else:
                            df_live, compact_live = run_live_sweep(
                                sim_cfg, optical, live_particle, ui_grid_name
                            )
                            grid_label = ui_grid_name
                    st.session_state.sweep_df_live = df_live
                    st.session_state.sweep_compact_live = compact_live
                    st.session_state.live_sim_cfg = sim_cfg
                    st.session_state.live_optical = optical
                    st.session_state.live_tag = build_live_tag(sim_cfg)
                    st.session_state.live_grid_name = grid_label
                    st.session_state.using_live_data = True
                    st.session_state.case_cache = {}
                    st.session_state.selected_particle = live_particle.name
                    st.success(f"完成，{len(df_live)} 个 case")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))

            if st.session_state.get("using_live_data"):
                st.caption("切回后将恢复标准结果库分析，并清除当前工程调试 detail 缓存。")
                if st.button("切回标准结果库", key="restore_btn"):
                    st.session_state.using_live_data = False
                    st.session_state.live_grid_name = None
                    st.session_state.case_cache = {}
                    if workflow_standard_prefix is not None:
                        st.session_state.data_prefix = workflow_standard_prefix
                    st.rerun()

    # ==== Build display copy (never modify cached original) ====
    df = df.copy()

    # ==== Score display logic ====
    if w_height != 1.0 or w_rate != 1.0 or w_cv != 1.0:
        df["score_display"] = recompute_scores(df, w_height, w_rate, w_cv)
        active_score_col = "score_display"
    else:
        active_score_col = "score"

    # ==== Live parameter summary bar ====
    if source.is_live:
        cfg = st.session_state.live_sim_cfg
        st.warning(
            f"当前是工程调试重算 sweep [{st.session_state.live_tag}]，不属于科研展示默认结果库。"
        )
        st.caption(
            f"调试摘要：网格={st.session_state.get('live_grid_name') or 'coarse'}  |  "
            f"粒子={particle_label}  |  "
            f"参考场比例因子 (rho)={cfg.rho}  α={cfg.ref_alpha}  β={cfg.ref_beta}  γ={cfg.ref_gamma}  |  "
            f"读出噪声标准差 (noise_std)={cfg.noise_std}  漂移={cfg.drift_slope}  "
            f"阈值倍数 (threshold_sigma)={cfg.threshold_sigma}σ  |  "
            f"v={cfg.mean_flow_velocity_m_s*1e3:.2f}mm/s  "
            f"扩散={'开启' if cfg.include_diffusion else '关闭'}  "
            f"参考场={cfg.reference_model}  耦合={cfg.coupling_model}"
        )
    elif standard_workflow_active:
        st.success(
            "当前页面分析的是标准 biomimetic full-range 主结果库。科研展示主线里的热图、排序和结论都应优先围绕这套结果解释。"
        )
    else:
        st.warning(
            f"当前页面使用的是 `{source.prefix}`，不是标准 biomimetic full-range 主结果库。"
        )

    # ==== Determine display metric column ====
    display_metric = active_score_col if metric == "score" else metric
    metric_label = _metric_label(display_metric)
    metric_column_header = f"{metric_label} (当前)"
    metric_higher_is_better = display_metric not in LOW_IS_BETTER_METRICS
    df_f = df[(df["particle_name"] == particle) & (df["wavelength_nm"] == wavelength)]
    sel_W = st.session_state.get("selected_W_nm")
    sel_H = st.session_state.get("selected_H_nm")
    sorted_df_f = _sort_cases_by_metric(df_f, display_metric, metric_higher_is_better)
    top = sorted_df_f.head(10).copy()
    top["当前指标"] = top[display_metric]
    top_columns = ["width_nm", "depth_nm", "当前指标"]
    for candidate_col in [
        "design_recommendation_label",
        "observation_freeze_status",
    ]:
        if candidate_col in top.columns:
            top_columns.append(candidate_col)
    for candidate_col in [
        "score",
        "final_engineering_score",
        "engineering_score",
        "robust_score",
        "detection_rate",
        "stable_detection_rate",
        "mean_peak_height",
        "CV",
    ]:
        if candidate_col in top.columns:
            top_columns.append(candidate_col)
    top_display = (
        top[top_columns]
        .rename(columns={"当前指标": metric_column_header})
        .reset_index(drop=True)
    )
    top_case = top.iloc[0]
    sorted_cases = _sort_cases_by_metric(df_f, display_metric, metric_higher_is_better)

    W_opts = sorted(df_f["width_nm"].unique())
    H_opts = sorted(df_f["depth_nm"].unique())
    default_W = sel_W if sel_W in W_opts else int(top_case["width_nm"])
    default_H = sel_H if sel_H in H_opts else int(top_case["depth_nm"])

    c1, c2 = st.columns(2)
    with c1:
        selected_W = st.selectbox(
            "W (nm)", W_opts,
            index=W_opts.index(default_W),
            key="sel_W_box",
        )
    with c2:
        selected_H = st.selectbox(
            "H (nm)", H_opts,
            index=H_opts.index(default_H),
            key="sel_H_box",
        )

    set_selected_case_context(
        particle_name=particle,
        wavelength_nm=wavelength,
        width_nm=selected_W,
        depth_nm=selected_H,
    )

    selected_case = df_f[
        (df_f["width_nm"] == selected_W) & (df_f["depth_nm"] == selected_H)
    ].iloc[0]
    selected_rank = int(
        sorted_cases[
            (sorted_cases["width_nm"] == selected_W) & (sorted_cases["depth_nm"] == selected_H)
        ].index[0]
    ) + 1
    decision_summary = build_case_decision_summary(
        design_recommendation_label=selected_case.get("design_recommendation_label"),
        design_recommendation_status=selected_case.get("design_recommendation_status"),
        design_recommendation_guidance=selected_case.get("design_recommendation_guidance"),
        engineering_gate_passed=bool(selected_case.get("engineering_gate_passed")),
        engineering_gate_status_label=selected_case.get("engineering_gate_status_label"),
        engineering_gate_primary_blocker_label=selected_case.get("engineering_gate_primary_blocker_label"),
        engineering_gate_blocker_summary=selected_case.get("engineering_gate_blocker_summary"),
        engineering_gate_guidance=selected_case.get("engineering_gate_guidance"),
        observation_freeze_status=selected_case.get("observation_freeze_status"),
        observation_freeze_guidance=selected_case.get("observation_freeze_guidance"),
    )

    st.markdown("### 当前候选")
    cols = st.columns(5)
    cols[0].metric("W", f"{selected_W} nm")
    cols[1].metric("H", f"{selected_H} nm")
    cols[2].metric(metric_label, _format_metric_value(display_metric, selected_case[display_metric]))
    cols[3].metric("排名", f"{selected_rank}/{len(df_f)}")
    cols[4].metric("检出率", f"{selected_case['detection_rate']:.0%}")
    st.caption(
        f"{decision_summary['decision_summary_headline']} | "
        f"{decision_summary['decision_summary_blocker_text']} | "
        f"{decision_summary['decision_summary_next_step']}"
    )

    st.markdown("### 热图")
    W_arr, H_arr, matrix = build_heatmap_matrix(df, particle, wavelength, display_metric)
    if matrix.size > 1:
        fig = go.Figure(data=go.Heatmap(
            x=W_arr, y=H_arr, z=matrix, colorscale="Viridis",
            hovertemplate="W=%{x}nm<br>H=%{y}nm<br>value=%{z:.3f}<extra></extra>",
        ))
        fig.update_layout(
            xaxis_title="通道宽度 W (nm)",
            yaxis_title="通道深度 H (nm)",
            height=500,
        )
        fig.add_trace(go.Scatter(
            x=[selected_W], y=[selected_H], mode="markers",
            marker=dict(size=16, symbol="x", color="red", line=dict(width=2)),
            showlegend=False,
        ))
        st.plotly_chart(fig, width="stretch")

    st.markdown("### 候选排名")
    st.dataframe(
        _style_candidate_table(top_display, metric_column_header, display_metric),
        width="stretch",
        hide_index=True,
    )

    st.markdown("### 稳健性切片")
    _wilson_lb_col = {
        "detection_rate": "detection_rate_wilson_lb",
        "stable_detection_rate": "stable_detection_rate_wilson_lb",
    }.get(display_metric)

    c_left, c_right = st.columns(2)
    with c_left:
        x_w, y_w = build_slice_data(
            df, particle, wavelength, "depth", selected_H, display_metric)
        fig_w = go.Figure(go.Scatter(x=x_w, y=y_w, mode="lines+markers", name=metric_label))
        if _wilson_lb_col and _wilson_lb_col in df.columns:
            x_wlb, y_wlb = build_slice_data(
                df, particle, wavelength, "depth", selected_H, _wilson_lb_col)
            fig_w.add_trace(go.Scatter(
                x=x_wlb, y=y_wlb, mode="lines",
                name="Wilson LB",
                line=dict(dash="dot", color="orange"),
            ))
        fig_w.add_vline(x=selected_W, line_dash="dash", line_color="red")
        fig_w.update_layout(
            title=f"{metric_label} 随 W 变化 (H={selected_H}nm)",
            xaxis_title="通道宽度 W (nm)", yaxis_title=metric_label, height=300,
        )
        st.plotly_chart(fig_w, width="stretch")
    with c_right:
        x_h, y_h = build_slice_data(
            df, particle, wavelength, "width", selected_W, display_metric)
        fig_h = go.Figure(go.Scatter(x=x_h, y=y_h, mode="lines+markers", name=metric_label))
        if _wilson_lb_col and _wilson_lb_col in df.columns:
            x_hlb, y_hlb = build_slice_data(
                df, particle, wavelength, "width", selected_W, _wilson_lb_col)
            fig_h.add_trace(go.Scatter(
                x=x_hlb, y=y_hlb, mode="lines",
                name="Wilson LB",
                line=dict(dash="dot", color="orange"),
            ))
        fig_h.add_vline(x=selected_H, line_dash="dash", line_color="red")
        fig_h.update_layout(
            title=f"{metric_label} 随 H 变化 (W={selected_W}nm)",
            xaxis_title="通道深度 H (nm)", yaxis_title=metric_label, height=300,
        )
        st.plotly_chart(fig_h, width="stretch")

    with st.expander("Top 3 候选点的 local_fine 入口", expanded=False):
        top3_raw = top.head(3).reset_index(drop=True)
        for idx, row in enumerate(top3_raw.to_dict("records")):
            row_cols = st.columns([1.1, 1.2, 1.2, 1.4, 1.8])
            row_cols[0].markdown(f"**Rank {idx + 1}**")
            row_cols[1].metric("W", f"{int(row['width_nm'])} nm")
            row_cols[2].metric("H", f"{int(row['depth_nm'])} nm")
            row_cols[3].metric(metric_label, _format_metric_value(display_metric, row[display_metric]))
            with row_cols[4]:
                if st.button(
                    "运行 local_fine",
                    key=f"run_local_fine_rank_{idx + 1}",
                    width="stretch",
                ):
                    _run_local_fine_from_candidate(
                        int(row["width_nm"]),
                        int(row["depth_nm"]),
                    )
