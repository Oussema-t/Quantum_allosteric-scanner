# TASK-0061 `claim.py add` — attributed stage-and-annotate, any path

## Context

- ID: TASK-0061
- Title: A new `claim.py add <TASK-ID> <path> --purpose "..."` subcommand
  (plus a manifest-file batch mode) that stages a file **and** appends a
  short, permanent "added `<path>` — `<purpose>`" record to the claiming
  task's own file, in one whitelisted call — unrestricted by directory
  (unlike `stage`), because the safety property here is *mandatory
  attribution to a real task*, not a path prefix
- Status: TODO
- Owner: Toolsmith
- Claimed By: —
- Claimed At: —
- Source: direct request, this session, 2026-07-11, prompted by
  `.ai/memory/questions/toolsmith/answered/Q-0001-*.md`'s incident — a
  concurrent thread's `git add` landed in another thread's staged index,
  caught by a *human/reviewer reading the proposed commit*, not by any
  tooling cross-referencing "what's staged" against "what the claiming
  task's own file says it's touching." Refined from this task's original
  "opt-in `--reflect-into` flag on `stage`" framing into a concrete shape
  per direct user design input: a dedicated `add` verb, one file (or a
  batch via manifest file) at a time, no directory scope restriction —
  see Decisions below for why that's safe here despite `stage`'s own
  restriction (TASK-0029) existing for the opposite reason.
- Scope: a new `.ai/tools/claim.py` subcommand, `add`. Does not change
  `stage`, `commit-guard`, `move`, `sync`, or `GIT-COMMIT`'s mechanics —
  **the commit gate is unchanged**: `add` only affects staging, a thread
  still must `claim GIT-COMMIT` → ... → `commit-guard --expect <full
  list>` → `git commit` → `release` exactly as today. `add` makes the
  *staging* step incremental, attributed, and per-file instead of a
  single bulk `--expect` declaration.

## Intent Contract

- Outcome: staging a file mid-task is one whitelisted command that both
  `git add`s it and permanently records why, in the claiming task's own
  file — so a reviewer (human or agent) can check a task's own file
  against what's actually staged/committed under it, without trusting
  free-text Done-section prose written after the fact or re-deriving
  intent from `git log -p`.
