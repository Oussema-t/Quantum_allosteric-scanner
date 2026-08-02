# TASK-0178 Binding-response coupling — module, specificity statistic, and evaluation

## Context

- ID: TASK-0178
- Title: implement the exact Gaussian-network allosteric coupling free energy
  `ddG(A,B)`, derive the distance-normalised specificity statistic that makes
  it scoreable, and run it through the unmodified verdict pipeline.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: orchestrating collaborator (Bartosz), 2026-07-29: *"the drug docking
  at the pocket should lead to the protein reorganising so that the active
  site is affected… maybe the protein exhibits the loss of propensity to
  something and that ought to be the observable."*
- Priority: **P1 — the strongest remaining *scientific* direction, but NOT on
  Phase-1's critical path. Ship [[TASK-0177]]/[[TASK-0180]] first.**
- **Revised 2026-07-29: absorbs the retired TASK-0179.** The original split
  (module / evaluation) was unnecessary — same owner, same outcome, and the
  module is meaningless without the evaluation. **Do not re-file 0179.**
- Suggested Predecessor: **[[TASK-0177]]**, same thread. Not a hard
  dependency for Phase A (the `response.py` module + its reciprocity/
  zero-coupling/dumbbell gates build independently of any label), but Phase
  B's final scoring needs 0177's frozen consensus label (incumbent usable
  meanwhile, see Dependency below) and the same owner carrying
  structural-biology/GNM context forward is the natural order. Recorded
  2026-08-01 (Architect).

## Why this matters — the register measures the wrong kind of object

Every observable here has the shape *"seed somewhere, watch where amplitude
goes."* Allosteric inhibition is not that. It is: a ligand binds, the
accessible ensemble changes, and the active site loses the propensity to do
its job. A *response* to a constraint, not a propagating signal.

For a Gaussian network with energy `(1/2) x^T K x`, this is exact and
closed-form. A ligand at site S is a set of added cross-links `P_S`
(mechanically, that *is* what binding does). With `F(K) = (kT/2) ln pdet(K)`:

```
ddG(A,B) = F(K + P_A + P_B) − F(K + P_A) − F(K + P_B) + F(K)
```

Four log-determinants. No MD, no trajectory, no sampling — legal under
§Constraint 3 for the same reason GNM is.

### The reciprocity theorem, and what it says about [[TASK-0162]]

`ddG` is a mixed second derivative of a free energy, so it is **exactly
symmetric**. Verified on a 249-residue synthetic fold:

```
ddG(active -> pocket) = -0.0000006966
ddG(pocket -> active) = -0.0000006966
|difference|          =  0.00e+00
```

[[TASK-0162]] measured forward clearing its floor in 10/25 cells and reverse
in 4/25, with CARDIAC_MYOSIN `prs_low` collapsing 0.836 → 0.321. **For a
genuine equilibrium coupling observable that asymmetry is impossible.** So
TASK-0162 is not a finding about allostery — it is proof that the propagation
observables are not coupling measures. Reciprocity is therefore this module's
**correctness gate**, not a result to be discovered.

## The trap, and the fix — both pre-measured

**Raw magnitude is worse than everything in the register.** On the same fold:

```
rho(|ddG|, -hop)    = +0.930
rho(|ddG|, -euclid) = +0.949      [CTQW on real targets: +0.61 to +0.97]
```

Elastic response decays with distance, so raw coupling magnitude is a
distance detector. **The magnitude is the wrong statistic — never report its
AUC as a result.**

The fix is a **specificity** statistic: coupling relative to what a generic
site at the same distance would give.

```
y_j     = log10 |ddG(active, patch_j)|
score_j = (y_j − mean(y over j' in the same hop shell))
          / (std(y over the same shell) + eps)
```

Hop shells from apo topology only — no label information, no leakage. This is
[[TASK-0123]]'s stratification applied as a *score transform* rather than only
as an evaluation lens, which is the substantive novelty.

With [[TASK-0167.001]]'s channel plant (which provably cannot move `hop`,
`euclid` or unweighted `degree` — all three rebuild a binary contact matrix
from `coords` alone, `baselines.py` l.59/65/116):

| plant strength | ddG(act,pocket) | raw \|ddG\| AUC | **shell-normalised AUC** | hop AUC |
|---|---|---|---|---|
| 0.0 | -6.97e-07 | 0.079 | 0.321 | 0.101 |
| 1.5 | -8.96e-06 | 0.135 | **0.467** | 0.101 |
| 4.0 | -7.45e-05 | 0.198 | **0.625** | 0.101 |
| 10.0 | -4.71e-04 | 0.262 | **0.738** | 0.101 |
| 30.0 | -4.51e-03 | 0.381 | **0.769** | 0.101 |

Coupling value moves ~6,500× while every proximity baseline is frozen. Raw
magnitude never clears the floor; the normalised residual clears from
strength 1.5, where the CTQW occupation needed strength 10 — **roughly 3–6×
more sensitive.** That is a synthetic-fold estimate and **must be measured,
not asserted.** Producing the real number is this task's core deliverable.

Reference implementation: `response_prototype_REFERENCE.py` (runs; scope
limits stated in its header).

## Intent Contract

- Outcome: `src/allostery/response.py` with `coupling_free_energy`,
  `ligand_stiffness`, `coupling_profile`, `active_site_rigidification`,
  `coupling_specificity`; full test module; and a scored evaluation across
  mandatory + generalization targets with its LOD reported beside CTQW's.
- Why required, not assumed: no observable in the register measures a
  perturbation response; [[TASK-0166]] tested the *unperturbed* degenerate
  case (static entropy, no binding) and correctly found it dead.

