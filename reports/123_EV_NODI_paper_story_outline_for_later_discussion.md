# EV/NODI paper story outline for later discussion

- 日期：2026-05-14；2026-05-23 状态覆盖
- 状态：讨论草案；不作为 report 88 的 claim 升级
- 作用：把 report 88 / report 140 之后的论文路线、主图结构、验证数据需求和审稿风险先保存下来，后续单独讨论
- 最新 full-grid 依赖：`reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md`
- 背景主报告：`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`

---

## 0. 本文档边界

这不是投稿稿件，也不是新结果报告。它只回答一个问题：

```text
如果以后要把当前 EV/NODI simulator 工程整理成论文，
最稳妥的 scientific story、figure plan、validation package 和 reviewer-risk checklist 应该是什么？
```

**不新增 claim**：

- 不新增 calibrated SNR claim；
- 不新增 absolute LOD claim；
- 不新增 true EV concentration claim；
- 不新增 biological specificity claim；
- 不新增 measured blank safety claim；
- 不把 selected-annulus lens 改写成 optical annular aperture；
- 不把 per-event detectability 改写成 concentration / count-rate / LOD；
- 不把 Tsuyama alignment 改写成 calibrated reproduction。

本文档里的"论文"优先按 **physics-governed relative design-space audit / route-selection framework** 来构思，而不是按 calibrated instrument-performance paper 来构思。

---

## 1. 推荐论文定位

### 1.1 最稳妥定位

建议主定位：

```text
A physics-governed no-measured-data design-space audit framework
for nanofluidic optical diffraction interferometry (NODI) route selection.
```

中文口径：

```text
一种面向 EV/NODI 路线选择的、物理约束的、无实测数据相对设计空间审计框架。
```

核心贡献不是"预测绝对检测性能"，而是：

1. 把 route selection 从单一 `Csca` 或 peak ranking 推进到 observation-chain audit；
2. 把材料 / Mie / detector operator / reference / interference / trajectory / noise / pulse extraction / scoring / claim governance 串成可审计链；
3. 用同一框架解释 660 / 404 / 532 / 488 的不同**路线角色**；
4. 明确指出从 no-measured-data audit 走向 calibrated model 所需的最小 artifact。

### 1.2 可选副定位

| 定位 | 可行性 | 适合期刊层级 | 主要风险 |
|---|---|---|---|
| Simulation method paper | 中高 | 方法 / 仪器模拟 / lab-on-chip 方向 | 审稿人会要求更多验证与 unit / limiting-case tests |
| Design-space audit paper | 高 | 设计方法 / 工程预筛选方向 | 必须把 claim 限制在 relative route selection |
| Tsuyama-aligned trend study | 中 | NODI / nanofluidic optics 特定读者 | 容易被误读成 Tsuyama calibrated reproduction |
| Calibrated EV detection paper | 低（当前不建议）| 更强期刊但门槛高 | 需要 measured blank、standard particle、detector chain、EV characterization |

### 1.3 本工程当前最适合讲的主张

推荐主张：

> We present an auditable surrogate observation-chain framework that ranks NODI route candidates under explicitly no-measured-data assumptions. The framework identifies a 660-nm-centered route as the conservative engineering mainline, preserves 404 nm as a high-value shortwave sidecar, and uses 532/488 nm as Tsuyama-aligned trend controls, while keeping all calibrated performance claims blocked pending measured artifacts.

中文可写为：

> 本文提出一个可审计的 NODI surrogate observation-chain 设计审计框架。在明确无实测校准的前提下，该框架把 660 nm 路线识别为保守工程主线，把 404 nm 保留为高价值短波 sidecar，并将 532/488 nm 作为 Tsuyama 文献趋势对照；所有校准性能声明仍由 measured artifact 阻断。

---

## 2. 论文核心故事线

### 2.1 一句话 story

```text
NODI route selection cannot be decided by scattering strength alone;
it needs a full observation-chain audit.
```

