from __future__ import annotations

import json
from pathlib import Path

import pytest

from nodi_simulator.review_package import generate_paper_provenance, paper_id_for_path

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_claim_bearing_paper_metadata_requires_manual_or_verified_source(tmp_path: Path) -> None:
    papers = tmp_path / "papers"
    provenance = papers / "provenance"
    provenance.mkdir(parents=True)
    paper_path = papers / "Claim Paper.pdf"
    paper_path.write_bytes(b"claim-bearing bytes")
    paper_id = paper_id_for_path("papers/Claim Paper.pdf")
    overrides = {
        "schema": "ev_nodi_paper_manifest_overrides_v1",
        "papers": {
            paper_id: {
                "title": "Claim Paper",
                "authors": "A. Author",
                "year": "2026",
                "doi": "10.0000/example",
                "used_for_claim_area": "paper_sanity_only",
                "metadata_source": "filename_guess",
            }
        },
        "unavailable_or_not_packaged_papers": [],
    }
    (provenance / "paper_manifest_overrides.yaml").write_text(
        json.dumps(overrides, sort_keys=True),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="manual_override or verified_source"):
        generate_paper_provenance(tmp_path)

    overrides["papers"][paper_id]["metadata_source"] = "manual_override"
    (provenance / "paper_manifest_overrides.yaml").write_text(
        json.dumps(overrides, sort_keys=True),
        encoding="utf-8",
    )
    generate_paper_provenance(tmp_path)


def test_current_paper_manifest_does_not_guess_claim_bearing_metadata() -> None:
    text = root_path("papers/provenance/paper_manifest.csv").read_text(encoding="utf-8")

    assert "filename_guess" not in text
