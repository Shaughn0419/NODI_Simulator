# Results / Papers Internal Slimming Audit 2026-05-23

## Executive Verdict

可以瘦，而且有明确高收益点；但不建议从“删除旧结果”开始。当前最大机会是把仍需保留在工程里的大证据转为压缩/归档形态，尤其是 `papers/analysis_full_v1/` 和大型 CSV diagnostic/summary 文件。按只读审计估算，在不把 `results/` / `papers/` 移出工程的前提下，保守可释放约 `3 GiB`，中等风险压缩方案可释放约 `8-10 GiB`；真正不能碰的是当前 report 140 依赖的 3seed full-grid aggregation 和完整性证据链，除非同步更新读取工具、hash manifest 与文档路径。

本报告只分析候选，不删除文件，不压缩原件，不重跑 full-grid。

2026-05-23 后续状态：用户要求 `papers/` 先不动后，已执行非 paper 瘦身第一轮；详见 `reports/145_nonpaper_results_slimming_20260523.md`。该轮只处理 `results/` 中的历史/支持性大文件，未触碰 `papers/`，未重跑 raw full-grid，稳定记录见 `results/nonpaper_results_internal_slimming_manifest_20260523.json`。

当前 Lens-B 科学解释锚点仍是：
`reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md`。

## Inputs Used

- `tmp/project_productization_cleanup_20260523/results_papers_externalization_manifest_20260523.csv`
- `tmp/project_productization_cleanup_20260523/results_papers_externalization_manifest_summary_20260523.json`
- `tmp/project_productization_cleanup_20260523/top_level_size_tiers.csv`
- local `du`, file-size, duplicate-hash, and reference-search checks

Manifest coverage from report 143:

| area | files | bytes |
| --- | ---: | ---: |
| `results/` + `papers/` total manifest | `3,647` | `12,117,002,343` |
| current full-grid seed raw/diagnostic lineage | `75` | `6,394,853,814` |
| current full-grid aggregation/postrun lineage | `14` | `5,248,840` |
| generated result artifacts | `535` | `4,434,327,679` |
| historical v2 generated evidence | `212` | `864,216,221` |
| paper extraction analysis artifacts | `2,620` | `244,337,925` |
| source paper binaries/references | `70` | `166,895,566` |

## Biggest Findings

### 1. `papers/analysis_full_v1/` Is The Cleanest First Win

`papers/analysis_full_v1/` has only about `233 MiB` apparent file bytes but consumes about `3.0 GiB` on this mounted volume because it contains `2,620` small files. A trial tar-gzip written outside the project produced a `212 MiB` archive.

This means the high-value action is not deleting papers. It is compacting the extracted paper-analysis tree.

Recommended safe mode:

- create `papers/analysis_full_v1_20260523.tar.gz`
- keep top-level ledgers that are directly referenced by reports/tests
- keep per-paper `analysis.md` cards that reports explicitly cite
- remove or archive expanded `page_renders/`, `figures/`, `text/`, `tables/`, and low-level evidence candidate folders
- add a restore note and hash manifest

Estimated practical saving: `2.5-2.8 GiB`.

Risk: medium. Reports and hardening code reference `papers/analysis_full_v1/...`; therefore this should be a deliberate pass with link checks after compaction.

### 2. Current Full-Grid Diagnostic CSVs Are Huge But Should Not Be Deleted

The six current diagnostic sidecars are each about `981 MiB`:

- `seed_11_fixed_660_gold_diagnostic_rows.csv`
- `seed_11_per_wavelength_gold_diagnostic_rows.csv`
- `seed_22_fixed_660_gold_diagnostic_rows.csv`
- `seed_22_per_wavelength_gold_diagnostic_rows.csv`
- `seed_33_fixed_660_gold_diagnostic_rows.csv`
- `seed_33_per_wavelength_gold_diagnostic_rows.csv`

They total about `5.9 GiB`. A 128 MiB sample gzip estimate on one diagnostic CSV gave a compression ratio of about `0.094`, implying about `92 MiB` compressed per file, or roughly `550-600 MiB` total.

Possible saving: about `5.2-5.4 GiB`.

Risk: high if done as blind deletion/rename. These diagnostic files preserve the compact distribution quantile fields that report 140 explicitly says are in diagnostic sidecars rather than raw CSVs. A safe compression pass would need:

- convert `.csv` to `.csv.gz`
- record new hashes
- update audit scripts to accept `.csv` or `.csv.gz`
- update report 140 / report 143 path wording if exact filenames change
- rerun full-grid integrity audit in read-only mode

Recommended action now: keep as-is until a dedicated “diagnostic CSV gzip compatibility” pass.

### 3. The v1 Full-Range Library Has Two Large Files With Different Risk

Large files:

- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_compact.pkl` — about `2.28 GiB`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv` — about `1.67 GiB`

The summary CSV is heavily referenced by tools, manifests, reports, and full-grid run plans. A gzip sample estimated it could shrink to about `402 MiB`.

The compact pickle is less directly referenced by current full-grid code, but may still support dashboard/precompute workflows. A gzip sample estimated it could shrink from `2.28 GiB` to about `1.47 GiB`.

Potential saving:

- summary CSV gzip: about `1.25 GiB`
- compact pickle gzip: about `0.8 GiB`
- removing compact pickle if proven regenerable and unused: up to `2.28 GiB`

Risk:

- summary CSV compression is medium/high because current CLI defaults and manifest paths name the `.csv`.
- compact pickle cleanup is medium; it needs dashboard/precompute usage verification first.

Recommended action: do not delete. First add loader fallback for `.csv` / `.csv.gz`, then compress the summary CSV; separately verify whether the compact pickle is still needed.

