# Solution outputs — Challenge Statement §5

Formats follow the organisers' answer of 2026-09-11: *"No specific formats are
prescribed. Please use formats accessible with conventional software."* Everything
here is plain text — CSV opens in Excel, R, pandas, or a text editor with no
special library.

## 1. Connectivity Matrix — `<TARGET>/connectivity_matrix.csv`

N×N, entry (i,j) = the quantum connectivity strength between residues i and j.

- **Self-describing**: the first row and the first column are **PDB residue
  numbers**, not array positions, so no separate index file is needed.
- Symmetric, and verified symmetric on export.
- Values are dimensionless transport weights in roughly `1e-5 … 0.5`, written to
  6 significant figures. Re-reading each file reproduces the source array to
  within `rtol=1e-5` — checked on export, not assumed.

| target | structure | N |
|---|---|---|
| KRAS_G12C | `4LDJ` (apo) | 170 |
| BCR_ABL1 | `1OPL` (apo) | 451 |
| CARDIAC_MYOSIN | `8QYR` (apo) | 704 |
| MYC_MAX | `1NKP` | 171 |

## 2. Hit List — `hit_list_all_targets.csv`, and `<TARGET>/hit_list.json`

The top five predicted allosteric residues per target, ranked. The CSV is the
consolidated view; the per-target JSON additionally carries the score and
trivial-baseline confidence intervals and our own verdict for that target.

**Read the verdicts with the list.** For the three targets where a drug-bound
structure exists to check against, our own validation reports
`NO_SIGNAL_IN_APO` — the score's confidence interval overlaps the best trivial
baseline's. We submit the five as required and state plainly that we cannot
certify them; the reasoning is in Section 1 of the Concept Proposal.

`1NKP` (c-Myc) has no drug-bound structure in the PDB, so its five are a genuinely
prospective prediction with no ground truth to score against.

## 3. Methodological Report — `<TARGET>/report.txt`

Per-target: the metric, the AUC against the proximity floor with bootstrap
confidence intervals, the operator-term attribution, and the verdict. The argument
for *why* this metric proxies biological signal transmission is Section 2 of the
Concept Proposal; these files are its per-target evidence.

## Provenance

Produced by the pipeline in `github.com/Oussema-t/Quantum_allosteric-scanner`
(branch `bartosz`). The five residues in each hit list match the Concept
Proposal's own five-guess table exactly.
