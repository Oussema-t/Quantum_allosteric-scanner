# TASK-0180 Site-level prediction + the single end-to-end apo→pocket runner

## Context

- ID: TASK-0180
- Title: convert per-residue scores into ranked, spatially-resolved **sites**,
  and provide one command that goes apo PDB ID → top-5 predicted allosteric
  sites → scored against [[TASK-0177]]'s consensus holo label, emitting every
  §5 deliverable in one pass.
- Status: Done
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: orchestrating collaborator (Bartosz), 2026-07-29: *"begin from an
  apo structure and end up predicting a pocket that is detected in the holo
  form."*
- Priority: **P0 — this is the required deliverable. Ships regardless of what
  [[TASK-0178]] concludes.**
- Suggested Follow-Up: **[[TASK-0181]] Phase A**, same thread. Not a hard
  dependency (0181 can build its QUBO machinery independently), but 0181's
  benchmark set explicitly includes this task's own site-level clustering
  and chance-level metric — running 0181 before this lands means redoing
  that comparison once it does, so this task landing first is the natural
  order. Recorded 2026-08-01 (Architect) so the link survives whichever
  thread picks 0181 up next.

## Why this matters — the current hit list is not a list of sites

The challenge's §5 asks for *"a ranked list of the top 5 predicted allosteric
**sites** (residue indices)."* `report.assemble_hit_list` returns
`hit_list(scores, k=5, resnums, exclude_idx)` — the top 5 residues by raw
score, with **no spatial deduplication** (checked directly). Because every
observable in this register is spatially smooth, the top 5 are frequently
5 neighbours in one groove. That is **one predicted site reported as five**,
and it inflates any P@5-style statistic while under-reporting coverage.

Two further consequences, both live:

- **The two branches emit different deliverables from the same science.** The
  `main` branch already applies `min_sep=8.0` greedy dedup plus an optional
  `distal_ang` filter; the research branch applies neither. A judge clicking
  the demo and a referee reading the paper see different hit lists.
- **`min_sep`/`distal_ang` are unreported verdict-flipping knobs** on `main`.
  [[TASK-0075]]'s standing finding (an 18-combination grid flipped go/no-go in
  15 of 18 cases) applies directly. Whatever clustering this task adopts must
  emit a **knob spread**, not a point estimate.

## Design

**Site definition.** Cluster high-scoring residues into spatially contiguous
candidate sites, then rank *sites*, not residues:

1. Take the top-`m` residues by score (`m` ≈ 10–15% of N; a stated knob).
2. Single-linkage cluster them at a Cα cutoff (~8 Å — the same contact scale
   the rest of the pipeline uses; do **not** introduce a new geometric
   constant without deriving it).
3. Drop clusters smaller than a minimum size (a druggable pocket is not one
   residue) — stated knob.
4. Score each cluster by an aggregate of its members' scores. **Use the
   mean, not the max**: a max-over-members statistic reintroduces exactly the
   winner's-curse structure [[TASK-0131]] and [[TASK-0123]] both found
   inflates this project's statistics. Report the max as a secondary column.
5. Rank clusters; emit the top 5 with their residue members.

**A site-level hit is a genuine, defensible metric.** A predicted site counts
as a hit if it overlaps the consensus pocket by ≥1 residue (report also ≥3,
and centroid-distance). This is closer to how a medicinal chemist would judge
the output than residue-level AUC — and unlike `main`'s `pocket_pk(tol=6.0)`,
it does not dilate the label. **For reference: that 6 Å dilation covers 27.7%
of a KRAS-sized protein, giving chance P@5 = 0.26 and a pure distance-to-seed
predictor P@5 = 0.66** (measured, 2026-07-28 external review §8). Any
site-level metric introduced here must ship with its own chance level and its
own proximity floor computed the same way.

**The runner.** One command per target:

```
apo PDB id ──► clean ──► H/K build ──► score (apo only, frozen_context)
        └─► site clustering ──► top-5 sites ──► §5 deliverables
                                     │
   [verification only, never read by the predictor]
   TASK-0177 consensus holo label ──┴─► AUC / floor / CI / null / site-hits
```

Emits, in one pass: `quantum_connectivity_matrix.npz` ([[TASK-0160]]),
`hit_list.json` (now site-level **and** residue-level), `verdict.json`,
`report.txt`, and a new `end_to_end.json` carrying the full statement from
[[TASK-0176]] with every clause filled or explicitly marked unavailable.

## Intent Contract

- Outcome: `allostery.sites` (clustering + site ranking + site-level hit
  metrics with chance level and floor), wired into `scripts/run_challenge.py`
  so one invocation produces every §5 deliverable plus the end-to-end record.
