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
| `H_new` vs its own base `exp/sym` (λ=0) | **+0.04–0.05 AUC, p = 0.003–0.026, n≈100** — the diagonal site potential is load-bearing (HYP-P4) (§6b.8) |
| Winners are a structural class | **no** — the only separating feature is a 2.5× larger annotated pocket; no topology feature separates them (§6b.9) |
| fpocket ∩ PASSer as pocket selector | **same protein count as fpocket alone (13 vs 13)** but stable across `MIN_HOP` where fpocket-only halves; the earlier "3×" was a cell-count artefact (§6b.3, §6b.8) |
| The right pocket is often never proposed | **22–30% of proteins** — detector-limited, before physics (§6b.1) |
| §14 operator-consensus on one protein is evidence | **no** — at scale the 13 operators agree in 100 % of proteins and elect the drug pocket in ≤ 6 %, below the 9.4 % chance rate (§6b.11) |

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

**At the cell level, yes; at the protein level it is a tie (13 vs 13) — see §6b.8.** The cell
count is inflated by one protein (`ASB_1W25`, 25 cells). Consensus does yield the first P@5 = 1.0 proteins.
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
| `H_new`'s site potential earns its place | **yes** — beats its own λ=0 base on ~100 proteins, p ≤ 0.026 (§6b.8) |
| Winners form a structural class usable for prediction | **no** — only labelled-pocket size separates them (§6b.9) |
| Defensible positives at benchmark scale | **6 distinct proteins at the residue level** (§6b.9); **none at the pocket level** — the two pocket-level candidates are within chance (§6c.3) |
| §14 consensus block generalises | **no** — elects the true pocket ≤ chance (1–6 % vs 9.4 %) while operators agree 100 %; median-rank aggregation is size-biased (§6b.11) |
| Seeding the walk from the WHOLE pocket ranks the drug pocket first | **no** — top-1 8–11 % vs 12–16 % chance; PASSer #1 alone gets 43.5 %, largest pocket 40 %. The two apparent successes are consistent with the favourite-pocket null (8 observed vs 11 expected) (§6c.3) |


### 6b.8 Protein-level correction, and `H_new` head-to-head

**Cells are not proteins.** §6b.3 counts cells; one protein (`ASB_1W25`) alone contributes 25 of the
54 consensus cells. Counted per **protein** (any of the 96 cells clearing AUC > 0.6 **and** P@5 ≥ 0.8):

| selector | tested | clear | rate | P@5 = 1.0 | clear **and** beat own null |
|---|---|---|---|---|---|
| fpocket only, hop 2 | 106 | 13 | 12.3 % | 1 | 9 |
| fpocket ∩ PASSer, hop 2 | 96 | 13 | 13.5 % | 3 | 7 |
| fpocket only, hop 1 | 107 | 7 | 6.5 % | 0 | 5 |
| fpocket ∩ PASSer, hop 1 | 99 | 12 | 12.1 % | 2 | 9 |

The two selectors tie at hop 2 and find **different** proteins (4 shared, 9 each unique). The consensus
advantage is **robustness to `MIN_HOP`**, not volume: fpocket-only halves when seeds adjacent to the active
site are excluded, consensus does not. Union over both hops: **15 proteins in 9 families**, of which
**10 clear at both hop settings**.

**`H_new` added as a 13th operator**, ported verbatim from cell 39 and verified against it
(max |Δ| = 0.000e+00 on the operator and on `V_B, V_T, V_R, V_C, V_M`; the sweep's parser had to be
extended to read B-factors). Consensus seeds, 13 × 8 = 104 cells/protein:

| paired on the same protein, best score each | H_new | exp/sym (its λ=0 base) | Δ | Wilcoxon p | wins |
|---|---|---|---|---|---|
| MIN_HOP = 2 (n = 101) | 0.659 | 0.622 | **+0.037** | 0.026 | 53/101 |
| MIN_HOP = 1 (n = 99) | 0.658 | 0.610 | **+0.049** | 0.0027 | 56/99 |

