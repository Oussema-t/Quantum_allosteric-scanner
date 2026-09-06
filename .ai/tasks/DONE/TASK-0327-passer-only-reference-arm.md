# TASK-0327 — Build the PASSer-only and random-order reference arms the pipeline design already specifies

- Status: Done
- Owner: **Oussema** (owns `allosteric` branch) — Reviewer thread available to cross-check
- Priority: **Highest — this is the one number that decides what the pipeline is**
- Filed: 2026-09-06 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0325]], [[TASK-0320]], [[TASK-0305]], [[TASK-0254]], [[TASK-0287]]
- Upstream: `allosteric` branch, commit `f257789`,
  `allosteric/results/veto_pipeline/pocketsweep.py`

## Why this is first

`allosteric/results/veto_pipeline/PIPELINE_DESIGN.md` §S5 specifies **three**
reference arms: chance, random-residue-order through the same veto, and
**PASSer #1 alone with no walk**. Only the label-permutation null was built.
The one arm that decides whether the walk earns its place was designed and
never run.

This register reached the same conclusion independently and from the other
direction. [[TASK-0325]] gated fpocket candidates by druggability and measured
every arm inside the surviving set: the **gate** moved random-within-gate from
2.5% → 11.4% top-1, a 4.5× gain with no walk involved, while the CTQW did not
beat random inside its own gate (below it at two of four gates). A selection
stage that carries the result is the failure mode this register has already
measured once. The v2 pipeline has a stronger gate (PASSer, ~90% coverage) and
the same open question.

## Intent Contract

- Outcome: for the identical post-stage-2 candidate sets, the identical cohort
  and the identical P@5/AUC definitions, four numbers reported side by side:
  1. **PASSer score alone**, no CTQW at any stage, veto on and off.
  2. **Random residue order** through the same veto.
  3. **Chance floor** from the per-protein positive count (see below).
  4. The pipeline as reported.
- Why required, not assumed: if arm 1 lands near arm 4, stages 3 and 5 are
  decoration and the finding is "PASSer plus a crypticity veto works" — which
  is a real, defensible, publishable instrument and fits §2 of the submission.
  If arm 4 clears arm 1, the walk has earned its place nine days out. Either
  answer is usable; not knowing is not.
- In Scope: `pocketsweep.py` already computes everything needed — `pockets`
  carries PASSer's own ordering, `y` carries the labels, `ranks` carries the
  per-cell orderings. This is a scoring pass over stored artifacts, not a
  re-run of the walk.
- Out Of Scope: changing the pipeline, adding operators, re-tuning the veto.
- Constraints And Invariants:
  - **Report the chance floor next to every P@5.** With ~9 surviving
    candidates and 4 positives, random ordering gives P@5 ≈ 0.44; with 5
    positives, ≈ 0.56. A threshold count without its floor is not a result.
    The stored `base` field (median 0.123 round 1, 0.206 round 2) sets this
    per protein.
  - Family-level aggregation stays mandatory — CAS0002 is 28 structures of one
    protein, per the upstream README's own caveat.
- Planned Validation: the PASSer-only arm must reproduce the upstream README's
  own stage-1 claim (drug pocket in the top-10 for ~90% of proteins) as a
  positive control before its ranking numbers are trusted.

## A metric incomparability to settle in the same pass

`pocketsweep.py` computes P@5 over **seeds (residues)**:
`TOP5=np.argsort(-S,axis=1)[:,:5]`, `y` per seed. [[TASK-0305]] measured CTQW
P@5 = 0.0056 against a random baseline of 0.0171 on 108 ASBench structures —
a different denominator over a different object. **The two numbers do not
calibrate each other in either direction**, and the ~150× apparent jump between
them is at least partly a change of metric, not of method. State which
definition each reported number uses, or the comparison will be made for us by
a reviewer.

## Notes for whoever picks this up

PASSer is a live web API (`https://passer.smu.edu/api`, ensemble model) and
`allosteric/datasets/passer_cache.json` already holds 399 KB of cached
rankings. This register recorded PASSer as **never built**
(`ALGORITHM_REGISTER.md` §F rates it 3; `PLAN.md` still carries it as an open
box) — that record is now stale, and [[TASK-0325]]'s stated blocker
("`fpocket ∩ PASSer` is not runnable today") is lifted. Update both.

