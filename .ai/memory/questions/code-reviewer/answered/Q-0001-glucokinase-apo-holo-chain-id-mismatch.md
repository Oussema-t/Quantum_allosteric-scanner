# Q-0001 GLUCOKINASE's apo/holo structures use different chain IDs — `targets.yaml`'s single `chains` field can't express this

## Context

- ID: Q-0001 (code-reviewer addressee folder — first question filed here, folder
  created per `.ai/memory/questions/README.md`'s "create the first time a question
  needs one" rule)
- Status: Answered
- Addressee: Code Reviewer
- Raised By: Implementer C, 2026-07-15
- Related: [[TASK-0081]] (generalization set, ASD targets, in progress),
  [[TASK-0003]] (targets.yaml reconciliation, Done — originally curated
  this entry as `draft`/`unverified`)

## Question

`config/targets.yaml`'s `GLUCOKINASE` entry has `chains: null` with a
comment flagging an unresolved conflict between two source docs
(`SYSTEMS_allosteric_corrected_v2.md` says `"A"`, `backend/systems.py`
says `"X"`). Checked directly against real RCSB data (not either source
doc): **both are right, for different structures** — apo (`1V4S`) has
only chain `A`; holo (`3H1V`) has only chain `X`. `run_challenge.py`'s
`_load_apo_holo` (and `clean_from_config` generally) uses one shared
`target_config["chains"]` list to select chains from *both* apo and
holo independently — there is no schema field for "chain A in apo maps
to chain X in holo." Is this:

1. A real, structural gap in `targets.yaml`'s schema (should gain a
   per-role chain field, e.g. `apo_chains`/`holo_chains`, generalizing
   past this one target) that's worth a task on its own, or
2. Not worth generalizing the schema for one target — better to leave
   `GLUCOKINASE` in `omitted_targets` (like `LDH` already is, for its own
   apo-ID ambiguity) with this finding as the documented reason, and
   revisit only if a future target hits the same shape?

I did not attempt either fix myself — this is a schema-level call
(affects every target's config, not just this one), which felt like the
Code Reviewer/Architect's decision to make, not an implementer's to
guess at while assembling a generalization-set run.

## Background

TASK-0081 (generalization set: 2-4 ASD targets, real ground truth, run
through the existing end-to-end pipeline) is selecting from `targets.yaml`'s
already-curated `draft` entries (`TASK-0003`'s prior work) rather than
sourcing new targets from scratch. Of the 10 draft ASD candidates, most
carry an explicit warning that allostery is inter-subunit and requires
the full oligomeric assembly ("single-chain analysis destroys the
mechanism" — ATCase, HEMOGLOBIN, GLYCOGEN_PHOSPHORYLASE, PFK,
GROEL_SUBUNIT, CASPASE1/7 all carry some form of this warning), which
is out of this task's "cheap, one-command run" scope. `PTP1B` and
`GLUCOKINASE` are the two monomeric, single-chain-valid candidates.

`PTP1B` was independently RCSB-verified this session: apo (`1SUG`) and
holo (`1T49`) both use chain `A`; `drug_ligand: 892` (previously flagged
"NOT RCSB-rechecked") is confirmed present in `1T49`'s hetero records.
Clean, ready to use.

`GLUCOKINASE` failed the same check for a reason neither source doc
anticipated — not "which letter is correct" but "both letters are
correct, on different structures," which is a schema expressiveness gap,
not a data-entry error. `TAR_RECEPTOR` is being used as a third
candidate instead (weaker evidence — `drug_ligand` still unconfirmed,
transmembrane, confidence 0.45 — reported as such in TASK-0081's own
write-up, not silently substituted for GLUCOKINASE without a note).

## Answer

**Answered by Implementer C, 2026-07-18, TASK-0127.** Option 1 — a real
schema gap, worth generalizing past this one target. Added optional
`apo_chains`/`holo_chains` per-role override fields: `clean_from_config`
now reads `cfg.get(f"{role}_chains", cfg.get("chains"))` instead of always
reading the shared `chains` field. Additive and fully backward-compatible
— every target that only ever set `chains` (all 13 others) is unaffected,
verified by a new `chains` == `chains` fallback test
(`test_clean.py::test_falls_back_to_shared_chains_when_no_per_role_override`).
`GLUCOKINASE` now sets `apo_chains: ["A"]`, `holo_chains: ["X"]`, matching
TASK-0081's own already-confirmed real data, and is promoted from `draft`
to `verified: true`.

## Action

`__WORK_IN_PROGRESS__/src/allostery/clean.py::clean_from_config` — added
the per-role fallback (5 lines). `__WORK_IN_PROGRESS__/tests/test_clean.py`
— new file, 5 tests covering the override/fallback logic without a live
RCSB fetch. `config/targets.yaml`'s `GLUCOKINASE` entry updated. See
[[TASK-0127]]'s Done section for the real end-to-end run this unblocked.
