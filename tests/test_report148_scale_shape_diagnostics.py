from __future__ import annotations

from tools.audits.analyze_report148_scale_shape_diagnostics import (
    evaluate_norm_repin_cases,
)


def test_norm_repin_diagnostic_reports_tiny_v1_v2_amplitude_deltas() -> None:
    rows = evaluate_norm_repin_cases()

    assert len(rows) == 3
    assert all(row["sca_abs_delta"] < 1e-4 for row in rows)
    assert all(row["ref_abs_delta"] < 1e-12 for row in rows)
    assert all(row["n_ref_raw"] > 0.0 for row in rows)
    assert all(row["n_sca_raw"] > 0.0 for row in rows)
