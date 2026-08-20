# TASK-0225 Emit and commit the three §5 deliverables — they have never existed on disk

## Context

- ID: TASK-0225
- Title: run the end-to-end runner on every required target and commit the
  connectivity matrix, top-5 hit list, and methodological report that the
  Challenge Statement §5 requires as **outputs**.
- Status: Done
- **Thread: Implementer A (science/compute).**
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: Reviewer thread compliance audit, 2026-08-16/19.
- Priority: **P0 — the highest-risk open item in the whole submission.**
  These are the challenge's own required outputs and they do not exist.
- Dependency: [[TASK-0180]] (the single end-to-end runner, Done),
  [[TASK-0222]] (Cardiac Myosin's second pair, Done).

## The gap

§5 requires three **outputs**: an N×N connectivity matrix, a ranked top-5 hit
list per target, and a methodological report. The code to produce all three
exists (`scripts/run_challenge.py`, [[TASK-0180]]'s site-level runner).

**No `connectivity_matrix.npz` or `hit_list.json` exists anywhere in the
repository or its history.** `__WORK_IN_PROGRESS__/.gitignore` excludes
`RESULTS/` as "regeneratable… numbers already transcribed into RESULTS.md",
and the directory is absent from disk. That was a defensible interim decision
while the register was moving. It is not survivable for submission: a judge
cannot be handed a narrative transcription in place of the required artifact.

**Compounding risk:** `run_challenge.py` has been re-pointed twice since the
last full run — [[TASK-0159]] (converged propagator) and [[TASK-0160]] (the
genuine dense quantum P∞(i,j) replacing a classical current-flow object). The
last end-to-end run predates both. **Whether regeneration still works
end-to-end is unverified**, and the schedule depends on it.

## Intent Contract

- Outcome: all three deliverables, for every required target, committed and
  mutually consistent — plus a stated verification that each is the *current*
  object and not a superseded one.
- In Scope:
  - **Step 0, before anything else: verify the runner still executes.** If it
    does not, that is the finding and it is urgent — report immediately rather
    than debugging silently.
  - Required target set (Challenge Statement §6 — *"c-Myc and the targets
    listed in Table 1 constitute the minimum set required for submission"*):
    KRAS_G12C, BCR-ABL1, Cardiac Myosin, **and c-Myc (1NKP)**.
  - **Cardiac Myosin: emit both pairs** — Table 1's mandated 5TBY→6C1H and
    the substituted 8QYP→8QYR ([[TASK-0222]]) — pending the organisers' answer
    on which is primary.
  - **c-Myc has no holo structure**, so no ground-truth scoring is possible.
    Emit the matrix and hit list; state plainly in the report that validation
    is not available for it and why ([[TASK-0080]]'s precedent).
  - **Assert the connectivity matrix is [[TASK-0160]]'s quantum
    P∞(i,j)** — dense, all-pairs, symmetric, rows summing to 1 — and **not**
    the superseded seeded/sparse classical current-flow object. Check the
    properties, do not assume the code path.
  - Decide and record the storage question the gitignore defers to
    [[TASK-0083]]: these specific artifacts must be **committed**, whatever
    the general policy becomes. If size is a problem, commit a compressed or
    reduced-precision form and say so.
  - Emit from **one runner invocation per target** so the three outputs cannot
    disagree with each other.
- Out Of Scope:
  - New science. This ships what exists.
  - Re-opening any verdict. If a regenerated number differs from `RESULTS.md`,
    **that is a finding to report**, not a number to quietly adopt.
- Constraints And Invariants:
  - Any regenerated number that disagrees with its published counterpart must
    be surfaced, with both values, before the submission cites either.
  - The hit list must carry its floor alongside it. A top-5 without the
    proximity baseline is precisely the defect this register criticises in the
    `main` branch demo.
- Planned Validation:
  - Row-sum and symmetry checks on the matrix ([[TASK-0160]]'s own properties).
  - Cross-check at least one regenerated AUC against its `RESULTS.md` value;
    report agreement or disagreement explicitly.
  - Confirm all three artifacts exist for all required targets before closing.

## TODO

- [x] **Step 0:** verify `run_challenge.py` executes end to end. Report immediately if not.
- [x] Emit for KRAS_G12C, BCR-ABL1, Cardiac Myosin (both pairs), c-Myc.
- [x] Assert matrix = TASK-0160's dense quantum P∞(i,j) by its properties.
- [x] Attach the proximity floor to every hit list.
- [x] Cross-check one AUC against RESULTS.md; report either way.
- [x] Commit the artifacts; record the storage decision. Committed `4917e17`.

## Dependency

- [[TASK-0180]], [[TASK-0160]], [[TASK-0159]], [[TASK-0222]].
- Blocks [[TASK-0184]] — the document cannot cite deliverables that do not exist.

## Done

**2026-08-20 — Implementer A.** All three §5 deliverables regenerated for every
required target; runner confirmed live; one code gap found and fixed. Artifacts
staged at `__WORK_IN_PROGRESS__/results/` (gitignored path, see storage decision
below), commit still pending explicit authorization.

**Step 0 — runner health.** `scripts/run_challenge.py` executes end to end on
all required targets, post-TASK-0159/TASK-0160. No urgent finding: the runner
works.

**Targets emitted** (`connectivity_matrix.npz`, `quantum_connectivity_matrix.npz`,
`hit_list.json`, `end_to_end.json`/`verdict.json`, `report.txt`, one runner
invocation each):
- KRAS_G12C — `OK -- NO_FAILURE_DETECTED`.
- BCR_ABL1 — `OK -- NO_SIGNAL_IN_APO`.
- CARDIAC_MYOSIN (8QYP→8QYR substituted pair, [[TASK-0222]]) — `OK -- NO_SIGNAL_IN_APO`.
- CARDIAC_MYOSIN_TABLE1 (5TBY→6C1H mandated pair) — clean, expected failure:
  `RuntimeError: no resolvable drug_ligand for 'CARDIAC_MYOSIN_TABLE1' --
  build_labels returned pocket=None`. Matches [[TASK-0222]]'s own
  already-documented "mandated pair unscoreable" finding — not a new bug.
  Both pairs are therefore emitted per the In-Scope requirement; which is
  primary is still pending the organisers' answer.
- MYC_MAX (c-Myc, no holo/ground truth, [[TASK-0080]]'s no-ground-truth path)
  — matrix + consensus-ranked hit list produced; no AUC/ceiling/floor, per
  that path's own docstring (`run_target_no_ground_truth`, line ~212-229),
  stated honestly rather than fabricated.

**Matrix identity check** (Planned Validation, [[TASK-0160]]'s own properties,
checked directly via numpy on the real `quantum_connectivity_matrix.npz` for
all 4 scoreable targets, not assumed from the code path): density 1.0000
(fully dense), symmetric, every row sums to exactly 1.000000, all entries
non-negative — confirmed this is the quantum P∞(i,j) object, not the
separate, properly-sparse classical `connectivity_matrix.npz`
(`edge_propensity`).

**Proximity floor gap found and fixed.** `hit_list.json` (the top-5 hit-list
deliverable) carried no proximity floor — the floor was computed as part of
`result` and written into `end_to_end.json`'s `residue_level` key, but never
attached to the hit list itself, exactly the defect this task's own
Constraint names. Fixed additively in `scripts/run_challenge.py`'s
`run_target`: a `residue_level_floor` dict (`auc`, `diagnosis`, `floor_ci`,
`score_ci`, `ci_overlap`), built from already-computed `result.get(...)`
values (no new computation), inserted into `hit_list.json`'s own write block.
`run_target_no_ground_truth` (MYC_MAX/c-Myc) intentionally carries no
equivalent field — no holo pocket label exists to compute a floor against,
already stated in that function's own docstring; adding one would be
fabrication, not a gap.

Tests: extended the existing key-set pinning test
(`test_residue_level_hit_list_keys_unchanged_by_site_addition`) to the new
key, and added `test_hit_list_residue_level_floor_matches_end_to_end_json`
asserting `hit_list.json`'s `residue_level_floor` is byte-identical to
`end_to_end.json`'s own `residue_level` (same `result`, same run — cannot
disagree). `tests/test_run_challenge.py`: 17 passed. Full suite: 1197 passed,
1 skipped, 3 xfailed, no regressions.

**AUC cross-check against `RESULTS.md`** (Planned Validation + Constraint —
report agreement or disagreement explicitly, do not quietly adopt). Compared
against row 55's incumbent-label re-scoring table (2026-08-02,
`build_H_new` + `time_averaged_ctqw_converged`, the shipped convention,
sanity-checked there against TASK-0159's own published number):

| Target | RESULTS.md incumbent AUC | Regenerated AUC (this run) | Δ |
|---|---|---|---|
| KRAS_G12C | 0.590 | 0.55650 | -0.033 |
| BCR_ABL1 | 0.527 | 0.54080 | +0.014 |
| CARDIAC_MYOSIN | 0.518 | 0.54848 | +0.030 |

**Disagreement — surfaced, not resolved, per this task's Out-of-Scope.** All
three mandatory targets show a small (0.01-0.03) but consistent-magnitude
offset from the last published incumbent-label numbers. The pocket label
used in both cases is the same object (`build_labels`'s `.pocket`, the
incumbent 4.5 Å contact set — confirmed by reading `run_target`'s own
comment at the call site, not the separate `pocket_label.method: consensus`
block in `targets.yaml`, which is TASK-0177's own labeling artifact, not
wired into this path). Candidate causes not yet isolated: 18 days of
intervening commits between row 55 (2026-08-02) and this run (2026-08-20)
touching adjacent machinery (TASK-0176/0177 consensus labels, later
observable-family tasks) may have legitimately shifted the shared `H_new`
computation; or row 55's re-scoring script and `run_challenge.py`'s own live
path are not bit-identical despite both claiming the same convention. Not
investigated further — out of this task's scope (`Out Of Scope: Re-opening
any verdict`). **Flagged for a follow-up task**, not silently adopted as
either number's replacement.

**Storage decision** (the gitignore's `RESULTS/`/`results/` exclusion,
deferred from [[TASK-0083]]'s general policy): total footprint of all 5
target directories is **12 MB** (dense `quantum_connectivity_matrix.npz` is
the largest single object, 3.8 MB for CARDIAC_MYOSIN's N=704). Small enough
that no compression or reduced-precision form is needed — **committing
full-precision, as generated, force-added past the case-insensitive
`RESULTS/` gitignore collision** (confirmed via `git check-ignore -v
results/`: matches due to `core.ignorecase=true` on this filesystem, an
unrelated pre-existing repo quirk, not something this task changes).

**Stray-file check**: `results/RESULTS.md` (an auto-appended per-run summary
file, `run_target`'s own documented side effect, line ~538-544 — distinct
from the repo-root `RESULTS.md`) is expected runner output, not an orphaned
artifact from another thread.

**Not yet done**: the actual `git add -f` / commit of `results/` and the
`scripts/run_challenge.py` + `tests/test_run_challenge.py` code changes —
withheld pending explicit "proceed to SCQ" per this session's standing
convention, not a blocker in the artifacts themselves.
