# TASK-0290 — Make `detect_active_site` deterministic and recompute every `min_A`

- Status: Done — **run a day early, 2026-08-29, on the repo owner's explicit go-ahead** (originally scheduled for Sunday 2026-08-30; confirmed with the user before starting, see Done section)
- Assignee: Implementer A
- Priority: **High — last caveat on [[TASK-0288]] Finding F, which is headed for the Phase 1 write-up**
- Filed: 2026-08-29 by Reviewer thread (user-directed: "let us do the recompute on Sunday")
- Related: [[TASK-0289]], [[TASK-0288]], [[TASK-0258]], [[TASK-0253]], [[TASK-0184]]
- **LANE 1 — critical path. Sole owner of `backend/active_site.py` and of
  `results/tasks/0258_allosteric_distance_taxonomy/pocket_taxonomy.json`.
  No other lane may touch either.**
- **Blocks: [[TASK-0293]] (2 of its frozen 20 are unstable targets),
  [[TASK-0288]] Finding F, [[TASK-0184]]'s Finding F wording.**
- Absorbs the remediation scope formerly duplicated in [[TASK-0289]],
  which is now closed as a defect record only.

## Why

[[TASK-0289]] measured the blast radius of the `detect_active_site`
non-determinism and **rejected** the hypothesis that it manufactured
[[TASK-0288]] Finding F's contact spike. What it did **not** do is
recompute `min_A` under a deterministic active site — every `min_A` in
the register is still the value produced by whichever fallback tier
answered on the run that wrote it.

Finding F (**~32% of the benchmark has its "allosteric" pocket covalently
bonded to the active site**) is the strongest benchmark-validity result
this register holds and is headed for the Phase 1 submission. It should
go in **without an asterisk**.

## Scope

- [x] **Fixed `backend/active_site.py:174-187`.** Two separate defects in
      one block:
      1. **Non-determinism** — resolves once, caches to disk keyed by
         `(pdb_id, chain)` at `pdb_cache/active_site_cache.json`; network
         only on a cache miss. Verified: warm call ~0.1ms, byte-identical.
      2. **Silent downgrade** — added an additive `raise_on_error` kwarg
         through `rcsb._get_json`/`data_layer.fetch`/`rcsb.ligands_and_
         sites`/`discovery.get_uniprot` (default False, every existing
         caller unchanged, HTTP 404 always still returns `None`).
         `detect_active_site`'s tiers opt in: a real network failure
         (`_RETRYABLE` -- `URLError`/timeout/`OSError`/`JSONDecodeError`
         only) retries once then raises `ActiveSiteNetworkError`, verified
         live via a monkeypatched permanent failure. A real negative still
         returns `None` and falls through, unchanged.
- [x] Propagated `source` through `task0242_two_stage_dryrun.prep()` --
      stashed on the already-returned `cfg` dict (`cfg["active_site_
      source"]`, no tuple-shape change, zero call-site breakage) rather
      than a 5th return value. `task0258_allosteric_distance_taxonomy.
      measure()` now records it as `active_site_source` per target.
- [x] Recomputed `min_A`/`median_A`/`max_A` for all 33 taxonomy targets
      under the fixed path, fresh cold cache. **Diffed against the
      committed taxonomy: 0/33 moved** -- every value byte-identical,
      including the 3 unstable targets. Reported as a measured outcome
      (Constraint: not gated on reproducing committed numbers), not
      assumed clean.
- [x] Re-ran [[TASK-0288]] Finding F on the corrected values: 9/28
      (32.1%), binomial p=2.033e-06, all 9 at sequence gap=1, identical
      residue pairs -- exact reproduction of the published numbers.
- [x] Re-checked `DHPS_GC7`, `NAMPT_NPA1R`, `HIV1_RT` directly (two
      consecutive calls, fresh cache): all 3 now stable. `HIV1_RT`
      resolves to `uniprot`, 7 residues, never empty -- [[TASK-0253]]'s
      failure mode confirmed closed.

## Constraints

