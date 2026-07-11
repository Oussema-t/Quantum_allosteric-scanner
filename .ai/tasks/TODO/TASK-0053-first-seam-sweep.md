# TASK-0053 First seam sweep — TASK-0003 through TASK-0012

## Context

- ID: TASK-0053
- Title: Run the Seam Protocol's own prescribed "edge-discovery pass" for
  the first time against the now-mostly-landed `__WORK_IN_PROGRESS__/
  src/allostery` module chain (TASK-0003–0012), registering new `.ai/
  seams/` records for cross-unit invariants beyond the 5 already seeded
  by [[TASK-0050]]
- Status: TODO
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

- [ ] Enumerate cross-unit data flows among TASK-0003–0012's modules.
- [ ] Re-check the 3 `OPEN` seeds from [[TASK-0050]] against current
      code state.
- [ ] Name the invariant per flow as an assertion, not prose.
- [ ] Register new `.ai/seams/SEAM-XXXX` records for anything not already
      covered.
- [ ] File owner tasks for any newly-`OPEN` seam without an existing
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

(not yet)
