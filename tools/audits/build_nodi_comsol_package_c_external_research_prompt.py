#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
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


DATE_STAMP = "20260701"
OUTPUT_DIR = PROJECT_ROOT / f"reports/joint_interface_{DATE_STAMP}"
REPORT_DIR = PROJECT_ROOT / "reports"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/Shaughn0419/NODI_Simulator/main"
GITHUB_BLOB_BASE = "https://github.com/Shaughn0419/NODI_Simulator/blob/main"
EXPECTED_CONTEXT_ROWS = 7

DISPOSITION = "NODI_PACKAGE_C_EXTERNAL_RESEARCH_PROMPT_READY_NO_PROOF_REGISTRATION"
ARTIFACT_ID = "PACKAGE_C_EXTERNAL_RESEARCH_PROMPT_20260701"
CLAIM_BOUNDARY = "external_research_prompt_not_package_c_proof_registered_not_runtime"
SELF_MANIFEST_SHA256 = "SELF_MANIFEST_NOT_SELF_HASHED_BY_DESIGN"
GITHUB_VISIBILITY_STATUS = "local_worktree_pre_commit_urls_valid_after_publish"

ALLOWED_USE = (
    "External AI broad method/literature research prompt;Package C proof-gap context;"
    "no-proof-registration"
)
BLOCKED_USE = (
    "Package C proof/pass registration;package_C_validation_status pass;runtime configuration;"
    "sidewall PRS/EAS numeric output;NODI runtime recomputation;COMSOL launch;.mph load;"
    "validated Brownian solver output;validated hindered diffusion;trapezoid Poiseuille solver output;"
    "fixed-pressure q_ch output;flux-weighted sampling;electrokinetic grid output;optical solver output;"
    "true W_eff;reference strength claim;detector response claim;sidewall scattering claim;"
    "route_score;winner;JRC;q_ch weighting;yield;detection_probability;wet pass probability;"
    "clogging rate;time-to-clog;recovery;fabrication release;production ingestion"
)

READINESS_STATUS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_STATUS_20260701.json"
)
READINESS_INDEX = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_INDEX_20260701.csv"
)
READINESS_BLOCKERS = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_BLOCKERS_20260701.csv"
)
READINESS_QUESTIONS = (
    OUTPUT_DIR
    / "NODI_COMSOL_PACKAGE_C_PROOF_READINESS_EXTERNAL_RESEARCH_QUESTIONS_20260701.csv"
)
THRESHOLD_TABLE = (
    OUTPUT_DIR / "NODI_COMSOL_PACKAGE_C_PROOF_THRESHOLD_TABLE_20260701.csv"
)

SOURCE_FILES = {
    "proof_readiness_status": READINESS_STATUS,
    "proof_readiness_index": READINESS_INDEX,
    "proof_readiness_blockers": READINESS_BLOCKERS,
    "proof_readiness_external_research_questions": READINESS_QUESTIONS,
    "proof_threshold_table": THRESHOLD_TABLE,
    "external_research_prompt_builder": PROJECT_ROOT
    / "tools/audits/build_nodi_comsol_package_c_external_research_prompt.py",
    "external_research_prompt_tests": PROJECT_ROOT
    / "tests/test_nodi_comsol_package_c_external_research_prompt.py",
    "roadmap": REPORT_DIR / "100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md",
    "audit_packet": REPORT_DIR / "345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a self-contained external AI research prompt for Package C."
    )
    parser.add_argument(
        "--confirm-package-c-external-research-prompt",
        action="store_true",
    )
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


def bool_text(value: bool) -> str:
    return str(bool(value)).lower()


def rel(path: Path) -> str:
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def raw_url(path: Path) -> str:
    return f"{GITHUB_RAW_BASE}/{rel(path)}"


def blob_url(path: Path) -> str:
    return f"{GITHUB_BLOB_BASE}/{rel(path)}"


