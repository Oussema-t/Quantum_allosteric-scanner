# Phase-2 PoC Sprint Plan — 3–4 months

**Team AuraQu · Cleveland Clinic Global Quantum + AI Challenge 2026**

> Written for [[TASK-0183]], to be lifted directly into the Phase-1
> proposal's Feasibility section (`documentation/PHASE1_SUBMISSION_DRAFT.md`
> §3/§6). Every runtime, cost, and capability claim below is traced to a
> measured number in the register or a cited external spec — no invented
> estimates, per this task's own Constraint.
>
> **Holding assumption, stated so it is cheap to re-check, not silently
> inherited** ([[Q-0002]]): this plan is sized against Feasibility = 20% of
> the Phase-1 score, per [[TASK-0184]]'s own 25/25/20/15/5/10 weighting.
> Those weights, and the "Phase 1 is scored as ideation" premise this whole
> plan's own shape depends on (a plan that *describes* rather than
> *demonstrates*), do not appear in `documentation/Cleveland-Clinic-
> Challenge-Statement-vF-1.md` — the only challenge document in this repo.
> The source document is requested in [[TASK-0221]]. If Phase 1 turns out
> to be scored as implementation rather than ideation, this plan's own
> shape, not just its numbers, needs revisiting.

## What this sprint builds, and what it does not

**We are not proposing to run a quantum algorithm on a protein in this
sprint.** [[TASK-0217]]'s closing synthesis found nine identified
quantum-advantage routes, all closed by measurement — including the two
this plan's own earlier draft (2026-07-29) was built around: side-chain
rotamer packing is NP-hard in general but trivial at pocket scale
(treewidth 2-5, exact solve in 0.001-0.159 s, [[TASK-0204]]), and coupled
backbone+rotamer search is not hard either on the one target where the
objective is valid and succeeds (13/65 restarts, [[TASK-0213]]). A sprint
built around either would commit this proposal to solving, with a QUBO,
a problem this same team's own register already solved in milliseconds.

**What we build instead — the certifying instrument [[TASK-0184]] §3
already commits to**, matching the narrative decision (A′) has already
made: (a) a certifying cryptic-pocket benchmark, scaled past this
register's own 13-14 hand-curated targets; (b) an apo-only screening
criterion for the hard/easy regime — the one genuinely open question this
register has (KRAS_G12C 20% easy, PTP1B 0% hard, and neither TEM-1 pair
easier, [[TASK-0216]] leg B); (c) the apo-vs-stripped-holo delta against
published external-benchmark numbers, a quantity we believe has not been
reported. **If (b) finds a real, apo-detectable hard regime with more than
today's n=1, that becomes the quantum-candidate route for a later phase.
Finding the route is this sprint's job, not building a solver for one that
does not yet exist.**

## Milestones — month boundaries, falsifiable exit criteria

### Month 1 — Scale the certifying benchmark

Productize [[TASK-0209]]'s already-built, already-validated pipeline (the
blind VALID rule: apo pocket closed → holo pocket open, ligand-stripped,
fpocket-scored; the endogenous-ligand audit that already found BCR_ABL1's
`MYR` and GLUCOKINASE's `MRK`; the holo-native positive control) and run
it at scale against a candidate pool larger than this register's own 13-14
hand-curated targets — sourced from published cryptic/allosteric-pocket
benchmark sets (ASBench, CASBench) and fresh RCSB apo/holo pairs, not the
register's own already-exhausted internal pool ([[TASK-0164]]: 0 of 6
remaining draft configs resolvable — stated honestly, this sprint's
growth comes from outside that pool, not inside it).

**Named sub-deliverable: c-Myc.** In the minimum submission set, scored on
consensus + docking viability rather than a held-out label — a genuinely
different kind of deliverable from the VALID-rule targets, given its own
explicit milestone here rather than folded silently into "the mandatory
three."

**Exit criterion (falsifiable):** report the VALID fraction on the new
pool with a 95% CI. This register's own existing measurement is 2 of 7
(28.6%, [[TASK-0209]]). If the new pool's rate is not credibly different,
that is itself the reportable finding — a benchmark-wide validity ceiling,
not an artifact of this register's own target selection. Either outcome
ships.

**Resource:** classical only — `numpy`/`scipy`/vendored `fpocket`, no
quantum hardware. Per-target cost matches this register's own already-run
pipeline (label/pocket scoring: seconds to low minutes per target, per
runtimes recorded throughout `RESULTS.md`).

### Month 2 — The apo-vs-stripped-holo delta

