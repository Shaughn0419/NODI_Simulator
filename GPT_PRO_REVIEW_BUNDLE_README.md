# GPT-Pro Review Bundle

This bundle was originally intended for external GPT-Pro review of report 88.
As of 2026-06-12, the current no-data closure set is report 140 + report 147
+ report 148. Report 88 and report 100 remain historical/background reports,
not current route-conclusion authorities.

Primary copyable prompt:

```text
reports/124_GPT_PRO_REVIEW_PROMPT_FOR_REPORT_88.md
```

Primary reports:

```text
reports/140_exhaustive_ev_gold_fullgrid_3seed_10000e_postrun_analysis_20260523.md
reports/147_detector_forward_identity_full_chain_adversarial_audit_synthesis_20260610.md
reports/148_extreme_simulation_roadmap_post_audit_20260610.md
```

Historical/background reports:

```text
reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md
reports/100_EV_NODI_lens_b_tau1ms_stage_b6_only_analysis.md
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
evidence, measured blank/FPR safety evidence, true EV concentration evidence,
biological specificity evidence, detector-resolved winner evidence, or NODI
heterodyne gain evidence.

Current-state note: the final reader-facing conclusion is `candidate families
under detector surrogate`, not a single absolute route winner. Use `404/W500`
as the fixed-view candidate family and `660/W800` as the per-wavelength-view
candidate family. `fixed_660_gold` and `per_wavelength_gold` are normalization
views over shared physical events, not independent event campaigns. EV rows are
recommendation rows; gold rows are diagnostics; 488/532 are control/trend
wavelengths. R1 and C/D×V2 are deferred outside the narrowed no-data sealing
gate.
