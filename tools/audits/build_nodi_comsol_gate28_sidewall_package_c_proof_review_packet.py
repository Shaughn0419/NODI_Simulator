#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nodi_simulator.realism_v2_io import (  # noqa: E402
    read_csv_rows,
    sha256_file,
    write_csv_rows,
    write_json_atomic,
)
from tools.audits.build_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight import (  # noqa: E402
    REQUIRED_PROOF_CONTRACT_FIELDS as GATE27_REQUIRED_PROOF_CONTRACT_FIELDS,
)


DATE_STAMP = "20260630"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"

EXPECTED_GATE27_DISPOSITION = (
    "NODI_GATE27_SIDEWALL_PACKAGE_C_IMPLEMENTATION_DESIGN_PREFLIGHT_READY_NO_AUTH"
)
DISPOSITION = (
    "NODI_GATE28_SIDEWALL_PACKAGE_C_PROOF_REVIEW_PACKET_READY_NO_PROOF_REGISTRATION"
)
ALLOWED_USE = (
    "external review packet;unit-test evidence ledger;proof-readiness review input;"
    "no-proof-registration no-runtime no-numeric-output"
)
BLOCKED_USE = (
    "Package C proof/pass registration;runtime configuration;sidewall PRS/EAS numeric output;"
    "NODI runtime recomputation;COMSOL launch;.mph load;validated hindered diffusion;"
    "trapezoid Poiseuille solver output;fixed-pressure q_ch output;flux-weighted sampling;"
    "electrokinetic grid output;optical solver output;true W_eff;route_score;winner;JRC;"
    "q_ch weighting;yield;detection_probability;wet pass probability;clogging rate;"
    "time-to-clog;recovery;fabrication release;production ingestion"
)

GATE27_STATUS = OUTPUT_DIR / "NODI_COMSOL_GATE27_SIDEWALL_STATUS_20260630.json"
GATE27_REPORT = OUTPUT_DIR / "NODI_COMSOL_GATE27_SIDEWALL_REPORT_20260630.json"
GATE27_PROOF_CONTRACT = (
    OUTPUT_DIR / "NODI_COMSOL_GATE27_SIDEWALL_PROOF_ARTIFACT_CONTRACT_20260630.csv"
)

SOURCE_FILES = {
    "cross_section_geometry": PROJECT_ROOT / "nodi_simulator/cross_section_geometry.py",
    "trajectory": PROJECT_ROOT / "nodi_simulator/trajectory.py",
    "next_artifacts_contract": PROJECT_ROOT / "nodi_simulator/nodi_comsol_next_artifacts.py",
    "gate27_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight.py",
    "gate28_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_gate28_sidewall_package_c_proof_review_packet.py",
    "cross_section_tests": PROJECT_ROOT / "tests/test_cross_section_geometry.py",
    "trajectory_tests": PROJECT_ROOT / "tests/test_trajectory.py",
    "next_artifacts_tests": PROJECT_ROOT / "tests/test_nodi_comsol_next_artifacts_contracts.py",
    "gate27_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight.py",
    "gate28_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_gate28_sidewall_package_c_proof_review_packet.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
    "gate27_status": GATE27_STATUS,
    "gate27_report": GATE27_REPORT,
    "gate27_proof_contract": GATE27_PROOF_CONTRACT,
}
GATE28_GITHUB_VISIBLE_REVIEW_FILES = tuple(
    Path(path)
    for path in (
        "reports/joint_interface_20260630/NODI_COMSOL_GATE28_SIDEWALL_EXTERNAL_REVIEW_PROMPT_20260630.md",
        "reports/joint_interface_20260630/NODI_COMSOL_GATE28_SIDEWALL_MANIFEST_20260630.csv",
        "reports/joint_interface_20260630/NODI_COMSOL_GATE28_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv",
        "reports/joint_interface_20260630/NODI_COMSOL_GATE28_SIDEWALL_PROOF_REVIEW_PACKET_REPORT_20260630.md",
        "reports/joint_interface_20260630/NODI_COMSOL_GATE28_SIDEWALL_REPORT_20260630.json",
        "reports/joint_interface_20260630/NODI_COMSOL_GATE28_SIDEWALL_SOURCE_LOCK_20260630.csv",
        "reports/joint_interface_20260630/NODI_COMSOL_GATE28_SIDEWALL_STATUS_20260630.json",
        "reports/joint_interface_20260630/NODI_COMSOL_GATE28_SIDEWALL_TEST_EVIDENCE_20260630.json",
        "reports/joint_interface_20260630/NODI_COMSOL_GATE28_SIDEWALL_TEST_EVIDENCE_SUMMARY_20260630.csv",
    )
)

