# .ai Common Hub

Last Updated: 2026-07-04
Status: Active

## Purpose

Central coordination hub for the repo-local agent scaffold.

## Quick Navigation

- scaffold overview: `.ai/README.md`
- architecture overview: `.ai/ARCHITECTURE_OVERVIEW.md`
- active bootstrap task: `.ai/tasks/IN_PROGRESS/TASK-0001-agent-scaffold-bootstrap.md`
- first agent bootstrap guide: `.ai/reference/FIRST_AGENT_BOOTSTRAP.md`
- second expert handoff walkthrough: `.ai/reference/SECOND_EXPERT_THREAD_WALKTHROUGH.md`
- local automation guidance: `.ai/reference/LOCAL_AUTOMATION_MANUAL_ENVIRONMENTS.md`
- capability catalog: `.ai/reference/CAPABILITIES.md`
- traceability model: `.ai/reference/TRACEABILITY_MODEL.md`
- resolution vocabulary: `.ai/reference/RESOLUTION_VOCABULARY.md`
- adoption guide: `.ai/reference/ADOPTION_GUIDE.md`
- minimum copy bundle: `.ai/reference/MINIMUM_COPY_BUNDLE.md`
- issue backend contract: `.ai/reference/ISSUE_BACKEND_PLACEHOLDER_CONTRACT.md`
- memory policy: `.ai/memory/README.md`
- addressed questions (per-role, lifecycle-foldered): `.ai/memory/questions/`
- backend selection: `.ai/reference/BACKEND_SELECTION.md`
- claim/lock tool (TASK-0024, TASK-0027, TASK-0028, TASK-0029): `.ai/tools/claim.py` — `claim`/`release`/`status`/`sync`/`move`/`commit-guard`/`stage`, see "Current Rules" below
- command hygiene (TASK-0025): `.github/instructions/tooling/command-hygiene.instructions.md` — one command per call, no chains/pipes; `.claude/skills/command-hygiene/` is the applied procedure
- roadmap / phase-gated plan: `.ai/tasks/PLANS/PLAN.md`
- weekly timeline overlay: `.ai/tasks/PLANS/PLAN-01.07.26.md`
- seam protocol (TASK-0050): `.ai/reference/SEAM_PROTOCOL.md`, registry at `.ai/seams/`
- invariance protocol (TASK-0051): `.ai/reference/INVARIANCE_PROTOCOL.md`, registry at `.ai/invariants/`

## Source Of Truth

| Scope | Authoritative Location | Notes |
|------|------------------------|-------|
| Stable repo-local runtime policy | `.github/` | Keep durable and short |
| Mutable scaffold coordination | `.ai/` | Active status, backlog, open questions |
| Reviewed scaffold learnings | `.ai/memory/shared/*` | Team truth for the scaffold |
| Capability contracts | `.ai/reference/CAPABILITIES.md` | Behavior-first catalog |
| Workflow backend selection | `.ai/reference/BACKEND_SELECTION.md` | Current task, test, and delegation backend defaults |
| New work touching `__WORK_IN_PROGRESS__` module code | `.ai/tasks/TASK-XXXX` | See "Task ledger boundary" below — `.claude/TASKS.md` is closed to new entries |
| Cross-unit invariants (boundaries between tasks/modules) | `.ai/seams/` | TASK-0050. Every seam needs a real task owner — see `.ai/seams/README.md` |
| GAUGE/KNOB/SIGNAL classification per reported quantity | `.ai/invariants/` | TASK-0051. No transformation table → not reportable — see `.ai/invariants/README.md` |

## Task Ledger Boundary

`.claude/TASKS.md` and `.ai/tasks/TODO\|IN_PROGRESS\|DONE/` are two systems
covering overlapping ground (both can describe work on
`__WORK_IN_PROGRESS__/src/allostery/`). Decision (TASK-0002, 2026-07-04):
they do **not** get merged.

- `.claude/TASKS.md` stays as the closed historical ledger for its own
  BLUE/RED/ORCH review-remediation cycle (T-001…T-021, sourced from
  `.claude/criticism/*`). Do not delete or renumber it.
- **No new `T-NNN` entries get added.** Any new work item — including work
  on the same `__WORK_IN_PROGRESS__` codebase — is filed as a
  `.ai/tasks/TASK-XXXX` file going forward (TASK-0003 already establishes
  this pattern for module-content work).
- If `.claude/TASKS.md`'s remaining `TODO`/`Blocked` rows (T-017, T-018,
  T-021) are picked up again, wrap them in a `TASK-XXXX` file that links
  back to the `T-NNN` row rather than resuming the old ledger in place.

## Active Work Registry

**Note (2026-07-04, this thread):** this table was found reverted twice in
one session — first to a pre-TASK-0017 snapshot (missing the claim
columns and every row from TASK-0003 through TASK-0019), then, mid-repair,
to a partial state missing most of TASK-0003–0019 again — even though all
of those task files exist on disk the whole time (`ls .ai/tasks/TODO
IN_PROGRESS DONE` re-checked immediately before this write). Reconstructed
directly from that file listing rather than from another prose read, to
stop chasing a moving target. TASK-0024 (new, below) builds an atomic
claim/free tool so this stops happening. **If you were mid-edit on this
table when it was overwritten, your intended change is not lost** — the
task file itself is the source of truth; re-apply your registry row from
it once you read this note, and treat concurrent whole-file writes to
this table as unsafe until TASK-0024 lands.

Before starting or resuming a row, read `Claimed By` / `Claimed At` first —
see the claim-before-start rule under "Current Rules" below.

