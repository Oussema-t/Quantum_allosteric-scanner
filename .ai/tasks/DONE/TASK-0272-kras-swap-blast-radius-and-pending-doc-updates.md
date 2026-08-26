# TASK-0272 — Finish the KRAS swap: stale numbers still live in two documents, plus two flagged-but-unmade updates

- Status: Done
- Assignee: Implementer C
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

- [x] Submission draft carries current KRAS numbers; the misannotation
      narrative kept and strengthened.
- [x] Brief's R1 table corrected; §04 carries [[TASK-0263]]; §08 carries
      [[TASK-0269]].
- [x] ENM-validity counts recounted wherever the tally appears.
- [x] Dated pointers added to the four historical sections, with an explicit
      statement that no conclusion in them turned on the KRAS row.
- [x] A single grep-check recorded in the task: no document presents a 4OBE
      figure as a current KRAS_G12C result.

## Constraint

The corrected KRAS number is **worse** — 0.514 and `NO_SIGNAL_IN_APO`, where
the old one was our only clean mandatory-target floor-clear. Report it as
plainly as the old one was reported. The submission's credibility rests on
having found and fixed this ourselves, not on the figure it produced.

## Done

**2026-08-26, Implementer C.**

### 1. `documentation/PHASE1_SUBMISSION_DRAFT.md`

New dated banner entry (2026-08-26, [[TASK-0270]]/[[TASK-0272]]) added
after the existing TASK-0229.006 entry, following this document's own
established convention (correct a historical changelog banner by *adding*
a new dated entry, not rewriting old narration in place — the precedent is
the existing "Correction, 2026-08-23" entry already in the file). Finding
5's own body text corrected in place (AUC 0.557-0.590 → 0.514, floor
0.530, now below floor, diagnosis `NO_SIGNAL_IN_APO`, with an inline dated
disclosure of the correction — matching Finding 4's own established
in-place-correction style, the precedent this task's own filing named).

**Finding 6 checked, not assumed stale**: its own "(AUC 0.557)" citation
is a *holo*-structure (6OIM) measurement — `void_score` computed directly
on the already-open drug-bound structure, per [[TASK-0229.005]]'s own Done
section text ("computed directly on the HOLO structure"). 6OIM is
unaffected by the apo swap and was independently re-verified genuine G12C
by [[TASK-0270]] itself. **Left unchanged** — the task filing's own
premise that this citation needed the same fix as Finding 5 does not
hold; recorded here as a real correction to the task's own filing, not
silently followed.

**A second stale table found by this task's own grep-check, not in the
original filing's named line list**: §2.5's own rank-of-known-site /
enrichment-at-k table (TASK-0229.001) carries KRAS_G12C's own 4OBE-era AUC
(0.557) and N (169). Flagged with an inline dated note, not silently
fixed — rank-of-known-site and enrichment-at-k were not among the
statistics [[TASK-0270]] re-ran on `4LDJ`, so no verified replacement
number exists; fabricating one would violate this register's own citation
discipline. A real, disclosed gap for a future task.

### 2. `documentation/CTQW_CONTRIBUTION_BRIEF.html`

§05's top ENM-validity stat-row recounted (6/5/4 → 5/6/4, dated caption
added). §05's R1 table **baseline row** recounted (6/4/4 → 5/5/4, since
KRAS_G12C's own PASS→MARGINAL move is a property of the corrected
structure, independent of R1). **The R1 experimental row itself, and its
own caption's "KRAS_G12C regressed 0.646 → 0.472" claim, were explicitly
NOT altered** — that specific heavy-atom-weighting measurement was never
re-run on `4LDJ`, so correcting it would require fabricating a number;
disclosed inline instead, per this register's own standing rule (see
[[TASK-0257]]'s own "Not done" precedent for exactly this kind of gap).

§04 gained a new "CTQW against its own ingredients" subsection carrying
[[TASK-0263]]'s own terms-block-vs-CTQW result (0.751 vs 0.575,
cluster-robust p=0.019) and its own added-last figure once potential
terms are in the model (median −0.4%, p=0.973) — flagged by [[TASK-0263]]
itself as "the strongest single result in the brief's argument" and
missing until now. §08's PocketMiner paragraph rewritten from "could not
be run this session" to [[TASK-0269]]'s own real, later outcome (added-
last median +0.4%, cluster-p=0.277, not significant; crypticity-
stratified the right direction for once, +7.0% cryptic vs +0.0% open, not
formally tested due to a straddling cluster) — strengthens, not weakens,
the section's own existing Phase-2 argument, exactly as [[TASK-0269]]
itself predicted it would.

