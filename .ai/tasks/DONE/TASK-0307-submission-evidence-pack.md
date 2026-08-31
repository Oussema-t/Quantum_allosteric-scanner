# TASK-0307 — Submission evidence pack: every number in TASK-0184, traced to a committed artifact

- Status: Done
- Assignee: Implementer D
- Priority: **Critical — the Phase 1 deadline is 2026-09-15 and this register's headline numbers have moved repeatedly in the last week**
- Filed: 2026-08-31 by Reviewer thread
- Related: [[TASK-0184]], [[TASK-0288]], [[TASK-0297]], [[TASK-0298]], [[TASK-0299]], [[TASK-0300]], [[TASK-0304]], [[TASK-0305]]

## Why

Numbers that were correct a week ago are now wrong, and several are quoted
in a brief already sent to the collaborator:

| quantity | was | now | moved by |
|---|---|---|---|
| pocket-level ceiling (in-sample) | 0.1649 | **0.0899** | [[TASK-0298]] |
| pocket-level ceiling (LOTO) | 0.122 | **0.0000** | [[TASK-0298]] |
| Finding F spike | 9/28, p=2.03e-06 | **8/28, p=1.51e-05** | [[TASK-0297]] |
| Finding F headline | "~32%" | **"~29%"** | [[TASK-0297]] |
| "classical ceiling beats CTQW" | claimed | **retracted** | [[TASK-0299]] |
| SVC figures | quoted | **withdrawn** | stability re-run, `34bf290` |
| KRAS P@5 | 0.200 | **0.000** | [[TASK-0283]] |

This register has already shipped a stale number once (the 0.200 P@5 in
the brief). It must not happen in the submission.

## Scope

- [x] Enumerate **every** quantitative claim destined for [[TASK-0184]]
      and the collaborator brief (`CTQW_CONTRIBUTION_BRIEF.html`).
- [x] For each: the current value, the **committed artifact** it comes
      from (path + commit SHA), and the task that last changed it.
- [x] **Flag every figure whose source artifact predates the commit that
      last invalidated it.** That is the actual deliverable — a stale-list.
- [x] Produce one table, committed, that the write-up can be checked
      against line by line.
- [x] Explicitly cover: Finding F (spike count, p, %, and whether stated
      on `min_A` or `max_A` — [[TASK-0291]] recommends `max_A`), the
      ceiling numbers, the CTQW comparison, the ASBench figures
      ([[TASK-0304]]/[[TASK-0305]]), and the attribution shares
      (geometry / CTQW / unexplained).

## Constraints

- **Verify, do not re-derive.** If a number cannot be traced to a
  committed artifact, that is the finding — report it, do not recompute a
  replacement and quietly substitute it.
- **Do not edit the brief or [[TASK-0184]].** This task produces the
  audit; applying it is a separate, deliberate step by whoever owns those
  documents.
- Where a claim's wording (not its number) is now wrong — e.g. "classical
  ceiling outperforms CTQW" — flag the wording too.

## Done (2026-08-31, Implementer D)

**Verify-only, per this task's own Constraint.** Neither
`PHASE1_SUBMISSION_DRAFT.md` nor `CTQW_CONTRIBUTION_BRIEF.html` was edited.

**Headline, established before tracing individual claims**: checked via
`git log` directly (not assumed from dates) — the draft's last commit is
`3b3be11` (TASK-0272, 2026-08-26); the brief's is `34bf290` (2026-08-28
17:21). `git log ae1fd01..HEAD -- <both paths>` (`ae1fd01` = TASK-0299,
2026-08-30 21:12) returns **empty** — neither file has moved since. Every
Done task from TASK-0288 onward (13 tasks, 2026-08-29 through today) is
therefore categorically absent from both documents.

**This task's own seven-item filing table, traced individually** (full
detail and exact line numbers in the deliverable): 2/7 already correct —
SVC withdrawal and KRAS P@5=0.000, both landed the same evening (`34bf290`).
4/7 are **missing outright**, not wrong-in-place: the pocket-level ceiling
(both in-sample and LOTO variants), and Finding F's spike count/p/%
(neither the stale nor the corrected number appears anywhere — the finding
itself, TASK-0288, is entirely absent from both documents). The 7th item —
"classical ceiling beats CTQW," which this task's own filing said was
"retracted" — **was never written into either committed document**: grepped
directly for the claim and its variants, no hit in either file. So there is
no text to flag as stale; TASK-0299's own text says the collaborator "has
just agreed to" that framing, meaning it was communicated verbally, not
written down. What's owed is telling the collaborator directly, per
TASK-0299's own still-unchecked action item — a conversation gap, not a
document gap.

