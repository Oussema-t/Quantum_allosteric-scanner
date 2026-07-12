# TASK-0070 Pocket label exclusion assembly (`pocket & ~functional & ~terminal`)

## Context

- ID: TASK-0070
- Title: Add the `build_labels` assembly step that actually computes
  `pocket & ~functional & ~terminal`, gated and consumed correctly across
  `labels.py` / `protocol.py` / `analysis.py`.
- Status: Done
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 0, item 0.1 —
  "**Oldest live defect.** Nothing assembles `pocket & ~functional &
  ~terminal`; `labels` owns ingredients, `protocol` gates them, `analysis`
  consumes the raw mask. Survived four reviews *because no task owns it* —
  it is a seam, not a module." Blocks TASK-0052 (0.2) and TASK-0063 (0.4).

## Intent Contract

- Outcome: a `build_labels` step exists somewhere in the pipeline that
  assembles the final pocket label as `pocket & ~functional & ~terminal`,
  with an assertion `pocket ∩ active_site == ∅`, and every downstream
  consumer (`protocol.py`'s frozen gate, `analysis.py`'s scoring) reads
  this assembled label rather than a raw, unexcluded mask.
- In Scope: `labels.py` (owns the ingredient masks: pocket, functional,
  terminal), the new assembly logic (wherever it structurally belongs —
  likely `labels.py` itself, since `test_leakage_gate.py` already assumes
  a `build_labels()` there per TASK-0052/SEAM-0003), and every call site in
  `protocol.py`/`analysis.py` that currently consumes an unexcluded mask.
- Out Of Scope: the leakage-gate contract test reconciliation itself
  (TASK-0052 owns making `test_leakage_gate.py` match the real API) —
  this task provides the `build_labels` function TASK-0052 needs to bind
  to; do them together per the plan's ordering but keep them separately
  reviewable.
- Acceptance Scenarios:
  - Given a target with overlapping pocket/functional/terminal residue
    sets, when `build_labels` runs, then the returned pocket label
    excludes every functional and terminal residue.
  - Given the assembled label, then `assert pocket ∩ active_site == ∅`
    holds for every benchmark target in `config/targets.yaml`.
  - **Decision required, must be recorded, not inherited by omission**:
    KRAS **Cys12** — in or out of the pocket label? `targets.yaml` says
    exclude; sotorasib (MOV) is covalent at Cys12, so Cys12 enters the
    MOV-derived contact set. Pick one explicitly and write down why.
- Constraints And Invariants: this is the seam TASK-0018/TASK-0053's
  sweeps missed because no single module owned it — name a single owner
  function/module for the assembly so it can't fall between files again;
  register a `.ai/seams/` record for it per the Seam Protocol if this
  creates a new cross-module boundary that didn't have one before.
- Planned Validation: unit test asserting the exclusion property on a
  synthetic overlapping case; integration check against
  `config/targets.yaml`'s real benchmark targets, especially KRAS_G12C's
  Cys12 case.

## Dependency

- Blocks TASK-0052 (leakage-gate contract reconciliation, SEAM-0003) —
  `test_leakage_gate.py` assumes `build_labels()` exists; it doesn't yet.
- Blocks TASK-0063 (`functional_indices` gate parameter gap) — same seam,
  do together per the plan.
- Reads `labels.py` (TASK-0004, Done), `protocol.py` (TASK-0006, Done).

## Open Questions

- KRAS Cys12 in/out — see Acceptance Scenarios above; this is the one
  decision this task must not leave implicit.
  - **Resolved (2026-07-12):** Cys12 is **excluded** from the final
    pocket label, via the *general* `~active_site` exclusion rule, not a
    KRAS-specific special case. Verified empirically against real
    4OBE(apo)/6OIM(holo) data: Cys12 (apo residue 12) is in
    `pocket_raw` (True — it's sotorasib/MOV's covalent anchor, so it's a
    raw ligand-contact hit) *and* in `active_site` (True — it's also a
    GDP-contact functional residue, `func_ligand: ["GDP"]`), so the
    `pocket_raw & ~active_site & ~terminal` formula excludes it
    automatically. Matches `targets.yaml`'s own literature note on this
    target ("EXCLUDE Cys12/P-loop (covalent/orthosteric)"). No
    special-casing was added or needed — see
    `tests/test_labels.py::test_kras_g12c_real_cys12_excluded`.

## Done

- `labels.py`: added `Labels` dataclass (`pocket`, `pocket_raw`,
  `active_site`, `terminal`, `functional_provenance`, `drug_ligand`) and
  `build_labels(apo, holo, target_config, cutoff, terminal_fraction) ->
  Labels`, which assembles `pocket_raw & ~active_site & ~terminal` and
  **asserts** (not just documents) `pocket ∩ active_site == ∅` and
  `pocket ∩ terminal == ∅` — the SEAM-0003 invariant now actually
  executes instead of being a docstring claim with nothing to check it.
  `target_config: dict` (not the `allosteric_ligand`/`func_ligands`
  positional args `test_leakage_gate.py`'s CONTRACT section assumed) —
  matches every other function in `labels.py`'s existing convention
  (`pick_drug`, `functional_indices`); TASK-0052 reconciles the test
  against this real signature.
- `protocol.py`: `get_pocket_mask` now returns `build_labels(...).pocket`
  (the assembled label) instead of `labels.holo_pocket_mask`'s raw,
  unexcluded mask — this was the actual defect ("labels owns ingredients,
  protocol gates them, analysis consumes the raw mask"). Its signature
  changed from `(apo, holo, target_name, ligand_code, cutoff)` to
  `(apo, holo, target_name, target_config, cutoff)`, now consistent with
  `get_functional_indices`/`get_superpose_report`'s existing shape (it
  was the odd one out before). Added `get_labels` (gated, returns the
  full `Labels` object) for callers that need more than the final mask.
  `analysis.py`/`select.py`/`diagnostics.py`/`report.py` were checked
  (grepped for `holo_pocket_mask`/`pocket_mask`) and confirmed to already
  take a generic, caller-supplied `labels`/`pocket_mask` array — no
  changes needed there; they automatically benefit once the gate supplies
  the correctly-assembled mask instead of a raw one.
- Tests: `tests/test_labels.py` gained `TestBuildLabels` (4 synthetic
  cases: overlapping exclusion, disjoint case stays populated, no-drug
  `None` handling, provenance recording) plus two real-target checks
  (`test_kras_g12c_real_cys12_excluded`,
  `test_bcr_abl1_real_exclusion_invariant_holds` — a second independent
  real target, not just KRAS, confirming the fix generalizes).
  `tests/test_protocol.py`'s fixture (`_apo_holo_with_ligand`) was
  extended with a second, disjoint functional ligand — the old
  single-ligand fixture fell through to the top-degree fallback for
  `active_site`, which on that 12-residue synthetic helix happened to
  fully swallow the drug-contact residues, silently emptying the
  assembled pocket (caught by actually running the updated tests, not
  assumed). Added `test_get_pocket_mask_returns_assembled_not_raw` and
  `test_get_labels_gated`.
- Full suite: 368 passed, 1 pre-existing xfail, 1 pre-existing xpass, **2
  new failures — expected, not a regression to fix here:**
  `test_leakage_gate.py::test_labels_allosteric_ligand_only` (calls
  `build_labels` with the old assumed positional signature, now a real
  `TypeError` instead of silently xfail-ing via `ImportError`) and
  `::test_labels_alignment_not_resnum` (its own body is a literal
  `raise AssertionError("implement: ...")` once the import succeeds —
  written that way deliberately, per the file's own design, to force the
  reconciliation once `build_labels` exists). **This task's own Out Of
  Scope line names this exact handoff**: "this task provides the
  `build_labels` function TASK-0052 needs to bind to" — reconciling
  `test_leakage_gate.py` against the real signature is TASK-0052's job,
  picked up immediately next in this same session per
  `EXECUTION_PLAN.md`'s 0.1 -> 0.2 ordering ("Needs 0.1 to bind
  `build_labels`").
- `viz.py`'s `test_viz.py`/`test_seam_0006_pathways_viz.py` still fail to
  collect (`ModuleNotFoundError: matplotlib`, TASK-0014's own concurrent
  in-progress dependency gap) — excluded from the count above, unrelated
  to this task, not touched.
