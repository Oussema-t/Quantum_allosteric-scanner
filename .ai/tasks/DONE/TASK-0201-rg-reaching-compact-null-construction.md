# TASK-0201 A null construction that can actually reach real-pocket Rg

## Context

- ID: TASK-0201
- Title: build a compact-ish null-patch generator whose radius-of-gyration
  support actually covers real pocket geometry, for targets where
  `nulls.compact_patch`'s own k-NN-ball construction has a hard Rg ceiling
  below the real pocket's measured Rg.
- Status: Done
- Resolution: done
- Resolution Note: New nulls.graph_walk_patch (Eden-growth on the contact graph) reaches real pocket Rg where compact_patch structurally cannot; decisive 20k-replicate re-run flips PTP1B dcc_low k=10 to survive its pre-registered bar (p=0.0027 vs 0.003125), CARDIAC_MYOSIN unchanged. Mixed result per TASK-0190's own reading rule, flagged into RESULTS.md's zero-positives headline additively
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: [[TASK-0190]]'s own Headline finding (Done section,
  `.ai/tasks/DONE/TASK-0190-real-pocket-rg-matched-null.md`), 2026-08-03.
- Priority: P2 — does not change [[TASK-0190]]'s own already-decided
  negative verdict (a genuinely-reaching null would, if anything, be *more*
  lenient than the already-tried matched null, and `dcc_low` still failed
  to clear its bar under that more-lenient version). This closes a
  methodological gap for future work, not an open verdict.

## Why this matters

[[TASK-0190]] re-tested `dcc_low` (CARDIAC_MYOSIN, PTP1B) against
`nulls.compact_patch_matched(target_rg=<real pocket Rg>, tol=0.35)`. The
rejection sampler never raised `RuntimeError` (looked like it worked), but
the Planned Validation's own sanity check — "verify the matched null's own
draw-Rg distribution actually centres on `target_rg`" — caught that it
does not:

| Target | Real pocket Rg | `compact_patch`'s own max (20,000 draws) | Matched-null accepted-draw mean Rg |
|---|---|---|---|
| CARDIAC_MYOSIN | 9.628 | **7.784** (hard ceiling) | 6.544 |
| PTP1B | 7.969 | **7.134** (hard ceiling) | 6.024 |