## NOT YET CRITIC-REVIEWED — cite only the corrected, held-out numbers below, and even those pending review

**Added 2026-09-06 per direct reviewer feedback, before this task's own
numbers could be cited anywhere further** (they already were, once,
inadvertently — see the "A confound found, then a correction to the
correction" section below): "the obvious comparison is the wrong one,
and it flatters [PASSer]." The reviewer was right about the mechanism
(ASBench train/test leakage). **This task's own first fix was itself
wrong** — it over-corrected by also excluding CASBench, which
PASSer's own papers treat as an external test set, not training data;
the properly-cited fix restores CASBench to the held-out pool
(n=44-64, not n=18-25) and finds PASSer's advantage shrinks from the
leaky headline but survives, decisively. **Cite the held-out numbers
(28.1%/40.9% pre/post-veto), never the full-cohort ones (40.6%/55.2%),
and still put a Critic review gate on this task** before either travels
further — the citations are now precise, but the two-step self-correction
above is exactly the kind of thing a second reader should verify
independently before this becomes load-bearing anywhere. This
banner should be removed only once that review has run, not once
someone finds the number convenient.

## Done

**2026-09-06, Implementer A.** Claimed by override on explicit user
instruction (this task was already claimed by "Reviewer thread";
released/overridden per `claim.py`'s own `--force --reason` convention,
disclosed here rather than silently taken). Note on scope: this task's
own `Owner` is Oussema (who owns the `allosteric` branch); nothing on
that branch was pushed to or altered — the work below is a read-only
scoring pass over `allosteric`'s already-stored artifacts (commit
`f257789`, confirmed current HEAD of `origin/allosteric` at claim time),
run from a local git worktree, with the analysis script and its output
copied back into *this* repo's own results tree rather than committed
upstream. Oussema/Reviewer thread should still cross-check, per the
task's own stated review structure — flagging that explicitly, not
skipping it because the number came out clean.

### Method

