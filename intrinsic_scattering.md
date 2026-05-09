# `nodi_simulator/intrinsic_scattering.py`

> 本文件为模块导航摘要；完整 API、边界条件与实现细节以源码 docstring 和测试为准。

## 文件定位
- 类型：核心仿真模块
- 模块摘要：NODI Interferometric Simulator — Intrinsic Scattering Module
- 当前职责：把粒子与介质参数送入 Mie 引擎，得到本征散射量与方向性结果。

## 主要符号
- 顶层函数：`compute_intrinsic_scattering`
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：这里承载核心物理或仿真逻辑，修改时应优先保证数值口径稳定，并补充对应测试。

## 关联代码
- `nodi_simulator/data_objects.py`（`Particle`、`Medium`）
- `nodi_simulator/mie_engine.py`（`mie_compute`、`mie_angular`）

## 专题补充
- [`guides/core/03_intrinsic_scattering.md`](guides/core/03_intrinsic_scattering.md)

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
