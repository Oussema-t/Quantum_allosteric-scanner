# TASK-0192 Propagate the KRAS_G12C wrong-genotype finding out of `RESULTS.md`

## Context

- ID: TASK-0192
- Title: flag or correct `apo_pdb: 4OBE` everywhere it is used as a "KRAS
  G12C" structure — research config, live backend, public docs, and
  `COMPETENCE_MAP.md`'s headline table.
- Status: Done
- Resolution: done
- Resolution Note: Genotype flag propagated to all 5 in-scope surfaces (targets.yaml, systems.py, SOFTWARE.md, COMPETENCE_MAP.md x2, ARCHITECTURE.md changelog); covalent_anchor=12 question decided (not defensible as shipped, flagged not fixed); no numbers/response shapes changed
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

- [x] Re-verify 4OBE residue 12 = GLY directly (independent of TASK-0155's
      own RCSB check): `grep`'d the local `4obe.pdb` directly — chain A
      residue 12 CA atom is `GLY`. Confirmed.
- [x] Flag `config/targets.yaml:58`.
- [x] Flag `backend/systems.py`; decided + recorded the `covalent_anchor=12`
      question (see Done section — NOT defensible as currently shipped,
      flagged as a real inconsistency, not fixed).
- [x] Flag `SOFTWARE.md:222` (benchmark table + a dated footnote).
- [x] Caveat `COMPETENCE_MAP.md`'s KRAS row **and** its narrative section
      (`### KRAS_G12C — "ceiling below floor" is retracted...`).
- [x] `ARCHITECTURE.md` change-log line (dated, signed, newest-first).
- [x] `grep -rn "4OBE"` sweep — all 5 in-scope surfaces confirmed flagged;
      remaining hits are historical/DONE task files (not retroactively
      edited, per the no-silent-overwrite convention), test fixtures using
      4OBE as literal structure data (not a genotype claim), and one
      frontend `<input placeholder>` example (not a claim at all, no flag
      needed).

## Dependency

- [[TASK-0155]] (Done) — the finding.
- Feeds [[TASK-0184]] — the submission cannot present KRAS as a surviving
  result without this caveat.

## Open Questions

- Is `covalent_anchor=12` on a Gly12 apo structure actually wrong for the
  app's purpose? The Switch-II cryptic pocket is a property of the apo fold,
  and using a WT apo is a defensible modelling choice — but the target is
  *labelled* G12C and the anchor is *labelled* covalent. Decide and record;
  do not leave it implied. **Decided: not defensible as currently shipped.**
  The apo-fold-as-input argument is real, but `covalent_anchor=12`/
  `top5_full_named=["CYS12",...]` don't just use the fold — they assert a
  covalent Cys12 anchor that does not exist in the actual input structure
  (Gly12). That is a factual mismatch between the metadata and the
  geometry it is attached to, not a modelling-choice trade-off. Recorded as
  an unresolved inconsistency in a dated code comment; not fixed (fixing it
  means either changing `apo` — a register-wide re-run — or changing the
  metadata to stop asserting a covalent anchor the structure doesn't have,
  both out of this flag-only task's scope).
- Does the register want a re-anchor to a true-G12C apo before 2026-09-15?
  [[TASK-0155]] already produced 10 verified candidates. Almost certainly no
  (register-wide re-run, past the freeze), but it should be a stated
  decision, not an omission. **Stated, not decided by this task**: recorded
  explicitly in every flag added (targets.yaml, systems.py, SOFTWARE.md,
  COMPETENCE_MAP.md, ARCHITECTURE.md) as an open team call, not silently
  assumed "no" — the actual go/no-go decision belongs to [[TASK-0184]]'s
  submission-narrative process, not to this implementer.

## Done

**2026-08-03, Implementer B.** Re-verified the finding
independently before touching anything: `grep`'d the local `4obe.pdb`
directly (not re-trusting [[TASK-0155]]'s own RCSB check) — chain A
residue 12's `CA` atom is `GLY`. Confirmed.

Flagged all 5 in-scope surfaces with a dated, cited caveat (no numbers
changed anywhere, per the Constraint):
- `__WORK_IN_PROGRESS__/config/targets.yaml:58` — inline comment on the
  `apo_pdb: 4OBE` line.
- `backend/systems.py` — a block comment above the `KRAS_G12C` dict entry,
  explicitly deciding the `covalent_anchor=12` question (see Open
  Questions: not defensible as shipped, not fixed here).
- `SOFTWARE.md`'s benchmark table — a footnote marker + dated note citing
  both TASK-0155's finding and its own 10-structure distribution.
- `COMPETENCE_MAP.md` — **two** caveats, per the Intent Contract's own
  "row and narrative section" requirement: one on the headline
  floor/ceiling/actual table (right after the KRAS_G12C row), one at the
  top of the `### KRAS_G12C` per-target narrative section.
- `ARCHITECTURE.md`'s change log — one dated, signed line, newest-first,
  per convention #7 — the first entry in that log since 2026-06-28 (this
  is the first product-facing, non-research-scaffold change since then).

`grep -rn "4OBE"` swept across the whole repo: confirmed every hit is
either one of the 5 now-flagged surfaces, a historical/DONE task file
(left as-is — retroactively editing closed task files violates this
project's own no-silent-overwrite convention and they already describe
what was true when written), a test fixture using 4OBE as literal
structure data with no genotype claim attached, or a frontend `<input
placeholder="4OBE">` UI hint (not a claim, no flag needed).

Verified no regression: `backend.systems` still imports and returns
identical values (`apo="4OBE"`, `covalent_anchor=12` — unchanged, per the
Constraint) after the comment-only edit; `targets.yaml` re-parses cleanly
after the inline-comment edit.

**Not done, flagged not hidden**: no re-run, no apo swap, no response-shape
change anywhere (all explicitly Out of Scope). Frontend benchmark dropdown
checked directly (not assumed): `frontend/*.html`/`*.js` contain zero
hardcoded "KRAS_G12C"/"KRAS G12C" strings — the dropdown is populated
dynamically from `GET /api/targets`, which serves `backend/systems.py`'s
`SYSTEMS` dict directly, already flagged above. No separate frontend edit
needed.
