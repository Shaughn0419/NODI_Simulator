# Tools Directory Tiers

Tool entrypoints are grouped by expected maintenance level:

- `benchmarks/`: long-lived benchmark and performance experiment entrypoints.
- `audits/`: repeatable analysis or audit entrypoints used by tests, reports, or routine review.
- `one_shot/`: historical generation/adjudication scripts kept for provenance.

Shared helpers that are safe across tiers live in `tools/_common.py`.

Legacy `tools/<name>.py` entrypoints are retained as compatibility wrappers.
New automation and documentation should point at the tiered paths directly.
For `one_shot/` writers, both canonical tiered scripts and legacy wrappers must
support safe `--help` and refuse accidental writes without explicit
`--execute`. When automation intentionally regenerates historical artifacts,
run the canonical module from the repository root with
`python -m tools.one_shot.<module> --execute ...`, or call the direct script
path with `--execute`. Do not add an environment-variable bypass for one-shot
execution, because that hides write intent from command logs and shell history.

Legacy root tool wrappers are scheduled for removal after 2026-12. Earlier
removal is acceptable if internal automation no longer references
`tools/<name>.py`, external collaborators have had at least 30 days of
migration notice, and the tiered paths remain covered by the wrapper
completeness test.
