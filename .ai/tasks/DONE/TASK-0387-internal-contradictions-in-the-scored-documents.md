# TASK-0387 — Internal contradictions a reviewer will hit in the scored documents

- Status: Done
- Owner: Implementer
- Priority: Medium-high. Items 1–2 are near-free; 3–5 cost page budget.
- Filed: 2026-09-13 by Reviewer thread
- Source: [[REVIEW-2026-09-13-adversarial-submission-package]] §E1–E6, F4
- Related: [[TASK-0369]], [[TASK-0385]]

All five verified directly against HEAD by the Reviewer.

## 1. "We followed it in each case" is contradicted by the table underneath it

`PHASE1_SUBMISSION_V4.md:21` — *"Their reply of 2026-08-26 answered three points,
and we followed it in each case:"* The KRAS row immediately below says the
organisers suggested `8S8C` and **we rejected it**. We were right to (8S8C is
holo, MK-1084-bound — confirmed by the external reviewer and consistent with our
own check). **Being right and describing ourselves as compliant when we were not
is the worst available combination.**

Rewrite to: *"answered three points; we adopted two and, on the third, checked
the suggested structure, found it holo, and substituted a verified apo instead."*

Near-free — replaces a clause with a clause.

## 2. The deviation count disagrees across three places

| where | says |
|---|---|
| `03_Problem_Statement_Selection.md:24` | "**Four** structure choices deviate from Table 1" |
| `PHASE1_SUBMISSION_V4.md:30` footnote | "**Two** rows above are deviations, one a retention" |
| actual deviating structures | **three**: `4LDJ`, `8QYP`, `8QYR` |

Both statements are defensible about different things (rows vs structures) and
together they read as carelessness. Pick one unit, state it, make all three
agree. Doc 03's other claim — that the reasons are "in Section 1 of the Concept
Proposal" — **is now true**, so only the number needs fixing.

## 3. Our own inputs are not ligand-free, and §1 does not say so

§1's fourth finding is *"'Apo' does not mean ligand-free"* — and the proposal then
labels `4LDJ` "(apo)" (GDP + Mg) and `8QYP` "(apo)" (**ADP + VO₄ + Mg**, a
transition-state mimic), disclosing only 1OPL's myristate and omitting 1OPL's
second ligand (P16) entirely. [[TASK-0278]] already found all of this.

**We are under-reporting our own strongest evidence in the one section where a
reviewer is primed to check.** Suggested sentence, from the review and verified
against the cached structures:

> Our own three inputs are no exception: 4LDJ carries GDP·Mg, 8QYP carries
> ADP·VO₄·Mg, and 1OPL carries both myristate and an ATP-site inhibitor. All
> three are apo only with respect to the scored pocket — which is the strongest
> form of the point.

## 4. Cardiac myosin is bovine and the Concept Proposal never says so

8QYP/8QYR are *Bos taurus* Myosin-7. The artefacts README discloses it; the
**scored** document does not. This matters because our stated objection to Table
1's `6C1H` is partly a species objection (rat myosin-Ib on rabbit actin). The
defence is easy and strong — bovine β-cardiac myosin is a near-identical
orthologue of the human target, whereas myosin-Ib is a **different class** — but
we have to make it, or the asymmetry reads as convenient.

## 5. The cardiac PDB code is missing from the five-guess table

`PHASE1_SUBMISSION_V4.md:44` — KRAS, BCR-ABL1 and c-Myc rows all carry their code
in the Target column; cardiac myosin does not. Flagged on 2026-09-11, still open.
Verified still missing. Near-free.

## 6. MYC_MAX: our own config says the pocket does not exist

`targets.yaml:437` — `allosteric_pocket_exists: false`. We ship a top-5 for a
target our own configuration asserts has no folded-state pocket, and the fpocket
druggability we report (max 0.161) sits well under our own 0.5 bar. "Unverified"
is honest but incomplete. Say the harder thing:

> Our own configuration records that this target has no folded-state allosteric
> pocket; we supply the five because the challenge requires them, and we report
> that our best candidate site scores 0.161 druggability against our own 0.5
> threshold.

That is a better answer to §6's "theoretical docking viability" than the current
one.

## Done when

All six reconciled, PDFs rebuilt, body still 6/6 PASS. If page budget forces a
choice, reviewer's order is **1, 2, 5 (near-free) → 3 → 6 → 4**.

## Done — 2026-09-13, Implementer D

**5 of 6 shipped; item 4 dropped, exactly per this task's own stated fallback
order, and the drop is a measured page-budget fact, not a judgment call.**

