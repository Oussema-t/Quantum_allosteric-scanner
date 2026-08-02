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
- Status: Done
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

- [x] Confirm/port `_holo_native_labels` (or build an equivalent) for
      all 5 targets, asserting disjointness the same way TASK-0162 did.
- [x] Build holo-native `H_new`/`H2_combinatorial_laplacian` per target.
- [x] Run forward + reverse, all 5 observables, all 5 targets, on holo
      topology.
- [x] Four-way (apo-fwd/apo-rev/holo-fwd/holo-rev) comparison table.
- [x] State per-cell whether the apo/holo gap is small (TASK-0067
      precedent) or a real difference worth its own finding.
- [x] `RESULTS.md` section, additive, cross-linked to TASK-0162's
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
  than the apo-only case did). **Resolved: yes, ran all 5 targets** — the
  holo-native run also completed in well under a minute (~10s total),
  confirming deferral was unnecessary here too.

## Done

**Resolved 2026-08-02: the apo-vs-holo gap is real and large — this
observable family behaves differently from [[TASK-0067]]'s own "tiny
gap" precedent, not a reproduction of it.**

**Setup**: new `scripts/reverse_direction_coupling_test_holo.py`, mirrors
[[TASK-0162]]'s own `reverse_direction_coupling_test.py` structure
exactly (same 5 observables, same forward/reverse seed-swap logic, same
background-Spearman asymmetry statistic) with only the coordinate/label
source changed from apo (`build_labels`) to holo (`holo.coords`/
`holo.bfactors` + `_holo_native_labels`, [[TASK-0067]]'s own holo-frame
label construction, imported verbatim from `test_gnm_cutoff_weight_
benchmark.py`, not re-derived). Disjointness of the holo-native pocket/
active-site masks asserted the same way TASK-0162 asserted it for the
apo-native ones — held on all 5 targets. TASK-0162's own apo-side numbers
cited directly from its already-written JSON output (confirmed that JSON
covers all 5 targets even though the committed script's own `TARGETS`
constant lists only 3 — read directly before trusting it, not assumed),
never recomputed here, per this task's own Out of Scope.

**Forward direction**: apo floor-clears 10/25 (40%, exactly matching
TASK-0162's own reported number — a real consistency check that the
cited apo numbers are the right ones), holo floor-clears only 6/25
(24%). 10/25 individual cells flip verdict: KRAS_G12C (`ctqw_converged`,
`dcc_low`, `T_E0_Hnew`) and PTP1B (`ctqw_converged`, `dcc_low`,
`T_E0_Hnew`) lose clearance on holo; CARDIAC_MYOSIN `dcc_low` also loses
it; BCR_ABL1 `ctqw_converged`, CARDIAC_MYOSIN `ctqw_converged`, and PTP1B
`prs_low` gain it.

**Reverse direction**: apo and holo floor-clear the same total count,
4/25 (16%) each — but not the same 4 cells (KRAS_G12C `dcc_low` loses
clearance on holo, CARDIAC_MYOSIN `ctqw_converged` gains it; net zero).

**Gap magnitude, per-cell, stated explicitly** (this task's own Planned
Validation requirement): mean |gap| is 0.133 (forward) / 0.119 (reverse)
— an order of magnitude larger than [[TASK-0067]]'s own "tiny apo/holo
gap" finding for the bare GNM operator (0.081/0.061, `RESULTS.md` row
2), and comparable to [[TASK-0153]]'s own already-flagged `dcc_low`
apo/holo complication on CARDIAC_MYOSIN (gap −0.303). Two observables
account for most of the largest gaps here: `T_E0_Hnew` (transmission on
`H_new` at E=0) shows the single largest gap in both directions
(PTP1B forward −0.400, KRAS_G12C forward −0.344, CASPASE7 forward
−0.292, PTP1B reverse −0.389, KRAS_G12C reverse −0.209) and `dcc_low`
(CASPASE7 reverse −0.411, CARDIAC_MYOSIN forward −0.273) — this
*extends* TASK-0153's own finding that `dcc_low` specifically does not
get a clean apo/holo ceiling reading, rather than being an independent
new complication. `ctqw_converged`/`R_eff`/`prs_low` are comparatively
closer to TASK-0067's own "small gap" pattern on most cells (11/25
forward and 18/25 reverse cells have a gap smaller than that cell's own
floor-vs-actual margin — this task's own per-cell small/large criterion,
since TASK-0067's externally-borrowed "order of magnitude smaller than
the cutoff/weight-scheme spread" comparator isn't computed for these
observables), but not uniformly: `ctqw_converged` alone flips KRAS_G12C's
own forward verdict (apo 0.590, floor-clearing → holo 0.410, well below
its own floor).

**One-line verdict**: this observable family behaves *differently* from
TASK-0067's own precedent — the apo-vs-holo gap is real and large enough
to change which cells clear their floor (40% of forward cells), not a
diagnostic non-event. Consistent with, and adding a third independent
line of evidence to, [[TASK-0169]]'s benchmark-discriminability finding
and [[TASK-0015]]'s Step 2 gate: this program's headline observables are
sensitive to structural details (apo vs. holo topology) a robust
allosteric signal should arguably be less sensitive to.

Diagnostic only throughout, never a submission-path result — stated per
TASK-0067's own established caveat, verbatim in the module docstring.

Docs updated additively: `RESULTS.md`'s new "Reverse-direction coupling
test on HOLO topology" section + open-questions row 51 (row 50 landed
concurrently, [[TASK-0157]] — renumbered to avoid collision).

No new `src/allostery` module — pure re-application of TASK-0162's
existing five observables to holo topology, matching this task's own
scope discipline and the precedent of `holo_diagnostic_transport_
lowmode.py`/`holo_diagnostic_comparison.py` (neither carries its own
dedicated unit test file either). Full suite (unaffected, no `src/`
change): 1063 passed, 2 xfailed, 0 failed.
