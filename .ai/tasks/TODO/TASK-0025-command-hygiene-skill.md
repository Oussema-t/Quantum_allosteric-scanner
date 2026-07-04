# TASK-0025 command-hygiene-skill

## Context

- ID: TASK-0025
- Title: Single-command preference + reusable-script convention for all
  threads (widened 2026-07-04 from `.ai/` scaffold-only), delivered as a
  written policy plus a Claude Skill
- Status: TODO
- Owner: Skills Crafter
- Claimed By: Skills Crafter (this thread)
- Claimed At: 2026-07-04 16:30
- Source: direct request, this session, 2026-07-04 — motivated by the same
  class of problem TASK-0024 hardens (concurrent threads doing ad hoc,
  non-reusable things in `.ai/` coordination work), but aimed at command
  shape and token/determinism cost rather than atomicity: threads currently
  free to chain (`&&`) or pipe (`|`) arbitrary Bash invocations reinvent the
  same multi-step sequences per-session, burning tokens re-deriving them and
  producing non-deterministic variants of the "same" operation.
- Scope: **repo-wide, all threads** (updated 2026-07-04, superseding the
  scaffold-only narrowing below — explicit user decision: "all threads
  should use the as-few-commands-in-one-shot-as-possible approach — this is
  the base for whitelisting and using a capability-runner approach"). The
  as-few-commands rule is not just a token/determinism preference in
  isolation — it is the precondition that makes both a small, stable
  `.claude/settings.json` allowlist *and* the `agents-tools/
  capability-runner.sh` single-entry-point design (TASK-0026) tractable:
  fewer distinct ad hoc command shapes means fewer allowlist patterns to
  reason about and a real incentive to route through the capability runner
  instead of composing shell inline. Original narrower framing, kept for
  history: "`.ai/` scaffold-coordination threads only (task
  claiming/releasing, registry edits, task packaging, review artifact
  assembly, etc.) — NOT a repo-wide constraint on backend/frontend
  engineering work." That framing is superseded, not deleted.
