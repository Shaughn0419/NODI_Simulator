"""
dashboard/panels/research_story.py

Research-first dashboard pages:
    - Decision Summary
    - Exosome Route
    - Engineering Windows
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from nodi_simulator.dashboard.backend import (
    check_data_files,
    ensure_summary_geometry_columns,
    list_available_datasets,
    load_metadata,
    load_result_health,
    load_sweep_summary,
)
from nodi_simulator.dashboard.panels.common import (
    render_display_banner,
    render_page_header_hub,
    render_section_intro,
)

RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "results",
)
PRIMARY_STORY_PREFIX = "ev_design_full_range_biomimetic_exosome_with_anchors_10000e"
EXOSOME_BAND_SPECS = [
    ("40–80 nm", 40, 80),
    ("90–150 nm", 90, 150),
    ("160–220 nm", 160, 220),
    ("230–300 nm", 230, 300),
]

WAVELENGTH_COLORS = {
    404: "#2F6BFF",
    488: "#12B3B6",
    532: "#2D9D57",
    660: "#D97430",
}
MECHANISM_PRIORITY_ROWS = [
    {"场景": "mean_peak_height（exosome 全库）", "波长": 0.038, "宽度": 0.150, "深度": 0.030, "粒径": 0.364},
    {"场景": "mean_peak_height（default-ready exosome）", "波长": 0.047, "宽度": 0.106, "深度": 0.035, "粒径": 0.402},
    {"场景": "detection_rate（90–150 nm）", "波长": 0.007, "宽度": 0.473, "深度": 0.262, "粒径": 0.179},
    {"场景": "detection_rate（160–220 nm）", "波长": 0.001, "宽度": 0.486, "深度": 0.413, "粒径": 0.072},
    {"场景": "detection_rate（230–300 nm）", "波长": 0.001, "宽度": 0.477, "深度": 0.391, "粒径": 0.061},
]
DETECTION_CORRELATION_ROWS = [
    {"变量": "mean_local_snr", "与 detection_rate 的 Spearman 相关": 0.944},
    {"变量": "mean_peak_height", "与 detection_rate 的 Spearman 相关": 0.941},
    {"变量": "mean_peak_to_threshold_ratio", "与 detection_rate 的 Spearman 相关": 0.930},
    {"变量": "mean_peak_margin_z", "与 detection_rate 的 Spearman 相关": 0.930},
    {"变量": "E_sca_normalized", "与 detection_rate 的 Spearman 相关": 0.786},
    {"变量": "mean_transit_time_ms", "与 detection_rate 的 Spearman 相关": 0.603},
    {"变量": "phase_flip_fraction", "与 detection_rate 的 Spearman 相关": -0.117},
]
def _frame(rows: list[dict[str, Any]]) -> pd.DataFrame:
    return pd.DataFrame(rows)

def _safe_bool_mean(series: pd.Series) -> float:
    if series.empty:
        return float("nan")
    return float(pd.Series(series).fillna(False).astype(bool).mean())

def _safe_sum_matches(series: pd.Series, target: object) -> int:
    return int((pd.Series(series).fillna("") == target).sum())

@st.cache_data(show_spinner=False)
def _load_named_dataset(prefix: str) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any] | None]:
    csv_path, _, meta_path = check_data_files(RESULTS_DIR, prefix)
    parquet_path = os.path.join(RESULTS_DIR, f"{prefix}_case_summary.parquet")
    df = ensure_summary_geometry_columns(
        load_sweep_summary(csv_path, parquet_path=parquet_path)
    )
    meta = load_metadata(meta_path)
    health = load_result_health(RESULTS_DIR, prefix, summary_df=df)
    return df, meta, health

def _aggregate_wavelength_table(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(
            columns=[
                "wavelength_nm",
                "case_count",
                "gate_pass",
                "gate_rate",
                "recommended_default",
                "recommended_default_rate",
                "positive_final",
                "mean_final",
                "mean_detection",
                "mean_stable",
                "mean_phase_flip_ub",
                "mean_peak_margin_z",
            ]
        )

    table = (
        df.groupby("wavelength_nm", dropna=False)
        .agg(
            case_count=("wavelength_nm", "size"),
            gate_pass=("engineering_gate_passed", lambda s: int(pd.Series(s).fillna(False).astype(bool).sum())),
            gate_rate=("engineering_gate_passed", _safe_bool_mean),
            recommended_default=("design_recommendation_status", lambda s: _safe_sum_matches(s, "recommended_default")),
            recommended_default_rate=("design_recommendation_status", lambda s: _safe_bool_mean(pd.Series(s).fillna("") == "recommended_default")),
            positive_final=("final_engineering_score", lambda s: int((pd.to_numeric(s, errors="coerce") > 0).sum())),
            mean_final=("final_engineering_score", "mean"),
            mean_detection=("engineering_basis_detection_rate", "mean"),
            mean_stable=("engineering_basis_stable_detection_rate", "mean"),
            mean_phase_flip_ub=("engineering_basis_phase_flip_fraction_wilson_ub", "mean"),
            mean_peak_margin_z=("engineering_basis_mean_peak_margin_z", "mean"),
        )
        .reset_index()
        .sort_values(
            ["recommended_default", "gate_pass", "mean_final", "mean_stable"],
            ascending=[False, False, False, False],
        )
        .reset_index(drop=True)
    )
    return table

def _format_order(order: list[int]) -> str:
    return " > ".join(f"`{int(wl)}`" for wl in order)

def _metric_card(label: str, value: str, caption: str) -> None:
    st.metric(label, value)
    st.caption(caption)

def _bar_figure(
    table: pd.DataFrame,
    *,
    x_col: str,
    y_col: str,
    title: str,
    y_axis_title: str,
    percent: bool = False,
) -> go.Figure:
    x_values = [f"{int(v)} nm" for v in table[x_col].tolist()]
    y_values = table[y_col].tolist()
    colors = [WAVELENGTH_COLORS.get(int(v), "#6B7280") for v in table[x_col].tolist()]
    if percent:
        text = [f"{float(v):.1%}" for v in y_values]
    else:
        text = [f"{float(v):.3f}" if isinstance(v, (float, np.floating)) else str(v) for v in y_values]

    fig = go.Figure(
        data=[
            go.Bar(
                x=x_values,
                y=y_values,
                marker_color=colors,
                text=text,
                textposition="outside",
            )
        ]
    )
    fig.update_layout(
        title=title,
        height=340,
        margin=dict(l=24, r=24, t=64, b=24),
        yaxis_title=y_axis_title,
        xaxis_title="波长",
    )
    if percent:
        fig.update_yaxes(tickformat=".0%")
    return fig

def _load_primary_story_inputs() -> tuple[str, pd.DataFrame, dict[str, Any], dict[str, Any] | None]:
    prefix = _resolve_story_dataset_prefix()
    df, meta, health = _load_named_dataset(prefix)
    return prefix, df, meta, health

def _resolve_story_dataset_prefix() -> str:
    available = list_available_datasets(RESULTS_DIR)
    if PRIMARY_STORY_PREFIX not in available:
        preview = ", ".join(available[:8]) if available else "(none)"
        raise FileNotFoundError(
            "科研展示主线要求结果库 "
            f"`{PRIMARY_STORY_PREFIX}`，当前 results/ 中未找到。"
            f"可用结果库: {preview}"
        )
    return PRIMARY_STORY_PREFIX

def _filter_default_ready_within_envelope(df: pd.DataFrame) -> pd.DataFrame:
    sub = df.copy()
    sub = sub[sub["observation_freeze_status"] == "default_ready_for_result_freeze"]
    sub = sub[sub["rho_physical_envelope_status"] == "within_envelope"]
    return sub

def _aggregate_band_wavelength_table(
    df: pd.DataFrame,
    *,
    material: str,
    band_specs: list[tuple[str, int, int]],
    conservative: bool = False,
) -> pd.DataFrame:
    source = df[df["particle_material"] == material].copy()
    if conservative:
        source = _filter_default_ready_within_envelope(source)
    rows: list[dict[str, Any]] = []
    for band_order, (band_label, low_nm, high_nm) in enumerate(band_specs):
        band = source[
            (source["particle_diameter_nm"] >= low_nm)
            & (source["particle_diameter_nm"] <= high_nm)
        ].copy()
        if band.empty:
            continue
        for wavelength_nm, sub in band.groupby("wavelength_nm", dropna=False):
            rows.append(
                {
                    "band_label": band_label,
                    "band_order": band_order,
                    "wavelength_nm": int(wavelength_nm),
                    "case_count": int(len(sub)),
                    "gate_rate": _safe_bool_mean(sub["engineering_gate_passed"]),
                    "recommended_default_rate": _safe_bool_mean(pd.Series(sub["design_recommendation_status"]).fillna("") == "recommended_default"),
                    "mean_final": float(pd.to_numeric(sub["final_engineering_score"], errors="coerce").mean()),
                    "mean_detection": float(pd.to_numeric(sub["detection_rate"], errors="coerce").mean()),
                    "mean_stable": float(pd.to_numeric(sub["stable_detection_rate"], errors="coerce").mean()),
                    "max_final": float(pd.to_numeric(sub["final_engineering_score"], errors="coerce").max()),
                }
            )
    return pd.DataFrame(rows)

def _band_heatmap_figure(
    table: pd.DataFrame,
    metric_col: str,
    title: str,
    *,
    colorbar_title: str,
    percent: bool = False,
) -> go.Figure:
    fig = go.Figure()
    if table.empty:
        fig.update_layout(title=title, height=380)
        return fig
    order = table[["band_label", "band_order"]].drop_duplicates().sort_values("band_order")
    band_labels = order["band_label"].tolist()
    wavelength_order = sorted(int(v) for v in table["wavelength_nm"].unique())
    pivot = (
        table.pivot(index="band_label", columns="wavelength_nm", values=metric_col)
        .reindex(index=band_labels, columns=wavelength_order)
    )
    text = []
    for row in pivot.to_numpy(dtype=float):
        text.append([
            "N/A"
            if not np.isfinite(value)
            else f"{float(value):.1%}" if percent else f"{float(value):.3f}"
            for value in row
        ])
    fig.add_trace(
        go.Heatmap(
            z=pivot.to_numpy(dtype=float),
            x=[f"{int(v)} nm" for v in wavelength_order],
            y=band_labels,
            text=text,
            texttemplate="%{text}",
            colorscale="YlGnBu",
            colorbar_title=colorbar_title,
        )
    )
    fig.update_layout(
        title=title,
        height=380,
        margin=dict(l=24, r=24, t=64, b=24),
        xaxis_title="波长",
        yaxis_title="粒径分组",
    )
    return fig

def _segment_window_table(
    df: pd.DataFrame,
    *,
    material: str,
    low_nm: int,
    high_nm: int,
    top_k: int = 6,
) -> pd.DataFrame:
    sub = df[
        (df["particle_material"] == material)
        & (df["particle_diameter_nm"] >= low_nm)
        & (df["particle_diameter_nm"] <= high_nm)
    ].copy()
    sub = _filter_default_ready_within_envelope(sub)
    if sub.empty:
        return pd.DataFrame()
    table = (
        sub.groupby(["wavelength_nm", "width_nm", "depth_nm"], dropna=False)
        .agg(
            case_count=("particle_diameter_nm", "size"),
            recommended_default_count=("design_recommendation_status", lambda s: _safe_sum_matches(s, "recommended_default")),
            recommended_default_rate=("design_recommendation_status", lambda s: _safe_bool_mean(pd.Series(s).fillna("") == "recommended_default")),
            mean_final=("final_engineering_score", "mean"),
            mean_detection=("detection_rate", "mean"),
            mean_stable=("stable_detection_rate", "mean"),
        )
        .reset_index()
    )
    table["coverage_label"] = np.where(
        table["recommended_default_rate"] >= 0.999,
        "整段全默认",
        np.where(table["recommended_default_rate"] >= 0.70, "高覆盖", "局部窗口"),
    )
    return table.sort_values(
        ["recommended_default_rate", "mean_final", "mean_detection", "mean_stable"],
        ascending=[False, False, False, False],
    ).head(top_k)

def _format_window_family(
    table: pd.DataFrame,
    *,
    wavelength_nm: int | None = None,
    top_k: int = 3,
    include_wavelength: bool = False,
) -> str:
    if table.empty:
        return "暂无稳定默认窗口"
    sub = table.copy()
    if wavelength_nm is not None:
        wavelength_sub = sub[sub["wavelength_nm"] == wavelength_nm].copy()
        if not wavelength_sub.empty:
            sub = wavelength_sub
    items: list[str] = []
    for row in sub.head(top_k).to_dict("records"):
        geometry = f"{int(row['width_nm'])}×{int(row['depth_nm'])} nm"
        label = f"{int(row['wavelength_nm'])} nm + {geometry}" if include_wavelength else geometry
        if label not in items:
            items.append(label)
    return " / ".join(items) if items else "暂无稳定默认窗口"

def _pick_top_window(table: pd.DataFrame, *, wavelength_nm: int | None = None) -> pd.Series | None:
    if table.empty:
        return None
    if wavelength_nm is not None:
        sub = table[table["wavelength_nm"] == wavelength_nm]
        if not sub.empty:
            return sub.iloc[0]
    return table.iloc[0]

def _format_window_case(row: pd.Series | None) -> str:
    if row is None:
        return "暂无"
    return f"{int(row['wavelength_nm'])} nm + {int(row['width_nm'])}×{int(row['depth_nm'])} nm"

def _format_wavelength_label(wavelength_nm: int | None) -> str:
    if wavelength_nm is None:
        return "N/A"
    return f"{int(wavelength_nm)} nm"

def _top_wavelengths(table: pd.DataFrame, top_k: int = 2) -> list[int]:
    if table.empty or "wavelength_nm" not in table.columns:
        return []
    return [int(v) for v in table["wavelength_nm"].head(top_k).tolist()]

def _window_range_label(
    table: pd.DataFrame,
    *,
    wavelength_nm: int | None = None,
    top_k: int = 6,
) -> str:
    if table.empty:
        return "暂无稳定默认窗口"
    sub = table.copy()
    if wavelength_nm is not None:
        wavelength_sub = sub[sub["wavelength_nm"] == wavelength_nm].copy()
        if not wavelength_sub.empty:
            sub = wavelength_sub
    sub = sub.head(top_k)
    if sub.empty:
        return "暂无稳定默认窗口"
    width_min = int(sub["width_nm"].min())
    width_max = int(sub["width_nm"].max())
    depth_min = int(sub["depth_nm"].min())
    depth_max = int(sub["depth_nm"].max())
    return f"W={width_min}–{width_max} nm, H={depth_min}–{depth_max} nm"

def _build_exosome_route_context(full_df: pd.DataFrame) -> dict[str, Any]:
    exosome_df = full_df[full_df["particle_material"] == "exosome"].copy()
    exosome_rank = _aggregate_wavelength_table(exosome_df)
    route_order = _top_wavelengths(exosome_rank, top_k=4)
    primary_wl = route_order[0] if len(route_order) >= 1 else None
    secondary_wl = route_order[1] if len(route_order) >= 2 else None

    conservative_exosome = _filter_default_ready_within_envelope(exosome_df)
    conservative_rank = _aggregate_wavelength_table(conservative_exosome)
    conservative_order = _top_wavelengths(conservative_rank, top_k=4)
    conservative_primary_wl = (
        conservative_order[0] if len(conservative_order) >= 1 else None
    )

    default_window_table = _segment_window_table(
        full_df,
        material="exosome",
        low_nm=90,
        high_nm=300,
    )
    primary_window = _pick_top_window(default_window_table, wavelength_nm=primary_wl)
    secondary_window = _pick_top_window(default_window_table, wavelength_nm=secondary_wl)
    strongest_default_window = _pick_top_window(default_window_table)

    return {
        "rank_table": exosome_rank,
        "conservative_rank_table": conservative_rank,
        "route_order": route_order,
        "route_order_text": _format_order(route_order) if route_order else "N/A",
        "primary_wl": primary_wl,
        "secondary_wl": secondary_wl,
        "primary_label": _format_wavelength_label(primary_wl),
        "secondary_label": _format_wavelength_label(secondary_wl),
        "conservative_primary_wl": conservative_primary_wl,
        "conservative_primary_label": _format_wavelength_label(conservative_primary_wl),
        "default_window_table": default_window_table,
        "primary_window": primary_window,
        "secondary_window": secondary_window,
        "strongest_default_window": strongest_default_window,
        "primary_window_family": _format_window_family(
            default_window_table,
            wavelength_nm=primary_wl,
        ),
        "secondary_window_family": _format_window_family(
            default_window_table,
            wavelength_nm=secondary_wl,
        ),
        "primary_window_range": _window_range_label(
            default_window_table,
            wavelength_nm=primary_wl,
        ),
        "secondary_window_range": _window_range_label(
            default_window_table,
            wavelength_nm=secondary_wl,
        ),
        "strongest_default_window_text": _format_window_case(strongest_default_window),
        "strongest_default_window_range": _window_range_label(default_window_table),
    }

def _aggregate_dimension_profile(
    df: pd.DataFrame,
    *,
    material: str,
    dimension_col: str,
    wavelengths: list[int] | None = None,
    conservative: bool = True,
) -> pd.DataFrame:
    source = df[df["particle_material"] == material].copy()
    if conservative:
        source = _filter_default_ready_within_envelope(source)
    if wavelengths is not None:
        source = source[source["wavelength_nm"].isin(wavelengths)].copy()
    if source.empty:
        return pd.DataFrame()
    return (
        source.groupby(["wavelength_nm", dimension_col], dropna=False)
        .agg(
            case_count=(dimension_col, "size"),
            recommended_default_rate=(
                "design_recommendation_status",
                lambda s: _safe_bool_mean(pd.Series(s).fillna("") == "recommended_default"),
            ),
            mean_final=("final_engineering_score", "mean"),
            mean_detection=("detection_rate", "mean"),
            mean_stable=("stable_detection_rate", "mean"),
        )
        .reset_index()
        .sort_values(["wavelength_nm", dimension_col])
        .reset_index(drop=True)
    )

def _dimension_profile_figure(
    table: pd.DataFrame,
    *,
    dimension_col: str,
    metric_col: str,
    title: str,
    y_axis_title: str,
    percent: bool = False,
) -> go.Figure:
    fig = go.Figure()
    if table.empty:
        fig.update_layout(title=title, height=360)
        return fig
    for wavelength_nm in sorted(int(v) for v in table["wavelength_nm"].unique()):
        sub = table[table["wavelength_nm"] == wavelength_nm].sort_values(dimension_col)
        fig.add_trace(
            go.Scatter(
                name=f"{wavelength_nm} nm",
                x=sub[dimension_col].tolist(),
                y=sub[metric_col].tolist(),
                mode="lines+markers",
                line=dict(color=WAVELENGTH_COLORS.get(wavelength_nm, "#6B7280"), width=3),
                marker=dict(size=7),
            )
        )
    fig.update_layout(
        title=title,
        height=360,
        margin=dict(l=24, r=24, t=64, b=24),
        xaxis_title="W (nm)" if dimension_col == "width_nm" else "H (nm)",
        yaxis_title=y_axis_title,
    )
    if percent:
        fig.update_yaxes(tickformat=".0%")
    return fig

def _geometry_heatmap_table(
    df: pd.DataFrame,
    *,
    material: str,
    low_nm: int,
    high_nm: int,
    wavelength_nm: int,
    conservative: bool = True,
) -> pd.DataFrame:
    source = df[
        (df["particle_material"] == material)
        & (df["particle_diameter_nm"] >= low_nm)
        & (df["particle_diameter_nm"] <= high_nm)
        & (df["wavelength_nm"] == wavelength_nm)
    ].copy()
    if conservative:
        source = _filter_default_ready_within_envelope(source)
    if source.empty:
        return pd.DataFrame()
    return (
        source.groupby(["depth_nm", "width_nm"], dropna=False)
        .agg(
            case_count=("particle_diameter_nm", "size"),
            recommended_default_rate=(
                "design_recommendation_status",
                lambda s: _safe_bool_mean(pd.Series(s).fillna("") == "recommended_default"),
            ),
            mean_final=("final_engineering_score", "mean"),
            mean_detection=("detection_rate", "mean"),
            mean_stable=("stable_detection_rate", "mean"),
        )
        .reset_index()
    )

def _geometry_heatmap_figure(
    table: pd.DataFrame,
    *,
    metric_col: str,
    title: str,
    colorbar_title: str,
    percent: bool = False,
) -> go.Figure:
    fig = go.Figure()
    if table.empty:
        fig.update_layout(title=title, height=400)
        return fig
    depth_order = sorted(int(v) for v in table["depth_nm"].unique())
    width_order = sorted(int(v) for v in table["width_nm"].unique())
    pivot = (
        table.pivot(index="depth_nm", columns="width_nm", values=metric_col)
        .reindex(index=depth_order, columns=width_order)
    )
    text = []
    for row in pivot.to_numpy(dtype=float):
        text.append(
            [
                "N/A"
                if not np.isfinite(value)
                else f"{float(value):.1%}" if percent else f"{float(value):.3f}"
                for value in row
            ]
        )
    fig.add_trace(
        go.Heatmap(
            z=pivot.to_numpy(dtype=float),
            x=width_order,
            y=depth_order,
            text=text,
            texttemplate="%{text}",
            colorscale="YlGnBu" if percent else "Viridis",
            colorbar_title=colorbar_title,
        )
    )
    fig.update_layout(
        title=title,
        height=400,
        margin=dict(l=24, r=24, t=64, b=24),
        xaxis_title="W (nm)",
        yaxis_title="H (nm)",
    )
    return fig

def _rank_band_route_table(table: pd.DataFrame) -> pd.DataFrame:
    if table.empty:
        return table
    return table.sort_values(
        ["recommended_default_rate", "mean_final", "mean_detection", "mean_stable"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)

def _band_route_context(
    df: pd.DataFrame,
    *,
    band_label: str,
    low_nm: int,
    high_nm: int,
) -> dict[str, Any]:
    band_table = _aggregate_band_wavelength_table(
        df,
        material="exosome",
        band_specs=[(band_label, low_nm, high_nm)],
        conservative=False,
    )
    ranked_table = _rank_band_route_table(
        band_table.drop(columns=["band_label", "band_order"], errors="ignore")
    )
    windows = _segment_window_table(
        df,
        material="exosome",
        low_nm=low_nm,
        high_nm=high_nm,
    )
    primary_wl = (
        int(ranked_table.iloc[0]["wavelength_nm"]) if not ranked_table.empty else None
    )
    secondary_wl = (
        int(ranked_table.iloc[1]["wavelength_nm"])
        if len(ranked_table) > 1
        else None
    )
    return {
        "band_label": band_label,
        "table": ranked_table,
        "windows": windows,
        "primary_wl": primary_wl,
        "secondary_wl": secondary_wl,
        "primary_label": _format_wavelength_label(primary_wl),
        "secondary_label": _format_wavelength_label(secondary_wl),
        "primary_window_family": _format_window_family(
            windows,
            wavelength_nm=primary_wl,
            top_k=2,
        ),
        "secondary_window_family": _format_window_family(
            windows,
            wavelength_nm=secondary_wl,
            top_k=2,
        ),
    }

def _geometry_route_matrix(df: pd.DataFrame) -> pd.DataFrame:
    ctx_90_150 = _band_route_context(
        df,
        band_label="90–150 nm",
        low_nm=90,
        high_nm=150,
    )
    ctx_160_220 = _band_route_context(
        df,
        band_label="160–220 nm",
        low_nm=160,
        high_nm=220,
    )
    ctx_230_300 = _band_route_context(
        df,
        band_label="230–300 nm",
        low_nm=230,
        high_nm=300,
    )
    return pd.DataFrame(
        [
            {
                "分组": "90–150 nm exosome",
                "主路线": ctx_90_150["primary_label"],
                "主窗口": ctx_90_150["primary_window_family"],
                "备选": ctx_90_150["secondary_label"],
                "怎么读": "困难段先看该段自己的聚合排序，再看对应的 default-ready 平台。",
            },
            {
                "分组": "160–220 nm exosome",
                "主路线": ctx_160_220["primary_label"],
                "主窗口": ctx_160_220["primary_window_family"],
                "备选": ctx_160_220["secondary_label"],
                "怎么读": "中段更容易出现 tuned 平台，主线和备线都应一起保留。",
            },
            {
                "分组": "230–300 nm exosome",
                "主路线": ctx_230_300["primary_label"],
                "主窗口": ctx_230_300["primary_window_family"],
                "备选": ctx_230_300["secondary_label"],
                "怎么读": "大粒径段窗口会向更深或更宽扩张，要按当前段内排序读，不直接套总平均。",
            },
        ]
    )

def _top_caution_peak_table(df: pd.DataFrame, top_k: int = 10) -> pd.DataFrame:
    sub = df[df["particle_material"] == "exosome"].copy()
    sub = sub[
        (sub["design_recommendation_status"] == "recommended_with_caution")
        & (sub["observation_freeze_status"] == "caution_probe_before_result_freeze")
    ].copy()
    if sub.empty:
        return pd.DataFrame()
    return (
        sub.sort_values(
            ["final_engineering_score", "detection_rate", "particle_diameter_nm"],
            ascending=[False, False, False],
        )[
            [
                "particle_diameter_nm",
                "wavelength_nm",
                "width_nm",
                "depth_nm",
                "final_engineering_score",
                "design_recommendation_status",
                "observation_freeze_status",
            ]
        ]
        .head(top_k)
        .rename(
            columns={
                "particle_diameter_nm": "粒径 (nm)",
                "wavelength_nm": "波长 (nm)",
                "width_nm": "W (nm)",
                "depth_nm": "H (nm)",
                "final_engineering_score": "final score",
                "design_recommendation_status": "推荐标签",
                "observation_freeze_status": "freeze",
            }
        )
    )

def _width_engineering_table(df: pd.DataFrame) -> pd.DataFrame:
    sub = df[df["particle_material"] == "exosome"].copy()
    if sub.empty:
        return pd.DataFrame()
    return (
        sub.groupby("width_nm", dropna=False)
        .agg(
            default_ready_rate=(
                "observation_freeze_status",
                lambda s: _safe_bool_mean(pd.Series(s).fillna("") == "default_ready_for_result_freeze"),
            ),
            recommended_default_rate=(
                "design_recommendation_status",
                lambda s: _safe_bool_mean(pd.Series(s).fillna("") == "recommended_default"),
            ),
            mean_peak_height=("mean_peak_height", "mean"),
            detection_rate=("detection_rate", "mean"),
            mean_final=("final_engineering_score", "mean"),
            mean_A_ref=("A_ref", "mean"),
        )
        .reset_index()
        .rename(
            columns={
                "width_nm": "W (nm)",
                "default_ready_rate": "default ready rate",
                "recommended_default_rate": "recommended default rate",
                "mean_peak_height": "mean peak height",
                "detection_rate": "mean detect",
                "mean_final": "mean final",
                "mean_A_ref": "mean A_ref",
            }
        )
    )

def _shape_group_label(width_nm: int, depth_nm: int) -> str:
    delta = int(depth_nm) - int(width_nm)
    if delta <= -200:
        return "宽远大于深"
    if delta == -100:
        return "宽略大于深"
    if delta == 0:
        return "宽深接近"
    if delta == 100:
        return "深略大于宽"
    return "深远大于宽"

def _build_shape_group_table(df: pd.DataFrame) -> pd.DataFrame:
    sub = df[df["particle_material"] == "exosome"].copy()
    sub = _filter_default_ready_within_envelope(sub)
    sub = sub[sub["design_recommendation_status"] == "recommended_default"].copy()
    if sub.empty:
        return pd.DataFrame()
    sub["shape_group"] = [
        _shape_group_label(width_nm, depth_nm)
        for width_nm, depth_nm in zip(sub["width_nm"], sub["depth_nm"])
    ]
    order = {
        "宽远大于深": 0,
        "宽略大于深": 1,
        "宽深接近": 2,
        "深略大于宽": 3,
        "深远大于宽": 4,
    }
    table = (
        sub.groupby("shape_group", dropna=False)
        .agg(
            case_count=("shape_group", "size"),
            mean_final=("final_engineering_score", "mean"),
            mean_detection=("detection_rate", "mean"),
            mean_stable=("stable_detection_rate", "mean"),
        )
        .reset_index()
    )
    table["shape_order"] = table["shape_group"].map(order)
    return table.sort_values("shape_order").drop(columns="shape_order")

def _workflow_reading_table(route_context: Mapping[str, Any]) -> pd.DataFrame:
    primary_label = str(route_context.get("primary_label", "N/A"))
    secondary_label = str(route_context.get("secondary_label", "N/A"))
    strongest_default_window = str(
        route_context.get("strongest_default_window_text", "暂无稳定默认窗口")
    )
    return pd.DataFrame(
        [
            {"页面": "Decision Summary", "先回答的问题": "当前 biomimetic exosome 最新主库结论是什么", "重点图表": "决策一页表 + 阅读地图", "读完拿到的结论": f"{primary_label} 聚合主线、{secondary_label} 聚合第二路线、{strongest_default_window} 是当前最强默认平台"},
            {"页面": "Model Scope & Ranking", "先回答的问题": "当前结果库的模型口径、目标角色和排序原则是什么", "重点图表": "模型参数表 + 数据健康状态 + 排序原则表", "读完拿到的结论": "先按 exosome 选主线，再用 gold 做验证"},
            {"页面": "Exosome Route", "先回答的问题": f"为什么当前聚合排序是 {primary_label} 第一、{secondary_label} 第二", "重点图表": "四波长总表 + conservative 子集", "读完拿到的结论": "知道聚合排序与 default-ready 平台峰值是否一致"},
            {"页面": "Size-Band Selection", "先回答的问题": "不同粒径段该怎么分流和保留平台", "重点图表": "四段分组对比 + 每段窗口表", "读完拿到的结论": "40–80 先当锚点，90–150 明确选 404，中大粒径保留 488"},
            {"页面": "Engineering Windows", "先回答的问题": "工程保守线和研究上限线怎么分开", "重点图表": "上限尖峰表 + 宽深 profile + 形状组", "读完拿到的结论": "`W=500/600` 只看上限，默认平台缩到 `W=700–900, H=700–1000`"},
            {"页面": "Tsuyama Comparison", "先回答的问题": "Tsuyama 2024 在当前工程链里该放在哪个位置", "重点图表": "论文图表映射 + Tsuyama-like 几何切片 + 40–60 nm gold overlap", "读完拿到的结论": "论文强支撑平台原理和 gold 控制链，但不直接替代 exosome 主路线"},
            {"页面": "Validation Roadmap", "先回答的问题": "最后的 exosome 选型和 gold 验证顺序怎么落地", "重点图表": "选型矩阵 + gold 验证顺序 + 首批实验清单", "读完拿到的结论": "知道主路线、第二路线、gold bring-up 和不建议方向"},
        ]
    )

def _decision_one_pager_table(
    route_context: Mapping[str, Any],
    *,
    gold_top_label: str = "N/A",
) -> pd.DataFrame:
    primary_label = str(route_context.get("primary_label", "N/A"))
    secondary_label = str(route_context.get("secondary_label", "N/A"))
    primary_window_family = str(
        route_context.get("primary_window_family", "暂无稳定默认窗口")
    )
    secondary_window_family = str(
        route_context.get("secondary_window_family", "暂无稳定默认窗口")
    )
    strongest_default_window = str(
        route_context.get("strongest_default_window_text", "暂无稳定默认窗口")
    )
    strongest_default_window_range = str(
        route_context.get("strongest_default_window_range", "暂无稳定默认窗口")
    )
    return pd.DataFrame(
        [
            {"决策问题": "exosome 聚合主路线", "推荐": f"{primary_label} + {primary_window_family}", "适用范围": "90–300 nm 聚合 exosome 口径", "为什么": f"当前主库按 gate / recommended_default / mean final 聚合后，{primary_label} 排在第一。", "备注": f"对应稳定窗口范围：{route_context.get('primary_window_range', '暂无稳定默认窗口')}"},
            {"决策问题": "exosome 聚合第二路线", "推荐": f"{secondary_label} + {secondary_window_family}", "适用范围": "作为第二排序路线与交叉验证基线", "为什么": f"当前主库聚合排序中，{secondary_label} 是第二名，应保留为对照路线。", "备注": f"对应稳定窗口范围：{route_context.get('secondary_window_range', '暂无稳定默认窗口')}"},
            {"决策问题": "小 exosome", "推荐": "不作为当前主设计目标", "适用范围": "40–80 nm", "为什么": "这一段整体仍缺完整默认平台", "备注": "但 `80 nm + 404 + 700×700` 已经是一个默认-ready 工程锚点"},
            {"决策问题": "当前最强默认平台", "推荐": strongest_default_window, "适用范围": "default-ready + within-envelope 保守子集", "为什么": "它是当前主库默认工程口径里表现最强的窗口。", "备注": f"默认平台主范围：{strongest_default_window_range}"},
            {"决策问题": "研究上限线", "推荐": "W=500/600 nm 只作为研究上限", "适用范围": "理论峰值探索", "为什么": "这些点经常给出最高分尖峰，但 freeze 状态统一是 caution_probe_before_result_freeze", "备注": "不能直接替代默认工程方案"},
            {"决策问题": "gold 验证链", "推荐": f"小 gold 优先 {gold_top_label}；中大 gold 继续做多波长回归", "适用范围": "系统回归与 bring-up", "为什么": "gold 更像高对比参考链，适合验证系统健康，不应主导 exosome 选型", "备注": "大 gold 先建系统基准，再切回 exosome 主问题"},
        ]
    )

def render_research_overview() -> None:
    st.header("Decision Summary — 一页先拿到主结论和读图顺序")
    st.caption("这页只做一件事：把 38 号 biomimetic exosome 报告压成一页读图入口。先知道主路线、第二路线、默认几何和不建议方向，再决定往哪一层细看。")
    render_page_header_hub("Decision Summary")
    render_display_banner(
        eyebrow="Executive View",
        title="先拿结论，再决定细看哪一层证据",
        body="这页只围绕当前 biomimetic exosome 10000e 全量库回答 4 件事：主路线是谁、第二路线是谁、默认几何是什么、哪些高分点不该直接拿去做默认方案。",
        tone="info",
    )

    try:
        prefix, full_df, full_meta, _full_health = _load_primary_story_inputs()
    except (FileNotFoundError, ValueError) as exc:
        st.error(str(exc))
        return

    exosome_df = full_df[full_df["particle_material"] == "exosome"].copy()
    route_context = _build_exosome_route_context(full_df)
    gold_rank = _aggregate_wavelength_table(full_df[full_df["particle_material"] == "gold"])
    exosome_overall = (
        exosome_df.groupby("wavelength_nm", dropna=False)
        .agg(
            gate_rate=("engineering_gate_passed", _safe_bool_mean),
            recommended_default_rate=("design_recommendation_status", lambda s: _safe_bool_mean(pd.Series(s).fillna("") == "recommended_default")),
            mean_final=("final_engineering_score", "mean"),
        )
        .reset_index()
        .sort_values("wavelength_nm")
    )
    default_ready_fraction = _safe_bool_mean(
        pd.Series(full_df["observation_freeze_status"]).fillna("") == "default_ready_for_result_freeze"
    )
    conservative_band = _aggregate_band_wavelength_table(
        full_df,
        material="exosome",
        band_specs=EXOSOME_BAND_SPECS,
        conservative=True,
    )
    exosome_presets = sorted(
        {
            str(model.get("structure_params", {}).get("preset_name"))
            for model in full_meta.get("particle_models", [])
            if model.get("particle_material") == "exosome"
        }
        - {"None"}
    )
    preset_label = ", ".join(exosome_presets) if exosome_presets else "biomimetic_corona_nominal"

    metrics = st.columns(5)
    with metrics[0]:
        _metric_card("当前主库", prefix, f"{full_meta.get('n_events_per_case', 'N/A')} events/case")
    with metrics[1]:
        _metric_card("Exosome 口径", "biomimetic", f"preset={preset_label}")
    with metrics[2]:
        _metric_card("Exosome 聚合主路线", route_context["primary_label"], f"排序：{route_context['route_order_text']}")
    with metrics[3]:
        _metric_card("Exosome 聚合第二路线", route_context["secondary_label"], "来自同一主库聚合排序")
    with metrics[4]:
        _metric_card("最强默认平台", route_context["strongest_default_window_text"], f"default-ready={default_ready_fraction:.1%}")

    render_section_intro(
        title="一页决策表",
        body="如果你只看一页，这里应该已经足够回答：主路线是谁、第二路线是谁、小粒径怎么处理、几何保守线在哪里、研究上限线怎么和默认方案分开。",
        tone="success",
    )
    gold_top_label = _format_wavelength_label(
        _top_wavelengths(gold_rank, top_k=1)[0] if not gold_rank.empty else None
    )
    st.dataframe(
        _decision_one_pager_table(route_context, gold_top_label=gold_top_label),
        width="stretch",
        hide_index=True,
    )

    render_section_intro(
        title="先把这三句话记住",
        body="如果读者只带走三件事，应该是主路线、第二路线，以及哪些方向不要被局部高分误导。",
        tone="warning",
    )
    takeaway_cols = st.columns(3)
    with takeaway_cols[0]:
        st.success(
            f"先记聚合排序：`{route_context['primary_label']}` 第一，"
            f"`{route_context['secondary_label']}` 第二。"
        )
    with takeaway_cols[1]:
        st.info(
            f"当前最强 default-ready 平台是 `{route_context['strongest_default_window_text']}`；"
            "聚合路线和平台峰值需要分开读。"
        )
    with takeaway_cols[2]:
        st.warning("`W=500/600 nm` 的高分尖峰只代表研究上限；gold 只负责验证链，不负责定义 exosome 主设计。")

    with st.expander("查看 7 页阅读地图", expanded=False):
        st.dataframe(
            _workflow_reading_table(route_context),
            width="stretch",
            hide_index=True,
        )

    render_section_intro(
        title="先看这两张总览图",
        body="左图先回答 exosome 四波长总路线，右图先回答不同粒径段的默认平台覆盖率。读完这两张图，就知道为什么后面必须按粒径和几何继续拆开。",
        tone="neutral",
    )
    chart_cols = st.columns(2)
    with chart_cols[0]:
        st.plotly_chart(
            _bar_figure(
                exosome_overall,
                x_col="wavelength_nm",
                y_col="recommended_default_rate",
                title="Exosome 四波长总路线：recommended_default rate",
                percent=True,
                y_axis_title="recommended_default rate",
            ),
            width="stretch",
        )
    with chart_cols[1]:
        st.plotly_chart(
            _band_heatmap_figure(
                conservative_band,
                "recommended_default_rate",
                "Exosome 保守平台总览：各粒径段默认推荐率",
                colorbar_title="默认推荐率",
                percent=True,
            ),
            width="stretch",
        )

    with st.expander("查看当前 workflow 采用的数据口径", expanded=False):
        st.markdown(f"- 当前 workflow 主库：`{prefix}`")
        st.markdown(f"- 总 case：`{int(full_meta.get('n_cases', len(full_df))):,}`")
        st.markdown(f"- 每个 case：`{full_meta.get('n_events_per_case', 'N/A')}` events")
        st.markdown(f"- exosome 模型：`mie_core_shell`，preset=`{preset_label}`")
        st.markdown("- 任务主次：`exosome` 是主设计目标，`gold` 只作为系统验证链")
        st.markdown("- 排序原则：先看 `gate -> recommended_default -> freeze -> final score`")
        st.markdown("- 几何阅读口径：先看 `default_ready + within_envelope` 平台，再看研究上限尖峰")

def render_geometry_platform() -> None:
    st.header("Engineering Windows — 把研究上限线和工程保守线分开")
    st.caption("这页专门讲 38 号报告里最容易被误读的部分：最高分尖峰不等于默认工程方案。这里要把 `W=500/600 nm` 的研究上限线和 `W=700–900, H=700–1000 nm` 的工程保守线明确拆开。")
    render_page_header_hub("Engineering Windows")
    render_display_banner(
        eyebrow="Engineering Window",
        title="几何页不该盯着最高分点，而该先分清哪条是工程保守线",
        body="当前 biomimetic exosome 库里，很多最高分点都落在 `W=500/600 nm`，但它们统一是 `recommended_with_caution + caution_probe_before_result_freeze`。真正适合做默认方案的，是 `W=700–900, H=700–1000 nm` 的稳定平台带。",
        tone="warning",
    )

    try:
        prefix, full_df, full_meta, _ = _load_primary_story_inputs()
    except (FileNotFoundError, ValueError) as exc:
        st.error(str(exc))
        return

    shape_table = _build_shape_group_table(full_df)
    geometry_matrix = _geometry_route_matrix(full_df)
    width_engineering = _width_engineering_table(full_df)
    caution_peaks = _top_caution_peak_table(full_df, top_k=10)
    exosome_df = full_df[full_df["particle_material"] == "exosome"].copy()
    rho_404 = int(
        (
            (exosome_df["wavelength_nm"] == 404)
            & (pd.Series(exosome_df["rho_physical_envelope_status"]).fillna("") != "within_envelope")
        ).sum()
    )
    width_profile = _aggregate_dimension_profile(
        full_df,
        material="exosome",
        dimension_col="width_nm",
        wavelengths=[404, 488],
        conservative=True,
    )
    depth_profile = _aggregate_dimension_profile(
        full_df,
        material="exosome",
        dimension_col="depth_nm",
        wavelengths=[404, 488],
        conservative=True,
    )
    heatmap_specs = [
        ("90–150 nm @ 404 nm", 90, 150, 404, "困难段主平台：默认推荐率"),
        ("160–220 nm @ 488 nm", 160, 220, 488, "中段 tuned 平台：默认推荐率"),
        ("230–300 nm @ 404 nm", 230, 300, 404, "大粒径平台：默认推荐率"),
    ]

    shape_focus = "宽深接近 / 深略大于宽"
    if not shape_table.empty:
        shape_focus = " / ".join(
            shape_table.sort_values(
                ["mean_final", "mean_detection", "mean_stable"],
                ascending=[False, False, False],
            )["shape_group"].head(2)
        )

    metrics = st.columns(5)
    with metrics[0]:
        _metric_card("当前主库", prefix, f"{full_meta.get('n_events_per_case', 'N/A')} events/case")
    with metrics[1]:
        _metric_card("工程保守宽度带", "700–900 nm", "默认平台先缩到这里")
    with metrics[2]:
        _metric_card("工程保守深度带", "700–1000 nm", "深度更像调工作点")
    with metrics[3]:
        _metric_card("研究上限线", "W=500/600 nm", "高分尖峰统一属于 caution")
    with metrics[4]:
        _metric_card("形状偏好", shape_focus, f"404 还有 {rho_404} 个 rho 包络外 case 要记住")

    render_section_intro(
        title="先记住三条工程规则",
        body="展示页最重要的不是把所有 raw 明细摊开，而是先让读者记住这三条能直接指导选型的工程规则。",
        tone="success",
    )
    rule_cols = st.columns(3)
    with rule_cols[0]:
        st.success("先缩宽度：默认家族先保留 `W=700–900 nm`，`W=500/600 nm` 只看研究上限。")
    with rule_cols[1]:
        st.info("再定深度：`H=700–1000 nm` 是主工作带，其中 `900–1000 nm` 往往更稳。")
    with rule_cols[2]:
        st.warning("最后看形状：优先 `W≈H` 或 `H` 略大于 `W`，极端扁或极端深都不适合做全局默认。")

    with st.expander("查看研究上限尖峰和宽度明细", expanded=False):
        render_section_intro(
            title="研究上限线 vs 工程保守线",
            body="左边是当前 exosome 最高分的 caution 尖峰，右边是按宽度看的工程状态。这里主要用来解释为什么 `W=500/600 nm` 只能当上限，不能直接当默认。",
            tone="warning",
        )
        top_cols = st.columns([0.48, 0.52])
        with top_cols[0]:
            st.markdown("**研究上限尖峰（只当上限，不当默认）**")
            st.dataframe(
                caution_peaks.style.format({"final score": "{:.4f}"}),
                width="stretch",
                hide_index=True,
            )
        with top_cols[1]:
            st.markdown("**按宽度看的工程状态**")
            width_view = width_engineering[
                width_engineering["W (nm)"].isin([500, 600, 700, 800, 900, 1000, 1500, 2000])
            ].copy()
            st.dataframe(
                width_view.style.format(
                    {
                        "default ready rate": "{:.1%}",
                        "recommended default rate": "{:.1%}",
                        "mean peak height": "{:.3f}",
                        "mean detect": "{:.3f}",
                        "mean final": "{:.3f}",
                        "mean A_ref": "{:.3f}",
                    }
                ),
                width="stretch",
                hide_index=True,
            )

    render_section_intro(
        title="工程保守窗口家族",
        body="不同粒径段会把最佳几何推向不同窗口，但它们仍然收敛到一个很清晰的工程家族：宽度先缩到 700–900，深度再按段和波长微调。",
        tone="neutral",
    )
    st.dataframe(geometry_matrix, width="stretch", hide_index=True)

    render_section_intro(
        title="宽和深分别在做什么",
        body="下面两张 profile 图不是在找单点最优，而是在看不同宽度、不同深度沿着整条路线留下多少默认推荐窗口。读法上，宽度先定义家族，深度再定义工作点。",
        tone="warning",
    )
    profile_cols = st.columns(2)
    with profile_cols[0]:
        st.plotly_chart(
            _dimension_profile_figure(
                width_profile,
                dimension_col="width_nm",
                metric_col="recommended_default_rate",
                title="Exosome 默认平台：宽度 profile",
                y_axis_title="recommended_default rate",
                percent=True,
            ),
            width="stretch",
        )
    with profile_cols[1]:
        st.plotly_chart(
            _dimension_profile_figure(
                depth_profile,
                dimension_col="depth_nm",
                metric_col="recommended_default_rate",
                title="Exosome 默认平台：深度 profile",
                y_axis_title="recommended_default rate",
                percent=True,
            ),
            width="stretch",
        )
    st.caption("读法：宽度越往大走，404/488 的默认覆盖率都会持续下降；深度不是越浅越好，而是在 `900–1000 nm` 左右形成更稳的综合工作点。")

    render_section_intro(
        title="机制摘要",
        body="这两张表是 38 号报告里最值得拿来解释“为什么”的部分：一张讲谁在驱动峰值和检测率，一张讲 detection rate 最相关的量是什么。",
        tone="neutral",
    )
    mechanism_cols = st.columns(2)
    with mechanism_cols[0]:
        st.dataframe(
            _frame(MECHANISM_PRIORITY_ROWS).style.format(
                {
                    "波长": "{:.3f}",
                    "宽度": "{:.3f}",
                    "深度": "{:.3f}",
                    "粒径": "{:.3f}",
                }
            ),
            width="stretch",
            hide_index=True,
        )
    with mechanism_cols[1]:
        st.dataframe(
            _frame(DETECTION_CORRELATION_ROWS).style.format(
                {"与 detection_rate 的 Spearman 相关": "{:.3f}"}
            ),
            width="stretch",
            hide_index=True,
        )

    render_section_intro(
        title="代表性 W/H 热图",
        body="如果要看‘宽和深一起变’时平台长什么样，这里给三个最关键的代表段。困难段看 404，中段看 488，大粒径平台回到 404。",
        tone="neutral",
    )
    heatmap_tabs = st.tabs([label for label, *_ in heatmap_specs])
    for tab, (label, low_nm, high_nm, wavelength_nm, subtitle) in zip(heatmap_tabs, heatmap_specs):
        with tab:
            heatmap_table = _geometry_heatmap_table(
                full_df,
                material="exosome",
                low_nm=low_nm,
                high_nm=high_nm,
                wavelength_nm=wavelength_nm,
                conservative=True,
            )
            st.plotly_chart(
                _geometry_heatmap_figure(
                    heatmap_table,
                    metric_col="recommended_default_rate",
                    title=f"{label}：{subtitle}",
                    colorbar_title="默认推荐率",
                    percent=True,
                ),
                width="stretch",
            )
            st.caption(
                "这张图的读法是：先找连续高覆盖区域，而不是只找一个最亮格子。连续区域越宽，越适合拿来做默认平台。"
            )

    render_section_intro(
        title="形状组结论",
        body="最后用 shape group 把结论压成一句话：默认平台更偏向近方形或略深几何，而不是极端扁或极端深的长宽比。",
        tone="success",
    )
    if shape_table.empty:
        st.caption("当前没有足够数据生成 shape group 对比。")
    else:
        st.dataframe(
            shape_table.rename(
                columns={
                    "shape_group": "形状组",
                    "case_count": "cases",
                    "mean_final": "mean final",
                    "mean_detection": "mean detect",
                    "mean_stable": "mean stable",
                }
            ).style.format(
                {
                    "mean final": "{:.4f}",
                    "mean detect": "{:.4f}",
                    "mean stable": "{:.4f}",
                }
            ),
            width="stretch",
            hide_index=True,
        )
        st.caption("结论：默认平台优先保留 `W≈H` 或 `H` 略大于 `W`；极端扁平和极端深槽都更像局部窗口，而不是全局默认家族。")
