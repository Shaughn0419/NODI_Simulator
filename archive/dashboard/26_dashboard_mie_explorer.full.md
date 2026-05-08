# dashboard/panels/mie_explorer.py — Mie Explorer

<!-- ARCHIVE_STATUS:START -->
> 归档状态：历史快照，仅保留当时推理、实验性计算或迁移记录；不代表当前 v1/v2 结论。当前读者入口请以 `README.md`、`文档导航.md`、`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`、`reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` 和 `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` 为准。
<!-- ARCHIVE_STATUS:END -->

> 2026-04-08 复核：已按当前代码、当前 dashboard 导航结构与当前文档分层重新核对；如与更深层专题分析冲突，应以明确标注为“现行”的专题文档和同名代码说明为准。

> 2026-04-07 补充：Mie Explorer 当前默认围绕四波长 `404 / 488 / 532 / 660 nm` 解释本征散射，并与标准 `fine_full_range_*` 结果库结论对齐。

> 阶段 B 更新（2026-04-07）：`Mie Explorer` 已开始从“相对独立的 Mie 说明页”向“标准结果库中的本征散射解释页”收口。页面现在会优先把当前选中 case 锚定到标准 `fine_full_range_*` 结果库，并在页首显示 recommendation / gate / detection / freeze 这组结果库结论；其主要职责变成解释“这个 case 在进入 reference、noise 和 gate 之前，本征散射处在什么位置”。 

## 当前使用方式

- 文档定位：Mie Explorer 专题
- 推荐阅读时机：当你要解释本征散射、角分布和固定角度量在 dashboard 中的角色时，读这份。
- 与代码的关系：如果你要继续落到具体实现，请同时对照对应的同名 `.md` 或直接查看相关代码文件。
- 建议搭配阅读：
- [dashboard/panels/mie_explorer.md](../../dashboard/panels/mie_explorer.md)
- [22_dashboard_interference_explorer.full.md](./22_dashboard_interference_explorer.full.md)
- [25_核心计算逻辑与公式总说明.md](../../25_核心计算逻辑与公式总说明.md)

## 作用

`Mie Explorer` 只看粒子的本征 Mie 散射，不引入 reference field、clean signal、噪声或检测阈值。它回答的是：

- 粒径变大以后，`Csca / Qsca / size parameter` 怎么变
- 固定角度下的 `dCsca/dOmega` 或 `Esca amplitude` 怎么变
- 不同材料、不同波长、不同粒径下的角分布差异在哪里

这页是整条 dashboard 学习链路里的第一步：

`Principle Guide -> Mie Explorer -> Interference Explorer -> Noise & Detection Explorer -> Design Explorer -> Case Inspector`

当前页面已经取消正文里的跨页跳转按钮，改成在总览图和统计表之后直接给出“本页结论”，优先说明在当前筛选下究竟是哪组材料 / 粒径 / 波长在本征散射指标上占优。
最近这一轮又往前推进了一步：总览图下面新增了“怎么看当前这张图”，不再只报哪个点最高，而会直接解释：

- 当前曲线总体是“随粒径增大而上升”，还是“不同曲线会交叉”
- 现在看的量更像“总量”还是“效率”
- 如果目标是后续检测，为什么固定角度量通常比总截面更值得优先看
- 现在还会明确区分“纵向比较同一粒径下谁更高”和“横向看单条曲线随粒径怎么变”，避免把两种问题混在一起
- 最近这一轮之后，总览图还会再明确给出 `这张图先回答什么 / 先看哪种比较 / 最容易误读什么`，让用户一眼知道当前纵轴适不适合拿来判断后续检测

## 当前粒径逻辑

从 2026-04-03 起，Mie Explorer 与 dashboard 其它页面统一使用同一套粒径口径：

- 支持范围：`40–300 nm`
- 输入步进：`10 nm`
- 默认值：`100 nm`
- 若从其它页面同步进来的粒径不在 10nm 网格上，会先被 snap 到最近的 `10 nm`

这一规则由 [config.py](../../dashboard/config.py) 里的共享 helper 负责：

- `snap_diameter_nm()`
- `diameter_values_between()`
- `DASHBOARD_DIAMETER_STEP_NM`

同时，Mie Explorer 的高频界面标签也已改成中文主标签：

- `粒径范围`
- `单变量扫描`
- `折射率对比扫描`
- `相对折射率实部 / 虚部`

## 页面结构

### 1. 主页面

- `Mie 总览`
  - 选择材料、粒径范围、波长、固定角度 `theta`
  - 输出 `Csca / Cext / Cabs / Qsca / Qext / Qabs / dCsca/dOmega @ theta / Esca amplitude @ theta`
