# TASK-0381 — Tier 0: COREX ensemble coupling on BCR-ABL1, CPU-only, while the GPU is unavailable

- Status: Done
- Owner: **Implementer**
- Priority: **High. Runs on CPU, needs no GPU, and tests the mechanism the thermodynamics literature says is dominant.**
- Filed: 2026-09-13 by Reviewer thread (id via `claim.py reserve-next`)
- Source: Team Lead, 2026-09-13 — Tier 1 is blocked on desktop GPU availability; Tier 0 is not
- Related: [[TASK-0377]], [[TASK-0229.006]], [[TASK-0166]], [[HYP-P13]]

## Why this is the right thing to run while waiting

[[TASK-0377]]'s Tier 0 is *"COREX/EAM — CPU, hours"*, and `src/allostery/corex.py`
is already written ([[TASK-0229.006]]). **It needs no GPU and no MD engine**, both
of which this machine lacks and the desktop currently cannot supply.

It is also the arm that tests the mechanism the field's own thermodynamics
literature considers dominant: ref [4] (Motlagh, Wrabl, Li & Hilser 2014,
*Nature* 508:331) argues allosteric coupling is **a partition-function quantity
over folded/unfolded microstates**, not a pathway on a contact graph. Every arm
this project has run so far was a pathway-on-a-graph arm.

## Precondition gate — settle this before computing anything

**In this construction, "ligand bound" can only mean "these residues are held
folded".** So the discriminative control [[TASK-0377]] calls its best design
element — *asciminib enhances nilotinib but not dasatinib* — **is only available
if the two ligands contact materially different residue sets.** If their contact
sets are near-identical, COREX represents them identically and **cannot
discriminate them, by construction**.

**Determine this first, from the structures, and write the answer down before
proceeding:**

- Nilotinib contacts from `5MO4` (or `3CS9`), dasatinib contacts from `2GQG`.
- Report the two sets, their overlap, and the residues unique to each.

There is a real reason to expect a difference: **nilotinib is type II (DFG-out,
extending into the back pocket) and dasatinib is type I (DFG-in)**, so their
footprints differ, and nilotinib's is the one overlapping the region asciminib's
conformational effect acts on. **But that is a prediction, not a measurement.**

**If the sets are near-identical, stop and report that.** A number produced from
two near-identical constraint sets would look like discrimination and be a
size artifact. Reporting the gate's failure is the correct deliverable in that
case.

## In scope, if the gate passes

1. **Add a folded-constraint to `corex.py`.** `corex_ensemble(model, chain_id,
   window_sizes, temperature)` currently has no ligand or constraint argument.
   The Hilser construction is to hold a residue set in the folded state and
   recompute the partition function — a small, well-defined addition, not a
   rewrite.
2. **The four-state cycle.** Apo; asciminib-bound (myristoyl residues held
   folded); nilotinib-bound (ATP-site residues held folded); both. Report the
   coupling as the cycle closure.
3. **Both directions.** Myristoyl→ATP and ATP→myristoyl. A partition-function
   coupling is symmetric by construction, so **asymmetry in the output is a bug
   signal**, and a free internal check worth reporting.
4. **The discriminative control.** Repeat the ATP-site arm with dasatinib's own
   contact set. **The pre-registered expectation is coupling for nilotinib and
   materially less for dasatinib.**

## What this can and cannot deliver

**Ordinal, not absolute.** `window_free_energy` returns kcal/mol, but on
deliberately simplified parameters — a single temperature, a two-term
`dG_hydrophobic − T·dS_conf`, a flat 4.1 cal/(mol·K) backbone entropy, and
carbon-only apolar classification, all stated plainly in the module's own header
rather than hidden. **Do not compare the magnitude to the ~7 kcal/mol figure.**

That figure is, per [[TASK-0377]]'s own correction, a **small-cluster
H-bond-only DFT estimate**, and **no experimental ΔΔG exists for this system at
all** — the only measurements are cell IC50s converting to ≈0.4–0.9 kcal/mol.
Comparing a simplified ensemble model to a truncated DFT cluster is two different
levels of theory on two different system definitions, which is exactly the trap
Tier 1's gate was already corrected for.

**So the deliverable is the sign and the ordering**: does coupling exist at all
between these two sites, and does it discriminate nilotinib from dasatinib?

## Planned Validation

