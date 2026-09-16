# Official DAMASK usage reference

Condensed from official DAMASK documentation accessed 2026-09-16. Recheck the linked current pages for version-sensitive details.

## Solver and environment matrix

| Choice | Use | Constraint |
|---|---|---|
| Grid | Regular `.vti` geometry; spectral FFT/FEM; mixed periodic boundaries | MPI decomposes the z-axis into roughly equal layers |
| Mesh | Unstructured `.msh` geometry; FEM | Officially under development, with feature and convergence limitations |
| MSC Marc | Commercial FEM and complex boundary conditions | Licensed software and installed DAMASK coupling required |
| Linux package | Full open-source suite | Distribution/version support varies |
| Conda | Full suite on Linux/macOS | Native Windows lacks solver dependencies |
| PyPI | Python pre/post-processing | Does not install solvers |
| Containers | Solvers and processing; Docker is cross-platform, Podman is Linux-only | Mount inputs and use container-visible paths |
| WSL | Solvers or source builds on Windows | Requires a Unix environment |
| Source | Development or MSC Marc coupling | Expert path with PETSc and compiled dependencies |

The workflow is solver selection, pre-processing, simulation, then post-processing. Material-point configuration uses YAML. Grid and mesh runs also require geometry and load files.

## Native commands

```sh
damask_grid --load load.yaml --geom grid.vti --material material.yaml
damask_mesh --load load.yaml --geom mesh.msh --material material.yaml
```

Mandatory flags are `--load/-l`, `--geom/-g`, and `--material/-m`. Common options are `--numerics/-n`, `--jobname/-j`, a working-directory option, and `--help/-h`. Grid also supports `--restart/-r N` from `{jobname}_restart.hdf5` in the working directory when the load case produced snapshots. The default job name is `{grid}_{load}_{material}`; an explicit `--jobname` changes the expected snapshot name. Confirm that the requested increment was written, and confirm long-option spelling with the installed `--help`; documentation and releases can differ.

```sh
OMP_NUM_THREADS=4 damask_grid --load load.yaml --geom grid.vti --material material.yaml
mpiexec -n 4 damask_grid --load load.yaml --geom grid.vti --material material.yaml
```

MPI and OpenMP can be combined. Mesh MPI partitions by approximately equal element counts.

## Installation and containers

```sh
conda install -c conda-forge damask
pip3 install damask
```

`pip` installs processing tools only. Official container images include:

- `damaskmultiphysics/damask-grid:latest`
- `damaskmultiphysics/damask-mesh:latest`
- `damaskmultiphysics/python-damask:latest`
- `damaskmultiphysics/jupyter-damask:latest`

Example grid container:

```sh
docker run --rm -it -v "${PWD}:/wd" -e OMP_NUM_THREADS=4 \
  damaskmultiphysics/damask-grid:latest \
  --load load.yaml --geom grid.vti --material material.yaml
```

The Jupyter image exposes port `8805`; if occupied, change only the host side of `HOST_PORT:8805`. On Windows, run official container examples in PowerShell or Windows Terminal, not `cmd.exe`. Keep Windows path syntax in PowerShell and WSL path syntax in WSL; do not mix them. The official container page lists Podman support for Linux only.

The bundled `scripts/run_solver.py` accepts Docker and Podman for grid/mesh runs. It deliberately rejects container MPI because host networking, MPI libraries, schedulers, and image builds vary. Use native MPI or construct a site-specific container command only after inspecting that environment.

The helper requires an explicit image tag or digest, verifies that it is already local before execution, and refuses implicit pulls. Prefer an installed-version-matched tag or immutable digest; do not infer compatibility from `:latest`.

## MSC Marc essentials

- Couple DAMASK through the `hypela2` user subroutine in `DAMASK_Marc.f90`.
- Keep `material.yaml`, optional `numerics.yaml`, and Marc inputs in the current working directory.
- Assign material through `State Variable 2`; DAMASK material IDs are zero-based.
- Use Marc `State Variable 1` in kelvin for temperature-aware models.
- Use Updated Lagrange, disable switching to Total Lagrange, and select Multiplicative Decomposition.
- Keep Marc thermal properties consistent with `material.yaml`; DAMASK does not check them.
- Restart only from the last converged increment.

```python
import damask

solver = damask.solver.Marc()
solver.submit_job(model=modelname, job=jobname, domains=num_domains)
```

## Python processing

Use `ConfigMaterial`, `GeomGrid`, `LoadcaseGrid`, `Rotation`, and `seeds` for preprocessing. Use `Result`, `mechanics`, `tensor`, `Orientation`, and `Colormap` for post-processing.

```python
import damask

result = damask.Result("job.hdf5")
print(result)
last = result.view(increments=-1)
```

Use Python help for the installed API: `help(damask.GeomGrid.from_Voronoi_tessellation)`.

## Sources

- https://damask-multiphysics.org/documentation/usage.html
- https://damask-multiphysics.org/installation/index.html
- https://damask-multiphysics.org/installation/package_manager
- https://damask-multiphysics.org/installation/container.html
- https://damask-multiphysics.org/installation/pypi.html
- https://damask-multiphysics.org/installation/source_code.html
- https://damask-multiphysics.org/documentation/processing_tools/index.html
