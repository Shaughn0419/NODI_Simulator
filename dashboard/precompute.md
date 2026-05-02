# `dashboard/precompute.py`

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

## 文件定位
- 类型：Dashboard 支撑模块
- 模块摘要：dashboard/precompute.py — 预计算 sweep 并保存结果
- 当前职责：预计算任务入口，负责构造 sweep、保存结果、维护 checkpoint 与产物元数据。

## 主要符号
- 顶层函数：`_remember_summary_dataframe`、`_build_saved_path_log_message`、`_build_saved_dataframe_log_message`、`_execute_precompute_save_step`、`_build_parameter_sweep_kwargs`、`_build_precompute_save_steps`、`build_precompute_sim_cfg`、`_format_duration_readable`、`_write_json_atomic`、`_write_pickle_atomic`、`_write_dataframe_atomic`、`_eta_iso_from_remaining` 等
- 顶层类：`PrecomputeSaveStep`、`PrecomputeArtifactPaths`、`PrecomputeMetadata`、`PrecomputeCheckpointManifest`、`PrecomputeProgressSnapshot`、`PrecomputeJobState`、`PrecomputeSaveContext`、`PrecomputeRunContext`、`FreezeProbeReportPayload`、`ResultHealthReportPayload`、`SweepRuntimeProgress`

## 调用与使用
- 典型使用方式：通常作为脚本从仓库根目录运行；建议先阅读文件内参数或 `main()` 入口。
- 直接维护建议：这里适合放共享配置、结果加载和计算桥接逻辑；尽量避免把页面展示文案和大段 UI 拼装塞进来。
- 当前执行交接建议：如果你不是在改实现，而是在接手“下一步要跑什么”，先读 [`24_高性能预计算与增量重算方案.md`](../24_高性能预计算与增量重算方案.md)。

补充：
- CLI 的 `--workers` 当前默认值为 `8`，用于测试 / probe / 其他常规预计算。
- 正式全量重算仍应显式传 `--workers 28`，不要依赖默认值。
- `meta.json` 当前是 `dashboard_schema_version = 1.24`
- CLI 支持 `--artifact-profile {full,standard,minimal}`。默认 `standard`，只保存 dashboard 必需的 `summary / compact / meta / result_health`、可选 `freeze_probe` 和设计复盘用 `design_postprocess.csv`，跳过重复 `case_summary` 与 heavy parquet split exports；需要历史兼容拆分导出时显式传 `--artifact-profile full`。
- `--tag` / profile default tag 会先经过安全文件名校验，只允许字母、数字、`.`、`_`、`-`，避免输出前缀逃逸 `output_dir`。
- 默认不允许 partial result：case 失败会让 precompute 失败，而不是保存一个看起来完成的偏置库。只有显式 `--allow-partial` 才会记录 partial policy 并保存成功子集。
- checkpoint 默认批量 flush 为 `--checkpoint-batch-size 100`，用于降低全量重算 checkpoint I/O；中断后仍可用同一命令 `--resume --checkpoint` 补跑缺失 case。
- `build_precompute_sim_cfg(...)` 会先调用 `make_ev_nodi_design_sweep_config(...)`，把正式预计算主线固定到 EV/NODI relative design 语义：`readout_preset="EV_NODI_only_design"`、`readout_observable_mode="magnitude"`、`nodi_readout_semantics="bandpass_envelope_surrogate"`、`readout_internal_demod_route="analytic_lockin_surrogate"`、`initial_position_distribution_mode="flux_weighted"`，并把 particle-induced channel perturbation 保持为 diagnostic-only。
- metadata 会完整记录 `SimulationConfig`，并新增 `analysis_lanes` / `schema_feature_inventory.route_contract` 中的 all-crossing 与 selected-annulus traceability；selected-annulus 会记录 `edge_norm_min/max`、source、claim level 与 paper alignment target，避免下游只从 CSV 文件名推断口径。claim/target 值统一引用 `design_claim_governance.py` registry，当前 selected-annulus target 为 `tsuyama_2022_nodi_table_s1`；paper-fit 工具会进一步校验 target metadata 与 claim compatibility，因此 stale/mismatched readout 或 annulus 口径不能被静默拼成同一 selected-annulus paper claim。
- metadata 会记录 `model_semantics_version`、`result_library_role`、`schema_feature_inventory` 与
  `legacy_current_code_library_compatible=False`，避免旧 current-code 结果库被误当成现行结果库。