- In Scope — **Phase A, module + gates:**
  - `ligand_stiffness` — clique of springs over the bound site; **same
    nullspace as `K`**, asserted.
  - `coupling_free_energy` via pseudo-determinant, null tolerance derived from
    the spectrum's own scale (not a bare `1e-9` — [[TASK-0128]]: BCR_ABL1 and
    CARDIAC_MYOSIN carry extra near-machine-precision zeros).
  - `active_site_rigidification` — the direct "loss of propensity" form,
    `(msf_A(K) − msf_A(K+P_j))/msf_A(K)`.
  - GNM/Kirchhoff primary. ANM/3N optional and must be justified — the
    6-zero-mode nullspace makes the pseudo-determinant fragile.
  - Low-rank shortcut: `P_j` is rank ≤ |patch|, so a matrix-determinant-lemma
    route should give the whole profile from **one** decomposition
    ([[TASK-0145]] did this for `T(E)`, O(N⁴)→O(N²)). **Verify against brute
    force to 1e-10 before using.**

- In Scope — **Phase B, statistic + evaluation:**
  - `coupling_specificity` as above.
  - **Report `rho(score, -hop)` on every real target BEFORE any AUC.** If it is
    not materially below the raw +0.93, the normalisation failed on real data
    and that is the result — [[TASK-0149]]'s precedent is explicit that a
    synthetic decorrelation claim (predicted 0.08–0.16) can fail to transfer
    (observed −0.51 to +0.63).
  - Full verdict chain, unmodified. Record **which gate binds**, per target.
  - Nulls: `compact_patch_matched` at each target's measured pocket Rg, with
    scattered / ball / matched reported side by side ([[TASK-0167.003]]'s
    calibration question is live).
  - LOD via [[TASK-0167.002]]'s detection curve, same plant and grid, so the
    CTQW comparison is like-for-like.
  - Score against all three of [[TASK-0177]]'s labels once available.

- Out Of Scope:
  - Reporting raw-magnitude ranking as a result.
  - Tuning shell definition, `kappa`, or patch size against any AUC. **Fix the
    grid before running.**
  - Any quantum claim. **This observable is classical** — see Open Questions.
  - Replacing any existing observable.

- Constraints And Invariants:
  - **Reciprocity gate:** `|ddG(A,B) − ddG(B,A)| == 0` to machine precision,
    over ≥20 random site pairs on ≥3 topologies. An identity, not a tolerance.
  - **Zero-coupling gate:** `ddG → 0` as sites decouple; exactly 0 on a
    disconnected graph.
  - **Dumbbell gate (mandatory):** run against [[TASK-0103]]'s
    `build_dumbbell_network`. Pre-registered expectation: a *coupling*
    observable tracks the coupling, not the well. **If it tracks the well, the
    module's justification collapses — report it, do not tune `kappa` until
    it passes.**
  - `kappa` is a KNOB: sweep, report spread, flag verdict flips
    ([[TASK-0075]]).
  - Adds cells to the multiplicity budget — count and update [[TASK-0161]].

- Planned Validation:
  - All four gates above, before any real data.
  - Independent route: the Gaussian free energy is (up to constants) the
    configurational entropy, so `ddG` must agree with a direct
    entropy-difference computation. Two routes, one number.
  - Pre-registered falsification, written before running: *if
    `rho(score,-hop)` on real targets stays above ~0.6, or the LOD is no
    better than CTQW's, this observable class adds nothing and the response
    reframing is recorded as tested-and-negative.*

## In Progress

None

## TODO

- [ ] Write the pre-registered falsification into this file before coding.
- [ ] Phase A: module + reciprocity / zero-coupling / entropy-cross-check gates.
- [ ] **Dumbbell gate — pre-register the expected direction first.**
- [ ] Low-rank shortcut, verified to 1e-10 or omitted.
- [ ] `kappa` KNOB sweep.
- [ ] Phase B: `coupling_specificity`; `rho(score,-hop)` **before** any AUC.
- [ ] Full verdict chain; binding gate per target; three null draws.
- [ ] LOD vs CTQW, like-for-like.
- [ ] Re-score against [[TASK-0177]]'s three labels; update [[TASK-0161]].

## Dependency

- [[TASK-0103]] (Done) — dumbbell harness.
- [[TASK-0167.001]] (Done) — `plant.py`.
- [[TASK-0128]] (Done) — floppy-mode / n_zero handling.
- [[TASK-0145]] (Done) — low-rank precedent and its verification bar.
- [[TASK-0123]], [[TASK-0158]], [[TASK-0165]] (Done) — evaluation machinery.
- [[TASK-0177]] — headline label; incumbent usable meanwhile.

## Open Questions

- **Is this quantum?** No, and the task must say so plainly. Log-determinants
  of a Kirchhoff matrix are as classical as this project gets. Honest framing:
  this is the classical mechanism the challenge's own ref [4] (Motlagh &
  Hilser) describes, tested properly for the first time; the quantum framing
  (Gibbs-state preparation / partition-function estimation for Gaussian
  systems) is a **forward proposal**, labelled as such. A real trade against
  criterion 2 — **Bartosz's decision, not an implementer's.**
- Is `kappa` calibratable? Candidate anchor: choose it so the induced
  rigidification at the binding site matches the observed apo→holo B-factor
  drop there. One experiment; if it fails, `kappa` stays a characterised knob.
- Does a clique over the whole site over-model a small drug? Consider
  weighting `P_S` by per-residue ligand contact area. Flag; not in v1.
- **Reverse direction:** reciprocity says it is the same number, so unlike
  [[TASK-0162]] there is nothing to measure — but confirming `ddG` gives an
  identical answer both ways is a cheap, strong consistency check on the whole
  framing. Do it once, state it.

## Done

(not yet)
