# TASK-0370 — The shipped artefacts: contradictions with the proposal, missing definitions, and a hit list that cannot be reproduced

- Status: Done
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

## Done — 2026-09-12, Implementer

**Item 6 (fix the generator, not the file — literal, per this task's own
Constraint).** `src/allostery/report.py`:
- `_consensus_confidence_statement`: all three branches now say "unverified"
  instead of "high"/"moderate"/"low"; the full-agreement branch cites the CP's
  own §2 measurement that these operators are correlated distance detectors,
  not independent evidence.
- `verdict_template`: added optional `target_name=`/`structure=` kwargs
  (prepend a header line; omitted entirely when both are `None` — backward
  compatible) and a `ci_overlap` reconciliation on the DECISION-SUPPORT block,
  so a "meaningful"/"genuinely helps" DAUC line is qualified whenever the
  already-rendered CI-overlap diagnosis says the same gain is statistically
  indistinguishable from the trivial floor.
- `tests/test_report.py`: renamed the test that used to assert "Confidence:
  high" to assert "unverified" instead; added 6 new tests for the header line
  and the CI-overlap qualifier. `pytest tests/test_report.py -q` → **41
  passed**.
- Applied by hand to the four shipped `report.txt` files, appending only the
  verified new substrings next to the original, untouched numbers (full
  regeneration from the *displayed* 3-decimal AUCs was tried and rejected —
  it does not reproduce the shipped values bit-for-bit, e.g. recomputes
  KRAS's +0.171 as +0.172 from rounded inputs; this task's Constraint forbids
  changing any shipped number). KRAS/BCR/CARDIAC each got a
  `Target: <name> | Structure: <id> (...)` header and a CI-overlap caveat on
  the DAUC lines that needed it; MYC_MAX's confidence line was replaced with
  the exact fixed-generator output for its consensus.

**Item 3.** `artefacts/README.md`'s connectivity-matrix table: `8QYR` (apo) →
`8QYP` (apo), `8QYR` relabelled as the holo/mavacamten structure it actually
is. Sourced from `config/targets.yaml` (`apo_pdb: 8QYP`, `holo_pdb: 8QYR`,
`apo_chains: ["A"]`), cross-checked by parsing both structures with ProDy:
chain A of `8QYP` (not `8QYR`) contains all 5 shipped hit-list residues, and
`8QYP`'s N (704) matches the shipped matrix, `8QYR`'s does not. Independently
confirmed a third way after the fact: `PHASE1_SUBMISSION_V4.md` §1's own
deviation table states `8QYP → 8QYR` (apo → holo) for cardiac myosin. Species
(*Bos taurus*) disclosed, was previously omitted. Not blocked — this task's
own text authorizes fixing the label "either way" independent of
[[TASK-0368]]'s biology.

**Items 20/21.** New `artefacts/README.md` subsection covering both: the
BCR_ABL1 `sites` block (56 residues, 0 overlap with the true pocket, centroid
20.4 Å away, `knob_spread: UNSTABLE`, Jaccard-min 0.0) disclosed as a failed
secondary result, not a second answer; the cardiac five acknowledged as one
coupled cluster (680–683 sequential, coupling to 127/128/134 confirmed
directly in the shipped matrix), not five independent candidates. The
mechanistic "why" for both stays deferred to [[TASK-0368]], as this task's
own Constraint requires.

**Item 22.** Added a `chain` column to `hit_list_all_targets.csv` (2nd
position). `A` for every target except `MYC_MAX`, whose two chains (`A` =
c-Myc, `B` = Max, per `config/targets.yaml`) were resolved per-residue via
ProDy against the deposited `1NKP` structure, not assumed uniform.
UniProt-equivalent numbering stays open, tracked against [[TASK-0368]] per
this task's own Constraint.

**Item 23.** New `artefacts/README.md` paragraph stating the matrix-entry
formula in plain terms: entry (i,j) is the time-averaged CTQW transition
probability from residue i to j, rows sum to 1 (±1e-6), diagonal is the row
max in ~78% of rows (recomputed directly from the shipped `CARDIAC_MYOSIN`
matrix via numpy: 78.27%, matching the reviewer's own cited figure — checked,
not trusted). States the naive-heatmap implication (reads diagonal-bright;
mask the diagonal or use a log/percentile scale).

