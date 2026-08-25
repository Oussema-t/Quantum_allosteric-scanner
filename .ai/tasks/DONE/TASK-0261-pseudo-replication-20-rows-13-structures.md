# TASK-0261 — 20 rows, 13 structures: every p-value in the frozen-set analyses is over-counted

- Status: Done
- Assignee: unassigned (suggest Implementer — mechanical but touches every headline number)
- Priority: **High — it affects TASK-0249, TASK-0254, TASK-0257, TASK-0259 and the collaborator brief**
- Filed: 2026-08-25 by Reviewer
- Related: [[TASK-0243]] (the frozen set), [[TASK-0249]], [[TASK-0254]], [[TASK-0257]], [[TASK-0259]], `documentation/CTQW_CONTRIBUTION_BRIEF.html`

## The defect

[[TASK-0243]]'s frozen set has **20 scoreable rows but only 13 distinct apo
structures**. Seven rows are a second ligand bound to an apo structure already
counted:

| apo PDB | rows |
|---|---|
| 7SBN | GAC_BPTES, GAC_CPD12 |
| 2PBK | KSHV_PROTEASE_24Q, KSHV_PROTEASE_25G |
| 2GIQ | HCV_NS5B_VRX, HCV_NS5B_VR1 |
| 2HAI | HCV_NS5B_POO, HCV_NS5B_CMF |
| 5LDZ | FBPASE_94D, FBPASE_95S |
| 1K7X | TRP_SYNTHASE_F6F, TRP_SYNTHASE_F19 |
| 7FS3 | PKR_MITAPIVAT, PKR_AG946 |

**Every apo-side score is identical within a pair** — geometry, CTQW, ENM
validity, hop distances, fpocket cavities all derive from the same apo
coordinates. Only the pocket label differs. These are not independent
observations for any apo-side statistic, yet every Wilcoxon and Mann-Whitney
test in the frozen-set analyses treats them as n=20.

Note this is *not* a curation error — two ligands on one target is legitimate
and informative. The error is purely in the **statistics**, which never
accounted for the clustering.

## First-pass measurement (Reviewer, 2026-08-25)

Re-run by averaging within each apo structure, n=13:

| statistic | n=20 (rows) | n=13 (structures) |
|---|---|---|
| CTQW added-last | −0.06%, p=0.5016 | +0.01%, p=0.7354 |
| geometry Shapley | +41.8%, p=0.0001 | +40.9%, p=0.0002 |
| fpocket Shapley | +8.0%, p=0.0032 | +8.0%, **p=0.0266** |
| CTQW Shapley | +11.2%, p=0.0333 | +14.3%, p=0.0327 |
| rho(apo-open, unexplained) | −0.771, p=0.0001 | −0.646, **p=0.0170** |

**No conclusion is overturned.** The headline null (CTQW adds nothing) is a
null either way — pseudo-replication cannot manufacture a null. But note the
direction: **the corrections cut against our own positive claims**, not
against CTQW. fpocket's significance and the crypticity correlation both
weaken materially while surviving.

## Scope

- [x] Do it properly rather than by averaging. Averaging within a cluster is a
      first pass, not the right method — use a cluster-robust test or a mixed
      model with apo structure as a random effect, and say which and why.
- [x] Re-run every frozen-set statistic that reports a p-value:
      [[TASK-0249]]'s composite-vs-CTQW (currently p=0.0137, n=20),
      [[TASK-0254]]'s added-last values for all three blocks,
      [[TASK-0257]]'s R2 paired comparison, [[TASK-0259]]'s subgroup tests.
- [x] Decide and document a standing rule for the register: does a second
      ligand on the same apo structure count as a new target? Our view is that
      it does for label-side questions and does not for apo-side ones — but
      the rule must be written down once and applied everywhere, not decided
      per analysis.
- [x] Check whether the same clustering exists in [[TASK-0216]]'s candidate
      set and the 15 register targets (CARDIAC_MYOSIN / CARDIAC_MYOSIN_TABLE1
      are a probable case).
- [x] Update `documentation/CTQW_CONTRIBUTION_BRIEF.html` with the corrected
      values, and add the clustering to its §09 "places your reproduction will
      diverge" list — a reproducing thread will hit exactly this.

