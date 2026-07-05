# TASK-0033 Reconcile `quantum_seed_readiness`'s hardcoded verdict thresholds

## Context

- ID: TASK-0033
- Title: commit `89215bc` ("Port corrected §5h/§5i to the SW: data-driven
  seed readiness (no hardcoding)") still leaves fixed constants in the
  final SAFE/PARTIAL/RISKY verdict logic
- Status: TODO
- Owner: Implementer
- Source: review of all `Oussema-t`-authored commits, 2026-07-05 session —
  Medium-severity finding #3 (the one clear intent-vs-implementation
  mismatch found in the review)
- Scope: `backend/analysis.py::quantum_seed_readiness`, lines building the
  `verdict` (`frac < 0.34`, `frac >= 0.60`, `distal_enrich >= 1.2 / 0.5`)

## ⚠️ Before implementing

**Do a short review before changing anything.** This may not actually be a
bug — it's possible the notebook's §5h/§5i source deliberately fixes these
aggregate cutoffs while only the per-residue flags (`deg_lo`, `cpl_lo`,
`msf_hi` — already percentile-based) are meant to be relative. Check the
notebook (`notebooks/H_new_engineering (4) CLEAN.ipynb`) for what §5h/§5i
actually specifies before assuming the commit's "no hardcoding" claim is
wrong rather than just imprecisely worded.

## Intent Contract

- Outcome: either (a) the verdict thresholds become relative/derived the
  same way the per-residue flags already are, matching the commit's stated
  intent, or (b) the notebook confirms these are intentionally fixed
  constants and the commit message / a code comment is corrected instead
  — record whichever is true, don't just pick one and implement.
- In Scope:
  - read notebook §5h/§5i for the source specification of these
    thresholds.
  - if they're meant to be relative: derive them the same way `deg_lo`/
    `cpl_lo`/`msf_hi` are (percentile-based on the protein's own
    distribution), re-validate the SAFE/PARTIAL/RISKY verdict on the
    existing benchmark targets to confirm no regression in the case this
    feature already handles correctly.
  - if they're meant to be fixed: add a one-line comment explaining why
    (e.g. "aggregate verdict cutoffs are deliberately fixed calibration
    constants, unlike the per-residue percentile flags above") so a future
    reader doesn't re-flag this.
- Out Of Scope: redesigning the seed-readiness feature itself.
- Constraints And Invariants: CLAUDE.md convention 4 — don't change the
  `/api/connectivity-change` response shape; if the verdict logic changes,
  the field names (`verdict`, `frac_good`, `distal_enrich`, etc.) must stay
  the same.
- Planned Validation: run `quantum_seed_readiness` against every verified
  benchmark target in `systems.py` before and after, confirm the verdict
  for each either stays the same or the change is deliberate and
  explainable (not a silent behavior shift on live-app targets).

## TODO

- [ ] Read notebook §5h/§5i, determine what it actually specifies for the
      aggregate verdict thresholds.
- [ ] Implement whichever of (a)/(b) above the notebook supports.
- [ ] Re-run against all verified benchmark targets, compare verdicts
      before/after.

## Dependency

- None.

## Open Questions

- None yet — resolves once the notebook is read.

## Done

(not yet)
