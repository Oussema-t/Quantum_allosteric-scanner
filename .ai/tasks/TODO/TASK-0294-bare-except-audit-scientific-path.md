# TASK-0294 — Audit the scientific path for bare `except Exception` that can silently substitute an input

- Status: TODO
- Assignee: unassigned
- Priority: Medium — **LANE 3, read-only, blocks nothing and is blocked by nothing**
- Filed: 2026-08-29 by Reviewer thread (split out of [[TASK-0290]] so it cannot block the recompute)
- Related: [[TASK-0289]], [[TASK-0253]], [[TASK-0290]]

## Why

Twice now this register has been damaged by the same pattern: a bare
`except Exception` that returns **plausible numbers instead of raising**.

- [[TASK-0253]] — an unresolved active site produced an all-NaN score
  array that `np.argsort` silently turned into fabricated-looking ranks.
- [[TASK-0289]] — `backend/active_site.py:174-187` silently downgrades
  through a three-tier fallback on any network hiccup, swinging
  `HCV_NS5B_POO`'s `min_A` between 1.33 Å and 17.94 Å by call order alone.

Both were found by accident, months apart, while investigating something
else. Phase 2 adds more network-backed inputs. This task is the
systematic sweep neither of those got.

## Scope

- [ ] Enumerate every `except Exception`, `except:`, and broad
      `except (A, B)` in the scientific path — `src/allostery/`,
      `backend/`, and `__WORK_IN_PROGRESS__/scripts/` helpers that other
      scripts import (`task0242`, `task0255`, `task0257`, …).
- [ ] For each, classify:
      **(i) benign** — genuinely optional, the fallback is equivalent;
      **(ii) LOUD-NEEDED** — swallows a real error and substitutes a
      different input, changing a scientific result;
      **(iii) MASKING** — hides a bug that should surface.
- [ ] Report as a table: file:line, what it catches, what it substitutes,
      and which published result could move if it fired.
- [ ] **Do not fix them in this task.** Report first. A blanket
      narrow-the-except pass risks breaking working paths and would
      collide with Lane 1, which owns `backend/active_site.py`.

## Constraints

- **Read-only.** No edits to `backend/` or `src/` in this task. If a
  fix is obviously required, file it as a follow-up with the evidence.
- Do not touch `backend/active_site.py` — [[TASK-0290]] owns it this
  window. Note it in the table and move on.
- No compute needed. This lane must not contend for the machine with
  Lane 1's recompute or Lane 2's LOTO.

## Why it is worth a lane at all

The two known instances both produced **publishable-looking numbers**
rather than errors, and both survived into committed results. The value
here is not the fixes — it is knowing how many more of these are sitting
under the Phase 1 claims before the write-up is drafted.
