# parameter_sweep.py — 参数扫描与编排模块

## 文件职责

这是整个工程中最大的模块，承担编排（orchestration）角色。它将所有下游模块串联成完整的模拟流水线，实现从"单次事件"到"批次统计"再到"参数扫描排名"的全部逻辑。

本轮按当前代码重新梳理后，确认这里的主责任没有漂移：

- `simulate_one_event()` 只负责单事件链路，不混入跨 case 归一化或评分
- `run_single_case_batch()` 负责把本征散射、检测角插值、归一化和 batch 统计收成一个 case
- `run_parameter_sweep()` 负责跨 `(particle, W, H, λ)` 遍历、统一归一化、single/joint/robust 评分
- selected detector-mode 属于 batch summary / report 的并行分析口径：`detection_rate` 保持 all-crossing 主分母；`selected_detector_mode_candidate_*` 与 `selected_detector_mode_annulus_*` 不进入 `compute_case_score` 或 engineering gate，但 EV targeted panel 与全量 size-weighted route analysis 会生成独立 selected-annulus ranking / comparison；annulus 边界来自 `SimulationConfig.selected_annulus_edge_norm_min/max`，默认 `0.5-0.8`；旧输入缺 selected-annulus 源列或新输入出现空 annulus 分母时，下游会显式标记 unavailable/null/NaN，gold-lane flatten 也会保留 NaN 而不是回填 0

当前实现除主流程函数外，还包含一组并行辅助函数，用于 case 级多进程调度。

主要函数如下：

| 函数 | 层级 | 作用 |
|------|------|------|
| **add_detector_noise** | **信号层** | **支持 drift 的噪声模型** |
| simulate_one_event | 事件层 | 模拟单个粒子通过事件 |
| summarize_batch | 统计层 | 统计一批事件的峰高/峰宽分布 |
| run_single_case_batch | Case 层 | 对一组 (W,H,λ) 跑完整 batch |
| compute_case_score | 评分层 | 计算单个 case 的综合评分 |
| **compute_joint_score** | **评分层** | **双对象联合评分** |
| **compute_robust_scores** | **评分层** | **邻域鲁棒评分** |
| run_parameter_sweep | 扫描层 | 遍历所有参数组合并排名 |
| _resolve_worker_count | 并行辅助 | 归一化 worker 配置 |
| _configure_parallel_worker_env | 并行辅助 | 限制每个 worker 的 BLAS/OpenMP 线程数 |
| _iter_case_specs | 并行辅助 | 生成可序列化的 case 任务 |
| _run_case_spec | 并行辅助 | 执行单个 case 任务 |
| _drain_parallel_cases | 并行辅助 | 有界地调度和回收进程池任务 |

---

## 函数详解

### 1. `add_detector_noise(signal_trace, time_s, sim_cfg, rng, *, detected_intensity=None, baseline_intensity=None) → dict`

当前 raw 噪声层已经拆成两部分：

- 固定电子学噪声：`noise_std`
- 基线相关 shot-noise surrogate：`shot_noise_scale`

**gaussian 模式**（默认）：
```
noise(t) ~ N(0, noise_std²)
```

**gaussian_plus_drift 模式**：
```
noise(t) = N(0, noise_std²) + drift_slope × t
```

如果 `shot_noise_scale > 0`，还会额外叠加：

```
shot_noise(t) ~ N(0, shot_noise_scale² · I_proxy(t))
I_proxy(t) = max(I_det(t), I_baseline)
```

当前这层还会显式导出 3 个 sanity diagnostics：

- `shot_noise_reference_dominated_fraction`
- `mean_shot_noise_intensity_proxy`
- `mean_shot_noise_baseline_proxy`

它们分别回答：

- `I_proxy` 有多少时间是被 `I_baseline` floor 顶住的
- 实际用于生成 shot-noise std 的平均 proxy 强度是多少
- baseline floor 本身的平均量级是多少

线性漂移模拟真实实验中的基线漂移。`drift_slope` 的单位是信号单位/秒。

`add_detector_noise` 通过 `sim_cfg.noise_model`、`sim_cfg.drift_slope` 和 `shot_noise_scale` 选择噪声模式。

### 2.5 `apply_readout_chain(signal_raw_noisy, time_s, sim_cfg, *, transit_time_s=None) → dict`

当前 `lockin_surrogate` 已经不是单纯“low-pass 一下 raw signal”。它现在的最小频率链是：

```
pod_source  = lowpass(raw)
nodi_source = lowpass(raw - pod_source)

pod_true  = demod(pod_source,  pod_f  -> pod_f)
nodi_true = demod(nodi_source, nodi_f -> nodi_f)

pod_leak  = demod(nodi_source, nodi_f -> pod_f)
nodi_leak = demod(pod_source,  pod_f  -> nodi_f)
```

然后再叠加：

```
signal_pod  = pod_true  + nodi_to_pod_crosstalk * pod_leak
signal_nodi = nodi_true + pod_to_nodi_crosstalk * nodi_leak
```

所以当前读出层已经同时包含：

