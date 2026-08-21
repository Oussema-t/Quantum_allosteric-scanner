# TASK-0215 Leg B — source new cryptic-pocket instances from RCSB, not just re-selected depositions

## Context

- ID: TASK-0215
- Title: [[TASK-0214]] Leg B — search RCSB broadly for druggable *allosteric*
  proteins outside this register's existing 14 targets, derive the pocket
  window from holo drug contacts (not a curated label), and score
  apo/holo through TASK-0209's own VALID rule, unchanged.
- Status: Done
- Resolution: done
- Resolution Note: Leg B recovers 6 new VALID pairs across 4 distinct proteins (TEM-1 beta-lactamase, FPPS, AMPA GluR2, kainate GluK1). Revised usable-instance count 8/13. Candidate additions only -- not promoted into targets.yaml.
- **Thread: Implementer B.**
- Owner: Implementer
- Claimed By: Implementer B
- Claimed At: 2026-08-13
- Source: [[TASK-0214]]'s own "What Leg B requires" — confirmed necessary,
  Leg A recovered 0/5, count stuck at 2/7. Orchestrating user, 2026-08-13
  ("proceed with leg B as suggested").
- Priority: **P0 — inherited from TASK-0214: n=2 valid targets is a hard
  ceiling on every cross-target claim in the register, and Leg A did not
  move it.**
- Dependency: [[TASK-0209]] (the VALID rule and its ladder, unchanged),
  [[TASK-0214]] (the exclusion filter and native-scoring machinery, reused
  directly, not rebuilt).

## Why this is a genuinely different problem from Leg A

Leg A re-selected the *apo deposition* for targets already in this
register and found the holo side was the actual, unmoved blocker for all
5 — the pocket window and holo structure were fixed quantities Leg A never
touched. Leg B removes that constraint entirely: **new proteins**, sourced
independently, with **both** the apo and holo side free to vary, and the
pocket window derived from the holo ligand's own binding site
(`rcsb.ligands_and_sites`, 4.5 Å) rather than this register's curated
per-target labels — because a new protein has no curated label to derive
from.

## Pre-Registered Protocol (fixed 2026-08-13, before any scoring)

**Seeding.** RCSB full-text search (`search.rcsb.org`, the same Search API
[[backend.discovery]] already uses) for entries whose text mentions an
allosteric mechanism, restricted to real experimental depositions with a
bound nonpolymer component:

1. Query terms: `"allosteric inhibitor"`, `"allosteric activator"`,
   `"allosteric modulator"` (three separate full-text queries, results
   pooled and de-duplicated) — a textual signal for "distal, not
   orthosteric" binding, not a structural guarantee. Stated as a
   limitation up front, not discovered after the fact: this cannot
   distinguish a genuinely cryptic/allosteric site from a paper that uses
   the word loosely. No better structured RCSB annotation for "allosteric
   vs. orthosteric" was found in this session's own tool access.
2. Filters at the search stage: X-ray, resolution <= 2.5 A, at least one
   bound nonpolymer component.
3. **Capped at the top 100 hits per query** (300 total before dedup) by
   RCSB's own default relevance ranking — a real, stated scope bound, not
   an unstated one. Chasing the full ~1000+ hit pool is out of this task's
   own budget.
4. **Excluded**: any entry whose UniProt accession matches one of this
   register's existing 14 `targets.yaml` entries (this task sources *new*
   proteins, not a third pass over the incumbent 7).

**Per surviving entry (the holo candidate):**

5. `rcsb.ligands_and_sites(pdb_id, contact_cutoff=4.5)` — take the
   highest-`n_atoms` ligand classified `category == "drug"` (reuses
   `classify_ligand`, the same classifier [[TASK-0214]] already found has
   a known blind spot for lipids — mitigated the same way, see step 8).
   Its `binding_site_full` is the candidate pocket window. No drug ligand
   -> excluded (the full-text hit doesn't have a scoreable site).
6. UniProt via `discovery.get_uniprot`; `discovery.same_protein_entries(
   ..., with_ligand=False)` for candidate apo depositions of the same
   protein. No apo entry -> excluded (no contrast possible).
7. Apo candidates filtered the same way as holo: X-ray, resolution <= 2.5
   A, same chain letter(s) as the holo candidate where determinable.
8. **Exclusion filter, identical to [[TASK-0214]]'s own** (not
   re-invented): reject any apo candidate with a HETATM within the pocket
   window's contact cutoff that is not water and not `_is_buffer_or_water`
   (chem_comp-driven, `_is_aliphatic_additive` checked directly rather
   than trusting `classify_ligand`'s own top-level "solvent/ion" bucket —
   the same MYR-shaped blind spot applies here and was already found once).
