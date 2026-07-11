# TASK-0057 Retroactively apply the Seam/Invariance Protocol to TASK-0012 (`pathways.py`)

## Context

- ID: TASK-0057
- Title: Register the seam and invariant gaps TASK-0012 (`pathways.py`)
  left open once the newly-adopted Seam/Invariance protocols ([[TASK-0050]],
  [[TASK-0051]]) are applied to it
- Status: Done
- Owner: Implementer
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-11 12:21
- Source: user request, 2026-07-11 session — after reading the Architect
  thread's protocol-adoption commit (`e1ee382`), asked to "proceed with the
  topics that were freshly discovered according to the updated protocols."
  TASK-0012 closed to DONE *before* the new Seam gate landed, so it was
  never checked against it — this task is that retroactive check, run by
  the same Implementer thread that built the module, since it already has
  full context on `pathways.py`'s math.

## Intent Contract

- Outcome: `pathways.py`'s two gaps under the new protocols are closed or
  explicitly registered as OPEN with a real owner — not silently left
  unaddressed now that a mechanism exists to catch them.
- In Scope:
  1. **Seam gate.** `pathways.py`'s output (`edge_propensity`,
     `extract_pathway`) is consumed by `viz.py` (TASK-0014, not yet built)
     — this is "opens a seam" under `SEAM_PROTOCOL.md`'s own definition.
     Register `SEAM-0006` with owner TASK-0014; the seam-test itself can't
     be written for real until `viz.py` exists (same precedent as
     SEAM-0004/SEAM-0005 pointing at not-yet-landed consumers), so this
     stays `OPEN` by construction.
  2. **Invariance gate.** `edge_propensity`/`extract_pathway` are reported
     quantities with no GAUGE/KNOB/SIGNAL table yet. Unlike the seam above,
     the GAUGE rows *are* testable right now, entirely within this
     module's own scope (no dependency on `viz.py`) — write them for real,
     not just register the gap:
     - SE(3) invariance: `pathways.py` takes only `H` (never raw
       coordinates) as input, so it is SE(3)-invariant *by construction*
       whenever the `H` it's fed is itself SE(3)-invariant — which
       `hamiltonians.py`'s contact-matrix construction already is (built
       from pairwise Euclidean distances). Verify this compositionally:
       rotate+translate coordinates, rebuild `H` via `hamiltonians.py`,
       confirm `pathways.py`'s output is unchanged to `atol≈1e-9` — this
       is the actual empirical check the Invariance Protocol's own rule
       of engagement demands ("multi-turn agreement is not verification";
       a proof-by-inspection still needs the twelve lines of code run).
     - Permutation invariance: relabeling residue indices (`H' = P H
       Pᵀ`) must permute `edge_propensity`/`extract_pathway`'s output
       identically, not just "should mathematically" — same empirical
       standard.
  - KNOB (choice of `H` variant passed in — H2 vs H_new etc.) and SIGNAL
    (null control on a structureless graph) rows are registered but left
    `OPEN`, same precedent as INV-0001 leaving its own KNOB/SIGNAL rows
    open at seeding — full grid characterization is out of this bounded
    slice.
- Out Of Scope: building `viz.py` itself (TASK-0014); KNOB/SIGNAL
  characterization (follow-up, not filed as a separate task yet — the
  `OPEN` row in `INV-0002` is the marker).
- Constraints And Invariants: this task's own output must follow the
  registry formats `SEAM-0003`/`SEAM-0004`/`SEAM-0005`/`INV-0001` already
  established — no new format invented.
- Planned Validation: the two new GAUGE tests actually run and pass
  (`pytest_local.py wip-all`), not just asserted in prose.

## In Progress

None

## TODO

- [x] Add SE(3)-invariance test (compose `hamiltonians.py` + `pathways.py`).
- [x] Add permutation-invariance test.
- [x] Run `pytest_local.py wip-all` for real.
- [x] Write `.ai/seams/SEAM-0006-pathways-viz-consumption.md`.
- [x] Write `.ai/invariants/INV-0002-pathways-edge-propensity.md`.
- [x] Update `.ai/COMMON.md` registry row + move this task to DONE.

## Dependency

- [[TASK-0012]] (Done) — the module this task retroactively covers.
- [[TASK-0050]] / [[TASK-0051]] — the protocols being applied.
- [[TASK-0014]] — named as SEAM-0006's owner (not claimed or started by
  this task).

## Open Questions

- None new; KNOB/SIGNAL characterization for `INV-0002` is left as a
  standing gap, not a question — file a dedicated task if/when someone
  picks it up, per INV-0001's own precedent.

## Done

- **SEAM-0006** registered (`.ai/seams/SEAM-0006-pathways-viz-consumption.md`):
  `pathways.py` output -> `viz.py` (TASK-0014) boundary, `OPEN`, owner
  TASK-0014 — cannot have a real seam-test until `viz.py` exists, same
  precedent as SEAM-0004/SEAM-0005 pointing at not-yet-landed consumers.
- **INV-0002** registered (`.ai/invariants/INV-0002-pathways-edge-propensity.md`):
  - SE(3) invariance: **GAUGE-VERIFIED**. `pathways.py` never takes
    coordinates, only `H` — invariant by construction given an
    SE(3)-invariant `H`. Verified compositionally (rotate+translate real
    coords, rebuild `H` via `hamiltonians.H2_combinatorial_laplacian`,
    confirm `edge_propensity` identical): measured `max diff == 0.0`
    before the assertion was written, not assumed from the proof alone.
  - Permutation invariance (`edge_propensity`): **GAUGE-VERIFIED**,
    same empirical standard.
  - Permutation invariance (`extract_pathway`'s traced path):
    **PARTIAL** — verified for the tested graph/permutation (no exact
    tie encountered), but the greedy walk's node-index tie-break is
    provably *not* permutation-invariant in general when two candidate
    next-hops tie exactly. Recorded as an OPEN caveat in INV-0002, not
    silently passed over.
  - KNOB (H-variant choice, cutoff) and SIGNAL (structureless-graph null
    control): registered but left `OPEN` — out of this bounded slice,
    same precedent as INV-0001 leaving its own KNOB/SIGNAL rows open.
- Three new tests added to `test_pathways.py::TestInvariance`:
  `test_se3_invariance_composed_with_hamiltonians`,
  `test_permutation_invariance_edge_propensity`,
  `test_permutation_invariance_extract_pathway`.
- Full local run: `python3 .ai/tools/pytest_local.py wip-all --json` →
  343 passed, 4 skipped, 1 xfailed (pre-existing, `test_leakage_gate.py`
  per SEAM-0003/TASK-0052), 0 failed.
- What was *not* done, deliberately: no attempt to close the tie-break
  gap or the KNOB/SIGNAL rows — both are real open items, not silently
  dropped, but fixing them is separate follow-up work outside this task's
  bounded scope (retroactive gate-compliance for TASK-0012, not a full
  audit of pathways.py). Whoever next touches `pathways.py` or runs the
  TASK-0053 seam sweep should pick these up rather than assume this task
  closed them.
