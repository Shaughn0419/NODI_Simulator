# Project Productization Cleanup 2026-05-23

## Executive Status

本轮按“把工程变成相对成品、减少臃肿”的目标执行了第一轮稳态清理。结论：已清理明确安全的本地缓存、导出包、review bundle、AppleDouble 元数据和源码侧 `__pycache__/`；没有删除或覆盖 `results/` raw / diagnostic / aggregation 证据链，没有删除 `papers/` 文献证据链，没有重跑任何 raw full-grid 计算。当前源码与文档入口仍以 report 140 为 Lens-B 最新科学解释入口。

当前 Lens-B 解释锚点：
`reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md`。

清理前工作区顶层体量约 `45,616,128 KiB`，清理后约 `45,218,816 KiB`，本轮净释放约 `397,312 KiB`（约 `388 MiB`，已计入新增 evidence manifest 的体量）。剩余体量主要不是源码冗余，而是需要受控外置的证据/运行环境：`results/` 约 `12,158 MiB`，`papers/` 约 `3,251 MiB`，`.venv/` 约 `21,089 MiB`，`.venv-tests/` 约 `1,090 MiB`，`.pytest_vendor/` 约 `712 MiB`，`.claude/` 约 `1,099 MiB`。

## Cleanup Plan Used Before Edits

1. 先锁定行为和文档当前性：运行关键 claim / full-grid guard 测试与逐 Markdown 当前性审计。
2. 生成 productization 清单：把顶层目录分成 source-reviewed、safe local generated、preserve local runtime、externalize-with-manifest。
3. 只删除明确安全的本地生成物：cache、临时导出、review bundle、AppleDouble 和源码侧 `__pycache__/`。
4. 对 `results/`、`papers/`、`.venv/`、`.claude/`、`.omx/` 等大目录只记录，不直接删除。
5. 写出成品化报告与后续深度重构路线，再跑静态/测试/文档复核。

## Behavior Lock

清理前已运行：

```bash
python -m pytest tests/test_review_package_claim_scan.py tests/test_verify_review_package_cli.py tests/test_review_package_manifest.py tests/test_exhaustive_fullgrid_chain_guards.py -q
python tmp/current_documentation_status_audit_20260523.py
```

结果：

- 关键保护测试：`23 passed`
- Markdown 当前性审计：`312` 个 Markdown，`0` 个当前入口缺少 report 140 anchor

## Artifact Inventory Produced

清单脚本：

- `tmp/project_productization_cleanup_20260523.py`

输出：

- `tmp/project_productization_cleanup_20260523/summary.json`
- `tmp/project_productization_cleanup_20260523/top_level_size_tiers.csv`
- `tmp/project_productization_cleanup_20260523/cleanup_action_candidates.csv`
- `tmp/project_productization_cleanup_20260523/tracked_top_level_counts.csv`
- `tmp/project_productization_cleanup_20260523/appledouble_candidates.csv`
- `tmp/project_productization_cleanup_20260523/long_function_top.csv`
- `tmp/project_productization_cleanup_20260523/results_papers_externalization_manifest_20260523.csv`
- `tmp/project_productization_cleanup_20260523/results_papers_externalization_manifest_summary_20260523.json`

最终清单摘要：

| item | result |
| --- | ---: |
| top-level total after cleanup | `45,218,816 KiB` |
| safe-remove candidates remaining | `0 KiB` |
| AppleDouble metadata remaining | `0` |
| preserve-runtime optional cleanup tier | `24,799,232 KiB` |
| externalize-with-manifest tier | `15,778,816 KiB` |
| long functions still flagged | `162` |

Evidence externalization manifest:

| item | result |
| --- | ---: |
| `results/` + `papers/` files hashed | `3,647` |
| bytes covered by SHA-256 manifest | `12,117,002,343` |
| current full-grid seed raw/diagnostic lineage | `75` files / `6,394,853,814` bytes |
| current full-grid aggregation/postrun lineage | `14` files / `5,248,840` bytes |
| generated result artifacts | `535` files / `4,434,327,679` bytes |
| source paper binaries/references | `70` files / `166,895,566` bytes |
| paper extraction analysis artifacts | `2,620` files / `244,337,925` bytes |

