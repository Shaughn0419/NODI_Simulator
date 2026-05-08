# 35 方法学补充摘要

> 当前状态：方法学说明。旧 full-range 数值报告已降级为历史快照；当前 reader-facing 综合报告是 `reports/88_*`。本文只保留重写报告或审查评分口径时仍应使用的方法。

## 保留的方法学原则

1. 选型不能只看最高 `final_engineering_score`。
2. 主路线要同时看 coverage、stable detection、phase flip、health/freeze 和 recommendation label。
3. EV/sEV 与 gold 分开解释；gold 用于系统验证，不直接决定 EV/sEV 主设计。
4. `engineering_ranking`、`paper_aligned_comparison`、`reference_calibrated_relative` 和更高 calibrated claim 必须分开。
5. 没有实测 calibration 和 uncertainty propagation 时，不输出 quantitative confidence / CI。

## 生成新综合报告时应检查

- route-level best cases
- EV/sEV size-weighted summary
- wavelength-level coverage
- channel-family summary
- gate pass fraction
- recommendation distribution
- claim-level / calibration-level distribution
- synthetic fixture case fraction

## 数据源

当前正式基础库和 v2 收口报告已经生成。重写报告时至少核对：

- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_meta.json`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_result_health.json`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_runtime_performance.json`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_freeze_probe.json`
