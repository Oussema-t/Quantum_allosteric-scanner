# TASK-0347 — Get a LaTeX toolchain, and render the submission two-column

- Status: Done
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

## Added 2026-09-08 — the page counter is wrong, and this is the strongest argument for the task

The CSS multi-column fallback named below was applied and built. Measured:

| | |
|---|---|
| physical pages in the rendered PDF | **3** |
| pages reported by `submission_build.py` | **7 / 6 — FAIL** |

**A greater than 2× error, in the one number the whole build exists to certify.**
`column-count` breaks whatever `pdf_to_pages()` uses to attribute text to pages,
and the checker reports a failure on a document that is comfortably compliant.

Two consequences, both of which raise this task's priority:

1. **The CSS fallback is not a fallback.** It produces a correct PDF that our own
   tooling cannot measure, so we would be shipping on an uncertified page count.
   Strike it as the cheap route back — it is only cheap if the checker works.
2. **No page count in this register has ever been validated against physical
   reality.** Single-column numbers were never cross-checked the way this
   two-column one accidentally was. Before trusting any figure from
   `submission_build.py` again, assert `len(pdfplumber.pages)` against the
   reported total — a one-line check that would have caught this immediately, and
   whose absence is the same "unverified checker" failure [[TASK-0319]] keeps
   finding.

**This is why LaTeX rather than more CSS.** Pagination in a two-column CSS render
is emergent and, as measured here, not reliably observable by our own tools.
LaTeX pagination is explicit, deterministic and reproducible from the source — it
is the format the checker can trust, and it gives the document the conventional
scientific presentation a panel expects. Priority raised accordingly.

## Done — 2026-09-08, Toolsmith

### What was built

`.ai/tools/submission_build_latex.py` + `.ai/tools/test_submission_build_latex.py`
(22 tests: 19 pure-function, 3 end-to-end). One command:

```
.venv/bin/python3 .ai/tools/submission_build_latex.py
```

Pipeline: `PHASE1_SUBMISSION_V2.md` → pandoc → LaTeX body → wrapped in a
generated template (twocolumn, A4, 10.5pt floor, `table*`/`figure*` full-width
spanning) → Tectonic → PDF → **`submission_build.py`'s own
`pdf_to_pages`/`analyze`/`evaluate`/`render_report` reused directly, not
reimplemented.** Same report shape, same exit-code contract.

### THE REAL NUMBER — real content, real compile, re-verified across multiple runs

```
[PASS] paper size      A4 (595.3 x 841.9 pt)
[PASS] body pages      5 / 6
[PASS] appendix pages  0 / 3
[PASS] body font       10.5 pt (min 10 pt)
[WARN] small text      2 characters < 10 pt (7.0-7.3pt -- \textsuperscript{14}
                       in "10^14", the same conventional-smaller-superscript
                       exception the HTML route already accepts)
[PASS] no horizontal overflow   0 words past the printable margin
RESULT: PASS
```

**5 pages of body against a 6-page limit, real headroom, on the real submission
content, with every table intact and nothing clipped.** The single-column HTML
route was at 6/6 with zero headroom before this session started; this session
separately found it had regressed further (TASK-0342's own follow-up finding,
same day) to 12/6 FAIL on the same content, driven by a still-unresolved
`column-count` font-collapse bug in the CSS fallback (see next section).

Visually inspected the rendered PDF (this task's own Planned Validation
instruction: "the automated checks cannot see a table clipped to nothing") --
clean two-column academic layout, all four tables render in full at full
column width, the ASCII diagram (transliterated to plain ASCII box-drawing,
see below) is intact and legible.

### Decisions (Toolsmith)

