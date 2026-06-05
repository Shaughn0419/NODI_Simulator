# 全论文库抽取与工程参照分析报告

日期：2026-05-18

## 1. 完成状态

本轮已完成 `papers/` 下全部本地 paper 的去重、文本抽取、图像/图表证据抽取、逐篇工程分析卡生成，以及覆盖复核。

结果目录：

- `papers/analysis_full_v1/`

核心索引：

- `papers/analysis_full_v1/manifest.csv`：69 个本地文件实例，含重复路径到唯一 paper 的映射。
- `papers/analysis_full_v1/manifest_unique.csv`：53 个唯一内容 hash。
- `papers/analysis_full_v1/library_engineering_matrix.csv`：逐篇工程用途和 claim boundary 矩阵。
- `papers/analysis_full_v1/library_table_gap_review.csv`：机器表格缺口的增强分类、layout/OCR 候选状态和复核动作。
- `papers/analysis_full_v1/library_engineering_evidence_ledger.csv`：跨论文工程证据台账，绑定 priority、topic、证据类型、路径和人工复核动作。
- `papers/analysis_full_v1/library_gap_review.md`：最终覆盖和缺口复核。
- `papers/analysis_full_v1/library_quality_review.csv`：逐篇抽取/分析质量审计表。
- `papers/analysis_full_v1/<paper_id>/analysis.md`：每篇 paper 的工程分析卡。
- `reports/126_paper_library_post_soffice_quality_review.md`：安装 `soffice` 后的二次质量复核报告。
- `reports/127_paper_library_evidence_enhancement_plan.md`：证据补强路线。
- `reports/128_paper_library_evidence_enhancement_report.md`：表格缺口与工程证据台账补强结果。

复核结果：

- 文件实例覆盖：69 / 69
- 唯一内容覆盖：53 / 53
- 抽取失败：0
- 低文本风险文件（<1000 chars）：0
- 无图像或关键页面视觉证据文件：0
- DOCX supplementary：`soffice` 渲染状态 `ok`，输出 9 页 PNG、5 个 embedded images、2 个 table CSV。
- 逐篇质量审计：53 / 53，`needs_fix=0`。
- 机器表格抽取为 0 的 41 篇已完成增强分类：13 篇补出 layout/OCR 候选，28 篇重分类为非表格型图文证据缺口，剩余纯视觉表格复核项为 0。

## 2. 产物怎么用

建议以后查文献证据时按这个顺序走：

1. 先打开 `library_engineering_matrix.csv`，按 priority / topic 找候选 paper。
2. 再打开对应 `<paper_id>/analysis.md`，看工程用途、不能外推的边界和候选数值。
3. 需要引用图表或表格时，打开同目录下：
   - `text/full_text.txt`
   - `caption_index.csv`
   - `tables/*.csv`
   - `page_renders/*.png`
   - `figures/embedded/*`
4. 若机器表格 CSV 缺失，先查 `library_table_gap_review.csv` 和对应 `<paper_id>/evidence/table_candidates.csv`。
5. 任何要进入代码、参数、报告 claim 的硬约束，都应回到原 PDF 页面、表格候选或渲染图复核一遍。

## 3. 工程分层结论

### 3.1 Tsuyama / Mawatari 主链

这组仍是工程最核心的 paper-alignment 参照源。它们不是一个可以合并成单一 calibration 的证据包，而是分层约束：

- `2020 diffraction`：约束 nanochannel diffraction / phase-filter / width-depth reference 语义。
- `2022 NODI`：约束 single-channel NODI 的 reference light、Au/Ag particle ladder、pulse height/width、selected detector-mode、dual-wavelength classification。
- `2024 paired POD+NODI`：约束 paired absorption + scattering readout，但不能替代 2022 NODI 单通道校准。
- `2019/2020 POD`：约束 photothermal / solvent-enhanced / counting branch，不能直接当作 NODI scattering 检出率。

