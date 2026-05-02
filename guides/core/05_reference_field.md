# reference_field.py — 纳米通道参考场模块


<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

## 文件职责

计算 NODI 检测中的干涉参考场 E_ref。在 NODI 的物理机制中，纳米通道本身的衍射光扮演 interferometric reference 的角色——它不是背景噪声，而是主动参与干涉以增强弱散射信号的关键组成部分。

**设计原则**：reference field 必须独立成模块，不能混进 Mie 模块或 illumination 模块，因为它的物理来源不同——它来自通道几何，不来自粒子。

## 2026-04-28 关键更新

- `tsuyama_bfp_integrated` 不再只看默认 symmetric/slit surrogate ROI。若 `SimulationConfig.bfp_roi_mask_path` 指向 measured/calibrated BFP ROI mask，并且 manifest/role/schema 均通过 `build_bfp_roi_mask_contract(...)`，reference path 会把 mask row 投影到 Tsuyama 1D BFP q grid 后执行 weighted ROI 积分。
- 新增导出：`tsuyama_bfp_roi_mode="calibrated_bfp_roi_mask_projected_1d"`、`bfp_roi_mask_projection_status`、`bfp_roi_mask_projected_row_count`、`bfp_roi_mask_projected_sample_count`。
- 这条路径会改变 `E_ref_complex_roi / I_ref_intensity_roi`，但仍明确标记为 `calibrated_roi_mask_projected_1d_no_detector_unit_chain`；它不是完整 2D detector-unit overlap，也不解锁 calibrated voltage/photon/SNR claim。
- Synthetic fixture / template mask 不会进入积分，只保留 contract/status，防止模板被误用为实测 ROI。

---

## 函数

### `compute_reference_field(channel, optical, sim_cfg, medium_refractive_index=None) → dict`

#### 输入

- `channel`：通道几何（`geometry_scaled` / `calibrated_lookup` 模式使用 W 和 H）
- `optical`：光学系统（`geometry_scaled` / `calibrated_lookup` 模式使用 wavelength_m）
- `sim_cfg`：模拟配置（提供 ρ、reference_model、reference_route / solver_route、缩放参数，以及可选的 blank-channel 标定表路径）
- `medium_refractive_index`：通道内介质的实折射率；未提供时会回退到水样 baseline 值

#### 模式 1：constant

```python
A_ref = sim_cfg.rho        # 例如 0.5
phi_ref = 0.0
g = 1.0
E_ref_complex = A_ref · exp(i · 0) = A_ref + 0j
```

参考场是常数复数，不随通道几何或波长变化。legacy 兼容。

#### 模式 2：geometry_scaled

```python
W0, H0, lambda0 = 800e-9, 550e-9, 660e-9    # baseline 参考点
g_raw = (W/W0)^α · (H/H0)^β · (λ0/λ)^γ
g = max(g_raw, g_min)                         # 数值安全下限
A_ref = ρ · g
phi_ref = ref_phi0_rad
```

**关键注意**：这是一个 **surrogate scaling model**，用于相对排序，**不是物理衍射解**。代码中有显式注释标注此定位。

本轮又把这条 fallback 的“工程等级”写成了显式 diagnostics：

- `reference_model_precision_tier = "legacy_empirical_fallback"`
- `reference_model_precision_rank = 1`
- `reference_model_role = "legacy_fallback_only"`

也就是说，当前代码已经明确承认 `geometry_scaled` 不是和
`channel_angular_surrogate / calibrated_lookup` 同级的 reference model，
而只是当没有 blank-channel 标定表、又不方便使用角谱 surrogate 时的经验回退路径。

**参数含义**：

| 参数 | 物理含义 | 初始建议值 |
|------|---------|-----------|
| α (ref_alpha) | W 依赖：通道越宽衍射参考光越强 | 0.5 |
| β (ref_beta) | H 依赖：通道越深衍射参考光越强 | 0.3 |
| γ (ref_gamma) | λ 依赖：波长越短衍射效率越高 | 1.0 |
| g_min (ref_g_min) | 下限保护，防极端参数下 reference 崩为 0 | 0.01 |

**退化性**：α=β=γ=0 时 g=1.0，精确退化为 constant 模式。

**物理注意**：参考光更强不一定总更好——如果参考光太强而散射不变，信噪比反而可能变差。geometry_scaled 的效果是让 (W,H,λ) 通过 reference 强度影响 sweep 排名，而不仅仅通过粒子位置采样。

