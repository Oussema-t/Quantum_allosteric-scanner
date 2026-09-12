# TASK-0368 — Consult Berke: are our five shipped residues per target the pockets we say they are?

- Status: TODO
- Owner: **Berke Turkaydin** (team member, not an agent) — coordinated by the Reviewer
- Priority: **High. It concerns the only per-target deliverable a medicinal chemist will actually read.**
- Filed: 2026-09-11 by Reviewer thread (id via `claim.py reserve-next`)
- Source: `.ai/reviews/2026-09-11/REVIEW-2026-09-11-external-adversarial-submission-package.md`, items 3, 19, 21, 22
- Related: [[TASK-0367]], [[TASK-0369]], [[TASK-0370]]

## Why this needs Berke and not an agent

An external adversarial reviewer claims our shipped hit lists point at the **wrong
pockets**, and the claim is specific enough to be checkable but rests on
residue-numbering conventions and structural biology judgement. **This register's
own discipline is that biological calls belong to the person whose research area
this is.** No agent should adjudicate it, and no submission text should change
until it is adjudicated.

The reviewer explicitly asks for Berke by name on the BCR-ABL1 numbering.

## The specific claims to confirm or refute

Each needs a verdict and, where the reviewer is right, the correct statement.

### 1. BCR-ABL1 (`1OPL`) — "the five are the ATP site, not the myristoyl pocket"

We ship **402, 311, 310, 301, 338**.

- The claim: `1OPL` uses Abl-1b numbering (1a + 19), so a myristate-site residue
  set of E481/P484/V487/I521 in 1OPL numbering corresponds to the canonical
  E462/P465/V468/I502 in 1a.
- Under that mapping the reviewer reads **402 as the DFG glycine, 338 as the
  hinge, and 301/310/311 as the αC region** — i.e. the orthosteric ATP site.
- **Question for Berke:** is the 1a/1b offset applied correctly here, and are our
  five ATP-site residues rather than myristoyl-pocket residues?

### 2. `1OPL` ligand content — "doubly liganded, and we mention only one"

- The claim: `1OPL` carries **myristic acid *and* a dichlorophenyl
  pyridopyrimidinone (P16)**, an ATP-site inhibitor. Our text names only the
  myristate.
- **Question:** confirm the ligand inventory. If correct, our "apo" framing for
  this structure is wrong in a second way, and §1's contamination argument gains
  a stronger example rather than losing one.

### 3. Cardiac myosin — which structure is apo, and which species

- We ship a 704-residue matrix and label it `8QYR (apo)` in `artefacts/README.md`.
- The claim: **`8QYR` is the β-cardiac myosin motor domain in the pre-powerstroke
  state complexed with mavacamten, and it is *Bos taurus***; the register's apo
  input is `8QYP`, whose N matches the shipped matrix.
- **Question:** which PDB ID is the apo structure actually behind the shipped
  matrix, and is the bovine origin correct and worth disclosing?

### 4. Cardiac five — "one site, not five"

We ship **682, 683, 681, 680, 133**.

- The claim: in the shipped matrix 680–684 couple most strongly to each other and
  to 127/128/134 — so the five hits amount to **one site**.
- **Question:** is that one contiguous site biologically, and is it the mavacamten
  pocket or something else?

### 5. c-Myc (`1NKP`) — numbering that cannot be UniProt

We ship **943, 246, 925, 226, 243**.

- The claim: residue 943 exceeds c-Myc's 439 residues and 226/243/246 exceed Max's
  160, so these are neither UniProt numbers nor unambiguous without a chain.
- **Question:** what chain does each belong to, and what are the UniProt-equivalent
  numbers? Also: for a protein with **no active site**, what seed is defensible —
  the register does not state one.

### 6. KRAS (`4LDJ`) — switch I and no switch II

We ship **31, 122, 33, 121, 29**.

- The claim: these are the nucleotide-pocket rim — switch I (29/31/33) and
  residues adjacent to the NKCD motif (121/122) — with **no switch-II residues**,
  and switch II is where the G12C allosteric pocket is.
- **Question:** confirm. If right, this is the clearest illustration in the whole
  package of what the proximity confound produces as a deliverable.

## What we do with the answers

- **If the reviewer is right**, this is not a disaster — it is the submission's own
  thesis, demonstrated on our own output. One honest sentence ("this is what the
  proximity confound looks like in a deliverable") is stronger than a quiet
  correction, and consistent with everything else we report.
- **If the reviewer is wrong**, we need to know precisely where, because the same
  claims will be made by a reviewer we cannot reply to.

## Constraints

- **Do not change the shipped residues.** They are what the method produced; the
  question is what they *are*, not what we wish they were.
- Record the verdict per item with a locator — PDB entry, paper, or numbering
  convention — so a later reader can check it the way we check everything else.
- **Do not let submission text move ahead of this.** [[TASK-0369]] and
  [[TASK-0370]] must wait on items 1–6 for anything touching hit-list biology.

## Suggested form of the ask

A single message with the six questions and the shipped five-residue lists,
answerable in prose. Berke does not need the register to answer it, and should not
have to read it.


---

## Status, 2026-09-12

**Asked and accepted.** The six questions have been put to Berke and he has
confirmed he is working on them. Nothing in [[TASK-0369]] or [[TASK-0370]] that
touches hit-list biology moves until the answers arrive.

### Item 3 narrowed by the register — the reviewer is right, and so was the recollection

Grepped, as the Team Lead suggested, and it settles it:

- `.ai/tasks/DONE/TASK-0003-targets-yaml-reconciliation.md:91` — *"8QYR: confirmed
  real **Bos taurus** MYH7, 1.80 Å X-ray"*, and `:102` records it as the
  **`holo_validation=8QYR` substitute**.
- `.ai/tasks/DONE/TASK-0114-pocket-label-cutoff-sensitivity.md:113` — **`8QYP`, N=704**,
  which is exactly the shipped matrix's dimension.

**So `8QYR` is the holo validation structure, `8QYP` is the apo input, and the shipped
matrix is `8QYP`.** The external reviewer's item 3 is a **label error in
`artefacts/README.md`**, not a wrong structure — the scanner was not run on the
drug-bound structure. **The species claim is also correct and is ours**: our own
register confirmed *Bos taurus* on 2026-06 and the submission never discloses it.

[[TASK-0370]]'s cardiac label fix may therefore proceed on register evidence without
waiting. **Item 3 still goes to Berke** — reduced to a confirmation rather than an
investigation, and he should still say whether the bovine origin needs disclosing in
the submission and whether it affects the biological reading at all.
