# dashboard/panels/explorer.py — Design Explorer 页面

<!-- DOCSYNC:START -->
> 归档提示（2026-04-28）：本文保留历史快照，不覆盖现行代码事实。当前主线已更新到 EV/NODI relative design gate 拆分、detector caution 分层、calibrated BFP ROI mask 到 Tsuyama 1D projected ROI、完整 governance diagnostics 导出；验证基线为 `pytest -q` = `509 passed`，`ruff check .` / `pyright` 通过。现行结论以根目录 `README.md`、`文档导航.md`、`00/24/42/43` 和代码测试为准。
<!-- DOCSYNC:END -->

> 2026-04-08 复核：已按当前代码、当前 dashboard 导航结构与当前文档分层重新核对；如与更深层专题分析冲突，应以明确标注为“现行”的专题文档和同名代码说明为准。


> 2026-04-07 补充：Design Explorer 当前默认解释四波长标准主库 `404 / 488 / 532 / 660 nm`，相关推荐、聚合统计和排序都应基于 `55296 cases` 的 full-range 结果集理解。



## 当前使用方式

- 文档定位：Design Explorer 专题
- 推荐阅读时机：当你要理解平台筛选、热图、候选排序和 design explorer 的使用边界时，读这份。
- 与代码的关系：如果你要继续落到具体实现，请同时对照对应的同名 `.md` 或直接查看相关代码文件。
- 建议搭配阅读：
- [dashboard/panels/explorer.md](../../dashboard/panels/explorer.md)
- [20_dashboard_inspector.full.md](./20_dashboard_inspector.full.md)
- [archive/reports/33_full_range_4w_analysis.md](../../archive/reports/33_full_range_4w_analysis.md)

## 文件职责

面板的主页面。通过热图、排名表、切片图帮助用户找到最优 (W, H, λ) 设计区。支持两级控件：即时筛选/显示和物理参数重跑。

> 阶段 A 更新（2026-04-07）：`Design Explorer` 已开始按新的 dashboard 主路线收口。页面默认优先围绕标准 `fine_full_range_*` 结果库工作；live sweep 仍保留，但已明确降级为“工程调试”入口，不再和主流程结果库分析处于同一叙事层级。

页面顶部现在会先显示跨页工作流提示，告诉用户这一页在整个分析链里的位置：
`Principle Guide -> Mie Explorer -> Interference Explorer -> Noise & Detection Explorer -> Design Explorer -> Case Inspector`

---

## 页面布局

