#!/usr/bin/env python3
# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportCallIssue=false, reportIndexIssue=false
from __future__ import annotations

import sys
from collections.abc import Iterable
from dataclasses import dataclass
from functools import cache
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
STAGE_B6_DIR = ROOT / "results/stage_b6_tau1ms_ev_gold_fullgrid_1000e_seed42_22worker_restart_20260514"
RAW_CSV = STAGE_B6_DIR / "seed_42_raw_rows.csv"
ROUTE_CSV = STAGE_B6_DIR / "derived_1000e/lens_b_ev_fullgrid_route_ranking.csv"
GOLD_CSV = STAGE_B6_DIR / "derived_1000e/lens_b_gold_anchor_tsuyama_diagnostic_summary.csv"
REPORT_PATH = ROOT / "reports/100_EV_NODI_lens_b_tau1ms_stage_b6_only_analysis.md"


Route = tuple[int, int, int]


@dataclass(frozen=True)
class RouteStats:
    route: Route
    csca_m2: float
    csca_proxy: float
    e_sca: float
    a_ref: float
    ae_product: float
    g_ref: float
    peak: float
    transit_ms: float
    snr: float
    all_detection: float
    selected_detection: float
    annulus_fraction: float
    reference_band: str


def pct(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def num(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}f}"


def sci(value: float, digits: int = 2) -> str:
    return f"{value:.{digits}e}"


def ratio(value: float, base: float, digits: int = 2) -> str:
    if base == 0 or pd.isna(base):
        return "NA"
    return f"{value / base:.{digits}f}x"


REPORT88_READER_CSCA_RATIO_TO_660 = {
    404: 7.10,
    488: 3.34,
    532: 2.37,
    660: 1.00,
}


def reader_csca_ratio(route: Route, base: Route) -> str:
    """Report-88-style fixed-panel intrinsic Csca stage ratio."""
    if route[0] == base[0]:
        return "1.00x"
    if base[0] == 660 and route[0] in REPORT88_READER_CSCA_RATIO_TO_660:
        return f"{REPORT88_READER_CSCA_RATIO_TO_660[route[0]]:.2f}x"
    return "NA"


def band_cn(value: str) -> str:
    if value == "electronics_noise_limited_useful":
        return "参考光可用"
    if value == "reference_too_weak":
        return "弱参考边界"
    if value == "mixed_reference_useful_and_too_weak":
        return "混合参考状态"
    return value


def compute_csca_table(ev: pd.DataFrame) -> pd.DataFrame:
    from dashboard.config import THETA_GRID_RAD, medium_for_particle, particle_from_name
    from nodi_simulator.intrinsic_scattering import compute_intrinsic_scattering

    rows: list[dict[str, object]] = []
    pairs = (
        ev[["particle_name", "wavelength_nm"]]
        .drop_duplicates()
        .sort_values(["particle_name", "wavelength_nm"])
    )
    for particle_name, wavelength_nm in pairs.itertuples(index=False):
        particle = particle_from_name(str(particle_name))
        medium = medium_for_particle(particle)
        intrinsic = compute_intrinsic_scattering(
            particle,
            medium,
            float(wavelength_nm) * 1e-9,
            THETA_GRID_RAD,
        )
        rows.append(
            {
                "particle_name": str(particle_name),
                "wavelength_nm": int(wavelength_nm),
                "Csca_m2": float(intrinsic["Csca_m2"]),
            }
        )
    return pd.DataFrame(rows)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[Route, RouteStats]]:
    raw = pd.read_csv(RAW_CSV, low_memory=False)
    routes = pd.read_csv(ROUTE_CSV, low_memory=False)
    gold = pd.read_csv(GOLD_CSV, low_memory=False)
    ev = raw[raw["particle_material"].astype(str).eq("exosome")].copy()
    ev["wavelength_nm"] = pd.to_numeric(ev["wavelength_nm"], errors="coerce").astype(int)
    csca = compute_csca_table(ev)
    raw = raw.merge(csca, on=["particle_name", "wavelength_nm"], how="left")
    ev = raw[raw["particle_material"].astype(str).eq("exosome")].copy()
    for col in [
        "wavelength_nm",
        "width_nm",
        "depth_nm",
        "particle_diameter_nm",
        "E_sca_normalized",
        "A_ref",
        "g_ref",
        "mean_peak_height",
        "mean_transit_time_ms",
        "mean_local_snr",
        "all_crossing_detection_rate",
        "selected_detector_mode_annulus_detection_rate",
        "selected_detector_mode_annulus_fraction",
        "Csca_m2",
    ]:
        ev[col] = pd.to_numeric(ev[col], errors="coerce")

    grouped: dict[Route, RouteStats] = {}
    for key, sub in ev.groupby(["wavelength_nm", "width_nm", "depth_nm"], sort=False):
        route = (int(key[0]), int(key[1]), int(key[2]))
        e = sub["E_sca_normalized"].astype(float)
        grouped[route] = RouteStats(
            route=route,
            csca_m2=float(sub["Csca_m2"].mean()),
            csca_proxy=float((e * e).mean()),
            e_sca=float(e.mean()),
            a_ref=float(sub["A_ref"].mean()),
            ae_product=float((sub["A_ref"] * sub["E_sca_normalized"]).mean()),
            g_ref=float(sub["g_ref"].mean()),
            peak=float(sub["mean_peak_height"].mean()),
            transit_ms=float(sub["mean_transit_time_ms"].mean()),
            snr=float(sub["mean_local_snr"].mean()),
            all_detection=float(sub["all_crossing_detection_rate"].mean()),
            selected_detection=float(sub["selected_detector_mode_annulus_detection_rate"].mean()),
            annulus_fraction=float(sub["selected_detector_mode_annulus_fraction"].mean()),
            reference_band=str(sub["reference_operating_band"].mode().iat[0]),
        )
    return raw, routes, gold, grouped


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    out.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(out)


def profile_detection_table(routes: pd.DataFrame, route_list: list[Route]) -> str:
    rows: list[list[str]] = []
    for w, width, depth in route_list:
        r = routes[
            (routes["wavelength_nm"].astype(int) == w)
            & (routes["width_nm"].astype(int) == width)
            & (routes["depth_nm"].astype(int) == depth)
        ].iloc[0]
        rows.append(
            [
                f"{w} / {width} x {depth}",
                pct(float(r["uniform_weighted_selected_annulus_detection"])),
                pct(float(r["small_ev_literature_weighted_selected_annulus_detection"])),
                pct(float(r["broad_ev_literature_weighted_selected_annulus_detection"])),
                pct(float(r["sharp_msc_sev_empirical_weighted_selected_annulus_detection"])),
                band_cn(str(r["reference_operating_band"])),
            ]
        )
    return md_table(
        ["路线", "均匀粒径假设", "小 EV 文献假设", "宽 EV 文献假设", "尖锐小 EV 假设", "参考光状态"],
        rows,
    )


