# TASK-0372 — E0: is the aromatic enrichment at allosteric sites real, or is it burial plus ligand contact?

- Status: Done
- Owner: **Implementer**
- Priority: **High. Cleared to run — compute is available (Team Lead, 2026-09-12).**
- Filed: 2026-09-12 by Reviewer thread (id via `claim.py reserve-next`)
- Source: external reviewer discussion, 2026-09-11/12 (conical intersections / electronic coupling)
- Related: [[TASK-0329]], [[TASK-0345]], [[TASK-0373]], [[TASK-0374]], [[HYP-P13]]

## The claim under test

Screening ASBench's 118 curated entries (1,413 annotated allosteric residues), an
external reviewer reports:

> **Aromatic (F/Y/W/H) content at allosteric sites: 15.7% vs ~10.2% background.
> Roughly 1.5×.** Tyr 5.3%, Phe 5.0%, His 3.5%, Trp 1.8%. 69% of targets above
> background, 36 of 115 above 20%. Top: hemoglobin 50%, P450 50%, Cu nitrite
> reductase 44%, COX-2 36%, IDH1 26%.

The background figure is sane — F+Y+W+H across proteins is ≈10.8% (Phe ~3.9,
Tyr ~3.2, His ~2.3, Trp ~1.4) — so the 1.54× is real arithmetic, not a slip.

**The reviewer names the burial confound themselves and pre-registers this gate
before doing anything else.** That is the right instinct and the reason this is
worth a task rather than a dismissal.

## The confound they did not name, and it is in our own register

Their E0 residualises on **burial**. That is necessary and not sufficient.

**ASBench annotates allosteric sites as ligand-contact residues.** Our own §1
reports, committed and checked: **40 of 40 ASBench structures we sampled carry a
bound ligand at the scored site** ([[TASK-0329]], generalised at scale by
[[TASK-0345]]). And aromatics dominate ligand binding generally — that is
textbook, not a subtle effect.

**So 15.7% vs 10.2% may be measuring "aromatics touch ligands", which is neither
allostery nor electronic structure.**

The reviewer's paired active-site control is the right instinct, because active
sites are ligand sites too. But **matched on burial alone it will pass while
testing the wrong thing.** The match must be on **burial *and* ligand contact**.

## Intent Contract

- **Outcome:** does aromatic enrichment at allosteric sites survive a control
  matched on both burial and ligand contact, using active sites in the *same
  protein* as the paired comparison?
- **In scope:**
  1. Resolve **residue identities** for active sites from the PDB files — ASBench
     annotates them by number only (`"A41"`), so the paired control cannot be run
     from the catalogue alone. This is the step that makes the task non-trivial.
  2. Compute relative SASA for every annotated residue.
  3. **Test aromatic enrichment residualised on relative burial, paired
     within-protein against active sites** — the register's standard
     rank-residualisation, the same machinery that demoted our own headline.
  4. **Add the ligand-contact stratum.** Report the enrichment separately for
     residues within contact distance of a bound ligand and for those outside it.
     If the effect lives only in the contacting stratum, it is a ligand-binding
     result.
  5. Cluster-robust inference ([[TASK-0337]]) — 118 entries are not 118
     independent proteins.
- **Out of scope:** E1–E4 ([[TASK-0374]]); any submission text ([[TASK-0373]]);
  any electronic-structure calculation. This task is entirely classical.
- **Constraints and invariants:** the comparison is **within protein**, not
  against a global background — a cross-protein background cannot control for
  composition. State the ligand-contact rule once, before scoring.

## Pre-registered prediction

Two-sided and genuinely uncertain. **The most likely single outcome is that the
effect is burial plus ligand contact and vanishes**, which is a clean negative and
is recorded as one. **The interesting outcome is narrower than the headline**: if
allosteric sites are *more* aromatic than equally-buried, equally-ligand-contacting
active sites **in the same protein**, that is a real asymmetry and nothing in this
register explains it.

## Timing — cleared to run, with the reason the gate existed still standing

**Ungated 2026-09-12: compute is available, so run it.**

The original hold was never about the calendar — it was about the risk of a rushed
E0 that omits the ligand-contact stratum and reports burial as electronics. **That
risk does not go away because there is more compute.** Run it properly or not at
all: the stratum is not optional, and neither is the within-protein pairing.

Two consequences of running before the deadline rather than after:

- **A result in hand is worth more than a plan**, and if the enrichment survives,
  [[TASK-0373]]'s reframe stops being purely a hypothesis about the input and
  gains one measured fact behind it. **It still must not be stated as a quantum
  result** — surviving E0 means "aromatic composition differs", not "electronic
  coupling matters".
