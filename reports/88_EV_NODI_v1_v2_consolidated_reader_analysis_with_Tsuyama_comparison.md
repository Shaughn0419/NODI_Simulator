# EV/NODI v1+v2 综合分析报告：无实测、面向真实仪器约束的模拟补强与 Tsuyama 文献对照

日期：2026-05-11
版本：v3.0（合并 realism v2 收口 + post-v2 P0-P18）
报告性质：读者向综合分析报告
适用口径：无实测数据、合成相对先验模型、面向真实仪器约束的模拟补强，以及 post-v2 审计/有界 trace 证据

---

## 0. 读者须知

这份报告不是实验报告，也不是仪器校准报告。

这里的 v2 指的是一条 **没有实测数据、但把真实仪器和真实工程约束考虑得更充分的模拟补强线**。2026-05-11 之后，本报告还合并了 post-v2 P0-P18 的审计、物理上限诊断、solver-readiness、六条有界 trace lane 和停止/继续裁决。它们共同把原有两条结果口径接起来：

1. 原来的工程逻辑：从散射、参考场、干涉增强、读出、事件级 pulse 到设计筛选。
2. 原来的全量模拟结果：`32,032` 个基础设计组合、每个组合 `10,000` 次合成事件的相对设计筛选库。

v2 增加的是仪器情景约束、路线角色锁定、空白样本和热效应旁路保护、近壁网格判据、窄通道运输风险先验，以及后续仍缺哪些物理证据的清单。post-v2 P0-P18 增加的是可审计的相对路线裁决链、review package provenance、P1/P2 readiness scaffold、P3-P5/P7/P9/P11/P13/P15/P17 授权门、P6/P8/P10/P12/P14/P16 六条窄范围 deterministic trace，以及 P18 的 stop-or-continue synthesis。它们没有增加真实采集数据，也没有把任何结果升级为校准后的信噪比、校准后的事件概率、绝对检出限、真实 EV 浓度或生物特异性。

数据覆盖范围：

```text
v1 full-grid library = 32,032 基础设计组合，每个组合 10,000 次合成事件
v2 supplement = R0/R2/R3/R4/R5/R6/R7/R7.1/R7.2/no-measured-data closure
post-v2 P0 audit = 572 个路线聚合审计行，覆盖 404/488/532/660 nm 各 143 个唯一 route aggregate
post-v2 P6-P16 bounded traces = 6 条 trace-only lane，均只覆盖 P4/P6 选定的 3 条路线
实测数据 = 0
```

因此，本文所有“更可信”“更真实”的意思都是：

```text
更符合仪器和工程约束的相对模拟判断
```

不是：

```text
已经被真实仪器采集或真实样品实验验证
```

---

执行摘要：

这份报告回答 6 个问题。

1. 原工程主线和原全量模拟做完后，还差什么？答：差仪器现实约束、空白样本风险、读出语义、路线角色边界、窄通道风险先验和证据缺口清单。
2. v2 在不引入实测的前提下能补到哪一步？答：补到“当前模型还缺哪些物理或仪器证据”的登记表；不能补到任何校准或绝对量级结论。
3. 660 nm 主路线在 v2 之后还成立吗？答：在当前无实测、受限先验模型内仍成立，锁定为 660 nm、800 nm 宽、1400/1500 nm 深的两条主路线。
4. 弱参考场路线和窄深上下文路线为什么一度看起来更高？答：更可能是窄通道工程风险在原模型中被低估；本报告用低自由度宽度风险先验解释，不把它升级为物理定律。
5. Tsuyama 论文支持到了什么程度？答：3 篇对当前 NODI 主线约束强，3 篇主要提供 POD/热效应边界；当前是趋势和固定条件对齐，不是论文数值的完整校准复现。
6. post-v2 P0-P18 改变了什么？答：P0 把路线裁决做成可复核的相对审计包；P1/P2 把后续物理上限/solver readiness 做成不执行 solver 的合同；P6-P16 的六条有界 trace 没有支持 route promotion，反而显示 `main_660_W800_D1400` 与 `main_660_W800_D1500` 的 trace-only 首位在不同 lane 间切换；P18 因此停止机械式继续滚 lane，要求先做 P19 evidence-strategy gate。

读完整份报告大约需要 30-40 分钟。如果只想看结论，请读第 1 节、第 8 节、第 12 节和第 13 节。

---

## 1. 总结结论

当前 v2 已经完成其无实测数据范围内的修改和收口。最强结论可以写成：

```text
在受限的无实测合成先验模型内，
660 nm 主路线仍保持为治理锁定的主路线集合；
弱参考场路线和窄深上下文路线一度高分的现象，
可以被低自由度的窄通道工程风险先验稳定解释；
post-v2 P0-P18 没有支持任何 route promotion 或 calibration claim；
这些结论是相对模拟/相对审计判断，不是实测校准。
```

主路线状态：

| 项目 | 当前结论 | 技术证据来源 |
|---|---|---|
| 660 nm 主路线 | 800 nm 宽、1400 nm 深；800 nm 宽、1500 nm 深 | v2 路线治理收口表 |
| post-v2 后的主路线裁决 | 两条 main-660 仍是 `conditional_relative_main`；二者不能被 P6-P16 trace 分出单一冠军 | P0 audit + P18 synthesis |
| 是否允许其它路线直接升级为主路线 | 否 | v2 closure + P0 audit + P18 synthesis |
| 是否允许重新定义 660 nm 主路线 | 否 | 同上 |
| 660 nm、900 nm 宽、1400 nm 深路线 | 只作为 `optional_robustness_probe_only`，不作为主路线替代 | v2 路线治理收口表 + P0 audit |
| 404 nm、600 nm 宽、1300 nm 深路线 | 只作为 `probe_only` 短波机制路线；P6-P16 trace 中始终排第 3 | P0 audit + P6/P8/P10/P12/P14/P16 trace |
| 弱参考场 660 nm、700 nm 宽、1500 nm 深路线 | 只作为 `relative_control_candidate` / weak-reference control | P0 audit |
| 局部环带窗口 | 只作为并行诊断视角，不替代全局路线排序 | 同上 |
| 404 nm 热效应旁路 | 只作为安全和机制风险提示，不给 NODI 光学分数加分 | 404 nm 热效应旁路汇总表 |
| 当前最终模型类别 | 无实测、合成相对先验 + post-v2 relative-audit / trace-only scaffold | v2 结论边界收口表 + P0-P18 |
| 实测数据 | 未使用 | 同上 |
| 校准信噪比 / 校准事件概率 | 禁止 | 同上 |

Tsuyama 文献对照的最终判断：

1. **2020 diffraction、2022 NODI、2024 POD+NODI** 对当前 NODI/EV 工程主线有直接约束。当前模型在参考场、660 nm 主波长、读出口径和事件级脉冲方向上与这些论文趋势明显趋同。
2. **2019 POD、2020 counting POD、2020 solvent-enhanced POD** 对 POD thermal / photothermal / solvent / heat-diffusion 支线有重要边界意义，但不能直接拿来校准 EV NODI scattering detectability。
3. 当前模型对 Tsuyama 的对齐是 **机制与趋势对齐、固定论文条件下的对照、以及部分金颗粒读出口径对照**。它不是所有论文图表的逐式复现，也不是论文数值的校准复现。

