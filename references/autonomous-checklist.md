# Bounded autonomous DAMASK checklist

Use only after the user explicitly authorizes unattended setup or execution. A failed or unknown applicable item blocks launch. Inspect missing facts when possible; ask only for decisions or authorization that cannot be recovered from the task and files. Prepare a dry run if its required files/options are known. Existing execution authorization remains valid within its stated scope.

## Before launch

- Host, working directory, solver, runtime, DAMASK version, and executable `--help` are inspected.
- Threads, MPI ranks, wall-time expectation, storage expectation, and stop conditions are recorded.
- Geometry, load, material, and optional numerics files are readable from the effective work directory.
- Container image is already local and uses an inspected non-`latest` tag or digest.
- A complete case was staged, or every custom fragment has provenance. Long arrays are copied exactly—not manually counted or normalized.
- A created or transformed input has retained sources, a deterministic generation command or script, and source/output hashes. Never infer a material model, units, phase mapping, texture, or calibration target from a material name alone.
- Geometry material IDs are in range for the zero-based `material.yaml` entries; every referenced phase and homogenization name exists. The load matrix was inspected so that each `x` component, prescribed component, and stress-controlled component is explicitly accounted for.
- Geometry is described accurately: an `Nz=1` regular grid is a one-voxel-thick 3-D grid, not proof of a 2-D model or plane strain.
- Boundary-condition language matches the matrices. In particular, unknown lateral deformation with zero lateral stress is uniaxial-stress loading, not plane strain.
- No constitutive parameter, boundary condition, or numerical tolerance was changed merely to make a failed case converge.

## Launch and failure handling

- Print and retain the exact command before execution.
- Use wrappers that return the solver's real status; with shell pipelines, enable `pipefail` and preserve the solver status.
- Log stdout/stderr without masking failure.
- On failure, preserve inputs, log, status/restart files, and partial results. Retry only within the authorized scope and stop conditions, using unchanged scientific inputs or a schema correction reproduced exactly from an inspected compatible source; record any correction's diff and hashes and pass the version-specific validation gate. The launcher's path/option dry run alone is insufficient. Ask before changing geometry, physics, or numerics.

## Result and report gate

- Require status zero, a successful solver termination in the log, and the expected HDF5 result.
- Retain input hashes, command, image reference, log, result path, and postprocessing command together.
- Start postprocessing with `damask.Result(...)` and check the installed API.
- Name stress and strain measures explicitly: for example first Piola–Kirchhoff `P11`, Cauchy `σ11`, engineering strain, or logarithmic strain.
- Do not label first Piola–Kirchhoff `P` as Cauchy stress. If reporting `mean(F11)-1`, state that exact component-average calculation and do not present it as an unqualified macroscopic strain measure.
- State whether a value is local, volume averaged, or a measure calculated from the averaged tensor.
- Derive plot coordinates from geometry size/cell metadata; do not relabel voxel indices with guessed physical units.
- Validate hand-written tensor identities against the DAMASK API or a standard identity. For symmetric Cauchy stress, the component von Mises expression uses `6*(σ12²+σ23²+σ31²)` inside the half-sum form.
- Separate solver convergence from scientific validation. Label uncalibrated examples and small smoke tests accordingly.
