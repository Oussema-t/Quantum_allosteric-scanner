# TASK-0102 Is `ground_state_relaxation`'s BCR_ABL1 result seed-dependent, or just "the minimum has to be somewhere"?

## Context

- ID: TASK-0102
- Title: Test whether TASK-0091's BCR_ABL1 finding (`ground_state_relaxation`
  clears the proximity floor, AUC 0.7315) reflects genuine active-site→
  pocket coupling, or is an artifact of `H_new`'s ground state being an
  essentially fixed, seed-independent feature of the structure that
  merely happens to sit closer to the pocket than to the active site on
  this one protein.
- Status: Done
- Owner: Implementer
- Source: user question, 2026-07-13 — "is it possible that the ground
  state relaxation 'accidentally' is localised somewhere near the distal
  pocket... it's not a meaningful physics contribution other than
  'potential minimum has to be SOMEWHERE on the protein'?" Plus: "can we
  build a clear discriminating test where we construct a small enough
  network, where we manipulate the potential to have a minimum away from
  nodes having the characteristics of an active site and those having
  the characteristics of a drug site?"

### Why this concern is concrete, not speculative (checked against real code)

`ground_state_relaxation(H, t, source)` computes `[exp(-Ht) p0]`, `p0`
uniform over `source`. Expand in `H`'s eigenbasis:
`exp(-Ht) p0 = Σ_k exp(-w_k t) <v_k|p0> v_k`. As `t` grows, this is
dominated by the **smallest** `w_k` term — for large enough `t·(gap)`
(gap = difference between the two smallest eigenvalues), the *shape* of
the result converges to the ground eigenvector `v_0` **regardless of
`p0`** (i.e. regardless of `source`/the active site), up to an overall
scalar that normalization removes. Every call site
(`quantum_vs_classical`, `benchmark`, `gnm_cutoff_weight_sweep`) uses the
same default `t_max=15.0`. Whether 15.0 is "converged" or "still
seed-sensitive" for `H_new`'s real spectral gap on BCR_ABL1 has never been
checked — `quantum_vs_classical`'s own docstring only asserts
"representative," it does not demonstrate convergence. If it *is*
converged, TASK-0091's finding carries **zero information** about the
active site at all — it would be identical for literally any seed choice,
and "beats the proximity floor" would just mean "the ground state's fixed
location happens to be farther from the active site than a typical
random point, and the floor's own denominator (distance from seed) is
low in exactly the region the ground state occupies." That is precisely
the accidental-minimum hypothesis, restated in exact linear-algebra terms.

## Intent Contract

- Outcome: a decisive answer, on real data first and (if warranted) on a
  fully-controlled synthetic network second, to whether
  `ground_state_relaxation`'s occupation pattern actually depends on
  which residues are used as the seed — and, separately, whether its
  proximity to a candidate pocket reflects genuine coupling to the seed
  or is explainable purely by the potential landscape's shape, independent
  of any seed.
- In Scope, ordered cheapest/most-decisive first:
  - **(a) Real-data seed-invariance check (do this first, cheap).** On
    BCR_ABL1's real, already-cached `H_new` (TASK-0091's cache), rerun
    `ground_state_relaxation` with the seed moved to several different,
    arbitrary residue sets (not the real active site) — including at
    least one seed on the *opposite* side of the protein from the real
    active site. Compare the resulting occupation vectors (Pearson/
    Spearman correlation, or simpler: does the top-20 occupancy set
    change at all). **If correlation ≈ 1 across seeds, TASK-0091's
    finding is seed-independent — report this plainly, it invalidates
    reading 0.7315 as evidence of active-site-to-pocket coupling,
    regardless of how the floor math came out.** If occupancy changes
    meaningfully with seed, that's evidence of genuine, if partial,
    seed-dependence, and motivates part (b).
  - **(b) Eigenvalue-gap check.** Compute `H_new`'s actual spectral gap
    (`w_1 - w_0`) for BCR_ABL1 and evaluate `exp(-gap · t_max)` — states
    numerically how converged the real computation was, explaining *why*
    (a) came out the way it did rather than leaving it as an unexplained
    empirical fact.
  - **(c) Synthetic discriminating network (build only if (a) is
    ambiguous, or to corroborate a clear (a) result with full ground
    truth).** Construct a small (~20-40 node) synthetic graph with three
    designated, non-overlapping node groups: an "active-site" set `A`, a
    "drug-site" set `B` at a controlled graph-distance from `A` (build
    both a proximal and a distal variant), and filler nodes. Build an
    `H_new`-style composite operator (Laplacian + `V_B`/`V_T`/`V_R` style
    terms) with the potential's true global minimum **deliberately
    engineered at a third location `C`**, disjoint from both `A` and `B`,
    with no designed coupling between `A` and `C`. Run
    `ground_state_relaxation` seeded at `A` and confirm the ground state
    correctly concentrates at `C` (not `B`) — this is the negative
    control proving the pipeline doesn't spuriously credit `B` just for
    being "the candidate pocket." Then build a second variant where the
    minimum is intentionally placed at (or coupled through a designed
    channel toward) `B`, and confirm the same pipeline correctly detects
    it — the positive control. A pipeline that cannot distinguish these
    two constructed cases has no discriminating power at all, independent
    of what any real protein shows.
