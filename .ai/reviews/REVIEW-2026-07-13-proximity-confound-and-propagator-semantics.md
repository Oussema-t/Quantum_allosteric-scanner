# REVIEW 2026-07-13 — Proximity confound, propagator semantics, phantom operators

**Scope**: `src/allostery/{baselines,hamiltonians,propagators,analysis,diagnostics}.py`,
`RESULTS.md` Run 2026-07-12, open TASK-0091/0092/0093.
**Method**: every claim below was **executed against this repo's own code** on a synthetic
170-residue globule, using the real `build_H_new`, `time_averaged_ctqw`, `heat`,
`H6/H11/H12`, and `contact_matrix`. Nothing here is inferred from reading alone.
**Origin**: raised by an external reviewer; independently verified, and one of their
conclusions is **corrected** below (§Non-findings).

Status tags follow `RESULTS.md` convention.

---

## P1-A — [OBSERVED] The headline AUCs are confounded by distance from the seed

**Observation.** The propagator is seeded at the functional/active-site set (`source=`,
`analysis.py:77,165`). The label is "residues within 4.5 Å of the allosteric ligand,
minus the active site." Nothing in the pipeline controls for the score being, to first
order, a **distance-to-active-site map**.

**Evidence** (real code, synthetic globule, cutoff 8.0 Å, seed = 6-residue cluster):

| Measurement | Value |
|---|---|
| Spearman(`time_averaged_ctqw` occupation, −Euclidean distance from seed) | **+0.853** |
| Spearman(CTQW occupation, −hop distance from seed) | **+0.880** |
| AUC, pocket placed **adjacent** to seed — CTQW | 0.914 |
| AUC, same pocket — **pure distance baseline** | **0.966** ← beats the walk |
| AUC, pocket placed **distal** from seed — CTQW | **0.035** ← anti-correlated |
| AUC, distal pocket — pure distance baseline | 0.000 |

**Impact.** `classify_failure`'s only floor is `degree_centrality`, which is **not** the
confounding variable. `baselines.py` currently exposes `random_baseline`,
`surface_baseline` (= −degree), `degree_centrality`, `betweenness_centrality`,
`fpocket_baseline` — **there is no proximity/distance baseline at all**. A score can
therefore clear every floor we have while being pure geometry.

This is a sufficient (not yet confirmed) explanation for the cross-target pattern in
`RESULTS.md`:

| Target | Pocket vs. active site | AUC |
|---|---|---|
| KRAS_G12C | SII-P, **adjacent** to nucleotide site | 0.779 |
| CARDIAC_MYOSIN | near ADP/converter | 0.786 |
| BCR_ABL1 | myristoyl, **~25 Å distal** | 0.525 |

The one target with a genuinely distal pocket is the one target at chance. That is the
signature of a proximity detector, not an allostery detector — and it is the worst
possible failure mode for this challenge, whose entire premise is *distal* regulatory
sites.

**[OBSERVED]** Related: the reported top-5 KRAS hits (34, 35, 36, 11, 59) are Switch-I /
P-loop residues — the shell **ringing the nucleotide site** — and contain **none** of the
canonical AMG510 SII-P residues (68, 69, 72, 95, 96, 99, 100). The "3 of 5 in
`pocket_full`" cross-check in `RESULTS.md` passes because `pocket_full` includes the
nucleotide-proximal shell, **not** because the switch-II pocket was found. The
cross-check as written does not discriminate the hypothesis it appears to support.

**Remediation → TASK-0094.** Add `euclid_from_seed_centroid` and `hop_from_seed` (both
negated, so "closer = higher score") to `baselines.py`; include them in `floor_scores`
and in `classify_failure`'s floor. Re-run all three mandatory targets.

**Acceptance criterion (hard).** A target's AUC may only be reported as signal if it
**clears the proximity floor**, not merely chance and degree. If KRAS's 0.779 does not
clear it, the number is geometry and must be reported as such. *A well-evidenced "our
method is a proximity detector" is a legitimate, publishable result under `PLAN.md`'s
own gates-before-build framing — silently shipping 0.779 as allosteric signal is not.*

---

## P1-B — [OBSERVED] `propagators.heat` on `H_new` is not classical diffusion

**Observation.** `heat()`'s own docstring states *"H should be a positive-semidefinite
Laplacian"* (`propagators.py:85`). `H_new` is **indefinite by design** — `V_R`/`V_C`/`V_M`
contribute negative diagonals (already noted in T-012). Feeding an indefinite operator to
`exp(−Ht)` is imaginary-time Schrödinger evolution, not a diffusion semigroup.

