# nodi_simulator/trajectory.py — 粒子轨迹模块

## 文件职责

生成单个粒子穿过检测区的时空轨迹。轨迹决定了粒子在每个时刻的位置 (x(t), y(t), z(t))，进而决定了照明包络和散射信号的时间变化。

---

## 坐标约定

- **y**：流动方向（粒子沿 y 轴运动）
- **x**：通道宽度方向，范围 [-W/2, W/2]
- **z**：通道深度方向，范围 [-H/2, H/2]

---

## 函数

### 关于初始位置采样的边界

真正的初始 `(x0, z0)` 采样实现放在 [04_utils.md](./04_utils.md)
对应的 `sample_initial_position(...)` 中，但它和轨迹层属于同一条输运链，所以这里把边界一起写清：

- 轨迹积分只负责“给定起点后如何随时间演化”
- 起点当前可以来自：
  - `initial_position_distribution_mode="uniform"`
  - `initial_position_distribution_mode="uniform_accessible_area"`
  - `initial_position_distribution_mode="center_biased_surrogate"`
  - `initial_position_distribution_mode="flux_weighted"`
- `electrostatic_equilibrium` / `measured_cross_section_distribution` 仍只是 schema-reserved future lane，当前会被 `SimulationConfig` 拒绝
- `center_biased_surrogate` 和 `flux_weighted` 只改变初始截面占据分布，不会直接篡改
  `simulate_particle_trajectory(...)` 的扩散、反射边界或流速公式

### `_reflect(val, lo, hi) → float`

将 val 反射回 [lo, hi] 区间。使用迭代反射处理极端情况（粒子在单步内多次越界）。

```python
while val < lo or val > hi:
    if val < lo: val = 2·lo - val
    if val > hi: val = 2·hi - val
```

### `simulate_particle_trajectory(channel, optical, sim_cfg, initial_x_m, initial_z_m, particle_radius_m=0.0, diffusion_coefficient=None, rng=None) → dict`

#### 输入

| 参数 | 类型 | 说明 |
|------|------|------|
| channel | Channel | 通道几何（验证 + 反射边界） |
| optical | OpticalSystem | 提供 beam_waist_y_m、focus_y_m |
| sim_cfg | SimulationConfig | 提供 velocity、timing、include_diffusion、reflecting_boundary |
| initial_x_m | float | 初始 x 位置 |
| initial_z_m | float | 初始 z 位置 |
| particle_radius_m | float | 粒子半径。用于可达区域边界和近壁受限扩散 |
| **diffusion_coefficient** | **float \| None** | **Stokes-Einstein D (m²/s)** |
| **rng** | **Generator \| None** | **随机数生成器。扩散模式必需** |

#### 内部逻辑

**输入验证**：当前先计算粒子中心的可达区域：

`x ∈ [-(W/2-a), +(W/2-a)]`

`z ∈ [-(H/2-a), +(H/2-a)]`

再检查 `initial_x_m / initial_z_m` 是否落在可达区域内。这样不会再出现“粒子中心已经穿墙，但数值上还算在通道里”的乐观假设。

**时间网格**：
```python
dt = 1 / sampling_rate_Hz
n_samples = int(total_time_s × sampling_rate_Hz)
time_s = [0, dt, 2dt, ..., (n_samples-1)·dt]
```

**y 方向（流动）**：

当前支持三种流速口径：

- `flow_profile_model="plug"`：
  `v_y = mean_flow_velocity`
- `flow_profile_model="parabolic_rect"`：
  `v_y = mean_flow_velocity × 9/4 × (1-(x/half_w_acc)^2) × (1-(z/half_h_acc)^2)`
- `flow_profile_model="rect_series"`：
  用矩形截面 Poiseuille 级数解的截断 surrogate 近似局部流速，并重新归一化到可达截面的平均流速

后两种都用来表达：

- 中心流线更快
- 近壁流线更慢

`y_start` 会按初始位置上的局部流速设置，使粒子大致在时间窗中部经过焦点。

**x, z 方向 — 纯对流模式**（include_diffusion=False）：
```
x(t) = initial_x_m    （常数）
z(t) = initial_z_m    （常数）
```

**x, z 方向 — 布朗扩散模式**（include_diffusion=True）：
```
Δx_i = √(2D·dt) · ξ_x     ξ_x ~ N(0,1)
Δz_i = √(2D·dt) · ξ_z     ξ_z ~ N(0,1)

x_{i+1} = x_i + Δx_i → 反射回 [-(W/2-a), +(W/2-a)]
z_{i+1} = z_i + Δz_i → 反射回 [-(H/2-a), +(H/2-a)]
```

- `diffusion_coefficient` 必须为正，否则抛出 ValueError
- 反射边界由 `sim_cfg.reflecting_boundary` 控制（默认 True）
- 若 `diffusion_hindrance_model="near_wall_surrogate"`，则本地扩散系数会再乘近壁抑制因子：
  `D_x,local = D × f_x(x,z)`
  `D_z,local = D × f_z(x,z)`
- 若 `diffusion_hindrance_model="anisotropic_tensor_surrogate"`，则会进一步区分
  平行壁面与垂直壁面的 mobility/diffusion surrogate，并把这种近壁抑制也轻量耦合到轴向输运速度
- 本轮 `near_wall_surrogate` 已从纯 gap 幂次推进成更明确的 Faxen-like `a/h` 依赖：
  先分别计算“沿壁平行”和“朝壁垂直”的单壁 mobility surrogate，再做一个较软的双壁混合
