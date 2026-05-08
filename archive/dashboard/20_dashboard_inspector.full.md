# dashboard/panels/inspector.py — Case Inspector 页面

<!-- ARCHIVE_STATUS:START -->
> 归档状态：历史快照，仅保留当时推理、实验性计算或迁移记录；不代表当前 v1/v2 结论。当前读者入口请以 `README.md`、`文档导航.md`、`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`、`reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` 和 `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` 为准。
<!-- ARCHIVE_STATUS:END -->

> 2026-04-08 复核：已按当前代码、当前 dashboard 导航结构与当前文档分层重新核对；如与更深层专题分析冲突，应以明确标注为“现行”的专题文档和同名代码说明为准。

> 2026-04-07 补充：当前 Inspector 默认读取标准 `fine_full_range_*` 主库，所展示的 case 结论与上下文均以四波长 `404 / 488 / 532 / 660 nm` 结果库为准。

> 补充说明（2026-04-03）：Inspector 的摘要卡、batch 指标名和 live 参数提示已统一改成中文主标签，例如“评分 / 稳健评分 / 检出率 / 平均峰高 / 峰宽”。

## 当前使用方式

- 文档定位：Case Inspector 专题
- 推荐阅读时机：当你要理解单点 verdict、机制统计和 trace 复核逻辑时，读这份。
- 与代码的关系：如果你要继续落到具体实现，请同时对照对应的同名 `.md` 或直接查看相关代码文件。
- 建议搭配阅读：
- [dashboard/panels/inspector.md](../../dashboard/panels/inspector.md)
- [19_dashboard_explorer.full.md](./19_dashboard_explorer.full.md)
- [23_dashboard_noise_detection_explorer.full.md](./23_dashboard_noise_detection_explorer.full.md)

## 文件职责

剖析单个 case 的详情。提供两级视图：
- **Summary View**（默认）：从 compact 数据读取，显示摘要卡片 + 本页结论 + 关键判断量 + 物理分解 + 直方图
- **Detail View**（按需）：点击按钮后运行 `run_case_on_demand`（5–10 秒），显示单事件 trace + 事件统计表

> 阶段 A 更新（2026-04-07）：`Case Inspector` 现在默认按标准 `fine_full_range_*` 结果库解释单个 case；如果 session 中存在 live 数据，会被明确标记为“工程调试口径”，不再和主流程标准结果库混淆。

页面顶部现在会先显示跨页工作流提示，告诉用户这一页更适合在 Design Explorer 选出候选点之后使用。

---

## 页面布局

