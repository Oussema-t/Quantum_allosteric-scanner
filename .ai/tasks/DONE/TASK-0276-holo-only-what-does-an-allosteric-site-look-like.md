# TASK-0276 — Holo-only: is an allosteric site structurally distinguishable *at all*, even with the answer in hand?

- Status: Done
- Assignee: Implementer A (claimed via user-authorized override of a reserved-but-unimplemented placeholder held by reviewer-opus)
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

- [x] Assemble the verified KRAS holo ensemble — ten structures, ten different
      drugs, already enumerated and checked in [[TASK-0270]]: `8AZX`/BI-2865,
      `7A1X`/QWB, `8QUG`/WYU, `9UOH`/ASP2453, `7YCE`/IQN, `7MDP`/Z07,
      `7RP3`/MKZ, `8AFC`/LXK, `8S8C`/MK-1084, `6OIM`/sotorasib. Re-verify live;
      [[TASK-0155]]'s pool was wrong on 8 of 10 and that is exactly how.
- [x] Compute structural features on each **holo** structure with the ligand
      stripped: `V_C` (DCC centrality — the strongest single term per
      [[TASK-0275]]), `V_B`, SASA, degree, fpocket descriptors.
- [x] **Allosteric vs orthosteric within the same structure**: does any
      feature separate the Switch-II pocket from the GDP/GTP site? Report per
      structure and pooled. (4 of 5 features do, significantly, at n=10.)
- [x] **Commonality across the ten**: which residues/features are shared by
      the allosteric site across all ten drugs, and which are drug-specific?
      This is the "common denominator" question directly. (16-residue
      consensus at K=6/10; pairwise Jaccard median 0.650 across all 10.)

### Stage 2 — a second family, independently

- [x] Repeat on a second protein with real holo coverage — candidates with
      multiple ligands already in hand: **HCV_NS5B**, **GAC**, **PKR**,
      **TRP_SYNTHASE**, **KSHV_PROTEASE**. Pick on coverage, and **fix the
      choice before looking at Stage 1's outcome.** (HCV_NS5B chosen for its
      4 distinct chemotypes, most of the candidate list, decided before any
      Stage 1 number was computed.)
- [x] Ask the same two questions. Does *this* family show a within-family
      commonality? (Same feature directions as KRAS on all 5; commonality is
      real but site-specific — two disjoint allosteric sites, each
      near-perfectly self-consistent, see Done.)

### Stage 3 — across families

