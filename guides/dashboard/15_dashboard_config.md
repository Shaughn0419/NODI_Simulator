# dashboard/config.py — 共享配置

<!-- DOCSYNC:START -->
> 2026-05-02 当前同步状态：在 2026-04-28 EV/NODI governance 基础上，代码主线已加入 selected-annulus parallel analysis lens：工程 gate 与主评分仍使用 all-crossing `detection_rate`；selected-candidate 与 edge-norm `0.5-0.8` annulus 条件率同时导出，EV targeted panel 与全量 size-weighted route analysis 现在会输出 selected-annulus 独立 ranking/comparison，用于和主口径交叉验证。Tsuyama 2022 Table S1 fixed-index Au/Ag audit profile、selected-annulus joint-fit paper-calibration lane、bounded `signal_transfer_fit` / `size_response` paper-fit variants、linked 488-window/532-max classification feature lane、以及 selected-annulus paper-fit EV targeted / 3-seed pre-fullgrid robustness audit 已加入 paper-claim 审计路径；这些 paper-fit 项不改变全局材料默认或 EV ranking。2026-05-02 追加复核已将 `joint_fit_score` 明确为 lower-is-better loss-style penalty，`paper_alignment_target` 元数据约束和 selected-annulus claim compatibility check 已落到代码/测试；annulus sensitivity 输出固定报告 Au `20/30/40/60 nm` 与 Ag `40/60 nm` 当前 joint-fit 粒径口径；all-crossing 不对齐 paper target、paper audit/工程主库 lane 分层和 non-paper-target joint-fit variant early rejection 已同步。当前验证基线：`ruff check .` 通过；`python -m pyright` 0 errors；`pytest -q` = `563 passed`，无 warnings；缺 selected-annulus 列的旧 CSV 输入会显式标记 lens unavailable/NaN，不再伪造 selected 结果。
<!-- DOCSYNC:END -->

> 2026-04-08 复核：已按当前代码、当前 dashboard 导航结构与当前文档分层重新核对；如与更深层专题分析冲突，应以明确标注为“现行”的专题文档和同名代码说明为准。

> 2026-04-28 补充：当前 nominal anchor 主库口径是 `ev_design + full_range_biomimetic_exosome_with_anchors`。若要把 EV optical-model uncertainty 纳入 worst-case/percentile score，应使用 `ev_design_biomimetic_ensemble_with_anchors`。旧 `fine_full_range_*` 与不带 Au20/Au30 anchor 的 `full_range_biomimetic_exosome` 只作为兼容/对照口径，不再作为 current truth。



## 当前使用方式

- 文档定位：dashboard 配置专题
- 推荐阅读时机：当你要理解 dashboard 默认口径、粒径/波长范围和共享配置时，读这份。
- 与代码的关系：如果你要继续落到具体实现，请同时对照对应的同名 `.md` 或直接查看相关代码文件。
- 建议搭配阅读：
- [dashboard/config.md](../../dashboard/config.md)
- [dashboard/app.md](../../dashboard/app.md)
- [dashboard/panels/common.md](../../dashboard/panels/common.md)

## 文件职责

整个可视化面板的**唯一配置来源**。precompute.py（预计算）和 backend.py（面板后端）都从这里读取物理参数、网格定义、粒子工厂和 UI 文本。修改此文件等于修改整个面板的物理假设。

从 2026-04-12 这一轮开始，`single_case_calculator.py` 的页面默认值也直接从这里取，不再单独回退到基础包 `data_objects.py::DEFAULT_SIM_CFG`。

本轮需要特别注意的是：这里已经不再只定义“频率 + 串扰”的最小 lock-in surrogate，而是额外承载了：

- `readout_observable_mode`
- `pod_reference_phase_rad / nodi_reference_phase_rad`
- `post_readout_noise_std / post_readout_drift_slope`

也就是说，dashboard 默认配置现在已经能区分：

- in-phase 观测
- magnitude 包络观测
- raw 光学噪声
- readout 之后的电子学/基线扰动

