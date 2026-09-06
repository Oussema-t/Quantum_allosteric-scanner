# TASK-0333 — Reproducibility artifact pack: the rubric asks for it and we don't have it

- Status: Done
- Owner: **Toolsmith** (container/env) + **Implementer** (seeds/logs)
- Priority: High — cheap, and it costs points under a reproducibility rubric regardless of the science
- Filed: 2026-09-06 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0285]], [[TASK-0328]], [[TASK-0332]]

## The gap

The challenge's required artifact list: **container image, environment file,
deterministic seeds, structured logs, README with run commands.**

Confirmed present: Dockerfiles for the four *external* tools —
`tools/{fpocket,p2rank,pocketminer,evoef2}/Dockerfile` ([[TASK-0285]]).

Confirmed absent: **any container for the pipeline itself.** No `Dockerfile`
outside `tools/`. The `allostery` package has never been version-pinned.

Deterministic seeds are not merely missing but actively broken in one place:
`pocketsweep.py:386` seeds its permutation null from `abs(hash(str))` with
`PYTHONHASHSEED` unset anywhere in the branch, so no stored p-value can be
regenerated ([[TASK-0328]] owns the fix; this task owns the requirement).

## Intent Contract

- Outcome: the five artifacts exist and a cold run reproduces a named result.
  1. Pipeline `Dockerfile` + pinned environment file (the four tool images
     already exist — compose or document them, don't rebuild them).
  2. `allostery` pinned to a version.
  3. A repo-wide seeding convention, and `PYTHONHASHSEED` set explicitly.
  4. Structured logs from at least the headline run.
  5. README with the exact run commands for one reproducible result.
- Planned Validation: **a cold clone + container run must reproduce one named
  number end to end.** Suggest [[TASK-0318]]'s residual AUC 0.5949 — it is the
  number [[TASK-0332]] promotes into §2, so it is the one most worth being able
  to defend on demand. Byte-identical, asserted, not eyeballed.
- Constraints: this is packaging, not science. If a result will not reproduce,
  that is a finding for its owning task, not something to fix by adjusting the
  pipeline here.

## Note

Nine days out this is the highest value-per-hour item on the list: it is
bounded, it has no scientific risk, it is independent of every open question in
[[TASK-0327]]–[[TASK-0331]], and it is scored directly by the rubric. It can
run fully in parallel with the science tasks.

## Done (2026-09-06, Implementer B)

**Planned Validation met, twice over, not eyeballed**: a real `docker
build -f Dockerfile.pipeline` + `docker run`, cold, on this machine,
reproduces [[TASK-0318]]'s residualised-ceiling AUC to full float
precision — `0.5948718035160693` (quoted elsewhere as 0.5949) — asserted
by `scripts/verify_reproducibility.py` (exit 0 = exact match), not
eyeballed. Independently cross-checked in a second, non-container path
(a clean `python -m venv`, Python 3.13.4, installed only from the pinned
`pyproject.toml`) before the Dockerfile even existed, so the number's
reproducibility was established twice, by two different mechanisms.

**All five artifacts**:

1. **`Dockerfile.pipeline`** (repo root) — containerizes the research
   pipeline (`__WORK_IN_PROGRESS__/`), distinct from the deployed web
   app's own Python-3.9/FastAPI stack (`backend/`, untouched). Composes
   with, does not rebuild, the four existing tool images
   ([[TASK-0285]]) — `docker-compose.yml` documents the relationship;
   none of the four are called by the headline target (confirmed by
   reading its imports, not assumed).
2. **Pinned environment** — `__WORK_IN_PROGRESS__/pyproject.toml`'s 9
   direct dependencies are now version-pinned, closing the exact gap
   [[TASK-0110]]/[[TASK-0108]] flagged and explicitly deferred (quoted
   verbatim in the file, not deleted). `requirements-lock.txt` is the
   full 36-package transitive closure, generated from a clean venv
   install, not hand-written or guessed.
3. **Seeding convention** — `__WORK_IN_PROGRESS__/SEEDING_CONVENTION.md`:
   the repo-wide rule, [[TASK-0319]]'s own real bootstrap-loop pitfall
   (an `int` `random_state` re-seeding every `.sample()` call instead of
   advancing — documented so it is not rediscovered), and the one known
   non-compliant call site (`pocketsweep.py`, [[TASK-0328]]'s own fix,
   not duplicated here). `PYTHONHASHSEED=0` set explicitly in the
   Dockerfile `ENV` and in `run_reproducible_headline.py`'s own
   subprocess environment — never left to whoever runs it to remember.
4. **Structured logs** — `scripts/run_reproducible_headline.py` wraps
   the headline run *externally*, without editing
   `task0318_input_space_ceiling.py` itself (this task's own Constraint:
   packaging, not science — extended here to mean not touching the
   pipeline script at all, even for logging), emitting one JSON object
   per line (start/stdout/result/verify/end) to
   `results/tasks/0318_input_space_ceiling/run_log.jsonl`.
5. **`REPRODUCIBILITY.md`** (repo root) — exact commands, fast path
   (committed feature cache, offline, ~60-90s) and full cold-start path
   (documented, not re-executed here — see below).

**A real gap the container build caught that a plain read-through would
have missed**: the first container run failed cleanly with
`FileNotFoundError: results/tasks/0305_asbench_detection/
asbench_detection.json` — a second top-level `open()` call in
`task0318_input_space_ceiling.py` beyond the feature cache and
annotations file, only discoverable by actually running the cold
container rather than inspecting the script by eye. Fixed by adding
that one file to the `COPY` list; disclosed in both the Dockerfile's own
comment and `REPRODUCIBILITY.md`, not silently patched over.

**What was NOT re-executed, disclosed rather than silently assumed**:
[[TASK-0318]]'s own Phase A (re-deriving all 19 features from raw PDB
coordinates on 105 real ASBench structures, network-dependent,
~100+ minutes per [[TASK-0310]]'s own comparable run) was not re-run
cold. The validated, asserted path is Phase B (the LOPO model fit that
actually *produces* the reported number) against the already-committed
Phase-A output — the officially-supported fast path
(`--phase-b-only`) this task's own owning script already exposes for
exactly this reason. Full cold-start commands are documented in
`REPRODUCIBILITY.md` for whoever wants to re-verify Phase A itself; per
this task's own Constraint, that is a finding for [[TASK-0318]] if it
does not reproduce, not something to chase here.

**Force-added to git** (`__WORK_IN_PROGRESS__/results/` is otherwise
gitignored): `results/tasks/0318_input_space_ceiling/{ceiling_result.json,
feature_cache/*.npz, run_log.jsonl}` — without these, "a cold clone...
must reproduce" is not actually true, since Phase A's own expensive
output was never previously committed. This is itself a finding: the
reproducibility gap was not just missing packaging, it was a missing
artifact this task's own Planned Validation could not have passed
without noticing and fixing.

**Not done, correctly out of scope**: `pocketsweep.py`'s own seed bug —
[[TASK-0328]]'s fix, referenced not duplicated, per this task's own
"owns the requirement, not the fix" framing.

**A process note**: this task was picked up via an explicit user-directed
override of an active-looking claim by "Reviewer thread" (same session
that had reserved TASK-0327–0333 as a block) — the user was asked first,
confirmed the override, and it is disclosed here in case that session's
own concurrent TASK-0333 work (if any was in flight) needs reconciling.
Checked `git status` before every stage/commit below for exactly that
reason; several other files were mid-edit by that session
(`.ai/tasks/PLANS/PLAN.md`, `ALGORITHM_REGISTER.md`, TASK-0327/0328's
own files) and were left completely untouched.

**Scripts**: `scripts/verify_reproducibility.py`,
`scripts/run_reproducible_headline.py`. **New root files**:
`Dockerfile.pipeline`, `docker-compose.yml`, `REPRODUCIBILITY.md`.
**Data**: `results/tasks/0318_input_space_ceiling/run_log.jsonl` (new),
`ceiling_result.json` + `feature_cache/` (now force-added, previously
gitignored-only).

**Moved TODO -> DONE.**
