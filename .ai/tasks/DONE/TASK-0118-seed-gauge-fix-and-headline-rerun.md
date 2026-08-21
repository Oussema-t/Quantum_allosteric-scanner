# TASK-0118 Fix the seed gauge: one convention, registered invariant, re-run floor/ceiling/actual

## Context

- ID: TASK-0118
- Title: Declare and enforce a single CTQW/GSR seed convention across
  `run_challenge.py`, `ceiling.py`/`ceiling_search_batched.py`, and every
  other scoring call site; register it as an invariant; re-run
  floor/ceiling/actual for all 3 mandatory targets under that one
  convention; correct `COMPETENCE_MAP.md`'s "ceiling below floor" claim.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer A (this thread)
- Claimed At: 2026-07-16 22:30
- Source: `.ai/reviews/REVIEW-panel-2026-07-16-v2.md` §2.1, §5 P0-1 — the
  panel's single highest-priority item ("reverses the central claim").
- Priority: **P0 — this week.** Blocks every floor/ceiling/actual number
  currently in `COMPETENCE_MAP.md`/`RESULTS.md`.
- **Dependency status, 2026-07-16: [[TASK-0090]] landed.** `select.py`'s
  `_hop_distances_from_source`/`ballistic_exponent` (multi-source BFS) and
  `source_specificity` (the actual crash site -- not `ballistic_exponent`
  as first assumed, checked by execution) are fixed and validated against
  real KRAS_G12C data (full 18-residue active-site array through
  `unsupervised_score`, finite differentiated scores, no crash). This task
  is now **unblocked and ready to start** -- the "claim TASK-0090 as this
  task's own first step" fallback in In Scope below no longer applies.

## Intent Contract

