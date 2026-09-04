# Allosteric-site prediction — results, methods and parameters

Team AuraQu · Cleveland Clinic Quantum + AI Challenge · branch `allosteric`

Everything here was measured by `Quantum_Allosteric_Scanner_v2.ipynb` in this directory.
Numbers are quoted with the configuration that produced them. Where a result is exploratory,
tuned, or confounded, it says so **in the same table as the number** — the honest reading is
that this project currently has **one** defensible positive and a large amount of well-measured
negative and infrastructural work around it.

---

## 1. Headline

| claim | status |
|---|---|
| HIV1-RT, pre-registered, held out (§14f) | **AUC 0.697, p = 0.0175** — the one defensible positive |
| KRAS / BCR-ABL1 high scores | **confounded** — proximity-inflated or high base rate (§6) |
| Green's function beats CTQW | **not established** — its two free parameters span AUC 0.350–0.691 (§5.3) |
| Most benchmark pockets are distal | **false** — only **13%** are (§3.2). Most cannot test propagation at all |
| Topology predicts pocket distance | only **algebraic connectivity**, ρ = −0.477 after size control (§3.3) |
| Pocket-seeded CTQW at scale (138 proteins) | **+0.03 AUC over a permutation null**, signal in ~15 proteins only; P@5 gains nothing (§6b) |
| fpocket ∩ PASSer as pocket selector | **3× the clearing rate** of fpocket alone, first P@5 = 1.0 proteins (§6b.3) |
| The right pocket is often never proposed | **22–30% of proteins** — detector-limited, before physics (§6b.1) |

---

## 2. What was built

| component | what it does |
|---|---|
| §7b | **measures** every fpocket cavity: druggability, PASSer allostery rank, PocketMiner accessibility state |
| 13z | **selects** which pockets seed the walk (all seed knobs live here) |
| §14 | runs the CTQW over 14 operators × 18 scores, applies `MIN_HOP` |
| §14y | head-to-head propagator comparison on one target |
| §14f | the pre-registered test: operator, score and null fixed in advance |
| 4b–4h | external-benchmark catalog, audit, distances, topology, classes, relationship test |

### 2.1 PocketMiner, ported and validated

PocketMiner (Meller et al. 2023, *Nat Commun* 14:2135) runs **natively on macOS arm64, no Docker**:
python 3.9.6 + `tensorflow-macos 2.13` + `mdtraj 1.10.3`, gvp pinned at `187062d`.
TF ≥ 2.11 needs `tf.keras.optimizers.legacy.Adam` or the checkpoint restore raises.

**Port validated against upstream's own held-out set: pooled AUC 0.868 over 35 structures /
1846 labelled residues**, versus ~0.87 published. Recipe in `tools/pocketminer/`.

Dead ends recorded so they are not repeated: Rosetta/x86_64 fails because TF wheels require
AVX, which Rosetta does not emulate (`Abort trap: 6`); no `tensorflow<=2.9` wheel exists for
macOS arm64.

---

## 3. The benchmark (1233 proteins, five datasets)

### 3.1 Composition and audit

Measured against RCSB's own ligand inventory, **not** the datasets' labels:

| dataset | n | genuine apo→holo | problem |
|---|---|---|---|
| ASBench | 110 | **0** | 108/110 already contain the annotated allosteric ligand |
| CASBench | 314 | **0** | single structures, no holo at all |
| CryptoBench | 1107 | 979 | the workhorse; 1 structure per protein, no pseudo-replication |
| CryptoSite | 21 | 21 | partial subset — full 93 is behind a paywalled SI |
| PocketMiner | 55 | 42 | 55 structures are only **14** proteins |

**1042 of 1607 are genuine apo→holo pairs.** ASBench/CASBench annotate allosteric sites *on
ligand-bound structures*: usable for ranking, not for cryptic-pocket prediction.

### 3.2 How far is the allosteric site from the active site?

Measured on the 8 Å Cα contact graph, aggregated to protein families:

| group | structures | families | median hop | median Å | **distal** |
|---|---|---|---|---|---|
| curated allosteric | 422 | 106 | 2.0 | 10.1 | **23%** |
| drug-contact | 598 | 582 | **0.0** | **0.0** | **7%** |
| ASBench | 109 | 73 | 2.0 | 11.1 | 45% |
| CASBench | 313 | 33 | 1.0 | 5.2 | 15% |

