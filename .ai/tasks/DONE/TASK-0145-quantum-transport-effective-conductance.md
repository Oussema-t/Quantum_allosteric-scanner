# TASK-0145 Quantum transport / effective-conductance observable (Landauer-Büttiker transmission + classical effective resistance)

## Context

- ID: TASK-0145
- Title: reframe the scoring question from "where does an excitation
  seeded at the active site spread to over time" (every observable this
  project has tried) to "what is the steady-state current/transmission
  from the active site to each candidate residue" — a non-equilibrium
  steady-state (NESS) transport calculation, the formalism used in
  molecular electronics (Landauer-Büttiker; Nitzan & Ratner's quantum
  transport reviews) rather than a seeded-walk-and-wait one.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer C (this thread)
- Claimed At: 2026-07-24
- Source: raised by the orchestrating user, 2026-07-20, as an open
  "what's still worth trying" question; this Architect/Planner thread's
  own analysis rated it the highest-plausibility remaining idea
  precisely because it has a structural argument (not just "different
  math") for why it might not inherit the proximity confound — the same
  shape of argument that made chiral circulation (TASK-0140) the one
  idea that escaped it before its own gating premise failed.
- Priority: **P1.** Complements, does not duplicate, [[TASK-0136]]'s
  percolation/edge-connectivity work — that is a discrete, combinatorial
  connectivity measure; this is a continuous conductance/transmission
  measure. Both test "is communication distributed or bottlenecked,"
  from genuinely different mathematical angles.

## Intent Contract

- Outcome: two related quantities, built in order (cheapest, most
  well-established first):
  1. **Classical effective resistance/conductance** between the active
     site and each candidate residue — closed-form, no simulation:
     `R_eff(i,j) = L^+_ii + L^+_jj - 2*L^+_ij`, where `L^+` is the
     Moore-Penrose pseudo-inverse of the graph Laplacian. **This is
     nearly free to compute** — `H14_anm_pinv_trace` already computes
     `L^+`'s trace via `np.linalg.pinv`; this task needs the full matrix,
     not just its trace, reusing the same decomposition. Score
     `1/R_eff(active_site, j)` (conductance, higher = better connected)
     per candidate residue `j`.
  2. **Quantum generalization**: a Landauer-Büttiker-style transmission
     `T(E) = Tr[Gamma_L G(E) Gamma_R G(E)^dagger]` using the retarded
     Green's function `G(E) = (E - H + i*eta)^-1` at a stated energy `E`
     (start with `E=0` and/or the walk's own natural energy scale from
     `H`'s spectrum — state the choice and why), with `Gamma_L`/
     `Gamma_R` as simple broadening/coupling terms at the source and
     candidate sites (state the exact coupling model chosen — a minimal,
     standard choice, e.g. a small imaginary self-energy at the source/
     drain sites, is acceptable; do not invent an elaborate lead model
     without justifying it against the literature cited above).
  3. **Report whether the quantum transmission differs meaningfully from
     the classical effective resistance**, per this project's own
     "effectively decoherent" precedent (`time_averaged_ctqw`'s own
     finding that its converged limit is provably phase-free) — if `T(E)`
     reduces to (or tracks) `1/R_eff` closely, that is itself an honest,
     reportable finding ("the quantum transmission calculation is
     classical here too"), not a failure to hide.
- Why required, not assumed: effective resistance already accounts for
  *all* parallel paths between two nodes, weighted by strength — a
  genuinely different mathematical object from graph-hop distance
  ([[TASK-0136]]) and from CTQW occupation (everything else). Whether
  either quantity is less proximity-confounded than what's already been
  tried is an empirical question this task answers, not assumes.
- In Scope:
  - Implement effective resistance/conductance from `L^+` (reuse
    `H14_anm_pinv_trace`'s existing pseudo-inverse call, do not
    re-decompose).
  - Implement the Green's-function transmission calculation, stating the
    lead/coupling model choice explicitly.
  - Synthetic falsification gate first, per this project's own standing
    discipline (e.g. the dumbbell construction, [[TASK-0103]] — does
    either quantity track coupling strength, not just well-depth or
    proximity, on a constructed case before trusting real data).
  - Score both quantities on all 3 mandatory targets against
    [[TASK-0094]]'s proximity floor, with block-bootstrap CIs
    ([[TASK-0112]]) and a permutation null on any max-over-something
    step (this project's own standing requirement, per
    `.ai/reference/IMPLEMENTER_SPINUP_BRIEF.md`).
- Out Of Scope:
  - Reselecting the submission operator (Tier-2-gated, [[TASK-0100]]).
  - A full multi-lead/multi-terminal transmission network — a two-
    terminal (source, one candidate at a time) calculation is sufficient
    to answer this task's own question.
- Constraints And Invariants: state the energy `E` and lead-coupling
  model explicitly in Done — these are real modeling choices, not
  free parameters to tune against labels.
- Planned Validation: the dumbbell gate first; then real-target scoring
  against the proximity floor, reported whichever way it comes out.

## In Progress

None

## TODO

- [x] Implement effective resistance/conductance from `L^+` (reuse
      existing pseudo-inverse machinery).
- [x] Implement Green's-function transmission `T(E)`, stating the lead/
      coupling model and energy choice.
- [x] Synthetic falsification gate (dumbbell or equivalent) before real
      data.
- [x] Score both quantities, all 3 mandatory targets, vs. the proximity
      floor, with CIs and a permutation null.
- [x] Report whether `T(E)` differs meaningfully from classical `1/R_eff`
      — an honest "it's classical here too" is a valid outcome.

## Dependency

- [[TASK-0094]] (Done) — proximity floor.
- [[TASK-0103]] (Done) — dumbbell falsification gate.
- [[TASK-0112]] (Done) — bootstrap CI.
- Reuses `H14_anm_pinv_trace`'s pseudo-inverse computation.

## Open Questions

- Exact lead/coupling model for the Green's-function calculation — not
  pre-decided; Implementer's call, state the choice and why in Done.
  **Resolved**: wide-band-limit (WBL) leads, `Gamma_L`/`Gamma_R` diagonal
  and nonzero only at the source/candidate contact site(s)
  (`gamma_lead = 0.1 * bandwidth` default, weak-coupling regime) — the
  minimal standard model (Nitzan & Ratner), no elaborate lead structure
  invented.
- Energy `E` at which to evaluate `T(E)` — state the choice; report
  sensitivity if it materially changes the verdict. **Resolved**:
  `E=0` (DC/zero-bias limit) is the primary, pre-registered choice —
  chosen because it is the point where a Laplacian's quantum
  transmission is expected to connect most directly to its classical
  effective-resistance limit (both zero-frequency/steady-state
  quantities), confirmed empirically (Spearman rho 0.74-0.85 vs. `1/R_eff`
  on real data, see Done). `E` sensitivity is real and large (see Done)
  — characterized as a KNOB via a small grid, not used to pick a
  best-scoring point against labels.

## Done

**2026-07-24, Implementer C (this thread).**

**Both quantities implemented, new `src/allostery/transport.py`.**
Effective resistance: `R_eff(i,j) = L+_ii + L+_jj - 2*L+_ij`, `L+` via
the same eigh-based pseudo-inverse convention `H14_anm_pinv_trace`
already established (not `np.linalg.pinv`), on a genuine combinatorial
graph Laplacian (`hamiltonians.H2_combinatorial_laplacian`) — confirmed
by direct inspection that `H_new` does **not** qualify (its diagonal
potential terms, and its use of the *normalised* Laplacian variant, both
break the null-space handling `R_eff`'s formula relies on). Multi-index
`source` handled via a virtual-supernode construction (a strong shorting
edge from every source residue to one new virtual node), reusing
`percolation.py`'s (TASK-0136) own already-debugged "virtual super-source"
pattern rather than re-deriving the shorted-supernode pseudo-inverse
formula from scratch. Verified against the textbook path-graph analytic
result (`R_eff(0,k)=k` for unit resistors in series) before trusting it
on anything else.

Quantum transmission: `T(E) = Tr[Gamma_L G(E) Gamma_R G(E)^dagger]`,
`G(E) = (E - H + i*Gamma/2)^-1`, wide-band-limit leads (see Open
Questions). **A real algorithmic contribution, not just a port**: since
`Gamma_R` at each candidate `j` is always a single-site diagonal
perturbation of the same source-only baseline, a Sherman-Morrison rank-1
update gives a closed form (`T(E,j) = gamma_lead^2 * sum_{s in source}
|G_0[s,j]|^2 / |1+i*(gamma_lead/2)*G_0[j,j]|^2`) computable from ONE
`N x N` matrix inversion (`G_0`) instead of `N` separate full
re-inversions per candidate — `O(N^2)` total once `G_0` is known, not
`O(N^4)`. Derived and verified numerically against a brute-force
per-candidate re-inversion (`tests/test_transport.py`) before trusting
it, not assumed correct from the algebra alone (matched to `1e-10`,
including confirming the brute-force reference's own imaginary part is
genuinely zero, as physically required).

**Synthetic falsification gate**: two new test classes in
`tests/test_dumbbell_negative_control.py`
(`TestEffectiveResistanceDumbbellGate`/`TestTransmissionDumbbellGate`),
reusing `build_dumbbell_network`/`_mean_auc_over_seeds` as-is per this
file's own established convention. Real finding while scoping the
gate: `R_eff` is **provably** well-invariant (a mathematical consequence
of the formula, not an empirical hope) — the well only touches `H`'s
diagonal, which `R_eff`'s off-diagonal-derived formula structurally
cannot see once the coupling-only adjacency is recovered (same recovery
`connectivity_robustness`'s own dumbbell adapter already uses); confirmed
directly by checking C1 and C2 (which differ only in `well_lobe`) score
*exactly* identically, not just similarly. Both observables give a clean,
decisive double dissociation against GSR on the conflict cells (C2/C3:
`R_eff` 1.000/0.000, `T(E)` 1.000/0.000, every seed, vs. GSR's own
well-following direction) — genuinely follow coupling, not the well. C1
(cues agree) is not asserted directionally for `T(E)`, matching
`TestModeCoparticipationDumbbellGate`'s own established precedent for
the identical reason (a deep co-located well perturbs the low-mode/
Green's-function structure into a resonance-sensitive regime even when
coupling agrees — `T(E)`'s own C1 measured at exactly 0.000, the same
value CP's C1 was independently found at). **A real, characterized
finding, not glossed over**: C4 (no well, equal coupling — the
"uninformative" null cell) has much higher per-seed variance for both
new observables (0.076-0.924 over 20 seeds) than the propagator-based
observables already in this file show at only 5 seeds — a genuine
property of exact resistor-network/Green's-function calculations being
more sensitive to the construction's own small per-seed random
intra-lobe weight differences than a propagator is; a wider seed count
(20, not this file's usual 5) is used for these two gates' C4 checks
specifically to get a stable mean rather than risk reading one noisy
small-sample draw as "off."

**Real-target scoring, all 3 mandatory targets**
(`scripts/transport_observable_real_run.py`), against TASK-0094's
proximity floor with block-bootstrap CIs and a permutation null on
every cell (not only the ones that clear — none of this task's own
scores are selected via a best-of-K sweep against labels, `E`/`gamma_lead`
are both fixed a priori per the resolved Open Questions above, so no
cell here is a "max of something" requiring correction in the usual
sense; the null is due-diligence scrutiny on each cell's own standing
number regardless). `R_eff`/`T(E)` both computed on the shared plain
Laplacian `L` (the direct classical-vs-quantum comparison this task's
own point 3 needs); `T(E)` additionally run on `H_new` directly (no
null-space requirement for the Green's-function calculation) as a
secondary check, since that is this project's actual submission
operator, not required by the Intent Contract but cheap once the
function exists and directly relevant to whether this reframing helps
the project's real pipeline:

| Target | R_eff AUC (p) | T(E=0) on L AUC (p) | T(E=0) on H_new AUC (p) | Floor |
|---|---|---|---|---|
| KRAS_G12C | 0.4187 (0.864) | 0.3716 (0.962) | 0.6402 (0.034) | 0.4818 |
| BCR_ABL1 | 0.5980 (0.107) | **0.6985 (0.003)** | 0.6362 (0.036) | 0.5817 |
| CARDIAC_MYOSIN | 0.4448 (0.774) | 0.4560 (0.726) | 0.4680 (0.651) | 0.5679 |

(`p` = permutation-null p-value, 1000 replicates, Bonferroni
alpha=0.0167 for 3 targets.) **Headline: one genuinely decisive result**
— BCR_ABL1's `T(E=0)` on the bare topological Laplacian clears
Bonferroni correction (p=0.003), the only cell of 9 that does. The two
`H_new`-based transmission cells that clear the floor at point estimate
(KRAS_G12C 0.640, BCR_ABL1 0.636) are uncorrected-significant only
(p=0.034/0.036 > 0.0167) — real but not decisive, the now-standard
pattern this project's other point-estimate clearances share. Every
cell's 95% CI overlaps the floor's own CI regardless of permutation-null
significance (matches `diagnostics.classify_failure`'s own point-
estimate-vs-CI distinction used throughout this project). CARDIAC_MYOSIN:
no signal from either observable, on either operator.

**Point 3 — classical vs. quantum, answered decisively**: Spearman
correlation between `1/R_eff` and `T(E=0)`, same shared Laplacian `L`,
is strongly positive on all 3 targets (rho=0.74-0.85, all p<1e-45) —
the quantum transmission calculation at the DC limit tracks the
classical effective-resistance ranking closely, confirming the physical
connection this task's own `E=0` choice was made for. **Not identical,
though**: BCR_ABL1's own numbers show the two are NOT interchangeable in
practice — `T(E=0)` on `L` (AUC 0.699, Bonferroni-significant) clearly
outperforms `R_eff` on the identical graph (AUC 0.598, not significant)
despite the strong rank correlation. So the honest finding is neither
"pure classical restatement" nor "wholly different physics" — a real,
if modest, quantum-formalism advantage survives on top of a mostly-
shared classical ranking, on the one target where either observable
shows real signal at all.

**`E` sensitivity — a real, large KNOB, characterized not exploited**:
a 3-point grid (`E in {0, 0.05, 0.1} * bandwidth`) swept per target,
*not* used to pick a best-scoring point against labels (`E=0` stays the
sole reported/pre-registered value). BCR_ABL1's own grid: AUC 0.698
(E=0) -> 0.306 (E=0.05*bw) -> 0.464 (E=0.1*bw) -- a >2x, non-monotonic
swing. `gamma_lead` is a much weaker KNOB by comparison (BCR_ABL1:
0.680-0.705 across a {0.05,0.1,0.2}*bandwidth grid) -- consistent with
being deep in the intended weak-coupling regime. Full grids:
`results_task0145_transport/transport_observable_real_run.json`.

**Not done / explicitly out of scope** per this task's own Intent
Contract: no submission-operator reselection (Tier-2 gated,
[[TASK-0100]]); no multi-lead/multi-terminal transmission network (a
two-terminal, one-candidate-at-a-time calculation, as scoped). Full
regression suite re-run after this change: 901 passed, 2 xfailed, no
failures.

**Generalization-set check, 2026-07-24 ([[TASK-0151]], per [[TASK-0115]]'s Rule #6):**
this task's own headline (BCR_ABL1's `T(E=0)` on L, p=0.003) does not clearly
generalize to PTP1B/CASPASE7. PTP1B's identical quantity comes back *below chance*
(AUC 0.382, p=0.926 — the opposite direction); CASPASE7 echoes the direction (AUC
0.748) but only at uncorrected p=0.011, not clearing TASK-0151's own stricter
6-comparison Bonferroni bar. This finding is not retracted (TASK-0151's own
Constraint) but should be framed as a single-target result, not yet cross-target
replicated. Full detail: `RESULTS.md`'s own generalization-set section,
open-questions row 33; `.ai/tasks/DONE/TASK-0151-generalization-check-transport-lowmode-findings.md`.
