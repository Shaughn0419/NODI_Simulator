# `tests/test_physics_core.py`

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

## 文件定位
- 类型：测试模块
- 模块摘要：Focused pytest suite for core physics and signal-chain invariants.
- 当前职责：物理核心测试，覆盖基础散射、信号链与核心数值稳定性。

## 主要符号
- 顶层函数：`_synthetic_design_result`
- 顶层类：`TestDataObjects`、`TestMie`、`TestIntrinsicScattering`、`TestUtils`、`TestReferenceField`、`TestPaperAlignedProfiles`、`TestTsuyamaPhaseFilter`、`TestIllumination`、`TestTrajectory`、`TestScatteringTrace`、`TestInterferometricTrace`、`TestPulseAnalysis`、`TestReadoutSurrogate`、`TestPopulationTraceSimulator`、`TestRunStateModel`、`TestBatchSummaryAndEngineeringScore`、`TestDesignMetricsAndPostprocess`、`TestSeedRobustness`、`TestIntegration`

## 调用与使用
- 典型使用方式：通常由 `pytest` 或 `tests/run_tests.py` 调用，不是面向最终用户的直接入口。
- 直接维护建议：当页面结构、数据口径或核心物理逻辑变化时，应同步更新这里的断言与测试夹具。

## 关联代码
- `data_objects.py`
- `illumination.py`
- `interferometric_trace.py`
- `intrinsic_scattering.py`
- `mie_engine.py`
- `parameter_sweep.py`
- `pulse_analysis.py`
- `reference_field.py`
- `scattering_trace.py`
- `trajectory.py`
- `utils.py`

## 专题补充
- [`guides/operations/14_测试说明.md`](../guides/operations/14_测试说明.md)

## 备注
- 当前核心回归覆盖 manifest kind guard：错 lane manifest 会被标为 `manifest_kind_mismatch`，不能让 BFP ROI mask 暴露 `calibrated_mask` 或通过 gate。
- 当前核心回归还覆盖 `run_parameter_sweep` 的 `theta_grid_rad` 前置校验、case failure partial policy、`event_block_v3` 与 scalar summary 对照、`block_lane_order` 的显式 RNG policy、2D light illumination kernel 与 full diagnostics 的信号字段一致性，以及 plug-diffusive trajectory block 的 scalar RNG 顺序一致性。
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
