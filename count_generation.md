# `count_generation.py`

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
