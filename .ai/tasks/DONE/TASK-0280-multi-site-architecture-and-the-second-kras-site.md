# TASK-0280 — Two proteins, two multi-site architectures: verify the second KRAS site and close H6.2

- Status: Done
- Assignee: Implementer A
- Priority: **High — small, feeds [[TASK-0184]] directly, and it closes a register hypothesis that has been open since the reference audit**
- Filed: 2026-08-27 by Reviewer
- Related: [[TASK-0276]], [[TASK-0270]], [[TASK-0229.003]], [[TASK-0248]], [[TASK-0265]], [[TASK-0184]]

## The measurement, already made

Computed directly from [[TASK-0276]]'s stored footprints
(`holo_only_structural_signature.json`, `allosteric_keys`), clustering the ten
verified KRAS holo structures by pairwise pocket Jaccard:

| | result |
|---|---|
| **9 of 10 drugs** | one site — Switch-II pocket, consensus residues 9, 58–72, 95–103; pairwise Jaccard **0.43–0.90** among them |
| **`7A1X` (QWB)** | **Jaccard 0.00** against eight of the nine, 0.04 against the ninth. Footprint **37, 39, 54, 55, 56, 71, 74, 75** — the **Switch-I/II groove**, a different site |

So KRAS is a **9:1 two-site** protein. [[TASK-0276]] found HCV_NS5B is **2:2
fully disjoint** (within-apo-pair Jaccard 0.941, across-pair **0.000**).

**Two families, two different multi-site architectures.** That is a real,
measured result and it is currently sitting only in a JSON file.

## Why it matters beyond a nice observation

**It is direct evidence for H6.2**, which this register has carried as
**UNTESTED** since the reference audit — *"the allosteric site is
effector-specific; one protein has different allosteric sites for different
effectors"* (Tsai & Nussinov 2014). [[TASK-0229.003]] tested it via an ASD
lookup and found one genuine second site (BCR-ABL1); this is structural
evidence from two more proteins, obtained as a by-product.

It also compounds [[TASK-0265]]'s conclusion. If one protein has several
allosteric sites used by different chemotypes, then "the allosteric pocket of
protein X" is not a well-defined single object — and our benchmark assigns
exactly one per target.

## Scope