## Cleanup Performed

已删除：

- `.pytest_cache/`
- `.ruff_cache/`
- `.mypy_cache/`
- `.pdf_output/`
- `review_bundles/`
- `exports/`
- all `._*` AppleDouble metadata outside `.git` source history requirements
- source-side `__pycache__/` directories, excluding virtualenv/vendor/result/paper traversals
- `.DS_Store` if present

本轮没有删除：

- `results/`
- `papers/`
- `.venv/`
- `.venv-tests/`
- `.pytest_vendor/`
- `.claude/`
- `.omx/`
- ignored historical archive data

这些保留不是因为它们都应该长期留在成品源码包里，而是因为它们需要单独的 hash manifest / relocation / rebuild proof，不能在同一轮 cleanup 中无差别删除。

## Productization Structure Decision

成品化后建议把工程视为三层，而不是一个混合目录：

| tier | examples | policy |
| --- | --- | --- |
| source-reviewed core | `nodi_simulator/`, `dashboard/`, `tools/`, `tests/`, `docs/`, `guides/`, current reports | 留在源码工程；接受 lint/type/test/code review |
| evidence artifacts | `results/`, `papers/`, historical raw sidecars | 先生成 hash manifest，再外置或单独 artifact bundle；不在 cleanup 中直接删除 |
| local runtime/generated | `.venv/`, `.venv-tests/`, `.pytest_vendor/`, `.claude/`, `.omx/`, caches, exports | caches 可删；runtime/env 只有在重建路径验证后才删 |

## Remaining Bloat By Category

1. **Local runtime/dependency bulk**：`.venv/`, `.venv-tests/`, `.pytest_vendor/` 合计约 `22.9 GiB`。这不是源码冗余，但占据最大磁盘空间。若要进一步瘦身，应先确认当前系统 Python / `pyproject.toml` 可重建测试环境，再删除。
2. **Evidence artifact bulk**：`results/` + `papers/` 合计约 `15.0 GiB`。它们是科学证据链，不应直接删除。下一步应创建 external evidence bundle manifest。
3. **Source cognitive bulk**：`162` 个长函数仍在，主要集中在 `nodi_simulator/parameter_sweep.py`, `nodi_simulator/realism_v2.py`, `dashboard/precompute.py`, `dashboard/backend.py`, dashboard panels 和 one-shot audit tools。
4. **Historical documentation bulk**：历史 reports / archive 仍保留 provenance。当前入口已经由 README、`文档导航.md`、reports 140/141/142/143 限定，不再需要把旧报告逐个重写成当前结论。

## Long-Function Refactor Queue

优先级最高的深度重构目标：

| priority | file | function | lines | recommended handling |
| --- | --- | --- | ---: | --- |
| P1 | `nodi_simulator/parameter_sweep.py` | `run_single_case_batch` | `2452` | 先加 characterization tests，再拆 shared-state construction / event loop / aggregation / metadata emission |
| P1 | `nodi_simulator/parameter_sweep.py` | `_simulate_stream_event_block` | `586` | 拆 event-state input object 与 result assembler |
| P1 | `nodi_simulator/parameter_sweep.py` | `simulate_one_event` | `527` | 拆 physics components，但保持 numerical snapshot tests |
| P2 | `dashboard/precompute.py` | `results_to_dataframe` | `748` | 拆 schema mapping / derived metrics / health payload |
| P2 | `dashboard/backend.py` | `build_physics_breakdown` | `923` | 拆 view-model builders；不要在 UI path 里重算物理 |
| P2 | `dashboard/panels/explorer.py` | `render_explorer` | `755` | 拆 controls / summary / charts；保留 AppTest smoke |
| P3 | `nodi_simulator/realism_v2.py` | multiple historical audit runners | `500-862` | 若非 current production path，优先归档或标 lifecycle，不急于重构 |
| P3 | `tools/one_shot/*` | one-shot report builders | `400-603` | 归入 historical tools 或保留 read-only provenance |

## Next Safe Cleanup Pass

下一轮推荐顺序：

