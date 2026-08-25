# TASK-0268 — Local energetic frustration: the direct test of HYP-P13

- Status: TODO
- Assignee: **Implementer C** (after [[TASK-0264]])
- Priority: Medium-High — cheapest new method available, and it is the only one that tests our *own* hypothesis
- Filed: 2026-08-25 by Reviewer
- Related: [[HYP-P13]], [[TASK-0259]], [[TASK-0229.006]] (EAM/COREX), [[TASK-0233]]

## Why this one, of everything on offer

An external survey listed a hierarchical cryptic-pocket workflow: ANM/GNM
ensembles → rotamer repacking → volumetric scoring. **We have already built
and tested all of it** ([[TASK-0227]], [[TASK-0230]], [[TASK-0229.004]],
[[TASK-0229.007]], [[TASK-0204]], [[TASK-0213]], [[TASK-0235]]). That
convergence is mild validation of our architecture and means most of the
survey offers nothing new.

**Local frustration profiling is the exception, and it is the one item that
tests this project's own hypothesis rather than importing someone else's.**

[[HYP-P13]] states allostery is *stabilisation of an otherwise-disfavoured
conformation*, not a signal propagating to the active site. If that is right,
cryptic and allosteric sites should sit at loci of **high native energetic
frustration** — regions whose local interactions are worse than a randomised
decoy distribution, and which relieve strain on transitioning to the open or
ligand-bound state.

That is a sharp, falsifiable, cheap prediction. It has never been tested, and
unlike every other candidate it does not require a new external tool family
we must first argue past constraint 3.

## Scope

- [ ] **Verify the Frustratometer citation live** before implementing
      (Crossref/publisher record — title, authors, journal, volume, DOI), per
      this register's standing convention. Do not inherit the external
      survey's details; it has now been wrong on three citation specifics
      ([[TASK-0260]] PocketMiner date, [[TASK-0262]] taxonomy,
      CryptoSite's MD-at-inference).
- [ ] Establish whether a runnable local implementation exists or whether it
      is web-server-only — [[TASK-0260]] lost FTMap on exactly that, so check
      installability **before** committing effort.
- [ ] Compute per-residue frustration on the **apo** structures of
      [[TASK-0243]]'s frozen set. Apo only — holo leaks the label.
- [ ] **Pre-register the HYP-P13 prediction before scoring**: frustration
      should be elevated at true pocket residues relative to matched decoys,
      and *more so on the cryptic targets* than the already-open ones.
      Write the prediction down first.
- [ ] Score it as an attribution block alongside geometry / fpocket / CTQW,
      and report its contribution **added last**.
- [ ] Stratify by crypticity, exactly as [[TASK-0260]] did — that is where the
      prediction lives.
- [ ] Cluster-robust significance ([[TASK-0261]]'s method).

## Acceptance

- [ ] Citation verification record and installability finding.
- [ ] Pre-registered prediction, recorded before the first number.
- [ ] Frustration as an attribution block, added-last value, crypticity split.
- [ ] An explicit verdict on the HYP-P13 prediction.
- [ ] `RESULTS.md`; update [[HYP-P13]] in `.claude/hypotheses/physics.md` with
      the outcome either way.

## Constraint

[[HYP-P13]] is this project's own hypothesis and the Reviewer wrote it up.
That makes a favourable result *less* trustworthy, not more. Pre-register the
prediction, and if frustration shows nothing, record that in
`physics.md` with the same prominence the hypothesis currently enjoys.
