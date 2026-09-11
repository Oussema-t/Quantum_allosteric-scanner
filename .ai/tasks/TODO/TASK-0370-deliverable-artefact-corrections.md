# TASK-0370 — The shipped artefacts: contradictions with the proposal, missing definitions, and a hit list that cannot be reproduced

- Status: TODO
- Owner: **Implementer**
- Priority: **High — these files are the §5 deliverable and a reviewer opens them directly**
- Filed: 2026-09-11 by Reviewer thread (id via `claim.py reserve-next`)
- Source: `.ai/reviews/2026-09-11/REVIEW-2026-09-11-external-adversarial-submission-package.md`, items 6, 20, 21, 23, 24, 25, 26
- Related: [[TASK-0368]], [[TASK-0369]]

## The worst of it: our own files contradict our own proposal

**Item 6.** The Concept Proposal's whole credibility rests on reporting negatives
honestly. The shipped `report.txt` files say the opposite:

- **KRAS** `report.txt`: *"CTQW genuinely helps"*, ΔAUC +0.171 — on **one
  structure**, with a CI width ≈0.35, against baselines at 0.346 and 0.342 that
  are themselves **below chance**.
- **MYC** `report.txt`: *"Confidence: high."* The Concept Proposal says
  **unverified**.

A reviewer who opens a shipped file and finds it claiming a win the proposal
disclaims will not read the rest charitably. **Four-operator agreement is not
confidence** — our own proposal shows those operators are all distance detectors.

**Fix:** regenerate or correct the verdict lines so the files say what the
proposal says. If the generator produces these strings, fix the generator, not
the file.

## Missing information that makes the deliverable unusable

| # | Gap |
|---|---|
| 23 | **No shipped file states what a matrix entry is.** The reviewer reverse-engineered it: 704×704, exactly symmetric, rows sum to 1 ± 1e-6, diagonal is the row maximum in 78% of rows — i.e. a **time-averaged transition probability**, and therefore diagonal-dominated in any heatmap. Both facts belong in `artefacts/README.md`: the formula, and the warning that a naive heatmap will show mostly diagonal. |
| 24 | **Seed residues are not shipped, so the hit list cannot be reproduced from the matrix.** §6 claims the artefacts "cannot disagree with each other"; a reader currently cannot check that. The reviewer tried a guessed nucleotide-site seed and did not reproduce the cardiac top five. **Ship the seed set per target.** |
| 22 | **The hit-list CSV has no chain column**, and c-Myc's numbering is ambiguous without one. Add chain; add UniProt-equivalent numbering once [[TASK-0368]] supplies it. |
| 25 | **`report.txt` hygiene**: three of four files have no target or PDB header; 7 of 13 metric lines are `N/A`; TASK/REVIEW references dangle for anyone without the repo; `V_B`, `V_R`, `V_C`, `V_M`, `V_T` are never defined; `AUC_heat_mean` is not heat diffusion by the file's own note; *"optimised"* equals *"default"*; and §6 promises "provenance, controls run, cohort" which is not there. |

## Corrections

- **Item 3 — `8QYR` is labelled "(apo)" in `artefacts/README.md`.** The reviewer
  states `8QYR` is the mavacamten-complexed pre-powerstroke structure and *Bos
  taurus*, while the register's apo input is `8QYP`, whose N matches the shipped
  matrix. **Blocked on [[TASK-0368]] item 3** for the correct ID; fix the label
  either way, and disclose the species.
- **Item 20 — the BCR `hit_list.json` ships an unmentioned site-level result**:
  1 site of 56 residues, **zero overlap** with the true pocket, centroid 20.4 Å
  away, `knob_spread: UNSTABLE` (Jaccard min 0.0). Either explain it or remove it.
  Shipping it silently is the worst of the three options.
- **Item 21 — the cardiac five are one site**, not five. Acknowledge it in the
  README; the challenge accepts residue indices, but a chemist reading five
  numbers will assume five candidates. **Blocked on [[TASK-0368]] item 4** for the
  biology.
- **Item 26** — `*_ci` fields are `[estimate, lo, hi]` and read as `[lo, hi]`
  unless documented; the MYC JSON lacks the verdict fields the README promises;
  and **the package README gives the size as 6.3 MB in §B and 8.8 MB in §C**
  (8.8 is correct — mine, from updating one section and not the other).
- **The artefacts README oversells §2.** It says Section 2 argues *"why this metric
  proxies biological signal transmission"*. Section 2 argues that **it does not,
  beyond distance**. Say that plainly — it is the honest answer to §5's third
  deliverable and consistent with everything else we ship.

## Constraints

- **Do not change any shipped number or residue.** These are what the method
  produced. Everything here is labelling, documentation, and removing claims the
  files should never have made.
- Anything blocked on [[TASK-0368]] stays blocked. Do not guess at structure
  identity, chain, or numbering.
- Re-verify the package size and the per-file inventory after changes, and keep
  `README.md` §B and §C consistent with each other — the inconsistency above is
  exactly what happens when they are edited separately.

## Planned Validation

After the fixes: re-read every shipped `report.txt` and `hit_list.json` and
confirm **no file asserts a result the Concept Proposal disclaims**. That is the
check whose absence produced item 6.
