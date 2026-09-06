# Reproducibility (TASK-0333)

This is the artifact pack the challenge's reproducibility rubric asks
for: a container image, a pinned environment, deterministic seeds,
structured logs, and one named result that a cold clone can reproduce
on demand.

**Scope**: this covers the *research pipeline*
(`__WORK_IN_PROGRESS__/`, the `allostery` package and its `task0NNN_*.py`
analysis scripts) — not the deployed web app (`backend/` + `frontend/`,
Python 3.9, FastAPI, unaffected by anything below, still deployed and
run exactly as `CLAUDE.md` already documents). These are two separate
codebases with separate dependency stacks; conflating them here would
misrepresent which one this pack makes reproducible.

## The five artifacts

1. **Container image** — `Dockerfile.pipeline` (repo root). Composes
   with, but does not rebuild, the four pre-existing external-tool images
   (`tools/{fpocket,p2rank,pocketminer,evoef2}/Dockerfile`, [[TASK-0285]]);
   see `docker-compose.yml` for how all five relate — the headline target
   below calls none of the four tools, confirmed by reading its imports.
2. **Pinned environment** — `__WORK_IN_PROGRESS__/pyproject.toml`'s own 9
   direct dependencies are now version-pinned (closing the gap
   [[TASK-0110]]/[[TASK-0108]] explicitly flagged and deferred);
   `__WORK_IN_PROGRESS__/requirements-lock.txt` is the full 36-package
   transitive closure, generated from a clean venv, not hand-written.
3. **Deterministic seeds** — `__WORK_IN_PROGRESS__/SEEDING_CONVENTION.md`:
   the repo-wide rule, a real bootstrap-loop pitfall found and fixed by
   [[TASK-0319]] (documented there so it isn't rediscovered), and the one
   known non-compliant call site ([[TASK-0328]]'s own, not fixed here).
   `PYTHONHASHSEED=0` is set explicitly in `Dockerfile.pipeline` and in
   `scripts/run_reproducible_headline.py`'s own subprocess environment.
4. **Structured logs** — `scripts/run_reproducible_headline.py` wraps the
   headline run (without editing it — packaging, not science) and emits
   `results/tasks/0318_input_space_ceiling/run_log.jsonl`, one JSON object
   per event (start/stdout/result/verify/end), machine-parseable.
5. **This README** — exact commands below.

## The one reproducible result

[[TASK-0318]]'s residualised-ceiling AUC, the number [[TASK-0332]]
promotes into the submission's own §2 — chosen per this task's own
Planned Validation as "the one most worth being able to defend on
demand":

```
0.5948718035160693   (quoted elsewhere, rounded, as 0.5949)
```

### Fast path (recommended — what the container image runs by default)

Uses the feature cache already committed under
`results/tasks/0318_input_space_ceiling/feature_cache/` (Phase A's own
expensive output, re-derived from 105 real ASBench PDB structures once
and cached — see [[TASK-0318]]'s own script docstring). Fully
deterministic, no network access needed, ~60-90s.

```bash
docker build -f Dockerfile.pipeline -t qas-pipeline .
docker run --rm qas-pipeline
# runs scripts/run_reproducible_headline.py, which:
#   1. runs task0318_input_space_ceiling.py --phase-b-only with
#      PYTHONHASHSEED=0
#   2. asserts the result against 0.5948718035160693 via
#      scripts/verify_reproducibility.py (exit 0 = byte-identical match)
#   3. writes results/tasks/0318_input_space_ceiling/run_log.jsonl
```

Without Docker, from a venv built off `requirements-lock.txt` (see
below), from `__WORK_IN_PROGRESS__/`:

```bash
python3 -m venv .venv-repro && source .venv-repro/bin/activate
pip install -r requirements-lock.txt
pip install -e . --no-deps
python3 scripts/run_reproducible_headline.py
```

**Verified before this file was written, not asserted on faith, two
ways**: (1) in a completely clean venv (`python -m venv`, Python 3.13.4,
no prior packages, installed only from the pinned `pyproject.toml` /
`requirements-lock.txt`); (2) a real `docker build -f Dockerfile.pipeline`
+ `docker run` from that image, cold, on this machine. Both reproduce
`0.5948718035160693` to full float precision — exact, not "close
enough." The container build caught a real gap the venv check alone
missed: the script also reads `results/tasks/0305_asbench_detection/
asbench_detection.json` at import time, not just the feature cache and
annotations — a clean `FileNotFoundError` on the first container run
named exactly what was missing, fixed in `Dockerfile.pipeline`.

### Full cold-start path (re-derives the feature cache from raw PDB data)

**Not re-executed as part of this task's own validation** (network-
dependent RCSB fetches across 105 structures plus every TASK-0310
observable, including chiral circulation's own per-field-direction
Peierls Hamiltonian construction — [[TASK-0310]]'s own Done section
records ~111 minutes wall time for a comparable run). Documented for
completeness; if it does not reproduce, that is a finding for
[[TASK-0318]], not a defect in this packaging task (this task's own
Constraint: "packaging, not science").

```bash
rm -rf results/tasks/0318_input_space_ceiling/feature_cache
python3 scripts/task0318_input_space_ceiling.py   # Phase A + Phase B, no --phase-b-only
python3 scripts/verify_reproducibility.py
```

## Regenerating the lock file

If `pyproject.toml`'s pins ever change:

```bash
python3 -m venv /tmp/relock && /tmp/relock/bin/pip install -e __WORK_IN_PROGRESS__/
/tmp/relock/bin/pip freeze > __WORK_IN_PROGRESS__/requirements-lock.txt
```
