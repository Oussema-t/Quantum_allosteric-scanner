# TASK-0248 — Reconcile the reference hypothesis register against the completed TASK-0229 family

- Status: Done
- Assignee: unassigned (suggest Knowledge Curator)
- Priority: **High — blocks TASK-0249; and the register is currently being cited as evidence of untested work that has in fact been done**
- Filed: 2026-08-24 by Reviewer
- Related: [[TASK-0229]] family (.001–.007, all DONE), `documentation/REFERENCES.md`

## Problem

`.claude/hypotheses/reference_register.md` still carries `STATUS: UNTESTED` (or
`PARTIAL`) on hypotheses that the [[TASK-0229]] family has since tested with
real runs on real structures. All seven subtasks are DONE and each produced a
real verdict:

| subtask | refs / hypotheses | outcome recorded in the task |
|---|---|---|
| .001 | [9] / H9 — negative-class validity | citation verified, metric question addressed |
| .002 | [10],[11] / H10, H11 — hardware routes | citations verified, both routes examined |
| .003 | [6] / H6 — multi-site answer key | ASD lookup live on 4 targets; **one genuine second site found (BCR_ABL1)**, other three single-site |
| .004 | [1] / H1 — Zheng NMA sampling | implemented against verified citation |
| .005 | [1]+[2] / H1, H2 — NMA + persistent homology | implemented against verified citation |
| .006 | [4] / H4 — Ensemble Allosteric Model | built, run on both TASK-0209-VALID targets, **real mixed result** |
| .007 | [15],[7] / H15, H7 — two-state ANM, non-equilibrium | both parts run; (a) fails own validation on whole structure, (b) clean negative |

`documentation/REFERENCES.md` **was** updated (ref 4 now `PARTIAL` with
[[TASK-0226]]'s numbers). `reference_register.md` was not. The two disagree.

This surfaced when the register was queried directly for which references
frame allostery as population sampling rather than signal propagation: it
returned H6/H4/H5/H9 as UNTESTED, which is wrong for at least H6, H4, H9.

## Scope

- [x] For each hypothesis section in `reference_register.md`, set STATUS from
      the actual outcome of the corresponding TASK-0229 subtask, citing it by
      `[[TASK-…]]` and date. Do not restate the result — link it.
- [x] Where a subtask tested only part of a hypothesis, say which part, and
      leave the remainder explicitly open with its own STATUS line. .006 and
      .007 both self-describe as partial/mixed — those need precise wording,
      not a blanket "TESTED".
- [x] Identify hypotheses with **no** TASK-0229 coverage at all. Current read:
      **H5** (MWC / concerted transitions / scope truncation) is the clearest
      case — it has only incidental mentions and no test. **H16.1** (GNM
      slow-mode minima mark functional sites) appears only partially covered.
      Confirm or refute this read against the task files, don't inherit it.
      **Confirmed H5 (both H5.1/H5.2), refuted the H16.1 description**: the
      register's own H16.1 is actually "GNM reproduces B-factors" (a
      model-validity check), not "slow-mode minima mark functional sites" —
      that claim is H16.2, and H16.2 **is** tested (via [[TASK-0226]], not
      any TASK-0229 subtask). H16.1 as the register actually defines it is
      also confirmed genuinely open. See Done.
- [x] Make the two files agree, or state explicitly why they differ and which
      is authoritative.

## Acceptance

- [x] No STATUS field in `reference_register.md` contradicts a DONE task.
- [x] A short table at the top of the register: hypothesis → status → task →
      date, so the next reader can see coverage without opening seven files.
- [x] An explicit list of genuinely-open hypotheses, which becomes the input to
      any follow-up test tasks.

## Constraint

The register is a review artifact and its authority comes from being current.
A stale UNTESTED is not a harmless omission — it caused this reviewer to report
tested hypotheses as untested to the user on 2026-08-24. Fix the mechanism, not
just the entries: state in the register how it is meant to be kept in sync.

## Done

**2026-08-24, Implementer D.**

Read all 7 [[TASK-0229]] subtask Done sections in full (not summaries), plus
[[TASK-0226]] — which turned out to be load-bearing and outside this task's
own literal "TASK-0229 family" framing, see below — before writing a single
STATUS line, per this task's own "don't restate, don't inherit" instruction.

