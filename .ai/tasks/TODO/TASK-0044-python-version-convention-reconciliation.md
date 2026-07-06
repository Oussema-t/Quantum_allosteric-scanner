# TASK-0044 Reconcile the "Python 3.9" convention against the actual 3.11.9 deploy runtime and a 3.10+-only dependency

## Context

- ID: TASK-0044
- Title: Verify, settle, and document the correct Python version floor for
  this repo — the "Python 3.9" convention stated in CLAUDE.md/SOFTWARE.md/
  AGENTS.md does not match the deployed runtime, and is already contradicted
  by a pinned dependency.
- Status: TODO
- Owner: Architect/Planner (decision + doc-sync); no code change expected.
- Source: user request, 2026-07-06 session — asked why 3.9 was chosen over
  latest/3.12 while setting up a local venv (no `python3.9` binary available
  on the dev machine, so venv was created under 3.12). Investigation below
  is that session's findings, not yet a settled decision.
- Scope: `CLAUDE.md`, `SOFTWARE.md`, `AGENTS.md` (the three places stating
  "Python 3.9"), `render.yaml`, `DEPLOY.md`, `requirements.txt` (`biotite`
  pin specifically).

## Intent Contract

- Outcome: one recorded, justified answer to "what Python version floor
  does this repo actually target," with all three convention-statement
  files (CLAUDE.md convention 1, SOFTWARE.md §"Conventions" item 1,
  AGENTS.md stack line) updated to say the same, correct thing in the same
  commit (CLAUDE.md convention 7: docs/code change together).
- In Scope:
  - Confirm whether "3.9" was ever meant as a literal interpreter pin, or
    only as a syntax-compatibility floor (no `X | None` PEP 604 unions).
  - Confirm the real deploy runtime (`render.yaml` says 3.11.9 — verify
    this is still what Render actually runs, not just what the file says).
  - Resolve the `biotite==0.41.0` conflict: PyPI metadata marks it
    `requires-python:>=3.10`, which is incompatible with a literal-3.9
    reading of the convention.
  - Decide the actual floor going forward (candidates: keep 3.11.9 runtime
    + relax the "no `X | None`" rule to whatever 3.11 already permits
    safely; or keep a stricter syntax floor for portability reasons if one
    is articulated) and update the three docs to match.
- Out Of Scope: changing `requirements.txt` pins or `render.yaml`'s runtime
  version themselves unless the decision requires it (e.g. if 3.9 turns out
  load-bearing for some untested reason — unlikely per evidence below, but
  not yet ruled out).
- Acceptance Scenarios:
  - Given a fresh reader of CLAUDE.md/SOFTWARE.md/AGENTS.md, when they read
    the Python-version convention, then it matches what `render.yaml`
    actually deploys and what `requirements.txt` actually requires — no
    contradiction discoverable by grep.
  - Given the `biotite==0.41.0` pin, when installed under whatever floor
    the docs end up stating, then there is no version floor/dependency
    mismatch left unexplained.
- Constraints And Invariants:
  - Don't silently rewrite the convention without recording *why* (this
    task's Done section is that record) — per this session's own finding,
    the original "why" for 3.9 was never documented anywhere, so this
    task's output is partly a retroactive rationale, partly a correction.
  - Any doc edit must touch CLAUDE.md, SOFTWARE.md, and AGENTS.md together
    (CLAUDE.md convention 7) — not just one of the three.
- Planned Validation: `grep -rn "3\.9\|3\.10\|3\.11" CLAUDE.md SOFTWARE.md AGENTS.md render.yaml DEPLOY.md` after the edit shows one consistent version story, not three different ones.

## Findings from the 2026-07-06 investigation (evidence, not yet a decision)

