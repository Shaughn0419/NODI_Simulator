# Tsuyama 2022 Linked 488/532 Classification Lane

<!-- ARCHIVE_STATUS:START -->
> 归档状态：历史快照，仅保留当时推理、实验性计算或迁移记录；不代表当前 v1/v2 结论。当前读者入口请以 `README.md`、`文档导航.md`、`reports/88_EV_NODI_v1_v2_consolidated_reader_analysis_with_Tsuyama_comparison.md`、`reports/87_EV_NODI_realism_v2_no_measured_data_closure_analysis.md` 和 `reports/84_EV_NODI_realism_v2_no_measured_data_consolidated_roadmap.md` 为准。
<!-- ARCHIVE_STATUS:END -->

## Scope

- This lane exports linked 488/532 event features for the 2022 Au/Ag classification protocol.
- It does not modify joint-fit scoring, global simulator defaults, or EV ranking.
- The 532 feature is measured as the maximum within the matched 488 pulse window.
- Any computed SVM value is simulated feature accuracy, not an experimental reproduction claim.

## Metadata

- schema: `tsuyama_2022_linked_488_window_532_max_classification_protocol_v2`
- candidate: `baseline_current_estimates__paper_5sigma_signal_transfer_fit`
- scenario: `nodi_2022_10sigma_single`
- geometry: `800x550`
- n_events/class: `20`
- random_seed: `42`

## Summary

| schema_id                                                         | n_events_requested_per_class | width_nm | depth_nm | class_count | feature_rows | usable_both_detected_rows | usable_for_paper_svm_rows | usable_min_class_count | usable_class_counts_json                  | paper_transfer_gain_488 | paper_transfer_gain_532 | classification_feature_policy                | paper_protocol_match_status                                  | sklearn_available | svm_accuracy_status                              | svm_accuracy_claim_level |
| ----------------------------------------------------------------- | ---------------------------- | -------- | -------- | ----------- | ------------ | ------------------------- | ------------------------- | ---------------------- | ----------------------------------------- | ----------------------- | ----------------------- | -------------------------------------------- | ------------------------------------------------------------ | ----------------- | ------------------------------------------------ | ------------------------ |
| tsuyama_2022_linked_488_window_532_max_classification_protocol_v2 | 20                           | 800      | 550      | 4           | 80           | 46                        | 46                        | 10                     | {"Ag40":10,"Ag60":12,"Au40":12,"Au60":12} | 2.75554                 | 1.78061                 | linked_488_detected_pulse_window_532_maximum | feature_export_matches_488_pulse_window_532_maximum_protocol | False             | not_computed_missing_optional_sklearn_dependency | no_accuracy_claim        |

## Output Files

- `tsuyama_2022_classification_features_v2.csv`
- `tsuyama_2022_classification_summary_v2.csv`
- `tsuyama_2022_classification_meta_v2.json`
