# nodi_simulator/data_objects.py — 数据对象定义

## 文件职责

定义整个工程中所有模块共用的 5 个核心数据类（dataclass）以及它们的默认实例。这些数据类的作用是把物理参数和计算逻辑彻底分开——所有物理参数通过这些对象传递，计算模块本身不硬编码任何参数值。

---

## 5 个数据类

### 1. Particle（粒子）

描述被检测的单个纳米粒子。

| 属性 | 类型 | 说明 |
|------|------|------|
| name | str | 描述性名称，如 "gold_40nm_diameter" |
| radius_m | float | 粒子半径（米），必须 > 0 |
| n_real | float | 折射率实部（固定值模式），必须 ≥ 0 |
| n_imag | float | 折射率虚部（固定值模式），默认 0.0，必须 ≥ 0 |
| model_type | str | 散射模型：`"mie"` 为均匀球，`"mie_core_shell"` 为同心 core-shell 球 |
| material_key | str \| None | 材料数据库键名，如 "gold"、"polystyrene" |
| use_material_model | bool | 是否启用波长依赖材料模型 |
| structure_key | str \| None | 结构化粒子 profile key；`model_type="mie_core_shell"` 时必填 |
| structure_params | dict \| None | 结构化粒子参数覆盖项 |

**属性方法**：`n_complex` 返回固定复折射率 `ñ = n_real + i·n_imag`。

**实例方法**：

```python
def n_complex_at(self, wavelength_m: float) -> complex
```

- `use_material_model=True` 时：从 `nodi_simulator/materials.py` 查询该波长下的真实光学常数
- `use_material_model=False` 时：返回固定的 `n_complex`

**使用说明**：
- 跨波长扫描时应设 `use_material_model=True`，让不同波长使用不同的光学常数
- `use_material_model=True` 时必须同时设置 `material_key`，否则抛出 ValueError
- 默认 `use_material_model=False`，返回固定的 `n_complex`（legacy 兼容行为）

### 2. Medium（介质）

描述纳米通道内的液体。

| 属性 | 类型 | 说明 |
|------|------|------|
| name | str | 如 "pbs_1x" |
| refractive_index | float | 实折射率（固定值），必须 > 0 |
| viscosity_Pa_s | float \| None | 动力粘度（Pa·s），扩散系数用 |
| temperature_K | float \| None | 温度（K），扩散系数用 |
| material_key | str \| None | 材料数据库键名，如 "pbs_1x" |
| use_material_model | bool | 是否启用波长依赖模型 |

**实例方法**：

```python
def refractive_index_at(self, wavelength_m: float) -> float
```

- `use_material_model=True` 时：从 `nodi_simulator/materials.py` 查询，取实部
- `use_material_model=False` 时：返回固定的 `refractive_index`

**注意**：当前介质语义已经按粒子分流：金粒子计算使用 `water`，exosome 计算使用 `1x PBS`。启用材料模型时，`water` 走 visible Cauchy nominal surrogate，`pbs_1x` 走 water Cauchy + nominal PBS offset；固定值字段只作为 legacy fallback。

### 3. Channel（纳米通道）

描述通道横截面。

| 属性 | 类型 | 说明 |
|------|------|------|
| width_m | float | 通道宽度 W（米），扫描范围 500–2000nm |
| depth_m | float | 通道深度 H（米），扫描范围 500–2000nm |
| wall_refractive_index | float | 壁面折射率（固定值），默认 1.46 |
| material_name | str | 壁材名称，默认 "fused_silica" |
| wall_material_key | str \| None | 壁材料数据库键名，如 "fused_silica" |

**坐标约定**：x 方向 [-W/2, W/2]，z 方向 [-H/2, H/2]。

**实例方法**：

```python
def wall_refractive_index_at(self, wavelength_m: float) -> float
```

- `wall_material_key` 非 None 时：从 `nodi_simulator/materials.py` 查询，取实部
- `wall_material_key` 为 None 时：返回固定的 `wall_refractive_index`

**注意**：当前默认壁材已经切到熔融石英。`wall_material_key="fused_silica"` 时走 Malitson Sellmeier nominal dispersion；`wall_refractive_index` 固定值只在 `wall_material_key=None` 的 legacy fallback 中使用。接口也为后续 near-wall correction / full-wave escalation 保留。

### 4. OpticalSystem（光学系统）

描述激光聚焦和检测几何。

