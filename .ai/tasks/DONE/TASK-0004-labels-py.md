# TASK-0004 Implement `labels.py` — pocket/label derivation

## Context

- ID: TASK-0004
- Title: Implement `__WORK_IN_PROGRESS__/src/allostery/labels.py`
- Status: Done
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

None — all TODO items complete, see Done section.

## TODO

- [x] Read notebook §1 cells; extract the active-site detection logic into
      `functional_indices`. Initially ported notebook tier 3 ("literature
      anchor" via a resnum list) — **corrected once `targets.yaml` landed
      this session**: the real schema has no `active_site` resnum field,
      only `func_ligand` (ligand code(s)/marker(s) to exclude, e.g.
      KRAS_G12C's `["GDP"]`, BCR_ABL1's `["NIL"]`). Rewrote
      `functional_indices` to resolve `func_ligand` via ligand contact
      (same geometry as `pick_drug`), falling through gracefully for
      entries that aren't real ligand codes (PTP1B's descriptive-text
      marker, MYC_MAX's `"DNA"`). Tiers 1-2 from the notebook (pipeline
      labels, generic nucleotide-contact) still not ported — need
      pipeline/raw-structure context this module boundary doesn't carry.
- [x] Implement `residues_near` (heavy-atom cutoff contact, reuses
      `hamiltonians.contact_matrix`'s distance-computation pattern).
- [x] Implement sequence alignment apo↔holo for `holo_pocket_mask` — used a
      minimal local Needleman-Wunsch (stdlib/numpy only), not Biopython:
      neither `biopython` nor `prody` is installed in
      `__WORK_IN_PROGRESS__/.venv` as of this session, so a dependency-free
      aligner keeps the module actually importable/testable here (see
      "Open Questions" below — this resolves that one). Regression-tested
      against a +19 resnum offset (ABL1 1a/1b-style) on synthetic data.
- [x] Implement `pick_drug` with an explicit allow-list per target
      (`target_config["drug_ligand"]`) rather than "largest/first ligand"
      heuristics — no fallback candidate-picking at all; returns `None` if
      unconfigured or absent. Checked against every real `targets.yaml`
      entry: handles `null` (MYC_MAX) and descriptive non-code text
      (GROEL_SUBUNIT's `"GroES (protein, not a small molecule...)"`)
      correctly by falling through to `None`, not erroring.
- [x] Unit tests for all of the above on synthetic data
      (`tests/test_labels.py`, 25 tests: `residues_near`, `terminal_mask`
      (cross-checked against `potentials.V_T`), `pick_drug`,
      `holo_pocket_mask` (incl. the numbering-offset case and the
      heavy-atom-path regression case), `functional_indices` (incl. the
      `func_ligand`-schema cases above), `ligand_groups_from_atomgroup`,
      `protein_heavy_atoms_by_residue`, and `_contact_residue_indices`, all
      via duck-typed fake prody objects).
- [x] One real-target integration check against KRAS_G12C (4OBE/6OIM),
      cross-checked by hand against `backend/systems.py`'s existing
      `pocket_full[4.5]` list. User approved installing `prody` into
      `__WORK_IN_PROGRESS__/.venv` (network access confirmed available) —
      see Done section for the full run and a second, material finding
      (Calpha-vs-heavy-atom contact gap) this check surfaced and fixed.

## Dependency

- ~~TASK-0003~~ (`targets.yaml`) — **done** (Implementer A, 2026-07-06);
  needed apo/holo ids, chain, drug ligand code per target. Real schema
  cross-checked against this task's implementation (see TODO).
- Existing `hamiltonians.py`, `potentials.py` (both `[have]`) for
  contact/terminal-mask conventions to stay consistent with.

## Open Questions

- ~~Biopython/gemmi/Biotite~~ — **resolved this session**: lighter
  dependency. Neither `biopython` nor `prody` is installed in
  `__WORK_IN_PROGRESS__/.venv`; `holo_pocket_mask` uses a local
  Needleman-Wunsch (stdlib/numpy only) instead of adding a new runtime
  dependency for this one function.
- ~~Should `pick_drug`'s per-target allow-list live in `targets.yaml`?~~ —
  **resolved by TASK-0003**: yes, `targets.yaml`'s `drug_ligand` field.
  `pick_drug`/`functional_indices` are implemented against that real
  schema now (`drug_ligand`, `func_ligand`), not a guessed one.
- Signature notes (both deviate from the Intent Contract's literal
  single/two-arg signatures, for reasons documented in each function's own
  docstring): `functional_indices(coords, ligand_groups, target_config,
  cutoff=4.5)` needs the structure's own coords and ligand groups to
  resolve `func_ligand` contacts, not `target_config` alone;
  `holo_pocket_mask`'s `apo`/`holo` args are CleanResult-shaped objects,
  and `holo` additionally needs a `.ligand_groups` attribute that
  `clean.py`'s protein-only `CleanResult` doesn't carry (this module
  defines that contract itself, via `LigandGroup` /
  `ligand_groups_from_atomgroup`).
- New: should `LigandGroup`/`ligand_groups_from_atomgroup` move to a
  shared module (e.g. `clean.py` or a new `structures.py`) once a real
  raw-fetch layer exists and other modules (TASK-0005 `superpose.py`?)
  also need ligand data? Currently lives in `labels.py` since this task
  owns the first consumer. Flag for TASK-0018 (backend/allostery
  architecture reconciliation) if it recurs.
- New: `prody` is now installed in `__WORK_IN_PROGRESS__/.venv` (user-approved
  this session, for the integration check). `biopython` came along
  transitively as one of `prody`'s own dependencies — `labels.py` still does
  not import it (the Needleman-Wunsch decision above stands); it's present
  in the venv but unused. Neither is yet in a `requirements.txt`/
  `pyproject.toml` for `__WORK_IN_PROGRESS__` (that gap was already flagged
  in TASK-0003's Open Questions).

## Done

- All 5 functions implemented in `__WORK_IN_PROGRESS__/src/allostery/labels.py`:
  `residues_near`, `terminal_mask`, `pick_drug`, `holo_pocket_mask`,
  `functional_indices`, plus the `LigandGroup` data contract and two prody
  adapters (`ligand_groups_from_atomgroup`, `protein_heavy_atoms_by_residue`)
  and a shared `_contact_residue_indices` helper.
- `tests/test_labels.py`: 25 tests, all passing. Full WIP suite (`python3
  .ai/tools/pytest_local.py wip-all`): 217 passed, 1 xpassed (a pre-existing
  `test_superpose.py` test-order flake, unrelated to this task — passes
  standalone; TASK-0005 territory, not fixed here).
- `targets.yaml` landed mid-session (TASK-0003, Implementer A). Cross-checked
  the real schema against this task's assumptions and corrected
  `functional_indices` (no `active_site` resnum field exists; the real field
  is `func_ligand`, a list of ligand codes/markers) before calling anything
  done — see TODO.
- **Real-target integration check, KRAS_G12C (4OBE apo / 6OIM holo), run
  2026-07-06** (user-approved `prody` install into
  `__WORK_IN_PROGRESS__/.venv`; network access confirmed available):
  - `pick_drug(ligand_groups, cfg)` correctly resolved `MOV` (sotorasib).
  - First run (Calpha-only contact): derived pocket = 9 residues, all a
    subset of `backend/systems.py`'s `pocket_full[4.5]` (21 residues) — zero
    false positives, but 12 residues missed. Investigated rather than
    accepted: side-chain heavy atoms reach several A closer to a bound
    ligand than Calpha does, so a 4.5 A Calpha-only cutoff systematically
    under-counts contacts. This also matches the Intent Contract's own
    wording ("heavy-atom distance contact set") and the notebook's own
    `residues_near` precedent (cell 9), which contacts against full protein
    heavy atoms, not Calpha — the initial implementation had quietly
    under-delivered on that.
  - Fix: added `protein_heavy_atoms_by_residue` (prody adapter, selects
    `protein and (chain ...) and not hetero`, maps each heavy atom to its
    position in the structure's residue sequence) and
    `_contact_residue_indices` (aggregates per-atom contact hits back to
    per-residue hits when heavy-atom data is supplied; falls back to the
    Calpha approximation otherwise, so synthetic/unit tests with no
    heavy-atom data are unaffected). Wired into both `holo_pocket_mask` and
    `functional_indices`.
  - Second run (heavy-atom contact): derived pocket = **21/21 exact match**
    with `backend/systems.py`'s `pocket_full[4.5]` — `[9, 10, 11, 12, 13,
    16, 34, 58, 59, 60, 61, 62, 63, 68, 69, 72, 95, 96, 99, 100, 103]`, zero
    extra, zero missing.
  - Also surfaced and fixed a second, independent bug while building this
    check: `ligand_groups_from_atomgroup`'s `"hetero and not water"`
    selector (ported directly from the notebook) silently misses bound
    nucleotide ligands — prody classifies GDP under its `nucleic` flag,
    making its derived `hetero` flag False even though GDP is a real HETATM
    ligand. Fixed by selecting on prody's raw `hetatm` record flag instead
    (verified this still correctly excludes real polymer nucleic acid,
    checked against MYC_MAX's 1NKP DNA chain). Without this fix,
    `functional_indices` would have silently fallen back to the
    least-informative top-degree tier for every nucleotide-anchored target
    (KRAS_G12C's GDP, CARDIAC_MYOSIN's ADP/ATP) despite `func_ligand` being
    correctly configured in `targets.yaml`.
  - `functional_indices` on 6OIM: provenance `func_ligand-contact:GDP`,
    resnums `[11, 12, 13, 14, 15, 16, 17, 18, 28, 30, 32, 116, 117, 119,
    120, 145, 146, 147]` (holo numbering) — plausible P-loop/nucleotide
    contact region for a GTPase, not independently cross-checked against a
    second reference (no equivalent `active_site` field exists in
    `backend/systems.py` at 4.5 A to compare against; its `active_site` list
    uses a different, unspecified cutoff/method).
  - Both fixes (heavy-atom contact, `hetatm` selector) are regression-tested
    on synthetic data in `tests/test_labels.py` (no prody/network
    dependency for the test suite itself — the live check was a session-local
    scratch script, not committed, matching TASK-0003's own validation-script
    convention).
- Downstream consumers (TASK-0005 `superpose.py`, TASK-0006 `protocol.py`)
  should pass `heavy_atom_coords`/`heavy_atom_seq_index` (from
  `protein_heavy_atoms_by_residue`) into `holo_pocket_mask`/
  `functional_indices` whenever real heavy-atom data is available — the
  Calpha-only fallback exists for synthetic/test convenience, not as an
  equally-valid production path.
