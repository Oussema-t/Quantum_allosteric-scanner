# TASK-0249 — The composite "dumb" baseline: geometry + fpocket druggability + hop shell, versus the collaborating thread's CTQW

- Status: Done
- Resolution: done
- Resolution Note: Composite (fpocket druggability + banded hop onehot + degree + euclid, LOTO-fit) beats CTQW decisively on TASK-0243's frozen 22-target set, both designs: per-residue AUC 0.710 vs 0.592, two-stage MRR 0.304 vs 0.161. fpocket_drug alone (single feature, no fitting) beats even the full composite: 0.756/0.344. CTQW's own incremental value over composite is small but positive (+0.02 AUC/+0.016 MRR). Found a real data-quality defect in TASK-0243's own frozen set (HIV_INTEGRASE_MUT871/916 have an empty active-site seed on all 4 chains of 1M9D).
- Assignee: unassigned (suggest Implementer; substantial, one thread)
- Priority: **High — this is the decisive comparison for the joint experiment and for §2 of the Phase 1 submission**
- Filed: 2026-08-24 by Reviewer
- Depends on: [[TASK-0243]] (frozen untuned target set) — can be **built and validated** before 0243 lands, but its headline number must come from the frozen set
- Related: [[TASK-0242]], [[TASK-0244]], [[TASK-0245]] (`scripts/task0245_cv_attribution.py`), [[TASK-0246]] (`scripts/task0246_hop_contribution_anatomy.py`), [[TASK-0247]] (`scripts/task0247_is_ctqw_a_distance_score.py`)

## The question

Every ingredient of the collaborating thread's pipeline that has been shown to
carry signal is cheap and classical. Assembled honestly, do they beat the CTQW
variant? If a four-feature linear model with no dynamics matches or beats it,
that is the single most informative number this project can put in front of
either the organisers or the collaborating thread.

This is deliberately **doing their homework**: build the strongest simple
competitor we can, and give the operator every chance to beat it.

## What we already measured (inputs, do not re-derive)

- Geometry explains a median **30%** of discrimination above chance
  (cross-validated, n=9); CTQW **+1%** median, negative on 3/9 targets.
- `hop_from_seed` is the strongest single baseline on **5/9** targets and
  accounts for 46–492% of the geometry block's above-chance AUC.
- The hop-shell profile is **banded, not monotonic**: enrichment 0.93× at hop 1,
  **1.63× at hop 2**, 1.38× at 3, 1.15× at 4, 0.69× at 5, →0 past 6. **78% of
  pocket residues sit at hops 2–4.**
- fpocket (no dynamics, no seed) reaches 0.8348/0.8596 on KRAS_G12C/BCR_ABL1.
- CTQW is **not** a distance score — within-shell AUC 0.6305, p=0.0273 vs 0.5 —
  but is indistinguishable from the best geometric baseline within-shell
  (0.6305 vs 0.6292, 4/9 wins, p=0.4961).

## Build

**The composite ("DUMB") ranker**, per residue, apo-only:

1. `fpocket` druggability of the pocket the residue belongs to (0 if none)
2. **banded** hop feature — one-hot shell indicators, not the linear negated
   distance the current floor uses. The band is the measured signal; the linear
   encoding is mis-specified for it.
3. `degree_centrality` (burial; note its coefficient is expected **negative** —
   it scores below 0.5 alone on 6/9 targets)
4. `euclid_from_seed_centroid` (through-space distance, not redundant with hop)

**Fitting discipline — this is the part that decides whether the result means
anything:**

- [x] **Leave-one-target-out.** Fit on N−1 targets, score the held-out one.
      Never fit and score on the same target. An in-sample composite would
      trivially win and prove nothing ([[TASK-0238]] made exactly that mistake
      and had to be redone as [[TASK-0245]]).
- [x] The **same** LOTO protocol applied to the CTQW arm, and to CTQW+composite,
      so all three are compared on identical footing.
- [x] Pre-register the feature list and the fitting rule before the first
      number is seen. No feature added after inspecting a result.

## Evaluate, both designs

