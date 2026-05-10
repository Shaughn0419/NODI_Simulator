from __future__ import annotations

from pathlib import Path

import pytest

from nodi_simulator.review_package import generate_paper_provenance

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def _snapshot(root: Path) -> dict[str, bytes]:
    provenance = root / "papers/provenance"
    return {path.name: path.read_bytes() for path in sorted(provenance.iterdir()) if path.is_file()}


def test_paper_provenance_generator_is_deterministic_on_synthetic_project(tmp_path: Path) -> None:
    papers = tmp_path / "papers"
    papers.mkdir()
    (papers / "Example Paper.pdf").write_bytes(b"example pdf bytes")
    (papers / "Example Supplement.docx").write_bytes(b"example docx bytes")

    generate_paper_provenance(tmp_path)
    first = _snapshot(tmp_path)
    generate_paper_provenance(tmp_path)
    second = _snapshot(tmp_path)

    assert first == second
    assert "paper_manifest.csv" in first
    assert "paper_hashes.sha256" in first


def test_current_paper_provenance_has_expected_files() -> None:
    expected = {
        "paper_manifest.csv",
        "paper_manifest_overrides.yaml",
        "paper_hashes.sha256",
        "paper_bibliography.bib",
        "paper_provenance_notes.md",
        "unavailable_or_not_packaged_papers.csv",
    }
    actual = {path.name for path in (root_path("papers/provenance")).iterdir() if path.is_file()}

    assert expected.issubset(actual)
