# EV/NODI v1+v2 综合分析报告：无实测、面向真实仪器约束的模拟补强与 Tsuyama 文献对照

日期：2026-05-11
版本：v4.0（双口径并立：合并 realism v2 收口 + post-v2 P0-P18 + selected-annulus paper-audit 全量并入）
报告性质：读者向综合分析报告
适用口径：无实测数据、合成相对先验模型、面向真实仪器约束的模拟补强，以及 post-v2 审计/有界 trace 证据
口径并立：本文同时承载 **all-crossing 工程主排序口径**（§1–§13）与 **selected-annulus paper-audit 口径**（§14），两者在本报告中是同等优先的读者入口；§15 为双口径综合分析与共同收口

---

## 0. 读者须知

这份报告不是实验报告，也不是仪器校准报告。

它从 v4.0 起改为 **双口径并立**：

```text
口径 A：all-crossing 全局工程口径
       回答 “在 32,032 基础设计组合 + 8 仪器情景的全量库内，
              EV/NODI 工程路线如何相对排序，主路线如何治理”
       证据来源：v1 全量库、realism v2 R0-R7.2、post-v2 P0-P18
       当前状态：main-660 conditional_relative_main 集合
                 {800x1400, 800x1500} 已收口，
                 P19 evidence strategy gate 之前不再机械式滚 lane。

口径 B：selected-annulus paper-audit 口径
       回答 “在 selected-annulus 0.5-0.8 固定窗口下，
              Tsuyama 论文 proxy 数值能否被估计参数自然复现”
       证据来源：Tsuyama Phase 2 / Phase 2.5-2.11 reproduction lens 链、
                 R5.2 bounded scenario-prior audit、
                 instrument-aware feasibility、paper-statistics sensitivity
       当前状态：当前参数集已冻结为口径 B 选型
                 (D2.1 best + gamma 0.749 + global SNR scale 0.728
                  + SNR response exp 0.812 + selected-annulus 0.5-0.8
                  + 660/800x550 与 660/1200x550 主对照
                  + ET-2030 + LI5640 current input/TIA 接法)；
                 release_status = negative_or_diagnostic_result_only；
                 详细参数 §14.12，对论文对比 §14.13，选型推荐 §14.14。
```

两个口径回答的是不同问题，不是主辅关系。本文 §1–§13 是口径 A 的完整分析；§14 是口径 B 的完整分析；§15 做双口径综合对照、共同 forbidden claim 和共同收口。两个口径的 forbidden claim **包含**一条共同对称约束：

```text
口径 A 不替代口径 B 的 paper-audit 结论；
口径 B 不替代口径 A 的工程主排序。
```

任何后续 realism v2 / post-v2 P19+ 阶段证据并入本文时，必须同时评估并写入两个口径下的对应结论；某口径下若没有等价证据，必须显式标注 "另一口径下未扩展"，不得只写一边。详见 §15.5。

下面继续口径 A（all-crossing）的完整分析。口径 B（selected-annulus）的完整分析在 §14。

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

执行摘要（双口径）：

这份报告并立回答 8 个问题，前 6 个属于口径 A（all-crossing），后 2 个属于口径 B（selected-annulus）。

口径 A — all-crossing 全局工程口径：

1. 原工程主线和原全量模拟做完后，还差什么？答：差仪器现实约束、空白样本风险、读出语义、路线角色边界、窄通道风险先验和证据缺口清单。
2. v2 在不引入实测的前提下能补到哪一步？答：补到"当前模型还缺哪些物理或仪器证据"的登记表；不能补到任何校准或绝对量级结论。
3. 660 nm 主路线在 v2 之后还成立吗？答：在当前无实测、受限先验模型内仍成立，锁定为 660 nm、800 nm 宽、1400/1500 nm 深的两条主路线。
4. 弱参考场路线和窄深上下文路线为什么一度看起来更高？答：更可能是窄通道工程风险在原模型中被低估；本报告用低自由度宽度风险先验解释，不把它升级为物理定律。
5. Tsuyama 论文支持到了什么程度？答：3 篇对当前 NODI 主线约束强，3 篇主要提供 POD/热效应边界；当前是趋势和固定条件对齐，不是论文数值的完整校准复现。
6. post-v2 P0-P18 改变了什么？答：P0 把路线裁决做成可复核的相对审计包；P1/P2 把后续物理上限/solver readiness 做成不执行 solver 的合同；P6-P16 的六条有界 trace 没有支持 route promotion，反而显示 `main_660_W800_D1400` 与 `main_660_W800_D1500` 的 trace-only 首位在不同 lane 间切换；P18 因此停止机械式继续滚 lane，要求先做 P19 evidence-strategy gate。

口径 B — selected-annulus paper-audit 口径：

7. selected-annulus 0.5-0.8 固定窗口下，Tsuyama paper proxy 数值能否被自然复现？答：**negative_or_diagnostic_result_only；没有 accepted paper-calibrated candidate**。Phase 2 family-ladder full inverse 完成 `52` candidates × `3` seeds × `10000 events/case`；formula-consistent Ag/Au signal 已通过；raw Au size-response 仍偏陡（D2.1 局部 smoke raw Au exponent 范围约 `3.05–3.19`，full inverse / 3000-event size-only raw peak-height exponent 约 `3.17–3.25`，目标 `2.3`，limiting pair `40-60` nm）。**v4.0 起口径 B 已把当前参数集冻结为选型**：候选 `tau_2ms_global_refphi_plus_collection_narrow`（D2.1 best）+ single global response compression `gamma=0.749` + global SNR scale `0.728` + SNR response exponent `0.812`，total reproduction score `2.033`（descriptive partial）。冻结理由是再降分需要 per-diameter / per-geometry / per-case correction，越过 estimated-parameter 复现边界；当前选型已是 reproduction lens 框架内可交付的最佳低自由度解。详细参数集见 §14.12，逐论文对比表见 §14.13，选型推荐见 §14.14。
8. selected-annulus 与 all-crossing 在 R5 全量库 shadow 上是什么关系？答：`selected_all_uplift_median ≈ 1.384x`、`max ≈ 1.557x`，未越过 `1.6x` warning；同时 R5.2 bounded scenario-prior audit 把 sidecar 治理写成 `selected_annulus_replaces_all_crossing_ranking = false`、`selected_annulus_bound_change_authorized = false`。两个口径并立、互不替代。

读完整份报告大约需要 50-60 分钟。如果只想看口径 A 结论，请读第 1 节、第 8 节、第 12 节和第 13 节；只想看口径 B 结论与冻结选型，请读 §14.12 / §14.13 / §14.14；想看双口径综合与共同收口，请读 §15。

---

## 1. 总结结论（口径 A：all-crossing）

> 本节是口径 A（all-crossing 全局工程口径）下的总结结论。口径 B（selected-annulus paper-audit 口径）的总结结论在 §14.1。双口径并立的对照见 §15。

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

所以本文只能说 2022 NODI 的趋势和固定条件对照是同向的，不能说已经完整复现论文表格或分类准确率。这段总结对应口径 B 的 Phase 2 / 2.5–2.11 reproduction-lens 链，详细可审计 score（包括 D2.1 best `gamma ≈ 0.749` / `score 2.033`、size delta、SNR scale 等估计项）见 §14.5。

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

## 8. 哪些话现在可以说，哪些话不能说（口径 A：all-crossing）

> 本节是口径 A 下的允许 / 禁止结论。口径 B 的对应清单在 §14.11；双口径合并的 unified forbidden claim 在 §15.3。本节与 §14.11 / §15.3 之间不冲突：§8 与 §14.11 是各自口径内的具体说法，§15.3 收口于双口径不互相替代等共同约束。

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

## 9. 读者向最终解释（口径 A：all-crossing）

> 本节是口径 A 的读者向叙事。口径 B 的等价叙事是 §14.1 + §14.12（lens 定义 + 最终收口）；双口径合并的读者向叙事见 §15.4。

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

## 10. 对分析报告体系的影响（口径 A：all-crossing）

> 本节是口径 A 视角下的报告体系建议。口径 B（selected-annulus）报告体系建议合并入 §14（已等规模并入），口径 B 不另起独立读者向报告；双口径同时在 §15 整合。

加入 v2 后，原来的读者向报告需要全面改写口径，但不需要推翻原全量计算：

| 原报告容易写成 | v2 后应改成 |
|---|---|
| "模拟找到了最优路线" | "相对模拟给出主工程候选，v2 检查其在真实仪器约束先验下的稳定性" |
| "检测率 / 事件数" | "相对先验分数 / 合成代理计数，不是实际观察到的事件数" |
| "SNR 足够" | "只能讨论不同仪器情景下的相对探测器风险，不能写成已校准信噪比" |
| "404 灵敏度高所以可能更好" | "404 nm 是机制、旁路或上下文对照；热效应旁路不得加分" |
| "局部环带窗口支持某路线" | "局部环带窗口是并行诊断视角，不能替代全局交叉排序" |
| "Tsuyama 已复现" | "Tsuyama 固定条件和趋势对齐；论文数值校准复现未签发" |
| "下一步做采集" | "v2 内不做采集；采集只能作为 v2 之后的独立研究计划另行设计" |

因此，现在最适合保留以下报告分层：

1. **读者向综合报告**：就是本文。v4.0 起以双口径并立形式同时承载 all-crossing（§1–§13）与 selected-annulus paper-audit（§14），并在 §15 做综合收口。
2. **技术附录/阶段报告**：保留阶段门控、运行清单、校验和测试证据，供审计而非普通读者阅读。
3. **post-v2 P0-P18 审计/有界 trace 证据**：作为本文第 13 节（口径 A）的增量证据，不另起读者版结论口径；selected-annulus 口径下的对应反映在 §14.10。
4. **selected-annulus paper-audit raw provenance**：[reports/49](49_Tsuyama_Phase2_paper_calibrated_selected_annulus_analysis.md) 与 [reports/71](71_EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit_analysis.md) 仍作为 raw provenance 保留；本文 §14 是它们的读者级合并。

