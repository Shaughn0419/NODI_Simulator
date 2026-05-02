# `parameter_sweep.py`

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

## 文件定位
- 类型：核心仿真模块
- 模块摘要：NODI Interferometric Simulator — Parameter Sweep Module
- 当前职责：组织批量事件仿真、读出链、统计汇总与 sweep 级别评分，是结果库生成的主计算模块。

## 主要符号
- 顶层函数：`add_detector_noise`、`add_post_readout_noise`、`_first_order_lowpass_alpha`、`_pod_frequency_response_gain`、`_nodi_transit_response_diagnostics`、`apply_readout_chain`、`_build_observation_signature`、`_estimate_transit_time_s`、`simulate_one_event`、`run_single_case_batch`、`summarize_batch`、`wilson_lower_bound`、`wilson_upper_bound`、`compute_empirical_roc_auc`、`compute_hit_rate_at_fixed_false_alarm`、`compute_d_prime`、`build_sweep_case_key`、`compute_case_score`、`compute_engineering_score`、`compute_final_engineering_score`、`compute_final_engineering_rank`、`compute_joint_score`、`compute_robust_scores` 等
- 顶层类：`SweepCaseResult`、`SweepRawResult`

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：这里承载核心物理或仿真逻辑，修改时应优先保证数值口径稳定，并补充对应测试。

## 关联代码
- `data_objects.py`、`intrinsic_scattering.py`、`reference_field.py`
- `illumination.py`、`trajectory.py`、`scattering_trace.py`
- `interferometric_trace.py`、`pulse_analysis.py`、`utils.py`

## 专题补充
- [`guides/core/11_parameter_sweep.md`](guides/core/11_parameter_sweep.md)

## 备注
- 当前 summary / intrinsic / reference 会同步带出文件43 v5 的 P0/P1 diagnostic/scaffold 字段，包括 EV reporting、assay controls、selection/event QC、wavelength/objective/exposure blockers、particle-channel double-count guard、BFP detector operator、population/full-trace scaffold、fluidic diagnostics、calibration advisor 和 experimental-design advisor。
- sweep / precompute worker 路径现在启用 worker-local cache：同一进程内复用 `intrinsic scattering`、`reference field base` 和 `collection operator`。cache key 包含粒子、介质、波长、通道、光学配置、theta grid 与当前 `SimulationConfig` identity；缓存只为性能服务，不跨进程共享，也不会写入结果语义。
- `run_single_case_batch(..., stream_summary_only=True, retain_event_traces=False)` 会直接把 event 级 summary 所需量喂给 `_BatchSummaryAccumulator`，不保留 slim event 列表。summary-only 路径还会跳过未消费的 NODI post-readout 诊断数组，但会显式推进对应 RNG，使后续 POD 噪声和最终 summary 与旧路径保持一致。
- precompute 主线默认使用 `vectorized_event_engine="off"`、`event_block_size=32`、`event_block_rng_order="event_loop_order"`。这条路径逐 event 推进，是当前正式全量重算的保守高吞吐口径；`event_block_v3` 在 summary-only 场景下可批量推进事件并复用 2D illumination / readout / peak-summary 快路径，但当前只作为显式性能实验/回归对照。
- `event_block_rng_order="block_lane_order"` 是显式实验选项：它用按 lane 分离的随机流换取少量速度收益，会改变个体 event 数值轨迹，当前不作为正式默认。
- `run_parameter_sweep(...)` 现在会在开始执行 case 前验证 `theta_grid_rad`；缺失或非 1D 空网格会立即抛错。
- sweep case 失败不会再被静默保存成“完成的部分结果”。默认 `allow_partial=False` 会在任意 case 失败后抛出 `SweepCaseFailureError`；只有调用方显式传 `allow_partial=True` 时，才允许返回成功子集，并由 precompute metadata 记录 partial policy。
- `run_single_case_batch` 会为每个 case 构建一次 trajectory/readout/pulse context，并传入每个 event；其中 `TrajectoryContext` 来自 `trajectory.py`，负责复用时间网格、可达半跨和 `rect_series` 系数。
- `_BatchSummaryAccumulator` 现在同时输出 raw all-crossing 和 selected detector-mode 条件诊断：`detection_rate` / `all_crossing_detection_rate` 保持全穿越事件分母；`selected_detector_mode_candidate_*` 使用 width gate 前 `event_max_margin_z >= 0` 的事件分母；`selected_detector_mode_annulus_*` 使用初始位置 `edge_norm = max(abs(x_norm), abs(z_norm))` 落在 `SimulationConfig.selected_annulus_edge_norm_min/max` 的事件分母，默认仍为 `0.5-0.8`。这些字段不参与 `compute_case_score` 或工程 ranking，只供 Tsuyama selected detector-mode 语义解释和报告诊断；当 annulus 分母为空时，conditional rate / Wilson LB / mean edge norm 输出 `NaN`，并在 gold-lane flatten / 下游 route analysis 中继续保留 unavailable/NaN 语义；`dashboard.precompute` 已把它们贯通到 summary / compact / diagnostics-long，`results/selected_annulus_fullchain_dryrun_20260501_v2/` 的小型全链路试算已确认下游 route analysis 能直接消费这些列；旧 CSV 缺源列时仍必须显式标记 unavailable/null/NaN。
- BFP ROI mask 字段会从 collection operator 贯通到 summary、intrinsic、reference、precompute 和 dashboard：`bfp_roi_mask_source/status/data_role/gate_passed` 只说明 ROI mask contract 状态，不会单独解锁 detector-unit quantitative claim。
- 当前 `observation_signature` 不只冻结 reference / phase / readout，也会把 material model/uncertainty status、Mie-to-power chain status、detector field units、calibration design rank、held-out validation status、superposition validity / channel-particle coupling model、interface output sensitivity / full-wave escalation、POD quantitative route / wavelength grouping / heat-source blockers、count-generation boundary / Poisson arrival / crossing-conditioned transport status、`K_sca_uncertainty_status`、standard-particle uncertainty budget、`coupling_model`、`illumination_mode`、`flow_profile_model`、`include_diffusion`、`diffusion_hindrance_model`、`reflecting_boundary` 这些材料、单位链、calibration、界面、POD、弱叠加、计数、输运与照明 provenance 一并串入审计签名。
- phase-filter reference path 的 validity / subwavelength groove status 也进入 `observation_signature`，避免 paper-aligned comparison 与普通 legacy route 被混用。
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
