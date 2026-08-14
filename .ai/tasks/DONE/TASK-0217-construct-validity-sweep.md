# TASK-0217 Construct-validity sweep (parent) — the register verified its statistics, never its constructs

## Context

- ID: TASK-0217 (parent; subtasks .001–.004)
- Title: systematically audit whether the quantities this register measures are
  the quantities it names — the failure class every correction in the
  2026-08-06→13 window belonged to, and the one its review apparatus does not
  cover.
- Status: Done
- Owner: Architect/Planner (parent), Implementer (subtasks)
- Claimed By: —
- Claimed At: —
- Source: Reviewer thread + orchestrating user, 2026-08-13, after a week in
  which six independent corrections all belonged to one class.
- Priority: **P0.** Estimated days, not weeks — the classes are enumerable and
  the audits are mostly mechanical.

## The diagnosis this family exists to act on

Between 2026-08-06 and 2026-08-13, six independent findings reversed or
qualified results that had each already survived multiple reviews. **Every one
moved the same direction** — from *"we have a result"* toward *"the
measurement was not measuring what it claimed."* Not once did a correction
reveal a hidden positive.

Noise reverses both ways. A one-directional drift has a common cause, and it
is identifiable:

> **The register built an elaborate apparatus for *statistical* validity —
> proximity floors, spatially-correct nulls, limits of detection,
> program-level multiplicity budgets, frozen-context provenance stamps — and
> almost none for *construct* validity: whether the quantity being measured is
> the quantity being named.**

Every defect found tests against that:

| Defect | Task | Class |
|---|---|---|
| Gate required `opt_rate > 1.0`, unattainable | [[TASK-0204]] D1 | criterion cannot express its own positive |
| Frustration signature required `joint < 0`, never observed | [[TASK-0208]] V1 | same |
| Bonferroni family made the gate unreachable (`1/n_reps > α`) | [[TASK-0189]] | same |
| Active site silently substituted by top-5 degree, 9/13 targets | [[TASK-0216]] | silent proxy substitution |
| Holo heavy-atom indices written into an apo-sized array | [[TASK-0216]] | silent misalignment |
| `backbone_explained` credits the backbone for displacement it merely carries | [[TASK-0208]] V3 | metric does not measure its name |
| 5 of 7 benchmark targets cannot express the apo-closed/holo-open contrast | [[TASK-0209]] | instances cannot express the construct |
| No positive control; apo-only sanity check for a cryptic pocket | [[TASK-0204]] D2 | absent control |

**Not one is a statistical error.** The statistics were sound throughout —
which is precisely why they survived every prior review: the reviews were
looking at the layer that was already correct.

## Why this is worth days, and what it will and will not change

**Predicted, stated before the sweep so it can be scored honestly:**

1. More construct-validity failures, concentrated wherever a helper can
   degrade silently rather than raise.
2. Essentially nothing in the statistical layer.
3. **Little change to the register's conclusions.** These failure modes
   preferentially threaten *positives*, not negatives: if the seed is wrong
   and nothing is found, the right seed usually also finds nothing — the space
   is dominated by the proximity floor either way. A wrong construct can
   manufacture a spurious positive; it rarely conceals a real one. The
   register has **one** positive, so the blast radius on conclusions is far
   smaller than the blast radius on individual numbers.

Evidence for (3) from the window itself: through six reversals the headline
never moved — nine routes closed by measurement, a benchmark that cannot
certify, no advantage available in the specified formulation at any N ≤ 704.
[[TASK-0204]] went from "closed on criterion #1" to "closed on complexity
grounds" (still closed, better evidence); [[TASK-0208]] went CLOSED →
INCONCLUSIVE (a conclusion *removed*, not reversed); [[TASK-0213]]'s CLOSED
weakened but the route stayed closed.

**A register whose conclusions survive its own corrections is in better shape
than one that has never been corrected.** That is the honest framing, and it
belongs in [[TASK-0184]] as a strength rather than being hidden.

## What this family is NOT

- **Not a re-run of ~190 tasks.** The failure classes are enumerable; the
  sweep targets those classes, not the register wholesale.
- **Not a re-litigation of the statistics.** Floors, nulls, LOD and the
  multiplicity budget are repeatedly checked and repeatedly clean. Leave them.
- **Not licence to retract numbers.** Every finding lands as an additive
  advisory (the [[TASK-0192]]/[[TASK-0201]] precedent), never a silent rewrite.

## Subtasks

