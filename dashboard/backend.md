# `dashboard/backend.py`

## 文件定位
- 类型：Dashboard 支撑模块
- 模块摘要：模块 docstring 存在编码噪声，以下说明按当前代码职责重新整理。
- 当前职责：Dashboard 数据桥接层，负责结果文件加载、结果源切换、DataFrame 补全与页面查询。

## 主要符号
- 顶层函数：`check_data_files`、`list_available_datasets`、`is_standard_dashboard_dataset_prefix`、`resolve_preferred_dataset_prefix`、`sync_dashboard_data_prefix`、`load_sweep_summary`、`load_sweep_compact`、`load_metadata`、`load_result_health`、`load_dashboard_data_bundle`、`load_workflow_case_anchor`、`build_dashboard_data_source`、`build_heatmap_matrix`、`build_slice_data`、`recompute_scores`、`get_case_summary`、`build_physics_breakdown`、`build_sim_cfg_from_ui`、`build_optical_from_ui`、`build_live_tag`、`run_live_sweep`、`build_local_fine_grid` 等
- 顶层类：`DashboardDataSource`、`DashboardLoadedData`

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：这里适合放共享配置、结果加载和计算桥接逻辑；尽量避免把页面展示文案和大段 UI 拼装塞进来。

补充：
- 当前结果库 schema 版本为 `1.24`
- 当前标准结果库前缀为 `ev_design_full_range_biomimetic_exosome_with_anchors_10000e`；旧前缀只作为兼容/历史读取对象，不应被当作 current truth。
- 当前正式结果库按 precompute 默认的 `standard` artifact profile 导出，backend 读取合同以 `summary / compact / meta / result_health / freeze_probe / design_postprocess` 为准；`case_summary` 与 heavy parquet split exports 仅属于 `full` 兼容 profile。
- backend 读取 metadata 时，会把完整 `sim_cfg` 与分波长 illumination provenance 一并视为现行结果库口径
- metadata 的 `schema_feature_inventory` 会列出当前 schema 承诺导出的 reference/detector/calibration、coordinate/vector/superposition、detector-noise/units、readout、threshold、material、interface、thermal-POD、count-generation 和 Mie incident-field provenance 字段组。
- metadata 的 `reference_calibration_health` 会汇总 blank-reference 标定启用、覆盖、外推、`A_ref` / `g_ref` 依赖和 phase source 状态。
- metadata 的 `collection_operator_calibration_health` 会汇总 collection operator 表启用、几何覆盖、外推、absolute throughput 覆盖和 operator normalization。
- physics breakdown 会显示 standard-particle `K_sca` / global phase offset 覆盖、blank false-positive calibration summary、operator normalization、BFP ROI mask source/role/gate 和 absolute throughput 状态；这些字段只是 route/provenance，缺 detector-unit power chain 时不会把结果提升为定量。
- schema 不匹配的旧 current-code 结果库会被拒绝；新导出的 meta 还会带库级模型语义标记。
- case physics breakdown 会展示 material model/source/uncertainty、Mie-to-power chain、detector field units、calibration design/held-out validation、superposition validity、`K_sca_uncertainty_status` 与 standard-particle uncertainty budget；未完成 `dCsca/dΩ -> dP_sca/dΩ -> detector field/voltage`、缺少可识别 calibration design，未做 joint fullwave / weak-superposition 验证，或缺失标准粒子尺寸分布、shape、ligand/shell、batch、浓度、材料数据集 uncertainty 时保持未传播状态。
- phase-filter validity 细项会显示在 case physics breakdown 中，深通道外推或 full-wave 需求不能只停留在底层 reference 字典。
- interface correction breakdown 会显示 output sensitivity、dipole-surrogate validity 与 quantitative blockers；phase / polarity / angular-pattern 输出触发的 full-wave 需求不会只藏在底层 intrinsic 字典里。
- thermal-POD breakdown 会显示 quantitative route status、probe reference field、heat-source、`dn/dT`、detector responsivity、spectral filter 与 validation blockers；POD unavailable / surrogate 状态不会只表现为 amplitude=False。
- detector-noise breakdown 会逐项显示 photon-shot、electronics、RIN、speckle-like、drift 与 lock-in-output noise term status。
- count-generation breakdown 会显示 per-event detectability boundary、Poisson arrival status、volumetric-flow source、crossing-conditioned transport status、blank false-positive / missed-event / dead-time / occupancy correction status，以及 count-rate confidence / uncertainty status。
- 错 lane manifest 会显示为 `manifest_kind_mismatch` 或相应 not-applied status，dashboard 不应把它解释成 measured calibration。

## 关联代码
- `dashboard/config.py`
- `dashboard/precompute.py`
- `nodi_simulator/data_objects.py`
- `nodi_simulator/parameter_sweep.py`
- `nodi_simulator/utils.py`

## 设计原则
1. 标准结果库优先于 live 数据。
2. 旧结果库字段缺失时，允许在加载层补齐 gate / recommendation / decision summary 解释字段。
3. 页面层不直接重写这些补齐规则，统一由 backend 收口。

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
