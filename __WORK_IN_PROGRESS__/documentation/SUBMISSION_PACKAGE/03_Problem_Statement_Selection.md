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

Three structures deviate from Table 1 (`4LDJ` replacing `4OBE`; `8QYP`/`8QYR`
replacing `5TBY`/`6C1H`); BCR-ABL1's `1OPL` is retained, not substituted. **Each
is stated, with its reason and its evidence, in Section 1 of the Concept
Proposal**, and each traces to the organisers' clarification of 2026-08-26. They
are not repeated here: a single authoritative statement is less likely to drift
than two, and the Concept Proposal is the document a reviewer assesses.

## Required outputs

Challenge Statement §5's three deliverables are supplied as follows:

| § 5 output | Where |
|---|---|
| **Connectivity Matrix** — N×N quantum connectivity strength | `Connectivity_Matrices.csv` |
| **Hit List** — top five predicted allosteric residues per target | `Solution_Outputs.pdf`, and machine-readable in the same file set |
| **Methodological Report** — the quantum metric chosen, and why it proxies biological signal transmission | **Section 2 of the Concept Proposal**, with per-target detail in `Solution_Outputs.pdf` |

---

## Note on organiser correspondence

*Included at the organisers' request, so that this submission is neither
advantaged nor disadvantaged relative to teams working from the published
Challenge Statement alone.*

Several choices below follow from replies the Cleveland Clinic team sent in
answer to questions we raised. The Challenge Statement was not publicly revised,
so a reader holding only the published version would otherwise see unexplained
deviations from Table 1. Each reply, and what it changed here:

| organiser reply | what it changed in this submission |
|---|---|
| **2026-08-26** — cardiac myosin: our `8QYP`–`8QYR` substitution is *accepted as primary* | Cardiac myosin is scored on `8QYP`/`8QYR` rather than Table 1's `5TBY`/`6C1H` |
| **2026-08-26** — a suggested KRAS G12C structure, `8S8C` | We checked `8S8C` against the PDB, found it **holo** (MK-1084-bound) and therefore unusable as the apo half of a contrast, and substituted verified apo `4LDJ` instead |
| **2026-08-26** — BCR-ABL1: `1OPL` may be substituted with an alternative apo structure, *"please document the rationale in your submission"* | We **declined** the substitution and retained `1OPL`. Rationale, as requested: its myristate occupancy is the finding, not a defect — it is how we established that "apo" depositions are not reliably ligand-free. Stated in Section 1 of the Concept Proposal |
| **2026-08-26** — no specific deliverable formats are prescribed; use formats accessible with conventional software | The five-file package structure, and the connectivity matrices shipped as one long-format CSV rather than an archive |
| **2026-09-07** — submitted documents may be revised and re-uploaded | Nothing in the science; recorded for completeness |
| **2026-09-08** — ENM methods are permitted, as is an MD-*trained* tool used with MD-free inference | PocketMiner retained as the cryptic-opening veto |

These replies granted latitude on **structure choice and deliverable format**.
They did not endorse any finding in this submission, and no finding here is
presented as endorsed.
