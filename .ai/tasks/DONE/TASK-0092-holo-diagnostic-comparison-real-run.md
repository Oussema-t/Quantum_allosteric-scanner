# TASK-0092 Wire the holo-side diagnostic comparison into the real end-to-end run (apo-vs-holo upper bound, not a prediction)

## Context

- ID: TASK-0092
- Title: Compute `AUC_holo_Hnew_optimised`/`mean_rho_apo_holo`/
  `mean_jacc20` for the real KRAS_G12C/BCR_ABL1 runs (currently `N/A` in
  both reports) using `protocol.run_frozen_verdict`'s already-supported
  `holo_H`/`holo_source`/`holo_labels`/`apo_idx`/`holo_idx` kwargs, which
  [[TASK-0079.004]]'s orchestrator deliberately left unwired.
- Status: Done
- Owner: Implementer
- Source: [[TASK-0079.005]]'s first real end-to-end run, and the
  discussion that followed it (2026-07-12) — read that task's Done
  section in full before starting; this task's Context only summarizes
  the load-bearing reasoning, it is not the primary record.

### Why this is being asked for, precisely (do not misread this task's purpose)

The user's own framing, verbatim intent: *"biologically speaking, [holo]
is where the actual signal propagation takes place, whilst APO is just
our available starting structure"* — asking whether comparing against
holo would be informative. **The answer is yes, but not for the reason
the question's framing implies, and this distinction must survive into
whoever picks this up:**

- This project's central question (`PLAN.md`: "is the answer even in the
  apo topology?") is explicitly a **predictive-setting** question: in a
  real use case you do not have the holo structure in advance. Scoring
  against holo topology is never a legitimate substitute for the apo
  prediction — it cannot become "the real result."
- Its actual value is **diagnostic**: it distinguishes two different
  failure explanations for a near-chance apo result. (a) *Apo lacks the
  information* — the pocket is genuinely cryptic/anharmonic and only
  visible once the ligand has already induced the conformational change
  (the KRAS Switch-II textbook case `PLAN.md` itself names). (b) *The
  propagator/operator is the bottleneck, not apo's information content*
  — if holo topology, handed to the *same* operator family, **also**
  scores near chance, then more apo data wouldn't have helped; the
  method itself is what needs work.
