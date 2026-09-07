# TASK-0345 — Measure the apo vs stripped-holo delta: the number nobody reports

- Status: TODO
- Owner: **Implementer** — triggerable unattended
- Priority: High — it converts a submission row from "not reported" into a result
- Filed: 2026-09-07 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0329]], [[TASK-0331]], [[TASK-0320]], [[TASK-0305]]
- Feeds: `PHASE1_SUBMISSION_V2` §2 component (b) and the §4 impact table

## The claim being tested

Leading cryptic-pocket methods report 89.8% / 98.1% on ASBench / CASBench. Those
evaluations run on **ligand-removed holo** structures, not on genuine apo
depositions. Removing a ligand does not close a pocket — the side-chain
conformation stays open — so a method scored that way is being handed a pocket
that a real apo structure would not contain.

**We have found no report of the delta between the two.** If it is large, every
published cryptic-pocket accuracy number is measuring an easier task than the
one the field believes it is measuring. That is the single most transferable
result available to us before Phase 2, and it is cheap.

## Why it is cheap — measured, not estimated

Timed in this repo against the vendored binary: **5.43 s per fpocket run** on
cached structures. 100 pairs × 3 states = 300 runs ≈ **27 minutes of compute**.
PDB fetches dominate the rest and many are already cached.

The pairs exist: the unified 1233-protein benchmark identified **1042 clean
apo→holo pairs** (CryptoBench / CryptoSite / PocketMiner). These carry no active
site — irrelevant here, because this measurement needs only the pocket, not a
seed. **The cohort that was useless for propagation is exactly the right cohort
for this.**

## Intent Contract

- Outcome: for ≥ 100 apo/holo pairs, pocket detection scored in three states —
  **(1)** genuine apo, **(2)** holo with ligand stripped, **(3)** holo as
  deposited — at the annotated site. Report the (2) − (1) delta: this is the
  headline. Report (3) as the ceiling.
- Metric: fpocket druggability and cavity rank at the annotated site, plus a
  binary "site detected at all". Reuse `task0242.fpocket_candidates` — same
  vendored binary, same `(chain, resnum)` keying as every other result here; do
  not write a second parser.
- Constraints And Invariants:
  - **Cluster by protein and report cluster-robust statistics**, not per-structure
    — this register has lost four selection procedures to pseudo-replication and
    one recent result to exactly this ([[TASK-0337]]).
  - State the ligand-stripping rule precisely: HETATM removal is not
    apo-isation, and [[TASK-0329]] measured that stripping changes fpocket
    druggability in both directions (1DKU 1.000 → 0.427; 1B86 0.460 → 0.962).
    **That variance is part of the finding**, not noise to average away.
  - Deterministic seeds and a fixed structure list written to disk before the
    run, so the cohort cannot drift between re-runs.
  - If the delta is ~zero, **say so** — that is equally publishable and it
    retires our own §2(b) proposal rather than embarrassing us in Phase 2.
- Planned Validation: a handful of pairs scored by hand against the automated
  output before the full run. And a positive control: state (3), deposited holo,
  must score highest of the three; if it does not, the scoring is wrong.

## Note

This is the one experiment in the current plan whose result is interesting
whichever way it lands, and whose cost is under an hour. It should run first.
