from __future__ import annotations

from pathlib import Path
import zipfile

import pytest

from nodi_simulator.review_package import export_review_package

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_exported_review_package_zip_has_required_p0a_contents(tmp_path: Path) -> None:
    zip_path = export_review_package(root_path("."), output_path=tmp_path / "review.zip")

    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())

    assert "REVIEW_PACKAGE_MANIFEST.json" in names
    assert "REVIEW_PACKAGE_HASHES.sha256" in names
    assert "configs/realism_v2/r5_scenario_bundle_manifest.yaml" in names
    assert "configs/realism_v2/forbidden_claims_lexicon.yaml" in names
    assert "calibration/bfp_roi_mask_template.json" in names
    assert "papers/provenance/paper_manifest.csv" in names
    assert (
        "results/post_v2_mandatory_audit/top_candidate_mandatory_audit_manifest.json"
        in names
    )
    assert "results/post_v2_mandatory_audit/top_candidate_mandatory_audit.csv" in names
    assert "results/post_v2_mandatory_audit/top_candidate_pairwise_rank_inversion.csv" in names
    assert not any(name.startswith("__MACOSX/") or "/._" in name or name.startswith("._") for name in names)
    assert "REVIEW_BUILD_MANIFEST.json" not in names
