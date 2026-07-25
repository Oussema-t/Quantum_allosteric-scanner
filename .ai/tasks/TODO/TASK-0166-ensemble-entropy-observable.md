# TASK-0166 Ensemble/entropic observable — per-residue conformational entropy from GNM mode participation

## Context

- ID: TASK-0166
- Title: `PANEL_REVIEW_2026-07-25.md` §7.3(1)/V9 — the challenge's own
  reference [4] (Motlagh & Hilser 2014, *Nature*) argues allostery is
  **ensemble redistribution**, not signal transmission — a mechanism the
  entire program has tested zero routes of. Every observable in this
  project seeds at the active site and asks "where does signal go,"
  which presupposes a directed-channel picture. The ensemble picture
  says a cryptic pocket exists because the conformational *ensemble*
  contains states where it is open, not because something propagates
  there. This is computable from GNM mode participation with **no MD**,
  is challenge-legal, and — per the review — is higher-expected-value
  than any remaining quantum route, because if correct it would
  *mechanistically explain* the program's entire negative result rather
  than just adding one more null.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `PANEL_REVIEW_2026-07-25.md` §2.4, §3.1, §7.3(1), V9.
- Priority: **P1** — real, cheap (uses existing GNM machinery,
  `superpose.anm_modes`/`potentials._kirchhoff_eigh` already computed
  for every other observable), and tests a mechanism, not just another
  route to the same directed-channel picture that has failed ~a dozen
  times already.

## Intent Contract

- Outcome: a per-residue conformational-entropy score derived from GNM
  mode participation — e.g., the Shannon/differential entropy of each
  residue's fluctuation distribution under the low-mode subspace
  (participation-weighted sum of per-mode variance contributions,
  standard GNM entropy formalism — cite the specific formula used, do
  not invent one; Implementer's own literature check for the exact
  established form before implementing) — scored against the holo
  pocket label with the project's own AUC/floor/stratified-null
  machinery, same discipline as every other observable in the register.
- Why required: this is the one mechanism named by the challenge's own
  cited reference that the project has never operationalized, and a
  positive result here would explain *why* the directed-channel
  observables have uniformly failed (ensemble redistribution doesn't
  require a propagation path at all) rather than adding another
  negative to the pile.
- In Scope:
  - New function (natural home: `analysis.py` or a new small module,
    Implementer's own call), computing per-residue conformational
    entropy from the existing GNM/ANM low-mode decomposition — no MD, no
    new structure-fetch requirement.
  - Score against all 3 mandatory targets + generalization set, same
    AUC/floor/[[TASK-0123]] stratified-AUC/permutation-null discipline
    as the rest of the register.
  - Explicit framing distinguishing this from the directed-channel
    family: report whether entropy-based ranking correlates with (or is
    orthogonal to) the proximity floor and the program's existing
    directed-channel scores — a genuinely different mechanism should, if
    real, show low correlation with the confound that has dominated
    every other observable.
- Out Of Scope:
  - Any MD simulation — GNM-mode-based entropy only, per this task's own
    "no MD, challenge-legal" framing.
  - Full ensemble reweighting / Boltzmann-weighted conformer sampling —
    a much larger undertaking than a mode-participation entropy proxy;
    state this scope boundary explicitly if picked up, don't silently
    expand.
- Constraints And Invariants: same seed/labels/cutoff conventions as the
  rest of the register — no bespoke setup tuned to make this observable
  look better.
- Planned Validation: AUC vs. floor, stratified AUC + permutation null,
  correlation-with-proximity-floor check, all 3 mandatory targets +
  generalization set; report whichever way it comes out, including a
  clean negative (still valuable — it would mean the ensemble mechanism
  also isn't visible at Cα/GNM resolution, closing another route
  honestly).

## TODO

- [ ] Literature-confirm the standard GNM-based per-residue
      conformational-entropy formula (cite it, don't invent one).
- [ ] Implement, reusing existing ANM/GNM mode machinery.
- [ ] Score all 3 mandatory targets + generalization set.
- [ ] TASK-0123 stratified AUC + permutation null.
- [ ] Correlation-with-proximity-floor check (tests whether this is a
      genuinely different mechanism or reproduces the existing confound).
- [ ] `RESULTS.md` section, framed explicitly as testing the ensemble/
      entropic mechanism (challenge ref [4]), not another directed-
      channel route.

## Dependency

- `superpose.anm_modes`/`potentials._kirchhoff_eigh` (existing) — the
  mode decomposition this task reuses.
- [[TASK-0123]] (Done) — stratified AUC + permutation-null methodology.
- [[TASK-0094]] (Done) — proximity floor for comparison.

## Open Questions

- Exact entropy formalism (differential entropy of a Gaussian
  fluctuation model vs. a discretized Shannon entropy over mode
  participation weights) — resolve via literature check at pickup, cite
  the source.

## Done

(not yet)
