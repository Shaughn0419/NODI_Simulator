# 单案例计算页设计框架

<!-- DOCSYNC:START -->
> 归档提示（2026-04-28）：本文保留历史快照，不覆盖现行代码事实。当前主线已更新到 EV/NODI relative design gate 拆分、detector caution 分层、calibrated BFP ROI mask 到 Tsuyama 1D projected ROI、完整 governance diagnostics 导出；验证基线为 `pytest -q` = `509 passed`，`ruff check .` / `pyright` 通过。现行结论以根目录 `README.md`、`文档导航.md`、`00/24/42/43` 和代码测试为准。
<!-- DOCSYNC:END -->

> 文档状态：设计草案。当前单案例页已经实现；如果你要理解或维护现行实现，请优先查看 [dashboard/panels/single_case_calculator.md](../../dashboard/panels/single_case_calculator.md)。

> 2026-04-07 补充：当前单案例计算页定位为流程外 live 工具页，前 6 页主流程默认围绕标准 `fine_full_range_*` 结果库展开；标准主库口径为 `404 / 488 / 532 / 660 nm`、`55296 cases`。


> 设计状态（2026-04-06）：本文基于当前完整计算核心、当前 dashboard 页结构，以及当前 `signal_backend / backend / mie_backend` 已有能力整理而成。它不是新的 physics 路线图，而是一个**流程外的单案例计算页**设计框架，用于把“输入一个具体 case，逐阶段看结果”做成独立页面。当前仍处于设计阶段，尚未开始写该页面的 Python 代码。

---

## 1. 页面目标

这页的目标不是“帮用户在大参数空间里选最优设计”，而是：

**给定一个具体粒子 + 波长 + 通道几何，沿着当前完整计算链从上到下展示每个重要阶段的原理与结果。**

也就是说，它回答的问题是：

1. 这个 case 在当前模型里到底是怎么一步步算出来的？
2. 每个阶段各自贡献了什么？
3. 最终为什么会得到这样的 clean signal、detect / miss、engineering judgement？

因此这页应当与当前 6 步工作流分离：

- 现有 6 页：强调“分析流程”
- 新页：强调“单个 case 的全链路计算剖面”

它应该是一个**独立工具页**，而不是再塞进 `Principle -> ... -> Inspector` 那条主工作流里。

---

## 2. 科学边界与命名约束

### 2.1 必须先写清的边界

当前核心模型直接使用的几何自由度是：

- `W`：通道宽度
- `H`：通道深度 / 高度

**当前主链并没有把“通道长度 L”作为独立光学自由度进入计算核心。**

因此页面输入不能写成模糊的“通道长和宽”，而应在 UI 中明确写成：

- `通道宽度 W`
- `通道深度 H`

如果后续真的要引入“通道长度”，那属于另一条物理扩展，不应在这页里假装已经被当前模型精确建模。

### 2.2 这页不是哪几种东西

这页**不是**：

- 新的 sweep / ranking 页面
- 新的结果排序页面
- 新的局部 fine-scan 页面
- 简化版 Inspector

这页应该是：

- `单 case`
- `单次点击计算`
- `逐阶段展开`
- `原理在左，结果在右`
- `从上到下的计算链`

### 2.3 命名展示规范

这页不应直接把内部变量名裸露给用户，而应统一采用：

- **中文解释 + 符号**

也就是优先写成：

- `参考场幅值 (A_ref)`
- `散射截面 (Csca)`
- `归一化散射场幅值 (E_sca)`
- `等效检测角 (theta_det)`
- `检测阈值 (threshold)`

而不是只写：

- `A_ref`
- `Csca`
- `E_sca`
- `theta_det`
- `threshold`

这样用户在第一次看页面时，能同时知道：

1. 这个量的物理意义
2. 它在代码和公式中的符号

因此这页的输入标签、阶段指标、图例、阅读提示和结论文案，都应尽量遵守同一套命名口径。

---

## 3. 用户输入框架

### 3.1 第一层：核心输入

