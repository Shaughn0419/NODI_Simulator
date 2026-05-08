# `scattering_trace.py`

## 文件定位
- 类型：核心仿真模块
- 模块摘要：NODI Interferometric Simulator — Scattering Field Trace Module
- 当前职责：根据轨迹、照明与耦合关系生成散射随时间变化的 trace。

## 主要符号
- 顶层函数：`_wrap_to_pi`、`_surrogate_focus_crossing_phase`、`_resolve_path_opd_diagnostics`、`spatial_coupling_factor`、`compute_scattering_field_trace`
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：这里承载核心物理或仿真逻辑，修改时应优先保证数值口径稳定，并补充对应测试。

## 关联代码
- `data_objects.py`（`Channel`、`OpticalSystem`、`SimulationConfig`）

## 专题补充
- [`guides/core/08_scattering_trace.md`](guides/core/08_scattering_trace.md)

## 备注
- `compute_scattering_field_trace(...)` 不再强制要求 illumination payload 持有 `E_env_complex` 和所有 beam-phase 诊断数组。summary-only / event-block light 路径只传 `A_env` 与 `phi_beam_*` 信号字段时，会按需组合复包络并为缺失诊断提供零相位 fallback。
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