*(distal = min_hop ≥ 2 **and** min_euclid > 12 Å)*

**138 of 1020 proteins (13%) are distal — 86 independent families.** For the other 882 the
target sits on or beside the seed, so "finding" it demonstrates proximity, not propagation.
The drug-contact median of 0.0/0.0 means those cryptic pockets frequently **are** the active site.

### 3.3 Does topology predict that distance?

Distal curated families (n = 43), Spearman, raw vs partial (controlling `n_residues`):

| feature | raw ρ | partial ρ | p |
|---|---|---|---|
| **algebraic connectivity** | −0.531 | **−0.477** | **0.0014** |
| graph diameter | 0.392 | 0.301 | 0.053 |
| n_edges | 0.282 | 0.111 | 0.485 |

Only the Fiedler value survives size control: **loosely-connected (two-lobed) proteins have more
distant allosteric sites.** Everything else was protein size in disguise.

Unsupervised structural classes (4h): silhouette **0.257 / 0.267** — no natural grouping; these
proteins are one continuum. Clustering on raw features "predicts" pocket distance at p = 0.0002;
strip size out and it is p = 0.91.

---

## 4. Pocket selection (cell 13z)

Three measurements, one decision:

| tool | measures | knob |
|---|---|---|
| fpocket | cavity geometry → druggability | `N_SEED_POCKETS` |
| PASSer | supervised ASD classifier → allostery | `SEED_TOP_K` |
| PocketMiner | cryptic opening → accessibility | `SEED_PM_STATES` |

```python
SEED_SOURCE  = "fpocket" | "consensus" | "threeway" | "triple"
SEED_TOP_K   = 10
SEED_COMBINE = "minrank" | "rrf" | "both"
SEED_WEIGHTS = (1.0, 1.0, 0.5)     # druggability, allostery, accessibility ("rrf" only)
SEED_PM_STATES = ("OPEN(lig)", "CRYPTIC", "mixed")   # only "no-open" is excluded
MIN_HOP = 2                         # owned by §14, not 13z
```

**Accessibility must be a score, not a filter.** `OPEN(lig)` → 1.0 (a ligand is already in it),
`no-open` → 0.0, otherwise the calibrated cryptic percentile. An already-open pocket is the
*easiest* to drug; ranking by cryptic-ness demotes exactly the pockets that need no opening.

### 4.1 Selection failures found (each one silently zeroes P@5)

| target | true pocket | druggability | allostery | accessibility | consequence |
|---|---|---|---|---|---|
| KRAS_G12C | P2 | #6 | #2 | #4 | dropped by `fpocket` top-5 |
| HIV1_RT | P1 | **#11** | **#3** | #21 | dropped by `fpocket` top-5; **0 drug seeds at every `MIN_HOP`** |
| CARDIAC_MYOSIN | P96 | #3 | #3 | **#65 `no-open`** | PocketMiner is **wrong**; `minrank` lets one bad axis veto |

Two lessons, both now enforced by the cell's own output:
- **fpocket alone is not enough.** On HIV it ranks the true pocket **11th** while PASSer ranks it **3rd**.
- **PocketMiner is a predictor (~0.87 AUC), not ground truth.** As a hard gate its errors become yours.

13z prints, per target, whether the true pocket survived and **which axis excluded it**, plus the
base rate at each `MIN_HOP` — so a null result caused by seeding is distinguishable from one
caused by the method.

---

## 5. Methods and their parameters

### 5.1 Operators
14: `H_new` (`L_norm(α=0.3, r_c=8Å)` + V_B/V_T/V_R/V_C/V_M, λ = 0.08/0.16/0.08/0.04/0.04) plus H1–H12.
**Known defect: `H4_powL` ≡ `H3_normL` at `beta=1.0`** (max diff 2.9e-15) — a duplicate vote in
every consensus. Not yet fixed.

### 5.2 Scores (18, all computed per operator)
`p_avg`, `p_peak`, `R = p_peak/p_avg`, `residual LOG` (primary), `residual RAW`, `residual ± dX`,
`p_avg/dX`, `−E[D]`, `−dD`, `dX dip depth`, **5 × Green** `(E, η)`, `QMI`.

### 5.3 Propagators — and the parameter asymmetry that matters