| ID | Audit | Catches, retrospectively |
|---|---|---|
| **.001** | Silent degradation paths — every helper that returns a value where it should raise | [[TASK-0216]]'s top-degree fallback; the apo/holo index mismatch |
| **.002** | Criterion outcome-reachability + positive-control presence | [[TASK-0204]] D1/D2, [[TASK-0208]] V1, [[TASK-0189]] |
| **.003** | Seed/anchor provenance, register-wide | [[TASK-0216]] — started there, closed here |
| **.004** | Metric-construct audit — does each reported metric measure its own name? | [[TASK-0208]] V3's carriage confound |

Each subtask states its own retrospective test: **it must catch the already-known
defect in its class before it is trusted on anything new.** An audit that
cannot rediscover the bug that motivated it is not an audit.

## Intent Contract

- Outcome: a per-class findings list, additive advisories on affected
  `RESULTS.md` sections, and — where cheap — a permanent guard (test, warning,
  or assertion) so each class cannot recur silently.
- Why required, not assumed: six corrections in one week, all one class, all
  found by re-derivation rather than review. **Reading a task file has never
  once caught one of these; re-running the measurement has caught all of them.**
  That asymmetry is the argument for a mechanical sweep over another read-through.
- Constraints And Invariants:
  - Additive advisories only; no silent rewrites.
  - Each subtask's retrospective test runs first.
  - Report the count of *clean* checks too — "we audited 40 helpers and 3 were
    defective" is a materially different claim from "we found 3 defects."
- Planned Validation: the retrospective tests above, plus an explicit statement
  per subtask of what it did **not** cover.

## Dependency

- [[TASK-0216]] (seed provenance — .003 continues it)
- [[TASK-0209]] (instance validity — already done, not repeated here)
- Feeds [[TASK-0184]]: the sweep's own result is submission content.

## Open Questions

- Does the effective-rank finding ([[TASK-0199]]) interact with this? If ~28
  observables span ~3 dimensions, a construct defect in a shared upstream
  component (e.g. the seed) propagates to all of them at once. That is
  consistent with what [[TASK-0216]] found and is worth stating explicitly.
  **Resolved by .003 — yes, confirmed, not just consistent.** The seed
  defect was real on `PTP1B`/`CASPASE1`/`CASPASE7`, and `PTP1B` is both a
  fallback-seeded target and part of the effective-rank family's own
  generalization set — a shared upstream defect on one target reaches
  every seeded observable computed there, not just the one headline cell
  (`dcc_low`) .003 actually re-scored. **Left open, stated not
  quantified**: whether any *other* seeded observable on these 3 targets
  (CTQW, `prs_low`, transport, chiral, spectral coherence) would itself
  flip under the corrected seed — .003 deliberately scoped to the one
  cell a register-level conclusion rested on, per this family's own "not
  a re-run of ~190 tasks" boundary, not because the others are known
  unaffected.
- Should the convention amendment (state the positive control's expected
  result alongside the pass bar; demonstrate each verdict is reachable) land
  as part of .002, or separately? Recommend .002 — it is the same evidence.
  **Resolved — landed in .002**, `.ai/reference/INTENT_CONTRACT_TEMPLATE.md`'s
  own "Planned Validation" section, checked against all 4 known instances.

## Done

**2026-08-14, Implementer A — closing synthesis.** All 4 subtasks Done
(`.001` Implementer A, `.002` Implementer B, `.003`/`.004` Implementer A).
This section synthesizes across them; each subtask's own Done section is
the full record and is not repeated here.

### Combined denominator

| Subtask | Audited | Flagged/defective | Clean |
|---|---|---|---|
| .001 (silent degradation) | 15 fallback/degradation branches | 2 (1 already-known+fixed, 1 **new**) | 13 |
| .002 (criterion reachability) | 13 pre-registered criteria | 5 (3 known reachability + 1 known missing control, all pre-existing/already-fixed; 1 **new**, latent) | 8 |
| .003 (seed provenance) | 13 targets' seed provenance | 3 (post-fix; 1 headline cell re-derived) | 10 |
| .004 (metric construct) | 6 claim-bearing metrics | 4 (3 pre-existing, consolidated under this class for the first time; 1 **new** suspicion) | 2 |

**Register-wide: every subtask reports its clean count, not just its
defects**, per this family's own Constraint. The pattern across all four:
most of what was checked was already correct — construct-validity defects
are real but not the majority case, consistent with the family's own
"the classes are enumerable" framing rather than "the register is
broadly unreliable."

### The 3 genuinely new findings (not re-confirmations of already-known defects)

