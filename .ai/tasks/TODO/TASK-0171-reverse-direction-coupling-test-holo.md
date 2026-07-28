# TASK-0171 Reverse-direction coupling test on HOLO topology (comparison to TASK-0162)

## Context

- ID: TASK-0171
- Title: TASK-0162's forward/reverse coupling test (`scripts/
  reverse_direction_coupling_test.py`) ran every propagation on **APO**
  topology exclusively — `build_H_new(apo.coords, ...)` and
  `H2_combinatorial_laplacian(apo.coords, ...)`, confirmed directly from
  the script; holo was used only to derive labels. Run the identical
  forward/reverse comparison on **HOLO** topology, holo-native
  end-to-end, as a diagnostic comparison — matching the precedent
  `TASK-0067` already established for exactly this apo-vs-holo question
  on a different observable family.
- Status: TODO
- Owner: Implementer
- Source: direct user question, 2026-07-28 — confirmed via code reading
  (not assumed) that TASK-0162 is apo-only; user then asked for the
  holo-side run to be filed as its own task.
- Crit Ref: `run_challenge._load_apo_holo` fetches apo and holo
  independently, with no superposition/blending between them
  (`run_challenge.py:125-145`) — apo and holo have their own coordinate
  frames and, in general, their own residue numbering. A holo run must
  therefore use **holo-native** labels (built directly on `holo.coords`/
  `holo.ligand_groups`), not apo-derived labels naively re-applied to
  holo's coordinate array — `TASK-0067` hit and solved exactly this
  problem already (see Dependency).

## Intent Contract

- Outcome: for each of TASK-0162's 5 target x 5 observable cells (3
  mandatory + PTP1B/CASPASE7), the same forward (source=active_site,
  label=pocket) / reverse (source=pocket, label=active_site) comparison,
  computed entirely from **holo** coordinates/topology instead of apo,
  reported side by side with TASK-0162's existing apo numbers — not as
  a replacement, an additional comparison layer.
- In Scope:
  - Reuse `test_gnm_cutoff_weight_benchmark.py::_holo_native_labels`
    (or an equivalent helper, promoted to non-test code if that's
    cleaner) to build **holo-native** `pocket`/`active_site` masks —
    do not port apo-numbered indices onto holo's coordinate array.
  - Build `H_new`/`H2_combinatorial_laplacian` from `holo.coords`/
    `holo.bfactors` (not apo's) for every one of TASK-0162's 5
    observables, otherwise reusing each scoring function completely
    unmodified, per TASK-0162's own precedent.
  - Run both FORWARD and REVERSE directions on this holo-native setup,
    same floor comparison (`degree_centrality`/`euclid_from_seed_
    centroid`/`hop_from_seed`, all computed on `holo.coords`) and same
    background-Spearman asymmetry statistic TASK-0162 already defines.
  - Report a four-way table per target x observable: apo-forward,
    apo-reverse (TASK-0162's existing numbers, cited not recomputed
    unless a discrepancy is suspected), holo-forward, holo-reverse.
  - State explicitly, per cell, whether the apo-vs-holo gap is small
    (matching TASK-0067's own finding: "an order of magnitude smaller
    than the cutoff/weight-scheme spread... near-chance performance is
    not an apo-vs-holo artifact") or whether this observable family
    behaves differently.
- Out Of Scope:
  - Any new observable — pure re-application of TASK-0162's existing
    five, on holo topology, matching that task's own scope discipline.
  - Re-litigating TASK-0162's apo-side numbers — cite them as given.
  - Blending apo and holo in any way (average structure, apo labels on
    holo coords, etc.) — this is a second, fully self-contained,
    holo-native run, not a hybrid.
- Constraints And Invariants: this is explicitly **not** a leakage-safe
  prediction result, same caveat TASK-0067 stated for its own holo run —
  it is a diagnostic comparison (does having the actual holo topology in
  hand change these observables' behavior), not a submission-path
  computation. State this plainly in the write-up, matching TASK-0067's
  own framing verbatim if convenient.
- Planned Validation: real run against all 5 targets' live holo
  structures (network-gated, matches TASK-0162/TASK-0067's own
  precedent); the four-way comparison table; an explicit statement of
  whether any observable's apo-vs-holo gap is large enough to be its own
  finding, per-cell, not just an aggregate.

## TODO

- [ ] Confirm/port `_holo_native_labels` (or build an equivalent) for
      all 5 targets, asserting disjointness the same way TASK-0162 did.
- [ ] Build holo-native `H_new`/`H2_combinatorial_laplacian` per target.
- [ ] Run forward + reverse, all 5 observables, all 5 targets, on holo
      topology.
- [ ] Four-way (apo-fwd/apo-rev/holo-fwd/holo-rev) comparison table.
- [ ] State per-cell whether the apo/holo gap is small (TASK-0067
      precedent) or a real difference worth its own finding.
- [ ] `RESULTS.md` section, additive, cross-linked to TASK-0162's
      existing section.

## Dependency

- [[TASK-0162]] (Done) — the apo-side run this task compares against;
  reuses its script structure and all 5 scoring functions unmodified.
- [[TASK-0067]] — the established precedent for a holo-native
  diagnostic run (`_holo_native_labels`) and for how to frame the
  "not leakage-safe, diagnostic upper bound only" caveat.

## Open Questions

- Whether to also run this against the generalization set within this
  task's own scope, matching TASK-0162's own decision to do so — given
  TASK-0162 found the full 5-target run took under a minute, deferral
  is likely unjustified here too, but Implementer's own call to confirm
  at execution time (holo network fetches may dominate wall time more
  than the apo-only case did).

## Done

(not yet)
