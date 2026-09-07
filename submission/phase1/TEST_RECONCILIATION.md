# Two tests, two answers — are they the same test?

**Short answer: no, and the difference is decisive. The stricter test supersedes the looser one,
and the stricter test is the one on the `bartosz` branch.**

Written for the two workstreams to agree on a single number before submission.

---

## The apparent contradiction

| | allosteric branch (this analysis) | bartosz branch (the v53 submission) |
|---|---|---|
| headline | +41 families over chance, p < 0.001 | no arm clears more than 5 of 276 families |
| raw count | 115 families clear P@5 >= 0.8 | BH-FDR survivors 0 of 110 |
| quantum vs classical | not tested in this run | indistinguishable, McNemar p = 1.0 |

These look irreconcilable. They are not. They are different tests, and one of them is wrong.

---

## The tests are NOT identical — five differences

| | this analysis | v53 submission |
|---|---|---|
| **null model** | label permutation *within* protein: shuffle which residues are positive, keep n_seeds and n_drug | **spatially matched pocket-block null**: preserves the real positives' own spatial concentration |
| multiplicity | corrected within protein (221 cells); NOT corrected across families | matched multiplicity across arms, one candidate set |
| unit / metric | family clears if ANY cell reaches P@5 >= 0.8 | BH-FDR survivors at cell level |
| cohort | 630 proteins / 399 families, MIN_HOP=1 | 1022 proteins / 276 families |
| classical comparison | absent from this test | present (McNemar) |

The first row is the one that matters. The rest are refinements.

---

## Why the null model decides it

A real allosteric pocket is a **spatially contiguous cluster of residues** on the protein surface.
It is not a random scatter of residue indices.

My null destroys that structure. Permuting labels within a protein takes a compact 20-residue
pocket and scatters those 20 positives uniformly across ~40 candidates. So the null asks:
*"can the walk beat a randomly scattered target?"*

Any method that concentrates its top-5 on **any** contiguous surface patch beats a scattered
target — without knowing anything about allostery. Contact-graph methods concentrate by
construction, because neighbouring residues have similar connectivity. So the comparison is
rigged in the method's favour before allostery enters.

The pocket-block null fixes exactly this: it plants a null "pocket" with the same spatial
concentration as the real one, and asks whether the method finds the *right* blob rather than
*a* blob. That is the question the challenge actually poses.

**The measured effect of this correction on the v53 side was 45 BH-FDR survivors -> 0.** A
correction that removes 45 of 45 survivors on one cohort will not leave +41 families standing on
another. My +41 is very likely the same artifact, uncorrected.

---

## Conclusion

**My +41 families should not be reported.** It is measured correctly against the null I chose, and
the null I chose is inadequate for spatially clustered targets. It answers a question nobody asked.

**The v53 number is the defensible one.** Its null is harder, its multiplicity handling is stricter,
and it includes the classical comparison that this test omits.

What survives from this analysis is narrower and still worth stating: selection over 221
configurations manufactures ~74 families from pure chance (range 65-84), so **any raw
best-of-N count in this project is roughly three-quarters artifact before any other correction is
applied**. That is a useful independent confirmation of why the v53 submission refuses to quote
raw counts.

## What both workstreams should do

1. **Do not submit the raw counts** (137 families / 240 proteins / "260 proteins with P@5 >= 0.8").
   They do not survive either null.
2. **Re-run this analysis under the pocket-block null** before quoting any number from the
   `allosteric` branch. Until then the branch has no chance-corrected headline.
3. **Quote one number, from one test, on one cohort.** A reviewer who finds two numbers from the
   same team asks which is true, and the answer "both, different tests" reads as unresolved.

---

*Reconciliation performed 2026-09-07. The permutation test behind the +41 figure is at
`/tmp/permtest.py` logic reproduced from `r2_minhop1.json.gz`; the pocket-block null is on the
`bartosz` branch.*