同时，dashboard 默认 `DEFAULT_SIM_CFG` 现在已经把参考场空间口径推进到：

- `reference_spatial_mode="cross_section_surrogate"`
- `reference_spatial_amplitude_strength=0.35`
- `reference_spatial_phase_strength_rad≈36°`

也就是说，Interference / Noise / Inspector 等 live/on-demand 页面默认已经不再把
reference 场视作“整个事件完全不变的标量”。

---

## 核心设计：粒子系统分离

粒子由**材料类型 + 粒径**两部分定义，不再绑定为固定对象：

| 场景 | 粒子来源 | 说明 |
|------|----------|------|
| nominal anchor 全量重算 | `get_precompute_profile("full_range_biomimetic_exosome_with_anchors")` | 当前 EV/NODI design nominal 主库口径：gold 20/30nm anchors + gold 40–300nm + biomimetic core-shell exosome 40–300nm，主范围 10nm 步进 |
| EV optical-uncertainty 全量重算 | `get_precompute_profile("ev_design_biomimetic_ensemble_with_anchors")` | Au20/Au30 anchors + gold 40–300nm + 四个 literature-bounded EV optical presets × 50–150nm，用于 EV optical uncertainty worst-case/percentile 评分 |
| quick / legacy sweep | `get_precompute_profile("quick" / "full_range")` | 用于快速浏览或历史 homogeneous exosome 对照，不是当前标准全量库 |
| live sweep | `make_particle(material, diameter)` | 底层仍支持传入任意直径；但 dashboard UI 当前统一使用 40–300nm、10nm 步进 |
| baseline 归一化 | `BASELINE_PARTICLE` | 固定 gold 40nm |

---

## 常量与数据结构

### 角度网格

| 常量 | 值 | 说明 |
|------|-----|------|
| `THETA_GRID_RAD` | `np.linspace(0.01, π-0.01, 500)` | Mie 散射计算的角度采样点 |

### 粒子系统

| 常量 | 类型 | 说明 |
|------|------|------|
| `MATERIAL_OPTIONS` | `list[str]` | 可选材料：`["gold", "exosome"]` |
| `DIAMETER_RANGE_NM` | `tuple` | 粒径范围：`(40, 300)` |
| `FULL_DIAMETER_STEP_NM` | `int` | `full_range` 预计算粒径步进，当前为 `10` |
| `FULL_DIAMETER_VALUES_NM` | `list[int]` | `full_range` 粒径列表：`[40, 50, ..., 300]` |
| `DASHBOARD_DIAMETER_STEP_NM` | `int` | dashboard 粒径控件共享步进，当前为 `10` |
| `DASHBOARD_DIAMETER_VALUES_NM` | `tuple[int, ...]` | dashboard 共享粒径网格，当前等于 `FULL_DIAMETER_VALUES_NM` |
| `DEFAULT_DASHBOARD_DIAMETER_NM` | `int` | dashboard 页面的默认粒径，当前为 `100` |
| `MATERIAL_DEFAULTS` | `dict` | 各材料默认折射率 n_real + n_imag |
| `BASELINE_PARTICLE` | `Particle` | 归一化基准粒子（gold 40nm） |
| `MATERIAL_PHYSICS_LABELS` | `dict[str, str]` | 材料的物理类型标签，供 UI selectbox 显示 |

### 光学与模拟

| 常量 | 说明 |
|------|------|
| `MEDIUM` | dashboard 通用 fallback 介质，当前为 `WATER`；真正运行时会通过 `medium_for_material()` / `medium_for_particle()` 按粒子类型分流：gold→`WATER`，exosome→`PBS_1X` |
| `OPTICAL_TEMPLATE` | 光学系统模板（模板波长 660nm；实际 illumination geometry 会按每个波长分别解析） |
| `DEFAULT_SIM_CFG` | dashboard live/on-demand 标准默认 SimulationConfig（`rect_series + diffusion + joint score`；precompute 会先套用 EV/NODI design preset 再按 case 单粒子落盘） |

