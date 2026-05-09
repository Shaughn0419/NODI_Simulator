from __future__ import annotations

import re
import runpy
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _python_sources(*roots: Path) -> list[Path]:
    return [
        path
        for root in roots
        for path in root.rglob("*.py")
        if not path.name.startswith((".", "_"))
    ]


def test_legacy_one_shot_help_and_bare_call_do_not_execute_underlying_writer(tmp_path):
    blocked_output_dir = tmp_path / "should-not-run"
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "ev_nodi_realism_v2_R6_route_prior_sensitivity_audit.py"),
            "--help",
        ],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Compatibility wrapper for a tiered one-shot tool." in result.stdout

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "ev_nodi_realism_v2_R6_route_prior_sensitivity_audit.py"),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "refuses to execute one-shot writers" in result.stdout

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "tools" / "ev_nodi_realism_v2_R6_route_prior_sensitivity_audit.py"),
            "--output-dir",
            str(blocked_output_dir),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "refuses to execute one-shot writers" in result.stdout
    assert not blocked_output_dir.exists()


def test_canonical_one_shot_help_and_stray_args_do_not_execute_underlying_writer(tmp_path):
    blocked_output_dir = tmp_path / "should-not-run"
    script = (
        PROJECT_ROOT
        / "tools"
        / "one_shot"
        / "ev_nodi_realism_v2_R6_route_prior_sensitivity_audit.py"
    )

    help_result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "--execute" in help_result.stdout
    assert "--output-dir" in help_result.stdout
    assert "--write-root-manifest" in help_result.stdout

    refusal = subprocess.run(
        [sys.executable, str(script)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert refusal.returncode != 0
    assert "refusing to execute one-shot writer without --execute" in refusal.stderr

    stray_arg = subprocess.run(
        [sys.executable, str(script), "--output-dir", str(blocked_output_dir)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert stray_arg.returncode != 0
    assert not blocked_output_dir.exists()


def test_legacy_run_tool_forwards_execute_to_canonical_module(monkeypatch):
    from tools._legacy_entrypoint import run_legacy_tool

    observed: dict[str, object] = {}

    def fake_run_module(module_name: str, *, run_name: str) -> None:
        observed["module_name"] = module_name
        observed["run_name"] = run_name
        observed["argv"] = list(sys.argv)

    monkeypatch.setattr(runpy, "run_module", fake_run_module)
    monkeypatch.setattr(sys, "argv", ["legacy.py", "--execute", "--sentinel"])

    run_legacy_tool(
        "tools.one_shot.fake_writer",
        require_execute=True,
        pass_execute_to_module=True,
    )

    assert observed == {
        "module_name": "tools.one_shot.fake_writer",
        "run_name": "__main__",
        "argv": ["legacy.py", "--execute", "--sentinel"],
    }


def test_every_legacy_one_shot_wrapper_requires_execute():
    one_shot_modules = {
        f"tools.one_shot.{path.stem}"
        for path in (PROJECT_ROOT / "tools" / "one_shot").glob("*.py")
        if not path.name.startswith((".", "_"))
    }
    matched_modules: set[str] = set()

    for legacy_path in (PROJECT_ROOT / "tools").glob("*.py"):
        if legacy_path.name.startswith((".", "_")):
            continue
        source = legacy_path.read_text(encoding="utf-8")
        for module in one_shot_modules:
            if module in source:
                matched_modules.add(module)
                assert "safe_help=True" in source, f"{legacy_path.name} missing safe_help"
                assert "require_execute=True" in source, (
                    f"{legacy_path.name} missing require_execute"
                )
                line_count = len(source.splitlines())
                assert line_count <= 30, (
                    f"{legacy_path.name} grew beyond minimal wrapper shape "
                    f"({line_count} lines); switch this test to AST checks if "
                    "the wrapper is doing real logic."
                )
                break

    assert matched_modules == one_shot_modules


def test_entrypoints_do_not_prepend_project_parent_to_import_path():
    for path in _python_sources(PROJECT_ROOT / "tools", PROJECT_ROOT / "dashboard"):
        source = path.read_text(encoding="utf-8")
        assert "PROJECT_PARENT =" not in source, f"{path} should not add project parent"
        assert "PARENT = PROJECT_ROOT.parent" not in source, (
            f"{path} should not add project parent"
        )
        assert "project_parent = project_root.parent" not in source, (
            f"{path} should not add project parent"
        )


def test_retired_root_package_module_fallbacks_are_absent():
    root_realism_import = re.compile(r"^\s*import\s+realism_v2\s+as\s+rv2\b", re.MULTILINE)
    direct_realism_import = re.compile(
        r"^\s*from\s+nodi_simulator[.]realism_v2\s+import\b",
        re.MULTILINE,
    )
    root_helper_imports = re.compile(
        r"^\s*from\s+(realism_v2_io|type_coerce)\s+import\b",
        re.MULTILINE,
    )
    paths = _python_sources(PROJECT_ROOT / "tools" / "one_shot") + [
        PROJECT_ROOT / "nodi_simulator" / "realism_v2.py",
    ]
    for path in paths:
        source = path.read_text(encoding="utf-8")
        assert not root_realism_import.search(source), (
            f"{path} must not fall back to retired root realism_v2.py"
        )
        assert not direct_realism_import.search(source), (
            f"{path} should import nodi_simulator.realism_v2 through the package namespace"
        )
        assert not root_helper_imports.search(source), (
            f"{path} must not import retired root helper modules"
        )
