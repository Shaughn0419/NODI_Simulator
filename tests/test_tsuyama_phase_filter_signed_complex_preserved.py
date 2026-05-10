from __future__ import annotations

import cmath
import csv

import pytest

from nodi_simulator.post_v2_audit import (
    tsuyama_signed_phase_factor,
    write_tsuyama_bfp_reference_summary,
)

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def _rows() -> list[dict[str, str]]:
    path = root_path("results/post_v2_mandatory_audit/tsuyama_bfp_reference_summary.csv")
    if not path.exists():
        write_tsuyama_bfp_reference_summary(root_path("."))
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_tsuyama_signed_phase_factor_preserves_complex_sign() -> None:
    factor = tsuyama_signed_phase_factor(wavelength_nm=660, depth_nm=550)
    theta = 2.0 * cmath.pi * (1.333 - 1.45) * 550 / 660

    assert factor == pytest.approx(cmath.exp(1j * theta) - 1.0)
    assert factor.imag < 0


def test_tsuyama_summary_records_signed_complex_phase_filter_fields() -> None:
    rows = _rows()

    assert rows
    assert {row["tsuyama_signed_complex_phase_filter_preserved"] for row in rows} == {"True"}
    assert {row["tsuyama_phase_filter_unit_test_status"] for row in rows} == {"pass"}
    assert {row["tsuyama_claim_level"] for row in rows} == {
        "signed_relative_phase_filter_audit_only"
    }
    assert any(float(row["tsuyama_phase_filter_complex_factor_imag"]) < 0 for row in rows)
