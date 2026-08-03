# TASK-0201 A null construction that can actually reach real-pocket Rg

## Context

- ID: TASK-0201
- Title: build a compact-ish null-patch generator whose radius-of-gyration
  support actually covers real pocket geometry, for targets where
  `nulls.compact_patch`'s own k-NN-ball construction has a hard Rg ceiling
  below the real pocket's measured Rg.
- Status: TODO
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

- [ ] Characterize why `compact_patch`'s Rg ceiling exists (seed-selection
  / local-density argument).
- [ ] Prototype >=1 alternative construction; verify its own Rg support
  empirically (>=20,000 draws) before trusting it.
- [ ] Re-run `dcc_low` (CARDIAC_MYOSIN, PTP1B) against the new,
  genuinely-centred matched null.
- [ ] State whether [[TASK-0190]]'s verdict changes.

## Dependency

- [[TASK-0190]] (Done) — the finding this task fixes; its own evidence
  table is the starting point, not to be re-measured from scratch.
- [[TASK-0158]] (Done) — `compact_patch`'s own original construction and
  rationale.

## Open Questions

- Is the right fix a different seed-selection rule for the same k-NN-ball
  shape, or a genuinely different shape family (e.g. surface-patch growth,
  the review's own `surf_frac` framing)? Investigate before committing to
  either.

## Done

—
