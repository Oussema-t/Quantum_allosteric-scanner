# TASK-0083 Result artifact contract ⚠️ decide EARLY

## Context

- ID: TASK-0083
- Title: Define the versioned artifact `allostery` emits and `backend`
  consumes — the seam between research and delivery.
- Status: Done
- Resolution: done
- Resolution Note: Result artifact contract v1 decided (JSON+NPZ hybrid). Reference writer (allostery.artifact) + reader stub (backend/artifact_reader.py, zero allostery imports) implemented. Real KRAS_G12C reference artifact produced from run_challenge.py's own output, round-tripped and tamper-tested.
- Owner: Architect/Planner
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md`'s Architectural premise
  (top of the plan) and Phase 6, item 6.1 — "This one decision keeps
  `backend` free of `allostery` imports and unblocks frontend work **in
  parallel** with the science. Filed early even though 6.2–6.4 are late."
  Final link in the critical path (`... → 5.2 → 6.1`). Keystone decision:
  **"The research package emits versioned result artifacts. The backend
  serves artifacts; it never recomputes science in the request path."**
  This corrects/extends TASK-0018's "port, don't cross-import" verdict —
  `backend/` still imports nothing from `allostery/`, but now reads a
  JSON/NPZ contract instead of having no relationship to the research
  results at all.

## Intent Contract

- Outcome: a documented, versioned artifact format that `allostery/`'s
  pipeline (via TASK-0079's end-to-end run) writes and `backend/` (via
  TASK-0084's results API) reads — with no code import in either
  direction across the `backend/`↔`allostery/` boundary, consistent with
  TASK-0018's Constraints.
- In Scope: the artifact schema, covering (per the plan): the N×N
  connectivity matrix (NPZ), ranked residues + scores, per-target verdict
  (GO / NO / **UNSTABLE**, per TASK-0075) with knob-spread, floor/ceiling/
  headroom (TASK-0082's competence map), a frozen-config **hash**
  (provenance that the result came from the actual frozen pipeline state,
  not a stale or hand-edited run), and general provenance metadata
  (target ID, structure versions, timestamp, pipeline version).
- Out Of Scope: implementing the producer (TASK-0079 already does the
  computation; this task defines what it writes) or consumer (TASK-0084)
  — this task is the contract/schema decision itself, plus perhaps a
  reference writer/reader stub, not the full API.
- Acceptance Scenarios:
  - Given the contract is defined, when `allostery/`'s pipeline finishes
    a target run, then it can write one artifact file/bundle satisfying
    the schema, self-contained (no live recomputation needed to interpret
    it).
  - Given the same artifact, when `backend/` reads it, then it can serve
    every field the frontend (TASK-0085) needs without importing
    `allostery/` or recomputing anything.
  - Given a stale or hand-edited artifact, when its frozen-config hash is
    checked, then a mismatch is detectable (provenance integrity).
- Constraints And Invariants: **decide this early, before 6.2–6.4** per
  the plan's explicit flag — it unblocks frontend work in parallel with
  ongoing science work. Must accommodate TASK-0075's `UNSTABLE` verdict
  state and TASK-0082's floor/ceiling/headroom fields from day one, not
  as a later add-on. No science recomputation in `backend/`'s request
  path (Render cold-start budget, per TASK-0018's Constraints, still
  applies).
- Planned Validation: a reference artifact produced by TASK-0079 for one
  target, validated against this task's schema; a stub reader confirming
  `backend/` could parse it without importing `allostery/`.

## Dependency

- Should be decided **before** TASK-0084 (backend results API) and
  TASK-0085 (frontend research visualization) start, per the plan's
  explicit "decide EARLY" flag — but can be scoped in parallel with
  TASK-0079/5.1-5.2 rather than strictly after them, since the schema
  design doesn't require the actual run to complete first (though
  validating against a real artifact does).
- Must incorporate TASK-0075's verdict vocabulary (GO/NO-GO/UNSTABLE) and
  TASK-0082's competence-map fields (floor/ceiling/headroom).
- Feeds TASK-0084 (backend results API) and TASK-0086 (execution/trigger
  path — how the artifact actually gets produced/refreshed).

## Open Questions

- NPZ vs JSON vs a hybrid (NPZ for the dense connectivity matrix, JSON
  for everything else) — the plan mentions both formats without
  specifying which field uses which; this task should decide and record.

## Done

**Verdict: contract decided (v1, JSON+NPZ hybrid, resolving the Open
Question below explicitly), reference writer + reader stub implemented,
one real reference artifact produced from KRAS_G12C and validated
round-trip including tamper detection. No new science — every field's
value comes from an already-existing, already-tested function.**

**NPZ vs JSON, decided**: NPZ for the dense `N x N` connectivity matrix
only (compact binary, no float-string round-trip risk at `N` up to ~950);
JSON for everything else (scalars, short hit-list/grid arrays, metadata) —
human-readable and small enough that JSON's overhead doesn't matter. Full
schema: `RESULT_ARTIFACT_CONTRACT.md`.

**Every section maps to an already-real function's output, checked
directly before designing anything, not assumed**:
`verdict`/`diagnosis` <- `report.verdict_template`'s own documented keys +
`diagnostics.classify_failure`'s `return_ci=True` shape; `hit_list` <-
`report.assemble_hit_list`; the connectivity matrix <- `pathways.
edge_propensity_to_matrix`; `stability_gate` <- either of two existing,
related-but-distinct gate mechanisms this codebase already has
(`superpose.cumulative_overlap_gate`, GO/NO_GO/UNSTABLE, or `sites.
site_knob_sweep`, STABLE/UNSTABLE — `run_challenge.py`'s own real
end-to-end path calls the latter, confirmed by reading it, not assumed;
schema carries a `"source"` tag rather than forcing one vocabulary);
`competence` <- `COMPETENCE_MAP.md`'s own floor/ceiling/actual/headroom
convention, including its already-established handling of the degenerate
`ceiling <= floor` case (a `headroom_reason` string instead of a
nonsensical fraction, not reinvented).

**Real finding while designing provenance, not assumed reusable**:
`protocol.stamp_provenance`/`verify_frozen_stamp` already exist and look
like exactly what this task's "frozen-config hash" wants — checked
directly before reusing, and they are not suitable. The mechanism issues
a random token into an in-process, in-memory Python `set`
(`protocol._issued_frozen_stamps`) and verifies *set membership*, which
has no meaning once the process exits and specifically **cannot be
verified after the artifact is serialized to disk and read back by a
different process** — `backend/` reading an artifact `allostery/` wrote in
an earlier run is definitionally a different process. `frozen_verified`
is still recorded (a real, write-time fact worth keeping), but two new,
stateless hashes do the actual provenance work `RESULT_ARTIFACT_
CONTRACT.md`'s own Acceptance Scenario needs: **`content_hash`**
(self-integrity — SHA256 over the artifact's own canonical JSON minus
itself, catches hand-editing) and **`config_hash`** (SHA256 over the
resolved target config + git commit at write time — catches a stale run,
comparable against a freshly recomputed hash of the current config).

**Reference implementation**:
- `allostery.artifact.write_result_artifact(...)` (`src/allostery/
  artifact.py`) — the writer. Every argument independently optional,
  omitted (not null) when absent, matching `verdict_template`'s own
  "missing key renders N/A" philosophy extended to this artifact.
- `backend/artifact_reader.py` — the reader stub (not the full
  [[TASK-0084]] API). **Zero imports from `allostery`**, checked
  mechanically (`TestNoAllosteryImport`, parses this file's own AST and
  asserts no `allostery` import node exists — a comment could go stale
  silently, an AST walk over the actual file cannot). Independently
  re-implements the same hashing recipe rather than importing it (that
  import is exactly what must not exist) — a cross-check test
  (`TestBackendReaderCrossCheck`) confirms both implementations agree
  on both a clean and a tampered artifact, so a future silent drift
  between the two copies is caught, not assumed away.
- 22 new tests (`tests/test_artifact.py`, `backend/test_artifact_
  reader.py`), full local suite re-run clean afterward: 1179 passed, 1
  skipped, 3 xfailed, 0 failed (`pytest_local.py wip-all`) — no
  regression anywhere else in the package.

**One real reference artifact produced, per this task's own Planned
Validation** ("a reference artifact produced by TASK-0079 for one
target"): `scripts/task0083_write_reference_artifact.py` runs
`run_challenge.py`'s own real, already-existing `run_target('KRAS_G12C',
...)` — no recomputation, this task's own Out Of Scope — and repackages
its real output (`verdict.json`, `hit_list.json`, `connectivity_matrix
.npz`) into `results/tasks/0083_reference_artifact/KRAS_G12C/artifact_v1
.json` + `connectivity_v1.npz`. Floor/ceiling (`0.4818`/`0.6288`) read
directly from `COMPETENCE_MAP.md`'s own current headline table (not part
of `run_challenge.py`'s output, a separate TASK-0046 process); `actual`
(`0.5565`) is deliberately this fresh run's own number, not
`COMPETENCE_MAP.md`'s slightly different historical point estimate —
headroom (`50.8%`) recomputed from the two real numbers actually in hand,
cited not silently reused, per this project's own standing convention.
Round-tripped through `backend.artifact_reader.read_result_artifact`
(reads correctly, `content_hash` verifies) and tamper-tested directly
(hand-edited `competence.actual` in a copy — `content_hash` mismatch
correctly raised; hand-edited the NPZ file — matrix-hash mismatch
correctly raised), both per this task's own Acceptance Scenarios.

**Note on the reference artifact's own honesty**: KRAS_G12C's apo (4OBE)
carries [[TASK-0155]]'s own genotype caveat (wild-type, not G12C) —
unchanged and un-hidden here; this task's job is demonstrating the
*contract* works against a real run, not re-litigating that finding. The
artifact's `provenance.config_hash`/`git_commit` let anyone trace exactly
which config state produced these specific numbers.

**Out of scope, as stated in this task's own Intent Contract, not
attempted**: the actual `backend/` results API ([[TASK-0084]]); the
execution/trigger path ([[TASK-0086]]); any recomputation of an already-
real number.

Full schema + design reasoning: `RESULT_ARTIFACT_CONTRACT.md`. Code:
`src/allostery/artifact.py`, `backend/artifact_reader.py`,
`scripts/task0083_write_reference_artifact.py`. Reference artifact:
`results/tasks/0083_reference_artifact/KRAS_G12C/`.
