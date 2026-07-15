# Q-0001 GLUCOKINASE's apo/holo structures use different chain IDs — `targets.yaml`'s single `chains` field can't express this

## Context

- ID: Q-0001 (code-reviewer addressee folder — first question filed here, folder
  created per `.ai/memory/questions/README.md`'s "create the first time a question
  needs one" rule)
- Status: Open
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

(empty — Status: Open)

## Action

(empty until answered)