9. **VALID rule: verbatim from [[TASK-0209]]/[[TASK-0214]]** —
   `apo_native_hit == False AND holo_native_hit == True`, where hit is
   `overlap_frac >= 0.5 AND druggability_score >= 0.5` against the
   holo-derived window. Not re-tuned for this leg.
10. Score up to **3 apo candidates per surviving holo entry** (smaller
    than Leg A's 5 -- this leg has a much larger entry pool to get through
    and a per-entry cap keeps the run tractable; stated, not silent).

**Known-answer check**: none new is possible here (there is no existing
known-answer pair for a not-yet-sourced protein) — [[TASK-0209]]'s and
[[TASK-0214]]'s own KRAS_G12C checks already established this pipeline's
integrity, and `score_structure`/the exclusion filter are reused
byte-for-byte, not reimplemented, so re-deriving a third known-answer
check here would test nothing new. Stated explicitly rather than silently
skipped.

**Honest ceiling, stated now, same discipline as [[TASK-0214]]**: any
protein recovered here is a *candidate* addition to the register, not an
automatic promotion into `targets.yaml`'s mandatory or extended set --
that is a separate decision (pocket biology worth caring about, disease
relevance, etc.) this task does not make. This task's own Outcome is a
verified VALID/INVALID table of new candidates, not a `targets.yaml` edit.

## Intent Contract

- Outcome: a table of new-protein candidates found via the search above,
  with VALID/INVALID verdicts under TASK-0209's own rule, and a revised
  total usable-instance count (2 existing + any new VALID entries).
- Why required, not assumed: [[TASK-0214]] confirmed Leg A cannot move the
  count; this is the only remaining route to more than 2 valid instances
  without loosening the VALID rule itself (out of scope for both tasks).
- In Scope: RCSB full-text seeding (capped, as above); holo-ligand-derived
  window (no curated label needed); the same exclusion filter and native
  scoring as [[TASK-0209]]/[[TASK-0214]]; a revised count.