当前 dashboard 对 lock-in 时间常数的现行理解也同步为：

- 论文实验范围：`1–2 ms`
- 当前面板默认：`1 ms`
- 这样做是为了与真实机器可直接设置的 `1 ms / 2 ms` 档位保持一致

注意：这里的 `DEFAULT_SIM_CFG.score_mode="joint"` 是 live/on-demand 页面默认口径；
`dashboard/precompute.py::build_precompute_sim_cfg()` 会在深拷贝该配置后把
`score_mode` 强制改为 `"single"`，因为预计算数据集按单个 particle / case 落盘。
正式全量重算还会固定 `readout_preset="EV_NODI_only_design"`、`readout_observable_mode="magnitude"`、`nodi_readout_semantics="bandpass_envelope_surrogate"`、`readout_internal_demod_route="analytic_lockin_surrogate"` 和 `initial_position_distribution_mode="flux_weighted"`。

| `GRID_CONFIGS` | 扫描网格定义：`coarse`、`fine` 和当前正式 `ev_design`（W=500/600/700/800/900/1000/1100/1200/1300/1400/1500nm，H=500/550/600/650/700/800/900/1000/1100/1200/1300/1400/1500nm，λ=404/488/532/660nm） |

---

## 函数

### `make_particle(material_key, diameter_nm) → Particle`

粒子工厂。从材料类型和粒径构建 Particle 实例。

| 参数 | 类型 | 说明 |
|------|------|------|
| `material_key` | `str` | `"gold"` 或 `"exosome"` |
| `diameter_nm` | `float` | 粒径（nm），范围 40–300 |

返回带 `material_key` 和 `use_material_model=True` 的 Particle 实例。名称自动生成为 `"{material}_{diameter}nm"`，其中非整数粒径会先四舍五入到最近的整数纳米再进入名称。

**当前约定**：
- UI 面向用户显示的材料名只有 `gold` 和 `exosome`
- `make_particle("exosome", ...)` 仍返回 homogeneous `exosome_uniform`，只用于 quick / legacy / live fallback
- 正式全量重算不走 homogeneous fallback，而是通过 `build_biomimetic_exosome_family(...)` 生成 biomimetic core-shell exosome 粒子族
- 当前标准 `full_range_biomimetic_exosome_with_anchors` 预计算档位包含 `20 / 30 nm` Au anchors，以及 `40, 50, ..., 300 nm` 的 gold 与 biomimetic exosome 主范围；主范围不是逐 `1 nm` 扫描
- 当前 EV optical-uncertainty 档位 `ev_design_biomimetic_ensemble_with_anchors` 额外包含 `50, 60, ..., 150 nm` 的四个 EV optical presets，不只是 nominal biomimetic preset。

### `clip_diameter_nm()` / `snap_diameter_nm()` / `diameter_values_between()`

这组 helper 是当前 dashboard 粒径逻辑的统一入口：

- `clip_diameter_nm()`：把输入裁剪到 `40–300 nm`
- `snap_diameter_nm()`：把粒径吸附到最近的 `10 nm` 网格
- `diameter_values_between()`：生成某个范围内可用的 dashboard 粒径列表

`Mie Explorer`、`Interference Explorer` 和 `Noise & Detection Explorer` 现在都通过它们保持一致，不再各自写一套粒径步进逻辑。

### `build_particle_family(material_key, diameters_nm) → list[Particle]`

按给定粒径列表批量生成同材质粒子族。`quick` 和 legacy `full_range` 通过它构建 homogeneous 粒子列表；当前正式全量重算中的 gold 粒子族也通过它生成。

### `build_biomimetic_exosome_family(diameters_nm, preset_name=...) → list[Particle]`

按给定粒径列表生成 biomimetic core-shell exosome 粒子族。当前标准 `full_range_biomimetic_exosome_with_anchors` profile 使用这个函数生成 exosome lane。