## Acceptance

- [x] Every frozen-set p-value restated under the chosen clustering method,
      old and new side by side.
- [x] A written rule for what counts as an independent target.
- [x] Brief updated; §09 gains the clustering item.
- [x] An explicit statement of which conclusions changed. Current expectation:
      none, but two weaken.

## Constraint

Report this **before** the collaborating thread finds it. It is a real defect
in our statistics, we found it ourselves, and it corrects in their favour on
two of our claims. Volunteering it costs us little and is worth a great deal
to the credibility of everything else in the brief.

## Done

**2026-08-25, Implementer B.** New `scripts/task0261_cluster_robust_stats.py`.
Reuses, does not recompute, every underlying per-target statistic —
[[TASK-0249]]'s `headline_per_residue.json`, [[TASK-0254]]'s
`part_a_shapley_attribution.json`, [[TASK-0257]]'s `part_a_shapley_sasa.json`,
[[TASK-0259]]'s `profile.json` — this task only changes how significance is
computed from numbers already on disk.

**Premise checked before designing the fix, not assumed**: this task's own
filing states "every apo-side score is identical within a pair." Checked
directly against `config/candidate_targets_task0243.yaml`: **5/7 pairs use an
identical apo chain selection** (bit-identical apo-side quantities); **2/7**
(GAC_BPTES/GAC_CPD12, FBPASE_94D/FBPASE_95S) use a **different chain subset**
of the same deposited apo entry — correlated, not bit-identical (confirmed:
their `gnm_r` values differ, e.g. 0.697 vs 0.811). Doesn't change the
clustering unit (same PDB entry, overlapping chains, same crystallographic
origin — still clearly non-independent) but reported precisely rather than
repeating the slightly-overstated "identical" claim unchecked.

**Method chosen: exact cluster-level permutation, not a mixed model or
averaging.** With 13 clusters (6 singletons, 7 pairs) there is not enough
replication to fit a random-intercept variance component reliably — a mixed
model needs many more non-trivial clusters than 7 to avoid a degenerate fit.
Permutation makes no distributional assumption and is *exact* here: one-sample
and paired tests use cluster-level sign-flips (2^13=8,192 patterns, enumerated
exactly — the direct generalisation of Wilcoxon's own exact-enumeration logic
from rows to clusters); two-group and correlation tests use cluster-block
reassignment (exact via `itertools.combinations` when the outcome space is
small enough — true for every two-group test here, largest is C(13,10)=286 —
Monte Carlo, 40,000 draws, for the correlation tests where 13! is intractable).
This keeps every row's own contribution to the test statistic (unlike
averaging, which the task's own Scope explicitly rules out) while deriving the
null distribution's variability from the correct, cluster-level unit.

### Every re-run statistic, old vs. cluster-robust

| statistic | n=20 (or subgroup) p | n=13 clusters p | conclusion |
|---|---|---|---|
| [[TASK-0249]] composite vs CTQW (paired) | 0.0137 | 0.0449 | survives, more narrowly |
| [[TASK-0254]] geometry Shapley | 0.0001 | 0.0002 | unchanged |
| [[TASK-0254]] geometry added-last | 0.0002 | 0.0002 | unchanged |
| [[TASK-0254]] fpocket Shapley | 0.0032 | 0.0188 | survives, more narrowly |
| [[TASK-0254]] fpocket added-last | 0.0019 | 0.0042 | survives, more narrowly |
| [[TASK-0254]] CTQW Shapley | 0.0333 | 0.0420 | survives, more narrowly |
| [[TASK-0254]] CTQW added-last (headline null) | 0.5016 | 0.2170 | null either way |
| [[TASK-0257]] R2 paired (SASA − degree) | 0.4781 | 0.3354 | null either way |
| [[TASK-0259]] ENM valid>invalid (pre-registered direction) | 0.9674 | 0.9615 | unchanged — data run the other way |
| [[TASK-0259]] ENM valid vs invalid, **two-sided** (not pre-registered) | 0.0803 | **0.0420** | **crosses 0.05 — see below** |
| [[TASK-0259]] Spearman(ENM validity, CTQW added-last) | 0.6171 | 0.6325 | unchanged |
| [[TASK-0259]] CTQW added-last, ENM-valid only, vs 0 | 0.7820 | 0.8379 | unchanged |
| [[TASK-0259]] Spearman(apo crypticity, unexplained) | 0.0001 | 0.0005 | unchanged, still strongest correlate |

