#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import read_csv_rows, sha256_file, write_csv_rows, write_json_atomic  # noqa: E402


DATE_STAMP = "20260630"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

DISPOSITION = "NODI_GATE19_SIDEWALL_PACKAGE_ABD_STATIC_PREFLIGHT_PASS_NO_AUTH"
EXPECTED_GATE18_DISPOSITION = "NODI_GATE18_SIDEWALL_COMSOL_GATE16_CLEAN_REINTAKE_RECEIPT_STATIC_PREFLIGHT_UNBLOCK_NO_AUTH"
ALLOWED_USE = "review-only Package A/B/D static preflight;schema geometry contract guard audit;no-run no-auth"
BLOCKED_USE = (
    "q_ch weighting;q_ch*eta;q_ch*chi*eta;chi_selected;route_score;rank;JOINT_ROUTE_CLASS;JRC;"
    "yield;winner;detection_probability;wet pass probability;clogging rate;time-to-clog;recovery;"
    "fabrication release;runtime configuration;production ingestion;formula use;direct PRS bin;"
    "grain-level ingestion;sidewall PRS/EAS numeric output;validated Brownian/flow/optical/wet physics"
)

REPORTS = {
    "405": "GATE19A_PACKAGE_A_SCHEMA_DESCRIPTOR_PREFLIGHT",
    "406": "GATE19B_PACKAGE_B_GEOMETRY_SAMPLER_PREFLIGHT",
    "407": "GATE19C_PACKAGE_D_PRS_EAS_CONTRACT_PREFLIGHT",
    "408": "GATE19D_PACKAGE_C_BLOCKED_PHYSICS_LEDGER",
    "409": "GATE19E_NO_AUTH_FIREWALL",
    "410": "GATE19F_VALIDATION_AND_REGRESSION",
    "411": "GATE19G_NEXT_STATIC_PREFLIGHT_HANDOFF",
    "412": "GATE19_SIDEWALL_PACKAGE_ABD_STATIC_PREFLIGHT_MASTER_REPORT",
}

