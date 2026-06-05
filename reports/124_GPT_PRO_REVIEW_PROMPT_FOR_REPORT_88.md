# GPT-Pro review prompt for report 88

- 日期：2026-05-23 覆盖更新
- 用途：复制给 GPT-Pro，让它审查 report 140 的 Lens-B 3seed × 10000e post-run 结论、report 88 综合背景与后续论文路线
- 最新主报告：`reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md`
- 背景主报告：`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`
- 论文路线草案：`reports/123_EV_NODI_paper_story_outline_for_later_discussion.md`

---

## Copy prompt

```text
You are reviewing an EV/NODI simulator repository and its current reader-facing analysis report.

First, establish reproducibility status:

1. If the repository root is available, run:

   python tests/run_tests.py --workers 7

2. If the command cannot be run because the environment lacks the unpacked repository, dependencies, or test files, state that clearly. Do not claim that tests passed unless you personally ran them in this review session.

3. Even if tests cannot run, continue the conceptual/document review. Treat test unavailability as a reproducibility note, not as a reason to skip the report review.

Primary files to read:

- reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md
- reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md
- reports/122_EV_NODI_report_88_v4_dual_lens_consolidation_ledger.md
- reports/123_EV_NODI_paper_story_outline_for_later_discussion.md
- 文档导航.md
- README.md

Optional supporting files if available:

- nodi_simulator/review_package.py
- tools/analyze_lens_b_ev_gold_fullgrid.py
- results/lens_b_ev_gold_fullgrid_1seed_20260513/lens_b_fullgrid_analysis_report.md
- results/lens_b_ev_gold_fullgrid_1seed_20260513/lens_b_ev_fullgrid_route_ranking.csv
- results/lens_b_ev_gold_fullgrid_1seed_20260513/lens_b_ev_recommendation_eligible_404_660.csv
- results/lens_b_ev_gold_fullgrid_1seed_20260513/lens_b_ev_control_only_488_532.csv
- results/lens_b_ev_gold_fullgrid_1seed_20260513/lens_b_gold_anchor_tsuyama_diagnostic_summary.csv
- results/lens_b_ev_gold_fullgrid_1seed_20260513/lens_b_a_vs_b_difference_explainer.csv
- tests/test_paper_provenance_disjoint_and_supersession.py
- tests/test_claim_language_regression.py
- configs/realism_v2/forbidden_claims_lexicon.yaml
- results/post_v2_mandatory_audit/*
- results/ev_nodi_realism_v2_full_grid_R5_v2/*
- reports/49*, reports/70*, reports/71*, reports/84*, reports/87*, reports/89*, reports/121*

Review target:

The current Lens-B full-grid report is report 140. Report 88 remains the consolidated background report. Report 100 is historical B6/B7 single-seed method context. These are no-measured-data, relative design-space audits for EV/NODI route selection. They are not calibrated simulators, not experimental reports, not biological-specificity reports, and not full-wave electromagnetic solvers.

Please review it from two perspectives.

Part 1 — External reader / logic audit of report 88

Audit whether report 88 is internally logical, readable, and hard to misinterpret for a first-time technical reader.

Focus on:

1. Does the first-time reader entrance work?
   - §0.0 claim boundary
   - §0.0 selected-annulus optical-annulus warning and number-comparability rule
   - §0.3c wavelength roles / lineage / figure specifications
   - §2.1a / §2.1b workflow and core computation diagrams
   - §7.0a lens-coded evidence/gap map (`D-A / D-N / D-P / D-S / M / R / G`)
   - §10.6a route-role decision matrix and evidence-type row
   - §16.2a P19 minimum acceptance criteria

2. Are the report boundaries strong enough?
   - It may claim relative route robustness, route roles, audit provenance, and validation gaps.
   - It may not claim calibrated SNR, LOD, concentration, count rate, absolute physical optimality, EV biological specificity, full-wave truth, or measured blank safety.

3. Is the dual-lens logic clear?
   - Lens A: all-crossing engineering route selection.
   - Lens B: selected-annulus Tsuyama-anchored EV application lens: B1 fits/freezes estimated parameters from Au/Ag anchors, then B2 applies those parameters to EV biomimetic candidates.
   - B2 latest robust evidence is report 140: shared-dual 3 seeds × 10000 events/case over 572 route triples and 56 particles.
   - Here selected-annulus should read as an event-position / analysis-window lens, not a BFP optical annular aperture unless code evidence explicitly supports it.
   - Neither lens should replace the other.
   - Anchor diagnostic geometry should not be mistaken for EV recommendation geometry.
   - Gold rows should be read only as anchor / Tsuyama consistency diagnostics, not mixed with EV rows into a combined winner.

4. Is the 660 / 404 / 532 / 488 comparison clear enough?
   - 660 nm should read as the conservative main route under the current relative audit.
   - 404 nm should read as a high-value shortwave sidecar / probe and lens-B recommendation-eligible shortwave shortlist item, not an automatic mainline replacement.
   - 532 and 488 nm should read as Tsuyama-aligned trend/control anchors, not current EV recommendation wavelengths even if a raw metric table ranks them first.
   - The final Lens-B EV recommendation table should be read from the 404/660 recommendation-eligible outputs; 488/532 belong in control-only / trend-only outputs.

5. Are the tables sufficient?
   - Identify tables that are overloaded, redundant, too dense, or not needed in the main report.
   - Identify tables that should move to appendix / supplement.
   - Identify any missing table columns such as claim level, source type, strict controlled status, lens, panel, not-allowed interpretation, or validation artifact.
   - Pay special attention to whether `D-A`, `D-N`, `D-P`, and `D-S` in §7.0a prevent mixed-lens "D" misreading.

6. Are the current diagrams sufficient?
   - Decide whether the whole engineering workflow and core computation unit diagrams are clear enough.
   - Decide whether a full project flowchart, internal calculation flowchart, route-role matrix, heatmap, line plot, bar chart, Sankey, decision tree, or evidence/risk matrix would make the report easier to understand.
   - For every proposed figure, specify: placement, plot type, required data source, intended message, and what the caption must forbid.

7. Is the comparison strong enough for a reader to know what is better?
   - Be careful: "better" must mean "more robust under the current relative audit", not "physically absolutely better".
   - Check whether 660 vs 404 and 532/488 controls are explained with enough physics, governance, and claim-boundary context.

8. Identify any remaining dangerous wording.
   - Flag wording that sounds like calibrated prediction, absolute optimality, route promotion, measured validation, selected-annulus optical aperture, or Tsuyama calibration.
   - In particular, flag any internal workflow wording that still uses "calibration" where "reproduction-lens target fitting" or "frozen reproduction-parameter set" would be safer.

Output for Part 1:

- Executive verdict.
- P0/P1/P2 findings ordered by severity.
- Concrete section-level edit suggestions.
- A table of recommended figures/tables with placement and caption warnings.
- A short "safe wording" replacement list for risky phrases.

Part 2 — Journal reviewer / future paper roadmap

Think as a journal reviewer. If this engineering project were the basis for a paper, what would be needed?

Please decide the strongest safe paper framing:

- Preferred framing: physics-governed relative design-space audit / route-selection framework.
- Avoid framing as calibrated EV detection, absolute wavelength optimization, LOD prediction, or validated biological assay unless measured artifacts are added.

Review:

1. What is the central paper story?
2. What are the main contributions?
3. What data are currently sufficient for a framework paper?
4. What data are missing for a stronger instrument / detection paper?
5. What figures should become main figures?
6. What figures/tables should become supplementary?
7. What validation artifacts are minimally required before submission?
8. What reviewer objections are likely, and how should the manuscript answer them?

Minimum validation package to think through:

- measured blank-channel reference per wavelength;
- detector operator / BFP / slit / pinhole / ROI measurement;
- standard particle calibration, especially Au 20/30/40/60 nm and soft-particle controls;
- detector gain, noise, lock-in/readout chain;
- flow / trajectory / transit-time validation;
- EV and contaminant characterization;
- 488/532 Tsuyama-style trend reproduction if used as an external anchor;
- representative full-wave spot checks.

Output for Part 2:

- Recommended paper positioning.
- Detailed manuscript outline.
- Main figure plan.
- Supplementary figure/table plan.
- Required validation package, separated into minimum / strong / best-case tiers.
- Reviewer-risk checklist with suggested responses.
- Sentences that should and should not appear in the abstract or conclusion.

Important constraints:

- Do not invent measured data.
- Do not treat synthetic detection proxy as event probability.
- Do not treat per-event detectability as count rate, concentration, or LOD.
- Do not treat selected-annulus as an optical annular aperture unless code evidence explicitly supports that.
- Do not treat Tsuyama alignment as calibration of this local simulator.
- Do not treat 488/532 raw metric wins as recommendation conclusions; final recommendation wavelengths are restricted to 660/404.
- Do not treat lens-B anchor diagnostic geometry as lens-B EV recommendation geometry.
- Do not mix gold anchor rows and EV/exosome rows into one lens-B winner.
- Do not treat the one-seed lens-B EV+gold full-grid as a 3-seed robust consensus.
- Do not merge `D-A`, `D-N`, `D-P`, and `D-S` evidence classes into one direct-comparison class.
- Do not treat P19 as complete unless the minimum acceptance criteria cover both lenses or explicitly mark the uncovered lens as a gap.
- Give concrete file/section references where possible.
```

---

## Local status to paste with the prompt if useful

As of 2026-05-14 in the local workspace, report 88 has moved to v5.2.6 and the B-EV + gold full-grid analysis artifacts have been generated from `results/lens_b_ev_gold_fullgrid_1seed_20260513/`. Rerun the commands below before claiming full-package verification:

```text
python -m py_compile tools/analyze_lens_b_ev_gold_fullgrid.py
  -> passed
python tools/analyze_lens_b_ev_gold_fullgrid.py --check-only
  -> passed
git diff --check
  -> passed
python -m pytest tests/test_paper_provenance_disjoint_and_supersession.py tests/test_claim_language_regression.py -q
  -> 19 passed in 0.05s
python tests/run_tests.py --workers 7
  -> AppTest lane: 5 passed, 1347 deselected in 1.78s
  -> non-AppTest lane: 1347 passed in 79.84s
```

This local status should be treated as context only. GPT-Pro should still state whether it personally reran tests in its own environment.
