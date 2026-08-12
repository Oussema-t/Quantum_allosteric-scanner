# TASK-0208 What actually changes between apo and holo — the cheap gate that decides whether the coupled-search route exists

## Context

- ID: TASK-0208
- Title: decompose the real apo→holo structural difference into backbone
  (φ/ψ) vs. side-chain (χ) components, and measure how **coupled** those
  changes are — the gate for [[TASK-0210]].
- Status: Done
- **Thread: Implementer A (science, original run) → Reviewer thread
  (recompute, 2026-08-07) → Architect (2026-08-12, write-up
  reconciliation only — no new computation).** Cheap, no search, no
  sampling — pure analysis of two deposited structures per target.
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: Reviewer thread + orchestrating user, 2026-08-06 — the "what would
  it actually take to transform apo into holo" question, reduced to its
  cheapest decisive measurement.
- Priority: **P0 for the new direction — it can close [[TASK-0210]] before a
  line of search code is written, and it is hours of work.**
- Dependency: none.

## Why this matters — it is a gate, not a survey

[[TASK-0204]]'s reformulation closed side-chain rotamer packing **on
complexity grounds**: exact minimization of a fixed-backbone packing MRF
costs `O(m·n^(tw+1))`, and on real pocket windows (m=12, n=15) the exact
global optimum lands in **0.001–0.159 s** against a naive `1e14.1` search
space.

That result has a precise boundary, and this task tests which side of it the
real problem sits on:

> The treewidth argument works because the interaction graph is **fixed**.
> Move the backbone and the graph itself becomes a variable — the elimination
> order is invalid and the tractability result does **not** transfer.

So the question that decides whether the coupled backbone+rotamer route is
real:

- **If the apo→holo change is dominantly side-chain-only** → the fixed-backbone
  result applies directly, at the same scale, and [[TASK-0210]] closes without
  being built. Same closure, cheaply, for the same reason.
- **If it is substantially backbone, and the backbone and side-chain changes
  are coupled** → the tractability argument genuinely does not reach it, and
  the route is open.

Neither answer is a disappointment. The first is a second, independent
confirmation of a closure the register already has. The second is the first
genuinely open computational route since the program began.

## The coupling question, stated precisely

"How different are apo and holo" is not the useful quantity — RMSD is already
known and says nothing about search difficulty. The useful quantity is
whether the required changes are **decomposable or frustrated**:

- **Decomposable**: each residue's change is individually favourable given the
  rest of apo. A greedy per-residue pass finds it. Easy, regardless of how
  many residues move.
- **Frustrated**: no single change is favourable alone; several must happen
  simultaneously to reach the holo basin. This is what makes combinatorial
  optimization hard, and it is the property that maps onto an Ising/QUBO
  formulation at all.

Frustration is measurable on two known structures without any search.

## Intent Contract

- Outcome: per target, (a) the backbone/side-chain split of the apo→holo
  change at and around the pocket, (b) a coupling/frustration statistic, and
  (c) an explicit gate verdict for [[TASK-0210]].
- Why required, not assumed: the entire coupled-search direction rests on the
  premise that real cryptic-pocket opening involves coupled backbone motion.
  That premise has never been measured in this register, and [[TASK-0185]]'s
  backbone-only result (pocket recovery is *not* rare, 1–8 draws) is weak
  evidence against it.
- In Scope:
  - Structural alignment apo↔holo reusing the register's own
    `superpose`/`_needleman_wunsch_map`/`chain_map_from_config` path — no new
    alignment code.
  - Per-residue φ/ψ and χ1..χ4 in both structures; the change decomposition
    at the pocket window and a matched distal control set.
  - **Backbone/side-chain attribution**: what fraction of the pocket's
    apo→holo heavy-atom displacement is reproduced by (i) applying only the
    holo χ angles to the apo backbone, vs. (ii) applying only the holo φ/ψ
    with apo rotamers. This is the load-bearing number.
  - **Coupling statistic**: for the residues that move, is each residue's holo
    conformation individually favourable on the apo background, or only
    jointly? Operationalize via the packing energy already available
    (EvoEF2, vendored) — swap one residue at a time to its holo rotamer on the
    apo backbone and record ΔE; then swap them jointly. **Large joint gain
    with individually-unfavourable singles is frustration**; additive ΔE is
    decomposition.
  - Run on all targets whose apo/holo pair is usable — noting [[TASK-0209]]'s
    finding that BCR_ABL1's 1OPL is pre-opened by myristate and is not a valid
    cryptic instance.
