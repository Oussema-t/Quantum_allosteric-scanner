# TASK-0237 Collaborator's ported `hamiltonians.py` cell — H14 question answered (Done); other operators still blocked if ever revisited

## Context

- ID: TASK-0237
- Title: assess whether `.ai/reviews/2026-08-23 - hamiltonians/hamiltonians.py`
  (a Colab-notebook cell the collaborator provided) invalidates this
  project's own finding that CTQW does not deliver a floor-beating result
  across different proteins.
- Status: Done
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: Bartosz, 2026-08-23 — collaborator-provided file, asked whether it
  invalidates the CTQW-cross-protein-negative hypothesis. **Narrowed same
  day**: only `H14_anm_pinv` is of interest — does it help CTQW score
  better, checkable with this project's own existing methods.
- Priority: P1 — resolved same day as filed, no blocker in the end for the
  question actually asked.

## What was checked, and the answer to the question as asked

**The file as provided contains no result to check.** It is cell 13 of a
larger Colab notebook ("13 - Contact graph + Hamiltonian H_new") — pure
operator construction (`contact_matrix`, `laplacian`, `V_B/V_T/V_R/V_C/V_M`,
`build_H_new`, the H1-H12/H14 register, and a per-target sanity-check loop
that only asserts symmetry and prints a spectral gap). **No CTQW
propagation, no scoring, no AUC, no floor comparison anywhere in it.** The
file's own comments reference later notebook sections not included here
("sec 5/6" for `SITE_CUTOFF`/ligand proximity, "sec 14" for mixing time,
"sec 20" for "the benchmark") — the actual scoring, if it exists, lives in
cells this repo does not have. `ACTIVE` (the target list) and `EXTRACT`
(the per-target coordinate/B-factor data) are read but never defined in
this file either — both come from an earlier, also-missing cell (comment:
"set BY HAND IN CELL 1").

**Fidelity check against this repo's own `hamiltonians.py`/`potentials.py`,
done line-by-line, not assumed from the file's own "ported verbatim"
claim**: every function checked — `contact_matrix`, `laplacian`,
`normalised_laplacian_alpha`, `V_B`, `V_T`, `V_R`, `V_C`, `V_M`,
`build_H_new`, `H1`/`H2`/`H4`/`H6`/`H8`/`H9`/`H10`/`H11`/`H12`, and the
vectorised `H14` (einsum-based 3N×3N Hessian + pseudo-inverse trace) —
matches this repo's current source exactly in formula, defaults
(`ALPHA=0.3`, `LAMBDAS` B/T/R/C/M = 0.08/0.16/0.08/0.04/0.04,
`TERM_FRAC=0.05`, `N_LOW_MODES=10`, `H6`'s own 12.0 Å cutoff, `H8`'s own
7.5 Å cutoff), and the same documented caveats this repo's own code
carries (e.g. H11's "despite the name, not actually anisotropic" note,
reproduced verbatim in the collaborator's comment). One cosmetic
implementation difference, verified mathematically inert: the collaborator's
`V_*` functions return bare (N,) vectors summed then diagonalised once at
the end of `build_H_new`, where this repo's return (N,N) diagonal matrices
summed directly — identical by linearity of `diag()`, confirmed by hand,
not merely asserted. **No bug, no parameter drift, no formula divergence
found anywhere in what was provided.**

**Conclusion**: this file is faithful groundwork, not a competing result.
It cannot invalidate (or confirm) the cross-protein CTQW finding either
way, because it never reaches the propagation/scoring step that finding is
about.

## Intent Contract

- Outcome: either (a) the collaborator's remaining notebook cells (setup +
  the actual scoring/benchmark cells referenced as "sec 14"/"sec 20") are
  obtained, adapted to pure Python, and run against this project's own
  real targets and established floor/chance baselines — a genuine new data
  point on the cross-protein CTQW question — or (b) if no more of the
  notebook exists/can be obtained, that is recorded as the answer (nothing
  to validate) and this task closes without a re-run.
- Why required, not assumed: the operator layer is already verified
  identical to this repo's own code (done above) — re-porting it again
  would duplicate work for no new information. The only thing that could
  actually bear on the cross-protein hypothesis is code this task does not
  yet have.
