# TASK-0104 Re-frame GSR/BCR_ABL1 claim in RESULTS.md and the methodological report

## Context

- ID: TASK-0104
- Title: Change the claim attached to BCR_ABL1's `ground_state_relaxation`
  (GSR) AUC=0.731 finding from "allosteric signal propagation" to "an
  apo-computable structural prior for cryptic/soft pockets," per
  `REVIEW-2026-07-13b`'s falsification evidence. **The number does not
  change; the claim attached to it does.**
- Status: TODO
- Owner: Implementer (documentation-only; no code/analysis change)
- Claimed By: —
- Claimed At: —
- Source: `REVIEW-2026-07-13b`, §7 Tier 1, item **T-B** — "cheap, and it
  stops a false claim entering the submission."
- Crit Ref: directly revises [[TASK-0091]]'s Done conclusion. TASK-0091's
  own numbers (floor-clearing margin, hit-list diffuseness) are **not**
  wrong and do not need to change — only the causal claim attached to them
  does. Read TASK-0091's Done section and this review together, not either
  alone.

## Intent Contract

- Outcome: `RESULTS.md` (and any methodological-report draft referencing
  the BCR_ABL1 GSR finding) states the corrected claim from the review's
  §3: *"Allosteric pockets tend to coincide with soft, low-coordination
  regions. This is an apo-computable structural prior, detectable without
  reference to the active site"* — explicitly framed as a cryptic-pocket-
  detection finding, addressing a different challenge objective than
  signal propagation, not folded into the same narrative as the CTQW/
  ENAQT communication story.
- In Scope:
  - locate every place `RESULTS.md` (and the in-progress methodological
    report, if one exists as a file) currently frames GSR=0.731 as
    evidence of allosteric communication or signal propagation
  - rewrite to the corrected claim, citing the review's falsification
    evidence (the 2×2 control matrix, [[TASK-0103]] once it lands) as the
    basis for the correction — don't silently change the claim without a
    citable reason a future reader can check
  - remove the "classical heat vs. quantum CTQW" framing tied to this
    number specifically (review §3: "this comparison remains void... it
    was never a classical/quantum comparison")
  - preserve TASK-0091's own hit-list-diffuseness finding (0/5 top hits
    despite the good AUC) — that finding is orthogonal to the causal
    re-framing and remains correct and worth keeping
- Out Of Scope:
  - re-running any analysis — the AUC number itself does not change
  - the ENAQT experiment ([[TASK-0106]]) or the new operator
    ([[TASK-0105]]-range) — separate tasks
  - KRAS_G12C's own AUC discrepancy ([[TASK-0093]]) — a different target,
    different operator (CTQW, not GSR), tracked separately
- Constraints And Invariants:
  - do not retract the number — the review is explicit: "The number is
    real; the *claim* attached to it was wrong."
  - cite the falsification evidence, don't just assert the new framing
    — a reader should be able to see *why* the claim changed.
- Planned Validation: not code — validation is "does every GSR/BCR_ABL1
  mention in `RESULTS.md` now match the review's corrected claim," checked
  by direct re-read, not assumed.

## In Progress

None

## TODO

- [ ] Grep `RESULTS.md` for every GSR/BCR_ABL1/0.731 mention.
- [ ] Rewrite each to the corrected structural-prior claim, citing
      `REVIEW-2026-07-13b` and [[TASK-0103]].
- [ ] Remove/correct the classical-vs-quantum framing tied to this number.
- [ ] Confirm the hit-list-diffuseness finding (TASK-0091) is preserved,
      not deleted along with the causal claim.

## Dependency

- [[TASK-0091]] (Done) — the finding being re-framed, read together with
  this task, not superseded by it.
- [[TASK-0103]] — ideally lands first or alongside, so this task's
  citation of the falsification evidence points at a real, passing test,
  not just the review document alone.

## Open Questions

- Does a "methodological report" file exist yet as a committed artifact,
  or only `RESULTS.md`? Check at execution time — the Intent Contract
  covers whichever files currently exist making this claim.

## Done

(not yet)
