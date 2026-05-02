# 35 方法学补充摘要

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：本文仍是方法学说明；代码主线已包含 EV/NODI relative design gate、detector caution、analytic lock-in surrogate、严格 event QC、EV biomimetic ensemble/anchors、calibrated BFP ROI 1D projected lane、dashboard diagnostics/schema inventory、selected-annulus parallel analysis lens、Tsuyama selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants，以及 linked 488-window/532-max classification feature lane。Selected-annulus paper-fit EV targeted panel 与 3-seed pre-fullgrid robustness audit 已通过；旧 CSV 缺 selected-annulus 源列时会标记 unavailable/null/NaN。`joint_fit_score` 已明确为 lower-is-better loss-style penalty，paper target metadata 与 claim compatibility 已进入代码测试。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings。
<!-- DOCSYNC:END -->

> 当前状态：方法学说明。旧 full-range 数值报告已降级为历史快照；本文只保留重写报告时仍应使用的方法。

## 保留的方法学原则

1. 选型不能只看最高 `final_engineering_score`。
2. 主路线要同时看 coverage、stable detection、phase flip、health/freeze 和 recommendation label。
3. EV/sEV 与 gold 分开解释；gold 用于系统验证，不直接决定 EV/sEV 主设计。
4. `engineering_ranking`、`paper_aligned_comparison`、`reference_calibrated_relative` 和更高 calibrated claim 必须分开。
5. 没有实测 calibration 和 uncertainty propagation 时，不输出 quantitative confidence / CI。

## 新库完成后应重新计算

- route-level best cases
- EV/sEV size-weighted summary
- wavelength-level coverage
- channel-family summary
- gate pass fraction
- recommendation distribution
- claim-level / calibration-level distribution
- synthetic fixture case fraction

## 数据源

当前旧主数据已删除。新报告必须等待：

- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_meta.json`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_result_health.json`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_runtime_performance.json`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_freeze_probe.json`
