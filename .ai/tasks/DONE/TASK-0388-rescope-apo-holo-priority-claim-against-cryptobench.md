# TASK-0388 — Rescope the apo/stripped-holo priority claim, and name the incumbent benchmark

- Status: Done
- Owner: Explorer to verify the claim; Implementer to apply
- Priority: High. A reviewer who catches this discounts §1's other four findings by association.
- Filed: 2026-09-13 by Reviewer thread
- Source: [[REVIEW-2026-09-13-adversarial-submission-package]] §C
- Related: [[TASK-0345]], [[TASK-0346]]

## The claim at risk

`PHASE1_SUBMISSION_V4.md:34` — *"And ligand-removed holo is measurably easier
than apo — **a gap we have found no report of**."* §5 and the Phase-2 table
repeat it.

The external reviewer states that **CryptoBench** (Pluskal group, *Bioinformatics*
2025; bioRxiv 2024) says in its abstract that current methods rely on holo
conformations for training and evaluation while overlooking apo states, and that
this is particularly problematic for cryptic sites, where holo-based assessment
yields unrealistic performance expectations.

**Our own register cites CryptoBench thirteen times** — as a dataset we chose not
to fetch ([[TASK-0345]], [[TASK-0346]]). Nobody appears to have read the paper's
argument.

## FIRST: verify, do not take this on trust

The Reviewer could **not** check this offline — it rests entirely on the external
reviewer's quotation of an abstract. Before rewriting anything, someone opens the
paper. This is the standing rule **"a PDB ID is a claim until someone opens the
entry"** applied to a citation.

**Scope the check precisely.** Only line 34 is exposed. The same "we have found
no report of" construction carries two *other* claims that CryptoBench does not
touch and that must not be weakened by association:

- line 132 — the **protein-identity floor** (constant-per-protein score reaching
  AUC 0.65). Independent of apo/holo.
- line 135 — the **convergence check** on propagation time (50 of 108 structures
  flip verdict between T=15 and the converged limit). Independent.

## If it is confirmed — two fixes, one paragraph

1. **Rescope to magnitude, not existence:**

   > The direction of this gap is known (CryptoBench, 2025); what we have found
   > no quantitative measurement of is its size on a matched apo/holo cohort with
   > a single detector and truth definition — we measure +0.199 AUC, CI [+0.102,
   > +0.296], n = 63 pairs.

   That survives contact with an expert. The current wording does not.

2. **Differentiate the Phase-2 deliverable.** §5 component (a) is "a certifying
   cryptic-pocket benchmark". **CryptoBench and AHoJ-DB already occupy that
   ground** (4.68 M apo/holo pocket pairs, UniProt-grouped, sequence-clustered),
   and neither is mentioned anywhere in the submission. A reviewer asked to fund
   a benchmark will ask what ours adds.

   We have a real answer — the blind validity rule, the endogenous-ligand audit,
   the measured detection limit, the distal/cryptic separation — but it has to be
   stated **against the named incumbent**, not against an unnamed field. One
   sentence in the §5 table's "(a)" row.

## Done when

The paper is read and the outcome recorded here either way; if confirmed, both
fixes applied and the two unrelated "no report of" claims left intact.

## Done

**Verified, not taken on trust — the external reviewer's quotation is accurate.**
Fetched the actual abstract from two independent sources (Oxford Academic
`academic.oup.com/bioinformatics/article/41/1/btae745` and the PMC mirror
`pmc.ncbi.nlm.nih.gov/articles/PMC11725321`), both returning the identical
verbatim sentence: *"current prediction methodologies often rely on holo
(ligand-bound) protein conformations for training and evaluation, overlooking
the significance of the apo (ligand-free) states. This oversight is
particularly problematic in the case of cryptic binding sites (CBSs) where
holo-based assessment yields unrealistic performance expectations."*
`PHASE1_SUBMISSION_V4.md:34`'s "a gap we have found no report of" is therefore
**confirmed overclaimed on existence** — CryptoBench (Škrhák et al.,
*Bioinformatics* 2025, transliterated to plain ASCII as `Skrhak` in our own
reference list to avoid a real glyph-coverage failure, see below) states the
qualitative direction of this gap in its own abstract.

