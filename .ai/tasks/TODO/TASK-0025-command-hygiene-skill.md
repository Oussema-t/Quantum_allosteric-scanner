# TASK-0025 command-hygiene-skill

## Context

- ID: TASK-0025
- Title: Single-command preference + reusable-script convention for `.ai/`
  scaffold threads, delivered as a written policy plus a Claude Skill
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
- Scope: `.ai/` scaffold-coordination threads only (task claiming/releasing,
  registry edits, task packaging, review artifact assembly, etc.) — NOT a
  repo-wide constraint on backend/frontend engineering work. Narrowed to
  scaffold-only per explicit decision this session; do not silently widen it.

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
  - a policy/reference doc (candidate location:
    `.ai/reference/COMMAND_HYGIENE.md`) stating the preference, the
    escape-hatch rule for genuinely-required multi-step commands, and the
    rationale (see below) — linked from `.ai/COMMON.md`'s Quick Navigation
    like the other reference docs.
  - a Claude Skill under `.claude/skills/` (this repo currently has none —
    all skills referenced elsewhere in this session, e.g.
    `fewer-permission-prompts` and `update-config`, are user-level, not
    repo-local; this would be the first repo-local skill) that a thread can
    invoke when it's about to run, or just ran, a chained/piped command
    during `.ai/`-scoped work. The skill should: recognize the repeated
    pattern, propose extracting it into a small named script under
    `.ai/tools/`, draft the matching `CAPABILITIES.md` entry, and draft (not
    apply) the `.claude/settings.json` allowlist addition for a human to
    approve — mirroring the scan-propose-apply shape of
    `fewer-permission-prompts` but for command consolidation instead of
    permission friction.
  - explicit rationale captured in the doc, not just asserted: (1) low token
    churn — a named script invocation is cheaper context per call than an
    agent re-deriving/reasoning through a chained pipeline every time it
    needs the same effect; (2) deterministic outcomes — a reviewed, named
    script's behavior is fixed and auditable, where an ad hoc pipeline
    composed fresh each time can silently vary (flag order, quoting,
    intermediate state) between threads or sessions.
- Out Of Scope:
  - repo-wide enforcement over backend/frontend engineering Bash usage —
    explicitly scaffold-only per this session's decision.
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
    provider, not a shipped one. This task must not assume that runner
    exists; if the skill's first worked example would naturally live behind
    that runner, either build the runner first as its own dependency (out of
    this task's scope — flag it) or place the new script directly under
    `.ai/tools/` as its own standalone entry point.
  - keep the policy doc short — this is a preference statement plus one
    escape hatch, not a new process layer.
- Planned Validation: pick one real chained/piped command this session
  already used more than once while working the scaffold (e.g. a
  `find | xargs` or `git status && git log` style combo), run the new skill
  against it end-to-end, confirm it produces: a working script under
  `.ai/tools/`, a correct `CAPABILITIES.md` entry, and a correct draft
  allowlist line — then have a human approve the allowlist addition before
  it's applied.

## TODO

- [ ] Draft `.ai/reference/COMMAND_HYGIENE.md` (policy + rationale + escape
      hatch) and link it from `.ai/COMMON.md`'s Quick Navigation.
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
- [ ] Decide and record whether "Skills Crafter" becomes a seeded role brief
      under `.ai/experts/` (it is currently used as this task's `Owner` but
      has no brief, unlike Toolsmith/Implementer/etc.) — see Open Questions.

## Dependency

- `.github/instructions/tooling/capability-selection.instructions.md` —
  provider-order rule this task's script must follow.
- Loosely related to TASK-0024 (claim/lock tool) as a sibling example of
  "expose repeated coordination behavior as a small named tool" — not
  blocking, not blocked by it.

## Open Questions

- Should "Skills Crafter" be formalized as a new specialist overlay in
  `.ai/experts/README.md` (alongside Code Reviewer, Commit Packager, Test
  Report Reviewer), given it doesn't map cleanly onto Toolsmith (which owns
  capability contracts generically) or Implementer (bounded execution)? This
  task's Owner field uses it without a corresponding brief — flagged, not
  resolved, here.
- `agents-tools/capability-runner.sh` is referenced as an already-existing
  provider throughout `CAPABILITIES.md` but is absent from disk — is that
  tracked anywhere as its own gap, or does it only surface incidentally
  (as it does here) whenever a task tries to build on top of it? If not
  tracked, this may warrant its own follow-up task.
- Repo-wide widening: if this preference proves useful for `.ai/` threads,
  is there appetite to propose it (via CLAUDE.md or a `.github/instructions`
  entry) for backend/frontend engineering threads too? Deliberately deferred
  out of this task's scope, not decided against.

## Done

(not yet)
