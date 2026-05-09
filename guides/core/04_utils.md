# nodi_simulator/utils.py — 共享工具函数

## 文件职责

提供所有模块共用的工具函数。这些函数被多个模块调用，放在一起是为了避免重复和确保一致性。

本轮又补了一层结果解释 helper：不再让 `parameter_sweep / precompute / backend`
各自拼接推荐标签，而是统一由 `classify_design_recommendation(...)`
输出最终浏览层语义。

### `classify_design_recommendation(engineering_gate_passed, observation_freeze_status) -> dict`

统一归约结果浏览层推荐标签。

当前会返回：

- `design_recommendation_status`
- `design_recommendation_label`
- `design_recommendation_rank`
- `design_recommendation_guidance`

归约顺序是：

1. 先看 `engineering_gate_passed`
2. 再看 `observation_freeze_status`
3. 最后映射成 `recommended_default / recommended_with_caution / physics_ready_gate_blocked / not_recommended_freeze_blocked / monitor_only`

这层 helper 不改变 physics、`engineering_score` 或 gate，只统一“如何把结果解释给用户看”。

### `classify_engineering_gate_explanation(engineering_gate_passed, engineering_gate_reason, engineering_gate_failed_count) -> dict`

把原始 `engineering_gate_reason` 从自由文本收口成稳定字段。

当前会返回：

- `engineering_gate_status_label`
- `engineering_gate_primary_blocker`
- `engineering_gate_primary_blocker_label`
- `engineering_gate_blocker_summary`
- `engineering_gate_guidance`

当前主要 blocker 分类包括：

- `detected_events`
- `detection_rate`
- `stable_detection_rate`
- `phase_flip_fraction`
- `peak_margin`
- `strict_paired`
- `paired_detection_rate`

这层 helper 同样不改变 gate 结果本身，只负责把“为什么没过”变成可导出、可排序、可稳定显示的解释字段。

### `build_case_decision_summary(...) -> dict`

把结果层已经存在的三类解释量再压缩成一个**面向页面 callout 的统一摘要块**：

- 推荐标签：`design_recommendation_*`
- engineering gate 解释：`engineering_gate_*`
- 结果冻结状态：`observation_freeze_status`

当前统一返回：

- `decision_summary_tone`
- `decision_summary_headline`
- `decision_summary_badge`
- `decision_summary_primary_message`
- `decision_summary_blocker_text`
- `decision_summary_next_step`

归约顺序是：

1. 先读 `design_recommendation_status`
2. 再组合 `engineering_gate_passed / engineering_gate_status_label`
3. 最后叠加 `observation_freeze_status`

当前典型输出语义包括：

- `recommended_default -> success`
- `recommended_with_caution -> warning`
- `physics_ready_gate_blocked -> warning`
- `not_recommended_freeze_blocked -> error`
- 其余落到 `info`

这层 helper 的目的不是新增新的 physics 判据，而是把已经存在的
recommendation / gate / freeze 诊断收口成一块可复用的 UI 语义。现在
`Design Explorer`、`Case Inspector` 和 `build_physics_breakdown()` 都共用这一个摘要块，
从而避免三处页面各自拼接 slightly different 的解释文案。

---

## 函数列表

### `interpolate_at_theta(theta_grid_rad, values, theta_target_rad) → float`

**作用**：在角度网格上做一维线性插值，返回目标角度处的值。

**为什么单独提取出来**：baseline normalization（`compute_baseline_normalization`）和运行时（`run_single_case_batch`）都需要在 θ_det 处插值取散射幅值。如果两处用不同的插值方法（比如一个取最近点，一个做线性插值），会产生微小但系统性的不一致。把插值逻辑提取为共享函数，从根本上避免这个问题。

**内部实现**：
1. 检查 theta_target 是否在 theta_grid 范围内，否则抛出 ValueError
2. 调用 `np.interp` 做线性插值
3. 返回 float

---

### `interpolate_complex_at_theta(theta_grid_rad, values, theta_target_rad) → complex`

**作用**：在角度网格上对**复数值**数组做一维线性插值，实部与虚部分别调用 `interpolate_at_theta` 独立插值后合并。

**为什么单独提取出来**：`compute_detected_scattering_field` 的 `gaussian_weighted` / `pupil_slit_surrogate` 模式需要在 θ_det 处对 S1/S2 这类复散射振幅取值。实部与虚部分别插值可以保证与标量路径使用完全相同的插值逻辑，避免相位上的系统性误差。

**内部实现**：
```python
real = interpolate_at_theta(theta_grid_rad, np.real(values), theta_target_rad)
imag = interpolate_at_theta(theta_grid_rad, np.imag(values), theta_target_rad)
return complex(real, imag)
```

