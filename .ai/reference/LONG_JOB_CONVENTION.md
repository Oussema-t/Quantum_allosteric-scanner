# Long-Job Convention

Filed by [[TASK-0134]] Part 2, raised directly by the orchestrating user
([[P-0005]], `.ai/memory/shared/pitfalls.md`): "I am unsure if the
possibility of a 'computer went to sleep mode, was woken up after 1.5hrs,
restarted computing' option was ruled out... this kind of risk — not
properly assuring how much compute IS being consumed — is the ether of
this project." This document is the reusable answer, generalized beyond
the one claim ([[TASK-0110]]) that prompted it.

## When this applies

Any compute expected to exceed a practical in-session attention span —
this project's own working threshold is **~10-15 minutes**: below that,
just block synchronously and wait; above it, use the pattern below. This
threshold isn't arbitrary — it matches the Bash tool's own default
120-second timeout (already too short for a lot of this project's real
runs, e.g. `TASK-0105`'s multi-minute-per-gamma ENAQT sweeps) and the
point past which a thread checking back via a tight polling loop starts
wasting more effort than the job itself.

## The two failure modes this prevents

1. **Blocking synchronously and declaring infeasibility when the
   session's own patience runs out** — [[TASK-0110]]'s original
   situation: a single process-state check (`R`, "genuinely computing")
   at the moment a job was killed proves activity *at that instant*, not
   continuous execution across the whole elapsed interval. A real
   contention/suspension event between checks would have looked
   identical from the outside.
2. **Not attempting a long job at all**, because no thread considered
   handing it off — the job never runs, and "we don't know" gets
   reported as if it were "infeasible."

## The default pattern

1. **Instrument before launching**, not after — `allostery.runlog.
   RunLogger` (TASK-0135, built with this exact convention in mind).
   Sample periodically (every N units of work, or every fixed wall-clock
   interval, whichever is more natural for the job) — a `run_start`
   header (environment fingerprint) plus one `step()` record per sample,
   flushed and fsync'd immediately so a killed or crashed job still
   leaves a usable trace, not just a final summary.
2. **Run detached, not blocking the calling thread.** Two distinct
   detachment mechanisms, matched to two distinct time horizons — do not
   conflate them:
   - **Harness-tracked background execution** (this environment's own
     `run_in_background`, or equivalent) for anything expected to finish
     within the current session's own working span (minutes to a couple
     hours) — the thread gets a completion notification automatically
     and can keep doing other useful work meanwhile (exactly how this
     task's own Part 1 re-verification was run: launched, worked on Part
     2 in parallel, picked back up on notification). **Cheap, but tied to
     this session/process's own lifetime** — if the session ends, the job
     may not survive it (implementation-dependent; do not assume it does
     for anything long enough to matter).
   - **OS-level detachment** (`nohup ... > log 2>&1 & disown`, or a
     `tmux`/`screen` session) for anything expected to outlast a single
     session (many hours+) — survives the controlling process/session
     ending, which harness-tracked background execution is not
     guaranteed to do. This is the mechanism genuine HITL hand-off (below)
     needs.
3. **Monitor by reading the log file's tail, never by blocking on the
   process or polling it in a tight loop.** Checking back is itself
   cheap (`tail -20 results_taskNNNN/run.jsonl`); a synchronous wait or a
   sub-minute polling loop is not — see `ScheduleWakeup`'s own guidance
   in this environment: match check-back cadence to how fast the state
   you're watching actually changes, never poll faster than that just to
   "be sure."

## The diagnostic this task's own Part 1 found, and got wrong on the first pass

**CPU-time exceeding wall-clock is normal, not evidence of anything —
this is the opposite direction from what a naive reading of "compare
CPU-time to wall-clock" suggests, and worth stating explicitly since it
is easy to get backwards.** `time.process_time()` (what `RunLogger` uses)
sums CPU-seconds across *every thread* of the process. Any multithreaded
BLAS call (which is most of this project's own numerical code, unless
explicitly capped via `OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/etc.)
naturally produces `cpu_elapsed_s` several times larger than
`wall_elapsed_s` — this task's own first scratch check (uncapped,
16-core machine) measured a **~16x ratio**, matching the core count
almost exactly, not a bug or a sign of anything unusual.

**The real diagnostic for contention/suspension is ratio *stability*
across successive samples, not the ratio's absolute magnitude.** A
process genuinely computing without interruption (single- or
multi-threaded) produces a roughly *constant* `cpu_elapsed_s /
wall_elapsed_s` ratio from one `step()` sample to the next. A
suspension/contention event (the sleep-mode scenario [[P-0005]] raised,
or the process simply getting starved of CPU by something else on a
shared host) shows up as a *drop* in that ratio between two consecutive
samples — wall-clock keeps advancing while CPU-time stalls. Check the
**sequence** of per-step ratios in a `RunLogger` JSONL trace, not a
single before/after comparison.

**Match the BLAS thread cap to whatever the original/comparison run
used**, or the ratio comparison is not apples-to-apples. This project's
own established real-target-script convention
(`os.environ.setdefault("OMP_NUM_THREADS", "4")` etc., set *before*
`import numpy`) exists for reproducibility reasons independent of this
finding — reuse it, don't invent a different cap per script.

## HITL hand-off

For a job expected to run well past any single session's practical span
(hours+): start it OS-detached (see above), and leave explicit,
self-contained instructions for whoever checks back next — human or a
later agent thread — covering:
- the exact command that was run and where its log file lives,
- what "done" looks like in the log (a `run_finish` record) vs. "still
  running, healthy" (a recent `step()` record with a plausible, stable
  cpu/wall ratio) vs. "stalled, needs attention" (no new `step()` records
  for far longer than the sampling interval, or a collapsed ratio),
- what to do with the result once it lands (which file/task to update).
Post these instructions somewhere durably visible — a note in
`.ai/COMMON.md`'s Active Work Registry (if a task is claimed against the
job) or a short `results_taskNNNN/HITL_CHECKBACK.md` file alongside the
job's own output, not only in a chat transcript that may not be read
again by anyone.

## Where this lives

This file, cross-linked from `.ai/reference/IMPLEMENTER_SPINUP_BRIEF.md`
(every implementer thread already reads that before its first commit)
and from `OPERATION_PROTOCOL.md`'s own artifact list. No new tool was
built for this — `allostery.runlog.RunLogger` (TASK-0135) and this
environment's own `run_in_background`/`ScheduleWakeup` primitives were
already adequate; this document generalizes an already-demonstrated
pattern (this Architect/Planner thread's own prior use of
`run_in_background` for a full test-suite run, checked for concurrent
contention via `ps aux` first) rather than building something new from
scratch, per this task's own In Scope allowance.
