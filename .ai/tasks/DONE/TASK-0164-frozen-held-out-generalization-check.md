# TASK-0164 Frozen held-out set — resolve 3 unused ASD configs, run once, never again

## Context

- ID: TASK-0164
- Title: `PANEL_REVIEW_2026-07-25.md` W5/V3 — [[TASK-0115]] correctly
  identified repeated-exposure risk and [[TASK-0081]]/[[TASK-0127]]
  mitigated it by extending the generalization set. But PTP1B/CASPASE7
  have now been scored **twice** ([[TASK-0127]], [[TASK-0151]]), and
  PTP1B is now cited as *confirmatory evidence* for `dcc_low`. A held-out
  set that has informed a hypothesis's own framing is no longer held
  out. There are 7 unresolved ASD configs in `config/targets.yaml`
  ([[TASK-0127]]'s own Done section names the ones it did not resolve
  and why) — the review's recommendation: freeze 3 of them now and do
  not look at them again until the final pre-submission check.
- Status: Done
- Owner: Architect/Planner (the freeze decision + config resolution),
  handoff to Implementer for the single frozen run.
- Claimed By: Implementer D (this thread)
- Claimed At: 2026-07-25 10:20
- Source: `PANEL_REVIEW_2026-07-25.md` §2.2/W5, §4 action item, V3.
- Priority: **P1** — the review's own estimate is 1 day; must happen
  *before* any further generalization-set analysis consumes more of the
  already-thin held-out margin.

## Intent Contract

- Outcome: resolve real, runnable configs for 3 of the 7 currently-
  unresolved ASD targets (re-check [[TASK-0127]]'s own Done section for
  exactly which 7 and why each was previously left unresolved — some
  fail for structural reasons that won't change, e.g. missing
  biological-assembly chains; pick 3 where the blocker is a genuinely
  resolvable schema/chain issue, not a missing-ligand or
  already-occupied-apo issue that would make the target unusable
  regardless). **Freeze them**: resolve the config, verify it loads
  cleanly, then do not run any scoring against these 3 targets' labels
  until every other analysis task in flight (including [[TASK-0158]]'s
  null fix) has landed — a single, final, pre-submission run.
- Why required: this is the only mechanism left in the program that can
  produce a genuinely never-seen confirmatory (or disconfirmatory) data
  point before the write-up locks in a claim.
