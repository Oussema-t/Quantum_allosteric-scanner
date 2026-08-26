# TASK-0274 — What categories is the residual made of? Two feature families we have never tested

- Status: TODO
- Assignee: unassigned (suggest Implementer A or D — reuses the attribution machinery unchanged)
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

- [ ] **Conservation block.** Build a per-residue conservation score.
      MD-free and Constraint-3-clean by construction. Prefer a route with no
      heavyweight dependency: a Pfam/UniProt MSA via API, or a
      ConSurf-equivalent computed locally. **Verify any citation live** before
      implementing, per standing convention. State the alignment depth per
      target — a shallow MSA gives a meaningless score and that must be
      visible, not hidden.
- [ ] **Chemistry block.** Per-residue physicochemical descriptors: a
      hydrophobicity scale (Kyte–Doolittle or equivalent — name it), charge,
      aromaticity, side-chain volume. Deliberately simple and interpretable;
      the point is to find out whether *anything* chemical helps, not to build
      a good chemistry model.
- [ ] Add both as blocks to [[TASK-0254]]'s Shapley attribution. Reuse the
      n-block exact routine [[TASK-0260]] already generalised — do not rewrite it.
- [ ] Report each block's **contribution when added last**, on top of
      geometry + fpocket + CTQW. That is the decision statistic throughout
      this register.
- [ ] Report **how much of the 27–29% residual each closes**, and how much
      survives both.
- [ ] **Stratify by crypticity**, as every block since [[TASK-0260]] has been.
      The prediction worth pre-registering: conservation should help on
      *functional* sites regardless of openness, unlike fpocket and P2Rank,
      whose gains concentrate on already-open targets (+30.4% vs +8.3%).
      **If conservation shows the same open-target concentration, it is
      tracking cavity presence rather than function.**
- [ ] Cluster-robust significance ([[TASK-0261]]'s exact cluster-level
      permutation, 13 clusters).

## Explicitly out of scope

**Ligand-side features.** A per-residue label cannot be predicted from
properties of the drug, since the drug is constant within a target — modelling
that needs a different experimental design (rank *pockets* per ligand, not
residues). Note it as a named remaining category and leave it; do not
improvise a design here.

## Acceptance

- [ ] Conservation and chemistry blocks implemented, with alignment depth
      reported per target.
- [ ] Five-or-more-block attribution, added-last for every block.
- [ ] An explicit residual number after both, versus the current 27–29%.
- [ ] Crypticity-stratified breakdown, with the pre-registered prediction
      judged.
- [ ] `RESULTS.md`. If the residual drops materially, flag
      `documentation/CTQW_CONTRIBUTION_BRIEF.html` §08 — do not edit it here,
      [[TASK-0272]] currently owns the brief.

## Constraint

If conservation closes a large share of the residual, the honest reading is
that this register spent months on dynamics while omitting a standard,
decades-old classical feature. **Say so plainly.** That is a more useful
finding than another negative, and it is exactly the kind of omission a Phase
2 reviewer would otherwise find for us.
