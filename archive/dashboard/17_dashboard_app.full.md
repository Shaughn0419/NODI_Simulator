# dashboard/app.py — Streamlit 主入口

<!-- DOCSYNC:START -->
> 归档提示（2026-04-28）：本文保留历史快照，不覆盖现行代码事实。当前主线已更新到 EV/NODI relative design gate 拆分、detector caution 分层、calibrated BFP ROI mask 到 Tsuyama 1D projected ROI、完整 governance diagnostics 导出；验证基线为 `pytest -q` = `509 passed`，`ruff check .` / `pyright` 通过。现行结论以根目录 `README.md`、`文档导航.md`、`00/24/42/43` 和代码测试为准。
<!-- DOCSYNC:END -->

> 2026-04-08 复核：已按当前代码、当前 dashboard 导航结构与当前文档分层重新核对；如与更深层专题分析冲突，应以明确标注为“现行”的专题文档和同名代码说明为准。

> 2026-04-10 补充：`app.py` 当前主流程已默认面向 biomimetic exosome 全量库读取结果；标准 `data_prefix` 的首选目标已更新为 `fine_full_range_biomimetic_exosome_10000e`。


> 2026-04-07 补充：`app.py` 当前默认围绕标准 `fine_full_range_*` 结果库组织主流程，标准主库口径为 `404 / 488 / 532 / 660 nm`、`55296 cases`。



## 当前使用方式

- 文档定位：dashboard 入口说明
- 推荐阅读时机：当你要理解页面路由、三层导航和 session_state 边界时，优先读这份。
- 与代码的关系：如果你要继续落到具体实现，请同时对照对应的同名 `.md` 或直接查看相关代码文件。
- 建议搭配阅读：
- [dashboard/app.md](../../dashboard/app.md)
- [27_dashboard_common.full.md](./27_dashboard_common.full.md)
- [dashboard/panels/research_story.md](../../dashboard/panels/research_story.md)

## 文件职责

面板的唯一入口文件。负责两件事：
1. 初始化 `session_state`（全局状态）
2. 页面路由（根据侧边栏 radio 选择加载不同页面）

不包含任何业务逻辑或 UI 组件。

本轮重新核对后，`app.py` 的关键职责边界仍然成立：

- 真正的页面路由状态是 `dashboard_page`
- 侧边栏 radio 是当前唯一的页面切换入口
- `dashboard_page_radio` 继续保留为 widget 显示状态，`dashboard_page` 保留为路由状态，两者分离只是为了让状态同步更稳

---

## 启动方式

```bash
streamlit run dashboard/app.py
```

或通过启动脚本：
```bash
# macOS
./start_dashboard.command

# Windows
start_dashboard.bat
```

当前这两个启动脚本只负责：

- 找到可用的 Python + Streamlit 环境
- 检查当前标准结果库 `fine_full_range_biomimetic_exosome_10000e_*` 是否存在
- 如果缺失，只提示当前标准重算命令，不再自动触发旧的 coarse 预计算
- 启动 dashboard 并在端口冲突时自动换到下一个可用端口

---

## session_state 键定义

| 键 | 默认值 | 说明 |
|----|--------|------|
| `dashboard_page` | `Principle Guide` | 当前页面路由状态 |
| `dashboard_page_radio` | `Principle Guide` | 侧边栏 `radio` 的显示状态；与 `dashboard_page` 分离，避免 widget 状态与页面路由互相覆盖 |
| `selected_particle` | `None` | 当前选中的粒子名称 |
| `selected_wavelength_nm` | `None` | 当前选中的波长（nm） |
| `selected_W_nm` | `None` | 当前选中的通道宽度（nm） |
| `selected_H_nm` | `None` | 当前选中的通道深度（nm） |
| `case_cache` | `{}` | case detail 缓存，key=(particle, λ, W, H, tag) |
| `data_prefix` | 优先 `fine_full_range_biomimetic_exosome_10000e`，否则回退到可用的 `fine_fine_full_range_10000e / fine_full_range / fine_current_model_full_range / coarse_full_range / coarse_default` | 主流程预计算数据集前缀 |
| `using_live_data` | `False` | 是否使用 live 模式数据 |
| `sweep_df_live` | `None` | live sweep 的 DataFrame |
| `sweep_compact_live` | `None` | live sweep 的 compact list |
| `live_sim_cfg` | `None` | live 模式的 SimulationConfig |
| `live_optical` | `None` | live 模式的 OpticalSystem |
| `live_tag` | `None` | live 数据标识字符串 |

