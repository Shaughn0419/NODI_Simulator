from __future__ import annotations

import pytest

from nodi_simulator.review_package import v1_hash_drift_is_authorized

from ._review_package_test_helpers import load_json


pytestmark = pytest.mark.review_package_required


def test_current_v1_hash_matches_pinned_release_hash() -> None:
    manifest = load_json("REVIEW_PACKAGE_MANIFEST.json")
    v1_group = next(
        group for group in manifest["artifact_groups"] if group["group"] == "v1_key_result_artifacts"
    )
    contract = v1_group["contract"]

    assert contract["summary_csv_hash_matches_pin"] is True
    assert v1_hash_drift_is_authorized(contract)


def test_v1_hash_drift_without_evidence_blocks_release() -> None:
    assert not v1_hash_drift_is_authorized(
        {
            "summary_csv_hash_matches_pin": False,
            "approved_v1_summary_drift_evidence_path": None,
        }
    )
    assert v1_hash_drift_is_authorized(
        {
            "summary_csv_hash_matches_pin": False,
            "approved_v1_summary_drift_evidence_path": "reports/v1_hash_drift.md",
        }
    )