---

## 2. 原始模拟做了什么，v2 为什么需要补

原来的主工程线已经完成了大规模相对模拟计算。它的价值是：

- 枚举大量波长、通道宽度、通道深度、颗粒类型和读出口径；
- 给出设计筛选用的相对排序；
- 保留全局交叉判据作为主工程排序口径；
- 用局部环带窗口作为并行交叉检查，而不是替代全局排序；
- 用接近 Tsuyama 条件的金颗粒对照和论文条件对照做文献趋势复核。

但原来的模拟也有天然边界：

1. 探测器、锁相放大器、后焦面、狭缝和针孔读出仍有近似成分；
2. 空白样本、相对强度噪声、50 欧姆读出路径、外置跨阻放大器、采集分辨率和热效应旁路等现实仪器问题没有充分进入主判断；
3. 近壁条件、网格精度和粗筛结果在路线决策中的角色需要裁决；
4. 某些上下文路线偶尔高于锁定主路线时，需要区分真实物理趋势、先验模型偏差和路线治理边界；
5. 没有实测空白样本、金颗粒阶梯、后焦面读出算子、制程计量或 EV 样品数据，所以不能输出绝对量级结论。

v2 的目的正是补这些 **工程现实性**，而不是重新做一个“看起来更贴论文的过拟合版本”。

---

## 3. v2 相比原模拟新增了什么

### 3.1 仪器链路显式化

v2 把原来比较抽象的读出和探测器部分拆成更接近实验系统的约束：

| 新增层 | 作用 |
|---|---|
| 从散射截面到实际光功率和局部照度 | 避免只在散射截面层做判断 |
| 后焦面、狭缝、针孔和读出区域 | 把论文里的衍射光区域和孔径选择纳入模型 |
| 探测器连接状态 | 防止把未知接线方式当作已校准通道 |
| 锁相放大器读出约束 | 限制时间常数、等效噪声带宽、满量程和饱和等解释空间 |
| 激光调制、强度噪声、光束和采集链路 | 把现实噪声和采集链路风险作为情景先验 |
| 空白样本和罕见假阳性先验 | 防止把有限空白样本误写成安全性证明 |

这些新增层没有提供真实测量值，但它们能约束原模型不要越过仪器现实边界。

### 3.2 路线角色治理和结论边界

v2 最重要的一条治理线是：模拟分数高不等于路线升级。

v2 全量仪器情景扩展发现：

| 路线类别 | 合成评估行数 | 平均相对可检测性分数 |
|---|---:|---:|
| 弱参考场控制路线 | 448 | 0.152257 |
| 锁定的 660 nm 主路线 | 896 | 0.126095 |
| 可选的 660 nm 稳健性探针 | 448 | 0.123041 |
| 长波局部环带交叉检查路线 | 1344 | 0.100906 |
| 中波基线路线 | 896 | 0.077653 |
| 大范围上下文路线 | 250432 | 0.070901 |
| 短波机制候选路线 | 448 | 0.044475 |
| 短波局部环带交叉检查路线 | 1344 | 0.040433 |

这里最容易被误读的是：弱参考场控制路线的平均分高于锁定的 660 nm 主路线。v2 没有把它升级成主路线，而是把它作为一个需要解释的警告，进入后续的路线角色稳定性、情景先验和宽度风险敏感性分析。

### 3.3 660 nm 主路线的近壁粗筛裁决

前一轮近壁复核曾暴露出：660 nm 主路线在粗网格筛查、近壁应力条件下没有达到全部判据。随后只针对两条锁定主路线做细网格复核：660 nm、800 nm 宽、1400 nm 深；以及 660 nm、800 nm 宽、1500 nm 深。

近壁细网格复核结论：

```text
细网格确认通过比例 = 1.0
复核级网格通过比例 = 1.0
细网格与复核级网格一致性 = 1.0
```

因此，粗网格筛查结果被保留为“只提示风险”的筛查警告，不再作为降低路线角色的证据。660 nm 主路线在复核级网格上的证据得到恢复。

### 3.4 全量仪器情景扩展

v2 没有重新做随机事件级扩展，而是把原有基础设计组合放入 8 个受限仪器情景中做确定性扩展：

```text
基础设计组合 = 32,032
仪器情景 = 8
随机种子 = 0
扩展后的合成评估行 = 256,256
```

8 个仪器情景分别代表：

- 标称仪器和干净空白样本；
- 50 欧姆探测器路径的悲观情况；
- 外置跨阻放大器的乐观情况；
- 空白样本中存在突发强度噪声的情况；
- 后焦面/狭缝偏移带来的泄漏风险；
- PEG 或近壁损失更悲观的情况；
- 404 nm 热效应风险较高、功率较低的情况；
- 数据采集分辨率较低的情况。

这些情景是为了观察路线角色稳定性和仪器先验敏感性，不是为了生成真实事件概率。

### 3.5 弱参考场和窄深路线警告，以及宽度风险解释

受限情景先验审计发现：

```text
弱参考场控制路线在 8 / 8 个仪器情景中高于 660 nm 主路线
20 / 20 条高分上下文路线在全部 8 个仪器情景中高于 660 nm 主路线
```

这说明警告是系统性的，不是某个仪器情景的偶然异常。

后续测试进一步追问：这些警告是否必须靠“逐条路线手工调参”才能解释。结果是，不需要。一个低自由度的窄通道风险先验已经足够解释：

下面这张表的读法：

- **主路线保留比例**：引入宽度风险先验后，660 nm 主路线平均分相对原结果的保留比例。`1.000` 表示没有被压低，`0.886` 表示保留到原值的 88.6%。
- **上下文路线越线数**：20 条高分上下文路线在引入先验后仍高于 660 nm 主路线的条数。`0` 表示这类警告完全消失。
- **弱参考场是否仍越线**：弱参考场控制路线在引入先验后是否仍高于 660 nm 主路线。`0` 表示已不再越线。

我们要找的是同时满足“主路线不被明显压低”“高分上下文路线不再越线”“弱参考场控制路线不再越线”的低自由度先验。这样的先验既能解释系统性警告，又不会人为打压主路线。

| 宽度风险解释模型 | 解释等级 | 参考宽度 | 惩罚强度 | 主路线保留比例 | 上下文路线越线数 | 弱参考场越线数 |
|---|---|---:|---:|---:|---:|---:|
| 以 800 nm 为参考、1.5 次方的温和宽度惩罚 | 可接受解释 | 800 nm | 1.5 | 1.000 | 0 | 0 |
| 以 800 nm 为参考、2.0 次方的二次宽度惩罚 | 可接受解释 | 800 nm | 2.0 | 1.000 | 0 | 0 |
| 以 850 nm 为参考、2.0 次方的稍强宽度惩罚 | 可接受但需谨慎 | 850 nm | 2.0 | 0.886 | 0 | 0 |

宽度风险敏感性分析同时说明：

- 以 800 nm 为参考的线性惩罚太弱；
- 以 750 nm 为参考的二次惩罚太弱；
- 以 900 nm 为参考的二次惩罚能压掉弱参考场和上下文路线警告，但代价有两个：
  - （a）660 nm 主路线保留比例从 `1.0` 降到 `0.79`，对主路线惩罚明显；
  - （b）压低后的 660 nm 主路线反而被 660 nm、900 nm 宽、1400 nm 深的可选探针路线越过，路线治理边界会被动摇。
  - 因此本报告把 900 nm 参考宽度的二次惩罚视为过强模型，不作为可接受解释；
