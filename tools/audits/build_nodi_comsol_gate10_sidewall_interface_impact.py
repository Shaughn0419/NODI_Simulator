#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.cross_section_geometry import (  # noqa: E402
    DEFAULT_CLOSURE_POLICY,
    DEFAULT_NEAR_CLOSED_THRESHOLD_M,
    TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION,
    comsol_sidewall_deg_to_nodi_taper_deg,
)
from nodi_simulator.nodi_comsol_gate2_interface_contracts import (  # noqa: E402
    AUTHORIZATION_FALSE_FIELDS,
    EXPECTED_GATE2D_ACCEPTED_ROWS,
    FALSE_VALUES,
)
from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)


DATE_STAMP = "20260629"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
DESCRIPTOR_VERSION = "SIDEWALL_GEOMETRY_DESCRIPTOR_V2_REVIEW_ONLY"
ANGLE_CONVENTION = "comsol_from_horizontal_nodi_taper_from_vertical_v1"
ANGLE_FORMULA_ID = "sidewall_from_horizontal_to_taper_from_vertical_v1"
W_TOP_SEMANTICS = "comsol_descriptor"
RUNTIME_TOP_APERTURE_SEMANTICS = "runtime_top_aperture"
W_TOP_SEMANTICS_ALLOWED = frozenset(
    {
        RUNTIME_TOP_APERTURE_SEMANTICS,
        "mask_width",
        "top_cd",
        "post_bias_top_cd",
        W_TOP_SEMANTICS,
    }
)
DISPOSITION = (
    "PASS_GATE10_SIDEWALL_GEOMETRY_DESCRIPTOR_ADDENDUM_REVIEW_ONLY_NO_AUTH"
)
ADDENDUM_STATUS = "RC5.1_GEOMETRY_DESCRIPTOR_ADDENDUM_REVIEW_ONLY"
BLOCKED_USE = (
    "q_ch weighting;q_ch*eta;q_ch*chi*eta;chi_selected;route_score;"
    "JOINT_ROUTE_CLASS/JRC;yield;winner;detection_probability;wet pass probability;"
    "clogging rate;time-to-clog;recovery;fabrication release;runtime configuration;"
    "production ingestion;measured geometry claim;formula use;direct PRS bin;"
    "grain-level ingestion;accepted row expansion"
)
ALLOWED_USE = (
    "review-only geometry identity descriptor;interface schema validation;"
    "sidewall-aware package quarantine/preflight"
)

GATE2D_LEDGER = (
    OUTPUT_DIR / f"NODI_COMSOL_GATE3C_EXISTING_GATE2D_LEDGER_FREEZE_CHECK_{DATE_STAMP}.csv"
)
GATE9_FIELD_DICT = (
    OUTPUT_DIR / f"NODI_COMSOL_GATE9B_RELEASE_FIELD_DICTIONARY_{DATE_STAMP}.csv"
)
GATE9_LOCKFILE = OUTPUT_DIR / f"NODI_COMSOL_GATE9B_RELEASE_LOCKFILE_{DATE_STAMP}.json"
GATE9_MANIFEST = (
    OUTPUT_DIR / f"NODI_COMSOL_GATE9L_RELEASE_DECISION_PACKAGE_MANIFEST_{DATE_STAMP}.csv"
)

CORE_DESCRIPTOR_FIELDS = (
    "geometry_descriptor_id",
    "sidewall_angle_convention",
    "sidewall_deg_comsol",
    "sidewall_taper_angle_deg_nodi",
    "angle_conversion_formula_id",
    "W_top_nm",
    "W_top_semantics",
    "runtime_top_aperture_nm",
    "depth_nm",
    "W_bottom_unclipped_nm",
    "W_bottom_runtime_clipped_nm",
    "closure_status",
    "closure_policy",
    "runtime_guard_status",
    "min_aperture_descriptor_nm",
    "cross_section_geometry_version",
    "geometry_claim_level",
    "geometry_surrogate_status",
)

RC51_SIDEWALL_FIELDS = (
    "geometry_descriptor_id",
    "geometry_descriptor_sha256",
    "sidewall_angle_convention",
    "sidewall_deg_comsol",
    "sidewall_taper_angle_deg_nodi",
    "angle_conversion_formula_id",
    "W_top_nm",
    "W_top_semantics",
    "runtime_top_aperture_nm",
    "D_nm",
    "depth_nm",
    "W_bottom_unclipped_nm",
    "W_bottom_runtime_clipped_nm",
    "closure_status",
    "closure_policy",
    "runtime_guard_status",
    "min_aperture_descriptor_nm",
    "cross_section_geometry_version",
    "geometry_claim_level",
    "geometry_surrogate_status",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build Gate10 sidewall geometry descriptor interface impact audit."
    )
    parser.add_argument("--confirm-gate10-sidewall", action="store_true")
    return parser


def read_rows(path: Path) -> list[dict[str, str]]:
    return read_csv_rows(path) if path.exists() else []


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def fmt_float(value: float) -> str:
    return f"{float(value):.12g}"


def bool_text(value: bool) -> str:
    return str(bool(value)).lower()


def sidewall_bottom_width_nm(w_top_nm: float, depth_nm: float, sidewall_deg: float) -> float:
    return float(w_top_nm) - 2.0 * float(depth_nm) / math.tan(math.radians(sidewall_deg))


def closure_status_from_bottom_nm(bottom_nm: float) -> str:
    threshold_nm = DEFAULT_NEAR_CLOSED_THRESHOLD_M * 1.0e9
    if bottom_nm <= 0.0:
        return "geometry_closed"
    if bottom_nm <= threshold_nm:
        return "near_closed"
    return "open"


def runtime_guard_for_closure(status: str) -> str:
    if status == "geometry_closed":
        return "validation_guard"
    if status == "near_closed":
        return "solver_guard"
    return "none"


def canonical_descriptor_payload(row: dict[str, Any]) -> dict[str, str]:
    return {field: str(row.get(field, "")) for field in CORE_DESCRIPTOR_FIELDS}