---

## 11. 本报告使用的本地证据（双口径）

> 本节列出双口径在本报告中使用的本地证据。口径 A、口径 B 的证据各自分组；§14 还会在自己的段落里给出 selected-annulus 专属的工具/输出清单。

核心 v2 证据（口径 A）：

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

Tsuyama 对照证据（双口径共用）：

```text
archive/tsuyama/48_tsuyama六篇严格补读结论.md
archive/tsuyama/51_tsuyama_paper_aligned全论文闭环审查.md
archive/tsuyama/56_tsuyama已解决与尚未解决问题_中英对照表.md
archive/tsuyama/57_工程主线与Tsuyama论文结果趋势对照_中英对照.md
archive/tsuyama/58_tsuyama固定条件对标与结果表.md
```

selected-annulus 口径主源（口径 B）：

```text
reports/49_Tsuyama_Phase2_paper_calibrated_selected_annulus_analysis.md
reports/70_EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit_plan_for_external_review.md
reports/71_EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit_analysis.md
results/tsuyama_phase2_paper_target_audit_v1/
results/tsuyama_phase2_acceptance_baseline_v1/
results/tsuyama_phase2_parameter_inverse_full_v1/
results/tsuyama_phase2_acceptance_full_inverse_v1/
results/tsuyama_phase2p5_operator_phase_bfp_smoke_v1/
results/tsuyama_phase2p5_operator_phase_bfp_acceptance_smoke_v1/
results/tsuyama_phase2p5_d2p1_refphi_collection_smoke_v1/
results/tsuyama_phase2p5_d2p1_refphi_collection_acceptance_v1/
results/tsuyama_phase2p6_paper_reproduction_fit_d2p1_v1/
results/tsuyama_phase2p6_paper_reproduction_fit_full_inverse_v1/
results/tsuyama_phase2p6_paper_reproduction_fit_3000e_v1/
results/tsuyama_phase2p6_paper_reproduction_fit_3000e_acceptance_v1/
results/tsuyama_phase2p7_snr_response_rescore_3000e_v1/
results/tsuyama_phase2p8_reviewed_score_rescore_3000e_v1/
results/tsuyama_phase2p9_maximal_upper_rescore_3000e_v1/
results/tsuyama_phase2p9_maximal_upper_rescore_full_inverse_v1/
results/tsuyama_phase2p9_maximal_upper_rescore_d2p1_v1/
results/tsuyama_phase2p10_size_response_decomposition_3000e_v1/
results/tsuyama_phase2p10_size_response_decomposition_full_inverse_v1/
results/tsuyama_phase2p10_size_response_decomposition_d2p1_v1/
results/tsuyama_phase2p11_response_compression_rescore_3000e_v1/
results/tsuyama_phase2p11_response_compression_rescore_full_inverse_v1/
results/tsuyama_phase2p11_response_compression_rescore_d2p1_v1/
results/tsuyama_2022_classification_lane_phase2_smoke_v1/
results/instrument_hardware_feasibility_v1/
results/tsuyama_paper_statistics_sensitivity_v1/
results/ev_nodi_realism_v2_R5_2_bounded_scenario_prior_audit/
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

## 12. 最终收口（口径 A：all-crossing）

> 本节是口径 A 的最终收口。selected-annulus 口径的最终收口在 §14.12。两个口径共同收口在 §15.4。

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

## 13. post-v2 P0-P18 合并更新（口径 A：all-crossing）

> 本节是口径 A 下的 post-v2 P0-P18 证据合并。selected-annulus 口径下 post-v2 阶段的反映情况在 §14.10。双口径下 P0-P18 的对照见 §15.2。

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
| p0 | P0 release package 从阶段报告上升为 review-ready mandatory audit 包，完成 P0 证据链闭环并对报告 88 合并生效。 | `REVIEW_PACKAGE_MANIFEST.json`、`REVIEW_PACKAGE_HASHES.sha256`、`results/post_v2_mandatory_audit/`；并通过 `python -m pytest tests/test_review_package_manifest.py` 与 `python tests/run_tests.py --workers 7`。 | 本阶段把 v2 sidecar 从阶段叙事中提取为主审计入口，并与 `reports/88` 的 P0-P18 边界统一；未变更 `v2 无实测校准` 约束。 | 证据传播仍在外部 review 打包层面有一次性优化空间；未提供 measured route calibration 前提下不改主路线晋升。 |
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

---

## 14. selected-annulus paper-audit 口径完整分析（口径 B）

> 本节是口径 B（selected-annulus paper-audit 口径）的完整分析，与 §1–§13 的口径 A 并立、规模相当。证据 provenance 来自 [reports/49_Tsuyama_Phase2_paper_calibrated_selected_annulus_analysis.md](49_Tsuyama_Phase2_paper_calibrated_selected_annulus_analysis.md) 与 [reports/71_EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit_analysis.md](71_EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit_analysis.md)。本节做读者级合并，不再要求读者回去翻 49/71 才能理解结论；49/71 仍作为 raw provenance 保留。
>
> 与口径 A 的关系见 §15。本节末尾 §14.9–§14.10 显式列出 selected-annulus 口径下 realism v2 R0–R7.2 与 post-v2 P0–P18 的反映情况；不存在等价证据的阶段会被显式标注为 "selected-annulus 口径下未扩展"。

### 14.1 selected-annulus 口径定义、问题域与边界

selected-annulus 口径不是 all-crossing 全局排序的子集，而是另一个问题：

```text
口径 B 问题：
在 selected-annulus 0.5-0.8 固定窗口下，
若使用 Tsuyama paper-audit proxy target（Table S1 Ag/Au signal、
Au size exponent 2.3、Au30/Au20 SNR ratio 33/12 等），
当前 simulator 的低自由度估计参数能否自然复现这些数值？
```

它和口径 A 的关键差异如下：

| 维度 | 口径 A：all-crossing | 口径 B：selected-annulus paper-audit |
|---|---|---|
| 比较窗口 | 全 BFP 全 crossing | 固定 selected-annulus `0.5-0.8` |
| 评估对象 | EV/NODI 工程路线（404 / 488 / 532 / 660 nm 全 grid） | Tsuyama paper-audit candidate（Ag40/Au40，Au20/30/40/60） |
| 主排序候选 | 32,032 基础设计组合 + 8 仪器情景 | `52` Phase 2 family-ladder candidates + D2.1 局部 12 variants + size-only F-family + reproduction rescore 系列 |
| 主结论形式 | route role（main / context / probe / control / optional） | candidate release status（accepted / negative / diagnostic） |
| 当前结论 | 660 nm `800x1400` / `800x1500` 双 main，conditional_relative_main | `negative_or_diagnostic_result_only`，无 accepted candidate |
| 主 No-Go | 无（已收口） | `raw_size_response_alignment_not_met` |
| 是否替代另一口径 | 否 | 否 |
| 是否解锁 calibration | 否 | 否 |

selected-annulus 口径不解锁任何 calibrated SNR / absolute LOD / true concentration / biological specificity claim；它的合法产物只有：

```text
paper-audit proxy candidate 的 release status
estimated-parameter reproduction lens 的 score 与 fit term
sidecar guardrail（不可修改 selected-annulus 边界、不可替代 all-crossing 排序）
```

### 14.2 G0/G1 — Target audit 与 baseline acceptance

口径 B 的 Phase 2 把 Tsuyama paper side 信息拆成四类 target，避免把 diagnostic-only 当 hard target：

| 类别 | 示例 | 是否 hard target |
|---|---|---|
| Direct / audit | Table S1 Ag40/Au40 `interferometric_column_ratio`（488/532/660 nm） | 保留 strict 审计，但因 Ag 行 vs "interferometric scattering = scattering 开方" 文字解释存在歧义，已不再是唯一 hard target |
| Formula-consistent | Table S1 scattering cross-section 列的 `sqrt_scattering_column_ratio` | 当前推荐 hard signal-ratio mode |
| Recomputed-Mie | 用 Table S1 fixed n,k 在本 simulator 内重算 `sqrt(Csca_Ag/Csca_Au)` | inferred / cross-check |
| Inferred | Au size exponent `2.3`、Au30/Au20 SNR ratio `33/12 ≈ 2.75` | hard |
| Operational | Au30/40/60 selected-annulus detection proxy bands、Au20 upper-detection guard、Au20 low-sensitivity warning、selected-annulus geometry guardrail | hard |
| Diagnostic only | classification accuracy `71.9 ± 4.0%`、2020 POD Au20 near-100% counting、2024 paired POD+NODI classification | 仅诊断，不入 hard target |

Baseline acceptance（read-only，不重跑 simulation）：

| 指标 | 状态 | 解释 |
|---|---|---|
| best candidate | `baseline_current_estimates__paper_5sigma_signal_size_transfer_fit` | joint_fit_score `0.498779` |
| paper_fit_status | `candidate_joint_fit_with_paper_transfer` | 依赖 transfer + size correction |
| target audit | pass | hard target 不含 diagnostic_only |
| detection alignment | `partial_pass_with_Au20_low_warning` | Au30/40/60 median pass；Au20 only-low miss |
| signal ratio | pass | calibrated Ag/Au residual 很小 |
| size exponent | pass | calibrated Au exponent = `2.3`，delta 在 guardrail 内 |
| SNR ratio | pass | Au30/Au20 ratio = `3.36086`，在 log tolerance 内但偏高 |
| classification | diagnostic_complete | feature export 对齐，但本地 `sklearn` 不可用，`no_accuracy_claim` |
| no-go status | pass | baseline 不签 accepted；需要 family-ladder inverse confirmation |

baseline 可作为 Phase 2 起点，但不能直接签为最终 accepted；原因不是 Au20 偏低，而是 baseline 还没有证明 raw / non-transfer 参数族能自然解释 signal ratio 与 size-response。

### 14.3 G2 — Family-ladder inverse search 主结果

`tools/one_shot/tsuyama_phase2_parameter_inverse.py` 把 inverse search 拆成 A–E 五族，Phase 2.5 又新增 raw-only `D2_operator_phase_bfp_raw`，Phase 2.6 再新增 size-only `F_paper_reproduction_fit`：

| Family | 角色 |
|---|---|
| A | blank / threshold / colored noise / post-readout noise |
| B | logger / lock-in / pulse width policy |
| C | transport / event shape / fluxmix |
| D | reference / collection / rho / BFP ROI |
| D2 | paper-aligned reference phase / BFP ROI / collection operator raw search |
| E | bounded Ag transfer / Au size-response（local paper-fit lens） |
| F | size-only paper reproduction fit（global Au size flattening + global SNR scale） |

`10000 events/case`、seeds `42 / 43 / 44`、`8 workers`、`52` candidates × `3` seeds = `156` summary rows、`5616` raw rows，runtime 约 `24968 s`（约 `6.94 h`）。

整体排序：

| 排名口径 | family | best candidate | median score | 解读 |
|---|---|---|---:|---|
| 全局 best | E | `baseline_current_estimates__paper_5sigma_signal_size_transfer_fit` | `0.496282` | signal ratio、size exponent、SNR proxy 都能被 local lens 拉齐 |
| E 次优 | E | `low_noise_stack_uniform_accessible__paper_5sigma_signal_size_transfer_fit` | `0.519414` | 仍依赖 signal + size transfer |
| raw best | B | `tau_2ms` | `2.641891` | 不触发 guardrail，但仍是 `candidate_needs_signal_transfer_or_phase_fit` |
| D best | D | `refspace_0p25__paper_5sigma_sensitivity` | `2.855049` | reference-space 调整未解决 signal/size residual |
| A best | A | `baseline_current_estimates__paper_5sigma_sensitivity` | `2.875281` | readout/noise family 不能独立对齐 |
| C best | C | `low_noise_stack_fluxmix_0p10` | `2.915548` | transport/fluxmix family 不能独立对齐 |

acceptance 触发当前唯一主 No-Go：

```text
raw_size_response_alignment_not_met
```

raw / non-transfer family 共 `38` 个可用 candidate；strict Table S1 target 下 `raw_strict_signal_aligned_count = 0`（标 `strict_table_s1_signal_unresolved_formula_signal_pass` diagnostic warning）；formula-consistent Table S1 target 下 `raw_formula_signal_aligned_count = 27`（说明 Ag/Au raw signal mismatch 很大一部分来自 target-mode 歧义）；但 `raw_size_aligned_count = 0`、`raw_joint_signal_size_aligned_count = 0`，因此不能签 accepted。

detection side 状态为 `partial_pass_with_Au20_low_warning`：Au20 在 `6` 个 joint cases 中只有 `3` 个进入 operational band，且 miss 全部偏低，与论文 Au20 weak-SNR / not-all-detected 描述相容；Au30 为 `5/6` minor/borderline warning；Au40/Au60 为 `6/6`。

最终签发：

```text
release_status = negative_or_diagnostic_result_only
no_accepted_paper_calibrated_candidate = true
```

### 14.4 G2.5 — D2 raw-operator + D2.1 局部 smoke

`D2_operator_phase_bfp_raw` 用 `1500 events/case`、3 seeds、8 workers，`20` candidates、`60` summary rows、`2160` raw rows、`12` guardrail failure rows，runtime `1827.9 s`：

| 口径 | best candidate | 结果 | 解释 |
|---|---|---:|---|
| lowest joint score | `tau_2ms_global_refphi_plus` | median score `2.444` | 比 `tau_2ms_control` 略好，但仍需 signal transfer / phase fit |
| formula-consistent Ag/Au signal | `tau_2ms_bfp_lobe_045` | formula signal score `0.0098` | Ag/Au signal 最好，但触发 hard guardrail 且 size exponent 更差 |
| raw Au size exponent | `tau_2ms_global_refphi_plus` | exponent median `3.090` | D2 中最接近 `2.3` 的 raw size-response，但仍高出约 `0.79` |
| promote rule | none | `0` candidates | 没有候选同时满足 formula signal、size exponent、guardrail 和 detection sanity |

随后 D2.1 把搜索缩到 `tau_2ms_control`、`global_refphi_plus` 的 `+0.2 / +0.4 / +0.6` 小步长、`collection_narrow` 与组合，`2000 events/case`、3 seeds、8 workers：

| candidate | joint score | formula joint score | formula signal score | raw Au exponent | size score | 判断 |
|---|---:|---:|---:|---:|---:|---|
| `tau_2ms_global_refphi_plus_collection_narrow` | 2.377 | 0.687 | 0.0286 | 3.071 | 1.212 | 全局 score 最低，guardrail pass，但 size 仍失败 |
| `tau_2ms_global_refphi_plus_0p6` | 2.383 | 0.677 | 0.0322 | 3.050 | 1.149 | raw size 最好，但仍明显高于 2.3 |
| `tau_2ms_global_refphi_plus` | 2.471 | 0.761 | 0.0334 | 3.097 | 1.297 | 比 control 改善，但不够 |
| `tau_2ms_control` | 2.635 | 0.906 | 0.0328 | 3.190 | 1.616 | D2.1 baseline |

D2.1 价值在于**确认趋势**：global reference phase 往正方向移动确实能稳定压低 raw Au exponent，窄 collection + `+0.4` 组合能进一步改善 joint score；但最好的 raw exponent 仍约 `3.05`，没达到 `<= 2.85` 的 promote floor，更没接近 `2.3`。因此 D2.1 后**不进入** raw-family `10000 events/case` confirm。下一步只能在两个目标里二选一：要 physical calibration 就需实测 blank、BFP/slit/ROI、lock-in/logger 与 Au raw trace；只要数值复现就转入显式 paper-reproduction rescore（即 G2.6+），不再扩大 raw 自由度。

### 14.5 G2.6–G2.11 — 估计参数 reproduction lens 链

口径 B 选了"用估计项尽量复现论文数值"的目标。Phase 2.6–2.11 全部是 read-only rescore + 一次 size-only `3000 events/case` 小确认；不修改 selected-annulus、不回写 EV full-grid、不开 per-diameter / per-geometry / per-case correction。

#### 14.5.1 Phase 2.6 — paper-reproduction formula + size-only F-family confirm

只允许两个全局 reproduction-only fit terms：一个 power-law size-response delta（作用于所有 Au 粒径、全部 wavelength/geometry），一个 single global SNR scale（把 Au20/Au30 local SNR 映射到论文 anchor）。

| rescore source | best candidate | formula score | required Au size delta | SNR scale | status |
|---|---|---:|---:|---:|---|
| D2.1 local smoke | `tau_2ms_global_refphi_plus` | `3.7428` | `-0.7973` | `0.7279` | `bounded_reproduction_fit` / `reproduction_fit_not_met` |
| full inverse | `refspace_0p25__paper_5sigma_sensitivity` | `4.6815` | `-0.9583` | `0.4138` | `bounded_reproduction_fit` / `reproduction_fit_not_met` |
| full inverse E-family ref | `baseline_current_estimates__paper_5sigma_signal_size_transfer_fit` | `5.6926` | `-0.9632` | `0.4200` | `maximal_paper_fit` / `reproduction_fit_not_met` |

最小可解释 correction 是全局 Au size-response flattening；D2.1 底座所需 delta 约 `-0.80`，比 full inverse / E-family 的约 `-0.96` 更温和。Phase 2.6 只发布 `paper_reproduction_fit_only_not_physical_calibration`。

随后用 `F_paper_reproduction_fit`、`3000 events/case`、4 candidates × 3 seeds = 12 summary rows、8 workers 做 size-only 小确认：

| candidate | formula joint score | reproduction score | required Au size delta | SNR scale | detection status | 判断 |
|---|---:|---:|---:|---:|---|---|
| `tau_2ms_global_refphi_plus_0p6__paper_5sigma_size_response_fit` | `0.2788` | `3.9541` | `-0.8782` | `0.7304` | pass + Au20 high-outlier warning + Au30 minor warning | size-only reproduction best；未过 bounded pass/partial |
| `tau_2ms_global_refphi_plus_collection_narrow__paper_5sigma_size_response_fit` | `0.3000` | `16.4235` | `-0.8414` | `0.5062` | detection loss 高 | joint score 接近，但 reproduction score 被 detection/SNR 拉低 |
| `tau_2ms_global_refphi_plus__paper_5sigma_size_response_fit` | `0.2983` | `15.6535` | `-0.8943` | `0.7266` | detection loss 高 | 不优于 `+0.6` |
| `tau_2ms__paper_5sigma_size_response_fit` | `0.3337` | `16.0397` | `-0.9563` | `0.7193` | detection loss 高 | baseline reproduction 对照 |

显式全局 size flattening 把 size exponent score 归零，formula-consistent signal 保持 pass；但综合 score 仍高于 `<= 2.0` 的 bounded partial threshold。不进入 10000-event confirmation，不签任何 accepted calibration。

#### 14.5.2 Phase 2.7 — single global SNR response rescore

新增 `paper_reproduction_snr_response` primary score mode：一个全局 SNR/readout power-law exponent + 一个全局 scale。同一 best candidate 不变：

| rescore mode | best candidate | score | SNR response exponent | SNR ratio loss | detection loss | complexity loss | 判断 |
|---|---|---:|---:|---:|---:|---:|---|
| Phase 2.6 size-only | `..._global_refphi_plus_0p6__paper_5sigma_size_response_fit` | `3.9541` | none | `1.4053` | `1.0500` | `1.3400` | size-only best，未过 partial |
| Phase 2.7 SNR response | 同上 | `3.8076` | `0.8120` | `0.4235` | `1.0500` | `1.9308` | SNR ratio 显著改善，复杂度抵消一部分；仍未过 partial |

#### 14.5.3 Phase 2.8 — reviewed / descriptive rescore

`paper_reproduction_reviewed`：strict Table S1 residual 仅报告不入 primary score（因为 Table S1 Ag 行 vs "interferometric scattering = 开方" 文字存在 target-mode 歧义）；detection warning 与 fit complexity 降权。

| rescore mode | best candidate | score | SNR response exponent | detection loss | strict loss | complexity loss | status |
|---|---|---:|---:|---:|---:|---:|---|
| Phase 2.7 SNR response | 同上 | `3.8076` | `0.8120` | `1.0500` | `0.1788` | `1.9308` | `reproduction_fit_not_met` |
| Phase 2.8 reviewed/descriptive | 同上 | `1.9385` | `0.8120` | `0.3500` | `0.0000` | `0.9654` | `bounded_reproduction_partial_descriptive` |

读法非常严格：Phase 2.8 不是新的 acceptance pass，而是说明在"只求论文数值复现叙事"的 reader-facing score 下，当前低自由度估计项已达 partial reproduction；但 `candidate_release_status` 仍为 `negative_or_diagnostic_result_only`，No-Go 仍是 `raw_size_response_alignment_not_met`。

#### 14.5.4 Phase 2.9 — maximal upper-bound rescore

`paper_reproduction_maximal_upper`：允许 hypothetical strict Table S1 per-wavelength Ag transfer（受 `0.25-4.0` bounded gain guardrail 约束，单独记入 complexity / DOF）。

| source | best candidate | maximal score | maximal status | size delta | strict Ag transfer gain range | 解读 |
|---|---|---:|---|---:|---:|---|
| 3000-event size-only | `..._global_refphi_plus_0p6__paper_5sigma_size_response_fit` | `1.2869` | `maximal_paper_fit_partial_upper_bound` | `-0.8782` | `1.810-3.070` | 仍 partial；低自由度候选不靠 strict Ag transfer 已可读 |
| full inverse | `refspace_0p25__paper_5sigma_sensitivity` | `0.9814` | `maximal_paper_fit_upper_bound` | `-0.9583` | `1.902-3.116` | 上限 score 可过 `<=1`，但需要更强 size delta + strict Ag transfer |
| D2.1 local smoke | `tau_2ms_global_refphi_plus_collection_narrow` | `0.9893` | `maximal_paper_fit_upper_bound` | `-0.7706` | `1.758-3.085` | 需要的 size delta 最温和，但仍是 high-DOF upper-bound lens |

Phase 2.9 给出**可映射性上限**，不是 raw-family 自然复现。继续追更低分只能引入 per-diameter / per-geometry / per-case correction 或 detection logistic remap，越过本项目允许的 estimated-parameter 复现边界。

#### 14.5.5 Phase 2.10 — raw Au size-response residual decomposition

按 wavelength × geometry × observable × adjacent size pair 拆 raw Au exponent：

| source / best | observable | median exponent | residual vs 2.3 | 最主要相邻粒径段 | 解读 |
|---|---|---:|---:|---|---|
| D2.1 `tau_2ms_global_refphi_plus_collection_narrow` | peak height | `3.0679` | `+0.7679` | `40-60` | 当前 raw 最优底座；仍明显偏陡 |
| D2.1 best | local SNR | `3.0882` | `+0.7882` | `40-60` | local SNR 没有解决 size-response |
| D2.1 best | peak margin z | `3.3165` | `+1.0165` | `40-60` | margin 口径更陡 |
| D2.1 best | peak height × width | `3.9420` | `+1.6420` | `40-60` | width/area-like 口径更不适合作为 size target |
| 3000-event size-only best | peak height | `3.1738` | `+0.8738` | `40-60` | size-only correction 前的 raw 底座更陡 |
| full inverse maximal best | peak height | `3.2541` | `+0.9541` | `40-60` | full inverse 上限分低，但 raw size 底座更陡 |

D2.1 best peak-height case-level decomposition：最接近的组合是 `660 / 1200x550`（exponent `3.0335`）和 `660 / 800x550`（`3.0456`）；最差是 `532 / 800x550`（`3.1563`）。**所有 6 个 peak-height case 的 limiting pair 都是 `40-60`**，不是 `20-30`。这关键地说明：继续调 Au20 检出率、Au20 lower band 或 Au20 SNR 解决不了 raw exponent 偏陡；真正需要解释的是大粒径段 readout / phase / trajectory / collection 是否存在全局压缩或饱和。

只读估算：用单一 global pulse-height response compression `signal' = signal^gamma`，D2.1 best 需要 `gamma ≈ 0.749` 才能把 peak-height exponent 映射到 `2.3`；该 gamma 把 Au30/Au20 SNR ratio 从 `3.28` 压到约 `2.43`，formula-consistent Ag/Au loss 仍约 `0.041`，strict Table S1 loss 仍高。response compression 是比 per-diameter correction 更值得考虑的下一种估计项；不过它仍是 reproduction lens，不是 raw calibration。

