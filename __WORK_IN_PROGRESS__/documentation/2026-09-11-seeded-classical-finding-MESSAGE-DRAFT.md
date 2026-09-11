# One thing we found in `seeded_classical`, and how

*Draft, 2026-09-11. Not sent.*

---

Short version: **your `p = 2.3e-12` result is real, and it is not about coherence.**
We think your own README describes it as something it isn't, and you'd want that
before a reviewer does.

## What we were doing

We went looking for results on your branch that hadn't reached us — we had already
found one positive reported to us as a negative (Model 1, topology→MIN_HOP, AUC
0.793) and wanted to know whether there were more. Read-only, no re-runs.

## What we found, and verified

`seeded_classical/README.md` reports the seeded CTQW beating the heat kernel
`e^{-Lt}`, 0.600 against 0.512, Wilcoxon `p = 2.3e-12` on 630 proteins, and frames
it as *"the exact classical twin: same Laplacian, same seed"* — one variable,
amplitudes versus probabilities.

We reproduced the numbers from `sc_{0..7}.json` exactly. Then we read the script
that makes them.

**`seeded_classical.py:76`**

```python
ns=len(y); ctqw=1.0-(np.asarray(v["ranks"][FIX],float)-1)/max(ns-1,1)
```

with **`FIX = "gauss|sym|neg_dE"`** at line 25.

The CTQW arm is never computed in that script — it is read from precomputed ranks
in `r2_minhop1.json.gz` for one fixed cell. The heat-kernel arm *is* computed
there, fresh, on the plain Laplacian `L` (lines 44–52).

So the two arms differ in **two** things, the operator *and* the score. The CTQW
arm never touches the Laplacian the heat kernel uses.

## Why that matters for the conclusion

`ALL_RESULTS_SUMMARY.md:99–104`, your own analysis of your own best score:

> Our best score reproduces **exactly (ρ = 1.0000)** from the diagonals of H and H².
> It sees only two-step neighbourhoods… it carries **no phase, no interference, no
> long-range coupling**, and the same formula on the classical operator gives the
> same numbers.

`neg_dE` is phase-free by your own measurement. So a comparison whose quantum arm
is `neg_dE` cannot be evidence about coherence, at any p-value.

## What the result actually is

A well-powered finding about **operator and score choice**: a two-step
energy-uncertainty score on a Gaussian symmetric-normalised operator beats a
plain-Laplacian heat kernel, n = 630, p = 2.3e-12. That is worth reporting. It is
just a different claim from "coherence does something".

## Consequence for the disagreement

There isn't one. Our null toggles `coherent=True/False` on a **fixed** Hamiltonian,
seed, cohort and scoring. Yours changes the operator and uses a phase-free score.
Two different questions, both internally sound, neither refuting the other — so no
reconciliation is owed and neither branch has to give anything up.

## The part we'd pass on regardless

We reproduced your numbers to four decimals **and that is exactly what hid this**.
The arithmetic was never wrong; what the arm *was* was wrong. Reproducing a number
verifies arithmetic — only reading the code that produces it verifies what was
measured. It is the second time this has caught us too (we once wrote that our
results were "consistent with" a published ρ≈0.95 we then measured at 0.41).

And the specific way it survives here is worth naming: **the file that states the
claim is not the file that computes it.** That is not carelessness, it's just how
a README and a script drift apart.

## One ask

If you agree, `seeded_classical/README.md`'s "exact classical twin — same
Laplacian, same seed" line needs changing, and the result is worth keeping under
its true heading. If we've misread the code, tell us and we'll correct our own
record — we've already marked the finding superseded on our side pending your
answer.
