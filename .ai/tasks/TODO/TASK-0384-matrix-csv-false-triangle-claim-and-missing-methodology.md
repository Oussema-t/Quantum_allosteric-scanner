# TASK-0384 — The matrix CSV states a false reconstruction rule, and output 1's methodology is in a file nobody receives

- Status: TODO
- Owner: Implementer
- Priority: **High and FREE — costs no Concept Proposal page budget.** Take this one regardless of what is decided about §1's space.
- Filed: 2026-09-13 by Reviewer thread
- Source: [[REVIEW-2026-09-13-adversarial-submission-package]] §A3, §D
- Related: [[TASK-0370]]

## Part 1 — "upper triangle only" is false, and it can actively mislead

Independently verified by the Reviewer, counting rows in the shipped
`Connectivity_Matrices.csv`:

| target | rows | rows with `residue_i > residue_j` |
|---|---:|---:|
| KRAS_G12C | 14,535 | 0 |
| BCR_ABL1 | 101,926 | 0 |
| CARDIAC_MYOSIN | 248,160 | 0 |
| **MYC_MAX** | **14,706** | **7,304** |

Cause: `1NKP` chain A numbers 897–984 and chain B numbers 202–284, so **array
order and residue-number order disagree**. The file is still *correct* — verified
**0 duplicate unordered pairs** and **379,327 distinct pairs**, matching the
README exactly — but both of these statements are wrong:

- CSV header line 2: *"Symmetric, so only i <= j is listed"*
- `SUBMISSION_PACKAGE/README.md`: *"**Upper triangle only.**"*

**A reviewer reconstructing MYC_MAX by assuming `i <= j` silently mis-places
7,304 rows.** Reword both to **"each unordered pair is listed exactly once"**.

This is the only item in the whole review that can cause a reader to compute a
wrong answer from a correct file. That is why it is first.

## Part 2 — the methodology landed in a file we do not upload

`artefacts/README.md` explains that a matrix entry is the time-averaged
transition probability, that rows sum to 1, that the diagonal is the row maximum
in ~78% of rows, and that a naive heatmap therefore reads as diagonal-dominated.
The external reviewer verified all four claims independently and they hold.

**But `artefacts/` is not one of the five uploaded files.** The scorer receives
only `Connectivity_Matrices.csv`, whose header says nothing beyond "value =
time-averaged quantum connectivity strength, dimensionless, 6 significant
figures."

Move those four sentences into the CSV header comment block. It is the **only
place the methodological content of §5 output 1 reaches a scorer**, and it costs
nothing.

## Part 3 — decide on the `#` preamble, knowingly

Four `#` comment lines precede the header row, so `pd.read_csv(path)` without
`comment='#'` fails. The organisers' own answer was *"formats accessible with
conventional software."*

Note the tension with Part 2, which **adds** header lines. Options:
- Keep `#` comments and accept it (they are conventional for CSV and `comment='#'`
  is one argument) — but then Part 2 makes the preamble longer.
- Move the prose into a sibling plain-text block inside the PDF (file 5) and keep
  the CSV header minimal.

Reviewer's read: **keep the comments and expand them.** A scorer who cannot pass
`comment='#'` is not reconstructing the matrix anyway, and the alternative buries
output 1's methodology in a different file again — which is the defect being
fixed.

## Part 4 — no `chain` column in the matrix CSV

`hit_list_all_targets.csv` gained one; the matrix did not. MYC_MAX is the
two-chain case and it survives **only because the numbering ranges happen not to
collide** (897–984 vs 202–284). Our own register already knows fpocket residue
numbers are chain-agnostic; this is the same trap one level up.

Adding a `chain` column changes the row format and the README's documented
schema. **Decide explicitly**: add it, or state in the header that MYC_MAX
numbering is unambiguous across its two chains and give the two ranges. The
second is cheaper and sufficient.

## Part 5 — one line the README should claim, because it is checkable

The external reviewer tried to break the matrices four ways and could not:
reconstruction reproduces all four per-target artefact matrices exactly
(max |diff| = 0.0 over 2,000 sampled entries per target), all symmetric to 1e-9,
row counts exact. **Say so in the README in one line.** Most submissions will not
survive that check and ours does.

## Done when

- Both "upper triangle" statements reworded and `grep` confirms no third copy.
- CSV header carries the entry definition, row-sum and diagonal facts.
- Part 3 and Part 4 decided in writing here, not left implicit.
- Round-trip re-verified after any header change (the parser must still skip the
  right number of lines).
