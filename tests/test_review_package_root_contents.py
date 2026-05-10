from __future__ import annotations

import pytest

from ._review_package_test_helpers import load_json, root_path


pytestmark = pytest.mark.review_package_required


def test_review_package_root_files_exist() -> None:
    load_json("REVIEW_PACKAGE_MANIFEST.json")

    assert root_path("REVIEW_PACKAGE_MANIFEST.json").is_file()
    assert root_path("REVIEW_PACKAGE_HASHES.sha256").is_file()
    assert root_path("REVIEW_PACKAGE_README.md").is_file()


def test_release_manifest_declares_p0b_artifacts_or_deferred_roles_without_stubs() -> None:
    manifest = load_json("REVIEW_PACKAGE_MANIFEST.json")
    deferred = manifest["deferred_p0b_roles"]
    groups = {group["group"]: group for group in manifest["artifact_groups"]}

    if deferred:
        assert all("deferred_to" in role for role in deferred)
    else:
        assert "post_v2_mandatory_audit_artifacts" in groups
        assert all(
            artifact["path_status"] == "exists"
            for artifact in groups["post_v2_mandatory_audit_artifacts"]["artifacts"]
        )
    assert "must_be_generated" not in root_path("REVIEW_PACKAGE_MANIFEST.json").read_text(
        encoding="utf-8"
    )
