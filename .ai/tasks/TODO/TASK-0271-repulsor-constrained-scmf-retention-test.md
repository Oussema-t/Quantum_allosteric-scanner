# TASK-0271 — Repulsor-constrained self-consistent repack, then release: does the pocket stay open?

- Status: TODO
- Assignee: unassigned (suggest Implementer B or D — TASK-0235's machinery is the base)
- Priority: **High — it is a direct [[HYP-P13]] test by an independent route, and it fills a gap three prior tasks left open**
- Filed: 2026-08-26 by Reviewer
- Related: [[TASK-0230]], [[TASK-0235]], [[TASK-0241]], [[TASK-0213]], [[TASK-0268]], [[HYP-P13]], [[TASK-0204]]

## The gap

Three tasks have displaced a backbone and repacked side chains — [[TASK-0230]]
(ceiling), [[TASK-0235]] (local-Kabsch + EvoEF2), [[TASK-0213]] (coupled
search). **None of them ever released the constraint and asked whether the
opened pocket stays open.** That is the metastability question, and it has
never been run here.

The construction comes from an external exchange, and its two halves fix each
other's defect:

- Our own displacement approach has **no coupling** — frozen backbone, frozen
  repack, applied in sequence.
- A self-consistent mean-field loop (alternating repack/minimise) supplies the
  coupling, but it is **downhill**, so it converges back to the apo basin —
  the same excited-state error this register has hit three times.
- **A pinned repulsor holds the pocket open while the loop converges.** Then
  remove it and re-converge, measuring retention.

**Naming discipline, load-bearing**: the loop is **self-consistent mean-field
side-chain packing** and is operationally what Rosetta's FastRelax has done
for over a decade. It is **not** novel and must not be presented as such. The
external exchange attributed it to Koehl & Delarue 1994 — **verify that
citation live before writing it down**; this register has inherited three
wrong citation details from external sources already ([[TASK-0260]],
[[TASK-0262]]).

## Why this is a HYP-P13 test, not a quantum one

[[HYP-P13]] states allostery is *stabilisation of an otherwise-disfavoured
conformation*. That predicts, directly: **the pocket should collapse once the
repulsor is removed.** Persistence would mean the open state is its own
minimum and the ligand is not doing the stabilising.

[[TASK-0268]] just failed HYP-P13's frustration prediction (cryptic residues
showed *lower* frustration, cluster-p=0.727). This attacks the same hypothesis
by a completely independent route. **Two independent tests are worth having
whichever way this lands** — and if it also fails, HYP-P13 should be retired
rather than left standing on the strength of the four findings it was
originally written to explain.

Scope this as a HYP-P13 / metastability test. **It needs no quantum claim to
be worth running, and should not carry one.**

## Scope

- [ ] Reuse [[TASK-0235]]'s `local_rigid_reconstruction` + `_run_evoef2`
      machinery rather than introducing Rosetta — a new toolchain turns a
      two-day task into a two-week one, and EvoEF2 is already vendored and
      validated here.
- [ ] Implement the alternating loop: repack → local backbone relax → repack,
      to convergence, **with a pinned repulsor** occupying the target pocket.
- [ ] **Pre-register the retention criterion before running.** Suggested:
      fpocket recovers the pocket at ≥50% residue overlap after release, and
      volume retained ≥ some stated fraction. Fix the numbers first.
- [ ] Release the repulsor, re-converge the same loop, and measure retention.
- [ ] Report per target on [[TASK-0243]]'s frozen set, prioritising the **11
      cryptic-testing targets** ([[TASK-0254]] part B) — the already-open ones
      cannot test collapse because there is nothing to collapse.
- [ ] **Trial independence**: [[TASK-0241]] found TASK-0235's "4 trials" were
      one computation repeated four times, byte-identical inputs, because
      `_run_evoef2` takes no seed. Vary the seed or perturb the input, hash
      the trial inputs to prove they differ, and report the jitter band before
      treating any spread as sampling.
- [ ] Cluster-robust significance ([[TASK-0261]]'s exact cluster-level
      permutation) — 20 rows are 13 structures.

## Acceptance

- [ ] Verified citation for the SCMF loop, or an explicit "attribution not
      established".
- [ ] Pre-registered retention criterion, recorded before the first number.
- [ ] Per-target retention on the cryptic subset, with a jitter band and
      hashed trial inputs.
- [ ] An explicit HYP-P13 verdict, and an update to
      `.claude/hypotheses/physics.md` either way.
- [ ] `RESULTS.md`.

## Constraint

[[HYP-P13]] is this register's own hypothesis, written up by the Reviewer.
That makes a favourable result **less** trustworthy, not more — the same
caution [[TASK-0268]] carried. Pre-register, and if the pocket persists after
release, report that as evidence *against* HYP-P13 with the prominence the
hypothesis currently enjoys.
