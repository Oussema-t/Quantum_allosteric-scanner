# TASK-0096 Delete or implement the phantom H11/H12 operators

## Context

- ID: TASK-0096
- Title: `H11_anisotropic_mechanical` and `H12_anm_scalarised` are
  undocumented duplicates of `H6`/the unweighted-contact Laplacian — either
  implement the anisotropy their docstrings claim, or delete both and
  remove them from the sweep and `ALGORITHM_REGISTER`.
- Status: TODO
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/REVIEW-2026-07-13-proximity-confound-and-propagator-semantics.md`,
  finding **P2-A**. Verified with `np.allclose` on real code, cutoff 8.0 Å:
  - `H11_anisotropic_mechanical` (`hamiltonians.py:161-166`) is body-identical
    to `H6_exponential_decay` (`np.allclose` → `True`). Its docstring claims
    "weight edges by dot-product of unit displacement" — it does not do this.
  - `H12_anm_scalarised` computes `k_ij = np.dot(r, r)` where `r` is a
    **unit** vector — the code's own comment reads `# = 1.0 for unit
    vector` (`hamiltonians.py:180`). Every edge weight is therefore 1.0,
    making it identical to the unweighted-contact Laplacian (`np.allclose`
    → `True`). There is no anisotropy in it.
- Relationship to TASK-0037: that task already records these as "not
  implemented," but per the review, that finding is **not sufficient**
  while both operators are still live in the sweep and the register —
  a judge or reviewer who reads the docstrings and then the bodies will
  find a claimed-but-absent capability. This task closes TASK-0037 for
  real (fix or removal), rather than leaving it as a known-but-unactioned
  gap.

## Intent Contract

- Outcome: for each of `H11_anisotropic_mechanical` and
  `H12_anm_scalarised`, either (a) implement the anisotropic
  displacement-dot-product weighting the docstring actually claims, with
  a test proving it now diverges numerically from `H6`/the unweighted
  Laplacian on a non-trivial case, or (b) delete the function entirely
  and remove every reference to it from the operator sweep and
  `ALGORITHM_REGISTER`.
- In Scope: `hamiltonians.py` (the two functions), the sweep enumeration
  wherever it lives (check `analysis.py`/wherever `ALGORITHM_REGISTER` is
  defined), any test that currently exercises these two names.
- Out Of Scope: the other operators in the register (H1-H10, H13,
  `build_H_new`/`build_H10`) — this task is scoped exactly to the two
  named phantoms the review verified.
- Acceptance Scenarios:
  - Given the decision (implement or delete) is made per operator, when
    the sweep runs, then it either contains a genuinely-distinct H11/H12
    (numerically different from H6/unweighted-Laplacian on a real test
    case) or does not contain them at all — never a same-output entry
    masquerading as distinct.
  - Given `ALGORITHM_REGISTER` (or wherever operator capabilities are
    documented for the submission), then it accurately reflects whichever
    decision was made — no claimed-but-absent capability remains.
- Constraints And Invariants: this decision should be made per-operator,
  not both-implement or both-delete by default — check whether either
  anisotropic weighting is actually useful for the submission's story
  before spending effort implementing physics nobody asked for; deletion
  is the cheaper, always-valid default per the review's phrasing ("either
  implement... or delete both").
- Planned Validation: `np.allclose` check proving post-fix divergence (if
  implemented) or a grep confirming zero remaining references (if
  deleted); re-run of any test suite touching the operator sweep.

## Dependency

- Closes out TASK-0037 (already-recorded "not implemented" finding) —
  cross-reference, don't duplicate that task's record.
- Independent of TASK-0094/0095 — can be done in parallel per the
  review's own sequencing note.

## Open Questions

- Implement or delete, per operator — the review explicitly leaves this
  choice open ("either... or"); this task should make and record the
  decision rather than defaulting silently.

## Done

(not yet)