**Item 24.** New "Seed residues, per target" table in `artefacts/README.md`,
computed by re-running this repository's own
`allostery.labels.build_labels`/`functional_indices` (the same call the
shipped numbers came from, via `scripts/run_challenge.py`'s real
orchestration path — not a guessed active-site detector). Confirmed zero
overlap between each target's seed set and its own top-5 hit list for
KRAS/BCR/CARDIAC, as the pipeline's exclusion logic requires. **Disclosed
finding, not smoothed over**: MYC_MAX's seed set is bit-identical to its own
shipped top-5 hit list — `func_ligand: DNA` matched nothing in the apo
structure, so `functional_indices` fell back to its own logged
topological-degree-proxy warning, and the consensus ranking (itself
degree-correlated) converged on the same five residues the fallback seed
already named. Documented as a circular result, consistent with this
project's other proximity/degree-confound findings, not as corroboration.

**Item 25.** `artefacts/README.md` §3: corrected the reversed claim about
what Concept Proposal §2 argues (it argues the metric does *not* proxy
biological signal transmission beyond distance, not that it does); added a
table defining `V_B`/`V_T`/`V_R`/`V_C`/`V_M` — **sourced from
`src/allostery/potentials.py`'s own docstrings, not the Concept Proposal**,
which does not name them (verified: zero matches for these terms in both
`PHASE1_SUBMISSION_V1.md` and the actual current `PHASE1_SUBMISSION_V4.md` —
see the correction note below); clarified `AUC_heat_mean` is `H_new`'s own
ground-state relaxation score, not a diffusion baseline; clarified
"optimised" means the default configuration (`AUC_apo_Hnew_optimised ==
AUC_apo_Hnew_default` in every shipped file — checked). Report headers added
per item 6 above cover the missing target/PDB identification.

**Item 26.** `artefacts/README.md` documents the CI array order
(`[estimate, lower, upper]`, not `[lower, upper]`) and explicitly scopes
"the JSON carries a verdict" to the three targets where one exists —
`MYC_MAX`'s JSON has no verdict/CI fields by design (`1NKP` has no
drug-bound structure), not a gap. `SUBMISSION_PACKAGE/README.md`'s stale
6.3 MB package-size line (§B) corrected to 8.8 MB, matching §C.

**Self-caught correction, mid-task (disclosed per this project's
truthfulness convention, not hidden):** items 25's `V_B`/etc. claim and this
README's other Concept-Proposal cross-references were first drafted assuming
`PHASE1_SUBMISSION_V1.md` — the document this same thread had been editing in
the immediately preceding TASK-0332/0343/0344 work. A routine verification
grep caught that "V_B" does not appear in V1 at all. Further checking
(`git log -- .../01_Concept_Proposal.pdf`, commits `9f1d521`/`48033c8`)
showed the actual shipped Concept Proposal PDF is now built from
`PHASE1_SUBMISSION_V4.md`, advanced by other threads' work in parallel and
not previously visible to this thread. Re-verified every Concept-Proposal
cross-reference in `artefacts/README.md` (§1/§2/§6 citations, the "five-guess
table" match, the "cannot disagree with each other" quote) directly against
V4's real, current text: all held except the V_B/etc. claim, which is fixed
above. V4 has no numbered "Finding N" statements anywhere — the "Finding 3"
citations in `report.py`, `test_report.py`, `MYC_MAX/report.txt`, and
`artefacts/README.md` (all referring to the operators-are-distance-detectors
result) were corrected to cite §2 by content instead of a finding number that
does not exist in the document.

**Planned Validation.** Re-read all four shipped `report.txt` files and
inspected all four `hit_list.json`'s top-level verdict fields directly:
KRAS/BCR/CARDIAC's `residue_level_floor` all report `diagnosis:
NO_SIGNAL_IN_APO`, `ci_overlap: true`, consistent with the CP's "we submit
the five as required and state plainly that we cannot certify them"; MYC_MAX
carries no verdict/CI fields at all, consistent with its "no ground truth"
framing. No shipped file asserts a result the Concept Proposal disclaims.

**Out of scope, left alone per this task's own Constraints:** item 4
(substitution-reason text — tracked to [[TASK-0368]]); UniProt-equivalent
c-Myc numbering (item 22's remainder — [[TASK-0368]]); the mechanistic
biology behind items 20/21 ([[TASK-0368]]).


---

## Item 3 unblocked, 2026-09-12 (Reviewer)

The cardiac label fix **no longer waits on [[TASK-0368]]**. The register settles it:
`TASK-0003:91/:102` records `8QYR` as the **`holo_validation` substitute**, confirmed
*Bos taurus* MYH7 at 1.80 Å; `TASK-0114:113` records **`8QYP`, N=704**, matching the
shipped matrix exactly.

**`artefacts/README.md` should read `8QYP` (apo), not `8QYR` (apo)** — a label error,
not a wrong structure. The scanner was not run on the drug-bound structure, and the
README currently says it was.

Disclose the **bovine** origin while fixing it: our own register confirmed it and the
submission has never mentioned it. Berke still reviews the biological reading; the
label itself does not need him.
