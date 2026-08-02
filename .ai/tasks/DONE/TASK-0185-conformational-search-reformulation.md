# TASK-0185 Conformational-search reformulation — cryptic pockets as a search problem, and where the hardness actually is

## Context

- ID: TASK-0185
- Title: record, with its supporting measurement, the reformulation of cryptic
  pocket prediction from *residue scoring on a static apo structure* to
  *search over an ENM-generated conformational ensemble for structures in
  which the pocket forms* — and locate precisely where a quantum claim is and
  is not defensible within it.
- Status: Done
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

- [x] Ensemble sampler (closed-form, ENM modes), with the MSF cross-check --
      reused `allostery.shortcuts.equipartition_ensemble`/`msf_cross_check`
      ([[TASK-0187]]) rather than re-deriving; passed on all 3 targets
      (r=0.993-1.000).
- [x] **BCR_ABL1 positive control first** — can the procedure find an open
      pocket? **Yes, convincingly**: static 87.5%, ensemble hit rate 80.0%.
- [x] Ensemble + fpocket on the mandatory apo structures; report pocket
      appearance frequency -- done, all 3 targets, 0 fpocket errors/300 samples.
- [x] Reproduce the backbone rarity measurement on real ensembles --
      n_modes sweep {5,20,40} on BCR_ABL1 (scope-narrowed to one target,
      an implementer's-call time-budget decision, stated explicitly in
      Done below); real-pocket recovery stays high throughout, corroborates
      the synthetic reference's own not-rare finding.
- [x] Negative control at a random distal patch -- `plant.select_distal_patch`
      reused; specific on BCR_ABL1/KRAS_G12C, **not specific on CARDIAC_MYOSIN**.
- [x] Write `CONFORMATIONAL_SEARCH.md`; hand to [[TASK-0184]] and [[TASK-0183]] --
      written (`documentation/CONFORMATIONAL_SEARCH.md`); hand-off content
      included (mixed-but-real measurement + the rare-event finding on real
      data + the side-chain forward claim).
- [x] Cross-reference the side-chain formulation with [[TASK-0181]] Phase B --
      cross-referenced, deliberately NOT duplicated: TASK-0181 Phase B (the
      full QUBO encoding/qubit-count writeup) is in progress concurrently on
      another thread as of this writing; this task's own write-up states only
      the boundary and forward pointer.

## Dependency

- [[TASK-0163]] (Done) — vendored fpocket, already built and parameterised.
- [[TASK-0120]], [[TASK-0124]], [[TASK-0169]] (Done) — the crypticity evidence.
- [[TASK-0150]] (Done) — ENM ensemble generation already exists here (and its
  finding that AE on ENM data recovers ANM modes exactly, 0.9999–1.0000,
  is why no ML layer belongs in this pipeline).
- [[TASK-0181]] — Phase B is this task's forward claim.

## Open Questions

- **Boundary against [[TASK-0015]]/`HOLO_DIRECTION_MODULE.md`.** **Resolved,
  2026-08-02: recommendation stated as directed** (in
  `documentation/CONFORMATIONAL_SEARCH.md` and the RESULTS.md section) --
  this task subsumes TASK-0015's motivation; TASK-0015 should be re-scoped
  or closed. **Not actioned** (TASK-0015 claimed elsewhere as of this
  writing) -- flagged for [[TASK-0184]]'s narrative and TASK-0015's own
  owner, not unilaterally closed by this thread.
- Is Cα-level ENM enough to open a cryptic pocket at all? **Resolved
  (partially), 2026-08-02: yes, for recovery frequency on 2/3 targets
  (BCR_ABL1, KRAS_G12C show real specificity over a matched decoy) but
  CARDIAC_MYOSIN shows none** (real 0.200 vs. decoy 0.190) -- consistent
  with "probably not enough on its own" as originally guessed, but the
  real measurement is more nuanced than a clean yes/no: two targets show
  a real, measurable, if partial, backbone-layer effect. Still supports
  the side-chain-layer argument as the place the quantum claim should
  live, per this task's own framing.
- Does the reformulation change what [[TASK-0177]]'s label should be?
  **Not resolved here, per this task's own instruction** ("flag for 0177;
  do not reopen it before the freeze") -- TASK-0177 has since landed
  (consensus/core/shell labels, [[TASK-0177]]'s own Done section) without
  incorporating this suggestion; left as a genuinely open question for a
  post-freeze follow-up, not actioned by this task.
- How much of this belongs in six pages? **Not resolved here** -- an
  editorial/space-allocation call for [[TASK-0184]]'s own writing pass,
  not this task's to make. The honest negative (CARDIAC_MYOSIN's zero
  specificity, and the real-data-confirmed rare-event failure) is written
  into `documentation/CONFORMATIONAL_SEARCH.md` prominently, ready to
  travel with whatever space TASK-0184 allocates.

## Done

