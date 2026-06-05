# EV NODI report 88 v4.0 dual-lens consolidation ledger 2026-05-11

This ledger records the 2026-05-11 in-place restructure of `reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md` from v3.0 to **v4.0 dual-lens**, plus the follow-on v5.x updates required to keep the all-crossing lens and the selected-annulus Tsuyama-anchored lens equally weighted as reader entrances.

It is a review artifact. As of 2026-05-23, the current Lens-B full-grid source of truth is `reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md`; report 88 remains the consolidated v1/v2/post-v2 background. Raw provenance for the selected-annulus lens remains `reports/49` (B1 Phase 2 / 2.5–2.11), `reports/71` (R5.2 bounded scenario-prior audit + sidecar guardrail), and the report 140 audited shared-dual 3seed × 10000e seed/aggregation directories.

## v5.2.6 full-grid addendum (2026-05-14): lens B EV+gold full-grid final

Resolved in report 88 v5.2.6:

- B2 is no longer pending or represented by targeted EV evidence. The completed full-grid directory is `results/lens_b_ev_gold_fullgrid_1seed_20260513/`.
- Precheck status: `32,032` rows, `seed=42`, `10000` events/case, particle materials `exosome/gold`, and wavelengths `404 / 488 / 532 / 660`.
- EV recommendation uses EV/exosome rows only. Gold rows are retained only for anchor / Tsuyama consistency diagnostics and must not be mixed into an EV winner.
- Recommendation-eligible wavelength conclusions are restricted to `404` and `660`. `488/532` remain in raw tables, trend plots, and control-only tables, but cannot become final recommendation wavelengths.
- The EV-only selected-annulus full-grid is dominated by `660 nm / 800 nm` width; report-level conservative B2 recommendation is written as `660 / 800x1400` and `660 / 800x1500`, with `404` retained as a shortwave eligible sidecar rather than the full-grid winner.
- The result is a one-seed synthetic relative result, not a 3-seed robust consensus, not a measured blank result, and not calibrated SNR/LOD or biological specificity evidence.

Derived files added for this addendum:

| File | Role |
|---|---|
| `lens_b_fullgrid_data_precheck.json` | result integrity and scope precheck |
| `lens_b_ev_fullgrid_route_ranking.csv` | EV-only full-grid route / geometry / wavelength ranking |
| `lens_b_ev_recommendation_eligible_404_660.csv` | EV-only recommendation-eligible 404/660 table |
| `lens_b_ev_control_only_488_532.csv` | EV-only 488/532 control/trend table |
| `lens_b_gold_anchor_tsuyama_diagnostic_summary.csv` | gold anchor / Tsuyama diagnostic-only summary |
| `lens_b_a_vs_b_difference_explainer.csv` | lens / parameter / metric / particle-scope difference table |
| `lens_b_fullgrid_analysis_report.md` | short B full-grid final analysis report |

## v5.2.5 correction addendum (2026-05-13): lens B EV application

User clarification (2026-05-13):

```text
口径 B 的创建目标，是修改所有估计的参数值，让锚点尺寸的结果与 Tsuyama 论文中的数据一致，
然后用这些估计的参数值，来计算出哪些尺寸才是最合适的。
口径 B 也是要用估计值来看 EV biomimetic，不是只看 anchor。
推荐波长只在 660 / 404 内选，488 / 532 只作趋势/对照；
这个规则只反映到选型结论，中间对比表格和图不要受影响。
```

Resolved in report 88 v5.2.5, then superseded for B2 selection by the v5.2.6 full-grid addendum above:

- Lens B is now explicitly split into **B1 anchor target-fitting / residual diagnostic** and **B2 EV biomimetic application**.
- B1 keeps the frozen estimated parameter set (`D2.1 best`, `gamma = 0.749`, `snr_scale = 0.728`, `snr_response_exp = 0.812`, selected-annulus `0.5-0.8`) and the anchor diagnostic geometry `660 / 800x550` + `660 / 1200x550`.
- B2 applied those frozen parameters to EV biomimetic targeted evidence as an interim correction. The raw metric top1 `488 / 600x1500` remains in comparison/trend/control output, but no longer appears as a recommendation conclusion.
- Recommendation conclusions choose only among `660` and `404`. The then-current targeted recommendation-eligible shortlist `404 / 600x1300` plus `660 / 800x1400-1500` has been replaced for current B2 selection by the v5.2.6 EV+gold full-grid result.
- No simulation, solver case, candidate, lane, seed, measured artifact, frozen B parameter, or raw metric table changed.

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

