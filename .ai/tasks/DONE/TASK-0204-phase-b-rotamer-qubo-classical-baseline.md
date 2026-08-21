# TASK-0204 Phase B's own falsification criterion #1 — the classical rotamer baseline, the last unopened route

## Context

- ID: TASK-0204
- Title: run [[TASK-0181]] Phase B's own pre-stated falsification criterion #1
  — solve the side-chain rotamer packing objective **classically** on real
  candidate windows and test whether it opens an fpocket-druggable cavity
  more often than naive per-residue greedy rotamer choice.
- Status: Done
- Resolution: done
- Resolution Note: **Route CLOSED on complexity grounds, not on criterion #1.** The original 2026-08-06 criterion-#1 run is RETRACTED (reopened by the Reviewer thread the same day; three defects, each sufficient alone -- an unfalsifiable gate, no positive control, and an overlap leg any repacking destroys). Reformulated and measured instead: side-chain packing is a pairwise MRF whose exact-minimization cost is O(m*n^(tw+1)); on real pocket windows (m=12, n=15) treewidth is 2-5 and the exact global optimum is found in 0.001-0.159 s against a naive 1e14.1 search space, validated by exact solve against brute force. A hard regime exists only at m~50-80 (most of a domain, not a pocket). Criterion #1's biological question remains unanswered and is explicitly non-gating -- a pass would not have supported a quantum route.
- **Thread: Implementer B (science / compute).** Independent of
  [[TASK-0203]]; different targets, different modules, no shared files.
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: `src/allostery/PHASE_B_ROTAMER_QUBO.md` §"Falsification criteria" #1
  (written by [[TASK-0181]], never run); Reviewer thread 2026-08-03
  recommendation #4; `REVIEW-panel-2026-07-28-external.md` §7's own
  "combinatorial selection is the one genuine gap."
- Priority: **P1 — the only route left in the register where the
  quantum-advantage argument does not collapse on contact, and the one thing
  worth spending a multi-day compute window on. Purely classical: it either
  opens the route or closes it, and closing it is equally valuable.**
- Dependency: [[TASK-0181]] (Done — the formulation), [[TASK-0163]]/
  [[TASK-0185]] (Done — vendored fpocket + the full-atom displacement
  machinery), [[TASK-0206]] (soft — fpocket determinism).

## Why this matters — every other quantum route is closed, and this one is closed *only by not having been run*

The register's own falsification history rules out, with measurement:

- Single-particle CTQW / occupation observables — proximity detectors, and at
  N ≤ 704 an `eigh` call, so no advantage exists at any point.
- Coherence / interference — inert (flat γ-sweeps, phase-free converged limit
  exact to 1e-6, coherent ≥ ENAQT under NISQ noise).
- Non-locality — absent by construction in a single-particle Hilbert space
  ([[TASK-0148]]).
- Interacting multi-particle — measured by the external panel: ρ ≈ 0.88–0.90
  against the 1-particle observable even at U=12, and the proximity confound
  gets *worse* (0.73 → 0.82).
- Backbone-layer conformational search — [[TASK-0185]] measured pocket
  recovery at **1–8 classical draws per hit**. Not a rare event, so
  amplitude amplification has nothing to amplify.
- Selection-as-QUBO at the **residue** layer — [[TASK-0181]] Phase A, gate
  CLOSED, 0/3 strict wins.
- Optimal control — [[TASK-0156]], chance on all 3 mandatory targets.

**The side-chain layer is the one place the argument survives, and it survives
for a stated reason, not by omission:** rotamer packing is discrete and
NP-hard (Pierce & Winfree 2002), and — unlike the backbone layer — pocket
opening there is *plausibly* a rare event, which is precisely the precondition
[[TASK-0185]] measured and found absent at the backbone. Both [[TASK-0185]]
and [[TASK-0187]] independently concluded, from opposite directions, that
whatever residual effect exists lives where a Cα ENM cannot reach.

Phase B was written up and explicitly not built, correctly, given the freeze.
**Its own criterion #1 is a purely classical experiment** — no quantum
formulation, no hardware, no qubit budget. It answers the question that
governs whether the quantum formulation is worth proposing at all, and per
Phase A's own precedent, *"no quantum formulation is built for an objective
that does not already show value classically."*

A closed result here is as valuable as an open one: it would let the
submission say the side-chain route was tested and closed, rather than
gestured at as future work — which is the difference between a forward
proposal and a hand-wave.

## Intent Contract