| method | free parameters |
|---|---|
| CTQW average mixing (`p_avg`) | **none** — `M = Σ_k |v_k(i)|²|v_k(j)|²`, fixed by `H` |
| Szegedy discriminant | **none** |
| Green's function | **`E`, `η`** |
| CTQW finite-t, QMI | `t` |
| classical heat kernel (control) | `t` |

**Green's function is not a separate algorithm.** Verified numerically to 7.5×10⁻⁵:
`G(E) = −i ∫₀^∞ e^{iEt}e^{−ηt} U(t) dt` — it is the CTQW propagator, Laplace-transformed.
The real difference is *when you square*: `p_avg` squares then averages (phases destroyed);
Green integrates then squares (phases kept). So Green is the **more coherent** observable, and
`p_avg` is its decoherent limit.

**Its parameters dominate.** BCR-ABL1, one operator, same seeds:
`E=0,η=0.05 → 0.646` · `E=λmax,η=0.01 → 0.427` · `E=median,η=0.2 → 0.440`.
A 4-operator × 4-E × 4-η grid spans **AUC 0.350–0.691** (residualised 0.307–0.863).
Any single Green number is one cell of that grid.

### 5.4 Time parameters — `p_avg` is immune
`T_max = C_T/gap`, `n_t` by Nyquist. **`p_avg` uses no time grid at all** (exact T→∞ closed form),
so `C_T` cannot move it. `p_peak` and `R` are window maxima and do.

**KRAS `C_T` sweep (settles the `C_T=5.0` override):** AUC spread **0.0087** over `C_T` ∈ [0.5, 10];
`C_T=1 → 0.7587` vs `C_T=5 → 0.7616`. **Top-5 identical, same order, at all seven values; P@5 = 0.6
throughout.** The override was harmless — report at `C_T = 1`.

---

## 6. Results per target, with the configuration that produced them

| target | operator | score | AUC | P@5 | configuration | honest status |
|---|---|---|---|---|---|---|
| **HIV1_RT** | `H_new` fixed | residual (closed-form `p_avg`) | **0.697** | — | §14f, 2000× label permutation, **p = 0.0175**, n=281 seeds | ✅ **pre-registered, held out** |
| KRAS_G12C | `H3_normL` | `p_avg` | 0.828 | 1.0 | `N_SEED_POCKETS=5, MIN_HOP=1, C_T=5` | ⚠️ **proximity-inflated** — P@5 → 0.2 at `MIN_HOP≥2` |
| KRAS_G12C | `H_new` | `p_avg` | 0.762 | 0.6 | consensus seeding, 51 seeds, `MIN_HOP=2` | reference run |
| KRAS_G12C | `H_new` | Green `E=0,η=0.05` | 0.797 | 0.8 | same seeds | ⚠️ residual → 0.465: top-5 is proximity |
| BCR_ABL1 | `H2_combL` | `p_avg` | 0.767 | 1.0 | `MIN_HOP=2`, 23 seeds | ⚠️ **base rate 0.78** — 18/23 seeds already in pocket; apo `1OPL` has MYR bound |
| BCR_ABL1 | `H_new` | `p_avg` | 0.501 | 0.2 | 68 seeds, base 0.26 | chance; residual 0.342 (below chance) |
| BCR_ABL1 | `H_new` | Green `E=0,η=0.05` | 0.646 | 0.8 | same seeds | residual 0.624 — survives here, unlike KRAS |
| CARDIAC_MYOSIN | `H6_exp` | residual LOG | 0.713 | 0.0 | 243 seeds, `MIN_HOP=2` | ❌ **fpocket control = 0.747 beats it** |

### 6.1 Best cells (selection, not results)
KRAS, 5 operators × 18 scores: best AUC **0.837** (`Green E=median,η=0.05` / `H3_normL`),
best P@5 **0.8** (`Green E=zero,η=0.05*` / `H_new`). **The two metrics pick different cells.**
With 14 operators the grid is ~250 cells; the maximum of 250 tries is not a result. Only the
starred pre-registered cell is quotable.

### 6.2 Propagator head-to-head (BCR-ABL1, `H_new`, 68 seeds)

| method | AUC | P@5 | AUC residual |
|---|---|---|---|
| CTQW avg-mixing | 0.501 | 0.2 | 0.342 |
| Green `\|G\|²` | 0.646 | 0.8 | 0.624 |
| Szegedy | 0.574 | 0.2 | 0.601 |
| QMI | 0.544 | 0.4 | 0.384 |
| **classical heat kernel (control)** | 0.523 | 0.0 | **0.611** |

