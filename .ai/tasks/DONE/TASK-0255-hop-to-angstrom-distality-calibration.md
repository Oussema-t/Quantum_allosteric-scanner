# TASK-0255 — Does MIN_HOP ≥ 2 mean anything in Ångströms? Calibrating our distality criterion

- Status: Done
- Assignee: unassigned (suggest Implementer — small, self-contained, high leverage)
- Priority: **High — MIN_HOP is a parameter the joint pre-registered protocol proposes to freeze, and we have never validated it**
- Filed: 2026-08-24 by Reviewer
- Related: [[TASK-0246]] (hop-shell profile), [[TASK-0242]]/[[TASK-0244]] (MIN_HOP=2 in the two-stage design), [[TASK-0169]] (the KRAS 3.75 Å finding), [[TASK-0209]]

## The question

[[TASK-0246]] measured where pocket residues actually sit relative to the
active site, in **graph hops**:

| hop | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8+ |
|---|---|---|---|---|---|---|---|---|
| enrichment | 0.93× | **1.63×** | 1.38× | 1.15× | 0.69× | 0.18× | 0.15× | 0.00× |

78% of pocket residues sit at hops 2–4. The register's whole premise is that
allosteric sites are **distal** to the active site, and `MIN_HOP = 2` is the
operational definition of "distal" in the two-stage design.

**Nobody has ever checked what hop 2 is in Ångströms.**

[[TASK-0169]] already found the failure mode on KRAS_G12C: minimum Cα–Cα
distance between an active-site residue and a pocket residue is **3.75 Å** —
van der Waals contact range — while the pair is nominally "distal". A pocket
can be several graph hops away and still fold directly against the active site
in 3D.

If `MIN_HOP ≥ 2` routinely corresponds to 6–10 Å rather than the 15–20 Å that
would constitute genuine allosteric separation, then the two-stage protocol's
distality filter is not filtering for distality, and **both threads would be
freezing a parameter that does not mean what its name says.**

## Scope

- [x] For every target in [[TASK-0243]]'s frozen set, compute the joint
      distribution of graph-hop distance and **minimum heavy-atom Euclidean
      distance** to the active site, per residue.
- [x] Report per hop shell: median, IQR, and **minimum** Euclidean distance.
      The minimum is the load-bearing statistic — it is what catches the KRAS
      case, which a median would hide.
- [x] State what fraction of `MIN_HOP ≥ 2` candidate pockets have any residue
      within **8 Å** of the active site (contact-adjacent despite passing the
      filter).
- [x] Pre-register a genuine-separation bar (the external suggestion is
      15–20 Å minimum) and report how many frozen-set targets meet it. If very
      few do, that is a benchmark finding on the scale of [[TASK-0169]].
- [x] Recommend a replacement or supplementary criterion — e.g. MIN_HOP plus a
      minimum-Euclidean floor — with the measured consequence of adopting it
      (how many candidates and targets it removes).
- [x] Re-run [[TASK-0242]]'s two-stage arm under the recommended criterion so
      the cost of the change is measured, not assumed.

## Acceptance

- [x] Hop↔Ångström calibration table across the frozen set.
- [x] The fraction of nominally-distal pockets that are contact-adjacent in 3D.
- [x] A concrete recommendation for the joint protocol, with its measured cost.
- [x] `RESULTS.md`; and a note to send to the collaborating thread, since this
      changes a parameter both sides would otherwise freeze unexamined.

## Constraint

This is not an argument for making the criterion stricter to produce a
different verdict. Report the calibration and its consequence in both
directions — if `MIN_HOP ≥ 2` turns out to correspond to genuine separation,
that retires a live concern and should be said as clearly as the alternative.

## Done

**2026-08-25, Implementer B.** New `scripts/task0255_hop_angstrom_calibration.py`.
Reuses `task0242_two_stage_dryrun`'s own `prep()`/`fpocket_candidates()`
(seed/pocket resolution, candidate pockets) and [[TASK-0243]]'s frozen
22-target config, altloc="all" monkeypatch. `hop_from_seed`'s own sign
convention flipped back to true hop counts, same as `task0242.run()`.
20/22 targets usable (HIV_INTEGRASE_MUT871/916 skipped — the empty
active-site seed [[TASK-0249]]/[[TASK-0253]] are independently
re-auditing at its source).