### `get_precompute_profile(profile_name) → dict`

返回预计算 profile 元数据，包括：
- `label`
- `description`
- `particles`
- `default_tag`

当前 profile 口径：
- `quick`：`gold 40nm` + homogeneous `exosome 100nm`，用于快速浏览
- `full_range`：`gold / homogeneous exosome × [40, 50, ..., 300] nm`，legacy 对照口径
- `full_range_biomimetic_exosome`：`gold + biomimetic core-shell exosome × [40, 50, ..., 300] nm`，不带 Au20/Au30 anchor 的兼容对照口径
- `full_range_biomimetic_exosome_with_anchors`：`gold 20/30nm anchors + gold / biomimetic core-shell exosome × [40, 50, ..., 300] nm`，当前 nominal anchor 全量重算口径
- `ev_design_biomimetic_ensemble_with_anchors`：`gold 20/30nm anchors + gold × [40, 50, ..., 300] nm + four EV optical presets × [50, 60, ..., 150] nm`，当前 EV optical-uncertainty 全量重算口径

### `get_precompute_particles(profile_name) → list[Particle]`

返回指定 profile 的粒子列表。

当前数量：
- `quick`：2 个粒子
- `full_range`：54 个粒子（gold 27 个 + homogeneous exosome 27 个）
- `full_range_biomimetic_exosome`：54 个粒子（gold 27 个 + biomimetic core-shell exosome 27 个）
- `full_range_biomimetic_exosome_with_anchors`：56 个粒子（gold anchors 2 个 + gold 27 个 + biomimetic core-shell exosome 27 个）
- `ev_design_biomimetic_ensemble_with_anchors`：73 个粒子（gold anchors 2 个 + gold 27 个 + EV optical preset ensemble 44 个）

### `compute_particle_physics_status(material_key, diameter_nm, wavelength_nm) → dict`

实时计算粒子的物理状态，供 Explorer 侧边栏显示。

返回：
- `size_parameter`：x = 2πa·n_m/λ
- `scattering_regime`：`"Rayleigh"` / `"Rayleigh–Mie 过渡区"` / `"Mie"`
- `scattering_scaling`：散射缩放关系描述
- `material_type`：物理类型描述

### `get_score_explanation(case_data) → dict`

自动分析 case 的 score 成因。输入为 compact 格式的 case dict。

返回：
- `explanation`：中文成因描述
- `trust_level`：`"high"` / `"medium"` / `"low"`
- `trust_reason`：可信度原因
- `dominant_factor`：`"scattering"` / `"reference"` / `"coupling"` / `"balanced"`
- `E_sca_E_ref_ratio`：散射场与参考场的比值

---

## 三层参数说明体系

### `PARAM_HELP`（简短版）

供 UI 控件的 `help=` tooltip 参数使用。每个参数一行简述。

### `PARAM_HELP_FULL`（完整版）

供"参数解释模式"展开显示。每个参数包含三层：
- **定义**：参数的物理含义
- **物理作用**：如何影响模拟过程
- **对结果影响**：改变此参数会导致什么变化 + 建议范围

## 被哪些文件依赖

| 依赖方 | 使用的内容 |
|--------|-----------|
| `precompute.py` | `BASELINE_PARTICLE`, `MEDIUM`, `OPTICAL_TEMPLATE`, `DEFAULT_SIM_CFG`, `THETA_GRID_RAD`, `GRID_CONFIGS` |
| `backend.py` | `DEFAULT_SIM_CFG`, `OPTICAL_TEMPLATE`, `BASELINE_PARTICLE`, `MEDIUM`, `THETA_GRID_RAD`, `GRID_CONFIGS` |
| `explorer.py` | `GRID_CONFIGS`, `MATERIAL_OPTIONS`, `PARAM_HELP`, `PARAM_HELP_FULL`, `MATERIAL_PHYSICS_LABELS`, `compute_particle_physics_status` |
| `inspector.py` | `get_score_explanation` |
