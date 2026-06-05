# Generated artifact boundary

This repository separates source-of-truth code and documentation from generated
or machine-local artifacts.

Source-reviewed areas:

- `nodi_simulator/`, `dashboard/`, `tools/`, and `tests/`
- `docs/`, `guides/`, and current reader-facing `reports/`
- selected provenance manifests that are explicitly unignored in `.gitignore`

Generated or machine-local areas:

- `results/`: computed CSV/JSON/Markdown evidence artifacts
- `exports/`: local export bundles and dashboard data extracts
- `review_bundles/`: packaged review zips and staging directories
- `.pdf_output/`: extracted paper text/images
- `.claude/`, `.omx/`, `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/`
- virtual environments and vendored test runtimes such as `.venv/`,
  `.venv-tests/`, and `.pytest_vendor/`

Result-lineage policy:

- `results/ev_nodi_realism_v2_*` directories are v2 evidence lineage, not
  reader entry points.
- `results/post_v2_*` directories are review/audit/trace records. They are not
  measured data and must not be treated as calibrated detector outputs.
- `results/exhaustive_ev_gold_fullgrid_shared_dual_10000e_seed*_16worker_20260518`
  and
  `results/exhaustive_ev_gold_fullgrid_shared_dual_3seed_10000e_*_aggregation_20260518`
  are the current exhaustive Lens-B EV+gold 3-seed 10000e evidence lineage.
  They remain generated evidence artifacts; use report 140 for reader-facing
  interpretation and do not edit or overwrite raw run outputs during cleanup.
- Large regenerated result directories should stay local unless a specific
  provenance manifest or regression test explicitly requires a tracked file.

Cleanup policy:

- Delete caches and OS metadata freely: `__pycache__/`, `.pytest_cache/`,
  `.ruff_cache/`, `.mypy_cache/`, `.DS_Store`, and `._*`.
- Local exports and generated review bundles (`exports/`, `review_bundles/`,
  `.pdf_output/`) are safe to remove during productization cleanup when no
  active handoff explicitly names them.
- Do not remove local runtime/dependency folders such as `.venv/`,
  `.venv-tests/`, `.pytest_vendor/`, `.claude/`, or `.omx/` as part of an
  automated cleanup pass unless a rebuild or runtime-state replacement has
  been verified.
- Do not delete or move `results/` or `papers/` directly. First write a
  path/size/hash/role manifest and update reader-facing references so report
  lineage remains auditable after externalization.
- Do not delete tracked `results/post_v2_*` exception files without checking the
  paired schema tests and `nodi_simulator/post_v2_entrypoint_registry.py`.
- Prefer adding a manifest/schema test before promoting any generated result
  into source review.

The 2026-05-23 productization cleanup ledger is
`reports/143_project_productization_cleanup_20260523.md`.
