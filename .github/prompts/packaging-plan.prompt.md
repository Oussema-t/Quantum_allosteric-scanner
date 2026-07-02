---
description: "Build or refresh a full commit split plan from all current changes using AI grouping and persist it."
name: "Packaging Plan"
argument-hint: "Optional overrides: intent=<area> boundary=strict|big-bang include=<csv> exclude=<csv> defer-branch=<name> min-area-group-size=<n> group-mode=layered|area-first|mixed keep-together=<csv>"
agent: "agent"
---

Use the Commit Packager workflow to build a persisted split plan from the complete set of current changes.

Sources:

- capability contract: [CAPABILITIES](../../.ai/reference/CAPABILITIES.md)
- slash-command catalog: [SLASH_COMMAND_CANDIDATES](../../.ai/reference/SLASH_COMMAND_CANDIDATES.md)
- provider entrypoint: [capability-runner.sh](../../agents-tools/capability-runner.sh)

Required behavior:

- Treat this as an AI-authored planning workflow using `repo.vcs.changed-files` as the source capability.
- Call exactly one capability-runner command to fetch complete change scope by default: `repo.vcs.changed-files --scope all --json`.
- Infer primary feature intent from the current branch/ticket naming and align the first feature group to that intent.
- UI area and branch intent are top priority for grouping.
- Default boundary mode is `strict`: if completed work includes files outside the current branch intent area, keep them in plan coverage but place them into `status: "deferred"` groups with a `targetBranch` note.
- `big-bang` boundary mode is opt-in only via slash args and allows cross-area mixed pending groups.
- Optional slash overrides:
	- `intent=<area>`: explicit intent area when branch name is not enough.
	- `boundary=strict|big-bang`: enforce split-across-branches or allow single-branch packaging.
	- `include=<csv>` / `exclude=<csv>`: explicit area filters.
	- `defer-branch=<name>`: target branch label for deferred groups.
	- `min-area-group-size=<n>`: when an area has at least `n` changed files, allow/require its own group (default `3`).
	- `group-mode=layered|area-first|mixed`: choose whether layer grouping or area grouping has priority.
	- `keep-together=<csv>`: explicit path-prefix areas that must stay in one dedicated group.
- Build commit groups by semantic concern (feature slices, tooling, docs/config, refactors), not fixed bucket heuristics.
- Keep one dominant feature noun per group (for example buckets, keys, registry); split mixed groups unless there is a hard dependency.
- When a single feature area still has many files, prefer layer splits in this order: UI model layer (page objects/components), action-support layer (actions/helpers/constants/context), spec suite layer (spec files).
- Area-cohesion gate: if files from one path area appear across multiple groups and area file count is >= `min-area-group-size`, create one dedicated area group unless an explicit `group-mode=layered` override is set.
- Commit-size floor: avoid single-file commits by default; target >=3 files when possible unless the file is a required dependency singleton.
- Keep groups reviewable; when a group grows beyond about 25 files, split it if possible and justify when not possible.
- Persist the result into `.ai/tasks/commit-split-plan.json` unless user overrides path.
- Ensure every changed file is either assigned to exactly one group or listed under `ambiguousFiles`.
- After writing the plan, run one validation call through capability runner:
	- `agents-tools/capability-runner.sh repo.packaging.validate-plan-coverage --json`
- Use commit subjects in conventional format and keep each group bounded to one coherent intent.
- Write each group rationale in this exact order: `Intent: ... Includes: ... Excludes: ... Dependency: ...`.
- Use concise layer-forward naming for these groups (for example ui-model-layer, action-support-layer, spec-suite) instead of raw implementation acronyms.
- Do not stage files and do not create commits.

Execution hint:

- `agents-tools/capability-runner.sh repo.vcs.changed-files --scope all --json`
- `agents-tools/capability-runner.sh repo.packaging.validate-plan-coverage --json`

Examples:

1. Branch-intent strict split (default):
	- `/Packaging-Plan intent=buckets boundary=strict`

2. Keep a known area together as a dedicated group:
	- `/Packaging-Plan intent=buckets boundary=strict keep-together=FIX_HERE`

3. Prefer area groups over layered split when areas are mixed:
	- `/Packaging-Plan intent=buckets boundary=strict group-mode=area-first min-area-group-size=3`

4. Explicitly defer out-of-scope work to another branch label:
	- `/Packaging-Plan intent=buckets boundary=strict defer-branch=hamiltonians`

5. Intentional big-bang packaging override:
	- `/Packaging-Plan intent=object-storage boundary=big-bang group-mode=mixed`

Plan file shape (minimum):

```json
{
	"strategy": "assistant-authored",
	"scope": "all",
	"sourceCapability": "repo.vcs.changed-files",
	"changedCount": 0,
	"groups": [
		{
			"name": "group-name",
			"subject": "chore(repo): ...",
			"status": "pending",
			"targetBranch": "optional-branch-for-deferred-groups",
			"rationale": "why these files belong together",
			"files": ["path/file"]
		}
	],
	"ambiguousFiles": [],
	"generatedAt": "ISO-8601"
}
```

Respond in this shape:

- `Answer:` one to three lines with plan result.
- `Evidence:` source capability call, branch intent signal, changed count, pending group count, deferred group count, ambiguous count, coverage validation output, plan file path.
- `Risk/Unknown:` unresolved ownership or ambiguous files.
- `Next:` smallest useful follow-up.
