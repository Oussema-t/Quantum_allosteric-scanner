# Paper Citation Protocol

*Written after `.claude/hypotheses/reference_register.md` landed — 285 lines of
hypotheses extracted from the challenge's own bibliography by an external
session with no repo access, no RCSB access, and numbers computed on bundled
non-target structures. The register is good work and stayed in a reviews
folder, unintegrated, for a full day before [[TASK-0229]] gave it a home. Both
halves of that incident are why this protocol exists: a source worth using is
worthless if no one can find it, and a number from outside this repo's own
verification discipline is dangerous if it reads as validated.*

## Why this exists

Every implementer eventually needs to either (a) find out whether this
project already has a reference for a claim, or (b) use a paper's finding to
justify a task's design or interpret a result. Before this protocol there was
no fixed place to check first and no fixed rule for how much verification a
citation needs before it can be used in scored work or the submission. Two
concrete failure modes this is built to prevent, one already observed:

1. **A citation you remember is not a citation you've checked.** LLM-recalled
   author/year/journal/DOI combinations are wrong often enough that this
   project's own precedent ([[TASK-0156]]) explicitly verified three citations
   against the live article before trusting them, and found the exercise
   worth doing. Treat every author-year pair pulled from memory as unverified
   until its DOI resolves to the claimed paper.
2. **An externally-produced number can look identical to a locally-verified
   one once it's sitting in a task file.** The reference register's own
   header states plainly that its numbers came from bundled non-target
   structures — but nothing about *reading* a hypothesis document distinguishes
   a real result from a flagged-but-unverified one unless the reader checks
   the status tag every time. [[TASK-0229]]'s own standing caveat exists
   because this is a real, not hypothetical, risk on exactly this material.

## Before citing anything: check `documentation/REFERENCES.md` first

That file is the durable index — citation, DOI/URL, one-line takeaway, task
link if one exists. Check it before:
- Writing a new citation into a task file, `RESULTS.md`, or the submission.
- Filing a task whose Intent Contract rests on a paper's claim.
- Assuming "the literature says X" in an Open Question or Constraint.

If the source you need isn't there, add it (see below) rather than citing it
inline-only — a citation that exists in one task file and nowhere else is
already halfway to the same "unintegrated for a day" problem this protocol
responds to.

## Adding a new reference

1. **Verify the DOI resolves to the paper you think it is** — author names,
   year, journal, and (if checkable) the actual claim you're about to cite.
   Don't add a citation you haven't at least confirmed exists as described.
2. **Add one row** to the relevant table in `REFERENCES.md` (challenge
   bibliography vs. method/tool papers — extend the file's own section
   structure rather than starting a new document): full citation, DOI link,
   a status tag if this project has tested the claim (`UNTESTED` / `PARTIAL`
   / `OBSERVED` / `CONTESTED` — [[TASK-0229]]'s own tagging convention, reuse
   it, don't invent a new one), a one-line takeaway **in this project's own
   words**, not a copy of the abstract, and a task link if one exists.
3. **If you hold a local copy** (downloaded PDF, notebook export, extracted
   text) of the source, put it under `__WORK_IN_PROGRESS__/documentation/
   references/` — gitignored, not project output, purely a convenience cache.
   Never assume it will still be there on a fresh checkout; the tracked
   `REFERENCES.md` entry is what persists, the local copy is not.

## Using a claim from a reference in actual work

State **which** of these three you're doing, every time — conflating them is
the exact failure mode this protocol exists to prevent:

- **A direct claim from the paper.** Cite it as such (`[[REFERENCES.md]]#N`
  or the DOI directly), and if the claim is load-bearing for a task's
  Intent Contract or a submission sentence, quote or closely paraphrase the
  specific finding rather than gesturing at "the paper shows...".
- **This project's own re-derivation or test of the paper's claim.** State
  the result as this project's own finding, citing the paper only as the
  source of the *hypothesis being tested* — not as the source of the number.
  This is the normal, correct shape for most of `RESULTS.md`.
- **A claim inherited from an external, unverified drop** (like the
  reference register). Carry its own caveat forward explicitly — do not
  strip the caveat off just because the claim is now sitting in a task file
  that looks like every other task file. If the source document says
  "PDB-RETEST: YES" or similar, that qualifier travels with the claim until
  someone actually retests it, not just until someone re-quotes it.

## Verification bar before a claim reaches the submission

Nothing from an external, no-repo-access source may be cited in the
submission document ([[TASK-0184]]) as a validated result before it has been
re-run against real challenge targets in this repo — this is [[TASK-0229]]'s
own standing caveat, stated here as the general rule it actually is, not a
one-task exception. A paper's own claim (not this project's re-test of it)
can be cited as background/motivation without that bar — the bar is for
*this project's own numbers*, wherever they came from.

## Worked example

`.claude/hypotheses/reference_register.md` → `.ai/tasks/TODO/TASK-0229-*.md`
(parent) → `.001`-`.007` (subtasks, one per hypothesis family) →
`documentation/REFERENCES.md` (the durable index this protocol points at).
Follow that chain to see the shape this protocol asks for: a claim found,
tagged with its own honest confidence level, given a task if it's worth
running down, and indexed somewhere a later reader can actually find it.
