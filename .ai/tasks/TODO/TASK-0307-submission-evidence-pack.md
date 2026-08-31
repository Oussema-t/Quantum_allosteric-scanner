# TASK-0307 — Submission evidence pack: every number in TASK-0184, traced to a committed artifact

- Status: TODO
- Priority: **Critical — the Phase 1 deadline is 2026-09-15 and this register's headline numbers have moved repeatedly in the last week**
- Filed: 2026-08-31 by Reviewer thread
- Related: [[TASK-0184]], [[TASK-0288]], [[TASK-0297]], [[TASK-0298]], [[TASK-0299]], [[TASK-0300]], [[TASK-0304]], [[TASK-0305]]

## Why

Numbers that were correct a week ago are now wrong, and several are quoted
in a brief already sent to the collaborator:

| quantity | was | now | moved by |
|---|---|---|---|
| pocket-level ceiling (in-sample) | 0.1649 | **0.0899** | [[TASK-0298]] |
| pocket-level ceiling (LOTO) | 0.122 | **0.0000** | [[TASK-0298]] |
| Finding F spike | 9/28, p=2.03e-06 | **8/28, p=1.51e-05** | [[TASK-0297]] |
| Finding F headline | "~32%" | **"~29%"** | [[TASK-0297]] |
| "classical ceiling beats CTQW" | claimed | **retracted** | [[TASK-0299]] |
| SVC figures | quoted | **withdrawn** | stability re-run, `34bf290` |
| KRAS P@5 | 0.200 | **0.000** | [[TASK-0283]] |

This register has already shipped a stale number once (the 0.200 P@5 in
the brief). It must not happen in the submission.

## Scope

- [ ] Enumerate **every** quantitative claim destined for [[TASK-0184]]
      and the collaborator brief (`CTQW_CONTRIBUTION_BRIEF.html`).
- [ ] For each: the current value, the **committed artifact** it comes
      from (path + commit SHA), and the task that last changed it.
- [ ] **Flag every figure whose source artifact predates the commit that
      last invalidated it.** That is the actual deliverable — a stale-list.
- [ ] Produce one table, committed, that the write-up can be checked
      against line by line.
- [ ] Explicitly cover: Finding F (spike count, p, %, and whether stated
      on `min_A` or `max_A` — [[TASK-0291]] recommends `max_A`), the
      ceiling numbers, the CTQW comparison, the ASBench figures
      ([[TASK-0304]]/[[TASK-0305]]), and the attribution shares
      (geometry / CTQW / unexplained).

## Constraints

- **Verify, do not re-derive.** If a number cannot be traced to a
  committed artifact, that is the finding — report it, do not recompute a
  replacement and quietly substitute it.
- **Do not edit the brief or [[TASK-0184]].** This task produces the
  audit; applying it is a separate, deliberate step by whoever owns those
  documents.
- Where a claim's wording (not its number) is now wrong — e.g. "classical
  ceiling outperforms CTQW" — flag the wording too.
