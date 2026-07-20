<!-- APPEND to .claude/hypotheses/physics.md, after HYP-P8. Do not renumber. -->
<!-- Source: REVIEW-panel-2026-07-20 (new-observable batch). Tasks: TASK-0139..0142. -->

---

## HYP-P9 · A chiral (broken-time-reversal) walk yields a proximity-orthogonal, directional loop observable

**Claim:** Replacing the real-symmetric operator's hoppings with complex
Peierls phases (a uniform "magnetic" field B, flux = B·(loop area)) produces
a directed bond-current whose Helmholtz-Hodge *circulating* component is
orthogonal to the radial proximity flow by construction, and which tracks
active-site *coupling* rather than distance-to-seed. This is the physically
justified form of "controlled phase shifts" (the collaborator's Idea #2):
an arbitrary initial phase on a real-symmetric H only reshuffles amplitudes
and is an unjustified, label-leaking knob; the only gauge-invariant phase
effect is around cycles.

**Supporting evidence:** Chiral quantum walks break time-reversal only on
cyclic topologies (Zimborás et al. 2013, Sci. Rep. 3, 2361; Lu et al. 2016,
PRA 93, 042302). On synthetic gates this batch: the circulating current
(i) dissociates coupling from well-depth where single-particle imaginary-time
occupation chases the well, and (ii) beats the proximity floor on a distal
loop pocket with residual ρ(score,−dist)≈+0.33 vs the occupation's +0.6..+0.97.
The Hodge gradient/curl split maps exactly onto proximity-flow / loop-signal.

**Counter-evidence / conditions under which this fails:**
- **Single-particle → classically tractable.** This is a *modeling* advantage
  (directionality, loop-native, proximity-orthogonal), not asymptotic quantum
  advantage. The converged occupation limit is provably phase-free
  (TASK-0130); the chiral current is a different, time-reversal-odd observable.
- **No real loop signal.** If pockets are not graph-open (HYP-P10 FAIL), there
  is no non-proximity cycle to circulate in and the score collapses to the
  floor. The synthetic passes prove the observable *can* read a loop, not that
  real pockets carry one.
- **Seed/field gauge.** A field direction or source seed tuned to labels would
  reintroduce overfitting; the flux content is gauge-invariant only if the
  field grid is fixed blind to labels.

**To test:** [[TASK-0140]] — gated benchmark eval vs the proximity floor with
block-bootstrap CIs and distance-stratified AUC + permutation null.

---

## HYP-P10 · Cryptic pockets carry a "near-in-3D / far-on-apo-graph" coordinated-closure signature

**Claim:** The residues a ligand bridges on binding are Euclidean-near but
graph-hop-far in the *apo* contact graph (the open cleft means the apo graph
does not connect them), so mean(apo graph-hop)/mean(Euclidean) among the
pocket residues is anomalously high vs a matched-spread random cluster.

**Supporting evidence:** This is close to the *definition* of a cryptic
pocket (spatially coherent in holo, not connected in the open apo state), so
the premise is more plausible than the generic single-loop idea (which
Falsifier A killed: at 8 Å a spatial cluster is already a clique; a single
ligand chord adds triangles indistinguishable from a decoy, and ambient
b1~8N dwarfs it). On the constructed open-cleft synthetic the signature hits
the ~100th percentile against a matched-spread null.

**Counter-evidence / conditions under which this fails:**
- **Grooves.** A shallow surface groove is contractible and graph-adjacent
  already — no near-space/far-graph anomaly. If the benchmark pockets are
  grooves rather than closing clefts, the signature is absent.
- **Pre-formed pockets.** BCR_ABL1's myristoyl pocket moves *less* than
  background (ratio 0.49, TASK-0120) — likely already graph-connected in apo,
  so this signature should be weak-to-absent there (a per-target prediction).
- **Distinct from the existing openness gate.** This is NOT
  `cumulative_overlap`/`cryptic_openness_gate` ([[TASK-0059]]/[[TASK-0120]]),
  which asks whether the apo→holo displacement is soft-mode-spanned — an
  orthogonal *dynamics* question that can agree or disagree with this
  *structural-graph* one.

**To test:** [[TASK-0139]] — matched-spread random-closure null, all mandatory
+ ASD targets, Bonferroni. This is the premise gate for HYP-P9/P12.

---

## HYP-P11 · Engineered dephasing (ENAQT) does not improve pocket discrimination — it relaxes the walk to the classical/proximity limit

**Claim:** Sweeping a Haken-Strobl dephasing rate γ finds no interior optimum
that improves *discrimination* of pocket vs background, because increasing γ
de-traps the Anderson-localized walker only by driving it toward classical
diffusion, whose occupation is the proximity confound. The ENAQT "optimal
rate" from the transport literature optimizes a different quantity (transfer
efficiency to a known sink), not discrimination.

