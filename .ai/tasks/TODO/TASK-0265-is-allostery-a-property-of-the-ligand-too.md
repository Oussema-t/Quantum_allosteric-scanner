# TASK-0265 — Is a pocket allosteric partly because of *what* binds to it? Label validity, and a rule that needs revising

- Status: TODO
- Assignee: **Implementer B**
- Priority: **High — it is a construct-validity finding for the Phase 1 submission, and it corrects a rule filed the same day**
- Filed: 2026-08-25 by Reviewer
- Related: [[TASK-0261]] (the rule to revise), [[TASK-0229.001]] (H9), [[TASK-0258]], [[TASK-0169]], [[HYP-P13]]

## The question, from Bartosz, 2026-08-25

> Is the BCR-ABL1 pocket with myristoyl bound actually acting allosterically
> *in contrast to* the same pocket with myristic acid in it? Is any pocket an
> allosteric pocket also because of what ligand binds to it, and *how*?

This is the mirror of **H9**. H9 ([[TASK-0229.001]], Gunasekaran/Ma/Nussinov)
attacks the **negative** class: maybe every surface pocket is potentially
allosteric, so decoys are not true negatives. This attacks the **positive**
class: maybe the same pocket is allosteric with one ligand and inert with
another, so our positives are not clean either.

## Measurement already taken (Reviewer, 2026-08-25) — start from this

Five same-apo-structure ligand pairs exist in [[TASK-0243]]'s frozen set.
Pocket-label Jaccard overlap, identical apo coordinates:

| apo | pair | Jaccard |
|---|---|---|
| 2HAI | HCV_NS5B_POO / CMF | **1.000** |
| 2GIQ | HCV_NS5B_VRX / VR1 | 0.882 |
| 1K7X | TRP_SYNTHASE_F6F / F19 | 0.833 |
| 7FS3 | PKR_MITAPIVAT / AG946 | 0.769 |
| 2PBK | KSHV_PROTEASE_24Q / 25G | 0.750 |

Median **0.833**, none below 0.75. Script: `/tmp/pairtest.py` (transient —
**re-implement properly under `scripts/` as part of this task**).

**Two consequences follow, and both need writing up:**

1. **Our label cannot represent ligand-dependent allostery at all.** It is
   drug-contact geometry. Two ligands give near-identical residue sets, so
   "myristoyl works, myristic acid does not" is inexpressible in our data even
   if true. We measure *where a drug binds*, not *where binding produces an
   allosteric effect*. That is a distinct construct-validity finding from
   anything currently in the register.
2. **[[TASK-0261]]'s standing rule is too generous.** It states a second
   ligand on an already-counted apo structure is a new target for *label-side*
   questions. At 75–100% label overlap these are barely independent on the
   label side either. The rule was filed the same day; revise it rather than
   letting it harden.

## Scope

- [ ] Re-implement the pair measurement as a proper script under `scripts/`,
      with the result written to `results/tasks/`.
- [ ] **Verify the BCR-ABL1 mechanism live before writing anything about it.**
      Specifically: does myristate binding alone induce the αI helix bend that
      creates the SH2/SH3 docking site, and does full autoinhibition require
      the covalent tether to the N-cap? The Reviewer's understanding is that
      the tether is what makes it an intramolecular latch, but this is
      explicitly **flagged as unverified** and must not be repeated as fact.
      [[TASK-0236]] already verified asciminib/myristoyl citations — start
      there, do not re-derive.
- [ ] Check what BCR_ABL1's own config actually uses as `drug_ligand` /
      `func_ligand`, and whether our pocket for it corresponds to the
      myristoyl site at all.
- [ ] Revise [[TASK-0261]]'s standing rule with the Jaccard evidence. Propose
      a concrete replacement (e.g. label-side independence requires Jaccard
      below some stated bar) and apply it to the frozen set — say how many
      genuinely independent label-side observations remain.
- [ ] Extend the Jaccard measurement to any same-structure pairs outside the
      frozen set (`candidate_targets_task0216.yaml`, `targets.yaml` —
      CARDIAC_MYOSIN / CARDIAC_MYOSIN_TABLE1 is a probable case).

## Acceptance

- [ ] Reproducible pair-overlap script and results.
- [ ] Live-verified statement on BCR-ABL1, or an explicit "not established".
- [ ] A revised independence rule with the frozen set re-counted under it.
- [ ] `RESULTS.md`, and a §10 addition to
      `documentation/CTQW_CONTRIBUTION_BRIEF.html` — **this task owns the
      brief edit for this batch**, see parallelisation note.

## Constraint

This weakens our own benchmark, not the collaborating thread's method. Report
it that way. It also strengthens the case in the brief's §08 that a better
target set is the highest-value Phase 2 work — a label that cannot express
ligand-dependent allostery is a design problem no method can solve.