def route_chain_table(stats: dict[Route, RouteStats], route_list: list[Route], base: Route) -> str:
    b = stats[base]
    rows: list[list[str]] = []
    for route in route_list:
        s = stats[route]
        rows.append(
            [
                f"{route[0]} / {route[1]} x {route[2]}",
                reader_csca_ratio(route, base),
                ratio(s.csca_proxy, b.csca_proxy),
                ratio(s.e_sca, b.e_sca),
                ratio(s.a_ref, b.a_ref),
                ratio(s.peak, b.peak),
                num(s.transit_ms, 2),
                ratio(s.snr, b.snr),
                pct(s.all_detection),
                pct(s.selected_detection),
                band_cn(s.reference_band),
            ]
        )
    return md_table(
        [
            "路线",
            "Mie Csca",
            "散射强度代理",
            "散射场幅值",
            "参考场幅值",
            "平均峰值",
            "通过时间 ms",
            "局部 SNR",
            "全穿越检测率",
            "选定环带检测率",
            "参考光状态",
        ],
        rows,
    )


def abs_ratio_pair(left: float, right: float, digits: int = 3) -> str:
    if right == 0 or pd.isna(right):
        return f"{num(left, digits)} / {num(right, digits)}"
    return f"{num(left, digits)} / {num(right, digits)} ({left / right:.2f}x)"


def abs_sci_ratio_pair(left: float, right: float, digits: int = 2) -> str:
    if right == 0 or pd.isna(right):
        return f"{sci(left, digits)} / {sci(right, digits)}"
    return f"{sci(left, digits)} / {sci(right, digits)} ({left / right:.2f}x)"


def route_label(route: Route) -> str:
    return f"{route[0]} / {route[1]} x {route[2]}"


def minmax(values: Iterable[float]) -> tuple[float, float]:
    vals = [float(v) for v in values]
    return min(vals), max(vals)


def pct_range(values: Iterable[float]) -> str:
    lo, hi = minmax(values)
    return f"{pct(lo)}-{pct(hi)}"


def num_range(values: Iterable[float], digits: int = 2) -> str:
    lo, hi = minmax(values)
    return f"{num(lo, digits)}-{num(hi, digits)}"


def ratio_range(values: Iterable[float], base: float, digits: int = 2) -> str:
    vals = [float(v) for v in values]
    if base == 0 or pd.isna(base):
        return "NA"
    return f"{min(vals) / base:.{digits}f}-{max(vals) / base:.{digits}f}x"


def absolute_with_ratio_range(values: Iterable[float], digits: int = 4) -> str:
    lo, hi = minmax(values)
    if lo == 0 or pd.isna(lo):
        return f"{num(lo, digits)} -> {num(hi, digits)}"
    return f"{num(lo, digits)} -> {num(hi, digits)} ({hi / lo:.1f}x)"


def driver_summary_table(raw: pd.DataFrame, stats: dict[Route, RouteStats]) -> str:
    sizes = [40, 50, 60, 80, 100, 150, 200, 250, 300]
    particle_sub = raw[
        (raw["particle_material"].astype(str) == "exosome")
        & (raw["wavelength_nm"].astype(int) == 660)
        & (raw["width_nm"].astype(int) == 800)
        & (raw["depth_nm"].astype(int) == 1100)
        & (raw["particle_diameter_nm"].astype(int).isin(sizes))
    ].copy()

    wavelength_routes = [(w, 800, 1100) for w in (404, 488, 532, 660)]
    height_routes = [(660, 800, d) for d in (500, 550, 600, 650, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500)]
    width_routes = [(660, w, 1100) for w in range(500, 1600, 100)]
    useful_width_routes = [r for r in width_routes if stats[r].reference_band == "electronics_noise_limited_useful"]

    rows = [
        [
            "粒子尺寸",
            "660 / 800 x 1100；粒径 40-300 nm",
            absolute_with_ratio_range(particle_sub["mean_peak_height"], 4),
            num_range(particle_sub["mean_transit_time_ms"], 2),
            pct_range(particle_sub["selected_detector_mode_annulus_detection_rate"]),
            "最大驱动项：小 EV 先天峰值低，因此最容易漏检；大 EV 接近饱和后，检测率主要受轨迹和环带分母限制。",
        ],
        [
            "波长",
            "固定 800 x 1100；404/488/532/660 nm",
            ratio_range([stats[r].peak for r in wavelength_routes], stats[(660, 800, 1100)].peak),
            num_range([stats[r].transit_ms for r in wavelength_routes], 2),
            pct_range([stats[r].selected_detection for r in wavelength_routes]),
            "波长能改变散射阶段、参考场和通过时间，但在当前中心尺寸下，检测率跨度小于粒径跨度。",
        ],
        [
            "通道高度",
            "固定 660 nm / 800 nm 宽；高度 500-1500 nm",
            ratio_range([stats[r].peak for r in height_routes], stats[(660, 800, 1100)].peak),
            num_range([stats[r].transit_ms for r in height_routes], 2),
            pct_range([stats[r].selected_detection for r in height_routes]),
            "高度主要调参考场和停留时间；1000-1400 nm 是宽平台，不是一个脆弱单点。",
        ],
        [
            "通道宽度",
            "固定 660 nm / 1100 nm 高；宽度 500-1500 nm",
            ratio_range([stats[r].peak for r in width_routes], stats[(660, 800, 1100)].peak),
            num_range([stats[r].transit_ms for r in width_routes], 2),
            pct_range([stats[r].selected_detection for r in width_routes]),
            "窄宽度会把参考场和峰值推得很高，但 500-700 nm 被标成弱参考边界，不能直接发布为推荐。",
        ],
        [
            "发布可用宽度",
            "同上，但只看参考光可用的宽度 800-1500 nm",
            ratio_range([stats[r].peak for r in useful_width_routes], stats[(660, 800, 1100)].peak),
            num_range([stats[r].transit_ms for r in useful_width_routes], 2),
            pct_range([stats[r].selected_detection for r in useful_width_routes]),
            "去掉弱参考后，800 nm 宽度成为 660 nm 推荐族的左边界和最高分位置。",
        ],
    ]
    return md_table(
        ["影响因素", "固定条件 / 扫描范围", "平均峰值变化", "通过时间 ms", "选定环带检测率", "读法"],
        rows,
    )


def wavelength_404_660_explanation_table(stats: dict[Route, RouteStats]) -> str:
    geometries = [
        ((800, 1100), "默认中心；404 的参考场更强，但散射代理略低，峰值只小幅高。"),
        ((800, 1000), "宽粒径 EV 邻近候选；趋势与默认中心相同。"),
        ((800, 1400), "高度加深后 404 的参考场优势变小，平均峰值几乎持平。"),
        ((500, 1100), "404 fixed-view 候选宽度背景；660 在此尺寸是弱参考边界，所以只作机制对照。"),
        ((800, 550), "类似论文锚点几何；404 峰值较高，但通过时间仍明显短。"),
    ]
    rows: list[list[str]] = []
    for (width, depth), note in geometries:
        s404 = stats[(404, width, depth)]
        s660 = stats[(660, width, depth)]
        rows.append(
            [
                f"{width} x {depth}",
                reader_csca_ratio((404, width, depth), (660, width, depth)),
                abs_ratio_pair(s404.csca_proxy, s660.csca_proxy),
                abs_ratio_pair(s404.a_ref, s660.a_ref),
                abs_ratio_pair(s404.peak, s660.peak),
                f"{num(s404.transit_ms, 2)} / {num(s660.transit_ms, 2)}",
                f"{pct(s404.selected_detection)} / {pct(s660.selected_detection)}",
                note,
            ]
        )
    return md_table(
        [
            "固定宽度 x 高度",
            "Mie Csca：404 / 660",
            "散射强度代理：404 / 660",
            "参考场幅值：404 / 660",
            "平均峰值：404 / 660",
            "通过时间 ms：404 / 660",
            "选定环带检测率：404 / 660",
            "读法",
        ],
        rows,
    )


