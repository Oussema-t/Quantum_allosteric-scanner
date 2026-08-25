# TASK-0251 — H5: MWC / conformational selection, and whether the challenge's own scope truncates the mechanism

- Status: Done
- Assignee: unassigned (suggest Explorer → Implementer)
- Priority: **High — H5.2 may invalidate a mandatory target by construction**
- Filed: 2026-08-24 by Reviewer
- Parent: [[TASK-0248]] (confirmed genuinely open by direct search)
- Reference: Changeux J-P, Edelstein SJ, *Science* 2005, "Allosteric Mechanisms of Signal Transduction", [10.1126/science.1108595](https://doi.org/10.1126/science.1108595)
- Related: [[TASK-0169]] (benchmark discriminability), [[TASK-0222]] (both Cardiac Myosin pairs), [[TASK-0236]] (mavacamten/SRX citation check)

## Hypotheses

- **H5.1** — Pre-existing equilibrium between states; **ligand selects rather
  than induces**. Directly contradicts the induced-fit/propagation framing our
  CTQW pipeline is built on, and is the same family as [[HYP-P13]] (allostery
  as stabilisation) which this register arrived at independently from data.
- **H5.2** — Allosteric transitions are **concerted across subunits** in
  oligomers.

## Why H5.2 is the urgent half

The challenge's own Scope note says *"Included: the catalytic domains"*. If a
target's real mechanism is **inter-subunit or inter-domain**, then scoping the
model to a single catalytic domain **removes the coupling from the model by
construction** — before any observable is computed. The target would then be
unscoreable in principle, not merely difficult, and a negative result on it
would carry no information about the method.

**CARDIAC_MYOSIN is the flagged candidate** (mavacamten / SRX / interacting-heads
biology). Flagged, not confirmed — confirming or refuting it is this task's job.
Note the target already has two known problems ([[TASK-0222]]: mandated pair
unscoreable; [[TASK-0169]]: 6C1H does not contain mavacamten). A third,
mechanistic one would settle whether it belongs in the benchmark at all.

## Scope

- [x] Verify the Changeux & Edelstein citation directly before working against
      it (the family convention — [[TASK-0137]], and every TASK-0229 subtask).
- [x] For each benchmark target, establish from primary literature whether the
      published mechanism is intra-domain, inter-domain, or inter-subunit.
      Record the citation per target; do not infer from structure alone.
- [x] For any target whose mechanism is inter-subunit: determine whether our
      chain selection retains the coupling partners. If it does not, mark the
      target **unscoreable-by-construction** and say so wherever its results
      are reported.
- [x] H5.1: state what would distinguish conformational selection from induced
      fit **using apo/holo structure pairs only** (no MD — constraint 3). If
      nothing available distinguishes them, say that plainly and close H5.1 as
      *not decidable with our inputs* rather than leaving it open forever.
- [x] Connect to [[HYP-P13]]: H5.1 is the literature statement of the same
      idea. Either fold them together or state precisely how they differ.

## Acceptance

- [x] Per-target mechanism table with citations: intra-domain / inter-domain /
      inter-subunit, and scope-retained yes/no.
- [x] An explicit verdict on CARDIAC_MYOSIN.
- [x] H5.1 either tested or formally closed as undecidable with our inputs.
- [x] Register STATUS for H5 updated to cite this task.

## Constraint

If a mandatory target turns out unscoreable by construction, that goes in the
Phase 1 submission as a finding about the benchmark — not quietly into a
limitations paragraph. [[TASK-0169]] set that precedent and it was the right one.

## Done

**2026-08-24, Implementer B.**

**Citations verified live (Crossref/publisher record, title+authors+journal+
volume+DOI checked, not recalled from training data), before working against
any of them:**

| Claim | Citation | DOI |
|---|---|---|
| Ref [5], MWC | Changeux J-P, Edelstein SJ. Allosteric Mechanisms of Signal Transduction. *Science*. 2005;308:1424-1428. | [10.1126/science.1108595](https://doi.org/10.1126/science.1108595) |
| KRAS switch-II pocket, monomeric | Ostrem JM, Peters U, Sos ML, Wells JA, Shokat KM. K-Ras(G12C) inhibitors allosterically control GTP affinity and effector interactions. *Nature*. 2013;503:548-551. | [10.1038/nature12796](https://doi.org/10.1038/nature12796) |
| BCR_ABL1 myristoyl/SH3-SH2 autoinhibition | Nagar B, Hantschel O, Young MA, et al. Structural basis for the autoinhibition of c-Abl tyrosine kinase. *Cell*. 2003;112:859-871. | [10.1016/S0092-8674(03)00194-6](https://doi.org/10.1016/S0092-8674(03)00194-6) |
| PTP1B α7 allosteric site | Wiesmann C, et al. Allosteric inhibition of protein tyrosine phosphatase 1B. *Nat Struct Mol Biol*. 2004;11:730-737. | [10.1038/nsmb803](https://doi.org/10.1038/nsmb803) |
| Glucokinase GKA site, monomeric | Kamata K, Mitsuya M, Nishimura T, Eiki J, Nagata Y. Structural basis for allosteric regulation of the monomeric allosteric enzyme human glucokinase. *Structure*. 2004;12:429-438. | [10.1016/j.str.2004.02.013](https://doi.org/10.1016/j.str.2004.02.013) |
| Caspase-7 dimer-interface allosteric site | Hardy JA, Lam J, Nguyen JT, O'Brien T, Wells JA. Discovery of an allosteric site in the caspases. *PNAS*. 2004;101:12461-12466. | [10.1073/pnas.0404781101](https://doi.org/10.1073/pnas.0404781101) |
| Caspase-1 dimer-interface allosteric site | Scheer JM, Romanowski MJ, Wells JA. A common allosteric site and mechanism in caspases. *PNAS*. 2006;103:7595-7600. | [10.1073/pnas.0602571103](https://doi.org/10.1073/pnas.0602571103) |
| Cardiac myosin SRX/IHM, two-head | Anderson RL, et al. Deciphering the super relaxed state of human β-cardiac myosin... *PNAS*. 2018;115:E8143-E8152 (already ref [23]); Green EM, et al. *Science*. 2016;351:617-621 (ref [22]); Rohde JA, et al. Mavacamten stabilizes an autoinhibited state of *two-headed* cardiac myosin. *PNAS*. 2018;115:E7486-E7494 (already verified, [[TASK-0236]] — reused, not re-derived). | see rows above |
| Cardiac myosin — mavacamten also has a single-head-intrinsic component | Rohde JA, et al. A small-molecule modulator of cardiac myosin acts on multiple stages of the myosin chemomechanical cycle. *J Biol Chem*. 2017;292:16571-16577. | [10.1074/jbc.M117.776815](https://doi.org/10.1074/jbc.M117.776815) |
| Scope quote | Challenge Statement §5, "Scope and Assumptions": *"Included: The catalytic domains of the proteins."* | `documentation/Cleveland-Clinic-Challenge-Statement-vF-1.md:83`, quoted verbatim, not paraphrased |

### Per-target mechanism table

Scope = the 7 real-drug-ligand, scoreable targets ([[TASK-0209]]'s own
enumeration) plus the Table-1-mandated Cardiac Myosin pair. Non-scoreable
reference entries (HEMOGLOBIN, PFK, GLYCOGEN_PHOSPHORYLASE, TAR_RECEPTOR,
GROEL_SUBUNIT, ATCase, LDH — all `drug_ligand: null` or non-small-molecule)
are out of this table's scope by construction (nothing to score), noted
below where they corroborate the pattern.

| Target | Mechanism (primary lit.) | Class | Scope-retained? |
|---|---|---|---|
| KRAS_G12C | Switch-II pocket on a monomeric small GTPase; the pocket "is not visible in other structures... probably highly dynamic when GDP-bound" (Ostrem 2013) | Intra-domain | **YES** — single chain suffices |
| BCR_ABL1 | Myristoyl group docks into the kinase-domain C-lobe, inducing SH3-SH2 clamp assembly onto the *same* polypeptide's N-lobe/linker (Nagar 2003) | Inter-domain, single chain | **YES** — confirmed directly: 1OPL chain A is 537 residues, 5MO4 chain A is 495 (deposited)/429 (modeled); both far exceed the isolated kinase domain (~280 aa) and match the SH3-SH2-kinase construct length. `chains: ["A"]` retains the whole unit |
| CARDIAC_MYOSIN (incumbent, 8QYP/8QYR) | Mavacamten stabilizes the super-relaxed (SRX) state via the interacting-heads motif (IHM) — **two** myosin-heavy-chain motor domains folding onto each other and their own S2 tails (Anderson 2018, Rohde 2018 — title literally "two-headed") | **Inter-subunit** | **NO** |
| CARDIAC_MYOSIN_TABLE1 | Same mechanism | Inter-subunit | **NO** (and independently unscoreable already, TASK-0169/0222) |
| PTP1B | Allosteric pocket at the α3/α6/α7-helix junction, ~20 Å from Cys215, entirely within one catalytic domain (Wiesmann 2004) | Intra-domain | **YES** |
| GLUCOKINASE | Large/small-domain closure in "the monomeric allosteric enzyme" — the paper's own title (Kamata 2004) | Intra-domain (monomeric) | **YES** |
| CASPASE1 | Allosteric thiol site at the dimer interface, ~15 Å from the active site, a functional circuit couples both protomers (Scheer/Romanowski/Wells 2006) | **Inter-subunit** | **YES** — `chains: ["A","B"]` already retains both protomers |
| CASPASE7 | Allosteric site at the dimer interface, ~14 Å from the active site, same discovery family as CASPASE1 (Hardy et al. 2004) | **Inter-subunit** | **YES** — `chains: ["A","B"]` already retains both protomers |

**Corroborating pattern, not scored (out of table scope):** `ATCase`'s own
config already self-documents the identical defect class — "Allostery is
INTER-SUBUNIT (regulatory vs. catalytic chains). Single-chain analysis
destroys the mechanism" — and confirms only 4 of the true 12-chain
dodecameric assembly are present in either deposited entry used
(`targets.yaml:559-570`). Consistent with this task's finding elsewhere,
not re-derived; `ATCase` is `status: draft, drug_ligand: null`, never
scored, so it does not change any existing result.

### Explicit verdict on CARDIAC_MYOSIN

**Unscoreable-by-construction for the mechanism this target's own config
claims to study**, both pairs. `targets.yaml`'s own `site_name` field says
"Mavacamten super-relaxed/IHM-stabilization site" — but the incumbent
apo/holo pair (8QYP chain A / 8QYR chain B) is, by the config's own prior
comment, deliberately a **single motor domain**, chosen *over* the real
6-chain IHM structure (9GZ1) "because it's cleaner... than a 6-chain IHM
complex" (`targets.yaml:240-247`). That comment already stated the
structural fact; this task supplies the mechanistic consequence it was
never connected to: the coupling the SRX/IHM mechanism runs on — two heads
folding onto each other — is removed from the model before any observable
is computed, exactly H5.2's predicted failure mode. `CARDIAC_MYOSIN_TABLE1`
fails the same way from the opposite direction: its apo (5TBY) genuinely
*is* the 6-chain IHM assembly, but `apo_chains: ["B"]` keeps only one head,
discarding the second on purpose for comparability with the old config.

**One real nuance, not overclaimed.** Rohde et al. 2017 (*J Biol Chem*
292:16571) found mavacamten's inhibition has *two* mechanistically distinct
components: a slowed phosphate-release step **intrinsic to a single S1
head** (present in isolated S1, no IHM required) plus a *separate*,
HMM/two-head-only effect on a slow ADP-release phase. So the physical
XB2 **binding pocket** genuinely is fully formed and drug-contactable
within one motor domain — that half of "find the pocket" may be
representable in a single-chain model. What is **not** representable is
the specific mechanism the target's own name and `objective` field claim
("super-relaxed/IHM-stabilization site") — the distal, allosteric
*consequence* of occupying that pocket is a two-head property, and a
single-chain contact graph has no second head to couple to. The
CTQW pipeline does not distinguish which of the two effects it might be
detecting either way, since it only ever sees one chain.

**This is a third, independent defect** on top of [[TASK-0222]] (mandated
pair's own ligand doesn't resolve) and [[TASK-0169]] (6C1H isn't even
mavacamten-bound) — CARDIAC_MYOSIN fails at three different, independent
checkpoints (label resolution, drug identity, mechanism scope), each
sufficient alone. Per this task's own Constraint, this goes into the
Phase 1 submission as a benchmark finding.

### H5.1 — resolved as not decidable with a single static apo/holo pair; one cheap follow-up identified

**A single deposited apo structure and a single deposited holo structure,
by themselves, cannot distinguish conformational selection from induced
fit.** Both models predict the same observable endpoint — apo ≠ holo
structurally — for different reasons (CS: the ligand captures a rare
pre-existing state; IF: the ligand creates the state). The literature's
actual discriminating signatures are either kinetic (concentration
dependence of binding rates — CS gives saturating/hyperbolic kinetics,
IF does not; Vogt & Di Cera–style analysis) or require an *ensemble* of
the unliganded state (multiple independent apo structures, NMR relaxation
dispersion, room-temperature multi-conformer refinement) to check whether
the holo-like state is already sparsely populated absent ligand. This
register has **one** deposited apo structure per target, not an ensemble,
and constraint 3 excludes MD/kinetics. **Closed: not decidable with our
current inputs**, exactly as this task's own Scope anticipated should be
stated plainly rather than left open indefinitely.

**One piece of existing apparatus could test it without violating
constraint 3, flagged not built**: [[TASK-0229.006]]'s COREX
implementation already generates a computed microstate ensemble from a
*single* structure (combinatorial partial-unfolding statistical
thermodynamics — not MD, not multiple experimental structures). It was
built and run to test EAM-vs-propagation ranking agreement, a different
question. Re-analyzing its own already-computed ensemble to check whether
low-stability microstates already include an active-site-disrupting
conformation, absent any ligand, would be a genuine, cheap test of CS's
core prediction — not attempted here, named as the concrete next step per
this task's own precedent of flagging rather than building beyond scope.

**A correction found while closing this, applied to `REFERENCES.md`
ref [18]'s own note** (see below): that note currently reads the Ostrem
2013 KRAS finding as "induced" ("the pocket is *induced* by the covalent
ligand and does not pre-exist"). The cited paper's own language — "not
visible in other structures... probably highly dynamic when GDP-bound,
until initial encounter with [the] compounds" — is compatible with a
transiently-sampled, minimally-populated pre-existing state (conformational
selection) just as much as with genuine induction, and does not itself
resolve the distinction. This is the same ambiguity H5.1 identifies
in general, now caught in a specific existing claim rather than left as
an abstract point.

### Connecting H5.1 to [[HYP-P13]]

**Same underlying claim, not two open hypotheses.** H5.1 (MWC:
pre-existing equilibrium, ligand selects) and [[HYP-P13]] (allostery is
stabilisation of an already-disfavoured conformation, not propagated
signal) are the same population-shift model of allostery, independently
arrived at — H5.1 is its formal 2005-review literature citation; HYP-P13
is this register's own elaboration, with four register findings it
explains and a decisive test already specified ([[TASK-0229.006]]).
They should **not** be tracked as two separate open items. **Folded**:
`reference_register.md`'s H5.1 line now points to `physics.md`'s HYP-P13
section as the register's live, owned treatment (below); H5's own entry
keeps H5.2 (concerted transitions) as its distinct, separate remaining
question — that half is *not* the same claim as HYP-P13 and stays under
H5's own name.

Ref [4] (Motlagh/Hilser 2014, Ensemble Allosteric Model — already TESTED,
[[TASK-0229.006]]) is the same family again, one level more specific
(binary folded/unfolded units, not just "an equilibrium exists"). So H5.1's
core concept is not "zero coverage" the way [[TASK-0248]]'s citation-level
reconciliation correctly stated (no task had cited *ref [5] itself*) — it
has substantial *indirect* coverage through H4/HYP-P13's own tests. Both
things are true at once and both are stated: the citation was never
directly tested (accurate), and the concept has real, mixed, already-run
evidence via a closely related formulation (also accurate, and the more
useful fact for a reader deciding whether this is worth a new task).

### `REFERENCES.md` updated in the same commit

- Ref [5] (Changeux & Edelstein): STATUS `UNTESTED` → citation-verified
  live; takeaway now points to this task and states the H5.1/H5.2 split
  and the CARDIAC_MYOSIN verdict, rather than the pre-task "flagged, not
  confirmed" language.
- Ref [22]/[23] (Green 2016 / Anderson 2018): STATUS `context`/"not yet
  checked against this citation directly" → verified directly (title,
  journal, volume, DOI all confirmed), now cited as the CARDIAC_MYOSIN
  verdict's own evidentiary basis.
- Ref [18] (Ostrem 2013): takeaway corrected — "induced" language softened
  to the CS/IF-ambiguous phrasing the source paper actually supports (see
  H5.1 above).
- **New rows, method/tool papers table**: Nagar 2003 (BCR_ABL1), Wiesmann
  2004 (PTP1B), Kamata 2004 (GLUCOKINASE), Hardy 2004 (CASPASE7), Scheer
  2006 (CASPASE1), Rohde 2017 (CARDIAC_MYOSIN single-head nuance).

### `reference_register.md` H5 section updated

STATUS line changed from "UNTESTED — confirmed genuinely open" to: H5.1
resolved (folded into HYP-P13, not decidable with current inputs beyond
that fold), H5.2 tested and answered (CARDIAC_MYOSIN both pairs
unscoreable-by-construction; all other 6 scoreable targets' mechanisms
verified either intra-domain/monomeric or inter-subunit-but-scope-retained).
Coverage-summary table row updated to cite [[TASK-0251]].

### Not done

- H5.2's per-target literature check covered the 7 scored targets + the
  Table-1 pair, not every entry in `targets.yaml` (HEMOGLOBIN/PFK/etc. are
  non-scoreable placeholders — noted, not chased further, since nothing
  changes for them either way).
- The COREX-ensemble re-analysis flagged above for H5.1 is named, not built.
- **`documentation/PHASE1_SUBMISSION_DRAFT.md` is not edited here**, despite
  this task's own Constraint ("goes in the Phase 1 submission... not quietly
  into a limitations paragraph"). Checked directly: neither [[TASK-0222]]
  (mandated pair unscoreable) nor [[TASK-0169]] (6C1H isn't mavacamten-bound)
  is cited anywhere in that document either — CARDIAC_MYOSIN currently has
  **zero** of its three known defects written up there, not just this task's
  own third one. Writing only this task's finding would misrepresent the
  target as having one problem instead of three independent ones. A proper
  fix needs all three folded together in one place, which is a larger,
  separate scope than this task's own Acceptance requires — flagged as a
  concrete follow-up, not done silently and not done half-right.
- No code changed. Documentation/citation task only, per its own Scope.

Tests: none — documentation/citation task, no `src/`/`allostery/` code
touched.