- **Engine: Tectonic**, exactly per the task's own prediction. Single bottled
  Homebrew formula (`brew install tectonic`), ~20MB, no multi-GB TeX Live.
  First compile ~105s (populates a local package cache over the network);
  every compile after, **0.2-0.3s** -- confirmed live, dramatically faster and
  more reproducible than this session's own repeated headless-Chrome
  flakiness (60-120s+ hangs, Mach-port/sandbox errors under this
  environment's Bash sandbox, an undiagnosed font-collapse bug -- see below).
  `pandoc` (also brew, bottled) converts the Markdown body; a hand-written
  preamble/postamble supplies layout, not hand-authored content.
- **Source of truth: `PHASE1_SUBMISSION_V2.md`, unchanged.** LaTeX is
  *generated* from it via pandoc, every run, never hand-edited -- satisfies
  the task's own explicit requirement ("preferred: LaTeX generated from the
  Markdown ... three hand-maintained copies is precisely the failure
  doc_parity.py was built to prevent"). The `.tex`/`.pdf` outputs live in
  `__WORK_IN_PROGRESS__/documentation/_build_latex/`, not yet gitignored --
  **follow-up**, see below.
- **Compliance/report layer reused wholesale, not reimplemented**, per the
  task's own explicit requirement. `pdf_to_pages`, `analyze`, `evaluate`,
  `render_report`'s structure, `next_version`, every git-context helper are
  imported from `submission_build.py` and called directly. Only the ONE
  HTML-specific message (the "small text" check's explanation, which named an
  SVG diagram and a CSS floor that don't exist here) is re-labelled locally
  (`_relabel_small_text_check`) rather than forked -- `evaluate()` itself is
  untouched, one implementation, two callers.
- **Change report is Markdown-native**, reusing `doc_parity.md_to_text`
  directly (already existed, already used by the HTML route's own parity
  check) rather than a new extractor -- adds section segmentation
  (`_sections_md`, split on `##`) the same way the HTML route added
  `_sections` for `<h2`.
- **Every table forced full-width (`table*`)**, not a per-table judgment
  call, closing the task's own named risk ("wide tables in a ~8cm column will
  either overflow or be squeezed"). Pandoc's default `longtable` output was
  rewritten with a targeted regex (`widen_tables_to_full_width`) -- a real bug
  in the FIRST version of that rewrite (a doubled `\\` producing a "Missing
  number" TeX error) was caught only by actually compiling, not by reading
  the regex, matching this whole project's standing "verify by rendering"
  rule.
- **The ASCII diagram (S6): kept verbatim, transliterated to plain ASCII
  box-drawing** (`+`/`-`/`|` instead of `┌─┐│└┘`), not redrawn in TikZ. Two
  independent reasons converged on the same answer: the task's own "motivation
  is density, not typesetting quality" note, AND a real, confirmed finding --
  Unicode box-drawing characters are not present in a default LaTeX text font
  under XeTeX, so keeping them Unicode produced missing-glyph errors. A
  plain-ASCII diagram is a normal, portable technical-document convention,
  not a downgrade needing an excuse.
- **Unicode math symbols (>=, x, ->, minus sign, rho, section-sign) are
  substituted before pandoc sees them**, not left as literal Unicode. Same
  underlying cause as the diagram (XeTeX's default text font lacks them), but
  the FIRST fix attempt (`$-$`-style bare math delimiters) was itself wrong --
  confirmed by looking at the rendered PDF, not assumed: pandoc's
  `tex_math_dollars` extension rejects a bare `$-$` as "not really math", so
  it came through as four literal, visible dollar-sign characters in the
  PDF. Fixed with pandoc's raw-attribute inline syntax
  (`` `\ensuremath{...}`{=latex} ``), confirmed to pass through unescaped
  regardless of any math-content heuristic.
- **No text is shrunk below the 10.5pt floor anywhere in the template.**
  Tables and the diagram were originally wrapped in `\small` (9pt, LaTeX's
  classic `size10.clo` value, independent of this template's own `\normalsize`
  redefinition) -- measured, found to FAIL the floor, removed. Same mistake
  TASK-0342 already found and fixed once in the HTML route; found and fixed
  here too by the same method (render and measure, don't assume).
- **Appendix-page detection reuses the exact HTML-route mechanism and its
  corrected lesson**: an invisible, unique literal token
  (`_APPENDIX_MARKER_TOKEN`, the SAME constant `submission_build.py` defines)
  inserted as the first thing after the matched appendix heading, found by
  searching the rendered PDF's text for that literal token -- not by matching
  the word "Appendix" in prose, which TASK-0342 already proved false-positives
  on an inline citation. `PHASE1_SUBMISSION_V2.md` currently has no appendix
  section, so this is built and unit-tested but not yet exercised against
  real appendix content (`--appendix-heading` is optional, no-ops cleanly
  when absent or unmatched).
- **Determinism: `SOURCE_DATE_EPOCH` + `-Z deterministic-mode`.** Verified
  live, not assumed: two independent compiles of the identical source are
  byte-identical for the **entire rendered content** -- every diff confined to
  the xref trailer's `/ID` field (a random value `xdvipdfmx` writes on every
  run; no flag found that removes it). Pinned down precisely by a dedicated
  test (`test_end_to_end_determinism_content_is_byte_identical_except_trailer_id`)
  rather than left as a vague "mostly deterministic" claim. This is a
  materially stronger determinism guarantee than the HTML/Chrome route ever
  had (Chrome's own page count moved across runs of this same session before
  TASK-0342's fixes landed).

### On the filed "the page counter is wrong" finding, above

Investigated directly rather than taken at face value, because it's the
stated reason to prefer LaTeX and deserved checking. Reproduced the CSS
two-column fallback exactly as filed (`column-count:2` baked into
`PHASE1_SUBMISSION_V2.html`'s own source) and found something **different**
from a page-count miscount: `submission_build.py`'s own font-floor check
(already built, TASK-0342) correctly caught the dominant body text collapsing
to **~7.5pt** -- confirmed live to be unrelated to `column-count` itself (the
same collapse reproduces with `column-count:1`, i.e. columns disabled), root
cause not identified after ruling out the obvious candidates (the grid
layout, tables, the ASCII diagram, in that order, each tested in isolation).
Given that finding, `pdf_to_pages()`'s own count (`len(pdfplumber.pages)`,
which literally *is* the "physical pages" number) collapsing from 7 to 3
between the filed measurement and this thread's own re-measurement is fully
explained by the font shrinking in between, not by a page-counting defect --
smaller text means fewer physical pages, which is exactly what happened.
**Not fully resolved either way**: this thread did not reproduce the filed
7-reported/3-physical discrepancy directly (the CSS experiment had moved on
by the time of re-measurement), so this is the most consistent explanation
found, not a certified refutation. Either way it does not change this task's
conclusion -- the CSS route has a real, confirmed, still-unexplained font
defect, which is reason enough on its own to prefer LaTeX regardless of which
account of the page-count number is correct.

### Not done / follow-ups

- **`__WORK_IN_PROGRESS__/documentation/_build_latex/` is not yet gitignored**
  -- same pattern as `_build/` for the HTML route (`.gitignore`). Left
  unstaged deliberately (a `.gitignore` edit is a repo-wide, easily-reviewed
  one-liner, not bundled silently into a large task commit) -- add before
  this route is used routinely.
- **No `--appendix-heading` content exists yet to exercise end-to-end** (see
  above) -- `PHASE1_SUBMISSION_V2.md` has none right now. Unit-tested via a
  synthetic fixture; needs a real run once appendix content exists.
- **This does not replace the HTML pipeline.** Per the task's own instruction
  ("keep the current HTML build working throughout... it is what we ship if
  this is not finished") `submission_build.py` is untouched and still works.
  Whether the actual submission ships from the LaTeX route now that it is
  real and passing is a **decision for the owner/Reviewer**, not a silent
  switch made here -- the evidence above is what that decision should be made
  from.
- Not wired into CI, same reasoning as the HTML route (Tectonic's own
  network-dependent first-run package fetch is an extra reason it would need
  a warmed cache to run reliably in CI, beyond the local-only rationale
  `submission_build.py` already states).
- No `claim.py`-style whitelist entry yet for either `brew install
  tectonic`/`pandoc` (already run, one-time) or `submission_build_latex.py`
  itself.
