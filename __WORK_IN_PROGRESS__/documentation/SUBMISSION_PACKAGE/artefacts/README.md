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

**What entry (i,j) is, and what that implies for a naive heatmap** (TASK-0370,
item 23 — not previously stated in any shipped file). Entry (i,j) is the
**time-averaged transition probability** of the underlying continuous-time
quantum walk from residue i to residue j: each row sums to 1 (±1e-6), and the
diagonal is the row's own maximum in roughly 78% of rows (checked directly on
the shipped `CARDIAC_MYOSIN` matrix). **A plain heatmap of this matrix will
read as diagonal-dominated** — that is the walk's own probability of staying
near its starting residue over the averaging window, not a defect in the
matrix or a sign that off-diagonal transport is absent. Off-diagonal structure
is real but visually smaller by construction; a reader plotting this should
either mask the diagonal or use a log/percentile colour scale, not read a
diagonal-bright heatmap as "no coupling."

| target | structure | N |
|---|---|---|
| KRAS_G12C | `4LDJ` (apo) | 170 |
| BCR_ABL1 | `1OPL` (apo) | 451 |
| CARDIAC_MYOSIN | `8QYP` (apo, *Bos taurus*) | 704 |
| MYC_MAX | `1NKP` | 171 |

**Correction (TASK-0370, external adversarial review item 3): the apo
structure is `8QYP`, not `8QYR`.** `8QYR` — previously labelled "(apo)"
here — is the mavacamten-complexed pre-powerstroke validation structure
(`holo_pdb` in `config/targets.yaml`); `8QYP` is the true apo input
(`apo_pdb`), independently confirmed by two routes: it is the only one of
the two whose residue count (N=704) matches this shipped matrix, and
`config/targets.yaml`'s own committed `apo_chains: ["A"]` resolves to
chain A of `8QYP` specifically (chain A of `8QYR` is a different chain —
checked directly, not assumed). Both structures are *Bos taurus* (bovine),
disclosed here since the field the previous table omitted was easy to miss.

## 2. Hit List — `hit_list_all_targets.csv`, and `<TARGET>/hit_list.json`

The top five predicted allosteric residues per target, ranked. The CSV is the
consolidated view and now carries a `chain` column (below); the per-target
JSON additionally carries the score, trivial-baseline confidence intervals
(`[estimate, lower, upper]`, in that order — not `[lower, upper]`), and our
own verdict, **for the three targets where one exists** (`MYC_MAX` has none,
by design — see below).

### The two columns are not the same number — read this before using them

| column | meaning |
|---|---|
| `residue_number` | the **PDB residue number**, as deposited. This is the one to quote, and the one that matches the Concept Proposal's five-guess table. |
| `residue_index_0based` | the **row/column position in the connectivity matrix**, counting from 0. |

They differ because PDB numbering does not start at zero and is not always
contiguous — a structure can begin at residue 81, or skip numbers where residues
were unresolved. The matrix is a dense N×N array, so its positions are
0…N−1 regardless.

| target | residue numbers run | contiguous? | example |
|---|---|---|---|
| KRAS_G12C (`4LDJ`) | 0 → 169 | yes | index 31 **is** residue 31 — the two columns coincide |
| BCR_ABL1 (`1OPL`) | 81 → 531 | yes | index 321 is residue 402 |
| CARDIAC_MYOSIN (`8QYP`) | 32 → 780 | **no** — gaps at unresolved residues | index 611 is residue 682 |
| MYC_MAX (`1NKP`) | 897 → 284 | **no** — two chains concatenated, so the sequence is not even monotonic | index 46 is residue 943 |

**KRAS is the trap**: its two columns are identical, so code tested only on KRAS
will silently use the wrong column everywhere else. The CSV matrices avoid the
problem entirely — their row and column headers are residue *numbers*, so no
index arithmetic is needed to read them.

**`hit_list_all_targets.csv` now carries a `chain` column** (TASK-0370, item
22) — added because c-Myc's residue numbering is otherwise ambiguous without
one (`1NKP` concatenates two chains, see the table above). Chain is `A` for
every target except `MYC_MAX`, which uses `config/targets.yaml`'s own
`chains: ["A", "B"]` pairing (`A` = c-Myc, `B` = Max); each `MYC_MAX` hit's
chain was resolved directly against the deposited structure, per residue, not
assumed uniform. UniProt-equivalent numbering (c-Myc's own residue 943 does
not exist in UniProt's 439-residue c-Myc — this numbering is `1NKP`'s own
deposited numbering, not UniProt) is a separate, still-open item, tracked
against [[TASK-0368]].

**Seed residues, per target — not previously shipped** (TASK-0370, item 24).
§6 of the Concept Proposal states the three artefacts "cannot disagree with
each other," which was unverifiable without the seed set the walk was
launched from. Computed directly from this repository's own pipeline
(`allostery.labels.build_labels`/`functional_indices`, the same call the
shipped numbers came from — not re-derived or guessed), and confirmed to
share **zero residues** with that target's own top-5 hit list, as the
pipeline's own exclusion logic requires:

