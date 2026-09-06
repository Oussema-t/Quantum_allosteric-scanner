# TASK-0335 — Scope-correct the standing CTQW negatives: they are stated wider than they were measured

- Status: TODO
- Owner: **Implementer D** (ran [[TASK-0331]]; knows which claims it undercuts)
- Priority: High — these claims are already in outward-facing documents
- Filed: 2026-09-06 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0331]], [[TASK-0320]], [[TASK-0325]], [[TASK-0327]], [[TASK-0329]], [[HYP-P21]], [[HYP-P18]]

## The problem

Four independent findings say this register's CTQW negatives were measured in a
regime where nothing could have succeeded — and the negatives are written down
without that regime attached:

| finding | source | consequence |
|---|---|---|
| the distal subset cannot detect **proximity itself** (median ρ +0.064, p=**0.89**) | [[TASK-0331]] | the distal claim is **untested**, not refuted |
| ~30% of benchmark "allosteric" pairs are covalently adjacent | [[HYP-P21]] | no distal signal exists to find |
| 40/40 sampled ASBench structures are ligand-open | [[TASK-0329]] | pockets pre-opened in the input |
| **ASBench is PASSer's training data** | [[TASK-0327]] | the comparator was fitted on the test set |

The supported claim is narrower than the written one. Stated precisely:
*on predominantly non-distal, ligand-open, comparator-contaminated benchmark
structures, at pocket selection, the CTQW sits at or below chance.* That is
still a real negative — it is simply not "the walk does not work".

## Intent Contract

- Outcome: every standing CTQW negative carries its measured regime. Sweep at
  minimum: [[TASK-0320]], [[TASK-0325]], [[TASK-0327]], [[HYP-P18]],
  `PHASE1_SUBMISSION_V1.{md,html}`, `REVERSE_CTQW_BRIEF.html`.
- Specific corrections owed:
  - [[TASK-0325]]'s "raw cavity size is the best selector at 17.1%" — measured
    on ligand-open pockets, which favours geometric methods. Caveat or retract.
  - [[TASK-0325]] recommended PASSer as the gate worth having. Still true, but
    it now needs the ASBench-training caveat from [[TASK-0327]].
  - [[TASK-0327]]'s "actively subtracting value" — hold until [[TASK-0334]]
    reports; it is an interpretation, not a measurement.
- Constraints And Invariants:
  - **Do not weaken a negative that is correctly scoped.** [[TASK-0328]]'s
    0/110 and 1/80 compact-null survivors, and [[TASK-0327]]'s held-out 8.9%
    vs 18.4%, are properly controlled and stand as written. This task adds
    denominators; it does not soften conclusions.
  - Anything edited in `documentation/` goes through `.ai/tools/doc_parity.py`
    on both twins in the same commit.
- Planned Validation: after the sweep, a cold reader of any one corrected claim
  must be able to state the cohort it was measured on without opening a second
  file.

## Note

The scope correction makes the Phase-1 story *stronger*, not weaker: "here is
the cohort defect that makes distal allostery currently untestable, measured
three independent ways" is a contribution. An unqualified negative is not, and
is the easier thing for a reviewer to take apart.
