# TASK-0291 — One drug, several "pockets": sequence strips, fpocket splitting, or genuinely separate cavities?

- Status: Done
- Assignee: Reviewer thread
- Priority: Medium — answers a user question and **refines [[TASK-0288]] Finding F**
- Filed: 2026-08-29 by Reviewer thread (user question, prompted by a collaborator's output showing one drug's contacts split across several pockets)
- Related: [[TASK-0288]], [[TASK-0289]], [[TASK-0258]], [[TASK-0254]]

## The question

A collaborator's output categorises one drug's contact residues into
several separate pockets. User's analogy: a noodle wrapped around a
meatball — one ball, but unwinding the noodle shows several separate
sauce strips. Is that what is happening, a different mechanism, or a
software artifact?

Three mechanisms, separated by two independent measurements on the raw
drug-contact set:

| | measurement | signature |
|---|---|---|
| (a) sequence strips | contiguous resnum runs | many strips, ONE spatial component |
| (b) fpocket splitting | fpocket candidates overlapping one drug site | 1 cavity but >1 numbered pocket |
| (c) separate cavities | inter-component Cα distance | components >14 Å apart |

**This analysis never calls `detect_active_site`** — it uses the raw
drug-contact set before the active-site subtraction — so it is **immune
to the [[TASK-0289]] non-determinism**, unlike every `min_A`-based result.

## Findings

**The analogy is correct, and (a) is universal.** Sequence segments per
drug site: **median 9, range 2–13, and never 1** across 33 targets. Every
drug site in this register is lined by residues from many
sequence-distant strips. That is ordinary protein folding, not an artifact.

**But "several pockets" in a tool's output is usually (b), not (a).**
fpocket assigns a **median of 4** distinct numbered pockets to a single
drug's contact set (range 1–14), and the best single candidate covers
only a **median 0.56** of that drug's contacts. In **11/33** targets the
cavity is provably single (one connected component) yet fpocket still
places more than one numbered pocket on it. **That split is an artifact
of alpha-sphere clustering, not biology.**

**(c) is real for about a quarter of targets.** Of 33: 14 have a single
spatial component; 10 more have all components within 14 Å (two walls of
one wide cavity); **9 have contact clusters more than 14 Å apart** —
`TRP_SYNTHASE` (up to **38.4 Å**, the α/β substrate tunnel),
`SUMO_E1_FHJ` (29.1 Å), `KSHV_PROTEASE` (27.9 Å). So **24/33 are one
physical pocket; 9/33 genuinely span separate regions.**

The 14 Å cut is a **judgment call** — roughly the longest dimension of a
large drug — not a derived constant. It is recorded in the results JSON.

## Refinement to [[TASK-0288]] Finding F — important

`min_A` is a **minimum** over the drug's contact residues. For a
dispersed site it reports the nearest strip, not the site. Checking the
spike targets on dispersion:

| target | min_A | median_A | max_A | comps | widest gap |
|---|---|---|---|---|---|
| FPPS_YF0282 | 1.33 | 2.98 | **5.87** | 1 | — |
| FBPASE_95S | 1.35 | 3.97 | **5.93** | 2 | 9.4 |
| PF_ATCASE | 1.36 | 2.33 | **6.88** | 3 | 18.0 |
| TEM1_BLA_CBT | 1.33 | 3.48 | **7.09** | 1 | — |
| DHPS_GC7 | 1.33 | 3.34 | **8.18** | 3 | 19.5 |
| MKK7_IBRUTINIB | 1.32 | 6.00 | **8.23** | 1 | — |
| GLUK1_BPAM | 1.32 | 6.56 | **8.31** | 1 | — |
| KRAS_G12C | 1.31 | 6.96 | 14.43 | 1 | — |
| TRP_SYNTHASE_F6F | 1.29 | **14.10** | **20.52** | 7 | **38.4** |

**Seven of the nine have their ENTIRE drug-contact set within 8.4 Å of
the active site** — for those, "not a distal site" is *stronger* than
`min_A` alone said, since it holds for every contact residue, not just
the closest.

**Two do not.** `TRP_SYNTHASE` (median 14.1 Å, spanning 38 Å) and to a
lesser degree `KRAS_G12C` (max 14.4 Å) touch the active site with one
strip while extending well away. For those, `min_A ≈ 1.3 Å` was
misleading and should not be read as "the pocket is the active site".

**Consequence:** Finding F should be reported on `max_A`, not `min_A` —
"the entire annotated drug site lies within 8.4 Å of the active site" for
7 targets — which is both more defensible and a stronger claim.
Recommended for [[TASK-0290]]'s recompute.

## Next

- [[TASK-0290]] should recompute `max_A` and `median_A` alongside `min_A`
  and restate Finding F on `max_A`.
- Worth telling the collaborator that the multi-pocket split they are
  seeing is **mostly fpocket's clustering**, not distinct biology — with
  the 11/33 and median-0.56-coverage numbers as evidence.
