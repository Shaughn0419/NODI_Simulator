# EV NODI full update review ledger 2026-05-11

This ledger records the 2026-05-11 in-place consolidation of the current full-data reader report, the file-by-file source/config/test review, the documentation review, and the verification evidence. It is a review artifact; the current scientific single source of truth remains `reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md` v3.0.

## Report baseline and merge record

- Baseline selected: `reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`.
- Reason: `reports/current/README.md` marks report 47 as historical and identifies report 88 as the current reader-facing v1/v2 interpretation; after this pass, report 88 is v3.0 and includes P0-P18.
- Version/date after update: `v3.0`, `2026-05-11`.
- Coverage after update: v1 full-grid `32,032` base design combinations at `10,000` synthetic events per case; realism v2 no-measured-data closure; P0 review-ready relative audit (`572` route aggregate rows, `143` per wavelength); P1-P18 physical-ceiling contracts and six bounded trace-only lanes.
- Current boundary: no measured acquisition data, no calibration-data ingest, no calibrated SNR/event-probability/LOD/concentration/biological-specificity claim, no route promotion, no main-660 redefinition.

## Code review findings by severity

- P0: none found.
- P1: none found.
- P2: Untracked AppleDouble metadata files detected outside ignored runtime folders: 1454. They are not tracked source, but naive recursive tools such as `compileall` can fail on null bytes unless they use tracked-file lists or exclude `._*`.
- P3: No tracked-source blocking correctness/security defect found by per-file syntax scan, ruff, pyright, mypy, targeted tests, full test runner, and review-package verifier.
- P3: Historical supersession generator drift was found and fixed so generated supersession docs keep report 88 v3.0/P0-P18 rows.
- P3: Generated post-v2 lane modules intentionally duplicate manifest/guardrail code; defer consolidation until P19 evidence strategy decides whether this lane family continues.
- P3: Typed static checking remains scoped to the configured typed seed allowlist; full-repository type coverage is still a maintainability backlog.
- P3: Review-package manifests and hashes are generated provenance files; they were refreshed to match updated hash-bearing docs and verified with the local-dev verifier.

## Verification evidence

- `python -m py_compile` over all 347 tracked Python files: pass.
- `python -m pytest -q tests/test_code_review_hardening.py tests/test_review_package_manifest.py tests/test_bounded_lane_synthesis_stop_continue.py`: 29 passed.
- `python tests/run_tests.py --workers 7`: 1342 non-AppTest tests passed and 5 AppTest tests passed through the canonical two-lane runner.
- `python -m ruff check nodi_simulator dashboard tools tests --output-format=concise`: pass.
- `python -m pyright`: 0 errors, 0 warnings.
- `python -m mypy`: success, no issues in 6 source files.
- `python tools/verify_review_package.py --package-root . --mode local-dev`: pass.
- `python tools/verify_review_package.py --package-root . --mode external-review`: pass.
- Central Markdown links in README/navigation/report-current/audit/ledger: pass.
- `git diff --check`: pass.
- Naive recursive `compileall` over broad directories is not a release gate on this mounted volume because untracked AppleDouble `._*` metadata files contain null bytes; use tracked-file compilation instead.

## Source/config/test file-by-file ledger

Tracked files reviewed in git order: 519. Each row records the path, category, finding summary, recommended action, and whether this pass changed the file.