## v5.1 amendment (2026-05-12): reader table supplement on top of v5.0 (codex 第二轮反馈吸收)

User instruction (2026-05-12, via codex 第二轮 review):

```text
不要推翻 v5.0，而是在 c67c768 的基础上做 v5.1 读者表格增强 / 解释增强。
核心目标不是再重构一次，而是补上"读者最想直接看懂的对比表"和
"阶段量之间如何传导到结论"的解释。
请尽量利用已有结果文件派生表格，不要新增 simulation；
如果只是从既有 CSV 汇总、取中位数、取固定条件切片，
可以明确标注为"derived reader table"。
```

Resolved: **v5.1 reader table supplement**——只补读者表格 / 增解释，不改变 v5.0 / v4.2 任何数值或 forbidden。新增 10 个章节小节 + 1 个章节扩展，按 codex 8 项验收问题映射。

### v5.1 新增 / 扩展章节清单（10 项 + 1 扩展）

| 改动 | 位置 | 类型 | codex 验收对应 |
|---|---|---|---|
| §0.3b 读者问题导航表（10 行） | §0 阅读须知 | 新增 | 验收 1–10 总览 |
| §3.0a 阶段量级联（"是谁、归谁管、三条骨架公式、三条不保证"）| §3 可调变量 | 新增 | 验收 3 |
| §2.4 扩展为 4 波长机制链（404 / 488 / 532 / 660）| §2 物理链 | 扩展 | 验收 1 / 5 |
| §7.0 变量固定法 5 条（如何读 controlled comparison）| §7 变量隔离 | 新增 | 总原则一致性 |
| §7.2.5a 信号链扩列对比（2 张代表性扩列表：800 × 1400 vary λ + 660 nm/H=1500 vary W）| §7 变量隔离 | 新增 | 验收 1 / 2 |
| §8.5 blocker 分类表（10 类 detection blocker）| §8 噪声归因 | 新增 | 验收 4 |
| §8.6 噪声 sensitivity 数值版（含 reference×2 / noise×2 假想）| §8 噪声归因 | 新增 | 验收 7 / 8 |
| §10.6 多候选裁决表（why yes / why not 8 候选）| §10 口径 A 推荐 | 新增 | 验收 5 / 6 |
| §11.8 口径 B step 流程表（input → output → what it is NOT）| §11 口径 B 推荐 | 新增 | 验收 7 |
| §13.2 阶段量来源与置信等级映射（13 个阶段量）| §13 估计值来源 | 新增 | 验收 8 |
| 旧有 §8.5 一句话总结改名为 §8.7（因 blocker / sensitivity 占用 §8.5 / §8.6） | §8 噪声归因 | 重编号 | 内部一致性 |

### codex 验收清单映射

| # | codex 验收问题 | v5.1 解决位置 |
|--:|---|---|
| 1 | 我能不能看到某个固定尺寸下 404/488/532/660 的完整对比？ | §2.4 + §7.2.5a.1 |
| 2 | 我能不能看到固定 660 nm 时不同 W/H 为什么有差异？ | §7.2.5a.2 + §7.2.x + §10.4 + §10.6 |
| 3 | 我能不能看懂 Csca / E_sca / reference / cross-term / peak / noise / detection 之间不是简单线性关系？ | §3.0a + §13.2 |
| 4 | 我能不能知道 detection 低到底败在什么 blocker？ | §8.5 |
| 5 | 我能不能理解为什么 404 peak 强但不一定推荐？ | §2.4 + §6.4.F + §10.6 + §8 |
| 6 | 我能不能理解为什么 660 main route 被保留？ | §10.2 + §10.4 + §10.5 + §10.6 |
| 7 | 我能不能理解口径 B 是"校准后选型"，不是"为了贴近 Tsuyama 而选型"？ | §11.4 + §11.8 + §10.6 |
| 8 | 我能不能清楚知道哪些表是既有 artifact 派生 / simulation 原始输出 / 解释性诊断？ | §13.2 + §5 |