- Outcome: (1) `run_challenge.py`'s single-residue seed workaround
  (`source = int(np.sort(active_site_idx)[0])`, a TASK-0090 crash
  workaround, not a physics choice) is replaced by real multi-index
  seeding, unblocked by [[TASK-0090]]'s fix to `select.py`; (2) one
  seed convention is chosen and used everywhere — the panel recommends
  an **incoherent mixture over the active-site residues** (a coherent
  18-residue superposition asserts a specific relative phase with no
  biophysical basis; an incoherent mixture is the defensible object);
  (3) an `.ai/invariants/INV-XXXX` record is filed classifying seed
  definition as a GAUGE, closing the gap both `[[Q-0003]]` and
  `EXECUTION_PLAN.md`'s 5bbcdc4 note flagged and left unresolved; (4)
  floor (TASK-0094's baselines), ceiling (TASK-0046/TASK-0082), and
  actual (`run_challenge.py`'s live run) are all re-computed for
  KRAS_G12C, BCR_ABL1, and CARDIAC_MYOSIN under this one convention —
  not compared across the old mixed conventions again; (5)
  `COMPETENCE_MAP.md` is corrected from "ceiling below floor" /
  "the strongest evidence gathered" to **undetermined→recomputed**,
  citing this task, not silently overwritten (this project's standing
  no-silent-overwrite convention, per TASK-0104's precedent).
- In Scope:
  - Hard dependency: [[TASK-0090]] must land first (`select.py`'s
    multi-index crash) — do not route the seed convention around that
    bug again; if TASK-0090 is not yet claimed, claim it as this task's
    own first step rather than waiting idle.
  - The panel's own validation-strategy row (§6): sweep
    `source = {1, k-subset, full-array, incoherent-mixture}` × all 3
    targets: "AUC spread > 0.1 → it is a SIGNAL, not a gauge, the
    pipeline has no defined initial condition (current evidence: ≈0.3 →
    already failed)." Run this sweep explicitly as part of choosing and
    justifying the final convention, not skip it because the panel
    already flagged the likely answer — confirm on the real targets,
    do not assume the synthetic estimate transfers.
  - Explicitly reject the framing that fixing the seed produces a new
    *positive* claim. Per the review (§2.1): the other thread's
    "ceiling 0.524 clears the array floor 0.482 by +0.042" splices
    TASK-0046 (ceiling) with TASK-0093 (floor) — two different runs,
    different cutoff/label context. Report whatever the single-convention
    re-run actually finds — do not pre-decide it is a positive or a
    negative before running it.
- Out Of Scope:
  - The clock fix ([[TASK-0119]]) — separate gauge, separate task, do
    not conflate a seed-convention re-run with a t_max re-run in the
    same pass; if both land around the same time, the final headline
    re-run should use both fixes together and say so explicitly, not
    silently attribute a combined effect to only one.
  - The potential renormalization ([[TASK-0121]]) — different confound
    (diagonal contamination vs. observable contamination per §2.4),
    separate task.
- Constraints And Invariants:
  - Every floor/ceiling/actual number this task reports must cite which
    seed convention produced it — no bare number without that label,
    per this project's own GAUGE/KNOB/SIGNAL discipline.
  - `ceiling_context()`/`frozen_context()` gating (per TASK-0046/TASK-0100
    precedent) applies to the ceiling/actual re-runs the same as before —
    this task does not relax any existing leakage discipline.
- Planned Validation: the sweep in "In Scope" above, plus a full re-run
  of floor/ceiling/actual for all 3 targets under the chosen convention,
  reported with the seed-convention label attached to every number.

## In Progress

None

## TODO

- [x] Claim/verify [[TASK-0090]] is landed (multi-index `select.py` fix)
      before starting — hard dependency, do not route around it.
- [x] Run the seed-convention sweep (`{1, k-subset, full, incoherent
      mixture}` × 3 targets) on real data; report the AUC spread.
- [x] Decide the final convention (panel recommends incoherent mixture);
      state the decision and why in Done.
- [x] File `.ai/invariants/INV-XXXX` classifying seed definition as GAUGE.
      (Filed as [[INV-0006]] — classified KNOB, not GAUGE; see Done.)
- [x] Re-run floor (TASK-0094 baselines), ceiling (TASK-0046/0082 methodology),
      and actual (`run_challenge.py`) for KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN
      under the one chosen convention.
- [x] Correct `COMPETENCE_MAP.md`: replace "ceiling below floor"/"strongest
      evidence gathered" with the honest re-run result, framed as
      undetermined→recomputed, additive per the no-silent-overwrite
      convention (cite this task by ID).

## Dependency

- [[TASK-0090]] — hard blocker, must land first.
- Feeds [[TASK-0119]] (the clock fix should ideally use this task's
  chosen seed convention in its own re-run, not the old mixed one).
- Feeds [[TASK-0126]] (H13 ceiling comparison should also use the
  post-fix convention, not restart the confusion).

## Open Questions

- Whether the incoherent-mixture seed changes `select.py`'s own scoring
  formulas (uniform mass split, per `propagators.py`'s existing
  convention) or needs a distinct implementation — Implementer's call,
  state the choice and why in Done. **Answered in Done**: `select.py`
  itself is untouched; the incoherent mixture is a new `coherent=False`
  parameter on `propagators.ctqw`/`time_averaged_ctqw`, threaded through
  `analysis.benchmark`/`quantum_vs_classical` and `ceiling.
  consistency_score`/`ceiling_search`, but deliberately *not* into
  `select.unsupervised_score`'s own internal label-free selection
  heuristics — see Done's "scope boundary" note.

## Done

- 2026-07-16, Implementer A.

**1. Root capability — `propagators.py`.** Added `coherent: bool = True`
to `ctqw`/`time_averaged_ctqw` (default preserves every existing caller's
behavior byte-identically, verified by dedicated tests). `coherent=False`
computes an *incoherent statistical mixture* over a multi-index `source`
(`rho0 = (1/k) sum_i |i><i|`) instead of the existing *coherent* equal-
amplitude superposition (`psi0 = (1/sqrt(k)) sum_i |i>`) — implemented as
the average of each seed index's own independent single-source occupation
(unitary evolution is linear in the density matrix, so this needs no new
eigendecomposition, reusing TASK-0111's eigh-caching intact). New helper:
`_ctqw_mixture_from_eigh`. 13 tests in `test_propagators.py::
TestIncoherentMixture` (manual-average reference check, scalar-source
identity, genuine multi-index divergence on a real Hamiltonian, valid-
probability-vector checks).

**2. Real 3-target sweep, `scripts/seed_convention_sweep.py`** — swept
`{single, k_subset, full_coherent, full_incoherent}` (all four derived
from the same real active-site residue set, not four independent seed
choices) on `H_new` default config, `t_max=15`/`n_steps=500` (this
task's own scope: the seed axis only, not also the clock — TASK-0119's
job). **AUC spread**: KRAS_G12C 0.326, BCR_ABL1 0.079, CARDIAC_MYOSIN
0.049. KRAS_G12C decisively fails the panel's own stated GAUGE criterion
(spread > 0.1) — confirmed on real data, not just the panel's synthetic
0.61-Spearman estimate (which this real spread exceeds). **A second,
narrower finding**: within "full array," coherent-vs-incoherent alone
moves AUC far less than cardinality does (KRAS_G12C: 0.0081 vs. the
0.326 single-vs-full spread) — seed *cardinality*, not coherence, is the
dominant driver of the gauge problem.

**3. Classification — [[INV-0006]]** (not `INV-0005`, claimed twice this
session by [[TASK-0099]]/[[TASK-0109]] concurrently — see that record's
own numbering note). **Classified KNOB, not GAUGE**, contradicting this
task's own Intent Contract wording ("(3)... classifying seed definition
as a GAUGE") — checked by execution, found false on real KRAS_G12C data,
reported as found rather than as filed. The **declared convention**
(policy, not an invariance claim): full active-site array, incoherent
statistical mixture (`coherent=False`) — the panel's own recommendation,
adopted because a single defensible convention is required regardless of
whether it's invariant, and this one has no unphysical relative-phase
assumption and no crash-workaround cardinality reduction.

**4. Wiring — `coherent` threaded through the functions that produce
this task's own required re-run numbers**: `analysis.quantum_vs_
classical`, `analysis.benchmark`, `ceiling.consistency_score`,
`ceiling.ceiling_search`, `protocol.run_frozen_verdict` (all default
`coherent=True`, byte-identical for every existing caller — verified by
the full pre-existing suite passing unmodified, 190 tests across the 7
touched files). **Scope boundary, deliberate**: `analysis.ablation` and
`select.py`'s internal scoring (`focusing`/`source_specificity`/
`unsupervised_score`, used only by `select_frozen_config`'s label-free
*candidate selection*, not by any reported AUC) were **not** threaded —
`ablation` feeds only most/least-impactful-term diagnostics, not a
floor/ceiling/actual number this task must re-run; `select.py`'s
selection heuristics were built and tested against the coherent
superposition, and this parameter only needs to affect *reported* AUCs,
not which candidate wins (`run_frozen_verdict`'s own docstring states
this boundary explicitly). New wiring tests (spy-based, not AUC-diff-
based — AUC is rank-based and happens to be invariant to this specific
perturbation on several small synthetic test fixtures, a fixture/metric
property, not a wiring failure) in `test_analysis.py`, `test_ceiling.py`,
`test_protocol.py`.

**5. Pipeline call sites updated**: `run_challenge.py`'s single-index
crash workaround (`source = int(np.sort(active_site_idx)[0])`, cited by
its own module docstring as TASK-0090's workaround) replaced with the
full active-site array + `coherent=False`, threaded into
`run_frozen_verdict` and the winner-occupation/hit-list computation.
`ceiling_search_batched.py`'s `run()` gained `coherent: bool = False` as
its **own default** (already used the full array; only the coherence
axis changed) plus a `--coherent` CLI flag for old-convention A/B
comparison only, with an explicit docstring warning that resuming an old
checkpoint directory after changing `coherent` silently mixes
conventions within one "completed" trial set (checkpoint records don't
carry which convention produced them).

**6. Real re-run, all 3 mandatory targets, fresh checkpoint directories
(`results/tasks/0118/`, `results/tasks/0118_ceiling/` — deliberately not
resuming `results/tasks/0082/`'s old `coherent=True`-only ceiling
checkpoints):**

| Target | Floor | Ceiling | Actual | Diagnosis | Headroom |
|---|---|---|---|---|---|
| KRAS_G12C | 0.4818 | 0.5269 | 0.4614 | `NO_SIGNAL_IN_APO` | −45.3% |
| BCR_ABL1 | 0.5817 | 0.6057 | 0.5608 | `BEATS_CHANCE_NOT_FLOOR` | −86.9% |
| CARDIAC_MYOSIN | 0.7921 | 0.8439 | 0.8310 | `NO_FAILURE_DETECTED` | +75.1% |

**Findings, reported as found per this task's own explicit instruction
not to pre-decide positive or negative:**
- **KRAS_G12C's "ceiling below floor" is retracted.** Under the one
  correct convention, ceiling (0.5269) clears floor (0.4818) by +0.045 —
  real headroom exists in `H_new`'s physical-scalar space after all. This
  is **not** a new positive claim for the *actual* result, which remains
  below floor (chance-level) — same shape as BCR_ABL1, not a reversal to
  "the operator works."
- **BCR_ABL1**: same qualitative shape as before (ceiling clears floor by
  a modest margin, actual does not), numbers shifted slightly under the
  corrected convention (+0.024 margin vs. the old +0.047).
- **CARDIAC_MYOSIN**: diagnosis changed `INSUFFICIENT_RESOLUTION` →
  `NO_FAILURE_DETECTED` for **two independent reasons**, both reported —
  (a) this task's seed fix changed the AUC, and (b) an unrelated,
  pre-existing fact found while re-running this target:
  `diagnostics.LARGE_N_THRESHOLD` was already raised 800→1000 on
  2026-07-14 (that constant's own code comment, "explicit user
  direction," no task ID, predates this session's TASK-0118 work
  entirely), which alone flips this flag off regardless of the seed fix
  — `COMPETENCE_MAP.md`'s prior text was already stale before this task
  touched anything. The actual result now genuinely clears its own floor
  (+75.1% headroom), but this target's apo structure (5TBY, 20 Å docked
  homology model) still carries its own unresolved, independent data-
  quality caveat (`REVIEW-panel-2026-07-16-v2` §1.2's "worst structure in
  the set") — **not reported or endorsed as a clean positive**;
  [[TASK-0124]] is the right place to resolve whether this number is
  reportable at all.

**7. Documents updated**: `COMPETENCE_MAP.md` (full recompute per the
SUPERSEDED notice added at the top — old numbers preserved in prose, not
deleted, per this project's no-silent-overwrite convention/TASK-0104's
precedent); `[[Q-0003]]` (update note — the ceiling-below-floor finding
it was raised against no longer holds as stated; left Open for the
Architect/Planner to formally close/re-scope, not closed unilaterally
here); `.ai/memory/shared/pitfalls.md` P-0002 (resolution note — the
negative-denominator symptom it documents traced to a seed-convention
unit mismatch, not a genuine ceiling-below-floor inversion; extended
corollary added: confirm both sides of *any* cross-quantity comparison
share a convention, not just that the comparison's arithmetic is
well-defined).

**Tests**: 190 passed across `test_analysis.py`/`test_ceiling.py`/
`test_protocol.py`/`test_propagators.py`/`test_select.py`/
`test_run_challenge.py`/`test_report.py` (synthetic + non-network real-
target subset), plus the 4 real-network KRAS_G12C tests separately —
zero regressions from the `coherent` parameter threading. Not run through
`pytest_local.py wip-all` this session (targeted files only, established
precedent this session for avoiding the multi-session-contention hang).

**Not done, explicitly out of scope**: TASK-0081's ASD generalization-set
targets (PTP1B/CASPASE7) were not re-run under the new convention —
flagged as a gap in `COMPETENCE_MAP.md`'s Open Items for whoever picks up
TASK-0081/0127 next, not silently left inconsistent without a pointer.

**Discovered at close-out**: [[TASK-0119]] (the per-operator clock fix,
`t* = -ln(tol)/gap` replacing the fixed `t_max=15` every number above
still uses) landed **concurrently** with this task — claimed the same
minute (2026-07-16 22:30), by a different thread, entirely independently.
The two fixes were not combined into one re-run; `EXECUTION_PLAN.md`'s
own pre-existing text anticipated exactly this ("if both land around the
same time, the final headline re-run should use both fixes together...
not silently attribute a combined effect to only one"). Flagged in
`COMPETENCE_MAP.md`'s Open Items and `EXECUTION_PLAN.md`'s critical-path
note as the concrete next step — not completed here (would mean re-running
the full ceiling search a second time under yet another parameter change,
genuinely a separate piece of work, not a quick addendum).

**Also discovered at close-out (commit-time)**: this task's own uncommitted
edits to `protocol.py`, `EXECUTION_PLAN.md`, and `.ai/COMMON.md` had
already been swept into another thread's commit (`ef1e979`, "TASK-0112:
wire block-bootstrap CI into headline AUC reporting") before this task's
own GIT-COMMIT claim was taken — almost certainly a broad `git add` on
the shared working tree that picked up this task's still-uncommitted
changes alongside TASK-0112's own. Same failure shape as the incident
`.ai/memory/questions/toolsmith/answered/Q-0001-*.md` already documents
("a non-honoring thread's `git add` landed in another thread's staged
index despite the lock being held"). Not re-committed here (the content
at HEAD already matches this task's intended changes, verified by direct
diff before staging anything else) — noted for the record rather than
silently unremarked, since `ef1e979`'s own commit message does not
mention TASK-0118 or this task's own changes at all.