### 2.2 叙事三幕

**第一幕：为什么不能只看散射截面。**

- EV-like Rayleigh particles 在 404 nm 的 `Csca` 高于 660 nm；
- 但 field amplitude 走 `sqrt(Csca)`，不是 `Csca`；
- reference、phase、transit、readout、noise、threshold、pulse extraction 都会改写最终 detectability；
- 所以"shorter wavelength gives stronger scattering"不是 route recommendation。

**第二幕：如何把 observation chain 做成可审计框架。**

- Mie / intrinsic scattering：给出 `Csca`、`S1/S2`、`dCsca/dΩ`；
- detector operator：把 angular scattering 投影到 BFP / slit / ROI surrogate；
- reference field：用 channel diffraction surrogate 提供干涉参考；
- interference：保留 self term + cross term；
- transport / trajectory：决定 transit 和事件采样；
- noise / readout：决定 margin 与 threshold；
- pulse extraction：决定 per-event detectability；
- governance：把 route role、claim level 和 forbidden claim 写入结果。

**第三幕：路线选择不是"波长第一"，而是"角色第一"。**

- 660 nm：conservative main route；
- 404 nm：shortwave sidecar / thermal-sensitive probe；
- 532/488 nm：Tsuyama-aligned controls；
- 任何 route promotion 都需要 measured artifact。

---

## 3. 论文题目候选

1. **Physics-Governed Route Selection for Nanofluidic Optical Diffraction Interferometry**
2. **A Relative Design-Space Audit Framework for EV/NODI Wavelength and Geometry Selection**
3. **From Mie Scattering to Route Governance: An Auditable Observation-Chain Model for NODI Design**
4. **No-Measured-Data Design Auditing of Four-Wavelength NODI Routes for Extracellular-Vesicle-Like Particles**
5. **Surrogate Observation-Chain Modeling for Nanofluidic Interferometric Detection Route Selection**

推荐标题方向是 1 或 2。标题里最好出现 `relative`、`audit` 或 `route selection` 中至少一个词，以免读者预期 calibrated instrument paper。

---

## 4. 摘要逻辑

### 4.1 Abstract skeleton

```text
Background:
Nanofluidic optical diffraction interferometry can detect single nanoparticles,
but route selection across wavelength, channel geometry, readout, and particle
class cannot be based on scattering cross-section alone.

Problem:
Measured blank-channel references, detector operators, standard-particle
calibrations, and EV-specific validation are often unavailable at the
pre-experimental design stage.

Approach:
We construct a physics-governed relative audit framework that propagates
material and particle inputs through Mie scattering, detector-operator
surrogates, channel-reference fields, interferometric trace formation,
transport/readout/noise models, pulse extraction, and claim-governed route
scoring.

Results:
Under the current no-measured-data assumptions, the framework identifies
660-nm routes around 800 x 1400/1500 nm as the conservative engineering
mainline, preserves 404 nm as a high-value shortwave sidecar/probe, and uses
532/488 nm as Tsuyama-aligned trend controls.

Boundary:
The results are relative route-prioritization outputs, not calibrated SNR,
LOD, concentration, count-rate, or biological-specificity claims.

Outlook:
We specify the measured artifact package required to upgrade the framework
from relative audit to calibrated physical prediction.
```

### 4.2 摘要里不能写的句型

避免：

- "We validate the simulator..."，除非只说 validate internal consistency / unit tests；
- "We predict the detection limit..."；
- "We optimize EV detection at 660 nm..."；
- "404 nm is worse / better physically..."；
- "Tsuyama data calibrates our system..."；
- "selected-annulus aperture..."，除非真的有 optical annulus operator 证据。

推荐替代：

- "prioritize route candidates"；
- "relative design audit"；
- "mechanism-aligned trend controls"；
- "calibration-blocked performance claims"；
- "validation artifacts required for upgrade"。

---

## 5. 论文结构提纲

## 5.1 Introduction

### 5.1.1 Problem statement