- 时间常数 `lockin_time_constant_s`
- POD / NODI 两路参考频率
- POD / NODI 两路参考相位
- POD lane 的最小频率响应 surrogate
- I / Q / magnitude 三种内部读出量
- 简化频率失配抑制
- 通道串扰

本轮又补了一层更接近 Tsuyama 论文结论的最小趋势：

```
pod_gain = clip((pod_frequency_response_reference_Hz / pod_lockin_frequency_Hz)^exponent)
pod_true <- pod_gain * pod_true
pod_leak <- pod_gain * pod_leak
```

因此当前 `lockin_surrogate` 至少已经能表达：

- POD 调制频率越低，`signal_pod_true` 越强
- 在其他条件近似不变时，POD demod lane 里的 `signal_pod_leak` 也会一起变强
- 这仍然只是“最小频率响应解释力”，不是完整的热扩散/吸收/相位延迟模型

这一轮又把 NODI lane 的时间尺度约束显式接进了读出层：

```
f_transit ~ 1 / transit_time
f_lockin ~ 1 / (2π · lockin_time_constant)
nodi_gain ~ clip(1 / sqrt(1 + (f_transit / f_lockin)^2))
```

然后：

```
nodi_true <- nodi_gain * nodi_true
nodi_leak <- nodi_gain * nodi_leak
```

因此当前 `lockin_surrogate` 现在至少还能表达：

- 粒子过焦区越快，NODI lane 越容易被时间常数压低
- lock-in 时间常数越慢，NODI lane 越容易表现出带宽受限
- 这层效果也被显式导出，而不是埋在 `signal_nodi` 的幅值里

当前默认时间常数口径补充：

- Tsuyama 2022 / 2024 的实验范围是 `1–2 ms`
- 当前函数默认值已经统一到 `1 ms`
- 这是为了和真实机器常见的 `1 ms / 2 ms` 离散档位对齐，不再把 `1.5 ms` 当作现行默认值

并且检测层现在还多了一层选择：

- `readout_observable_mode="in_phase"`：阈值直接看 I 分量
- `readout_observable_mode="magnitude"`：阈值看 `sqrt(I^2+Q^2)` 包络

---

### 3. `_compute_diffusion_coefficient(particle, medium) → float | None`

Stokes-Einstein 自由空间扩散系数：

```
D = kB·T / (6π·η·a)
```

如果 medium 缺少 viscosity 或 temperature 数据，返回 None。

**注意**：这是自由空间公式，对受限通道中的近壁效应不做修正。近壁扩散抑制在 trajectory 模块中通过 `diffusion_hindrance_model` 应用。

---

### 4. `simulate_one_event(...) → dict`

**流水线"单次执行"函数。** 串联从轨迹到峰提取的所有步骤：

```
1. sample_initial_position → (x₀, z₀)
2. _compute_diffusion_coefficient → D         （仅 include_diffusion=True 时）
3. simulate_particle_trajectory(D, rng) → trajectory
4. compute_illumination_envelope → illumination
5. compute_scattering_field_trace(coupling_model) → sca_trace
6. generate_interferometric_trace → trace
7. add_detector_noise(time_s, sim_cfg) → signal_raw_noisy
8. apply_readout_chain → signal_detect_pre_post
9. add_post_readout_noise → signal_noisy
10. estimate_threshold_robust(前20%背景段) → threshold
11. extract_pulse_features / pairing filter → features
```

**当前行为说明**：
- 步骤 2-3：当 `include_diffusion=True` 时，计算 Stokes-Einstein D 并传给 trajectory
- 步骤 7：`add_detector_noise` 支持 drift 噪声
- 步骤 11：先得到 `features_nodi / features_pod`，再依据 `detection_decision_mode` 选择最终 `features`

**当前新增的物理点**：
- 单个 case 会先解析实际使用的等效检测角 `theta_det`
- 这个 `theta_det` 会同时影响 `E_sca_at_det` 插值和 `axial_path` 相位模型
- 因此在 `channel_diffraction` 模式下，宽度 `W` 的变化不仅影响位置采样，也会直接影响检测角和相位条件
- 当前 `compute_reference_field(...)` 也会显式接收 `medium.refractive_index_at(optical.wavelength_m)`，因此 reference 场不再默认使用空气/真空口径
- 当前事件链还会先把 case 级 `reference` 推进为 event 级 `reference_trace`：
  - `A_ref_trace`
  - `phi_ref_trace_rad`
  - `reference_amplitude_scale`
  - `reference_spatial_phase_rad`
  然后再进入 `generate_interferometric_trace`
- 当前事件链还会把 case 级散射相位诊断继续传进 `compute_scattering_field_trace(...)`：
  - `phi_sca_material_rad`
  - `phi_sca_material_parallel_rad`
  - `phi_sca_material_perpendicular_rad`
  - `phi_projection_rad`
  - `interference_overlap_factor_complex`
  - `interference_overlap_factor_abs`
  - `interference_overlap_factor_phase_rad`
  - `interference_overlap_status`

### 当前 overlap 审计如何接进 batch

在 `run_single_case_batch()` 里，reference/scattering 两侧当前会先导出角谱场：

