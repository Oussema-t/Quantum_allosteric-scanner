# Holo-direction module — actionable spec

**What this is.** An optional enhancement to the apo→transport pipeline: instead of
running CTQW/ENAQT only on the *static apo* graph, predict the direction of the
apo→holo conformational change from the apo structure, generate a small family of
admissible deformed graphs, and run transport on each. Goal is not to beat
structure prediction — it is to recover *statically hidden* active-site→pocket
edges and lift the hit rate above the apo-only floor, **per target, with every
claim falsifiable**.

**Where it slots.** Between PLAN.md Phase 1 (apo/holo superposition + mode
projection) and Phase 3 (LOPO). It reuses the Phase 1b mode machinery; it must
clear its own go/no-go gate (Step 2) before any quantum work.

---

## Prior art — you are NOT reinventing this (cite these)

| Component of the idea | Established method | Reference |
|---|---|---|
| Perturb a few sites, read whole-protein structural response | Linear Response Theory (LRT) | Ikeguchi, Ueno, Ota, Kidera, *PRL* 2005 |
| Scan perturbations site-by-site to map response | Perturbation Response Scanning (PRS) | Atilgan & Atilgan, *PLoS Comput Biol* 2009; General & Bahar applications |
| apo→holo change lives in a few lowest modes; measure by overlap | Mode/conformational-change overlap | Tama & Sanejouand, *Protein Eng* 2001 |
| Interpolate apo↔holo when both endpoints known | Two-state ANM | Das, Gur, Cheng, Jo, Bahar, Roux, *PLoS Comput Biol* 2014 — **challenge ref [15]** |
| Normal-mode-guided sampling to predict allosteric sites | CG-NMA conformational sampling | Zheng, *J Chem Phys* 2023 — **challenge ref [1]** |
| Predict cryptic-pocket *location* from one structure, no MD | PocketMiner (GNN) | Meller, Ward, Borowsky… Bowman, *Nat Commun* 2023 |
| Vibrations open blocked transport paths | ENAQT / dephasing-assisted transport | Plenio & Huelga, *NJP* 2008; Rebentrost, Mohseni, Lloyd, Aspuru-Guzik, *NJP* 2009 |
| Discrete conformational search as QUBO on a QPU | Quantum folding | Robert, Barkoutsos, Woerner, Tavernelli, *npj QI* 2021; Perdomo-Ortiz et al., *Sci Rep* 2012 (D-Wave) |
| Forward linear solve Δr = H⁻¹f, quantum form | HHL / QSVT inversion | Harrow, Hassidim, Lloyd, *PRL* 2009; Gilyén, Su, Low, Wiebe, STOC 2019 |
| Path waypoints need not be occupiable states | String method / NEB / transition-path theory | E, Ren, Vanden-Eijnden 2002; Jónsson, Mills, Jacobsen 1998 |
| apo-computable pocket-openness objective | fpocket (cavity detection) | Le Guilloux, Schmidtke, Tuffery, *BMC Bioinf* 2009 |

**Novelty to claim:** not the parts — the *composition* (predict the holo-direction
graph, then run a coherent/ENAQT walk on it, gated by an overlap test and scored
by headroom recovered). Claim the assembly, not the ingredients.

---

## The actionable build

### Step 0 — Freeze the protocol (do this before looking at any holo)
Pre-register, in code, the fixed perturbation protocol applied identically to every
protein incl. targets: site-selection rule, number of sites, mode set `k`, amplitude
range, and the **apo-computable** objective. Rationale: iterating the protocol until
the competence map looks good = leakage through protocol selection. (Same discipline
as ceiling-before-LOPO, one level up.)

### Step 1 — Build the admissible deformation family (the "stays intact" bound)
Quantify the constraint that the protein can't be ripped apart, which is what makes
the scan small:
- modes: lowest `k ≈ 5–20` ANM modes only (soft = least elastic + bond strain).
- amplitude ceiling: elastic energy `E = ½ Σ_k κ λ_k a_k² ≤ E_max`, with κ from
  B-factor calibration (Phase 1b).
- integrity: Cα–Cα neighbor spacing stays ≈3.8 Å; no steric clash; bounded global
  RMSD from apo.
- output: tens (not exponentially many) of candidate deformed graphs `G_1…G_m`.
Method basis: LRT (Ikeguchi 2005) for the linear response; two-state ANM (Das 2014)
when both endpoints exist; Tama–Sanejouand (2001) for the mode selection.

