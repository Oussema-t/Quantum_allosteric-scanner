# Phase-1 submission package — Team AuraQu

Assembled 2026-09-11. Sources are the two governing documents, quoted rather than
remembered:

- `documentation/2026-04-06-Phase-1-Submission-Guidelines-VF.md` §4 — *what to submit*
- `documentation/Cleveland-Clinic-Challenge-Statement-vF-1.md` §5 — *what the solution must generate*

---

## A. Submission components (Guidelines §4)

| § | Required | In this folder | Status |
|---|---|---|---|
| 4.1 | Team Profile — team name, **lead contact details**, member descriptions, prior quantum experience | `02_Team_Profile.md` | **Complete** — lead contact is Bartosz Chmura, chmura.quantum@gmail.com, Unaffiliated |
| 4.2 | Problem Statement Selection | `03_Problem_Statement_Selection.md` | Complete |
| 4.3 | Concept Proposal, **max 6 pages, PDF** | `01_Concept_Proposal.pdf` | Complete — **body is 6/6 pages, at the limit**, appendix 1/3 |
| 4.4 | *Optional*: up to 3 pages of appendices; link to a public code repository | appendix is inside the PDF (1 of 3 used); repo link is stated in the Concept Proposal | Complete |

Also required by §3 and not a file: **the team lead must have accepted the
Challenge Terms & Conditions at the point of submission.**

## B. Solution outputs (Challenge Statement §5)

All three, for each of the four required targets, under `artefacts/<TARGET>/`:

| # | Required output | File | Form |
|---|---|---|---|
| 1 | **Connectivity Matrix** — N×N, entry (i,j) = quantum connectivity strength between residues i and j | `<TARGET>/connectivity_matrix.csv` | first row and first column are PDB residue numbers, so the file is self-describing; 6 significant figures, round-trip verified |
| 2 | **Hit List** — top 5 predicted allosteric sites per target | `hit_list_all_targets.csv` + `<TARGET>/hit_list.json` | CSV is the consolidated ranked view; the JSON adds score/floor CIs and the per-target verdict |
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

## C. The solution outputs are in, in conventional formats

**Settled by the organisers, 2026-09-11.** Asked whether §5's connectivity matrix,
hit list and methodological report have required file formats, they answered:

> *"No specific formats are prescribed. Please use formats accessible with
> conventional software."*

They answered the format question rather than saying the outputs belong to Phase 2
— so we treat them as expected now and ship them.

**Consequence, acted on:** the matrices were `.npz` (NumPy), which is **not**
accessible with conventional software. They are now **CSV**, with PDB residue
numbers as both the first row and the first column, so each file is
self-describing and opens in Excel, R, pandas or a text editor. The `.npz` copies
were dropped from the package rather than shipped alongside — same data, less
accessible format, and two copies invites a question about which is authoritative.
They remain in the repository.

Round-trip verified on export: re-reading each CSV reproduces the source array to
`rtol=1e-5`. Symmetry checked, not assumed.

Added a consolidated `artefacts/hit_list_all_targets.csv` and
`artefacts/README.md` describing all three output types and their columns.

**Package total: 8.8 MB**, against the §5 cap of 20 MB.

## D. Open items before this can be sent

1. **Terms & Conditions acceptance** by the team lead at the point of submission (§3).
2. **`CARDIAC_MYOSIN_TABLE1` produced only an `error.txt`** and is deliberately not
   included: the Table-1 structure could not be processed, and the substitution
   (`8QYP` → `8QYR`) was accepted as primary by the organisers. The shipped
   `CARDIAC_MYOSIN` artefacts are the substituted structure. The Concept Proposal
   states the substitution and the reason.
3. **Body is at 6 of 6 pages.** Any further addition to the Concept Proposal now
   requires removing something. One appendix page of the three remains.

## E. Not part of the submission

The task register, the version ledger, and the `_build_latex` working directory
are development artefacts. The public repository link in the Concept Proposal is
how a reviewer reaches them if they want to.
