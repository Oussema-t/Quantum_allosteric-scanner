# TASK-0192 Propagate the KRAS_G12C wrong-genotype finding out of `RESULTS.md`

## Context

- ID: TASK-0192
- Title: flag or correct `apo_pdb: 4OBE` everywhere it is used as a "KRAS
  G12C" structure — research config, live backend, public docs, and
  `COMPETENCE_MAP.md`'s headline table.
- Status: TODO
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: [[TASK-0155]] (Done, 2026-07-30); Reviewer thread, 2026-08-03,
  finding F4 (independently re-verified).
- Priority: **P0 — cheap, and one of the affected surfaces is the live
  jury-facing web app.**
- Dependency: none.

## Why this matters

[[TASK-0155]] found that `targets.yaml`'s `apo_pdb: 4OBE` is **wild-type**,
not G12C. **Independently re-verified by the Reviewer thread**, directly
against the local `4obe.pdb`: chain A residue 12 is `GLY`, not `CYS`. The
finding is correct.

It is documented in `RESULTS.md` and in the open-questions index. It has
propagated **nowhere else**:

| Surface | Current state |
|---|---|
| `__WORK_IN_PROGRESS__/config/targets.yaml:58` | `apo_pdb: 4OBE`, no note |
| `backend/systems.py:19-22` | ships 4OBE as the KRAS_G12C apo **with `covalent_anchor=12`** — i.e. the live app asserts a covalent Cys12 anchor on a Gly12 structure |
| `SOFTWARE.md:222` | benchmark table lists 4OBE as the KRAS_G12C apo |
| `COMPETENCE_MAP.md` | **zero** mentions of [[TASK-0155]], "lucky draw", "genotype", or 4OBE's status |

The `COMPETENCE_MAP.md` gap is the serious one. Its current table (the
[[TASK-0130]] closed-form recompute) carries KRAS_G12C as the project's
**only** `NO_FAILURE_DETECTED` mandatory-target row, at **+73.7% headroom** —
and that is precisely the number [[TASK-0155]] showed is (a) computed on the
wrong mutant and (b) sitting at the high end of a distribution centred on
chance (median AUC 0.482 across 10 verified true-G12C structures; **P@5 =
0.000 on all ten**, versus 4OBE's own 0.200).

A referee reading `COMPETENCE_MAP.md` alone would take that row as the
project's strongest surviving result. It is the row most likely to be quoted
back.

## Intent Contract

- Outcome: every surface that names 4OBE as a G12C structure either carries an
  explicit, dated genotype flag or is corrected; `COMPETENCE_MAP.md`'s KRAS
  row carries a [[TASK-0155]] caveat inline, not only in `RESULTS.md`.
- Why required, not assumed: this project's stated culture is that a finding
  is not landed until the documents that would mislead someone are updated.
  The finding is five days old and has not left the file it was written in.
- In Scope:
  - `config/targets.yaml` — add a dated comment on the `apo_pdb: 4OBE` line
    stating it is wild-type, citing [[TASK-0155]]. **Do not change the value
    silently**: every historical number in the register is conditioned on it,
    and swapping it invalidates the whole apo-side register at once.
  - `backend/systems.py` — same flag. Decide explicitly whether
    `covalent_anchor=12` is defensible on a Gly12 structure for the app's
    visualization purpose, and record the decision either way.
  - `SOFTWARE.md` — annotate the benchmark table row.
  - `COMPETENCE_MAP.md` — add a dated caveat to the KRAS_G12C row **and** to
    its per-target narrative section, stating the genotype error and the
    10-structure distribution. This is the load-bearing edit.
  - `ARCHITECTURE.md` change log — one dated, signed line, per convention #7.
- Out Of Scope:
  - **Re-running anything.** Swapping the apo structure is a register-wide
    re-run and is not this task. If the team decides to re-anchor, that is a
    separate, large task with its own filing.
  - The frontend's benchmark dropdown labels, unless the flag is trivially
    placeable there.
- Constraints And Invariants:
  - No numbers change. This task adds caveats and does not retract results —
    the same convention [[TASK-0104]] established.
  - The flag text must state both halves: wrong genotype **and** lucky draw.
    Either alone understates it.
- Planned Validation:
  - `grep -rn "4OBE"` across the repo; every hit either carries the flag or is
    a historical/superseded context that explicitly says so.
  - Re-verify Gly12 independently (one line against `4obe.pdb`) rather than
    trusting either [[TASK-0155]] or this task file.

## In Progress

—

## TODO

- [ ] Re-verify 4OBE residue 12 = GLY directly.
- [ ] Flag `config/targets.yaml:58`.
- [ ] Flag `backend/systems.py`; decide + record the `covalent_anchor=12` question.
- [ ] Flag `SOFTWARE.md:222`.
- [ ] Caveat `COMPETENCE_MAP.md`'s KRAS row **and** its narrative section.
- [ ] `ARCHITECTURE.md` change-log line (dated, signed).
- [ ] `grep -rn "4OBE"` sweep to confirm no unflagged surface remains.

## Dependency

- [[TASK-0155]] (Done) — the finding.
- Feeds [[TASK-0184]] — the submission cannot present KRAS as a surviving
  result without this caveat.

## Open Questions

- Is `covalent_anchor=12` on a Gly12 apo structure actually wrong for the
  app's purpose? The Switch-II cryptic pocket is a property of the apo fold,
  and using a WT apo is a defensible modelling choice — but the target is
  *labelled* G12C and the anchor is *labelled* covalent. Decide and record;
  do not leave it implied.
- Does the register want a re-anchor to a true-G12C apo before 2026-09-15?
  [[TASK-0155]] already produced 10 verified candidates. Almost certainly no
  (register-wide re-run, past the freeze), but it should be a stated
  decision, not an omission.

## Done

—
