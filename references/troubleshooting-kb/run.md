# DAMASK KB — `run` (running the simulation: solver choice, restart, capabilities, interop)

Scope: launching/executing simulations, restart workflow, solver capability & limitations, debugging builds, external-solver integration at runtime.
Use: query by symptom (restart error, "not possible", interop) or by keyword (restart, solver, element type, INP, Mentat).

---

### Torsional load with spectral/grid solver — not possible · [#5](https://github.com/damask-multiphysics/DAMASK/discussions/5)
**Problem:** Wants torsional loading with the spectral solver.
**Fix / steps:** No fix — **not supported**. The spectral/grid solver is inherently periodic; a torsionally deformed RVE cannot tile space, so torsion is incompatible with periodic BCs.

### Explicit high-strain-rate (e.g. laser peening) — not supported · [#20](https://github.com/damask-multiphysics/DAMASK/discussions/20)
**Problem:** Wants ABAQUS/Explicit-style high-strain-rate CPFEM.
**Fix / steps:** No — DAMASK has **no explicit solver**.

### Restart HDF5 error when regridding / re-running increments · [#30](https://github.com/damask-multiphysics/DAMASK/discussions/30)
**Problem:** Restart fails because DAMASK tries to **rewrite an already-recorded increment** in `result.hdf5`.
**Fix / steps:**
1. Understand files: `f_out` = result write frequency; `f_restart` = restart-file write frequency (always overwrites `*_restart.hdf5`).
2. If `f_out` is denser than `f_restart`, restart re-writes existing increments → HDF5 error.
3. Delete recorded load increments **after** `n_restart` in `result.hdf5`, then restart.
4. Regridding: old `MarDiehl/regridding` is outdated; use `MarDiehl/regrid`.

### Step-by-step debugging of `DAMASK_grid` iterations · [#33](https://github.com/damask-multiphysics/DAMASK/discussions/33)
**Problem:** Wants to inspect variables per iteration with gdb; symbol/step control unavailable in the binary.
**Fix / steps:**
1. Build DAMASK yourself in debug mode: `make BUILD_TYPE=debug`.
2. Prerequisite: know how to build PETSc.

### Start a new computation from a previous one (restart) · [#35](https://github.com/damask-multiphysics/DAMASK/discussions/35)
**Problem:** How to continue a finished run with added load steps without repeating it.
**Fix / steps:**
1. In `load.yaml` set `f_restart: N` (write restart snapshots); note the last `n_restart`.
2. Append the extra load step to `load.yaml`.
3. Run: `DAMASK_grid -g geom.vti -l load.yaml -m material.yaml -r n_restart`.
4. Restart refers to the **restart file** (per `f_restart`), **not** the last `result.hdf5` recording.
5. Gotcha: `H5Gcreate2()` error on 3.0.0-beta — 3.0.1 fixed it; docs now show `-r` takes an int.

### Restart after an accidental interruption · [#39](https://github.com/damask-multiphysics/DAMASK/discussions/39)
**Problem:** `--restart 4500` → `could not open file: *_restart.hdf5`.
**Fix / steps:** No restart file was ever written — you must set `f_restart` in `load.yaml` **before** the original run so a `*_restart.hdf5` exists; pick the restart increment from that file.

### Element type choice (grid vs mesh solver) · [#45](https://github.com/damask-multiphysics/DAMASK/discussions/45)
**Problem:** What is the default element type / how to change it?
**Fix / steps:**
1. `DAMASK_mesh` (FEM): element type is chosen by your **meshing in MSC.Marc**.
2. `DAMASK_grid` (spectral): each cell is a hexahedron with **one evaluation point at its centre** (≈ linear hex with reduced integration); no element-type switch.

### Convert DAMASK model (.vti/.yaml) to ABAQUS INP · [#58](https://github.com/damask-multiphysics/DAMASK/discussions/58)
**Problem:** Wants to export a DAMASK model as an ABAQUS `.inp`.
**Fix / steps:**
1. Grid solver operates on regular grids → **importing arbitrary INP geometry is not possible**; mesh solver still in progress.
2. Workaround used by OP: extract VTI data and write the INP with a custom Python script.

### Restart of a 2-step load gives different results · [#71](https://github.com/damask-multiphysics/DAMASK/discussions/71)
**Problem:** Stress drops when restarting step 2 separately vs running both steps continuously.
**Fix / steps:**
1. Cause: the 2nd load step was **already executed in the first run**, so restart acts on the tail of the same loadcase.
2. Split loadcases: run step 1 with `load-short.yaml` (only step 1), restart with the full `load.yaml` at the right increment.
3. Known bug: **stress BC** computation — use `P` instead of `P_dot`; issue opened by maintainers.

### MSC Marc/Mentat: how to attach `material.yaml` · [#96](https://github.com/damask-multiphysics/DAMASK/discussions/96)
**Problem:** Can't find a way to import `material.yaml` in Mentat (only `.umt/.ume` offered).
**Fix / steps:** No need to specify the material file in Mentat — DAMASK **expects a `material.yaml` to be present**. Follow the official "Setting up a model in MSC.Mentat" usage page.
