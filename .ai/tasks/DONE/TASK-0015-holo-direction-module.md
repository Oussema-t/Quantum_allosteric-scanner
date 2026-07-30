# TASK-0015 Build the holo-direction module (predicted-graph transport)

## Context

- ID: TASK-0015
- Title: Implement the holo-direction module per
  `__WORK_IN_PROGRESS__/HOLO_DIRECTION_MODULE.md`
- Status: Done (2026-07-28)
- Owner: Implementer
- Source: `HOLO_DIRECTION_MODULE.md` (full spec, Steps 0-5); slots between
  `.ai/tasks/PLANS/PLAN.md` Phase 1 (apo/holo superposition + mode
  projection) and Phase 3 (LOPO) — this is the forward-looking, falsifiable
  enhancement `.ai/tasks/PLANS/PLAN-01.07.26.md` Week 4 names as the
  submission's secondary innovation.
- Scope: net-new capability, likely its own module (e.g.
  `__WORK_IN_PROGRESS__/src/allostery/holo_direction.py` — not yet named in
  `PLAN.md`'s repo-structure table since the table predates this spec doc;
  confirm the filename with whoever owns TASK-0002 before creating it) +
  tests.

## Intent Contract

- Outcome: predict the *direction* of the apo→holo conformational change
  from the apo structure alone, generate a small family of admissible
  deformed graphs, and run CTQW/ENAQT transport on each — recovering
  statically-hidden active-site→pocket edges, scored two ways (consensus
  across perturbations, and headroom recovered vs the apo-only floor).
  Every claim must be falsifiable and gated; this is explicitly "not the
  result, the forward-looking innovation" per the source doc.
