# TASK-0163 Run external classical baselines (PocketMiner, ProteinLens, fpocket)

## Context

- ID: TASK-0163
- Title: `PANEL_REVIEW_2026-07-25.md` W7/V8 — the challenge explicitly
  scores "comparison to classical analogs." The project has run ~40
  quantum-flavored observables but only **one** external classical
  comparator (GNM transfer entropy, [[TASK-0132]]). `ALGORITHM_REGISTER.md`
  itself rates PocketMiner, ProteinLens, and fpocket at 4 and none was
  ever run. A referee will ask directly why a program with this much
  quantum-side testing volume has one classical baseline.
- Status: Done (2026-07-28)
- Owner: Implementer
- Claimed By: Implementer C (this thread)
- Claimed At: 2026-07-25 10:20
- Source: `PANEL_REVIEW_2026-07-25.md` §2.2/W7, §4 action item 6, V8.
- Priority: **P1** — the review's own estimate is 2 days, mostly waiting
  on external web servers/tools, not analysis time. Either outcome
  strengthens the submission (per the review: if they hit where this
  project misses, the operator is the bottleneck; if they also miss,
  that is independent corroboration of the project's own thesis that
  apo topology may not encode the answer).

## Intent Contract

- Outcome: run PocketMiner, ProteinLens, and `fpocket` (a local,
  installable classical pocket-detection tool — the closest of the
  three to a first attempt, per `ALGORITHM_REGISTER.md`'s own rating)
  against the 3 mandatory targets' apo structures; score each against
  the same holo-defined pocket labels and the same AUC/floor
  methodology already established, so the comparison is apples-to-apples
  with the project's own reported numbers.
- Why required: this is the one comparison the challenge explicitly
  scores and the project has not made at the scale its own testing
  volume would suggest.
- In Scope:
  - `fpocket`: install (document as a new external dependency, same
    disclosure convention as `ripser`/`optuna` — [[TASK-0108]]/
    [[TASK-0110]]'s own precedent), run on the 3 mandatory apo
    structures, score its predicted pockets against the holo labels
    using the project's own AUC/floor convention.
  - PocketMiner / ProteinLens: web-server or downloadable-model based
    (confirm actual access method before starting — if either requires
    an account/API key/institutional access not available, state that
    explicitly as a blocker for that tool specifically, do not silently
    skip without saying so).
  - Report each tool's AUC against the project's own floor and against
    the project's own best surviving observable, same target set.
- Out Of Scope:
  - Any new observable of this project's own — pure external-tool
    benchmarking.
  - Installing/running tools not named in `ALGORITHM_REGISTER.md`'s own
    rated list.
- Constraints And Invariants: score external tools against the exact
  same holo-defined pocket labels this project already uses — no
  bespoke evaluation favoring either side.
- Planned Validation: a comparison table (this project's own best
  observable vs. each external tool vs. the proximity floor), all 3
  mandatory targets, explicit report of which tools were actually
  reachable/runnable and which were blocked.

## TODO

- [x] Confirm access method for PocketMiner and ProteinLens (web
      server / downloadable / blocked); state findings explicitly.
- [x] Install `fpocket`; document as new external dependency.
- [x] Run all reachable tools on the 3 mandatory apo structures.
- [x] Score against holo pocket labels, project's own AUC/floor
      convention.
- [x] `RESULTS.md`/`ALGORITHM_REGISTER.md` comparison table; update the
      register's own rating entries to reflect "run," not just "rated."

## Dependency

- [[TASK-0094]] (Done) — proximity floor, reused for comparison.
- `ALGORITHM_REGISTER.md` — the existing rating/candidate list this task
  acts on.

## Open Questions

- Whether PocketMiner/ProteinLens are actually reachable from this
  project's own working environment (web-server access, rate limits,
  account requirements) — resolve at the start of this task, report
  honestly if blocked rather than substituting a different tool
  silently.

## Done

**2026-07-28.** Access-method confirmed for all 3 tools before any run, per this
task's own Constraint:
- **fpocket**: no server, no account — built from source (`Discngine/fpocket`
  `4.2.3`, plain `make`, no root/apt needed) into
  `__WORK_IN_PROGRESS__/tools/fpocket/` — a permanent, repo-local install
  (`ldd` confirms it links only system `libm`/`libstdc++`/`libc`/`libgcc_s`),
  documented as a new external dependency, same disclosure convention as
  `ripser`/`optuna`.
- **PocketMiner**: web server (`pocket-miner-ui.azurewebsites.net`) is DNS-dead,
  confirmed two independent ways (`curl`, `WebFetch`). Local install needs
  `tensorflow==2.6.2` (Python ≤3.9 only) — incompatible with this repo's Python
  3.12, so run in a genuinely separate, isolated repo
  (`/home/bchmura/PROJECTS/PocketMiner/`), not this one, via a from-source
  Python 3.9.18 build (no root needed). No account/API key required once
  installed; model weights ship in the cloned repo.
- **ProteinLens**: web server live and reachable, no login required — but
  browser-only interactive UI, no discovered API/batch endpoint. **Explicit
  blocker, not run, not silently substituted** — this task's own Intent
  Contract requires stating this rather than skipping quietly.

fpocket and PocketMiner run against all 3 mandatory targets' apo structures
(`4OBE`/`1OPL`/`8QYP`, chain A), scored against this project's own holo pocket
labels using the exact same `labels.build_labels`/`metrics.auc`/proximity-floor
convention every other observable in this register uses
(`scripts/task0163_external_baseline_scoring.py`):

| Target | Floor | This project's own actual (`H_new`/CTQW) | fpocket AUC | PocketMiner AUC |
|---|---|---|---|---|
| KRAS_G12C | 0.4818 | 0.5901 | **0.8348** | 0.6932 |
| BCR_ABL1 | 0.5817 | 0.5266 | **0.8596** | 0.5603 |
| CARDIAC_MYOSIN | 0.5679 | 0.5176 | 0.5345 | 0.5732 |

**Headline: fpocket — purely geometric, no propagator, no eigendecomposition, no
active-site seed — decisively beats both this project's own proximity floor and
its own `H_new`/CTQW headline observable on 2/3 mandatory targets** (KRAS_G12C,
BCR_ABL1), and sits just below its own floor on CARDIAC_MYOSIN. PocketMiner is
mixed: beats this project's own actual on KRAS_G12C/CARDIAC_MYOSIN (narrowly
clearing its own floor on the latter, +0.0053), falls short of floor on
BCR_ABL1. This is exactly the informative-either-way outcome the filing review
anticipated: the classical geometric method hits decisively where this
project's own quantum-walk observable does not.

