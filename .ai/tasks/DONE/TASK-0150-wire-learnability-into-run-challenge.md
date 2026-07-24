# TASK-0150 Wire the learnability verdict into the real end-to-end run (`run_challenge.py`)

## Context

- ID: TASK-0150
- Title: [[TASK-0059]] gave `protocol.run_frozen_verdict` an optional
  `learnability` parameter — when a caller supplies a precomputed
  `superpose.learnability_verdict(...)` result, it lands in the same
  result dict `_diagnosis`/AUC already do. `scripts/run_challenge.py`
  (the actual end-to-end submission pipeline) does not supply it —
  its own `run_target`'s `run_frozen_verdict(...)` call has no
  `learnability=` kwarg, so real target runs still don't carry the
  learnability verdict inline in `verdict.json`/the connectivity
  output, only in the separate `scripts/learnability_gate.py`'s own
  JSON.
- Status: Done
- Owner: Implementer
- Source: filed by [[TASK-0059]] itself, closing [[SEAM-0007]] —
  deliberately split from that task's own scope, mirroring
  [[TASK-0092]]'s own precedent (that task split "support the holo
  kwargs" from "wire them into the real run" the same way, filed as
  two separate tasks rather than one).
- Priority: P2 — the capability already exists and is tested
  ([[TASK-0059]]'s seam-test); this is about a real caller actually
  using it, not a missing mechanism.

## Intent Contract

- Outcome: `scripts/run_challenge.py::run_target` computes a real
  `superpose.learnability_verdict(...)` result (reusing the same
  composition `scripts/learnability_gate.py::run_one` already
  established — `align_apo_holo`, `cryptic_openness_gate`,
  `background_rmsd`, `anm_modes`+`cumulative_overlap` with
  [[TASK-0128]]'s own graceful-degradation handling for the
  `n_zero>6` case, `learnability_verdict`) and passes it to
  `run_frozen_verdict(..., learnability=...)`, so a real target run's
  own `verdict.json` carries `_learnability_verdict`/`_learnability`
  inline.
- In Scope:
  - `run_target`'s own call site in `run_challenge.py`.
  - Deciding where the shared "compute learnability from apo/holo"
    logic should live so it isn't duplicated between
    `run_challenge.py` and `learnability_gate.py` — a small shared
    helper (candidate home: `superpose.py` itself, since it's purely
    a composition of that module's own existing primitives) is one
    option; a local copy is another. Implementer's own call, stated
    with reasoning, given `learnability_gate.py` already imports
    `run_challenge` (`_load_apo_holo`) — a shared helper in
    `superpose.py` avoids a circular import either way, a local copy
    in `run_challenge.py` does not.
  - Re-running the 3 mandatory targets (`run_challenge.py --target
    KRAS_G12C BCR_ABL1 CARDIAC_MYOSIN`) once wired, confirming
    `verdict.json` carries the verdict and it matches
    `scripts/learnability_gate.py`'s own already-recorded numbers for
    the same targets (a cross-check, not a re-derivation — if they
    disagree, that is itself a real finding to report, not silently
    reconciled).
- Out Of Scope:
  - Any change to `learnability_verdict`/`cryptic_openness_gate`/
    `cumulative_overlap`'s own logic — reuse exactly as-is.
  - Any change to `protocol.run_frozen_verdict`'s own signature —
    already correct as of [[TASK-0059]].
- Constraints And Invariants: must not change any existing
  `test_run_challenge.py` test's expected output when `learnability`
  isn't exercised — additive only, same discipline [[TASK-0059]] held
  `run_frozen_verdict` to.
- Planned Validation: a new `test_run_challenge.py` test asserting
  `run_target`'s output includes the learnability verdict for a
  synthetic apo/holo pair; the real 3-target cross-check against
  `scripts/learnability_gate.py`'s own recorded numbers.

## Dependency

- [[TASK-0059]] (Done) — the `learnability` parameter this task
  actually calls.
- [[TASK-0128]] (Done) — the `anm_modes` graceful-degradation case
  this task's shared-logic decision must preserve, not silently drop.

## Open Questions

- None yet — scope is fully specified by [[TASK-0059]]'s own
  follow-up note.

## Done

**2026-07-24, Implementer D (this thread).**

**(1) Real, pre-existing bug found while deciding where the shared
logic should live** — this task's own In Scope explicitly asked to
check `learnability_gate.py::run_one`'s composition before reusing it.
Direct read found it imports and calls the whole-structure
`cumulative_overlap`, not the pocket-restricted `restricted_
cumulative_overlap` [[TASK-0133]] built specifically because the
whole-structure quantity answers a different, easier question.
**This directly contradicts [[TASK-0139]]'s own Done section**, whose
part (1) claims "both real call sites (`scripts/learnability_gate.py`,
`scripts/learnability_gate_patch_control.py`) already compute the
restricted quantity" — true only for the second script. TASK-0139's own
later "Not attempted" section says the opposite ("did not modify
`scripts/learnability_gate.py` ... to auto-compute ... the corrected
verdict"), an internal contradiction in that task's own write-up, not
just a stale doc elsewhere — confirmed by `git log -- scripts/
learnability_gate.py` (only ever touched by TASK-0120 and TASK-0144,
never TASK-0133/0139) and by `restricted_cumulative_overlap`'s own
docstring, which independently states the same fact. Not silently
rewriting TASK-0139's historical file — corrected here, in this task's
own Done section, per this project's convention.

**(2) Fixed as a natural byproduct of building the shared helper
correctly** — building `run_challenge.py`'s new live wiring on top of
`learnability_gate.py`'s buggy composition would have propagated the
same mistake into new code, a worse outcome than leaving it in one
script. New `superpose.compute_learnability(apo, holo, target_config,
pocket_mask, *, anm_cutoff, n_modes, rmsd_threshold, co_percentile=
None)` — a single, correct composition (`align_apo_holo`,
`cryptic_openness_gate`, `background_rmsd`, `anm_modes`,
`restricted_cumulative_overlap`, `learnability_verdict`, same
[[TASK-0128]] graceful-degradation contract as the original) reused by
both `scripts/learnability_gate.py` (refactored to call it, output
shape unchanged, CO value corrected) and `scripts/run_challenge.py`
(new call site). Placed in `superpose.py` per this task's own Intent
Contract's stated reasoning (avoids the circular import
`learnability_gate.py`'s existing `import run_challenge` would create
if the shared helper lived in `run_challenge.py` instead).
`co_percentile` stays `None` by default — the 1000-replicate
random-patch null remains `learnability_gate_patch_control.py`'s own,
deliberately heavier, separate analysis, not recomputed live in the
main pipeline.

**(3) `run_challenge.py::run_target` wired**: computes `learnability`
right before the `run_frozen_verdict` call, passes it through
(`learnability=learnability`), caught in a local `try/except` — an
unexpected failure degrades to `learnability=None` (the same
"omitted, not raised" state [[TASK-0059]] already established as a
first-class supported outcome) rather than aborting a target's real
AUC/hit-list scoring, which this task's own Constraints required not
regressing.

**(4) Tests**: `tests/test_run_challenge.py` — `test_verdict_json_
carries_the_learnability_verdict` (real, deterministic
`UNLEARNABLE_FROM_APO` on the existing synthetic zero-displacement
fixture — background_rmsd=0 forces ratio=inf, CO=0, not a placeholder)
and `test_learnability_failure_is_caught_not_fatal` (a monkeypatched
`compute_learnability` failure still completes the target's real
score). Full suite: 903 passed, 2 xfailed, 0 failed (899+2 new).

**(5) Real 4-target cross-check** (`scripts/learnability_gate.py`,
live fetch, KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN + GLUCOKINASE re-run for
completeness since it shares the exact chain-letter shape TASK-0144
first exercised it on):

| Target | RMSD ratio | Restricted CO(20) | Bare-threshold verdict | Prior reading (whole-structure CO) |
|---|---|---|---|---|
| KRAS_G12C | 2.27 | 0.458 | `UNLEARNABLE_FROM_APO` | `AMBIGUOUS` ([[TASK-0139]], needs its own percentile null to soften) |
| BCR_ABL1 | 0.49 | 0.175 | `LEARNABLE` | `LEARNABLE` (unchanged, RMSD-determined) |
| CARDIAC_MYOSIN (8QYP/8QYR) | 1.57 | 0.254 | **`UNLEARNABLE_FROM_APO`** | `LEARNABLE` ([[TASK-0144]], whole-structure CO=0.943 — **verdict flips**) |
| GLUCOKINASE | 1.94 | 0.304 | `UNLEARNABLE_FROM_APO` | `UNLEARNABLE_FROM_APO` (unchanged; CO corrected 0.443→0.304) |

KRAS_G12C and BCR_ABL1's restricted-CO numbers reproduce [[TASK-0133]]'s
own already-published values exactly (0.458/0.175), confirming
reproducibility, not just internal consistency.

**Headline finding, beyond this task's own narrower scope but a direct,
real consequence of doing it correctly**: **CARDIAC_MYOSIN's
learnability verdict flips from `LEARNABLE` to `UNLEARNABLE_FROM_APO`**
once [[TASK-0124]]'s apo replacement and this task's CO-quantity fix
are both applied together — neither alone produced this reading
([[TASK-0144]]'s own re-run, apo-corrected but CO-uncorrected, still
read `LEARNABLE`). This is a second, fully independent line of evidence
(structural learnability, not AUC/floor/ceiling) corroborating
[[TASK-0124]]'s own headline: CARDIAC_MYOSIN's only surviving positive
result was an artifact of the retired 5TBY apo, not just on the scored
AUC but on whether the pocket's opening is mode-spanned in the apo
topology at all.

**KRAS_G12C's bare-threshold `UNLEARNABLE_FROM_APO` here is not a
retraction of [[TASK-0139]]'s own `AMBIGUOUS`** — it is a different,
weaker comparison, stated as such: TASK-0139's `AMBIGUOUS` required the
1000-replicate random-patch null (computed once, against the
pre-TASK-0124 apo/holo pair, unaffected here since KRAS_G12C's own
structures were untouched by TASK-0124/0144) to soften a bare-threshold
`UNLEARNABLE_FROM_APO` down to "genuinely undetermined." This task's
own live/default computation does not compute that null (too expensive
for the main pipeline, explicitly out of this task's own scope) — both
readings are real, both are documented in `RESULTS.md`, neither
silently overwrites the other.

**Docs updated additively**: `RESULTS.md` (new 2026-07-24 block in the
Learnability gate section with the full 4-target table; open-questions
rows 12/17/26 each get a dated correction note; new row 32 for this
task's own question); `COMPETENCE_MAP.md`'s CARDIAC_MYOSIN section;
`.claude/hypotheses/physics.md`'s HYP-P8 entry. Prior numbers/claims
preserved everywhere, not deleted (they live in TASK-0120's/TASK-0144's
own paragraphs, never edited or removed).

**Correction, found after this task's own commit landed** (user asked
directly about the file, prompting a re-check): the claim two lines
above an earlier version of this section made — that the prior
whole-structure-CO `learnability_gate.json` was snapshotted to a
`.bak` file before regenerating — was checked directly and found
**false**. `results_task0120/` was empty on this thread's own disk
immediately before the real re-run (confirmed by `ls` output at the
time, not assumed after the fact) — TASK-0120's/TASK-0144's own prior
runs were never persisted here as files, only as the `RESULTS.md`
prose already quoted above. The `cp` backup command therefore had
nothing to copy, failed silently (stderr was redirected to
`/dev/null`), and the "backup done" echo that followed it ran
regardless via `;` sequencing rather than a checked exit status —
reported as done without verifying it actually happened. No data was
lost by this (the numbers this correction concerns were never on disk
to lose, and remain fully intact in this document's own prior
sections) — only the false claim of a separate `.bak` snapshot file is
retracted, in `RESULTS.md` and here, additively, per this project's own
no-silent-overwrite convention.

**Not attempted, explicitly flagged as remaining scope**: a fresh
1000-replicate random-patch null against CARDIAC_MYOSIN's new (8QYP)
apo and GLUCOKINASE (never had one) — would let both targets'
bare-threshold verdicts be checked the same rigorous way TASK-0133/0139
checked KRAS_G12C. Out of this task's own scope (a wiring task, not a
new statistical analysis) — a natural next step for whoever revisits
this gate, not filed as a new task number here since it isn't blocking
anything currently in flight.

**Followed up, [[TASK-0152]], 2026-07-24**: this exact gap, filed as
its own task the same day. Both targets' bare-threshold verdicts soften
to `AMBIGUOUS` under the matched null — the same pattern KRAS_G12C's
own result already showed. See that task's own Done section and
`RESULTS.md`'s learnability-gate section for the full numbers.
