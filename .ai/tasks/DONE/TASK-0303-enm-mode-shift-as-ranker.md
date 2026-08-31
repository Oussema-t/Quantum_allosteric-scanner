# TASK-0303 — Add ENM mode shift to the pocket-ranking family

- Status: Done
- Priority: High — an independent physical signal that is **not in the rule family at all**
- Filed: 2026-08-30 by Reviewer thread
- Related: [[TASK-0301]], [[TASK-0300]], external Experiment D

## Why

Every one of the 61 rules in [[TASK-0282]]'s family is a function of
distance-to-seed and fpocket druggability ([[TASK-0301]]). **ENM mode
shift is a dynamics signal — independent of both — and it has already
shown effect** in your agents' Experiment D:

- Open stratum: **p = 0.005–0.013**, cluster-collapsed, surviving
  **fixed-node-budget AND volume-residualisation AND both candidate
  settings**. Not a size artifact.
- More robust than hydrophobic density to candidate-set expansion: going
  default → `-m 2.8`, hydrophobic density's open rank-1 falls 6/6 → 3/6
  while mode shift's p is unmoved (0.0052 → 0.0060).
- Cryptic stratum: not significant (p = 0.15–0.65), but median percentile
  0.24–0.28 against a K=6 detection boundary of 0.173 — **on the right
  side of chance**, unlike conservation at 0.66–0.69.

## Scope

- [x] Port Experiment D's mode-shift computation into this repo's own
      pipeline (`expD_modeshift.py` in
      `.ai/reviews/2026-08-29 - distal pockets/`).
- [x] **Re-run with this repo's per-target `enm_cutoff`.** Experiment D
      used a uniform GNM 7.3 Å because `build_H_new`'s per-target cutoff
      was unavailable in that container — its own §3 flags this as a
      caveat that must be cleared "before the cryptic conclusion is
      trusted."
- [x] **AMENDED 2026-08-31 (lane collision):** do **NOT** add mode shift to
      `task0282_pocket_selection_sweep.METRICS` or re-run that sweep this
      window. LANE B owns all `task0282` runs while it re-runs the extended
      cohort, and two implementers editing and running the same script
      produces results on a moving target. Evaluate mode shift **standalone**
      — its own ranker, scored against random, cluster-robust. Integration
      into `METRICS` (with [[TASK-0300]]'s cluster-mean selection fix, not
      the defective row-mean criterion) is a follow-up after Lane B lands.
- [x] Report whether mode shift is independent of druggability and pocket
      size (partial correlation), since that independence is the entire
      reason for adding it.

## Constraint

Do **not** re-sweep the whole family looking for a new winner.
[[TASK-0300]] showed selection on 13 clusters is what breaks. Add the
metric, report its own standalone performance and its independence, and
leave selection alone.

## Done (2026-08-31, Implementer C)

**Verdict: does not reproduce, on either statistic, once ported into this
repo's own real apparatus.** Not this register's own standard ranker
statistic (top-mode-shift-candidate EH vs random, p = 0.20–0.56
everywhere) and not Experiment D's own exact percentile/Fisher statistic
either (open stratum Fisher p = 0.306/0.319, vs. that experiment's own
claimed 0.005–0.013). The one genuine positive: mode shift **is**
independent of druggability once pocket size is controlled for
(supporting, though no longer the deciding factor for, this task's own
"add a genuinely independent signal" premise).

### Port, faithful to Experiment D's own method

New `scripts/task0303_enm_mode_shift.py`. Same computation (fill a
candidate pocket with dummy nodes at its fpocket alpha-sphere centres,
rebuild the GNM Kirchhoff, measure softest-mode stiffening; `raw` = every
alpha-sphere as a node, `kfix` = k-means-reduced to a fixed 8 nodes so
pocket size cannot re-enter through node count), reusing this register's
own shared, already-tested `allostery.potentials.gnm_context` instead of
Experiment D's own from-scratch Kirchhoff/eigh reimplementation. Alpha-
sphere coordinates are not exposed by `t0242.fpocket_candidates`'s own
return dict (residue-level only) — parsed directly from fpocket's own
`pocket{id}_vert.pqr` output, a new, small, self-contained helper.

