# `dashboard/config.py`

## 文件定位
- 类型：Dashboard 支撑模块
- 模块摘要：dashboard/config.py — 共享配置
- 当前职责：Dashboard 共享配置层，统一粒子标签、默认范围、预计算配置和解释性文本。

## 主要符号
- 顶层函数：`normalize_material_key`、`material_display_name`、`infer_particle_material`、`medium_for_material`、`medium_for_particle_name`、`medium_for_particle`、`infer_particle_diameter_nm`、`infer_biomimetic_exosome_preset_name`、`format_particle_label`、`clip_diameter_nm`、`snap_diameter_nm`、`diameter_values_between`、`particle_from_name`、`make_particle`、`build_particle_family`、`build_biomimetic_exosome_family`、`get_precompute_profile`、`get_precompute_particles`、`compute_particle_physics_status`、`get_score_explanation` 等
- 顶层类：当前没有顶层类，或主要以函数式模块组织逻辑。

## 调用与使用
- 典型使用方式：通常由其他模块导入调用，或被 dashboard / sweep / 测试脚本间接使用。
- 直接维护建议：这里适合放共享配置、结果加载和计算桥接逻辑；尽量避免把页面展示文案和大段 UI 拼装塞进来。

补充：
- `dashboard/config.py::DEFAULT_SIM_CFG` 现在不仅供 backend / live 页面使用，也作为 single-case 页面默认值来源。
- `DEFAULT_SIM_CFG.score_mode` 在 live/on-demand 页面中保持 `"joint"`；预计算入口会通过 `dashboard/precompute.py::build_precompute_sim_cfg()` 先套用 `make_ev_nodi_design_sweep_config(...)`，再改为 `"single"`，以匹配 EV/NODI relative design 主库口径和按单 particle / case 落盘的数据集结构。
- 当前 nominal anchor 全量重算 profile 是 `full_range_biomimetic_exosome_with_anchors`：gold lane 包含 `20 / 30 nm` Au anchor 与 `40–300 nm` 主范围，exosome lane 来自 `build_biomimetic_exosome_family(...)` 的 `40–300 nm` biomimetic core-shell 粒子族；`full_range_biomimetic_exosome` 保留为不带 Au20/Au30 anchor 的兼容口径，`make_particle("exosome", ...)` 保留为 homogeneous quick / legacy fallback。
- 当前 EV optical-uncertainty profile 是 `ev_design_biomimetic_ensemble_with_anchors`：Au20/Au30 anchors + gold `40–300 nm` + `50–150 nm` 的四个 literature-bounded EV optical presets，用于让 EV score worst-case/percentile 同时反映 size 与 optical-model uncertainty。
- 当前正式设计网格是 `ev_design`：`W = 500 / 600 / 700 / 800 / 900 / 1000 / 1100 / 1200 / 1300 / 1400 / 1500 nm`，`H = 500 / 550 / 600 / 650 / 700 / 800 / 900 / 1000 / 1100 / 1200 / 1300 / 1400 / 1500 nm`，`λ = 404 / 488 / 532 / 660 nm`。

## 关联代码
- `nodi_simulator`（绝对导入：`Particle`、`Medium`、`Channel` 等核心数据对象和物理函数）

## 专题补充
- [`guides/dashboard/15_dashboard_config.md`](../guides/dashboard/15_dashboard_config.md)

## 备注
- 本说明文件使用 UTF-8 编写，并与同名 Python 文件保持一一对应。
