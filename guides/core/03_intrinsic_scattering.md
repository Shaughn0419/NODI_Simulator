# intrinsic_scattering.py — 粒子本征散射模块


<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

## 文件职责

计算粒子的本征光学响应：散射截面、微分散射截面、场幅值。

**核心设计原则**：本模块是**纯物理层**——只计算粒子本征量，不做任何与检测系统、通道几何或归一化相关的操作。归一化放在外层（`run_single_case_batch`）完成。

---

## 函数

### `compute_intrinsic_scattering(particle, medium, wavelength_m, theta_grid_rad) → dict`

#### 计算步骤

**步骤 1：获取材料光学常数**
```python
n_p = particle.n_complex_at(wavelength_m)      # 波长依赖（或固定值）
n_m = medium.refractive_index_at(wavelength_m)  # 波长依赖（或固定值）
```

`n_complex_at()` 和 `refractive_index_at()` 支持波长依赖的材料模型；当 `use_material_model=False` 时，返回固定常数（legacy 兼容行为）。

**步骤 2：基本量**
```
k = 2π · n_m / λ₀          （介质中的波数）
x = k · a                   （尺寸参数）
m = ñ_p / n_m               （相对复折射率）
```

**步骤 3：调用 Mie 引擎**

调用 `mie_compute(x, m)` 得到 Qext、Qsca；调用 `mie_angular(x, m, theta_grid)` 得到 S1(θ)、S2(θ)。

**步骤 4：截面计算**
```
Csca = Qsca · π · a²
Cext = Qext · π · a²
Cabs = Cext - Csca
```

**步骤 5：微分散射截面**

对非偏振入射光，取两个偏振分量的平均：
```
dCsca/dΩ(θ) = (|S1(θ)|² + |S2(θ)|²) / (2 · k²)
```

量纲为 m²/sr。

**步骤 6：场幅值**
```
Esca_unit_amp(θ) = √(dCsca/dΩ(θ))
```

#### 输出字典

| 键 | 类型 | 说明 |
|----|------|------|
| k_m | float | 波数 k (1/m)，canonical key |
| k_m_inv | float | deprecated legacy alias，仍等于 k_m，不是 1/k_m |
| size_parameter | float | 尺寸参数 x = ka |
| relative_index | complex | 相对折射率 m |
| Csca_m2 | float | 散射截面 (m²) |
| Cext_m2 | float | 消光截面 (m²) |
| Cabs_m2 | float | 吸收截面 (m²) |
| dCsca_dOmega_m2_sr | ndarray | 微分散射截面，与 theta_grid 对应 |
| theta_grid_rad | ndarray | 角度网格（原样返回，供下游插值） |
| Esca_unit_amp | ndarray | √(dCsca/dΩ)，**未归一化** |
| S1_complex | ndarray | Mie 振幅函数 S1(θ)，复数 |
| S2_complex | ndarray | Mie 振幅函数 S2(θ)，复数 |

**S1/S2 的用途**：为后续偏振分析、角窗口积分预留。当前不直接使用，但计算过程中已经产生，额外输出成本为零。

**关键设计点**：输出中没有 `Esca_unit_amp_normalized`。归一化在外层通过 `interpolate_at_theta` + `/ E_sca_ref` 完成。这使得本模块完全独立于检测系统配置。

---

## 数据流位置

```
materials.py → n_p, n_m
                  ↓
本模块输出 → interpolate_at_theta(θ_det) → ÷ E_sca_ref → scattering_trace 模块
```

本模块处于流水线最上游，其输出既用于 baseline normalization（计算 E_sca_ref），也用于每个扫描 case 的实际计算。两者走同一条路径确保一致性。

---

## 带来的物理效果

启用材料模型后，gold 在不同波长下的 Csca 不再相同：

| 波长 | n_p (gold) | Csca |
|------|-----------|------|
| 488nm | 0.668 + 1.586i | ~1.11e-16 m² |
| 532nm | 0.320 + 1.564i | ~1.68e-16 m² |
| 660nm | 0.164 + 2.470i | ~1.58e-16 m² |

532nm 附近散射最强，因为接近金的等离子体共振频率。这个趋势与文献一致。
