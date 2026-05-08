# EV/NODI Realism v2 Physics Spec

> Current status: core v2 physics-boundary contract. It describes allowed module and claim semantics; it does not imply measured data are present or that calibrated claims are unlocked.

## Module States

`off`, `surrogate`, `bounded_prior`, `measured_prior`, `calibrated`, `blocked`.

## Claim Levels

`relative_proxy`, `relative_with_priors`, `scenario_count_rate`,
`safety_sidecar`, `diagnostic_only`, `absolute_blocked`,
`calibrated_absolute`.

No R0/P0 output may use `calibrated_absolute` unless both measured detector
transfer and measured blank artifacts are present and referenced by the
calibration artifact registry.

## Mie-to-Power

Probe power is converted to local irradiance before scattering integration:

```text
I_inc(r,t,lambda) = P_probe(lambda,t) * p_beam(r,t,lambda)
integral_A p_beam dA = 1
P_sca_ROI = integral_ROI(I_inc * dCsca_dOmega * T_coll dOmega)
```

`P_sca_ROI` has units of watts. `dCsca_dOmega` has units of `m^2/sr`, and the
solid-angle integral yields `m^2`; multiplying by `W/m^2` yields `W`.

## BFP / Slit / Pinhole ROI Operator

The ROI operator integrates the intensity perturbation and signed interference:

```text
integral_ROI((|E_ref + E_sca|^2 - |E_ref|^2) W du dv)
P_cross_ROI_W = integral_ROI(2 Re(conj(E_ref) E_sca) W J du dv)
```

For direction-cosine coordinates, the Jacobian is:

```text
dOmega = du dv / sqrt(1 - u^2 - v^2)
```

For physical BFP coordinates:

```text
u = x_BFP / (f_obj * n_medium)
v = y_BFP / (f_obj * n_medium)
u^2 + v^2 < 1
u^2 + v^2 <= (NA / n_medium)^2
```

The same operator is applied to reference and scattering fields.

## Detector / Lock-In Chain

ET2030 BNC biased output is path-dependent. It is not a bare photodiode current
terminal. The state machine blocks:

```text
ET2030_BNC_biased_output + LI5640 current input direct
```

unless a bench validation artifact exists in the calibration registry.

Noise PSD units:

- Shot noise: `A^2/Hz`
- Johnson voltage noise: `V^2/Hz`
- Johnson equivalent current noise: `A^2/Hz`
- RIN PSD: `1/Hz`

PSD and ENBW conventions must be explicit.

## Blank Rare Tail

Micro-anchor blank safety uses analytic or semi-analytic tails. It must not infer
high-sigma safety from short finite Monte Carlo traces with zero false events.

Trace hierarchy:

1. detector off
2. laser off, detector on
3. laser on, no channel or blocked
4. blank channel buffer
5. blank matrix
6. particle standard

## 404 Thermal Sidecar

The 404 thermal/POD-like sidecar separates particle, contaminant, medium, glass,
and filter leakage absorbed power. It is a gate only and never increases NODI
optical score.
