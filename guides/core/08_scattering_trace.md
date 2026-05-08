# scattering_trace.py — 时域散射场模块

## 文件职责

将上游模块的结果（本征散射幅值、照明包络、轨迹）组合成时域散射复场 E_sca(t)。这是从"静态散射量"到"时间信号"的桥梁。

---

## 核心公式

```
E_sca(t) = E_env_complex(t) · E_sca_unit_normalized · f_coupling(t) · e^{iφ_extra(t)}
```

各项含义：

| 因子 | 来源 | constant 模式 | gaussian_xy 模式 |
|------|------|--------------|-----------------|
| E_env_complex(t) | illumination 模块 | 复高斯包络 surrogate | 复高斯包络 surrogate |
| E_sca_unit_normalized | intrinsic → 插值 → 归一化 | 无量纲复场代理 | 无量纲复场代理 |
| f_coupling(t) | spatial_coupling_factor | **1.0** | **exp(-(x(t)/wcx)² - (z(t)/wcz)²)** |
| e^{iφ(t)} | 相位模型 | e^{i·0} = 1 | `axial_path` 时随 z(t) 变化；`relative_surrogate` 时再叠加简化 focus-crossing 项 |

---

## 函数

### `spatial_coupling_factor(x0_m, z0_m, channel, coupling_model) → float | ndarray`

位置相关的几何耦合因子，表示粒子在当前位置的散射光被检测系统收集的效率。
当前实现既支持标量输入，也支持整条轨迹数组输入。

#### constant 模式
```python
return 1.0
```
所有位置耦合效率相同。legacy 兼容。

#### gaussian_xy 模式
```python
wcx = channel.width_m / 2    # 特征宽度 = 通道半宽
wcz = channel.depth_m / 2    # 特征深度 = 通道半深
return exp(-(x0/wcx)² - (z0/wcz)²)
```

- 通道中心 (0,0)：f = 1.0（最大耦合）
- 通道边缘 (W/2, 0)：f = exp(-1) ≈ 0.368
- 通道角落 (W/2, H/2)：f = exp(-2) ≈ 0.135

#### 关于与 illumination 的双重衰减

`A_env(t)` 已经对横向偏离焦点进行高斯衰减（照明强度）。`gaussian_xy` 再加一层衰减代表的是**不同的物理机制**：

- **A_env**：照明光在横向的强度分布（粒子被照亮的程度）
- **f_coupling**：几何耦合效率（散射光被检测系统收集的程度）

两者可以物理上同时存在。但如果合并后衰减过强（sweep 排名剧变），应调整 coupling 的特征长度（例如放宽为 `wcx = channel.width_m`）。建议做 constant vs gaussian_xy 对照实验确认合理性。

---

### `compute_scattering_field_trace(...) → dict`

#### 输入