- EV / nanoparticle detection in nanofluidic channels requires high sensitivity and robust route choice.
- NODI uses channel diffraction / reference scattering interference; the detectable event is not just particle scattering cross-section.
- Wavelength and geometry choices jointly affect scattering, reference, transit, phase, readout, and noise.

### 5.1.2 Why a design audit is needed

- Experimental calibration artifacts are expensive and may not exist at design stage.
- A premature calibrated claim would be misleading.
- But a purely heuristic ranking is also insufficient.
- Need an audit framework that is more physical than a score table, while staying honest about no measured data.

### 5.1.3 Literature anchor

- Tsuyama / Mawatari NODI and POD work provides mechanism and trend anchors:
  - nanochannel diffraction reference;
  - slit / pinhole / lock-in style readout;
  - Au / Ag and 488 / 532 nm dual-wavelength classification contexts;
  - absorption / scattering separation in later work.
- iSCAT literature provides interference and reference/scattering phase framing.
- EV literature provides optical-property and biological-specificity limits.

### 5.1.4 Main contribution

- An auditable observation-chain simulator for route selection.
- A governance layer separating relative route recommendation from calibrated claims.
- A four-wavelength role analysis.
- A validation roadmap.

## 5.2 Methods

### 5.2.1 Design-space definition

- Wavelengths: 404 / 488 / 532 / 660 nm.
- Channel geometry grid: width / depth candidates.
- Particle classes:
  - EV biomimetic;
  - Au anchors;
  - Ag / Tsuyama anchor target-fitting panel;
  - contaminant / uncertainty profiles where available.
- Readout / optical scenarios:
  - all-crossing engineering lens;
  - selected-annulus Tsuyama-anchored EV application lens;
  - v2 scenario bundles.

### 5.2.2 Observation-chain model

Subsections:

1. Material dispersion and particle representation.
2. Mie / intrinsic scattering.
3. Detector operator surrogate.
4. Channel reference field surrogate.
5. Interferometric trace.
6. Trajectory and transport.
7. Noise and readout.
8. Pulse extraction.
9. Batch statistics.
10. Route scoring and claim governance.

Each subsection should include:

- formula;
- implemented file/function;
- units;
- what is physical vs surrogate;
- what validation artifact would upgrade it.

### 5.2.3 Lens definitions

| Lens | What it answers | Denominator | Claim level |
|---|---|---|---|
| All-crossing engineering lens | EV / NODI engineering route selection | all BFP / all crossings | relative route recommendation |
| Selected-annulus Tsuyama-anchored EV application lens | B1 Au/Ag anchor target-fitting plus B2 EV biomimetic application | fixed selected-annulus 0.5-0.8 | diagnostic / negative_or_diagnostic_result_only |
| NODI engineering lens | stricter NODI-like candidate subset | gate-passing subset | internal consistency and trend |

### 5.2.4 Scoring and route governance

Define:

- `score`;
- `engineering_score`;
- `engineering_gate`;
- `observation_freeze_status`;
- `route_role`;
- `final recommendation`;
- forbidden claim filters.

This section should explicitly show why a high score is not automatically a route recommendation.

### 5.2.5 Reproducibility and artifact manifest

- Code modules.
- Configs.
- Result directories.
- Review package manifest.
- Test suite.
- Hash/provenance policy.

## 5.3 Results

### Result 1: Observation-chain coverage

Message:

> The simulator covers the full route-selection observation chain, but with explicit surrogate boundaries.

Figure:

- Full workflow diagram.

Table:

| Stage | Formula/model | Evidence level | Current limitation | Upgrade artifact |
|---|---|---|---|---|

### Result 2: Scattering strength alone misleads route selection

Message:

> 404 nm can raise intrinsic scattering and peak proxy, but transit, phase, readout, threshold, and governance prevent direct main-route promotion.

Figures:

- Fixed-geometry four-wavelength signal-chain plot.
- Stage waterfall: `Csca -> sqrt(Csca) -> reference/cross-term -> peak -> margin -> detection`.

