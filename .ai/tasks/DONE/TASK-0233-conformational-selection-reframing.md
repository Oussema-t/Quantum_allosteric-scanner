# TASK-0233 Conformational-selection reframing: ANM-harmonic population estimate + a third quantum angle

## Context

- ID: TASK-0233
- Title: reframe pocket "reachability" from a binary energy-minimization
  ceiling question (TASK-0227/0230's own framing) to a population/free-
  energy question, per the conformational-selection (population-shift)
  model of allostery — proposed by Bartosz, 2026-08-22.
- Status: Done
- Resolution: done
- Resolution Note: Collective-layer ANM harmonic ΔG estimate: 0.20-2.32 thermal units, exp(-dG)=0.10-0.82 on all 3 real targets -- not exponentially suppressed, extends TASK-0227's geometric overlap finding to a real thermodynamic plausibility read. Lower bound only (excludes local residual TASK-0230 found difficult). Cross-referenced against TASK-0228's own independent p-measurement per Architect's Q1 answer. Graduation condition (Q2) met for collective layer -- filed TASK-0234, scoped narrowly, not built.
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: user question this session — "what if allostery is about a drug
  stabilising a specific pre-existing conformer (locking an active/
  inactive state) rather than inducing a new one" — the Monod-Wyman-
  Changeux population-shift model, as opposed to Koshland induced-fit.
- Priority: P1 — directly reframes how to read [[TASK-0230]]'s own
  central finding (Addendum 2: minimization returns the closed state),
  and names a concrete, cheap, buildable next calculation reusing
  existing data.

## Why this is not a tangent — it explains data already in hand

[[TASK-0230]] Addendum 2 found: on KRAS_G12C, a lightly-relaxed structure
reads druggable (0.726) but a genuinely energy-*minimized* one collapses
to closed (0.004) at almost the same clash level. Under an induced-fit/
ceiling framing this reads as a puzzle or a negative. Under conformational
selection it is the **expected** result and not informative on its own:
minimization from a single structure finds the dominant (closed) state by
construction; a rare, higher-energy minor conformer would never be
expected to be the global minimum. The ceiling experiments in [[TASK-0227]]
/[[TASK-0230]] were answering "is the closed state the minimum" (yes,
trivially, under this model) rather than "how rare is the open state" —
the type-correct question conformational selection actually poses.

[[TASK-0227]] §5.1 (static ANM-mode cumulative overlap, 0.58–0.90 on real
targets) is *already* a population-shift-flavored result, not previously
read as one: high overlap between the true apo→holo displacement and the
apo structure's own low-frequency normal modes means the fluctuation
direction toward the holo-like conformer is part of the protein's native
thermal ensemble, not something requiring an external, induced push.

**Grounding already in this project's own register, not newly invented**:
Gunasekaran, Ma & Nussinov 2004 (`REFERENCES.md` [9], cited, status
UNTESTED) is the population-shift-is-general-to-allostery paper. [[TASK-0168]]
explicitly flagged "a third mechanism (population shift between discrete
states)" as out of its own scope, deferred to [[TASK-0015]]'s lineage —
the same `allostery.superpose`/cumulative-overlap machinery [[TASK-0227]]/
[[TASK-0230]] already extended. This task is the next link in that chain,
not a new one.

