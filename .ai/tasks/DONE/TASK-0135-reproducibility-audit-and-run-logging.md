# TASK-0135 Reproducibility audit (is identical-seed output actually identical?) + a shared run-logging convention

## Context

- ID: TASK-0135
- Title: test, don't assume, whether this project's headline
  computations are numerically reproducible across repeated invocations
  given identical logical inputs and a fixed RNG seed — and separately,
  build a shared logging convention (per-step/per-sample compute time,
  environment fingerprint) so future runs are self-documenting instead
  of requiring after-the-fact reconstruction.
- Status: Done
- Resolution: done
- Owner: Implementer / Toolsmith (two coupled halves, same split as
  [[TASK-0134]] — claim both or split, state which in Done)
- Claimed By: Implementer C (this thread)
- Claimed At: 2026-07-19 12:42
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

- [x] Re-run BCR_ABL1's `H_new` spectral gap computation multiple times,
      identical inputs/seed; reconcile or characterize the existing
      0.0374/0.1933 discrepancy with real repeat-run data.
- [x] Re-run `ceiling.ceiling_search` on KRAS_G12C at fixed `seed=7`,
      multiple times; report whether the best trial reproduces exactly.
- [x] Re-run `optuna_scan` at fixed `seed=7`, multiple times; report
      whether the converged optimum reproduces exactly.
- [x] Design and land a shared environment-fingerprint + per-step/
      per-sample timing log format; adopt it in at least one real script.
- [x] If a real spread is confirmed anywhere: flag affected documents/
      tasks additively; do not silently pick a value.
