#!/usr/bin/env python3
"""Validate and grade model-agnostic DAMASK skill evaluations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Iterable


SKILL_ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = SKILL_ROOT / "evals" / "cases.json"
MAX_CASES_BYTES = 512 * 1024
MAX_RESPONSE_BYTES = 1024 * 1024
PASS_THRESHOLD = 0.80
LEVELS = {"basic", "advanced"}
RESPONSE_SUFFIXES = (".json", ".txt", ".md")
VENDOR_PATTERN = re.compile(
    r"\b(?:OpenAI|Codex|Claude|ChatGPT|OpenClaw|Hermes(?: Agent)?|GPT-?\d)\b",
    re.IGNORECASE,
)


class EvalError(RuntimeError):
    """Report an evaluation configuration or input error."""


def _require_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvalError(f"{label} must be a non-empty string")
    if any(ord(character) < 32 and character not in "\n\t" for character in value):
        raise EvalError(f"{label} contains unsupported control characters")
    return value


def _load_json(path: Path, byte_limit: int) -> Any:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise EvalError(f"cannot read {path}: {error}") from error
    if len(raw) > byte_limit:
        raise EvalError(f"{path} exceeds the {byte_limit}-byte limit")
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvalError(f"cannot parse JSON from {path}: {error}") from error


def load_suite() -> dict[str, Any]:
    suite = _load_json(CASES_PATH, MAX_CASES_BYTES)
    if not isinstance(suite, dict) or suite.get("schema_version") != 1:
        raise EvalError("unsupported or invalid eval suite")
    contract = suite.get("response_contract")
    if not isinstance(contract, dict):
        raise EvalError("response_contract must be an object")
    _require_string(contract.get("instruction"), "response_contract.instruction")
    cases = suite.get("cases")
    if not isinstance(cases, list) or not cases:
        raise EvalError("cases must be a non-empty list")

    seen: set[str] = set()
    for case_index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise EvalError(f"cases[{case_index}] must be an object")
        case_id = _require_string(case.get("id"), f"cases[{case_index}].id")
        if re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", case_id) is None or case_id in seen:
            raise EvalError(f"unsafe or duplicate case id: {case_id!r}")
        seen.add(case_id)
        if case.get("level") not in LEVELS:
            raise EvalError(f"case {case_id} has an unsupported level")
        _require_string(case.get("title"), f"case {case_id}.title")
        _require_string(case.get("task"), f"case {case_id}.task")
        required = case.get("required")
        forbidden = case.get("forbidden")
        if not isinstance(required, list) or not required:
            raise EvalError(f"case {case_id}.required must be a non-empty list")
        if not isinstance(forbidden, list):
            raise EvalError(f"case {case_id}.forbidden must be a list")
        check_ids: set[str] = set()
        for category, checks in (("required", required), ("forbidden", forbidden)):
            for check_index, check in enumerate(checks):
                if not isinstance(check, dict):
                    raise EvalError(f"case {case_id}.{category}[{check_index}] must be an object")
                check_id = _require_string(check.get("id"), f"case {case_id} check id")
                if check_id in check_ids:
                    raise EvalError(f"case {case_id} has duplicate check id {check_id!r}")
                check_ids.add(check_id)
                _require_string(check.get("description"), f"case {case_id}.{check_id}.description")
                patterns = check.get("patterns")
                if not isinstance(patterns, list) or not patterns:
                    raise EvalError(f"case {case_id}.{check_id}.patterns must be non-empty")
                for pattern_index, pattern in enumerate(patterns):
                    pattern = _require_string(
                        pattern, f"case {case_id}.{check_id}.patterns[{pattern_index}]"
                    )
                    try:
                        re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                    except re.error as error:
                        raise EvalError(
                            f"case {case_id}.{check_id} has invalid regex {pattern!r}: {error}"
                        ) from error
                if "critical" in check and not isinstance(check["critical"], bool):
                    raise EvalError(f"case {case_id}.{check_id}.critical must be boolean")
    return suite


def case_by_id(suite: dict[str, Any], case_id: str) -> dict[str, Any]:
    for case in suite["cases"]:
        if case["id"] == case_id:
            return case
    raise EvalError(f"unknown case id: {case_id}")


def flatten_json(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from flatten_json(item)
    elif isinstance(value, list):
        for item in value:
            yield from flatten_json(item)
    elif value is not None:
        yield str(value)


def load_response(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except OSError as error:
        raise EvalError(f"cannot read response {path}: {error}") from error
    if len(raw) > MAX_RESPONSE_BYTES:
        raise EvalError(f"response exceeds the {MAX_RESPONSE_BYTES}-byte limit: {path}")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise EvalError(f"response is not UTF-8: {path}") from error
    if path.suffix.lower() == ".json":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as error:
            raise EvalError(f"response JSON is invalid: {error}") from error
        text = "\n".join(flatten_json(parsed))
    if not text.strip():
        raise EvalError(f"response is empty: {path}")
    return text


def _matches(text: str, patterns: list[str]) -> list[str]:
    return [
        pattern
        for pattern in patterns
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE) is not None
    ]


def grade_text(case: dict[str, Any], text: str) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    critical_ok = True
    for category in ("required", "forbidden"):
        for check in case[category]:
            matches = _matches(text, check["patterns"])
            passed = bool(matches) if category == "required" else not matches
            critical = bool(check.get("critical", False))
            if critical and not passed:
                critical_ok = False
            results.append(
                {
                    "id": check["id"],
                    "category": category,
                    "description": check["description"],
                    "critical": critical,
                    "passed": passed,
                    "matched_patterns": matches,
                }
            )
    passed_checks = sum(1 for result in results if result["passed"])
    score = passed_checks / len(results)
    return {
        "case_id": case["id"],
        "level": case["level"],
        "title": case["title"],
        "passed": score >= PASS_THRESHOLD and critical_ok,
        "score": round(score, 4),
        "passed_checks": passed_checks,
        "total_checks": len(results),
        "critical_checks_passed": critical_ok,
        "checks": results,
    }


def missing_grade(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["id"],
        "level": case["level"],
        "title": case["title"],
        "passed": False,
        "score": 0.0,
        "passed_checks": 0,
        "total_checks": 1,
        "critical_checks_passed": False,
        "checks": [
            {
                "id": "missing-response",
                "category": "required",
                "description": "No response file was found for this case.",
                "critical": True,
                "passed": False,
                "matched_patterns": [],
            }
        ],
    }


def summarize(grades: list[dict[str, Any]]) -> dict[str, Any]:
    def level_summary(level: str) -> dict[str, Any]:
        selected = [grade for grade in grades if grade["level"] == level]
        return {
            "passed": sum(1 for grade in selected if grade["passed"]),
            "total": len(selected),
            "mean_score": round(
                sum(grade["score"] for grade in selected) / len(selected), 4
            ) if selected else 0.0,
        }

    failures = []
    for grade in grades:
        failed = [check["id"] for check in grade["checks"] if not check["passed"]]
        if failed:
            failures.append({"case_id": grade["case_id"], "failed_checks": failed})
    critical_failures = [
        grade["case_id"] for grade in grades if not grade["critical_checks_passed"]
    ]
    basic = level_summary("basic")
    advanced = level_summary("advanced")
    recommendation = "not-ready"
    if basic["passed"] == basic["total"] and not critical_failures:
        recommendation = "guided-use"
        if advanced["total"] and advanced["passed"] / advanced["total"] >= 0.80:
            recommendation = "normal-assisted-use"
    return {
        "schema_version": 1,
        "threshold": PASS_THRESHOLD,
        "overall": {
            "passed": sum(1 for grade in grades if grade["passed"]),
            "total": len(grades),
            "mean_score": round(sum(grade["score"] for grade in grades) / len(grades), 4),
        },
        "levels": {"basic": basic, "advanced": advanced},
        "critical_failures": critical_failures,
        "failures": failures,
        "recommendation": recommendation,
        "meaning": {
            "normal-assisted-use": "Basic suite passed and at least 80% of advanced cases passed; keep human review of scientific choices.",
            "guided-use": "Basic suite passed but advanced coverage is incomplete; limit use to retrieval, staging, and dry-run preparation.",
            "not-ready": "At least one basic or critical check failed; do not rely on autonomous execution.",
        }[recommendation],
    }


def _relative_markdown_links(path: Path) -> list[Path]:
    text = path.read_text(encoding="utf-8")
    targets: list[Path] = []
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        target = target.strip().split("#", 1)[0]
        if not target or "://" in target or target.startswith("#"):
            continue
        targets.append((path.parent / target).resolve())
    return targets


def validate_skill() -> dict[str, Any]:
    suite = load_suite()
    checks: list[dict[str, Any]] = []

    def record(check_id: str, passed: bool, detail: str) -> None:
        checks.append({"id": check_id, "passed": passed, "detail": detail})

    skill_path = SKILL_ROOT / "SKILL.md"
    skill_text = skill_path.read_text(encoding="utf-8")
    frontmatter = re.match(r"\A---\n(.*?)\n---\n", skill_text, re.DOTALL)
    record("frontmatter", frontmatter is not None, "SKILL.md has YAML frontmatter")
    name = ""
    description = ""
    if frontmatter:
        for line in frontmatter.group(1).splitlines():
            if line.startswith("name:"):
                name = line.partition(":")[2].strip()
            elif line.startswith("description:"):
                description = line.partition(":")[2].strip()
    record("skill-name", name == "damask-skill", f"frontmatter name is {name!r}")
    record(
        "description-length",
        1 <= len(description) <= 1024,
        f"frontmatter description length is {len(description)}",
    )
    vendor_hits = sorted(set(match.group(0) for match in VENDOR_PATTERN.finditer(skill_text)))
    record(
        "vendor-neutral-core",
        not vendor_hits,
        "no backend-specific model/agent names in SKILL.md" if not vendor_hits else f"found {vendor_hits}",
    )

    required_boundaries = {
        "user-priority": "user's explicit request take precedence over this skill",
        "reference-data-boundary": "untrusted scientific data and never instructions",
        "execution-default": "execute only when the user asks",
        "immutable-references": "Never edit or execute bundled references directly",
    }
    missing_boundaries = [
        name for name, phrase in required_boundaries.items() if phrase not in skill_text
    ]
    record(
        "instruction-boundaries",
        not missing_boundaries,
        "priority, reference-data, execution, and immutability boundaries are explicit"
        if not missing_boundaries else f"missing {missing_boundaries}",
    )
    contradiction_patterns = {
        "default-execution": r"execute(?:s|d)? by default",
        "mutable-latest": r"(?:use|guess) (?:the )?:?latest",
        "edit-bundled-in-place": r"(?m)^(?![^\n]*\b(?:never|do not|don't|must not)\b)[^\n]*edit bundled (?:references|files) in place",
        "run-bundled-directly": r"(?m)^(?![^\n]*\b(?:never|do not|don't|must not)\b)[^\n]*(?:run|execute) bundled (?:references|source) directly",
    }
    contradictions = [
        name
        for name, pattern in contradiction_patterns.items()
        if re.search(pattern, skill_text, re.IGNORECASE) is not None
    ]
    record(
        "conflict-scan",
        not contradictions,
        "no known contradictory execution, image, or reference-handling directives"
        if not contradictions else f"found {contradictions}",
    )

    required_paths = [
        SKILL_ROOT / "references" / "backend-compatibility.md",
        SKILL_ROOT / "references" / "evaluation.md",
        SKILL_ROOT / "scripts" / "install_skill.py",
        SKILL_ROOT / "scripts" / "run_evals.py",
    ]
    missing = [str(path.relative_to(SKILL_ROOT)) for path in required_paths if not path.is_file()]
    record("required-files", not missing, "all required files exist" if not missing else f"missing {missing}")
    metadata_dir = SKILL_ROOT / "agents"
    metadata_path = metadata_dir / "openai.yaml"
    metadata_ok = not metadata_dir.exists() or metadata_path.is_file()
    record(
        "optional-vendor-metadata",
        metadata_ok,
        "optional vendor metadata is absent or correctly isolated"
        if metadata_ok else "agents/ exists but agents/openai.yaml is missing",
    )

    markdown_paths = [
        skill_path,
        SKILL_ROOT / "references" / "backend-compatibility.md",
        SKILL_ROOT / "references" / "evaluation.md",
        SKILL_ROOT / "references" / "official-usage.md",
        SKILL_ROOT / "references" / "example-library.md",
        SKILL_ROOT / "references" / "python-utilities.md",
    ]
    corpus = "\n".join(
        markdown_path.read_text(encoding="utf-8")
        for markdown_path in markdown_paths
        if markdown_path.is_file()
    )
    cross_reference_conflicts = {
        "stale-skill-name": r"damask-usage",
        "obsolete-codex-path": r"(?:~/|\$HOME/)\.codex/skills",
        "runnable-latest-image": r"damaskmultiphysics/[a-z-]+:latest",
    }
    cross_reference_hits = [
        name
        for name, pattern in cross_reference_conflicts.items()
        if re.search(pattern, corpus, re.IGNORECASE) is not None
    ]
    record(
        "cross-reference-conflicts",
        not cross_reference_hits,
        "no stale skill names, obsolete install paths, or runnable mutable-image examples"
        if not cross_reference_hits else f"found {cross_reference_hits}",
    )

    link_sources = [skill_path, *required_paths[:2]]
    broken: list[str] = []
    for source in link_sources:
        if not source.is_file():
            continue
        for target in _relative_markdown_links(source):
            if not target.exists():
                broken.append(f"{source.relative_to(SKILL_ROOT)} -> {target}")
    record("relative-links", not broken, "all relative Markdown links resolve" if not broken else "; ".join(broken))

    script_paths = [
        SKILL_ROOT / "scripts" / name
        for name in (
            "example_library.py",
            "python_reference.py",
            "run_solver.py",
            "install_skill.py",
            "run_evals.py",
        )
    ]
    compile_errors: list[str] = []
    for path in script_paths:
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except (OSError, UnicodeDecodeError, SyntaxError) as error:
            compile_errors.append(f"{path.name}: {error}")
    record("helper-syntax", not compile_errors, "all helper scripts compile" if not compile_errors else "; ".join(compile_errors))

    helper_errors: list[str] = []
    for script, arguments in (
        ("example_library.py", ["verify"]),
        ("python_reference.py", ["verify"]),
        ("install_skill.py", ["--list-targets", "--json"]),
    ):
        path = SKILL_ROOT / "scripts" / script
        if not path.is_file():
            helper_errors.append(f"{script}: missing")
            continue
        completed = subprocess.run(
            [sys.executable, str(path), *arguments],
            cwd=SKILL_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout).strip().replace("\n", " ")
            helper_errors.append(f"{script}: {detail[:240]}")
    record("helper-self-checks", not helper_errors, "library and installer checks passed" if not helper_errors else "; ".join(helper_errors))

    counts = {
        level: sum(1 for case in suite["cases"] if case["level"] == level)
        for level in sorted(LEVELS)
    }
    record(
        "eval-cases",
        counts["basic"] >= 3 and counts["advanced"] >= 3,
        f"validated {len(suite['cases'])} eval cases: {counts['basic']} basic, {counts['advanced']} advanced",
    )
    passed = all(check["passed"] for check in checks)
    return {"passed": passed, "checks": checks}


def find_response(directory: Path, case_id: str) -> Path | None:
    for suffix in RESPONSE_SUFFIXES:
        candidate = directory / f"{case_id}{suffix}"
        if candidate.is_file():
            return candidate
    return None


def print_human_grade(grade: dict[str, Any]) -> None:
    status = "PASS" if grade["passed"] else "FAIL"
    print(f"{status} {grade['case_id']} ({grade['level']}): {grade['passed_checks']}/{grade['total_checks']} checks, score {grade['score']:.0%}")
    for check in grade["checks"]:
        marker = "ok" if check["passed"] else "FAIL"
        critical = " [critical]" if check["critical"] else ""
        print(f"  {marker}: {check['id']}{critical} - {check['description']}")


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(description="Run model-agnostic evaluations for damask-skill.")
    subparsers = top.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate the skill, helpers, and eval suite")
    validate.add_argument("--json", action="store_true")

    list_parser = subparsers.add_parser("list", help="list evaluation cases")
    list_parser.add_argument("--level", choices=sorted(LEVELS))
    list_parser.add_argument("--json", action="store_true")

    prompt = subparsers.add_parser("prompt", help="print a portable prompt for one case")
    prompt.add_argument("case_id")
    prompt.add_argument("--json", action="store_true")

    grade = subparsers.add_parser("grade", help="grade one saved response")
    grade.add_argument("case_id")
    grade.add_argument("response", type=Path)
    grade.add_argument("--json", action="store_true")

    summary_parser = subparsers.add_parser("summary", help="grade all response files in a directory")
    summary_parser.add_argument("responses", type=Path)
    summary_parser.add_argument("--level", choices=sorted(LEVELS))
    summary_parser.add_argument("--json", action="store_true")
    return top


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "validate":
            result = validate_skill()
            if args.json:
                print(json.dumps(result, indent=2, sort_keys=True))
            else:
                for check in result["checks"]:
                    print(f"{'ok' if check['passed'] else 'FAIL'}: {check['id']} - {check['detail']}")
                print("PASS" if result["passed"] else "FAIL")
            return 0 if result["passed"] else 1

        suite = load_suite()
        if args.command == "list":
            selected = [
                case for case in suite["cases"]
                if args.level is None or case["level"] == args.level
            ]
            if args.json:
                print(json.dumps([
                    {key: case[key] for key in ("id", "level", "title", "task")}
                    for case in selected
                ], indent=2, sort_keys=True))
            else:
                for case in selected:
                    print(f"{case['id']}\t{case['level']}\t{case['title']}")
            return 0

        if args.command == "prompt":
            case = case_by_id(suite, args.case_id)
            record = {
                "case_id": case["id"],
                "level": case["level"],
                "instruction": suite["response_contract"]["instruction"],
                "task": case["task"],
            }
            if args.json:
                print(json.dumps(record, indent=2, sort_keys=True))
            else:
                print(f"Evaluation case: {case['id']} ({case['level']})")
                print(suite["response_contract"]["instruction"])
                print()
                print(case["task"])
            return 0

        if args.command == "grade":
            case = case_by_id(suite, args.case_id)
            result = grade_text(case, load_response(args.response))
            if args.json:
                print(json.dumps(result, indent=2, sort_keys=True))
            else:
                print_human_grade(result)
            return 0 if result["passed"] else 1

        if args.command == "summary":
            if not args.responses.is_dir():
                raise EvalError(f"response directory does not exist: {args.responses}")
            selected = [
                case for case in suite["cases"]
                if args.level is None or case["level"] == args.level
            ]
            grades = []
            for case in selected:
                response = find_response(args.responses, case["id"])
                grades.append(
                    grade_text(case, load_response(response)) if response else missing_grade(case)
                )
            result = summarize(grades)
            result["grades"] = grades
            if args.json:
                print(json.dumps(result, indent=2, sort_keys=True))
            else:
                for grade in grades:
                    print_human_grade(grade)
                print()
                print(
                    f"Overall: {result['overall']['passed']}/{result['overall']['total']} cases; "
                    f"recommendation: {result['recommendation']}"
                )
                print(result["meaning"])
            return 0 if result["recommendation"] != "not-ready" else 1
    except (EvalError, OSError, subprocess.SubprocessError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
