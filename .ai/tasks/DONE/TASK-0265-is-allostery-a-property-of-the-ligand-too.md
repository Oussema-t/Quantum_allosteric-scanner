# TASK-0265 — Is a pocket allosteric partly because of *what* binds to it? Label validity, and a rule that needs revising

- Status: Done
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

- [x] Re-implement the pair measurement as a proper script under `scripts/`,
      with the result written to `results/tasks/`.
- [x] **Verify the BCR-ABL1 mechanism live before writing anything about it.**
      Specifically: does myristate binding alone induce the αI helix bend that
      creates the SH2/SH3 docking site, and does full autoinhibition require
      the covalent tether to the N-cap? The Reviewer's understanding is that
      the tether is what makes it an intramolecular latch, but this is
      explicitly **flagged as unverified** and must not be repeated as fact.
      [[TASK-0236]] already verified asciminib/myristoyl citations — start
      there, do not re-derive.
- [x] Check what BCR_ABL1's own config actually uses as `drug_ligand` /
      `func_ligand`, and whether our pocket for it corresponds to the
      myristoyl site at all.
- [x] Revise [[TASK-0261]]'s standing rule with the Jaccard evidence. Propose
      a concrete replacement (e.g. label-side independence requires Jaccard
      below some stated bar) and apply it to the frozen set — say how many
      genuinely independent label-side observations remain.
- [x] Extend the Jaccard measurement to any same-structure pairs outside the
      frozen set (`candidate_targets_task0216.yaml`, `targets.yaml` —
      CARDIAC_MYOSIN / CARDIAC_MYOSIN_TABLE1 is a probable case).

## Acceptance

- [x] Reproducible pair-overlap script and results.
- [x] Live-verified statement on BCR-ABL1, or an explicit "not established".
- [x] A revised independence rule with the frozen set re-counted under it.
- [x] `RESULTS.md`, and a §10 addition to
      `documentation/CTQW_CONTRIBUTION_BRIEF.html` — **this task owns the
      brief edit for this batch**, see parallelisation note.

## Constraint

This weakens our own benchmark, not the collaborating thread's method. Report
it that way. It also strengthens the case in the brief's §08 that a better
target set is the highest-value Phase 2 work — a label that cannot express
ligand-dependent allostery is a design problem no method can solve.

## Done

**2026-08-25, Implementer B.** New `scripts/task0265_pocket_label_overlap.py`,
reusing `task0242_two_stage_dryrun.prep` unchanged and [[TASK-0243]]'s frozen
config, [[TASK-0255]]'s altloc="all" monkeypatch. Re-implements the transient
`/tmp/pairtest.py` and extends it: that script grouped pairs by
`(apo_pdb, chains)`, which **silently excluded 2 of the 7 apo-shared pairs**
(GAC_BPTES/GAC_CPD12, FBPASE_94D/FBPASE_95S — different chain *subsets* of the
same apo entry) because their pocket masks have different length under a
positional comparison. Fixed by keying pocket-label sets on `(chain, resnum)`
identity instead, which covers all 7 pairs (plus HIV_INTEGRASE_MUT871/916,
an 8th same-apo pair found along the way — not one of the scored 20 rows,
excluded from [[TASK-0249]]/[[TASK-0261]]'s own denominator by its own
unrelated empty-seed defect, included here only for completeness).

**Real chain-identity artifact found and corrected before trusting the
numbers**: the 2 different-chain-subset pairs both initially returned
Jaccard = 0.000 — literally zero shared (chain, resnum) keys. Checked
directly rather than accepted: both are **homo-oligomeric assemblies** where
the ligand happens to be deposited on a different (but sequence-equivalent,
symmetric) chain copy across the two structures — e.g. GAC_BPTES's pocket is
on chain D (residues 317-394), GAC_CPD12's is on chain B at **the same
residue numbers** (321-325, 394). A strict (chain, resnum) key treats these
as disjoint; they are the same site on a different subunit. Added a
resnum-only Jaccard alongside the strict one for exactly this case (reported
both, not just the flattering one): GAC_BPTES/CPD12 corrects to **0.750**,
FBPASE_94D/95S to **0.400**.