- [x] Only if Stages 1 and 2 each found something: is the commonality **the
      same** across families, or family-specific? (Both found something. The
      FEATURE signature — V_C/fpocket up, degree down — is the same direction
      in both families. The specific RESIDUE commonality is family- and even
      site-specific, per HCV_NS5B's own two-disjoint-sites finding.)
- [x] A family-specific signature is still a real finding — it would mean
      allostery has no single structural denominator, which is itself the
      answer to the question and consistent with [[TASK-0258]]'s taxonomy
      (58% contact-adjacent, 27% proximal, 15% intermediate, 0% remote).
      (Not what was found: the FEATURE-level signature IS shared across
      families; only the exact residue set is family/site-specific.)

## What each outcome means — decide the interpretation in advance

| Stage 1 outcome | reading |
|---|---|
| No feature separates allosteric from orthosteric, even in holo | **The task is ill-posed from structure alone.** The single most important result this register could produce, and it would explain all nine failures at once. |
| A signature exists in holo and is shared across drugs | Then ask whether any trace survives into apo — that becomes the real predictive question, and gives Phase 2 a concrete target. |
| A signature exists but is drug-specific | Supports [[TASK-0265]]'s finding that allostery is partly a property of the ligand, not the pocket. |

## Acceptance

- [x] Verified holo ensemble manifests for both families.
- [x] Allosteric-vs-orthosteric discrimination per structure, with the
      leakage control stated and honoured.
- [x] Within-family commonality reported for each family separately, before
      any cross-family comparison.
- [x] An explicit verdict against the table above.
- [x] `RESULTS.md`.

## Constraint

**Do not use holo-derived features to predict the holo-derived label and
report it as a result.** That is circular, and it is the most likely way this
task goes wrong. The output is a *descriptive characterisation* and a
*ceiling measurement*, not a predictor. If a signature is found, the
predictive question is a separate, later task, and it must be tested on apo.

## Done (2026-08-26, Implementer A)

**Row 2 of the task's own outcome table: a real signature exists in holo,
and it is shared across drugs.** Not row 1 (ill-posed) — the single most
consequential possible negative for this entire register did not happen.

**Method, avoiding the leakage trap as designed**: self-referential
throughout — every holo structure supplies its own 5 ligand-stripped
features (`V_C` GNM DCC centrality, `V_B` raw B-factor, `degree`, `SASA`,
`fpocket` druggability) AND its own two label groups (allosteric drug
contact vs. orthosteric catalytic/GDP site), never an apo structure. The
comparison is allosteric-vs-orthosteric, never allosteric-vs-empty-cavity —
both groups are real, independently-defined, ligand-adjacent-or-catalytic
sites in the same structure. SASA and fpocket both computed on a genuinely,
physically ligand-stripped copy (a separate temp file per structure), not
merely excluded from the report — the specific leakage risk the task's own
module docstring calls out by name.

**Stage 1, KRAS_G12C, n=10/10 usable** (all live-verified per
[[TASK-0270]]'s own pool, [[TASK-0273]]'s own re-verification reused):
4 of 5 features discriminate allosteric from orthosteric significantly at
this ensemble's finest cluster resolution (each of the 10 is its own
cluster, no shared apo among them): `fpocket` AUC median 0.675 (p=0.0039),
`degree` 0.405 — orthosteric ranks HIGHER (p=0.0020), `V_C` 0.595
(p=0.0117), `SASA` 0.551 (p=0.0215); `V_B` 0.587 not quite significant
(p=0.0742). The `degree`-vs-`V_C` disagreement in DIRECTION is the sharpest
part of this finding: the allosteric site is not simply "the well-connected
residues" -- raw static connectivity favors the orthosteric site, while the
dynamics-aware DCC-coupling measure favors the allosteric one. Commonality:
16-residue consensus at K=6/10 (Switch-II pocket, matches the register's
own prior knowledge), pairwise allosteric-site Jaccard median 0.650 across
all 10 chemically-unrelated-drug pairs.

**Stage 2, HCV_NS5B, n=4/4 usable, family fixed on coverage grounds before
any Stage 1 number was computed**: every feature moves in the SAME
direction as KRAS (`V_C` up -- AUC=1.000 in literally all 4 structures,
`fpocket` up, `degree` down), in a protein sharing nothing else with KRAS
(different fold, different function -- viral RNA polymerase vs. a small
GTPase -- and a completely different orthosteric-resolution mechanism,
`backend.active_site.detect_active_site`'s live UniProt call rather than a
co-bound ligand; verified directly that this resolves to the real GDD/YGDD
catalytic motif, not a topological-proxy fallback). Cluster-robust p-values
are floor-limited at 0.5 with only 2 independent clusters (CMF/POO share
apo 2HAI, VR1/VRX share apo 2GIQ) -- `V_C=1.000` in all 4 structures is a
maximal, noise-free effect the test cannot express as significant with this
few clusters, reported as floor-limited, not conflated with "not
significant" in the ordinary sense. **Commonality, properly stratified --
more informative than a flat consensus number**: within-apo-pair Jaccard
0.941 (CMF vs POO; VR1 vs VRX) but ACROSS-pair Jaccard 0.000 -- NS5B has
(at least) two disjoint allosteric sites, each near-perfectly self-
consistent across its own chemotype, not one common site the way KRAS has.

