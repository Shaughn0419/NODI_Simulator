# `dashboard/signal_backend.py`

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

## 文件定位
- 类型：Dashboard 支撑模块
- 模块摘要：dashboard/signal_backend.py — Signal-chain helpers for explanatory dashboard pages
- 当前职责：为干涉、噪声和单案例页面提供信号链计算、扫描结果与解释性统计。

## 主要符号
- 顶层函数：`_resolve_projection_basis`、`_wrapped_phase_delta_rad`、`_rank_correlation`、`_classify_reference_consistency`、`_classify_interference_overlap`、`_classify_path_opd_and_gouy_freeze`、`_summarize_reference_consistency_subset`、`_projection_mode_semantics`、`_dominant_clean_peak_summary`、`_resolve_esca_reference`、`build_case_inputs`、`compute_interference_case`、`build_interference_scan_dataframe`、`build_projection_mode_validation_dataframe`、`build_reference_model_consistency_report`、`build_path_opd_freeze_report`、`compute_noise_detection_case`、`build_event_trace_dataframe`、`build_rho_sensitivity_report`、`build_single_case_stage_report`、`build_detection_scan_dataframe` 等
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：这里适合放共享配置、结果加载和计算桥接逻辑；尽量避免把页面展示文案和大段 UI 拼装塞进来。

## 关联代码
- `dashboard/config.py`

## 专题补充
- 当前没有专门的编号专题说明；本文件的同名说明文档就是第一份对应说明。

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