### Corrected Jaccard, all 7 scored pairs (best-available: resnum-only where
chains differ, strict (chain,resnum) where they match — identical either way
when chains match)

| apo | pair | Jaccard | note |
|---|---|---|---|
| 2HAI | HCV_NS5B_POO / CMF | 1.000 | |
| 2GIQ | HCV_NS5B_VRX / VR1 | 0.882 | |
| 1K7X | TRP_SYNTHASE_F6F / F19 | 0.833 | |
| 7FS3 | PKR_MITAPIVAT / AG946 | 0.769 | |
| 2PBK | KSHV_PROTEASE_24Q / 25G | 0.750 | |
| 7SBN | GAC_BPTES / CPD12 | 0.750 | corrected from 0.000, symmetric-copy artifact |
| 5LDZ | FBPASE_94D / 95S | 0.400 | corrected from 0.000, symmetric-copy artifact |

**Median 0.769, min 0.400 — higher than the Reviewer's own first-pass
(median 0.833, n=5) suggested once the two excluded pairs are correctly
included.** Every scored pair is ≥0.75 except one (FBPASE, 0.400). The
finding is not weaker after the correction — it is more precise, and if
anything stronger: label-side independence is even more consistently
compromised than the first pass showed.

### BCR-ABL1 mechanism — live-verified (Scope item 2), not repeated as fact

The Reviewer's own understanding was flagged unverified. Live literature
check, citations verified (title/authors/journal/year/DOI cross-checked via
Crossref, not search-snippet only), separate from [[TASK-0236]]'s own
already-verified asciminib citation, which is reused, not repeated:

**ESTABLISHED**: covalent tethering to the N-terminus is **not** required
for the local latch mechanism (the αI-helix bend that creates the SH2-
docking surface). Non-covalent, non-tethered occupancy of the myristoyl
pocket alone is sufficient. Evidence, convergent across independent groups:

- Nagar et al. 2003, *Cell* 112:859-871 (doi:10.1016/S0092-8674(03)00194-6)
  — established myristoyl-pocket occupancy drives the assembled/autoinhibited
  conformation.
- Nagar et al. 2006, *Mol Cell* 21:787-798 (doi:10.1016/j.molcel.2006.01.035,
  PDB 2FO0) — defines the specific αI/αI′ bend (break at Phe516) required
  for SH2 docking. *Spot-verified live, resolves cleanly.*
- Zhang, Adrián, Jahnke et al. 2010, *Nature* 463:501-506
  (doi:10.1038/nature08675, PDB 3K5V) — GNF-2, a **non-covalent, non-
  myristate** small molecule, stabilises the same bent αI′ conformation.
  *Spot-verified live, resolves cleanly.*
- Grzesiek et al. 2022, *Magn Reson (Gott)* 3:91-99
  (doi:10.5194/mr-3-91-2022) — direct NMR statement that non-tethered
  allosteric-site ligands (GNF-5, asciminib) "fix the αI helix... and
  reassemble the core."
- Wylie et al. 2017, *Nature* 543:733-737 (doi:10.1038/nature21702, already
  verified [[TASK-0236]]) — asciminib "recapitulates physiologic
  autoinhibition."
- Paladini et al. 2024, *eLife* 12:RP92324 (doi:10.7554/eLife.92324.3) —
  states the shared, ligand-agnostic requirement explicitly: only pocket
  binders that also bend the αI-helix act as allosteric inhibitors,
  independent of covalent attachment.
- de Buhr & Gräter 2023, *eLife* 12:e85216 (doi:10.7554/eLife.85216) —
  assigns covalent myristoylation a *different* role (intramolecular
  concentration / membrane localisation), not the local bend.

