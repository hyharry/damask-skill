# DAMASK KB — `post` (post-processing: extracting & exporting results)

Scope: reading `result.hdf5`, averaging/deriving quantities, exporting VTK/pyvista, IPF/orientation output, plots, grain boundaries, tangent modulus.
Use: query by keyword (average, stress–strain, export, VTK, orientation, IPF, plot, HDF5).

---

### Extract per-phase / per-crystallite data · [#2](https://github.com/damask-multiphysics/DAMASK/discussions/2)
**Problem:** Can get phase-averaged stress/strain but not whole-material or per-grain data.
**Fix / steps:**
1. `r = damask.Result('out.hdf5'); r.add_stress_Cauchy(); r.add_equivalent_Mises('sigma')`.
2. `cauchy = r.view(increments=[10]).get('sigma')` → dict per phase; concatenate/average per phase or overall.
3. `N_constituents` = how many entities make up **one material point** (homogenization), not a way to split output.

### Macro P-K stress per increment · [#3](https://github.com/damask-multiphysics/DAMASK/discussions/3)
**Problem:** Wants the macro stress printed per increment as a curve.
**Fix / steps:** Average the field per step over all points: `r.add_stress_Cauchy()` then `np.average(r.get('sigma')[i])` per increment (see "Data analysis with Matplotlib and Pandas" tutorial).

### Post-process `dislotwin` twin volume fraction `f_tw` · [#6](https://github.com/damask-multiphysics/DAMASK/discussions/6)
**Problem:** `f_tw` ≈ 1e-10 (suspiciously tiny) — is it input params or post-processing?
**Fix / steps:**
1. Compute correctly: `f_tw_new = [np.average(np.sum(f_tw[i], axis=1)) for i in res.increments]` (sum over twin variants **before** averaging).
2. Average strain via `add_strain()`/`add_equivalent_Mises('epsilon_V^0.0(F)')`.
3. Check `p_s` (0 < p_s ≤ 1) and other params if values stay physical-but-small.

### Show grain boundaries on result plots · [#18](https://github.com/damask-multiphysics/DAMASK/discussions/18)
**Problem:** Field plots show no grain boundaries.
**Fix / steps:** Export to DREAM.3D and segment there (see also `GeomGrid.get_grain_boundaries`, ref #47).

### Export results for a specific element / non-uniform meshing · [#21](https://github.com/damask-multiphysics/DAMASK/discussions/21)
**Problem:** Extract data for one element; wants mesh refinement near grain boundaries with the spectral solver.
**Fix / steps:**
1. Use `damask.Result.place(...)` to get **spatially ordered** results (then index the element).
2. Spectral solver requires a **regular grid** — local refinement is not supported (use mesh solver for non-uniform meshes).

### Extract stress–strain numbers from HDF5 · [#23](https://github.com/damask-multiphysics/DAMASK/discussions/23)
**Problem:** HDFView shows empty / can't pull σ–ε numerically.
**Fix / steps:**
1. Update HDFView (old version couldn't read the file).
2. For averages use the Python API, e.g. the `r-value_Marc` example; don't rely on screenshots — follow the helpdesk question template.

### Incremental equivalent plastic strain · [#43](https://github.com/damask-multiphysics/DAMASK/discussions/43)
**Problem:** Can `add_calculation` give the *incremental* equivalent plastic strain?
**Fix / steps:** `add_calculation` (like all `add_*`) works only within **one HDF5 group/increment**. Get strain per increment and **subtract consecutive increments in Python**.

### Texture evolution: no orientation info in output · [#44](https://github.com/damask-multiphysics/DAMASK/discussions/44)
**Problem:** Can't track grain texture; thinks DAMASK ignores orientation evolution.
**Fix / steps:**
1. Add **`O`** (lattice orientation, quaternion) to the `phase: ... mechanical: output` list.
2. Over-straining (F_zz→2) or huge `xi` values breaks convergence; reduce strain per step (~1e-3), coarsen N, check `h_sl-sl`.

### Wrong σ–ε: averaged full tensors instead of `_vM` · [#46](https://github.com/damask-multiphysics/DAMASK/discussions/46)
**Problem:** Looks like no plastic response; can't reproduce the 2013 paper.
**Fix / steps:**
1. Use the **equivalent** datasets (suffix `_vM`): `r.add_equivalent_Mises('sigma')`, `r.add_equivalent_Mises('epsilon_V^0.0(F)')`.
2. `sigma_vM = [np.average(s)/1e6 for s in r.get('sigma_vM').values()]`; `epsilon = [np.average(e)*100 for e in r.get('epsilon_V^0.0(F)_vM').values()]`.

### Grain boundaries in post-processing · [#47](https://github.com/damask-multiphysics/DAMASK/discussions/47)
**Problem:** Stress/strain maps show no grain boundaries.
**Fix / steps:** Use `damask.GeomGrid.get_grain_boundaries(...)` — exists for **grid files** and for the **undeformed** configuration.

### Plot 3 curves (phase + total) without overlap · [#64](https://github.com/damask-multiphysics/DAMASK/discussions/64)
**Problem:** σ–ε curves for ferrite, pearlite and total overlay each other.
**Fix / steps:** Per-phase curves need per-phase views: `r.view(phases='ferrite')`, `r.view(phases='pearlite')`, plus the full-field average for the total. *(Unsolved in-thread; no files given.)*

### Macroscopic tangent modulus dP/dF · [#65](https://github.com/damask-multiphysics/DAMASK/discussions/65)
**Problem:** Need dP/dF (or C_ep / L_eff) from DAMASK 3.0.0-beta.
**Fix / steps:** No direct output. Recommended: numerical differentiation of the macroscopic P vs F response in post-processing. *(Unanswered in-thread.)*

### Final orientation of each grain from HDF5 · [#69](https://github.com/damask-multiphysics/DAMASK/discussions/69)
**Problem:** Adding `'O'` to output doesn't show up in the result.
**Fix / steps:**
1. `'O'` is only valid at the **phase** level — put it **directly under `mechanical:`** (not under `plastic:`/`elastic:`).
2. Homogenization level has no `O`; output appears as `phase <name> mechanical O`.

### IPF visualisation & orientation reference frames · [#81](https://github.com/damask-multiphysics/DAMASK/discussions/81)
**Problem:** Confusion about IPF colouring and lab vs crystal frames.
**Fix / steps:**
1. Core object: `damask.Orientation` = `Rotation` (lab→crystal transform) + symmetry/lattice.
2. `Orientation.IPF_color(vector)`: the colour encodes **which crystal direction is parallel to the chosen fixed lab direction** (e.g. lab z = (0,0,1)) — not "a fixed colour per lab direction".
3. Use the snippet in-thread (cubic example, pyvista) to verify frame conventions.

### Export multi-phase results to VTK (shape mismatch) · [#83](https://github.com/damask-multiphysics/DAMASK/discussions/83)
**Problem:** `export_VTK` broadcast error `(N,3)` vs `(N,1)`; can't add custom phase fields.
**Fix / steps:**
1. Export **per phase view**: `result.view(phases='A').export_VTK()` and `...phases='B'...`; optionally `export_VTK(output='xi_sl')`.
2. `r.export_VTK()` with no args is also worth trying.
3. Convention: fence YAML snippets with ` ```YAML ` for clarity/copy-paste.