`allosteric/results/veto_pipeline/pocketsweep.py`'s own `top_pocket()`
(mean-of-members) is defined but **never called** in `main()` — the
checked-in per-cell output has no pocket-level rank baked in at all, and
`top_pocket()` also contradicts `PIPELINE_DESIGN.md`'s own stated S3
rule ("pocket rank = rank of its BEST residue... averaging is
size-biased"). Flagged, not silently used. Implemented the design doc's
own rule instead, in a new read-only script,
`reference_arms.py` (copied here:
`__WORK_IN_PROGRESS__/results/tasks/0327_passer_reference_arms/`):

**Key identity, proved once and used throughout, not per-arm**: under a
"best member wins" rule, the top-ranked pocket for any residue-score
vector is *exactly* whichever pocket contains the single top-ranked
residue overall — no other pocket's best member can exceed the global
max. This collapses two things to closed forms instead of simulation:
- **The real pipeline's per-cell prediction** = look up which pocket
  owns the residue with `ranks[cell][i]==1` (verified: every stored rank
  vector, all cells, both round-1 and round-2 shards, is a genuine
  1..n permutation — checked directly, not assumed).
- **Random residue order through the same veto** = `P(hit) = |drug
  pocket| / n_total_candidate_seeds`, cross-checked against an actual
  10-protein × 2000-rep Monte Carlo shuffle (max abs. error 0.019,
  round 1; 0.016, round 2 — the closed form holds).

Truth/drug pocket per protein: `argmax(n_drug, drug_frac)` among
candidate pockets, accepted only if `drug_frac ≥ 0.25`
(`PIPELINE_DESIGN.md`'s own "argmax rule" acceptance bar) — proteins
failing this bar are excluded from all four arms' denominators (this
*is* the "coverage" positive control, see below), not silently kept
with an undefined truth pocket.

### Positive control (Planned Validation) — passes, close to the claimed number

Coverage (a valid drug pocket present among the candidate list at all):
**87.3%** pre-veto (96/110 scoreable proteins), **83.75%** post-veto
(67/80) — close to, if not exactly, the upstream README's own "~90%"
stage-1 claim. Read as a pass (same ballpark, not an exact
reproduction the two different measurement methods would even be
expected to agree on bit-for-bit) rather than silently assumed.

### Result — the four arms, side by side

| arm | pre-veto (round 1, n=96) | post-veto (round 2, n=67) |
|---|---|---|
| (3) chance = 1/n_pockets | 12.4% | 25.3% |
| (2) random residue order, same veto | 17.5% | 32.4% |
| **(1) PASSer alone, no walk** | **40.6%** | **55.2%** |
| (4) pipeline as reported — pooled over cells | 9.3% | 16.2% |
| (4) pipeline as reported — per-protein majority (design doc's own criterion 3) | 0.0% | 1.5% |
| (1) PASSer alone — family-level majority | 38.2% | 55.0% (of 40 families) |
| (4) pipeline — family-level majority | 0.0% | 0.0% (of 40 families) |

**Arm 1 does not land near arm 4 — it clears it by 2.5× to 37× depending
on aggregation level, at every level tested.** This is a sharper, more
decisive answer than the task's own framing anticipated ("if arm 1 lands
near arm 4, stages 3 and 5 are decoration"): arm 1 does not merely match
arm 4, it dominates it, including beating the random-order-through-veto
null (arm 2) — the walk's own residue ranking, at the pocket-rank-1
task, performs *worse than chance given the veto's own pocket-size
distribution*, not merely no-better-than-PASSer. **Per the design's own
pre-registered decision rule (S5, "beating (a) but not (b) means the
veto works and the walk does not"): the veto/PASSer combination clears
both chance and random convincingly; the walk clears neither** — the
CTQW stage (S2/S3) is actively subtracting value at this task, not
merely failing to add it, on the identical candidate sets both arms
were scored against.

**This table's own exact magnitude (2.5-37x) does not survive the
confound found next, but the direction does — read the following
section for the corrected, properly-cited, still-decisive numbers
before quoting "2.5-37x" as the takeaway.**

### A confound found, then a correction to the correction — precise citations settle it

Per direct reviewer feedback (2026-09-06, relayed after this task's
first pass): *"the obvious comparison is the wrong one, and it
flatters [PASSer]."* Checked, and largely correct, but it took two
tries to get the fix itself right — recorded here in full rather than
smoothing over the false step, per this project's own no-silent-fix
convention.

**Live-verified citations** (per this project's own
`PAPER_CITATION_PROTOCOL.md` discipline — fetched from the publisher
page/PMC directly, not recalled):

- Xiao, S.; Tian, H.; Tao, P. **"PASSer2.0: Accurate Prediction of
  Protein Allosteric Sites Through Automated Machine Learning."**
  *Front. Mol. Biosci.* **2022**, *9*, 879251.
  DOI: [10.3389/fmolb.2022.879251](https://doi.org/10.3389/fmolb.2022.879251).
  Trained on ASD (90 proteins, quality-filtered) + ASBench's
  core-diversity set (138 proteins).
- Tian, H.; Xiao, S.; Jiang, X.; Tao, P. **"PASSer: fast and accurate
  prediction of protein allosteric sites."** *Nucleic Acids Res.*
  **2023**, *51*(W1), W427–W431.
  DOI: [10.1093/nar/gkad303](https://doi.org/10.1093/nar/gkad303).
  This is the **"ensemble" model** — `passer_cache.json`'s own cache
  key (`"pdb|chain|ensemble"`) matches this paper's model naming, not
  PASSerRank's. Trained on ASD (207 proteins) + ASBench core-diversity
  (138); **CASBench (1,049 proteins after filtering) held out as an
  external test set, not used to fit the model** (stated explicitly in
  the paper's own Methods).
- Tian, H.; Xiao, S.; Jiang, X.; Tao, P. **"PASSerRank: Prediction of
  Allosteric Sites with Learning to Rank."** *J. Comput. Chem.*
  **2023**. DOI: [10.1002/jcc.27193](https://doi.org/10.1002/jcc.27193)
  (preprint: [arXiv:2302.01117](https://arxiv.org/abs/2302.01117)).
  Trained on ASD (207, 80/20 split); **CASBench again an external test
  set** (ASD-overlap explicitly removed by the authors); **ASBench
  explicitly not used for training** in this specific paper.

**Net, across all three papers in the PASSer lineage: ASBench is
consistently training data; CASBench is consistently the authors' own
held-out test set, not training data.** My first correction (posted
above the strikethrough-equivalent note below) wrongly lumped both
together as "trained/validated on" and excluded both from the
held-out subset — an over-correction, not the fix the citations
actually support. Re-run with the citation-correct definition
(`LEAKY_SOURCES = {"asbench"}` only, `casbench` restored to the
held-out pool):

| arm | pre-veto, held-out (n=64) | post-veto, held-out (n=44) |
|---|---|---|
| (3) chance = 1/n_pockets | 12.8% | 27.3% |
| (2) random residue order, same veto | 18.4% | 36.3% |
| (1) PASSer alone, no walk | **28.1%** | **40.9%** |
| (4) pipeline as reported — pooled over cells | 8.9% | 15.7% |

**Corrected reading: PASSer's advantage over the pipeline is real and
survives on properly-defined held-out data (nearly 3x pre-veto,
~2.6x post-veto) — smaller than the leaky full-cohort numbers (40.6%/
55.2%) but not the near-total evaporation my first, over-corrected
pass reported.** PASSer also still clears both chance and the
random-order-through-veto null on this held-out set at every point
(28.1%&gt;18.4%&gt;12.8% pre-veto; 40.9%&gt;36.3%&gt;27.3% post-veto) — the
design's own pre-registered decision rule (S5: beat both (a) chance
and (b) random) is satisfied by PASSer here, not just by a training-
contaminated number. The pipeline does not clear it either way
(8.9%/15.7%, below its own random null in both rounds). **This is now
a properly-powered (n=44-64, not n=18-25), correctly-cited, and still
decisive result: on data ASBench-leakage cannot explain, PASSer alone
still beats the CTQW pipeline by a wide margin, and the pipeline still
does not clear chance or random.**

Updated analysis script (citations + corrected `LEAKY_SOURCES` in the
module docstring) + all three readings (full cohort, first
over-corrected held-out, final citation-correct held-out):
`__WORK_IN_PROGRESS__/results/tasks/0327_passer_reference_arms/
{reference_arms.py,reference_arms_result.json}`.

### The metric incompatibility, settled

This is a **pocket-level** metric: is the single correct pocket, out of
a small candidate set (mean ~4-10 post-selection), ranked #1 by
whichever residue among all its members scores best. [[TASK-0305]]'s
CTQW P@5=0.0056 is a **residue-level** metric: are any of the top-5
residues, out of the whole protein (hundreds), truth residues. Different
object, different denominator, different chance floor (12-25% here vs.
~1.7% there) — the ~150× apparent gap between the two headline numbers
this task's own filing flagged is a metric-definition difference, not a
contradiction between the two findings. Both point the same direction
(CTQW near or below its own floor), measured two different ways.

### Constraints honored

Nothing in the pipeline changed; no operator re-tuned; no veto
re-designed. Family-level aggregation reported alongside protein-level
throughout, not substituted for it. Chance floor reported next to every
other number, per this task's own Constraint, not left implicit.

### Not done / explicitly out of scope

- Did not recompute or challenge the upstream README's own residue-level
  P@5≥0.8/≥0.6 family-clearing counts (19/32/etc.) — those use a
  different metric (see above), not re-derived here.
- Did not push `reference_arms.py` to the `allosteric` branch — copied
  into this repo's own results tree instead (see Scope note above);
  landing it upstream is Oussema's call.
- Did not update `PIPELINE_CURRENT.md`/`ABLATIONS.md` on the
  `allosteric` branch itself, for the same reason.
- **Did not verify the `cryptobench`/`pocketminer`/`casbench`-is-held-out
  assumption against PASSer's actual training manifest** (unavailable
  to this task) — read from three published papers' own stated
  Methods sections (DOIs above, fetched live, not recalled), which is
  strong evidence but not the manifest itself. This is the single
  largest remaining uncertainty and the first thing a Critic pass
  should check.
- **Did not mint a hypothesis-register entry for this finding.** Given
  the reviewer's own reminder to consider one for anything new: this
  finding is a strong candidate (a real train/test leakage confound in
  an external comparator, found and partially corrected in the same
  task) — but landing it while still gated by an open Critic review
  would repeat the exact mistake being corrected here. Propose after
  the gate clears, not before.

**Files**: `__WORK_IN_PROGRESS__/results/tasks/0327_passer_reference_arms/
{reference_arms.py,reference_arms_result.json}`. Updated (this repo,
`bartosz` branch): `__WORK_IN_PROGRESS__/ALGORITHM_REGISTER.md` (PASSer
entry), `.ai/tasks/PLANS/PLAN.md` (external-baseline checkbox).