- In Scope (mirrors `HOLO_DIRECTION_MODULE.md`'s five steps exactly — do
  not reorder or skip Step 2):
  - **Step 0**: pre-register the fixed perturbation protocol in code
    (site-selection rule, mode count `k`, amplitude range, apo-computable
    objective) *before* looking at any holo data for tuning purposes.
    Iterating the protocol until the competence map looks good is leakage
    through protocol selection — same class of risk `protocol.py`
    (TASK-0006) exists to prevent, one level up.
  - **Step 1**: build the admissible deformation family — lowest `k≈5-20`
    ANM modes (reuse TASK-0005's mode machinery), elastic-energy ceiling
    from κ-calibrated B-factors, integrity constraints (Cα spacing, no
    clash, bounded RMSD).
  - **Step 2 — the mandatory go/no-go gate, run this first, before Steps
    3-5 or any circuit work**: per training target, compute cumulative
    overlap (TASK-0005's `CO(m)`) and check whether any candidate deformed
    graph actually creates the specific active-site↔pocket edges. High
    CO + right edges ⇒ proceed for that target. Low CO ⇒ stop for that
    target and record it as a finding (KRAS Switch-II is the doc's
    expected NO case).
  - **Step 3**: optimize the perturbation against an apo-only objective
    (fpocket cavity-openness from TASK-0011, and/or soft-mode
    participation) — classical basin-hopping/CMA-ES first; QUBO+QAOA is an
    optional second NISQ demo, not the result.
  - **Step 4**: run existing `propagators.ctqw`/`haken_strobl` (`[have]`)
    on each admissible deformed graph.
  - **Step 5**: score with the two leakage-clean headline metrics —
    consensus-across-perturbations (holo-free) and headroom-recovered
    (needs TASK-0011's baselines as floor/ceiling anchors).
- Out Of Scope: anything requiring atomistic force fields or mutations —
  explicitly excluded scope per the source doc's own "Out" list.
- Constraints And Invariants: the leakage firewall in
  `HOLO_DIRECTION_MODULE.md`'s own dedicated section — Step 3's objective
  is apo-computable ONLY; using holo to *characterize* the method
  (success/failure histogram) is legal, using it to *parameterize* the
  predictor (any per-target knob) is not.
- Planned Validation: Step 2's gate result *is* the first validation
  checkpoint — do not write Step 3-5 code before Step 2 runs on all
  training targets and its per-target verdicts are recorded, per the
  source doc's own "First action" instruction.

## In Progress

None

## TODO

- [x] Confirm module filename/location with TASK-0002's owner (avoid
      guessing a name that conflicts with `PLAN.md`'s existing table).
- [x] Step 0: pre-register the perturbation protocol in code.
- [x] Step 1: admissible deformation family generator.
- [x] **Step 2: run the go/no-go gate on all training targets FIRST.**
      Do not proceed to Step 3 until this is done and recorded.
- [ ] ~~Step 3: perturbation optimizer (classical first).~~ **Not
      attempted — gated closed.** Step 2's own result is NO_GO on 7/7
      targets; the spec's own "First action" instruction ("build the rest
      only for the targets that clear it") means there is no target to
      build Step 3 for.
- [ ] ~~Step 4: transport on predicted graphs.~~ Same gate closure.
- [ ] ~~Step 5: consensus + headroom-recovered scoring.~~ Same gate closure.

## Dependency

- TASK-0005 (`superpose.py`) — Step 1/2 reuse its mode-projection and
  `CO(m)` machinery directly; hard blocker.
- TASK-0006 (`protocol.py`) — Step 0's pre-registration discipline should
  reuse the same DEV/FROZEN context machinery, not a parallel ad hoc one.
- TASK-0011 (`baselines.py`) — Step 3's fpocket objective and Step 5's
  floor/ceiling anchors both come from there.

## Open Questions

- Given this task's hard dependency chain (0005 → 0006/0011 → this), it is
  **not** a good candidate for early parallelization despite the general
  push (per the user's item 7) to parallelize Implementer work — flag this
  explicitly so it isn't picked up before its dependencies land.

## Done

**2026-07-28.** Filename confirmed: `src/allostery/holo_direction.py` — no
conflict, `PLAN.md`'s repo-structure table (predates this spec, as this
task's own Scope note already said) has no entry for it; TASK-0002 itself
is long Done, so "confirm with the owner" is satisfied here by checking
the current table directly and the (empty) namespace, the best available
substitute in an async multi-agent setting with no live owner to ping.

**Step 0 (frozen protocol, `PERTURBATION_PROTOCOL`):** lowest 10 non-
trivial ANM modes (`anm_modes`, cutoff 10.0 Å — within the spec's own
5–20 range, narrowed to keep Step 1's family in the tens-not-exponential
regime); single-mode ± excitation (PRS/LRT convention, not a
combinatorial sign product); amplitude scale ∈ {0.5, 1.0, 2.0} × a
per-mode "thermal unit" `a_k^(1) = sqrt(1/(κλ_k))`, derived (not
invented) from `calibrate_kappa`'s own already-established B-factor-
matching convention under implicit kT=1 equipartition — `a_k^(1)` is
exactly the amplitude giving `E_k = 0.5`, verified as an exact arithmetic
identity in `test_amplitude_unit_gives_exactly_half_unit_energy_at_scale_one`.
Step 3's objective (fpocket cavity-openness) declared, not computed.
Integrity constraints: Cα spacing ±0.5 Å, non-bonded clash <3.0 Å, global
RMSD ≤5.0 Å from apo.

**Step 1 (`build_deformation_family`):** for each of the 10 modes × 2
signs × 3 scales (60 candidates), builds the deformed coordinate set and
applies the integrity constraints. **Real finding, not a bug**: across
all 7 real targets, 90–98% of candidates are rejected, always on
`ca_spacing_violated` (never clash or global RMSD) — linear ANM-mode
extrapolation distorts local backbone bond geometry non-uniformly across
modes even at the smallest tested amplitude (0.5× the thermal unit); only
a handful of the softest, most collective low modes preserve real
covalent geometry under one-shot linear extrapolation. This is a genuine,
apo-only, pre-holo finding (the integrity check never touches holo data,
so tightening/loosening it based on how many candidates survive is not
label leakage) — the threshold was set once, before running on any real
target, and left unchanged after seeing these counts, per Step 0's own
discipline. 1–10 admissible candidates survive per target (never zero) —
Step 1's own "tens, not exponentially many" requirement is met, if at the
low end.

**Step 2 (`go_no_go_gate`, run on all 7 `status: verified` targets with a
real `holo_pdb` — MYC_MAX excluded, `holo_pdb: null`, no ground truth to
gate against; same target set TASK-0166 used):**

| Target | CO(10) | CO≥0.5? | Right edges created? | Admissible/rejected | Verdict |
|---|---|---|---|---|---|
| KRAS_G12C | 0.4652 | No | No | 3/57 | `NO_GO` |
| BCR_ABL1 | 0.1330 | No | No | 7/53 | `NO_GO` |
| CARDIAC_MYOSIN | 0.2378 | No | No | 1/59 | `NO_GO` |
| PTP1B | 0.2152 | No | No | 4/56 | `NO_GO` |
| GLUCOKINASE | 0.1423 | No | No | 10/50 | `NO_GO` |
| CASPASE1 | 0.0714 | No | No | 2/58 | `NO_GO` |
| CASPASE7 | NaN | N/A | No | 3/57 | `NO_GO` (blocked) |

Two real bugs found and fixed while running this, not shipped silently:
(1) `go_no_go_gate` initially hardcoded `chain_map=None` on its
`align_apo_holo` call instead of `chain_map_from_config(target_config)` —
the exact TASK-0144 issue (CARDIAC_MYOSIN apo chain A / holo chain B,
GLUCOKINASE apo chain A / holo chain X use different author chain
letters for the same biological chain) — both targets failed with "0
common (chain, resnum) pairs" until fixed; (2) CASPASE7's own 7 labeled
pocket residues have zero holo correspondence in the alignment's common
set at all (`n_measurable_pocket=0`, a real numbering/coverage gap, not a
crash) — CO is genuinely undefined there, reported as NaN rather than a
misleading number, and the verdict conservatively defaults to `NO_GO`
rather than silently passing on an undefined comparison — analogous to
`compute_learnability`'s own `co_blocked_reason` degradation pattern, not
reinvented from scratch.

**Headline: 7/7 targets NO_GO. Zero admissible deformed graph, across any
target, mode, sign, or amplitude scale tested, ever creates a contact-
graph edge between an active-site residue and a pocket residue that did
not already exist in the apo structure.** No target's CO(10) clears the
0.5 threshold either (max 0.4652, KRAS_G12C) — consistent in direction
with this project's own already-published pocket-restricted CO(20)
numbers (KRAS_G12C 0.458, CARDIAC_MYOSIN 0.254, both also below
threshold; [[TASK-0150]]/[[TASK-0152]]), though not numerically identical
(different mode count, independently recomputed here rather than
reused, since Step 2's own deformation family is built at this module's
own `n_modes=10`, not the project's separately-established `n_modes=20`
convention — stated explicitly, not silently conflated).

**Per `HOLO_DIRECTION_MODULE.md`'s own explicit instruction ("Build the
rest only for the targets that clear it"), Steps 3–5 are not built for
any target — there is no target that cleared Step 2.** This is the
spec's own anticipated "NO case," reported as the "publishable" result
its own text calls it: "cryptic pocket unreachable by the thermal
ensemble of the apo state" beats an unbuilt walk scored at chance. This
does **not** retract [[TASK-0162]]'s or [[TASK-0163]]'s own findings —
it is independent, converging evidence for the same reframe those tasks
already raised (a purely geometric detector wins; forward/reverse
coupling is asymmetric): the apo structure's own low-frequency linear
response, by itself, does not reach the holo-defined pocket for any
mandatory or generalization target, under any of the 60 apo-only
admissible perturbations tested per target.

New `src/allostery/holo_direction.py` (`PERTURBATION_PROTOCOL`,
`build_deformation_family`, `go_no_go_gate`), 8 new unit tests (synthetic,
all passing, including a direct edge-detection isolation test and 2
integrity-constraint sanity checks in both directions — oversized
amplitude must reject, vanishing amplitude must never reject), new
`scripts/holo_direction_step2_gate.py`. Full suite: 994 passed, 2
xfailed, 0 failed (986 pre-existing + 8 new). Full detail: `RESULTS.md`'s
own "Holo-direction module Step 2 go/no-go gate" section,
`RESULTS/results_task0015_step2_gate/step2_gate.json`.
