# Report 196 - NODI/COMSOL Gate 1 Pre-JRC Dry Mapping

Date: 2026-06-18

## Disposition

`PASS_PRE_JRC_DRY_MAPPING_WITH_BLOCKED_REGISTER_NO_OUTPUT_JRC`

This report records Gate 1 of the NODI/COMSOL linkage plan. Gate 1 is a
pre-`JOINT_ROUTE_CLASS` dry mapping only. It maps current PRS/EAS/descriptor keys,
identifies missing route/view coverage, and writes a missing-field register.

Gate 1 did not:

- run COMSOL
- rerun NODI
- generate `JOINT_ROUTE_CLASS`
- perform q_ch weighting or q_ch*eta
- compute yield
- choose a winner
- compute detection probability
- claim true W_eff
- claim measured geometry
- claim optical solver output
- claim fabrication release
- claim P3 solver conclusions

## Implemented Gate 1 CLI

New CLI:

```text
tools/audits/build_nodi_comsol_pre_jrc_dry_mapping.py
```

The CLI writes sidecars only when called with:

```text
--confirm-dry-mapping-report
```

This confirmation authorizes only dry mapping sidecar writing. It does not
authorize any joint output or weighted result.

## Execution

Command:

```bash
python tools/audits/build_nodi_comsol_pre_jrc_dry_mapping.py \
  --confirm-dry-mapping-report \
  --output-dir tmp/nodi_comsol_pre_jrc_dry_mapping_20260618
```

Result:

```text
NODI_COMSOL_PRE_JRC_DRY_MAPPING: PASS_PRE_JRC_DRY_MAPPING_WITH_BLOCKED_REGISTER_NO_OUTPUT_JRC
```

Output artifacts:

```text
tmp/nodi_comsol_pre_jrc_dry_mapping_20260618/NODI_COMSOL_PRE_JRC_DRY_MAPPING_REPORT_20260618.json
tmp/nodi_comsol_pre_jrc_dry_mapping_20260618/NODI_COMSOL_PRE_JRC_DRY_MAPPING_REPORT_20260618.md
tmp/nodi_comsol_pre_jrc_dry_mapping_20260618/NODI_COMSOL_PRE_JRC_DRY_MAPPING_ROUTE_VIEW_COVERAGE_20260618.csv
tmp/nodi_comsol_pre_jrc_dry_mapping_20260618/NODI_COMSOL_PRE_JRC_DRY_MAPPING_ROWS_20260618.csv
tmp/nodi_comsol_pre_jrc_dry_mapping_20260618/NODI_COMSOL_PRE_JRC_MISSING_FIELD_REGISTER_20260618.csv
```

Output hashes:

```text
report json:      05879ab706e95e9b97dabb5279e468f76350468eb566771403045d5b4d1a2d38
report md:        7ce93a9f15ab43d832fb5032e425d869ab599351c7fd44b7fd7a573d13f6ef3f
coverage csv:     e1207f430719dab6b44271ed6eca08ba7def20b50889494a07e604600108c847
dry mapping csv:  8ab92c9316ec3c310b832e9d420727d78aa4d06dea61305523b52647ea900861
missing register: b2e1725b8044b8d5d6ce72015044f6886f6e6739b1963708129a92022ca9ba8d
```

## Gate 1 Result

Counts:

```text
coverage rows: 8
dry mapping rows: 16
missing-register rows: 18
issues: none
```

Coverage status:

```text
dry_map_keys_available: 2
dry_map_keys_incomplete: 6
```

Missing-field status:

```text
BLOCKED_MISSING_PRS_FOR_ROUTE_VIEW: 6
BLOCKED_NOT_AUTHORIZED: 12
```

## Interpretation

Gate 1 found that the currently dry-mappable route/view keys are:

```text
404/W500/D900 fixed_660_gold
404/W500/D900 per_wavelength_gold
```

For those keys, PRS rows, EAS rows, and nominal smooth 85 degree descriptor keys
are present. The dry mapping expands these into 16 key rows:

```text
2 views x 2 PRS diameters x 4 EAS surrogate modes = 16 dry mapping rows
```

The following EAS/descriptor route/view keys are not dry-mappable yet because
current production PRS rows are absent:

```text
404/W500/D1200 fixed_660_gold
404/W500/D1200 per_wavelength_gold
660/W800/D900 fixed_660_gold
660/W800/D900 per_wavelength_gold
660/W800/D1200 fixed_660_gold
660/W800/D1200 per_wavelength_gold
```

These are explicitly recorded as:

```text
BLOCKED_MISSING_PRS_FOR_ROUTE_VIEW
```

This is not a failure of Gate 1, but it is also not full route/view readiness.
It is the intended missing-field register for future scoping: downstream work
must either authorize future PRS expansion or explicitly accept a reduced-scope
dry mapping before any JRC-related step.

The machine-readable report therefore uses a PASS status that includes blocked
register semantics:

```text
PASS_PRE_JRC_DRY_MAPPING_WITH_BLOCKED_REGISTER_NO_OUTPUT_JRC
has_blocked_route_view_coverage = true
blocked_route_view_coverage_count = 6
has_blocked_future_fields = true
blocked_future_field_count = 12
```

## Future Fields Still Blocked

The missing-field register keeps these future fields blocked:

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

All dry mapping rows keep:

```text
future_joint_route_class_id = blank
future_joint_route_class_status = BLOCKED_NOT_GENERATED_GATE1
q_ch_weight = blank
q_ch_weight_status = BLOCKED_MISSING_GATE2_COMSOL_SIDE_QCH
transported_position_distribution = blank
transported_position_distribution_status = BLOCKED_MISSING_GATE2_COMSOL_TRANSPORT
weighted_response = blank
yield = blank
winner = blank
detection_probability = blank
```

## Verification

Focused tests:

```bash
python -m pytest tests/test_nodi_comsol_pre_jrc_dry_mapping.py -q
```

Result:

```text
4 passed
```

Static checks:

```bash
python -m py_compile tools/audits/build_nodi_comsol_pre_jrc_dry_mapping.py
python -m ruff check tools/audits/build_nodi_comsol_pre_jrc_dry_mapping.py \
  tests/test_nodi_comsol_pre_jrc_dry_mapping.py
```

Results:

```text
py_compile: pass
ruff: All checks passed
```

## Next Mainline Step

The next efficient step is not JRC generation. It is a Gate 1 review and then a
choice between two bounded routes:

1. `reduced_scope_pre_jrc_package`:
   keep only the two dry-mappable `404/W500/D900` route/view keys and prepare a
   reduced-scope consumer package with every missing field still blocked.
2. `Gate 2 planning`:
   define the exact future authorization needed for COMSOL transport/q_ch sidecar
   collection and/or PRS expansion for the six missing route/view keys.

Neither route authorizes COMSOL execution, JRC regeneration, q_ch weighting,
yield, winner, or detection probability without a separate future gate.