```

页面还新增了两层阅读引导：
- **全页引导**：`这页怎么用`，强调先看 summary/成因，再看分布，最后看单事件 trace；现在默认折叠，避免一打开页面先被说明占满
- **视图引导**：Score 成因分析、物理分解、峰高/峰宽分布、单事件详情前都会提示“看什么 / 怎么理解”
- **本页结论**：在评分成因分析与可信度判断之后，页面会直接归纳当前 case 是“默认推荐”“需复核推荐”还是“当前不建议”
- **当前跨页上下文**：在页首持续显示统一样式的摘要卡，展示当前粒子、波长、W、H，避免分析到一半忘记当前 case

最近又做了两层减法：

- **成因与可信度后置**：`评分成因分析` 和 `结果可信度` 现在合并进 `为什么这么判断：评分成因与可信度` 展开区，首屏先给 verdict，再按需看解释
- **快速判断摘要**：主页面优先保留 `Csca / E_sca/E_ref / 主导因素 / 稳定检出率 / 稳健 CV / 峰高 z-margin`
- **趋势语言补充**：快速判断摘要下面现在还会直接解释“什么变化代表更可信、什么变化代表只是边缘事件在托底”，不再只给状态词
- **判断模板补充**：`本页结论` 下方现在还会直接给出 `什么样的点更值得信 / 什么样的点是假好点 / 先信什么证据` 三条短判断
- **扩展 batch 指标后置**：`ROC-AUC / 局部 SNR / paired rate / 正负峰均值` 统一收进 `查看扩展 batch 判断指标`
- **细表后置**：`Case 固有物理量表`、`Batch 统计结果表`、`全部事件统计表` 都改成按需展开
- **Batch 大表已删除**：最近这一轮又进一步删掉了 `Batch 统计结果表`，主页面只保留关键判断量、扩展指标、直方图和单事件 trace
- **工程判别补充**：摘要和 batch 表现在还会额外显示 `mean_local_snr / mean_transit_time / single_channel_detection_rate / paired_channel_detection_rate / paired_channel_stable_detection_rate / strict_paired_detection_rate_wilson_lb / paired_detection_rate / ROC-AUC / d′`，帮助区分“信号弱”“停留时间短”和“双通道不一致”
- **极性分组补充**：摘要和 batch 表现在还会额外显示 `mean_positive_peak_height / mean_negative_peak_height / positive_peak_fraction / negative_peak_fraction`，帮助区分“平均峰高低”到底是整体偏弱，还是正负峰互相抵消
- **strict paired gate 补充**：当工程口径启用了 `engineering_min_strict_paired_detection_rate` 时，摘要会直接显示要求值与当前 Wilson 下界，方便判断“不是没检出，而是严格双通道确认还不够稳”
- **工程 basis 补充**：Inspector 现在还会显示 `engineering_decision_basis / engineering_gate_basis`，用于区分“最终 detect/miss 怎么定义”和“工程排序到底按 final、single 还是 paired 在审”
- **事件级观测链补充**：Detail View 现在还会显示局部 `A_ref`、`Δφ_ref`、`phi_material`、`phi_projection`、`phi_path_x` 与 `phi_path_z`，方便核对这次事件里究竟是“材料散射相位”、还是“宽度/深度方向的路径差”在驱动当前 pulse
- **reference / shot-noise sanity 补充**：Case Physics 现在还会显示 `reference model tier / geometry_scaled depth exponent / mean I_baseline / mean shot-noise std / shot-noise baseline-dominated fraction / mean |E_ref|/|E_sca|`，方便判断当前 case 的 reference surrogate 和噪声层是否仍在合理物理边界内
- **rho 物理包络补充**：Case Physics 现在还会显示 `rho requested / rho envelope nominal / rho envelope lower / rho envelope upper / rho ratio-to-nominal / rho envelope status / reference first-order diffraction efficiency`，方便判断当前 `rho` 是否已经明显偏离 reference-side phase-grating 给出的最小量级区间
- **窄通道 width-saturation 补充**：Case Physics 现在还会显示 `reference width saturation mode / status / effective width / saturation factor`，方便判断当前 reference 的 width 向角谱是否已经进入 `W ≲ λ_eff` 的 soft-cutoff 区间
- **偏振基底补充**：Case Physics 现在还会显示 `scattering projection basis / reference projection basis / reference-scattering basis match / reference projection coupling status`，方便确认当前 reference 干涉到底是不是“同基底满幅”，还是“同基底但被泄漏压低”
- **freeze judgement 补充**：Case Physics 现在还会显示 `interference overlap freeze status / projection freeze status / delta_phi_gouy validity / observation freeze status`，方便判断当前 case 是“已经能进入结果冻结”，还是仍处于 `review_required_before_result_freeze`
- **推荐标签补充**：Summary View / Case Physics 现在还会显示 `design_recommendation_label / design_recommendation_status`，把“推荐（默认）”“推荐（需复核）”“可研究（门槛未过）”这几类结果先在解释层拆开
- **gate 解释补充**：Summary View / Batch 表现在还会显示 `engineering_gate_primary_blocker_label / engineering_gate_blocker_summary / engineering_gate_guidance`，把“没过门槛”进一步拆成“主要卡点是什么、下一步先查什么”
- **统一决策摘要补充**：Summary View 的 physics breakdown 顶部现在还会先显示 `decision_summary` callout，把 recommendation / gate / freeze 三层解释压成一块统一摘要，并明确给出 `headline / blocker_text / next_step`
- **旧结果兼容补充**：如果当前读取的是早于这轮解释层实现的 `compact.pkl`，backend 会在加载时自动补齐 `design_recommendation_*` 与 `engineering_gate_*` 字段，所以 Summary View / Case Physics 仍能直接展示最新解释，不需要先重跑 full-range
- **结果库健康补充**：Summary View 顶部现在还会额外提示当前结果库的整体健康状态，例如 `ready 占比 / shared-beam caution 占比 / rho 包络外 case 数`，避免用户只盯着当前 case 而忽略它所处结果库的整体稳定性
┌────────────────────────────────────────────────────────────┐
│  [数据来源标识栏]（标准 full-range 结果库 / 工程调试 live）  │
├────────────────────────────────────────────────────────────┤
│  Case 摘要卡片（6 列 metric）                              │
│  Score | Robust | Det Rate | Mean Height | Std | Width    │
├────────────────────────────────────────────────────────────┤
│  本页结论                                                  │
│  [为什么这么判断：评分成因与可信度]（按需展开）            │
├────────────────────────────────────────────────────────────┤
│  ┌── Case 物理量 ──┐  ┌── 峰高直方图 ──┐                │
│  │ Csca, E_sca    │  │               │                │
│  │ g_ref, A_ref   │  ├───────────────┤                │
│  │ E_sca/E_ref    │  │ 峰宽直方图    │                │
│  │ 主导因素        │  │               │                │
│  ├── Batch 统计 ──┤  │               │                │
│  │ 关键判断 6 指标 │  │               │                │
│  └────────────────┘  └───────────────┘                │
├────────────────────────────────────────────────────────────┤
│  [重算此 Case 详情（当前结果库口径）]                      │
│  Detail View（按钮触发后显示）                             │
│  ┌── Trace 图 ──┐  ┌── 事件统计表 ──┐                   │
│  │ clean+noisy  │  │ x₀,z₀,det    │                   │
│  │ +threshold   │  │ height,width  │                   │
│  │              │  │ local A_ref   │                   │
│  │              │  │ Δφ_ref range  │                   │
│  │              │  │ phi_material  │                   │
│  │              │  │ phi_projection│                   │
│  │ [事件滑块]   │  │               │                   │
│  └──────────────┘  └───────────────┘                   │
└────────────────────────────────────────────────────────────┘
```

