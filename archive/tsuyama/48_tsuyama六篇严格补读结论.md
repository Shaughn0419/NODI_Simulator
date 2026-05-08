# Tsuyama 六篇严格补读结论

<!-- ARCHIVE_STATUS:START -->
> 归档状态：历史快照，仅保留当时推理、实验性计算或迁移记录；不代表当前 v1/v2 结论。当前读者入口请以 `README.md`、`文档导航.md`、`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`、`reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` 和 `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` 为准。
<!-- ARCHIVE_STATUS:END -->

> 建立时间：2026-04-14  
> 用途：回答“工程里的 6 篇 Tsuyama 论文，是否都已经完成阅读、全面分析和参考”  
> 说明：这份文件是在前一轮 `43 / 47` 的基础上，对此前相对浅一些的 `2019 POD`、`2020 counting POD`、`2020 solvent-enhanced POD` 再做一轮严格补读后的结论收口

---

## 1. 最严格口径下的直接回答

如果问题是：

> “工程里的 6 篇 Tsuyama / Mawatari 论文，你是不是都已经真正读过，并且纳入分析和参考了？”

我的当前答案是：

**是，现在 6 篇都已经完成阅读并纳入分析参考。**

但如果问题进一步变成：

> “这 6 篇是不是都已经做到完全同等级、同深度、同约束力度的 code-to-paper 闭环分析？”

最严格的答案是：

**现在已经比上一轮完整得多，但它们对 current 工程主线的约束强度并不相同。**

也就是说：

- 6 篇我现在都读了，也都参考进来了  
- 但不是 6 篇都能同样直接转成 current NODI/exosome 主线的硬约束  
- 真正最直接约束 current 主线的，仍然是：
  - `2020 diffraction`
  - `2022 NODI`
  - `2024 POD+NODI`

而新增补读更深的那 3 篇：

- `2019 POD`
- `2020 counting POD`
- `2020 solvent-enhanced POD`

更多是在 **POD 支线、热扩散语义、diffracted-region 检测逻辑、以及不可外推边界** 上补强，而不是再额外引出新的 current NODI 主线 must-fix。

---

## 2. 当前已覆盖的 6 篇论文

### 2.1 论文清单

1. `Tsuyama_Mawatari_2019_Nonfluorescent Molecule Detection in 10^2 nm Nanofluidic Channels by Photothermal Optical Diffraction`
2. `Tsuyama和Mawatari - 2020 - Characterization of optical diffraction by single nanochannel for aL–fL sample detection in nanoflui`
3. `Tsuyama_Mawatari_2020_Detection and Characterization of Individual Nanoparticles in a Liquid by Photothermal Optical Diffraction and Nanoﬂuidics`
4. `Tsuyama_Mawatari_2020_Concentration Determination at a Countable Molecular Level in Nanofluidics by Solvent-Enhanced Photothermal Optical Diffraction`
5. `Tsuyama_Mawatari_2022_Nanofluidic optical diffraction interferometry for detection and classification`
6. `Tsuyama和Mawatari - 2024 - Nanofluidic detection platform for simultaneous light absorption and scattering measurement of indiv`

### 2.2 当前覆盖深度

| 论文 | 当前覆盖状态 | 对 current 工程主线的直接约束强度 |
|------|--------------|------------------------------------|
| 2019 POD | 已补做严格补读 | 中 |
| 2020 diffraction | 已做严格主审查 | 高 |
| 2020 counting POD | 已补做严格补读 | 中 |
| 2020 solvent-enhanced POD | 已补做严格补读 | 中 |
| 2022 NODI | 已做严格主审查 | 高 |
| 2024 POD+NODI | 已做严格主审查 | 高 |

---

## 3. 这次严格补读的三篇，分别新增了什么

## 3.1 2019 POD：新增确认

### 读到的关键点

1. 信号确实主要出现在 **diffracted-light region**，不是 transmitted-light region  
2. probe focal position 在 channel 上时信号最大，而不是像 TLM/PDS 那样在 `±zc` 处最大  
3. POD 信号与 diffracted-light intensity 近线性  
4. `400 nm × 400 nm` channel 下 LOD `5.0 μM`，约 `500 molecules / 0.23 fL`  
5. 到 `200 nm × 200 nm` channel 时，**sensitivity per detection volume 没有明显恶化**

### 对 current 工程的意义

这篇论文补强了三件事：

1. **slit 选择 diffracted region** 这条底层链是对的  
2. **heat diffusion to glass 可以是信号贡献，不只是热损失**  
3. 对超小通道，POD 不应该继续沿用普通 TLM 那种“越小越崩”的直觉

### 是否引出新的 must-fix

**没有。**

原因是：

- 它主要约束的是 POD molecule-detection 支线
- 当前 mainline 的核心争议在 NODI/exosome/gate/provenance
- 当前代码并没有把 2019 这篇当成 NODI detectability 的直接定量校准

### 但它补出的一条重要边界

如果未来要把 current model 拿去做 **定量 POD molecule validation**，
那就不能只靠现在这套最小 POD/NODI 分频 surrogate。

因为 2019 POD 的实验主语义包括：

- excitation-driven photothermal source
- glass/substrate thermal response
- diffracted intensity enhancement

而 current model 的 POD lane 还主要是 **频率分离与串扰 surrogate**，
不是完整分子级 photothermal amplitude model。

---

## 3.2 2020 solvent-enhanced POD：新增确认

### 读到的关键点

1. POD signal 同时受：
   - `diffraction factor`
   - `photothermal factor`
   控制
