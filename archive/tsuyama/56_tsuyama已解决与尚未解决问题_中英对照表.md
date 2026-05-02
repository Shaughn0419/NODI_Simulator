# Tsuyama 已解决与尚未解决问题（中英对照表）

<!-- DOCSYNC:START -->
> 归档提示（2026-04-28）：本文保留历史快照，不覆盖现行代码事实。当前主线已更新到 EV/NODI relative design gate 拆分、detector caution 分层、calibrated BFP ROI mask 到 Tsuyama 1D projected ROI、完整 governance diagnostics 导出；验证基线为 `pytest -q` = `509 passed`，`ruff check .` / `pyright` 通过。现行结论以根目录 `README.md`、`文档导航.md`、`00/24/42/43` 和代码测试为准。
<!-- DOCSYNC:END -->

> 目的 / Purpose：基于 Tsuyama / Mawatari 6 篇论文原文内容，并辅以专业 interferometric-scattering 文献复核，严格区分：
>
> 1. Tsuyama 已经被论文直接回答的问题 / problems already answered in the Tsuyama papers
> 2. Tsuyama 尚未被系统回答的问题 / problems not yet systematically answered in the Tsuyama papers
> 3. 这个空白是否足以支持一篇新论文 / whether the gap is sufficient for a new paper

---

## 1. 核心研究问题 / Core Research Question

中文：

在固定光学与读出条件下，什么样的纳米通道几何参数 `宽度 W × 深度 H` 能使 NODI 的事件级脉冲信号最优，并在 `pulse height`、`pulse width`、`SNR`、`count rate`、`classification separability` 等指标上取得最佳综合表现？

English:

Under fixed optical and readout conditions, what nanochannel geometry `width W × depth H` maximizes event-level pulse detectability in NODI, as quantified by `pulse height`, `pulse width`, `SNR`, `count rate`, and `classification separability`?

这个问题与 Tsuyama 已回答问题的区别 / Why this is different from what Tsuyama already answered：

- Tsuyama 多篇论文已经回答了“空白通道如何产生参考衍射场”“diffracted-light region 中为什么会有干涉增强”“某些固定条件下什么 detection frequency 更优”“某些条件下 diffracted light intensity 对 width 有最优值”等问题。
- 但这些并不自动等价于：

$$
(W,H) \to \text{pulse height / width / SNR / counts / classification}
$$

这一整条 `geometry-to-pulse` 设计规律。

---

## 2. Tsuyama 已解决的问题 / Problems Already Solved by Tsuyama