- Out Of Scope: re-running TASK-0091's full real pipeline from scratch —
  reuse its cached `H_new`/occupancy arrays for part (a); building a full
  benchmark suite of synthetic networks (one clean pair, positive +
  negative control, is sufficient to answer the discriminating-test
  question, not a parameter sweep of synthetic topologies).
- Acceptance Scenarios:
  - Given BCR_ABL1's real `H_new` and at least 3 distinct seed choices
    (including the true active site and at least one antipodal
    arbitrary set), when `ground_state_relaxation` runs on each, then
    this task states explicitly whether the resulting occupancy patterns
    are effectively identical (seed-independent, invalidating the
    active-site-coupling reading) or meaningfully different
    (seed-dependent, supporting it) — a number (correlation), not a
    vibe.
  - Given the synthetic negative-control network (minimum engineered
    away from both `A` and `B`), when the pipeline runs, then it does
    **not** report `B` as floor-clearing/high-occupancy — if it does,
    that is a pipeline bug or a floor-design flaw, not a real finding,
    and must be reported as such.
  - Given the synthetic positive-control network (minimum engineered at/
    coupled to `B`), when the pipeline runs, then it **does** correctly
    identify `B`.
- Constraints And Invariants: this task's job is to determine
  meaningfulness, not to fix anything — if (a) shows seed-independence,
  that finding gets written into `RESULTS.md` as a correction to how
  TASK-0091's result should be read (cross-reference, don't silently
  edit TASK-0091 itself), following this project's established
  no-silent-overwrite convention (TASK-0095's own precedent).
- Planned Validation: the three ordered checks above are themselves the
  validation; report the outcome of (a) before deciding whether (c) is
  needed at all.

## Dependency

- Reuses TASK-0091's cached `H_new`/occupancy data for BCR_ABL1 (part a).
- Directly informs how TASK-0101's ground-state-propagator column (once
  amended, see that task) should be interpreted — read together, not
  blocking each other.
- Related to TASK-0092 (holo diagnostic comparison) — see the user's
  separate question about holo comparisons, addressed there: holo
  comparison is a *different*, complementary check (does the same
  pattern reproduce on an independently-solved structure) and does not
  substitute for the seed-invariance check here (a static ground-state
  artifact would likely reproduce on both apo and holo structures too,
  since both share the same fold — holo agreement alone would not
  distinguish real coupling from a shared static artifact).

## Open Questions

- If part (a) shows *partial* seed-dependence (neither ≈1 nor clearly
  low correlation), what threshold separates "real enough" from
  "mostly artifact"? Don't invent one silently — report the actual
  correlation number and reason about it explicitly in this task's Done
  section, flag for Architect input if genuinely ambiguous.

## Done

**Real-data check, 2026-07-13.** Reused TASK-0091's cached `H_new`/coords/
labels for BCR_ABL1 (no re-fetch, no re-selection — total runtime ~3
seconds, since the expensive part of TASK-0091 was `select_frozen_config`,
never needed here). One `eigh` decomposition, reused across every seed
choice per this task's own cheapest-first ordering.