`corex_ensemble` must reproduce [[TASK-0229.006]]'s own committed numbers on
whatever target that task ran, unchanged, before the new constraint path is
trusted. **The constraint addition must also be a no-op when the constrained set
is empty** — if constraining nothing changes the answer, the implementation is
wrong and the task stops there.

## Pre-registered prediction

**Coupling exists and is non-trivial** — this is the mechanism the ensemble
literature says dominates, and [[TASK-0377]] records ~half of asciminib's measured
effect (3.7 ± 0.5 kcal/mol) living in the ensemble shift rather than in contacts.

**The dasatinib discrimination is genuinely uncertain**, and is the interesting
half. If a crude ensemble model with no MD, no quantum content and no fitted
parameters reproduces a published pharmacological asymmetry, that is a real
result and it is CPU-cheap. If it does not, it bounds what this level of theory
can do — and that bound is worth knowing before Tier 1 costs GPU-days.

## Constraints

- **No claim in kcal/mol against any external number.** Ordinal only.
- The [[TASK-0166]] caveat stands and must not be misread in either direction:
  that task's harmonic-entropy result was proximity-confounded, and
  `corex.py`'s own header explicitly refuses the inference that the entropy route
  is therefore closed — **harmonic stiffening is not unfolding.** This task
  implements the nonlinear picture, which remains untested.
- Every parameter simplification in the module's header is carried into the
  write-up. They are already disclosed there; they must not become invisible by
  being one layer down.

## Done (2026-09-13, Implementer C)

**Gate passes, but only after catching a real numbering trap that
initially gave the opposite answer. Coupling exists, is small, and does
not discriminate nilotinib from dasatinib — for a diagnosed, disclosed
reason (real footprint overlap), not an unexplained null. The "asymmetry
is a bug signal" prediction is falsified for the dGf-based metric and
explained, not just reported.**

### Precondition gate — a real numbering trap caught before trusting anything

Nilotinib and asciminib contacts (both from `5MO4`'s own single chain A,
one structure, one numbering) mapped cleanly onto `1OPL` (25/26 and
20/20 identity matches). **Dasatinib's contacts from `2GQG` did not: 1/21
identity match at raw resnums** — `2GQG` uses Abl-1b numbering, the same
**+19 offset** [[TASK-0377]] already documented for T315I/T334I. Applying
it: 21/21 identity match. **This reverses the gate's own conclusion**:
raw resnums give nilotinib-vs-dasatinib Jaccard **0.09** (looks
near-disjoint, easy pass); the corrected resnums give Jaccard **0.567**
(17/21 dasatinib contacts are also nilotinib contacts) — real, substantial
overlap, not "near-identical" (43% of the union is still exclusive to one
ligand) but a materially weaker discriminating signal than the
uncorrected number suggested. **Proceeded on the corrected numbers**,
flagging every downstream result against this real overlap rather than
assuming clean discrimination.

### Planned Validation — passed, twice

`corex.py`'s own `run_sanity_check`/`corex_ensemble` reproduces
[[TASK-0229.006]]'s committed numbers on both original targets exactly:
KRAS_G12C ρ=−0.365 (p=1.06×10⁻⁶, committed −0.365/1.06×10⁻⁶), PTP1B
ρ=−0.2979 (p=1.61×10⁻⁷, committed −0.298/1.61×10⁻⁷) — reproduced before
trusting anything on a new target. **BCR_ABL1 itself also passes the same
qualitative sanity gate** (ρ=−0.2693, p=6.2×10⁻⁹) — not required by name
in this task's own Planned Validation, but cheap and directly relevant,
so run anyway rather than skipped. **No-op check**: an empty perturbation
set reproduces the unperturbed dGf to the last digit
(`dGf=-0.773803` both ways) — the constraint mechanism does not silently
change behaviour when constraining nothing.

### Item 1 — no new mechanism needed

