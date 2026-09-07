# TASK-0341 — A deterministic PDF render + page-count gate for the submission

- Status: Done
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

## Requirements revised, 2026-09-07 — this section takes precedence

Two inputs from the repo owner change what this tool is for. Read this before the
Intent Contract above; where they conflict, this wins.

### 1. The need is a BUILD, not a checker

Stated directly: *"any agent can generate more text than I will be capable of
reading… re-reading the same document several times will quickly make me blind to
changes. I need the least clicks before a version gets created."*

So the deliverable is **one command that produces a numbered PDF**, with the
compliance checks running as a side effect and reporting themselves. Not a gate
the human invokes separately — a build whose output happens to be certified.

```
<one command>  ->  PHASE1_SUBMISSION_v<N>.pdf   +   a short report
```

The page count is the part the owner *can* check at a glance and will. Margins,
font size, paper size and the print stylesheet are the parts they explicitly do
**not** want to re-check — *"I will likely check this once or twice."* So those
must be asserted by the tool on every run and surface only as PASS, or as a loud
FAIL naming the specific rule broken. Silence means compliant.

### 2. The bigger need is a CHANGE REPORT, and it is the part nothing covers yet

Blindness to repeated re-reading is the real problem, and a page count does not
touch it. The tool should answer *"what changed since the last version"* so the
owner reads only the delta, not the document.

**`doc_parity.py` already has the machinery.** It extracts numbers, headings,
code identifiers and the title as comparable sets in order to diff the `.md`
against the `.html`. **Point the same extractors at v(N) and v(N−1) of the same
file** and a semantic change report falls out nearly free:

- numbers added / removed / changed (the highest-value line — this register's
  failure mode is a stale figure surviving an edit)
- headings added / removed / reordered
- per-section word-count delta, so growth is visible where it happened
- anything that moved out of, or into, the appendix split

Reuse, do not reimplement — a second extractor that drifts from `doc_parity`'s
would be worse than none. If the extractors need to be lifted into a shared
module to be usable twice, that refactor is in scope.

### 3. Unlimited re-upload — confirmed by the organisers, 2026-09-07

> *"You can cancel and reupload as many times as you want until the Sep 15th
> deadline is reached. After that, everything you've uploaded by that time will
> be counted as submitted."*

This removes the cliff. **There is no penalty for uploading a v1 today and a v9
on the 14th**, and a submitted-but-imperfect document strictly dominates an
unsubmitted perfect one. Two consequences for this task:

- Version numbering must be **monotonic and traceable** — the PDF should carry,
  or the report should print, the commit SHA it was built from, so an uploaded
  artifact can be matched back to a repo state after the fact.
- Optimise the tool for **iteration count, not for one perfect run.** If a build
  takes a minute and the report is three lines, it will be run twenty times. If
  it takes ten minutes and emits a wall of output, it will be run twice and then
  bypassed.

Recorded in `documentation/2026-08-26-organiser-clarifications.md` alongside the
other organiser answers.

### Acceptance, revised

- One command, from a clean tree, produces a numbered PDF and a report.
- The report fits on a screen. Compliance is PASS/FAIL, not a table to read.
- The change report names what changed since the previous version, using
  `doc_parity`'s own extractors.
- Still ships with a test proving it **fails** on a seeded over-length fixture
  ([[TASK-0319]]), and now also one proving the change report **detects** a
  seeded number change. A change report that silently misses an edit is the
  failure mode that matters here.

## Done — 2026-09-07, Toolsmith

### Deliverable

- `.ai/tools/submission_build.py` — one command. `.venv/bin/python3
  .ai/tools/submission_build.py` → a numbered PDF under
  `__WORK_IN_PROGRESS__/documentation/_build/` (gitignored, new rule added) +
  a screen-sized report to stdout and a `.report.txt` twin. Exit 0 PASS /
  1 compliance FAIL / 2 usage / 3 environment.
- `.ai/tools/test_submission_build.py` — 16 tests. The two acceptance-bar
  cases are pure functions (no Chrome): `test_overlength_body_fails` and
  `test_change_report_detects_number_change`. Chrome e2e tests run when Chrome
  is present and `skip` (not fail) when a sandbox blocks the render.
  `pytest .ai/tools/test_submission_build.py .ai/tools/test_doc_parity.py` →
  30 passed (doc_parity regression clean — extractors imported, not forked).
- `CAPABILITIES.md` — new "Submission Document Capability Set" section:
  `doc.submission.build` + a row for the pre-existing `doc.parity.check`.

### THE NUMBER (the deliverable as much as the tool — run against committed HEAD `b7a6a99`)