- 单独使用参考场工作带惩罚或后焦面/狭缝对准风险，均不足以解释警告。

这支持的科学解释是：

```text
弱参考场和窄深路线的高分警告，很可能来自原模型低估了窄通道工程风险。
```

它不支持：

```text
(W / 800)^2 就是真实物理定律。
```

### 3.6 机制分解与证据缺口

后续机制分解把宽度风险先验拆成更像物理机制的候选解释：

| 机制家族 | 当前 v2 内状态 |
|---|---|
| 颗粒与壁面的间隙、PEG 层和近壁运输 | 可用已有模拟字段做相对先验近似 |
| 运输存活、堵塞和样品通量风险 | 可用已有模拟字段做相对先验近似 |
| 参考场工作范围、饱和和噪声裕度 | 需要后续独立的仪器或算子证据 |
| 后焦面、狭缝和读出区域对准 | 需要后续独立的算子输出或扫描证据 |
| 制程和计量裕度 | 需要后续独立的计量或工艺窗口证据 |
| 不同颗粒类别的残余差异 | 只能报告残余，不能做逐颗粒经验拟合 |

最终收口把这些整理为 6 类证据缺口、共 30 个必需字段。v2 closure 明确：这些是后续独立项目才可能解决的依赖，不是 v2 内的采集计划。

---

## 4. v1+v2 现在怎样接回原口径

v2 并没有推翻 v1。更准确地说：

```text
v1 = 大规模相对设计筛选库
v2 = 面向真实仪器和工程约束的模拟补强
```

接回后的读法如下：

| 原始口径 | v2 后的读法 |
|---|---|
| 全局交叉排序 | 仍是主工程排序，不被局部环带窗口替代 |
| 局部环带窗口 | 只作为并行诊断视角，不能替代全局排序 |
| 660 nm 主路线 | 仍锁定 800 nm 宽、1400/1500 nm 深两条路线 |
| 404 / 532 / 488 nm 路线 | 作为机制、上下文或旁路对照，不直接升级为主路线 |
| Tsuyama 论文条件对照 | 用于文献趋势和读出口径复核，不等于论文数值校准复现 |
| 可检测性分数 | 相对先验分数，不是事件概率 |
| 类似计数的字段 | 合成代理计数，不是实际观察到的检测事件 |

660 nm 主路线两条几何的 v2 汇总：

| 路线 | 近壁细网格证据 | 细网格通过比例 | 复核网格通过比例 | 合成评估行数 | 平均相对可检测性分数 |
|---|---|---:|---:|---:|---:|
| 660 nm、800 nm 宽、1400 nm 深 | 已继承 | 1.0 | 1.0 | 448 | 0.125190 |
| 660 nm、800 nm 宽、1500 nm 深 | 已继承 | 1.0 | 1.0 | 448 | 0.127001 |

这不是说 800x1400 / 800x1500 是物理上唯一正确路线，而是说：在当前无实测、受限 v2 先验模型内，它们仍是治理锁定的 660 nm 主路线比较基准。

---

## 5. Tsuyama 文献对照总览

本项目共纳入 6 篇 Tsuyama / Mawatari 相关论文。它们对当前模型的约束强度并不相同。

| 论文 | 对当前主线的约束强度 | 当前对照方式 | 结论 |
|---|---|---|---|
| 2019 POD 分子检测 | 中 | POD 热效应边界和衍射光读出区域 | 支持衍射光区域与小通道 POD 可行性；不直接校准 EV NODI |
| 2020 单纳米通道衍射 | 高 | 固定 633 nm 的衍射和参考场对照 | 参考场、宽度和深度趋势强对齐 |
| 2020 POD 纳米颗粒计数 | 中 | POD 计数边界和流动/读出时间尺度 | 支持毫秒级瞬态和金颗粒 POD 可检测性；不能外推为 NODI 散射校准 |
| 2020 溶剂增强 POD | 中 | 热效应和溶剂边界 | 支持溶剂、光热和符号翻转边界；当前 v2 不做热效应 POD 定量 |
| 2022 NODI | 高 | 接近论文条件的 NODI 对照 + 金颗粒对照 | 660 nm 主波长、读出口径、事件级脉冲趋势趋同 |
| 2024 POD+NODI | 高 | 双频读出和 POD/NODI 配对语义 | 配对读出方向对齐；未复现完整电子链路和分类器 |

最简洁的结论是：

```text
当前模型和 Tsuyama 的关系是“趋势一致、固定论文条件下已检查”，
不是“已按论文数值完成校准”。
```

---

## 6. 分论文固定条件对比

### 6.1 Tsuyama 2019 POD：Nonfluorescent Molecule Detection in 10^2 nm Nanofluidic Channels by POD

论文重点：

- 目标是非荧光分子 POD detection；
- 信号集中在衍射光区域；
- 约 `400 x 400 nm` channel 下 LOD 约 `5.0 uM`，对应约 `500 molecules / 0.23 fL`；
- 到 `200 x 200 nm` channel 时，按 detection volume 看 sensitivity 没有明显恶化。

与当前模型的同条件关系：

| 项目 | 论文 | 当前模型 |
|---|---|---|
| 检测机制 | 光热光学衍射 | 当前主线是 NODI 散射干涉 |
| 通道尺度 | 10^2 nm 级 POD 通道 | v1/v2 覆盖 500-900 nm 宽度范围内的主路线、诊断路线和上下文路线 |
| 热扩散到玻璃基底 | 核心机制之一 | v2 不做完整的热效应 POD 源项模型 |
| 衍射光区域 | 核心读出区域 | v2 用后焦面、狭缝和读出区域约束 |

结论：

2019 POD 支持的是 **衍射光区域作为读出区域** 和 **小通道不是天然不可用** 的趋势。它不能直接把 POD 分子检出限外推成 EV NODI 的事件概率。v2 正确地把热效应和光热相关结论放在旁路风险或后续证据缺口中，而不是写成 NODI 分数加成。

### 6.2 Tsuyama 2020 diffraction：Characterization of optical diffraction by single nanochannel

论文固定条件：

```text
probe = 633 nm He-Ne
illumination objective = 20x, NA = 0.45
collection NA = 0.9
lock-in modulation = 1.1 kHz
time constant = 1 s
channel width/depth varied
```

本地对照方式：

```text
使用更接近论文的空白通道相位滤波参考场；
比较不同宽度和深度下的参考场强度。
```

固定条件下的参考场振幅对比：

| 波长 | 通道几何 | 当前参考场 / 论文条件参考场 | 判断 |
|---|---|---:|---|
| 404 nm | 500 nm 宽、800 nm 深 | 0.968x | 差异小 |
| 404 nm | 500 nm 宽、900 nm 深 | 0.960x | 差异小 |
| 404 nm | 500 nm 宽、1200 nm 深 | 0.930x | 深通道偏差开始明显 |
| 404 nm | 500 nm 宽、1400 nm 深 | 0.908x | 深窄短波偏差最大 |
| 660 nm | 800 nm 宽、550 nm 深 | 1.000x | 基本重合 |
| 660 nm | 800 nm 宽、1400 nm 深 | 0.963x | 差异小 |
| 660 nm | 900 nm 宽、1200 nm 深 | 0.976x | 差异小 |

