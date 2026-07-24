# TASK-0154 Gate `stage` on `GIT-COMMIT` being held

## Context

- ID: TASK-0154
- Title: `.ai/tools/claim.py stage` refuses outright unless `GIT-COMMIT`
  is currently claimed (by anyone) — closes a real gap found during a
  tooling verification pass: nothing previously stopped `stage` from
  running lock-less
- Status: Done
- Resolution: done
- Owner: Toolsmith
- Claimed By: Toolsmith (this thread)
- Claimed At: 2026-07-24 21:15
- Source: direct user finding, 2026-07-24 — "An implementer managed to
  use our tooling to stage their files before they claimed the git
  commit lock. Our tooling should check whether the git commit lock is
  claimed - if not, no staging should be allowed." Raised mid-way through
  a requested verification pass over the commit-lock/staging tooling.
- Scope: `.ai/tools/claim.py`'s `stage` subcommand only. Explicitly does
  **not** touch `move`/`resolve`/`scq-enter`/`scq-leave`/`claim`/
  `release`/`commit-guard` — confirmed with the user via an explicit
  scope question before implementing (see Decided below).

## Intent Contract

- Outcome: `stage --expect PATH [PATH ...]` refuses immediately (before
  touching the index) if `GIT-COMMIT` is unclaimed, forcing the
  documented workflow order (`claim` before `stage`) to actually be
  enforced rather than just written down.
- In Scope:
  - **Decided (user, explicit choice between two options): gate `stage`
    only, not `move`/`resolve`.** `stage` is the one subcommand whose
    entire purpose is the deliberate, immediately-pre-commit staging
    step (`claim GIT-COMMIT` → `commit-guard --expect-empty` → `stage`
    → `commit-guard --expect` → `git commit` → `release`). `move`/
    `resolve` also call `git add`/`git mv` internally, but gating them
    the same way would break an established, actively-relied-on pattern
    (routine task-file housekeeping — e.g. marking a task Done mid-
    session — called constantly this session without holding
    `GIT-COMMIT` first, and TASK-0061 already reasoned explicitly
    against requiring the lock for the analogous `add` subcommand).
  - The check is an **existence** check (`read_lock("GIT-COMMIT") is not
    None`), not yet an **identity** check against the calling thread —
    `stage` has no `--as`/claimant argument today, so it cannot verify
    "the *caller* holds it," only "*someone* holds it." Adding caller
    identity is a natural, separate hardening step (flagged in Open
    Questions), not required to close the gap the user found.
  - Clear, actionable refusal message naming the fix (`claim.py claim
    GIT-COMMIT <claimant>`) and the full recommended workflow, not just
    a bare "refused."
- Out Of Scope:
  - `move`/`resolve`/`scq-enter`/`scq-leave` gaining the same check (see
    Decided above).
  - identity verification (caller vs. lock claimant) — Open Question.
  - TASK-0042's hook-enforced `git commit`/`git push` gate — a separate,
    complementary mechanism (Claude Code `PreToolUse` hook, intercepts
    the outer Bash call) that would not have caught this gap either:
    `claim.py stage ...` never contains the literal text "git commit"/
    "git push" in its own command string, so a hook filtering on those
    verbs wouldn't see `stage`'s internal `git add` at all. This task and
    TASK-0042 close different, non-overlapping parts of the same
    advisory-only surface.
- Constraints And Invariants:
  - Python stdlib only, no new dependency.
  - the check runs before any other validation in `cmd_stage` (scope
    check, missing-on-disk check) — fail on the more fundamental
    precondition first, don't let a caller get partway through arg
    validation before hitting the lock check.
- Planned Validation:
  1. `stage --expect <path>` with `GIT-COMMIT` unclaimed → refused, clear
     message, index untouched.
  2. `claim GIT-COMMIT <claimant>`, then the same `stage` call → succeeds
     exactly as before (no behavior change once the lock is held).
  3. Confirm `stage`'s existing scope restriction (`.ai/`/`.claude/`
     only) and self-verification are unaffected — same refusal/success
     shape as before TASK-0154, just gated behind the new precondition.
  4. Confirm `move`, `resolve`, `scq-enter` all still succeed with
     `GIT-COMMIT` unclaimed — regression check that the scope decision
     (stage-only) actually holds in the implementation, not just the
     design.
  5. Full workflow smoke test: `claim GIT-COMMIT` → `commit-guard
     --expect-empty` → `stage --expect` → `commit-guard --expect` →
     `git commit` → `release GIT-COMMIT` — unchanged end to end.

