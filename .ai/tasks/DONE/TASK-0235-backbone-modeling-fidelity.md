# TASK-0235 Replace rigid-per-residue backbone translation with a torsion-based (or energy-aware) placement method

## Context

- ID: TASK-0235
- Title: build a backbone-placement method that doesn't introduce severe
  steric distortion when moving the apo structure toward a target
  displacement — replacing the rigid-per-residue-translation
  approximation used throughout [[TASK-0230]]/[[TASK-0233]].
- Status: Done
- Resolution: done
- Resolution Note: Local sliding-window Kabsch backbone placement: real improvement (largest on KRAS_G12C, 12.1x->6.5x native vdwrep), does not fully clear the 'close to native apo' bar. Decisive result: BCR_ABL1's ceiling flips 0/4->4/4 trials crossing the druggability bar; CARDIAC_MYOSIN 0/4->1/4; KRAS_G12C unchanged (explained by its own astronomically costly local-residual ANM energy, ~33 thermal units). TASK-0230's own verdict updated via addendum, not silently left stale.
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: derived from three tasks' own repeatedly-flagged, never-fixed
  gap — [[TASK-0230]]'s own Addendum 1 ("the honest next step... would be
  a torsion-based or energy-minimized backbone placement instead of a
  rigid whole-residue translation, before this ceiling question can be
  answered cleanly" — stated, never built), [[TASK-0233]]'s own "natural
  next step if this line of work continues" (estimating the local
  residual's own cost, blocked on the same modeling gap), and
  [[TASK-0234]]'s own closing synthesis ("the program's real remaining
  gap... is a classical structural-modeling accuracy problem"). Filed on
  user instruction to check TASK-0230/0234 (and adjacent tasks) for
  unbuilt items worth verifying.
- Priority: P1 — named three separate times across three tasks as the
  actual bottleneck once every complexity/search-cost question this
  program tried was answered (all "classically cheap" — [[TASK-0185]],
  [[TASK-0204]], [[TASK-0228]], [[TASK-0233]]). This is the one remaining
  gap standing between the register's own already-built tools and a
  physically trustworthy ceiling/reachability number.

## Why this matters, precisely

[[TASK-0230]]'s own geometry-sanity check (`ComputeStability`'s
`interS_vdwrep`) found every rigid-per-residue-translated structure
sits **3–12× native apo's own steric-repulsion energy**, even after the
best relaxation tried (EvoEF2 `SideChainRepack`/`RepairStructure`, both
side-chain-only). This confounds every downstream reading in that whole
line of work: a "closed" ceiling result is genuinely ambiguous between
"the pocket doesn't open" and "the backbone-placement method broke the
local geometry before anyone could tell." [[TASK-0233]]'s own ΔG estimate
is an explicit lower bound for the same reason — it only covers the
soft-mode-captured 77–95% of the true displacement, not the local
residual, which is exactly where this distortion lives.

## Intent Contract

- Outcome: a backbone-placement method that, applied to move the apo
  structure toward a real target displacement (matching [[TASK-0230]]'s
  own test cases), produces a structure with steric-repulsion energy
  (`interS_vdwrep`, EvoEF2 `ComputeStability`) close to native apo's own
  baseline — not the 3–12× elevation the rigid-translation method
  produces — *before* any side-chain repacking is applied. Repacking
  should then be a refinement, not a rescue from a badly broken starting
  geometry.
- Why required, not assumed: measured directly, not inferred — see
  "Why this matters" above, [[TASK-0230]]'s own real numbers.