**Supporting evidence:** Synthetic γ-sweep this batch (`enaqt_sanity.py`):
AUC flat-then-collapsing (0.72→0.16 as γ:0→5) while ρ(occ,−dist) rose +0.10→
+0.68, reaching +0.92 at the classical endpoint. Consistent with the existing
register finding that ENAQT enhances transport 1.24–1.70× but degrades
discrimination in every observed cell, and with the phase-free converged
limit (TASK-0130). Transport-efficiency optima: Mohseni-Rebentrost-Lloyd-
Aspuru-Guzik 2008; Rebentrost 2009; Caruso 2014; Viciani 2015 (experimental
optimum) — all for transfer to a fixed trap, not pocket ranking.

**Counter-evidence / conditions under which this fails (i.e. would overturn):**
- If some interior γ on real data clears the proximity floor with
  non-overlapping CIs and beats the coherent γ=0 point, the prior is wrong and
  the result folds into the submission. The prior is a synthetic; real data is
  the test. This is why the task is run, not assumed.
- The Zeno regime (γ→∞ freezing) is a distinct failure from the classical-
  diffusion crossover; the prior is that discrimination dies at the crossover,
  *before* Zeno — the sweep should report which mechanism dominates.

**To test:** [[TASK-0141]] — γ-sweep on KRAS/ABL/PTP1B, scoring discrimination
AUC vs floor (NOT transport), with the mandatory γ→∞ classical-limit sanity
endpoint and localization-length-vs-γ as the mechanism covariate.

---

## HYP-P12 · The coordinated multi-site closure is a topological void (persistent H2 / Hodge-L1), and this is the only rung where a genuine quantum-advantage object coincides with the biology

**Claim:** A buried pocket a ligand caps is an H2 *void* (not an H1 loop), and
the ligand-as-k-simplex is captured by the Hodge Laplacian L1 (dim ker L1 =
b1; its non-harmonic edge-modes are the flow around the multi-loop cage), both
of which the graph Laplacian discards. Persistent H2 of the apo complex should
localize buried pockets that H1/graph-level observables and grooves miss.

**Supporting evidence:** CrypToth (challenge ref [2]) uses topological data
analysis for cryptic-pocket detection. Falsifier D: a true ring gives a stable
persistent b1; a filled disk / contractible bowl do not (once persistence is
done correctly) — grooves are topologically invisible, consistent with pockets
being voids, not loops. Betti-number / Hodge-Laplacian estimation (Lloyd-
Garnerone-Zanardi) is the canonical (regime-dependent, partially dequantized —
Tang; Gyurik-Cade-Dunjko) quantum-advantage candidate defined on exactly this
structure; Jones-polynomial approximation of the closed curve is BQP-complete
(Aharonov-Jones-Landau).

**Counter-evidence / conditions under which this fails:**
- **Cα resolution.** At an 8 Å Cα cutoff the complex is dominated by spurious
  intermediate-radius cycles (Falsifier D); a real void may not survive to a
  clean persistent H2 generator. Real persistence tooling (GUDHI/Ripser),
  never a homemade b1, is mandatory.
- **Dequantization.** LGZ's speedup survives only in dense-complex / favorable-
  Betti-ratio regimes — the advantage is regime-dependent, a *proposal* claim,
  not a demonstrated one. The classical observable is what this hypothesis
  tests; the quantum claim is forward-looking.
- **Inherits HYP-P10.** If pockets aren't graph-open/void-like, this fails with
  the rest of the family.

**To test:** [[TASK-0142]] — L1 joint-support score + persistent H2 generator
localization vs a matched random-patch null, gated on HYP-P10/HYP-P9 showing
life. b1(ker L1) == E−N+C as the setup-validity gate.