1. **The deployed runtime has never been 3.9.** `render.yaml:14-15` pins
   `PYTHON_VERSION: "3.11.9"`, added in commit `bcc302a` ("Add login gate
   (HTTP Basic Auth) + Render deploy config", 2026-06-22). `DEPLOY.md:28`
   states the same value for manual dashboard setup. This predates the
   "3.9" convention below by three days.

2. **The "3.9" convention was introduced later, and reads as a syntax
   rule, not a runtime pin.** Added in commits `4e6e148` ("Add CLAUDE.md +
   AGENTS.md", 2026-06-25) and `23cac6e` ("Add SOFTWARE.md"). All three
   places phrase it as: "Python 3.9 — use `typing.Optional`/`List`, never
   `X | None` at runtime" (CLAUDE.md convention 1; SOFTWARE.md §Conventions
   item 1 near line 253; AGENTS.md stack line). That's a ban on PEP 604
   union syntax (3.10+), i.e. a *syntax-compatibility floor*, not
   necessarily "the interpreter must be literally 3.9."

3. **No commit message, task file, or doc records why 3.9 specifically was
   chosen.** Checked: `git log --all -S "3.9"` (only touches the three doc
   files above) and `git log --all -S "Python 3.9"` (same three commits).
   No PR description, no `.ai/tasks/` entry, no code comment gives a
   reason. `.ai/tasks/TODO/TASK-0021-backend-api-test-baseline.md:71` cites
   "Python 3.9 conventions apply (CLAUDE.md convention 1)" but only
   *references* the rule, doesn't explain its origin.

4. **A pinned dependency already contradicts a literal-3.9 reading.**
   `requirements.txt:7` pins `biotite==0.41.0`. Installing it in a fresh
   3.12 venv (this session, `pip install -r requirements.txt`) succeeded
   but with: `WARNING: The candidate selected for download or install is a
   yanked version: 'biotite' (version 0.41.0 ... requires-python:>=3.10)`.
   So `biotite==0.41.0` cannot install on a literal Python 3.9 interpreter
   at all — the pin and the stated convention are already inconsistent,
   independent of anything this session did.

5. **Working inference (labeled Inference, not confirmed):** 3.9 was
   likely chosen as a conservative baseline for hackathon/judge-environment
   portability (unknown grader Python version at submission time) rather
   than tied to a real technical constraint — since the actual deploy
   target was always 3.11.9 and a core dependency already needs 3.10+.
   This task should confirm or refute this inference with whoever set the
   convention, if traceable, rather than treat it as settled.

6. **Local dev-environment note (not part of the doc fix, context only):**
   this session's sandbox has no `python3.9` binary installed; the venv
   created for local development runs 3.12. Not itself evidence for what
   the convention *should* say, but confirms 3.9 is not universally
   available even for contributors trying to follow the current wording
   literally.

## In Progress

None

## TODO

- [ ] Confirm with whoever owns the convention (or infer from any
      untracked source, e.g. challenge submission rules for Global Quantum
      + AI Challenge 2026, if such a constraint exists) whether 3.9 was
      ever a hard external requirement.
- [ ] Decide the stated floor: keep "avoid `X | None`, target 3.11.9
      runtime" as the corrected wording, or something else if a real
      constraint surfaces.
- [ ] Update CLAUDE.md convention 1, SOFTWARE.md §Conventions item 1, and
      AGENTS.md's stack line together, in one commit, to state the
      resolved version floor consistently.
- [ ] Resolve the `biotite==0.41.0` requires-python:>=3.10 conflict
      explicitly in the doc update — either note that the "3.9" floor was
      always aspirational/syntax-only (not a literal interpreter
      requirement), or re-pin `biotite` if literal 3.9 support turns out
      to matter (out of scope for this task per Constraints unless the
      decision requires it).
- [ ] Add a dated `ARCHITECTURE.md` change-log line per CLAUDE.md
      convention 7 once the doc edit lands.

## Dependency

None — self-contained doc/decision task. Not blocking any other TASK-XXXX;
flag if TASK-0021 (backend API test baseline) or any future contributor
guidance references the corrected convention once settled.

## Open Questions

- Was there ever an external constraint (challenge submission environment,
  a specific judge's grading harness) that required 3.9, or is that a myth
  that calcified into a convention? Unresolved — see Finding 5.
- Does "avoid `X | None`" need to remain a rule at all if the real runtime
  is 3.11.9 (which fully supports PEP 604)? Or is there a separate reason
  (e.g. wanting code portable to a hypothetical older grading environment)
  to keep avoiding the newer syntax regardless of what Render runs?

## Done

(not yet)
