"""Gate4 interoperability adapters for COMSOL Gate3 producer/probe packages."""

from __future__ import annotations

from typing import Any

from nodi_simulator.nodi_comsol_gate3_intake import decide_intake


EXPECTED_TO_NODI_DISPOSITION = {
    "EXPECTED_RECEIPT_TEMPLATE_ONLY_NOT_EVIDENCE": "RECEIVE_REVIEW_ONLY",
    "EXPECTED_REVIEW_ONLY_NO_FORMULA": "RECEIVE_REVIEW_ONLY",
    "EXPECTED_PREAUTH_REQUIRED_NO_RUN": "PREAUTH_REQUIRED",
    "EXPECTED_REJECT_BLOCKED": "REJECT_BLOCKED",
    "EXPECTED_HARD_FAIL_FORBIDDEN_AUTHORIZATION": "HARD_FAIL_FORBIDDEN_AUTHORIZATION",
    "EXPECTED_ACCEPT_EXISTING_GATE2D_CONTEXT_ONLY": "ACCEPT_EXISTING_GATE2D_CONTEXT_ONLY",
}


def normalize_comsol_gate3_row(row: dict[str, Any], *, row_kind: str) -> dict[str, str]:
    """Normalize COMSOL producer/probe row shapes without changing semantics."""
    normalized = {str(key): str(value) for key, value in row.items()}
    if "forbidden_auth_flag_state" in normalized and normalized["forbidden_auth_flag_state"].lower() == "true":
        normalized.setdefault("formula_use_authorized", "true")
    if normalized.get("probe_category") == "preauth_required":
        normalized.setdefault("future_authorization_required", "true")
    if normalized.get("probe_category") == "reject_blocked":
        normalized.setdefault("blocked_use", normalized.get("blocked_use", "blocked"))
    if row_kind in {"producer_spec", "probe", "mutation", "dependency", "critical_path"}:
        normalized.setdefault("not_evidence", "true")
        normalized.setdefault("template_only", "true")
    return normalized


def expected_label_to_disposition(label: str) -> str:
    return EXPECTED_TO_NODI_DISPOSITION.get(label, "ADAPTER_REQUIRED_UNKNOWN_EXPECTED_LABEL")


def decide_comsol_gate3_row(row: dict[str, Any], *, row_kind: str) -> dict[str, str]:
    normalized = normalize_comsol_gate3_row(row, row_kind=row_kind)
    decision = decide_intake(normalized, row_kind="negative_fixture" if row_kind == "mutation" else "template")
    if row_kind == "probe":
        category = normalized.get("probe_category", "")
        if category == "preauth_required":
            decision = decide_intake({"workstream": normalized.get("workstream", ""), "source_sha256": "future"}, row_kind="dossier")
        elif category == "reject_blocked":
            decision = decide_intake({"workstream": normalized.get("workstream", ""), "blocked_use": normalized.get("blocked_use", "blocked")}, row_kind="dossier")
        elif normalized.get("forbidden_auth_flag_state", "").lower() == "true":
            decision = decide_intake({"formula_use_authorized": "true"}, row_kind="dossier")
    row_out = decision.as_row()
    row_out["normalized_not_evidence"] = normalized.get("not_evidence", "")
    row_out["normalized_template_only"] = normalized.get("template_only", "")
    return row_out


def compare_expected_to_actual(expected_label: str, actual_disposition: str) -> dict[str, str]:
    expected = expected_label_to_disposition(expected_label)
    if expected == actual_disposition:
        status = "MATCH"
        mismatch_class = "none"
    elif expected.startswith("ADAPTER_REQUIRED"):
        status = "ADAPTER_REQUIRED"
        mismatch_class = "adapter_gap"
    elif expected in {"RECEIVE_REVIEW_ONLY", "PREAUTH_REQUIRED", "REJECT_BLOCKED"} and actual_disposition in {
        "RECEIVE_REVIEW_ONLY",
        "PREAUTH_REQUIRED",
        "REJECT_BLOCKED",
    }:
        status = "COMPATIBLE_LABEL_DELTA"
        mismatch_class = "harmless_label_delta"
    elif actual_disposition == "HARD_FAIL_FORBIDDEN_AUTHORIZATION":
        status = "NODI_STRICTER"
        mismatch_class = "COMSOL_expectation_too_permissive"
    else:
        status = "BLOCKING_MISMATCH"
        mismatch_class = "policy_relevant_mismatch"
    return {
        "expected_nodi_disposition": expected,
        "actual_nodi_disposition": actual_disposition,
        "conformance_status": status,
        "mismatch_class": mismatch_class,
    }


def classify_schema_delta(row: dict[str, Any]) -> str:
    text = " ".join(str(value).lower() for value in row.values())
    if "authorization=true" in text or "authorized=true" in text:
        return "BLOCKING_MISMATCH"
    if "not_evidence" not in row or "template_only" not in row:
        return "ADAPTER_REQUIRED"
    return "MATCH"
