# `nodi_simulator/trajectory.py`

> 本文件为模块导航摘要；完整 API、边界条件与实现细节以源码 docstring 和测试为准。

## 文件定位
- 类型：核心仿真模块
- 模块摘要：NODI Interferometric Simulator — Trajectory Module
- 当前职责：生成粒子穿过通道时的运动轨迹，包括流动与可选扩散过程。

## 主要符号
- 顶层函数：`build_trajectory_context`、`estimate_max_axial_velocity`、`axial_velocity_m_s`、`hindered_diffusion_factors`、`axial_transport_velocity_m_s`、`simulate_particle_trajectory`、`simulate_particle_trajectory_block`。
- 重要内部 helper：rect-series / wall-hindrance / reflection kernels。
- 顶层类：`TrajectoryContext`

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：这里承载核心物理或仿真逻辑，修改时应优先保证数值口径稳定，并补充对应测试。

## 关联代码
- `nodi_simulator/data_objects.py`（`Channel`、`OpticalSystem`、`SimulationConfig`）

## 专题补充
- [`guides/core/07_trajectory.md`](guides/core/07_trajectory.md)

## 备注
- `TrajectoryContext` 是 case-level 性能上下文，用来在同一 case 的多个 event 之间复用 `n_samples / dt_s / time_s / accessible half spans / rect_series` 常量。它不保存随机轨迹，不改变初始位置采样、扩散随机数或反射边界逻辑。
- `simulate_particle_trajectory(..., trajectory_context=...)` 在未传 context 时仍会按旧路径即时构建，保持单函数调用兼容；precompute / sweep 会优先在 case 层构建并复用。
- `plug + diffusion + no hindrance` 子路径有块级 kernel，可供显式启用的 `event_block_v3` 批量事件路径使用；它保持 scalar RNG 消费顺序和反射边界语义。当前正式 precompute 默认仍是 `vectorized_event_engine="off"` 的 scalar event loop。
- `numba` 仍是可选加速依赖；缺失时 trajectory kernel 会发出 runtime warning，并退回无 JIT 路径。
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
