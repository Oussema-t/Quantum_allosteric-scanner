# TASK-0274 — What categories is the residual made of? Two feature families we have never tested

- Status: Done
- Assignee: Implementer D
- Priority: **High — cheap, and it tests the two most obvious omissions in our entire feature set**
- Filed: 2026-08-26 by Reviewer
- Related: [[TASK-0254]], [[TASK-0259]], [[TASK-0260]], [[TASK-0263]], [[TASK-0266]], [[TASK-0269]], [[TASK-0273]]

## The gap, stated plainly

Every attribution block this register has ever tested is **geometric or
dynamical**:

`geometry` (degree, euclid, hop) · `fpocket` · `ctqw` · `sasa` ([[TASK-0266]])
· `p2rank` ([[TASK-0260]]) · `potential terms` ([[TASK-0263]]) · `pocketminer`
([[TASK-0269]])

Checked directly: `task0254_fpocket_variance_and_crypticity.py` declares
`BLOCKS = ["geometry", "fpocket", "ctqw"]`, and a grep across
`src/allostery/` finds **no sequence conservation feature of any kind** and no
explicit residue chemistry — `corex.py` has a thermodynamic hydrophobic-burial
term, `frustration.py` mentions hydrophobic packing, and that is the extent of it.

**We have never tested evolutionary conservation, and we have never tested
residue chemistry.** Conservation is among the oldest and strongest predictors
of functional sites in structural biology — it is a headline feature of
CryptoSite, which we excluded on Constraint-3 grounds without ever testing the
*feature family* it rests on.

The residual currently sits at **27–29%** ([[TASK-0254]], [[TASK-0260]]) and
has survived: a second geometric detector (P2Rank, added-last +0.0%), a
purpose-built cryptic predictor (PocketMiner, does not close it), a better
burial measure (SASA), and `H_new`'s own potential terms. It correlates with
crypticity at rho −0.771 and with nothing else measured.

**Before concluding the residual is irreducible or exotic, test the two
ordinary things we left out.**

## Candidate categories for the residual

| category | status |
|---|---|
| Crypticity / conformational change | measured, rho=−0.771; PocketMiner did **not** close it |
| **Label noise** | **never measured** — [[TASK-0273]] measures it |
| **Evolutionary conservation** | **never tested** — this task |
| **Residue chemistry** | **never tested** — this task |
| Ligand-side properties (size, shape, chemistry of the drug) | never tested; scoped out here, see below |
| Irreducible | whatever survives all of the above |

## Scope

- [x] **Conservation block.** Build a per-residue conservation score.
      MD-free and Constraint-3-clean by construction. Prefer a route with no
      heavyweight dependency: a Pfam/UniProt MSA via API, or a
      ConSurf-equivalent computed locally. **Verify any citation live** before
      implementing, per standing convention. State the alignment depth per
      target — a shallow MSA gives a meaningless score and that must be
      visible, not hidden.
- [x] **Chemistry block.** Per-residue physicochemical descriptors: a
      hydrophobicity scale (Kyte–Doolittle or equivalent — name it), charge,
      aromaticity, side-chain volume. Deliberately simple and interpretable;
      the point is to find out whether *anything* chemical helps, not to build
      a good chemistry model.
- [x] Add both as blocks to [[TASK-0254]]'s Shapley attribution. Reuse the
      n-block exact routine [[TASK-0260]] already generalised — do not rewrite it.
- [x] Report each block's **contribution when added last**, on top of
      geometry + fpocket + CTQW. That is the decision statistic throughout
      this register.
- [x] Report **how much of the 27–29% residual each closes**, and how much
      survives both.
- [x] **Stratify by crypticity**, as every block since [[TASK-0260]] has been.
      The prediction worth pre-registering: conservation should help on
      *functional* sites regardless of openness, unlike fpocket and P2Rank,
      whose gains concentrate on already-open targets (+30.4% vs +8.3%).
      **If conservation shows the same open-target concentration, it is
      tracking cavity presence rather than function.**
- [x] Cluster-robust significance ([[TASK-0261]]'s exact cluster-level
      permutation, 13 clusters).

## Explicitly out of scope

**Ligand-side features.** A per-residue label cannot be predicted from
properties of the drug, since the drug is constant within a target — modelling
that needs a different experimental design (rank *pockets* per ligand, not
residues). Note it as a named remaining category and leave it; do not
improvise a design here.

## Acceptance

- [x] Conservation and chemistry blocks implemented, with alignment depth
      reported per target.
- [x] Five-or-more-block attribution, added-last for every block.
- [x] An explicit residual number after both, versus the current 27–29%.
- [x] Crypticity-stratified breakdown, with the pre-registered prediction
      judged.
- [x] `RESULTS.md`. If the residual drops materially, flag
      `documentation/CTQW_CONTRIBUTION_BRIEF.html` §08 — do not edit it here,
      [[TASK-0272]] currently owns the brief.

## Constraint

If conservation closes a large share of the residual, the honest reading is
that this register spent months on dynamics while omitting a standard,
decades-old classical feature. **Say so plainly.** That is a more useful
finding than another negative, and it is exactly the kind of omission a Phase
2 reviewer would otherwise find for us.

