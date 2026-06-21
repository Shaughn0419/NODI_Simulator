# Report 197 - NODI PRS Route/View Expansion for Gate 1

Date: 2026-06-18

## Disposition

`PASS_PRS_ROUTE_VIEW_EXPANSION_GATE1_PRS_COVERAGE_UNBLOCKED`

This report records the PRS expansion performed after Report 196 identified six
Gate 1 route/view keys blocked by missing PRS coverage. The expansion used only
NODI PRS source-accumulation sidecars and existing production gates. It did not
run COMSOL, generate `JOINT_ROUTE_CLASS`, perform q_ch weighting, compute yield,
select a winner, compute detection probability, claim true `W_eff`, claim
measured geometry, claim optical solver output, claim fabrication release, or
make P3 solver conclusions.

## Scope

Targeted missing Report 196 route/view keys:

```text
404/W500/D1200 fixed_660_gold
404/W500/D1200 per_wavelength_gold
660/W800/D900 fixed_660_gold
660/W800/D900 per_wavelength_gold
660/W800/D1200 fixed_660_gold
660/W800/D1200 per_wavelength_gold
```

Selected campaign shards:

```text
PRS_ACCUM_CAMPAIGN_SHARD_0007
PRS_ACCUM_CAMPAIGN_SHARD_0027
PRS_ACCUM_CAMPAIGN_SHARD_0033
```

Shard `0007` and shard `0033` are transition shards. They intentionally bring
the 300 nm tail of the prior D900 route plus the first 40 nm D1200 route/view
coverage. This report therefore claims route/view key coverage, not complete
all-diameter coverage for the expanded route families.

## Accumulation Results

Each selected shard was accumulated to 528144 events, slightly below the
529200-event planned count but sufficient for the edge-primary production
eligibility policy.

Batch reports:

```text
tmp/nodi_position_response_source_accumulation_campaign_shard0007_accumulator_batch_chunk009_023_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_BATCH_REPORT_20260618.json
tmp/nodi_position_response_source_accumulation_campaign_shard0027_accumulator_batch_chunk009_023_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_BATCH_REPORT_20260618.json
tmp/nodi_position_response_source_accumulation_campaign_shard0033_accumulator_batch_chunk009_023_20260618/NODI_POSITION_RESPONSE_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_BATCH_REPORT_20260618.json
```

Batch statuses:

```text
0007: PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_BATCH_NOT_PRODUCTION
0027: PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_BATCH_NOT_PRODUCTION
0033: PASS_PRS_SOURCE_ACCUMULATION_CAMPAIGN_SHARD_ACCUMULATOR_BATCH_NOT_PRODUCTION
```

Eligibility statuses:

```text
0007: PASS_PRS_SOURCE_PRODUCTION_ELIGIBILITY_EDGE_PRIMARY_NOT_PRODUCTION
0027: PASS_PRS_SOURCE_PRODUCTION_ELIGIBILITY_EDGE_PRIMARY_NOT_PRODUCTION
0033: PASS_PRS_SOURCE_PRODUCTION_ELIGIBILITY_EDGE_PRIMARY_NOT_PRODUCTION
```

Edge-primary candidate statuses:

```text
0007: PASS_PRS_EDGE_PRIMARY_CANDIDATE_VALIDATED_NOT_PROMOTED
0027: PASS_PRS_EDGE_PRIMARY_CANDIDATE_VALIDATED_NOT_PROMOTED
0033: PASS_PRS_EDGE_PRIMARY_CANDIDATE_VALIDATED_NOT_PROMOTED
```

Each new candidate contains 1868 rows and has:

```text
xz_primary_promoted_row_count: 0
```

## Candidate Merge

New helper:

```text
tools/audits/merge_nodi_position_response_edge_primary_candidates.py
```

The helper only copies already validated PRS candidate rows, blocks duplicate
route/diameter/view/bin keys, and revalidates the merged PRS contract. It does
not generate measurements or change claim semantics.

Merge report:

```text
tmp/nodi_position_response_edge_primary_candidate_merged_route_view_expansion_20260618/NODI_POSITION_RESPONSE_EDGE_PRIMARY_CANDIDATE_MERGE_REPORT_20260618.json
```

Merge result:

```text
status: PASS_PRS_EDGE_PRIMARY_CANDIDATE_MERGED_VALIDATED_NOT_PROMOTED
report_sha256: 220d4ac73f49cbc2b78d54e47f1b1cd518a8f51f90b1f8666a1d6ba82745f046
candidate_csv_sha256: 9ba83c84a563cd856b2fc624c523843a6e283206d5ac2e592a2b72607645f393
candidate rows: 7472
route/diameter/view grains: 16
rows per grain: 467
```

Merged PRS row composition:

```text
edge_norm_primary: 368
xz_norm_diagnostic: 7104
xz_norm_primary_if_adequate: 0
```

## Expanded Production Gate

Production-generation report:

```text
tmp/nodi_next_artifacts_production_generation_prs_route_view_expansion_20260618/NODI_NEXT_ARTIFACTS_PRODUCTION_GENERATION_REPORT_20260618.json
```

Result:

```text
status: PASS_PRODUCTION_GENERATION
report_sha256: 5402671927e8e5d57e23f490c4e0d801c1d04f07e3fd5e8acd63bd7c18ff30ba
NODI_POSITION_RESPONSE_SURFACE.csv sha256: 9ba83c84a563cd856b2fc624c523843a6e283206d5ac2e592a2b72607645f393
NODI_POSITION_RESPONSE_SURFACE.csv rows: 7472
```

Expanded PRS grains:

```text
404/W500/D1200 40 fixed_660_gold
404/W500/D1200 40 per_wavelength_gold
404/W500/D900 40 fixed_660_gold
404/W500/D900 40 per_wavelength_gold
404/W500/D900 60 fixed_660_gold
404/W500/D900 60 per_wavelength_gold
404/W500/D900 300 fixed_660_gold
404/W500/D900 300 per_wavelength_gold
660/W800/D1200 40 fixed_660_gold
660/W800/D1200 40 per_wavelength_gold
660/W800/D900 40 fixed_660_gold
660/W800/D900 40 per_wavelength_gold
660/W800/D900 60 fixed_660_gold
660/W800/D900 60 per_wavelength_gold
660/W800/D900 300 fixed_660_gold
660/W800/D900 300 per_wavelength_gold
```

## Gate 1 Recheck

Dry-mapping report:

```text
tmp/nodi_comsol_pre_jrc_dry_mapping_prs_route_view_expansion_20260618/NODI_COMSOL_PRE_JRC_DRY_MAPPING_REPORT_20260618.json
```

Result:

```text
status: PASS_PRE_JRC_DRY_MAPPING_WITH_BLOCKED_REGISTER_NO_OUTPUT_JRC
report_sha256: 8a20fe8e01e30f6e0888cbfd180afc58f8a6f7201887294f17539f8bf052f5dc
coverage rows: 8
dry mapping rows: 64
missing-register rows: 12
blocked_route_view_coverage_count: 0
blocked_future_field_count: 12
```

Coverage status after expansion:

```text
dry_map_keys_available: 8
dry_map_keys_incomplete: 0
```

Missing-field status after expansion:

```text
BLOCKED_MISSING_PRS_FOR_ROUTE_VIEW: 0
BLOCKED_NOT_AUTHORIZED: 12
```

The remaining blocked register entries are future authorization fields only:

```text
joint_route_class_id
q_ch_weight
transported_position_distribution
q_ch_eta_weighted_response
yield
winner
detection_probability
true_W_eff
measured_geometry
optical_solver_output
fabrication_release
P3_solver_conclusion
```

## Verification

Validators:

```bash
python tools/audits/validate_nodi_position_response_surface.py \
  tmp/nodi_next_artifacts_production_generation_prs_route_view_expansion_20260618/NODI_POSITION_RESPONSE_SURFACE.csv \
  --require-complete-row-arithmetic

python tools/audits/validate_nodi_effective_aperture_surrogate_sensitivity.py \
  tmp/nodi_next_artifacts_production_generation_prs_route_view_expansion_20260618/NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY.csv
```

Results:

```text
NODI_POSITION_RESPONSE_SURFACE: PASS
NODI_EFFECTIVE_APERTURE_SURROGATE_SENSITIVITY: PASS
```

Tests and static checks:

```bash
python -m pytest \
  tests/test_nodi_comsol_next_artifacts_contracts.py::test_prs_edge_primary_candidate_merge_blocks_duplicate_rows \
  tests/test_nodi_comsol_pre_jrc_dry_mapping.py -q

python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py -q

python -m py_compile \
  tools/audits/merge_nodi_position_response_edge_primary_candidates.py \
  tools/audits/build_nodi_comsol_pre_jrc_dry_mapping.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py \
  tests/test_nodi_comsol_pre_jrc_dry_mapping.py
ruff check \
  tools/audits/merge_nodi_position_response_edge_primary_candidates.py \
  tests/test_nodi_comsol_next_artifacts_contracts.py \
  tools/audits/build_nodi_comsol_pre_jrc_dry_mapping.py \
  tools/audits/validate_nodi_position_response_surface.py
```

Results:

```text
focused dry-mapping + merge tests: 5 passed
tests/test_nodi_comsol_next_artifacts_contracts.py: 142 passed
py_compile: pass
ruff: All checks passed
```

## Boundary

This report does not authorize:

- COMSOL execution
- NODI full-grid rerun outside the explicit PRS source accumulation sidecars
- `JOINT_ROUTE_CLASS` generation
- q_ch weighting or q_ch*eta
- yield, winner, or detection-probability claims
- true `W_eff`
- measured geometry
- optical solver output
- fabrication release
- P3 solver conclusions

The correct next gate is still a separate authorization decision for future
joint/transport/JRC work. Report 197 only removes the Report 196 PRS route/view
coverage blocker.