`H_new` is the **best single operator of 13** on best-cell AUC (0.537 vs 0.517 for `exp/sym`) and the
per-protein winner most often (19/101 at hop 2, 23/99 at hop 1). Its family-averaged AUC is still
**0.439** — best of a set that does not work on average. With `H_new` in the grid the strict-bar set
becomes **18 proteins / 10 families**; `H_new` is the winner in 6 and clears the bar in 7. Of the 12
non-`H_new` winners only 2 (`exp/sym`, `binary/sym`) are reachable by `H_new`'s dials; the other 10
use `adj`/`comb` normalisation or `gauss`/`harm` kernels that are structurally outside it.

### 6b.9 Are the winners a class? — no; they have bigger labelled pockets

18 features compared, winners vs rest, protein- and family-level (Mann–Whitney):

| feature | winners | rest | p (family level) |
|---|---|---|---|
| truth residues among seeds | **14** | **5.5** | **0.001** |
| base rate | **0.157** | **0.072** | **0.006** |
| n_residues / diameter / algebraic connectivity / clustering / degree / spectral radius / min_hop / min_euclid | — | — | all ≥ 0.07 |
| truth type, source dataset | — | — | 0.44, 0.37 |

**The only thing that separates winners is a ~2.5× larger annotated allosteric site.** No topology,
size, connectivity or distance feature does. The random-null P@5 tracks base rate at ρ = 0.99, so
"P@5 ≥ 0.8" largely selects proteins with big labelled pockets. After the per-protein permutation null,
**8 of 15 winners survive** (0.8 expected by chance) — real, but **7 of the 15 are the same protein**
(CAS0002, 7 PDB entries), so the defensible count is **6 distinct proteins of 138 (4 %)**.

**Pseudo-replication in the cohort itself:** CAS0002 is **28 of the 138** distal proteins (20 %);
72 of the 86 families have a single structure. Family-level aggregation is mandatory for every number
in this section.

**Winning Hamiltonian per significant protein** (identical at hop 1 and hop 2 for 12/13):
`ASB_1W25` binary/comb, `CB_6RXD` exp/adj, `ASB_2BXA` binary/adj, `CB_4DNC` binary/comb, `ASB_1W96`
gauss/comb — **all five with Green `|G|²` at (E = λmax, η = 0.05)**; `CAS_1DGK` exp/sym + residLOG.
Nine different operators win across 15 proteins; the **score** is far more consistent than the
Hamiltonian. `(E, η)` was one of three settings in the grid, so this is a hypothesis for a
confirmatory run, not a claim.

### 6b.10 Threshold ladder (consensus selector, both hops)

| bar | proteins | families |
|---|---|---|
| AUC > 0.6 anywhere | 101 | 61 |
| AUC > 0.8 anywhere | 38 | 32 |
| P@5 ≥ 0.6 anywhere | 52 | 27 |
| P@5 ≥ 0.8 anywhere | 19 | 9 |
| AUC > 0.6 **and** P@5 ≥ 0.8 | 15 | 9 |
| …and beats own permutation null | **9** | **7** |

"P@5 ≥ 0.6 anywhere in 104 cells" is reached by the **random null in 33 proteins**, and observed beats
null in 50/101 — exactly chance. Only the ≥ 0.8 bar separates from noise.

### 6b.11 Section-14 consensus block at scale — the operators agree, on the wrong pocket

The notebook's §14 CONSENSUS machinery, applied verbatim to all 101 consensus-seeded proteins
(`sec14_consensus.py` on `consensus13_hop2_ranks.json`): per score, each of the 13 operators ranks the
seed residues; a pocket's score is the **median rank of its residues**; each operator votes for its best
pocket; Kendall's W + Friedman p test whether the operators agree; TRUE drug pocket = `drug_frac > 0.5`.

| score | consensus elects a TRUE pocket | operators AGREE (W, p<0.05) | operator votes to TRUE |
|---|---|---|---|
| p_avg | 2 / 101 | 101 / 101 | 3.4 % |
| p_peak | 3 / 101 | 101 / 101 | 3.4 % |
| R | 6 / 101 | 35 / 101 | 7.8 % |
| residLOG | 4 / 101 | 101 / 101 | 5.3 % |
| residRAW | 4 / 101 | 101 / 101 | 4.5 % |
| green (0, 0.05) | 2 / 101 | 101 / 101 | 1.9 % |
| green (0, 0.01) | 2 / 101 | 101 / 101 | 3.0 % |
| green (λmax, 0.05) | 1 / 101 | 101 / 101 | 2.4 % |
| **chance** (random pocket) | **9.4 %** | — | — |
| **ceiling** (proteins with a TRUE pocket among seeds) | **61 / 101** | — | — |

