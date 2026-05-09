# Repository Guidance

This file applies to the whole repository.

## Test Runner

- Prefer `python tests/run_tests.py --workers 7` for full regression checks.
- `tests/run_tests.py` runs two lanes concurrently:
  - non-AppTest tests use pytest-xdist workers via `-m "not app_interactions"`
  - real Streamlit AppTest interaction tests use `-m "app_interactions"` and stay serial inside that lane
- `zsh tests/run_pytest_suite.sh` delegates to the same runner.
- Use `python tests/run_tests.py --workers 8 --sequential-lanes` only when reproducing the older non-AppTest-then-AppTest order.

## Adding Tests

- Put new pytest tests under `tests/` with normal `test_*.py` naming.
- Leave ordinary tests unmarked so they run in the parallel non-AppTest lane.
- Mark only real Streamlit UI/AppTest interaction tests with `@pytest.mark.app_interactions`.
- Keep AppTest tests as lightweight routing/render smoke tests; move content assertions, page-helper behavior, and old-navigation regressions into ordinary pytest tests when possible.
- Keep parallel-lane tests order independent and avoid fixed shared temp paths, un-restored global state, and unscoped environment changes.
- Prefer `tmp_path` for file output and `monkeypatch` for environment/global changes.
- Tests that depend on gitignored precomputed artifacts should use the existing `requires_results` / `tests/conftest.py` skip mechanism.
