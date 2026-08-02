# TASK-0176 Phase-1 end-to-end path — apo → predicted pocket → undisputed holo verification

## Context

- ID: TASK-0176 (parent coordinator — subtask table below)
- Title: close the challenge's Phase-1 loop end to end: (a) an *undisputable*
  holo-derived ground truth, and (b) a single apo-only run emitting ranked
  **pockets** scored against it — plus the forward-proposal spine that
  explains where the method goes next.
- Status: TODO
- Owner: Architect/Planner (this file) — slices to Implementer
- Claimed By: —
- Claimed At: —
- Source: orchestrating collaborator (Bartosz), 2026-07-29: *"begin from an
  apo structure and end up predicting a pocket that is detected in the holo
  form"* and *"undisputably find the pocket in the holo form."*
- Priority: **P0 — this is the submission's required deliverable.**
- **Revised 2026-07-29** after the conformational-search reframing (see §"What
  changed"). Numbering floor verified: max committed task in the repo is
  **TASK-0172**; 0173/0174/0175 are claimed by uncommitted work-in-flight, so
  0176+ is safe *conditional on those landing*. **Run a repo-wide collision
  grep before committing** — TASK-0172's own header documents two prior
  collision incidents and a revert.

## Why this exists — the loop is not closed at either end

The project has ~40 observables, 226 scored cells, and a falsification
apparatus better than the science it tests. It does **not** have a single
defensible statement of the form *"from 4OBE alone we predict pocket P, and P
is the pocket 6OIM shows."*

**Gap 1 — the answer key is disputable.** `labels.holo_pocket_mask` is a
single-cutoff ligand-contact set. Live, documented defects:

| Defect | Evidence |
|---|---|
| Cutoff on a moving slope — the residue set changes at **every** 0.5 Å step, both directions | [[TASK-0114]] |
| A named validation structure can lack the drug (6C1H: ADP/MG only) | [[TASK-0169]] |
| "Pocket" can overlap the active site — KRAS min Cα–Cα **3.75 Å** | [[TASK-0169]] |
| Pocket can be pre-formed, not cryptic — BCR_ABL1 RMSD ratio **0.49** | [[TASK-0120]]/[[TASK-0169]] |
| A contact set is not a cavity — fpocket beats every observable here on 2/3 targets (0.8348/0.8596) | [[TASK-0163]] |

→ [[TASK-0177]], hard-blocks everything.

**Gap 2 — the prediction is not a pocket.** `report.assemble_hit_list` returns
top-k residues by raw score with **no spatial deduplication** (verified
directly). Because every observable here is spatially smooth, five adjacent
residues in one groove are reported as five sites. `main` applies
`min_sep=8.0`; the research branch does not — the two branches emit different
deliverables from identical science. → [[TASK-0180]].

## What changed in this revision

Two findings from 2026-07-29 reshape the program's *forward* half. Neither
changes Gaps 1–2, which remain the critical path.

**(a) The register has been solving a category error.** A cryptic pocket is
*defined* by absence in apo. KRAS's Switch-II pocket does not exist in 4OBE.
So every static apo scorer here has been ranking residues on a structure
where the target feature is **not present**. That is a better explanation of
the program's results than any of the mechanism hypotheses tested to date,
and it is corroborated by the register's own data: BCR_ABL1's pocket *is*
pre-formed (RMSD ratio 0.49) and fpocket scores 0.8596 there.

Cryptic-pocket prediction is therefore a **conformational search** problem.
This is legal under §Constraint 3 — which forbids MD *trajectories as inputs*,
not conformational sampling; ENM equilibrium ensembles are closed-form
Gaussian draws with no integrator. Challenge reference **[1]** (Zheng 2023)
is literally *"Predicting allosteric sites using fast conformational sampling
as guided by coarse-grained normal modes."* The register has never run it.
→ [[TASK-0185]].

**(b) The naive quantum-advantage argument for that search fails, and the
measurement is worth keeping.** Pocket opening under ENM soft modes is *not*
rare (p = 0.24–0.69 for a +25% cleft-volume opening across 5–40 modes) —
soft modes *are* the opening motions. Even the conjunctive druggability
constraint gives joint p ≈ 0.0017–0.005, i.e. ~200–600 classical draws.
Nothing there for amplitude amplification. **The hardness is at the
side-chain layer** (rotamer packing: discrete, NP-hard), not the backbone
layer. [[TASK-0181]] is revised accordingly.

## Subtasks

| ID | Slice | Priority | Est. | Status |
|---|---|---|---|---|
| [[TASK-0177]] | Consensus holo ground truth — the undisputable answer key | **P0** | ~2 d | blocks all scoring |
| [[TASK-0180]] | Site-level prediction + the single end-to-end runner | **P0** | ~1 d | §5.2 deliverable |
| [[TASK-0182]] | Hardware realization + resource accounting | P1 | ~2 d | §4.2 / Constraint 2 |
| [[TASK-0178]] | Binding-response coupling: module + specificity + evaluation | P1 | ~2.5 d | new science |
| [[TASK-0181]] | Selection formulation — classical gate now, side-chain forward | P1 | ~2 d | Phase A only before freeze |
| [[TASK-0185]] | Conformational-search reformulation — forward-proposal spine | P1 | ~1 d | **writing only** |
| [[TASK-0183]] | PoC sprint plan | **P0** | ~1 d | Feasibility, 20% |
| [[TASK-0184]] | The Phase-1 submission | **P0** | — | the deliverable |

**TASK-0179 is retired** — its content (the coupling-specificity statistic and
its evaluation) is folded into [[TASK-0178]], which was split needlessly:
same owner, same outcome, and the module is meaningless without the
evaluation. Do not re-file 0179; leave the number unused to avoid a
third collision incident.

**Sequencing.** 0177 + 0180 are the deliverable and run in parallel. 0183 +
0184 are writing and start now, not after the science lands. 0178/0181/0185
are the forward half; if the 2026-08-07 freeze arrives first, ship the
deliverable and carry them as proposal content.

**Explicitly not in this program:** `HOLO_DIRECTION_MODULE.md` /
[[TASK-0015]] predicts the apo→holo deformation and feeds a deformed graph to
transport — a submission-path preprocessor. This program uses real
experimental holo as a *verification artifact only*. Same boundary
[[TASK-0175]] draws. Note that [[TASK-0185]] sits close to this line and must
state on which side it falls.

## Intent Contract

- Outcome: one command producing ranked *sites* from apo alone, a consensus
  holo pocket definition with stated resolution, and the scored verdict
  relating them.
- Why required, not assumed: neither end of the loop exists; §5's deliverables
  cannot be honestly claimed without both.
- In Scope: the eight subtasks above.
- Out Of Scope:
  - Changing existing observable numbers.
  - Retracting the negative result. **If the end-to-end run reproduces the
    program's negatives against a better label, that is a stronger negative.**
  - Tuning any threshold against the holo label.
- Constraints And Invariants:
  - Apo-only prediction, gate-enforced.
  - Consensus label frozen before any scoring run reads it.
  - Disagreement between criteria is reported as the label's resolution, never
    resolved by picking the variant that scores better.
- Planned Validation: [[TASK-0177]]'s convergence statistic is the program's
  own control — non-convergence on a target means *not verifiable*, which is
  itself a Phase-1 result.

## In Progress

None

## TODO

- [x] **Collision grep before commit** (0173–0175 in flight) — run 2026-07-31
      (Architect, this thread) across `main`/`bartosz`/`scaffold` and all
      remotes: **TASK-0173/0174/0175 do not exist anywhere** (no file, no
      commit, on any branch). No collision with 0176–0185. The "in flight"
      premise this file was written under appears stale or was never
      committed from wherever it originated — filing 0176–0185 as numbered
      is safe regardless, but if 0173–0175 surface later from another
      thread, resolve any resulting gap/duplicate through `claim.py
      reserve-next`, not by renumbering these files.
- [ ] Dispatch [[TASK-0177]] and [[TASK-0180]] in parallel.
- [ ] Start [[TASK-0183]] and [[TASK-0184]] **now** — they are not gated on science.
- [ ] Decide before 2026-08-07 which of 0178/0181/0185 ship vs. become proposal.
- [ ] Write the end-to-end statement per target into `RESULTS.md`, every clause
      filled or explicitly marked unavailable.

## Dependency

- [[TASK-0167.001]] (Done) — `plant.py`.
- [[TASK-0169]] (Done) — the discriminability audit this program answers.
- [[TASK-0114]], [[TASK-0163]], [[TASK-0120]] (Done) — the label defects.

## Open Questions

- If [[TASK-0177]] finds a mandatory target not verifiable by convergent
  criteria, is it still reported? **Yes** — all three are required. Report the
  score *and* the label's resolution.
- Does site-level output change existing AUC? No — additive. Stated so nobody
  "upgrades" the convention.

## Done

(not yet)
