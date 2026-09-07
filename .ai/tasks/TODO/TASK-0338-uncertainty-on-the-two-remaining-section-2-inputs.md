# TASK-0338 — Put error bars on TASK-0336, and make TASK-0318's 0.6017 regenerable

- Status: TODO
- Owner: **Implementer B**
- Priority: High — both feed [[TASK-0332]]'s §2 and one feeds its exclusion argument
- Filed: 2026-09-07 by Reviewer thread (id via `claim.py reserve-next`)
- Source: `.ai/reviews/2026-09-07/...adversarial-submission-audit.md` §3.3, §3.4
- Related: [[TASK-0336]], [[TASK-0318]], [[TASK-0332]], [[TASK-0333]]

## Part A — [[TASK-0336]]'s "classical beats CTQW" is a one-family difference

From `matched_comparison_result.json`: CTQW **4 / 276** families, fpocket_drug /
passer_rank / pocket_size **5 / 276**, chance 1.25 for all. `real_excess` is a
bare `obs - chance` subtraction — **no variance, no CI, no p-value anywhere in
the script or output.** On counts this small the Poisson sd on the observed term
alone is ≈2, so +2.75 and +3.75 are indistinguishable by any test.

**The honest reading, which is also the stronger submission sentence**: under
matched multiplicity, a matched candidate set and a matched null, *no arm —
quantum or classical — clears more than 5 of 276 families, and the arms are
statistically indistinguishable from each other and barely distinguishable from
chance.*

This matters beyond the task: [[TASK-0332]]'s brief update currently excludes the
v2 pipeline results **for the wrong stated reason** ("three classical descriptors
beat the CTQW"). The right reason is the one [[TASK-0336]] genuinely owns —
best-of-221-cells selection does not survive multiplicity matching, 69 families
→ 4. Exclude on the methodology, which is unassailable, not on a difference of
one family, which a referee can turn around.

- Outcome: bootstrap or Poisson CIs on every arm's family count; the brief's
  exclusion sentence rewritten to the methodological argument.
- Secondary, same artifact: `degree` and `proximity(-hop)` emit `"ALL":
  {"n_families": 48}` where 48 is the **distal** count and `"near": 0`. Those two
  arms were distal-only — disclosed in the script docstring, but the JSON is what
  others read. Rename the key to `distal_only` or emit `null`.
- Also state, wherever the ALL row is cited: **proximity — the baseline this
  whole register is organised around — is missing from the ALL comparison.**

## Part B — [[TASK-0318]]'s 0.6017 exists but cannot be regenerated

**Correcting the review on this one.** It reported
`no_proximity_feature_check.json` as absent; it **is present and committed**
(`__WORK_IN_PROGRESS__/results/tasks/0318_input_space_ceiling/`). The review
worked from a snapshot that predated it.

The defect that *does* stand: **no script produces it.** `scripts/` holds only
`task0318_input_space_ceiling.py` (flags: `--phase-b-only`) and
`task0318_negative_control.py` — neither has a proximity-exclusion path. So the
number doing the most argumentative work in §2 — the one converting "a
high-capacity model just reconstructs proximity" from an open objection into a
closed one — is a committed JSON with no executable provenance.

- Outcome: add `--exclude-proximity` to the existing Phase B (~10 lines), run it
  against the committed cache, and confirm it **reproduces the committed JSON**.
  ~2 minutes of compute.
- If it does not reproduce, that is a finding and the number comes out of the
  draft until it is explained.
- Planned Validation: byte-compare against the existing artifact, do not eyeball.
