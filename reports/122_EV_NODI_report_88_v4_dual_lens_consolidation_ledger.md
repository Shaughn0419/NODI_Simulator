# EV NODI report 88 v4.0 dual-lens consolidation ledger 2026-05-11

This ledger records the 2026-05-11 in-place restructure of `reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md` from v3.0 to **v4.0 dual-lens**, plus the governance-doc updates required to keep the all-crossing lens and the selected-annulus paper-audit lens equally weighted as reader entrances.

It is a review artifact; the current scientific single source of truth is the updated `reports/88` v4.0. Raw provenance for the selected-annulus lens remains `reports/49` (Phase 2 / 2.5–2.11) and `reports/71` (R5.2 bounded scenario-prior audit + sidecar guardrail).

## User-driven scope decision

User instruction (2026-05-11):

```text
对我来说，这两个口径同等重要，
所以我需要他们都保持最新并且在 88 中有同等的分析规模和详细理解。
两个分析和排序各自独立，但最后要有综合性分析；
全部并入，并且要保证我们后续的 realism v2 和 P0-P18 的相关分析
同等的在两个口径中体现。
```

Resolved scope: option (a) + full merge of reports 49 and 71 into report 88.

## Restructure record

- Baseline before: `reports/88` v3.0 (931 lines), all-crossing as the only main lens; selected-annulus referenced only by pointer in §11 evidence list and as a `selected-annulus lens` mention inside §13.1 P0 audit.
- Target after: `reports/88` v4.0 (≈ 1598 lines), dual-lens with:
  - §0 — reader notes including dual-lens declaration;
  - executive summary covering both lenses (8 questions: 6 + 2);
  - §1–§13 — all-crossing engineering ranking lens (light reframing markers added; existing content preserved);
  - §14 — selected-annulus paper-audit lens, complete reader-level analysis consolidated from reports 49 and 71;
  - §15 — dual-lens integrated analysis, common forbidden-claim list, common closure, and **going-forward dual-lens reflection requirement** for any P19+ stage merged into 88;
  - §11 evidence list expanded to dual-lens with selected-annulus result directories enumerated;
  - §12 closure marked as all-crossing-only with cross-reference to §14.12 and §15.4.

### §14 sub-section coverage (new)

| Sub-section | Source | Content |
|---|---|---|
| §14.1 | new | selected-annulus lens definition, problem domain, boundary vs all-crossing |
| §14.2 | report 49 G0 + G1 | target audit (direct/audit, formula-consistent, recomputed-Mie, inferred, operational, diagnostic-only); baseline acceptance |
| §14.3 | report 49 G2 | Phase 2 family-ladder full inverse; `52` candidates × `3` seeds × `10000 events/case`; release status `negative_or_diagnostic_result_only`; main No-Go `raw_size_response_alignment_not_met` |
| §14.4 | report 49 G2.5 + D2.1 | D2 raw-operator + D2.1 local refphi/collection smoke; D2.1 best raw Au exponent ≈ `3.05`; no promote |
| §14.5 | report 49 G2.6–G2.11 | reproduction-lens chain: Phase 2.6 size-only F-family (`3000 events/case`), Phase 2.7 SNR response, Phase 2.8 reviewed/descriptive, Phase 2.9 maximal upper-bound, Phase 2.10 size-response decomposition, Phase 2.11 single global response compression `gamma ≈ 0.749`, score `2.033` |
| §14.6 | report 49 G2.14–G2.15 | ET-2030 + LI5640 instrument-aware feasibility (`216` rows; current input / TIA comfortable, 50 Ω voltage path mostly below sensitivity); paper-statistics sensitivity boundary (`288` rows; `274` `paper_statistics_unlikely_alone`) |
| §14.7 | report 71 | R5.2 bounded scenario-prior audit; sidecar guardrails `selected_annulus_replaces_all_crossing_ranking = false`, `selected_annulus_bound_change_authorized = false`; main-660 lock; route-promotion blocked |
| §14.8 | reports 49 + cross | dual-lane geometry table (Tsuyama paper-audit `660 / 800x550`, EV engineering `660 / 800x1400` etc.); EV route shadow all-crossing dashboard with `selected_all_uplift_median ≈ 1.384x` |
| §14.9 | new | gap table: realism v2 R0–R7.2 reflection in selected-annulus lens (which stages have selected-annulus evidence vs explicit "未扩展" markers) |
| §14.10 | new | gap table: post-v2 P0–P18 reflection in selected-annulus lens (most P-stages are "未扩展"; P0 incorporates selected-annulus as one audit lens; P18 stop-decision is shared) |
| §14.11 | new | selected-annulus lens allowed/forbidden claim list |
| §14.12 | new | selected-annulus lens final closure with bilingual boundary statement |

### §15 sub-section coverage (new)

