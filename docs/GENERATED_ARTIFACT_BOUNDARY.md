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
- Large regenerated result directories should stay local unless a specific
  provenance manifest or regression test explicitly requires a tracked file.

Cleanup policy:

- Delete caches and OS metadata freely: `__pycache__/`, `.pytest_cache/`,
  `.ruff_cache/`, `.mypy_cache/`, `.DS_Store`, and `._*`.
- Do not delete tracked `results/post_v2_*` exception files without checking the
  paired schema tests and `nodi_simulator/post_v2_entrypoint_registry.py`.
- Prefer adding a manifest/schema test before promoting any generated result
  into source review.