1. **External evidence relocation pass**：`results/` 和 `papers/` 的 path / size / sha256 / role manifest 已生成；下一步是在不改 hash 的前提下把大型 raw artifacts 移出源码工作区，并更新恢复说明。
2. **Runtime rebuild pass**：确认从空环境执行 `python -m venv .venv && python -m pip install -e ".[dev]"` 后测试可运行，再删除旧 `.venv/`, `.venv-tests/`, `.pytest_vendor/`。
3. **Tools lifecycle pass**：把 production CLI、postprocess、audit、one-shot historical tools 分层，给每个 current CLI 加 smoke test。
4. **Parameter-sweep refactor pass**：先锁 numeric behavior，再拆 `run_single_case_batch`。
5. **Dashboard payload refactor pass**：拆 `dashboard/precompute.py` 与 `dashboard/backend.py`，减少 UI 侧认知负担。

## Commands Run

```bash
git status --short --ignored
du -sh . ./* ./.??* 2>/dev/null | sort -h
git clean -ndX
python -m pytest tests/test_review_package_claim_scan.py tests/test_verify_review_package_cli.py tests/test_review_package_manifest.py tests/test_exhaustive_fullgrid_chain_guards.py -q
python tmp/current_documentation_status_audit_20260523.py
python tmp/project_productization_cleanup_20260523.py
python tmp/evidence_externalization_manifest_20260523.py
rm -rf .pytest_cache .ruff_cache .mypy_cache .pdf_output review_bundles exports
find . -path './.git' -prune -o -name '._*' -print -delete
find . \( -path './.git' -o -path './.venv' -o -path './.venv-tests' -o -path './.pytest_vendor' -o -path './results' -o -path './papers' \) -prune -o -type d -name '__pycache__' -exec rm -rf {} +
find . -path './.git' -prune -o -name '.DS_Store' -print -delete
python tmp/project_productization_cleanup_20260523.py
python tools/generate_review_package_manifest.py
ruff check .
python -m pyright
python -m mypy
python -m pytest tests/test_review_package_claim_scan.py tests/test_verify_review_package_cli.py tests/test_review_package_manifest.py tests/test_exhaustive_fullgrid_chain_guards.py -q
python tests/run_tests.py --workers 7
python tmp/full_project_source_doc_audit_20260523.py
python tmp/current_documentation_status_audit_20260523.py
git diff --check
```

No raw full-grid calculation was run.

Forbidden commands not run:

```bash
python tools/lens_b_ev_gold_fullgrid_runner.py --mode full ...
python tools/run_pre3seed_3seed_10000e_from_manifest.py --execute ...
```

## Residual Risks

- The project is less noisy on disk, but not yet a small source-only repository because `results/`, `papers/`, and local runtime folders remain intentionally preserved.
- Deleting `.venv/` or `.pytest_vendor/` could save much more space, but should wait until a clean rebuild/test lane proves replacement is available.
- Moving `results/` and `papers/` should be done with hashes and references because report 140 depends on that evidence lineage.
- Long-function debt remains; this pass identifies the queue but does not risk broad behavior-changing refactors without tighter tests.

## Final Validation Snapshot

| check | result |
| --- | --- |
| `ruff check .` | pass |
| `python -m pyright` | pass: 0 errors, 0 warnings, 0 informations |
| `python -m mypy` | pass: no issues in 6 source files |
| review package / full-grid guard tests | pass: 23 passed after regenerating review package hashes |
| `python tests/run_tests.py --workers 7` | pass: AppTest 5 passed; non-AppTest 1410 passed |
| full source/doc audit | pass: 975 source/doc/config files, 313 Markdown files, 0 Python syntax errors, 0 Markdown local broken links |
| Markdown currentness audit | pass: 313 Markdown files, 0 current-entry files missing report 140 anchor |
| productization inventory | pass: safe-remove candidates 0 KiB; externalize tier 15,778,816 KiB; runtime-preserve tier 24,799,232 KiB |
| evidence externalization manifest | pass: 3,647 `results/` + `papers/` files hashed |
| final diff whitespace check | pass |

Note: full tests recreate `.pytest_cache/` and mounted-volume AppleDouble metadata; those were removed again after validation.