本轮还额外把 `ref_beta` 的物理解释显式导出为：

- `reference_geometry_depth_exponent`
- `reference_geometry_depth_scaling_class`
- `reference_geometry_depth_scaling_guidance`

当前 guidance 是：

- 薄相位光栅式直觉下，**幅度**更接近 `H^1`
- 对应**强度**更接近 `H^2`
- 如果 `ref_beta` 不靠近这两类，就会被标成 `intermediate_empirical / sub_amplitude_empirical / super_intensity_empirical`

因此现在审查 `geometry_scaled` 时，不再只是看 `g_ref` 变没变，而是能直接看当前 `H` 指数更像哪一类经验近似。

#### 模式 3：calibrated_lookup（新增）

当 `reference_model="calibrated_lookup"` 时，模块会从
`sim_cfg.reference_calibration_path` 指向的 `.csv` 或 `.json`
标定表读取 blank-channel 参考场数据。

推荐表头：

| 列名 | 含义 |
|------|------|
| `width_nm` | 通道宽度 |
| `depth_nm` | 通道深度 |
| `wavelength_nm` | 波长 |
| `g_ref` | 相对 reference scaling |
| `A_ref` | 参考场幅值（可选，若提供则优先使用） |
| `phi_ref_rad` | 参考场相位（可选） |

查询逻辑：

- 先按 `(W_nm, H_nm, λ_nm)` 做精确点匹配
- 若无精确点，则做三维线性插值
- 若线性插值落在凸包外，则退回最近邻，并把该 case 标记为 `calibration_extrapolated=True`

如果表里提供了 `A_ref`，则直接使用 `A_ref`；如果只有 `g_ref`，
则按：

`A_ref = rho · g_ref`

来构造参考场幅值。

相位 `phi_ref_rad` 若存在，则用相量插值 `exp(i phi)` 做平滑过渡；
若不存在，则默认 `0`。

这个模式的定位是：

- 仍然是工程 surrogate，而不是完整全波解
- 但比手写幂律 `geometry_scaled` 更接近真实 blank-channel 标定
- 适合未来把实验标定表直接接进模拟器

#### 模式 4：channel_angular_surrogate（当前无标定默认回退）

先生成一个最小通道衍射角谱复场 surrogate，再用**与 `E_sca` 完全相同的探测算子**做 collapse。这里的“相同”不是只共享 `theta_weights`，而是共享同一套：

- `collection_angle_model`
- `collection_integration_mode`
- `phi/slit/pinhole` 权重
- `scattering_projection_mode`
- `throughput_scale`

也就是说，`E_ref` 现在和 `E_sca_at_det / E_sca_ref` 一样，都会通过同一条 `operator_signature` 标识的收集算子。这样后面核对 reference 与 scattering 的相对口径时，不再只是文档约定，而是代码层显式约束。

这一轮还修掉了一个关键口径漏洞：`channel_angular_surrogate` 的**源场**不再提前乘
`exp[-theta^2 / (2 sigma^2)]` 这类 detector-side `theta` 接受包络。

当前正确分工是：

- `reference_field.py::_channel_diffraction_field_surrogate(...)`
  只负责生成通道本身的最小角谱复场 surrogate
- `utils.py::build_collection_operator(...)`
  与 `collapse_angular_field_with_operator(...)`
  统一负责 detector acceptance、slit/pinhole、theta/phi 权重和 throughput

这样做的原因很直接：

- 如果在 source field 里先乘一次 detector acceptance
- 后面 collapse 时再由 collection operator 乘第二次

就会把 reference amplitude 人为双重压低。

所以当前 `channel_angular_surrogate` 的语义已经明确变成：

`source angular field × shared collection operator`

而不是：

`source angular field × detector envelope × shared collection operator`

这一步修完后，`A_ref / g_ref` 才真正只反映：

- 通道 sinc 图样
- phase grating / width saturation
- shared detector operator

之间的相对关系，而不再混入 detector acceptance 的重复加权。

这一步现在还进一步显式吃进了 `medium_refractive_index`：

- 角谱里的波矢使用 `k = 2π n_m / λ0`
- 通道角谱幅值现在按**幅度一阶近似**
  `|Δn| = |n_wall - n_m|` 缩放，而不是按强度律 `Δn²` 解释
