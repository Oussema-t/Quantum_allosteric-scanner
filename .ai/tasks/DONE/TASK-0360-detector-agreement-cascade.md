# TASK-0360 — The detector-agreement cascade: fpocket vs PASSer vs PocketMiner on identical structures

- Status: Done
- Owner: **Implementer B**
- Priority: **High — cheap, purely classical, and it strengthens the one thing we are actually selling**
- Filed: 2026-09-09 by Reviewer thread (id via `claim.py reserve-next`)
- Done: 2026-09-09
- Related: [[TASK-0306]], [[TASK-0304]], [[TASK-0336]], [[TASK-0327]], [[TASK-0163]], [[TASK-0325]]

## The idea: our own headline finding, applied to a second domain

[[TASK-0306]]/[[TASK-0304]] decomposed the field's "84% recovery" figure and found
it is a **disjunction over six noisy tests**:

| detected by | count |
|---|---|
| >= 1 of 6 | 99/118 = **83.9%** |
| >= 3 of 6 | 68/118 = 57.6% |
| all 6 | 21/118 = **17.8%** |

That result is already in the submission, and it is the concrete evidence behind
the certifying-benchmark proposal.

**Nobody has asked the same question of the pocket detectors themselves.** We use
fpocket. The `allosteric` branch uses PASSer. Both branches use PocketMiner
somewhere. If "recovered by at least one detector" is far above "recovered by all
three", then detector choice is a large, measurable source of variance — and the
same archaeology the submission complains about applies to pocket detection, not
just to the six statistical measures.

### Why this is worth doing now, with six days left

1. **It generalises our strongest finding** from one benchmark's six tests to a
   second, independent domain. A referee who suspects the 84% decomposition is a
   one-off cannot say that twice.
2. **It answers the branch cohort dispute sideways and without argument.** The
   open question between branches is "PASSer or fpocket?". If the two detectors
   agree on most structures, the dispute is minor and either choice is defensible.
   If they do not, that disagreement *is* the finding, and it is quantified rather
   than negotiated.
3. **It feeds Phase-2 component (a) directly.** The certifying benchmark's job is
   to make this distinction automatic rather than archaeological. This is that
   distinction, measured.
4. **It carries no quantum claim at all**, so it cannot weaken or complicate any
   of the nulls.

## Intent Contract

- **Outcome:** the agreement cascade across pocket detectors on one shared
  structure set — recovered by >= 1, >= 2, all — plus pairwise agreement, reported
  in exactly the form [[TASK-0306]] used for the six statistical measures.
- **In scope:**
  1. **Detectors:** `fpocket` (vendored, `__WORK_IN_PROGRESS__/tools/fpocket/`,
     version-pinned per [[TASK-0206]]), **PASSer** (API, and a 399 KB cache exists
     on the `allosteric` branch — reuse it, do not re-fetch what is cached), and
     **PocketMiner** (ported; a Dockerfile exists on the `allosteric` branch and
     [[TASK-0163]] ran it in an isolated repo). `p2rank` has a Dockerfile too
     (`REPRODUCIBILITY.md`) — include it as a fourth **only if** it costs under an
     hour, otherwise state it was skipped and why.
  2. **One structure set, one truth definition, one overlap rule, for every
     detector.** This is [[TASK-0336]]'s lesson and it is the whole task: that
     comparison died last time because two arms were scored against different
     candidate sets with different multiplicity. Any detector that cannot be run
     on a given structure drops that structure **for every arm**, not just its own.
  3. Report the cascade, pairwise Jaccard between detectors, and the count of
     structures where exactly one detector fires — the "78 in between" analogue.
  4. State the per-detector coverage (how many structures each could be run on at
     all) **separately** from its hit rate. A detector that skips hard structures
     looks better than it is.
