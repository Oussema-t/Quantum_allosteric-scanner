# Q-0005 Does the conformational-selection reframing change how the reachability program should be sequenced?

## Context

- ID: Q-0005 (architect-planner addressee folder)
- Status: Open
- Addressee: Architect/Planner
- Raised By: Implementer B, 2026-08-22
- Related: [[TASK-0227]] (Done, real-target ANM mode-overlap ceiling),
  [[TASK-0230]] (Done, ANM ceiling + scorer-brittleness + energy-repack
  addenda), [[TASK-0228]] (In Progress, conformer-graph search
  branching/depth), [[TASK-0233]] (TODO, this question's own companion
  task), [[TASK-0168]] (Done, flagged population-shift as an out-of-scope
  "third mechanism"), `REFERENCES.md` [9] (Gunasekaran 2004, cited,
  UNTESTED).

## Question

Proposed by Bartosz this session (a "silly question" that turned out to
be the standard conformational-selection/population-shift model of
allostery, MWC 1965, vs. induced-fit): what if the drug isn't inducing a
new pocket at all, but selecting and stabilizing a pre-existing,
sparsely-populated conformer the protein already samples? This reframes
[[TASK-0230]]'s own central finding (energy minimization returns the
closed state, on KRAS_G12C, directly measured) from a negative result
into an *expected, uninformative-on-its-own* one — under this model,
minimization is supposed to find the dominant closed state; that was
never evidence against a rare open state existing.

Two questions above an implementer's own call:

1. **Does this change the priority/sequencing of [[TASK-0228]]'s own
   conformer-graph search framing** (branching factor vs. depth, `p`
   progress-probability) relative to [[TASK-0233]]'s proposed population/
   free-energy estimate? The two are not mutually exclusive, but
   [[TASK-0233]]'s calculation is cheap (reuses already-validated
   `allostery.superpose` machinery, no new tooling) and could cheaply
   rule the whole reachability question in or out per target *before*
   more search-based work is invested — is that worth resequencing for,
   or should both proceed independently?
2. **Is a third quantum-sampling angle (quantum Gibbs/Boltzmann sampling
   or a quantum walk over conformational microstates, biased toward the
   Boltzmann distribution) worth adding to the hypothesis register
   alongside QUBO-minimization (already argued mistyped, now directly
   confirmed by [[TASK-0230]] Addendum 2's own real-target data) and
   Montanaro backtracking search ([[TASK-0228]]'s own proposal)? It
   connects back to this program's existing CTQW investment more
   naturally than either alternative, but is unbuilt and uncosted —
   worth a hypothesis-family subtask (matching [[TASK-0229]]'s own
   pattern) or premature before [[TASK-0233]]'s own ΔG numbers exist?

## Background

[[TASK-0230]] Addendum 2 (2026-08-22): a lightly-relaxed KRAS_G12C
structure reads druggable (fpocket `druggability_score` 0.726) at clash
energy `vdwrep`=297; a genuinely energy-minimized one (EvoEF2
`SideChainRepack`, real simulated annealing) collapses to closed (0.004)
at almost the same clash level (285.7) — closure tracks which rotamers
get chosen, not overall relaxation. Direct, real-target confirmation of
the source document's own §6.1 diagnosis ("QUBO returns a minimum;
cryptic pockets are excited states... minimising energy over
backbone⊕rotamers returns the apo structure"). Did not replicate on
BCR_ABL1/CARDIAC_MYOSIN (both stay near-zero at every relaxation level,
consistent with — not contradicting — their own already-flagged weak-
holo-recognition caveat).

[[TASK-0227]] §5.1 (already-committed, real-target): static apo ANM-mode
cumulative overlap with the true apo→holo displacement is 0.58–0.90 on
all 3 real, valid target pairs — high enough that the "collective part
is reachable" reading was already established before this question was
raised. Under conformational selection, that overlap is itself evidence
the holo-like direction is part of the native thermal ensemble's own
low-mode fluctuations, not something requiring an artificial induced
push — a re-reading of an existing number, not a new measurement.

`REFERENCES.md` [9] (Gunasekaran, Ma & Nussinov 2004, "Is allostery an
intrinsic property of all dynamic proteins?") is the population-shift-is-
general paper, already cited (status UNTESTED — [[TASK-0229.001]] worked
out one consequence, negative-class validity for the register's AUC
framing, but not the mechanism question this raises). [[TASK-0168]]
explicitly named "a third mechanism (population shift between discrete
states)" as out of its own scope in 2026-08-04, deferred to [[TASK-0015]]'s
lineage — the same `allostery.superpose` cumulative-overlap machinery
[[TASK-0227]]/[[TASK-0230]] already extended. [[TASK-0233]] is the next
link in that already-flagged, previously-deferred chain, not a new idea
introduced from outside the project's own register.

Per-target mechanism grounding (KRAS/sotorasib traps the GDP-bound-like
inactive conformer, already cited via Ostrem 2013 [18]; BCR_ABL1/
asciminib mimics the kinase's own natural myristoylation-based
autoinhibition; CARDIAC_MYOSIN/mavacamten stabilizes the naturally
occurring "super-relaxed" autoinhibited state) is field-standard but its
specific citations were not DOI-verified when this question was raised —
flagged in [[TASK-0233]]'s own Open Questions, not asserted as validated.

## Answer

(not yet — Status: Open)

## Action

(fill in once answered — likely [[TASK-0233]] itself owns the
follow-through if the answer is "yes, worth building now")
