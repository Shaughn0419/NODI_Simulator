"""Gate3 pre-authorization intake emulator for NODI-COMSOL packages.

The emulator is intentionally pre-production.  It classifies hypothetical,
template, dossier, and closure-trial rows into receiver dispositions without
accepting evidence, opening formula use, or changing the frozen Gate2D ledger.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nodi_simulator.nodi_comsol_gate2_interface_contracts import (
    AUTHORIZATION_FALSE_FIELDS,
    FALSE_VALUES,
    FORBIDDEN_TERMS,
)


DISPOSITIONS = (
    "ACCEPT_EXISTING_GATE2D_CONTEXT_ONLY",
    "RECEIVE_REVIEW_ONLY",
    "PREAUTH_REQUIRED",
    "REJECT_BLOCKED",
    "HARD_FAIL_FORBIDDEN_AUTHORIZATION",
)


@dataclass(frozen=True)
class IntakeDecision:
    disposition: str
    reason: str
    required_next_gate: str
    allowed_use: str
    blocked_use: str
    human_review_required: bool
    future_authorization_required: bool

    def as_row(self) -> dict[str, str]:
        return {
            "disposition": self.disposition,
            "reason": self.reason,
            "required_next_gate": self.required_next_gate,
            "allowed_use": self.allowed_use,
            "blocked_use": self.blocked_use,
            "human_review_required": str(self.human_review_required).lower(),
            "future_authorization_required": str(self.future_authorization_required).lower(),
        }


def has_forbidden_authorization(row: dict[str, Any]) -> bool:
    for field in AUTHORIZATION_FALSE_FIELDS:
        if field in row and str(row[field]).strip().lower() not in FALSE_VALUES:
            return True
    joined = " ".join(f"{key}={value}" for key, value in row.items()).lower()
    positive_patterns = (
        "authorized=true",
        "authorization=true",
        "approved=true",
        "policy_use_requested=true",
        "formula_use_authorized=true",
        "qch_weighting_authorized=true",
        "jrc_authorized=true",
        "production_ingestion_authorized=true",
        "runtime_configuration_authorized=true",
    )
    return any(pattern in joined for pattern in positive_patterns)


def is_blocked_or_fixture_mention(row: dict[str, Any]) -> bool:
    joined = " ".join(str(value).lower() for value in row.values())
    markers = ("blocked", "fixture", "negative", "denial", "not approved", "claim boundary", "blocked_use")
    return any(term.lower() in joined for term in FORBIDDEN_TERMS) and any(marker in joined for marker in markers)


def workstream_of(row: dict[str, Any]) -> str:
    text = " ".join(str(value).upper() for value in row.values())
    if "QCH" in text or "Q_CH" in text or "FLOW" in text:
        return "QCH"
    if "BINDING" in text or "D1200" in text or "220" in text or "UNBOUND" in text:
        return "BINDING"
    if "EDGE" in text or "EDGE20" in text or "EDGE4" in text:
        return "EDGE"
    if "V4" in text:
        return "V4"
    if "LOCAL_Q" in text or "LOCAL-Q" in text:
        return "LOCAL_Q"
    return str(row.get("workstream", "UNKNOWN") or "UNKNOWN")


def required_gate_for_workstream(workstream: str) -> str:
    if workstream == "EDGE":
        return "Gate3_EDGE_PREAUTH_NUMERIC_LOSS_ERROR_REVIEW"
    if workstream == "QCH":
        return "Gate3_QCH_FORMAL_SIDECAR_PREAUTH_REVIEW"
    if workstream == "BINDING":
        return "Gate3_BINDING_EXACT_REPAIR_PREAUTH_REVIEW"
    return "Gate3_REVIEW_ONLY_TRIAGE"


def decide_intake(row: dict[str, Any], *, row_kind: str = "dossier") -> IntakeDecision:
    if has_forbidden_authorization(row):
        return IntakeDecision(
            disposition="HARD_FAIL_FORBIDDEN_AUTHORIZATION",
            reason="row contains positive authorization semantics",
            required_next_gate="Gate3_FORBIDDEN_AUTHORIZATION_REMEDIATION",
            allowed_use="none",
            blocked_use="all downstream use",
            human_review_required=True,
            future_authorization_required=False,
        )

    text = " ".join(str(value).lower() for value in row.values())
    if row_kind == "gate2d_ledger" and "context_only_acceptance_allowed" in row:
        return IntakeDecision(
            disposition="ACCEPT_EXISTING_GATE2D_CONTEXT_ONLY",
            reason="existing frozen Gate2D context-only row; no expansion",
            required_next_gate="Gate2D_LEDGER_FREEZE_ONLY",
            allowed_use="existing context-only ledger reference",
            blocked_use="formula; weighting; JRC; production/runtime; grain-level ingestion",
            human_review_required=False,
            future_authorization_required=False,
        )

    workstream = workstream_of(row)
    if "not_evidence" in text or "template_only" in text or row_kind in {"template", "negative_fixture", "synthetic"}:
        return IntakeDecision(
            disposition="RECEIVE_REVIEW_ONLY",
            reason="template/synthetic/fixture row is not evidence",
            required_next_gate=required_gate_for_workstream(workstream),
            allowed_use="contract validation and negative-fixture testing",
            blocked_use="evidence acceptance; formula; weighting; JRC; production/runtime",
            human_review_required=False,
            future_authorization_required=True,
        )

    if is_blocked_or_fixture_mention(row) or "blocked" in text or "fail_closed" in text:
        return IntakeDecision(
            disposition="REJECT_BLOCKED",
            reason="row is blocked or fail-closed under current receiver policy",
            required_next_gate=required_gate_for_workstream(workstream),
            allowed_use="blocker tracking only",
            blocked_use="evidence acceptance; policy approval; formula; production/runtime",
            human_review_required=True,
            future_authorization_required=True,
        )

    if row_kind in {"closure_trial", "dossier"}:
        return IntakeDecision(
            disposition="PREAUTH_REQUIRED",
            reason="dossier/trial requires future pre-authorization before evidence intake",
            required_next_gate=required_gate_for_workstream(workstream),
            allowed_use="pre-authorization review preparation",
            blocked_use="evidence acceptance; formula; weighting; JRC; production/runtime",
            human_review_required=True,
            future_authorization_required=True,
        )

    return IntakeDecision(
        disposition="RECEIVE_REVIEW_ONLY",
        reason="row is review-only under default fail-closed receiver posture",
        required_next_gate=required_gate_for_workstream(workstream),
        allowed_use="review context only",
        blocked_use="evidence acceptance; formula; weighting; JRC; production/runtime",
        human_review_required=True,
        future_authorization_required=True,
    )
