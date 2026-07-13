# REVIEW 2026-07-13(c) — CTQW trapping as the mechanism behind the proximity confound

**Scope**: `propagators.{time_averaged_ctqw, ctqw, haken_strobl}`, `hamiltonians.build_H_new`
and its diagonal potentials (V_B/V_T/V_R/V_C/V_M), the P1-A proximity confound
(`REVIEW-2026-07-13`) and the well-vs-coupling confound (`REVIEW-2026-07-13b`).
**Method**: executed against this repo's own `propagators.py`/`hamiltonians.py` on a
synthetic compact globule (network access unavailable when this was run — no PDB fetch,
not a re-run of the real mandatory targets). Treat as a mechanism test, pending real-data
confirmation (TASK-0106).
**Origin**: verifies a colleague's hypothesis ("CTQW is becoming trapped, rather than just
measuring nearest proximity") against the real code, precisified first since "trapped" and
"measuring proximity" are not rival explanations at the same level — proximity describes
the *output*, trapping is a *mechanism* that produces it.

---

## 0. Verdict

**Partly confirmed, and the confirmed part matters more than the informal framing suggests
— but "trapping *instead of* proximity" is the wrong framing.** Trapping and proximity are
not rival hypotheses: a trapped walk's occupation *is* a distance-decaying map. What's
testable is whether the trapping is real, what causes it, and whether it's what kills
distal detection. All three: yes.

## 1. The walk is genuinely trapped, and `H_new`'s potentials cause it

Coherent CTQW, same graph, propagated to t=50:

| Operator | PR/N @ t=50 | ⟨hop from seed⟩ @ t=50 |
|---|---|---|
| clean `L_norm` (all λ=0) | 0.414 | 2.49 |
| `H_new` (default λ) | **0.024** | **0.73** |

On the bare normalized Laplacian the walk spreads across the protein. With
V_B+V_T+V_R+V_C+V_M turned on, it never leaves the seed's first contact shell, at any time
out to t=50. Transport is arrested, not slow — textbook disorder-induced (Anderson-like)
localization, caused by the diagonal potentials `H_new` was built with.

Disorder sweep, H(λ) = L_norm + λ·(V_B+V_T+V_R+V_C+V_M):

| λ | mean eigenvector PR/N | occupation PR/N | ρ(occ, −hop) | decay length (hops) |
|---|---|---|---|---|
| 0.00 | 0.217 | 0.187 | 0.820 | 0.83 |
| 0.25 | 0.075 | 0.121 | 0.862 | 0.58 |
| 1.00 (default) | 0.022 | 0.065 | 0.890 | **0.27** |
| 4.00 | 0.009 | 0.047 | 0.900 | 0.15 |

Eigenvector localization increases ~10x with the potentials; occupation decay length falls
to 0.27 hops — sub-nearest-neighbour.

## 2. The proximity correlation is not *created* by the trapping

At **λ=0 — zero disorder, zero potentials — ρ(occ, −hop) is already 0.82.** The distance
signature is intrinsic to a time-averaged walk on a compact contact graph; disorder pushes
it from 0.82 → 0.90, it doesn't manufacture it from nothing.

Contrast: a classical random walk's stationary distribution (π ∝ degree) has
ρ(π, −euclid) = **−0.07** on the same graph — a genuinely-transporting process forgets its
source. This operator's score remembers the seed because it never transported.

**Correct statement:** it is proximity, and trapping is *why* it's proximity — not
"trapping instead of proximity."

## 3. Dephasing does not rescue it

Haken–Strobl on `H_new`, γ: 0→5. Occupation partially delocalizes (PR/N 0.029→0.09), but
ρ(occ, −euclid) goes **up**, 0.787→0.919 — the dephased walk becomes a *purer* distance
map, converging on a diffusive front. Consistent with this repo's own flat-dephasing
finding (TASK-0091/RESULTS.md). **Caution for [[TASK-0105]]** (the real-target ENAQT
γ-sweep): if it sweeps `H_new` specifically, an absent interior optimum may reflect this
operator's trapping, not an absence of the ENAQT effect in general — the sweep should not
be limited to `H_new` alone (see §5).

## 4. The consequential test: does un-trapping restore distal detection?

Distal pocket (12 residues, 27.9 Å / 5.1 hops from seed — the BCR_ABL1 geometry), scored
via `time_averaged_ctqw`:

| Operator | ⟨hop⟩ @ t=50 | AUC on distal pocket |
|---|---|---|
| pure −euclid baseline | — | 0.000 |
| `H_new` (default) | 0.73 | 0.122 |
| `H_new`, λ=0.25 | 2.18 | 0.132 |
| `H10_disorder_suppressed` | 2.45 | **0.582** |
| `H2_combinatorial_laplacian` | 2.39 | **0.592** |

Transport-preserving operators score **above chance on a pocket where the proximity
baseline scores exactly zero.** `H_new` — the current submission operator — scores 0.12,
*anti*-correlated with the true pocket.

**Real-data corroboration already in `RESULTS.md`**: on BCR_ABL1, `AUC_apo_H10_baseline` =
0.558 vs `H_new` = 0.525. Previously read as a −0.033 noise-level gap
([[TASK-0093]]/`RESULTS.md`). This mechanism predicts that sign, which changes how that gap
should be read — not necessarily noise.

## 5. What this changes

- **`H_new` may be the wrong submission operator for the challenge's actual goal** — it was
  selected (originally under conditions with label leakage, since corrected) for potentials
  that arrest transport, on a challenge premised on long-range communication. This is a
  clean, honest, and genuinely important finding *if it reproduces on real data* — it is
  not yet a basis for reselecting the submission operator (that decision is explicitly
  Tier-2-gated, [[TASK-0100]], via `frozen_context`/`leave_one_protein_out` across all 3
  mandatory targets — an ungated swap on this evidence alone would be exactly the N=3
  multiple-comparisons risk TASK-0100 already flagged).
- **[[TASK-0105]] (ENAQT γ-sweep)** should not run `H_new` only — a trapped operator's flat
  dephasing response could be mistaken for "no ENAQT effect" when it's actually "no
  transport to dephase in the first place." Sweep across at least `H_new`, `H10`, `H2`.
- **[[TASK-0101]] (operator-sweep harness)** should report a transport diagnostic
  (⟨hop⟩ or participation ratio at fixed t) alongside AUC/floor-clearance for every
  operator — "operators that transport find distal pockets; operators that trap find
  geometry" is a result, not just a leaderboard row.
- **[[TASK-0093]]** (KRAS AUC discrepancy) and the BCR_ABL1 H10-vs-H_new gap in `RESULTS.md`
  should be re-read in light of this mechanism before either is written off as noise.

## Caveats (stated plainly)

Synthetic globule, one geometry, one seed, one pocket placement. No network access to
verify on real 4OBE/1OPL at review time. The λ=0→1 trapping effect is large and
unambiguous; the H2/H10 ≈ 0.59 distal AUC is suggestive and may be geometry-specific.
**Do not report this in RESULTS.md or the submission until it reproduces on real targets —
[[TASK-0106]] is that reproduction, and is the gate before any claim changes.**
