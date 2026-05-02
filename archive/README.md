# Archive

<!-- DOCSYNC:START -->
> 归档提示（2026-04-28）：本文保留历史快照，不覆盖现行代码事实。当前主线已更新到 EV/NODI relative design gate 拆分、detector caution 分层、calibrated BFP ROI mask 到 Tsuyama 1D projected ROI、完整 governance diagnostics 导出；验证基线为 `pytest -q` = `509 passed`，`ruff check .` / `pyright` 通过。现行结论以根目录 `README.md`、`文档导航.md`、`00/24/42/43` 和代码测试为准。
<!-- DOCSYNC:END -->

This directory stores historical notes, long-form snapshots, and design drafts.

Rules:

- Archive files preserve historical context and may mention old result libraries or old code states.
- Do not treat archive conclusions as current truth unless a live document explicitly re-adopts them.
- Current entry points live in the repository root, [guides/](../guides/), [dashboard/](../dashboard/), and [reports/current/](../reports/current/).

Contents:

- `dashboard/` — historical dashboard plans and `.full.md` drafts.
- `reports/` — historical analysis reports, including old full-library selection reports.
- `tsuyama/` — Tsuyama / Mawatari audit notes and paper-aligned experiments.
- `docx/` — converted source documents and document artifacts.