第一版建议只放最关键、最稳定的输入：

1. `粒子类型`
   - `gold`
   - `exosome`

2. `粒径 (nm)`

3. `激光波长 (nm)`

4. `通道宽度 W (nm)`

5. `通道深度 H (nm)`

6. `计算` 按钮

### 3.2 第二层：高级参数

为了不把页面做复杂，建议默认折叠到“高级设置”里，只在需要时展开：

- `reference_model`
- `rho`
- `noise_std`
- `threshold_sigma`
- `mean_flow_velocity`
- `include_diffusion`
- `n_events`

第一版不建议把所有 dashboard 调参项都开放，否则这页又会变成第二个 live tuning 面板。

### 3.3 默认值建议

默认目标应当与当前项目目标一致：

- 默认粒子类型：`exosome`
- 默认粒径：`100 nm`
- 默认波长：使用当前冻结结果里对 exosome 更稳的那一档，作为默认起点
- 默认 `W/H`：使用当前 exosome 候选区中较稳的一组，而不是全库 rank 1 的 gold 点

这样这页一打开就是“服务 exosome”的，不会被 gold 验证视角带偏。

---

## 4. 页面结构

整页建议分成两大区：

### A. 顶部：输入与总判断

顺序建议为：

1. 输入区
2. `计算` 按钮
3. `本页结论`
4. 一句当前 case 的核心判断

例如：

- 当前 case 更像 `reference-dominated heterodyne` 还是 `intrinsic-scattering dominated`
- 当前 detect 风险主要卡在 `threshold / bandwidth / phase flip / gate`
- 当前 case 更适合作为 `最终候选 / 机制验证 / 边界 case`

### B. 下方：逐阶段结果流

每一段固定使用两列：

- 左列：这个阶段的原理、公式、要点
- 右列：这个阶段的实际计算结果、图、表、结论

并且从上到下严格按照当前计算链排列。

---

## 5. 逐阶段展示框架

建议采用 9 段主链，顺序不要打乱。

### Stage 0. 输入与当前假设

左边：

- 当前输入项是什么
- 当前使用了哪些默认模型
- 哪些量是当前没有展开给用户改的，但在后台已固定

右边：

- 粒子 / 波长 / W / H
- reference / phase / overlap / readout 等当前主链默认值
- observation signature

### Stage 1. 粒子与 Mie 本征散射

左边：

- 尺寸参数 `x = 2π a n_m / λ`
- 当前粒子更接近 Rayleigh、过渡区还是 Mie 区
- 本阶段只回答“粒子本身会散射成什么样”，不含参考场、不含噪声

右边：

- `Csca / Cext / Cabs / Qsca`
- `dCsca/dΩ(θ_det)` 或代表角度值
- `S1 / S2` 主投影幅值与相位
- 一张最关键的小图

这里的展示名应优先写成：

- `散射截面 (Csca)`
- `消光截面 (Cext)`
- `吸收截面 (Cabs)`
- `散射效率 (Qsca)`
- `角分辨散射截面 (dCsca/dΩ)`

### Stage 2. 检测几何与收集

左边：

- 当前 `theta_det` 怎么确定
- 当前收集算子是 fixed 还是 channel-diffraction / pupil-slit surrogate
- 这一步只回答“散射有多少真的进了检测链”

右边：

- `theta_det`
- collection operator 摘要
- detected scattering amplitude
- 如有必要给出一个极简角谱示意图

这里的展示名应优先写成：

- `等效检测角 (theta_det)`
- `检测面散射场幅值 (E_sca@det)`

### Stage 3. 参考场

左边：

- 参考场来自什么模型
- `rho` 和 `phase grating / width saturation` 各在控制什么
- 这一步只回答“参考场强不强、相位怎么来”

右边：

- `A_ref`
- `g_ref`
- `phi_ref`
- `rho` 包络状态
- `requested / nominal rho`
- `rho probe` 结论（例如“包络内且稳 / 包络外且敏感”）
- 包络内 `detection rate` 漂移量
- width saturation 状态

