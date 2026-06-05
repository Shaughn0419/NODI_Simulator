# Full Project Code / Documentation Cleanup Audit 2026-05-23

## Executive Status

本轮审查的直接目标是：在不重跑原始 full-grid 计算、不覆盖 completed raw results、不改动物理/科学范围的前提下，复核工程代码与说明文件，清理安全冗余，把读者入口推进到 `reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md` 的最新状态。

结论：本轮没有发现需要立即修复的 Python 语法错误、Markdown 本地链接断裂、secret-like 凭据泄漏或会改变当前全量分析结论的文档矛盾。已清理机器生成冗余（AppleDouble `._*` 与 `__pycache__/`），已更新入口说明、旧 Lens-B 报告覆盖说明和 generated-artifact 边界。保留下来的重复编号、历史 archive 重复文件、calibration/export 模板副本和大型长函数属于 provenance / 已知技术债，不在本轮无破坏清理中删除或重构。

## Scope And Non-Destructive Boundary

审查覆盖当前 source-reviewed 工作区，而不是把 generated evidence 当成源码逐行改写：

- 源码与测试：`nodi_simulator/`, `dashboard/`, `tools/`, `tests/`
- 文档与入口：`README.md`, `文档导航.md`, `docs/`, `guides/`, current reader-facing `reports/`
- 配置与小型文本工件：`.py`, `.md`, `.json`, `.toml`, `.ini`, `.yml`, `.yaml`, `.bat`, `.command`, `.txt`, `.csv`, `.sha256`

刻意排除的 generated / local-only 区域：

- `.git/`, `.claude/`, `.omx/`
- `.venv/`, `.venv-tests/`, `.pytest_vendor/`
- `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`, `.pdf_output/`, `__pycache__/`
- `papers/`, `results/`, `review_bundles/`, `tmp/`

`results/exhaustive_ev_gold_fullgrid_shared_dual_*` 原始结果和聚合结果只作为 report 140 已审计证据引用；本轮没有重跑 raw full-grid、没有覆盖 raw/diagnostic CSV、没有删除 result lineage。

## Cleanup Plan Used Before Edits

1. 先跑完整测试基线，避免在不知情状态下整理文档。
2. 用只读审计脚本建立 file inventory、line flags、Python AST metrics、Markdown link map、duplicate hash / basename / report-number map。
3. 只删除明确机器生成且 policy 允许自由删除的缓存/OS 元数据。
4. 只更新当前入口文档和旧报告的覆盖说明，不改历史 raw evidence。
5. 重跑审计和静态/测试验证；任何失败先修复再总结。

## Audit Method

审计脚本：

- `tmp/full_project_source_doc_audit_20260523.py`

输出目录：

- `tmp/full_project_review_20260523/summary.json`
- `tmp/full_project_review_20260523/file_inventory.csv`
- `tmp/full_project_review_20260523/line_flags.csv`
- `tmp/full_project_review_20260523/python_ast_metrics.csv`
- `tmp/full_project_review_20260523/markdown_links.csv`
- `tmp/full_project_review_20260523/broken_markdown_links.csv`
- `tmp/full_project_review_20260523/duplicate_hashes.csv`
- `tmp/full_project_review_20260523/duplicate_basenames.csv`
- `tmp/full_project_review_20260523/duplicate_report_numbers.csv`

脚本做的是可追溯的机械逐行扫描：逐文件读取、逐行标记 decode replacement / tab / very long line / library print / TODO / bare pass / secret-like pattern / forbidden-claim-positive wording；Python 文件额外做 AST parse 和长函数定位；Markdown 文件额外解析本地链接是否存在。这个流程不能替代未来对每个长函数的人工重构设计，但能保证本轮入口文档更新没有跳过基础完整性检查。

## Findings

本轮审计后关键结果：

