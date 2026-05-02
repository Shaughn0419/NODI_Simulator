"""
dashboard/app.py - Streamlit dashboard entrypoint.
"""

import os
import sys

import streamlit as st


st.set_page_config(page_title="NODI Interferometric Simulator - Dashboard", layout="wide")

# Ensure the project remains importable even if the repo directory is renamed.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_PARENT = os.path.dirname(PROJECT_ROOT)
for candidate in (PROJECT_ROOT, PROJECT_PARENT):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

from nodi_simulator.dashboard.backend import (
    list_available_datasets,
    resolve_preferred_dataset_prefix,
)
from nodi_simulator.dashboard.config import DEFAULT_DATA_PREFIX
from nodi_simulator.dashboard.panels.common import (
    PAGE_OPTIONS,
    PAGE_PURPOSES,
    initialize_dashboard_session_state,
    inject_dashboard_theme,
)


RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "results",
)


def _default_data_prefix() -> str:
    """Prefer the current standard workflow dataset when it is available."""
    preferred_prefix = resolve_preferred_dataset_prefix(list_available_datasets(RESULTS_DIR))
    if preferred_prefix:
        return preferred_prefix
    return DEFAULT_DATA_PREFIX


def _render_decision_summary() -> None:
    from nodi_simulator.dashboard.panels.research_story import render_research_overview

    render_research_overview()

def _render_engineering_windows() -> None:
    from nodi_simulator.dashboard.panels.research_story import render_geometry_platform

    render_geometry_platform()


def _render_mie_explorer() -> None:
    from nodi_simulator.dashboard.panels.mie_explorer import render_mie_explorer

    render_mie_explorer()


def _render_interference_explorer() -> None:
    from nodi_simulator.dashboard.panels.interference_explorer import render_interference_explorer

    render_interference_explorer()


def _render_noise_detection_explorer() -> None:
    from nodi_simulator.dashboard.panels.noise_detection_explorer import render_noise_detection_explorer

    render_noise_detection_explorer()


def _render_design_explorer() -> None:
    from nodi_simulator.dashboard.panels.explorer import render_explorer

    render_explorer()


def _render_case_inspector() -> None:
    from nodi_simulator.dashboard.panels.inspector import render_inspector

    render_inspector()


def _render_single_case_calculator() -> None:
    from nodi_simulator.dashboard.panels.single_case_calculator import (
        render_single_case_calculator,
    )

    render_single_case_calculator()


PAGE_RENDERERS = {
    "Decision Summary": _render_decision_summary,
    "Engineering Windows": _render_engineering_windows,
    "Mie Explorer": _render_mie_explorer,
    "Interference Explorer": _render_interference_explorer,
    "Noise & Detection Explorer": _render_noise_detection_explorer,
    "Design Explorer": _render_design_explorer,
    "Case Inspector": _render_case_inspector,
    "Single-Case Calculator": _render_single_case_calculator,
}


initialize_dashboard_session_state(_default_data_prefix())
inject_dashboard_theme()


st.title("NODI Interferometric Simulator - Dashboard")
st.caption("精简模式：默认围绕当前标准结果库阅读，页面只保留核心结论、机制证据、候选筛选和单案例计算。")

if st.session_state.get("dashboard_page") not in PAGE_OPTIONS:
    st.session_state["dashboard_page"] = "Decision Summary"

page = st.sidebar.radio(
    "页面",
    PAGE_OPTIONS,
    index=PAGE_OPTIONS.index(st.session_state["dashboard_page"]),
)
st.session_state["dashboard_page_radio"] = page
st.session_state["dashboard_page"] = page

with st.sidebar:
    st.caption(f"当前页重点：{PAGE_PURPOSES[page]}")

PAGE_RENDERERS[page]()
