"""
dashboard/panels/common.py — Shared dashboard guidance helpers
"""

from __future__ import annotations

from collections.abc import Callable
from collections.abc import Mapping
from copy import deepcopy
from typing import Any

import streamlit as st

from nodi_simulator.dashboard.config import (
    DEFAULT_DASHBOARD_DIAMETER_NM,
    DEFAULT_SIM_CFG,
    FULL_SWEEP_WAVELENGTHS_NM,
    MATERIAL_OPTIONS,
    OPTICAL_TEMPLATE,
    format_particle_label,
    infer_particle_diameter_nm,
    infer_particle_material,
    snap_diameter_nm,
)


WORKFLOW_STEPS = [
    {
        "page": "Decision Summary",
        "goal": "先拿到主结论、主数据口径和默认路线。",
    },
    {
        "page": "Engineering Windows",
        "goal": "把研究上限线和工程保守线拆开，收成可制造窗口。",
    },
]

EVIDENCE_PAGES = [
    {
        "page": "Mie Explorer",
        "goal": "只看粒子本征散射，用于机制拆解，不直接给最终设计结论。",
    },
    {
        "page": "Interference Explorer",
        "goal": "看 reference 如何把散射转成 clean signal，属于机制证据页。",
    },
    {
        "page": "Noise & Detection Explorer",
        "goal": "看噪声、阈值和检出边界，属于检测链条附录。",
    },
    {
        "page": "Design Explorer",
        "goal": "在结果空间里主动筛平台和代表点，属于证据决策页，不是第一层展示页。",
    },
    {
        "page": "Case Inspector",
        "goal": "对具体候选点做最终证据核查，确认成因、波动和单事件表现。",
    },
]

CALCULATOR_PAGES = [
    {
        "page": "Single-Case Calculator",
        "goal": "独立输入一个具体 case，逐阶段做现场重算，不依赖主展示的选点流程。",
    },
]

PAGE_PURPOSES = {
    **{step["page"]: step["goal"] for step in WORKFLOW_STEPS},
    **{page["page"]: page["goal"] for page in EVIDENCE_PAGES},
    **{page["page"]: page["goal"] for page in CALCULATOR_PAGES},
}
WORKFLOW_PAGE_OPTIONS = [step["page"] for step in WORKFLOW_STEPS]
EVIDENCE_PAGE_OPTIONS = [page["page"] for page in EVIDENCE_PAGES]
CALCULATOR_PAGE_OPTIONS = [page["page"] for page in CALCULATOR_PAGES]
PAGE_OPTIONS = WORKFLOW_PAGE_OPTIONS + EVIDENCE_PAGE_OPTIONS + CALCULATOR_PAGE_OPTIONS


DashboardDefaultValue = object | Callable[[str], object]


DASHBOARD_SESSION_DEFAULTS: tuple[tuple[str, DashboardDefaultValue], ...] = (
    ("dashboard_page", "Decision Summary"),
    ("dashboard_page_radio", "Decision Summary"),
    ("selected_particle", None),
    ("selected_wavelength_nm", None),
    ("selected_W_nm", None),
    ("selected_H_nm", None),
    ("case_cache", lambda default_data_prefix: {}),
    ("data_prefix", lambda default_data_prefix: default_data_prefix),
    ("using_live_data", False),
    ("sweep_df_live", None),
    ("sweep_compact_live", None),
    ("live_sim_cfg", None),
    ("live_optical", None),
    ("live_tag", None),
    ("live_grid_name", None),
    ("single_case_material", None),
    ("single_case_diameter_nm", None),
    ("single_case_wavelength_nm", None),
    ("single_case_width_nm", None),
    ("single_case_depth_nm", None),
    ("single_case_n_events", 12),
    ("single_case_rho", None),
    ("single_case_include_diffusion", None),
    ("single_case_noise_std", None),
    ("single_case_threshold_sigma", None),
    ("single_case_velocity_mm_s", None),
    ("single_case_stage_report", None),
)


def inject_dashboard_theme() -> None:
    """Keep dashboard styling intentionally minimal."""
    return None


def render_display_banner(
    *,
    title: str,
    body: str,
    eyebrow: str | None = None,
    tone: str = "info",
) -> None:
    """Render a compact plain-text banner."""
    prefix = f"{eyebrow}: " if eyebrow else ""
    message = f"**{prefix}{title}**\n\n{body}"
    tone_map = {
        "info": st.info,
        "success": st.success,
        "warning": st.warning,
        "danger": st.error,
    }
    tone_map.get(tone, st.info)(message)