#### 14.5.6 Phase 2.11 — single global response-compression rescore

`paper_reproduction_response_compression`：同一全局 `gamma` 同时作用于 Au size-response、Au20/Au30 SNR ratio、Ag/Au signal ratio；只允许一个 global SNR scale；不允许 per-wavelength / per-geometry / per-diameter / per-case gamma；不做 detection logistic remap。

| 输入 | best candidate | gamma | response-compression score | status |
|---|---|---:|---:|---|
| D2.1 local smoke | `tau_2ms_global_refphi_plus_collection_narrow` | `0.749` | `2.033` | `response_compression_fit_not_met` |
| full inverse | `low_noise_stack` | `0.703` | `2.651` | `response_compression_fit_not_met` |
| 3000-event size-only confirmation | `..._global_refphi_plus_0p6__paper_5sigma_size_response_fit` | `0.724` | `3.722` | `response_compression_fit_not_met` |

D2.1 best 的 score breakdown：SNR-ratio loss `0.387`、SNR-anchor loss `0.0146`、formula-consistent Ag/Au loss `0.0410`、complexity penalty `0.818`、detection loss `0.65`（合计约 `1.91`，与 total score `2.033` 的差额 ≈ `0.12` 来自尚未在 breakdown 中拆出的 strict Table S1 residual / Ag-anchor 等次要项；以 [reports/49](49_Tsuyama_Phase2_paper_calibrated_selected_annulus_analysis.md) 原文 score 为准）。`gamma` 是按 target / raw Au exponent 反推出的全局 readout/pulse-height compression，因此 size loss 贴近 0 是该 reproduction lens 的定义结果；真正残差检验是 SNR ratio、paper-normalized SNR anchor、formula-consistent Ag/Au signal、detection warning 与 complexity。total score `2.033` 仍略高于 bounded partial 阈值 `2.0`。

