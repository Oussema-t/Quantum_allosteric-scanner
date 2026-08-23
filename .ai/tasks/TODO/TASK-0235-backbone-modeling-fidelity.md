# TASK-0235 Replace rigid-per-residue backbone translation with a torsion-based (or energy-aware) placement method

## Context

- ID: TASK-0235
- Title: build a backbone-placement method that doesn't introduce severe
  steric distortion when moving the apo structure toward a target
  displacement — replacing the rigid-per-residue-translation
  approximation used throughout [[TASK-0230]]/[[TASK-0233]].
- Status: TODO
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

(not yet)
