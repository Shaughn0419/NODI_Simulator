# \_\_init\_\_.py — 包入口文件

## 文件职责

作为 Python 包的入口，统一导出所有公开接口。使用者只需 `from nodi_simulator import ...` 即可访问所有核心功能，无需了解内部模块结构。

---

## 导出内容

### 数据类（来自 nodi_simulator/data_objects.py）
- `Particle`、`Medium`、`Channel`、`OpticalSystem`、`SimulationConfig`
- `DesignObjectiveConfig`
- 默认实例：`BASELINE_PARTICLE`、`PBS_1X`、`WATER`、`BASELINE_CHANNEL`、`BASELINE_OPTICAL`、`DEFAULT_SIM_CFG`
- EV/NODI design helper：`make_ev_nodi_design_sweep_config`、`make_gold_baseline_particle`、`DEFAULT_DESIGN_OBJECTIVE_CONFIG`

### 材料数据库（来自 nodi_simulator/materials.py）
- `get_n_complex`、`list_materials`、`material_property_summary`、`MATERIAL_DB`

### Mie 引擎（来自 nodi_simulator/mie_engine.py）
- `mie_compute`、`mie_angular`

### 物理计算（来自各功能模块）
- `compute_intrinsic_scattering`
- `compute_reference_field`
- `compute_reference_field_from_tsuyama_bfp`
- `compute_reference_field_trace`
- `compute_tsuyama_phase_filter_bfp_field`、`decompose_tsuyama_reference_field`、`integrate_bfp_roi`
- `compute_illumination_envelope`
- `simulate_particle_trajectory`
- `compute_scattering_field_trace`、`spatial_coupling_factor`
- `generate_interferometric_trace`

### 文件43治理 / scaffold / diagnostics
- design claim 与 minimum schema：`build_design_claim_governance_diagnostics`
- design metrics / postprocess：`attach_anchor_equivalent_metrics`、`attach_fluidic_practicality_metrics`、`attach_reference_operating_metrics`、`attach_ev_design_postprocess`
- EV / assay / controls：`build_ev_reporting_metadata_diagnostics`、`build_assay_control_matrix_diagnostics`、`build_control_interpretation_diagnostics`
- detector / reference / perturbation：`build_bfp_detector_operator_diagnostics`、`compute_detector_integrated_interference`、`build_particle_channel_perturbation_diagnostics`、`build_reference_operating_point_diagnostics`
- fluidics / geometry / electrokinetics / integrity：`build_fluidic_network_diagnostics`、`compute_rectangular_channel_hydraulic_resistance`、`build_channel_geometry_diagnostics`、`build_electrokinetic_transport_diagnostics`、`build_ev_integrity_risk_diagnostics`
- population / count / OOD / calibration planning：`build_count_likelihood_diagnostics`、`simulate_population_trace_from_event_library`、`build_population_inference_scaffold`、`build_ood_detection_diagnostics`、`build_bayesian_calibration_scaffold`、`build_calibration_plan_advisor`、`build_experimental_design_advisor`
- readout / units / wavelength / hardware safety：`build_nodi_readout_transfer_diagnostics`、`build_unit_axis_convention_diagnostics`、`build_mie_validation_diagnostics`、`build_wavelength_comparability_diagnostics`、`build_optical_exposure_safety_diagnostics`、`evaluate_objective_panel`
- run / selection / event QC / seed robustness：`build_run_state_diagnostics`、`build_selection_function_diagnostics`、`build_event_quality_control_diagnostics`、`run_seed_replicates`

### 信号处理（来自 nodi_simulator/pulse_analysis.py）
- `estimate_threshold_robust`、`extract_pulse_features`

### 编排与扫描（来自 nodi_simulator/parameter_sweep.py）
- `add_detector_noise`
- `simulate_one_event`、`summarize_batch`
- `run_single_case_batch`、`compute_case_score`
- `compute_joint_score`
- `compute_robust_scores`
- `run_parameter_sweep`

### 工具函数（来自 nodi_simulator/utils.py）
- `interpolate_at_theta`、`validate_simulation_config`
- `sample_initial_position`、`min_max_normalize`
- `compute_baseline_normalization`、`compute_baseline_normalization_per_wavelength`
- `compute_detected_scattering_field`
- `build_interference_overlap_diagnostics`
- `resolve_projection_basis`
- `classify_interference_overlap_freeze`
- `classify_projection_freeze`
- `classify_delta_phi_gouy_geometry_validity`
- `classify_observation_freeze`
- `classify_design_recommendation`
- `classify_engineering_gate_explanation`
- `build_case_decision_summary`

这意味着包根现在不仅导出基础数值工具，也直接导出 freeze judgement 所需的 helper，
方便 dashboard / tests / 外部脚本复用同一套判据，而不是各自复制一份阈值逻辑。
当前这套 helper 又向上延伸到了结果浏览层：`classify_design_recommendation()` 会把
`engineering_gate_passed + observation_freeze_status` 归约成统一的推荐标签。

此外，包根现在也直接导出文件43 v5 的治理/scaffold helper。它们默认用于生成 provenance、blocker、minimum schema、future calibration 插槽和 bounded claim 文本，不表示这些 lane 已经成为 calibrated quantitative solver。

---

## 版本号

`__version__ = "0.2.1"`

---

## 文件顶部注释

包含当前功能说明和主要工作流描述。