| 参数 | 类型 | 说明 |
|------|------|------|
| trajectory | dict | 轨迹（提供时间轴） |
| E_sca_unit_normalized | complex \| float | 已在外层完成角谱收集和归一化的复场代理 |
| optical | OpticalSystem | 光学系统 |
| illumination | dict | 照明包络（提供 `A_env / phi_beam_rad / phi_beam_gouy_rad / phi_beam_curv_rad / E_env_complex`） |
| channel | Channel | 通道几何（传给 spatial_coupling_factor） |
| initial_x_m, initial_z_m | float | 粒子初始位置（没有轨迹数组时的后备值） |
| phase_model | str | 相位模型："constant"、"axial_path" 或 "relative_surrogate" |
| **coupling_model** | **str** | **空间耦合模式参数** |
| path_opd_model | str | `z` 向路径差相对 reference surrogate plane 的定义："single_pass"`、`"reference_plane_roundtrip_surrogate"` 或 `"wall_referenced_gap_surrogate"` |
| detection_theta_rad | float \| None | 当前 case 的等效检测角 |
| medium_refractive_index | float | 当前波长下介质折射率 |
| reference_phase_rad | float \| ndarray | 参考场相位；既可传 case 级标量，也可传 event 级 `phi_ref(t)` 数组，用于显式输出 `Δφ = phi_sca - phi_ref` |

注意 `E_sca_unit_normalized` 现在可以是**复标量代理**而非纯正实数。时间依赖性仍主要来自 `E_env_complex(t)`，但材料散射相位、beam phase 和角谱投影相位都可被分层保留。

`scattering_phase_diagnostics` 是这一轮新增的审计入口。它允许把 case 级收集算子已经得到的相位诊断继续传入事件层，包括：

- `phi_sca_material_rad`
- `phi_sca_material_parallel_rad`
- `phi_sca_material_perpendicular_rad`
- `phi_projection_rad`

这样 `compute_scattering_field_trace(...)` 不再只输出“合成后的 `phi_sca`”，而是能把“材料相位”和“投影后进入干涉的相位”显式拆开。

这一轮 illumination 端也进入了同一偏振语义，因此 `E_env_complex` 不再总是纯标量包络。
如果 `illumination_polarization_mode` 与当前散射主通道交叉，照明幅度会先被压低，
然后再进入 `E_sca(t)` 的构造。

当前 `export_full_diagnostics=False` 的 event-block light 路径可能不会传
`E_env_complex`、`beam_inverse_wavefront_radius_m_inv` 或强度数组。`compute_scattering_field_trace(...)`
会用 `A_env * exp(i phi_beam_rad)` 按需恢复复包络，并对缺失的
`phi_beam_gouy_rad / phi_beam_curv_rad` 使用零数组 fallback；这只影响诊断数组的构造方式，
不改变进入信号链的 `A_env / phi_beam_rad`。

`coupling_model` 由 `sim_cfg.coupling_model` 传入，通过 `simulate_one_event` 传递。

#### 输出

```python
{
    "E_sca_complex": ndarray,   # 复数数组，shape = (n_samples,)
    "A_sca": ndarray,           # 实数幅值数组
    "phi_sca_rad": ndarray,     # 相位数组
    "phi_material_rad": ndarray,# 当前主投影通道对应的材料散射相位
    "phi_projection_rad": ndarray,# 当前探测算子压缩后的投影相位
    "phi_material_parallel_rad": ndarray,# arg(S2/k_m) 显式诊断
    "phi_material_perpendicular_rad": ndarray,# arg(S1/k_m) 显式诊断
    "phi_beam_rad": ndarray,    # 复照明包络带来的 beam phase
    "phi_beam_gouy_rad": ndarray,# beam phase 中的 Gouy-like 穿焦项
    "phi_beam_curv_rad": ndarray,# beam phase 中的波前曲率项
    "phi_focus_crossing_rad": ndarray,# scattering-side focus-crossing surrogate
    "phi_gouy_ref_rad": ndarray,# reference trace 中实际进入 E_ref 的 Gouy 贡献；当前为 0
    "phi_gouy_sca_rad": ndarray,# scattering trace 中实际进入 E_sca 的 y 向相位贡献：
                                 #   relative_surrogate → phi_focus_crossing（去重后）
                                 #   constant/axial_path → phi_beam_gouy + phi_focus_crossing
    "delta_phi_gouy_rad": ndarray,# 显式差分 Gouy = phi_gouy_sca - phi_gouy_ref
    "gouy_dedup_active": bool,   # True 当 phase_model=="relative_surrogate"（去重已生效）
    "phi_gouy_reference_status": str,# 当前 reference 是否真的携带 Gouy 贡献
    "phi_gouy_scattering_status": str,# 当前 scattering 侧使用哪一种 y 相位口径
    "phi_gouy_semantics_status": str,# 审计字段语义 = active_interference_contribution_fields
    "phi_ref_rad": ndarray,     # 参考场相位（显式对齐到同一时间轴）
    "phi_sca_path_x_rad": ndarray,# x 向路径差项
    "phi_sca_path_z_rad": ndarray,# z 向路径差项（语义由 path_opd_model 冻结）
    "phi_sca_path_rad": ndarray,# 散射侧路径/穿焦 surrogate 相位
    "path_opd_model": str,      # 当前 z 向 OPD surrogate 口径
    "path_opd_reference_plane": str,# 当前 reference plane surrogate 命名
    "path_opd_z_geometry_factor": float,# z 向几何因子（1 或 2）
    "path_opd_z_reference_mode": str,# z 向项到底按哪种 reference-plane 语义解释
    "path_opd_default_model": str,# 当前冻结的默认 OPD 主线
    "path_opd_model_role": str, # default_frozen_mainline 或 diagnostic_review_alternative
    "path_opd_default_frozen": bool,# 当前口径是否就是默认冻结主线
    "path_opd_freeze_status": str,# default_frozen_active 或 alternative_review_mode
    "delta_phi_ref_rad": ndarray,# 显式相对参考场相位
    "f_coupling": ndarray|float,# 当前使用的耦合因子
    "illumination_polarization_effective_mode": str,
    "illumination_polarization_amplitude_factor": float,
    "illumination_polarization_alignment_status": str,
}
```

这几组量的关系可以理解成：

- `phi_material_*`
  是 case 级 Mie 复振幅在选定偏振通道上的“材料本征相位”
- `phi_projection_rad`
  是经过有限角收集与偏振投影后，真正送进干涉层的相位
- `phi_beam_gouy_rad + phi_beam_curv_rad + phi_sca_path_rad`
  是事件内随轨迹变化的 beam / path surrogate 相位
- `phi_sca_rad`
  是上述相位加总后的总散射相位

---

## 相位模型

### constant
```
φ(t) = 0
```
所有时刻散射场同相。

### axial_path
```
φ(t) = g_z · k_m · (z(t) - z_focus) · cos(theta_det)
```

这是一个深度相关的 surrogate path-difference 模型。它不是严格的全波相位解，但能反映：
- 粒子位于不同深度时，和参考场的相对相位不同
- 开启扩散后，粒子在事件内的相位条件也会随时间变化
- 其中 `g_z` 与下方 `relative_surrogate` 相同，也由 `path_opd_model` 冻结

### relative_surrogate
```
φ_extra(t) =
    k_m · (x(t) - x_focus) · sin(theta_det)
  + k_m · (z(t) - z_focus) · cos(theta_det)
  + φ_focus_crossing(t)
