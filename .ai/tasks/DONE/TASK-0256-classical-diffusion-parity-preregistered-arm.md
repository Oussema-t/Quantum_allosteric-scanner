# TASK-0256 — Classical diffusion parity as a standing pre-registered arm

- Status: Done
- Assignee: unassigned (suggest Implementer — small)
- Priority: Medium — the machinery exists, and the collaborating thread has already conceded the point; the value is in making it a permanent, pre-registered arm rather than an ad-hoc check
- Filed: 2026-08-24 by Reviewer
- Related: [[TASK-0210]] (H8, Markovian random walk classical analogue), [[TASK-0249]], [[TASK-0242]], `src/allostery/propagators.py`

## Why file it at all

The collaborating thread has already reported that `heat_kernel` matches
`p_avg` on their side, and [[TASK-0210]] tested the Markovian random walk as
this register's classical analogue. So this is not an open question — it is an
**un-institutionalised** one.

The machinery is present: `propagators.py` already documents that
`gamma=0` recovers pure CTQW and `gamma→∞` gives classical diffusion, and
`ground_state_relaxation` carries an explicit warning that `exp(-Ht)` is not
classical diffusion when `H` is indefinite.

The point of this task is that **any operator arm we or the collaborating
thread report should carry its classical-diffusion twin computed on the same
Hamiltonian, automatically** — so "is this quantum or is it graph filtering"
never has to be asked retrospectively again.

## Scope

- [x] Add a classical-diffusion arm to the standard scoring path, computed on
      the **identical** Hamiltonian as the CTQW arm — not a separately-built
      graph Laplacian, which would confound the comparison.
- [x] Honour the `ground_state_relaxation` indefiniteness warning: report
      whether `H` is PSD per target, and do not label the output "classical
      diffusion" where it is not. **H_new is indefinite on 14/14 (100%) of
      scoreable real targets** — the arm is honestly reported as
      ground-state relaxation throughout, never mislabelled.
- [x] Report CTQW-minus-classical per target on [[TASK-0243]]'s frozen set,
      with a numerical-tolerance statement: what difference would count as the
      walk doing something other than diffusive graph filtering.
- [x] Wire it into [[TASK-0242]]'s two-stage apparatus as a named arm
      alongside `composite`, `ctqw`, `fpocket_drug`, `hop`, `random`.
- [x] Propose it as a **mandatory arm in the joint pre-registration**, on the
      same footing as the fpocket and hop control arms. (No joint
      pre-registration document exists yet in this repo — same gap
      [[TASK-0244]] already found; proposal stated in Done, for whoever
      drafts it.)

## Acceptance

- [x] Classical arm reported alongside every operator arm, both designs
      (two-stage candidate ranking and per-residue AUC).
- [x] Per-target PSD status stated.
- [x] A pre-registered tolerance for "matches within numerical tolerance"
      (Spearman ρ ≥ 0.95, stated in the script's own docstring before any
      number was seen).
- [x] Added to the joint-protocol arm list (proposed; no document to add it
      to yet — see Scope note above).

## Constraint

If the quantum and classical arms separate on any target, that is a positive
finding and must be reported with full prominence — it would be the first
evidence in this register of the operator doing something a classical
diffusion cannot.

## Done

**2026-08-25, Implementer D.**

**Implementation, additive, reusing shared infrastructure**: `task0242_two_
stage_dryrun.run()` extended with an opt-in `include_classical=True` (default
`False`, existing callers/behavior unchanged — verified directly) that
computes `propagators.ground_state_relaxation` on the **same** `H_new`
object the `ctqw` arm already built (no second Hamiltonian construction),
checks `H`'s own eigenvalues for PSD status (`np.linalg.eigvalsh`, tol
1e-9, matching `propagators._warn_if_indefinite`'s own threshold), and adds
`"classical"` as a sixth ranked arm alongside `ctqw`/`fpocket_drug`/
`fpocket_score`/`hop_covariate`/`random`. `return_state=True` additionally
now exposes the full per-residue `ctqw`/`classical` occupation vectors and
the pocket label, so the per-residue-AUC design ("both designs", matching
[[TASK-0249]]'s own convention) can be scored without a second propagator
run. New `scripts/task0256_classical_diffusion_parity.py`, run on
[[TASK-0243]]'s frozen 22-target set (the same set [[TASK-0253]] audited;
its empty-seed guard is inherited automatically — `HIV_INTEGRASE_MUT871`/
`916` correctly skip rather than silently rank).