For both targets, the real pocket's Rg is **above the maximum Rg a
contiguous k-NN ball of that pocket's own size can ever produce** on that
target's geometry — confirmed with 20,000 unconstrained draws (`p99.9 ==
max`, a hard support boundary, not a rare tail event). `tol=0.35`'s wide
acceptance window doesn't fail loudly (its lower bound overlaps the
proposal's own natural upper tail) — it silently accepts draws dominated by
that tail's own shape instead, which is a more dangerous failure mode than
outright infeasibility because it looks like it worked.

This directly answers a question this project has asked twice now (external
review §2.1 name-checks a `surf_frac`/surface-concavity axis; [[TASK-0190]]'s
own Open Questions repeats it): **a compact (k-NN ball) null is structurally
the wrong family for pockets this dispersed** — no tolerance widening fixes
it, because the underlying construction cannot produce the shape at all.

## Intent Contract

- Outcome: a null-patch generator (`nulls.py` or a new sibling module) that
  can produce compact-ish, contiguous, same-size patches whose Rg support
  genuinely covers real pocket Rg values on every mandatory + generalization
  target, verified the same way [[TASK-0190]] verified the current one
  failed (draw a large sample, confirm `target_rg` is within — not beyond —
  the observed range, before ever rejection-sampling toward it).
- Why required, not assumed: [[TASK-0190]] measured, decisively, that the
  current construction cannot do this for 2 of 3 targets tested — this is
  not a hypothetical gap.
- In Scope:
  - Characterize *why* `compact_patch` has this ceiling (a k-NN ball's
    Rg is bounded by local packing density around whichever seed residue
    was drawn — investigate whether a different seed-selection strategy,
    a non-ball contiguous-growth process, or a genuinely different shape
    family raises the reachable Rg).
  - At least one alternative construction, with its own Rg support
    characterized empirically (large unconstrained sample, not assumed)
    on the same 2 targets [[TASK-0190]] found infeasible for, before
    trusting it as "matched."
  - Re-run [[TASK-0190]]'s own `dcc_low` CARDIAC_MYOSIN/PTP1B cells against
    the new construction, genuinely centred this time (verify centring
    directly, same check that caught the original defect) — report
    whether the verdict changes (it may not; report either way).
- Out Of Scope:
  - Changing [[TASK-0158]]'s default null anywhere else in the register.
  - Re-litigating [[TASK-0190]]'s own already-closed verdict evaluation
    logic (survival bars, §5.3 reading rule) — reuse it.
  - The full `surf_frac`/surface-concavity axis as a general-purpose new
    observable family, if that turns out to be a much larger effort than
    a null-patch generator fix — scope down to "can it reach real Rg,"
    not "is it a physically complete concavity model," unless the smaller
    version turns out to be insufficient.
- Constraints And Invariants:
  - Verify the new construction's own Rg support empirically before using
    it for anything — this is the exact check that was skipped (or rather,
    run but not acted on until [[TASK-0190]]) for the current one.
  - State plainly whether [[TASK-0190]]'s own "dcc_low still doesn't
    survive, and a more-reaching null would only make that null more
    lenient" reasoning holds up once a real reaching null exists, or
    whether it was wrong.
- Planned Validation:
  - Large-sample (>=20,000, matching [[TASK-0190]]'s own diagnostic scale)
    unconstrained draw from the new construction on CARDIAC_MYOSIN/PTP1B;
    confirm `target_rg` sits within the observed range, not at or beyond
    its edge.
  - Re-run the two previously-infeasible-to-reach `dcc_low` cells; report
    the corrected matched p-value and whether it changes [[TASK-0190]]'s
    own verdict.

## In Progress

—

## TODO

- [x] Characterize why `compact_patch`'s Rg ceiling exists (seed-selection
  / local-density argument) — see Done section / `nulls.py`'s own docstring.
- [x] Prototype >=1 alternative construction; verify its own Rg support
  empirically (>=20,000 draws) before trusting it — `graph_walk_patch`,
  reaches 14.15/14.30 (max, 20,000 draws) vs. real pocket Rg 9.63/7.97.
- [x] Re-run `dcc_low` (CARDIAC_MYOSIN, PTP1B) against the new,
  genuinely-centred matched null — 20,000 replicates/cell, all 4 k-values,
  all 3 nulls side by side, ordering check passed on all 8 cells.
- [x] State whether [[TASK-0190]]'s verdict changes — **yes, on PTP1B**
  (survives its own bar); CARDIAC_MYOSIN's verdict is unchanged.

## Dependency

- [[TASK-0190]] (Done) — the finding this task fixes; its own evidence
  table is the starting point, not to be re-measured from scratch.
- [[TASK-0158]] (Done) — `compact_patch`'s own original construction and
  rationale.

## Open Questions

- Is the right fix a different seed-selection rule for the same k-NN-ball
  shape, or a genuinely different shape family (e.g. surface-patch growth,
  the review's own `surf_frac` framing)? Investigate before committing to
  either. **Answered**: a different seed-selection rule cannot work — the
  ceiling is intrinsic to "always take the closest available point," not a
  property of which seed is chosen (every seed's own k-NN ball is
  near-maximally tight, by construction). A genuinely different shape
  family was required; `graph_walk_patch` (randomized connected growth on
  the contact graph, not Euclidean nearest-neighbour) is that family — see
  Done section for why it reaches farther and the empirical confirmation.
- (New, raised by this task's own result) Does PTP1B's `dcc_low` (k=10)
  survival hold under a stricter Bonferroni family that accounts for the
  fact a new null construction was tried specifically because the first
  one failed a target (a form of researcher-degrees-of-freedom / multiple-
  null-testing)? Not addressed here — this task reused TASK-0190's own
  pre-registered bar unchanged, per its own Out-of-Scope ("reuse it, do
  not re-litigate the evaluation logic"), but a stricter reader could argue
  the act of building a second null after the first one's failure is
  itself a researcher degree of freedom that should widen the family. Named
  for whoever decides how this result is framed for [[TASK-0184]], not
  resolved here.

## Done

**2026-08-04, Implementer B.**

### Why `compact_patch` has a hard Rg ceiling (characterized, not assumed)

`compact_patch` always takes the `size` Euclidean-*closest* points to a
random seed — the tightest possible packing available in that seed's own
local neighbourhood, by construction (it can never skip a near point to
reach a farther one). Across every possible seed, the achievable spread is
bounded by how anisotropic the *densest* local packing gets anywhere in
the structure — for a Cα chain at roughly uniform local density (the
typical case), that ceiling is low and does not vary much with which seed
is drawn. This is why TASK-0190 found `p99.9 == max` across 20,000
draws on both affected targets: the ceiling isn't a rare-tail statistical
fact, it's close to a hard geometric one. A different seed-selection rule
cannot fix this (every seed's own ball is already near-maximally tight);
only a construction that doesn't require "closest first" can.

### `graph_walk_patch` — randomized connected growth on the contact graph

New `nulls.build_adjacency`/`nulls.graph_walk_patch`/`nulls.
graph_walk_patch_matched` (ADD-only, `nulls.py`). Each newly added residue
only needs to be adjacent to something already in the growing patch — not
close to the original seed — so the walk can wander along a curved surface
path (a groove, a cleft) and reach far greater Euclidean spread for the
same cardinality than a Euclidean-nearest-neighbour ball ever could.
Verified empirically before trusting it (this task's own Constraint, the
exact check that caught TASK-0190's original defect): 20,000 unconstrained
draws on both previously-infeasible targets — max Rg 14.15
(CARDIAC_MYOSIN, real 9.63, 83.8th percentile of support) and 14.30
(PTP1B, real 7.97, 17.9th percentile — not even in the upper tail). Both
real Rg values sit inside the support now, not at its edge.

### Matched-null centring: materially improved, not perfect

`graph_walk_patch_matched`'s own accepted-draw mean Rg came in at 8.613
(CARDIAC_MYOSIN, target 9.628) and 8.775 (PTP1B, target 7.969) — much
closer to target than `compact_patch_matched`'s own 6.544/6.024 (TASK-0190),
though still short of exact (the `tol=0.35` acceptance window's own
asymmetric proximity to the proposal distribution's mode remains a
residual effect, reported not hidden, not "fixed" further — a tighter
match would need a different sampling scheme, e.g. importance-reweighting
the growth process itself toward larger patches, named as a follow-up not
built here).

### Decisive re-run, 20,000 replicates/cell, all 3 nulls, ordering check on all 8 cells

Full table in `RESULTS.md`'s own "A null that can actually reach real
pocket Rg" section (not duplicated here). Headline:

- **CARDIAC_MYOSIN: verdict unchanged.** Min matched p = 0.0254 (k=15),
  3× its own bar (0.00833) — TASK-0190's "does not survive" conclusion
  holds under a null that can now genuinely reach this target's real
  pocket Rg, not one that structurally could not.
- **PTP1B: verdict changes.** `dcc_low` (k=10) survives its own
  pre-registered bar: p=0.0027 < 0.003125 (95% CI [0.0020, 0.0035] —
  point estimate clears, CI slightly straddles the bar; reported exactly,
  not rounded to a clean win). `real_auc=1.000` independently matches
  [[TASK-0151]]'s own already-published number for this exact cell — the
  same strong effect this project has measured multiple times, now
  surviving a correctly-specified null for the first time.
- **Ordering check (`p_scattered<=p_matched<=p_compact`) passed on all 8
  cells, zero violations** — the strongest available evidence this is a
  real result, not an artifact of the new construction (replay of the same
  check TASK-0190 itself used, at 20,000 replicates instead of 1,000).

**Mechanism named, not just observed, for why PTP1B flips and CARDIAC_MYOSIN
doesn't**: TASK-0190 reasoned a genuinely-reaching (more dispersed) null
could only be *more* lenient. That conflates "more dispersed" with "more
lenient for this specific score field" — `dcc_low` (low-mode dynamic
cross-correlation) plausibly scores tight, compact patches higher than
topologically-elongated ones of the same size, independent of location. A
null built from more-branching shapes (even Rg-matched to the real,
more-dispersed pocket) can therefore produce a *lower* null-score
distribution than a tight-ball null, making the real (compact) high-scoring
pocket look *more* extreme relative to it — smaller p, not larger. Reported
as a plausible, internally-consistent mechanism (matches the ordering-check
result), not independently verified beyond this (out of scope).

### Per TASK-0190's own pre-registered reading rule, this is now a mixed result

TASK-0190's own §5.3 reading rule, fixed before any of these numbers
existed: *"If exactly one [cell] survives... a mixed result, not smoothed
into complete negative."* That rule now applies literally: CARDIAC_MYOSIN
falsified, PTP1B survives. **[[TASK-0161]]/[[TASK-0191]]'s "zero confirmed
positives program-wide" headline no longer holds unqualified** — flagged
additively in both places in `RESULTS.md` (not corrected in place, per the
no-silent-overwrite convention) and in this document's own Open-Questions
row 60. Deciding how PTP1B's survival gets framed for [[TASK-0184]]'s
submission narrative is that task's own call, not this one's — this task's
job was the corrected number, delivered with every check this project's
own discipline requires (ordering check, replicate-count convergence to a
tight CI, independent AUC cross-reference, CI reported not hidden).

### A second synthesis gap found, flagged not fixed

[[TASK-0190]] itself has **no `RESULTS.md` section of its own** — the same
gap [[TASK-0191]] fixed for [[TASK-0167.003]] recurred one task later.
`RESULTS.md`'s new section covers both TASK-0190's own finding (recapped,
cited) and this task's fix, explicitly noting in its own opening banner
that it does not substitute for TASK-0190's own backfill. Named here as a
recurring pattern (this is the second time in two days a landed task's own
`RESULTS.md` section went missing) — worth its own process fix
([[TASK-0195]]'s territory), not attempted here.

### Additive changes

`nulls.build_adjacency`/`nulls.graph_walk_patch`/`nulls.
graph_walk_patch_matched` (new, ADD-only — every existing `nulls.py`
function's behaviour is byte-identical). New `scripts/
graph_walk_matched_null_rerun.py`. 24 new tests
(`tests/test_nulls.py::TestGraphWalkPatch`/`TestGraphWalkPatchMatched`).

### Tests

Full suite: `.venv/bin/python3 -m pytest -q tests/` — 1122 passed,
1 skipped, 2 xfailed, no regressions.

### Out of scope, confirmed not needed

No change to [[TASK-0158]]'s default null anywhere in the register (this
task adds a second null family, does not replace the first). TASK-0190's
own verdict-evaluation logic (survival bars, §5.3 reading rule) reused
unchanged, not re-litigated. BCR_ABL1's `T(E=0)` cell not re-run — its
target Rg (7.448) was already within `compact_patch`'s own natural range
per TASK-0190's own finding, so it was never in this task's own scope
(only CARDIAC_MYOSIN/PTP1B's structurally-unreachable cells were).