- `anisotropic_tensor_surrogate` 仍然比 `near_wall_surrogate` 更严格；
  它更接近“方向性 tensor product”语义，而不是软混合
- 当前 `f_z` 仍比 `f_x` 更容易被压低，用来表达深度方向受限扩散对相位和收集稳定性的更直接影响
- y 方向不直接做布朗扩散，但如果启用了 `parabolic_rect` 或 `rect_series`，随着 x/z 漂移，`v_y(t)` 会随时间变化

#### 输出

```python
{
    "time_s": ndarray,    # shape = (n_samples,)
    "x_m": ndarray,       # shape = (n_samples,)，扩散时不再是常数
    "y_m": ndarray,       # shape = (n_samples,)，线性增长
    "z_m": ndarray,       # shape = (n_samples,)，扩散时不再是常数
    "v_y_m_s": ndarray,   # shape = (n_samples,)，当前局部轴向流速
}
```

---

## 扩散系数的计算

扩散系数 D 不在 nodi_simulator/trajectory.py 内部计算，而是在 `nodi_simulator/parameter_sweep.py` 的 `simulate_one_event` 中通过 Stokes-Einstein 公式计算后传入：

```
D = kB·T / (6π·η·a)
```

其中 kB 为 Boltzmann 常数，T 为温度，η 为粘度，a 为粒子半径。

**重要限制**：当前仍然从自由空间 Stokes-Einstein `D` 出发；近壁效应虽然已推进到更明确的 Faxen-like `a/h` 依赖，但 `near_wall_surrogate` / `anisotropic_tensor_surrogate` 仍是紧凑代理，不是严格的受限扩散张量解。

**典型值**（gold 40nm, 水, 25°C）：
- D = 1.38e-23 × 298.15 / (6π × 1e-3 × 20e-9) ≈ 1.09e-11 m²/s
- √(2D·dt) ≈ √(2 × 1.09e-11 × 5e-5) ≈ 1.04e-7 m ≈ 104 nm/step
- 通道半宽 400 nm → 约 4 步随机游走跨越通道半宽

---

## 时间尺度估算

以默认参数为例：

- beam_waist_y = 700nm = 7e-7 m
- velocity = 0.2 mm/s = 2e-4 m/s
- transit_duration = 700e-9 / 2e-4 = 3.5 ms
- total_time = 0.2 s = 200 ms

脉冲约占总时间的 3.5/200 ≈ 1.75%。绝大部分时间是背景。

---

## 对信号的影响

启用扩散和更真实流速口径后：
- x(t) 和 z(t) 随时间随机游走，不再是常数
- y 方向局部流速也可能因 x/z 位置变化而改变
- 照明包络 A_env(t) 的形状不再是纯高斯，而是被扩散轨迹和局部流速共同调制
- 对于较小的粒子（D 更大），峰高分布和峰宽分布都会变宽
- 反射边界现在基于粒子中心可达区域，物理上比旧版更保守

---

## 运行时优化说明（2026-04-06）

当前代码已经为轨迹热路径加入了“标量快路径”，但**没有改变物理语义**：

- `simulate_particle_trajectory(...)` 的内层时间步循环现在优先走标量版本的
  `hindered_diffusion_factors` / `axial_transport_velocity_m_s`
- 对单粒子逐步推进这种场景，不再在每一步都重复经过
  `np.asarray / np.maximum / np.clip` 这类数组分支
- `rect_series` 轴向流速 surrogate 也补了标量级数版本，并在单条轨迹内缓存
  可达截面的 `mean_raw`
- 对固定 channel / radius 的单条轨迹，`half_w / half_h` 会在轨迹开始时解析一次，
  不再在每个时间步重复解析

这次优化的原则是：

- 数组输入仍保留原来的 NumPy 路径，方便批量分析和现有外部调用
- 标量输入走专门快路径，服务于当前最耗时的 event-level trajectory 积分
- 通过“标量输入 vs 单元素数组输入”一致性测试锁定数值语义

2026-04-26 后，precompute 的事件块主线还包含一个更窄的块级轨迹 kernel：

- 适用条件：`flow_profile_model="plug"`、`include_diffusion=True`、`diffusion_hindrance_model="none"`
- 用途：服务 `event_block_v3` 的批量事件路径
- 边界：保持 scalar event loop 的随机数消费顺序、反射边界语义和输出字段；不适用的流型或近壁抑制模型会走对应的通用路径

代表性 microbenchmark（同机、同配置、优化后）：

- `hindered_diffusion_factors`：约 `1.01s / 50k` → `0.07s / 50k`
- `axial_transport_velocity_m_s`：约 `1.02s / 30k` → `0.14s / 30k`
- `simulate_particle_trajectory`：约 `1.33s / 6 runs` → `0.21s / 6 runs`

所以这轮优化的目标不是改变模型，而是把“当前确认最慢的标量时间步路径”从
数组语义开销里解放出来。

---

## 在流水线中的位置

```
sample_initial_position → (x₀, z₀)
_compute_diffusion_coefficient → D   
        │                          │
        ▼                          ▼
simulate_particle_trajectory(x₀, z₀, D, rng)
        │
        ▼ {time_s, x_m(t), y_m(t), z_m(t)}
compute_illumination_envelope
```

如果启用了 `center_biased_surrogate`，那么 `sample_initial_position` 这一步还会额外导出：

- `initial_position_distribution_active`
- `initial_position_confinement_ratio`
- `initial_position_x_norm / initial_position_z_norm`

这些量随后会被 `nodi_simulator/parameter_sweep.py` 带入事件级、batch 级和 `observation_signature`
审计链，而不是只停留在 utils 内部。
