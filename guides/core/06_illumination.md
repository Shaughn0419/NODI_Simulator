# illumination.py — 激光照明包络模块


<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

## 文件职责

计算粒子在每个位置上受到的激光照明强度、实数场包络，以及最小复高斯包络 surrogate。当粒子沿轨迹运动时，它在不同位置接收到不同强度的入射光，这决定了散射信号的时间包络形状；同时焦区附近的 beam phase 也会给 `E_sca(t)` 额外带来一层可审计的相位来源。

---

## 【2026-04 新增】照明模式（illumination_mode）

### 背景与物理原因

NODI 实验中存在两种截然不同的照明策略，对检测率有显著影响：

#### 模式 A：`tight_focus`（紧聚焦，旧默认）

- 照明物镜 NA 较高，束腰尺寸 ≪ 通道宽度
- 粒子横向位置决定了它接收到的照明强度
- 通道边缘粒子：`A_env ≈ exp(-(W/2/w)²)`；当 w=300 nm, W=700 nm 时，A_env ≈ 0.26
- 信号幅度严重依赖粒子位置，边缘粒子的散射信号被压低约 74%

#### 模式 B：`overfill`（过填充，Tsuyama 2022 实验方法）

- Tsuyama et al. 2022 使用 NA=0.45 照明物镜，产生约 2 μm 光斑
- 光斑尺寸远大于 800 nm 通道宽度（约 2.5× 倍）
- **所有粒子均通过激光斑中心附近** → A_env ≈ 1.0（均匀）
- 论文原文："*all nanoparticles pass through near the center of the laser spot, ensuring almost the same laser illumination for all nanoparticles*"

#### 两种模式对检测率的影响

| 波长 | tight_focus 边缘 A_env | overfill A_env | 检测率差异（估算） |
|------|----------------------|---------------|-----------------|
| 404 nm | ~0.26（w=300 nm, W=700 nm）| ~1.0 | +15~20 pp |
| 488 nm | ~0.26 | ~1.0 | +12~18 pp |
| 532 nm | ~0.26 | ~1.0 | +10~15 pp |
| 660 nm | ~0.26 | ~1.0 | 受 NA 截止主导 |

注：pp = percentage points（百分点）。

**仿真–实验系统性偏差的主要来源之一**：之前代码默认使用 300 nm 束腰（< 通道宽度）建模，相当于 tight_focus 模式，导致仿真检测率比 Tsuyama 2022 实验结果系统性低估 10~20 pp。

#### 代码实现

在 `compute_illumination_envelope()` 中，在高斯包络计算之后、强度计算之前加入分支：

```python
# illumination.py
_active_illumination_mode = (
    sim_cfg.illumination_mode if sim_cfg is not None else "tight_focus"
)
if _active_illumination_mode == "overfill":
    A_env_scalar = np.ones_like(A_env_scalar, dtype=float)
```

`SimulationConfig` 中新增字段：

```python
# data_objects.py → SimulationConfig
illumination_mode: str = "overfill"  # "overfill" 或 "tight_focus"
```

**默认值设为 `"overfill"`**，以匹配 Tsuyama 2022 实验条件（修正后默认即可复现实验）。旧行为（紧聚焦）需显式设置 `illumination_mode = "tight_focus"`。

#### beam phase 在 overfill 模式下的处理

`overfill` 模式只将 `A_env_scalar` 设为全 1，beam phase（Gouy 相位和波前曲率项）计算逻辑**不改变**。原因：

1. 在 overfill 实验中，粒子穿越焦点的 Gouy 相位贡献比粒子自身散射相位小得多
2. 保留 beam phase 计算逻辑便于后续需要时恢复 tight_focus 模式的完整行为

#### 与 `coupling_model` 的关系

- `coupling_model = "constant"`（SimulationConfig 字段）：空间耦合因子恒为 1.0，不随位置变化
- `illumination_mode = "overfill"`：照明包络恒为 1.0

两者相辅相成，共同实现"所有粒子位置等效"。在 Tsuyama 2022 实验条件下，这两个参数均应使用 `constant/overfill`。