**Evidence** (real `build_H_new`):

| Measurement | Value |
|---|---|
| `H_new` spectrum | min **−1.833**, max 10.155 → **indefinite** |
| ‖exp(−H·20)·p₀‖₁ **before** the internal clip/renormalise | **1.75 × 10¹³** (conservative diffusion = 1.0) |
| Spearman(`heat(H_new, t=20)`, \|ground state\|²) | **0.998** |

`heat(H_new)` is returning the **ground-state density of `H_new`**. The clip-and-normalise
step masks a 13-order-of-magnitude divergence.

**Impact — two, both serious.**

1. **`RESULTS.md`'s BCR_ABL1 headline is mis-framed.** "Classical heat 0.731 vs CTQW
   0.525" is **not** a classical-vs-quantum comparison. It is: *the ground state of
   `H_new` localizes differently than the time-averaged walk*. Every place this appears
   (`RESULTS.md`, `report.txt`, the methodological report) currently makes a false
   physical claim.
2. **TASK-0091 rests on a false premise — do not run it as framed.** The Haken–Strobl
   γ→∞ limit is a classical random walk with rates ∝ |H_ij|²/γ, generated by the
   **off-diagonals**. `heat(H_new)` is dominated by the **diagonals**. The dephasing sweep
   is structurally incapable of converging to `heat(H_new)`, so it cannot "recover" 0.731
   — and if AUC happens to rise, attributing it to ENAQT would be an unsupported causal
   claim.

**Remediation → TASK-0095.** (a) Rename `heat` → `ground_state_relaxation` (or equivalent)
so the name stops asserting physics the code does not do. (b) Add a guard: raise (or emit a
loud diagnostic) if `min(eigvalsh(H)) < -tol`, so an indefinite operator can never be
silently treated as a diffusion generator. (c) Correct every downstream framing.

---

## P2-A — [OBSERVED] Two operators in the sweep are phantoms (duplicates of others)

**Evidence** (`np.allclose` on real code, cutoff 8.0 Å):

- `H11_anisotropic_mechanical` — body is `contact_matrix(weight="exponential")` +
  `laplacian` (`hamiltonians.py:161-166`). **Identical to `H6_exponential_decay`
  → verified `True`.** Its docstring claims *"weight edges by dot-product of unit
  displacement."* It does not.
- `H12_anm_scalarised` — computes `k_ij = np.dot(r, r)` where `r` is a **unit** vector;
  the code's own comment reads `# = 1.0 for unit vector` (`hamiltonians.py:180`). Every
  edge weight is therefore 1.0. **Identical to the unweighted-contact Laplacian
  → verified `True`.** There is no anisotropy in it.

**Impact.** Both remain in the operator sweep and in `ALGORITHM_REGISTER`, inflating the
apparent breadth of the baseline comparison. A judge (or a reviewer) who reads the
docstrings and then the bodies will find a claimed-but-absent capability. TASK-0037 records
that these are "not implemented" — that is **not sufficient while they are still running
and being reported**.

**Remediation → TASK-0096.** Either implement the documented anisotropy or **delete both**
and remove them from the sweep and the register. Do not ship a sweep containing two
operators that are secret duplicates of H6 and H1/H2.

---

## P2-B — [OBSERVED] The "quantum metric" is a decoherent spectral quantity

`time_averaged_ctqw` returns Σₖ |v_k(j)|² |v_k(s)|² — the infinite-time-average /
decoherent limit. **All phase information is averaged out by construction.** This is fully
consistent with the repo's existing flat-dephasing-sweep finding, and is a legitimate
choice — but it means the challenge deliverable's "quantum metric" is a **spectral overlap
quantity**, not a coherent quantum walk.

