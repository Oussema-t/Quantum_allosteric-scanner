# TASK-0364 — Read the sponsor group's own quantum binding-site paper closely, and state our delta against it

- Status: Done
- Owner: **Explorer or Reviewer** (literature, not compute)
- Priority: **High before submission; the claim it supports is already in the shipping document**
- Filed: 2026-09-10 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0348]], [[TASK-0349]], [[TASK-0363]]

## Why

The submission currently states:

> *The sponsor's own group has separately published a quantum binding-site
> structure prediction result [8], so we make no claim that this domain is
> untouched by quantum methods. Cryptic-pocket prediction specifically, as far as
> we can establish, has none.*

Reference [8] is **Zhang Y, et al., "A quantum framework for protein binding-site
structure prediction on utility-level quantum processors", *Adv Sci.* 2026;13:e13641,
doi:10.1002/advs.202513641** — verified to exist, cited correctly, and **not read
closely by anyone on this side.**

That is a gap with two distinct risks, and the second is the dangerous one:

1. **We assert a negative about it** — that it does not cover cryptic-pocket
   prediction. That assertion is currently based on title and abstract, not on
   the paper. It is hedged ("as far as we can establish"), which is honest, but
   hedging is not the same as having looked.
2. **It is the sponsor's own group.** A reviewer from that group will know this
   paper in detail. If our one-sentence characterisation of it is even slightly
   off, it is the sentence they will notice, and it sits immediately beside our
   own prior-art paragraph about [7]. [[TASK-0348]] already showed what happens
   when a published number is repeated rather than checked: the draft claimed our
   measurements were "consistent with" a JACS ρ≈0.95 that we then measured at
   0.41.

## Intent Contract

- **Outcome:** a short, sourced characterisation of what [8] actually does, and a
  one-paragraph statement of our delta against it — good enough that the sentence
  in the submission is defensible line by line to an author of the paper.
- **In scope:**
  1. Read the paper. Not the abstract — **the method section and the evaluation
     section**, which is where the difference between binding-site *structure
     prediction* and *cryptic-pocket* prediction will or will not appear.
  2. Answer these specific questions, each with a quotation or figure/section
     reference: What problem is solved? What is the quantum component, and what
     runs classically? What hardware, how many qubits, and is the quantum step
     load-bearing or a demonstration? What is the benchmark and the metric? **Does
     it address cryptic or apo-state pockets anywhere?**
  3. **Verify or correct our sentence.** If the paper does touch cryptic pockets,
     the submission's claim is wrong and must change before it ships — that is the
     outcome this task exists to catch.
  4. Check whether it belongs in the prior-art paragraph beside [7] rather than
     only in the "domain is not untouched" aside.
- **Out of scope:**
  - Reproducing or re-running anything from the paper.
  - Reviewing its quality. We are establishing **what it claims** and **how ours
    differs**, not judging it.
  - Broadening into a general literature survey. One paper.
- **Constraints and invariants:** every characterisation carries a locator
  (section, figure, or quotation). Where the paper is ambiguous, say so and quote
  the ambiguous passage rather than resolving it in our favour — **the entire
  value of this task is that it is the sponsor's own work and we do not get to be
  approximately right about it.**

## Planned Validation

The existing citation's metadata (authors, journal, volume, DOI) re-checked
against the publisher record before anything else is trusted from it, per the
same discipline [[TASK-0348]] applied to the JACS DOIs.

## Pre-registered expectation

The submission's sentence is probably right — binding-site structure prediction
and cryptic-pocket detection are different problems. **If so, this task returns a
sharper sentence rather than a correction, and the value is that we can defend it
to its own authors.** If it is wrong, we found it ourselves rather than hearing it
from a reviewer.

## Budget

Capped at one working session. If the paper is paywalled and unavailable, report
that plainly and **narrow the submission's sentence to what the abstract
supports** rather than leaving a claim we cannot source.

## Staged Files