def render_section_intro(
    *,
    title: str,
    body: str,
    tone: str = "neutral",
) -> None:
    """Render a minimal section intro."""
    st.markdown(f"#### {title}")
    st.caption(body)


def initialize_dashboard_session_state(default_data_prefix: str) -> None:
    """Seed dashboard session state using one shared default registry."""
    for key, default in DASHBOARD_SESSION_DEFAULTS:
        if key in st.session_state:
            continue
        st.session_state[key] = (
            default(default_data_prefix)
            if callable(default)
            else default
        )


def get_selected_case_context() -> dict[str, object] | None:
    """Read the currently selected cross-page case context from session state."""
    return build_case_context(
        st.session_state.get("selected_particle"),
        st.session_state.get("selected_wavelength_nm"),
        st.session_state.get("selected_W_nm"),
        st.session_state.get("selected_H_nm"),
    )


def set_selected_case_context(
    *,
    particle_name: str | None,
    wavelength_nm: int | float | None,
    width_nm: int | float | None,
    depth_nm: int | float | None,
) -> None:
    """Persist one selected case context back into dashboard session state."""
    st.session_state["selected_particle"] = particle_name
    st.session_state["selected_wavelength_nm"] = wavelength_nm
    st.session_state["selected_W_nm"] = width_nm
    st.session_state["selected_H_nm"] = depth_nm


def get_active_data_source_tag() -> str | None:
    """Return the current dashboard data source tag used for caches/captions."""
    if st.session_state.get("using_live_data"):
        return st.session_state.get("live_tag")
    return st.session_state.get("data_prefix")


def resolve_active_system_defaults() -> tuple[object, object, str]:
    """Return the active sim/optical defaults and a matching source label."""
    if (
        st.session_state.get("using_live_data")
        and st.session_state.get("live_sim_cfg") is not None
        and st.session_state.get("live_optical") is not None
    ):
        tag = st.session_state.get("live_tag", "live")
        return (
            deepcopy(st.session_state["live_sim_cfg"]),
            deepcopy(st.session_state["live_optical"]),
            f"当前参数默认继承工程调试 live 系统参数 [{tag}]",
        )

    return (
        deepcopy(DEFAULT_SIM_CFG),
        deepcopy(OPTICAL_TEMPLATE),
        f"当前参数默认继承当前结果库口径 [{st.session_state.get('data_prefix', 'default')}]",
    )


def resolve_shared_case_parameter_defaults(
    *,
    default_material: str = "gold",
    default_wavelength_nm: int = 660,
    default_width_nm: int = 800,
    default_depth_nm: int = 550,
) -> tuple[dict[str, object], object, object]:
    """Resolve selected-case defaults shared by evidence panels."""
    particle_name = st.session_state.get("selected_particle")
    material = infer_particle_material(particle_name) if particle_name else default_material
    if material not in MATERIAL_OPTIONS:
        material = default_material

    diameter_nm = (
        infer_particle_diameter_nm(particle_name)
        if particle_name
        else DEFAULT_DASHBOARD_DIAMETER_NM
    )
    diameter_nm = snap_diameter_nm(diameter_nm)

    wavelength_nm = st.session_state.get("selected_wavelength_nm")
    if wavelength_nm is None:
        wavelength_nm = default_wavelength_nm
    wavelength_options = list(FULL_SWEEP_WAVELENGTHS_NM)
    wavelength_nm = int(
        min(wavelength_options, key=lambda value: abs(value - float(wavelength_nm)))
    )

    width_nm = st.session_state.get("selected_W_nm")
    depth_nm = st.session_state.get("selected_H_nm")
    if width_nm is None:
        width_nm = default_width_nm
    if depth_nm is None:
        depth_nm = default_depth_nm

    sim_cfg, optical, source_label = resolve_active_system_defaults()
    return (
        {
            "material": material,
            "diameter_nm": int(diameter_nm),
            "wavelength_nm": int(wavelength_nm),
            "width_nm": int(round(float(width_nm))),
            "depth_nm": int(round(float(depth_nm))),
            "source_label": source_label,
        },
        sim_cfg,
        optical,
    )


