# TASK-0327 — Build the PASSer-only and random-order reference arms the pipeline design already specifies

- Status: TODO
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