统计：

```text
平均绝对差异 ≈ 2.13%
最大绝对差异 ≈ 9.20%
```

结论：

这篇论文是当前模型最强的参考场约束。它支持：空白通道不是背景常数，而是会形成参考场的相位滤波结构。当前模型在固定条件下与论文条件对照的差异多数为几百分点，因此可以说 **机制和趋势强对齐**。但它不支持“所有绝对衍射强度已逐图复现”。

### 6.3 Tsuyama 2020 counting POD：Detection and Characterization of Individual Nanoparticles in a Liquid by POD

论文固定条件和实验语义：

```text
channel ≈ 800 x 710 nm
pressure = 100 kPa
flow velocity ≈ 0.17 mm/s
lock-in frequency ≈ 1.1 kHz
lock-in time constant ≈ 2 ms
particle = 20 nm Au
POD counting mode shows near-100% detection under its photothermal setup
```

本地同类对照：

| 项目 | 论文 | 当前模型 |
|---|---|---|
| 通道 | `800 x 710 nm` | 本地金颗粒对照覆盖 `800x500`, `800x600`, `1200x500`, `1200x600` |
| 锁相时间常数 | `2 ms` | 本地近论文金颗粒对照使用 `1 ms`，v2 读出同样位于毫秒级瞬态范围 |
| 颗粒 | `20 nm Au` | 本地金颗粒对照覆盖 `20/30/40/50/60 nm Au` |
| 检测机制 | POD 光热计数 | 当前是 NODI 金颗粒散射/干涉对照，不直接等同 |

在 660 nm、800 nm 宽、500 nm 深的近 Tsuyama 条件金颗粒对照中：

| Au 直径 | 判据 | 合成检出比例 | 稳定检出比例 | 平均脉冲峰值 | 散射截面 |
|---|---|---:|---:|---:|---:|
| 20 nm | fail | 0.000 | 0.000 | 0.00000 | `2.019e-18` |
| 30 nm | fail | 0.146 | 0.140 | 0.04414 | `2.499e-17` |
| 40 nm | pass | 0.266 | 0.265 | 0.10954 | `1.577e-16` |
| 50 nm | pass | 0.305 | 0.300 | 0.23239 | `6.956e-16` |
| 60 nm | pass | 0.315 | 0.308 | 0.44681 | `2.449e-15` |

结论：

这篇论文说明 20 nm 金颗粒在 POD 光热计数条件下可以被检测，但当前 NODI 散射对照不应把这个 POD 结论直接外推为“20 nm 金颗粒在 NODI 中必然通过”。当前金颗粒对照中，20 nm 仍是边界或失败，40 nm 以上明显增强；这与“粒径变大、信号增强”的趋势同向，也保持了 POD 到 NODI 外推边界的诚实。

### 6.4 Tsuyama 2020 solvent-enhanced POD：Concentration Determination at a Countable Molecular Level

论文固定条件和结论：

```text
excitation = 532 nm
probe = 633 nm
channel = about 400 x 400 nm
modulation optimum ≈ 1.1 kHz
PD optimum ≈ 15 mV
solvent enhancement can exceed 30x
LOD = 75 nM
equivalent molecules ≈ 10 / 0.23 fL
signal sign can flip when solvent RI relation changes
```

当前模型边界：

| 项目 | 论文 | 当前 v2 |
|---|---|---|
| solvent `dn/dT` | 核心变量 | 未作为 NODI 主模型物理项 |
| 光热源项 | 核心变量 | 404 nm 热效应旁路只做风险/机制提示，不做加分 |
| sign flip | POD thermal/diffraction coupling | v2 不把它当成 NODI sign-preservation 替代指标 |
| 浓度和检出限 | 实验论文目标 | v2 明确禁止真实浓度和绝对检出限结论 |

结论：

这篇论文对当前报告最重要的作用是 **边界控制**。它提醒我们：POD 热效应和溶剂增强可以很强，但这不是 EV NODI 散射可检测性的直接校准来源。v2 正确地禁止热效应旁路增加 NODI 光学分数，也禁止输出绝对检出限或真实 EV 浓度。

### 6.5 Tsuyama 2022 NODI：Nanofluidic optical diffraction interferometry for detection and classification

论文相关固定条件：

```text
illumination objective ≈ 20x, NA = 0.45  # 沿用 2020 diffraction 同一物镜
collection NA ≈ 0.9
slit ≈ 1 mm
pinhole ≈ 400 um
time constant ≈ 1-2 ms
pressure = 100 kPa
flow velocity ≈ 0.2 mm/s
channel near 800 x 550 nm
NODI 读出以 660 nm 为中心
```

本地历史审查记录只显式记录 2022 NODI 的收集数值孔径、狭缝、针孔、时间常数、压力/流速、几何与读出中心波长；照明物镜在论文里沿用 2020 diffraction 的 `20x / NA=0.45` 设置，但本报告不依赖这条做任何对照判断。

本地接近 2022 NODI 论文条件的对照方式：

```text
使用更接近论文的空白通道相位滤波参考场；
采用近似过填充照明；
读出使用脉冲幅值而不是只看同相信号；
锁相时间常数为 1 ms；
NODI 读出频率为 3 kHz；
按单通道 NODI 判据做比较。
```

固定条件路线对照：

| 对照口径 | 路线 | 严格通过数 | 平均合成检出比例 | 平均稳定检出比例 | 小 EV 加权稳定检出比例 |
|---|---|---:|---:|---:|---:|
| 当前工程口径 | 404 nm，500 nm 宽，800 nm 深 | 16 | 0.3425 | 0.3365 | 0.2162 |
| 当前工程口径 | 660 nm，800 nm 宽，550 nm 深 | 16 | 0.4830 | 0.4715 | 0.4090 |
| 当前工程口径 | 660 nm，800 nm 宽，1400 nm 深 | 19 | 0.4580 | 0.4515 | 0.3727 |
| 当前工程口径 | 660 nm，900 nm 宽，1200 nm 深 | 14 | 0.4350 | 0.4260 | 0.3672 |
| 2020 衍射论文口径 | 404 nm，500 nm 宽，800 nm 深 | 16 | 0.3535 | 0.3450 | 0.2188 |
| 2020 衍射论文口径 | 660 nm，800 nm 宽，550 nm 深 | 23 | 0.4505 | 0.4350 | 0.4128 |
| 2020 衍射论文口径 | 660 nm，800 nm 宽，1400 nm 深 | 17 | 0.4160 | 0.4100 | 0.3421 |
| 2020 衍射论文口径 | 660 nm，900 nm 宽，1200 nm 深 | 13 | 0.4485 | 0.4420 | 0.3616 |
| 2022 NODI 论文口径 | 404 nm，500 nm 宽，800 nm 深 | 21 | 0.3600 | 0.3540 | 0.2334 |
| 2022 NODI 论文口径 | 660 nm，800 nm 宽，550 nm 深 | 25 | 0.4875 | 0.4670 | 0.4593 |
| 2022 NODI 论文口径 | 660 nm，800 nm 宽，1400 nm 深 | 25 | 0.4395 | 0.4290 | 0.3748 |
| 2022 NODI 论文口径 | 660 nm，900 nm 宽，1200 nm 深 | 25 | 0.4775 | 0.4705 | 0.3972 |