```text
这 0.033 不应通过调权重抹掉。
剩余项来自真实的 SNR ratio residual、gamma complexity 与 detection warning。
```

至此，计算路线已基本收口；再追更低分就需要 per-diameter / per-geometry / per-case / logistic remap 等过拟合项。

### 14.6 G2.14–G2.15 — Stop-decision 后的边界检查

#### 14.6.1 Instrument-aware feasibility（ET-2030 + LI5640）

不是继续 paper-fit 搜索，而是检查实际读出链的量级边界。`tools/audits/instrument_hardware_feasibility.py` 用 ET-2030 silicon responsivity / NEP / 0.4 mm active area、LI5640 current/voltage sensitivity、time constant 与 filter-order prior 生成 `216` 个 feasibility rows；每行同时给出 current-input / low-noise TIA 与 50 Ω voltage path 两种接法的 verdict：

| 接法（同 216 rows 内的列 verdict） | comfortable margin | near minimum | below minimum sensitivity |
|---|---:|---:|---:|
| current input / low-noise TIA | `216/216`（全部） | 0 | 0 |
| 50 Ω voltage path | 0 | `5/216` | `211/216` |

结论是硬件估计支持 current input / TIA 作为可行路线；50 Ω voltage path 几乎全部低于最小 voltage sensitivity（仅 `5/216` near minimum）。这只是 instrument feasibility estimate，不解锁 absolute SNR calibration。它支持第一轮实验**先核对 current-input / TIA 接法和量程**，而不是继续在 optical surrogate 里调相位。

#### 14.6.2 Paper-statistics sensitivity boundary

用 Phase 2.10 limiting-pair decomposition 只读估算 IQR trimming、finite-count sampling 或 vendor diameter distribution 各需贡献多大才能把 limiting pair slope 拉到 `2.3`：

| 类别 | 行数 | 解读 |
|---|---:|---|
| `paper_statistics_unlikely_alone` | `274/288` | 单凭论文统计 / 粒径分布解释不通 |
| `paper_statistics_borderline` | `14/288` | 边界 |

最佳 D2.1 local-SNR case 仍需要对 high-diameter signal 做中位约 `30.6%` suppression，peak-height 需要约 `31.8%`。结论：paper statistics / size distribution 可以作为解释贡献项，但**没有 event-level pulses 或 measured size distribution 时，不能单独承担 raw Au size-response mismatch**。

### 14.7 R5.2 — Bounded scenario-prior audit + selected-annulus sidecar guardrail

来自 [reports/71](71_EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit_analysis.md)。R5.2 是 bounded、posthoc、existing-R5-artifact only 的审计：

```text
audited route IDs = 33
audited existing R5 rows = 14784
scenario bundles = 8 existing R5 bundles
new case rows = 0
new scenario bundles = 0
new stochastic seeds = 0
new solver cases = 0
new experiments = 0
```

R5.2 在 selected-annulus 口径下产出 13 个 pre-registered outputs，其中与口径 B 直接相关的 sidecar guardrail 记录如下：

```text
selected_annulus_replaces_all_crossing_ranking = false
selected_annulus_bound_change_authorized = false
thermal_sidecar_used_to_increase_NODI_score = false
```

R5.2 的核心审计 finding：

```text
weak_reference_control 在 8/8 个 existing R5 scenario bundles 中超过 main_660
20/20 个 above-main context routes 在全部 8 个 scenario bundles 中超过 main_660
```

均值：

```text
main_660 mean relative-prior score = 0.126095
weak_reference_control mean relative-prior score = 0.152257
above-main context-route family mean = 0.151919
```

