# PLAN — allostery pipeline

Plan of action, repo structure, and feature backlog for the Cleveland Clinic
Quantum + AI challenge submission.

## Guiding principle: gates before build

Every phase below is a **validity or feasibility gate**. A gate that fails is a
*result*, not a setback — it saves the downstream effort and often yields a more
honest, more publishable finding than a forced positive. Order is deliberate:
prove the operators are correct, prove the data is clean, prove the answer is
physically present in the apo structure, and bound the best achievable result
*with* the labels — before building the blind machinery.

Two findings already visible in the H_new notebook suggest some gates may fail,
which is exactly why they go first:
- optimized AUC_apo on KRAS ≈ 0.53 (near chance even with the answer key);
- Haken–Strobl AUC is flat in the dephasing parameter (coherence adds ~nothing).

If those hold up under the gates, the headline result is "topology-only / CTQW
cannot recover cryptic allosteric pockets from apo, and here is the rigorous
evidence" — a legitimate primary result.

---

## Phase 0 — Substrate validity: physics tests + data cleaning

These run together because both ask "is the substrate correct."

### 0a. Physics unit tests (analytical, small graphs)
Hamiltonian "quantumness" splits into two questions; test both.

* **Mechanical correctness** (is the coherent evolution right?):
  * line / large cycle, adjacency H: `|<x|e^{-iAt}|0>|^2 == J_x(2t)^2` (Bessel).
  * dimer (N=2): coherent occupation == Rabi `cos^2 / sin^2`.
  * cycle C_n: eigenvalues == `2*cos(2*pi*k/n)`.
  * CTQW unitarity: `U^† U == I`; time-avg `P` rows sum to 1, `P >= 0`.
  * Laplacian nullspace dim == number of connected components (this test
    DOUBLES as a disconnection detector — see 0b).
* **Scientific relevance** (does coherence buy anything?):
  * dephasing sweep via Haken–Strobl `omega in [0,1]`: tabulate AUC(omega).
    Flat AUC ⇒ coherence irrelevant, the "quantum walk" is a graph kernel.
    (Existing data already suggests flat — formalize it.)

### 0b. Data cleaning (scripted, deterministic — gemmi/Biotite, headless)
Replaces the manual PyMOL procedure. Per-target config drives the exceptions.

* strip waters, ions, cofactors, alt-locs (keep occupancy 'A'/highest),
  insertion codes; normalize to one model.
* keep `polymer.protein`; **keep `polymer.nucleic` for MYC_MAX (1NKP is
  cMyc/Max on DNA)** — config flag `keep_nucleic`.
* chain selection by biological assembly, NOT "largest chain" by default:
  KRAS/BCR/PTP1B single-domain OK; myosin is a complex; hemoglobin/ATCase
  allostery is inter-subunit — config flag `chains` / `assembly`.
* **correct ligand selection (allosteric vs orthosteric), curated per target.**
  Known bug: BCR-ABL `pick_drug` chose NIL (nilotinib, ATP-site orthosteric)
  over the allosteric ligand. The challenge wants the myristoyl/asciminib site.
* missing residues: **do not model unresolved apo loops** — they are often the
  cryptic pocket and modeling them fabricates the answer. Work on the apo/holo
  common resolved set; flag gaps; bridge virtually only for graph connectivity.
* quality quarantine: resolution, degenerate/zero B-factors, completeness.
  Myosin 5TBY (parsed "20 Å", B≈2.3, drug not detected) is quarantined until a
  usable structure is sourced.

**Gate:** no disconnected graphs (0a nullspace test), every target has a
curated allosteric pocket and a sane source set, quarantined targets excluded.

---

## Phase 1 — apo/holo superposition + learnability

The most important physical gate: is the answer even in the apo topology?

* Kabsch/SVD superpose holo onto apo on common Cα; per-chain RMSD discrepancy
  (catches register/numbering errors independently of sequence alignment).
* map the holo pocket onto the apo frame **by 3D position** — cross-checks the
  sequence-alignment label mapping; disagreement = label bug, caught
  geometrically.
