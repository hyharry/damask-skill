# DAMASK KB — `advance` (advanced modelling: nonlocal, damage, dislotwin/TWIP-TRIP, thermal, regridding, model dev)

Scope: constitutive complexity and extension — nonlocal plasticity, damage/phase-field, eigenstrain, dislotwin/TWIP-TRIP, thermal coupling, cyclic loading, precipitates, regridding, custom source changes.
Use: query by keyword (nonlocal, damage, phi, dislotwin, TWIP, TRIP, thermal, eigenstrain, regrid, precipitate, precipitate strengthening, new model).

---

### Nonlocal model: no runnable examples / how to tell it's working · [#4](https://github.com/damask-multiphysics/DAMASK/discussions/4)
**Problem:** Wants ready-to-run nonlocal input; unsure the model is active; output file huge.
**Fix / steps:**
1. Nonlocal is hard to converge; follow Kords' thesis for parameter sets.
2. Fix `material.yaml` output placement so dislocation densities are written (`phase ... mechanical: output`).
3. Control output size with **`f_out`** (write frequency) — not every increment.

### Damage run produces no damage output (`phi`) · [#9](https://github.com/damask-multiphysics/DAMASK/discussions/9)
**Problem:** Damage simulation outputs only the driving force `f_phi`, no `phi`.
**Fix / steps:**
1. Select a **solver for the damage field** in `load.yaml`: `solver: {mechanical: spectral_basic, damage: spectral}`.
2. Request output in the **homogenization** block: `homogenization: SX: N_constituents: 1 mechanical: {type: pass} damage: {type: pass, output: [phi]}`.
3. DAMASK damage **is** a phase-field formulation (refer to the DAMASK paper).

### Nonlocal: reproduce Kords thesis — dislocations don't move · [#13](https://github.com/damask-multiphysics/DAMASK/discussions/13)
**Problem:** Nonlocal edge dislocations don't glide; can't find elastic constants for isotropic example.
**Fix / steps:** Not a bug — **nonlocal is not recommended for beginners**. Build up with simple constitutive models first, then move to nonlocal.

### `dataset "phi" not found` in damage simulation · [#14](https://github.com/damask-multiphysics/DAMASK/discussions/14)
**Problem:** Damage run errors on missing `phi`; then `f_phi`/`phi` absent or unchanged in ParaView.
**Fix / steps:**
1. Set the **initial condition in the `.vti`**: `g = damask.GeomGrid.load(fn); g.initial_conditions['phi'] = 1; g.save(fn)`.
2. In recent releases the damage driving-force label is **`Psi_D`** (not `f_phi`) — use the correct label for your version.
3. Unchanged `phi` often means the microstructure hasn't damaged yet.
4. Numerical option keys **changed between alpha7 and beta** — use the `numerics.yaml` matching your version (`N_cutback_max` etc.).

### Nonlocal can't reproduce grain refinement / subgrain boundaries · [#15](https://github.com/damask-multiphysics/DAMASK/discussions/15)
**Problem:** Nonlocal doesn't form low-angle subgrain boundaries matching in-situ EBSD.
**Fix / steps:** Not a fit — **DAMASK is probably not suitable** for this use case.

### Softening during hot deformation (negative slope after yield) · [#17](https://github.com/damask-multiphysics/DAMASK/discussions/17)
**Problem:** How to get softening (post-yield negative stress–strain slope) in hot deformation.
**Fix / steps:** *(Unanswered.)* Needs a recrystallisation/thermal-softening-capable model — check whether any DAMASK constitutive model provides it; otherwise custom source work.

### dislotwin: how to set the self-diffusion coefficient `D_0` · [#19](https://github.com/damask-multiphysics/DAMASK/discussions/19)
**Problem:** Unsure how `D_0` (self-diffusion coeff. for fcc Fe) is set in dislotwin.
**Fix / steps:** The climb-velocity model was **changed** to Argon & Moffat (Acta Metall. 1981); see implementation in `src/phase_mechanical_plastic_dislotwin.f90` (~line 702). Read the code for exact parameter physics.

### Plastic (ductile) fracture of metals · [#26](https://github.com/damask-multiphysics/DAMASK/discussions/26)
**Problem:** Only brittle-fracture examples exist; wants plastic fracture.
**Fix / steps:**
1. Combine an **`isobrittle`/`anisobrittle` damage model with a plasticity law**.
2. The **ductile damage model was removed in v3** (a new improved one was in development).
3. v2→v3 is a major update; prefer v3 (more stable), compare module source if migrating.

