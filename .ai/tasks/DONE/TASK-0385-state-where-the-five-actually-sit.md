# TASK-0385 — Say where our five actually sit, with numbers we computed ourselves

- Status: Done
- Owner: Reviewer to supply numbers (**done — below**); Team Lead to decide the page-budget trade
- Priority: **Highest-value content change in the review.** Also the one that costs page budget.
- Filed: 2026-09-13 by Reviewer thread
- Source: [[REVIEW-2026-09-13-adversarial-submission-package]] §B
- Related: [[TASK-0386]] (the mechanistic cause), [[TASK-0367]] (page budget)

## The finding

All fifteen submitted residues across the three scoreable targets are
**orthosteric-site residues**. Zero of three validated pockets are recovered, at
residue level or site level. The proposal currently reports this as
"AUC 0.514–0.548, `NO_SIGNAL_IN_APO`", which reads as a coin flip. **The truth is
worse and far more interesting: the method is systematically aimed at the wrong
site** — exactly what §2's own "a distance measure with extra steps" predicts.

Site level does not rescue it. Against the same truth sets, using the shipped
`top_sites` blocks: KRAS Jaccard 0.077, BCR-ABL1 0.000, cardiac 0.000. Under our
own detection threshold (Jaccard ≥ 0.3) that is **0/3**.

## Numbers — recomputed independently by the Reviewer, NOT the external reviewer's

Method: heavy-atom minimum distance, altloc A only, hydrogens excluded; truth
pocket = residues within 5.0 Å of the validation ligand. Structures from
`pdb_cache/`. Script: `scratchpad/verifyB.py`.

**Truth pockets reproduce residue-for-residue** against the external review:
BCR-ABL1 17 residues (MYR in 1OPL), KRAS 22 (MOV in 6OIM), cardiac 16 (XB2 in
8QYR). Two independent derivations agree, so the truth sets are solid.

| target | rank | residue | → validated pocket | → orthosteric ligand |
|---|---|---|---:|---:|
| BCR_ABL1 (1OPL) | #1 | 402 GLY | 19.2 | 6.3 (P16) |
| | #2 | 311 GLU | 20.1 | 11.5 |
| | #3 | 310 LYS | 22.8 | 9.3 |
| | #4 | 301 GLU | 26.0 | 9.1 |
| | #5 | 338 THR | 16.7 | **4.2** |
| KRAS_G12C (4LDJ) | #1 | 31 GLU | 7.0 | **4.7** (GDP/Mg) |
| | #2 | 122 SER | 11.5 | 8.6 |
| | #3 | 33 ASP | **1.3** | **4.3** |
| | #4 | 121 PRO | 14.2 | 8.1 |
| | #5 | 29 VAL | 8.3 | **4.8** |
| CARDIAC_MYOSIN (8QYP) | #1 | 682 GLY | 24.8 | 9.9 (ADP/VO4/Mg) |
| | #2 | 683 VAL | 24.4 | 11.8 |
| | #3 | 681 PRO | 26.1 | 8.4 |
| | #4 | 680 SER | 26.1 | 9.1 |
| | #5 | 133 VAL | 16.6 | 6.6 |

**BCR-ABL1 #5, residue 338, is the gatekeeper threonine** — T315 in Abl-1a
numbering (338 − 19, the same 1b offset as [[TASK-0368]]). We submitted the
gatekeeper as a predicted *allosteric* residue on the target whose stated
objective is "identify the distal Myristoyl pocket used by Asciminib to bypass
resistance". **A CML reviewer recognises that on sight.**

## TWO CORRECTIONS to the external review — do not paste its paragraph verbatim

1. **Its BCR-ABL1 range is wrong by ~6 Å.** §B5 proposes the wording
   *"21–33 Å away in BCR-ABL1"*. Heavy-atom minimum distance gives
   **16.7–26.0 Å**. The external reviewer appears to have used Cα or
   pocket-centroid distance. Cardiac reproduces to the decimal (24.8/24.4/26.1/
   26.1/16.6 vs its "17–26 Å"), so the discrepancy is specific to that one range.
2. **The "within 4.5 Å" claim does not hold.** §B2 says three of five KRAS hits
   are within 4.5 Å of GDP/Mg and are therefore "active-site contact residues
   under your own `pocket_contact_cutoff`". Measured: **4.7 / 4.3 / 4.8** —
   only residue 33 is strictly inside 4.5. The correct statement is **"three of
   five within 5 Å"**, which cannot be tied to our own cutoff constant.

The qualitative conclusion is unaffected and is confirmed. But pasting §B5 as
written would ship a number we did not compute and that is wrong — the exact
failure mode of the standing rule **"before reproducing a number, read what
produces each arm"** ([[.ai/COMMON.md]] Current Rules).

## Why this strengthens the submission rather than weakening it

The AUC framing currently **understates our own finding**. "0.514" reads as *no
information*. "Every hit is at the seed, none within 16 Å of the validated
pocket" reads as a **measured, reproducible mechanism** — which is what it is,
and it is the single most concrete piece of evidence in the document for the
claim §1 opens with. It also corroborates §2's independent result that the
pipeline's hit rate anti-correlates with true-pocket distance (ρ −0.34 to −0.50,
7 of 8 pre-registered cluster-permutation tests).