- Out Of Scope:
  - Any search, sampling, or optimization. This measures two known endpoints.
  - Building the coupled formulation — that is [[TASK-0210]], gated on this.
  - Predicting anything. Both structures are known; this is characterization.
- Constraints And Invariants:
  - **Pre-register the gate threshold before running**: what backbone
    fraction, and what degree of frustration, counts as "the fixed-backbone
    result does not transfer"? Write it in this file first.
  - The distal control set is mandatory — a pocket that changes no more than
    background is a finding, and without the control it is invisible.
  - Report per-target. A route that is open on one target and closed on
    three is a different proposal from one that is open everywhere.
- Planned Validation:
  - Reconstruct holo heavy-atom positions from (apo backbone + holo χ) and
    from (holo φ/ψ + apo χ); the two reconstruction errors must bracket the
    true apo→holo displacement. If neither reconstruction gets close, the
    decomposition is not capturing the change and the analysis is wrong.
  - Sanity: a residue with identical φ/ψ/χ in both structures must show zero
    attributed change.

## Pre-Registered Gate (written before any computation — 2026-08-07, Implementer A)

**Target set.** Mandatory: `KRAS_G12C` (4OBE/6OIM), `PTP1B` (8QYP/8QYR),
`CASPASE1` (1ICE/2FQQ) — all have a resolvable `drug_ligand` and a simple
`chains` list in `config/targets.yaml`. `BCR_ABL1` (1OPL/5MO4) is excluded:
[[TASK-0209]] found it pre-opened by myristate (apo druggability 0.566 >
holo 0.356), not a valid cryptic instance. Extend to `GLUCOKINASE`
(1V4S/3H1V) and `CASPASE7` (1F1J/1SHL) if cheap once the pipeline runs
clean on the mandatory 3.

**PTP1B's validity caveat, stated not silently assumed**: only
`KRAS_G12C` has been through [[TASK-0209]]'s own open/closed apo-validity
audit (confirmed valid: apo druggability 0.001 -> holo 0.886). `PTP1B` and
`CASPASE1`'s apo structures have *not* been through that audit here. PTP1B
is run anyway because this task's own TODO explicitly asks whether it —
the register's one surviving positive ([[TASK-0201]]/[[TASK-0203]]) — is
also the most coupled target; its result is reported with this caveat
attached, not silently treated as equal-confidence to KRAS_G12C's.

**Backbone/side-chain attribution** (reconstruction fractions, both
measured as heavy-atom RMSD reduction relative to the raw apo->holo
displacement at the pocket window):

- `side_chain_explained = 1 - RMSD(apo_backbone + holo_chi -> true_holo) / RMSD(apo -> true_holo)`
- `backbone_explained    = 1 - RMSD(holo_backbone + apo_chi -> true_holo) / RMSD(apo -> true_holo)`

Verdict per target:
- **Side-chain-dominant** (closes on TASK-0204 grounds) if
  `side_chain_explained >= 0.70` AND `backbone_explained < 0.50`.
- **Substantially backbone** (tractability boundary reached) if
  `backbone_explained >= 0.50` OR `side_chain_explained < 0.70`.