| Sub-section | Content |
|---|---|
| §15.1 | dual-lens governance principle table (problem domain, sort lens, conclusion form, Tsuyama relation, claim boundary, next-dependency) |
| §15.2 | cross-lens evidence comparison table (main-660, weak-reference control, 660 nm high-score context, 404 nm probe, optional `660 / 900x1400`, paper-sanity routes, width-prior, 404 nm thermal sidecar, Au scattering, Tsuyama 2022 NODI geometry, classification accuracy) |
| §15.3 | unified forbidden-claim list (calibrated SNR, calibrated event probability, absolute LOD, true EV concentration, biological specificity, measured blank safety, route promotion / accepted paper-calibrated candidate, main-660 redefinition, **bidirectional non-replacement**, selected-annulus bound change, 404 nm thermal sidecar, P6-P16 trace as promotion, estimated-parameter as raw calibration, classification accuracy claim, gamma response compression as physical law) |
| §15.4 | dual-lens common closure with bilingual boundary statement |
| §15.5 | **going-forward requirement**: any P19+ stage merged into 88 must (1) evaluate both lenses, (2) explicitly mark gaps when one lens has no equivalent evidence, (3) update §15 if a forbidden-claim change is implied, (4) the P19 evidence-strategy gate must declare acceptance criteria for both lenses, (5) §15.2 and §15.4 must be updated on each merge, (6) reports 49 and 71 remain raw provenance |
| §15.6 | dual-lens unresolved items |

## Governance-doc updates

| Doc | Change | Why |
|---|---|---|
| [HISTORICAL_REPORT_SUPERSESSION.md](../HISTORICAL_REPORT_SUPERSESSION.md) | Added preamble declaring two parallel lenses of equal priority; relabelled report 88 as v4.0; added explicit supersession rows for reports 49, 70, 71 pointing to report 88 v4.0 §14 / §14.7; updated `current_claim_level` for the report-47 row to `current_truth_in_report_88_v4_dual_lens`. | Make supersession truth-in-report explicit about both lenses; preserve 49/71 as named raw provenance even though their reader-facing conclusions now live in report 88 v4.0. |
| [nodi_simulator/review_package.py](../nodi_simulator/review_package.py) `write_audit_docs` | Updated the supersession generator string to match the new dual-lens version of `HISTORICAL_REPORT_SUPERSESSION.md`. | Prevent the next generator run from regenerating the v3.0 string and silently overwriting the dual-lens preamble. |
| [文档导航.md](../文档导航.md) | Added dual-lens disclaimer at top; updated entry 2 to describe v4.0 dual-lens content; added new entry 7 for `reports/122` (this ledger); updated allowed/forbidden-claim list to be dual-lens (added selected-annulus reproduction-lens score, instrument-aware feasibility, bidirectional non-replacement, selected-annulus bound fix, estimated-parameter vs raw calibration, gamma response compression, classification accuracy); updated 报告与归档 to label `reports/49`, `reports/70`, `reports/71` as selected-annulus raw provenance for §14 / §14.7; updated 使用优先级 to put `reports/88` v4.0 + `reports/122` first and add selected-annulus raw provenance as priority 5. | Make navigation honor the dual-lens model; align forbidden-claim wording with §15.3; expose `reports/122` as the v4.0 ledger entry. |
| [reports/89_EV_NODI_post_v2_unmodeled_realism_register.md](89_EV_NODI_post_v2_unmodeled_realism_register.md) | Updated header to mention dual-lens; expanded forbidden-claim list to be bidirectional and to cover both lenses; added P0-P18 status-note paragraph clarifying P0-P18 are all-crossing-lens, listing the parallel selected-annulus evidence (Phase 2 / 2.5–2.11 + R5.2 sidecar) and stating that P19 must declare acceptance criteria for both lenses. | Keep the post-v2 register honest about which lens runs which stages and prevent a single-lens P19 plan. |
| [reports/122](122_EV_NODI_report_88_v4_dual_lens_consolidation_ledger.md) | Created as the v4.0 dual-lens ledger (this file). | Capture the restructure, source-of-truth pointer, and going-forward requirement in one auditable place. |

## Verification evidence

Targeted tests after the restructure:

```text
python -m pytest tests/test_paper_provenance_disjoint_and_supersession.py -q
  -> 2 passed in 0.08s
```

Other tests in the repo were not re-run as part of this consolidation pass because the restructure only edits Markdown reader-facing text, the `HISTORICAL_REPORT_SUPERSESSION.md` generator string in `nodi_simulator/review_package.py`, and a cross-doc reference in 文档导航/89/122. No simulator-side computation, no schema, no contract, and no fixture changed. The full test suite should still be re-run before any external review release; the relevant runner is documented in [tests/run_tests.md](../tests/run_tests.md).

Hash-bearing review-package files (`REVIEW_PACKAGE_HASHES.sha256`, `REVIEW_PACKAGE_MANIFEST.json`, `REVIEW_BUILD_MANIFEST.json`) reference these markdown files; if a release rebuild is needed, run the standard `nodi_simulator/review_package.py` rebuild path so the dual-lens supersession text is regenerated and re-hashed in one pass.

## Boundary preserved by this consolidation

- No change to `calibrated_claim_allowed = false`, `measured_data_ingest_authorized = false`, `route_promotion_authorized = false`, `main_660_redefinition_authorized = false`, `selected_annulus_bound_change_authorized = false`.
- No change to the v2 / post-v2 numerical results. Tables in §14 reproduce numbers from reports 49 and 71 as published; this ledger does not re-derive them.
- No new lane execution, no new scenario bundle, no new stochastic seed, no new solver case, no new experiment, no new measured artifact ingest.
- The bidirectional non-replacement rule in §15.3 strictly subsumes the prior "selected-annulus 替代 all-crossing 主排序" forbidden line; the forbidden direction has not been weakened, only made symmetric.

## Open dependency