EVIDENCE_COMMANDS: tuple[dict[str, Any], ...] = (
    {
        "evidence_id": "G28-EVIDENCE-001",
        "purpose": "compile Package C geometry/trajectory/schema/builders",
        "argv": [
            sys.executable,
            "-m",
            "py_compile",
            "nodi_simulator/cross_section_geometry.py",
            "nodi_simulator/trajectory.py",
            "nodi_simulator/nodi_comsol_next_artifacts.py",
            "tools/audits/build_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight.py",
            "tools/audits/build_nodi_comsol_gate28_sidewall_package_c_proof_review_packet.py",
        ],
    },
    {
        "evidence_id": "G28-EVIDENCE-002",
        "purpose": "run sidewall geometry and trajectory Package C unit tests",
        "argv": [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_cross_section_geometry.py",
            "tests/test_trajectory.py",
            "-q",
        ],
    },
    {
        "evidence_id": "G28-EVIDENCE-003",
        "purpose": "run sidewall artifact and Package C proof-scaffold contract tests",
        "argv": [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_nodi_comsol_next_artifacts_contracts.py",
            "-q",
            "-k",
            "package_c_proof_scaffold or sidewall or production_candidate_validator",
        ],
    },
    {
        "evidence_id": "G28-EVIDENCE-004",
        "purpose": "run Gate27 proof-contract builder tests",
        "argv": [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_nodi_comsol_gate27_sidewall_package_c_implementation_design_preflight.py",
            "-q",
        ],
    },
    {
        "evidence_id": "G28-EVIDENCE-005",
        "purpose": "run Gate28 review-packet builder tests",
        "argv": [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_nodi_comsol_gate28_sidewall_package_c_proof_review_packet.py",
            "-q",
        ],
    },
    {
        "evidence_id": "G28-EVIDENCE-006",
        "purpose": "check staged/unstaged diff whitespace only",
        "argv": ["git", "diff", "--check"],
    },
)

