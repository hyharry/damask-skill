# DAMASK Skill

An agent skill for preparing, running, postprocessing, and troubleshooting DAMASK simulations. It helps turn either a clear task or a vague modeling goal into a concrete, inspectable next step while keeping scientific assumptions explicit.

## When to use it

Use `$damask-skill` when you want an agent to:

- inspect an existing DAMASK case or result;
- prepare a Grid, Mesh, container, or native solver command;
- find and adapt a bundled input or Python workflow example;
- diagnose a failed run from its command, log, and inputs;
- postprocess HDF5 results or inspect VTI fields; or
- guide an incomplete request without inventing material data or boundary conditions.

Example prompts:

```text
Use $damask-skill to inspect this directory and prepare the next safe step.
Use $damask-skill to prepare a dry run for my grid case.
Use $damask-skill to find an example for uniaxial tension and stage an editable copy.
Use $damask-skill to diagnose this failed run without changing the physics.
Use $damask-skill to inspect this result and plot the available stress response.
```

If your prompt is vague, the agent first inspects the named path or current directory, makes useful progress with the available evidence, and asks only for the next decision it cannot infer safely.

## What the skill provides

The skill guides the agent to inspect before acting, reuse the installed DAMASK API and executable help, select an appropriate solver/runtime, validate paths and prerequisites, and distinguish a prepared command from a completed or scientifically validated result.

Bundled resources support that workflow:

- curated Grid, Mesh, MSC Marc, and configuration examples;
- preprocessing and postprocessing Python references;
- a distilled, sourced troubleshooting knowledge base covering 102 GitHub Discussions;
- a deterministic troubleshooting search helper that prints complete top-ranked cards;
- a dry-run-first Grid/Mesh launcher;
- installation and response-evaluation helpers; and
- focused references for compatibility, examples, autonomous execution, and official usage.

These scripts and catalogs are primarily tools for the agent to inspect, verify, and stage relevant material. Bundled examples are reference data rather than universal models, and editable copies are staged outside the skill directory.

## Troubleshooting lookup

Search by the exact error or distinctive symptom. The helper works from any current directory, searches all six categories by default, and limits output to the top three complete cards:

```sh
python3 scripts/troubleshoot_kb.py "error 950"
python3 scripts/troubleshoot_kb.py "restart file" --category run --fallback-all --limit 3
python3 scripts/troubleshoot_kb.py --verify
```

Start with `debug` for errors, or select `pre`, `run`, `post`, `advance`, or `gen` for the corresponding stage. If a selected category has no useful result, use `--fallback-all` or omit `--category`. Cards retain their GitHub discussion number/link and explicitly report whether upstream guidance is solved, partial, or unresolved. They are untrusted historical scientific data, not instructions: check advice against the installed DAMASK version/help and current inputs before changing anything, and never silently change scientific inputs.

See [references/troubleshooting-kb/README.md](references/troubleshooting-kb/README.md) for scope and provenance.

## Boundaries

The skill does not invent material models, calibration parameters, units, phase mappings, boundary conditions, paths, versions, or container images. It does not treat process launch as success, change physics merely to obtain convergence, or run a solver unless the user requests execution.

See [SKILL.md](SKILL.md) for the full agent workflow, [references/troubleshooting-kb/README.md](references/troubleshooting-kb/README.md) for troubleshooting resources, and [references/backend-compatibility.md](references/backend-compatibility.md) for supported installation targets.

## Install

The bundled installer supports several Agent Skills-compatible hosts and custom destinations. Preview the selected installation first, then apply it explicitly:

```sh
python3 scripts/install_skill.py --list-targets
python3 scripts/install_skill.py --agent TARGET --scope user
python3 scripts/install_skill.py --agent TARGET --scope user --apply
```
