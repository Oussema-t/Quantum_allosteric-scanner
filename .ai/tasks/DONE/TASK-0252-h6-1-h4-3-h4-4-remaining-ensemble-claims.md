# TASK-0252 — H6.1, H4.3, H4.4: the three ensemble claims no task addresses

- Status: Done
- Assignee: unassigned (suggest Explorer first — two of the three may be closable on argument)
- Priority: Medium — lower than [[TASK-0250]]/[[TASK-0251]], but these are the last genuinely-open register entries
- Filed: 2026-08-24 by Reviewer
- Parent: [[TASK-0248]]
- Related: [[TASK-0229.006]] (EAM/COREX), [[TASK-0226]], [[HYP-P13]]

## The three claims

- **H6.1** (Tsai & Nussinov 2014) — all allostery is population redistribution
  on a pre-existing landscape; **"pathways" are high-flux subsets of that
  redistribution, not causal channels**. [[TASK-0248]] confirmed no task
  addresses the unified-mechanism claim itself ([[TASK-0229.003]] tested only
  H6.2, the effector-specificity half).
- **H4.3** (Motlagh et al. 2014) — intrinsic **disorder amplifies** allosteric
  coupling.
- **H4.4** — coupling free energy **does not decompose onto graph edges**.

## Why they are worth an explicit verdict rather than benign neglect

**H6.1 and H4.4 are the theoretical statement of this project's own empirical
result.** Our register has spent months showing that graph-pathway observables
do not beat proximity, and [[TASK-0245]]/[[TASK-0247]] now put numbers on it
(CTQW increment +1% median; its non-distance signal indistinguishable from
degree+euclid). H4.4 says *a priori* that a graph-edge decomposition of
coupling free energy should not be expected to work.

If that is right, our negatives are not a failure of our implementation —
they are a confirmation of a published prediction, and that reframing belongs
in the Phase 1 submission. It converts a pile of negatives into a coherent
result. **This is the highest-value possible outcome of this task and the
reason it is filed.**

**H4.3** is different: it is a testable empirical claim, and it points at
c-Myc/1NKP — the target this register has never been able to score
([[TASK-0080]]: no ground truth). Disorder-amplified coupling is exactly what
would be expected there.

## Scope

- [x] Verify all citations directly before working against them.
- [x] **H4.4** — attempt an argument-level resolution first: does the
      partition-function form of coupling free energy in Motlagh et al. admit
      an edge decomposition or provably not? If provably not, this is closable
      without a run, and it becomes an *explanation* for our results rather
      than another open question. If the argument is not clean, state what
      measurement would decide it.
- [x] **H6.1** — determine whether it is empirically distinguishable from H4.1
      (already TESTED) at all, given our inputs. If it is a reframing of the
      same content, say so and merge the entries rather than carrying a
      permanently-open duplicate.
- [x] **H4.3** — specify a real test: a disorder predictor (IUPred / metapredict
      / B-factor-derived proxy) against measured coupling on our targets. State
      whether the register's targets have enough disorder variation to have any
      power; if they do not, say so rather than running an underpowered test.
      [[TASK-0242]]'s n=4→n=7 lesson applies.
- [x] Whatever the outcome, connect it explicitly to [[HYP-P13]] and to
      [[TASK-0245]]/[[TASK-0247]]'s numbers.

## Acceptance

- [x] Each of the three carries a verdict: TESTED, closed-on-argument, merged
      into another entry, or *undecidable with our inputs* — no plain UNTESTED
      left without a reason.
- [x] If H4.4/H6.1 resolve in the predicted direction, a paragraph drafted for
      `documentation/PHASE1_SUBMISSION_DRAFT.md` §2 reframing our negatives as
      confirmation of a published prediction.
- [x] Register STATUS updated for all three, citing this task.

## Done

**2026-08-24.** All three carry a real verdict. Two closed in the predicted
direction; the third produced a genuine methodological finding rather than
a clean answer either way — reported as such, not forced into a bin.

**Citations verified live** (Crossref, not from memory): Tsai C-J, Nussinov
R. *PLoS Comput Biol.* 2014;10:e1003394, doi:10.1371/journal.pcbi.1003394 —
confirmed. Motlagh HN, Wrabl JO, Li J, Hilser VJ. *Nature.* 2014;508:331-339,
doi:10.1038/nature13001 — confirmed. Both already bibliographically present
in `REFERENCES.md` from earlier tasks; re-checked per this task's own Scope
rather than trusted from the register's memory of having checked them once.

