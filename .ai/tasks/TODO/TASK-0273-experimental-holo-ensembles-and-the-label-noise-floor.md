# TASK-0273 — Experimental holo ensembles: how reproducible is our pocket label, and what does that ceiling imply?

- Status: TODO
- Assignee: unassigned (suggest Implementer B — structural-validity work, continues TASK-0265/0270)
- Priority: **Highest — it measures a ceiling that bounds every AUC this register has published, and nobody has measured it**
- Filed: 2026-08-26 by Reviewer
- Related: [[TASK-0265]], [[TASK-0270]], [[TASK-0254]], [[TASK-0259]], [[TASK-0243]], [[TASK-0155]]

## The observation that prompted this

[[TASK-0270]]'s audit of [[TASK-0155]]'s candidate pool found **8 of 10
"apo" KRAS structures are actually drug-bound** — and named them with their
ligands: `8AZX` (BI-2865), `7A1X` (QWB), `8QUG` (WYU), `9UOH` (ASP2453),
`7YCE` (IQN), `7MDP` (Z07), `7RP3` (MKZ), `8AFC` (LXK). Add `8S8C` (MK-1084)
and `6OIM` (sotorasib) and that is **ten verified KRAS holo structures with
ten different drugs.**

That is not a defect to clean up. **It is a ready-made experimental
conformational ensemble** — real crystallography, already verified, requiring
no simulation and raising no Constraint-3 question at all.

## The measurement nobody has made: our label's own reproducibility

Every AUC in this register treats the pocket label as exact. It is not. It is
"residues within 4.5 Å of the drug in one crystal structure."

[[TASK-0265]] measured five same-apo-structure ligand *pairs* at Jaccard
median **0.833** (range 0.750–1.000) and concluded ligand identity barely
moves the residue set. But that measurement has no noise floor beneath it:
**we do not know what Jaccard two crystals of the *same* protein with the
*same* drug would give.**

- If same-drug replicates give ~0.99, then 0.833 across different drugs is a
  real chemical effect.
- If same-drug replicates give ~0.85, then 0.833 is **within crystallographic
  noise** and the label carries far less information than we have assumed.

**Either answer bounds every AUC we have published from above**, and we have
never computed it.

## Scope

- [ ] **Build the KRAS holo ensemble** from the ten already-verified
      structures. Re-verify each live (ligand present, chain, resolution,
      residue 12 = Cys) — do not inherit [[TASK-0155]]'s pool unchecked, which
      is precisely how the 8-of-10 error survived.
- [ ] **Find same-drug replicates.** Sotorasib (MOV) and adagrasib in
      particular are likely to have several independent depositions. Search
      RCSB by ligand code, not by paper. This is the noise-floor measurement
      and it is the single most valuable item here.
- [ ] Compute the pairwise Jaccard distribution over the ensemble, split into
      **same-drug** and **different-drug** pairs. Report both distributions,
      not a single number.
- [ ] Define and compute a **consensus pocket** (residues present in ≥K of N
      holo structures) and a **union pocket**. State K before looking.
- [ ] **Re-score KRAS against consensus and union labels** and compare to the
      single-structure label. If AUC rises against consensus, part of what we
      have been calling unexplained is **label noise**, not missing physics.
      That is a different diagnosis from [[TASK-0259]]'s crypticity finding
      and would need saying loudly.
- [ ] Repeat for at least two more proteins with rich holo coverage. Candidates
      from the frozen set with multiple ligands already: **HCV_NS5B** (4 rows,
      2 apo structures), **PKR**, **GAC**, **FBPASE**, **TRP_SYNTHASE**,
      **KSHV_PROTEASE**. Prefer whichever has genuine same-drug replicates.
- [ ] Feed the result back to [[TASK-0265]]'s independence rule: if the label
      is noisy at the 0.85 level, "second ligand = new target" is even weaker
      than that task already concluded.

## Acceptance

- [ ] Verified ensemble manifest per protein: PDB ID, ligand code, resolution,
      chain, method.
- [ ] Same-drug vs different-drug Jaccard distributions, reported separately.
- [ ] Consensus/union labels defined with K stated in advance, and KRAS
      re-scored against all three label definitions.
- [ ] An explicit statement of the implied AUC ceiling, and which published
      numbers sit above or below it.
- [ ] `RESULTS.md`.

## Constraint

If the label turns out to be substantially noisy, **that lowers the ceiling on
our own published results as much as on anyone else's method.** Report it that
way. It also strengthens, independently, the argument in
`documentation/CTQW_CONTRIBUTION_BRIEF.html` §08 that the benchmark rather
than the method is the limiting factor — but do not let that make the finding
more welcome than it should be.