### Result 3: Four-wavelength role map

Message:

> The four wavelengths have different roles, not a single best-wavelength ordering.

Figure:

- Route-role decision matrix.

Table:

| Wavelength | Role | Support | Risk | Next validation |
|---|---|---|---|---|

### Result 4: Geometry and governance change the naive ranking

Message:

> Numeric high-score routes can be downgraded by width-prior risk, weak-reference status, or route-governance blockers.

Figures:

- Wavelength x geometry heatmap.
- Governance overlay showing promoted / not promoted / sidecar / control.

### Result 5: Dual-lens reconciliation

Message:

> The engineering all-crossing lens and the selected-annulus Tsuyama-anchored EV application lens answer different questions and must remain parallel.

Figure:

- Lens agreement / disagreement matrix.

Table:

| Route | Lens A verdict | Lens B verdict | Integrated reading | Forbidden misread |
|---|---|---|---|---|

### Result 6: Tsuyama alignment is a trend anchor, not calibration

Message:

> Tsuyama data supports mechanism and trend alignment but does not calibrate this simulator without matching measured artifacts.

Figures:

- Per-paper alignment matrix.
- Tsuyama 2022 dual-wavelength / particle-class anchor panel.

### Result 7: Validation artifact roadmap

Message:

> The path from relative audit to calibrated prediction is explicit and finite.

Figure:

- Evidence ladder: surrogate -> bounded trace -> measured artifact -> calibrated claim.

Table:

| Artifact | Current gap | Claim it could unlock | Failure consequence |
|---|---|---|---|

## 5.4 Discussion

### 5.4.1 Why 660 is the conservative main route

Discuss:

- stable route role;
- governance after width-prior risk;
- bounded trace behavior;
- available evidence across lenses;
- not a calibrated optimum.

### 5.4.2 Why 404 remains valuable

Discuss:

- high shortwave sensitivity;
- thermal / photothermal / readout stress test;
- sidecar value;
- why it cannot replace main route yet.

### 5.4.3 Why 532/488 belong in the paper

Discuss:

- Tsuyama dual-wavelength anchors;
- Au / Ag trend comparison;
- controls rather than main route candidates.

### 5.4.4 Why dual-lens parity matters

Discuss:

- engineering lens answers route choice;
- lens B answers both B1 Tsuyama-anchor target-fitting and B2 frozen-B-lens EV biomimetic recommendation filtering;
- neither replaces the other.

### 5.4.5 What would change the conclusion

Potential conclusion-changing artifacts:

- measured blank/BFP reference differs strongly from surrogate;
- standard-particle transfer reverses route stability;
- shortwave detector throughput or thermal cross-talk changes 404 status;
- full-wave spot checks invalidate reference phase / BFP operator assumptions;
- EV sample characterization shows particle model mismatch dominates.

## 5.5 Limitations

Must state clearly:

1. No measured blank trace.
2. No measured BFP / slit / pinhole detector operator.
3. No standard-particle transfer calibration.
4. No detector voltage / photon / current unit chain.
5. No absolute SNR / LOD / concentration claim.
6. EV model is simplified and not biological-specific.
7. Selected-annulus is an event-position / analysis-window lens, not automatically an optical annulus.
8. Full-wave channel Green tensor not globally solved.
9. Noise/readout is scenario-bound surrogate.
10. Tsuyama alignment is not calibrated reproduction.

---

## 6. Main figure plan

### Figure 1: Claim boundary + observation-chain overview

Panels:

- A: claim boundary card.
- B: full observation-chain workflow.
- C: evidence-level ladder.

Purpose:

- Establish honesty and method boundary immediately.

### Figure 2: Core physical computation chain

Panels:

- A: Mie / intrinsic scattering.
- B: detector operator / BFP / slit / ROI surrogate.
- C: reference + scattering interference.
- D: readout/noise/pulse extraction.

