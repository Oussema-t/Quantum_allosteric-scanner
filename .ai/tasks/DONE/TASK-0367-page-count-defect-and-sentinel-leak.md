# TASK-0367 — The page-count check cannot see the violation it exists to catch, and the build sentinel ships inside the PDF

- Status: Done
- Owner: **Toolsmith**
- Priority: **Blocking. Nothing else about the submission can be trusted until the build tells the truth.**
- Filed: 2026-09-11 by Reviewer thread (id via `claim.py reserve-next`)
- Source: `.ai/reviews/2026-09-11/REVIEW-2026-09-11-external-adversarial-submission-package.md`, items 2 and 32
- Related: [[TASK-0349]], [[TASK-0362]], [[TASK-0363]], [[TASK-0365]]

## Defect 1 — body pages are undercounted, and it is the page limit that is at stake

`submission_build_latex.py` splits body from appendix at an invisible marker and
reports *"body = pages 1-6, appendix = pages 7-7"*. **That is wrong whenever body
content shares a page with the start of the appendix**, which is exactly what
happens now.

Verified directly from the shipped PDF (`pdfplumber`, page 7 text layer):

```
sentinel at char 738 | "Appendix" at char 670
--- BODY text on page 7, before the sentinel ---
Oussema Turki   Quantum algorithms   Operator design, propagator ...
Berke Turkaydin Computational biophysics / ...
Bartosz Chmura  Molecular photophysics; software ...
github.com/Oussema-t/Quantum_allosteric-scanner (branch bartosz).
```

That is **Section 7, Team Capability — body content — on page 7.** The tool counts
the page on which the appendix *begins* as the first appendix page, so any body
spill onto that page is invisible to the check.

**Consequence:** every `body 6/6 PASS` reported this session, once the body reached
page 7, measured the wrong thing. Submission Guidelines §5: *"Submissions
exceeding the page limit may be returned or assessed only on the first 6 pages."*
The section that would be cut is Team Capability, which answers a 10% criterion.

**This is the gate we have been trusting to tell us we are compliant, and it
cannot detect the one violation that gets a submission returned.**

## Defect 2 — the build sentinel is in the shipped text layer

`SUBMISSION_BUILD_APPENDIX_START_7f3a9c` appears in page 7's extracted text.
Invisible when rendered; survives copy-paste and any automated screening an
organiser runs. It is our own marker, not part of the document.

## Intent Contract