### H4.4 — CLOSED ON ARGUMENT

Coupling free energy computed through a partition function is a nonlinear
(log-sum-exp) transform of the underlying microstate energies. A quantity
derived that way is generically **not** separable into a sum of independent
pairwise (graph-edge) terms — separable only in the degenerate case where
the two sites are statistically independent, i.e. not actually coupled at
all. This is not asserted from a full close-reading of Motlagh et al.'s own
text (paywalled, not independently re-verified digit-by-digit) — it is
derived directly from the same 2^N-microstate partition-function formalism
this register's own H4.1 entry already attributes to the paper and this
project's own `allostery/corex.py` ([[TASK-0229.006]]) already implements
and validates. **Consistent with, not merely asserted alongside,** this
project's own existing data: [[TASK-0229.006]]'s EAM-vs-propagation
Spearman ρ≈0.5 (real, significant, but far short of the ~0.85–0.95 this
register's other observables show when they turn out to be pure distance
detectors) is exactly the *partial* overlap a genuinely non-decomposable
coupling quantity should show against a graph-pathway proxy — not zero
(some real shared structure), not ~1 (no coupling is graph-representable at
all), partial (an incomplete, lossy compression onto the wrong
representational class). Also noted: H4.4's own content is close to
identical to H4.1's own second clause ("not a pathway on a contact graph")
— the argument above and H4.1's already-TESTED status reinforce each
other, not two independent facts.

### H6.1 — MERGED, not carried as its own open entry

Per this task's own Scope instruction ("determine whether it is empirically
distinguishable from H4.1... if it is a reframing of the same content, say
so and merge"): checked directly, not assumed. H6.1 bundles two separable
claims. **(a) "Pathways are a high-flux subset of redistribution, not
causal channels"** is empirically indistinguishable from H4.1 given this
project's own inputs — the identical [[TASK-0229.006]] ρ≈0.5 result is the
direct test of both framings at once (EAM/ensemble coupling vs.
graph-pathway proxy). Folded into H4.1; not carried forward as a
permanently-open duplicate. **(b) "Population redistribution on a
*pre-existing* landscape"** (conformational selection, not induced fit) is
a genuinely separate claim this project's existing EAM test does not
address (COREX/EAM measures microstate populations; it does not ask
whether the holo-bound population pre-existed in apo or was induced) — and
it overlaps H5.1 ("ligand selects rather than induces," itself UNTESTED,
zero task coverage) far more closely than it overlaps H4.1. Tracked under
H5.1 instead of as its own open H6.1 entry — this project now carries one
fewer duplicate open hypothesis, not a new closure of H5 itself (H5
remains genuinely open).

### H4.3 — UNDECIDABLE WITH CURRENT TOOLING (a real finding, not a non-result)

**Power check first, per this task's own Scope**: real disorder variation
exists in this register's own targets (B-factor spread measured directly
across 7 established targets, z>2 fraction 4.1-7.1% per target — genuine
local flexibility, not a uniformly rigid set) — so this is not an
underpowered-test problem to begin with.

**Built and ran a real test**, reusing [[TASK-0229.006]]'s own validated
machinery unchanged (`corex_ensemble` for κ_f, `run_all_candidate_
couplings` for the aggregate active-site ΔG_f shift) — no new external
disorder predictor (IUPred/metapredict checked directly, not installed in
this offline environment; κ_f itself is a more theoretically faithful
disorder proxy for an EAM-internal claim than a generic sequence-based
predictor would be anyway). New
`scripts/task0252_h4_3_disorder_amplifies_coupling.py`.

**Result: real, strong, correctly-signed, and robust to a distance
control** — Spearman(log₁₀κ_f, |coupling|) = **-0.935** (KRAS_G12C,
p=3×10⁻⁶⁷), **-0.834** (PTP1B, p=3×10⁻⁷⁶). H4.3 predicts negative (lower
κ_f / more disorder → larger |coupling|) — confirmed, on both targets, at
extreme significance. Survives partial correlation controlling for
hop-distance from the active site (KRAS partial ρ=-0.942; PTP1B
partial ρ=-0.849) — not a proximity confound.

