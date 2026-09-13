# TASK-0385 — Say where our five actually sit, with numbers we computed ourselves

- Status: TODO
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
