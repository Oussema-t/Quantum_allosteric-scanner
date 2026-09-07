# TASK-0347 — Get a LaTeX toolchain, and render the submission two-column

- Status: TODO
- Owner: **Toolsmith**
- Priority: High — the page budget is the binding constraint on the submission
- Filed: 2026-09-07 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0341]], [[TASK-0342]], [[TASK-0344]], [[TASK-0333]]

## Why

The concept proposal is capped at 6 pages. The current single-column HTML→Chrome
render sits **exactly at 6/6**, so every addition now displaces something, and the
last three content additions each cost a round of trimming elsewhere. A
two-column layout typically fits 40–60% more text per page for prose-plus-tables
material of this kind. That is the difference between fighting the limit and
having room for the appendix material and the results still coming from
[[TASK-0345]]/[[TASK-0346]].

## Confirmed state

**Nothing is installed.** Checked directly:

```
pdflatex   -      xelatex   -      tectonic  -
latexmk    -      pandoc    -
```

No LaTeX engine, no converter. This is a from-zero toolchain task, not a
configuration one.

## Intent Contract

- Outcome: a two-column PDF of the concept proposal, produced by one command,
  meeting every constraint the current build already enforces — **A4, ≥10pt body
  text, ≤6 body pages, ≤3 appendix pages, no clipped tables.**
- Engine choice is the Toolsmith's, with a stated reason. The obvious candidates:
  - **Tectonic** — single self-contained binary, downloads only the packages a
    document actually uses, no multi-GB install. Likely the right answer here.
  - **TeX Live / MacTeX** — complete and conventional, but multi-GB and slow to
    install.
  - **pandoc + an engine** — adds a Markdown→LaTeX path, which matters because
    `PHASE1_SUBMISSION_V2.md` already exists and is the natural source.
- **The source-of-truth question must be answered explicitly, not by accident.**
  There are currently two twins (`.md` and `.html`) kept in parity by
  `doc_parity.py`. Adding LaTeX makes three. Either LaTeX is generated from the
  Markdown (preferred — one authored source), or it becomes the authored source
  and the other two are derived, or the pipeline keeps two and drops one. Pick
  one and say so; three hand-maintained copies of a submission is precisely the
  failure `doc_parity.py` was built to prevent.
- **Do not lose what `submission_build.py` already earns.** It certifies page
  counts, enforces the 10pt floor, checks for horizontal overflow, records the
  Chrome version and commit SHA, and produces a change report against the
  previous version. A LaTeX route must keep the equivalent checks or the
  regression is worse than the page saving. Reuse the existing report format.
- Constraints And Invariants:
  - **Ships with a test proving it fails on an over-length fixture**
    ([[TASK-0319]]'s standing rule), as `submission_build.py` does.
  - Deterministic: same input, byte-identical PDF. LaTeX embeds timestamps by
    default — set `SOURCE_DATE_EPOCH` or the engine's equivalent.
  - Tables must not clip. This was a real defect in the HTML route
    ([[TASK-0342]]) and two-column layout makes it *more* likely, not less —
    wide tables in a ~8 cm column will either overflow or be squeezed. Plan for
    full-width (`table*`-style) spanning for the wide ones from the start.
  - The ASCII pipeline diagram in §6 needs a decision: keep as verbatim, or
    redraw with TikZ. Verbatim in a narrow column will not fit.
- Planned Validation: render the current `PHASE1_SUBMISSION_V2.md`, report the
  page count against the single-column baseline of 6, and **open the PDF** —
  the automated checks cannot see a table clipped to nothing.

## Decision gate, and the fallback

**This is a pipeline replacement eight days before the deadline.** The existing
route is validated, passing, and produced a submittable PDF today. So:

- **Timebox it.** If a working two-column render is not standing within a day,
  stop and report — do not leave the submission depending on a half-migrated
  pipeline.
- **The fallback is not "do nothing".** Chrome honours CSS multi-column
  (`column-count: 2` with `column-span: all` on tables, headings and the
  diagram) in print, which gets the same density on the existing, already-
  validated pipeline in roughly one line of CSS. It was drafted and set aside in
  favour of this task; if LaTeX runs long, that is the cheap route back.
- Keep the current HTML build working throughout. It is what we ship if this is
  not finished.

## Note

The motivation is density, not typesetting quality — the current PDF is already
clean. Judge the result on pages saved and constraints kept, not on whether it
looks like a LaTeX paper.
