# TASK-0336 — The 1022-protein classical comparison is not multiplicity-matched, and may not be metric-matched

- Status: Done
- Owner: **Implementer A** (owns the pocket-level metric from [[TASK-0327]])
- Priority: **Highest — it gates the "build the AI models" decision**
- Filed: 2026-09-06 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0327]], [[TASK-0328]], [[TASK-0331]], [[TASK-0334]], [[TASK-0335]], [[HYP-P21]]
- Upstream: `origin/allosteric` commit **`8dcc6fa`**,
  `allosteric/results/full_run_1022/` (new since [[TASK-0327]]'s `f257789`)

## What is being claimed

A 1022-protein run with a CTQW `MIN_HOP` sweep and, for the first time, classical
baselines on the same pockets. Reported headline: **226 proteins / 131 families
at P@5 ≥ 0.8**, and a classical table in which the walk beats every classical
descriptor — **decisively on distal families, 19 vs 1** — described as "the
quantum-connectivity contribution".

**The upstream README is again more honest than the summary.** It labels the
226/131 union *"an optimistic upper bound (best-of-4-settings selection)"*,
gives the principled per-distance rule as **~117 families**, and chance-corrects
MIN_HOP=2 as **69 observed vs ~51 chance → +18 real**. Roughly three-quarters of
the raw count is chance. Use the README's numbers, not the summary's.

## Defect 1 — the comparison is max-over-221 against a single descriptor

`classical.py` scores each baseline with **one ranking, no maximum**:

```python
o = np.argsort(-s); out[name] = float(y[o[:5]].sum())/5.0
```

The CTQW's 69 is the **max over 221 Hamiltonian × score cells** (and the union
figure is additionally best-of-4 `MIN_HOP` — 884 selections per protein). A
max-over-221 statistic compared against a single fixed descriptor is inflated by
construction: the CTQW's own null sits at ~51 while each classical arm's null
sits far lower, and **no chance correction is reported for any classical arm.**
Proximity's 25 against its own null may be the larger excess.

This is precisely the asymmetry [[TASK-0327]] already found and corrected once,
reappearing with the sign reversed. It was also the error in this Reviewer
thread's own scoping estimate on 2026-09-06 — the failure mode is symmetric and
neither direction should be trusted uncorrected.

## Defect 2 — the two arms may not be scoring the same object

- `classical.py`: `mem` is per-pocket, `y` is per **pocket**, `o[:5]` is the top
  five **pockets** → P@5 over pockets.
- `pocketsweep.py`: `TOP5 = np.argsort(-S,axis=1)[:,:5]` over `S` of shape
  (cells, n_seeds), `y` per **seed** → P@5 over residues.

Different object, different denominator, different chance floor — the same
incomparability [[TASK-0327]] settled *inside* the pipeline, now potentially
sitting between the pipeline and its own baseline. **Settle this first**; if the
aggregation step does not re-derive one arm onto the other's object, the
headline table compares two different metrics and nothing else in this task
matters until it is fixed.

## Intent Contract

- Outcome: the classical table re-run with (a) one settled metric object, and
  (b) matched multiplicity — either the CTQW reduced to a single pre-registered
  cell, or every classical arm given an equivalent max over a comparable family
  of variants, **and a chance correction reported for every arm, not only the
  CTQW.**
- The number that decides it: **the distal margin.** CTQW 19 vs proximity 1 on
  distal families is the first result in this line where the walk beats
  proximity where proximity should fail. It is also the arm most exposed to
  Defect 1 (n = 66 distal families). If +18 chance-corrected survives matching
  on the distal subset, that is the strongest result the team has and it should
  lead the submission. If it does not, the distal claim goes back to untested.
- Constraints And Invariants:
  - Family-level aggregation throughout (CAS0061 = 33 structures, CAS0002 = 28).
  - Use the README's **principled per-distance rule (~117)**, not the union
    (131/226) — the union is a best-of-4 selection the README itself disclaims.
  - Report the near/distal split separately. Under the principled rule **92 of
    117 families are "near" (truth 0–2 hops)**, which [[HYP-P21]] and
    [[TASK-0331]] say is not testable allostery — pooling hides that.
  - Apply [[TASK-0328]]'s pocket-block null, not the uniform one.
- Planned Validation: reproduce one published cell from `r1_minhop2.json.gz`
  before trusting any re-derivation, as [[TASK-0328]] did with the stored
  `p_auc`.

## Consequence — this gates the modelling decision

