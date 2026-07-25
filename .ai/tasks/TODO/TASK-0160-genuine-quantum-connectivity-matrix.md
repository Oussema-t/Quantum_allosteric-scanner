# TASK-0160 Replace the connectivity-matrix deliverable with a genuine dense quantum-defined P_∞(i,j)

## Context

- ID: TASK-0160
- Title: `PANEL_REVIEW_2026-07-25.md` W3 — the challenge (§5) requires
  "an N×N matrix where entry (i,j) represents the calculated **quantum**
  connectivity strength between residue i and residue j." What
  `run_challenge.py` currently writes to `connectivity_matrix.npz` is
  `edge_propensity_to_matrix(edge_propensity(H_new, active_idx))` — a
  **classical current-flow linear solve**, **seeded at the active site**
  (not an all-pairs property), and **non-zero only on contact-graph
  edges** (not dense). It fails the deliverable on three independent
  counts: not quantum, not all-pairs, not dense.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `PANEL_REVIEW_2026-07-25.md` §2.2/W3, §4 action item 3.
- Priority: **P0** — a stated, explicitly-scored deliverable requirement
  is currently non-compliant on three counts; the review's own estimate
  is the fix is "nearly free" (½ day).

## Intent Contract

- Outcome: `run_challenge.py` additionally emits a genuine dense,
  symmetric, all-pairs, quantum-defined connectivity matrix:
  `P_inf(i,j) = Σ_k |v_k(i)|² |v_k(j)|²` — exactly what
  `time_averaged_ctqw_converged`'s own eigendecomposition already
  computes internally, just not currently exposed as a full matrix
  (today's callers only ever read the seeded column). Compute once per
  target's eigendecomposition (reuse [[TASK-0130]]'s own `eigh()` call —
  do not re-diagonalize).
- Why required: this is a stated, scored deliverable (challenge §5);
  the current artifact does not meet its own definition of "quantum
  connectivity matrix." Correctly computed, this quantity genuinely *is*
  quantum-defined (an eigenprojector sum of a unitary generator's
  eigenvectors), dense (every (i,j) pair, not just contact edges), and
  all-pairs (not seeded at one site) — satisfying all three failure
  counts at once from machinery that already exists.
- In Scope:
  - New function (natural home: `propagators.py`, alongside
    `time_averaged_ctqw_converged` — Implementer's own call if a
    different module fits better, state reasoning) computing the full
    N×N `P_inf` matrix from one eigendecomposition.
  - Wire into `run_challenge.py`'s output — **additive**: keep the
    existing `connectivity_matrix.npz` output for backward
    compatibility (per this project's own ADD-only convention) and add
    the new dense quantum matrix under an explicit, differently-named
    key/file so a consumer cannot mistake one for the other.
  - Confirm symmetry (`P_inf(i,j) == P_inf(j,i)`, a mathematical
    consequence of the sum-of-outer-products form) and that the diagonal
    is meaningful (`P_inf(i,i) = Σ_k |v_k(i)|⁴`, the IPR-like
    self-term) — state what it means, don't leave it unexplained.
- Out Of Scope:
  - Removing or renaming the existing `edge_propensity`-based output —
    it may still be independently useful (a classical current-flow
    baseline), just must not be mislabeled as the quantum deliverable.
  - Any change to `time_averaged_ctqw_converged` itself.
- Constraints And Invariants: the new matrix must be computed from the
  same `H` each target's real run already builds — no new operator
  choice, no new gauge.
- Planned Validation: symmetry check (exact, not approximate — a
  mathematical identity); a small synthetic-graph test confirming
  `P_inf` matches a brute-force `Σ_k |v_k(i)|²|v_k(j)|²` computation;
  real run on all 3 mandatory targets, confirm output shape/dtype/file
  size are sane for N up to CARDIAC_MYOSIN's ~700-950.

## TODO

- [ ] New `P_inf` matrix function, reusing the existing eigendecomposition.
- [ ] Wire into `run_challenge.py`'s output, additive (new key/file,
      existing `connectivity_matrix.npz` untouched).
- [ ] Symmetry + brute-force-match tests.
- [ ] Real run, all 3 mandatory targets; confirm sane output.
- [ ] `SOFTWARE.md`/`RESULTS.md` note describing the new deliverable and
      explicitly distinguishing it from the pre-existing
      `edge_propensity` output (what each one is, which one is the
      challenge's own "quantum connectivity matrix").

## Dependency

- [[TASK-0130]] (Done) — the eigendecomposition this task reuses.

## Open Questions

- Exact output filename/key for the new matrix — Implementer's own call,
  state reasoning (e.g. `quantum_connectivity_matrix.npz` vs. a key
  inside the existing `.npz`); must be unambiguous to a downstream
  consumer which file satisfies the challenge's own §5 requirement.

## Done

(not yet)