```

其中：

- `z_R,eff = π · n_m · w_eff² / λ`
- `w_eff = sqrt(w_x · w_z)`
- `φ_focus_crossing(t) = arctan((y(t)-y_focus)/z_R,eff)`

这不是严格的矢量成像 Gouy 相位，而是一个更接近”相对相位”结构的 surrogate：既保留深度路径差，又保留沿流动方向穿焦时的相位趋势，所以当前文档和代码都改用 `focus-crossing` 命名，而不再把它直接叫 Gouy 相位。

#### ⚠️ Gouy 相位去重（2026-04-12 修正）

`illumination.py` 输出的 `phi_beam` 包含两项：

```
phi_beam = phi_gouy_surrogate + phi_curv
         = arctan((y - y_f) / z_R)  +  ½ · k · r² / R(y)
```

其中 `phi_gouy_surrogate = arctan((y-y_f)/z_R)` 与上方 `phi_focus_crossing` 的公式**完全相同**。若在 `relative_surrogate` 模式下直接使用完整 `phi_beam`，则 `arctan` 项会被叠加两次，Gouy 相位幅度虚增 2×。

**修正方案（Option B）：** 在 `relative_surrogate` 模式下，`phi_sca_unwrapped` 仅使用 `phi_beam_curv`（曲率项），不含 `phi_beam_gouy`：

```python
# relative_surrogate 模式（_gouy_dedup_active = True）：
phi_sca_unwrapped = phi_beam_curv + unit_phase + phi_extra
#                 = phi_curv + unit_phase + (phi_path_x + phi_path_z + phi_focus_crossing)

