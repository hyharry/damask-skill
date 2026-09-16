#!/usr/bin/env python3
"""Validate, print, and optionally run a DAMASK grid or mesh command."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys


GEOMETRY_SUFFIX = {"grid": ".vti", "mesh": ".msh"}
YAML_SUFFIXES = {".yaml", ".yml"}
IMAGE_DIGEST_PATTERN = re.compile(r"^[^@]+@sha256:[0-9a-f]{64}$")


def contains_control(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)


def powershell_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def nonnegative_int(value: str) -> int:
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be a non-negative integer")
    return number


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Build or run a DAMASK grid/mesh command; print only by default."
    )
    p.add_argument("--solver", choices=("grid", "mesh"), required=True)
    p.add_argument("--runtime", choices=("native", "docker", "podman"), default="native")
    p.add_argument("--geom", required=True, type=Path)
    p.add_argument("--load", required=True, type=Path)
    p.add_argument("--material", required=True, type=Path)
    p.add_argument("--numerics", type=Path)
    p.add_argument("--jobname")
    p.add_argument("--workdir", type=Path, default=Path.cwd())
    p.add_argument("--threads", type=positive_int, default=1)
    p.add_argument("--mpi", type=positive_int, default=1)
    p.add_argument("--restart", type=nonnegative_int)
    p.add_argument(
        "--restart-increment-confirmed",
        action="store_true",
        help="confirm the requested restart increment was inspected in the matching snapshot",
    )
    p.add_argument(
        "--image",
        help="explicit local container image reference (required for containers)",
    )
    p.add_argument("--execute", action="store_true", help="run after validation")
    return p


def checked_file(path: Path, workdir: Path, label: str) -> Path:
    resolved = path if path.is_absolute() else workdir / path
    resolved = resolved.resolve()
    if not resolved.is_file():
        raise ValueError(f"{label} is not a readable file: {path}")
    try:
        with resolved.open("rb") as stream:
            stream.read(1)
    except OSError as error:
        raise ValueError(f"{label} is not a readable file: {path}") from error
    return resolved


def container_path(path: Path, workdir: Path) -> str:
    try:
        relative = path.relative_to(workdir)
    except ValueError as error:
        raise ValueError(f"container input is outside the mounted workdir: {path}") from error
    return relative.as_posix()


def render(command: list[str], env_prefix: dict[str, str] | None = None) -> str:
    if os.name == "nt":
        return "& " + " ".join(powershell_quote(argument) for argument in command)
    prefix = ""
    if env_prefix:
        prefix = " ".join(f"{key}={shlex.quote(value)}" for key, value in env_prefix.items()) + " "
    return prefix + shlex.join(command)


def build_command(args: argparse.Namespace) -> tuple[list[str], Path, dict[str, str]]:
    workdir = args.workdir.resolve()
    if not workdir.is_dir():
        raise ValueError(f"working directory does not exist: {workdir}")

    files = {
        "geometry": checked_file(args.geom, workdir, "geometry"),
        "load": checked_file(args.load, workdir, "load"),
        "material": checked_file(args.material, workdir, "material"),
    }
    if args.numerics:
        files["numerics"] = checked_file(args.numerics, workdir, "numerics")

    expected_suffix = GEOMETRY_SUFFIX[args.solver]
    if files["geometry"].suffix.lower() != expected_suffix:
        raise ValueError(
            f"{args.solver} geometry must use {expected_suffix}: {args.geom}"
        )
    for label in ("load", "material", "numerics"):
        if label in files and files[label].suffix.lower() not in YAML_SUFFIXES:
            raise ValueError(
                f"{label} input must use .yaml or .yml: {getattr(args, label)}"
            )
    if args.restart is not None and args.solver != "grid":
        raise ValueError("--restart is supported only for the grid solver")
    if args.runtime != "native" and args.mpi != 1:
        raise ValueError("container MPI needs an environment-specific setup; use native MPI here")
    if args.runtime == "native" and args.image:
        raise ValueError("--image requires --runtime docker or --runtime podman")
    if args.runtime != "native" and args.image is None:
        raise ValueError("container runs require an explicit --image; do not guess a mutable tag")
    if args.image is not None and (
        not args.image
        or args.image.startswith("-")
        or any(character.isspace() for character in args.image)
        or contains_control(args.image)
        or len(args.image) > 512
    ):
        raise ValueError(
            "--image must be a valid non-whitespace image reference and cannot start with '-'"
        )
    if args.image is not None:
        final_component = args.image.rsplit("/", 1)[-1]
        if "@" in args.image:
            if IMAGE_DIGEST_PATTERN.fullmatch(args.image) is None:
                raise ValueError(
                    "--image digest must use @sha256:<64 lowercase hex characters>"
                )
        elif ":" not in final_component or final_component.endswith(":latest"):
            raise ValueError("--image must include a non-latest tag or immutable digest")
    if os.name == "nt" and args.runtime == "native":
        raise ValueError("DAMASK solvers are not supported on native Windows; use Docker or WSL")
    if args.runtime == "podman" and not sys.platform.startswith("linux"):
        raise ValueError(
            "Podman support in this launcher is Linux-only; use Docker or a Linux/WSL environment"
        )

    if args.jobname is not None:
        if (
            not args.jobname
            or args.jobname in {".", ".."}
            or "/" in args.jobname
            or "\\" in args.jobname
            or contains_control(args.jobname)
            or len(args.jobname) > 255
        ):
            raise ValueError(
                "--jobname must be a safe file name without paths or control characters"
            )
    if args.restart is None and args.restart_increment_confirmed:
        raise ValueError("--restart-increment-confirmed requires --restart")
    if args.restart is not None and not args.restart_increment_confirmed:
        raise ValueError(
            "--restart requires --restart-increment-confirmed after inspecting the snapshot"
        )
    if args.restart is not None:
        jobname = args.jobname or "_".join(
            files[name].stem for name in ("geometry", "load", "material")
        )
        checked_file(
            workdir / f"{jobname}_restart.hdf5", workdir, "restart snapshot"
        )

    def visible(name: str) -> str:
        if args.runtime == "native":
            return str(files[name])
        return container_path(files[name], workdir)

    solver_args = [
        "--load", visible("load"),
        "--geom", visible("geometry"),
        "--material", visible("material"),
    ]
    if args.numerics:
        solver_args += ["--numerics", visible("numerics")]
    if args.jobname:
        solver_args += ["--jobname", args.jobname]
    if args.restart is not None:
        solver_args += ["--restart", str(args.restart)]

    environment = {"OMP_NUM_THREADS": str(args.threads)}
    if args.runtime == "native":
        command = [f"damask_{args.solver}", *solver_args]
        if args.mpi > 1:
            command = ["mpiexec", "-n", str(args.mpi), *command]
    else:
        command = [
            args.runtime, "run", "--rm", "--pull=never",
            "--volume", f"{workdir}:/wd", "--workdir", "/wd",
            "--env", f"OMP_NUM_THREADS={args.threads}",
            args.image, *solver_args,
        ]
    return command, workdir, environment


def required_executables(args: argparse.Namespace) -> list[str]:
    if args.runtime != "native":
        return [args.runtime]
    required = [f"damask_{args.solver}"]
    if args.mpi > 1:
        required.append("mpiexec")
    return required


def help_preflight(
    args: argparse.Namespace, workdir: Path, environment: dict[str, str]
) -> int:
    if args.runtime == "native":
        name = f"damask_{args.solver}"
        command = [name, "--help"]
    else:
        name = f"{args.runtime} image {args.image}"
        inspected = subprocess.run(
            [args.runtime, "image", "inspect", args.image],
            cwd=workdir,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if inspected.returncode != 0:
            print(
                f"error: container image is not local; refusing an implicit pull: {args.image}",
                file=sys.stderr,
            )
            return inspected.returncode or 2
        command = [
            args.runtime, "run", "--rm", "--pull=never", args.image, "--help"
        ]
    completed = subprocess.run(command, cwd=workdir, env=environment, check=False)
    if completed.returncode != 0:
        print(
            f"error: {name} --help failed with status {completed.returncode}",
            file=sys.stderr,
        )
    return completed.returncode


def main() -> int:
    args = parser().parse_args()
    try:
        command, workdir, environment = build_command(args)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    shown_env = environment if args.runtime == "native" else None
    print(render(command, shown_env))
    if not args.execute:
        return 0

    run_env = os.environ.copy()
    run_env.update(environment)
    for required in required_executables(args):
        if shutil.which(required, path=run_env.get("PATH")) is None:
            print(f"error: executable not found on PATH: {required}", file=sys.stderr)
            return 127
    preflight_status = help_preflight(args, workdir, run_env)
    if preflight_status != 0:
        return preflight_status
    completed = subprocess.run(command, cwd=workdir, env=run_env, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
