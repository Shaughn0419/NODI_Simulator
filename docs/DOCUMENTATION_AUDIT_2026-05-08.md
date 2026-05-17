# Documentation Audit 2026-05-08

Purpose: record every Markdown documentation file covered by the documentation cleanup/audit pass, including active docs and archived historical docs, so future readers can see which files are current entry points and which files are preserved provenance snapshots.

2026-05-14 status note: this audit is a historical file-coverage snapshot. The
current reader-facing single source of truth is now
`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`
v5.2.6, including the completed lens-B EV+gold full-grid final. Use
`文档导航.md` for current entry ordering.

2026-05-11 status note: at that time, the reader-facing single source of truth became
`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`
v3.0. It merges the v1 full-grid analysis, realism v2 no-measured-data closure,
P0 review-ready relative audit, and P1-P18 bounded physical-ceiling /
trace-governance conclusions. Use
`reports/121_EV_NODI_full_update_review_ledger_2026-05-11.md` for the 2026-05-11
code-review and documentation-update ledger.

2026-05-09 status note: package-module implementations and current companion
docs now use canonical `nodi_simulator/<module>.py` paths; root
package-module compatibility wrappers have been retired. Treat this audit as a
file-coverage snapshot, not the latest migration-status source. Use
`docs/PROJECT_ORGANIZATION_ROADMAP_2026-05-09.md` for current organization
state.

Scope excludes generated/runtime/vendor/extracted-text areas: `.venv*`, `.venv-tests/`, `.codex_pdf_venv/`, `.pytest_cache/`, `.pytest_vendor/`, `.omx/`, `.claude/`, `.pdf_output/`, `results/`, and `review_bundles/`. AppleDouble `._*.md` metadata files are not documentation and are deleted when found.

Current interpretation anchors:

- `README.md` and `文档导航.md` for navigation.
- `reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md` for reader-facing v1/v2 interpretation.
- `reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` and `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` for v2 no-measured-data boundary.
- `reports/89_EV_NODI_post_v2_unmodeled_realism_register.md` for post-v2 realism gaps that are acknowledged but not solved inside v2.
- `reports/90-120` for post-v2 P0-P18 provenance; at the 2026-05-11 audit point their conclusions were consolidated into report 88 v3.0, and the current entry order is now governed by report 88 v5.2.6 plus `文档导航.md`.
- `reports/121_EV_NODI_full_update_review_ledger_2026-05-11.md` for this later audit/update pass.

Forbidden-current-claim reminder: v2 and P0-P18 have no measured data and do not authorize calibrated SNR, calibrated event probability, absolute LOD, true EV concentration, biological specificity, measured blank safety, route promotion, main-660 redefinition, selected-annulus replacement of all-crossing ranking, or use of P6-P16 trace ordering as a single main-660 champion.

Covered active Markdown files: 117
Covered archived Markdown files: 56
Covered Markdown files total: 173

Archive rule: every `archive/` Markdown file is marked as historical provenance and must not be read as current truth unless a current entry document explicitly re-adopts it.