- In Scope (once/if more notebook content arrives):
  - Adapt the setup cell (cell 1: `NET_CUTOFF`, `SITE_CUTOFF`, `ACTIVE`,
    `EXTRACT`) and whichever scoring cell(s) produce AUC/floor/diagnosis
    into a standalone pure-Python script under `__WORK_IN_PROGRESS__/
    scripts/`, reusing this repo's own `propagators.
    time_averaged_ctqw_converged`/`diagnostics.classify_failure`/
    `baselines.*` floor functions wherever the collaborator's own scoring
    step turns out to reimplement the same thing (check first, don't
    assume — port only what's genuinely new).
  - Run against this project's own real, RCSB-fetched target set (not
    bundled/synthetic structures) — matching this project's own standing
    convention (`.ai/reference/PAPER_CITATION_PROTOCOL.md`'s own PDB-retest
    rule, same discipline applied here to a collaborator drop as to the
    2026-08-21 reference-register drop).
  - Compare against this repo's own already-established floor/chance
    baselines for whichever targets overlap ([[TASK-0094]]'s proximity
    floor, [[TASK-0159]]'s converged-limit propagator) — a same-target
    same-method comparison is what would actually bear on the hypothesis,
    not a differently-scored number on a different target set.
  - State plainly whether the collaborator's own target set (`ACTIVE`,
    once known) is a subset of, overlaps, or is disjoint from this
    project's own 13-target register — the question as raised ("different
    proteins") may specifically mean the collaborator tested proteins
    outside this project's own set, which changes what a positive result
    there would and wouldn't imply about this project's own findings.
- Out Of Scope:
  - Re-verifying the operator-construction fidelity — already done in this
    task's own filing, above.
  - Building new observables or Hamiltonians beyond what the collaborator's
    own notebook cells contain.
- Constraints And Invariants: apply this project's own full verification
  discipline to anything the collaborator's later cells claim as a
  result — floor comparison (not chance alone), a stated seed/active-site
  convention, converged (not truncated) propagation, and this project's
  own diagnosis taxonomy (`classify_failure`) — a collaborator-provided
  positive that skips any of these is exactly as unverified as an
  internally-produced one would be under the same gap.
- Planned Validation: if a positive (floor-beating) result emerges on any
  real target, cross-check it against this project's own independently-
  computed floor/chance baseline for that same target before reporting it
  as a finding — the same discipline TASK-0159/TASK-0217.001 already
  applied to this project's own numbers.

## Dependency

- **Blocking, not yet resolved**: does the collaborator's notebook have
  more cells than this one? Specifically cell 1 (`ACTIVE`/`EXTRACT`/
  `NET_CUTOFF`/`SITE_CUTOFF` setup) and whichever cell(s) implement "sec
  14"/"sec 20" (mixing time, the actual benchmark). Without these, there
  is nothing further this task can do — it is not an implementer-level
  question, it needs the collaborator or Bartosz.
- [[TASK-0094]] (proximity floor), [[TASK-0159]] (converged propagator) —
  the baselines any new result must be checked against.

## Open Questions

- Is `ACTIVE` (the collaborator's own target set) this project's own 13
  targets, the reference-register's bundled non-target structures (the
  same caveat [[TASK-0229]]'s own drop required), or a genuinely new,
  independent protein set? Unknowable from this file alone.
- Is "sec 20" ("the benchmark") floor-comparison scoring in the same sense
  this project uses the term, or a different metric (e.g. raw AUC against
  chance only, no proximity floor)? If the latter, a positive result there
  would not actually contradict this project's own floor-specific finding.

## Done

**2026-08-23, Architect.** Scope narrowed the same day the task was filed:
Bartosz clarified only `H14_anm_pinv` (the collaborator's port) is of
interest, and asked whether this project's own existing methods can check
whether it helps CTQW score better — no need to wait on the collaborator's
missing notebook cells for this specific question, since the collaborator's
`H14_anm_pinv` is, per this task's own fidelity check above, formula-for-
formula identical to this repo's own `H14_anm_pinv_trace`
(`hamiltonians.py`). That means this repo's own history already answers the
question directly, with more rigor than a fresh port would add.

**Answer: no. H14 does not help CTQW score better on any of the 3 mandatory
targets.** Already established in [[TASK-0138]] (2026-07-19), which ran
exactly this project's own full validation stack against H14 — ceiling
search under [[TASK-0130]]'s converged (not truncated) propagator, a
permutation null matching [[TASK-0131]]'s own methodology, and a trial-
density convergence check — the same scrutiny this project applies to its
own `H_new` operator, not a lighter-touch standard for a favorable-looking
candidate:

| Target | H14 ceiling − floor margin | vs. `H_new`'s own ceiling | Permutation-null result |
|---|---|---|---|
| CARDIAC_MYOSIN | **−0.0218** (negative) | `H_new` wins by 0.059 | 0th percentile (n=30) — worse than every null replicate; no positive margin to test |
| KRAS_G12C | +0.091 (0.573, ~0.595 once trial-density-converged) | `H_new`'s 0.629 still higher | 70th percentile (n=200), p=0.30 uncorrected |
| BCR_ABL1 | +0.136, and H14's ceiling *does* exceed `H_new`'s here (0.717 vs 0.667, +0.050) | — | **79th percentile (n=200), p=0.21 uncorrected** — not significant even before any multi-target correction |

This is a *ceiling* result — the best score reachable with the answer key
in hand, the single most favorable test this project's own methodology
offers an operator. Since even the ceiling fails to clear the floor with
statistical support on 2 of 3 targets (and doesn't clear it at all on the
third), the blind/frozen-config actual score — what CTQW would report in a
real run — would be equal or worse. **H14 does not rescue CTQW's
cross-protein performance on any target this project has tested it on.**

**Consequence for this task's original (broader) question**: unaffected
for H14 specifically — resolved without needing any of the collaborator's
missing cells. The broader question (does the *rest* of the collaborator's
notebook, e.g. whatever "sec 20" scores, contain a genuine new result for
some *other* operator) remains exactly as blocked as originally filed —
not reopened here, since Bartosz's own narrowing makes that moot unless
raised again separately.

No new files. Full detail: `.ai/tasks/DONE/TASK-0138-h14-ceiling-validity-characterization.md`.