def peak_recheck_table(stats: dict[Route, RouteStats]) -> str:
    rows: list[list[str]] = []
    for width, depth, note in [
        (800, 1100, "默认中心；平均峰值小幅高，但全穿越等效峰值几乎相同。"),
        (800, 1400, "高度加深后 660 的峰值系数更高，抵消了 404 的参考场优势。"),
        (500, 1100, "窄宽度下 660 弱参考导致参考场过强，峰值显著高但不可发布。"),
    ]:
        s404 = stats[(404, width, depth)]
        s660 = stats[(660, width, depth)]
        p404 = s404.peak / max(s404.ae_product, 1e-15)
        p660 = s660.peak / max(s660.ae_product, 1e-15)
        rows.append(
            [
                f"{width} x {depth}",
                abs_ratio_pair(s404.ae_product, s660.ae_product),
                abs_ratio_pair(s404.peak, s660.peak),
                abs_ratio_pair(p404, p660),
                abs_ratio_pair(s404.peak * s404.all_detection, s660.peak * s660.all_detection),
                note,
            ]
        )
    return md_table(
        [
            "固定宽度 x 高度",
            "参考场 x 散射场均值：404 / 660",
            "平均峰值：404 / 660",
            "峰值 / (参考场 x 散射场)：404 / 660",
            "全穿越等效峰值：404 / 660",
            "复核读法",
        ],
        rows,
    )


@cache
def au_baseline_ref_ratios(width: int, depth: int) -> dict[int, float]:
    from dashboard.config import BASELINE_PARTICLE, THETA_GRID_RAD, WATER
    from nodi_simulator.utils import compute_baseline_normalization_per_wavelength
    from tools.audits import tsuyama_gold_aligned_detection_lane as lane
    from tools.lens_b_ev_gold_fullgrid_runner import build_frozen_b_cfg

    cfg, optical_template = build_frozen_b_cfg(1, 42)
    wavelengths_m = np.asarray([404e-9, 488e-9, 532e-9, 660e-9], dtype=float)
    channel = lane.case_baseline_channel(width, depth)
    refs = compute_baseline_normalization_per_wavelength(
        BASELINE_PARTICLE,
        WATER,
        optical_template,
        wavelengths_m,
        THETA_GRID_RAD,
        channel=channel,
        sim_cfg=cfg,
    )
    ref_660 = float(refs[660e-9])
    return {int(round(wl * 1e9)): float(refs[float(wl)] / ref_660) for wl in wavelengths_m}


def baseline_normalization_audit_table(stats: dict[Route, RouteStats]) -> str:
    rows: list[list[str]] = []
    for width, depth, note in [
        (800, 1100, "默认中心；基准金颗粒归一化几乎抵消 404 的 EV 绝对 Csca 优势。"),
        (500, 1100, "404 fixed-view 候选宽度背景；归一化更强，且 660 为弱参考边界。"),
        (800, 550, "锚点几何；归一化强度与默认中心接近。"),
    ]:
        ref_ratio = au_baseline_ref_ratios(width, depth)[404]
        s404 = stats[(404, width, depth)]
        s660 = stats[(660, width, depth)]
        rows.append(
            [
                f"{width} x {depth}",
                f"{ref_ratio:.2f}x",
                reader_csca_ratio((404, width, depth), (660, width, depth)),
                ratio(s404.e_sca, s660.e_sca),
                ratio(s404.peak, s660.peak),
                note,
            ]
        )
    return md_table(
        [
            "固定宽度 x 高度",
            "Au 基准 E_sca_ref：404 / 660",
            "EV Mie Csca：404 / 660",
            "EV 归一化散射场：404 / 660",
            "平均峰值：404 / 660",
            "审查结论",
        ],
        rows,
    )


def normalization_revision_sensitivity_table(stats: dict[Route, RouteStats]) -> str:
    rows: list[list[str]] = []
    for width, depth, note in [
        (800, 1100, "默认中心；修正后 404 散射场不再被 Au 基准除掉。"),
        (800, 1000, "宽粒径邻近候选；应和默认中心一起重算。"),
        (800, 1400, "小 EV 压力测试高度；当前 660 略高但差距很小。"),
        (500, 1100, "404 fixed-view 候选宽度背景；660 弱参考，必须单独治理。"),
        (800, 550, "Tsuyama 几何邻近；用于锚点敏感性，不作 EV 推荐。"),
    ]:
        ref_ratio = au_baseline_ref_ratios(width, depth)[404]
        s404 = stats[(404, width, depth)]
        s660 = stats[(660, width, depth)]
        current_e_ratio = s404.e_sca / s660.e_sca
        fixed_660_e_ratio = current_e_ratio * ref_ratio
        current_a_ratio = s404.a_ref / s660.a_ref
        fixed_reference_cross_term = current_a_ratio * fixed_660_e_ratio
        same_unit_cross_term = (s404.ae_product / s660.ae_product) * ref_ratio * ref_ratio
        rows.append(
            [
                f"{width} x {depth}",
                f"{ref_ratio:.2f}x",
                f"{current_e_ratio:.2f}x",
                f"{fixed_660_e_ratio:.2f}x",
                f"{current_a_ratio:.2f}x",
                f"{fixed_reference_cross_term:.2f}x",
                f"{same_unit_cross_term:.2f}x",
                ratio(s404.peak, s660.peak),
                note,
            ]
        )
    return md_table(
        [
            "固定宽度 x 高度",
            "Au 基准 404/660",
            "当前归一化散射场",
            "固定 660 基准散射场估计",
            "当前参考场",
            "保守 cross-term 估计",
            "同单位 cross-term 尺度（非检测率）",
            "当前观测峰值",
            "方法判断",
        ],
        rows,
    )


def fixed_geometry_table(stats: dict[Route, RouteStats], width: int, depth: int) -> str:
    route_list = [(w, width, depth) for w in (404, 488, 532, 660)]
    base = (660, width, depth)
    return route_chain_table(stats, route_list, base)


def fixed_wavelength_depth_table(
    stats: dict[Route, RouteStats],
    wavelength: int,
    width: int,
    depths: Iterable[int],
    base_depth: int,
) -> str:
    route_list = [(wavelength, width, int(d)) for d in depths if (wavelength, width, int(d)) in stats]
    base = (wavelength, width, base_depth)
    return route_chain_table(stats, route_list, base)


def fixed_wavelength_width_table(
    stats: dict[Route, RouteStats],
    wavelength: int,
    depth: int,
    widths: Iterable[int],
    base_width: int,
) -> str:
    route_list = [(wavelength, int(w), depth) for w in widths if (wavelength, int(w), depth) in stats]
    base = (wavelength, base_width, depth)
    return route_chain_table(stats, route_list, base)