- **Outcome:** a page check that counts body pages the way a reader (and an
  organiser's screening) would, and a PDF with no build-internal strings in it.
- **In scope:**
  1. **Count a page as body if it carries any body content**, regardless of where
     the appendix marker falls on it. A page shared between the two counts toward
     both, and the body count is what the limit applies to. Report both numbers
     and say when a page is shared.
  2. **Remove the sentinel from the output.** Options, in order of preference:
     locate the split by the appendix *heading* rather than an injected string;
     or render the marker in a way that leaves no text-layer trace; or strip it
     from the PDF after the split is computed. Do not simply recolour it —
     invisible-but-extractable is the current bug.
  3. **A regression test for each.** A fixture whose body deliberately spills onto
     the appendix's first page must FAIL the page check, and no build output may
     contain `SUBMISSION_BUILD`. These are the two tests whose absence let this
     ship.
- **Out of scope:**
  - Editing the submission to fit. That is [[TASK-0369]]'s job, and it must be
    done against a *correct* page count, which is why this task blocks it.
  - Changing the 6-page or 3-page limits, which come from the Guidelines.
- **Constraints and invariants:** every other compliance check keeps its current
  behaviour and its current output format; this is a correctness fix, not a
  redesign.

## Planned Validation

Re-run against the currently shipped PDF. The tool must now report the body as
**7 pages and FAIL**, not 6 and PASS. If it still passes, the fix is not done.

## Why this is first

Three tasks downstream ([[TASK-0369]], [[TASK-0370]], [[TASK-0371]]) all end in
"rebuild and check". Until this returns a true number, none of their results mean
anything, and we would be trimming text against a measurement we already know is
wrong.

## Done — 2026-09-11, Toolsmith

Both defects fixed at the root, in the shared `submission_build.py` layer both
routes reuse. Planned Validation re-run against the real, current submission
source and confirmed live.

### Defect 1 — shared-page detection

`analyze()` gained two new, default-`None` (fully backward-compatible)
parameters: `appendix_page` (a pre-located split page, for a caller that finds
it its own way) and `appendix_heading_pattern` (the literal heading substring,
used ONLY to detect a page shared between body and appendix). A page counts as
shared -- and therefore as BOTH a body page and the first appendix page -- when
real content precedes the heading's own occurrence on that page, not merely
"any text precedes the split point" (which would misfire on the heading's own
line: the heading text itself always sits between real body content and the
split, in both the old marker-based insertion and the new detector). `evaluate()`
and both routes' `render_report()` now name the shared page explicitly when one
exists ("page 7 carries both body content and the appendix start").

### Defect 2 — sentinel leak (LaTeX route)

Retired the injected-marker mechanism entirely for `submission_build_latex.py`
(`mark_appendix_start`/`_APPENDIX_MARKER_TOKEN`, deleted, TASK-0347/0349's own
code) -- Option 1 from this task's own Intent Contract, its first preference:
locate the split from the PDF's own real heading text, not an injected string.
New `_locate_appendix_by_heading(pages, heading_pattern, min_size_pt)`
(`submission_build.py`, shared) finds the FIRST occurrence of the heading
pattern rendered at >= `APPENDIX_HEADING_MIN_SIZE_PT` (11.0pt) -- i.e. as an
actual heading, not body prose merely containing the same words (TASK-0342's
own false-positive class, generalized: an inline "(Appendix C)" citation
renders at body size, 10.5pt, never heading size). Threshold picked from a
real measurement, not a guess: the real shipped PDF's actual heading measures
11.96pt (pdfplumber, `extract_words(extra_attrs=["size"])`), a single,
unambiguous occurrence across the whole document -- checked directly before
trusting the design, not assumed from the LaTeX class's documented defaults.
`RenderedPage` gained a `word_sizes: List[Tuple[str, float]]` field
(`pdf_to_pages` populates it) to make this possible; existing fields (`words`,
`char_sizes`) untouched, so TASK-0342's clipping check and the font-floor
check are unaffected.

The HTML/Chrome route (`submission_build.py`'s own `build()`) still uses its
original marker-based `_first_appendix_page` by default -- deliberately not
touched. That route's own docstring claims a forced page break makes a shared
page structurally impossible there, and there is no reported incident against
it (unlike the LaTeX route, where the shipped PDF proved it); changing its
split-detection mechanism too would be strictly more change than this task's
own reported defects require. Flagged as a known, latent residual -- if the
HTML route is ever used for a real shipped deliverable again, its own marker
text has the identical extractability problem and should get the same fix.

### Validation

- Full `submission_build.py`/`submission_build_latex.py` suite:
  **49 passed** (test_submission_build.py 24, test_submission_build_latex.py
  25 -- 4 new pure-function tests for the locator/shared-page logic, the
  4 `mark_appendix_start` tests deleted with the function they tested, 1 new
  source-level "never emits the retired marker string" guard, the real e2e
  compile test extended to also check the shipped PDF's text layer for the
  marker string).
  - Pure-function regression matching TASK-0342's own false-positive class,
    generalized to the new locator (`test_locate_appendix_by_heading_ignores_
    body_sized_mention`).
  - **This task's own required regression test**, built from the real
    shipped PDF's exact shape (Team Capability table + reference list before
    "Appendix -- References," all on page 7):
    `test_analyze_detects_a_page_shared_between_body_and_appendix` --
    asserts `body_pages == 7`, `shared_page == 7`, AND (the literal ask)
    `evaluate()` returns FAIL with "7 / 6" in the body-pages check.
  - Real e2e compile (`test_end_to_end_appendix_heading_split_compiles_and_
    lands_correctly`): confirmed the fixture's own real pagination shares a
    page too (not the clean break I'd assumed writing the fixture -- the
    test's assertion was wrong, not the code; fixed the assertion to check
    the correct relationship for either case, not one hardcoded shape) --
    caught by actually running it, not by reading the diff.
- **Planned Validation, run for real against the current submission source**
  (`PHASE1_SUBMISSION_V4.md` -- `DEFAULT_MD` itself is stale, still points at
  V2; used `--md` explicitly, flagged below, not fixed here):
  `.venv/bin/python .ai/tools/submission_build_latex.py --md .../PHASE1_
  SUBMISSION_V4.md --appendix-heading Appendix --no-change-report` ->
  **`[FAIL] body pages 7 / 6 (page 7 carries both body content and the
  appendix start...)`, `RESULT: FAIL`** -- exactly what this task's own
  Planned Validation demanded, not 6/PASS.
  Separately confirmed zero occurrences of `SUBMISSION_BUILD` in both the
  newly-built PDF's extracted text (all 7 pages, pdfplumber) and its `.tex`
  source (`grep -c`) -- Defect 2 closed on the real artifact, not just in a
  fixture.

### Found while validating, not fixed here (flagged, per this task's own
### "state impact before executing" discipline for anything beyond its scope)

- `submission_build_latex.py`'s `DEFAULT_MD` constant still points at
  `PHASE1_SUBMISSION_V2.md`; the real current source is `PHASE1_SUBMISSION_
  V4.md` (confirmed via the most recent real build's own report). A plain
  `submission_build_latex.py` invocation with no `--md` silently measures
  the wrong document. Not this task's call whether that's deliberate staging
  or simple staleness -- flagged for whoever next runs a real build to check
  first, not assumed either way.
- **Unrelated environment finding, discovered while running the full
  `.ai/tools/` suite for a final regression check**: every `git`
  subprocess call made FROM `.venv/bin/python` (an x86_64 interpreter) now
  fails -- `xcrun: error: unable to load libxcrun ... (have 'arm64,arm64e',
  need 'x86_64')`. Confirmed this is a pre-existing machine/toolchain issue,
  not caused by this task's changes: reproduced identically on
  `test_claim.py`'s pre-existing `TestChainedTransitionNoDuplicate` class
  (untouched by this task) and on a bare `git rev-parse HEAD` in the real
  repo, both via the same interpreter; `git` run directly (not as a child of
  `.venv/bin/python`) works fine. This task's own tests are unaffected
  (`submission_build.py`/`submission_build_latex.py` don't spawn fresh
  scratch git repos the way `test_claim.py`'s helper does) -- the 49/49
  pass count above is real and uncontaminated by this. Not fixed here:
  it needs Xcode Command Line Tools reinstalled/repaired at the OS level,
  a `sudo`-gated machine change outside this task's scope and this
  session's authority to make unprompted. Worth a dedicated task or a
  direct heads-up to the user -- `claim.py`'s own scratch-repo test suite
  (`test_claim.py`, ~40+ tests) cannot currently run to completion on this
  machine via `.venv/bin/python`.
