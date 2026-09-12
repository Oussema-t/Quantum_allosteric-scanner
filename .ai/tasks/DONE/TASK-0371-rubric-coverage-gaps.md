# TASK-0371 — Rubric coverage: work we did that the proposal never mentions, and the one gap that is a real strategic risk

- Status: Done
- Owner: **Reviewer** (scoring judgement + Team Lead decision on the last item)
- Priority: **Medium-High — cheap points, except the last item, which is a genuine trade-off**
- **Blocked on [[TASK-0367]]** for length: the body is currently over the limit, so nothing may be added until the count is true and something has been cut.
- Filed: 2026-09-11 by Reviewer thread (id via `claim.py reserve-next`)
- Source: `.ai/reviews/2026-09-11/REVIEW-2026-09-11-external-adversarial-submission-package.md`, "Strategic: rubric coverage"
- Related: [[TASK-0367]], [[TASK-0369]]

## Three things we did and did not say

Each is a clause, not a section, and each answers a criterion we currently leave
partly unanswered.

1. **Challenge Statement §4.1: participants "must build a quantum circuit."**
   We transpiled against `FakeSherbrooke` — 538–1486 two-qubit gates at coarse
   resolution, fidelity ≈ 0.015. **The proposal reports only analytic gate
   counts.** One clause naming the transpilation meets the letter of a mandatory
   sentence in the problem statement. Verify the numbers against their own
   artifact before quoting them.

2. **§4.2 noise resilience.** We tested it, and the phase-free robustness
   hypothesis was **falsified on balance**. It is absent from the proposal.
   A falsified robustness claim is still an answer to a secondary objective, and
   omitting it looks like we never addressed noise at all.

3. **§4.2 3D visualisation.** The Challenge Statement asks for output that
   prioritises *"3D visualization of the quantum connectivity maps"*. The
   main-branch 3Dmol application does exactly this. **If it is publicly
   reachable**, one clause covers the criterion — which makes it contingent on the
   same repository-visibility decision as [[TASK-0369]] §A.

## The strategic gap: Phase 2 contains no quantum execution

This is the item worth real thought rather than a clause.

**The position is scientifically defensible** — we measured that the quantum stage
adds nothing, so proposing to run it on hardware would contradict our own result.
**But it puts Technical Approach (25%) and Feasibility (20%) at risk**, because a
reviewer scoring a Quantum challenge sees a Phase-2 plan with no quantum in it.

**Option offered by the reviewer:** a small, pre-registered hardware arm — Braket
or Classiq — using the challenge's **own** ref [11] log encoding (~10 system
qubits + 1 ancilla, so it fits real hardware; 10⁵–10⁶ gates, so it will be noisy).

**Framed as a noise measurement and an instrument test subject — explicitly not as
an advantage claim.** That framing is consistent with everything else we report:
we would be measuring what the hardware does to a signal we have already shown is
absent, which is a legitimate and honest thing to learn.

**Trade-offs, stated so the decision is made with them in view:**

- Costs body page budget we do not currently have.
- It will not find signal, and we must say so in advance rather than discover it.
- It converts "no quantum execution" into "one pre-registered, honestly-framed
  quantum execution", which is a materially different answer to two criteria
  carrying 45% of the score between them.

**This is a Team Lead decision, not a Reviewer one.** Record the decision either
way — including a decision *not* to do it, with the reason — so that a Phase-2
reviewer asking "why no hardware?" gets our answer rather than their assumption.

## Constraints

- **Nothing is added until the page count is correct and something has been cut.**
  [[TASK-0367]] first, then [[TASK-0369]]'s trims, then this.
- Every number quoted here is currently **unverified by this thread** — the
  FakeSherbrooke gate counts and fidelity came from the reviewer. Check each
  against its own artifact before it enters the document. This register has twice
  been caught repeating a number instead of checking it ([[TASK-0348]],
  [[TASK-0366]]).
- No claim of quantum advantage, anywhere, under any framing.


---

## Done — verification pass, 2026-09-12 (Reviewer)

**No submission text changed.** The body is **7/6 and FAILING**, so nothing may be
added until [[TASK-0369]] cuts. What this pass delivers is the thing that must
precede any text: **every number the external reviewer supplied, checked against
our own artifact** — which this register has twice been caught not doing
([[TASK-0348]], [[TASK-0366]]).

### 1. FakeSherbrooke transpilation — CONFIRMED, and the reviewer's framing of it is WRONG

Verified at `.ai/tasks/DONE/TASK-0182-hardware-realization-and-resource-accounting.md:253-270`:

- Coarse-grained to Louvain's actual N≈9–15: **538–1486 two-qubit gates, depth
  1010–2565**, transpiled against `qiskit_ibm_runtime.fake_provider.FakeSherbrooke`
  — a genuine calibration snapshot, not a model.