REPORTS = {
    "471": "GATE28A_PACKAGE_C_TEST_EVIDENCE_PACKET",
    "472": "GATE28B_PACKAGE_C_EXTERNAL_REVIEW_PROMPT",
    "473": "GATE28C_PACKAGE_C_NO_PROOF_FIREWALL",
    "474": "GATE28_SIDEWALL_PACKAGE_C_PROOF_REVIEW_MASTER_REPORT",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Gate28 Package C proof review packet.")
    parser.add_argument("--confirm-gate28-package-c-proof-review-packet", action="store_true")
    return parser


def run_git(args: list[str], cwd: Path = PROJECT_ROOT) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={cwd.as_posix()}", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.strip()


def safe_git_head(path: Path = PROJECT_ROOT) -> str:
    try:
        return run_git(["rev-parse", "HEAD"], cwd=path)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNKNOWN_COMMIT_READONLY_REFERENCE"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def bool_text(value: bool) -> str:
    return str(bool(value)).lower()


def csv_count(path: Path) -> int:
    return len(read_csv_rows(path)) if path.exists() and path.suffix.lower() == ".csv" else 0


def gate27_proof_contract_fields() -> set[str]:
    if not GATE27_PROOF_CONTRACT.exists():
        return set()
    return {
        row.get("required_field", "")
        for row in read_csv_rows(GATE27_PROOF_CONTRACT)
        if row.get("required_field")
    }


def write_md(path: Path, title: str, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join([f"# {title}", "", *lines]) + "\n", encoding="utf-8")


def source_lock_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for label, path in SOURCE_FILES.items():
        exists = path.exists()
        rows.append(
            {
                "source_label": label,
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "exists": bool_text(exists),
                "sha256": sha256_file(path) if exists else "",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def run_evidence_command(spec: dict[str, Any], execute_tests: bool) -> dict[str, Any]:
    if not execute_tests:
        return {
            "evidence_id": spec["evidence_id"],
            "purpose": spec["purpose"],
            "argv": spec["argv"],
            "returncode": None,
            "duration_s": 0.0,
            "status": "not_executed_builder_unit_test",
            "stdout": "",
            "stderr": "",
        }
    start = time.perf_counter()
    result = subprocess.run(
        spec["argv"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return {
        "evidence_id": spec["evidence_id"],
        "purpose": spec["purpose"],
        "argv": spec["argv"],
        "returncode": result.returncode,
        "duration_s": round(time.perf_counter() - start, 3),
        "status": "pass" if result.returncode == 0 else "fail",
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def evidence_summary_rows(evidence: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in evidence:
        rows.append(
            {
                "evidence_id": str(row["evidence_id"]),
                "purpose": str(row["purpose"]),
                "status": str(row["status"]),
                "returncode": "" if row["returncode"] is None else str(row["returncode"]),
                "duration_s": str(row["duration_s"]),
                "argv": " ".join(str(part) for part in row["argv"]),
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def no_proof_firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_status": "PASS_GATE28_REVIEW_PACKET_NO_PROOF_REGISTRATION",
            "package_c_proof_artifact_registered": "false",
            "package_c_validation_status_pass_authorized": "false",
            "proof_registry_update_authorized": "false",
            "runtime_configuration_authorized": "false",
            "sidewall_prs_eas_numeric_output_authorized": "false",
            "nodi_runtime_recomputation_authorized": "false",
            "comsol_launch_authorized": "false",
            "mph_load_authorized": "false",
            "hindered_diffusion_claim_authorized": "false",
            "trapezoid_flow_solver_claim_authorized": "false",
            "electrokinetic_solver_claim_authorized": "false",
            "optical_solver_claim_authorized": "false",
            "route_score_authorized": "false",
            "winner_authorized": "false",
            "yield_authorized": "false",
            "detection_probability_authorized": "false",
        }
    ]


def build_payload(execute_tests: bool = True) -> dict[str, Any]:
    gate27_status = read_json(GATE27_STATUS)
    gate27_summary = gate27_status.get("summary", {})
    gate27_contract_fields = gate27_proof_contract_fields()
    source_rows = source_lock_rows()
    evidence = [run_evidence_command(spec, execute_tests) for spec in EVIDENCE_COMMANDS]
    firewall = no_proof_firewall_rows()
    evidence_pass_rows = sum(row["status"] == "pass" for row in evidence)
    evidence_fail_rows = sum(row["status"] == "fail" for row in evidence)
    summary = {
        "disposition": DISPOSITION,
        "gate28_build_head": safe_git_head(),
        "gate27_disposition": gate27_status.get("disposition", ""),
        "gate27_no_auth": gate27_status.get("no_auth") is True,
        "gate27_review_only": gate27_status.get("review_only") is True,
        "gate27_proof_contract_rows": gate27_summary.get("proof_contract_rows", 0),
        "gate27_proof_contract_required_field_rows": len(
            GATE27_REQUIRED_PROOF_CONTRACT_FIELDS
        ),
        "gate27_proof_contract_field_rows": len(gate27_contract_fields),
        "gate27_proof_contract_missing_required_fields": sorted(
            GATE27_REQUIRED_PROOF_CONTRACT_FIELDS - gate27_contract_fields
        ),
        "gate27_proof_contract_extra_fields": sorted(
            gate27_contract_fields - GATE27_REQUIRED_PROOF_CONTRACT_FIELDS
        ),
        "gate27_proof_artifact_registered_rows": gate27_summary.get(
            "proof_artifact_registered_rows", -1
        ),
        "gate27_can_update_proof_registry_rows": gate27_summary.get(
            "can_update_proof_registry_rows", -1
        ),
        "source_lock_rows": len(source_rows),
        "source_missing_rows": sum(row["exists"] != "true" for row in source_rows),
        "evidence_command_rows": len(evidence),
        "evidence_pass_rows": evidence_pass_rows,
        "evidence_fail_rows": evidence_fail_rows,
        "evidence_not_executed_rows": sum(
            row["status"] == "not_executed_builder_unit_test" for row in evidence
        ),
        "no_auth_firewall_failures": 0
        if firewall[0]["firewall_status"] == "PASS_GATE28_REVIEW_PACKET_NO_PROOF_REGISTRATION"
        else 1,
        "review_only": True,
        "no_auth": True,
        "proof_registration_authorized": False,
        "runtime_allowed": False,
        "numeric_prs_eas_allowed": False,
        "comsol_launch_allowed": False,
        "mph_load_allowed": False,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    return {
        "summary": summary,
        "source_locks": source_rows,
        "test_evidence": evidence,
        "test_evidence_summary": evidence_summary_rows(evidence),
        "no_proof_firewall": firewall,
        "gate27_proof_contract_fields": sorted(gate27_contract_fields),
        "gate27_required_proof_contract_fields": sorted(
            GATE27_REQUIRED_PROOF_CONTRACT_FIELDS
        ),
    }


def validate_payload(payload: dict[str, Any], require_evidence_pass: bool = True) -> list[str]:
    s = payload["summary"]
    firewall = payload["no_proof_firewall"][0]
    checks = {
        "Gate27 disposition": s["gate27_disposition"] == EXPECTED_GATE27_DISPOSITION,
        "Gate27 no-auth": s["gate27_no_auth"] is True,
        "Gate27 review-only": s["gate27_review_only"] is True,
        "Gate27 required-field proof contract": s["gate27_proof_contract_rows"]
        == len(GATE27_REQUIRED_PROOF_CONTRACT_FIELDS),
        "Gate27 proof contract field names complete": not s[
            "gate27_proof_contract_missing_required_fields"
        ],
        "Gate27 proof contract has no unexpected fields": not s[
            "gate27_proof_contract_extra_fields"
        ],
        "Gate27 no proof registered": s["gate27_proof_artifact_registered_rows"] == 0,
        "Gate27 no proof updates": s["gate27_can_update_proof_registry_rows"] == 0,
        "Sources present": s["source_missing_rows"] == 0,
        "No evidence failures": s["evidence_fail_rows"] == 0,
        "No-auth firewall": s["no_auth_firewall_failures"] == 0,
        "Review only": s["review_only"] is True,
        "No auth": s["no_auth"] is True,
        "No proof registration": s["proof_registration_authorized"] is False,
        "No runtime": s["runtime_allowed"] is False,
        "No numeric PRS/EAS": s["numeric_prs_eas_allowed"] is False,
        "No COMSOL launch": s["comsol_launch_allowed"] is False,
        "No mph load": s["mph_load_allowed"] is False,
    }
    if require_evidence_pass:
        checks["All evidence commands executed"] = s["evidence_not_executed_rows"] == 0
        checks["All evidence commands passed"] = (
            s["evidence_pass_rows"] == s["evidence_command_rows"]
        )
    for key, value in firewall.items():
        if key.endswith("_authorized") or key == "package_c_proof_artifact_registered":
            checks[f"No-proof false: {key}"] = value == "false"
    return [label for label, ok in checks.items() if not ok]


def external_review_prompt_text(
    payload: dict[str, Any],
    evidence_sha256: str,
    source_lock_sha256: str,
) -> str:
    s = payload["summary"]
    proof_fields_text = "\n".join(
        f"- `{field}`" for field in payload["gate27_required_proof_contract_fields"]
    )
    return f"""# Gate28 External AI Review Prompt: NODI Package C Sidewall Reflection Proof Evidence

You are reviewing a GitHub-visible NODI sidewall-angle implementation candidate.
You cannot see local files unless they are committed to GitHub, so this prompt is
self-contained and names the exact committed files/artifacts to inspect.

## Verdict requested

Return one of:
- `READY_FOR_EXTERNAL_PROOF_REGISTRATION_REVIEW_ONLY`
- `NEEDS_MORE_TEST_EVIDENCE_BEFORE_PROOF_REGISTRATION`
- `BLOCKED_PHYSICS_OR_CLAIM_BOUNDARY_UNSAFE`

Do not recommend NODI runtime recomputation, COMSOL launch, `.mph` load, PRS/EAS
numeric output, route_score/winner/JRC/q_ch weighting, yield, detection probability,
wet-pass probability, clogging rate, time-to-clog, recovery, fabrication release,
or production ingestion.

## Current Gate28 status

- Disposition: `{DISPOSITION}`.
- Build commit recorded by packet: `{s["gate28_build_head"]}`.
- Gate27 disposition: `{s["gate27_disposition"]}`.
- Gate27 proof contract rows: `{s["gate27_proof_contract_rows"]}`.
- Gate27 proof registry/update rows: `{s["gate27_proof_artifact_registered_rows"]}` / `{s["gate27_can_update_proof_registry_rows"]}`.
- Evidence commands passed: `{s["evidence_pass_rows"]}` of `{s["evidence_command_rows"]}`.
- Test evidence JSON sha256: `{evidence_sha256}`.
- Source lock CSV sha256: `{source_lock_sha256}`.
- Proof registration authorized: `{s["proof_registration_authorized"]}`.
- Runtime / numeric PRS-EAS / COMSOL / `.mph`: `{s["runtime_allowed"]}` / `{s["numeric_prs_eas_allowed"]}` / `{s["comsol_launch_allowed"]}` / `{s["mph_load_allowed"]}`.

## Implementation target and claim boundary

Package C targets Brownian reflected diffusion in a symmetric convex trapezoid
particle-center support domain, not hydrodynamic hindered diffusion or wet
clogging/adhesion physics.

Target model:

```text
brownian_boundary_target_model =
  skorokhod_normal_reflection_convex_offset_trapezoid_v1
```

Particle center domain:

```text
D_a = {{ g_i(x,u) >= 0 for all walls }}
g_i = d_i(x,u) - a
```

Inward unit normals used by the design:

```text
top:    g_top = u - a
        n_top = (0, +1)

bottom: g_bottom = H - a - u
        n_bottom = (0, -1)

left:   g_left = (x + h(u))/sqrt(1+k^2) - a
        n_left = (1, -k)/sqrt(1+k^2)

right:  g_right = (h(u) - x)/sqrt(1+k^2) - a
        n_right = (-1, -k)/sqrt(1+k^2)
```

Current implementation candidate name:

```text
trapezoid_skorokhod_normal_reflection_euler_active_set_v1
```

Current claim level:

```text
finite_step_reflection_surrogate_not_hindered_hydrodynamics_not_package_c_proof_registered
```

This packet still does not register Package C proof/pass. It only packages
review evidence for an external or independent reviewer.

## Files to inspect on GitHub

- `nodi_simulator/cross_section_geometry.py`
- `nodi_simulator/trajectory.py`
- `nodi_simulator/nodi_comsol_next_artifacts.py`
- `tests/test_cross_section_geometry.py`
- `tests/test_trajectory.py`
- `tests/test_nodi_comsol_next_artifacts_contracts.py`
- `reports/joint_interface_20260630/NODI_COMSOL_GATE28_SIDEWALL_TEST_EVIDENCE_20260630.json`
- `reports/joint_interface_20260630/NODI_COMSOL_GATE28_SIDEWALL_SOURCE_LOCK_20260630.csv`
- `reports/joint_interface_20260630/NODI_COMSOL_GATE28_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv`
- `reports/joint_interface_20260630/NODI_COMSOL_GATE27_SIDEWALL_PROOF_ARTIFACT_CONTRACT_20260630.csv`

## Gate27 required-field proof scaffold to review

The Gate27 proof contract currently contains exactly
{len(GATE27_REQUIRED_PROOF_CONTRACT_FIELDS)} required fields. Every field below
must be present before any separate future gate can even consider
`package_C_validation_status=pass`:

{proof_fields_text}

## Review questions

1. Does the finite-step active-set normal reflection candidate remain correctly
   labeled as a Brownian reflecting-boundary surrogate, not ballistic specular
   reflection and not hydrodynamic hindered diffusion?
2. Are the current tests sufficient as proof-registration evidence for the
   implemented claim level, especially support invariance, no boundary atom,
   corner active-set convergence, accessible-area equilibrium moments,
   u-slice local-width uniformity/symmetry, dt-halving one-wall convergence,
   angle/depth mutation, and rectangle limit?
3. Are the 28 proof scaffold fields sufficient before any future
   `package_C_validation_status=pass` row is allowed?
4. Are any claims still over-promoted, especially hindered diffusion,
   trapezoid flow solver, electrokinetic solver, optical/reference solver,
   PRS/EAS numeric output, route/yield/detection, wet pass, clogging, or
   production/fabrication release?
5. What exact additional tests or schema fields would you require before a
   separate future authorization could register a Package C proof artifact?
"""


def manifest_rows(paths: list[Path]) -> list[dict[str, str]]:
    rows = []
    for path in paths:
        rows.append(
            {
                "artifact": path.name,
                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                "sha256": sha256_file(path) if path.exists() else "",
                "disposition": DISPOSITION,
                "policy_impact": "none_no_proof_registration",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def write_outputs(payload: dict[str, Any]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    source_lock_path = OUTPUT_DIR / "NODI_COMSOL_GATE28_SIDEWALL_SOURCE_LOCK_20260630.csv"
    write_csv_rows(source_lock_path, payload["source_locks"])
    generated.append(source_lock_path)

    evidence_path = OUTPUT_DIR / "NODI_COMSOL_GATE28_SIDEWALL_TEST_EVIDENCE_20260630.json"
    write_json_atomic(evidence_path, payload["test_evidence"])
    generated.append(evidence_path)

    evidence_summary_path = (
        OUTPUT_DIR / "NODI_COMSOL_GATE28_SIDEWALL_TEST_EVIDENCE_SUMMARY_20260630.csv"
    )
    write_csv_rows(evidence_summary_path, payload["test_evidence_summary"])
    generated.append(evidence_summary_path)

    firewall_path = OUTPUT_DIR / "NODI_COMSOL_GATE28_SIDEWALL_NO_PROOF_FIREWALL_20260630.csv"
    write_csv_rows(firewall_path, payload["no_proof_firewall"])
    generated.append(firewall_path)

    prompt_path = OUTPUT_DIR / "NODI_COMSOL_GATE28_SIDEWALL_EXTERNAL_REVIEW_PROMPT_20260630.md"
    prompt = external_review_prompt_text(
        payload,
        evidence_sha256=sha256_file(evidence_path),
        source_lock_sha256=sha256_file(source_lock_path),
    )
    prompt_path.write_text(prompt, encoding="utf-8")
    generated.append(prompt_path)

    report_json = OUTPUT_DIR / "NODI_COMSOL_GATE28_SIDEWALL_REPORT_20260630.json"
    write_json_atomic(
        report_json,
        {
            "summary": payload["summary"],
            "evidence_sha256": sha256_file(evidence_path),
            "source_lock_sha256": sha256_file(source_lock_path),
            "prompt_sha256": sha256_file(prompt_path),
        },
    )
    generated.append(report_json)

    status_json = OUTPUT_DIR / "NODI_COMSOL_GATE28_SIDEWALL_STATUS_20260630.json"
    write_json_atomic(
        status_json,
        {
            "disposition": DISPOSITION,
            "summary": payload["summary"],
            "review_only": True,
            "no_auth": True,
            "proof_registration_authorized": False,
        },
    )
    generated.append(status_json)

    master_md = OUTPUT_DIR / "NODI_COMSOL_GATE28_SIDEWALL_PROOF_REVIEW_PACKET_REPORT_20260630.md"
    write_md(
        master_md,
        "NODI COMSOL Gate28 Sidewall Package C Proof Review Packet",
        [
            f"- Disposition: `{DISPOSITION}`",
            f"- Evidence commands passed: {payload['summary']['evidence_pass_rows']}/{payload['summary']['evidence_command_rows']}.",
            f"- Gate27 proof contract rows: {payload['summary']['gate27_proof_contract_rows']}.",
            "- Boundary: no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no PRS/EAS numeric output, no route/yield/detection claims.",
            f"- External review prompt: `{prompt_path.relative_to(PROJECT_ROOT).as_posix()}`.",
        ],
    )
    generated.append(master_md)

    manifest_path = OUTPUT_DIR / "NODI_COMSOL_GATE28_SIDEWALL_MANIFEST_20260630.csv"
    write_csv_rows(manifest_path, manifest_rows(generated))
    generated.append(manifest_path)

    for number, title in REPORTS.items():
        path = REPORT_DIR / f"{number}_NODI_COMSOL_{title}_20260630.md"
        write_md(
            path,
            title.replace("_", " "),
            [
                f"- Gate28 disposition: `{DISPOSITION}`",
                f"- Evidence commands passed: {payload['summary']['evidence_pass_rows']}/{payload['summary']['evidence_command_rows']}.",
                f"- Gate27 proof contract rows: {payload['summary']['gate27_proof_contract_rows']}.",
                "- Boundary: no proof/pass registration, no runtime, no COMSOL launch, no .mph load, no PRS/EAS numeric output, no route/yield/detection claims.",
                f"- Machine-readable support: `{OUTPUT_DIR.relative_to(PROJECT_ROOT).as_posix()}`.",
            ],
        )
        generated.append(path)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_gate28_package_c_proof_review_packet:
        parser.error("--confirm-gate28-package-c-proof-review-packet is required")
    payload = build_payload(execute_tests=True)
    failures = validate_payload(payload, require_evidence_pass=True)
    write_outputs(payload)
    if failures:
        print("BLOCKED_GATE28_SIDEWALL_PACKAGE_C_PROOF_REVIEW_PACKET")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
