#!/usr/bin/env python3
"""Safely install damask-skill for several Agent Skills-compatible agents."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import uuid
from typing import Any, Iterable


SKILL_ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "damask-skill"
MAX_FILES = 5000
MAX_TOTAL_BYTES = 128 * 1024 * 1024
AGENT_ALIASES = {
    "codex": "codex",
    "openai-codex": "codex",
    "claude": "claude-code",
    "claude-code": "claude-code",
    "pi": "pi",
    "openclaw": "openclaw",
    "hermes": "hermes",
    "hermes-agent": "hermes",
    "generic": "generic",
}
TARGETS = {
    "codex": {
        "user": "~/.agents/skills",
        "project": ".agents/skills",
        "vendor_metadata": True,
        "reload": "Start a new Codex task if the skill is not detected in the current task.",
    },
    "claude-code": {
        "user": "~/.claude/skills",
        "project": ".claude/skills",
        "vendor_metadata": False,
        "reload": "Claude Code normally detects SKILL.md changes live; restart if the top-level skills directory was newly created.",
    },
    "pi": {
        "user": "~/.pi/agent/skills",
        "project": ".pi/skills",
        "vendor_metadata": False,
        "reload": "Start a new Pi session or invoke /skill:damask-skill to verify discovery.",
    },
    "openclaw": {
        "user": "~/.openclaw/skills",
        "project": "skills",
        "vendor_metadata": False,
        "reload": "OpenClaw's watcher normally detects changes on the next agent turn; otherwise start a new session.",
    },
    "hermes": {
        "user": "~/.hermes/skills",
        "project": ".hermes/skills",
        "vendor_metadata": False,
        "reload": "For project scope, run 'hermes skills trust <project>' before loading the skill; then start a new session if needed.",
    },
    "generic": {
        "user": None,
        "project": None,
        "vendor_metadata": False,
        "reload": "Restart or rescan the target agent's skills after installation.",
    },
}
EXCLUDED_TOP_LEVEL = {".git", ".gitignore", ".codegraph"}
EXCLUDED_NAMES = {"__pycache__", ".DS_Store"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".swp", ".swo"}


class InstallError(RuntimeError):
    """Report a safe installation error."""


def contains_control(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def normalize_agent(value: str) -> str:
    try:
        return AGENT_ALIASES[value.lower()]
    except KeyError as error:
        raise argparse.ArgumentTypeError(
            f"unsupported agent {value!r}; choose from {', '.join(sorted(AGENT_ALIASES))}"
        ) from error


def should_include(relative: Path, *, include_vendor_metadata: bool) -> bool:
    if not relative.parts:
        return False
    if relative.parts[0] in EXCLUDED_TOP_LEVEL:
        return False
    if not include_vendor_metadata and relative.parts[0] == "agents":
        return False
    if any(part in EXCLUDED_NAMES for part in relative.parts):
        return False
    if relative.name.endswith("~") or relative.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    return True


def source_files(*, include_vendor_metadata: bool) -> list[Path]:
    files: list[Path] = []
    total_bytes = 0
    for path in sorted(SKILL_ROOT.rglob("*")):
        relative = path.relative_to(SKILL_ROOT)
        if not should_include(relative, include_vendor_metadata=include_vendor_metadata):
            continue
        if path.is_symlink():
            raise InstallError(f"source contains a symbolic link: {relative}")
        if path.is_file():
            files.append(relative)
            total_bytes += path.stat().st_size
            if len(files) > MAX_FILES or total_bytes > MAX_TOTAL_BYTES:
                raise InstallError("source exceeds installer file-count or size limits")
    required = {Path("SKILL.md"), Path("scripts/install_skill.py")}
    missing = sorted(str(path) for path in required - set(files))
    if missing:
        raise InstallError(f"source is missing required files: {', '.join(missing)}")
    return files


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest(root: Path, files: Iterable[Path]) -> dict[str, str]:
    return {relative.as_posix(): sha256(root / relative) for relative in files}


def check_no_symlink_components(path: Path) -> None:
    candidate = path.expanduser().absolute()
    existing: list[Path] = []
    current = candidate
    while True:
        if current.exists() or current.is_symlink():
            existing.append(current)
        if current.parent == current:
            break
        current = current.parent
    for component in reversed(existing):
        if component.is_symlink():
            raise InstallError(f"destination path contains a symbolic link: {component}")


def target_root(agent: str, scope: str, project: Path | None, destination: Path | None) -> Path:
    if destination is not None:
        root = destination.expanduser()
    else:
        template = TARGETS[agent][scope]
        if template is None:
            raise InstallError("--destination is required for the generic agent")
        if scope == "user":
            root = Path(str(template)).expanduser()
        else:
            base = (project or Path.cwd()).expanduser()
            root = base / str(template)
    if contains_control(str(root)):
        raise InstallError("destination cannot contain control characters")
    return root.absolute()


def validate_source_name() -> None:
    try:
        text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    except OSError as error:
        raise InstallError(f"cannot read SKILL.md: {error}") from error
    name = ""
    if text.startswith("---\n"):
        for line in text.split("---\n", 2)[1].splitlines():
            if line.startswith("name:"):
                name = line.partition(":")[2].strip()
                break
    if name != SKILL_NAME:
        raise InstallError(f"SKILL.md name must be {SKILL_NAME!r}, found {name!r}")


def install(
    *,
    agent: str,
    scope: str,
    project: Path | None,
    destination: Path | None,
    apply: bool,
    replace: bool,
) -> dict[str, Any]:
    validate_source_name()
    include_vendor_metadata = bool(TARGETS[agent]["vendor_metadata"])
    files = source_files(include_vendor_metadata=include_vendor_metadata)
    root = target_root(agent, scope, project, destination)
    target = root / SKILL_NAME
    source_resolved = SKILL_ROOT.resolve()
    target_resolved = target.resolve(strict=False)
    if target_resolved == source_resolved or source_resolved in target_resolved.parents:
        raise InstallError("destination cannot be the source skill or a directory inside it")
    check_no_symlink_components(root)
    if target.exists() and not replace:
        raise InstallError(f"destination already exists; use --replace to back it up first: {target}")
    if target.is_symlink():
        raise InstallError(f"destination is a symbolic link: {target}")

    source_manifest = manifest(SKILL_ROOT, files)
    result: dict[str, Any] = {
        "agent": agent,
        "scope": scope,
        "mode": "apply" if apply else "dry-run",
        "source": str(source_resolved),
        "skills_root": str(root),
        "target": str(target),
        "file_count": len(files),
        "total_bytes": sum((SKILL_ROOT / path).stat().st_size for path in files),
        "included_vendor_metadata": include_vendor_metadata,
        "excluded": [".git", ".gitignore", ".codegraph", "cache/temp files"] + ([] if include_vendor_metadata else ["agents/"]),
        "backup": None,
        "reload": TARGETS[agent]["reload"],
    }
    if agent == "openclaw":
        result["native_alternative"] = (
            "openclaw skills install ./path/to/damask-skill --as damask-skill "
            "(add --global for the shared managed store)"
        )
    if not apply:
        return result

    root.mkdir(parents=True, exist_ok=True)
    check_no_symlink_components(root)
    staging = root / f".{SKILL_NAME}.tmp-{uuid.uuid4().hex}"
    backup: Path | None = None
    try:
        staging.mkdir(mode=0o700)
        for relative in files:
            source = SKILL_ROOT / relative
            destination_path = staging / relative
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination_path)
        installed_manifest = manifest(staging, files)
        if installed_manifest != source_manifest:
            raise InstallError("staged copy verification failed")
        if target.exists():
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup = root / f"{SKILL_NAME}.backup-{stamp}-{uuid.uuid4().hex[:8]}"
            os.replace(target, backup)
        os.replace(staging, target)
        if manifest(target, files) != source_manifest:
            raise InstallError("installed copy verification failed")
    except Exception:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        if target.exists():
            failed = root / f".{SKILL_NAME}.failed-{uuid.uuid4().hex}"
            os.replace(target, failed)
        if backup is not None and backup.exists():
            os.replace(backup, target)
        raise
    result["backup"] = str(backup) if backup is not None else None
    result["manifest_verified"] = True
    return result


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Install damask-skill for Codex, Claude Code, Pi, OpenClaw, Hermes, or another compatible agent. Dry-run by default."
    )
    p.add_argument("--agent", type=normalize_agent, help="target agent")
    p.add_argument("--scope", choices=("user", "project"), default="user")
    p.add_argument("--project", type=Path, help="project/workspace root for project scope")
    p.add_argument("--destination", type=Path, help="explicit skills root; damask-skill is appended")
    p.add_argument("--apply", action="store_true", help="perform the installation")
    p.add_argument("--replace", action="store_true", help="back up and replace an existing installation")
    p.add_argument("--list-targets", action="store_true", help="list supported agents and default roots")
    p.add_argument("--json", action="store_true", help="emit JSON")
    return p


def print_result(result: dict[str, Any]) -> None:
    print(f"Mode: {result['mode']}")
    print(f"Agent: {result['agent']} ({result['scope']} scope)")
    print(f"Target: {result['target']}")
    print(f"Files: {result['file_count']} ({result['total_bytes']} bytes)")
    print(f"Vendor metadata included: {'yes' if result['included_vendor_metadata'] else 'no'}")
    if result.get("backup"):
        print(f"Backup: {result['backup']}")
    if result["mode"] == "dry-run":
        print("No files were changed. Add --apply to install.")
    else:
        print("Installed copy verified.")
    print(result["reload"])
    if result.get("native_alternative"):
        print(f"OpenClaw native alternative: {result['native_alternative']}")


def main() -> int:
    args = parser().parse_args()
    try:
        if args.list_targets:
            listing = {
                name: {
                    "user_skills_root": data["user"],
                    "project_skills_root": data["project"],
                    "includes_agents_metadata": data["vendor_metadata"],
                }
                for name, data in TARGETS.items()
            }
            if args.json:
                print(json.dumps(listing, indent=2, sort_keys=True))
            else:
                for name, data in listing.items():
                    print(f"{name}: user={data['user_skills_root'] or 'explicit --destination'}, project={data['project_skills_root'] or 'explicit --destination'}")
            return 0
        if args.agent is None:
            raise InstallError("--agent is required unless --list-targets is used")
        if args.project is not None and args.scope != "project":
            raise InstallError("--project requires --scope project")
        if args.replace and not args.apply:
            raise InstallError("--replace requires --apply")
        result = install(
            agent=args.agent,
            scope=args.scope,
            project=args.project,
            destination=args.destination,
            apply=args.apply,
            replace=args.replace,
        )
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print_result(result)
        return 0
    except (InstallError, OSError, shutil.Error) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
