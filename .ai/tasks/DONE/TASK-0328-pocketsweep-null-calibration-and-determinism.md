# TASK-0328 — pocketsweep.py: non-reproducible null seed, and a null shape that flatters smooth scores

- Status: Done
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

## Done

**2026-09-06, Implementer C.** Scope note (this task's own Owner is Oussema,
who owns the `allosteric` branch — same convention as [[TASK-0327]]):
nothing on that branch was pushed to or altered. Worked from a local git
worktree at `origin/allosteric` (confirmed `f257789`, current HEAD at claim
time, matching this task's own Upstream line exactly), copied the 4 stored
sweep artifacts + `pocketsweep.py` into this repo's own results tree
(`__WORK_IN_PROGRESS__/results/tasks/0328_pocketsweep_null_recalibration/upstream_artifacts/`),
worktree removed after. The fix and the re-run both live in *this* repo, not
upstream — landing the one-line patch on `allosteric` is Oussema's call.

### No PDB refetch, no fpocket, no eigh needed — the expensive physics was
never the thing that had to be redone

`pocketsweep.py`'s own null computation only ever consumes two objects it
already stores per protein: `ranks` (182 cells × n_seeds, rank 1 = top
score) and `y` (the truth labels). Reproduced its exact rank-sum arithmetic
(`(RK[:,pos].sum(1)-off)/denom`, `top5 = rank<=5`) from the stored `ranks`
directly — validated line-by-line before trusting it further: recomputed
the *original* (uniform, buggy-seed-replaced-with-a-fixed-one) null for 8
spot-checked proteins and compared against the stored `p_auc` — 0.141 vs
0.14, 0.44 vs 0.46, 0.624 vs 0.62, 0.746 vs 0.79, 0.023 vs 0.02, 0.0 vs 0.0,
0.297 vs 0.305, 0.024 vs 0.015 (`upstream_artifacts/` + spot-check
transcript in this file's own commit). Close enough (Monte Carlo noise at
different B/seed, same true null) to confirm the rank-sum reimplementation
is correct, not a rewrite that happens to look plausible.

### Defect 1 (non-reproducible seed) — fixed, in a patch this task hands to
Oussema rather than applies

`hash(w["name"])` is process-salted (`PYTHONHASHSEED` confirmed unset
anywhere in the branch). Replaced with
`int(hashlib.sha256(name.encode()).hexdigest(),16) % 2**32` — a one-line
upstream diff, written out in full as `POCKETSWEEP_PATCH` at the bottom of
`task0328_pocketsweep_null_recalibration.py`. **Proven, not asserted, to
matter**: `test_task0328_...py::test_broken_hash_seed_is_NOT_reproducible_across_processes`
runs the *original* scheme in 3 separate subprocesses and asserts they
disagree (they do) — a negative control proving the reproducibility test
below would actually have caught Defect 1, per [[TASK-0319]]'s standing
finding that an unverified checker isn't verified.
`test_deterministic_seed_reproduces_byte_identical` asserts the fixed
scheme gives literally identical floats across two independent runs — not
eyeballed, asserted, per this task's own Planned Validation.

### Defect 2 (null shape) — reused this register's own compactness-null
machinery, in the form this dataset already provides for free

[[TASK-0158]]/[[TASK-0190]]/[[TASK-0201]]'s `compact_patch()` draws a null
positive set as the nearest-by-3D-distance residues to a random center.
This pipeline already contains its own compact spatial units without
needing a structure refetch: each fpocket/PASSer *pocket* is by
construction a spatially contiguous cluster, and `seed_pocket[k]` (already
stored) names which pocket every seed belongs to. **Checked, not assumed,
that this is the right generalization**: the REAL positive sets in this
data are themselves concentrated in 1-3 pockets (52/110 single-pocket,
37/110 spanning 2, 20/110 spanning 3, 1/110 spanning 5 in round 1; similar
in round 2) — a null drawn as whole pockets (accumulated in random order
until the required count is reached, trimming only the last pocket added)
reproduces that same 1-3-pocket spread by construction, which a pure
3D-radius patch would not obviously do without refetching every structure.
This is this register's own established compactness-null principle,
applied in the dataset-native unit this specific pipeline already computes
— **not a new hypothesis or a new statistic**; the "if anything is new,
consider a hypothesis" reminder was checked against this and does not
apply, since TASK-0158/190/201 already own this principle in
`physics.md`/the register's standing null-construction convention.

### Result — both nulls, B=2000, same rank-sum statistic, same proteins,
same kpos, deterministic seeds

| | round 1 (n=110) | round 2, veto (n=80) |
|---|---|---|
| mean null max-AUC, **uniform** (this task's re-derivation) | 0.740 | 0.763 |
| mean null max-AUC, **pocket-block (compact)** | 0.821 | 0.846 |
| BH-FDR 5% survivors, uniform | 45/110 | 33/80 |
| BH-FDR 5% survivors, **pocket-block (compact)** | **0/110** | **1/80** |

**More extreme than this task's own cited motivating measurement** (11/55,
4/40 from an external circular-shift-null re-run, not independently
reproduced there). Read plainly: essentially none of the round-1 survivors,
and only 1 of the round-2 (veto) survivors, clear a null that respects the
same spatial-clustering structure the real positives themselves show.
**Difference from the external estimate flagged, not glossed over**: a
whole-pocket-block null is a stricter compactness match than a circular
shift over 3D coordinates — it also captures pocket-level *score*
correlation (seeds in the same detected pocket tend to score similarly
under a spatially smooth operator, not just tend to be close in space),
which a coordinate-only shift would not fully capture. Both are legitimate
readings of "compactness-matched"; this task's own number is the stricter
one, reported as such, not as the only possible one.

**Uniform-null numbers kept, not deleted** (this task's own Constraint) —
both rows above stand side by side in `result.json`.

### Verification

- `../.venv/bin/python3 -m pytest scripts/test_task0328_pocketsweep_null_recalibration.py -q` → 3 passed.
- Re-ran the main script twice end to end; `result.json` byte-identical
  both times (`diff` empty) — the reproducibility claim holds at the
  full-pipeline level, not just in the isolated unit test.
- `draw_pocket_block_null`'s exact-kpos guarantee re-checked externally
  (not just its own inline `assert`) across 15 proteins × 20 draws each —
  no duplicate indices, no under/overshoot.

### Not done / explicitly out of scope

- Did not push `POCKETSWEEP_PATCH` to the `allosteric` branch, and did not
  re-run the actual `pocketsweep.py` pipeline (fpocket + 12-Hamiltonian
  eigh sweep) — not needed, since the null recomputation only touches
  already-stored `ranks`/`y`, and re-running the full physics is Oussema's
  compute budget to spend, not this task's to assume.
- Did not update `PIPELINE_CURRENT.md`/`ABLATIONS.md`/the veto-pipeline
  README on the `allosteric` branch — same ownership reason as
  [[TASK-0327]].
- `TASK-0330` (the across-protein per-family operator-choice correction,
  named in this task's own "Credit where the design is already right"
  section) is explicitly out of scope here — a different multiplicity axis.

**Files**: `__WORK_IN_PROGRESS__/scripts/task0328_pocketsweep_null_recalibration.py`,
`__WORK_IN_PROGRESS__/scripts/test_task0328_pocketsweep_null_recalibration.py`,
`__WORK_IN_PROGRESS__/results/tasks/0328_pocketsweep_null_recalibration/{result.json,upstream_artifacts/}`.

**Moved TODO/IN_PROGRESS -> DONE.**
