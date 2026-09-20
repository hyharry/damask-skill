# DAMASK Skill

A compact, safety-first skill for people and AI agents working with DAMASK. It helps inspect an existing setup, stage a reproducible case, prepare a command, run only with explicit authorization, and verify a scientific result rather than just a process launch.

**Scope:** DAMASK Grid/Mesh/MSC Marc guidance, Docker/Podman/native command preparation, staged examples, and result handoff. It does not invent material models, calibration, boundary conditions, paths, versions, or container images.

## Safe quick start

Run these commands from this repository. Bundled examples are read-only reference data; stage a copy before editing or executing.

```sh
# 1. Inspect only
python3 scripts/example_library.py describe grid-tension-small

# 2. Stage an editable case (does not run DAMASK)
python3 scripts/example_library.py stage grid-tension-small --destination ./case
cd case

# 3. Dry run: validate inputs and print the command (no solver launch)
python3 ../scripts/run_solver.py \
  --solver grid --geom 20grains16x16x16.vti \
  --load tensionX.yaml --material material.yaml --numerics numerics.yaml

# 4. Execute only after the user explicitly authorizes it
python3 ../scripts/run_solver.py \
  --solver grid --geom 20grains16x16x16.vti \
  --load tensionX.yaml --material material.yaml --numerics numerics.yaml \
  --execute

# 5. Verify: exit status, solver log, and the expected HDF5 result
```

Before step 4, inspect the runtime's `--help`, record the working directory/resources/inputs, and confirm the expected result name. See [SKILL.md](SKILL.md) and the [autonomous checklist](references/autonomous-checklist.md) for the full gate.

## Install

The standard-library installer is a dry run unless `--apply` is present:

```sh
python3 scripts/install_skill.py --list-targets
python3 scripts/install_skill.py --agent openclaw --scope project --project /path/to/workspace
python3 scripts/install_skill.py --agent openclaw --scope project --project /path/to/workspace --apply
```

It supports Codex, Claude Code, Pi, OpenClaw, Hermes, and an explicit generic destination. Existing installations require `--replace --apply` and are backed up first. See [backend compatibility](references/backend-compatibility.md).

## Verified DAMASK 3.1.0 Docker example

A bounded live run on `mapc4_wsl2` used the already-local, inspected image `damaskmultiphysics/damask-grid:3.1.0` (image ID beginning `sha256:f9b9d085e0c1`) and deliberately disabled pulls. From the prepared case directory, its solver command was:

```sh
IMAGE=damaskmultiphysics/damask-grid:3.1.0
docker image inspect "$IMAGE"
docker run --rm --pull=never \
  -v "$PWD:/wd" -w /wd -e OMP_NUM_THREADS=2 \
  "$IMAGE" \
  --geom 20grains16x16x16.vti --load load_uniaxial_short.yaml \
  --material material_ferrite_steel.yaml --numerics numerics.yaml \
  --jobname ferritic_steel_16cubed
```

For Python postprocessing in that image, override the solver entrypoint explicitly:

```sh
docker run --rm --pull=never --entrypoint python \
  -v "$PWD:/wd" -w /wd "$IMAGE" plot_results.py
```

That run exited 0, logged 10/10 converged increments, and wrote `ferritic_steel_16cubed.hdf5`. Its reported checks were `mean(F11)-1 = 0.005` and `mean(P11) ≈ 1035 MPa`; these are the stated component-average calculations, not a general calibration or a claim that `P` is Cauchy stress.

**Compatibility note:** this is narrow evidence for that pinned local Docker image and prepared case on `mapc4_wsl2`; validate every other input, API, schema, and runtime with the installed DAMASK version.

## Autonomy boundaries

- Default to inspection and dry runs. Execute only on explicit request after all prerequisites pass.
- Never change physics, numerical tolerances, or boundary conditions merely to obtain convergence.
- Preserve the command, image reference, input hashes, log, result path, and postprocessing command; report named stress/strain measures and averaging.
- For autonomous work, stop at a dry run whenever a scientific decision, provenance, material-ID mapping, or boundary-condition component is unknown.

## Evaluate responses

```sh
python3 scripts/run_evals.py validate
python3 scripts/run_evals.py list
python3 scripts/run_evals.py prompt basic-grid-dry-run
python3 scripts/run_evals.py grade basic-grid-dry-run response.txt
```

## Workflow improvement ideas

1. **Run receipt:** add an optional machine-readable receipt writer for the final command, image ID, hashes, status, and result path.
2. **Schema preflight:** add a read-only DAMASK 3.1 input inspector for material-ID and load-matrix checks before a solver run.
3. **Result smoke check:** provide a small `damask.Result(...)` verifier that confirms increments and named output fields without mutating the HDF5 file.