**Went one level deeper than the task's own pre-drafted fix required**: asked
whether CryptoBench also reports a *quantitative* apo-vs-holo detection-gap
number (not just the qualitative direction), since that would undercut even the
rescoped "magnitude not reported" claim. It does, partially: CryptoBench's own
Table 5 gives P2Rank AUC 0.81 (apo) vs 0.89 (holo) — but with the ligand
**retained**, not stripped. This is a materially different experimental design
from our own 63-pair, ligand-*stripped*, single-detector measurement (fpocket,
+0.199 druggability-score delta, CI [+0.102, +0.296]) — ligand-retained holo can
leak pocket location through the ligand's own atoms, which stripping is
specifically designed to rule out. This distinction is what makes the rescoped
claim ("size on a matched, ligand-stripped cohort was not reported") still
correct rather than a second overclaim in disguise.

**Also caught, while re-deriving the exact number to cite**: the task's own
pre-drafted fix text called the +0.199 delta an "AUC" figure. Checked against
[[TASK-0345]]'s committed Result table directly — it is a mean fpocket
**druggability-score** delta, not an AUC (TASK-0345 never computed an AUC for
this comparison). The existing submission text already had this exact unit
conflation ("roughly 0.2 AUC easier") one sentence later; fixed both instances
while rewriting the paragraph rather than propagating a units error into a
document already this heavily audited.

### Fix 1 — rescoped line 34 (magnitude, not existence)

Old: *"And ligand-removed holo is measurably easier than apo — a gap we have
found no report of."* ... *"those headline numbers describe a task roughly 0.2
AUC easier"*

New: *"Ligand-removed holo is measurably easier than apo — the direction is
known [16], its size on a matched cohort was not."* ... *"those headline
figures describe a task measurably easier"* (AUC-unit error dropped, not just
relabelled). Added reference **[16]** (CryptoBench, ASCII-transliterated
author names) to the Appendix.

### Fix 2 — named the incumbent in the §5/Phase-2 table's "(a)" row

`PHASE1_SUBMISSION_V4.md:92`, the "(a) Certifying cryptic-pocket benchmark"
row, gained `— beyond CryptoBench [16]/AHoJ-DB's own pair curation` naming both
incumbents the task asked for, next to what our own instrument adds (blind
validity rule, endogenous-ligand audit, positive control, measured detection
limit, at scale) that neither of them provides.

### Page budget and a second real glyph bug, both caught before shipping

Body was at 6/6 with **zero slack** (confirmed via
`submission_build_latex.py`, same tool [[TASK-0385]]/[[TASK-0387]] used).
First-draft edits (both fixes plus the CryptoBench P2Rank comparison spelled
out in-body) pushed body to **7/6 FAIL**. Trimmed by moving the
ligand-retained-vs-stripped distinction out of the body paragraph entirely
(kept only in this task file, not duplicated into `Solution_Outputs.md` —
judged not essential enough to spend that file's own space on, unlike
[[TASK-0385]]'s distance-range detail) rather than shortening the two required
fixes themselves. Final paragraph is 69 characters **shorter** than the
original despite adding a citation. Also hit the same glyph-coverage failure
class as [[TASK-0386]]: `Škrhák`/`Krivák`'s Czech diacritics (`Š`, `ý`) have no
LaTeX rendering in this template and failed the build's own glyph check —
fixed by transliterating to plain ASCII (`Skrhak`, `Krivak`) in the reference
entry, the same fix pattern as TASK-0386's Unicode-subscript bug, now the
second instance this review cycle.

**Final build**: `submission_build_latex.py --json` → `"result": "PASS"` — A4,
body 6/6, appendix 1/3, 10.5pt, 0 words past margin, glyph coverage clean,
every citation resolving including the new [16]. Rebuilt PDF copied to
`01_Concept_Proposal.pdf` and verified by reading the actual rendered PDF back
(not just trusting the build's own report) — both fixes render correctly, cite
`[16]`, and reference 16 prints correctly in the appendix.

Pre-existing, not touched: the build's own "small text" WARN (6 characters at
7.0/7.3pt) was present in the unmodified baseline build too — flagged as
already-live, not introduced here, and out of this task's scope.

**Not done / out of scope**: did not add the CryptoBench P2Rank
retained-vs-stripped distinction to `Solution_Outputs.md` — judged as
optional value-add beyond the task's own two required fixes, available as a
quick follow-up if a reviewer's comment surfaces it. Did not touch AHoJ-DB with
its own citation (named inline only, consistent with how PocketMiner/P2Rank
are named elsewhere in this document without individual brackets at every
mention).

Files touched: `__WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V4.md`,
`__WORK_IN_PROGRESS__/documentation/SUBMISSION_PACKAGE/01_Concept_Proposal.pdf`.