### Step 2 — GO/NO-GO gate: overlap-against-holo (the barrier-penetrability test)
For each training target with known holo:
- `Δr = holo_aligned − apo`; compute cumulative overlap
  `CO(m) = ||Σ_{k≤m} (Δr·û_k) û_k|| / ||Δr||` (Tama & Sanejouand 2001).
- separately: does any graph in `G_1…G_m` actually create the specific edges linking
  the active site to the cryptic pocket?
**Decision:** high CO + right edges appear → the holo direction is inside the
admissible manifold (barrier penetrable in a reachable direction) → proceed for that
target. Low CO → you'd propagate on a fictional graph; **stop for that target** and
record it. KRAS Switch-II is the expected NO case (local/anharmonic opening). The
NO result is publishable: "cryptic pocket unreachable by the thermal ensemble of the
apo state" beats "walk scored at chance."

### Step 3 — Optimize the perturbation (classical first; quantum optional)
Find the admissible deformation maximizing an **apo-only** objective:
- objective = cavity-openness (fpocket, Le Guilloux 2009) and/or thermal
  accessibility / soft-mode participation. **Never** "match holo B-factors/exposure"
  — that is holo-derived = leakage.
- classical optimizer: basin-hopping or CMA-ES in low-dim mode-amplitude space
  (cheap precisely because of your coarse-graining).
- quantum-native option (second demo, not the result): discretize mode amplitudes →
  QUBO → QAOA / annealing (Robert 2021; Perdomo-Ortiz 2012). Forward solve Δr=H⁻¹f
  is a linear solve; do NOT dress it as quantum (HHL/QSVT pointless at N~hundreds).

### Step 4 — Transport on the predicted graph(s)
Run the existing CTQW / ENAQT-QSW (propagators.py) on each admissible graph; the
active-site→pocket signal now flows on the deformed connectivity. ENAQT rationale:
coherent walks localize on disordered graphs; calibrated dephasing reopens blocked
paths (Plenio–Huelga 2008; Rebentrost 2009). Calibrate γ from vibrational timescales
(B-factor→κ→mode relaxation), not a blind sweep.

### Step 5 — Score with two leakage-clean headline metrics
1. **Consensus across perturbations** (primary, holo-free): is the predicted pocket
   the same region across `G_1…G_m`? Stable region = real resolving power; smear
   across the surface = none. Computable with no holo at all.
2. **Headroom recovered** (accuracy claim, per target):
   `(method − floor) / (ceiling − floor)`, where floor = best honest apo-only run
   (beats random + surface + degree baselines) and ceiling = supervised in-sample
   max. Report "we close X% of the gap that knowing the answer would close." This
   normalizes per-protein difficulty and makes failures legible instead of averaged
   into a vague win. **Do not** budget additive +20/+40/+20 — expect a lift on the
   modes-aligned subset and ~0 on the cryptic ones; let Step 2 say which is which.

---

## Leakage firewall (the project's central risk, new disguise)
- objective in Step 3 is apo-computable ONLY (ENM energy, cavity openness, apo
  B-factor flexibility). Referencing holo signatures = back-door leakage.
- Step 0 protocol frozen before the competence map is viewed.
- using holo to **characterize the method** (success/failure histogram) is legal;
  using holo to **parameterize the predictor** (any per-target knob) is not.

## NISQ demo (where the points actually are)
The challenge scores noise resilience, not speed. Trotterize `e^{-iHt}` on a
coarse-grained `N ≤ ~12–16` qubit graph; run under a depolarizing + amplitude-damping
model with realistic 2-qubit error rates; report top-5 ranking degradation vs circuit
depth and error rate. **Key result to look for:** is the ENAQT/QSW variant *more*
noise-robust than coherent CTQW? If device dephasing sits near the ENAQT-helpful
regime, hardware noise is a feature — a clean NISQ story needing no advantage claim.
Connects to the challenge's SVD/quantum-biology ref [11] (Oh, Krogmeier, Schlimgen,
Head-Marsden, *ACS Phys Chem Au* 2024) via QSVT application of f(H).

## Scope
- **In:** mode-bounded deformation scan; LRT/PRS direction; overlap gate; apo-only
  openness objective; solvent-like perturbation (uniform/surface pressure term — the
  "direction not detail" justification holds here).
- **Out / drop from the accuracy ladder:** atomistic force fields (re-introduces the
  MD the rules forbid; breaks topology-only) and mutations (a scope change / target
  change, not a refinement — keep for MYC/p53 learning base only).

## First action
Run Step 2 on all training targets *before* building Steps 3–5 or any circuit. The
cumulative-overlap number per protein tells you which targets have a penetrable
barrier in a reachable direction — i.e., where this module can possibly help — and
which are walls. Build the rest only for the targets that clear it.