Purpose:

- Show why route selection is not a one-variable problem.

### Figure 3: Four-wavelength mechanism decomposition

Panels:

- A: `Csca` relative trend.
- B: `sqrt(Csca)` / field-amplitude trend.
- C: reference/cross-term/peak trend.
- D: transit / readout / detection trend.

Purpose:

- Explain 404 vs 660 tension.

### Figure 4: Route-role decision matrix

Panels:

- A: 660 main routes.
- B: 404 sidecar/probe.
- C: 532/488 controls.
- D: forbidden interpretations.

Purpose:

- Make route roles unambiguous.

### Figure 5: Wavelength x geometry heatmap with gap overlay

Panels:

- A: strict data cells.
- B: route-level cells.
- C: gaps / no direct line.
- D: governance overlay.

Purpose:

- Prevent readers from treating missing cells as zero or route-level evidence as strict variable isolation.

### Figure 6: Dual-lens reconciliation and validation roadmap

Panels:

- A: lens A vs lens B purpose table.
- B: agreement / disagreement matrix.
- C: minimum artifact package.
- D: route-status after each artifact.

Purpose:

- Tie results to next-step experimental program.

---

## 7. Supplementary figure / table plan

| Supplement | Content | Source |
|---|---|---|
| Supplementary Fig. 1 | Full module-level code map | `nodi_simulator/` |
| Supplementary Fig. 2 | Unit and limiting-case tests | `tests/` |
| Supplementary Fig. 3 | Detector-operator variants | `reference_field.py`, detector/operator modules |
| Supplementary Fig. 4 | Noise/readout scenario sensitivity | `configs/realism_v2/`, R5 outputs |
| Supplementary Fig. 5 | Selected-annulus Tsuyama-anchor + EV-application provenance | report 49 / report 71 / report 88 §11 |
| Supplementary Table 1 | Full route ranking table | result artifacts |
| Supplementary Table 2 | Claim-governance vocabulary | configs + report 88 §15 |
| Supplementary Table 3 | Tsuyama per-paper alignment matrix | papers + report 88 §14 |
| Supplementary Table 4 | Validation artifacts and claim unlocks | report 88 §16 |
| Supplementary Table 5 | Strict vs route-level comparison inventory | report 88 appendix F |

---

## 8. Minimum validation package before strong submission

### 8.1 Tier 1: must-have for calibrated-upgrade discussion

| Artifact | Minimum implementation | Why it matters | Claim impact |
|---|---|---|---|
| Blank-channel reference trace | Each wavelength, representative geometries | Tests reference surrogate and blank drift | Could upgrade reference from surrogate to measured |
| BFP/slit/ROI scan | Measured detector operator | Tests shared projection for reference/scattering | Could validate or revise route ranking |
| Standard-particle transfer | Au / PS / silica panel across wavelengths | Converts relative pulse proxy toward physical transfer | Prerequisite for calibrated SNR discussion |
| Detector gain/noise chain | Current/TIA/lock-in/logger characterization | Prevents arbitrary unit confusion | Prerequisite for voltage/current/noise claims |
| Flow / transit validation | Measured velocity / pulse width / residence time | Tests transit-readout coupling | Could alter 404 sidecar interpretation |

### 8.2 Tier 2: needed for EV-specific paper claims

| Artifact | Minimum implementation | Why it matters |
|---|---|---|
| EV size / RI / morphology characterization | NTA + TEM/cryo-TEM + refractive-index proxy | EV is not Au/Ag sphere |
| Contaminant controls | lipoprotein / protein aggregate / vesicle controls | biological specificity blocked without controls |
| Coincidence / blended-pulse audit | concentration ladder + occupancy check | per-event detectability does not equal count rate |
| Fouling / adsorption / PEG-layer check | time-course blank and particle response | channel surface changes route stability |

### 8.3 Tier 3: numerical physics upgrade

