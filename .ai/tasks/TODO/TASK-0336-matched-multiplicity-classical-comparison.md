# TASK-0336 — The 1022-protein classical comparison is not multiplicity-matched, and may not be metric-matched

- Status: TODO
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
