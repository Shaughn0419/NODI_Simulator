from __future__ import annotations

import logging

import pytest

import nodi_simulator.parameter_sweep as parameter_sweep


def test_progress_callback_failure_is_logged_when_not_verbose(caplog):
    def failing_callback(_payload: dict) -> None:
        raise RuntimeError("progress sink unavailable")

    with caplog.at_level(logging.WARNING, logger=parameter_sweep.__name__):
        parameter_sweep._emit_progress_callback(
            progress_callback=failing_callback,
            progress_state={"completed_cases": 1},
            verbose=False,
        )

    assert "Sweep progress callback failed" in caplog.text
    assert "progress sink unavailable" in caplog.text


def test_case_result_callback_failure_is_logged_when_not_verbose(caplog):
    def failing_callback(_payload: dict) -> None:
        raise RuntimeError("checkpoint sink unavailable")

    with caplog.at_level(logging.WARNING, logger=parameter_sweep.__name__):
        parameter_sweep._emit_case_result_callback(
            case_result_callback=failing_callback,
            raw_result={"case_id": "example"},
            verbose=False,
        )

    assert "Sweep case-result callback failed" in caplog.text
    assert "checkpoint sink unavailable" in caplog.text


def test_progress_callback_failure_can_raise_in_strict_mode():
    def failing_callback(_payload: dict) -> None:
        raise RuntimeError("strict progress failure")

    with pytest.raises(RuntimeError, match="strict progress failure"):
        parameter_sweep._emit_progress_callback(
            progress_callback=failing_callback,
            progress_state={"completed_cases": 1},
            verbose=False,
            callback_error_policy="raise",
        )


def test_case_result_callback_failure_can_raise_in_strict_mode():
    def failing_callback(_payload: dict) -> None:
        raise RuntimeError("strict checkpoint failure")

    with pytest.raises(RuntimeError, match="strict checkpoint failure"):
        parameter_sweep._emit_case_result_callback(
            case_result_callback=failing_callback,
            raw_result={"case_id": "example"},
            verbose=False,
            callback_error_policy="raise",
        )
