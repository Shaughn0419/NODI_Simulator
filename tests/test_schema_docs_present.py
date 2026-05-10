from __future__ import annotations

import pytest

from ._review_package_test_helpers import root_path


pytestmark = pytest.mark.review_package_required


def test_schema_docs_exist_for_review_package_surfaces() -> None:
    expected = {
        "post_v2_mandatory_audit_schema.md",
        "review_package_manifest_schema.md",
        "noise_readout_scenario_bundle_schema.md",
        "ev_sample_profiles_schema.md",
        "forbidden_claims_lexicon_schema.md",
    }
    schema_dir = root_path("docs/schemas")
    actual = {path.name for path in schema_dir.glob("*.md")}

    assert expected.issubset(actual)
    for filename in expected:
        text = (schema_dir / filename).read_text(encoding="utf-8")
        assert "calibrated" in text.lower() or "relative" in text.lower()
