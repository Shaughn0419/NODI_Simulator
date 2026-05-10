from __future__ import annotations

import csv

import pytest

from nodi_simulator.post_v2_audit import (
    write_noise_readout_route_sensitivity,
    write_noise_readout_scenario_bundle,
)

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def _scenario_rows() -> list[dict[str, str]]:
    path = root_path("results/post_v2_mandatory_audit/noise_readout_scenario_bundle.csv")
    if not path.exists():
        write_noise_readout_scenario_bundle(root_path("."))
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _route_rows() -> list[dict[str, str]]:
    path = root_path("results/post_v2_mandatory_audit/noise_readout_route_sensitivity.csv")
    if not path.exists():
        write_noise_readout_route_sensitivity(root_path("."))
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_noise_bundle_reuses_live_r5_scenario_ids_and_provenance() -> None:
    rows = _scenario_rows()
    scenario_ids = {row["scenario_id"] for row in rows}

    assert len(rows) == 8
    assert "nominal_instrument_clean_blank" in scenario_ids
    assert {row["extends_scenario_bundle_id"] for row in rows} == {
        "R5_scenario_bundle_manifest_v1"
    }
    assert {row["source_scenario_manifest_path"] for row in rows} == {
        "configs/realism_v2/r5_scenario_bundle_manifest.yaml"
    }


def test_noise_route_sensitivity_has_at_least_five_applicable_scenarios_per_route() -> None:
    rows = _route_rows()
    by_route: dict[str, set[str]] = {}
    for row in rows:
        by_route.setdefault(row["route_key"], set()).add(row["scenario_id"])

    assert by_route
    assert min(len(scenarios) for scenarios in by_route.values()) >= 5
