# TASK-0359 — Limited cohort extension by distinct protein, not by structure

- Status: TODO
- Owner: **Implementer**
- Priority: **High — but hard-capped by the 2026-09-15 deadline; see Budget**
- Filed: 2026-09-09 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0308]], [[TASK-0310]], [[TASK-0350]], [[TASK-0357]], [[TASK-0358]], [[TASK-0337]], [[HYP-P13]]

## Why: our power is limited by proteins, and we have been adding structures

Every quantum-arm null in this register — [[TASK-0350]]'s coherent/decoherent
result, [[TASK-0357]]'s single-delay run, [[TASK-0358]]'s eleven-point scan — is
computed on the **same 108 structures in 76 clusters**. That is **1.42 structures
per cluster**: the cohort is already nearly one-structure-per-protein, so adding
more *structures* buys almost no independent information while inflating the row
count that cluster-permutation has to discount.

**What limits every one of those p-values is the number of distinct proteins, not
the number of structures.** An extension that adds PDB entries for proteins we
already have makes the cohort look bigger and tests nothing new.

### The specific question this unblocks

The external `allosteric` branch reports a family-level effect (+0.107, p=0.007)
that this register cannot reproduce at any delay. Their own document contains the
signature that would explain it:

> *CAS0002 dominance: 28 of 91 distal structures are one protein. Without it CTQW
> 0.617 -> 0.501.*

One family carrying an effect is exactly the "the observable separates **proteins**
rather than **sites within a protein**" failure mode — and leave-one-family-out
does not protect against it, because holding a family out does not remove a
per-family baseline offset from the families that remain. **Testing that requires
more independent proteins. It cannot be answered by more structures of the ones we
have.**

## Intent Contract

- **Outcome:** a cohort extended along the axis that actually carries power —
  distinct proteins — plus the first test of whether our observables separate
  proteins rather than sites.
- **In scope:**
  1. **Add distinct proteins only.** Selection key is the protein (UniProt
     accession / sequence cluster), **not** the PDB entry. A candidate whose
     protein is already represented in the 108 is **rejected**, however good the
     structure. Target: **+40 to +60 distinct proteins**, drawn from the benchmark
     sources already in use — no new benchmark, no new label convention.
  2. **Audit the additions the same way the existing cohort was audited.** 40 of
     40 ASBench structures in the current cohort carry a ligand at the scored
     site; new entries are **not** assumed clean. Apply the existing contamination
     audit and report the contaminated fraction of the extension separately from
     the fraction of the original — do not merge them into one number.
  3. **Re-run exactly two things on the extended cohort**, both existing validated
     code paths, nothing new built:
     - [[TASK-0350]]'s coherent vs decoherent comparison.
     - [[TASK-0358]]'s tau-scan **anchor point only** (`f=1`), signed and unsigned,
       not the full eleven-point scan.
  4. **The protein-vs-site separation test** — the one genuinely new measurement:
     does the score separate *proteins from each other* better than it separates
     *sites within a protein*? State the statistic before running it. A score that
     discriminates protein identity but not within-protein site location is a
     classifier, not a locator, and every family-level p-value in this register
     inherits the finding.
- **Out of scope:**
  - Rebuilding the `allosteric` branch's 435 MIN_HOP=2 structures. Still not worth
    it, and [[TASK-0358]] made it their experiment to run, not ours.
  - Adding structures for proteins already present, for any reason.
  - Reselecting the operator (Tier-2-gated, [[TASK-0100]]).
  - The held `+0.031`. Unchanged.
- **Constraints and invariants:** same labels, same scoring, same cluster-
  permutation convention ([[TASK-0337]]); the original 108 must reproduce their
  committed numbers **unchanged** within the extended cohort before any pooled
  number is quoted.
- **Planned Validation:** the 108 original structures, scored inside the extended
  cohort, must reproduce [[TASK-0358]]'s committed `f=1` values (signed raw 0.5031
  / rho -0.0157 / resid 0.5018; unsigned raw 0.5797 / rho 0.3466 / resid 0.5287).
  If they do not, the extension has changed something it should not have, and the
  task stops there.

## Pre-registered prediction

Recorded before the run, and deliberately two-sided. If the nulls hold on a cohort
with ~50% more independent proteins, they get materially stronger and the
submission can say so. If the protein-vs-site test shows our scores separate
proteins better than sites, that is a **finding about every family-level number in
this register**, ours included — not a point scored against the other branch.

## Budget — read before claiming

Six days to the deadline. **This task is capped, not open-ended.** If protein
selection and the contamination audit alone consume more than one working day,
stop and report the extension as filed-but-unrun rather than delivering a
half-audited cohort. A contaminated extension is worse than no extension, because
every pooled number would inherit the contamination silently.

## Dependency

- [[TASK-0358]] (Done) — the harness, the anchor values, and the reason this is
  the right axis.
- [[TASK-0308]]/[[TASK-0310]] (Done) — the existing cohort and its scoring.
- Contamination audit convention — the 40/40 ASBench finding this extension must
  not quietly undo.

## Staged Files

- [2026-09-09 20:26] `__WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V3.md` -- rewrite the QAOA non-proposal; name the two surviving quantum routes
- [2026-09-09 20:26] `__WORK_IN_PROGRESS__/documentation/2026-09-09-allosteric-branch-message-DRAFT.md` -- message draft to the allosteric branch, not sent
- [2026-09-09 20:26] `.ai/COMMON.md` -- registry row
- [2026-09-09 20:26] `.ai/tasks/TODO/TASK-0359-cohort-extension-by-protein-not-by-structure.md` -- the task file itself
