# Current Documentation Status Audit 2026-05-23

## Executive Status

本轮按“逐个说明文件”口径重新检查了仓库内所有 Markdown 说明文件，并把每个文件的当前性状态写成一行机器清单。结论：当前入口、工程说明、prompt、`reports/current/` 说明和关键历史 supersession 文件已经更新到 report 140 口径；archive 与历史 reports 保留为 provenance，不改写成当前结论。当前 Lens-B full-grid 解释入口是 `reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md`，不是 report 88 / report 100 的单 seed B6/B7 overlay。

## Per-File Ledger

逐个文件清单：

- `tmp/current_documentation_status_20260523/current_documentation_file_status_20260523.csv`
- `tmp/current_documentation_status_20260523/summary.json`

该 CSV 对每个 `.md` 文件记录：

- path
- class
- status
- issue
- line_count
- whether it has the report 140 anchor
- whether it mentions report 88 / report 100 / B6 / B7
- whether it contains current/latest wording
- handling note

## Scope

纳入审查：

- root Markdown 说明文件
- `docs/`, `guides/`, `dashboard/`, `prompts/`, `tests/`, `tools/`
- current and historical `reports/`
- `archive/` Markdown provenance

排除：

- `.git/`, `.claude/`, `.omx/`
- virtualenv / vendor / cache directories
- `results/`, `papers/`, `tmp/`
- AppleDouble `._*` metadata files

## Classification Summary

| class | count | handling |
| --- | ---: | --- |
| current_spec_or_prompt | 117 | kept current; report 140 anchor added where these docs act as review entrypoints |
| historical_report | 96 | retained as historical provenance; current truth governed by README / 文档导航 / report 140 |
| historical_archive | 56 | retained as archive-only provenance |
| current_module_or_tool_doc | 20 | checked as code-companion docs; no full-grid claim text needed unless they discuss results |
| current_entry_or_governance | 14 | updated or checked for current report 140 routing |
| historical_current_dir_note | 5 | updated where they still used report 88 / report 100 as current Lens-B entry |
| current_report | 4 | report 140, report 141, report 142, and report 143 retained as current reports |
| other_markdown | 1 | AGENTS.md; instruction file, not scientific conclusion source |

Final status counts:

| status | count | meaning |
| --- | ---: | --- |
| ok | 144 | current or neutral docs checked |
| historical_ok | 157 | historical/archive files intentionally preserved, not current truth |
| reviewed_current_context | 12 | current-facing docs mention historical B6/B7/report 100 context but now carry report 140 anchor |
| needs_current_anchor | 0 | no current-facing doc remained missing the latest full-grid anchor |

## Files Updated In This Pass

Current entry / governance docs:

- `00_工程总指南.md`
- `24_高性能预计算与增量重算方案.md`
- `26_评分复盘与现状分析.md`
- `42_全量重算前复核结论与现行边界.md`
- `43_Tsuyama对齐主链升级路线图与修改框架.md`
- `HISTORICAL_REPORT_SUPERSESSION.md`
- `GPT_PRO_REVIEW_BUNDLE_README.md`
- `REVIEW_PACKAGE_README.md`

Current reports / current-directory notes:

- `reports/current/README.md`
- `reports/current/35_method_notes.md`
- `reports/current/36_exosome_biomimetic_surface_model.md`
- `reports/current/46_全量计算性能优化复核.md`
- `reports/current/47_EV_NODI全量结果分层分析报告.md`
- `reports/122_EV_NODI_report_88_v4_dual_lens_consolidation_ledger.md`
- `reports/123_EV_NODI_paper_story_outline_for_later_discussion.md`
- `reports/124_GPT_PRO_REVIEW_PROMPT_FOR_REPORT_88.md`
- `reports/125_lens_b_tau1ms_recalibration_roadmap_2026-05-14.md`
- `reports/126_lens_b_tau1ms_stage_b5_targeted_probe_note_2026-05-14.md`
- `reports/127_lens_b_tau1ms_stage_b6_1000e_fullgrid_note_2026-05-15.md`

Prompt docs:

- `prompts/claude_post_v2_review_ready_audit_prompt.md`
- `prompts/gpt_pro_physics_review_prompt.md`
- `prompts/gpt_pro_report88_reader_journal_review_prompt.md`

Historical audit / navigation:

- `docs/DOCUMENTATION_AUDIT_2026-05-08.md`
- `README.md`
- `文档导航.md`

Generated documentation sources:

- `nodi_simulator/review_package_docs.py`
- `nodi_simulator/review_package_governance.py`

## Current Interpretation Rules Now Reflected

- `reports/140` is the current Lens-B 3seed × 10000e full-grid post-run analysis.
- `reports/88` remains consolidated v1/v2/post-v2 background, not the newest Lens-B route-family decision.
- `reports/100` and B6/B7 1000e files remain historical single-seed method overlays.
- `fixed_660_gold` and `per_wavelength_gold` are normalization views over shared physical events, not independent physical campaigns.
- EV recommendations use EV/exosome rows; gold rows are anchor / Tsuyama diagnostics only.
- 488/532 remain control/reference wavelengths.
- selected-annulus remains an event-position / analysis-window lens, not an optical BFP annulus.
- The project remains no-measured-data Level-1 relative/proxy evidence only.

## Historical Files Policy

Historical reports and archive files were not rewritten line by line into current claims because doing so would destroy provenance. Instead, current entry documents now route readers away from stale conclusions. This is intentional:

- Archive Markdown is `historical_archive`.
- Numbered stage reports before report 140 are `historical_report` unless explicitly named as current background/provenance.
- `reports/current/` is a historical comparison directory, not the current entrypoint.

## Commands Run

```bash
python tmp/current_documentation_status_audit_20260523.py
python tmp/full_project_source_doc_audit_20260523.py
ruff check .
python -m pyright
python -m mypy
python -m pytest tests/test_review_package_claim_scan.py tests/test_verify_review_package_cli.py tests/test_review_package_manifest.py -q
python tests/run_tests.py --workers 7
```

Verification commands from the paired cleanup pass remain:

```bash
ruff check .
python -m pyright
python -m mypy
python -m pytest tests/test_review_package_claim_scan.py tests/test_verify_review_package_cli.py tests/test_review_package_manifest.py -q
python tests/run_tests.py --workers 7
python tmp/full_project_source_doc_audit_20260523.py
```

## Final Verification Snapshot

| check | result |
| --- | --- |
| per-file documentation status audit | pass: 313 Markdown files, 0 current-entry files missing report 140 anchor |
| full source/doc audit | pass: 975 source/doc/config files, 313 Markdown files, 0 Python syntax errors, 0 Markdown local broken links |
| `ruff check .` | pass |
| `python -m pyright` | pass: 0 errors, 0 warnings, 0 informations |
| `python -m mypy` | pass: no issues in 6 source files |
| review package claim/verifier tests | pass: 10 passed |
| `python tests/run_tests.py --workers 7` | pass: AppTest 5 passed; non-AppTest 1410 passed |

## Residual Caveats

- The per-file audit proves every Markdown file was classified and checked for current-entry routing; it does not turn historical reports into current reports.
- Some historical files still contain words like “current” or “latest” inside their original dated context; they are safe because navigation and supersession now mark them as historical provenance.
- Module companion docs were checked for stale full-grid routing, but their API content still depends on code evolution and should be regenerated from code if their implementation changes.