| 分类 Category | 已解决的问题 Solved Question | 证据与事实 Basis in the Papers | 代表论文 Supporting Papers | 学术判断 Academic Interpretation |
|---|---|---|---|---|
| 空白通道衍射 Blank-channel diffraction | 证明了单纳米通道可作为相位滤波器并产生可预测的衍射场 / Demonstrated that a single nanochannel can act as a phase filter and generate a predictable diffraction field | `2020 diffraction` 从 Fresnel–Kirchhoff/phase-filter 角度建立理论，并与实验在测量范围内吻合 | `2020 diffraction` | 这一层回答了 `channel phase delay -> diffraction field` 的基本物理问题 |
| 通道宽度与衍射强度 Width vs diffracted intensity | 在固定 optics 与检测区域条件下，normalized diffracted light intensity 对 width 存在最优值 / Under fixed optical and detection conditions, normalized diffracted-light intensity has an optimum with channel width | 文中明确写到：在其条件下 optimum channel width 约为 `500 nm`，同时也明确说 optimum 依赖 wavelength 与 detection region | `2020 diffraction` | 这回答的是 `width -> diffraction-intensity proxy` 的局部最优，而不是 pulse signal 的全局最优 |
| 通道深度与衍射强度 Depth vs diffracted intensity | 说明了 depth 会影响 diffracted light intensity / Showed how channel depth affects diffracted-light intensity | 测量范围内，文中报告 diffracted light intensity 随 channel depth 变化，并认为其 phase-filter approximation 在该范围有效 | `2020 diffraction` | 这回答了 depth 对参考场 proxy 的影响，但仍未进入 event-level pulse 指标 |
| 小尺寸通道可工作 Small channels remain workable | 证明了 `10^2 nm` 量级通道可以实现 POD 检测 / Demonstrated that `10^2 nm`-scale channels are experimentally workable for POD detection | `2019 POD` 中 `200 nm` 通道没有明显 LOD 劣化，并明确说 POD 已适用于 `10^2 nm` 级通道 | `2019 POD` | 这回答的是“能否工作”，不是“是否最优” |
| 干涉 pulse 的来源 Origin of interferometric pulses | 证明了 NODI 脉冲来自 diffracted-light region 中的 interferometric scattering，而不是纯散射背景 / Verified that NODI pulses arise from interferometric scattering in the diffracted-light region rather than from pure scattering alone | `2022 NODI` 比较了 diffracted-light region、其外部区域和宽微通道，只有 diffracted-light region 中 pulse 明显增强 | `2022 NODI` | 这一步把 `reference field + particle scattering -> pulse generation` 机制闭环了 |
| pulse 与 diffracted light intensity 的关系 Pulse vs diffracted intensity | 证明了 average pulse height 会随 diffracted light intensity 增强 / Showed that average pulse height increases with diffracted-light intensity | `2022 NODI` 中 slit 扫描显示在 diffracted-light region 中 pulse counts 高、average pulse height 增强 | `2022 NODI` | 这是非常关键的机制验证，但仍然不是系统的几何优化图谱 |
| 最优读出频率 Optimum detection frequency | 识别了固定体系下 detection frequency 的经验最优窗口 / Identified an empirical optimum detection-frequency window under fixed conditions | 文中明确给出 optimum detection frequency around `1–6 kHz`，并说明 flow rate、optics、external noise 都会影响它 | `2022 NODI` | 这是 `readout-optimal`，不是 `geometry-optimal` |
| 单颗粒 size trend Single-particle size trend | 验证了 pulse signal 与粒径之间存在可用的经验尺度关系 / Verified a usable empirical size-signal relation for pulse observables | `2022 NODI` 给出 measured average signal 随粒径的经验幂次关系，并据此开展 size measurement | `2022 NODI` | 这说明 event-level pulse 可用于表征，但没有把 channel geometry 作为系统变量展开 |
| 单通道分类 Single-channel classification | 证明了 pulse features 可用于单通道 nanoparticle classification / Demonstrated pulse-feature-based single-channel nanoparticle classification | `2022 NODI` 用 pulse heights 与 widths 做 SVM 分类 | `2022 NODI` | 说明 pulse observables 是有判别力的输出变量 |
| 双通道联合分类 Dual-channel classification | 证明了 POD + NODI 双通道 pulse features 可以提升 classification / Demonstrated that dual-channel POD + NODI pulse features improve classification | `2024 POD+NODI` 用两条通道的 height/width 做联合分类，并比较单通道与双通道结果 | `2024 POD+NODI` | 说明事件级 pulse 特征是论文最终关心的实验输出 |

---

## 3. Tsuyama 尚未系统解决的问题 / Problems Not Yet Systematically Solved by Tsuyama

