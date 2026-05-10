from __future__ import annotations

import hashlib

import pytest

from nodi_simulator.review_package import sha256_file

from ._review_package_test_helpers import load_json, root_path


pytestmark = pytest.mark.review_package_required


def test_hash_manifest_matches_release_manifest_artifacts() -> None:
    manifest = load_json("REVIEW_PACKAGE_MANIFEST.json")
    hash_path = root_path("REVIEW_PACKAGE_HASHES.sha256")
    entries = {}
    for line in hash_path.read_text(encoding="utf-8").splitlines():
        digest, relpath = line.split("  ", 1)
        entries[relpath] = digest

    expected_paths = set()
    for group in manifest["artifact_groups"]:
        for artifact in group["artifacts"]:
            expected_paths.add(artifact["path"])

    expected_paths.discard("REVIEW_PACKAGE_MANIFEST.json")
    expected_paths.discard("REVIEW_PACKAGE_HASHES.sha256")
    assert set(entries) == expected_paths
    for relpath, digest in entries.items():
        assert digest == sha256_file(root_path(relpath))


def test_hash_manifest_sha_is_pinned_in_manifest() -> None:
    manifest = load_json("REVIEW_PACKAGE_MANIFEST.json")
    digest = hashlib.sha256(root_path("REVIEW_PACKAGE_HASHES.sha256").read_bytes()).hexdigest()

    assert manifest["hashes_manifest_path"] == "REVIEW_PACKAGE_HASHES.sha256"
    assert manifest["hashes_manifest_sha256"] == digest
