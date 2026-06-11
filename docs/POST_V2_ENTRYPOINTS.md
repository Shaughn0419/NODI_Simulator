# Post-v2 entrypoint lifecycle

2026-06-12 note: this is a source-code lifecycle contract for post-v2 entrypoint
modules. It does not define the current scientific conclusion. Current no-data
claim wording lives in report 140 plus the 147/148 closure set.

The package-level `nodi_simulator/post_v2_*.py` files are not disposable scratch
files. They are active review-package contracts with paired generator and/or
verifier wrappers under `tools/`, and many are imported directly by tests.

Deletion policy:

- Do not delete a `post_v2_*.py` module unless it is first removed from
  `nodi_simulator/post_v2_entrypoint_registry.py` and the registry test proves
  that no package/tool wrapper remains uncovered.
- Treat `active_review_package_contract` modules as public artifact writers for
  existing review outputs.
- Treat `active_bounded_solver_program` modules as frozen-lane contract writers:
  clean internals cautiously, but preserve filenames, CLI wrappers, output
  filenames, schemas, and verifier behavior.
- Generated CSV/JSON/Markdown outputs under `results/post_v2_*` remain
  generated artifacts; source code and wrapper lifecycle are tracked by the
  registry, not inferred from result directory timestamps.