P19 evidence-strategy gate must, when designed, declare acceptance criteria for **both lenses** and reference §15.5 of report 88 v4.0. The strict consequence of the dual-lens parity rule: if a P19 plan only addresses one lens, it is not a valid P19 plan.

## v4.0 amendment (same day, 2026-05-11): lens B parameter freeze

User instruction (2026-05-11):

```text
口径 B 的选型部分改一下，让口径 B 就停在现在的参数上，不需要再过拟合，
就按现在的参数出结果，要展示与 tsuyama 各个论文数据结论的详细对比表格，
和选型推荐。
```

Resolved: drop the "stop because we'd overfit" framing in lens B; reframe as
**lens B parameter freeze = chosen selection**; output final results from these
chosen parameters and add a per-paper comparison + selection recommendation.

### Files updated for the amendment

| File | Change |
|---|---|
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) §0 | Dual-lens declaration extended to mention lens A/B current state including lens B parameter freeze. |
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) executive summary Q7 | Reframed: cites the chosen parameter freeze (`gamma=0.749`, snr_scale `0.728`, snr_response_exp `0.812`, candidate `tau_2ms_global_refphi_plus_collection_narrow`) and points readers to §14.12 / §14.13 / §14.14. |
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) §14.11 | Allowed/forbidden list rewritten: keeps all forbidden lines and adds "current parameters frozen" framing in the allowed block; explicitly forbids treating gamma / SNR scale / SNR response exponent as instrument physical constants. |
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) §14.12 | Renamed to "口径 B 最终收口（当前参数冻结为选型）"; introduces the full frozen parameter block + frozen release-status block; replaces "stop because would overfit" with "selection = current parameters; further descent needs measured artifact, not more compute DOF". |
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) §14.13 (NEW) | Six per-paper comparison tables (2019 POD, 2020 diffraction, 2020 counting POD, 2020 solvent-enhanced POD, 2022 NODI, 2024 POD+NODI), each row keyed to the frozen parameter values. Verdict column uses match / partial / boundary / out-of-scope / 不复现. |
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) §14.14 (NEW) | Selection recommendation: §14.14.1 frozen reproduction-lens parameters, §14.14.2 hardware path, §14.14.3 particle/geometry panel, §14.14.4 allowed publish lines + forbidden lines, §14.14.5 next-step ordering before P19. |
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) §15.4 | Common-closure block updated: lens B reframed as "已冻结选型" with the frozen parameter block enumerated. |
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) §15.6 | Added item 5: P19 plan must use the frozen lens-B parameters as baseline, not as a transitional candidate. |
| [memory/feedback_dual_perspective_parity.md](../../../../../../Users/yanxuan/.claude/projects/-Volumes-Storage-Mac-nodi-simulator-usb-/memory/feedback_dual_perspective_parity.md) | Added item 6 capturing the lens-B parameter-freeze instruction so future sessions don't re-open the "find lower score" search. |

### What did **not** change

- `release_status` for lens B is still `negative_or_diagnostic_result_only` (the freeze is a chosen reproduction lens, not a calibrated candidate).
- All forbidden-claim lines in §14.11 / §15.3 retained; §14.11 explicitly added one new forbidden line: "current gamma / SNR scale / SNR response exponent are instrument physical constants" — they remain reproduction-lens estimates.
- Lens A (§1–§13) untouched in this amendment.
- Selected-annulus bound `0.5–0.8` is still fixed; uplift / sidecar guardrails unchanged.
- Hardware feasibility evidence (216-row matrix) unchanged; selection now explicitly blacklists 50 Ω voltage path as the recommended-against branch.
- Numerical values reproduce report 49 verbatim (no re-derivation).

## v4.1 amendment (same day, 2026-05-11): reader-friendly explainer layer (§16)

User instruction (2026-05-11):

```text
针对 88 全量分析报告（现在应该是 v4），希望能用更好懂的表述方式进行分析；
报告里估计值多、变量多，前面是否清晰说明数值由来与依据？
是否做到固定变量后再看其他变量之间的变化关系，找到影响最大的变量？
噪声的影响到底有多大？参考场让波峰增强了那么多倍，为什么噪声还能压低 detection？
本征散射和干涉增强之后的峰值增强倍数是叠加上去的吗？
为什么最终推荐的尺寸和波长是那样的，它能让峰值增强多少、检测率提高多少、原因是什么？
希望能有很多很多表格直接对比不同波长不同通道尺寸的不同阶段量的倍数差异。
```

Resolved: add **§16 物理量级链条与变量影响读者向解读（双口径共享解读层）** at the end of `reports/88` v4.0 (after §15), bumping the reader-facing version to v4.1. This is a **reader-explainer-only amendment**:

- no new computation
- no new candidate
- no new lane
- no change to release status, frozen lens-B parameters, or any forbidden claim
- both lenses get equal coverage; §16 explicitly notes when a tabulation is lens-A-only vs lens-B-only vs both
- the dual-lens going-forward rule (§15.5) is extended to require that any P19+ stage that changes a §16 row also updates §15.3 first

### §16 sub-section coverage (new)