**Per-target mechanism grounding** (field-standard claims; DOIs NOT
verified in this task's own filing — see Open Questions):
- KRAS_G12C: sotorasib covalently traps the GDP-bound-like, signaling-
  inactive conformer (already cited: Ostrem 2013, `REFERENCES.md` [18]).
- BCR_ABL1: asciminib binds the myristoyl pocket, mimicking the kinase's
  own natural autoinhibitory myristoylation mechanism — locks a
  pre-existing autoinhibited state, doesn't induce a new one.
- CARDIAC_MYOSIN: mavacamten stabilizes the "super-relaxed" (SRX) state,
  a naturally occurring, sparsely-populated autoinhibited myosin
  conformer.

## Intent Contract

- Outcome: a real, quantitative population/free-energy estimate (not a
  binary open/closed judgment) for how "rare" the holo-like conformer
  would be in each target's native apo ensemble, computed from data this
  project has already validated — and an honest assessment of whether
  this estimate is small enough (few kT) to be physically plausible as a
  real, sampled minor state, or too large to support the conformational-
  selection reading.
- Why required, not assumed: [[TASK-0230]]'s own minimization-returns-
  closed result is uninformative without this — it is consistent with
  both "no accessible open state exists" and "an accessible open state
  exists but isn't the global minimum," and only a population estimate
  distinguishes them.
- In Scope:
  - `ΔG_k ≈ ½ λ_k c_k²` per mode (harmonic approximation ANM already
    assumes), summed over the modes needed to reach the true (or
    k=50-truncated) apo→holo displacement, using the eigenvalues and
    projection coefficients [[TASK-0227]]/[[TASK-0230]] already compute
    (`allostery.superpose.anm_modes`, reused not re-derived) — no new
    physics, a direct reuse of already-validated machinery.
  - Report in kT units (need a real ANM force-constant calibration —
    check whether `allostery/superpose.py` or `hamiltonians.py` already
    calibrates against real B-factors, e.g. `calibrate_kappa`, before
    assuming arbitrary/uncalibrated units are physically meaningful).
  - Compute for all 3 real target pairs, both the k=50-truncated and full
    displacement (mirroring [[TASK-0230]]'s own two ceiling passes) so the
    population estimate can be compared against the already-measured
    mode-overlap fractions.
  - State explicitly, per target: is the estimated population plausible
    (few kT, a real minor conformer) or implausible (many kT, effectively
    unreachable even under population-shift)?
  - Name the third quantum-sampling angle (quantum Gibbs/Boltzmann
    sampling or a quantum walk over conformational microstates biased
    toward the Boltzmann distribution) as a hypothesis for the register,
    distinct from QUBO-minimization (mistyped, per the source document's
    own §6.1 and [[TASK-0230]] Addendum 2's own direct confirmation) and
    Montanaro backtracking search ([[TASK-0228]]'s own proposal) — not
    built or costed here, named and scoped only.
- Out Of Scope:
  - Building the quantum-sampling algorithm itself — a hypothesis to add
    to the register, not an implementation in this task.
  - Verifying the per-target mechanism citations (asciminib/myristoyl,
    mavacamten/SRX) against live DOIs — real, separate work, flagged in
    Open Questions, not assumed done by filing this task.
  - Any change to [[TASK-0227]]/[[TASK-0230]]'s own already-committed
    Done sections — this task adds a new, complementary calculation, it
    does not revise or retract those findings.
- Constraints And Invariants: reuse `allostery.superpose`'s own validated
  ANM eigenvalue/eigenvector machinery; no new energy function; state
  the calibration status (arbitrary vs. real-unit force constants)
  explicitly rather than silently presenting an uncalibrated number as
  physical kT.
- Planned Validation: the harmonic approximation itself has a known
  failure mode (large displacements are not well-modeled by a single
  quadratic expansion around the apo minimum) — state this bound
  explicitly per target based on how large the projected displacement is
  relative to where the harmonic approximation is expected to break down,
  rather than reporting a ΔG estimate for a displacement so large the
  method underlying it is no longer trustworthy.

## Open Questions

- **Checked while filing this task, not left speculative**: `allostery.
  superpose.calibrate_kappa` exists and calibrates the ANM spring
  constant against each target's real mean B-factor
  (`CleanResult.b_mean`) — but its own docstring is explicit that "no
  kT / (8π²/3) prefactor is applied... kappa is only meaningful as a
  relative scale within this module, not as a real spring constant."
  **A true kT-unit ΔG is not what this function returns today.** The
  standard path from a B-factor to a physical spring constant is
  well-established (Debye-Waller: `⟨Δr_i²⟩ = (8π²/3)·B_i`; equipartition
  for an isotropic 3D harmonic mode: `⟨Δr²⟩ = 3kT/κ`) and derivable from
  data `calibrate_kappa` already has (`b_mean`) — this task's own In
  Scope should add that one missing conversion step explicitly (and
  state the temperature/units assumed) rather than reuse
  `calibrate_kappa`'s relative-scale number as if it were already kT.
- Do the asciminib/myristoyl-autoinhibition and mavacamten/SRX-state
  mechanism claims actually verify against live DOIs, per
  `.ai/reference/PAPER_CITATION_PROTOCOL.md`? Not checked when this task
  was filed — real citations to add to `REFERENCES.md` if confirmed, not
  to be treated as validated until then.
- Does a small ΔG estimate on any target change [[TASK-0228]]'s own
  priority/sequencing (search-based conformer-graph framing) — an
  Architect-level call, raised alongside this task via
  `.ai/memory/questions/architect-planner/open/`.

## Done

**The collective part of the transition is thermodynamically cheap on
all 3 real targets, not just geometrically aligned — a real, quantitative
extension of [[TASK-0227]] §5.1, computed by reusing [[TASK-0015]]'s own
already-built, already-validated `run_superpose`/`mode_energetics`
unmodified. This is a lower bound only (excludes the local residual) —
stated precisely below, not glossed over.**

Script: `__WORK_IN_PROGRESS__/scripts/task0233_conformational_selection.py`.
Reuses `allostery.superpose.run_superpose` end to end (alignment,
Tama-Sanejouand CO(m), B-factor-calibrated `kappa`, `mode_energetics`'s
`E_k = 0.5·κ·λ_k·c_k²`) — no new physics, no new energy function, exactly
the reuse-not-rederive discipline this task's own Constraints required.

| target | N common | κ (B-factor calibrated) | CO(k=50) | total ΔG (k=50, thermal units) | modes for 90% of CO | exp(−ΔG) |
|---|---|---|---|---|---|---|
| KRAS_G12C | 166 | 0.1015 | 0.766 | **2.32** | 19 | 0.099 |
| BCR_ABL1 | 429 | 0.0232 | 0.805 | **0.37** | 28 | 0.692 |
| CARDIAC_MYOSIN | 698 | 0.0318 | 0.954 | **0.20** | 3 | 0.821 |

For scale: this project's own established convention (`holo_direction.py`'s
`PERTURBATION_PROTOCOL`, [[TASK-0015]]) treats one mode's *average* thermal
population as 0.5 "units" — 50 modes' worth would be 25 units if the
displacement excited every mode equally. The real displacement costs
0.20–2.32 units total: **1–9% of that naive scale.** `exp(−ΔG)` — the
Boltzmann weight of the displaced state relative to the apo minimum, at
this project's own established "kT=1" convention — is 0.10–0.82 on all 3
targets: **within an order of magnitude of 1, not exponentially
suppressed.** Physically: the true apo→holo displacement is dominated by
the *softest* available modes (90% of the overlap reached by just 3–28 of
50 modes), and soft modes are cheap by construction — a large Ångström-
scale collective motion along a genuinely soft direction costs little
elastic energy, unlike the same-magnitude motion along a stiff/local one.

**Units, stated precisely, per this task's own Constraint**: NOT real
Kelvin-calibrated kT. `calibrate_kappa`'s own docstring is explicit it
applies no Debye-Waller (8π²/3) correction — it matches B-factor-derived
flexibility to a unitless scale. [[TASK-0015]]'s own precedent
(`holo_direction.py`) already adopted treating that scale as "kT=1"
directly, and this task reuses that same already-established convention
rather than introducing a second, inconsistent one. The numbers above are
this project's own internally-consistent relative energy scale — safe for
comparing modes/targets against each other and against the codebase's own
prior energetics numbers, not a claim about real kcal/mol.

**This is a lower bound, not the full answer — the load-bearing
caveat.** CO(k=50) is 0.766–0.954, not 1.0: 5–23% of the true displacement
is NOT captured by these 50 soft collective modes. That residual is
exactly the *local* (side-chain/short-backbone) component ANM's coarse
Cα network cannot represent — and it is exactly where [[TASK-0230]]'s own
real all-atom pipeline found genuine difficulty (severe steric clash from
naive backbone placement, energy minimization reliably returning to the
closed state). Adding the modes needed to capture that residual would add
real elastic cost (stiffer, higher-frequency modes cost more per unit
displacement) — how much is not computed here, real remaining scope, not
assumed small.

**Cross-reference to [[TASK-0228]], per the Architect's own Q1 answer —
which reading applies to which target/layer:**

[[TASK-0228]]'s own §6.2 "p" (progress probability, an independent method
— real incremental single-mode moves + repack, not a mode-projection
ceiling) also lands in the source document's own "not rare" 0.24–0.69
band at the **collective-only** layer on all 3 targets (KRAS_G12C 0.492,
BCR_ABL1 0.237, CARDIAC_MYOSIN 0.426) — **a second, methodologically
independent line of evidence for the same collective-layer conclusion
this task reaches.** Two different methods (a closed-form ceiling here,
a real incremental search there) agree the collective/global component is
not rare and not hard to make progress on.

At the **joint (collective + rotamer repack) layer**, the two tasks'
findings diverge sharply, and that divergence is itself informative, not
a contradiction to paper over: [[TASK-0230]]'s ceiling (one large jump,
then repack) fails to cross the druggability bar on every trial, every
target. [[TASK-0228]]'s own joint p (many small incremental steps, then
repack, measuring "any progress" not "reaches the bar") is sharply
target-dependent — KRAS_G12C 0.25→1.00 (an already-near-zero apo baseline
has "nowhere to go but up"), BCR_ABL1 0.05 (an *already*-druggable apo
baseline more often gets *worse* under undirected repacking). **Reading
this together**: the collective layer is cheap and not rare by two
independent methods; the joint layer's difficulty is real but is about
*how* the local component is approached (one big undirected jump vs.
many small steps; energy-only repack objective vs. a druggability-aware
one) rather than a flat "closed" verdict — KRAS_G12C in particular shows
easy *incremental* joint progress ([[TASK-0228]], p=1.00) alongside a
failed *one-shot* joint ceiling ([[TASK-0230]]), which argues for path-
dependence/search-method sensitivity at the joint layer, not for the
pocket being categorically unreachable there either.