2. 当 `n_solvent < n_glass` 与 `n_solvent > n_glass` 时，signal 相位/符号会翻转  
3. 初始 diffracted light intensity `PD` 存在最优值，约在 `15 mV` 左右  
4. modulation frequency 的 S/N 最优点约在 `1.1 kHz`  
5. 用有机溶剂后，POD sensitivity 相对水可提高到 `>30x`  
6. 优化后 LOD 可到 `75 nM`，约 `10 molecules / 0.23 fL`

### 对 current 工程的意义

这篇论文补充得最重要的一点是：

> **POD 不能被理解成“只有一个热项”的检测。**

它明确说明：

- reference/diffraction side
- photothermal side
- solvent refractive index
- `dn/dT`

是耦合在一起决定 POD signal 的。

### 是否引出新的 current mainline must-fix

对 **当前 NODI/exosome 主线** 来说，**没有新增 must-fix**。

因为：

- 这篇主要是 molecule-POD / solvent-enhanced POD
- current mainline 默认并不拿它做 exosome/NODI 的定量标定

### 但它补出的一条严格边界

如果未来我们要声称 current model 已经可以 **定量解释 POD 溶剂增强、符号翻转、分子级浓度 LOD**，
那这个说法现在还不能成立。

因为 current model 里还没有实验级显式建模：

1. solvent-dependent `dn/dT`
2. photothermal source term
3. `n_solvent > n_glass` 时 POD sign flip
4. 实验级 `PD optimum`

所以这篇论文对当前最严格口径的意义是：

> **它没有再暴露出 NODI 主线 bug，但它要求我们把 POD 支线的“可解释范围”说得更克制。**

---

## 3.3 2020 counting POD：新增确认

### 读到的关键点

1. channel 约 `800 × 710 nm`
2. `100 kPa` 时流速约 `0.17 mm/s`
3. particle transit through focus 约 `10 ms`
4. lock-in 条件约 `1.1 kHz`、`2 ms`
5. `20 nm Au` 在 counting-mode POD 下接近 `100% detection efficiency`
6. peak counts per unit time 服从 Poisson，说明重复计数和 trapping 很小
7. 在 nanochannel 里 beam spot `≫` channel，trajectory dependence 被显著压低
8. size estimate 基本遵循 photothermal absorption 路径，近似 `signal ~ d^3`

### 对 current 工程的意义

它强化了两条我们已经在 `2022/2024` 上用到的判断：

1. `~10 ms` transit 是真实可信的时间尺度  
2. 在 sub-μm channel 中，particle path 的横向差异会被 beam-over-channel 几何大幅压缩

### 是否引出新的 current mainline must-fix

**仍然没有新增 must-fix。**

但它提供了一个非常重要的“不能误外推”提醒：

> **20 nm Au 在 POD 里接近 100% detect，不等于 20 nm Au 在 NODI scattering lane 里也应该接近 100%。**

也就是说：

- 2020 counting POD 强支撑 POD absorption lane
- 2022/2024 则告诉我们 NODI scattering lane 的 `20 nm Au` 更接近边界

所以这反而进一步支持我们当前已经写过的边界：

**不能把 POD 成功 detectability 直接拿来替 NODI 主 gate 背书。**

---

## 4. 六篇合起来后，有没有新增 current code must-fix

最严格的结论是：

**没有新增 current NODI/exosome 主线 must-fix。**

六篇都看完后，当前最重要的 must-fix 仍然还是之前已经识别并处理过的那些：

1. `NA cutoff`
2. illumination / collection 解耦
3. `overfill` 语义修正
4. Gouy 去重
5. Tsuyama gold validation 的 `paper_aligned` 判据修正
6. Tsuyama 支撑范围缩窄

这次补读新增的，主要不是新的 code bug，而是两类 **更严格的边界判断**：

### 4.1 POD 支线的定量能力不能说过头

当前 POD lane 更像：

- frequency-separation surrogate
- leakage / crosstalk surrogate

而不是：

- solvent-calibrated photothermal amplitude model
- molecule-level POD concentration metrology model

### 4.2 POD detectability 不能直接外推到 NODI detectability

特别是：

- `20 nm Au` 在 2020 counting POD 里接近 `100%` detect
- 不能据此要求 2022/2024 NODI lane 也必须达到同等级 detectability

---

## 5. 现在对“六篇是否都完成全面分析和参考”的最终说法

我建议以后对外或对项目内部，都用下面这个最严格版本来表述：

### 可以成立的说法

1. **工程里的 6 篇 Tsuyama 论文，现在都已经完成阅读并纳入分析参考。**
2. **其中 2020 diffraction、2022 NODI、2024 POD+NODI 是 current NODI/exosome 主线最核心的外部约束链。**
3. **2019 POD、2020 counting POD、2020 solvent-enhanced POD 进一步补强了 POD / diffraction / thermal-diffusion 语义，但没有额外引出新的 current NODI 主线 must-fix。**

### 不应再说的过头表述

1. 不应说“6 篇都同样直接完成了对 exosome 主路线的验证”  
2. 不应说“当前 POD lane 已经达到 2019/2020 POD 论文那种实验级定量模型”  
3. 不应说“20 nm Au 在 POD 的高 detectability，直接证明了 NODI lane 也应同样高 detectability”

---

## 6. 这轮补读后的最终一句话

**现在我可以更严格地说：6 篇 Tsuyama 论文都已经读过并纳入分析了；但它们对 current 工程主线的约束并不等强，而新增补读的 3 篇主要补的是 POD 支线边界，不是新的 current NODI 主线硬 bug。**