| 分类 Category | 尚未解决的问题 Unresolved Question | 为什么说尚未解决 Why It Is Still Unresolved | 论文证据 Evidence in the Papers | 学术判断 Academic Interpretation |
|---|---|---|---|---|
| 宽深到 pulse 的设计定律 Geometry-to-pulse law | 尚未建立 `W × H -> pulse height / pulse width / SNR / count rate / classification` 的系统设计图 / No systematic `W × H -> pulse metrics` design map has been established | 现有论文没有做系统的 width-depth pulse matrix，而是分别研究 diffraction、frequency、classification 等局部问题 | 全部 6 篇合看 | 这是最核心的未解问题 |
| diffraction-optimal vs pulse-optimal | 尚未证明“让 diffracted light intensity 最强的几何”就等于“让单颗粒 pulse signal 最优的几何” / It has not been shown that the geometry maximizing diffracted-light intensity also maximizes event-level pulse signal | `2020 diffraction` 给的是 diffraction-intensity optimum；`2022 NODI` 关心 pulse，但未系统扫宽深将二者直接对应起来 | `2020 diffraction`, `2022 NODI` | 这是一个真正新的研究问题，而不是旧结果的直接延伸 |
| width/depth 对 event metrics 的联合影响 Joint effect of width and depth on event metrics | 尚未系统量化 width/depth 对 pulse height、pulse width、SNR、counts 的联合影响 / Joint effects of width/depth on event metrics have not been systematically quantified | `2022` 与 `2024` 通道几何基本固定；`2019`/`2020` 中的宽深扫描主要是 diffraction/POD 可行性，不是 NODI event pulse map | `2019 POD`, `2020 diffraction`, `2022 NODI`, `2024 POD+NODI` | 目前缺的是一张 geometry-to-event observables 图谱 |
| 通道尺寸极限 Size limit | 尺寸极限没有被封闭 / The ultimate channel-size limit was not closed | `2019 POD` 明确写出 “the size limit of the nanochannel is under investigation” | `2019 POD` | 作者自己承认边界问题未解决 |
| 多因素联合优化 Multi-factor co-optimization | 没有把 `W, H, λ, beam size, detection region, NA, flow rate, lock-in frequency` 联合成统一优化问题 / No unified co-optimization over `W, H, λ, beam size, detection region, NA, flow rate, lock-in frequency` | 论文中这些变量是分散讨论的：width/depth 在 diffraction 文中，frequency 在 NODI 文中，classification 在 2022/2024 文中 | 全部 6 篇合看 | 目前是“局部最优集合”，不是“统一设计定律” |
| pulse 稳定性与几何的关系 Geometry vs pulse robustness | 尚未系统回答不同几何对 pulse fluctuation、CV、漏检、误检的影响 / No systematic answer has been given for how geometry affects pulse fluctuation, CV, missed detections, or false detections | `2022 NODI` 承认 measured size dependence and CV relative to prediction are still under investigation；分类文也主要固定通道几何 | `2022 NODI`, `2024 POD+NODI` | 这意味着“可检测”与“稳健可检测”仍然有空白 |
| 几何对分类可分性的直接作用 Geometry vs classification separability | 尚未系统回答 geometry 如何影响 feature-space separability / No systematic answer has been given for how geometry controls classification separability in feature space | `2022` 和 `2024` 直接做了分类，但没有把 geometry 当成主自变量进行 feature-space mapping | `2022 NODI`, `2024 POD+NODI` | 这是一个非常适合新论文的方向 |

---

## 4. 最严格的事实修正版结论 / Strictly Factual Revised Conclusion

下面这几句，是在复核后最稳妥、最符合事实的表达：

| 结论类型 Conclusion Type | 更严格的表述 More Rigorous Formulation |
|---|---|
| 不能说的过头话 What should NOT be overstated | 不能直接说 “Tsuyama 没回答什么通道尺寸更好”。因为他确实回答了：在固定条件下，什么 width 会让 diffracted light intensity 更强。 |
| 可以说的话 What CAN be said | 可以说：Tsuyama 尚未系统回答 “什么样的通道宽度和深度能够使单颗粒 pulse signal 综合最优”。 |
| 更学术的表达 A more academic wording | Tsuyama has identified local optima for diffraction intensity and detection frequency under fixed conditions, but has not yet established a general channel-geometry-to-pulse design law for event-level detectability. |

---

## 5. 外部专业文献复核 / Cross-Check with Professional Literature

之所以说上面的“尚未解决问题”在学术上是合理的，不只是因为 Tsuyama 自己没系统做，还因为 interferometric-scattering 领域本身就强调：检测优化不能只看一个 proxy，而要同时看 `reference field`、`phase`、`contrast`、`background noise`、`focus`、`false positives/negatives` 等因素。