| 属性 | 类型 | 说明 |
|------|------|------|
| wavelength_m | float | 真空波长 |
| peak_irradiance_W_m2 | float | 焦点处峰值照度 I₀ |
| beam_waist_x/y/z_m | float | 三个方向的 1/e² beam waist 半径 |
| focus_x/y/z_m | float | 焦点坐标，默认 (0,0,0) |
| collection_theta_rad | float | 固定角模式下的检测角 θ_det，默认 π/2 |
| illumination_NA | float \| None | 照明物镜 NA。若显式 beam waist 缺失，会用 `0.61*lambda/illumination_NA` 推导有效 illumination waist，当前默认 0.45 |
| NA_collection | float | 收集物镜 NA，当前默认 0.9；reference-side NA cutoff 直接使用它 |
| system_efficiency | float | 系统效率，保留但不乘入公式 |
| detection_mode | str | 检测模式，默认 "NODI" |

当前 `OpticalSystem` 里最重要的新语义是：**照明和收集已经拆成两套口径**。

- `illumination_NA` / effective illumination waist 负责 Tsuyama 条件下的照明几何
- `NA_collection` 负责 reference-side 可收集性 cutoff
- 因此当前不会再把 illumination `NA=0.45` 和 collection `NA=0.9` 混成同一套 beam semantics

### 5. SimulationConfig（模拟配置）

集中管理所有模拟控制参数。