**`reference_register.md` fully rewritten** (`.claude/hypotheses/
reference_register.md`), not patched line-by-line, since nearly every Tier
A/B hypothesis needed a status change: new "Coverage summary" table at the
top (hypothesis → status → task(s) → date, [[TASK-0229.001]]–[[TASK-0229.007]]
plus [[TASK-0226]]), a "How to keep this register in sync" section (this
task's own Constraint — a process rule for future tasks: update this
register in the same commit, or name the gap explicitly in the closing
task's own Done section, so staleness is `grep`-able rather than silent),
and per-hypothesis STATUS lines updated to link (not restate) the source
task, precisely worded per subtask where the result is partial/mixed:

- **H9** (ref 9): PARTIAL — conceptual claim confirmed untestable directly
  (as this register's own original framing anticipated, not a gap);
  response metrics (rank-of-known-site, enrichment-at-k) built and run,
  [[TASK-0229.001]].
- **H6.1**: still UNTESTED (no task addresses the unified-mechanism claim
  itself). **H6.2**: PARTIAL/TESTED, [[TASK-0229.003]] — 1 genuine second
  site found (BCR_ABL1/5DC4), 3/4 single-site, full union-key re-score
  flagged as that task's own remaining gap, not silently closed here.
- **H4.1**: TESTED via two independent measurements — the harmonic proxy on
  real targets ([[TASK-0226]], confirms the non-target estimate, 0.795
  vs. 0.773) and the genuine COREX EAM ([[TASK-0229.006]], real mixed
  result, ρ≈0.5-0.54 vs. propagation, neither pre-registered closure).
  **H4.2**: PARTIAL — escapes the confound on real targets but its own
  negative control did not reach significance (p=0.333, [[TASK-0226]]).
  **H4.3/H4.4**: still UNTESTED (c-Myc explicitly excluded from
  [[TASK-0229.006]] as unvalidatable, not silently run anyway).
- **H1**: TESTED, [[TASK-0229.004]] — beats the quantum arm's point
  estimate on KRAS_G12C, explicitly not counted as register-significant.
- **H2.1**: TESTED (pre-existing, [[TASK-0142]], not a TASK-0229 item).
  **H2.2**: TESTED — decisive negative, [[TASK-0229.005]] — the positive
  control itself fails on both VALID targets, apo-ensemble scoring
  reported as an explicit ungated diagnostic, not forced past the gate.
- **H7**: TESTED — clean negative on the independence test,
  [[TASK-0229.007]] part (b); a related-but-distinct steady-state
  quantity separately found confounded, [[TASK-0226]] (`transmission_E0`,
  explicitly not a test of ref 7's actual non-equilibrium claim).
- **H15**: TESTED — mixed, [[TASK-0229.007]] part (a): whole-structure
  variant fails its own pre-registered comparison, pocket-restricted
  variant passes that one comparison but not a clean 7-target separation.
- **H8**: TESTED, unchanged verdict, but **citation corrected**: the
  register cited "TASK-0210", which is this repo's own unrelated,
  already-completed task — the external drop that produced these numbers
  was re-indexed to [[TASK-0226]] on filing specifically to avoid that
  collision (confirmed via that task's own Context section, "re-indexed
  from ... TASK-0210_observable_family_confound"). Also **updated to the
  real-PDB retest number** ([[TASK-0226]]: 0.755±0.062, real targets) —
  the register was still citing the non-target-structure estimate
  (0.711±0.125) despite its own real retest existing in the repo.
- **H16.1**: confirmed genuinely open (see Scope note above — the task
  filing's own description of H16.1 named the wrong claim; corrected
  against the register's own actual text, not silently followed).
  **H16.2**: TESTED, same TASK-0210→[[TASK-0226]] citation fix as H8, and
  the real-PDB number is **materially different** from the non-target
  estimate the register still carried (0.496±0.193 on real targets vs.
  0.292±0.218 non-target) — real targets escape the confound *less*
  cleanly, a real reportable difference, not a refinement in the
  direction the register implied.
- **H10/H11**: TESTED (paper-level, matching this register's own original
  "cheap, scores under Feasibility" framing for exactly this kind of
  venue), [[TASK-0229.002]] — real per-target cut counts for H10,
  reinforcing `FAULT_TOLERANT_ONLY`; H11 the one route that clears the
  qubit-count bar under an explicitly unbuilt encoding.

**Genuinely open hypotheses, confirmed by direct search (`grep` across the
full task history for B-factor-correlation checks and MWC/Changeux/
concerted-transition mentions), not inherited from the register's own or
the filing task's own prior framing**: **H5** (both H5.1 and H5.2 — zero
coverage anywhere) and **H16.1** (GNM–B-factor model-validity check — zero
coverage anywhere, as defined by the register's own text, not the filing
task's description of it). These are named explicitly as the input to any
follow-up test task, per this task's own Acceptance.

**`documentation/REFERENCES.md` cross-check**: this task's own Problem
section says that file's ref-4 row was "updated... with TASK-0226's
numbers" — confirmed accurate on inspection (row 4 already cites both
[[TASK-0229.006]] and [[TASK-0226]] with the real retest number,
0.795±0.082). No edit needed there; the disagreement this task exists to
fix was entirely in `reference_register.md`, not in `REFERENCES.md`.

**Not done, and why**: the two remaining open hypotheses (H5, H16.1)
themselves — filing new test tasks for them is explicitly the *next* step
this task's own Acceptance sets up, not this task's own scope (a
reconciliation task, not a new-hypothesis-testing task). The Tier D
context/target-specific rows were left largely as-is (annotated where a
cross-reference was stale, e.g. [20][21]'s BCR_ABL1 myristoyl-occupancy
question is already independently resolved by TASK-0209's own Finding 2)
since none of them are named in this task's own Scope and none contradict
a DONE task.

Tests: none — documentation-only task, no `src/` code touched.

Artifacts: `.claude/hypotheses/reference_register.md` (fully reconciled).
