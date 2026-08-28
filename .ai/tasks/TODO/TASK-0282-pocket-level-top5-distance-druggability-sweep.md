# TASK-0282 — A pocket-level top-5: sweep distance × druggability, and compare it to CTQW fairly

- Status: TODO
- Assignee: unassigned (suggest Implementer A or D — reuses TASK-0242's apparatus wholesale)
- Priority: **Highest — it is the only open item that could change what the Phase 1 submission actually delivers, and the writeup is imminent**
- Filed: 2026-08-28 by Reviewer
- Related: [[TASK-0242]], [[TASK-0249]], [[TASK-0254]], [[TASK-0255]], [[TASK-0258]], [[TASK-0184]]

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

- [ ] Candidate pockets from fpocket on **apo** (reuse
      `task0242_two_stage_dryrun.fpocket_candidates`, not re-derived).
- [ ] Sweep the selection rule over:
      - **distance metric**: graph hop, Euclidean centroid, and **minimum
        heavy-atom distance** to the active site. [[TASK-0255]] showed hop and
        Å diverge badly — `MIN_HOP ≥ 2` is a median of only 7.5 Å — so the
        metric choice is not cosmetic.
      - **exclusion cutoff** (to drop orthosteric pockets): a grid in each
        metric's own units, stated before running.
      - **combination**: druggability alone after filtering; a weighted sum;
        a rank product; strict lexicographic (distance-bin, then druggability
        — Bartosz's "categorise then rank").
- [ ] Draw convention: report **expected hits = overlap / pocket_size**, the
      analytic version of a random draw, so there is no Monte-Carlo noise.
      Report a fpocket-alpha-sphere-ranked draw alongside if it differs.

### Fitting discipline — this decides whether the result means anything

- [ ] **Leave-one-target-out over [[TASK-0243]]'s frozen 20.** Choose the rule
      on N−1 targets, score the held-out one. **A rule tuned on three
      mandatory targets and reported on those same three is worthless**, and
      it is the obvious way this task fails.
- [ ] Report the LOTO number as the headline. In-sample may appear beside it,
      labelled.
- [ ] Cluster-robust where a p-value is quoted ([[TASK-0261]], 13 clusters).

### The comparison to CTQW must be like-for-like

- [ ] **Do not compare a pocket-level method to a residue-level CTQW.** That
      compares output shapes, not methods.
- [ ] Run **CTQW through the identical pocket-selection wrapper** — rank the
      same fpocket candidates by mean CTQW occupancy, draw the same way.
      [[TASK-0242]]/[[TASK-0249]] already built this: CTQW MRR 0.161 against
      fpocket's 0.344 on the two-stage arm.
- [ ] Also report **random pocket selection** and **best-overlap oracle** as
      the two bracketing baselines. Beating CTQW is a low bar — CTQW's
      added-last marginal is p=0.973 ([[TASK-0263]]) — and a result that beats
      CTQW while sitting near random pocket choice has demonstrated nothing.

## Acceptance

- [ ] One table: {residue-ranking, swept pocket rule, CTQW-in-wrapper, random
      pocket, oracle ceiling} × {mandatory 3, frozen 20}, LOTO throughout.
- [ ] An explicit verdict on the pre-registered prior above.
- [ ] The selected rule stated in closed form, with its cutoff in Å as well as
      hops.
- [ ] `RESULTS.md`; and if the pocket-level rule beats residue-ranking under
      LOTO, a recommendation to [[TASK-0184]] that the **top-5 deliverable
      switch to pocket selection**, with both reported.

## Constraint

The ceiling is **0.8 / 0.7 / 0.3** — even a perfect oracle picking the best
fpocket candidate does not reach 4/5 on two of three mandatory targets. **State
that ceiling next to every result**, so no reader takes a good BCR-ABL1 number
as evidence the approach generalises.

And if the swept rule beats CTQW only because CTQW is very poor, say exactly
that. *"Outperforms CTQW"* and *"works"* are different claims, and only the
second belongs in a submission without qualification.