- 当前实现会显式导出
  `reference_index_contrast_abs / reference_contrast_amplitude_scale /
  reference_contrast_scaling_law`，便于审查 `Δn` 缩放是否真的按当前约定进入
- 返回值会带出 `reference_medium_refractive_index`

所以当前 `channel_angular_surrogate` 已经不再默认走“空气/真空参考场”口径，而是和主模拟里 `Medium` 的折射率语义一致。

这一轮又把**depth phase grating 的第二轮主线**接进了 reference 主链。当前不再只依赖：

- `|Δn|` 一阶幅度律
- 2D sinc 角谱

而是还显式引入：

```python
phase_delay = 2π · |Δn| · H / λ
legacy_sinc_scale = (H/H0) · |sinc(phase_delay / 2π)|
phase_grating_sine_scale = 2 · |sin(phase_delay / 2)|
phase_grating_amplitude_scale = (
    phase_grating_sine_scale      # 默认 phase_grating_sine 主线
    or legacy_sinc_scale          # legacy_sinc_linearized 诊断/兼容模式
)
phase_grating_phase = phase_delay / 2
```

其中：

- `H0 = 550 nm` 是当前 reference surrogate 的 baseline depth
- `reference_phase_grating_mode="phase_grating_sine"` 是当前默认主线
- `reference_phase_grating_mode="legacy_sinc_linearized"` 只保留作诊断/兼容对照
- `phase_grating_sine_scale = 2|sin(phase_delay/2)|` 更接近矩形相位凹槽的一阶相位光栅响应
- `legacy_sinc_scale` 保留旧的线性化口径，方便直接审计新旧趋势差异
- `phase_grating_phase` 负责把通道深度引起的相位延迟显式接进 `phi_ref`

这里当前要特别注意一个语义边界：在默认 `phase_grating_sine` 模式下，
`2|sin(phase_delay/2)|` 已经自身携带了 `Δn / H / λ` 的主要深度响应，因此
旧的 `reference_contrast_amplitude_scale` 不再作为 active amplitude multiplier，
而只作为**小相位延迟线性化诊断量**导出，避免把 `Δn·H` 重复计算两次。

这个实现仍然不是全波解，但它已经比“只有 `|Δn|` 一阶项 + 几何幂律”更接近相位物体 / 薄相位光栅的最小工程行为。

这一轮又补了一层 **极窄通道 width-saturation / cutoff surrogate**，它只作用在 width 向 sinc 包络，不额外改动 depth 向 phase grating：

```python
lambda_eff = wavelength_m / n_medium
u = W / lambda_eff
u_cutoff = reference_width_saturation_cutoff_ratio

if reference_width_saturation_mode == "none":
    W_eff = W
else:
    u_eff = sqrt(u**2 + u_cutoff**2)
    W_eff = lambda_eff * u_eff

width_sinc = sinc(W_eff * kx / 2π)
```

这层 surrogate 的物理意图是：

- `W >> λ_eff` 时，`W_eff ≈ W`，主链几乎回到原来的 width 向 sinc 口径
- `W ≲ λ_eff`，尤其接近 `λ_eff/2` 时，`W_eff > W`，因此 width 向角谱展宽会比自由空间 slit 外推更保守
- 它不是 RCWA / FDTD，也不是波导模求解；只是把“embedded groove 不是 free-space slit”的最小修正显式接进 reference 主链

当前会显式导出：

- `reference_width_saturation_mode`
- `reference_width_saturation_model`
- `reference_width_saturation_status`
- `reference_width_saturation_active`
- `reference_width_saturation_cutoff_ratio`
- `reference_width_lambda_ratio_nominal`
- `reference_width_lambda_ratio_effective`
- `reference_width_effective_m`
- `reference_width_saturation_factor`

其中：

- `active_soft_cutoff`：当前 case 真正触发了窄通道修正
- `inactive_wide_channel`：主链虽然启用了这层 surrogate，但当前几何已足够宽，几乎退化回旧模型
- `disabled_legacy_width_sinc`：显式关闭 width 饱和修正，仅保留旧口径作为对照

相位结构这轮也做了最小补强：矩形通道的 `sinc(W·kx)`、`sinc(H·kz)` 不再只把正负号隐含在振幅里，而是显式拆成：