**Coupling/frustration statistic**, on the pocket window only (EvoEF2
`ComputeStability` whole-structure `Total` energy line — a design energy,
not a folding free energy, stated per this task's own Open Question):

- `sum_singles = sum_i ΔE_i`, each `ΔE_i` = `E(apo, residue i's side chain
  transplanted to its holo rotamer via local N/CA/C Kabsch fit)` minus
  `E(apo baseline)`, one residue swapped at a time, rest of the window
  left at apo's own rotamer.
- `joint = E(apo, all window residues transplanted simultaneously) -
  E(apo baseline)`.
- **Decomposable** if `|joint - sum_singles| < 0.30 * |sum_singles|` (a
  generous, explicitly-arbitrary 30% band for "additive" — no prior
  convention for this exact statistic exists in the register).
- **Frustrated** if `joint` is more favorable (more negative) than
  `sum_singles` by more than that band, i.e. `sum_singles - joint >=
  0.30 * |sum_singles|`. Reported as a stronger finding if at least one
  individual `ΔE_i > 0` (unfavorable alone) while `joint < 0`
  (favorable jointly) — the textbook frustration signature.
- If `sum_singles ~= 0` (no window residues change side chain
  meaningfully), the statistic is reported as `not_evaluable`, not forced
  through the ratio.

**Overall per-target gate verdict for [[TASK-0210]]**:
`OPEN` (coupled route genuinely untested by TASK-0204) requires
**substantially backbone AND frustrated**. Any other combination
(side-chain-dominant, or substantially-backbone-but-decomposable) is
`CLOSED` — a backbone change that is itself decomposable/greedy-findable
does not need a coupled QUBO either.

**Dihedral change magnitude** (cheap distal-control comparison, not the
expensive EvoEF2 statistic): mean `|Δφ| + |Δψ|` (backbone) and mean
`sum |Δχ_k|` (side chain) at the pocket window vs. a matched-size distal
control set (same count as the window, the residues in the common
correspondence set with the *largest* geodesic distance from the pocket
centroid). Pocket must exceed distal control on both to confirm the
pocket is the site of real conformational change, not just background
noise — a pre-registered sanity check, not the gate itself.

**Correction (found during the GLUCOKINASE extension run, 2026-08-07,
before any mandatory-target verdict was affected)**: the "Substantially
backbone" clause above (`backbone_explained >= 0.50 OR side_chain_explained
< 0.70`) is not mutually exclusive with "neither reconstruction is
dominant" — GLUCOKINASE measured `side_chain_explained=0.46,
backbone_explained=0.20` (neither clears its own bar), yet the literal OR
still forced `substantially_backbone`. Corrected to a clean 3-way
partition: `side_chain_dominant` (as above, unchanged) /
`substantially_backbone` if `backbone_explained >= 0.50` / `ambiguous`
otherwise. **Does not change any mandatory-target verdict** — KRAS_G12C
(0.733), PTP1B (0.539), CASPASE1 (0.524) all clear `backbone_explained >=
0.50` directly, independent of the OR clause. Flagged here rather than
silently patched, per this register's own precedent for pre-registration
defects found mid-run ([[TASK-0204]]'s criterion-#1 retraction).

**Validation** (per Planned Validation above): the two reconstruction
RMSDs must both be `<= RMSD(apo -> true_holo)` and neither can be `~0`
while the other is `~= RMSD(apo -> true_holo)` unless the true change
really is 100% attributable to one component — if both reconstructions
fail to approach the true displacement combined, the decomposition itself
is flagged broken and the target's gate verdict is withheld
(`not_evaluable`), not silently reported anyway.

## In Progress

Implementing `scripts/task0208_apo_holo_decomposition.py`.

## TODO

- [x] Pre-register the gate threshold in this file. **Before running.**
- [x] apo↔holo alignment + per-residue φ/ψ/χ extraction, both structures.
- [x] Backbone vs. side-chain attribution at pocket + distal control.
- [x] Reconstruction validation (both directions bracket the true displacement).
- [x] Coupling/frustration statistic: single-residue vs. joint ΔE.
- [x] Per-target gate verdict for [[TASK-0210]].
- [x] Check the [[TASK-0201]] link: is PTP1B — the one target with a surviving
      positive — also the most *coupled*? If so, say so; it would connect the
      register's one positive to this direction mechanistically.
      **Nominally yes, not claimed as confirmed — see Done.**

## Dependency

- [[TASK-0204]] (In Progress) — the fixed-backbone tractability result whose
  boundary this task probes.
- [[TASK-0209]] — target validity; do not run on a pre-opened apo.
- Gates [[TASK-0210]].

## Open Questions

- Which energy function for the coupling statistic? EvoEF2 is vendored and
  already used, so it is the default — but it is a *design* energy, not a
  folding energy. State the limitation; do not silently treat ΔE as free energy.
- Is χ-angle comparison meaningful for surface residues with poor density?
  Filter on B-factor/occupancy and say what was filtered.

## REVIEWER VERDICT 2026-08-07 — the gate reads INCONCLUSIVE, not CLOSED

**Reviewer thread (Opus), auditing `results.json` directly. The process work
in this task is good — reconstruction validation, the distal control reported
honestly when it failed, BCR_ABL1 correctly excluded, CASPASE7 dropped with a
stated reason, Q-0001 answered properly, and an "interpretive limitation"
paragraph that caught the shape of the problem unprompted. The *measurement
design* is what fails, and most of that design came from the Reviewer thread's
own task specification.**

**The compound AND-gate had one leg that could not fire and another that is
confounded. It therefore could not return `OPEN` on any data, and its `CLOSED`
output must not gate [[TASK-0210]].**

### V1 — The frustration statistic's positive outcome is structurally unreachable

Every `joint` is large and **positive**: +25.44 (KRAS_G12C), +28.95 (PTP1B),
+23.50 (CASPASE1), +114.75 (GLUCOKINASE). This task's own pre-registered
"textbook frustration signature" requires `joint < 0` — favourable jointly.
**That cannot occur under this construction.** Transplanting rigid holo
rotamers onto an apo backbone always clashes: 9/12, 10/12, 5/6 and 5/12 of the
individual swaps are destabilizing. GLUCOKINASE's +114.75 is a clash energy,
not a coupling measurement.

The statistic as built measures *"do rigid holo side chains fit on an apo
backbone"* — answer: never — not *"are these changes coupled."* It needs
post-transplant relaxation before the energies carry meaning.

Same **class** as [[TASK-0204]]'s D1: a criterion whose positive outcome the
measurement setup cannot produce. Not arithmetically impossible this time, but
structurally unreachable.

### V2 — The `not_evaluable` guard keyed off the wrong variable

This task pre-registered: *"If `sum_singles ≈ 0` (no window residues change
side chain meaningfully), report as `not_evaluable`."*

KRAS_G12C has `side_chain_explained = 0.036` — exactly the case the guard was
written for. But `sum_singles = 25.45`, far from zero, because it is dominated
by **clash** energy rather than real side-chain change. The guard did not fire
and KRAS_G12C's +0.04% was reported as a genuine "decomposable" result. The
Done section notices the symptom ("measuring near-nothing") without connecting
it to its own guard failing.

### V3 — The attribution metric is structurally biased toward "backbone"

The two reconstructions are not symmetric. `holo_backbone + apo_chi` moves
N/CA/C **and drags every side chain with it**; `apo_backbone + holo_chi` moves
only atoms beyond Cβ. Backbone therefore receives credit for displacement the
side chains would have undergone regardless.

The dihedral data collected by this same task contradicts the attribution
directly:

| Target | pocket backbone Δ | pocket χ Δ | `backbone_explained` | reported verdict |
|---|---|---|---|---|
| PTP1B | **21.3°** | **149.9°** | 0.539 | substantially_backbone |
| CASPASE1 | 88.6° | 142.5° | 0.524 | substantially_backbone |

PTP1B's pocket side chains rotate **7× more** than its backbone, and its
distal control is the reverse (62.3° vs 46.0°). By dihedral magnitude that is
a **side-chain-dominated** pocket change, labelled substantially backbone.

The metric measures *how much heavy-atom displacement is **carried** by
backbone motion*, not *how much of the functional change is backbone-driven*.
Those diverge whenever the backbone moves at all — and the distinction is the
entire purpose of this gate, which exists to decide whether [[TASK-0204]]'s
fixed-backbone closure applies.

### V4 — Undeclared deviation from the pre-registered attribution rule

The pre-registered rule is *substantially backbone if `backbone >= 0.50` **OR**
`side_chain < 0.70`* — a disjunction that classifies almost anything as
backbone. GLUCOKINASE satisfies it (`side_chain` 0.463 < 0.70) despite
side-chain explaining **2.3×** more than backbone (0.463 vs 0.204). The Done
section labels it `ambiguous`, a category absent from the pre-registration.
That is the honest call and the right one — but it is an undeclared deviation
from a pre-registered rule and is recorded here as one.

### V5 — The distal-control failure is under-weighted

Pocket Cα motion fails to exceed distal on 2 of 4 (CASPASE1 1.631 vs 1.684;
GLUCOKINASE 0.789 vs 0.933), and PTP1B's pocket backbone dihedral change is
**3× smaller** than its distal control (21.3° vs 62.3°). Reported honestly,
but the combined reading is stronger than stated: **on several targets the
pocket is not where the backbone action is.** That bears on whether the
4.5 Å drug-contact window is the right locus, and it rhymes with
[[TASK-0169]]'s benchmark-discriminability finding.

### Specification error, owned

The compound AND-gate was written into this task by the Reviewer thread. It
conflated two different questions — *"does [[TASK-0204]]'s closure apply?"*
and *"is the search hard?"* — and the second was never answerable by a
statistic that requires the correct holo backbone already in hand. Third
specification failure of this shape in sequence ([[TASK-0204]] D1, [[TASK-0204]]
criterion #1, this). The convention amendment is filed rather than repeated.

### Corrected verdict

**INCONCLUSIVE on all 4 targets.** [[TASK-0210]] is **not** closed by this
result and remains gated pending the recompute below. The one signal that
survives intact — and it points the *opposite* way from the reported verdict —
is PTP1B's dihedral profile: large χ rotation on a nearly static pocket
backbone, inverted distally, on the register's one surviving-positive target.

### Recompute (Reviewer thread, 2026-08-07) — DONE. All three fixes land; the original conclusion does not survive.

`scripts/task0208_recompute.py`,
`results_task0208_apo_holo_decomposition/results_recompute.json`. Written to a
**separate artifact**; the original `results.json` is untouched as the record.

**V1 — relaxation confirms the original statistic was measuring steric overlap, not coupling.**
Adding EvoEF2 `RepairStructure` before `ComputeStability` (0.3 s/call) removes
**~97%** of the measured energy on the one target that can be evaluated:

| Target | original (rigid) | relaxed |
|---|---|---|
| GLUCOKINASE | sum_singles 116.13, joint 114.75 | **sum_singles 4.15, joint 3.77** |

The original numbers were clash energy almost in their entirety. The relaxed
values sit in a physically meaningful range — and `joint` is still positive
(3.77), gap 9.2%, so GLUCOKINASE remains **not frustrated** on a statistic
that could now, for the first time, have said otherwise.

**V2 — with the guard re-keyed, 3 of 4 targets cannot be evaluated at all.**

| Target | `side_chain_explained` | original verdict | corrected |
|---|---|---|---|
| KRAS_G12C | 0.036 | decomposable (+0.04%) | **not_evaluable** |
| PTP1B | 0.078 | decomposable (+16.2%) | **not_evaluable** |
| CASPASE1 | 0.043 | anti-frustrated (−10.0%) | **not_evaluable** |
| GLUCOKINASE | 0.463 | decomposable (+1.2%) | evaluable, not frustrated (9.2%) |

**Three of the four "decomposable" readings in the original table were
vacuous** — including PTP1B's +16.2%, which the Done section above reported
as the largest, most HYP-S6-consistent value and which [[TASK-0212]] was
filed to chase. That observation does not survive: it was computed on a
side-chain component that accounts for 7.8% of the change, dominated by
clash. **[[TASK-0212]] must be re-scoped or dropped** — the rank it was
built to test does not exist.

**V3 — dihedral-space attribution reverses the backbone verdict on every target.**

| Target | RMSD `backbone_explained` | dihedral bb-share, pocket | dihedral bb-share, distal |
|---|---|---|---|
| KRAS_G12C | 0.733 → "substantially backbone" | **0.374** | 0.561 |
| PTP1B | 0.539 → "substantially backbone" | **0.205** | 0.532 |
| CASPASE1 | 0.524 → "substantially backbone" | **0.356** | 0.247 |
| GLUCOKINASE | 0.204 → "ambiguous" | 0.357 | 0.371 |

In dihedral space the backbone share at the pocket is **below 0.5 on all four
targets** — side-chain torsion change dominates the pocket conformational
change everywhere, most extremely on PTP1B (0.205, i.e. ~80% χ). And the
**distal control is higher than the pocket on 3 of 4**, so backbone change is
relatively more important *away* from the pocket while side-chain change is
specifically concentrated *at* it. That is a real, pocket-specific signal the
original metric inverted.

### The corrected reading — and the tension that is itself the finding

The two attribution metrics disagree systematically, and both are correct
about different things:

- `side_chain_explained` ≈ 0.04–0.08 on 3/4 targets: **rotating side chains
  on the apo backbone gets you almost nowhere.** The backbone must move.
- dihedral bb-share ≈ 0.20–0.37: **most of the torsional change is in χ.**

Both hold simultaneously, and the resolution is the interesting part: **the
backbone moves little but is load-bearing.** A small backbone shift
repositions the side-chain frames; without it, no amount of χ rotation
reaches the holo pocket. The side chains do most of the rotating; the
backbone does little rotating but gates all of it.

That is neither the pure-backbone regime nor the pure-side-chain regime — it
is the description of a **coupled** one. It does not prove coupling (the
statistic that would is inapplicable on 3/4 targets), but it is the opposite
of evidence for closure.

### Final gate verdict: INCONCLUSIVE, and [[TASK-0210]] stays open

The coupling question is **unanswered**, not answered negatively: on 3 of 4
targets the statistic is inapplicable, and on the fourth it is not frustrated
at a 9.2% gap. Neither the original `CLOSED` nor an `OPEN` is supported.

What did change: the attribution leg no longer supports "substantially
backbone" once measured in a space the backbone cannot win by carriage, and
`side_chain_explained` rules out the pure-side-chain closure via
[[TASK-0204]] just as firmly. Both simple closures are now excluded.

**For [[TASK-0210]]:** the gate does not close it and does not open it. Its
own pre-registered reading should use `side_chain_explained` (rules out the
[[TASK-0204]] shortcut) together with the dihedral attribution (rules out a
pure-backbone framing), and treat the frustration statistic as **not
measured** rather than as measured-and-negative.

### Follow-ups this recompute creates

1. **[[TASK-0212]] is invalidated as filed** — PTP1B's +16.2% was vacuous.
2. **A coupling statistic that works when `side_chain_explained` is small is
   still missing.** Every construction tried so far needs a meaningful
   side-chain component to compare against; on these targets there isn't one.
   Measuring coupling here likely requires moving backbone and side chain
   *together* (HYP-S2's local-closure moves), not transplanting χ onto a
   fixed backbone.
3. **The pocket-vs-distal dihedral inversion** (side-chain change concentrated
   at the pocket, backbone change concentrated distally, 3/4 targets) is a new
   observation with no owner.

---

## Done

**2026-08-12, Architect — reconciliation.** This section previously
reported the pre-recompute reading ("Overall gate verdict: CLOSED on all
4 evaluated targets") as if it were the operative result, unreconciled
with the Reviewer thread's own "REVIEWER VERDICT"/"Recompute" sections
above, which supersede it and reach **INCONCLUSIVE**. The two were left
side-by-side in the file, contradicting each other, with no corrections
propagated to [[COMMON.md]]'s registry (`TASK-0208`/`TASK-0210`/
`TASK-0212` rows all still stated the retracted `CLOSED`/`+16.2%`
numbers). Nothing new was computed here — the recompute
(`scripts/task0208_recompute.py`, `results_recompute.json`) was already
run and is correct; this pass only fixes the write-up so the file no
longer asserts two different verdicts. The original per-target table and
its "CLOSED" framing are kept below, relabeled **superseded**, for the
record of what changed and why — not deleted, per this register's own
no-silent-overwrite convention.

### Original per-target results (2026-08-07, Implementer A) — superseded by the recompute above

| Target | backbone_explained | side_chain_explained | attribution | Cα pocket / distal (Å) | frustration gap | gate |
|---|---|---|---|---|---|---|
| KRAS_G12C | 0.733 | 0.036 | substantially_backbone | 2.225 / 2.002 | +0.04% | CLOSED |
| PTP1B | 0.539 | 0.078 | substantially_backbone | 1.691 / 1.332 | **+16.2%** | CLOSED |
| CASPASE1 | 0.524 | 0.043 | substantially_backbone | 1.631 / 1.684 | -10.0% (anti-frustrated) | CLOSED |
| GLUCOKINASE | 0.204 | 0.463 | ambiguous | 0.789 / 0.933 | +1.2% | CLOSED |

Reconstruction validation passed on all 4 (both partial reconstructions
bracket the true apo→holo displacement; no resname mismatches excluded) —
this part is unaffected by the recompute and still holds.
Frustration gap = `(sum_singles - joint) / |sum_singles|`; the
pre-registered frustration bar is 30%.

**Why this table is superseded, not just qualified**: V1 showed the
`joint`/`sum_singles` values above are ~97% clash energy from the rigid
transplant, not a coupling measurement; V2 showed the `not_evaluable`
guard should have fired on 3 of these 4 rows (`side_chain_explained`
0.036–0.078) and didn't; V3 showed `backbone_explained`'s
"substantially_backbone" calls invert once measured in dihedral space.
None of the four `gate: CLOSED` entries above survive — see the
Recompute section for the corrected per-target reading.

### Operative gate verdict: **INCONCLUSIVE on all 4 targets** (per the Recompute section above, 2026-08-07, Reviewer thread)

The frustration statistic is `not_evaluable` on 3/4 targets (KRAS_G12C,
PTP1B, CASPASE1 — `side_chain_explained` too small for the transplant-ΔE
statistic to mean anything) and not-frustrated-at-9.2%-gap on the fourth
(GLUCOKINASE, after relaxation). The attribution leg no longer supports
"substantially backbone" once measured in dihedral space (backbone share
0.20–0.37 at the pocket on all 4, below 0.5 everywhere), so neither the
pure-side-chain closure (via [[TASK-0204]]) nor a pure-backbone framing is
supported. **[[TASK-0210]] is neither opened nor closed by this
evidence** — the coupling question is genuinely unanswered, and a working
coupling statistic for the `side_chain_explained`-small regime does not
yet exist (Recompute follow-up #2). Full reasoning, numbers, and the
"backbone moves little but is load-bearing" reading: the Recompute
section above.

**A real interpretive limitation, unchanged by the recompute and worth
keeping**: even a working frustration statistic only tests side-chain
coupling *given* the correct holo backbone already in hand — it cannot,
by construction, test whether *finding* the correct backbone move itself
is hard. That question remains fully open regardless of how the
side-chain statistic resolves.

### The mandatory distal-control check did not hold uniformly

Pocket Cα motion exceeds distal-control Cα motion on KRAS_G12C (2.225 vs.
2.002 Å) and PTP1B (1.691 vs. 1.332 Å), but **not** on CASPASE1 (1.631 vs.
1.684 Å — background moves slightly *more*) or GLUCOKINASE (0.789 vs.
0.933 Å — same). PTP1B's backbone-dihedral magnitude check shows the same
pattern even more sharply (pocket mean 21.3°/residue vs. distal 62.3°) —
the drug-contact pocket itself is not always where the largest raw
backbone motion is; other regions (crystal-packing artifacts, a different
flexible loop, or genuine allosteric propagation to a site the fixed
4.5 Å drug-contact definition doesn't capture) can move as much or more.
This does not overturn the reconstruction-based attribution (which is
pocket-local by construction and still shows real signal on all 4), but
it means "the pocket changes more than background" cannot be assumed and
should be checked per-target going forward, as done here.

### [[TASK-0201]] link: is PTP1B the most coupled?

**Superseded — the premise did not survive the recompute.** PTP1B's
+16.2% frustration gap (the basis for the "nominally yes" reading
originally written here, and for filing [[TASK-0212]]) was computed on
`side_chain_explained = 0.078` — one of the three rows V2 showed should
have been `not_evaluable`. There is no PTP1B frustration number left to
rank against HYP-S6. [[TASK-0212]] is invalidated as filed; see its own
file for the re-scope decision.

### Overlap ≠ coupling (framing, [[Q-0001]]/A2)

Magnitude and hardness are orthogonal. RMSD and Cα displacement measure
*how much* structure changed; they say nothing about whether that change
is reachable by independent per-residue moves (easy, any magnitude) or
requires several changes to happen jointly (hard). The single-vs-joint ΔE
statistic above is what actually tests the second question — no overlap
measure in this task substitutes for it, and none of this task's RMSD/Cα
numbers should be read as evidence about search difficulty on their own.

### Q-0001 amendments (Reviewer thread)

A1 (Cα-only pocket-local cross-check) accepted and implemented — see
`ca_rmsd_pocket`/`ca_rmsd_distal` in the script and the table above. A2
(overlap≠coupling framing) accepted, stated above. A3 (PTP1B rank-
correlation hypothesis) declined for this task, filed as [[TASK-0212]].
Full reasoning: [[Q-0001]] (`.ai/memory/questions/implementer/answered/`).

### Not attempted

- BCR_ABL1 excluded per [[TASK-0209]] (pre-opened by myristate).
- CASPASE7 attempted, dropped (empty pocket/common-residue intersection).
- HYP-S4 (endpoint-vs-path coupling) and HYP-S5 (instance enrichment) —
  explicitly out of scope per [[Q-0001]]'s Background, not folded in.
- Reproducibility of the frustration statistic itself — [[TASK-0212]].