- Why required, not assumed: the current hit list is residue-level and
  undeduplicated; no single command currently produces the end-to-end
  statement; and the two branches disagree on what the deliverable is.

- In Scope:
  - `cluster_sites(coords, scores, ...)` → ranked sites with members,
    centroid, aggregate score.
  - Site-level hit metrics **with their own chance level and proximity floor**
    (a distance-to-active-site ranker put through the identical clustering —
    without this the metric is uninterpretable, exactly the defect measured on
    `main`).
  - **Knob spread, per [[TASK-0075]]**: sweep `m`, linkage cutoff, minimum
    cluster size; emit `UNSTABLE` when the knobs decide the top-5 rather than
    the scores. Do not ship a point estimate.
  - Wire into `run_challenge.py` additively; residue-level outputs stay
    byte-identical so the 226-cell register does not move.
  - `end_to_end.json` + a `RESULTS.md` section stating the [[TASK-0176]]
    sentence per target.
  - **Reconcile with `main`**: either port this clustering to `main/backend/
    quantum.py` or document precisely why the two differ. Shipping two
    different hit lists is not an option.

- Out Of Scope:
  - Changing any score, operator, floor or null.
  - Changing residue-level AUC conventions — site-level is **additional**.
  - `main`'s frontend rendering (separate, though the floor-reporting fix
    flagged in the 2026-07-28 review §8 remains outstanding and should be
    filed if not already).
  - Any new observable.