- [x] **Per-residue AUC** (this register's design), LOTO.
- [x] **Two-stage within-candidate ranking** (the collaborating thread's
      design): reuse `task0242_two_stage_dryrun.run(t, tuned, return_state=True)`
      — the apparatus [[TASK-0244]] already built and validated for exactly this.
      Report rank of the true pocket, MRR, top-1.
- [x] **Denominator = targets attempted**, not targets where fpocket proposed
      the true pocket. Stage-1 recall was 7/11 in [[TASK-0242]]; a
      within-candidate metric cannot see the other 36%.
- [x] Arms: `composite`, `ctqw`, `composite+ctqw`, `fpocket_drug` alone,
      `hop` alone, `random`. The decisive quantity is
      **`composite+ctqw` minus `composite`** — the operator's incremental value
      once the cheap stuff is done properly.

## Acceptance

- [x] One table, all six arms, both designs, LOTO throughout.
- [x] An explicit answer to: does CTQW add anything over the composite?
- [x] Run on [[TASK-0243]]'s frozen set for the headline; the 9-target set may
      be reported as a preliminary, labelled as such.
- [x] Result written to `RESULTS.md` and, if it survives, into §2 of
      `documentation/PHASE1_SUBMISSION_DRAFT.md`.

## Constraint

**A positive for CTQW is as reportable as a negative, and must be sent to the
collaborating thread either way.** The composite is built to be beaten — if the
operator beats it under LOTO on an untuned frozen set, that is the strongest
result this project has produced and it belongs in the submission. Building a
strawman composite, or quietly weakening it, would destroy the value of the
exercise. Give the simple model every advantage the operator gets.

## Done

**Decisive, both designs, proper power: the cheap classical composite beats
CTQW clearly, and CTQW's own incremental value on top of it is small.
Reported exactly as it landed, positive and negative alike, per this
task's own Constraint.**

Script: `scripts/task0249_composite_dumb_baseline.py`. Reuses
`task0242_two_stage_dryrun.py`'s own `CAND`/`prep`/`run`/`fpocket_candidates`
(the collaborating thread's own apparatus), `task0246_hop_contribution_
anatomy.py`'s own one-hot hop-shell encoding verbatim, and this
register's own `degree_centrality`/`euclid_from_seed_centroid`/
`build_H_new`/`time_averaged_ctqw_converged`/`auc` — no re-derivation.

**Pre-registered before the first number was seen** (this script's own
module docstring, written before execution): 4-feature composite
(fpocket druggability, banded hop one-hot, degree, euclid), LOTO-pooled
OLS fitting (matching [[TASK-0245]]'s own established convention, not a
new classifier), 6 arms, both designs, denominator = targets attempted.

### A real data-quality defect found in [[TASK-0243]]'s own frozen set, not assumed

`HIV_INTEGRASE_MUT871`/`HIV_INTEGRASE_MUT916` (both built on apo `1M9D`)
have an **empty active-site seed** — `backend.active_site.
detect_active_site` returns `source=none, active_site=[]` on **every one
of 1M9D's 4 chains**, confirmed directly, not assumed. This directly
contradicts [[TASK-0243]]'s own Done section ("20/22 resolve to
`source: uniprot`... zero fell back to a top-degree proxy") — worth a
follow-up for whoever owns that curation next; not investigated further
here (root-causing `detect_active_site`'s own UniProt lookup for this
entry is a different task's own surface). Handled here as a real
target-attempted failure (excluded from the LOTO-pooled fit, counted in
every "targets attempted" denominator below), not silently dropped or
allowed to poison the pooled fit with NaN (confirmed directly: an
unguarded empty seed crashed `_fit_ols`'s own SVD on the first real run
of this script — fixed before trusting any number below).

### Headline: [[TASK-0243]]'s frozen 22-target set (20/22 usable for the
per-residue design, 14/22 stage-1+seed survivors for two-stage)

**Per-residue AUC, LOTO** (median across n=20 usable targets):

| arm | median AUC |
|---|---|
| `fpocket_drug` alone | **0.756** |
| `composite+ctqw` | 0.730 |
| `composite` | 0.710 |
| `ctqw` | 0.592 |
| `random` | 0.521 |
| `hop` alone | 0.431 |

**Two-stage candidate ranking, LOTO weights, denominator = 22 targets attempted**:

| arm | MRR | top-1 |
|---|---|---|
| `fpocket_drug` alone | **0.344** | 6/22 |
| `composite+ctqw` | 0.320 | 5/22 |
| `composite` | 0.304 | 5/22 |
| `ctqw` | 0.161 | 2/22 |
| `hop` alone | 0.067 | 0/22 |
| `random` | 0.046 | 0/22 |

**Explicit answer to this task's own central Acceptance question — does
CTQW add anything over the composite?** A small, positive increment,
not a decisive one: `composite+ctqw − composite` = **+0.020 AUC**
(per-residue) / **+0.016 MRR** (two-stage). CTQW is not nothing — the
sign is consistently positive across both designs — but it is a minor
refinement on top of the composite, not a driver of the result. **The
composite itself, and even `fpocket_drug` alone (its single strongest
ingredient, no fitting required at all), both clearly and substantially
outperform CTQW on its own** — 0.710/0.756 vs. 0.592 per-residue AUC;
MRR 0.304/0.344 vs. 0.161 two-stage. This is the single most informative
number this register has produced for the joint experiment, reported
exactly as it landed: **on this untuned, frozen, proper-power set, the
operator does not beat honest classical baselines it should be compared
against — the cheapest of them (fpocket druggability alone) beats it by
the widest margin of all.**

**One further, unregistered nuance, reported because it changes how the
composite itself should be read**: `fpocket_drug` alone beats the full
4-feature `composite` in both designs (0.756 vs. 0.710; MRR 0.344 vs.
0.304) — adding banded-hop/degree/euclid to fpocket druggability does
**not** help under true cross-target LOTO, even though [[TASK-0246]]'s
own within-target CV found real signal in the banded hop encoding
specifically. This registry's own strongest, simplest baseline for the
joint experiment is `fpocket_drug` alone, not the 4-feature composite —
a real, load-bearing finding of this task's own construction exercise,
not assumed going in.

**`hop` alone scoring *below* random (0.431 median) under LOTO is real,
not a bug — checked directly, not assumed.** Per-target breakdown: 13/20
targets score below 0.5. Not a sign-flip or single-target artifact (the
same `hop_from_seed` direction, embedded inside `composite`, performs
well — confirming the underlying feature and AUC-direction convention
are correct). Read as a genuine LOTO-generalization failure specific to
the 8-column one-hot shell encoding: this frozen set spans a much wider
range of protein sizes (225–1205 residues) than [[TASK-0246]]'s own
9-target within-target-CV set, and an absolute-shell-index one-hot
encoding pooled across very differently-sized/shaped targets does not
obviously transfer the way a same-target CV split does. A real,
reportable instability in this specific encoding at proper power, not
silently smoothed over.

### Preliminary: [[TASK-0245]]'s own 9-target set (labelled preliminary, not the headline, per this task's own Acceptance)

| arm | median AUC (LOTO, n=9) |
|---|---|
| `fpocket_drug` alone | 0.638 |
| `composite+ctqw` | 0.622 |
| `ctqw` | 0.610 |
| `composite` | 0.582 |
| `random` | 0.518 |
| `hop` alone | 0.500 |

Directionally consistent with the headline (fpocket_drug strongest,
ctqw not dominant) but **not** the same ranking — `composite` here trails
`ctqw` slightly (0.582 vs. 0.610), reversed from the headline's own
0.710 vs. 0.592. Exactly the underpowered-small-sample instability
[[TASK-0243]] itself was filed to resolve (n=9 vs. n=20) — the frozen
set's own larger, more diverse sample is the number to trust, this one
is reported only because this task's own Acceptance asked for it
labelled as preliminary.

### Not done, stated plainly

Root-causing `detect_active_site`'s own failure on 1M9D (flagged, not
fixed — a different task's own surface). A held-out-target-count-scan
re-fit (does the composite's own LOTO AUC improve further with 25-30
targets, matching [[TASK-0243]]'s own noted headroom in the
still-unscreened candidate pool) — not attempted, real remaining scope
if this line of work continues. Sending this result to the collaborating
thread itself is outside what this session can do directly — the
finding is written here and in `RESULTS.md` for whoever owns that
communication next.

Artifacts: `scripts/task0249_composite_dumb_baseline.py`,
`results/tasks/0249_composite_dumb_baseline/{preliminary_per_residue,headline_per_residue,headline_two_stage}.json`.