- In Scope:
  - Re-read [[TASK-0127]]'s own Done section; pick 3 of its 7 named
    unresolved targets with a genuinely resolvable blocker.
  - Resolve chain/ligand config fields (same schema-fix pattern
    [[TASK-0127]] already used for GLUCOKINASE's `apo_chains`/
    `holo_chains`).
  - Verify the config loads and produces a non-empty pocket label — do
    **not** score against it yet.
  - Document the freeze explicitly (a dated note in `EXECUTION_PLAN.md`
    or `INVARIANCE_PROTOCOL.md`, cross-linked from [[TASK-0115]]'s own
    Rule #6) naming the 3 targets and stating they are not to be touched
    until the final pre-submission check.
- Out Of Scope:
  - Actually scoring the 3 frozen targets — that is a separate, later
    task, deliberately not filed yet (filing it now would itself be a
    form of repeated exposure to the plan).
  - The other 4 of the 7 unresolved targets, if their blocker is
    structural/permanent (state which and why, don't force a resolution
    where [[TASK-0127]] already found a real substantive reason not to).
- Constraints And Invariants: once frozen, **no scoring, no peeking at
  labels, no informal checks** — the whole value of this task is that
  these 3 targets stay genuinely unseen.
- Planned Validation: 3 configs resolved and confirmed loadable
  (structure fetch + label build succeeds, non-empty pocket), zero
  scoring runs against them, a dated freeze note in the shared docs.

## TODO

- [ ] Re-read [[TASK-0127]]'s own 7-target unresolved list; select 3
      with a genuinely resolvable (not structural) blocker.
- [ ] Resolve chain/ligand config fields per target.
- [ ] Verify config loads cleanly (fetch + label build only — no
      scoring).
- [ ] Dated freeze note in `EXECUTION_PLAN.md`, cross-linked from
      [[TASK-0115]]'s Rule #6, naming the 3 targets explicitly.

## Dependency

- [[TASK-0081]]/[[TASK-0127]] (Done) — the generalization set and its
  own list of unresolved targets, source of the 3 to pick from.
- [[TASK-0115]] (Done) — the repeated-exposure rule this task is a
  direct application of.

## Open Questions

- Which 3 of the 7 — resolve at pickup time by re-reading
  [[TASK-0127]]'s own Done section; do not guess from this task's own
  summary.

## Done

**2026-07-25, Implementer D (this thread).**

**(1) Re-read [[TASK-0127]]'s own Done section before trusting this
task's own "7 unresolved" count** — found a real, small factual
discrepancy: `config/targets.yaml` has exactly **6** `status: draft`
targets under its own `targets:` key (ATCase, HEMOGLOBIN, TAR_RECEPTOR,
GLYCOGEN_PHOSPHORYLASE, PFK, GROEL_SUBUNIT), not 7. `LDH` — the 7th
name a naive count might include — lives under a separate
`omitted_targets:` key with its own already-closed decision
(TASK-0003, 2026-07-06: dropped per the source doc's own "borderline
allostery, candidate to drop" call, apo-PDB ID ambiguity never
resolved) — not a live unresolved config in the same sense as the
other 6, correctly excluded from this task's own scope by that prior
decision.

**(2) Of the 6 real candidates, 5 are already RCSB-verified by
[[TASK-0127]] as permanently blocked** — re-confirmed by re-reading
that task's own Done section directly, not re-verified from scratch
(Out Of Scope: "don't force a resolution where TASK-0127 already found
a real substantive reason not to"):
- **ATCase**: deposited structures (6AT1/4KH1) have only 4 of the
  full 12-chain dodecamer — the regulatory subunits carrying the
  allosteric site are entirely absent from the file. Needs real
  biological-assembly expansion, not a config fix.
- **HEMOGLOBIN**: neither structure has the target ligand (BPG) at
  all; also an apo/holo chain-count mismatch.
- **TAR_RECEPTOR**: holo has zero hetero ligand records at all.
- **GLYCOGEN_PHOSPHORYLASE**: apo already occupied by a competing
  effector (G6P) at the intended site; holo's only ligand is at a
  different (catalytic) site.
- **PFK**: apo already has the intended allosteric ligand (FBP)
  bound; holo's only ligand is unrelated (PO4); apo/holo may not even
  be the same isoform (size mismatch).

None of these 5 is a "chain letter"/schema-field issue like
GLUCOKINASE's — all 5 are genuine structural/data-availability gaps in
the deposited PDB entries themselves, unfixable by any config change.

**(3) `GROEL_SUBUNIT` (1GRL/1AON) — never independently checked by any
prior task — RCSB-verified directly for the first time, live fetch**
(RCSB structure pages, not trusted from `targets.yaml`'s own "Not
RCSB-rechecked" comment):
- Apo (1GRL): real GroEL, *E. coli*, but the deposited entry has only
  7 of the biological assembly's 14 chains (A14, D7 symmetry) — the
  second heptameric ring exists only via crystallographic symmetry
  operators, not explicit chains. Resolving this needs real
  biological-assembly-expansion code (generating symmetry mates) —
  the same class of gap [[TASK-0127]] already found and deferred for
  ATCase, not a `chains`/`apo_chains` field resolution.
- Holo (1AON): real GroEL-GroES-ADP complex, 21 chains (GroEL A-N,
  GroES O-U), ADP+Mg bound to the GroEL cis ring — but this
  target's own `drug_ligand` field is honestly documented as "GroES
  (protein, not a small molecule)". `labels.py::holo_pocket_mask`'s
  entire methodology (heavy-atom contacts with an RCSB
  chemical-component-coded small molecule) does not apply to a
  7-chain protein-protein interface at all — a second, independent,
  out-of-scope methodological gap, not a config fix either.

**Headline: 0 of 6, not 3 of 6 — the premise this task was filed
under does not hold, checked directly rather than forced.** This
task's own text asked to "pick 3 where the blocker is a genuinely
resolvable schema/chain issue" — after independently verifying the
one previously-unchecked candidate and re-confirming the other 5's
already-established findings, no such candidate exists in the current
pool. This is not a partial result softened to look like progress —
it is reported as the real, decisive negative it is, per this
project's own "an honest NO is a publishable result" convention.

**Escalation, not a unilateral call**: the only remaining path to a
genuinely never-seen validation target is sourcing brand-new ASD
candidates from scratch — a materially larger undertaking than
resolving an existing config (comparable in scope to [[TASK-0081]]/
[[TASK-0127]] themselves, both of which already searched this exact
draft pool and ended below their own round-number targets rather than
backfill). Out of this task's own In Scope ("pick 3 of its 7 named
unresolved targets," not "source new ones") — flagged for the
Architect/Planner role or the orchestrating user to decide whether
that larger search is worth running before the write-up locks in any
generalizability claim, not decided here.

**Docs updated additively**: `.ai/reference/INVARIANCE_PROTOCOL.md`'s
own "Repeated-exposure risk (TASK-0115)" section (new dated addendum,
the full verification detail); `EXECUTION_PLAN.md`'s 1E.7 row context
(a short dated update paragraph, matching this table's own lighter
shape — no per-row status column to edit in place).

**Constraints honored**: no scoring was run against any of the 6
targets — verification was limited to structure fetch + chain/ligand
inspection (RCSB metadata + direct `WebFetch`), never a pocket-label
build or AUC computation, matching this task's own "no peeking at
labels" constraint even for the targets ultimately found unusable.

**Not attempted, explicitly out of scope**: sourcing brand-new ASD
candidates from scratch (see Escalation above); building
biological-assembly-expansion code for ATCase/GROEL_SUBUNIT; building
a protein-protein-interface pocket-definition methodology for
GROEL_SUBUNIT — all real, larger, separately-scoped undertakings, not
silently started here.
