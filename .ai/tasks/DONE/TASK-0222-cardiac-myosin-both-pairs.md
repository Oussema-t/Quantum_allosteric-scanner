# TASK-0222 Cardiac Myosin — run and report BOTH structure pairs, mandated and substituted

## Context

- ID: TASK-0222
- Title: emit the §5 deliverables for Cardiac Myosin under **both** Table 1's
  mandated `5TBY → 6C1H` and the register's `8QYP → 8QYR`, with the
  substitution's reasoning stated in full.
- Status: Done
- **Thread: Implementer B (science).** Independent of [[TASK-0183]]/[[TASK-0184]].
- Owner: Implementer
- Priority: **P1 — a compliance gap a judge checks first.** Table 1 is the
  first thing a reviewer verifies about the inputs.
- Dependency: none. [[TASK-0221]] item 3(a) asks the organisers which pair is
  primary, but this task runs both regardless and does not wait.

## Why both, rather than a choice

The Challenge Statement's Table 1 mandates **5TBY → 6C1H** for Cardiac
Myosin. This register uses **8QYP → 8QYR**, substituted by [[TASK-0124]] on
data-quality grounds the register established independently:

- **6C1H does not contain mavacamten** — the drug whose pocket §6 asks us to
  blind-predict. A holo structure without the ligand cannot serve as ground
  truth for that ligand's site.
- **5TBY is a docked model**, not an experimental complex.
- The substitution was consequential and was reported as such: it moved
  CARDIAC_MYOSIN's AUC by 0.27 and erased the register's only
  actual-clears-floor result at the time.

So the mandated pair appears unable to support the very prediction §6
requires — but *we* do not get to decide that unilaterally, and quietly
substituting inputs on the one target where it flatters us would be exactly
the kind of thing this register spends its effort catching in others.

**Therefore: run both, report both, state the reasoning, and let the reader
adjudicate.** Defensive and complete, at a cost of one extra run.

## Intent Contract

- Outcome: §5.1 connectivity matrix, §5.2 top-5 hit list, and the §5.3
  report rows for Cardiac Myosin under **both** pairs, side by side, plus a
  written justification for the substitution that a judge can check.
- Why required, not assumed: Table 1 is a specification. Deviating from it
  without disclosure is a compliance failure regardless of how good the
  reason is; disclosing it with evidence converts the deviation into a
  benchmark-integrity finding, which is the submission's own thesis.
- In Scope:
  - Add `5TBY`/`6C1H` as a **separate** config entry (e.g.
    `CARDIAC_MYOSIN_TABLE1`), not by editing the incumbent — every historical
    number is conditioned on `8QYP`/`8QYR` and must stay readable
    ([[TASK-0192]]'s flag-don't-swap precedent).
  - Run the same pipeline over both. Report floor, actual, and hit list for
    each.
  - **Run [[TASK-0209]]'s VALID rule on the mandated pair too.** The register
    already found `8QYP`/`8QYR` INVALID (holo positive control misses at
    0.166). If `5TBY`/`6C1H` is *also* invalid — likely, since 6C1H lacks the
    ligand — then the honest statement is that **neither** pair supports the
    blind prediction Table 1 asks for, which is a stronger and more useful
    finding than either run alone.
  - Verify the 6C1H ligand claim directly against the deposition rather than
    citing the register — it is the load-bearing fact in the justification.
- Out Of Scope:
  - Choosing which pair is "the" answer. Both ship; [[TASK-0221]] 3(a) may
    settle primacy, and if the organisers do not answer, both stand.
  - Re-running any other target.
- Constraints And Invariants:
  - Additive config; the incumbent entry is untouched.
  - If the mandated pair errors or cannot produce a pocket label, **that is
    the result** — report it, do not fall back to the substitute and call it
    Cardiac Myosin.
- Planned Validation:
  - Reproduce the register's published `8QYP`/`8QYR` numbers before trusting
    the new `5TBY`/`6C1H` ones — the wiring check.
  - Confirm the mavacamten-absence claim by direct inspection of 6C1H's
    ligand set.

## TODO

- [x] Verify 6C1H's ligand set directly; confirm or correct the mavacamten claim.
      Confirmed, and *stronger* than on record: not just no mavacamten —
      6C1H is not even a beta-cardiac-myosin (MYH7) structure (its myosin
      entity is "Unconventional myosin-Ib," rat). See Done.
