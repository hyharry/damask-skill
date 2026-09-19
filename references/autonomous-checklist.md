# Bounded autonomous DAMASK checklist

Use only after the user explicitly authorizes unattended setup or execution. A failed or unknown item means stop at a dry run and ask for the missing scientific decision.

## Before launch

- Host, working directory, solver, runtime, DAMASK version, and executable `--help` are inspected.
- Threads, MPI ranks, wall-time expectation, storage expectation, and stop conditions are recorded.
- Geometry, load, material, and optional numerics files are readable from the effective work directory.
- Container image is already local and uses an inspected non-`latest` tag or digest.
- A complete case was staged, or every custom fragment has provenance. Long arrays are copied exactly—not manually counted or normalized.
- Geometry is described accurately: an `Nz=1` regular grid is quasi-2D, while the solver remains 3-D and periodic.
- Boundary-condition language matches the matrices. In particular, unknown lateral deformation with zero lateral stress is uniaxial-stress loading, not plane strain.
- No constitutive parameter, boundary condition, or numerical tolerance was changed merely to make a failed case converge.

## Launch and failure handling

- Print and retain the exact command before execution.
- Use wrappers that return the solver's real status; with shell pipelines, enable `pipefail` and preserve the solver status.
- Log stdout/stderr without masking failure.
- On failure, preserve inputs, log, status/restart files, and partial results. Retry only a smaller equivalent case or a schema correction reproduced exactly from an inspected compatible source. Ask before changing physics or numerics.

## Result and report gate

- Require status zero, a successful solver termination in the log, and the expected HDF5 result.
- Retain input hashes, command, image reference, log, result path, and postprocessing command together.
- Start postprocessing with `damask.Result(...)` and check the installed API.
- Name stress and strain measures explicitly: for example first Piola–Kirchhoff `P11`, Cauchy `σ11`, engineering strain, or logarithmic strain.
- State whether a value is local, volume averaged, or a measure calculated from the averaged tensor.
- Derive plot coordinates from geometry size/cell metadata; do not relabel voxel indices with guessed physical units.
- Validate hand-written tensor identities against the DAMASK API or a standard identity. For symmetric Cauchy stress, the component von Mises expression uses `6*(σ12²+σ23²+σ31²)` inside the half-sum form.
- Separate solver convergence from scientific validation. Label uncalibrated examples and small smoke tests accordingly.