- reference：`reference_angular_field`, `reference_theta_grid_rad`, `reference_phi_grid_rad`
- scattering：`angular_field_theta`, `theta_grid_rad`, `collection_operator`

然后用共享 helper 构造：

```python
collapsed_product = (collapse E_ref) · (collapse E_sca)*
joint_overlap = ∬ W E_ref E_sca* dΩ
overlap_factor = joint_overlap / collapsed_product
```

因此当前 case / event / batch 三层都会显式保留 overlap 诊断：

- case/reference 层：
  - `interference_overlap_mode`
  - `interference_cross_term_joint_available`
  - `interference_overlap_status`
  - `interference_overlap_factor_abs`
  - `interference_overlap_factor_phase_rad`
- event 层：
  - `interference_cross_term_collapsed`
  - `interference_cross_term_joint`
  - `interference_cross_term_mode`
- batch summary：
  - `mean_interference_overlap_factor_abs`
  - `mean_interference_overlap_factor_phase_rad`

这说明“角谱联合干涉”现在已经不是路线图上的抽象建议，而是贯穿到结果导出和 dashboard 的可审计量。
  因此单事件结果现在不仅有 `phi_sca_rad / phi_sca_path_rad / phi_ref_trace_rad / delta_phi_ref_rad`，还显式包含“材料散射相位”和“投影后进入干涉的相位”
- 当前事件链也把 OPD 语义显式冻结成可审计配置：
  - `path_opd_model`
  - `path_opd_reference_plane`
  - `path_opd_z_geometry_factor`
  - `path_opd_z_reference_mode`
  - `path_opd_default_model`
  - `path_opd_model_role`
  - `path_opd_default_frozen`
  - `path_opd_freeze_status`
  因此 `phi_sca_path_z_rad` 不再只是内部 surrogate，而是可以明确区分当前是单程 detector-projection 口径，还是 roundtrip-like reference-plane 对照口径
- 当前事件链还把差分 Gouy 审计量显式带出来了：
  - `phi_focus_crossing_rad`
  - `phi_gouy_ref_rad`
  - `phi_gouy_sca_rad`
  - `delta_phi_gouy_rad`
  因此现在可以把“beam 共享 Gouy 项”和“scattering 相对 reference 的穿焦差分项”分开审查
- 当前事件链还会把偏振基底一致性一起导出：
  - `scattering_projection_basis`
  - `illumination_projection_basis / illumination_projection_basis_match / illumination_projection_coupling_status`
  - `reference_projection_basis / reference_projection_basis_match / reference_projection_coupling_status`
  - `interference_projection_basis_match / interference_projection_coupling_status`
  因此“当前是否真的是同基底干涉”也不再需要靠页面端猜测
- 当前事件级结果还会补一组 reference-vs-scattering 幅值诊断：
  - `mean_A_ref_local`
  - `mean_A_sca_local`
  - `mean_reference_to_scattering_amplitude_ratio`
  - `median_reference_to_scattering_amplitude_ratio`
  - `reference_dominated_fraction`
  这组量的目的，是把“当前事件是不是仍处于 reference-dominated weak-scattering 区间”显式记录下来，而不是只看最终峰值
- 当前 pulse 判决链已拆成 `features_nodi / features_pod / features_paired / features`
  - `features_nodi`：NODI 单通道结果
  - `features_paired`：只保留那些能在 `pulse_pairing_tolerance_s` 内与 POD 峰配对的 NODI 峰
  - `features`：最终进入 `n_detected / detection_rate` 统计的峰集合
  - `detection_decision_mode="single_channel"` 时，`features = features_nodi`
  - `detection_decision_mode="paired_channel"` 时，`features = features_paired`
- 当前事件级结果还会把 `rho` 物理包络一并带出：
  - `rho_requested`
  - `rho_physical_envelope_source`
  - `rho_physical_envelope_nominal / lower / upper`
  - `rho_physical_ratio_to_nominal`
  - `rho_physical_envelope_in_range`
  - `rho_physical_envelope_status`
  - `reference_diffraction_efficiency_model`
  - `reference_diffraction_efficiency_zeroth_order / first_order`
  - `reference_field_amplitude_envelope_nominal`
  因此单事件结果现在还能明确回答：当前使用的 `rho` 是否已经偏离 reference 相位光栅给出的最小量级包络
- 当前事件级结果也会把 width-saturation 诊断一并带出：
  - `reference_width_saturation_mode`
  - `reference_width_saturation_status`
  - `reference_width_saturation_cutoff_ratio`
  - `reference_width_lambda_ratio_nominal`
  - `reference_width_lambda_ratio_effective`
  - `reference_width_effective_m`
  - `reference_width_saturation_factor`
  因此单事件结果现在还能明确回答：当前 reference 的 width 向角谱是否还停留在旧的自由空间 slit 外推口径，还是已经进入 `W ≲ λ_eff` 的软 cutoff 区间
- 当前 `observation_signature` 也会显式记录 `path_opd_model=...`，避免不同 OPD 假设下的 batch 结果被误当成同一观测链
- 当前 `observation_signature` 也会显式记录 `reference_phase_grating_mode=...`，避免 `phase_grating_sine` 和 `legacy_sinc_linearized` 两条 reference 主线混到同一结果集里
- 当前 `observation_signature` 也会显式记录：
  - `reference_width_saturation_mode=...`
  - `reference_width_saturation_cutoff_ratio=...`
  避免不同窄通道 cutoff 口径下的结果被误当成同一 reference 主线