---

### `resolve_collection_theta_rad(channel, optical, sim_cfg, medium_refractive_index=None) → float`

**作用**：解析当前 case 实际使用的等效检测角。

**支持两种模式**：

- `fixed`：直接返回 `optical.collection_theta_rad`
- `channel_diffraction`：返回一个弱几何依赖的中心角代理；它先用
  `lambda_eff = lambda0 / n_medium` 形成 `arcsin(m * lambda_eff / W)` 的基值，
  再做宽深比缩放；若 `reference_model="calibrated_lookup"`，则把中心角固定到
  前向 `0 rad`，避免与 blank-channel 标定重复计入几何效应

**参数说明**：

- `medium_refractive_index`：可选浮点数。若不提供（或传入 `None`），回退为 `1.0`（真空/空气值），而非水的折射率（1.33）。传入实际介质折射率可确保 `channel_diffraction` 模式的等效波长计算正确。

**为什么需要它**：旧版本把所有 case 都固定在同一个检测角。更新后，如果启用 `channel_diffraction`，宽度 `W` 和介质折射率会一起影响等效检测中心；这样 `E_sca_at_det` 和归一化后的 `E_sca_normalized` 就不再被硬性锁死在旧的单角度假设上。同时，当参考场已经由标定表驱动时，中心角会回到前向，避免几何信息双计。

### `compute_detected_scattering_field(intrinsic, channel, optical, sim_cfg) → dict`

**作用**：把本征角分布压缩成检测链实际使用的一个复场代理。

当前关键点：

1. `single_angle` 模式保留旧式点采样
2. `gaussian_weighted` 模式使用 1D `theta` 核积分
3. `pupil_slit_surrogate` 模式会再引入一个 `phi` 向 surrogate，把 objective/pupil、slit 和 pinhole 压缩成最小可用的 2D 探测算子
4. 核函数里显式乘了 `sin(theta)` Jacobian，避免高角区权重失真
5. `pupil_slit_surrogate` 现在会额外引入 `theta` 向 pinhole 再筛选和显式 throughput 因子，因此“更窄的 slit / 更小的 pinhole”不仅改变权重形状，也会真实减小总收集量
6. `phi` 方向不再只是一条标量响应，而是最小二维复投影 surrogate，所以 parallel / perpendicular 通道现在会给出不同的复场结果
7. collection operator 当前还会显式保存自己的 `theta_grid_rad / phi_grid_rad`，避免 overlap 审计把 reference/scattering 的不同角网格静默混用

因此当前口径已经不再是“单点角采样”，而是“角谱中心 + 二维 surrogate 探测算子”的最小实现。

当前返回值除了 `E_sca_at_det / E_sca_normalized` 这一组主结果外，还会显式导出 4 个与相位审查直接相关的诊断量：

- `phi_projection_rad`
  当前探测算子真正压缩得到的复场相位，也就是后续实际进入干涉层的投影相位
- `phi_sca_material_rad`
  当前主投影通道对应的材料散射相位；`parallel` 取 `arg(S2 / k_m)`，`perpendicular` 取 `arg(S1 / k_m)`，`intensity_proxy` 则固定为 `0`
- `phi_sca_material_parallel_rad`
  不论当前主投影选择什么，都额外导出 `arg(S2 / k_m)`，便于和 `parallel` 主路径对照
- `phi_sca_material_perpendicular_rad`
  不论当前主投影选择什么，都额外导出 `arg(S1 / k_m)`，便于和 `perpendicular` 主路径对照

这样后续模块就可以区分：

- “材料本身的 Mie 散射相位”
- “经过有限角收集和偏振投影后，真正进入干涉计算的相位”

这也是当前路线图里“散射相位显式化”的第一步。`intensity_proxy` 仍保留用于历史对照，但现在更适合作为 compatibility / regression 路径，而不是默认物理解释主路径。

### `build_interference_overlap_diagnostics(...) → dict`

**作用**：把当前干涉层的两条交叉项语义并排导出并做 freeze 诊断：

- `collapsed_then_multiplied`
- `joint_overlap_integrated`

当前 helper 会先把 reference / scattering 的角谱场重采样到 operator 自己的 `theta` 网格，再计算：

```python
collapsed_product = (collapse E_ref) · (collapse E_sca)*
joint_overlap     = ∬ W E_ref E_sca* dΩ
overlap_factor    = joint_overlap / collapsed_product
```

因此当前会显式导出：

- `interference_collapsed_product_complex`
- `interference_joint_overlap_complex`
- `interference_overlap_factor_complex`
- `interference_overlap_factor_abs`
- `interference_overlap_factor_phase_rad`
- `interference_overlap_status`
- `interference_overlap_default_model`
- `interference_overlap_alternative_model`
- `interference_overlap_default_freeze_status`
- `interference_overlap_alternative_role`

