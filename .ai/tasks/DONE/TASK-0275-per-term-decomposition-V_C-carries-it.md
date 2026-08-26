# TASK-0275 — Decompose the potential terms: `V_C` alone beats CTQW, and we lumped it

- Status: TODO
- Assignee: unassigned (suggest Implementer A — owns TASK-0263, reuses its cached CV)
- Priority: **High — cheap, and it converts TASK-0263's headline into a much sharper and more credible claim**
- Filed: 2026-08-26 by Reviewer
- Related: [[TASK-0263]], [[TASK-0254]], [[TASK-0257]], [[TASK-0259]], [[TASK-0261]], [[TASK-0276]] (the same ceiling logic, at the discrimination level rather than the feature level)

## What TASK-0263 did, and what it hid

[[TASK-0263]] scored `H_new`'s potential terms as **one lumped block**
(`BLOCKS4 = ["geometry", "fpocket", "ctqw", "terms"]`) and got the register's
best constructive result: terms 0.751 vs CTQW 0.575, cluster-robust p=0.019.

It also computed per-term solo AUCs and stored them
(`per_term_auc.json`) but **never used the terms as separate attribution
categories.** Re-aggregating that file per term across the 20 targets:

| term | what it is | median AUC | >0.7 | max |
|---|---|---|---|---|
| **`V_C`** | **GNM dynamic cross-correlation centrality** — mean abs. normalised DCC, the standard allosteric-coupling measure (Haliloglu & Bahar 1999) | **0.6365** | **8/20** | 0.973 |
| `V_B` | B-factor penalty — raw experimental flexibility, no model | 0.5940 | 6/20 | 0.873 |
| `V_R` | — | 0.5323 | 0/20 | 0.699 |
| `V_M` | — | 0.5295 | 1/20 | 0.715 |
| `V_T` | — | 0.5142 | 0/20 | 0.548 |

**Two things the lumping concealed:**

1. **`V_C` alone (0.6365) already beats the whole CTQW (0.575).** The single
   strongest ingredient is the field's own classical allosteric-coupling
   metric, used directly as a per-residue score. `V_B` — pure deposited
   B-factors — is second. Three of the five terms are near chance.
2. **The terms are not redundant with each other.** All ten cross-term
   Spearman correlations over the 20 targets are weak (|ρ| ≤ 0.45; only
   `V_T`–`V_C` reaches p<0.05). Five distinct signals, not one — so a joint
   decomposition may show genuine complementarity that a single block cannot.

## Why this matters beyond tidiness

"Our potential terms beat our quantum walk" is a decent finding. "**The
standard classical allosteric-coupling measure, scored directly, beats the
quantum walk built on top of it**" is a much sharper, more citable, and more
credible one — and it names the specific physics rather than gesturing at a
bundle. It is also far harder for a reviewer to dismiss.

## Scope

- [x] Re-run [[TASK-0254]]'s Shapley with the five terms as **separate
      blocks** alongside geometry / fpocket / CTQW. That is 8 blocks — exact
      Shapley is 8! = 40,320 permutations per target, still cheap, but confirm
      the runtime before launching and use the n-block routine [[TASK-0260]]
      generalised rather than rewriting it. Timed first (~0.042s/`cv_auc`
      call, ~7 min projected for both flavours) — ran the full 8 blocks, the
      6-block reduction was not needed.
- [x] If 8 blocks is impractical, run the defensible reduction — not needed,
      see above.
- [x] Report **each term's contribution added last**, on top of geometry +
      fpocket + CTQW. The decision statistic, as everywhere in this register.
- [x] **The headline question**: does CTQW retain any added-last contribution
      once `V_C` specifically is in the model? [[TASK-0263]] found p=0.973
      against the lumped block; test it against `V_C` alone. See Done.
- [x] Reuse [[TASK-0263]]'s cached CV where possible — reused
      `potential_term_vectors` (flavour-agnostic, works unchanged on holo)
      directly; the CV cache itself could not be reused as-is because this
      task's own matched-common-set requirement (see below) recomputes every
      block on a different residue index set than [[TASK-0263]]'s own.
- [x] Cluster-robust significance ([[TASK-0261]]'s exact cluster-level
      permutation, 13 clusters).
- [x] Crypticity stratification, as every block since [[TASK-0260]].

## Apo AND holo — both flavours, added 2026-08-26

**Scope correction (Bartosz, 2026-08-26).** As first filed this task was
apo-only, which measures *performance* and says nothing about what these terms
could do given the right conformation. [[TASK-0276]] establishes a ceiling by
looking at holo; the same logic applies here, at the feature level, and is
more actionable because it names which physics is recoverable.