1. **.001 — the array-correspondence bug**: holo-space heavy-atom contact
   indices used directly as apo-space indices, live and unfixed until this
   sweep, on 10/13 targets including 2/3 mandatory. Distinct from
   [[TASK-0216]]'s own top-degree-fallback finding (a different bug in the
   same function). Fixed with a permanent, additive guard.
2. **.002 — the latent `fpocket_conditional_analysis.py` reachability
   margin**: not a live defect (every verdict ever produced was reachable),
   but at ~60% of its own floor and closing as `TARGETS` grows — fixed
   before it could fail silently, the family's own "concentrated wherever a
   helper can degrade silently" prediction realized in its purest,
   pre-emptive form.
3. **.004 — the `degree_centrality`-never-binds suspicion**: labelled a
   suspicion, not a confirmed defect, per its own subtask's explicit
   discipline — the one finding in the family that stops short of a
   demonstrated divergence case.

### The predictions, scored honestly (as this file's own "Why this is worth
days" section promised before the sweep ran)

1. **"More construct-validity failures, concentrated wherever a helper can
   degrade silently rather than raise."** — Confirmed. Both genuinely new
   code-level findings (.001, .002) are exactly this shape: a helper
   returning a plausible value, or a gate remaining silently reachable
   only by a shrinking margin, instead of raising.
2. **"Essentially nothing in the statistical layer."** — Confirmed. .002
   found the permutation-floor/reachability layer clean on 8/13 criteria
   on first audit; .004 directly verified the stratified well-powered-max
   AUC's own null replicates its full shell-selection procedure (no
   look-elsewhere leak) and `effective_rank`'s Spearman construction is
   scale-free. No new statistical-layer defect anywhere in the family.
3. **"Little change to the register's conclusions... the blast radius on
   individual numbers is far smaller than it would be if the register had
   more than one positive."** — **This is the one prediction worth reading
   carefully, not just checking off.** Its own text explicitly named the
   risk this sweep then realized: *"A wrong construct can manufacture a
   spurious positive; it rarely conceals a real one. The register has
   *one* positive, so the blast radius on conclusions is far smaller than
   the blast radius on individual numbers."* .003 found exactly that:
   PTP1B's `dcc_low` positive — the register's one — did not survive its
   own seed correction (AUC 1.000→0.598, p 0.00275→0.567, no k survives).
   The register's honest positive count is now **zero**. This is not a
   failure of the prediction; it is the prediction's own explicitly-named
   worst case, and it is the one conclusion in the whole register this
   sweep actually changed. Every other headline (nine routes closed, no
   benchmark can certify the challenge's premise, no quantum advantage at
   any N ≤ 704) is unchanged, matching the prediction's other half exactly.

### Consequence, stated plainly

**The register now has zero surviving positives, not one — the single
material change to any conclusion this entire sweep produced.** Everything
else the family found (2 new code-level bugs, 1 new suspicion, and the
convention amendment) closes failure classes and hardens the pipeline
without moving a verdict. Per this family's own framing, restated because
it is the actual headline: **a register whose conclusions survive its own
corrections is in better shape than one that has never been corrected**,
and losing the one positive to the same rigor that found and fixed the
defect *is* that shape holding, not breaking.

### Feeds [[TASK-0184]]

Already landed, not a forward pointer: [[TASK-0217.003]]'s own advisories
updated `RESULTS.md` and rewrote `documentation/PHASE1_SUBMISSION_DRAFT.md`
§2.4 (one weak positive → zero surviving positives, framed as a second
self-auditing-strengthens-the-narrative instance). [[TASK-0217.001]]'s
KRAS_G12C/BCR_ABL1 pocket-label correction and [[TASK-0217.004]]'s
proximity-floor suspicion are additive advisories only, no submission text
changed for either — flagged here as available if a numbers-audit pass on
the submission draft wants them.

### Not attempted (family-wide)

- Re-scoring any observable beyond the one headline cell ([[TASK-0217.003]]'s
  PTP1B `dcc_low`) that a register-level conclusion actually rested on —
  the open question above states this precisely rather than assuming it
  away.
- A general-purpose static check for reachability defects ([[TASK-0217.002]]'s
  own flagged Open Question) — construction-specific reasoning was applied
  per instance instead.
- Redefining any flagged metric ([[TASK-0217.004]]) — advisories only.
- Extending any subtask's own targeted scope into a full register re-run —
  every subtask's own "not a re-run of ~190 tasks" boundary held throughout.