**Candidate/truth apparatus mirrors `task0282_pocket_selection_sweep.
build_target`'s own call shape exactly** (`t0242.prep` + `t0242.
fpocket_candidates` + the same TASK-0298 (chain,resnum)-keyed `idx_of`)
but is a **separate, duplicated ~15-line implementation, not an import
from that module** — the 2026-08-31 lane-collision amendment explicitly
forbids touching `task0282` while Lane B owns its own re-run of the
extended cohort.

**The cutoff caveat, cleared and reported precisely, not glossed over**:
this repo's own per-target `enm_cutoff` (`config/candidate_targets_
task0243.yaml`) is used throughout, replacing Experiment D's own uniform
7.3 Å placeholder — but checked directly, not assumed to vary: **every
one of the 22 configured targets carries the identical value, 8.0 Å**.
The fix is real (the actual per-target field is read, not a hardcoded
constant) but in practice resolves to a single uniform +0.7 Å shift for
this cohort, not a heterogeneity correction — stated so the non-
reproduction below is not misattributed to "some targets finally got
their own real cutoff."

### Standalone evaluation, both statistics, cluster-robust throughout

This register's own EH-of-top-ranked-candidate-vs-random statistic
(`task0282`'s own established convention, [[TASK-0261]]'s exact 13-cluster
sign-flip test):

| variant | n | n_clusters | mean Δ(selected − random EH) | p |
|---|---|---|---|---|
| raw | 20 | 13 | +0.021 | 0.557 |
| kfix | 20 | 13 | +0.063 | 0.204 |

Crypticity-stratified (1 straddling cluster excluded from this split
only, [[TASK-0260]]/[[TASK-0266]]'s own established handling):

| variant | stratum | n | n_clusters | mean Δ | p |
|---|---|---|---|---|---|
| raw | open | 8 | 5 | +0.037 | 0.875 |
| raw | cryptic | 10 | 7 | −0.000 | 1.000 |
| kfix | open | 8 | 5 | +0.073 | 0.500 |
| kfix | cryptic | 10 | 7 | +0.053 | 1.000 |

**Not significant anywhere, either variant, either stratum.**

**Experiment D's own exact statistic added afterward, for a genuine
apples-to-apples check** (percentile rank of the true — max-recall —
candidate's own mode-shift value among all candidates, Fisher-combined
per stratum, its own published method):

| variant | stratum | n | median percentile | rank-1 hits | Fisher p |
|---|---|---|---|---|---|
| raw | open | 8 | 0.392 | 1/8 | 0.306 |
| raw | cryptic | 10 | 0.344 | 1/10 | 0.178 |
| raw | ALL | 20 | 0.297 | 4/20 | **0.033** |
| kfix | open | 8 | 0.329 | 0/8 | 0.319 |
| kfix | cryptic | 10 | 0.357 | 1/10 | 0.150 |
| kfix | ALL | 20 | 0.282 | 3/20 | **0.029** |

**Open stratum does not reproduce** (0.306/0.319 vs. Experiment D's own
claimed 0.005–0.013). The only marginal signal is the un-stratified
ALL-20 Fisher combination (p≈0.03) — and that number is **not
cluster-robust**: Fisher's own combination treats all 20 rows as
independent, exactly the pseudo-replication this register has already
found breaks four other selection procedures ([[TASK-0300]]'s own
count). Read as noise until cluster-corrected, not reported as a
positive.

### Independence — the one part of the premise that holds

Pooled, per-target-z-scored Spearman across all 789 real candidates:
raw correlation with `fpocket_drug` is real (ρ=0.173, p=9.9e-7) — but
**controlling for pocket size (`n_res`) via OLS residualisation drops it
to ρ=−0.044, p=0.212**, indistinguishable from zero. Mode shift's own
correlation with druggability is a shared-size artifact, not a genuine
relationship — once size is accounted for, the two really are
independent, confirming the one premise this task's own Scope named as
"the entire reason for adding it," even though that independence does
not translate into ranking power.

### Real bug found and fixed at the source, disclosed

`task0254_fpocket_variance_and_crypticity.crypticity` still assumed
`p["resnums"]` was a bare-int set — [[TASK-0298]] changed
`fpocket_candidates`'s own output to `(chain, resnum)` tuples (a real
chain-collision fix) without updating this downstream consumer, which
crashed on first use here. Fixed to handle both shapes defensively.
Every existing caller ([[TASK-0260]], [[TASK-0266]], [[TASK-0268]]) ran
before [[TASK-0298]] landed, so their own already-published numbers are
unaffected by this fix — not silently invalidated, checked by date, not
assumed.

### Not done

Docker was briefly down mid-task (this register's own fpocket/EvoEF2/
P2Rank now run containerized, [[TASK-0285]]) — caught immediately via a
`fpocket exited 1` failure rather than a silent bad number, Docker
Desktop restarted, the affected run re-verified clean before any number
above was trusted. `task0282`'s own `METRICS`/sweep was not touched, per
this task's own amended Constraint — mode shift stays outside that
family; whether it is worth integrating (with [[TASK-0300]]'s own
cluster-mean selection fix, not the defective row-mean one) is a Lane-B-
after-landing follow-up, not resolved here.

**Script:** `scripts/task0303_enm_mode_shift.py`. **Data:**
`results/tasks/0303_enm_mode_shift/mode_shift.json`. **Also touched:**
`scripts/task0254_fpocket_variance_and_crypticity.py` (the
`crypticity()` tuple-format fix above, a shared-module bug fix, not new
scope).
