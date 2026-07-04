# TASK-0004 Implement `labels.py` — pocket/label derivation

## Context

- ID: TASK-0004
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/labels.py`
- Status: TODO
- Owner: Implementer
- Source: notebook `notebooks/H_new_engineering (4) CLEAN.ipynb` §1 "Robust
  functional-site detection" (partial precedent only — see below);
  `SYSTEMS_allosteric_corrected_v2.md`'s derivation rule;
  `.ai/tasks/PLANS/PLAN.md` Phase 0b/1
- Scope: `__WORK_IN_PROGRESS__/src/allostery/labels.py` (currently a
  5-line `NotImplementedError` stub) +
  `__WORK_IN_PROGRESS__/tests/test_labels.py` (new)

## Intent Contract

- Outcome: given an apo structure, its holo counterpart, and a target config
  (from TASK-0003's `targets.yaml`), produce the allosteric pocket label
  mask and the functional/active-site index list — programmatically, not by
  hand-transcription.
- In Scope:
  - `residues_near(coords, ligand_coords, cutoff=4.5)` — heavy-atom distance
    contact set.
  - `holo_pocket_mask(apo, holo, ligand_code, cutoff=4.5)` — maps holo
    ligand-contact residues back onto the apo residue numbering via **global
    sequence alignment**, not residue-number equality (`SYSTEMS_v2` calls out
    the ABL1 1a/1b +19 numbering offset as a live hazard this must handle).
  - `functional_indices(target_config)` — the active/catalytic site to
    seed from and exclude from the pocket label (e.g. BCR_ABL1's NIL/ATP
    site must be excluded, not predicted).
  - `terminal_mask(n_residues, terminal_fraction=0.05)` — matches the
    existing `potentials.V_T` convention, reused here for pocket-eligibility
    filtering.
  - `pick_drug(holo_structure, target_config)` — select the *allosteric*
    ligand when a holo structure contains more than one bound ligand
    (the BCR_ABL1 NIL-vs-asciminib bug this whole doc chain traces back to).
- Out Of Scope: cryptic-openness scoring (TASK-0005/`superpose.py` consumes
  this module's output, doesn't produce it).
- Constraints And Invariants:
  - **leakage discipline**: this module is allowed to look at holo to build
    the label (that's its entire purpose), but nothing downstream of the
    label (transport operators, scoring) may call back into holo except
    through this module's output. Document this boundary in the module
    docstring so `protocol.py` (TASK-0006) can cite it.
  - never hand-transcribe a residue list; if a target's ligand can't be
    resolved programmatically, the pocket is `None`/empty and flagged, not
    guessed (mirrors `SYSTEMS_allosteric_corrected_v2.md`'s central rule).
- Planned Validation: unit tests on synthetic apo/holo coordinate pairs
  (small helix + a displaced "ligand" point cloud) so the contact-set and
  alignment logic is checked without a network fetch; one integration test
  gated behind network access (`@pytest.mark.network` or similar) against
  KRAS_G12C (4OBE/6OIM) once TASK-0003's config exists.

## Why this is a partial port, not a full one

Notebook §1 ("Robust functional-site detection") covers *active-site*
detection, which maps to this module's `functional_indices`. It does **not**
cover holo-ligand-contact pocket derivation or the sequence-alignment
residue mapping — those are net-new per `SYSTEMS_allosteric_corrected_v2.md`
and `.ai/tasks/PLANS/PLAN.md`'s repo-structure spec (`labels.py` marked
`NEW` there, not `[have]`). Read notebook §1 for the active-site half; build
the pocket-derivation half fresh against the two markdown specs.

## In Progress

None

## TODO

- [ ] Read notebook §1 cells; extract the active-site detection logic into
      `functional_indices`.
- [ ] Implement `residues_near` (heavy-atom cutoff contact, reuse
      `hamiltonians.contact_matrix`'s distance-computation pattern if
      applicable).
- [ ] Implement sequence alignment apo↔holo (Biopython pairwise2 or a
      minimal Needleman-Wunsch) for `holo_pocket_mask` — this is the piece
      that catches the ABL1 1a/1b offset bug.
- [ ] Implement `pick_drug` with an explicit allow-list per target from
      `targets.yaml` (`drug_ligand` field) rather than "largest/first
      ligand" heuristics — that heuristic is exactly what produced the
      original NIL-vs-asciminib bug.
- [ ] Unit tests for all of the above on synthetic data.
- [ ] One real-target integration check against KRAS_G12C, cross-checked
      by hand against `backend/systems.py`'s existing `pocket_full[4.5]`
      list — they should approximately agree; investigate and document any
      material disagreement rather than silently trusting either.

## Dependency

- TASK-0003 (`targets.yaml`) — needs apo/holo ids, chain, drug ligand code
  per target.
- Existing `hamiltonians.py`, `potentials.py` (both `[have]`) for
  contact/terminal-mask conventions to stay consistent with.

## Open Questions

- Biopython/gemmi/Biotite — `clean.py` already imports `prody`/parses via
  its own path; should the sequence-alignment step reuse whatever library
  `clean.py` settles on, or is a lighter dependency acceptable here?
- Should `pick_drug`'s per-target allow-list live in `targets.yaml`
  (TASK-0003) or be hardcoded in `labels.py`? Recommend `targets.yaml`,
  since that keeps this module target-agnostic.

## Done

(not yet)