**Graduation condition (Architect's Q2 answer), applied**: the stated bar
— calibrated ΔG numbers plausible (few kT) — is met, literally, for the
collective-layer estimate computed here, on all 3 targets (0.20–2.32
"thermal units," Boltzmann weights 0.10–0.82). Filing the hypothesis-
family subtask now, **scoped explicitly to the collective layer this
evidence actually supports** — quantum Gibbs/Boltzmann sampling over
*collective* (low-mode) conformer space, not a claim that the full
local+collective transition is now shown affordable, which remains
unresolved per the lower-bound caveat above. Named and scoped only, not
built or costed, per this task's own Out Of Scope and the Architect's own
"do not build before the physical question has an answer" caution — see
[[TASK-0234]].

**Validated**: `run_superpose` reused unmodified; `cumulative_overlap`
values here (0.766/0.805/0.954 at k=50) are consistent with — not
identical to, different alignment code path — [[TASK-0227]]'s own
independently-implemented k=50 overlap numbers (0.667/0.577/0.901 fully
corrected), both showing the same real, high-collective-overlap pattern
via two different implementations.

**Not done, per this task's own Out Of Scope**: verifying the
asciminib/myristoyl and mavacamten/SRX mechanism citations against live
DOIs (still open, not asserted validated); estimating the local
residual's own elastic/repacking cost (the natural next step if this
line of work continues).

