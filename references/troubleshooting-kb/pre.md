# DAMASK KB — `pre` (pre-processing: geometry, material.yaml, loadcase, initial conditions)

Scope: building geometry/RVE (Voronoi, Neper, DREAM3D), writing `material.yaml` (phases, elasticity, plasticity params, lattice), loadcase/BC syntax, initial conditions, orientations/textures, unit handling.
Use: query by keyword (geometry, material.yaml, loadcase, DREAM3D, Neper, orientation, initial condition, temperature, units).

---

### DREAM3D load: wrong grain count + grain-ID offset · [#8](https://github.com/damask-multiphysics/DAMASK/discussions/8)
**Problem:** `load_DREAM3D` reports different #materials and shifted grain IDs vs raw h5py.
**Fix / steps:**
1. Grain IDs are **0-based** and index into the `material` list in `material.yaml` (confirmed correct).
2. Index-order difference: DAMASK uses **Fortran (column-major, x fastest)**; DREAM3D uses **C (row-major, z fastest)** → compare with `.flatten('F')` vs `.flatten('C')`.
3. If `feature_Ids` is not passed, DREAM3D segmentation is ignored and cells are lumped by identical orientation+phase.

### `material.yaml` for HCP (Mg) materials · [#16](https://github.com/damask-multiphysics/DAMASK/discussions/16)
**Problem:** How to configure an HCP phase (elastic only) / missing `c/a`.
**Fix / steps:**
1. Set `lattice: hP` **and** `c/a: <ratio>` (e.g. `1.623` for Mg) — needed even for elastic-only; omitting it errors.
2. Hex has **5 independent stiffness constants** (C_11,C_12,C_13,C_33,C_44); C_66 is derived.

### `load_DREAM3D` KeyError / wrong base group · [#24](https://github.com/damask-multiphysics/DAMASK/discussions/24)
**Problem:** `KeyError: object 'Phases' doesn't exist` on a `.dream3d`.
**Fix / steps:** File has multiple data groups; specify the one that has the spacing info:
`damask.GeomGrid.load_DREAM3D("file.dream3d", base_group='DataContainers/SyntheticVolumeDataContainer')`

### Loadcase: syntax for rotation `R` (BC) · [#28](https://github.com/damask-multiphysics/DAMASK/discussions/28)
**Problem:** What YAML syntax expresses a BC rotation from grid→load frame?
**Fix / steps:** Give **axis + angle in degrees**: `R: [0,0,1,30]` (= 30° about z). (Docs were reworded + example added.)

### Meaning of `material.yaml` / plasticity parameters · [#29](https://github.com/damask-multiphysics/DAMASK/discussions/29)
**Problem:** Where are `N_sl, a_sl, h_0_sl-sl`, … documented?
**Fix / steps:** Names follow the DAMASK constitutive-model overview paper (see thread link); also `damask/example/config/...` YAML references.

### Periodic centroid of a grain (periodic tiling) · [#31](https://github.com/damask-multiphysics/DAMASK/discussions/31)
**Problem:** Plain averaging gives wrong grain centroid under periodic BCs.
**Fix / steps:**
1. Use a periodic-aware centroid (unwrap across boundaries) — code snippet in thread.
2. For `GeomGrid` objects this already exists: `damask.seeds.from_grid`.

### `damask.GeomGrid` → `pyvista.ImageData` · [#32](https://github.com/damask-multiphysics/DAMASK/discussions/32)
**Problem:** Need a pyvista image object from a GeomGrid for visualisation.
**Fix / steps:** `pv.ImageData(dimensions=grid.cells+1, spacing=grid.size/grid.cells, origin=grid.origin)`; set `img['material'] = grid.material.flatten('F')` (note **`'F'`** order).

### DREAM3D import: #materials too high → build material array · [#41](https://github.com/damask-multiphysics/DAMASK/discussions/41)
**Problem:** 2-phase structure came out with many materials.
**Fix / steps:** **#materials = #unique (phase, orientation) combinations** — not phases alone. Provide orientation data (e.g. via `ConfigMaterial.load_DREAM3D(..., phase_names=...)`) to collapse duplicates.

### Rotate / flip a GeomGrid (2D→X-Z plane) · [#48](https://github.com/damask-multiphysics/DAMASK/discussions/48)
**Problem:** `rotate`/`flip` "didn't work" when reorienting an RVE for z-parallelism.
**Fix / steps:** `GeomGrid.rotate(...)` is **not in-place** — it **returns a new GeomGrid**. Assign/use the return value.