def read_json_summary(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8")).get("summary", {})


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
                "path": rel(path),
                "exists": bool_text(exists),
                "sha256": sha256_file(path) if exists else "",
                "github_raw_url": raw_url(path),
                "github_blob_url": blob_url(path),
                "github_visibility_status": GITHUB_VISIBILITY_STATUS,
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def no_proof_firewall_rows() -> list[dict[str, str]]:
    return [
        {
            "firewall_status": "PASS_PACKAGE_C_EXTERNAL_RESEARCH_PROMPT_NO_PROOF_REGISTRATION",
            "package_c_proof_artifact_registered": "false",
            "proof_registration_authorized": "false",
            "package_c_validation_status_pass_authorized": "false",
            "runtime_configuration_authorized": "false",
            "substep_runtime_policy_authorized": "false",
            "sidewall_prs_eas_numeric_output_authorized": "false",
            "nodi_runtime_recomputation_authorized": "false",
            "comsol_launch_authorized": "false",
            "mph_load_authorized": "false",
            "validated_brownian_solver_output_authorized": "false",
            "hindered_diffusion_claim_authorized": "false",
            "trapezoid_flow_solver_claim_authorized": "false",
            "electrokinetic_solver_claim_authorized": "false",
            "optical_solver_claim_authorized": "false",
            "true_w_eff_authorized": "false",
            "wet_claim_authorized": "false",
            "route_score_authorized": "false",
            "winner_authorized": "false",
            "yield_authorized": "false",
            "detection_probability_authorized": "false",
            "production_ingestion_authorized": "false",
        }
    ]


def context_rows() -> list[dict[str, str]]:
    readiness = read_json_summary(READINESS_STATUS)
    index_rows = read_csv_rows(READINESS_INDEX) if READINESS_INDEX.exists() else []
    threshold_rows = read_csv_rows(THRESHOLD_TABLE) if THRESHOLD_TABLE.exists() else []
    row_by_metric = {row["metric_id"]: row for row in threshold_rows}
    return [
        {
            "context_id": "entrypoint",
            "context_value": readiness.get("artifact_id", ""),
            "details": (
                f"readiness_index_rows={readiness.get('readiness_index_rows', '')};"
                f"open_blocker_rows={readiness.get('open_blocker_rows', '')};"
                f"external_research_question_rows={readiness.get('external_research_question_rows', '')}"
            ),
            "github_url": blob_url(READINESS_STATUS),
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "context_id": "artifact_roles",
            "context_value": ";".join(row["artifact_role"] for row in index_rows),
            "details": "Current evidence blocks covered by the readiness index.",
            "github_url": blob_url(READINESS_INDEX),
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "context_id": "stationarity_gap",
            "context_value": row_by_metric.get("max_u_accessible_cdf_l1_to_uniform", {}).get(
                "observed_value",
                "",
            ),
            "details": "u marginal and x-local stationarity lines meet numeric proof thresholds but still need proof-level method/source binding.",
            "github_url": blob_url(THRESHOLD_TABLE),
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "context_id": "one_wall_wall_pileup_refinement",
            "context_value": row_by_metric.get("max_one_wall_positive_control_ks", {}).get(
                "observed_value",
                "",
            ),
            "details": "Expanded one-wall/wall-pileup refinement meets numeric proof-threshold lines but remains candidate-only and not proof registered.",
            "github_url": blob_url(THRESHOLD_TABLE),
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "context_id": "near_boundary_expected_band_method",
            "context_value": row_by_metric.get("max_near_boundary_expected_band_z_abs", {}).get(
                "observed_value",
                "",
            ),
            "details": "Near-boundary expected-band method is bound as candidate evidence using area(radius+band) differences; external review should assess method and threshold, not proof/pass.",
            "github_url": blob_url(THRESHOLD_TABLE),
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "context_id": "substep_runtime_cost",
            "context_value": row_by_metric.get("max_required_substeps_to_meet_threshold", {}).get(
                "observed_value",
                "",
            ),
            "details": "Worst current substep requirement before any runtime policy.",
            "github_url": blob_url(THRESHOLD_TABLE),
            "claim_boundary": CLAIM_BOUNDARY,
        },
        {
            "context_id": "runtime_substep_policy_design",
            "context_value": row_by_metric.get("runtime_substep_policy_design_status", {}).get(
                "observed_value",
                "",
            ),
            "details": "Runtime/substep policy classes are now design-bound, including prohibitive cost handling, but runtime remains unauthorized.",
            "github_url": blob_url(THRESHOLD_TABLE),
            "claim_boundary": CLAIM_BOUNDARY,
        },
    ]


def external_scope_rows(rows: list[dict[str, str]], source_artifact: str) -> list[dict[str, str]]:
    scoped_rows: list[dict[str, str]] = []
    for row in rows:
        scoped = dict(row)
        inherited_claim_boundary = scoped.get("claim_boundary", "")
        if inherited_claim_boundary and inherited_claim_boundary != CLAIM_BOUNDARY:
            scoped["source_claim_boundary"] = inherited_claim_boundary
        scoped["source_artifact"] = source_artifact
        scoped["claim_boundary"] = CLAIM_BOUNDARY
        scoped["allowed_use"] = ALLOWED_USE
        scoped["blocked_use"] = BLOCKED_USE
        scoped_rows.append(scoped)
    return scoped_rows


def prompt_markdown() -> str:
    readiness = read_json_summary(READINESS_STATUS)
    questions = read_csv_rows(READINESS_QUESTIONS) if READINESS_QUESTIONS.exists() else []
    blockers = read_csv_rows(READINESS_BLOCKERS) if READINESS_BLOCKERS.exists() else []
    threshold_rows = read_csv_rows(THRESHOLD_TABLE) if THRESHOLD_TABLE.exists() else []
    question_text = "\n".join(
        f"{idx}. {row['question']}\n   Scope guard: {row['scope_guard']}"
        for idx, row in enumerate(questions, start=1)
    )
    blocker_text = "\n".join(
        f"- {row['blocker_id']}: {row['evidence']} -> {row['required_resolution']}"
        for row in blockers
    )
    metric_text = "\n".join(
        (
            f"- {row['metric_id']}: observed={row['observed_value']}; "
            f"candidate={row['candidate_acceptance']}; proof={row['proof_acceptance']}; "
            f"status={row['current_status']}"
        )
        for row in threshold_rows
    )
    return f"""# External AI Research Prompt: NODI Package C Sidewall Reflection Proof Gaps

You can only inspect GitHub-visible files. Do not assume access to local Codex files, local COMSOL projects, local `.mph` files, local CSVs outside GitHub, or uncommitted artifacts. If a GitHub URL is not visible yet, treat it as a publish-timing limitation, not as evidence absence.

Primary GitHub-visible entrypoint after publish:
- Readiness status: {blob_url(READINESS_STATUS)}
- Readiness index CSV: {blob_url(READINESS_INDEX)}
- Open blockers CSV: {blob_url(READINESS_BLOCKERS)}
- External research questions CSV: {blob_url(READINESS_QUESTIONS)}
- Proof threshold table CSV: {blob_url(THRESHOLD_TABLE)}
- Roadmap: {blob_url(REPORT_DIR / '100_NODI_SIDEWALL_ANGLE_INTEGRATION_ROADMAP_20260629.md')}
- Audit packet: {blob_url(REPORT_DIR / '345_NODI_SIDEWALL_ANGLE_IMPLEMENTATION_AUDIT_PACKET_20260630.md')}

Current disposition:
- {readiness.get('disposition', '')}
- artifact_id={readiness.get('artifact_id', '')}
- readiness_index_rows={readiness.get('readiness_index_rows', '')}
- open_blocker_rows={readiness.get('open_blocker_rows', '')}
- external_research_question_rows={readiness.get('external_research_question_rows', '')}

Hard boundary:
- Do not register Package C proof/pass.
- Do not mark `package_C_validation_status=pass`.
- Do not authorize runtime configuration, NODI recomputation, COMSOL launch, `.mph` load, numeric PRS/EAS output, route_score, winner, JRC, q_ch weighting, yield, detection_probability, wet pass, clogging, time-to-clog, recovery, fabrication release, or production ingestion.
- Treat all current metrics as candidate/readiness evidence, not validated Brownian solver output, hindered hydrodynamics, trapezoid Poiseuille, electrokinetic solver, optical solver, wet behavior, or production evidence.

Open blockers:
{blocker_text}

Current threshold rows:
{metric_text}

Research questions to answer in one pass:
{question_text}

Requested output:
1. Give a concise verdict for each research question: recommended proof-level method/threshold, supporting references or reasoning, and whether current candidate evidence is sufficient, insufficient, or needs a different metric.
2. Identify the highest-leverage next local evidence block. Prefer one block that can move multiple proof gaps at once.
3. Keep claim boundaries explicit. If you suggest future runtime/substep policy, state exactly what remains required before runtime can be authorized.
4. Do not provide route, yield, detection, wet, fabrication, or production conclusions.
"""


def build_payload() -> dict[str, Any]:
    contexts = context_rows()
    raw_questions = read_csv_rows(READINESS_QUESTIONS) if READINESS_QUESTIONS.exists() else []
    raw_blockers = read_csv_rows(READINESS_BLOCKERS) if READINESS_BLOCKERS.exists() else []
    questions = external_scope_rows(raw_questions, "PACKAGE_C_PROOF_READINESS_INDEX_20260701")
    blockers = external_scope_rows(raw_blockers, "PACKAGE_C_PROOF_READINESS_INDEX_20260701")
    sources = source_lock_rows()
    firewall = no_proof_firewall_rows()
    prompt = prompt_markdown()
    summary = {
        "disposition": DISPOSITION,
        "artifact_id": ARTIFACT_ID,
        "claim_boundary": CLAIM_BOUNDARY,
        "build_head": safe_git_head(),
        "context_rows": len(contexts),
        "research_question_rows": len(questions),
        "blocker_rows": len(blockers),
        "source_lock_rows": len(sources),
        "source_missing_rows": sum(row["exists"] != "true" for row in sources),
        "prompt_character_count": len(prompt),
        "prompt_status": "copyable_external_research_prompt_ready",
        "proof_registration_authorized": False,
        "package_c_validation_status_pass_authorized": False,
        "runtime_allowed": False,
        "numeric_prs_eas_allowed": False,
        "comsol_launch_allowed": False,
        "mph_load_allowed": False,
        "candidate_only": True,
        "no_auth": True,
        "github_visibility_status": GITHUB_VISIBILITY_STATUS,
        "allowed_use": ALLOWED_USE,
        "blocked_use": BLOCKED_USE,
    }
    return {
        "summary": summary,
        "context_rows": contexts,
        "research_questions": questions,
        "blockers": blockers,
        "source_locks": sources,
        "no_proof_firewall": firewall,
        "prompt_markdown": prompt,
    }


def validate_payload(payload: dict[str, Any]) -> list[str]:
    s = payload["summary"]
    prompt = payload["prompt_markdown"]
    firewall = payload["no_proof_firewall"][0]
    checks = {
        "Context rows": s["context_rows"] == EXPECTED_CONTEXT_ROWS,
        "Research questions": s["research_question_rows"] >= 4,
        "Blockers": s["blocker_rows"] >= 4,
        "Source lock complete": s["source_missing_rows"] == 0,
        "Prompt has GitHub entrypoint": "github.com/Shaughn0419/NODI_Simulator" in prompt,
        "Prompt states no local file access": "Do not assume access to local Codex files" in prompt,
        "Prompt blocks proof/pass": "Do not register Package C proof/pass" in prompt,
        "Prompt blocks runtime": "Do not authorize runtime configuration" in prompt,
        "No proof registration": s["proof_registration_authorized"] is False,
        "No Package C pass": s["package_c_validation_status_pass_authorized"] is False,
        "No runtime": s["runtime_allowed"] is False,
        "No numeric PRS/EAS": s["numeric_prs_eas_allowed"] is False,
        "No COMSOL launch": s["comsol_launch_allowed"] is False,
        "No mph load": s["mph_load_allowed"] is False,
    }
    for key, value in firewall.items():
        if key.endswith("_authorized") or key in {
            "package_c_proof_artifact_registered",
            "proof_registration_authorized",
        }:
            checks[f"Firewall false: {key}"] = value == "false"
    return [label for label, ok in checks.items() if not ok]


def artifact_manifest_rows(
    paths: list[Path],
    *,
    self_manifest_path: Path | None = None,
) -> list[dict[str, str]]:
    rows = [
        {
            "artifact": path.name,
            "path": rel(path),
            "sha256": sha256_file(path) if path.exists() else "",
            "disposition": DISPOSITION,
            "policy_impact": "external_research_prompt_no_proof_registration",
            "allowed_use": ALLOWED_USE,
            "blocked_use": BLOCKED_USE,
        }
        for path in paths
    ]
    if self_manifest_path is not None:
        rows.append(
            {
                "artifact": self_manifest_path.name,
                "path": rel(self_manifest_path),
                "sha256": SELF_MANIFEST_SHA256,
                "disposition": DISPOSITION,
                "policy_impact": "manifest_self_row_no_recursive_sha_no_proof_registration",
                "allowed_use": ALLOWED_USE,
                "blocked_use": BLOCKED_USE,
            }
        )
    return rows


def write_outputs(
    payload: dict[str, Any],
    *,
    output_dir: Path | None = None,
    report_dir: Path | None = None,
) -> dict[str, Path]:
    active_output_dir = output_dir or OUTPUT_DIR
    active_report_dir = report_dir or REPORT_DIR
    active_output_dir.mkdir(parents=True, exist_ok=True)
    active_report_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []

    csv_specs = {
        "NODI_COMSOL_PACKAGE_C_EXTERNAL_RESEARCH_CONTEXT_20260701.csv": payload[
            "context_rows"
        ],
        "NODI_COMSOL_PACKAGE_C_EXTERNAL_RESEARCH_QUESTIONS_20260701.csv": payload[
            "research_questions"
        ],
        "NODI_COMSOL_PACKAGE_C_EXTERNAL_RESEARCH_BLOCKERS_20260701.csv": payload[
            "blockers"
        ],
        "NODI_COMSOL_PACKAGE_C_EXTERNAL_RESEARCH_SOURCE_LOCK_20260701.csv": payload[
            "source_locks"
        ],
        "NODI_COMSOL_PACKAGE_C_EXTERNAL_RESEARCH_NO_PROOF_FIREWALL_20260701.csv": payload[
            "no_proof_firewall"
        ],
    }
    for name, rows in csv_specs.items():
        path = active_output_dir / name
        write_csv_rows(path, rows)
        generated.append(path)

    prompt_path = active_output_dir / "NODI_COMSOL_PACKAGE_C_EXTERNAL_RESEARCH_PROMPT_20260701.md"
    prompt_path.write_text(payload["prompt_markdown"], encoding="utf-8")
    generated.append(prompt_path)

    status_path = active_output_dir / "NODI_COMSOL_PACKAGE_C_EXTERNAL_RESEARCH_STATUS_20260701.json"
    write_json_atomic(
        status_path,
        {
            "disposition": DISPOSITION,
            "summary": payload["summary"],
            "proof_registration_authorized": False,
            "package_c_validation_status_pass_authorized": False,
            "runtime_allowed": False,
            "numeric_prs_eas_allowed": False,
            "comsol_launch_allowed": False,
            "mph_load_allowed": False,
        },
    )
    generated.append(status_path)

    public_report = active_report_dir / "510_NODI_COMSOL_PACKAGE_C_EXTERNAL_RESEARCH_PROMPT_20260701.md"
    public_report.write_text(payload["prompt_markdown"], encoding="utf-8")
    generated.append(public_report)

    manifest_path = active_output_dir / "NODI_COMSOL_PACKAGE_C_EXTERNAL_RESEARCH_MANIFEST_20260701.csv"
    report_path = active_output_dir / "NODI_COMSOL_PACKAGE_C_EXTERNAL_RESEARCH_REPORT_20260701.json"
    report_outputs = [path.name for path in generated] + [report_path.name, manifest_path.name]
    write_json_atomic(report_path, {"summary": payload["summary"], "outputs": report_outputs})
    generated.append(report_path)
    write_csv_rows(
        manifest_path,
        artifact_manifest_rows(generated, self_manifest_path=manifest_path),
    )
    return {"status": status_path, "report": report_path, "manifest": manifest_path}


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.confirm_package_c_external_research_prompt:
        parser.error("--confirm-package-c-external-research-prompt is required")
    payload = build_payload()
    failures = validate_payload(payload)
    if failures:
        print("BLOCKED_PACKAGE_C_EXTERNAL_RESEARCH_PROMPT")
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    write_outputs(payload)
    print(DISPOSITION)
    print(json.dumps(payload["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
