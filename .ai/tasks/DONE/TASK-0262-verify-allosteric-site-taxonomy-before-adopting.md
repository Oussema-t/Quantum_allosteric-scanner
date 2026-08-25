# TASK-0262 — Verify the "Type I–IV" allosteric site taxonomy before adopting it

- Status: Done
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

- [x] Establish whether a canonical Type I–IV **allosteric site** taxonomy
      exists in the literature, distinct from the kinase-inhibitor Type I–IV
      classification. Verify live (Crossref/publisher record), not from
      recall.
- [x] If it exists: get the primary citation, the exact class definitions, and
      whether the classes are defined by **distance**, **mechanism**, or
      **structural relationship**. Our bins are distance-based; a
      mechanism-based taxonomy is not interchangeable with them.
- [x] Check what the ASD itself actually uses as a site classification, if
      anything. [[TASK-0229.003]] already had to work around an expired TLS
      certificate on the ASD endpoint — reuse that finding rather than
      rediscovering it.
- [x] Spot-check the four cited exemplars against our own data: is KRAS
      Switch-II under 5 Å in our measurement (we measure **1.32 Å** minimum
      heavy-atom), is BCR-ABL1's site inter-domain (we measure **7.96 Å**,
      category proximal), is CARDIAC_MYOSIN inter-subunit ([[TASK-0251]] says
      yes, and that the challenge's catalytic-domain scope truncates it).
- [x] **Outcome A** — it exists and is distance-or-structure based: map our
      categories onto it, keep both, and cite it properly.
- [x] **Outcome B** — it does not exist as described, or is kinase-specific:
      keep our own bins, and record in [[TASK-0258]] and the brief that a
      literature taxonomy was sought and not found. That is itself a useful
      statement for the submission.

## Acceptance

- [x] A verified answer, either way, with citations.
- [x] If adopted: a mapping table from our distance bins to the taxonomy, with
      the four exemplars checked against our measurements.
- [x] If not adopted: a one-line record in `TASK-0258`'s script docstring and
      the brief saying so, so the question is not reopened from scratch.

## Done

**2026-08-25.** Outcome B, decisively — the proposed taxonomy does not exist.
Not adopted. Own bins stand undecorated.

**No general "allosteric site" Type I–IV taxonomy found**, live-searched, not
recalled — full-text search for a structural/distance-based Type I–IV
allosteric-*site* classification (as opposed to kinase inhibitors) returned
nothing canonical. The one candidate general classification found
(Tsai, del Sol & Nussinov 2009, *Mol Biosyst*, a real, checked paper) uses a
**six-descriptor functional scheme** — cooperativity sign, thermodynamic
driver, oligomeric state, etc. — not a Type I–IV structural-distance ladder
at all. **ASD itself defines no such taxonomy** either — checked directly
against the live ASD site (its own front matter mentions "SITE" and
"ALLOSITE-POTENTIAL" modules, no structural-type classification of any
kind).

**A real Type I–IV taxonomy exists, but it is not this one.** It classifies
**kinase inhibitors** by conformational/ATP-pocket relationship — Type I
(ATP-competitive, active/DFG-in), Type II (ATP-competitive, inactive/DFG-out),
Type III (allosteric, adjacent "back pocket" next to the ATP site), Type IV
(allosteric, remote from the ATP site) — Dar AC, Shokat KM. *Annu Rev
Biochem.* 2011;80:769-795, doi:10.1146/annurev-biochem-090308-173656
(Types I–III); extended to IV by Gavrin LK, Saiah E. *MedChemComm.*
2013;4:41-51, doi:10.1039/c2md20180a. Both DOIs verified live via Crossref.
**This is a genuinely different classification** — defined by conformational
state and ATP-pocket relationship, kinase-specific — not the distance/
structural-relationship scheme (proximal/intra-domain/inter-domain/
inter-subunit) the external proposal described under the same four labels.
Reusing the label "Type I–IV" for both would be a real, citable-looking but
false equivalence — exactly this task's own Constraint.

**Exemplar spot-check against this project's own real measurements**
(`results/tasks/0258_allosteric_distance_taxonomy/pocket_taxonomy.json`,
[[TASK-0258]]'s own script, real structures, not assumed):

| target | proposed type / exemplar | our measurement | verdict |
|---|---|---|---|
| KRAS_G12C (Switch-II) | Type I, <5 Å, contiguous with cleft | min_A=**1.32 Å**, category `contact-adjacent` | distance claim roughly holds |
| BCR_ABL1 (SH2/SH3–catalytic interface) | Type III, inter-domain/hinge | min_A=**7.96 Å**, category `proximal`, same_chain=True | **exemplar is a different site** — the SH2/SH3-kinase interface is [[TASK-0229.003]]'s own real *second* BCR_ABL1 site (5DC4 monobody), not the myristoyl pocket this project's own pipeline actually scores |
| CARDIAC_MYOSIN | Type IV, inter-subunit/quaternary | min_A=11.81 Å, category `proximal`, **same_chain=True** | **classification doesn't match this pipeline's own construct** — the true SRX/IHM mechanism *is* inter-subunit ([[TASK-0251]]), but the scope-truncated single-chain structure this project actually scores is not (same_chain=True, not `inter-chain`) |
| PTP1B (α7 helix, not in this task's own required 3, checked anyway) | Type II, intra-domain distal | min_A=11.24 Å, category `proximal`, same_chain=True | loosely consistent (intra-domain, distal-leaning) — no formal taxonomy to check it against either way |

Two of three required exemplars fail on inspection — not close calls. BCR_ABL1's
named exemplar site is real but is a *different pocket* than the one this
register scores; CARDIAC_MYOSIN's "inter-subunit" label describes the real
biology, not what the challenge's own scope-truncated construct lets this
pipeline actually measure. Adopting the taxonomy would have meant citing
exemplars this project's own data contradicts.

**Recorded, per this task's own Acceptance**: one-line-plus-citation note
added to `task0258_allosteric_distance_taxonomy.py`'s own module docstring
(the mapping table above, condensed); `documentation/CTQW_CONTRIBUTION_
BRIEF.html`'s existing line ("Bin edges in section 08 are ours... not a
literature taxonomy") already stated the right conclusion — left as-is,
correct and sufficient, not rewritten to restate this task's own longer
argument.

**Not done, and why**: PTP1B was checked as a bonus (not one of the task's
own 3 required exemplars) — no formal verdict rendered on it since no real
taxonomy exists to check it against either way. The Tsai/del Sol/Nussinov
2009 six-descriptor scheme was not adopted or mapped onto our bins — it is
a real, different, functionally-defined (not distance-defined) classification,
out of this task's own scope to integrate.

**Validated**: both DOIs (Dar & Shokat, Gavrin & Saiah) confirmed live via
Crossref, not from memory. Exemplar numbers pulled directly from
[[TASK-0258]]'s own already-computed, real-structure results file, not
re-derived or assumed.

## Constraint

Do not adopt a taxonomy to make our categories look more authoritative. Our
own bins are defensible precisely because we declare them as ours. Borrowed
authority that does not survive a referee's check is worth less than none.