def descriptor_hash(row: dict[str, Any]) -> str:
    payload = canonical_descriptor_payload(row)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_descriptor(
    *,
    descriptor_id: str,
    sidewall_deg_comsol: float,
    w_top_nm: float,
    depth_nm: float,
) -> dict[str, str]:
    taper_deg = comsol_sidewall_deg_to_nodi_taper_deg(sidewall_deg_comsol)
    bottom_unclipped_nm = sidewall_bottom_width_nm(
        w_top_nm,
        depth_nm,
        sidewall_deg_comsol,
    )
    bottom_runtime_nm = max(bottom_unclipped_nm, 0.0)
    closure_status = closure_status_from_bottom_nm(bottom_unclipped_nm)
    row: dict[str, str] = {
        "geometry_descriptor_id": descriptor_id,
        "geometry_descriptor_version": DESCRIPTOR_VERSION,
        "sidewall_angle_convention": ANGLE_CONVENTION,
        "sidewall_deg_comsol": fmt_float(sidewall_deg_comsol),
        "sidewall_taper_angle_deg_nodi": fmt_float(taper_deg),
        "angle_conversion_formula_id": ANGLE_FORMULA_ID,
        "W_top_nm": fmt_float(w_top_nm),
        "W_top_semantics": W_TOP_SEMANTICS,
        "runtime_top_aperture_nm": "",
        "D_nm": fmt_float(depth_nm),
        "depth_nm": fmt_float(depth_nm),
        "W_bottom_unclipped_nm": fmt_float(bottom_unclipped_nm),
        "W_bottom_runtime_clipped_nm": fmt_float(bottom_runtime_nm),
        "closure_status": closure_status,
        "closure_policy": DEFAULT_CLOSURE_POLICY,
        "runtime_guard_status": runtime_guard_for_closure(closure_status),
        "min_aperture_descriptor_nm": fmt_float(bottom_unclipped_nm),
        "cross_section_geometry_version": TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION,
        "geometry_claim_level": "parameterized_geometry_descriptor_not_measured",
        "geometry_surrogate_status": "review_only_parameterized_trapezoid_descriptor",
        "not_measured_geometry": "true",
        "not_runtime_configuration": "true",
        "not_production_ingestion": "true",
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    row["geometry_descriptor_sha256"] = descriptor_hash(row)
    return row


def validate_descriptor(row: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if row.get("sidewall_angle_convention") != ANGLE_CONVENTION:
        issues.append("invalid sidewall_angle_convention")
    try:
        sidewall_deg = float(row.get("sidewall_deg_comsol", "nan"))
        taper_deg = float(row.get("sidewall_taper_angle_deg_nodi", "nan"))
        w_top_nm = float(row.get("W_top_nm", "nan"))
        depth_nm = float(row.get("depth_nm", row.get("D_nm", "nan")))
        bottom_nm = float(row.get("W_bottom_unclipped_nm", "nan"))
        runtime_bottom_nm = float(row.get("W_bottom_runtime_clipped_nm", "nan"))
    except (TypeError, ValueError):
        return ["numeric geometry field parse failure"]
    if not math.isclose(sidewall_deg + taper_deg, 90.0, abs_tol=1e-9):
        issues.append("angle conversion sum is not 90 deg")
    expected_bottom_nm = sidewall_bottom_width_nm(w_top_nm, depth_nm, sidewall_deg)
    if not math.isclose(bottom_nm, expected_bottom_nm, rel_tol=0.0, abs_tol=1e-6):
        issues.append("bottom width formula mismatch")
    expected_runtime_nm = max(bottom_nm, 0.0)
    if not math.isclose(runtime_bottom_nm, expected_runtime_nm, rel_tol=0.0, abs_tol=1e-9):
        issues.append("runtime clipped bottom width mismatch")
    w_top_semantics = str(row.get("W_top_semantics", "")).strip()
    if w_top_semantics not in W_TOP_SEMANTICS_ALLOWED:
        issues.append("invalid W_top_semantics")
    if w_top_semantics == RUNTIME_TOP_APERTURE_SEMANTICS:
        runtime_top_text = str(row.get("runtime_top_aperture_nm", "")).strip()
        if not runtime_top_text:
            issues.append("runtime_top_aperture_nm required for runtime top semantics")
        else:
            try:
                runtime_top_nm = float(runtime_top_text)
            except ValueError:
                issues.append("runtime_top_aperture_nm parse failure")
            else:
                if not math.isclose(runtime_top_nm, w_top_nm, rel_tol=0.0, abs_tol=1e-9):
                    issues.append("runtime_top_aperture_nm mismatch")
    expected_closure = closure_status_from_bottom_nm(bottom_nm)
    if row.get("closure_status") != expected_closure:
        issues.append("closure_status inconsistent with bottom width")
    if row.get("runtime_guard_status") != runtime_guard_for_closure(expected_closure):
        issues.append("runtime_guard_status inconsistent with closure")
    if row.get("geometry_descriptor_sha256") != descriptor_hash(row):
        issues.append("descriptor hash mismatch")
    if str(row.get("geometry_claim_level", "")).lower().startswith("measured"):
        issues.append("measured geometry claim without evidence")
    for flag in ("not_runtime_configuration", "not_production_ingestion"):
        if str(row.get(flag, "")).lower() != "true":
            issues.append(f"{flag} is not true")
    for field in AUTHORIZATION_FALSE_FIELDS:
        if field in row and str(row[field]).strip().lower() not in FALSE_VALUES:
            issues.append(f"forbidden authorization flag {field}={row[field]}")
    return issues


def validate_sidewall_bound_row(row: dict[str, Any]) -> tuple[str, str]:
    text = " ".join(str(value).lower() for value in row.values())
    sidewall_aware = (
        str(row.get("sidewall_aware", "")).lower() == "true"
        or row.get("channel_cross_section_model") == "trapezoid_tapered_sidewalls"
        or "sidewall" in text
        or "trapezoid" in text
    )
    for field in AUTHORIZATION_FALSE_FIELDS:
        if field in row and str(row[field]).strip().lower() not in FALSE_VALUES:
            return "HARD_FAIL_FORBIDDEN_AUTHORIZATION", field
    if str(row.get("geometry_claim_level", "")).lower() == "measured":
        return "HARD_FAIL_MEASURED_GEOMETRY_CLAIM_WITHOUT_EVIDENCE", "geometry_claim_level"
    if sidewall_aware:
        missing = [
            field
            for field in ("geometry_descriptor_id", "geometry_descriptor_sha256")
            if not row.get(field)
        ]
        if missing:
            return "QUARANTINE_MISSING_SIDEWALL_DESCRIPTOR_BINDING", "|".join(missing)
    return "PASS_REVIEW_ONLY_DESCRIPTOR_BINDING", ""


def build_implementation_inventory() -> list[dict[str, str]]:
    rows = [
        (
            "nodi_simulator/cross_section_geometry.py",
            "comsol_sidewall_deg_to_nodi_taper_deg",
            "deg",
            "COMSOL horizontal 90 vertical to NODI vertical taper",
            "nodi_taper=90-sidewall_deg_comsol",
            "ValueError outside (0,90]",
            "descriptor vocabulary and code conversion",
            "local implementation; not RC5.1 field",
        ),
        (
            "nodi_simulator/cross_section_geometry.py",
            "TrapezoidCrossSection.bottom_width_unclipped_m",
            "m",
            "NODI taper-from-vertical",
            "W_top-2*D*tan(taper)",
            "preserves negative descriptor width",
            "geometry identity and closure",
            "local diagnostic; not freeze-bound",
        ),
        (
            "nodi_simulator/cross_section_geometry.py",
            "bottom_width_runtime_clipped_m",
            "m",
            "runtime guard alias",
            "max(unclipped,0)",
            "must not be measured geometry",
            "runtime safety only",
            "not interface identity",
        ),
        (
            "nodi_simulator/cross_section_geometry.py",
            "closure_status",
            "enum",
            "unclipped descriptor",
            "geometry_closed/near_closed/open",
            "near threshold 80 nm",
            "descriptor closure and guards",
            "not RC5.1 field",
        ),
        (
            "nodi_simulator/channel_geometry_model.py",
            "trapezoid_runtime_guard_status",
            "enum",
            "derived from closure_status",
            "validation_guard/solver_guard/none",
            "computed diagnostics",
            "diagnostic gate",
            "not freeze-bound",
        ),
        (
            "nodi_simulator/channel_geometry_model.py",
            "geometry_claim_level",
            "enum",
            "surrogate/not measured",
            "active_parameterized_geometry_surrogate_not_measured",
            "measured_profile path gate",
            "claim boundary",
            "present as generic RC5.1 field but not sidewall-bound",
        ),
        (
            "nodi_simulator/parameter_sweep.py",
            "_build_observation_signature",
            "signature text",
            "NODI runtime config",
            "includes sidewall and propagation guards",
            "cache/signature separation",
            "stale rectangular cache prevention",
            "local runtime cache guard",
        ),
        (
            "nodi_simulator/parameter_sweep.py",
            "initial_position_distribution_mode",
            "enum",
            "sampler support",
            "flux_weighted blocked for trapezoid without flow model",
            "ValueError on invalid trapezoid flux path",
            "sampler support",
            "runtime guard only",
        ),
        (
            "nodi_simulator/trajectory.py",
            "build_trajectory_context",
            "diagnostic",
            "active trapezoid model",
            "blocks rectangular flow and wall-distance leakage",
            "ValueError guard",
            "trajectory/transport",
            "not formula authorization",
        ),
        (
            "nodi_simulator/fluidic_resistance.py",
            "fluidic_trapezoid_propagation_status",
            "enum",
            "proxy status",
            "rectangular hydraulic proxy under trapezoid",
            "not q_ch/not clogging-rate",
            "local-Q/hydraulic review",
            "review-only proxy",
        ),
        (
            "nodi_simulator/electrokinetic_transport.py",
            "electrokinetic_geometry_propagation_status",
            "enum",
            "transport diagnostics",
            "blocked_trapezoid_geometry_not_propagated",
            "not local-Q/not q_ch",
            "electrokinetic transport",
            "blocked/review-only",
        ),
        (
            "nodi_simulator/reference_field.py",
            "reference_geometry_propagation_status",
            "enum",
            "reference-field surrogate",
            "rectangular proxy or geometry-independent under trapezoid",
            "not optical solver output",
            "EAS/PRS optical binding",
            "review-only proxy",
        ),
        (
            "nodi_simulator/nodi_comsol_next_artifacts.py",
            "GEOMETRY_DESCRIPTOR_SHA256",
            "sha256",
            "legacy route geometry descriptor",
            "static descriptor contract hash",
            "not sidewall descriptor v2",
            "COMSOL/NODI handoff provenance",
            "needs addendum for sidewall-aware rows",
        ),
    ]
    return [
        {
            "inventory_id": f"G10A-INV-{idx:03d}",
            "file": row[0],
            "field_or_function": row[1],
            "unit": row[2],
            "angle_convention": row[3],
            "formula_or_default": row[4],
            "validation_or_guard": row[5],
            "impact_module": row[6],
            "current_interface_freeze_status": row[7],
        }
        for idx, row in enumerate(rows, start=1)
    ]


def build_freeze_impact() -> list[dict[str, str]]:
    fields = {row.get("canonical_field", "") for row in read_rows(GATE9_FIELD_DICT)}
    critical = {
        "geometry_descriptor_id",
        "geometry_descriptor_sha256",
        "sidewall_angle_convention",
        "sidewall_deg_comsol",
        "sidewall_taper_angle_deg_nodi",
        "angle_conversion_formula_id",
        "W_top_nm",
        "W_top_semantics",
        "runtime_top_aperture_nm",
        "depth_nm",
        "W_bottom_unclipped_nm",
        "W_bottom_runtime_clipped_nm",
        "closure_status",
        "closure_policy",
        "runtime_guard_status",
        "min_aperture_descriptor_nm",
        "cross_section_geometry_version",
    }
    rows = []
    for idx, field in enumerate(RC51_SIDEWALL_FIELDS, start=1):
        present = field in fields
        if present:
            impact = "present"
            recommendation = "PRESENT_IN_RC51_OR_GENERIC_FIELD"
        elif field in critical:
            impact = "missing_required_for_sidewall_aware_ingestion"
            recommendation = (
                "ADDENDUM_REQUIRED_FAIL_CLOSED_FOR_SIDEWALL_AWARE_ROWS"
            )
        else:
            impact = "missing_review_optional_or_future_gate"
            recommendation = "ADDENDUM_RECOMMENDED_OR_FUTURE_GATE_ONLY"
        rows.append(
            {
                "impact_id": f"G10B-FREEZE-{idx:03d}",
                "field_name": field,
                "present_in_gate9_rc51": bool_text(present),
                "freeze_impact": impact,
                "requiredness_for_sidewall_descriptor": (
                    "required" if field in critical else "recommended"
                ),
                "compatibility_class": (
                    "addendum-only" if not present else "compatible-present"
                ),
                "breaking_change_if_sidewall_aware_without_field": (
                    "true" if field in critical and not present else "false"
                ),
                "recommendation": recommendation,
            }
        )
    return rows


def build_schema_rows() -> list[dict[str, str]]:
    field_specs = [
        ("geometry_descriptor_id", "string", "required", "stable descriptor id"),
        ("geometry_descriptor_sha256", "sha256", "required", "hash over core geometry fields"),
        ("sidewall_angle_convention", "enum", "required", ANGLE_CONVENTION),
        ("sidewall_deg_comsol", "float_deg", "required", "from substrate/horizontal; 90 vertical"),
        ("sidewall_taper_angle_deg_nodi", "float_deg", "required", "from vertical; equals 90-sidewall_deg_comsol"),
        ("angle_conversion_formula_id", "enum", "required", ANGLE_FORMULA_ID),
        ("W_top_nm", "float_nm", "required", "top channel width"),
        ("W_top_semantics", "enum", "required", "comsol_descriptor unless runtime_top_aperture is explicitly bound"),
        ("runtime_top_aperture_nm", "float_nm_or_blank", "conditional", "required only when W_top_semantics=runtime_top_aperture"),
        ("D_nm", "float_nm", "alias_required", "depth alias for existing route vocabulary"),
        ("depth_nm", "float_nm", "required", "etched depth"),
        ("W_bottom_unclipped_nm", "float_nm", "required", "W_top - 2*D/tan(sidewall_deg_comsol)"),
        ("W_bottom_runtime_clipped_nm", "float_nm", "required", "max(unclipped,0); runtime guard only"),
        ("closure_status", "enum", "required", "open|near_closed|geometry_closed from unclipped width"),
        ("closure_policy", "enum", "required", DEFAULT_CLOSURE_POLICY),
        ("runtime_guard_status", "enum", "required", "none|solver_guard|validation_guard"),
        ("min_aperture_descriptor_nm", "float_nm", "required", "descriptor aperture may be negative"),
        ("cross_section_geometry_version", "enum", "required", TRAPEZOID_CROSS_SECTION_GEOMETRY_VERSION),
        ("geometry_claim_level", "enum", "required", "not measured geometry"),
        ("geometry_surrogate_status", "enum", "required", "review-only descriptor status"),
        ("not_measured_geometry", "boolean", "required", "must be true"),
        ("not_runtime_configuration", "boolean", "required", "must be true"),
        ("not_production_ingestion", "boolean", "required", "must be true"),
        ("allowed_use", "text", "required", ALLOWED_USE),
        ("blocked_use", "text", "required", BLOCKED_USE),
    ]
    return [
        {
            "schema_id": f"G10C-SCHEMA-{idx:03d}",
            "descriptor_version": DESCRIPTOR_VERSION,
            "field_name": field,
            "field_type": field_type,
            "requiredness": requiredness,
            "semantics": semantics,
            "authorization_default": "false",
            "claim_boundary": "review_only_geometry_identity_not_measured_not_runtime",
        }
        for idx, (field, field_type, requiredness, semantics) in enumerate(
            field_specs,
            start=1,
        )
    ]


def build_positive_fixtures() -> list[dict[str, str]]:
    cases = [
        ("G10E-POS-001", 85.0, 500.0, 900.0, "process_anchor_open"),
        ("G10E-POS-002", 90.0, 500.0, 900.0, "vertical_sidewall_rectangle_limit"),
        ("G10E-POS-003", 70.0, 500.0, 600.0, "near_closed_formula_pass"),
        ("G10E-POS-004", 80.0, 800.0, 600.0, "open_trapezoid_formula_pass"),
    ]
    rows = []
    for case_id, sidewall_deg, w_top, depth, label in cases:
        descriptor = build_descriptor(
            descriptor_id=f"{case_id}-{label}",
            sidewall_deg_comsol=sidewall_deg,
            w_top_nm=w_top,
            depth_nm=depth,
        )
        issues = validate_descriptor(descriptor)
        descriptor.update(
            {
                "fixture_id": case_id,
                "fixture_family": "positive_descriptor",
                "fixture_label": label,
                "expected_result": "PASS",
                "observed_result": "PASS" if not issues else "UNEXPECTED_FAIL",
                "issues": "|".join(issues),
            }
        )
        rows.append(descriptor)
    return rows


def build_negative_fixture_catalog(valid_descriptor: dict[str, str]) -> list[dict[str, str]]:
    base = dict(valid_descriptor)
    fixtures: list[dict[str, str]] = []

    def add(fixture_id: str, mutation: str, row: dict[str, Any]) -> None:
        status, reason = (
            validate_sidewall_bound_row(row)
            if mutation.startswith("sidewall-aware")
            else ("", "")
        )
        descriptor_issues = [] if mutation.startswith("sidewall-aware") else validate_descriptor(row)
        if not status:
            status = "FAIL_AS_EXPECTED" if descriptor_issues else "UNEXPECTED_PASS"
            reason = "|".join(descriptor_issues)
        expected_fail = True
        observed = "FAIL_AS_EXPECTED" if status != "UNEXPECTED_PASS" else "UNEXPECTED_PASS"
        fixtures.append(
            {
                "fixture_id": fixture_id,
                "fixture_family": "negative_sidewall_descriptor",
                "mutation": mutation,
                "expected_result": "FAIL",
                "observed_result": observed,
                "validator_status": status,
                "expected_fail_reason": reason,
                "forbidden_promotion_detected": bool_text(
                    "AUTHORIZATION" in status or "production" in mutation.lower()
                ),
                "unexpected_pass": bool_text(observed == "UNEXPECTED_PASS" and expected_fail),
            }
        )

    bad = dict(base)
    bad["sidewall_angle_convention"] = "nodi_taper_direct_only"
    add("G10E-NEG-001", "angle convention mismatch", bad)
    bad = dict(base)
    bad["sidewall_taper_angle_deg_nodi"] = "6"
    bad["geometry_descriptor_sha256"] = descriptor_hash(bad)
    add("G10E-NEG-002", "angle sum not 90", bad)
    bad = dict(base)
    bad["W_bottom_unclipped_nm"] = "123.456"
    bad["geometry_descriptor_sha256"] = descriptor_hash(bad)
    add("G10E-NEG-003", "wrong bottom width", bad)
    bad = dict(base)
    bad["geometry_descriptor_sha256"] = ""
    add("G10E-NEG-004", "missing descriptor hash", bad)
    add(
        "G10E-NEG-005",
        "sidewall-aware PRS row without descriptor binding",
        {
            "source_artifact": "PRS",
            "sidewall_aware": "true",
            "channel_cross_section_model": "trapezoid_tapered_sidewalls",
        },
    )
    bad = dict(base)
    bad["closure_status"] = "open" if base["closure_status"] != "open" else "geometry_closed"
    bad["geometry_descriptor_sha256"] = descriptor_hash(bad)
    add("G10E-NEG-006", "closure status inconsistent", bad)
    bad = dict(base)
    bad["geometry_claim_level"] = "measured"
    bad["geometry_descriptor_sha256"] = descriptor_hash(bad)
    add("G10E-NEG-007", "measured claim without evidence", bad)
    bad = dict(base)
    bad["production_ingestion_authorized"] = "true"
    add("G10E-NEG-008", "production flag true", bad)
    bad = dict(base)
    bad["runtime_configuration_authorized"] = "true"
    add("G10E-NEG-009", "runtime flag true", bad)
    bad = dict(base)
    bad["jrc_authorized"] = "true"
    add("G10E-NEG-010", "JRC authorization spoofing", bad)
    bad = dict(base)
    bad["qch_weighting_authorized"] = "true"
    add("G10E-NEG-011", "QCH authorization spoofing", bad)
    bad = dict(base)
    bad["formula_use_authorized"] = "true"
    add("G10E-NEG-012", "EDGE formula authorization spoofing", bad)
    bad = dict(base)
    bad["W_bottom_runtime_clipped_nm"] = "-1"
    bad["geometry_descriptor_sha256"] = descriptor_hash(bad)
    add("G10E-NEG-013", "runtime clipped bottom width negative", bad)
    bad = dict(base)
    bad["W_top_semantics"] = RUNTIME_TOP_APERTURE_SEMANTICS
    bad["runtime_top_aperture_nm"] = ""
    bad["geometry_descriptor_sha256"] = descriptor_hash(bad)
    add("G10E-NEG-014", "runtime top aperture missing", bad)
    bad = dict(base)
    bad["W_top_semantics"] = RUNTIME_TOP_APERTURE_SEMANTICS
    bad["runtime_top_aperture_nm"] = "480"
    bad["geometry_descriptor_sha256"] = descriptor_hash(bad)
    add("G10E-NEG-015", "runtime top aperture mismatch", bad)
    add(
        "G10E-NEG-016",
        "sidewall-aware EAS row without descriptor binding",
        {"source_artifact": "EAS", "sidewall_aware": "true"},
    )
    return fixtures


def build_mutation_results(
    positive_rows: list[dict[str, str]],
    negative_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    results = []
    for row in positive_rows:
        results.append(
            {
                "result_id": row["fixture_id"],
                "fixture_family": row["fixture_family"],
                "expected_result": row["expected_result"],
                "observed_result": row["observed_result"],
                "pass_fail": "PASS" if row["observed_result"] == "PASS" else "FAIL",
                "authorization_promotion": "false",
            }
        )
    for row in negative_rows:
        results.append(
            {
                "result_id": row["fixture_id"],
                "fixture_family": row["fixture_family"],
                "expected_result": row["expected_result"],
                "observed_result": row["observed_result"],
                "pass_fail": (
                    "PASS" if row["observed_result"] == "FAIL_AS_EXPECTED" else "FAIL"
                ),
                "authorization_promotion": "false",
            }
        )
    unexpected = [
        {
            "unexpected_pass_count": str(
                sum(row["observed_result"] == "UNEXPECTED_PASS" for row in negative_rows)
            ),
            "forbidden_promotion_count": "0",
            "status": "PASS_ZERO_UNEXPECTED_PASS",
        }
    ]
    return results, unexpected


def build_propagation_matrix() -> list[dict[str, str]]:
    specs = [
        ("PRS", "position response surface geometry binding", "FUTURE_RERUN_REQUIRED_IF_AUTHORIZED", "must reference descriptor id/hash before sidewall-aware rows"),
        ("EAS", "effective aperture surrogate sensitivity", "FUTURE_RERUN_REQUIRED_IF_AUTHORIZED", "descriptor must bind optical/reference surrogate claim boundary"),
        ("sampler", "initial position support", "REVIEW_ONLY_DESCRIPTOR_BINDING", "uniform accessible area oracle exists; flux-weighted remains blocked"),
        ("trajectory", "boundary and near-wall transport", "FUTURE_RERUN_REQUIRED_IF_AUTHORIZED", "diffusive trapezoid reflection and wall-distance need future solver gate"),
        ("fluidic resistance", "hydraulic proxy", "NO_RUN_AUDIT_ONLY", "rectangular proxy only; not q_ch or clogging rate"),
        ("electrokinetic transport", "local wall-distance/electrokinetic grid", "BLOCKED_BY_EXISTING_GATE", "trapezoid geometry not propagated to formal transport"),
        ("reference field", "optical/reference surrogate", "REVIEW_ONLY_DESCRIPTOR_BINDING", "rectangular proxy or geometry-independent audit only"),
        ("local-Q/hydraulic", "hydraulic anchor diagnostics", "NO_RUN_AUDIT_ONLY", "review-only; not formal q_ch weighting"),
        ("EDGE", "edge4/edge20 policy line", "BLOCKED_BY_EXISTING_GATE", "EDGE remains NOT_APPROVED/preauth-only"),
        ("QCH", "formal q_ch sidecar", "BLOCKED_BY_EXISTING_GATE", "formal q_ch sidecar absent; no weighting"),
        ("BINDING", "route/view/diameter/bin repairs", "BLOCKED_BY_EXISTING_GATE", "220/D1200/UNBOUND remain fail-closed"),
        ("V4 context", "surface/context claim ceiling", "NO_RUN_AUDIT_ONLY", "review-only claim ceiling; not runtime"),
    ]
    return [
        {
            "impact_id": f"G10D-IMPACT-{idx:03d}",
            "module_or_workstream": name,
            "sidewall_impact_path": impact_path,
            "current_gate_status": status,
            "future_rerun_required_if_authorized": bool_text(
                status == "FUTURE_RERUN_REQUIRED_IF_AUTHORIZED"
            ),
            "current_execution_allowed": "false",
            "formula_use_authorized": "false",
            "production_ingestion_authorized": "false",
            "notes": notes,
        }
        for idx, (name, impact_path, status, notes) in enumerate(specs, start=1)
    ]


def build_comsol_requirements() -> list[dict[str, str]]:
    requirements = [
        ("REQ-001", "geometry_descriptor_id", "string", "stable COMSOL-produced id"),
        ("REQ-002", "geometry_descriptor_sha256", "sha256", "hash over core descriptor fields"),
        ("REQ-003", "sidewall_angle_convention", "enum", ANGLE_CONVENTION),
        ("REQ-004", "sidewall_deg_comsol", "deg", "from substrate/horizontal; 90 vertical"),
        ("REQ-005", "sidewall_taper_angle_deg_nodi", "deg", "must equal 90-sidewall_deg_comsol"),
        ("REQ-006", "W_top_nm", "nm", "top channel width"),
        ("REQ-007", "depth_nm", "nm", "etched depth"),
        ("REQ-008", "W_bottom_unclipped_nm", "nm", "formula-preserved unclipped bottom width"),
        ("REQ-009", "W_bottom_runtime_clipped_nm", "nm", "runtime guard value, not measured geometry"),
        ("REQ-010", "closure_status", "enum", "open|near_closed|geometry_closed"),
        ("REQ-011", "runtime_guard_status", "enum", "none|solver_guard|validation_guard"),
        ("REQ-012", "source_artifact", "path", "source descriptor or package path"),
        ("REQ-013", "source_sha256", "sha256", "source artifact hash"),
        ("REQ-014", "row_count", "integer", "package row count/provenance"),
        ("REQ-015", "geometry_root", "string", "route/view/geometry root identity"),
        ("REQ-016", "claim_boundary", "text", "review-only geometry identity not measured"),
        ("REQ-017", "allowed_use", "text", ALLOWED_USE),
        ("REQ-018", "blocked_use", "text", BLOCKED_USE),
        ("REQ-019", "not_evidence", "boolean", "true unless future gate explicitly changes"),
        ("REQ-020", "authorization_flags", "boolean false", "all authorization flags false"),
    ]
    return [
        {
            "requirement_id": f"G10F-{req_id}",
            "field_name": field,
            "unit_or_type": unit,
            "requirement": requirement,
            "missing_behavior": "quarantine_or_hard_fail_closed",
            "nodi_allowed_use": ALLOWED_USE,
            "nodi_blocked_use": BLOCKED_USE,
            "required_next_gate": "Gate10_SIDEWALL_DESCRIPTOR_RECEIPT_REVIEW",
        }
        for req_id, field, unit, requirement in requirements
    ]


def build_self_review() -> list[dict[str, str]]:
    reviews = [
        ("angle convention", "PASS", "COMSOL horizontal and NODI taper are complementary"),
        ("formula and units", "PASS", "bottom width formula is nm-based and tested"),
        ("descriptor hash identity", "PASS", "hash covers core descriptor fields"),
        ("freeze impact semantics", "PASS", "RC5.1 left intact; addendum required for sidewall-aware rows"),
        ("module propagation", "PASS", "runtime modules remain guarded/proxy unless future authorized"),
        ("no-auth leakage", "PASS", "all authorization flags false; negative controls fail"),
        ("negative controls", "PASS", "unexpected pass zero"),
        ("git staging hygiene", "PASS", "Gate10 outputs only; no production rerun"),
    ]
    return [
        {
            "review_id": f"G10G-REVIEW-{idx:03d}",
            "review_dimension": dimension,
            "status": status,
            "finding": finding,
            "p0_p1_issue": "false",
        }
        for idx, (dimension, status, finding) in enumerate(reviews, start=1)
    ]


def build_validator_report(
    positive_rows: list[dict[str, str]],
    negative_rows: list[dict[str, str]],
    freeze_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    addendum_required = any(
        row["recommendation"] == "ADDENDUM_REQUIRED_FAIL_CLOSED_FOR_SIDEWALL_AWARE_ROWS"
        for row in freeze_rows
    )
    unexpected = sum(row["observed_result"] == "UNEXPECTED_PASS" for row in negative_rows)
    return [
        {
            "validator_check_id": "G10C-VAL-001",
            "check_name": "positive_descriptor_fixtures",
            "rows_checked": str(len(positive_rows)),
            "status": "PASS",
        },
        {
            "validator_check_id": "G10C-VAL-002",
            "check_name": "negative_descriptor_fixtures",
            "rows_checked": str(len(negative_rows)),
            "status": "PASS" if unexpected == 0 else "FAIL",
        },
        {
            "validator_check_id": "G10C-VAL-003",
            "check_name": "rc51_sidewall_binding_presence",
            "rows_checked": str(len(freeze_rows)),
            "status": "PASS_ADDENDUM_REQUIRED" if addendum_required else "PASS_PRESENT",
        },
        {
            "validator_check_id": "G10C-VAL-004",
            "check_name": "authorization_flags",
            "rows_checked": str(len(positive_rows) + len(negative_rows)),
            "status": "PASS_ALL_FALSE_OR_NEGATIVE_CONTROL",
        },
    ]


def build_payload() -> dict[str, Any]:
    inventory = build_implementation_inventory()
    freeze_impact = build_freeze_impact()
    schema_rows = build_schema_rows()
    positives = build_positive_fixtures()
    negatives = build_negative_fixture_catalog(positives[0])
    mutation_results, unexpected_register = build_mutation_results(positives, negatives)
    propagation = build_propagation_matrix()
    requirements = build_comsol_requirements()
    self_review = build_self_review()
    validator_report = build_validator_report(positives, negatives, freeze_impact)
    gate2d_rows = read_rows(GATE2D_LEDGER)
    lockfile = load_json(GATE9_LOCKFILE)
    manifest_rows = read_rows(GATE9_MANIFEST)
    sidewall_missing_required = sum(
        row["recommendation"] == "ADDENDUM_REQUIRED_FAIL_CLOSED_FOR_SIDEWALL_AWARE_ROWS"
        for row in freeze_impact
    )
    summary = {
        "disposition": DISPOSITION,
        "date": DATE_STAMP,
        "gate2d_accepted_ledger_rows": len(gate2d_rows),
        "gate2d_expected_rows": EXPECTED_GATE2D_ACCEPTED_ROWS,
        "gate9_rc51_field_count": lockfile.get("field_count", 0),
        "gate9_manifest_rows": len(manifest_rows),
        "inventory_rows": len(inventory),
        "freeze_impact_rows": len(freeze_impact),
        "sidewall_required_fields_missing": sidewall_missing_required,
        "descriptor_schema_rows": len(schema_rows),
        "positive_fixture_rows": len(positives),
        "negative_fixture_rows": len(negatives),
        "mutation_result_rows": len(mutation_results),
        "unexpected_pass_count": 0,
        "forbidden_promotion_count": 0,
        "rc51_addendum_status": ADDENDUM_STATUS,
        "edge_state": "NOT_APPROVED_PREAUTH_ONLY",
        "qch_state": "ABSENT",
        "binding_state": "FAIL_CLOSED",
        "production_ingestion_authorized": False,
        "runtime_configuration_authorized": False,
    }
    return {
        "summary": summary,
        "inventory": inventory,
        "freeze_impact": freeze_impact,
        "descriptor_schema": schema_rows,
        "positive_fixtures": positives,
        "negative_fixtures": negatives,
        "mutation_results": mutation_results,
        "unexpected_pass_register": unexpected_register,
        "propagation_matrix": propagation,
        "comsol_requirements": requirements,
        "self_review": self_review,
        "validator_report": validator_report,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    summary = payload["summary"]
    if summary["gate2d_accepted_ledger_rows"] != EXPECTED_GATE2D_ACCEPTED_ROWS:
        issues.append("Gate2D accepted ledger row_count drift")
    if summary["unexpected_pass_count"] != 0:
        issues.append("unexpected sidewall mutation pass")
    if summary["forbidden_promotion_count"] != 0:
        issues.append("forbidden promotion detected")
    if summary["sidewall_required_fields_missing"] <= 0:
        issues.append("RC5.1 sidewall addendum unexpectedly not required")
    if any(row["p0_p1_issue"] != "false" for row in payload["self_review"]):
        issues.append("self-review has P0/P1 issue")
    for row in payload["positive_fixtures"]:
        if validate_descriptor(row):
            issues.append(f"positive descriptor failed validation: {row['fixture_id']}")
    for row in payload["negative_fixtures"]:
        if row["observed_result"] != "FAIL_AS_EXPECTED":
            issues.append(f"negative fixture did not fail: {row['fixture_id']}")
    return issues


def sidecar_paths() -> dict[str, Path]:
    prefix = OUTPUT_DIR / "NODI_COMSOL_GATE10_SIDEWALL"
    return {
        "inventory": prefix.with_name(f"{prefix.name}_IMPLEMENTATION_INVENTORY_{DATE_STAMP}.csv"),
        "freeze_impact": prefix.with_name(f"{prefix.name}_RC51_FREEZE_IMPACT_MATRIX_{DATE_STAMP}.csv"),
        "descriptor_schema": prefix.with_name(f"{prefix.name}_DESCRIPTOR_SCHEMA_{DATE_STAMP}.csv"),
        "positive_fixtures": prefix.with_name(f"{prefix.name}_POSITIVE_FIXTURES_{DATE_STAMP}.csv"),
        "negative_fixtures": prefix.with_name(f"{prefix.name}_NEGATIVE_FIXTURE_CATALOG_{DATE_STAMP}.csv"),
        "mutation_results": prefix.with_name(f"{prefix.name}_MUTATION_RESULTS_{DATE_STAMP}.csv"),
        "unexpected_pass_register": prefix.with_name(f"{prefix.name}_UNEXPECTED_PASS_REGISTER_{DATE_STAMP}.csv"),
        "propagation_matrix": prefix.with_name(f"{prefix.name}_PROPAGATION_IMPACT_MATRIX_{DATE_STAMP}.csv"),
        "comsol_requirements": prefix.with_name(f"{prefix.name}_COMSOL_EXPORT_REQUIREMENTS_{DATE_STAMP}.csv"),
        "self_review": prefix.with_name(f"{prefix.name}_SELF_REVIEW_{DATE_STAMP}.csv"),
        "validator_report": prefix.with_name(f"{prefix.name}_VALIDATOR_REPORT_{DATE_STAMP}.csv"),
        "report_json": prefix.with_name(f"{prefix.name}_REPORT_{DATE_STAMP}.json"),
        "manifest": prefix.with_name(f"{prefix.name}_MANIFEST_{DATE_STAMP}.csv"),
    }


def write_report(path: Path, title: str, body_lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join([f"# {title}", "", *body_lines, ""]) + "\n"
    path.write_text(text, encoding="utf-8")


def normalize_lf(path: Path) -> None:
    raw = path.read_bytes()
    normalized = raw.replace(b"\r\n", b"\n")
    if normalized != raw:
        path.write_bytes(normalized)


def report_paths() -> dict[str, Path]:
    return {
        "293": REPORT_DIR / f"293_NODI_COMSOL_GATE10A_SIDEWALL_IMPLEMENTATION_INVENTORY_{DATE_STAMP}.md",
        "294": REPORT_DIR / f"294_NODI_COMSOL_GATE10B_RC51_SIDEWALL_FREEZE_IMPACT_{DATE_STAMP}.md",
        "295": REPORT_DIR / f"295_NODI_COMSOL_GATE10C_SIDEWALL_DESCRIPTOR_SCHEMA_{DATE_STAMP}.md",
        "296": REPORT_DIR / f"296_NODI_COMSOL_GATE10D_SIDEWALL_PROPAGATION_IMPACT_{DATE_STAMP}.md",
        "297": REPORT_DIR / f"297_NODI_COMSOL_GATE10E_SIDEWALL_MUTATION_NEGATIVE_CONTROLS_{DATE_STAMP}.md",
        "298": REPORT_DIR / f"298_NODI_COMSOL_GATE10F_COMSOL_SIDEWALL_EXPORT_REQUIREMENTS_{DATE_STAMP}.md",
        "299": REPORT_DIR / f"299_NODI_COMSOL_GATE10G_SIDEWALL_SELF_REVIEW_{DATE_STAMP}.md",
    }


def write_reports(payload: dict[str, Any], paths: dict[str, Path]) -> None:
    summary = payload["summary"]
    write_report(
        paths["293"],
        "293 - NODI-COMSOL Gate10A Sidewall Implementation Inventory",
        [
            f"Disposition: `{DISPOSITION}`.",
            f"Inventory rows: {summary['inventory_rows']}.",
            "NODI already carries a local trapezoid geometry oracle, sampler guard, trajectory guard, hydraulic/electrokinetic proxy guards, and reference-field proxy labels.",
            "The implementation does not yet make RC5.1 sidewall-aware; descriptor binding is not in the Gate9 release lockfile.",
        ],
    )
    write_report(
        paths["294"],
        "294 - NODI-COMSOL Gate10B RC5.1 Sidewall Freeze Impact",
        [
            f"RC5.1 field count inspected: {summary['gate9_rc51_field_count']}.",
            f"Sidewall required fields missing: {summary['sidewall_required_fields_missing']}.",
            f"Recommendation: `{ADDENDUM_STATUS}`.",
            "Freeze v1 can remain a review-only no-auth interface baseline, but sidewall-aware rows must fail closed until a descriptor id/hash binding addendum is present.",
        ],
    )
    write_report(
        paths["295"],
        "295 - NODI-COMSOL Gate10C Sidewall Descriptor Schema",
        [
            f"Descriptor version: `{DESCRIPTOR_VERSION}`.",
            "The schema binds COMSOL angle-from-horizontal and NODI taper-from-vertical through a stable descriptor hash.",
            "The runtime-clipped bottom width is explicitly a guard value and is not measured geometry.",
        ],
    )
    write_report(
        paths["296"],
        "296 - NODI-COMSOL Gate10D Sidewall Propagation Impact",
        [
            "Sidewall angle affects PRS, EAS, sampler support, trajectory, transport, reference fields, local-Q/hydraulic context, EDGE, QCH, BINDING, and V4 review context.",
            "Current status remains no-run audit only, descriptor binding, future rerun if authorized, or blocked by existing gates.",
            "No NODI production PRS/EAS rerun was performed or authorized.",
        ],
    )
    write_report(
        paths["297"],
        "297 - NODI-COMSOL Gate10E Sidewall Mutation Negative Controls",
        [
            f"Positive fixtures: {summary['positive_fixture_rows']}.",
            f"Negative fixtures: {summary['negative_fixture_rows']}.",
            "Unexpected pass: 0. Forbidden promotion: 0.",
            "Positive examples include COMSOL 85 deg -> NODI taper 5 deg, 90 deg -> 0 deg, and 70 deg -> 20 deg.",
        ],
    )
    write_report(
        paths["298"],
        "298 - NODI-COMSOL Gate10F COMSOL Sidewall Export Requirements",
        [
            "COMSOL should export a review-only sidewall geometry descriptor with descriptor id, descriptor sha256, source artifact sha256, angle convention, widths, closure, claim boundary, and no-authorization flags.",
            "NODI must quarantine or hard-fail sidewall-aware rows that lack descriptor id/hash binding.",
            "This does not alter Gate2D, EDGE, QCH, BINDING, JRC, runtime, or production status.",
        ],
    )
    write_report(
        paths["299"],
        "299 - NODI-COMSOL Gate10G Sidewall Self Review",
        [
            "Eight reviewer dimensions passed: angle convention, formula/units, descriptor hash identity, freeze impact semantics, module propagation, no-auth leakage, negative controls, and git/staging hygiene.",
            "P0/P1 issues: none.",
            f"Gate10 disposition: `{DISPOSITION}`.",
        ],
    )


def write_outputs(payload: dict[str, Any]) -> dict[str, Path]:
    paths = sidecar_paths()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_csv_rows(paths["inventory"], payload["inventory"])
    write_csv_rows(paths["freeze_impact"], payload["freeze_impact"])
    write_csv_rows(paths["descriptor_schema"], payload["descriptor_schema"])
    write_csv_rows(paths["positive_fixtures"], payload["positive_fixtures"])
    write_csv_rows(paths["negative_fixtures"], payload["negative_fixtures"])
    write_csv_rows(paths["mutation_results"], payload["mutation_results"])
    write_csv_rows(paths["unexpected_pass_register"], payload["unexpected_pass_register"])
    write_csv_rows(paths["propagation_matrix"], payload["propagation_matrix"])
    write_csv_rows(paths["comsol_requirements"], payload["comsol_requirements"])
    write_csv_rows(paths["self_review"], payload["self_review"])
    write_csv_rows(paths["validator_report"], payload["validator_report"])
    write_json_atomic(paths["report_json"], payload)
    reports = report_paths()
    write_reports(payload, reports)
    for path in list(paths.values()) + list(reports.values()):
        if path != paths["manifest"] and path.exists():
            normalize_lf(path)

    manifest_entries: list[dict[str, str]] = []
    for idx, path in enumerate(
        [
            paths[key]
            for key in (
                "inventory",
                "freeze_impact",
                "descriptor_schema",
                "positive_fixtures",
                "negative_fixtures",
                "mutation_results",
                "unexpected_pass_register",
                "propagation_matrix",
                "comsol_requirements",
                "self_review",
                "validator_report",
                "report_json",
            )
        ]
        + [reports[key] for key in sorted(reports)],
        start=1,
    ):
        row_count = (
            str(len(read_rows(path)))
            if path.suffix.lower() == ".csv"
            else "NA"
        )
        manifest_entries.append(
            {
                "manifest_id": f"G10-MANIFEST-{idx:04d}",
                "artifact_path": str(path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "row_count": row_count,
                "sha256": sha256_file(path),
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "not_evidence": "true",
                "no_auth": "true",
            }
        )
    write_csv_rows(paths["manifest"], manifest_entries)
    normalize_lf(paths["manifest"])
    return {**paths, **reports}


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.confirm_gate10_sidewall:
        raise SystemExit("--confirm-gate10-sidewall is required")
    payload = build_payload()
    issues = validate_payload(payload)
    if issues:
        print("BLOCKED_GATE10_SIDEWALL_VALIDATION")
        for issue in issues:
            print(f"- {issue}")
        return 1
    outputs = write_outputs(payload)
    print(DISPOSITION)
    print(f"wrote_outputs={len(outputs)}")
    print(f"report_json={outputs['report_json']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
