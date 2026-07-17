# TASK-0128 `calibrate_kappa`'s exactly-6-near-zero-mode assertion blocks 2/3 mandatory targets

## Context

- ID: TASK-0128
- Title: `superpose.calibrate_kappa`/`anm_modes` `raise ValueError` unless
  exactly 6 near-zero rigid-body ANM modes are found (TASK-0005's own
  hardening, `n_zero < 6` -> `n_zero != 6`). Discovered while running
  [[TASK-0099]]'s calibrated coherence-sensitivity sweep on all three
  mandatory targets: KRAS_G12C calibrates cleanly (`n_zero=6`), but
  BCR_ABL1 finds `n_zero=7` and CARDIAC_MYOSIN finds `n_zero=10` --
  both raise instead of calibrating, blocking any analysis that needs
  `gamma_scale`/`kappa` on those two targets.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer B (this thread)
- Claimed At: 2026-07-17 23:39
- Source: TASK-0099's real 3-target run, 2026-07-16 (Implementer A).
- Crit Ref: TASK-0005's own Done section already anticipated exactly this
  failure mode and flagged it as future work, not a surprise: *"This is
  correct for the single-chain targets this task validated against
  (KRAS_G12C), but a genuinely multi-chain/floppy-linker target (e.g.
  MYC_MAX's cMyc+Max+DNA assembly) might legitimately have more than 6
  near-zero-but-not-exactly-zero modes without being 'disconnected' in the
  error sense -- worth revisiting this strictness once a multi-chain
  target is actually run through this module."* That target has now
  actually been run (twice: BCR_ABL1, CARDIAC_MYOSIN), confirming the
  prediction.

## Intent Contract

- Outcome: determine *why* BCR_ABL1/CARDIAC_MYOSIN have 7/10 near-zero ANM
  modes instead of 6 (genuine multi-domain/floppy-linker softness vs. an
  actual disconnected contact graph at the configured `cutoff` vs. a
  numerical near-degeneracy at the `1e-8` threshold), then either (a) widen
  `calibrate_kappa`/`anm_modes`'s acceptance criterion appropriately (e.g.
  accept `n_zero >= 6` again but only after confirming the graph is
  actually connected via `operator_diagnostics`, restoring the original
  "≥6" intent without reintroducing the disconnected-graph false pass
  TASK-0005 fixed), or (b) confirm the strict check is catching a real bug
  on these targets and fix the actual root cause instead.
- In Scope:
  - Diagnose BCR_ABL1 (N=451, `n_zero=7`) and CARDIAC_MYOSIN (N=950,
    `n_zero=10`) directly -- print/inspect the extra near-zero eigenvalues'
    magnitudes and the corresponding mode shapes; check
    `diagnostics.operator_diagnostics(H13_3N_anm_hessian(...))`'s
    `n_components` for a real disconnection before assuming floppiness.
  - Decide and implement the fix (widened criterion, or a real bug fix),
    with a regression test per target case (synthetic disconnected graph
    must still raise; a synthetic multi-domain/floppy-linker construction
    with >6 legitimate near-zero modes must not).
  - Re-run [[TASK-0099]]'s coherence-sensitivity sweep on BCR_ABL1 and
    CARDIAC_MYOSIN once unblocked, and update `RESULTS.md`'s TASK-0099
    section from "blocked" to a real result.
- Out Of Scope: any other `superpose.py` functionality; TASK-0099's own
  classification logic (already correct and tested independently of this
  blocker).
- Planned Validation: the new regression tests above, plus a real re-run
  of TASK-0099's sweep on both previously-blocked targets.

## Dependency

- [[TASK-0005]] -- owns `calibrate_kappa`/`anm_modes`, source of the
  original `!= 6` hardening this task revisits.
- [[TASK-0099]] -- the consumer that discovered this; blocked on it for
  BCR_ABL1/CARDIAC_MYOSIN's own calibrated-gamma-scale result.

## Open Questions

- None yet -- root cause (floppiness vs. disconnection vs. numerical
  threshold) is this task's own first step to determine, not pre-decided
  here.

## Done

