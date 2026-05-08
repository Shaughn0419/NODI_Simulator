# `photothermal_pod.py`

Thermal POD provenance helper.

## 主要符号
- 顶层函数：`build_photothermal_pod_diagnostics`

## 说明

This module intentionally does not implement the photothermal PDE. It records
the missing pieces that block quantitative POD sign or amplitude:

- separated probe/excitation wavelength bookkeeping
- absorption cross-section at the excitation wavelength
- thermal source and heat diffusion through liquid/substrate
- solvent `dn/dT`
- ROI-integrated `dI/dtheta` or recomputed thermal phase-filter field
- detector/filter responsivity at the probe wavelength

Until those pieces exist, the POD lane remains a frequency-separated paired
diagnostic rather than an absolute photothermal-amplitude model.

Current outputs also expose flat provenance fields for the route status:
`pod_quantitative_route_status`, `pod_probe_reference_field_status`,
`pod_heat_source_status`, wavelength-specific `dn/dT`, detector responsivity,
spectral-filter status, and `pod_thermal_validation_status`. These are blockers,
not hidden defaults; they prevent a configured POD lane from being interpreted
as calibrated thermal-POD amplitude.