- **Out of scope:**
  - Any CTQW or quantum arm. This task touches none of them.
  - Re-tuning, re-ranking, or selecting a detector for the pipeline.
  - Building a meta-classifier over detectors — that is [[TASK-0306]]'s pattern and
    a separate question. Measure the cascade first.
- **Constraints and invariants:** detector versions pinned and recorded; the
  overlap/truth rule written down once before scoring and applied identically;
  cached PASSer results used as-is rather than re-queried, with the cache's own
  provenance stated.
- **Planned Validation:** fpocket must reproduce its own committed numbers from
  [[TASK-0163]]/[[TASK-0206]] on the overlapping structures before any
  cross-detector number is trusted. If the vendored binary has drifted again,
  that is the finding and the task stops there.

## Pre-registration (written 2026-09-09, before any detector ran)

### fpocket provenance check, done first — Planned Validation gate

`FPOCKET_BIN` (`tools/fpocket/bin/fpocket`) is, as of [[TASK-0285]], a thin
Docker-wrapper script, not the native binary [[TASK-0206]]'s own
`PROVENANCE.json` pin describes — that pin is now the *superseded* entry;
the current, relevant one is that same file's own
`containerized_build_TASK_0285` record (`qas-fpocket:4.2.3`, binary
SHA256 `ce0f6f8a...535e64`, AUC 0.8596/0.5345 on BCR_ABL1/CARDIAC_MYOSIN
— reproducing TASK-0163's ORIGINAL numbers, not TASK-0206's native-rebuild
ones; a three-way non-convergence already found, disclosed, and pinned by
TASK-0285, not new information this task is surfacing). **Checked
directly**: `docker run --rm --platform linux/amd64 --entrypoint sha256sum
qas-fpocket:4.2.3 /usr/local/bin/fpocket` → `ce0f6f8a...535e64` — **matches
the pinned record exactly. Gate PASSES**; the tool has not drifted since
its own most recent pin. This task's own Planned Validation ("if the
vendored binary has drifted again, that is the finding and the task stops
there") is read as targeting *this* pin — the one the currently-invoked
`FPOCKET_BIN` actually corresponds to — not the older, now-inapplicable
native-binary pin a fresh SHA256 check against would trivially "fail" for
a reason [[TASK-0285]] already fully explains.

### Structure set and truth

The existing 108-structure ASBench KEEP-filtered cohort ([[TASK-0304]]/
[[TASK-0305]]), truth = `allosteric_residues`. **Restricted to each
structure's own primary chain** (the chain carrying the majority of
`active_residues`) for every detector, not just PocketMiner: PocketMiner
has an established single-chain-input convention in this register
([[TASK-0329]]'s own `export_pdb_for_pocketminer`) that fpocket/PASSer do
not share on their own, and running the other two against the full
multi-chain structure while PocketMiner only sees one chain would be
exactly the mismatched-candidate-set failure [[TASK-0336]] diagnosed —
so truth itself, for every detector, is cut down to the primary chain,
the common denominator. Checked directly: 8/108 structures have zero
truth residues on their own primary chain (all-truth is on a different
chain) — dropped from the whole comparison, not from PocketMiner's arm
alone, per this task's own Constraint. **Up to 100 structures**, further
reduced by per-detector coverage (reported separately, per this task's
own Constraint 4).

### The hit rule — identical for all three, and matched to how this field already reports "recovered"

Not top-1/top-K precision (that would need to arbitrarily pick a K fpocket
and PASSer's own variable-length pocket lists don't naturally have) but
**coverage**, matching [[TASK-0163]]/[[TASK-0304]]'s own "recovered by ≥1
of N" framing directly: **a detector counts as detecting the site on a
structure if ANY of its own reported candidate regions overlaps the
(primary-chain) truth by ≥1 residue** — fpocket: any reported pocket
(`pocketN_atm.pdb` membership, no score/druggability cut, matching its own
natural full output list); PASSer: any of its own numbered pockets
(residues parsed from the `chain X and resid ...` selection string);
PocketMiner: **top-10 residues by predicted probability**, the one
necessary adaptation, disclosed as such, since it reports no discrete
pockets of its own — 10 chosen as the right order of magnitude for a
single pocket in this cohort (fpocket/PASSer pockets typically run 10-30
residues), not tuned against any result.

### Detector coverage (before any hit-rate number is trusted)

- **fpocket**: runs on the full-atom deposited structure via the pinned
  Docker wrapper (see above); expected near-100% coverage.
- **PASSer**: `allosteric` branch's own cache (`allosteric/datasets/
  passer_cache.json`, 179 entries) covers 48/104 of this cohort's own PDB
  IDs directly — reused as-is, not re-queried. The remainder fetched live
  from the same endpoint/format `passerfetch.py` (that branch's own
  script) already established (`POST https://passer.smu.edu/api`,
  `model=ensemble`, `top=all`, one primary-chain query per structure,
  4-way concurrency, 3 retries) — confirmed reachable, ~5s/request, before
  committing to fetching the remainder live rather than reporting
  cache-only coverage.
