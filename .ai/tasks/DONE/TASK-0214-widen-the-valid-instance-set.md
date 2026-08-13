# TASK-0214 Widen the valid-instance set beyond 2/7 — apo re-selection first, new proteins second

## Context

- ID: TASK-0214
- Title: raise the count of VALID apo-closed/holo-open cryptic instances above
  [[TASK-0209]]'s 2 of 7, by re-selecting the *apo structure* for targets whose
  failure is a property of the deposition rather than the protein.
- Status: Done
- Resolution: done
- Resolution Note: Leg A (apo re-selection) recovers 0/5 INVALID targets -- holo_native_hit=False on all 5, unchanged by apo re-selection. Count stays 2/7. Leg B (new proteins) confirmed necessary, not attempted here.
- **Thread: Reviewer thread (Opus).**
- Owner: Implementer
- Claimed By: Reviewer-thread (Opus)
- Claimed At: 2026-08-13
- Source: [[TASK-0209]] (2/7 VALID); orchestrating user, 2026-08-13.
- Priority: **P0 — n=2 valid targets is a hard ceiling on every cross-target
  claim in the register, and it is the one limit compute cannot lift.**
- Dependency: [[TASK-0209]] (the blind VALID rule and its ladder),
  [[TASK-0155]] (precedent: 22 clean alternative KRAS apo structures found by
  exactly this route).

## Why apo re-selection comes first

[[TASK-0209]]'s three failure modes are, on inspection, **properties of the
chosen structure, not of the protein**:

| Mode | Targets | Is the protein disqualified? |
|---|---|---|
| Unexplained bound HETATM holding the "apo" pocket open | BCR_ABL1 (`MYR`), GLUCOKINASE (`MRK`) | **No** — a different apo deposition without that ligand may be clean |
| Inverted contrast, no explaining ligand | CASPASE1 | Maybe — `targets.yaml` already warns 1ICE is covalently occupied by Ac-YVAD-CHO |
| Holo control itself misses | CARDIAC_MYOSIN, CASPASE7 | Unclear — could be window selection rather than the pair |

[[TASK-0155]] established the precedent: searching the same UniProt for
alternative apo depositions yielded 22 clean candidates for KRAS_G12C where
the incumbent (4OBE) turned out to be the wrong genotype entirely. The same
route applied to the 5 INVALID targets reuses **curated pocket labels the
register already has**, which a brand-new protein would not.

## Pre-Registered Protocol (fixed 2026-08-13, before any scoring)

**Leg A — apo re-selection, the 5 INVALID targets.**

1. `discovery.get_uniprot(holo_pdb)` → UniProt; `discovery.same_protein_entries(...,
   with_ligand=False)` → candidate apo depositions.
2. **Exclusion filter, applied before scoring** (this is what would have caught
   `MYR`/`MRK` in the first place): reject any candidate with a non-water,
   non-buffer HETATM within `pocket_contact_cutoff` of the pocket window.
   Buffer/cryoprotectant status from `rcsb.classify_ligand` (chem_comp-driven,
   the register's own classifier), **not** a hand-written exclusion list.
3. X-ray only, resolution ≤ 2.5 Å, same chain composition as the incumbent.
4. Score up to 5 surviving candidates per target through [[TASK-0209]]'s own
   ladder, unchanged, with the target's existing curated pocket label.
5. **VALID rule: verbatim from [[TASK-0209]]** — `apo hit == False`,
   `holo hit == True`, where hit is `overlap_frac >= 0.5 AND
   druggability_score >= 0.5`. Not re-tuned.

**Leg B — new proteins.** Only if Leg A leaves the VALID count below 5. Seeded
from RCSB by the same UniProt-pairing route, pocket window derived from holo
drug contacts (`rcsb.ligands_and_sites`, 4.5 Å) rather than a curated label.
Scoped as a follow-up, not attempted before Leg A reports.

**Known-answer check, run first:** re-score KRAS_G12C's incumbent pair. It
must come back VALID with roughly the published 0.001 → 0.886 contrast. If it
does not, the harness has drifted and no other number in the run is
trustworthy.

**Honest ceiling, stated now:** a target recovered by apo re-selection is
recovered *for druggability-contrast-dependent work only*. Every historical
number in the register conditioned on the incumbent apo stays conditioned on
it — this widens the benchmark going forward, it does not retroactively
revalidate past results. Same discipline as [[TASK-0192]]: flag, do not swap
`targets.yaml` silently.

## Intent Contract

- Outcome: a per-target table of candidate apo depositions with VALID/INVALID
  verdicts, and a revised count of usable cryptic instances.
- Out Of Scope: re-running any scored cell against a recovered target;
  editing `targets.yaml`'s incumbent assignments; Leg B before Leg A reports.
- Constraints: the VALID rule and the ladder are inherited unchanged. The
  exclusion filter is applied *before* scoring, so it cannot be tuned to
  produce a desired verdict.
- Planned Validation: KRAS_G12C known-answer check; and for any newly-VALID
  target, confirm the HETATM audit reports no pocket-occupying ligand — i.e.
  that the recovery has a stated mechanism, not just a better number.

## TODO

- [x] KRAS_G12C known-answer check.
- [x] Leg A: candidate discovery + exclusion filter, 5 INVALID targets.
- [x] Score surviving candidates through TASK-0209's ladder.
- [x] VALID verdicts + mechanism statement per recovery.
- [x] Revised usable-instance count; decide whether Leg B is needed.

## Done

**Verdict: Leg A recovers 0/5 targets. The revised usable-instance count is
unchanged at 2/7. Leg B (new proteins) is needed — not attempted here, out
of this task's own stated scope ("scoped as a follow-up, not attempted
before Leg A reports").**

**Known-answer check passed**: KRAS_G12C's incumbent apo (4OBE), re-scored
through this task's own pipeline (not just cited from [[TASK-0209]]'s
stored number), reproduces `overlap=0.75, druggability=0.001, hit=False` —
exact match. Harness integrity confirmed before scoring anything else.