### Files updated for the v5.1 amendment

| File | Change |
|---|---|
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) | 头部 v5.0 → **v5.1 reader table supplement**；新增 §0.3b / §3.0a / §7.0 / §7.2.5a / §8.5 / §8.6 / §10.6 / §11.8 / §13.2；扩展 §2.4 到 4 波长；§8 重编号；§13 拆 §13.1 / §13.2；附录 C 增列；§18 加 v5.0 二次精修行 + v5.1 行 + §18.4 验收映射 + §18.5 v5.1 不变量。从 1906 行 → 2215 行。 |
| [reports/122](122_EV_NODI_report_88_v4_dual_lens_consolidation_ledger.md) | 本段落（v5.1 amendment ledger entry）。 |

### What did **not** change in the v5.1 amendment

- `release_status` for lens B 仍 `negative_or_diagnostic_result_only`；冻结参数集 + γ=0.749 / s_SNR=0.728 / e_SNR=0.812 不变。
- §15 forbidden claim 一条未放宽。
- 全部 v5.0 / v4.2 数值结论：所有 detection 表行（§3.2 路线类、§4 main-660、§6 NODI lens / Tsuyama / Au gold、§13.1 P0 audit 572/563、§14.5 reproduction lens γ=0.749 / score 2.033、§14.7 R5.2 sidecar、§14.6.1 instrument 216/216）。
- 双口径并立、selected-annulus 0.5–0.8 固定、sidecar guardrails 全部维持。
- 没有新计算 / 新 candidate / 新 lane / 新随机种子 / 新 solver case / 新 experiment / 新 measured artifact ingest。
- 没有修改 `nodi_simulator/review_package.py` 生成字符串 / `HISTORICAL_REPORT_SUPERSESSION.md` / `文档导航.md`（v5.0 章节号在 v5.1 内仍有效；v5.1 新增小节都在 v5.0 已有大节内 / 之间）。
- 没有修改 tests。

### Verification evidence (v5.1 amendment)

```text
python -m pytest tests/test_paper_provenance_disjoint_and_supersession.py -q
  → 2 passed in 0.03s
```

v5.1 amendment 仍是纯 reader-facing markdown 增补；未触及 simulator / schema / contract / fixture / generator string / nav doc，因此未触发额外 pytest。

### Boundary preserved by the v5.1 amendment

- 全部 v5.0 二次精修后的术语口径在 v5.1 内继续生效（detection → synthetic detection score / proxy；transit → ms 绝对值；倍数列只用于阶段量；不跨 lens / panel 直接百分比 ranking）。
- 口径 B 流程严格按 §11.8 step 1–6 顺序展开；几何选型不走"哪个最像 Tsuyama"捷径在 §11.4 + §11.8 step 4/5 双重重申。
- §15 共同 forbidden 全部继承。

### Open dependency unchanged

P19 evidence-strategy gate must, when designed, declare acceptance criteria for **both lenses**. v5.0 §12.3 / §16 / §18.3 / §18.5 全部重申这条不变量。v5.1 reader table 增强不改变这条 dependency 的内容或紧迫性。

## v5.1.1 + v5.2 amendment (2026-05-12): hotfix + reader comparison table pack (codex 第三轮反馈)

User instruction (2026-05-12, codex 第三轮 review)：

```text
v5.1 方向正确，读者导航、阶段量解释、口径 B 流程、blocker/sensitivity 框架都补上了；
但当前还不适合说"完全验收"。建议先做 v5.1.1 hotfix，再规划 v5.2 多表格增强。
```

Resolved: 拆为两个步骤：

**v5.1.1 hotfix（codex 第三轮 P0 + P1 必修）**：

