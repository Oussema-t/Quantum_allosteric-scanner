# TASK-0342 — Every table is clipped in the PDF: `overflow-x:auto` does not scroll on paper

- Status: TODO
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
