# TASK-0326 — Classify every task against the hypothesis register, draft the missing hypotheses

- Status: In Progress
- Owner: Explorer (classification pass) → Architect/Planner (reviews NO-HYP
  drafts before they become register content, same review gate [[TASK-0323]]
  used) → Implementer (applies the reviewed drafts)
- Priority: High
- Filed: 2026-09-03 by Architect/Planner, at the repo owner's direct request
- Related: [[TASK-0321]] (the original write-mostly finding), [[TASK-0322]]
  (checker/index), [[TASK-0323]]/[[TASK-0324]] (the narrower precedent this
  generalizes), [[TASK-0307]] (same shape in the submission drafts)

## Why this exists

Discussing [[TASK-0321]]'s numbers, the repo owner asked directly: of ~344
tasks and only ~39 registered hypotheses (21 `HYP-P*`/`HYP-S*` +
18 rows in `reference_register.md`'s own scheme) cited by roughly 50-60 tasks
total, what were the *other* ~85% of tasks actually doing? [[TASK-0323]]
already answered this for the narrow case of matching a task to one of the 14
*originally-unjudged* hypotheses. This task generalizes that to the whole
corpus and adds the piece [[TASK-0323]] didn't attempt: **a task can test a
real, genuine, decided scientific claim that was never named as a hypothesis
at all, before or after the fact.** Those claims currently exist only as prose
inside individual task files — this task surfaces them as hypotheses in their
own right, not just links to existing ones.

**Do not assume most tasks are missing hypotheses.** A large fraction of the
344 are pure engineering/process work (bug fixes, path sweeps, claim/lock
cleanup, doc-sync) with no scientific claim to name. Overclaiming the
un-hypothesized-science bucket would just be a second write-mostly register.

## Intent Contract

- Outcome: a durable, tracked ledger — one row per task file — classifying
  each into exactly one of:
  - **`HYP-<id>`** — this task tested/decided a claim matching an existing
    hypothesis (either scheme). Cite the specific id(s); a task may map to
    more than one.
  - **`NO-HYP`** — this task tested a genuine, specific scientific claim or
    mechanism, and no existing hypothesis (either scheme) captures it. Each
    `NO-HYP` task gets a **proposed draft hypothesis stub** (claim, in the
    register's own existing style; dated status already filled in, since the
    deciding task already exists; citation to the deciding task(s)) —
    proposed, not silently added to the live register.
  - **`ENG`** — infrastructure/process/tooling work; no scientific claim to
    classify. No draft owed.
  - **`UNCLASSIFIED`** — genuinely ambiguous after a real read; needs a human
    (Architect or the repo owner) judgment call. Keep this bucket honest and
    small — it is not a place to dump anything effortful.
- Why required, not assumed: the repo owner's own framing — hypotheses
  "written into the task itself, but never named 'this is a hypothesis'" are
  currently invisible to the register, the checker, and anyone reading the
  register cold. This is the mechanism that finds them.
- In Scope: all 344 task files (`.ai/tasks/{TODO,IN_PROGRESS,DONE}/*.md`).
  Start with a **pilot of 30-40 tasks** (a mix of eras and apparent kinds —
  don't cherry-pick only-obvious cases) to validate the four-way scheme and
  the ledger format before committing to the full sweep; report the pilot's
  own bucket distribution before continuing, so the Architect can sanity-check
  the split is not systematically miscalibrated (e.g. `UNCLASSIFIED` too
  large, or `ENG` quietly absorbing real science).
- Out Of Scope: writing `NO-HYP` drafts directly into
  `.claude/hypotheses/*.md` — propose them in the ledger (or a staging file),
  reviewed before landing, matching [[TASK-0323]]'s own precedent of not
  self-authorizing new register content. Re-litigating any `HYP-<id>`
  classification already recorded by [[TASK-0323]]/[[TASK-0324]] for the
  original 14 — trust that work, don't redo it.
- Constraints And Invariants:
  - A `NO-HYP` draft needs the same evidentiary bar the register already
    holds itself to — cite the specific deciding task and its actual result,
    not a paraphrase from memory.
  - Where multiple tasks bear on the same un-named claim (a family, not one
    task), propose ONE hypothesis citing all of them — don't fragment one
    claim into several near-duplicate drafts.
  - The ledger itself must be easy to regenerate/audit later — a flat table
    (task id | classification | evidence/one-line reasoning | draft ref if
    NO-HYP) is sufficient; don't over-engineer the format before the pilot
    proves it out.
- Planned Validation: after the pilot, spot-check 5 classifications (mixed
  across all 4 buckets) against the actual task file content before trusting
  the scheme at full scale.

## TODO

- [x] Decide and record the ledger's location (suggest under
      `.claude/hypotheses/`, since it's fundamentally register tooling, but
      an Architect call — don't block the pilot on this, a scratch location
      is fine until the format is proven). → `.claude/hypotheses/
      TASK_CLASSIFICATION_LEDGER.md`, per the task's own suggestion.
- [x] Pilot: 30-40 tasks, mixed eras/kinds, all four buckets populated or
      explicitly absent-and-why. Report the distribution. → 39 tasks,
      stratified sample; ENG 27 (69%), HYP 6 (15%), NO-HYP 6/5-groups
      (15%), UNCLASSIFIED 0. Full ledger + reasoning in the file above.
- [ ] Full sweep: remaining ~300-310 tasks. **Not started — gated on
      Architect sign-off of the pilot, per this task's own Planned
      Validation requirement ("report the pilot's own bucket distribution
      before continuing, so the Architect can sanity-check the split").**
- [ ] Compile `NO-HYP` drafts, grouped by claim (not one-per-task where
      several tasks share a claim). **5 pilot drafts written** (see ledger)
      — not "compiled" in the sense of final/ready-to-land, since the full
      sweep may add more to the same claim families.
- [ ] Hand drafts to Architect/Planner for review before any land in the live
      register. **This Progress note + the ledger file is that handoff for
      the pilot's 5 drafts** — full-sweep drafts still pending.
- [ ] Once approved, an Implementer applies them (new `## HYP-` entries or
      new `reference_register.md`-style rows, whichever scheme fits each
      claim — some `NO-HYP` claims may be methodology/statistics findings
      that fit neither existing file cleanly; flag rather than force a fit).
      **Not started — depends on Architect approval above.**
- [ ] Re-run [[TASK-0322]]'s checker/index after any register additions land.
      **Not started — no register additions have landed yet.**

## Dependency

- [[TASK-0323]] — reuse its classification of the 14 originally-unjudged
  hypotheses rather than re-deriving it.
- [[TASK-0322]]'s checker — the tool this task's output should ultimately be
  validated against once new hypotheses land.

## Progress (2026-09-03, Implementer A) — pilot complete, awaiting sign-off

**Status: still In Progress, deliberately not moved to Done.** This
task's own Planned Validation requires the pilot's bucket distribution
to be reported and sanity-checked by the Architect before the full
~306-task sweep starts — that is a hard checkpoint, not a suggestion,
so the remaining TODO items (full sweep, drafts landing, checker re-run)
are correctly left undone pending that sign-off rather than run through.

**Pilot**: 39 tasks (stratified sample, every 9th of 345, full method
in the ledger). Distribution: `ENG` 27 (69%), `HYP-<id>` 6 (15%),
`NO-HYP` 6 tasks / 5 draft groups (15%), `UNCLASSIFIED` 0 (0%). Not
degenerate in either direction the task's own Why worried about
(`ENG` is large but not absorbing everything; `UNCLASSIFIED` is empty
because every case was specific enough to decide on a real read, not
because ambiguous cases were forced into a confident bucket — see the
reclassification below).

**7 spot-checks run (5 required + 2 more)**: full-file reads for
TASK-0057, TASK-0206 (`ENG`, confirmed), TASK-0133 (`HYP-P8`,
confirmed and materially richer than its excerpt — a real KRAS_G12C
verdict-flip finding), TASK-0278 (**reclassified `HYP-P13` → `NO-HYP`**
on the full read — its excerpt undersold it as a mere addendum to
TASK-0209; the full file is a standalone, decisive finding with its
own MYR-stripping control and a worse unflagged instance found
register-wide), TASK-0305 (`NO-HYP`, confirmed). Widened by 2 more
(TASK-0220, TASK-0188, both `ENG`, confirmed) specifically because the
TASK-0278 miss showed excerpt-only classification isn't reliable
enough to trust blind at full scale — matches [[TASK-0323]]'s own
"widen the spot-check if any of the required N don't hold up" norm,
applied here even though this task's own text only required 5.

**Full ledger, per-task reasoning, and 5 proposed `NO-HYP` draft
hypotheses** (dcc_low/transport generalization; detection-power/LOD;
external SOTA predictors vs. the residual; occupancy≠allosteric-effect
[BCR-ABL1 MYR]; ASBench enrichment-vs-retrieval): `.claude/hypotheses/
TASK_CLASSIFICATION_LEDGER.md`. No hypothesis file edited — all drafts
proposed only, per this task's own Out Of Scope and [[TASK-0323]]'s
precedent.

**Two flagged, not resolved, Architect-level calls** (both noted in
the ledger, neither decided here): (1) Draft 2 (detection-power/LOD,
TASK-0167.002) may thematically overlap `HYP-P14`'s later headroom
framing — merge, cross-reference, or keep distinct. (2) Draft 4
(TASK-0278) sharpens `HYP-P13`'s existing MYR/asciminib prose with a
decisive structural control — fold into `HYP-P13` as an update, or
land as its own id.

**Next step**: report this pilot to the repo owner/Architect for the
sign-off this task's own Planned Validation requires, then continue to
the full sweep only after that. Not self-authorized here.

## Architect sign-off (2026-09-04)

**Pilot approved — method and bucket distribution not miscalibrated.**
Reviewed directly with the repo owner (who spot-read the ledger independently
and found the classifications reasonable) and re-verified myself against
source: read HYP-P14's full claim/evidence table and HYP-P13's existing
BCR-ABL1/MYR/asciminib prose in full before ruling on drafts 2 and 4 below,
rather than taking the ledger's own framing on trust. The stratified sample,
the 7-deep spot-check (2 over the required 5), and the TASK-0278
reclassification caught by that spot-check are exactly the right shape of
diligence — proceed to the full ~306-task sweep as planned.

**Standing rule for every `NO-HYP` draft, this pilot's 5 and the full
sweep's**, per the repo owner's own instruction: **a `NO-HYP` finding
becomes its own new hypothesis only if it bears a genuinely different claim
or mechanism — not if it only sharpens, extends the evidence for, or adds a
second instance of a claim an existing hypothesis already makes.** A
sharpened finding is a dated update to the existing hypothesis's own
section, not a new id. Applying it to the two flagged calls:

- **Draft 2 (detection power / LOD, [[TASK-0167.002]]) — approved as its own
  new hypothesis.** Checked against [[HYP-P14]]'s actual claim (every signal
  collapses onto **proximity**, a representational confound) — Draft 2's
  claim is that the pipeline's own **statistical test lacks power** to
  detect a planted signal at realistic strengths, independent of whether a
  real signal exists. Different mechanism, not a sharpening of the same one
  (P14 didn't exist yet when TASK-0167.002 ran, so there is nothing prior
  for this to sharpen). Land it, and cross-reference [[HYP-P14]] explicitly
  in its own text — the thematic overlap ("the pipeline can't detect what
  it's looking for") is real and worth a reader seeing both, even though the
  underlying claims are distinct.
- **Draft 4 (occupancy ≠ allosteric effect, [[TASK-0278]]) — do NOT land as
  a new id. Fold into [[HYP-P13]] as a dated status update instead.** Read
  HYP-P13's own existing text directly (`physics.md` "It also reinterprets
  our benchmark failures as mechanism rather than defect" section): it
  already states the BCR-ABL1/MYR/asciminib claim in prose — "under HYP-P13
  it is the mechanism showing through." TASK-0278 supplies the missing
  decisive evidence for that *same, already-stated* claim (the MYR-stripping
  control proving the confound is structural, not the ligand's presence)
  plus a second instance found by the same rule (PKR_MITAPIVAT/AG946,
  `7FS3`). That is sharpening and extending existing evidence, exactly the
  case the standing rule above excludes from becoming a new id. Add it as a
  dated status/update inside HYP-P13's existing section, citing
  [[TASK-0278]] directly, not as `## HYP-P15`.
- **Drafts 1, 3, 5 — approved as new hypotheses, no existing entry covers
  any of them** (confirmed: none references `dcc_low`/transport
  generalization, external SOTA predictor comparison, or the
  enrichment-vs-retrieval reframing anywhere in either scheme).

**Authorized to continue**: full sweep, land drafts 1/2/3/5 as new hypotheses
(register-file/style per the ledger's own suggestion), fold draft 4 into
HYP-P13, apply this same new-vs-sharpening test to whatever the full sweep
turns up, then re-run [[TASK-0322]]'s checker/index once all additions land.

## Done

(not yet — pilot approved above; task remains open through the full sweep)
