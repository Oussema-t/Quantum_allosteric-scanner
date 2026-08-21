# Search & Complexity Hypotheses

**Scope:** conjectures about the *computational* character of cryptic-pocket
prediction — what is hard, what is easy, and where a quantum formulation
could even in principle matter. Companion to `physics.md` (claims about the
protein physics) and `ceiling.md` (strategic framing). These are testable
claims, not implementation tasks; each names the task that owns it.

**Origin:** discussion between the orchestrating user and the Reviewer thread
(Opus), 2026-08-05/06, following [[TASK-0204]]'s reopening. Condensed here so
the reasoning survives the conversation.

---

## Where the register actually stands (the one-screen version)

Every route closed so far closed for the same reason: **the problem turned
out not to be hard.** Each closure has a boundary, and the boundaries all
point at the same gap.

| Closed route | Why it closed | Boundary it left |
|---|---|---|
| Single-particle CTQW / all 28 observables | `eigh` at N≤704; effective rank ~3 ([[TASK-0199]]) | single particle, **single static graph** |
| Coherence / interference / non-locality | flat γ-sweeps; converged limit phase-free; no entanglement in a 1-particle space | — |
| Interacting multi-particle | ρ≈0.88–0.90 vs 1-particle even at U=12; confound *worsens* | — |
| Backbone-only ENM search | pocket recovery in 1–8 draws, not rare ([[TASK-0185]]) | **side chains unmodelled** |
| Residue-selection QUBO (Phase A) | 0/3 targets ([[TASK-0181]]) | — |
| Optimal control (GRAPE) | chance on 3/3 ([[TASK-0156]]) | — |
| Fixed-backbone rotamer packing (Phase B) | treewidth 2–5; exact optimum in **0.001–0.159 s** vs naive 1e14.1 ([[TASK-0204]]) | **interaction graph is fixed** |

**The gap:** coupled backbone + side-chain search, on a non-decomposable
objective, over an ensemble rather than one structure. That is where every
hypothesis below lives.

**The one surviving positive:** PTP1B `dcc_low` k=10, p=0.0027 vs bar
0.003125, CI [0.0020, 0.0035] ([[TASK-0201]]) — under a null built
specifically because the previous one structurally could not reach real
pocket geometry. Its mechanism is unreplicated ([[TASK-0168]]: `dcc_low`'s
signature holds on KRAS_G12C, fails on BCR_ABL1, PTP1B untested).

---

## HYP-S1 · The treewidth closure is objective-dependent, and a black-box detector breaks it

**Claim.** [[TASK-0204]]'s closure holds because the objective is a
**pairwise-decomposable** packing energy — that is what makes the problem a
Markov random field and lets bucket elimination run in `O(m·n^(tw+1))`. The
moment the objective is *"find any conformation where fpocket fires"*, no
decomposition exists: fpocket's druggability is a black-box function of the
whole structure, not a sum of pairwise residue terms. **Exact inference is
then unavailable and the closure does not transfer.**

**Why it matters.** This is the strongest formal hardness argument the
register has ever had, and it was closed too fast. It is also the precise
statement of the orchestrating user's observation that *apo→holo with known
holo may be laptop-solvable while apo→? with unknown holo is a different
problem*: with a known target the search is guided and decomposable; with a
black-box oracle it is neither.

**Counter-evidence, and it is serious.** [[TASK-0185]] measured pocket
recovery under ENM sampling at **1–8 draws per hit** — a black-box oracle did
not make the *instances* hard, because random sampling finds them. So the
formal argument restores hardness while the empirical result denies it, at
the backbone layer.