Top context-route audit rows：

```text
660_500x1500 mean = 0.196396, ratio_vs_main = 1.557516
660_500x1400 mean = 0.189745, ratio_vs_main = 1.504774
660_500x1300 mean = 0.182575, ratio_vs_main = 1.447910
660_500x1200 mean = 0.173859, ratio_vs_main = 1.378789
660_600x1500 mean = 0.165472, ratio_vs_main = 1.312275
```

所有 context warning rows 仍记：

```text
context_route_promotion_authorized = false
route_promotion_eligible = false
interpretation = systematic_above_main_context_warning_not_route_promotion
```

R5.2 的最终决定：

```text
selected_future_recommendation_class = prepare_route_prior_model_revision_plan_only
audit_decision = systematic_weak_reference_and_context_prior_warning_blocks_R6_plan
```

Main-660 仍锁定 `660_800x1400` 与 `660_800x1500`；不允许 R6 plan execution、route promotion、main-660 redefinition、optional `660 / 900x1400` redefining main-660、selected-annulus 边界变更、route-specific manual sign flips 或 calibrated/absolute claims。

R5.2 用 `python -m pytest -q` 全套 853 passed in 206.47s 通过，review-bundle integrity / 提取 bundle 重测均 pass。

### 14.8 selected-annulus 口径下的 Tsuyama 论文对照

口径 B 的 paper geometry 与口径 A 的 EV engineering geometry 必须保持双栏 claim：

| Lane | Geometry | Allowed claim |
|---|---|---|
| Tsuyama paper-audit（口径 B 主） | `660 / 800x550`、`660 / 1200x550`，并含 488/532 对照 | selected-annulus paper-audit proxy；本轮为 negative / diagnostic，不签 accepted candidate |
| EV engineering（口径 A 主） | `660 / 800x1400`、`660 / 800x1500` | reference-useful long-wave candidate，不是 paper geometry 复现 |
| Boundary control（双口径共用） | `660 / 700x1500` | weak-reference / NA boundary control |
| Short-wave engineering（双口径共用） | `404 / 600x1300`、`404 / 800x700` sanity | short-wave mechanism / blank / exposure validation，不是 Tsuyama direct target |

口径 B 不阻塞 660/404 第一轮实验准备；660/404 实验真正需要的是 blank、BFP、Au ladder、EV mimic、404 exposure/integrity 与 PEG/fluidic 数据。selected-annulus 口径只让 Tsuyama paper-audit 叙事更可审计。

EV route shadow all-crossing dashboard（口径 B 内做的 sanity，不进入 Tsuyama paper score）：

| 指标 | 数值 | 解释 |
|---|---:|---|
| route_count | 572 | EV route-level full-grid route 数 |
| selected_all_uplift_median | `1.383647` | selected-annulus 系统性偏乐观，但仍在当前 uplift warning 上限内 |
| selected_all_uplift_max | `1.556754` | 未超过 `1.6x` warning threshold |
| selected_fraction_mean | `0.401984` | selected 子集约覆盖 40% 事件 |
| selected_contribution_mean | `0.060904` | annulus 子区对全事件分母的平均贡献 |
| all_crossing_detection_mean | `0.114024` | EV route all-crossing mean detection |
| selected_detection_mean | `0.151295` | selected-annulus mean detection |
| reference_useful_routes | `507` | 可作 selected cross-check |
| weak_reference_boundary_routes | `65` | 只能作边界对照 |

这组 shadow 指标支持继续使用 selected-annulus 作为 paper-audit lens；同时再次提醒：selected-annulus 不应替代 all-crossing 主工程口径（口径 A），反过来口径 A 的工程主排序也不能替代口径 B 的 paper-audit 结论。

### 14.9 selected-annulus 口径下 realism v2 R0–R7.2 的反映

| realism v2 阶段 | selected-annulus 口径下的反映 |
|---|---|
| R0 / R2 anchor smoke | selected-annulus 口径下未独立扩展；R5 全量库 selected dashboard 已覆盖 |
| R3 reduced grid / R3b uncertainty | selected-annulus 口径下未独立扩展；R5 全量库 selected dashboard 已覆盖 |
| R4 representative full-wave / R4 numerical solver / R4 route revision / R4.2 main-660 nearwall mesh | selected-annulus 口径下未独立扩展；R5.2 sidecar 仍记 `selected_annulus_replaces_all_crossing_ranking = false`，R4.2 nearwall 结论双口径共享 |
| R5 full-grid v2 | EV route shadow all-crossing dashboard 即基于 R5 全量库；`selected_all_uplift_median ≈ 1.384x`、`max ≈ 1.557x`，未越过 `1.6x` warning |
| R5.1 route-role stability | 与口径 A 共享结论：route role 在 R5 scenario bundles 内稳定；selected-annulus 不替代 ranking |
| R5.2 bounded scenario-prior audit | **selected-annulus 口径主源**：见 §14.7 |
| R5.3 route-prior model revision | selected-annulus 口径下未独立扩展；其结论以口径 A 为准 |
| R6 route-prior sensitivity | selected-annulus 口径下未独立扩展；R5.2 已 block R6 plan |
| R7 route-prior mechanistic decomposition / R7.1 operator artifact validation / R7.2 operator artifact gap register | selected-annulus 口径下未独立扩展；机制分解和 artifact gap register 在双口径共享，详见 §15.2 |
| no-measured-data closure | 双口径共享 closure boundary：`calibrated_claim_allowed = false` |

### 14.10 selected-annulus 口径下 post-v2 P0–P18 的反映

| post-v2 阶段 | selected-annulus 口径下的反映 |
|---|---|
| P0 mandatory audit | P0 把 BFP ROI、Tsuyama BFP、noise/readout、EV/sample uncertainty、**selected-annulus lens**、pairwise inversion、forbidden-claim blockers 一起纳入审计；selected-annulus 是 P0 audit 的 lens 之一，不是路线晋升判据。详见 §13.1 |
| P1 physical-ceiling diagnostic contracts | selected-annulus 口径下未独立扩展；4 条 contract 是 surrogate-risk reduction 通用 |
| P2 bounded physical-solver readiness | selected-annulus 口径下未独立扩展；solver execution blocked |
| P3 minimal pilot design | selected-annulus 口径下未独立扩展 |
| P4 dry-run preflight | selected-annulus 口径下未独立扩展 |
| P5 authorization gate | selected-annulus 口径下未独立扩展 |
| P6 minimal bounded Green kernel trace | selected-annulus 口径下未独立扩展；P6–P16 是 all-crossing main-660 内部 trace lane |
| P7 / P9 / P11 / P13 / P15 / P17 lane authorization design | selected-annulus 口径下未独立扩展 |
| P8 phase-gradient trace | selected-annulus 口径下未独立扩展 |
| P10 curvature-balance trace | selected-annulus 口径下未独立扩展 |
| P12 resonance-compactness trace | selected-annulus 口径下未独立扩展 |
| P14 phase-curvature residual trace | selected-annulus 口径下未独立扩展 |
| P16 phase-curvature residual trace | selected-annulus 口径下未独立扩展 |
| P18 synthesis stop/continue | 双口径共享：`bounded_lanes_sufficient_for_route_promotion = false`、`stop_mechanical_lane_roll_forward_pending_p19_evidence_strategy`；selected-annulus 口径下也不解锁 paper calibration |

显式约束：P19 evidence strategy gate 必须在两个口径下都给出 acceptance criteria。selected-annulus 口径要求至少包含 measured Au raw trace、blank、BFP/slit/ROI、lock-in/logger，否则 paper-audit lane 仍只能停在 estimated-parameter reproduction lens。

### 14.11 口径 B 的允许 / 禁止结论

口径 B 允许说：

```text
selected-annulus 0.5-0.8 固定窗口下，
Tsuyama paper-audit lane 已完成 G0-G5 + Phase 2.5-2.11 一遍闭环；
当前选型已冻结，按现行参数出最终结果（详见 §14.12 / §14.14）。
```

```text
formula-consistent Ag/Au signal proxy 已通过 raw signal-ratio target；
strict Table S1 interferometric-column residual 保留为 diagnostic warning（target-mode 歧义）。
```

```text
当前选定的低自由度复现 lens 是单一全局 response compression（gamma = 0.749），
配合 D2.1 best 算子底座（tau_2ms_global_refphi_plus_collection_narrow），
formula-consistent Ag/Au loss ≈ 0.041、SNR-ratio loss ≈ 0.387；
total reproduction score = 2.033（descriptive partial reproduction 级别）。
```

```text
ET-2030 + LI5640 instrument-aware feasibility 显示：
current input / low-noise TIA 路径在 216/216 配置上具备 comfortable sensitivity margin；
50 Ω voltage path 在 211/216 配置上低于最小 sensitivity（5/216 仅 near minimum），
因此 voltage-path 不被推荐作为口径 B 的硬件接法。
```

```text
EV route shadow dashboard 显示 selected/all uplift median ≈ 1.384x，
max ≈ 1.557x，均未超 1.6x warning；
selected-annulus 与 all-crossing 并立，不互相替代。
```

```text
当前选型的几何主对照是 660 / 1200x550（raw Au peak-height exponent 3.0335）
与 660 / 800x550（3.0456）；其余几何作为 488/532 wavelength 对照保留。
```

口径 B 不能说：

```text
存在 accepted paper-calibrated candidate（仍是 negative_or_diagnostic_result_only）。
```

```text
Tsuyama paper 的 Table S1 / classification 数值已被 raw 参数自然复现。
```

```text
selected-annulus 0.5-0.8 边界可以移动以"贴近"论文。
```

```text
selected-annulus 排序可以替代 all-crossing 工程排序（与 §15.3 共同 forbidden 一致）。
```

```text
ET-2030 / LI5640 instrument feasibility 已校准 absolute SNR / LOD / 浓度。
```

```text
classification accuracy 已被本地复现（本地 sklearn 不可用，仍 no_accuracy_claim）。
```

```text
gamma response compression 是真实物理定律。
```

