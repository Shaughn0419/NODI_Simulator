# `tests/run_tests.py`

`tests/run_tests.py` is a compatibility wrapper for older local commands. It
still supports:

```bash
python tests/run_tests.py --workers 8
```

For current development, prefer the direct verification commands:

```bash
ruff check .
python -m pyright
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q
```

The latest local cleanup/review baseline was:

```text
ruff check . -> pass
python -m pyright -> 0 errors, 0 warnings
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q -> 953 passed
```

`review_bundles/`, `.claude/`, virtual environments, caches, and generated
artifact directories are excluded from normal collection. This prevents external
review packages and local agent scratch files from being interpreted as project
tests.

The wrapper should remain broad. Do not narrow it to a small subset of test
files, because the project relies on cross-cutting regression coverage for the
dashboard, full-grid result processing, selected-annulus side lanes, Tsuyama
paper-audit boundaries, realism v2 governance, and claim guardrails.

Related docs:

- [guides/operations/14_测试说明.md](../guides/operations/14_测试说明.md)
- [README.md](../README.md)
- [文档导航.md](../文档导航.md)
