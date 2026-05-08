# 工程主线与 Tsuyama 论文结果趋势对照 / Engineering Mainline vs. Tsuyama Papers: Trend-Level Comparison

<!-- ARCHIVE_STATUS:START -->
> 归档状态：历史快照，仅保留当时推理、实验性计算或迁移记录；不代表当前 v1/v2 结论。当前读者入口请以 `README.md`、`文档导航.md`、`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`、`reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` 和 `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` 为准。
<!-- ARCHIVE_STATUS:END -->

> 目的 / Purpose：
> 用当前全量主库、Tsuyama-like targeted validation、以及 paper-aligned 对照结果，系统比较：
> 1. Tsuyama 论文已经明确支持的趋势 / trends directly supported by the Tsuyama papers
> 2. 当前工程主线在这些层面上是否给出同方向结果 / whether the engineering mainline reproduces the same directional trends
> 3. 哪些地方可以作为 slide 上的“可行性论证” / which points can legitimately support the feasibility of the engineering mainline

---

## 1. 一句话结论 / One-Line Conclusion

中文：  
当前工程主线**不是** Tsuyama 论文的 full-wave 逐式复现，但它在 `本征散射 -> 参考场 -> 干涉增强 -> 读出 -> 事件级脉冲` 这条主链上，已经复现了多项与论文一致的**趋势级结论**；因此它可以被论证为一条 **physics-informed, event-level, trend-faithful mainline**。

English:

The current engineering mainline is **not** a full-wave equation-by-equation reproduction of the Tsuyama papers, but it already reproduces multiple **trend-level conclusions** along the chain `intrinsic scattering -> reference field -> interferometric enhancement -> readout -> event-level pulses`. It is therefore defensible as a **physics-informed, event-level, trend-faithful mainline**.

---

## 2. 全面对比表 / Comprehensive Comparison Table