| 修法 | 位置 | 来由 |
|---|---|---|
| 新增真实 §6.4.F 表（4 波长信号链汇总）| §6.4.E 后 | 修复 5 处先前引用 `§6.4.F` 但实际只到 §6.4.E 的悬空 |
| §2.4 拆为块 A（strict 物理阶段量）+ 块 B（route-level evidence）| §2.4 内 | 防止读者把 detection 行误读为 strict λ-only 对照 |
| §8.6 reference×2 行修正逻辑（option A：noise 不变 → threshold 不同步上抬）| §8.6 内 | 原写法"threshold 上抬抵消"在 noise×=1 假设下逻辑矛盾 |
| §10.6 拆 mixed-lens cell 为 all-cross + NODI 两列 | §10.6 候选裁决表 | 防止跨 lens 直接百分比比较 |
| 统一 detection 表头为 `synthetic detection score (%)` / `proxy (%)` | §6.4 / §7.1 / §7.2 多张表 | v5.0 二次精修术语口径继续清理 |
| 修正 §8.5 / §8.6 takeaway 的表号引用 | §8.5 / §8.6 段末 | 原 v5.1 写成 "表 8.6" / "表 8.7" 应为 "表 8.5" / "表 8.6" |
| 修复 `window-prior` → `width-prior` 拼写 | §10.6 裁决原则段 | 单处拼写错误 |
| Header "不引入新计算" 改为精确表述 | header 说明段 | 把"派生重组、单位换算、物理近似解释"显式列出，避免误以为所有数字都是旧表原样搬运 |
| §18.4 "完全验收"改为"第一层代表性补表" | §18.4 口径声明段 | 口径准确化，明确剩余 reader pack 在 v5.2 |

**v5.2 reader comparison table pack（codex 第三轮 7 项核心扩展）**：

| 新增 | 位置 | 数量 |
|---|---|---|
| 附录 D 固定 W × H vary λ 完整 reader tables | 附录 D | 5 张表（800×1400 / 800×1500 / 800×550 / 600×1300 / 500×1500）|
| 附录 E 固定 λ vary W × H 完整 reader tables | 附录 E | 5 张表（660 H=1400 / 660 H=1500 / 660 W=800 / 660 W=500 / 404 sweep）|
| 附录 F strict controlled vs route-level 对照矩阵 | 附录 F | 14 行总表 |
| §18.6 v5.2 验收（codex 10 项）| §18.6 | 10 行验收映射 |
| §18.7 旧 report 47 迁移决定修正 | §18.7 | v5.2 新增迁移决定；v5.2.1 复核确认 CSV 存在于 `reports/current/47_ev_design_full_grid_analysis/`，迁移仍因 provenance / 术语 / forbidden 审计成本延后 |

### codex 第三轮验收映射（10 项）

详见 [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) §18.6 完整 10 行表（全部 ✅）。

### Files updated for the v5.1.1 + v5.2 + v5.2.1 amendment

| File | Change |
|---|---|
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) | 头部 v5.1 → **v5.2.1 reader comparison table pack + consistency hotfix**；新增 §6.4.F + 附录 D / E / F + §18.6 + §18.7；修正 §2.4 / §8.6 / §10.6；统一 detection 表头；修正表号 / 拼写 / report 47 CSV 路径判断。从 2215 行 → 2453 行（+238 行）。 |
| [reports/122](122_EV_NODI_report_88_v4_dual_lens_consolidation_ledger.md) | 本段落（v5.1.1 + v5.2 + v5.2.1 amendment ledger entries）。 |

### What did **not** change in v5.1.1 + v5.2 + v5.2.1

- `release_status` for lens B 仍 `negative_or_diagnostic_result_only`；冻结参数集 + γ=0.749 / s_SNR=0.728 / e_SNR=0.812 不变。
- §15 forbidden claim 一条未放宽。
- 全部 v5.0 / v5.1 数值结论（路线类、main-660、Au gold 阶梯、Tsuyama lens 对照、P0 audit、reproduction lens 等）。
- 双口径并立、selected-annulus 0.5–0.8 固定、sidecar guardrails 全部维持。
- 没有新 simulation / solver case / candidate / lane / random seed / experiment / measured artifact ingest；新增表格只做派生重组、单位换算、物理近似解释和读者向诊断。
- 没有修改 `nodi_simulator/review_package.py` / `HISTORICAL_REPORT_SUPERSESSION.md` / `文档导航.md` / tests。

### Verification evidence (v5.1.1 + v5.2)

```text
python -m pytest tests/test_paper_provenance_disjoint_and_supersession.py -q
  → 2 passed in 0.04s (executed after merge to main)
```

v5.1.1 + v5.2 amendment 仍是纯 reader-facing markdown 增补 + 修正；未触及 simulator / schema / contract / fixture / generator string / nav doc，因此未触发额外 pytest。