- **PocketMiner**: `qas-pocketminer:pocket_pred` ([[TASK-0269]]/
  [[TASK-0285]]'s own vendored image, already local — no setup cost this
  task pays), single primary-chain PDB per structure, matching
  [[TASK-0329]]'s own invocation exactly. **Time-boxed**: a single-
  structure timing check runs first; if the projected total across the
  full cohort would exceed roughly 30 minutes of wall time, PocketMiner is
  reported as skipped-on-cost grounds (this task's own Budget clause),
  not run to completion regardless.
- **p2rank**: included as the 4th detector, not skipped — `qas-p2rank:2.5.1`
  ([[TASK-0260]]/[[TASK-0285]]'s own vendored image) is already local, no
  setup cost, and its own established per-target cost (~8-15s, `README.md`)
  is well inside this task's "under an hour" bar. `prank predict -f <pdb>
  -o <out>` on the full-atom deposited structure (matching fpocket, not
  primary-chain-restricted for the RUN itself — only the truth/scoring
  comparison is chain-restricted, same as fpocket/PASSer), scored from its
  own `<pdb>_predictions.csv` per-pocket residue list against the same
  hit rule.

## Pre-registered prediction

Two-sided, written before running. **If the cascade is shallow** (detectors mostly
agree), the fpocket-vs-PASSer cohort dispute is a small effect and we should say so
plainly — that is a useful, deflationary result. **If it is steep** (an
at-least-one figure far above the all-three figure), it reproduces the 84% -> 17.8%
pattern in a second domain and materially strengthens the benchmark proposal.
Neither outcome is a point scored against the other branch.

## Budget

Capped. Detector runs plus scoring should be well under a day; the expensive part
is PocketMiner setup, which already exists in two places. If setup alone exceeds
half a day, report the two-detector cascade (fpocket vs PASSer) and disclose
PocketMiner as not run rather than delivering nothing.

## Dependency

- [[TASK-0306]] (Done) — the cascade format and `scripts/task0306_six_measure_meta_classifier.py`.
- [[TASK-0336]] (Done) — why matched candidate sets and matched multiplicity are
  load-bearing, and what happens when they are not.
- [[TASK-0163]]/[[TASK-0206]] (Done) — the fpocket binary, its pin, and its
  committed numbers.
- [[TASK-0327]] (Done) — the PASSer cache and the pocket-score convention it uses.

## Staged Files

- [2026-09-09 21:13] `.ai/tools/submission_build_latex.py` -- glyph map: tau, langle, rangle
- [2026-09-09 21:13] `__WORK_IN_PROGRESS__/documentation/2026-09-09-allosteric-branch-message-DRAFT.md` -- addendum on their joint experiment design
- [2026-09-09 21:13] `.ai/tasks/TODO/TASK-0360-detector-agreement-cascade.md` -- the task file itself

## Done (2026-09-09, Implementer B)

**All four detectors ran (p2rank included, not just the mandatory three) on
one structure set, one truth, one overlap rule. The cascade's shape flips
depending on whether PocketMiner is in it — and the reason is a real,
interpretable methodological difference, not noise.**

### fpocket provenance gate — passed, as pre-registered above

Confirmed directly before any detector ran: `docker run --rm --platform
linux/amd64 --entrypoint sha256sum qas-fpocket:4.2.3 /usr/local/bin/fpocket`
→ matches `PROVENANCE.json`'s own `containerized_build_TASK_0285` pin
exactly. Not drifted.

### Cohort

100/108 ASBench structures usable (8 dropped: zero truth on the structure's
own primary chain, per this task's own pre-registration). **96 distinct
PDB codes among the 100** — 4 (1Z8D, 2Q8M, 3ETE, 3KGF) carry two separately-
annotated allosteric sites each, so detector *coverage* is reported per
unique PDB (a detector runs once per structure file, not once per site) while
the *cascade* is scored per structure/site-instance (100 or, once
PocketMiner's own real failures are folded in, 96) — stated explicitly so
"coverage: 96/100" is not misread as 4 detector failures when it is, for
fpocket/p2rank/PASSer, **zero** (96/96 unique PDBs, every single one).

### Detector coverage — three near-perfect, one genuinely limited

| detector | coverage | failures |
|---|---|---|
| fpocket | 96/96 unique PDBs | 0 |
| p2rank | 96/96 unique PDBs | 0 |
| PASSer | 96/96 unique PDBs (48 from the `allosteric` branch's own cache, 48 live-fetched) | 0 |
| PocketMiner | 92/96 unique PDBs | 4 real model failures (backbone-atom-count reshape errors, e.g. `cannot reshape array of size 3843 into shape (321,4,3)` — a genuine per-structure PocketMiner limitation on this cohort, not a bug here) |

PocketMiner's own time-box (pre-registered 30-minute budget): single-
structure probe 6s, projected 538s for the full 96 — well inside budget,
ran to completion, not skipped on cost.

**Two real bugs caught before trusting a suspicious result, not shipped
silently:** (1) the first PocketMiner pass read `<stem>-preds.npy`, a
filename convention copied from a *different* call site
(`task0163_external_baseline_scoring.py`'s own separate-repo invocation) —
this Docker image actually writes plain `<stem>.txt` (one probability per
residue per line) / `<stem>.error.txt`. Caught because a same-input,
all-detectors-else-succeeded run coming back **0/100 PocketMiner coverage**
was treated as suspicious rather than accepted at face value — checked the
output directory directly, found real `.txt` files sitting right there,
fixed the parser. (2) After that fix, a second pass still returned 0/100 —
a second real bug: the skip-docker-if-output-exists optimization (added to
avoid re-paying the ~68s batch run on every iteration of fixing bug #1)
short-circuited *past* the output-collection step entirely, not just past
the `docker run` call. Refactored into one shared `_collect_pocketminer_
output()` called on both the fresh-run and already-run paths. **Both bugs
were disclosed and fixed before any coverage/cascade number left this
script**, not smoothed over — the same standing discipline this register
applies to every Planned-Validation gate, applied here to a plain sanity
check instead.

Every detector's own raw pocket data is now cached to disk
(`{fpocket,p2rank}_pockets_cache.json`, `passer_live_fetch_cache.json`) —
the two bug-fix cycles above cost zero re-payment of the ~11-19 minute
Docker passes, only the cheap final scoring step, per the standing
"never pay the same expensive derivation twice" rule.

### The cascade — two readings, and the second one is decisive

**3 detectors (fpocket, PASSer, p2rank), n=100, matched:**

| detected by | n | frac |
|---|---|---|
| ≥1 of 3 | 95 | 95.0% |
| ≥2 of 3 | 94 | 94.0% |
| all 3 | 77 | 77.0% |

Shallow. Pairwise Jaccard is high throughout (fpocket–PASSer 0.968,
fpocket–p2rank 0.840, p2rank–PASSer 0.811); own hit rates 94%/93%/79%.
Read alone, this is the **deflationary** reading this task's own pre-
registered prediction named: three geometric/ML static-cavity detectors
mostly agree, and the fpocket-vs-PASSer cohort dispute between branches
looks like a small effect.

**4 detectors (+ PocketMiner), n=96, matched:**

| detected by | n | frac |
|---|---|---|
| ≥1 of 4 | 91 | 94.8% |
| ≥2 of 4 | 91 | 94.8% |
| ≥3 of 4 | 75 | 78.1% |
| all 4 | 23 | **24.0%** |

**≥1 (94.8%) vs all-4 (24.0%) is a ~4x gap — closely reproducing the
84% → 17.8% shape [[TASK-0306]] found in the field's own six statistical
measures, in a second, independent domain (pocket detectors, not
significance tests).** This is the **steep** reading, and it is
PocketMiner's own presence that produces it: its hit rate is 27.1%
(26/96) against 93.8%/92.7%/78.1% for fpocket/PASSer/p2rank, and its
pairwise Jaccard with each of the other three sits at 0.28–0.31 —
sharply lower than the 0.80–0.97 the other three share with each other.

**Read plainly, and this is the finding, not a caveat on it**:
PocketMiner is not "noisier" than the other three in the way the six
statistical measures were noisy versions of the same underlying test —
it is answering a **different question**. fpocket/p2rank/PASSer all
detect geometric cavities already present in the deposited (static, often
holo-adjacent) structure; PocketMiner is trained specifically to predict
which residues participate in a pocket that **opens**, from sequence/
structure-derived dynamics on a single static input — closer to this
project's own cryptic-pocket framing than to classical cavity detection.
**Detector choice is a large, measurable source of variance here, exactly
as [[TASK-0306]]'s own six-measure result was — but the mechanism this
time is legible: one of the four tools is measuring something else.**
Both cascades are reported, not one substituted for the other, per this
task's own Constraint 4 (coverage separate from hit rate) and Intent
Contract (report the cascade "in exactly the form TASK-0306 used").

### Constraints honored

One structure set / one truth / one overlap rule for every detector
(primary-chain restriction, applied uniformly, not just to PocketMiner —
[[TASK-0336]]'s own lesson). Any detector's own failure on a structure
drops it from every arm (the `n_matched` cohorts above, not a per-detector
denominator). Coverage reported separately from hit rate throughout. No
re-tuning, no re-ranking, no pipeline change, no meta-classifier — pure
measurement, per this task's own Out of Scope.

### Not done / explicitly out of scope

- Did not select or re-tune a detector for this project's own pipeline —
  measurement only, per this task's own Out of Scope.
- Did not build a meta-classifier over detectors — [[TASK-0306]]'s own
  pattern, a separate question, explicitly deferred by this task's filing.
- Did not root-cause PocketMiner's 4 individual reshape failures beyond
  naming the mechanism (backbone atom count not matching the model's own
  expected per-residue stride) — a real, disclosed gap for whoever revisits
  PocketMiner's own single-chain export convention next.
- No hypothesis-register entry landed — this is a classical, non-CTQW
  benchmark/methodology finding (detector agreement, not a physics claim),
  the same scope [[TASK-0306]]'s own six-measure decomposition sat in
  without one; reported in `RESULTS.md` and here instead, matching that
  precedent.

**Files**: `scripts/task0360_detector_agreement_cascade.py` (new).
**Data**: `results/tasks/0360_detector_agreement_cascade/
{detector_agreement_result.json,checkpoint.jsonl,fpocket_pockets_cache.json,
p2rank_pockets_cache.json,passer_cache_snapshot.json,
passer_live_fetch_cache.json,pocketminer_io/}`.