- 当前 `observation_signature` 还会显式记录 `nodi_transit_model=...`，避免不同 NODI 读出口径下的结果被误当成同一观测链
- 当前 `observation_signature` 还会显式记录：
  - `initial_position_distribution_mode=...`
  - `initial_position_center_bias_strength=...`
  - `initial_position_center_bias_min_confinement_ratio=...`
  因此不同初始位置采样口径下的 batch 结果也不会再被误当成同一输运链
- 当前 `observation_signature` 还会显式记录：
  - `coupling_model=...`
  - `illumination_mode=...`
  - `flow_profile_model=...`
  - `include_diffusion=...`
  - `diffusion_hindrance_model=...`
  - `reflecting_boundary=...`
  这样同一组光学参数下，如果只是输运 / 照明主线不同，也不会再被误归到同一观测链

**随机性来源**：
- (x₀, z₀) 的随机采样
- 高斯噪声的随机实现
- 布朗扩散轨迹（当 `include_diffusion=True`）

---

### 5. `summarize_batch(event_results, stable_detection_margin_z_min=1.0) → dict`

统计一批事件的检测结果。对每个事件取最高峰。

| 指标 | 含义 |
|------|------|
| n_events | 总事件数 |
| n_detected | 至少检测到一个峰的事件数 |
| detection_rate | n_detected / n_events |
| stable_detection_rate | margin_z 超过稳定门槛的事件占比 |
| hit_rate_at_fixed_false_alarm | 以背景分布设定固定误报率后，事件分布能越过该阈值的比例 |
| roc_auc_event_vs_background | 事件最大判别分数 vs 背景最大判别分数的经验 ROC-AUC |
| d_prime_event_vs_background | 事件分布与背景分布的 d′ 可分性 |
| mean_peak_height | 平均峰高 |
| mean_positive_peak_height | 只对正峰取平均的峰高 |
| mean_negative_peak_height | 只对负峰取平均的峰高（按绝对峰高统计） |
| std_peak_height | 峰高标准差 |
| robust_cv_peak_height | `1.4826*MAD(heights) / median(heights)` |
| event_artifact_risk_score | event QC 相关 artifact 风险分数，进入工程连续分数的惩罚项 |
| mean_peak_width_s | 平均峰宽 |
| mean_peak_margin_z | 平均 `(peak_height-threshold) / robust_std_bg` |
| mean_transit_time_s | 主 Gaussian waist 区域内的平均 transit time |
| mean_local_snr | 读出链主峰相对本地 robust 噪声的平均局部 SNR |
| mean_nodi_transit_bandwidth_Hz | 事件 `1 / transit_time` 的 batch 平均值 |
| mean_nodi_transit_bandwidth_gain | NODI lane transit-bandwidth gain 的 batch 平均值 |
| mean_nodi_bandwidth_limited_fraction | NODI lane 因 transit/lock-in 时间尺度不匹配而受限的平均比例 |
| single_channel_n_detected | 按 `detected_single_channel` 统计的单通道检出事件数 |
| single_channel_detection_rate | 以 `features_nodi` 统计的单通道检出率 |
| single_channel_detection_rate_wilson_lb | 单通道检出率的 Wilson 保守下界 |
| single_channel_stable_detection_rate | 单通道口径下 `margin_z` 超过稳定门槛的事件占比 |
| paired_channel_detection_rate | 以 `features_paired` 统计的严格双通道检出率 |
| paired_channel_detection_rate_wilson_lb | 双通道检出率的 Wilson 保守下界 |
| paired_channel_stable_detection_rate | 双通道口径下 `margin_z` 超过稳定门槛的事件占比 |
| strict_paired_detection_rate | 当前与 `paired_channel_detection_rate` 同义，显式导出供 dashboard / 审查层使用 |
| strict_paired_detection_rate_wilson_lb | `strict_paired_detection_rate` 的 Wilson 保守下界 |
| paired_detection_rate | 检出事件里至少一个 NODI 峰能与 POD 峰配对的比例 |
| mean_I_baseline | 事件级 `|E_ref|^2` 基线强度平均值 |
| mean_shot_noise_std | shot-noise surrogate 的平均标准差 |
| mean_shot_noise_reference_dominated_fraction | `I_proxy` 被 `I_baseline` floor 主导的平均时间占比 |
| mean_A_ref_local / mean_A_sca_local | 事件内平均 reference / scattering 幅值 |
| mean_reference_to_scattering_amplitude_ratio | 平均 `|E_ref| / |E_sca|` 比值 |
| mean_reference_dominated_fraction | `|E_ref| >= |E_sca|` 的平均时间占比 |
| rho_requested | 当前 case 请求的 `sim_cfg.rho` |
| rho_physical_envelope_nominal | reference-side 包络与 `g_ref_geometry` 映射得到的 `rho` 名义量级 |
| rho_physical_envelope_lower / upper | `rho` 诊断包络上下界 |
| rho_physical_ratio_to_nominal | `rho_requested / rho_physical_envelope_nominal` |
| rho_physical_envelope_in_range | 当前 `rho` 是否落在诊断包络内 |
| rho_physical_envelope_status | `within_envelope / below_envelope / above_envelope / unavailable` |
| reference_diffraction_efficiency_zeroth_order / first_order | `delta_ref` 对应的最小薄相位光栅 `η0 / η1` 诊断 |
| n_positive_peaks / n_negative_peaks | 检出峰里正峰 / 负峰的个数 |
| positive_peak_fraction / negative_peak_fraction | 检出峰里正峰 / 负峰的占比 |
| all_heights | 所有峰高列表 |
| all_widths | 所有峰宽列表 |