- [x] Compute every term **twice**: on the apo structure (performance, the
      real prediction task) and on the holo structure (ceiling). Computed on
      the **matched common apo/holo (chain, resnum) set**
      (`align_apo_holo`), not apo's own full residue set for the apo arm —
      required for a fair gap comparison (same node set both flavours,
      disclosed as a deliberate deviation from [[TASK-0263]]'s own full-apo
      numbers, see Done).
- [x] Report the **per-term apo→holo gap**. See Done.
- [x] **Pre-registered prediction**: tested, does **not** hold — see Done.
- [x] Also run the CTQW arm on holo. See Done.

### Leakage status per feature — not uniform, do not run a blanket holo sweep

| feature | holo arm | why |
|---|---|---|
| `V_C`, `V_B`, `V_R`, `V_M`, `V_T` | **run it** | protein-only quantities; they see the drug's structural imprint but not the drug. Ceiling, not predictor. |
| geometry (degree, euclid, hop) | **run it** | same status. |
| CTQW | **run it** | same status. |
| SASA | **run it**, flagged | burial changes on binding; the imprint is stronger here. |
| **fpocket** | **exclude, or report separately and label maximally leaky** | it is a cavity detector, and the holo cavity is drug-shaped. Scoring it on holo trivially recovers the label and measures nothing. |

**Every number from the holo arm is a ceiling and must be labelled as one in
`RESULTS.md`.** None of it may be reported as predictive performance, and none
of it may be mixed into the apo attribution table without a column heading
saying which flavour it came from.

## Relationship to [[TASK-0276]] — read together, not in isolation

The two are the same ceiling question at different levels:

- **This task** asks, per physical term, *how much performance is lost by
  having to use apo* — an attribution of the apo penalty across `V_C`, `V_B`,
  geometry, CTQW. Actionable: it names which physics is recoverable.
- **[[TASK-0276]]** asks whether the allosteric site is distinguishable **at
  all** in holo — an existence question, and the harder ceiling.

**If this task's holo arm shows large per-term gains while [[TASK-0276]] finds
no allosteric-vs-orthosteric separation, the two results are in tension, and
that tension is itself the finding**: the terms would be tracking *the drug's
structural imprint* rather than anything about allostery. Whichever of the two
runs second must check its result against the other's rather than reporting in
isolation.

[[TASK-0276]] was picked up before this note was written — **pass this
relationship to whoever owns it.**

## Acceptance

- [x] Per-term added-last values with cluster-robust p-values.
- [x] An explicit answer to "does CTQW add anything over `V_C` alone?" — in
      **both** the apo and holo flavours.
- [x] A per-term apo→holo gap table, every number labelled by flavour, with
      the pre-registered crypticity prediction judged.
- [x] A statement of whether the terms are complementary or whether `V_C`
      subsumes the rest.
- [x] `RESULTS.md`. Flag `documentation/CTQW_CONTRIBUTION_BRIEF.html` §04 for
      an update — do not edit it here. **Flagged in Done, not edited.**

## Constraint

If `V_C` subsumes the other four, say so — a one-term result is a *better*
finding than a five-term one, not a diminished version of it. And if some term
turns out to carry signal only in combination, that is genuine complementarity
and equally worth reporting.

## Done

**2026-08-26, Implementer B.** Full numbers in `RESULTS.md`'s own section
(not duplicated verbatim here) — summary:

**Method note, stated up front**: both flavours are scored on the
**matched common apo/holo (chain, resnum) residue set**
(`allostery.superpose.align_apo_holo`), not on apo's own full residue set
for the apo arm — required so the apo-vs-holo gap compares an identical
node set both ways, not apo's full graph against holo's reduced one. This
means the apo-flavour numbers here are **not** a re-verification of
[[TASK-0263]]'s own apo numbers and differ from them, sometimes by a
non-trivial margin (checked directly, e.g. `DHPS_GC7` V_C: 0.392 →
0.586) — CTQW and the geometry block are graph-topology-sensitive, and
restricting to the common set changes the graph. Disclosed, not silently
different.

**8-block Shapley ran in full** (apo: geometry/fpocket/ctqw/V_B/V_T/V_R/
V_C/V_M; holo: the same minus fpocket, excluded per this task's own
leakage table). Timing confirmed first (~0.042s/`cv_auc` call), full run
~11 min for both flavours — the 6-block fallback was not needed.

**Headline — does CTQW add anything once `V_C` alone is in the model?**
No, in apo (as `V_C` alone predicted): AUC(`V_C`+ctqw) − AUC(`V_C` alone)
median **−0.0047**, cluster-robust p=0.30 — CTQW's own marginal is at or
below zero. On holo, a small, real, *positive* effect reaches marginal
significance: median **+0.0051**, p=0.037 — but the effect size (half a
percentage point of AUC) is not the "CTQW recovers value once given the
right conformation" result [[TASK-0263]]'s own filing flagged as the
sharper possible finding; it is a genuinely small, borderline-significant
nudge, reported at that size, not inflated. The **full 8/7-block
added-last marginal** (CTQW against every other block, not just `V_C`)
stays indistinguishable from zero in both flavours (apo median −0.0005
p=0.21; holo median +0.0016 p=0.69) — this is [[TASK-0263]]'s own original
finding (p=0.973 there, a different exact composition but the same
verdict), now confirmed against `V_C` specifically as well as the lumped
block.

