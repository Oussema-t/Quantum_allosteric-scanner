# TASK-0093 Reconcile KRAS_G12C's real end-to-end AUC (0.779) against the previously-documented near-chance finding (~0.51-0.53)

## Context

- ID: TASK-0093
- Title: Determine which real methodology difference — cutoff (8.0 Å vs
  10.0 Å) or pocket-label definition (assembled/excluded vs raw
  ligand-contact) — explains why `TASK-0079.005`'s real KRAS_G12C run
  scored far above this repo's own previously-documented, tested result
  for the same target.
- Status: TODO
- Owner: Implementer
- Source: [[TASK-0079.005]]'s first real end-to-end run (2026-07-12).
  This is a genuine discrepancy between two honest, real, network-backed
  numbers for the *same* target — not a hypothesis, a measured fact that
  needs an explanation before either number is trusted as "the" KRAS_G12C
  result.

### The discrepancy (the load-bearing fact this task exists to resolve)

| | Existing, documented, tested | New, real run (TASK-0079.005) |
|---|---|---|
| `AUC_apo_Hnew_default` | ~0.51-0.53 ("near chance even with the answer key," asserted `0.3 < AUC < 0.7` in `test_analysis.py::test_kras_g12c_real_target_near_chance_and_flat_dephasing`) | **0.779** (outside that asserted band entirely) |
| `enm_cutoff` | 10.0 Å (that test's own default) | 8.0 Å (`targets.yaml`'s configured `enm_cutoff` for KRAS_G12C, used by `.004`'s orchestrator) |
| Pocket label | raw `holo_pocket_mask(apo, holo, "MOV", cutoff=4.5)`, pre-exclusion | `labels.build_labels(...)`'s assembled `.pocket` — `pocket_raw & ~active_site & ~terminal` (TASK-0070, post-dates the older test) |
| Propagation source | a specific aligned/mapped GDP-contact subset (`functional_indices` on holo, mapped through `align_apo_holo` to apo) | `np.where(labels.active_site)[0]` — `functional_indices` computed **directly on apo**, via `build_labels`, not cross-mapped from holo |

Independent corroborating evidence the new number isn't a fluke or a
leak: `_diagnosis: NO_FAILURE_DETECTED` (cleared both the chance check
*and* the degree-centrality floor via `floor_scores`), and a real,
non-trivial cross-check — 3 of the top-5 hit-list resnums (34, 11, 59)
land directly in `backend/systems.py`'s independently-sourced
`pocket_full[4.5]` reference set (`test_labels.py`'s own pinned KRAS
reference, 21 residues total, ~12% baseline prevalence). The new result
does not look like a leak; it looks like a real, different, better
answer under different conditions — which is exactly why it needs
explaining, not dismissing in either direction.

## Intent Contract

- Outcome: an evidence-backed attribution of the ~0.25 AUC gap to one or
  more of the three identified variables (cutoff, pocket-label
  definition, source definition), each tested independently by holding
  the other two fixed — not a guess, and not "probably the labels."
- In Scope:
  - **Isolate cutoff**: rerun the real KRAS_G12C pipeline at cutoff=10.0
    (matching the old test) with everything else identical to
    TASK-0079.005's real run (assembled `build_labels` pocket,
    apo-derived `active_site` source). If AUC drops back toward ~0.5,
    cutoff is the dominant variable.
  - **Isolate pocket-label definition**: at whichever cutoff isolates
    cleanly, score against the *raw* `holo_pocket_mask` output (like the
    old test) instead of `build_labels`'s assembled `.pocket`, everything
    else held fixed. If AUC drops, the exclusion-assembly is the
    dominant variable (a smaller, cleaner label set could legitimately
    score differently than a noisier raw one — not a bug, but worth
    knowing which one the submission should report).
  - **Isolate source definition**: compare `active_site`-derived source
    (apo-native `functional_indices`) against the old test's
    holo-aligned-then-mapped source, everything else held fixed.
  - Report a small factorial table (which combination gives which AUC),
    not just a single "found it" claim — per this session's own
    Invariance-Protocol-adjacent discipline: report the actual spread
    across the tested combinations, don't collapse to one number
    prematurely.
- Out Of Scope: deciding which methodology is "correct" for the
  submission — that is a downstream decision for whoever owns the
  competence-map/artifact-contract work ([[TASK-0082]]/[[TASK-0083]]),
  informed by this task's factorial evidence, not decided here. Also out
  of scope: re-litigating TASK-0070's exclusion-assembly design itself
  (already reviewed, Done) — this task checks its *AUC consequence* on
  this one target, not its correctness as a leakage boundary.
- Constraints And Invariants: every variant tested must still go through
  the real `frozen_context`/`run_frozen_verdict` gate — this is a
  methodology-sensitivity investigation, not license to bypass the
  leakage firewall for convenience.
- Planned Validation: the factorial table itself, plus a one-paragraph
  attribution statement in this task's Done section.

## Dependency

- [[TASK-0079.005]] — source of the discrepancy.
- [[TASK-0070]] (`build_labels`'s exclusion assembly) and the older
  `test_kras_g12c_real_target_near_chance_and_flat_dephasing`
  (`test_analysis.py`) — the two real, tested reference points being
  reconciled.

## Open Questions

- None yet — scope is bounded to attributing one already-measured gap on
  one target.

## Done

(not yet)
