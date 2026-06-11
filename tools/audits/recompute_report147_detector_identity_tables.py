#!/usr/bin/env python3
"""Reproduce the quantitative tables in reports/147 (detector-forward identity audit).

This script is the concrete reproduction path requested in the report 147 review.
It does NOT depend on the external review bundle; it requires the full local
result artifacts (the 1.6 GB v1 summary and the Lens-B diagnostic_rows), which
are tracked locally but intentionally omitted from the cropped external bundle.

Outputs (printed + optional CSV):
  - detector-route disagreement distribution (band / gate / roi_vs_scalar)
  - EV self / signed-cross / abs-cross by wavelength  (signed-cross is NEGATIVE;
    the packaged mechanism_chain table reports the MAGNITUDE, which is the source
    of the sign confusion flagged in the review)
  - EV net |signal|/self distribution by wavelength
  - eligibility-flag fractions (relative vs detector_resolved)

Usage:
  python tools/audits/recompute_report147_detector_identity_tables.py \
      --v1-summary results/ev_design_full_range_biomimetic_exosome_with_anchors_10000e_summary.csv \
      --lensb-diagnostic results/exhaustive_ev_gold_fullgrid_shared_dual_10000e_seed11_16worker_20260518/seed_11_fixed_660_gold_diagnostic_rows.csv
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import statistics as st
from collections import Counter, defaultdict
from pathlib import Path


def _sha256(path: Path, limit_bytes: int | None = None) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        read = 0
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
            read += len(chunk)
            if limit_bytes is not None and read >= limit_bytes:
                break
    return h.hexdigest()


def _is_ev(family: str) -> bool:
    f = family.lower()
    return "gold" not in f and any(
        k in f for k in ("exo", "membrane", "msc", "biomim", "sev", "vesicle", "ev")
    )


def _ffloat(value: str) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x


def scan_summary(path: Path) -> None:
    print(f"\n=== {path.name} (sha256[:16]={_sha256(path, 1<<24)[:16]}, head-hashed) ===")
    with path.open(newline="") as fh:
        reader = csv.reader(fh)
        header = next(reader)
        idx = {c: i for i, c in enumerate(header)}

        band = Counter()
        gate = Counter()
        roi: list[float] = []
        elig = {
            k: Counter()
            for k in (
                "relative_design_eligible",
                "detector_resolved_relative_design_eligible",
                "absolute_global_green_eligible",
                "final_green_eligible",
            )
            if k in idx
        }
        ev = defaultdict(
            lambda: {"self": [], "cross_signed": [], "neg": 0, "pos": 0, "zero": 0, "absrat": []}
        )
        gold_absrat = defaultdict(list)
        wl_col = "wavelength_nm" if "wavelength_nm" in idx else "wavelength_m"
        nrows = 0

        for row in reader:
            nrows += 1
            if "detector_operator_disagreement_band" in idx:
                band[row[idx["detector_operator_disagreement_band"]]] += 1
            if "detector_operator_gate_passed" in idx:
                gate[row[idx["detector_operator_gate_passed"]]] += 1
            r = _ffloat(row[idx["roi_vs_scalar_signal_ratio"]]) if "roi_vs_scalar_signal_ratio" in idx else None
            if r is not None:
                roi.append(r)
            for k, ctr in elig.items():
                ctr[row[idx[k]]] += 1
            if "particle_family" not in idx:
                continue
            s = _ffloat(row[idx["self_sca_detector_integrated"]]) if "self_sca_detector_integrated" in idx else None
            c = _ffloat(row[idx["cross_term_detector_integrated"]]) if "cross_term_detector_integrated" in idx else None
            sig = _ffloat(row[idx["signal_detector_integrated"]]) if "signal_detector_integrated" in idx else None
            wl = _ffloat(row[idx[wl_col]])
            if wl is None:
                continue
            nm = round(wl * 1e9) if wl_col == "wavelength_m" else round(wl)
            fam = row[idx["particle_family"]]
            if _is_ev(fam):
                a = ev[nm]
                if c is not None:
                    a["cross_signed"].append(c)
                    a["neg"] += int(c < 0)
                    a["pos"] += int(c > 0)
                    a["zero"] += int(c == 0)
                    if s not in (None, 0):
                        a["absrat"].append(abs(c) / abs(s))
                if s is not None:
                    a["self"].append(s)
                if s not in (None, 0) and sig is not None:
                    a.setdefault("netrat", []).append(abs(sig) / abs(s))
            elif "gold" in fam.lower() and s not in (None, 0) and c is not None:
                gold_absrat[nm].append(abs(c) / abs(s))

    print(f"rows={nrows}")
    if band:
        print("disagreement_band:", dict(band))
    if gate:
        print("detector_operator_gate_passed:", dict(gate))
    if roi:
        rs = sorted(roi)
        print(f"roi_vs_scalar_signal_ratio: median={rs[len(rs)//2]:.3f} p10={rs[len(rs)//10]:.3f} p90={rs[9*len(rs)//10]:.3f}")
    for k, ctr in elig.items():
        print(f"{k}: {dict(ctr)}")
    if ev:
        print("\nEV self / SIGNED cross / |cross| by wavelength (signed cross is NEGATIVE under the current uncalibrated reference-phase convention; not a calibrated destructive-interference claim):")
        for nm in sorted(ev):
            a = ev[nm]
            ms = st.median(a["self"]) if a["self"] else float("nan")
            mc = st.median(a["cross_signed"]) if a["cross_signed"] else float("nan")
            mr = st.median(a["absrat"]) if a["absrat"] else float("nan")
            net = sorted(a.get("netrat", []))
            netmed = net[len(net)//2] if net else float("nan")
            netp10 = net[len(net)//10] if net else float("nan")
            netp90 = net[9*len(net)//10] if net else float("nan")
            print(
                f"  {nm}nm self={ms:.3f} cross_signed_median={mc:.3f} "
                f"med|cross|/self={mr:.3f} cross<0={a['neg']} >0={a['pos']} =0={a['zero']} "
                f"| net|signal|/self med={netmed:.3f} p10={netp10:.3f} p90={netp90:.3f}"
            )
    if gold_absrat:
        print("\ngold |cross|/self by wavelength:")
        for nm in sorted(gold_absrat):
            v = sorted(gold_absrat[nm])
            print(f"  {nm}nm median={v[len(v)//2]:.4f}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--v1-summary", type=Path, default=None)
    ap.add_argument("--lensb-diagnostic", type=Path, nargs="*", default=[])
    args = ap.parse_args()

    if args.v1_summary and args.v1_summary.exists():
        scan_summary(args.v1_summary)
    for p in args.lensb_diagnostic:
        if Path(p).exists():
            scan_summary(Path(p))


if __name__ == "__main__":
    main()
