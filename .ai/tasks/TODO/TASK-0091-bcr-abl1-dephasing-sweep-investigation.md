# TASK-0091 BCR_ABL1 dephasing-sweep investigation — does calibrated decoherence recover CTQW's lost signal?

## Context

- ID: TASK-0091
- Title: Run `analysis.dephasing_sweep` (calibrated, not blind) on BCR_ABL1's
  real winning `H_new` operator to determine whether CTQW's near-chance
  performance is a coherence problem (fixable by calibrated dephasing) or
  a propagator-independent ceiling.
- Status: TODO
- Owner: Implementer
- Source: [[TASK-0079.005]]'s first real end-to-end run (2026-07-12).
  This task **is** the load-bearing record of the reasoning behind this
  task — read it in full before starting, don't re-derive from a
  paraphrase.

### The finding this task exists to investigate

BCR_ABL1's real, network-backed run (`__WORK_IN_PROGRESS__/results/BCR_ABL1/`,
winning apo `H_new` at `enm_cutoff=8.0`, `NO_SIGNAL_IN_APO` diagnosis)
produced:

| Quantity | Value |
|---|---|
| `AUC_apo_Hnew_default` (CTQW, H_new) | 0.525 (chance) |
| `AUC_apo_H10_baseline` (CTQW, H10) | 0.558 (noise-level vs. H_new, per report's own `DAUC=-0.033` verdict) |
| `AUC_ctqw_mean` (H_new, CTQW) | 0.525 |
| `AUC_heat_mean` (H_new, classical heat kernel, **same operator**) | **0.731** |

The report's own line-2 logic already flags this (`DAUC = -0.206`,
"CTQW does NOT add biological information beyond the operator") — but
that framing conflates two axes that must be kept separate:

1. **Operator choice** (H_new vs H10) — both scored via CTQW, gap is
   noise-level (`-0.033`). Not what this task investigates.
2. **Propagator choice on the same operator** (CTQW vs heat) — gap is
   large (`0.206`) and is what this task investigates.

### Why this is not automatically "CTQW is just worse" (the reasoning that must survive into any review of this task)

This repo already has a **directly relevant, established result** that
must not be conflated with this one: `test_kras_g12c_dephasing_flat_
survives_kappa_calibration` (`test_analysis.py`) found that for
KRAS_G12C, AUC is **flat** across a *calibrated* dephasing sweep
(`gamma` derived from `superpose.calibrate_kappa`/`mode_energetics`'s
`relaxation_time`, not a blind range) — i.e. "coherence adds ~nothing"
for that target. It would be a mistake to assume this generalizes to
BCR_ABL1 and conclude the CTQW/heat gap here is uninteresting or already
explained by that finding, because:

- KRAS's flat-sweep result is a comparison of **CTQW vs. progressively
  dephased CTQW** (`propagators.haken_strobl`, `gamma: 0 -> large`).
- BCR_ABL1's gap here is a comparison of **CTQW vs. `propagators.heat`**
  — a *different* classical diffusion process (`exp(-Ht)`, monotonic
  relaxation to the graph's stationary distribution), not proven
  equivalent to the `gamma -> large` limit of Haken-Strobl dephasing
  anywhere in this codebase.
- Therefore: KRAS's "coherence adds ~nothing" does **not** predict what
  a calibrated dephasing sweep would show for BCR_ABL1. It is an open,
  target-specific, propagator-specific question, not a settled one.

This distinction is the entire point of this task — collapsing it would
silently discard a real chance to test PLAN.md's own ENAQT hypothesis
("coherent walks localize on disordered graphs; calibrated dephasing
reopens blocked paths," Plenio-Huelga 2008 / Rebentrost 2009,
`HOLO_DIRECTION_MODULE.md` Step 4) on a target where it might actually
matter, rather than the one target (KRAS) where it already didn't.

## Intent Contract

- Outcome: a real, calibrated `dephasing_sweep` run on BCR_ABL1's actual
  winning `H_new` (the same one `TASK-0079.005`'s run selected — rebuild
  it via `hamiltonians.build_H_new(apo.coords, apo.bfactors, cutoff=8.0)`
  against a freshly re-fetched 1OPL, not a cached/guessed operator), and
  an explicit answer to: does AUC rise from ~0.525 toward ~0.731 as
  `gamma` increases from 0 through the calibrated scale and plateau
  (**adapt**: calibrated dephasing recovers the signal, a genuine ENAQT
  finding worth pursuing further), or does it stay flat near 0.525
  regardless of `gamma` (**abandon for this target**: coherence isn't
  the lever, matches KRAS's own flat-sweep precedent after all)?
- In Scope:
  - Reuse `test_kras_g12c_dephasing_flat_survives_kappa_calibration`'s
    exact calibration recipe, not a blind omega range: `calibrate_kappa`
    → `anm_modes` → `mode_energetics`'s `relaxation_time` → `gamma_scale
    = 1 / mean(relaxation_time[:20])` → sweep `{0.5, 1, 2} * gamma_scale`
    at minimum (widen if the result is ambiguous at just 3 points).
  - Use BCR_ABL1's real apo (1OPL, chain A) and the same active-site
    source / pocket label `TASK-0079.005`'s run used (`labels.build_labels`,
    `enm_cutoff=8.0`, `pocket_contact_cutoff=4.5` — read
    `config/targets.yaml`'s `BCR_ABL1` entry directly, don't hardcode
    from memory).
  - Also run `gamma=0` as an explicit sanity point and confirm it
    reproduces `AUC_ctqw_mean=0.525` (within the sweep's own `rtol`/`atol`
    tolerance) — this pins the new sweep to the real run it's
    investigating, not a freshly-independent computation that might
    silently diverge (different `t_max`, different source, etc.).
- Out Of Scope: implementing any actual "adaptation" (e.g. wiring a
  calibrated-dephasing propagator into `run_frozen_verdict`/`.004`'s
  orchestrator as the new default) — this task answers the diagnostic
  question only; if the answer is "adapt," the adaptation itself is a
  follow-up task, filed after this one lands, not guessed at here.
- Constraints And Invariants: this is a real-network, real-compute
  investigation (matches TASK-0079.005's own "not mockable" precedent) —
  report the actual numbers, not a synthetic stand-in.
- Planned Validation: the sweep's own output table (`gamma`, `AUC`) is
  the validation; state the adapt-vs-abandon conclusion explicitly in
  this task's Done section, per this whole session's established
  "state a conclusion, don't leave it implicit" convention.

## Dependency

- [[TASK-0079.005]] — the real run and the finding this task investigates.
- `analysis.dephasing_sweep` (TASK-0008, Done), `superpose.calibrate_kappa`/
  `mode_energetics` (TASK-0005, Done) — both already validated on
  KRAS_G12C, reused here, not reimplemented.

## Open Questions

- None yet — scope is bounded to one calibrated sweep on one already-
  identified target/operator.

## Done

(not yet)
