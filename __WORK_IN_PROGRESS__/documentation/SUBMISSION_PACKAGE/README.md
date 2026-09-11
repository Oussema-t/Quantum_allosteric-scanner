# Phase-1 submission package — Team AuraQu

Assembled 2026-09-11. Sources are the two governing documents, quoted rather than
remembered:

- `documentation/2026-04-06-Phase-1-Submission-Guidelines-VF.md` §4 — *what to submit*
- `documentation/Cleveland-Clinic-Challenge-Statement-vF-1.md` §5 — *what the solution must generate*

---

## A. Submission components (Guidelines §4)

| § | Required | In this folder | Status |
|---|---|---|---|
| 4.1 | Team Profile — team name, **lead contact details**, member descriptions, prior quantum experience | `02_Team_Profile.md` | **INCOMPLETE — lead contact details are missing and are flagged as missing inside the file rather than invented. This blocks submission.** |
| 4.2 | Problem Statement Selection | `03_Problem_Statement_Selection.md` | Complete |
| 4.3 | Concept Proposal, **max 6 pages, PDF** | `01_Concept_Proposal.pdf` | Complete — **body is 6/6 pages, at the limit**, appendix 1/3 |
| 4.4 | *Optional*: up to 3 pages of appendices; link to a public code repository | appendix is inside the PDF (1 of 3 used); repo link is stated in the Concept Proposal | Complete |

Also required by §3 and not a file: **the team lead must have accepted the
Challenge Terms & Conditions at the point of submission.**

## B. Solution outputs (Challenge Statement §5)

All three, for each of the four required targets, under `artefacts/<TARGET>/`:

| # | Required output | File | Form |
|---|---|---|---|
| 1 | **Connectivity Matrix** — N×N, entry (i,j) = quantum connectivity strength between residues i and j | `quantum_connectivity_matrix.npz` | keys `matrix` (N×N float) and `resnums` (N,) so matrix indices map to PDB residue numbers |
| 2 | **Hit List** — top 5 predicted allosteric sites per target | `hit_list.json` | `indices` (0-based) and `resnums` (PDB numbering), plus the score/floor CIs and the verdict |
| 3 | **Methodological Report** — the quantum metric and why it proxies biological signal transmission | `report.txt` per target; the argument itself is Section 2 of the Concept Proposal | |

### Matrix dimensions, as shipped

| target | N | top-5 (PDB residue numbers) |
|---|---|---|
| KRAS_G12C | 170 | 31, 122, 33, 121, 29 |
| BCR_ABL1 | 451 | 402, 311, 310, 301, 338 |
| CARDIAC_MYOSIN | 704 | 682, 683, 681, 680, 133 |
| MYC_MAX | 171 | 943, 246, 925, 226, 243 |

The five residues in each row match the Concept Proposal's own five-guess table
exactly — checked, not assumed.

Package size: **6.3 MB**.

---

## C. Open items before this can be sent

1. **Team lead contact details** (§4.1). Missing. The only hard blocker here.
2. **Terms & Conditions acceptance** by the team lead at the point of submission (§3).
3. **`CARDIAC_MYOSIN_TABLE1` produced only an `error.txt`** and is deliberately not
   included: the Table-1 structure could not be processed, and the substitution
   (`8QYP` → `8QYR`) was accepted as primary by the organisers. The shipped
   `CARDIAC_MYOSIN` artefacts are the substituted structure. The Concept Proposal
   states the substitution and the reason.
4. **Body is at 6 of 6 pages.** Any further addition to the Concept Proposal now
   requires removing something. One appendix page of the three remains.

## D. Not part of the submission

The task register, the version ledger, and the `_build_latex` working directory
are development artefacts. The public repository link in the Concept Proposal is
how a reviewer reaches them if they want to.
