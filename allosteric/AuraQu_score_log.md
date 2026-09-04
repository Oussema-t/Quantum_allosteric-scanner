# AuraQu — CTQW §14 Score Log

Manually recorded reference runs of `Quantum_Allosteric_Scanner_v2.ipynb`, §14
(PennyLane qubit CTQW, multi-Hamiltonian walk, seeded from fpocket pockets).

**Why this file exists:** Jupyter keeps no per-run history, and VS Code local
history prunes within a few days — the KRAS `H3_normL 0.828/1.0` run was lost
this way. Record every notable run HERE, with the **full parameter set** and an
**honest caveat**, so it can be reproduced and is never mistaken for a clean win.

Scoring: vs the holo drug pocket (DRUG_POCKET firewalled). AUC + P@5 by `p_avg`
(long-time transfer to the active set). `base` = fraction of seeds already in the
drug pocket (a high base makes P@5 easy and AUC less meaningful).

---

## KRAS_G12C — best operator H3_normL
*Recorded 2026-08-05 from screenshot; original live run between Aug 1–5 (not saved to disk).*

| param | value |
|---|---|
| operator (best) | **H3_normL (conn)** |
| N_SEED_POCKETS | **5**  (gives 37 distal seeds; the current `10` gives 61 → different board) |
| MIN_HOP | **1** (uses all seeds incl. 1-hop) |
| SITE_CUTOFF / NET_CUTOFF | 4.5 / 10 |
| C_T | 5.0 |
| qubits / seeds / base | 8-qubit / 37 distal seeds / **base 0.22** |

**Scores (p_avg):**
| operator | AUC | P@5 |
|---|---|---|
| **H3_normL** | **0.828** | **1.0** ← best |
| H_new (submission) | 0.797 | 0.8 |
| H2_combL | 0.685 | 0.4 |
| H6_exp | 0.470 | 0.4 |

**⚠️ CAVEAT — proximity-inflated.** P@5=1.0 is at `MIN_HOP=1`, which keeps seeds
adjacent to the active site. The run's own MIN_HOP sweep (operator H_new):

| hop≥ | seeds | AUC | P@5 |
|---|---|---|---|
| 1 (incl 1-hop) | 37 | 0.797 | 0.8 |
| 2 | 28 | 0.731 | **0.2** |
| 3 | 12 | 0.636 | **0.2** |

→ the signal **collapses** once near-active seeds are excluded. Report as
*MIN_HOP=1, proximity-confounded*, not as a headline result.

**Reproduce:** cell 1 `SITE_CUTOFF=4.5, NET_CUTOFF=10`; §14 `N_SEED_POCKETS=5, MIN_HOP=1`;
`RUN_ONLY=["KRAS_G12C"]`; run §14.

---

## BCR_ABL1 — best operator H2_combL
*Recorded 2026-08-05 from screenshot (live run, not saved to disk).*

| param | value |
|---|---|
| operator (best) | **H2_combL (conn)** |
| N_SEED_POCKETS | not captured (run gave 28 seeds at hop≥1 / 23 at hop≥2) |
| MIN_HOP | **2** (the sweep marks hop≥2 = 23 seeds as "current") |
| qubits / seeds / base | 9-qubit / 23 distal seeds / **base 0.78** |

**Scores (p_avg):**
| operator | AUC | P@5 |
|---|---|---|
| **H2_combL** | **0.767** | **1.0** ← best |
| H6_exp | 0.711 | 1.0 |
| H_new (submission) | 0.656 | 1.0 |
| H3_normL | 0.144 | 0.2 |

**⚠️ CAVEAT — high base rate (near-trivial P@5).** `base = 0.78`: **18 of 23
seeds already lie inside the drug pocket**. This is the known BCR-ABL1 issue —
apo `1OPL` already has the myristoyl ligand (MYR) bound, so the pocket is **not
cryptic** and the seed set overlaps it massively. P@5=1.0 is almost guaranteed and
AUC is measured against a 78% base. MIN_HOP sweep (H_new):

| hop≥ | seeds | n_drug | AUC | P@5 | base |
|---|---|---|---|---|---|
| 1 | 28 | 18 | 0.528 | 0.6 | 0.64 |
| 2 | 23 | 18 | 0.656 | 1.0 | 0.78 |
| 3 | 14 | 13 | 0.538 | 1.0 | 0.93 |