当前 `stable_detection_rate` 已不再通过原始 `peak/threshold` ratio 判定，而是使用
`stable_detection_margin_z_min` 门槛判断 `margin_z` 是否足够大。这比直接使用原始比值更稳，因为它显式参考了背景 `robust_std`。

本轮又补了一层极性分组统计：

- `mean_positive_peak_height`
- `mean_negative_peak_height`
- `n_positive_peaks / n_negative_peaks`
- `positive_peak_fraction / negative_peak_fraction`

其中 `mean_negative_peak_height` 仍沿用当前 `peak_height` 口径，也就是统计“被检测到的负峰的绝对峰高”；真正带符号均值仍看 `mean_signed_peak_height`。

当前还额外构造了两组“事件 vs 背景”的判别分数：

- `event_max_margin_z = (max(signal_for_detection) - threshold) / robust_std_bg`
- `background_max_margin_z = (max(background_segment_for_detection) - threshold) / robust_std_bg`

其中 `signal_for_detection` 会跟随 `pulse_detection_mode` 选择 `signal` 或 `|signal|`。基于这两组分数，当前 batch 统计会进一步输出：

- `hit_rate_at_fixed_false_alarm`
- `roc_auc_event_vs_background`
- `d_prime_event_vs_background`
- `fixed_false_alarm_rate_used`

同时这层现在还会显式给出 reference / scattering / shot-noise 的联动 sanity diagnostics：

- `mean_I_baseline`
- `mean_shot_noise_std`
- `mean_shot_noise_reference_dominated_fraction`
- `mean_reference_to_scattering_amplitude_ratio`

所以当前 batch 汇总已经能直接回答：

- shot noise 是不是主要由 reference baseline 主导
- 当前 case 还是不是明显处在 `|E_ref| > |E_sca|` 的弱散射干涉口径
- 当前 `rho` 是否仍然落在 reference-side 物理建议区间

本轮还补了一组“初始位置分布是否已经偏中心”的 batch 诊断：

- `initial_position_distribution_mode`
- `initial_position_distribution_active_fraction`
- `cross_section_event_bias_status`
- `flux_weighted_sampling_acceptance_rate`
- `flux_weighted_sampling_attempts`
- `mean_abs_initial_x_norm / mean_abs_initial_z_norm`
- `mean_initial_position_confinement_ratio`
- `mean_initial_position_confinement_activation`
- `mean_initial_position_center_bias_x_exponent / mean_initial_position_center_bias_z_exponent`

其中：

- `initial_position_distribution_active_fraction` 表示这一批事件里真正启用了中心偏置采样的事件占比
- `mean_abs_initial_x_norm / mean_abs_initial_z_norm` 用归一化到截面的初始位置绝对值，直接反映“起始点是否被拉向通道中心”
- `mean_initial_position_center_bias_*_exponent` 用来审计当前 bias surrogate 在宽度方向与深度方向分别有多强

当前 batch 汇总还会额外给出三类“更方便解释事件机制”的量：

- `mean_transit_time_s / median_transit_time_s`
  用 `A_env >= exp(-1)` 的持续时间估算粒子经过主腰斑的停留时间
- `mean_local_snr / median_local_snr`
  用 `max(|signal_detect_pre_post|) / robust_std_bg` 估算局部读出 SNR
- `mean_nodi_transit_bandwidth_Hz / mean_nodi_transit_bandwidth_gain / mean_nodi_bandwidth_limited_fraction`
  把 NODI lane 是否受到 transit-time / time-constant 失配压低显式统计出来
- `single_channel_detection_rate / paired_channel_detection_rate / strict_paired_detection_rate`
  明确区分单通道 detect 和严格双通道 detect
- `single_channel_stable_detection_rate / paired_channel_stable_detection_rate`
  把“是否检出”和“检出后是否足够稳”拆开，便于后续工程 gate 改按 paired 口径校准
- `single_channel_detection_rate_wilson_lb / paired_channel_detection_rate_wilson_lb / strict_paired_detection_rate_wilson_lb`
  给三套 detect 口径都配上小样本保守下界，便于工程 gate 和 dashboard 直接复用
- `paired_event_rate / paired_detection_rate / best_peak_pairing_rate`
  用 POD/NODI 两路峰时刻在 `pulse_pairing_tolerance_s` 内是否对齐，给出最小双通道 pulse-pairing 诊断；其中 `paired_detection_rate` 当前是“单通道已检出事件里，同时具备 POD 配对的比例”

