from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_generated_artifact_boundary_is_reader_discoverable():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    boundary = (PROJECT_ROOT / "docs" / "GENERATED_ARTIFACT_BOUNDARY.md").read_text(
        encoding="utf-8"
    )

    assert "docs/GENERATED_ARTIFACT_BOUNDARY.md" in readme
    assert "docs/POST_V2_ENTRYPOINTS.md" in readme
    for required_path in (
        "results/",
        "exports/",
        "review_bundles/",
        ".pdf_output/",
        ".pytest_cache/",
        ".ruff_cache/",
        ".mypy_cache/",
    ):
        assert required_path in boundary