| 外部文献 External Literature | 核心观点 Key Takeaway | 对本问题的意义 Relevance to This Question |
|---|---|---|
| `Interferometric Scattering Microscopy: Seeing Single Nanoparticles and Molecules via Rayleigh Scattering` (Nano Lett., 2019) | 干涉散射检测的本质是 reference field 与 scattering field 的叠加，信号受振幅与相位共同控制 | 支持“不能只看某个 channel geometry 下的 diffraction intensity proxy，就断言 pulse 最优” |
| `Robust Visualization and Discrimination of Nanoparticles by Interferometric Imaging` (IEEE JSTQE, 2017 / PMC 2017) | 稳健检测和判别需要同时处理对比度、离焦、对准、误检与漏检 | 支持“geometry-optimal” 应该定义在 event-level detectability 上，而不只是光强最大值上 |
| `Leveraging Partial Coherence to Enhance Nanoparticle Detection Sensitivity and Throughput in Interferometric Scattering Microscopy` (ACS, 2025) | interferometric sensitivity 取决于 signal contrast、background noise 与 focus dependence 的共同作用 | 支持“更好的 pulse signal”本质上是一个多因素 detectability 优化问题 |

外部文献的作用 / Role of the external literature：

- 它们**不是**用来证明 Tsuyama 说错了
- 它们是用来证明：把问题从 “diffraction-optimal” 推进到 “pulse/detectability-optimal” 在学术上是自然且合理的

---

## 6. 这是否足够支撑一篇新的论文 / Is This Gap Large Enough for a New Paper?

### 6.1 简短结论 / Short Answer

是，**有希望足够支撑一篇新的论文**，但前提是选题要写成：

$$
\text{from diffraction-optimal geometry}
\to
\text{to pulse-optimal geometry}.
$$

而不是仅仅写成“再做一次 width scan”。

### 6.2 更学术的论文命题 / More Academic Paper Framing

可写成：

“Tsuyama and co-workers established the formation of the blank-channel diffraction reference field and validated nanoparticle pulse generation in the diffracted-light region. However, the channel geometry that optimizes diffraction intensity has not been systematically linked to the geometry that maximizes event-level pulse detectability. Here, we establish a channel-geometry-to-pulse design law for nanofluidic optical diffraction interferometry.”

中文对应：

“Tsuyama 团队已经建立了空白通道参考衍射场形成与单颗粒干涉脉冲生成的基本物理图景，但尚未系统建立‘衍射最优几何’与‘脉冲可检测性最优几何’之间的联系。本文尝试建立纳流体光学衍射干涉体系的 `通道几何 -> 事件级脉冲性能` 设计规律。”

### 6.3 什么时候不够一篇论文 / When It Would NOT Be Enough

如果你只是做：

- 几个不同宽度/深度的通道
- 比较一下平均 signal
- 选一个最大的

那更像补充实验，不一定足以形成独立论文。

### 6.4 什么时候有机会够一篇论文 / When It Could Be Enough

如果你做的是：

- 系统的 `W × H` 通道矩阵
- 固定 optics、flow、readout、sample
- 同时比较 `pulse height / width / SNR / count rate / CV / classification accuracy`
- 区分 `diffraction-optimal` 和 `pulse-optimal`
- 给出可复用的 design law 或 design map

那就更像一篇真正的新论文。

---

## 7. 我们的工程主线 + 不同宽深通道实验，能否回答这个问题 / Can Our Current Engineering Pipeline Plus Width-Depth Experiments Answer This Question?

