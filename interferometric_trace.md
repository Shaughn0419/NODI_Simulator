# `interferometric_trace.py`

## 文件定位
- 类型：核心仿真模块
- 模块摘要：NODI Interferometric Simulator — Interferometric Trace Module
- 当前职责：把散射 trace 与参考场叠加，生成干涉读出、clean signal 与相关诊断量。

## 主要符号
- 顶层函数：`generate_interferometric_trace`
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：这里承载核心物理或仿真逻辑，修改时应优先保证数值口径稳定，并补充对应测试。

## 关联代码
- `data_objects.py`（`SimulationConfig`）

## 专题补充
- [`guides/core/09_interferometric_trace.md`](guides/core/09_interferometric_trace.md)

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
