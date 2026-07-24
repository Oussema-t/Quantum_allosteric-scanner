# TASK-0149 Low-mode PRS/DCC predictor (`prs_low`/`dcc_low`) — port, real-target run, distance-stratified evaluation

## Context

- ID: TASK-0149
- Title: port and score two proximity-orthogonal-by-construction
  observables — low-mode Perturbation Response Scanning (`prs_low`,
  Atilgan 2009 / Ikeguchi 2005 LRT, restricted to the `k` lowest ANM
  modes) and low-mode GNM dynamic cross-correlation (`dcc_low`) — against
  the proximity floor and, critically, [[TASK-0123]]'s distance-
  stratified AUC.
- Status: DONE
- Owner: Implementer
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-23 20:08
- Source: real, executed work delivered 2026-07-22 (relayed via
  `.ai/reviews/2026-07-22/`) — `lowmode_predictor.py`,
  `test_lowmode_predictor.py`, `lowmode_predictor_synthetic_control.py`.
  Built against this project's real APIs (`superpose.anm_modes`,
  `potentials._kirchhoff_eigh`), **executed only on synthetic controls**
  — the delivering thread was honest that RCSB was unreachable from its
  own sandbox and explicitly declined to fabricate real-target numbers
  ("Fabricating real-target numbers is exactly what you'd (rightly) run
  cross-model validation to catch, so I won't"). Real-target execution
  is this task's own job.
- Priority: **P1.** Cross-reference, do not conflate, with [[TASK-0122]]
  (`mode_coparticipation`/`CP_low`) — a related but mathematically
  distinct construction (mode-participation-product, not a truncated
  ANM pseudo-inverse response or truncated GNM covariance) that mostly
  failed to decorrelate from distance on real `H_new`. This is a
  genuinely different method, not a re-run of that one, and its own
  synthetic result decorrelates far more cleanly than `CP_low`'s did —
  worth checking on real data for that reason specifically.

## What was already found, on synthetic data only — read before running

On a constructed two-domain hinge protein (seed at the far end of one
domain, a planted allosteric pocket at the far end of the other, coupled
only through the lowest bending mode):

| observable | whole-graph AUC | ρ(score, −hop) | distance-stratified AUC |
|---|---|---|---|
| CTQW-occ (confounded) | 0.213 | +0.713 | 0.375 |
| proximity floor (−hop) | 0.092 | +1.000 | 0.207 |
| `prs_low` (k=20) | 0.493 | **+0.160** | 0.588 |
| `prs_low` (k=5) | 0.517 | **+0.076** | 0.596 |
| `dcc_low` (k=20) | 0.261 | +0.559 | 0.290 |

**The clean, honest finding — not the hoped-for one**: mode-filtering
does exactly what the learnability gate ([[TASK-0120]]/[[TASK-0133]])
predicted it should — it removes the proximity confound (`ρ` collapses
from +0.71 to +0.08 for `prs_low`). **It does not thereby manufacture
whole-graph discrimination** (AUC sits at chance, ~0.50) — the low-mode
response is high both near the seed *and* at the genuinely-coupled
distal end, so a whole-graph ranking doesn't separate them. A modest
signal (~0.59 vs 0.5) appears only under the distance-stratified lens.
`dcc_low` is markedly worse than `prs_low` on the same synthetic case.

**Two honest caveats already flagged by the delivering thread, not
resolved**: (1) the synthetic "uncoupled distal" control still moves in
the global hinge mode (a clean two-domain system couldn't cleanly plant
an uncoupled-but-distant region), so the 0.59 stratified number is
plausibly optimistic; (2) this predicts, for the real run, that
whole-graph AUC will sit at chance and **the only place any signal can
show up at all is the stratified lens** — if it's absent there too, per
the delivering thread's own words, "the low-mode route is genuinely
dead and you can say so with a mechanism."

## Intent Contract

- Outcome: port `lowmode_predictor.py` → `src/allostery/`,
  `test_lowmode_predictor.py` → `tests/`,
  `lowmode_predictor_synthetic_control.py` → `scripts/` (per this
  project's own port-don't-cross-import convention). Confirm the 3
  delivered tests still pass as-is (they already ran clean per the
  delivering thread's own account — re-verify, don't re-trust). Then run
  `prs_low`/`dcc_low` on all 3 mandatory targets:
  1. Whole-graph AUC vs. [[TASK-0094]]'s proximity floor.
  2. **[[TASK-0123]]'s distance-stratified AUC with its own permutation
     null** — per this task's own synthetic prediction, this is the only
     place a real signal could show up; do not report a whole-graph null
     result as the final answer without also checking here.
  3. Report using the project's **correct, current seed convention** —
     full active-site array, incoherent mixture ([[TASK-0118]]/
     `INV-0006`), not the delivered code's own scalar-seed default used
     for its synthetic runs (the delivering thread flagged this exact
     divergence risk explicitly).
  4. Sweep `k_modes` in `{5, 10, 15, 20}` (the delivered code defaults to
     20 to match `CO(20)`; the delivering thread's own synthetic result
     found `k=5` slightly *better* than `k=20`) — report per-`k`
     sensitivity, don't silently pick one.
- In Scope: real-target execution and evaluation only — the
  implementation itself is delivered and should not be rebuilt from
  scratch; if a real bug is found while running it, fix it and say so,
  don't rewrite the method's own formula without cause.
- Out Of Scope: rewriting `prs_low`'s O(N·k²) inner-loop computation for
  performance unless it's actually intractable at CARDIAC_MYOSIN's
  scale (N=704) — a real, separate concern if it comes up, not
  pre-emptively addressed here.
- Constraints And Invariants: gate through [[TASK-0123]]'s stratified
  AUC and its own permutation null before reading *any* number as
  signal, per the delivering thread's own explicit instruction.
- Planned Validation: the synthetic tests already delivered, re-verified
  as passing, plus the real-target stratified-AUC result, reported
  whichever way it comes out — including the "genuinely dead, with a
  mechanism" outcome the delivering thread itself predicted as likely.

## In Progress

None

## TODO

- [x] Port the three delivered files into their real homes; re-verify
      the 3 existing tests pass unmodified.
- [x] Re-run on real targets under this project's actual seed convention
      (full active-site array, `coherent=False`), not the delivered
      code's scalar default.
- [x] Score whole-graph AUC vs. the proximity floor, all 3 targets.
- [x] Score via TASK-0123's distance-stratified AUC + permutation null —
      the one place signal is predicted to be visible, if anywhere.
- [x] Sweep `k_modes` in {5, 10, 15, 20}; report sensitivity.
- [x] Report the result, including a "genuinely dead, with a mechanism"
      verdict if that's what real data shows.

## Dependency

- [[TASK-0094]] (Done) — proximity floor.
- [[TASK-0123]] (Done) — stratified AUC + permutation-null methodology,
  reused directly, not re-derived.
- [[TASK-0118]] (Done) — the seed convention this task must use.
- Cross-referenced, not duplicated: [[TASK-0122]] (`CP_low`, a related
  but distinct construction, already Done with mostly-negative results).

## Open Questions

- None — scope, method, and evaluation lens are all fully specified by
  the delivered code and its own stated predictions.

## Done

**2026-07-24, Implementer B.** Executed as scoped: ported unmodified, re-ran on real
targets under the project's actual seed convention, gated through TASK-0123's
stratified AUC + permutation null, swept `k_modes`.

**Port**: `lowmode_predictor.py` -> `src/allostery/`, `test_lowmode_predictor.py` ->
`tests/`, `lowmode_predictor_synthetic_control.py` -> `scripts/`, byte-identical to the
delivered versions. The 3 delivered tests re-verified passing (3/3), not re-trusted
from the delivering thread's own account.

**New `scripts/lowmode_predictor_real_run.py`**, reusing TASK-0123's own
`_prepare_target`/`stratified_auc`/well-powered-shell-filter/permutation-null
machinery directly rather than re-deriving an evaluation pipeline (per this task's
own Constraint). A real bug was found and fixed in this new script itself (not in the
ported `lowmode_predictor.py`, which is unaffected): the first version's `rho`
computation used the wrong sign relative to the delivered convention (`spearmanr(score,
-hop)`) -- `_prepare_target`'s `shells` is the real, non-negative hop distance, and the
script initially correlated against `shells` directly instead of `-shells`. Caught by
checking a raw per-shell score trend against the printed sign before trusting any
number, not assumed correct because the script ran without error; fixed, re-run, and
every number in `RESULTS.md`/this section uses the corrected sign.

**Real-target result (k=20 primary, full `k∈{5,10,15,20}` sweep as sensitivity)**:

| Target | Observable | Whole-graph AUC | Floor | ρ(score,−hop) | Stratified well-powered max AUC | p (uncorrected) |
|---|---|---|---|---|---|---|
| KRAS_G12C | `prs_low` | 0.481 | 0.482 | −0.18 | 0.595 | 0.672 |
| KRAS_G12C | `dcc_low` | 0.522 | 0.482 | +0.52 | 0.506 | 0.878 |
| BCR_ABL1 | `prs_low` | 0.188 | 0.582 | −0.26 | 0.439 | 0.918 |
| BCR_ABL1 | `dcc_low` | 0.378 | 0.582 | +0.50 | 0.518 | 0.803 |
| CARDIAC_MYOSIN | `prs_low` | **0.836** | 0.568 | −0.40 | **0.922** | **0.006** |
| CARDIAC_MYOSIN | `dcc_low` | **0.711** | 0.568 | +0.48 | **0.962** | **<0.001** |

**KRAS_G12C/BCR_ABL1: genuinely dead** -- no cell at any `k` reaches significance
(p=0.67-0.99 across the full 16-cell sub-grid), matching the delivering thread's own
predicted possible outcome verbatim.

**CARDIAC_MYOSIN: real, stratification-surviving signal at every `k`** (`prs_low`
p=0.003-0.006; `dcc_low` p<0.001-0.007), surviving the primary 6-comparison Bonferroni
bar (alpha=0.05/6=0.0083) for both observables at k=20; only 2/8 CARDIAC_MYOSIN cells
survive the maximally conservative 24-comparison full-grid Bonferroni
(alpha=0.05/24=0.0021) -- both readings reported, neither cherry-picked. Confirmed via
direct per-shell inspection (not just the summary statistic): the 2 well-powered
shells (n_pos>=3) both score high for both observables (0.79-0.96), 2 independent
shells, not a single-shell artifact.

**Real, honestly-reported divergence from the synthetic control's own prediction**:
ρ(score,−hop) stays substantial on every real target (`prs_low` −0.18 to −0.51;
`dcc_low` +0.44 to +0.63), far from the synthetic control's own ~0.08-0.16 "cleanly
decorrelated" result. `dcc_low` reproduces the classic proximity-confound sign/
magnitude on real data (matching, not contradicting, the synthetic control's own
"markedly worse than `prs_low`" finding). `prs_low` decorrelates in the *opposite*
(anti-proximity, distal-favoring) direction instead of toward zero -- meaning
CARDIAC_MYOSIN's own whole-graph AUC number is not, on its own, trustworthy proof of a
non-proximity signal (the true pocket happens to sit distally, which a systematic
distal bias could exploit on its own) -- exactly why the stratified, permutation-
null-gated result is reported as the actual finding, not the whole-graph number.

**`k_modes` sensitivity: no sign or verdict flip across `{5,10,15,20}` on any target.**

**Cross-reference, not conflation** (this task's own Priority note): [[TASK-0122]]'s
`mode_coparticipation`/`CP_low` mostly failed to decorrelate from distance on real
`H_new`. This task's own real-data rho values show the same qualitative split hinted
at by the synthetic comparison -- `prs_low` decorrelates (and over-corrects into
anti-proximity) far more than `CP_low` did, `dcc_low` does not decorrelate at all --
a genuinely different method independently checked, not a re-run of TASK-0122's own
result.

**No bug found in the delivered `lowmode_predictor.py` itself.** `prs_low`'s O(N*k)
Python double loop timed at <=1.7s even on CARDIAC_MYOSIN (N=704, 18 seed residues) --
not intractable, so the Out Of Scope note against rewriting it for performance was
never triggered.

**Full test suite**: 901 passed, 2 xfailed, 0 failed.

Full detail: `RESULTS.md`'s "Low-mode PRS/DCC real-target run" section, open-questions
row 30, `results_task0149_lowmode_predictor/lowmode_predictor_real_run.json`.
