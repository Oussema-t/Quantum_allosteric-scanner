# Q-0005 Does the conformational-selection reframing change how the reachability program should be sequenced?

## Context

- ID: Q-0005 (architect-planner addressee folder)
- Status: Answered
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

**Answered by Architect, 2026-08-22.**

**Q1 — resequencing [[TASK-0228]] vs. [[TASK-0233]]: no resequencing needed,
and events have already settled it.** [[TASK-0228]] is, as of this answer,
substantively complete (604 lines, real branching/depth measurements landed
— the one remaining item is its own `RESULTS.md` addendum, blocked only on
that file's write-lock, not on any open question). It ran to completion
independently of this question, which is the right outcome, not a missed
opportunity: the two calculations are genuinely complementary, not
redundant, so there was never a real ordering constraint between them.
[[TASK-0233]]'s ΔG estimate answers *whether a rare open state plausibly
exists at all*; [[TASK-0228]]'s search framing answers *how hard finding it
is, given that a search must be run*. A cheap population estimate does not
make a search-cost measurement unnecessary — even a physically plausible
(few-kT) minor state still needs a search method to actually locate it
without the answer key, which is the question [[TASK-0228]] was built to
answer. Running both in parallel, as happened, was the correct call.

**What genuinely needs sequencing is not execution but *interpretation*.**
[[TASK-0233]]'s ΔG number gates how [[TASK-0228]]'s own per-target numbers
should be read, retroactively: on a target where the estimated population
turns out implausible (many kT), that target's branching/depth search
numbers describe the cost of finding something that may not physically be
there to find — informative about the search method in the abstract, not
about that target's own reachability. On a target where the population is
plausible (few kT), [[TASK-0228]]'s numbers become directly meaningful as a
reachability statement. **Action: when [[TASK-0233]]'s ΔG numbers land,
write one short cross-reference paragraph (in [[TASK-0233]]'s own Done
section, pointing at [[TASK-0228]]'s numbers per target) stating which
reading applies to which target — do not let the two results sit in
separate task files implying two independent conclusions when they are
actually one conclusion read through two lenses.**

**Q2 — a third quantum-sampling hypothesis-family subtask: premature, and
[[TASK-0233]]'s own filing already reached the same conclusion
independently.** Its own In Scope already commits to *naming and scoping*
the angle, explicitly not building or costing it — the right amount of
work before the physical question it depends on has an answer. Building a
full hypothesis-family subtask (matching [[TASK-0229]]'s pattern) now would
repeat exactly the failure mode [[TASK-0229]]'s own register was careful to
avoid elsewhere (an "unbuilt, uncosted, only *type-correct*" claim asserted
before the underlying physical quantity is known — see `REFERENCES.md`
ref [4]'s takeaway and [[TASK-0229.006]]'s own "do not claim advantage"
constraint, same shape of caution, reused here rather than re-derived): if
[[TASK-0233]]'s harmonic ΔG estimate comes back implausible (many kT) on
every target, there is no rare state for *any* sampling method — classical
or quantum — to find, and the hypothesis would be motivated by nothing.

**Graduation condition, stated so it does not have to be re-derived later**:
once [[TASK-0233]]'s calibrated (real-kT, per its own Open Questions'
Debye-Waller/equipartition fix) ΔG numbers exist, file the dedicated
hypothesis-family subtask **only** for target(s) where the estimate is
plausible (few kT) — scoped to those targets specifically, not filed
register-wide by default. If every target comes back implausible, record
that as the answer to this half of the question (a real, reportable
negative under conformational selection too — the state isn't just
hard to find, no method should expect to find it) and do not file the
subtask at all.

## Action

- [[TASK-0233]] proceeds as already scoped (Implementer B, claimed) — no
  change to its own Intent Contract from this answer.
- When [[TASK-0233]] reaches its own Done section: add the
  [[TASK-0228]]-cross-reference paragraph (Q1) and apply the graduation
  condition (Q2) — file [[TASK-0229]]-pattern hypothesis-family subtask(s)
  only for targets with a plausible ΔG, or record the register-wide
  negative if none clear it. Neither requires a new task to track; both are
  [[TASK-0233]]'s own closing steps, now explicit rather than implicit.

**Closed out, 2026-08-22.** [[TASK-0233]] Done: collective-layer ΔG
0.20–2.32 thermal units, `exp(−ΔG)`=0.10–0.82 on all 3 real targets — the
graduation bar (few kT) was met on every target, not a mixed result
needing per-target filtering. Q1's cross-reference paragraph written,
covering both where [[TASK-0228]]'s own `p`-measurement agrees
(collective layer, independent method, same "not rare" conclusion) and
where the two tasks' joint-layer findings diverge (read as search-method/
path-dependence, not a contradiction). Q2's graduation condition applied:
[[TASK-0234]] filed, scoped explicitly to the collective layer the
evidence supports, named and limits stated, not built or costed — matching
this answer's own caution against an "unbuilt, uncosted, only type-correct"
claim outrunning its physical grounding.
