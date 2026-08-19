# WORKFLOW — the pipeline as shipped, one step at a time

**What this is.** The canonical, end-to-end account of what this project
actually does to attempt the challenge, in the order it does it, transcribed
from the code that runs (`scripts/run_challenge.py::run_target`, the
orchestrator every real per-target result in `RESULTS.md` traces back to) —
not from the original design notes, and not idealized. Written for
[[TASK-0224]], filed 2026-08-19 after the project's own register (~220 task
files, ~6,000-line result document) turned out to contain no single place
that states the pipeline itself.

**Why this document, not a flowchart.** The valuable part is not the shape of
the pipeline — it is **which step's assertion has actually failed**, because
every methodologically significant finding of the 2026-08 window is exactly
that: a named step, an assertion that should have held, and a task that found
it didn't. The table below is that list, with the failure traced to the
actual code and the current fix state — not just the task that found it.

**How to read the enforcement column.** Three states, used precisely:
- **Enforced** — the code raises, refuses, or hard-fails when the assertion
  is violated; a caller cannot silently get a wrong answer past this point.
- **Enforced downstream** — the assertion is not checked at this step, but a
  later step's own hard gate would catch most violations as a side effect.
  Named explicitly per step; do not assume this without a citation.
- **Documented / audited, not gated** — the assertion is checked by a
  separate script or one-off audit (cited), and/or stated in this document,
  but `run_challenge.py`'s own per-target run does not check it and will
  proceed regardless. This is the honest majority case for the later steps.

A document that reads as more rigorous than the code is worse than no
document — every "Enforced" claim below is a real citation into the file
that raises, not an inference.

---

## The pipeline

### Step 1 — Resolve the apo/holo pair

- **What it does.** `run_target` calls `_load_apo_holo`
  (`scripts/run_challenge.py:159`), which fetches and cleans both structures
  (`clean.clean_from_config`, role `"apo"`/`"holo"`) and attaches the holo
  structure's ligand groups and heavy-atom coordinates.
- **Assertion.** Both PDB entries are the same protein, and a chain letter
  shared by apo and holo actually denotes the same biological chain.
- **Enforced?** **Partially.** By default, apo/holo correspondence is
  assumed by **matching chain letter and residue number** — no check that the
  letters mean the same thing biologically. A per-target override exists
  (`targets.yaml`'s `apo_chains`/`holo_chains`, read by
  `superpose.chain_map_from_config`, TASK-0127/TASK-0144) but it is **opt-in**
  — a target without it gets no correspondence check beyond coincidence.
  `superpose.align_apo_holo` does raise (`ValueError`) if fewer than 3 common
  `(chain, resnum)` Cα pairs are found — a real, enforced floor, but coarse:
  it catches total numbering mismatches, not a plausible-looking wrong pairing
  that still clears 3 points.
- **Failure actually found.** GLUCOKINASE's apo structure (`1V4S`) has chain
  `A`, but `backend/systems.py` (the deployed web app, a separate codebase
  from this scientific pipeline) configured it as chain `X` — silently
  returned `None` from every fetch until caught ([[TASK-0219]]). GLUR2's holo
  structure uses chain `B` where its apo uses chain `A` ([[TASK-0216]]).
  PTP1B was pre-registered as PDB pair `8QYP`/`8QYR` in an earlier document
  when the pipeline's own config has always used `1SUG`/`1T49` — a
  documentation/config drift, not a code bug, caught the same audit pass.
- **Task:** [[TASK-0219]], [[TASK-0216]].

### Step 2 — Assert the apo is genuinely unliganded at the site

- **What it does.** Nothing, inside `run_target` itself.
- **Assertion.** No non-buffer HETATM sits within the pocket-contact cutoff
  of the labelled site in the apo structure — i.e., the "closed" state is
  actually closed.
- **Enforced?** **Documented / audited, not gated.** No function in
  `run_challenge.py`'s call path checks this. It is checked by a dedicated,
  separately-run audit (`scripts/task0209_instance_verification.py`,
  [[TASK-0209]]) against the register's targets, not automatically for every
  pipeline run.