**Real bug found and fixed before trusting any number**: `allostery.
labels.protein_heavy_atoms_by_residue`'s own `resnum_to_seq_idx` dict is
keyed on bare residue number only — correct for its existing single-chain
callers, but it silently collapses same-numbered residues across chains
in a multi-chain target. Confirmed directly on GAC_BPTES (3 chains, 1223
residues, only 411 unique resnums): the bare-resnum map left 812/1223
residues with **zero** heavy atoms mapped, which would have corrupted
exactly the statistic this task exists to report. Re-implemented locally,
keyed on `(chain, resnum)` — not by editing the shared helper, which has
its own established callers and is out of this task's scope. Re-verified:
0/1223 NaN after the fix, true-pocket distance unchanged (that one number
happened to survive the bug by luck).

### Hop → Ångström calibration (pooled, all residues, all 20 usable targets)

| hop | n | median | IQR | **min** |
|---|---|---|---|---|
| 1 | 1574 | 3.18 Å | [1.38, 3.76] | **1.21 Å** |
| 2 | 2287 | 7.50 Å | [6.35, 8.94] | **2.09 Å** |
| 3 | 2644 | 12.14 Å | [10.66, 13.79] | **2.79 Å** |
| 4 | 1964 | 16.88 Å | [14.96, 18.58] | **3.55 Å** |
| 5 | 1158 | 21.72 Å | [19.23, 23.57] | **7.02 Å** |
| 6 | 820 | 26.47 Å | [23.85, 28.81] | **10.42 Å** |
| 7 | 435 | 31.48 Å | [27.39, 33.91] | **7.73 Å** |
| 8+ | 382 | 40.96 Å | [36.42, 46.54] | **17.63 Å** |

**Both things are true, and both are reported.** The *median* grows
monotonically with hop shell (3.18 Å → 40.96 Å) — hop is a real, usable
aggregate distance signal, not noise. But the *minimum* at hop 2 is
**2.09 Å** — closer than a hydrogen bond — and stays under 4 Å through
hop 4. `MIN_HOP ≥ 2` guarantees nothing about any single candidate's real
separation; it only guarantees the graph-contact-defined path is ≥2 edges,
which a folded protein can satisfy while the residue's own side chain
reaches back to touch the active site through space.

### The answer key itself, not just candidates, fails a genuine-separation bar

Pre-registered per this task's own Scope: 15 Å and 20 Å, the external
suggestion. Per-target true-pocket (the **answer key**, not a candidate)
minimum heavy-atom distance to the active site:

| target | min dist | ≥15 Å | ≥20 Å |
|---|---|---|---|
| GAC_BPTES | 6.66 Å | fail | fail |
| GAC_CPD12 | 6.75 Å | fail | fail |
| DHPS_GC7 | 1.33 Å | fail | fail |
| PF_ATCASE | 1.36 Å | fail | fail |
| KSHV_PROTEASE_24Q/25G | 3.04 Å | fail | fail |
| SUMO_E1_FHJ | 2.81 Å | fail | fail |
| HCV_NS5B_VRX/VR1 | 19.72 Å | **PASS** | fail |
| HCV_NS5B_POO/CMF | 17.94 Å | **PASS** | fail |
| FBPASE_94D | 2.88 Å | fail | fail |
| FBPASE_95S | 1.35 Å | fail | fail |
| TRP_SYNTHASE_F6F/F19 | 1.29 Å | fail | fail |
| SMYD3_DIPERODON | 8.33 Å | fail | fail |
| PKR_MITAPIVAT/AG946 | 11.69 Å | fail | fail |
| MKK7_IBRUTINIB | 1.32 Å | fail | fail |
| NAMPT_NPA1R | 2.78 Å | fail | fail |

**Meet ≥15 Å: 4/20 (20%). Meet ≥20 Å: 0/20 (0%).**

Spot-checked the extreme case (DHPS_GC7, 1.33 Å), not assumed correct:
the closest true-pocket residue (A239) sits at hop **1** from the active
site — an immediate contact-graph neighbor of seed residue A238. Confirmed
not a bug in this task's own code — it is a real property of the
consensus pocket-label pipeline: the labelled "distal" pocket routinely
includes residues immediately flanking the active site. This is
[[TASK-0169]]'s KRAS_G12C finding (3.75 Å Cα–Cα), independently found to
be the **register-wide norm on the frozen set, not a single-target
outlier** — 16/20 targets fail even the looser 15 Å bar, and the true
pocket is within 8 Å of the active site (contact-adjacent by this task's
own bar) on the large majority of targets.

