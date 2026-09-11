# TASK-0371 — Rubric coverage: work we did that the proposal never mentions, and the one gap that is a real strategic risk

- Status: TODO
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