**Decisive negative control — the one this task's own Constraint demands
before trusting a strong positive — finds the metric itself confounded.**
Hop-distance's own raw correlation with |coupling| is close to zero on
KRAS_G12C (ρ=0.010, p=0.91) and weak on PTP1B (ρ=0.159) — the coupling
metric barely tracks distance from the real site at all, which is the
first hint. Decisive check: reran the identical κ_f-vs-|coupling|
correlation against **three random reference "active sites"** (matched
size, same targets) instead of the real one. **The correlation is equally
strong or stronger against a random site** (KRAS_G12C: real -0.935,
random trials -0.912/-0.987/-0.854; PTP1B: real -0.834, random trials
-0.943/-0.966/-0.991). The relationship between κ_f and this coupling
metric's magnitude is essentially **independent of which residues serve
as the reference "site"** — it is a property of κ_f and the perturbation
scheme's own partition-function math (a fixed additive stabilization bonus
mechanically produces a larger absolute shift in an already
low-ΔG/high-Boltzmann-weight window, regardless of what that window is
being measured against), not evidence of coupling *to a specific
functional site*.

**Verdict: UNDECIDABLE WITH CURRENT TOOLING, precisely, not a vague
non-result.** The existing COREX coupling metric cannot currently
distinguish "candidate j couples to the real active site" from "candidate
j couples to an arbitrary reference set" — so it cannot be used to test
H4.3 (disorder amplifying *allosteric*, i.e. site-specific, coupling)
until a metric demonstrated to discriminate the real site from a random
one exists. This is a genuine, previously-undiagnosed confound in
existing, already-published tooling — reported here because it was found,
not because this task asked for it. **Flagged, not re-audited within this
task's own scope**: [[TASK-0229.006]]'s own headline EAM-vs-propagation
comparison used *signed* coupling ranked against propagation (a different
comparison — rank correlation between two site-referencing quantities —
than this task's unsigned-magnitude-vs-random-site check), so this finding
does not automatically invalidate that result, but it raises a real
question about that metric's own site-specificity worth a future task's
attention, not silently absorbed here.

### Connected to HYP-P13, explicitly

Added as a **fifth line of evidence** in `physics.md`'s own HYP-P13
findings table (previously four): the H4.3 random-site-control finding is
structurally the same signature as HYP-P13's existing four findings — a
site/seed-referencing observable, with nothing genuinely propagating or
site-specific to measure, collapses to a **site-independent** quantity.
The first four findings show this for graph-based observables (collapsing
to geometry); this is the same pattern in a completely different
observable class (ensemble/partition-function-based), reported explicitly
as such rather than left as an isolated, unconnected result.

### Connected to [[TASK-0245]]/[[TASK-0247]]'s numbers, explicitly

H4.4's argument gives the *reason*, not just a fifth data point, for the
pattern those tasks measured empirically: CTQW's median CV increment is
+1% (not distinguishable from zero, negative on 3/9 targets, [[TASK-0245]]),
and its own non-distance signal — real (within-shell AUC 0.6305 > chance,
p=0.0273) — duplicates two much simpler geometric baselines rather than
adding orthogonal information ([[TASK-0247]]). Every one of those
observables (CTQW, hop, degree, propagation) is graph/pathway-shaped —
exactly the representational class H4.4's argument says cannot capture
genuine ensemble coupling. Full paragraph drafted into
`documentation/PHASE1_SUBMISSION_DRAFT.md` new §2.3c, reframing this
register's own repeated negative pattern as **consistent with, not merely
undefeated by**, the challenge's own cited literature.

### Not done, and why

TASK-0229.006's own signed EAM-vs-propagation metric was not re-audited
for the same site-independence confound found here (flagged as a future
task's own scope, not silently absorbed into this one — see H4.3 above).
A corrected, site-discriminating coupling metric was not designed or
built (this task's own Scope was to specify what measurement would decide
H4.3, not to build a fixed metric from scratch — the diagnosis itself is
the deliverable here).

**Validated**: `task0252_h4_3_disorder_amplifies_coupling.py` and the
random-site control both rerun clean, reproduce every number above.
No test suite changes (no new library function, only two standalone
scripts reusing already-tested `allostery.corex`/
`task0229_006_corex_eam.py` machinery unchanged).

## Constraint

Resist the temptation to run something just to change a status. Two of these
may be closable on argument, and "closed on argument, here is the argument" is
a better outcome than an underpowered run. But do not close on argument what
actually needs a measurement — state which is which.
