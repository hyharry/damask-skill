# DAMASK KB — `debug` (errors, crashes, build failures, convergence)

Scope: numbered error codes, segfaults, HDF5/Fortran build errors, convergence/cutback failures, install/patch problems.
Use: query by **error code** (402, 613, 706, 844, 950, 100, 155, 211) or symptom (segfault, type mismatch, killed, not converging).

---

### Error: `Attempting to allocate already allocated variable 'a_ns'` (phenopowerlaw, multi-phase) · [#7](https://github.com/damask-multiphysics/DAMASK/discussions/7)
**Problem:** Multi-phase phenopowerlaw crashes in `phase_mechanical_plastic_phenopowerlaw.f90` (line ~175).
**Fix / steps:**
1. Known **bug fixed in the development version** — upgrade to the next release.
2. Source users: apply the upstream fix and recompile.

### Build against central PETSc/HDF5: `Cannot open module file 'hdf5.mod'` · [#11](https://github.com/damask-multiphysics/DAMASK/discussions/11)
**Problem:** Source build against site PETSc/HDF5 can't find `hdf5.mod`.
**Fix / steps:**
1. Confirm HDF5 was built **with Fortran bindings** (`nm -gC libhdf5.so | grep -i fortran`).
2. Add the dir containing `hdf5.mod` to the compile **include** paths.
3. PETSc must be aware of HDF5 (and FFTW); otherwise manually tweak the **root** `CMakeLists.txt` (not `src/CMakeLists.txt`).

