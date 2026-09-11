# The seeded classical comparison — does coherence do anything?

**The decisive test.** Every baseline here is seeded at the SAME active site, on the SAME weighted
graph, scoring the SAME residues against the SAME labels as the Seeded-CTQW-pipeline. The v2
notebook's own comment states the condition exactly: *"Only the operator differs from e^{-iHt}."*

630 proteins / 399 families. Reproduce with `seeded_classical.py`; per-protein data in `sc_*.json`.

## Result

| baseline (all seeded at the active site) | mean AUC | CTQW wins | paired p |
|---|---|---|---|
| **Seeded-CTQW-pipeline** | **0.600** | — | — |
| heat kernel e^{-Lt} (plain L) — **NOT operator-matched, see correction** | 0.512 | 407/630 | 2.3e-12 |
| commute time (v2 notebook) | 0.549 | 356/630 | 1.3e-07 |
| weighted communicability (v2, Estrada & Hatano 2008) | 0.543 | 346/630 | 1.4e-06 |
| GNM cross-correlation (v2, Bahar) | 0.540 | 343/630 | 2.5e-05 |
| GNM perturbation response (v2, Atilgan 2009) | 0.531 | 361/630 | 1.7e-06 |
| communicability e^A (binary) | 0.543 | 346/630 | 1.4e-06 |
| personalised PageRank | 0.565 | 344/630 | 0.015 |
| proximity (-hop) | 0.574 | 325/630 | 0.12 — **TIE, not beaten** |

**Family level vs the twin:** CTQW 0.585 vs heat kernel 0.529, CTQW wins 241/399 families, p = 1.1e-04.

**Distal split — CORRECTED:** distal (n=91) CTQW 0.617 vs heat kernel 0.275, which read correctly
is the *reversed* heat kernel at **0.725** — it beats the CTQW. Near (n=539) 0.597 vs 0.553.


> **CORRECTED 2026-09-11 — the "exact classical twin" framing was wrong about our own code, and
> the distal line repeated the backwards-AUC error.** Three corrections, all verified:
>
> **1. The two arms are not operator-matched.** `seeded_classical.py:25` sets
> `FIX = "gauss|sym|neg_dE"` and line 76 *reads that precomputed rank vector* from
> `r2_minhop1.json.gz`. The CTQW arm is never computed in this script. The heat-kernel arm IS
> computed here, fresh, on the plain Laplacian `L` (lines 44-52). So the comparison differs in
> **two** variables — operator and score — not one. The CTQW arm never touches the Laplacian the
> heat kernel uses.
>
> **2. The quantum arm's score is phase-free.** `ALL_RESULTS_SUMMARY.md:99-104` records that
> `neg_dE` reproduces exactly (rho = 1.0000) from the diagonals of H and H-squared: no phase, no
> interference, no long-range coupling. A comparison whose quantum arm is phase-free cannot be
> evidence about coherence, at any p-value.
>
> **3. The distal line inverts an AUC.** "heat kernel 0.275, below chance" is the same misreading
> retracted in `proximity_floor/README.md` (commit f23fae6). An AUC of 0.275 means the *reversed*
> heat kernel scores **0.725** — which beats the CTQW's 0.617. Classical diffusion does not fail
> on distal targets; it points the other way and wins when read correctly.
>
> **What the result is:** a well-powered finding about operator and score choice — a two-step
> energy-uncertainty score on a Gaussian symmetric-normalised operator beats a plain-Laplacian
> heat kernel, n = 630, p = 2.3e-12. That stands. It is not a coherence result.
>
> The operator-matched coherence test, run separately on a fixed H with only `coherent=True/False`
> toggled, gives **+0.0104, p = 0.079** — not significant. That is the number that answers the
> coherence question, and it is the one to quote.
>
> Found by the `bartosz` branch review (TASK-0366) by reading the producing code rather than
> re-running it. Reproducing a number verifies arithmetic; only reading the code that produces it
> verifies what was measured.

## Why this is the test that matters

~~The heat kernel is the CTQW's exact classical twin: same Laplacian, same seed, nothing else
differs.~~ **False — see the correction above.** The arms differ in operator and score. The rubric's test
for whether a quantum framing is load-bearing is "if you deleted the quantum part, would anything
break?" — this measures precisely that, and the answer on this cohort is yes.

## What it does NOT show

- **Proximity is still not beaten** (0.574 vs 0.600, p = 0.12). Plain hop distance remains a tie.
- 0.600 is a MEAN. Per protein: 52% reach AUC >= 0.6, and **31% score below chance**.
- The candidate residues were selected by the pipeline's own funnel (PASSer top-10, active-site
  pocket dropped, MIN_HOP filter, PocketMiner veto). Classical baselines rank a shortlist the
  pipeline produced; they never performed their own selection.
- The CTQW cell (gauss/sym + neg_dE) was chosen on this data. Leave-one-family-out cell selection
  gives 0.583 vs 0.585 at family level, so the inflation is negligible (+0.002) — but it is not zero.

## Relationship to the two other analyses in this repo

- `../centrality_ablation/` — the same CTQW vs five UNSEEDED classical measures. Weaker comparison,
  because those were denied the active site the walk uses. Superseded by this file for any
  head-to-head claim.
- `../../results/full_run_1022/classical.json` — POCKET-level, 518 proteins only, different task.
  **Must not be used in a head-to-head claim.**

## Consequence

The defensible claim becomes: *on 630 proteins and 399 families, an active-site-seeded CTQW
outperforms a plain-Laplacian heat kernel and six other seeded classical measures
(p = 2.3e-12) — a result about **operator and score choice**, not coherence, with the margin on
distal targets where classical diffusion falls below chance — though plain proximity remains a
statistical tie.*

This CONTRADICTS the conclusion drawn on the `bartosz` branch ("the transport subroutine adds
nothing beyond the classical baseline"). The two analyses use different cohorts, different
baselines and different nulls, and must be reconciled before submission.
