# TASK-0335 — Scope-correct the standing CTQW negatives: they are stated wider than they were measured

- Status: Done
- Owner: **Implementer D** (ran [[TASK-0331]]; knows which claims it undercuts)
- Priority: High — these claims are already in outward-facing documents
- Filed: 2026-09-06 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0331]], [[TASK-0320]], [[TASK-0325]], [[TASK-0327]], [[TASK-0329]], [[HYP-P21]], [[HYP-P18]]

## The problem

Four independent findings say this register's CTQW negatives were measured in a
regime where nothing could have succeeded — and the negatives are written down
without that regime attached:

| finding | source | consequence |
|---|---|---|
| the distal subset cannot detect **proximity itself** (median ρ +0.064, p=**0.89**) | [[TASK-0331]] | the distal claim is **untested**, not refuted |
| ~30% of benchmark "allosteric" pairs are covalently adjacent | [[HYP-P21]] | no distal signal exists to find |
| 40/40 sampled ASBench structures are ligand-open | [[TASK-0329]] | pockets pre-opened in the input |
| **ASBench is PASSer's training data** | [[TASK-0327]] | the comparator was fitted on the test set |

The supported claim is narrower than the written one. Stated precisely:
*on predominantly non-distal, ligand-open, comparator-contaminated benchmark
structures, at pocket selection, the CTQW sits at or below chance.* That is
still a real negative — it is simply not "the walk does not work".

## Intent Contract

- Outcome: every standing CTQW negative carries its measured regime. Sweep at
  minimum: [[TASK-0320]], [[TASK-0325]], [[TASK-0327]], [[HYP-P18]],
  `PHASE1_SUBMISSION_V1.{md,html}`, `REVERSE_CTQW_BRIEF.html`.
- Specific corrections owed:
  - [[TASK-0325]]'s "raw cavity size is the best selector at 17.1%" — measured
    on ligand-open pockets, which favours geometric methods. Caveat or retract.
  - [[TASK-0325]] recommended PASSer as the gate worth having. Still true, but
    it now needs the ASBench-training caveat from [[TASK-0327]].
  - [[TASK-0327]]'s "actively subtracting value" — hold until [[TASK-0334]]
    reports; it is an interpretation, not a measurement.
- Constraints And Invariants:
  - **Do not weaken a negative that is correctly scoped.** [[TASK-0328]]'s
    0/110 and 1/80 compact-null survivors, and [[TASK-0327]]'s held-out 8.9%
    vs 18.4%, are properly controlled and stand as written. This task adds
    denominators; it does not soften conclusions.
  - Anything edited in `documentation/` goes through `.ai/tools/doc_parity.py`
    on both twins in the same commit.
- Planned Validation: after the sweep, a cold reader of any one corrected claim
  must be able to state the cohort it was measured on without opening a second
  file.

## Note

The scope correction makes the Phase-1 story *stronger*, not weaker: "here is
the cohort defect that makes distal allostery currently untestable, measured
three independent ways" is a contribution. An unqualified negative is not, and
is the easier thing for a reviewer to take apart.

## Done

**2026-09-06, Implementer C.** Owner note: this task's own Owner field names
Implementer D (ran [[TASK-0331]]); no active claim existed on it when picked
up (`claim.py status` showed nothing held), and the user directed picking it
up explicitly — disclosed, not silently taken, same convention this session
used for [[TASK-0327]]'s own override precedent.

### Sweep results, item by item against the task's own "sweep at minimum" list

- **[[TASK-0320]]** — needed the correction, applied. Its own "raw cavity
  size is the best selector at 17.1%" line and its "reverse-seeded CTQW does
  not select allosteric pockets" verdict are both measured on the unfiltered
  ASBench cohort — since found predominantly non-distal (~45% genuinely
  distal, [[TASK-0331]]) and scored on ligand-bound input (40/40 sampled
  structures carry a ligand, [[TASK-0329]]). Added a dated "Scope correction"
  section stating the corrected sentence for the submission, per the Note's
  own framing — **not weakened** (per this task's own Constraint): the
  measurement, numbers, and verdict all stand exactly as run.
- **[[TASK-0325]]** — needed the correction, applied. Same cohort, same two
  defects. Two lines flagged: "raw cavity size is still the best selector at
  every gate" and the task's own headline ("the gate is the entire effect").
  Added a dated "Scope correction" section with the corrected framing for
  each, plus the specific point [[TASK-0329]] itself makes (ligand-openness
  inflates the geometric arms without correcting CTQW's, so if anything this
  *understates* the gap on genuinely closed pockets, not overstates it) —
  stated explicitly rather than left for a reader to work out.
- **[[TASK-0327]]** — checked, no edit needed. Its own Done file was already
  corrected by another thread in a separate, prior commit (`9c6a1e7`,
  predates this task being picked up) with the full ASBench/CASBench-leakage
  analysis and citations; `ALGORITHM_REGISTER.md`'s PASSer entry carries the
  same correction. The one interpretation this task explicitly says to
  **hold** ("actively subtracting value" — [[TASK-0327]] line ~180) was left
  untouched, per this task's own Constraint: [[TASK-0334]] (checked —
  currently claimed/in-progress, not yet Done) is the gate on that specific
  interpretive claim, not this task.
  - The Intent Contract's second "specific correction owed" bullet
    ("[[TASK-0325]] recommended PASSer as the gate worth having... needs the
    ASBench-training caveat") **does not apply as literally stated** —
    checked directly: [[TASK-0325]]'s own text never recommends PASSer (it
    names PocketMiner as "the untested residue" and mentions PASSer once,
    as a blocker — "the literal gate is not runnable today" — not a
    recommendation). The PASSer recommendation and its leakage caveat both
    live in [[TASK-0327]]/`ALGORITHM_REGISTER.md`, already corrected as
    above. Recorded here so this bullet isn't silently dropped as
    unaddressed — it was checked and found to target a different file than
    named.
