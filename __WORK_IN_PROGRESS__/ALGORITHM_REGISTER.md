# Algorithm register — rated for the Cleveland Clinic challenge

**Rating scale (usability for THIS challenge, my judgment):**
5 = build now, core · 4 = build, high value · 3 = optional / situational ·
2 = demo or grounding only · 1 = skip (wrong tool here).

Ratings are about fit to *our* problem (topology-only, MD-free, apo→holo
allosteric-site prediction with a NISQ story), not the method's general quality.

---

## A. Conformational change / apo→holo morphing (characterization, holo known)

**Two-state ANM — Das, Gur, Cheng, Jo, Bahar, Roux 2014 (challenge ref [15]) — 5**
Mixes the apo and holo elastic networks to drive the transition. Already cited by
the challenge, simplest rigorous way to interpolate between known endpoints, and it
directly yields the contact make/break events our transport pipeline wants. Lowest-
effort, highest-alignment starting point for the morph.

**Normal Mode Flexible Fitting (NMFF) — Tama, Miyashita, Brooks 2004 — 5**
The exact iterative loop you sketched (pick best-overlap modes → small deform →
recompute → repeat), originally for cryo-EM fitting with holo standing in for the
density. This is *the* algorithm for the characterization morph. Recompute the
Hessian each step (the load-bearing detail) so the mode basis tracks the curving
path; drive on the global residual, not a local patch.

**Tama–Sanejouand cumulative overlap — 2001 — 5**
Not a morph but the diagnostic: how few low modes span Δr = holo−apo. This is the
Step-2 go/no-go gate and the single most informative number — it tells you per target
whether the holo direction is even reachable from apo. **Corrected 2026-07-18
(TASK-0130, superseding the "KRAS Switch-II likely fails" prediction above)**:
TASK-0120 actually ran this gate on real KRAS_G12C data and measured CO(20)=0.638 —
well above the 0.5 low-overlap bar — so KRAS_G12C's Switch-II pocket direction
classifies `LEARNABLE`, the opposite of this entry's original (unmeasured) guess.
Cheap, decisive, leakage-free.

**Plastic Network Model — Maragakis & Karplus 2005 (adenylate kinase) — 4**
Two-basin energy surface giving a physically meaningful path *with barrier/energetics*
— the thing RMSD-greedy morphing cannot give you. Use when you need to say whether the
transition is downhill or crosses a barrier. More setup than NMFF; add it only once the
geometric morph works.

**MinActionPath — Franklin, Koehl, Doniach, Delarue 2007 — 3**
Least-action trajectory between two ENM endpoints. Nice complement to PNM for path
energetics and ordering of events; optional, overlaps in purpose with PNM. Pick one of
the two for the energetics claim, not both.

**Morph Server / adiabatic NM interpolation — Krebs & Gerstein 2000 — 3**
The classic, quick apo→holo interpolation. Useful as a fast baseline/sanity morph to
check your own implementation against; older and less suited to large curvilinear
motions than iterative NMFF.

**RTB / block normal modes — Tama, Gadea, Marques, Sanejouand 2000 — 3**
**iMOD internal-coordinate NMA — López-Blanco, Garzón, Chacón 2011 — 3**
Needed only if a target's motion is a large *rotation* (helix swing), where Cartesian
ANM deformation stretches bonds. Situational: rate jumps to 4 on any target with big
rotational apo→holo change, otherwise skip.

**NMSim — Krüger, Ahmed, Gohlke 2012 — 3**
Rigidity-constrained + normal-mode geometric deformation; covers the rigidity/
connectivity angle. A ready-made alternative to rolling your own constrained scan;
optional, evaluate if the hand-built admissible-deformation scan proves fiddly.

---

## B. Linear response / perturbation direction (forward engine)

**Linear Response Theory — Ikeguchi, Ueno, Sato, Kidera,** *PRL* **94:078102 (2005) — 4**
Δr = C·f: apply a force, read the structural response via the covariance. The forward
engine for the blind holo-direction module and cheap (one linear solve). Solid, well-
cited; the inverse problem (which f opens the pocket) is the hard part, not this.
**[[TASK-0137]], 2026-07-22: third author corrected "Ota" -> "Sato"** (confirmed via
PubMed + 2 independent search sources) — real citation error, propagated from an
earlier filing, now fixed here and in `HOLO_DIRECTION_MODULE.md`. Paper's content not
independently verifiable (APS paywalled, no legitimate OA copy found) — attribution
only, not a content check.

