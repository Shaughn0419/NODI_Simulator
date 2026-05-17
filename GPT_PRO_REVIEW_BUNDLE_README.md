# GPT-Pro Review Bundle

This bundle is intended for external GPT-Pro review of report 88 v5.2.6 and the
supporting EV/NODI simulator code, tests, reports, configs, papers, and result
artifacts.

Primary copyable prompt:

```text
reports/124_GPT_PRO_REVIEW_PROMPT_FOR_REPORT_88.md
```

Primary report:

```text
reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md
```

Paper-story outline for later discussion:

```text
reports/123_EV_NODI_paper_story_outline_for_later_discussion.md
```

Run the full test suite from the unpacked bundle root:

```bash
python tests/run_tests.py --workers 7
```

If the environment is missing dependencies, install the project dependencies
declared in `pyproject.toml` first. The bundled `.pytest_vendor/` directory is
included only to provide pytest/xdist support for the local test runner; it does
not replace scientific runtime dependencies such as NumPy, pandas, SciPy,
Plotly, or Streamlit.

The package includes a small local Git metadata directory so tests that verify
review-manifest commit reachability can run after extraction. It is not intended
as a history-preserving repository clone.

Claim boundary: this is a no-measured-data relative-audit review bundle. It must
not be interpreted as calibrated physical prediction evidence, absolute SNR/LOD
evidence, measured blank safety evidence, true EV concentration evidence, or
biological specificity evidence.

Lens-B current-state note: report 88 v5.2.6 includes the completed one-seed
EV+gold full-grid application under
`results/lens_b_ev_gold_fullgrid_1seed_20260513/`. EV recommendation rows must
be read from EV/exosome rows only; gold rows are diagnostics only; 488/532 are
control/trend wavelengths, not final recommendation wavelengths.
