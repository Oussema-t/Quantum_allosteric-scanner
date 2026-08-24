# SEAM-0016 Indices returned across an apo/holo array boundary must live in the caller's own coordinate space

- units: `labels.functional_indices`/`holo_pocket_mask` (producer — resolves
  contact indices against whichever structure's heavy-atom array was
  supplied) -> `heavy_atom_seq_index`/`heavy_atom_coords` (the intermediate
  holo-space index array) -> any caller assuming the returned indices are
  already in `coords`' (apo's) own row-index space (consumer —
  `build_labels`, every real scored-target call site)
- invariant: indices returned by a function that was handed a *different*
  structure's heavy-atom array (the common real case: holo's heavy atoms,
  for true heavy-atom contact geometry against a ligand that only exists in
  holo, alongside apo's own `coords`) must be translated into `coords`' own
  index space via the Needleman-Wunsch correspondence `holo_pocket_mask`
  already uses, before being returned — never silently returned in the
  wrong array's space and used as if they were the caller's own
- owner: [[TASK-0217.001]] (Done) — built the guard: `functional_indices`
  raises `ValueError` if `heavy_atom_coords` is supplied cross-structure
  without the matching `heavy_atom_resnames`/`coords_resnames` pair needed
  to translate safely, rather than guessing or silently misindexing;
  [[TASK-0216]] (Done) — discovered the defect class (confirmed on
  KRAS_G12C, BCR_ABL1, and 8 other real targets — every real target pair in
  the register with a resolvable `func_ligand` contact was affected before
  the fix)
- seam-test: `tests/test_labels.py::
  test_cross_structure_heavy_atoms_without_resnames_raises` (negative case
  — the guard fires on a constructed bad input) and `tests/test_labels.py::
  test_cross_structure_heavy_atoms_translated_to_coords_space` (positive
  case — supplying both name arrays translates correctly); also exercised
  indirectly by `tests/test_protocol.py::
  test_get_functional_indices_forwards_heavy_atom_params`
- status: **VERIFIED**
- provenance: opened 2026-08-24 by [[TASK-0232]] (Architect/Planner registry
  pass, source: Bartosz, 2026-08-21). This seam and [[SEAM-0015]] share a
  discoverer ([[TASK-0216]]) but are genuinely two different invariants —
  SEAM-0015 is about *which* residues are the seed (a config/resolution-tier
  question), this seam is about *whether the returned indices point at the
  right structure's rows at all* (an array-correspondence question) — kept
  separate per this task's own filing (not merged into one record).