| item | result |
| --- | --- |
| Scanned source/doc/config files | 984 |
| Scanned lines | 256,371 |
| Python files | 386 |
| Markdown files | 311 |
| Python syntax errors | 0 |
| Markdown local broken links | 0 after report 141 creation and final audit |
| Mechanical line flags | 2,433 retained for future triage |
| Long Python functions flagged | 162 |
| Duplicate content-hash groups | 14 retained by provenance/template policy |
| Duplicate report-number groups | 5 retained as historical numbering collisions |
| Secret-like credential flags | 0 material findings |
| Raw full-grid rerun | not run |
| Post-processing rerun | not run |
| Deleted safe redundancy | AppleDouble `._*`, `__pycache__/` |
| Kept by design | historical report-number collisions, archive duplicates, calibration/export template mirrors, empty package `__init__.py` sentinels |

重要已知技术债：

- `nodi_simulator/parameter_sweep.py::run_single_case_batch` 等长函数仍然很大；直接拆分会影响 shared simulation behavior，未在本轮无破坏清理中重构。
- `tools/audits/tsuyama_detection_rate_calibration.py::candidate_catalog` 等工具函数较长；它们是历史审计/候选目录生成逻辑，未在没有专门 regression spec 的情况下拆动。
- reports 100 / 124 / 125 / 126 / 127 存在编号碰撞；这些是历史阶段编号重用，不是当前入口冲突。本轮在 `文档导航.md` 明确优先级，而不是重命名历史报告。
- `calibration/` 与 `exports/calibration/` 有模板镜像副本；它们服务不同使用面，未作为重复垃圾删除。

## Documentation Updates

已更新：

- `README.md`
  - 当前项目状态改为 report 140 的 3seed × 10000e exhaustive EV+gold full-grid 结论。
  - 明确 `fixed_660_gold` / `per_wavelength_gold` 是 normalization views，不是独立 physical campaigns。
  - 把 report 140 放到 reader entry 第一位，并把 report 88 / 100 降为背景与历史 overlay。
  - 更新当前科学 bottom line：fixed view 指向 404/W500 mid-depth；per-wavelength view 保留 660/W800 D1400-D1500；488/532 仍 control/reference。
- `文档导航.md`
  - 第一屏加入 report 140 提示、双 normalization-view 边界和最新 route-family 解释。
  - 当前读者入口把 report 140 放在 report 88 / 100 之前。
  - 使用优先级改为：当前代码/测试 → report 140 → report 88/100 → 其它治理文档。
- `reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`
  - 顶部加入 2026-05-23 覆盖说明，防止读者把 v5.2.8 的 1000e B6/B7 语言误当最新 Lens-B full-grid 结论。
- `reports/100_EV_NODI_lens_b_tau1ms_stage_b6_only_analysis.md`
  - 顶部加入 2026-05-23 覆盖说明，明确它是历史单 seed 1000e overlay，最新 robust conclusion 见 report 140。
- `docs/GENERATED_ARTIFACT_BOUNDARY.md`
  - 增加 exhaustive Lens-B EV+gold 3seed 10000e result-lineage policy，明确这些目录是 generated evidence artifact，不在 cleanup 中覆盖或删除。

## Full-Grid Analysis Documentation Status

当前 full-grid 主报告仍是：

- `reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md`

本轮没有改写 report 140 的科学结论，因为它已经完成 output integrity audit、cross-view comparison、prior-conclusion delta 和 no-rerun caveats。入口文档和旧报告覆盖说明已改成指向 report 140，读者不会再只停留在 report 88/100 的 1000e 单 seed 状态。

必须保留的 claim boundary：

- Level-1 no-measured-data relative/proxy evidence only。
- 不得宣称任何高阶实测性能、detector voltage、photon count、POD amplitude、EV biological specificity 或 clinical/diagnostic performance。
- selected-annulus 是 event-position / analysis-window lens，不是 optical BFP annulus。
- `fixed_660_gold` 和 `per_wavelength_gold` 是共享物理事件上的 analysis / normalization views，不能双倍计数物理随机样本。
- gold rows 是 anchor / Tsuyama diagnostics，不是 EV final recommendation。

## Verification

已执行验证分为四层：

- static checks: `ruff check .`, `python -m pyright`, `python -m mypy`
- full regression: `python tests/run_tests.py --workers 7`
- release claim scanner / verifier path: `python -m pytest tests/test_review_package_claim_scan.py tests/test_verify_review_package_cli.py tests/test_review_package_manifest.py -q`
- documentation invariant loop: 50 passes over README / 文档导航 / generated-artifact boundary / reports 88 / 100 / 140 / 141

