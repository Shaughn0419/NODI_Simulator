# `nodi_simulator/data_objects.py`

> 本文件为模块导航摘要；完整 API、边界条件与实现细节以源码 docstring 和测试为准。

## 文件定位
- 类型：核心仿真模块
- 模块摘要：NODI Interferometric Simulator — Data Objects
- 当前职责：定义仿真所需的核心数据对象与配置结构，是物理计算与 sweep 的统一输入层。

## 主要符号
- 顶层函数：`resolve_reference_route_name`、`resolve_reference_solver_route_name`、`make_gold_baseline_particle`、`get_readout_preset_overrides`、`apply_readout_preset`、`make_ev_nodi_design_sweep_config`
- 顶层类：`Particle`、`Medium`、`Channel`、`OpticalSystem`、`DesignObjectiveConfig`、`SimulationConfig`

## 调用与使用
- 典型使用方式：通常作为包内定义文件被其他模块引用。
- 直接维护建议：这里承载核心物理或仿真逻辑，修改时应优先保证数值口径稳定，并补充对应测试。

## 关联代码
- `nodi_simulator/materials.py`（延迟导入：`get_n_complex`，在 `n_complex_at` / `refractive_index_at` 方法内按需调用）

## 专题补充
- [`guides/core/01_data_objects.md`](guides/core/01_data_objects.md)

## 备注
- 当前 `OpticalSystem` 已显式区分 `illumination_NA` 与 `NA_collection`：前者服务照明几何与 effective waist，后者服务收集口径与 NA cutoff。
- 当前 `SimulationConfig` 也已把 `illumination_mode`、`flow_profile_model`、`coupling_model`、`include_diffusion`、`reflecting_boundary` 等输运/照明开关冻结为统一配置字段。
- `SimulationConfig` 还包含事件块执行配置：`vectorized_event_engine`、`event_block_size`、`event_block_rng_order`。基础包和正式 dashboard/precompute 默认均为 `vectorized_event_engine="off"`，以保持最保守的 scalar event loop；`event_block_v3 / 32 / event_loop_order` 保留为显式性能实验/回归对照。
- `Particle.model_type` 当前支持 homogeneous `"mie"` 与 `"mie_core_shell"`；core-shell 粒子必须提供 `structure_key`。
- 需要注意两层默认值：基础包里的 `nodi_simulator/data_objects.py::DEFAULT_SIM_CFG` 仍是最小审计链；dashboard / precompute / single-case 主默认则以 `dashboard/config.py::DEFAULT_SIM_CFG` 为准。
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