**No quantum method beats the classical control on the residual.** SQW rows are excluded: the
integration window (~6/‖H‖) was too short to distinguish dephasing rates — γ=0.0 and γ=0.5 gave
identical AUC. Not a valid ENAQT test.

Proximity diagnostic on the same target: `ρ(score, hop)` = −0.286 (CTQW), −0.613 (Green),
−0.893 (heat kernel). **Proximity alone scores AUC 0.458 — below chance on BCR-ABL1**, so removing
distance *improves* every method there. That is target-specific and does not generalise.

---

---

## 6b. Pocket-seeded sweep at scale — 138 distal proteins

The §14 experiment run as a **benchmark** rather than per-target: seed the walk from detected
pockets, walk to the active site, score with the full §14 battery, ask whether the drug pocket
ranks first. Two seed selectors compared, each at `MIN_HOP` ∈ {1, 2}. 96 cells per protein
(12 operators × 8 scores). Raw output and scripts: `results/pocket_seeded_sweep/`.

### 6b.1 Coverage — what the selector costs before any walk runs

| selector | testable | lost | why lost |
|---|---|---|---|
| fpocket top-10 by druggability | 106 / 138 | 32 | drug pocket not among the 10 |
| **fpocket ∩ PASSer** (minrank, J ≥ 0.5) | **96 / 138** | 42 | 26 as above, **10 with no fpocket↔PASSer match at all**, 6 fpocket failures |

**In 22–30% of proteins the right pocket was never on the ballot.** That is a property of the
pocket detectors, not of the walk, and it caps any pocket-seeded method before physics enters.

### 6b.2 Against a correlation-preserving null

The per-protein "best of 96 cells" is a **maximum over correlated draws** and cannot be read as
a score. The null permutes the labels against the *actual* score vectors (200 draws, rank-sum
AUC), so it preserves the correlation between cells.

| run | best-of-96 AUC | null | Δ | p | best-of-96 P@5 | Δ P@5 | proteins p<0.05 |
|---|---|---|---|---|---|---|---|
| fpocket, hop 2 | 0.799 | 0.765 | **+0.034** | 2.9e-05 | 0.468 | +0.001 | 19 / 106 |
| consensus, hop 2 | 0.777 | 0.745 | **+0.032** | 1.3e-04 | 0.483 | +0.002 | 16 / 96 |
| fpocket, hop 1 | 0.787 | 0.760 | +0.027 | 1.7e-04 | 0.407 | **−0.017** | 16 / 107 |
| consensus, hop 1 | 0.764 | 0.733 | **+0.031** | 5.0e-04 | 0.463 | +0.006 | 18 / 99 |

**There is a small real effect and it is ~10× smaller than the raw maximum suggests.**
The naive reading ("mean winning AUC 0.798, 108/108 proteins above 0.6") is almost entirely
selection over 96 cells. Against the null the gain is **+0.03 AUC**, concentrated in
**16–19 proteins per run where ~5 are expected by chance** — i.e. roughly 15% of the cohort
carries signal and the rest does not. **P@5 gains nothing** (+0.002), and P@5 is the measure
that decides whether a pocket is actually picked.

### 6b.3 Does the consensus selector help?

| | fpocket hop2 | **consensus hop2** | fpocket hop1 | **consensus hop1** |
|---|---|---|---|---|
| cells clearing AUC > 0.6 **and** P@5 ≥ 0.8 | 24 / 10176 | **54 / 9216** | 9 / 10272 | **32 / 9504** |
| clearing rate | 0.24 % | **0.59 %** | 0.09 % | **0.34 %** |
| proteins reaching P@5 = 1.0 | 1 | **3** | 0 | **2** |

**Yes, on the criterion that matters.** Requiring a pocket to be druggable *and* allosteric
simultaneously roughly **triples the clearing rate** and yields the first P@5 = 1.0 proteins.
Raw AUC falls (0.799 → 0.777) but so does the null (0.765 → 0.745): the candidate set is
smaller and harder, and the *margin over chance* is unchanged. The consensus gain is also
**stable across `MIN_HOP`**, where the fpocket-only selector degrades (P@5 goes negative at
hop 1) — evidence that fpocket-only hits lean on seeds adjacent to the active site.