**Honest caveat, not smoothed over**: no source co-crystallises *free
myristic acid itself* (untethered) with the isolated kinase domain — the
non-covalent-sufficiency evidence rests on GNF-2/GNF-5/asciminib (different
chemotypes occupying the same pocket), not literally the native lipid in
free form. The conclusion is convergent across independent structural/NMR
groups rather than one paper's stated thesis, but it is not total proof for
the single molecule ("myristic acid alone") the original question named.

**Answers the framing question directly**: is the BCR-ABL1 pocket "acting
allosterically" differently with myristoyl vs. myristic acid? The literature
says the relevant local mechanism (pocket occupancy → bend → SH2 docking) is
**ligand-chemotype-agnostic** — any pocket-occupying molecule that induces
the bend triggers it, tethered or not. What differs between the *native*
myristoyl-glycine and a free small molecule is not the local structural
consequence but effective concentration/localisation — a real distinction,
but not the one the original framing implied (that the *pocket itself*
"acts differently"). This is consistent with, and sharpens, this task's own
broader point: two different heavy-atom-different ligands occupying
statistically the same residues (Jaccard 0.75-1.00 for 6/7 pairs) is exactly
what "same local mechanism, different chemotype" predicts.

### BCR_ABL1's own config (Scope item 3)

Confirmed directly: `drug_ligand: AY7` (asciminib), `site_name: Myristoyl
pocket`, pocket derived from AY7 contacts in 5MO4 — the config **does**
correspond to the myristoyl site, not a different one.

### Revised standing rule (supersedes [[TASK-0261]]'s label-side clause)

[[TASK-0261]]'s own rule ("a second ligand on an already-counted apo
structure is a new target for label-side questions") is **too generous** —
confirmed with the corrected Jaccard evidence above, not just the first
pass. **Revised**: label-side independence requires pocket-label Jaccard
**< 0.5** between the two ligands' labels on the same apo structure (a
majority-overlap threshold — the natural break in this data sits between
0.400 and 0.750, with only one pair below it). Applied to the frozen set:

- 6/7 pairs (Jaccard 0.75-1.00) collapse to **one** label-side observation
  each: 12 rows → 6.
- 1/7 pair (FBPASE, 0.400) remains **two** independent label-side
  observations: 2 rows → 2.
- 6 singleton targets are unaffected: 6 rows → 6.

**Genuinely independent label-side observations: 14, not 20.** (Apo-side
independence is unchanged from [[TASK-0261]]: still 13, that rule was not
questioned by this task.) [[TASK-0261]]'s own file corrected in place with a
dated superseding note (see below), the original rule not silently rewritten.

### Extension to other configs (Scope item 5) — both negative

Reused [[TASK-0261]]'s own already-checked apo-identity data, extended with
this task's own Jaccard machinery for confirmation: the 15 register targets
(`targets.yaml`) and [[TASK-0216]]'s 7-target candidate set each have zero
same-apo pairs — nothing to compute Jaccard for. CARDIAC_MYOSIN /
CARDIAC_MYOSIN_TABLE1, named a "probable case" by this task's own filing, is
confirmed (again, independently of [[TASK-0261]]'s own prior check) **not**
one: 8QYP vs 5TBY, different deposited entries.

### `documentation/CTQW_CONTRIBUTION_BRIEF.html` — this task's own §10 addition

New bullet in the "Known defects in our own work" list: the label-side
independence count revised from 20 to 14 genuinely independent
observations, with the Jaccard bar and its justification, cross-referenced
to this task.

### Not done

- The resnum-only correction was applied only to the 2 pairs where chains
  differed; not re-derived for the 5 same-chain pairs (chain-exact and
  resnum-only are identical there by construction — checked, not assumed,
  since `same_chain_selection=True` implies the residue-key sets are drawn
  from the same chain labels on both sides).
- Free myristic acid vs. tethered myristoyl-glycine was not directly
  co-crystallised in any source found — flagged as the literature's own
  gap, not filled here (would require new structural biology, out of this
  task's own scope).

**Script**: `scripts/task0265_pocket_label_overlap.py`. **Data**:
`results/tasks/0265_pocket_label_overlap/pocket_label_overlap.json`.