Verified all six items directly against the current live documents before
editing (the package was restructured for the portal's five-file limit on
2026-09-13, after this task was filed — `PHASE1_SUBMISSION_V4.md` grew,
`03_Problem_Statement_Selection.md`/`Solution_Outputs.md` are now separate
PDFs; re-checked every cited line/claim against this current state, not the
filing's own line numbers).

**Item 1.** `PHASE1_SUBMISSION_V4.md:21` — replaced "we followed it in each
case" with the review's own suggested rewrite verbatim ("we adopted two and,
on the third, checked the suggested structure, found it holo, and
substituted a verified apo instead"). Applied as given.

**Item 2.** `03_Problem_Statement_Selection.md` — "Four structure choices
deviate" was wrong under either counting convention (3 deviating structures:
`4LDJ`, `8QYP`, `8QYR`; 2 deviating rows, since BCR-ABL1 is a retention).
Rewrote to state both explicitly ("Three structures deviate... BCR-ABL1's
`1OPL` is retained, not substituted"), consistent with `PHASE1_SUBMISSION_
V4.md`'s own footnote ("two rows... one a retention") rather than repeating
a bare, ambiguous number.

**Item 5.** `PHASE1_SUBMISSION_V4.md:44` five-guess table — added `(8QYP)`
to the Cardiac myosin row, matching the KRAS/BCR-ABL1/c-Myc rows' own
PDB-code convention.

**Item 3 — shipped, in a materially trimmed form; the real story is the page
budget, not the content decision.** Verified directly against cached PDB
HETATM records before writing anything (`grep HETATM` on `pdb_cache/{4ldj,
8qyp,1opl}.pdb`): `4LDJ` carries `GDP`+`MG`, `8QYP` carries `ADP`+`VO4`+`MG`
(+`M3L`, a modified residue, not a small-molecule ligand), `1OPL` carries
`MYR`+`P16` — the review's claim confirmed exactly, not trusted on its word.
**The baseline document has genuinely zero page-budget slack**, empirically,
not assumed: with items 1/2/5 applied, body sits at exactly 6/6; adding the
review's full suggested sentence for item 3 (or any of four progressively
shorter rewrites tried) pushed body to 7/6 every time, including a version
with item 4 fully absent. Only a minimal in-sentence insertion — extending
the existing myristate clause to "`1OPL` carries myristate... — as do `4LDJ`
(GDP·Mg) and `8QYP` (ADP·VO4·Mg)" rather than a new sentence, and dropping
the explicit restatement of `1OPL`'s second ligand (`P16`) — fit inside
6/6. **`P16` is not left undisclosed package-wide**: it is already named in
`Solution_Outputs.md`'s existing §2 ("`1OPL`... carries `MYR`/`P16`
instead"), just not repeated in the Concept Proposal itself. Also fixed a
real defect caught in the process: my first draft used `VO₄` (Unicode
subscript), which this LaTeX template cannot render (`[FAIL] glyph
coverage` on rebuild) — switched to plain `VO4`, matching the ASCII
convention already used elsewhere in this same document and in
`config/targets.yaml`.

**Item 6 — shipped in full, no page-budget cost.** `Solution_Outputs.md` is
a separate deliverable file, not subject to the Concept Proposal's 6-page
cap. Verified `config/targets.yaml:461` (`allosteric_pocket_exists: false`,
with its own documented rationale: "Myc/Max are IDPs with no surface pocket
in the folded dimer") and the shipped druggability values (max 0.161 across
the five listed pockets) before writing the review's suggested sentence
verbatim after the existing docking-viability block, plus the `DRUGGABILITY_
BAR = 0.5` convention (confirmed real and pre-existing: `task0204`/`task0209`/
`task0214`/`task0230`/`task0346`, "fpocket's own commonly-cited druggable/
non-druggable cutoff" — not invented for this sentence).

**Item 4 — dropped, per this task's own explicit fallback order.** Tried
first at full length, then trimmed twice; even the shortest defensible
version ("`8QYP`/`8QYR` are themselves *Bos taurus*... so our own species
substitution is far milder than Table 1's") did not fit once item 3 already
claimed the last available line — confirmed by testing item 4 alone (with
item 3 absent) and finding it ALSO overflows to 7/6 on its own, i.e. neither
addition alone fits without a compensating cut to existing body text, and
cutting existing substantive content was judged outside this task's own
scope (a bigger editorial call than a contradiction fix). Per the task's own
stated priority (**"if page budget forces a choice ... → 6 → 4"**), 4 is the
one to drop. **Left open, not silently abandoned**: the bovine-species
disclosure already exists in `artefacts/README.md` (per [[TASK-0370]]); only
the *Concept Proposal's* own copy is missing, and the fix (a one-clause
addition) is ready to apply verbatim the next time the CP's page budget has
any slack (e.g. if a page-budget task trims existing text).

**PDFs rebuilt and copied into the package**: `01_Concept_Proposal.pdf`
(source `PHASE1_SUBMISSION_V4.md`, via `submission_build_latex.py`),
`03_Problem_Statement_Selection.pdf`, `Solution_Outputs.pdf` — all three
via the same tool, text-extraction-verified afterward (`pdfplumber`) to
confirm each edit's exact wording is present and the pre-edit wording is
gone, not just that the build succeeded.

**Final compliance, `01_Concept_Proposal.pdf`**: `[PASS] body pages 6/6`,
`[PASS] appendix pages 1/3`, `[PASS] glyph coverage`, `[PASS] citations`,
`[PASS] no horizontal overflow`; one pre-existing `[WARN] small text`
unchanged from the unedited baseline (confirmed by rebuilding baseline
before any edits) — not introduced by this task. `03_Problem_Statement_
Selection.pdf` and `Solution_Outputs.pdf` both `RESULT: PASS`, no page cap
applicable to either. Package total ≈13.6 MB, against the 20 MB cap
(`Connectivity_Matrices.csv` unchanged, still the dominant size).

**Not in scope, correctly left alone**: item 7 (E7 in the review — hit-list
reproducibility from the shipped matrix), which this task's own item list
never included.

**Files**: `PHASE1_SUBMISSION_V4.md`, `SUBMISSION_PACKAGE/{03_Problem_
Statement_Selection.md,Solution_Outputs.md,01_Concept_Proposal.pdf,
03_Problem_Statement_Selection.pdf,Solution_Outputs.pdf}`.
