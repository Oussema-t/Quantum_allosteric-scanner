# TASK-0229 The challenge's own bibliography — seven untested hypotheses (parent)

## Context

- ID: TASK-0229 (parent; subtasks .001–.007)
- Status: Done
- Owner: Architect/Planner (parent), Implementer (subtasks)
- Source: `.claude/hypotheses/reference_register.md` — systematic extraction of
  testable hypotheses from the Challenge Statement's own references [1]–[25],
  produced by the 2026-08-21 external session and **moved into the hypotheses
  home on filing** (it was left in a reviews folder and never integrated).
- Priority: **mixed and stated per subtask** — three are submission-critical,
  four are Phase-2 forward material. Do not treat the family as one block.

## Why this exists

The register is the first systematic pass over the organisers' own
bibliography, and it found that **the challenge cites references whose claims
attack our results**, several of which we had never registered as hypotheses
at all. Two facts make this urgent rather than academic:

1. **Ref [9] (Gunasekaran) attacks the negative class of every AUC in the
   program.** If there is no clean class of non-allosteric surface sites, then
   matched-decoy nulls and all ROC framing rest on an unsound premise — and a
   chance-level AUC stops being evidence of no signal. This is *mandatory in
   the limitations section whether or not it is ever tested.*
2. **Ref [1] (Zheng, NMA-guided conformational sampling) is reference number
   one, is MD-free, is the canonical method for this program's own reframing —
   and has never been implemented as a baseline.** A reviewer who checks the
   bibliography will notice.

The register also contradicts itself against our repo in one place that must
be settled before either number is written down: its `GNM_corr_low10` stayed
proximity-confounded at 0.870 where our register reports `prs_low` collapsing
to ≈0.08. Different observables, so not a formal conflict — but load-bearing.
Owned by [[TASK-0226]].

## Standing caveat, inherited

Every measured number in the source register was produced **on bundled
non-target structures without rcsb.org access**. Nothing from it may be cited
in the submission before a PDB-retest on real challenge targets. Subtasks
carry this individually.

## Subtasks

| ID | Hypothesis | Ref | Why | Priority |
|---|---|---|---|---|
| **.001** | Negative-class validity + metric change | [9] | Attacks every AUC's negative class. Limitations text is **mandatory**; adds rank-of-known-site and enrichment-at-k, which degrade gracefully under a contaminated negative class | **P0 — submission** |
| **.002** | Quantum hardware story: circuit cutting + SVD dilation | [10],[11] | Paper-level only, cheap, and discharges the coarse-graining half of objective §4.2 plus the missing ENAQT implementation route | **P0 — submission** |
| **.003** | ASD multi-site answer-key audit | [6],[25] | Allosteric sites are effector-specific; a single ground-truth pocket per target may make genuine sites count as false positives | **P1 — may correct our own FP rate** |
| **.004** | Zheng NMA-guided sampling as a scored baseline | [1] | The challenge's own reference #1, MD-free, never implemented. If it outperforms our quantum arm, that is a finding we must report ourselves | **P1 — forward proposal** |
| **.005** | NMA sampling → persistent homology → pocket ranking | [1]+[2] | The register's own "highest-value construction". Zero MD, both halves from the organisers' bibliography. Revives the H₂ arm, which [[TASK-0143]]'s 0/7 did not kill (bad proxy) | **P1 — forward proposal** |
| **.006** | Ensemble Allosteric Model (COREX-style) | [4] | The genuine nonlinear EAM is untested; the harmonic proxy is already confounded (0.773). **Type-correct quantum target** — partition-function estimation, not propagation. Only route to c-Myc via H4.3 | **P1 — forward proposal** |
| **.007** | Two-state ANM; non-equilibrium impulse response | [15],[7] | [15] is the principled instrument to **quantify** [[TASK-0209]]'s 2/7 rather than assert it. [7] notes the entire pipeline is equilibrium; ENM impulse response is closed-form and MD-free | **P2** |

## Constraints And Invariants

- **.006 must not claim advantage.** Quantum speedups for classical partition
  functions are at best quadratic and conditional. Claim *type-correctness*
  only — the register says so explicitly and it is right.
- **.004's honest outcome may be that a 2023 classical method beats us.**
  Report it either way; we already do this with fpocket.
- Every subtask that produces a number states whether it ran on real challenge
  targets or on the drop's non-target structures.

## Dependency

- [[TASK-0226]] settles the `GNM_corr_low10` / `prs_low` conflict.
- .001 and .002 feed [[TASK-0184]] directly.
- .004/.005/.006 feed [[TASK-0184]]'s forward-proposal section and [[TASK-0183]].

## Done

**2026-08-24, Architect (closing synthesis).** All 7 subtasks Done
(`.001`–`.007`, 2026-08-21 through 2026-08-23); this parent itself was
never formally closed until now — picked up on direct user instruction
after an audit found the family's own subtasks solid but two of its own
Dependency commitments unfulfilled.

**What the family found, in one place**: 3 real classical baselines beat
this project's own quantum observable on real targets (Zheng NMA
sampling, `.004`; the harmonic ensemble-coupling proxy stayed confounded,
`.001`'s negative-class audit); 2 forward-proposal constructions failed
their own cheapest gates decisively (NMA+persistent-homology, `.005`;
the genuine nonlinear EAM gave a real mixed result instead of a clean
failure, `.006`); 1 real database-completeness gap found and bounded
(`.003`'s BCR_ABL1 second site, correction to the top-5 hit list: zero);
2 hardware-story citations checked against this register's own resource
numbers (`.002` — circuit cutting reinforces `FAULT_TOLERANT_ONLY`,
SVD/dilation is the one route that clears the qubit-count bar under an
unbuilt encoding); 1 principled instrument built to quantify (not just
assert) [[TASK-0209]]'s own 2/7 finding, with an honest non-generalizing
result (`.007`). [[TASK-0226]] separately resolved the family's own
internal `GNM_corr_low10`/`prs_low` discrepancy (different observables,
not a real conflict, confirmed on real PDB data).

**Audit found before this closing, now fixed**: the parent's own
Dependency line ("`.004`/`.005`/`.006` feed [[TASK-0184]]'s
forward-proposal section and [[TASK-0183]]") was only half true.
`.004`/`.005` reached `PHASE1_SUBMISSION_DRAFT.md` (Findings 5/6) but
`.006` never did, and **none of the three reached
`documentation/POC_SPRINT_PLAN.md`, which had already shipped and
closed** ([[TASK-0183]], Done 2026-08-17) before `.006` even ran
(2026-08-23). Closed today, honestly dated as a post-closing addition in
both documents, not a silent backfill: new Finding 7 + a §3(d)
cross-reference in `PHASE1_SUBMISSION_DRAFT.md`, a dated addendum
section in `POC_SPRINT_PLAN.md` (named as a candidate, not folded into
any already-committed milestone), and `RESULTS.md` row 81 (`.001`/`.002`/
`.004`/`.005` already had rows 76-79; `.006` did not, until now).

**Not chased further, flagged rather than silently closed**: `.003`'s
own residual gap (a full whole-protein re-score against the ASD union
key, beyond the top-5 check actually run) and `.007`'s own (GLUCOKINASE
as an unexplained counterexample to the pocket-restricted two-state-ANM
instrument) are each already honestly recorded in their own Done
sections — not re-opened here, since neither was named in this parent's
own Dependency as something owed to another document.

Full detail: each subtask's own Done section; `RESULTS.md` rows 76-81.
