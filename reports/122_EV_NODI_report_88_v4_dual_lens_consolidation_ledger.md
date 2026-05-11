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
