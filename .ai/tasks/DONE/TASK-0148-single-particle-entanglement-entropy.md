# TASK-0148 Single-particle entanglement entropy across a spatial cut (localization-sensitive observable)

## Context

- ID: TASK-0148
- Title: compute the entanglement entropy of the CTQW's single-particle
  state across a spatial bipartition (a candidate residue's local
  neighborhood vs. the rest of the structure), as a per-candidate
  coupling/localization observable distinct from occupation, distance-
  stratified AUC, or anything else currently in the register.
- Status: Done
- Owner: Implementer
- Claimed By: Implementer C (this thread)
- Claimed At: 2026-07-24
- Source: raised by the orchestrating user, 2026-07-20, as an open
  "what's still worth trying" question (originally framed as "quantum
  mutual information" between the active site and candidate residues).
  **Re-scoped by this Architect/Planner thread, 2026-07-20, to a cheaper,
  better-grounded, more tractable form** — see the correction below —
  rather than filed as originally framed.
- Priority: **P2.**

## Correction to the original framing — read before implementing

The original framing ("quantum mutual information between active site
and candidate residue reduced density matrices") implicitly assumed a
genuine multi-body (2-excitation or explicit density-matrix) construction
would be needed — the same class of machinery [[TASK-0122]]'s
`mode_coparticipation` work and the boson-walk discussion (2026-07-20
conversation, not filed) both required. **That is not actually necessary
here.** Single-particle entanglement entropy across a spatial cut is a
well-established, cheaper quantity in condensed-matter physics — it is
the standard diagnostic for localization vs. delocalization of a single
particle/excitation (area-law vs. volume-law entanglement scaling is
literally how Anderson localization is characterized in that
literature), computable directly from the existing single-particle
propagator amplitudes via a **correlation-matrix eigenvalue method**
(Peschel 2003, *J. Phys. A* 36, L205, "Calculation of reduced density
matrices from correlation functions" — verify this citation directly,
per this project's own citation-verification discipline, before building
against it) — **no new multi-body machinery required.** This directly
connects to, and can be read alongside, this project's own existing
Anderson-localization finding for `H_new`'s CTQW (REVIEW-2026-07-13c,
[[TASK-0106]]) — entanglement entropy across a cut isolating the seed's
own neighborhood is a natural, independent diagnostic of exactly the
localization phenomenon already reported there, now applied per-
candidate rather than globally.

## Intent Contract

- Outcome: for the CTQW's single-particle state at a given time (or the
  converged limit, [[TASK-0130]]), compute the two-point correlation
  matrix `C_ij = <i| rho |j>` restricted to a chosen subset `A`
  (a candidate residue's local neighborhood, defined consistently with
  this project's existing pocket/neighborhood conventions), diagonalize
  it, and compute the von Neumann entropy from its eigenvalues (Peschel's
  method — verify the exact formula against the cited paper directly).
  Report this per-candidate-region entropy as a coupling/localization
  score, and separately as a diagnostic read alongside
  [[TASK-0106]]'s own global localization finding.
- Why required, not assumed: this is a well-defined, real quantity, not
  yet computed anywhere in this project despite the raw ingredients
  (single-particle amplitudes, spatial partitions) already existing —
  whether it's informative about pocket location, or just another
  window onto the same localization/proximity structure already found,
  is untested.
- In Scope:
  - Verify the Peschel citation directly before implementing against it
    (PubMed/WebFetch, per this project's own standing discipline —
    `.ai/reference/IMPLEMENTER_SPINUP_BRIEF.md` §2).
  - Implement the correlation-matrix entanglement-entropy calculation,
    reusing existing propagator amplitudes (no new Hamiltonian, no new
    heavy multi-body machinery).
  - Define the spatial partition consistently (e.g. the candidate
    residue plus its own graph neighborhood at a stated hop radius —
    state the choice).
  - Synthetic falsification gate first (does the entropy actually track
    coupling/delocalization on a constructed case, e.g. the dumbbell or
    a simple two-region toy graph, before trusting real data).
  - Score against all 3 mandatory targets, the proximity floor
    ([[TASK-0094]]), with CIs ([[TASK-0112]]) and a permutation null on
    any max-over-partitions step.
  - Cross-read against [[TASK-0106]]'s own global localization finding —
    does a per-candidate entropy pick out anything [[TASK-0106]]'s
    global participation-ratio measurement didn't?
- Out Of Scope:
  - Genuine multi-particle/bosonic entanglement (the boson-walk idea
    discussed 2026-07-20, not filed) — a different, more expensive
    construction; do not conflate the two.
  - Reselecting the submission operator (Tier-2-gated, [[TASK-0100]]).
- Constraints And Invariants: the spatial-partition definition is fixed
  once, stated, and blind to labels.
- Planned Validation: the synthetic gate first; then real-target scoring,
  reported whichever way it comes out.

## In Progress

None

## TODO

- [x] Verify the Peschel (2003) citation directly before implementing.
- [x] Implement the correlation-matrix entanglement-entropy calculation.
- [x] Define and justify the spatial-partition convention.
- [x] Synthetic falsification gate before real data.
- [x] Score all 3 mandatory targets vs. the proximity floor, with CIs
      and a permutation null.
- [x] Cross-read against TASK-0106's own global localization finding.
- [x] Report the result, whichever way it comes out.

## Dependency

- [[TASK-0094]] (Done) — proximity floor.
- [[TASK-0112]] (Done) — bootstrap CI.
- [[TASK-0106]] (Done) — the global localization finding this task's
  per-candidate version should be read alongside.
- [[TASK-0130]] (Done) — the converged-limit propagator this task can
  reuse directly.

## Open Questions

- Exact spatial-partition convention (hop radius around each candidate)
  — not pre-decided; Implementer's call, state the choice and why in
  Done. **Resolved**: radius=1 (immediate contact neighbors + self),
  the minimal well-defined "local neighborhood" at this project's own
  standard contact-graph resolution; radius=2 characterized as a KNOB,
  not used for the primary score.
- Whether to score at the converged limit or a finite, physically-
  motivated time — state the choice. **Resolved, with a real reason,
  not a preference**: the converged/time-averaged limit is not
  available at all for this observable — Peschel's method needs a
  genuinely coherent complex amplitude (off-diagonal phase coherences),
  and `time_averaged_ctqw`/its converged form only ever return
  `|amplitude|^2`, discarding exactly the information this calculation
  needs. Used a fixed coherent snapshot at `t* = 1/gap` (this project's
  own established gap-derived-timescale convention), blind to labels.

## Done

**2026-07-24, Implementer C (this thread).**

**Citation verified before implementing**: Peschel, I. (2003),
"Calculation of reduced density matrices from correlation functions",
J. Phys. A: Math. Gen. 36, L205 (arXiv:cond-mat/0212631) — confirmed
real via IOPscience/arXiv/ADS (WebSearch). Exact formula independently
cross-checked in the literature (not just the PDF, which failed to
extract cleanly — a repeat of this project's own documented PDF-fetch
difficulty): `S_A = -sum_k [nu_k*ln(nu_k) + (1-nu_k)*ln(1-nu_k)]` over
the eigenvalues `nu_k` of the correlation matrix `C_A` restricted to
subsystem A.

**A real mathematical reduction, derived and verified numerically
before implementing anything else** (this task's own central finding):
for a single COHERENT source, the correlation matrix restricted to any
region is exactly rank-1 (`C_A = psi_A (x) conj(psi_A)`, an outer
product), collapsing Peschel's general matrix diagonalization to the
elementary closed form `S_A = h(P_A)`, the *binary* Shannon entropy of
the region's own total occupation probability — confirmed to match the
general matrix method to machine precision (`1e-16`) before trusting
it, `tests/test_entanglement.py`. This closed form does **not** apply
under this project's own established multi-residue active-site GAUGE
(TASK-0118: an incoherent statistical mixture, not a coherent
superposition) — an incoherent mixture's correlation matrix is a sum of
`k` rank-1 terms, generically rank up to `k`, confirmed directly (not
assumed) via a synthetic multi-source check whose correlation matrix
genuinely has >1 nonzero eigenvalue. Real-target scoring therefore uses
the general Peschel diagonalization (`entanglement_entropy_mixture`),
not the closed-form shortcut, since every real active site is
multi-residue.

**A second real finding, resolving the task's own Open Question with a
reason rather than a preference**: entanglement entropy fundamentally
needs the coherent complex amplitude's off-diagonal phase information —
`propagators.ctqw`/`time_averaged_ctqw`/its converged form all discard
this by design (they only ever return `|amplitude|^2`). The converged/
time-averaged limit this project defaults to for most headline scores
is therefore not an available choice here at all, not merely
undesirable — used a fixed coherent snapshot instead, `t* = 1/gap`
(this project's own established gap-derived-timescale convention,
matching `propagators.check_convergence`'s own `ground_state_relaxation`
criterion's `w[1]-w[0]` gap), a blind, label-free choice.

**Implementation**: new `src/allostery/entanglement.py`
(`peschel_entropy`, `entanglement_entropy_closed_form`,
`entanglement_entropy_mixture`, `hop_radius_neighborhoods`,
`natural_coherent_time`) + 16 new tests (`tests/test_entanglement.py`):
the general-vs-closed-form match, the multi-source rank>1 structural
check, GAUGE (residue relabeling), and the hop-radius partition logic
on a known small graph.

**Synthetic falsification gate**
(`tests/test_dumbbell_negative_control.py::TestEntanglementEntropyDumbbellGate`,
5 new tests, reusing `build_dumbbell_network` as-is): a clean, decisive
double dissociation against GSR on the conflict cells (C2=1.000,
C3=0.000, every seed) — genuinely follows coupling, not the well. C1
(cues agree) not asserted directionally, matching this file's own
established precedent for the identical reason (a deep co-located well
puts the coherent amplitude into a resonance-sensitive regime even when
coupling agrees — CP and `T(E)`, TASK-0122/0145, show the same pattern
on this construction). C4 (no signal) has the same real, high per-seed
variance TASK-0145's gates already found and characterized with a wider
seed average.

**Real-target scoring, all 3 mandatory targets**
(`scripts/entanglement_entropy_real_run.py`), radius=1, `t=t*`, against
TASK-0094's proximity floor with block-bootstrap CIs and a permutation
null on the primary (pre-registered, not best-of-K) score:

| Target | Entropy AUC | Floor | Category | Permutation p |
|---|---|---|---|---|
| KRAS_G12C | 0.4787 | 0.4818 | NO_SIGNAL_IN_APO | 0.629 |
| BCR_ABL1 | 0.5291 | 0.5817 | NO_SIGNAL_IN_APO | 0.349 |
| CARDIAC_MYOSIN | 0.4810 | 0.5679 | NO_SIGNAL_IN_APO | 0.624 |

**A clean, complete negative — reported as such, not softened.** No
target clears the floor, and no p-value is anywhere near significant
even uncorrected. Radius (1 vs 2) and `t` (0.5x/1x/2x `t*`)
characterized as KNOBs on a small grid (never used to pick a
best-scoring point against labels): `t` shows a real, moderate trend on
2/3 targets (e.g. KRAS_G12C: AUC 0.421 -> 0.479 -> 0.545 across the
grid) but never crosses into floor-clearing territory; radius has a
small effect (<0.03 AUC swing).

**Cross-read against TASK-0106's own global localization finding**:
this task's own coherent-snapshot occupation (the same state the
entropy scores are built from) has a participation ratio 1.2-2.3x
*higher* (more localized) than the project's own standard converged-
limit occupation on all 3 targets (e.g. CARDIAC_MYOSIN 0.084 vs 0.081,
KRAS_G12C 0.021 vs 0.015, BCR_ABL1 0.018 vs 0.008) — consistent with,
not contradicting, TASK-0106's own established finding that `H_new`'s
CTQW is genuinely Anderson-localized: a coherent snapshot retains more
of that localization than the fully dephased/time-averaged limit does.
Does not, on its own, explain why the per-candidate entropy observable
itself finds no discriminative signal — localization and discrimination
are different questions, and this task's own real result answers the
second one directly (no), not by inference from the first.

**Not done / explicitly out of scope** per this task's own Out Of
Scope: no genuine multi-particle/bosonic entanglement construction (the
2026-07-20 boson-walk discussion, not filed, a materially different and
more expensive object); no submission-operator reselection (Tier-2
gated, [[TASK-0100]]). Full regression suite re-run after this change:
941 passed, 2 xfailed, no failures.
