# TASK-0065 Informational FIFO queue for `GIT-COMMIT`

## Context

- ID: TASK-0065
- Title: When `claim GIT-COMMIT` is refused because another thread holds
  it, let the refused thread opt into an ordered queue (a ticket number,
  visible position, and who's ahead) instead of a bare "already claimed"
  — visibility only, no ordering *enforcement*
- Status: TODO
- Owner: Toolsmith
- Claimed By: —
- Claimed At: —
- Source: direct request, this session, 2026-07-11 — design discussion
  following this thread's own live experience of `GIT-COMMIT` contention
  (waiting on another thread's Phase 3 review commit two turns earlier
  in this same session) and Q-0001's finding that the lock is advisory,
  not enforced. The immediate trigger for filing: the user, mid-request,
  pointed out this thread should check its own queue position before
  staging ("you are not first in queue") — the exact discipline this
  task's own design formalizes into a checkable state instead of an
  informal habit.
- Scope: extend `.ai/tools/claim.py`'s existing `GIT-COMMIT` handling
  (`claim`/`release`/`status`) with an opt-in queue. Does not change
  `commit-guard`, `stage`, `add` (TASK-0061), or `move`/`sync`.

## Intent Contract

- Outcome: a thread refused `claim GIT-COMMIT` can see exactly where it
  stands (ticket number, current holder, who's ahead) instead of just
  "already claimed" — and can choose to wait informedly rather than
  retry-storming the lock the instant it looks free, same as several
  threads racing a released lock today with no ordering signal at all.
- In Scope:
  - **Decided: visibility only, not enforcement.** `claim` still performs
    its normal `O_EXCL` attempt whenever the lock is free; nothing stops
    a thread *not* at the front of the queue from successfully claiming
    it first if it calls `claim` the instant it's released. Enforcing
    strict FIFO ordering (refusing an out-of-turn claim) is explicitly
    **not** built here — there is no concrete queue-jumping incident
    motivating it yet, only the mixed-attribution incident (Q-0001)
    visibility already addresses. Matches this scaffold's standing
    "advisory first, harden only after a real failure" precedent
    (TASK-0017→TASK-0024, TASK-0025's deferral, TASK-0028→TASK-0042) —
    building enforcement ahead of a failure would be the one place this
    session breaks that pattern for no demonstrated reason.
  - `claim GIT-COMMIT <claimant> --enqueue`: on refusal (lock already
    held), atomically allocate a ticket number and write a small queue
    entry (claimant, ticket, enqueued-at) instead of just printing the
    holder and exiting. `--enqueue` is opt-in and explicit — a thread
    decides once that it wants to wait; plain `claim GIT-COMMIT`
    (no `--enqueue`) keeps today's exact behavior (refuse, print holder,
    exit 1, no ticket). This avoids the alternative failure mode of a
    naive design (auto-enqueueing on every retry, producing a fresh
    duplicate ticket per poll from the same thread).
  - **Decided: reuse `reserve-next`'s existing atomic-allocation logic
    for ticket numbers, generalized to a namespace parameter — do not
    write a third allocator.** This is now the *third* proposed consumer
    of "give me a race-safe next id in some space" this session
    (TASK-0060's `derive-task` reuses it for `TASK-XXXX` ids directly;
    TASK-0062 wants it generalized for `INC-XXXX` incident ids; this task
    wants it for ticket numbers). Whichever of TASK-0062/TASK-0065 lands
    first should do the actual generalization (a namespace/directory
    parameter on the existing highest-plus-one-with-retry function); the
    other consumes it rather than re-deriving the retry loop a third
    time. Flag this coordination point in both tasks' Dependency
    sections, not just here.
  - `claim.py status GIT-COMMIT` (and the no-argument full listing) shows
    the queue when one exists: current holder, then ordered
    ticket/claimant/enqueued-at entries for everyone waiting — so any
    thread can check the whole picture, not just its own position.
  - a ticket is automatically removed once that same claimant
    successfully claims `GIT-COMMIT` (whether or not they were at the
    front — see Decided above, this doesn't enforce turn order, it just
    clears a redeemed ticket).
  - **Decided: stale-ticket handling mirrors TASK-0017's existing claim-
    staleness convention** (no numeric TTL, advisory, "no activity for
    longer than one working session reads as stale") rather than
    inventing a new expiry mechanism — a thread or human noticing an
    old, clearly-abandoned ticket can remove it the same judgment-call
    way a stale task claim gets overridden today.
- Out Of Scope:
  - enforcing queue order on `claim` (see Decided above).
  - any change to `commit-guard`, `stage`, `add`, `move`, or `sync`.
  - a real blocking/wakeup mechanism — these are stateless CLI calls with
    no persistent process to notify; a queued thread still has to poll
    `status GIT-COMMIT` itself. This task only makes that polling
    informed (ordered, visible) instead of blind.
  - automatic ticket cleanup beyond the staleness convention above (e.g.
    a numeric TTL, a background sweep) — advisory/manual, matching every
    other lock in this scaffold.
- Constraints And Invariants:
  - Python stdlib only, no new dependency.
  - the queue's on-disk form stays plain and grep-able (small per-ticket
    files under `.ai/tasks/.locks/`, matching the existing lock-file
    convention — not a single JSON blob that reintroduces the whole-
    file-write race this scaffold has already had to fix once for
    `.ai/COMMON.md`).
  - must not change `claim`'s behavior for any caller that omits
    `--enqueue`, or for any resource id other than `GIT-COMMIT` (task-row
    claims are unaffected — this is `GIT-COMMIT`-specific for now; widen
    only if a second resource shows the same contention pattern).
- Planned Validation:
  1. Two threads: first claims `GIT-COMMIT` normally; second calls
     `claim GIT-COMMIT --enqueue`, confirm it's refused *and* reports
     ticket #1 with the first thread named as holder.
  2. A third thread also enqueues; confirm it reports ticket #2 and sees
     ticket #1 ahead of it in `status GIT-COMMIT`'s queue listing.
  3. First thread releases; second thread claims (without needing
     `--enqueue` again) — confirm its ticket is removed automatically on
     success.
  4. Confirm a thread that claims out of turn (skipping the queue
     entirely, or jumping ahead of an earlier ticket) still succeeds if
     the lock is free — proving this is genuinely advisory/visibility-
     only, not silently-added enforcement.
  5. Confirm plain `claim GIT-COMMIT` (no `--enqueue`) on a held lock
     behaves byte-identical to today — no ticket created, same refusal
     message shape as before, unless explicitly opted in.

## Dependency

- [TASK-0045](../DONE/TASK-0045-highest-task-lookup-tool.md) (Done) —
  `reserve-next`'s allocation logic, generalized (not duplicated) for
  ticket numbers.
- [TASK-0062](TASK-0062-incident-reporting-registry.md) (TODO, unclaimed)
  — the other pending consumer of the same generalization; coordinate so
  only one of these two tasks actually does the `reserve-next`
  generalization work.
- [TASK-0042](TASK-0042-hook-enforced-commit-gate.md) (TODO, unclaimed) —
  this queue's value compounds once commits are hook-enforced rather
  than advisory: a blocking hook can surface queue position on denial,
  which is a much stronger reason to have built this than today's purely
  voluntary check. Not a hard dependency (this task stands alone), but
  implement with awareness that TASK-0042 is the natural next consumer of
  the queue-visibility data this task produces.
- `.ai/memory/questions/toolsmith/answered/Q-0001-*.md` — the incident
  that first surfaced `GIT-COMMIT`'s advisory-only nature; read its
  Answer section so this task's own "visibility, not enforcement" framing
  doesn't quietly contradict that reasoning.

## Open Questions

- Should `status GIT-COMMIT`'s queue listing be included by default, or
  only on an explicit flag (e.g. `--show-queue`) to keep the common-case
  output unchanged? Recommend included by default when a queue exists,
  suppressed (today's exact output) when it doesn't — no flag needed for
  the common empty-queue case, which is most calls.
- Exact refusal message wording/shape for the `--enqueue` case — left to
  the implementer to match `claim`'s existing refusal-message style
  rather than specified in the abstract here.

## Done

(not yet)