结论：

1. 固定到 2022 NODI 语义后，`660` 仍然强于 `404`。
2. 最优几何会向论文器件附近的 `800x550` 收缩。
3. 这说明原工程主线的 660 nm 主波长趋势没有丢，但默认深通道主路线和接近论文浅通道器件的优化目标并不完全相同。

这个 `800x550` 结果只是论文固定条件下的 cross-check 观察，不是路线治理候选；当前 main-660 仍锁定为 `660 nm，800 nm 宽，1400 nm 深` 与 `660 nm，800 nm 宽，1500 nm 深`，不因本表发生 route promotion 或 main-660 重定义。

关于论文数值复现的边界：

此前的 Tsuyama 论文数值复核曾尝试对 2022 NODI 论文目标做更严格复现。结果是：

```text
按论文公式计算的银/金信号关系基本成立；
金颗粒随粒径变化的原始响应斜率仍未完全解释；
用一个全局响应压缩因子可以接近论文数值，但没有正式通过受限复现判据；
没有任何候选模型被签发为“论文数值已校准复现”。
```

所以本文只能说 2022 NODI 的趋势和固定条件对照是同向的，不能说已经完整复现论文表格或分类准确率。

### 6.6 Tsuyama 2024 POD+NODI：Simultaneous light absorption and scattering measurement

论文固定条件与语义：

```text
probe wavelength = 660 nm
excitation wavelength = 532 nm
time constant ≈ 1-2 ms
frequency split ≈ 1.2 / 4.1 kHz
channel width roughly 800-1200 nm
depth roughly 550 nm
paired POD + NODI pulse observables
```

当前可对标部分：

| 对标层 | 当前模型状态 |
|---|---|
| 660 nm 探测光 | NODI 和金颗粒对照中 660 nm 保持主导趋势 |
| 532 nm 激发光 / POD 侧信号 | 只作为热效应或 POD 旁路对照，不进入 NODI 光学分数 |
| 双频读出语义 | v2 有幅值读出和同相读出的对照 |
| 配对分类 | 当前不复现完整电子链路和分类器协议 |

读出口径固定对照：

| 读出口径 | 通过数 | 平均合成检出比例 | 平均稳定检出比例 | 平均相位翻转比例 | 平均脉冲峰值 |
|---|---:|---:|---:|---:|---:|
| 基线：同相读出且使用相位门控 | `0/60` | 0.11075 | 0.10850 | 0.44738 | 0.095283 |
| 同相读出但不使用相位门控 | `9/60` | 0.11075 | 0.10850 | 0.44738 | 0.095283 |
| 幅值读出 | `9/60` | 0.10967 | 0.10732 | 0.00000 | 0.095390 |

对 `660 nm`：

| 读出口径 | 通过比例 | 平均合成检出比例 | 平均稳定检出比例 | 平均脉冲峰值 |
|---|---:|---:|---:|---:|
| 基线：同相读出且使用相位门控 | 0.00 | 0.18275 | 0.17890 | 0.15637 |
| 同相读出但不使用相位门控 | 0.45 | 0.18275 | 0.17890 | 0.15637 |
| 幅值读出 | 0.45 | 0.18145 | 0.17735 | 0.15641 |

结论：

这说明读出口径会显著改变“是否通过”的解释，但合成检出比例、稳定检出比例和脉冲峰值本身几乎不变。这个结果与 Tsuyama 2022 / 2024 使用脉冲观测量、最大信号值和配对读出的方向一致。它不等于完整复现 2024 的配对电子链路、热通道或分类协议。

---

## 7. 近 Tsuyama 条件的金颗粒固定参数总表

为了避免只讲论文摘要，这里单独列出本地近 Tsuyama 条件金颗粒对照的固定条件：

```text
波长 = 488 / 532 / 660 nm
通道几何 = 800x500, 800x600, 1200x500, 1200x600 nm
金颗粒直径 = 20 / 30 / 40 / 50 / 60 nm
每个组合的合成事件数 = 1000
锁相时间常数 = 1 ms
读出方式 = 脉冲幅值读出
相位翻转不作为硬剔除条件
```

按波长聚合：

| 波长 | 通过比例 | 平均合成检出比例 | 平均稳定检出比例 | 平均脉冲峰值 | 平均散射截面 |
|---|---:|---:|---:|---:|---:|
| 488 | 0.00 | 0.0608 | 0.0595 | 0.05245 | `2.856e-16` |
| 532 | 0.00 | 0.0868 | 0.0851 | 0.07730 | `3.932e-16` |
| 660 | 0.45 | 0.1815 | 0.1774 | 0.15641 | `6.658e-16` |

这张表是当前和 Tsuyama gold 语义最直观的连接点：

```text
660 > 532 > 488
```

它说明 660 nm 主波长在近论文金颗粒对照里没有被计算链条翻掉。

---

## 8. 哪些话现在可以说，哪些话不能说

### 8.1 可以说

可以说：

```text
v2 是对原工程逻辑和原全量模拟结果的“面向真实仪器约束”补强。
```

可以说：

```text
在无实测、受限合成先验模型内，660 nm 主路线仍保持治理锁定。
```

可以说：

```text
弱参考场路线和窄深上下文路线高于主路线的警告，
可以被低自由度的宽度风险先验稳定解释。
```

可以说：

```text
Tsuyama 2020 衍射论文、2022 NODI 论文、2024 POD+NODI 论文的若干固定条件和趋势，
与当前模型的参考场、660 nm 主波长、事件级脉冲和读出口径趋同。
```

### 8.2 不能说

不能说：

```text
v2 使用了真实采集数据。
```

不能说：

```text
v2 校准了信噪比、事件概率、检出限或真实 EV 浓度。
```

不能说：

```text
Tsuyama 论文的全部图表和数值已逐式复现。
```

不能说：

```text
宽度风险先验已被证明是真实物理定律。
```

不能说：

```text
上下文路线或 660 nm、900 nm 宽、1400 nm 深的可选路线已经可以升级为主路线。
```

不能说：

```text
404 nm 热效应旁路可以提高 NODI 光学分数。
```

---

## 9. 读者向最终解释

如果把整个项目讲给不看阶段报告的读者，最合适的叙事是：

1. 第一阶段建立了一个相对模拟库，用来比较不同波长、通道宽深和颗粒条件下的 NODI 可检测性。
2. 这个库本身不是实验校准，所以不能直接给出真实浓度、真实 LOD 或真实检测概率。
3. v2 在不引入实测数据的前提下，把仪器链、读出链、空白样本风险、后焦面/狭缝/针孔、近壁网格、热效应旁路、路线治理和宽度风险先验加进来，检查原结论是否经得起更现实的约束。
4. 检查后，660 nm、800 nm 宽、1400 nm 深和 660 nm、800 nm 宽、1500 nm 深这两条路线仍作为主路线比较基准保持锁定。
5. v2 也发现了一个重要警告：一些弱参考场路线或窄深上下文路线在原仪器情景先验下看起来更高。
6. 后续宽度风险和机制分解分析说明，这个警告可以由“窄通道工程风险被低估”这一低自由度先验解释，而不需要逐条路线手动调参。
7. Tsuyama 论文对这个结论的支持主要是趋势级和固定条件级：参考场机制、660 nm 主波长、毫秒级读出、脉冲观测量和读出口径与当前模型方向一致。
8. 但 Tsuyama POD thermal / solvent / molecule-detection 论文不能直接拿来校准 EV NODI scattering detectability；2022/2024 的分类准确率也没有被当前模型严格复现。