- **Do not pin to whichever tier reproduces the currently committed
  numbers.** The deliverable is a defensible recorded provenance per
  target, not agreement with values that may themselves be artifacts.
- If a target's `min_A` moves across the 1.5 Å spike boundary or the
  near/far boundary, that is a **result to report**, not a regression to
  suppress.
- Findings A–E of [[TASK-0288]] are **not** gated on this: they test
  scale-free landscape shape against scale-free position within each
  protein's own geometry and do not depend on the absolute active-site
  definition. Do not re-open them.

## Handoff when done

Post the recompute diff (every target whose `min_A` moved, with old and
new values and the `source` that produced each) before doing anything
else with it. [[TASK-0293]] is waiting on exactly that diff and can
re-run in minutes once it exists.

**Posted in `RESULTS.md` (2026-08-29): 0/33 moved.** [[TASK-0293]] can
drop its PROVISIONAL label -- its two dependency targets (`DHPS_GC7`,
`NAMPT_NPA1R`) are confirmed unchanged. [[TASK-0184]]'s Finding F wording
needs no numeric correction, only the provenance asterisk removed
(rewording itself is explicitly out of this window's scope, per
`.ai/COMPUTE_WINDOW_2026-08-29.md`).

## Note

The bare-`except Exception` audit across the scientific path is **LANE 3**
([[TASK-0294]]), not part of this task — it is a read-only sweep and must
not block the recompute.

## Done (2026-08-29, Implementer A)

**Timing**: task file scheduled this for Sunday 2026-08-30. User explicitly
confirmed proceeding a day early when asked (`AskUserQuestion`, "Proceed
now" selected) -- not assumed from the pickup request alone, given the
file's own multi-lane coordination language implied deliberate timing.

**Root cause chain, traced deeper than the task's own literal scope**:
`detect_active_site`'s bare `except Exception` (the named defect) could
never actually distinguish anything, because `rcsb._get_json` and
`data_layer.fetch` *underneath* it already swallowed every network
exception into a bare `None` -- by the time an exception would reach
`detect_active_site`'s own try/except, there was nothing left to catch
(confirmed: `_from_uniprot` never raised under the old code, on any input).
Fixing only the named block would have been a no-op. Threaded an additive,
backward-compatible `raise_on_error` opt-in through the whole call chain
instead (`rcsb.py`/`discovery.py`/`data_layer.py`) so the distinction the
task asks for is actually possible, while leaving every other existing
caller of those shared functions byte-for-byte unaffected (default
`raise_on_error=False`).

**Verified empirically at every step, not by code inspection alone**:
cold-vs-warm cache timing measured directly; a monkeypatched permanent
network failure confirmed 2 retries then a raised
`ActiveSiteNetworkError`, not a silent fallback; all 3 previously-unstable
targets re-resolved twice each and confirmed stable; the recompute diff
(0/33) computed by direct JSON comparison against a saved pre-fix copy,
not assumed from "the code looks right now."

**`backend/` test suite**: 6 pre-existing failures in
`test_analysis_characterization.py` (KRAS_G12C pinned golden values,
stale since the 2026-08-26 4OBE->4LDJ genotype fix never propagated to
those fixtures) -- confirmed identical with this task's own changes fully
reverted via `git stash`, so not a regression. Flagged, not fixed (out of
LANE 1's scope).

**Headline finding**: the fix closes a real, live-reproduced risk
([[TASK-0289]]'s 16.6 Å swing) but the currently-published taxonomy was
not, in fact, corrupted by it -- 0/33 targets move. Finding F reproduces
exactly (9/28, p=2.033e-06) and [[TASK-0291]]'s `max_A` restatement
reproduces exactly (7/9 spike targets within 8.4 Å). Both go to the Phase
1 submission without an asterisk.

**Not done (explicitly out of this window's scope, `.ai/COMPUTE_
WINDOW_2026-08-29.md`)**: rewording [[TASK-0288]] Finding F in the
collaborator brief or [[TASK-0184]] itself -- that is a separate,
deliberately-deferred step for whoever owns those documents, now unblocked
by this diff.

**Moved TODO/IN_PROGRESS -> DONE.**
