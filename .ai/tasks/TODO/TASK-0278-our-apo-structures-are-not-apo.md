# TASK-0278 — Three of six "apo" structures are ligand-bound, and BCR-ABL1's ligand sits *in the pocket we are predicting*

- Status: TODO
- Assignee: unassigned (suggest Implementer B — continues the TASK-0270/0273 structural-validity line)
- Priority: **Highest — this is a benchmark-integrity defect on a mandatory target, and it invalidates the premise of BCR-ABL1's apo→holo contrast**
- Filed: 2026-08-26 by Reviewer
- Related: [[TASK-0270]], [[TASK-0169]], [[TASK-0120]], [[TASK-0139]], [[TASK-0209]], [[TASK-0265]], [[TASK-0276]]

## The finding

Bartosz asked whether BCR-ABL1's myristoyl pocket is "pre-formed, partially
opened by myristic acid" in our apo. **Checked live against RCSB — yes, and
worse than the question assumed:**

| structure | role | non-polymer entities |
|---|---|---|
| `1OPL` | our **apo** | **`MYR` (myristic acid)** + **`P16`** (an ATP-site inhibitor) |
| `5MO4` | our holo | `NIL` (nilotinib) + `AY7` (asciminib) |

**Our BCR-ABL1 "apo" is doubly ligand-bound, and one of those ligands —
myristic acid — occupies the very pocket the pipeline is asked to find.**

The contrast we have been calling apo→holo is not empty→bound. It is
**ligand-swap → ligand-swap**: myristic acid + ATP-site inhibitor, replaced by
asciminib + nilotinib.

### Audit of every other mandatory/register apo, same method

| apo | target | contents | verdict |
|---|---|---|---|
| `4LDJ` | KRAS_G12C | GDP + Mg | **fine** — cognate substrate, physiological resting state |
| `1SUG` | PTP1B | Tris, glycerol | **fine** — buffer / cryoprotectant |
| `1F1J` | CASPASE7 | sulfate | **fine** |
| **`1OPL`** | BCR_ABL1 | **MYR + P16** | **broken** — ligand in the target pocket |
| **`1V4S`** | GLUCOKINASE | glucose + **`MRK`** | **broken** — `MRK` is a synthetic drug-like compound |
| **`8QYP`** | CARDIAC_MYOSIN | ADP + **vanadate** + Mg | **suspect** — ADP-vanadate is a transition-state analogue, a chemically trapped state, not a resting apo |

**The distinction that matters, and it must be applied consistently**: a
cognate substrate (GDP in a GTPase, glucose in glucokinase) or a
buffer/cryoprotectant is a legitimate apo. **A synthetic drug-like molecule
occupying the target pocket is not.**

## Why this explains several existing results

- [[TASK-0120]]/[[TASK-0139]] found BCR-ABL1's pocket "measurably pre-formed
  in apo" (RMSD ratio 0.49). **It is pre-formed because myristic acid is
  holding it open.** That was reported as a property of the protein; it is a
  property of the crystal's contents.
- [[TASK-0169]] failed BCR-ABL1 on "cryptic". Now mechanically explained.
- fpocket's 0.8596 on BCR-ABL1 — one of the numbers used throughout to argue
  geometry beats our observables — is scored against a pocket that is **open
  and occupied** in the input structure.
- [[TASK-0270]] declined the BCR-ABL1 apo substitution after checking
  candidates (`2G1T`, `2G2H`, `2G2I`) and finding none genuinely ligand-free.
  **It does not appear to have checked the incumbent by the same standard.**
  That is the irony to record: substitutes were rejected for a defect the
  sitting structure has worse.

## The conceptual point, which is the more important half

Myristic acid occupies the myristoyl pocket. It does **not** produce the
therapeutic allosteric effect — asciminib does. Same pocket, different
occupant, different outcome.

That is direct, single-target, structurally-verified evidence for
[[TASK-0265]]'s conclusion: **allostery is a property of the protein–ligand
complex, not of the cavity.** [[TASK-0265]] reached it statistically (label
Jaccard 0.833 across ligand pairs); this reaches it mechanistically, on the
canonical allosteric-inhibitor example in the field.

It also sharpens [[TASK-0276]]'s Row-2 result. That task found a real
holo-side signature separating allosteric from orthosteric sites. **If
occupancy alone were sufficient, `1OPL`'s myristic-acid-bound pocket would
already be "allosteric" — and clinically it is not.** Whatever the signature
is measuring, it must be able to distinguish occupancy from effect, and that
has not been tested.

## Scope

- [ ] Extend the audit to **every** apo structure in `config/targets.yaml` and
      `config/candidate_targets_task0243.yaml` — the frozen 22 have never been
      checked this way either. Report contents per structure with the
      cognate/buffer/synthetic classification applied.
- [ ] **Write the classification rule down** as a reusable convention, and add
      it to [[TASK-0209]]'s VALID rule so no future curation repeats this.
      `nonpolymer_bound_components` is not sufficient — it silently missed
      non-coordinating inhibitors in [[TASK-0270]]'s audit; enumerate
      non-polymer entities directly.
- [ ] For BCR-ABL1: decide what to do. Options, all needing the organiser
      permission already on record (`2026-08-26-organiser-clarifications.md`,
      item 4 — substitution permitted with documented rationale):
      (a) find a genuinely myristoyl-pocket-empty ABL1 structure;
      (b) keep `1OPL` and **report the defect explicitly** as a benchmark
      finding, which is defensible and may be the honest choice if no clean
      apo exists;
      (c) strip `MYR` computationally and state that the cavity is
      ligand-shaped regardless.
      **Do not pick (c) silently** — a stripped structure is not an apo
      structure.
- [ ] Re-run BCR-ABL1's headline numbers under whichever option is chosen,
      old vs new side by side, as [[TASK-0270]] did for KRAS.
- [ ] Quantify how much of BCR-ABL1's fpocket 0.8596 survives if the pocket is
      not pre-opened by a bound ligand.

## Acceptance

- [ ] Full apo-contents audit across both configs with the classification
      applied.
- [ ] The classification rule written into [[TASK-0209]]'s VALID criteria.
- [ ] A decision on BCR-ABL1 with a submission-ready rationale.
- [ ] Side-by-side re-run of affected numbers.
- [ ] `RESULTS.md`; and flag `documentation/PHASE1_SUBMISSION_DRAFT.md`, which
      currently discusses BCR-ABL1's pre-formed pocket without this cause.

## Constraint

This is a defect in **our own** benchmark construction, found by us, on a
mandatory target. Report it with the prominence [[TASK-0169]] and
[[TASK-0270]] received. It makes several of our own prior findings *less*
mysterious rather than more impressive — BCR-ABL1's "pre-formed pocket" was
never a discovery about protein dynamics — and that correction is owed.