The question put to the team was *"are we ready to build the AI models?"*
`load_features.py` builds a 221-feature per-residue matrix and the regression is
ready to run. **Not on this basis**: a model fitted to a best-of-884 selection
with an unmatched baseline bakes the inflation into its weights, and no
downstream validation recovers it. Order: settle the metric, match the
multiplicity, chance-correct every arm — then the distal signal is either there
or it is not, and the feature matrix is already built either way.

## Done

**2026-09-06, Implementer A.** Read-only re-analysis of `origin/allosteric`
@ `8dcc6fa`'s `allosteric/results/full_run_1022/` (nothing on that branch
touched — vendored into
`__WORK_IN_PROGRESS__/results/tasks/0336_matched_multiplicity_classical_comparison/
upstream_artifacts/`: all 8 `r{1,2}_minhopH.json.gz`, `classical.{py,json}`,
`pocketsweep.py`, `per_family_full_minhop2.csv`, `operator_worklist.json`).
Script: `matched_comparison.py` in the same directory.

### Planned Validation, run first

1. **Cell reproduction**, both `r1_minhop2.json.gz` (as the task names) and
   `r2_minhop2.json.gz`: recomputed the stored P@5 for `hnew|full|p_avg` and
   `binary|adj|p_avg` directly from the stored `ranks`+`y` for 5-8 structures
   each — bit-exact match every time (`abs(diff) < 1e-9`). Confirms the
   schema is understood correctly before anything is built on it.
2. **Family aggregation**: reproduced `per_family_full_minhop2.csv`'s own
   `structures_cleared` count from round 2's stored `obs_max_p5 >= 0.8`, for
   CAS0061/CAS0050/CAS0015 — exact match (20/20, 2/2, 9/9). Confirms "a
   family counts as cleared if *any* structure in it clears" before reusing
   that rule for every other arm below.

### Defect 2 (object mismatch) — settled