## Done (2026-08-26, Implementer D)

**Both blocks built real, not placeholders.** Conservation: UniProt-offset
mapping reused verbatim from `backend.active_site` (`get_uniprot`/
`_residues_by_num`/`_uniprot_features`/`_find_offset`) → InterPro Pfam
domain match → Pfam **seed** alignment (curated, via InterPro's alignment
API) parsed with `Bio.AlignIO` (no MSA binary installed in this
environment — checked directly: no clustalo/mafft/muscle/hmmalign) →
per-column Shannon-entropy conservation → transferred onto the query
residues via a pairwise-alignment nearest-homolog anchor (BLOSUM62,
`Bio.Align.PairwiseAligner`). Citation verified live via Crossref: Mistry
et al. 2021, *Nucleic Acids Research*, DOI 10.1093/nar/gkaa913. Chemistry:
Kyte-Doolittle hydropathy (DOI 10.1016/0022-2836(82)90515-0, verified
live), charge (D/E=-1, K/R=+1, H=0), aromaticity (F/W/Y), Zamyatnin 1972
side-chain volume (DOI 10.1016/0079-6107(72)90005-3, verified live).

**Alignment depth, reported per target, not hidden**: 20/20 frozen-set
targets got a real Pfam seed mapping (`conservation_depth.json`). n_seed
sequences median 32 (range 5-245). Best-homolog identity to the query's own
domain fragment: median 97%, but 4 targets (PF_ATCASE 48%, KSHV protease
53%, MKK7 44%, SMYD3 45%) sit at genuinely shallow homology — flagged, not
smoothed into the summary. Multi-chain targets: conservation is chain[0]-
scoped only (the same limitation `detect_active_site` itself already has,
not a new one introduced here) — other chains get NaN, imputed like every
other NaN block value in this register; true per-target coverage
(`n_mapped/n_total`) is in the printed table and `conservation_depth.json`.

**Headline (this task's own decision statistic — each new block added on
top of the geometry+fpocket+CTQW baseline specifically, reusing the exact
same CV-AUC calls the 5-block Shapley cache already computed, no second CV
run)**: conservation median **-0.08%**, chemistry median **-0.35%**. Both
slightly negative. Cluster-robust ([[TASK-0261]]'s exact permutation, 13
clusters): conservation **p=0.6946**, chemistry **p=0.6492** — neither
distinguishable from zero. Full 5-block added-last (on top of everything
else, including each other): conservation median -0.05% (p=0.8423),
chemistry median -0.27% (p=0.8318) — consistent with the 3-block-baseline
statistic, not a different story depending on which model the marginal is
taken against.

**Residual**: 3-block (geom/fpocket/ctqw) median unexplained 28.6% →
5-block (+conservation+chemistry) median unexplained **30.7%** — not lower,
marginally *higher*, consistent with two uninformative dimensions adding
noise to a 20-row 5-fold CV rather than any real signal being captured.

**Crypticity-stratified, the pre-registered prediction judged**:
conservation's own cryptic-vs-open split (3-block-baseline-plus-
conservation statistic) is cryptic median -0.66% vs open median -0.07%,
cluster-perm p=0.572 — **not significant, and not even in the predicted
direction**. There is no conservation signal to be "tracking cavity
presence instead of function" — it carries no signal in either regime.
Straddling cluster (TRP_SYNTHASE_F6F/F19, same apo structure, opposite
sides of the 80% crypticity bar) excluded from this stratification only,
per [[TASK-0266]]'s own established handling.

**Answered per this task's own Constraint, plainly**: conservation does
**not** close any material share of the residual, and neither does
chemistry. Two ordinary, decades-old feature families, implemented for
real and tested with the same cluster-robust rigor as every other block in
this register, both come back statistically indistinguishable from noise.
This closes two of the three concretely-named remaining candidate
categories from this task's own filing table ([[TASK-0273]] covers the
third, label noise). What remains: "ligand-side properties" (explicitly
out of scope here — needs a per-pocket, not per-residue, design) and
"irreducible."

**One per-target outlier noted, not chased further**: DHPS_GC7 shows a real
conservation Shapley share of +32.7% — the only target where conservation
does anything measurable. A single point, not a pattern; real remaining
scope if anyone wants to look at why (its Pfam family, PF01916, has 191
seed sequences at 99.7% best-homolog identity — not a shallow-alignment
artifact).

`documentation/CTQW_CONTRIBUTION_BRIEF.html` §08 **not flagged/edited** —
this task's own Acceptance only requires it if the residual drops
materially; it moved the wrong way (28.6% → 30.7%).

**Script:** `scripts/task0274_conservation_chemistry_residual.py`.
**Data:** `results/tasks/0274_conservation_chemistry_residual/`
(`shapley_5block.json`, `crypticity.json`, `conservation_depth.json`,
`cluster_robust_results.json`, `pfam_seed_cache/`). **Full RESULTS.md
row** filed the same commit.
