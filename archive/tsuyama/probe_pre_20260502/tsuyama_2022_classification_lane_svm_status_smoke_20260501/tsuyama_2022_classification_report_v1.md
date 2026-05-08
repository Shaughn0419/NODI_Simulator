# Tsuyama 2022 Linked 488/532 Classification Lane

<!-- ARCHIVE_STATUS:START -->
> 归档状态：历史快照，仅保留当时推理、实验性计算或迁移记录；不代表当前 v1/v2 结论。当前读者入口请以 `README.md`、`文档导航.md`、`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`、`reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` 和 `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` 为准。
<!-- ARCHIVE_STATUS:END -->

> Historical v1 output: this run is superseded by `results/tsuyama_2022_classification_lane_v2_smoke_20260501/`, where the feature policy uses the detected 488 pulse window and the 532 maximum within that window. Keep this file only as provenance for the older feature-export-only protocol.

## Scope

- This lane exports linked 488/532 event features for the 2022 Au/Ag classification protocol.
- It does not modify joint-fit scoring, global simulator defaults, or EV ranking.
- Exact paper accuracy remains blocked until the 532 feature is measured as the maximum within the 488 pulse window and an SVM dependency is available.
- Any computed SVM value is a surrogate accuracy, not a paper-exact claim.

## Metadata

- schema: `tsuyama_2022_linked_488_532_classification_protocol_v1`
- candidate: `baseline_current_estimates__paper_5sigma_signal_transfer_fit`
- scenario: `nodi_2022_10sigma_single`
- geometry: `800x550`
- n_events/class: `10`
- random_seed: `42`

## Summary

| schema_id                                              | n_events_requested_per_class | width_nm | depth_nm | class_count | feature_rows | usable_both_detected_rows | usable_min_class_count | usable_class_counts_json              | paper_transfer_gain_488 | paper_transfer_gain_532 | classification_feature_policy                                    | paper_protocol_match_status                                                 | sklearn_available | svm_accuracy_status                              | svm_accuracy_claim_level |
| ------------------------------------------------------ | ---------------------------- | -------- | -------- | ----------- | ------------ | ------------------------- | ---------------------- | ------------------------------------- | ----------------------- | ----------------------- | ---------------------------------------------------------------- | --------------------------------------------------------------------------- | ----------------- | ------------------------------------------------ | ------------------------ |
| tsuyama_2022_linked_488_532_classification_protocol_v1 | 10                           | 800      | 550      | 4           | 40           | 25                        | 6                      | {"Ag40":6,"Ag60":7,"Au40":6,"Au60":6} | 2.57689                 | 1.67348                 | linked_488_532_best_detected_peak_features_by_common_event_index | feature_export_only_not_paper_exact_missing_532_max_within_488_pulse_window | False             | not_computed_missing_optional_sklearn_dependency | no_accuracy_claim        |

## Output Files

- `tsuyama_2022_classification_features_v1.csv`
- `tsuyama_2022_classification_summary_v1.csv`
- `tsuyama_2022_classification_meta_v1.json`
