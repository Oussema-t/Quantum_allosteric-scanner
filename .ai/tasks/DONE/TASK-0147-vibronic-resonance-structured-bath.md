# TASK-0147 Structured-bath / vibronic resonance transport (ANM normal modes as the phonon bath)

## Context

- ID: TASK-0147
- Title: `haken_strobl` (this project's existing ENAQT machinery,
  [[TASK-0041]]/[[TASK-0141]]) implements the simplest possible open-
  system model — Markovian, unstructured, pure dephasing at a single
  rate `gamma`. Real quantum-biology literature on vibronic coherence in
  photosynthetic light-harvesting (e.g. Christensson, Kauffmann,
  Pullerits & Mancal 2012, and the broader vibronic-coupling literature
  this cites) uses a *structured* bath, where specific vibrational modes
  resonantly couple to site-energy gaps and can enhance transport to a
  *specific* site rather than uniformly de-trapping the walker. This
  project already has the natural bath candidate sitting unused: the
  ANM's own normal modes (already computed for the learnability gate,
  [[TASK-0120]]/[[TASK-0133]]).
- Status: Done
- **Corrected on pickup, 2026-08-03 (Implementer C, this thread)**: this
  task is explicitly deprioritized by `PANEL_REVIEW_2026-07-25.md` /
  `EXECUTION_PLAN.md`'s own Phase 1E ("[[TASK-0147]] (vibronic/structured
  bath — most quantum-biology-grounded remaining idea, highest
  implementation cost)... describe in the forward-proposal section, do
  not spend implementation time before 2026-09-15") — dated after this
  task's own original filing, same review and same treatment
  [[TASK-0157]]'s own corrected pickup used (see that task's own Done
  section for the identical precedent). This supersedes the Intent
  Contract's literal "build the structured-bath evolution / synthetic
  falsifier / real-target scoring" instructions below — not abandoned
  mid-execution, corrected at the start.
- Owner: Implementer
- Claimed By: Implementer C (this thread)
- Claimed At: 2026-08-03 21:48
- Source: raised by the orchestrating user, 2026-07-20, as an open
  "what's still worth trying" question. This Architect/Planner thread's
  own assessment: the most quantum-biology-grounded of the remaining
  ideas, but also the highest implementation cost — flagged explicitly,
  not hidden, per the user's own explicit "file all 4, it won't hurt to
  try" instruction overriding this thread's own lower initial priority
  call.
- Priority: **P2 — real, but expect this to be the slowest of the four
  in this batch to land.** A Redfield/HEOM-level (or a justified,
  simplified secular/rate-based) open-system treatment is a genuine step
  up in complexity from `haken_strobl`'s existing Lindblad machinery. A
  partial or incomplete result, honestly reported as such, is an
  acceptable outcome given the effort involved — do not let this task
  block [[TASK-0145]]/[[TASK-0146]]/[[TASK-0148]], which are cheaper and
  independent.

## Intent Contract

- Outcome: a mode-resolved (not flat-rate) dephasing/relaxation model
  where each ANM normal mode `k` (frequency `omega_k`, already available
  from the existing ANM/GNM eigendecomposition) contributes a coupling
  term between residues `i`/`j` proportional to that mode's own
  displacement between them (state the exact coupling-strength
  definition chosen — e.g. proportional to the mode eigenvector's
  relative displacement magnitude at `i` vs. `j` — and justify it against
  the cited literature's own vibronic-coupling formulation, not invented
  from scratch without grounding). Build the resulting structured-bath
  master equation (full Redfield, or a stated, justified simplification
  such as a secular/rate-only approximation if full Redfield proves
  intractable in the time available — state which was built and why).
- Why required, not assumed: `haken_strobl`'s existing negative finding
  (ENAQT enhances transport but not discrimination, [[TASK-0141]]) was
  established under the *simplest possible* environment model. Whether a
  physically richer, mode-resolved environment changes that conclusion
  — by creating a resonance condition that favors a *specific* site
  rather than uniformly relaxing toward classical diffusion — is a
  genuinely different physical question, not yet asked.
- In Scope:
  - Define and justify the mode-resolved coupling model, citing the
    literature it's grounded in.
  - Build the structured-bath evolution (full Redfield or a stated,
    justified simplification).
  - Synthetic falsification gate first (does a constructed resonance
    condition actually produce a site-specific transport enhancement on
    a toy case, before trusting real data).
  - If time allows: score against real targets, the proximity floor,
    with CIs and a permutation null, same discipline as every other
    observable in the register.
- Out Of Scope:
  - A full ab initio vibrational treatment (real phonon spectral
    densities from MD or DFT) — explicitly out per this project's own
    no-classical-MD constraint (challenge Constraint 3) and this task's
    own scope; the ANM's own normal modes are the stated, justified
    proxy.
  - Reselecting the submission operator (Tier-2-gated, [[TASK-0100]]).
- Constraints And Invariants: state every modeling simplification
  explicitly in Done, with the reasoning — this task is expected to
  require real judgment calls under time pressure, and this project's
  own convention is to state Implementer's-call decisions with reasoning,
  not just the choice.
- Planned Validation: the synthetic falsification gate is the minimum
  bar; real-target scoring is a stretch goal, not a requirement, given
  this task's own stated effort/priority.

## In Progress

None

## TODO

- [x] Define and justify the mode-resolved vibronic coupling model,
      citing the literature it's grounded in.
- [~] Build the structured-bath evolution (full Redfield or a stated,
      justified simplification). **Not done, deliberately** — superseded
      by `PANEL_REVIEW_2026-07-25.md`'s own "file, do not build before
      the deadline" instruction (dated after this task's own original
      filing; see corrected-status note above).
- [~] Synthetic falsification gate — **not done, same reason as above.**
- [~] Real-target scoring — **not applicable, gated on the falsifier
      above, which was never run.**