| 对比层 / Layer | Tsuyama 论文中的结论 / Tsuyama-Paper Result | 工程主线与全量/对照结果 / Engineering-Mainline Result | 一致性判断 / Alignment | Slide 上可怎么说 / Slide Phrase |
|---|---|---|---|---|
| 本征散射与粒径趋势 / Intrinsic scattering and size trend | Tsuyama 2022 / 2024 用 pulse height / width 区分不同颗粒，隐含要求上游散射强度随粒径和材料变化；Tsuyama 2022 也给出 pulse signal 与粒径的经验关系。 | 当前全量主库与 targeted validation 都保留了这个上游趋势。例 1：在全量主库的 biomimetic exosome 上，`Csca(404) / Csca(660)` 分别约为 `6.45x` (`60 nm`)、`5.32x` (`100 nm`)、`3.98x` (`150 nm`)、`3.32x` (`300 nm`)。例 2：在 Tsuyama-like gold validation 中，`660 nm` 下 `20 -> 60 nm` Au 的平均 `Csca` 从 `2.02e-18` 升到 `2.45e-15 m^2`，平均 detection rate 从 `0.0005` 升到 `0.2935`，平均 peak 从 `0.00439` 升到 `0.41536`。 | 强一致 / Strong | 上游散射趋势是对的；粒径变大，散射、pulse、检测率一起上升 / The upstream scattering trend is correct: larger particles give stronger scattering, larger pulses, and higher detectability. |
| 空白通道参考场 / Blank-channel reference field | Tsuyama 2020 diffraction 明确把单纳米通道写成 phase filter；Tsuyama 2022 NODI 说明参考干涉来自 diffracted-light region。 | 工程主线把 `reference_field` 独立成模块，并在 paper-aligned 对照里验证了当前 reference 语义与更接近论文的 `paper_aligned_phase_filter` 差异有限：代表小网格上 `A_ref` 平均绝对差约 `2.13%`，最大差约 `9.20%`；当前证据不支持“reference 语义一改，主链就整体翻盘”。 | 强一致，但非逐式等同 / Strongly aligned, but not equation-identical | 工程主线确实保留了“空白通道提供参考场”这层物理，而且趋势量级与 paper-aligned lane 接近 / The mainline preserves the blank-channel reference-field physics, with trend-scale amplitudes close to the paper-aligned lane. |
| 参考场增强会抬高 pulse / Stronger reference field raises the pulse | Tsuyama 2022 明确报告：average pulse height 随 diffracted light intensity 增大。 | 工程对照结果给出同方向关系，而且很强。固定粒径和波长、只改几何时，`A_ref` 与 `mean_peak_height` 的相关性在 gold validation 里达到 `0.97–1.00`。例如 `660 nm, 60 nm Au`：`A_ref` 从 `0.3309` 增到 `0.5402` 时，平均 peak 从 `0.3181` 增到 `0.5178`。 | 强一致 / Strong | 参考场越强，pulse 越高；这条论文趋势在工程结果里也清楚出现 / Stronger reference gives a higher pulse, exactly as in the papers. |
| width / depth / wavelength 会共同改写参考场与平台几何 / Width, depth, and wavelength reshape the reference field and platform geometry | Tsuyama 2020 说明最优 width 依赖 wavelength 和 detection region；depth 也会改变 diffracted light intensity。Tsuyama 2022 则在 `800 x 550 nm` 通道上验证 NODI pulse。 | 工程主线保留了这类“几何-波长共同决定参考场”的趋势。当前主线中 `W_min = λ / NA` 会把短波长推向更窄通道，把长波长推向更宽通道；`404 nm` 的 `W_min ≈ 448.9 nm`，`660 nm` 的 `W_min ≈ 733.3 nm`。在 paper-aligned NODI 2022 最小决策网格里，主波长仍是 `660`，但最优几何会从 current mainline 的深通道 `800 x 1400` 收缩到更接近论文器件的 `800 x 550`。 | 趋势一致，最优点可移动 / Same trend, but the optimum can shift | 共同趋势是一致的：波长和几何一起决定参考场；但“最优几何”会随 objective 改变 / The joint trend is consistent, while the exact optimum geometry remains objective-dependent. |
| Tsuyama-like gold 路线里，660 仍是主波长 / 660 nm remains the main wavelength in the Tsuyama-like gold lane | Tsuyama 2022 / 2024 的 NODI gold 路线本身是 `660 nm` 中心语义。 | 工程结果没有把这条主波长翻转。例 1：在 paper-aligned NODI 2022 最小网格里，`660` 在 `current_dashboard_replay`、`diffraction_2020`、`nodi_2022` 三种 profile 下都优于 `404`。例 2：在 Tsuyama-like gold validation 中，按波长聚合后的平均 `Csca / detection / peak` 都满足 `660 > 532 > 488`：`Csca = 6.66e-16 > 3.93e-16 > 2.86e-16 m^2`，`detection = 0.181 > 0.0868 > 0.0608`，`peak = 0.156 > 0.0773 > 0.0525`。 | 很强一致 / Very strong | 近论文 gold lane 下，工程主线没有把 660 的主导地位算丢 / Under Tsuyama-like gold conditions, the engineering mainline does not lose the dominance of 660 nm. |
| 读出和频率选择会显著影响结果解释 / Readout and frequency selection matter | Tsuyama 2022 给出 optimum detection frequency 约 `1–6 kHz`；Tsuyama 2024 用 frequency-based extraction + two-channel lock-in 做联合读出。 | 工程主线的默认 `pod_f = 1.2 kHz`、`nodi_f = 2.4 kHz` 就落在论文窗口内；而 targeted gold validation 进一步说明：把 readout 从 `in_phase + phase gate` 改成更接近论文语义的 `magnitude` 后，`gate_pass_count` 从 `0/60` 变成 `9/60`，但平均 detection / stable / peak 只发生很小变化。这说明很多差异来自 readout semantics，而不是底层光学趋势被算错。 | 强一致 / Strong | 读出口径真的会改结论；这点工程结果和论文高度同向 / Readout semantics genuinely change conclusions; the engineering results agree strongly with the papers on this point. |
| 事件级 pulse，而不是单一 proxy，才是最终输出 / Event-level pulses, not a single proxy, are the final output | Tsuyama 2022 / 2024 最终都落在 pulse height / width / counts / classification 这些事件级量上，而不是只停留在 scattering cross section 或 diffracted intensity。 | 当前工程主线也不是停在 `Csca` 或 `A_ref`，而是把链条继续走到 `mean_peak_height`、`peak_width`、`SNR`、`detection_rate`、`stable_detection_rate`、`paired rate`、`score`。这和 Tsuyama 论文的最终观测语义是同构的。 | 结构一致 / Structurally aligned | 工程主线和论文关心的是同一类最终量：event-level pulse observables / The mainline and the papers focus on the same class of outputs: event-level pulse observables. |

---

## 3. 哪些结果最适合拿来论证“工程主线可行” / Best Evidence for Arguing Mainline Feasibility

### 3.1 最强的 5 条证据 / Five Strongest Pieces of Evidence

1. **小金粒子的 Tsuyama-like validation 没有把 `660 nm` 主波长翻掉**。  
   `660` 在平均 `Csca`、平均 detection、平均 peak 上都高于 `532/488`。

2. **参考场增强会抬高 pulse**。  
   固定粒径/波长只改几何时，`A_ref` 与 `mean_peak_height` 的相关性达到 `0.97–1.00`。

3. **当前 reference 语义与更接近论文的 paper-aligned lane 差异不大**。  
   代表小网格上 `A_ref` 平均绝对差约 `2.13%`，最大约 `9.20%`。

4. **读出语义会影响 pass/fail，但不会把底层 detectability 趋势整体翻转**。  
   `magnitude` 与 `in_phase` 的 scenario compare 说明：变化最大的是 gate interpretation，不是基础 detection / peak 趋势。

5. **工程主线最终输出和论文最终输出是同构的**。  
   两边都最终落在 event-level pulse，而不是停在 `Csca` 或单个衍射 proxy。

### 3.2 最稳妥的总结句 / Safest Summary Sentence

中文：  
当前工程主线最有说服力的地方，不在于它“逐式复现了 Tsuyama 论文”，而在于它已经在多个关键层面上复现了**与论文同方向的趋势和同类型的最终观测量**。