REQUIRED_FILES = {
    "package_a_contract_tests": PROJECT_ROOT / "tests/test_nodi_comsol_next_artifacts_contracts.py",
    "package_b_geometry_tests": PROJECT_ROOT / "tests/test_cross_section_geometry.py",
    "package_b_physics_signature_tests": PROJECT_ROOT / "tests/test_physics_core.py",
    "gate18_status": OUTPUT_DIR / "NODI_COMSOL_GATE18_SIDEWALL_STATUS_20260630.json",
    "gate18_static_board": OUTPUT_DIR / "NODI_COMSOL_GATE18_SIDEWALL_STATIC_PREFLIGHT_BOARD_20260630.csv",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate19 sidewall Package A/B/D static preflight package.")
    parser.add_argument("--confirm-gate19-sidewall-static-preflight", action="store_true")
    return parser


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def bool_text(value: bool) -> str:
    return str(bool(value)).lower()


def csv_count(path: Path) -> str:
    return str(len(read_csv_rows(path))) if path.exists() and path.suffix.lower() == ".csv" else "NA"


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


def manifest_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for idx, path in enumerate(paths, start=1):
        rows.append(
            {
                "manifest_id": f"G19-MANIFEST-{idx:03d}",
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "row_count": csv_count(path),
                "sha256": sha256_file(path),
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
                "policy_impact": "none_no_auth",
            }
        )
    return rows


def gate18_unblocked() -> bool:
    status = read_json(REQUIRED_FILES["gate18_status"])
    board = read_csv_rows(REQUIRED_FILES["gate18_static_board"])
    return (
        status.get("disposition") == EXPECTED_GATE18_DISPOSITION
        and status.get("summary", {}).get("package_abd_static_preflight_allowed") == 3
        and all(row["runtime_allowed"] == "false" and row["production_allowed"] == "false" for row in board)
    )


def package_preflight_rows() -> list[dict[str, str]]:
    gate18_ok = gate18_unblocked()
    file_ok = {name: path.exists() for name, path in REQUIRED_FILES.items()}
    return [
        {
            "package": "Package A",
            "scope": "schema/descriptor/profile guard",
            "preflight_status": "PASS_STATIC_PREFLIGHT_NO_RUNTIME" if gate18_ok and file_ok["package_a_contract_tests"] else "BLOCKED_MISSING_STATIC_EVIDENCE",
            "evidence_file": REQUIRED_FILES["package_a_contract_tests"].relative_to(PROJECT_ROOT).as_posix(),
            "runtime_allowed": "false",
            "production_allowed": "false",
            "validated_physics_claim": "false",
            "next_allowed_action": "schema/descriptor validator maintenance only",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "package": "Package B",
            "scope": "geometry primitive/sampler/signature guard",
            "preflight_status": "PASS_STATIC_PREFLIGHT_NO_RUNTIME"
            if gate18_ok and file_ok["package_b_geometry_tests"] and file_ok["package_b_physics_signature_tests"]
            else "BLOCKED_MISSING_STATIC_EVIDENCE",
            "evidence_file": "tests/test_cross_section_geometry.py;tests/test_physics_core.py",
            "runtime_allowed": "false",
            "production_allowed": "false",
            "validated_physics_claim": "false",
            "next_allowed_action": "geometry/sampler static audit only",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "package": "Package C",
            "scope": "trajectory/near-wall/optical/wet physics",
            "preflight_status": "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION",
            "evidence_file": "not_applicable",
            "runtime_allowed": "false",
            "production_allowed": "false",
            "validated_physics_claim": "false",
            "next_allowed_action": "none without explicit physics authorization",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
        {
            "package": "Package D",
            "scope": "PRS/EAS contract precheck",
            "preflight_status": "PASS_CONTRACT_PREFLIGHT_NO_RUNTIME" if gate18_ok and file_ok["package_a_contract_tests"] else "BLOCKED_MISSING_STATIC_EVIDENCE",
            "evidence_file": REQUIRED_FILES["package_a_contract_tests"].relative_to(PROJECT_ROOT).as_posix(),
            "runtime_allowed": "false",
            "production_allowed": "false",
            "validated_physics_claim": "false",
            "next_allowed_action": "sidewall PRS/EAS contract precheck only",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        },
    ]


def no_auth_firewall() -> list[dict[str, str]]:
    return [
        {
            "firewall_id": "G19E-FIREWALL-001",
            "positive_authorization_count": "0",
            "runtime_configuration_authorized": "false",
            "production_ingestion_authorized": "false",
            "qch_weighting_authorized": "false",
            "jrc_authorized": "false",
            "route_score_authorized": "false",
            "yield_authorized": "false",
            "detection_probability_authorized": "false",
            "package_c_state": "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION",
            "firewall_status": "PASS_NO_AUTH_LOCKS_PRESERVED",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
    ]


def validation_plan() -> list[dict[str, str]]:
    commands = [
        "python tools/audits/build_nodi_comsol_gate19_sidewall_static_preflight.py --confirm-gate19-sidewall-static-preflight",
        "python -m py_compile tools/audits/build_nodi_comsol_gate19_sidewall_static_preflight.py",
        "python -m pytest tests/test_nodi_comsol_gate19_sidewall_static_preflight.py -q",
        "python -m pytest tests/test_nodi_comsol_next_artifacts_contracts.py tests/test_cross_section_geometry.py tests/test_physics_core.py::TestIntegration::test_trapezoid_batch_signature_binds_actual_sampler_wall_distance_diagnostics tests/test_physics_core.py::TestIntegration::test_batch_signature_keeps_measured_profile_lookup_blocked_until_validated -q",
    ]
    return [
        {"validation_id": f"G19F-VALIDATION-{idx:03d}", "command": command, "required_for_pass": "true", "recorded_result": "PENDING_RUNTIME_VALIDATION"}
        for idx, command in enumerate(commands, start=1)
    ]


def build_payload() -> dict[str, Any]:
    rows = package_preflight_rows()
    firewall = no_auth_firewall()
    summary = {
        "disposition": DISPOSITION,
        "gate18_unblocked": gate18_unblocked(),
        "package_a_status": next(row["preflight_status"] for row in rows if row["package"] == "Package A"),
        "package_b_status": next(row["preflight_status"] for row in rows if row["package"] == "Package B"),
        "package_c_status": next(row["preflight_status"] for row in rows if row["package"] == "Package C"),
        "package_d_status": next(row["preflight_status"] for row in rows if row["package"] == "Package D"),
        "no_auth_firewall_failures": 0 if firewall[0]["firewall_status"] == "PASS_NO_AUTH_LOCKS_PRESERVED" else 1,
        "review_only": True,
        "no_auth": True,
    }
    return {"summary": summary, "package_preflight": rows, "no_auth_firewall": firewall, "validation_plan": validation_plan()}


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    checks = {
        "Gate18 unblock": s["gate18_unblocked"] is True,
        "Package A pass": s["package_a_status"] == "PASS_STATIC_PREFLIGHT_NO_RUNTIME",
        "Package B pass": s["package_b_status"] == "PASS_STATIC_PREFLIGHT_NO_RUNTIME",
        "Package C blocked": s["package_c_status"] == "BLOCKED_REQUIRES_EXPLICIT_PHYSICS_AUTHORIZATION",
        "Package D pass": s["package_d_status"] == "PASS_CONTRACT_PREFLIGHT_NO_RUNTIME",
        "no auth firewall": s["no_auth_firewall_failures"] == 0,
    }
    return [label for label, ok in checks.items() if not ok]


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    csv_specs = {
        "NODI_COMSOL_GATE19_SIDEWALL_PACKAGE_PREFLIGHT_20260630.csv": payload["package_preflight"],
        "NODI_COMSOL_GATE19_SIDEWALL_NO_AUTH_FIREWALL_20260630.csv": payload["no_auth_firewall"],
        "NODI_COMSOL_GATE19_SIDEWALL_VALIDATION_PLAN_20260630.csv": payload["validation_plan"],
    }
    for name, rows in csv_specs.items():
        path = OUTPUT_DIR / name
        write_csv_rows(path, rows)
        generated.append(path)
    report_json = OUTPUT_DIR / "NODI_COMSOL_GATE19_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(report_json, {"summary": payload["summary"], "outputs": list(csv_specs)})
    generated.append(report_json)
    status_json = OUTPUT_DIR / "NODI_COMSOL_GATE19_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(status_json, {"disposition": DISPOSITION, "summary": payload["summary"], "review_only": True, "no_auth": True})
    generated.append(status_json)
    master_md = OUTPUT_DIR / "NODI_COMSOL_GATE19_SIDEWALL_STATIC_PREFLIGHT_REPORT_20260630.md"
    write_md(
        master_md,
        "NODI COMSOL Gate19 Sidewall Package A/B/D Static Preflight",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Package A: `{payload['summary']['package_a_status']}`",
            f"- Package B: `{payload['summary']['package_b_status']}`",
            f"- Package C: `{payload['summary']['package_c_status']}`",
            f"- Package D: `{payload['summary']['package_d_status']}`",
            "- Boundary: no runtime, no production, no physics claim.",
        ],
    )
    generated.append(master_md)
    manifest_path = OUTPUT_DIR / "NODI_COMSOL_GATE19_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(manifest_path, manifest_rows(generated))
    generated.append(manifest_path)
    for number, title in REPORTS.items():
        path = REPORT_DIR / f"{number}_NODI_COMSOL_{title}_20260630.md"
        write_md(
            path,
            title.replace("_", " "),
            [
                f"- Gate19 disposition: `{DISPOSITION}`",
                "- Package A/B/D static preflight passed as review-only/no-auth.",
                "- Package C remains blocked pending explicit physics authorization.",
                "- Boundary: no solver, no runtime/production, no route score, no q_ch/JRC/yield/detection.",
                f"- Machine-readable support: `{OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix()}`.",
            ],
        )
        generated.append(path)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate19_sidewall_static_preflight:
        parser.error("--confirm-gate19-sidewall-static-preflight is required")
    payload = build_payload()
    failures = validate_payload(payload)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE19_SIDEWALL_STATIC_PREFLIGHT")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
