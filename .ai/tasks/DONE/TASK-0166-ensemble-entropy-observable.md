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
- Status: Done
- Owner: Implementer
- Claimed By: Implementer D (this thread)
- Claimed At: 2026-07-25 10:20
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

- [x] Literature-confirm the standard GNM-based per-residue
      conformational-entropy formula (cite it, don't invent one).
- [x] Implement, reusing existing ANM/GNM mode machinery.
- [x] Score all 3 mandatory targets + generalization set.
- [x] TASK-0123 stratified AUC + permutation null.
- [x] Correlation-with-proximity-floor check (tests whether this is a
      genuinely different mechanism or reproduces the existing confound).
- [x] `RESULTS.md` section, framed explicitly as testing the ensemble/
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
  the source. **Resolved (see Done section): differential entropy of a
  Gaussian, per this task's own Intent Contract wording read literally
  ("participation-weighted sum of per-mode variance contributions" IS
  the Gaussian's own variance parameter) — the discretized-Shannon-over-
  normalized-weights alternative answers a different question (motion
  spread-across-modes, not motion amount) and was not what this task's
  own filing described.**

## Done

**Resolved 2026-07-28: a clean double negative — no significant signal,
and not proximity-orthogonal either.**

**Literature check (this task's own required disclosure):** Bahar,
Atilgan & Erman, *Fold. Des.* 2:173-181 (1997) — the founding GNM paper —
establishes each residue's fluctuation as Gaussian-distributed with
variance `sigma_i^2 = sum_k (1/lambda_k) U_ik^2` (the standard MSF
formula, already implemented in this codebase as `potentials._gnm_msf`,
here restricted to the lowest `n_modes=20` Kirchhoff eigenmodes rather
than the full spectrum, matching the register's own established low-
mode-subspace convention). The differential entropy of a univariate
Gaussian, `h = 0.5*ln(2*pi*e*sigma^2)`, is a textbook information-theory
identity (Cover & Thomas, *Elements of Information Theory*, 2nd ed.,
Thm. 8.4.1). New `allostery.conformational_entropy` combines these two
already-established results — no new physics invented, confirmed against
the codebase's own existing `_gnm_msf` via a direct regression test
(`n_modes >= N-1` reduces exactly to the full-spectrum formula, `rtol=
1e-10`).

**Implementation**: `src/allostery/conformational_entropy.py` —
`gnm_lowmode_variance(coords, cutoff, n_modes)` and
`residue_conformational_entropy(coords, cutoff, n_modes)`. Reuses
`potentials._kirchhoff_eigh` directly (the same GNM machinery
`transfer_entropy.py`/`lowmode_predictor.py` already use), no new
diagonalization primitive. 9 new unit tests (`tests/test_
conformational_entropy.py`): shape/finiteness, exact reduction to
`_gnm_msf` at full spectrum, monotonicity in mode count, correct
selection of the *slowest* modes specifically (not an arbitrary subset),
hand-verification of the entropy formula against the variance it
reports, and a real structural control (locally widening helix spacing
raises entropy in that stretch, not merely "runs without error").

**Real-target scoring** (`scripts/ensemble_entropy_real_run.py`): all 3
mandatory targets + 4 of the other `status: verified` targets (PTP1B,
GLUCOKINASE, CASPASE1, CASPASE7) — 7 cells. MYC_MAX (also `status:
verified`) deliberately excluded, not silently skipped: its own config
states `allosteric_pocket_exists: false`/`holo_pdb: null` explicitly (an
IDP heterodimer with no surface pocket at all, per its own `objective`
field) — confirmed directly when a first draft including it failed with
`ValueError("... no 'holo_pdb' defined")`, not treated as a bug to work
around.

Methodology matches the register's current (post-[[TASK-0158]]) standard:
TASK-0123 distance-stratified AUC (well-powered-shell max, shells =
`-hop_from_seed`) + [[TASK-0158]]'s corrected `nulls.compact_patch`
permutation null used directly (this task postdates TASK-0158; no reason
to use the superseded scattered draw even once) + `diagnostics.
classify_failure` + Spearman correlation against both proximity floors
(`-hop_from_seed`, `-euclid_from_seed_centroid`), per this task's own
Planned Validation requirement to report orthogonality-or-not explicitly.

**Result 1 — no significant signal**: zero of 7 cells survive Bonferroni
correction (α/7=0.00714). GLUCOKINASE (well-powered max AUC 0.971,
p=0.035) is the closest near-miss anywhere in the table but does not
clear the corrected bar. KRAS_G12C 0.730/p=0.241, BCR_ABL1 0.741/p=0.326,
CARDIAC_MYOSIN 0.623/p=0.394, PTP1B 0.356/p=0.712, CASPASE1 0.371/p=0.677,
CASPASE7 0.353/p=0.718. Consistent with [[TASK-0161]]'s program-wide
"zero confirmed positives" finding — this task adds one more real,
honestly-reported negative to that count, not an exception to it.

**Result 2 — not proximity-orthogonal, despite having no seed or
propagation step at all**: ρ(entropy, −hop-from-seed) is strongly
positive on every target (0.39 KRAS_G12C to 0.76 CARDIAC_MYOSIN),
matching the same confound magnitude found pervasively elsewhere in this
register (e.g. [[TASK-0146]]'s +0.68 to +0.72). This directly answers
this task's own Planned Validation question: unlike [[TASK-0140]]'s
chiral circulation (proximity-orthogonal by construction) or
[[TASK-0149]]'s mode-filtered PRS/DCC (built specifically to weaken this
confound), a Gaussian-entropy reframing of GNM low-mode flexibility has
no structural guarantee of distance-independence, and empirically
delivers none.

**A limitation worth stating plainly, not hidden**: entropy is a
strictly increasing function of the underlying low-mode variance
(`0.5*ln(2*pi*e*sigma^2)`), so every AUC/ranking result above is, by
construction, identical to what scoring raw `gnm_lowmode_variance` alone
would give — confirmed directly as its own regression test
(`test_strictly_monotonic_in_variance_so_auc_ranking_is_identical`). In
ranking terms, this task operationalizes and tests "does per-residue
low-mode flexibility magnitude predict the pocket" — a narrower claim
than the general ensemble-redistribution mechanism, and the answer is no
on this data. Out of Scope per this task's own filing (full ensemble
reweighting/Boltzmann conformer sampling, any MD) not attempted — stated
as a scope boundary, not silently expanded.

Docs updated additively: `RESULTS.md`'s new "Per-residue GNM low-mode
conformational entropy" section + open-questions row 43.

Full suite: 971 passed, 2 xfailed, 0 failed (7 new module-boundary tests
+ 2 pre-existing xfails, no regressions).
