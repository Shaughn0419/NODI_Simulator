# `tests/test_dashboard_workflow.py`

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

## 文件定位
- 类型：测试模块
- 模块摘要：Focused pytest suite for dashboard workflow, live tuning, and cross-page behavior.
- 当前职责：Dashboard 工作流测试，覆盖导航、跨页状态、主线展示和交互行为。

## 主要符号
- 顶层函数：`test_result_health_report_exposes_count_generation_monitoring`、`test_freeze_probe_report_exposes_count_generation_monitoring`、`test_particle_medium_routing_uses_water_for_gold_and_pbs_for_exosome`、`test_single_case_stage_report_exposes_rho_probe_summary`、`test_rho_sensitivity_report_exports_envelope_probe_rows_top_level`、`test_design_explorer_defaults_to_exosome_when_available`、`test_particle_from_name_rebuilds_biomimetic_exosome_particle`、`test_biomimetic_precompute_profiles_are_available`、`test_build_metadata_records_particle_models_for_biomimetic_profile`、`test_build_metadata_summarizes_reference_calibration_health`、`test_build_metadata_summarizes_collection_operator_calibration_health`、`test_precompute_sweep_default_standard_artifact_profile_skips_heavy_exports` 等
- 顶层类：`_SessionStateGuard`、`TestDashboardWorkflow`、`TestDashboardAppInteractions`

## 调用与使用
- 典型使用方式：通常由 `pytest` 或 `tests/run_tests.py` 调用，不是面向最终用户的直接入口。
- 直接维护建议：当页面结构、数据口径或核心物理逻辑变化时，应同步更新这里的断言与测试夹具。

## 关联代码
- `dashboard/backend.py`
- `dashboard/config.py`
- `dashboard/estimate_precompute_runtime.py`
- `dashboard/mie_backend.py`
- `dashboard/panels/common.py`
- `dashboard/panels/explorer.py`
- `dashboard/panels/interference_explorer.py`
- `dashboard/panels/mie_explorer.py`
- `dashboard/panels/noise_detection_explorer.py`
- `dashboard/panels/single_case_calculator.py`
- `dashboard/precompute.py`
- `dashboard/signal_backend.py`

## 专题补充
- [`guides/operations/14_测试说明.md`](../guides/operations/14_测试说明.md)

## 备注
- 当前这组 workflow 回归还显式覆盖三类最近新增风险：`meta.json` 的 `schema 1.24 + full sim_cfg + wavelength-specific illumination provenance + reference_calibration_health + collection_operator_calibration_health + schema_feature_inventory` 是否持续导出，standard precompute artifact profile 是否保留 dashboard 必需产物并跳过 heavy split exports，dashboard physics breakdown 是否继续暴露 material model / phase-filter validity / Mie-to-power chain / detector field units / collection operator calibration / standard-particle calibration / blank false-positive calibration / detector-unit chain / raw blank / BFP ROI source/status/role/gate / calibration design + held-out validation / superposition validity / per-term noise status / thermal-POD blockers / count-generation provenance / `K_sca_uncertainty_status` / standard-particle uncertainty budget，health / freeze probe 是否聚合 governed provenance status，以及 `Single-Case Calculator` 是否持续继承 dashboard 主默认配置。
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