**Remediation → TASK-0097.** State this plainly in the methodological report and in
`RESULTS.md`. Better that we name it than that a judge discovers it. (This is
`ALGORITHM_REGISTER`'s honest-capability posture applied to the headline metric.)

---

## Non-findings — what this review does **not** conclude

The external reviewer proposed that the heat/ground-state result is *"immune to the
proximity confound"* and *"the most interesting real result in the repo."* **That is a
hypothesis, and it does not survive the test they did not run.** Measured on the same
synthetic system:

- Spearman(`heat` occupation, −Euclidean distance from seed) = **+0.589** — weaker than
  CTQW's 0.853, but **not immune**.
- AUC on a **distal** pocket: `heat` = **0.048** — just as anti-correlated as CTQW (0.035).

**[HYPOTHESIS — untested]** Ground-state localization *may* still detect distal pockets on
real protein topologies (BCR_ABL1's 0.731 is real and unexplained). But it is **not**
demonstrated to escape the proximity confound, and must not be promoted to a finding
before it is measured. Do not repeat the error this review is about.

---

## Retraction of prior guidance

Earlier advice to prioritise TASK-0091 as "the ENAQT story with real evidence" is
**withdrawn** — see P1-B. The dephasing sweep cannot bridge CTQW→heat and would have
produced a plausible, confidently-wrong causal claim. TASK-0091 must be re-filed (below)
before any cycle is spent on it.

---

## Task proposals

- **TASK-0094 — Proximity baselines into the floor.** Add `euclid_from_seed_centroid` and
  `hop_from_seed` to `baselines.py`, wire into `floor_scores` and `classify_failure`; re-run
  all mandatory targets. *Hard acceptance: no AUC is reported as signal unless it clears the
  proximity floor.* **Blocks every current headline number. Do this first.**
- **TASK-0095 — Correct propagator semantics.** Rename `heat` → `ground_state_relaxation`;
  guard against indefinite `H` in any diffusion-semantics path; correct all downstream
  framing in `RESULTS.md` / `report.txt` / methodological report.
- **TASK-0096 — Delete or implement H11/H12.** Remove the phantom operators from the sweep
  and `ALGORITHM_REGISTER`, or implement the anisotropy their docstrings claim.
- **TASK-0097 — Name the metric honestly.** Document that `time_averaged_ctqw` is the
  decoherent limit (a spectral overlap quantity), in the report and the register.
- **TASK-0091 (RE-FILE) — Does the `H_new` ground state localize on *distal* pockets?**
  Replace the dephasing-sweep framing (false premise). Test directly against BCR_ABL1's
  0.731 **with the proximity floor from TASK-0094 applied**. This is the one open line of
  inquiry that is not proximity in disguise.
- **TASK-0093 (UPDATE) — KRAS reconciliation now has a candidate mechanism.** The 8.0 vs
  10.0 Å cutoff changes the contact graph, which changes the distance-decay of the walk.
  Test the cutoff delta **against the proximity baseline**, not just against chance.
- **TASK-0098 (NEW, protocol) — Amend `INVARIANCE_PROTOCOL`'s SIGNAL class.** The null
  control currently asks *"does it beat random?"*. It must ask *"does it beat the obvious
  domain heuristic?"* — here, distance-from-seed. A floor that is weaker than the trivial
  confounder is not a floor.

---

## Sequencing

1. **TASK-0094** (proximity floor) — one day, and it **decides whether we have a result**.
2. **TASK-0095** (propagator semantics) — cheap, and it stops a false physical claim from
   propagating into the submission.
3. **TASK-0096** (phantom operators) — cheap, removes an audit liability.
4. Then **TASK-0091 (re-filed)** and **TASK-0093** — the real scientific questions, now
   asked against a floor that can actually falsify them.
5. **TASK-0097 / TASK-0098** — reporting honesty and protocol hardening, can run in parallel.

Delivery (0083–0086) and graduation (0076–0078) remain correct but stay subordinate: there
is no point shipping a pipeline whose headline number has not yet cleared its true floor.

---

## Meta — the pattern, for the register

This is the third instance of the same failure mode in this project:

| Domain | Assumed-gauge symmetry that was never executed |
|---|---|
| ENM mode selection | SE(3) rotation → found index-slicing over a degenerate null space |
| Quantum-channel object | SU(2) conjugation → found a Clifford-only, fixed-frame artifact |
| **This** | **Translation away from the seed** → score is largely distance |

**The discriminating test is the assumed-gauge symmetry no one executed.** The leakage
firewall guards against *knowing the answer*; nothing guarded against the score being
*trivially predictable from geometry*. Both are leaks — one through labels, one through
coordinates.

**Credit where due:** the external reviewer found this quickly **because** `RESULTS.md`'s
`[OBSERVED]` / `[HYPOTHESIS]` tagging made the claims falsifiable. The honesty discipline
worked exactly as designed. It was simply pointed at the wrong variable.