| Task ID | Description | Assigned To | Status | Priority | Last Active | Claimed By | Claimed At | Path |
|---------|-------------|-------------|--------|----------|-------------|------------|------------|------|
| TASK-0001 | Bootstrap repo-local agent scaffold under `.github` + `.ai` | Architect/Planner | In Progress | P0 | 2026-06-25 | — | — | `.ai/tasks/IN_PROGRESS/TASK-0001-agent-scaffold-bootstrap.md` |
| TASK-0002 | AI-scaffold hygiene & engineering review (this reconciliation pass) | General Critic | Done | P0 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0002-ai-scaffold-hygiene-review.md` |
| TASK-0003 | Reconcile and author `__WORK_IN_PROGRESS__/config/targets.yaml` | Implementer | Done | P1 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0003-targets-yaml-reconciliation.md` |
| TASK-0004 | Implement `__WORK_IN_PROGRESS__/src/allostery/labels.py` | Implementer | Done | P1 | 2026-07-06 | — | — | `.ai/tasks/DONE/TASK-0004-labels-py.md` |
| TASK-0005 | Implement `__WORK_IN_PROGRESS__/src/allostery/superpose.py` | Implementer | Done | P1 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0005-superpose-py.md` |
| TASK-0006 | Implement `__WORK_IN_PROGRESS__/src/allostery/protocol.py` | Implementer | Done | P1 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0006-protocol-py.md` |
| TASK-0007 | Implement `__WORK_IN_PROGRESS__/src/allostery/select.py` | Implementer | Done | P1 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0007-select-py.md` |
| TASK-0008 | Implement `__WORK_IN_PROGRESS__/src/allostery/analysis.py` | Implementer | Done | P1 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0008-analysis-py.md` |
| TASK-0009 | Implement `__WORK_IN_PROGRESS__/src/allostery/diagnostics.py` | Implementer | Done | P1 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0009-diagnostics-py.md` |
| TASK-0010 | Implement `__WORK_IN_PROGRESS__/src/allostery/report.py` | Implementer | Done | P1 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0010-report-py.md` |
| TASK-0011 | Implement `__WORK_IN_PROGRESS__/src/allostery/baselines.py` | Implementer | Done | P1 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0011-baselines-py.md` |
| TASK-0012 | Implement `__WORK_IN_PROGRESS__/src/allostery/pathways.py` | Implementer | Done | P1 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0012-pathways-py.md` |
| TASK-0013 | Implement `__WORK_IN_PROGRESS__/src/allostery/coarse.py` | Implementer | Done | P2 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0013-coarse-py.md` |
| TASK-0014 | Implement `__WORK_IN_PROGRESS__/src/allostery/viz.py` | Implementer | Done | P3 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0014-viz-py.md` |
| TASK-0015 | Build the holo-direction module (`HOLO_DIRECTION_MODULE.md`) | Implementer | TODO | P2 (blocked on 0005/0006/0011) | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0015-holo-direction-module.md` |
| TASK-0016 | Add test for `heat()` behavior on indefinite `H_new` output (orphaned gap, see IMP-H4) | Implementer | TODO | P2 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0016-heat-indefinite-hnew-test.md` |
| TASK-0017 | Soft-lock claim column on this registry (fixes the concurrent-edit near-miss between this session and a parallel thread on TASK-0002/COMMON.md/TASK-0007) | Implementer | Done | P0 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0017-registry-claim-lock.md` |
| TASK-0018 | Reconcile `backend/` (QAS) vs `__WORK_IN_PROGRESS__/src/allostery` (CCC) architecture — granularity/design-pattern gap confirmed, wraps closed-ledger T-018/T-021 | Architect/Planner | Done | P1 | 2026-07-05 | Architect/Planner (this thread) | 2026-07-05 08:26 | `.ai/tasks/DONE/TASK-0018-backend-vs-allostery-architecture-reconciliation.md` |
| TASK-0019 | Package accumulated `.ai`/`.claude` scaffold changes on `bartosz` into ordered, reviewable commits (Commit Packager overlay) | Commit Packager | Done | P1 | 2026-07-05 | — | — | `.ai/tasks/DONE/TASK-0019-scaffold-commit-packaging.md` |
| TASK-0020 | Product (backend/frontend) intent & feature inventory audit — endpoint/UI-control census mapped to rubric/roadmap | Architect/Planner | Done | P0 | 2026-07-04 | Intent-Inferrer (this thread) | 2026-07-04 15:10 | `.ai/tasks/DONE/TASK-0020-product-intent-inventory.md` |
| TASK-0021 | Backend API test-coverage baseline — codify `SOFTWARE.md` §9 examples as Playwright API tests | Implementer | TODO | P0 | 2026-07-04 | Intent-Inferrer (this thread) | 2026-07-04 15:10 | `.ai/tasks/TODO/TASK-0021-backend-api-test-baseline.md` |
| TASK-0022 | Frontend/UI tiered test coverage — presence / isolated functionality / intent chains / E2E process | Implementer | TODO | P0 | 2026-07-04 | Intent-Inferrer (this thread) | 2026-07-04 15:10 | `.ai/tasks/TODO/TASK-0022-frontend-ui-tiered-test-coverage.md` |
| TASK-0023 | YAGNI / scope-creep review of Product feature backlog vs. challenge rubric | General Critic | In Progress | P1 | 2026-07-04 | Intent-Inferrer (this thread) | 2026-07-04 15:10 | `.ai/tasks/IN_PROGRESS/TASK-0023-product-yagni-scope-review.md` |
| TASK-0024 | Whitelisted claim/free tool for scaffold coordination files — hardens TASK-0017 after two real collisions this session | Toolsmith | Done | P0 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0024-claim-lock-tool.md` |
| TASK-0024.001 | Extend `claim.py` to lock whole-file resources (e.g. `COMMON.md` itself), not just `TASK-XXXX` rows — filed after a risky git-checkout/restore maneuver on this file this session | Toolsmith | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0024.001-whole-file-resource-locks.md` |
| TASK-0024.002 | Fix `commit-guard`/`stage`'s shared `_staged_paths()`: git's content-similarity rename detection makes a moved+edited file's `--expect` shape unpredictable (needs old+new path sometimes, only new path other times) — add `--no-renames` for deterministic always-split behavior | Toolsmith | TODO | P1 | 2026-07-09 | — | — | `.ai/tasks/TODO/TASK-0024.002-rename-detection-false-mismatch.md` |
| TASK-0025 | Single-command preference + reusable-script convention for all threads (widened from `.ai/`-only), delivered as a `.github/instructions/` policy doc + Claude Skill | Skills Crafter | Done | P2 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0025-command-hygiene-skill.md` |
| TASK-0026 | Recover `agents-tools/capability-runner.sh` (parent/coordinator — see subtasks below) | Toolsmith | TODO | P1 | 2026-07-04 | Skills Crafter (this thread) | 2026-07-04 16:45 | `.ai/tasks/TODO/TASK-0026-capability-runner-recovery.md` |
| TASK-0026.001 | Dispatcher entry point + `repo.vcs.*` primitives + `repo.packaging.snapshot` | Toolsmith | Done | P1 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0026.001-vcs-core.md` |
| TASK-0026.002 | Remaining `repo.packaging.*` + `repo.maintenance.behavior-contract-capture` + `repo.test.playwright-local` (blocked on .001) | Toolsmith | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0026.002-packaging-remainder.md` |
| TASK-0026.003 | `CAPABILITIES.md` honesty pass + draft allowlist entry (blocked on .001, .002) | Toolsmith | TODO | P2 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0026.003-capabilities-doc-correction.md` |
| TASK-0026.004 | Named `repo.test.playwright-local` presets tied to TASK-0021/0022 + sibling `repo.test.pytest-local` — whitelisted self-verification for any thread | Toolsmith | In Progress | P1 | 2026-07-06 | Intent-Inferrer (this thread) | 2026-07-04 16:55 | `.ai/tasks/IN_PROGRESS/TASK-0026.004-test-execution-self-verification.md` |
| TASK-0026.005 | `pytest_local.py` uses `sys.executable` unconditionally — fails in any environment where the wrapper's own interpreter lacks the test deps (hit directly: fresh checkout, no ambient `.venv`); resolve `.venv/bin/python3` first, fall back unchanged | Toolsmith | Done | P2 | 2026-07-09 | — | — | `.ai/tasks/DONE/TASK-0026.005-pytest-local-venv-resolution.md` |
| TASK-0027 | Whitelisted `claim.py move` subcommand for TODO/IN_PROGRESS/DONE task-file transitions — folder move + Status field + registry row as one claim-checked command | Toolsmith | Done | P1 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0027-task-move-tool.md` |
| TASK-0028 | Commit lock (`claim.py`-backed) serializing stage-and-ship across threads, plus an index-hygiene guard refusing unexpected staged paths before commit — filed after a real misattributed-commit incident this session | Toolsmith | Done | P0 | 2026-07-05 | — | — | `.ai/tasks/DONE/TASK-0028-commit-lock.md` |
| TASK-0029 | Scoped `claim.py stage --expect` subcommand — stages exactly the declared `.ai/`/`.claude/` paths and self-verifies, closing the loop with `commit-guard` without making the tool's blanket whitelist imply unconstrained `git add` | Toolsmith | Done | P1 | 2026-07-05 | — | — | `.ai/tasks/DONE/TASK-0029-scoped-stage-tool.md` |
| TASK-0030 | Extract a shared, unit-tested Kabsch helper in `backend/` — dedupes `discovery.py::_kabsch` / `analysis.py::_kabsch_rotate`; reuse target for TASK-0005; concrete instance of TASK-0018 evidence #6 | Implementer | Done | P2 | 2026-07-05 | — | — | `.ai/tasks/DONE/TASK-0030-backend-kabsch-dedup.md` |
| TASK-0031 | Broaden `backend/data_layer.py::fetch()`'s exception handling (only catches `HTTPError`, not `URLError`/timeout) — High finding from the `Oussema-t` commit review | Implementer | Done | P1 | 2026-07-12 | — | — | `.ai/tasks/DONE/TASK-0031-data-layer-fetch-error-handling.md` |
| TASK-0032 | Escape RCSB-sourced strings before `innerHTML` injection in `frontend/app.js` — High finding from the `Oussema-t` commit review | Implementer | Done | P1 | 2026-07-05 | — | — | `.ai/tasks/DONE/TASK-0032-frontend-html-escaping.md` |
| TASK-0033 | Reconcile `quantum_seed_readiness`'s hardcoded verdict thresholds vs. commit `89215bc`'s "no hardcoding" claim — Medium finding, the one clear intent/implementation mismatch found | Implementer | TODO | P2 | 2026-07-05 | — | — | `.ai/tasks/TODO/TASK-0033-seed-readiness-verdict-thresholds.md` |
| TASK-0034 | Reconcile RCSB-fetch error-handling philosophy + `data_layer.py`/`rcsb_extract.py` overlap — Medium finding, backend-internal instance of the TASK-0018 duplication pattern | Architect/Planner | TODO | P2 | 2026-07-05 | — | — | `.ai/tasks/TODO/TASK-0034-rcsb-fetch-error-philosophy-reconciliation.md` |
| TASK-0035 | Performance-audit the seed-readiness/permutation bootstrap cost (measure first, optimize only if needed) — Medium finding | Implementer | TODO | P2 | 2026-07-05 | — | — | `.ai/tasks/TODO/TASK-0035-seed-readiness-bootstrap-performance.md` |
| TASK-0036 | Surface an explicit warning when `complete_apo` skips Kabsch alignment (currently only inferable from a null `align_rmsd`) — Medium finding | Implementer | TODO | P2 | 2026-07-05 | — | — | `.ai/tasks/TODO/TASK-0036-complete-apo-alignment-warning.md` |
| TASK-0037 | `H11_anisotropic_mechanical`/`H12_anm_scalarised` don't implement the anisotropic physics their docstrings claim (both silently duplicate H6/H2) — High finding from the `Bartosz`/`bchmura` commit review | Implementer | TODO | P1 | 2026-07-05 | — | — | `.ai/tasks/TODO/TASK-0037-h11-h12-anisotropic-not-implemented.md` |
| TASK-0038 | `clean.py`'s module docstring says disconnected graphs are an error; `_assert_connected` only warns — contract mismatch | Implementer | TODO | P1 | 2026-07-05 | — | — | `.ai/tasks/TODO/TASK-0038-clean-py-connectivity-gate-contract.md` |
| TASK-0039 | `clean.py`'s alt-loc handling always keeps `'A'`, never implements the docstring's "or highest occupancy" fallback | Implementer | TODO | P2 | 2026-07-05 | — | — | `.ai/tasks/TODO/TASK-0039-clean-py-altloc-occupancy-fallback.md` |
| TASK-0040 | `potentials.py` recomputes the GNM eigendecomposition redundantly in `_gnm_msf`/`V_C`/`V_M` — no shared context, unlike `backend/analysis.py::gnm_context` | Implementer | TODO | P2 | 2026-07-05 | — | — | `.ai/tasks/TODO/TASK-0040-potentials-shared-gnm-context.md` |
| TASK-0041 | `propagators.haken_strobl` never checks `solve_ivp`'s `sol.success` flag — a failed integration would silently return as if it succeeded | Implementer | TODO | P2 | 2026-07-05 | — | — | `.ai/tasks/TODO/TASK-0041-haken-strobl-solve-ivp-success-check.md` |
| TASK-0042 | Hook-enforce the `GIT-COMMIT` gate via a Claude Code `PreToolUse` hook (upgrades TASK-0028's advisory lock to a blocking one) — filed as a handoff for Toolsmith, justified by this session's repeated real coordination incidents | Toolsmith | TODO | P1 | 2026-07-05 | — | — | `.ai/tasks/TODO/TASK-0042-hook-enforced-commit-gate.md` |
| TASK-0043 | Split `bartosz` into a `scaffold` branch (40 commits, PR-ready toward `main`) holding back the one product-code commit (TASK-0030) as its own chunk — push/PR step blocked on user credentials, not available in this sandbox | Architect/Planner | Done | P1 | 2026-07-05 | — | — | `.ai/tasks/DONE/TASK-0043-scaffold-branch-split.md` |
| TASK-0044 | Reconcile the "Python 3.9" convention (CLAUDE.md/SOFTWARE.md/AGENTS.md) against the actual 3.11.9 Render runtime and a `biotite==0.41.0` pin requiring 3.10+ — no documented rationale found for 3.9 | Architect/Planner | TODO | P2 | 2026-07-06 | — | — | `.ai/tasks/TODO/TASK-0044-python-version-convention-reconciliation.md` |
| TASK-0045 | Extend `claim.py` with an atomic `reserve-next` task-id allocator — filed after this exact task number collided with a concurrent thread's TASK-0045 (see TASK-0046), which is the live incident motivating it | Toolsmith | Done | P1 | 2026-07-07 | — | — | `.ai/tasks/DONE/TASK-0045-highest-task-lookup-tool.md` |
| TASK-0046 | Give notebook §8's coordinate-descent ceiling search a home (`ceiling.py` or `analysis.ceiling_search`) — filed after TASK-0006/0007 landed, the trigger condition TASK-0008's own Open Questions named for this (renumbered from a colliding TASK-0045 claimed concurrently by another thread) | Implementer | TODO | P1 (blocked on TASK-0008 if the analysis.py-function option is chosen) | 2026-07-07 | — | — | `.ai/tasks/TODO/TASK-0046-ceiling-coordinate-descent-search.md` |
| TASK-0047 | Bridge gaps from Reviewer A's Foundation Review (TASK-0003/0004/0005): add the missing network-gated KRAS_G12C integration test `labels.py`'s own TASK-0004 Intent Contract promised, and strengthen the numbering-offset test with a real alignment indel case | Implementer | Done | P2 | 2026-07-07 | — | — | `.ai/tasks/DONE/TASK-0047-foundation-review-gap-bridging.md` |
| TASK-0048 | Phase 3 review (Code Reviewer overlay): `protocol.py` (TASK-0006) + `select.py` (TASK-0007), both now Done — same evidence-first method as the Foundation review; deferred to next session per user direction | Code Reviewer | Done | P2 | 2026-07-07 | — | — | `.ai/tasks/DONE/TASK-0048-phase3-review-protocol-select.md` |
| TASK-0049 | Target decomposition proposal for `backend/` + `frontend/` into smaller single-concern modules (plan only, no code moved yet) — prepared ahead of a repository-standards meeting to diff against an external expert review | Architect/Planner | TODO | P1 | 2026-07-09 | Architect/Planner (this thread) | 2026-07-09 20:49 | `.ai/tasks/TODO/TASK-0049-backend-frontend-decomposition-proposal.md` |
| TASK-0050 | Adopt the Seam Protocol: `.ai/seams/` registry (5 seed records) + definition-of-done/green-bar gates + cross-link from OPERATION_PROTOCOL.md | Architect/Planner | Done | P1 | 2026-07-11 | — | — | `.ai/tasks/DONE/TASK-0050-adopt-seam-protocol.md` |
| TASK-0051 | Adopt the Invariance Protocol: `.ai/invariants/` registry seeded with `INV-0001` (real finding on `cumulative_overlap`), `SUGGESTION.md` absorbed into `pitfalls.md` | Architect/Planner | Done | P1 | 2026-07-11 | — | — | `.ai/tasks/DONE/TASK-0051-adopt-invariance-protocol.md` |
| TASK-0052 | Reconcile `test_leakage_gate.py`'s assumed `build_labels`/`FrozenConfig`/`lopo` contract against the real `labels.py`/`protocol.py` API — owns SEAM-0003 | Implementer | Done | P1 | 2026-07-11 | — | — | `.ai/tasks/DONE/TASK-0052-reconcile-leakage-gate-contract.md` |
| TASK-0053 | First seam sweep (General Critic overlay) — enumerate cross-unit invariants across TASK-0003–0012, register new `.ai/seams/` records | General Critic | Done | P2 | 2026-07-11 | — | — | `.ai/tasks/DONE/TASK-0053-first-seam-sweep.md` |
| TASK-0054 | Add the missing SE(3)-joint-rotation regression test for `cumulative_overlap`/`anm_modes` — owns INV-0001's one OPEN GAUGE row | Implementer | TODO | P2 | 2026-07-11 | — | — | `.ai/tasks/TODO/TASK-0054-se3-invariance-regression-test.md` |
| TASK-0055 | Verify `AUC_*_optimised` provenance is structurally tied to `protocol.py`'s frozen state, not just a matching label — owns SEAM-0004 | Implementer | Done | P2 | 2026-07-11 | — | — | `.ai/tasks/DONE/TASK-0055-optimised-auc-freeze-provenance-check.md` |
| TASK-0056 | Phase 4 review (Code Reviewer overlay): `diagnostics.py`/`report.py`/`baselines.py`/`pathways.py` (TASK-0009-0012), none reviewed yet — cross-checks SEAM-0004/SEAM-0005 while reading `report.py`/`baselines.py` | Code Reviewer | Done | P2 | 2026-07-11 | — | — | `.ai/tasks/DONE/TASK-0056-phase4-review-diagnostics-report-baselines-pathways.md` |
| TASK-0057 | Retroactively apply Seam/Invariance protocol to TASK-0012 (`pathways.py`): registers SEAM-0006 (owner TASK-0014) + INV-0002, writes real SE(3)/permutation invariance tests | Implementer | Done | P2 | 2026-07-11 | — | — | `.ai/tasks/DONE/TASK-0057-pathways-seam-invariance-registration.md` |
| TASK-0058 | Wire a `floor_scores` beats-floor check into `diagnostics.classify_failure` — closes SEAM-0005 (a seam-test already exists, `xfail(strict=True)` pending this task) | Implementer | Done | P2 | 2026-07-11 | — | — | `.ai/tasks/DONE/TASK-0058-wire-baseline-floor-into-classify-failure.md` |
| TASK-0059 | Wire the cumulative-overlap go/no-go gate into which targets `analysis.py` actually scores — closes SEAM-0007, found by TASK-0053's sweep | Implementer | TODO | P2 | 2026-07-11 | — | — | `.ai/tasks/TODO/TASK-0059-wire-openness-gate-into-scoring.md` |
| TASK-0060 | `claim.py question` subcommand family for the `.ai/memory/questions/` lifecycle (move between open/answered/need-action) + a `derive-task` helper reusing `reserve-next` — filed after answering Q-0001 by hand | Toolsmith | TODO | P2 | 2026-07-11 | — | — | `.ai/tasks/TODO/TASK-0060-question-lifecycle-tooling.md` |
| TASK-0061 | New `claim.py add <TASK-ID> <path> --purpose "..."` (+ manifest-file batch mode) — stages a file and appends an attributed record to the claiming task's own file, any path (not `.ai/`-scoped like `stage`) since attribution, not directory, is the safety property; commit gate unchanged | Toolsmith | TODO | P2 | 2026-07-11 | — | — | `.ai/tasks/TODO/TASK-0061-staged-files-task-audit-trail.md` |
| TASK-0062 | `.ai/memory/incidents/` registry + `.ai/tools/incident.py` — structured facts (detection/blast-radius/data-loss/recovery), not self-declared severity, so severity can be inferred consistently across incidents later | Toolsmith | TODO | P2 | 2026-07-11 | — | — | `.ai/tasks/TODO/TASK-0062-incident-reporting-registry.md` |
| TASK-0063 | `protocol.get_functional_indices` doesn't forward `labels.functional_indices`'s `heavy_atom_coords`/`heavy_atom_seq_index` — FROZEN-path callers silently forced onto the coarser Cα-only approximation, no way around the gate — TASK-0048's P2 finding | Implementer | Done | P2 | 2026-07-11 | Implementer A (this thread) | 2026-07-12 11:42 | `.ai/tasks/DONE/TASK-0063-functional-indices-gate-parameter-gap.md` |
| TASK-0064 | Wire `select.unsupervised_score` into a real FROZEN-loop consumer — closes SEAM-0009 (`analysis.py` never imports `select.py` despite both Done), found by TASK-0048's Phase 3 review, missed by TASK-0053's same-day sweep | Implementer | Done | P2 | 2026-07-11 | Reviewer B (this thread) | 2026-07-11 18:07 | `.ai/tasks/DONE/TASK-0064-wire-unsupervised-score-into-frozen-loop.md` |
| TASK-0065 | Informational FIFO queue for `GIT-COMMIT` — ticket + visible position on refusal (via `--enqueue`), no ordering enforcement; reuses `reserve-next`'s allocation logic (coordinate with TASK-0062, same generalization needed by both) | Toolsmith | TODO | P3 | 2026-07-11 | — | — | `.ai/tasks/TODO/TASK-0065-git-commit-queue.md` |
| TASK-0066 | Shared Kirchhoff-context + DCC numpy helper — dedupes `backend/analysis.py::gnm_context`/`_dcc` vs `allostery/potentials.py::_gnm_msf`/`V_R`/`V_C`/`V_M`'s independently re-derived pseudo-inverse math (TASK-0030-style port, not import); filed by TASK-0018's decision doc | Implementer | TODO | P2 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0066-shared-kirchhoff-dcc-helper.md` |
| TASK-0067 | Run the T-018 (GNM cutoff 7.5/8.0/10.0 Å) and T-021 (5 contact-weight schemes) benchmark against `config/targets.yaml` — resolves the three-way cutoff divergence TASK-0018's decision doc found, wraps closed-ledger T-018/T-021 | Implementer | Done | P1 | 2026-07-12 | — | — | `.ai/tasks/DONE/TASK-0067-gnm-cutoff-weight-scheme-benchmark.md` |
| TASK-0068 | NISQ noise-model simulation (depolarizing + amplitude-damping Trotterized sim, top-5 degradation vs depth/error) consuming `coarse.py`'s output — owns SEAM-0010, filed per TASK-0013's own Open Question once `coarse.py` landed | Implementer | TODO | P2 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0068-nisq-noise-model-simulation.md` |
| TASK-0069 | `pytest_local.py`'s `wip-*` presets resolve the wrong venv (top-level `.venv`, not `__WORK_IN_PROGRESS__/.venv`) now that a root venv exists — found live while TASK-0014 needed `matplotlib`, installed in the WIP venv only | Toolsmith | TODO | P1 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0069-pytest-local-wip-venv-resolution-regression.md` |
| TASK-0070 | Pocket label exclusion assembly — assemble `pocket & ~functional & ~terminal` (`build_labels`), assert `pocket ∩ active_site == ∅`, record the KRAS Cys12 in/out decision — filed from `EXECUTION_PLAN.md` Phase 0.1, the oldest live defect (no seam-owner) | Implementer | Done | P0 | 2026-07-12 | — | — | `.ai/tasks/DONE/TASK-0070-pocket-label-exclusion-assembly.md` |
| TASK-0071 | Permutation-null leak detector in `diagnostics.py` — shuffle labels, re-run, flag anything still scoring above chance, backstopping the DEV/FROZEN firewall's prevention with real-time detection — `EXECUTION_PLAN.md` Phase 1.4 | Implementer | Done | P1 | 2026-07-12 | — | — | `.ai/tasks/DONE/TASK-0071-permutation-null-leak-detector.md` |
| TASK-0072 | Golden-value cross-tree drift test — fix a reference structure, assert `backend/`/`allostery/` produce numerically identical shared-primitive output, the anti-drift mechanism TASK-0066 needs — `EXECUTION_PLAN.md` Phase 2.3 | Implementer | TODO | P2 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0072-golden-value-cross-tree-drift-test.md` |
| TASK-0073 | Register cross-tree seams — `.ai/seams/` records (owner + seam-test) for the shared Kirchhoff/DCC primitive and the GNM cutoff constant — `EXECUTION_PLAN.md` Phase 2.5 | Implementer | TODO | P2 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0073-register-cross-tree-seams.md` |
| TASK-0074 | Characterization tests for `backend/analysis.py` (`gnm_context`/`site_potentials`/`quantum_seed_readiness`/`connectivity_change`) pinning current live output before any convergence touches it — hard-rule prerequisite for TASK-0066/0072 per `EXECUTION_PLAN.md` Phase 4.2 | Implementer | TODO | P1 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0074-backend-analysis-characterization-tests.md` |
| TASK-0075 | Knob-spread reporting for the cumulative-overlap gate — sweep cutoff × variant × k × reference, return `UNSTABLE` when knobs (not physics) decide go/no-go (18-combo toy case swung 0.067–0.860, flipped 15/18) — `EXECUTION_PLAN.md` Phase 5.5, ties to INV-0001 | Implementer | TODO | P1 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0075-knob-spread-overlap-gate-reporting.md` |
| TASK-0076 | WIP graduation part 1: `git mv __WORK_IN_PROGRESS__/src/allostery → allostery/` at repo top level, update imports/test paths, behaviour-neutral (252-green before/after) — `EXECUTION_PLAN.md` Phase 3.1 | Implementer | TODO | P2 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0076-graduation-part1-promote-package.md` |
| TASK-0077 | WIP graduation part 2: single CI workflow running `backend/` + `allostery/` suites together, ending the two-test-worlds split — `EXECUTION_PLAN.md` Phase 3.2, depends on TASK-0076 | Implementer | TODO | P2 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0077-graduation-part2-one-ci.md` |
| TASK-0078 | WIP graduation part 3: move remaining `__WORK_IN_PROGRESS__` contents to permanent homes (`config/`, `notebooks/`, `documentation/`), delete the folder — `EXECUTION_PLAN.md` Phase 3.3, depends on TASK-0076/0077 | Implementer | TODO | P2 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0078-graduation-part3-dissolve-folder.md` |
| TASK-0079 | End-to-end challenge run (parent, thin coordinator — split into .001-.005 subtasks 2026-07-12) — one command producing the N×N connectivity matrix, top-5 hit list, and methodological report per mandatory target (KRAS_G12C, BCR_ABL1, CARDIAC_MYOSIN; MYC_MAX is TASK-0080) — `EXECUTION_PLAN.md` Phase 5.1, critical-path link | Implementer | TODO | P0 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0079-end-to-end-challenge-run.md` |
| TASK-0079.001 | Schema assembly: `analysis.py` real nested output -> `report.py`'s flat results dict — closes SEAM-0008 | Implementer | Done | P0 | 2026-07-12 | Implementer A (this thread) | 2026-07-12 17:21 | `.ai/tasks/DONE/TASK-0079.001-analysis-report-schema-assembly.md` |
| TASK-0079.002 | Connectivity matrix (`pathways.edge_propensity` half-matrix -> dense N×N array) + hit-list assembly (`report.hit_list`) | Implementer | Done | P0 | 2026-07-12 | — | — | `.ai/tasks/DONE/TASK-0079.002-connectivity-matrix-hit-list-assembly.md` |
| TASK-0079.003 | FROZEN-gated per-target verdict pipeline — `select_frozen_config` -> `analysis.py` scoring -> `stamp_provenance` -> .001's assembly, all inside one `frozen_context` | Implementer | Done | P0 | 2026-07-12 | Implementer A (this thread) | 2026-07-12 19:01 | `.ai/tasks/DONE/TASK-0079.003-frozen-gated-verdict-pipeline.md` |
| TASK-0079.004 | One-command orchestrator (`run_challenge.py --target ...`) + output files — depends on .002, .003 | Implementer | Done | P0 | 2026-07-12 | Implementer A (this thread) | 2026-07-12 20:19 | `.ai/tasks/DONE/TASK-0079.004-one-command-orchestrator.md` |
| TASK-0079.005 | Run end-to-end for KRAS_G12C / BCR_ABL1 / CARDIAC_MYOSIN (live network) + manual inspection against Acceptance Scenarios — depends on .004 | Implementer | TODO | P0 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0079.005-run-mandatory-targets.md` |
| TASK-0080 | c-Myc/1NKP application — no holo ground truth, route to consensus + theoretical docking viability reporting instead of AUC/ceiling — `EXECUTION_PLAN.md` Phase 5.7 | Implementer | TODO | P2 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0080-cmyc-1nkp-application.md` |
| TASK-0081 | Generalization set — run the frozen pipeline on 2–4 extra Allosteric-Database targets to evidence robustness/scalability, encouraged (not required) by the brief — `EXECUTION_PLAN.md` Phase 5.8, depends on TASK-0079 | Implementer | TODO | P2 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0081-generalization-set-asd-targets.md` |
| TASK-0082 | Competence map synthesis — per-target floor/ceiling/headroom table, the submission's central "honest NO is a publishable result" claim — `EXECUTION_PLAN.md` Phase 5.2, critical-path link | Implementer | TODO | P0 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0082-competence-map-synthesis.md` |
| TASK-0083 | Result artifact contract ⚠️ decide EARLY — versioned NPZ/JSON artifact `allostery` emits and `backend` consumes (connectivity matrix, ranked hits, verdict+knob-spread, floor/ceiling/headroom, frozen-config hash) so `backend` never recomputes science in the request path — `EXECUTION_PLAN.md` Phase 6.1, critical-path link, keystone decision | Architect/Planner | TODO | P0 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0083-result-artifact-contract.md` |
| TASK-0084 | Backend results API — ADD-only endpoints (`/api/results/{target}`, `/api/connectivity/{target}`, `/api/verdict/{target}`) serving precomputed artifacts, no science in the request path — `EXECUTION_PLAN.md` Phase 6.2, depends on TASK-0083 | Implementer | TODO | P2 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0084-backend-results-api.md` |
| TASK-0085 | Frontend research visualization — top-5 pockets on 3Dmol, N×N connectivity heatmap, floor/method/ceiling competence panel, explicit `UNSTABLE` state — the scored interpretability objective — `EXECUTION_PLAN.md` Phase 6.3, depends on TASK-0084 | Implementer | TODO | P2 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0085-frontend-research-visualization.md` |
| TASK-0086 | Execution/trigger path — decide + implement offline-batch (preferred) vs async-job-queue run triggering so artifacts are producible without heavy compute in the web request path — `EXECUTION_PLAN.md` Phase 6.4, depends on TASK-0083 | Architect/Planner | TODO | P1 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0086-execution-trigger-path.md` |
| TASK-0087 | Harden `protocol.py`'s firewall from a cooperative gate (bypassable by calling `labels.py`/`superpose.py` directly) to a hard data-seal matching `test_leakage_gate.py`'s `_SealedLabels` reference spec, or explicitly document the weaker guarantee as an accepted trust boundary — real gap found verifying equivalence for TASK-0052 | Implementer | TODO | P1 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0087-harden-protocol-firewall-to-data-seal.md` |
| TASK-0088 | Structurally gate `provenance="frozen"` in `report.verdict_template` against `protocol.py`'s frozen-config state machine (e.g. a `stamp_provenance()` helper only callable from inside `frozen_context`) — closes SEAM-0004, real gap found by TASK-0055 | Implementer | Done | P1 | 2026-07-12 | — | — | `.ai/tasks/DONE/TASK-0088-structurally-gate-frozen-provenance.md` |
| TASK-0089 | Classify `select.py`'s reported quantities (GAUGE/KNOB/SIGNAL) — closes `INV-0004`, flagged by TASK-0064 | Implementer | TODO | P2 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0089-select-invariance-classification.md` |
| TASK-0091 | Run a calibrated (not blind) `dephasing_sweep` on BCR_ABL1's real winning `H_new` — CTQW scores 0.525 (chance) but classical heat on the *same operator* scores 0.731; determine whether calibrated decoherence recovers the signal (adapt) or it stays flat (abandon), reusing the KRAS_G12C calibration precedent exactly — real finding from TASK-0079.005 | Implementer | TODO | P1 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0091-bcr-abl1-dephasing-sweep-investigation.md` |
| TASK-0092 | Wire `run_frozen_verdict`'s already-supported holo kwargs into the real end-to-end run (`AUC_holo_Hnew_optimised`/`mean_rho_apo_holo`/`mean_jacc20` are `N/A` in both real reports) — a diagnostic upper bound, not a prediction substitute; extends TASK-0067's own apo-vs-holo finding (tiny gap, bare operator) to the full `H_new` pipeline — real gap from TASK-0079.005 | Implementer | TODO | P2 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0092-holo-diagnostic-comparison-real-run.md` |
| TASK-0093 | Reconcile KRAS_G12C's real end-to-end AUC (0.779) against this repo's own previously-asserted near-chance band (0.3-0.7, `test_analysis.py`) for the same target — factorial isolation of cutoff (8.0 vs 10.0 Å) / pocket-label definition (assembled vs raw) / source definition (apo- vs holo-derived) — real discrepancy from TASK-0079.005 | Implementer | TODO | P1 | 2026-07-12 | — | — | `.ai/tasks/TODO/TASK-0093-kras-auc-discrepancy-reconciliation.md` |

## Current Rules

- Additive bootstrap only. Do not rewrite `.claude` broadly in this phase.
- Stable policy belongs in `.github/`.
- Live execution belongs in `.ai/tasks/`.
- Named capabilities belong in `.ai/reference/CAPABILITIES.md`.
- Durable scaffold learnings belong in `.ai/memory/shared/*` after review.
- Whoever creates or moves a `TASK-XXXX` file must update this registry in
  the same edit — it must not silently drift out of sync (see Task Ledger
  Boundary above for the `.claude/TASKS.md` split).
- **Claim before you start (TASK-0017, hardened by TASK-0024).** Before
  starting or resuming work on a registry row — or editing this registry
  itself, the single most contended file in the scaffold — run
  `python3 .ai/tools/claim.py claim <TASK-ID> "<your label>"` first. This is
  an atomic, whitelisted local operation (an `O_EXCL`-created lock file
  under `.ai/tasks/.locks/`), not a hand-edit of this table's `Claimed By` /
  `Claimed At` cells — **do not hand-edit those two cells anymore**; run
  `python3 .ai/tools/claim.py sync` to regenerate them from the lock files
  (everything else in a row — Description/Assigned To/Status/Priority/Last
  Active/Path — is still hand-maintained exactly as before). If the row is
  already claimed, `claim` fails loudly and prints the current holder:
  either pick a different unclaimed task, or override with
  `--force --reason TEXT` if you judge the claim stale (see below) — the
  reason is recorded in the lock file for audit. Free-text claim labels are
  still fine (e.g. "Implementer (this thread)").
- **Staleness override (TASK-0017).** A claim with no corresponding file
  activity (check the task file's own mtime / `git log -- <path>`) for
  longer than one working session is stale and may be taken over via
  `claim.py claim <TASK-ID> "<label>" --force --reason "..."`. No numeric
  TTL is enforced — a human or agent reading the table makes the call, same
  as everything else in this scaffold.
- **This table's claim columns are no longer edited by hand (TASK-0024).**
  `.ai/tools/claim.py sync` is the only writer of `Claimed By` /
  `Claimed At` — it reads lock files and rewrites only those two cells per
  row, serialized through a short-lived `.ai/COMMON.md.synclock` file, so
  concurrent `sync` runs can't clobber each other's claim data. Two such
  whole-table collisions happened in one session before this landed.
  Adding, removing, or reordering *rows* (new tasks, moved tasks) is still a
  manual edit with the original whole-file-write risk — `ls .ai/tasks/TODO
  IN_PROGRESS DONE` immediately before such an edit and reconcile against
  that, not against a prose read that may already be stale.
- **Moving a task file between folders is no longer a manual `mv` + two
  hand-edits (TASK-0027).** Run `python3 .ai/tools/claim.py move <TASK-ID>
  <TODO|IN_PROGRESS|DONE> --as "<your label>"` — it relocates the file,
  rewrites its own `- Status:` line, and updates this registry's `Status`/
  `Path` cells for that row, together. Refuses on a claim mismatch the same
  way `claim` does (`--force --reason TEXT` to override); moving to `DONE`
  auto-releases the claim by default (`--keep-claim` to opt out). `--as` is
  always required.
- **Claim `GIT-COMMIT` before staging anything you intend to commit
  (TASK-0028, workflow completed by TASK-0029) — but the claim alone is
  advisory, not enforced; `commit-guard` is the real safety net (see
  `.ai/memory/questions/toolsmith/answered/Q-0001-*.md` for a real
  incident where a non-honoring thread's `git add` landed in another
  thread's staged index despite the lock being held; hardening this into
  an actually-blocking hook is TASK-0042, TODO).** Full sequence:
  1. `python3 .ai/tools/claim.py claim GIT-COMMIT "<your label>"` before
     the *first* `git add` of a commit-bound change, not right before
     `git commit`. If another thread holds it, `claim` refuses and names
     the holder; do not proceed, and do not pass
     `--force --reason --hitl-override` yourself — that combination
     requires an explicit human instruction in the current conversation,
     not an agent's own judgment call, unlike the advisory task-row
     override above. **Holding this claim does not stop a thread that
     never checks it** — treat it as a courtesy signal other cooperating
     threads read, not a lock the filesystem enforces.
  2. `python3 .ai/tools/claim.py commit-guard --expect-empty` — fail fast
     if the index isn't actually clean, before you touch it (beats
     staging first and discovering contamination after).
  3. `python3 .ai/tools/claim.py stage --expect <path> [<path> ...]` for
     any `.ai/`/`.claude/` files — stages exactly those paths and
     self-verifies. Files outside `.ai/`/`.claude/` still need a plain
     `git add`, which correctly prompts (deliberately not whitelisted —
     see TASK-0029's Intent Contract for why an unscoped stage would have
     been a whitelist-bypass in disguise).
  4. **`python3 .ai/tools/claim.py commit-guard --expect <path> [<path>
     ...]` immediately before `git commit` — every time, even if no time
     seems to have passed since step 2/3.** This is the check that
     actually catches contamination; step 1's claim is not a substitute
     for it. Refuses if the staged index contains anything beyond what
     you declared.
  5. `git commit`, then `python3 .ai/tools/claim.py release GIT-COMMIT`.
- **Seam gate (TASK-0050).** A task may not move to `DONE` if it opens a
  seam (its output is consumed by another unit, or it splits a
  responsibility a previous unit held whole) without a corresponding
  `.ai/seams/SEAM-XXXX` record with a named owner and seam-test (may be
  `xfail` while `OPEN`). The repo is not green if any `OPEN` seam has no
  seam-test at all; `WAIVED` requires a reason and expiry. See
  `.ai/seams/README.md`.
- **Invariance gate (TASK-0051).** Before a quantity is reported, its
  GAUGE/KNOB/SIGNAL transformation table must exist in `.ai/invariants/`
  — no table, not reportable. "Invariant on our test set" is a trigger to
  widen the transformation group, not a green light — see
  `.ai/invariants/README.md` and [[pitfalls#P-0001]].

## Open Questions

- When should root-level expert briefs be introduced instead of staying reference-first?
- Which existing `agents-tools` providers should be wrapped first behind generic capability contracts?
- What should be the first post-bootstrap pilot after commit packaging?
