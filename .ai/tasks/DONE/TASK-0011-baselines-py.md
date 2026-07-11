# TASK-0011 Implement `baselines.py` — classical + external baselines

## Context

- ID: TASK-0011
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/baselines.py`
- Status: Done
- Owner: Implementer
- Source: **no notebook precedent — net-new.** `.ai/tasks/PLANS/PLAN.md`
  Phase 2 ("must beat the right baselines... random residues, non-functional
  surface pockets, AND degree/betweenness centrality") and Phase 4
  ("external predictors as a baseline column AND a diagnostic").
  `ALGORITHM_REGISTER.md` §F rates the external tools: fpocket (4),
  PocketMiner (4), ProteinLens (4), AlloPred/PASSer/DeepAllo (3).
- Scope: `__WORK_IN_PROGRESS__/src/allostery/baselines.py` (currently a
  5-line stub) + `__WORK_IN_PROGRESS__/tests/test_baselines.py` (new)

## Intent Contract

- Outcome: a ceiling number only means something if it beats these
  baselines — per `PLAN.md`, "a ceiling that node degree also reaches is
  structure, not your method." This module is the gate that makes Phase 2's
  ceiling claim legitimate.
- In Scope:
  - `random_baseline(n, k)`, `surface_baseline(coords, k)` (non-functional
    surface-pocket score — the challenge's own comparison bar per
    `PLAN.md`).
  - `degree_centrality`, `betweenness_centrality` baselines on the contact
    graph.
  - thin client wrappers for external tools rated ≥3 in
    `ALGORITHM_REGISTER.md`: fpocket (apo-computable cavity score — also
    the openness objective the holo-direction module, TASK-0015, needs),
    PocketMiner, ProteinLens, and optionally AlloPred/PASSer/DeepAllo.
- Out Of Scope: fpocket's use as the holo-direction module's optimization
  objective (TASK-0015 consumes this module's fpocket wrapper, doesn't
  reimplement it).
- Constraints And Invariants: external-server wrappers must degrade
  gracefully (skip + warn, not crash) when offline/rate-limited — this
  module will be exercised in CI environments without guaranteed network
  access. Mirror `rcsb_extract.py`'s existing convention in `backend/`
  ("errors never raise").
- Planned Validation: unit tests for the classical baselines (random,
  degree, betweenness) on synthetic graphs with known centrality structure;
  external-tool wrappers tested only for graceful-failure behavior
  (mock the network call), not for correctness of the external service.

## In Progress

None

## TODO

- [x] Implement `random_baseline`, `surface_baseline`.
- [x] Implement `degree_centrality`, `betweenness_centrality` (networkx
      confirmed already a project dependency — `requirements.txt` and
      existing local-import precedent in `clean.py`).
- [x] Implement fpocket wrapper (local binary, confirmed not installed in
      this sandbox — real subprocess wrapper + graceful degradation path).
- [x] PocketMiner / ProteinLens wrappers — deliberately left not-wired
      (see Open Questions); implemented as honest, deterministic-error
      placeholders rather than guessing at an unverified API contract.
- [x] Unit tests for classical baselines; graceful-failure tests
      (mocked) for the fpocket wrapper.

## Dependency

- TASK-0004 (`labels.py`) — baselines are scored against the same pocket
  labels the main method is scored against.

## Open Questions

- fpocket: local binary dependency (adds a system-level install
  requirement) vs a hosted API — which fits this project's "no GPU,
  embarrassingly parallel, CPU-hours only" compute profile better
  (per `PLAN.md`'s compute note)? Recommend local binary if available in
  the target CI/dev environment, to avoid a network dependency for a
  baseline that should be cheap and always available. Resolved for this
  pass: local binary (`fpocket_baseline`), confirmed not installed here
  (`shutil.which("fpocket")` returns None) — real wrapper built, graceful-
  degradation path is what actually runs in this sandbox.
- Which of AlloPred/PASSer/DeepAllo (all rated 3, "lower priority than the
  three above" per `ALGORITHM_REGISTER.md`) are worth building clients for
  at all vs. just fpocket + PocketMiner + ProteinLens (all rated 4)?
  Recommend deferring the rating-3 tools unless the submission specifically
  needs the extra breadth. Not built this pass, per that recommendation.
- New: PocketMiner and ProteinLens are both rated 4/4 but
  `ALGORITHM_REGISTER.md` documents no concrete API/local-inference
  contract for either. Rather than guess at an endpoint (a wrong one would
  produce silently-wrong external-baseline numbers — worse than an honest
  gap), both are implemented as deterministic `{"error": "not yet
  wired..."}` placeholders with the right call signature to be a drop-in
  once a real provider is chosen. Needs a human decision: hosted API vs.
  local model weights for PocketMiner; confirm ProteinLens's web server
  supports programmatic (non-browser) access before building that client.

## Done

- `random_baseline(n, seed=None)`, `surface_baseline(coords, cutoff=10.0)`,
  `degree_centrality(coords, cutoff=10.0)`,
  `betweenness_centrality(coords, cutoff=10.0)` — all four classical
  baselines, returning per-residue score arrays that plug into the same
  `metrics.auc`/`report.hit_list` pipeline as the main method.
- `fpocket_baseline(pdb_path, timeout=120.0)`: real subprocess wrapper
  (binary-not-found / file-not-found / nonzero-exit / timeout / missing-
  output-file / parse-failure all degrade to `{"error": ...}`, never
  raises) + `_parse_fpocket_info` (best-effort regex parse of fpocket's
  `<name>_info.txt`, tested independently against a synthetic multi-pocket
  string since the real binary isn't available here to validate against).
- `pocketminer_baseline`, `proteinlens_baseline`: honest not-yet-wired
  placeholders — see Open Questions.
- `__WORK_IN_PROGRESS__/tests/test_baselines.py`: 17 tests — hand-computed
  degree/betweenness on a synthetic 4-point chain (known path-graph
  structure), surface-baseline ordering, disconnected-graph no-crash,
  fpocket's five graceful-failure paths (all mocked, per this task's own
  Planned Validation), the info-file parser, and both not-wired
  placeholders' deterministic error returns.
- Full suite green via the now-fixed `pytest_local.py all` (see
  TASK-0026.005, filed and landed in the same pass after this task's
  "rerun the tests" step hit the interpreter-resolution gap): 343 passed
  (was 301 before TASK-0011; wip suite also picked up an unrelated
  `test_leakage_gate.py`/`test_pathways.py` from other concurrent threads
  in that count), 4 pre-existing skips.
- No changes to any other module; no API/response-shape changes.
- Claim note: TASK-0011 was claimed by "Implementer B" at 22:08 with zero
  follow-up (stub unchanged, no test file, no commit) before this thread
  force-claimed it per explicit user direction after checking for
  progress — see `claim.py status`/`sync` history in this session's
  `.ai/COMMON.md` diffs.