## Dependency

- [TASK-0029](../DONE/TASK-0029-scoped-stage-tool.md) (Done) — `stage`'s
  existing scope-restriction/self-verify logic, unchanged by this task.
- [TASK-0028](../DONE/TASK-0028-commit-lock.md) (Done) — `GIT-COMMIT`'s
  lock mechanics (`read_lock`), reused directly, not re-derived.
- `.ai/memory/questions/toolsmith/answered/Q-0001-*.md` — the original
  finding that `GIT-COMMIT` is advisory-only; this task closes one
  specific, previously-unclosed instance of that gap (staging via
  `stage` itself), distinct from TASK-0042's `git commit`/`push` hook
  and TASK-0024.001's whole-file-resource-lock generalization.
- [TASK-0042](TASK-0042-hook-enforced-commit-gate.md) (TODO, unclaimed)
  — complementary, does not overlap (see Out Of Scope).
- [TASK-0061](TASK-0061-staged-files-task-audit-trail.md) (TODO,
  unclaimed) — its own explicit "out of scope: requiring GIT-COMMIT for
  `add`" reasoning is exactly why this task doesn't extend the same gate
  to `move`/`resolve`/the future `add`.

## Open Questions

- Should `stage` gain a `--as`/claimant argument so the check can verify
  *this specific caller* holds `GIT-COMMIT`, not just that *someone*
  does (closing the residual gap where a non-holding thread could still
  stage while a *different* thread holds the lock)? Recommend as a
  follow-up, not blocking this fix — the existence check alone already
  closes the concrete incident (staging with the lock fully unclaimed by
  anyone), and adding a required new argument changes `stage`'s calling
  convention for every existing caller/doc reference.
- Should `move`/`resolve` eventually get a *softer* signal (a warning,
  not a refusal) when `GIT-COMMIT` is unclaimed, short of the hard gate
  `stage` now has? Recommend no for now — no incident motivates it, and
  a warning nobody reads is exactly the kind of advisory theater this
  scaffold has tried to avoid; revisit only if a real incident traces
  back to `move`/`resolve` specifically.

## Done

- Added a check at the top of `cmd_stage` (before scope/missing-on-disk
  validation): refuses with a clear message naming the fix if
  `read_lock("GIT-COMMIT")` is `None`.
- Updated the module docstring (new "Extended for TASK-0154" paragraph)
  and `CAPABILITIES.md`'s `repo.commit.stage` row to document the new
  precondition and why it's scoped to `stage` alone.
- Validated (isolated scratch git repo, mirroring the actual claim ->
  commit-guard -> stage -> commit -> release workflow):
  1. `stage --expect <path>` with `GIT-COMMIT` unclaimed -> refused,
     clear message, index untouched (confirmed via `commit-guard
     --expect-empty` still passing after the refusal).
  2. Same call after `claim GIT-COMMIT` -> succeeds exactly as before.
  3. `stage`'s existing scope restriction (`.ai/`/`.claude/` only) still
     refuses an out-of-scope path even with the lock held -- unaffected
     by this change, just gated behind the new precondition.
  4. `move`, `resolve`, `scq-enter` all still succeed with `GIT-COMMIT`
     unclaimed -- confirms the stage-only scope decision actually holds
     in the implementation, not just in the design doc.
  5. Full workflow smoke test end to end: `claim` -> `commit-guard
     --expect-empty` -> `stage` -> `commit-guard --expect` (both match
     and mismatch directions, extra-staged and missing-expected) ->
     `git commit` -> `release` -- all unchanged from before this task.
  6. Also re-confirmed the `GIT-COMMIT` override-guard chain unrelated to
     this task's own change (plain claim refused while held; `--force`
     alone refused; `--force --reason` without `--hitl-override`
     specifically refused for `GIT-COMMIT` but *not* for a plain
     `TASK-XXXX` claim, confirming the stricter gate is correctly scoped
     to `SPECIAL_RESOURCE_IDS` only) -- pre-existing behavior, unchanged,
     confirmed still correct while verifying this fix.
- Filed per explicit user finding, not a hypothetical: nothing in
  `stage`/`move`/`resolve` referenced `GIT-COMMIT` at all before this
  change (`grep -n "GIT-COMMIT" .ai/tools/claim.py` confirmed zero hits
  in any of the three functions).