```
[PASS] paper size      A4 (595.0 x 841.9 pt)
[FAIL] body pages      9 / 6
[FAIL] appendix pages  8 / 3
[PASS] body font       12.4 pt (min 10 pt)
[WARN] small text      1229 characters < 10 pt (6.3–9.9 pt): eyebrow, .meta,
                       .foot, h2 .sub captions, table <th>, verdict chips
RESULT: FAIL
```

**The document is 17 pages against a 9-page allowance** — body 3 over, appendix
5 over — *after* the injected print CSS (A4, tightened margins, `.wrap`
max-width removed, forced light theme). This is the trigger the task's own
**Consequence** section describes: [[TASK-0332]]'s drafting plan changes before
it starts, not after. [[TASK-0339]] already named the cut order (§7 first, then
Appendix A's QUALIFIED rows) — but a 3-page body overage and a 5-page appendix
overage is well beyond what trimming §7 recovers. This needs an owner/Reviewer
decision on structural cuts, not word-count nibbling. **Flagged, not acted on
— this task measures; TASK-0332 decides what to cut.**

The `small text` WARN is a second, separate exposure: the guidelines say
"minimum 10pt font" flatly. 1229 characters render below that — mostly
chrome (eyebrow, meta, footer) and table headers / status chips, not body
copy. Left as WARN because body text is compliant and "minimum font" is
conventionally read as body copy, but a strict screener could bounce it.
Design/Reviewer call.

### Decisions (Toolsmith)

- **Renderer: headless Google Chrome, `--headless=old`.** `--headless=new`
  deadlocks against an already-running Chrome on macOS (reproduced — the
  render never returns). Old headless is fully independent. No
  `pandoc`/`weasyprint`/`wkhtmltopdf` install; prints the CI-parity-enforced
  HTML twin, so there is no third artifact to keep in sync.
- **Does not wait for Chrome to exit.** Chrome writes the PDF in ~2 s but
  routinely does not terminate promptly (lingering helpers; under a sandbox it
  hangs on a Mach-port rendezvous). The tool polls for the output file to
  appear and stop growing, then kills the process group. This is why the
  first naive `subprocess.run(timeout=90)` version timed out even though the
  PDF was already on disk.
- **Determinism is injected into a *copy*, never the source** (task
  constraint: do not modify the submission). The exact injected CSS is
  printed in every report. Pins: `@page size:A4` + fixed margins; forced
  light theme via `!important` custom-property overrides (beats the twin's
  `prefers-color-scheme` / `[data-theme]` rules regardless of specificity);
  `#appendix { break-before: page }` so the body/appendix split is a real
  page boundary, not a "which page did the heading land on" heuristic.
  Report records the Chrome version and whether webfonts were fetched online
  (offline → Georgia fallback → different pagination, stated loudly).
- **Change report reuses `doc_parity.py`'s extractors verbatim** (`html_to_text`,
  `numbers`, `_norm_heading`) via same-directory import — no second extractor
  to drift. Adds section segmentation (`_sections`, split on `<h2>`) for the
  per-section word delta, which `doc_parity` did not need. Compares the
  working-tree HTML against `--since` (default `HEAD`); skips with a note when
  the ref has no such file.
- **Local-only, no new CI workflow.** Chrome is macOS-local; webfont loading
  over the network is flaky in CI; the gate's value is pre-upload. The tool
  exits 3 with a clear message when Chrome/pdfplumber is absent, so if anyone
  wires it to CI later it skips cleanly rather than failing for the wrong
  reason. `doc_parity` stays the CI content check.
- **`pdfplumber` is a dev-only dependency** — already in `.venv`, deliberately
  not added to `requirements.txt` (same policy as `pytest` for
  `pytest_local.py`; Render never renders PDFs). Lazily imported; the tool
  prints the `pip install` line if it is missing.
- **Versioning:** `max(existing v<N>) + 1`, or `--version N`. PDF and report
  are named `PHASE1_SUBMISSION_v<N>_<sha>[-dirty]` so an uploaded artifact
  traces back to a repo state without committing the binary (organisers
  confirmed unlimited re-upload — recorded in the task's §3).

### Not done / follow-ups

- The tool does **not** decide or make any cut to the submission — see THE
  NUMBER above; that is [[TASK-0332]] / owner+Reviewer.
- `doc_parity`'s number regex occasionally surfaces a spurious bare integer
  (e.g. `-6` from a folded `10⁻⁶`) in the change report's figure list.
  Cosmetic, in the shared extractor, CI-wired — not touched under this task.
- No `claim.py`-style whitelist entry added to `.claude/settings.json` yet;
  the tool is invoked as `.venv/bin/python3 .ai/tools/submission_build.py`
  and will prompt until whitelisted. Worth a follow-up if it is run often.