- `单变量扫描`
  - 扫描轴支持 `wavelength_nm` 或 `diameter_nm`
  - 其中粒径扫描现在统一走 `40, 50, ..., 300 nm`

主页面现在刻意只保留这两条主线：先看总览，再看单变量。这样一打开页面时，不会同时被角分布、折射率扫描和单点明细分散注意力。
其中 `Mie 总览` 现在又多了一层“趋势翻译”：

- `Csca / Cext / Cabs`：解释成“整体有多会散、会吸”
- `Qsca / Qext / Qabs`：解释成“单位几何面积是不是更高效”
- 固定角度量：解释成“探测器那个方向究竟能收到多少”

这样用户不需要先懂 Mie 术语，也能知道当前该怎么读图。

### 2. 高级浏览

- `角分布对比`
  - 粒径候选列表来自当前粒径范围内的 `10 nm` 网格
- `折射率对比扫描`
  - 固定粒径、固定波长、固定角度，对 `relative index real` 做敏感性分析
- `单 case 明细`
  - 展示当前材料、粒径、波长对应的关键 Mie 量

这三部分现在统一收进一个“高级分析：角分布 / 折射率 / 单点明细”展开区，只有在你已经看完主线、需要进一步核对角分布或单点数值时再展开。

## 关键函数

### `_resolve_linked_mie_defaults()`

读取跨页面同步状态：

- `selected_particle`
- `selected_wavelength_nm`

并把粒径默认值 snap 到 dashboard 统一的 `10 nm` 网格。

### `_summary_df_cached()`

调用 `dashboard/mie_backend.py::build_mie_summary_dataframe()`，生成总览图所需的批量 Mie 数据。

### `_angular_df_cached()`

调用 `build_mie_angular_dataframe()`，生成角分布图。

### `render_mie_explorer()`

主渲染函数，负责：

- 初始化 linked defaults
- 构建 sidebar 控件
- 触发总览、角分布、固定角度扫描、折射率扫描和单 case 明细

## 与其它页面的边界

- 本页只看本征散射，不看 `A_ref`
- 不看 `clean signal`
- 不看 `noise / threshold / detect`
- 不看最终 `score`

所以如果这里看到某个粒径/波长组合散射很强，也不等于它一定会在完整系统里拿到最高分。下一页 [interference_explorer.py](../../dashboard/panels/interference_explorer.py) 才开始回答 reference field 如何把本征散射变成 clean pulse。

## 当前总览图怎么读

- 如果曲线整体随粒径增大而升高：
  说明“粒子变大”本身就在增强本征散射，这是最常见的趋势
- 如果不同波长或材料曲线交叉：
  说明“最优波长 / 最优材料”会依赖粒径，不能给一个全局唯一答案
- 如果你看的是 `Qsca` 这类效率：
  重点是“是否进入更高效的散射区”，而不是探测器最终能收多少信号
- 如果你看的是 `dCsca/dOmega @ theta` 或 `Esca amplitude @ theta`：
  这比总截面更贴近后续系统页，因为后续检测并不是收全空间散射，而是收某个角谱方向上的那一部分

最近这一轮之后，这里又把“看图动作”拆得更明确了：

- **先纵向比高低**：同一粒径下哪条曲线更高，回答“谁更强”
- **再横向看斜率**：同一条曲线随粒径怎么变，回答“继续变大还会不会更好”

这样用户不需要先自己判断“我是该看高低还是看斜率”，页面已经把这两层问题拆开了。

另外，页面当前会优先使用“中文解释 + 符号”的口径来显示关键量，例如：

- `散射截面 (Csca)`
- `散射效率 (Qsca)`
- `固定角散射截面 (dCsca/dOmega @ theta)`
- `固定角散射场幅值 (Esca @ theta)`

这样可以把“这是什么量”和“它在代码里的符号”同时交代清楚。
## 2026-04-07 D / E 收口

- `Mie Explorer` 现在也和其他主流程页共用结果库锚点说明模板。
- 本页已明确改成“标准结果库中的本征散射解释页”，不再作为独立自由计算页使用。
- live 参数如果仍留在 session 中，只作为工程调试上下文保留；本页主流程解读以上方标准结果库锚点为准。

## 2026-04-07 来源提示统一

- `Mie Explorer` 页头现在通过共享 helper 渲染：workflow 锚点摘要、标准结果库 / live 来源提示、当前跨页选中 case 的导入说明。
- 同时新增统一的“术语与结果来源”折叠块，明确本页只解释本征散射，不替代后续 reference / noise / gate 页面。