最终结论：

```text
v2 已经完成了“无实测、偏真实模拟补强”的任务。
它提升了原工程逻辑和原模拟结果的可信度，
但没有把模型升级成实测校准模型。
下一步如果要继续提高物理确定性，
必须作为 v2 之后的独立研究计划，另行解决参考场工作范围、
后焦面/狭缝/读出区域算子、制程与计量窗口、壁面/PEG/运输风险、
颗粒类别残余，以及 900 nm 宽可选路线的治理诊断证据。
```

---

## 10. 对分析报告体系的影响

加入 v2 后，原来的读者向报告需要全面改写口径，但不需要推翻原全量计算：

| 原报告容易写成 | v2 后应改成 |
|---|---|
| “模拟找到了最优路线” | “相对模拟给出主工程候选，v2 检查其在真实仪器约束先验下的稳定性” |
| “检测率 / 事件数” | “相对先验分数 / 合成代理计数，不是实际观察到的事件数” |
| “SNR 足够” | “只能讨论不同仪器情景下的相对探测器风险，不能写成已校准信噪比” |
| “404 灵敏度高所以可能更好” | “404 nm 是机制、旁路或上下文对照；热效应旁路不得加分” |
| “局部环带窗口支持某路线” | “局部环带窗口是并行诊断视角，不能替代全局交叉排序” |
| “Tsuyama 已复现” | “Tsuyama 固定条件和趋势对齐；论文数值校准复现未签发” |
| “下一步做采集” | “v2 内不做采集；采集只能作为 v2 之后的独立研究计划另行设计” |

因此，现在最适合保留两层报告：

1. **读者向综合报告**：就是本文，解释结论、边界和 Tsuyama 对照。
2. **技术附录/阶段报告**：保留阶段门控、运行清单、校验和测试证据，供审计而非普通读者阅读。
3. **post-v2 P0-P18 审计/有界 trace 证据**：作为本文第 13 节的增量证据，不另起读者版结论口径。

---

## 11. 本报告使用的本地证据

核心 v2 证据：

```text
reports/51_EV_NODI_realism_v2_instrument_aware_roadmap.md
reports/75_EV_NODI_realism_v2_R6_route_prior_sensitivity_audit_analysis.md
reports/77_EV_NODI_realism_v2_R7_route_prior_mechanistic_decomposition_audit_analysis.md
reports/81_EV_NODI_realism_v2_R7_2_operator_artifact_gap_register_generation_analysis.md
reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md
reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md
results/ev_nodi_realism_v2_full_grid_R5_v2/
results/ev_nodi_realism_v2_R6_route_prior_sensitivity_audit/
results/ev_nodi_realism_v2_R7_route_prior_mechanistic_decomposition_audit/
results/ev_nodi_realism_v2_R7_2_operator_artifact_gap_register/
results/ev_nodi_realism_v2_no_measured_data_closure/
```

post-v2 P0-P18 证据：

```text
reports/90_EV_NODI_post_v2_review_ready_relative_audit_roadmap.md
reports/91_EV_NODI_post_v2_P0_release_completion_note.md
reports/92_EV_NODI_P1_physical_ceiling_extensions_plan.md
reports/98_EV_NODI_P2_bounded_physical_solver_readiness_plan.md
reports/99_EV_NODI_P2_bounded_physical_solver_readiness_completion_note.md
reports/100_EV_NODI_P3_bounded_solver_authorization_pilot_design_plan.md
reports/101_EV_NODI_P4_bounded_solver_dry_run_preflight_plan.md
reports/102_EV_NODI_P5_bounded_solver_authorization_gate_plan.md
reports/103_EV_NODI_P6_minimal_bounded_solver_execution_plan.md
reports/104_EV_NODI_P7_second_lane_authorization_design_plan.md
reports/105_EV_NODI_P8_second_bounded_solver_lane_execution_plan.md
reports/106_EV_NODI_P8_second_bounded_solver_lane_closure_note.md
reports/107_EV_NODI_P9_next_bounded_lane_authorization_design_plan.md
reports/108_EV_NODI_P10_third_bounded_solver_lane_execution_plan.md
reports/109_EV_NODI_P10_third_bounded_solver_lane_closure_note.md
reports/110_EV_NODI_P11_fourth_bounded_lane_authorization_design_plan.md
reports/111_EV_NODI_P12_fourth_bounded_solver_lane_execution_plan.md
reports/112_EV_NODI_P12_fourth_bounded_solver_lane_closure_note.md
reports/113_EV_NODI_P13_fifth_bounded_lane_authorization_design_plan.md
reports/114_EV_NODI_P14_fifth_bounded_solver_lane_execution_plan.md
reports/115_EV_NODI_P14_fifth_bounded_solver_lane_closure_note.md
reports/116_EV_NODI_P15_sixth_bounded_lane_authorization_design_plan.md
reports/117_EV_NODI_P16_sixth_bounded_solver_lane_execution_plan.md
reports/118_EV_NODI_P16_sixth_bounded_solver_lane_closure_note.md
reports/119_EV_NODI_P17_seventh_bounded_lane_authorization_design_plan.md
reports/120_EV_NODI_P18_bounded_lane_synthesis_stop_continue_design.md
results/post_v2_mandatory_audit/
results/post_v2_minimal_bounded_solver_execution/
results/post_v2_second_bounded_solver_lane_execution/
results/post_v2_third_bounded_solver_lane_execution/
results/post_v2_fourth_bounded_solver_lane_execution/
results/post_v2_fifth_bounded_solver_lane_execution/
results/post_v2_sixth_bounded_solver_lane_execution/
results/post_v2_bounded_lane_synthesis_stop_continue/
```

Tsuyama 对照证据：

```text
archive/tsuyama/48_tsuyama六篇严格补读结论.md
archive/tsuyama/51_tsuyama_paper_aligned全论文闭环审查.md
archive/tsuyama/56_tsuyama已解决与尚未解决问题_中英对照表.md
archive/tsuyama/57_工程主线与Tsuyama论文结果趋势对照_中英对照.md
archive/tsuyama/58_tsuyama固定条件对标与结果表.md
reports/49_Tsuyama_Phase2_paper_calibrated_selected_annulus_analysis.md
```

本地论文文件：

```text
papers/Tsuyama_Mawatari_2019_Nonfluorescent Molecule Detection in 10^2 nm Nanofluidic Channels by.pdf
papers/Tsuyama和Mawatari - 2020 - Characterization of optical diffraction by single nanochannel for aL–fL sample detection in nanoflui.pdf
papers/Tsuyama_Mawatari_2020_Detection and Characterization of Individual Nanoparticles in a Liquid by.pdf
papers/Tsuyama_Mawatari_2020_Concentration Determination at a Countable Molecular Level in Nanofluidics by.pdf
papers/Tsuyama_Mawatari_2022_Nanofluidic optical diffraction interferometry for detection and classification.pdf
papers/Tsuyama和Mawatari - 2024 - Nanofluidic detection platform for simultaneous light absorption and scattering measurement of indiv.pdf
```

