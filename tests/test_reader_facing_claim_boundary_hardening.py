from __future__ import annotations

import csv
from pathlib import Path

from ._review_package_test_helpers import root_path


def _csv_header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        return next(csv.reader(handle))


def test_reader_facing_mechanism_csv_does_not_expose_bare_cross_term_column() -> None:
    checked = 0
    for path in root_path("reports/current").glob("**/*.csv"):
        if path.name.startswith("._"):
            continue
        checked += 1
        header = _csv_header(path)
        assert "median_cross_term_detector_integrated" not in header, path
    assert checked > 0


def test_report47_mechanism_csv_exposes_signed_cross_term_diagnostics() -> None:
    path = root_path(
        "reports/current/47_ev_design_full_grid_analysis/"
        "mechanism_chain_by_wavelength_EV_medians.csv"
    )
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))

    assert rows
    assert "median_cross_term_detector_integrated_magnitude_deprecated" in rows[0]
    assert "median_signed_cross_term_detector_integrated" in rows[0]
    assert "median_abs_cross_term_detector_integrated" in rows[0]
    assert "cross_term_negative_fraction" in rows[0]
    assert "phase_convention" in rows[0]

    by_wavelength = {int(row["wavelength_nm"]): row for row in rows}
    assert float(by_wavelength[404]["median_cross_term_detector_integrated_magnitude_deprecated"]) > 0
    assert float(by_wavelength[404]["median_signed_cross_term_detector_integrated"]) < 0
    assert float(by_wavelength[404]["cross_term_negative_fraction"]) == 1.0
    assert by_wavelength[404]["phase_convention"] == "current_uncalibrated"
