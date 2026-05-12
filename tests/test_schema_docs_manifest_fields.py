from __future__ import annotations

from pathlib import Path

import pytest

from tools import verify_schema_docs_manifest_fields as audit


def _configure_audit_roots(monkeypatch: pytest.MonkeyPatch, root: Path) -> Path:
    doc_dir = root / "docs" / "schemas"
    doc_dir.mkdir(parents=True)
    monkeypatch.setattr(audit, "PROJECT_ROOT", root)
    monkeypatch.setattr(audit, "DOC_DIR", doc_dir)
    return doc_dir


def test_alias_matches_are_still_field_checked(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    doc_dir = _configure_audit_roots(monkeypatch, root)
    monkeypatch.setattr(audit, "ARTIFACT_NAME_ALIASES", {"logical_contract": ("alias_artifact",)})

    doc = doc_dir / "logical_contract_schema.md"
    doc.write_text("Documented field: `documented_field`.\n", encoding="utf-8")
    (root / "alias_artifact.json").write_text(
        '{"documented_field": true, "missing_field": true}\n',
        encoding="utf-8",
    )

    ok, checked, missing = audit._analyze_doc(
        doc,
        strict=True,
        artifact_index=audit._build_artifact_index(),
    )

    assert ok is False
    assert checked == 2
    assert missing == 1


def test_declared_multi_artifact_schema_bindings_match_doc_claims() -> None:
    assert {
        "top_candidate_mandatory_audit",
        "top_candidate_mandatory_audit_manifest",
    }.issubset(set(audit.ARTIFACT_NAME_ALIASES["post_v2_mandatory_audit"]))
    assert {
        "REVIEW_BUILD_MANIFEST",
        "REVIEW_PACKAGE_MANIFEST",
    }.issubset(set(audit.ARTIFACT_NAME_ALIASES["review_package_manifest"]))


def test_artifact_index_skips_symlinked_data_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _configure_audit_roots(monkeypatch, root)
    external = tmp_path / "external.json"
    external.write_text('{"outside_field": true}\n', encoding="utf-8")
    symlink = root / "linked_artifact.json"
    try:
        symlink.symlink_to(external)
    except OSError:
        pytest.skip("filesystem does not support symlinks")

    artifact_index = audit._build_artifact_index()

    assert "linked_artifact" not in artifact_index