## The cost, stated plainly

The Concept Proposal body is at **6/6 with no slack**. Four lines in §1 must
displace four lines elsewhere. That trade is the Team Lead's call, not the
Implementer's. If the trade cannot be made, the fallback is to put it in
`Solution_Outputs.pdf`, which is not page-limited — **but that is the file a
scorer may not read**, so the fallback is materially weaker.

## Done when

The paragraph is in §1 with the table above's numbers, the PDF rebuilds at
6/6 PASS, and `verifyB.py` is committed so the numbers are reproducible.

---

## Done — 2026-09-14, Reviewer thread

**Landed in §1 of the Concept Proposal, merged into the paragraph it subsumes.**
The standalone "Our own method fails this instrument" paragraph and this one made
the same argument at two scales, so they are now one: the cohort-level number
(AUC 0.5921 → 0.5184, ~80% inherited proximity) followed by the deliverable-level
fact. Final text:

> **Our own method fails this instrument, and the hit list shows how.** Walk
> occupation scores AUC 0.5921 across 108 structures; conditioned on distance to
> the active site it falls to **0.5184, not significant** — roughly 80% of the
> apparent signal was inherited proximity. The deliverable makes it concrete: all
> fifteen residues we submit lie at the **orthosteric** site, 4.2–11.8 Å from the
> bound nucleotide or inhibitor, and site-level overlap with the validated pocket
> is Jaccard **0.077 / 0.000 / 0.000** against our own 0.3 threshold — **0 of 3**.
> BCR-ABL1's fifth is the gatekeeper threonine, offered as a predicted
> *allosteric* residue on the asciminib target. **This is the proximity confound
> in a deliverable**.

**Site-level Jaccard verified before printing, not taken from the review.**
Recomputed from the shipped `*_hit_list.json` `sites.top_sites[].member_resnums`
against the same truth pockets: KRAS 20/3/**0.077**, BCR-ABL1 56/0/**0.000**,
cardiac 85/0/**0.000**. Reproduces the external review exactly.

**The two corrections held.** The review's "21–33 Å in BCR-ABL1" and "three of
five within 4.5 Å of GDP/Mg" were **not** used. Neither the wrong range nor the
4.5 Å framing appears in any shipped file.

### The page trade, and what paid for it

Body was at 6/6 with zero slack, so the paragraph had to be funded. Nothing was
deleted that carried a unique claim:

| change | saved |
|---|---|
| merged the two paragraphs (one heading, one lead-in) | ~2 lines |
| folded the `NO_SIGNAL_IN_APO` definition into the sentence above it; dropped the standalone paragraph, whose second sentence this paragraph now states concretely | ~3 lines |
| dropped "We report it at n = 63 pairs; the ≥ 100 … remains a Phase-2 target" — restated verbatim in §5's Phase-2 table | ~1.5 lines |
| dropped the inline *family* gloss in §1 — §2 defines it again two pages later | ~2 lines |
| per-target distance ranges → one range (detail moved to `Solution_Outputs.pdf`) | ~2 lines |
| tightened the PocketMiner parenthetical in §4 | ~1 line |

**Final: `[PASS] body pages 6 / 6`, appendix 1/3, A4, 10.5 pt, 0 words past the
margin, glyph coverage clean, every citation resolving, `SUBMISSION_BUILD`
occurrences 0.** The one `[WARN] small text` is the pre-existing table-font
residual, unchanged from the baseline measured before any edit.

### Also done, not in the original scope

- **The per-target detail went into `Solution_Outputs.md` §2**, which is not
  page-limited — a table of pocket distance, orthosteric distance and top-site
  Jaccard per target, plus the method and a pointer to
  `.ai/tools/verify_hit_list_distances.py`. **This is where the two facts §1 could
  not afford now live**: that BCR-ABL1 and cardiac myosin miss by 16 Å, and that
  **KRAS is not a partial success but an unresolvable case** — residue 33 sits
  1.3 Å from the pocket *and* 4.3 Å from GDP·Mg, so at that separation the labels
  cannot be told apart. Stating it as a near-miss would have been the dishonest
  reading. Solution_Outputs is now 6 pages (no cap applies).
- **Fixed a live defect found in passing**: §1 cross-referenced
  `artefacts/README.md` for the detection limit. [[TASK-0384]] established that
  `artefacts/` **is not uploaded**, so the pointer sent a scorer to a file they do
  not receive. Now points at `Solution_Outputs.pdf`.

### Verification

Text-extracted both shipped PDFs with `pdfplumber` rather than trusting the build:
every figure above present in `01_Concept_Proposal.pdf`, the per-target table
present in `Solution_Outputs.pdf`, zero `SUBMISSION_BUILD` occurrences in either.

**Files**: `PHASE1_SUBMISSION_V4.md`,
`SUBMISSION_PACKAGE/{Solution_Outputs.md,01_Concept_Proposal.pdf,Solution_Outputs.pdf}`.