| File | Audit class |
|---|---|
| `00_工程总指南.md` | root-governance-or-theory-current/historical-marked |
| `24_高性能预计算与增量重算方案.md` | root-governance-or-theory-current/historical-marked |
| `25_核心计算逻辑与公式总说明.md` | root-governance-or-theory-current/historical-marked |
| `26_评分复盘与现状分析.md` | root-governance-or-theory-current/historical-marked |
| `34_完整全波理论推导与当前模型边界.md` | root-governance-or-theory-current/historical-marked |
| `41_实验对齐原则与计算修正备忘.md` | root-governance-or-theory-current/historical-marked |
| `42_全量重算前复核结论与现行边界.md` | root-governance-or-theory-current/historical-marked |
| `43_Tsuyama对齐主链升级路线图与修改框架.md` | root-governance-or-theory-current/historical-marked |
| `README.md` | entry-current |
| `archive/README.md` | archive-historical-marked-not-current |
| `archive/dashboard/16_dashboard_precompute.full.md` | archive-historical-marked-not-current |
| `archive/dashboard/17_dashboard_app.full.md` | archive-historical-marked-not-current |
| `archive/dashboard/18_dashboard_backend.full.md` | archive-historical-marked-not-current |
| `archive/dashboard/19_dashboard_explorer.full.md` | archive-historical-marked-not-current |
| `archive/dashboard/20_dashboard_inspector.full.md` | archive-historical-marked-not-current |
| `archive/dashboard/22_dashboard_interference_explorer.full.md` | archive-historical-marked-not-current |
| `archive/dashboard/23_dashboard_noise_detection_explorer.full.md` | archive-historical-marked-not-current |
| `archive/dashboard/26_dashboard_mie_explorer.full.md` | archive-historical-marked-not-current |
| `archive/dashboard/27_dashboard_common.full.md` | archive-historical-marked-not-current |
| `archive/dashboard/28_修改框架与完善路线图.full.md` | archive-historical-marked-not-current |
| `archive/dashboard/29_dashboard_single_case_calculator.md` | archive-historical-marked-not-current |
| `archive/dashboard/30_dashboard_single_case_calculator.full.md` | archive-historical-marked-not-current |
| `archive/dashboard/README.md` | archive-historical-marked-not-current |
| `archive/docx/NODI_Core_Computation_Logic_EN_Expanded_Reformatted.md` | archive-historical-marked-not-current |
| `archive/docx/NODI_核心计算逻辑详解_扩充版_Reformatted.md` | archive-historical-marked-not-current |
| `archive/docx/README.md` | archive-historical-marked-not-current |
| `archive/reports/31_exosome_50_150_focus_test.md` | archive-historical-marked-not-current |
| `archive/reports/32_exosome_50_150_focus_404_analysis.md` | archive-historical-marked-not-current |
| `archive/reports/33_full_range_4w_analysis.md` | archive-historical-marked-not-current |
| `archive/reports/35.4_最新全量数据库全面复核与选型报告.full.md` | archive-historical-marked-not-current |
| `archive/reports/35_10000e_exosome_selection_report.md` | archive-historical-marked-not-current |
| `archive/reports/README.md` | archive-historical-marked-not-current |
| `archive/tsuyama/43_tsuyama论文与工程全面复核笔记.md` | archive-historical-marked-not-current |
| `archive/tsuyama/44_tsuyama_gold读出phase_gate对照复核.md` | archive-historical-marked-not-current |
| `archive/tsuyama/45_phase_gate跨对象敏感性复核.md` | archive-historical-marked-not-current |
| `archive/tsuyama/46_主路线一致性审计.md` | archive-historical-marked-not-current |
| `archive/tsuyama/47_tsuyama修正闭环清单.md` | archive-historical-marked-not-current |
| `archive/tsuyama/48_tsuyama六篇严格补读结论.md` | archive-historical-marked-not-current |
| `archive/tsuyama/49_tsuyama宽深记号与当前reference_surrogate复核.md` | archive-historical-marked-not-current |
| `archive/tsuyama/50_paper_aligned_reference对照结果.md` | archive-historical-marked-not-current |
| `archive/tsuyama/51_tsuyama_paper_aligned全论文闭环审查.md` | archive-historical-marked-not-current |
| `archive/tsuyama/52_paper_aligned_profiles说明.md` | archive-historical-marked-not-current |
| `archive/tsuyama/53_paper_aligned_nodi2022最小决策网格结果.md` | archive-historical-marked-not-current |
| `archive/tsuyama/54_tsuyama核心计算流程_中英对照.md` | archive-historical-marked-not-current |
| `archive/tsuyama/55_tsuyama散射与干涉增强主链_精简版.md` | archive-historical-marked-not-current |
| `archive/tsuyama/56_tsuyama已解决与尚未解决问题_中英对照表.md` | archive-historical-marked-not-current |
| `archive/tsuyama/57_工程主线与Tsuyama论文结果趋势对照_中英对照.md` | archive-historical-marked-not-current |
| `archive/tsuyama/58_tsuyama固定条件对标与结果表.md` | archive-historical-marked-not-current |
| `archive/tsuyama/59_Tsuyama对齐主链升级路线图与修改框架_2026-04-24完成态.md` | archive-historical-marked-not-current |
| `archive/tsuyama/README.md` | archive-historical-marked-not-current |
| `archive/tsuyama/probe_pre_20260502/README.md` | archive-historical-marked-not-current |
| `archive/tsuyama/probe_pre_20260502/tsuyama_2022_classification_lane_smoke_20260501/tsuyama_2022_classification_report_v1.md` | archive-historical-marked-not-current |
| `archive/tsuyama/probe_pre_20260502/tsuyama_2022_classification_lane_svm_status_smoke_20260501/tsuyama_2022_classification_report_v1.md` | archive-historical-marked-not-current |
| `archive/tsuyama/probe_pre_20260502/tsuyama_2022_classification_lane_v2_smoke_20260501/tsuyama_2022_classification_report_v2.md` | archive-historical-marked-not-current |
| `archive/tsuyama/probe_pre_20260502/tsuyama_annulus_ratio_sensitivity_smoke_debug2/annulus_ratio_sensitivity_decision_v1.md` | archive-historical-marked-not-current |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_annulus_full_chain_probe_20260501/44_Tsuyama_gold_aligned_detection_lane_report.md` | archive-historical-marked-not-current |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_annulus_joint_fit_inphase_probe_20260501/selected_annulus_joint_fit_report.md` | archive-historical-marked-not-current |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_annulus_joint_fit_smoke_20260501/selected_annulus_joint_fit_report.md` | archive-historical-marked-not-current |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_annulus_joint_fit_transfer_probe_20260501/selected_annulus_joint_fit_report.md` | archive-historical-marked-not-current |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_annulus_joint_fit_v2_geometry_smoke_20260501/selected_annulus_joint_fit_report.md` | archive-historical-marked-not-current |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_annulus_joint_fit_v2_size_diag_smoke_20260501/selected_annulus_joint_fit_report.md` | archive-historical-marked-not-current |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_annulus_joint_fit_v2_size_response_smoke_20260501/selected_annulus_joint_fit_report.md` | archive-historical-marked-not-current |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_annulus_more_cases_probe/selected_annulus_more_cases_report_v1.md` | archive-historical-marked-not-current |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_annulus_nonempty_ev_panel_probe_20260501/44_Tsuyama_gold_aligned_detection_lane_report.md` | archive-historical-marked-not-current |
| `archive/tsuyama/probe_pre_20260502/tsuyama_selected_detector_mode_fulltest_annulus_0p5_0p8/tsuyama_detection_rate_calibration_report.md` | archive-historical-marked-not-current |
| `count_generation.md` | module-companion-current |
| `dashboard/app.md` | module-companion-current |
| `dashboard/backend.md` | module-companion-current |
| `dashboard/config.md` | module-companion-current |
| `dashboard/estimate_precompute_runtime.md` | module-companion-current |
| `dashboard/mie_backend.md` | module-companion-current |
| `dashboard/panels/common.md` | module-companion-current |
| `dashboard/panels/explorer.md` | module-companion-current |
| `dashboard/panels/inspector.md` | module-companion-current |
| `dashboard/panels/interference_explorer.md` | module-companion-current |
| `dashboard/panels/mie_explorer.md` | module-companion-current |
| `dashboard/panels/noise_detection_explorer.md` | module-companion-current |
| `dashboard/panels/research_story.md` | module-companion-current |
| `dashboard/panels/single_case_calculator.md` | module-companion-current |
| `dashboard/precompute.md` | module-companion-current |
| `dashboard/signal_backend.md` | module-companion-current |
| `data_objects.md` | module-companion-current |
| `docs/DOCUMENTATION_AUDIT_2026-05-08.md` | audit-index |
| `docs/realism_v2/PRD.md` | v2-contract-current-with-history-note |
| `docs/realism_v2/failure_mode_dashboard_template.md` | v2-contract-current-with-history-note |
| `docs/realism_v2/physics_spec.md` | v2-contract-current-with-history-note |
| `docs/realism_v2/task_list_R0_P0.md` | v2-contract-current-with-history-note |
| `docs/realism_v2/test_spec.md` | v2-contract-current-with-history-note |
| `guides/core/01_data_objects.md` | guide-current-or-historical-marked |
| `guides/core/02_materials.md` | guide-current-or-historical-marked |
| `guides/core/02_mie_engine.md` | guide-current-or-historical-marked |
| `guides/core/03_intrinsic_scattering.md` | guide-current-or-historical-marked |
| `guides/core/04_utils.md` | guide-current-or-historical-marked |
| `guides/core/05_reference_field.md` | guide-current-or-historical-marked |
| `guides/core/06_illumination.md` | guide-current-or-historical-marked |
| `guides/core/07_trajectory.md` | guide-current-or-historical-marked |
| `guides/core/08_scattering_trace.md` | guide-current-or-historical-marked |
| `guides/core/09_interferometric_trace.md` | guide-current-or-historical-marked |
| `guides/core/10_pulse_analysis.md` | guide-current-or-historical-marked |
| `guides/core/11_parameter_sweep.md` | guide-current-or-historical-marked |
| `guides/core/12_init.md` | guide-current-or-historical-marked |
| `guides/core/README.md` | guide-current-or-historical-marked |
| `guides/dashboard/15_dashboard_config.md` | guide-current-or-historical-marked |
| `guides/dashboard/25_dashboard_estimate_precompute_runtime.md` | guide-current-or-historical-marked |
| `guides/dashboard/28_修改框架与完善路线图.md` | guide-current-or-historical-marked |
| `guides/dashboard/README.md` | guide-current-or-historical-marked |
| `guides/operations/14_测试说明.md` | guide-current-or-historical-marked |
| `guides/operations/15_无实测数据时如何接入未来校准数据.md` | guide-current-or-historical-marked |
| `guides/operations/README.md` | guide-current-or-historical-marked |
| `illumination.md` | module-companion-current |
| `interface_correction.md` | module-companion-current |
| `interferometric_trace.md` | module-companion-current |
| `intrinsic_scattering.md` | module-companion-current |
| `materials.md` | module-companion-current |
| `mie_engine.md` | module-companion-current |
| `optional_acceleration.md` | module-companion-current |
| `papers/README.md` | reference-bibliography-doc-current |
| `parameter_sweep.md` | module-companion-current |
| `photothermal_pod.md` | module-companion-current |
| `pulse_analysis.md` | module-companion-current |
| `reference_field.md` | module-companion-current |
| `realism_v2_io.md` | module-companion-current |
| `reports/48_EV_NODI_full_recompute_external_analysis.md` | stage-evidence-report-preserved |
| `reports/49_Tsuyama_Phase2_paper_calibrated_selected_annulus_analysis.md` | stage-evidence-report-preserved |
| `reports/50_计算侧收口总结与工程瘦身记录.md` | stage-evidence-report-preserved |
| `reports/51_EV_NODI_realism_v2_instrument_aware_roadmap.md` | stage-evidence-report-preserved |
| `reports/52_EV_NODI_realism_v2_R2_anchor_smoke_analysis.md` | stage-evidence-report-preserved |
| `reports/53_EV_NODI_realism_v2_R3_reduced_grid_plan_for_external_review.md` | stage-evidence-report-preserved |
| `reports/54_EV_NODI_realism_v2_R3a_reduced_grid_analysis.md` | stage-evidence-report-preserved |
| `reports/55_EV_NODI_realism_v2_R3b_uncertainty_expansion_plan_for_external_review.md` | stage-evidence-report-preserved |
| `reports/56_EV_NODI_realism_v2_R3b_uncertainty_expansion_analysis.md` | stage-evidence-report-preserved |
| `reports/57_EV_NODI_realism_v2_R4_representative_full_wave_plan_for_external_review.md` | stage-evidence-report-preserved |
| `reports/58_EV_NODI_realism_v2_R4_representative_full_wave_validation_analysis.md` | stage-evidence-report-preserved |
| `reports/59_EV_NODI_realism_v2_R4_numerical_solver_rerun_analysis.md` | stage-evidence-report-preserved |
| `reports/60_EV_NODI_realism_v2_R4_route_model_revision_plan_for_external_review.md` | stage-evidence-report-preserved |
| `reports/61_EV_NODI_realism_v2_R4_route_model_revision_audit_analysis.md` | stage-evidence-report-preserved |
| `reports/62_EV_NODI_realism_v2_R4_revised_rerun_plan_for_external_review.md` | stage-evidence-report-preserved |
| `reports/63_EV_NODI_realism_v2_R4_revised_rerun_analysis.md` | stage-evidence-report-preserved |
| `reports/64_EV_NODI_realism_v2_R4_2_main660_nearwall_mesh_adjudication_plan_for_external_review.md` | stage-evidence-report-preserved |
| `reports/65_EV_NODI_realism_v2_R4_2_main660_nearwall_mesh_adjudication_analysis.md` | stage-evidence-report-preserved |
| `reports/66_EV_NODI_realism_v2_R5_full_grid_v2_plan_for_external_review.md` | stage-evidence-report-preserved |
| `reports/67_EV_NODI_realism_v2_R5_full_grid_v2_analysis.md` | stage-evidence-report-preserved |
| `reports/68_EV_NODI_realism_v2_R5_1_route_role_stability_interpretation_plan_for_external_review.md` | stage-evidence-report-preserved |
| `reports/69_EV_NODI_realism_v2_R5_1_route_role_stability_interpretation_analysis.md` | stage-evidence-report-preserved |
| `reports/70_EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit_plan_for_external_review.md` | stage-evidence-report-preserved |
| `reports/71_EV_NODI_realism_v2_R5_2_bounded_scenario_prior_audit_analysis.md` | stage-evidence-report-preserved |
| `reports/72_EV_NODI_realism_v2_R5_3_route_prior_model_revision_plan_for_external_review.md` | stage-evidence-report-preserved |
| `reports/73_EV_NODI_realism_v2_R5_3_route_prior_model_revision_audit_analysis.md` | stage-evidence-report-preserved |
| `reports/74_EV_NODI_realism_v2_R6_route_prior_sensitivity_plan_for_external_review.md` | stage-evidence-report-preserved |
| `reports/75_EV_NODI_realism_v2_R6_route_prior_sensitivity_audit_analysis.md` | stage-evidence-report-preserved |
| `reports/76_EV_NODI_realism_v2_R7_route_prior_mechanistic_decomposition_plan_for_external_review.md` | stage-evidence-report-preserved |
| `reports/77_EV_NODI_realism_v2_R7_route_prior_mechanistic_decomposition_audit_analysis.md` | stage-evidence-report-preserved |
| `reports/78_EV_NODI_realism_v2_R7_1_operator_artifact_validation_plan.md` | stage-evidence-report-preserved |
| `reports/79_EV_NODI_realism_v2_R7_1_operator_artifact_validation_protocol_analysis.md` | stage-evidence-report-preserved |
| `reports/80_EV_NODI_realism_v2_R7_2_operator_artifact_gap_register_plan.md` | stage-evidence-report-preserved |
| `reports/81_EV_NODI_realism_v2_R7_2_operator_artifact_gap_register_generation_analysis.md` | stage-evidence-report-preserved |
| `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` | current-v2-reader-boundary-report |
| `reports/85_EV_NODI_realism_v2_target_alignment_self_review.md` | stage-evidence-report-preserved |
| `reports/86_EV_NODI_realism_v2_no_measured_data_closure_plan.md` | stage-evidence-report-preserved |
| `reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` | current-v2-reader-boundary-report |
| `reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md` | current-v2-reader-boundary-report |
| `reports/89_EV_NODI_post_v2_unmodeled_realism_register.md` | post-v2-boundary-register-current |
| `reports/current/35_method_notes.md` | current-reports-indexed-historical-where-needed |
| `reports/current/36_exosome_biomimetic_surface_model.md` | current-reports-indexed-historical-where-needed |
| `reports/current/46_全量计算性能优化复核.md` | current-reports-indexed-historical-where-needed |
| `reports/current/47_EV_NODI全量结果分层分析报告.md` | current-reports-indexed-historical-where-needed |
| `reports/current/README.md` | current-reports-indexed-historical-where-needed |
| `scattering_trace.md` | module-companion-current |
| `tests/run_tests.md` | test-operation-doc-current |
| `trajectory.md` | module-companion-current |
| `type_coerce.md` | module-companion-current |
| `utils.md` | module-companion-current |
| `文档导航.md` | entry-current |
