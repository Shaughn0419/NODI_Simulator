# dashboard/panels/common.py 说明

<!-- DOCSYNC:START -->
> 归档提示（2026-04-28）：本文保留历史快照，不覆盖现行代码事实。当前主线已更新到 EV/NODI relative design gate 拆分、detector caution 分层、calibrated BFP ROI mask 到 Tsuyama 1D projected ROI、完整 governance diagnostics 导出；验证基线为 `pytest -q` = `509 passed`，`ruff check .` / `pyright` 通过。现行结论以根目录 `README.md`、`文档导航.md`、`00/24/42/43` 和代码测试为准。
<!-- DOCSYNC:END -->

> 2026-04-08 复核：已按当前代码、当前 dashboard 导航结构与当前文档分层重新核对；如与更深层专题分析冲突，应以明确标注为“现行”的专题文档和同名代码说明为准。


> 2026-04-07 补充：`common.py` 维护的 workflow 共享状态，当前默认服务于标准 `fine_full_range_*` 主库；相关 case context 与 workflow 提示都应按 `404 / 488 / 532 / 660 nm` 口径理解。



## 当前使用方式

- 文档定位：dashboard 共享语义专题
- 推荐阅读时机：当你要统一页面口径、header、workflow helper 和术语边界时，读这份。
- 与代码的关系：如果你要继续落到具体实现，请同时对照对应的同名 `.md` 或直接查看相关代码文件。
- 建议搭配阅读：
- [dashboard/panels/common.md](../../dashboard/panels/common.md)
- [17_dashboard_app.full.md](./17_dashboard_app.full.md)
- `21_dashboard_principles.md`（历史草案未归档到当前工作区）

## 作用

`dashboard/panels/common.py` 负责 dashboard 多页面共用的引导与上下文展示逻辑，主要包括：

- 工作流步骤定义 `WORKFLOW_STEPS`
- 独立计算页定义 `CALCULATOR_PAGES`
- 当前 case 上下文构建 `build_case_context()`
- 顶部工作流条与上下文条渲染
- 侧边栏页面说明 `render_sidebar_page_guide()`

## 2026-04-03 当前口径

- 工作流说明统一采用中文优先表述。
- `Interference Explorer` 的目标说明已改为“把本征散射接到参考场上，看 clean signal 为什么会被放大”。
- `Noise & Detection Explorer` 的目标说明已改为“再看加噪、阈值和检出，理解为什么有信号不一定能被检出”。
- 顶部工作流块标题已从 `Step N` 改为“第 N 步”。
- 页面内部的“下一步建议”跳转按钮已经整体移除；现在统一通过侧边栏切页，`common.py` 只保留工作流提示和跨页上下文。
- 顶部 header hub 现在把“当前页定位 + 当前目标 + 可选展开完整科研展示主线”收成统一结构，避免每页首屏都被重复工作流卡片占满。
- 当前 sidebar 页面结构已经分成两类：
  - 主流程页面：`Principle -> ... -> Inspector`
  - 独立计算页：`Single-Case Calculator`
  这样独立计算工具不会被误解成 workflow 的第 7 步。

## 说明

- 页面内部路由名仍保持英文，如 `Design Explorer`、`Case Inspector`。这部分同时承担页面标识和侧边栏选项值，不建议在展示层之外改名。
- `render_workflow_banner()` 当前优先回答“我现在在科研展示链的什么位置、这一页主要回答什么”，完整主线则收进折叠区，属于低频辅助信息。
- `render_page_header_hub()` 当前也把更多宽度让给跨页上下文摘要卡，因为对连续分析来说，当前粒子 / 波长 / W / H 往往比完整工作流图更高频。
- 2026-04-06 补充：`dashboard/panels/common.py` 已扩展为 dashboard 共享状态入口，统一提供 session 默认值初始化、当前选中 case 的读写以及当前数据源 tag，减少跨页面状态约定漂移。
## 2026-04-07 D / E 收口

- `common.py` 现在承担统一的结果库锚点说明模板，新增：
  - `format_case_verdict_caption()`
  - `render_workflow_anchor_summary()`
  - `render_workflow_source_notice()`
- 这三个 helper 的目标是把科研展示层与证据页里重复出现的 `recommendation / gate / freeze / blocker / source` 说明统一成单一实现。
- 统一后，页面层不再各自手写一套锚点卡片和 live-vs-standard 提示，减少字段漂移和措辞分叉。

## 2026-04-07 阶段 C

- `common.py` 继续承担科研展示、证据页与独立计算页的共享 UI 语义：
  - 新增 `render_auxiliary_page_header()`
  - `render_current_context_bar()` 支持自定义标题与引导文案
- shared session defaults 现在已经纳入 `single_case_*`，用于把 single-case 状态与 workflow 的 `selected_*` 明确拆开。

## 2026-04-07 术语与来源说明收口

- 新增共享 helper `render_workflow_case_source_panel()`：统一处理 workflow 页顶部的锚点摘要、结果来源提示、跨页选中 case 提示。
- 新增共享 helper `render_workflow_terms_expander()`：统一解释 `标准结果库`、`当前选中 case`、`工程调试 live`、`结果来源提示` 这几类术语边界。
- 各页面现在不再各自维护一套近似但不完全一致的来源说明文案；后续若调整导航或 workflow 口径，应优先修改这里的共享 helper。
