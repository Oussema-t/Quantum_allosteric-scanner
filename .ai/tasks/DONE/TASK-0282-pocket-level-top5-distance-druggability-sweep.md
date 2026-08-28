# TASK-0282 — A pocket-level top-5: sweep distance × druggability, and compare it to CTQW fairly

- Status: Done
- Assignee: Implementer A
- Priority: **Highest — it is the only open item that could change what the Phase 1 submission actually delivers, and the writeup is imminent**
- Filed: 2026-08-28 by Reviewer
- Related: [[TASK-0242]], [[TASK-0249]], [[TASK-0254]], [[TASK-0255]], [[TASK-0258]], [[TASK-0184]], [[TASK-0261]]

## Why

The §5 deliverable asks for *"the top 5 predicted allosteric **sites**."* Our
pipeline ranks all N residues and takes the top 5 — a harder problem than the
one posed, and it performs accordingly: measured P@5 on the mandatory targets
is **0.2 / 0.0 / 0.0**, one hit in fifteen.

Bartosz proposed the alternative: choose a **pocket** by druggability and
distance, then draw residues from inside it. Spot-checked on the three
mandatory targets (Reviewer, 2026-08-27, expected hits from a random draw):

| target | ceiling (best-overlap pocket) | druggability + MIN_HOP≥2 | our residue ranking | best pocket's druggability | its rank |
|---|---|---|---|---|---|
| **BCR_ABL1** | 0.7 | **0.7** | **0.0** | 0.566 | **#2 / 37** |
| KRAS_G12C | 0.8 | 0.1 | 0.2 | **0.001** | #6 / 9 |
| CARDIAC_MYOSIN | 0.3 | 0.1 | 0.0 | **0.001** | #39 / 55 |

On BCR-ABL1 the simplest possible version already reaches **≈3.5/5 where our
deliverable gets 0/5**: the true pocket's fpocket candidate holds 14 of 16
residues and ranks #2 by druggability; the #1 sits at `min_hop = 0` — it is the
active site — so a distality filter promotes the right pocket to first.

## The prior this task must test, stated before running

**On KRAS and CARDIAC_MYOSIN the correct pocket has druggability ≈ 0.001.**
fpocket finds it and scores it as essentially undruggable. **No monotone
function of druggability and distance can select it**, because the ranking
signal is not there to threshold. Pre-registered prediction: **the sweep will
work on BCR-ABL1 and fail on the other two**, and any function that appears to
succeed on all three is overfitting.

If that prediction holds, the finding is not "we built a better predictor" but
**"pocket selection works exactly where the pocket is already open"** — the
same 9-of-20-already-open split ([[TASK-0254]]) seen from a third angle, and
note BCR-ABL1's pocket is open because myristic acid is holding it
([[TASK-0278]]).

## Scope

### The sweep

- [x] Candidate pockets from fpocket on **apo** (reused
      `task0242_two_stage_dryrun.fpocket_candidates` verbatim).