#### 引用与依据

- Tsuyama et al. 2022, *Microfluidics and Nanofluidics* — 照明方法说明（NA=0.45 照明物镜，2 μm 光斑）
- 工程文件 `41_实验对齐原则与计算修正备忘.md` Principle 2（照明均匀性对比表）
- 工程文件 `25_核心计算逻辑与公式总说明.md` § 19.9（已修正状态）

---

## 核心物理

激光聚焦后的强度分布近似为 3D 高斯：

```
I_inc(x,y,z) = I₀ · exp[-2(x-x_f)²/w_x² - 2(y-y_f)²/w_y² - 2(z-z_f)²/w_z²]
```

其中 I₀ 是焦点处的峰值强度，w_x, w_y, w_z 是三个方向的 1/e² beam waist 半径。

**场包络**的定义：

```
A_env = √(I_inc / I₀)
      = exp[-(x-x_f)²/w_x² - (y-y_f)²/w_y² - (z-z_f)²/w_z²]
```

注意指数系数从 -2 变成了 -1（因为取了平方根）。

**为什么要定义场包络而不只用强度？** 因为后续需要把局部照明效果乘到散射**场**振幅上（E_sca = A_env · E_sca_unit），而不是直接乘到强度上。场是振幅级别的量，强度是振幅平方。如果直接用 I_inc 乘 E_sca_unit，物理量纲会出错。

---

## 函数

### `compute_illumination_envelope(x_m, y_m, z_m, optical, medium_refractive_index=1.0, sim_cfg=None) → dict`

#### 输入

- `x_m, y_m, z_m`：粒子轨迹上每个时刻的位置坐标（numpy 数组）
- `optical`：光学系统（提供 beam waist、焦点坐标、I₀）
- `medium_refractive_index`：beam-phase surrogate 使用的介质折射率
- `sim_cfg`：可选。提供当前散射主通道和照明偏振设置；若不传，则退化回旧的纯标量照明行为

#### 内部实现

先算未投影的标量包络 `A_env_scalar`（指数系数为 -1），再由它算
`I_inc_scalar = I₀ · A_env_scalar²`：

```python
exponent = -(x-xf)²/wx² - (y-yf)²/wy² - (z-zf)²/wz²
A_env_scalar = exp(exponent)
I_inc_scalar = I₀ · A_env_scalar²
```

这样做数值上更稳定（避免直接计算 exp(-2·...)再开方）。

当前 beam phase 也不再只是一条未拆解的 `phi_beam_rad`。代码已经把它显式写成：

```python
z_rayleigh = π · n_medium · w_eff² / λ
w_eff = sqrt(w_x · w_z)
phi_beam_gouy = arctan((y-y_f) / z_rayleigh)
1 / R_eff(y) = (y-y_f) / ((y-y_f)² + z_rayleigh²)
phi_beam_curv = 0.5 · k_medium · ((x-x_f)² + (z-z_f)²) · (1 / R_eff)
phi_beam = phi_beam_gouy + phi_beam_curv
```

这里的 `phi_beam_curv` 是最小 Gaussian-wavefront surrogate，而不是完整矢量高斯光束求解；但它现在已经满足一个重要边界：

- 当 `y = y_f` 时，`1 / R_eff = 0`
- 因而焦点处 `phi_beam_curv = 0`

也就是说，焦点附近的额外 beam 相位不会再被“曲率项假信号”污染。

如果传入了 `sim_cfg`，当前实现还会按最小统一偏振框架，再乘一个常数幅度因子：

- 同偏振：`illumination_polarization_amplitude_factor = 1`
- `unpolarized`：按单通道等分，幅度因子 `sqrt(1/2)`
- 交叉偏振：按 `cross_polarization_leakage` 压低

于是真正送进散射链的是：

`A_env = A_env_scalar · illumination_polarization_amplitude_factor`

#### 输出

