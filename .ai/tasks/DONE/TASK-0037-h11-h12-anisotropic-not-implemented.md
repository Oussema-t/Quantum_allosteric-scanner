# TASK-0037 `H11`/`H12` don't implement the anisotropic physics their docstrings claim

## Context

- ID: TASK-0037
- Title: `H11_anisotropic_mechanical` is a byte-for-byte duplicate of
  `H6_exponential_decay`; `H12_anm_scalarised`'s `k_ij` is always exactly
  `1.0` regardless of geometry, making it a duplicate of
  `H2_combinatorial_laplacian`
- Status: Done
- Owner: Implementer
- Source: review of all `Bartosz`/`bchmura`-authored commits, 2026-07-05
  session — High-severity finding #1
- Scope: `__WORK_IN_PROGRESS__/src/allostery/hamiltonians.py` —
  `H11_anisotropic_mechanical`, `H12_anm_scalarised`

## ⚠️ Before implementing

**Do a short review before writing any physics.** Read the notebook
(`notebooks/H_new_engineering (4) CLEAN.ipynb`) for whatever H11/H12 were
originally meant to compute — the module's own docstring for H12 already
half-admits the problem in a comment (`# = 1.0 for unit vector; trace
variant`), which suggests this may have been a known placeholder rather
than a shipped-as-final implementation. Confirm what the *intended* formula
was before inventing a new one — this is a "port from source," not
"design from scratch," task per this repo's own convention (CLAUDE.md
convention 2: port science from the research notebook, cite the section).

## Intent Contract

- Outcome: H11 and H12 either compute genuinely distinct physics from
  their neighbors (H6, H2) as their docstrings describe, or their
  docstrings/registration are corrected to state plainly that they're
  simplified/placeholder variants — not silently shipped as if the
  anisotropic mechanism were implemented.
- In Scope:
  - `H11`: implement actual directional/anisotropic weighting — e.g.
    scale each edge's contribution by a genuine anisotropy measure (the
    docstring's own suggestion, "dot-product of unit displacement,"
    needs a *second* vector to dot against — a reference axis, a mode
    direction, or a pairwise correlation — not just the edge's own unit
    vector dotted with itself, which is where H12's bug came from too).
  - `H12`: same root cause — `k_ij` needs to come from something other
    than `np.dot(r, r)` on a single unit vector. Check whether the
    intended formula was a genuine 3N ANM Hessian trace/projection
    (per the docstring) and implement that, reusing `H13_3N_anm_hessian`'s
    already-correct 3N×3N block construction rather than re-deriving it
    (project/trace that down to N×N instead of building a separate,
    broken N×N approximation).
  - if the notebook shows no such variants were ever specified (i.e.,
    H11/H12 were invented for this port, not sourced) — document that
    plainly and decide whether they're worth keeping at all vs. removing
    from the H1–H13 family (a smaller, honest family beats a padded one
    with duplicates).
- Out Of Scope: touching H1–H10, H13, or `build_H_new` (which doesn't use
  H11/H12 at all — confirmed by reading `build_H_new`'s body).
- Constraints And Invariants: whatever replaces the current bodies must be
  numerically distinct from every other H1–H13 variant on a non-trivial
  test structure — add a regression test asserting this (see Planned
  Validation) so a future edit can't silently re-collapse them.
- Planned Validation: on a synthetic non-colinear structure (reuse the
  T-011 fixture — a 6-residue synthetic helix, chosen specifically because
  a colinear fixture gives spurious degeneracies), assert `H11` is NOT
  equal (elementwise, some tolerance) to `H6`'s output, and `H12` is NOT
  equal to `H2`'s output, on the same coordinates/cutoff.

## TODO

- [ ] Read the notebook for H11/H12's original specification (if any).
- [ ] Implement or correct each per the Intent Contract above.
- [ ] Add the "not identical to its neighbor" regression test for both.
- [ ] Re-run existing `test_hamiltonians.py` (T-011's H1–H13 smoke test)
      to confirm no regression in the properties it already checks
      (PSD/nullity per-Hamiltonian).

## Dependency

- None — self-contained within `hamiltonians.py`.

## Open Questions

- If the notebook has no record of H11/H12 as originally specified
  (i.e., they were invented during the port), is the right call to fix
  them into something meaningful, or to remove them and renumber/rename
  the family honestly? Recommend deciding this once the notebook check
  is done, not before.

## Done

Superseded and closed by **TASK-0096** (filed from the same finding,
re-surfaced by REVIEW-2026-07-13 P2-A, because this task was still open
with both phantom operators still live in `hamiltonians.py`). TASK-0096
did the notebook check this task's own "Before implementing" note called
for, found real original formulas for both `H11_anisotropic_mechanical`
and `H12_anm_scalarised` in `notebooks/H_new_engineering (4) CLEAN.ipynb`
cell 11, ported them verbatim, and added regression tests proving
divergence from their former duplicate-of-H6/H2 bodies. Full
implementation record, validation, and the decision rationale (implement
rather than delete) live in TASK-0096's own Done section — not duplicated
here.