**(1) Root cause diagnosed directly, real data, before touching any
code** (per this task's own In Scope ordering): fetched BCR_ABL1
(`n_zero=7`)/CARDIAC_MYOSIN (`n_zero=10`) and inspected the actual
eigenvalues and eigenvector shapes, not just the counts.

- **Not a disconnected contact graph.** `diagnostics.operator_diagnostics`
  called directly on the real 3N×3N `H13_3N_anm_hessian` (confirmed
  this function correctly reduces block-sparsity to residue-level
  connectivity, verified against an independent scalar-contact-graph
  Laplacian check before trusting it): `n_components=1` for both targets.
- **Not a numerical near-degeneracy at the `1e-8` threshold either.**
  Both targets' "extra" eigenvalues sit at true machine-precision zero
  (~1e-16 to 1e-15, indistinguishable from the 6 trivial rigid-body
  modes), then jump 5 orders of magnitude (BCR_ABL1: to 5.56e-4) or 9
  orders of magnitude (CARDIAC_MYOSIN: to 5.77e-7) to the real
  low-frequency spectrum — a clean, sharp gap, not a smooth continuum of
  legitimately-small-but-nonzero floppy modes blending into the zero
  cluster the way TASK-0005's own "floppy-linker" speculation imagined.
- **Genuine, localized structural softness — real, not a bug.**
  Inspected each extra zero-mode eigenvector directly (per-residue
  displacement norm, top-5 by participation): BCR_ABL1's single extra
  mode localizes almost entirely onto a compact ~10-residue segment
  (chain A, resnums 198-207); CARDIAC_MYOSIN's *all four* extra modes
  localize onto the same compact ~17-residue segment (chain B, resnums
  819-835) — not spread across the structure. This is the well-known
  artifact of a purely central-force (distance-only, no angular term)
  ANM model: a locally under-constrained substructure can have an
  exact zero-energy internal rotational mode without the graph being
  disconnected at all (a node/small cluster whose local contact
  geometry doesn't fully constrain rotation costs nothing to rotate,
  in a model that only penalizes distance changes). For CARDIAC_MYOSIN
  specifically, this is plausibly connected to that target's own
  independently-documented 5TBY low-resolution/under-constrained
  caveat (already flagged elsewhere in this project) — not re-derived
  or asserted here, just noted as a plausible, consistent connection.

**(2) Fix implemented: Option (a) from this task's own Intent Contract**
— widened `n_zero != 6` back to `n_zero >= 6`, but only after confirming
real connectivity, restoring the original "≥6" intent without
reintroducing the disconnected-graph false-pass TASK-0005 fixed.
Extracted the check (previously duplicated verbatim in both `anm_modes`
and `calibrate_kappa`) into a single shared `_check_anm_rigid_body_
nullspace(H, w, n_zero)` helper in `superpose.py`:
- `n_zero < 6` → unconditional `ValueError` (fewer than the mandatory
  minimum can't happen for a real ANM Hessian; always a bug, no
  connectivity check needed).
- `n_zero > 6` → call `operator_diagnostics(H)["n_components"]`; raise
  only if `!= 1` (genuinely disconnected — TASK-0005's original
  regression), otherwise accept and proceed (TASK-0128's real,
  connected-but-locally-floppy case).
- `n_zero == 6` → accepted directly, no extra connectivity call (the
  common/expected case, avoids paying the `operator_diagnostics` BFS
  cost when nothing about the original assumption is in question).

**(3) Regression tests** (`tests/test_superpose.py`, 5 new, `TestAnmModes`):
`test_raises_when_fewer_than_six_zero_modes` (unconditional `n_zero<6`
case); `test_disconnected_graph_still_raises_even_with_many_zero_modes`
(TASK-0005's own original regression, re-verified directly against real
numbers this time — `n_zero=12`, `n_components=2`, confirmed via `eigh`/
`operator_diagnostics` before asserting the raise, not just "still
raises"); `test_connected_structure_with_more_than_six_zero_modes_does_
not_raise` (this task's actual fix target — a small synthetic
main-cluster-plus-thinly-bridged-sub-cluster construction reliably
reproduces the real pattern, `n_zero=7`, `n_components=1`, found by
direct experimentation rather than guessed); `test_calibrate_kappa_
also_accepts_the_connected_floppy_case` (confirms the shared helper
actually reaches both call sites, not just `anm_modes`). Full
`test_superpose.py`: 50 passed.

**(4) Re-ran TASK-0099's coherence-sensitivity sweep on both previously-
blocked targets** (`scripts/coherence_sensitivity_scan.py`, real fetch):

| Target | `gamma_scale` | Sweep | `auc_range` | Classification |
|---|---|---|---|---|
| BCR_ABL1 | 7.41e-4 | full 4-point | 0.0050 | `COHERENCE_NOT_SIGNIFICANT` |
| CARDIAC_MYOSIN | 9.38e-3 | γ=0 anchor only | N/A | `INFEASIBLE_NOT_RUN` |

BCR_ABL1's calibration and full sweep now both succeed, matching KRAS_
G12C's exact conclusion (flat across γ, every point floor-cleared,
`COHERENCE_NOT_SIGNIFICANT`) — this project's coherence-adds-nothing
finding is now confirmed on 2 of 3 mandatory targets, not 1. CARDIAC_
MYOSIN's `gamma_scale` now computes successfully (confirms this task's
own blocker is resolved for that target too), but its full 4-point sweep
remains not-run — for a *separate*, pre-existing reason (`haken_strobl`'s
own ~30+ min/call cost at N=950, TASK-0105's own already-documented
finding, nothing to do with `calibrate_kappa`) — reported honestly as
`INFEASIBLE_NOT_RUN`, not silently converted into a result it doesn't
have or conflated with this task's own blocker.

**(5) `RESULTS.md` updated additively** — TASK-0099's own "blocked, not
silently skipped" section gets a dated `[RESOLVED]` block with the root-
cause diagnosis and the real re-run numbers; open-questions row #10
updated in place (this table's own established convention — see rows
1-9's own "resolved DATE" cell pattern — not the main-prose append-only
convention) to reflect 2/3 targets now confirmed, not 1/3.

**Not attempted, explicitly out of this task's own scope**: any other
`superpose.py` functionality; re-deriving TASK-0099's own classification
logic (already correct, untouched); making CARDIAC_MYOSIN's full sweep
feasible (a distinct, pre-existing `haken_strobl` performance question,
not this task's blocker).