| Study | Minimum implementation | Why it matters |
|---|---|---|
| Full-wave blank-channel field | 6-12 representative geometries | Tests reference field surrogate |
| Particle-in-channel Green tensor spot checks | main 660 + 404 sidecar + controls | Tests wall-modified scattering |
| Vector polarization / high-NA transfer | representative objective / polarization states | Tests scalar projection assumptions |
| Roughness / fabrication background | bounded perturbation sweep | Tests false background and route fragility |

---

## 9. Reviewer-risk checklist

### 9.1 Highest-risk reviewer questions

1. If no measured blank/reference exists, why trust the reference field?
2. If no detector operator is measured, why trust BFP/slit/ROI ranking?
3. If no standard-particle calibration exists, why mention SNR-like quantities?
4. If EVs are heterogeneous, why use spherical EV biomimetic particles?
5. Why does 404 not win if Rayleigh scattering is stronger?
6. What exactly is selected-annulus?
7. How do you separate Tsuyama trend alignment from calibrated reproduction?
8. Can route governance change the conclusion by arbitrary prior choices?
9. Are 532/488 controls or candidates?
10. What one measurement would most likely change the recommendation?

### 9.2 Preemptive answer strategy

| Reviewer concern | Preemptive answer |
|---|---|
| "No measured data" | The paper is a relative audit framework; measured-data upgrade is listed explicitly |
| "Score arbitrary" | Show ablation, gate logic, route-governance table, and strict vs route-level inventory |
| "404 should win" | Show stage waterfall: `Csca` -> field -> peak -> transit/noise/pulse -> governance |
| "Tsuyama calibration?" | Write mechanism/trend alignment only; measured calibration blocked |
| "selected-annulus ambiguity" | Define as analysis lens unless optical operator is explicitly implemented |
| "EV specificity" | Keep EV-like optical route selection separate from biological specificity |

---

## 10. Candidate journal framing

### 10.1 Most compatible journal categories

- optical biosensing methods;
- nanofluidic detection methods;
- computational design audit;
- lab-on-chip instrumentation design;
- single-particle detection simulation methods.

### 10.2 Best-fit manuscript type

Preferred:

```text
Methods / computational framework article
```

Acceptable:

```text
Design-space analysis article
```

Not current:

```text
Experimental validation article
```

### 10.3 Reviewer expectation management

The manuscript should state in the title, abstract, or first page that it is:

- relative;
- audit-oriented;
- pre-experimental or no-measured-data;
- claim-governed.

This is not weakness if stated early. It becomes weakness only if readers discover it after seeing strong route recommendations.

---

## 11. One-day, one-week, one-month paper-prep plan

### 11.1 If only one day

1. Rewrite report 88 opening into paper-style introduction and claim boundary.
2. Create Figure 1 workflow and Figure 4 route-role matrix.
3. Extract four-wavelength role table and validation artifact table.

### 11.2 If one week

1. Generate all six main figure drafts.
2. Convert report 88 §2 / §10 / §11 / §15 / §16 into manuscript outline.
3. Write Methods skeleton with formula/code/file crosswalk.
4. Build supplementary provenance tables.
5. Run full tests and record verification.

### 11.3 If one month

1. Add measured or simulated validation artifacts for at least Tier 1 partial upgrade.
2. Add full-wave spot-check panel if feasible.
3. Prepare polished manuscript draft.
4. Run external review focused on overclaim and figure clarity.
5. Decide target journal / article type.

---

## 12. Current recommendation

Do not start by writing the full paper. Start by producing three durable artifacts:

1. **Figure 1 observation-chain workflow**;
2. **Figure 4 route-role decision matrix**;
3. **Table: validation artifact -> claim unlock / blocker**.

Once those are stable, the manuscript story will become much easier to write, because every section can refer back to those three artifacts.

The paper should make a virtue of being claim-governed:

```text
This work is valuable because it tells us what can be ranked before calibration,
what cannot be claimed before calibration, and which measurements most efficiently
turn a relative route audit into a calibrated instrument model.
```
