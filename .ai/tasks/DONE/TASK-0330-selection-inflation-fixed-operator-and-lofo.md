# TASK-0330 — Measure the selection inflation: one fixed operator, and leave-one-family-out

- Status: Done
- Owner: **Oussema** — Reviewer thread to review the design before the run
- Priority: High — decides whether the per-family Hamiltonian table can be shown at all
- Filed: 2026-09-06 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0300]], [[TASK-0301]], [[TASK-0314]], [[TASK-0199]], [[TASK-0207]], [[TASK-0328]]

## The exposure

Selection happens at four levels, and only the first is currently controlled:

1. **182 operator × score cells per protein** — controlled. `pocketsweep.py`
   compares the observed max against a **null max** over the same 182 cells.
   That is a correct within-protein multiplicity correction and stronger than
   this register's own default; say so.
2. **Per-family operator choice across proteins** — not controlled. "No single
   winner, but consistent groups" is what post-hoc partitioning looks like when
   the groups are read off the scores.
3. **Six new §14 scores** whose value is measured on the data that motivated
   them.
4. **"Best config: top-10, with veto"** chosen among configs (the upstream
   README shows four).

[[TASK-0314]] Part B states outright that this register has no family-wise
error control. [[TASK-0300]] and [[TASK-0301]] killed selection procedures for
exactly this shape — and [[TASK-0301]]'s lesson is the sharper one here: 61
rules all failed because all 61 were functions of the same two inputs, i.e.
one signal at 61 settings. This register's own effective-rank result
(**2.6–4.1 across ~28 observables**, [[TASK-0199]]/[[TASK-0207]]) says 182
cells are nothing like 182 independent chances either.

## Intent Contract

- Outcome: two numbers reported beside every per-family number.
  1. **One operator/score pair fixed in advance**, applied to every family.
     Pre-register the choice (or take the single best-on-average pair from
     round 1 and freeze it) before scoring.
  2. **Leave-one-family-out**: choose the operator on the other families,
     apply it cold to the held-out one.
  **The gap between the per-family picks and these two *is* the selection
  inflation**, and it is the number a reviewer will compute if we don't.
- Constraints And Invariants:
  - The per-family Hamiltonian table (`per_family_winners.csv`) **should not
    be shown externally until the LOFO number sits beside it.** Right now it
    is 182 cells selected on the same data they are scored on.
  - Family-level aggregation throughout — CAS0002 is 28 structures of one
    protein.
  - Report the chance floor with every P@5 ([[TASK-0327]]).
- Planned Validation: the fixed-operator arm must be run against the same
  compactness-matched null as [[TASK-0328]], not the uniform one.

## What a good outcome looks like

The upstream README already offers the honest reading — chance-corrected excess
**~+4 families over chance at P@5 ≥ 0.8, p ≈ 0.06**, and *"the defensible
reading is ~15 genuine families, not the raw count."* That framing survives
review. The raw threshold counts will not.

If the fixed-operator number survives a matched null **and** beats PASSer-only
([[TASK-0327]]), that is a genuinely new result nine days out and should lead
the submission. If it does not, the defensible instrument is still there:
PASSer top-10 at ~90% coverage plus a crypticity-aware veto, which is the same
crypticity split [[TASK-0254]] measured at 0.854 (open) vs 0.515 (cryptic).

## Closed without running — 2026-09-06, Reviewer thread

**Reason: the deliverable's target no longer exists.** This task's outcome was
a fixed-operator and leave-one-family-out number to sit *beside* the per-family
Hamiltonian table (`per_family_winners.csv`), so the selection inflation in
that table could be read off. Two results landed after filing and removed the
table from consideration entirely:

- [[TASK-0328]] — under a pocket-block (compactness-matched) null, BH-FDR 5%
  survivors fall from 45/110 to **0/110** (round 1) and 33/80 to **1/80**
  (round 2, veto). Essentially nothing in the sweep clears a null that respects
  the same spatial clustering the real positives show. There is no surviving
  per-family signal for a LOFO number to qualify.
- [[TASK-0327]] — on properly-defined held-out data (ASBench excluded as
  PASSer's training set), PASSer alone scores 28.1% pre-veto / 40.9% post-veto
  against the pipeline's 8.9% / 15.7%, with the pipeline below its own
  random-order null in both rounds. The pipeline is not a candidate for
  per-family operator attribution.

Running LOFO now would measure the selection inflation of a table that must not
be shown on independent grounds. That is effort spent qualifying a retracted
claim.

**What survives from this task, and where it went**: the constraint that the
per-family table "should not be shown externally until the LOFO number sits
beside it" is superseded by the stronger instruction — do not show it at all
pending [[TASK-0334]]/[[TASK-0335]]. Carried into [[TASK-0335]]'s sweep.

**Not closed by this**: the register-wide multiplicity concern ([[TASK-0314]]
Part B) is untouched and remains open on its own task. This closure is scoped
to the per-family Hamiltonian table only.