当前默认主线已经切到 `joint_overlap_integrated`。因此 overlap helper 的职责不再是“证明 collapsed 能不能继续当默认”，而是：

- 允许 `joint_overlap_integrated` 直接作为 `default_frozen_mainline`
- 用 `collapsed_then_multiplied` 作为显式 alternative / legacy 对照
- 当两者差异大时，把 collapsed 降级成 `legacy_collapsed_review_only`

这一步的意义是把“角谱联合干涉和标量塌缩乘积到底差多少”从路线图概念推进成可审计的代码路径。

这一轮又补了一层偏振基底审计 helper：

- `resolve_projection_basis(mode)`：把模式折叠到 `parallel / perpendicular / intensity_proxy`
- `build_projection_basis_diagnostics(prefix, polarization, scattering_projection_mode)`：
  把 illumination / reference 端当前到底是不是“与散射场共用同一探测基底”
  显式导出成：
  - `*_projection_basis`
  - `*_effective_basis`
  - `*_projection_basis_match`
  - `*_projection_coupling_status`

因此偏振链不再只剩一个 `alignment_status` 文本，而是可以继续区分：

- 同基底满幅干涉 `shared_basis_matched`
- 同基底但交叉偏振泄漏压低 `shared_basis_cross_suppressed`
- 同基底的非偏振等分 `shared_basis_unpolarized_split`
- legacy 无基底语义 `legacy_basisless`

这一轮 utils 层又新增了 4 个 freeze judgement helper，用来把这些底层诊断进一步归约成结果冻结建议：

- `classify_projection_freeze(...)`
  把 `illumination / reference / interference` 三路的基底耦合状态压缩成
  `projection_default_freeze_status`
- `classify_interference_overlap_freeze(...)`
  把 overlap factor 的幅值、相位和 collapsed-vs-joint 误差压缩成
  `interference_overlap_default_freeze_status`
- `classify_delta_phi_gouy_geometry_validity(...)`
  用 `W / w_x`、`H / w_z` 这类无量纲几何比值，把 shared-beam Gouy 语义区分成
  `shared_beam_acceptable` 或 `shared_beam_caution`
- `classify_observation_freeze(...)`
  把 `path_opd / overlap / projection / gouy geometry` 四组 freeze judgement 再压缩成
  `observation_freeze_status`

因此当前 utils 已经不只是提供原始审计量，而是开始承担“把现有审计量归约成结果冻结判据”的责任。

---

### `validate_simulation_config(sim_cfg, optical) → None`

**作用**：在模拟开始前验证配置的物理合理性。

**检查内容**：

1. **总时间 ≥ 10 × transit duration**

   transit_duration = beam_waist_y / velocity。如果总时间太短，脉冲占信号的比例过大，背景估计不准。

2. **前 20% 时间段不含脉冲**

   轨迹设计让粒子在总时间 50% 处到达焦点。在前 20% 处，粒子距焦点的距离为 0.3 × total_time × velocity。这个距离必须 ≥ 5 × beam_waist_y，确保前 20% 段确实是纯背景。

3. **采样点数 ≥ 10**

不通过则抛出 ValueError。

---

### `sample_initial_position(channel, rng, particle_radius_m=0.0, sim_cfg=None) → (x0, z0, diagnostics)`

**作用**：在粒子中心可达横截面内采样事件初始位置，并导出本次采样对应的输运分布诊断。

**第一步：定义可达截面**
```python
half_w = W/2 - a
half_h = H/2 - a
```

因此采样永远发生在粒子中心真实可达的截面内，而不是名义通道边界上。

**uniform 模式**：
```python
x0 = rng.uniform(-half_w, half_w)
z0 = rng.uniform(-half_h, half_h)
```

**center_biased_surrogate 模式**：

先取 `u_x, u_z ~ Uniform(-1, 1)`，再做对称幂次拉伸：

```python
x0 = half_w * sign(u_x) * |u_x|**p_x
z0 = half_h * sign(u_z) * |u_z|**p_z
```

其中：

- `p_x > 1`、`p_z > 1` 时，采样分布会向中心集中
- `p_z` 当前通常比 `p_x` 更大，以表达深度方向更强的中心偏置
- 这两个指数由 `initial_position_center_bias_strength` 和
  `a / min(half_w, half_h)` 这组限域强度 proxy 决定

**uniform_accessible_area 模式**：

数值采样与 `uniform` 一样，仍在粒子中心可达截面内均匀采样；区别是 diagnostics 会明确输出
`cross_section_event_bias_status="uniform_over_accessible_particle_center_area"`，
用于和 legacy `uniform` 标签分开审计。