```

页面还新增了两层使用引导：
- **全页引导**：`这页怎么用`，解释什么时候先来这页、推荐顺序、如何区分平台型高分和尖峰型高分；现在默认折叠，避免一打开页面先被长说明占满
- **视图引导**：热图、Top 10、参数点选择、切片图前都会提示“看什么 / 怎么理解”
- **当前筛选结论**：在当前候选点摘要和统一决策摘要之后，页面会直接给出一段简短结论，说明当前筛选结果更像“平台区”“尖峰点”还是“仍需回头查 physics/gate”
- **当前点详细指标后置**：当前候选点的长串 score / robust / freeze / gate 细指标不再直接铺在主页面，而是先后置到展开区
- **当前点长明细已删除**：最近这一轮又继续做减法，把这块长明细进一步收掉，只保留一行 `CV / 稳健评分 / 平均峰高` 的补充摘要
- **当前跨页上下文**：在候选点摘要后显示统一样式的摘要卡，展示当前粒子、波长、W、H，帮助用户确认后续页面共享的是哪个 case
- **Top 3 -> local_fine**：候选点概览下方提供按钮，可直接围绕前 3 个候选点做局部 `100 nm` 细扫
- **推荐标签前置**：候选点表和当前候选点摘要现在会直接显示 `design_recommendation_label / observation_freeze_status`，把“推荐（默认）”“推荐（需复核）”“可研究（门槛未过）”先在浏览层拆开
- **gate 卡点前置**：当当前点未过工程门槛时，摘要现在还会显示 `engineering_gate_primary_blocker_label / engineering_gate_guidance`，不用先跳 Inspector 才知道主要是卡在稳定检出率、相位翻转还是 paired 确认
- **统一决策摘要卡**：当前候选点处不再先给一块独立 callout、再重复一遍筛选结论；现在把 `decision_summary` 直接并入 `当前筛选结论`，减少重复判断
- **旧结果兼容显示**：即使当前加载的是较早冻结的 `summary/compact` 文件，只要其中仍保留 `engineering_gate_*` 基础字段和 `observation_freeze_status`，backend 也会在加载时自动补齐 `design_recommendation_*` 与 `engineering_gate_*` 解释层字段，所以候选表不会因为结果文件版本略旧而丢失推荐标签
- **结果库健康摘要**：热图区前面现在会先显示一块 dataset-level health summary，先判断当前结果库能不能放心浏览；详细分布与切片后置到展开区
- **整体趋势结论前置**：结果库健康摘要之后，页面现在会按当前选中的目标材料组织结论。若当前是 `exosome`，页面会明确采用“面向 exosome 的选型结论”口径：gold 只作为验证参照，不再与 exosome 平级竞争“谁更强”；真正要先回答的是 exosome 自己在哪个波长和哪类几何上形成更稳的平台
- **趋势阅读提示补充**：三条整体趋势结论下面现在还会再给一句“怎么看这些趋势”，明确区分“已经形成稳定平台”与“仍然只是孤立亮点”，避免把单点最高误读成全局最优
- **筛选框架补充**：最近这一轮又新增 `先按什么筛 / 优先信什么证据 / 最要警惕什么` 三条短框，帮助把材料、波长、几何三条结论真正变成筛选动作
┌────────────────────────────────────────────────────────────┐
│  [数据来源标识栏]（仅 live 模式显示参数摘要）               │
├────────────────────────────────────────────────────────────┤
│  结果库健康摘要                                            │
├────────────────────────────────────────────────────────────┤
│  整体趋势结论（材料 / 波长 / 几何）                        │
├────────────────────────────────────────────────────────────┤
│  热图：先看区域                                            │
├────────────────────────────────────────────────────────────┤
│  候选点概览：再看 top 是否集中                             │
├────────────────────────────────────────────────────────────┤
│  当前候选点摘要 + 当前筛选结论                             │
├────────────────────────────────────────────────────────────┤
│  W/H 切片：最后看扰动敏感性                                │
└────────────────────────────────────────────────────────────┘
```

---

## 侧边栏结构

现在侧边栏已经拆成两个 tab：

- **结果库筛选**：主流程结果库、粒子/粒径、波长、热图指标、评分权重
- **工程调试**：live sweep 相关的粒子模型、reference、噪声、流动、归一化与耦合参数

这样做的目的是把“标准结果库分析”和“真的要改模型重跑”分开，避免首次使用时被 live 调参入口打断主流程。

当前 UI 文案口径也已统一：

- 面向用户的控件标签优先使用中文
- 内部枚举值仍保留 `constant / geometry_scaled / gaussian_xy / per_wavelength` 等代码值
- 因此文档里提到这些枚举时，表示的是“选项值”，不是界面主标签

### 一级控件（即时生效）

| 控件 | 类型 | 说明 |
|------|------|------|
| 参数解释模式 | toggle | 开启后每个参数下方显示完整三层解释 |
| 粒子类型 | selectbox | 只显示用户材料名：`gold` / `exosome`；当两者都存在且当前没有历史选择时，默认优先落到 `exosome`，因为页面默认服务最终 exosome 选型 |
| 粒径 | selectbox | 从当前数据集可用粒径中筛选；若是 full_range，则口径为 `40–300 nm`、`10 nm` 步进 |
| 波长 | selectbox | 从数据中筛选 |
| 热图指标 | selectbox | `score / engineering_score / final_engineering_score / detection_rate / stable_detection_rate / mean_peak_height / mean_local_snr / mean_transit_time_ms / paired_detection_rate / ROC-AUC / d′ / CV` |
| 峰高/检出率/CV 权重 | slider ×3 | 重算 score_display，不影响 robust/joint |

### 二级控件（改后需重跑）

