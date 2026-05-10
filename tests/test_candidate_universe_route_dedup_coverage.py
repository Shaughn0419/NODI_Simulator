from __future__ import annotations

import json

import pytest

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def _manifest() -> dict:
    return json.loads(
        root_path("results/post_v2_mandatory_audit/candidate_universe_manifest.json").read_text(
            encoding="utf-8"
        )
    )


def test_candidate_universe_uses_unique_route_dedup_key_and_covers_v1_routes() -> None:
    manifest = _manifest()

    assert manifest["candidate_universe_route_dedup_key"] == "wavelength_nm,width_nm,depth_nm"
    assert manifest["candidate_universe_case_rows"] == 32032
    assert manifest["candidate_universe_unique_routes"] == 572
    assert len(manifest["route_aggregates"]) == manifest["candidate_universe_unique_routes"]
    assert set(manifest["candidate_universe_coverage_by_wavelength"]) == {
        "404",
        "488",
        "532",
        "660",
    }
    assert manifest["candidate_universe_min_case_rows"] >= 200
    assert manifest["candidate_universe_min_unique_routes"] == 572


def test_static_mandatory_routes_and_optional_probe_governance_are_present() -> None:
    manifest = _manifest()
    static_ids = {row["candidate_id"] for row in manifest["static_mandatory_candidates"]}

    assert manifest["mandatory_static_routes_missing_count"] == 0
    assert "optional_660_W900_D1400" in static_ids
    assert manifest["optional_660_W900_D1400_present"] is True
    assert manifest["optional_660_W900_D1400_never_redefines_main_660"] is True
