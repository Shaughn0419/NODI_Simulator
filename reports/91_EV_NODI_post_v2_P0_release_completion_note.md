# EV/NODI post-v2 P0 release completion note

Date: 2026-05-10

## Status

P0 is closed as an independent review-ready relative-audit milestone. The
release package contains the P0a reproducibility/provenance scaffold and the
P0b mandatory route-audit artifacts. The package remains a no-measured-data
relative audit, not a calibrated physical prediction.

## Evidence

- `REVIEW_PACKAGE_MANIFEST.json` declares `package_role =
  external_review_relative_audit`, `release_readiness =
  p0_p0b_review_ready_relative_audit`, `calibrated_claim_allowed = false`, and
  zero deferred P0b roles.
- `REVIEW_PACKAGE_HASHES.sha256` is the canonical no-cycle hash manifest; it
  excludes itself and `REVIEW_PACKAGE_MANIFEST.json`.
- `papers/provenance/` is generated from manual or verified-source metadata
  only, with packaged and unavailable/not-packaged lists kept disjoint.
- `results/post_v2_mandatory_audit/` contains the candidate universe, BFP ROI
  audit, Tsuyama audit, noise/readout audit, EV/sample audit, final route
  decision table, and P0 pairwise adjudication artifacts.
- `exports/ev_nodi_post_v2_review_package_20260510_p0b_review_package.zip`
  was generated without `__MACOSX/` or resource-fork entries.

## Verification

- `python tools/verify_review_package.py --package-root . --mode local-dev`
  passed all package gates.
- `python -m pytest -q -m "review_package_required and not
  requires_measured_data and not requires_fullwave and not
  requires_fullgrid_recompute"` passed the P0/P1/P2 review-package lane.
- `python tests/run_tests.py --workers 7` passed the full regression suite.

## Boundary

P1 physical-ceiling extensions are intentionally not part of this P0 release
line. A later `physical-ceiling extensions` branch or task may split full-wave,
vector/Jones, roughness/leakage, and transport work into separate tracks, but
that work does not change the P0 release conclusion.