```text
当前 gamma / SNR scale / SNR response exponent 是仪器物理参数（它们是 reproduction lens 估计项）。
```

### 14.12 口径 B 最终收口（当前参数冻结为选型）

口径 B 已经完成它应该完成的工作：在不修改 selected-annulus 边界、不回写 EV full-grid、不开 per-diameter / per-geometry / per-case correction 的前提下，完整跑通 Tsuyama paper-audit lane 的 G0–G5 + 2.5–2.11 + instrument-aware feasibility + paper-statistics sensitivity。

**v4.0 起，口径 B 选型在以下参数集上冻结**，不再继续追更低 reproduction score；后续如需推进必须先有实测 artifact，否则按本节参数出结果即可。

冻结的口径 B 选型参数集：

```text
chosen_lens_id      = single_global_response_compression_with_d2p1_base_v1
chosen_candidate_id = tau_2ms_global_refphi_plus_collection_narrow   # D2.1 best
chosen_response_compression_gamma = 0.749
chosen_global_snr_scale           = 0.728
chosen_global_snr_response_exp    = 0.812
selected_annulus_window           = 0.5–0.8                          # 固定，不移动
lock_in_time_constant             = 1–2 ms
readout_observable                = pulse peak height (脉冲幅值)
phase_flip_hard_reject            = false
hardware_silicon_detector         = ET-2030 (responsivity / NEP / 0.4 mm active area)
hardware_lock_in                  = LI5640
hardware_connection               = current_input_with_low_noise_TIA  # 推荐
hardware_connection_blacklist     = 50_ohm_voltage_path                # 几乎全部 below sensitivity
au_diameter_panel                 = 20 / 30 / 40 / 60 nm
geometry_paper_audit_primary      = 660 / 1200x550, 660 / 800x550
geometry_paper_audit_secondary    = 488 / 800x550, 532 / 800x550, 488 / 1200x550, 532 / 1200x550
```

冻结后的 release status 与 score：

```text
release_status                          = negative_or_diagnostic_result_only
no_accepted_paper_calibrated_candidate  = true
chosen_lens_total_reproduction_score    = 2.033   # bounded partial 阈值 2.0
detection_status                        = partial_pass_with_Au20_low_warning
formula_consistent_signal               = pass
strict_table_s1_signal                  = unresolved (target-mode 歧义，diagnostic-only)
raw_au_size_response                    = unresolved (limiting pair 40-60 nm)
classification_accuracy                 = no_accuracy_claim (本地 sklearn 不可用)
selected_annulus_replaces_all_crossing  = false
selected_annulus_bound_change           = not_authorized
thermal_sidecar_used_to_increase_NODI   = false
```

冻结的判据是：再追更低 reproduction score 必须引入 per-diameter / per-geometry / per-case correction 或 detection logistic remap，越过 estimated-parameter 复现边界；当前参数已经把"在 reproduction lens 框架内能交付的 paper proxy alignment"全部做完。所以本报告不把"未达 score 2.0"读成"任务未完成"，而是读成"当前选型 = 当前参数集；进一步下降需要的不是计算自由度，而是实测 artifact"。

口径 B 共同必须保留的双语边界：

```text
全部 selected-annulus 结论都是 estimated-parameter / reproduction-lens 结论；
不构成对任何实物仪器、实物样品或绝对量级的校准；
selected-annulus 不替代 all-crossing 工程主排序，
all-crossing 不替代 selected-annulus paper-audit 结论。

All selected-annulus conclusions are estimated-parameter / reproduction-lens
results; they do not constitute calibration of any real instrument,
real sample, or absolute magnitude. The selected-annulus lens does not
replace the all-crossing engineering ranking, and vice versa.
```

口径 B 与口径 A 一起，构成本报告的双口径并立读者入口；任何后续阶段（P19+）的并入必须同时给出两个口径下的对应结论或显式 gap 标注（见 §15.5）。在 P19 evidence strategy gate 之前，**口径 B 输出 = 本节冻结参数 + §14.13 对照表 + §14.14 选型推荐**，不再做新一轮 reproduction-score 搜索。

### 14.13 口径 B 当前参数与 Tsuyama 各论文数据的详细对比

> 本节按 §14.12 冻结参数集（D2.1 best + gamma `0.749` + global SNR scale `0.728` + SNR response exponent `0.812` + selected-annulus `0.5-0.8` + 660/800x550 与 660/1200x550 主对照几何 + Au20/30/40/60 颗粒）输出当前 selected-annulus paper-audit 与 Tsuyama 6 篇论文的逐项对比。所有"当前选型值"列均使用上述冻结参数，不再做新拟合。
>
> 判定语义：
> - **match**：在当前 reproduction lens 内方向与量级一致；
> - **partial**：方向一致、量级仍有 bounded residual；
> - **boundary**：仅作为 boundary / safety / diagnostic 提示；
> - **out-of-scope**：论文机制不在当前 NODI 散射 lane 内；
> - **不复现**：明确不在本项目复现范围内（`no_accuracy_claim` 等）。

#### 14.13.1 vs Tsuyama 2019 POD（Nonfluorescent Molecule Detection in 10² nm Nanofluidic Channels）

| 论文项 | 论文值 / 结论 | 当前选型值 / 结论 | 判定 |
|---|---|---|---|
| 检测机制 | 光热衍射（POD），分子级 | NODI 散射干涉，颗粒级 | out-of-scope |
| 通道尺度 | `400×400 nm` 至 `200×200 nm` | 主对照 `800×550 / 1200×550 nm`；EV engineering 覆盖 500–900 nm 宽 | out-of-scope（机制不同，几何只能并列对照） |
| 衍射光区域作为读出区域 | 核心机制 | v2 用 BFP / slit / pinhole / readout region 显式约束 | match（方向） |
| 小通道 LOD 不显著恶化 | `400×400 nm: ~5.0 µM`、`200×200 nm: 按 detection volume 不恶化` | 当前禁止 absolute LOD claim | out-of-scope |
| 热扩散到玻璃基底 | 核心物理项 | v2 不做完整热效应 POD 源项；旁路只作 boundary | boundary |

#### 14.13.2 vs Tsuyama 2020 diffraction（Characterization of Optical Diffraction by Single Nanochannel）

| 论文项 | 论文值 / 结论 | 当前选型值 / 结论 | 判定 |
|---|---|---|---|
| Probe wavelength | `633 nm He-Ne` | 当前选型 paper-audit 主对照用 660 nm（最近对照点）| match（方向）|
| Illumination NA | `0.45`（20×物镜）| 当前对照不依赖具体物镜 | 不评估 |
| Collection NA | `0.9` | 当前 Phase 2 D2.1 best 用 `collection_narrow` 作为操作算子 | partial（方向一致；NA 数值非校准）|
| Lock-in modulation | `1.1 kHz` | 当前选型 NODI 读出 3 kHz；time constant 1–2 ms 对齐 | partial（频率不同；time constant 与论文同 order）|
| Time constant | `1 s`（论文连续测量）| 当前选型 1–2 ms（与 2022 NODI / 2020 counting POD 对齐）| partial（论文跨场景不同 time constant）|
| 参考场振幅 / 论文条件参考场 比值 | 1.000x（基准）| 660/800x550 = `1.000x`，660/800x1400 = `0.963x`，660/900x1200 = `0.976x` | match（最大绝对差异 ≈ 9.20%，平均 ≈ 2.13%）|
| 参考场是相位滤波结构 vs 背景常数 | 相位滤波结构 | v2 + 当前选型采用 paper-aligned phase filter 参考场 | match |

#### 14.13.3 vs Tsuyama 2020 counting POD（Detection and Characterization of Individual Nanoparticles in a Liquid by POD）

| 论文项 | 论文值 / 结论 | 当前选型值 / 结论 | 判定 |
|---|---|---|---|
| 检测机制 | POD 光热计数 | NODI 散射 / 干涉 | out-of-scope（机制不同，仅做趋势对照）|
| 通道几何 | `800 × 710 nm` | 主对照 `800x550 / 1200x550 nm`，金颗粒对照覆盖 `800x500/600, 1200x500/600` | partial（同一 800 nm 宽 family，深度不同）|
| 颗粒 | `20 nm Au` | 当前选型颗粒 panel = Au 20 / 30 / 40 / 60 nm | match（覆盖 paper 颗粒 + Table S1 集合）|
| Au20 检出 | POD `near-100%` | 当前 NODI 选型：Au20 detection `partial_pass_with_Au20_low_warning`（6 个 joint cases 中 3 个进入 operational band，全部偏低）| boundary（与论文 Au20 weak-SNR 描述相容；NODI 散射不能外推 POD 100% 检出）|
| 锁相时间常数 | `2 ms` | 当前选型 1–2 ms | match |
| 流速 | `0.17 mm/s` | 当前选型流速近 0.2 mm/s（与 2022 NODI 同 order）| partial |
| 660 nm，800 nm 宽，500 nm 深，Au20 通过 | `pass`（POD 光热）| `fail`（NODI 散射，合成检出 0.000）| out-of-scope（不可外推 POD → NODI）|
| 660 nm，800 nm 宽，500 nm 深，Au40 通过 | — | `pass`（NODI 散射，合成检出 0.266）| match（粒径变大、信号增强趋势同向）|
| 660 nm，800 nm 宽，500 nm 深，Au60 通过 | — | `pass`（NODI 散射，合成检出 0.315）| match |

#### 14.13.4 vs Tsuyama 2020 solvent-enhanced POD（Concentration Determination at a Countable Molecular Level）

| 论文项 | 论文值 / 结论 | 当前选型值 / 结论 | 判定 |
|---|---|---|---|
| Probe / excitation | `633 nm` probe + `532 nm` excitation | 当前 NODI 选型只在 660 nm 主对照 + 488/532 wavelength 对照；不做 thermo-optic excitation | out-of-scope |
| Solvent thermo-optic `dn/dT` | 核心变量 | 不在当前 NODI 模型物理项中 | out-of-scope |
| Solvent enhancement | `>30x` | 不评估 | out-of-scope |
| LOD | `75 nM` 等价约 `10 / 0.23 fL` | 当前禁止 absolute LOD claim | out-of-scope |
| Sign flip when solvent RI changes | POD thermal/diffraction coupling 特征 | 当前 NODI 不把 sign flip 当作 sign-preservation 替代指标 | boundary |