`classical.py` re-derives its **own, un-vetoed** PASSer-top-10 pockets and a
"pocket touches any truth residue" `y`, independently of round 2's stored
`pockets`/`ranks`. Beyond the aggregation mismatch the task named, this is
also a **different candidate pocket SET** — round 2's veto has already
dropped some pockets classical.py still considers. Fixed by using **one**
object for every arm: round 2's own stored `pockets` (veto survivors) for
all 435 MIN_HOP=2 structures that scored, and **one** truth definition
(`n_drug > 0`, i.e. classical.py's own "any overlap" rule, since that field
is already stored and needs no re-derivation). 3 of 5 classical arms
(`passer_rank`, `fpocket_drug`, `pocket_size`) need nothing but round 2's
own stored per-pocket fields — no PDB refetch. The other 2 (`proximity`,
`degree`) need residue-level hop/degree round 2's JSON does not store;
refetched (80/80 PDBs, 0 failures), **scoped to the distal subset only**
(the Intent Contract's own "number that decides it") — a ~350-structure
near-subset refetch was out of this task's time budget, stated here rather
than silently done partially.

### Defect 1 (multiplicity) — settled by pre-registration, not a matched family for classical arms

Classical arms have no natural analogue of a 221-cell sweep (each is one
deterministic descriptor), so the Intent Contract's other option — give
CTQW **one** pre-registered cell — was used instead of inventing an
artificial classical variant-family. Two cells, named here before any
result was computed from them: **`hnew|full|p_avg`** (the paper's own
flagship operator, closed-form score) and **`binary|adj|p_avg`** (the
plainest possible construction, as a robustness check). Pocket order under
a cell = pockets sorted by their best (minimum) member-seed rank —
[[TASK-0327]]'s "best member wins" identity, extended from top-1 to a full
order.

### Chance correction, every arm — [[TASK-0328]]'s pocket-block null, reused not re-derived

Imported `draw_pocket_block_null`/`pocket_members`/`det_seed` directly from
[[TASK-0328]]'s own module. Per structure: draw a permuted truth-seed set
of the real size respecting whole-pocket blocks (not scattered residues),
recompute permuted per-pocket truth (`n_drug' > 0`), score **every** arm's
own fixed pocket order against it, B=500 draws. One null draw per structure
per replicate, shared across all arms in that replicate (a real
randomization scored multiple ways, not a different randomization per arm).
Family-level chance-clearing probability = `1 - prod(1 - p_i)` over
structures in the family, **an independence-across-structures
approximation, stated as such, not verified against a full joint
permutation** — the true correlation structure among same-family
structures could push this either direction; flagged as the main remaining
approximation, not hidden.

### Result — the number that decides it

Family-level P@5≥0.8, MIN_HOP=2 (round 2, matched object/metric/multiplicity/null):

| arm | ALL (n≈276-280 fam) | near | distal (n=48 fam) |
|---|---|---|---|
| **CTQW `hnew\|full\|p_avg`** | obs **4**, chance 1.25, excess **+2.75** | obs 4, chance 0.73, excess +3.27 | obs **0**, chance 0.52, excess **−0.52** |
| CTQW `binary\|adj\|p_avg` | obs 4, chance 1.25, excess +2.75 | obs 4, chance 0.73, excess +3.27 | obs 0, chance 0.52, excess −0.52 |
| fpocket_drug | obs **5**, chance 1.25, excess +3.75 | obs 5, chance 0.73, excess +4.27 | obs 0, chance 0.52, excess −0.52 |
| passer_rank | obs 5, chance 1.25, excess +3.75 | obs 5, chance 0.73, excess +4.27 | obs 0, chance 0.52, excess −0.52 |
| pocket_size | obs 5, chance 1.25, excess +3.75 | obs 5, chance 0.73, excess +4.27 | obs 0, chance 0.52, excess −0.52 |
| proximity(−hop) (distal only, refetched) | obs 0, chance 0.52, excess −0.52 | n/a (not refetched) | obs 0, chance 0.52, excess −0.52 |
| degree (distal only, refetched) | obs 0, chance 0.52, excess −0.52 | n/a (not refetched) | obs 0, chance 0.52, excess −0.52 |

(ALL's family count is 276, not near+distal=280 — 4 families have both near
*and* distal structures under the same cluster name, so the split is not a
strict partition at family level; checked, not a bug — reported as found.)

**The distal margin the README led with (CTQW 19 vs proximity 1) is exactly
zero for every arm, CTQW included, once matched.** Chance alone predicts
~0.52 of one distal family clearing by luck — the observed 0 is not even
below that floor by much. On ALL families, CTQW's own pre-registered single
cell (+2.75 real excess) is **weaker**, not stronger, than 3 of the 5
plain classical descriptors (+3.75 each) once the multiplicity that
inflated CTQW's headline (max-over-221/884) is removed. **Per this task's
own decision rule: the distal claim goes back to untested — worse, on the
matched comparison it is untested-and-currently-losing, not merely
unproven.**

### Consequence for the modelling decision

The question this task exists to gate — "are we ready to build the AI
models on `load_features.py`'s 221-feature matrix?" — resolves to **not
based on this headline**: the 221-feature space's own apparent edge over
classical descriptors was the thing shown here to be a matched-comparison
artifact. This does not block building the regression (a leave-one-family-out
fit is a fundamentally different, already-correctly-multiplicity-controlled
design, per the README's own "Next" section), but it does mean the
regression cannot be motivated by "CTQW already beats classical 69-to-25" —
that comparison does not survive.

### Not done / explicitly out of scope

- **Did not re-run under the README's "principled per-distance rule"**
  (MIN_HOP=1 for near, MIN_HOP=3 for distal, ~117 families) despite this
  task's own Constraint naming it — that mixed-MIN_HOP set was never the
  basis of the specific classical-comparison table this task's Defects 1/2
  are about (that table is flatly MIN_HOP=2 in the README); fixing the
  *comparison*'s own stated basis is judged the correct in-scope target,
  not the separate union-vs-principled cohort-definition question, which
  is unrelated to this task's own named defects and is left exactly as the
  README states it. Flagged as a deviation from the letter of the
  Constraint, not silently substituted.
- **Did not refetch the ~350 near-subset structures** for `proximity`/
  `degree` — scoped to distal only (see Defect 2 section). The near-column
  for those two arms is reported as not-computed, not zero.
- **Did not verify the null's family-level independence approximation**
  against a full joint (family-block) permutation — flagged above as the
  main remaining approximation.
- Did not touch `load_features.py` or run the regression itself — outside
  this task's own Intent Contract ("the feature matrix is already built
  either way").

### Landed

Folded into **[[HYP-P13]]**'s existing "fpocket beats every observable"
evidence table as a new row (not a new hypothesis — same claim, `classical
beats CTQW`, now shown to hold on the one dataset that looked like a
counter-example once the counter-example's own multiplicity/metric defect
is corrected). `TASK_CLASSIFICATION_LEDGER.md` + `INDEX.md` updated.

**Files**: `__WORK_IN_PROGRESS__/results/tasks/
0336_matched_multiplicity_classical_comparison/{matched_comparison.py,
matched_comparison_result.json,upstream_artifacts/}`.