---

### 6. `run_single_case_batch(...) → dict`

一组参数跑完整 batch 的入口。归一化在此完成：

```python
intrinsic = compute_intrinsic_scattering(...)
collection_operator = build_collection_operator(...)
E_sca_detected_complex = compute_detected_scattering_field(..., collection_operator=collection_operator)
E_sca_unit_normalized = E_sca_detected_complex / E_sca_ref
reference = compute_reference_field(...)
# 跑 n_events 次 → summarize_batch
```

归一化放在编排层而非 intrinsic_scattering，保持物理计算的纯净性。

当前每个 case 还会额外生成：

- `operator_signature`：仅描述探测算子
- `observation_signature`：把探测算子、参考场模型/相位、reference depth phase-grating 主线、相位模型、检测模式、读出模型、噪声模型、`shot_noise_scale` 和 `pulse_pairing_tolerance_s` 串成一条完整观测链签名
- 当前 `observation_signature` 还会记录：
  - `reference_spatial_mode`
  - `reference_phase_grating_mode`
  - `reference_spatial_amplitude_strength`
  - `reference_spatial_phase_strength_rad`
  - `detection_decision_mode`
  - `initial_position_distribution_mode`
  - `initial_position_center_bias_strength`
  - `initial_position_center_bias_min_confinement_ratio`
  - `coupling_model`
  - `illumination_mode`
  - `flow_profile_model`
  - `include_diffusion`
  - `diffusion_hindrance_model`
  - `reflecting_boundary`
- 当前 `intrinsic` 还会额外导出 case 级散射相位诊断：
  - `phi_projection_rad`
  - `phi_sca_material_rad`
  - `phi_sca_material_parallel_rad`
  - `phi_sca_material_perpendicular_rad`
- 当前 case / event / batch 结果还会显式带出初始位置分布诊断：
  - 事件级：`initial_position_distribution_active / initial_position_confinement_ratio / initial_position_x_norm / initial_position_z_norm`
  - batch 级：`initial_position_distribution_active_fraction / mean_abs_initial_x_norm / mean_abs_initial_z_norm`
  - 这样 sweep 结果在审查时就能直接区分“是相位链在变”，还是“是初始截面占据分布先偏向了通道中心”
- `reference_interference_on / nanoconfinement_on / background_subtraction_on`：把参考场交叉项、通道限域输运和背景减法拆成三个可审计的增强来源开关
- 当前 case / batch 结果还会把 `rho` 包络诊断显式冻结进 summary：
  - `rho_requested`
  - `rho_physical_envelope_source`
  - `rho_physical_envelope_nominal / lower / upper`
  - `rho_physical_ratio_to_nominal`
  - `rho_physical_envelope_in_range`
  - `rho_physical_envelope_status`
  - `reference_diffraction_efficiency_model`
  - `reference_diffraction_efficiency_zeroth_order / first_order`
  - `reference_field_amplitude_envelope_nominal`

这组量当前仍然是**诊断字段**，不会静默覆盖 `sim_cfg.rho`；它们的职责是给下一步 freeze judgement 提供更可审计的 reference 强度边界。

---

### 7. `compute_case_score(H_norm, R_norm, CV_norm, ...) → float`

综合评分函数：

```
J = w_height · H̃ + w_rate · R̃ - w_cv · CṼ
```

默认权重全为 1.0。传入值必须已做 min-max 归一化。

### 7.1 `compute_engineering_score(stable_rate_norm, threshold_margin_norm, local_snr_norm, CV_norm, robust_CV_norm, phase_flip_penalty, ...) → float`

工程排序当前使用：

`engineering_score = 1.0*stable_rate_norm + 0.7*threshold_margin_norm + 0.4*local_snr_norm + 0.5*auc_norm + 0.5*hit_rate_norm + 0.3*d_prime_norm - 0.4*CV_norm - 0.4*robust_CV_norm - 0.5*phase_flip_penalty - 0.6*event_artifact_risk_norm`

这里虽然参数名还保留 `CV_norm / threshold_margin_norm`，但当前代码口径已经更新为：

- `threshold_margin_norm` 来自当前 `engineering_decision_basis` 对应的 `mean_peak_margin_z`
- `local_snr_norm` 来自 `mean_local_snr`
- `auc_norm` 来自 `roc_auc_event_vs_background`
- `hit_rate_norm` 来自 `hit_rate_at_fixed_false_alarm`
- `d_prime_norm` 来自 `d_prime_event_vs_background`
- `CV_norm` 来自普通 `CV`
- `robust_CV_norm` 来自 `robust_cv_peak_height`
- `stable_rate_norm` 当前使用 `engineering_decision_basis` 对应的稳定检出 Wilson 下界
- `phase_flip_penalty` 当前使用 `engineering_decision_basis` 对应的翻相 Wilson 上界
- `event_artifact_risk_norm` 来自 `event_artifact_risk_score`

也就是说，当前工程评分已经不再主要依赖原始 `peak/threshold` ratio 和普通 `std/mean`。

