# Problem Statement Selection

**Problem statement addressed:** Cleveland Clinic — *Unlocking undruggable
targets: quantum simulation of allosteric signal propagation*
(Global Quantum + AI Challenge 2026, `Cleveland-Clinic-Challenge-Statement-vF-1.pdf`).

## How we interpreted it

Rather than only running the requested algorithm on the provided structures, our
Phase-1 work audited the challenge's own premise and dataset. Our measurements
show that the standard benchmark targets conflate **static cavity retrieval** with
**genuine cryptic-pocket discovery**: roughly half of apo/holo pairs cannot
express the required contrast at all.

Our proposal therefore addresses the challenge's core objective by delivering a
**validated, unconfounded benchmarking instrument** capable of certifying
allosteric methods — quantum or classical — alongside the required predictions.

## Targets

We address the complete mandatory set required by Challenge Statement §6: **KRAS
G12C, BCR-ABL1, cardiac myosin, and c-Myc.**

Four structure choices deviate from Table 1. **Each is stated, with its reason and
its evidence, in Section 1 of the Concept Proposal**, and each traces to the
organisers' clarification of 2026-08-26. They are not repeated here: a single
authoritative statement is less likely to drift than two, and the Concept Proposal
is the document a reviewer assesses.

## Required outputs

Challenge Statement §5's three deliverables are supplied as follows:

| § 5 output | Where |
|---|---|
| **Connectivity Matrix** — N×N quantum connectivity strength | `Connectivity_Matrices.csv` |
| **Hit List** — top five predicted allosteric residues per target | `Solution_Outputs.pdf`, and machine-readable in the same file set |
| **Methodological Report** — the quantum metric chosen, and why it proxies biological signal transmission | **Section 2 of the Concept Proposal**, with per-target detail in `Solution_Outputs.pdf` |
