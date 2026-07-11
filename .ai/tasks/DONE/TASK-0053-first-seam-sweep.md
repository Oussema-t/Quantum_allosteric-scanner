# TASK-0053 First seam sweep — TASK-0003 through TASK-0012

## Context

- ID: TASK-0053
- Title: Run the Seam Protocol's own prescribed "edge-discovery pass" for
  the first time against the now-mostly-landed `__WORK_IN_PROGRESS__/
  src/allostery` module chain (TASK-0003–0012), registering new `.ai/
  seams/` records for cross-unit invariants beyond the 5 already seeded
  by [[TASK-0050]]
- Status: Done
- Owner: General Critic (the protocol explicitly names this "a dedicated
  review role," distinct from a node-execution Implementer — see
  `SEAM_PROTOCOL.md`'s "The seam sweep" section: "Node-execution agents
  will not find seams — a seam is by definition outside any single
  task's scope")
- Claimed By: —
- Claimed At: —
- Source: user request, 2026-07-11 session — see [[TASK-0050]]'s Source.
  [[TASK-0050]] adopts the protocol's machinery; this task is the first
  real use of it, which the protocol itself requires ("Seed it with the
  edges already known... including the ones that are fine").
- Crit Ref: timing matches the protocol's own guidance — "run at each
  phase boundary and before any multi-task merge." TASK-0003 through
  TASK-0012 (data foundation through baselines/pathways) is close to a
  natural phase boundary per `PLAN.md`'s phasing, and several of these
  modules are landing concurrently right now via parallel Implementer
  threads (TASK-0011/TASK-0012 both actively claimed as of this task's
  filing) — a good moment to check what's been assumed across their
  boundaries before more work stacks on top.

## Intent Contract

- Outcome: every cross-unit data flow among the landed
  `__WORK_IN_PROGRESS__/src/allostery` modules has either a `VERIFIED`
  seam record, a newly-registered `OPEN` one with a named owner, or is
  confirmed not to need one (single-module, no cross-boundary invariant) —
  stated explicitly, not silently skipped.
- In Scope:
  - follow the protocol's own 4-step method (`SEAM_PROTOCOL.md`, "The
    seam sweep"): (1) enumerate every cross-unit data flow — what does
    each module *consume* that another *produces*; (2) name the
    invariant that must hold per flow; (3) check VERIFIED vs. needs a new
    `OPEN` record; (4) output new `.ai/seams/SEAM-XXXX` records, never
    silent reconciliation
  - explicitly re-check the 3 already-`OPEN` seeds from [[TASK-0050]]
    against current state (some may have moved since seeding — e.g.
    `SEAM-0005`'s `baselines.py` dependency is actively being
    implemented right now)
  - cover at minimum: `labels.py` -> `protocol.py` (pocket/functional/
    terminal masks into LOPO selection), `protocol.py` -> `analysis.py`
    (frozen-context provenance into reported metrics), `superpose.py` ->
    `analysis.py` (cumulative-overlap gate into which targets proceed to
    scoring), `diagnostics.py`/`report.py` -> whatever consumes their
    output (per TASK-0009/0010, both Done)
- Out Of Scope:
  - fixing anything found — matches every other decide/record-vs-execute
    split in this scaffold (TASK-0018, TASK-0023, TASK-0050). Each newly
    `OPEN` seam gets a named owner task, filed as a follow-up, not
    resolved inline.
  - re-litigating the 2 already-`VERIFIED` seeds without new evidence —
    confirm they still hold given current code, don't redo the original
    verification from scratch.
- Constraints And Invariants:
  - every new record needs a real owner task per the protocol's core
    rule — if no natural owner exists yet, this task files one (matches
    how [[TASK-0050]] handled its own seed records).
  - evidence-first: cite the actual function/line producing and
    consuming each flow, not a general description of the module.
- Planned Validation: the protocol's own Gate 2 — "the repo is not green
  if any `OPEN` seam has no passing seam-test" — applied to this sweep's
  own output: every new `OPEN` record from this task must name a
  seam-test (may be `xfail`), not just an invariant in prose.

## In Progress

None

## TODO

- [x] Enumerate cross-unit data flows among TASK-0003–0012's modules.
- [x] Re-check the 3 `OPEN` seeds from [[TASK-0050]] against current
      code state. (Found 5, not 3, existing seeds — TASK-0057 landed
      SEAM-0006 concurrently with this sweep; treated as already covered,
      not re-verified from scratch.)
- [x] Name the invariant per flow as an assertion, not prose.
- [x] Register new `.ai/seams/SEAM-XXXX` records for anything not already
      covered.
- [x] File owner tasks for any newly-`OPEN` seam without an existing
      natural owner.

## Dependency

- [[TASK-0050]] — must land first; this task needs `.ai/seams/` and its
  README/conventions to exist.
- [[TASK-0011]], [[TASK-0012]] — currently in progress; this sweep should
  probably wait for at least these two to land (or explicitly note which
  flows involve still-open modules and treat those as provisional).

## Open Questions

- Should this run now (against a partially-landed module set, with
  TASK-0011/0012 still in flight) or wait for the full TASK-0003–0016
  chain to close? The protocol says "at each phase boundary," and
  TASK-0003–0012 is not quite the full phase — recommend running it now
  for the modules that are Done, and re-running/extending after
  TASK-0013–0016 land, rather than waiting for one big sweep at the very
  end (matches the protocol's own "not more upfront planning... seams
  are discovered continuously" framing).

## Done

Read `labels.py`, `protocol.py`, `superpose.py`, `analysis.py`,
`diagnostics.py`, `report.py` in full (current landed state, all Done).
Cross-checked `test_protocol.py`/`test_report.py` directly rather than
trusting docstrings.

**Existing seeds re-checked (5, not the 3 named at filing — SEAM-0006 was
seeded by a concurrent TASK-0057 pass during this sweep, treated as
already-covered rather than re-verified from scratch, per this task's own
Out-Of-Scope on re-litigating without new evidence):**

- **SEAM-0001** (labels seq-pocket ↔ superpose geom-pocket) — confirmed
  accurate as-is, `pocket_cross_map` exists exactly as described. No change.
- **SEAM-0002** (protocol firewall ↔ label readers) — **upgraded from
  "not independently re-verified" to confirmed VERIFIED.** Named the exact
  seam-tests (`test_protocol.py::test_get_pocket_mask_raises_when_target_blocked`
  and two siblings) that genuinely cross the protocol.py↔labels.py/
  superpose.py boundary, distinct from the same-module `assert_readable`
  tests that don't qualify per this registry's own definition.
- **SEAM-0003** (pocket excludes functional/terminal) — confirmed still
  OPEN, no `build_labels()`/assembly function exists. TASK-0052 remains
  correct owner, no change.
- **SEAM-0004** (`AUC_*_optimised` provenance) — confirmed still OPEN,
  strengthened with direct evidence: `verdict_template`'s `provenance` is
  a plain caller-supplied keyword, zero connection to
  `protocol.current_context().mode` anywhere in the codebase. TASK-0055
  remains correct owner.
- **SEAM-0005** (verdict signal vs. baseline floor) — confirmed still
  OPEN, corroborated from the `diagnostics.py` side (prior evidence was
  `baselines.py`-side only): `classify_failure`'s actual signature has no
  `floor_scores` parameter. TASK-0058 remains correct owner.
- **SEAM-0006** (pathways→viz) — landed by TASK-0057 concurrently with
  this sweep; not re-verified, out of scope to re-litigate.

**New seams found and registered:**

- **SEAM-0007** (new): `superpose.run_superpose`'s cumulative-overlap
  go/no-go gate is never consumed by any of `analysis.py`'s six scoring
  functions — confirmed by reading every one of their signatures, none
  reference the gate at all. This is one of the four flows this task's own
  Intent Contract named to check explicitly, and it was open. Filed
  **TASK-0059** as owner (no natural existing owner found).
- **SEAM-0008** (new): no assembly function converts `analysis.py`'s real
  (nested) output shapes into `report.verdict_template`'s expected flat
  schema (`AUC_apo_Hnew_default` etc.) — confirmed by grep: every
  occurrence of those key names across the whole package is inside
  `test_report.py`'s hand-built fixture, zero in production code.
  `verdict_template` has never once been exercised against real
  `analysis.py` output. Did not file a new task — **TASK-0056** (existing,
  unclaimed Phase 4 review of `report.py` among others) is the natural
  owner and was already scoped to ask exactly this question; cross-linked
  the finding into its Intent Contract directly instead of duplicating.

**Not done in this pass:** did not extend the sweep to TASK-0013–0016
(coarse.py/viz.py/holo-direction module/heat-test) — those aren't Done
yet, matching this task's own Open-Question recommendation to run now for
landed modules and extend later rather than wait for one sweep at the end.
A follow-up sweep once TASK-0013–0016 land would be a new task, not a
reopening of this one.
