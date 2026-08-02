# TASK-0185 Conformational-search reformulation — cryptic pockets as a search problem, and where the hardness actually is

## Context

- ID: TASK-0185
- Title: record, with its supporting measurement, the reformulation of cryptic
  pocket prediction from *residue scoring on a static apo structure* to
  *search over an ENM-generated conformational ensemble for structures in
  which the pocket forms* — and locate precisely where a quantum claim is and
  is not defensible within it.
- Status: TODO
- Owner: Architect/Planner (**writing and one measurement — not a build**)
- Claimed By: —
- Claimed At: —
- Source: orchestrating collaborator (Bartosz), 2026-07-29: *"how to
  fold/vibrate the protein given only the APO structure… find the family of
  low-energy structures in which a pocket forms with the expected properties."*
- Priority: **P1 — the spine of the forward proposal, and the strongest
  Technical-Approach argument available to [[TASK-0184]]. ~1 day, writing plus
  one measurement. Do NOT build the pipeline before the freeze.**

## Why this matters — the register has been solving a category error

A cryptic pocket is *defined* by absence in the apo structure. KRAS's
Switch-II pocket does not exist in 4OBE; sotorasib induces it. **Every static
apo scorer in this register — ~40 observables, 226 scored cells — has been
ranking residues on a structure in which the target feature is not present.**

That is a better explanation of the program's results than any mechanism
hypothesis tested to date, and it is a *simpler* one. It also predicts the
register's own pattern, which no other explanation does:

| Target | Cryptic? | Evidence | fpocket AUC |
|---|---|---|---|
| BCR_ABL1 | **No** — pre-formed | apo→holo pocket RMSD ratio **0.49**, moves *less* than background ([[TASK-0120]]) | **0.8596** |
| KRAS_G12C | Yes (but overlaps active site, 3.75 Å) | [[TASK-0169]] | 0.8348 |
| CARDIAC_MYOSIN | Unresolved (label substituted) | [[TASK-0124]] | 0.5345 |

A purely geometric detector does *best* where the pocket is already open.
That is what the category-error reading predicts.

**And this is legal.** §Constraint 3 forbids *"classical MD trajectories as
inputs"* — not conformational sampling. ENM equilibrium ensembles are
closed-form Gaussian draws (amplitude ~ N(0, √(kT/λ))), no integrator, no
trajectory. Challenge reference **[1]** is Zheng 2023, *"Predicting allosteric
sites using fast conformational sampling as guided by coarse-grained normal
modes"* — the challenge's own first citation is this method, and the register
has never run it. Reference **[2]** (CrypToth) does the mixed-solvent-MD
version of the same idea.

**The elegant consequence.** [[TASK-0163]]'s fpocket result is currently the
register's most damaging finding — a 2009 geometric tool with no dynamics and
no seed beats every observable here on 2/3 targets. Under the search framing
it inverts: **fpocket becomes the oracle, not the competitor.** The method is
not "out-score fpocket on apo"; it is "search conformational space for the
structure where fpocket fires." That reuses an already-vendored, already-run
tool ([[TASK-0163]]) as the constraint checker.

## The measurement — and why it moves the quantum claim

The intuitive quantum argument is rare-event search: the conformational space
is astronomically large, pocket-open states are rare, and amplitude
amplification gives 1/√p against classical 1/p. **Measured, that argument
fails at the backbone layer.**

Two-lobe fold with a closable cleft, ANM Hessian, exact Gaussian
equilibrium sampling in mode space
(`conformational_search_prototype_REFERENCE.py`, runs):

```
n_modes   p(cleft opens +25%)
5         0.244
20        0.518
40        0.694
```

**Pocket opening is not rare** — ENM soft modes *are* the opening motions.
That is what makes ENM work, and it is fatal to a Grover-style claim.

The realistic conjunctive constraint (specific site, druggable volume band,
buried, energetically accessible) is rarer but still cheap:

```
n_modes=20   C1=0.400 C2=0.716 C3=0.017 C4=0.764 | JOINT p=0.00267
             classical ~375 draws | amplitude-amplification ~19
```

~375 draws is seconds. A 20× speedup on a trivial computation is not a
quantum advantage claim and a reviewer would say so. Note the rarity is
driven almost entirely by **C3, specificity** (p ≈ 0.017) — localising the
opening to *this* site rather than globally inflating.

**Where the hardness actually is: the side-chain layer.** Backbone motion is
ENM-tractable (continuous, ~10–40 dimensional, dense targets). But cryptic
pockets do not open by backbone breathing alone — they open by **side-chain
repacking**, and side-chain placement over rotamer libraries is discrete and
**NP-hard** (Pierce & Winfree 2002, *Protein Engineering*), with an existing
QUBO literature for annealers. That is [[TASK-0181]] Phase B.

## Intent Contract

- Outcome: a `RESULTS.md` section + `documentation/CONFORMATIONAL_SEARCH.md`
  stating the reformulation, the measurement above reproduced on ≥1 real apo
  target, the honest negative on backbone-layer rare-event search, and the
  side-chain formulation as the forward claim — written to be lifted into
  [[TASK-0184]]'s Technical Approach section.
