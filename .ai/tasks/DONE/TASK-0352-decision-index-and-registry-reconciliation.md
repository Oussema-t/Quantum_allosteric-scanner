# TASK-0352 — An index of where decisions live, and a three-way consistency check. Not a search tool.

- Status: Done
- Owner: **Toolsmith**
- Priority: Medium — **do not start before 2026-09-15**
- Filed: 2026-09-09 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0321]], [[TASK-0322]], [[TASK-0323]], [[TASK-0326]], [[TASK-0270]], [[TASK-0349]]

## Why this is an index and not a search tool

The repo owner proposed a search tool and flagged it as risky in the same breath.
That instinct is right and the task is scoped around it.

**A search tool makes a *negative* result authoritative.** *"I ran the register
search and found nothing"* reads far stronger than *"I grepped and found
nothing"* — and if coverage is incomplete, that confident negative **licenses**
the assumption it was built to prevent. Strictly worse than no tool.

This register has produced that exact failure repeatedly: the page counter wrong
by >2× ([[TASK-0344]]), the appendix marker that never compiled ([[TASK-0349]]),
the bootstrap LRT re-seeding bug ([[TASK-0319]]), `hyp_register_check`'s own
status-detection bug. Every one was a checker trusted because it existed.

**Search cost is also not the binding constraint.** A grep over four directories
takes seconds; [[TASK-0321]] measured a **9% citation rate**. That is not "grep
was too slow", it is "nobody looked". A faster grep does not fix that.

**The decisive property**: an index can be checked for staleness. A search cannot
be checked for completeness. Build the thing that can be verified.

## Part B first — the three-way reconciliation (cheap, mechanical, do this one)

Three sources of truth about live work disagree silently today:

| source | what it knows |
|---|---|
| `.ai/tasks/.locks/*.lock` | who holds what |
| `.ai/tasks/{TODO,IN_PROGRESS,DONE}/` | what state the file claims |
| `.ai/COMMON.md` Active Work Registry | what a fresh session actually reads |

**Measured 2026-09-09, the incident that prompted this**: [[TASK-0350]] was
claimed and *running*, its file still under `TODO/`, and it had **no registry row
at all** — nor did [[TASK-0347]] or [[TASK-0351]]. All three were filed by the
Reviewer thread, which omitted the rows despite COMMON.md's own explicit rule.
The lock prevented a collision; **the coordination hub simply did not know the
work existed.**

- Outcome: one command reporting every disagreement — claimed but no registry
  row, registry row but no file, file in `DONE/` with a live claim, `Status:`
  line disagreeing with its folder, row `Status` disagreeing with either.
- This is a consistency check over **structured** data. It is deterministic,
  needs no judgement, and would have caught the incident above the moment the
  task was filed. **It should ship even if Part A never does.**
- Reuse `claim.py`'s own lock-reading and disk-scan (`task_locate.py` already
  does this for a single id — generalise it, do not write a second scanner).

## Part A — the decision index (harder, judgement-laden, gated on B)

Where the four recent assumption failures actually had their answers:

| assumed | where the answer was |
|---|---|
| "just run the suggested `8S8C`" | **`config/targets.yaml` inline comment** |
| "KRAS numbering looks like an index bug" | targets.yaml + the PDB itself |
| "the chiral walk was the only interference test" | [[TASK-0130]], cited by four tasks |
| "consistent with the JACS ρ≈0.95" | nowhere — genuinely unmeasured |

**Two of four sat in a config file's comments**, which no task-file search would
reach and which nobody thinks to grep. That is not a search problem — it is that
**decisions and their reasons are scattered across places nobody enumerates.**

- Outcome: a generated index, one line per recorded decision: *what was decided,
  when, and **where the reason lives*** — pointing at least at `config/targets.yaml`,
  `documentation/2026-08-26-organiser-clarifications.md`,
  `.claude/hypotheses/*`, the retraction record, and DONE task verdicts.
- **Record the pointer, never restate the reason.** A restatement drifts from its
  source and then there are two answers, which is worse than one hard-to-find
  one. This is the single most important constraint in this task.
- [[TASK-0322]] built exactly this shape for hypotheses. Follow that precedent
  rather than inventing a second one.

## Constraints And Invariants

- **Ships with a test that fails on a seeded gap** — remove a registry row, the
  check must go red. [[TASK-0319]]'s standing rule, and the specific reason Part
  B is trustworthy where a search tool would not be.
