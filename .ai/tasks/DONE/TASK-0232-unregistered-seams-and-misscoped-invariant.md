# TASK-0232 Three unregistered seams, and an invariant scoped to the wrong axis

## Context

- ID: TASK-0232
- Status: Done
- **Thread: Architect/Planner.** Registry hygiene; no compute.
- Owner: Architect/Planner
- Source: Bartosz, 2026-08-21 — *"So many tests added and no newer seams?"*
- Priority: **P1.** The registries exist precisely to catch cross-unit
  invariants, and they missed the largest one of the month.

## Finding 1 — three seams that were never registered

14 seams are registered; the newest (SEAM-0013/0014) dates to 2026-08-05.
Nothing since — through a window that produced three findings which are
textbook seams, i.e. **cross-unit invariants that no single module owns**:

| Proposed | Invariant | Discovered by |
|---|---|---|
| `func_ligand` config ↔ `functional_indices` ↔ seeded observables ↔ `degree_centrality` floor | The seed must be a real functional site, **and must not coincide with a quantity that also feeds the proximity floor** | [[TASK-0216]] |
| apo array ↔ holo array ↔ index-returning functions | Returned indices must live in the array space their caller assumes; apo/holo correspondence is a precondition, not an assumption | [[TASK-0216]] |
| pre-registered criterion ↔ measurement resolution | Every verdict a criterion can report must be reachable given `n_reps`, the statistic's range, and the construction's attainable sign | [[TASK-0204]] D1, [[TASK-0208]] V1, [[TASK-0189]] |

The first is the worst kind and explains why nothing caught it: the invariant
spans a **config file**, a **library function**, and a **scoring baseline**.
No module owned it, so no module's tests covered it — which is the exact
situation `.ai/seams/` exists for.

## Finding 2 — `INV-0006` is named "seed definition" and misses the seed's reality

`INV-0006-seed-definition.md` is the invariant record for precisely this
quantity. It characterises **seed cardinality** (single residue vs. k-subset
vs. full active-site array, coherent vs. incoherent) as a KNOB, with a real
data sweep across all three mandatory targets.

It contains **zero** mentions of provenance or fallback. It swept *how many*
residues the seed contains while never asking *whether the seed is an active
site at all* — and on 9 of 13 targets it was not.

**We held the invariant record for the exact quantity that broke, and it was
scoped to the wrong axis.** That is a more useful finding than the defect
itself, because it says the registry's failure mode is *scope selection*, not
absence.

## Intent Contract

- Outcome: three seam records filed with real owners; `INV-0006` extended to
  cover provenance; and a short note in `.ai/seams/README.md` on how the
  scope-selection failure happened, so it is not repeated.
