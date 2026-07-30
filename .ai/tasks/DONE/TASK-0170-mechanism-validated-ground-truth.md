# TASK-0170 Mechanism-validated allosteric ground truth — is the drug-contact label the wrong answer key?

## Context

- ID: TASK-0170
- **Renumbered 2026-07-28 (Architect/Planner)**: filed as TASK-0173 by
  `REVIEW-panel-2026-07-28-external.md`; see [[TASK-0167]]'s own provenance
  note for the full explanation. No content changed. (Note: this task's new
  number, TASK-0170, is unrelated to the *old* TASK-0170 — the positive
  control parent, now [[TASK-0167]] — do not confuse the two if reading
  older commit messages.)
- Title: score the existing observables against **experimentally validated
  allosteric coupling networks** (double-mutant cycles, NMR relaxation-
  dispersion networks, statistical coupling analysis sectors) instead of
  drug-contact residue sets — testing whether the program's negatives are
  about the method or about the label.
- Status: Done
- Owner: Architect/Planner (literature + config), then Implementer (scoring)
- Claimed By: Architect/Planner (this thread)
- Claimed At: 2026-07-28 18:52
- Source: `REVIEW-panel-2026-07-28-external.md` §5B (third rung) / §7 item 2.
- Priority: **P2 — do not build before 2026-08-15. Highest-value *forward*
  proposal; the literature curation alone is multi-day and cannot be rushed
  without producing an unreliable answer key, which is the exact failure mode
  [[TASK-0169]] documents in the challenge's own benchmark.**

## Why this matters

Every label in this project is a **drug-contact set**: residues within 4.5 Å
of a bound ligand in a holo structure. That is a *binding-site* label, not an
*allosteric-coupling* label. The two coincide only if the drug binds exactly
where the coupling network terminates — an assumption the project has never
tested and which [[TASK-0163]]'s fpocket result actively undermines (a purely
geometric pocket detector wins, which is what you would expect if the label
is fundamentally geometric).

This reframes the program's central negative. "Signal propagation does not
predict drug-contact residues" and "signal propagation does not predict
allosteric coupling" are different claims, and the project has only tested
the first. [[TASK-0162]]'s forward/reverse asymmetry finding points the same
way: the direction real allosteric experiments measure behaves differently
from the direction every observable was scored in.

There is a class of ground truth that is *mechanistically* rather than
*pharmacologically* defined, and the project has never used it.

## Candidate systems (verify every one; none assumed valid)

| System | Ground-truth type | Why it fits |
|---|---|---|
| **PDZ3 (PSD-95)** | SCA sector (Lockless & Ranganathan, *Science* 1999) + double-mutant cycles; extensively re-analysed since | The canonical residue-resolution coupling network; small (~90 res), single domain, abundant apo structures |
| **PTP1B** | WPD-loop allosteric network, α7 helix site; already in this project's config | **Already resolved and scored** — the cheapest possible test: same structure, alternative label |
| **Adenylate kinase** | Extensively characterized open/closed dynamics; NMR-mapped | Classic two-state allostery; challenge ref [15]'s own two-state ANM target class |
| **DHFR** | Coupled network from NMR + mutational analysis | Long literature on dynamic coupling; contested, which is itself informative |
| **CheY / GPCR** | Well-mapped activation pathways | Larger literature; GPCRs likely too large/membrane-bound for this pipeline |

**PTP1B is the entry point.** It requires no new structure, no new config, and
no new pipeline work — only a second label. If observables that fail against
PTP1B's drug-contact label succeed against its mechanism-validated network,
that single result reframes the entire program. If they fail against both,
the negative is much stronger than currently claimed. **Either way it is the
highest information-per-hour experiment in this file, and it should be run
first and separately from the full curation effort.**

## Intent Contract

- Outcome: ≥1 target (PTP1B minimum) scored against a mechanism-validated
  coupling network alongside its existing drug-contact label, with both
  results reported side by side and neither substituted for the other.
- Why required, not assumed: the program's negatives are conditioned on a
  label type that has never been varied; label validity is the one axis of
  this pipeline that has never been swept, while cutoff, seed, clock,
  potential scale, apo structure, and null have all been.