**All five of this task's own explicit coverage items checked**:
- **Finding F, `min_A` vs `max_A`**: missing entirely from both docs, and
  found **internally unreconciled even within its own task family** —
  TASK-0291's `max_A` restatement ("7/9 spike targets within 8.4 Å") was
  computed (TASK-0290, `b6ee248`) against the **pre-TASK-0297** 9-member
  spike; TASK-0297's chain-matching fix removed TRP_SYNTHASE — one of the
  two `max_A` exceptions in TASK-0291's own table — from the spike, and
  nobody has recomputed the `max_A` restatement against the corrected
  8-member spike. Flagged, not computed here (would be re-deriving a
  number, out of this verify-only task's own Constraint).
- **Ceiling numbers**: found and separated **six** distinct values that
  all answer to "the ceiling" (fixed-rule in-sample 0.0899, swept-rule
  in-sample 0.1000, swept-rule LOTO 0.0000, category-oracle 0.1899,
  per-target-oracle 0.3307, candidate-oracle 0.3984) — conflating any two
  of these is exactly the failure mode TASK-0299/TASK-0300 exist to
  correct, and none currently appear in either document, so if one is
  added later it must say precisely which.
- **CTQW comparison**: the pocket-level result (CTQW indistinguishable
  from random, p=1.000, TASK-0299) is missing from both docs. The
  classical-diffusion-parity claim already in the brief's own §07
  criterion 2 was checked against its own source and is **current,
  verified correct** — not everything in the brief is stale.
- **ASBench figures**: TASK-0304 (Finding F generalizes: 26/117=22.2%
  below 1.5 Å on 118 external, largely-disjoint structures — its own
  characterization, "the strongest external support the register has
  produced for its own central claim") and TASK-0305 (our own CTQW
  P@5=0.0056 on ASBench, significantly *worse* than random, p<1e-4 — its
  own characterization, "the cleanest negative this register has
  produced") are both entirely absent from both documents. **Separately
  found**: the draft's own §3c citation ("Amor et al. 2016; Wu et al. 2022
  report 89.8%/98.1% on ASBench/CASBench") has carried the document's own
  "still outstanding, not yet auditable... needs a citation-accuracy
  check" flag since **2026-08-13** (checked the document's own top banner
  directly) — 18 days uncorrected. TASK-0304 has since read the real
  paper and independently recomputed its actual headline (99/118=83.9% at
  ≥1-of-6-measures without ligand; the honest all-six figure this
  register's own standards would report is 17.8%) — close to but not
  matching "89.8%," and "Amor et al. 2016" plus the CASBench "98.1%"
  figure remain wholly unverified by anyone, still.
- **Attribution shares**: the draft's "median 29% unexplained" (TASK-0254)
  is itself current in number and already self-aware of its own earlier
  superseded 9-target table (correctly labelled "superseded" in the text).
  But five later Shapley re-runs on the identical frozen set are absent:
  SASA (→27.2%), local frustration (unchanged, p=0.727), and this
  session's own TASK-0274 (conservation+chemistry: unexplained → **30.7%,
  higher, not lower**, neither block significant) — P2Rank and PocketMiner
  already made it into the brief's §08. **Also found**: TASK-0263's own
  result (`H_new`'s potential terms score 0.751 directly vs. CTQW's 0.575,
  cluster-robust p=0.019 — per TASK-0272's own COMMON.md characterization,
  "that task's own strongest single result in the brief") **is in the
  brief but absent from the draft entirely** — checked via grep for
  "0.751"/"potential terms" in `PHASE1_SUBMISSION_DRAFT.md`, no hit.

**Two more stale items found beyond this task's own filing table, in the
course of reading both documents in full**: the brief's own §06c "two
populations, discovered not imposed" (1D k-means silhouette 0.737) is
missing TASK-0288's own same-day, same-family correction (Finding B: "the
bimodality LRT is underpowered here... p=0.137 must not be reported as
evidence against two populations") — checked the exact commit ordering:
TASK-0288 landed `8acb1ca` at 2026-08-29 00:42, **7 hours after** the
brief's last commit `34bf290` (2026-08-28 17:21), and TASK-0288's own
header states directly that it "corrects [[TASK-0284]] Finding A as
published in the collaborator brief."

**Deliverable, committed**:
`documentation/2026-08-31-submission-evidence-pack.md` — one table,
checkable line by line, every row carrying an exact line number (or
"absent"), the current value, its committed-artifact source (task file
path + commit SHA), and a `CURRENT`/`STALE`/`MISSING`/`UNVERIFIED`
verdict. `RESULTS.md` new section, same commit.

**Not done, correctly out of scope per this task's own Constraint**:
recomputing the TASK-0291 `max_A` restatement against TASK-0297's
corrected 8-member spike (flagged as a one-line follow-up, not computed);
editing either submission document (a separate, deliberate step for
whoever owns them); telling the collaborator about the ceiling-comparison
retraction (a conversation, not something this task can do).