def particle_size_table(raw: pd.DataFrame, route: Route, sizes: Iterable[int]) -> str:
    w, width, depth = route
    sub = raw[
        (raw["particle_material"].astype(str) == "exosome")
        & (raw["wavelength_nm"].astype(int) == w)
        & (raw["width_nm"].astype(int) == width)
        & (raw["depth_nm"].astype(int) == depth)
    ].copy()
    rows: list[list[str]] = []
    for size in sizes:
        r = sub[sub["particle_diameter_nm"].astype(int) == int(size)]
        if r.empty:
            continue
        row = r.iloc[0]
        rows.append(
            [
                f"{int(size)}",
                sci(float(row["Csca_m2"]), 2),
                f"{float(row['E_sca_normalized']):.4g}",
                f"{float(row['mean_peak_height']):.4g}",
                f"{float(row['mean_local_snr']):.1f}",
                num(float(row["mean_transit_time_ms"]), 2),
                pct(float(row["all_crossing_detection_rate"])),
                pct(float(row["selected_detector_mode_annulus_detection_rate"])),
            ]
        )
    return md_table(
        ["粒径 nm", "Mie Csca m2", "散射场幅值", "平均峰值", "局部 SNR", "通过时间 ms", "全穿越检测率", "选定环带检测率"],
        rows,
    )


def gold_table(gold: pd.DataFrame) -> str:
    keep = gold[
        (gold["wavelength_nm"].astype(int) == 660)
        & (gold["width_nm"].astype(int).isin([800, 1200]))
        & (gold["depth_nm"].astype(int) == 550)
    ].copy()
    keep = keep.sort_values(["width_nm"])
    rows: list[list[str]] = []
    for _, r in keep.iterrows():
        rows.append(
            [
                f"{int(r['wavelength_nm'])} / {int(r['width_nm'])} x {int(r['depth_nm'])}",
                f"{float(r['raw_peak_exponent_20_60']):.6f}",
                f"{float(r['raw_peak_exponent_20_60_abs_residual_vs_2p3']):.6f}",
                pct(float(r["mean_anchor_all_crossing_detection"])),
                pct(float(r["mean_anchor_selected_annulus_detection"])),
                "否",
            ]
        )
    return md_table(
        ["锚点几何", "Au20-60 峰值指数", "相对 2.3 残差", "全穿越均值", "选定环带均值", "能否作 EV 推荐"],
        rows,
    )


