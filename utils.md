# `nodi_simulator/utils.py`

> 本文件为模块导航摘要；完整 API、边界条件与实现细节以源码 docstring 和测试为准。

## 文件定位
- 类型：核心仿真模块
- 模块摘要：NODI Interferometric Simulator — Utility Functions
- 当前职责：提供跨模块复用的通用辅助函数与结果整理工具。

## 主要符号
- 顶层函数：`interpolate_at_theta`、`interpolate_complex_at_theta`、`resolve_collection_theta_rad`、`resolve_effective_polarization_mode`、`resolve_polarization_coupling`、`resolve_projection_basis`、`build_projection_basis_diagnostics`、`classify_projection_freeze`、`classify_interference_overlap_freeze`、`classify_delta_phi_gouy_geometry_validity`、`classify_observation_freeze`、`classify_design_recommendation`、`classify_engineering_gate_explanation`、`build_case_decision_summary`、`build_field_measure_diagnostics`、`build_coordinate_frame_mapping_diagnostics`、`build_detector_forward_diagnostics`、`build_collection_operator`、`compute_detected_scattering_field`、`compute_baseline_normalization`、`compute_baseline_normalization_per_wavelength` 等
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：这里承载核心物理或仿真逻辑，修改时应优先保证数值口径稳定，并补充对应测试。
- particle diagnostics 会拆出材料源、固定 RI / materials_db 模式、波长插值状态、温度修正状态与材料 uncertainty 状态；calibration diagnostics 会显式声明 Mie-to-power 单位链尚未闭合、calibration design 暂无 standards/wavelengths/geometries/held-out validation，且 `K_sca_uncertainty` 尚未传播。标准粒子尺寸分布、shape、ligand/shell、batch、浓度和材料数据集不确定度缺失时，不得把输出解释为 quantitative uncertainty。
- calibration manifest validation 会同时检查必需字段和 `calibration_kind`；错 lane manifest 会以 `manifest_kind_mismatch` 暴露，不能让 collection operator、standard particle、blank false-positive 或 BFP ROI mask 被当作有效标定。
- `build_collection_operator()` 会附带 BFP ROI mask contract 字段。未配置时保持 `current_radian_surrogate_mask`；synthetic/template 只测试管线；只有 measured/experimental role、字段完整、manifest kind 匹配且非 synthetic 时才允许 `bfp_roi_mask_source="calibrated_mask"`。
- `compute_detected_scattering_field()` 可接收已构建的 `collection_operator`，供 `nodi_simulator/parameter_sweep.py` 的 worker-local cache 复用 operator weights / calibration lookup 结果。未传入时仍按旧路径即时调用 `build_collection_operator()`，保持单函数调用兼容。
- background diagnostics 会输出 independent-superposition validity、`E_sca/E_ref` 估计、extinction-to-beam-area 估计与 channel-particle coupling model；未做 joint fullwave 时只作为弱叠加工程诊断。
- detector-noise diagnostics 会同时输出 `noise_terms` dict 与扁平的 photon-shot / electronics / RIN / speckle-like / drift / lock-in-output term status，便于 dataframe 和 dashboard 审计。

## 关联代码
- `nodi_simulator/data_objects.py`（`Particle`、`Medium`、`Channel`、`OpticalSystem`、`SimulationConfig`）
- `nodi_simulator/intrinsic_scattering.py`（`compute_intrinsic_scattering`）
- `nodi_simulator/trajectory.py`（`estimate_max_axial_velocity`）

## 专题补充
- [`guides/core/04_utils.md`](guides/core/04_utils.md)

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