- Why required, not assumed: the reformulation reinterprets the entire
  register and is the proposal's strongest differentiator; the rare-event
  argument must be measured rather than asserted, because it is the part a
  quantum reviewer will test.

- In Scope:
  - **One measurement on real data:** generate ENM equilibrium ensembles for
    the mandatory apo structures, run the already-vendored fpocket
    ([[TASK-0163]]) across the ensemble, and report (a) does the known holo
    pocket appear in *any* sampled conformation, and (b) at what frequency.
    This is the single most informative number the reformulation can produce
    and it is cheap — the ensemble generator is closed-form and fpocket is
    already wired.
  - Reproduce the rarity measurement on that real ensemble (backbone layer).
  - Write the side-chain QUBO formulation as forward content (encoding, qubit
    count, falsification criteria) — cross-referenced to [[TASK-0181]] Phase B
    so the two do not diverge.
  - State the boundary against `HOLO_DIRECTION_MODULE.md`/[[TASK-0015]]
    explicitly (see below).

- Out Of Scope:
  - **Building the search pipeline.** Forward-proposal content only before the
    freeze. This is the constraint most likely to be violated because the idea
    is interesting; it is stated first for that reason.
  - Any MD.
  - Retracting or re-running existing scored cells. The reformulation
    *explains* them; it does not invalidate their arithmetic.
  - Claiming the reformulation would have worked. It is untested.

- Constraints And Invariants:
  - Ensembles generated in closed form from ENM modes — no integrator, no
    trajectory. Assert this in code and say it in the write-up; it is the
    §Constraint 3 compliance argument and a reviewer will check it.
  - fpocket run with the same parameters as [[TASK-0163]], so the numbers are
    comparable to the existing baseline rather than a new convention.
  - **The measurement is reported whichever way it comes out.** If the known
    pocket never appears in an ENM ensemble, that is a strong negative on the
    whole reformulation and must be published as prominently as a positive.
  - No claim that this is quantum. The reformulation is classical; only the
    side-chain layer carries a quantum claim, and that claim is a proposal.

- Planned Validation:
  - **Positive control:** run the ensemble+fpocket procedure on BCR_ABL1,
    whose pocket is *pre-formed* (RMSD ratio 0.49). The pocket should be found
    at or near the apo conformation, at high frequency. If the procedure
    cannot find an already-open pocket, it is broken and no cryptic result
    from it is trustworthy. **Run this first.**
  - **Negative control:** the same procedure should *not* report a druggable
    cavity at a randomly chosen distal surface patch at comparable frequency.
  - Cross-check ensemble validity: the generated ensemble's per-residue MSF
    must match the analytic GNM/ANM MSF. If it does not, the sampler is wrong
    and every downstream number is meaningless.

## In Progress

None

## TODO

- [ ] Ensemble sampler (closed-form, ENM modes), with the MSF cross-check.
- [ ] **BCR_ABL1 positive control first** — can the procedure find an open pocket?
- [ ] Ensemble + fpocket on the mandatory apo structures; report pocket
      appearance frequency.
- [ ] Reproduce the backbone rarity measurement on real ensembles.
- [ ] Negative control at a random distal patch.
- [ ] Write `CONFORMATIONAL_SEARCH.md`; hand to [[TASK-0184]] and [[TASK-0183]].
- [ ] Cross-reference the side-chain formulation with [[TASK-0181]] Phase B.

## Dependency

- [[TASK-0163]] (Done) — vendored fpocket, already built and parameterised.
- [[TASK-0120]], [[TASK-0124]], [[TASK-0169]] (Done) — the crypticity evidence.
- [[TASK-0150]] (Done) — ENM ensemble generation already exists here (and its
  finding that AE on ENM data recovers ANM modes exactly, 0.9999–1.0000,
  is why no ML layer belongs in this pipeline).
- [[TASK-0181]] — Phase B is this task's forward claim.

## Open Questions

- **Boundary against [[TASK-0015]]/`HOLO_DIRECTION_MODULE.md`.** That module
  predicts the apo→holo *deformation direction* from apo and feeds a deformed
  graph to transport. This task samples the *equilibrium ensemble* and asks
  whether the pocket appears anywhere in it — no direction prediction, no
  transport. They are close and the write-up must say which side it is on.
  **Recommend: state explicitly that this task subsumes the motivation for
  TASK-0015 and that TASK-0015 should be re-scoped or closed** rather than
  leaving two overlapping specs in the register.
- Is Cα-level ENM enough to open a cryptic pocket at all? Probably not on its
  own — which is the argument *for* the side-chain layer, and should be stated
  as such rather than discovered later.
- Does the reformulation change what [[TASK-0177]]'s label should be? Possibly:
  under a search framing the natural ground truth is *"a conformation in which
  fpocket reports the holo pocket,"* not a contact set. Flag for 0177; do not
  reopen it before the freeze.
- How much of this belongs in six pages? It is the Technical-Approach spine,
  so it earns real space — but the honest negative on backbone rare-event
  search must travel with it. A reviewer who finds the 1/√p argument and then
  discovers we measured it and it fails will trust everything else more.

## Done

(not yet)
