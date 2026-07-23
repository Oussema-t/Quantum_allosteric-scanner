# TASK-0081 Generalization set (ASD targets)

## Context

- ID: TASK-0081
- Title: Run the frozen pipeline on 2–4 extra targets pulled from the
  Allosteric Database (ASD) with known sites, to evidence robustness and
  scalability beyond the required minimum set.
- Status: Done
- Owner: Implementer
- Source: `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` Phase 5, item 5.8 —
  "The brief **highly encourages** extra targets to demonstrate
  robustness/scalability. Pull 2–4 from the Allosteric Database with
  known sites. Cheap once 5.1 [TASK-0079] is a one-command run; directly
  feeds 'Technical Approach / Innovation'."

## Intent Contract

- Outcome: 2–4 additional targets from ASD (with known allosteric sites,
  i.e. real ground truth available, unlike TASK-0080's c-Myc case) added
  to `config/targets.yaml` and run through TASK-0079's end-to-end
  pipeline, producing the same three deliverables as the mandatory
  targets.
- In Scope: selecting the 2–4 targets (criteria: known allosteric site,
  reasonable size/complexity for the pipeline's current scope, ideally
  some diversity from the mandatory set's fold/mechanism types),
  `targets.yaml` entries, and the run itself.
- Out Of Scope: this task doesn't build new pipeline capability — it's
  purely additional coverage using what TASK-0079 already produces.
- Acceptance Scenarios:
  - Given 2–4 selected ASD targets, when run through the end-to-end
    pipeline, then each produces the same three deliverables (connectivity
    matrix, top-5 hits, methodological report) as the mandatory targets.
  - Given the results, then they're written up as evidence for the
    "Technical Approach / Innovation" rubric section the plan references.
- Constraints And Invariants: depends on TASK-0079 being a working
  one-command run first — "cheap once 5.1 is a one-command run" per the
  plan; don't start target selection work before that exists.
- **Added 2026-07-15, `REVIEW-2026-07-15-execution-plan-gap-audit.md`
  finding #4 (`TASK-0115`):** this task is more than "encouraged extra
  evidence" — it is the concrete mitigation for a repeated-exposure risk
  the review names: every claim in `RESULTS.md` so far has been shaped
  by ~15 review cycles that all looked at the same 3 mandatory targets'
  true labels. Treat no `RESULTS.md` claim as submission-final until it
  has been checked against this task's targets, which this review
  history has not seen. See `TASK-0115` for the protocol-note write-up
  this constraint is drawn from.
- Planned Validation: successful end-to-end run for each selected target,
  same acceptance bar as the mandatory-target runs.

## Dependency

- Depends on TASK-0079 (end-to-end challenge run) being Done.
- Feeds the submission's "Technical Approach / Innovation" writeup
  (whatever task or document assembles the final submission — not yet
  filed; flag if one doesn't exist by the time this lands).

## Open Questions

- **Resolved**: 2 targets, **PTP1B** and **CASPASE7** — see Done for
  selection rationale (most of the ASD-curated candidate pool turned out
  unusable for reasons discovered while vetting them, not because 2 was
  the target count from the start).

## Done

**Selection**: `config/targets.yaml` already carried 10 `draft`/unverified
ASD candidates from prior work (`TASK-0003`), not sourced from scratch.
Of those, 6 (ATCase, HEMOGLOBIN, GLYCOGEN_PHOSPHORYLASE, PFK,
GROEL_SUBUNIT, CASPASE1) carry their own explicit warning that allostery
is inter-subunit and single-chain analysis "destroys the mechanism" —
out of this task's "cheap" scope (would need biological-assembly
resolution work first). Of the remaining 4 (PTP1B, GLUCOKINASE,
TAR_RECEPTOR, CASPASE7), each was independently RCSB-verified (fetched
apo/holo directly, checked real chain IDs and hetero ligand records —
not trusted from either source doc):

| Target | Result |
|---|---|
| **PTP1B** | Verified clean: apo (1SUG) and holo (1T49) both chain A; ligand `892` confirmed present. **Used.** |
| **GLUCOKINASE** | New finding: apo (1V4S) is chain A, holo (3H1V) is chain X — both source docs' conflicting chain guesses were each individually correct, for different structures. `targets.yaml`'s single `chains` field can't express this. Not used; raised to Code Reviewer (`.ai/memory/questions/code-reviewer/open/Q-0001-...md`), not resolved unilaterally (a schema-level call). |
| **TAR_RECEPTOR** | New finding: holo (1VLT) has zero hetero ligand records at all — no bound aspartate detected, contrary to the config's own "Asp?" guess. Not used; stays draft/unconfirmed. |
| **CASPASE7** | Verified and corrected: `chains` resolved to `["A","B"]` (both required — this target's own allostery is dimer-interface, needs both subunits present to form a meaningful pocket, unlike PTP1B); `drug_ligand` resolved to `FXN` (the real hetero record in 1SHL — the config's own "FICA?" guess was unconfirmed and may be a literature name for the same compound, not reconciled, FXN used as the real RCSB code). **Used.** |

Ended at 2 targets, not 4, because half the initially-plausible pool
failed independent verification — reported as found, not backfilled
with a third/fourth weaker pick to hit a round number.

**Real bug found and fixed**: PTP1B's first run failed
(`RuntimeError: no resolvable drug_ligand`) despite `892` being
independently confirmed present in `1T49`. Root cause: `drug_ligand: 892`
unquoted in YAML parses as an integer, not a string — every downstream
`resname == ligand_code` comparison then silently fails (never raises,
just never matches), surfacing only as `build_labels`'s generic "no
resolvable drug_ligand" error several calls later. Fixed by quoting
(`"892"`); confirmed via direct YAML parse before re-running. Checked
every other `drug_ligand` value in the file — `892` was the only bare
numeric code, so no other entry was silently broken the same way.

**Real runs** (`run_challenge.py --target PTP1B CASPASE7`, live RCSB
fetch, `results_task0081/<target>/`):

| Target | N | Pocket size | Actual AUC | Max floor | Diagnosis |
|---|---|---|---|---|---|
| PTP1B | 298 | 14 | **0.2497** | 0.4847 | `BEATS_CHANCE_NOT_FLOOR` |
| CASPASE7 | 461 | 7 | 0.7130 | 0.7565 | `BEATS_CHANCE_NOT_FLOOR` |

Both deliverables verified by direct load: connectivity matrices
`(298,298)`/`(461,461)`, symmetric, zero diagonal; hit lists have 5 real
resnums each (PTP1B: 52/35/70/50/67; CASPASE7: 265/225/289/263/269).

**PTP1B's result is a distinct, more striking finding than "beats chance
not floor" alone conveys**: 0.2497 is not merely below its floor, it is
**anti-correlated** with the true pocket (well below 0.5 — the method
actively scores the known allosteric BB site *lower* than average, not
just indistinguishably-from-average). `classify_failure`'s vocabulary
does not distinguish "beats chance" (deviates from 0.5, either
direction) from "beats chance in the informative direction" — both
currently route through the same `BEATS_CHANCE_NOT_FLOOR` label; not a
bug in that function (its own chance-check is symmetric by design), but
worth a human reader knowing before treating this diagnosis label as
uniformly meaning "positively correlated but modest." PTP1B's allosteric
site sits ~20 A from the catalytic Cys215 (config's own `objective`
field) — genuinely distal, structurally the same category as BCR_ABL1's
myristoyl site (also distal, also near-chance/`NO_SIGNAL_IN_APO`). This
is real, independent, cross-target corroboration of this project's
central cross-target pattern (adjacent pockets score artificially high
via proximity; distal pockets score at or below chance) — on a target
none of this session's ~15 prior review cycles have seen, exactly the
mitigation `TASK-0115` names this task as providing.

**CASPASE7** clears chance with a real, positively-correlated signal
(0.7130) but falls short of its own floor (0.7565, margin -0.0435) —
consistent with the mandatory-set pattern (raw AUC without a proximity
floor overstates apparent signal) generalizing to a genuinely different
fold/mechanism class (oligomeric protease, dimer-interface allostery,
vs. the mandatory set's GTPase/kinase/motor proteins).

**Cross-target reading**: both new targets land in the same
`BEATS_CHANCE_NOT_FLOOR` category the mandatory set's KRAS_G12C already
occupies — no ASD generalization target in this pass produced a
floor-clearing positive result, consistent with (not contradicting)
`COMPETENCE_MAP.md`'s mandatory-target headline. `COMPETENCE_MAP.md`'s
"Generalization targets" placeholder section updated with these real
rows (no longer a stub).

**Acceptance Scenarios**: met — both targets produced all three
deliverables; results written up here and cross-linked from
`COMPETENCE_MAP.md` for the "Technical Approach / Innovation" rubric
section.

**Full-suite regression check**: running these targets surfaced a real
dispatch bug in `TASK-0080`'s no-ground-truth branch (a pre-existing
test fixture missing `holo_pdb` entirely was silently misrouted) — see
`TASK-0080`'s Done addendum for the finding and fix. `.venv/bin/python3
-m pytest -q tests/ -k "not real_target and not kras_g12c_real and not
real_run and not fetch"` — 581 passed after the fix, 0 failed.

**Addendum, [[TASK-0115]], 2026-07-23**: this generalization set (later
extended by [[TASK-0127]] to 4 targets and promoted to the reported
headline) is this project's actual mitigation for the repeated-exposure
risk named by TASK-0115 — a target set this project's own ~15-cycle
review history has never seen, unlike the mandatory 3. Formalized in
`INVARIANCE_PROTOCOL.md`'s new "Repeated-exposure risk" section: no
`RESULTS.md` claim about robustness/generalizability is submission-final
without checking it against this set, not merely "encouraged extra
evidence" per the brief's own wording.