```python
{
    "I_inc_W_m2": ndarray,   # 局部照明强度，shape = (n_samples,)
    "I_inc_scalar_W_m2": ndarray,  # 偏振投影前的标量强度
    "A_env": ndarray,         # 场包络，值域 [0, 1]
    "A_env_scalar": ndarray,  # 偏振投影前的标量场包络
    "phi_beam_rad": ndarray,  # 最小 beam-phase surrogate（= gouy + curv 之和）
    "phi_beam_gouy_rad": ndarray,  # Gouy-like 穿焦项
    "phi_beam_curv_rad": ndarray,  # 波前曲率 surrogate
    "beam_rayleigh_range_m": float,  # 近似 Rayleigh 长度
    "beam_inverse_wavefront_radius_m_inv": ndarray,  # 1 / R_eff(y)
    "E_env_complex": ndarray, # 复场包络，满足 |E_env_complex| = A_env
    "illumination_polarization_effective_mode": str,
    "illumination_polarization_amplitude_factor": float,
    "illumination_polarization_alignment_status": str,
    "illumination_projection_basis": str,
    "illumination_effective_basis": str,
    "illumination_projection_basis_match": bool,
    "illumination_projection_coupling_status": str,
}
```

当调用方传 `export_full_diagnostics=False` 时，当前实现只返回 event block 信号生成和 summary 所需字段：

- `A_env`
- `A_env_scalar`
- `phi_beam_rad`
- `phi_beam_gouy_rad`
- `phi_beam_curv_rad`
- beam waist / Rayleigh range / illumination provenance
- polarization / projection diagnostics

此时会省略 `I_inc_W_m2`、`I_inc_scalar_W_m2`、`E_env_complex` 和
`beam_inverse_wavefront_radius_m_inv`。这些数组只服务完整诊断导出，不参与
`event_block_v3` 的 light signal path。

当前还有一个 2D light kernel：当 `x_m / y_m / z_m` 是同 shape 的 2D event block
数组、`export_full_diagnostics=False` 且 `numba` 可用时，`compute_illumination_envelope`
会走 `_illumination_light_2d_kernel`。该路径用于预计算热循环，已用测试锁定
`A_env / A_env_scalar / phi_beam_*` 与 full diagnostics 的一致性。

#### 关键性质

- 焦点处：A_env = 1.0，I_inc = I₀（`tight_focus` 模式）
- `overfill` 模式：全轨迹 A_env = 1.0（均匀照明）
- 距焦点越远：A_env 单调递减（仅 `tight_focus` 模式）
- 恒等关系：A_env² · I₀ == I_inc（数值误差 < 1e-12）
- A_env 值域：`tight_focus` 时严格在 [0, 1]；`overfill` 时恒为 1.0
- `|E_env_complex| == A_env`
- `phi_beam_rad` 在穿焦过程中会平滑变化，用于把 beam phase 从附加相位项里拆出来
- `phi_beam_gouy_rad` 与 `phi_beam_curv_rad` 已分开导出，便于审查”穿焦项”和”曲率项”分别贡献了多少相位
- 焦点处即使粒子有横向偏移，`phi_beam_curv_rad` 也应趋近 0；只有离焦且离轴时，曲率项才逐步显现
- illumination 端现在还会显式告诉你当前是不是仍与散射主通道共用同一 detector basis，而不只剩一个 `matched / cross_suppressed` 文本

**注意**：在 `overfill` 模式下，`A_env` 全 1，但 `phi_beam_rad`（Gouy 相位和曲率项）仍正常计算，保留完整的 beam phase surrogate。

---

## 在流水线中的位置

```
trajectory → (x(t), y(t), z(t))
                 │
                 ▼
compute_illumination_envelope
                 │
                 ▼ A_env(t), phi_beam(t), E_env_complex(t)
compute_scattering_field_trace：E_sca(t) = E_env_complex(t) · E_sca_unit_normalized · e^{iφ_extra}
```

A_env(t) 本质上决定了脉冲的**形状**：当粒子穿过焦点时 A_env 先升后降，形成一个类高斯的时间包络。脉冲的宽度大致等于 beam_waist_y / velocity。