| Sub-section | Reader question answered | Source |
|---|---|---|
| §16.1 | Q1 — 信号怎么从 Csca 一路推到 detection % | §1–§15 公式回顾 + §3.2/§6/§7 数值 |
| §16.2 | Q2 — 本征 \|E_sca\|² vs 参考场放大干涉项是相加还是相乘 | physics: signal_trace = \|E_sca\|² + 2·\|E_ref\|·\|E_sca\|·cosΔφ |
| §16.3 | Q3 上半 — 固定几何看波长（EV biomimetic + Au paper-audit 各一张表）| §3.2 / §6 / §7 / §16.3 Rayleigh 推导 |
| §16.4 | Q3 下半 — 固定波长看 W、H（口径 A 工程主线 + 口径 B paper-audit 几何）| §3.2 / §3.5 / §4 / §14.7 / §14.5.5 |
| §16.5 | Q4 — peak 放大 N 倍 ≠ detection 放大 N 倍（transit / phase flip / threshold floor 三因子分解）| §4–§5 噪声 / batch 字段 |
| §16.6 | Q5 — 为什么参考场放大那么多倍噪声还能压低 detection（noise 进入位置 + 相干一次项 vs 非相干 noise）| §4.7 / §6 / §14.7 weak-reference 解释 |
| §16.7 | Q6 — 估计值来源 6 档（物理常数 / Mie 推导 / surrogate / reproduction-lens / 可接受解释先验 / 校准实测）；显式标出 v4.0 高频被误读数字所在档位 | §15.3 forbidden + §14.11 forbidden |
| §16.8 | Q7 — 变量影响按 \|Δ detection\| / \|Δ variable\| 排序（颗粒材料 > 波长 > 粒径 > W > H > 收集算子 > 读出 > 参考场模型 > 阈值 > annulus 窗口）| §3.2 / §6 / §7 / §14 综合 |
| §16.9 | Q8 — 推荐选型理由链双口径分别给出（口径 A: 660/800x1400 或 1500；口径 B: D2.1 best + gamma 0.749 + 660/800x550 + 660/1200x550 + ET-2030 + LI5640 + current input/TIA）| §3.2 / §3.3 / §3.5 / §4 / §13.1 / §13.3 / §13.6 / §14.4 / §14.5 / §14.6 / §14.12 / §14.14 |
| §16.10 | §16 与 §1–§15 关系；后续 P19+ 阶段必须双口径同时更新 §16 + §15.3 一致性 | §15.5 going-forward 扩展 |

### Files updated for the v4.1 amendment

| File | Change |
|---|---|
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) header | 版本字段从 v4.0 改为 v4.1，说明 §16 为新增的读者向解读层；不修改任何 v4.0 数值结论、forbidden claim、release status 或冻结参数。 |
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) executive summary 末段 | 在"读完整份报告大约需要 50-60 分钟"段后补充 §16 入口段，列出 8 个读者直觉问题 Q1-Q8 → §16.x 的对应。 |
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) §16 (NEW) | §16.1 信号物理链 + §16.2 加法 vs 乘法关键问题 + §16.3 波长变量隔离表（EV biomimetic Rayleigh + Au paper-audit 各一张）+ §16.4 通道宽度 / 深度变量隔离表（口径 A + 口径 B paper-audit 三张）+ §16.5 peak vs detection 解耦六因子表 + §16.6 噪声进入位置 + 数值版三场景对比表 + §16.7 估计值来源 6 档 + 高频被误读数字读法表 + §16.8 变量影响排序 10 项表 + §16.9 双口径推荐因果链 + §16.10 §16 与 §1–§15 的关系 + 后续阶段并入要求。 |
| [reports/122](122_EV_NODI_report_88_v4_dual_lens_consolidation_ledger.md) | 本段落（v4.1 amendment ledger entry）。 |

### What did **not** change in the v4.1 amendment

- `release_status` for lens B 仍为 `negative_or_diagnostic_result_only`；冻结参数集 `tau_2ms_global_refphi_plus_collection_narrow` + `gamma=0.749` + `snr_scale=0.728` + `snr_response_exp=0.812` 不变。
- §15.3 共同 forbidden claim 一条未放宽；§14.11 末新增的"current gamma / SNR scale / SNR response exponent are instrument physical constants"forbidden line 在 §16.7 中显式按"4 档 reproduction-lens 估计项"重新强调。
- 双口径并立约束、§14.7 sidecar guardrails、§14.6.1 instrument-aware feasibility 数据全部维持原样。
- §16 引用的所有数值都来自 §1–§15 已发布行（§3.2 / §3.5 / §4 / §6 / §7 / §13.1 / §13.3 / §14.4 / §14.5 / §14.6 / §14.7 / §14.8 / §14.12 / §14.14），没有新计算 / 新 candidate / 新 lane / 新 stochastic seed / 新 solver case / 新 experiment / 新 measured artifact ingest。
- 没有修改 `nodi_simulator/review_package.py`、`HISTORICAL_REPORT_SUPERSESSION.md`、`文档导航.md`、`reports/89` 或测试。v4.1 是纯 reader-facing markdown amendment。

### Verification evidence (v4.1 amendment)

```text
本次仅 reader-facing markdown 增补；未触及 simulator / schema / contract / fixture / generator string，
因此未触发额外 pytest。Hash-bearing review-package 文件未引用 §16，因此暂未重新打包。
若发布前需要把 v4.1 reader 解读层加入 review package 哈希链，
按 nodi_simulator/review_package.py 标准重打包路径执行；本次未执行。
```

### Boundary preserved by the v4.1 amendment