| 分组 | 控件 | 条件禁用 |
|------|------|----------|
| **粒子选择** | 材料类型 selectbox + 粒径 slider（当前统一 `40–300 nm`、`10 nm` 步进）+ 实时物理状态 | — |
| **干涉系统** | reference_model, ρ, α, β, γ | constant 模式下隐藏 α/β/γ |
| **噪声与检测** | noise_model, noise_std, drift_slope, threshold_sigma | gaussian 模式下隐藏 drift_slope |
| **流动参数** | 流速, beam_waist_y, 布朗扩散开关 | — |
| **归一化与耦合** | normalization_mode, coupling_model | — |

### 操作按钮

- **以当前参数重跑 Sweep** — 运行当前选择的网格分辨率 sweep，结果存入 session_state
- **恢复预计算数据** — 仅 live 模式下显示，清空 live 数据和 case_cache

### 扫描分辨率（新增）

live sweep 现在不再固定只能用 `coarse`，而是提供两档：

- `coarse`：`500 nm` 步长，适合第一轮找大致区域
- `fine`：`100 nm` 步长，适合第二轮认真比较不同宽深、判断平台边界和局部结构
- `local_fine`：围绕当前选中的 `W/H` 做 `100 nm` 局部细扫，默认看 `±300 nm` 范围

从实际使用出发，更推荐两段式：

1. 先用 `coarse` 快速定位候选高分区
2. 再优先用 `local_fine` 复核当前候选点附近的局部平台、峰位和宽深敏感性

如果你真的需要全范围精细比较，再用 `fine`。

另外，现在 `Top 3 -> local_fine` 被后置到候选区的展开块里：

- 不需要先手动把该点再选一遍
- 不需要先把网格切到 `local_fine`
- 直接点击即可围绕该候选点重跑局部细扫

---

## 关键逻辑

### 数据源切换

```python
if using_live_data and sweep_df_live is not None:
    df = sweep_df_live
else:
    df = load_sweep_summary(csv_path)
```

**当前行为**：
- 默认预计算数据只包含代表粒径（例如 gold 40nm、exosome 100nm）
- 若要探索完整粒径覆盖，优先切到 `full_range` 数据集；其粒径口径为 `40–300 nm`、`10 nm` 步进
- 页面会显示“当前数据集粒子组合”，避免把 UI 支持范围误解为预计算覆盖范围
- 页面现在还会同步调用 `load_result_health()`：
  - 若结果目录已有 `*_result_health.json`，直接读取
  - 若是旧结果库尚未生成该文件，则基于当前 `summary_df` 即时补一份

因此这页当前已经能同时回答两件事：

1. 某个点在当前热图里是不是候选
2. 这个结果库整体上是不是仍然处于“可以继续拿来做默认浏览”的健康状态

并且最近这一轮又往前推进了一步：

3. 当前 caution 主要集中在哪个波长子组
4. 当前 caution 是否主要集中在某一类粒子
5. 当前默认结果库整体上是谁更强、哪个波长更占优、高分几何更偏向哪一侧

### score_display 与原始 score 分离

```python
if weights_changed:
    df["score_display"] = recompute_scores(df, w_h, w_r, w_cv)
    active_score_col = "score_display"
else:
    active_score_col = "score"
```

热图/排名/切片在 metric="score" 时使用 `active_score_col`，其他指标直接使用原始列。

### 当前指标一致性（本轮修正）