- **Failure actually found.** BCR-ABL1's apo (`1OPL`) has `MYR` (myristic
  acid) 3.47 Å from the pocket — the endogenous myristoyl-pocket ligand that
  holds ABL1's own autoinhibited pocket open. GLUCOKINASE's apo (`1V4S`) has
  `MRK` 2.45 Å from the pocket, same shape, previously unexplained. Both hold
  the nominal "apo" pocket open, invalidating any apo→holo contrast measured
  on them.
- **Task:** [[TASK-0209]].

### Step 3 — Assert the pair actually expresses the closed→open contrast

- **What it does.** Nothing, inside `run_target` itself.
- **Assertion.** The apo structure scores *closed* and the holo structure
  scores *open* on an independent druggability measure (fpocket) — i.e., the
  benchmark instance is a real cryptic-pocket case, not vacuously easy or
  vacuously impossible.
- **Enforced?** **Documented / audited, not gated.** Same audit as Step 2
  ([[TASK-0209]]); `run_challenge.py` will run — and did run, historically —
  on invalid pairs without complaint.
- **Failure actually found.** Of 7 targets with a real small-molecule
  `drug_ligand`, only **2 validate** (KRAS_G12C, PTP1B). 5 fail, in three
  distinct modes: apo scores *more* druggable than holo (BCR-ABL1,
  GLUCOKINASE — Step 2's ligand-occupancy explanation), an apo that is
  intrinsically open with no occupying ligand found (CASPASE1), or the holo
  positive control itself misses (CARDIAC_MYOSIN, CASPASE7). **2 of the 3
  mandatory targets are invalid** by this test.
- **Task:** [[TASK-0209]].

### Step 4 — Assert index spaces correspond before crossing between them

- **What it does.** `build_labels` (`scripts/run_challenge.py:350`) computes
  the pocket and active-site labels from apo/holo heavy-atom contacts.
- **Assertion.** An index computed in the holo structure's residue array is
  never used to index the apo structure's array without translation — apo and
  holo do not always share numbering or length.
- **Enforced?** **Enforced**, as of [[TASK-0217.001]] (2026-08-14). Before
  that date this was a live bug: holo-space heavy-atom contact indices were
  written directly into an apo-sized mask in `build_labels` and 3 other call
  sites, silently correct only when apo and holo happened to share numbering.
  The fix (`heavy_atom_resnames`/`coords_resnames` correspondence, reusing the
  Needleman-Wunsch path `holo_pocket_mask` already had) is wired into
  `build_labels`'s own default call path — this is a genuine landed fix, not
  an opt-in flag a caller must remember to pass.
- **Failure actually found.** **10 of 13 real targets exposed**, including 2
  of the 3 mandatory ones. Confirmed wrong with a real number before fixing:
  KRAS_G12C's own "active site" residue was reported as 12 when it should
  have been 11. Consequence beyond the seed: the pocket ground-truth label
  itself shifted on the same 10 targets (KRAS_G12C's pocket: 18→17 residues),
  and a previously-pinned golden AUC moved (0.7910→0.8210, `test_fpocket_pin.py`,
  marked `xfail` with a dated reason rather than silently re-pinned).
- **Task:** [[TASK-0217.001]].

### Step 5 — Derive the active site

- **What it does.** `labels.functional_indices` (called inside
  `build_labels`) resolves the seed residues that every propagation and every
  scored quantity is computed from.
- **Assertion.** `func_ligand` in `targets.yaml` names a real chem-comp code
  present in the holo structure, and the resolved seed has real biological
  provenance — not a topological stand-in.
- **Enforced?** **Enforced as a loud warning, tiered.** `functional_indices`
  has three tiers: (1) a real `func_ligand` chem-comp match; (2) a curated
  `active_site_uniprot` field ([[TASK-0217.003]], added for targets with no
  functional ligand in the deposited structure at all); (3) a fallback to the
  top-5 highest-degree residues, which **raises a `RuntimeWarning`** naming
  the fallback explicitly (not a silent default) — but does not raise an
  exception, so a caller that does not inspect warnings gets a result anyway.
- **Failure actually found.** **9 of 13 targets** were silently seeded at
  top-degree fallback before the warning existed, including PTP1B — the
  register's one target with a claimed corrected-null-surviving positive.
  6 of the 9 were fixable with a real `func_ligand` code; the remaining 3
  (PTP1B, CASPASE1, CASPASE7) have no functional ligand in the deposited
  structure at all and now resolve via the UniProt tier instead. Rescoring
  PTP1B's `dcc_low` under the corrected seed **reversed its own result**: AUC
  1.000→0.598, p 0.00275→0.567 — it no longer clears the significance bar.
  **The register's one surviving positive did not survive its own seed
  correction.**
- **Task:** [[TASK-0216]], [[TASK-0217.003]].

### Step 6 — Build the contact graph

- **What it does.** Every operator in `analysis._operator_registry` builds
  its own contact graph from `hamiltonians.contact_matrix`/`build_H_new` at
  the target's configured `enm_cutoff` (`targets.yaml`, default 10.0 Å,
  overridable per target — KRAS_G12C uses 8.0 Å).
- **Assertion.** The cutoff is stated (not silently hardcoded per call site),
  and a disconnected contact graph is caught rather than silently propagated
  on a graph that doesn't represent one connected structure.
- **Enforced? Enforced, but not where a reader would expect.**
  `clean._assert_connected` only **warns** on a disconnected Cα graph — a
  deliberate choice ([[TASK-0038]], resolved 2026-08-14): a single bad chain
  break should not abort a `clean()` run before quality metadata can be
  inspected. The real hard gate is downstream and independent of `clean()`:
  `superpose.py`'s ANM rigid-body-nullspace check **raises** when the operator
  it builds is disconnected (TASK-0005's original regression test). A caller
  that only calls `clean()` and never reaches the ANM step would not be
  stopped by anything.
- **Failure actually found.** Cutoff sensitivity itself was swept
  ([[TASK-0067]]/[[TASK-0113]]) rather than picked once and trusted; no
  disconnection incident is on record for a scored target, but the two-gate
  structure above (warn early, raise late) was itself only made honest in the
  module's own docstring on 2026-08-14 — until then the docstring claimed
  disconnection "is an error" when the code only warned.
- **Task:** [[TASK-0038]], [[TASK-0067]].

### Step 7 — Propagate

- **What it does.** The winning operator's eigendecomposition feeds
  `propagators.time_averaged_ctqw_converged` (`scripts/run_challenge.py:446`),
  scoring the seed's steady-state occupation as an **incoherent statistical
  mixture** across every active-site residue (`coherent=False`, the one
  declared seed convention for every scored call site in this codebase,
  TASK-0118 / `INV-0006`).
- **Assertion.** The reported occupation is the converged (infinite-time)
  limit, not a truncated finite-time snapshot that happens to look plausible.
- **Enforced.** `run_challenge.py` calls the exact closed-form converged
  function directly — there is no `T_MAX`/`N_STEPS` truncation left in this
  call path to accidentally under-run. (`SELECTION_GSR_ABLATION_T`/`_N_STEPS`
  still exist in this file, but are used only for candidate *selection*'s own
  blind heuristic and the ablation diagnostic — both a declared, different,
  still-finite-by-design use, not the headline score.)
- **Failure actually found.** The shipped truncated clock (`T_MAX=15.0`,
  `N_STEPS=500`) was, measured directly against the true converged limit on
  all 5 touched targets, **83,834×–420,682× too short** to have actually
  converged ([[TASK-0159]]; the closed form itself was separately validated
  by brute-force integration to true convergence — 877K–4.6M steps, up to
  12.3 wall-hours for CARDIAC_MYOSIN — agreeing to 1e-6/1e-7, floating-point
  noise, not an approximation gap). Using the truncated clock flipped a real
  target's own verdict: PTP1B's converged AUC (0.4859) disagrees with an
  older, pre-convergence-fix table's own row (0.2050), flipping
  `BEATS_CHANCE_NOT_FLOOR` → `NO_SIGNAL_IN_APO` — this is not a theoretical
  concern, it changed a published number.
- **Task:** [[TASK-0159]].

### Step 8 — Score

- **What it does. ** `diagnostics.classify_failure`, called inside
  `run_frozen_verdict`, classifies the scored result before it is accepted at
  face value.
- **Assertion.** A result must beat the **strongest trivial proximity
  baseline available** — not merely chance — before it is treated as
  structure the method actually found. `floor_scores` is the max AUC across
  `degree_centrality`, `euclid_from_seed_centroid`, and `hop_from_seed`
  (`scripts/run_challenge.py:384`), matching SEAM-0005 widened by
  [[TASK-0094]].
- **Enforced.** `classify_failure` is a total function over six categories
  (`OPERATOR_DEGENERATE`, `LABEL_SUSPECT`, `INSUFFICIENT_RESOLUTION`,
  `NO_SIGNAL_IN_APO`, `BEATS_CHANCE_NOT_FLOOR`, `NO_FAILURE_DETECTED`),
  checked in that order, stamped into every result's `_diagnosis` field. It
  does not abort the run — a `BEATS_CHANCE_NOT_FLOOR` result is reported
  honestly, not hidden — but it is never silently skipped: `floor_scores`
  is passed on every real call site in `run_challenge.py`.
- **Failure actually found.** [[TASK-0094]]'s review found `degree_centrality`
  alone was an insufficient floor — it measures graph degree, not proximity
  to the propagation seed, the confound that actually dominates raw scores.
  A widened, later, independent audit ([[TASK-0217.004]]) flagged (as a
  **suspicion**, not a confirmed defect) that across the 3 targets with a
  published 3-leg breakdown, `degree_centrality` never actually binds the
  `max()` in practice — `euclid`/`hop` alternate as the real floor.
- **Task:** [[TASK-0094]], [[TASK-0217.004]].

### Step 9 — Test significance

- **What it does.** Two distinct things live under this name, and conflating
  them is itself a documented risk this project has hit:
  1. **GATE-B4** (`diagnostics.detect_permutation_leak`, wired into
     `run_frozen_verdict` via `leak_check_n_perm`): checks that
     `select_frozen_config`'s blind candidate-selection heuristic is not
     itself tracking shuffled labels. **Enforced, hard.** `run_challenge.py`
     raises (`scripts/run_challenge.py:432`) if the leak check fires — a
     positive detection here is a hard failure of the run, not a warning
     ([[TASK-0218]]).
  2. **Corrected-null significance testing** — the specific claim that a
     scored positive (e.g. PTP1B's `dcc_low`) beats a null distribution
     matched to the label's own geometry (`nulls.compact_patch_matched`/
     `graph_walk_patch_matched`). **Documented / audited, not gated.**
     `run_challenge.py` does not construct or check any such null for any
     target — this layer exists only in separate, per-claim analysis
     scripts, applied to specific results that a thread chose to test
     further, not automatically for every scored quantity in a run.
- **Failure actually found (the second kind).** Three successive null
  constructions were needed before the null actually matched the label's own
  geometry ([[TASK-0158]] → [[TASK-0190]] → [[TASK-0201]]) — each earlier
  attempt was itself a plausible-looking null that turned out to under- or
  over-state significance. This is the single clearest illustration in the
  register of why "documented, not gated" is a real risk category and not a
  formality: the null construction was wrong three times *while being
  actively used to certify a claim*, and each wrongness was silent until
  specifically re-examined.
- **Task:** [[TASK-0218]] (GATE-B4), [[TASK-0158]]/[[TASK-0190]]/[[TASK-0201]]
  (null construction).

### Step 10 — Interpret

- **What it does.** Every pre-registered pass/fail criterion in the register
  (not only the main pipeline's own `_diagnosis`) is meant to be able to
  express every one of its own possible outcomes, and every conjunctive
  ("AND") criterion is meant to have every leg actually able to bind.
- **Assertion.** A criterion's positive outcome must be reachable by the
  measurement as constructed; a compound criterion's reported verdict must
  not be silently decided by only one of its legs; a positive control must
  exist to confirm the criterion *can* fire.
- **Enforced?** **Audited, not gated at construction time** — there is no
  code-level check that a newly-written criterion satisfies this; it is
  caught by review. [[TASK-0217.002]] specifically audited this: **13
  pre-registered criteria** (every "Pre-Registered" section header,
  2026-08-02 through 2026-08-13), finding 3 known reachability defects + 1
  known missing control (all already fixed by the time of that audit) plus
  **1 new instance**, and 8 clean. A convention amendment (state the positive
  control's expected result; demonstrate each verdict is reachable) landed in
  `.ai/reference/INTENT_CONTRACT_TEMPLATE.md`'s own Planned Validation section
  as a result — this is now a documented pre-registration requirement, not
  yet a code-enforced one.
- **Failure actually found.**
  - [[TASK-0204]] D1: a criterion's gate (`opt_rate > (1.0 if greedy_hit else
    0.0)`) demanded a value the statistic could not attain — unfalsifiable in
    the positive direction on any greedy-hit target.
  - [[TASK-0204]] D2: no positive control existed at all — only the apo
    structure was ever scored, where the target property is closed by
    definition.
  - [[TASK-0208]] V1: a frustration statistic's "positive" signature required
    a negative energy gap that a rigid rotamer transplant structurally could
    not produce — every measured value was clash energy, not coupling.
  - [[TASK-0189]]: a related reachability defect in a zero-plant Bonferroni
    gate.
  - New (TASK-0217.002): `scripts/fpocket_conditional_analysis.py`'s `ALPHA`
    gate is reachable today but sits at only ~60% of its own permutation
    floor and shrinks as the target set grows — fixed pre-emptively
    (`assert_gate_reachable`) before it could silently fire.
- **Task:** [[TASK-0217.002]] (the audit), [[TASK-0204]], [[TASK-0208]],
  [[TASK-0189]] (the instances).

---

## What this pipeline cannot do

Stated plainly, not left implicit:

- **Apo-only input.** The scored propagation always runs on a single apo
  conformation. No ensemble, no trajectory is fed to the operator that
  produces the reported occupation (a legal, closed-form ensemble *is* used
  elsewhere, e.g. [[TASK-0187]]/[[TASK-0211]], but never as the input to the
  headline scored quantity).
- **Cα / 8–10 Å resolution.** Every operator in `analysis._operator_registry`
  is built from Cα coordinates at a fixed contact cutoff per target. No
  side-chain-resolved contact is a pipeline input (side-chain rotamer
  questions are answered by an entirely separate code path, e.g.
  [[TASK-0204]]/[[TASK-0208]], never fed back into the scored occupation).
- **Single-conformer assumption.** Alt-loc handling keeps one conformer per
  residue (`clean.py`); no partial-occupancy blending.
- **No automatic instance validity check.** As Steps 2–3 state explicitly,
  `run_challenge.py` will run — and score, and report a diagnosis — on a
  target pair that is not a genuine closed→open cryptic-pocket case. Only 2
  of 7 real-drug-ligand targets are validated instances today
  ([[TASK-0209]]); the pipeline itself has no code path that would refuse to
  run on one of the other 5.
- **The flagship target is a documented outlier, not a typical case.**
  KRAS_G12C's own apo structure (`4OBE`) is wild-type KRAS, not the G12C
  mutant — kept unchanged because every historical number in the register is
  conditioned on it, but the register's own apo-structure sensitivity sweep
  ([[TASK-0155]], propagated by [[TASK-0192]]) found it is **a lucky-draw
  outlier among 10 independently RCSB-verified true-G12C structures**: median
  AUC **0.482** (below the 0.5 chance line) and P@5 = **0.000 on all ten**. A
  reader should not generalize from KRAS_G12C's own headline number to "this
  method works on KRAS."
- **No automated significance testing by default.** As Step 9 states, the
  corrected-null significance layer is applied per-claim, by a human/thread
  choosing to run it, not automatically for every target/operator pair a run
  produces.

## Walkthrough — KRAS_G12C through the pipeline

Config resolves (`--dry-run` confirms): `apo_pdb: 4OBE`, `holo_pdb: 6OIM`,
chain `A`, `enm_cutoff: 8.0`, `pocket_contact_cutoff: 4.5`,
`drug_ligand: MOV`, `func_ligand: ["GDP"]`. N = 169 residues.

1. **Resolve pair** — no `apo_chains`/`holo_chains` override is set (both
   structures already share chain `A`); `align_apo_holo` finds well more than
   3 common Cα pairs, no raise.
2–3. **Not checked by this run.** [[TASK-0209]]'s separate audit found
   KRAS_G12C *is* one of the 2 validated instances (apo drug-score 0.001 →
   holo 0.886) — a case where Steps 2–3 would have passed had they run.
4. **Index correspondence** — `build_labels` uses the post-[[TASK-0217.001]]
   translation path; apo and holo share numbering closely enough here that
   this mattered less than on the 10 exposed targets, but the same code path
   runs regardless.
5. **Active site** — `func_ligand: ["GDP"]` resolves via tier 1 (real
   chem-comp match), not a fallback; no warning fires. Post-fix, the correct
   residue (11, not the pre-fix 12) is what seeds the propagation.
6. **Contact graph** — built at 8.0 Å; `_assert_connected` finds one
   component (169 residues, no reported chain break); the real gate
   (`superpose.py`'s ANM nullspace check) never fires because there is
   nothing disconnected to catch.
7. **Propagate** — `time_averaged_ctqw_converged`, incoherent mixture over
   the active-site array, exact closed form (no truncated clock in this call
   path).
8. **Score** — `classify_failure` runs against the max of the 3 floor
   baselines; KRAS_G12C's own headline number is discussed at length
   elsewhere in the register (see the apo-structure sensitivity sweep
   section, `RESULTS.md`) — not repeated here since this walkthrough is about
   which code path runs, not re-deriving the number.
9. **Significance** — GATE-B4 runs at `n_perm=30` (N=169 ≤ 250,
   `_leak_check_n_perm_for`); no corrected-null significance layer runs
   automatically.
10. **Interpret** — the compound-criterion audit ([[TASK-0217.002]]) does not
    apply to this per-target run directly; it applies to the register's
    separately-constructed criteria (rotamer packing, apo-holo decomposition,
    etc.), several of which also use KRAS_G12C as one of their targets.

Every step above traces to a real function call in `run_target`, in order,
for this one target — the validation this document's own Planned Validation
section asked for.

## For the submission (§4.3 item 2)

The compressed form: apo/holo structures are fetched and validated for
correspondence (Steps 1, 4); the active site is resolved from real ligand or
curated provenance (Step 5); a contact-graph propagator is built and its
occupation computed at the converged (infinite-time) limit, seeded
incoherently from the full active site (Steps 6–7); the result is classified
against the strongest trivial proximity baseline before being accepted as
signal (Step 8); a hard leak check guards the candidate-selection step, and a
separate, geometry-matched-null significance layer is applied to specific
claims (Step 9); every pre-registered pass/fail criterion is audited for
reachability before its verdict is trusted (Step 10). What the pipeline does
**not** do by default: validate that a given apo/holo pair is a genuine
cryptic-pocket instance before scoring it (Steps 2–3), or run significance
testing automatically for every result. Both are named, audited gaps, not
silent ones.
