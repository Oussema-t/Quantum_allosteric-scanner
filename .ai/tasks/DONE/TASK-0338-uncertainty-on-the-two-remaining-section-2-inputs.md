# TASK-0338 — Put error bars on TASK-0336, and make TASK-0318's 0.6017 regenerable

- Status: DONE
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

## Done, 2026-09-07

### Part A

Added to `matched_comparison.py` (reused the per-structure null draws already
computed by the script — no re-run of the Monte Carlo null needed):

- `poisson_ci(k)` — exact (Garwood 1936) two-sided Poisson 95% CI via the
  chi-squared/Poisson duality, the same closed form R's `poisson.test` and
  scipy's own docs use for exact Poisson intervals. Appropriate here because
  each arm's family-clearing count is a rare-event count out of a large
  family pool (4-5 / 276, <2%), where the Poisson approximation to the
  underlying binomial is standard and conservative. Attached as
  `poisson_ci95` on every arm/split in `family_table`.
- A paired exact test (McNemar, via `scipy.stats.binomtest` on the
  discordant families), not a second independent-sample comparison — every
  arm is scored on the identical 276 families, so this is the statistically
  correct test, and cheaper/cleaner than deriving a joint null distribution
  from the existing per-structure Monte Carlo draws.

Result (`ALL` split, all pairs CTQW × classical):

| comparison | CTQW-only clears | classical-only clears | McNemar exact p |
|---|---|---|---|
| every CTQW cell × every classical arm (6 pairs) | 0 | 1 | **1.0** |

Poisson 95% CIs: CTQW `[1.09, 10.24]`, classical (fpocket_drug/passer_rank/
pocket_size) `[1.62, 11.67]` — heavily overlapping. **Confirms the filing's
own hypothesis exactly**: 4 vs 5 of 276 is not a real gap. [[HYP-P13]]'s own
Status was updated with this correction (2026-09-07) rather than left
standing on the bare 4-vs-5 framing. [[TASK-0332]]'s draft exclusion
sentence was rewritten to the methodological argument (multiplicity, not a
one-family scoreboard loss) — see its own "Brief update" section.

Secondary fix, same artifact: `degree` and `proximity(-hop)` (refetch-scoped
to the 80 distal structures only, by design — see the script's own
`classical_pocket_order_refetch` docstring) emitted `"ALL"` duplicating
`"distal"`'s own 48-family count under a key that reads as full-cohort
coverage. Renamed to `"distal_only"` for those two arms; every other arm's
real `"ALL"` is unchanged. Checked every outward-facing doc
(`RESULTS.md`, `physics.md`, `TASK-0332.md`, `PHASE1_SUBMISSION_V1.md`) for
an existing citation of the mislabeled row — none found, so the disclosure
requirement ("state wherever the ALL row is cited that proximity is missing
from it") is closed by the rename alone; nothing to retrofit.

**Validation**: `validation_cell_reproduction` and
`validation_family_aggregation` (the script's own pre-existing Planned
Validation, re-run) still pass exactly; every original `n_families`/
`observed_clearing`/`chance_expected_clearing`/`real_excess` value in the
regenerated `matched_comparison_result.json` is byte-identical to the
pre-edit file (checked field-by-field, not eyeballed) — the additions are
strictly new fields, no existing number changed.

### Part B

Added `--exclude-proximity` to `task0318_input_space_ceiling.py`: drops
`hop_prox`/`euclid_prox` (2 of the 19 existing features — the two that ARE
proximity) from the LOPO design matrix before the `HistGradientBoosting`
fit; the residualisation self-checks and the CTQW/TASK-0310 cross-check are
untouched (they read `r["hop"]`/`r["euclid"]`/`r["X"][:, ctqw_idx]`
directly from the cache, not from the reduced design matrix). Ran
`--phase-b-only --exclude-proximity` against the existing committed feature
cache (105 structures, no PDB refetch, ~2 min):

```
n=105  raw_mean=0.6487  raw_median=0.6907
       resid_mean=0.6017  resid_median=0.6321  wilcoxon_p=2.33e-07
```

Byte-compared against the committed `no_proximity_feature_check.json`:
**identical**, field for field (`kept_features`, `n`, `raw_mean`,
`raw_median`, `resid_mean`, `resid_median`, `wilcoxon_p`). The 0.6017 number
is now regenerable, not just committed. Default `--phase-b-only` (no
`--exclude-proximity`) was also re-run to confirm `ceiling_result.json` is
byte-identical to its pre-edit content — ADD-only, the existing path was
not touched.

One bug found and fixed while wiring the flag: the feature-importance
report zipped `imp` (length = number of *kept* features, 17 under
`--exclude-proximity`) against the full 19-item `FEATURE_NAMES` — silent
positional mislabeling had it shipped uncaught. Fixed to zip against
`kept_features` in both the printed table and the JSON output; harmless
under the default (no-flag) path since `kept_features == FEATURE_NAMES`
there, confirmed by the byte-identical `ceiling_result.json` re-run above.

**Constraints honored**: no PDB refetch (cache-only run, per the task's own
~2-minute budget); no change to `ceiling_result.json`'s path or content
(ADD-only); byte-compared, not eyeballed, per the task's own Planned
Validation.

**Files**:
`__WORK_IN_PROGRESS__/scripts/task0318_input_space_ceiling.py`,
`__WORK_IN_PROGRESS__/results/tasks/0336_matched_multiplicity_classical_comparison/{matched_comparison.py,matched_comparison_result.json}`,
`.claude/hypotheses/{physics.md,INDEX.md,TASK_CLASSIFICATION_LEDGER.md}`,
`.ai/tasks/TODO/TASK-0332-submission-v2-corrections.md` (targeted
correction to its staged "Brief update" text, not a full execution of that
task — still owned by Reviewer thread → Berke → repo owner),
`__WORK_IN_PROGRESS__/RESULTS.md`.

No missing or unclear paper references found in this task — Part A's
Poisson-CI and McNemar-test citations are standard closed-form statistical
methods (Garwood 1936; McNemar 1947), not literature claims this register's
`PAPER_CITATION_PROTOCOL.md` live-verification applies to.
