# TASK-0367 — The page-count check cannot see the violation it exists to catch, and the build sentinel ships inside the PDF

- Status: TODO
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
