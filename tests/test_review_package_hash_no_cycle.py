from __future__ import annotations

import pytest

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_review_package_hash_manifest_excludes_self_and_release_manifest() -> None:
    lines = root_path("REVIEW_PACKAGE_HASHES.sha256").read_text(encoding="utf-8").splitlines()
    paths = {line.split("  ", 1)[1] for line in lines}

    assert "REVIEW_PACKAGE_HASHES.sha256" not in paths
    assert "REVIEW_PACKAGE_MANIFEST.json" not in paths
    assert "REVIEW_BUILD_MANIFEST.json" not in paths