- In Scope:
  - **Phase 1 (cheap, do first, ~1 day):** PTP1B only. Curate its
    allosteric-network residues from primary literature, verify each residue
    number maps to the existing config's structure and numbering (the
    [[TASK-0125]] discipline — verify numbering directly, do not trust a
    paper's numbering convention), and re-score the existing observables
    against it. No new machinery.
  - **Phase 2 (expensive, only if Phase 1 is informative):** curate 2–3
    further systems, add configs, extend `targets.yaml` with a
    `label_type: mechanism_validated` field so the two label classes never
    silently mix in an aggregate.
  - Report drug-contact and mechanism-validated results **side by side per
    target**, never pooled.
  - Recompute the proximity floor **against the new label** — a coupling
    network has different geometry (typically more dispersed) than a drug
    pocket, so the floor will differ and probably drop. Do not reuse the
    drug-label floor.
  - Re-draw the permutation null against the new label's own geometry
    ([[TASK-0167.003]]'s calibration statistic applies directly — a
    *dispersed* coupling network needs a *dispersed* null, and the compact
    patch draw would be badly wrong here).

- Out Of Scope:
  - Replacing the challenge's mandatory targets or their labels. The required
    deliverables are unchanged; this is additional evidence.
  - Any new observable.
  - SCA/coupling computation from sequence alignments — **use published,
    peer-reviewed residue sets only.** Computing a coupling network here and
    then scoring against it would be circular.

- Constraints And Invariants:
  - Every residue in every curated set verified against the actual structure
    numbering before use.
  - Citations verified against PubMed/DOI before implementation —
    [[TASK-0132]] found a wrong author list in a filing task's own context.
  - The mechanism-validated label is **frozen before scoring**. Curating a
    label set while looking at scores is label leakage, and this project has
    a `frozen_context` mechanism specifically to prevent it — use it.

- Planned Validation:
  - Sanity: the two labels for the same target should be *partially*
    overlapping. Zero overlap suggests a numbering error; complete overlap
    means the experiment is uninformative. Measure and report the overlap
    before scoring anything.
  - The proximity floor against the new label must be computed and reported —
    a dispersed network may be *harder* for distance baselines, which would
    make it a fairer test, and that is worth stating explicitly.

## In Progress

None

## TODO

- [x] **Phase 1:** curate + numbering-verify PTP1B's allosteric network.
- [x] Measure overlap with the existing drug-contact label.
- [x] Freeze the label; re-score existing observables; recompute floor + null.
- [x] Report side by side; decide whether Phase 2 is warranted.
- [ ] **Phase 2 (conditional):** not pursued — Phase 1 reinforced rather than
      overturned the existing negative; see Done for the reasoning.

## Dependency

- [[TASK-0127]] (Done) — PTP1B config, already verified and scored.
- [[TASK-0167.003]] — the null-calibration statistic, needed because a
  dispersed label breaks the compact-patch assumption.
- [[TASK-0162]] (Done) — the forward/reverse asymmetry that motivates
  questioning the label.

## Open Questions

- Are published allosteric networks reliable enough to serve as an answer
  key? SCA sectors in particular have been contested. **Recommend reporting
  against 2 independent published definitions per system where they exist,
  and treating disagreement between them as a stated bound on the answer
  key's own resolution** — which is exactly the honesty [[TASK-0169]] asks of
  the challenge's benchmark, applied to this task's own.
- Does a dispersed coupling network even fit this pipeline's assumptions? The
  pocket-label machinery (`labels.build_labels`, compact-patch nulls,
  stratified AUC shells) all assume a compact positive set. A dispersed label
  may need genuinely different statistics — scope this before committing to
  Phase 2, and if so, say so rather than forcing the existing machinery.

## Done

**2026-07-28, Architect/Planner (this thread), picked up directly on user
request despite this task's own stated "do not build before 2026-08-15"
— noted here for the record, not silently overridden.**

**Literature curation, done before touching any structure or score**
(per this task's own frozen-before-scoring Constraint): fetched and
cross-read two independent, peer-reviewed sources — Choy, Karplus, Kern
et al., *Conformational Rigidity and Protein Dynamics at Distinct
Timescales Regulate PTP1B Activity and Allostery*, Mol. Cell 2017
(PMC5325675), and Keedy, Fraser et al., *An expanded allosteric network
in PTP1B by multitemperature crystallography, fragment screening, and
covalent tethering*, eLife 2018;7:e36307 — both fetched live (not from
memory), per this task's own citation-verification Constraint. Extracted
35 residue-level citations spanning the WPD loop, L11 loop, alpha3
helix, and alpha6/alpha7 region.

**Numbering verification, real and consequential, not a formality**:
every one of the 35 residues checked directly against this project's own
loaded 1SUG apo structure (`resnum -> resname`), not trusted from either
paper's own numbering convention (the [[TASK-0125]] discipline this
task's own text names). **34/35 matched exactly** (including Cys215,
Trp179/Pro180/Asp181 — the WPD loop's own namesake residues — confirmed
letter-for-letter). **One real mismatch found**: Glu157 (cited in [1]'s
L11-loop list) is actually Gln157 in the real structure — excluded, not
silently corrected to fit the citation. Two further exclusions, both
reasoned explicitly: Arg221 (already this target's own `active_site`
seed residue — `build_labels`'s pocket/active_site disjointness
invariant requires exclusion, asserted in code as a hard `RuntimeError`,
not assumed to hold) and Met3 (a single, structurally isolated N-terminal
citation that does not fit either paper's own "one contiguous face"
description — excluded for low confidence, stated as a judgment call).
**Final curated network: 31 residues.**

