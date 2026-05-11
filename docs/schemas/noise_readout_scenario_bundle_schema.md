# Noise/Readout Scenario Bundle Schema

The post-v2 noise audit extends `configs/realism_v2/r5_scenario_bundle_manifest.yaml` by reference. Pass criteria are relative rank-percentile stability versus nominal; SNR, false-positive, and absolute margin floors remain blocked.

## Artifact-field alignment note

These fields are present in the paired artifact payload and are checked by schema drift audit:

- `absolute_snr_gate_used`
- `event_probability_claim_level`
- `fixed_margin_z_floor_used`
- `forked_scenario_ids_allowed`
- `mean_detectability_relative_prior_score`
- `n_case_rows`
- `noise_pass_criterion_claim_level`
- `p_detect_mapping_claim_level`
- `scenario_alias_map`
- `scenario_bundle_definition_checksum`
- `source_scenario_manifest_sha256`
- `source_summary_sha256`
- `snr_claim_level`