- [x] Swept the selection rule over:
      - **distance metric**: graph hop, Euclidean centroid, and **minimum
        heavy-atom distance** to the active site (the last via
        [[TASK-0255]]'s own `min_heavy_atom_dist_to_seed`, reused not
        re-derived).
      - **exclusion cutoff**: hop∈{1,2,3}, min_euclid∈{6,8,10,12}Å,
        centroid_euclid∈{10,15,20}Å — 10 (metric,cutoff) pairs.
      - **combination**: druggability alone; weighted sum (0.5/0.5 z-score);
        rank product; strict lexicographic, **both directions** — far-first
        (this task's own original reading of "categorise then rank") and
        near-first (added mid-run, see below). 61 total configurations.
- [x] Draw convention: expected hits = overlap/pocket_size, analytic, no
      Monte-Carlo noise. An fpocket-alpha-sphere-ranked draw was not run
      separately — the `fpocket_drug`/`fpocket_score` arms already sweep
      fpocket's own two native scores; a third alpha-sphere-count draw was
      judged redundant with `fpocket_score` and dropped, not silently
      skipped.

**Mid-run addition, disclosed**: a Reviewer probe
(`task0282_prior_lexicographic_probe.py`, filed while this task was already
claimed/IN_PROGRESS) found in-sample that a NEAR-first lexicographic
ordering (nearest surviving distance stratum first, druggability as
tiebreak — the opposite of this task's own original far-first reading)
recovers KRAS_G12C's true pocket at its oracle ceiling. Folded into the
grid as `lex_near_first` (a rule family, not a chosen winner) so LOTO could
test it rather than adopting it on the probe's own 3-target spot-check —
see RESULTS.md for the outcome (it does not win any LOTO fold).

### Fitting discipline — this decides whether the result means anything

- [x] **Leave-one-target-out over [[TASK-0243]]'s frozen 20.** Rule chosen on
      N−1 targets (mean EH, deterministic tie-break to first rule in the
      pre-registered enumeration order), scored on the held-out target.
      Every one of the 20 folds selected the identical rule.
- [x] LOTO number is the headline throughout RESULTS.md; in-sample top-6
      rules reported alongside for context, labelled.
- [x] Cluster-robust ([[TASK-0261]]'s exact 13-cluster sign-flip, reused
      verbatim: `CM`/`cluster_sign_flip_test`) on all 3 comparisons quoted.

### The comparison to CTQW must be like-for-like

- [x] Did not compare pocket-level to residue-level CTQW.
- [x] Ran CTQW through the identical pocket-selection wrapper (fixed
      `MIN_HOP>=2`, [[TASK-0242]]'s own spec, not swept — rank survivors by
      mean CTQW occupancy, same draw convention).
- [x] Reported random pocket selection (mean EH over all raw fpocket
      candidates, no filter) and best-overlap oracle (EH of the
      max-RECALL candidate — verified this definition against the
      Reviewer's own filed spot-check numbers before adopting it, see
      Done section) as the two bracketing baselines.

## Acceptance

- [x] One table: {residue-ranking, swept pocket rule, CTQW-in-wrapper, random
      pocket, oracle ceiling} × {mandatory 3, frozen 20}, LOTO throughout —
      in RESULTS.md.
- [x] Explicit verdict on the pre-registered prior: **HOLDS** (works on
      BCR_ABL1, fails on KRAS_G12C/CARDIAC_MYOSIN, on the actual
      LOTO-selected general rule).
- [x] Selected rule in closed form: `MIN_HOP >= 1` (median 3.18 Å, IQR
      1.38–3.76 Å) + rank surviving fpocket candidates by
      `druggability_score` alone.
- [x] `RESULTS.md` written. Swept rule beats residue-ranking **in aggregate
      mean**, not on every target (loses to the deployed pipeline's own
      cited number on KRAS_G12C specifically, not cluster-robustly
      significant at n=13) — recommendation to [[TASK-0184]] is to **report
      both, not switch**, exactly the qualified form this Acceptance item's
      own "if...beats...under LOTO" wording allows.

## Constraint

The ceiling is **0.8 / 0.7 / 0.3** — even a perfect oracle picking the best
fpocket candidate does not reach 4/5 on two of three mandatory targets. **State
that ceiling next to every result**, so no reader takes a good BCR-ABL1 number
as evidence the approach generalises.

And if the swept rule beats CTQW only because CTQW is very poor, say exactly
that. *"Outperforms CTQW"* and *"works"* are different claims, and only the
second belongs in a submission without qualification.

## Done (2026-08-28, Implementer A)

**Claimed after** `99f6c02` (Reviewer's own filing) landed; the Reviewer's
own follow-up probe (`4ba81e6`) landed mid-build, while this task was
already IN_PROGRESS — its own header explicitly deferred to whoever owned
this task rather than editing the file, so its finding was folded into the
grid here (see Scope) rather than lost.

**Apparatus**: new `scripts/task0282_pocket_selection_sweep.py`, reusing
`task0242_two_stage_dryrun` (candidates, `prep`), `task0255_hop_
angstrom_calibration` (`min_heavy_atom_dist_to_seed`), `task0258_
allosteric_distance_taxonomy` (`measure`, site-category covariate),
`task0261_cluster_robust_stats` (`CM`, `cluster_sign_flip_test`), and
`allostery.baselines`/`hamiltonians`/`propagators`/`metrics` throughout.
Import-order discipline followed ([[TASK-0273]]/[[TASK-0276]]'s own
established fix): the altloc="all" `prody.parsePDB` patch is applied
before `allostery` is ever imported, so its own folder-defaulting patch
composes rather than being clobbered — verified directly (no stray PDBs
left outside `pdb_cache/`).

**Oracle-ceiling definition resolved by direct verification, not assumed**:
"best-overlap pocket" in the Reviewer's own filed spot-check table means
the candidate that best RECALLS the true pocket (max overlap_count/
n_pocket), not the candidate maximizing precision/EH directly — confirmed
by reproducing the Reviewer's own 3 numbers essentially exactly
(0.8/0.737/0.279 here vs. the filed 0.8/0.7/0.3, plus the filed
druggability values 0.566/#2-of-37 and 0.001/#6-of-9 matching exactly) only
under the recall-based definition; a naive precision-maximizing "oracle"
gave 0.857/0.8/0.5 and did not match at all — caught before trusting it.

**Real discrepancy found and disclosed, not resolved by fiat**: this task's
own Why section cites "our residue ranking" P@5 as 0.0/0.2/0.0 on the 3
mandatory targets; an independent recompute here, under this exact task
family's own single pre-registered GAUGE operator (H_new/ctqw_converged_
incoherent — the same operator `CTQW-in-wrapper` uses), gives 0.0/0.0/0.0
on the identical targets. The deployed backend evidently selects a
different Hamiltonian gauge than this family's simpler fixed one on
KRAS_G12C. Resolved by using the task file's own cited numbers for the
mandatory-3 residue-ranking column (what actually ships) and flagging the
discrepancy explicitly in RESULTS.md, rather than silently picking
whichever number made the pocket-level method look better — this matters
materially: under the correct (cited) number, the swept rule LOSES to
residue-ranking on KRAS_G12C (0.071 vs 0.200), not a uniform win as an
uncorrected first draft of this writeup implied.

**Headline finding**: every one of the 20 LOTO folds selects the identical
rule (`MIN_HOP>=1` + druggability alone) — the Reviewer probe's own
`lex_near_first` family never wins a fold, confirming the probe's own
explicit warning that its in-sample 0.267 was overfitting. Full numbers,
category breakdown, and cluster-robust stats in RESULTS.md.

**Suite**: no code in `src/allostery` was modified; no regression run
required. New script only.

**Moved TODO/IN_PROGRESS → DONE.**
