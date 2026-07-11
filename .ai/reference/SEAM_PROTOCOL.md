# Seam Protocol

*Decomposition creates edges, not just nodes. The task registry tracks the nodes.
Seams track the edges. An unverified edge is where correct parts add up to a wrong whole.*

## Why this exists

The scaffold is good at cutting work into boundable units — claim-lock, task
registry, one-module-per-task — and that is load-bearing for parallel agents.
But cutting a whole into parts creates **boundaries between the parts**, and those
boundaries are owned by no task by default. Every part can be individually correct,
tested, and reviewed, and the composition can still be wrong because an obligation
lived *between* two tasks' scopes.

Worked example from this repo (the failure this protocol would have caught):
`labels.py` correctly produces `holo_pocket_mask` **and** `functional_indices` **and**
`terminal_mask`, each implemented and unit-tested. The scoring pipeline consumes "the
pocket." The invariant `pocket ∩ functional == ∅` belonged to neither task — `labels`
owned the ingredients, `protocol` owned the gating, `analysis` owned the consumption —
so the exclusion was never assembled. It survived three reviews because every *node*
was green. There was no *edge* to be red.

Formally: tasks are charts, seams are the transition maps between them, and a
decomposition is only sound if the transition maps agree on their overlaps. This
protocol registers and verifies those transition maps. It is the process-level twin of
the cumulative-overlap gate the science already uses: **maximal overlap of parts with
the intended whole, minimal residual difference.**

## Definitions

- **Seam** — a shared boundary between two or more units (tasks, modules, branches)
  where an invariant must hold across the boundary for the composition to be correct.
- **Seam-invariant** — the property that must hold across the seam, stated as an
  assertion, not prose (`X ∩ Y == ∅`, `provenance(a) == "frozen"`, `map(a) == map(b)`).
- **Seam-owner** — exactly one task or agent responsible for the invariant holding.
  A seam with no owner is the defect condition this protocol exists to prevent.
- **Seam-test** — an executable check that exercises the invariant *across* the units,
  distinct from either unit's own tests. If a unit test on either side could catch it,
  it is not a seam-test.

## The registry

Seams live in a registry parallel to `tasks/` (e.g. `.ai/seams/`), one record each:

```
SEAM-0001  pocket-excludes-functional
  units:      labels.holo_pocket_mask  ->  <assembly>  ->  analysis (consumer)
  invariant:  assembled_pocket ∩ (functional ∪ terminal) == ∅   (per-target)
  owner:      TASK-00XX   (MUST be a real, open or done task — not "TBD")
  seam-test:  tests/test_seam_exclusion.py::test_pocket_disjoint_from_functional
  status:     OPEN | VERIFIED | WAIVED(reason, expiry)
  provenance: opened-by REVIEW-2026-07-XX ; decision-needed: KRAS Cys12 in/out
```

Seed it with the edges already known, *including the ones that are fine* — the green
records are proof-of-coverage, not clutter:

| Seam | Invariant | Status |
|---|---|---|
| labels seq-pocket ↔ superpose geom-pocket | the two constructions agree (`pocket_cross_map`) | **VERIFIED** — superpose flags disagreement |
| protocol firewall ↔ any label reader | held-out labels unreadable during selection | **VERIFIED** — `assert_readable` raises |
| pocket ↔ functional/terminal | assembled pocket excludes both | **OPEN** — no assembly step exists |
| report `AUC_*_optimised` ↔ protocol freeze | "optimised" AUCs are frozen/DEV provenance, not label-tuned | **OPEN** — unchecked; re-imports the §8 leak if false |
| classify_failure / verdict ↔ baselines | "signal" is beats-floor, not beats-chance/beats-H10 | **OPEN** — floor stubbed (`baselines.py`) |

## Gates (the teeth)

Two additions to the existing definition-of-done and green-bar, enforced by the same
commit-gate machinery that already checks claims and locks:

1. **Definition-of-done addendum.** A task may not move to DONE if it *opens* a seam it
   does not register. "Opens a seam" = its output is consumed by another unit, or it
   splits a responsibility that a previous unit held whole. Registering means: a
   SEAM record exists with a named owner and a named seam-test (the test may be
   `xfail` at open, but must exist).
2. **Green-bar addendum.** The repo is not green if any `status: OPEN` seam has no
   passing seam-test. `WAIVED` is allowed but must carry a reason and an expiry date;
   an expired waiver fails the bar. This prevents silent indefinite deferral — the
   mechanism, not discipline, remembers the edge.

## The seam sweep (the "shadow" pass)

Node-execution agents will not find seams — a seam is by definition outside any single
task's scope. So the protocol adds one **edge-discovery pass**, owned by a dedicated
review role, run at each phase boundary and before any multi-task merge:

1. Enumerate every cross-unit data flow (what does each module *consume* that another
   *produces*, and what does each branch inherit that another authored).
2. For each flow, name the invariant that must hold across it.
3. Check that invariant is either a VERIFIED seam or a newly-registered OPEN one.
4. Output: new SEAM records, never silent reconciliation.

This is the dual of the task backlog: the backlog asks "what work remains"; the sweep
asks "what connections between finished work remain unverified." The scaffold currently
has the first and not the second — this closes that asymmetry.

## Smells (open a seam when you see these)

- An invariant stated in a docstring but not asserted anywhere (docstring ≠ contract).
- Two tasks whose Intent Contracts each assume the *other* handles boundary case X.
- A module returns two things that "should" relate (a mask and its exclusion set) with
  no test on the relation.
- A consumer reads a field whose validity depends on *how* it was produced
  (provenance-carrying values: "optimised", "frozen", "holo-derived").
- A cross-model / cross-branch cherry-pick: the picked slice assumes context from the
  branch it left.

## What this is not

Not more upfront planning. Seams are discovered continuously, as units land, because
you cannot enumerate the edges of a decomposition until the nodes exist. This is
verification woven through the middle — the point on the uncertainty axis where the
work actually is — not a gate bolted to either end.
