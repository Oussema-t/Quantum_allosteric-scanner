# 2026-07-31 rev-8 batch

Nine task files (TASK-0176, 0177, 0178, 0180, 0181, 0182, 0183, 0184, 0185)
were filed into `.ai/tasks/TODO/` verbatim on 2026-07-31 and registered in
`.ai/COMMON.md`'s Active Work Registry. TASK-0179 was retired before filing
(folded into TASK-0178) and its number is deliberately left unused.

Collision grep run at filing time (all local branches + all remotes):
TASK-0173/0174/0175, assumed "in flight" by TASK-0176's own header, do not
exist anywhere in this repo. No collision with 0176-0185 either way — see
TASK-0176's TODO checklist for the full note.

## What's still here

Reference implementations, kept in place per this project's "port, don't
cross-import" convention (same pattern as `2026-07-28/plant_prototype_REFERENCE.py`,
ported into `__WORK_IN_PROGRESS__/src/allostery/plant.py` by TASK-0167.001):

- `response_prototype_REFERENCE.py` — reference for TASK-0178
  (`src/allostery/response.py`).
- `conformational_search_prototype_REFERENCE.py` — reference for TASK-0185's
  ensemble+fpocket measurement.
