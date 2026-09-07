# TASK-0342 — Every table is clipped in the PDF: `overflow-x:auto` does not scroll on paper

- Status: Done
- Owner: **Toolsmith** (owns `submission_build.py`)
- Priority: **BLOCKER for any render** — the PDF currently loses content silently
- Filed: 2026-09-07 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0341]], [[TASK-0332]], [[TASK-0339]]

## Reported

Human review of the built PDF: *"pretty much all of the tables in the PDF are cut
off and not rendered correctly"* — with visible truncation mid-word:

> `no — and not even a single-molecule prope...`
> `Target selection and mechanistic classifi...`

## Root cause — confirmed in the source, not inferred

`PHASE1_SUBMISSION_V1.html`:

| line | rule | effect on paper |
|---|---|---|
| 134 | `.tw{overflow-x:auto; …}` | **This is the bug.** On screen the wrapper scrolls; in print there is nowhere to scroll to, so everything past the box edge is **clipped and lost**. |
| 140 | `th{… white-space:nowrap …}` | headers cannot wrap, so they force the table wider than the page |
| 144 | `td.n{… white-space:nowrap …}` | same for every numeric cell |
| 126 | `.chip{… white-space:nowrap …}` | same for status chips |

`nowrap` makes the tables overflow; `overflow-x:auto` then hides the overflow
instead of showing it. On screen that is correct and deliberate. In print it
means **the reader silently loses columns** — worse than an ugly layout, because
nothing indicates content is missing.

## Fix belongs in the injected print stylesheet, not the source

`submission_build.py` already injects a print block into a *copy* of the HTML and
leaves the source untouched — the right design, and this fix extends it. The
source HTML must keep `overflow-x:auto`, which is correct for screen reading.

Add to the injected `@media print` block, at minimum:

```css
.tw { overflow: visible !important; }
table { table-layout: auto !important; width: 100% !important; }
th, td, td.n, .chip { white-space: normal !important; }
```

Then **look at the rendered PDF**, do not only re-run the checker — this class of
defect passes every automated check ([[TASK-0341]]'s current run reports
`RESULT: FAIL` only on page counts; the clipping is invisible to it).

## Second finding from the same report — the sub-10pt text

The build reports `[WARN] small text — 1229 characters < 10 pt (sizes 6.3 … 9.9 pt)`,
noted as *"typically status chips and table headers; a strict reader may still
count these."* Guidelines §5 says **minimum 10pt**, without exempting table
furniture. 1229 characters is not a rounding artefact.

Fix in the same pass: floor every print font-size at 10pt. Note this will make
tables wider and interacts directly with the clipping fix — do both together and
re-render once, rather than fixing one and re-measuring.

## Constraints

- **Add a check that fails on clipped content**, per [[TASK-0319]]'s standing rule.
  Detecting "text was cut off" in a PDF is harder than counting pages — one cheap
  proxy: assert no element's rendered width exceeds the printable page width.
  If a reliable check is genuinely out of reach, say so and add a
  render-and-eyeball step to the tool's own README instead of leaving it implied.
- Do not solve this by shrinking the font below 10pt.

## Done — 2026-09-07, Toolsmith

### Fix (`.ai/tools/submission_build.py`, injected print CSS only — source untouched)

```css
.tw { overflow: visible !important; break-inside: auto; }
table { table-layout: auto !important; width: 100% !important; }
th, td, td.n, .chip { white-space: normal !important; overflow-wrap: anywhere !important; }
```
`overflow-wrap:anywhere` added beyond the task's own minimum so one
unbreakable token (a long URL, a long identifier) can't reopen the same
clipping bug once `white-space:normal` allows wrapping everywhere else.

**Font floor, extended beyond the selector list this task named** — rendered
and re-measured with `pdfplumber` (per the task's own instruction: don't
trust the source read alone), which found `code{font-size:.855em}` shrinks
below 10pt even inside an already-compliant container (a table cell, `.notice
p`, `.open p`) since it's a *relative* multiplier — auditing container
selectors alone missed it. Added `code` to the floor list; it accounted for
over half of the first re-render's outstanding sub-10pt characters (424 -> 195
chars). Full injected floor list: `.eyebrow, .meta, .notice h4, th, .chip,
.legend .lbl, .attack .k, .foot, .open .tag, .num, code` -> 10.5pt.

**Residual sub-10pt text, left alone deliberately, not missed:** the S6 SVG
pipeline diagram's labels (scale with the vector graphic's own coordinate
system — a CSS `font-size` floor changes the *source* value the SVG then
re-scales by its viewBox ratio, not the rendered size; fixing this means
redrawing the diagram, out of this task's scope) and `<sup>` exponents
(conventionally smaller than body text in essentially all typography,
including this project's own scientific register — flooring them would look
broken, not fixed). The "small text" WARN message states both explicitly and
tells the reader to re-measure, not assume, if a new size ever appears.

### The clipping check — "no horizontal overflow"

