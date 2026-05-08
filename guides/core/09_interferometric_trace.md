# interferometric_trace.py — 干涉信号生成模块

## 文件职责

这是整个 NODI 模拟器的**核心模块**。它将参考场 E_ref 与散射场 E_sca(t) 叠加，产生干涉检测信号。NODI 的检测灵敏度就来自这一步的干涉增强效应。

---

## 核心物理

### 场叠加

```
E_det(t) = E_ref(t) + E_sca(t)
```

当前实现里：

- 旧模式下 `E_ref` 仍可退化为标量复数
- 启用 `reference_spatial_mode="cross_section_surrogate"` 后，
  `E_ref` 会变成 event 级时间序列 `E_ref_trace_complex(t)`
- 交叉项当前还会并排保留两条语义：
  - `joint_overlap_integrated`
  - `collapsed_then_multiplied`

### 探测强度

```
I_det(t) = |E_det(t)|² = E_det(t) · E_det*(t)
```

### 展开

```
I_det(t) = |E_ref(t)|² + |E_sca(t)|² + 2·Re(E_ref(t) · E_sca*(t))
```

三项的物理含义：
- `|E_ref(t)|²`：参考场背景强度（当前可以是时变）
- `|E_sca(t)|²`：纯散射强度（极弱，在弱散射极限下可忽略）
- `2·Re(E_ref · E_sca*(t))`：**干涉交叉项**（NODI 灵敏度的来源）

### 当前交叉项的两条实现

当前代码会同时计算：

```python
cross_collapsed(t) = 2 Re(E_ref(t) · E_sca*(t))
cross_joint(t) = 2 Re(overlap_factor · E_ref(t) · E_sca*(t))
```

其中 `overlap_factor` 来自上游的角谱联合 overlap 审计。

因此当前工程的语义是：

- 默认使用 `cross_joint`
- 同时把 `cross_collapsed` 和 `overlap_factor` 一起导出，作为 legacy 对照与 freeze 审计依据

### 基线扣除

```
I_baseline(t) = |E_ref(t)|²
signal_trace(t) = I_det(t) - I_baseline(t)
               = |E_sca|² + 2·Re(E_ref(t) · E_sca*)
```

### 弱散射极限

当 |E_sca| ≪ |E_ref| 时：
```
signal_trace(t) ≈ 2·Re(E_ref · E_sca*(t))
```

这就是为什么 NODI 能检测极弱散射的粒子：干涉项将 E_sca 的幅值线性放大了 2|E_ref| 倍。

### 数值例子

以默认参数为例：
- E_ref = ρ = 0.5（A.U.）
- E_sca_peak = A_env_max · E_sca_unit_normalized = 1.0 · 1.0 = 1.0（A.U.）
- signal_trace_peak ≈ 2 × 0.5 × 1.0 + 1.0² = 2（A.U.）
- 纯散射信号 = |E_sca|² = 1.0（A.U.）
- **干涉增强比 = 2 / 1 = 2 倍**

---

## 函数

### `generate_interferometric_trace(trajectory, reference, scattering_trace, sim_cfg) → dict`

#### 输入

| 参数 | 来源 | 说明 |
|------|------|------|
| trajectory | trajectory 模块 | 提供 time_s |
| reference | reference_field 模块 | 提供 `E_ref_complex`，以及可选的 `E_ref_trace_complex` |
| scattering_trace | scattering_trace 模块 | 提供 E_sca_complex(t) |
| sim_cfg | data_objects | 模拟配置 |

#### 内部计算

```python
E_det = E_ref + E_sca                     # 场叠加
I_det = (E_det * conj(E_det)).real        # 强度
I_baseline_trace = |E_ref(t)|²            # 每个采样点的背景
I_baseline = mean(I_baseline_trace)       # 标量摘要，保留旧接口兼容
signal_trace = I_det - I_baseline_trace   # 基线扣除后的信号
```

#### 输出

```python
{
    "time_s": ndarray,
    "E_ref_complex": ndarray,
    "E_det_complex": ndarray,
    "I_det": ndarray,
    "I_baseline": float,
    "I_baseline_trace": ndarray,
    "signal_trace": ndarray,
    "scattering_only_intensity": ndarray,
    "interference_cross_term": ndarray,
    "interference_cross_term_collapsed": ndarray,
    "interference_cross_term_joint": ndarray,
    "interference_cross_term_mode": str,
    "interference_overlap_factor_complex": complex,
    "interference_overlap_factor_abs": float,
    "interference_overlap_factor_phase_rad": float,
    "interference_overlap_status": str,
}
```

注意：

- 当 `interference_overlap_mode="joint_overlap_integrated"` 时，`signal_trace`
  当前走 joint 交叉项，这已经是基础包默认主线
- 当 `interference_overlap_mode="collapsed_then_multiplied"` 时，`signal_trace`
  会回到 legacy collapsed 口径；该模式现在主要用于对照与审计，而不是默认结果冻结主线

---

## 验证要点

| 测试条件 | 预期结果 |
|----------|----------|
| E_sca = 0 | signal_trace = 0 |
| E_ref = 0 | signal_trace = \|E_sca\|² |
| 弱散射 | signal_trace ≈ 2·Re(E_ref·E_sca*) |
| 恒等关系 | signal_trace == I_det - I_baseline_trace（精确） |
| I_det ≥ 0 | 始终成立（强度不能为负） |

---

## 在流水线中的位置

```
reference_field → E_ref（标量）/ E_ref(t)（数组）
scattering_trace → E_sca(t)（数组）
        │                │
        ▼                ▼
generate_interferometric_trace
        │
        ▼ signal_trace(t)
add_detector_noise → estimate_threshold → extract_pulse_features
```