### 当前默认口径（2026-04-08）

- `app.py` 现在会优先把科研展示层路由到标准 `fine_full_range_*`
- 如果 session 里残留的是旧的 `coarse_default / coarse_full_range`，backend 同步阶段会自动迁移到标准 `fine_full_range` 前缀；这属于兼容修正，不代表旧前缀仍是当前默认阅读路径
- `Single-Case Calculator` 保留为独立计算页，不参与科研展示默认数据源选择

---

## 页面路由

| 页面 | 层级 | 来源 |
|------|------|------|
| Research Overview | 科研展示 | `panels/research_story.py` |
| Full-Range Conclusions | 科研展示 | `panels/research_story.py` |
| Focused 404 Analysis | 科研展示 | `panels/research_story.py` |
| Design Recommendations | 科研展示 | `panels/research_story.py` |
| Principle Guide | 证据与机理 | `panels/principles.py` |
| Mie Explorer | 证据与机理 | `panels/mie_explorer.py` |
| Interference Explorer | 证据与机理 | `panels/interference_explorer.py` |
| Noise & Detection Explorer | 证据与机理 | `panels/noise_detection_explorer.py` |
| Design Explorer | 证据与机理 | `panels/explorer.py` |
| Case Inspector | 证据与机理 | `panels/inspector.py` |
| Single-Case Calculator | 独立计算 | `panels/single_case_calculator.py` |

## 新的页面蓝图

当前 dashboard 已重构成三层导航：

1. `科研展示`
   - `Research Overview`
   - `Full-Range Conclusions`
   - `Focused 404 Analysis`
   - `Design Recommendations`
2. `证据与机理`
   - `Principle Guide`
   - `Mie Explorer`
   - `Interference Explorer`
   - `Noise & Detection Explorer`
   - `Design Explorer`
   - `Case Inspector`
3. `独立计算`
   - `Single-Case Calculator`

推荐第一次阅读顺序：

`Research Overview -> Full-Range Conclusions -> Focused 404 Analysis -> Design Recommendations`

如果需要解释证据链，再进入：

`Principle Guide -> Mie Explorer -> Interference Explorer -> Noise & Detection Explorer -> Design Explorer -> Case Inspector`

`Single-Case Calculator` 不属于科研展示主线，而是用来输入一个具体 case，逐阶段看完整计算链。
这页的页首结论当前已经固定成“人话 headline + 辅助状态行”的结构，不会直接把
`未分类`、`未判定` 或 `freeze=...` 这类内部状态码暴露成主结论。

### Mie Explorer 当前能力

- 纯 Mie 总览：`Csca / Cext / Cabs / Qsca / Qext / Qabs / size parameter`
- 固定任意角度 `theta` 的总览指标：`dCsca/dOmega @ theta`、`Esca amplitude @ theta`
- 多 case 角分布对比：主图为 `dCsca/dOmega(theta)`，`|S1|`、`|S2|` 收纳在高级视图
- 单变量固定角度扫描：固定粒径扫波长，或固定波长扫粒径；其中 dashboard 粒径输入统一为 `10 nm` 步进
- 折射率对比扫描：固定粒径 / 波长 / 角度后，扫描 relative index 实部
- 跨页联动：可继承最近一次在 Explorer / Inspector 中选中的粒径与波长，并支持一键同步到当前 Mie 参数
- 侧边栏分层：`主趋势分析` 放总览与单变量扫描，`高级分析` 放角分布、折射率灵敏度和单点明细
- 数值表后置：分材料、单变量扫描、折射率扫描、单点明细的表格都改成按需展开，主页面优先保留图形趋势
- 次级区块后置：`按材料细看` 与 `高级：折射率对比扫描` 默认折叠，避免主页面过长
- 进阶区块后置：`进阶：角分布对比` 与 `进阶：单点明细` 也默认折叠，主页面优先保留总览与固定角度扫描

