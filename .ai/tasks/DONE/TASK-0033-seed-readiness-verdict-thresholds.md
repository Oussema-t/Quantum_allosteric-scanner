# TASK-0033 Reconcile `quantum_seed_readiness`'s hardcoded verdict thresholds

## Context

- ID: TASK-0033
- Title: commit `89215bc` ("Port corrected §5h/§5i to the SW: data-driven
  seed readiness (no hardcoding)") still leaves fixed constants in the
  final SAFE/PARTIAL/RISKY verdict logic
- Status: Done
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

- [x] Read notebook §5h/§5i, determine what it actually specifies for the
      aggregate verdict thresholds. **Could not be read — see Done**: no
      "5h"/"5i"/§5h/§5i/seed-readiness content exists anywhere in the
      currently-committed `notebooks/H_new_engineering (4) CLEAN.ipynb`,
      and the citing commits (fd6eeed/89215bc, 2026-06-28) predate that
      notebook file's own addition to the repo (2026-06-30/ecd53a8) by 2
      days — the citation is not checkable against any version of the
      notebook this repo has ever held. Resolved via direct code analysis
      + empirical validation instead (Done section).
- [x] Implement whichever of (a)/(b) above the notebook supports.
      **(b)**: added the explanatory comment `backend/analysis.py` itself
      calls for in this branch.
- [x] Re-run against all verified benchmark targets, compare verdicts
      before/after. Identical before/after (comment-only change, no logic
      touched) — see Done for the actual numbers.

## Dependency

- None.

## Open Questions

- None yet — resolves once the notebook is read. **N/A** — see TODO.

## Done

**2026-08-16, Implementer D.** Resolved as **(b): the aggregate verdict
thresholds are correctly, deliberately fixed** — not a hardcoding bug,
and not something to make relative like `deg_lo`/`cpl_lo`/`msf_hi`.

**Why the notebook check (this task's own required first step) could not
be done as specified**: `git log` shows `fd6eeed`/`89215bc` (the commits
that introduced/"corrected" §5h/§5i) are dated 2026-06-28; the notebook
file itself was first added to this repo on 2026-06-30 (`ecd53a8`, and
two apparent duplicate/rebased copies of the identical commit,
`add62d1`/`101cfe3` — same author-date, same 4869-line content, not three
independent edits). The notebook has never been modified since being
added (no other commits touch `notebooks/`). Searched the full, current
notebook (top-level headers, and every cell's raw source) for `"5h"`,
`"5i"`, `"§5"`, `"seed readiness"`, `"seed-readiness"` — zero matches
anywhere. Conclusion: the §5h/§5i citation refers to a notebook state
that was never committed to this repository, not a section that was
later renumbered or deleted from what's here now. Recorded honestly
rather than fabricated or silently skipped.

**Fallback verification actually used** (since the notebook path was a
dead end): direct analysis of what `frac`/`distal_enrich` (the two
quantities the verdict thresholds gate on) actually are, plus empirical
validation against real data, matching the spirit of this task's own
Planned Validation.
- **Code-level**: `deg_lo`/`cpl_lo`/`msf_hi` (already percentile-based)
  gate *raw* per-residue quantities (`deg[i]`, `cpl[i]`, `msf[i]`) whose
  absolute scale is protein-size-dependent — an 88-mer's raw contact
  degree isn't comparable to a 950-mer's, so percentile derivation is
  necessary there. `frac` and `distal_enrich` are different in kind:
  `frac` is already a fraction in [0, 1] by construction (n_good/n_total);
  `distal_enrich` is already a ratio to *this protein's own* computed
  uniform-spread baseline (the code's own pre-existing comment: "replaces
  hard-coded 0.05/0.15 cutoffs — works for an 88-mer or a 950-mer alike").
  Both are scale-invariant *before* any threshold is applied — a fixed
  cutoff on an already-normalized quantity is the correct design, the
  same category of choice as e.g. "AUC >= 0.7 is good" being a legitimate
  fixed bar despite AUC itself being computed differently per dataset.
- **Empirical**: ran `quantum_seed_readiness` directly (`.venv`, real
  RCSB fetches via `backend/data_layer.py`, no synthetic stand-in) on all
  5 `verified=True` `systems.py` targets:

  | target | N | n_seed | verdict | frac_good | distal_enrich |
  |---|---|---|---|---|---|
  | KRAS_G12C | 169 | 22 | PARTIAL | 0.360 | 0.941 |
  | BCR_ABL1 | 451 | 18 | PARTIAL | 0.440 | 0.819 |
  | CARDIAC_MYOSIN | 950 | 16 | PARTIAL | 0.940 | 0.895 |
  | PTP1B | 298 | 9 | RISKY | 0.000 | 0.775 |
  | GLUCOKINASE | 448 | 28 | PARTIAL | 0.540 | 0.948 |

  Across a 5.6x range in N (169-950), neither `frac_good` nor
  `distal_enrich` shows a monotonic or otherwise N-driven trend (the
  largest target, CARDIAC_MYOSIN, has the *highest* frac_good, not the
  lowest) — no empirical evidence a fixed threshold introduces a
  size bias. Re-ran identically after the comment-only fix: same 5
  results, byte-for-byte (expected — no logic changed).

  **Aside, out of scope, flagged not fixed**: `GLUCOKINASE`'s row above
  used `chain="A"`, not `systems.py`'s configured `chain="X"` — apo 1V4S
  only has chain A (confirmed directly against the fetched structure).
  This is the same apo/holo chain-letter mismatch
  `__WORK_IN_PROGRESS__/src/allostery/clean.py`'s `clean_from_config`
  already fixed for its own tree (TASK-0127: "GLUCOKINASE: apo 1V4S is
  chain A, holo 3H1V is chain X") — this live backend's `systems.py`
  still has the old, wrong single `chain` field and would currently fail
  to load GLUCOKINASE's apo structure at all in production. Not this
  task's scope (verdict-threshold contract, not target config
  correctness) — recorded here so it isn't lost, not filed as a new task
  without the user's steer.

  **Aside #2, also flagged not fixed**: none of the 5 real verified
  targets reach the `SAFE` verdict (all PARTIAL except PTP1B's RISKY) —
  `SAFE` requires `frac >= 0.60 AND distal_enrich >= 1.2` jointly, a
  fairly stringent AND condition against this real data's actual range.
  Not evidence the thresholds are wrong (this task's scope is the
  relative-vs-fixed *contract*, not re-calibrating the cutoff values
  themselves) but worth knowing before anyone is surprised `SAFE` never
  fires on the current benchmark set.

**Fix**: `backend/analysis.py`, added a comment directly above the
verdict-threshold block explaining why `frac`/`distal_enrich`'s cutoffs
are deliberately fixed unlike the three percentile-based flags above
them, citing both the code-level reasoning and this task's own empirical
check — so a future reader doesn't re-flag this the way the original
2026-07-05 review did. No production logic changed; `CLAUDE.md`
convention 4's constraint (response shape/field names for
`/api/connectivity-change` must stay identical) is trivially satisfied.

**Tests**: `backend/test_analysis.py` (31 tests, includes live-KRAS_G12C
regression) and `test_golden_value_cross_tree_drift.py` (11 tests,
cross-checks `backend/analysis.py`'s shared math against
`__WORK_IN_PROGRESS__/src/allostery/potentials.py`'s independently-ported
copy) both re-run clean after the change — 42/42 passing, 0 failed.

Artifacts: `backend/analysis.py` (comment only).