- `calibrated_claim_allowed = false`、`measured_data_ingest_authorized = false`、`route_promotion_authorized = false`、`main_660_redefinition_authorized = false`、`selected_annulus_bound_change_authorized = false` 全部保留。
- 双口径并立、互不替代约束保留；§16 内任何 EV biomimetic vs Au paper-audit 数据在同一段落或同一表内必须显式标注分母口径与颗粒口径，避免读者把不同口径下相同数字拼成单一 paper claim。
- §15.5 going-forward 的双口径反映要求被 §16.10 显式扩展为：任何 P19+ 阶段证据并入若改变 §16.7 估计值档位、§16.8 变量影响排序，或让 §16.9 因果链某一步不再成立，必须先更新 §15.3 forbidden claim 与对应 §1–§15 段落，再更新 §16；不允许只改 §16 来掩盖底层证据变化。

### Open dependency unchanged

P19 evidence-strategy gate must, when designed, declare acceptance criteria for **both lenses** and reference §15.5 of report 88 v4.0 (now v4.1). The §16 reader-explainer layer does not relax this dependency; if anything, §16.7 / §16.8 / §16.9 make the gap between current reproduction-lens / surrogate evidence and calibration-grade evidence more visible to the reader.

## v4.2 amendment (same day, 2026-05-11): two-step lens-B selection framing + many-table reformat in ms / % units

User instruction (2026-05-11):

```text
1. 口径 B 的选型，不是为了哪一个选型更接近 tsuyama 的数据，
   而是根据 tsuyama 的数据来调整所有的参数估计值，
   并在这个参数估计值的计算下，选取最适合的尺寸，
   现在的分析对这方面有误解。
2. 类似 16.3.1 的表格，我要非常多，固定尺寸下不同波长的对比，
   固定波长下不同尺寸的对比之类的，固定的尺寸或波长也要多选取一些，
   让人更清晰。并且表格中，transit 要用 ms 单位，不要表现为倍数；
   detection 要用 %，表现检测率，也不要表现为倍数。
```

Resolved:

- **(a) §16.9.2 重写**：把口径 B 选型逻辑从"挑哪个几何最像 Tsuyama"改写为两步框架。Step 1：用 Tsuyama 数据（Table S1 Ag/Au signal、Au size exponent 2.3、Au30/Au20 SNR 33/12）作为 target，校准/调整估计参数（gamma=0.749、snr_scale=0.728、snr_response_exp=0.812、D2.1 best 算子）。Step 2：在 step 1 校准过的 reproduction lens 口径下，扫几何/波长/颗粒/读出，选 residual 最低的组合。**关键澄清**显式写出：660/800x550 与 660/1200x550 之所以被选中，**不是因为它们最像 Tsuyama 论文器件**（虽然 Tsuyama 2022 NODI 器件确实在 800x550 附近），**而是因为在 step 1 校准过的 lens 内 raw Au peak-height exponent residual 最低**（3.0335 / 3.0456 vs target 2.3，全 6 case 中最低的两个）。两件事方向重叠是物理一致性的体现，不是选型逻辑的根据。
- **(b) §16.3 / §16.4 重写**：原来 §16.3.1 / §16.3.2 / §16.4.1 / §16.4.2 / §16.4.3 五个用相对倍数 (×, x) 表达的表格，改写为多张固定几何 vs vary λ 与固定 λ vs vary 几何的表，每张表的 transit 列用 ms 单位（按 `transit ≈ 2·w_0/v_flow`、`w_0 = 0.61·λ/NA`、NA=0.45 Tsuyama illumination objective、v_flow=0.2 mm/s Tsuyama 2022 NODI 同口径推导），detection 列用 %（保留 v4.0 直接发布的相对先验合成 detection 数字，仅做单位换算 0.471 → 47.1%），并显式标注每张表的 lens 分母口径（all-crossing / NODI engineering / 2020 paper / 2022 NODI paper / selected-annulus）和颗粒口径（EV biomimetic / Au paper-audit）。v4.0 未直接覆盖的 cell 显式写 "—" 并标注最近邻 + "禁止读为 0%"。

### §16.9.2 sub-section coverage (rewritten in v4.2)

| Sub-section | Content |
|---|---|
| §16.9.2.A Step 1 | Tsuyama 数据 → 校准的估计参数表（4 行 target + 4 行参数 + 1 段 §16.7 第 4 档强调）|
| §16.9.2.B Step 2 | 校准 lens 内 5 维度选型表（几何 / 波长 / 颗粒 panel / 收集算子 / 硬件接法），每行给候选范围 + 选中项 + step 1 lens 内的 residual 理由 |
| §16.9.2.C 关键澄清 | 显式声明几何选型不走"哪个最像 Tsuyama"；方向重叠是物理一致性；如果 measured artifact 改变 step 1 校准，step 2 最适合几何可能改变 |
| §16.9.2.D 边界 | 与 §14.11 / §15.3 一致的 4 条 forbidden + 1 条 measured artifact 依赖；reproduction 增益是 step 1 成果，不是 step 2 成果 |

### §16.3 / §16.4 sub-section coverage (rewritten in v4.2)