---

## 12. 最终收口

v2 已经完成它应该完成的工作：在没有实测数据的情况下，把原工程逻辑和原模拟结果放进更现实的仪器约束、路线治理和先验敏感性框架中重新审视。post-v2 P0-P18 又完成了第二层收口：把路线裁决、证据包装、物理上限 readiness、授权门和窄范围 trace 证据全部约束在相对审计/trace-only 边界内。

它带来的增量不是“更多漂亮分数”，而是：

```text
更清楚的结论边界
更现实的仪器和 blank 约束
更严格的 660 nm 主路线治理
更清楚的 Tsuyama trend alignment
更诚实的 artifact gap register
```

所以，当前可以把 v2 与 P0-P18 作为最终读者口径写入总报告；但必须同时保留这句双语边界：

```text
全部 v2 结论都是无实测数据的合成相对先验结论；
不构成对任何实物仪器、实物样品或绝对量级的校准。

All v2 conclusions are synthetic relative-prior conclusions
without measured-data calibration.
```

## 13. post-v2 P0-P18 合并更新

本节是 2026-05-11 合并更新。它把 realism v2 之后新增的 P0-P18 结果并入本文；不另起新版读者报告。P0-P18 的共同边界是：

```text
calibrated_claim_allowed = false
measured_data_ingest_authorized = false
calibration_data_ingest_authorized = false
route_promotion_authorized = false
main_660_redefinition_authorized = false
raw_magnitude_final_gate_allowed = false
solver_native_raw_magnitude_final_gate_allowed = false
```

### 13.1 P0 mandatory audit 的结论

P0 把 v2 sidecars 转换成强制路线审计链，并冻结可复核 review package。它的关键结果是：

| 项目 | 数值 / 结论 |
|---|---|
| 审计行数 | `572` 个 route aggregate |
| 波长覆盖 | 404 / 488 / 532 / 660 nm 各 `143` 个唯一 route aggregate |
| `relative_main_candidate` | `2` 条：`main_660_W800_D1400`、`main_660_W800_D1500` |
| main-660 最终裁决 | 两条均为 `conditional_relative_main` |
| `probe_only` | `probe_404_W600_D1300`，最终为 `shortwave_probe_only` |
| `relative_control_candidate` | `control_660_W700_D1500`，最终为 `weak_reference_control_only` |
| `optional_robustness_probe_only` | `optional_660_W900_D1400`，不得重定义 main-660 |
| `paper_sanity_only` | 4 条 Tsuyama/paper-sanity 路线 |
| 被降级为 surrogate-sensitive | `563` 条，不允许按 v1 高分直接晋升 |
| 必需下一证据 | main/control/optional 多数指向 `measured_blank_bfp` 或 `fullwave_spot_check` |

P0 解决的冲突是：v1 全量库中大量 660 nm context routes 的 scalar 排名很高，但 P0 审计把 BFP ROI、Tsuyama BFP、noise/readout、EV/sample uncertainty、selected-annulus lens、pairwise inversion 和 forbidden-claim blockers 一起纳入后，绝大多数只能保留为 `surrogate_sensitive_not_promoted`。因此旧式“高分 = 主路线”的读法被废止。

### 13.2 P1-P5 readiness / authorization 链

P1-P5 没有产生 calibrated physical prediction；它们建立的是后续物理证据的门控合同。

| 阶段 | 核心结论 | 仍未解决或存疑点 |
|---|---|---|
| P1 | 完成 full-wave/Green tensor、Vector/Jones、roughness/leakage、transport/residence-time 四条 physical-ceiling diagnostic contract；全部为 surrogate-risk reduction only。 | 只生成 no-solver rank diagnostics，不运行重型 solver。 |
| P2 | 完成 bounded physical-solver readiness；source binding、route universe、schema manifest 和 verifier 均要求 solver execution blocked。 | 未来 solver 只能在有明确授权和可解释性标准后运行。 |
| P3 | 完成最小 pilot design；只选 P4/P6 后续使用的 3 条路线子集。 | 只设计，不执行。 |
| P4 | 完成 dry-run preflight；确认 input manifest、mesh/boundary/unit preflight、authorization record 的形状。 | mesh manifest 明确为 `not_generated_no_mesh_generation`。 |
| P5 | 完成 authorization gate；默认 decision 是 `not_authorized_pending_explicit_later_phase_execution_request`。 | 只有明确短语才能开启后续最小 bounded execution；P5 自身仍不执行。 |

### 13.3 P6-P18 有界 trace 结论

P6、P8、P10、P12、P14、P16 是六条 narrow deterministic trace lane，均只覆盖同一 3 条路线：

```text
main_660_W800_D1400
main_660_W800_D1500
probe_404_W600_D1300
```

它们的排序行为如下：

| 阶段 | trace lane | 第 1 名 | 第 2 名 | 第 3 名 | 解读 |
|---|---|---|---|---|---|
| P6 | minimal bounded Green kernel | `main_660_W800_D1400` | `main_660_W800_D1500` | `probe_404_W600_D1300` | trace-only；不支持 promotion。 |
| P8 | phase-gradient trace | `main_660_W800_D1400` | `main_660_W800_D1500` | `probe_404_W600_D1300` | 与 P6 同序。 |
| P10 | curvature-balance trace | `main_660_W800_D1500` | `main_660_W800_D1400` | `probe_404_W600_D1300` | main-660 内部首位切换。 |
| P12 | resonance-compactness trace | `main_660_W800_D1500` | `main_660_W800_D1400` | `probe_404_W600_D1300` | 与 P10 同序。 |
| P14 | phase-curvature residual trace | `main_660_W800_D1400` | `main_660_W800_D1500` | `probe_404_W600_D1300` | 再次切回 800x1400。 |
| P16 | phase-curvature residual trace | `main_660_W800_D1500` | `main_660_W800_D1400` | `probe_404_W600_D1300` | 再次切回 800x1500。 |
| P18 | synthesis stop/continue | 不选单一冠军 | 不选单一冠军 | 404 probe 仍非主路线 | 停止机械式继续滚 lane，要求 P19 evidence strategy gate。 |

P18 的结论是：

```text
bounded_lanes_sufficient_for_route_promotion = false
rank_instability_across_bounded_lanes_detected = true
stop_continue_decision = stop_mechanical_lane_roll_forward_pending_p19_evidence_strategy
```

这说明 P6-P16 不是“主路线更确定”的证据，而是“两个 main-660 候选仍应作为集合保留、不能从 trace-only lane 中挑单一 winner”的证据。

### 13.4 p0-p18 单项合并记录

