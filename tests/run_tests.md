# `tests/run_tests.py`

`tests/run_tests.py` is the canonical fast full-suite runner. It still supports
the older local command:

```bash
python tests/run_tests.py --workers 8
```

By default it starts two independent lanes at the same time:

- non-AppTest pytest modules with `pytest-xdist`
- real Streamlit `app_interactions` tests in one serial AppTest process

Keep AppTest tests focused on routing/render smoke. Move content assertions and
page-helper regressions into ordinary pytest tests so they stay in the xdist
lane.

For routine full regression checks, prefer:

```bash
python tests/run_tests.py --workers 7
```

For focused development, use the direct verification commands:

```bash
ruff check .
python -m pyright
python -m mypy
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_targeted_module.py -q
```

`pyright` and `mypy` currently cover the typed seed allowlist in their config
files. Treat that as a real but intentionally scoped type gate while the broader
repository type debt is reduced.

The latest local timing baseline was:

```text
pre-change serial full pytest -> 214.69s wall time
two-lane full runner before AppTest pruning -> 101.80s wall time
AppTest lane after pruning full-page-only checks -> 5 passed in 3.67s wall time
```

`review_bundles/`, `.claude/`, virtual environments, caches, and generated
artifact directories are excluded from normal collection. This prevents external
review packages and local agent scratch files from being interpreted as project
tests.

On mounted macOS storage, AppleDouble `._*` metadata files can reappear beside
tracked files. They are ignored by git and should be excluded from ad hoc
recursive compile/static checks; the canonical runner works from pytest's normal
collection and the repository's ignore rules instead of treating those metadata
forks as source.

The wrapper should remain broad. Do not narrow it to a small subset of test
files, because the project relies on cross-cutting regression coverage for the
dashboard, full-grid result processing, selected-annulus side lanes, Tsuyama
paper-audit boundaries, realism v2 governance, and claim guardrails.

Related docs:

- [guides/operations/14_测试说明.md](../guides/operations/14_测试说明.md)
- [README.md](../README.md)
- [文档导航.md](../文档导航.md)