| 属性 | 类型 | 说明 |
|------|------|------|
| total_time_s | float | 总模拟时长，必须 ≥ 10×transit duration |
| sampling_rate_Hz | float | 采样率 |
| mean_flow_velocity_m_s | float | 平均流速（沿 y） |
| include_diffusion | bool | 是否启用扩散 |
| flow_profile_model | str | 流场模型："plug"、`"parabolic_rect"` 或 `"rect_series"` |
| phase_model | str | 相位模型："constant"、"axial_path" 或 "relative_surrogate"；当前基础包默认已切到 `"relative_surrogate"` |
| collection_phi_sigma_rad | float | 2D pupil/slit surrogate 在 `phi` 方向的高斯宽度 |
| slit_phi_limit_rad | float | 2D pupil/slit surrogate 的 slit 半宽角 |
| path_opd_model | str | 散射侧 `z` 向 OPD 相对 reference surrogate plane 的定义："single_pass"`、`"reference_plane_roundtrip_surrogate"` 或 `"wall_referenced_gap_surrogate"`；当前基础包默认 `"single_pass"`，并已冻结为默认主线 |
| reference_model | str | 参考场模型："constant"、"geometry_scaled"、"calibrated_lookup"、"channel_angular_surrogate"、"paper_aligned_phase_filter" 或 "tsuyama_bfp_integrated"；当前基础包默认已切到 `"channel_angular_surrogate"` |
| reference_spatial_mode | str | 参考场横截面空间模式："uniform" 或 "cross_section_surrogate"；当前基础包默认已切到 `"cross_section_surrogate"` |
| reference_phase_grating_mode | str | `channel_angular_surrogate` 的 depth phase grating 模式：`"phase_grating_sine"` 或 `"legacy_sinc_linearized"`；当前基础包默认 `"phase_grating_sine"` |
| reference_width_saturation_mode | str | `channel_angular_surrogate` 的 width 向窄通道饱和模式：`"waveguide_cutoff_surrogate"` 或 `"none"`；当前基础包默认 `"waveguide_cutoff_surrogate"` |
| reference_width_saturation_cutoff_ratio | float | width-saturation 的无量纲 cutoff 比值 `u_cutoff`，控制 `W ≲ λ_eff` 时的软饱和强度，必须 > 0 |
| interference_overlap_mode | str | 干涉交叉项口径：`"collapsed_then_multiplied"` 或 `"joint_overlap_integrated"`；当前基础包默认 `"joint_overlap_integrated"` |
| reference_spatial_amplitude_strength | float | 参考场局部幅值随横截面位置起伏的强度 |
| reference_spatial_phase_strength_rad | float | 参考场局部相位随横截面位置起伏的强度 |
| reference_spatial_min_amplitude_scale | float | 参考场局部幅值的最小缩放下限 |
| reference_interference_on | bool | 是否保留 `2Re(E_ref E_sca*)` 交叉项 |
| nanoconfinement_on | bool | 是否保留通道限域输运 surrogate |
| background_subtraction_on | bool | 是否做 `I_det - |E_ref|^2` 背景减法 |
| free_solution_window_scale | float | 关闭通道限域时的自由窗口放大倍数 |
| collection_angle_model | str | 检测角模型："fixed" 或 "channel_diffraction"；当前基础包默认已切到 `"channel_diffraction"` |
| scattering_projection_mode | str | 当前散射主通道："intensity_proxy"、"parallel" 或 "perpendicular"；当前基础包默认已切到 `"parallel"`，`intensity_proxy` 仅保留为 legacy compatibility 路径 |
| coupling_model | str | 位置耦合模式：`"constant"` 或 `"gaussian_xy"` |
| illumination_mode | str | 照明模式：`"overfill"` 或 `"tight_focus"`；当前基础包默认 `"overfill"` |
| illumination_polarization_mode | str | 照明端如何投影到当前散射主通道："match_scattering"、"parallel"、"perpendicular" 或 "unpolarized" |
| reference_projection_mode | str | 参考场如何投影到当前散射主通道："match_scattering"、"parallel"、"perpendicular" 或 "unpolarized" |
| cross_polarization_leakage | float | 当照明/参考场被强制放到正交通道时保留的最小幅度比例，范围 [0,1] |
| diffraction_order | int | 检测角模型中的衍射级次，默认 1 |
| pulse_detection_mode | str | 脉冲检测模式："positive" 或 "absolute"；当前基础包默认已切到 `"absolute"` |
| detection_decision_mode | str | 最终判决模式："single_channel" 或 "paired_channel" |
| engineering_decision_basis | str | 工程评分 / gate 参考的检测口径："final_decision"、"single_channel" 或 "paired_channel" |
| engineering_min_strict_paired_detection_rate | float | 严格双通道检出率的工程 gate 下限，默认 0.0（关闭） |
| readout_model | str | 检测读出链模型："raw" 或 "lockin_surrogate"；当前基础包默认已切到 `"lockin_surrogate"` |
| readout_observable_mode | str | 锁相输出是 `"in_phase"` 还是 `"magnitude"` |
| lockin_time_constant_s | float | lock-in surrogate 的时间常数；当前默认 `1.0e-3 s = 1 ms` |
| pod_lockin_frequency_Hz | float | POD surrogate 的锁相参考频率 |
| nodi_lockin_frequency_Hz | float | NODI surrogate 的锁相参考频率 |
| pod_reference_phase_rad | float | POD 锁相参考相位 |
| nodi_reference_phase_rad | float | NODI 锁相参考相位 |
| pod_frequency_response_model | str | POD 频率响应 surrogate："flat" 或 `"inverse_power_surrogate"` |
| pod_frequency_response_reference_Hz | float | POD 频率响应归一化参考频率 |
| pod_frequency_response_exponent | float | POD 响应随频率下降的指数 |
| pod_frequency_response_min_gain | float | POD 频率响应增益下限 |
| pod_frequency_response_max_gain | float | POD 频率响应增益上限 |
| nodi_transit_response_model | str | NODI 通道渡越时间响应 surrogate：`"flat"` 或 `"time_constant_surrogate"` |
| nodi_transit_response_min_gain | float | NODI 渡越时间响应增益下限 |
| nodi_transit_response_max_gain | float | NODI 渡越时间响应增益上限 |
| pod_to_nodi_crosstalk | float | POD 通道泄漏到 NODI 的系数 |
| nodi_to_pod_crosstalk | float | NODI 通道泄漏到 POD 的系数 |
| noise_std | float | pre-readout 加性高斯噪声标准差 |
| shot_noise_scale | float | 与 `I_baseline / I_det` 相关的 pre-readout shot-noise surrogate 系数 |
| evaluation_false_alarm_rate | float | 用于把事件/背景分布转换成 fixed-false-alarm 命中率的目标误报率 |
| initial_position_distribution_mode | str | 初始 `(x0, z0)` 采样模式：`"uniform"`、`"uniform_accessible_area"`、`"center_biased_surrogate"` 或 `"flux_weighted"`；`"electrostatic_equilibrium"` / `"measured_cross_section_distribution"` 当前只保留在 schema 中并会被校验拒绝 |
| initial_position_center_bias_strength | float | 中心偏置采样的强度系数，越大越偏向通道中心 |
| initial_position_center_bias_min_confinement_ratio | float | 当 `a / min(W/2, H/2)` 超过该阈值时，中心偏置 surrogate 才开始显著偏离均匀分布 |

这一轮新增的偏振字段只做“最小统一通道语义”，不是完整矢量电场解。它们当前主要回答三件事：

- 当前 dashboard / batch 走的是哪条散射偏振通道
- 照明场是否与该通道同偏振，还是被按交叉偏振压低
- 参考场是否与该通道同偏振，还是被按交叉偏振压低

| 属性 | 类型 | 说明 |
|------|------|------|
| pulse_pairing_tolerance_s | float | POD/NODI 峰被视作同一事件时允许的最大时间偏差 |
| post_readout_noise_std | float | post-readout 高斯噪声标准差 |
| threshold_sigma | float | 阈值倍数（几个 σ） |
| min_peak_width_s | float | 最小峰宽（秒） |
| min_peak_interval_s | float | 最小峰间隔（秒） |
| n_events | int | 每个 batch 的事件数 |
| random_seed | int \| None | 随机种子 |
| vectorized_event_engine | str | 事件块执行引擎：`"off"`、`"pure_advection_block"`、`"event_block_v2"` 或 `"event_block_v3"`；基础包与正式 dashboard/precompute 默认均为 `"off"`，`event_block_v3` 只作为显式性能实验/回归对照 |
| event_block_size | int | 事件块最大 event 数；当前 precompute 固定默认 `32` |
| event_block_rng_order | str | `event_block_v2/v3` 的随机数消费顺序；当前正式默认 `"event_loop_order"`，实验选项 `"block_lane_order"` 会改变个体 event 轨迹 |
| rho | float | \|E_ref\| / \|E_sca_ref\| 的比值，默认 0.5 |
| normalization_mode | str | 归一化模式；当前基础包默认已切到 `"per_wavelength"` |
| ref_alpha | float | W 依赖指数，默认 0.0 |
| ref_beta | float | H 依赖指数，默认 0.0 |
| ref_gamma | float | λ 依赖指数，默认 0.0 |
| ref_g_min | float | geometry scaling 下限，默认 0.01 |
| ref_phi0_rad | float | geometry_scaled 参考相位，默认 0.0 |
| coupling_model | str | 空间耦合模式，默认 "constant" |
| noise_model | str | 噪声模式："gaussian" 或 "gaussian_plus_drift" |
| drift_slope | float | pre-readout 线性漂移斜率（信号单位/秒），默认 0.0 |
| post_readout_drift_slope | float | post-readout 线性漂移斜率（信号单位/秒），默认 0.0。 |
| reflecting_boundary | bool | 扩散反射边界开关，默认 True |
| score_mode | str | 评分模式："single" 或 "joint" |
| joint_alpha | float | 联合评分中对象 A 的权重，默认 0.5 |

**normalization_mode 的两个取值**：
- `"global_single_lambda"`：所有波长共用一个 E_sca_ref（legacy 兼容）
- `"per_wavelength"`（当前基础包默认）：每个波长独立计算自己的 E_sca_ref，消除跨波长锚定偏置

**vectorized_event_engine / event_block_rng_order 的当前边界**：

- 基础包 `DEFAULT_SIM_CFG` 默认 `vectorized_event_engine="off"`，这是为了让外部直接调用保持最保守的 scalar 行为。
- `dashboard.precompute.build_precompute_sim_cfg(...)` 会把正式预计算口径固定为 `vectorized_event_engine="off"`、`event_block_size=32`、`event_block_rng_order="event_loop_order"`。
- `off` 走 scalar event loop，不是低精度模式；它是当前 16C/32T 全量重算基准中更快且更保守的默认路径。
- `event_block_v3` 只作为显式实验选项。历史 64-case / 3000-event / 8-worker 对照中它快于 scalar 且 summary 对齐，但 16C/32T / 10000-event 对照中慢于 scalar/off，因此不作为正式全量默认。
- `block_lane_order` 只作为实验选项。它会带来检测率、稳定检测率、峰高、峰宽和工程 gate 漂移，因此不作为默认。

**reference_model 的六个取值**：
- `"constant"`：E_ref = ρ，不依赖几何（legacy 兼容）
- `"geometry_scaled"`：E_ref = ρ · g(W,H,λ)，surrogate 经验模型。α=β=γ=0 时退化为 constant
- `"calibrated_lookup"`：从 blank-channel 标定表读取或插值 `A_ref / phi_ref / g_ref`，更适合实验约束后的默认工作流
- `"channel_angular_surrogate"`（当前基础包默认）：先生成最小通道衍射角谱场，再过与 `E_sca` 相同的探测算子；适合作为“没有标定表时”的默认物理 fallback
- `"paper_aligned_phase_filter"`：Tsuyama paper-aligned comparison route，用于论文语义对照，不作为实测 calibrated truth
- `"tsuyama_bfp_integrated"`：BFP/ROI-resolved Tsuyama comparison lane，用于诊断/对照，不替代 calibrated lookup，也不授权 detector-resolved winner claim

**reference_spatial_mode 的两个取值**：
- `"uniform"`：整个事件内沿用同一个 case 级 `E_ref`
- `"cross_section_surrogate"`（当前基础包默认）：把 case 级 `E_ref` 推进为 `E_ref(x,z)`，让局部参考场幅值和相位随粒子横截面位置变化

**initial_position_distribution_mode 的 runtime-active 取值**：
- `"uniform"`（当前默认）：在粒子中心可达截面内均匀采样初始 `(x0, z0)`
- `"uniform_accessible_area"`：与 `uniform` 同样在粒子中心可达截面内均匀采样，但以更明确的状态名输出 `uniform_over_accessible_particle_center_area`
- `"center_biased_surrogate"`：在较强限域时，把初始位置分布向通道中心拉回；它是输运诊断 surrogate，不会直接修改 Mie / reference / interference 公式
- `"flux_weighted"`：按局部轴向输运速度做 acceptance-rejection 采样，使事件起点更接近通量条件化的截面分布；会导出 `flux_weighted_sampling_acceptance_rate / attempts`

`"electrostatic_equilibrium"` 和 `"measured_cross_section_distribution"` 目前只是 future schema 选项；当前 `SimulationConfig` 会拒绝它们，避免把未实现的实测/电荷平衡分布误当 runtime-active。

当前这条输运增强链会显式导出：

- 事件级：`initial_position_distribution_active / initial_position_confinement_ratio / initial_position_x_norm / initial_position_z_norm`
- batch 级：`initial_position_distribution_active_fraction / mean_abs_initial_x_norm / mean_abs_initial_z_norm`

这样后续审查就能直接区分：统计变化究竟来自光学链本身，还是来自初始截面占据分布变化。

**reference_phase_grating_mode 的两个取值**：
- `"phase_grating_sine"`（当前基础包默认）：depth response 采用 `2|sin(phase_delay/2)|`，作为更接近矩形相位凹槽的一阶相位光栅主线
- `"legacy_sinc_linearized"`：保留旧的 `(H/H0)|sinc(phase_delay/2π)|` 口径，作为显式诊断/兼容模式

**reference_width_saturation_mode 的两个取值**：
- `"waveguide_cutoff_surrogate"`（当前基础包默认）：在 `channel_angular_surrogate` 的 width 向 `sinc(W·...)` 中，用 `W_eff` 代替原始 `W`，避免极窄通道继续被自由空间 slit 口径乐观外推
- `"none"`：关闭 width 饱和修正，保留旧的 width 向 sinc 口径，只作为 legacy / 对照模式

当前这层 width-saturation surrogate 的最小语义是：

- `lambda_eff = λ0 / n_medium`
- `u = W / lambda_eff`
- `u_eff = sqrt(u^2 + u_cutoff^2)`
- `W_eff = lambda_eff · u_eff`

因此当 `W >> λ_eff` 时，`W_eff ≈ W`，主链几乎回到原模型；当 `W ≲ λ_eff`，尤其接近 `λ_eff/2` 时，`W_eff > W`，width 向 sinc 不再继续无限展宽。当前代码会显式校验：

- `reference_width_saturation_mode` 只能是 `"waveguide_cutoff_surrogate"` 或 `"none"`
- `reference_width_saturation_cutoff_ratio` 必须是有限正数

当前 `cross_section_surrogate` 还不是严格通道场解，但已经把 reference 场从“只有 case 级量”推进成了“case 级 anchor + event 级空间调制”的结构化 surrogate：

- `reference_spatial_amplitude_strength`：控制边缘/中心的局部 reference 幅值差异
- `reference_spatial_phase_strength_rad`：控制横截面位置引入的局部参考相位偏移
- `reference_spatial_min_amplitude_scale`：限制局部幅值不会数值塌缩到 0

**collection_angle_model 的两个取值**：
- `"fixed"`：直接使用 `OpticalSystem.collection_theta_rad`
- `"channel_diffraction"`（当前基础包默认）：使用 `theta = arcsin(m * lambda / W)` 的紧凑代理，让等效检测角随通道宽度变化

**pulse_detection_mode 的两个取值**：
- `"positive"`：只检测正峰（legacy 兼容模式）
- `"absolute"`（当前基础包默认）：在 `|signal|` 上找峰，但保留原始带符号峰高；适合引入位置相关相位后仍把负脉冲视为有效响应

**detection_decision_mode 的两个取值**：
- `"single_channel"`（默认）：最终 detect/miss 直接取 NODI 通道的峰提取结果
- `"paired_channel"`：先做 NODI 峰提取，再只保留那些能在 `pulse_pairing_tolerance_s` 内与 POD 峰配对的峰，最终 `detection_rate` 也随之切到严格双通道口径

**paired engineering gate 补充**：
- `engineering_min_strict_paired_detection_rate=0.0`（默认）表示不额外要求 strict paired detect
- 当该值大于 0 时，最终工程门槛会再要求 `strict_paired_detection_rate_wilson_lb >= engineering_min_strict_paired_detection_rate`
- 这样可以把“严格双通道口径下也要足够稳”作为独立 gate，而不只是展示型诊断量

**engineering_decision_basis 的三个取值**：
- `"final_decision"`（默认）：工程评分和 gate 跟随最终 `features` 口径
- `"single_channel"`：工程评分和 gate 固定按 NODI 单通道统计
- `"paired_channel"`：工程评分和 gate 固定按 paired-channel 统计

这让“最终 detect/miss 怎么定义”和“工程上要按哪套口径保守筛选”可以显式分开。例如：

- 可以保留 `detection_decision_mode="single_channel"` 做结果浏览
- 同时把 `engineering_decision_basis="paired_channel"`，要求工程排序优先尊重严格双通道确认

**phase_model 的三个取值**：
- `"constant"`：`phi_sca(t) = 0`，始终建设性干涉的最乐观近似
- `"axial_path"`：`phi_sca(t) = g_z * k_m * (z(t) - z_focus) * cos(theta_det)`，用于反映深度位置和扩散带来的干涉条件变化；`g_z` 由 `path_opd_model` 冻结
- `"relative_surrogate"`（当前基础包默认）：在 `axial_path` 基础上再加入沿流动方向的简化 Gouy 项；`phi_ref` 不会被重复乘入散射场，而是继续通过 `E_ref_complex` 进入干涉，模块同时显式输出 `Δφ = phi_sca - phi_ref`

**path_opd_model 的三个取值**：
- `"single_pass"`（当前基础包默认）：`phi_sca_path_z` 按单程 detector-projection surrogate 解释，`z` 向几何因子 = 1
- `"reference_plane_roundtrip_surrogate"`：`phi_sca_path_z` 按 roundtrip-like reference-plane surrogate 解释，`z` 向几何因子 = 2；当前主要用于对照审查，不作为默认冻结口径
- `"wall_referenced_gap_surrogate"`：`phi_sca_path_z` 改按“最近通道壁 gap 相对中截面居中”的诊断口径解释；它仍保持 `x` 向项不变，但会显式切换 `path_opd_reference_plane / path_opd_z_reference_mode`

这条配置不会改变 `x` 向项，只影响：

- `phi_sca_path_z_rad`
- `path_opd_reference_plane`
- `path_opd_z_geometry_factor`
- `path_opd_z_reference_mode`
- `path_opd_default_model`
- `path_opd_model_role`
- `path_opd_default_frozen`
- `path_opd_freeze_status`
- `delta_phi_ref` 的几何解释

当前 scattering trace 还会显式导出一组差分 Gouy 审计量：

- `phi_focus_crossing_rad`
- `phi_gouy_ref_rad`
- `phi_gouy_sca_rad`
- `delta_phi_gouy_rad`
- `gouy_dedup_active`

当前最小语义是：

- `phi_gouy_ref_rad = 0`
- `phi_gouy_sca_rad = phi_focus_crossing_rad` 当 `phase_model="relative_surrogate"`
- `phi_gouy_sca_rad = phi_beam_gouy_rad + phi_focus_crossing_rad` 当走未去重的 legacy / non-relative 路径
- `delta_phi_gouy_rad = phi_gouy_sca_rad - phi_gouy_ref_rad`
- `gouy_dedup_active = (phase_model == "relative_surrogate")`

这里需要特别注意：

- `phi_beam_gouy_rad` 现在保留为 illumination-side audit 字段
- `phi_gouy_ref_rad / phi_gouy_sca_rad / delta_phi_gouy_rad` 则明确表示“真实进入当前干涉链的 active Gouy 贡献”
- 也就是说，当前代码已经不再把 `phi_beam_gouy_rad` 直接等同于 reference trace 上的有效 Gouy 相位

**interference_overlap_mode 的两个取值**：
- `"joint_overlap_integrated"`（当前基础包默认）：先在角谱空间构造 `E_ref(theta,phi) · E_sca*(theta,phi)` 的联合 overlap，再在同一个探测算子下积分；当前已提升为默认 phase-aware 干涉主线
- `"collapsed_then_multiplied"`：先分别把 `E_ref(theta,phi)` 和 `E_sca(theta,phi)` 通过同一个探测算子 collapse 成两个标量复场，再计算交叉项；当前保留为 legacy-compatible 审计 / 对照口径

这条配置现在不再只是“先做审计再决定要不要启用”。当前工程已经根据 coarse probe 把 `joint_overlap_integrated` 提升成默认主线；`collapsed_then_multiplied` 的角色变成了显式的 alternative / legacy 对照路径。

**readout_model 的两个取值**：
- `"raw"`：直接在原始含噪干涉轨迹上做阈值和峰提取
- `"lockin_surrogate"`（当前基础包默认）：先把原始含噪轨迹分成 POD/NODI surrogate 两路，再通过各自的频率参考做最小 demod + low-pass，显式保留 I/Q 与 magnitude，最后叠加简化串扰并在 NODI 读出通道上做检测

**readout_observable_mode 的两个取值**：
- `"in_phase"`（当前 dashboard 默认）：检测层读取锁相的 I 分量，保留符号信息
- `"magnitude"`：检测层读取 `sqrt(I^2 + Q^2)` 包络，更接近“幅值锁相”读数，但会弱化符号信息

**当前 lock-in surrogate 的最小频率链**：
- `pod_lockin_frequency_Hz`：POD 通道的参考频率
- `nodi_lockin_frequency_Hz`：NODI 通道的参考频率
- `pod_reference_phase_rad / nodi_reference_phase_rad`：两路锁相参考相位
- `pod_frequency_response_model="inverse_power_surrogate"`（当前增强默认）：让 POD 通道额外乘一个近似 `gain ~ (f_ref / f_pod)^exponent` 的最小频率响应，低频更强，高频更弱，并裁剪到 `pod_frequency_response_min_gain ~ pod_frequency_response_max_gain`
- `nodi_transit_response_model="time_constant_surrogate"`（当前增强默认）：把 NODI lane 的可解调带宽显式挂到事件 `transit_time` 与 `lockin_time_constant_s` 上；当前最小 surrogate 使用 `f_transit ~ 1 / transit_time` 与 `f_lockin ~ 1 / (2π\tau)`，并把增益裁剪到 `nodi_transit_response_min_gain ~ nodi_transit_response_max_gain`

当前关于 `lockin_time_constant_s` 的现行口径补充如下：

- Tsuyama 2022 / 2024 给的是 `1–2 ms` 实验范围
- 当前代码默认值已统一为 `1 ms`
- 原因是实验设备通常按离散档位设置，直接给 `1 ms / 2 ms`
- 因此现在应把 `1 ms` 当作默认工作点，再对 `1 ms / 2 ms` 做敏感性检查

这一步不是完整光热传输模型，但已经能显式表达两件事：

- POD true lane 在低调制频率下更强
- NODI source 泄漏到 POD demod lane 的 `signal_pod_leak` 也会随 POD 频率一起变强，因此页面上终于能看到“低频 POD 更强、分离更难”的最小趋势
- 两者拉开时，cross-demod leakage 会被自然抑制；两者过近时，串扰更容易回到检测通道
- 粒子过焦区越快、而 lock-in 时间常数越慢时，NODI lane 会出现更强的带宽受限压低，不再把所有通过事件都当成同样容易被 NODI 读出

**collection_integration_mode 的三个取值**：

- `"single_angle"`：旧式单角点采样
- `"gaussian_weighted"`：1D `theta` 高斯收集核
- `"pupil_slit_surrogate"`：`theta + phi` 的最小可用 2D 收集 surrogate，包含弱 pupil、slit 与 pinhole 加权

**coupling_model 的两个取值**：
- `"constant"`（默认）：f_coupling = 1.0
- `"gaussian_xy"`：f_coupling = exp(-(x/wcx)² - (z/wcz)²)，中心耦合最强

**noise_model 的两个取值**：
- `"gaussian"`（默认）：纯高斯白噪声
- `"gaussian_plus_drift"`：高斯噪声 + 线性基线漂移 `drift_slope × t`

**当前噪声层说明**：
- `noise_std`：固定电子学/底噪 surrogate
- `shot_noise_scale`：随 `I_baseline / I_det` 放大的 pre-readout 光子统计噪声 surrogate
- `evaluation_false_alarm_rate`：把 `event_max_margin_z / background_max_margin_z` 转成 `hit_rate_at_fixed_false_alarm` 时使用的目标误报率
- `pulse_pairing_tolerance_s`：做最小双通道 pulse-pairing 诊断时，POD / NODI 峰时刻允许的最大偏差
- `post_readout_noise_std / post_readout_drift_slope`：读出之后、阈值之前的额外扰动

**score_mode 的两个取值**：
- `"single"`（默认）：每种粒子独立评分
- `"joint"`：双对象联合评分，要求恰好 2 种粒子类型。权重由 `joint_alpha` 控制（A 的权重 α，B 的权重 1-α）

**计算属性**：
- `dt_s`：时间步长 = 1/sampling_rate_Hz
- `n_samples`：总采样点数 = int(total_time_s × sampling_rate_Hz)

**当前校验补充**：
- `detection_decision_mode` 必须是 `"single_channel"` 或 `"paired_channel"`
- `engineering_decision_basis` 必须是 `"final_decision"`、`"single_channel"` 或 `"paired_channel"`
- `engineering_min_strict_paired_detection_rate` 必须落在 `[0, 1]`
- `nodi_transit_response_model` 必须是 `"flat"` 或 `"time_constant_surrogate"`
- `nodi_transit_response_min_gain` 必须 `>= 0`
- `nodi_transit_response_max_gain` 必须 `<= 1`
- `nodi_transit_response_max_gain >= nodi_transit_response_min_gain`

---

## 默认实例

| 实例名 | 说明 |
|--------|------|
| BASELINE_PARTICLE | 金粒子，直径 40nm，n_real=0.164，n_imag=2.47（Johnson & Christy, 660nm），material_key="gold" |
| PBS_1X | 1x PBS，n≈1.334，viscosity_Pa_s=1e-3，temperature_K=298.15 |
| WATER | 纯水，n≈1.33，viscosity_Pa_s=1e-3，temperature_K=298.15 |
| BASELINE_CHANNEL | W=800nm, H=550nm |
| BASELINE_OPTICAL | λ=660nm, wy=700nm；`collection_theta_rad = π/2` 仅在 `fixed` 模式下生效 |
| DEFAULT_SIM_CFG | 0.2s, 20kHz, 100 events, ρ=0.5；当前基础包默认主链：`channel_diffraction + pupil_slit_surrogate + parallel + relative_surrogate + channel_angular_surrogate + cross_section_surrogate + absolute + lockin_surrogate + per_wavelength`；当前默认 `lockin_time_constant_s = 1 ms`；`constant / fixed / single_angle / intensity_proxy / raw / positive` 保留为 legacy 兼容路径 |

---

## 输入验证

所有数据类在 `__post_init__` 中执行输入验证，使用 `raise ValueError` 而非 `assert`。当前校验包括：
- `Particle`：`use_material_model=True` 时 `material_key` 不能为 None
- `Medium`：`use_material_model=True` 时 `material_key` 不能为 None
- `SimulationConfig`：`collection_angle_model` 必须是 `"fixed"` 或 `"channel_diffraction"`
- `SimulationConfig`：`pulse_detection_mode` 必须是 `"positive"` 或 `"absolute"`
- `SimulationConfig`：`detection_decision_mode` 必须是 `"single_channel"` 或 `"paired_channel"`
- `SimulationConfig`：`phase_model` 必须是 `"constant"`、`"axial_path"` 或 `"relative_surrogate"`
- `SimulationConfig`：`path_opd_model` 必须是 `"single_pass"`、`"reference_plane_roundtrip_surrogate"` 或 `"wall_referenced_gap_surrogate"`
**illumination_mode 的两个取值**：
- `"overfill"`（当前基础包默认）：抹平横向 `x/z` 照明包络，但保留沿流向 `y` 的有限过境窗口；这是当前和 Tsuyama 条件对齐后的主线
- `"tight_focus"`：保留三维 Gaussian 包络，作为旧式紧聚焦对照模式

**flow_profile_model 的三个取值**：
- `"plug"`（当前基础包默认）：最小 advection surrogate
- `"parabolic_rect"`：矩形通道二次型近似
- `"rect_series"`：矩形 Poiseuille 的级数近似；dashboard 主默认链当前会优先用这条更完整的输运口径

这里要特别区分两层默认：

- `nodi_simulator/data_objects.py::DEFAULT_SIM_CFG` 是基础包最小默认链，仍偏保守、便于审计
- `dashboard/config.py::DEFAULT_SIM_CFG` 是 dashboard / precompute 主默认链，当前已切到 `rect_series + diffusion + gaussian_xy`

所以如果你在单案例页、预计算 metadata 或 dashboard 结果里看到默认输运口径比基础包更“重”，这是当前设计，而不是文档或代码漂移。
