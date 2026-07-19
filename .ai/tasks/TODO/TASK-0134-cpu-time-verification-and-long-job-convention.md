# TASK-0134 CPU-time re-verification of the `time_averaged_ctqw` infeasibility claim, plus a reusable long-job convention

## Context

- ID: TASK-0134
- Title: [[TASK-0110]]'s "a single `time_averaged_ctqw` call did not
  return after 2+ hours" claim (cited downstream by
  `.ai/invariants/INV-0005-propagator-time-parameters.md`, [[SEAM-0012]],
  and [[TASK-0130]]) was corroborated by process state (`R`, "genuinely
  computing, not hung") at the point it was killed, but not by CPU-time
  consumed over the interval. Process state at one checkpoint proves
  active scheduling at that moment; it does not prove continuous
  execution for the full elapsed wall-clock duration. Re-verify with
  real CPU-time instrumentation, and separately, propose a reusable
  convention for how this project's agent threads should run and
  monitor genuinely long compute jobs generally.
- Status: TODO
- Owner: Implementer / Toolsmith (two distinct pieces, see In Scope —
  claim both or split, state which in Done)
- Claimed By: —
- Claimed At: —
- Source: raised directly by the orchestrating user, 2026-07-18 — "I am
  unsure if the possibility of a 'computer went to sleep mode, was woken
  up after 1.5hrs, restarted computing' option was ruled out... this kind
  of risk — not properly assuring how much compute IS being consumed —
  is the ether of this project." Filed as [[P-0005]]
  (`.ai/memory/shared/pitfalls.md`) and an update to [[SEAM-0012]].
- Priority: **P2, downgraded 2026-07-19 — Part 1 is now largely moot.**
  [[TASK-0130]] replaced `time_averaged_ctqw`'s finite-time approximation
  with the exact closed form for every headline call path — the specific
  `t_max`/`n_steps` combination that produced the original "2+ hours,
  did not return" observation is no longer how this project computes
  this quantity, so re-verifying that exact historical multiplier has
  materially less value than it did when this task was filed (nobody is
  going to run that code path again in the way that produced the
  original number). **Part 2 (a reusable long-job/background-monitoring
  convention, including the HITL hand-off option) remains fully valid
  and independent of this** — general infrastructure, not tied to the
  specific claim that motivated it. Whoever picks this up should treat
  Part 1 as optional/historical-record-only and Part 2 as the actual
  remaining deliverable.

## Intent Contract

- Outcome, part 1 (re-verification): re-run the specific call TASK-0110
  made (real `time_averaged_ctqw` at the AAKV-prescribed `t_max`/
  `n_steps` on real KRAS_G12C data) with CPU-time logged continuously
  across the interval (`resource.getrusage(RUSAGE_SELF)` sampled
  periodically, or wrap with `/usr/bin/time -v` if invoked as a
  subprocess) — not just a single process-state check at kill time.
  Report wall-clock elapsed *and* CPU-seconds consumed side by side. If
  CPU-time tracks wall-clock closely (no long gaps), the original claim
  is corroborated as stated. If there's a large gap (CPU-time much less
  than wall-clock), that is direct evidence of contention/suspension
  during the run, and the "2+ hours" figure should be corrected
  wherever it's cited (additively, per this project's no-silent-
  overwrite convention) to state the real CPU cost instead.
- Outcome, part 2 (convention): propose and document a reusable pattern
  for this project's agent threads to run compute expected to exceed a
  practical in-session attention span (tens of minutes to hours) —
  default to detached/background execution with periodic CPU-time
  logging to a file the thread (or a later thread, or the orchestrating
  user) can check, rather than either (a) blocking synchronously in one
  session and declaring infeasibility when the session's own patience
  runs out, or (b) not attempting a long job at all because no thread
  considered handing it off. Explicitly include the human-in-the-loop
  option the user raised — a job expected to run past a session's
  practical span can be started and left running with instructions for
  a human to check back, not only auto-monitored by another agent
  thread. Where this belongs (a `.ai/tools/` wrapper, a documented
  pattern in `.ai/reference/OPERATION_PROTOCOL.md`, or elsewhere) is
  this task's own call — state the choice and why in Done.
- In Scope:
  - The CPU-time re-measurement itself (part 1) — real, on real data,
    not a synthetic proxy.
  - Correcting any downstream citation of "2+ hours"/the specific
    multipliers if the re-measurement finds a material gap between
    wall-clock and CPU-time.
  - A documented convention (part 2) — does not need new tooling built
    from scratch if an adequate pattern already exists in this session's
    own history (e.g. this Architect/Planner thread's own use of
    `run_in_background` for a full test-suite run, checked for
    concurrent contention via `ps aux` first) — capturing and
    generalizing an already-demonstrated good practice is in scope, not
    only building something new.
- Out Of Scope:
  - Re-litigating [[TASK-0130]]'s own recommendation (promote the
    closed-form limit) — unaffected by this task's outcome either way.
  - Re-measuring every other timing claim in this project's history
    (TASK-0105's ENAQT per-call costs, TASK-0068's NISQ Trotter-step
    timing, etc.) — flag them as candidates for the same scrutiny in
    Done if this task's own finding suggests they're at risk, but do not
    re-run all of them here.
- Constraints And Invariants: the re-measurement must run long enough to
  either reproduce the original non-completion or reach a real
  conclusion — do not truncate early and call the question re-opened
  rather than answered.
- Planned Validation: the CPU-time-vs-wall-clock comparison itself is
  this task's primary validation artifact; the convention (part 2)
  is validated by being concrete enough that a future thread could
  actually follow it without re-deriving the pattern from scratch.

## In Progress

None

## TODO

- [ ] Re-run TASK-0110's specific infeasibility-triggering call with
      continuous CPU-time logging, real data.
- [ ] Report wall-clock vs. CPU-time side by side; state whether the
      original "2+ hours" claim is corroborated or was inflated.
- [ ] If inflated: correct `INV-0005-propagator-time-parameters.md`,
      `SEAM-0012`, and any task Done sections citing the specific
      multipliers, additively.
- [ ] Document a reusable long-job/background-monitoring convention,
      including the HITL hand-off option, in whatever location is the
      right fit (state the choice in Done).
- [ ] Flag (not re-run) any other timing-based feasibility claims in
      this project's history that share the same unverified-CPU-time
      risk.

## Dependency

- [[TASK-0110]] (Done) — the specific claim this task re-verifies.
- [[TASK-0111]] (Done) — the prior, independently-confirmed instance of
  the same confound class (contention inflating a different timing
  measurement in this same sandbox) — reuse its own "controlled,
  same-moment" measurement discipline as a template.
- Cross-referenced: [[P-0005]] (`.ai/memory/shared/pitfalls.md`),
  [[SEAM-0012]] (`.ai/seams/`).

## Open Questions

- Whether this environment is even capable of OS-level suspend/sleep at
  all (the user's specific hypothesized mechanism) — genuinely unknown;
  this task's own re-measurement doesn't need to answer that directly
  (CPU-time-vs-wall-clock is diagnostic regardless of which specific
  mechanism, sleep or contention, would explain a gap if one is found).

## Done

(not yet)