- **This exact question was already asked and answered once this
  session, for a different operator family**: [[TASK-0067]]'s apo-vs-holo
  benchmark (raw GNM Kirchhoff, no potential terms, heat-kernel scoring)
  found the apo/holo gap was tiny (KRAS +0.009, BCR_ABL1 -0.020) —
  *an order of magnitude smaller* than the cutoff/weight-scheme spread
  it was measuring. That finding was specifically about the bare
  operator family. **It has not been checked for the full `H_new`
  pipeline** (with potential terms, CTQW propagation, the actual
  winning-candidate selection `TASK-0079.005`'s real run uses) — this
  task is that check, on the operator family that actually matters for
  the submission, not the diagnostic-only bare Kirchhoff.

## Intent Contract

- Outcome: `AUC_holo_Hnew_optimised`, `mean_rho_apo_holo`, and
  `mean_jacc20` populated with real values (not `N/A`) in a fresh run of
  KRAS_G12C and BCR_ABL1, plus an explicit statement of which failure
  explanation ((a) or (b) above) the result supports for each target.
- In Scope:
  - Build `holo_H` using the **same operator recipe as the winning apo
    candidate** (same `build_H_new` cutoff — `run_frozen_verdict`'s own
    docstring requires this: "built from the same operator recipe as the
    winning apo candidate... reconstructing one here would mean
    inventing a new search space, out of this function's scope"). The
    winning cutoff must be read from the real run's own selection, not
    assumed.
  - Derive holo-frame `pocket`/`active_site` masks entirely within
    holo's own numbering — reuse the `_holo_native_labels` pattern
    already written and validated for [[TASK-0067]]'s benchmark
    (`test_gnm_cutoff_weight_benchmark.py`): `functional_indices` called
    directly on `holo.coords`/`holo.ligand_groups`, the same
    `pocket_raw & ~active_site & ~terminal` assembly `build_labels` uses,
    no apo involved in deriving them. Do not re-derive this from
    scratch.
  - Compute `apo_idx`/`holo_idx` via `superpose.align_apo_holo` for the
    consistency computation.
  - Call `protocol.run_frozen_verdict` with the holo kwargs supplied —
    this function already implements the composition
    (`TASK-0079.003`'s Done section confirms holo keys are populated
    when these four arguments are given) — do not reimplement any part
    of that composition here.
  - Interpret the result explicitly per target: apo-vs-holo AUC gap
    small (matches TASK-0067's pattern) -> failure explanation (b),
    propagator/operator is the bottleneck; gap large -> failure
    explanation (a), apo genuinely lacks the information, a legitimate
    cryptic-pocket finding.
- Out Of Scope: [[TASK-0015]] (the holo-*direction* module — optimizing
  an admissible deformation *toward* holo, a generative search) — this
  task is a diagnostic *scoring* comparison only, reusing already-built
  machinery, not building new holo-direction search machinery. Do not
  conflate the two; a reviewer familiar with TASK-0015's name should not
  assume this task duplicates it.
  Also out of scope: modifying [[TASK-0079.004]]'s shipped orchestrator
  in place — land this as its own script/function (or an additive,
  opt-in flag on the existing orchestrator, implementer's call), not a
  silent behavior change to a task already marked Done.
- Constraints And Invariants: real network/compute, not mockable, same
  precedent as TASK-0079.005 and TASK-0067.
- Planned Validation: the populated report + the explicit (a)/(b)
  interpretation per target, written to this task's Done section.

## Dependency

- [[TASK-0079.003]] (`run_frozen_verdict`'s holo kwargs, Done) — the
  mechanism this task calls, not reimplements.
- [[TASK-0079.004]] (Done) — the orchestrator this extends (additively).
- [[TASK-0067]] — the `_holo_native_labels` pattern and the prior,
  narrower (bare-operator) apo-vs-holo finding this task extends to the
  full `H_new` pipeline.
- [[TASK-0079.005]] — the real run this task adds holo numbers to.

## Open Questions

- None yet.

## Addendum (2026-07-13, per user question) — extend to `ground_state_relaxation` for BCR_ABL1 specifically

User asked whether it makes sense to compare against holo structures in
light of TASK-0091's BCR_ABL1 finding (`ground_state_relaxation` clears
the proximity floor, AUC 0.7315). **Yes — add this as an explicit,
additional cell in this task's scope**, alongside the existing
`AUC_holo_Hnew_optimised` (CTQW) comparison: compute
`ground_state_relaxation`'s holo-side AUC for BCR_ABL1 the same way,
using holo-native labels/coords per this task's existing recipe.

**Important interpretive caveat, so this isn't over-read once computed**
(cross-references TASK-0102, filed the same day): if apo and holo
`ground_state_relaxation` occupancy patterns agree closely, that is
**not**, by itself, strong evidence the apo finding is real — a static
artifact of `H_new`'s potential-term composition (independent of the
seed, per TASK-0102's concern) would plausibly reproduce on holo too,
since apo and holo share nearly the same fold. Holo agreement is
necessary-but-not-sufficient corroboration; the seed-invariance check in
TASK-0102 is the more direct discriminator. Holo *disagreement*, or a
localization shift specifically toward the pocket upon ligand binding,
would be more informative — the kind of thing worth reporting explicitly
either way, not silently folded into a single pass/fail.

## Done

**Implemented as its own script** (`__WORK_IN_PROGRESS__/scripts/holo_diagnostic_comparison.py`),
not a modification of `run_challenge.py` (per Out Of Scope). Two-pass per
target, both real `run_frozen_verdict` calls: pass 1 (apo only) discovers
the real winning candidate for this fresh run; pass 2 supplies
`holo_H` (built from the *same* operator recipe as pass 1's winner, via
a name->builder map, not assumed to always be `H_new`), `holo_source`,
`holo_labels` (via TASK-0067's own `_holo_native_labels`, imported
directly from `test_gnm_cutoff_weight_benchmark.py`, not re-derived),
and `apo_idx`/`holo_idx` (`superpose.align_apo_holo`). Pass 2 asserts it
re-selects the same winner as pass 1 (selection is blind/deterministic,
no RNG in `select.py`'s scoring path) as a live self-check. Real network
+ real compute, both mandatory targets with holo ground truth.

Output: `__WORK_IN_PROGRESS__/results_task0092/{KRAS_G12C,BCR_ABL1}/{verdict.json,report.txt}`
(gitignored `results_*/`, TASK-0094's own precedent).

### KRAS_G12C

| Quantity | Value |
|---|---|
| `AUC_apo_Hnew_optimised` | 0.7792 |
| `AUC_holo_Hnew_optimised` | 0.6980 |
| `mean_rho_apo_holo` | 0.7301 |
| `mean_jacc20` | 0.25 |

Winner: `H_new_default`, cutoff=8.0 (both passes agreed).

**Interpretation:** gap is small and in the *unexpected* direction --
holo AUC (0.698) is **lower** than apo AUC (0.779), not higher. Per this
task's (a)/(b) framework, a small gap points to explanation (b)
(propagator/operator is the bottleneck, not apo's information content)
-- but here it points more precisely to "apo's score is not obviously
information-starved relative to holo's own topology fed to the same
operator", which is consistent with (though does not on its own decide)
REVIEW-2026-07-13's P1-A finding that KRAS's 0.779 is substantially a
proximity/geometry artifact: proximity-to-seed structure is present in
both apo and holo topologies alike, so a proximity-dominated score
doesn't necessarily improve when given the "better" (holo) topology.
`mean_rho_apo_holo`=0.73 (moderately high rank agreement) and
`mean_jacc20`=0.25 (modest top-20 overlap) are consistent with "same
general regions light up in both frames," not a sharp holo-specific
localization. **Does not by itself resolve TASK-0093/TASK-0094's
proximity-confound question** -- reported as a data point for that
question, not a substitute for it.

### BCR_ABL1

| Quantity | Value |
|---|---|
| `AUC_apo_Hnew_optimised` (CTQW) | 0.5250 |
| `AUC_holo_Hnew_optimised` (CTQW) | 0.5857 |
| `mean_rho_apo_holo` | 0.9710 |
| `mean_jacc20` | 0.60 |

Winner: `H_new_default`, cutoff=8.0 (both passes agreed).

**Interpretation:** CTQW gap is small (+0.061) and both sides sit near
chance (0.525 apo, 0.586 holo) -- explanation (b): the propagator
itself (CTQW on `H_new`) is the bottleneck, not apo's information
content, since even holo's own topology barely moves the needle through
the same operator. This is independent, real-data corroboration for
REVIEW-2026-07-13c's CTQW-trapping hypothesis (Anderson-like
localization at the seed's first contact shell) -- consistent with, but
not a substitute for, TASK-0106's own dedicated real-data gate.

### Addendum -- `ground_state_relaxation` holo-side AUC for BCR_ABL1

| Quantity | Value |
|---|---|
| `ground_state_relaxation` AUC, apo (`AUC_heat_mean`) | 0.7315 |
| `ground_state_relaxation` AUC, holo | 0.7394 |

Reproduces TASK-0091's apo finding (0.7315) exactly on this fresh run.
Holo and apo GSR AUCs are **very close** (0.7394 vs 0.7315, Δ=0.008) --
per this task's own Addendum caveat, this is the "static artifact"
signature, not the "localization shift toward the pocket upon ligand
binding" signature: if GSR were picking up a real ligand-induced
conformational change, holo (which has the ligand) would be expected to
diverge from apo, not track it this closely, especially compared to
CTQW's own apo/holo gap on the same operator (0.061) which is larger
than GSR's (0.008) despite CTQW being the propagator with markedly
*lower* absolute AUC. **This holo agreement is necessary-but-not-
sufficient corroboration only, per the Addendum's own explicit
instruction** -- it does not independently confirm BCR_ABL1's GSR
finding is a real communication signal rather than a static structural-
prior artifact of `H_new`'s potential-term composition (the same
concern TASK-0102/REVIEW-2026-07-13b's dumbbell negative-control raised
and, per `0b0323d`'s commit message, already found evidence for: GSR
tracks the well, not the coupling). This result is consistent with,
not contradictory to, that finding.

### Failure-explanation summary

| Target | Gap (holo - apo, CTQW) | Explanation |
|---|---|---|
| KRAS_G12C | -0.081 (holo *lower*) | Neither (a) nor (b) cleanly -- apo is not information-starved relative to holo; consistent with a proximity-dominated score present in both frames (P1-A). |
| BCR_ABL1 | +0.061 (small) | (b) -- propagator/operator (CTQW) is the bottleneck, not apo's information content. Real-data corroboration for the CTQW-trapping mechanism (REVIEW-2026-07-13c), pending TASK-0106's dedicated gate. |