**Every score elects the true pocket at or below the 9.4 % chance rate**, while the 13 Hamiltonians agree
with each other in **100 % of proteins** for 7 of the 8 scores (Kendall's W 0.4–0.9). That is the
failure mode §14's own comment warns about: *operator agreement within a score is agreement on that
score's shared bias, not on the answer.* Per protein, **91 of 101 have 0 of 8 scores electing the true
pocket**; 4 proteins are unanimous across all 8 scores and in **none** of the 4 is the unanimous pocket the
drug pocket. Only **`ASB_1W25` (6/8 scores) and `CB_6RXD` (5/8)** behave the way a single-protein §14
printout suggests every protein does.

**What gets elected instead** (464 wrong elections): the elected pocket is *smaller* (median 8 vs 15
seed residues; larger than the true pocket in only 16 % of cases), *less* druggable (fpocket rank 10 vs
8) and *less* allosteric (PASSer rank 11 vs 4). Under `p_avg`, operator votes anti-correlate with pocket
size (Spearman ρ = −0.29, p = 2e-17): **median-rank pocket scoring favours small pockets**, because a
few well-ranked residues dominate a short median. The consensus block therefore carries a
size bias that works *against* the (typically large) true pocket — a scoring artefact to fix before
any pocket-level consensus is quoted, and independent of which Hamiltonian is used.

**MIN_HOP = 1 (`consensus13_hop1_ranks.json`, 100 proteins):** the same picture — operators agree in
100 % of proteins for 7/8 scores, the consensus elects the true pocket in **0–5 %** per score (chance
9.4 %), **91/100** proteins have 0/8 scores electing it, the 2 unanimous proteins are unanimous on a
non-drug pocket, and `ASB_1W25` (5/8) is the only protein where most scores elect the drug pocket.

**Consequence.** The single-protein §14 view — a SCORE × HAMILTONIAN matrix with agreeing operators
electing one pocket — looks like evidence and is not: at scale it elects the true pocket less often than
a random draw. The ~6 proteins that genuinely work (§6b.9) are the ones where the residue-level ranking
is strong enough to survive the pocket aggregation.


---

---

## 6c. Pocket-seeded walk — the initial state is the whole pocket

§6b seeds the walk at **one residue at a time** and then has to aggregate residues back into pockets
(§6b.11 shows that aggregation is size-biased). This experiment removes the aggregation: for each
selected pocket P the initial state is the **uniform superposition over its residues**,

    |ψ₀⟩ = |P|^(−1/2) Σ_{i∈P} |i⟩ ,

the walk runs to the active site A, and every score is evaluated **once per pocket**, so the ~10 pockets
of a protein are ranked directly. Everything else is held fixed: same selection (fpocket ∩ PASSer,
minrank, Jaccard ≥ 0.5, top 10, active-site pocket removed), same `MIN_HOP` residue filter applied to
pocket members (pocket dropped if < 2 remain), same 13 Hamiltonians, same 8 scores.

| score | pocket-level definition |
|---|---|
| `p_avg` | Σ_k \|⟨k\|ψ₀⟩\|² Σ_{a∈A} \|v_k(a)\|²  — the T→∞ average of Σ_a \|⟨a\|e^{−iHt}\|ψ₀⟩\|² (non-degenerate approximation, same as §6b) |
| `p_peak`, `R` | max over 48 t ∈ [0, 1/gap] of Σ_a \|⟨a\|e^{−iHt}\|ψ₀⟩\|²; `R` = peak / average |
| Green ×3 | Σ_a \|⟨a\|(E + iη − H)^{−1}\|ψ₀⟩\|² at (0, 0.05), (0, 0.01), (λmax, 0.05) |
| `residLOG`, `residRAW` | `p_avg` regressed on [1, mean hop of members, log pocket size] **across the protein's pockets**, robust z-score of the residual |

Every score is computed twice: **coherent** (ψ₀ as above — the new physics, with interference between
pocket residues) and **incoherent** (the mean of the individual residue walks — i.e. what a mean-aggregation
of §6b would give). Comparing the two isolates whatever pocket-level coherence contributes.

**Truth and metric.** A pocket is the drug pocket if `drug_frac > 0.5` (§14's rule). The metric is the
**rank of the (best) true pocket** among the protein's pockets — top-1 = "the method put the drug pocket
first". The chance rate is exact per protein, k/n (true pockets / pockets), and is reported alongside.
Best-of-all-cells is compared to a label-permutation null on the same cells. The per-cell score vectors
are stored (`pocketwalk_hop{1,2}.json`) so any other pocket metric can be computed offline.
Scripts: `pocketwalk.py` (sweep), `pocketwalk_analyze.py`. Self-tests: closed-form coherent `p_avg`
matches the long-time numerical average (0.02750 vs 0.02731); incoherent `p_avg` equals the member
mean exactly; a planted-signal analysis test recovers 100 % top-1 for the planted mode and ~chance
(0.18 vs 0.20) for the null mode.

### 6c.1 Results — strict truth (`drug_frac > 0.5`)

**Coverage.** Under the strict rule only **57 / 138** proteins can be scored at all: in **67** proteins
no selected pocket has more than half its residues in the drug site (their most drug-like pocket has
median `drug_frac` 0.23), plus the usual 14 selector/fpocket losses. Median 8–9 pockets per protein,
1 true pocket → **chance top-1 rate 15–16 %**.

| MIN_HOP = 2, 57 proteins, 13 × 8 cells | top-1 rate (all cells) | top-3 rate | chance top-1 |
|---|---|---|---|
| **coherent** pocket superposition | **11.1 %** | 37.9 % | 15.9 % |
| **incoherent** (mean of residue walks) | 6.2 % | 26.6 % | 15.9 % |

| MIN_HOP = 1, 57 proteins | top-1 | top-3 | chance |
|---|---|---|---|
| coherent | 9.1 % | 27.8 % | 14.5 % |
| incoherent | 6.5 % | 20.7 % | 14.5 % |

**The pocket-seeded walk does not put the drug pocket first: its average top-1 rate is *below* the
chance rate at both hop settings.** Coherent seeding is consistently better than the incoherent
mean-of-residues baseline (+5 points top-1, +11 top-3) — pocket-level interference is doing *something*
— but not enough to reach a random draw. No cell exceeds 0.42 top-1 over proteins (best cell:
`binary/comb` + Green (0, 0.01), 0.42, and `gauss/comb` + Green (0, 0.01), 0.40 — the `comb` Green cells
are the only ones clearly above chance, and they are 2 of 104). Per protein, no protein has the true pocket
first in ≥ 75 % of cells; only **2 exceed chance by > 0.25 at both hops — `ASB_1W25` (0.54 / 0.41) and
`CB_6RXD` (0.42 / 0.42)** — the same two proteins that survive every other test in this report.
"Some cell puts the true pocket first" is true for 57/57 proteins and for 99 % of proteins under the
label-permutation null, i.e. it is meaningless with 208 cells and ~9 pockets.

### 6c.2 Results — relaxed truth (the pocket with the most drug residues, `drug_frac ≥ 0.25`)

Second run with the gate relaxed so that **every** protein with ≥ 3 pockets and ≥ 1 drug residue is scored
(99–100 / 138; the 26 proteins whose selected pockets contain *no* drug residue at all cannot be scored
under any rule). The truth rule is then applied offline. "argmax" = the single pocket with the most drug
residues, accepted if its `drug_frac` ≥ 0.25 — 83–85 proteins usable, vs 58–59 under the strict rule.

| rule | hop | usable proteins | chance top-1 | **coherent** top-1 / top-3 | incoherent top-1 / top-3 |
|---|---|---|---|---|---|
| strict (> 0.5) | 2 | 58 | 16.4 % | **11.2 %** / 38.4 % | 6.1 % / 26.5 % |
| strict (> 0.5) | 1 | 59 | 14.1 % | **9.0 %** / 26.8 % | 6.1 % / 19.5 % |
| argmax (≥ 0.25) | 2 | 85 | 13.0 % | **10.7 %** / 33.5 % | 5.6 % / 24.7 % |
| argmax (≥ 0.25) | 1 | 83 | 11.7 % | **8.4 %** / 25.4 % | 5.2 % / 18.9 % |

**Relaxing the truth rule changes nothing.** Under every rule and both hop settings the whole-pocket walk
ranks the drug pocket first *less* often than a random draw; coherent seeding stays ~5 points above the
incoherent baseline and ~3–5 points below chance. Per protein, exactly **two** exceed chance by more than
0.25 in all four runs — **`ASB_1W25`** (0.41–0.54 vs 0.11) and **`CB_6RXD`** (0.42 vs 0.11) — the same two
proteins that pass every other test in this report. Under the argmax rule `CB_1RXD` (0.25–0.31 vs 0.12)
is a weak third. The strict-run and relaxed-run numbers agree to within 0.3 points on the shared
proteins, so the two HPC runs reproduce each other.

### 6c.3 Reviewer pass — the two "successes" are consistent with chance

Three checks that should have preceded any claim about `ASB_1W25` and `CB_6RXD`:

**(i) Favourite-pocket null.** The walk concentrates its 104 coherent cells on one pocket per protein
(the favourite gets 41 % of cells on average, median 35 %). If that favourite were unrelated to the drug
pocket it would coincide with it in Σ 1/n_pockets proteins by luck:

| rule | proteins | favourite = drug pocket, observed | expected by chance | P(≤ observed) |
|---|---|---|---|---|
| argmax | 85 | **8** | 11.1 | 0.21 |
| strict | 58 | **4** | 7.8 | 0.10 |

Fewer proteins than chance have the drug pocket as the walk's favourite. `CB_6RXD` (0.46) and
`ASB_1W25` (0.44) sit **below the median favourite-share of proteins whose favourite is a non-drug pocket**
(0.34–0.38; 90th percentile 0.71–0.76). They are not outliers; they are the expected lucky draws.
**The earlier statement that "two proteins are real" is withdrawn.**

**(ii) Trivial baselines** (argmax rule, hop 2, 85 proteins; top-1 = drug pocket ranked first):

| ranker | top-1 |
|---|---|
| **PASSer #1 (most allosteric)** | **43.5 %** |
| **largest pocket** | **40.0 %** |
| fpocket #1 (most druggable) | 21.2 % |
| chance | 13.0 % |
| **CTQW, whole-pocket, coherent** | **10.7 %** |
| closest pocket to the active site | 0.0 % |

Two one-line heuristics beat the walk by 4×. `ASB_1W25`'s drug pocket is PASSer rank 1 — the detector
alone finds it. `CB_6RXD`'s is fpocket rank 14 / PASSer rank 10, so there the walk does find something the
detectors miss — a single case, consistent with (i). "Closest pocket" scores 0 % because the cohort is
distal by construction (§3.2).

**(iii) Integrity.** No ties at the top in either protein (0/104 cells). Strict-run and relaxed-run
shares agree exactly (`CB_6RXD` 0.46 / 0.46 / 0.46 across strict-hop2, relaxed-hop2, relaxed-hop1;
`ASB_1W25` 0.44 / 0.44 / 0.31). Truth enters `pocketwalk.py` only as labels and as the scoring gate
(which proteins are evaluated), never in pocket selection, `MIN_HOP` filtering, the initial state,
the operators, or the regression covariates — reviewed by reading, not by an ablation.

**What §6c settles.** Seeding from the whole pocket removes the §6b.11 aggregation defect and still ranks
the drug pocket first below chance, below the largest-pocket heuristic, and far below PASSer alone.
Coherent seeding beats the incoherent mean by a stable 3–5 points in all four runs — a measurable but
practically irrelevant effect. No protein can be held up as a demonstrated success of the pocket-seeded
walk; the §6b.9 list of "6 defensible proteins" (residue level, permutation null) stands only at the
residue level and does not translate into ranking the pocket. The one substantive lesson is that
**pocket appearance (PASSer, size) predicts the drug pocket far better than active-site coupling does on
this benchmark** — the §7b comment anticipated exactly this.

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
Three further `cx43` runs for §6b.8–6b.11 (H_new, pocket votes; one aborted half-provisioned run) added ≈ EUR 0.03. The §6c pocket-seeded runs (two `cx43` nodes, ~15 min each) added ≈ EUR 0.02. Cumulative HPC spend: **≈ EUR 0.26**.