- In Scope:
  - File the three seams above, each naming a task owner (per
    `.ai/seams/README.md`'s own rule that every seam needs one).
  - Extend `INV-0006` with a **provenance** row: seed provenance is not a
    GAUGE and not a KNOB — a fallback seed is a *different quantity*, not the
    same quantity under a transformation. Classify accordingly and say why.
  - State the circularity explicitly in the first seam: seed ⊆ top-degree and
    floor ∋ `degree_centrality`, so observable and floor share a construction
    and the comparison stops being independent.
- Out Of Scope:
  - Writing the tests — that is [[TASK-0231]].
  - Re-litigating any classification already recorded in INV-0001…0008.
- Constraints And Invariants:
  - Additive. `INV-0006`'s existing KNOB characterisation stands; it was
    correct about the axis it measured.
  - Each seam records what would have caught it, so the record is actionable
    rather than merely descriptive.
- Planned Validation: for each new seam, confirm a concrete artifact
  ([[TASK-0231]]'s guard, or a named test) would fire on the historical
  failure. A seam nothing can detect is a note, not a seam.

## TODO

- [x] File the three seam records with owners.
- [x] Extend INV-0006 with the provenance row + classification rationale.
- [x] Note the scope-selection failure mode in `.ai/seams/README.md`.
- [x] Confirm each seam has a detecting artifact (or name the gap).

## Dependency

- [[TASK-0231]] supplies the detecting artifacts.
- [[TASK-0216]], [[TASK-0204]], [[TASK-0208]], [[TASK-0189]] — the source findings.

## Done

**2026-08-24 — Implementer A.** All three seams filed, INV-0006 extended,
README note added. One seam only partially closeable with what already
exists — named honestly rather than force-closed, and a follow-up task
filed to own the rest.

**[[SEAM-0015]]** (func_ligand config ↔ functional_indices ↔ seeded
observable ↔ degree_centrality floor circularity) — **VERIFIED**. Owner
[[TASK-0231]] (built `labels.assert_functional_provenance_allowed`, wired
into `build_labels`, raises unless a target's config explicitly opts into
the fallback tier) + [[TASK-0216]] (found it). Detecting artifact confirmed
real, not assumed: `tests/test_config_integrity.py`'s three test classes,
per TASK-0231's own Done section, demonstrated fail-first (the original
GLUCOKINASE mutation re-introduced into real `targets.yaml`, 3 targeted
failures) before being confirmed passing against the fix. Circularity
(seed ⊆ top-degree, floor ∋ degree_centrality) stated explicitly in the
seam's own invariant, per this task's own Constraint — with a scope note
that the guard closes the *silent* case; an explicit, disclosed opt-in
(CARDIAC_MYOSIN_TABLE1) is a visible choice, not a re-opened defect.

**[[SEAM-0016]]** (apo array ↔ holo array ↔ index-returning functions) —
**VERIFIED**. Owner [[TASK-0217.001]] (built the cross-structure
translation guard in `functional_indices`, raises rather than silently
misindexing) + [[TASK-0216]] (found it — every real target pair with a
resolvable `func_ligand` contact was affected before the fix). Detecting
artifact: `tests/test_labels.py::
test_cross_structure_heavy_atoms_without_resnames_raises` (negative case)
+ `test_cross_structure_heavy_atoms_translated_to_coords_space` (positive
case), both already existing and passing — confirmed by reading, not
re-run here (Out of Scope: no new compute this task).

**[[SEAM-0017]]** (pre-registered criterion ↔ measurement resolution) —
**OPEN, honestly**. This is the one genuinely new finding of this task's
own registry pass, not just paperwork for already-fixed defects: the
invariant has **two** sub-cases, and only one has a general guard.
Sub-case (a), `n_reps`/`alpha` reachability — owner [[TASK-0189]],
`diagnostics.assert_gate_reachable`, real and tested
(`tests/test_diagnostics.py::TestAssertGateReachable`), **VERIFIED**.
Sub-case (b), a statistic's own attainable range/sign — [[TASK-0204]]'s D1
and [[TASK-0208]]'s V1 are both real, already-fixed instances of this exact
shape (V1's own text: "same class as TASK-0204's D1"), but each fix was
local (`not_evaluable_greedy_ceiling`; a relaxation step) — **no reusable
guard, no seam-test, anywhere in the repo**. Named as the gap per this
task's own Planned Validation ("a seam nothing can detect is a note, not a
seam") rather than silently marked VERIFIED on the strength of sub-case
(a) alone. **New [[TASK-0240]] filed** (reserved-then-released, unclaimed,
ready to pick up) to own generalizing the guard and writing its seam-test
— kept out of this task's own scope deliberately: this task's own
Out-of-Scope line ("Writing the tests — that is TASK-0231") and
`.ai/seams/README.md`'s own hard requirement ("a seam-test must exist once
registered") pull in opposite directions here, since TASK-0231's actual
scope never covered this seam's subject at all. Resolved by filing the
task that will write it, the same producer/consumer split every other
seam in this registry already uses, rather than an Architect/Planner
thread authoring test code itself. This tension is recorded in
[[SEAM-0017]]'s own provenance field, not smoothed over.

**INV-0006** extended with a new `## PROVENANCE` section (2026-08-24):
classifies seed provenance as **neither GAUGE nor KNOB** — a fallback seed
is not a transformation of the active-site quantity the record's existing
KNOB rows characterize, it is a silent substitution of a categorically
different quantity (graph-degree centrality) answering a different
question. States why a KNOB framing ("sweep it, report the spread") would
have been actively misleading here, and links the circularity finding
back to [[SEAM-0015]].

**`.ai/seams/README.md`** extended with a dated note on the scope-selection
failure mode Finding 2 diagnosed: an invariant record can exist, be
correct about the axis it measured, and still miss a real defect that
lives on a *different* axis of the same quantity — checking "does a record
exist" is not sufficient, "does its own stated scope cover this failure"
is the actual question.

**Not done, per this task's own Out Of Scope**: writing any new test code
(SEAM-0017's gap is named and delegated to [[TASK-0240]], not closed here);
re-litigating any existing INV-0001…0008 classification.
