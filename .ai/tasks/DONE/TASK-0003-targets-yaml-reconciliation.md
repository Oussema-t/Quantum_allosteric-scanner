# TASK-0003 Reconcile and Author `config/targets.yaml`

## Context

- ID: TASK-0003
- Title: Produce `__WORK_IN_PROGRESS__/config/targets.yaml`, reconciling
  `__WORK_IN_PROGRESS__/SYSTEMS_allosteric_corrected_v2.md` against the
  production `backend/systems.py`
- Status: Done
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

## TODO (resolved 2026-07-06, Implementer A)

- [x] For the 4 mandatory targets (KRAS_G12C, BCR_ABL1, CARDIAC_MYOSIN,
      MYC_MAX): confirm on RCSB directly whether the `backend/systems.py`
      resolutions (AY7, 8QYR, MYC pocket=None) are correct, independent of
      trusting either doc.
  - RCSB-reconfirmed via `data.rcsb.org`/`rcsb.org` REST+structure-page
    fetches on 2026-07-06:
    - 6OIM: `nonpolymer_bound_components` = GDP, MG, MOV; MOV = sotorasib.
      Matches both docs.
    - 5MO4: title "ABL1 kinase (T334I_D382N) in complex with asciminib and
      nilotinib"; ligands AY7=asciminib, NIL=nilotinib, chain B (auth A).
      Resolves v2's *** CRITICAL FIX *** placeholder — AY7 confirmed
      correct. T334I/D382N is a consistent +19 shift from lit T315I/D363N
      (the documented ABL1 1a/1b offset), not a doc error.
    - 6C1H: confirmed NOT mavacamten-bound (actin + myosin-1b(rat) +
      calmodulin + ADP/MG only) — matches both docs' "unusable" note.
    - 8QYR: confirmed real *Bos taurus* MYH7, 1.80 Å X-ray, XB2
      (mavacamten) bound to chain B (auth) — matches
      `holo_validation`/`holo_validation_chain` in `backend/systems.py`.
    - 5TBY (apo): confirmed 20.0 Å cryo-EM IHM assembly (6 chains,
      homology model docked to EMD-2240) — the apo-construct concern v2
      raised is real and left **open** (not resolved by this task); see
      `CARDIAC_MYOSIN.confidence=0.65` and its warnings in `targets.yaml`.
    - 1NKP: confirmed 2 protein entities + 1 DNA entity (cMyc/Max/DNA),
      consistent with both docs' chain layout.
  - CARDIAC_MYOSIN verdict: v2's quarantine condition ("confirm 6C1H
    actually contains mavacamten") is satisfied by confirming the
    negative — it does not, and the `holo_validation=8QYR` substitute is
    independently confirmed genuine. Quarantine lifted (`quarantine:
    false`), but confidence held at 0.65 (not promoted to the ~0.90-0.95
    of the other 3) because the apo 5TBY IHM/homology-model concern is a
    distinct, still-open issue.
- [x] Write `targets.yaml` for the 4 mandatory targets using
      `backend/systems.py`'s resolved apo/holo/chain/ligand values, but
      carrying forward v2's `warnings`/`confidence`/`keep_nucleic` fields
      (schema richer than the production dict).
  - Done in `__WORK_IN_PROGRESS__/config/targets.yaml`. One deliberate
    deviation from straight "trust production": MYC_MAX uses
    `chains: ["A", "B"]` (v2's Myc+Max heterodimer pairing) instead of
    `backend/systems.py`'s `chain="A"`, because that production field
    contradicts its own inline note (`"Use chain='A,D'"` — two Myc copies,
    no Max at all). Flagged in the entry's `warnings` for anyone who wants
    to revisit it.
  - No hand-transcribed pocket-residue numbers were added anywhere,
    including `covalent_anchor`/`active_site` residue lists from
    `backend/systems.py` — per the Intent Contract's constraint, those
    stay out of this file entirely (narrative mentions like "Cys12" in
    `objective` text are carried-forward context, same style v2 itself
    uses, not structured residue fields).
- [x] Add the 11 ASD draft entries from v2 as `status: draft` /
      `verified: false` entries — do not silently promote them to verified.
  - All 11 added (PTP1B, GLUCOKINASE, ATCase, CASPASE1, CASPASE7,
    HEMOGLOBIN, TAR_RECEPTOR, GLYCOGEN_PHOSPHORYLASE, PFK, GROEL_SUBUNIT,
    and LDH — LDH then dropped, see below). PTP1B/GLUCOKINASE carry
    `backend/systems.py`'s already-resolved `drug_ligand` values (892,
    TK1) as *candidates* only, explicitly flagged as not RCSB-rechecked
    this pass, and still `status: draft` — this task's RCSB re-check was
    scoped to the 4 mandatory targets only, not the ASD expansion.
  - `GLUCOKINASE.chains` left `null`: v2 says chain "A", `backend/
    systems.py` says chain "X" — genuine conflict, not guessed.
