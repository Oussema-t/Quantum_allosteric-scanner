# TASK-0341 — A deterministic PDF render + page-count gate for the submission

- Status: TODO
- Owner: **Toolsmith**
- Priority: High — it is the last unverified constraint that can force a rewrite rather than an edit
- Filed: 2026-09-07 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0339]], [[TASK-0332]], [[TASK-0307]], [[TASK-0319]], [[TASK-0340]]

## Why

[[TASK-0339]] cut §7 by 187 words and spent 234 on §1/§2/§3 — a **net +47** on a
~2233-word body. It could not certify the result: *"PDF rendering not performed —
disclosed, not silently skipped. No pandoc/wkhtmltopdf/weasyprint available."*
Its own recommendation was an actual render before freeze.

**Nobody has ever counted the pages.** Every page estimate in this register is
words × a words-per-page constant.

## The rules the tool must enforce (from the source, not memory)

`documentation/2026-04-06-Phase-1-Submission-Guidelines-VF.md`:

- **Concept proposal: maximum 6 pages**, A4 or US Letter, PDF, **minimum 10pt font** (§ lines 153–155)
- **Appendices: maximum 3 additional pages** (line 157)
- *"Submissions exceeding the page limit may be returned or assessed only on the first 6 pages"* (lines 163–165)

That last clause is why this is a gate and not a report: over-length does not cost
style points, it **truncates the document mid-argument**.

Note also line 237 — *"a well-structured 4-page proposal will outperform a rambling
6-page one."* The tool measures the ceiling; it does not imply we should approach it.

## The renderer question — do not install a toolchain

`pandoc`, `wkhtmltopdf`, `weasyprint`, `prince`, `chromium` are all absent, and
`reportlab`/`fpdf`/`markdown`/`playwright` are absent from the venv. **But
`/Applications/Google Chrome.app` is present**, and this project already maintains
an HTML twin of the submission under CI-enforced parity ([[TASK-0340]] wired
`doc_parity.py` into `.github/workflows/`).

So the cheap correct path is **Chrome headless printing the existing HTML twin** —
it reuses an asset the project already pays to keep in sync, rather than adding a
Markdown→PDF pipeline whose output would be a third artifact nobody validates:

```
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf=out.pdf "file://$(pwd)/PHASE1_SUBMISSION_V1.html"
```

Toolsmith's call whether that is the right mechanism — it is a starting point, not
a specification. If a better one exists that does not require installing a
toolchain, take it and say why.

## Intent Contract

- Outcome: `.ai/tools/submission_pagecount.py` (name negotiable), which renders the
  submission and **exits non-zero** when any limit is breached, reporting body
  pages, appendix pages, and the effective body font size.
- **Body and appendices must be counted separately** — 6 and 3 are separate limits,
  so a single 9-page count passes a check that the panel would fail. The tool needs
  a defined split point (suggest the first `Appendix` heading) and must state which
  rule it used.
- **Determinism is the whole point.** A page count that moves with the machine is
  worse than none, because it will be trusted. Pin explicitly: paper size (pick
  **A4** and say so), margins, and a font stack with a real fallback — a silent
  webfont fallback changes pagination. Record the Chrome version in the output.
- **Verify the 10pt floor**, don't assume it. The HTML's print CSS is what
  determines rendered size; a `rem`-based stack with a smaller root, or a `@media
  print` block nobody checked, can put body text under 10pt while the source looks
  fine.
- **Check the print stylesheet before trusting any output.** The twin is
  theme-aware — if it carries dark-theme tokens without a `@media print` override,
  the PDF may render light-on-dark or drop backgrounds entirely. Look at the
  rendered PDF, do not only count its pages.
- Constraints And Invariants:
  - **Ships with a test that proves it fails on a seeded violation** — an
    over-length fixture must exit non-zero. [[TASK-0319]]'s standing finding: an
    unverified checker is not verified. This is the acceptance bar, not a nicety.
  - Do not modify the submission to make it fit. This task measures; [[TASK-0332]]
    decides what to cut.
  - Chrome is macOS-local, so CI cannot run it as-is. Either gate it behind an
    availability check that skips cleanly (matching `doc_parity`'s CI job style),
    or use a containerised headless browser — Toolsmith's call, but say which and
    why, and do not leave a workflow that fails on every push for the wrong reason.
- Planned Validation: run it against the current `PHASE1_SUBMISSION_V1.html` and
  **report the real number** — body pages, appendix pages, pass/fail. That number
  is the deliverable as much as the tool is.

## Consequence

If the body is over 6 pages, [[TASK-0332]]'s drafting plan changes before it starts
rather than after: [[TASK-0339]] already identified the cut order (§7 first, then
Appendix A's QUALIFIED rows). If it is comfortably under, §3 — 107 words for a
20%-weighted criterion — has room it is currently not using, and that is worth
knowing with equal urgency.