这里的展示名应优先写成：

- `参考场幅值 (A_ref)`
- `参考场几何缩放 (g_ref)`
- `参考场比例因子 (rho)`

补充说明：

- 当前实现不会静默重写用户输入的 `rho`
- 但会额外运行一个 `rho` probe：把当前 case 按 `requested / lower /
  nominal / upper` 四个 anchor 重新计算
- probe 结果会被压缩成一句可读判断，用来回答“这个 case 的绝对结论到底有多依赖 rho”
- 当 `sim_cfg.random_seed` 没有显式提供时，single-case report 会对这组
  probe 使用固定 fallback seed，避免把 case 之间的差异和随机抽样噪声混在一起

### Stage 4. 轨迹与照明

左边：

- 粒子在光束中如何经过
- diffusion / advection / beam envelope 在这一阶段分别干什么
- 这一步只回答“粒子是否在好位置、好时间里被照到”

右边：

- transit time
- representative trajectory
- illumination envelope
- 一张 `position / A_env` 简图

### Stage 5. 散射场与相位分解

左边：

- `phi_sca_material`
- `phi_sca_path`
- `phi_beam_gouy / phi_beam_curv`
- 这一步只回答“散射场本身为什么是这个相位和振幅”

右边：

- `A_sca`
- `phi_material`
- `phi_path_x / phi_path_z`
- `delta_phi_gouy`
- 相位构成条目

这里的展示名应优先写成：

- `材料散射相位 (phi_material)`
- `横向路径相位 (phi_path_x)`
- `深度路径相位 (phi_path_z)`
- `差分 Gouy 相位 (delta_phi_gouy)`

### Stage 6. 干涉 clean signal

左边：

- `|E_sca|^2 + 2 Re(E_ref E_sca*)`
- 当前是 heterodyne 放大主导，还是 `|E_sca|^2` 抬头主导
- overlap / projection / freeze 在这里分别意味着什么

右边：

- clean trace
- peak cross-term
- peak intrinsic term
- overlap factor
- 一句“真变好 / 假变好”的判断

这里的展示名应优先写成：

- `干净信号 (clean signal)`
- `干涉交叉项峰值 (peak cross-term)`
- `散射平方项峰值 (peak |E_sca|^2)`
- `角谱重叠因子 (overlap factor)`

### Stage 7. 噪声、读出与阈值

左边：

- raw noise、shot-noise surrogate、lock-in surrogate、threshold 各自的位置
- 这一步只回答“有信号后，读出链会不会把它吃掉”

右边：

- noisy trace
- threshold
- local SNR
- NODI bandwidth gain
- 带宽受限 / 阈值受限判断

这里的展示名应优先写成：

- `加噪轨迹 (noisy trace)`
- `检测阈值 (threshold)`
- `局部信噪比 (local SNR)`

### Stage 8. 检出与 batch 统计

左边：

- 为什么单事件强不代表 batch 一定稳
- 为什么要同时看 stable detection / phase flip / paired detection

右边：

- detection rate
- stable detection rate
- phase flip fraction
- paired detection rate
- mean peak metrics

### Stage 9. 工程解释与最终结论

左边：

- 最后如何把 physics / detection / gate / recommendation 汇总
- 这一步给的是工程判断，不是物理公式本身

右边：

- design recommendation
- engineering gate explanation
- decision summary
- 结论建议：
  - `适合作为 exosome 候选`
  - `适合作为机制验证`
  - `物理可研究但工程门槛未过`

---

## 6. 结果展示风格

### 6.1 每个阶段都必须回答一个问题

不能只是“放一张图”。

每段都必须显式回答：

- 这一阶段在算什么？
- 当前这个 case 在这一阶段好不好？
- 这一阶段的结果会怎么传给下一阶段？

### 6.2 每段都要有一句结论

除了图和表，每段右侧必须有一句人话结论，例如：