* **cryptic-openness gate:** per-residue apo→holo RMSD at the pocket. If the
  pocket rearranges substantially apo→holo (KRAS SII-P is the textbook cryptic
  case), the apo contact graph does not encode the pocket and no topology-only
  method can recover it. Report as "pocket absent from apo topology" — a
  finding, with a figure — rather than dropping the target silently.

### 1b. Conformational-change mode analysis (the apo/holo "physics" estimate)
Turns the observed motion into modes / timescales / energies, and **calibrates
the CTQW propagation time** (closes the "is t meaningful" hole).

* `Δr = holo_aligned − apo` (3N).
* apo ANM modes `u_k`, eigenvalues `λ_k` (drop 6 rigid-body).
* cumulative overlap `CO(m) = ||proj_{k≤m} Δr|| / ||Δr||` — how few modes carry
  the change (Tama–Sanejouand: usually 1–3 low modes).
* calibrate spring constant κ by matching ANM fluctuations to crystallographic
  B-factors.
* per-mode amplitude `a_k = Δr·û_k`; elastic energy `E_k = ½ κ λ_k a_k²`.
* **timescale: overdamped (solvent) relaxation `τ_k ~ ζ/(κ λ_k)`** is the
  physical number; underdamped period `2π/ω_k` is a lower bound only. Report the
  relaxation time.
* set the CTQW propagation time `t` to the dominant-mode timescale; add a
  sensitivity test (sweep t_max, top-5 Jaccard stability) and an infinite-time
  (parameter-free, decoherent-limit) comparison.
* operator-design check: if Δr lives in modes the NES filter damps, the filter
  is removing the signal.

**Gate:** per target, "learnable from apo?" yes/no. Only learnable targets
proceed to ceiling/LOPO; non-learnable ones become reported findings.

---

## Phase 2 — Ceiling (best supervised fit)

The feasibility gate for blind work. Heavy optimizer, answer key in hand
(leakage is the *goal* here), honest labeling.

* strongest search available (Optuna, many trials) per surviving target.
* report as an **optimistic in-sample upper bound** with block-bootstrap CI.
* must beat the right baselines to count: random residues, non-functional
  surface pockets (challenge bar), AND degree/betweenness centrality. A ceiling
  that node degree also reaches is structure, not your method.
* surface-accessibility / non-active-site filter on predictions (the challenge
  scores vs non-functional *surface* pockets; a buried active-site-adjacent
  predictor fails this even at high raw AUC).

**Gate:** ceiling-minus-baseline per target. If the ceiling sits at the floor
(plausible for KRAS given current numbers), blind LOPO is not worth running —
report the ceiling result.

---

## Phase 3 — Blind generalization (LOPO)

Only on targets whose ceiling clears the baselines.

* `leave_one_protein_out` + `select.unsupervised_score` (focusing,
  source-specificity, ballistic exponent) — label-free config selection,
  enforced by `protocol.FROZEN`.
* headline number: **ceiling − LOPO gap** = quantified cost of not knowing the
  answer.

---

## Phase 4 — External cross-check + analysis + report

* **External predictors as a baseline column AND a diagnostic:** run targets
  through ProteinLens (bond-to-bond propensity), AlloPred/PASSer/DeepAllo
  servers. If they hit apo pockets and we don't → our problem is the operator
  (ceiling reachable). If they also miss → corroborates "signal absent from
  apo." Either way it sharpens the story.
* analysis: quantum-vs-classical on same H, per-term ablation, apo↔holo
  consistency, spectral/low-mode enrichment.
* report: verdict template (already prose in the notebook) → code that fills
  from frozen-run numbers; the dephasing-sweep (0a) and apo/holo-RMSD (1) results
  are likely the two strongest honest findings regardless of LOPO outcome.
* quantum-hardware story: Trotter depth + qubit budget; QSW (non-reciprocal,
  N²×N²) demonstrated on coarse-grained graphs only.

---

## Repo structure