| 阶段 | 核心结论 | 关键数据/证据 | 与前后阶段的衔接或冲突 | 未解决点 |
|---|---|---|---|---|
| p0 | P0 release package 达到 review-ready relative-audit milestone。 | `REVIEW_PACKAGE_MANIFEST.json`、`REVIEW_PACKAGE_HASHES.sha256`、`results/post_v2_mandatory_audit/`、full regression passed 记录。 | 将 v2 sidecars 从“阶段报告”提升为 mandatory route-audit evidence chain；不改变 v2 无实测边界。 | 外部 review zip 仍包含完整 v1 summary，未来可优化包装模式。 |
| p1 | Physical-ceiling extensions 完成 no-solver rank diagnostic contracts。 | 四条 lane contract：full-wave/Green tensor、Vector/Jones、roughness/leakage、transport/residence-time。 | 为 P2 readiness 提供 surrogate-risk reduction 输入；不执行 solver。 | 缺真实 full-wave/vector/roughness/transport 输出。 |
| p2 | Bounded physical-solver readiness 完成，但 solver execution blocked。 | bounded route universe、source binding、schema manifest、artifact manifest。 | 把 P1 诊断合同转成未来 preflight universe；为 P3 pilot design 提供边界。 | 仍无 mesh、operator、solver output 或 measured ingest。 |
| p3 | Minimal pilot design 完成。 | 只选择 2 条 main-660 + 1 条 pairwise/full-wave spot-check 路线。 | 为 P4 dry-run preflight 定义固定 3-route subset。 | 只设计，不执行。 |
| p4 | Dry-run preflight 完成。 | input manifest、mesh/boundary/unit preflight、execution authorization record。 | 明确 mesh 未生成、execution 未授权；为 P5 gate 提供证据。 | 仍不产生 solver output。 |
| p5 | Authorization gate 完成但默认阻断执行。 | `required_next_authorization_phrase = authorize minimal bounded solver execution`。 | 将 p4 dry-run 绑定到后续授权门。 | 需要明确授权短语才能执行 p6。 |
| p6 | 第 1 条 minimal bounded trace 已执行。 | 三路线排序：800x1400 > 800x1500 > 404 probe。 | 首次产生 trace-only solver output；不改变 P0/P1/P2/P3/P4/P5 边界。 | 非 full-wave solver；不能 route promotion。 |
| p7 | 第二 lane 授权设计完成。 | future phrase: `authorize second bounded solver lane execution`。 | 绑定 p6 trace，但不解释为 calibration。 | 仍不执行。 |
| p8 | 第二 bounded trace 已执行并通过 closure review。 | phase-gradient 排序同 p6；closure verdict `NO P8 BLOCKERS FOUND`。 | 与 p6 同序，但仍 trace-only。 | 不能证明主路线唯一性。 |
| p9 | 第三 lane 授权设计完成。 | 绑定 p8 closure，future phrase for p10。 | 设计下一 gate，不新增 output。 | 仍需独立授权。 |
| p10 | 第三 bounded trace 已执行并通过 closure review。 | 排序切换为 800x1500 > 800x1400 > 404 probe；closure verdict `NO P10 BLOCKERS FOUND`。 | 与 p6/p8 冲突：main-660 内部首位反转。 | 反转不能按 route preference 解读。 |
| p11 | 第四 lane 授权设计完成。 | 绑定 p10 closure，future phrase for p12。 | 继续 gate 链，不执行。 | 仍缺接受准则。 |
| p12 | 第四 bounded trace 已执行并通过 closure review。 | 排序继续为 800x1500 > 800x1400 > 404 probe；closure verdict `NO P12 BLOCKERS FOUND`。 | 支持 p10 的 trace 排序，但仍与 p6/p8 不一致。 | 仍不能 route promotion。 |
| p13 | 第五 lane 授权设计完成。 | 绑定 p12 closure，future phrase for p14。 | 只设计下一 gate。 | 仍不执行。 |
| p14 | 第五 bounded trace 已执行并通过 closure review。 | 排序切回 800x1400 > 800x1500 > 404 probe；closure verdict `NO P14 BLOCKERS FOUND`。 | 与 p10/p12 冲突；记录 trace rank instability。 | 需要停止机械式 lane 扩展并定义证据策略。 |
| p15 | 第六 lane 授权设计完成。 | 记录 P12-to-P14 rank delta `[-1, +1, 0]`。 | 把 rank instability 明确升级为治理证据。 | 仍不是 final gate。 |
| p16 | 第六 bounded trace 已执行并通过 closure review。 | 排序切回 800x1500 > 800x1400 > 404 probe；closure verdict `NO P16 BLOCKERS FOUND`。 | 再次确认 main-660 内部首位不稳定。 | 不支持第七 lane 机械延续。 |
| p17 | 第七 lane 授权设计完成但未执行。 | 记录 P12-to-P14 与 P14-to-P16 都出现 `[-1,+1,0]`。 | 为 p18 synthesis 提供停止/继续问题。 | 需要 p19 evidence-strategy gate。 |
| p18 | Synthesis-only stop/continue design 完成。 | top sequence = 800x1400, 800x1400, 800x1500, 800x1500, 800x1400, 800x1500。 | 裁决 P6-P16 不足以 route promotion；停止机械滚 lane。 | 下一步必须先定义 P19 evidence strategy 与 acceptance criteria。 |

### 13.5 冲突点与取舍理由

| 冲突点 | 取舍 |
|---|---|
| 旧 all-crossing/full-grid 报告曾把 488/532/404 深通道作为第一批实验候选；v2 与 P0 后把 main-660 锁定为 800x1400/1500。 | 保留旧报告作为历史全量库解释；当前主报告以 v2/P0 的仪器约束、路线治理和 mandatory audit 为准。理由是新证据显式纳入 BFP、noise/readout、route-role、artifact gap 和 forbidden-claim blockers。 |
| v2 closure 锁定两条 main-660；P6-P16 trace 试图比较二者，但首位在 lane 间反复切换。 | 不选单一 winner。两条 main-660 维持 `conditional_relative_main` 集合；P18 判定 bounded traces 不足以 route promotion。 |
| P0 audit 中许多 660 context routes 的 v1 scalar percentile 高于 main-660。 | 不按 v1 scalar 高分晋升。P0 将 563 条路线降为 `surrogate_sensitive_not_promoted`，因为 BFP rank shift、pairwise inversion、claim blockers 或后续证据需求仍未闭合。 |
| P6/P8/P10/P12/P14/P16 已产生 solver-like trace output，但 v2 禁止 calibrated claims。 | trace output 只用于 rank、rank-percentile、pairwise order 与 rank delta；不允许原始 magnitude、detector unit、SNR、LOD、浓度或 route promotion。 |
| P17 记录第七 lane 未来短语；P18 又停止机械式继续。 | 以 P18 为准。未来不能只凭 `authorize seventh bounded solver lane execution` 继续；必须先有 P19 evidence-strategy gate 和接受准则。 |

### 13.6 当前未决事项

1. P19 需要先定义 evidence strategy、acceptance criteria 和停止准则，而不是继续机械生成第七条 bounded lane。
2. `measured_blank_bfp`、standard particle transfer、slit/ROI scan、full-wave spot-check 等仍是后续独立证据依赖。
3. EV polydispersity、non-sphericity、coincidence/blended pulses、roughness/fabrication background、PEG fouling 和 drift 仍属于 post-v2 validation program，不应回写成 v2 内 calibration。
4. 本报告仍禁止 calibrated SNR、absolute LOD、true EV concentration、biological specificity、detector voltage prediction、sample-count、measured blank safety、route promotion 和 main-660 redefinition。
