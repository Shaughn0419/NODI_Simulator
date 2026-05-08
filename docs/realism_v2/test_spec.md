# EV/NODI Realism v2 Test Spec

> Current status: historical R0/P0 test contract plus still-active claim-boundary expectations. Later v2 stages add more tests, but the constraints here remain valid.

Focused tests live in `tests/test_realism_v2_*.py`.

## R0 Contract Tests

- v1 route key compatibility no-op.
- claim level enum validation.
- module state enum validation.
- route key schema and scenario identity separation.
- run manifest required fields and checksum fields.
- calibration artifact registry schema.
- detector connection state machine.
- ET2030 BNC direct current-input path forbidden unless bench validated.
- legacy `detector_SNR` and `calibrated_detector_SNR` output names rejected.

## P0 Sidecar Tests

- Mie-to-power yields watts and not `W*m^2`.
- `P_sca_ROI <= I_inc * Csca`.
- `P_sca_total + P_abs <= P_ext` within tolerance.
- radius vs diameter and vacuum vs medium wavelength are separated.
- BFP Jacobian and physical-BFP-to-uv mapping are applied.
- Valid uv domain and NA clipping are enforced.
- Signed and absolute NODI peak power are both exported.
- Detector path does not silently fall back.
- LI5640/LI5660/LI5650 specs cannot be mixed.
- Shot, Johnson, RIN, PSD, and ENBW units/conventions are explicit.
- `scenario_detector_SNR` is exported only with `SNR_claim_level`.
- No calibrated absolute SNR without measured artifacts.
- Blank rare tail includes analytic/semi-analytic estimates and zero-event upper bound.
- 404 thermal sidecar cannot increase optical score.

## Micro-Anchor Tests

- Required result files exist.
- Optical-power outputs carry watt units.
- Invalid ET2030 current-input path is blocked.
- `scenario_detector_SNR` is not `calibrated_absolute`.
- Blank FP/min is not inferred from finite Monte Carlo zero events.
- Manifest declares that R2/R3/R5 were not run.
