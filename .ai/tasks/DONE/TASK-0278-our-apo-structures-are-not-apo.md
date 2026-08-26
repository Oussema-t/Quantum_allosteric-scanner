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

- [x] Extend the audit to **every** apo structure in `config/targets.yaml` and
      `config/candidate_targets_task0243.yaml`. 29 distinct apo PDBs audited
      live; see Done.
- [x] **Write the classification rule down** as a reusable convention, and add
      it to [[TASK-0209]]'s VALID rule. Done as a dated addendum to that
      task's own file (append-only, per this register's own convention —
      historical numbers untouched).
- [x] For BCR-ABL1: decide what to do. **Decision: (b) — keep `1OPL`, report
      the defect explicitly**, plus (c) run explicitly as a disclosed
      *control*, not a fix (see Done for why stripping does not actually
      close the pocket). (a) remains foreclosed — [[TASK-0270]] already
      searched and found no genuinely myristoyl-pocket-empty candidate.
- [x] Re-run BCR-ABL1's headline numbers old vs new (native vs MYR-stripped
      control) side by side. See Done.
- [x] Quantify how much of BCR-ABL1's fpocket signal survives if the pocket
      is not pre-opened by a bound ligand. See Done — the precise historical
      "0.8596" figure's own originating script was not chased down further
      (several close-but-not-identical numbers exist in this register for
      related-but-different quantities); a fresh, reproducible number is
      computed directly instead.

## Acceptance

- [x] Full apo-contents audit across both configs with the classification
      applied.
- [x] The classification rule written into [[TASK-0209]]'s VALID criteria.
- [x] A decision on BCR-ABL1 with a submission-ready rationale.
- [x] Side-by-side re-run of affected numbers.
- [x] `RESULTS.md`; and flag `documentation/PHASE1_SUBMISSION_DRAFT.md`, which
      currently discusses BCR-ABL1's pre-formed pocket without this cause.
      **Flagged in Done, not edited**, per this task's own Acceptance wording.

## Constraint

This is a defect in **our own** benchmark construction, found by us, on a
mandatory target. Report it with the prominence [[TASK-0169]] and
[[TASK-0270]] received. It makes several of our own prior findings *less*
mysterious rather than more impressive — BCR-ABL1's "pre-formed pocket" was
never a discovery about protein dynamics — and that correction is owed.

## Done

**2026-08-26, Implementer B.** Full numbers in `RESULTS.md`'s own section
and `results/tasks/0278_apo_contents_audit/` (not duplicated verbatim
here) — summary:

**The underlying MYR measurement already existed.** [[TASK-0209]]'s own
`hetatm_audit` (2026-08-07) already flagged `MYR` as
`unexpected_near_pocket` (`min_dist_to_pocket_window=3.47`) for BCR_ABL1.
What this task adds: a *named, reusable* classification rule, live
verification of every other apo structure in the register by the same
standard, and a decision + re-run for BCR_ABL1 specifically. Written up
as a dated addendum to [[TASK-0209]]'s own file (Scope item 2), not a
silent rewrite of its historical numbers.