### 3. Historical entries — dated pointers added, dependency checked not inherited

[[TASK-0245]] and [[TASK-0247]]'s own DONE files: checked directly, not
assumed. In both cases KRAS_G12C's own row is **not** the value that sets
the cited median (PTP1B occupies that rank in every table checked) — the
headline conclusions are not directly determined by the KRAS row, though
whether the *exact* median would move under a full recompute was not
tested (a real, stated limit on this check's own confidence, not silently
elided). [[TASK-0247]]'s own KRAS row is flagged separately as the single
most extreme value in one non-headline column (`ctqw − best geometry`
gap) — noted so a future reader does not over-generalise from it.
[[TASK-0246]]'s own DONE file: no per-target breakdown exists to check
against — noted as such. `task0258_allosteric_distance_taxonomy.py`'s own
docstring (TASK-0258 itself has no task file to annotate against, already
independently confirmed missing by another thread) gained a dated note:
its stored output predates the fix, but the script itself reads live
config (already updated) and would reproduce correctly if re-run; TASK-
0270's own re-measured distance for KRAS_G12C (1.32 Å → 1.31 Å) confirms
the category label this script assigns does not change either way.

### 4. Also found and fixed, beyond the task's own named scope

`documentation/WORKFLOW.md`'s "What this pipeline cannot do" bullet and
its own KRAS_G12C walkthrough both stated `4OBE` as the *current* apo and
N=169 — corrected (structure, N=170, three separate line occurrences) with
the real re-run numbers from [[TASK-0270]]. Its own stale "10
independently RCSB-verified true-G12C structures, median AUC 0.482" claim
was not merely marked stale but **dropped rather than repeated** — TASK-
0270's own Done section found 8 of those 10 were actually drug-bound, so
restating that specific number would perpetuate a second, independent
error alongside the genotype one.
`documentation/2026-08-26-organiser-clarifications.md` (the decision
record TASK-0270 itself was filed from) gained a short dated update note
pointing to the actual decision — kept as the historical record it is,
not rewritten.

### Grep-check (Acceptance's own explicit requirement)

`grep -rn "4OBE"` and `grep -rn "0.646"` across every live document
(`documentation/`, `SOFTWARE.md`, `ARCHITECTURE.md`, `COMPETENCE_MAP.md`,
`__WORK_IN_PROGRESS__/documentation/*.md`, `*.html`), re-run after every
edit above. **Result: every remaining hit is either the organisers' own
Challenge Statement (not ours to edit), a generic API-example PDB code
(`SOFTWARE.md`'s `/api/compare?apo=4OBE...` docs, `backend/`'s own example
code/tests — illustrative, not a benchmark-validity claim), or explicitly
dated/historical/disclosed text.** No live document presents a `4OBE`
figure as a current KRAS_G12C result.

### Not done

Two gaps found and disclosed rather than silently fixed or silently
ignored: (1) §2.5's rank-of-known-site/enrichment-at-k table needs its own
re-run on `4LDJ` — a new measurement, out of this doc-propagation task's
own scope; (2) the CTQW brief's own R1 heavy-atom-weighting experiment
needs re-running on `4LDJ` before its own KRAS_G12C regression claim can
be restated as current — also a new measurement, also out of scope here.
Both are real follow-ups, not silently absorbed into this task's own
closure.

**Script:** none — a document-propagation task, no new computation.
**Files touched:** `documentation/PHASE1_SUBMISSION_DRAFT.md`,
`documentation/CTQW_CONTRIBUTION_BRIEF.html`, `documentation/WORKFLOW.md`,
`documentation/2026-08-26-organiser-clarifications.md`,
`.ai/tasks/DONE/TASK-0245-cv-variance-attribution.md`,
`.ai/tasks/DONE/TASK-0246-hop-contribution-anatomy.md`,
`.ai/tasks/DONE/TASK-0247-is-ctqw-a-distance-score.md`,
`scripts/task0258_allosteric_distance_taxonomy.py` (all under
`__WORK_IN_PROGRESS__/` except the four `.ai/tasks/DONE/` files).
