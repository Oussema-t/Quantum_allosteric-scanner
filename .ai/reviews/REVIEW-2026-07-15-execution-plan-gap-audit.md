# Execution Plan Gap Audit — parameter sweeps, proof of validity

## Reviewer

Architect/Planner thread (Critic overlay, per direct user request: "read through
EXECUTION_PLAN.md and recently delivered TASKs with a CRITIC hat on... discover
gaps... parameter sweeps? proof of validity?"), 2026-07-15. Evidence-first: read
`EXECUTION_PLAN.md` in full, `SEAM-0004`/`SEAM-0008`, and verified claims against
real code (`metrics.py`, `analysis.py`, `RESULTS.md`) rather than trusting the
plan's own status table.

## Linked Docs

- `__WORK_IN_PROGRESS__/EXECUTION_PLAN.md` (Phases 0–7, full)
- `__WORK_IN_PROGRESS__/RESULTS.md`
- `.ai/seams/SEAM-0004-optimised-auc-freeze-provenance.md`,
  `.ai/seams/SEAM-0008-analysis-report-schema-assembly.md`

## Scope

Not a code review of any one module — a plan-level audit asking what claims of
validity the submission currently rests on that have no corresponding sweep,
check, or uncertainty measure anywhere in the repo.

## Method

1. Read `EXECUTION_PLAN.md` end to end, including all four same-day correction
   banners (07-13, 07-13b/c) — the plan already retracts/re-scopes itself
   repeatedly, which is a good sign, but each correction was qualitative
   (right/wrong mechanism), never quantitative (is a margin real or noise).
2. For every TODO row still open, cross-checked whether it blocks a claim
   currently stated as settled elsewhere in the plan or in `RESULTS.md`.
3. Grepped the actual code for mechanisms the plan's prose implies exist
   (uncertainty quantification, cutoff sensitivity) rather than assuming the
   prose is current.

## Findings

### Already tracked, still open — re-confirmed as real blockers, not stale

| Task | Gap | Severity |
|---|---|---|
| TASK-0108/0109/0110 | CTQW numerical params (`t_max=15`, `n_steps=500`) never validity-checked; same fixed values used on 169/451/950-residue systems | Critical |
| TASK-0054 | SE(3) rotation/translation invariance never regression-tested on real code | Critical |
| TASK-0075 | Overlap gate flips go/no-go in 15/18 knob combos (0.067–0.860 spread) | High |
| TASK-0105 | ENAQT γ-sweep — "highest scientific upside" per `REVIEW-2026-07-13c` — unswept | High |
| TASK-0106 | CTQW-trapping real-data reproduction gate, blocks 1B.5 | High |
| TASK-0102 | Seed-dependence of GSR's ground-state minimum unresolved — undermines the one retained headline number (BCR_ABL1 0.7315) | High |
| TASK-0072 | Cross-tree drift *prevention* (golden values) not built — only the one-time 8.0/10.0 Å reconciliation happened | Medium |
| TASK-0081 | Generalization set (ASD targets) not run — zero evidence any result generalizes past the 3 mandatory targets | High |
| TASK-0021 / 4.3 | Backend test floor thin — deployed submission-facing app largely unprotected | Medium |

### New — not tracked anywhere before this pass

1. **No uncertainty quantification on any reported AUC.** `metrics.py:36`
   (`block_bootstrap_ci`) is implemented and used by `select.py`'s LOPO path,
   but never called from `analysis.py`'s headline scoring, `report.py`, or
   anywhere `RESULTS.md`'s numbers originate — grep for
   `ci|bootstrap|±|confidence` in `RESULTS.md` returns zero hits. Every
   floor-vs-score comparison currently treated as decided (KRAS 0.779 vs.
   floor 0.798 — the finding that overturned the original headline result;
   BCR_ABL1 CTQW 0.525 vs. floor 0.565; GSR 0.7315 vs. floor 0.565) is a bare
   point estimate on N≈20–100 pocket residues, N=3 proteins. Filed as
   **TASK-0112**.
2. **TASK-0067's cutoff sweep validated the wrong operator.**
   `analysis.py::gnm_cutoff_weight_sweep` (line 420) scores a bare
   contact-Laplacian via `ground_state_relaxation`, not `H_new` (five
   potential terms) and not `time_averaged_ctqw` — the two functions that
   actually produce every headline AUC. The sweep's own docstring justifies
   this narrowly ("comparing operator construction, not propagator choice"),
   but the plan's progress tracker records "8.0 Å confirmed fine" as if it
   covered the operator the submission reports. It doesn't. Filed as
   **TASK-0113**.
3. **Pocket-label ligand-contact cutoff (4.5 Å) has no sensitivity sweep.**
   Distinct from the GNM graph cutoff TASK-0067 covers — this cutoff defines
   ground truth itself (`holo_pocket_mask`). No task anywhere checks whether
   4.0/5.0 Å would flip enough residues to move a headline AUC across a floor
   threshold, the same failure mode TASK-0075 already proved exists in the
   overlap gate. Filed as **TASK-0114**.
4. **Meta-level repeated-exposure risk across the review cycle itself.**
   TASK-0100/`frozen_context`/LOPO gate *code-level* parameter and operator
   selection against true labels. They do not, and cannot, gate the ~15 human
   review cycles this project has already run, each looking at the same 3
   targets' real AUCs before deciding what to rename, re-scope, or re-frame
   (`heat`→`ground_state_relaxation`, the floor definition, SEAM-0008's
   reassignment, the GSR causal-claim correction). Individually each decision
   is well-evidenced; collectively this is researcher-degrees-of-freedom
   exposure on a 3-point answer key that no existing protocol document
   accounts for, because `INVARIANCE_PROTOCOL.md`/`SEAM_PROTOCOL.md` both
   operate at the code/data level, not the review-history level. The
   practical mitigation already exists in the plan (TASK-0081's generalization
   set) but nothing currently states that no `RESULTS.md` claim should be
   treated as final until checked against targets none of this review history
   has seen. Filed as **TASK-0115**.

## Notable good practice observed

- Phase 1B's self-correction discipline (07-13 → 07-13b → 07-13c) is a real,
  unusual asset: the plan caught its own proximity confound, then caught its
  own causal misattribution on top of that, each time via a decisive
  controlled experiment rather than argument. TASK-0112 extends the same
  standard to the one place it hasn't reached yet: whether the margins in
  those very corrections are themselves statistically distinguishable from
  noise.
- `TASK-0103`'s dumbbell negative-control harness (`build_dumbbell_network`,
  public) is exactly the kind of reusable synthetic-falsification tool
  TASK-0114 (pocket-label cutoff sensitivity) can build on rather than
  inventing a second synthetic-network helper.

## Status

No P0/P1 code defects — this is a plan-level audit, not a code review. Nine
already-filed tasks reconfirmed as genuine open blockers (none stale). Four
new tasks filed (TASK-0112–0115) for gaps with no prior task coverage,
ranked Critical (0112) down to High (0115). Recommend TASK-0112 gate Phase
5.2 (competence map synthesis) explicitly, alongside Phase 1B — a
floor-vs-score margin without a confidence interval is not yet a settled
verdict.
