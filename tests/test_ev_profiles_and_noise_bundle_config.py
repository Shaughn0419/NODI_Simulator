from __future__ import annotations

import json

import pytest

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_ev_sample_profiles_include_required_profiles_and_unknown_medium_risk() -> None:
    payload = json.loads(
        root_path("configs/realism_v2/ev_sample_profiles.yaml").read_text(encoding="utf-8")
    )
    profiles = payload["profiles"]

    assert {"unknown", "IEX_MSC_EV", "UF_MSC_EV", "PEG_like", "SEC_like"}.issubset(profiles)
    assert profiles["unknown"]["min_risk_label"] == "medium"
    assert all(profile["biological_specificity_claim_allowed"] is False for profile in profiles.values())


def test_noise_bundle_config_extends_r5_by_reference_without_forking_ids() -> None:
    payload = json.loads(
        root_path("configs/realism_v2/noise_readout_scenario_bundle.yaml").read_text(
            encoding="utf-8"
        )
    )
    r5 = json.loads(
        root_path("configs/realism_v2/r5_scenario_bundle_manifest.yaml").read_text(
            encoding="utf-8"
        )
    )
    r5_ids = [row["scenario_id"] for row in r5["scenario_bundles"]]

    assert payload["extends_scenario_bundle_id"] == "R5_scenario_bundle_manifest_v1"
    assert payload["source_scenario_manifest_path"] == "configs/realism_v2/r5_scenario_bundle_manifest.yaml"
    assert payload["required_scenario_ids"] == r5_ids
    assert payload["scenario_alias_map"] == {}
    assert payload["forked_scenario_ids_allowed"] is False
