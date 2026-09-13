# TASK-0386 — Name the mechanistic defect: orthosteric exclusion never fires on our own inputs

- Status: Done
- Owner: Implementer (verification done); Team Lead to decide fix-vs-name
- Priority: High — this is the *cause* of [[TASK-0385]], and naming it is worth more than fixing it silently
- Filed: 2026-09-13 by Reviewer thread
- Source: [[REVIEW-2026-09-13-adversarial-submission-package]] §B6
- Related: [[TASK-0385]], [[TASK-0278]]

## Verified against `config/targets.yaml` and the cached structures

| target | `func_ligand` | what the apo input actually carries | exclusion fires? |
|---|---|---|---|
| BCR_ABL1 | `["NIL"]` (nilotinib, from **holo** 5MO4) | 1OPL: **MYR + P16** | **no** |
| CARDIAC_MYOSIN | `["ADP","ATP"]` | 8QYP: **ADP + VO4 + Mg + M3L** | partially — **VO4 not listed** |
| KRAS_G12C | `["GDP"]` | 4LDJ: GDP + Mg | yes |

`func_ligand` exists precisely to exclude the orthosteric region from the
allosteric label. On BCR-ABL1 the listed code is a ligand **from the holo
structure that is not present in the apo input**, so the machinery never fires
and the walk is free to nominate the ATP site — which is exactly what it did
([[TASK-0385]]: residue 338 is the gatekeeper, 4.2 Å from P16).

Same shape on cardiac myosin: VO4 is part of the ADP·VO₄ transition-state mimic
and is not in the list.

## The decision

Whether or not the code is fixed before the deadline, **naming this is worth
more than fixing it silently**: it is a concrete, mechanistic defect in our own
instrument, found by our own audit standard, in a proposal whose entire thesis is
that instruments in this field are not audited. Fixing it quietly and shipping a
new top-5 would also invalidate every number already in the package with ~36
hours left.

**Reviewer's recommendation: name it, do not fix it before the deadline.**
Re-running changes the hit lists, the matrices, the AUCs and the reports, and
there is no time to re-audit the result. File the fix as Phase-2 work.

## Done when

- One sentence in the Concept Proposal or `Solution_Outputs.pdf` names the defect.
- A follow-up task exists for the actual code fix, explicitly scoped post-deadline.
- `targets.yaml` gains a comment at both entries recording the finding, so the
  next person does not rediscover it.

## Done

**All three finding conditions re-verified from raw structures before writing
anything**, not trusted from the filing: `grep "^HETATM" pdb_cache/1OPL.pdb`
gives exactly `MYR`, `P16` (no `NIL`); `pdb_cache/8QYP.pdb` gives `ADP`, `VO4`,
`MG`, `M3L`; `pdb_cache/4LDJ.pdb` gives `GDP`, `MG` — confirming the filing's
three-row table exactly, including the KRAS_G12C control case where exclusion
does fire.

**1. The defect is named, in the actual PDF, not just the `.md` source.**
`Solution_Outputs.md` §2 ("Known limitations, measured") gained a fourth,
measured bullet naming the mechanism (exact ligand-code lookup, silent
fall-through), both concrete instances (BCR_ABL1 full miss, CARDIAC_MYOSIN
partial miss on `VO4`), and the explicit named-not-fixed decision with the
task-id trail (TASK-0386 → TASK-0391). Chose `Solution_Outputs.pdf` over the
Concept Proposal deliberately: [[TASK-0385]] documents the Concept Proposal body
at 6/6 page budget with **no slack**, actively being fought over by another
thread's task; `Solution_Outputs.pdf` is explicitly not page-limited per this
package's own `README.md`, so adding here costs nothing and risks nothing.

**Rebuilt the PDF, not just the source** — the artifact a reviewer actually
opens. No build script for this file exists in the repo (checked: neither
`submission_build.py` nor `submission_build_latex.py` take a plain `.md` input
of this shape; both are for the numbered `PHASE1_SUBMISSION_*` / two-column
Concept-Proposal pipeline). Rebuilt directly with `pandoc --pdf-engine=tectonic
-V geometry:margin=0.6in -V fontsize=10pt -V papersize=letter` — chosen after a
naive default run overflowed the page (30+ pt overfull hboxes on the verbatim
report blocks, the exact bug TASK-0367/0369's own commits describe fixing once
already). Final build: 2 warnings at 1.4pt overfull (sub-visible, present even
before this change — confirmed by rebuilding the unmodified file first as a
baseline). **Caught and fixed a real glyph bug before shipping it**: my first
draft used `ADP·VO₄⁻` (Unicode subscript-4/superscript-minus); tectonic's
default font rendered it as literal `VOffff` garbage in the extracted text —
found by reading the rendered PDF back, not assumed correct. Replaced with
plain-ASCII `ADP-vanadate`; re-extracted text confirms it now reads correctly.
Paginates at 4 pages vs the previous build's 5 (different margin/font choice,
undiscoverable original recipe — no script, no metadata trail); acceptable
since this file carries no page-budget constraint. `targets.yaml` still
parses (`yaml.safe_load` via `.venv`) and the new keys land only on the two
intended entries — checked, not assumed (`func_ligand_note` present on
`BCR_ABL1`/`CARDIAC_MYOSIN`, absent on `CARDIAC_MYOSIN_TABLE1`).

**2. Follow-up task filed: [[TASK-0391]]**, reserved via `claim.py reserve-next`
(not hand-picked — TASK-0387 was already taken by a concurrent thread, a live
instance of the exact collision class TASK-0045 exists to prevent). Cites the
`labels.py::functional_indices` code path directly (line ~424, the
`if ligand is None: continue` fall-through), both concrete instances, three
candidate fix directions (warn-only, config-time lint, data fix) with the data
fix marked required before any re-shipped number can be trusted, and an
explicit Constraint against silently re-running and re-shipping without a
disclosed audit pass.

**3. `targets.yaml` gets a `func_ligand_note` at both entries**, following the
existing convention already used elsewhere in the file (e.g. PTP1B's own
`func_ligand_note` a few hundred lines down) rather than inventing a new
annotation shape. Each note states the specific mismatch, cites the exact
`pdb_cache/*.pdb` check that confirms it, names the downstream consequence
(TASK-0385's #5 hit for BCR_ABL1), and cross-links TASK-0386/TASK-0391.

**Not done / out of scope** (per the Reviewer's own recommendation, adopted
as-is): the actual code fix (TASK-0391, deferred), any re-run of hit
lists/AUCs/matrices, and reconciling the original Solution_Outputs.pdf build
recipe (untraceable — flagged for whoever owns that pipeline next, not chased
further here since this file's build is not gated on it).

Files touched: `__WORK_IN_PROGRESS__/documentation/SUBMISSION_PACKAGE/Solution_Outputs.md`,
`Solution_Outputs.pdf`, `__WORK_IN_PROGRESS__/config/targets.yaml`,
`.ai/tasks/TODO/TASK-0391-fix-func-ligand-silent-fallthrough.md` (new).
