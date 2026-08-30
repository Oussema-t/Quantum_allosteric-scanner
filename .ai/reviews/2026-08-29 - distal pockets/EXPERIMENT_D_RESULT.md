# Experiment D — APOP-style ENM global mode shift

Handover §6 item 5 called this "the highest-value remaining experiment": the
discrimination review reports 92/104 top-3 for *global mode frequency shift +
local hydrophobicity*, and names mode shift as the component that might work in
the **cryptic** stratum, where hydrophobic density provably does not.

**Result: mode shift is a genuine, size-neutral, largely independent pocket
signal — but it works in the open stratum, exactly where hydrophobic density
already works, and it is not significant in the cryptic stratum. The review's
premise for running it is not supported. It is, however, the first thing in this
register that looks like it *might* have cryptic signal, and the cohort is too
small to resolve it.**

---

## 1. Method

For each fpocket candidate, fill the pocket with dummy nodes at its alpha-sphere
centres, rebuild the elastic network, and measure how much the softest global
modes stiffen:

```
GNM, C-alpha nodes, cutoff 7.3 A, 10 softest non-trivial modes
shift = mean_i ( lambda'_i - lambda_i ) / lambda_i
```

Truth = max-Jaccard candidate, detection Jaccard ≥ 0.3 (handover §2). Both
candidate settings. Cluster-collapsed to apo structure before any p-value.

### The confound, controlled three ways

Adding nodes always stiffens the network and a bigger pocket adds more nodes —
precisely the failure that killed volume and SASA under max-Jaccard truth. So:

| variant | control |
|---|---|
| `raw` | none — APOP as published |
| `kfix` | alpha spheres k-means-reduced to **exactly 8** nodes for every pocket, so node count cannot carry size |
| `resid` | mode shift regressed on volume **within target, on ranks**; true pocket scored on the residual |

Correlation with pocket volume: raw ρ = 0.44 / 0.55, kfix ρ = 0.33 / 0.32
(default / `-m 2.8`). kfix reduces the confound but does not remove it, which is
why `resid` exists.

## 2. Result

Cluster-collapsed Fisher p on the within-target percentile of the true pocket:

| setting | stratum | K | n det | median kfix | median resid | p (kfix) | p (resid) |
|---|---|---|---|---|---|---|---|
| default | open | 4 | 6 | 0.051 | 0.051 | **0.0052** | **0.0132** |
| default | cryptic | 5 | 5 | 0.533 | 0.600 | 0.55 | 0.65 |
| `-m 2.8` | open | 4 | 6 | 0.067 | 0.080 | **0.0060** | **0.0113** |
| `-m 2.8` | cryptic | 6 | 8 | 0.279 | 0.237 | 0.20 | 0.15 |

**The open-stratum signal survives every control.** Fixed node budget,
volume-residualisation, both candidate settings, cluster-collapsed — p stays in
the 0.005–0.013 band. This is not a size artifact.

**The cryptic stratum does not reach significance at either setting.**

## 3. Mode shift is more robust than hydrophobic density

The most useful practical finding. Under candidate-set expansion
(default → `-m 2.8`, roughly 2.5× more candidates):

| | default | `-m 2.8` |
|---|---|---|
| hydrophobic density, open rank-1 | **6/6** | 3/6 |
| mode shift (kfix), open Fisher p | 0.0052 | 0.0060 |

Arm 1's headline degrades badly when the candidate set grows; mode shift does
not move. Since handover §6 recommends adopting `-m 2.8` as the default
candidate generator, **this matters for which feature the register should build
on.** Hydrophobic density is the better ranker at default settings; mode shift
is the more stable one at the settings the register is about to adopt.

## 4. The APOP combination does not reproduce

They are not redundant — median within-target ρ(mode shift, hyd density) = 0.069
(default), 0.481 (`-m 2.8`). Two largely independent signals. And yet:

| setting | hyd alone | Borda(mode shift, hyd) |
|---|---|---|
| default | 7/11 | 4/11 (kfix), 2/11 (raw) |
| `-m 2.8` | 3/14 | 3/14 (kfix), 2/14 (raw) |

**Combining never beats the better component.** An unweighted Borda sum averages
a strong ranker with a weaker one and lands in between; that is arithmetic, not
biology. A properly *weighted* combination might do better — but weighting means
fitting, and at K_eff = 4–6 clusters this cohort cannot support a fitted weight
that anyone should believe. The review's 92/104 figure comes from a cohort that
can; this one cannot.

So: the 92/104 claim is neither confirmed nor refuted here. What is shown is
that **the parameter-free version of it fails**, and that the cohort cannot
honestly test the fitted version.

## 5. The cryptic result is suggestive, not null

Worth distinguishing from the conservation arms, which were flatly negative:

| | median percentile (cryptic) | detectable at K=6 |
|---|---|---|
| conservation | 0.66–0.69 (wrong side of chance) | ≤ 0.173 |
| mode shift `-m 2.8` | **0.237–0.279** | ≤ 0.173 |

Conservation is nowhere near, and pointing the wrong way. Mode shift is on the
right side of chance and within striking distance of the detection boundary —
it just cannot clear it with 6 clusters. Combined with the fact that cryptic
detection itself rises 5/11 → 8/11 at `-m 2.8`, so more cryptic targets are
scoreable than ever before, this is **the first candidate cryptic signal the
register has produced.**

The honest statement: *underpowered, direction favourable, worth re-testing on a
cohort that can resolve it.* That is a different recommendation from the one
handover §6 anticipated, which expected mode shift to either work or not.

## 6. Recommendations

1. **Do not adopt the APOP combination.** The parameter-free form is
   destructive; the fitted form is untestable here.
2. **Report mode shift alongside hydrophobic density, not merged with it.** They
   are independent, and which one wins depends on the candidate setting.
3. **Mode shift is the cryptic hypothesis worth carrying to a bigger cohort.**
   Cryptic K_eff must exceed ~10 clusters for this to be resolvable; the current
   6 cannot do it whatever the truth is.
4. **Revisit the per-target `enm_cutoff`.** These runs use a uniform GNM 7.3 Å;
   the repo has per-target cutoffs from `build_H_new` that were not available in
   this container. A tuned cutoff could move the cryptic numbers either way and
   should be checked before the cohort conclusion is trusted.

## Artifacts

`expD_modeshift.py`, `expD_followup.py`, `expD_default.json`,
`expD_-m_2.8.json`, `run_fpocket.py`, `prep_apo.py`, `fp_full.json`
(all 40 fpocket runs with alpha-sphere coordinates — the thing `hyd_cache.json`
lacked).
