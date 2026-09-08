# TASK-0349 — `--appendix-heading` breaks the LaTeX compile: the branch has never been exercised

- Status: TODO
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
