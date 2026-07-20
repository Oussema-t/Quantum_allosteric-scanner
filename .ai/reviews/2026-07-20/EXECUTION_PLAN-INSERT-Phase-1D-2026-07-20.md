<!-- INSERT into __WORK_IN_PROGRESS__/EXECUTION_PLAN.md.
     Block A: a new phase section, after "## Phase 1C ..." and before
     "## Phase 2 ...". Block B: a one-liner-intents batch entry, appended
     under "## Task files created from this plan". Block C: a note appended
     to "## Critical path to 15 Sept". Do not renumber existing IDs. -->

=== BLOCK A — new phase section (insert after Phase 1C, before Phase 2) ===

## Phase 1D — new-observable falsification battery (2026-07-20, from REVIEW-panel-2026-07-20)

Four new-observable hypotheses ([[HYP-P9]]–[[HYP-P12]]), triaged this batch by
cheapest-possible synthetic falsifiers before any real run. Three of five
earlier-proposed families were killed on the toy (cycle-counting, naive
interacting multi-particle, and the trivial single-loop version — recorded in
the review, not filed as tasks). The survivors are filed below. **The battery
is gated: 1D.1 (openness premise) is the make-or-break, classical, ~½-day run;
1D.2/1D.4 inherit its fate.** Division of labor per the in-thread proposal —
the collaborator builds + runs the code; physics is pre-checked here so every
acceptance criterion is fully pre-registered and an agent can execute unbiased.

| ID | Task | Why now | Status |
|---|---|---|---|
| 1D.1 | **[FILED] [[TASK-0139]] — coordinated-closure graph-openness premise (HYP-P10)** | **P0 of this batch.** Classical, no quantum, ~½ day. Tests whether real cryptic pockets are Euclidean-near but apo-graph-far (the multi-site reframe that survives Falsifier A's kill of the trivial single-loop idea). Gates 1D.2/1D.4. Distinct from the `cumulative_overlap` gate ([[TASK-0059]]/[[TASK-0120]]) — a structural-graph question, not a soft-mode-span question. Matched-spread random-closure null, Bonferroni across 7 targets. **A clean negative kills the loop family in an afternoon — the intended high-information outcome.** | TODO |
| 1D.2 | **[FILED] [[TASK-0140]] — chiral (broken-time-reversal) circulation observable (HYP-P9)** | **P1.** The disciplined form of the collaborator's Idea #2 (an arbitrary initial phase is a label-leaking knob; complex Peierls hopping is the only gauge-invariant phase, acting on cycles — Zimborás 2013, Lu 2016). Hodge-decomposed circulating current is proximity-orthogonal by construction; passed both synthetic gates this batch (dissociates coupling from well; beats floor at ρ≈+0.33 vs CTQW's +0.6..+0.97). Single-particle → modeling advantage, NOT asymptotic. Soft-gated by 1D.1. Eval with CIs ([[TASK-0112]]) + stratified AUC ([[TASK-0123]]) + permutation null ([[TASK-0131]]). | TODO |
| 1D.3 | **[FILED] [[TASK-0141]] — engineered-dephasing (ENAQT) sweep (HYP-P11)** | **P1, independent.** The collaborator's Idea #1, run with the correct scored quantity (discrimination, NOT transport efficiency). Physics prior (this batch, `enaqt_sanity.py`): no γ helps — dephasing de-traps only by relaxing to classical diffusion = the proximity confound (AUC 0.72→0.16, ρ +0.10→+0.92 as γ:0→5). Run anyway: a literature-anchored negative discharges the **noise-resilience** secondary objective with a mechanism. γ→∞ classical-limit sanity endpoint mandatory; γ never tuned to labels. | TODO |
| 1D.4 | **[FILED] [[TASK-0142]] — Hodge-L1 + persistent H2 observable (HYP-P12)** | **P2, gated on 1D.1/1D.2 showing life.** The correct topological home for the multi-site closure: a capped pocket is an H2 *void* (not H1 loop — why Falsifier D's grooves were invisible); the ligand-as-k-simplex is what L1 keeps and the graph Laplacian discards. The one rung where the biology (capped cavity) meets a genuine quantum-advantage object (quantum Betti / Hodge-Laplacian estimation, LGZ; Jones-polynomial BQP-completeness). Real persistence tooling (GUDHI/Ripser) mandatory — no homemade b1 as evidence. Matched random-patch null ([[TASK-0133]]). | TODO |

**Forward-proposal note (writing, not code — [[TASK-0142]] Out-of-Scope):**
the #P-hard / BQP framing (self-avoiding cycle counting; quantum Betti /
Hodge-Laplacian estimation, regime-dependent BQP; Jones polynomial at roots of
unity, BQP-complete) is the Phase-2 forward-proposal backbone, to be written up
backed by whichever of 1D.1–1D.4 survives — labeled clearly as a proposal, not
a demonstrated advantage. This is the framing under which "advantage" survives
contact with the falsification apparatus.

**Explicitly ruled out this batch (recorded, not filed):** cycle-*counting* as
an observable (ambient b1~8N drowns any added loop); naive interacting multi-
particle walks (the coincidence observable reduces to single-particle², and
on-site repulsion reduced co-occupation — Falsifier C near-no); arbitrary
initial-phase sweeps (label-leaking knob, subsumed by 1D.2's gauge-invariant
flux). Grover / QML kernels / HHL remain ruled out per prior batches.

=== BLOCK B — batch entry (append under "## Task files created from this plan") ===

### 2026-07-20 batch — from REVIEW-panel-2026-07-20 (new-observable proposals)

- **[[TASK-0139]]** — coordinated-closure graph-openness premise on real
  targets (HYP-P10). P0/gating, classical. Make-or-break for the loop family.
- **[[TASK-0140]]** — chiral broken-time-reversal circulation observable
  (HYP-P9). P1. Idea #2 done right (gauge-invariant flux, not initial phase).
- **[[TASK-0141]]** — engineered-dephasing/ENAQT sweep (HYP-P11). P1. Idea #1
  with discrimination (not transport) as the scored quantity; expected-negative
  pre-registered, overturnable by data.
- **[[TASK-0142]]** — Hodge-L1 + persistent H2 observable (HYP-P12). P2, gated.
  The topological rung + the quantum-Betti advantage bridge.

=== BLOCK C — append to "## Critical path to 15 Sept" ===

**2026-07-20 addendum — new-observable battery sequencing.** Run [[TASK-0139]]
first and alone; it is classical, ~½ day, and decides whether [[TASK-0140]] and
[[TASK-0142]] are worth running at all. [[TASK-0141]] is independent and can run
in parallel (its value — discharging the noise-resilience objective — holds even
as the pre-registered negative). None of 1D.* blocks the six-page write-up: if
1D.1 fails, the loop family becomes one honest paragraph ("we tested the
multi-site closure premise and it does not hold on these pockets"); if it
passes, 1D.2/1D.4 become the batch's positive content and the quantum-Betti
forward proposal gets its empirical anchor. **The writing remains the binding
constraint — do not let the battery displace it.**