A real alignment bug was found and fixed while scoring PocketMiner on
CARDIAC_MYOSIN, not silently worked around: its apo (8QYP) carries two
trimethyllysine (`M3L`) residues stored as `HETATM` records; an initial
`ATOM`-only resSeq parser undercounted PocketMiner's own residue axis by
exactly these 2 (704 vs. the true 706), tripping a length-mismatch guard.
Fixed by parsing `HETATM` CA records too — `M3L` was renamed to canonical
`LYS` before feeding the structure to PocketMiner (chemically inert to its
prediction: PocketMiner's featurizer reads only backbone N/CA/C/O + residue
identity, never side-chain atoms), while this project's own `clean()` excludes
`M3L` from `apo.resnums` entirely (prody's `protein` selector doesn't
recognize the non-standard name) — the 2 extra PocketMiner predictions at
those positions are simply never queried once alignment is by `(chain,
resnum)` lookup rather than array position, an honest resolution, not one
favoring either tool.

This project's own "actual" column is a fresh `run_challenge.py` run against
the current `TASK-0124`-corrected 8QYP-era CARDIAC_MYOSIN apo, not the retired
5TBY/N=950 numbers some earlier `RESULTS.md`/`COMPETENCE_MAP.md` sections still
cite for that target — KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN floor and actual
values reproduce [[TASK-0132]]'s and [[TASK-0124]]'s own already-published
numbers exactly, cross-validating this task's own pipeline reconstruction.

`RESULTS.md` (new "External classical-pocket-detection baselines" section +
open-questions row 44), `ALGORITHM_REGISTER.md` (fpocket/PocketMiner marked
RUN with real numbers, ProteinLens marked BLOCKED with the reason), and
`EXECUTION_PLAN.md` (1E.6 completion annotation) all updated in this same
commit. Not attempted, per this task's own Out of Scope: reselecting the
submission operator based on this result; any new observable of this
project's own.

Full detail: `RESULTS.md`'s own section,
`__WORK_IN_PROGRESS__/scripts/task0163_external_baseline_scoring.py`,
`__WORK_IN_PROGRESS__/results/tasks/0163_external_baselines/results.json`,
`/home/bchmura/PROJECTS/PocketMiner/` (separate repo).