#### 14.13.5 vs Tsuyama 2022 NODI（Nanofluidic Optical Diffraction Interferometry for Detection and Classification）

> 这是口径 B 的中心对照论文。下表把 §14 冻结参数集与论文 Table S1 / 主要数值结论逐项对齐。

| 论文项 | 论文值 / 结论 | 当前选型值 / 结论 | 判定 |
|---|---|---|---|
| Probe wavelength | `660 nm` | 当前选型主对照 `660 nm` | match |
| 通道几何 | `≈ 800 × 550 nm` | 当前选型 paper-audit 主对照 `660/800x550` 与 `660/1200x550` | match |
| Collection NA | `0.9` | D2.1 best 用 `collection_narrow` 算子；不做 absolute NA 校准 | partial（方向一致）|
| Slit | `1 mm` | 当前 BFP / slit / pinhole 几何位于约束中；不复现绝对尺寸 | partial |
| Pinhole | `400 µm` | 同上 | partial |
| Time constant | `1–2 ms` | 当前选型 `1–2 ms` | match |
| Pressure / flow velocity | `100 kPa / 0.2 mm/s` | 当前选型流速近 0.2 mm/s | match |
| Table S1 Ag40/Au40 signal ratio（formula-consistent `sqrt_scattering_column_ratio` 模式）| paper 数值 | 当前选型：formula-consistent Ag/Au loss ≈ `0.041`（pass）| match |
| Table S1 Ag40/Au40 signal ratio（strict `interferometric_column_ratio` 模式）| paper strict 数值 | 当前选型：strict residual unresolved（target-mode 歧义；保留为 diagnostic warning）| out-of-scope（target ambiguity，不入 hard target）|
| Au size exponent | `2.3` | 当前选型 raw peak-height exponent：`660/1200x550 = 3.0335`、`660/800x550 = 3.0456`、`532/800x550 = 3.1563`；gamma `0.749` 之后映射到 `2.3`（lens 定义结果）| partial（reproduction lens 内对齐；raw 自然复现仍偏陡，limiting pair `40-60` nm）|
| Au30 / Au20 SNR ratio | `33 / 12 ≈ 2.75` | 当前选型 raw `3.36`；gamma compression 后 ≈ `2.43`；SNR-ratio loss ≈ `0.387` | partial |
| Au20 detection | weak-SNR / not-all-detected | 当前选型 `partial_pass_with_Au20_low_warning`（Au20 only-low miss）| match |
| Au30 detection | minor / borderline | 当前选型 Au30 minor warning（5/6 joint cases pass）| match |
| Au40 detection | full | 当前选型 6/6 pass | match |
| Au60 detection | full | 当前选型 6/6 pass | match |
| Classification accuracy | `71.9 ± 4.0%`（SVM）| 本地 sklearn 不可用：`no_accuracy_claim`；feature export 完整、`200` rows、min class count `24` | 不复现 |
| 信号方向：660 强于 488/532 | 是 | 当前选型 488/532/660 对照中 660 通过比例 `0.45`，488/532 均 `0.00`；mean pulse peak 660 = `0.15641`、532 = `0.07730`、488 = `0.05245` | match |

#### 14.13.6 vs Tsuyama 2024 POD+NODI（Nanofluidic detection platform for simultaneous light absorption and scattering measurement）

| 论文项 | 论文值 / 结论 | 当前选型值 / 结论 | 判定 |
|---|---|---|---|
| Probe wavelength | `660 nm` | 当前选型主对照 `660 nm` | match |
| Excitation wavelength（POD 侧）| `532 nm` | 不进入 NODI 选型；仅作 boundary 对照 | boundary |
| Time constant | `1–2 ms` | `1–2 ms` | match |
| Frequency split | `1.2 / 4.1 kHz` | 当前 NODI 单通道读出 3 kHz；不复现双频 split | partial |
| 通道几何 | width `800–1200 nm`、depth `~550 nm` | 当前选型 paper-audit 主对照覆盖 `660/800x550` 与 `660/1200x550` | match |
| Paired POD + NODI pulse observables | 核心读出语义 | 当前选型只输出 NODI 侧 pulse peak height + amplitude / in-phase 对照；不复现完整双频电子链路 | partial |
| 同相读出 vs 幅值读出（660 nm 通过比例）| paper 用 paired pulses | 当前选型：基线（in-phase + phase-gated）通过 `0.00`、in-phase no-gate `0.45`、amplitude `0.45`；mean detection 几乎不变 | match（方向）|
| 分类协议 | paired POD + NODI 分类器 | 不复现完整分类器协议 | 不复现 |

### 14.14 口径 B 选型推荐

> 本节是 P19 evidence strategy gate 之前 **口径 B 的最终选型**。任何 P19 plan 必须以此为口径 B 的 baseline，不允许在没有 measured artifact 的前提下把这组参数视为"过渡候选"再做新一轮搜索。

#### 14.14.1 推荐计算侧选型（reproduction lens）

```text
chosen_lens_id      = single_global_response_compression_with_d2p1_base_v1
chosen_candidate_id = tau_2ms_global_refphi_plus_collection_narrow

# global reproduction-lens 估计项（不解读为物理常数）
global_response_compression_gamma = 0.749
global_snr_scale                  = 0.728
global_snr_response_exponent      = 0.812

# 算子 / 几何 / 颗粒
selected_annulus_window           = 0.5 – 0.8                      # 固定，不移动
geometry_primary                  = 660 / 1200x550, 660 / 800x550
geometry_secondary_for_wavelength = 488 / 800x550, 532 / 800x550,
                                    488 / 1200x550, 532 / 1200x550
au_diameter_panel                 = 20 / 30 / 40 / 60 nm

# 读出 / 数据采集
lock_in_time_constant             = 1 – 2 ms
readout_observable                = pulse peak height (脉冲幅值)
phase_flip_hard_reject            = false
events_per_case                   = D2.1 局部 smoke 用 2000；
                                    paper-audit confirm 用 3000–10000
```

附核心 score 与 alignment：

```text
total_reproduction_score          = 2.033       # bounded partial 阈值 2.0；冻结，不再追低
formula_consistent_Ag_Au_loss     ≈ 0.041
SNR_ratio_loss                    ≈ 0.387
SNR_anchor_loss                   ≈ 0.0146
detection_loss                    ≈ 0.65
complexity_penalty                ≈ 0.818

raw_Au_peak_height_exponent_660_1200x550 = 3.0335
raw_Au_peak_height_exponent_660_800x550  = 3.0456
raw_Au_peak_height_exponent_532_800x550  = 3.1563
limiting_size_pair                       = 40 – 60 nm
```

#### 14.14.2 推荐硬件接法（instrument-aware feasibility）

```text
silicon_detector       = ET-2030 (estimated responsivity / NEP / 0.4 mm active area)
lock_in_amplifier      = LI5640
recommended_connection = current_input_with_low_noise_TIA
                         (216 / 216 配置 comfortable margin)
blacklisted_connection = 50_ohm_voltage_path
                         (211 / 216 below sensitivity, 5 / 216 near minimum)
```

#### 14.14.3 推荐对照颗粒与几何（paper-audit lane）

| 用途 | 颗粒 | 几何 | 备注 |
|---|---|---|---|
| 主对照 | Au40 / Ag40 | `660 / 800x550`、`660 / 1200x550` | Table S1 中心；raw Au exponent 最优组合 |
| Au size exponent 对照 | Au20 / Au30 / Au40 / Au60 | 同上 | Au20 保留 low-sensitivity warning，不视为 release blocker |
| Wavelength 对照 | Au40 / Ag40 | `488 / 800x550`、`488 / 1200x550`、`532 / 800x550`、`532 / 1200x550` | 用于 660 > 532 > 488 趋势复核 |
| Boundary control（双口径共用）| EV-like | `660 / 700x1500` | weak-reference / NA boundary |
| Short-wave engineering（双口径共用）| EV-like | `404 / 600x1300`、`404 / 800x700` | sanity，不是 Tsuyama direct target |

#### 14.14.4 推荐报告口径与禁止条目

允许直接发布的口径：

```text
release_status          = negative_or_diagnostic_result_only
chosen_lens             = single_global_response_compression_with_d2p1_base_v1
chosen_lens_score       = 2.033 (descriptive partial reproduction)
formula_consistent_pass = true
detection_status        = partial_pass_with_Au20_low_warning
hardware_recommendation = current_input_with_low_noise_TIA
```

禁止从本选型推导出的结论（与 §14.11 / §15.3 一致）：

```text
accepted_paper_calibrated_candidate
absolute_SNR / LOD / 浓度
biological specificity
classification accuracy 已本地复现
gamma / SNR scale / SNR exponent 是仪器物理常数
selected_annulus 边界可移动
selected_annulus 替代 all-crossing 工程排序
```

#### 14.14.5 推荐下一步（在 P19 evidence strategy gate 之前）

1. **不再做新一轮 reproduction-score 搜索**：当前参数集已是 single global response compression lens 的最佳低自由度解；继续下降需要 per-diameter / per-geometry / per-case correction，越过本项目允许的复现边界。
2. **以本节冻结参数为口径 B baseline**：任何 P19 plan 必须把这组参数 + §14.13 的 6 张对比表当作 baseline，不能把它们视为"过渡候选"。
3. **第一轮硬件验证优先核 current input / TIA 接法**：不要再在 50 Ω voltage path 上调相位或调 annulus；voltage path 已被量级估计排除。
4. **实测 artifact 优先级**：measured Au raw trace、blank、BFP / slit / ROI 扫描、lock-in / logger、PEG / fluidic 流体可行性数据，是把口径 B 从 `negative_or_diagnostic_result_only` 推进到 paper-calibrated candidate 的硬依赖。
5. **classification accuracy** 要本地复现需在另一台具备 sklearn 的环境跑 svm；本报告仍 `no_accuracy_claim`。