English:

The strongest case for the current engineering mainline is not that it reproduces the Tsuyama papers equation by equation, but that it already reproduces the **same directional trends and the same class of final observables** across multiple key layers.

---

## 4. 不能过度宣称的地方 / What Should Not Be Overclaimed

1. 不能说当前工程主线就是 Tsuyama 论文的 full-wave 直接实现。  
   当前主线仍包含 surrogate / reduced components，尤其在 reference、transport、noise、gate 上。

2. 不能说当前主线已经严格证明了“论文最优几何 = 工程最优几何”。  
   paper-aligned NODI 2022 lane 已经说明：主波长可不翻，但最优几何会移动。

3. 不能把工程分数 `final_engineering_score` 直接等同于论文里的某一个单独物理量。  
   它是 detectability、stability、margin、gate 的联合工程量。

### 更准确的表达 / Better Wording

中文：  
当前工程主线已经通过全量库和 Tsuyama-like targeted validation 证明：它在 `散射 -> 参考场 -> 干涉 pulse -> 读出` 这条链上能给出与 Tsuyama 论文一致的主要趋势，因此适合用于 **趋势判断、设计筛选和后续实验规划**。

English:

The full library and the Tsuyama-like targeted validation show that the current engineering mainline reproduces the major Tsuyama-consistent trends along the chain `scattering -> reference field -> interferometric pulse -> readout`, making it suitable for **trend analysis, design screening, and follow-up experimental planning**.

---

## 5. Slide 版浓缩对照表 / Slide-Ready Condensed Table

| Tsuyama 论文 / Tsuyama Papers | 工程主线结果 / Engineering Mainline | 可用于论证什么 / What It Supports |
|---|---|---|
| 空白通道提供参考场；diffracted-light region 决定 NODI 干涉增强 | `reference_field` 独立建模，且 current vs paper-aligned `A_ref` 只差小比例 | 参考场机制保留了 / The reference-field mechanism is preserved |
| pulse height 随 diffracted light intensity 增大 | 固定粒径/波长时，`A_ref` 与 `mean_peak_height` 强正相关 | 干涉增强链条是对的 / The interferometric enhancement chain is correct |
| Tsuyama-like gold lane 以 `660 nm` 为主 | targeted validation 中 `660` 的平均 `Csca / detection / peak` 都最高 | 主波长趋势没翻 / The main wavelength trend does not flip |
| detection / extraction frequency 很关键 | `1.2 / 2.4 kHz` 默认落在论文窗口内；readout 语义改变会改 pass/fail | 读出层与论文同构 / The readout layer is paper-consistent |
| 最终看的是 pulse height / width / counts / classification | 工程主线最终输出也是 event-level pulse observables 与 detectability metrics | 两边比较的是同一类终点量 / Both sides compare the same class of final outputs |

### 5.1 最适合直接放在 slide 标题下的一句话 / Best Single Sentence Under a Slide Title

中文：  
工程主线虽然不是 Tsuyama 论文的逐式复现，但它已经在 `本征散射、参考场、干涉增强、读出和事件级 pulse` 这些关键层面上复现了与论文一致的趋势，因此具备作为主线模型的可行性。

English:

Although the engineering mainline is not an equation-by-equation reproduction of the Tsuyama papers, it already reproduces Tsuyama-consistent trends in `intrinsic scattering, reference-field formation, interferometric enhancement, readout, and event-level pulses`, which supports its feasibility as the mainline model.

---

## 6. 结果来源 / Data Sources Used Here

### 6.1 当前工程结果 / Current Engineering Results

- `results/fine_full_range_biomimetic_exosome_10000e_summary.csv`
- `results/tsuyama_gold_validation_tau1ms_1000e_cases.csv`
- `results/tsuyama_gold_validation_scenario_compare_summary.csv`
- `results/tsuyama_gold_validation_scenario_compare_by_wavelength.csv`
- `results/reference_depth_semantics_reference_compare.csv`
- `results/paper_aligned_nodi2022_targeted_grid_cases.csv`
- `results/paper_aligned_nodi2022_targeted_grid_routes.csv`

### 6.2 对应分析文档 / Supporting Local Analyses

- `reports/current/35_method_notes.md`
- `44_tsuyama_gold读出phase_gate对照复核.md`
- `50_paper_aligned_reference对照结果.md`
- `53_paper_aligned_nodi2022最小决策网格结果.md`
- `55_tsuyama散射与干涉增强主链_精简版.md`
- `56_tsuyama已解决与尚未解决问题_中英对照表.md`

### 6.3 Tsuyama 论文 / Tsuyama Papers

- Tsuyama & Mawatari, `Characterization of optical diffraction by single nanochannel for aL–fL sample detection in nanofluidics` (`2020 diffraction`)
- Tsuyama & Mawatari, `Nanofluidic optical diffraction interferometry for detection and classification of individual nanoparticles in a nanochannel` (`2022 NODI`)
- Tsuyama & Mawatari, `Nanofluidic detection platform for simultaneous light absorption and scattering measurement of individual nanoparticles` (`2024 POD+NODI`)