- **A clean negative is equally usable and costs nothing**, because the submission
  does not currently claim anything here. Report it either way, as this register
  reports every other null.

## Dependency

- [[TASK-0329]] / [[TASK-0345]] (Done) — the 40/40 ligand-occupancy finding that
  makes the second control mandatory.
- ASBench catalogue, already vendored on the `allosteric` branch.

## Done

**2026-09-12, Implementer A.** No blocker before pickup (dependencies Done,
ASBench catalogue present, `allostery.corex` SASA machinery reusable
as-is). Script: `scripts/task0372_aromatic_enrichment_gate.py`. Full
118-entry cohort, 205s wall time, 1 structure (`3BCR`) failed to fetch
(404, not RCSB-current) — 117 scored.

### Reused, not re-derived

`allostery.corex.per_atom_asa`/`per_residue_native_asa`/`MAX_ASA` (the
same validated BioPython ShrakeRupley SASA computation TASK-0257/
TASK-0266 already used) for burial; TASK-0329's own ligand-contact
definition (non-JUNK HETATM within 4.5 Å of a residue's own heavy atoms,
same `JUNK` list), reshaped from TASK-0359's whole-structure boolean into
a per-residue flag since this task's own Intent Contract needs the
contacting/non-contacting split kept separate, not collapsed. Residue
identities: `allosteric_residues` already carries the resname in
ASBench's own annotation string; `active_residues` does not (`"A41"`,
chain+resnum only) — resolved by parsing the deposited structure, the
step the filing named as non-trivial.

### Planned Validation — reproduce the reviewer's own raw number first

Allosteric aromatic fraction = **0.1562** (reviewer: 0.157) — matches to
three significant figures, confirming the cohort/parsing is right before
trusting anything built on it. Active-site fraction (this task's own
matched control, not the reviewer's generic cross-protein background) =
**0.1276**, giving ratio **1.22**, not the reviewer's cross-protein 1.54 —
**a first, cheap finding on its own**: active sites are themselves
aromatic-enriched relative to bulk protein composition (unsurprising —
they bind small molecules too), so part of the reviewer's own naive 1.54×
was already comparing against the wrong baseline, before burial or ligand
contact are even considered.

### Result — burial-residualised, paired within-protein, cluster-tested by protein

| stratum | n rows | n proteins | raw allo | raw act | mean resid Δ | cluster-p |
|---|---|---|---|---|---|---|
| all residues | 3830 | 79 | 15.6% | 12.8% | +5.86 | **0.856** |
| ligand-contacting | 2147 | 49 | 16.5% | 14.0% | +18.4 | **0.515** |
| non-contacting | 1683 | 20 (exact) | 11.7% | 11.9% | **−25.4** | **0.406** |

**The pre-registered most-likely outcome holds: the effect does not
survive.** Once matched within the same protein against its own active
site and residualised on burial, the aromatic-enrichment signal is not
significant in any stratum — p=0.86 overall, p=0.52 where a ligand is
present, p=0.41 where it is not. The non-contacting stratum's own point
estimate even **reverses sign** (allosteric sites very slightly *less*
aromatic than active sites there), though at n=20 proteins (exact
sign-flip enumeration, not Monte Carlo) that reversal is itself far from
significant — reported because the task's own Constraint says state it,
not because it is a finding on its own.

**Read plainly, per this task's own pre-registered framing: this is a
clean negative, and it is the burial + ligand-contact / wrong-baseline
result the task predicted was most likely, not a narrower surviving
asymmetry.** The raw 15.6%-vs-12.8% gap that motivated the check is
consistent with active sites and allosteric sites both being more
aromatic than bulk protein (real, but not allostery-specific), amplified
further within the ligand-contacting stratum specifically, and gone once
compared to the right baseline with burial accounted for.

### Landed

New hypothesis **HYP-P29** in `physics.md` — a distinct claim from every
existing register hypothesis (none tests aromatic composition against a
within-protein active-site-matched, burial-and-ligand-contact-controlled
null). `TASK_CLASSIFICATION_LEDGER.md` + `INDEX.md` updated;
`hyp_register_check.py` re-run clean.

### Not done / explicitly out of scope, per this task's own Constraints

- No submission text — [[TASK-0373]]'s own scope, not this task's.
- No electronic-structure calculation of any kind — [[TASK-0374]]'s own
  scope.
- Did not re-litigate E1–E4 or any claim beyond E0's own aromatic-content
  question.

**Files**: `__WORK_IN_PROGRESS__/scripts/task0372_aromatic_enrichment_gate.py`,
`__WORK_IN_PROGRESS__/results/tasks/0372_aromatic_enrichment_gate/
{aromatic_enrichment_gate.json,rows.json,run_log.txt}`.