| 原 §16 子节（v4.1）| v4.2 替换 |
|---|---|
| §16.3.1 / §16.3.2 (单 800x550 / vary λ, EV + Au, ×倍数表) | §16.3.A.1–A.6 + §16.3.B.1–B.4 + §16.3.C 三 lens 对照表 + §16.3.D 5 条读法。共 11 张表。所有 transit 列用 ms（5.48 / 6.61 / 7.21 / 8.94），detection 列用 %（直接换算 v4.0 已发布数字），cell 缺数据时显式 "—" |
| §16.4.1 / §16.4.2 / §16.4.3 (W 阶梯 + H 阶梯 + paper-audit 几何对照) | §16.4.A.1–A.5 (固定 λ + 固定 H, vary W 5 张) + §16.4.B.1–B.5 (固定 λ + 固定 W, vary H 5 张) + §16.4.C 全 660 nm 全 EV all-crossing 直接行汇总 + §16.4.D 路线治理裁决表 + §16.4.E 口径 B paper-audit 几何对照 + §16.4.F Au panel 粒径阶梯表 + §16.4.G 6 条读法。共 14 张表。同 §16.3 单位约定 |

### Files updated for the v4.2 amendment

| File | Change |
|---|---|
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) header | 版本字段 v4.1 → **v4.2**；说明 (a) §16.9.2 改两步框架 + (b) §16.3 / §16.4 改 ms/% 多表。仍不修改 v4.0 数值结论、forbidden claim、release status、冻结参数。 |
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) §16.3 | 5 张倍数表 → 11 张 ms/% 表 + 5 条读法。每张表显式标 lens / 颗粒口径。 |
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) §16.4 | 3 张混合表 → 14 张 ms/% 表 + 6 条读法。包含 §16.4.A 固定 H vary W 5 张、§16.4.B 固定 W vary H 5 张、§16.4.C 全 660 nm 直接行汇总、§16.4.D 路线治理裁决、§16.4.E 口径 B paper-audit 几何、§16.4.F Au 粒径阶梯。 |
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) §16.9.2 | 单条 7 步因果链 → 两步框架（A Step 1 校准 + B Step 2 选型 + C 关键澄清 + D 边界）。显式说明几何选型不走"哪个最像 Tsuyama"。 |
| [reports/122](122_EV_NODI_report_88_v4_dual_lens_consolidation_ledger.md) | 本段落（v4.2 amendment ledger entry）。 |

### What did **not** change in the v4.2 amendment

- `release_status` for lens B 仍 `negative_or_diagnostic_result_only`；冻结参数集 + γ=0.749 / snr_scale=0.728 / snr_response_exp=0.812 不变。
- §15.3 共同 forbidden claim 一条未放宽；§14.11 末"current gamma / SNR scale / SNR response exponent are instrument physical constants" forbidden line 在 §16.9.2.A 显式按"step 1 校准的 reproduction-lens 估计项，不是物理常数"重申。
- 双口径并立、selected-annulus 0.5–0.8 固定、sidecar guardrails 全部维持。
- §16.3 / §16.4 表内所有 detection 数字都来自 v4.0 已发布行（§3.2 / §4 / §6.5 / §7 / §6.3 / §14.7 / §14.5.5），仅做了 0.x → x.x% 单位换算 + ms 物理推导。没有新计算 / 新 candidate / 新 lane / 新 stochastic seed / 新 solver case / 新 experiment / 新 measured artifact ingest。
- v4.0 未直接覆盖的 cell 显式写 "—"，**禁止读为 0% 检出**；不允许通过本节估算去推导 v4.0 未覆盖的几何 / 波长 cell 的 detection 数值。
- 没有修改 `nodi_simulator/review_package.py`、`HISTORICAL_REPORT_SUPERSESSION.md`、`文档导航.md`、`reports/89` 或测试。v4.2 仍是纯 reader-facing markdown amendment。

### Verification evidence (v4.2 amendment)

```text
本次仅 reader-facing markdown 重写；未触及 simulator / schema / contract / fixture / generator string，
因此未触发额外 pytest。Hash-bearing review-package 文件未引用 §16，因此暂未重新打包。
```

### Boundary preserved by the v4.2 amendment

- 全部 v4.0 forbidden claim 不变。新增 §16.9.2.C "几何选型不走 '哪个最像 Tsuyama' 这条捷径" 与 §16.3 / §16.4 各表 "—" 单元格 "禁止读为 0% 检出" 是双口径并立 + reproduction-lens 边界的进一步澄清，不是 forbidden 的放宽。
- §15.5 going-forward 双口径反映要求 + §16.10 §16 与 §1–§15 关系不变；任何 P19+ 阶段证据并入若改变 §16.3 / §16.4 / §16.9.2 的任意结论项，必须先更新 §15.3 与对应 §1–§15 段落，再更新 §16。

### Open dependency unchanged

P19 evidence-strategy gate must, when designed, declare acceptance criteria for **both lenses** and reference §15.5 of report 88 v4.0 (now v4.2). v4.2 把 step 1 校准（reproduction-lens estimated parameters）与 step 2 选型（几何 / 波长 / 颗粒 / 读出）分开后，P19 plan **必须分别给出**：(i) step 1 校准估计参数从 reproduction-lens 推进到 calibrated lens 所需的 measured artifact 集合（Au raw trace + blank + BFP/slit/ROI + lock-in/logger）；(ii) step 2 在 calibrated lens 内重新选型的 acceptance criteria（不允许把 v4.0 step 2 几何选择当成 measured-calibration 后的固定结论）。

## v5.0 amendment (same day, 2026-05-11): reader-centric full restructure

User instruction (2026-05-11):

