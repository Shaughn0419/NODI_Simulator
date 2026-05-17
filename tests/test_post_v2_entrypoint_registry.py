from __future__ import annotations

from pathlib import Path

from nodi_simulator.post_v2_entrypoint_registry import (
    POST_V2_MODULE_ENTRIES,
    indexed_post_v2_modules,
    indexed_post_v2_tools,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_post_v2_module_registry_covers_package_entrypoints():
    package_modules = {
        path.stem
        for path in (PROJECT_ROOT / "nodi_simulator").glob("post_v2*.py")
        if path.name != "post_v2_entrypoint_registry.py"
    }

    assert package_modules == indexed_post_v2_modules()
    assert all(entry.lifecycle.startswith("active_") for entry in POST_V2_MODULE_ENTRIES)


def test_post_v2_tool_registry_covers_generator_and_verifier_wrappers():
    tool_entrypoints = {
        path.relative_to(PROJECT_ROOT).as_posix()
        for path in (PROJECT_ROOT / "tools").glob("*_post_v2*.py")
        if path.name.startswith(("generate_", "verify_"))
    }

    assert tool_entrypoints == indexed_post_v2_tools()