**Are the terms complementary, or does `V_C` subsume the rest?**
Complementary, not subsumed — matching this task's own Constraint's
"equally worth reporting" framing. `V_C` carries the largest median
Shapley share among the five terms (apo +13.3%, holo +14.3%, both clearly
above `V_B`/`V_R`/`V_T`/`V_M`), but every other term still contributes a
real (if smaller) positive median share in at least one flavour — none is
driven to zero by `V_C`'s presence, consistent with [[TASK-0263]]'s own
finding that all ten cross-term correlations are weak. Geometry
(apo +26.5%, holo +24.6%) and fpocket (apo +10.5%, apo-only) remain the
largest single contributors overall — `V_C` is the strongest of the five
physical terms, not the strongest predictor in the full model.

**Per-term apo→holo gap vs. the pre-registered crypticity prediction: does
not hold.** Prediction was a negative correlation (larger gap on cryptic
targets). Measured, cluster-permutation ([[TASK-0261]]'s method):
`V_B` ρ=−0.376 p=0.14 (right direction, not significant); `V_R` ρ=**+0.464
p=0.025** (significant, **wrong direction**); `V_C` ρ=+0.166 p=0.57; `V_M`
ρ=+0.001 p=0.999; CTQW ρ=+0.038 p=0.87. `V_T` excluded from this test — a
real structural fact, not noise: `V_T` depends only on residue count, not
coordinates or B-factors, so on the matched common set (same n both
flavours by construction) its gap is identically 0.0 for all 20 targets,
confirmed directly. **Per this task's own Scope**: crypticity is not what
the apo penalty is made of, at the per-term level — [[TASK-0259]]'s own
ρ=−0.771 correlation (an aggregate, different-observable finding) does not
decompose cleanly onto these five physical terms.

**A bigger, unplanned finding underneath the crypticity-gap null**:
whether *holo acts as a ceiling above apo at all*, for these 7 non-leaky
blocks. A direct like-for-like check (apo scored on the SAME 7 blocks as
holo, fpocket excluded from both so the comparison is fair) shows apo's
own median full AUC (0.896) is numerically *higher* than holo's (0.834),
apo ahead on 14/20 targets — not statistically significant
(cluster-robust p=0.10), so **not** a claim that apo beats holo, but a
clean absence of the assumed holo advantage. `results/tasks/
0275_term_decomposition_apo_holo/apo_7block_no_fpocket_for_fair_ceiling_
comparison.json` has the full per-target numbers.

**Relationship to [[TASK-0276]], checked as this task's own Scope
requires**: [[TASK-0276]] completed concurrently (Implementer A) and found
a REAL positive signature — `V_C` (the same term this task centers on)
significantly discriminates allosteric from orthosteric sites within holo
structures, in two independent protein families (KRAS_G12C, HCV_NS5B).
That is not the "no separation" arm this task's own tension table names,
so there is no contradiction to flag — but the two results combine into a
sharper joint reading than either alone: `V_C`'s signal is real and
robust ([[TASK-0276]]), and it does not require the bound conformation to
be present (this task: no significant apo→holo gain) — **the physics `V_C`
captures is already available from the unbound structure**, which is the
actionable, favourable version of [[TASK-0276]]'s own ceiling question at
the feature level.

**`documentation/CTQW_CONTRIBUTION_BRIEF.html` §04 flagged, not edited**,
per this task's own Acceptance: needs the sharper `V_C`-vs-CTQW headline
(both flavours) and the apo/holo ceiling-null finding.

**Bug fixed before the real run**: `NAMPT_NPA1R`'s own already-documented
altloc defect ([[TASK-0249]]'s own fix) — this new script had not yet
inherited it; added the same global `prody.parsePDB(altloc="all")`
monkeypatch, verified against the same target that broke [[TASK-0271]]'s
own first run for the identical reason.

**Artifacts**: `scripts/task0275_term_decomposition_apo_holo.py`;
`results/tasks/0275_term_decomposition_apo_holo/` (per-term AUC both
flavours, 8-block and 7-block Shapley, headline cluster tests, per-term
gap + crypticity correlation, the fair-ceiling addendum); `RESULTS.md`;
this file.

**Not attempted, explicitly out of scope**: `SASA` as an additional block
(not part of [[TASK-0254]]'s original 3-block set or this task's own named
8; [[TASK-0276]] already covers it at the allosteric-vs-orthosteric level);
re-fitting [[TASK-0263]]'s own cache in place (superseded by the matched
common-set requirement, see Method note above).