**No pre-registered conclusion flips.** The headline null (CTQW added-last)
is a null either way — pseudo-replication cannot manufacture a null.
Direction matches the Reviewer's own first-pass exactly: corrections cut
against **our own** positive claims (composite-vs-CTQW, fpocket, CTQW's own
Shapley share all weaken, two of them from "comfortable" to "narrow"), not
against CTQW.

**One caught mistake before it shipped**: my first pass compared the
row-level Mann-Whitney (one-sided, `alternative='greater'`, the pre-registered
direction) against a *two-sided* cluster permutation for the ENM valid/invalid
test, which manufactured an apparent "significance flip" (p=0.97→p=0.04) that
was actually just an artifact of comparing a one-sided p to a two-sided one.
Fixed by computing both sides identically at both levels — see table above.
The pre-registered direction stays solidly non-significant, unchanged
(0.9674→0.9615). **A genuine, exploratory, non-pre-registered finding survives
the fix**: the *two-sided* (or reverse-direction) version of the same test
moves from p=0.080 (already borderline at n=20) to p=0.042 (n=13 clusters) —
i.e. there is now borderline-significant evidence that CTQW's marginal is
*larger*, not smaller, on ENM-invalid targets. Reported as exploratory/post
hoc, not a new positive for CTQW — it further undercuts, rather than rescues,
the "give it a valid model" defence [[TASK-0257]] tested, since it says CTQW
isn't systematically failing where its physical model doesn't fit.

### Standing rule (Scope item 3)

A second ligand bound to an apo structure already in the set counts as a
**new target for label-side questions** (pocket identity, ranking,
druggability — these differ genuinely between rows) and does **not** count as
a new target for **apo-side questions** (ENM validity, geometry, any
statistic tested against zero or correlated across targets without
conditioning on the label) — cluster by apo structure for the latter, always,
written down once (this section + the brief's own new box) rather than
decided per analysis.

### Independence check elsewhere in the register (Scope item 4)

Checked directly, not assumed: the **15 register targets** [[TASK-0250]]
scored each use a **distinct apo PDB entry** — no shared-structure clustering
found. `CARDIAC_MYOSIN`/`CARDIAC_MYOSIN_TABLE1`, this task's own filing's
named "probable case," is **not** one — they use different apo entries
(8QYP vs 5TBY), not a shared structure; the filing's suspicion is corrected,
not confirmed. [[TASK-0216]]'s own 7-target candidate set likewise has 7
distinct apo entries. The clustering is isolated to [[TASK-0243]]'s frozen
22-target set.

### `documentation/CTQW_CONTRIBUTION_BRIEF.html` updated

- §01 decision-number stat-row: cluster-robust p added alongside each
  row-level p (geometry/fpocket/CTQW added-last).
- §04 main results table: new "p (n=13 clusters)" column; composite-vs-CTQW
  line updated with both numbers.
- New §04 subsection, "Every p-value above is over-counted, and here is the
  corrected version" — full table, method explanation, the exploratory
  ENM-direction finding (carefully caveated), the two independence checks,
  and the standing rule, all in one place ahead of §05.
- §05 R2 table: cluster-robust column added.
- §09: "Five places" → **"Six places your reproduction will legitimately
  diverge from ours"** — clustering added as item 6; new script listed.
- §10: new bullet, "every p-value in the frozen-set analyses was computed at
  n=20 rows against 13 distinct apo structures... self-caught and corrected."

### Not done

- No mixed-model comparison was built alongside the permutation method — the
  Scope's own "say which and why" was answered by choosing permutation
  outright (justified above: too few non-trivial clusters for a reliable
  random-intercept fit), not by running both and comparing.
- The exploratory ENM-direction finding is reported, not chased further
  (e.g. no attempt to build a larger ENM-invalid target set to test it
  properly at higher power) — flagged as the natural next step, not this
  task's own scope.

**Script**: `scripts/task0261_cluster_robust_stats.py`. **Data**:
`results/tasks/0261_cluster_robust_stats/cluster_robust_results.json`.
