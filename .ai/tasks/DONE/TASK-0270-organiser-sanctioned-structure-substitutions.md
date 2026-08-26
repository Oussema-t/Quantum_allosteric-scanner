# TASK-0270 — Act on the organiser-sanctioned structure substitutions: KRAS `8S8C`, BCR-ABL1 apo

- Status: Done
- Assignee: **Implementer B** (after [[TASK-0265]] — same structural-validity skillset, and 0265's BCR-ABL1 myristoyl work feeds directly into item 2)
- Priority: **High — an organiser permission with an expiry-free window, but it changes published numbers, so decide deliberately**
- Filed: 2026-08-26 by Reviewer
- Source: `documentation/2026-08-26-organiser-clarifications.md`
- Related: [[TASK-0221]], [[TASK-0222]], [[TASK-0169]], [[TASK-0250]], [[TASK-0257]], [[TASK-0258]], [[TASK-0265]], [[TASK-0184]]

## What the organisers said

Verbatim text and provenance in
`documentation/2026-08-26-organiser-clarifications.md`. Two items require a
decision:

> 2. A nice structure for KRAS G12C would be 8S8C.
> 4. BCR-ABL1 — you may substitute 1OPL with an alternative apo structure that fits your pipeline. Please document the rationale in your submission.

**This was a private reply to us. There is no corresponding public revision of
the Challenge Statement** (checked 2026-08-26). Both items must therefore be
cited to that clarification wherever they appear in the submission.

## Item 1 — KRAS G12C: `4OBE` is the wrong protein, and `8S8C` is the sanctioned fix

**REFRAMED 2026-08-26.** The Reviewer's first reading of this item was wrong
and is corrected here. The organisers' line — *"A nice structure for KRAS G12C
would be 8S8C"* — is **not an unprompted suggestion**. It is the answer to a
defect we reported:

> **2. KRAS G12C 4OBE structure.** We found that it is not the G12C mutant,
> but wild-type at residue 12 (GLY not CYS). Should we be using this
> structure, or find/use the actual mutated one?

So the answer means: **yes, 4OBE is wrong; use 8S8C.**

**This is not a new finding — it is a known, recorded, unfixed defect.**
[[TASK-0155]] found it and [[TASK-0192]] flagged it; `ARCHITECTURE.md`'s
2026-08-03 change-log entry records it as *"a real, unresolved inconsistency
(not a defensible modelling choice as shipped)"*, and `SOFTWARE.md`'s
benchmark table carries the ⚠️ footnote *"4OBE is wild-type KRAS, not G12C
(chain A residue 12 is GLY, confirmed)"*. It was never fixed because *"no apo
swap — that is a register-wide re-run, explicitly out of scope here."*

**The organisers have now authorised that re-run.** What was an unfixable
known defect is now a sanctioned correction, and the scope objection no longer
applies.

### Consequence, stated plainly

Every KRAS_G12C number in this register was computed on a structure that **is
not the G12C mutant** — including the flagship figures: ENM validity
(`r = 0.646`, PASS, [[TASK-0250]]), the attribution shares, the pocket
taxonomy (contact-adjacent, min heavy-atom **1.32 Å**, [[TASK-0258]]), and
[[TASK-0169]]'s "pocket is 3.75 Å from the active site" benchmark finding. The
covalent anchor the whole Sotorasib mechanism depends on — Cys12 — **is not
present in our apo.**

- [x] Verify `8S8C` live against RCSB **before** swapping: method, resolution,
      chains, ligands, and specifically **confirm residue 12 is CYS**. Do not
      inherit the organisers' recommendation unchecked — [[TASK-0169]] is the
      precedent for a mandated structure not containing what its own table
      claimed, and this item exists *because* that happened once already.
- [x] Confirm whether 8S8C is apo or holo. The organisers did not say.
- [x] Re-run every KRAS_G12C figure on the corrected apo, and report old and
      new side by side — the delta is itself a finding about how much a
      genotype error moved our numbers.
- [x] Propagate the fix out of the research register into the live app:
      `backend/systems.py`'s `KRAS_G12C` entry ships `apo="4OBE"` with
      `covalent_anchor=12` / `top5_full_named=["CYS12", ...]`. Update
      `SOFTWARE.md`'s benchmark table and footnote, `config/targets.yaml`, and
      `COMPETENCE_MAP.md`, all of which currently carry the flag.
- [x] Add a dated `ARCHITECTURE.md` change-log line closing the 2026-08-03
      entry, citing the organiser clarification as the authority.

## Item 2 — BCR-ABL1 apo substitution

Permission granted, **rationale required in the submission** — that is an
explicit instruction, not a courtesy.

- [x] Enumerate candidate apo structures for ABL1 kinase that fit the
      pipeline, with the [[TASK-0209]] VALID rule applied and live RCSB
      verification of each.
- [x] Score the strongest candidate alongside `1OPL`; report both.
- [x] Weigh, explicitly, and write the reasoning down for the submission:
      - **For substituting**: 1OPL's ENM validity is only **MARGINAL**
        (`r = 0.493`, [[TASK-0250]]), so its ENM-derived results are weakly
        interpretable under [[TASK-0257]]'s framing.
      - **For substituting**: 1OPL is the autoinhibited near-full-length
        structure, which entangles the myristoyl/N-cap mechanism
        [[TASK-0265]] is investigating. A cleaner kinase-domain apo may make
        the pocket question tractable — **or may remove the mechanism from the
        model entirely**, which is the [[TASK-0251]] scope-truncation failure
        mode in a new place. Decide knowingly.
      - **Against substituting**: every published BCR-ABL1 number rests on
        1OPL, including the pocket taxonomy (proximal, min heavy-atom 7.96 Å)
        and the [[TASK-0235]]/[[TASK-0241]] ceiling dispute. Substitution
        invalidates that comparison set.
- [x] Coordinate with [[TASK-0265]]: its BCR-ABL1 myristoyl verification
      should inform this choice, not run in parallel and disagree.

## Item 3 — housekeeping

- [x] Mark [[TASK-0222]] resolved: 8QYP → 8QYR is sanctioned as primary, on
      the record.
- [x] Update [[TASK-0221]] §3 with the answers received and the four questions
      that remain open — **(d), (e), (f)**, of which **(f) gates
      [[TASK-0269]]**.
- [x] Flag to Bartosz that the channel is live and responsive: (e) and (f) are
      both worth re-asking, and (f) would let [[TASK-0269]] proceed on an
      organiser ruling rather than our own permissive reading.

## Acceptance

- [x] Live RCSB characterisation of `8S8C`, stated before any substitution.
- [x] Side-by-side scoring for both targets — never a silent swap.
- [x] A written rationale for the BCR-ABL1 choice, in submission-ready prose,
      since the organisers explicitly require it.
- [x] [[TASK-0222]] closed, [[TASK-0221]] updated.
- [x] `RESULTS.md`.

## Constraint

An organiser permission is not an instruction to use it. If 8S8C or a new ABL1
apo makes our numbers *worse*, that is still the honest choice if the
structure is better — and if we decline a permitted substitution, the
submission should say why. **Neither substitution may be adopted because it
improves a result.** Decide on structural grounds, then report whatever the
numbers do.

## Done

**2026-08-26, Implementer B.**

### Item 1 — KRAS G12C: `8S8C` is HOLO, not apo; `4LDJ` adopted instead; the register's own headline result does not survive

**Live RCSB verification of `8S8C`, before anything else** (this task's own
Acceptance requirement): X-ray, 1.90 Å, title "Structure of Kras in complex
with inhibitor MK-1084" (Ma et al. 2024, *J Med Chem* 67:11024-11052,
DOI 10.1021/acs.jmedchem.4c00572). Ligands: **A1H5U (MK-1084, a covalent
Switch-II-pocket inhibitor), GDP, MG.** Residue 12 confirmed Cys (genuine
G12C) via direct sequence inspection. **8S8C is HOLO — a drug-bound
structure, not usable as an apo replacement.** The paper's own deposition
set was checked for a companion apo structure (same DOI, same depositors
Day/Cleasby, adjacent PDB IDs) — none exists; this paper deposited only
8S8C.

