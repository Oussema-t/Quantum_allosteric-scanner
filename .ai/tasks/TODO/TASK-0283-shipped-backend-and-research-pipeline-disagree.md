# TASK-0283 — The shipped backend and the research pipeline disagree on KRAS's P@5, and the submission must quote one number

- Status: TODO
- Assignee: unassigned (suggest Implementer A — surfaced it in TASK-0282)
- Priority: **Highest — a Phase 1 deliverable figure currently has two values and no stated provenance**
- Filed: 2026-08-28 by Reviewer
- Related: [[TASK-0282]], [[TASK-0184]], [[TASK-0270]], [[TASK-0263]], [[TASK-0130]]

## The discrepancy

[[TASK-0282]] recomputed our residue-ranking top-5 under this task family's own
**single pre-registered GAUGE operator** (`H_new` / `ctqw_converged`,
incoherent — the same operator its `CTQW-in-wrapper` arm uses) and got
**P@5 = 0.000** on KRAS_G12C. The Reviewer's own measurement from the shipped
`results/KRAS_G12C/hit_list.json` gives **P@5 = 0.200** (one hit, residue 60).

Both are correctly computed. **The deployed backend selects a different
Hamiltonian gauge than the register's fixed one**, and nobody has decided
which is the pipeline of record.

[[TASK-0282]] handled it correctly for its own purposes — it used the *cited*
(0.200) number, which made its own swept rule look **worse** on KRAS (0.071 vs
0.200), and flagged the discrepancy rather than silently choosing the
favourable figure. That was the right call and this task is not a criticism of
it. But the underlying inconsistency is unresolved, and it is now load-bearing.

## Why it is load-bearing

**This is a Phase 1 deliverable number.** §5 requires the top-5 hit list;
[[TASK-0184]] will quote its accuracy. Quoting 0.2 when the pre-registered
operator gives 0.0 — or the reverse — with no stated provenance is exactly the
class of defect this register has caught three times already in other people's
numbers ([[TASK-0239]] stale triplets, [[TASK-0270]] wrong genotype,
[[TASK-0155]]'s mislabelled pool). It would be worse to ship one of our own.

## Scope

- [ ] Establish **which operator the deployed backend actually uses** for the
      hit list, and why it differs from the register's fixed GAUGE. Read the
      code path, do not infer from the numbers.
- [ ] Determine whether this is (a) a deliberate, documented consensus/sweep
      choice in `run_challenge.py` — the file's own comments mention a
      consensus-across-operators hit list distinct from the single-operator
      matrix — or (b) drift that nobody intended.
- [ ] **If (a)**: document it plainly, state that the register's headline AUCs
      and the shipped hit list come from different operators, and make sure
      [[TASK-0184]] never places the two side by side without saying so.
- [ ] **If (b)**: fix it, re-run all three mandatory targets, and report the
      corrected P@5 old-vs-new the way [[TASK-0270]] handled the KRAS genotype
      swap.
- [ ] Check whether the same divergence affects **BCR_ABL1** and
      **CARDIAC_MYOSIN** — both currently read 0.000 from both routes, which
      may be coincidence rather than agreement.
- [ ] Check whether it affects the **N×N connectivity matrix** deliverable
      too, not just the hit list. `run_challenge.py`'s own comments state the
      matrix uses "the consensus operator with the highest total" while the
      ranking is "the actual consensus-across-operators output" — if the two
      deliverables come from different operators, that needs saying in the
      methodological report.
- [ ] Fix **one number of record** for each mandatory target, with its
      provenance written next to it, and hand that to [[TASK-0184]].

## Acceptance

- [ ] A written answer to "which operator produces the shipped hit list, and
      is that deliberate?"
- [ ] One P@5 per mandatory target, with provenance, ready to quote.
- [ ] An explicit statement of whether the matrix and hit-list deliverables
      share an operator.
- [ ] `RESULTS.md`; and a line to [[TASK-0184]] so the draft quotes the agreed
      figure.

## Constraint

Resolve this on **provenance**, not on which number is higher. The favourable
figure (0.200) is the one currently shipping and the one the Reviewer quoted
first; the pre-registered operator gives 0.000. If the honest answer is that
our best-documented operator scores zero on all three mandatory targets, that
is what the submission says.
