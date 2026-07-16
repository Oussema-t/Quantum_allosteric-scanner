# TASK-0090 `select.py::ballistic_exponent` crashes on a multi-index `source`

## Context

- ID: TASK-0090
- Title: `select.unsupervised_score`/`ballistic_exponent`/
  `_hop_distances_from_source` raise `ValueError: The truth value of an
  array with more than one element is ambiguous` when a candidate's
  `"source"` is a multi-residue index array — despite `unsupervised_score`'s
  own docstring precedent ("focusing"/"source_specificity" both support a
  multi-index seed, mirroring `propagators.py`'s "a multi-index source is
  a uniform mass split" convention) implying the whole module does.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer A (this thread)
- Claimed At: 2026-07-16 21:21
- Source: found while implementing TASK-0079.004 (the end-to-end
  orchestrator). `protocol.run_frozen_verdict`'s `candidates_builder`
  naturally wants to offer `select_frozen_config` the same seed
  (`labels.Labels.active_site`, typically several residues — every
  `func_ligand` contact) that `analysis.benchmark`/`ablation`/
  `quantum_vs_classical` already accept fine as a multi-index array
  (confirmed working via `test_analysis.py`'s real KRAS_G12C test,
  `apo_src_idx`). `select.py`'s own scoring path cannot, so `.004` had to
  route around it (single representative seed index for the
  *selection* step only) rather than pass the real multi-residue seed —
  see `run_challenge.py`'s own docstring for that decision.
- Reproduction (empirically confirmed 2026-07-12, not hypothetical):
  ```python
  from allostery.select import ballistic_exponent
  from allostery.hamiltonians import laplacian
  import numpy as np
  H = laplacian(path_adjacency(12))
  ballistic_exponent(H, np.array([2, 3]))   # returns fine, single-seed BFS silently uses only [source] as one opaque list element
  from allostery.select import unsupervised_score
  unsupervised_score([{"H": H, "source": np.array([2, 3]), "t": 5.0}])
  # ValueError: The truth value of an array with more than one element is ambiguous
  ```
  Root cause: `_hop_distances_from_source(H, source)` does
  `dist[source] = 0; frontier = [source]` — for an array `source` this
  wraps the *whole array* as a single list element instead of seeding a
  BFS frontier with each of its residues, and later code
  (`adjacency[node]` / `if dist[nb] == -1`) breaks on that shape. Note
  `ballistic_exponent` alone (called directly, not through
  `unsupervised_score`) does not itself raise — it silently returns a
  number computed from the wrong/degenerate frontier; the crash above is
  `unsupervised_score`'s own `_zscore`/downstream path making that hidden
  wrong-shape state finally explicit. **Both are bugs** — the crash is
  just the visible one.

## Intent Contract

- Outcome: `ballistic_exponent`/`_hop_distances_from_source` correctly
  support a multi-index `source` — BFS frontier seeded from *every* index
  in `source`, `dist[source] = 0` for all of them, matching
  `propagators.py`'s and `analysis.py`'s already-established multi-index
  convention this module's own docstring claims to mirror.
- In Scope: `select.py`'s `_hop_distances_from_source`/`ballistic_exponent`
  only. A regression test with a real multi-index `source` (e.g. two
  residues on a path/star graph, asserting a real, non-degenerate
  `alpha` exponent, not just "does not crash") plus a
  `unsupervised_score`/`select_frozen_config` end-to-end multi-index
  candidate test.
- Out Of Scope: `focusing`/`source_specificity` (already correct, use
  `time_averaged_ctqw` which handles multi-index natively) — do not
  touch code that isn't broken.
- Constraints And Invariants: scalar `source` behavior must stay
  byte-identical (existing tests, e.g. `test_select.py`, must keep
  passing unmodified) — this is a widening fix, not a rewrite.
- Planned Validation: `test_select.py`'s existing suite unchanged +ex new
  multi-index tests; re-run `TASK-0079.004`'s `run_challenge.py` with the
  real multi-residue `source` (removing the single-index workaround this
  task's own fix makes unnecessary) once this lands, to confirm the
  workaround can be safely deleted, not just that the new tests pass in
  isolation.

## Dependency

- [[TASK-0007]] (`select.py`, Done) — the module with the bug.
- [[TASK-0079.004]] — found this while implementing it; that script's own
  single-seed workaround becomes deletable once this is fixed.
- **Blocks [[TASK-0118]]** (added 2026-07-16, per
  `.ai/reviews/REVIEW-panel-2026-07-16-v2.md` §2.1, §5 P0-1).

## Open Questions

- None yet.

## Priority update, 2026-07-16

**Escalated to P0 — highest-priority open task in the plan.** The panel
review found that this task's own crash workaround (`run_challenge.py`'s
single-residue seed, in place *because* this bug forced it) is
independently the dominant driver behind two separate headline
reconciliations this week: TASK-0093's KRAS_G12C AUC swing (~0.44-0.53
array vs. ~0.78-0.82 scalar) and TASK-0106's BCR_ABL1 operator-ranking
sign flip (`H_new` lowest-scoring under the scalar convention, highest
under the array). The panel's own executed check: single-vs-array
seeding gives occupation Spearman only **0.61** even on synthetic data.
Both the "KRAS is a proximity detector" and "ceiling below floor" claims
are gauge-contaminated by this exact workaround and cannot be asserted
as written until it's fixed. **Do not defer this task further** — it is
the hard dependency for [[TASK-0118]], which cannot start without it.