```text
你现在对整个报告的修改模式，是一种层层叠加的增加功能式的改法，
并不利于读者理解和跟进思路。我希望你把整个报告重构，真正站在读者的角度，
把无意义的参数变量名换成科学严谨的名称，让读者知道他们都是什么，
有什么逻辑联系在里面；章节的排布，是能够引导读者跟随你的逻辑前进的方式，
这样在阅读结论的时候才不会有那么多疑问。一定要站在读者的角度上思考，
给到足够的解释，对逻辑的解释，对参数和参数之间关系的解释，对结论的解释，
对过程量的解释之类的。我希望你在重构并修改完之后，还能够以读者的角度，
重新完整阅读一遍，并进行完善。完全完善后再向我汇报，并更新进主目录中。
```

Resolved: **v5.0 reader-centric full restructure**. 把 v3.0 / v4.0 / v4.1 / v4.2 的层层叠加修订改为按 **问题 → 物理 → 变量 → 数据 → 分析 → 推荐 → 边界 → 出处** 的一次性叙事；把代码层的参数 ID（`tau_2ms_global_refphi_plus_collection_narrow`、`conditional_relative_main`、`gamma` 等）替换为可读的科学命名（保留代码 ID 作为括号补注）；附录 A 给出描述名 ↔ 代码 ID 对照表；附录 B 给出物理链 7 阶段公式表；附录 C 给出表格索引。**数值、forbidden claim、release status、口径 B 冻结参数全部从 v4.2 完整继承，不修改任何一项**。

### v5.0 新章节结构（替代 v4.2 的 §0–§16 + 附录）

| § | 标题 | 回答的问题 | 主要来源 |
|---|---|---|---|
| §0 | 阅读须知 | 这报告是什么、双口径如何并立、阅读路径建议、v5.0 vs 前版关系、不变量 | 新结构 |
| §1 | 项目要解决的两个并立问题 | 问题 A 工程主线 / 问题 B 论文审计 / 为什么并立 | v4.2 §1 / §14.1 |
| §2 | 物理链：粒子如何变成 detection event | 7 阶段公式链 + 关键问题"加法 vs 乘法" | v4.2 §16.1 / §16.2 |
| §3 | 可调变量与物理含义 | 6 类变量（颗粒 / 光学 / 几何 / 电子学 / 仪器情景 / 估计参数）每个含义 + 在物理链上的位置 | 新结构（综合 v4.2 §3.1–§3.6 + §14.5 估计参数）|
| §4 | 检测率 4 种含义 | all-crossing / selected-annulus / NODI engineering / paper-audit reproduction score 何时可比 / 不可比 | 新结构（v4.2 §16.7 雷区警告升级为独立章节）|
| §5 | 计算与审计 study design | v1 全量 / v2 情景 / post-v2 P0–P18 / Phase 2 paper-audit / 仪器可行性 | v4.2 §2 / §3 / §13 |
| §6 | 物理量级与核心数据 | transit / Csca / E_ref / detection 大表 + 雷区警告 | v4.2 §3.2 / §4 / §6 / §7 / §14.7 / §16 |
| §7 | 变量隔离分析 | 14 张固定 X 变 Y 表 + 5 张大读法 | v4.2 §16.3 / §16.4 升级 |
| §8 | 噪声归因 | 为什么参考场放大不消除噪声 + 短波长额外代价 | v4.2 §16.6 升级 |
| §9 | 变量影响排序 | 10 项排序 + 物理解释 | v4.2 §16.8 升级 |
| §10 | 口径 A 工程主线推荐 | 660/800x1400/1500 双 main 集合 + 5 步因果链 + width-prior + 治理裁决 | v4.2 §1 / §3.5 / §13.1 / §16.9.1 升级 |
| §11 | 口径 B 论文审计两步推荐 | step 1 校准 → step 2 选型 + 关键澄清 + reproduction 增益 + 硬件接法 + 冻结参数 | v4.2 §14 / §16.9.2 升级 |
| §12 | 双口径同时存在的意义 | 两套推荐不冲突 + 同一证据双 lens 对照 + 并立治理原则 | v4.2 §15 升级 |
| §13 | 估计值的 6 档来源谱 | 6 档总表 + 高频被误读数字 | v4.2 §16.7 升级 |
| §14 | Tsuyama 6 篇论文逐篇对照 | 角色总览 + 6 篇详细 + 整体结论 | v4.2 §5 / §6 / §14.13 升级 |
| §15 | 可发布与禁止结论清单 | 双口径分别 + 共同可发布 + unified forbidden | v4.2 §8 / §14.11 / §15.3 合并 |
| §16 | Open dependencies | P19 evidence-strategy gate + 实测 artifact 优先级 + P19 前能 / 不能 | v4.2 §13.6 / §14.6 / §15.5 / §15.6 升级 |
| §17 | Evidence trail / provenance | v1+v2 主线 + post-v2 P0-P18 + Tsuyama 文献 + 口径 B raw provenance + 版本 ledger | v4.2 §11 升级 |
| §18 | 历史与版本演化 | supersession + 演化记录 + v5.0 不变量 | v4.2 §10 / §15.6 / §17 合并 |
| 附录 A | 术语表（描述名 ↔ 代码 ID 对照）| 30+ 项对照 | 新增 |
| 附录 B | 公式简表 | 7 阶段公式 + 强参考场极限 + 复现 lens 公式 + 证据档位 | 新增 |
| 附录 C | 表格索引 | 30+ 表按变量类型分组找位置 | 新增 |