Run the effective-rank-reduced observable family (~3 independent axes —
proximity, directed transport, ensemble/mode structure, [[TASK-0199]],
refined by [[TASK-0207]]; testing 28 nominal observables here would be
multiplicity abuse for no information gain, per that task's own finding)
on **both** apo and ligand-stripped holo, for every valid instance from
Month 1 plus this register's own existing valid set. Compare against
published propensity-based numbers — Amor et al. 2016 (89.8%, ASBench),
Wu et al. 2022 (98.1%, CASBench) — which evaluate ligand-removed **holo**
conformations, not apo. To our knowledge this delta has not been reported.

**Exit criterion (falsifiable):** report the apo-vs-stripped-holo delta
with a CI, per observable axis. Pre-register: is it statistically
distinguishable from zero? A null result (apo and stripped-holo carry
statistically indistinguishable signal under these observables) would
itself contradict "cryptic pockets are absent from apo by definition" at
the *observable* level — reportable either way, not just descriptive.

**Resource:** classical only. Requires ASBench/CASBench access — **stated
as an open item, not assumed**: licensing/availability has not been
checked as of this writing.

### Month 3 — The screening criterion

Construct apo-only-computable candidate features at each pocket window —
ANM soft-mode cumulative overlap (`superpose.py`'s own machinery, already
built for [[TASK-0139]]/[[TASK-0150]]), local interaction-graph treewidth
(`task0204_packing_hardness.py`'s own machinery), side-chain rotamer
degrees of freedom, B-factor/flexibility — and correlate against known
search-difficulty outcomes. **Honest power statement, not hidden**:
today's known-answer set is n=4 (KRAS_G12C 20% easy; PTP1B, TEM1_BLA_CBT,
TEM1_BLA_FTA all 0/20-65, [[TASK-0213]]/[[TASK-0216]] leg B) — genuinely
underpowered for a correlation claim. Month 1's expanded valid-instance
pool is what grows n: every new VALID target gets [[TASK-0213]]'s own
coupled-search solver run against it this month, at its own real,
calibrated cost (2-10 s/`SideChainRepack` call, 65 restarts × 25
iterations ≈ 1 hour/target at the budget [[TASK-0213]] measured).

**Exit criterion (falsifiable):** pre-register a bar before looking (a
candidate feature must beat a trivial baseline — pocket size or N alone —
at a stated threshold). Report pass/fail honestly at whatever n Month 1
actually delivers; if n stays too small to test at all, that is reported
as the finding, not silently skipped.

**Resource:** the sprint's one real compute cost. Budget: ~1 hour/target
× (Month-1 valid-instance count), single-machine, no quantum hardware.

### Month 3–4 — Packaging and adversarial review

Package the certifying benchmark, the delta measurement, and the
screening-criterion result (whatever it is) as a reusable, documented,
open artifact — code release plus a written specification, matching
[[TASK-0169]]'s own "constructive half" framing (the benchmark audit is a
specification for a working instrument, not just a critique). Final
adversarial read against all six Phase-1 criteria, `PANEL_REVIEW_*.md`'s
own established convention, specifically probing whether the write-up
overstates.

## Resource requirements

**Compute.** This register's own ~200-task program ran single-machine
throughout; nothing in this plan changes that scale. Named real numbers,
not estimates: [[TASK-0130]]'s 12.3-hour brute-force integration is this
register's own measured *upper bound* (a validation run, not typical);
most label/scoring pipelines run in single-digit minutes per target
(recorded throughout `RESULTS.md`); [[TASK-0213]]'s coupled-search solver
is ~1 hour/target at its own calibrated budget (Month 3's real cost,
above). `LONG_JOB_CONVENTION.md` exists because a job was lost to session
teardown once — the lesson (OS-detached, sequential not parallel) is
already written down and applies here unchanged.

**Quantum hardware.** [[TASK-0182]]'s own measured verdict:
`FAULT_TOLERANT_ONLY` at both full resolution (169-704 qubits, 3.3M-124.9M
two-qubit gates — the 704-qubit figure is CARDIAC_MYOSIN's own N under
this register's own substituted 8QYP→8QYR pair, not Table 1's mandated
5TBY→6C1H; [[TASK-0222]] will report the mandated pair's own numbers
separately) and NISQ-plausible coarse-graining (538-1486 two-qubit gates,
depth 1010-2565 transpiled against `FakeSherbrooke`'s real calibration
snapshot; estimated fidelity 0.015 against a `(1-p)^n_2q ≥ 0.5` usability
bar). [[TASK-0172]]'s follow-up (Schur-complement reduction beats the
Louvain baseline decisively on 1 of 3 mandatory targets, loses on another)
improves the coarse-graining *method* but does not change this verdict's
order of magnitude. **No quantum hardware execution is planned or
promised in this sprint** — the fidelity gap is orders of magnitude, not
a scheduling problem.

**Named platforms: Amazon Braket and Classiq**, both provided at no cost
by the challenge itself (§Constraint 4) and unused so far — [[TASK-0182]]
substituted a local `FakeSherbrooke` snapshot and a hand-built IQM
coupling map for Braket (blocked on credentials) and never evaluated
Classiq. Account access is requested in [[TASK-0221]]; this plan targets
both concretely once available rather than staying silent on which
platform, since a plan naming the challenge's own supplied infrastructure
is a stronger feasibility claim than one that does not, independent of
whether the fidelity verdict above changes. If accounts do not arrive in
time, Month 3-4's own packaging step reports the same simulator-only
evidence already validated, with the platform gap stated plainly rather
than assumed away.