最终验证结果记录在本报告末尾的 `Final Validation Snapshot`。

## Commands Run

```bash
python tests/run_tests.py --workers 7
python tmp/full_project_source_doc_audit_20260523.py
find . \( -path './.git' -o -path './.claude' -o -path './.omx' -o -path './.venv' -o -path './.venv-tests' -o -path './.pytest_vendor' -o -path './results' -o -path './papers' -o -path './tmp' \) -prune -o \( -name '._*' -o -name '__pycache__' \) -exec rm -rf {} +
python tmp/full_project_source_doc_audit_20260523.py
ruff check .
python -m pyright
python -m mypy
python -m pytest tests/test_review_package_claim_scan.py tests/test_verify_review_package_cli.py tests/test_review_package_manifest.py -q
python tests/run_tests.py --workers 7
rm -rf .pytest_cache
find . \( -path './.git' -o -path './.claude' -o -path './.omx' -o -path './.venv' -o -path './.venv-tests' -o -path './.pytest_vendor' -o -path './results' -o -path './papers' -o -path './tmp' \) -prune -o \( -name '._*' -o -name '__pycache__' \) -exec rm -rf {} +
python tmp/full_project_source_doc_audit_20260523.py
python - <<'PY'
# 50-pass documentation invariant self-review.
from pathlib import Path
import json

root = Path('.')
required = {
    'readme': root / 'README.md',
    'nav': root / '文档导航.md',
    'boundary': root / 'docs/GENERATED_ARTIFACT_BOUNDARY.md',
    'r88': root / 'reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md',
    'r100': root / 'reports/100_EV_NODI_lens_b_tau1ms_stage_b6_only_analysis.md',
    'r140': root / 'reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md',
    'r141': root / 'reports/141_full_project_code_doc_cleanup_audit_20260523.md',
}
summary = json.loads((root / 'tmp/full_project_review_20260523/summary.json').read_text(encoding='utf-8'))
for i in range(50):
    texts = {name: path.read_text(encoding='utf-8') for name, path in required.items()}
    assert summary['python_syntax_error_count'] == 0
    assert summary['broken_markdown_link_count'] == 0
    assert 'reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md' in texts['readme']
    assert 'reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md' in texts['nav']
    assert '2026-05-23 覆盖说明' in texts['r88']
    assert '2026-05-23 覆盖说明' in texts['r100']
    assert 'fixed_660_gold' in texts['readme'] and 'per_wavelength_gold' in texts['readme']
    assert 'analysis views' in texts['r140'] and '960,960,000' in texts['r140']
    assert 'not an optical BFP annulus' in texts['r140']
print('50-pass documentation invariant self-review passed')
PY
```

No forbidden raw full-grid command was run:

```bash
python tools/lens_b_ev_gold_fullgrid_runner.py --mode full ...
python tools/run_pre3seed_3seed_10000e_from_manifest.py --execute ...
```

## Final Validation Snapshot

This section is updated after the final audit/test pass.

| check | status |
| --- | --- |
| `python tmp/full_project_source_doc_audit_20260523.py` | pass: 984 files, 256,371 lines, 0 Python syntax errors, 0 broken Markdown links |
| `ruff check .` | pass |
| `python -m pyright` | pass: 0 errors, 0 warnings, 0 informations |
| `python -m mypy` | pass: no issues in 6 source files |
| targeted claim-scan verifier tests | pass: 10 passed |
| `python tests/run_tests.py --workers 7` | pass: AppTest 5 passed; non-AppTest 1410 passed |
| 50-pass document invariant self-review | pass |

## Residual Risks

- 本轮审查没有安全地拆分大型历史函数；这需要独立 refactor plan、行为锁定测试和分步重构。
- 历史 report-number collision 保留；重命名会破坏旧引用和审阅 provenance，收益低于风险。
- generated `results/` 原始数据没有逐行打印或改写；完整性解释以 report 140 的 audit manifest 和 aggregation artifacts 为证据。
- 机械逐行扫描能发现结构问题、链接问题、语法问题和文字风险，但不能证明每条历史说明都已经被人工重写成最优表达；本轮通过入口优先级和覆盖说明防止旧结论误导当前读者。
