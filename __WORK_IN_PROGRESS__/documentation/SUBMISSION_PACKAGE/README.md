# Phase-1 submission package — Team AuraQu

Assembled 2026-09-11, restructured 2026-09-13 for the portal's **five-file** limit.
Sources are the two governing documents, quoted rather than remembered:

- `documentation/2026-04-06-Phase-1-Submission-Guidelines-VF.md` §4 — *what to submit*
- `documentation/Cleveland-Clinic-Challenge-Statement-vF-1.md` §5 — *what the solution must generate*

---

## The five files to upload

| # | file | size | covers |
|---|---|---|---|
| 1 | `01_Concept_Proposal.pdf` | 84 K | Guidelines §4.3 **and** Challenge Statement §5's methodological report |
| 2 | `02_Team_Profile.pdf` | 40 K | Guidelines §4.1 |
| 3 | `03_Problem_Statement_Selection.pdf` | 28 K | Guidelines §4.2 |
| 4 | `Connectivity_Matrices.csv` | 13 M | Challenge Statement §5, output 1 |
| 5 | `Solution_Outputs.pdf` | 56 K | Challenge Statement §5, outputs 2 and 3 |

**Total ≈ 14 MB** against the §5 cap of 20 MB. **Markdown is not an accepted upload
format**, which is why 2, 3 and 5 are PDFs; their `.md` sources sit alongside them
and are not uploaded.

### How §5's three outputs are satisfied without a sixth file

| §5 output | where |
|---|---|
| **Connectivity Matrix** — N×N, entry (i,j) = quantum connectivity strength | file 4 |
| **Hit List** — top five predicted allosteric residues per target | file 5 (and machine-readable under `artefacts/`) |
| **Methodological Report** — the metric, and why it proxies signal transmission | **Section 2 of the Concept Proposal**, which now says so in its own heading; per-target detail in file 5 |

## File 4 — how the matrices were combined

Four targets with different N cannot share one wide CSV, and archives are not an
accepted format, so the matrices are in **long form**:

```
target,pdb_id,residue_i,residue_j,value
```

- **Each unordered pair is listed exactly once**, in each matrix's own row/column
  order — not sorted, so `residue_i > residue_j` occurs (true for MYC_MAX; see
  the CSV header). Each matrix was checked symmetric on export, so (j,i) equals
  (i,j) and listing both would double the file for no information.
- `residue_i`/`residue_j` are **PDB residue numbers as deposited**, not array
  indices. The two differ for three of the four targets.
- Values are dimensionless transport weights to 6 significant figures.
- **379,327 rows**, and the reconstruction was verified: cardiac myosin's full
  704×704 was rebuilt from the CSV and compared to the source array —
  `allclose` at rtol 1e-5, max absolute difference 4.9e-07.
- **All four targets survive independent adversarial reconstruction**: rebuilding
  each per-target matrix from this file reproduces the `artefacts/` source array
  exactly (max |diff| = 0.0 over 2,000 sampled entries per target), every matrix
  is symmetric to numerical precision, and row counts match this table exactly
  (TASK-0384).

| target | structure | N | pairs |
|---|---|---|---|
| KRAS_G12C | `4LDJ` (apo) | 170 | 14,535 |
| BCR_ABL1 | `1OPL` (apo) | 451 | 101,926 |
| CARDIAC_MYOSIN | `8QYP` (apo) | 704 | 248,160 |
| MYC_MAX | `1NKP` | 171 | 14,706 |

**`8QYP` is the apo input. `8QYR` is the mavacamten-bound holo validation
structure and is not in these matrices** — an earlier draft of this file had that
backwards.

## Not uploaded, kept for provenance

`artefacts/` holds the per-target sources these files were built from — the
individual matrices, the hit-list JSON with its confidence intervals, and each
target's `report.txt`. They are the inputs to files 4 and 5, not additional
submission components.

## Open items before upload

1. **Terms & Conditions acceptance** by the team lead at the point of submission (§3).
2. **The repository is published on 2026-09-15.** The Concept Proposal states that
   date, so a reviewer following the link before then sees a stated fact rather
   than a 404. If uploading earlier, confirm the portal does not surface links to
   reviewers before the deadline closes.
3. `CARDIAC_MYOSIN_TABLE1` produced only an `error.txt` and is deliberately absent:
   the Table-1 structure could not be processed, and the substitution was accepted
   as primary by the organisers.