## Done

- 2026-07-16, Implementer A. Root cause confirmed by direct execution
  before fixing (this task's own reproduction snippet): `ballistic_exponent`
  alone does **not** crash on a multi-index `source` -- `_hop_distances_
  from_source`'s `frontier = [source]` wraps the whole array as one list
  element, so `adjacency[node]` runs on a 2-row fancy-indexed slice and
  silently computes a garbage neighbor set (a wrong-answer bug, not a
  raised exception). The actual crash in this task's own documented
  reproduction traces to `source_specificity`'s `others = np.array([i for
  i in range(N) if i != source])` -- `i != source` on an array `source`
  raises exactly `ValueError: The truth value of an array...` inside
  `unsupervised_score`'s per-candidate loop.
- **Correction to this task's own Intent Contract**: `source_specificity`
  was marked Out Of Scope ("already correct, use time_averaged_ctqw which
  handles multi-index natively") -- checked by execution, found false, and
  fixed anyway rather than left broken because a stale scope note said not
  to touch it. `focusing` (no `source` parameter) is unaffected and
  genuinely untouched, matching the rest of that Out Of Scope note.
- Fixed `select.py`:
  - `_hop_distances_from_source(H, source)`: `source` normalized via
    `np.atleast_1d(np.asarray(source, dtype=int))`, `dist[source_idx] = 0`,
    `frontier = list(source_idx)` -- a standard multi-source BFS (each
    node's distance = min hop-count to *any* seed), scalar path
    byte-identical by construction (`np.atleast_1d(3).tolist() == [3]`).
  - `ballistic_exponent`: signature widened to the same `Source =
    Union[int, Sequence[int]]` alias (mirrors `propagators.Source`,
    defined locally rather than cross-imported, matching this module's
    existing decoupling convention); body unchanged, `ctqw`/
    `_hop_distances_from_source` already handle it.
  - `source_specificity`: `others` exclusion set rebuilt via
    `excluded = set(np.atleast_1d(source).tolist())` + membership test,
    replacing the scalar-only `i != source` comparison. Scalar behavior
    identical by construction.
- Tests: `test_select.py::TestMultiIndexSource` (9 new cases) -- multi-source
  BFS correctness (min-over-seeds on a path graph), single-element-array
  matches scalar (both `_hop_distances_from_source` and
  `ballistic_exponent`), scalar behavior unchanged (explicit
  `np.arange(N)` check), `source_specificity` no longer crashes + its own
  exclusion-set edge case, and this task's own Context reproduction
  verbatim (12-node path, `source=np.array([2, 3])`) now returns a finite
  score instead of raising. `test_protocol.py::TestSelectFrozenConfig::
  test_picks_a_winner_with_a_real_multi_index_source` -- the
  `unsupervised_score`/`select_frozen_config` end-to-end test this task's
  own Planned Validation named. All existing `test_select.py`
  (14 pre-existing) and `test_protocol.py` tests pass unmodified --
  `.venv/bin/python3 -m pytest -q test_select.py test_protocol.py` ->
  68 passed.
- **Planned Validation's real-data check**: confirmed the crash workaround
  in `run_challenge.py` (`source = int(np.sort(active_site_idx)[0])`,
  its own module docstring citing this task) is now genuinely removable
  -- ran `select.unsupervised_score` on real KRAS_G12C data with the
  **full** 18-residue active-site array (`labels_obj.active_site`, not the
  single-index workaround) through `H_new`/`H10` candidates: returned
  `[3.0, -3.0]`, finite and differentiated, no crash (4.3s). **Did not
  edit `run_challenge.py` itself** -- that file has another thread's
  own in-progress, uncommitted changes (+137 lines, unrelated), and
  actually changing the pipeline's live seed convention is explicitly
  [[TASK-0118]]'s job (this task unblocks it, per the 2026-07-16 Priority
  update, rather than duplicating its "declare one convention, re-run
  floor/ceiling/actual" scope here).
- Not run through `pytest_local.py wip-all` this session (targeted files
  only, to avoid re-triggering the multi-session-contention hang
  investigated earlier this session).
- Documents updated post-completion, per explicit user request: `EXECUTION_
  PLAN.md`'s Phase 1C.1/1C.2 rows (Done + unblocked), its critical-path
  paragraph, and its progress-tracker ID snapshot (0090 moved Done, 0128
  added TODO, 76→77); [[SEAM-0009]] extended (a 3rd seam-test, the real
  multi-index consumption path, still VERIFIED); [[INV-0004]] gained a new
  KNOB row (scalar-vs-multi-index source, newly characterizable, still
  OPEN -- the actual spread measurement is [[TASK-0118]]'s job); TASK-0118's
  own file updated to reflect it is now unblocked, not still waiting on
  this task.