| 方面 Aspect | 判断 Assessment | 说明 Explanation |
|---|---|---|
| 工程是否足以做问题定义 Is the current engineering pipeline sufficient for problem formulation? | 是 / Yes | 我们当前主线已经把 `reference field -> scattering -> interference -> readout -> pulse detection` 串起来了，足以表达 `geometry -> pulse` 的问题 |
| 工程是否足以单独给出最终答案 Is the pipeline alone sufficient for a definitive answer? | 否 / No | 当前工程仍是 reduced / surrogate-rich mainline，不适合单独宣称“第一性原理下的绝对最优尺寸” |
| 工程最适合扮演什么角色 What is the best role of the pipeline? | 机制解释 + 候选通道筛选 / mechanism interpretation + candidate-channel screening | 它非常适合作为 physics-informed reduced model，用于预测哪些 `W × H` 值最值得实验 |
| 加上宽深通道实验后能否闭环 Can the question be closed with additional width-depth experiments? | 很可能可以 / Very likely yes | 只要实验矩阵足够系统，并且输出指标是 event-level pulse metrics，而不是单一 proxy |
| 最重要的输出变量 What should be the primary outputs? | `pulse height`, `pulse width`, `SNR`, `count rate`, `CV`, `classification accuracy` | 这些量才真正对应 “better pulse signal” |

### 7.1 推荐的最小实验矩阵 / Recommended Minimal Experimental Matrix

建议至少包含：

- 多个 `width` 水平
- 多个 `depth` 水平
- 固定 wavelength
- 固定 spot size / NA
- 固定 slit position（放在 diffracted-light region）
- 固定 flow rate
- 固定 readout / threshold / pulse extraction
- 同一类标准颗粒样本

### 7.2 推荐的核心论文图 / Recommended Core Figures

如果以此写论文，最关键的图通常会是：

1. `W × H -> mean pulse height`
2. `W × H -> count rate`
3. `W × H -> local SNR`
4. `W × H -> classification accuracy`
5. `diffraction-intensity optimum` 与 `pulse optimum` 的偏移图

---

## 8. 最终结论 / Final Conclusion

最符合事实、也最适合作为论文引言空白陈述的一句话是：

中文：

“Tsuyama 团队已经回答了空白通道如何产生参考衍射场、何种条件下 diffracted light intensity 或 detection frequency 更优，以及这些参考场如何支持单颗粒干涉脉冲与分类；但他们尚未系统回答何种通道宽度与深度能够使单颗粒 pulse signal 在事件级指标上综合最优。”

English:

“Tsuyama and co-workers have clarified how a blank nanochannel generates a diffraction reference field, identified condition-specific optima for diffracted-light intensity or detection frequency, and validated the use of that reference field for single-particle interferometric pulses and classification. However, they have not yet systematically determined which channel width and depth maximize event-level pulse performance.”

---

## 9. 参考文献与链接 / References and Links

### 9.1 Tsuyama 相关论文 / Tsuyama-Related Papers

- Tsuyama & Mawatari, `Nonfluorescent Molecule Detection in 10^2 nm Nanofluidic Channels by Photothermal Optical Diffraction`  
  DOI: `10.1021/acs.analchem.9b01334`
- Tsuyama & Mawatari, `Concentration Determination at a Countable Molecular Level in Nanofluidics by Photothermal Optical Diffraction`  
  DOI: `10.1021/acs.analchem.9b04683`
- Tsuyama & Mawatari, `Characterization of optical diffraction by single nanochannel for aL–fL sample detection in nanofluidics`  
  DOI: `10.1007/s10404-020-02333-7`
- Tsuyama & Mawatari, `Concentration Determination at a Countable Molecular Level in Nanofluidics by Solvent-Enhanced Photothermal Optical Diffraction`  
  DOI: `10.1021/acs.analchem.0c02897`
- Tsuyama & Mawatari, `Nanofluidic optical diffraction interferometry for detection and classification of individual nanoparticles in a nanochannel`  
  DOI: `10.1007/s10404-022-02562-y`
- Tsuyama & Mawatari, `Nanofluidic detection platform for simultaneous light absorption and scattering measurement of individual nanoparticles`  
  DOI: `10.1021/acs.analchem.4c01671`

### 9.2 外部专业文献 / External Professional Literature

- Piliarik & Sandoghdar, `Interferometric Scattering Microscopy: Seeing Single Nanoparticles and Molecules via Rayleigh Scattering`  
  Nano Letters, 2019  
  Link: https://pubs.acs.org/doi/10.1021/acs.nanolett.9b01822
