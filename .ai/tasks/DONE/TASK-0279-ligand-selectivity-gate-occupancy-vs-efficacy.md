# TASK-0279 — The ligand-selectivity gate: does `V_C` measure allosteric *efficacy*, or just occupancy?

- Status: Done
- Assignee: Implementer C
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

- [x] Score `V_C` (and the other non-leaky features from [[TASK-0277]]'s
      grading: `V_B`, `degree`, SASA, geometry) on the myristoyl-pocket
      residues of **`1OPL`** and of **`5MO4`**, ligand physically stripped
      from both — the same per-structure ligand-stripping [[TASK-0276]]
      already implemented, reused, not re-derived.
- [x] **Match the residue set.** Use `allostery.superpose.align_apo_holo` so
      both arms score the identical node set, exactly as [[TASK-0275]] found
      necessary — it changed `DHPS_GC7`'s `V_C` from 0.392 to 0.586 when the
      node sets were not matched. An unmatched comparison here would be
      worthless.
- [x] Note that `1OPL` **also** carries `P16` in the ATP site and `5MO4`
      carries `NIL`. Both arms are therefore doubly occupied, which is
      convenient — the orthosteric site is occupied in both, so that variable
      is controlled too. **State this explicitly rather than treating `1OPL`
      as apo**, which is the error [[TASK-0278]] exists to correct.
- [x] Report the effect size, not only a p-value. With n=2 structures there is
      no meaningful significance test at the structure level — **do not
      manufacture one.** Report per-residue distributions within the pocket
      and say plainly that this is a two-structure comparison.
- [x] **Extend the design where the register can support it.** Any other
      target with an inert-vs-efficacious pair in the same cavity is worth
      more than another BCR-ABL1 replicate. [[TASK-0273]]'s ensembles and
      [[TASK-0276]]'s KRAS ten-structure set are the places to look — KRAS's
      ten drugs are all *efficacious*, so they cannot serve; the search is
      specifically for a **known inert or weakly-active binder** in a pocket
      that also has a real modulator.

## Acceptance

- [x] `V_C` and the other non-leaky features scored on both arms, matched node
      sets, ligands stripped.
- [x] An explicit verdict against the two-outcome table above.
- [x] Effect sizes with the n=2 limitation stated, not disguised.
- [x] A search result for further inert-vs-efficacious pairs, even if empty.
- [x] `RESULTS.md`, and a note to [[TASK-0276]]'s record recording how its
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

## Done (2026-08-26, Implementer C)

**Verdict: the gate does not confirm `V_C` as an efficacy-specific
signature — and the data land in the unfavourable row more decisively than
a simple null.** `V_C` is HIGHER on the myristate (inert) pocket than on
the asciminib (efficacious) pocket in **16 of 16** matched residues (median
57.44 vs 53.63, ~7% relative), the opposite direction the favourable
outcome required. Not the pre-registered "no separation" row exactly — a
significant separation in the *wrong* direction, which is a stronger
negative for the efficacy reading than a null would have been, reported
plainly per this task's own Constraint.

### Method — reusing [[TASK-0276]]'s own instrument, not re-deriving it

New `scripts/task0279_ligand_selectivity_gate.py`. `1OPL` (myristate + P16)
and `5MO4` (asciminib + nilotinib) via `allostery.clean.clean_from_config`;
myristoyl-pocket label and active-site seed via `allostery.labels.
build_labels` (this register's own standard BCR_ABL1 pocket definition:
AY7-contact in `5MO4`, mapped to `1OPL` numbering — stated explicitly, this
pocket definition is asciminib-derived and applied to both arms, not
independently re-derived per structure). **Node-set matching** (this
task's own Scope item 2, [[TASK-0275]]'s own precedent): `allostery.
superpose.align_apo_holo` gives 429 common (chain, resnum) Cα pairs (1OPL
has 451, 5MO4 has 429; RMSD 0.980 Å); all 16/16 myristoyl-pocket residues
and 26/26 active-site residues survive the restriction. Every graph
feature (`V_C`, `degree`, `euclid`, `hop`) computed on coordinates
RESTRICTED to that common set, in matched order, per structure — not each
structure's own full residue set, which is exactly the defect that moved
`DHPS_GC7`'s own `V_C` by 0.19 in [[TASK-0275]]. `V_B` and `SASA` computed
on each structure's own FULL resnums (a deliberately different choice,
stated in the script's own docstring: SASA is a local, all-real-neighbours
quantity that would be unphysical to compute on an artificially-pruned
residue set) and only indexed at the common set afterward. Ligands
physically stripped from both structures via [[TASK-0276]]'s own
`write_ligand_stripped_pdb`/`ligand_stripped_sasa`, reused unchanged, not
re-implemented.

**Both arms doubly occupied, stated explicitly, not treated as apo**
(this task's own Scope item 3): `1OPL` carries `MYR` (myristoyl pocket) +
`P16` (ATP site); `5MO4` carries `AY7` (myristoyl pocket) + `NIL` (ATP
site). The active-site seed used for `euclid`/`hop` is `NIL`-contact,
derived from `5MO4` and applied to both structures' own numbering — `1OPL`'s
own ATP-site occupant is the different molecule `P16`, not independently
re-resolved, both being ATP-competitive BCR-ABL1 inhibitors at the same
kinase pocket, stated as a modelling choice, not an oversight.

### The 6-feature sweep, per-residue paired, n=16 matched pocket residues

| feature | myristate (`1OPL`) median | asciminib (`5MO4`) median | Δ (asciminib − myristate) | frac. favouring asciminib | Wilcoxon p |
|---|---|---|---|---|---|
| **`V_C`** | **+57.44** | **+53.63** | **−3.86** | **0/16** | **<0.0001** |
| `degree` | +9.50 | +9.50 | +0.00 | 1/16 | 0.317 |
| `euclid` | −24.88 | −24.72 | +0.15 | 15/16 | 0.0001 |
| `hop` | −3.00 | −3.00 | +0.00 | 1/16 | 0.317 |
| `V_B` | +57.43 | +25.33 | −33.05 | 0/16 | <0.0001 |
| `SASA` | +15.83 | +15.22 | +1.45 | 12/16 | 0.079 |

**Effect size reported, not just p-values, per this task's own Scope**:
`V_C`'s own gap is a clean, near-total sweep (0/16 residues favour
asciminib) at a real magnitude (~7% median relative shift) — this is the
headline number, not the p-value, which the n=16-correlated-residues
caveat below already discounts. `degree`/`hop` are flat (as expected —
the least dynamics-aware features). `euclid` shows a small (0.6%),
consistent shift toward asciminib — a real but tiny effect, more likely a
minor overall conformational/domain-packing difference than a functional
signal. `SASA` is borderline, not decisive either way.