**Stage 3**: the FEATURE-level signature (which features separate the two
site classes, and in which direction) is the same across both independent
families. The specific RESIDUE-level commonality is family- and even
site-specific (HCV_NS5B's own two-disjoint-sites result). Both halves of
this are real, reported with equal prominence, matching the task's own
"a family-specific signature is still a real finding" framing -- except the
finding here is sharper than pure family-specificity: the underlying
*dynamical signature* generalizes even where the *residues* don't.

**Two real bugs found and fixed en route, one at the shared-module level**:
(1) `9UOH`/`8S8C` (5-character extended chemical-component IDs) fail
prody's legacy PDB parser -- the same limitation [[TASK-0273]] hit, fixed
this time inside `allostery.clean.clean()` itself (mmCIF fallback on
`PDBParseError`) rather than duplicated per-script, since this is now the
second task to need it. Verified non-regressing: all 12 `test_clean.py`
tests still pass; full suite re-run clean except 2 pre-existing failures
independently confirmed unrelated (a stale test expecting KRAS_G12C's
pre-[[TASK-0270]] apo `4OBE`, and a documentation-text linter hitting an
old quoted `RESULTS.md` line). (2) A second, subtler bug this task's own
script then hit: prody's mmCIF parser assigns each HETATM group its OWN
chain letter (unlike the legacy parser, which keeps it on its neighboring
protein chain's letter) -- restricting to `chain A` before extracting
ligand groups silently dropped both GDP and the drug for the 2 affected
entries, collapsing their active-site resolution to the tier-3
topological-proxy fallback (n=5) and their pocket to empty. Fixed locally
in this task's own script by extracting ligand groups from the
unrestricted parse. Caught by inspecting the actual per-structure numbers
(n_active_site=5 was visibly wrong), not assumed correct from a clean exit
code.

**Constraint honored**: no predictor was built or scored against its own
label; every number here is a within-structure discrimination AUC between
two independently-labeled groups, or a Jaccard/consensus over those same
groups -- a descriptive characterization and ceiling measurement, exactly
as required. The natural next task (explicitly NOT attempted here) is
whether `V_C` specifically -- the one feature with no notion of pocket
shape or drug-likeness, and therefore the hardest to dismiss as "of course
a drug pocket looks druggable" -- survives into apo. This task gives that
follow-up a concrete, real target for the first time.

**Validation**: script reruns clean (3 full runs: initial, post-`clean()`-fix,
post-chain-scoping-fix; final run's numbers are what's reported here).
Every structure fetched live via RCSB through `pdb_cache/` (TASK-0273's own
cache-hygiene fix, confirmed still in effect). `pytest tests/` re-run in
full during this task (not just `test_clean.py`) to verify the shared-module
edit; 2 pre-existing failures confirmed unrelated by direct inspection of
their assertion content.

**Script:** `scripts/task0276_holo_only_structural_signature.py`. **Data:**
`results/tasks/0276_holo_only_structural_signature/holo_only_structural_signature.json`.
**Also touched:** `src/allostery/clean.py` (mmCIF fallback, shared fix).

**2026-08-26 note ([[TASK-0279]]) — how this task's own `V_C` positive
should now be read.** [[TASK-0278]] flagged the gap this task's own
Constraint left open: does `V_C` measure allosteric *efficacy*, or just
that a cavity is occupied and coupled? [[TASK-0279]] closed on BCR-ABL1's
own controlled pair (`1OPL`/myristate, inert vs `5MO4`/asciminib,
efficacious, same pocket, node sets matched via `align_apo_holo`). **`V_C`
was HIGHER on the inert myristate pocket than the efficacious asciminib
pocket in 16/16 matched residues** — the opposite direction the
efficacy-specific reading required, though a real resolution confound
between the two structures (3.42 Å vs 2.17 Å) keeps that task's own result
from being a clean proof either way. **Read this task's own positive as:
a real holo-side structural pattern separating allosteric from orthosteric
sites, not yet distinguished from an occupancy/cavity-coupling
explanation** — the "does it survive into apo" follow-up this task's own
Done section deferred is still the right next question, but should not be
read as testing a confirmed *functional* signature until [[TASK-0279]]'s
own gap is closed some other way (a resolution-matched inert-vs-efficacious
pair, if one is ever found).