- Smallest circuit tested (MYC_MAX, 538 two-qubit gates): **estimated fidelity
  0.015** against FakeSherbrooke's real median ECR error of **0.78%**, under a
  disclosed `(1-p)^n_2q >= 0.5` usability bar, stated as a judgment call.
- Also there and not in the reviewer's summary: **IQM Garnet topology transpiled
  shallower at every data point** (KRAS_G12C N=12: depth 965 vs 1859) — disclosed
  as a connectivity difference, explicitly *not* a hardware-superiority claim.

**The reviewer's claim that "the CP reports only analytic counts" does not hold.**
`PHASE1_SUBMISSION_V4.md:103` already says *"Against a real IBM device calibration
snapshot, every mandated target verdicts `FAULT_TOLERANT_ONLY` **at both
resolutions**"* — that sentence **is** the transpiled result.

**What is genuinely missing is one word, not a paragraph.** Challenge Statement
§4.1 says participants *"must build a quantum circuit"*. Our paragraph implies one
was built and transpiled; it never says so. A reviewer checking that mandatory
sentence can miss it.

### 2. Noise resilience — CONFIRMED, and genuinely absent

`TASK-0182:277-282`: **"Pre-registered phase-free-robustness hypothesis: falsified
on balance."** Supported (time-averaged more noise-robust than a finite-time
snapshot) on KRAS_G12C and MYC_MAX at higher error rates; **contradicted on
BCR_ABL1**, where the time-averaged form was *worse* at every non-zero error rate.

**This is the real gap of the three.** §4.2 names noise resilience as a secondary
objective; we tested it, pre-registered the hypothesis, and falsified it — and the
submission says nothing, which reads as never having addressed noise at all.

### 3. Coarse-graining — ALREADY COVERED, and the reviewer missed it

§4.2 also asks participants to *"demonstrate a method for coarse-graining … and
**prove that this compression retains the essential topological signal**."*

`PHASE1_SUBMISSION_V4.md:103` already answers it, with a measured negative:
*"Coarse-graining to a NISQ-plausible 10–15 qubits destroys the ranking signal
(retention Jaccard 0.00–0.18)"* — from `TASK-0182:271-278` (Jaccard 0.00–0.18,
Spearman 0.02–0.26, top-10 retention between full and coarse-then-projected-back).

**We answer a named secondary objective with a falsifying measurement.** No change
needed; recorded so nobody "fixes" it.

### 4. 3D visualisation — the artefact exists; its reachability is NOT verified

`CLAUDE.md:27-29` records a 3Dmol.js + Plotly frontend deployed at
`https://quantum-allosteric-scanner.onrender.com`, login `jury` / `QAS@CC`.

**A `curl` from this environment returned no response (000).** That is *not*
evidence the app is down — this sandbox's network access is unreliable and a Render
free-tier instance may simply be asleep. **Someone must open it in a browser before
the URL goes anywhere near the submission.** Do not cite an endpoint we have not
seen respond.

Note this route does **not** depend on the repository going public on the 15th: a
credentialed live URL answers §4.2 on its own.

### 5. Wording, ready to drop in when space exists

Costed at roughly 40 words total, in priority order:

1. **Noise (the real gap)** — *"We pre-registered a phase-free robustness
   hypothesis and falsified it: time-averaging is more noise-robust than a
   finite-time snapshot on two of three targets and worse on the third."*
2. **Circuit (§4.1's mandatory sentence)** — add **"transpiled"** to the existing
   hardware sentence: *"…built and transpiled against a real IBM device
   calibration snapshot…"*. One word.
3. **Visualisation** — one clause naming the live 3D connectivity viewer, **only
   after someone has loaded it**.

### 6. The Phase-2 quantum-execution decision — recommendation

The reviewer proposes a small pre-registered Braket/Classiq arm on ref [11]'s log
encoding. **I recommend against it, and for [[TASK-0374]]'s E3 instead.**

- A hardware run of *our own walk* re-executes the thing we measured as adding
  nothing. Its honest pre-registration would read *"we expect to find no signal,
  degraded by noise"* — which is not a Phase-2 plan, it is a demonstration of a
  null we have already published.
- **E3 computes `ΔH_AB` between allosteric- and active-site fragments, apo vs
  holo — a quantity no force field can produce.** That is quantum execution where
  the quantum step does work nothing else does, and it answers the same 25%/20%
  criteria without asking a reviewer to believe we changed our minds about our own
  result.
- Both are capability claims, never advantage claims. E3 is simply the one with a
  reason.

**Team Lead's call.** Recorded either way, per this task's own filing — including
a decision to do neither, which is defensible and should be stated rather than
left for a Phase-2 reviewer to assume.

### Not done

- No submission edit (blocked on [[TASK-0369]]'s cuts).
- Reachability of the live app, which needs a human with a browser.
- Whether the `jury` / `QAS@CC` credential is appropriate to print in a submission
  — a question for the Team Lead, not a Reviewer.
