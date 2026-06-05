# Pre-3seed Final-Style Dry Run Report

Generated: 2026-05-17T17:38:35+00:00

## Route/Evidence State

7 route contracts; formula ledger rows: 24.

This dry report is a no-measured-data relative/proxy design-selection artifact.
All event fractions are conditional synthetic event metrics with explicit
denominators. Selected-annulus entries are event-position window diagnostics,
not optical BFP annuli. Detector units, photon units, empirical blank safety,
sample concentration, biological exosome specificity, and calibrated
cross-wavelength superiority remain blocked.

## Formula Ledger Summary

The formula ledger covers diameter/radius, vacuum/medium wavelength, material RI
convention, Mie/core-shell, dC/dOmega to field proxy, detector/BFP Jacobian,
reference phase-filter routes, illumination, interference, trajectory,
selected-annulus event-position selection, threshold/readout, Wilson/statistics,
ranking score, and normalization policy.

## Candidate Stability Classes

- `conditional_candidate`: 5
- `diagnostic_only`: 3
- `robust_relative_candidate`: 2
- `stress_branch`: 2

## Carry-Forward Manifest

- `au_control_660_W1200_D550`: `diagnostic_only` / `conditional_or_stress_branch_not_primary`
- `historical_488_W600_D1500`: `conditional_candidate` / `conditional_or_stress_branch_not_primary`
- `historical_532_W600_D1500`: `conditional_candidate` / `conditional_or_stress_branch_not_primary`
- `less_narrow_404_W700_D1400`: `conditional_candidate` / `conditional_or_stress_branch_not_primary`
- `main_660_W800_D1400`: `robust_relative_candidate` / `primary_relative_candidate`
- `main_660_W800_D1500`: `robust_relative_candidate` / `primary_relative_candidate`
- `narrow_404_W500_D1500`: `stress_branch` / `conditional_or_stress_branch_not_primary`
- `optional_900_660_W900_D1400`: `stress_branch` / `conditional_or_stress_branch_not_primary`
- `reference_edge_660_W700_D1500`: `diagnostic_only` / `conditional_or_stress_branch_not_primary`
- `shortwave_404_W600_D1300`: `conditional_candidate` / `conditional_or_stress_branch_not_primary`
- `tsuyama_like_660_W800_D550`: `diagnostic_only` / `conditional_or_stress_branch_not_primary`
- `wide_660_W1100_D1400`: `conditional_candidate` / `conditional_or_stress_branch_not_primary`

## Candidate Demotions

- `au_control_660_W1200_D550` -> `diagnostic_only`: reference_conditional_topk_set_sensitive; geometry_or_wall_transport_high_risk
- `historical_488_W600_D1500` -> `conditional_candidate`: reference_conditional_topk_set_sensitive
- `historical_532_W600_D1500` -> `conditional_candidate`: reference_conditional_topk_set_sensitive
- `less_narrow_404_W700_D1400` -> `conditional_candidate`: reference_conditional_topk_set_sensitive
- `narrow_404_W500_D1500` -> `stress_branch`: reference_conditional_topk_set_sensitive; geometry_or_wall_transport_high_risk
- `optional_900_660_W900_D1400` -> `stress_branch`: reference_conditional_topk_set_sensitive
- `reference_edge_660_W700_D1500` -> `diagnostic_only`: reference_conditional_topk_set_sensitive
- `shortwave_404_W600_D1300` -> `conditional_candidate`: reference_conditional_topk_set_sensitive
- `tsuyama_like_660_W800_D550` -> `diagnostic_only`: reference_conditional_topk_set_sensitive; geometry_or_wall_transport_high_risk; selected-annulus event-position window diagnostic only
- `wide_660_W1100_D1400` -> `conditional_candidate`: reference_conditional_topk_set_sensitive

## Stop-Gate Status

- `SG0` `passed`: route matrix and preflight linter policy generated
- `SG1` `passed`: formula ledger generated and validated
- `SG2` `passed`: micro smoke row count, linter, denominator fields
- `SG3` `passed`: physics invariant pytest suite required; see freeze/test result hash
- `SG4` `passed`: multi-source candidate manifest generated
- `SG5` `passed`: reference stability labels complete
- `SG6` `passed`: detector/readout/threshold labels complete
- `SG7` `passed`: geometry/transport labels complete
- `SG8` `passed`: EV prior evidence table and stress matrix generated
- `SG9` `passed`: interface/full-wave/404 flags complete
- `SG10` `passed`: candidate stability matrix generated
- `SG11` `passed`: low-event 3seed rehearsal passed schema/linter/seed consistency gates
- `SG12` `passed`: freeze manifest complete structurally; freeze.dirty=true; formal --execute is currently blocked until commit and regenerated freeze
- `SG13` `passed`: dry report preflight claim scan passed

## Allowed Claims

- Relative/proxy candidate-family classification within declared lens, route,
  normalization, and surrogate assumptions.
- Conditional/stress/diagnostic preservation for scientifically informative
  branches.
- Rehearsal schema and seed reproducibility evidence.
- All-crossing and selected-annulus event-position-window analyses may be
  compared only as separate lens scopes with explicit denominators.

## Forbidden Claims

- Calibrated detector performance, absolute limit-of-detection statements,
  empirical blank control, detector voltage, photon-counting, true sample
  concentration/count rate, biological specificity, or unscoped wavelength
  winners.
- Selected-annulus results must not be described as optical BFP annulus
  superiority, and selected-window ranks must not replace all-crossing ranks
  without saying the lens changed.