### Boundary preserved

- 全部 v5.1 二次精修后的术语口径在 v5.1.1 + v5.2 + v5.2.1 内继续生效（detection → synthetic detection score / proxy；transit → ms 绝对值；倍数列只用于阶段量；附录 F 14 行对照矩阵硬性约束 strict vs route-level 不可混读）。
- 口径 B 流程严格按 §11.8 step 1–6 顺序展开；几何选型不走"哪个最像 Tsuyama"捷径在 §11.4 + §11.8 + 附录 F 三重重申。
- §15 共同 forbidden 全部继承。
- 附录 D / E 中 detection cell **只在 source type 标为 strict 直接行时填**——这是 v5.2 防止"最近邻塞进 cell 伪装成 strict 数据"的硬约束；route-level 最近邻只能放 note。

## v5.2.1 consistency hotfix (2026-05-12): codex 第四轮复核收尾

Codex 第四轮复核指出 v5.2 内容主体有效，但仍有若干"声明和事实不一致"的小口子。v5.2.1 只做 consistency hotfix，不扩展表格、不新增数值结论。

| 修法 | 位置 | 说明 |
|---|---|---|
| 修正 report 47 CSV 存在性判断 | report 88 §18.7 + 本 ledger | v5.1.1 只查 `results/` 和 `archive/`，漏查 `reports/current/`；6 个 historical report 47 CSV 实际存在于 `reports/current/47_ev_design_full_grid_analysis/`。迁移仍延后，因为需要 provenance / 术语 / lens / panel / forbidden-claim 单独审计。 |
| 精确化"不引入新计算"表述 | report 88 header / §18.2 + 本 ledger | 改为不引入新 simulation / solver case / candidate / lane / random seed / measured artifact ingest；新增表格属于派生重组、单位换算、物理近似解释和读者向诊断。 |
| 继续统一 detection 表头 | report 88 §7.1.4 / §10.5 | `Au20 det (%)` 等改为 detection proxy；`all-crossing detection (%)` 改为 all-crossing synthetic detection score。 |
| 拆 mixed-lens cells | report 88 附录 D / E | D.1 / D.3 / E.3 / E.5 中不同 lens 数值移到 note，不在同一个 detection cell 内并列。 |
| 修正附录 F 约束语 | report 88 附录 F | 从"仅 660 cell 有 strict 直接行"改为"仅 source type 标 strict 直接行的 cell 可读"，覆盖 D.4 的 404/600×1300 strict 直接行。 |
| 清理格式和行数 typo | report 88 §6.4.F + 本 ledger | 清掉 trailing whitespace；report 88 行数从 2455 改为实际 2453。 |

### Verification evidence (v5.2.1)

```text
git diff --check
  -> passed
pytest tests/test_paper_provenance_disjoint_and_supersession.py -q
  -> 2 passed in 0.03s
```

本 hotfix 不触碰 simulator / schema / contract / fixture / generator string / nav doc。

### Open dependency unchanged

P19 evidence-strategy gate must, when designed, declare acceptance criteria for **both lenses**. v5.x §12.3 / §16 / §18.3 / §18.5 全部重申。v5.2 reader comparison pack 不改变这条 dependency；附录 D / E 中大量 `—` cell 直接显示 P19 实测的优先级（§16.2）。

## v5.2.2 external-review entrance layer (2026-05-13): GPT-Pro feedback triage

User instruction (2026-05-13):

```text
再深入思考之后，先开始完善分析报告。
对于论文的部分，深入思考之后，列一个详细的提纲，先保留为一个说明文档保存下来。
```

Resolved:

- report 88 升为 **v5.2.2 external-review entrance layer**；
- 只在 §0 增加外部初读者入口，不改任何数值、表格数据、release status、forbidden claim 或冻结参数；
- 论文路线不塞回主报告，单独保存为 `reports/123_EV_NODI_paper_story_outline_for_later_discussion.md`，后续再讨论。

### Files updated for v5.2.2

