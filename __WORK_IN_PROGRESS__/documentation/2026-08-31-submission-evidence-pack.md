# Submission evidence pack — every number traced, staleness flagged (TASK-0307)

**Filed 2026-08-31, Implementer D. Verify-only: nothing in
`PHASE1_SUBMISSION_DRAFT.md` or `CTQW_CONTRIBUTION_BRIEF.html` was edited
to produce this document, per TASK-0307's own Constraint.**

Scope note: TASK-0184 is the coordinating task file for
`documentation/PHASE1_SUBMISSION_DRAFT.md` (its own "Owner: Bartosz
(writing)" line) — the draft, not the task file, carries the numeric
claims and is what this pack audits. TASK-0184's own body is largely
structural (ToC coverage, section mapping) and is not separately audited
here.

**Headline finding, before the table**: `PHASE1_SUBMISSION_DRAFT.md` was
last touched by commit `3b3be11` (TASK-0272, 2026-08-26).
`CTQW_CONTRIBUTION_BRIEF.html` was last touched by commit `34bf290`
(2026-08-28 17:21). **Neither file has a single commit since** — verified
directly (`git log ae1fd01..HEAD -- <both paths>` returns empty, where
`ae1fd01` is TASK-0299, 2026-08-30 21:12). Every finding from **TASK-0288
onward (2026-08-29 through today, 2026-08-31 — 13 Done tasks)** is absent
from both documents, not merely under-cited. Some of those are omissions
(new findings never added); a smaller number are genuine stale numbers
still stated as current. Both kinds are in the table below, labelled.

## How to read the table

- **Current value / source**: what the number actually is right now, and
  the committed artifact it traces to (task file path + commit SHA — task
  files, not `RESULTS.md`, since `RESULTS.md` has no entry for TASK-0297/
  0298/0299/0300/0304/0305, a gap noted once here and not re-flagged per
  row).
- **In the doc now**: what the document currently states, with a line
  number, or **absent** if the finding isn't mentioned at all.
- **Verdict**: `STALE` (a number is stated and is wrong), `MISSING` (the
  finding doesn't appear at all), `CURRENT` (verified to match), or
  `UNVERIFIED` (never traced to a primary source by anyone, flagged as
  such per this task's own Constraint — "if a number cannot be traced to
  a committed artifact, that is the finding").

---

## 1. The seven items from this task's own filing table

| # | quantity | in the doc now | current value / source | verdict |
|---|---|---|---|---|
| 1 | pocket-level ceiling (in-sample, `MIN_HOP>=1 + drug_alone`) | **absent** from both docs (grepped `0.1649`/`0.0899`/`ceiling` in both — no hit in either) | **0.0899** (was 0.1649 pre-chain-fix) — `.ai/tasks/DONE/TASK-0298-chain-aware-fpocket-parsing.md` (`9d4ef2f`, 2026-08-30) | MISSING (never in either doc — the 0.1649 figure lives only in `.ai/tasks/DONE/TASK-0282-*.md` and this task family's own internal record, not in the submission docs) |
| 2 | pocket-level ceiling (LOTO, swept-rule) | absent | **0.0000** — every one of 20 folds, `TASK-0298` (`9d4ef2f`); independently reconfirmed `TASK-0299` (`ae1fd01`) | MISSING |
| 3 | Finding F spike count/p | absent (no "Finding F", "spike", "covalent", or "peptide bond" text anywhere in either doc — grepped) | **8/28, binomial p=1.51×10⁻⁵** (was 9/28, p=2.03×10⁻⁶ before the chain-matching fix moved TRP_SYNTHASE out of the spike) — `.ai/tasks/DONE/TASK-0297-chain-aware-seed-audit.md` (`c753b39`, 2026-08-30) | MISSING (the finding itself, TASK-0288, is also entirely absent — filed 2026-08-28, after the brief's last commit) |
| 4 | Finding F headline % | absent | **"~29%"** (8/28 = 28.6%; was "~32%", 9/28 = 32.1%) — same source as #3 | MISSING |
| 5 | "classical ceiling beats CTQW" | **not found as a literal claim in either committed document** (grepped `ceiling`, `beats CTQW`, `outperforms CTQW` — no hit) | Retracted — `.ai/tasks/DONE/TASK-0299-corrected-pocket-level-comparison.md` (`ae1fd01`, 2026-08-30): neither CTQW nor the classical rule beats random after the chain fix; CTQW's apparent edge is 1 cluster of 13, p=1.000 vs random | **N/A for the written docs** — TASK-0299's own text says the collaborator "has just agreed to" this framing, implying it was communicated verbally/informally, not written into either file. **Still owed**: telling the collaborator directly, per TASK-0299's own unchecked Action item. Not a text-edit gap; a conversation gap. |
| 6 | SVC figures | **withdrawn, correctly** — `CTQW_CONTRIBUTION_BRIEF.html:513` ("SVC results withdrawn: an earlier version... quoted linear SVC 0.546 and RBF SVC 0.500... Those two figures are not reportable and are removed") | matches commit `34bf290`'s own stated purpose ("Stability re-run before sending: two corrections to the brief") | **CURRENT** — verified correct, no action needed |
| 7 | KRAS P@5 | **0.000**, correctly, in both docs — `PHASE1_SUBMISSION_DRAFT.md:183` and `CTQW_CONTRIBUTION_BRIEF.html:528` | `.ai/tasks/DONE/TASK-0283-shipped-backend-and-research-pipeline-disagree.md` (`14e74c0`, 2026-08-28) | **CURRENT** — verified correct, no action needed |

**Two of seven are already correctly stated (SVC, KRAS P@5) — both fixed the
same evening (`34bf290`) as part of the same "stability re-run" pass.
Four of the remaining five are missing outright, not wrong-in-place; one
(the ceiling-beats-CTQW claim) was apparently never written down at all.**

## 2. This task's own explicit coverage requirements

### 2a. Finding F — spike count, p, %, min_A vs max_A

Covered in table §1 rows 3–4. One more layer, not in TASK-0307's own
summary table: **TASK-0291 recommended restating Finding F on `max_A`
instead of `min_A`** (7 of the original 9 spike members have their
*entire* drug-contact set within 8.4 Å, a stronger claim than "nearest
residue is 1.3 Å away"). TASK-0290's recompute (2026-08-29, `b6ee248`)
reproduced "7/9 within 8.4 Å" against the **pre-chain-fix 9-member spike**.
**TASK-0297's chain fix (2026-08-30) removed TRP_SYNTHASE from the spike
— one of the two `max_A` exceptions in TASK-0291's own table** — and
nobody has recomputed the `max_A` restatement against the corrected
8-member spike. The likely new figure is "7/8 within 8.4 Å" (KRAS_G12C
being the sole remaining exception), but this is **UNVERIFIED, not
computed here** — re-deriving it would be scope creep on a verify-only
task; flagged as a one-line follow-up.

Verdict: **MISSING in both docs** (neither `min_A` nor `max_A` framing of
Finding F appears anywhere in either document), **and internally
un-reconciled** even within the task family itself (TASK-0291's own
`max_A` recommendation was applied once, against a spike membership that
TASK-0297 has since changed).

### 2b. Ceiling numbers

Five distinct numbers all answer to "the ceiling," and conflating them is
exactly the failure mode this task exists to prevent. All from
`.ai/tasks/DONE/TASK-0298-*.md` (`9d4ef2f`) and
`.ai/tasks/DONE/TASK-0300-*.md` (`85ee20c`):

| ceiling variant | value | meaning |
|---|---|---|
| fixed pre-specified rule, in-sample | **0.0899** | `MIN_HOP>=1 + drug_alone`, no selection, no fitting |
| swept rule, in-sample | 0.1000 | `hop>=3 + lex_far_first`, selected by the (defective) row-mean criterion |
| swept rule, LOTO held-out | **0.0000** | the number that actually matters for a claim of generalization |
| category-stratified (oracle category) | 0.1899 | if the true near/far/intermediate category were known |
| best rule per target (oracle, 61-rule family) | 0.3307 | inflated by multiplicity — an upper bound, not reachable |
| fpocket candidate oracle (perfect pick) | 0.3984 | ceiling on the candidate list itself, no ranking involved |

None of these appear in either submission document (§1 rows 1–2 above).
If a "ceiling" figure is added to either document, it must say **which**
of these six it means — TASK-0299/0300 both exist specifically because
two earlier tasks conflated them.

### 2c. CTQW comparison

- **Attribution-based** (added-last, geometry+fpocket+CTQW): see §2e below
  — this IS current in the brief (§2.3b of the draft is one step further
  behind; see §3 below).
- **Pocket-level** (TASK-0299): CTQW mean EH 0.0389, indistinguishable
  from random (p=1.000) and from the swept rule (p=1.000) — entirely
  absent from both documents (§1 row 5).
- **§07 "what would change our mind" criterion 2** in the brief
  (`CTQW_CONTRIBUTION_BRIEF.html:538`) states "ρ = 0.79 median, AUC 0.5635
  vs 0.4930... classical arm ranks the true pocket better on 6 of 14" —
  this is TASK-0256's own classical-diffusion-parity result and **was
  checked and is current** (no later task revisits it; `git log` shows no
  commit to either file touching this section since it was written).
  **CURRENT.**

### 2d. ASBench figures (TASK-0304/0305)

| claim | in the doc now | current value | verdict |
|---|---|---|---|
| "84%" headline, decomposed | `PHASE1_SUBMISSION_DRAFT.md:604`: **"Amor et al. 2016; Wu et al. 2022 report 89.8%/98.1% on ASBench/CASBench"** | Wu et al. 2022's own real number, independently recomputed from their Table S3/S4: **99/118 = 83.9%** (without ligand) at-least-1-of-6; **89.0%** with ligand present. All-six (this register's own honest reportable figure under its own Bonferroni standard): **17.8%** (without ligand) / 22.9% (with). Source: `.ai/tasks/IN_PROGRESS/TASK-0304-asbench-casbench-cohort-extension.md` (script `task0304_asbench_finding_f.py`, commit `9da6bd9`) | **STALE, and doubly so.** "89.8%" is close to but does not match the with-ligand ≥1-measure figure (89.0%) verified from primary source; "98.1%" (CASBench) is still **UNVERIFIED by anyone** — TASK-0304's own "Still to do" list has "CASBench site annotations" unresolved. **"Amor et al. 2016" has never been independently checked at all** — only Wu, Strömich & Yaliraki 2022 has been read and verified (DOI 10.1016/j.patter.2021.100408). The document's own top banner has flagged this exact citation as "still outstanding, not yet auditable" since **2026-08-13** — 18 days uncorrected, and a real, better number has existed since 2026-08-30. |
| Finding F generalizes to ASBench | absent | **26/117 = 22.2%** below 1.5 Å (peptide-bond/covalent), on 118 external structures, 4× the size of this register's own 28-target set and 4/118 overlapping — `.ai/tasks/IN_PROGRESS/TASK-0304-*.md` (`728f7c3`, 2026-08-31) | MISSING — described by TASK-0304 itself as "the strongest external support the register has produced for its own central claim" |
| Our detection on ASBench (TASK-0305) | absent | CTQW P@5 **0.0056** on 108 ASBench structures, **significantly worse than random** (Wilcoxon p<1e-4) — every one of our arms at or below random; the field's own propensity score also only reaches P@5 0.0204 vs random 0.0176 on the same retrieval metric — `.ai/tasks/DONE/TASK-0305-our-detection-on-asbench.md` (`ec50af4`, 2026-08-31) | MISSING — TASK-0305's own framing ("the cleanest negative this register has produced") makes this a strong Phase-1 candidate finding, absent from both documents |

**TASK-0304 is itself still IN_PROGRESS** (CASBench annotations, cohort
ingestion into `clean_from_config`, and the TASK-0299/0300 re-runs on the
extended cohort are its own open Scope items) — its committed numbers
above are real and citable, but the task is not finished, so anything
pulled from it into the submission should say so.

### 2e. Attribution shares (geometry / CTQW / unexplained)

Two independent versions exist in the documents, at different vintages,
and they **disagree with each other** — not because either is wrong, but
because they were never reconciled after the second one landed:

- `PHASE1_SUBMISSION_DRAFT.md:355-366` (§2.3b, first table): **9-target,
  in-sample-adjacent design**, KRAS_G12C-specific row included. Explicitly
  labelled by the document itself as **"superseded as the estimate of
  record"** two paragraphs later (line 407) — this is correct, current,
  self-aware staleness, not a defect.
- `PHASE1_SUBMISSION_DRAFT.md:416-424` (§2.3b, "Corrected estimate of
  record"): **unexplained 2–62%, median 29%**, geometry median 42%,
  fpocket median +8%, CTQW median +11% — **TASK-0254** (`cbb2720`,
  2026-08-24), n=20, frozen/untuned set, exact 3-block Shapley. This is
  the number currently governing the document.
- Since TASK-0254, the SAME frozen 20-target Shapley attribution has been
  independently re-run with a 4th and a 5th block **four separate times**,
  none of which moved the residual materially and none of which appear in
  either document:

| block added | unexplained (3-block baseline 28.6%*) | added-last, cluster-robust p | source |
|---|---|---|---|
| SASA (burial control) | → 27.2% | p not the headline stat (see task); cryptic-lean p=0.0736→0.2392 | `TASK-0266` (2026-08-25) |
| local frustration | unchanged (~28%) | p=0.727, not significant | `TASK-0268` (2026-08-25/26) |
| P2Rank | → 27% (rows) / 26% (clusters) | p=0.881, not significant | `TASK-0260` — **this one IS in the brief**, §08 |
| PocketMiner | unchanged, 27% | p=0.277, not significant | `TASK-0269` — **this one IS in the brief**, §08 |
| conservation + chemistry (2 blocks) | → **30.7%**, i.e. *higher* | conservation p=0.6946, chemistry p=0.6492, neither significant | `TASK-0274` (2026-08-26) — **absent from both docs** |

*(28.6% here vs. the document's own "median 29%" is the same number to
rounding — not a discrepancy.)*

**Also absent from both documents**: `TASK-0263` (2026-08-25) — `H_new`'s
own potential terms, scored directly rather than propagated through
CTQW, reach AUC 0.751 against CTQW's 0.575 (cluster-robust p=0.019); CTQW
added-last against terms-already-in-the-model is p=0.973. **This result
IS in the brief** (§06b, "The Hamiltonian work is the reason we found our
best result... 0.751 against CTQW 0.575, cluster-robust p=0.019") but
**is not in `PHASE1_SUBMISSION_DRAFT.md` anywhere** — checked via grep
for "0.751" and "potential terms", no hit in the draft. This is arguably
the single strongest technical result in the whole register (per
TASK-0272's own COMMON.md characterization, "that task's own 'strongest
single result in the brief'") and it is missing from the actual
submission document.

**Verdict: CURRENT in number (median 29% is not wrong), but the document
is silent on five follow-on tests that all confirm the residual is real
and unmoved by six years' worth of ordinary/tried features — evidence
that would materially strengthen the Phase-2 case §3 already makes, and
is entirely absent. Also missing the single strongest technical result
(TASK-0263) that the brief already carries.**

## 3. Two more stale items found in the course of this audit, not in this task's own filing table

### 3a. The near/far bimodality claim (`CTQW_CONTRIBUTION_BRIEF.html` §06c, added 2026-08-28)

States, with confidence: "Two populations, discovered not imposed... 1D
k-means silhouette 0.737... log-normality rejected at p=0.0020." This is
`TASK-0284`'s own Finding A.

**`TASK-0288`** (filed 2026-08-28, landed `8acb1ca` 2026-08-29 00:42 —
**7 hours after** the brief's last commit `34bf290`, 2026-08-28 17:21)
explicitly states in its own header: **"corrects [[TASK-0284]] Finding A
as published in the collaborator brief."** Its Finding B: "the bimodality
LRT is UNDERPOWERED here — inconclusive, not negative... p=0.137... the
size-free evidence for two groups is weaker than Finding A implied...
**p=0.137 must not be reported as evidence against two populations.**"

This is not a reversal (TASK-0288 does not claim there is only one
population) — but the brief's own confident "discovered not imposed"
framing has a known, dated, self-identified caveat that has not been
folded in. **STALE (qualification missing, not a wrong number).**

### 3b. Section 06b/06c dates vs. what followed them

Both `§06b` ("what the last two weeks changed") and `§06c` are internally
dated "Added 2026-08-27" / "Added 2026-08-28" — accurate for their own
content, but nothing marks that **13 more Done tasks have landed since**,
several of which (TASK-0297/0298/0299/0300 especially) directly bear on
claims made in the very next section, §07 ("what would change our mind").
Not a numeric error — a missing "as of" boundary a reader would reasonably
assume is current.

## Summary — what a write-up check against this table should do

**Confirmed correct, no action**: SVC withdrawal, KRAS P@5=0.000, the
CTQW-vs-classical-diffusion parity claim (§07 criterion 2), the "median
29% unexplained" headline number itself.

**Missing outright (14 findings from 2026-08-29 onward, zero in either
document)**: Finding F (both `min_A` and the unreconciled `max_A`
restatement), all six pocket-level ceiling variants, the CTQW-vs-random
pocket-level result, the rule-selection defect, both ASBench results
(TASK-0304 generalizes Finding F; TASK-0305 is a clean negative on CTQW),
five further attribution-block negatives (SASA/frustration/conservation/
chemistry — P2Rank and PocketMiner already made it in), TASK-0263's own
best result (in the brief, missing from the draft).

**Stated and wrong (citation, not analysis)**: the "89.8%/98.1%"
ASBench/CASBench literature figure — flagged as unverified by the
document's own banner since 2026-08-13, still unverified for the
"Amor et al. 2016" half, and superseded for the Wu 2022 half by a real,
independently-recomputed number.

**Stated and incomplete (a caveat, not a number)**: the near/far
bimodality claim, missing its own same-family correction.

**Not a text problem**: the "classical ceiling beats CTQW" retraction —
apparently never written into either document, so there is nothing to
edit; what is owed is telling the collaborator, per TASK-0299's own
unchecked action item.
