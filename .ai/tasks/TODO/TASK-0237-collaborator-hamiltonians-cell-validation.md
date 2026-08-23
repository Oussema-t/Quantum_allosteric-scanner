# TASK-0237 Collaborator's ported `hamiltonians.py` cell — verify fidelity (done), get and run the actual scoring cells (blocked)

## Context

- ID: TASK-0237
- Title: assess whether `.ai/reviews/2026-08-23 - hamiltonians/hamiltonians.py`
  (a Colab-notebook cell the collaborator provided) invalidates this
  project's own finding that CTQW does not deliver a floor-beating result
  across different proteins.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: Bartosz, 2026-08-23 — collaborator-provided file, asked whether it
  invalidates the CTQW-cross-protein-negative hypothesis.
- Priority: **P1, but currently blocked on missing input — see Dependency.**
  Not urgent-and-actionable today; urgent to resolve *what's missing* so it
  doesn't sit unactioned.

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

—
