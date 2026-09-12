# TASK-0373 — Reframe the central null as a diagnosis of the input, not a dead end

- Status: TODO
- Owner: **Reviewer**
- Priority: **High value per word — but blocked on space**
- **Blocked on [[TASK-0369]].** The body is currently **7/6 pages and FAILING** ([[TASK-0367]] now reports this correctly). Nothing may be added until something is cut.
- Filed: 2026-09-12 by Reviewer thread (id via `claim.py reserve-next`)
- Source: external reviewer discussion, 2026-09-11/12
- Related: [[TASK-0350]], [[TASK-0358]], [[TASK-0367]], [[TASK-0369]], [[TASK-0371]], [[TASK-0372]], [[TASK-0374]]

## The idea, in the reviewer's own words

> the contact graph discards the degrees of freedom where quantum effects would
> live, so a quantum walk on it cannot find them — by construction

## Why it is worth scarce page space

The submission currently says: *a quantum walk on a residue contact graph adds
nothing over classical proximity.* That is true, well-measured, and repeatedly
replicated — and **stated alone it reads as a dead end.**

The reframe costs roughly two sentences and changes what the same evidence means:
an 8 Å Cα graph **cannot represent a π system**; to it, Phe and Ala are both "a
residue". So the coherent and decoherent limits agreeing ([[TASK-0350]],
+0.0023, p=0.92) and the finite-delay observable being flat at every delay
([[TASK-0358]], 0/11) are **what you would predict if the input had no quantum
content to begin with**.

It also gives Phase 2 a target, which is the gap [[TASK-0371]] records.

## What it must say, and must not

- **It is a hypothesis about why our null is a null.** Not a result. **We have not
  measured electronic coupling, and the sentence must not imply we have.**
- It does not soften any negative. Every number stands exactly as reported —
  this is an explanation of them, offered after they were published, not a hedge
  attached in advance.
- It must not claim the enrichment finding. [[TASK-0372]] is an ungated
  observation with a confound this register has already been burned by
  (40/40 ASBench structures carry a ligand at the scored site, and aromatics
  dominate ligand binding).

## Suggested shape

One sentence stating the limitation of the representation; one stating what
follows for Phase 2. Land it beside the existing *"a remaining quantum route must
supply something the static graph does not have"* sentence, which already gestures
at exactly this and currently names only many-body objects and dynamics — the
representation itself is the third and cheapest answer.

## Constraints

- **Length is the binding constraint.** Two sentences in, two or more out. Cut
  before writing.
- No claim of quantum advantage, under any framing.
- Update `SUBMISSION_VERSION_LEDGER.md` per [[TASK-0353]]'s format, including what
  must not regress: *this is a diagnosis, not a result.*