### 页面体验优化

- `app.py`：默认页现在切到 `Research Overview`，并把侧边栏拆成 `科研展示 / 证据与机理 / 独立计算` 三层导航
- `dashboard/panels/common.py`：跨页工作流提示已进一步收成“当前页定位 + 当前页目标 + 可选展开科研展示主线”，不再把整套工作流卡片默认铺在每一页顶部
- 科研展示层和证据页都增加了“当前跨页上下文”摘要卡，持续显示当前粒子、波长，以及可用时的 W/H
- 页面内部不再提供“下一步建议”跳转按钮；切页统一回到侧边栏，页面本身只负责给出当前结论与读图解释
- 页首把工作流提示和上下文摘要卡合并成统一的 header hub，减少顶部信息分散
- `Design Explorer`：增加“这页怎么用”和各视图的阅读提示，强调先找平台区、再看切片稳健性；候选表与切片图现在严格跟随当前指标，`CV` 会按越小越好排序；侧边栏拆成 `日常筛选 / 高级调参` 两层；长说明默认折叠，主页面优先保留热图、候选和切片；热图指标现支持并列查看 `score / engineering_score / final_engineering_score`，并新增 `ROC-AUC / fixed-false-alarm hit rate / d′ / 局部 SNR / 平均 transit time / 双通道配对率` 这类更接近工程判别的指标，默认优先显示最终工程评分
- `Design Explorer`：live sweep 新增 `coarse / fine / local_fine` 网格选择；`coarse` 对应 `500 nm` 步长，适合第一轮粗筛，`fine` 对应全范围 `100 nm` 步长，`local_fine` 则围绕当前选中的 `W/H` 做局部 `100 nm` 细扫，更适合第二轮认真比较宽深差异
- `Design Explorer`：候选点概览下还新增了 `Top 3 -> local_fine` 快捷按钮，可以直接围绕前 3 个候选点中的任一个做局部细扫
- `Design Explorer`：右侧候选区默认先显示前 3 个候选，完整 Top 10 后置到按需展开
- `Case Inspector`：增加“这页怎么用”和成因/可信度/单事件 trace 的阅读顺序提示；首屏先给 verdict，再按需展开成因与可信度；快速判断摘要只保留 6 个关键量，完整物理表 / batch 表 / 全事件表后置
- `Mie Explorer`：每个视图都增加“看什么 / 怎么理解 / 实用建议”，并把 `|S1| / |S2|` 收到高级视图，主线优先聚焦 `dCsca/dOmega(theta)`；同时支持继承最近选中的 case 作为默认参数，侧边栏拆成 `主趋势分析 / 高级分析`
- `Interference Explorer`：新增 clean-signal 机制页，强调 `A_ref`、`E_sca normalized`、`|E_sca|^2` 与 `2Re(E_ref·E_sca*)` 的关系，并提供单变量放大扫描；现在还会明确显示当前使用的相位模型、检测角模型和等效检测角
- `Noise & Detection Explorer`：新增 detect/miss 机制页，强调 `clean / raw / readout / threshold` 对照、事件级 detect/miss 审核和 noise/threshold/velocity 扫描；现在首屏还会直接给出 `当前检测区间 / 主要瓶颈 / 优先比较`
- 这一轮又统一补上“趋势怎么读”的语言层：不仅告诉你哪个点最好，也明确区分“同一条件下谁更强”和“继续往哪个方向调参会更好”
- 同时也继续做了减法：`Design Explorer` 的当前点长明细、`Interference/Noise` 的扫描原始表、`Inspector` 的 batch 大表都已经从主路径移除
- `Design Explorer` 当前默认的热图浏览口径已经从 `final_engineering_score` 调整为 `engineering_score`，因为前者更适合切分 gate 通过/未通过，后者更适合看趋势和候选区间
- `Design Explorer` 现在进一步改成了“exosome 选型优先”的页面语义：当数据集中同时存在 `gold` 和 `exosome` 时，默认先落到 `exosome`，顶部趋势结论也会先回答 exosome 自己在什么波长和几何上更稳；gold 只保留为验证参考，不再和 exosome 平级争“谁更强”
- `Principle Guide`：增加按任务选择阅读路径的导航提示，并把术语速查与归一化/参考场细节收进高级附录；首屏先给摘要结论，不再一打开就进入长文档模式
- dashboard 各分析页当前统一采用“中文解释 + 符号”的展示口径，例如 `参考场幅值 (A_ref)`、`散射截面 (Csca)`、`检测阈值 (threshold)`，减少只暴露内部变量名带来的阅读负担

