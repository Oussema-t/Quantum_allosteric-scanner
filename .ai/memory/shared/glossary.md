# Shared Glossary

Add canonical terms only when the project needs stable vocabulary across agents and docs.

## Structural hierarchy: Protein → Site → Residue (Cα) → Atom

- **Protein**: the full molecular structure loaded from a PDB entry. A single PDB file
  may contain multiple proteins/chains/ligands — `clean.py` selects down to the specific
  chain(s) a target actually uses.
- **Site**: a named *region* — a set of residues, not a single one (e.g. the active
  site / catalytic pocket, or a druggable allosteric pocket). "Active site" and "pocket"
  in this codebase are always residue **sets** (`labels.build_labels(...).active_site`/
  `.pocket` are boolean arrays over all residues), never a single residue standing in
  for the whole region.
- **Amino acid / residue**: the graph node. Represented by its **Cα coordinate only**
  (or **P** for nucleic acids) — `clean.py:140`, `"name CA or (nucleic and name P)"`.
  Every graph/Hamiltonian/propagator in this pipeline (`hamiltonians.contact_matrix`,
  `build_H_new`, `ctqw`/`time_averaged_ctqw`/`ground_state_relaxation`/`haken_strobl`)
  operates on the `(N, 3)` array of these coordinates, where **N = number of residues**,
  never atoms.
- **Atom**: used in exactly one place — determining which *residues* count as "pocket"
  by real heavy-atom ligand-contact distance (`labels.protein_heavy_atoms_by_residue`,
  `holo_pocket_mask`), because a Cα-only distance check would miss side-chain-mediated
  contacts. The result always collapses back to residue indices
  (`labels.py:171`, `np.unique(heavy_atom_seq_index[atom_hits])`) before touching the
  propagation graph — no atom is ever a graph node.

**Consequence worth remembering**: because "site" = a set of residues, seeding a CTQW
"from the active site" is ambiguous between seeding from *all* of that site's residues
at once (multi-index source) versus a single representative residue standing in for the
site (single-index source). Both conventions exist in this repo right now and disagree:
`ceiling.py`'s real cross-check uses the full multi-residue `active_site` array;
`scripts/run_challenge.py` (the path that produced the reported headline AUCs) reduces
the same site down to one residue (`source = int(np.sort(active_site_idx)[0])`, a
crash workaround per [[TASK-0090]], not a physics decision). This is a live, unresolved
confound in the floor/ceiling/actual comparison — see [[P-0002]] and [[Q-0003]]
(`.ai/memory/questions/architect-planner/open/`).