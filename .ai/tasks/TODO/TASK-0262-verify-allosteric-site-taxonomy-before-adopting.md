# TASK-0262 — Verify the "Type I–IV" allosteric site taxonomy before adopting it

- Status: TODO
- Assignee: unassigned (suggest Explorer — this is a literature-verification task, not a coding one)
- Priority: Medium — but **blocking** for anything that cites a taxonomy in the Phase 1 submission
- Filed: 2026-08-25 by Reviewer
- Related: [[TASK-0258]] (our own distance bins), [[TASK-0137]] (citation-verification audit), [[TASK-0169]], [[TASK-0251]]

## Context

[[TASK-0258]] replaced the unjustified `MIN_HOP >= 2` filter with reported
heavy-atom distance plus a site category, using **this register's own bin
edges**, stated openly in the script docstring as ours and explicitly *not*
presented as a literature taxonomy.

An external model then proposed we map onto an "established biophysical and
Allosteric Database (ASD) structural taxonomy":

| proposed type | description given |
|---|---|
| Type I | Second-sphere / proximal sub-pockets, <5 Å, contiguous with the orthosteric cleft (KRAS Switch-II cited) |
| Type II | Intra-domain distal sites, same tertiary domain (PTP1B α7 helix cited) |
| Type III | Inter-domain / hinge sites (BCR-ABL1 SH2/SH3–catalytic interface cited) |
| Type IV | Inter-subunit / quaternary interfaces (caspase dimer interface, haemoglobin cited) |

## Why this needs verifying rather than adopting

**A well-established Type I–IV taxonomy exists for _kinase inhibitors_** —
Type I ATP-competitive, Type II DFG-out, Type III allosteric adjacent to the
ATP site, Type IV allosteric and remote. The suggestion above may be that
taxonomy generalised to allosteric *sites* across all protein families, which
is a different and possibly non-existent classification.

Adopting a taxonomy that turns out not to exist as stated — or that exists
only for kinases — in a document going to the challenge organisers would be a
worse error than using our own openly-declared bins. This register has been
caught by exactly this class of problem before ([[TASK-0169]]: the challenge's
own named validation structure does not contain the ligand its table claims;
[[TASK-0137]]: a citation's author list was wrong in a filing task).

## Scope

- [ ] Establish whether a canonical Type I–IV **allosteric site** taxonomy
      exists in the literature, distinct from the kinase-inhibitor Type I–IV
      classification. Verify live (Crossref/publisher record), not from
      recall.
- [ ] If it exists: get the primary citation, the exact class definitions, and
      whether the classes are defined by **distance**, **mechanism**, or
      **structural relationship**. Our bins are distance-based; a
      mechanism-based taxonomy is not interchangeable with them.
- [ ] Check what the ASD itself actually uses as a site classification, if
      anything. [[TASK-0229.003]] already had to work around an expired TLS
      certificate on the ASD endpoint — reuse that finding rather than
      rediscovering it.
- [ ] Spot-check the four cited exemplars against our own data: is KRAS
      Switch-II under 5 Å in our measurement (we measure **1.32 Å** minimum
      heavy-atom), is BCR-ABL1's site inter-domain (we measure **7.96 Å**,
      category proximal), is CARDIAC_MYOSIN inter-subunit ([[TASK-0251]] says
      yes, and that the challenge's catalytic-domain scope truncates it).
- [ ] **Outcome A** — it exists and is distance-or-structure based: map our
      categories onto it, keep both, and cite it properly.
- [ ] **Outcome B** — it does not exist as described, or is kinase-specific:
      keep our own bins, and record in [[TASK-0258]] and the brief that a
      literature taxonomy was sought and not found. That is itself a useful
      statement for the submission.

## Acceptance

- [ ] A verified answer, either way, with citations.
- [ ] If adopted: a mapping table from our distance bins to the taxonomy, with
      the four exemplars checked against our measurements.
- [ ] If not adopted: a one-line record in `TASK-0258`'s script docstring and
      the brief saying so, so the question is not reopened from scratch.

## Constraint

Do not adopt a taxonomy to make our categories look more authoritative. Our
own bins are defensible precisely because we declare them as ours. Borrowed
authority that does not survive a referee's check is worth less than none.