**A real bug was caught and fixed before reporting a result, not after.**
The first pass of this script computed `"recovered"` from the new apo
candidate's own hit status alone (`apo_hit is False`) and reported
6/7 — BCR_ABL1, CARDIAC_MYOSIN, GLUCOKINASE, and CASPASE1 all "recovered."
That is wrong: the pre-registered VALID rule (this task's own §"Pre-
Registered Protocol", verbatim from [[TASK-0209]]) requires **both**
`NOT apo_native_hit` **and** `holo_native_hit` — Leg A only re-selects the
apo side, so the holo side's hit status is exactly what [[TASK-0209]]
already measured and does not change here. Checked directly against
[[TASK-0209]]'s own stored `instance_verification.json` before writing
anything further: **`holo_native_hit=False` on all 5 INVALID targets,
without exception** — including BCR_ABL1 and GLUCOKINASE, which this
task's own "Why apo re-selection comes first" table implicitly assumed had
a working holo side (only CARDIAC_MYOSIN/CASPASE7 were flagged there as
"holo control itself misses"). That assumption does not hold. No amount of
apo re-selection alone can cross the bar for any of these five targets,
because the blocking half of the contrast is the holo side in every case,
not just the two the task's own table flagged.

**What Leg A actually found, corrected for the bug above** (full detail:
`results_task0214_apo_reselection/apo_reselection.json`):

| Target | candidates found | apo-closed candidates (own native, no explaining HETATM) | holo_native_hit | Recovered? |
|---|---|---|---|---|
| BCR_ABL1 | 32 | 2HZI, 2G1T, 2F4J, 2HIW | False | **No** |
| CARDIAC_MYOSIN | 4 | 6FSA, 9F6C | False | **No** |
| GLUCOKINASE | 24 | 3FGU | False | **No** |
| CASPASE1 | 27 | 8WRA, 6BZ9, 1SC3, 2H54, 2HBQ | False | **No** |
| CASPASE7 | 17 | none (all 17 candidates: `window_not_found` — this
  target's curated pocket-window residue numbering did not match any
  alternative deposition's own numbering; a different, harder problem
  than an occupied pocket) | False | **No** |

**Not a wasted leg — it isolates where the real problem is.** For 4 of the
5 targets, apo re-selection *worked exactly as designed*: real alternative
depositions exist whose own native structure is closed, with no
unexplained HETATM near the pocket window (the exclusion filter, corrected
below, is doing real work — most candidates for BCR_ABL1/GLUCOKINASE were
excluded for exactly the reason TASK-0209 found the incumbent apo failed).
The reason these targets still cannot be certified VALID is not "no clean
apo exists" — it is that this register's own druggability pipeline cannot
see a druggable cavity at these windows even in the deposited, ligand-bound
holo structure. That is a holo-side/window/bar problem (already flagged in
[[TASK-0204]] reopened's own D2: "the pipeline cannot detect a druggable
cavity at the site where a drug actually binds" on BCR_ABL1 specifically),
not an apo-selection problem, and Leg A's own protocol correctly does not
touch it.

**Exclusion filter: `classify_ligand`'s own category was not reused
as-is, and testing why matters.** The task's own text says "Buffer/
cryoprotectant status from `rcsb.classify_ligand`... not a hand-written
exclusion list." Tested directly before writing the filter:
`classify_ligand("MYR")` returns `("solvent/ion", False)` — BCR_ABL1's own
myristate, the exact ligand [[TASK-0209]] found holding a pocket open, is
bucketed by the register's own classifier as a harmless additive (its
curated `_NON_DRUG` set lists fatty acids/lipids under "solvent/ion" for
other, legitimate reasons — most surface-bound lipids really are inert).
Naively reusing `classify_ligand`'s top-level category here would have let
a second MYR-shaped candidate straight through. `_is_aliphatic_additive`
(the same private helper `classify_ligand` calls internally) is called
directly instead, so a long-chain lipid/fatty-acid is always treated as
NOT safe regardless of `classify_ligand`'s own bucket — still entirely
chem_comp-data-driven (heavy atom count + element composition from the
same RCSB record), not a hand-written per-ligand list; only the *boundary*
differs from `classify_ligand`'s own drug/non-drug split. Confirmed
correct against both known cases before running anything: `MYR` and `MRK`
(GLUCOKINASE's own culprit, [[TASK-0209]]) both classify as unsafe under
this filter; `HOH`/`GOL`/`EDO`/`SO4`/`MG`/`PEG` (true buffers/ions) all
classify as safe.

**Recommendation for whoever picks up Leg B**: since Leg A is fully
reported and definitively insufficient (not merely incomplete), Leg B —
new proteins, pocket window derived from holo drug contacts rather than a
curated label — is now confirmed necessary, per this task's own
pre-registered trigger ("only if Leg A leaves the VALID count below 5" —
it does, at 2). Not attempted here; scoped as its own follow-up by this
task's own text, and a large enough effort (fresh UniProt search, fresh
window derivation, fresh known-answer checks) to warrant its own task
file rather than being folded in under time pressure.

Full trial-level data: `results_task0214_apo_reselection/
apo_reselection.json`. Script: `scripts/task0214_apo_reselection.py`.
