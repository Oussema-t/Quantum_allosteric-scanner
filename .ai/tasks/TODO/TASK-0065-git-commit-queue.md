# TASK-0065 Stage-Commit-Queue (SCQ) — FIFO, gitignored, per-entry files

## Context

- ID: TASK-0065
- Title: A gitignored FIFO queue for the `GIT-COMMIT` resource — an agent
  proactively declares (not just on refusal) its intended file list and a
  prepared commit message, gets a ticket, and any thread can see the
  whole ordered queue — visibility only, no ordering *enforcement*
- Status: TODO
- Owner: Toolsmith
- Claimed By: —
- Claimed At: —
- Source: direct request, this session, 2026-07-11 — design discussion
  following this thread's own live experience of `GIT-COMMIT` contention
  and Q-0001's finding that the lock is advisory, not enforced.
  **Revised 2026-07-17** per a follow-up request: "consider a simple
  .gitignore'd file that would clearly implement a FIFO Stage-Commit-
  Queue (SCQ), where agents would enter their SCQ claim, list their
  files, prepare a commit message etc." — this reframes the original
  refusal-triggered ticket into a proactive, richer queue entry an agent
  publishes as soon as it knows what it intends to commit, not only when
  it's already been turned away.
- Scope: extend `.ai/tools/claim.py` with new `scq-enter`/`scq-leave`
  subcommands and fold the queue view into the existing `status
  GIT-COMMIT` output. Does not change `claim`/`release`/`commit-guard`/
  `stage`/`add` (TASK-0061)/`move`/`resolve` (TASK-0107)/`sync`.

## Intent Contract

- Outcome: any thread about to work toward a commit can publish, in one
  command, a ticket + its intended file list + a prepared commit message
  — so every other thread can see the whole ordered queue (who's ahead,
  what they're touching, roughly what they'll say) before it ever calls
  `claim GIT-COMMIT`, instead of learning about contention only at the
  moment of refusal.