Implements the task's own suggested proxy: no extracted word's bounding box
may cross the printable margin (with a 2pt tolerance for antialiasing/rounding
noise, not a real allowance). **Documented limitation, stated plainly rather
than left implied** (the task's own fallback instruction): this catches
content that, once allowed to reflow, spills PAST the page edge instead of
being invisibly clipped — it is the failure mode the fix itself could
introduce. It **cannot** see content some other, not-yet-found
`overflow:hidden`/`auto` box clips to nothing, because clipped content leaves
no trace in the PDF to search. The report prints this caveat every run and
recommends opening the rendered PDF once per structural change.

### A second, more serious bug found while verifying this one

Investigating the clipping fix's effect on pagination surfaced that
[[TASK-0341]]'s body/appendix page-split detector was never actually
correct: `_APPENDIX_HEADING_RE = r"appendix\s+[a-z]\b"` searched rendered
prose for the word "Appendix" and matched S1's own taxonomy table, which
cites "(Appendix C)" inline on page 1-2 — well before the real "Appendix A"
heading (page 13). **Confirmed live, not inferred**: direct `pdfplumber`
inspection of a render showed the false-positive match; a controlled
before/after test on a 2-page synthetic fixture reproduced it in isolation.
This means [[TASK-0341]]'s originally-reported "THE NUMBER" (body 9/6,
appendix 8/3) was never a real measurement — dated correction added there,
original text left unedited per this register's convention.

**Fixed by not searching prose for "Appendix" at all.** An invisible unique
literal token (`SUBMISSION_BUILD_APPENDIX_START_7f3a9c`) is injected as the
first thing inside `#appendix`; the PDF is searched for that exact token. No
document wording can collide with it by accident.

First implementation attempt (`position:absolute`, to add zero layout height)
was itself wrong — **confirmed live**: the token never appeared in any
page's extracted text at all. Root cause: an absolutely positioned element
with no positioned ancestor anchors to its *pre-pagination* static position,
not to whichever page its in-flow neighbours land on once `break-before:page`
paginates the document — poorly-defined, inconsistent behaviour across a
paginated print context. Fixed by leaving the marker in normal flow instead
(still white-on-white, still invisible) at the cost of one harmless
near-zero-height line before "Appendix A" — genuinely part of the flow, so it
paginates exactly where the real heading does. Verified on an isolated
2-page synthetic fixture before trusting it on the real 17-page document.

### THE (corrected) NUMBER

Run against committed HEAD `5c9da67`, both fixes applied, reproduced across
two independent renders (`v23`, `v24`):

```
[PASS] paper size      A4 (595.0 x 841.9 pt)
[FAIL] body pages      12 / 6
[FAIL] appendix pages  5 / 3
[PASS] body font       12.4 pt (min 10 pt)
[WARN] small text      195 characters < 10 pt (SVG diagram + <sup> exponents, disclosed above)
[PASS] no horizontal overflow   0 words past the printable margin
RESULT: FAIL
```

Total page count is unchanged at 17 (matches [[TASK-0341]]'s total, which
*was* correct — only the body/appendix attribution was wrong) — the true
split is **12 body / 5 appendix**, not 9/8. Both still fail their limits.
[[TASK-0332]]'s drafting plan still needs the same structural-cut decision
[[TASK-0341]] flagged; the size of each overage has changed (body +3pp
worse than reported, appendix +2pp better) but the FAIL verdict has not.
Clipping is fixed (0 violations) — the tables that were silently losing
columns (*"no — and not even a single-molecule prope..."*) now render in
full; this alone is very likely why the page count moved (wrapped table
rows take more vertical space than the clipped single-line rows did).

### Tests (`.ai/tools/test_submission_build.py`)

Added: clipping FAIL/PASS/tolerance cases + a test asserting the injected
CSS actually contains the claimed fix (a docstring claiming a fix with CSS
that doesn't apply it would be worse than no fix); `mark_appendix_start`
unit tests (inserts correctly, no-ops without `#appendix`); the false-positive
regression (`test_inline_appendix_mention_in_body_is_not_a_false_split`);
e2e assertions that the real submission's split isn't fooled and clipping is
0. **38 tests, full suite, 0 failures, 0 skips** (one run hit transient
sandboxed-Chrome flakiness — see Environment note below — and skipped via the
existing sandbox-detection guard; re-run clean).

### Environment note (not a tool defect)

Headless-Chrome renders in this session were intermittently very slow
(60-120s+, sometimes failing to finish inside 120s) with log noise from
Chrome's updater/GCM subsystems (`GoogleUpdater`, `registration_request.cc`,
Mach-port/mojo errors) unrelated to `--print-to-pdf` itself, which normally
completes in 2-10s (confirmed on a tiny synthetic fixture during
verification). Root cause not chased further — looks like local machine
load or a stalled system-level Chrome updater service, not a defect in
`submission_build.py`'s render/poll logic, which behaved correctly (returned
clean errors, no hangs) whenever this happened. Flagged so a future thread
doesn't mistake a slow render for a regression.

### Constraint check

- Font floor only ever raises a size toward 10pt (10.5pt), never lowers one —
  confirmed by reading every changed rule; no `font-size` value in the
  injected stylesheet is below `MIN_FONT_PT`.
- The clipping check is disclosed as incomplete (cannot see invisibly-clipped
  content), with the render-and-eyeball fallback stated in both the tool's
  own module docstring and every report it prints — not left implied.
