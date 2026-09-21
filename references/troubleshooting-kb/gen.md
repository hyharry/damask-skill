# DAMASK KB — `gen` (general: install, version, docs, integration)

Scope: environment/installation, versioning & updates, documentation requests, toolchain integration (MSC Marc/Mentat, WSL), platform questions.
Use: query by symptom/error or by tool name. Each entry is a compact *Problem → Fix (steps)* card; `#NNN` links to the source discussion.

---

### New to DAMASK — how to start / what files are needed · [#10](https://github.com/damask-multiphysics/DAMASK/discussions/10)
**Problem:** First install; no idea how to use it; tutorial video links broken.
**Fix / steps:**
1. A DAMASK run needs **3 input files**: geometry (`.vti`, references material IDs), material config (`material.yaml`), loadcase (BCs + solver).
2. Read usage docs + Processing Tools docs; work through the Jupyter examples.
3. To hook in your **own solver** → needs development access (private GitLab + CLA).

### `DAMASK_grid: command not found` after `pip install damask` · [#27](https://github.com/damask-multiphysics/DAMASK/discussions/27)
**Problem:** Ran `DAMASK_grid ...` → command not found.
**Fix / steps:**
1. `pip install damask` installs **only the Python (pre/post) tools** — not the solvers.
2. Install the grid binary via package manager (PPA) or build from source.

### Install on linux-aarch64 · [#42](https://github.com/damask-multiphysics/DAMASK/discussions/42)
**Problem:** No conda-forge DAMASK package for aarch64; source install docs thin on PETSc.
**Fix / steps:**
1. Build from source: unpack source → install PETSc → `cmake` solvers → install Python tools.
2. PETSc: `./configure ... --download-hdf5 --download-fftw --download-mpich --download-fblaslapack ...` (full flag list in thread).
3. PETSc has its own good docs; ask the PETSc team for PETSc-specific issues.

### Request: more detailed tutorial / where to set temperature · [#51](https://github.com/damask-multiphysics/DAMASK/discussions/51)
**Problem:** Wants a handbook-style tutorial (e.g. where does temperature go — material.yaml or load.yaml?).
**Fix / steps:** *(unsolved / doc request)*. Temperature is **not** in load.yaml — set as an initial condition on the grid (see `initial_conditions['T']`, ref #76/#94).

### Install DAMASK on Windows via WSL · [#85](https://github.com/damask-multiphysics/DAMASK/discussions/85)
**Problem:** How to get DAMASK running on Windows.
**Fix / steps:**
1. Quick: PowerShell (Admin) → `wsl --install` (enables WSL + VM platform, installs Ubuntu, sets WSL2).
2. Manual: `dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart` + VM platform feature.
3. Reboot, set Ubuntu user/password, install DAMASK inside WSL.

### Update v3.0.1 → v3.0.2 without reinstalling? · [#106](https://github.com/damask-multiphysics/DAMASK/discussions/106)
**Problem:** Wants in-place update of a source install to get a cF interaction-parameter fix.
**Fix / steps:**
1. No in-place updater — re-download source and rebuild (copy out local edits first).
2. Alternatively use the packaged release / PPA.