### Candidate-level contact-adjacency

Of 492 fpocket candidates surviving `MIN_HOP ≥ 2` across the 20 usable
targets: **115 (23.4%) have a residue within 8 Å of the active site** —
contact-adjacent despite nominally passing the distality filter.

### Cost of adopting the pre-registered bars as a hard replacement/supplement

| bar | targets scoreable | candidates surviving |
|---|---|---|
| `MIN_HOP≥2` only (current) | 14/22 | 407 |
| `MIN_HOP≥2` AND ≥15 Å | 6/22 (**−8**) | 80 (**−327**) |
| `MIN_HOP≥2` AND ≥20 Å | 4/22 (**−10**) | 42 (**−365**) |

Two-stage ranking under each (denominator = 22 targets attempted
throughout, per this register's own standing convention):

| criterion | ctqw MRR | fpocket_drug MRR | hop_cov MRR | random MRR |
|---|---|---|---|---|
| `MIN_HOP≥2` (current) | 0.161 | **0.344** | 0.093 | 0.122 |
| + ≥15 Å (n=6) | 0.136 | 0.099 | 0.066 | 0.117 |
| + ≥20 Å (n=4) | 0.136 | 0.106 | 0.100 | 0.109 |

Not read as a ranking result — n=4–6 is too small to support any
comparison; included only to show the cost is not free even setting
target-count aside (fpocket_drug's own advantage, this register's
strongest arm, collapses under the stricter bars, though at this sample
size that could as easily be noise as a real interaction).

### Recommendation

**Not a hard 15–20 Å floor as a replacement.** Two independent reasons,
not one: (1) the cost is severe — a 15 Å floor removes 57% of currently
scoreable targets and 80% of surviving candidates; 20 Å removes 71%/90%;
(2) more fundamentally, the **answer key itself fails the bar** in 16/20
(15 Å) to 20/20 (20 Å) targets — a hard filter built from this bar would
in those cases exclude the correct candidate from the pool entirely, which
is worse than an uninformative filter, it is an actively wrong one. A
"genuine separation" gate cannot be validated against ground truth that
does not itself clear it.

**Recommended instead**: (a) `MIN_HOP ≥ 2` stays as the primary distality
gate — its median trend is real, not spurious; (b) **minimum heavy-atom
Euclidean distance is reported as a required disclosed statistic
alongside every scored candidate and the true pocket**, not a pass/fail
gate, so "distal" is never silently read as "genuinely separated" again;
(c) treat distality the same way [[TASK-0244]] already treats hop for
CTQW — as a covariate/competing feature (already the case in this
register's own composite baseline, [[TASK-0249]]'s `hop_onehot`), not a
binary filter, since this task's own data shows a binary gate at any
Ångström threshold either passes almost everything (weak) or excludes
the ground truth (wrong).

### Constraint honoured

Reported in both directions, as required: `MIN_HOP` is **not** spurious
(the median calibration is real and monotonic) but it also does **not**
mean what "distal" implies at the level of any single candidate (the
minimum is single-digit Å through hop 4, and the answer key itself
routinely fails a genuine-separation bar). Neither side of this was
softened to produce a cleaner story.

### Not done

- Two-stage arm not re-run under the *recommended* criterion (b)/(c)
  above, since (b)/(c) are disclosure/covariate changes, not new hard
  filters with a candidate set to re-rank — there is nothing to re-run
  that isn't already the register's own established composite-baseline
  design ([[TASK-0249]]). The two hard-bar re-runs that *are* reported
  (15 Å, 20 Å) are the ones explicitly asked for by Scope, to show their
  cost, not because either is the recommendation.
- Did not extend the calibration to targets outside [[TASK-0243]]'s
  frozen set (e.g. the preliminary 9-target set) — out of this task's
  own stated scope.

**Script:** `scripts/task0255_hop_angstrom_calibration.py`. **Data:**
`results/tasks/0255_hop_angstrom_calibration/calibration.json`.