- Trueb et al., `Robust Visualization and Discrimination of Nanoparticles by Interferometric Imaging`  
  IEEE Journal of Selected Topics in Quantum Electronics, 2017  
  Link: https://pmc.ncbi.nlm.nih.gov/articles/PMC5627618/
- `Leveraging Partial Coherence to Enhance Nanoparticle Detection Sensitivity and Throughput in Interferometric Scattering Microscopy`  
  ACS, 2025  
  Link: https://pubmed.ncbi.nlm.nih.gov/40861264/

---

## 10. Slide 版浓缩对比表 / Slide-Ready Condensed Comparison Table

> 可直接放进汇报页 / Ready for slides

| Tsuyama 已解决 / Solved | Tsuyama 未解决 / Unsolved |
|---|---|
| 已知道：空白通道怎样形成参考场；固定条件下怎样让衍射更强 / Known: how the blank channel forms the reference field; how diffraction becomes stronger under fixed conditions | 未知道：衍射最强的通道，是否就是脉冲最强的通道 / Unknown: whether the channel with the strongest diffraction is also the channel with the strongest pulse |
| 已知道：为什么 diffracted-light region 会出现 interferometric pulse；什么 detection frequency 更合适 / Known: why interferometric pulses appear in the diffracted-light region; which detection frequency works better | 未知道：width/depth 会怎样改变 `pulse height / width / SNR / counts` / Unknown: how width/depth change `pulse height / width / SNR / counts` |
| 已知道：pulse features 可以用于单/双通道分类 / Known: pulse features can support single-/dual-channel classification | 未知道：什么通道几何最有利于 detectability、robustness 和 classification / Unknown: which channel geometry is best for detectability, robustness, and classification |

### 10.1 一句话版 / One-Line Takeaway

中文：

Tsuyama 已经解决了 `参考场形成` 与 `干涉脉冲存在性`，但尚未系统解决 `通道几何如何决定最优 pulse signal`。

English:

Tsuyama has solved `reference-field formation` and `the existence of interferometric pulses`, but has not yet systematically solved `how channel geometry determines the optimal pulse signal`.

---

## 11. 工程主线相对 Tsuyama 模型的新增考虑 / Additional Factors in Our Engineering Mainline

> 可用于图中外圈、图注或 slide 备注 / Can be used as outer-ring labels, figure notes, or slide annotations

| 外圈标签 / Outer-Ring Label | 简短说明 / Short Note | 可援引文献 / Supportive Papers |
|---|---|---|
| 轨迹与过焦时间 / Transit dynamics | 把静态光学对比转成事件级时域 pulse；决定峰何时出现、持续多久。 / Converts static optical contrast into an event-level time pulse; sets when a peak appears and how long it lasts. | `Tsuyama 2020 counting POD`; `Tsuyama 2022 NODI`; `Tsuyama 2024 POD+NODI` |
| 照明空间分布 / Illumination envelope | 颗粒在束斑中的位置会改变有效照明，从而改变散射振幅和 pulse 高度。 / Particle position within the beam changes effective illumination, and thus scattering amplitude and pulse height. | `Tsuyama 2020 diffraction`; `Tsuyama 2022 NODI` |
| 相对相位演化 / Relative phase evolution | 干涉增强由参考场与散射场的相对相位共同决定，不只取决于散射强度。 / Interference enhancement is governed by the relative phase between the reference and scattering fields, not by scattering amplitude alone. | `Piliarik & Sandoghdar 2019`; `Tsuyama 2022 NODI` |
| 参考场空间选择 / Reference-field selection | 参考场来自被收集的 diffracted-light region；探测位置和收集窗口会改变参考场。 / The reference field is defined by the collected diffracted-light region; detection position and collection window change it. | `Tsuyama 2020 diffraction`; `Tsuyama 2022 NODI` |
| 频率选择与读出链 / Frequency-selective readout | 清晰 pulse 取决于 detection/extraction frequency、time constant 和 leakage suppression。 / Clear pulses depend on detection/extraction frequency, time constant, and leakage suppression. | `Tsuyama 2022 NODI`; `Tsuyama 2024 POD+NODI` |
| 事件提取与可检测性 / Event extraction and detectability | 连续信号要经过 threshold、peak extraction、pairing 和统计评价，才变成可计数、可分类的事件。 / A continuous trace becomes countable or classifiable only after thresholding, peak extraction, pairing, and statistical evaluation. | `Tsuyama 2020 counting POD`; `Tsuyama 2024 POD+NODI`; `Trueb et al. 2017`; `ACS Photonics 2025` |