- **[[HYP-P18]]** — checked, no edit needed. Already dated 2026-09-06 by
  another thread with the corrected, held-out PASSer numbers (28.1-40.9%,
  matching [[TASK-0327]]'s own corrected figures exactly, not the stale
  leaky 40.6-55.2%) and its own explicit "caveat carried forward, not
  resolved here" disclosure. Verified by direct read, not assumed from the
  dated header alone.
- **`PHASE1_SUBMISSION_V1.md`/`.html`** — checked, no edit needed. Grepped
  both for "17.1", "cavity", "reverse-seeded", "TASK-0320", "TASK-0325",
  "pocket selection" — **zero hits**. This specific finding family (reverse-
  seeded CTQW as a pocket selector) is not currently cited in the submission
  draft at all, so there is nothing there to scope-correct for it. Per this
  task's own Constraint, `doc_parity.py` was not run — nothing was edited in
  this file, so there is no drift to introduce.
- **`REVERSE_CTQW_BRIEF.html`** — needed the correction, applied (this is
  [[TASK-0320]]'s own collaborator-facing brief and the most likely place an
  outside reader sees the unqualified claim). Added a `.note`-styled
  scope-correction box directly after the results table (matching the
  file's own existing box convention, e.g. its "honest limit of this
  operation" note), and updated two "Closed"/"Unaddressed" bullets in §6 to
  point at it. No `.md` twin exists for this file (confirmed:
  `ls documentation/ | grep -i reverse` → one file only) — `doc_parity.py`
  takes exactly two file arguments and has nothing to compare this HTML-only
  document against, so the Constraint does not apply to it.

### Adjacent finding, flagged not fixed — out of this task's own scope

The submission's own Appendix A claims ledger (`PHASE1_SUBMISSION_V1.md`)
carries several *other* CTQW negatives on ASBench cohorts likely affected by
the same non-distal/ligand-open defects (e.g. "No single observable survives
conditioning on proximity — 7 of 7 tested", "On 108 annotated structures,
nothing we have beats random at P@5") — these are a different task family
(TASK-0304/0305/0308/0310's own lineage, not [[TASK-0320]]/[[TASK-0325]]/
[[TASK-0327]]'s), outside this task's own named "sweep at minimum" list and
its "Specific corrections owed" bullets. Not touched here — flagged so
whoever next reviews the appendix table doesn't have to rediscover this
independently. A full appendix-wide audit would be its own task.

### Verification

- `grep -c "TASK-0335"` across the 3 edited files (TASK-0320, TASK-0325,
  REVERSE_CTQW_BRIEF.html) → each carries exactly one dated correction
  block, no duplicates.
- Re-read [[TASK-0329]]'s own file directly (not just TASK-0335's summary
  table) before citing its "40/40" number — confirmed at that file's own
  "What this register measured independently" section, not yet in its own
  Done section (TASK-0329 itself is still IN_PROGRESS, claimed by
  Implementer B) — the finding is real and written down regardless of that
  task's own completion status, cited as such.
- Planned Validation self-check: a cold reader of [[TASK-0320]]'s "Verdict"
  paragraph, [[TASK-0325]]'s headline, or `REVERSE_CTQW_BRIEF.html`'s
  results section can now state the cohort (unfiltered ASBench, ~45%
  distal, 100% ligand-bound) without opening a second file — each carries
  its own inline correction, not a pointer requiring one more hop.

**No script written** — pure documentation/scope-correction task, matching
[[TASK-0323]]'s own "no scripts" precedent for this shape of work.