→ AUC hovers near chance (0.5–0.66) while P@5 stays 1.0 purely because almost
every seed is in-pocket. **Not a clean win** — a high-base artifact. Use BCR-ABL1
as the *cautionary* target (per the science skill: 1OPL is not the cryptic case).

**Reproduce:** §14 `MIN_HOP=2`, `RUN_ONLY=["BCR_ABL1"]`; match seed count to the
recorded 23/hop≥2.

---

## Template for new runs
```
## <TARGET> — best operator <OP>
Recorded <date>. Params: N_SEED_POCKETS=?, MIN_HOP=?, SITE_CUTOFF=?, NET_CUTOFF=?, C_T=?, <q>-qubit, <n> seeds, base <b>.
Scores (p_avg): <OP> AUC=? P@5=?  | H_new AUC=? P@5=?  | ...
CAVEAT: <proximity? high base? cutoff sensitivity?>
Reproduce: RUN_ONLY=["<TARGET>"], <the exact param set>.
```

---

## KRAS_G12C — C_T convergence sweep (settles the `C_T=5.0` override)
*Run 2026-09-03, cell 14z. Operator H_new, 51 seeds, 8 in drug pocket, MIN_HOP/seed set as in §14 that run.*

**Why:** the score log records KRAS at `C_T=5.0` while every other target ran at `1.0` — which
looks like per-target tuning. Note the obvious test is NOT valid: in the current code `p_avg`
is the closed-form infinite-time average (`sq = V*V; M = sq @ sq.T`), so sweeping `C_T`
against it is an algebraic identity, not a convergence check. This sweeps the **finite-T**
average — the quantity the original `C_T=5.0` run actually computed, before the closed form
existed — and compares it to the closed form.

| C_T | T_max | n_t | AUC p_avg (finite-T) | AUC p_peak | AUC R | max abs(finite − closed) |
|---|---|---|---|---|---|---|
| 0.5 | 4872 | 300 | 0.7558 | 0.7645 | 0.5640 | 4.2e-03 |
| 1.0 | 9745 | 300 | 0.7587 | 0.7674 | 0.5174 | 1.8e-03 |
| 2.0 | 19490 | 300 | 0.7616 | 0.7820 | 0.4942 | 1.5e-03 |
| 3.0 | 29235 | 300 | 0.7616 | 0.7703 | 0.6831 | 7.5e-03 |
| 5.0 | 48726 | 300 | 0.7616 | 0.7500 | 0.5145 | 3.3e-03 |
| 8.0 | 77961 | 300 | 0.7616 | 0.7762 | 0.6308 | 3.9e-03 |
| 10.0 | 97451 | 300 | 0.7645 | 0.7471 | 0.5727 | 3.2e-03 |

Closed-form `p_avg` (T→∞, no time grid): **AUC 0.7616** — the value §14 reports.

**TOP-5 STABILITY (the sharper test — P@5 is what this log records, not AUC):** the closed-form
top-5 seeds are `[71, 75, 110, 61, 68]`, P@5 = 0.6. **Every C_T in the sweep reproduces that
list in the identical ORDER** — 1 distinct ordered top-5, 1 distinct set, P@5 = 0.6 at all seven
values. The hit list is genuinely time-independent.

**Not a contradiction with the 0.828/P@5 1.0 entry above:** that run was `H3_normL`,
`N_SEED_POCKETS=5, MIN_HOP=1`, 37 seeds; this one is `H_new`, 51 seeds, current consensus
seeding. Different configuration, not a different C_T. The seed set is the lever here — the
axis TASK-0118 on the `bartosz` branch classifies as a KNOB with a measured 0.326 AUC swing on
this same target — while C_T is not.

**VERDICT — the `C_T=5.0` override was HARMLESS.** Finite-T `p_avg` AUC spread across the whole
sweep is **0.0087**; `C_T=1 → 0.7587` vs `C_T=5 → 0.7616`, difference **+0.0029**. The finite-T
average tracks the closed form to <8e-03 everywhere. So the override did not create the KRAS
result, and everything can be reported at a single `C_T=1` with the per-target override dropped.

**But `p_peak` and `R` DO move** (p_peak 0.7471–0.7820; R 0.4942–0.6831, a 0.19 swing). They are
maxima over the sampled window, so any claim built on them must state its `C_T`. `p_avg` and the
residual scores built on it cannot move — no time enters them. State that as a rigour property.

**CAVEAT:** this is one target, one operator (H_new). It does not license `C_T`-independence for
other targets or for the time-dependent scores.