### Stress-controlled loading instead of strain-controlled · [#52](https://github.com/damask-multiphysics/DAMASK/discussions/52)
**Problem:** How to prescribe stress (to get stress–strain) rather than `dot_F`.
**Fix / steps:** Use `P:` BCs in the loadcase (see grid-solver load-case docs). *(OP then asked unrelated VSCode question without files.)*

### DREAM3D-NX file cannot be loaded · [#53](https://github.com/damask-multiphysics/DAMASK/discussions/53)
**Problem:** `ValueError: could not determine base group` for DREAM3D-NX output.
**Fix / steps:** DREAM3D file format **v8.0 not supported** at the time; needs a newer DAMASK (see #111 → supported in 3.1.0).

### Use a Neper-generated RVE in DAMASK · [#57](https://github.com/damask-multiphysics/DAMASK/discussions/57)
**Problem:** How to import a Neper 2D RVE.
**Fix / steps:** `damask.GeomGrid.load_Neper(...)`.

### Error 613 → Neper `.tess`→`.vtk`→`.vti` conversion · [#59](https://github.com/damask-multiphysics/DAMASK/discussions/59)
**Problem:** Error 613 because geometry was a raw VTK file (not DAMASK-compatible VTI).
**Fix / steps:**
1. Create tessellation in Neper; export `neper -T -loadtess file.tess -format vtk`.
2. **Neper IDs start at 1; DAMASK expects 0-based.** Don't blindly `-1` (Neper uses ID 0 for special materials). Do it in Python: `grid = damask.GeomGrid.load_Neper('file.vtk'); grid.material -= 1`.
3. Convert VTK→VTI: `damask.GeomGrid.load_Neper(...).save('grid.vti')`.
4. Also check Docker `--workdir /wd` mapping is present.

### Fiber-texture orientations look wrong (conventions) · [#60](https://github.com/damask-multiphysics/DAMASK/discussions/60)
**Problem:** `Rotation.from_fiber_component` texture disagreed with `orix` IPFs.
**Fix / steps:**
1. α-fiber definition differs bcc vs fcc — check which applies.
2. DAMASK and orix follow the same paper but **DAMASK uses P = −1, orix P = +1** → flip the quaternion imaginary part when converting.
3. OP's local fix: rotate random orientations about the **crystal** fibre axis, not the sample axis.

### Error 155 (material index out of bounds) · [#61](https://github.com/damask-multiphysics/DAMASK/discussions/61)
**Problem:** `error 155` from the `.vti` material indices.
**Fix / steps:** Material indices in the `.vti` must be **0..N-1 (0-based)**. OP had 1..10 while defining 10 materials → index 0 ignored, index 10 not found. Renumber to 0-based.

### Biphasic run fails: `N_constituents` mismatch · [#66](https://github.com/damask-multiphysics/DAMASK/discussions/66)
**Problem:** Errors when running a two-constituent material through `bicrystal` homogenization.
**Fix / steps:**
1. `N_constituents` in the homogenization must **equal the number of constituents** listed per material ID (2 entries at v=0.8/0.2 → `N_constituents: 2`).
2. `pass` homogenization only works with a **single** constituent.

### Error 844 (invalid VTI size) then 402 (bad quaternion) · [#67](https://github.com/damask-multiphysics/DAMASK/discussions/67)
**Problem:** 2D EBSD map → `error 844 invalid size` (z-thickness 0), then `error 402 invalid orientation`.
**Fix / steps:**
1. Give the 2D grid **non-zero thickness**: `grid.size[2] = grid.cells[2]*np.min((grid.size/grid.cells)[:2])`.
2. Validate all quaternions with `damask.Rotation.from_quaternion` — negative `q0` and norm ≠ 1 are invalid (often from Excel/default-precision imports).

### Initial condition as a function of spatial coordinates (nonlocal ρ) · [#70](https://github.com/damask-multiphysics/DAMASK/discussions/70)
**Problem:** Want a spatially graded initial dislocation density ρ(x) (e.g. normal distribution).
**Fix / steps:**
1. Option A: build a microstructure of **multiple materials (slices)** with different ρ.
2. Option B: run one increment → save restart snapshot (HDF5) → **edit state variables** (see `phase_mechanical_plastic_nonlocal.f90` for layout) → restart.
3. To hold a constant shear stress: split load steps; make the first (elasto-plastic transition) fine, then hold `P` in the second.

### Set temperature (TWIP-TRIP / dislotwin) · [#76](https://github.com/damask-multiphysics/DAMASK/discussions/76)
**Problem:** Doesn't know where to set the (initial) temperature.
**Fix / steps:**
1. Temperature is an **initial condition on the grid**, not `T_ref`: `grid.initial_conditions['T'] = ...` (or pass a dict at `GeomGrid` creation).
2. `T_ref` is only the reference for temperature-dependent material constants — do **not** change it.
3. To make T evolve you also need the thermal solver + thermal properties/heat sources.

### Rescale an RVE (µm → m) · [#77](https://github.com/damask-multiphysics/DAMASK/discussions/77)
**Problem:** Neper RVE is in µm; DAMASK inputs are SI.
**Fix / steps:** Most constitutive models are scale-independent (size doesn't affect results). To change size: `grid = damask.GeomGrid.load('x.vti'); grid.size = np.array([x,y,z]); grid.save('rescaled')`.

### `eigen` section: `"thermalexpansion" is not a dict` · [#80](https://github.com/damask-multiphysics/DAMASK/discussions/80)
**Problem:** Thermal eigenstrain block errors on indentation/structure.
**Fix / steps:**
1. The `eigen:` block must be nested **directly under `mechanical:`**, alongside `elastic:`/`plastic:` — not inside `plastic:`.
2. Watch YAML indentation/tabs; quote keys containing commas (`'C_11,T'`).
3. *(OP's specific case unresolved in-thread — check nesting level.)*

### Stress-controlled cyclic loading setup · [#86](https://github.com/damask-multiphysics/DAMASK/discussions/86)
**Problem:** How to set up uniaxial stress-controlled cyclic loading.
**Fix / steps:**
1. Load order/rates sensible; make the **first load** go to P_11=25 MPa over 12.5 s, then down to −5 MPa over 15 s (no explosive preload).
2. **Increment count** is usually too low for the stress "breathing" — estimate from the plastic strain expected per half-cycle.

### Set temperature in the dislotungsten model · [#94](https://github.com/damask-multiphysics/DAMASK/discussions/94)
**Problem:** Adding `T_ref: 500` did nothing to the yield point.
**Fix / steps:**
1. `T_ref` is only the **reference temperature** for temperature-dependent constants — changing it distorts C values. Don't use it to set temperature.
2. Set the initial value via the **vti initial condition** for `T` (see #76).
3. To let T evolve, activate the **thermal solver** (`thermal: spectral`) with thermal properties + heat sources; otherwise T stays at 293.15 K.

### Logarithmic increment (`log N`) in the loadcase · [#99](https://github.com/damask-multiphysics/DAMASK/discussions/99)
**Problem:** `log N: 3000` → `incomplete loadcase N missing` in DAMASK 3.
**Fix / steps:** The old `log` keyword was superseded by **`r`** (geometric-series scaling of the increment) in the loadcase discretization. Use `r` (+ `N`).

### Cementite crystal structure / `isotropic` lattice · [#103](https://github.com/damask-multiphysics/DAMASK/discussions/103)
**Problem:** `lattice_structure isotropic` existed in v2 but not v3.
**Fix / steps:** Use any lattice (easiest **cI or cF**) and set the elastic constants so the resulting behaviour is isotropic.

### DREAM3D-NX support / alternatives for EBSD · [#111](https://github.com/damask-multiphysics/DAMASK/discussions/111)
**Problem:** DREAM3D-NX dropped `_SIMPL_GEOMETRY`, so `load_DREAM3D` fails.
**Fix / steps:** **DREAM3D-NX support is added in DAMASK 3.1.0** → upgrade. (Related: #53.)

### New user: create `material.yaml` → grains → loadcase → submit · [#115](https://github.com/damask-multiphysics/DAMASK/discussions/115)
**Problem:** Beginner can't create `material_phase_phenopowerlaw.yaml`, then can't link grains/loadcase.
**Fix / steps:**
1. Follow the "Configure a DAMASK simulation" tutorial / video; `hyharry/cp_icme_workflow` repo is a good starter.
2. Build polycrystal: use the Voronoi tessellation How-To (`damask.Grid.from_Voronoi_tessellation(cells,size,seeds)`), or `seeds`/`GeomGrid` equivalents.
3. The `.vti` field **`material`** holds **0-based** indices into `material.yaml` → links grains to materials automatically.
4. Loadcase: `damask.Config(solver={'mechanical':'spectral_basic'}, loadstep=[...])`; submit with `DAMASK_grid -l ... -g ... -m ...`.
