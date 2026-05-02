# `data_objects.py`

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

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
- `materials.py`（延迟导入：`get_n_complex`，在 `n_complex_at` / `refractive_index_at` 方法内按需调用）

## 专题补充
- [`guides/core/01_data_objects.md`](guides/core/01_data_objects.md)

## 备注
- 当前 `OpticalSystem` 已显式区分 `illumination_NA` 与 `NA_collection`：前者服务照明几何与 effective waist，后者服务收集口径与 NA cutoff。
- 当前 `SimulationConfig` 也已把 `illumination_mode`、`flow_profile_model`、`coupling_model`、`include_diffusion`、`reflecting_boundary` 等输运/照明开关冻结为统一配置字段。
- `SimulationConfig` 还包含事件块执行配置：`vectorized_event_engine`、`event_block_size`、`event_block_rng_order`。基础包和正式 dashboard/precompute 默认均为 `vectorized_event_engine="off"`，以保持最保守的 scalar event loop；`event_block_v3 / 32 / event_loop_order` 保留为显式性能实验/回归对照。
- `Particle.model_type` 当前支持 homogeneous `"mie"` 与 `"mie_core_shell"`；core-shell 粒子必须提供 `structure_key`。
- 需要注意两层默认值：基础包里的 `data_objects.py::DEFAULT_SIM_CFG` 仍是最小审计链；dashboard / precompute / single-case 主默认则以 `dashboard/config.py::DEFAULT_SIM_CFG` 为准。
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
