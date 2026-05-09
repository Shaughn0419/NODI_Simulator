# `nodi_simulator/illumination.py`

> 本文件为模块导航摘要；完整 API、边界条件与实现细节以源码 docstring 和测试为准。

## 文件定位
- 类型：核心仿真模块
- 模块摘要：NODI Interferometric Simulator — Illumination Module
- 当前职责：定义照明包络、光束腰斑与位置依赖强度，用于把本征散射映射到时域事件。

## 主要符号
- 顶层函数：`compute_illumination_envelope`
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：这里承载核心物理或仿真逻辑，修改时应优先保证数值口径稳定，并补充对应测试。

## 关联代码
- `nodi_simulator/data_objects.py`（`OpticalSystem`、`SimulationConfig`）
- `nodi_simulator/utils.py`（`build_projection_basis_diagnostics`、`resolve_polarization_coupling`）

## 专题补充
- [`guides/core/06_illumination.md`](guides/core/06_illumination.md)

## 备注
- `compute_illumination_envelope(..., export_full_diagnostics=False)` 会跳过 `I_inc_*`、`E_env_complex` 与 `beam_inverse_wavefront_radius_m_inv` 等 stream-summary event block 不消费的大数组；信号生成仍保留 `A_env / A_env_scalar / phi_beam_rad / phi_beam_gouy_rad / phi_beam_curv_rad`。
- 当输入是 2D event block 数组且安装了 `numba` 时，light diagnostics 路径会走 `_illumination_light_2d_kernel`，用于当前 `event_block_v3` 主线；它保持与 full diagnostics 中信号字段一致。
- `numba` 缺失时 illumination kernel 会发出 runtime warning，并退回无 JIT 路径。
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
