"""Claim-language scanning helpers for review-package checks."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .realism_v2_io import write_json_atomic
from .review_package_git import git_tracked_paths
from .review_package_json import load_json_compatible as _load_json_compatible
from .review_package_paths import normalize_relpath as _normalize_relpath


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ClaimFinding:
    text: str
    phrase: str
    language: str
    allowed_by_negator: bool


def build_forbidden_claims_lexicon() -> dict[str, Any]:
    return {
        "schema": "ev_nodi_forbidden_claims_lexicon_v1",
        "languages": ["en", "zh"],
        "claim_scope": "no_measured_data_relative_audit_only",
        "negator_window_tokens_en": 8,
        "negator_window_chars_zh": 16,
        "verbs": [
            "calibrated",
            "validated",
            "absolute",
            "confirmed",
            "established",
            "measured",
            "true",
            "physical",
        ],
        "objects": [
            "SNR",
            "signal-to-noise",
            "LOD",
            "detection limit",
            "p_detect",
            "event probability",
            "false positive",
            "blank safety",
            "EV concentration",
            "particle count",
            "biological specificity",
            "exosome-specific detection",
            "MSC-EV-specific detection",
            "route promotion",
            "main-660 redefinition",
            "detector-resolved winner",
            "absolute winner",
            "blank-FPR",
            "NODI gain",
        ],
        "zh_forbidden_verbs": ["校准", "验证", "确认", "绝对", "真实", "实测", "已证明"],
        "zh_forbidden_objects": [
            "SNR",
            "信噪比",
            "LOD",
            "检测限",
            "假阳性",
            "空白安全",
            "EV浓度",
            "颗粒浓度",
            "生物特异性",
            "外泌体特异性",
            "MSC-EV特异性",
            "路线晋升",
            "main-660重新定义",
            "detector-resolved winner",
            "绝对胜者",
            "探测器分辨胜者",
            "blank-FPR",
            "空白FPR",
            "外差增强倍数",
        ],
        "forbidden_phrase_negators": [
            "blocked",
            "forbidden",
            "not allowed",
            "cannot",
            "do not",
            "does not",
            "not",
            "no",
            "not supported",
            "not a claim",
            "not mean",
            "must not",
            "unauthorized",
            "not authorized",
            "not calibrated",
        ],
        "zh_negators": [
            "禁止",
            "阻断",
            "不允许",
            "不能",
            "不应",
            "未校准",
            "非校准",
            "不代表",
            "未实现",
            "未达",
            "无法",
            "尚未",
            "暂未",
            "不可声称",
            "已封禁",
            "已封锁",
            "被阻断",
            "不授权",
        ],
        "allowed_blocker_examples": [
            "calibrated SNR blocked",
            "absolute LOD blocked",
            "not calibrated",
            "relative robustness only",
            "no-measured-data audit-only",
            "absolute claim blocked",
            "biological specificity blocked",
            "no absolute winner",
            "detector-resolved winner not authorized",
            "blank-FPR not calibrated",
            "NODI gain not a claim",
        ],
    }


def write_forbidden_claims_lexicon(project_root: Path = PROJECT_ROOT) -> Path:
    path = project_root / "configs/realism_v2/forbidden_claims_lexicon.yaml"
    write_json_atomic(path, build_forbidden_claims_lexicon(), sort_keys=True)
    return path


def _english_phrases(lexicon: Mapping[str, Any]) -> list[str]:
    phrases: list[str] = []
    for verb in lexicon["verbs"]:
        phrases.extend(f"{verb} {obj}".lower() for obj in lexicon["objects"])
    phrases.extend(str(obj).lower() for obj in lexicon["objects"])
    return sorted(set(phrases), key=len, reverse=True)


def _zh_phrases(lexicon: Mapping[str, Any]) -> list[str]:
    phrases: list[str] = []
    for verb in lexicon["zh_forbidden_verbs"]:
        phrases.extend(f"{verb}{obj}" for obj in lexicon["zh_forbidden_objects"])
    phrases.extend(str(obj) for obj in lexicon["zh_forbidden_objects"])
    return sorted(set(phrases), key=len, reverse=True)


def _contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def _ascii_object_only_phrase(phrase: str) -> bool:
    return phrase.isascii() and " " not in phrase and "-" not in phrase


def _has_negator_near_english(text: str, start: int, end: int, lexicon: Mapping[str, Any]) -> bool:
    lowered = text.lower()
    window = 320
    context = lowered[max(0, start - window) : min(len(text), end + window)]
    return any(str(negator).lower() in context for negator in lexicon["forbidden_phrase_negators"])


def _has_negator_near_zh(text: str, start: int, end: int, lexicon: Mapping[str, Any]) -> bool:
    window = int(lexicon["negator_window_chars_zh"])
    context = text[max(0, start - window) : min(len(text), end + window)]
    return any(str(negator) in context for negator in lexicon["zh_negators"])


def scan_forbidden_claims(text: str, lexicon: Mapping[str, Any]) -> list[ClaimFinding]:
    findings: list[ClaimFinding] = []
    lowered = text.lower()
    contains_cjk = _contains_cjk(text)
    for phrase in _english_phrases(lexicon):
        if contains_cjk and _ascii_object_only_phrase(phrase):
            continue
        start = lowered.find(phrase)
        if start == -1:
            continue
        end = start + len(phrase)
        findings.append(
            ClaimFinding(
                text=text,
                phrase=phrase,
                language="en",
                allowed_by_negator=_has_negator_near_english(text, start, end, lexicon),
            )
        )
    if not contains_cjk:
        return findings
    for phrase in _zh_phrases(lexicon):
        start = text.find(phrase)
        if start == -1:
            continue
        end = start + len(phrase)
        findings.append(
            ClaimFinding(
                text=text,
                phrase=phrase,
                language="zh",
                allowed_by_negator=_has_negator_near_zh(text, start, end, lexicon),
            )
        )
    return findings


def claim_text_passes(text: str, lexicon: Mapping[str, Any]) -> bool:
    return all(finding.allowed_by_negator for finding in scan_forbidden_claims(text, lexicon))


def load_forbidden_claims_lexicon(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    return _load_json_compatible(project_root / "configs/realism_v2/forbidden_claims_lexicon.yaml")


def claim_scan_paths(project_root: Path = PROJECT_ROOT) -> list[Path]:
    patterns = (
        "README.md",
        "reports/9[0-9]_*.md",
        "reports/100_*.md",
        "reports/101_*.md",
        "reports/102_*.md",
        "reports/103_*.md",
        "reports/104_*.md",
        "reports/105_*.md",
        "reports/106_*.md",
        "reports/107_*.md",
        "reports/108_*.md",
        "reports/109_*.md",
        "reports/110_*.md",
        "reports/111_*.md",
        "reports/112_*.md",
        "reports/113_*.md",
        "reports/114_*.md",
        "reports/115_*.md",
        "reports/116_*.md",
        "reports/117_*.md",
        "reports/118_*.md",
        "reports/119_*.md",
        "reports/120_*.md",
        "reports/post_v2_*.md",
        "results/post_v2_mandatory_audit/*.md",
        "results/post_v2_physical_ceiling/*.md",
        "results/post_v2_bounded_physical_solver_readiness/*.md",
        "results/post_v2_bounded_solver_authorization_pilot_design/*.md",
        "results/post_v2_bounded_solver_dry_run_preflight/*.md",
        "results/post_v2_bounded_solver_authorization_gate/*.md",
        "results/post_v2_minimal_bounded_solver_execution/*.md",
        "results/post_v2_second_lane_authorization_design/*.md",
        "results/post_v2_second_bounded_solver_lane_execution/*.md",
        "results/post_v2_second_bounded_solver_lane_closure/*.md",
        "results/post_v2_next_bounded_lane_authorization_design/*.md",
        "results/post_v2_third_bounded_solver_lane_execution/*.md",
        "results/post_v2_third_bounded_solver_lane_closure/*.md",
        "results/post_v2_fourth_bounded_lane_authorization_design/*.md",
        "results/post_v2_fourth_bounded_solver_lane_execution/*.md",
        "results/post_v2_fourth_bounded_solver_lane_closure/*.md",
        "results/post_v2_fifth_bounded_lane_authorization_design/*.md",
        "results/post_v2_fifth_bounded_solver_lane_execution/*.md",
        "results/post_v2_fifth_bounded_solver_lane_closure/*.md",
        "results/post_v2_sixth_bounded_lane_authorization_design/*.md",
        "results/post_v2_sixth_bounded_solver_lane_execution/*.md",
        "results/post_v2_sixth_bounded_solver_lane_closure/*.md",
        "results/post_v2_seventh_bounded_lane_authorization_design/*.md",
        "results/post_v2_bounded_lane_synthesis_stop_continue/*.md",
        "REVIEW_PACKAGE_README.md",
        "papers/README.md",
    )
    tracked_paths = git_tracked_paths(project_root)
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(project_root.glob(pattern))
    return sorted(
        {
            path
            for path in paths
            if path.is_file()
            and not path.name.startswith("._")
            and (
                tracked_paths is None
                or _normalize_relpath(path.relative_to(project_root)) in tracked_paths
            )
        },
        key=lambda path: _normalize_relpath(path.relative_to(project_root)),
    )


def _strip_fenced_code_blocks(text: str) -> str:
    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def scan_claim_files(project_root: Path = PROJECT_ROOT) -> list[dict[str, Any]]:
    lexicon = load_forbidden_claims_lexicon(project_root)
    violations: list[dict[str, Any]] = []
    for path in claim_scan_paths(project_root):
        text = _strip_fenced_code_blocks(path.read_text(encoding="utf-8"))
        for finding in scan_forbidden_claims(text, lexicon):
            if finding.allowed_by_negator:
                continue
            violations.append(
                {
                    "path": _normalize_relpath(path.relative_to(project_root)),
                    "phrase": finding.phrase,
                    "language": finding.language,
                }
            )
    return violations