**flux_weighted 模式**：

先从可达截面均匀提议 `(x,z)`，再按局部轴向输运速度相对最大速度做 acceptance-rejection：

```python
accept_probability = local_velocity(x, z) / max_velocity
```

通过后作为 `(x0, z0)`。这条路径用于 EV/NODI design sweep 中更接近通量条件化的事件起点分布；它只改变事件起点抽样，不改变后续轨迹积分、光学或阈值公式。

**diagnostics 输出** 当前至少包括：

- `initial_position_distribution_mode`
- `initial_position_distribution_active`
- `cross_section_event_bias_status`
- `flux_weighted_sampling_acceptance_rate`
- `flux_weighted_sampling_attempts`
- `initial_position_center_bias_strength`
- `initial_position_center_bias_min_confinement_ratio`
- `initial_position_confinement_ratio`
- `initial_position_confinement_activation`
- `initial_position_center_bias_x_exponent`
- `initial_position_center_bias_z_exponent`
- `initial_position_x_norm`
- `initial_position_z_norm`

**为什么重要**：现在 batch 事件间的随机性不再只是“随机起点”，而是“随机起点 + 明确的初始截面占据分布口径”。这样后面看到峰高、极性或 phase occupancy 变化时，可以直接判断是不是初始分布先变了。

---

### `min_max_normalize(value, all_values) → float`

**作用**：Min-max 归一化到 [0, 1]。

**公式**：
```
result = (value - min) / (max - min)
```

如果所有值相同（max == min），返回 0.0。

**用途**：参数扫描完成后，对 mean_peak_height、detection_rate、CV 做统一归一化，然后线性组合成评分。

---

### `compute_baseline_normalization(particle, medium, optical_baseline, theta_grid_rad, channel=None, sim_cfg=None) → dict`

**作用**：计算全局归一化常数 E_sca_ref。

**调用时机**：在参数扫描开始前调用**一次**。返回的 E_sca_ref 被所有后续的 case 共用（global_single_lambda 模式）。

**内部逻辑**：
1. 用 baseline 参数调用 `compute_intrinsic_scattering`
2. 如果提供 `channel + sim_cfg`，先用 `resolve_collection_theta_rad` 得到当前 baseline 的等效检测角
3. 用 `interpolate_at_theta` 在 θ_det 处取值（与运行时完全相同的插值函数）
3. 返回该值作为 E_sca_ref

**输出**：
```python
{
    "E_sca_ref": float,        # > 0
    "wavelength_m": float,     # 记录用了哪个波长
    "theta_det_rad": float,    # baseline 使用的等效检测角
}
```

---

### `compute_baseline_normalization_per_wavelength(particle, medium, optical_template, wavelength_list_m, theta_grid_rad, channel=None, sim_cfg=None) → dict` 

**作用**：为每个波长独立计算 E_sca_ref，消除跨波长锚定偏置。

**为什么需要这个函数**：旧版中所有波长共用在 660nm 下计算的 E_sca_ref。这意味着 488nm 和 532nm 的归一化散射幅值实际上是"相对于 660nm baseline 粒子"的比值，而不是"相对于自身波长下的 baseline"的比值。当粒子光学常数随波长变化时（如 gold），这会引入系统性偏置。

**内部逻辑**：
```python
for wl in wavelength_list_m:
    optical = copy(optical_template)
    optical.wavelength_m = wl
    bl = compute_baseline_normalization(
        particle, medium, optical, theta_grid_rad,
        channel=channel, sim_cfg=sim_cfg,
    )
    result[wl] = bl["E_sca_ref"]
```

每个波长复制 optical_template、替换波长、独立计算 baseline。由于 `particle.n_complex_at(wl)` 在每个波长返回不同的光学常数，最终得到的 E_sca_ref 在不同波长间是不同的。

**输出**：`dict[float, float]`，键为波长（米），值为该波长的 E_sca_ref。

**与 compute_baseline_normalization 的关系**：

| 模式 | 使用的函数 | 行为 |
|------|-----------|------|
| global_single_lambda | compute_baseline_normalization | 单次调用，返回一个标量 E_sca_ref |
| per_wavelength | compute_baseline_normalization_per_wavelength | 每个波长调用一次上面的函数，返回字典 |

per_wavelength 内部复用了 compute_baseline_normalization，没有重复逻辑。

**典型输出示例**（gold, 40nm）：
```
λ=488nm → E_sca_ref=2.576e-09
λ=532nm → E_sca_ref=3.169e-09
λ=660nm → E_sca_ref=3.068e-09
```
