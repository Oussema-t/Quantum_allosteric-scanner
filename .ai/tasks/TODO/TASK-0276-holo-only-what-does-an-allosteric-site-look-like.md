# TASK-0276 — Holo-only: is an allosteric site structurally distinguishable *at all*, even with the answer in hand?

- Status: TODO
- Assignee: unassigned (suggest a dedicated thread — this is a multi-stage study, not a single run)
- Priority: **Highest — it measures the ceiling every other task in this register has been working beneath without knowing it**
- Filed: 2026-08-26 by Reviewer
- Related: [[TASK-0273]], [[TASK-0270]], [[TASK-0258]], [[TASK-0259]], [[TASK-0254]], [[TASK-0265]]

## The gap, and it is a large one

**Holo structures have only ever been used to generate the label.** Every
score in this register is computed on apo; holo supplies "which residues are
within 4.5 Å of the drug" and nothing else. [[TASK-0273]] compared holo
structures to one another, but only through that same label — Jaccard overlap
of contact sets. **No structural feature has ever been computed on a holo
structure and compared across them.**

Bartosz's framing, 2026-08-26: *"True allostery happens in holo structures. So
we should be inspecting holo structures for that. Have we been doing so for
KRAS?"* The answer is **no**.

## The control nobody ran

Every negative in this register is of the form *"method X cannot predict the
allosteric pocket from apo."* Nine such attempts have now failed
([[TASK-0263]], [[TASK-0260]], [[TASK-0269]], [[TASK-0266]], [[TASK-0257]],
[[TASK-0268]], [[TASK-0271]], [[TASK-0273]], [[TASK-0274]]).

**Nobody has asked whether it is distinguishable with the answer in hand.**

If an allosteric site cannot be separated from other cavities *in the holo
structure itself* — where all the information is present — then the task is
not hard, it is **ill-posed from structure alone**, and no method, quantum or
classical, could ever have worked. That is the ceiling every result here has
been sitting beneath, unmeasured.

## The leakage trap — read before designing anything

A holo pocket is open **because** the drug is in it. So "find the open cavity"
trivially recovers the label and proves nothing. Any design that scores cavity
volume or openness on holo is measuring the drug's imprint.

**The sharp version that avoids this: in a holo structure, is the *allosteric*
site distinguishable from the *orthosteric* site?** Both are ligand-occupied,
both are open, both leave an imprint. If allostery has a common structural
denominator, that is where it must show up. Design around this comparison, not
around allosteric-vs-empty-cavity.

## Staged design, per Bartosz's own sequencing

### Stage 1 — within one family (KRAS)

- [ ] Assemble the verified KRAS holo ensemble — ten structures, ten different
      drugs, already enumerated and checked in [[TASK-0270]]: `8AZX`/BI-2865,
      `7A1X`/QWB, `8QUG`/WYU, `9UOH`/ASP2453, `7YCE`/IQN, `7MDP`/Z07,
      `7RP3`/MKZ, `8AFC`/LXK, `8S8C`/MK-1084, `6OIM`/sotorasib. Re-verify live;
      [[TASK-0155]]'s pool was wrong on 8 of 10 and that is exactly how.
- [ ] Compute structural features on each **holo** structure with the ligand
      stripped: `V_C` (DCC centrality — the strongest single term per
      [[TASK-0275]]), `V_B`, SASA, degree, fpocket descriptors.
- [ ] **Allosteric vs orthosteric within the same structure**: does any
      feature separate the Switch-II pocket from the GDP/GTP site? Report per
      structure and pooled.
- [ ] **Commonality across the ten**: which residues/features are shared by
      the allosteric site across all ten drugs, and which are drug-specific?
      This is the "common denominator" question directly.

### Stage 2 — a second family, independently

- [ ] Repeat on a second protein with real holo coverage — candidates with
      multiple ligands already in hand: **HCV_NS5B**, **GAC**, **PKR**,
      **TRP_SYNTHASE**, **KSHV_PROTEASE**. Pick on coverage, and **fix the
      choice before looking at Stage 1's outcome.**
- [ ] Ask the same two questions. Does *this* family show a within-family
      commonality?

### Stage 3 — across families

- [ ] Only if Stages 1 and 2 each found something: is the commonality **the
      same** across families, or family-specific?
- [ ] A family-specific signature is still a real finding — it would mean
      allostery has no single structural denominator, which is itself the
      answer to the question and consistent with [[TASK-0258]]'s taxonomy
      (58% contact-adjacent, 27% proximal, 15% intermediate, 0% remote).

## What each outcome means — decide the interpretation in advance

| Stage 1 outcome | reading |
|---|---|
| No feature separates allosteric from orthosteric, even in holo | **The task is ill-posed from structure alone.** The single most important result this register could produce, and it would explain all nine failures at once. |
| A signature exists in holo and is shared across drugs | Then ask whether any trace survives into apo — that becomes the real predictive question, and gives Phase 2 a concrete target. |
| A signature exists but is drug-specific | Supports [[TASK-0265]]'s finding that allostery is partly a property of the ligand, not the pocket. |

## Acceptance

- [ ] Verified holo ensemble manifests for both families.
- [ ] Allosteric-vs-orthosteric discrimination per structure, with the
      leakage control stated and honoured.
- [ ] Within-family commonality reported for each family separately, before
      any cross-family comparison.
- [ ] An explicit verdict against the table above.
- [ ] `RESULTS.md`.

## Constraint

**Do not use holo-derived features to predict the holo-derived label and
report it as a result.** That is circular, and it is the most likely way this
task goes wrong. The output is a *descriptive characterisation* and a
*ceiling measurement*, not a predictor. If a signature is found, the
predictive question is a separate, later task, and it must be tested on apo.