- “本征散射不弱，但主要提升来自参考场而不是粒子本身。”
- “当前 `A_ref / A_sca` 仍处于 heterodyne 友好区。”
- “clean peak 足够高，但经过 readout 后主要被阈值吃掉。”

### 6.3 严禁一上来塞长表

这页的科学价值在于“理解流程”，不是“导出所有字段”。

因此每个阶段：

- 主区只显示最关键 3–6 个量
- 若需要完整字段，再放到该阶段的展开区

---

## 7. 需要复用的现有后端

当前代码已经有大量可复用能力，不应重写第二套计算链。

建议优先复用：

- `dashboard/mie_backend.py`
- `dashboard/signal_backend.py`
- `dashboard/backend.py`
- `run_single_case_batch`
- `compute_interference_case`
- `compute_noise_detection_case`
- `build_case_decision_summary`

真正缺的不是底层计算，而是一个**把这些结果组织成逐阶段 report 的统一 helper**。

建议新增一个中间层 helper，例如：

- `build_single_case_stage_report(...)`

它的职责不是重新计算所有物理，而是把现有后端结果整理成：

- `input_summary`
- `mie_stage`
- `collection_stage`
- `reference_stage`
- `trajectory_stage`
- `scattering_stage`
- `interference_stage`
- `readout_stage`
- `batch_stage`
- `final_decision_stage`

---

## 8. 页面注册与路由建议

因为用户明确说“在这个流程之外，单独加一页”，所以建议：

### 不要做成第 7 步

不要把它加进 `WORKFLOW_STEPS`。

### 建议做法

在 sidebar 页面列表中单独分组或单独标注：

- 主流程页面：
  - Principle Guide
  - Mie Explorer
  - Interference Explorer
  - Noise & Detection Explorer
  - Design Explorer
  - Case Inspector

- 独立工具页面：
  - Single-Case Calculator

这样不会破坏当前已经梳理好的 6 步主流程。

---

## 9. 实现顺序建议

### Step 1

先做后端组织层：

- `build_single_case_stage_report()`

先把阶段结构定住，不急着做页面细节。

### Step 2

再做新页面：

- `dashboard/panels/single_case_calculator.py`

第一版先保证：

- 输入稳定
- 计算按钮稳定
- 9 段主链都能出结果

### Step 3

最后再做页面层美化：

- 每阶段的结论文案
- 每阶段的小图
- 展开区和高级字段

---

## 10. 测试要求

新增页面后，至少补三类测试：

1. **后端结构测试**
   - `stage_report` 是否包含所有阶段
   - 每阶段关键字段是否存在

2. **页面 smoke test**
   - 输入默认值后页面是否能正常运行
   - 点击计算后是否出现阶段结果

3. **边界测试**
   - exosome 默认值是否正确
   - 用户输入非法几何时是否有清晰报错
   - 页面不会把“通道长度”伪装成当前模型已有变量

---

## 11. 当前建议结论

这页是值得加的，而且很适合现在这个阶段加。

原因不是“又多一个 dashboard 页面”，而是：

- 当前计算核心已经足够完整
- 现在最缺的不是新的 physics，而是一个能把全链路算例讲清楚的单案例剖面页
- 它会明显降低“为什么这个 case 会这样”的理解成本

最重要的设计原则只有一条：

**它必须服务“理解一个 case 是怎么被算出来的”，而不是变成另一个排序页。**

## 2026-04-07 阶段 C

- `Single-Case Calculator` 已明确收口为独立工具页，不再与前 6 页 workflow 混在一起。
- 它使用自己独立的 session 状态：`single_case_*`
- 它可以导入当前 workflow case 作为默认值，但不会回写 `selected_particle / wavelength / W / H`
- 它承担的是单案例 live 计算，不负责替代前 6 页围绕 `fine_full_range_*` 的标准结果库分析。

## 2026-04-07 阶段 C 收口

- 旧的 legacy single-case 实现已经删除，不再保留双实现并存。
- 当前 single-case 页面只保留一套正式入口，并与 workflow 状态做了明确隔离。