工程使用方式：

- 用于维护 `paper_aligned` / `selected_annulus` / `Tsuyama BFP` / `readout_transfer` 的边界。
- 用于检查 `660 nm`、`800/1200 x 550 nm`、`488/532/660 nm`、Au20/30/40/60 和 Ag40/60 的 paper-geometry / particle ladder 解释。
- 用于防止把 2020 POD 的 Au20 近 100% counting 误读成 2022 NODI selected-annulus detection target。

不能外推：

- 不能说当前 simulator 已经完成 Tsuyama raw physical calibration。
- 不能把 POD thermal absorption、NODI scattering、paired POD+NODI classification 混成一个统一 claim。
- 不能把 selected-annulus proxy 写成实验测得的 crossing-denominator efficiency。

### 3.2 Mie / Au-Ag 材料常数 / optical constants

代表 paper 包括 Bohren & Huffman、Johnson & Christy、Jain、Crut、Zhang 等。

工程使用方式：

- 支撑 `Csca/Cabs`、Au/Ag wavelength trend、粒径 scaling、材料常数不确定性的复核。
- 用于解释为什么 optical constants / Mie choice 会影响 `Au20_equivalent`、Ag/Au signal ratio 和 photothermal branch。

不能外推：

- Mie/material 正确不等于 detector transfer、blank noise、NODI reference、pulse extraction 都正确。
- Johnson & Christy 这类薄膜 optical constants 需要记录材料来源和适用范围，不能当作唯一无不确定性真值。

### 3.3 iSCAT / interferometric scattering / dark-field 相关

代表 paper 包括 Mitra、Ortega-Arroyo & Kukura、Young & Kukura、Young et al.、Spackova、Chen、Taylor、Wu 等。

工程使用方式：

- 支撑 reference-field heterodyne / interferometric contrast 的物理方向。
- 帮助判断 current simulator 中 `reference field -> interferometric trace -> pulse observable` 这条链是否保留了正确观测语义。
- 对 dark-field / nanofluidic / plasmonic scattering 的灵敏度和背景抑制提供机制参照。

不能外推：

- iSCAT 机制支持不自动给出 Tsuyama nanochannel geometry。
- surface / substrate / plasmonic interface 条件不同的 paper，只能做机制参照，不能直接替换 NODI channel reference。

### 3.4 EV refractive index / core-shell / scatter calibration

代表 paper 包括 Pleet、de Rond、van der Pol、Gardiner、Kashkanova、Varga、Welsh 等。

工程使用方式：

- 支撑 EV/exosome material prior、RI range、hollow/core-shell 风险、calibration bead 和 standard-particle ladder 设计。
- 支撑报告中对“EV-like / exosome-like / biological specificity”的谨慎措辞。
- 支撑 dashboard/reporting 中 calibration、sample prep、single-vs-swarm、standard-unit conversion 等 blocker。

不能外推：

- EV scatter calibration 不等于 NODI absolute SNR calibration。
- EV sample RI / size distribution 不足以证明 biological exosome specificity。
- Flow cytometry scatter units 和 NODI pulse score 之间需要显式 bridge，不能直接互换。

### 3.5 Detector calibration / LOD / reporting

代表 paper 包括 FCMPASS、MIFlowCyt-EV、Wood & Hoffman、de Rond 2020、single-vs-swarm detection 等。

工程使用方式：

- 检查 threshold、LOD、blank false positive、standard ladder、calibration manifest、reporting fields。
- 支撑当前报告里 “no measured data / no calibrated absolute claim” 的边界。
- 对 future measured-data closure 的实验记录模板有直接价值。

不能外推：

- fluorescence sensitivity / flow-cytometer scatter sensitivity 不应直接变成 NODI detector absolute sensitivity。
- 没有 blank、standard particle、detector transfer 和 sample-control 数据时，不能解锁 calibrated claim。

