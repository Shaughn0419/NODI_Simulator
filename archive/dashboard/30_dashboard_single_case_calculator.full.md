# dashboard/panels/single_case_calculator.py — 单案例全链路计算页

<!-- DOCSYNC:START -->
> 归档提示（2026-04-28）：本文保留历史快照，不覆盖现行代码事实。当前主线已更新到 EV/NODI relative design gate 拆分、detector caution 分层、calibrated BFP ROI mask 到 Tsuyama 1D projected ROI、完整 governance diagnostics 导出；验证基线为 `pytest -q` = `509 passed`，`ruff check .` / `pyright` 通过。现行结论以根目录 `README.md`、`文档导航.md`、`00/24/42/43` 和代码测试为准。
<!-- DOCSYNC:END -->

> 2026-04-08 复核：已按当前代码、当前 dashboard 导航结构与当前文档分层重新核对；如与更深层专题分析冲突，应以明确标注为“现行”的专题文档和同名代码说明为准。


> 2026-04-07 补充：当前单案例计算页是独立计算页，不替代科研展示层基于 `fine_full_range_*` 的标准结果解释；主库口径已升级为 `404 / 488 / 532 / 660 nm`。



## 当前使用方式

- 文档定位：单案例计算页专题
- 推荐阅读时机：当你要理解独立计算页的定位、阶段展示和与主展示的边界时，读这份。
- 与代码的关系：如果你要继续落到具体实现，请同时对照对应的同名 `.md` 或直接查看相关代码文件。
- 建议搭配阅读：
- [dashboard/panels/single_case_calculator.md](../../dashboard/panels/single_case_calculator.md)
- [dashboard/app.md](../../dashboard/app.md)
- [archive/dashboard/29_dashboard_single_case_calculator.md](./29_dashboard_single_case_calculator.md)

## 页面定位

这页是**独立计算页**，不属于当前科研展示主线。

它不是用来做：

- 全局热图筛选
- 候选排序
- sweep 排名

而是用来做：

- 单个 case 的完整计算剖面
- 逐阶段解释这个 case 为什么得到当前结果
- 把物理链、检测链和工程解释接在同一页里

## 输入区

当前主输入为：

- `粒子类型`
- `粒径 (nm)`
- `激光波长 (nm)`
- `通道宽度 W (nm)`
- `通道深度 H (nm)`
- `batch 事件数`

高级设置当前只开放少量关键量：

- `参考场比例因子 (rho)`
- `读出噪声标准差 (noise_std)`
- `阈值倍数 (threshold_sigma)`
- `流速`
- `启用布朗扩散`

从 2026-04-12 这轮开始，这些默认值直接继承 `dashboard/config.py::DEFAULT_SIM_CFG`。因此单案例页、预计算和 dashboard live backend 现在使用的是同一套标准 dashboard 默认，而不是分别回退到不同入口的默认值。

## 科学边界

当前模型直接使用的几何自由度是：

- `W`：通道宽度
- `H`：通道深度

因此这页明确写成 `W/H` 输入，而不是模糊写“通道长和宽”。

## 页面结构

页面分成两部分：

### 顶部

- 输入表单
- `计算当前案例`
- `本页结论`

其中 `本页结论` 当前已经固定遵守两条显示规则：

- 页首 headline 必须优先用人话给出判断，例如“当前案例可作为候选，但建议先复核”“当前案例更适合作为观察或对照对象”
- recommendation / gate / freeze 的原始状态只能作为辅助判定行出现，不应直接把 `未分类`、`未判定` 或 `freeze=caution_probe_before_result_freeze` 这类内部状态码暴露成主结论

另外，这一块现在还会再补一层“状态与原因”解释：

- 一句 `当前主要瓶颈 / 当前主要状态`
- 一句 `为什么这样判断`
- 三条短摘要，分别回答：
  - `本征散射现在是偏强还是偏弱`
  - `参考放大现在是有效还是偏弱`
  - `读出链现在是稳健还是仍有限制`