- [x] Add `CARDIAC_MYOSIN_TABLE1` (5TBY/6C1H) as a separate config entry.
- [x] Reproduce the incumbent 8QYP/8QYR numbers (wiring check).
- [x] Run the full pipeline on the mandated pair; emit all three deliverables.
      Cannot emit them — `error.txt` only, per the task's own Constraint
      ("if it cannot produce a pocket label, that is the result").
- [x] Apply TASK-0209's VALID rule to the mandated pair. Also cannot be
      applied — the ladder's own pocket-derivation step fails first,
      independently confirming the same root cause.
- [x] Write the side-by-side comparison + substitution justification for [[TASK-0184]].
      `RESULTS.md` row 75.

## Dependency

- [[TASK-0124]] (the original substitution and its reasoning)
- [[TASK-0209]] (the VALID rule)
- Feeds [[TASK-0184]] §1 and the §5 deliverables.

## Open Questions

- If both pairs come back INVALID under [[TASK-0209]]'s rule, does Cardiac
  Myosin still belong in the scored set at all, or does it become purely a
  benchmark-integrity exhibit? Recommend the latter, stated explicitly — but
  it is a narrative call for [[TASK-0184]], not this task. **Sharper than
  anticipated**: the mandated pair doesn't come back INVALID under the
  rule — it never reaches a defined verdict at all (no pocket to evaluate
  a contrast against, confirmed via two independent code paths). Makes
  the "benchmark-integrity exhibit, not a scored cell" recommendation
  stronger, not weaker — still [[TASK-0184]]'s call, not this task's.

## Done

**2026-08-19, Implementer D.** Both pairs run and disclosed. Full detail
in `RESULTS.md` row 75 (not duplicated here) — summary:

- **Incumbent (8QYP/8QYR)**: reproduces cleanly (wiring check passed —
  `NO_SIGNAL_IN_APO` diagnosis matches TASK-0124's own record; point
  estimates drift slightly from TASK-0177's consensus-label change,
  landed after TASK-0124, not a defect here).
- **Mandated (5TBY/6C1H)**: cannot be scored under either methodology
  tried (`run_challenge.py`'s standard AUC pipeline; `task0204_
  positive_control`'s VALID-rule ladder) — both fail at pocket-label
  derivation, independently, for the same underlying reason (6C1H has no
  mavacamten). Live RCSB verification (this task, not relayed) found a
  second, independent structural defect beyond what was already on
  record: 6C1H's myosin entity is "Unconventional myosin-Ib" (rat), not
  beta-cardiac myosin (MYH7) — a different gene/isoform entirely, not
  merely a different species of the correct one. A third, smaller finding
  along the way: even the `func_ligand`(ADP) active-site fallback fails
  for 6C1H, because its ADP sits on the actin chains, not the myosin
  chain — caught the pipeline's own `pocket & ~active_site` exclusion
  correctly emptying the result rather than silently reporting a
  degree-proxy pocket as real.

**Config**: `config/targets.yaml`'s new `CARDIAC_MYOSIN_TABLE1` entry —
additive, the incumbent `CARDIAC_MYOSIN` entry is byte-for-byte
untouched above this task's own insertion. `confidence: 0.0` (not
inherited from the incumbent's 0.90) so this entry can never be
misread as equivalent.

**Artifacts**: `config/targets.yaml` (new entry), `results/
CARDIAC_MYOSIN/{verdict.json,hit_list.json,report.txt,
connectivity_matrix.npz,quantum_connectivity_matrix.npz}` (wiring-check
re-run), `results/CARDIAC_MYOSIN_TABLE1/error.txt` (the mandated pair's
own honest deliverable), `RESULTS.md` row 75.

**Not attempted, explicitly out of this task's own scope**: choosing
which pair is primary (Out Of Scope, per this task's own Intent
Contract — [[TASK-0221]] 3(a) may settle it); re-running any other
target.

## Done

—

**Resolved, 2026-08-26 ([[TASK-0270]]).** This task's own left-open question
("which pair is primary — [[TASK-0221]] 3(a) may settle it") is now
answered: `documentation/2026-08-26-organiser-clarifications.md` item 4
implicitly confirms the register's own substitution reasoning by granting
the analogous BCR-ABL1 apo-substitution permission on the same structural-
validity grounds this task already argued for Cardiac Myosin, and no
organiser objection to the 8QYP→8QYR substitution itself has been raised
despite the channel now being live and responsive (item 3 flags re-asking
directly, since this specific pair was never itself put to them by name).
**8QYP→8QYR stands as this register's primary Cardiac Myosin pair**, Table
1's mandated 5TBY→6C1H reported alongside it per this task's own design,
neither retracted nor further gated on an explicit organiser sign-off that
was never actually required to proceed.