- 振幅包络：`|sinc(...)|`
- 离散相位跳变：当某个轴向的 `sinc < 0` 时，对应轴贡献一个 `π` 跳变

也就是说，当前 reference surrogate 的总相位由两部分组成：

- 平滑连续 surrogate `phi_ref,surr(theta, phi)`
- 最小矩形衍射 `π` 跳变结构

对应诊断量会显式导出：

- `reference_phase_structure_mode`
- `reference_width_phase_jump_fraction`
- `reference_depth_phase_jump_fraction`
- `reference_phase_jump_fraction`
- `reference_phase_jump_max_rad`
- `reference_phase_delay_rad`
- `reference_phase_grating_mode`
- `reference_phase_grating_amplitude_scale`
- `reference_phase_grating_sine_amplitude_scale`
- `reference_phase_grating_legacy_sinc_amplitude_scale`
- `reference_phase_grating_response_abs`
- `reference_phase_grating_phase_rad`
- `reference_phase_grating_depth_scale`
- `reference_phase_grating_model`
- `reference_phase_grating_active_components`
- `reference_contrast_scaling_role`

这轮还把 reference 端接进了最小统一偏振框架。也就是说，`compute_reference_field(...)`
现在会先算出“几何/标定意义上的原始参考场”，再按：

- `reference_projection_mode`
- 当前 `scattering_projection_mode`
- `cross_polarization_leakage`

得到真正送进干涉层的有效 `A_ref`。如果 reference 与当前散射主通道同偏振，
幅度因子为 `1`；如果被强制投到正交通道，则按 `cross_polarization_leakage`
显式压低，而不是继续隐含成“默认总能干涉”。

#### 模式 5：paper_aligned_phase_filter

`reference_model="paper_aligned_phase_filter"` 走 `paper_aligned_comparison` route，用于 Tsuyama paper semantics 对照。它会保留 thin phase-filter validity、subwavelength groove、NA/cutoff 等诊断，但不把 paper-aligned 对照升级为实测 blank-channel calibrated reference。

当前 `reference_solver_route="auto"` 时，这条模型解析为 `tsuyama_phase_filter_1d` 或 paper-aligned angular surrogate 语义；输出中会保留 `reference_route / reference_solver_route / reference_solver_claim_level`，避免与普通 engineering fallback 或 calibrated lookup 混用。

#### 模式 6：tsuyama_bfp_integrated

`reference_model="tsuyama_bfp_integrated"` 是 detector-resolved BFP comparison lane。它通过：

```python
compute_reference_field_from_tsuyama_bfp(...)
```

把 `tsuyama_phase_filter.py` 产生的 BFP 复场经 ROI / detector operator 口径折叠成 reference comparison diagnostic。它的职责是让 BFP-level reference 与 ROI/operator 对照进入结果，而不是替代 measured calibration 或 detector-unit voltage / photon chain。

### reference route 与 solver route

当前 reference model 不只由 `reference_model` 单字段解释，还会解析：

- `reference_route`
  - `calibrated_primary`
  - `paper_aligned_comparison`
  - `engineering_fallback`
  - `legacy_debug`
- `reference_solver_route`
  - `calibrated_lookup`
  - `tsuyama_phase_filter_1d`
  - `tsuyama_bfp_integrated`
  - `engineering_channel_angular_surrogate`
  - `legacy_debug`

`reference_route="auto"` 会按 model 自动归类。这个分层是当前 claim governance 的关键：没有真实 blank calibration path 时，`channel_angular_surrogate` 只能是 engineering fallback；paper/BFP route 是 comparison；synthetic/template 不会解锁 calibrated quantitative claim。

---

### 【2026-04 新增】物理 NA 截止检查（NA Cutoff）

#### 背景与物理原因

NODI 干涉检测要求纳米通道衍射的参考光能够进入收集物镜。对于宽度为 W、折射率介质 n 的通道，一阶衍射极小角为：

```
θ_diff = arcsin(λ / (n·W))
```

收集物镜的接受角上限为：

```
θ_NA = arcsin(NA / n)
```

**当 θ_diff > θ_NA 时（等效条件：W < λ/NA），衍射参考光完全无法进入物镜，A_ref 物理上必须为零，NODI 原理失效。**

这一条件也等价于工程约束：通道最小可用宽度

```
W_min = λ / NA
```

**典型案例（NA=0.9，水中 n=1.33）：**