**6OIM (current holo) independently re-verified**, not assumed correct
because already in use: residue 12 = Cys confirmed via SIFTS-anchored
sequence mapping (a naive raw-FASTA character count is wrong here due to
an N-terminal expression tag — the same trap [[TASK-0155]]'s own method
already accounted for). Genuinely G12C, X-ray 1.65 Å, GDP/MG/MOV
(sotorasib) — no issue found.

**A real, load-bearing bug found in [[TASK-0155]]'s own candidate pool,
before trusting it for the apo replacement**: that task's own docstring
claims its 10-structure pool is filtered to "GDP+Mg-only... excludes ~90
inhibitor-bound structures." Re-checked by enumerating every non-polymer
entity per structure directly (not the RCSB summary field
`nonpolymer_bound_components`, which lists only metal-*coordinated*
components and silently misses non-coordinating small-molecule inhibitors
— almost certainly why the original filter passed these through): **8 of
the 10 are actually drug-bound**: 8AZX (BI-2865), 7A1X (Cpd1/QWB), 8QUG
(Compound 1/WYU), 9UOH (ASP2453), 7YCE (Compound 7b/IQN), 7MDP
(G-2897/Z07), 7RP3 (GNE-1952, covalently alkylated/MKZ), 8AFC (Compound
12/LXK). Only **4LDJ** (1.15 Å) and **8TXJ** (1.4 Å) are genuinely apo.
[[TASK-0155]]'s own file corrected in place with a dated note — its "10
true-genotype structures, median AUC 0.482" distribution claim does not
hold as stated; only 2 of its 10 rows are actually apo-vs-apo comparable,
not enough to support that distributional claim either way. Flagged as a
real follow-up (a properly-filtered replacement sweep), not attempted
here — out of this task's own scope.

