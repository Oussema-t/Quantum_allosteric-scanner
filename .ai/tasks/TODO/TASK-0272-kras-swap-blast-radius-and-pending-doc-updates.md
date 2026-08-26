# TASK-0272 — Finish the KRAS swap: stale numbers still live in two documents, plus two flagged-but-unmade updates

- Status: TODO
- Assignee: unassigned (suggest Implementer A — mechanical, but it touches the submission draft)
- Priority: **High — the Phase 1 submission draft currently cites superseded KRAS numbers as current**
- Filed: 2026-08-26 by Reviewer
- Related: [[TASK-0270]], [[TASK-0250]], [[TASK-0257]], [[TASK-0258]], [[TASK-0263]], [[TASK-0245]], [[TASK-0246]], [[TASK-0247]], [[TASK-0239]]

## What [[TASK-0270]] already did — do not redo

The KRAS `4OBE → 4LDJ` swap was applied and propagated: `config/targets.yaml`
(verified — `apo_pdb: 4LDJ` with a dated comment), `backend/systems.py`,
`SOFTWARE.md`, `COMPETENCE_MAP.md`, `ARCHITECTURE.md`. KRAS's own named
figures were re-run old-vs-new: AUC 0.557 → **0.514**, diagnosis
`NO_FAILURE_DETECTED` → **`NO_SIGNAL_IN_APO`**, ENM validity 0.646 (PASS) →
**0.496 (MARGINAL)**, pocket-to-active-site min distance 1.32 Å → 1.31 Å.

## What is genuinely unaffected — verified, state it so nobody re-runs it

**`KRAS_G12C` is not in [[TASK-0243]]'s frozen set** (checked directly: not in
`config/candidate_targets_task0243.yaml`, and absent from
`part_a_shapley_attribution.json`, n=20). Therefore **none** of the following
need recomputation: [[TASK-0254]]'s Shapley attribution, [[TASK-0260]]'s
four-block P2Rank run, [[TASK-0263]]'s potential-terms result, [[TASK-0266]]'s
SASA control, [[TASK-0249]]'s composite-vs-CTQW comparison, [[TASK-0261]]'s
cluster-robust re-runs, or [[TASK-0269]]'s PocketMiner scoring. The headline
attribution numbers stand as published.

## What is still stale

### 1. `documentation/PHASE1_SUBMISSION_DRAFT.md` — cites superseded figures as current

Lines ~63, ~182, ~213 cite our quantum-observable AUC as **0.557–0.590** and
"(AUC 0.557)". **0.557 is the 4OBE number. The current value is 0.514**, and
the diagnosis changed to `NO_SIGNAL_IN_APO`.

Note the draft *already* discusses the 4OBE misannotation as a finding
(~line 161) — that section is correct and is now **stronger**, because the fix
is organiser-sanctioned and the consequence is measured. Keep the narrative;
correct the numbers beside it.

### 2. `documentation/CTQW_CONTRIBUTION_BRIEF.html` — an R1 baseline that no longer exists

Line ~363: *"KRAS_G12C regressed 0.646 → 0.472"* in [[TASK-0257]]'s R1 table.
**0.646 is 4OBE's ENM validity.** On 4LDJ the baseline is 0.496, so the R1
comparison for KRAS is now stated against a structure we no longer use.

### 3. [[TASK-0250]]'s ENM-validity counts shift

KRAS moves **PASS → MARGINAL**, so the 15-target distribution is no longer
6 PASS / 5 MARGINAL / 4 FAIL. Recount and correct everywhere that tally
appears — including [[TASK-0257]] R1's own baseline row, which used it.

### 4. Historical-record entries: annotate, do not overwrite

[[TASK-0245]] (9-target CV attribution), [[TASK-0246]] (hop anatomy),
[[TASK-0247]] (within-shell), [[TASK-0258]] (pocket taxonomy) all include a
KRAS row computed on 4OBE. Per `RESULTS.md`'s own no-silent-overwrite
convention these stay as historical artifacts — **add a dated pointer to
[[TASK-0270]]**, do not recompute or delete. Say explicitly whether any
conclusion in them depended on the KRAS row (the Reviewer's read: none did —
all four are multi-target medians — but check rather than inherit).

## Two flagged-but-unmade updates, unrelated to KRAS

- [ ] **[[TASK-0263]] flagged that `CTQW_CONTRIBUTION_BRIEF.html` §04 needs
      its result and did not make the edit** (brief ownership sat with
      [[TASK-0265]] for that batch). §04 currently understates the case: the
      brief does not yet carry *terms-block 0.751 vs CTQW 0.575, cluster-robust
      p=0.019*, nor CTQW's added-last **p=0.973** once its own potential terms
      are in the model. **This is the strongest single result in the brief's
      argument and it is missing.**
- [ ] **[[TASK-0269]]'s PocketMiner outcome** also belongs in §08 — a
      purpose-built cryptic predictor does **not** close the residual. That
      strengthens the section's existing argument for a cryptic-enriched
      target set.

## Acceptance

- [ ] Submission draft carries current KRAS numbers; the misannotation
      narrative kept and strengthened.
- [ ] Brief's R1 table corrected; §04 carries [[TASK-0263]]; §08 carries
      [[TASK-0269]].
- [ ] ENM-validity counts recounted wherever the tally appears.
- [ ] Dated pointers added to the four historical sections, with an explicit
      statement that no conclusion in them turned on the KRAS row.
- [ ] A single grep-check recorded in the task: no document presents a 4OBE
      figure as a current KRAS_G12C result.

## Constraint

The corrected KRAS number is **worse** — 0.514 and `NO_SIGNAL_IN_APO`, where
the old one was our only clean mandatory-target floor-clear. Report it as
plainly as the old one was reported. The submission's credibility rests on
having found and fixed this ourselves, not on the figure it produced.