- [2026-09-10 17:03] `.ai/COMMON.md` -- review pass / TASK-0364
- [2026-09-10 17:03] `.ai/tasks/TODO/TASK-0364-read-the-sponsor-group-quantum-binding-site-paper.md` -- review pass / TASK-0364
- [2026-09-10 17:03] `__WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V3.md` -- review pass / TASK-0364
- [2026-09-10 17:03] `__WORK_IN_PROGRESS__/documentation/SUBMISSION_VERSION_LEDGER.md` -- review pass / TASK-0364

## Done

**2026-09-10, Architect.** Read the paper (arXiv preprint 2506.22677, the
freely-accessible full text of [8] — Wiley's own page 403s to automated
fetch; DOI resolved and metadata cross-checked against the Wiley/TAU/
arXiv listings first, per Planned Validation: title, authors (Zhang Y et
al.), *Advanced Science* 13(12):e13641, doi:10.1002/advs.202513641 all
confirmed. Caveat carried forward, not resolved in our favor: this is the
preprint, not necessarily byte-identical to the final peer-reviewed text —
no method/scope difference is expected between a preprint and its
published version at this stage, but this was not independently
confirmed against the paywalled Wiley PDF.**

**Answers, each with a locator:**

1. **Problem solved**: 3D backbone structure of *short peptide fragments
   at already-located ligand-binding sites* (5–14 residues, Table 1) — not
   full-protein folding, not finding *where* a site is. Abstract: "short
   fragments that constitute ligand-binding pockets typically contain
   fewer than 20 amino acids."
2. **Quantum component**: VQE on a tetrahedral-lattice model; Hamiltonian
   encodes chirality, steric exclusion, geometry, and pairwise
   Miyazawa–Jernigan interactions as "an Ising-type Hamiltonian with
   sparse Pauli-ZZ support." Classical: COBYLA optimizer driving the VQE
   loop, plus downstream atom completion / docking. **Load-bearing, not a
   demonstration**: "measurement bitstrings... are reverse-mapped into a
   spatial backbone vector" that *is* the predicted structure.
3. **Hardware**: IBM–Cleveland Clinic 127-qubit superconducting
   processor (the sponsor's own hardware, not third-party) — 12 qubits
   (5-residue case) to 102 qubits (14-residue case), 23 cases run on real
   hardware end to end.
4. **Benchmark/metric**: 23 PDBbind fragments + 7 named therapeutic
   targets; RMSD vs. experimental structure and AutoDock Vina docking
   affinity, compared against AlphaFold3. Quantum RMSD 3.33 Å (median
   3.53) vs. AF3 3.87 Å; docking −4.38 vs. −4.00 kcal/mol.
5. **Cryptic or apo-state pockets — not addressed anywhere.** Every test
   case is extracted from a solved protein-**ligand complex** ("each
   fragment originated from a distinct protein-ligand complex with
   experimentally determined receptor structures") — the site's location
   and that it is *open* are both given as input, not predicted.
6. **Allosteric vs. orthosteric — orthosteric only.** No mention of
   allosteric sites, distal regulation, or non-active-site pockets found
   anywhere in the text.

**Verify-or-correct verdict**: the submission's sentence was **correct as
stated but under-specified** — matches the Pre-registered expectation's
"sharpen, don't correct" branch. Sharpened
(`__WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V4.md` §"Prior
art..."), stating precisely what [8] does (structure of an *already-known*
site) and precisely what it does not touch (detection, apo state,
allosteric) rather than only the negative claim about cryptic pockets —
defensible line by line against the paper's own method/evaluation
sections now, not against title and abstract.

**Paragraph placement (Intent Contract item 4)**: kept separate from the
[7] prior-art comparison, not merged in. [7] is genuinely comparable
prior art — the same CTQW construction, ablated head-to-head on our own
cohort. [8] is a different quantum paradigm entirely (VQE ground-state
energy minimization, not a walk/spectral method) solving a different
problem (fragment structure, not pocket scoring) — it is domain-adjacent
evidence, not a competing method to benchmark against. The existing
"domain is not untouched" aside is the right home for it.

**V3 not edited** — superseded by V4 per `SUBMISSION_VERSION_LEDGER.md`'s
own "never edit a shipped version in place" convention (V3→V4 landed in
[[TASK-0365]]/[[TASK-0362]], after this task was filed against V3's own
path). Edited V4 instead, the current live draft; ledger entry added
there.
