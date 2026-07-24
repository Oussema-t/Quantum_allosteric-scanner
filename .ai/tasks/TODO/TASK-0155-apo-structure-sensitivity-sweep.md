# TASK-0155 Apo-structure sensitivity sweep (is any result a lucky structural draw?)

## Context

- ID: TASK-0155
- Title: for a target with many deposited apo structures (KRAS G12C
  first), run the existing scoring pipeline across SEVERAL apo inputs of
  the same protein and report the DISTRIBUTION of AUC / P@5 / floor-clear,
  rather than the single point estimate from one hardcoded structure.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: raised by the orchestrating collaborator (Oussama), 2026-07,
  observing that `config/targets.yaml` hardcodes exactly one apo/holo
  pair per target and nothing sweeps the input structure.
- Priority: **P1 — high information, low cost. This stress-tests the one
  marginal surviving result (KRAS) directly.**

## Why this matters — the project already proved the point accidentally

[[TASK-0124]] replaced cardiac myosin's apo from 5TBY (20 A cryo-EM) with
a real X-ray structure (8QYP) and the AUC collapsed 0.79 -> 0.52 — the
target's only positive vanished. That was treated as a one-target data-
quality fix. The general lesson was not drawn: **every result in the
register is currently conditioned on a single, arbitrary structural
draw, and that sensitivity has never been measured.** The pipeline has
swept the ENM cutoff ([[TASK-0113]]), the pocket-contact cutoff
([[TASK-0114]]), the propagation time ([[TASK-0119]]), and the seed
convention — but never the input apo structure. KRAS is the ideal test:
it has many deposited apo structures AND it is the one target with a
marginal surviving signal (converged-limit point estimate clears floor,
CI-overlapping, ceiling p=0.045 uncorrected). A distribution of AUCs
across apo structures answers directly: is KRAS's result structure-robust,
or a lucky draw? Either answer is publishable.

## Intent Contract

- Outcome: a table of the existing scored observable's AUC / P@5 /
  floor-clear across >= 5 (target: 8-12) distinct apo structures of KRAS
  G12C, same holo ground truth (6OIM) and same pipeline, reported as a
  distribution (median, spread, fraction clearing floor) — plus a
  one-line verdict on structure-robustness.
- Why required, not assumed: TASK-0124 shows one swap can move AUC by
  ~0.27 and erase a headline; the sensitivity of the *surviving* result
  (KRAS) to this choice is unmeasured and is a liability a reviewer finds
  immediately.
- In Scope:
  - Assemble a list of valid KRAS G12C apo structures from RCSB — verify
    each on RCSB before use (correct protein, apo i.e. no orthosteric/
    allosteric ligand at the Switch-II site, resolvable catalytic
    domain). Candidate seeds to CHECK (do not assume valid): 4OBE
    (current), 4DSN, 3GFT, and other apo G12C/WT entries — the
    implementer verifies each on RCSB and states which were included/
    excluded and why. NOTE: `36OL`/`36OM`-style codes floated informally
    are almost certainly typos; verify every PDB ID on RCSB before use.
  - Run the existing `clean_from_config` -> `build_H_new` ->
    scored-observable pipeline unchanged per structure; only the apo
    input varies.
  - Handle NMR structures explicitly: they carry no crystallographic
    B-factors, on which V_B/V_T in `H_new` depend — either exclude them
    (stated) or document the degraded-operator handling. Do not silently
    feed zero/absent B-factors.
  - Report the AUC/P@5/floor-clear distribution + median + spread, with
    CIs per structure.
- Out Of Scope:
  - Changing the holo ground truth or the operator (this isolates the
    APO-structure variable only).
  - Re-running the ENM/pocket/time sweeps (already done; this is the
    orthogonal, missing axis).
  - Reselecting the submission operator (Tier-2-gated, [[TASK-0100]]).
- Constraints And Invariants: identical pipeline, holo, cutoffs, seed
  convention across all apo inputs; the ONLY varied quantity is the apo
  structure. Label-blind throughout.
- Planned Validation: the distribution itself IS the result; no synthetic
  gate needed (this is a robustness measurement of an existing observable,
  not a new observable). Optionally extend to BCR-ABL1 / PTP1B if KRAS
  shows large spread.

## In Progress

None

## TODO

- [ ] Assemble + RCSB-verify a list of valid KRAS G12C apo structures
      (state inclusions/exclusions and why).
- [ ] Run the existing pipeline unchanged per apo structure.
- [ ] Handle NMR / missing-B-factor structures explicitly.
- [ ] Report AUC/P@5/floor-clear distribution + median + spread + per-
      structure CIs.
- [ ] One-line verdict: is KRAS's result structure-robust or a lucky draw?
- [ ] Optionally extend to BCR-ABL1 / PTP1B if spread is large.

## Dependency

- [[TASK-0094]] (Done) — proximity floor.
- [[TASK-0112]] (Done) — bootstrap CI.
- [[TASK-0124]] (Done) — the myosin structure-swap that motivates this.
- [[TASK-0130]] (Done) — converged-limit propagator.

## Open Questions

- How many apo structures is "enough" for a stable distribution —
  Implementer's call, state the number and reasoning (>= 5 minimum).
- Whether to include close homolog/mutant apo structures or restrict to
  G12C — state the inclusion rule.

## Done

(not yet)
