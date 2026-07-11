# Phase 3 Review (TASK-0006 `protocol.py` / TASK-0007 `select.py`)

## Reviewer

Code Reviewer overlay ("Reviewer B" this session — TASK-0048's Context line
was a free-text session label, not a reserved sub-role; see
`.ai/memory/questions/architect-planner/answered/Q-0001-reviewer-b-pickup-of-task-0048.md`).
Same evidence-first method as the Foundation review
(`REVIEW-2026-07-07-foundation-0003-0005.md`): check implementation against
each task's own Intent Contract, run the tests, don't trust green alone.

## Linked Tasks

- `.ai/tasks/DONE/TASK-0006-protocol-py.md`
- `.ai/tasks/DONE/TASK-0007-select-py.md`

Foundation (TASK-0003/0004/0005) already reviewed, out of scope here. Phase 4
(TASK-0008+, TASK-0056) is a separate future pass.

## Scope

- `__WORK_IN_PROGRESS__/src/allostery/protocol.py` + `tests/test_protocol.py`
- `__WORK_IN_PROGRESS__/src/allostery/select.py` + `tests/test_select.py`
- Cross-task: `unsupervised_score`/`frozen_context` call-site contract,
  `PLAN.md` `[have]`-tag drift, leakage-boundary docstring consistency

## Test Execution

- `pytest __WORK_IN_PROGRESS__/tests/test_protocol.py test_select.py -v`:
  **35 passed**, 0 skipped. Neither file has a network/optional-dependency
  gate (both use only synthetic coordinates/graphs), so there was nothing to
  install-and-re-run beyond the Foundation review's `prody` case.
- Full WIP suite (`python3 .ai/tools/pytest_local.py wip-all`): **343
  passed, 4 skipped, 1 xfailed** — no regressions attributable to this
  cluster; the xfail is the pre-existing SEAM-0005 marker (TASK-0058, not
  this scope).

## Findings

### P2

- **`protocol.get_functional_indices` silently drops two of
  `labels.functional_indices`'s parameters — `heavy_atom_coords` and
  `heavy_atom_seq_index` — forcing every FROZEN-path caller onto the
  coarser Cα-only contact approximation with no way to opt into the more
  accurate path without bypassing the firewall.**
  `labels.functional_indices` accepts both (`labels.py:337-343`) and passes
  them straight to `_contact_residue_indices`, whose own docstring says the
  heavy-atom-vs-Cα distinction is "material, not cosmetic, for real
  structures" (`labels.py:160-165`). `protocol.get_functional_indices`
  (`protocol.py:117-122`) only forwards `coords, ligand_groups,
  target_config, cutoff` — the two heavy-atom params aren't in its
  signature at all, so a caller can't supply them through the gate. This is
  a real interface gap, not just a missing test: any current or future
  FROZEN-path caller needing heavy-atom-refined contacts must either accept
  the silently-degraded Cα-only result or call `labels.functional_indices`
  directly, defeating the exact firewall TASK-0006 exists to enforce.
  Compare the other two gated accessors: `get_pocket_mask` forwards
  `holo_pocket_mask`'s full signature exactly (`protocol.py:109-114`), and
  `get_superpose_report` uses `**kwargs` so it can never fall behind
  `run_superpose`'s signature (`protocol.py:125-132`) — `get_functional_indices`
  is the one accessor of the three built with an explicit, incomplete
  parameter list instead of either of those two safer patterns.
  - Evidence: `protocol.py:117-122` vs. `labels.py:337-343`,
    `labels.py:151-172`.
  - Impact: no current caller is broken today (no real caller exists yet —
    see the unsupervised_score cross-task check below), so this hasn't
    produced a wrong result in the wild. It will silently produce a less
    accurate pocket read the first time a FROZEN-path caller needs
    heavy-atom precision and doesn't notice the parameter is missing.
  - Filed as [TASK-0063](../tasks/TODO/TASK-0063-functional-indices-gate-parameter-gap.md).