- 热图标题、候选表排序、切片图 y 轴现在都严格跟随当前选择的指标
- 默认热图指标现在优先落在 `engineering_score`，而不是 `final_engineering_score`
- 原因是 `final_engineering_score` 会把所有未过 gate 的 case 压进同一条负值带，更适合做“通过/未通过”切分，不适合做未通过集合里的细比较
- 当指标为 `CV` 时，候选表会按 **从低到高** 排序，因为 `CV` 越小代表越稳定
- 候选表和当前点的数值格式现在也被显式固定：评分类保留 4 位小数、检出率按百分比、峰高按科学计数法，避免把非零小数看成一排 `0.000`
- 在“选择参数点”下方新增 **当前候选点摘要**，主页面只集中显示当前指标值、当前排名、detection rate；更长的 score / robust / mean height / freeze / gate 明细后置到 `查看当前点详细指标`
- 右侧候选区现在默认先显示 **前 3 个候选点**；完整 Top 10 则放进按需展开，减少主页面表格密度
- 当前这份候选点摘要又会继续带出 `design_recommendation_label` 与 `observation_freeze_status`，所以用户在跳到 Inspector 前，已经能先判断该点到底是默认推荐、谨慎推荐，还是 physics 已就绪但 gate 仍未通过
- `decision_summary` 现在直接并入 `当前筛选结论` callout，把这些状态压缩成一句 headline：
  - `recommended_default -> success`
  - `recommended_with_caution -> warning`
  - `physics_ready_gate_blocked -> warning`
  - `not_recommended_freeze_blocked -> error`
  - 其余走 `info`
  这样当前页就不再先后出现两块结论卡，而是直接告诉用户“这个点现在该优先细扫、复核 freeze，还是只适合作为边界 case”
- 页面顶部新增的 `整体趋势结论` 现在默认带“目标材料视角”：
  - 若当前是 `exosome`：`headline` 会明确写成“面向 exosome 的选型结论”，并提示 gold 仅作验证参照
  - `波长趋势`：按当前目标材料子集比较各波长的中位主指标，判断更像“短波整体占优”“长波整体占优”还是“没有单调优势”
  - `几何趋势`：按当前目标材料子集比较 top case 的中位 `W/H` 与该材料整组中位 `W/H`，判断高分区更偏向较小还是较大截面
  - `验证关系`：若当前目标是 `exosome` 且数据集中也有 `gold`，会显式说明“gold 更强只是验证更容易”，以及 gold 与 exosome 的趋势是否同向

因此这页当前的核心不是“gold 和 exosome 谁分更高”，而是：

1. 如果最终对象是 `exosome`，该先在哪个波长和几何区间里找平台
2. gold 只能帮你判断这些趋势是否值得信，不能直接替代 exosome 的最终设计

因此用户现在不必先自己翻热图和 Top 10，才能知道“这套结果总体更偏向谁”。
而且现在还能更直接判断：这些结论到底已经足够稳定，可以先相信区域趋势；还是仍需回到热图和切片，确认是不是只出现了几个尖峰点。

### 粒子物理状态实时显示

在粒子选择 expander 中，调用 `compute_particle_physics_status` 显示：
- Size parameter x
- Scattering regime（Rayleigh / 过渡区 / Mie）
- 散射缩放关系
- 材料类型描述

### Live 参数摘要栏

live 模式下在主区域顶部显示 `st.info`，包含当前粒子、grid 分辨率、ρ、α/β/γ、noise、drift、velocity、reference_model 等完整参数。

---

## 依赖关系

- **导入**：`backend.py`（数据加载、构图、live sweep）、`config.py`（配置常量、PARAM_HELP、CHART_HELP、物理函数）
- **写入**：`session_state`（selected_particle, selected_wavelength_nm, selected_W_nm, selected_H_nm, live 数据）
- **被读取**：`inspector.py`（通过 session_state 获取选点信息）

---

## 2026-04-03 文案补充

- 选点摘要里的 `Det Rate` 已统一为“检出率”。
- W/H 切片图的坐标轴已统一为“通道宽度 W (nm)”和“通道深度 H (nm)”。
- 图标题已改成“某指标随 W/H 变化”，弱化英文 `vs` 表达。
- 本页仍保留 `coarse / fine / local_fine` 作为网格名，原因是它们同时承担运行模式标识和跨页状态键的语义。
- 2026-04-06 补充：`Design Explorer` 现在复用 backend 的数据 bundle 和 common 的 case-context 写回 helper；数据源切换、选中 case 持久化、live/local_fine 后的 session 回填已减少重复实现。

## 2026-04-07 术语说明统一

- `Design Explorer` 现在接入共享的“术语与结果来源”折叠块。
- 本页继续负责全局设计筛选，但不再单独维护一套对 `标准结果库 / live` 的解释文案，避免与其他 workflow 页漂移。