**Perturbation Response Scanning — Atilgan & Atilgan,** *PLoS Comput Biol* **5(10):e1000544 (2009) — 4**
Scans perturbations site-by-site to map which sites propagate where. Directly useful
for choosing the source/injection set and for an apo-side allosteric-coupling readout.
Pairs naturally with LRT; classical and challenge-legal. **Verified [[TASK-0137]]**:
`documentation/references/Atilgan_Atilgan_PLoSCompBiol2009.md`.

---

## C. Network substrate (the graph itself)

**GNM — Bahar/Atilgan/Erman; Erman 2006 (ref [16]) — 5**
Your only empirically responsive family (source-conditioned propagation actually
varies). Core substrate; keep it central.

**ANM — Atilgan et al. 2001 — 4**
Needed for *directional* 3D modes (any deformation/morph requires ANM, not GNM). Caveat
from your own data: it can collapse to chain termini, so use with the integrity
constraints, not naively. Essential for Section A, hence 4.

---

## D. Transport / quantum readout (the core method + its honest quantum angle)

**CTQW (continuous-time quantum walk) — 5**
Your core propagator; maps cleanly to Trotterized Hamiltonian simulation, so it carries
the hardware story. Keep, but calibrate propagation time physically (mode timescales),
not by sweeping.

**ENAQT / dephasing-assisted transport (Haken–Strobl QSW) — Plenio & Huelga 2008;
Rebentrost, Mohseni, Lloyd, Aspuru-Guzik 2009 — 5**
The rigorous form of "vibrations open hidden edges": coherent walks localize on
disordered graphs, calibrated dephasing reopens blocked paths. This is your strongest
quantum-relevance argument *and* your best NISQ angle (device noise as a feature).
Calibrate γ from vibrational timescales.

**Non-reciprocal / chiral-phase walk (Peierls phases / non-Hermitian H) — 3**
Encodes signal *direction* (active→allosteric), which a symmetric Laplacian cannot.
Worth a secondary experiment; not core, and easy to over-claim. Useful mainly to show
directionality is representable.

**QSVT / QSP for f(H) — Gilyén, Su, Low, Wiebe 2019; ties to Oh et al. 2024 (ref [11]) — 3**
Principled spectral filtering (slow-mode band, resolvent/Green's function) with a real
hardware mapping and a link to a challenge reference. Advanced; high upside for the
methodology report, real implementation cost. Phase-2 ambition.

**HHL linear solve — Harrow, Hassidim, Lloyd 2009 — 1**
Quantum form of Δr = H⁻¹f. Pointless at N of a few hundred (state-prep/readout
overheads dominate; no advantage). Don't dress the forward solve as quantum.

---

## E. Inverse-problem optimization (find the pocket-opening perturbation)

**Classical basin-hopping / CMA-ES in mode-amplitude space — 4**
The actual workhorse for "which admissible deformation opens the cavity." Cheap exactly
because your coarse-graining makes the search low-dimensional. This produces the result;
treat it as primary.

**QUBO + QAOA / quantum annealing ("quantum folding") — Robert, Barkoutsos, Woerner,
Tavernelli 2021; Perdomo-Ortiz et al. 2012 — 3**
Discretize mode amplitudes → Ising → QPU. Legitimate as a *second* NISQ demo and it
strengthens the hardware narrative, but no demonstrated advantage and the classical
baseline above is strong. Demo, not result.

---

## F. Cryptic-pocket / external baselines (cross-check + objective)

**fpocket — Le Guilloux, Schmidtke, Tuffery 2009 — 4 — RUN [[TASK-0163]]**
Apo-computable cavity-openness score — the legal objective for the perturbation
optimizer and a standalone baseline. Fast, no force field. Use as the openness term.
**Run against all 3 mandatory targets' apo structures (2026-07-27/28), built from
source (`__WORK_IN_PROGRESS__/tools/fpocket/`, no root/apt needed, static-linked
against system libm/libstdc++/libc only). Per-pocket "Score" (openness, not
druggability) assigned per residue via pocket atom-membership files, scored against
this project's own holo pocket labels: AUC 0.8348/0.8596/0.5345 (KRAS_G12C/
BCR_ABL1/CARDIAC_MYOSIN) vs. this project's own floor 0.4818/0.5817/0.5679 and own
best observable (`H_new`/CTQW) 0.5901/0.5266/0.5176. Decisively beats both the
floor and this project's own headline observable on 2/3 targets (KRAS_G12C,
BCR_ABL1) by a wide margin — a purely geometric, non-dynamical classical tool
outperforms the quantum-walk observable there. On CARDIAC_MYOSIN it sits just
below its own floor. Full detail: `RESULTS.md`'s TASK-0163 section.**