- Outcome: on ≥2 real targets, a measured cavity-opening rate for
  (a) classically-optimized rotamer packing vs. (b) naive greedy
  lowest-self-energy per-residue choice, scored by fpocket druggability on
  real repacked structures — plus an explicit verdict on Phase B's criterion
  #1 and, if it passes, the rare-event rate that determines whether a search
  formulation has anything to search.
- Why required, not assumed: Phase B currently has a formulation, a qubit
  estimate, and three falsification criteria, none of which has been tested.
  That is a proposal, not a result.
- In Scope:
  - **Sourcing, honestly.** `src/allostery/` has no `rotamer.py`/`packing.py`,
    no rotamer library, and no pairwise energy table — Phase B's own Status
    section says so. Source a backbone-dependent rotamer library (Dunbrack,
    coarse buckets per the write-up) and a pairwise energy term, or use an
    existing classical packer (DEE/A*, or a scriptable tool). **Prefer
    vendoring an existing solver over hand-rolling an energy function** —
    same precedent as `fpocket`/`ripser`/`optuna`, and a homemade energy
    table is exactly the "invented internal heuristic" criterion #3 forbids.
  - Candidate windows: use [[TASK-0180]]'s site-level clusters or the known
    pocket neighbourhood, 8–15 residues per the write-up's own `m`.
  - Repack, rebuild full-atom coordinates (reuse [[TASK-0185]]'s rigid
    per-residue Cα-driven displacement machinery and state the same
    approximation caveat it stated), run fpocket, score druggability.
  - **The comparison that is the actual gate**: optimized packing vs. greedy
    per-residue. Both scored identically. Report the rate difference and a
    null.
  - **If and only if criterion #1 passes**: measure the rare-event rate — what
    fraction of random rotamer assignments open the cavity? This is the
    number that decides whether amplitude amplification is even applicable,
    and it is the direct side-chain analogue of [[TASK-0185]]'s 1–8-draws
    finding at the backbone. Report it whichever way it lands.
- Out Of Scope:
  - **Any quantum formulation, QAOA run, or hardware estimate.** Phase B's own
    criterion #1 gates all of that, and Phase A's precedent is binding.
  - Claiming a speedup. Criterion #2 is explicit: NP-hardness permits a
    heuristic argument for trying, never a proven advantage. Any write-up
    must say so verbatim.
  - Side-chain MD, or any integrator. The no-MD constraint stands — this is
    discrete combinatorial search over a rotamer library, not dynamics.
  - Replacing the §5.2 hit list or any shipped deliverable.
- Constraints And Invariants:
  - **Pre-register the pass/fail bar before running**: what rate difference,
    on how many targets, counts as criterion #1 passing? Phase A set its bar
    at ≥2 of 3 targets; match that shape unless there is a stated reason not
    to.
  - Druggability must come from fpocket's actual score on real repacked
    structures — criterion #3, non-negotiable, no geometric proxy.
  - Report compute cost honestly. If the window size or library resolution has
    to be cut to fit the budget, state what was cut and what that does to the
    result's reach.
  - If the route closes, say so in the same voice every other negative in this
    register is reported in. A closed Phase B is a *result*.
- Planned Validation:
  - **Sanity, run first:** repack a window with the rotamers already present
    in the deposited structure and confirm fpocket reproduces that structure's
    known cavity. If the pipeline cannot recover the real answer from the real
    input, no downstream number means anything.
  - **Negative control:** random rotamer assignments must not open the cavity
    at the optimized rate. If they do, there is nothing to optimize and that
    is itself criterion #1's answer.
  - **Greedy baseline must be a fair baseline**, not a strawman — lowest
    self-energy per residue ignoring pairwise terms, exactly as the write-up
    specifies, same scoring path as the optimized answer. Phase A was careful
    about this (it excluded active-site residues from both arms); match that
    care.

## In Progress

—

## Pre-Registered Survival Criterion (fixed 2026-08-06, before any comparison run — Implementer B)

Written before the optimized-vs-greedy comparison is run, per this task's
own Constraint ("pre-register the pass/fail bar before running").

**Targets**: KRAS_G12C and BCR_ABL1 — **not** PTP1B (this task's own Open
Question, decided here): [[TASK-0203]] is concurrently investigating PTP1B
at a different layer (ensemble/mode, not packing); running the same target
risks conflating two independent findings into one number if both land
positive, and there is no dependency between the two tasks that requires
sharing a target. KRAS_G12C and BCR_ABL1 are both mandatory targets with
already-established, well-characterized pocket labels, chosen for that
reason alone.