| 波长 | W_min (真空) | W_min (水中) | 700 nm 通道是否可用 |
|------|-------------|-------------|------------------|
| 404 nm | 449 nm | 304 nm | ✅ 可用 |
| 488 nm | 542 nm | 367 nm | ✅ 可用 |
| 532 nm | 591 nm | 400 nm | ✅ 可用 |
| **660 nm** | **733 nm** | **496 nm** | **❌ 不可用**（θ_diff=45.1° > θ_NA=42.6°）|

注：W_min(真空) = λ/NA；W_min(水中) = λ/NA_water，其中 NA_water = NA/n。

#### 代码实现

在 `compute_reference_field()` 的所有模型计算完成之后、偏振投影之前，加入统一截止检查：

```python
# reference_field.py，compute_reference_field() 中
_diff_ratio = optical.wavelength_m / (n_medium * channel.width_m)
_na_ratio   = optical.NA_collection / n_medium
_na_cutoff_active = bool(_diff_ratio > _na_ratio or _diff_ratio >= 1.0)
if _na_cutoff_active:
    A_ref = 0.0
    g = 0.0
```

**截止条件等价推导：**

```
θ_diff > θ_NA
⟺ arcsin(λ/(nW)) > arcsin(NA/n)
⟺ λ/(nW) > NA/n          （arcsin 在 [0,1] 上单调递增）
⟺ λ/W > NA
⟺ _diff_ratio > _na_ratio
```

#### 新增 `OpticalSystem` 字段

```python
# data_objects.py → OpticalSystem
NA_collection: float = 0.9  # 收集物镜数值孔径，用于 NA 截止检查
```

- 默认值 0.9 对应 Tsuyama 2022 实验中的高 NA 物镜
- 验证：`0 < NA_collection ≤ 2.0`
- 水浸物镜、油镜等高 NA 情况请相应修改（最大约 1.45~1.49）

#### 诊断量（新增到输出 dict）

```python
"na_cutoff_active": bool,       # 当前 case 是否触发了 NA 截止
"na_cutoff_diff_ratio": float,  # λ/(n·W)，第一阶衍射正弦值
"na_cutoff_na_ratio": float,    # NA/n，物镜接受角正弦值
"na_cutoff_NA_collection": float, # 当前使用的 NA 值
"na_cutoff_W_min_m": float,     # 当前波长对应的 W_min = λ/NA
```

#### 修正前后对比

| 场景 | 修正前 | 修正后 |
|------|--------|--------|
| 660 nm, W=700 nm, NA=0.9 | A_ref ≠ 0（计算错误） | A_ref = 0（物理正确）|
| 660 nm, W=800 nm, NA=0.9 | θ_diff=38.9° < 42.6° → A_ref OK | 无变化 |
| 404 nm, W=700 nm, NA=0.9 | θ_diff=25.6° << 42.6° → A_ref OK | 无变化 |

#### 引用与依据

- Tsuyama et al. 2022, *Microfluidics and Nanofluidics* — 实验几何约束分析（NA=0.9 检测物镜）
- 工程文件 `41_实验对齐原则与计算修正备忘.md` Principle 1（W_min 表格）
- 工程文件 `25_核心计算逻辑与公式总说明.md` § 19.8（已修正状态）

---

#### 输出