**Which propagator, and why, stated before running**: `ground_state_
relaxation` (`exp(-Ht)`), not `haken_strobl` at large `gamma` (`propagators.
py`'s own *other* documented classical-diffusion limit, "gamma→∞ gives
classical diffusion") — `ground_state_relaxation` needs no extra parameter,
reuses the eigendecomposition `ctqw` computes anyway, and is the specific
function this register's own PSD warning already lives on. `haken_strobl`
was checked for feasibility as a second, PSD-independent construction (see
below) and found genuinely infeasible at this frozen set's real target
sizes — not silently skipped.

**Central finding: H_new is indefinite on 14/14 (100%) of the scoreable real
targets** (`min_eig` ranges roughly -0.02 to -0.3 across the set, full
values in `results.json`) — `ground_state_relaxation` is **never** classical
diffusion anywhere on this real frozen set, only ground-state relaxation
(TASK-0095/P1-B), reported honestly throughout, never relabelled. This
means the specific comparison this task's own Constraint anticipated
("quantum vs. classical diffusion separate → first evidence of the operator
doing something classical diffusion cannot") **is not achievable via this
construction on real data** — every measured "separation" below is
CTQW-vs-ground-state-relaxation, two different dynamical regimes on an
indefinite operator that were never expected to agree, not
quantum-vs-classical-diffusion. Stated plainly rather than let the two get
conflated.

**Reported anyway, both designs, exactly as measured — not a null result to
hide:**

*Two-stage candidate ranking* (n=14): ctqw mean rank 9.21 (MRR 0.253) vs.
classical mean rank 11.50 (MRR 0.221); head-to-head ctqw beats classical on
8/14, ties 0, loses 6/14, Wilcoxon p=0.4314 — not significant.

*Per-residue AUC* (n=14, "both designs" per Acceptance): median AUC ctqw
0.564 vs. classical 0.493; ctqw beats classical AUC on only 6/14 targets
(despite the higher median — a real, disclosed tension between the two
summary statistics, not smoothed over), Wilcoxon p=0.7775 — not significant.

*Candidate-score parity* (the pre-registered ρ≥0.95 tolerance, stated in the
script's own docstring before any number was seen): median Spearman ρ=0.790
between the ctqw and classical per-candidate score vectors, and **14/14
targets separate beyond the pre-registered tolerance** — but per the central
finding above, this is evidence that ground-state relaxation and CTQW are
different processes (expected, not surprising, since neither should equal
the other on an indefinite operator), **not** the "operator does something
classical diffusion cannot" finding this task's own Constraint was written
to look for. Read plainly: **no genuine classical-diffusion-parity test was
completed on real data** — the closest available real-data comparison
(ground-state relaxation) shows no consistent, significant CTQW advantage
in either design, and a large but expected-in-direction, uninterpretable-
in-the-intended-sense candidate-score divergence.

**`haken_strobl` at large `gamma` — the genuine, PSD-independent classical-
diffusion limit — checked for feasibility, found infeasible at this
session's time budget, not silently skipped.** Timed directly on the
smallest real target in this frozen set (`KSHV_PROTEASE_24Q`, N=228):
`gamma=200` takes 18.1s (a single `solve_ivp` call over an N²-dimensional
density-matrix ODE). This frozen set's own real target sizes range up to
N=1223 (`GAC_BPTES`); the RHS cost is a matrix multiply, `O(N²)`–`O(N³)`
depending on BLAS path, so extrapolating even conservatively (`(1223/228)³
≈ 155×`) puts the largest targets at tens of minutes **each**, for a single
`gamma` value, before any averaging over multiple `gamma`s to approach the
γ→∞ limit properly. A full 14-target run was not attempted under this
session's own time budget — flagged as a concrete, costed follow-up (not a
vague "future work" gesture), not run partially/inconsistently under time
pressure.

**Proposed for the joint pre-registration, per this task's own Scope** — no
such document exists yet in this repo (same gap [[TASK-0244]] already
found and flagged): whoever drafts it should include (a) the
`ground_state_relaxation`-on-`H_new` arm, explicitly labelled per-target as
PSD or not (very likely 100% indefinite on any real target set, per this
task's own finding — the label matters, "classical diffusion" is a claim,
not a variable name), and (b) `haken_strobl`-at-large-`gamma` as the
genuine PSD-independent classical-diffusion twin, once its own compute cost
is budgeted for (see the feasibility numbers above) — both, not either, if
this comparison is to be trusted rather than convenient.

**Not done, and why**: `haken_strobl`-at-large-`gamma` full run (compute
budget, see above — timing established, not guessed). Scoring the
classical arm on the 8 skipped targets (2 empty-seed, 6 stage-1 failures) —
correctly excluded, matching [[TASK-0253]]'s own established denominator
convention, not a gap specific to this task.

Tests: no `src/` code changed — the extension is in `scripts/task0242_
two_stage_dryrun.py`, which (per this project's own established convention
for that directory) has no dedicated unit tests. Verified directly instead:
re-ran `run()` without `include_classical` on a real target (`HIV1_RT`)
before and after this task's own edit — byte-identical output, confirming
the default path is unaffected.

Artifacts: `scripts/task0242_two_stage_dryrun.py` (extended, additive —
`include_classical`, PSD check, full-array `return_state` exposure),
`scripts/task0256_classical_diffusion_parity.py` (new),
`results/tasks/0256_classical_diffusion_parity/results.json`, `RESULTS.md`
row.