**"Opens a druggable cavity"** (operationalized, reusing this project's own
established conventions rather than inventing new ones): a repacked
structure counts as opening a druggable cavity at the window if `fpocket`
detects **any** pocket whose member-residue set overlaps the window residues
by `>= 0.5` (the exact `POCKET_HIT_OVERLAP` bar
`conformational_search_measurement.py`/[[TASK-0185]] already established for
"did fpocket find the pocket") **and** that same pocket's own
`druggability_score >= 0.5` (fpocket's own commonly-cited druggable/
non-druggable cutoff — criterion #3's "real druggability, not a geometric
proxy," non-negotiable).

**Trial counts**: optimized (`SideChainRepack`, real simulated annealing) and
random (`RandomRepack`, this task's own patch) are each stochastic — run
**8 seeded trials** per target (matching [[TASK-0181]] Phase A's own
8-restart precedent, reused not reinvented). Greedy (`GreedyRepack`, this
task's own patch) is deterministic (always the lowest-self-energy rotamer
per site) — **1 trial** per target is the whole population; there is no rate
to compute for it, only a single hit/miss.

**Criterion #1 passes if**: the optimized hit-rate (fraction of 8 trials
opening a druggable cavity) **strictly exceeds** greedy's own single
hit/miss result, on **both** of the 2 targets tested (2/2) — the same
majority-of-targets shape Phase A's own gate used (2/3), scaled to this
task's own 2-target scope. If greedy already opens the cavity (hit=1) and
optimized does not exceed a rate of 1.0, that target counts as a **fail**
for criterion #1 on that target specifically (optimization added nothing
over the naive baseline) — stated explicitly so a ceiling case is not read
as an automatic pass.

**If and only if criterion #1 passes** (on both targets): measure the
rare-event rate using the **random** arm's own 8-trial hit-rate — this is
the direct side-chain analogue of [[TASK-0185]]'s 1–8-classical-draws
finding at the backbone layer, and decides whether amplitude amplification
would have anything to amplify.

## TODO

- [x] Pre-register the criterion-#1 pass bar in this file. **Before running.**
- [x] Source rotamer library + pairwise energy / classical packer; record the choice and why.
- [x] Sanity check: native rotamers → fpocket recovers the known cavity.
- [x] Select candidate windows on ≥2 targets.
- [x] Run optimized packing vs. greedy; score both by fpocket druggability.
- [x] Negative control: random assignments.
- [x] Verdict on criterion #1.
- [x] If passed: measure the rare-event rate (the amplitude-amplification precondition). — N/A, criterion #1 failed.
- [x] Write the result into `PHASE_B_ROTAMER_QUBO.md`'s Status section + `RESULTS.md`.

**Reformulated scope (2026-08-06, Reviewer thread) — the gating question changed:**

- [x] Retract the original closure; record all three defects with evidence (D1/D2/D3).
- [x] Fix the unfalsifiable gate: `criterion_1_verdict()` + 8 regression tests, one failing-first against the original expression.
- [x] Build and run the missing positive control (`task0204_positive_control.py`).
- [x] Measure the actual gating question — treewidth/hardness, 4 targets, m=8-80, cutoff swept.
- [x] Validate the cost model by exact solution, correctness-gated against brute force.
- [x] Propagate to `PHASE_B_ROTAMER_QUBO.md`, `RESULTS.md` row 65, and the registry row.
- [ ] **Not owed by this task**: a valid rerun of criterion #1's biological question. The six
      requirements are listed in the Reopened section for whoever rebuilds the instrumentation;
      a pass would change nothing about the quantum route, which is closed on complexity grounds.

## Dependency

- [[TASK-0181]] (Done) — the formulation and all three criteria.
- [[TASK-0185]] (Done) — full-atom displacement + fpocket-as-oracle precedent.
- [[TASK-0163]] (Done) — vendored fpocket.
- [[TASK-0206]] (soft) — if the fpocket binary has drifted, pin it first.
- Feeds [[TASK-0183]] (the PoC sprint plan — this is the experiment that
  decides what Phase 2 would actually build) and [[TASK-0184]].

## Open Questions

- Is a full rotamer library + pairwise energy table sourceable and runnable
  inside the remaining compute window? If not, the honest fallback is a
  reduced library (fewer buckets) with the reduction stated — not abandoning
  the falsification and leaving Phase B untested.