| Path | Category | Findings | Recommendation | Fixed in this pass |
|---|---|---|---|---|
| `.streamlit/config.toml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `REVIEW_BUILD_MANIFEST.json` | config/manifest | P3 generated review-package metadata refreshed because README/report 89/supersession are hash-bearing review artifacts | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Updated generated manifest/hash metadata. |
| `REVIEW_PACKAGE_HASHES.sha256` | config/manifest | P3 generated hash manifest refreshed so review-package verifier matches updated hash-bearing docs | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Updated generated manifest/hash metadata. |
| `REVIEW_PACKAGE_MANIFEST.json` | config/manifest | P3 generated review-package release metadata refreshed because README/report 89/supersession are hash-bearing review artifacts | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Updated generated manifest/hash metadata. |
| `calibration/bfp_roi_mask_template.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `calibration/blank_false_positive_template.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `calibration/blank_false_positive_template_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `calibration/calibration_manifest_template.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `calibration/collection_operator_template.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `calibration/collection_operator_template_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `calibration/raw_blank_trace_manifest_template.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `calibration/reference_blank_channel_template.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `calibration/reference_blank_channel_template_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `calibration/standard_particle_template.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `calibration/standard_particle_template_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/bounded_lane_synthesis_stop_continue_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/bounded_physical_solver_readiness_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/bounded_solver_authorization_gate_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/bounded_solver_authorization_pilot_design_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/bounded_solver_dry_run_preflight_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/calibration_artifact_registry.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/claim_level_matrix.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/detector_connection_state_machine.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/detector_path_schema.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/ev_sample_profiles.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/fifth_bounded_lane_authorization_design_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/fifth_bounded_solver_lane_closure_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/fifth_bounded_solver_lane_execution_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/forbidden_claims_lexicon.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/fourth_bounded_lane_authorization_design_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/fourth_bounded_solver_lane_closure_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/fourth_bounded_solver_lane_execution_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/full_wave_green_tensor_diagnostic_contract.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/laser_daq_schema.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/minimal_bounded_solver_execution_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/next_bounded_lane_authorization_design_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/noise_readout_scenario_bundle.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/physical_ceiling_extension_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/r3b_uncertainty_prior_table.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/r4_2_main660_nearwall_mesh_adjudication_plan.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/r4_representative_full_wave_plan.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/r4_revised_rerun_plan.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/r4_route_model_revision_plan.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/r5_1_route_role_stability_interpretation_plan.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/r5_2_bounded_scenario_prior_audit_plan.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/r5_3_route_prior_model_revision_plan.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/r5_full_grid_v2_plan.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/r5_scenario_bundle_manifest.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/r6_route_prior_sensitivity_plan.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/r7_1_operator_artifact_validation_plan.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/r7_2_operator_artifact_gap_register_plan.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/r7_route_prior_mechanistic_decomposition_plan.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/reason_code_vocabulary.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/roughness_leakage_diagnostic_contract.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/route_key_schema.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/route_role_vocabulary.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/run_manifest_schema.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/scenario_registry.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/second_bounded_solver_lane_closure_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/second_bounded_solver_lane_execution_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/second_lane_authorization_design_registry.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/seventh_bounded_lane_authorization_design_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/sixth_bounded_lane_authorization_design_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/sixth_bounded_solver_lane_closure_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/sixth_bounded_solver_lane_execution_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/third_bounded_solver_lane_closure_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/third_bounded_solver_lane_execution_registry.yaml` | config/manifest | P3 governance config is evidence/provenance critical; keep synchronized with tests and report 88 v3.0 before future lane execution | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `configs/realism_v2/transport_residence_time_diagnostic_contract.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/unit_registry.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/v1_summary_hash_pin.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/v2_no_measured_data_closure_plan.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `configs/realism_v2/vector_jones_polarization_diagnostic_contract.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `dashboard/__init__.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `dashboard/app.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `dashboard/backend.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `dashboard/config.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `dashboard/estimate_precompute_runtime.py` | source | P3 broad optional-dependency/write-cleanup exception handling is intentional fallback, but can hide unexpected runtime faults; P3 broad optional-dependency/write-cleanup exception handling is intentional fallback, but can hide unexpected runtime faults | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `dashboard/mie_backend.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `dashboard/panels/__init__.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `dashboard/panels/common.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `dashboard/panels/explorer.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `dashboard/panels/inspector.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `dashboard/panels/interference_explorer.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `dashboard/panels/mie_explorer.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `dashboard/panels/noise_detection_explorer.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `dashboard/panels/research_story.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `dashboard/panels/single_case_calculator.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `dashboard/precompute.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `dashboard/safe_pickle.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `dashboard/signal_backend.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/__init__.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/_exports.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/assay_control_matrix.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/bayesian_calibration.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/bfp_detector_operator.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/calibration_models.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/calibration_plan_advisor.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/channel_geometry_model.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/control_interpretation.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/count_generation.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/count_likelihood.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/data_objects.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/design_claim_governance.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/design_metrics.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/design_postprocess.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/detector_units.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/electrokinetic_transport.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/ev_integrity_risk.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/ev_population_prior.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/ev_reporting_metadata.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/event_quality_control.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/experimental_design_advisor.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/fluidic_network_model.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/fluidic_resistance.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/illumination.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/interface_correction.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/interferometric_trace.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/intrinsic_scattering.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/materials.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/mie_engine.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/nodi_thermal_contamination.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/objective_panel.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/ood_detection.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/optical_exposure_safety.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/optical_hardware_profiles.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/optional_acceleration.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/paper_aligned_profiles.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/parameter_sweep.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/particle_channel_perturbation.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/particle_design_library.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/photothermal_pod.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/polarization_jones_operator.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/population_inference.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/population_trace_simulator.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/post_v2_audit.py` | source | P3 generated post-v2 lane module repeats manifest/guardrail patterns; consider consolidation after P19 evidence-strategy stabilizes | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/post_v2_bounded_lane_synthesis_stop_continue.py` | source | P3 generated post-v2 lane module repeats manifest/guardrail patterns; consider consolidation after P19 evidence-strategy stabilizes | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/post_v2_bounded_physical_solver_readiness.py` | source | P3 generated post-v2 lane module repeats manifest/guardrail patterns; consider consolidation after P19 evidence-strategy stabilizes | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/post_v2_bounded_solver_authorization_gate.py` | source | P3 generated post-v2 lane module repeats manifest/guardrail patterns; consider consolidation after P19 evidence-strategy stabilizes | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/post_v2_bounded_solver_authorization_pilot_design.py` | source | P3 generated post-v2 lane module repeats manifest/guardrail patterns; consider consolidation after P19 evidence-strategy stabilizes | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/post_v2_bounded_solver_dry_run_preflight.py` | source | P3 generated post-v2 lane module repeats manifest/guardrail patterns; consider consolidation after P19 evidence-strategy stabilizes | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/post_v2_fifth_bounded_solver_lane_execution.py` | source | P3 generated post-v2 lane module repeats manifest/guardrail patterns; consider consolidation after P19 evidence-strategy stabilizes | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/post_v2_fourth_bounded_solver_lane_execution.py` | source | P3 generated post-v2 lane module repeats manifest/guardrail patterns; consider consolidation after P19 evidence-strategy stabilizes | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/post_v2_minimal_bounded_solver_execution.py` | source | P3 generated post-v2 lane module repeats manifest/guardrail patterns; consider consolidation after P19 evidence-strategy stabilizes | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/post_v2_p10_closure_p11_authorization_design.py` | source | P3 generated post-v2 lane module repeats manifest/guardrail patterns; consider consolidation after P19 evidence-strategy stabilizes | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/post_v2_p12_closure_p13_authorization_design.py` | source | P3 generated post-v2 lane module repeats manifest/guardrail patterns; consider consolidation after P19 evidence-strategy stabilizes | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/post_v2_p14_closure_p15_authorization_design.py` | source | P3 generated post-v2 lane module repeats manifest/guardrail patterns; consider consolidation after P19 evidence-strategy stabilizes | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/post_v2_p16_closure_p17_authorization_design.py` | source | P3 generated post-v2 lane module repeats manifest/guardrail patterns; consider consolidation after P19 evidence-strategy stabilizes | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/post_v2_p8_closure_p9_authorization_design.py` | source | P3 generated post-v2 lane module repeats manifest/guardrail patterns; consider consolidation after P19 evidence-strategy stabilizes | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/post_v2_physical_ceiling.py` | source | P3 generated post-v2 lane module repeats manifest/guardrail patterns; consider consolidation after P19 evidence-strategy stabilizes | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/post_v2_second_bounded_solver_lane_execution.py` | source | P3 generated post-v2 lane module repeats manifest/guardrail patterns; consider consolidation after P19 evidence-strategy stabilizes | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/post_v2_second_lane_authorization_design.py` | source | P3 generated post-v2 lane module repeats manifest/guardrail patterns; consider consolidation after P19 evidence-strategy stabilizes | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/post_v2_sixth_bounded_solver_lane_execution.py` | source | P3 generated post-v2 lane module repeats manifest/guardrail patterns; consider consolidation after P19 evidence-strategy stabilizes | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/post_v2_third_bounded_solver_lane_execution.py` | source | P3 generated post-v2 lane module repeats manifest/guardrail patterns; consider consolidation after P19 evidence-strategy stabilizes | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/pulse_analysis.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/readout_transfer_model.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/realism_v2.py` | source | P3 provenance helper falls back to `unavailable` on broad git failures; acceptable for local runs, verifier remains the release gate | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Not changed; recorded as review debt or intentional boundary. |
| `nodi_simulator/realism_v2_io.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/recompute_manifest.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/reference_field.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/reference_operating_point.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/review_package.py` | source | P3 supersession generator was stale for report 88 v3.0/P0-P18; fixed generator output so future manifest refresh preserves current supersession rows | Keep current behavior; address only if future lane execution or release-hardening scope requires it. | Fixed supersession generator output. |
| `nodi_simulator/run_state_model.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/scattering_trace.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/seed_robustness.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/selection_function.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/structured_particles.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/trajectory.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/tsuyama_phase_filter.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/type_coerce.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/uncertainty.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/unit_conventions.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/utils.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `nodi_simulator/wavelength_comparability.py` | source | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `papers/provenance/paper_hashes.sha256` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `papers/provenance/paper_manifest.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `papers/provenance/paper_manifest_overrides.yaml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `papers/provenance/unavailable_or_not_packaged_papers.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `pyproject.toml` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `pyrightconfig.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `pytest.ini` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_bounded_lane_synthesis_stop_continue/bounded_lane_rank_behavior_summary.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_bounded_lane_synthesis_stop_continue/bounded_lane_synthesis_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_bounded_lane_synthesis_stop_continue/bounded_lane_synthesis_stop_continue_record.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_bounded_physical_solver_readiness/bounded_physical_solver_readiness_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_bounded_physical_solver_readiness/bounded_physical_solver_readiness_route_universe_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_bounded_physical_solver_readiness/bounded_physical_solver_readiness_schema_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_bounded_physical_solver_readiness/bounded_physical_solver_readiness_source_binding_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_bounded_solver_authorization_gate/bounded_solver_authorization_gate_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_bounded_solver_authorization_gate/bounded_solver_authorization_gate_p4_binding_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_bounded_solver_authorization_gate/bounded_solver_authorization_gate_record.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_bounded_solver_authorization_pilot_design/bounded_solver_authorization_pilot_design_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_bounded_solver_authorization_pilot_design/bounded_solver_authorization_pilot_design_p2_route_binding_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_bounded_solver_authorization_pilot_design/bounded_solver_authorization_pilot_design_route_subset_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_bounded_solver_authorization_pilot_design/bounded_solver_authorization_pilot_design_schema_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_bounded_solver_dry_run_preflight/bounded_solver_dry_run_preflight_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_bounded_solver_dry_run_preflight/bounded_solver_dry_run_preflight_p3_binding_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_bounded_solver_dry_run_preflight/full_wave_green_tensor_execution_authorization_record.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_bounded_solver_dry_run_preflight/full_wave_green_tensor_mesh_boundary_unit_preflight_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_bounded_solver_dry_run_preflight/full_wave_green_tensor_minimal_pilot_input_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_fifth_bounded_lane_authorization_design/p13_next_authorization_design_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_fifth_bounded_lane_authorization_design/p13_next_authorization_gate_record.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_fifth_bounded_lane_authorization_design/p13_p12_closure_binding_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_fifth_bounded_solver_lane_closure/p14_claude_review_closure_record.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_fifth_bounded_solver_lane_closure/p14_closure_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_fifth_bounded_solver_lane_execution/fifth_bounded_solver_lane_execution_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_fifth_bounded_solver_lane_execution/fifth_bounded_solver_lane_execution_p13_authorization_binding_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_fifth_bounded_solver_lane_execution/fifth_bounded_solver_lane_trace_output.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_fifth_bounded_solver_lane_execution/fifth_bounded_solver_lane_trace_output_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_fourth_bounded_lane_authorization_design/p11_next_authorization_design_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_fourth_bounded_lane_authorization_design/p11_next_authorization_gate_record.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_fourth_bounded_lane_authorization_design/p11_p10_closure_binding_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_fourth_bounded_solver_lane_closure/p12_claude_review_closure_record.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_fourth_bounded_solver_lane_closure/p12_closure_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_fourth_bounded_solver_lane_execution/fourth_bounded_solver_lane_execution_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_fourth_bounded_solver_lane_execution/fourth_bounded_solver_lane_execution_p11_authorization_binding_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_fourth_bounded_solver_lane_execution/fourth_bounded_solver_lane_trace_output.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_fourth_bounded_solver_lane_execution/fourth_bounded_solver_lane_trace_output_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_mandatory_audit/bfp_roi_operator_summary.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_mandatory_audit/candidate_universe_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_mandatory_audit/ev_prior_contaminant_summary.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_mandatory_audit/noise_readout_route_sensitivity.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_mandatory_audit/noise_readout_scenario_bundle.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_mandatory_audit/top_candidate_extended_pairwise_stability.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_mandatory_audit/top_candidate_mandatory_audit_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_mandatory_audit/top_candidate_pairwise_rank_inversion.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_mandatory_audit/top_candidate_particle_panel_audit.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_mandatory_audit/tsuyama_bfp_reference_summary.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_minimal_bounded_solver_execution/full_wave_green_tensor_minimal_solver_output.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_minimal_bounded_solver_execution/full_wave_green_tensor_minimal_solver_output_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_minimal_bounded_solver_execution/minimal_bounded_solver_execution_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_minimal_bounded_solver_execution/minimal_bounded_solver_execution_p5_binding_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_next_bounded_lane_authorization_design/p9_next_authorization_design_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_next_bounded_lane_authorization_design/p9_next_authorization_gate_record.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_next_bounded_lane_authorization_design/p9_p8_closure_binding_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_physical_ceiling/full_wave_green_tensor_diagnostic.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_physical_ceiling/physical_ceiling_contract_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_physical_ceiling/physical_ceiling_diagnostic_schema_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_physical_ceiling/physical_ceiling_input_binding_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_physical_ceiling/physical_ceiling_route_coverage_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_physical_ceiling/roughness_leakage_diagnostic.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_physical_ceiling/transport_residence_time_diagnostic.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_physical_ceiling/vector_jones_polarization_diagnostic.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_second_bounded_solver_lane_closure/p8_claude_review_closure_record.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_second_bounded_solver_lane_closure/p8_closure_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_second_bounded_solver_lane_execution/second_bounded_solver_lane_execution_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_second_bounded_solver_lane_execution/second_bounded_solver_lane_execution_p7_authorization_binding_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_second_bounded_solver_lane_execution/second_bounded_solver_lane_trace_output.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_second_bounded_solver_lane_execution/second_bounded_solver_lane_trace_output_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_second_lane_authorization_design/second_lane_authorization_design_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_second_lane_authorization_design/second_lane_authorization_design_authorization_gate_record.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_second_lane_authorization_design/second_lane_authorization_design_candidate_lane_contract_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_second_lane_authorization_design/second_lane_authorization_design_p6_evidence_binding_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_seventh_bounded_lane_authorization_design/p17_next_authorization_design_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_seventh_bounded_lane_authorization_design/p17_next_authorization_gate_record.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_seventh_bounded_lane_authorization_design/p17_p16_closure_binding_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_sixth_bounded_lane_authorization_design/p15_next_authorization_design_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_sixth_bounded_lane_authorization_design/p15_next_authorization_gate_record.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_sixth_bounded_lane_authorization_design/p15_p14_closure_binding_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_sixth_bounded_solver_lane_closure/p16_claude_review_closure_record.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_sixth_bounded_solver_lane_closure/p16_closure_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_sixth_bounded_solver_lane_execution/sixth_bounded_solver_lane_execution_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_sixth_bounded_solver_lane_execution/sixth_bounded_solver_lane_execution_p15_authorization_binding_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_sixth_bounded_solver_lane_execution/sixth_bounded_solver_lane_trace_output.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_sixth_bounded_solver_lane_execution/sixth_bounded_solver_lane_trace_output_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_third_bounded_solver_lane_closure/p10_claude_review_closure_record.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_third_bounded_solver_lane_closure/p10_closure_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_third_bounded_solver_lane_execution/third_bounded_solver_lane_execution_artifact_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_third_bounded_solver_lane_execution/third_bounded_solver_lane_execution_p9_authorization_binding_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_third_bounded_solver_lane_execution/third_bounded_solver_lane_trace_output.csv` | data/table | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `results/post_v2_third_bounded_solver_lane_execution/third_bounded_solver_lane_trace_output_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `run_manifest.json` | config/manifest | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/__init__.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/_review_package_test_helpers.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/conftest.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/dashboard_test_helpers.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/run_pytest_suite.sh` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/run_tests.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_artifact_gap_binding.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_bfp_jacobian_closed_form.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_bfp_roi_magnitude_only_rejected_for_clean_main.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_bfp_roi_self_cross_decomposition_schema.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_bfp_roi_signed_cross_term_preserved.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_bounded_lane_synthesis_stop_continue.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_bounded_physical_solver_readiness.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_bounded_solver_authorization_gate.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_bounded_solver_authorization_pilot_design.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_bounded_solver_dry_run_preflight.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_candidate_universe_pre_scoring_required.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_candidate_universe_route_dedup_coverage.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_claim_language_regression.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_clean_relative_main_gate_consumption.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_code_review_hardening.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_coincidence_relative_proxy.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_contaminant_utilization_and_ev_profile_resolution.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_dashboard_workflow.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_ev_profiles_and_noise_bundle_config.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_ev_sample_contaminant_relative_audit.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_ev_selected_annulus_analysis.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_event_block_randoms.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_event_engine_benchmark.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_export_zip_contents.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_extended_pairwise_stability.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_fifth_bounded_solver_lane_execution.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_final_decision_to_route_role_mapping.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_fourth_bounded_solver_lane_execution.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_full_wave_green_tensor_diagnostic_contract.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_instrument_hardware_feasibility.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_mie_engine.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_minimal_bounded_solver_execution.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_noise_applicable_scenario_minimum.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_noise_readout_relative_criterion.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_optional_acceleration_dependency.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_p10_closure_p11_authorization_design.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_p12_closure_p13_authorization_design.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_p14_closure_p15_authorization_design.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_p16_closure_p17_authorization_design.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_p8_closure_p9_authorization_design.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_pairwise_rank_inversion_schema.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_paper_provenance_claim_bearing_metadata_verified.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_paper_provenance_disjoint_and_supersession.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_paper_provenance_generator_deterministic.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_parameter_sweep_callbacks.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_physical_ceiling_contract_manifest.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_physical_ceiling_extension_registry.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_physics_core.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_post_v2_mandatory_audit_schema.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_post_v2_reason_code_vocabulary.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_R4_2_adjudication.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_R4_2_adjudication_plan.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_R5_1_interpretation.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_R5_1_next_stage_plan.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_R5_2_bounded_scenario_prior_audit.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_R5_2_bounded_scenario_prior_audit_plan.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_R5_3_route_prior_model_revision_audit.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_R5_3_route_prior_model_revision_plan.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_R5_full_grid_v2.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_R5_plan.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_R6_plan.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_R6_route_prior_sensitivity_audit.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_R7_1_operator_artifact_validation_plan.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_R7_1_operator_artifact_validation_protocol.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_R7_2_operator_artifact_gap_register_generation.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_R7_2_operator_artifact_gap_register_plan.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_R7_plan.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_R7_route_prior_mechanistic_decomposition_audit.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_anchor_smoke.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_contract.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_io.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_micro_anchor.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_no_measured_data_closure.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_r3b_plan.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_r4_plan.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_reduced_grid_R3a.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_representative_full_wave_R4.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_revised_R4_rerun.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_revised_R4_rerun_plan.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_route_model_revision_audit.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_route_model_revision_plan.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_sidecars.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_realism_v2_uncertainty_R3b.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_reference_field.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_review_package_claim_scan.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_review_package_hash_manifest.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_review_package_hash_no_cycle.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_review_package_hash_order_is_deterministic.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_review_package_manifest.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_review_package_root_contents.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_roughness_leakage_diagnostic_contract.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_route_aggregation_scope_declared.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_route_role_vocabulary.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_schema_docs_present.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_second_bounded_solver_lane_execution.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_second_lane_authorization_design.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_selected_annulus_boundary_values.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_selected_annulus_claim_governance.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_selected_annulus_cross_lambda_regression.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_selected_annulus_reversal_predicate.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_severity_to_final_decision_mapping.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_sixth_bounded_solver_lane_execution.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_third_bounded_solver_lane_execution.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_tools_legacy_entrypoints.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_trajectory.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_transport_residence_time_diagnostic_contract.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_tsuyama_2022_classification_lane.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_tsuyama_annulus_ratio_sensitivity.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_tsuyama_gold_aligned_detection_lane.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_tsuyama_paper_statistics_sensitivity.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_tsuyama_paper_target_audit.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_tsuyama_phase2_acceptance.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_tsuyama_phase2_parameter_inverse.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_tsuyama_phase_filter_signed_complex_preserved.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_tsuyama_selected_annulus_joint_fit.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_tsuyama_tolerance_profile_recorded.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_type_coerce.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_v1_hash_drift_blocks_release.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_vector_jones_polarization_diagnostic_contract.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tests/test_verify_review_package_cli.py` | test | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/__init__.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/_common.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/_legacy_entrypoint.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/audits/__init__.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/audits/ev_size_weighted_route_analysis.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/audits/instrument_hardware_feasibility.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/audits/mainline_consistency_audit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/audits/tsuyama_2022_classification_lane.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/audits/tsuyama_annulus_ratio_sensitivity.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/audits/tsuyama_detection_rate_calibration.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/audits/tsuyama_detection_rule_sensitivity.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/audits/tsuyama_gold_aligned_detection_lane.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/audits/tsuyama_gold_validation_compare.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/audits/tsuyama_paper_statistics_sensitivity.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/audits/tsuyama_paper_target_audit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/audits/tsuyama_selected_annulus_joint_fit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/benchmarks/__init__.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/benchmarks/event_block_v2_experiment.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/benchmarks/event_engine_benchmark.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/benchmarks/peak_detector_vectorization_experiment.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/ev_nodi_realism_v2_R4_2_adjudication.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/ev_nodi_realism_v2_R5_1_interpretation.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/ev_nodi_realism_v2_R5_2_bounded_scenario_prior_audit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/ev_nodi_realism_v2_R5_3_route_prior_model_revision_audit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/ev_nodi_realism_v2_R6_route_prior_sensitivity_audit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/ev_nodi_realism_v2_R7_1_operator_artifact_validation_protocol.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/ev_nodi_realism_v2_R7_2_operator_artifact_gap_register.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/ev_nodi_realism_v2_R7_route_prior_mechanistic_decomposition_audit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/ev_nodi_realism_v2_anchor_smoke.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/ev_nodi_realism_v2_full_grid_R5_v2.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/ev_nodi_realism_v2_micro_anchor.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/ev_nodi_realism_v2_no_measured_data_closure.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/ev_nodi_realism_v2_reduced_grid_R3a.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/ev_nodi_realism_v2_representative_full_wave_R4.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/ev_nodi_realism_v2_revised_R4_rerun.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/ev_nodi_realism_v2_route_model_revision_audit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/ev_nodi_realism_v2_uncertainty_R3b.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/ev_size_weighted_route_analysis.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/event_block_v2_experiment.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/event_engine_benchmark.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/export_review_package.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_paper_provenance.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_bfp_roi_audit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_bounded_lane_synthesis_stop_continue.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_bounded_physical_solver_readiness.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_bounded_solver_authorization_gate.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_bounded_solver_authorization_pilot_design.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_bounded_solver_dry_run_preflight.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_candidate_universe.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_ev_audit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_fifth_bounded_solver_lane_execution.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_final_audit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_fourth_bounded_solver_lane_execution.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_minimal_bounded_solver_execution.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_noise_audit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_p10_closure_p11_authorization_design.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_p12_closure_p13_authorization_design.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_p14_closure_p15_authorization_design.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_p16_closure_p17_authorization_design.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_p1_extensions.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_p8_closure_p9_authorization_design.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_physical_ceiling_contract_manifest.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_second_bounded_solver_lane_execution.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_second_lane_authorization_design.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_sixth_bounded_solver_lane_execution.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_third_bounded_solver_lane_execution.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_post_v2_tsuyama_audit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/generate_review_package_manifest.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/instrument_hardware_feasibility.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/mainline_consistency_audit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/__init__.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/ev_nodi_realism_v2_R4_2_adjudication.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/ev_nodi_realism_v2_R5_1_interpretation.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/ev_nodi_realism_v2_R5_2_bounded_scenario_prior_audit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/ev_nodi_realism_v2_R5_3_route_prior_model_revision_audit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/ev_nodi_realism_v2_R6_route_prior_sensitivity_audit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/ev_nodi_realism_v2_R7_1_operator_artifact_validation_protocol.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/ev_nodi_realism_v2_R7_2_operator_artifact_gap_register.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/ev_nodi_realism_v2_R7_route_prior_mechanistic_decomposition_audit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/ev_nodi_realism_v2_anchor_smoke.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/ev_nodi_realism_v2_full_grid_R5_v2.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/ev_nodi_realism_v2_micro_anchor.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/ev_nodi_realism_v2_no_measured_data_closure.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/ev_nodi_realism_v2_reduced_grid_R3a.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/ev_nodi_realism_v2_representative_full_wave_R4.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/ev_nodi_realism_v2_revised_R4_rerun.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/ev_nodi_realism_v2_route_model_revision_audit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/ev_nodi_realism_v2_uncertainty_R3b.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/tsuyama_phase2_acceptance_report.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/one_shot/tsuyama_phase2_parameter_inverse.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/peak_detector_vectorization_experiment.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/tsuyama_2022_classification_lane.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/tsuyama_annulus_ratio_sensitivity.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/tsuyama_detection_rate_calibration.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/tsuyama_detection_rule_sensitivity.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/tsuyama_gold_aligned_detection_lane.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/tsuyama_gold_validation_compare.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/tsuyama_paper_statistics_sensitivity.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/tsuyama_paper_target_audit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/tsuyama_phase2_acceptance_report.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/tsuyama_phase2_parameter_inverse.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/tsuyama_selected_annulus_joint_fit.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/verify_post_v2_bounded_lane_synthesis_stop_continue.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/verify_post_v2_bounded_physical_solver_readiness.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/verify_post_v2_bounded_solver_authorization_gate.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/verify_post_v2_bounded_solver_authorization_pilot_design.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/verify_post_v2_bounded_solver_dry_run_preflight.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/verify_post_v2_fifth_bounded_solver_lane_execution.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/verify_post_v2_fourth_bounded_solver_lane_execution.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/verify_post_v2_minimal_bounded_solver_execution.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/verify_post_v2_p10_closure_p11_authorization_design.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/verify_post_v2_p12_closure_p13_authorization_design.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/verify_post_v2_p14_closure_p15_authorization_design.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/verify_post_v2_p16_closure_p17_authorization_design.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/verify_post_v2_p8_closure_p9_authorization_design.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/verify_post_v2_physical_ceiling_contracts.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/verify_post_v2_second_bounded_solver_lane_execution.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/verify_post_v2_second_lane_authorization_design.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/verify_post_v2_sixth_bounded_solver_lane_execution.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/verify_post_v2_third_bounded_solver_lane_execution.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |
| `tools/verify_review_package.py` | tool/script | No file-specific issue found by syntax/static/security-contract review. | No action. | No code change needed. |

## Documentation file-by-file ledger

Documentation/explanatory files reviewed in git order plus this ledger: 269. Historical/stage reports are preserved as provenance unless listed as updated; current entry points now route readers to report 88 v3.0 and this ledger.

| Path | Role | Update record |
|---|---|---|
| `AGENTS.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `HISTORICAL_REPORT_SUPERSESSION.md` | updated-current | updated through the review-package generator with report 47 and P3-P18 provenance supersession rows pointing to report 88 v3.0 |
| `README.md` | updated-current | updated current project state, v3.0 report pointer, P0-P18 boundaries, AppleDouble tooling note, and result-lineage guidance |
| `REVIEW_PACKAGE_README.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `archive/README.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/dashboard/16_dashboard_precompute.full.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/dashboard/17_dashboard_app.full.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/dashboard/18_dashboard_backend.full.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/dashboard/19_dashboard_explorer.full.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/dashboard/20_dashboard_inspector.full.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/dashboard/22_dashboard_interference_explorer.full.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/dashboard/23_dashboard_noise_detection_explorer.full.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/dashboard/26_dashboard_mie_explorer.full.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/dashboard/27_dashboard_common.full.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/dashboard/29_dashboard_single_case_calculator.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/dashboard/30_dashboard_single_case_calculator.full.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/dashboard/README.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/docx/NODI_Core_Computation_Logic_EN_Expanded_Reformatted.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/docx/README.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/reports/31_exosome_50_150_focus_test.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/reports/32_exosome_50_150_focus_404_analysis.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/reports/33_full_range_4w_analysis.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/reports/35_10000e_exosome_selection_report.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/reports/README.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/tsuyama/README.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/tsuyama/probe_pre_20260502/README.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/tsuyama/probe_pre_20260502/tsuyama_2022_classification_lane_smoke_20260501/tsuyama_2022_classification_report_v1.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/tsuyama/probe_pre_20260502/tsuyama_2022_classification_lane_svm_status_smoke_20260501/tsuyama_2022_classification_report_v1.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/tsuyama/probe_pre_20260502/tsuyama_2022_classification_lane_v2_smoke_20260501/tsuyama_2022_classification_report_v2.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/tsuyama/probe_pre_20260502/tsuyama_annulus_ratio_sensitivity_smoke_debug2/annulus_ratio_sensitivity_decision_v1.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_annulus_full_chain_probe_20260501/44_Tsuyama_gold_aligned_detection_lane_report.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_annulus_joint_fit_inphase_probe_20260501/selected_annulus_joint_fit_report.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_annulus_joint_fit_smoke_20260501/selected_annulus_joint_fit_report.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_annulus_joint_fit_transfer_probe_20260501/selected_annulus_joint_fit_report.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_annulus_joint_fit_v2_geometry_smoke_20260501/selected_annulus_joint_fit_report.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_annulus_joint_fit_v2_size_diag_smoke_20260501/selected_annulus_joint_fit_report.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_annulus_joint_fit_v2_size_response_smoke_20260501/selected_annulus_joint_fit_report.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_annulus_more_cases_probe/selected_annulus_more_cases_report_v1.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_annulus_nonempty_ev_panel_probe_20260501/44_Tsuyama_gold_aligned_detection_lane_report.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_detector_mode_fulltest_annulus_0p5_0p8/tsuyama_detection_rate_calibration_report.md` | historical-provenance-preserved | Reviewed; preserved as historical provenance and not rewritten to avoid changing archived evidence. |
| `count_generation.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `dashboard/app.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `dashboard/backend.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `dashboard/config.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `dashboard/estimate_precompute_runtime.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `dashboard/mie_backend.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `dashboard/panels/common.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `dashboard/panels/explorer.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `dashboard/panels/inspector.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `dashboard/panels/interference_explorer.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `dashboard/panels/mie_explorer.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `dashboard/panels/noise_detection_explorer.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `dashboard/panels/research_story.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `dashboard/panels/single_case_calculator.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `dashboard/precompute.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `dashboard/signal_backend.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `data_objects.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `docs/DOCUMENTATION_AUDIT_2026-05-08.md` | updated-current | added 2026-05-11 supersession note and current-anchor update |
| `docs/PROJECT_ORGANIZATION_ROADMAP_2026-05-09.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `docs/realism_v2/PRD.md` | governance-contract-current | Reviewed; retained as governance/test contract and interpreted through current report 88 v3.0. |
| `docs/realism_v2/failure_mode_dashboard_template.md` | governance-contract-current | Reviewed; retained as governance/test contract and interpreted through current report 88 v3.0. |
| `docs/realism_v2/physics_spec.md` | governance-contract-current | Reviewed; retained as governance/test contract and interpreted through current report 88 v3.0. |
| `docs/realism_v2/task_list_R0_P0.md` | governance-contract-current | Reviewed; retained as governance/test contract and interpreted through current report 88 v3.0. |
| `docs/realism_v2/test_spec.md` | governance-contract-current | Reviewed; retained as governance/test contract and interpreted through current report 88 v3.0. |
| `docs/schemas/bounded_physical_solver_readiness_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/bounded_physical_solver_readiness_route_universe_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/bounded_physical_solver_readiness_schema_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/bounded_physical_solver_readiness_source_binding_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/bounded_solver_authorization_gate_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/bounded_solver_authorization_gate_p4_binding_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/bounded_solver_authorization_gate_record_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/bounded_solver_authorization_pilot_design_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/bounded_solver_authorization_pilot_design_p2_route_binding_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/bounded_solver_authorization_pilot_design_route_subset_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/bounded_solver_authorization_pilot_design_schema_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/bounded_solver_dry_run_preflight_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/bounded_solver_dry_run_preflight_execution_authorization_record_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/bounded_solver_dry_run_preflight_input_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/bounded_solver_dry_run_preflight_mesh_boundary_unit_preflight_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/bounded_solver_dry_run_preflight_p3_binding_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/ev_sample_profiles_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/fifth_bounded_solver_lane_execution_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/fifth_bounded_solver_lane_execution_output_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/fifth_bounded_solver_lane_execution_p13_authorization_binding_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/forbidden_claims_lexicon_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/fourth_bounded_solver_lane_execution_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/fourth_bounded_solver_lane_execution_output_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/fourth_bounded_solver_lane_execution_p11_authorization_binding_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/minimal_bounded_solver_execution_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/minimal_bounded_solver_execution_output_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/minimal_bounded_solver_execution_p5_binding_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/noise_readout_scenario_bundle_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p10_closure_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p10_closure_review_record_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p11_next_authorization_design_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p11_next_authorization_gate_record_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p12_closure_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p12_closure_review_record_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p13_next_authorization_design_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p13_next_authorization_gate_record_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p14_closure_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p14_closure_review_record_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p15_next_authorization_design_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p15_next_authorization_gate_record_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p16_closure_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p16_closure_review_record_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p17_next_authorization_design_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p17_next_authorization_gate_record_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p18_bounded_lane_synthesis_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p18_bounded_lane_synthesis_record_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p8_closure_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p8_closure_review_record_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p9_next_authorization_design_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/p9_next_authorization_gate_record_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/physical_ceiling_contract_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/physical_ceiling_diagnostic_schema_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/physical_ceiling_input_binding_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/physical_ceiling_route_coverage_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/post_v2_mandatory_audit_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/review_package_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/second_bounded_solver_lane_execution_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/second_bounded_solver_lane_execution_output_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/second_bounded_solver_lane_execution_p7_authorization_binding_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/second_lane_authorization_design_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/second_lane_authorization_design_authorization_gate_record_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/second_lane_authorization_design_candidate_lane_contract_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/second_lane_authorization_design_p6_evidence_binding_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/sixth_bounded_solver_lane_execution_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/sixth_bounded_solver_lane_execution_output_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/sixth_bounded_solver_lane_execution_p15_authorization_binding_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/third_bounded_solver_lane_execution_artifact_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/third_bounded_solver_lane_execution_output_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `docs/schemas/third_bounded_solver_lane_execution_p9_authorization_binding_manifest_schema.md` | schema-doc-current | Reviewed; schema contract remains current for the corresponding tests/artifacts. |
| `guides/core/01_data_objects.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `guides/core/02_materials.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `guides/core/02_mie_engine.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `guides/core/03_intrinsic_scattering.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `guides/core/04_utils.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `guides/core/05_reference_field.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `guides/core/06_illumination.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `guides/core/07_trajectory.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `guides/core/08_scattering_trace.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `guides/core/09_interferometric_trace.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `guides/core/10_pulse_analysis.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `guides/core/11_parameter_sweep.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `guides/core/12_init.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `guides/core/README.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `guides/dashboard/15_dashboard_config.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `guides/dashboard/25_dashboard_estimate_precompute_runtime.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `guides/dashboard/README.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `guides/operations/README.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `illumination.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `interface_correction.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `interferometric_trace.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `intrinsic_scattering.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `materials.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `mie_engine.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `optional_acceleration.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `papers/README.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `papers/provenance/paper_provenance_notes.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `parameter_sweep.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `photothermal_pod.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `pulse_analysis.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `realism_v2_io.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `reference_field.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `reports/100_EV_NODI_P3_bounded_solver_authorization_pilot_design_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/101_EV_NODI_P4_bounded_solver_dry_run_preflight_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/102_EV_NODI_P5_bounded_solver_authorization_gate_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/103_EV_NODI_P6_minimal_bounded_solver_execution_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/104_EV_NODI_P7_second_lane_authorization_design_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/105_EV_NODI_P8_second_bounded_solver_lane_execution_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/106_EV_NODI_P8_second_bounded_solver_lane_closure_note.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/107_EV_NODI_P9_next_bounded_lane_authorization_design_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/108_EV_NODI_P10_third_bounded_solver_lane_execution_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/109_EV_NODI_P10_third_bounded_solver_lane_closure_note.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/110_EV_NODI_P11_fourth_bounded_lane_authorization_design_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/111_EV_NODI_P12_fourth_bounded_solver_lane_execution_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/112_EV_NODI_P12_fourth_bounded_solver_lane_closure_note.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/113_EV_NODI_P13_fifth_bounded_lane_authorization_design_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/114_EV_NODI_P14_fifth_bounded_solver_lane_execution_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/115_EV_NODI_P14_fifth_bounded_solver_lane_closure_note.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/116_EV_NODI_P15_sixth_bounded_lane_authorization_design_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/117_EV_NODI_P16_sixth_bounded_solver_lane_execution_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/118_EV_NODI_P16_sixth_bounded_solver_lane_closure_note.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/119_EV_NODI_P17_seventh_bounded_lane_authorization_design_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/120_EV_NODI_P18_bounded_lane_synthesis_stop_continue_design.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/48_EV_NODI_full_recompute_external_analysis.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/49_Tsuyama_Phase2_paper_calibrated_selected_annulus_analysis.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/51_EV_NODI_realism_v2_instrument_aware_roadmap.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/52_EV_NODI_realism_v2_R2_anchor_smoke_analysis.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/53_EV_NODI_realism_v2_R3_reduced_grid_plan_for_external_review.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/54_EV_NODI_realism_v2_R3a_reduced_grid_analysis.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/55_EV_NODI_realism_v2_R3b_uncertainty_expansion_plan_for_external_review.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/56_EV_NODI_realism_v2_R3b_uncertainty_expansion_analysis.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/57_EV_NODI_realism_v2_R4_representative_full_wave_plan_for_external_review.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/58_EV_NODI_realism_v2_R4_representative_full_wave_validation_analysis.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/59_EV_NODI_realism_v2_R4_numerical_solver_rerun_analysis.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/60_EV_NODI_realism_v2_R4_route_model_revision_plan_for_external_review.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/61_EV_NODI_realism_v2_R4_route_model_revision_audit_analysis.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/62_EV_NODI_realism_v2_R4_revised_rerun_plan_for_external_review.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/63_EV_NODI_realism_v2_R4_revised_rerun_analysis.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/64_EV_NODI_realism_v2_R4_2_main660_nearwall_mesh_adjudication_plan_for_external_review.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/65_EV_NODI_realism_v2_R4_2_main660_nearwall_mesh_adjudication_analysis.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/66_EV_NODI_realism_v2_R5_full_grid_v2_plan_for_external_review.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/67_EV_NODI_realism_v2_R5_full_grid_v2_analysis.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/68_EV_NODI_realism_v2_R5_1_route_role_stability_interpretation_plan_for_external_review.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/69_EV_NODI_realism_v2_R5_1_route_role_stability_interpretation_analysis.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/70_EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit_plan_for_external_review.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/71_EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit_analysis.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/72_EV_NODI_realism_v2_R5_3_route_prior_model_revision_plan_for_external_review.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/73_EV_NODI_realism_v2_R5_3_route_prior_model_revision_audit_analysis.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/74_EV_NODI_realism_v2_R6_route_prior_sensitivity_plan_for_external_review.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/75_EV_NODI_realism_v2_R6_route_prior_sensitivity_audit_analysis.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/76_EV_NODI_realism_v2_R7_route_prior_mechanistic_decomposition_plan_for_external_review.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/77_EV_NODI_realism_v2_R7_route_prior_mechanistic_decomposition_audit_analysis.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/78_EV_NODI_realism_v2_R7_1_operator_artifact_validation_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/79_EV_NODI_realism_v2_R7_1_operator_artifact_validation_protocol_analysis.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/80_EV_NODI_realism_v2_R7_2_operator_artifact_gap_register_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/81_EV_NODI_realism_v2_R7_2_operator_artifact_gap_register_generation_analysis.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/85_EV_NODI_realism_v2_target_alignment_self_review.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/86_EV_NODI_realism_v2_no_measured_data_closure_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md` | updated-current | updated in place to v3.0 with realism v2 plus P0-P18 merged conclusions |
| `reports/89_EV_NODI_post_v2_unmodeled_realism_register.md` | updated-current | added 2026-05-11 status note and P0-P18/P19 evidence-strategy boundary |
| `reports/90_EV_NODI_post_v2_review_ready_relative_audit_roadmap.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/91_EV_NODI_post_v2_P0_release_completion_note.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/92_EV_NODI_P1_physical_ceiling_extensions_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/93_EV_NODI_P1_full_wave_green_tensor_diagnostic_contract.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/94_EV_NODI_P1_vector_jones_polarization_diagnostic_contract.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/95_EV_NODI_P1_roughness_leakage_diagnostic_contract.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/96_EV_NODI_P1_transport_residence_time_diagnostic_contract.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/97_EV_NODI_P1_physical_ceiling_contract_manifest_completion_note.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/98_EV_NODI_P2_bounded_physical_solver_readiness_plan.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/99_EV_NODI_P2_bounded_physical_solver_readiness_completion_note.md` | stage-evidence-preserved | Reviewed; preserved as stage evidence. Current conclusions are consolidated in report 88 v3.0. |
| `reports/current/35_method_notes.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `reports/current/36_exosome_biomimetic_surface_model.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `reports/current/README.md` | updated-current | updated current-report status to report 88 v3.0 and clarified report 47 historical status |
| `results/post_v2_bounded_lane_synthesis_stop_continue/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_bounded_physical_solver_readiness/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_bounded_solver_authorization_gate/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_bounded_solver_authorization_pilot_design/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_bounded_solver_dry_run_preflight/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_fifth_bounded_lane_authorization_design/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_fifth_bounded_solver_lane_closure/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_fifth_bounded_solver_lane_execution/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_fourth_bounded_lane_authorization_design/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_fourth_bounded_solver_lane_closure/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_fourth_bounded_solver_lane_execution/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_mandatory_audit/top_candidate_mandatory_audit_readme.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_minimal_bounded_solver_execution/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_next_bounded_lane_authorization_design/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_physical_ceiling/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_second_bounded_solver_lane_closure/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_second_bounded_solver_lane_execution/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_second_lane_authorization_design/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_seventh_bounded_lane_authorization_design/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_sixth_bounded_lane_authorization_design/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_sixth_bounded_solver_lane_closure/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_sixth_bounded_solver_lane_execution/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_third_bounded_solver_lane_closure/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `results/post_v2_third_bounded_solver_lane_execution/README.md` | result-artifact-doc-preserved | Reviewed; result artifact README remains provenance for generated outputs, not reader entry point. |
| `scattering_trace.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `tests/run_tests.md` | updated-current | added AppleDouble mounted-storage verification caveat |
| `tools/README.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `trajectory.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `type_coerce.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `utils.md` | current-or-companion-doc-reviewed | Reviewed; no direct content change needed after navigation/report updates. |
| `reports/121_EV_NODI_full_update_review_ledger_2026-05-11.md` | updated-current | new ledger for full report merge, file-by-file code review, documentation review, and verification evidence |

## Consistency conclusion

Report 88 v3.0, README, navigation docs, report-current index, report 89, historical supersession generator/output, review-package manifests, and this ledger now agree that P0-P18 are no-measured-data relative-audit/trace-only evidence. The six bounded trace lanes are sufficient to show rank instability, not sufficient for route promotion. Remaining high-value work is P19 evidence strategy, measured blank/BFP artifacts, standard-particle calibration, full-wave spot checks, and future type-coverage expansion.
