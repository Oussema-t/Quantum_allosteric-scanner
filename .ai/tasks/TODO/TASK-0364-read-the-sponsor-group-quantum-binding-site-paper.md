# TASK-0364 — Read the sponsor group's own quantum binding-site paper closely, and state our delta against it

- Status: TODO
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