| File | Change |
|---|---|
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) | Header 升为 v5.2.2；新增 §0.3c 外部审稿人入口：四波长角色表、版本 / lens lineage 表、三张优先图表规格、report 123 论文提纲指针；§18.2 增加 v5.2.2 历史行。 |
| [reports/123](123_EV_NODI_paper_story_outline_for_later_discussion.md) | 新增后续论文路线讨论草案：paper positioning、storyline、methods/results outline、main figure plan、supplement plan、minimum validation package、reviewer-risk checklist。 |
| [文档导航.md](../文档导航.md) | 当前入口说明更新到 v5.2.2；新增 report 123 入口；报告优先级更新。 |
| [reports/122](122_EV_NODI_report_88_v4_dual_lens_consolidation_ledger.md) | 本段落。 |

### What did not change

- No new simulation / solver case / candidate / lane / random seed / experiment / measured artifact ingest.
- Lens A main-660 recommendation unchanged.
- Lens B frozen diagnostic set unchanged.
- selected-annulus 0.5–0.8 unchanged.
- `calibrated_claim_allowed = false` boundary unchanged.
- P19 evidence-strategy dependency unchanged.

### Verification status

This v5.2.2 pass is markdown-only. Run `git diff --check` and the targeted paper-provenance / claim-language tests before external release packaging.

## v5.2.3 reviewer-figure entrance layer (2026-05-13): remaining-change execution pass

User instruction (2026-05-13):

```text
接下来还有什么改动，都详细列出来，然后逐步去完成
```

Resolved remaining change list:

1. **First-time reviewer claim boundary** — add a compact box before §0.1 so external readers know the report is a relative route audit, not a calibrated simulator or experimental paper.
2. **Whole engineering workflow flowchart** — convert the existing 7-stage text chain into a Mermaid flowchart in §2.1a.
3. **Core computation unit diagram** — add a second Mermaid diagram in §2.1b showing Mie scattering, detector operator, reference field, interference, readout/noise, and pulse extraction.
4. **Evidence/gap map** — add §7.0a to show direct evidence vs mean/grouped evidence vs nearest route evidence vs true coverage gaps.
5. **Route-role decision matrix** — add §10.6a so 660 / 404 / 532 / 488 are read as route roles rather than absolute wavelength winners.
6. **GPT-Pro prompt** — add a copyable prompt for the next external review pass, including test-status honesty, report 88 logic review, figure/table review, and paper-roadmap review.
7. **Navigation and index sync** — update report 88 header/history/table index, `文档导航.md`, report 123 dependency line, and this ledger.

### Files updated for v5.2.3

| File | Change |
|---|---|
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) | Header 升为 v5.2.3；新增 §0.0、§2.1a、§2.1b、§7.0a、§10.6a；§18.2 和附录 C 同步新增项。 |
| [reports/123](123_EV_NODI_paper_story_outline_for_later_discussion.md) | 依赖主报告指针更新为 report 88 v5.2.2 / v5.2.3 之后的论文路线草案。 |
| [reports/124](124_GPT_PRO_REVIEW_PROMPT_FOR_REPORT_88.md) | 新增可复制 GPT-Pro 审查 prompt，覆盖 report 88 逻辑 / 图表 / 四波长角色 / 论文路线，并要求测试状态实话实说。 |
| [文档导航.md](../文档导航.md) | 当前入口说明和使用优先级更新到 v5.2.3，并列出新增 reviewer 图解入口。 |
| [reports/122](122_EV_NODI_report_88_v4_dual_lens_consolidation_ledger.md) | 本段落。 |

### What did not change

- No new simulation / solver case / candidate / lane / random seed / experiment / measured artifact ingest.
- Lens A main-660 recommendation unchanged.
- Lens B frozen diagnostic set unchanged.
- selected-annulus 0.5–0.8 unchanged.
- `calibrated_claim_allowed = false` boundary unchanged.
- P19 evidence-strategy dependency unchanged.

### Verification evidence (v5.2.3)

```text
git diff --check
  -> passed
python -m pytest tests/test_paper_provenance_disjoint_and_supersession.py tests/test_claim_language_regression.py -q
  -> 19 passed in 0.05s
python tests/run_tests.py --workers 7
  -> AppTest lane: 5 passed, 1347 deselected in 1.72s
  -> non-AppTest lane: 1347 passed in 73.57s
```

## v5.2.4 lens-language cleanup layer (2026-05-13): GPT-Pro follow-up triage