### 11.1 一句话概括 / One-Line Summary

中文：  
Tsuyama 模型主要回答 `参考场如何形成` 与 `干涉 pulse 为什么出现`，而我们的工程主线进一步把它扩展到 `事件如何形成、如何被读出、以及如何被稳定检测和比较`。

English:

The Tsuyama model mainly explains `how the reference field forms` and `why interferometric pulses appear`, whereas our engineering mainline extends it to `how events form, how they are read out, and how they are robustly detected and compared`.

---

## 12. 图示外圈精简版 / Outer-Ring Labels for the Schematic

> 专为图示（核心圈 = Tsuyama model，外圈 = 工程主线增项）设计。
> Each outer-ring element is: **short label (2–4 chars)** + one-line rationale + single primary citation.

### 12.1 核心圈 / Core Ring

`Tsuyama model`：空白通道参考衍射场 + 单颗粒干涉脉冲生成的静态物理图 / static physics of blank-channel reference field and single-particle interferometric pulse.

### 12.2 外圈六要素 / Six Outer-Ring Elements

| 外圈标签 Label | 一句话注 One-Line Note | 主引用 Primary Citation |
|---|---|---|
| **过焦动力学** Transit dynamics | 颗粒穿束斑的时域轨迹，决定脉冲何时出现、多宽。/ Particle trajectory through the beam sets pulse timing and width. | Tsuyama 2022 NODI |
| **照明包络** Illumination envelope | 高斯光场使有效激发随位置调制，改变散射振幅。/ Gaussian beam modulates effective excitation and scattering amplitude. | Tsuyama 2020 diffraction |
| **相位耦合** Relative phase | 干涉增强由参考与散射场的相对相位决定，非单看强度。/ Interference enhancement is governed by relative phase, not amplitude alone. | Piliarik & Sandoghdar 2019 |
| **收集几何** Collection geometry | slit 位置与 detection window 决定有效参考场。/ Slit position and detection window define the effective reference field. | Tsuyama 2020 diffraction |
| **锁相读出** Lock-in readout | 频率、时间常数、泄漏抑制把连续迹转为清晰脉冲。/ Frequency, time constant, and leakage suppression convert the trace into clean pulses. | Tsuyama 2024 POD+NODI |
| **事件提取** Event extraction | 阈值、峰提取、配对、CV / 分类评价 → 可计数可判别事件。/ Thresholding, peak extraction, pairing, CV, and classification produce countable events. | Trueb et al. 2017 |

### 12.3 图示一句话总括 / One-Line Caption

中文：
> 在 Tsuyama 的"参考场 + 干涉脉冲"静态图之外，工程主线显式建模 `轨迹 → 照明 → 相位 → 收集 → 读出 → 事件` 事件级闭环。

English:
> Beyond Tsuyama's static "reference field + interferometric pulse" picture, our mainline explicitly models the event-level loop `trajectory → illumination → phase → collection → readout → event`.

### 12.4 画图建议 / Drawing Tips

- **只放标签**：外圈每个扇区只写 2–4 字中文标签（如"过焦动力学"），一句话注放图注或 slide 备注。
- **顺序即物理流**：按"左上 → 顺时针"放 `过焦 → 照明 → 相位 → 收集 → 读出 → 事件`，读图即读信号链。
- **引用统一放图注**：在 figure caption 用上表"主引用"列的一条即可，不要把多条 DOI 堆在外圈里。
- **颜色分组**（可选）：前三项（过焦/照明/相位）是 *physics extensions*，后三项（收集/读出/事件）是 *measurement chain*，可用两种色调区分。
