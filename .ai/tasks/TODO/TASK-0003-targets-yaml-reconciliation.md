# TASK-0003 Reconcile and Author `config/targets.yaml`

## Context

- ID: TASK-0003
- Title: Produce `__WORK_IN_PROGRESS__/config/targets.yaml`, reconciling
  `__WORK_IN_PROGRESS__/SYSTEMS_allosteric_corrected_v2.md` against the
  production `backend/systems.py`
- Status: TODO
- Owner: Implementer
- Source: `.ai/tasks/PLANS/PLAN.md` Phase 0b ("Per-target config drives the
  exceptions"); `SYSTEMS_allosteric_corrected_v2.md`
- Scope: new `__WORK_IN_PROGRESS__/config/targets.yaml`;
  `__WORK_IN_PROGRESS__/src/allostery/clean.py::load_target_config` (already
  reads this path — currently 404s, nothing else changes there)

## Intent Contract

- Outcome: one YAML config file that `clean.py` and (later) `labels.py` can
  load per target, and that is provably consistent with both source
  documents rather than a third, independently-guessed version.
- In Scope: build the YAML from the two sources below, resolving every
  conflict explicitly (not silently picking one).
- Out Of Scope: deriving actual pocket residue lists (that's `labels.py`,
  TASK-0004 — this config only carries the *inputs* to derivation: apo/holo
  ids, chain, cutoff, drug ligand code, functional ligand to exclude,
  keep_nucleic, warnings).
- Constraints And Invariants:
  - per `SYSTEMS_allosteric_corrected_v2.md`'s central rule: **no
    hand-transcribed pocket residues** go in this file. If a field would
    require picking specific residue numbers, it stays out of scope for
    this task.
  - `CARDIAC_MYOSIN` and `MYC_MAX` keep their quarantine/no-pocket status —
    do not "fix" them into normal entries.
- Planned Validation: `clean.py::load_target_config("KRAS_G12C")` returns
  without error for every non-quarantined target; a short script prints the
  resolved config for all targets for manual eyeballing.

## Why this needs a review, not a straight copy

The two sources disagree in ways that matter and must be resolved by a human
call, not auto-merged:

| Field | `SYSTEMS_allosteric_corrected_v2.md` (2026-06-21, scaffold) | `backend/systems.py` (production, "ported verbatim from the research notebook") |
|---|---|---|
| BCR_ABL1 allosteric ligand code | `"ASCIMINIB"` — placeholder, flagged "*** CRITICAL FIX ***, verify 3-letter code on RCSB" | `"AY7"` — already resolved to a real RCSB 3-letter code |
| CARDIAC_MYOSIN | `confidence=0.40`, **"QUARANTINE until the apo construct and the 6C1H ligand are both confirmed"** | not quarantined — resolved via a validation substitute: `holo_validation="8QYR"` (real Bos taurus MYH7 + mavacamten X-ray), with 6C1H kept only as "challenge-listed but unusable" |
| MYC_MAX | `allosteric_pocket=[]`, confidence=0.75, extensive IDP/no-pocket rationale + a 3-tier learning-base recommendation (p53-Y220C, bHLH-LZ family, PPI-interface targets) | `pocket_full=None`, `verified=False`, one-line note — no learning-base guidance carried over |
| Pocket residues | explicitly `[]` everywhere — "derive from holo contacts, never transcribe" | populated `pocket_full`/`pocket_distal` dicts at 4.0/4.5/8.0 Å with named residues |
| ASD expansion targets (PTP1B, GLUCOKINASE, ATCase, CASPASE1/7, HEMOGLOBIN, TAR_RECEPTOR, GLYCOGEN_PHOSPHORYLASE, PFK, LDH, GROEL) | 11 draft entries, explicitly marked "NOT re-verified this pass... treat as DRAFT", several flagged as oligomeric-assembly hazards | only PTP1B and GLUCOKINASE present, both `verified=True` with populated pockets — the other 9 aren't in the production file at all |

Read that table as: **`backend/systems.py` is a later, more-resolved
snapshot than the v2 doc for the 4 mandatory targets** (it already answered
v2's own open questions — AY7 code, 8QYR validation structure). But v2 is
**more complete** for the ASD expansion (11 draft targets vs 2) and carries
context (MYC learning-base tiers, myosin quarantine rationale, per-target
`warnings` and `confidence`) that `backend/systems.py` dropped in favor of
terser `notes` strings.

The populated `pocket_full`/`pocket_distal` residue lists in
`backend/systems.py` look like the *output* of the derivation procedure v2
describes (`labels.py`'s job), not a hand-guess — the docstring says "ported
verbatim from the research notebook (§1)", and notebook §1 is "Robust
functional-site detection". This still needs a human eyes-on check: confirm
those lists actually came from a 4.5 Å holo-ligand-contact derivation
(matching v2's stated method) and are not the same kind of
hand-transcribed number v2 warns against for the *previous* (v1.2) file.
Do not assume; check.

## In Progress

None

## TODO

- [ ] For the 4 mandatory targets (KRAS_G12C, BCR_ABL1, CARDIAC_MYOSIN,
      MYC_MAX): confirm on RCSB directly whether the `backend/systems.py`
      resolutions (AY7, 8QYR, MYC pocket=None) are correct, independent of
      trusting either doc.
  - CARDIAC_MYOSIN in particular: does the production app's `holo_validation`
    approach satisfy v2's quarantine condition ("confirmed"), or should it
    stay `verified=False`/excluded until someone explicitly re-checks 6C1H?
- [ ] Write `targets.yaml` for the 4 mandatory targets using
      `backend/systems.py`'s resolved apo/holo/chain/ligand values, but
      carrying forward v2's `warnings`/`confidence`/`keep_nucleic` fields
      (schema richer than the production dict).
- [ ] Add the 11 ASD draft entries from v2 as `status: draft` /
      `verified: false` entries — do not silently promote them to verified.
- [ ] Resolve the LDH apo-id inconsistency v2 flags (6LDH vs 1LDH in the prior
      version) or drop LDH per v2's own suggestion ("borderline allostery,
      candidate to drop").
- [ ] Add a `schema_version` + `source` provenance field per entry so future
      readers know which document (or a fresh RCSB check) an entry traces to.

## Dependency

- Blocks TASK-0004 (`labels.py`) and TASK-0005 (`superpose.py`) — both need
  per-target apo/holo/chain/keep_nucleic to run at all.
- Informs TASK-0002 (scaffold hygiene) if it surfaces further doc
  inconsistencies worth recording there instead of here.

## Open Questions

- Should `backend/systems.py` itself be regenerated from the finished
  `targets.yaml` + `labels.py` pipeline once that exists, so there's one
  source of truth instead of two independently-maintained target tables
  (production app vs research scaffold)? Flag for TASK-0002 if so — that's a
  scaffold/production boundary decision, not this task's call to make alone.
- p53-Y220C and the other MYC_MAX learning-base analogs from v2 — do they
  get their own `targets.yaml` entries now, or only if/when someone picks up
  the MYC learning-base work specifically?

## Done

(not yet)