### NiTi shape-memory alloy (B2→B19′ transformation) · [#54](https://github.com/damask-multiphysics/DAMASK/discussions/54)
**Problem:** No monoclinic crystallographic structure available for NiTi.
**Fix / steps:** **Not implemented** — monoclinic phase transformation isn't supported.

### dislotwin `c/a_hP` parameter meaning · [#62](https://github.com/damask-multiphysics/DAMASK/discussions/62)
**Problem:** `c/a_hP` isn't in the paper — does it matter? Does c/a=1 change `f_tr`?
**Fix / steps:** It **is** used — required to compute the stiffness matrix of the twinned (hP) material. Read the code: `src/phase_mechanical_plastic_dislotwin.f90` (line ~499).

### Rigid clamps for simple shear in a bi-material (nonlocal BC) · [#63](https://github.com/damask-multiphysics/DAMASK/discussions/63)
**Problem:** How to set impenetrable rigid clamps to get simple shear of an inclusion.
**Fix / steps:**
1. Grid-solver BCs prescribe the **volume-average** response — they don't fix values at boundaries; interface shape depends on relative stiffness.
2. The interior shears simply **if the clamp material is at least as stiff/strong** as the interior.
3. Nonlocal transmissivity params: `chi_surface`, `chi_GB`; **phase boundaries are always transmissivity 0** internally — so don't make blue/red different *phases* if you want transmission.

### Nonlocal: the "density considered significant" threshold · [#74](https://github.com/damask-multiphysics/DAMASK/discussions/74)
**Problem:** What does the `rho_significant`/`rho_min` `where` condition in `getRho0` (`phase_mechanical_plastic_nonlocal.f90` ~L1635/1661) mean?
**Fix / steps:** Those lines **zero out dislocation densities below a threshold** `max(rho_min/v_0^(2/3), rho_significant)`. *(OP was analysing/modifying the model; no maintainer answer.)*

