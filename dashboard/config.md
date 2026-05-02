# `dashboard/config.py`

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

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
