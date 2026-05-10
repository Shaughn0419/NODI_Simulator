from __future__ import annotations

import pytest

from nodi_simulator.review_package import write_review_manifests

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_review_package_hash_manifest_order_is_deterministic() -> None:
    write_review_manifests(root_path("."))
    first = root_path("REVIEW_PACKAGE_HASHES.sha256").read_text(encoding="utf-8")
    write_review_manifests(root_path("."))
    second = root_path("REVIEW_PACKAGE_HASHES.sha256").read_text(encoding="utf-8")

    assert first == second
    paths = [line.split("  ", 1)[1] for line in first.splitlines()]
    assert paths == sorted(paths)
