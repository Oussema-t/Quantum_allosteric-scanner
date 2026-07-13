# TASK-0096 Delete or implement the phantom H11/H12 operators

## Context

- ID: TASK-0096
- Title: `H11_anisotropic_mechanical` and `H12_anm_scalarised` are
  undocumented duplicates of `H6`/the unweighted-contact Laplacian — either
  implement the anisotropy their docstrings claim, or delete both and
  remove them from the sweep and `ALGORITHM_REGISTER`.
- Status: Done
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

**Decision (per-operator, not both-implement/both-delete by default):
implement both.** User's explicit call: implement first, because a sweep
that proves the operators useless is itself a useful, documented result
("if the sweep proves the operators to be useless — we will document the
fact and remove/not use them"), whereas deleting first forecloses that
finding.

**Source check (TASK-0037's own "before implementing" instruction,
CLAUDE.md convention 2 — port from notebook, don't invent):**
`notebooks/H_new_engineering (4) CLEAN.ipynb`, cell 11,
`HamiltonianFactory` DOES contain real, distinct original formulas for
both — they were simply never ported:
- `H11_anisotropic_mechanical(alpha, cutoff)`: `W = T * exp(-alpha*D) *
  (1/(D**2 + 1e-2))` — an exponential-decay term multiplied by a harmonic
  (1/d²) term, i.e. a sharper/stiffer distance falloff than either H6 or
  H7 alone. Despite the name, this notebook formula has **no direction
  vector at all** — it is not actually anisotropic in the geometric sense.
  That name/formula mismatch predates this port; reproduced faithfully
  rather than invented around.
- `H12_anm_scalarized(cutoff)`: for each residue i, SVD the displacement
  vectors of its contact-graph neighbours to get the dominant local axis
  (first right-singular vector `Vt[0]`), then weight each edge `(i, j)`
  by `|unit(i→j) · axis_i|`. This one *is* genuinely (locally)
  anisotropic — two residues at the same distance from a shared neighbour
  get different coupling if their local neighbourhoods point in different
  directions. This is what the pre-fix docstring's "dot-product of unit
  displacement" was gesturing at, dotted against a second,
  independently-derived vector (the local axis) rather than against
  itself.

Both ported verbatim into `hamiltonians.py`'s existing
`(coords, cutoff=10.0, ...) -> (N, N)` function signatures, wrapped in the
repo's own `laplacian(W, normalised=False)` (matches this file's existing
house convention for H5–H10, which also diverge from the notebook's own
normalised-Laplacian choice — an already-established prior port decision,
not something new here).

**`H14_anm_pinv_trace` — added, not part of TASK-0096's original scope.**
While investigating, an earlier draft of this fix (before the notebook
check) had implemented a *global* ANM cross-correlation reduction —
`Trace([H13⁺]_ij)`, the trace of each 3×3 block of the Moore-Penrose
pseudo-inverse of the real anisotropic 3N×3N Hessian (`H13`), the standard
ANM covariance quantity (Bahar/Atilgan/Erman 1997, Atilgan et al. 2001).
That formula is not in the notebook (repo-original, not ported) and is
mechanically distinct from the local `H12`: it can assign nonzero
coupling between residues that are not direct contact-graph neighbours,
since the pseudo-inverse propagates through the whole elastic network,
where `H12`'s local SVD strictly cannot (`test_has_nonzero_long_range_coupling`).
Per explicit user instruction ("keep as a new hamiltonian... for research
purposes"), kept as a new `H14_anm_pinv_trace` operator rather than
discarded or used to replace `H12` — lets a future sweep against the
proximity floor (TASK-0094/REVIEW-2026-07-13 P1-A) judge the global vs.
local ANM formulation empirically rather than picking one now.

**Validation:**
- `np.allclose` divergence checks (H11 vs H6; H12 vs H2 and vs H6; H14 vs
  H2 and vs H6) on a 20–30-residue non-colinear synthetic helix — all
  `False`, confirmed via a scratch script before writing tests.
- `H12`'s locality/direction-dependence isolated with a hand-built 4-point
  fixture: neighbour 1 fixed at distance 3.0 Å along +x in both cases,
  residue 0's *other* two neighbours vary between a tight (±0.3 Å, mostly
  x-aligned local axis) and wide (±4.0 Å, mostly y-aligned local axis)
  spread — edge (0,1) weight goes from ≈ −1.0 to ≈ 0.0, proving the weight
  depends on neighbourhood shape, not distance alone (something no
  distance-only operator, and not the old constant-1.0 `H12`, could do).
- `H14`'s long-range property isolated the same way `H13`'s test does:
  confirmed nonzero `H14` weight exists between at least one non-adjacent
  pair on the helix fixture.
- Structural smoke tests (`test_hamiltonians.py::TestH1toH13Smoke`,
  `_LAPLACIAN_OPS["H11"]`/`["H12"]`): both remain symmetric PSD with
  nullity ≥ 1 on the connected 6-node fixture — unchanged from before this
  fix, confirming the new formulas didn't break the Laplacian-family
  invariants the rest of the sweep infrastructure assumes. `H14` gets the
  same three checks (new `TestH14AnmPinvTrace` class).
- Full suite: `477 passed, 1 xpassed` (`pytest tests/ -q
  --ignore=tests/test_viz.py --ignore=tests/test_seam_0006_pathways_viz.py`)
  — no regressions.

**Scope note — no runtime "sweep" wiring found to update.** Searched for
an `ALGORITHM_REGISTER`-style dict/enumeration that iterates H1–H13 by
name at runtime (`grep -rn "H11\|H12\|ALGORITHM_REGISTER"
src/ scripts/`): none exists. `scripts/run_challenge.py` only ever
constructs `H_new` and `H10` directly; `ALGORITHM_REGISTER.md` is a
capability-tracking document with no H11/H12 entries to correct. The only
places H11/H12 were referenced were `hamiltonians.py` itself and
`tests/test_hamiltonians.py` — both updated. If/when a real cross-operator
sweep harness against the proximity floor is built (a natural TASK-0094
follow-up), it should include `H11`, `H12`, and `H14` in that enumeration.

**Closes TASK-0037** (moved to DONE, cross-referencing this task — see
that file for its own record; not duplicated here).