**PocketMiner (GNN) — Meller, Ward, … Bowman 2023 — 4 — RUN [[TASK-0163]]**
State-of-the-art cryptic-pocket-*location* prediction from a single structure, no MD.
Best external baseline/cross-check: if it hits where you miss, your problem is the
operator; if it also misses, it corroborates "pocket absent from apo." Diagnostic.
**Web server (`pocket-miner-ui.azurewebsites.net`) confirmed DNS-dead (two
independent tools). Run locally instead, in a separate isolated repo
(`/home/bchmura/PROJECTS/PocketMiner/`, not this repo -- the pinned
`tensorflow==2.6.2` stack only ships wheels for Python ≤3.9, incompatible with
this project's own Python 3.12 environment) via a from-source Python 3.9.18 build.
Scored against this project's own holo pocket labels: AUC 0.6932/0.5603/0.5732
(KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN) vs. the same floor/actual numbers fpocket's
entry above cites. Beats this project's own `H_new`/CTQW on KRAS_G12C and
CARDIAC_MYOSIN, narrowly clears its own floor on CARDIAC_MYOSIN (+0.0053), falls
short of both on BCR_ABL1. Full detail: `RESULTS.md`'s TASK-0163 section.**

**ProteinLens / bond-to-bond propensity — Amor, Schaub, Yaliraki, Barahona 2016 — 4 — BLOCKED [[TASK-0163]]**
Published allosteric-site predictor (classical current-flow on an atomistic graph) with
a web server. External diagnostic + source of the distance-bias quantile-correction and
current-flow pathway ideas. Adopt the readout, not the all-atom graph.
**Web server confirmed live and reachable, no login/account required -- but
browser-only interactive UI with no discovered API/batch endpoint, so it cannot be
run unattended the way fpocket/PocketMiner were. Not run in TASK-0163's pass;
explicit blocker per that task's own Intent Contract ("state access-method
blockers explicitly, do not silently skip"), not a silent omission. Manual-run
instructions can be produced on request if a human is available to drive the
browser session per target.**

**AlloPred / PASSer / DeepAllo — 3**
Additional external server baselines for the comparison table. Cheap to run, good for
reviewer-legible breadth; lower priority than the three above.

---

## G. Conceptual grounding (probably not building)

**String method / NEB / transition-path theory — E & Vanden-Eijnden; Jónsson, Mills,
Jacobsen 1998 — 2**
Justifies "path waypoints need not be occupiable equilibrium states." Useful framing for
the report; full implementation is out of scope given MD constraints. Cite, don't build.

---

## H. NISQ deliverable (where the secondary-objective points are)

**Trotterized Hamiltonian simulation of e^{-iHt} under a noise model — 5**
Coarse-grain to N ≤ ~12–16 qubits, run CTQW/ENAQT under depolarizing + amplitude-damping
with realistic 2-qubit error rates, report top-5 ranking degradation vs depth and error.
The actual scoreable NISQ result; the key finding to look for is whether ENAQT/QSW is
*more* noise-robust than coherent CTQW.

---

## One-line build order
Gate first (Tama–Sanejouand overlap, 5) → morph (two-state ANM + NMFF, 5/5) → substrate
(GNM core, ANM for modes, 5/4) → transport (CTQW + ENAQT, 5/5) → openness objective +
classical optimizer (fpocket + CMA-ES, 4/4) → external cross-check (PocketMiner,
ProteinLens, 4/4) → NISQ noise study (5). Everything rated ≤3 is optional and added only
if a specific target or the methodology report demands it.