### 物理默认值更新

当前 dashboard 默认系统参数不再使用“固定 90° + 常相位”的最乐观近似，而是：

- `collection_angle_model="channel_diffraction"`
- `collection_integration_mode="pupil_slit_surrogate"`
- `scattering_projection_mode="parallel"`
- `phase_model="relative_surrogate"`
- `pulse_detection_mode="absolute"`
- `readout_model="lockin_surrogate"`
- `readout_observable_mode="in_phase"`

这意味着：
- 宽度 `W` 改变时，等效检测角 `theta_det` 会随之变化
- 检测链不再只取某一个角度点，而会围绕角谱中心做带权收集
- 干涉链不再只使用正实数散射幅值代理，而会保留一部分 Mie 复场相位
- 深度位置和沿流动方向的穿焦过程会共同改变散射场相位，从而不再默认所有事件都处于最大建设性干涉
- 负脉冲不会再因为“只找正峰”而被直接当成漏检；检测层会在 `|signal|` 上找峰，同时保留原始极性
- `Noise & Detection Explorer` 默认看到的是最小可用 lock-in surrogate 读出后的检测轨迹，而不是直接拿 raw noisy trace 做阈值
- 锁相读出默认以 in-phase 分量进入阈值层，但页面已经能切换到 magnitude 模式，并显式展示 I/Q 与包络的区别

此外，reference model 选择器默认会显示 `constant`、`geometry_scaled`
和 `channel_angular_surrogate`。当环境变量
`NODI_REFERENCE_CALIBRATION_PATH` 被设置为一份真实 blank-channel
标定表路径时，页面会额外开放 `calibrated_lookup` 选项，并把
dashboard 默认参考场模型切换为：
- 有真实标定表：`calibrated_lookup`
- 无真实标定表：`channel_angular_surrogate`
这样不会再直接回退到旧的幂律 surrogate。

### 新的后端支撑

- `dashboard/signal_backend.py`
  新增教学型信号链后端，专门为 `Interference Explorer` 和 `Noise & Detection Explorer` 产出：
  - 本征散射与参考场摘要
  - clean trace 分解
  - batch 事件表
  - 单事件 trace 数据
  - 单变量机制扫描数据

---

## 设计说明

- 使用 `st.set_page_config(layout="wide")` 启用宽屏布局
- 页面模块使用延迟导入（`if page == "..." : from ... import`），避免加载不需要的页面
- session_state 初始化使用 `if key not in` 模式，确保页面切换不丢失状态
- `dashboard_page` 与 `dashboard_page_radio` 现在显式分离：前者是路由状态，后者是 sidebar widget 状态。这样侧边栏选择和内部状态同步更稳，不会触发 Streamlit 的 widget state 冲突
- 页面注册源统一来自 `dashboard/panels/common.py` 的 `PAGE_OPTIONS`，避免侧边栏选项和页面实现分裂
- 2026-04-06 补充：`dashboard/app.py` 的 session 初始化已统一走 `dashboard.panels.common.initialize_dashboard_session_state()`；页面渲染也改成 `PAGE_RENDERERS` 注册表，避免主入口继续维护长 `elif` 路由链。

## 2026-04-07 阶段 C 收口补记

- `app.py` 的主入口职责已经进一步明确：
  - 科研展示层 = 标准 `fine_full_range_*` 默认阅读路径
  - `Single-Case Calculator` = 独立计算页
- 统一状态边界后，科研展示与证据页只消费标准结果库 case，上游工程调试参数不再混入默认解释链。