- [x] Update [[INV-0008]] with the actual finding (KNOB confirmed
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

- **Resolved**: yes, `OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/
  `MKL_NUM_THREADS` are freely settable per-invocation in this sandbox
  (plain env-var prefix on the `python3` call) — used directly to test
  `1/2/4/8` on the spectral-gap case. Cross-session repeatability was
  also directly available: `ceiling_search`'s KRAS_G12C `seed=7` result
  from a prior session (2026-07-18, [[TASK-0116]]) reproduced exactly
  today, no special handling needed.
- **Resolved (Owner split)**: claimed [[TASK-0135]] only, per the
  orchestrating user's explicit "pick up task 135." [[TASK-0134]] (CPU-
  time re-verification of TASK-0110's specific "2+ hours" infeasibility
  claim) was left unclaimed — its own Part 2 (a long-job/background-
  monitoring convention) overlaps with this task's Part 2, so
  `allostery.runlog`'s `RunLogger` (wall-clock *and* CPU-time per step,
  directly addressing P-0005/TASK-0134's own "wall-clock alone is not
  evidence" finding) was deliberately designed generally enough to serve
  both tasks' logging need without duplicating the design later.
  TASK-0134's own Part 1 (the specific CPU-time re-verification of the
  "did not return after 2+ hours" claim) was not attempted here — a
  different specific claim than any of this task's three representative
  computations, left for whoever picks up TASK-0134.

## Done

**Part 1 — the audit.** Three representative headline computations, each
re-run at least 3 times, fresh process every time (no cached objects,
fresh RCSB fetch where applicable):

1. **`H_new`'s spectral gap, BCR_ABL1** (`build_H_new` at current
   defaults, `eigvalsh`, `metrics.spectral_gap`'s own definition —
   smaller of the two smallest non-negative eigenvalues' difference).
   3 fresh repeats: `gap=0.032949006294881435` exactly, every time
   (`scripts/reproducibility_audit.py --target BCR_ABL1 --repeats 3`,
   logged via the new `RunLogger` to
   `results_task0135/BCR_ABL1/spectral_gap_audit.jsonl`).
   **Then tested the specific hypothesized mechanism directly**:
   `OMP_NUM_THREADS`/`OPENBLAS_NUM_THREADS`/`MKL_NUM_THREADS` varied
   `1/2/4/8` (one fresh process per setting) — real variation exists,
   but only in the ~14th significant figure
   (`0.03294900629488051`-`0.03294900629488746`, spread ~7e-15
   absolute, ~2e-13 relative). Utterly negligible for any quantity this
   project reports to 3-4 significant figures.
2. **`ceiling.ceiling_search`, KRAS_G12C, `seed=7`, 60 trials** (blind
   random, `ceiling_search_batched.py`). 3 independent full 60-trial
   runs: one from [[TASK-0116]]'s own work the prior session
   (2026-07-18), two fresh today in separate checkpoint directories
   (`results_task0135/repro_check_A`, `repro_check_B`) — deliberately
   *not* resumed from a shared checkpoint, each a genuinely independent
   60-trial computation. All three: identical best trial,
   `S=0.4735`, identical winning `params` dict down to the last
   printed digit. Confirms reproducibility spans session boundaries,
   not just same-session repeat calls. (Side observation, not chased:
   per-trial wall-clock varied 5-10x across the three runs — 1.4-3.6s/
   trial on 2026-07-18 vs. 6-12s/trial today — consistent with
   concurrent host contention from this session's other active threads,
   exactly the effect [[P-0005]]/[[TASK-0134]] describes; the *numeric*
   result was unaffected by it, only the wall-clock time was.)
3. **`optuna_scan.apo_floor_scan`, KRAS_G12C, `seed=7`, 20 trials**
   (TPE, pure function over an in-memory `H_new`, no network needed per
   repeat). 3 fresh in-process repeats: `best_value=1895379886243.563`,
   identical `best_params`, every time.

**Conclusion: reproducibility holds.** No confirmed nonzero spread on
any of the three representative computations beyond utterly negligible
BLAS-thread-count floating-point noise (~1e-13 relative). [[INV-0008]]
closed as GAUGE (holds), not KNOB.

**The BCR_ABL1 gap discrepancy that motivated this whole task (0.0374
vs. 0.1933) is directly refuted as environmental**: the real,
measured thread-count effect (~1e-13 relative) is ~11 orders of
magnitude too small to produce a 5.2x discrepancy.
`REVIEW-panel-2026-07-17.md`'s "from BLAS reduction order" attribution
was an inference, not itself a controlled test (no thread-count-
variation methodology appears in that review) — now tested directly and
found wrong at the relevant magnitude. **Real, most-likely cause,
traced but not exhaustively pinned**: `0.1933` originates from
[[TASK-0102]]'s Done section (2026-07-13), which explicitly states it
"reused TASK-0091's cached `H_new`" rather than rebuilding it — a
snapshot from 5 days before [[TASK-0121]] changed `build_H_new`'s
`lam_*` defaults (2026-07-18), among possibly other intervening code
changes in that window. Directly tested both the pre- and post-
TASK-0121 `lam_*` defaults on fresh BCR_ABL1 data to check this
specific hypothesis: neither reproduces `0.1933` exactly (pre-TASK-0121
gives `0.00107`, current gives `0.0329`), so the *exact* single change
is not pinned — some other code difference across that 5-day gap is the
more likely explanation, not chased further past this point. This is
the honest "confirmed nonzero spread, cause undetermined [for the
original number specifically, though NOT environmental]" outcome this
task's own Intent Contract names as valid — and the number itself is
moot regardless, since [[TASK-0130]] deleted the gap-based clock
entirely in favor of the closed-form limit.

**Corrected additively** (per this project's no-silent-overwrite
convention): [[INV-0008]] (full rewrite of its GAUGE/SIGNAL/Status
sections with the real finding, Provenance section left as historical
record); `COMPETENCE_MAP.md` (two passages citing "BLAS reduction
order," both given a dated correction note pointing to this task's real
test, neither passage deleted).

**Part 2 — the logging convention.** New `src/allostery/runlog.py`:
`environment_fingerprint()` (BLAS thread env vars, hostname, PID,
python/numpy/scipy/optuna versions, timestamp) and `RunLogger` (JSONL,
one line per step, flushed + `os.fsync`'d immediately so a killed run
still leaves a usable trace — same discipline
`ceiling_search_batched.py`'s own pre-existing checkpoint file already
established, generalized into a reusable module rather than
re-invented per script). Every `step()`/`finish()` call records both
`wall_elapsed_s` (`time.monotonic()`) and `cpu_elapsed_s`
(`time.process_time()`, this process's own CPU time) since the logger's
construction — directly answers [[P-0005]]/[[TASK-0134]]'s own finding
that wall-clock alone cannot distinguish genuine computation from
contention/suspension; a growing gap between the two across steps is
itself the diagnostic signal for that risk.

**Choice of location (module, not a doc)**: a real importable module
was chosen over a documented-only convention because this project
already has independent evidence a documented-only pattern doesn't get
followed — the ad-hoc `def _log(msg): print(f"[{time.strftime(...)}]
{msg}", flush=True)` helper is copy-pasted, not shared, across 10+
scripts in `scripts/` today (`ceiling_search_batched.py`,
`fix_clock_operator_sweep.py`, `combined_competence_map_rerun.py`,
`ceiling_search_optuna_run.py`, and others) — a real module a script
can `import` is directly reusable and enforceable, not just
describable.

**Adopted in a real script**: new `scripts/reproducibility_audit.py` —
the actual tool that produced this task's spectral-gap numbers above —
uses `RunLogger` for its own environment fingerprint and per-repeat
timing (`results_task0135/<target>/spectral_gap_audit.jsonl`), not the
ad-hoc `_log` pattern. Confirmed the CPU-vs-wall-clock split is
meaningful in practice, not just in theory: on this run,
`cpu_elapsed_s` (4.6s cumulative) *exceeded* `wall_elapsed_s` (2.5s) —
correctly reflecting genuine multi-threaded BLAS parallelism (4 threads
capped), the healthy opposite of P-0005's contention-starvation
concern, and a real demonstration that the tool distinguishes the two
cases rather than just recording two numbers that happen to differ.

**Test coverage**: new `tests/test_runlog.py` (9 tests) —
`environment_fingerprint`'s expected keys/BLAS-var coverage/version
presence; `RunLogger`'s start/step/finish record shapes, parent-
directory creation, per-line JSON validity (a killed run must leave a
fully parseable partial trace — directly tests the P-0005 partial-run
requirement), monotonically non-decreasing elapsed time across steps.
Full suite: 724 passed (`../.venv/bin/python -m pytest tests/ -q -k
"not real_target and not real_run and not fetch and not
kras_g12c_real"`).

**Not done, flagged rather than silently skipped**: [[TASK-0134]]'s own
Part 1 (CPU-time re-verification of TASK-0110's specific "did not
return after 2+ hours" claim) — a different specific historical claim
than any of this task's three representative computations, left for
whoever picks up that task; `RunLogger` is ready for it to use directly.
Backfilling the new logging convention into this project's existing
compute scripts beyond `reproducibility_audit.py` is out of this task's
own scope (explicitly named in Out Of Scope) — a natural follow-up, not
attempted here.