- **`select.unsupervised_score` has no wired consumer anywhere in
  production code — a real, previously-unregistered seam, missed by
  TASK-0053's same-day sweep.** `select.py`'s own docstring correctly
  states its intended call site ("usable inside
  `protocol.leave_one_protein_out`'s FROZEN loop"), which satisfied this
  task's own cross-task check on paper. But `grep -rn
  "unsupervised_score|from .select" __WORK_IN_PROGRESS__/src/allostery/*.py`
  returns zero hits outside `select.py` itself — `analysis.py` (TASK-0008,
  Done, landed after `select.py`) never imports it. Same shape as
  SEAM-0006/SEAM-0007 (producer and intended-consumer both reached Done,
  the wiring between them never landed) — added as
  [SEAM-0009](../seams/SEAM-0009-select-unsupervised-score-frozen-consumption.md),
  owner [TASK-0064](../tasks/TODO/TASK-0064-wire-unsupervised-score-into-frozen-loop.md).
  Read `.ai/reference/SEAM_PROTOCOL.md`/`.ai/reference/INVARIANCE_PROTOCOL.md`
  (both landed today, after this task file was originally written) as part
  of closing this review — TASK-0064 also flags that `select.py`'s
  reported quantities have no `.ai/invariants/` GAUGE/KNOB/SIGNAL table
  yet, a second, related gap left for that task rather than built here
  without empirical verification.

### P3

- **`PLAN.md`'s `protocol.py` row is stale — still tagged `NEW` even though
  TASK-0006 is Done.** TASK-0007's own Done section describes correcting
  `select.py`'s row from `NEW` to `[have]` "in this commit" (singular —
  only `select.py`), and the table on disk confirms that: `PLAN.md:185`
  correctly reads `[have]` for `select.py`, but `PLAN.md:186` still reads
  `protocol.py      NEW: DEV/FROZEN firewall + leave_one_protein_out —
  TASK-0006` with no corresponding fix ever landing for that row. The
  TASK-0048 Intent Contract's own suspicion ("`PLAN.md`'s stale `[have]`
  tag on `select.py`/`protocol.py`") had the direction backwards for
  `select.py` (that one's fine) but right for `protocol.py` (that one's
  genuinely stale).
  - Evidence: `.ai/tasks/PLANS/PLAN.md:185-186`; TASK-0007 Done section
    ("`select.py`'s row corrected from `NEW` to `[have]` in this commit").
  - Impact: cosmetic — a reader of `PLAN.md`'s repo-structure table would
    incorrectly conclude `protocol.py` doesn't exist yet. One-line fix,
    same as TASK-0007's own precedent of correcting this table inline
    rather than filing a task; left as a note here rather than edited
    directly, since fixing project docs isn't this review's role (see
    Foundation review precedent — report, don't fix).

## Confirmed / No Action Needed

- **`frozen_context`/`ceiling_context` are phase-switchable, not a blanket
  lock** — `ceiling_context()` blocks nothing (`protocol.py:61-71`),
  `frozen_context(X)` blocks only the named target(s)
  (`protocol.py:74-87`), innermost-context-wins on nesting
  (`test_nested_context_innermost_wins`). Matches TASK-0006's Constraint
  exactly ("switchable per phase, not a single global flag").
- **`leave_one_protein_out` yields every target exactly once per pass**,
  train set always excludes the held-out target, empty input yields
  nothing, and the generator itself never enters a context (composability
  over magic, as documented) — all four covered by
  `TestLeaveOneProteinOut`, all passing.
- **The gate wraps the real accessor functions, not a parallel
  reimplementation** — confirmed `get_pocket_mask`/`get_superpose_report`
  import and call `labels.holo_pocket_mask`/`superpose.run_superpose`
  directly at call time (`protocol.py:112`, `:130`), not a re-derivation.
  (`get_functional_indices` also calls through correctly — see the P2
  finding above for its narrower parameter surface, a signature gap, not a
  reimplementation.)
- **Unit tests cover both the "should raise" and "should permit" paths**
  for all three gated accessors, plus the "only the named target is
  blocked" case (`test_gate_only_blocks_the_named_target_not_others`) — 21
  tests in `test_protocol.py`, all passing.
- **`select.py` is fully label-free** — `grep -in "holo|label|ligand|pocket"
  __WORK_IN_PROGRESS__/src/allostery/select.py` returns only docstring
  prose (e.g. "never labels", "label-free"), zero code-level references;
  module-level imports are `numpy` only, with `propagators`/`metrics`
  imported locally and neither touches holo/label data. Every function
  (`focusing`, `source_specificity`, `ballistic_exponent`,
  `unsupervised_score`) is computable from `H` and a seed index alone, per
  TASK-0007's Constraint.
- **`focusing` reuses `metrics.ipr` directly**, not a reimplementation
  (`select.py:15-28`, `from .metrics import ipr`).
- **Synthetic path/star/complete graphs give clearly distinct readings** —
  confirmed via `TestFocusing`/`TestSourceSpecificity`/`TestBallisticExponent`,
  all passing; TASK-0007's own Done section additionally documents the
  empirical numbers behind each directional assertion, checked before the
  test was written rather than guessed.
- **`unsupervised_score` is a real combination, not a stub passthrough** —
  z-scored sum of all three metrics (`select.py:209-213`), tested for
  correct shape, zero mean, identical-input tie, and differentiation
  between distinct candidates (`TestUnsupervisedScore`, 4 tests, all
  passing).
- **`unsupervised_score`'s intended call site is documented even though no
  caller exists yet** — its docstring states directly: "Usable inside
  `protocol.leave_one_protein_out`'s FROZEN loop to pick a config for a
  held-out target without touching its holo pocket/labels"
  (`select.py:168-169`). Documentation confirmed correct and sufficient to
  satisfy this task's own cross-task check as originally scoped — but "no
  caller exists yet" turned out to be worth registering as its own seam,
  not just noting in passing; see the P2 finding above (SEAM-0009).
- **Leakage-boundary docstring language is consistent across all four
  modules.** `labels.py:10` ("this module is the only place downstream
  code may look at [holo]") is quoted near-verbatim by `protocol.py:24-25`;
  `select.py`'s framing ("never labels" / "without ever looking at labels",
  `select.py:6`, `:163`) is the complementary story for a module that must
  stay entirely outside the gate rather than being the gate itself — not
  an inconsistency, the correct framing for a module with zero holo access
  by design. Matches the Foundation review's prior spot-check of
  `labels.py`↔`protocol.py`↔`superpose.py`.

## Open Questions

- None beyond the two filed follow-ups (TASK-0063, TASK-0064) — the
  `PLAN.md` drift (P3) is small enough not to warrant its own task per
  TASK-0007's own precedent of inline one-line fixes; recommend whoever
  next touches `PLAN.md`'s repo-structure table fix the `protocol.py`
  row's tag at the same time.

## Seam / Invariance Protocol Cross-Check

`.ai/reference/SEAM_PROTOCOL.md` and `.ai/reference/INVARIANCE_PROTOCOL.md`
both landed today (TASK-0050/TASK-0051), after this task file was
originally written (2026-07-07) — read both before closing this review,
per the user's direction, rather than assuming TASK-0048's original scope
already covered them. Result: SEAM-0002 (protocol firewall, seeded at
TASK-0050's adoption) already covers TASK-0006's core boundary and needed
only a scope-clarifying note (see the P2 finding above), but SEAM-0009
(`select.unsupervised_score` -> no consumer) was genuinely missing —
TASK-0053's same-day sweep didn't catch it either, since its own scope
named four specific flows and this wasn't one of them. Registered here
rather than left implicit. `select.py`'s reported quantities also have no
`.ai/invariants/` GAUGE/KNOB/SIGNAL table — flagged as a TASK-0064
follow-up rather than built inline, since real classification needs
verification (per that protocol's own "multi-turn agreement is not
verification" rule), not asserted from reading the code once.

## Status

Findings above are P2/P3 only — no P0/P1 (blocking/structural) issues
found. Phase 3 slice (TASK-0006/0007) is sound and the FROZEN firewall does
what it claims for the two accessors that mirror their wrapped function's
full signature; the third (`get_functional_indices`) has a real but
currently-inert parameter gap, tracked as TASK-0063. Both modules are
individually correct and tested, but the composition between `select.py`
and its intended FROZEN-loop consumer never landed — tracked as SEAM-0009 /
TASK-0064, exactly the "correct parts, unverified edge" failure mode the
Seam Protocol exists to catch. No re-review required before Phase 4's own
pass (TASK-0056) unless TASK-0063 changes `protocol.py`'s public signature
in a way that also touches `select.py`'s assumptions (it shouldn't).