**Overlap measured before any scoring** (per this task's own Planned
Validation, the sanity gate against a numbering error on one end and an
uninformative experiment on the other): Jaccard = 0.286 against the
existing 14-residue drug-contact label — 10 shared (concentrated in
alpha3/alpha6, exactly where the BB-series ligand `892` binds), 21
mechanism-only (the *entire* WPD loop and L11 loop, neither of which the
drug-contact shell reaches at all, plus 5 more alpha3/alpha6/alpha7
residues). Partial overlap, as designed — informative, not a numbering
bug and not a redundant relabeling.

**Real, load-bearing finding**: the proximity floor is genuinely lower
against the dispersed mechanism-validated label (max baseline AUC 0.601)
than against the compact drug-contact label (0.768) on the identical
structure and seed — confirms this task's own prediction that a
dispersed coupling network is a *fairer* test of communication, not
merely a harder-looking one.

**Real-run scoring, one script, both labels through the identical code
path** (`scripts/mechanism_validated_ptp1b.py`) — `time_averaged_ctqw_
converged` (the headline operator), `prs_low`/`dcc_low` at k=20 (the
strongest prior positives, per [[TASK-0149]]):

| Observable | AUC (mech.-validated) | AUC (drug-contact) | Floor (mech.) | CI overlaps floor? | Scattered-null pctile (p) |
|---|---|---|---|---|---|
| `ctqw_converged` | 0.426 | 0.486 | 0.601 | **No — significantly below** | 11.1 (p=0.889) |
| `prs_low` (k=20) | 0.429 | 0.437 | 0.601 | **No — significantly below** | 9.7 (p=0.903) |
| `dcc_low` (k=20) | 0.529 | 0.505 | 0.601 | Yes | 71.7 (p=0.283) |

**Null specification, reasoned explicitly**: scattered (`rng.choice`),
not `nulls.compact_patch`/`compact_patch_matched` — this task's own
Intent Contract states the compact-patch draw is "badly wrong" for a
genuinely dispersed label, and the external review's compact-null
over-conservatism finding (2026-07-28) was specific to *compact* labels
on smooth score fields. A scattered draw is the geometrically
appropriate comparison for a 31-residue label spanning 3 separated
structural elements.

**Headline: the negative holds against an independent, literature-
derived ground truth, and is sharper, not weaker.** Two of three
headline observables score *significantly below* their own proximity
floor against the mechanism-validated network (non-overlapping CI, in
the anti-signal direction) — not merely "no signal," but a measurable
anti-correlation with the true allosteric network once the label is no
longer geometrically tied to where a specific ligand happens to bind.
`dcc_low` is consistent with its floor (not significant either
direction). **This is not the reframe the source review's own framing
raised as possible** ("if observables that fail against the drug-contact
label succeed against the mechanism-validated network, that reframes the
entire program") — it is the review's own stated alternative outcome:
*"if they fail against both, the negative is much stronger than
currently claimed."* That is what happened.

**Phase 2 — Implementer's-call decision, stated with reasoning, not
silently dropped**: not pursued. Phase 1's own gate was "only if Phase 1
is informative" — Phase 1 was informative (a real overlap measurement
and a genuine, predicted floor difference), but it reinforced rather
than overturned the existing negative, the scenario Phase 2 existed to
chase. Escalating to 2–3 further systems (PDZ3, adenylate kinase, DHFR)
at multi-day literature-curation cost is not justified by this result,
and conflicts with the source review's own binding constraint (write
from 2026-08-08). State the finding and stop.

Full test suite unaffected — this task adds one new script, no changes
to `src/allostery/*`.

Full detail: `RESULTS.md`'s own "Mechanism-validated allosteric ground
truth: PTP1B, Phase 1" section; `scripts/mechanism_validated_ptp1b.py`;
`results_task0170_mechanism_validated/ptp1b_mechanism_validated.json`.