---

## Score 成因分析（v8 新增）

调用 `get_score_explanation(case)` 自动判断：

| 输出 | 说明 |
|------|------|
| `explanation` | 中文描述（如"此设计高分主要由 reference 增强主导"） |
| `dominant_factor` | `scattering` / `reference` / `coupling` / `balanced` |
| `trust_level` | `high` / `medium` / `low` |
| `trust_reason` | 可信度原因（如"检出率极低 → 信号可能在噪声以下"） |
| `E_sca_E_ref_ratio` | 散射场/参考场比值 |

可信度用彩色标签显示：绿(高)、橙(中)、红(低)。

---

## 物理分解表增强

在 `build_physics_breakdown` 的基础上，Inspector 额外添加两行：
- **E_sca / E_ref ratio** — 直接量化散射 vs 参考场
- **信号主导因素** — 散射主导 / 参考场主导 / 耦合主导 / 均衡

当前 Inspector 的 physics breakdown 也会直接显示：

- `path OPD model / reference plane / z geometry factor`
- `path OPD default model / model role / default frozen / freeze status`

因此在单 case 复盘时，已经可以直接看出当前 `phi_sca_path_z` 是默认冻结主线，
还是仅用于对照审查的 roundtrip surrogate。

在这之上，Inspector 现在又多了一层“最终怎么解释这个 case”的稳定归约：

- `decision_summary_tone`
- `decision_summary_headline`
- `decision_summary_primary_message`
- `decision_summary_blocker_text`
- `decision_summary_next_step`

因此当前页面默认阅读顺序已经收口成：

1. 先看 `decision_summary` 判断这是推荐点、谨慎点、边界点还是冻结未就绪点
2. 再看 `为什么这么判断：评分成因与可信度`
3. 然后看 `Case 固有物理量` 和 `快速判断摘要`
4. 最后进入 Detail View 看具体事件

最近这一轮之后，`快速判断摘要` 的阅读方式已经进一步收口成：

