# TASK-0135 Reproducibility audit (is identical-seed output actually identical?) + a shared run-logging convention

## Context

- ID: TASK-0135
- Title: test, don't assume, whether this project's headline
  computations are numerically reproducible across repeated invocations
  given identical logical inputs and a fixed RNG seed — and separately,
  build a shared logging convention (per-step/per-sample compute time,
  environment fingerprint) so future runs are self-documenting instead
  of requiring after-the-fact reconstruction.
- Status: TODO
- Owner: Implementer / Toolsmith (two coupled halves, same split as
  [[TASK-0134]] — claim both or split, state which in Done)
- Claimed By: —
- Claimed At: —
- Source: raised directly by the orchestrating user, 2026-07-18, **explicitly
  framed as an untested hypothesis, not an assumed fact** — "a slightly
  different flavor of review fatigue... DO NOT TAKE IT FOR GRANTED... I am
  at the moment not really sure to what extent we are improving
  computations, and to what we are 'sampling'." Filed as [[INV-0008]]
  (`.ai/invariants/`).
- Priority: **P0.** This is upstream of trusting *any* "improvement" or
  "new best trial" comparison currently in flight — [[TASK-0130]]'s
  recompute, [[TASK-0131]]'s permutation null, and [[TASK-0116]]'s search
  upgrade all implicitly assume that re-running the same seeded
  computation twice gives the same answer. One confirmed counter-example
  already exists (see below); this task establishes whether it's an
  isolated near-degenerate-spectrum edge case or a real, general risk.

## Intent Contract

- **Part 1 — the audit (test the hypothesis).** Pick a small set of
  representative headline computations already reported in this
  project — at minimum: (a) `H_new`'s spectral gap on BCR_ABL1 (the
  already-confirmed discrepancy: `gap=0.0374` vs. `0.1933` on
  byte-identical input, [[TASK-0129]]/[[INV-0008]]), (b) `ceiling.
  ceiling_search`'s best trial on KRAS_G12C at a fixed `seed=7` (does the
  *same* 60-trial sequence reproduce the *same* best `S`?), (c)
  `optuna_scan`'s converged optimum at its own fixed `seed=7`. Re-run
  each **multiple times** (at minimum 3, ideally across different
  in-session and cross-session invocations, and — if controllable —
  different `OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS` settings, per this
  project's own existing thread-capping precedent in
  `run_challenge.py`/`sweep_operators.py`) and report: identical output,
  or a measured spread? If a spread exists, characterize its magnitude
  and, where feasible, correlate it with a candidate cause (thread count,
  concurrent host load per [[TASK-0111]]'s own precedent, spectral
  near-degeneracy per the existing BCR_ABL1 case) — root-cause where
  practical, but reporting "confirmed nonzero spread, cause undetermined"
  is a valid, honest outcome per this project's own convention, not a
  failure to hide.
- **Part 2 — the logging convention.** Design and land a shared,
  reusable logging pattern any of this project's real-compute scripts
  can adopt: (a) an environment fingerprint recorded once per run
  (BLAS library/version, thread-count env vars, numpy/scipy versions,
  RNG seed(s) used, hostname/session identifier if available); (b)
  per-step or per-sample timing (wall-clock *and* CPU-time, per
  [[P-0005]]/[[TASK-0134]]'s own finding that wall-clock alone is not
  sufficient) logged incrementally, not just a final summary, so a
  partially-completed or killed run still leaves a usable trace; (c) a
  stated, consistent file/format convention (e.g. one JSONL line per
  step, matching this project's own existing checkpoint-file precedent
  in `ceiling_search_batched.py`) so logs from different scripts are at
  least structurally comparable.
- Why both parts belong in one task: the audit (Part 1) needs Part 2's
  instrumentation to be *diagnostic*, not just confirmatory — "the
  numbers differ" is less useful than "the numbers differ and here is
  the environment fingerprint of each run," which is what actually lets
  a future thread root-cause a discrepancy instead of re-flagging it as
  another open mystery.
- In Scope:
  - Real re-runs, real data, on this project's actual code — not a
    synthetic stand-in.
  - If a real, non-negligible spread is confirmed: flag every task/
    document currently reporting the affected quantities as a bare
    point estimate without this caveat (`COMPETENCE_MAP.md`, `INV-0005`,
    `INV-0006`, others as found) — additively, per this project's
    no-silent-overwrite convention. Do not silently "fix" a headline
    number by picking one of the observed values.
  - The logging convention itself — concrete enough that a future
    script can adopt it without re-deriving the design (a small shared
    helper module, or a documented pattern, Implementer's call, state
    which and why in Done).
- Out Of Scope:
  - Re-running every headline computation in the project's history under
    the new logging — this task establishes the convention and tests a
    representative sample; broader backfill is a separate follow-up if
    Part 1 finds a real, general problem.
  - Fixing the root cause of any confirmed nondeterminism (e.g. forcing
    single-threaded BLAS, pinning a library version) — that is a
    consequence decision for whoever owns the affected task/quantity
    once this task's finding exists, not this task's own call to make
    unilaterally.
- Constraints And Invariants: any reproducibility claim this task makes
  must itself state how many repeat runs it's based on and under what
  conditions — the same discipline this task is enforcing on the rest of
  the project applies to its own output.
- Planned Validation: the repeat-run comparisons themselves are the
  validation; for the logging convention, a real script (at least one)
  actually adopting it, not just a spec written and unused.

## In Progress

None

## TODO

- [ ] Re-run BCR_ABL1's `H_new` spectral gap computation multiple times,
      identical inputs/seed; reconcile or characterize the existing
      0.0374/0.1933 discrepancy with real repeat-run data.
- [ ] Re-run `ceiling.ceiling_search` on KRAS_G12C at fixed `seed=7`,
      multiple times; report whether the best trial reproduces exactly.
- [ ] Re-run `optuna_scan` at fixed `seed=7`, multiple times; report
      whether the converged optimum reproduces exactly.
- [ ] Design and land a shared environment-fingerprint + per-step/
      per-sample timing log format; adopt it in at least one real script.
- [ ] If a real spread is confirmed anywhere: flag affected documents/
      tasks additively; do not silently pick a value.
- [ ] Update [[INV-0008]] with the actual finding (KNOB confirmed
      nonzero and characterized, or GAUGE confirmed negligible).

## Dependency

- [[TASK-0111]] (Done) — prior, related contention finding; reuse its
  own controlled-measurement methodology as a template.
- [[TASK-0134]] (TODO) — the CPU-time/wall-clock half of the same
  underlying "are we measuring what we think we're measuring" concern;
  coordinate rather than duplicate if picked up around the same time.
- Cross-referenced: [[INV-0008]] (`.ai/invariants/`).
- Feeds: [[TASK-0130]], [[TASK-0131]], [[TASK-0116]] — all three
  currently assume seeded reproducibility; this task's finding should be
  read before treating any of their own "before vs. after" comparisons
  as settled, if a real spread is confirmed.

## Open Questions

- Whether cross-session/cross-thread-count repeat runs are practically
  controllable in this sandbox at all (can this thread actually vary
  `OMP_NUM_THREADS` and re-invoke, or only observe whatever the ambient
  setting happens to be) — this task's own first practical constraint to
  discover, not assumed in advance.

## Done

(not yet)
