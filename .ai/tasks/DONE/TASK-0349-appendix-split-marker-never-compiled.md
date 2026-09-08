# TASK-0349 — `--appendix-heading` breaks the LaTeX compile: the branch has never been exercised

- Status: Done
- Owner: **Toolsmith** (owns `submission_build_latex.py`)
- Priority: Medium — not blocking today, but it gates the 3-page appendix allowance
- Filed: 2026-09-08 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0347]], [[TASK-0341]], [[TASK-0319]]

## Symptom, bisected

```
submission_build_latex.py                            -> RESULT: PASS
submission_build_latex.py --appendix-heading Appendix -> tectonic exited 1
```

Identical source both times. **The failure is in the marker path, not the
document** — the references appendix added today compiles fine when the split is
not requested.

## Why it was never caught

Every build to date has reported *"no `#appendix` marker found in the render"*.
`mark_appendix_start()` is a documented no-op when the pattern is absent, so the
insertion branch has **never executed in a passing build**. It was written, the
tool shipped green, and the first real use of it fails.

This is [[TASK-0319]]'s standing finding in a new place: a branch with no test
that exercises it is not verified by the suite passing.

## What is ruled out

`xcolor` **is** loaded (`submission_build_latex.py:138`), so the
`\color{white}` in the marker is not an undefined-macro failure — that was the
obvious hypothesis and it is wrong. The actual TeX error has not been read; the
failing run does not appear to retain a `.log` or `.tex` to inspect.

**First step is therefore to make the failure legible**, not to guess at the fix:
have the tool preserve the generated `.tex` and tectonic's log on a failed
compile. Right now a compile failure destroys its own evidence, which is a defect
in its own right and the reason this task cannot name a root cause.

## Intent Contract

- Outcome: `--appendix-heading` produces a compiling PDF with the appendix split
  correctly detected, and the report shows a non-zero appendix page count.
- On failure, the tool retains `.tex` and `.log` under the build directory so the
  next person does not have to re-derive the error.
- **Ships with a test that actually exercises the split** — a fixture with an
  appendix heading, asserting both that it compiles and that the reported split
  lands on the right page. A no-op-when-absent test does not cover this.
- Constraint: do not solve it by removing the marker mechanism. The split has to
  be detected in the rendered PDF, and searching rendered prose for a heading
  word is the failure mode the invisible marker exists to avoid.

## Why it matters, though not today

§4.4 allows **3 appendix pages** for "technical diagrams, references, prior
work". References are explicitly named. With the split working, the 15 references
added today move out of the 6-page body and free most of a page for content.
Today they fit inside the body at 6/6, so nothing is blocked — but the margin is
zero, and [[TASK-0345]]/[[TASK-0346]] results are still to land.

## Done (2026-09-08, Implementer C)

**Root cause found and fixed, not guessed at — the failure was made legible
first, per this task's own required first step.**

### Root cause

`--keep-logs` was missing from the `tectonic` invocation, so a FAILED
compile left no `.log` on disk at all — confirmed live: tectonic's own
stdout claims "Transcript written to ...log" but writes no file unless
asked. Added `--keep-logs`; re-ran the exact bisected failing command
(`--appendix-heading Appendix` against the real `PHASE1_SUBMISSION_V2.md`)
and read the real transcript:

```
! Missing $ inserted.
<inserted text>
                $
l.243 ...ntsize{10.5}{13.5}\selectfont SUBMISSION_
                                                  BUILD_APPENDIX_START_7f3a9c}
```

`_APPENDIX_MARKER_TOKEN` (`"SUBMISSION_BUILD_APPENDIX_START_7f3a9c"`,
shared with the HTML route in `submission_build.py`) contains raw `_` —
harmless inside an HTML `<span>`, but `_` is LaTeX's math-mode subscript
operator in plain text: writing the token unescaped inside the marker's
`{\color{white}...}` group is exactly the textbook "bare underscore in
text mode" defect, and produces an unrecoverable XeTeX halt. **`xcolor`
being loaded was correctly ruled out already by the filing** — the real
defect was one line further into the marker string.

### Fix

`mark_appendix_start()` now escapes the token (`_` → `\_`) **only in this
module**, not by changing the shared token in `submission_build.py` — the
HTML route's literal underscores are correct as-is; the two routes need
different escaping of the same logical token, not a different token.
Verified the escaping doesn't break detection: the split is read back from
the rendered PDF's extracted *text* (pdfplumber), and `\_` typesets to a
literal `_` glyph — `_APPENDIX_MARKER_TOKEN in pg.text` still matches
downstream, unchanged.

**Re-ran the exact bisected command after the fix**: compiles, `RESULT:
PASS`, non-zero appendix page count reported correctly (`body pages 4/6`,
`appendix pages 2/3`, `split rule: ... body = pages 1-4, appendix = pages
5-6`) — the outcome this task's own Intent Contract names as Done.

### Evidence retention (Intent Contract's own required first step)

`compile_latex()` now always passes `--keep-logs`; on a failed compile the
error message names the `.log` path directly when one was produced (and
says so explicitly when tectonic died before writing one at all, rather
than silently omitting the note). The `.tex` was already retained
unconditionally before this task (written to disk before `compile_latex`
is ever called) — the actual gap was the `.log` side only, now closed to
match.

### Test — ships with a fixture that actually exercises the split

Per this task's own Constraint ("A no-op-when-absent test does not cover
this"): `test_end_to_end_appendix_heading_split_compiles_and_lands_correctly`
builds a real fixture (6 filler sections + a genuine `## Appendix`
heading) through `--appendix-heading`, end to end, and asserts (a) it
compiles with no error, (b) the reported split lands strictly after page
1 and at or before the last page, and (c) `body_pages == appendix_starts_
on_page - 1` — the split lands exactly where the body ends, not merely
"somewhere". Caught its own fixture bug on the first run: the document's
own `# Split fixture` title originally read `# Appendix split fixture`,
and `mark_appendix_start`'s substring search matched "Appendix" inside
the TITLE first, reporting `appendix_starts_on_page: 1` (whole document
misclassified as appendix) — fixed the fixture, not the tool, since a
literal-substring search matching an unintended earlier occurrence is a
fixture-design bug, not a defect in the search itself (the real
submission's own single `## Appendix — References` heading has no such
collision). Also added a direct regression guard,
`test_mark_appendix_start_escapes_underscores_for_tex_text_mode`, that
fails if the raw (unescaped) token ever reappears in LaTeX output. Full
suite: 48 pass (`test_submission_build.py` + `test_submission_build_latex.py`,
this task's own 24, up from 22).

### Constraints honored

Marker mechanism kept — detection still reads the rendered PDF, not
rendered prose for a heading word (the [[TASK-0342]] lesson this task's
own Constraint names explicitly). Nothing guessed before the log was
readable.

**Files**: `.ai/tools/submission_build_latex.py` (escaping fix, `--keep-logs`,
log-path-on-failure), `.ai/tools/test_submission_build_latex.py` (2 new
tests, 1 existing test updated for the new escaped-token contract).