```python
{
    "E_ref_complex": complex,    # 参考场复振幅
    "A_ref": float,              # 参考场幅值
    "A_ref_unprojected": float,  # 偏振投影前的原始参考场幅值
    "phi_ref_rad": float,        # 参考场相位
    "g_ref": float,              # 偏振投影后的 effective reference scaling
    "g_ref_geometry": float,     # 仅几何/标定决定的 scaling（未乘偏振因子）
    "calibration_extrapolated": bool,  # 仅 calibrated_lookup 模式下出现
    "operator_signature": str,   # 仅 channel_angular_surrogate 模式下出现
    "na_cutoff_active": bool,    # NA 截止是否触发（2026-04 新增）
    "na_cutoff_diff_ratio": float,  # λ/(n·W)
    "na_cutoff_na_ratio": float,    # NA/n
    "na_cutoff_NA_collection": float, # 使用的 NA 值
    "na_cutoff_W_min_m": float,     # W_min = λ/NA
    "reference_projection_mode": str,
    "reference_projection_effective_mode": str,
    "reference_projection_amplitude_factor": float,
    "reference_projection_alignment_status": str,
    "reference_projection_basis": str,
    "reference_effective_basis": str,
    "reference_projection_basis_match": bool,
    "reference_projection_coupling_status": str,
    "reference_model_precision_tier": str,
    "reference_model_precision_rank": int,
    "reference_model_role": str,
    "reference_model_guidance": str,
    "reference_medium_refractive_index": float,  # 当前 reference 场采用的介质折射率
    "reference_index_contrast_abs": float,       # |n_wall - n_m|
    "reference_contrast_amplitude_scale": float, # 相对 baseline 的幅度缩放
    "reference_contrast_scaling_law": str,       # 当前缩放律说明
    "reference_contrast_scaling_role": str,      # 当前是 active multiplier 还是小信号诊断
    "reference_width_saturation_mode": str,      # waveguide_cutoff_surrogate 或 none
    "reference_width_saturation_model": str,     # 当前 width-saturation 说明文字
    "reference_width_saturation_status": str,    # active_soft_cutoff / inactive_wide_channel / disabled_legacy_width_sinc
    "reference_width_saturation_active": bool,   # 当前 case 是否真的触发窄通道修正
    "reference_width_saturation_cutoff_ratio": float,
    "reference_width_lambda_ratio_nominal": float,   # W / lambda_eff
    "reference_width_lambda_ratio_effective": float, # W_eff / lambda_eff
    "reference_width_effective_m": float,        # 当前实际用于 width 向 sinc 的 W_eff
    "reference_width_saturation_factor": float,  # W_eff / W
    "reference_phase_delay_rad": float,          # 通道深度引起的最小相位延迟
    "reference_phase_grating_mode": str,         # phase_grating_sine 或 legacy_sinc_linearized
    "reference_phase_grating_amplitude_scale": float, # depth phase grating 的额外幅度调制
    "reference_phase_grating_sine_amplitude_scale": float,         # 2|sin(phase_delay/2)|
    "reference_phase_grating_legacy_sinc_amplitude_scale": float,  # (H/H0)|sinc(phase_delay/2π)|
    "reference_phase_grating_response_abs": float,                 # 未加 floor 的 2|sin(phase_delay/2)|
    "reference_phase_grating_phase_rad": float,  # depth phase grating 显式相位项
    "reference_phase_grating_depth_scale": float,# H/H0
    "reference_phase_grating_model": str,        # 当前 depth phase grating 说明
    "reference_phase_grating_active_components": str, # 当前 active 幅度链说明
    "reference_diffraction_efficiency_model": str,
    "reference_diffraction_efficiency_zeroth_order": float,
    "reference_diffraction_efficiency_first_order": float,
    "reference_field_amplitude_envelope_role": str,
    "reference_field_amplitude_envelope_nominal": float,
    "reference_field_amplitude_envelope_lower": float,
    "reference_field_amplitude_envelope_upper": float,
    "reference_field_amplitude_envelope_lower_factor": float,
    "reference_field_amplitude_envelope_upper_factor": float,
    "reference_phase_structure_mode": str,       # 当前相位结构说明
    "reference_phase_jump_fraction": float,      # 发生 π 跳变的角谱占比
    "reference_geometry_depth_exponent": float,  # 仅 geometry_scaled 模式出现
    "reference_geometry_depth_scaling_class": str,
}
```

也就是说，reference 端现在不仅会告诉你“幅度有没有被 cross-polarization 压低”，
还会告诉你：

- 当前 reference 最终是投到哪条 detector basis 上
- 这条 basis 是否与当前 `scattering_projection_mode` 共用
- 当前属于“同基底满幅”“同基底泄漏压低”还是“legacy basisless”

### 本轮新增：reference-side diffraction efficiency 与幅度包络诊断

当前 reference 主线已经把 `phase_grating_sine` 当作 active depth 响应：

```python
delta_ref = 2π · |n_wall - n_medium| · H / λ
A_ref_active ~ 2 · |sin(delta_ref / 2)|
```

在这条 active 主线之外，代码又补了一层只用于 sanity check 的物理包络诊断：

```python
eta_0 = cos^2(delta_ref / 2)
eta_1 = sin^2(delta_ref / 2)
A_ref_envelope_nominal ~ |sin(delta_ref / 2)|
```

当前默认包络进一步写成：