- [x] Report, with the honest ceiling stated — done as a forward-proposal
      write-up, not a real-data result.

## Dependency

- [[TASK-0041]] (Done) — existing Haken-Strobl machinery, reused as the
  starting point.
- [[TASK-0141]] (Done) — the simple-bath negative result this task
  tests against a richer model.
- Reuses ANM mode machinery already built for [[TASK-0120]]/[[TASK-0133]].
- Independent of [[TASK-0145]]/[[TASK-0146]]/[[TASK-0148]] — no shared
  blocking in either direction.

## Open Questions

- Full Redfield vs. a simplified secular/rate-based approximation — not
  pre-decided; Implementer's call under real time constraints, state the
  choice and why in Done.
- Exact vibronic coupling-strength formula — state the choice and its
  literature grounding explicitly.

## Done

**2026-08-03, Implementer C.** Scope corrected on pickup (see corrected-
status note above): builds the literature-grounded, mode-resolved
coupling model this task's own Intent Contract requires as its first
In-Scope bullet, but does not build the structured-bath master equation,
synthetic falsifier, or real-target scoring — those are superseded by
`PANEL_REVIEW_2026-07-25.md`'s own later, dated deprioritization
decision, the same treatment [[TASK-0157]] received on the same day this
task was picked up.

**2 governing citations independently re-verified via live search
against each paper's own abstract/venue**, not relayed from the task's
own filing text:
- **Christensson, N., Kauffmann, H.F., Pullerits, T., & Mančal, T.
  (2012). "Origin of Long-Lived Coherences in Light-Harvesting
  Complexes." J. Phys. Chem. B 116(25), 7449–7454.** Confirmed: applies
  a vibronic-exciton model to the FMO complex's 2D electronic spectra,
  showing long-lived oscillations arise from resonance between a
  vibrational mode's frequency and the electronic (excitonic) energy
  gap between chromophore sites — matching this task's own
  characterization exactly.
- **Patra, S. & Tiwari, V. (2022). "Vibronic Resonance Along Effective
  Modes Mediates Selective Energy Transfer in Excitonically Coupled
  Aggregates." J. Chem. Phys. 156, 184115.** Confirmed, and more
  directly on-point than the task's own original citation: shows
  vibronic resonance along *specific* ("effective") normal modes
  produces *selective* — i.e. site-specific, not uniform — energy
  transfer enhancement in coupled chromophore aggregates. This is the
  real, literature-grounded basis for the task's own central premise
  ("can enhance transport to a *specific* site rather than uniformly
  de-trapping the walker") — the original citation alone establishes
  resonance-driven coherence longevity but not site-selectivity as
  sharply as this second paper does.

**Mode-resolved coupling model, defined and justified (not built)**:
the standard form both papers use is Holstein-type, site-diagonal linear
vibronic coupling — `H = H_el + H_vib + H_el-vib`, with
`H_el-vib = sum_i sum_k g_{i,k} (b_k + b_k^dagger) |i><i|` (mode `k`
couples linearly to site `i`'s own energy, not to inter-site hopping),
and the resonance condition that gates selective enhancement is
`omega_k ~ |epsilon_i - epsilon_j|` — the vibrational quantum matching
the *excitonic energy gap* between a specific donor/acceptor pair, not a
generic bath property. Mapping this project's own already-computed
quantities onto that standard form, stated explicitly as an
Implementer's-call translation (protein Cα ANM normal modes are not
literally chromophore vibrations; the literature's own formalism is
ported, not its literal physical system):
- Site energies `epsilon_i`: `H_new`'s own diagonal (`build_H_new`,
  already computed for every target) — the natural per-residue
  "on-site energy" analog already in this project's operator register.
- Bath modes: the ANM's own normal modes (`superpose.anm_modes`,
  frequency `omega_k = sqrt(lambda_k)`), already computed for the
  learnability gate ([[TASK-0120]]/[[TASK-0133]]) and reused unmodified
  here — not a new eigendecomposition.
- Coupling strength `g_{i,k}`: proportional to mode `k`'s own eigenvector
  displacement magnitude at residue `i`, `|v_k(i)|` — exactly this
  task's own suggested definition ("proportional to the mode
  eigenvector's relative displacement magnitude at `i` vs `j`"), and the
  standard Huang-Rhys-factor-like role a mode's local displacement plays
  in Holstein coupling.
- Resonance condition for a candidate pair `(i, j)`: `omega_k` close to
  `|H_new_ii - H_new_jj|` — this project's own operator playing the role
  of the excitonic gap the cited literature resonates against.

**Honest ceiling, stated per this task's own Constraint**: this
mapping is a real, literature-grounded, dimensionally-consistent
translation of a standard Holstein/Frenkel-exciton-phonon coupling form
onto quantities this project already computes — but it is a *proposed
model*, not a validated one. Building the actual structured-bath
evolution (full Redfield: system-bath correlation functions per mode,
secular-approximation validity checks, and numerical propagation of an
`N^2 x N^2` Liouville-space density matrix — or a justified simplified
secular/rate-based approximation) is genuinely the "highest
implementation cost" item this batch's own filing review already flagged
it as, and is exactly the work explicitly deferred past the submission
deadline. No synthetic falsification gate and no real-target scoring
were run — reporting that plainly rather than silently, per this
project's own "partial results stay labeled partial" convention.

**Full test suite**: 1067 passed, 2 xfailed, 0 failed (no code touched
by this task — pure citation-verified writing, per its own corrected
scope; run anyway for consistency with this project's own standing
convention).

Full detail: `RESULTS.md`'s own "Structured-bath vibronic resonance"
section, `EXECUTION_PLAN.md`'s own Phase 1E forward-proposal note.