`corex.py::coupling_score` already implements exactly the "folded
constraint" this task's own item 1 asked to add
([[TASK-0229.006]]'s own, pre-existing capability) — generalized here
from "one residue at a time" to "an arbitrary named region" (the same
math `scripts/task0229_006_corex_eam.py::run_all_candidate_couplings`
already validated), not a new addition to `corex.py` itself, which is
untouched.

### Four-state cycle, both directions

| state | dGf(T=ATP-site region) | dGf(M=myristoyl region) |
|---|---|---|
| apo | −0.7738 | −2.5116 |
| asciminib-bound (M stabilized) | −0.7632 | −5.5116 |
| nilotinib-bound (T stabilized) | −3.7738 | −2.3695 |
| both | −3.7631 | −5.3684 |

**Coupling M→T = +0.0106 kcal/mol; T→M = +0.1422 kcal/mol.** Both
correctly signed (positive = stabilizing one site destabilizes the
other's own folding a little, the allosteric-coupling direction), both
small relative to the 3 kcal/mol stabilization bonus that drives them
(well under 5% propagation either way) — real, non-zero, but not
"non-trivial" in the sense the pre-registered prediction hoped for.

### The symmetry check fails — diagnosed, not just reported

The task's own filing states coupling "is symmetric by construction" and
predicts asymmetry would be "a bug signal." **Measured: it is not
symmetric** (M→T and T→M differ ~13×). Rather than report this as an
unexplained defect, it was tested directly: a genuine statistical-
mechanics reciprocity theorem (Maxwell-relation type) DOES guarantee
symmetry, but only for the **raw, linear** unfolded-population response,
in the **infinitesimal-bonus limit** — not for `dGf`'s own **nonlinear
log-odds transform** of that population, and not necessarily at a large
finite bonus.

| bonus | dGf-based ratio (M→T / T→M) | raw-population ratio |
|---|---|---|
| 0.0001 | 0.084 | **1.000** |
| 0.001 | 0.084 | 1.000 |
| 0.01 | 0.083 | 0.997 |
| 0.1 | 0.082 | 0.969 |
| 1.0 | 0.076 | 0.836 |
| 3.0 (shipped) | 0.075 | 0.800 |

**The raw-population coupling converges to a perfect 1:1 ratio as the
bonus shrinks — the underlying thermodynamic reciprocity holds exactly,
confirming this is not a code bug.** The dGf-based ratio stays near 0.08
even in that same limit: `M` (baseline unfolded probability 0.0142) and
`T` (baseline 0.2131) sit at very different points on the nonlinear
log-odds curve — a **15× difference in baseline stability** — so the
SAME symmetric linear response, passed through `dGf = -RT·ln(folded/
unfolded)` at two different operating points, comes out asymmetric. **The
task's own prediction is falsified for the dGf-based metric and
confirmed for the underlying population-level quantity** — a real,
diagnosed methodological finding: dGf-based COREX coupling numbers are
not symmetric between regions of very different intrinsic stability, and
should not be compared as if they were, in this or any future use of
`coupling_score`-style aggregate readouts.

### Discriminative control — does not discriminate, and now the reason is known

**Coupling M→nilotinib-site = +0.01063 kcal/mol; M→dasatinib-site
(corrected) = +0.01062 kcal/mol — indistinguishable.** The pre-registered
prediction ("coupling for nilotinib and materially less for dasatinib")
fails. **This is not a surprise given the corrected precondition gate**:
17/21 (81%) of dasatinib's own contacts are also nilotinib contacts, so a
coarse windowed-region model that treats "any window touching the site"
identically cannot be expected to tell the two apart — the discriminative
control's own precondition (materially different contact sets) was only
partially met, and the result is exactly what that partial overlap
predicts, not an unexplained pharmacological null.

### Read against the pre-registered prediction

**"Coupling exists and is non-trivial"**: partially — real, correctly
signed, reproducible, but small (≤0.14 kcal/mol against a 3 kcal/mol
perturbation) at this level of theory. **"Dasatinib discrimination is
genuinely uncertain, and is the interesting half"**: resolved as **does
not discriminate**, for a diagnosed reason (footprint overlap, itself
only visible after fixing the numbering trap) — not the clean
"reproduces a pharmacological asymmetry" outcome that would have been
the headline result, but a real, mechanistically explained negative.

### Constraints honored

No claim in kcal/mol against any external number (~7 kcal/mol, IC50
conversions) — every comparison here is internal (M→T vs T→M, nilotinib
vs dasatinib, all under the identical model). The [[TASK-0166]] caveat
(harmonic stiffening is not unfolding) is not implicated — this task
implements the nonlinear COREX picture, untouched by that caveat. Every
simplification in `corex.py`'s own header (single temperature, two-term
free energy, flat backbone entropy, carbon-only apolar classification)
carries into this write-up rather than being hidden a layer down.

### Landed

New hypothesis **HYP-P32** in `physics.md`.

**Files**: `__WORK_IN_PROGRESS__/scripts/task0381_corex_bcr_abl1_coupling.py`.
**Data**: `__WORK_IN_PROGRESS__/results/tasks/0381_tier0_corex_bcr_abl1/
{precondition_gate.json,result.json}`.
