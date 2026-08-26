# TASK-0279 — The ligand-selectivity gate: does `V_C` measure allosteric *efficacy*, or just occupancy?

- Status: TODO
- Assignee: unassigned (suggest Implementer A — owns TASK-0276, same machinery)
- Priority: **Highest — it is the one control no imprint argument can explain away, and it decides what TASK-0276's positive result actually means**
- Filed: 2026-08-26 by Reviewer
- Related: [[TASK-0276]], [[TASK-0275]], [[TASK-0278]], [[TASK-0265]], [[TASK-0263]]

## The question

[[TASK-0276]] found a real holo-side signature: `V_C` (GNM dynamic
cross-correlation centrality) significantly separates allosteric from
orthosteric sites in two independent families (KRAS p=0.0117; HCV_NS5B
AUC=1.000 in all four structures). That is a genuine positive and the first
one this register has produced.

**But it does not distinguish "this pocket is occupied" from "this pocket
does something."** [[TASK-0278]] flagged that gap and could not close it.

[[TASK-0278]] also handed us the instrument to close it. BCR-ABL1 gives a
controlled pair that exists nowhere else in the register:

| structure | myristoyl pocket contains | clinical effect |
|---|---|---|
| `1OPL` | **`MYR`** — myristic acid | occupies the pocket; **no therapeutic autoinhibition** |
| `5MO4` | **`AY7`** — asciminib | occupies the same pocket; **is the allosteric drug** |

Same protein. Same cavity. One inert occupant, one efficacious modulator.

**Why this control is uniquely strong: both structures carry a ligand
imprint.** Every objection raised against holo-side results — cavity shape,
induced rotamers, local compression, "you are detecting the footprint" —
applies *equally to both arms* and therefore cannot explain a difference
between them. This is the only comparison available to us where the imprint
confound cancels.

## The two outcomes, both decisive

| result | reading |
|---|---|
| `V_C`(asciminib pocket) **>** `V_C`(myristate pocket), significantly | `V_C` measures allosteric **efficacy**, not occupancy. [[TASK-0276]]'s positive becomes a genuine functional signature, and Phase 2 has a real physical target. |
| No separation | `V_C` is a **hole-finder** — it detects that a cavity is occupied and coupled, not that the occupant does anything. [[TASK-0276]]'s result must be re-read as occupancy detection, and the register's one positive is substantially weakened. |

**Neither outcome is a null.** Say which one landed, plainly.

## Scope

- [ ] Score `V_C` (and the other non-leaky features from [[TASK-0277]]'s
      grading: `V_B`, `degree`, SASA, geometry) on the myristoyl-pocket
      residues of **`1OPL`** and of **`5MO4`**, ligand physically stripped
      from both — the same per-structure ligand-stripping [[TASK-0276]]
      already implemented, reused, not re-derived.
- [ ] **Match the residue set.** Use `allostery.superpose.align_apo_holo` so
      both arms score the identical node set, exactly as [[TASK-0275]] found
      necessary — it changed `DHPS_GC7`'s `V_C` from 0.392 to 0.586 when the
      node sets were not matched. An unmatched comparison here would be
      worthless.
- [ ] Note that `1OPL` **also** carries `P16` in the ATP site and `5MO4`
      carries `NIL`. Both arms are therefore doubly occupied, which is
      convenient — the orthosteric site is occupied in both, so that variable
      is controlled too. **State this explicitly rather than treating `1OPL`
      as apo**, which is the error [[TASK-0278]] exists to correct.
- [ ] Report the effect size, not only a p-value. With n=2 structures there is
      no meaningful significance test at the structure level — **do not
      manufacture one.** Report per-residue distributions within the pocket
      and say plainly that this is a two-structure comparison.
- [ ] **Extend the design where the register can support it.** Any other
      target with an inert-vs-efficacious pair in the same cavity is worth
      more than another BCR-ABL1 replicate. [[TASK-0273]]'s ensembles and
      [[TASK-0276]]'s KRAS ten-structure set are the places to look — KRAS's
      ten drugs are all *efficacious*, so they cannot serve; the search is
      specifically for a **known inert or weakly-active binder** in a pocket
      that also has a real modulator.

## Acceptance

- [ ] `V_C` and the other non-leaky features scored on both arms, matched node
      sets, ligands stripped.
- [ ] An explicit verdict against the two-outcome table above.
- [ ] Effect sizes with the n=2 limitation stated, not disguised.
- [ ] A search result for further inert-vs-efficacious pairs, even if empty.
- [ ] `RESULTS.md`, and a note to [[TASK-0276]]'s record recording how its
      positive should now be read.

## Constraint

[[TASK-0276]]'s positive is currently the best result in this register, and it
is one this reviewer has been promoting. **That makes a favourable outcome
here less trustworthy, not more.** Pre-register nothing beyond the two-outcome
table, and if `V_C` fails to separate myristate from asciminib, report it with
the same prominence [[TASK-0276]]'s positive received — including in
`documentation/CTQW_CONTRIBUTION_BRIEF.html`, where the `V_C` line is about to
become a headline.

**Do not optimise anything on these two structures.** They are a gate, not a
training set. A discriminator tuned to separate this pair would detect the
specific chemistry of asciminib and transfer nowhere.