def build_case_context(
    particle_name: str | None,
    wavelength_nm: int | float | None,
    width_nm: int | float | None,
    depth_nm: int | float | None,
) -> dict[str, object] | None:
    """Build a normalized cross-page case context summary."""
    if all(value is None for value in [particle_name, wavelength_nm, width_nm, depth_nm]):
        return None

    material = infer_particle_material(particle_name) if particle_name else None
    diameter_nm = infer_particle_diameter_nm(particle_name) if particle_name else None
    particle_label = None
    if material is not None:
        particle_label = format_particle_label(material, diameter_nm)

    return {
        "particle_name": particle_name,
        "material": material,
        "diameter_nm": diameter_nm,
        "particle_label": particle_label,
        "wavelength_nm": wavelength_nm,
        "width_nm": width_nm,
        "depth_nm": depth_nm,
    }


def render_page_header_hub(
    current_page: str,
    *,
    geometry_is_context_only: bool = False,
) -> None:
    """Render a minimal shared header area with current context only."""
    render_current_context_bar(
        current_page,
        geometry_is_context_only=geometry_is_context_only,
    )


def render_auxiliary_page_header(
    current_page: str,
    *,
    summary_message: str,
    detail_message: str,
) -> None:
    """Render a minimal header for pages kept outside the main research narrative."""
    st.caption(summary_message)
    render_current_context_bar(
        current_page,
        section_title="科研展示选中 case（仅供导入/对照）",
        intro_text=detail_message,
    )


def render_current_context_bar(
    current_page: str,
    *,
    geometry_is_context_only: bool = False,
    section_title: str = "当前跨页上下文",
    intro_text: str | None = None,
) -> None:
    """Render the currently selected cross-page case context in one compact line."""
    context = get_selected_case_context()
    if context is None:
        return

    def _context_int_value(value: object) -> int | None:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return int(round(value))
        if isinstance(value, str):
            try:
                return int(round(float(value)))
            except ValueError:
                return None
        return None

    particle_value = context["particle_label"] or "—"
    wavelength_nm = _context_int_value(context.get("wavelength_nm"))
    width_nm = _context_int_value(context.get("width_nm"))
    depth_nm = _context_int_value(context.get("depth_nm"))

    wavelength_value = (
        f"{wavelength_nm} nm"
        if wavelength_nm is not None
        else "—"
    )
    width_value = (
        f"{width_nm} nm"
        if width_nm is not None
        else "—"
    )
    depth_value = (
        f"{depth_nm} nm"
        if depth_nm is not None
        else "—"
    )
    st.caption(
        (intro_text or f"{section_title}：")
        + f" 粒子={particle_value} | 波长={wavelength_value} | W={width_value} | H={depth_value}"
    )
    if geometry_is_context_only and any(
        context[key] is not None for key in ["width_nm", "depth_nm"]
    ):
        st.caption("提示：本页直接使用的是粒子与波长；W/H 只保留为与你在系统页面中的 case 对照的上下文。")


def format_case_verdict_caption(
    case_like: Mapping[str, Any],
    *,
    include_blocker: bool = True,
) -> str:
    """Build one shared verdict caption from recommendation/gate/freeze fields."""
    parts = [
        f"推荐标签={case_like.get('design_recommendation_label', 'N/A')}",
        f"工程门槛={case_like.get('engineering_gate_status_label', 'N/A')}",
        f"结果冻结={case_like.get('observation_freeze_status', 'N/A')}",
    ]
    blocker = case_like.get("engineering_gate_primary_blocker_label")
    if include_blocker and blocker not in {None, "", "N/A"}:
        parts.append(f"主要卡点={blocker}")
    return " | ".join(parts)


def render_workflow_case_source_panel(
    *,
    anchor_row: Mapping[str, Any] | None,
    anchor_prefix: str | None,
    selected_case_exists: bool,
    selected_case_caption: str | None,
    empty_case_caption: str,
    primary_metric_label: str,
    primary_metric_value: str,
    explanation: str,
    missing_anchor_warning: str,
    no_selection_info: str,
    is_live: bool,
    live_tag: str | None,
    data_prefix: str | None,
    standard_message: str,
    live_message: str,
) -> None:
    """Render one minimal case/source summary for evidence pages."""
    if anchor_row is not None:
        st.caption(
            f"结果源={anchor_prefix or data_prefix or 'unknown'} | "
            f"{primary_metric_label}={primary_metric_value} | "
            f"{format_case_verdict_caption(anchor_row)} | {explanation}"
        )
    elif selected_case_exists:
        st.warning(missing_anchor_warning)
    else:
        st.info(no_selection_info)

    if is_live:
        tag = live_tag or "live"
        st.warning(f"{live_message} [{tag}]")
    elif selected_case_exists and selected_case_caption:
        st.caption(selected_case_caption)
    else:
        st.caption(empty_case_caption or standard_message)


    """Hide the long glossary block to keep pages compact."""
    return None