- Constraints And Invariants:
  - **Apo-only prediction, gate-enforced.** The consensus label enters only
    after scoring, inside the verification block. `frozen_context` +
    `stamp_provenance` as usual.
  - No new geometric constant without derivation — reuse the 8 Å contact
    scale ([[TASK-0067]]: 7.5/8.0/10.0 Å showed no significant difference,
    8.0 Å retained).
  - Site aggregation is **mean-primary**; max is reported but never the
    ranking key ([[TASK-0131]]/[[TASK-0123]] winner's-curse precedent).
  - Deterministic under a seeded rng; verified, not assumed.

- Planned Validation:
  - **Degenerate-case test:** on a score field that is pure distance-to-seed,
    site clustering must produce exactly one site near the seed — not five.
    This is the direct regression against the defect being fixed.
  - **Chance-level measurement:** random scores through the full clustering →
    the site-hit metric's null distribution, reported alongside every real
    number.
  - **Non-degeneracy:** on a real target, the top-5 sites must be mutually
    non-overlapping and pairwise ≥ the linkage cutoff apart. Asserted.
  - Residue-level outputs bit-identical pre/post ([[TASK-0074]]'s
    characterization-test precedent — pin them before touching the runner).

## In Progress

None

## TODO

- [x] `cluster_sites` + ranked site output.
- [x] Site-level hit metrics + chance level + site-level proximity floor.
- [x] Knob-spread sweep + `UNSTABLE` reporting.
- [x] Pin residue-level outputs, then wire additively into `run_challenge.py`.
- [x] `end_to_end.json` + the per-target [[TASK-0176]] statement.
- [x] Degenerate-case (pure-distance) regression test.
- [x] Reconcile with `main`'s `min_sep`/`distal_ang`, or document the divergence.

## Dependency

- [[TASK-0177]] — for the consensus label. Still In Progress, no frozen labels
  exist yet (confirmed by reading that task file this session) — this task
  used the incumbent 4.5 Å contact label (`labels_obj.pocket`) as its own
  Design section allows, and records `"label_source": "incumbent_4.5A_contact"`
  explicitly in `end_to_end.json` so it is never confused with TASK-0177's
  eventual consensus label.
- [[TASK-0160]] (Done) — connectivity-matrix deliverable already wired.
- [[TASK-0159]] (Done) — converged propagator already wired into the runner.
- [[TASK-0075]] (Done, corrected from "still TODO" above) — knob-spread
  convention (`superpose.cumulative_overlap_gate`'s GO/NO_GO/UNSTABLE grid
  shape); this task's `sites.site_knob_sweep` is its second, independent
  consumer, mirroring that shape directly.

## Open Questions

- Single-linkage or a density method (DBSCAN)? Single-linkage is simplest and
  reuses the contact cutoff; it chains through elongated grooves, which may be
  desirable (grooves are real) or not (it can merge two adjacent sites).
  Try both, report both, pre-commit to single-linkage as headline.
- Should the site-level metric be the *headline* deliverable and residue AUC
  the supporting detail? It matches the challenge's own §5 wording better.
  Recommend yes for the §5 table, with residue-level AUC retained everywhere
  as the statistical workhorse. Bartosz's call.
- Does site-level scoring change the multiplicity budget? It is a different
  statistic on the same scores. Count it; update [[TASK-0161]].

## Done

**2026-08-01, Implementer A.** Shipped as `src/allostery/sites.py` (new
module): `cluster_sites` (single-linkage headline / DBSCAN alternate,
mean-primary ranking, `top_n`/`m_frac`/`linkage_cutoff`/`min_cluster_size`
knobs), `site_hit_metrics` (undilated ≥1/≥3 overlap + centroid distance,
unlike `main`'s 6 Å-dilated `pocket_pk`), `site_chance_level` (random-score
null through the identical pipeline), `site_proximity_floor`
(`baselines.euclid_from_seed_centroid` through the identical pipeline —
reused, not reimplemented), `site_knob_sweep` (mirrors `superpose.
cumulative_overlap_gate`'s GO/NO_GO/UNSTABLE grid, TASK-0075), and
`end_to_end_record`/`end_to_end_statement` (the TASK-0176 sentence,
every clause filled or explicitly marked unavailable).

Wired additively into `scripts/run_challenge.py::run_target`: `hit_list.json`
gains one new `"sites"` key (existing `indices`/`resnums`/`scores` keys
verified unchanged — `test_run_challenge.py::
test_residue_level_hit_list_keys_unchanged_by_site_addition`); a new
`end_to_end.json` deliverable per target; one appended section to
`results/<run>/RESULTS.md` (**not** the repo-root `RESULTS.md` — writing
there unconditionally would have mutated a tracked file on every test run,
caught and fixed before landing).

**Empirical linkage-cutoff check** (this task's own addition, requested
mid-session rather than assuming TASK-0067's 8.0 Å contact-graph cutoff
transfers to clustering): ran the widened `1-10 Å` grid against two real,
live-fetched targets (KRAS_G12C, BCR_ABL1) with both a proximity-floor probe
and a real `H_new`/CTQW occupation score. Finding: cutoffs below ~3-4 Å
(consecutive-Cα spacing) produce zero surviving clusters; 4-7 Å is a volatile
transition region (5→1 sites); by 7-8 Å both targets converge to a stable
cluster count that holds to 10 Å. 8.0 Å sits inside that converged plateau on
both targets checked — retained as the shipped default on this evidence, not
merely carried over. Full write-up: `src/allostery/SITES_RECONCILIATION.md`
(also covers the `main`/`backend/quantum.py` divergence per the Intent
Contract's "reconcile or document" requirement — documented only, per this
session's explicit decision; `main` is untouched).

**Decisions made this session (user-confirmed):**
- Residue-level AUC stays the headline metric; site-level is reported
  as a clearly-labeled additional section, not a replacement (Open
  Questions' "should site-level be headline" resolved: no).
- `main`/`backend/quantum.py` not touched — comparison documented in
  `SITES_RECONCILIATION.md` instead of porting the clustering there.

**Tests:** `tests/test_sites.py` (17 new tests: degenerate pure-distance-
to-seed regression, chance-level determinism under a seeded rng,
non-degeneracy on 5 well-separated synthetic sites, mean-vs-max ranking,
low-cutoff fragmentation vs. converged-cutoff stability, DBSCAN parity) +
4 new tests in `test_run_challenge.py` (residue-level pinning, `sites` key
shape, `end_to_end.json` shape). Full suite: `996 passed, 2 skipped,
2 xfailed` (`pytest tests/`, no regressions). Real end-to-end smoke run:
`scripts/run_challenge.py --target KRAS_G12C` — completed in 5.9s, wrote
all 6 deliverables, `knob_spread.verdict=UNSTABLE` (honestly reported, not
hidden — the top-5 site set does move across the full knob grid on this
target), `site_chance_level.hit_rate_at_1=0.745` (a >=1-residue-overlap hit
is not very discriminating by itself on this target's geometry — exactly
the kind of finding a chance level exists to surface; `hit_rate_at_3=0.10`
is far more discriminating).

**Known limitation, not fixed here:** `site_chance_level`'s reported CI is
a raw 2.5/97.5 percentile over `n_null` boolean hit/no-hit outcomes, which
is uninformative near either extreme (collapses to `[0, 1]` unless the
hit rate is very close to 0 or 1) — a Wilson/Clopper-Pearson binomial
interval would be more informative. The point estimate (`hit_rate_at_t`)
is correct and is the number actually used above; flagging the CI's crudeness
for a future task rather than silently shipping it as more precise than it is.