**Method, and a real defect in the naive version caught before trusting
any number**: enumerated every non-water HETATM directly from the
resolved structure (`backend.rcsb.ligands_and_sites` — not the Data API's
own `nonpolymer_bound_components`, [[TASK-0270]]'s own already-found
blind spot). The first pass over-flagged: `M3L` (N-trimethyllysine,
`CARDIAC_MYOSIN`), `ACE`/`GG7` (N-terminal caps, `HIV_INTEGRASE`) are
**covalently peptide-bonded modified residues**, not free ligands —
`Bio.PDB`'s own hetero flag does not distinguish "free small molecule"
from "covalent in-chain modification," both are recorded as HETATM in
the PDB format. Checked directly (C–N bond distance to the neighbouring
residue, ~1.34 Å either side of `M3L`-129/549 in `8QYP`) before writing
the exclusion filter, not assumed from the residue code alone — 16/29
apo structures flagged broken on the first pass, 14/29 after excluding
genuine covalent modifications. A second correction, biochemical rather
than structural: `classify_ligand`'s own "drug"/"ligand" categories
mis-flag several genuine **cognate substrates/products** as synthetic —
`GLN` (glutaminase's own substrate, `GAC_BPTES`/`GAC_CPD12`), `GLC`
(glucose, `GLUCOKINASE`'s own substrate), `FBP` (phosphofructokinase's
own reaction product, entry `1PFK` explicitly titled "...WITH ITS
REACTION PRODUCTS"), `NMN` (NAMPT's own reaction product, entry `3DHF`
explicitly titled "...phosphorylated mimic form... complexed with
nicotinamide mononucleotide") — the tool was built for the live app's
"is this worth highlighting as a drug" question, not "is this cognate for
THIS enzyme," and the two questions differ.

**The decisive test is not "does the apo structure contain any ligand," it
is whether that ligand overlaps the SPECIFIC pocket window being
scored** — computed directly (heavy-atom binding-site vs. each target's
own pocket window, not assumed):

| target | apo | occupant | window overlap | verdict |
|---|---|---|---|---|
| **BCR_ABL1** | `1OPL` | `MYR` | **75%** | **pocket-confounding** (mandatory target) |
| **GLUCOKINASE** | `1V4S` | `MRK` | **88%** | **pocket-confounding** |
| **PKR_MITAPIVAT** / **PKR_AG946** | `7FS3` | `O9I` (an allosteric modulator, per the entry's own title) | **92% / 91%** | **pocket-confounding — the worst case found, not in this task's own original filing** |
| CARDIAC_MYOSIN | `8QYP` | `VO4` (vanadate) | **0%** | **not** pocket-confounding — corrects this task's own filing's "suspect" label; a chemically-trapped-state caveat remains, but it does not sit in the scored window |
| HCV_NS5B_VRX/VR1, HCV_NS5B_POO/CMF, KSHV_PROTEASE_24Q/25G, SMYD3_DIPERODON, PF_ATCASE | `2GIQ`, `2HAI`, `2PBK`, `6P7Z`, `7ZP2` | real inhibitors, each entry's own RCSB title explicitly names it a complex | 0% each | ligand-bound, but **not** at the scored site — not "clean apo" in an absolute sense, disclosed, but does not confound this specific pocket-prediction task |

**PKR_MITAPIVAT/PKR_AG946 is a new, real, and worse-than-BCR_ABL1 finding**,
found only because this task's own Scope asked for the full-register
sweep rather than stopping at the target the filing named. `7FS3` is
deposited as "Structure of liver pyruvate kinase in complex with
allosteric modulator 15" — used as "apo" for both targets, its own bound
modulator (`O9I`) covering 91–92% of the very window the pipeline scores.
**Not remediated here** — PKR is not a mandatory target and this task's
own Scope only asks for a BCR_ABL1 decision — flagged with full
prominence for a follow-up task; whoever owns curation next should not
have to rediscover this.

**BCR_ABL1 decision: (b) — keep `1OPL`, report the defect explicitly.**
(a) is foreclosed: [[TASK-0270]] already searched real candidates
(`2G1T`, `2G2H`, `2G2I`) and found none genuinely myristoyl-pocket-empty,
with real scored evidence (`2G1T` AUC=0.350, below chance) against
substituting. (c) was run explicitly, as this task's own Constraint
requires, as a **control, not a fix** — and it is decisive against
treating stripping as a solution:

| | native `1OPL` (MYR present) | `MYR` computationally stripped |
|---|---|---|
| window overlap_frac | 0.875 | 0.875 (**unchanged**) |
| window druggability_score | 0.761 | 0.566 (drops, still clears `_is_hit`) |
| residue-level fpocket AUC | 0.8952 | 0.8952 (**bit-identical**) |
| `apo_native_hit` | **True** | **True** (unchanged) |

**Stripping `MYR`'s own atoms does not close the pocket.** fpocket's
cavity detection is driven by the **protein backbone's own geometry**,
which is already in the myristate-stabilised open conformation — deleting
the ligand's coordinates after the fact does not relax the backbone back
toward a hypothetical closed state (no minimisation is performed; there is
nothing in this register's toolchain that would do so, the same
observation [[TASK-0271]]'s own repulsor-release test made from a
different angle). This *sharpens*, not softens, the finding: the confound
is not "an atom happens to be present in the file," it is that the
crystallised conformation itself was captured with the pocket already
held open — exactly consistent with `MYR` "holding the pocket open" being
a real structural fact, not an artifact fixable by deleting three lines
from a PDB file. **Scope item 5's own question, answered precisely: the
apo-side signal survives stripping almost entirely** (druggability drops
28% but the window classification and the residue-level predictor AUC are
unchanged) — reinforcing (b) over any silent reliance on (c) alone.

**Why this explains prior findings, now on direct, quantified evidence**
(not re-argued here, see this task's own filing and `RESULTS.md` for the
full mechanistic point already made about [[TASK-0265]]/[[TASK-0276]]):
[[TASK-0120]]/[[TASK-0139]]'s "pre-formed pocket" (RMSD ratio 0.49) and
fpocket's own strong BCR_ABL1 solo score are, at least in significant
part, properties of `1OPL`'s own crystal contents, not a discovery about
c-Abl's intrinsic dynamics.

**`documentation/PHASE1_SUBMISSION_DRAFT.md` flagged, not edited**, per
this task's own Acceptance — needs the MYR/pocket-pre-formation causal
note wherever BCR-ABL1's pre-formed pocket is currently discussed without
it.

**Artifacts**: `scripts/task0278_apo_contents_audit.py`,
`scripts/task0278_bcr_abl1_myr_strip.py`; `results/tasks/
0278_apo_contents_audit/{apo_contents_audit.json,bcr_abl1_myr_strip.json}`;
`.ai/tasks/DONE/TASK-0209-known-answer-cryptic-instance-set.md` (dated
addendum); `RESULTS.md`; this file.

**Not attempted, explicitly out of scope**: remediating PKR_MITAPIVAT/
PKR_AG946's own apo (flagged for a follow-up task, not this one's own
Scope); a deeper investigation of `PHN` (`TAR_RECEPTOR`, non-mandatory,
ambiguous chelator-vs-additive status left unresolved); re-scoring every
register number that ever cited BCR_ABL1's apo-side druggability (this
task states the defect and re-runs the specific numbers its own Scope
names, not a full register re-run).