- metadata 会记录 `reference_calibration_health`，汇总 blank-reference 标定是否启用、`A_ref` 是否覆盖、是否退回 `g_ref * rho`、是否外推以及 phase source 覆盖。
- metadata 也会记录 `collection_operator_calibration_health`，汇总 collection operator 表是否启用、几何覆盖、外推、absolute throughput 覆盖与 operator normalization。
- `schema_feature_inventory.reference_detector_and_calibration` 会列出 BFP ROI mask source/status/data role/gate，便于区分 current radian surrogate、synthetic fixture contract 和 measured calibrated mask。`results_to_diagnostics_long_dataframe()` 与 schema inventory 使用完整 `DESIGN_CLAIM_GOVERNANCE_FIELDS`，因此 `detector_operator_caution_reason`、`detector_resolved_relative_design_eligible`、`relative_design_with_detector_caution` 等分层字段不会从 dashboard long-form/inventory 表面消失。
- `SimulationConfig` 还会保留 standard-particle calibration table 与 blank false-positive calibration table 的配置入口；case physics 会导出 `K_sca` / phase-offset 覆盖状态和 empirical blank false-positive summary 状态，但缺 Mie-to-power / detector-unit 链时仍不会解锁 calibrated quantitative。
- illumination provenance 现在按波长分别写入 `optical.illumination_effective_beam_waists_by_wavelength_nm`
- compact 与 summary dataframe 会带出 material model/source/uncertainty、Mie-to-power chain、detector field units、calibration design/held-out validation、superposition validity、`K_sca_uncertainty_status` 和 standard-particle uncertainty budget 状态，用来防止无材料 uncertainty、无完整单位链、无 held-out calibration design、无 joint fullwave / weak-superposition 验证，或无标准粒子尺寸/材料/批次/浓度预算的结果被误读成已传播 quantitative uncertainty。
- compact、summary dataframe 与 diagnostics-long 现在都会带出 all-crossing / selected detector-mode 条件诊断字段：`all_crossing_detection_rate`、`selected_detector_mode_candidate_*`、`selected_detector_mode_annulus_*`。annulus 边界来自 `SimulationConfig.selected_annulus_edge_norm_min/max`，默认 `0.5-0.8`；空 annulus 分母输出 `NaN` conditional rate，而不是伪造 0% 检出率。`results/selected_annulus_fullchain_dryrun_20260501_v2/` 已用 `coarse + quick`、`8 workers` 跑通 precompute save -> EV route analysis -> selected-annulus ranking comparison，确认全量 summary 不会再丢失 selected-annulus 源列；2026-05-02 另有 `results/tsuyama_annulus_ratio_sensitivity_smoke_20260502/` 验证 annulus sensitivity 多 seed 输出链路，并在 decision 中记录 lower-is-better joint-fit score、scenario 和当前 Au `20/30/40/60 nm` / Ag `40/60 nm` 口径，但不作为 canonical 比例签发。
- phase-filter validity 细项（`H/lambda0`、subwavelength groove、depth reason、multiple-reflection warning）会随 reference diagnostics 进入 compact 与 dataframe。
- interface correction provenance 会带出 phase/polarity/angular-pattern output sensitivity、full-wave escalation reason 与 quantitative blocker summary；默认 homogeneous-medium Mie 可继续排序，但不能被误读成界面定量 phase/polarity 主线。
- thermal-POD provenance 会带出 probe reference field、excitation absorption / heat source、solvent `dn/dT`、detector responsivity、spectral filter、thermal validation 与 quantitative route blockers，避免把 frequency-lane surrogate 当成绝对 POD amplitude。
- noise terms 会以扁平列输出 photon-shot、electronics、RIN、speckle-like、drift 和 lock-in-output 状态，避免只保留不可直接筛选的 nested dict。
- count-generation provenance 会随 compact 与 dataframe 输出：per-event detectability boundary、Poisson arrival status、volumetric-flow source、crossing-conditioned transport status、blank false-positive / missed-event / dead-time / occupancy correction status，以及 count-rate confidence / uncertainty status。
- result health 与 freeze probe 报告也会聚合 detector / coordinate / calibration / background / readout / threshold / interface / material / thermal-POD / count-generation status，防止全量重算前只看 freeze/gate 指标而漏掉仍为 surrogate、未标定或 confidence unavailable 的结果库。
- Manifest kind mismatch 会保留为显式 validation status；错 lane 的 manifest 不会把任何 calibration fixture 升级为 measured lane。
- precompute worker 路径会调用 `run_parameter_sweep(..., stream_summary_only=True)`，并启用 worker-local invariant caches。缓存只影响运行时间和进程内对象复用，不写入结果语义，也不改变输出字段或随机数顺序。
- `build_precompute_sim_cfg(...)` 会固定正式主线事件引擎为 `vectorized_event_engine="off"`、`event_block_size=32`、`event_block_rng_order="event_loop_order"`。CLI 仍支持显式覆盖到 `event_block_v3` 做性能实验/回归对照，但正式全量重算不建议切到 `event_block_v3` 或 `block_lane_order`，因为当前 16C/32T 基准显示 scalar/off 更快，且 `block_lane_order` 会产生统计和 gate 漂移。

## 关联代码
- `dashboard/config.py`
- `parameter_sweep.py`

## 设计原则
1. 标准主库直接重算，不再走旧的合并过渡链路。
2. 长耗时预计算必须可观测，progress / checkpoint 是实现要求，不是附加优化。
3. 结果口径以当前 EV design + biomimetic anchor 主库为准。

## 专题补充
- [`24_高性能预计算与增量重算方案.md`](../24_高性能预计算与增量重算方案.md)

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