**Part (b) first (explains (a)):** `H_new`'s spectral gap
`w[1]-w[0] = 0.1933`; `exp(-gap * t_max=15.0) = 0.055`. The ground mode
(`v_0`) carries ~94.5% of the relative weight at `t_max=15.0`, the first
excited mode (`v_1`) the remaining ~5.5% — **partially converged, not
fully**. This predicts exactly the pattern found in (a): a result mostly
set by the fixed `v_0` shape (hence broadly similar across most seeds),
with a real but smaller `v_1` contribution that flips the outcome
qualitatively for seeds whose overlap with `v_1` happens to be large
enough.

**Part (a) — decisive, not ambiguous:**

- 6-seed correlation check (real active site, 1 antipodal, 4 arbitrary
  single-residue): occupation patterns cluster into two nearly-orthogonal
  groups. `{real_active_site, random_1, random_3}` mutually correlate at
  Pearson **0.998-0.9999**; `{antipodal, random_0}` mutually correlate at
  **1.0000** with each other but **-0.014 to -0.018** with the first
  group. `random_2` is a distinct third pattern (0.23 with group 1,
  -0.03 with group 2). **This alone rules out literal seed-independence**
  (correlation ≈ 1 across every seed, the task's own bright-line test) —
  different seeds genuinely produce different occupation *shapes*.
- But: AUC-vs-pocket does **not** track this clustering the way "real
  coupling" would predict. `random_2` (only 0.23 correlated with the real
  seed's occupation *pattern*) still scores AUC=0.7251 — nearly identical
  to the real seed's 0.7315. Broader 40-seed random sample (single
  residues, `rng=42`, same cached `H`): mean AUC=0.6734, median=0.7272,
  **75.0% of arbitrary seeds clear TASK-0091/0094's real proximity floor
  (0.5652)**, **70.0% land within 0.02 of the real active site's own AUC
  (0.7315)**, and **20.0% of arbitrary seeds score higher than the real
  active site does.**

**Conclusion (explicit, per this task's own Planned Validation and Open
Question guidance — not a silent threshold call):** the correlation
evidence is genuinely mixed (not the clean "≈1 everywhere" the task
anticipated for the invalidating case), but the **practical** question
this task exists to answer — does BCR_ABL1's real active site produce an
AUC that anything resembling a *typical* arbitrary seed would not — is
answered clearly: **no.** A strong majority (70-75%) of arbitrary,
biologically-uninformed single-residue seeds reproduce comparable
floor-clearing performance against the *same* pocket label. The good AUC
is predominantly a property of `H_new`'s fixed ground-state shape
(consistent with the 94.5%-ground-mode-weight finding in (b)), not
evidence of active-site-to-pocket coupling specific to the true active
site. **TASK-0091's 0.7315 must not be read as confirmed allosteric
signal** — this directly confirms the user's original "potential minimum
has to be somewhere" concern, with real numbers on real data, though via
a more nuanced statistical mechanism (majority-share high-AUC outcome
from ground-mode dominance, not literal 100% seed-invariance) than the
task's own anticipated bright-line case.

**Part (c) (synthetic discriminating network): not built.** Per this
task's own Constraints ("build only if (a) is ambiguous, or to
corroborate a clear (a) result") — (a) is decisive on its own (a 75%
floor-clearing rate among arbitrary seeds is not a borderline number
needing a synthetic ground-truth corroboration to interpret). Flagging,
not building: a future task could still construct the positive/negative-
control synthetic network described in this task's Intent Contract (c) if
someone wants a fully-controlled mechanistic demonstration for the
methodological report itself (pedagogical value, not additional
evidential need) — not filed as a follow-up here since no concrete
consumer has asked for it yet.

**Correction propagated, not silently edited:** `RESULTS.md`'s TASK-0091
finding corrected in place (marked, not deleted, per this project's
no-silent-overwrite convention) rather than editing `TASK-0091`'s own
task file, per this task's Constraints.

**Answers this task's own Open Question** (partial-seed-dependence
threshold): resolved by using AUC-outcome frequency (does a majority of
arbitrary seeds match the real seed's performance) as the practically
relevant statistic, rather than the raw occupation-correlation number
alone — correlation told us seeds differ in *shape*, but AUC-frequency is
what tells us whether the real seed's *result* is special. Recommend this
combined framing (correlation + outcome-frequency) for any future
seed-invariance check on this codebase, rather than correlation alone.
