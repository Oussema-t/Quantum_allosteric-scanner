# Capability Catalog

This file tracks reusable capabilities independently of the provider that implements them.

Capabilities should be slash-command-friendly when they are likely to become user-facing entry points.
That means small explicit inputs, bounded scope, predictable output, and no hidden script assumptions.

Provider order:

1. MCP or tool server
2. repo-local script or wrapper
3. manual fallback

In heavily manual customer environments, repo-local wrappers that produce local artifacts or read-only output are usually the first safe automation step before any backend-integrated provider.

## Commit Packager Capability Set

| Capability | Purpose | Current Provider | Scope | Safety | Notes |
|------------|---------|------------------|-------|--------|-------|
| `repo.vcs.current-branch` | Read the current branch name | `agents-tools/capability-runner.sh repo.packaging.snapshot` (field: `branch`) | generic | read-only | Surfaced through the snapshot composite output. |
| `repo.vcs.short-status` | Read short working-tree status | `agents-tools/capability-runner.sh repo.packaging.snapshot --include-working-tree` | generic | read-only | Optional context only; commit packaging remains staged-first. |
| `repo.vcs.staged-diff-stat` | Summarize staged diff size | `agents-tools/capability-runner.sh repo.packaging.snapshot` (field: `staged.diffStat`) | generic | read-only | Deterministic and machine-readable with `--json`. |
| `repo.vcs.staged-files` | List staged file paths | `agents-tools/capability-runner.sh repo.vcs.staged-files` | generic | read-only | Supports deterministic sorted output and `--json`. |
| `repo.vcs.changed-files` | List complete changed-file set from one call | `agents-tools/capability-runner.sh repo.vcs.changed-files` | generic | read-only | Supports `--scope all|staged` and `--json`; intended as the single-source input for AI-authored split planning. |
| `repo.packaging.classify-staged-files` | Bucket staged files into packaging groups | `agents-tools/capability-runner.sh repo.packaging.classify-staged-files` | reusable with config extraction | read-only | Supports deterministic sorted output and `--json`. |
| `repo.packaging.snapshot` | Summarize staged change packaging state for branch planning | `agents-tools/capability-runner.sh repo.packaging.snapshot` | reusable with wrapper | read-only | Composite capability over `repo.vcs.*` and packaging classification calls, with `--json`. |
| `repo.packaging.branch-file-list` | List staged files for a packaging target | `agents-tools/capability-runner.sh repo.packaging.branch-file-list <target>` | reusable with wrapper | read-only | Targets are `maintenance` and `cluster`; supports `--json`. |
| `repo.packaging.plan-next-commit` | Prepare next commit from persisted split plan | `agents-tools/capability-runner.sh repo.packaging.plan-next-commit` | reusable with wrapper | write (scoped) | Stages next group, writes commit-message draft, and marks group done in state when `--apply` is used. |
| `repo.packaging.validate-plan-coverage` | Validate plan coverage against changed-files source | `agents-tools/capability-runner.sh repo.packaging.validate-plan-coverage` | reusable with wrapper | read-only | Stable wrapper for changedCount/groupCount/plannedCount/missing/extra/ambiguous metrics; supports `--json` and optional `--strict`. |
| `repo.packaging.refine-plan` | Move an area path prefix into a dedicated plan group | `agents-tools/capability-runner.sh repo.packaging.refine-plan` | reusable with wrapper | write (scoped) | Supports `--path-prefix`, destination group metadata, optional deferred target branch, and JSON output. |
| `repo.packaging.review-plan-rules` | Review plan quality gates before execution | `agents-tools/capability-runner.sh repo.packaging.review-plan-rules` | reusable with wrapper | read-only | Reports coverage, area-cohesion conflicts, commit-size floor issues, and ambiguous-file status in JSON. |
| `repo.packaging.cleanup-plan` | Cleanup stale split-plan artifacts and commit-message drafts | `agents-tools/capability-runner.sh repo.packaging.cleanup-plan` | reusable with wrapper | write (scoped) | Safe dry-run by default; supports scoped archive or delete actions over plan/state/source/drafts. |
| `repo.packaging.mr-big-picture` | Generate a big-picture merge-request summary from plan/state | `agents-tools/capability-runner.sh repo.packaging.mr-big-picture` | reusable with wrapper | write (scoped) | Writes markdown summary file (default `.ai/tasks/mr-big-picture.md`) with done/deferred group scope and supports `--json`. |
| `repo.maintenance.behavior-contract-capture` | Capture scoped UI behavior contract artifacts for maintenance slices | `agents-tools/capability-runner.sh repo.maintenance.behavior-contract-capture` | reusable with wrapper | write (scoped) | Writes contract artifact under `.ai/tasks/contracts/` with Behavior Contract, Probe Matrix, and Fast-Fail Budgets; supports extraction from a task file and `--json`. |
| `repo.test.playwright-local` | Execute local Playwright TC runs through a stable wrapper | `agents-tools/capability-runner.sh repo.test.playwright-local` | playwright local test data | environment-dependent | Wrapper pins Playwright working directory and runtime env (`TS_NODE_PROJECT`, `NODE_OPTIONS`), supports explicit CLI spec/project/grep inputs, and supports strict-allowlist request-file mode via `.ai/tasks/playwright-local-run.request.json`. **Not yet real** — `agents-tools/` does not exist in this repo (TASK-0026 recovery still TODO), and no Playwright config/test files exist yet (TASK-0021/0022 haven't landed). Treat this row as a forward spec, not a callable capability today. |
| `repo.test.pytest-local` | Execute local pytest presets through a stable, whitelisted wrapper — no free-form pytest flags | `.ai/tools/pytest_local.py <preset> [--json]` | repo-local, `__WORK_IN_PROGRESS__/tests/` + `backend/test_geometry.py` only | environment-dependent (runs local pytest, never Render) | TASK-0026.004. Stdlib-only wrapper; presets are the whitelist surface (`wip-labels`, `wip-hamiltonians`, `wip-physics`, `wip-potentials`, `wip-all`, `backend`, `all`; `--list` prints the current set). Sets `PYTHONPATH` to `__WORK_IN_PROGRESS__/src` for `wip-*`/`all` presets since that package has no editable install; `backend` needs none. Invalid preset names are rejected by `argparse` before anything runs. `--json` emits `{preset, cmd, returncode, passed, stdout_tail, stderr_tail}` for machine-readable pass/fail. Deliberately lives under `.ai/tools/` (alongside `claim.py`) rather than `agents-tools/`, since that directory doesn't exist yet and this wrapper doesn't depend on its recovery. |

## Other Seeded Capabilities

| Capability | Purpose | Current Provider | Scope | Safety | Notes |
|------------|---------|------------------|-------|--------|-------|
| `workflow.task.create` | Create a task in the active task backend | manual fallback | generic with backend adapter | write | Backend may be on-disk task files, JIRA, or another HITL-selected system. |
| `workflow.task.update` | Update task status, content, or metadata in the active task backend | manual fallback | generic with backend adapter | write | Requires a stable task identifier and backend contract. |
| `workflow.task.perform` | Perform one selected TODO item from a task and synchronize task progress artifacts | prompt or agent orchestration | scaffold-specific with backend adapter | write | Requires `.ai/tasks/TASK-*.md` input and bounded single-item execution per run. |
| `workflow.task.assign` | Delegate or assign a task to a person, role, or agent | manual fallback | generic with backend adapter | write | Backend may support human assignees, role tags, or agent overlays differently. |
| `workflow.task.claim` | Atomically claim a task row so concurrent threads don't collide on it | `.ai/tools/claim.py claim <TASK-ID> <claimant>` | repo-local, on-disk task backend only | write (scoped) | TASK-0024. Creates `.ai/tasks/.locks/<TASK-ID>.lock` via an `O_EXCL` atomic open; fails loudly if already claimed unless `--force --reason TEXT`. Replaces hand-editing the `Claimed By`/`Claimed At` cells in `.ai/COMMON.md` directly. |
| `workflow.task.reserve-next` | Atomically hand back the next unused `TASK-XXXX` id — no read-then-write race when filing a new task | `.ai/tools/claim.py reserve-next --as <claimant>` | repo-local, on-disk task backend only | write (scoped) | TASK-0045. Filed after two threads independently computed "the highest task number" from a snapshot and both filed `TASK-0045` at the same time — a plain read (`find`/`ls`/a prior `CAPABILITIES.md`/`COMMON.md` read) has no lock between the read and the write. This takes `max(highest on-disk task file, highest currently-locked id) + 1` as a candidate and claims it via the same `O_EXCL` primitive as `claim`, retrying upward on a lost race. The returned id is already claimed under the given label (no separate `claim` call needed) — the caller still creates the task `.md` file and `COMMON.md` registry row manually. `--dry-run` previews the candidate without claiming (can go stale — informational only). `--quiet` prints only the bare id, for `$(...)` capture without a pipe. Validated against a 5-way concurrent-call race: all 5 returned distinct ids. |
| `workflow.task.release` | Release a task's claim | `.ai/tools/claim.py release <TASK-ID>` | repo-local, on-disk task backend only | write (scoped) | TASK-0024. Idempotent — a no-op if already unclaimed. `--claimant` checks expected holder (warns on mismatch, `--strict` to fail instead). |
| `workflow.task.claim-status` | Read current claim(s) without mutating anything | `.ai/tools/claim.py status [TASK-ID]` | repo-local, on-disk task backend only | read-only | TASK-0024. Single task or full listing. The full listing (no `TASK-ID` given) flags dangling locks (a lock with no corresponding task file on disk); single-task mode does not check this. |
| `workflow.registry.sync` | Regenerate the `Claimed By`/`Claimed At` cells of `.ai/COMMON.md`'s Active Work Registry from lock files | `.ai/tools/claim.py sync` | repo-local, `.ai/COMMON.md` only | write (scoped) | TASK-0024. Touches only those two columns per row — Description/Assigned To/Status/Priority/Last Active/Path stay hand-maintained. Supports `--dry-run` and `--check` (exit 1 if out of sync, no write); also warns (stderr) about task files on disk with no registry row and rows with no task file, without attempting to fix either. Serializes concurrent writers via a short-lived `.ai/COMMON.md.synclock` file. |
| `workflow.task.move` | Move a task file between TODO/IN_PROGRESS/DONE, syncing its own `- Status:` line and its `.ai/COMMON.md` registry row's `Status`/`Path` cells, in one command | `.ai/tools/claim.py move <TASK-ID> <TODO\|IN_PROGRESS\|DONE> --as <label>` | repo-local, on-disk task backend + `.ai/COMMON.md` | write (scoped) | TASK-0027. `--as` is always required. Refuses on a claim mismatch the same way `claim` does (`--force --reason TEXT` to override); if unclaimed, warns and proceeds — same advisory philosophy as `claim`. Moving to `DONE` auto-releases the claim by default (`--keep-claim` to opt out). Idempotent: a no-op if the file's folder, its `Status` line, and the registry row all already match. Refuses (without corrupting anything) if zero or more than one on-disk file matches the task id, or if another thread's concurrent move already relocated the file first. |
| `repo.commit.lock` | Serialize the `git add` → `git commit` critical section across threads | `.ai/tools/claim.py claim GIT-COMMIT <claimant>` / `.ai/tools/claim.py release GIT-COMMIT` | repo-local, one global lock | write (scoped) | TASK-0028. `GIT-COMMIT` is a fixed, non-`TASK-XXXX` resource id accepted by the same `claim`/`release`/`status` commands (not general arbitrary-resource support — see TASK-0024.001 for that broader mechanism). Claim it before the *first* `git add` intended for a commit, not right before `git commit` — the incident this hardens was two threads' staging windows overlapping, not two simultaneous commit calls. Overriding a held `GIT-COMMIT` claim requires `--force --reason TEXT` **and** `--hitl-override` — stricter than a normal task claim, since committing is a harder-to-reverse, shared-history action; do not pass `--hitl-override` without an explicit human instruction in the current conversation. |
| `repo.commit.guard` | Refuse to proceed unless the currently staged git index exactly matches an explicit expected path set | `.ai/tools/claim.py commit-guard --expect PATH [PATH ...]` | repo-local, reads `git diff --cached` only | read-only | TASK-0028. Complements `repo.commit.lock` — catches the actual incident that motivated both (stale content another thread had already staged, not a live race): run this immediately before `git commit` regardless of whether the lock was held. Exits non-zero and lists the extra paths if the index has more staged than `--expect`; also exits non-zero and lists them if `--expect` names paths that aren't actually staged. Never stages or unstages anything itself. `--expect-empty` (TASK-0029) is the mutually-exclusive fail-fast form: assert nothing is staged yet, *before* your first `git add`, instead of adding then discovering contamination and having to `git reset HEAD --` to undo it. |
| `repo.commit.stage` | `git add` exactly a declared path set, restricted to `.ai/`/`.claude/`, self-verifying immediately after | `.ai/tools/claim.py stage --expect PATH [PATH ...]` | repo-local, `.ai/` and `.claude/` only | write (scoped) | TASK-0029. Refuses (before staging anything) if any `--expect` path normalizes outside `.ai/`/`.claude/` (path-traversal-safe — checks the normalized path, so `.ai/../backend/x` is caught, not silently allowed) or doesn't exist on disk; anything outside that scope needs a plain `git add`, which correctly prompts. This scope restriction is load-bearing: `claim.py`'s own invocation is already blanket-whitelisted in `.claude/settings.json` (per subcommand, see TASK-0029's Reviewer-driven revision — no longer one broad wildcard), so an unscoped `stage` would have made that whitelist silently imply unconstrained `git add` of any repo path. Self-verifies with the same comparison `commit-guard` uses (shared helper, not re-derived) after staging. Full recommended workflow: `claim GIT-COMMIT` → `commit-guard --expect-empty` → `stage --expect ...` → `commit-guard --expect ...` → `git commit` → `release GIT-COMMIT`. |
| `workflow.task.locate` | Report a task's claim status and on-disk lifecycle-folder location in one call | `.ai/tools/task_locate.py <TASK-ID>` | repo-local, on-disk task backend only | read-only | TASK-0025. Worked-example command-hygiene fix: replaces the reproduced `claim.py status && echo ... && find ... && echo ... && ls ...` incident (see the callout below) with one whitelisted call. Imports `claim.py`'s own lock-reading/disk-scan functions directly (same directory) rather than re-deriving or shelling out to it. Accepts plain or dotted-subtask ids, same as `claim.py`. |
| `workflow.task.resolve` | Resolve a task with an explicit backend-relevant resolution value | manual fallback | generic with backend adapter | write | Distinct from deletion; backend adapters should map the resolution field correctly. |
| `workflow.task.promote` | Promote reusable outcomes from a TASK file into review and contract artifacts | prompt or agent orchestration | scaffold-specific with backend adapter | write (scoped) | Supports retrieval-first updates of `.ai/tasks/contracts/*` and `.ai/reviews/*` artifacts from resolved-task sections such as UI intent baselines and architecture findings. |
| `workflow.task.delete` | Permanently delete a task from the active task backend | manual fallback | generic with backend adapter | destructive | Do not overload with close, archive, or resolve semantics. |
| `workflow.testcase.create` | Create a test case in the active test-case system | manual fallback | generic with backend adapter | write | Backend may be markdown, TestRail, Jira/Xray, or another HITL-selected system. |
| `workflow.testcase.update` | Update test-case content, mapping, or status | manual fallback | generic with backend adapter | write | Exact fields depend on the selected test-case backend. |
| `workflow.testcase.link` | Link a test case to code, intent, workflow, or execution artifacts | manual fallback | generic with backend adapter | write | Important for intent-to-test traceability. |
| `workflow.teststep.create` | Create a managed test step under a test case in the active test-management system | manual fallback | generic with backend adapter | write | Test steps are management artifacts, not automation code. |
| `workflow.teststep.update` | Update managed test-step content or ordering | manual fallback | generic with backend adapter | write | Exact step fields depend on the selected backend. |
| `workflow.teststep.delete` | Permanently delete a managed test step from the active test-management system | manual fallback | generic with backend adapter | destructive | Keep step deletion distinct from testcase lifecycle changes. |
| `workflow.testcode.plan` | Derive or refine automated test implementation from intent and test-management artifacts | prompt or agent orchestration | scaffold-specific | control-plane | Test code belongs to the automation layer, not the test-management backend. |
| `workflow.testcode.update` | Create or modify automated test code in the repository | prompt or agent orchestration | scaffold-specific | write | Distinct from testcase and teststep operations. |
| `workflow.testcode.link` | Link automated test code to intent, testcase, teststep, or execution artifacts | manual fallback | generic with backend adapter | write | Supports traceability across management and automation layers. |
| `workflow.testexecution.run` | Execute selected automated test code locally or on an explicit project-specific backend | `runTests` for local execution | scaffold-specific with backend adapter | environment-dependent | Local repository execution is the current default; remote backends must be named explicitly. |
| `workflow.testreport.review` | Review test reports to classify failures, drift, and broken system areas | prompt or agent orchestration | scaffold-specific | read-only | Natural fit for a specialist report-review overlay. |
| `workflow.testreport.triage` | Apply the report triage taxonomy and route likely next actions | prompt or agent orchestration | scaffold-specific | read-only | Structured subset of report review focused on classification and routing. |
| `workflow.testreport.ticket-draft` | Draft follow-up ticket content from report triage results | manual fallback | generic with backend adapter | write | Keep candidate-only until the issue backend is explicit and satisfies the issue-backend placeholder contract. |
| `workflow.codequality.review` | Review code for duplication, DRY failures, weak abstraction, and best-practice issues | prompt or agent orchestration | scaffold-specific | read-only | Prefer one review capability with explicit focus such as `dry`, `duplication`, `generalization`, or `best-practice` over many unrelated command implementations. |
| `workflow.codequality.refactor-plan` | Turn accepted code-quality findings into bounded refactor steps | prompt or agent orchestration | scaffold-specific | control-plane | Use after review, not as a substitute for a findings-first pass. |
| `workflow.uiintent.review` | Infer UI intent from exported testcase artifacts and compare it to current test-code assertions | prompt or agent orchestration | scaffold-specific | read-only | Intended for detecting intent-vs-implementation drift before maintenance edits; outputs discrepancy summary plus smallest safe contract adjustment. |
| `workflow.learn.manage` | Internalize validated findings and retrieve canonical learned facts with explicit lookup-path metadata | prompt or agent orchestration | scaffold-specific | write (scoped) | Supports modes `internalize|retrieve|improve`; retrieval is schema-index authoritative and source grep is auxiliary only. |
| `workflow.agent.delegate` | Hand a slice to another agent role or overlay | prompt or agent orchestration | scaffold-specific | control-plane | Should route by role contract, not by ad hoc prose only. |
| `workflow.agent.review` | Invoke a review or critic pass by the appropriate role | prompt or agent orchestration | scaffold-specific | control-plane | Maps naturally to General Critic, Code Reviewer, or future specialized critics. |

**On the four `.ai/tools/claim.py`-backed rows above** (`workflow.task.claim`,
`workflow.task.release`, `workflow.task.claim-status`,
`workflow.registry.sync`): this table is a one-line summary and can drift
from the tool's actual behavior as it's extended (see TASK-0024.001,
TASK-0027 for planned extensions) — it already had one small inaccuracy,
corrected above. Before relying on exact flag names, defaults, or output
format, run `.ai/tools/claim.py --help` or `.ai/tools/claim.py <subcommand>
--help` (both already whitelisted in `.claude/settings.json`, same as any
other invocation of the tool — no separate permission needed), or read the
module docstring at the top of `.ai/tools/claim.py` directly. Treat this
table as a pointer to the tool, not a substitute for it.

**Invoke it directly — don't pipe or redirect its output** (e.g.
`... | head`, `... | grep`, `2>&1 | tee ...`). The whitelist entries only
cover invocations of `claim.py` itself; a pipe hands output to a *second*
program (`head`, `grep`, …) that isn't covered, so the whole command still
prompts even though `claim.py` alone wouldn't. This also isn't needed in
practice — `status` with no args prints one short line per active claim
(9 lines total as of this writing), and single-task `status TASK-ID` is
one line. Matches TASK-0025's broader command-hygiene guidance: prefer a
single, non-piped command over an ad hoc shell pipeline.

## Slash Command Fit

- Candidate command shapes live in `.ai/reference/SLASH_COMMAND_CANDIDATES.md`.
- Slash commands should bind to capabilities such as `repo.packaging.snapshot`, not to raw script paths.
- Primitive `repo.vcs.*` capabilities keep Commit Packager decoupled from direct git-specific reasoning.
- Implemented prompt surfaces currently include packaging, intent formulation and intent review, UI intent review, task creation, task performance, and task resolution, learn workflow, critic delegation, the code-quality review family, refactor planning, test report review and triage, and test execution.
- Task operations, test-case management, and agent handoff should also bind to named workflow capabilities before backend-specific implementations are chosen.
- Current backend resolution lives in `.ai/reference/BACKEND_SELECTION.md`.
- Local-automation guidance for manual-first environments lives in `.ai/reference/LOCAL_AUTOMATION_MANUAL_ENVIRONMENTS.md`.
- Issue escalation requirements live in `.ai/reference/ISSUE_BACKEND_PLACEHOLDER_CONTRACT.md`.
- End-to-end linking expectations live in `.ai/reference/TRACEABILITY_MODEL.md`.
- Canonical lifecycle and resolution meanings live in `.ai/reference/RESOLUTION_VOCABULARY.md`.
- Report triage classes live in `.ai/reference/TEST_REPORT_TRIAGE_TAXONOMY.md`.

## Provider Contract Template

For each new capability, document:

- capability name
- purpose
- provider order
- current provider
- environment contract
- output format
- safety constraints
- generalization status
- slash-command fit