### Segfault on reading a large `material.yaml` · [#25](https://github.com/damask-multiphysics/DAMASK/discussions/25)
**Problem:** `Segmentation fault` right after `reading material configuration`.
**Fix / steps:**
1. Usually **out of memory**, or a **stack-size** limit.
2. Try `ulimit -s unlimited` before running (also see #49).

### Editable/PEP-440 install fails: version string · [#37](https://github.com/damask-multiphysics/DAMASK/discussions/37)
**Problem:** `pip install -e .` fails because the dev version from `git describe` isn't PEP 440.
**Fix / steps:**
1. For a plain dev use, just add the module dir to `PYTHONPATH`.
2. For a pip install, **fix the `VERSION` file** manually: `sed 's/-/.dev/;s/-g/+/'` on it.

### `Type mismatch` during cmake build (gfortran ≥ 10 + MPICH) · [#38](https://github.com/damask-multiphysics/DAMASK/discussions/38)
**Problem:** Compiling grid/mesh solver fails with `Type mismatch` / implicit `mpi_bcast`.
**Fix / steps:**
1. Add the relaxation flag when invoking CMake: `-DBUILDCMD_POST='-fallow-argument-mismatch -Wno-pedantic'` (first of the two cmake calls).
2. Or downgrade gfortran (OP used 9.5).
3. Also update PETSc (3.0.0 does not work with newest PETSc 3.22 → use 3.0.1 / older PETSc).
4. Side note: an HDF5 `H5Gcreate2` error during a run usually means the simulation **did not converge**, not a build issue.

### `Recursive call to nonrecursive procedure 'h5open_f'` (HDF5 parallel) · [#40](https://github.com/damask-multiphysics/DAMASK/discussions/40)
**Problem:** `H5_ff.F90` runtime error when running nonlocal compute.
**Fix / steps:** Likely an HDF5 parallel/threading build issue. *(OP double-posted; issue folded into #38's thread — ensure HDF5 is built consistently and PETSc/config are compatible.)*

### Segfault "reading material configuration" (large config) · [#49](https://github.com/damask-multiphysics/DAMASK/discussions/49)
**Problem:** `Segmentation fault (signal 11)` right after reading a large material config.
**Fix / steps:** Add **`ulimit -s unlimited`** before running (or in the job `.sh`) → raises the stack limit. This fixed it.

### Error 402 (`invalid orientation specified / fromMatrix`) at large deformation · [#50](https://github.com/damask-multiphysics/DAMASK/discussions/50)
**Problem:** Shear run terminates around strain ≈1 with `error 402`.
**Fix / steps:**
1. Cause: cells distort too much → orientation→matrix conversion becomes invalid; convergence past strain ~1 is intrinsically hard.
2. Workaround: enable **regridding** (`damask.grid_filters.regrid()`) to keep cells well-shaped.
3. Caveat: after regrid the restart currently resumes from the pre-regrid state — check workflow ordering.

### Mesh solver: PETSc `SEGV` at `FEM_mech init` · [#68](https://github.com/damask-multiphysics/DAMASK/discussions/68)
**Problem:** `DAMASK_mesh` crashes in `FEM_mech init` (segfault) across compilers.
**Fix / steps:**
1. Mesh solver is less tested than grid; use a **recent gfortran + recent PETSc**.
2. Old gfortran (9.5/11.4) reproduce it — moving to a current compiler is the main suggestion; share input files to debug further.

### Error 402 then Error 100 (`could not open *_restart.hdf5`) · [#72](https://github.com/damask-multiphysics/DAMASK/discussions/72)
**Problem:** 402 at large grid; after enabling regrid → error 100 about missing restart file.
**Fix / steps:**
1. Error 100 = **no restart file exists** because `f_restart` was never set.
2. In `load.yaml` add `f_restart: N` (e.g. equal to `f_out`) so a `*_restart.hdf5` is written, then run with `-r N`.
3. Error 402 root cause (grid-size dependent) still open; regridding remains the mitigation.

### Error 950 near the end of a large simulation · [#75](https://github.com/damask-multiphysics/DAMASK/discussions/75)
**Problem:** 128³ grid hits `error 950` near completion; 402 earlier.
**Fix / steps:**
1. 950 = **max cutbacks exceeded** and appears tied to **memory pressure** on big grids.
2. Mitigate: reduce resolution (100³ ran fine), free RAM, or use a node with more memory.
3. Not fully root-caused in-thread.

### Error 402 due to wrong **units** in material.yaml · [#78](https://github.com/damask-multiphysics/DAMASK/discussions/78)
**Problem:** `error 402 invalid orientation / fromMatrix` after ~11 iterations.
**Fix / steps:**
1. OP's cause was **inconsistent units** in the constitutive model in `material.yaml` — fix the units.
2. Other contributors hit 402 from **excessive cell distortion** (see #50).

### Error 706 `type mismatch ... not a scalar` · [#82](https://github.com/damask-multiphysics/DAMASK/discussions/82)
**Problem:** `Error 706 type mismatch in YAML data node "[0.001,0.001,0.0,0.001]" is not a scalar`.
**Fix / steps:** Per-slip-family parameters must be a **flat list, not a list of lists**:
`dot_gamma_0_sl: [0.001,0.001,0.0,0.001]` (not `[[...]]`); same for `n_sl`. Compare with `config/phase/mechanical/plastic/phenopowerlaw_Ti.yaml`.

### Error 950 with a fresh/beginner setup · [#98](https://github.com/damask-multiphysics/DAMASK/discussions/98)
**Problem:** First test sim fails with 950 (convergence/cutback).
**Fix / steps:** *(Unsolved in-thread.)* See #75 — 950 = max cutbacks exceeded; reduce resolution / ease the load step / check BCs and material params.

### Nonlocal simulation gets killed (no OOM) · [#100](https://github.com/damask-multiphysics/DAMASK/discussions/100)
**Problem:** Nonlocal run is killed though RAM is plentiful (~256 GB); also fails with phenopowerlaw.
**Fix / steps:** *(Unsolved.)* Check for a **wall-time/CPU limit** on the cluster, `ulimit`s, and thread count; verify the material config isn't pathological. Cross-ref nonlocal config (#4, #102).

### `MSC_modifications.py` targets wrong Marc version (2025.2) · [#104](https://github.com/damask-multiphysics/DAMASK/discussions/104)
**Problem:** Patching script looks for 2024.1; no DAMASK menu appears in Mentat 2025.2.
**Fix / steps:**
1. Run `MSC_modifications.py --help`; set **`--marc-root` and `--marc-version`** explicitly.
2. To re-apply cleanly: run the script with **`uninstall`** first, then patch again.
3. Also verify the **license file** is reachable by the script (OP's failure was a licensing issue).

### Mentat: BC warnings "no entities found / no DOF prescribed" · [#107](https://github.com/damask-multiphysics/DAMASK/discussions/107)
**Problem:** Job checker ignores BCs (`apply1/apply2`).
**Fix / steps:** This is a **Marc/Mentat** error, not DAMASK. First get the model running with a **standard Marc material**, then switch to the DAMASK material.

### Error 211 `material parameter out of bounds: rho` (dislotwin) · [#112](https://github.com/damask-multiphysics/DAMASK/discussions/112)
**Problem:** `Error 211: material parameter out of bounds: rho` with dislotwin TWIP steel.
**Fix / steps:** *(Unsolved in-thread.)* One of the dislocation-density params (`rho_dip_0`/`rho_mob_0`) is outside the allowed range — verify against the dislotwin reference/example values (see #110, #19).