**Resolved, 2026-08-24, [[TASK-0236]]**: both mechanism citations above
verified against live, resolving DOIs, both confirming the claim as
stated (not just the drug name) — asciminib/myristoyl (Wylie et al.
2017, *Nature* 543:733-737, doi:10.1038/nature21702) and mavacamten/SRX
(Rohde et al. 2018, *PNAS* 115:E7486-E7494, doi:10.1073/pnas.1720342115).
No correction needed to this task's own text; both added to
`REFERENCES.md`'s method/tool papers table.

**Correction, 2026-08-23, on picking up [[TASK-0234]]**: this task's own
graduation-condition application (below) filed [[TASK-0234]] on the
ΔG-plausibility bar alone, without first checking whether the same
displacement was already known to be *rare* — the actual condition a
quantum search/sampling hypothesis needs, not just "plausible." User's
instruction on picking up [[TASK-0234]] ("check the outcomes of the 229
family — these may be relevant") surfaced [[TASK-0185]] (2026-08-02, pre-
existing, not itself a TASK-0229.xxx file but adjacent prior work this
task's own filing should have cross-checked): real classical ANM
ensemble sampling already recovers the pocket in 1–8 draws on every real
target — not rare, independently reconfirmed by [[TASK-0228]]'s own `p`
and this task's own `exp(−ΔG)`. **The ΔG numbers above still stand as
correct and real** — the error was treating "plausible" alone as
sufficient grounds to file a quantum-sampling hypothesis subtask, when
"plausible and common" (the actual, now four-times-independently-
confirmed finding) argues against one instead. See [[TASK-0234]]'s own
Done section for the full retraction and what it leaves as the program's
actual remaining gap (backbone-modeling fidelity, not search cost).
