# Non-paper results slimming report, 2026-05-23

## Executive verdict

After freezing `papers/`, I completed one reversible non-paper slimming pass focused on `results/`. The pass did not rerun any raw full-grid calculation and did not touch the current 3seed 10000e raw or diagnostic evidence. It compressed four large historical/result-support artifacts with gzip payload verification, added transparent `.csv.gz` / `.pkl.gz` fallback readers where those artifacts are still consumed, and saved `1,617,716,861` bytes (`1542.775 MiB`, `1.506616 GiB`) of apparent file size.

## Scope

Included:

- `results/ev_nodi_realism_v2_full_grid_R5_v2/full_grid_v2_case_manifest.csv`
- `results/ev_nodi_realism_v2_full_grid_R5_v2/full_grid_v2_summary.csv`
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_compact.pkl`
- `results/lens_b_fixed660_tau1ms_ev_gold_fullgrid_1000e_seed42_compact.pkl`

Explicitly excluded:

- `papers/` and all paper extraction/provenance content
- current exhaustive 3seed 10000e raw and diagnostic CSV evidence
- `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv`, because it remains an exact review-package and route-source path
- any raw full-grid calculation rerun

## Compatibility updates

Implemented fallback artifact readers before removing uncompressed copies:

- `nodi_simulator/realism_v2_io.py`
  - `resolve_artifact_path()` resolves a logical artifact path to a `.gz` twin when the uncompressed file is absent.
  - `open_text_artifact()` reads text artifacts through gzip when needed.
  - `sha256_file()` hashes the decompressed payload when a logical CSV path is backed by `.csv.gz`, preserving existing scientific provenance checksums.
  - `read_csv_rows()` and `read_csv_headers()` centralize CSV reads for logical/compressed artifacts.

- `nodi_simulator/realism_v2.py`
  - R5/R5.1/R5.2 CSV consumers now use the logical artifact reader.

- `nodi_simulator/post_v2_audit.py`
  - R5 noise-route sensitivity reads archived `full_grid_v2_summary.csv.gz`.

- `dashboard/backend.py`
  - dashboard dataset loading resolves `summary.csv.gz` and `compact.pkl.gz` fallbacks.

## Compressed artifacts

| Logical artifact | Stored artifact | Original bytes | Compressed bytes | Bytes saved | Verification |
| --- | --- | ---: | ---: | ---: | --- |
| `results/ev_nodi_realism_v2_full_grid_R5_v2/full_grid_v2_case_manifest.csv` | `results/ev_nodi_realism_v2_full_grid_R5_v2/full_grid_v2_case_manifest.csv.gz` | `184,559,923` | `4,305,350` | `180,254,573` | decompressed SHA-256 equals original; `256,256` data rows |
| `results/ev_nodi_realism_v2_full_grid_R5_v2/full_grid_v2_summary.csv` | `results/ev_nodi_realism_v2_full_grid_R5_v2/full_grid_v2_summary.csv.gz` | `348,192,595` | `14,996,549` | `333,196,046` | decompressed SHA-256 equals original; `256,256` data rows |
| `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_compact.pkl` | `results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_compact.pkl.gz` | `2,392,400,317` | `1,319,180,521` | `1,073,219,796` | decompressed SHA-256 equals original |
| `results/lens_b_fixed660_tau1ms_ev_gold_fullgrid_1000e_seed42_compact.pkl` | `results/lens_b_fixed660_tau1ms_ev_gold_fullgrid_1000e_seed42_compact.pkl.gz` | `39,033,578` | `7,987,132` | `31,046,446` | decompressed SHA-256 equals original |

Stable manifest:

- `results/nonpaper_results_internal_slimming_manifest_20260523.json`

Detailed operation manifests:

- `tmp/project_productization_cleanup_20260523/nonpaper_results_r5_gzip_compression_manifest_20260523.json`
- `tmp/project_productization_cleanup_20260523/nonpaper_results_compact_pickle_gzip_manifest_20260523.json`

Helper scripts:

- `tmp/project_productization_cleanup_20260523/compress_nonpaper_results_r5_artifacts_20260523.py`
- `tmp/project_productization_cleanup_20260523/compress_nonpaper_results_compact_pickles_20260523.py`

## What was deliberately not slimmed

- The six current 3seed 10000e diagnostic sidecars remain uncompressed because they directly support report 140's post-run analysis and are still high-value current evidence.
- The current 3seed 10000e raw rows remain unchanged.
- The v1 `summary.csv` remains uncompressed because existing review-package tests and external documentation still treat that exact path as the canonical single summary CSV.
- `papers/` remains frozen for this pass.

## Verification

Passed:

```bash
python -m pytest tests/test_realism_v2_io.py tests/test_realism_v2_R5_full_grid_v2.py tests/test_realism_v2_R5_1_next_stage_plan.py tests/test_realism_v2_R5_2_bounded_scenario_prior_audit_plan.py tests/test_noise_applicable_scenario_minimum.py tests/test_noise_readout_relative_criterion.py tests/test_post_v2_mandatory_audit_schema.py tests/test_dashboard_workflow.py::test_check_data_files_accepts_gzip_archived_summary_and_compact tests/test_dashboard_workflow.py::test_load_sweep_compact_reads_gzip_archive_from_logical_path tests/test_dashboard_workflow.py::test_load_sweep_summary_disables_chunked_csv_type_inference
```

Result: `51 passed in 14.09s`.

Also passed:

```bash
gzip -t results/ev_nodi_realism_v2_full_grid_R5_v2/full_grid_v2_case_manifest.csv.gz results/ev_nodi_realism_v2_full_grid_R5_v2/full_grid_v2_summary.csv.gz results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_compact.pkl.gz results/lens_b_fixed660_tau1ms_ev_gold_fullgrid_1000e_seed42_compact.pkl.gz
```

Dashboard path resolution was checked for:

- `ev_design_full_range_biomimetic_exosome_with_anchors_10000e`
- `lens_b_fixed660_tau1ms_ev_gold_fullgrid_1000e_seed42`

Both resolve `.pkl.gz` compact fallbacks while keeping the uncompressed `summary.csv` paths.

## Commands run

No raw full-grid command was run.

Commands used for this pass:

```bash
python -m pytest tests/test_realism_v2_io.py tests/test_realism_v2_R5_full_grid_v2.py tests/test_realism_v2_R5_1_next_stage_plan.py tests/test_realism_v2_R5_2_bounded_scenario_prior_audit_plan.py
python tmp/project_productization_cleanup_20260523/compress_nonpaper_results_r5_artifacts_20260523.py
python -m pytest tests/test_realism_v2_io.py tests/test_realism_v2_R5_full_grid_v2.py tests/test_realism_v2_R5_1_next_stage_plan.py tests/test_realism_v2_R5_2_bounded_scenario_prior_audit_plan.py
python -m pytest tests/test_noise_applicable_scenario_minimum.py tests/test_noise_readout_relative_criterion.py tests/test_post_v2_mandatory_audit_schema.py
python -m pytest tests/test_dashboard_workflow.py::test_check_data_files_accepts_gzip_archived_summary_and_compact tests/test_dashboard_workflow.py::test_check_data_files_rejects_stale_standard_wavelength_set tests/test_dashboard_workflow.py::test_load_sweep_compact_reads_gzip_archive_from_logical_path tests/test_dashboard_workflow.py::test_load_sweep_compact_backfills_gate_and_recommendation_fields tests/test_dashboard_workflow.py::test_load_sweep_summary_disables_chunked_csv_type_inference
python tmp/project_productization_cleanup_20260523/compress_nonpaper_results_compact_pickles_20260523.py
gzip -t results/ev_nodi_realism_v2_full_grid_R5_v2/full_grid_v2_case_manifest.csv.gz results/ev_nodi_realism_v2_full_grid_R5_v2/full_grid_v2_summary.csv.gz results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_compact.pkl.gz results/lens_b_fixed660_tau1ms_ev_gold_fullgrid_1000e_seed42_compact.pkl.gz
python -m pytest tests/test_realism_v2_io.py tests/test_realism_v2_R5_full_grid_v2.py tests/test_realism_v2_R5_1_next_stage_plan.py tests/test_realism_v2_R5_2_bounded_scenario_prior_audit_plan.py tests/test_noise_applicable_scenario_minimum.py tests/test_noise_readout_relative_criterion.py tests/test_post_v2_mandatory_audit_schema.py tests/test_dashboard_workflow.py::test_check_data_files_accepts_gzip_archived_summary_and_compact tests/test_dashboard_workflow.py::test_load_sweep_compact_reads_gzip_archive_from_logical_path tests/test_dashboard_workflow.py::test_load_sweep_summary_disables_chunked_csv_type_inference
```

## Residual caveats

- Compressing the current 3seed 10000e diagnostic sidecars could save much more space, but I deferred it because those files are current post-run evidence rather than older support artifacts.
- Compressing the canonical v1 `summary.csv` could save about another 1.25 GiB, but it should wait until review-package manifests, exact-path tests, and any external handoff expectations are updated together.
- The pass changes storage layout, not scientific scope. It does not add measured data, calibrated SNR, LOD, empirical false-positive rates, POD claims, or biological specificity.