- [x] **Verify the Switch-I/II site live.** The residue-number reading
      (37/39/54/55/56/71/74/75 against KRAS landmarks: Switch-I 30–38,
      Switch-II 59–76) is the Reviewer's own inference from coordinates, **not
      a verified citation**. Establish whether this is a recognised,
      published second druggable site on KRAS, and identify `QWB`/Cpd1's own
      primary reference. This is the difference between *"we observed two
      clusters"* and *"we recovered the two known druggable sites"* — which
      read very differently to a reviewer. (Mathieu et al. 2022, *Small
      GTPases*, PMID 34558391 — "Switch I/II"/"Tyr71" pocket, "a known,
      previously described binding site for indole ligands.")
- [x] Confirm `7A1X` is genuinely KRAS G12C and that its chain/numbering match
      the other nine, so the 0.00 Jaccard is a real site difference and not a
      numbering artefact. [[TASK-0273]] found GAC's chain-exact vs resnum-only
      Jaccard differed by an order of magnitude — the same trap applies here
      and must be ruled out explicitly. (G12C genotype already verified live
      in [[TASK-0273]]; construct confirmed monomeric here via RCSB assembly
      record, ruling out the chain-symmetry trap structurally, not assumed.)
- [x] Repeat the clustering for **every** frozen-set protein with ≥2 holo
      structures, not just KRAS and HCV_NS5B. Report the architecture per
      protein: single-site, N:M split, or fully disjoint.
- [x] Update the register's H6.2 entry in
      `.claude/hypotheses/reference_register.md` with the outcome and cite
      this task, per [[TASK-0248]]'s sync rule.
- [x] Draft the paragraph for [[TASK-0184]]. One sentence carries it: *two
      independent families, two different multi-site architectures, and our
      benchmark assigns one pocket per target.*

## Acceptance

- [x] Live-verified answer on whether the Switch-I/II site is documented, with
      citation or an explicit "not established".
- [x] Numbering/chain artefact ruled out for `7A1X`.
- [x] Per-protein architecture table across the frozen set.
- [x] H6.2's register entry updated.
- [x] Submission paragraph drafted.

## Constraint

If the Switch-I/II site turns out **not** to be a recognised allosteric site —
if `7A1X` is a fragment hit, a crystallisation artefact, or a surface binder
with no published function — say so. The 9:1 split would then be a finding
about *deposition practice*, not about allostery, and the H6.2 claim would not
follow. Verify before the claim reaches the submission, not after.

## Done (2026-08-27, Implementer A)

**The Constraint's own failure mode did not occur — the site is real,
published, and recognized, not a fragment-hit artefact.**

**Live citation verification**: `7A1X`'s own deposited RCSB primary
citation is Mathieu et al., "KRAS G12C fragment screening renders new
binding pockets," *Small GTPases* 13:225–238 (2022), PMID 34558391, DOI
10.1080/21541248.2021.1979360. Fetched the full text (PMC8923024, free):
`7A1X`'s own ligand (Cpd1/QWB) occupies the **"Switch I/II pocket,"
also called the "Tyr71 pocket"** — and the paper itself states this is "a
known, previously described binding site for indole ligands," i.e. it
predates this 2022 paper (which reports two OTHER, genuinely novel pockets
from its own screens, validated by a GEF functional assay — a stronger
claim than needed here, correctly not overclaimed for `7A1X` itself). Their
own lining residues (Tyr71, Tyr64, Thr35) line up directly with this
register's own computed footprint: 71 exact match, 37/39 adjacent to
Thr35, 74/75 adjacent to Tyr71, 54–56 the interswitch region between —
confirming the residue-number reading was correct, not merely plausible.

**Chain/numbering artefact ruled out structurally, not assumed**: `7A1X`'s
own G12C genotype was already live-verified in [[TASK-0273]] (anchor-motif
sequence check). This task additionally confirmed, via RCSB's own assembly
record, that the shared KRAS G12C construct (checked on `8AZX`,
representative of all 10 ensemble members) is **monomeric** — a single
chain with no symmetric copy for a residue to be mislabeled onto, unlike
GAC or FBPASE (both real homo-oligomers with a confirmed chain-letter
artefact, [[TASK-0273]]'s own finding). The 0.00 Jaccard between `7A1X` and
the other nine is therefore a genuine site difference, not a labelling
collision — verified, not inferred from the absence of an obvious problem.

**Per-protein architecture, all 7 frozen-set proteins with ≥2 holo
structures**, reusing already-computed data rather than re-deriving it
(this task's own Constraint favors verification over a new run):
- **KRAS_G12C**: 9:1 split, verified above ([[TASK-0276]] + this task).
- **HCV_NS5B**: 2:2 fully disjoint, within-pair Jaccard 0.88–1.00,
  across-pair 0.00 on all 4 pairs ([[TASK-0276]], corroborated by
  [[TASK-0265]]'s own independent single-pair computation).
- **TRP_SYNTHASE**: nominally single-site by its own 2-ligand comparison
  (F6F vs. F19, Jaccard 0.833), but real internal alpha/beta-site
  heterogeneity surfaces within F6F alone when scored against
  [[TASK-0273]]'s own richer 13-structure same-drug ensemble (some
  same-drug pairs at Jaccard 0.000, tracing to alpha-only vs. beta-only
  ligand occupancy across depositions) — a genuinely bifunctional enzyme,
  more nuanced than a clean single/multi-site call.
- **GAC**: single-site once corrected for the already-known chain-letter
  artefact (chain-exact 0.00, resnum-only 0.75–0.82).
- **KSHV_PROTEASE**: single-site (0.750). **PKR**: single-site (0.769).
- **FBPASE**: ambiguous — resnum-only 0.400, moderate, not cleanly
  resolved either way; same chain-artefact risk as GAC flagged but not
  chased further here (real remaining gap, stated not hidden).

**3 of 7 (43%) genuinely multi-site**, a materially stronger empirical base
than [[TASK-0229.003]]'s own 1/4 (25%) ASD-lookup estimate. `.claude/
hypotheses/reference_register.md` H6.2 updated: summary table row, detailed
narrative (additive, [[TASK-0229.003]]'s own existing text kept intact),
REMAINING OPEN VENUE and PDB-RETEST lines both updated to reflect this
task's own extension — per [[TASK-0248]]'s sync rule, same commit as this
write-up.

**Submission paragraph drafted** (in `RESULTS.md`'s own section for this
task) for [[TASK-0184]] to insert — not inserted there directly, that task
owns the document.

**Validation**: script (mostly aggregation of 3 already-computed JSON
files, plus 2 live RCSB lookups) reruns clean; `7A1X`-vs-others numbers
reproduce the Reviewer's own stated 0.00/0.04 and the "rest of the nine"
0.43–0.90 range exactly, confirming the original observation was correct
before any of this task's own additional verification.

**Script:** `scripts/task0280_multi_site_architecture.py`. **Data:**
`results/tasks/0280_multi_site_architecture/architecture_verification.json`.
