# TASK-0220 `quantum_seed_readiness`'s SAFE verdict never fires on real benchmark data

## Context

- ID: TASK-0220
- Title: across all 5 currently-loadable `verified=True` `systems.py`
  targets, `quantum_seed_readiness`'s verdict is never `SAFE` (4x
  `PARTIAL`, 1x `RISKY`) — is the `SAFE` threshold combination
  (`frac >= 0.60 AND distal_enrich >= 1.2`) miscalibrated against real
  protein data, or is `PARTIAL` actually the honest, correct answer for
  every real target checked so far?
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: observed incidentally while validating [[TASK-0033]] (which
  confirmed the threshold *values* are deliberately fixed constants, not
  a hardcoding bug — this task is about whether those specific values,
  0.34/0.60 on `frac` and 0.5/1.2 on `distal_enrich`, are well-calibrated,
  a distinct question TASK-0033 explicitly did not investigate, per its
  own Out Of Scope), 2026-08-16.
- Priority: **P2** — not a correctness bug (nothing crashes, nothing
  returns a wrong shape), but a real risk that the `SAFE` verdict is
  either unreachable in practice (dead code path, misleading to a user
  who might infer "unlikely to occur" incorrectly as "cannot occur, don't
  worry about the UI for it") or the calibration is simply off for this
  benchmark set specifically.

## The numbers that motivated this (from TASK-0033's own validation run)

| target | N | verdict | frac_good | distal_enrich |
|---|---|---|---|---|
| KRAS_G12C | 169 | PARTIAL | 0.360 | 0.941 |
| BCR_ABL1 | 451 | PARTIAL | 0.440 | 0.819 |
| CARDIAC_MYOSIN | 950 | PARTIAL | 0.940 | 0.895 |
| PTP1B | 298 | RISKY | 0.000 | 0.775 |
| GLUCOKINASE (chain=A, see [[TASK-0219]]) | 448 | PARTIAL | 0.540 | 0.948 |

Note `distal_enrich` sits in a tight 0.775-0.948 band on every single
target — never once above the 1.2 `SAFE` bar, despite `frac_good` alone
clearing 0.60 on CARDIAC_MYOSIN (0.940). `SAFE` requires *both*
conditions jointly, so CARDIAC_MYOSIN still lands `PARTIAL` on
`distal_enrich` alone. Whether `distal_enrich >= 1.2` is even achievable
on a real elastic-network-based transfer matrix (as opposed to a
theoretical/synthetic case that concentrates unusually hard on distal
residues) is exactly the open question here.

## Intent Contract

- Outcome: a stated, evidence-based answer to whether `SAFE`'s threshold
  combination is reachable and well-calibrated on real protein data, and
  either (a) recalibrated thresholds with a stated derivation/rationale,
  or (b) confirmation that `PARTIAL`-as-the-real-ceiling is correct and
  expected, with a code comment/doc note saying so (mirroring
  [[TASK-0033]]'s own "explain, don't silently leave surprising" pattern)
  so a future reader doesn't mistake this for a live bug.
- Why required, not assumed: TASK-0033 confirmed the threshold *contract*
  (fixed vs. relative) is correct; it did not check whether the specific
  fixed *values* are calibrated against real data — genuinely open.
- In Scope:
  - Extend the 5-target sample (this task's own motivating table) to
    every currently-loadable target in `systems.py` (fix or work around
    [[TASK-0219]]'s GLUCOKINASE chain issue as needed to include it
    cleanly), and to `verified=False` targets too if that doesn't
    meaningfully change scope.
  - Characterize `distal_enrich`'s real achievable range: what would a
    genuinely "SAFE" active site's transfer-matrix distal-concentration
    look like, physically — is 1.2x enrichment over uniform a reasonable
    bar, or does the elastic-network-model math this project already
    uses structurally cap real proteins well below that (e.g. via a
    synthetic positive-control case constructed to have a real,
    deliberately strong distal-favoring seed, checked against the same
    function).
  - If recalibrating: derive the new threshold(s) from the real
    distribution observed (e.g. a percentile of the benchmark set's own
    `distal_enrich` values), not picked to make a specific target look
    good — same non-circularity discipline this project's research tree
    (`__WORK_IN_PROGRESS__`) already applies to its own thresholds.
- Out Of Scope:
  - Re-opening TASK-0033's own resolved question (fixed vs. relative
    contract) — that stays fixed/relative as resolved; this task is
    about the fixed values themselves, if fixed values are kept.
  - Redesigning `quantum_seed_readiness`'s underlying metrics
    (`frac`/`distal_enrich`'s own formulas) — calibration only.
- Constraints And Invariants: CLAUDE.md convention 4 — response shape/
  field names (`verdict`, `frac_good`, `distal_enrich`, etc.) must stay
  the same regardless of outcome.
- Planned Validation: re-run against every target before/after any
  threshold change; a synthetic positive-control case (a hand-built or
  planted seed known to genuinely concentrate distally) should land
  `SAFE` if the recalibrated thresholds are reachable at all — if even a
  constructed best-case can't clear them, that's strong evidence the
  bar itself, not just real proteins, is set wrong.

## TODO

- [ ] Extend the validation table to every loadable `systems.py` target.
- [ ] Build or identify a synthetic/positive-control case to test whether
      `SAFE` is reachable in principle, not just empirically absent so
      far.
- [ ] Decide: recalibrate, or confirm-and-document `PARTIAL`-as-ceiling.
- [ ] If recalibrating: implement, re-run full validation, document the
      derivation.
- [ ] If confirming: add the explanatory comment/doc note.

## Dependency

- [[TASK-0033]] — established the threshold *contract* (fixed, not
  relative) this task builds on; do not re-litigate that finding.
- [[TASK-0219]] — soft; fixes GLUCOKINASE's load failure, useful for a
  clean 5/5+ sample here but not a hard blocker (this task can proceed
  with `chain="A"` as a manual workaround the way TASK-0033 did).

## Open Questions

- Is there a real, labeled "known-good" active site anywhere in this
  project's benchmark set to calibrate against, or is `SAFE`/`PARTIAL`/
  `RISKY` inherently more of a heuristic triage signal than something
  with ground truth to calibrate to? If the latter, "confirm and
  document" (option b) may be the more honest outcome than inventing a
  calibration that looks precise but isn't backed by anything.

## Done

(not yet)