### 6b.4 Marginals — no cell is good on its own

Family-averaged over 86 clusters, the best of the 96 cells reaches **AUC 0.521**
(`harm/comb` + `residLOG`, consensus hop 2); the full grid spans **0.34–0.54**. `p_avg` alone
runs 0.383–0.435, i.e. *below* chance. Among clearing cells `green_lmax_0.05` is the most
frequent score (14 / 54) and `adj` normalisation dominates the operators.

### 6b.5 Consequence for `H_new`

`H_new` is `L_norm(cutoff, α)` plus a diagonal, so it spans **`exp/sym` and `binary/sym` (α→0)
only**. The `adj` and `comb` normalisations and the `gauss`/`harm` kernels are **outside its
span**, and `adj` is exactly what dominates the cells that clear the bar. Expressing the
observed winners requires the `weight × norm` generalisation (`build_H_general`), not a
retuning of `H_new`'s nine dials.

### 6b.6 Ceiling correction

P@5 = 1.0 needs ≥ 5 truth residues among the seeds; only **69 / 138** proteins have that many,
and P@5 = 0.8 needs ≥ 4 (77 / 138). The **best achievable mean P@5 on this cohort is 0.64,
not 1.0**; observed is 0.58 of that ceiling (hop 2). Quoting P@5 against 1.0 on this benchmark
understates performance for half the set.

### 6b.7 Status

| claim | status |
|---|---|
| Pocket-seeded CTQW finds allosteric sites at benchmark scale | **no** — marginals at chance |
| fpocket ∩ PASSer beats fpocket alone | **yes** — 3× clearing rate, stable across `MIN_HOP` |
| The per-protein "winning Hamiltonian" is meaningful | **only for ~15 proteins** — grouping all 108 would fit noise |
| Green's `|G|²` is the strongest score | **suggestive only** — most frequent among clearing cells, `(E, η)` still unpinned (§5.3) |

---

## 7. Limitations

- **Multiplicity.** §14 evaluates ~250 score × operator cells per target. Only §14f is pre-registered.
- **Seed choice dominates.** Bartosz's `TASK-0118` measured a **0.326 AUC swing** on KRAS from seed
  cardinality alone. It is a KNOB, not a gauge, and must be fixed before any headline number.
- **`H4_powL` duplicates `H3_normL`** — inflates operator agreement.
- **Residual columns** may be unreliable where statsmodels' quantile fit hits its iteration limit
  (observed on BCR-ABL1); the notebook now warns.
- **Green's `(E, η)` is unpinned.** Until pre-registered, no Green number is quotable.
- **SQW is not validated** — window far too short for a steady-state or ENAQT claim.
- **CryptoSite is 21/93**, second-hand provenance (`datasets/cryptosite_PROVENANCE.txt`).
- The benchmark's own premise is weak: **87% of proteins have a non-distal target.**
- **Best-of-N is not a score.** The pocket-seeded sweep's per-protein maximum (0.798) collapses to
  +0.03 against a correlation-preserving null. Any "winning Hamiltonian" table built on maxima over
  the 96-cell grid is selection unless it is null-corrected (§6b.2).
- **P@5 = 1.0 is unreachable for half the cohort** — only 69/138 proteins have ≥5 truth residues
  among the seeds (§6b.6).
- **PASSer consensus shrinks coverage**: 10 proteins have no fpocket↔PASSer pocket match at
  Jaccard ≥ 0.5 and drop out entirely (§6b.1).

## 8. Reproducing

Run order: cell 1 → 4/4b/4c/4d → 4e/4f/4g/4h (analysis) → §5/§6 → §7b → **13z** → §14 → §14y/§14f.
PocketMiner runs **outside** the notebook: `tools/pocketminer/setup_native.sh`, then
`predict_native.py input output`, then re-run §7b. HIV1_RT and PTP1B were exported but
initially unscored — a silent cause of empty seed sets.

Compute: two Hetzner `ccx33` runs, **EUR 0.13 total** (topology over 1233 proteins, 296 s;
site derivation over 809, 768 s). Both deleted after results were pulled.
The pocket-seeded sweep (§6b) added three Hetzner `cx43` runs, **EUR 0.08**, all deleted
(orphaned primary IPs must be deleted separately — they keep billing after the server is gone).
Cumulative HPC spend: **EUR 0.21**.