# constant / axial_path 模式（phi_focus_crossing = 0）：
phi_sca_unwrapped = phi_beam + unit_phase + phi_extra
#                 = (phi_gouy + phi_curv) + unit_phase + phi_path_z
```

**数值验证（λ=660 nm, NA_ill=0.45, n=1.33）：**

| 指标 | 修正前 | 修正后 |
|------|--------|--------|
| FWHM 内相位摆幅 | 33.4° | 16.7° |
| 全轨迹相位摆幅 | 165.7° = 0.92π | 82.9° = 0.46π |
| 峰值 NODI 信号（外泌体）| 0.33 | 0.18 |
| 零交叉次数 | 1 次 | 1 次（拓扑不变）|

本轮又补了最小二维路径差，也就是在 `z` 向路径差之外，再显式加入
`x` 向投影项。当前假设探测方向位于 `x-z` 平面内，因此：

- `phi_sca_path_x_rad = k_m · (x-x_focus) · sin(theta_det)`
- `phi_sca_path_z_rad = g_z · k_m · (z-z_focus) · cos(theta_det)`

其中 `path_opd_model` 现在有三条显式语义：

- `single_pass`：`g_z = 1`，reference plane 解释为 `detector_projection_single_pass_surrogate`
- `reference_plane_roundtrip_surrogate`：`g_z = 2`，reference plane 解释为 `channel_center_reference_plane_roundtrip_surrogate`
- `wall_referenced_gap_surrogate`：`phi_sca_path_z = -k_m · |z| · cos(theta_det)`，reference plane 解释为 `nearest_channel_wall_centered_gap_surrogate`，并通过 `path_opd_z_reference_mode = nearest_wall_gap_centered_about_channel_midplane` 显式标记这不是简单的 `g_z` 乘法

当前这条 OPD 主线又往前收口了一步：默认冻结口径已经显式固定在
`single_pass`。因此除了 `path_opd_model / path_opd_reference_plane /
path_opd_z_geometry_factor` 之外，本模块现在还会同步导出：

- `path_opd_z_reference_mode`
- `path_opd_default_model = "single_pass"`
- `path_opd_model_role = "default_frozen_mainline" | "diagnostic_review_alternative"`
- `path_opd_default_frozen`
- `path_opd_freeze_status = "default_frozen_active" | "alternative_review_mode"`

本轮还把差分 Gouy 审计显式拆出来了：

- `phi_focus_crossing_rad` = arctan(y/z_R)，由 `_surrogate_focus_crossing_phase()` 计算
- `phi_beam_gouy_rad` 继续保留为 illumination 侧审计量
- `phi_gouy_ref_rad = 0`
  因为当前 `compute_reference_field_trace()` 的 `E_ref_trace_complex` 只携带
  `phi_ref_base + spatial_phase`，并不会把 `phi_beam_gouy` 乘进 reference trace
- `phi_gouy_sca_rad`（active 语义）：
  - `relative_surrogate` 模式 → `phi_focus_crossing_rad`
  - 其它模式 → `phi_beam_gouy_rad + phi_focus_crossing_rad`
- `delta_phi_gouy_rad = phi_gouy_sca_rad - phi_gouy_ref_rad`
- `gouy_dedup_active = (phase_model == "relative_surrogate")`
- `phi_gouy_reference_status = inactive_not_carried_by_reference_trace`
- `phi_gouy_scattering_status = active_focus_crossing_only_deduplicated | active_beam_gouy_component`
- `phi_gouy_semantics_status = active_interference_contribution_fields`

**2026-04-12 去重修正**：在此之前 `phi_gouy_sca_rad = phi_beam_gouy + phi_focus_crossing`，
这两项公式相同，等价于双倍 arctan，使 Gouy 相位幅度虚增 2×。
修正后 `relative_surrogate` 模式下信号路径只保留一个 arctan，
但诊断字段 `phi_beam_gouy_rad` 仍然输出，可作为照明侧审计量。

这仍然不是全波传播求解，但至少不再把宽度方向的位置变化只留给
amplitude/coupling 去表达。

需要特别注意：

- `phi_ref` 仍然由 `reference_field.py` 的 `E_ref_complex / E_ref_trace_complex`
  在干涉层体现
- 本模块不会把 `phi_ref` 重复乘进散射场
- 但现在会显式输出：
  - `phi_material_rad`
  - `phi_projection_rad`
  - `phi_ref_rad`
  - `phi_sca_path_x_rad`
  - `phi_sca_path_z_rad`
  - `phi_sca_path_rad`
  - `path_opd_model`
  - `path_opd_reference_plane`
  - `path_opd_z_geometry_factor`
  - `path_opd_z_reference_mode`
  - `path_opd_default_model`
  - `path_opd_model_role`
  - `path_opd_default_frozen`
  - `path_opd_freeze_status`
  - `phi_focus_crossing_rad`
  - `phi_gouy_ref_rad`
  - `phi_gouy_sca_rad`
  - `delta_phi_gouy_rad`
  - `delta_phi_ref_rad = phi_sca_rad - phi_ref_rad`

也就是说，相对相位已经不再只是“文档里的概念”，而是事件级可导出的分析量；并且可以继续区分“材料相位”和“投影相位”。

### linear_y（预留，未实现）
```
φ(t) = φ₀ + k_eff · y(t)
```

---

## 在流水线中的位置

```
intrinsic_scattering → 插值+归一化 → E_sca_unit_normalized（复标量代理）
illumination → A_env(t)（数组）
sim_cfg.coupling_model ─┐
        │               │         │
        ▼               ▼         ▼
   compute_scattering_field_trace
                │
                ▼ E_sca_complex(t)
   generate_interferometric_trace
```