**The open question this leaves** (and it is [[TASK-0210]]'s): does rarity
return in the *coupled* backbone+rotamer space, which is vastly larger than
the ENM mode space [[TASK-0185]] sampled? Formal non-decomposability plus
empirical rarity would be a real result. Formal non-decomposability with
recovery still at 1–8 draws is another closure.

**Status:** open. Owner [[TASK-0210]]. Do not cite the formal half without
the empirical half — alone it is the kind of argument this register exists to
refuse.

---

## HYP-S2 · The "noodle wiggle" — steric infeasibility is a *coupling detector*, not a cost function

**Claim (orchestrating user, 2026-08-06).** Walk the backbone from structure
A toward B by dihedral moves, and use **steric clashes** — not energy — as
the signal. When changing torsion α creates a clash that only some set β can
resolve, you have *directly observed* that α is coupled to β. Structures need
only be physically admissible, not low-energy.

**Why this is a strong idea.** It reformulates the problem as **constraint
satisfaction** rather than optimization, and that changes three things at
once:

1. **Coupling becomes explicit and measurable** — it is read off the
   constraint graph rather than inferred from an energy difference. This is
   exactly the quantity [[TASK-0208]] wants and that RMSD structurally cannot
   see (see HYP-S3).
2. **CSP hardness is well-characterized** — phase transitions at critical
   constraint density. Sparse constraints → greedy works. Dense → hard.
   Protein cores are dense. So "is this hard" becomes a measurable question
   with existing theory behind it, not a guess.
3. **CSP encodes naturally as QUBO** (constraints → penalty terms), so a
   positive result would arrive with its quantum formulation already implied
   rather than bolted on.

It is also a rediscovery of a real method class, which is a good sign, not a
bad one: robotics-derived loop closure, cyclic coordinate descent, concerted
rotations (Dodd et al.), backrub moves (Davis/Baker), polymer "wriggling"
move sets. **Any implementation should start from that literature, not from
scratch** — same "port, don't reinvent" convention the register applies to
physics.

**The trap that must be designed around — and it is fatal if missed.** In a
serial chain, changing φ at residue *i* rigidly displaces **everything
downstream**. Under a naive parameterization every torsion is therefore
"coupled" to every later residue, the coupling graph is trivially dense, and
the measurement is a property of the coordinate system rather than of the
protein. This is the same class of error as the seed/clock/potential-scale
gauge contamination Phase 1C spent weeks unwinding.

**The fix is what real methods already do**: use *local, chain-closing* moves
(concerted rotations, backrub) that change several torsions together so the
chain beyond the window is unmoved. Only then is observed coupling genuine.
**A wiggle implementation without local closure will produce a confident,
meaningless answer.**

**Is it "cheap protein folding"?** Partly, and the qualifier matters: fixed
topology, feasibility instead of an energy landscape, and (in the A→B case)
known endpoints. That is three simplifications away from folding — real, but
not the same problem, and the write-up must not blur them.

**Status:** open, unowned. Candidate instrument for [[TASK-0208]]'s coupling
measurement and [[TASK-0210]]'s search formulation. Not filed as a task
pending the [[TASK-0208]] gate result — if the apo→holo change is
side-chain-dominant, this is not needed.

---

## HYP-S3 · Overlap measures magnitude; hardness is set by coupling; they are orthogonal

**Claim.** Structural overlap (RMSD, contact-graph Jaccard, displacement)
answers *how much* changed. Search difficulty is set by *whether the changes
are separable*. Two structures can differ greatly through many independent,
individually-favourable changes — greedy finds it, easy at any magnitude — or
differ slightly through a few frustrated changes that only pay off jointly —
hard. **No overlap measure can distinguish these.**

**What overlap *can* do, rigorously.** Side-chain rotamer changes cannot move
Cα (Cα positions are fixed by backbone geometry). So:

- pocket-local Cα displacement > noise **⟹** backbone change, necessarily
- pocket-local Cα displacement ≈ 0 with large heavy-atom displacement **⟹**
  side-chain-only, necessarily

An implication in both directions — so the backbone/side-chain **split** is
cheaply and rigorously answerable by overlap. Only **coupling** is not.

**Mandatory caveat:** must be pocket-local. Global Cα RMSD averages a hinge
away; a single φ/ψ flip can rearrange a pocket while barely moving a
300-residue RMSD. [[TASK-0169]] already bit the register this way.

**Status:** established by construction, not yet used. Offered to
[[TASK-0208]] as amendments A1/A2 via
`.ai/memory/questions/implementer/open/Q-0001-*`.

---

## HYP-S4 · Endpoint coupling ≠ path coupling

**Claim (orchestrating user).** *"Just the possibility of near-zero coupling
in a pair of apo-holo structures does not mean that the coupling is near zero
all the way between them."* Correct, and it bounds what [[TASK-0208]] can
conclude.

[[TASK-0208]]'s frustration statistic compares single-residue against joint
ΔE of swapping to the holo conformation — an **endpoint** measure. Two
structures can be trivially interconvertible in the sum-of-changes sense
while **every path between them passes through a coupled bottleneck**. A
low endpoint-frustration reading is therefore evidence of *decomposability at
the endpoints*, not of an easy transition.

**Consequence, and it costs nothing:** [[TASK-0208]] should *state* this
limitation whether or not it measures it. A "low coupling" verdict that gets
read as "easy transition" would be a wrong closure of the whole direction —
and closures in this register are load-bearing.

**Status:** open. Limitation of [[TASK-0208]]; measurement would need
HYP-S2's machinery.

---

## HYP-S5 · Instance enrichment — 4–7 targets is an anecdote, but each target contains many transitions

**Claim (orchestrating user).** The n-problem ("one or two targets per class
is not a classification") is fixable without new targets: generate many A→B
pairs *per target* from rotamer variants and **non-equilibrium** ENM
structures. That converts 4–7 targets into a distribution of transition
instances, over which coupling can actually be measured as a distribution
rather than a handful of point estimates.

**Why it is more than a sample-size trick.** It also answers *where along the
apo→holo coordinate coupling becomes important* — the natural companion to
HYP-S4. Endpoint pairs give one reading; a family of intermediate pairs gives
the profile.

**Caveats.** (a) Enriched instances are synthetic and must be labelled as
such — a control, never a benchmark ([[TASK-0209]]'s standing rule). (b)
Non-equilibrium ENM structures are still trajectory-free and legal under
§Constraint 3 (see HYP-S7), but "non-equilibrium" needs a stated definition
or it becomes an unreported knob. (c) Instances drawn from one fold are not
independent samples; the effective n is smaller than the count.

**Status:** open, unowned. Natural extension of [[TASK-0208]]/[[TASK-0209]].

---

## HYP-S6 · Coupling is protein-dependent, and an apo-only observable may predict it

**Claim.** Coupling will vary by target — some backbone-driven, some
side-chain-driven, some genuinely coupled. **This is the better outcome, not
a complication**, because each regime routes to an existing closure and the
split itself becomes a screening criterion:

| Regime | Applies | Verdict |
|---|---|---|
| backbone-only | [[TASK-0185]]: 1–8 draws | easy, already closed |
| side-chain-only | [[TASK-0204]]: exact in ms | easy, already closed |
| **coupled** | neither — graph becomes variable | **open** |

A method that says *a priori* "these 2 of 7 targets are in the regime where a
quantum approach could even in principle matter" is a contribution in the
same shape as [[TASK-0169]] — characterization, which is what this program is
demonstrably good at.

**The predictive half (this is the interesting part).** A screen requiring
holo is useless for prediction. So: does an **apo-only** observable predict
coupling? Directional hypothesis, to be fixed before measurement:

> frustration rank across targets correlates with apo-only
> correlation-observable rank (`dcc_low`, mode co-participation,
> conformational entropy), and **PTP1B is highest on both**.

If it fires, `dcc_low` is plausibly *detecting coupling* — which gives the
register's only surviving positive ([[TASK-0201]]) a mechanism, and gives an
apo-only screen for the hard regime. Both quantities are already computed;
the correlation is free.

**Honest weakness, stated up front:** n=4–7 makes any rank correlation thin,
and it hangs on the frustration statistic being stable enough to *rank*
rather than merely to separate. **Measure that statistic's own
reproducibility first** (split the window, resample) or this is one noisy
rank against another.

**Status:** open. Offered to [[TASK-0208]] as amendment A3 (Q-0001). The
n-problem is why it is a hypothesis and not a plan.

---

## HYP-S7 · Conformational sampling is legal; only MD trajectories are forbidden

**Claim — settled, recorded because the Reviewer thread got it wrong once.**
§Constraint 3 forbids *"classical MD trajectories as inputs"*. It does **not**
forbid conformational sampling. Established by [[TASK-0185]], whose
closed-form ANM equipartition Gaussian draws (amplitude ~ N(0, √(kT/λ)), no
integrator, no trajectory) are the working precedent, and reinforced by the
challenge's own reference [1] (Zheng 2023) being a conformational-sampling
method.

**Consequence.** Trajectory-free structure search — including coupled
backbone+side-chain search over (φ, ψ, χ), and HYP-S2's wiggle — is legal.
The Reviewer thread's earlier statement that "the no-MD constraint forbids
it" was **wrong** and is retracted here.

**Status:** settled. Cite this before any reviewer asks.

---

## Standing constraint on every hypothesis above

**Classically hard ≠ quantum-solvable.** NP-hardness licenses *trying* a
QAOA/annealing formulation; it never licenses a speedup claim, and QAOA has
no general performance guarantee on any NP-hard instance class. This is Phase
B's own criterion #2 and it binds everything here.

The defensible Phase-2 proposal is: **a well-posed, verifiably hard,
biologically meaningful instance class, with a known-answer benchmark, a
stated quantum formulation, and pre-registered falsification criteria.** Not
a claim of advantage. That is a stronger submission, and every part of it is
checkable by a referee.

---

## Open threads carried from elsewhere, in one place

| Thread | State | Owner |
|---|---|---|
| PTP1B `dcc_low` positive vs. its unreplicated mechanism | conditional analysis inconclusive on PTP1B (fpocket only AUC 0.42 there); plant grid partial | [[TASK-0203]] |
| Effective rank ~3 — is it a property of the method class or only of *single-graph* methods? | untested; ensemble observable would decide | [[TASK-0211]] |
| BCR_ABL1 `1OPL` contains `MYR` in the myristoyl pocket — apo is pre-opened | verified directly; target invalid for pocket-opening work | [[TASK-0209]] |
| KRAS_G12C is a validated known-answer instance (apo drug 0.001 → holo 0.886) | measured 2026-08-06 | [[TASK-0209]] |
| Phase B closed on complexity grounds at pocket scale; hard regime exists only at m≈50–80 | measured + exact-solve validated | [[TASK-0204]] |
| PC1/PC2 stable across targets, **PC3 is not** | weakens the clean "three axes" framing | [[TASK-0207]] |

---

## External reference-hypothesis register (2026-08-21 drop)

`.ai/reviews/2026-08-21/REFERENCE_HYPOTHESIS_REGISTER.md` extracts hypotheses
from the challenge's own references [1]–[25], tiered by threat and value, with
tested-status per item. It is the first systematic pass over the organisers'
bibliography and it names several untested items that bear directly on the
submission:

- **[1] Zheng** — NMA-guided conformational sampling, MD-free. Reference
  *number one* in the challenge's own list, the canonical method for this
  program's own reframing, and **never implemented as a baseline.**
- **[1]+[2] stitched** — NMA sampling → persistent homology → pocket ranking.
  Zero MD, both halves from the organisers' bibliography. Would revive the H₂
  arm, which [[TASK-0143]]'s 0/7 did not kill (bad proxy, per the drop).
- **[9] Gunasekaran** — attacks the negative class of every AUC in the
  register. Mandatory in limitations whether or not it is tested.
- **[15] two-state ANM** — the principled instrument to *quantify*
  [[TASK-0209]]'s 2/7 rather than assert it.
- **[11] Oh SVD dilation** — the missing hardware story for ENAQT.
- **[10] circuit cutting** — discharges the coarse-graining half of objective
  §4.2 on paper.

Owned by [[TASK-0226]] / [[TASK-0227]] / [[TASK-0228]] where testable.