User feedback (2026-05-13) reviewed report 88 v5.2.3 and found the first-time reader layer substantially improved, but still flagged three high-priority risks:

1. §7.0a mixed-lens `D` labels could be misread as all-crossing direct evidence.
2. Internal "校准 / calibration" wording could still imply measured physical calibration.
3. `selected-annulus` needed an earlier optical-annulus warning.

Resolved v5.2.4 changes:

1. **Header compression** — keep the report entrance light: version, status, unchanged invariants, current route verdict, and §0 reading pointer only.
2. **selected-annulus optical-annulus warning** — add the first-mention warning in §0.0: selected-annulus is an event-position / analysis-window lens, not a BFP optical annular aperture unless detector-operator code explicitly implements one.
3. **Number comparability rule** — add a §0.0 micro-rule: direct quantitative comparison requires matching lens, particle panel, source type, and fixed variables.
4. **§7.0a lens-coded coverage map** — replace ambiguous `D` with `D-A`, `D-N`, `D-P`, and `D-S`; title the EV map as "not a single-lens map"; state that those four direct-evidence classes cannot be merged.
5. **NODI-lens warnings** — add explicit warnings above §7.1.1 and §7.1.2 so 45.15% / 47.15% NODI-lens values are not read as all-crossing main-route scores.
6. **Route-role evidence row** — add an "Evidence type" row to §10.6a distinguishing direct main-route evidence, partial strict shortwave cells, and literature/control grouped trend evidence.
7. **Target-fitting terminology cleanup** — rewrite internal workflow language from "校准 lens / 校准估计参数 / 校准在前" to "reproduction-lens target fitting / frozen reproduction-parameter set / target-fitting first, residual-based selection second" while preserving forbidden calibrated-claim warnings.
8. **P19 acceptance criteria** — add §16.2a with minimum acceptance criteria for measured blank/BFP/slit/ROI, Au raw traces, soft-particle controls, detector chain, flow/trajectory, full-wave spot checks, and EV/contaminant characterization.
9. **Navigation and prompt sync** — update `文档导航.md`, report 123 dependency line, report 124 GPT-Pro prompt, §18.2, and appendix C to v5.2.4.

### Files updated for v5.2.4

| File | Change |
|---|---|
| [reports/88](88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md) | Header 升为 v5.2.4；新增 §0.0 selected-annulus warning / comparability rule；§7.0a 改 lens-coded evidence map；§7.1.1 / §7.1.2 加 lens warning；§10.6a 加 evidence type 行；§11 术语改为 target-fitting；新增 §16.2a；§18.2 / 附录 C 同步。 |
| [reports/123](123_EV_NODI_paper_story_outline_for_later_discussion.md) | 依赖主报告指针更新为 report 88 v5.2.2–v5.2.4 之后的论文路线草案。 |
| [reports/124](124_GPT_PRO_REVIEW_PROMPT_FOR_REPORT_88.md) | GPT-Pro prompt 更新为审查 report 88 v5.2.4，并加入 D-A/D-N/D-P/D-S、target-fitting、selected-annulus warning、P19 criteria 关注点。 |
| [文档导航.md](../文档导航.md) | 当前入口说明、双口径提示、报告归档与使用优先级更新到 v5.2.4。 |
| [reports/122](122_EV_NODI_report_88_v4_dual_lens_consolidation_ledger.md) | 本段落。 |

### What did not change

- No new simulation / solver case / candidate / lane / random seed / experiment / measured artifact ingest.
- Lens A main-660 recommendation unchanged.
- Lens B frozen diagnostic set unchanged.
- selected-annulus 0.5–0.8 unchanged.
- `calibrated_claim_allowed = false` boundary unchanged.
- P19 remains a future evidence-strategy gate; v5.2.4 only states minimum acceptance criteria.

### Verification evidence (v5.2.4)

```text
git diff --check
  -> passed
python -m pytest tests/test_paper_provenance_disjoint_and_supersession.py tests/test_claim_language_regression.py -q
  -> 19 passed in 0.05s
python tests/run_tests.py --workers 7
  -> AppTest lane: 5 passed, 1347 deselected in 1.78s
  -> non-AppTest lane: 1347 passed in 79.84s
```