- **Never summarise or rank.** If any output is truncated it must say so
  explicitly and print how many were withheld.
- Read-only. It reports drift; it does not repair it. Auto-repair of a contended
  file is how the Active Work Registry got reverted twice in one session
  (COMMON.md's own 2026-07-04 note).
- No new source of truth. The index is *derived*; if it and the source disagree,
  the source wins and the index is stale.

## Timing, and the honest reason to wait

**Do not start before 2026-09-15.** [[TASK-0350]] and [[TASK-0351]] are unstarted
and the deadline is six days out; this is tooling, not submission work.

There is also a real epistemic reason: **the standing "check the register before
you assume" rule landed on 2026-09-08 and nobody has yet had a chance to follow
it.** If agents keep assuming with the rule in front of them, that is the evidence
Part A is needed — and the failures will say what to index. Building it now means
guessing at the index's contents from four data points.

## Hold released — 2026-09-09, Reviewer thread

**The Toolsmith may pick this up now.** The "do not start before 2026-09-15" line
above is superseded; it is left in place rather than deleted so the reasoning
stays visible.

That hold rested on two arguments. Both are now discharged, but not equally.

**Argument 1 — deadline pressure — is gone.** [[TASK-0350]] and [[TASK-0351]] were
the unstarted submission work it was protecting; both are Done, [[TASK-0353]] with
them. V3 is built and out for adversarial review, and the team has agreed the
first upload waits for a meeting rather than for more work. Genuine slack, not
manufactured slack.

**Argument 2 — "wait for evidence about what to index" — was only ever about
Part A**, and it applies less than it did. Part B never depended on it: its
evidence ([[TASK-0347]]/[[TASK-0350]]/[[TASK-0351]] filed with no registry rows,
a task claimed and running while its file sat in `TODO/`) was already complete
when this was filed. **Part B should start now regardless.**

For Part A there is now more evidence than the four incidents originally listed,
and it points somewhere slightly different from what this task assumed:

- The glyph-coverage and citation checks added to `submission_build_latex.py` on
  2026-09-09 each found a real defect **within seconds of existing** — a
  tofu-rendered `≈`, and three references listed but never cited — in a document
  three people had already read closely.
- The same day, a first reading of that PDF produced a *wrong* conclusion
  (`10¹⁴` "corrupted"), corrected only by checking the renderer rather than
  trusting the extraction.

**What that suggests for the design, offered as input rather than as a
requirement:** a check that fails loudly at the moment of building beat both a
prose rule and three careful human readings. Part A's index is passive by
construction — it helps only someone who chooses to consult it, which is
[[TASK-0321]]'s measured 9%. **If there is a way to make part of the decision
index assert itself at a natural moment — as a check something already runs —
that is likely worth more than making the index more complete.** The Toolsmith is
better placed than this thread to judge whether that is feasible.

**Unchanged, and still the point of the task**: an index can be checked for
staleness, a search cannot be checked for completeness; record the pointer, never
restate the reason; ship with a test that fails on a seeded gap; never summarise
or rank; read-only.

**One honest caveat on the evidence.** The standing "check the register before you
assume" rule is one day old and has not had time to be tested. Nothing here shows
it failing — only that *checks* have succeeded quickly. Do not read this addendum
as evidence the rule does not work.

## Done — 2026-09-09, Toolsmith

### Part B — shipped: `.ai/tools/task_reconcile.py` + `test_task_reconcile.py`

One command, read-only, reuses `claim.py`'s own lock-reading directly
(`_claim.read_lock`, `_claim.is_task_id`, `_claim._parse_row`,
`_claim.STATE_TO_STATUS`) rather than a second scanner — with one deliberate
exception: `disk_task_ids()` was **not** reused for the disk scan. Read it
first, and it silently collapses a task id that has files in two folders to
whichever folder it iterates last — exactly the kind of duplicate-file drift
this tool exists to surface, so reusing it would have hidden a category of
finding. Wrote `scan_disk_files()` instead, which keeps every match, and it
paid off immediately (see below).

Eleven finding kinds — every disagreement the task's own Part B outcome bullet
named, plus three it didn't ask for but the same reasoning implies
(`duplicate_task_file`, `duplicate_registry_row` — the same "don't trust one
source silently" logic as the rest of the check; `malformed_registry_row`,
added after the first real run, see the dated addendum below). 19 tests, all
pure-function (synthetic locks/disk/registry dicts passed to `reconcile()`
directly, no filesystem fixtures) so they don't depend on this repo's own
real, moving drift state. **Acceptance bar met directly, in the task's own
words**: `test_removing_the_registry_row_flips_a_clean_case_to_red` starts
from a verified-clean synthetic state, removes the registry row, and asserts
the check goes from `[]` to non-empty.

**Real run against the live repo, right now (first pass, before the addendum
below added the malformed-row check): 120 disagreements.** Far larger than
the 3-task incident that motivated filing this task —

- **108 `file_no_registry_row`** — DONE task files with **no COMMON.md row
  at all**, roughly `TASK-0095` through `TASK-0353`. Checked against
  `COMMON.md`'s own stated rule ("Whoever creates or moves a `TASK-XXXX`
  file must update this registry in the same edit — it must not silently
  drift out of sync") before reporting this as drift rather than an
  exemption — no exemption is stated anywhere in "Current Rules". **The
  registry has not tracked most task activity for a long stretch of this
  project's history, not just the three tasks that prompted this filing.**
  This is the single most important finding this task produced: Part
  B's own design argument ("an index can be checked for staleness")
  predicted exactly this — a passive registry nobody is checking degrades
  silently and nothing before this tool would have said so in one number.
- **1 real, concrete row-level bug**: `TASK-0316`'s registry row has Path
  `.ai/tasks/TODO/TASK-0316-*.md` — a literal, un-expanded `*` wildcard, not
  a real filename — while the actual file has been in `DONE/` with Status
  `Done` for some time. Both `registry_status_mismatch` and
  `registry_path_mismatch` fire on it.
- 2 dangling claims already known from earlier sessions (`TASK-0258` no
  file at all; `TASK-0259` sitting in `DONE/` while still locked).
- 5 `status_folder_mismatch` — four straightforward (a file's own `- Status:`
  line still says `TODO` while it sits in `DONE/`), one genuinely
  interesting rather than a bug: `TASK-0295`'s Status line reads "Diagnosis
  DONE... Remediation still open" while it sits in `IN_PROGRESS/` — the
  word-boundary check correctly does NOT silently pass this (the folder's
  implied word "In Progress" isn't in that string) without asserting it's
  wrong either; a human call, correctly surfaced rather than resolved by the
  tool.

**Design choice worth stating plainly**: the Status-line/registry-status
checks use case-insensitive whole-word *containment*, not equality. Real
`- Status:` lines carry legitimate trailing detail ("Done (2026-07-24) — H2
half: FAIL, see Done section") — equality would have flooded this report
with normal stylistic variation instead of the real drift above. Verified
this choice against the actual repo's own Status-line vocabulary
(`grep`-sampled ~30 distinct real values) before committing to it, not
assumed.

**Not repaired — this task is read-only by its own explicit constraint.**
The 108-row backlog is reported, not backfilled; whether it's worth
backfilling at all, now that the deadline pressure that would have made
"nobody can see this work happened" costly has eased, is a scope call for
the owner, not this tool.

### Part A — scoped down, not built as specified; reasoning + a filed follow-up

Investigated rather than built. The task's own "Why this is an index and not
a search tool" argument — an incomplete, confidently-presented index is
*worse* than no index — turns out to apply to Part A's own proposed index,
not just to a search tool. [[TASK-0322]]'s named precedent
(`.claude/hypotheses/INDEX.md`) works because hypotheses are already
structurally tagged (`HYP-Pxx`/`HYP-Sxx` ids in a canonical register); a
"decision" has no equivalent structural tag anywhere in this repo, so a real
index would mean either a large, unverifiable-as-complete retroactive
tagging pass, or an index that's mechanically easy but exactly as
incomplete as the search tool this task was scoped to avoid building. The
task's own addendum (2026-09-09, same day) points at the more defensible
answer directly — build-time assertions over a passive index, given the
9% citation rate [[TASK-0321]] already measured for a passive artifact.

Filed **[[TASK-0354]]** with that reframing and two concrete, tractable
starting candidates (a `targets.yaml` genotype/apo-verdict assertion; a
citation hook for the chiral-walk precedent), rather than either building
Part A as literally specified or silently dropping it. Low priority, no
timing hold, unclaimed — this thread's judgement call per the task's own
invitation ("The Toolsmith is better placed than this thread to judge
whether that is feasible"), not a decision to implement it now.

### Addendum, same session — a second, sharper finding: 26 rows are invisible to every tool that reads them, not just missing

While adding `TASK-0352`'s own registry row (below), it turned out to already
have one — but with **10 columns against the header's 9**. Checked why:
`claim.py move`'s registry-sync step had silently no-op'd on it (the row
never updated to `Status: Done`) because `_parse_row` requires *exactly* 9
columns and returns `None` otherwise. Checked how many other rows share this:
**26**, column counts ranging 10-15 (almost always an unescaped literal `|`
inside a cell's free text breaking the naive `split("|")`).

This matters more than a formatting nit: `_parse_row` is shared by
`claim.py`'s own `move`/`resolve` registry-sync, its `sync` command's
dangling-row warnings, and this tool's `scan_registry_rows()` — **every one
of them silently treats a malformed row exactly like a genuinely absent
one**, with no warning anywhere that the difference exists. Some fraction of
the 108 `file_no_registry_row` findings above are therefore not "nobody
added a row" but "a row was added and is unparseable" — a different, cheaper
fix (repair the row's column count) than the first framing implied (write a
new row from scratch).

Added an eleventh finding kind, `malformed_registry_row`, sourced from
`scan_malformed_registry_rows()` (matches `claim.py`'s own `TABLE_ROW_RE`
line-open pattern, then checks the column count independently of
`_parse_row` so a malformed row is reported rather than silently dropped).
Listed first in the report — it explains a subset of the findings that
follow it. 3 new tests, including a filesystem-backed one
(`test_scan_malformed_registry_rows_detects_extra_column`) since this
specific check's whole point is line-shape detection, which a purely
synthetic dict can't exercise the same way.

**Fixed `TASK-0352`'s own row to 9 columns as part of this same edit**
(folding its two extra columns' content — a date and a hand-written note —
into the row's existing cells, matching the 9-column shape every other
correctly-formed row in the table already uses) rather than leaving the
tool's own filing as one more instance of the exact defect it just found.
The other 25 malformed rows are reported, not touched — same read-only
boundary as the rest of this task; repairing 25 rows' formatting is real,
judgement-bearing content work (deciding where each row's overflow content
belongs), not a mechanical fix this task's own scope covers.

**Corrected total: 147 disagreements** on the run that added this check
(120 from the first pass + 26 newly-visible `malformed_registry_row` + 1
`claimed_no_registry_row` for this task's own then-still-TODO claim, which
resolved itself once the row above was fixed and the task moved to DONE).
Final state, after this task's own three rows (`TASK-0352`/`0354`/`0355`)
were added or corrected: **143**.

### Registry rows for all three tasks added or corrected in the same commit

Deliberately, given what Part B's own first real run just found: `TASK-0352`
(corrected from a malformed 10-column row to 9), `TASK-0354`, and `TASK-0355`
all get clean, 9-column `COMMON.md` rows in this same commit — not adding to
the backlog this task exists to report.

### Correction, 2026-09-09 (Toolsmith, while working [[TASK-0354]]) — Part A's own table cites the wrong task id

Part A's "Where the four recent assumption failures actually had their
answers" table names `[[TASK-0130]]` for "the chiral walk was the only
interference test." Wrong task: TASK-0130 is `time_averaged_ctqw_
converged` (the closed-form convergence fix) -- it contains no mention of
chirality or interference at all (checked directly, grepped the file).
The chiral-walk observable is **[[TASK-0140]]** (`chiral.py`, "Chiral
(broken-time-reversal) circulation observable"); TASK-0130 is cited
*inside* `chiral.py`'s own docstring as reused math (its degenerate-
eigenvalue-grouping discipline, generalized from a diagonal quantity to
an off-diagonal one) -- almost certainly the source of the mix-up, not a
typo with no explanation. Not corrected in the table itself (this task is
Done; the table's prose stays as originally written per this project's
no-silent-rewrite convention) -- flagged here so a future reader of Part
A's table does not chase the wrong task file. [[TASK-0354]]'s own
candidate-2 audit (propagators.py docstring pointer to [[TASK-0350]], the
decisive result this whole citation chain was ultimately about) used the
corrected id.