- **Prior art found (2026-07-04, later same session):** `.github/prompts/
  test-execute.prompt.md` (lines 25-30) already ships a stable, committed
  "Command-structure contract for local execution" for the
  `workflow.testexecution.run` capability — "use one stable capability
  command per run", "avoid chained shell orchestration (`&&`, `;`, mixed
  pipe workflows)", "avoid inline shell variable setup plus execution in
  one command", "prefer request-file mode for multi-argument or repeatable
  runs". This is the same principle this task proposes, already ratified
  in the stable `.github/` layer, just scoped to one workflow instead of
  `.ai/` coordination generally. Do not treat this task's doc as inventing
  the idea — treat it as either (a) a second, independently-scoped
  application of an existing principle, or (b) the trigger to extract a
  shared instruction both places cite, per the Open Questions update below.
  (Unrelated false lead, checked and ruled out: `no-chain` appears in
  `refactor-plan.prompt.md`, `best-practice-review.prompt.md`, and
  `task-perform.prompt.md` — but there it means "skip automatic
  prompt-to-prompt workflow chaining," not "avoid shell command chaining."
  Different concept, same word; don't conflate them when cross-referencing.)

## Intent Contract

- Outcome: a scaffold-coordination thread has a clear, discoverable
  preference — issue single, non-chained, non-piped commands wherever
  possible; where a multi-step/chained/piped sequence is genuinely required,
  it must be exposed as a short, named, reusable script under `.ai/tools/`
  (registered in `.ai/reference/CAPABILITIES.md` per the existing
  capability-first rule in
  `.github/instructions/tooling/capability-selection.instructions.md`) rather
  than composed ad hoc inline at the point of use.
- In Scope:
  - **doc location, decided 2026-07-04 following the repo-wide scope
    change:** `.github/instructions/tooling/command-hygiene.instructions.md`
    (stable layer), not the originally-candidate
    `.ai/reference/COMMAND_HYGIENE.md` — this generalizes
    `test-execute.prompt.md`'s existing "Command-structure contract" (see
    Context's Prior Art note) into a shared instruction both that prompt
    and every other thread cite, rather than maintaining two
    independently-drifting statements of the same rule. State the
    preference, the escape-hatch rule for genuinely-required multi-step
    commands, and the rationale (see below); link it from
    `.ai/COMMON.md`'s Quick Navigation and from
    `test-execute.prompt.md` itself (replace that prompt's inline
    contract with a pointer once this lands, so there's exactly one
    canonical copy).
  - a Claude Skill under `.claude/skills/` (this repo currently has none —
    all skills referenced elsewhere in this session, e.g.
    `fewer-permission-prompts` and `update-config`, are user-level, not
    repo-local; this would be the first repo-local skill) that a thread can
    invoke when it's about to run, or just ran, a chained/piped command in
    any part of the repo (widened from `.ai/`-scoped-only). The skill
    should: recognize the repeated pattern, propose extracting it into a
    small named script under `.ai/tools/` (or `agents-tools/` for
    capability-runner-backed cases), draft the matching `CAPABILITIES.md`
    entry, and draft (not apply) the `.claude/settings.json` allowlist
    addition for a human to approve — mirroring the scan-propose-apply
    shape of `fewer-permission-prompts` but for command consolidation
    instead of permission friction.
  - explicit rationale captured in the doc, not just asserted: (1) low token
    churn — a named script invocation is cheaper context per call than an
    agent re-deriving/reasoning through a chained pipeline every time it
    needs the same effect; (2) deterministic outcomes — a reviewed, named
    script's behavior is fixed and auditable, where an ad hoc pipeline
    composed fresh each time can silently vary (flag order, quoting,
    intermediate state) between threads or sessions.
- Out Of Scope:
  - **superseded 2026-07-04:** "repo-wide enforcement... explicitly
    scaffold-only" — no longer out of scope; see Context's Scope update.
    Kept here struck-through-in-spirit rather than deleted, so a reader
    following this task's history sees the reversal explicitly instead of
    silently.
  - retrofitting TASK-0024's claim/release tool once it lands — that tool is
    itself a case of "exposed as a short reusable script," it doesn't need
    separate hygiene review under this task.
  - enforcement mechanism beyond advisory (no hook, no CI gate blocking
    chained commands) — matches this scaffold's existing "advisory, human
    judgment call" philosophy (see TASK-0017's soft-lock precedent) unless a
    real incident later shows advisory isn't enough, the same way TASK-0024
    hardened TASK-0017 only after an actual failure.
  - building out `.ai/tools/` broadly — this task's script output should be
    limited to what the skill actually needs as its own worked example (see
    Planned Validation), not a speculative library.
- Constraints And Invariants:
  - no new runtime dependency beyond Python stdlib / POSIX shell for any
    script the skill produces (matches TASK-0024's constraint and this
    project's challenge-deadline "trivially runnable" bar).
  - `agents-tools/capability-runner.sh`, referenced repeatedly in
    `.ai/reference/CAPABILITIES.md` as the "Current Provider" for the entire
    Commit Packager capability set, does not exist anywhere on disk in this
    repo as of this writing — CAPABILITIES.md is documenting an aspirational
    provider, not a shipped one. **Tracked and being rebuilt under TASK-0026**
    (parent) and its `TASK-0026.001`-`.004` subtasks — this task must not
    assume the runner exists yet, and must not re-file a duplicate "the
    runner is missing" task; if the skill's first worked example would
    naturally live behind that runner, place the new script directly under
    `.ai/tools/` as its own standalone entry point instead of waiting on
    TASK-0026.
  - keep the policy doc short — this is a preference statement plus one
    escape hatch, not a new process layer.
- Planned Validation: pick one real chained/piped command this session
  already used more than once while working the scaffold (e.g. a
  `find | xargs` or `git status && git log` style combo), run the new skill
  against it end-to-end, confirm it produces: a working script under
  `.ai/tools/`, a correct `CAPABILITIES.md` entry, and a correct draft
  allowlist line — then have a human approve the allowlist addition before
  it's applied.

## In Progress

None

## TODO

- [ ] Draft `.github/instructions/tooling/command-hygiene.instructions.md`
      (policy + rationale + escape hatch) and link it from
      `.ai/COMMON.md`'s Quick Navigation and from `test-execute.prompt.md`.
- [ ] Design the Claude Skill's shape (name, trigger conditions, inputs,
      outputs) before writing it — per Toolsmith's own rule, "a
      capability-first contract before provider expansion."
- [ ] Implement the skill under `.claude/skills/`.
- [ ] Run Planned Validation against one real repeated command from this
      session.
- [ ] Register the resulting script as a capability in
      `.ai/reference/CAPABILITIES.md`.
- [ ] Draft (not apply) the `.claude/settings.json` allowlist addition; get
      human approval before it lands, consistent with this scaffold's
      approval-gated-local-helper rule in
      `.ai/reference/LOCAL_AUTOMATION_MANUAL_ENVIRONMENTS.md`.
- [x] Decide and record whether "Skills Crafter" becomes a seeded role brief
      under `.ai/experts/` — **Resolved 2026-07-04 (user decision): yes.**
      Formalized in `.ai/experts/skills-crafter.md` (Status: Active) and
      `.ai/experts/README.md` (no longer marked candidate).

## Dependency

- `.github/instructions/tooling/capability-selection.instructions.md` —
  provider-order rule this task's script must follow.
- Loosely related to TASK-0024 (claim/lock tool) as a sibling example of
  "expose repeated coordination behavior as a small named tool" — not
  blocking, not blocked by it.

## Open Questions

- **Resolved 2026-07-04 (user decision):** "Skills Crafter" is formalized
  as a specialist overlay. See `.ai/experts/skills-crafter.md` (Status:
  Active) and `.ai/experts/README.md`.
- **Resolved 2026-07-04 (user decision):** the `agents-tools/
  capability-runner.sh` gap is tracked — under TASK-0026 (filed same
  session as this task). User also directed adding an explicit
  cross-reference to any other task that assumes the runner exists without
  noting the rebuild; done for TASK-0019 (see its Open Questions) — the
  only other task found (via repo-wide grep) that touches
  `repo.packaging.*`/Commit Packager capabilities without already citing
  TASK-0026.
- **Resolved 2026-07-04 (user decision):** repo-wide widening — yes, "all
  threads should use the as-few-commands-in-one-shot-as-possible approach."
  See Context's Scope update above. Consequently also resolves the
  doc-location question this section previously carried: the policy doc
  lives at `.github/instructions/tooling/command-hygiene.instructions.md`
  (stable layer), generalizing `test-execute.prompt.md`'s existing contract
  rather than duplicating it in a scaffold-scoped `.ai/reference/` doc.

## Done

(not yet)