另外，最终工程决策已经不再只靠这个连续分数本身。当前 `run_parameter_sweep()` 会在 `engineering_score` 之后再计算：

- `engineering_decision_basis`
- `engineering_basis_detection_rate_wilson_lb`
- `engineering_basis_stable_detection_rate_wilson_lb`
- `engineering_basis_mean_peak_margin_z`
- `detection_rate_wilson_lb`
- `strict_paired_detection_rate_wilson_lb`
- `engineering_gate_basis`
- `engineering_gate_required_detected_events`
- `engineering_gate_stable_detection_rate_lb`
- `engineering_gate_phase_flip_fraction_ub`
- `engineering_gate_mean_peak_margin_z`
- `engineering_gate_strict_paired_rate_lb`
- `engineering_gate_required_strict_paired_detection_rate`
- `engineering_gate_passed / engineering_gate_failed_count / engineering_gate_reason`
- `engineering_gate_status_label / engineering_gate_primary_blocker / engineering_gate_primary_blocker_label / engineering_gate_blocker_summary / engineering_gate_guidance`
- `final_engineering_gate_rank / final_engineering_failure_rank / final_engineering_score_rank`
- `final_engineering_score`
- `design_recommendation_status / design_recommendation_label / design_recommendation_rank / design_recommendation_guidance`

其中 gate 的核心语义已经升级成：

- 先按 `engineering_decision_basis` 选定工程评估口径：`final_decision / single_channel / paired_channel`
- 再对这套口径检查绝对检出数门槛：`n_detected >= max(engineering_min_detected_events, ceil(engineering_min_detected_fraction * n_events))`
- 再对这套口径检查比例保守下界门槛：`detection_rate_wilson_lb >= engineering_min_detected_fraction`
- 可选 strict paired 门槛：当 `engineering_min_strict_paired_detection_rate > 0` 时，还要求 `strict_paired_detection_rate_wilson_lb >= engineering_min_strict_paired_detection_rate`
- 再叠加 `stable_detection_rate_wilson_lb / phase_flip_fraction_wilson_ub / mean_peak_margin_z`

因此，当前真正的最终工程排序是“先过门槛，再按失败项个数和 `engineering_score` 排序”，而不只是看单个标量。

当前主链又在 gate 之上补了一层推荐解释：

- gate 通过 + `observation_freeze_status = default_ready_for_result_freeze`
  - `design_recommendation_status = recommended_default`
  - `design_recommendation_label = 推荐（默认）`
- gate 通过 + `observation_freeze_status = caution_probe_before_result_freeze`
  - `design_recommendation_status = recommended_with_caution`
  - `design_recommendation_label = 推荐（需复核）`
- gate 未过，但 observation freeze 已 ready
  - `design_recommendation_status = physics_ready_gate_blocked`
  - `design_recommendation_label = 可研究（门槛未过）`
- observation freeze blocked / review-required
  - `design_recommendation_status = not_recommended_freeze_blocked`
  - `design_recommendation_label = 不推荐（冻结未就绪）`

这层标签不改变物理量、score 或 gate，只把“是否值得继续看”从排序分数里拆出来，供 dashboard 浏览层直接使用。

另外，当前 gate 本身的解释层也已经做成结构化字段，而不再只靠原始
`engineering_gate_reason` 字符串：

- `engineering_gate_status_label`
- `engineering_gate_primary_blocker`
- `engineering_gate_primary_blocker_label`
- `engineering_gate_blocker_summary`
- `engineering_gate_guidance`

因此现在可以稳定地区分：

- “工程门槛通过”
- “主要卡在稳定检出率”
- “主要卡在相位翻转占比”
- “主要卡在严格双通道确认”

而不是只在 Inspector 里手读一长串 `reason`。

---

### 8. `compute_joint_score(summary_a, summary_b, ...) → float`

双对象联合评分。

```
J_joint = α · J_a + (1-α) · J_b
```

**物理约束（CRITICAL）**：两个对象必须共享同一系统设定——同一 (W, H, λ)、同一 ρ、同一 reference_model、同一 coupling_model 和 noise_model。这反映的物理现实是两种粒子通过同一检测系统。不允许分别调参后再联合。

参数：
- `summary_a`, `summary_b`：两种粒子在同一 (W,H,λ) 下的 batch 统计
- `all_heights`, `all_rates`, `all_cvs`：全 sweep 的值列表（用于归一化）
- `alpha`：对象 A 的权重（默认 0.5）
- `score_weights`：评分权重字典

---

### 9. `compute_robust_scores(results, width_list, depth_list, wavelength_list) → list[dict]`

邻域鲁棒评分。对每个参数点，取其在 (W,H,λ) 网格上所有直接邻居的平均 score。

**设计动机**：单点 score 高可能是统计波动或参数尖峰。robust_score 高意味着整个邻域都好，是更可靠的设计推荐。

邻居定义：在 W、H、λ 三个维度各取前后一格（如果存在），形成最多 3×3×3=27 个邻居（含自身）。

原地修改：在每个 result dict 中添加 `robust_score` 键。

---

### 10. `run_parameter_sweep(...) → list[dict]`