def build_report() -> str:
    raw, routes, gold, stats = load_data()
    ev_rows = int((raw["particle_material"].astype(str) == "exosome").sum())
    gold_rows = int((raw["particle_material"].astype(str) == "gold").sum())
    route_count = int(routes.shape[0])
    current_routes = [
        (660, 800, 1100),
        (660, 800, 1000),
        (660, 800, 1400),
        (404, 500, 1100),
        (488, 600, 900),
        (660, 500, 550),
    ]
    sizes = [40, 50, 60, 80, 100, 150, 200, 250, 300]

    sections: list[str] = []
    sections.append(
        f"""# EV/NODI 口径 B 专项分析报告 v2.2：从“为什么能检测”开始的中文读者版

- 日期 / 版本：2026-05-15；v2.2；2026-06-12 标注为历史生成器。
- 数据来源：`{STAGE_B6_DIR.relative_to(ROOT)}/`。
- 当前证据规模：32,032 行，其中 EV（原始表标记为 exosome）{ev_rows:,} 行、金颗粒 {gold_rows:,} 行；EV 路线聚合后共 {route_count} 条路线。
- 当前运行配置：tau=1 ms（`lockin_time_constant_s = 0.001`），随机种子 42，每个工况 1000 个事件。
- 本报告只讨论口径 B。口径 B 是“以 Tsuyama 为锚点的 EV 应用读法”，不是全局工程主排序。
- 重要方法修正：Stage B6 使用“每个波长各自用金颗粒基准归一化”的口径。因此它能支持 Tsuyama 锚点诊断和同一波长内的几何排序，但**不能单独支撑 EV 跨波长绝对最终推荐**。本生成器产出的是历史 B6 解读；当前 no-data closure 以 `reports/140_*`、`reports/147_*`、`reports/148_*` 为准。

---

## 0. 先给结论

先把证据等级说清楚：下面的路线排序是 **Stage B6 的 gold-normalized、tau=1 ms、1000 events/case 历史设计读法**。它可以告诉我们“在当时 Tsuyama 锚定口径里哪一族最稳”，但还不能告诉我们“404 和 660 在绝对 EV 物理检测灵敏度上谁最终胜出”。

- **在这个历史 gold-normalized 口径里，领先的是一族路线：660 nm / 800 nm 宽度，1000-1400 nm 高度。**
- 历史中心可以写成 **660 / 800 x 1100 nm**。
- `660 / 800 x 1000 nm` 是宽粒径 EV 假设下的邻近候选；`660 / 800 x 1400 nm` 是尖锐小 EV 假设下的压力测试候选。当前总工程结论不再把 D1400/D1500 写成强制推荐，而是保留 D900-D1200 作为更保守工程带。
- **404 nm 没有被淘汰，也不能被当前归一化口径简单判负**：它在 tau=1 ms 下确实受益，绝对 Mie 散射也更强；后续 no-data closure 把它收口为 `404/W500` fixed-view candidate family。
- **488 / 532 不进入最终推荐**：它们只能作为趋势 / 对照。即使 488 在某些表中很高，也不能越过波长治理规则。
- **金颗粒行不参与 EV 推荐**：金颗粒只用来检查 Tsuyama 锚点和参数来源链。

当前 B6 证据仍是 **每工况 1000 个事件、单随机种子、低事件数历史设计证据**。它不是实测校准，不是 3-seed 10000e no-data closure，也不是跨波长绝对 winner 证据。

### 0.1 当前候选路线的检测率

下表中的检测率是口径 B 主读法：选定探测环带内的检测率，按不同 EV 粒径分布假设加权。"""
    )
    sections.append(profile_detection_table(routes, current_routes[:5]))
    sections.append(
        """
读法要分两层：

- 在 Stage B6 的 gold-normalized 口径里，660 / 800 宽度族在四个 EV 粒径分布假设下都稳定领先；404 / 500 x 1100 接近但没有超过；488 / 600 x 900 可以高分，但它是对照波长。
- 从方法审查角度看，这还不能结束 404 vs 660 的问题，因为当前归一化会把短波 EV 绝对散射优势除掉一部分。后续报告 140/147/148 已把问题改写为 fixed-view 与 per-wavelength-view 两个 candidate family，而非绝对 winner。

### 0.2 这版报告相对上一版最重要的改动

上一版已经解释了“404 的 Mie 散射截面更高，但归一化散射代理不高”。这版进一步修正结论边界：**这不是一个可以用文字解释过去的小现象，而是一个会影响跨波长推荐可信度的方法问题。**

因此本文把 Stage B6 结果定位为：

- 可以用于：同一 gold-normalized 口径下的路线排序、通道尺寸平台判断、噪声 / 阈值 / 弱参考边界解释、Tsuyama 锚点诊断。
- 不可用于：直接发布“660 在绝对 EV 跨波长检测物理上已经最终胜过 404”的结论。
- 当前状态：后续 no-data closure 已保留 `404/W500` fixed-view candidate 与 `660/W800` per-wavelength-view candidate；真正的绝对判决仍需实测 detector/noise/reference 校准。

---

## 1. 读者真正关心的问题：一条路线为什么能检测？

一条通道路线的检测率不是一个黑箱数字。它大致沿着下面的链条形成：

1. **粒子本征散射（Mie / 散射阶段）**：粒子在某个波长下本来能散射多少光。
2. **参考场幅值**：通道几何和光学模式给出多强的参考光。
3. **干涉峰值**：散射场与参考场叠加后，事件峰值有多高。
4. **通过时间**：粒子在光斑 / 通道读出区域停留多久；tau=1 ms 时，通过时间决定有效读出窗口。
5. **噪声与阈值**：峰值要穿过检测阈值；平均 SNR 高不等于每个事件都过阈值。
6. **选定环带分母**：口径 B 只把 Tsuyama 语义下的选定探测环带作为主读法。
7. **治理过滤**：404/660 才能进入最终推荐；488/532 只能作对照；金颗粒不能混入 EV 推荐。

### 1.1 本报告如何命名过程量

原始 CSV 有很多字段名。本报告不直接把字段名当解释，而按科学意义重命名：

| 报告名称 | 对应字段 / 计算 | 意义 | 注意 |
| --- | --- | --- | --- |
| Mie 散射截面 | `Csca_m2`，由粒子光学模型重新计算 | 粒子在该波长下的绝对散射截面 | 几何无关；同一波长和粒径下固定 |
| 散射场幅值 | `E_sca_normalized` | 粒子本征散射到检测方向后的相对场幅值 | 相对量，不是实测场强 |
| 散射强度代理 | `E_sca_normalized^2` | 进入检测链条后的归一化散射趋势 | 已被每波长基准粒子归一化，不等于绝对 `Csca_m2` |
| 参考场幅值 | `A_ref` | 通道几何和参考场模型给出的相对参考光幅值 | 仍是替代相对量 |
| 平均峰值 | `mean_peak_height` | 事件干涉峰值的平均高度 | 不等于检测率；还要过阈值和位置分布 |
| 通过时间 | `mean_transit_time_ms` | 粒子事件平均持续时间，单位 ms | 本报告不把它写成倍数 |
| 局部 SNR | `mean_local_snr` | 峰值相对局部噪声的平均余量 | 平均高不代表所有事件都过阈值 |
| 全穿越检测率 | `all_crossing_detection_rate` | 所有模拟穿越事件的检测率 | 反映整体分母 |
| 选定环带检测率 | `selected_detector_mode_annulus_detection_rate` | 落在选定探测环带内事件的检测率 | 口径 B 主检测率 |

这里的“散射强度代理”要特别小心：它用于回答“同一套检测链条内，进入读出模型后的相对散射场怎样变”；真正的绝对 Mie 散射截面由 `Csca_m2` 表示。二者不应该互相替代。

### 1.2 峰值增强是不是简单相乘？

不是。一个直觉式写法是：

```text
观测峰值 ≈ |E_ref + E_sca|^2 - |E_ref|^2
        ≈ 2 * A_ref * E_sca * cos(phase) + |E_sca|^2
```

所以本征散射和参考场会共同推高峰值，但最终峰值还会受到相位、位置、通道模式、选定环带、通过时间和锁相读出的影响。**不能把散射增强倍数、参考场增强倍数、峰值增强倍数简单相乘后当检测率。**

### 1.3 为什么峰值高，噪声仍然重要？

有三个原因：

- 检测是事件级阈值判断，不是只看平均峰值。小 EV、边缘轨迹、相位不利事件会拉低检测率。
- 全穿越分母包含很多不在选定环带的事件；它们的参考场 / 峰值条件不如主环带。
- 当前噪声和参考场仍是合成模型，没有接入实测空白噪声、后焦面 / 感兴趣区域图像、锁相 / 记录器轨迹。因此报告只能声明“合成相对设计证据”。

### 1.4 哪些变量影响最大？

下面先把几个变量放在同一张总览表里。这样读后面的细表时，读者能知道哪些变化是主效应，哪些只是局部微调。
"""
    )
    sections.append(driver_summary_table(raw, stats))
    sections.append(
        """
这张总览表给出的优先级是：**粒子尺寸最大，通道宽度受参考光治理强约束，通道高度给出宽平台，波长决定物理路线但不单独决定胜负。**

---

## 2. 当前推荐路线的物理链条

下面这张表把几条关键路线放在同一坐标系里。倍数都以 **660 / 800 x 1100** 为 1.00x。检测率用百分比；通过时间用 ms。请注意：这里的“推荐路线”指历史 gold-normalized Stage B6 口径下的设计排序，不是当前 140/147/148 的 no-data closure。"""
    )
    sections.append(route_chain_table(stats, current_routes, (660, 800, 1100)))
    sections.append(
        """
这张表回答几个最常见疑问，但结论边界必须守住：

- 404 的绝对 Mie Csca 更高，但归一化散射代理并不天然更高；它的峰值优势更多来自某些几何下的参考场和干涉项。短通过时间和小粒径漏检共同限制了当前 gold-normalized 检测率，所以它在 Stage B6 表内没有超过 660 主路线。
- 488 对照路线在某些几何上很强，但治理上仍是对照，不进入最终推荐。
- `660 / 500 x 550` 的原始分数很高，但参考光状态是弱参考边界；这种路线用于解释“高峰值不等于可发布推荐”。
- 这张表不能证明 404 在绝对 EV 跨波长灵敏度上已经输给 660；后续 no-data closure 已改用 candidate-family 边界表达，而不是把 B6 表升级为绝对判决。

---

## 3. 固定通道尺寸，看波长如何改变每一层

本节回答：“同一个通道尺寸下，换波长会让散射、参考场、峰值、通过时间和检测率怎样变化？”

每张表都以该尺寸下的 **660 nm** 为 1.00x。这样能直接看出 404 / 488 / 532 相对 660 的变化。表中倍数只在同一张表内有效；通过时间始终用 ms，检测率始终用百分比。

### 3.0 先解释一个容易误读的现象：为什么 404 和 660 差异不大？

第 3 章现在同时列出两种量：**Mie Csca** 和 **散射强度代理**。`Csca_m2` 是用粒子光学模型重新计算的绝对散射截面；散射强度代理来自 `E_sca_normalized^2`，而 `E_sca_normalized` 是相对基准金颗粒归一化后的检测方向散射场。

这就是为什么两者看起来不一样：当前运行配置使用每波长归一化，每个波长都会用同一基准金颗粒重新计算 `E_sca_ref`。这样做适合 Tsuyama anchor 的相对读法，但会压平一部分绝对波长散射差异。换句话说，**404 的绝对 Csca 可以明显大于 660，但归一化后进入检测链条的散射代理不一定大很多。**

从批判性审查看，这个归一化**不是无条件正确**。它的合理用途是“把各波长都放到各自的金颗粒锚点尺度上，做 Tsuyama lineage 的相对比较”；它的风险是“把 EV 自己的短波散射优势除掉一部分”。因此本报告不能只看归一化散射代理来判断短波是否有物理优势，必须同时列出 `Mie Csca`，并把当前 B6 结论写成 gold-normalized 设计证据，而不是跨波长绝对最终证据。
"""
    )
    sections.append(baseline_normalization_audit_table(stats))
    sections.append(
        """
这张审查表说明：按报告 88 的 strict physics reader 口径，EV 的本征 `Csca` 在 404 nm 是 660 nm 的约 7.10x；但 Au 基准 `E_sca_ref` 在 404 nm 也是 660 nm 的约 2.02x，而且当前 B6 进入检测链条的是 per-wavelength gold-normalized 后的散射场。归一化后，EV 散射场幅值变成约 0.98x。这个结果并非代码错误，而是归一化定义的直接后果。它适合锚定比较，但会弱化“404 对 EV 本征散射更强”的物理直觉。

为了判断这个问题是否只是“小修小补”，下面做一个不重跑模拟的敏感性换算。它只回答一个问题：如果不让 404 使用自己的 Au 基准去除，而是把 404 的散射场放回 660 金颗粒基准尺度，404 相对 660 的输入场会变多少？这不是新的检测率，也不是替代 B7 重算；它只用于判断当前归一化是否足以改变跨波长判断。
"""
    )
    sections.append(normalization_revision_sensitivity_table(stats))
    sections.append(
        """
敏感性表的读法如下：

- “当前归一化散射场”是 Stage B6 原始结果里真实进入检测链条的 `E_sca_normalized` 比值。
- “固定 660 基准散射场估计”把 404 的散射场重新乘回 `Au 基准 404/660`，近似回答“如果 404 不被自己的金颗粒基准除掉，会有多强”。
- “保守 cross-term 估计”只重标散射场，参考场沿用当前模型。
- “同单位 cross-term 尺度”把参考场和散射场都放到同一个 660 基准单位里；它说明量纲重标可能有多大，但不是峰值预测，也不能直接当检测率。

这张表给出的结论很强：默认 800 x 1100 下，404 当前归一化散射场只有 660 的约 0.98x，但固定 660 基准后会变成约 1.97x；保守 cross-term 估计约 2.55x。也就是说，当前 B6 的 per-wavelength gold normalization **足以显著改变 404 vs 660 的物理读法**。因此报告不能用当前 B6 直接宣布 660 已经在绝对 EV 跨波长灵敏度上胜出。

另外，第 3 章每一行是 27 个 EV 粒径点的路线均值，不是单一粒径的 Mie 曲线。粒径造成的峰值跨度可以达到约 178 倍，而 404 / 660 在固定尺寸下的路线均值差异会被粒径平均、检测方向归一化、参考相位、空间轨迹和选定环带共同压平。
"""
    )
    sections.append(wavelength_404_660_explanation_table(stats))
    sections.append(
        """
我也复核了平均峰值本身：报告没有重新模拟峰值，只是读取 Stage B6 原始行里的 `mean_peak_height` 并做路线均值。这个字段在运行器里是“检测到峰的事件”的峰值均值；没有检测到峰的事件不会以 0 进入这个均值。因此它不是“所有穿越事件的平均峰值”。为了检查是否有口径误导，下表补了一个简单的全穿越等效峰值：`mean_peak_height x all_crossing_detection_rate`。
"""
    )
    sections.append(peak_recheck_table(stats))
    sections.append(
        """
复核结论分两层：**没有发现报告聚合错误，但发现当前归一化口径不足以说服读者接受跨波长最终结论。**平均峰值差异偏小主要来自四件事：每波长基准归一化压平绝对 Csca；峰值均值只统计检测到峰的事件；相干干涉项包含相位和探测算子，不是 `Csca x A_ref`；404 通过时间更短，检测率被拉回。

所以这组表应这样读：

- **404 的绝对 Csca 确实更大**：按报告 88 的 reader 阶段量口径，404 / 660 写成 `7.10x`；当前 40-300 nm biomimetic EV 全粒径 panel 的 Csca 均值相除约为 `1.53x`，只作为聚合审查脚注，不放在主表 Csca 列里。
- **但 404 的归一化散射代理不一定更大**：在 800 nm 宽度族里，404 的散射强度代理约为 660 的 0.93x。
- **在当前 per-wavelength gold-normalized 口径里，404 的峰值优势主要来自参考场，而不是归一化散射代理本身**：例如 800 x 1100 下，404 的参考场是 660 的 1.29x，但平均峰值只到 1.10x。
- **峰值不是简单相乘**：平均峰值来自相干干涉项、相位、位置和探测算子，不能用“散射代理 x 参考场”直接推出。
- **检测率还被通过时间拉回**：404 的通过时间通常只有 660 的约 0.60-0.62 倍；tau=1 ms 下可积分的有效时间更短。
- 第 3 章后续表格同时保留 `Mie Csca` 和 `散射强度代理`，目的就是把“绝对散射截面”和“检测链条里的归一化散射代理”分开。
- **结论必须修改**：B6 可以作为 Tsuyama/gold-normalized 诊断和几何排序证据；当前 no-data closure 已由报告 140/147/148 接管，写成 404/W500 fixed-view 与 660/W800 per-wavelength-view 双 candidate family。

### 3.1 固定宽度 x 高度 = 800 x 1100 nm：当前默认中心"""
    )
    sections.append(fixed_geometry_table(stats, 800, 1100))
    sections.append("\n### 3.2 固定宽度 x 高度 = 800 x 1000 nm：宽粒径 EV 邻近候选")
    sections.append(fixed_geometry_table(stats, 800, 1000))
    sections.append("\n### 3.3 固定宽度 x 高度 = 800 x 1400 nm：尖锐小 EV 压力测试候选")
    sections.append(fixed_geometry_table(stats, 800, 1400))
    sections.append("\n### 3.4 固定宽度 x 高度 = 500 x 1100 nm：404 fixed-view 候选宽度的历史机制背景\n\n注意：这个尺寸下的 660 nm 基准本身是弱参考边界，所以本表只用于看波长机制，不能把 660 的高分当作可发布推荐。")
    sections.append(fixed_geometry_table(stats, 500, 1100))
    sections.append("\n### 3.5 固定宽度 x 高度 = 600 x 900 nm：488 对照高分几何\n\n注意：这个尺寸下的 660 nm 基准是弱参考边界；488 是参考光可用的对照高分路线。")
    sections.append(fixed_geometry_table(stats, 600, 900))
    sections.append("\n### 3.6 固定宽度 x 高度 = 600 x 1300 nm：短波 / 对照比较几何\n\n注意：这个尺寸下的 660 nm 基准也是弱参考边界；本表用于解释趋势，不用于最终选型。")
    sections.append(fixed_geometry_table(stats, 600, 1300))
    sections.append("\n### 3.7 固定宽度 x 高度 = 800 x 550 nm：类似 Tsuyama 论文锚点的几何")
    sections.append(fixed_geometry_table(stats, 800, 550))
    sections.append(
        """
固定尺寸后的主读法：

- 404 不应该在当前表里被简单解释成“短波散射一定更强”，因为表中的散射强度代理已经被每波长金颗粒基准重标了。在 800 nm 宽度族里，404 的归一化散射强度代理略低于 660，而 488 略高、532 明显低；但这不是 404 绝对 EV 散射较弱的证据。
- 660 的散射不一定最大，但它在当前 B 读法中同时拥有更长通过时间、较稳定的参考光工作区间和更稳健的选定环带检测率。
- 488/532 有助于看中波趋势，但不是最终推荐波长。
- 因为该历史口径会压平短波 EV 散射，404/660 不能在这里升级成绝对 winner；当前 closure 只保留 detector-surrogate candidate families。

---

## 4. 固定波长，看通道尺寸如何改变参考场和检测率

本节回答：“同一个波长下，改变通道宽高会让峰值增强多少、检测率提高多少？”

因为 `Mie Csca` 只由粒子和波长决定，不由通道宽高决定，所以本节固定波长扫描尺寸时，`Mie Csca` 一列会是 1.00x。这里真正随尺寸变化的是参考场、平均峰值、通过时间和检测率。

### 4.1 固定 660 nm、宽度 800 nm，扫描高度

倍数以 660 / 800 x 1100 为 1.00x。"""
    )
    sections.append(
        fixed_wavelength_depth_table(
            stats,
            660,
            800,
            [500, 550, 600, 650, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500],
            1100,
        )
    )
    sections.append("\n### 4.2 固定 660 nm、高度 1100 nm，扫描宽度")
    sections.append(fixed_wavelength_width_table(stats, 660, 1100, range(500, 1600, 100), 800))
    sections.append("\n窄宽度 500-700 nm 的检测率和峰值很高，但参考光状态是弱参考边界；真正可发布的宽度比较应从 800 nm 开始读。")
    sections.append("\n### 4.3 固定 660 nm、高度 1400 nm，扫描宽度")
    sections.append(fixed_wavelength_width_table(stats, 660, 1400, range(500, 1600, 100), 800))
    sections.append("\n这里同样如此：500-700 nm 解释了“窄通道能增强峰值”，但它们没有通过参考光可用性治理；推荐族仍从 800 nm 宽度开始。")
    sections.append("\n### 4.4 固定 404 nm、宽度 500 nm，扫描高度")
    sections.append(
        fixed_wavelength_depth_table(
            stats,
            404,
            500,
            [500, 550, 600, 650, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500],
            1100,
        )
    )
    sections.append("\n### 4.5 固定 488 nm、宽度 600 nm，扫描高度")
    sections.append(
        fixed_wavelength_depth_table(
            stats,
            488,
            600,
            [500, 550, 600, 650, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500],
            900,
        )
    )
    sections.append("\n### 4.6 固定 532 nm、宽度 600 nm，扫描高度")
    sections.append(
        fixed_wavelength_depth_table(
            stats,
            532,
            600,
            [500, 550, 600, 650, 700, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500],
            900,
        )
    )
    sections.append(
        """
固定波长后的主读法：

- 660 / 800 的高度曲线在 1000-1400 nm 一带很宽，不是单点尖峰，所以推荐写成高度带。
- 800 nm 宽度在关键 660 高度上通常是领先宽度；继续加宽会让参考场 / 峰值 / 检测率逐渐下降。
- 404 的 fixed-view 候选机制更偏向 500 nm 宽度；但在这个历史 B6 表内，它仍没有在四个 EV 粒径分布假设中超过 660。

---

## 5. 粒子尺寸为什么重要：同一路线下，小 EV 与大 EV 的差异

前面的表是 27 个 EV 粒径点的均值。下面直接按粒径拆开，回答“为什么有些粒子检测不到”。

### 5.1 当前默认中心：660 / 800 x 1100"""
    )
    sections.append(particle_size_table(raw, (660, 800, 1100), sizes))
    sections.append("\n### 5.2 404 fixed-view 候选背景：404 / 500 x 1100")
    sections.append(particle_size_table(raw, (404, 500, 1100), sizes))
    sections.append(
        """
粒径表的读法：

- 40-60 nm 小 EV 的散射场幅值和峰值显著低于大 EV，因此检测率明显低。
- 大 EV 的局部 SNR 很高，但检测率仍不会自动等于 100%，因为全穿越分母包含不利位置和不利相位事件。
- 选定环带检测率通常高于全穿越检测率，因为它只看 Tsuyama 语义下更有利的探测环带。

---

## 6. 噪声、阈值和弱参考：为什么“峰值高”还不能直接推荐？

口径 B 当前使用 5 sigma 阈值设置；但报告里的 SNR 是合成局部 SNR，不是实测空白噪声校准后的 SNR。它能说明趋势，不能替代实测噪声。

### 6.1 小 EV 与大 EV 的阈值余量对比

以 660 / 800 x 1100 为例，小 EV 的平均局部 SNR 已经超过 5 sigma，但选定环带检测率仍只有一部分事件通过；大 EV 则接近稳定通过。"""
    )
    sections.append(particle_size_table(raw, (660, 800, 1100), [40, 50, 60, 100, 150, 200, 250, 300]))
    sections.append(
        """
### 6.2 弱参考反例：660 / 500 x 550

这条路线的原始选定环带检测率很高，但被标记为弱参考边界。它说明：**高峰值 / 高选定环带分数不能自动成为推荐**，还必须通过参考光工作区间治理。"""
    )
    sections.append(route_chain_table(stats, [(660, 500, 550), (660, 800, 1100), (660, 800, 1000), (660, 800, 1400)], (660, 800, 1100)))
    sections.append(
        """
因此，噪声和参考场的关系应这样理解：

- 参考场增强会提高干涉峰值，但参考场本身也必须处在可解释、可发布的工作区间。
- 峰值增强主要改善事件过阈值的机会；检测率还受事件位置分布、选定环带分母、通过时间和相位影响。
- 当前 Stage B6 没有实测空白噪声、后焦面 / 感兴趣区域图像、记录器轨迹，所以只能给出合成相对设计结论。

---

## 7. 估计参数从哪里来？哪些真的参与了当前计算？

口径 B 有两类量，必须分清：

| 类别 | 当前值 / 来源 | 是否直接参与 Stage B6 运行 | 读者应该怎样理解 |
| --- | --- | --- | --- |
| 锁相时间常数 | `lockin_time_constant_s = 0.001` | 是 | 当前 B 固定为 tau=1 ms |
| 选定环带 | 归一化边缘位置 0.5-0.8 | 是 | 定义口径 B 主检测分母 |
| 参考相位 / 收集算子 | `tau_1ms_global_refphi_plus_collection_narrow` | 是 | 以 Tsuyama 语义冻结的 B 读法 |
| `gamma = 0.736502` | B4 目标拟合描述参数 | 否，当前运行器标记为仅元数据 | 参数来源链，不是物理常数 |
| `snr_scale = 0.890700` | B4 目标拟合描述参数 | 否，当前运行器标记为仅元数据 | 参数来源链，不是实测 SNR 校准 |
| `snr_response_exp = 0.810281` | B4 目标拟合描述参数 | 否，当前运行器标记为仅元数据 | 参数来源链，不是仪器响应定律 |
| `raw_global_snr_scale = 0.293130` | B4 目标拟合描述参数 | 否，当前运行器标记为仅元数据 | 参数来源链，不是实测噪声 |

这意味着：本报告的 Stage B6 排序主要来自真实跑完的 tau=1 ms 原始行，以及选定环带 / 参考光可用性治理；B4 的 `gamma / snr_scale / snr_response_exp` 解释参数来源，但不能被写成已实装的物理校准。

### 7.1 金颗粒锚点只做诊断
"""
    )
    sections.append(gold_table(gold))
    sections.append(
        """
金颗粒锚点几何可以说明 Tsuyama 参数来源链的一致性，但不能进入 EV 推荐。EV 推荐必须只来自 EV（exosome 标记）行。

---

## 8. Tsuyama 论文怎样约束本报告？

Tsuyama 论文不是“把结论直接搬过来”的校准证书。它们给口径 B 提供四类约束：

| 约束 | 对本报告的作用 | 不能外推成 |
| --- | --- | --- |
| 660 nm NODI 读出背景 | 支持 660 作为论文中心波长 | 660 在所有真实实验中必然最佳 |
| 选定探测环带 | 支持选定环带主指标 | 实测事件概率 |
| 1-2 ms 时间常数背景 | 支持当前 tau=1 ms 运行纪律 | 旧 2 ms 可改名成 1 ms |
| Au/Ag 锚点 | 支持 B1 参数来源链诊断 | 金颗粒行可混入 EV 推荐 |
| POD / thermal 论文 | 提供边界和对照 | POD LOD 可转移到 EV NODI |
| 每波长金颗粒锚定 | 支持论文 lineage 和锚点诊断 | EV 跨波长绝对推荐已经完成 |

当前最强、但仍然保守的说法是：

> 在 tau=1 ms、单随机种子、每工况 1000 个事件的合成 EV 全网格下，以 Tsuyama 金颗粒锚点归一化的口径 B 支持 660 nm / 800 nm 宽度族和 1000-1400 nm 高度带；404 nm 保留为 fixed-view 候选背景；488/532 nm 保留为对照。该结论不是实测校准，不是当前 no-data closure，也不是 404/660 绝对 EV 跨波长灵敏度的最终判决。

---

## 9. 发布边界

### 9.1 可以说

- Stage B6 tau=1 ms EV + 金颗粒全网格已完成 32,032 行。
- 当前 EV 推荐只使用 EV（exosome 标记）行。
- 该历史低事件数、gold-normalized 设计证据支持 660 / 800 x 1000-1400 家族。
- 在该 gold-normalized B6 表内，404 是 fixed-view 候选背景，但没有超过 660。
- 404 的绝对 Mie 散射优势没有被 B6 否定；当前 closure 将其保留为 `404/W500` candidate family。
- 488/532 是趋势 / 对照，不是最终推荐。
- 金颗粒只做 Tsuyama 锚点诊断。

### 9.2 不能说

- 不能说这是每工况 10000 个事件的最终验证。
- 不能说这是实测校准。
- 不能说 `660 / 800 x 1100` 是物理绝对最佳。
- 不能说当前 B6 已经证明 660 在绝对 EV 跨波长灵敏度上最终胜过 404。
- 不能说 404 因为短波散射强就必然替代 660。
- 不能把 488/532 写成最终推荐波长。
- 不能把金颗粒行混入 EV 行选胜出项。
- 不能把 B1 锚点几何直接写成 B2 EV 推荐。
- 不能把旧 2 ms 全网格改名成当前 1 ms 证据。
- 不能把每波长金颗粒归一化后的散射代理当作 EV 绝对散射强度。

---

## 10. 当前 closure 之后还需要什么？

| 目标 | 下一步 | 解决的问题 |
| --- | --- | --- |
| 当前 no-data 结论入口 | 使用 `reports/140_*`、`reports/147_*`、`reports/148_*`，不要用本 B6 生成器覆盖最终说法 | 把历史 B6 方法诊断和当前 3-seed 10000e closure 分开 |
| 模拟可补项 | R1 读出轴、C/D×V2 gauge cell 可补算，但已移交 narrowed gate 外 | 检查不确定度轴，而不是立刻改变 headline |
| 实测噪声 | 加入实测空白噪声 / 参考光记录 | 把阈值和噪声从替代量提升到实测量 |
| 实测参考场 | 加入后焦面 / 狭缝 / 感兴趣区域扫描 | 检查选定环带和参考光可用性是否真实成立 |
| 锚点校准 | 在 B1 几何测 Au 原始轨迹 | 检查金颗粒尺寸响应和参数来源链 |
| EV 实验 | 测 EV 粒径面板 | 只有验收通过后，才能把结论声明从合成改成实测 |

### 10.1 历史 B7 思路如何阅读

历史上，B7 的目的不是把 B6 多跑几倍事件数，而是把每波长金颗粒归一化和固定基准视图分开。当前读者不应把下面内容当作未完成的封板阻塞项；它是解释为什么后续 140/147/148 改用双 view/candidate-family closure 的方法背景。

1. **先做固定 660 基准重算**：对每个通道尺寸，仍用同一个基准金颗粒和同一个基准通道，但把所有波长的 `E_sca_ref` 固定为该通道在 660 nm 下的金颗粒值；实现上可使用 `normalization_mode = "global_single_lambda"`，并在每条 route 调用 `run_parameter_sweep` 前传入该通道的 660 nm `E_sca_ref`。
2. **同时保留当前 B6 作为对照**：B6 名称应写成“per-wavelength gold-normalized Tsuyama diagnostic lane”，不能覆盖 B7。
3. **B7 输出必须同时列三类表**：绝对 `Mie Csca`、固定 660 基准散射场 / cross-term、最终检测率。只有三者方向一致时，404/660 的最终判断才有说服力。
4. **如果 B7 仍支持 660**：报告可以说“404 的绝对散射优势经过固定基准检验后仍被通过时间、相位 / 轨迹和参考场治理抵消”。
5. **如果 B7 支持 404 或二者接近**：最终推荐应改成 404/660 双候选，并用实测噪声 / 参考场校准决定发布路线。

---

## 11. 最小复核命令

```bash
python -m py_compile tools/build_lens_b_reader_report.py tools/lens_b_ev_gold_fullgrid_runner.py tools/analyze_lens_b_ev_gold_fullgrid.py
python tools/build_lens_b_reader_report.py
python tools/analyze_lens_b_ev_gold_fullgrid.py \\
  --input-csv results/stage_b6_tau1ms_ev_gold_fullgrid_1000e_seed42_22worker_restart_20260514/seed_42_raw_rows.csv \\
  --output-dir /tmp/lens_b_check_derived \\
  --check-only
python tools/analyze_lens_b_ev_gold_fullgrid.py --check-only
git diff --check -- reports/100_EV_NODI_lens_b_tau1ms_stage_b6_only_analysis.md
```
"""
    )
    return "\n\n".join(sections).rstrip() + "\n"


def main() -> None:
    REPORT_PATH.write_text(build_report(), encoding="utf-8")
    print(REPORT_PATH)


if __name__ == "__main__":
    main()