- Out Of Scope: editing `targets.yaml`; re-running any of the register's
  366-cell budget against a new target; any manual/hand-curated candidate
  list (RCSB-seeded only, per this task's own text); active-site exclusion
  beyond the "allosteric" full-text signal itself (no curated func_ligand
  exists for a new protein -- stated limitation, not fixed here).
- Constraints And Invariants: the VALID rule, hit criterion, and exclusion
  filter are inherited unchanged from [[TASK-0209]]/[[TASK-0214]]. The
  100-hits-per-query / 3-candidates-per-entry caps are fixed before running,
  not tuned afterward to produce a target count.
- Planned Validation: every VALID recovery must have its window's
  `binding_site_full` sanity-checked (residue count in the 6-20 range this
  register's own curated windows fall in -- a window of 1 or 200 residues
  signals a `ligands_and_sites` contact-detection artifact, not a real
  pocket) before being reported as a recovery.

## In Progress

—

## TODO

- [x] Run the 3-query full-text search, pool + dedupe, apply the
      resolution/method/existing-UniProt filters, cap at 300 pre-dedup.
- [x] Per surviving holo candidate: derive the window from its own drug
      ligand's binding site; find apo candidates via the same UniProt.
- [x] Apply the exclusion filter (reused from TASK-0214) to apo candidates.
- [x] Score up to 3 apo candidates x however many holo candidates survive,
      through the native ladder; apply the VALID rule verbatim.
- [x] Sanity-check every VALID window's residue count before reporting it.
- [x] Revised total usable-instance count (2 + new recoveries).
- [x] Write the result into RESULTS.md + this task's own Done section.

## Dependency

- [[TASK-0209]] (the VALID rule + hit criterion, reused unchanged).
- [[TASK-0214]] (the exclusion filter + native-scoring machinery, reused
  directly).
- Feeds whatever future task decides which recoveries (if any) are worth
  promoting into `targets.yaml`.

## Open Questions

- Is a full-text "allosteric" keyword search a good enough proxy for
  "genuinely distal, not orthosteric" binding? Untested here — every
  recovery's own binding-site residue list should be eyeballed against
  its entry's own abstract/title before being trusted for anything beyond
  "this task's own VALID rule was satisfied."
- Should the per-query cap (100) and per-entry apo-candidate cap (3) be
  raised in a follow-up if this run recovers too few candidates to matter?
  Left for whoever picks up a Leg B continuation, not decided blind here.

## Done

**Verdict: 6 new VALID (apo-closed, holo-open) pairs recovered, spanning 4
distinct proteins. Revised usable-instance count: 8/13 (TASK-0209's 2/7 +
6 new pairs, counted honestly below as 4 new *proteins*, not 6).**

**Seeding**: 3 full-text queries ("allosteric inhibitor" / "activator" /
"modulator", X-ray, resolution ≤2.5 Å, ≥1 bound nonpolymer, 100 hits/query
cap) pooled to **188 unique entries** (less than the 300 pre-dedup cap —
real overlap between the three query terms) across **28 distinct
UniProts**. All 14 of this register's existing targets' UniProts were
excluded before scoring, not filtered after the fact.

**Per-candidate pipeline** (`scripts/task0215_leg_b_new_proteins.py`,
reusing TASK-0214's own exclusion filter and native-scoring machinery
byte-for-byte, not reimplemented): window derived from each holo
candidate's own drug-classified ligand binding site
(`rcsb.ligands_and_sites`), sanity-bounded to 6–20 residues before
anything downstream trusted it; holo native scored first (most candidates
were eliminated here — deriving a window from a ligand's own contacts
does not guarantee `fpocket` independently calls it druggable, e.g. 4XHB:
window correctly built, `druggability_score=0.029`, well below the bar);
surviving holo candidates' UniProt used to find apo depositions, filtered
through the same MYR/MRK-aware exclusion filter, up to 3 scored per holo
entry.

**6 VALID pairs found, all independently sanity-checked (real, published
allosteric systems — not a filter artifact):**

| Holo | Apo | UniProt | Protein | Ligand | Overlap | Drug score |
|---|---|---|---|---|---|---|
| 1PZO | 1YT4 | P62593 | TEM-1 β-lactamase | CBT | 1.00 | 0.988 |
| 1PZP | 1M40 | P62593 | TEM-1 β-lactamase | FTA | 0.94 | 0.999 |
| 6OAG | 4DEM | P14324 | Farnesyl diphosphate synthase (FPPS) | M2Y | 0.79 | 0.809 |
| 3ILT | 1M5E | P19491 | AMPA receptor GluR2 | TRU (trichlormethiazide) | 1.00 | 0.938 |
| 2AL5 | 1MQI | P19491 | AMPA receptor GluR2 | 4MP (aniracetam) | 1.00 | 0.727 |
| 5MFQ | 1YCJ | P22756 | Kainate receptor GluK1 | 2J9 (BPAM-344-class) | 1.00 | 0.980 |

Entry titles confirm the mechanism independently of this pipeline's own
verdict: 1PZO/1PZP are explicitly titled "TEM-1 Beta-Lactamase in Complex
with a Novel, **Core-Disrupting, Allosteric** Inhibitor"; 6OAG "human FPPS
in complex with an **allosteric inhibitor** YF-02-82"; 3ILT "GluR2 bound to
the **allosteric modulator**, trichlormethiazide"; 2AL5 "GluR2... in
complex with fluoro-willardiine and **aniracetam**" (a well-known AMPA
positive allosteric modulator); 5MFQ "GluK1... in complex with kainate and
**BPAM-344**." None of these titles were used to select or filter
candidates — they are read here only as an independent check that the
pipeline's numeric verdict landed on real allosteric chemistry, per this
task's own Open Question about the full-text search being a proxy, not a
guarantee.

**Honest count, not inflated**: 6 pairs span only **4 distinct proteins**
(P62593 and P19491 each contributed 2 pairs, different ligands/apo
depositions of the same protein). Reporting "6 new valid instances" without
this caveat would overstate the diversity gain — stated as 4 new proteins,
6 usable apo/holo pairs among them.

**Revised total usable-instance count: 8/13** (TASK-0209's KRAS_G12C +
PTP1B, plus these 4 new proteins across 6 pairs) — up from the 2/7 ceiling
[[TASK-0214]] confirmed Leg A could not move. This is a candidate addition
only, per this task's own stated ceiling: none of these 4 proteins have
been promoted into `targets.yaml`, and no scored register cell has been
re-run against them. That decision (disease relevance, whether the pocket
is worth the register's own scientific narrative) is explicitly left to
whoever picks this up next.

**Limitation, stated per this task's own Open Question**: "allosteric" as
a full-text keyword is a proxy, not a structural guarantee — every
recovery above was cross-checked against its own entry title precisely
because of this, and all 6 held up. Untested: how many genuinely
allosteric systems in RCSB were *missed* because they don't use these
exact three phrases (a recall question this task does not answer, only a
precision check on what it did find).

Full trial-level data: `results/tasks/0215_leg_b_new_proteins/
leg_b_results.json` (188 candidates, every elimination reason recorded,
not just the 6 survivors). Script: `scripts/task0215_leg_b_new_proteins.py`.