**Data.** RCSB (live fetch, this register's own established path) plus
external published benchmark sets (ASBench, CASBench — access/licensing
unchecked, stated open item, above). This register's own internal
candidate pool is confirmed exhausted ([[TASK-0164]]): Month 1's growth
comes from outside it.

## Risk register

| Risk | Already observed as | Mitigation |
|---|---|---|
| Long-job loss to session teardown | Real incident, `LONG_JOB_CONVENTION.md` | OS-detached, sequential long jobs |
| Verdict-flipping knobs (cutoff, seed convention) | [[TASK-0113]]'s cutoff-sensitivity finding | KNOB-vs-GAUGE classification (`INVARIANCE_PROTOCOL.md`) before trusting any single-point verdict |
| Null miscalibration | 3-generation null-construction history, [[TASK-0158]]→[[TASK-0190]]→[[TASK-0201]] | Validate a new null's own geometric support against real target geometry before trusting any p-value from it |
| Label instability | [[TASK-0114]]/[[TASK-0177]]'s consensus-label work | Score against consensus/core labels; report incumbent-vs-consensus disagreement explicitly |
| Benchmark non-discriminability | [[TASK-0169]] | This is the risk Month 1's own deliverable directly addresses, not merely hedges against |
| Construct-validity defects (silent fallback, array-correspondence bugs) | [[TASK-0217]]'s own family, this session | Apply its own retrospective-test discipline to any new pipeline component: can the check rediscover a known defect of its class before being trusted on new code? |

## Team and roles

Not aspirational — the split that already produced this register's own
~200 tasks, including the construct-validity sweep that found and fixed
the defects in the risk table above: an Architect/Planner role
(coordination, scope decisions, cross-task synthesis — the role that
owns this document and [[TASK-0184]]), an Implementer role (bounded
execution, local validation, retrospective tests before trusting a new
check), and a Reviewer role (adversarial audit — the thread that found
[[TASK-0204]]'s D1/D2/D3 and set the construct-validity sweep in motion in
the first place). Physics/science judgment calls (e.g. Month 1's VALID
rule extensions, Month 3's feature construction) sit with whoever holds
Implementer or Architect/Planner on that task; final scope and narrative
decisions — like this document's own — sit with Bartosz, per this
register's own standing convention for exactly that class of call.

## Explicit exclusions — the strongest available feasibility signal

- **No MD**, in any form — challenge's own §Constraint 3.
- **No further observable proliferation.** Effective rank is ~3
  ([[TASK-0199]]); adding scalar functions of the same static graph adds
  cost, not information, per [[TASK-0161]]'s own multiplicity budget.
- **No deep-ML on ENM data.** PCA/autoencoder subspace overlap with ANM
  soft modes measures 0.9999-1.0000 — provably circular ([[TASK-0150]]).
- **No quantum hardware execution promised.** [[TASK-0182]]'s own
  `FAULT_TOLERANT_ONLY` verdict stands; Braket access is an open item,
  not a milestone dependency.
- **No accuracy-target commitment.** [[TASK-0169]]'s own benchmark audit
  found the standard targets may not be able to certify one at all.
  **Committed instead: a detection-limit (LOD) target.** [[TASK-0167.002]]'s
  own established statistic (currently: no target reaches 80% power up to
  ~4× background conductance) is the one this team can actually guarantee
  movement on — this sprint commits to measurably reducing the required
  planted-coupling strength for 80% power on at least one target, not to
  a headline accuracy number the register's own audit says may be
  uncertifiable.
- **No promotion of unvalidated candidate targets into the main
  register.** [[TASK-0216]]'s own established convention — new/candidate
  targets stay in their own separate config file until independently
  curated and mechanism-validated, exactly as [[TASK-0215]]'s 6 pairs
  already do.

## Self-audit (Planned Validation, run before this document ships)

- Every milestone above has a stated exit criterion that could fail
  (Month 1: the VALID rate could match the existing 28.6%, a null result;
  Month 2: the delta could be indistinguishable from zero; Month 3: no
  feature could beat the trivial baseline, or n could stay too small to
  test at all). None is an "investigate X" milestone.
- Every resource number above is cited to a specific task
  ([[TASK-0130]], [[TASK-0182]], [[TASK-0172]], [[TASK-0213]],
  [[TASK-0164]]) rather than estimated.
- Adversarial read: would a reviewer call this optimistic? The honest
  answer is no in the direction that matters — the plan explicitly
  refuses to promise a quantum-hardware result, an accuracy number, or a
  scope this register has already shown does not work, and every
  milestone's stated failure mode is a real, reportable outcome, not a
  face-saving fallback.
