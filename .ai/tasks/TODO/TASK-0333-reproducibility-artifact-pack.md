# TASK-0333 — Reproducibility artifact pack: the rubric asks for it and we don't have it

- Status: TODO
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
