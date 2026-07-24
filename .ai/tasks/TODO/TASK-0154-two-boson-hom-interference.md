# TASK-0154 Two-boson Hong-Ou-Mandel interference observable (the one non-reducible multi-walker residual)

## Context

- ID: TASK-0154
- Title: a genuine two-particle *bosonic* interference observable —
  Hong-Ou-Mandel-style coincidence/bunching between two identical bosons,
  one launched at the active site and one swept across candidate
  residues — as a per-candidate coupling score that tests *path
  interference*, not co-location.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: the "multi-walking / boson-walk" idea (2026-07-20 conversation,
  previously unfiled; Architect rating attached in-thread). Filed now,
  scoped to the ONLY residual that has not already been ruled out — see
  the reducibility corrections below.
- Priority: **P3 — medium effort (~1-2 days, k=2 symmetrized space at
  N~950 is tractable), low prior. File-and-gate, do not let it block the
  cheaper tasks.**

## Reducibility corrections — read before implementing (do NOT re-run dead branches)

Three multi-walker variants are already dead or provably trivial. This
task is ONLY the fourth. Stating this so no implementer burns compute on
the refuted ones:

1. **Non-interacting fermions — provably classically trivial, DO NOT
   BUILD.** Non-interacting multi-fermion amplitudes reduce exactly to
   *determinants* of the single-particle transition amplitudes already
   computed (Valiant 1979; Terhal & DiVincenzo 2002, matchgates ==
   non-interacting fermions; determinant is in P). There is no new
   information content — a complexity-theory fact, not an empirical
   question. Worth at most a one-line footnote in the write-up
   ("checked; provably no advantage"), computed from existing amplitudes.
2. **Naive interacting co-occupation — already near-negative
   (Falsifier C, 2026-07-13b review).** The coincidence observable there
   reduced to single-particle occupation squared, and on-site repulsion
   only reduced co-occupation without adding discriminating information.
   Do not re-file that version.
3. **Anyons / parastatistics / quons — not testable, no formalism to
   port.** Anyonic exchange is strictly 2D (braiding needs a plane); a
   3D protein contact graph has no braiding manifold, so an anyonic walk
   is not well-defined on it. Parastatistics (Green 1953) has no
   established CTQW-on-a-graph formalism. These are aspirational Phase-2
   write-up paragraphs, NOT tasks.
4. **Two-boson HOM interference — THE residual this task builds.** This
   is *path* interference between two indistinguishable bosons, not
   "are two particles at the same node." It does NOT trivially reduce to
   the single-particle observable, and is tractable at k=2. NOTE the
   honest ceiling: two bosons is a 2x2 permanent — trivial to compute —
   so even a clean positive is a **better observable, not a quantum
   advantage** (Aaronson-Arkhipov hardness needs MANY photons,
   m = O(n^2) modes; boson-sampling advantage is asymptotic in photon
   number, not present at k=2). Frame accordingly.

## Precondition gate — write this BEFORE any N^2-cost work

Before building the symmetrized 2-particle space, the implementer must
write one paragraph stating **why the proposed HOM observable is not
reducible to the single-particle quantity** (i.e. why it is not
Falsifier C in disguise). If that paragraph cannot be written, the task
does not proceed — the synthetic falsifier would only reproduce Falsifier
C's near-negative. This mirrors the discipline that made TASK-0140
(chiral) legitimate: it survived because Hodge orthogonality was provable
by construction; the HOM observable needs its own such argument.

## Intent Contract

- Outcome: (1) construct the symmetrized two-boson Hilbert space and
  Hamiltonian from the existing single-particle `H_0` (tractable at k=2,
  N~950); (2) define the bunching/coincidence observable as a function
  of the second seed's position (first seed fixed at the active site);
  (3) score per-candidate.
- Why required, not assumed: whether two-boson path interference carries
  allosteric-coupling information beyond the single-particle walk is
  untested — but the prior is low precisely because every single-particle
  observable in this project inherits the same proximity confound, and
  bunching is itself a spatial-mode-overlap effect that is distance-
  correlated. Go in expecting a negative.
- In Scope:
  - Write the non-reducibility precondition paragraph FIRST (gate above).
  - Verify the reducibility citations (Valiant/Terhal-DiVincenzo/
    Aaronson-Arkhipov) directly before asserting them in the write-up.
  - Construct the k=2 symmetrized bosonic space and evolution.
  - Synthetic falsifier FIRST (dumbbell / two-region toy with known
    coupling) — does bunching track coupling at equal distance, and is
    it distinguishable from single-particle-squared?
  - Only if the falsifier passes: real-target scoring vs the proximity
    floor, CIs, permutation null; ASD unseen if mandatory clears.
- Out Of Scope:
  - Fermion, naive-co-occupation, and anyon/para/quon variants (dead;
    see corrections 1-3 above).
  - Any claim of asymptotic quantum advantage from k=2 (see ceiling
    above).
  - Reselecting the submission operator (Tier-2-gated, [[TASK-0100]]).
- Constraints And Invariants: second-seed convention and bunching-
  observable definition fixed once, stated, blind to labels.
- Planned Validation: the non-reducibility paragraph + synthetic
  falsifier are the minimum bar; real-target scoring only if both pass.

## In Progress

None

## TODO

- [ ] Write the non-reducibility precondition paragraph (gate).
- [ ] Verify Valiant / Terhal-DiVincenzo / Aaronson-Arkhipov citations.
- [ ] Construct k=2 symmetrized bosonic space + evolution from existing H_0.
- [ ] Synthetic falsifier: bunching vs coupling at equal distance,
      distinguishable from single-particle-squared?
- [ ] If passes: real-target scoring vs floor, CIs, permutation null.
- [ ] Report, with the honest ceiling (better observable != quantum
      advantage at k=2).

## Dependency

- [[TASK-0094]] (Done) — proximity floor.
- [[TASK-0112]] (Done) — bootstrap CI.
- [[TASK-0130]] (Done) — single-particle propagator this builds on.
- Related (do not duplicate): Falsifier C, `.ai/reviews/REVIEW-2026-07-13b-operator-falsification-negative-controls.md`.

## Open Questions

- Bunching observable exact definition (coincidence probability vs
  connected correlation) — state and justify; connected correlation was
  flagged in-thread as partly a time-averaging artifact, so define
  carefully.

## Done

(not yet)