- `稳定检出率` 越高，越说明不是靠少数幸运事件撑住
- `稳健 CV` 越低，越说明参数稍微扰动时结果更能保持
- `峰高 z-margin` 越高，越说明这个点不是刚好压线
- `E_sca/E_ref + 主导因素` 用来判断“高分更像粒子本身够强”，还是“高分主要靠 reference 放大”

同时，Inspector 当前也把高频指标逐步统一成“中文解释 + 符号”的展示口径，例如：

- `散射截面 (Csca)`
- `散射场/参考场比值 (E_sca / E_ref)`
- `局部参考场幅值 (A_ref)`
- `参考相位差 (Δφ_ref)`
- `材料散射相位 (phi_material)`
- `投影后相位 (phi_projection)`

这样顶部摘要、physics breakdown 和单事件详情的命名风格就不会再割裂。

---

## case_cache 机制

缓存 key = `(particle, λ, W, H, data_tag)`，其中 `data_tag` 为 live_tag 或 data_prefix。

| 事件 | 是否清空 cache | 原因 |
|------|---------------|------|
| live sweep 重跑 | 是 | 物理参数变了 |
| 恢复预计算 | 是 | 数据源变了 |
| 仅切换页面 | 否 | 数据未变 |
| 拖动事件滑块 | 否 | 同一 case 内 |

---

## Detail 来源标注

```python
if using_live_data:
    st.caption("📌 Detail 来源：基于当前 live 参数重算 [live_tag]")
else:
    st.caption("📌 Detail 来源：基于预计算默认参数重算 [data_prefix]")
```

Summary 区域也会显示来源：
- live 模式：`Summary 来源：当前 live sweep 结果 [live_tag]`
- 默认模式：`Summary 来源：预计算结果 [data_prefix]`

现在 Summary 区域还会继续显示一条结果库级 caption：

- `当前结果库健康：ready=... | shared-beam caution=... | rho 包络外=...`
- `当前子组健康：波长 ...nm -> ready / gate通过；材料 ... -> ready / shared-beam caution`

这条信息同样来自 `load_result_health()`：

- 新结果库优先读取 `*_result_health.json`
- 旧结果库若还没有该文件，则按当前 `summary_df` 即时补齐

也就是说 Inspector 现在既能看整库健康，也能看到“当前 case 所在波长”和“当前粒子类型”这两个子组的健康状态，而不必回 Explorer 再做一次对照。

---

## 依赖关系

- **导入**：`backend.py`（数据加载、case 查找、物理分解、按需重算）、`config.py`（CHART_HELP、CHART_HELP_FULL、get_score_explanation）
- **读取**：`session_state`（selected_particle, selected_wavelength_nm, selected_W_nm, selected_H_nm, using_live_data, live_tag, case_cache）

---

## 2026-04-03 文案补充

- Summary 区块说明已统一为“当前汇总来源”。
- `Score 成因分析` 已统一为“评分成因分析”。
- 峰高/峰宽直方图坐标轴已统一为“峰高 / 峰宽 (ms)”与“数量”。
- 单事件轨迹图的轴标题已统一为“时间 (ms)”与“信号 (a.u.)”，阈值标注也改为中文“阈值”。
- Detail View 事件表现在还会额外显示 `phi_material / phi_projection`，用于把“材料本征相位”和“探测投影相位”区分开审查。
- 2026-04-06 补充：`Case Inspector` 现在复用统一的数据 bundle/source captions/cache tag helper，不再自己维护一套 live-vs-precomputed 加载与 detail 来源说明逻辑。
## 2026-04-07 D / E 收口

- `Case Inspector` 现在复用 `format_case_verdict_caption()`，把顶部 verdict 文案和主 verdict 条统一到一套字段模板。
- 这样 `design_recommendation / engineering_gate / observation_freeze / primary_blocker` 的组合说明只维护一份，不再在 Inspector 内手写多套近似文案。

## 2026-04-07 术语说明统一

- `Case Inspector` 现在接入共享的“术语与结果来源”折叠块。
- 这页的口径已经统一为：围绕标准结果库中的单个候选点做最终复盘；detail 重算只负责按当前结果库口径复查，不改变 workflow 结论来源。
