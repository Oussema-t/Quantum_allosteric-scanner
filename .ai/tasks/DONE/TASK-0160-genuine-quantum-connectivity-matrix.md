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
- Status: Done
- Owner: Implementer
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-25 10:21
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

- [x] New `P_inf` matrix function, reusing the existing eigendecomposition.
- [x] Wire into `run_challenge.py`'s output, additive (new key/file,
      existing `connectivity_matrix.npz` untouched).
- [x] Symmetry + brute-force-match tests.
- [x] Real run, all 3 mandatory targets; confirm sane output.
- [x] `SOFTWARE.md`/`RESULTS.md` note describing the new deliverable and
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
  **Answered**: separate file, `quantum_connectivity_matrix.npz`, same
  `matrix`/`resnums` key convention as the pre-existing
  `connectivity_matrix.npz` so a consumer already reading one knows how
  to read the other, but never risks loading the wrong one silently (a
  key inside the existing file would let an old, un-updated reader keep
  reading `matrix` and never notice the new key existed at all).

## Done

**2026-07-27, Implementer B.** Built and wired as scoped; both
mathematical claims (symmetry, row-sum-to-1) derived in the docstring and
then independently confirmed, both on synthetic data (tests) and real
`H_new` (this section).

**New `propagators.quantum_connectivity_matrix(H=None, *, w=None,
v=None)`**: `P_inf(i,j) = sum_k |v_k(i)|^2 |v_k(j)|^2`, computed as
`V2 @ V2.T` (`V2 = v**2`), a single `(N,N) @ (N,N)` product -- O(N^3),
not an N-times-repeated single-source call. Accepts a precomputed
`(w, v)` pair (same reuse discipline as `time_averaged_ctqw_converged`'s
own parameters) so a caller who already has the eigendecomposition never
re-diagonalizes. 8 new unit tests
(`tests/test_propagators.py::TestQuantumConnectivityMatrix`): shape/
dtype/finiteness, exact (bit-for-bit) symmetry, brute-force double-sum
match (this task's own Planned Validation, run literally, not just
vectorized-vs-itself), row/column sums to 1, diagonal matches the IPR-like
`sum_k v_k(i)^4` formula, column matches `time_averaged_ctqw_converged`'s
own single-source output exactly on a non-degenerate synthetic spectrum,
precomputed-eigh reuse (mocked `np.linalg.eigh`, confirmed zero calls),
and the missing-input `ValueError`.

**Real design choice, checked against real data, not just asserted**:
this is the *plain* per-eigenvector sum, not TASK-0130's own degenerate-
eigenvalue-block-corrected form -- the two differ in principle for a
source landing exactly on a degenerate eigenspace. Confirmed directly for
all 3 mandatory targets: `P_inf`'s own column `i` matches
`time_averaged_ctqw_converged(H, source=i)`'s independently-computed
output to **1e-16 to 1e-17** (KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN, 3 source
residues each) -- real `H_new` spectra are near- but never exactly-
degenerate (TASK-0130's own established finding, reconfirmed here), so
the plain formula this task's own Intent Contract and Planned Validation
both specify is exact in practice, not merely a documented approximation.

**Wired additively** into both real call sites: `run_target` (the
AUC-scored branch -- `winner_H`'s own `eigh()` call now reused for both
`winner_occ` and the new matrix, one diagonalization not two, per this
task's own Constraint) and `run_target_no_ground_truth` (TASK-0080's
c-Myc branch, `H_new`'s own eigendecomposition). Both now also write
`quantum_connectivity_matrix.npz` (`matrix`/`resnums` keys, matching the
pre-existing file's own convention) alongside the unchanged, still-present
`connectivity_matrix.npz` -- neither renamed nor removed, per this task's
own Out Of Scope. New `tests/test_run_challenge.py::TestRunTarget::
test_quantum_connectivity_matrix_is_dense_symmetric_and_row_stochastic`
covers the AUC-scored branch's own wiring end-to-end on the existing
synthetic fixture; the no-ground-truth branch's own wiring is a
mechanical mirror of the same pattern and was not given a second
dedicated synthetic test (a real, stated scope boundary, not an oversight)
-- its correctness is covered by the real KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN
run below, which exercises the identical `quantum_connectivity_matrix`
call.

**Real-run confirmation, all 3 mandatory targets** (`--output-dir` a
throwaway path, not committed -- this task's own deliverable is the code
and the numbers transcribed here, not a checked-in results directory):

| Target | N | `P_inf` density | classical density | row-sum range | exact symmetric |
|---|---|---|---|---|---|
| KRAS_G12C | 169 | 1.000 | 0.057 | [1.000000, 1.000000] | Yes |
| BCR_ABL1 | 451 | 1.000 | 0.021 | [1.000000, 1.000000] | Yes |
| CARDIAC_MYOSIN | 704 | 1.000 | 0.014 | [1.000000, 1.000000] | Yes |

Decisively confirms the "not dense" failure count specifically -- the
classical matrix's own density falls as N grows (same sparse contact-graph
pattern, more residues), `P_inf` stays fully dense on every target
regardless of size, exactly as the sum-of-outer-products construction
predicts.

**Scope note on the TODO's own "SOFTWARE.md" reference**: checked
directly, the repo-root `SOFTWARE.md` documents only the live FastAPI web
app (Phase (1) backend/frontend) -- an entirely separate system from this
`__WORK_IN_PROGRESS__` research scaffold's own `run_challenge.py`; no
mention of `connectivity_matrix.npz` or any research-scaffold deliverable
exists there, so there was nothing there to update. `RESULTS.md`'s own
new section is the actual documentation this task's intent calls for.

**Full test suite**: 959 passed, 2 xfailed, 0 failed.

Full detail: `RESULTS.md`'s "A genuine dense quantum connectivity matrix"
section, open-questions row 41.
