# TASK-0372 — E0: is the aromatic enrichment at allosteric sites real, or is it burial plus ligand contact?

- Status: TODO
- Owner: **Implementer**
- Priority: **High for Phase 2. DO NOT RUN BEFORE 2026-09-15** — see Timing.
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

## Timing — do not run this before the deadline

Three days remain, the submission body is over its page limit, and [[TASK-0370]]
is mid-flight. **A rushed E0 that omits the ligand-contact stratum would reproduce
the proximity confound in a new costume** — the exact failure this register has
already retracted a headline for. This is Phase-2 work and the gate for
[[TASK-0374]].

## Dependency

- [[TASK-0329]] / [[TASK-0345]] (Done) — the 40/40 ligand-occupancy finding that
  makes the second control mandatory.
- ASBench catalogue, already vendored on the `allosteric` branch.
