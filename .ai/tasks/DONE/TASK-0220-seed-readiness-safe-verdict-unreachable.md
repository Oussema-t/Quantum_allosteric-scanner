# TASK-0220 `quantum_seed_readiness`'s SAFE verdict never fires on real benchmark data

## Context

- ID: TASK-0220
- Title: across all 5 currently-loadable `verified=True` `systems.py`
  targets, `quantum_seed_readiness`'s verdict is never `SAFE` (4x
  `PARTIAL`, 1x `RISKY`) — is the `SAFE` threshold combination
  (`frac >= 0.60 AND distal_enrich >= 1.2`) miscalibrated against real
  protein data, or is `PARTIAL` actually the honest, correct answer for
  every real target checked so far?
- Status: Done
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: observed incidentally while validating [[TASK-0033]] (which
  confirmed the threshold *values* are deliberately fixed constants, not
  a hardcoding bug — this task is about whether those specific values,
  0.34/0.60 on `frac` and 0.5/1.2 on `distal_enrich`, are well-calibrated,
  a distinct question TASK-0033 explicitly did not investigate, per its
  own Out Of Scope), 2026-08-16.
- Priority: **P2** — not a correctness bug (nothing crashes, nothing
  returns a wrong shape), but a real risk that the `SAFE` verdict is
  either unreachable in practice (dead code path, misleading to a user
  who might infer "unlikely to occur" incorrectly as "cannot occur, don't
  worry about the UI for it") or the calibration is simply off for this
  benchmark set specifically.

## The numbers that motivated this (from TASK-0033's own validation run)

| target | N | verdict | frac_good | distal_enrich |
|---|---|---|---|---|
| KRAS_G12C | 169 | PARTIAL | 0.360 | 0.941 |
| BCR_ABL1 | 451 | PARTIAL | 0.440 | 0.819 |
| CARDIAC_MYOSIN | 950 | PARTIAL | 0.940 | 0.895 |
| PTP1B | 298 | RISKY | 0.000 | 0.775 |
| GLUCOKINASE (chain=A, see [[TASK-0219]]) | 448 | PARTIAL | 0.540 | 0.948 |

Note `distal_enrich` sits in a tight 0.775-0.948 band on every single
target — never once above the 1.2 `SAFE` bar, despite `frac_good` alone
clearing 0.60 on CARDIAC_MYOSIN (0.940). `SAFE` requires *both*
conditions jointly, so CARDIAC_MYOSIN still lands `PARTIAL` on
`distal_enrich` alone. Whether `distal_enrich >= 1.2` is even achievable
on a real elastic-network-based transfer matrix (as opposed to a
theoretical/synthetic case that concentrates unusually hard on distal
residues) is exactly the open question here.

## Intent Contract

- Outcome: a stated, evidence-based answer to whether `SAFE`'s threshold
  combination is reachable and well-calibrated on real protein data, and
  either (a) recalibrated thresholds with a stated derivation/rationale,
  or (b) confirmation that `PARTIAL`-as-the-real-ceiling is correct and
  expected, with a code comment/doc note saying so (mirroring
  [[TASK-0033]]'s own "explain, don't silently leave surprising" pattern)
  so a future reader doesn't mistake this for a live bug.
- Why required, not assumed: TASK-0033 confirmed the threshold *contract*
  (fixed vs. relative) is correct; it did not check whether the specific
  fixed *values* are calibrated against real data — genuinely open.
- In Scope:
  - Extend the 5-target sample (this task's own motivating table) to
    every currently-loadable target in `systems.py` (fix or work around
    [[TASK-0219]]'s GLUCOKINASE chain issue as needed to include it
    cleanly), and to `verified=False` targets too if that doesn't
    meaningfully change scope.
  - Characterize `distal_enrich`'s real achievable range: what would a
    genuinely "SAFE" active site's transfer-matrix distal-concentration
    look like, physically — is 1.2x enrichment over uniform a reasonable
    bar, or does the elastic-network-model math this project already
    uses structurally cap real proteins well below that (e.g. via a
    synthetic positive-control case constructed to have a real,
    deliberately strong distal-favoring seed, checked against the same
    function).
  - If recalibrating: derive the new threshold(s) from the real
    distribution observed (e.g. a percentile of the benchmark set's own
    `distal_enrich` values), not picked to make a specific target look
    good — same non-circularity discipline this project's research tree
    (`__WORK_IN_PROGRESS__`) already applies to its own thresholds.
- Out Of Scope:
  - Re-opening TASK-0033's own resolved question (fixed vs. relative
    contract) — that stays fixed/relative as resolved; this task is
    about the fixed values themselves, if fixed values are kept.
  - Redesigning `quantum_seed_readiness`'s underlying metrics
    (`frac`/`distal_enrich`'s own formulas) — calibration only.
- Constraints And Invariants: CLAUDE.md convention 4 — response shape/
  field names (`verdict`, `frac_good`, `distal_enrich`, etc.) must stay
  the same regardless of outcome.
- Planned Validation: re-run against every target before/after any
  threshold change; a synthetic positive-control case (a hand-built or
  planted seed known to genuinely concentrate distally) should land
  `SAFE` if the recalibrated thresholds are reachable at all — if even a
  constructed best-case can't clear them, that's strong evidence the
  bar itself, not just real proteins, is set wrong.

## TODO

- [x] Extend the validation table to every loadable `systems.py` target.
- [x] Build or identify a synthetic/positive-control case to test whether
      `SAFE` is reachable in principle, not just empirically absent so
      far.
- [x] Decide: recalibrate, or confirm-and-document `PARTIAL`-as-ceiling.
- [ ] If recalibrating: implement, re-run full validation, document the
      derivation. **N/A — confirmed, not recalibrated.**
- [x] If confirming: add the explanatory comment/doc note.

## Dependency

- [[TASK-0033]] — established the threshold *contract* (fixed, not
  relative) this task builds on; do not re-litigate that finding.
- [[TASK-0219]] — soft; fixes GLUCOKINASE's load failure, useful for a
  clean 5/5+ sample here but not a hard blocker (this task can proceed
  with `chain="A"` as a manual workaround the way TASK-0033 did).

## Open Questions

- ~~Is there a real, labeled "known-good" active site anywhere in this
  project's benchmark set to calibrate against...~~ **Resolved — no.**
  All 6 currently-loadable `systems.py` targets are validated for their
  drug-binding *pocket* (apo/holo pairs with a known ligand), not for
  "this active site is an exceptionally strong quantum-walk seed" — no
  target carries an independent ground-truth label for that property.
  Confirms the task's own hedge: option (b), confirm-and-document, is the
  honest outcome here, not a percentile-derived recalibration that would
  fit noise from 6 data points and call it calibration.

## Done

**2026-08-19.** Resolved as **(b): `PARTIAL`/`RISKY` is the correct,
expected ceiling for a typical real active site under this operator; the
fixed `SAFE` thresholds (0.60/1.2) are not recalibrated.** Not dead code
either — a synthetic positive control reaches `SAFE` cleanly under the
exact shipped formula, so the verdict is reachable in principle; it is
just never hit by any of the 6 real, structurally diverse targets tested.

**Extended validation (all 6 currently-loadable `systems.py` targets,
`verified=True` and `verified=False`, direct call to
`quantum_seed_readiness` on real RCSB-fetched apo structures, `.venv`,
`GLUCOKINASE` via the `chain="A"` manual workaround TASK-0033 already
used pending [[TASK-0219]]):**

| target | verified | N | n_seed | verdict | frac_good | distal_enrich |
|---|---|---|---|---|---|---|
| KRAS_G12C | True | 169 | 22 | PARTIAL | 0.36 | 0.941 |
| BCR_ABL1 | True | 451 | 18 | PARTIAL | 0.44 | 0.819 |
| CARDIAC_MYOSIN | True | 950 | 16 | PARTIAL | 0.94 | 0.895 |
| MYC_MAX | **False** | 88 | 3 | PARTIAL | 1.00 | 0.785 |
| PTP1B | True | 298 | 9 | RISKY | 0.00 | 0.775 |
| GLUCOKINASE (chain=A) | True | 448 | 28 | PARTIAL | 0.54 | 0.948 |

`distal_enrich` sits in a tight 0.775-0.948 band on all 6 (adding
`MYC_MAX`, N=88, the smallest target by far, didn't widen the range or
break the pattern) — **never once above 1.0, the uniform-spread mark
itself**, let alone the 1.2 `SAFE` bar. No `SAFE` verdict occurs on any
currently-loadable target.

**Synthetic positive control (this task's own central question: is
`SAFE` reachable in principle, or dead code?):** built a dumbbell-shaped
coordinate case — two tight residue clusters ("lobes") joined by a short
percolating chain of relay points spaced within `R_c=8` Å of each other,
the second lobe placed comfortably past `distal_ang=12` Å — the same
seed↔distal-coupling-forcing shape
`__WORK_IN_PROGRESS__/tests/test_dumbbell_negative_control.py` (TASK-0103)
already uses for exactly this purpose elsewhere in the project, adapted
here to real 3D coordinates so it exercises the actual
`_ctqw_build_H`/`_average_mixing_matrix` code path rather than a
hand-substituted Hamiltonian. A single direct edge cannot satisfy both
"within `R_c=8`" and "past `distal_ang=12`" at once with the shipped
radii, so a relay chain is structurally required for *any* case
attempting this, real or synthetic — confirmed directly: a single-hop
dumbbell (no relay) never percolates any amplitude at all
(`distal_enrich=0.000` in every direct-gap trial run). A ~2500-trial
random search over lobe size / jitter / gap / bridge spacing (script:
this session's scratchpad, not committed — the search itself is not
load-bearing, only its best result, now pinned as a permanent regression
test) found a clean `SAFE` case:

- `n_lobe=4`, `n_distal_lobe=4`, `gap=14.6` Å, 4 relay points every
  ~3.16 Å, lobe jitter ~2 Å (both lobes).
- Result: `verdict=SAFE`, `frac_good=0.75` (bar 0.60), `distal_reach=0.313`,
  `distal_enrich=1.25` (bar 1.2).

**Conclusion: `SAFE` is reachable in principle, cleanly, under the exact
shipped thresholds and formula — this rules out "dead/unreachable code"
as the explanation.** The gap between this and every real target (0.775-
0.948, always *below* uniform) is physical, not a threshold-tuning
artifact: reaching a residue >12 Å away necessarily takes ≥2 hops under
this operator's own `R_c=8`/`r0=7` radii, and each hop dilutes amplitude
into the surrounding local structure (a typical protein's dense local
packing) rather than channeling it onward the way the synthetic case's
isolated two-cluster topology does by construction. Real active sites,
across a 5.6x range in target size (KRAS_G12C 169 to CARDIAC_MYOSIN 950)
and across GTPase/kinase/phosphatase/transcription-factor/myosin target
classes, consistently show local-dominant CTQW transport under this
specific short-range operator — a real, physically meaningful, and now
directly demonstrated property of the formalism on real protein data, not
a bug.

**Why not recalibrate**: this task's own Constraint requires deriving any
new threshold from the real distribution, not picking one that flatters a
target — with only 6 real data points, and this task's own resolved Open
Question confirming no target carries an independent "genuinely SAFE"
ground-truth label to calibrate against, any percentile-derived bar would
be indistinguishable from noise dressed up as calibration. `PARTIAL` as
the honest ceiling for typical real active sites, with `SAFE` legitimately
rare and reserved for unusually distal-favoring topology, is the more
defensible reading — the same "explain, don't silently leave surprising,
don't change without evidence" resolution shape [[TASK-0033]] used for
this same function's threshold *contract* one step earlier.

**Implemented**: `backend/analysis.py::quantum_seed_readiness` gained a
comment (next to TASK-0033's own, same location) recording this finding
and the reachability proof, cross-referencing the new test. New
`TestQuantumSeedReadinessSafeReachability` class in
`backend/test_analysis_characterization.py` pins the synthetic dumbbell
case's exact output (`verdict=SAFE`, `frac_good=0.75`,
`distal_reach=0.313`, `distal_enrich=1.25`) as a permanent regression
guard — a future accidental change to the thresholds or the
`distal_enrich`/`frac` formulas that silently makes `SAFE` unreachable
again would now be caught, not just re-discovered incidentally the way
this task itself was filed.

**Not done, and why**: no `MYC_MAX`-specific chain-override was needed
(loaded cleanly with its existing `chain="A"` config, all 3 active-site
residues resolved) — `verified=False` extension turned out to be free,
not a separate effort. The `GLUCOKINASE` table row above was run with a
manual `chain="A"` override (matching TASK-0033's own earlier workaround)
because [[TASK-0219]] was still `IN_PROGRESS` at the time this task's own
validation script ran; [[TASK-0219]] landed properly (`Done`) later the
same session, adding a real per-role `apo_chain`/`holo_chain` field
(`systems.py`'s `apo_chain="A"` for `GLUCOKINASE`) — the number itself is
unaffected (same chain, same structure) but a re-run today would use that
field directly rather than the manual override; not re-run here since
nothing about the actual measurement changes.

**Validation**: `python -m pytest backend/` — 37 passed (was 36 before
this task's one new test), no regressions. All 6 targets + the synthetic
control re-run directly against the final (comment-only) code — identical
to the numbers above (no logic changed, comment-only edit, same discipline
TASK-0033 followed for its own comment-only fix).