### Thermomechanical coupling (T BC, T-dependent params) · [#79](https://github.com/damask-multiphysics/DAMASK/discussions/79)
**Problem:** Can you impose average T BC? Correct syntax for T-dependent Hooke? T-dependent plasticity?
**Fix / steps:**
1. Average/initial T: set grid `initial_conditions['T']` (see #76); locally varying is possible.
2. Temperature-dependent constants use keys `X`, `X,T`, `X,T^2` (quote keys with commas: `'C_11,T'`).
3. **No direct T/Ṫ BC yet** — use a **heat source** for time-dependent (uniform or heterogeneous) heating.
4. No temperature dependence for initial slip resistances (can be mimicked).

### Define a new state variable / uncoupled ductile damage · [#87](https://github.com/damask-multiphysics/DAMASK/discussions/87)
**Problem:** Want a state variable `D` (delete voxel at D=1) without softening.
**Fix / steps:** *(Unanswered.)* Needs **source modification** — the relevant modules are `phase_damage.f90`, `homogenization_damage.f90`, `phase_damage_isobrittle.f90` (and `phase.f90`); implement the criterion there.

### Thermal module: temperature stays constant · [#88](https://github.com/damask-multiphysics/DAMASK/discussions/88)
**Problem:** Set `initial_conditions['T']=300`, added `dissipation`/`externalheat` sources, but T never changes.
**Fix / steps:** *(Closed as duplicate — see #79/#94.)* Ensure the **thermal solver is activated** in `load.yaml` and heat sources reference the right field; `T_ref` is not the temperature.

### Isotropic plasticity for cementite (orthorhombic) · [#90](https://github.com/damask-multiphysics/DAMASK/discussions/90)
**Problem:** Which lattice/elastic constants for orthorhombic cementite?
**Fix / steps:**
1. The isotropic plasticity model works with **any** lattice; the lattice fixes the required Voigt elastic constants.
2. Available lattices: **cI, cF, hP, tI** (cubic, hexagonal, tetragonal).
3. For other symmetries, implement it yourself (`src/crystal.f90`).

### Phase-field cleavage fracture: where to set `G_0`? · [#91](https://github.com/damask-multiphysics/DAMASK/discussions/91)
**Problem:** No docs on cleavage-fracture phase field; is `G_0` = `W_crit`?
**Fix / steps:** *(Unanswered.)* Use the **`anisobrittle`/`isobrittle`** damage model; the critical energy release rate maps to the damage-model critical parameter (`W_crit`) — verify against the DAMASK damage paper/source.

### Automated regridding — part 2 (driver loop) · [#95](https://github.com/damask-multiphysics/DAMASK/discussions/95)
**Problem:** Need to run an initial sim then multiple regridding passes automatically.
**Fix / steps:** Use the posted loop driver (imports `regrid_main`): set working dir, material params (N_GRAINS, SEED, PHASE_FILE, …), then iterate regrid passes. Builds on the `MarDiehl/regrid` approach.

### Nonlocal simulation gets killed / diverges at realistic ρ₀ · [#102](https://github.com/damask-multiphysics/DAMASK/discussions/102)
**Problem:** At realistic ρ₀ (1e6–1e14 m⁻²) nonlocal diverges at the first increment; at artificially high ρ₀ it crashes ~90%.
**Fix / steps:** *(Unsolved.)* Nonlocal is convergence-sensitive; cross-ref #4, #74, #100. Check parameter consistency with Kords' thesis, ease the first increment, and verify output/memory settings.

### Automated regridding — part 1 (pre-processing class) · [#97](https://github.com/damask-multiphysics/DAMASK/discussions/97)
**Problem:** Need to map a finished result onto a new grid for continuation.
**Fix / steps:** Use the posted `RegridPreproces` class: takes completed `result.hdf5` + restart file + original `geom.vti`, extracts deformation from the final increment, and writes compatible geometry + restart files for continuation. Based on `MarDiehl/regrid`.

### Explicit precipitates in CPFEM: no strengthening seen · [#101](https://github.com/damask-multiphysics/DAMASK/discussions/101)
**Problem:** Alloy with hard precipitates shows **lower** macroscopic stress than pure Al (contrary to strengthening).
**Fix / steps:**
1. Common pitfall: volume-averaging only the **matrix**, not the precipitate phase → apparent softening. Average over **both** phases.
2. A **local** model can't capture dislocation pile-ups at precipitates — expect limited strengthening.
3. OP: 0.679 vol% precipitates, 20³ grid, spectral_basic; re-check averaging + phase assignment.

### Free-surface BCs via a dilatational envelope · [#105](https://github.com/damask-multiphysics/DAMASK/discussions/105)
**Problem:** Emulating free surfaces with a soft/dilatational buffer layer → convergence problems.
**Fix / steps:**
1. Use **deformation BCs only** — don't also force stress = 0; the envelope provides the free surface.
2. **Match elastic and plastic levels** of the envelope to the interior: if envelope is ~100× softer, its yield stress must also be ~100× lower.
3. Also try **`spectral_polarization`** solver and reduce the stiffness/property mismatch of the buffer.

### Modify the dislocation-density model (solid-solution / 2nd-phase strengthening) · [#109](https://github.com/damask-multiphysics/DAMASK/discussions/109)
**Problem:** Want to add solid-solution and second-phase strengthening into CRSS.
**Fix / steps:** The model to modify is `src/phase_mechanical_plastic_dislotwin.f90` — add your strengthening contributions to the CRSS there.

### dislotwin parameter fitting — which values to use · [#110](https://github.com/damask-multiphysics/DAMASK/discussions/110)
**Problem:** Doesn't know which dislotwin parameters to fit or how to find them.
**Fix / steps:** *(Unanswered.)* Use the dislotwin/TWIP-TRIP example values as a baseline and the reference papers (Wong 2016; Argon & Moffat for climb). Cross-ref #19, #62, #112, #114.

### Eigenstrain implementation + convergence problems · [#113](https://github.com/damask-multiphysics/DAMASK/discussions/113)
**Problem:** Adding an eigenstrain field makes the sim diverge; pole figures off.
**Fix / steps:**
1. Follow the **Eshelby procedure**: apply the eigenstrain, then **relax the microstructure without loading** before loading.
2. See the integration test `tests/integration/test_initial_eigenstrain.py` for a working example.

### dislotwin TWIP-TRIP: p_sl/q_sl range + low twin/martensite VF · [#114](https://github.com/damask-multiphysics/DAMASK/discussions/114)
**Problem:** (1) Can't set `p_sl=1.15`, `q_sl=1.0` (out of allowed range). (2) Twin/martensite VF only 2–3% vs higher experimental values.
**Fix / steps:** *(Unanswered.)* (1) These exponents are range-restricted by the model. (2) Revisit interaction matrices / parameters; cross-ref #6, #110, #112.