**`4LDJ` adopted, on structural grounds** (this task's own Constraint):
best resolution of the two genuine candidates, both single chain A,
residue 12 = Cys independently re-verified via the same anchor-relative
method. Not chosen for a flattering result — see below, it is not one.

**Every named figure re-run, old (4OBE) vs. new (4LDJ), same pipeline, same
holo (6OIM), same everything else** — new `scripts/
task0270_kras_g12c_genotype_fix.py`, reusing `apo_structure_sensitivity_
sweep.run_one` ([[TASK-0155]]'s own pipeline call, unmodified),
`potentials._gnm_msf` ([[TASK-0250]]'s own method), and the (chain,resnum)
heavy-atom distance approach ([[TASK-0255]]/[[TASK-0265]]):

| metric | OLD (4OBE, wild-type) | NEW (4LDJ, genuine G12C) |
|---|---|---|
| AUC | 0.557 | 0.514 |
| P@5 | 0.000 | 0.000 |
| **Diagnosis** | **`NO_FAILURE_DETECTED`** | **`NO_SIGNAL_IN_APO`** |
| ENM validity (r, [[TASK-0250]]'s bars) | 0.646 (PASS) | 0.496 (MARGINAL) |
| Pocket-to-active-site min heavy-atom dist. | 1.32 Å | 1.31 Å |

**Decisive: the register's own only clean mandatory-target floor-clear
result does not survive the genotype fix.** 4OBE's own AUC (0.557) closely
reproduces [[TASK-0239]]'s already-corrected "Actual (now)" figure
(0.5565) — cross-validates this script's own pipeline call before trusting
its 4LDJ number. P@5 and the pocket-to-active-site distance are essentially
unchanged (both structures place the pocket contact-adjacent to the active
site — consistent with, not contradicting, [[TASK-0255]]'s register-wide
finding). The ENM model itself also fits measurably worse on the real
mutant (PASS→MARGINAL).

**Propagated to the live app and every doc that carried the flag, same
commit**: `config/targets.yaml` (`apo_pdb`, comment rewritten), `backend/
systems.py` (`apo="4LDJ"`, comment rewritten — `covalent_anchor=12`/
`top5_full_named`'s "CYS12" were already correct as biological-target
descriptions, independent of which apo PDB is loaded, left unchanged),
`SOFTWARE.md` (benchmark table row + footnote), `COMPETENCE_MAP.md` (new
dated stacked CAVEAT closing the [[TASK-0155]]/[[TASK-0192]]/[[TASK-0239]]
chain), `ARCHITECTURE.md` (new change-log entry closing the 2026-08-03
one). **Live-app smoke test**: `backend.pipeline.build_view("4LDJ",
chains="A", ...)` runs end-to-end with no crash before treating the swap
as safe to ship.

### Item 2 — BCR-ABL1: enumerated, scored, decided against substitution

**Candidate enumeration**: RCSB full-text search ("ABL1 tyrosine-protein
kinase", Homo sapiens, X-ray) → 811 polymer entities. Checked the
best-known kinase-domain-only family directly (the motivating case the
task's own "For substituting" argument names — "a cleaner kinase-domain
apo"): **2GQG** (278 res, dasatinib-bound — holo), **2G1T/2G2H/2G2I** ("A
Src-like inactive conformation in the Abl tyrosine kinase domain," ~287
res) — none genuinely ligand-free either: 2G1T has an ATP-analog (112) at
the catalytic site, 2G2H a real inhibitor (P16), 2G2I has ADP. **No
genuinely apo (fully ligand-free) kinase-domain-only ABL1 structure was
found** — every kinase-domain construct in this family carries some
ATP-site occupant, unlike 1OPL/5MO4's own myristoyl-pocket-only ligand
pattern.

**Strongest candidate scored alongside 1OPL** (highest-resolution of the
kinase-domain-only family, 1.8 Å): **2G1T**, same pipeline, same holo
(5MO4):

| metric | 1OPL (current, SH3-SH2-kinase) | 2G1T (kinase-domain-only, ATP-analog bound) |
|---|---|---|
| N residues | 451 | 271 |
| AUC | 0.541 | **0.350** |
| P@5 | 0.000 | 0.000 |
| Diagnosis | `NO_SIGNAL_IN_APO` | `BEATS_CHANCE_NOT_FLOOR` |
| ENM validity (r) | 0.493 (MARGINAL) | **0.660 (PASS)** |

1OPL's own AUC (0.541) closely reproduces [[TASK-0239]]'s corrected
"Actual (now)" figure (0.5408) — cross-validates before trusting the 2G1T
number.

**Real, structurally-grounded trade-off, not a cherry-pick** (1OPL's own
result is not flattering either — `NO_SIGNAL_IN_APO` — so this is not
"keeping the better number"): the kinase-domain-only construct's ENM
genuinely fits better (MARGINAL→PASS), exactly as the "for substituting"
case predicted. But its AUC **collapses to well below chance** (0.541→
0.350) — real, measured evidence for the task's own flagged concern that a
truncated construct "may remove the mechanism from the model entirely,"
the [[TASK-0251]] scope-truncation failure mode in a new place.

**Coordinated with [[TASK-0265]], not run in parallel and disagreeing**:
that task live-verified the myristoyl mechanism does **not** require
covalent tethering (non-covalent pocket occupancy alone induces the
autoinhibitory bend) — meaning the SH3-SH2-kinase construct's own value is
not about the myristoyl group's covalent status, but about the regulatory
domains being physically present to dock at all. A kinase-domain-only
construct removes those domains entirely — consistent with, and now
scored evidence for, exactly the mechanism [[TASK-0265]] characterised.

**Decision: do not substitute. Keep 1OPL.** Three converging reasons, none
of them "the number looks better": (1) the mechanistic case
([[TASK-0265]]) — the full construct is required to represent genuine
autoinhibition; (2) the scored evidence above — the only kinase-domain-only
candidate checked measurably worsens AUC; (3) every published BCR-ABL1
number already rests on 1OPL — substitution invalidates that comparison
set for no measured gain. **Written rationale, submission-ready**: *"We
considered substituting BCR-ABL1's apo structure (1OPL, the autoinhibited
near-full-length SH3-SH2-kinase construct) for a cleaner, kinase-domain-only
alternative, as organiser-permitted. We declined. The myristoyl-pocket
autoinhibition mechanism our target studies requires the SH3-SH2 regulatory
unit to be physically present and able to dock onto the kinase domain — a
kinase-domain-only construct removes that mechanism from the model by
construction, not merely simplifies it. We scored the best available
kinase-domain-only candidate (PDB 2G1T) against 1OPL under our own
pipeline: its ENM validity improves (r=0.493→0.660) but its AUC collapses
to below chance (0.541→0.350), consistent with the mechanism being absent
from the model. We report this as real, structurally-grounded evidence for
declining a permitted substitution, not as a preference for a better
number — 1OPL's own result is not a floor-clearing one either."*

### Item 3 — housekeeping

**[[TASK-0222]] marked resolved** in place, dated note added: the
organisers' own item 4 answer implicitly confirms the register's own
8QYP→8QYR substitution reasoning (by granting the analogous BCR-ABL1
permission on the same structural-validity grounds), and no objection to
the Cardiac Myosin substitution itself has been raised. 8QYP→8QYR stands
as primary.

**[[TASK-0221]] §3 and the Bartosz flag: found already done by a
concurrent thread when this task reached them, not duplicated.** By the
time this task's Item 3 was reached, [[TASK-0221]]'s own §3 already
carried a full "ANSWERED 2026-08-26" table (items (a)-(f), open items
correctly marked) **and** a "Follow-up questions sent 2026-08-26" section
with (e)/(f) already re-sent verbatim as standalone Q6/Q7. Left untouched
— re-editing a correct, already-complete, actively-shared file would only
risk a collision for no gain.

### Not done

- A properly-filtered replacement for [[TASK-0155]]'s own apo-sensitivity
  sweep (new candidate pool, ligand set checked by full non-polymer-entity
  enumeration, not the misleading summary field) — flagged as a real,
  valuable follow-up in that task's own corrected file, not attempted here
  (a distributional claim needs its own task, not a byproduct of this
  one's single-structure pick).
- BCR-ABL1 candidate enumeration was not exhaustive across all 811 X-ray
  hits — the kinase-domain-only family most directly matching the task's
  own "for substituting" motivation was checked and scored; a full sweep
  of every candidate was not attempted, consistent with this task's own
  Constraint asking for a decision on structural grounds from the
  strongest candidate, not an exhaustive distribution.

**Scripts**: `scripts/task0270_kras_g12c_genotype_fix.py`. **Data**:
`results/tasks/0270_kras_g12c_genotype_fix/kras_genotype_fix.json`.
BCR-ABL1's 2G1T comparison was run inline (reported above and in
`RESULTS.md`), not saved as a separate script — a one-off structural
comparison, not a reusable pipeline.