### 4. Historical v2 Full-Grid Artifacts Are Good Compression Candidates

`results/ev_nodi_realism_v2_full_grid_R5_v2/` is about `525 MiB` on disk. Its largest files are:

- `full_grid_v2_summary.csv` — about `332 MiB`; gzip sample estimate about `15 MiB`
- `full_grid_v2_case_manifest.csv` — about `176 MiB`

These are historical v2 evidence, while current reader interpretation is through reports 84/87/88/140. Review package code references smaller summary files in the same directory, not necessarily the whole raw full-grid CSV.

Potential saving: about `450-500 MiB`.

Risk: medium. It remains historical provenance and is referenced by reports and `post_v2_audit.py`; compression should update any exact path expectations.

### 5. Paper PDF Duplication Exists But Is Not The Main Problem

Duplicate paper binaries under root `papers/` and categorized `papers/paper- scattering/` account for roughly tens of MiB, not GiB. Examples:

- Pleet 2023 appears in three locations, about `11.4 MiB` total.
- Welsh/Jones 2020 appears in three locations, about `10.3 MiB` total.
- Several Tsuyama / iSCAT / EV PDFs appear twice.

Potential saving: about `40-60 MiB` if replaced by one canonical copy plus index links/manifest references.

Risk: low/medium. The categorized folder is useful for human browsing, so deleting duplicates may make the library less ergonomic unless an index replaces it.

Recommended action: lower priority than compacting `analysis_full_v1` and large CSVs.

## Suggested Slimming Tiers

| tier | action | estimated saving | risk | recommendation |
| --- | --- | ---: | --- | --- |
| A | compact `papers/analysis_full_v1` expanded extraction tree into archive, keep ledgers/cards | `2.5-2.8 GiB` | medium | best first pass |
| B | gzip current full-grid diagnostic sidecars with loader/doc updates | `5.2-5.4 GiB` | high | high value, needs dedicated compatibility pass |
| C | gzip v1 source summary CSV with `.csv.gz` fallback | `~1.25 GiB` | medium/high | useful after loader fallback |
| D | verify and compress/remove v1 compact pickle | `0.8-2.28 GiB` | medium | requires dashboard/precompute check |
| E | gzip historical v2 full-grid raw CSV/manifest | `0.45-0.5 GiB` | medium | good after current evidence is stable |
| F | de-duplicate paper PDFs into canonical copy + category index | `40-60 MiB` | low/medium | optional polish |
| G | remove old smoke/trial micro results | `<50 MiB` typical | low/medium | not worth doing first |

## Recommended Execution Order

1. **Paper extraction compaction pass**  
   Target `papers/analysis_full_v1/`. Keep the paper evidence in the project, but store heavy expanded artifacts in a compressed archive and keep only the files needed for current reports/tests open in the filesystem.

2. **CSV gzip compatibility pass**  
   Add helper logic so audit/postprocess tools accept both `.csv` and `.csv.gz`, then compress old/historical large CSVs first, not the current 3seed diagnostic sidecars.

3. **Current diagnostic compression pass**  
   Only after the compatibility pass, compress the six 3seed diagnostic CSVs and rerun report-140 integrity audit in read-only mode.

4. **v1 compact pickle verification pass**  
   Determine whether `ev_design_full_range..._compact.pkl` is still needed for dashboard/precompute. If not, replace it with a manifest note and regeneration command; if yes, compress it with a compatible loader.

5. **Paper PDF de-dup pass**  
   Keep one canonical paper binary per SHA-256 and replace category duplicates with manifest entries or symlinks if the filesystem/tooling supports them.

## Do-Not-Delete List For Now

Do not delete in a quick cleanup pass:

- `results/exhaustive_ev_gold_fullgrid_shared_dual_10000e_seed*_16worker_20260518/`
- `results/exhaustive_ev_gold_fullgrid_shared_dual_3seed_10000e_*_aggregation_20260518/`
- `results/exhaustive_ev_gold_fullgrid_shared_dual_3seed_10000e_*_20260523.*`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv`
- `papers/provenance/`
- top-level `papers/analysis_full_v1/*.csv`, `*.json`, and report-cited `analysis.md` files until a replacement index exists

## Commands Run

```bash
du -sh results/* papers/* 2>/dev/null | sort -h | tail -80
find results papers -maxdepth 2 -type f -not -name '._*' -print0 | xargs -0 ls -lh 2>/dev/null | sort -k5 -hr | head -80
python - <<'PY'
# aggregate SHA-256 manifest by top-level result/paper path and role
PY
find papers/analysis_full_v1 -maxdepth 2 -type d -name page_renders -print0 | xargs -0 du -ch 2>/dev/null | tail -1
find papers/analysis_full_v1 -maxdepth 2 -type d -name figures -print0 | xargs -0 du -ch 2>/dev/null | tail -1
find papers/analysis_full_v1 -maxdepth 2 -type d -name text -print0 | xargs -0 du -ch 2>/dev/null | tail -1
find papers/analysis_full_v1 -maxdepth 2 -type d -name evidence -print0 | xargs -0 du -ch 2>/dev/null | tail -1
find papers/analysis_full_v1 -maxdepth 2 -type d -name tables -print0 | xargs -0 du -ch 2>/dev/null | tail -1
tar -czf /tmp/nodi_papers_analysis_full_v1_20260523.tar.gz -C papers analysis_full_v1
rm -f /tmp/nodi_papers_analysis_full_v1_20260523.tar.gz
python - <<'PY'
# gzip sample estimates for large CSV / pickle files
PY
```

No files under `results/` or `papers/` were deleted or modified.
