# COMSOL Gate2B Formal q_ch / Flow-Split Sidecar Requirements - 2026-06-27

This document is a requirements contract only. It does not generate a formal q_ch sidecar, does not authorize q_ch weighting, and does not create q_ch*eta, q_ch*chi*eta, JRC, route_score, yield, winner, detection_probability, time-to-clog, recovery, calibrated clogging, or fabrication release outputs.

## Current Decision

`roadmap/COMSOL_GATE2A_QCH_PROVENANCE_ONLY_EXPORT_20260627.csv` remains `PROVENANCE_ONLY_NOT_GATE2_QCH_SIDECAR`. It is useful as descriptive provenance/review context, but it is not a formal NODI Gate2 q_ch or flow-split sidecar.

## Missing Pieces Before a Formal Sidecar

A future formal sidecar must provide route_key/route_family binding, NODI_view policy or explicit UNBOUND status, diameter grain, optional bin basis, q_ch value, flow_split value, units, normalization basis, solve/provenance id, source geometry hash, integration surface or volume definition, uncertainty/review flag when available, and a validation contract. `qch_weighting_authorized` must default to false until NODI opens a dedicated gate.

The machine-readable requirement table is `roadmap/COMSOL_GATE2B_QCH_FORMAL_SIDECAR_REQUIREMENTS_20260627.csv`.