| target | seed (PDB residue numbers) | source |
|---|---|---|
| KRAS_G12C | 11–18, 28, 30, 32, 116, 117, 119, 120, 145–147 (18 residues) | GDP/Cys12 contact site (`func_ligand: GDP`) |
| BCR_ABL1 | 267, 272, 275, 288–290, 304, 305, 308, 309, 312, 317, 318, 332, 334, 336, 337, 340, 373, 378, 380, 389, 398–401 (26 residues) | nilotinib (ATP-site) contact residues (`func_ligand: NIL`) |
| CARDIAC_MYOSIN | 114, 115, 126–128, 134, 179–186, 238, 240, 242, 461 (18 residues) | mavacamten-site contact residues |
| MYC_MAX | 226, 243, 246, 925, 943 | **top-5 highest-degree residues** — `func_ligand: DNA` matched nothing in this apo structure, so `functional_indices` fell back to its documented topological-degree proxy (its own logged warning, not a silent default) |

**MYC_MAX's seed and its own top-5 hit list are the identical five residues.**
Disclosed plainly rather than smoothed over: with no active site to seed from,
the fallback seed is itself a degree-based proxy, and the consensus ranking
(also correlated with degree, per the Concept Proposal's own §2 measurement
that this operator family is a distance/degree proxy rather than an
independent detector) landed
on the same five residues the seed already named. This is not independent
corroboration of those five residues — it is the same proximity/degree
confound the rest of this register documents, showing up in the one target
with no ground truth to catch it against. Read `MYC_MAX`'s hit list
accordingly: as an artefact of the fallback, not as a converged prediction.

**Read the verdicts with the list, where a verdict exists.** For the three
targets with a drug-bound structure to check against (`KRAS_G12C`,
`BCR_ABL1`, `CARDIAC_MYOSIN`), our own validation reports `NO_SIGNAL_IN_APO`
— the score's confidence interval overlaps the best trivial baseline's. We
submit the five as required and state plainly that we cannot certify them;
the reasoning is in Section 1 of the Concept Proposal. **`MYC_MAX`'s JSON
carries no verdict/CI fields at all** (TASK-0370, item 26) — not a gap, by
design: `1NKP` has no drug-bound structure, so no AUC, floor, or CI is
computable, exactly as `MYC_MAX/report.txt` states. The blanket "the JSON
carries a verdict for that target" line above describes the other three.

### Two things in the JSON files worth reading past the top-5 (TASK-0370, items 20–21)

- **`BCR_ABL1/hit_list.json` also carries a `sites` block reporting one
  whole-pocket, site-level clustering result nobody previously mentioned**:
  56 residues, **zero overlap** with the true pocket, centroid 20.4 Å away,
  and `knob_spread: "UNSTABLE"` (its own clustering solution changes with
  the clustering parameters, Jaccard-min 0.0 across the parameter grid
  stored alongside it). This is a secondary, whole-site construction — not
  the top-5 residue-level hit list above — and it failed by every measure
  it reports on itself. Disclosed rather than silently shipped: it is not a
  second, better answer, and should not be read as one.
- **`CARDIAC_MYOSIN`'s five residues are one cluster, not five candidates.**
  In the shipped matrix, 680–684 couple most strongly to each other and to
  127/128/134 (independently confirmed: 4 of the 5 shipped hits — 680, 681,
  682, 683 — are sequential). The challenge accepts residue indices, so all
  five are submitted as required, but a reader should not take "top-5" to
  mean five independent candidate sites here; it is one region reported at
  residue resolution. The mechanistic *why* is still open, tracked against
  [[TASK-0368]].

## 3. Methodological Report — `<TARGET>/report.txt`

Per-target: the metric, the AUC against the proximity floor with bootstrap
confidence intervals, the operator-term attribution, and the verdict.
**Section 2 of the Concept Proposal argues that this metric does *not*
proxy biological signal transmission beyond distance** (TASK-0370, item
25 — the previous wording here claimed the opposite of what Section 2
actually concludes); these files are that section's per-target evidence,
read together with its own residualised-signal finding, not in place of
it. `V_B`, `V_T`, `V_R`, `V_C`, and `V_M` (the `most_impactful_term` /
`least_impactful_term` fields) are five diagonal Hamiltonian potential
terms — **checked directly against `src/allostery/potentials.py`, not the
Concept Proposal, which does not name them** (TASK-0370, item 25 — the
previous wording here claimed they were defined there):

| term | what it rewards/penalises |
|---|---|
| `V_B` | low crystallographic B-factor (penalises high-flexibility residues) |
| `V_T` | non-terminal position (penalises chain-end residues) |
| `V_R` | rigidity — high graph degree + high local clustering + low GNM mean-square fluctuation |
| `V_C` | covariance centrality — high mean GNM dynamic cross-correlation with the rest of the structure (the standard allosteric-coupling measure, Haliloglu & Bahar 1999) |
| `V_M` | low-mode participation — high weight in the slowest GNM eigenmodes |

`AUC_heat_mean` is **not** a diffusion-process baseline despite
the name — it is `H_new`'s own ground-state relaxation score, an
indefinite-operator comparison, not a classical heat kernel (see each
report's own inline note next to that field). "Optimised" in
`AUC_apo_Hnew_optimised` means the default operator configuration — no
separate hyperparameter search was run per target, so this value equals
`AUC_apo_Hnew_default` in every shipped file; not a claim that tuning was
attempted and found unnecessary.

## Provenance

Produced by the pipeline in `github.com/Oussema-t/Quantum_allosteric-scanner`
(branch `bartosz`). The five residues in each hit list match the Concept
Proposal's own five-guess table exactly.