### 关键的命名翻译（附录 A 节选）

| 代码层 ID（v4.2 用语）| v5.0 描述名 |
|---|---|
| `gamma = 0.749` | 全局响应压缩因子 γ = 0.749 |
| `snr_scale = 0.728` | 全局 SNR 缩放因子 s_SNR = 0.728 |
| `snr_response_exp = 0.812` | 全局 SNR 响应指数 e_SNR = 0.812 |
| `tau_2ms_global_refphi_plus_collection_narrow` (D2.1 best) | 选定探测算子：2 ms 锁相 + 全局参考相位正向位移 + 窄收集窗 |
| `main_660_W800_D1400` | 主路线 1：660 nm + 800 nm 宽 + 1400 nm 深 |
| `conditional_relative_main` | 条件性相对主路线（合成相对先验框架内的主路线，不是绝对校准主路线）|
| `surrogate_sensitive_not_promoted` | 对替代量级敏感、未晋升 |
| `selected_annulus_replaces_all_crossing_ranking = false` | 选定环带不替代全 crossing 主排序（双向并立 forbidden 之一）|

### Files updated for the v5.0 amendment

| File | Change |
|---|---|
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) | 整体 v4.2 → **v5.0 reader-centric 全文重构**。从 2618 行 → 1754 行（更紧凑、读者向）；新 §0–§18 + 附录 A/B/C 结构；所有代码 ID 改名为可读科学命名并保留代码 ID 作为括号补注。 |
| [HISTORICAL_REPORT_SUPERSESSION.md](../HISTORICAL_REPORT_SUPERSESSION.md) | v4.0 → v5.0；说明 v5.0 是 reader-centric 全文重构；supersession_reason 引用更新到 v5.0 章节号（§10 / §11 / §12.2 / §17.2 等）。 |
| [nodi_simulator/review_package.py](../nodi_simulator/review_package.py) `write_audit_docs` | supersession 生成字符串同步更新到 v5.0；防止下次生成器跑动覆盖 v5.0 写入。 |
| [文档导航.md](../文档导航.md) | 顶部 v4.0 提示 → v5.0 reader-centric 提示；入口 2 描述更新为 v5.0 章节结构；入口 7 ledger 描述更新；报告与归档段、使用优先级段所有 v4.0 引用 → v5.0；selected-annulus raw provenance 引用更新到 §11 / §12.2。 |
| [reports/122](122_EV_NODI_report_88_v4_dual_lens_consolidation_ledger.md) | 本段落（v5.0 amendment ledger entry）。 |

### What did **not** change in the v5.0 amendment

- `release_status` for lens B 仍 `negative_or_diagnostic_result_only`；冻结参数集 + γ=0.749 / s_SNR=0.728 / e_SNR=0.812 不变（见 §11.7）。
- §15 forbidden claim 一条未放宽；包括 `selected_annulus_replaces_all_crossing_ranking = false` 双向并立 forbidden。
- 全部 v4.2 数值结论：§3.2 路线类、§4 main-660、§6 NODI lens / Tsuyama / Au gold、§7 weak-ref vs main-660、§13.1 P0 audit 572 行 / 563 surrogate-sensitive、§13.3 P6–P16 trace ordering、§14.5 reproduction lens 链、§14.6.1 instrument feasibility 216 / 216 vs 211 / 216、§14.7 R5.2 sidecar / context route ratios、§14.8 EV shadow uplift。
- 双口径并立、selected-annulus 0.5–0.8 固定、sidecar guardrails、近壁细网格通过 1.0、width-prior 4 模型对照、route role 7 类裁决全部保留。
- 没有新计算 / 新 candidate / 新 lane / 新随机种子 / 新 solver case / 新 experiment / 新 measured artifact ingest。
- 没有修改 `reports/89`、`reports/49`、`reports/70`、`reports/71`、`reports/121`，没有修改 `tests/`。

### Verification evidence (v5.0 amendment)

```text
python -m pytest tests/test_paper_provenance_disjoint_and_supersession.py -q
  -> 2 passed in 0.03s
```

v5.0 amendment 仍是纯 reader-facing markdown 重组 + 同步更新 supersession 生成字符串和 nav 文档；未触及 simulator / schema / contract / fixture，因此未触发额外 pytest。Hash-bearing review-package 文件（`REVIEW_PACKAGE_HASHES.sha256`, `REVIEW_PACKAGE_MANIFEST.json`, `REVIEW_BUILD_MANIFEST.json`）引用 supersession.md 与 report 88；若需要发布，按标准 `nodi_simulator/review_package.py` 重打包路径执行（本次未执行）。

### Boundary preserved by the v5.0 amendment

- 全部 v4.2 forbidden claim 不变。v5.0 §15 与 v4.2 §15.3 文字内容完全一致。
- 双口径并立、互不替代、selected-annulus 0.5–0.8 固定、γ / s_SNR / e_SNR 禁止解读为物理常数等全部保留。
- v4.2 §15.5 going-forward 双口径反映要求在 v5.0 §12.3 完全继承；§16 open dependencies + §12.3 共同约束 P19 evidence-strategy gate 必须双口径同时给 acceptance criteria。

### Open dependency unchanged

P19 evidence-strategy gate must, when designed, declare acceptance criteria for **both lenses**. v5.0 §12.3 / §16 / §18.3 全部重申这条不变量。v5.0 重构不改变这条 dependency 的内容或紧迫性。
