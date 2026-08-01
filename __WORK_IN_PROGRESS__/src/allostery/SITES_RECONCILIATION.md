# TASK-0180 — reconciliation with `main`'s site dedup

`sites.py` (this task) and `main`'s `backend/quantum.py::predict_allosteric_sites`
both exist to turn a per-residue score into a deduplicated top-5 site list. They
differ, deliberately, and are not merged in this task (decision recorded 2026-07-31,
see `.ai/tasks/IN_PROGRESS/TASK-0180-*`):

| | `main::predict_allosteric_sites` | `sites.py::cluster_sites` (this task) |
|---|---|---|
| Dedup method | Greedy farthest-first pick (`min_sep=8.0`) — each accepted residue must be ≥8 Å from every already-picked residue | Single-linkage clustering of the top-scoring residues at `linkage_cutoff` (default 8.0 Å), DBSCAN available as an alternate method |
| Aggregation | None — one residue *is* the site, no cluster/mean | Cluster of residues; ranked by **mean** member score, max reported but never the ranking key (TASK-0131/TASK-0123 winner's-curse precedent) |
| Hit metric | `pocket_pk(tol=6.0)` — dilates the label by 6 Å | `site_hit_metrics` — undilated overlap (≥1, ≥3 residues) + centroid distance |
| Chance level / floor | Not computed | `site_chance_level` (random-score null) + `site_proximity_floor` (distance-to-seed ranker through the identical pipeline) |
| Knob-spread reporting | Not computed — `min_sep`/`distal_ang` are unreported, verdict-flipping knobs (TASK-0075's standing finding) | `site_knob_sweep` — full grid, `STABLE`/`UNSTABLE` verdict, never a point estimate |

**This task's output (`sites.py`) is authoritative for the challenge submission.**
`main`'s `predict_allosteric_sites`/`pocket_pk` are unchanged — no code in
`backend/quantum.py` or the deployed frontend is touched by this task, per the
explicit scope decision recorded in the task file. A future task can port this
clustering to `main` if the two demos need to agree pixel-for-pixel; that is not
required for the challenge deliverable this task ships.

## Empirical check on the 8.0 Å linkage cutoff (not assumed)

TASK-0067 swept `{7.5, 8.0, 10.0}` Å for the **contact-graph** cutoff (the
Hamiltonian construction scale) and found no significant difference, retaining
8.0 Å. That sweep says nothing about the right scale for **clustering
already-selected top-scoring residues** — a different geometric question — so
`site_knob_sweep`'s own `linkage_cutoffs` default is deliberately widened to
`(1.5, 2.0, 3.0, 5.0, 7.5, 8.0, 10.0)` Å, and was run end-to-end (1.0-10.0 Å,
step 1.0 Å) against two real, live-fetched benchmark targets before committing
to 8.0 Å as the shipped default:

```
KRAS_G12C (N=169), euclid_from_seed_centroid probe (site_proximity_floor's own input):
  1-3 A: 0 sites (below consecutive-C-alpha spacing, ~3.8 A -- nothing chains)
  4 A:   5 sites (21 members)
  5-10 A: 1 site (21 members) -- converged

KRAS_G12C (N=169), real H_new/CTQW occupation score (what run_target actually clusters):
  1-3 A: 0 sites
  4-5 A: 5 sites (14-18 members)
  6 A:   2 sites (21 members)
  7-10 A: 1 site (21 members) -- converged

BCR_ABL1 (N=451), euclid_from_seed_centroid probe:
  1-3 A: 0 sites
  4 A:   5 sites (47 members)
  5 A:   5 sites (51 members)
  6 A:   4 sites (55 members)
  7 A:   2 sites (56 members)
  8-10 A: 1 site (56 members) -- converged
```

**Finding**: below ~3-4 Å (roughly this project's own consecutive-C-alpha
spacing), single-linkage clustering cannot chain even physically adjacent
residues, so nothing survives `min_cluster_size` — an easily-dismissed,
uninformative regime, exactly as anticipated. Between 4 Å and 7-8 Å, cluster
count monotonically drops from 5 fragments toward 1 as the cutoff widens — this
is real, useful information (how sensitive the top-5 output is to this knob is
exactly `site_knob_sweep`'s own job to report per-target, hence `UNSTABLE` on
both checks above at the full 1-10 Å grid). By 7-8 Å, both targets have already
converged to a stable cluster count and stay converged out to 10 Å. **8.0 Å
sits inside this converged plateau on both real targets checked, not in the
volatile 4-6 Å transition region** — retained as the shipped default on this
evidence, not merely carried over from TASK-0067's unrelated contact-graph
sweep. `site_knob_sweep`'s own per-target grid is reported alongside every real
run (`hit_list.json`'s `sites.knob_spread`) so a target where this does not
hold is flagged `UNSTABLE`, not silently assumed stable.