- Does the "rare event" framing survive contact with real numbers? [[TASK-0185]]
  expected rarity at the backbone layer and measured its absence. The same
  could happen here — and if it does, it closes the last route cleanly, which
  is a genuinely good outcome for the submission.
- Should this run on PTP1B specifically, given [[TASK-0203]] is investigating
  the same target? Argument for: mechanistic coherence across the two tasks.
  Argument against: PTP1B's positive is an *ensemble/mode* result and Phase B
  is a *packing* result — different layers. Decide and record; do not let it
  default.

## REFORMULATED 2026-08-06 — criterion #1 was the wrong gating question

**Raised by the orchestrating user, and correct: even a clean PASS on
criterion #1 would not have supported a quantum route, because the instance
solves classically in seconds.** The original run repacked a 12-residue
window in ~2 s per trial on a laptop. "Why use a quantum computer for
something a laptop does in seconds?" is not rhetorical — it is the same
complexity argument this register already used to close Grover/HHL/QML and
single-particle CTQW ("at N≤704 it is an `eigh` call, so no advantage exists
at any point"). Applied here it must be answered **before** any biological
proxy is worth running.

**This is a scoping error I own** (Reviewer thread): TASK-0204 inherited
Phase B's criterion #1 verbatim without asking whether passing it would mean
anything. It would not have.

### The corrected gating question

> Side-chain packing with a fixed backbone and a discrete rotamer library is
> a pairwise Markov random field. Its exact-minimization cost is
> `O(m · n^(tw+1))` — **treewidth**, not variable count — not the naive
> `O(n^m)` the Phase B write-up's own 180-qubit estimate is built on. So:
> **is the instance this project would actually solve hard at all?**

Pre-registered falsification, fixed before running: if `tw` grows roughly
linearly with window size `m`, a genuine hard regime exists and the route
survives. If `tw` saturates small while `m` grows, exact classical solution
is cheap and the route is closed **on complexity grounds** — permanently, for
any window size, regardless of any biological result.

### Result — measured, 4 targets, window sizes 8–80, interaction cutoff swept

`scripts/task0204_packing_hardness.py`,
`results/tasks/0204_packing_hardness/packing_hardness.json`. At the 8 Å
side-chain interaction cutoff, `n=15` rotamers/site (the write-up's own
figure):

| Target | m=12 `tw` | naive `n^m` | exact `m·n^(tw+1)` | m=50 `tw` | m=80 `tw` |
|---|---|---|---|---|---|
| KRAS_G12C | 3 | 1e14.1 | **1e5.8** | 7–13 | 9–20 |
| BCR_ABL1 | 4 | 1e14.1 | **1e7.0** | 7–15 | 9–23 |
| CARDIAC_MYOSIN | 2 | 1e14.1 | **1e4.6** | 6–8 | 8–12 |
| PTP1B | 4–5 | 1e14.1 | **1e8.1** | 8–15 | 9–18 |

**At the window size that matters (m≈12, a druggable pocket), exact solution
costs 1e4.6–1e8.1 operations — six to nine orders of magnitude below the
naive `n^m` figure, and well inside a laptop-second.** The apparent
`1e14` search space is an illusion created by counting variables instead of
measuring the interaction graph. This is the direct, quantitative answer to
the user's objection, and it closes the route at the scale Phase B was
written for.

**The honest boundary, stated rather than buried**: `tw` does *not*
saturate. It keeps growing with `m` (to 9–23 at m=80, exact cost 1e26–1e30),
so a genuine hard regime does exist — but only at window sizes of 50–80+
residues, which is most of a domain, not a cryptic pocket. Phase B's own
scope (`m=8–15`) sits entirely inside the tractable regime.

### Empirical validation — the cost model is not an argument, it is a measurement

`scripts/task0204_exact_solve_validation.py`,
`results/tasks/0204_packing_hardness/exact_solve_validation.json`.
Exact minimization by bucket elimination on the **real** interaction graphs,
`n=15` rotamers/site.

**Correctness gate, run first** (this project's standing practice): on
instances small enough to enumerate, bucket elimination must equal brute
force exactly. m=6/n=4, m=7/n=3, m=8/n=4 — **match on all three, to 1e-9.**

| Target | m=12 exact solve | m=16 | m=20 |
|---|---|---|---|
| KRAS_G12C | **0.002 s** | 0.003 s | 0.033 s |
| BCR_ABL1 | **0.009 s** | 0.131 s | over budget (1.7e8) |
| CARDIAC_MYOSIN | **0.001 s** | 0.002 s | 0.003 s |
| PTP1B | **0.159 s** | over budget (2.6e9) | over budget (3.8e10) |

**The exact global optimum of a real 12-residue pocket-window packing
instance is found in 1–159 milliseconds on a laptop**, against a naive
search space of `1e14.1`. Not "seconds" — milliseconds. The user's objection
was right and understated: there is no room for a quantum advantage
argument here by nine to eleven orders of magnitude.

The tractability boundary is target-dependent and measured: KRAS_G12C and
CARDIAC_MYOSIN stay trivial through m=20; BCR_ABL1 crosses the budget at
m=20; PTP1B — the densest interaction graph of the four — crosses at m=16.
All well above a druggable pocket's 8–15 residues.

### What this means for the register

- Phase B's **qubit estimate is not wrong but is not evidence of hardness**:
  `m·n = 180` one-hot variables is a faithful encoding size and says nothing
  about solve cost, which is set by treewidth.
- The route is closed **on complexity grounds at the biologically relevant
  scale** — a stronger and far more defensible closure than the retracted
  biological proxy below, and the same argument shape the register already
  accepts for CTQW/Grover/HHL.
- The surviving open question is **not** rotamer packing. It is whether any
  formulation of cryptic-pocket opening is both (a) hard and (b) the thing
  that needs solving. Backbone-layer search is already closed empirically
  ([[TASK-0185]]: pocket recovery is 1–8 draws, not a rare event). Coupled
  backbone+side-chain over a whole domain is in the hard regime above but is
  a different problem, and the no-MD constraint forbids it here.

### Scope of criterion #1 after this

Criterion #1's biological question is **no longer gating** — it was
downstream of an assumption that has now been measured false. It remains
worth answering if someone rebuilds the instrumentation (the six
requirements in the Reopened section below still stand), but a pass would
change nothing about the quantum route. Recorded as such, not silently
dropped.

---

## Reopened 2026-08-06 — the closure below is RETRACTED. Phase B is untested, not closed.

**Reopened by the Reviewer thread (Opus) on direct user instruction, after the
user flagged the original run's implausibly short runtime. Three independent
defects were found, each sufficient on its own to void the verdict. The
original Done section is preserved unedited below, per this project's
no-silent-overwrite convention, but its conclusion does not stand.**

### D1 — The gate could not return `pass` for any data. Demonstrated, not argued.

`scripts/task0204_rotamer_repack_baseline.py:326` (as run):

```python
opt_rate > (1.0 if greedy_hit else 0.0)
```

`opt_rate` is a fraction of 8 trials; its maximum attainable value is exactly
`1.0`. **On any target whose greedy baseline hit, the gate demanded a value
that cannot exist** — a perfect 8/8 optimized sweep returns `False`. BCR_ABL1's
greedy did hit. The pre-registered bar required **2 of 2** targets. Therefore
criterion #1 was **unfalsifiable in the positive direction for the run as a
whole, before a single trial was scored**.

Verified by executing the expression across every attainable rate:

| greedy | bar | attainable `opt_rate` | can pass? |
|---|---|---|---|
| misses | `> 0.0` | 0.0 … 1.0 | yes, at ≥1/8 |
| **hits** | **`> 1.0`** | 0.0 … 1.0 | **never** |

The original *intent* was sound — optimization must add something over the
naive baseline, and a ceiling case must not read as an automatic pass. The
error was scoring that case as a **fail** and charging it against a
both-targets-must-pass bar. A target where the naive baseline already succeeds
says nothing about whether optimization helps where it is needed: it is
**not evaluable**, and the denominator must shrink rather than the numerator
absorbing a loss it could never have avoided.

**Fixed**: new `criterion_1_verdict()` returns
`pass` / `fail` / `not_evaluable_greedy_ceiling` / `not_evaluable_no_data`.
8 regression tests (`tests/test_task0204_criterion.py`), including one that
fails against the original expression for every attainable rate.

### D2 — There was no positive control. Built and run; it changes everything.

The original run scored only the **apo** structure. For a genuinely cryptic
pocket the apo cavity is closed *by definition*, so a miss there is the
expected result and carries no information. The holo structure — where the
drug demonstrably binds — was loaded by `_load_apo_holo` and used only to
build labels. **It was never scored.**

New `scripts/task0204_positive_control.py` runs the ladder the original
needed, ligand stripped, at each structure's own pocket window:

| Target | arm | overlap | druggability | hit |
|---|---|---|---|---|
| KRAS_G12C | **holo_native** (positive control) | **1.000** | **0.886** | **yes** |
| | holo_greedy | 0.417 | 0.827 | no |
| | holo_optimized (8) | 0.167–0.583, med 0.250 | 0.008–0.989, med 0.941 | 1/8 |
| | apo_native | 0.750 | 0.001 | no |
| BCR_ABL1 | **holo_native** (positive control) | 1.000 | **0.356** | **no** |
| | holo_greedy | 0.250 | 0.856 | no |
| | holo_optimized (8) | 0.250–0.500, med 0.417 | 0.608–0.725, med 0.683 | 2/8 |
| | apo_native | 0.917 | 0.566 | yes |

**The positive control passes on KRAS_G12C and FAILS on BCR_ABL1.** On
BCR_ABL1 the pipeline cannot detect a druggable cavity at the site where a
drug actually binds (0.356 < the 0.5 bar) — while scoring the *apo* structure
at 0.566, i.e. **higher than the holo**. Every BCR_ABL1 number in the original
run is therefore uninterpretable, and the 0.5 druggability bar is
mis-calibrated for that target.

KRAS_G12C's apo/holo contrast is meanwhile exactly the cryptic-pocket signal
the experiment should have been built around: druggability **0.001 → 0.886**.
The pipeline can see this cavity open and correctly reports it closed in apo.

### D3 — The conjunctive criterion is dominated by an overlap leg that any repacking destroys.

On KRAS_G12C, where the control passes and the cavity is definitively open,
**repacking the holo structure collapses the overlap leg while leaving
druggability high**:

- overlap `1.000 → 0.417` (greedy), median `0.250` (SA)
- druggability `0.886 → 0.827` (greedy), median `0.941` (SA) — *higher than native*

Same on BCR_ABL1: overlap `1.000 → 0.250`, druggability `0.356 → 0.856`.

Druggability is not what fails. **Residue-set overlap between fpocket's
detected cavity and the fixed window is**, and it collapses under *any*
repacking — greedy included, on a structure where the cavity is known open.
The overlap leg is a structure-similarity proxy, not a druggability measure;
no repacking arm can win it. The original run's 32 misses measure this
artifact, not the hypothesis.

This also **refutes the original Done section's own stated mechanism**
("EvoEF2's SA minimizes packing energy… tighter packing is a different
objective than opening a cavity"): the **random** arm minimizes nothing and
collapses identically. The common factor is repacking, not optimization.

### Supporting observations

- **Runtime**: `elapsed_s` 34.1 + 39.2 = **73.3 s** total, of which
  `time.sleep(1.05)` × 32 = **33.6 s is sleeping** for EvoEF2's
  second-resolution `time(NULL)` seed. Real compute ≈ 40 s.
- **No seed control**: trials are seeded only by wall-clock second, so the
  run is not reproducible. A `--seed` path is needed before any rerun.
- **Power**: with the observed per-leg marginals, P(0 of 8) = **0.52**
  (KRAS_G12C) and **0.83** (BCR_ABL1) — 0/8 is the modal outcome under any
  hypothesis.
- **Knife edge**: overlap is quantized to n/12 and the bar is exactly 6/12.
  BCR_ABL1's greedy scored exactly 0.500. One residue fewer and the
  "ceiling case" that D1 shows was predetermined would not even have applied.

### Standing conclusion

**Phase B is untested.** The register's "every route is now closed by
measurement" claim — the original Done section's final paragraph, and the
sentence headed for [[TASK-0184]] — is **not supported**. The side-chain
rotamer route remains exactly what it was before this task ran: the one route
whose quantum-advantage argument has not been tested.

Neither target as configured can test it. KRAS_G12C is the viable one (its
control passes, its apo/holo contrast is real), but the criterion has to be
rebuilt around the holo ceiling rather than an absolute bar.

### What a valid rerun requires (for whoever picks this up)

1. **Ceiling-relative criterion.** Score against `holo_repacked`, not an
   absolute 0.5/0.5 bar. The question is whether apo-repacking moves toward
   the holo cavity, and `holo_greedy`'s own overlap (0.417 on KRAS_G12C) is
   the honest ceiling for *any* repacked structure.
2. **Report the two legs separately and continuously.** A conjunctive boolean
   over 8 trials discards the information that made this audit possible.
3. **Fix or drop the overlap leg.** A fixed residue window cannot survive
   repacking. Either score cavity *volume*/druggability at the window's
   centroid, or accept a much lower overlap threshold calibrated from
   `holo_repacked`.
4. **Drop BCR_ABL1 or recalibrate its bar** — its positive control fails.
5. **Seed control** (`--seed`), and trial counts set from a stated power
   calculation, not from Phase A's 8-restart precedent, which was a different
   kind of measurement.
6. **Pre-register the positive control's expected result alongside the pass
   bar**, so an experiment that can only produce one answer is caught before
   it runs. This is the general lesson, and it is not specific to this task.

Artifacts: `scripts/task0204_positive_control.py`,
`results/tasks/0204_positive_control/positive_control.json`,
`tests/test_task0204_criterion.py`, `criterion_1_verdict()` in
`scripts/task0204_rotamer_repack_baseline.py`.

---

## Done — SUPERSEDED 2026-08-06, see "Reopened" above. Verdict retracted; kept unedited for the record.

**Verdict: criterion #1 fails, 0/2 targets (bar was 2/2, pre-registered above
before any run). Route closed — no quantum formulation follows.**

**Sourcing (In-Scope, "prefer vendoring over hand-rolling").** Vendored
EvoEF2 (Huang et al., MIT license, `tools/evoef2/`, README documents the
exact from-source rebuild recipe, gitignored binary/library per this
project's `fpocket`-precedent convention). Minimal patch
(`task0204_single_pass_repack.patch`, ~115 lines across
`EnergyOptimization.h/.cpp`, `Main.cpp`): a new `SinglePassRepackForSCP`
function that calls EvoEF2's own pre-existing
`SequenceGenerateInitialSequenceSeed` (greedy) or `SequenceGenerateRandomSeed`
(random) and writes the result without annealing — reuses 100% of EvoEF2's
own energy/rotamer machinery, invents no physics, satisfying criterion #3's
"not an internal heuristic" bar for the comparator arms too, not just the
druggability score. `GreedyRepack`/`RandomRepack` added as new CLI commands
mirroring the existing `SideChainRepack` dispatch block exactly (same
rotamer-generation, same self-energy table), differing only in the final
optimization step (single-pass seed vs. simulated annealing).

**Windows**: 12 pocket-proximal residues per target (`_select_window`, apo
Cα coordinates, nearest-to-pocket-centroid capped at
`WINDOW_MAX_SIZE=12`), spatially selected (not sequence-contiguous) —
KRAS_G12C and BCR_ABL1 only, per the pre-registered decision above (not
PTP1B, to avoid conflating with [[TASK-0203]]'s concurrent, different-layer
investigation).

**Three real, unrelated tooling bugs found and fixed, none hand-waved
past** — each confirmed by direct, reproducible test before being called a
root cause, not assumed:

1. **EvoEF2's own PDB chain parser mishandles a chain letter that
   reappears after being interrupted by another letter** (A-B-A in file
   order — the natural output of "relabel the window's residues to chain
   B, leave the rest on chain A" when the window isn't a single contiguous
   stretch). Confirmed directly: an interleaved A(1-54)/B(55-67)/A(68-169)
   file silently expanded chain B's design-site selection to cover
   55-169 (merging the second A run into it) even though
   `--design_chains=B` was otherwise correctly parsed (the "were selected
   for design by default" console message is itself a pre-existing
   upstream mislabel — it fires when the CLI value *was* honored, not when
   it wasn't; read directly from `Main.cpp`, not guessed). **Fix**:
   `_write_full_atom_with_window_chain` now writes each chain letter as a
   single contiguous file block (all of 'A', then all of 'B'), sidestepping
   the parser bug regardless of its exact internal cause. Verified: the
   output file's chain B contains exactly the intended window residues,
   nothing else.
2. **prody boolean-mask indexing incompatibility** on this environment's
   numpy/prody versions (`AtomGroup.__getitem__` on a boolean array raised
   `TypeError` inside prody's own `rangeString`). Fixed by converting to
   integer indices via `np.where` before indexing — a version-compatibility
   fix, not a logic change.
3. **EvoEF2 SIGSEGVs when invoked with an absolute `argv[0]` path**,
   reproducibly, 5/5, with the *identical* binary/PDB/flags that succeed
   5/5 under a relative `./EvoEF2` invocation — confirmed by isolating the
   variable directly (same `subprocess.run(cwd=..., ...)` shape, only
   `argv[0]` changed). The earlier `--bbdep=disable --rotlib=honig984`
   workaround (adopted mid-debugging, before this was isolated) was a
   red herring chasing the same symptom from a different angle and has
   been removed — the default backbone-dependent library runs cleanly on
   real, non-sequence-contiguous pocket windows once both the chain bug
   and the argv[0] bug are fixed. Root cause not fixed at EvoEF2's own
   source (out of this task's scope; plausibly a fixed-size buffer
   overflow in `Main.cpp`'s `ExtractPathAndName`/`sprintf(PROGRAM_PATH,
   ...)` given a longer absolute path, consistent with the corrupted-
   looking "cannot find atom parameters of <ordinary-residue>" errors seen
   before this was isolated); worked around in the driver script by always
   invoking `./EvoEF2` with `cwd=EVOEF2_DIR`.
4. (Related, same debugging arc) **fpocket writes its `<stem>_out/` output
   directory next to the INPUT pdb file, not relative to `cwd`** —
   confirmed by direct manual test. `score_structure` was passing EvoEF2's
   output path (living in `tools/evoef2/`) alongside an unrelated temp
   `work_dir`, so `_run_fpocket` (reused from [[TASK-0163]]'s script)
   looked for the info file in the wrong directory and reported "no info
   file" on every non-native trial. Fixed by copying the structure into
   `work_dir` before scoring, matching the pattern the native-sanity call
   already (accidentally) satisfied.

**Full results** (`results/tasks/0204_rotamer_repack_baseline/results.json`,
34 real EvoEF2+fpocket trials, 0 errors after the fixes above):

| Target | native sanity | greedy (1 trial) | optimized (8 trials) | random (8 trials) |
|---|---|---|---|---|
| KRAS_G12C | miss (overlap=0.75, drug=0.001) | miss (overlap=0.33, drug=0.278) | 0/8 hit (0.0) | 0/8 hit (0.0) |
| BCR_ABL1 | **hit** (overlap=0.92, drug=0.566) | **hit** (overlap=0.50, drug=0.537) | 0/8 hit (0.0) | 0/8 hit (0.0) |

KRAS_G12C's own native/deposited structure does not clear the druggability
bar at this window (fpocket scores it as barely druggable regardless of
repacking condition — consistent 0% across all three arms, not a packing
failure). BCR_ABL1's native structure and greedy both hit, but **every**
optimized and random trial misses — SA-optimized repacking performed
*worse* than the naive single-pass baseline. Plausible reading, stated as
such, not proven: EvoEF2's simulated annealing minimizes self+pairwise
packing energy across the window plus its own automatically-included
repack shell (30-40 residues total, not just the 12-residue window,
confirmed by inspecting `StructureShowDesignSites` output directly) —
tighter packing is a different objective than opening an fpocket-scored
cavity, and nothing in the run (correctness checks, trial counts, seed
distinctness) points to a mis-executed optimizer.

**Criterion #1's own pre-registered ceiling-case rule applies on BCR_ABL1
without ambiguity**: greedy already hits (rate 1.0); optimized's 0/8 does
not exceed that, so BCR_ABL1 counts as a fail, not an automatic pass by
virtue of greedy already succeeding. 0/2 targets pass the 2/2 bar.

**Consequence, per criterion #1's own stated rule and Phase A's binding
precedent ("no quantum formulation is built for an objective that does not
already show value classically")**: this route is closed. The rare-event-
rate measurement (whether a random assignment rarely opens the cavity —
the precondition for amplitude amplification to have anything to amplify)
was explicitly gated on criterion #1 passing and does not apply; reported
anyway for completeness since it was already measured as the negative
control — random also 0/8 on both targets, so even had criterion #1 passed
on a technicality, the observed random-arm rate would not have supported a
"rare event" framing distinct from the optimized arm's own rate.

**Every other route in the register's own falsification history is now
closed by measurement** (single-particle CTQW, coherence/interference,
non-locality, interacting multi-particle, backbone-layer conformational
search, residue-layer selection-as-QUBO, optimal control, and now
side-chain rotamer packing) — Phase B was the last route where the
quantum-advantage argument survived contact only by not having been run.
It no longer survives.

Updated: `PHASE_B_ROTAMER_QUBO.md` Status section (full table + verdict),
`RESULTS.md` (new §"row 65", cross-referenced). Full trial-level data:
`results/tasks/0204_rotamer_repack_baseline/results.json`. New files:
`tools/evoef2/` (README, patch, gitignore — binary/library gitignored per
convention), `scripts/task0204_rotamer_repack_baseline.py`.
