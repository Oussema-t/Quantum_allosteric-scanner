# TASK-0388 — Rescope the apo/stripped-holo priority claim, and name the incumbent benchmark

- Status: TODO — **first step is to read the paper, not to edit the text**
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