---

## 15. 双口径综合分析与共同收口

> 本节是双口径综合：把口径 A（§1–§13）与口径 B（§14）的结论摆在一起做对照，给出共同 forbidden claim、共同收口和后续阶段并入要求。它不修改任何口径内的结论，只做共同语义层。

### 15.1 双口径并立治理原则

| 维度 | 口径 A：all-crossing | 口径 B：selected-annulus paper-audit | 双口径关系 |
|---|---|---|---|
| 适用问题 | EV/NODI 工程整体路线排序与治理 | Tsuyama paper-audit proxy 数值能否被估计参数自然复现 | 互补，不是主辅 |
| 主排序口径 | 全局 BFP 全 crossing | selected-annulus `0.5-0.8` 固定窗口 | 互不替代（双向 forbidden） |
| 主结论形式 | route role + main-660 conditional_relative_main 集合 | candidate release status（negative_or_diagnostic_result_only） | 不能交叉解读（口径 A 的 route role 不能解释成口径 B 的 paper candidate；反之亦然） |
| Tsuyama 关系 | 趋势对齐 + 固定条件对照 + 金颗粒读出口径对照 | paper-audit proxy + estimated-parameter reproduction lens | 共享文献来源（archive/tsuyama/*），结论形式不同 |
| 结论边界 | 无实测 / 合成相对先验 / trace-only | 无实测 / estimated-parameter / reproduction-lens | 共享：calibrated_claim_allowed = false |
| 后续依赖 | P19 evidence strategy gate | measured Au raw trace、blank、BFP/slit/ROI、lock-in/logger（详见 §14.6.1 实验排序） | P19 evidence strategy 必须同时给出两口径下的 acceptance criteria |

### 15.2 同一证据在两个口径下的差异对照

| 证据 / 主题 | 口径 A 下的结论 | 口径 B 下的结论 |
|---|---|---|
| main-660 路线 | `660 / 800x1400` 与 `660 / 800x1500` 双 conditional_relative_main；P6–P16 trace-only 首位在二者间反复切换 | `660 / 800x1400` 与 `660 / 800x1500` 是 reference-useful long-wave candidate；不是 paper geometry 复现，paper geometry 主对照是 `660 / 800x550` 与 `660 / 1200x550` |
| 弱参考场 control（`660 / 700x1500`） | `relative_control_candidate` → `weak_reference_control_only`（P0 audit 裁决）；R5.2 中在 8/8 R5 scenario bundles 高于 main-660 | weak-reference / NA boundary control |
| 660 nm 高分 context（`660 / 500x1300-1500`、`600x1500` 等） | 在 R5.2 bounded scenario-prior audit 中 ratio_vs_main 高达 `1.31-1.56x`，但 `context_route_promotion_authorized = false`，归类 `surrogate_sensitive_not_promoted` | selected-annulus uplift median `1.384x` 与 context 均值高度耦合，但同样 `selected_annulus_replaces_all_crossing_ranking = false` |
| 404 nm probe（`404 / 600x1300`） | `probe_only` → `shortwave_probe_only`（P0 audit）；P6–P16 trace 中始终排第 3 | short-wave engineering sanity，不是 Tsuyama direct target |
| optional `660 / 900x1400` | `optional_robustness_probe_only`，不得 redefine main-660 | selected-annulus 口径下未独立扩展 |
| 4 条 paper-sanity routes | P0 audit 标 `paper_sanity_only` | 与 Phase 2 paper-audit candidate 不同：paper-sanity 是工程口径下的诊断，paper-audit 是 selected-annulus 口径下的 candidate |
| width-prior 解释（W/800）^1.5 / ^2.0 | 可接受解释；主路线保留比例 1.000、context 越线 0、weak-reference 越线 0 | width-prior 是 R5.2 sidecar 提供的解释模型；不影响 Phase 2 paper-audit candidate score |
| 404 nm 热效应 | 旁路提示，不给 NODI 光学分数加分 | `thermal_sidecar_used_to_increase_NODI_score = false` 在 R5.2 sidecar guardrail 中显式记 |
| Au 颗粒散射对照（20–60 nm） | 660 > 532 > 488，660 nm 通过比例 0.45（其他 0.00），平均脉冲峰值 660 = `0.15641` | Phase 2 raw Au size exponent best 约 `3.05–3.19`（target `2.3`，limiting pair `40-60`） |
| Tsuyama 2022 NODI 论文几何 `800x550` | 工程口径下是 cross-check 观察，不替代 main-660 路线治理 | paper geometry 主对照之一，是 Phase 2 paper-audit candidate 的几何子集 |
| classification accuracy `71.9 ± 4.0%` | 引用为 Tsuyama 文献 anchor，不复现 | diagnostic_only target；本地 sklearn 不可用，`no_accuracy_claim` |

### 15.3 双口径共同 forbidden claim

下列禁止条目对两个口径同等适用（unified forbidden claim）：

```text
calibrated SNR
calibrated event probability
absolute LOD
true EV concentration
biological specificity
measured blank safety
detector voltage / sample-count prediction
route promotion（针对 EV engineering）或 accepted paper-calibrated candidate（针对 Tsuyama paper-audit）
main-660 redefinition
selected-annulus 边界变更
selected-annulus 替代 all-crossing 工程排序
all-crossing 替代 selected-annulus paper-audit 结论
404 nm 热效应旁路加分
P6-P16 trace 排名当作路线升级或单一冠军结论
estimated-parameter reproduction lens 当作 raw physical calibration
classification accuracy 已本地复现
gamma response compression 当作真实物理定律
```

### 15.4 双口径共同收口

两个口径都已经完成各自范围内的工作：

```text
口径 A（all-crossing）已收口：
  v2 + post-v2 P0-P18 在合成相对先验 / relative-audit / trace-only 范围内完成；
  main-660 仍是 conditional_relative_main 集合 {800x1400, 800x1500}；
  P18 已停止机械式 lane roll-forward；
  下一步必须先做 P19 evidence strategy gate。

口径 B（selected-annulus）已冻结选型：
  Phase 2 + Phase 2.5-2.11 + instrument-aware feasibility + paper-statistics sensitivity
  在 estimated-parameter / reproduction-lens 范围内完成；
  release_status = negative_or_diagnostic_result_only；
  当前参数集冻结为口径 B 选型（详见 §14.12 / §14.14）：
    candidate_id = tau_2ms_global_refphi_plus_collection_narrow (D2.1 best)
    gamma = 0.749, snr_scale = 0.728, snr_response_exp = 0.812
    selected_annulus = 0.5-0.8 (固定)
    geometry = 660/800x550, 660/1200x550 (主对照)
    hardware = ET-2030 + LI5640, current_input/TIA (216/216 comfortable)
  下一步是按本选型出最终结果（详细对比表见 §14.13）；
  不再做新一轮 reproduction-score 搜索；
  P19 evidence strategy 之前不重启 broad raw-parameter sweep。
```

共同收口边界（双语）：

```text
两个口径都不构成对任何实物仪器、实物样品或绝对量级的校准；
两个口径相互并立，不互相替代；
共同后续依赖是 P19 evidence strategy gate + 实测 artifact 集合。

Both lenses are no-measured-data conclusions and do not constitute calibration of
any real instrument, real sample, or absolute magnitude. The two lenses sit in
parallel and do not replace each other. The shared next dependency is the P19
evidence-strategy gate plus the measured-artifact set.
```

### 15.5 后续工作的双口径反映要求（going forward）

任何后续 realism v2 / post-v2 P19+ 阶段证据并入本文（report 88）时，必须遵守：

1. **同时评估两个口径**：写入两个口径下的对应结论；不允许只写一边。
2. **显式标注 gap**：某口径下若没有等价证据，必须显式写入 "selected-annulus 口径下未扩展" 或 "all-crossing 口径下未扩展"。本节 §14.9 与 §14.10 的表是当前 gap 标注格式的范例。
3. **双口径不互相替代**：新的证据若改变了 §15.3 共同 forbidden claim 中的任意一条，必须先在 §15.3 显式更新；不允许通过新阶段表述间接推翻共同 forbidden。
4. **P19 evidence strategy gate** 必须为两个口径都给出 acceptance criteria。口径 A 至少含 `measured_blank_bfp` / standard particle transfer / slit-ROI scan / full-wave spot-check；口径 B 至少含 measured Au raw trace、blank、BFP/slit/ROI、lock-in/logger。
5. **更新本节**：每次 P19+ 并入时，§15.2 对照表与 §15.4 收口段必须同步更新，确保两个口径在最新证据下仍可比较。
6. **Provenance 保留**：[reports/49](49_Tsuyama_Phase2_paper_calibrated_selected_annulus_analysis.md) 与 [reports/71](71_EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit_analysis.md) 仍是 selected-annulus 口径的 raw provenance；本文 §14 是它们的读者级合并，但不允许在不更新 §14 的情况下仅更新 49/71 就声称 88 已同步。

### 15.6 当前未决事项（双口径）

1. P19 evidence strategy gate 必须先定义两个口径下的 acceptance criteria 与停止准则，再继续任何 lane / family ladder。
2. 实测 Au raw trace / blank / BFP / slit / ROI / lock-in / logger / 流体可行性数据，是两个口径共同的下一步硬依赖。
3. EV polydispersity、non-sphericity、coincidence/blended pulses、roughness/fabrication background、PEG fouling 与 drift 仍属于 post-v2 validation program；既不应回写成口径 A 内 calibration，也不应回写成口径 B 内 paper-audit accepted candidate。
4. 共同 forbidden claim（§15.3）在没有新实测证据前不得放宽。
5. 口径 B 在 v4.0 已把当前参数集冻结为选型（§14.12 / §14.14）；任何 P19 plan 必须以此为口径 B baseline，不允许把这组冻结参数视为"过渡候选"再做新一轮搜索。