- In Scope:
  - **Decided: visibility only, not enforcement — unchanged from the
    original design.** `claim GIT-COMMIT` still performs its normal
    `O_EXCL` attempt whenever the lock is free; nothing stops a thread
    not at the front of the queue from claiming it first. No concrete
    queue-jumping incident motivates enforcement yet. Matches this
    scaffold's "advisory first, harden only after a real failure"
    precedent (TASK-0017→TASK-0024, TASK-0025's deferral,
    TASK-0028→TASK-0042) — unchanged by this revision.
  - **Decided (revised): a standalone `scq-enter` subcommand, not a
    `claim --enqueue` flag.** The original design only let a thread
    enqueue *after* being refused. That's too late for the stated goal
    (maximum lead time for other threads) and conflates two different
    actions (attempting the lock vs. declaring intent). `scq-enter` is
    independent of `claim` entirely — callable any time a thread knows
    enough to describe its intended commit, whether or not `GIT-COMMIT`
    is currently held by anyone:
    ```
    claim.py scq-enter --as LABEL --files PATH [PATH ...] \
        --message TEXT [--message-file PATH]
    ```
    Multi-line/longer prepared messages go in a file written with the
    `Write` tool and passed via `--message-file` — never inline on the
    command line — same quoting-fragility reasoning TASK-0061 already
    settled for batch manifests (`--message` stays for a short one-line
    summary shown in the queue listing; `--message-file`'s content is
    the full prepared message, read verbatim, not re-escaped).
  - **Decided: calling `scq-enter` again as the same claimant updates
    that claimant's existing entry in place (same ticket, new file
    list/message) instead of allocating a second ticket.** Replaces the
    original design's "don't auto-enqueue on every retry" concern with a
    cleaner rule: one live entry per claimant, re-declared as plans
    change, found by matching `claimant` across existing entries before
    allocating a new ticket.
  - **Decided: entries are per-ticket files, reusing the existing
    `.ai/tasks/.locks/*.lock` gitignore glob as-is — no new `.gitignore`
    line needed.** File name `SCQ-<ticket>.lock` (e.g.
    `.ai/tasks/.locks/SCQ-0001.lock`), same directory, same JSON-object-
    per-file shape as task/`GIT-COMMIT` locks (`claimant`, `ticket`,
    `entered_at`, `files`, `message`, `message_file` contents inlined).
    This directly answers the "simple .gitignore'd file" framing: it
    already exists, this task just adds a new filename pattern under it,
    not a new ignore rule. Confirmed current `.gitignore` line 32
    (`.ai/tasks/.locks/*.lock`) already matches this naming.
  - **Decided: one file per entry, not one shared queue file.** A single
    file holding every agent's queue entry would reintroduce the exact
    whole-file read-modify-write race this scaffold has fixed twice for
    `.ai/COMMON.md` (most recently TASK-0107's own validation, which
    found a live instance of a blanket write clobbering a concurrent
    thread's unrelated content) — two agents entering the queue at once
    would race on the same file. Per-ticket files sidestep this
    structurally: each entry is its own atomic `O_EXCL` create, exactly
    like every other lock file already does.
  - `scq-leave <ticket> --as LABEL`: explicit withdrawal (plans changed,
    already committed via a different bundling, etc.) — removes that
    one entry file. Refuses if `--as` doesn't match the entry's
    claimant, mirroring `release`'s existing claimant-mismatch handling
    (warn, or `--force` to override).
  - `claim.py status GIT-COMMIT` (and the no-argument full listing) shows
    the queue when one exists: current holder, then ordered
    ticket/claimant/files/message-summary/entered-at for everyone
    waiting — unchanged from the original design's intent, now richer
    per entry.
  - an entry is automatically removed once that same claimant
    successfully claims `GIT-COMMIT` (whether or not they were at the
    front — this doesn't enforce turn order, it just clears a redeemed
    entry) — unchanged from the original design.
  - **Decided: reuse `reserve-next`'s existing atomic-allocation logic
    for ticket numbers, generalized to a namespace parameter — do not
    write a fourth allocator.** Same coordination point as before, now a
    three-way shared need: `TASK-XXXX` (existing), `INC-XXXX`
    (TASK-0062), `SCQ-XXXX` (this task). Whichever of TASK-0062/TASK-0065
    lands first does the actual generalization; the other consumes it.
  - **Decided: stale-entry handling mirrors TASK-0017's existing claim-
    staleness convention** (no numeric TTL, advisory, "no activity for
    longer than one working session reads as stale") — unchanged from
    the original design.
- Out Of Scope:
  - enforcing queue order on `claim` (see Decided above) — unchanged.
  - any change to `commit-guard`, `stage`, `add`, `move`, `resolve`, or
    `sync` — unchanged. In particular, `scq-enter`'s file list is
    informational only; it does not stage anything itself and is not
    read by `stage`/`add`/`commit-guard` — an entry is a preview for
    other *agents* to read, not an input to any staging tool.
  - auto-executing a commit from a queue entry (e.g. a hypothetical
    `scq-commit <ticket>` that stages the listed files and fires the
    prepared message unattended) — flagged in Open Questions, not
    required here. Ship the informational queue first; an automated
    commit path is a much bigger trust/safety step (running someone's
    prepared message and file list without a human or fresh agent
    re-checking `commit-guard` immediately before) that needs its own
    real justification, matching this scaffold's incremental-hardening
    precedent.
  - a real blocking/wakeup mechanism — unchanged: stateless CLI calls,
    a queued thread still polls `status GIT-COMMIT` itself.
  - automatic entry cleanup beyond the staleness convention above —
    unchanged.
- Constraints And Invariants:
  - Python stdlib only, no new dependency.
  - one file per entry under `.ai/tasks/.locks/`, matching the existing
    `.lock` naming/gitignore coverage — not a single JSON blob.
  - must not change `claim`'s behavior for any caller or resource id —
    `scq-enter`/`scq-leave` are fully independent new subcommands, not a
    flag on `claim`. This is a stronger isolation guarantee than the
    original design (which modified `claim --enqueue`), reducing the
    risk of a regression in `claim`'s existing behavior to zero by
    construction (no shared code path to accidentally change).
  - entered file paths are recorded as given (repo-relative, caller's
    responsibility) — this task does not validate they exist on disk or
    resolve inside `.ai`/`.claude` (unlike `stage`'s scoping); it's a
    preview, not a staging boundary, so over-validating it would just be
    extra friction on a purely informational field.
- Planned Validation:
  1. Thread enters via `scq-enter --files a b c --message "..."`; confirm
     a ticket is allocated and `status GIT-COMMIT` shows it (ticket,
     claimant, files, message, entered-at).
  2. A second thread enters; confirm a distinct ticket, listed after the
     first, and that the first entry is unaffected.
  3. First thread calls `scq-enter` again with a changed file list;
     confirm the *same* ticket is updated in place, not a new one
     allocated, and the queue listing reflects the new file list.
  4. First thread proceeds to `claim GIT-COMMIT` and succeeds; confirm
     its SCQ entry is automatically removed, the second thread's is not.
  5. Confirm a thread that claims `GIT-COMMIT` out of turn (never
     entered the queue, or entered after the current front-of-queue
     thread) still succeeds if the lock is free — proving this stays
     advisory/visibility-only.
  6. `scq-leave <ticket> --as <claimant>` removes an entry without ever
     touching `GIT-COMMIT` itself; confirm claimant-mismatch is refused
     the same way `release` refuses one today.
  7. Confirm no new `.gitignore` line was needed — `git status
     --ignored` shows `SCQ-*.lock` files already excluded by the
     existing `.ai/tasks/.locks/*.lock` line.

## Dependency

- [TASK-0045](../DONE/TASK-0045-highest-task-lookup-tool.md) (Done) —
  `reserve-next`'s allocation logic, generalized (not duplicated) for
  `SCQ-XXXX` ticket ids.
- [TASK-0062](TASK-0062-incident-reporting-registry.md) (TODO, unclaimed)
  — the other pending consumer of the same generalization; coordinate so
  only one of these two tasks actually does the `reserve-next`
  generalization work.
- [TASK-0107](../DONE/TASK-0107-claim-resolve-subcommand.md) (Done) —
  read its Done section before implementing: found (live, during its own
  validation) that a blanket `git add .ai/COMMON.md` swept a concurrent
  thread's unrelated edits into the index, fixed with a surgical
  single-row stage. This task's own "one file per entry, never one
  shared queue file" decision is the same lesson applied to a gitignored
  file instead of a tracked one — the failure mode (concurrent
  read-modify-write on shared state) is identical regardless of whether
  git is involved.
- [TASK-0042](TASK-0042-hook-enforced-commit-gate.md) (TODO, unclaimed) —
  this queue's value compounds once commits are hook-enforced rather
  than advisory. Not a hard dependency.
- `.ai/memory/questions/toolsmith/answered/Q-0001-*.md` — the incident
  that first surfaced `GIT-COMMIT`'s advisory-only nature; read its
  Answer section so this task's "visibility, not enforcement" framing
  doesn't quietly contradict that reasoning.
- `.gitignore` line 32 (`.ai/tasks/.locks/*.lock`) — confirm the
  `SCQ-<ticket>.lock` naming lands inside this existing glob before
  writing any code; if the glob is ever narrowed (e.g. to a fixed-width
  numeric pattern) in the meantime, re-check it still matches.

## Open Questions

- Should `status GIT-COMMIT`'s queue listing show the full prepared
  message (from `--message-file`) or only the short `--message` summary,
  with the full text available via a separate `scq-show <ticket>`?
  Recommend summary-only in the default listing (keeps `status`'s output
  short even with several entries), full text on request via
  `scq-show` — cheap to add alongside `scq-enter`/`scq-leave` in the same
  implementation pass.
- Should entering the queue ever imply anything about `--as`'s identity
  matching a currently-claimed `TASK-XXXX` (i.e., can only enter if you
  hold a real task claim)? Recommend no — mirrors `stage`/`add`'s own
  looseness, and a single commit can legitimately bundle work from
  multiple claimed tasks.
- Worth the `scq-commit <ticket>` auto-execute path at all, ever, or is
  that permanently out of scope until TASK-0042's hook-enforced gate
  exists (at which point "safe to auto-fire" has a very different
  meaning)? Recommend leaving fully open — flagged in Out Of Scope,
  revisit only if manually re-typing a prepared commit message turns out
  to be a real recurring friction point once this ships.

## Done

(not yet)