目标是让读者一眼分清：当前 case 到底主要卡在本征散射、参考放大，还是读出链。

### 下方结果流

每一段都固定为：

- 左边：这个阶段在算什么
- 右边：这个阶段的结果

当前结果显示这轮又额外做了两点收口：

- 阶段结果不再用默认 `st.metric`，而是改成更窄、更能换行的紧凑结果卡片
- 数值会优先按科研阅读习惯切到更稳的科学计数法 / 紧凑小数显示，避免长数字在页面里被截断或挤坏布局
- 展示层的核心指标统一改成“中文解释 + 符号”口径，例如 `参考场幅值 (A_ref)`、`本征散射截面 (Csca)`、`检测阈值 (threshold)`，避免页面直接暴露内部变量名
- 每一段右侧结果又统一加了一层“关键看什么 / 当前怎么判断 / 先警惕什么”，不再只给数字和一句结论
- 需要画图的阶段现在都会额外标明“这张图先回答什么 / 先看哪里 / 什么趋势更好”，关键主峰位置也会用定位线标出来
- 10 个阶段现在进一步分成“建议先读的主线阶段”和“补充阶段”，主页面先保留真正决定判断的主链，补充背景收进折叠区

并且从上到下严格按当前主链排列。

## 当前阶段顺序

1. `输入与当前假设`
2. `粒子与 Mie 本征散射`
3. `检测几何与收集`
4. `参考场`
5. `轨迹与照明`
6. `散射场与相位分解`
7. `干涉 clean signal`
8. `噪声、读出与阈值`
9. `批量统计`
10. `工程解释与最终结论`

其中 Stage 4（页面标题里的 `参考场`）这轮又补了一层专门的 `rho` 审计：

- 不会静默改写用户输入的 `rho`
- 会把当前 case 按 `requested / lower / nominal / upper` 四个 anchor 额外重算
- 页面上会直接显示：
  - `当前 rho / nominal rho`
  - `rho probe 结论`
  - `包络内检出率漂移`
- 这一层的职责不是替代实验标定，而是把“当前 case 的绝对结论到底对 rho 有多敏感”变成页面可读结论

同时，single-case stage report 现在还会把这层 probe 结果显式带回 backend：

- `rho_sensitivity_df`
- `rho_sensitivity_summary`

因此这页当前已经不只是“看当前 rho 是否出界”，而是可以回答：

- 把 `rho` 拉回 nominal 后，当前 case 的 detection / stable detection 会不会明显变
- 当前 case 更接近“包络内且稳”，还是“包络外且敏感”

## 当前后端组织方式

页面没有重写另一套物理链，而是复用了当前已有后端：

- `build_case_inputs(...)`
- `compute_interference_case(...)`
- `compute_noise_detection_case(...)`
- `build_event_trace_dataframe(...)`

并在此基础上新增：

- `build_single_case_stage_report(...)`

这个 helper 的职责是把现有结果整理成“可按阶段展示”的 report，而不是重写 physics 公式。

当前这层 report 还会在直接计算模式下自动回填：

- `design_recommendation_*`
- `engineering_gate_*`
- `decision_summary_*`

因此单独计算页不会因为没有先经过结果库加载流程，就把推荐标签或工程门槛显示成占位词。

页面渲染当前也固定遵守一个顺序：先从 `report["stages"]` 取出有序阶段列表，再渲染页首导读和主/补充分组，避免页面层和 stage report 的顺序语义脱节。

## 当前适用场景

这页最适合：

- 你已经有一个具体 case，想知道它为什么强 / 为什么弱
- 你想把 clean trace、noisy trace、threshold、batch judgement 放在同一页看
- 你想把 `Inspector` 的总结和前面物理链真正连起来

它不适合替代：

- `Design Explorer`
- `Interference Explorer`
- `Noise & Detection Explorer`

因为它的目标不是扫空间，而是讲清一个 case。