**A confound this task cannot rule out, disclosed prominently rather than
buried**: `1OPL` (myristate) is a **3.42 Å** structure; `5MO4` (asciminib)
is **2.17 Å** — a large resolution gap. `V_B`'s own huge, maximally clean
gap (57.4 vs 25.3, 0/16) is almost certainly this artifact, not biology —
lower-resolution refinement systematically inflates B-factors, and this
register's own [[TASK-0250]] had already independently flagged `1OPL` as
MARGINAL (r=0.493) on the B-factor-correlation ENM-validity check,
consistent with a lower-quality model. `V_C` is coordinate-derived, not
B-factor-derived, so it is not susceptible to the *same* mechanism, but
coordinate precision at 3.42 Å is itself coarser, and this comparison
cannot distinguish "asciminib genuinely produces lower DCC coupling here"
from "the coarser model produces systematically different coupling
regardless of ligand" — **this is the honest limit of an n=2-structure
gate, not resolved here, and not silently assumed away.**

### With that caveat stated, the plain reading

`V_C` provides **no support** for the efficacy-specific reading of
[[TASK-0276]]'s own positive, and — subject to the resolution caveat —
points the opposite direction from what that reading requires. This does
not prove `V_C` is a pure occupancy/cavity-coupling detector (the
resolution confound keeps that from being a clean proof either), but it
removes the one piece of evidence that could have upgraded [[TASK-0276]]'s
signature from "real holo-side structural pattern" to "a genuine
functional target." [[TASK-0276]]'s own positive should now be read as
**not yet distinguished from occupancy** — exactly the reading this task's
own two-outcome table assigned to its unfavourable row, landed on more
sharply than that row's own wording anticipated.

### Extending the design (Scope item 5) — searched, not found within this task's own budget

KRAS's own ten-drug ensemble ruled out by the task's own filing (all ten
are efficacious). Checked, live, not from memory: HCV_NS5B's own
extensively-characterised thumb/palm allosteric sites (Ma et al./multiple
NNI crystallography series — real SAR campaigns typically deposit
low-potency early hits, so a candidate plausibly exists in the wider PDB)
and glutaminase/GAC's own BPTES-site literature. **No specific inert
occupant of the SAME site as one of this register's own already-curated
ligands (HCV_NS5B's CMF/POO/VR1/VRX, GAC's BPTES/CPD12, PKR's
mitapivat/AG946, TRP_SYNTHASE's F6F/F19, KSHV_PROTEASE's 24Q/25G) was
identified within this task's own bounded search** — establishing that
with confidence would need a structure-by-structure potency check against
each candidate's own deposited SAR data, a real follow-up beyond this
task's own time budget, not attempted further here. Reported empty per
this task's own explicit allowance, not silently skipped.

### Note to [[TASK-0276]]'s own record

Added directly to [[TASK-0276]]'s own DONE file (see that file's own
dated addendum) recording this reading.

### Not done, and why

`documentation/CTQW_CONTRIBUTION_BRIEF.html` **not edited** — checked
directly, its own §04/§08 do not yet carry [[TASK-0276]]'s own V_C
finding as a headline (that propagation has not happened yet, per this
task's own Constraint's own "about to become" phrasing). Nothing to
caveat there today; flagged so whoever adds [[TASK-0276]]'s own finding to
the brief is on notice to add this task's own gate result in the *same*
edit, not a follow-up one. **[[TASK-0278]] landed while this task was in
progress and confirms rather than invalidates the analysis above**: its
own decision is "keep `1OPL`, report the defect explicitly" — no config
change, so this task's own numbers stand unchanged, the live-dependency
risk flagged during this task's own run did not materialise. [[TASK-0278]]'s
own MYR-stripping control (computationally removing myristate from `1OPL`)
found the pocket does NOT close — "the confound is the crystallized
backbone conformation, not the ligand atoms' mere presence" — real,
independent corroboration of this task's own resolution-confound caveat
above: whatever is different about `1OPL`'s own coupling pattern is baked
into its coordinates, not trivially removable by stripping atoms, and this
task's own inability to fully separate "real ligand effect" from
"structure-quality/backbone-conformation effect" is the same open question
[[TASK-0278]] independently ran into from a different angle. No
structure-level significance test was computed or
reported (n=2, this task's own Constraint forbids manufacturing one); the
Wilcoxon p-values above are explicitly residue-level, descriptive/
exploratory statistics on spatially-correlated (non-independent) residues,
not a properly-powered inferential test — stated in the script's own
docstring and repeated here so the number is not later mis-cited as one.

**Script:** `scripts/task0279_ligand_selectivity_gate.py`. **Data:**
`results/tasks/0279_ligand_selectivity_gate/ligand_selectivity_gate.json`.