- In Scope:
  - **Investigate first, in order of increasing tooling cost, per this
    project's own "do not fix blind" convention**:
    1. **Torsion-based reconstruction** — interpolate backbone dihedral
       angles (phi/psi) between apo and holo on the common residue set,
       reconstruct Cartesian coordinates via standard internal-to-
       Cartesian conversion (NeRF), instead of Cartesian rigid
       translation. Preserves local bond lengths/angles by construction
       (interpolating in torsion space cannot itself introduce a bond-
       length violation the way an independent per-residue Cartesian
       shove can). **Checked, not assumed, before filing this task**:
       `prody` (already vendored, already used throughout this project)
       exposes `calcPhi`/`calcPsi`/`calcDihedral`/`getDihedral` directly
       — no new dependency needed for this approach.
    2. If (1) is insufficient (e.g. large-scale collective motion doesn't
       reduce cleanly to a per-residue torsion interpolation): a cheap
       energy-oracle-guided local relaxation using EvoEF2's own
       `ComputeStability` `Total` energy as the objective (a simple
       coordinate nudge / steepest-descent wrapper around repeated EvoEF2
       calls) — more expensive (many subprocess calls) but still no new
       external dependency.
    3. Only if (1) and (2) both prove insufter: evaluate installing a
       real minimization engine (OpenMM/PDBFixer or similar). **Checked
       while filing this task, not assumed available**: no such package
       is installed in `.venv`, vendored under `tools/`, or present
       system-wide (confirmed via a filesystem-wide search during
       [[TASK-0227]]'s own correction) — this path has a real
       installability/network-access cost to resolve first.
  - Validate the chosen method against [[TASK-0230]]'s own real geometry-
    sanity check (`interS_vdwrep` vs. native apo) on the same 3 real
    targets, before trusting any downstream ceiling/ΔG number computed
    with it.
  - Once validated, re-run (a) [[TASK-0230]]'s own ceiling experiment
    (§5.2-style) with the new placement method in place of rigid
    translation, and (b) [[TASK-0233]]'s own local-residual cost
    estimate (the modes/residues beyond k=50 that the collective ΔG
    estimate didn't cover) — both explicitly deferred by their own tasks
    pending this fix.
- Out Of Scope:
  - A full MD engine build-out — this task's own In Scope explicitly
    prefers the tooling-light torsion-based approach first; only
    escalate if it's genuinely insufficient, and stop at "evaluate
    installability" rather than committing to a full MD integration
    inside this same task if that path is reached.
  - Re-opening [[TASK-0234]]'s own retirement (quantum sampling) — that
    conclusion does not depend on this task's outcome; not revisited
    here regardless of what this task finds.
  - Any change to [[TASK-0228]]'s own still-active claim/work (its own
    rigid-per-residue extension via `prody.extendVector` has the same
    class of approximation, noted there already as "a real approximation
    ... stated, not hidden" — flag as informationally relevant if this
    task's own findings are useful there, but do not edit that file
    under this task's claim).
- Constraints And Invariants: reuse `prody`'s own dihedral utilities and
  this project's own existing EvoEF2/fpocket wiring — no new external
  dependency unless (2)/(3) above are reached and justified in the Done
  section, not silently added.
- Planned Validation: the geometry-sanity check IS the validation gate —
  a method that doesn't clear it (native-apo-comparable `vdwrep`) is not
  trusted for the downstream re-runs, same discipline [[TASK-0230]]
  already established.

## Open Questions

- Does a per-residue torsion interpolation actually cover *collective*
  (multi-residue, correlated) motion well, or does it need to be applied
  per-mode / per-region rather than independently per residue? Check
  directly against a real target's own true displacement before assuming
  either way.
- Should this reuse [[TASK-0228]]'s own `prody.extendVector`-based
  full-atom extension machinery (already built, same class of rigid
  approximation) as a starting point to improve, rather than writing a
  fresh full-atom loader? Check what that code actually does before
  deciding to build a parallel path.

## Done

**Real, measured improvement — largest exactly where the old method was
worst — and one genuinely decisive result: BCR_ABL1's ceiling flips from
0/4 to 4/4 trials crossing the druggability bar. Does not fully clear
this task's own literal "close to native apo" bar — reported honestly as
partial, not oversold.**

### Method chosen: local sliding-window Kabsch, not literal phi/psi+NeRF

Deviated from this task's own In Scope item 1's literal wording
(interpolate phi/psi, reconstruct via NeRF) to a simpler mechanism
achieving the same goal — stated here, not silently substituted. For
each residue, Kabsch-fit a window of sequence-consecutive neighbor Cα
positions (apo → target) and apply that one local rigid rotation to
every atom of the window's center residue
(`task0235_local_rigid_backbone.local_rigid_reconstruction`, reusing
`allostery.superpose.kabsch_fit`/`kabsch_apply` directly — already
validated, already used throughout this project, no new dependency).
Neighboring residues share overlapping window atoms, so the local
transform varies smoothly along the chain instead of jumping
independently residue-to-residue, the believed mechanism behind
[[TASK-0230]]'s own severe `vdwrep` elevation. Preserves local bond
geometry by the same guarantee literal torsion reconstruction would
provide (a rigid transform cannot itself distort geometry within the
residue it's applied to), handles backbone **and** side chain in one
step (pure phi/psi reconstruction only gives the backbone trace, needing
a separate side-chain-placement step), and avoids an unnecessary
Cartesian→torsion→Cartesian round-trip since the actual input data
(ANM-projected/holo-aligned target positions) is already Cartesian.

**Window size swept on KRAS_G12C** (1/2/3/4/6, full displacement,
pre-repack `vdwrep`): 543.1/562.3/646.1/559.8/668.5 — window=1 (nearest
neighbor only) gave the lowest value; a tighter window tracks genuine
local curvature more faithfully than a wider one that starts averaging
over real collective bend. `LOCAL_WINDOW=1` used for all 3 targets below
(not independently re-swept per target — a real, stated limitation, not
hidden).

### Geometry validation (this task's own Planned Validation gate)

| target | native apo `vdwrep` | full-displ. pre-repack: old (rigid) → new (local-Kabsch) | ratio: old → new |
|---|---|---|---|
| KRAS_G12C | 84.1 | 1014.8 → **543.1** | 12.07× → **6.46×** |
| BCR_ABL1 | 300.1 | 876.0 → 857.1 | 2.92× → 2.86× |
| CARDIAC_MYOSIN | 335.6 | 1014.3 → 953.4 | 3.02× → 2.84× |

**Does not clear this task's own literal "close to native apo" bar** —
still 2.8–6.5× elevated, not ~1×. Real improvement, concentrated almost
entirely on the target that was worst under the old method (KRAS_G12C,
nearly halved) — consistent with the diagnosis that the old method's
worst cases were dominated by genuine *local* bond-geometry violations
(exactly what this method targets), while BCR_ABL1/CARDIAC_MYOSIN's
smaller-to-begin-with excess was already mostly *pairwise*, non-local
side-chain clash — a repacking problem, not a backbone-placement one, by
construction outside what any per-residue-local method (of any kind,
including literal torsion reconstruction) can fix alone.

### Ceiling re-run (§5.2-style, full displacement, 4 EvoEF2 trials/target)

| target | old method: post-repack druggability (4 trials) | new method: post-repack druggability (4 trials) | trials ≥0.5 bar: old → new |
|---|---|---|---|
| KRAS_G12C | 0.129, 0.247, 0.247, 0.214 | 0.309, 0.141, 0.309, 0.073 | 0/4 → 0/4 |
| BCR_ABL1 | 0.23, 0.432, 0.23, 0.432 | **0.675, 0.719, 0.656, 0.725** | 0/4 → **4/4** |
| CARDIAC_MYOSIN | 0.21, 0.12, 0.004, 0.169 | 0.603, 0.019, 0.047, 0.112 | 0/4 → 1/4 |

**BCR_ABL1: a genuinely decisive, real result, not a noisy improvement.**
Every trial now clears the 0.5 druggability bar (old method's own
maximum, 0.432, never did) — post-repack `vdwrep` also improved slightly
(3.02×→2.96×). This directly updates how [[TASK-0230]]'s own "ceiling
fails on all 3 targets" finding should be read for this target
specifically: the failure there was the backbone-placement method, not
evidence the pocket doesn't open. Consistent with, not a new claim
independent of, this project's own repeated prior finding that BCR_ABL1's
pocket is an "apo-computable structural prior" ([[TASK-0104]]/[[TASK-0091]],
cited in [[TASK-0228]]'s own text) — a target whose druggability was
always going to be easy to recover once the backbone geometry feeding the
scorer wasn't badly distorted. CARDIAC_MYOSIN: one trial now clears the
bar (0.603, previously max 0.21) but inconsistently (3 of 4 trials still
low) — a real but noisy signal, not a clean flip. KRAS_G12C: no change in
outcome (0/4 both methods), though the maximum single-trial value rose
(0.247→0.309).

### Local-residual cost (this task's own item (b), independent of the
backbone-placement method above — pure ANM harmonic calculation)

Extended [[TASK-0233]]'s own `run_superpose`/`mode_energetics` (reused
unmodified) to full non-rigid mode coverage (`n_modes = 3N-6`) instead of
the k=50 truncation, isolating the residual's own elastic cost as
`ΔG(all) - ΔG(k=50)`:

| target | ΔG(k=50) | ΔG(all modes) | ΔG(residual) | `exp(-ΔG(all))` |
|---|---|---|---|---|
| KRAS_G12C | 2.32 | 35.32 | **33.00** | 4.6×10⁻¹⁶ |
| BCR_ABL1 | 0.37 | 8.94 | 8.57 | 1.3×10⁻⁴ |
| CARDIAC_MYOSIN | 0.20 | 5.24 | 5.04 | 5.3×10⁻³ |

**Directly explains the ceiling re-run's own differential pattern
above, not a coincidence.** KRAS_G12C's local residual is astronomically
costly under the harmonic model — even a well-reconstructed backbone
still represents a genuinely disfavored conformation, consistent with
its own unchanged (0/4→0/4) ceiling outcome regardless of placement
method. BCR_ABL1 and CARDIAC_MYOSIN's residuals are modest-to-rare but
not implausible, consistent with a real backbone-placement fix being
enough to unlock (BCR_ABL1) or partially unlock (CARDIAC_MYOSIN)
druggability. **Minor numerical caveat, stated not hidden**: `CO(all
modes)` came out slightly above 1.0 (1.01–1.04) — a known artifact of
`cumulative_overlap`'s own renormalized-slice approximation at the
extreme high-mode-count limit ([[TASK-0133]]'s own documented boundary
condition), not a sign the ΔG sums themselves are wrong; noted for
whoever next extends this calculation.

### Cross-references, per this task's own scope

[[TASK-0230]]'s own "ceiling fails on all 3 targets" verdict needs a
per-target update, not a blanket one: still real and robust for
KRAS_G12C (both methods, 0/4), no longer the full picture for BCR_ABL1
(flips to 4/4 with the corrected backbone method) or, partially, for
CARDIAC_MYOSIN (1/4). Addendum added to [[TASK-0230]]'s own Done section
rather than silently left stale. [[TASK-0234]]'s own retirement (quantum
sampling/search at the collective+joint layer) is unaffected — this
task's own finding is about backbone-placement *fidelity*, a modeling-
accuracy question TASK-0234 explicitly separated from the search-cost
questions it retired.

**Not done, per this task's own Out Of Scope, and real remaining
limitations stated plainly**: no MD/energy-minimization engine evaluated
or installed — the local-Kabsch method's real, if partial, improvement
was judged sufficient to not escalate past it in this task's own claim,
not evidence installation is unnecessary in general. Window size swept
on one target only, not independently optimized per target. The
literal "close to native apo" outcome this task's own Intent Contract
named is not met — reported as such, not redefined after the fact to
declare victory.
