# Noise/Readout Scenario Bundle Schema

The post-v2 noise audit extends `configs/realism_v2/r5_scenario_bundle_manifest.yaml` by reference. Pass criteria are relative rank-percentile stability versus nominal; SNR, false-positive, and absolute margin floors remain blocked.

Tracked scenario-bundle manifest keys from `configs/realism_v2/noise_readout_scenario_bundle.yaml`:

- `extends_scenario_bundle_id`
- `forked_scenario_ids_allowed`
- `pass_criterion_id`
- `required_scenario_ids`
- `scenario_alias_map`
- `source_scenario_manifest_path`
- `source_scenario_manifest_sha256`

Top-level columns in `results/post_v2_mandatory_audit/noise_readout_scenario_bundle.csv`:

- `absolute_snr_gate_used`
- `event_probability_claim_level`
- `fixed_margin_z_floor_used`
- `mean_detectability_relative_prior_score`
- `n_case_rows`
- `noise_pass_criterion_claim_level`
- `p_detect_mapping_claim_level`
- `scenario_bundle_definition_checksum`
- `snr_claim_level`
- `source_summary_path`
- `source_summary_sha256`
