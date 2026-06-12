from __future__ import annotations

from pathlib import Path
import subprocess
import sys
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
    assert "REVIEW_BUILD_MANIFEST.json" in names
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
    assert (
        "results/post_v2_mandatory_audit/top_candidate_extended_pairwise_stability.csv"
        in names
    )
    assert not any(name.startswith(("__MACOSX/", "._")) or "/._" in name for name in names)


def test_exported_review_package_replays_in_external_bundle_mode(tmp_path: Path) -> None:
    zip_path = export_review_package(root_path("."), output_path=tmp_path / "review.zip")
    unpacked = tmp_path / "unpacked"
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(unpacked)

    assert not any(
        path.name.startswith("._") or "__MACOSX" in path.parts
        for path in unpacked.rglob("*")
    )

    result = subprocess.run(
        [
            sys.executable,
            str(root_path("tools/verify_review_package.py")),
            "--package-root",
            str(unpacked),
            "--mode",
            "external-review",
            "--external-bundle-mode",
            "--allow-dirty",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "PASS external_bundle_mode" in result.stdout
    assert "PASS claim_blockers" in result.stdout