### 3.6 Flow / Brownian / nanofluidic transport

代表 paper 包括 Huh、Ishibashi、Mawatari extended nanofluidics、Morikawa、Schoch 等。

工程使用方式：

- 支撑 pressure-driven injection、attoliter/nanoliter handling、wall exclusion、diffusion、transport time、nanochannel fabrication feasibility。
- 对 transit-time、event rate、particle-channel interaction、fluidic practicality blocker 有价值。

不能外推：

- 通用 nanofluidic flow 论文不能直接给当前 W/H/lambda/objective 推荐排序。
- Fabrication feasibility 与 optical detectability 是不同层，不能互相替代。

### 3.7 Photothermal POD / absorption branch

代表 paper 包括 Shimizu 和 Tsuyama/Mawatari POD 相关 paper。

工程使用方式：

- 支撑 absorption / thermal lens / solvent enhancement / differential frequency extraction 的边界。
- 对 future paired POD+NODI 或 absorption sidecar 有价值。

不能外推：

- POD branch 不能直接校准 single-channel NODI scattering detection。
- Photothermal signal、thermal diffusion 和 NODI pulse event 的时间/频率语义必须分开。

### 3.8 EV sample preparation / biology

代表 paper 包括 Malvicini 2024 等。

工程使用方式：

- 提醒样品制备和 isolation method 会改变 EV characteristics / functional activity。
- 对未来实验设计、sample-control panel 和 biological specificity claim 有价值。

不能外推：

- Sample-prep 论文不能替代 optical calibration。
- 不应从 sample biology 直接推出 NODI detectability 或 device ranking。

## 4. 当前优先级分布

- critical：9
- high：23
- medium：18
- background：3

读法：

- `critical`：直接关系 Tsuyama/Mawatari paper-alignment 或 nanofluidic/POD/NODI 主边界。
- `high`：会直接影响材料、EV calibration/reporting、detector/threshold 或主 claim 语言。
- `medium`：支撑机制、transport、fabrication、iSCAT context 或 future experimental closure。
- `background`：主要做边界和背景，不建议直接改参数。

## 5. 复核中的注意点

- MuPDF 在少数 PDF 上报告了 structure tree warning，但最终 `text_chars`、page-level text、visual evidence 和 extraction status 都通过；当前判断为 PDF 标记结构 warning，不是抽取失败。
- `soffice` 已安装并复核可用；DOCX supplementary file 已完成 XML/text/media/table 抽取和 LibreOffice 版式渲染。
- `pdfplumber` 表格抽取对科研 PDF 不稳定，尤其多栏排版和图片表格；已用 `pdftotext -layout` 与 `tesseract` 补出 100 条更严格筛选后的表格候选，并把非表格型缺口拆出。
- 自动分析卡会提取候选句和数值 hook，但最终 claim 必须以原文页面/表格复核为准。

## 6. 对工程下一步的建议

1. 若要改 simulation 参数，优先从 `critical` 和 `high` 的 analysis card 查证据。
2. 若要写报告或对外 claim，先查 `library_engineering_matrix.csv` 的 `main_boundary` 列，避免跨机制外推。
3. 若要推进 measured-data closure，优先把 EV calibration/reporting、detector threshold、blank false positive、standard ladder、sample prep 这些 paper 的要求转成实验 checklist。
4. 若要继续 Tsuyama 对齐，不建议继续无边界扩大 numeric fitting；应回到具体 paper item：geometry、readout、Table S1、Au/Ag material profile、BFP/reference、blank/noise、classification feature protocol。

## 7. 最终判断

这次完成后，工程内 paper 不再只是“PDF 存放区”。现在已有一套可追踪的抽取和分析底座：每个本地 paper 都能追到文本、图像/图表证据、分析卡、工程用途和 claim 边界。后续真正做参数、报告、实验设计或 reviewer response 时，可以按这套索引逐项引用和复核。