- In Scope:
  - **Decided: a new `add` subcommand, not a flag on `stage`.** `stage`
    stays exactly as TASK-0029 built it (bulk-declare-and-verify an exact
    set for one commit, `.ai/`/`.claude/`-scoped). `add` is a different,
    complementary usage pattern — incremental, per-file, used as work
    progresses rather than all at once right before a commit. Forcing
    both shapes into one subcommand via flags would make `stage`'s
    already-precise self-verification semantics ambiguous (see `stage`'s
    own "asserts the *entire* index matches `--expect`" behavior,
    confirmed this session to conflict with any kind of incremental/
    partial use).
  - **Decided: no directory scope restriction (unlike `stage`).**
    `stage`'s `.ai/`/`.claude/` restriction exists because an unscoped
    bulk `git add` wrapper, riding on `claim.py`'s already-blanket
    `.claude/settings.json` whitelist, would let any thread silently
    stage *anything*, unattributed (TASK-0029's whole rationale). `add`
    doesn't have that failure mode: every call is mandatorily tied to a
    real, on-disk-resolvable `TASK-ID` and a required `--purpose`
    string, permanently appended to that task's own file. The safety
    property is *attribution*, not *path prefix* — a reviewer can always
    answer "who staged this and why" by reading the task file, which is
    precisely what was missing during Q-0001's incident. This does not
    reopen TASK-0029's gap: `stage` remains scoped for its own bulk/
    unattributed-by-default use pattern; `add` is safe unscoped because
    it can't be used unattributed at all.
  - **Decided: batch mode is a manifest *file*, never inline JSON on the
    command line.** `claim.py add <TASK-ID> --from-file <manifest.json>`,
    where the manifest is a JSON array of `{"file": "...", "purpose":
    "..."}` objects; a top-level `{"purpose": "...", "files": [...]}`
    shape is also accepted for the common case of one shared purpose
    covering several files (per-file `purpose` in the array form always
    wins if both are present). Inline JSON strings on the command line
    are explicitly rejected as a design option — nested quoting/escaping
    across a Bash call is exactly the fragility class command-hygiene
    exists to avoid; a manifest file is written with the `Write` tool
    (not Bash at all, no whitelisting concern) and only its path crosses
    into the one whitelisted `add` call.
  - single-file form: `claim.py add <TASK-ID> <path> --purpose "text"` —
    the common case, one file just written/edited, stage-and-annotate it
    immediately. Both forms perform the same two effects: (1) `git add
    --` the file(s), (2) append one line per file to `<TASK-ID>`'s own
    file under a new, dedicated `## Staged Files` section (created if
    absent) — e.g. `- [<timestamp>] \`<path>\` — <purpose>` — a targeted
    append, never a whole-file rewrite (same discipline
    `update_registry_row`/`move`'s Status-line rewrite already use).
  - after staging, a lighter self-check than `stage`'s exact-match
    assertion: confirm each just-added path actually now appears in
    `git diff --cached --name-only` (catches an add that silently failed
    or no-op'd, e.g. a gitignored path) — **not** an assertion that the
    whole index matches only these paths, since `add`'s whole purpose is
    incremental staging alongside whatever else is already staged.
  - refuse (not silently skip) if `<TASK-ID>` doesn't resolve to exactly
    one file on disk — reuse `find_task_file`'s existing zero-or-multiple
    refusal discipline directly, don't re-derive it.
  - register `add` in `.ai/reference/CAPABILITIES.md`; whitelist
    `Bash(python3 .ai/tools/claim.py add *)` (+ bare/`python` forms,
    matching every other subcommand's three-form enumeration in
    `.claude/settings.json`).
- Out Of Scope:
  - recording the eventual **commit hash** as a second phase (e.g. a
    follow-up `claim.py record-commit <TASK-ID>` after `git commit`
    resolves it) — flagged in Open Questions, not required for this task
    to be Done. Ship the staged-at-a-point-in-time record first; revisit
    once that's proven useful, matching this scaffold's incremental-
    hardening precedent (TASK-0017→TASK-0024, TASK-0028→TASK-0042).
  - any change to the commit gate itself (`GIT-COMMIT` claim,
    `commit-guard`'s `--expect` matching, `--expect-empty`) — unchanged;
    `add` only affects what gets staged, never `git commit` itself.
  - enforcing that `GIT-COMMIT` be held before `add` runs — not required.
    `add` is meant to be usable throughout a unit of work, including
    before a thread has decided it's ready to start assembling a commit;
    requiring the lock this early would push `claim GIT-COMMIT` earlier
    than TASK-0028's own convention ("before the *first* `git add`")
    already intends, without a clear benefit. A thread still must hold
    it before `git commit` itself, unchanged.
  - a distributed lock, CI gate, or anything beyond a script + local
    files — matches every prior `claim.py` extension's scope ceiling.
- Constraints And Invariants:
  - Python stdlib only, no new dependency.
  - the appended record must stay plain, grep-able markdown — no hidden
    structured/machine-only format, matching every other registry in
    this scaffold.
  - manifest JSON parsing uses stdlib `json` only; a malformed manifest
    file must refuse with a clear error naming the parse problem, not a
    raw traceback.
- Planned Validation:
  1. Single-file `add` against a real (or scratch) task; confirm the
     file is staged and the task file gains exactly one new
     `## Staged Files` line, nothing else changed.
  2. Batch `add --from-file` against a manifest covering 3+ files
     (mix of per-file and shared-purpose forms); confirm all files
     staged, one line appended per file, in the manifest's order.
  3. Confirm the refusal path when `<TASK-ID>` has zero or multiple
     on-disk matches — reuse, don't re-derive.
  4. Confirm a malformed manifest file refuses with a clear message, no
     partial staging (all-or-nothing, not some files added before the
     parse error is hit).
  5. Confirm `stage` and `commit-guard` are byte-identical to today —
     this task must not change their behavior at all.

## Dependency

- [TASK-0029](../DONE/TASK-0029-scoped-stage-tool.md) (Done) — `stage`
  stays as-is; read its Done section so `add` doesn't quietly duplicate
  or contradict its self-verification approach.
- [TASK-0027](../DONE/TASK-0027-task-move-tool.md) (Done) — the
  `find_task_file` zero-or-multiple-match discipline this task reuses.
- `.ai/memory/questions/toolsmith/answered/Q-0001-*.md` — the incident
  motivating this; its Answer section explains why `commit-guard` (not
  the lock) is the real backstop — `add` is additive documentation on top
  of that, not a replacement for running `commit-guard` before `git
  commit`.

## Open Questions

- Worth the two-phase design (stage-time record now, commit-hash record
  later via a second call) from the start, or ship staged-only first?
  Recommend staged-only first — see Out Of Scope; adding a commit-hash
  phase later is additive, and building it before knowing whether the
  staged-only record is useful in practice risks over-building.
- Should a derived task ever get its `## Staged Files` entries copied or
  summarized into `## Done` once the task moves to `DONE`, or is leaving
  the running log in place (regardless of the file's current lifecycle
  folder) sufficient? Recommend leaving it in place — it's already a
  permanent, dated record; forcing a copy-into-Done step adds a manual
  chore this task doesn't need to impose.
- Exact manifest schema details (e.g. should a manifest entry support a
  `category` or link to a SEAM/INV id, given TASK-0050/0051's protocols
  landed this session) — left open, not required for a first version;
  extend the schema later if a real need shows up rather than
  speculatively widening it now.

## Done

(not yet)