- [x] Resolve the LDH apo-id inconsistency v2 flags (6LDH vs 1LDH in the prior
      version) or drop LDH per v2's own suggestion ("borderline allostery,
      candidate to drop").
  - Dropped, per v2's own suggestion (lowest confidence of any ASD
    candidate, 0.35) rather than guessing between the two apo IDs.
    Documented under `omitted_targets.LDH` in `targets.yaml` with
    rationale and a re-add condition, not silently removed.
- [x] Add a `schema_version` + `source` provenance field per entry so future
      readers know which document (or a fresh RCSB check) an entry traces to.
  - `schema_version: 1` at file top; every entry (including omitted) has a
    `source` string naming its source doc(s) and whether TASK-0003
    independently RCSB-rechecked it.

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
  the MYC learning-base work specifically? **Not resolved by this task** —
  left for whoever picks up the MYC learning-base work.
- The `backend/systems.py::pocket_full`/`pocket_distal` provenance check
  (does it actually come from a 4.5 Å holo-contact derivation, per the
  Intent Contract's "Do not assume; check" note) was **not** performed —
  it's out of this task's scope (no pocket-residue fields exist in
  `targets.yaml` at all) and belongs to TASK-0004 (`labels.py`) once that
  derivation exists to compare against.
- New gap found, not previously tracked: `__WORK_IN_PROGRESS__/` has no
  `requirements.txt`/`pyproject.toml` of its own — its `.venv` existed but
  lacked `pyyaml` (added this session, user-approved) and lacks `prody`
  (needed by `clean()` itself, untested this session — only
  `load_target_config()` was exercised). Worth a follow-up task if
  `__WORK_IN_PROGRESS__` is meant to be independently runnable.

## Done

- `__WORK_IN_PROGRESS__/config/targets.yaml` written: 4 mandatory targets
  (all RCSB-reconfirmed 2026-07-06) + 11 ASD draft entries − 1 dropped
  (LDH, documented under `omitted_targets`) = 14 live target entries.
- Planned Validation executed and passed: a scratch script
  (session-local, not committed to the repo) called
  `allostery.clean.load_target_config(name, config_path=...)` for all 14
  targets against the new file using the `__WORK_IN_PROGRESS__/.venv`
  Python (after installing `pyyaml` there, user-approved) — all 14 loaded
  without error, none quarantined, `omitted_targets` correctly excludes
  LDH. Confirms `clean_from_config()`'s consumed fields
  (`apo_pdb`/`holo_pdb`/`chains`/`keep_nucleic`/`quarantine`) are present
  and well-typed for every entry.
- Every conflict the task file's comparison table raised was resolved
  explicitly (not auto-merged) and the resolution is recorded either
  inline in `targets.yaml`'s per-entry `warnings`/`source` fields or in
  the TODO section above: BCR_ABL1 ligand code, CARDIAC_MYOSIN
  quarantine/confidence, MYC_MAX chain pairing + pocket-non-applicability,
  ASD-entry draft status, LDH inconsistency.
- Follow-up (2026-07-06, same day): the throwaway validation script above
  had no permanent regression coverage, so
  `__WORK_IN_PROGRESS__/tests/test_targets_config.py` (38 tests) was added:
  `load_target_config()` succeeds for all 14 live targets and raises
  `KeyError` for an unknown one; LDH is absent from `targets` but present
  under `omitted_targets` with a reason; no entry carries a
  hand-transcribed residue field (`pocket_full`/`active_site`/
  `covalent_anchor`/etc. — the file's central invariant); the 4 mandatory
  targets are not quarantined and the 10 ASD entries are `status: draft`/
  `verified: false`; and the specific RCSB-reconfirmed facts from this
  task (KRAS_G12C anchors, BCR_ABL1's resolved AY7 code, CARDIAC_MYOSIN's
  8QYR/6C1H split + confidence<0.9, MYC_MAX's chain pairing/no-pocket
  flags) are pinned as regression checks. Run:
  `.venv/bin/python3 -m pytest tests/test_targets_config.py -q` from
  `__WORK_IN_PROGRESS__/` — 38 passed. Self-contained (inserts `src/` onto
  `sys.path` itself) because no repo-wide pytest path config exists yet
  (see the `requirements.txt`/pytest-config gap noted above) — the
  existing `test_hamiltonians.py`/`test_labels.py`/`test_physics.py`/
  `test_potentials.py` all currently fail collection the same way
  (`ModuleNotFoundError: No module named 'allostery'`) when pytest is run
  without a manually-set `PYTHONPATH`; fixing that repo-wide is out of
  this task's scope and was left as-is to avoid touching shared test
  config mid-session while another thread (Implementer B, TASK-0004) had
  `tests/test_labels.py` open concurrently.