**最顶层函数。** 遍历 particle_types × wavelength_list × width_list × depth_list。

#### 新增参数

| 参数 | 说明 |
|------|------|
| baseline_particle | 用于 per-wavelength baseline 计算。normalization_mode="per_wavelength" 时必填 |
| baseline_channel | collection angle 依赖通道宽度时，用于 baseline 归一化的基准通道 |
| n_workers | worker 进程数。`1` 表示串行；`0` 表示使用全部逻辑 CPU |

#### 新增行为

1. **Joint scoring**：当 `sim_cfg.score_mode="joint"` 时：
   - 要求恰好 2 种粒子类型，否则抛 ValueError
   - 按 (W,H,λ) 配对两种粒子的 summary
   - 计算 `joint_score` 并以此排序

2. **Robust scoring**：所有模式下都计算 `robust_score`（邻域平均分）

3. **排序**：
   - `score_mode="single"`：按 `score` 排序
   - `score_mode="joint"`：按 `joint_score` 排序

4. **并行执行**：
   - 当 `n_workers <= 1` 时，按旧行为串行执行
   - 当 `n_workers > 1` 时，以 case 为粒度使用 `ProcessPoolExecutor`
   - 为避免 Windows/OpenBLAS 出现“进程数 × BLAS 线程数”过度抢核，会自动把每个 worker 的 `OPENBLAS_NUM_THREADS`、`OMP_NUM_THREADS`、`MKL_NUM_THREADS` 等环境变量限制为 `1`
   - worker initializer 会只传一次粒子、介质解析器、光学模板、`SimulationConfig` 与 `theta_grid_rad`，case spec 中只保留轻量索引和几何/波长值，减少 IPC 和 pickle 开销

5. **失败策略**：
   - `theta_grid_rad` 是必需的 1D 非空网格，缺失时会在任何 case 执行前抛出 `ValueError`
   - 默认 `allow_partial=False`，任意 case 失败都会在 sweep 结束前抛出 `SweepCaseFailureError`，避免把空库或有偏部分库标记为完成
   - 只有显式 `allow_partial=True` 时才允许返回成功子集；precompute 会把 partial policy 写入 metadata

6. **事件块引擎**：
   - dashboard/precompute 主线默认使用 `vectorized_event_engine="off"`，即 scalar event loop
   - 当前固定默认为 `event_block_size=32`、`event_block_rng_order="event_loop_order"`
   - `event_loop_order` 保持 scalar event loop 的随机数消费顺序，便于 exact regression 对照
   - `event_block_v3` 保留为显式性能实验/回归对照；它不是当前正式全量默认
   - `block_lane_order` 使用分 lane 随机流，可能更快，但会改变个体 event 轨迹；当前只作为实验选项

#### 输出

每个 case 的结果 dict 包含：

| 键 | 类型 | 说明 |
|----|------|------|
| particle_name | str | 粒子类型名 |
| wavelength_m | float | 波长 |
| width_m | float | 通道宽度 |
| depth_m | float | 通道深度 |
| summary | dict | batch 统计结果 |
| score | float | 单粒子评分 |
| H_norm | float | 归一化峰高 [0,1] |
| R_norm | float | 归一化检出率 [0,1] |
| CV_norm | float | 归一化变异系数 [0,1] |
| **robust_score** | **float** | **邻域鲁棒评分** |
| **joint_score** | **float** | **联合评分（仅 joint 模式）** |

---

## 典型调用示例

```python
# 联合模式 + 扩散 + 漂移噪声
sim_cfg = SimulationConfig(
    ...,
    include_diffusion=True,
    noise_model="gaussian_plus_drift",
    drift_slope=0.001,
    score_mode="joint",
    joint_alpha=0.6,   # 60% 权重给 gold
)

results = run_parameter_sweep(
    particle_types=[gold, exosome],  # 恰好 2 种
    ...,
)

# 结果按 joint_score 排序
for r in results[:5]:
    print(f"joint={r['joint_score']:.3f}, robust={r['robust_score']:.3f}")
```

## 并行辅助函数说明

### `_resolve_worker_count(n_workers) → int`

统一处理 worker 配置：
- `None` → `1`
- `1` → 串行
- `0` → `os.cpu_count()`
- `<0` → 抛出 `ValueError`

### `_configure_parallel_worker_env() → dict`

在进入多进程路径前，为当前进程补齐线程限制环境变量。返回实际写入的变量，便于 `verbose=True` 时打印。

### `_iter_case_specs(...)`

把 `(particle, wavelength, W, H)` 展开成一个个可序列化任务 dict，便于在 Windows 的 spawn 模式下分发给子进程。

### `_run_case_spec(case_spec) → dict`

执行单个 case。成功时返回 `summary / intrinsic / reference`，失败时返回带 `ok=False / error / traceback` 的结果。上层 `run_parameter_sweep()` 默认会收集失败并抛出 `SweepCaseFailureError`，不会静默保存部分 sweep；只有显式 `allow_partial=True` 才允许继续使用成功子集。

### `_drain_parallel_cases(case_specs, n_workers)`

用有界的 in-flight future 数量去调度进程池，避免一次性提交过多任务占满内存。
