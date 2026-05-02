# `count_generation.py`

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

## 文件定位
- 类型：核心物理辅助模块
- 模块摘要：把 per-event detectability 与实验 concentration-to-count 预测分开。
- 当前职责：输出 Poisson flux、accessible area、体积流量、dead time、multi-occupancy 与 wall-interaction provenance。

## 主要符号
- 顶层函数：`build_count_model_diagnostics`

## 调用与使用
- 由 `parameter_sweep.run_single_case_batch()` 在 batch summary 形成后调用。
- 默认 `count_prediction_model="not_applied"`，只暴露 per-event detection 口径和几何/壁面 provenance。
- 当配置 `poisson_flux_deadtime_surrogate + number_concentration_m3` 时，才输出 `predicted_count_rate_Hz` / `predicted_counts_in_window`。
- 结果字段会显式标出 `count_generation_model`、`per_event_detectability_boundary`、Poisson arrival status、volumetric-flow source、crossing-conditioned transport status、blank false-positive / missed-event / dead-time / occupancy correction status，以及 count-rate confidence / uncertainty status。

## 设计原则
1. `conditional_detection_rate` 保持“给定一个事件发生后是否检出”的定义。
2. dead time、multi-occupancy、blank false positive 等实验计数因素只进入 count-model 字段，不回写 per-event detection rate。
3. 未建模的 wall interaction / adsorption / clogging 必须显式标记，而不是从结果中消失。
4. crossing-conditioned transport 还未实现时必须输出 `not_implemented_*` 状态，避免把现有 per-event 初始分布误读成已按实验通量条件化的事件生成。