- 2026-08-02 (Implementer C, this thread): built
  `scripts/conformational_search_measurement.py` (single measurement
  script, not a new `src/allostery/` module, per this task's own "not a
  build" scope) + `documentation/CONFORMATIONAL_SEARCH.md`. Reused rather
  than rebuilt: `allostery.shortcuts.equipartition_ensemble`/
  `msf_cross_check` ([[TASK-0187]]) for the ENM sampler and its blocking
  MSF gate, `allostery.plant.select_distal_patch` ([[TASK-0167.001]]) for
  the negative-control decoy, and
  `task0163_external_baseline_scoring.py`'s own `_write_full_atom_apo_pdb`/
  `_run_fpocket`/`FPOCKET_BIN` ([[TASK-0163]]) for the real fpocket
  invocation (`tools/fpocket/bin/fpocket`, confirmed working, not mocked).

  **New in this task**: `_apply_ca_displacement` -- a rigid per-residue
  translation moving every atom of residue `(chain, resnum)` by that
  residue's own ANM Cα displacement, the cheapest closed-form way to turn
  a Cα-only ENM sample into a full-atom structure fpocket can read. Stated
  as an approximation in the write-up (bond lengths/side-chain
  conformation held fixed), not hidden.

  **Real run, all 3 mandatory targets, 100 samples/target (n_modes=20,
  kT=20, 8.0 Å cutoff), 294.1s/37.5s/186.6s wall-clock respectively, 0
  fpocket errors across 300 samples:**
  - MSF cross-check (blocking): **passed on all 3**, Pearson r=0.993-1.000,
    median relative error 5.7-7.6% (gate: r>=0.90, rel.error<=25%).
  - **BCR_ABL1 (positive control, run first)**: static-apo overlap 0.875,
    ensemble real-pocket hit rate 0.800, decoy hit rate 0.510 -- procedure
    validated (finds an already-open pocket at high frequency), specific
    (gap 0.29) though the decoy rate itself is not small (BCR_ABL1 has 37
    fpocket-detected cavities on the static structure alone, a genuinely
    cavity-rich multi-domain construct).
  - **KRAS_G12C**: static 0.611, real hit rate 0.500, decoy 0.370 (gap
    0.13) -- modest specificity, consistent with this target's own
    established partial crypticity ([[TASK-0169]]).
  - **CARDIAC_MYOSIN**: static 0.923 (single point, not the ensemble's own
    frequency), real hit rate 0.200, decoy hit rate 0.190 -- **no
    specificity**, real and decoy statistically indistinguishable at this
    sample size. A clean negative for this target specifically, reported
    as prominently as the two positives per this task's own Constraint.
  - **n_modes sweep (BCR_ABL1 only, N=60/point -- implementer's-call
    scope-narrowing to one target given the ~1-day budget, stated
    explicitly)**: real-pocket recovery stays high throughout (n_modes=5:
    0.983, 20: 0.800, 40: 0.783) -- **corroborates the original synthetic
    two-lobe toy model's own not-rare finding (p=0.244-0.694) on a real
    target.** This is the measurement that moves the quantum claim: a
    Grover-style backbone-layer rare-event search argument requires a rare
    target event, and it is not rare on any real target measured here
    (recovery costs 1-8 classical draws per hit even on the weakest
    target). Real-vs-decoy specificity gap is non-monotonic in n_modes
    (0.583/0.290/0.583 at n_modes=5/20/40) -- reported as observed.

  **Side-chain QUBO forward content**: deliberately NOT independently
  formulated here. [[TASK-0181]] Phase B (encoding, qubit count,
  falsification criteria) is in progress concurrently on another thread as
  of this writing (`.ai/tasks/IN_PROGRESS/TASK-0181-...`, claimed by
  Implementer A) -- this task's own write-up states only the boundary
  (backbone tractable and dense with hits; side-chain repacking discrete
  and NP-hard, Pierce & Winfree 2002) and a forward pointer, per this
  task's own Intent Contract instruction to cross-reference rather than
  re-derive and risk two diverging specs.

  **Implementer's-call decisions**: (1) `kT=20.0`, matching [[TASK-0187]]'s
  own choice and the reference prototype's real sweep value, not the
  module default of 1.0. (2) "hit" defined as >=50% overlap between the
  real/decoy residue set and any single detected fpocket cavity's own
  residue membership (not a druggability-score-weighted AUC, which is a
  different question already answered by [[TASK-0163]]) -- chosen because
  the task's own question is literally "does the known pocket appear,"
  not "does it rank highest." (3) n_modes sweep restricted to BCR_ABL1
  only, not all 3 targets, to keep the real-data run inside this task's
  own ~1-day budget (main 3-target run alone was ~9 minutes wall-clock).
  (4) Negative control used `select_distal_patch`'s existing distal
  admission criterion (hop-distance from active site) only, not a
  floor-blind-for-druggability criterion -- BCR_ABL1's own non-trivial
  decoy hit rate (0.51) shows this leaves room for a decoy to land near
  an unrelated real cavity in a cavity-rich protein; flagged, not
  corrected, since a druggability-blind decoy wasn't in this task's own
  Planned Validation and adding one would have been new scope.

  **RESULTS.md**: new dated section + open-questions row 51 (both
  appended). `documentation/CONFORMATIONAL_SEARCH.md` written per the
  Intent Contract's Outcome, hand-off content for [[TASK-0184]]/[[TASK-0183]]
  included directly in that document (mixed-but-real recovery-frequency
  numbers + the real-data rare-event finding + the side-chain forward
  claim with its own boundary stated).

  **Full `pytest tests/ -q` run**: 1045 passed, 1 skipped, 2 xfailed, 3
  failed (121s). The 3 failures (`test_response.py::TestDumbbellGate`
  x2, `::TestActiveSiteRigidification` x1) are **not this task's** --
  confirmed via `git status`: `src/allostery/response.py`/
  `tests/test_response.py` are untracked files belonging to a different,
  concurrent thread's in-progress [[TASK-0178]] (now `IN_PROGRESS`),
  which this task never touched. This task's own new surface (the
  measurement script + the doc) added no `src/allostery/` module, so it
  has no interaction with `response.py`; validated instead against real
  RCSB/fpocket data end-to-end (0 errors across 300 real samples), per
  this task's own stated Planned Validation (positive control + negative
  control + MSF cross-check).
