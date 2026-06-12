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


def test_external_bundle_mode_preserves_existing_paper_manifest_without_sources(tmp_path: Path) -> None:
    provenance = tmp_path / "papers/provenance"
    provenance.mkdir(parents=True)
    manifest = provenance / "paper_manifest.csv"
    original = (
        "paper_id,title,authors,year,doi,local_path,sha256,included_in_package,"
        "license_or_access_note,used_for_claim_area,metadata_source\n"
        "paper_a,Example,A. Author,2024,10.000/example,papers/example.pdf,"
        "abc123,true,local_reference_copy_not_relicensed,,manual_override\n"
    )
    manifest.write_text(original, encoding="utf-8")
    (provenance / "paper_manifest_overrides.yaml").write_text(
        '{"schema":"ev_nodi_paper_manifest_overrides_v1","papers":{}}\n',
        encoding="utf-8",
    )

    paths = generate_paper_provenance(tmp_path, external_bundle_mode=True)

    assert manifest in paths
    assert manifest.read_text(encoding="utf-8") == original