```
src/allostery/
  data.py          fetch, parse Cα                                    [have]
  clean.py         NEW: deterministic structure cleanup (Phase 0b)
  labels.py        NEW: curated ligand pick, residues_near, seq-align map,
                   holo_pocket_mask, functional_indices, terminal_mask
  superpose.py     NEW: Kabsch superpose, per-chain RMSD, 3D pocket map,
                   cryptic-openness; mode-projection / κ calibration (Phase 1b)
  potentials.py    NEW: V_B, V_T, V_R, V_C, V_M  (H_new physics)
  hamiltonians.py  H1–H13, build_H_new, build_H10, normalized Laplacian  [have]
  propagators.py   heat, green(dephased), ctqw, qsw, chiral, spread      [have]
  metrics.py       P@k, AUC, block-bootstrap CI, perm, graph_features,
                   guardrails, distance-bias quantile correction (ProteinLens) [have+]
  baselines.py     NEW: degree/betweenness + external (ProteinLens/AlloPred…)
  select.py        unsupervised selector (focusing/specificity/ballistic)  [have]
  protocol.py      DEV/FROZEN firewall + leave_one_protein_out             [have]
  pathways.py      NEW: current-flow / edge-propensity pathway extraction
                   (the real version of the "green tube")
  coarse.py        NEW: Louvain/spectral coarse-grain + Trotter cost
  analysis.py      NEW: quantum_vs_classical, ablation, apo_holo_consistency,
                   spectral_enrichment, dephasing_sweep
  diagnostics.py   NEW: operator diagnostics + failure-mode classifier
  viz.py           structure/pathway viz (presentation only)
  report.py        verdict template + hit-list deliverable
config/targets.yaml   frozen registry: 4.5 Å pocket, curated allosteric ligand,
                      keep_nucleic / chains per target
tests/                physics unit tests (Phase 0a) + guardrails           [have+]
notebooks/report.ipynb  THIN: imports package, makes figures only
```

---

## Feature backlog

### Correctness / validity (do first)
- [ ] analytical physics tests: Bessel line, dimer Rabi, cycle spectrum,
      nullspace==components, CTQW unitarity.
- [ ] dephasing sweep AUC(omega) as the quantum-relevance test.
- [ ] deterministic cleanup; curated allosteric ligand per target; 4.5 Å pocket.
- [ ] apo/holo superpose + cryptic-openness gate + 3D pocket cross-map.
- [ ] mode-projection (cumulative overlap, κ-calibration) → physical t for CTQW.
- [ ] propagation-time sensitivity + infinite-time-average comparison.

### From ProteinLens / external work
- [ ] distance-bias **quantile correction** on scores (fair long-range ranking).
- [ ] **current-flow / edge-propensity pathway extraction** (model-derived
      pathway, replaces the sequence-range "green tube").
- [ ] external baseline column: ProteinLens, AlloPred, PASSer, DeepAllo servers.
- [ ] (ablation only, labeled outside topology-only) atomistic energy-weighted
      graph arm — keep optional; it fights the ENM assumption and the qubit budget.

### Method / submission
- [ ] ceiling with bootstrap CI + baseline beat (random/surface/degree).
- [ ] surface-accessibility / non-active-site filter on predictions.
- [ ] blind LOPO + ceiling−LOPO gap.
- [ ] coarse-graining + QSW non-reciprocity demo + Trotter/qubit estimate.
- [ ] report generator from frozen numbers.

---

## AI-assisted migration workflow (VSCode + agent)

1. one phase per branch; merge only when `pytest` is green AND one target's
   numbers eyeballed. Never batch phases — a confident agent will "fix" the
   firewall into leakage.
2. notebook outputs are a **regression oracle**: e.g. `build_H_new(KRAS_apo)`
   must reproduce spectrum `[-3.867, 8.703]`, eff_rank 117.7 (cell #15). Pin in
   a test so the refactor can't drift.
3. guardrails (degree-corr, constant-family, AUC↔distance, pocket-size,
   ligand-validity) stay green throughout — they are the agent's contract.
4. DEV vs FROZEN: scored targets only ever run the FROZEN path; selection cannot
   read labels.

## Compute note
Trivial: N≈150–300 dense eigendecomps, ms each; full study across ~10–15
proteins is tens of CPU-hours, embarrassingly parallel, no GPU. QSW (N²×N²) only
on coarse-grained N≤64. Braket/Classiq only for a small real-circuit demo.
Bottleneck is rigor and data curation, never compute.