```python
reference_field_amplitude_envelope_lower = 0.5 * A_ref_envelope_nominal
reference_field_amplitude_envelope_upper = 2.0 * A_ref_envelope_nominal
```

这里要特别注意语义边界：

- `eta_0 / eta_1 / A_ref_envelope_nominal` 当前不直接裁剪 reference 场
- 这组量的作用，是给后续 `rho` 提供一个 reference-side 的最小物理量级
- embedded groove 不是理想薄相位光栅，所以这里只把它当诊断包络，不当硬门槛

### `compute_reference_field_trace(trajectory, reference, channel, optical, sim_cfg, ...) → dict`

这一步是 2026-04-04 按路线图推进的第一批结构升级：把 case 级
`E_ref(W,H,λ)` 推进成 event 级的 `E_ref(x,z)` surrogate。

当前支持两种空间模式：

- `reference_spatial_mode="uniform"`
  退化回旧行为，整条事件里使用同一个 `E_ref_complex`
- `reference_spatial_mode="cross_section_surrogate"`
  在 case 级 `A_ref / phi_ref` 基础上，再按粒子轨迹里的 `x(t), z(t)`
  生成局部 reference 幅值和局部 reference 相位

当前 `cross_section_surrogate` 不是严格通道场解，但它已经让参考场的
event-to-event 变化不再只来自 `E_sca` 和轨迹本身，而是显式来自：

- `reference_amplitude_scale(x,z)`
- `reference_spatial_phase_rad(x,z)`

输出中会额外提供：

```python
{
    "E_ref_trace_complex": ndarray,
    "A_ref_trace": ndarray,
    "phi_ref_trace_rad": ndarray,
    "reference_amplitude_scale": ndarray,
    "reference_spatial_phase_rad": ndarray,
    "reference_x_norm": ndarray,
    "reference_z_norm": ndarray,
    "reference_spatial_mode": str,
}
```

---

## ρ 参数的物理含义

ρ 是 reference surrogate 的全局工程幅度系数；在当前主链里更准确的语义是：

`A_ref_unprojected = rho · g_ref_geometry`

- 当前基础包默认 `rho = 0.5`
- 在弱散射干涉中，信号 ≈ 2·Re(E_ref · E_sca*)，所以 ρ 越大干涉增强越明显
- ρ 是模型参数，**不是物理常数**，需要通过实验校准

### 当前 `rho` 物理包络诊断如何构造

reference 层给出的幅度包络现在不再去除以 scattering normalization 的 `E_sca_ref`。当前 case 层采用与 reference surrogate 一致的语义：

`rho_nominal ~ reference_field_amplitude_envelope / g_ref_geometry`

也就是说，当前显式导出的 `rho` 审计量是 reference-side 自洽包络，而不是跨到 scattering-side 归一化链。

```python
rho_physical_envelope_nominal ~ reference_field_amplitude_envelope_nominal / E_sca_ref
rho_physical_envelope_lower = 0.5 * rho_physical_envelope_nominal
rho_physical_envelope_upper = 2.0 * rho_physical_envelope_nominal
rho_physical_ratio_to_nominal = rho_requested / rho_physical_envelope_nominal
```

并进一步判断：

```python
rho_physical_envelope_in_range = (
    rho_physical_envelope_lower <= rho_requested <= rho_physical_envelope_upper
)
```

当前这组字段的定位仍然是**诊断性包络**：

- `sim_cfg.rho` 不会被静默改写
- 但 case / event / batch / dashboard 都会显式告诉你当前 `rho` 是否偏离 reference-side 的一阶物理建议区间

---

## 在流水线中的位置

```
SimulationConfig (ρ, α, β, γ, reference_calibration_path, reference_spatial_mode)
Channel (W, H)
OpticalSystem (λ)
        │
        ▼
compute_reference_field
        │
        ├── case-level E_ref_complex（复标量）+ g_ref
        │
        ▼
compute_reference_field_trace
        │
        ▼ E_ref_trace_complex(t) / phi_ref_trace_rad(t)
generate_interferometric_trace：E_det(t) = E_ref(t) + E_sca(t)
```

当前 reference 层已经不再总是“整个事件内完全不变的标量”。如果启用
`cross_section_surrogate`，它会在 case 级 anchor 上叠加 event 级位置相关
modulation，用来近似路线图里提出的 `E_ref(x,z)` 结构。
