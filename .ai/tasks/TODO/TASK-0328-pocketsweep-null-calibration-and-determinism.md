# TASK-0328 — pocketsweep.py: non-reproducible null seed, and a null shape that flatters smooth scores

- Status: TODO
- Owner: **Oussema** (owns the file) — Reviewer thread has the reproduction
- Priority: High — one defect blocks the challenge's own artifact requirement
- Filed: 2026-09-06 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0327]], [[TASK-0158]], [[TASK-0190]], [[TASK-0201]], [[TASK-0319]], [[TASK-0314]]
- Upstream: `allosteric` branch `f257789`,
  `allosteric/results/veto_pipeline/pocketsweep.py:386`

## Defect 1 — the null is not reproducible run to run (confirmed)

```python
rng = np.random.default_rng(abs(hash(w["name"])) % (2**32))
```

`hash()` on a `str` is salted per process. `PYTHONHASHSEED` is set **nowhere in
the branch** — verified by `git grep PYTHONHASHSEED f257789`, zero hits. Every
null in every stored JSON was drawn from a seed that will not recur, so no
reported p-value can be regenerated.

This is not only a science defect: the challenge's required artifact list names
**deterministic seeds** explicitly. Fix is one line — hash the name with
`hashlib.sha256(...).digest()` or seed from an explicit constant plus an index.

## Defect 2 — the null scatters labels uniformly; the truth is a contiguous block

```python
pos = rng.permutation(n)[:kpos]
```

A real pocket is a spatially contiguous set of residues and every CTQW score is
spatially smooth, so a smooth score beats *scattered* labels more easily than
*clustered* ones. The null is therefore softer than the alternative it is meant
to exclude. This register built compactness-matched nulls for precisely this
reason — [[TASK-0158]], [[TASK-0190]], [[TASK-0201]] — and that machinery
should be reused rather than re-derived.

An external re-run of the identical max-over-cells statistic against a
circular-shift null preserving block structure (B=2000) reported:

| | uniform null | compactness-matched |
|---|---|---|
| round 1, BH-FDR 5% survivors | 24 / 55 | **11 / 55** |
| round 2 + veto, BH-FDR survivors | 13 / 40 | **4 / 40** |
| mean null max-AUC (round 1) | 0.734 | 0.776 |

Roughly half to two-thirds of the AUC survivors do not survive a correctly
shaped null. **Not independently reproduced here** — treat as the motivating
measurement, and let this task's own re-run be the authority.

## What the stored artifacts already say (reproduced here, both shards)

`s14_r{1,2}_k10_h2_{0,1}.json`, read directly. Note an external analysis of the
same files reported ~half these counts by reading one shard of two; the medians
match exactly, so the qualitative picture below is not in dispute.

| | round 1 | round 2 (veto — the headline config) |
|---|---|---|
| records / scored / errors | 138 / 110 / 28 | 138 / 80 / **58** |
| P@5 ≥ 0.8, raw count | 34 | 43 |
| **of those clearing their own P@5 null** | **8** | **0** |
| median base rate | 0.123 | 0.206 |
| median observed max P@5 | 0.600 | 0.800 |
| median **null** max P@5 | 0.537 | 0.682 |
| p_auc < 0.05 (uncorrected) | 56 / 110 | 37 / 80 |

**The veto raises the base rate rather than the discrimination.** Observed max
P@5 goes 0.600 → 0.800 and its own null goes 0.537 → 0.682 alongside it; the
gap barely moves, and after the veto **not one protein clears its own P@5
permutation null.** The veto also drops 58 of 138 proteins.

`p_p5` and `p_auc` were computed and stored per protein by the same script that
produced the counts. The significance column exists — it was not carried into
the reported numbers.

## Credit where the design is already right

The statistic is `max` over all 182 cells compared against a **null max** over
the same 182 cells. That is a correct within-protein multiplicity correction
and should be stated as such — it is stronger than the register's own default.
What it does *not* correct is the across-protein per-family operator choice;
that is [[TASK-0330]].

## Intent Contract

- Outcome: deterministic seeding landed; every stored p-value regenerated under
  it; the compactness-matched null run alongside the uniform one, both reported.
- Constraints: do not delete the uniform-null numbers — report both, so the
  size of the null-shape effect is visible rather than silently corrected.
- Planned Validation: re-running the script twice must produce byte-identical
  p-values. Assert it, don't eyeball it — [[TASK-0319]]'s standing finding is
  that a checker ships with a test proving it fails on a seeded violation.
