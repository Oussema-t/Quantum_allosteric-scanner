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
- backend selection: `.ai/reference/BACKEND_SELECTION.md`
- claim/lock tool (TASK-0024, TASK-0027, TASK-0028, TASK-0029): `.ai/tools/claim.py` — `claim`/`release`/`status`/`sync`/`move`/`commit-guard`/`stage`, see "Current Rules" below
- command hygiene (TASK-0025): `.github/instructions/tooling/command-hygiene.instructions.md` — one command per call, no chains/pipes; `.claude/skills/command-hygiene/` is the applied procedure
- roadmap / phase-gated plan: `.ai/tasks/PLANS/PLAN.md`
- weekly timeline overlay: `.ai/tasks/PLANS/PLAN-01.07.26.md`

## Source Of Truth

| Scope | Authoritative Location | Notes |
|------|------------------------|-------|
| Stable repo-local runtime policy | `.github/` | Keep durable and short |
| Mutable scaffold coordination | `.ai/` | Active status, backlog, open questions |
| Reviewed scaffold learnings | `.ai/memory/shared/*` | Team truth for the scaffold |
| Capability contracts | `.ai/reference/CAPABILITIES.md` | Behavior-first catalog |
| Workflow backend selection | `.ai/reference/BACKEND_SELECTION.md` | Current task, test, and delegation backend defaults |
| New work touching `__WORK_IN_PROGRESS__` module code | `.ai/tasks/TASK-XXXX` | See "Task ledger boundary" below — `.claude/TASKS.md` is closed to new entries |

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
| TASK-0009 | Implement `__WORK_IN_PROGRESS__/src/allostery/diagnostics.py` | Implementer | Done | P1 | 2026-07-04 | Implementer A (this thread) | 2026-07-09 20:35 | `.ai/tasks/DONE/TASK-0009-diagnostics-py.md` |
| TASK-0010 | Implement `__WORK_IN_PROGRESS__/src/allostery/report.py` | Implementer | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0010-report-py.md` |
| TASK-0011 | Implement `__WORK_IN_PROGRESS__/src/allostery/baselines.py` | Implementer | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0011-baselines-py.md` |
| TASK-0012 | Implement `__WORK_IN_PROGRESS__/src/allostery/pathways.py` | Implementer | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0012-pathways-py.md` |
| TASK-0013 | Implement `__WORK_IN_PROGRESS__/src/allostery/coarse.py` | Implementer | TODO | P2 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0013-coarse-py.md` |
| TASK-0014 | Implement `__WORK_IN_PROGRESS__/src/allostery/viz.py` | Implementer | TODO | P3 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0014-viz-py.md` |
| TASK-0015 | Build the holo-direction module (`HOLO_DIRECTION_MODULE.md`) | Implementer | TODO | P2 (blocked on 0005/0006/0011) | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0015-holo-direction-module.md` |
| TASK-0016 | Add test for `heat()` behavior on indefinite `H_new` output (orphaned gap, see IMP-H4) | Implementer | TODO | P2 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0016-heat-indefinite-hnew-test.md` |
| TASK-0017 | Soft-lock claim column on this registry (fixes the concurrent-edit near-miss between this session and a parallel thread on TASK-0002/COMMON.md/TASK-0007) | Implementer | Done | P0 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0017-registry-claim-lock.md` |
| TASK-0018 | Reconcile `backend/` (QAS) vs `__WORK_IN_PROGRESS__/src/allostery` (CCC) architecture — granularity/design-pattern gap confirmed, wraps closed-ledger T-018/T-021 | Architect/Planner | TODO | P1 | 2026-07-05 | Architect/Planner (this thread) | 2026-07-05 08:26 | `.ai/tasks/TODO/TASK-0018-backend-vs-allostery-architecture-reconciliation.md` |
| TASK-0019 | Package accumulated `.ai`/`.claude` scaffold changes on `bartosz` into ordered, reviewable commits (Commit Packager overlay) | Commit Packager | Done | P1 | 2026-07-05 | — | — | `.ai/tasks/DONE/TASK-0019-scaffold-commit-packaging.md` |
| TASK-0020 | Product (backend/frontend) intent & feature inventory audit — endpoint/UI-control census mapped to rubric/roadmap | Architect/Planner | Done | P0 | 2026-07-04 | Intent-Inferrer (this thread) | 2026-07-04 15:10 | `.ai/tasks/DONE/TASK-0020-product-intent-inventory.md` |
| TASK-0021 | Backend API test-coverage baseline — codify `SOFTWARE.md` §9 examples as Playwright API tests | Implementer | TODO | P0 | 2026-07-04 | Intent-Inferrer (this thread) | 2026-07-04 15:10 | `.ai/tasks/TODO/TASK-0021-backend-api-test-baseline.md` |
| TASK-0022 | Frontend/UI tiered test coverage — presence / isolated functionality / intent chains / E2E process | Implementer | TODO | P0 | 2026-07-04 | Intent-Inferrer (this thread) | 2026-07-04 15:10 | `.ai/tasks/TODO/TASK-0022-frontend-ui-tiered-test-coverage.md` |
| TASK-0023 | YAGNI / scope-creep review of Product feature backlog vs. challenge rubric | General Critic | In Progress | P1 | 2026-07-04 | Intent-Inferrer (this thread) | 2026-07-04 15:10 | `.ai/tasks/IN_PROGRESS/TASK-0023-product-yagni-scope-review.md` |
| TASK-0024 | Whitelisted claim/free tool for scaffold coordination files — hardens TASK-0017 after two real collisions this session | Toolsmith | Done | P0 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0024-claim-lock-tool.md` |
| TASK-0024.001 | Extend `claim.py` to lock whole-file resources (e.g. `COMMON.md` itself), not just `TASK-XXXX` rows — filed after a risky git-checkout/restore maneuver on this file this session | Toolsmith | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0024.001-whole-file-resource-locks.md` |
| TASK-0025 | Single-command preference + reusable-script convention for all threads (widened from `.ai/`-only), delivered as a `.github/instructions/` policy doc + Claude Skill | Skills Crafter | Done | P2 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0025-command-hygiene-skill.md` |
| TASK-0026 | Recover `agents-tools/capability-runner.sh` (parent/coordinator — see subtasks below) | Toolsmith | TODO | P1 | 2026-07-04 | Skills Crafter (this thread) | 2026-07-04 16:45 | `.ai/tasks/TODO/TASK-0026-capability-runner-recovery.md` |
| TASK-0026.001 | Dispatcher entry point + `repo.vcs.*` primitives + `repo.packaging.snapshot` | Toolsmith | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0026.001-vcs-core.md` |
| TASK-0026.002 | Remaining `repo.packaging.*` + `repo.maintenance.behavior-contract-capture` + `repo.test.playwright-local` (blocked on .001) | Toolsmith | TODO | P1 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0026.002-packaging-remainder.md` |
| TASK-0026.003 | `CAPABILITIES.md` honesty pass + draft allowlist entry (blocked on .001, .002) | Toolsmith | TODO | P2 | 2026-07-04 | — | — | `.ai/tasks/TODO/TASK-0026.003-capabilities-doc-correction.md` |
| TASK-0026.004 | Named `repo.test.playwright-local` presets tied to TASK-0021/0022 + sibling `repo.test.pytest-local` — whitelisted self-verification for any thread | Toolsmith | In Progress | P1 | 2026-07-06 | Intent-Inferrer (this thread) | 2026-07-04 16:55 | `.ai/tasks/IN_PROGRESS/TASK-0026.004-test-execution-self-verification.md` |
| TASK-0027 | Whitelisted `claim.py move` subcommand for TODO/IN_PROGRESS/DONE task-file transitions — folder move + Status field + registry row as one claim-checked command | Toolsmith | Done | P1 | 2026-07-04 | — | — | `.ai/tasks/DONE/TASK-0027-task-move-tool.md` |
| TASK-0028 | Commit lock (`claim.py`-backed) serializing stage-and-ship across threads, plus an index-hygiene guard refusing unexpected staged paths before commit — filed after a real misattributed-commit incident this session | Toolsmith | Done | P0 | 2026-07-05 | — | — | `.ai/tasks/DONE/TASK-0028-commit-lock.md` |
| TASK-0029 | Scoped `claim.py stage --expect` subcommand — stages exactly the declared `.ai/`/`.claude/` paths and self-verifies, closing the loop with `commit-guard` without making the tool's blanket whitelist imply unconstrained `git add` | Toolsmith | Done | P1 | 2026-07-05 | — | — | `.ai/tasks/DONE/TASK-0029-scoped-stage-tool.md` |
| TASK-0030 | Extract a shared, unit-tested Kabsch helper in `backend/` — dedupes `discovery.py::_kabsch` / `analysis.py::_kabsch_rotate`; reuse target for TASK-0005; concrete instance of TASK-0018 evidence #6 | Implementer | Done | P2 | 2026-07-05 | — | — | `.ai/tasks/DONE/TASK-0030-backend-kabsch-dedup.md` |
| TASK-0031 | Broaden `backend/data_layer.py::fetch()`'s exception handling (only catches `HTTPError`, not `URLError`/timeout) — High finding from the `Oussema-t` commit review | Implementer | TODO | P1 | 2026-07-05 | — | — | `.ai/tasks/TODO/TASK-0031-data-layer-fetch-error-handling.md` |
| TASK-0032 | Escape RCSB-sourced strings before `innerHTML` injection in `frontend/app.js` — High finding from the `Oussema-t` commit review | Implementer | TODO | P1 | 2026-07-05 | — | — | `.ai/tasks/TODO/TASK-0032-frontend-html-escaping.md` |
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
| TASK-0047 | Bridge gaps from Reviewer A's Foundation Review (TASK-0003/0004/0005): add the missing network-gated KRAS_G12C integration test `labels.py`'s own TASK-0004 Intent Contract promised, and strengthen the numbering-offset test with a real alignment indel case | Implementer | TODO | P2 | 2026-07-07 | — | — | `.ai/tasks/TODO/TASK-0047-foundation-review-gap-bridging.md` |
| TASK-0048 | Phase 3 review (Code Reviewer overlay): `protocol.py` (TASK-0006) + `select.py` (TASK-0007), both now Done — same evidence-first method as the Foundation review; deferred to next session per user direction | Code Reviewer | TODO | P2 | 2026-07-07 | — | — | `.ai/tasks/TODO/TASK-0048-phase3-review-protocol-select.md` |

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
  (TASK-0028, workflow completed by TASK-0029).** Full sequence:
  1. `python3 .ai/tools/claim.py claim GIT-COMMIT "<your label>"` before
     the *first* `git add` of a commit-bound change, not right before
     `git commit`. If another thread holds it, `claim` refuses and names
     the holder; do not proceed, and do not pass
     `--force --reason --hitl-override` yourself — that combination
     requires an explicit human instruction in the current conversation,
     not an agent's own judgment call, unlike the advisory task-row
     override above.
  2. `python3 .ai/tools/claim.py commit-guard --expect-empty` — fail fast
     if the index isn't actually clean, before you touch it (beats
     staging first and discovering contamination after).
  3. `python3 .ai/tools/claim.py stage --expect <path> [<path> ...]` for
     any `.ai/`/`.claude/` files — stages exactly those paths and
     self-verifies. Files outside `.ai/`/`.claude/` still need a plain
     `git add`, which correctly prompts (deliberately not whitelisted —
     see TASK-0029's Intent Contract for why an unscoped stage would have
     been a whitelist-bypass in disguise).
  4. `python3 .ai/tools/claim.py commit-guard --expect <path> [<path>
     ...]` immediately before `git commit` — refuses if the staged index
     contains anything beyond what you declared, which is what would have
     caught the incident that motivated this whole rule (another thread's
     already-staged files silently riding along into an unrelated
     commit).
  5. `git commit`, then `python3 .ai/tools/claim.py release GIT-COMMIT`.

## Open Questions

- When should root-level expert briefs be introduced instead of staying reference-first?
- Which existing `agents-tools` providers should be wrapped first behind generic capability contracts?
- What should be the first post-bootstrap pilot after commit packaging?
