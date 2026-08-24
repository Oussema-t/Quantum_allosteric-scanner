# REFERENCE_HYPOTHESIS_REGISTER.md

Systematic extraction of testable hypotheses from the Cleveland Clinic challenge
statement's own reference list [1]–[25], with tested/untested status and open venues.

**Provenance:** produced in an external chat session, 2026-08-21, without repo access.
Status labels reflect what that session could infer about repo state. **Repo agents must
verify each `STATUS` line against actual task files before acting.** Where this document
reports a measured number, it comes from `TASK-0210_observable_family_confound.md` in the
same drop — run on bundled non-target PDB structures, never on challenge targets, unless
a line below explicitly says it has since been superseded by a real-PDB retest.

**Tagging:** OBSERVED / HYPOTHESIS / UNTESTED / PARTIAL / TESTED / CONTESTED.
**`PDB-RETEST`** = must be re-run on real challenge targets before any claim is written.

**Reconciled 2026-08-24 ([[TASK-0248]])** against the completed [[TASK-0229]] family
(.001–.007, all Done) and [[TASK-0226]] (the real-target PDB-retest of this document's
own original non-target confound numbers). Every `STATUS` line below states the actual
task and date, linking to its Done section rather than restating the result in full —
read the task file for the complete picture. See "Coverage summary" and "How to keep
this register in sync" immediately below.

---

## Coverage summary

| Hyp. | Claim (short) | Status | Task(s) | Date |
|---|---|---|---|---|
| H9 | No clean non-allosteric negative class | **PARTIAL** (conceptual claim untestable directly, as anticipated; response metrics built and run) | [[TASK-0229.001]] | 2026-08-21 |
| H6.1 | Allostery = population redistribution (unified mechanism) | **UNTESTED** | — | — |
| H6.2 | Sites are effector-specific (answer-key multiplicity) | **PARTIAL/TESTED** — 1 genuine second site found (BCR_ABL1), 3/4 targets single-site | [[TASK-0229.003]] | 2026-08-22 |
| H4.1 | EAM: partition-function coupling over 2^N microstates, not graph pathway | **TESTED** — harmonic proxy (real targets) still confounded; genuine COREX EAM run, real mixed result | [[TASK-0226]], [[TASK-0229.006]] | 2026-08-21/22, 2026-08-23 |
| H4.2 | Zero-mean-structural-change (Cooper–Dryden) entropic coupling | **PARTIAL** — proxy escapes the proximity confound on real targets; single-condition LOD check inconclusive | [[TASK-0226]] | 2026-08-21/22 |
| H4.3 | Disorder amplifies coupling (only route to c-Myc) | **UNTESTED** — c-Myc explicitly excluded as unvalidatable | [[TASK-0229.006]] (excluded, not tested) | 2026-08-23 |
| H4.4 | Coupling free energy doesn't decompose onto graph edges | **UNTESTED** | — | — |
| H5.1/H5.2 | MWC conformational selection; concerted multi-subunit transitions | **UNTESTED — genuinely open, zero coverage anywhere** (confirmed by direct search, not inherited) | — | — |
| H1 | NMA-guided conformational sampling finds cryptic sites | **TESTED** — implemented, validated, beats quantum arm's point estimate on KRAS_G12C (not register-significant) | [[TASK-0229.004]] | 2026-08-22 |
| H2.1 | Single-structure persistent-homology void signature | **TESTED (pre-existing)** — no real void detected, apo | [[TASK-0142]] | 2026-07-22 |
| H2.2 | TDA over an ensemble beats TDA on one structure | **TESTED — decisive negative**, positive control itself fails on both VALID targets | [[TASK-0229.005]] | 2026-08-23 |
| H7 | Non-equilibrium impulse-response energy transport | **TESTED — clean negative** (not a new axis vs. TASK-0199's ~3); a related steady-state quantity separately found confounded | [[TASK-0229.007]] (b), [[TASK-0226]] (`transmission_E0`) | 2026-08-23, 2026-08-21/22 |
| H15.1/H15.2 | Two-state ANM captures apo↔holo transitions | **TESTED — mixed**: whole-structure CO fails its own pre-registered comparison; pocket-restricted variant passes that one comparison but not a clean 7-target separation | [[TASK-0229.007]] (a) | 2026-08-23 |
| H8.1/H8.2 | Markov random walk / commute time (mandated classical baseline) | **TESTED** — real-PDB retest confirms: confounded, |partial ρ|=0.755±0.062, burial-loaded | [[TASK-0226]] | 2026-08-21/22 |
| H16.1 | GNM reproduces experimental B-factors (model-validity check) | **UNTESTED — genuinely open, zero coverage anywhere** (confirmed by direct search) | — | — |
| H16.2 | Binding sites at slow-mode minima | **TESTED** — real-PDB retest, escapes confound less cleanly than the non-target estimate: |partial ρ|=0.496±0.193 (was 0.292±0.218) | [[TASK-0226]] | 2026-08-21/22 |
| H10 | Circuit cutting / quasiprobability for non-local channels | **TESTED (paper-level)** — real per-target cut counts, reinforces `FAULT_TOLERANT_ONLY` | [[TASK-0229.002]] | 2026-08-22 |
| H11 | SVD/dilation for open-system hardware execution | **TESTED (paper-level)** — the one route that clears the qubit-count bar, under an unbuilt encoding | [[TASK-0229.002]] | 2026-08-22 |

**Genuinely open hypotheses (zero task coverage, confirmed by direct search, not inherited
from this register's own prior framing)**: **H5** (MWC / concerted transitions) and
**H16.1** (GNM–B-factor model-validity check). These are the two live inputs for any
follow-up test task this register motivates next — everything else above has at least
a partial measurement on record.

## How to keep this register in sync

The failure this task exists to fix: seven completed, real-data tasks (the [[TASK-0229]]
family) landed while this file kept saying `UNTESTED`/`PARTIAL`, and a reviewer relayed
that stale status to the user as current. The register's authority comes entirely from
being current — a stale `UNTESTED` is not a harmless omission, it is a false negative
about the program's own coverage.

**Rule, going forward**: any task that tests a hypothesis in this register (whether or
not it was filed as a `TASK-0229.0XX` subtask) must, in its own Done section, either (a)
update this register's `STATUS` line and Coverage-summary row directly, in the same
commit as the rest of its write-up, or (b) if out of that task's own stated scope, add
one sentence to its own Done section flagging the register as now-stale for that
hypothesis and naming the row — so the gap is discoverable by `grep`, not silent. A task
whose own Related/Source line cites a hypothesis in this register and does not touch
this file should be treated as leaving a known gap, not as having implicitly updated it.

---

## Tier A — hypotheses that attack current results

### H9 — Allostery is intrinsic to all dynamic proteins
*Ref [9] Gunasekaran, Ma & Nussinov 2004, Proteins 57:433.*

- **H9.1** Nearly every dynamic protein possesses latent allosteric capability; there is
  no clean class of "non-allosteric" surface sites.
- **STATUS:** PARTIAL. [[TASK-0229.001]] (2026-08-21) verified the citation directly and
  confirmed H9.1 is a conceptual claim about protein biology in general, not a
  per-target measurable one — not empirically tested, exactly as this register's own
  original "conceptual" framing anticipated, not a gap. The response half was built
  and run instead: `metrics.rank_of_known_site` (new) + `enrichment_at_k` recomputed on
  the 3 mandatory targets' headline cells — **enrichment@5 = 0.00 on all three**, which
  does not rescue the program's own AUC story but does change how "zero confirmed
  positives" must be phrased (evidence of no *robust* signal, not proof no signal
  exists). Limitations text landed in `documentation/PHASE1_SUBMISSION_DRAFT.md` §2.5.
- **WHY IT MATTERS:** This attacks the **negative class of every AUC in the program.**
  Matched-decoy nulls, setup-validity gates and all ROC framing presuppose that
  non-functional surface pockets are true negatives. [9] argues that premise is unsound.
  It cuts both ways: it inflates apparent false positives *and* it means a chance-level
  AUC is not evidence of no signal.
- **REMAINING OPEN VENUE:** (c) whether the ~226-cell multiple-comparison budget
  ([[TASK-0161]]/[[TASK-0199]]) is even the right frame if negatives are not negatives —
  addressed in [[TASK-0229.001]]'s own Done section (arithmetic unchanged, interpretation
  of the zero must be phrased carefully) rather than left open.
- **PDB-RETEST:** n/a (conceptual) — unchanged.

### H6 — Population shift is the unified mechanism; effects are effector-specific
*Ref [6] Tsai & Nussinov 2014, PLoS Comput Biol 10:e1003394.*

- **H6.1** All allostery is population redistribution on a pre-existing landscape;
  "pathways" are high-flux subsets of that redistribution, not causal channels.
- **H6.2** The allosteric site is **effector-specific** — one protein has different
  allosteric sites for different effectors.
- **STATUS:** H6.1 **UNTESTED** (no task addresses the unified-mechanism claim itself).
  H6.2 **PARTIAL/TESTED** — [[TASK-0229.003]] (2026-08-22) ran a live ASD lookup on 4
  targets (KRAS_G12C, BCR_ABL1, CARDIAC_MYOSIN, PTP1B). 3/4 confirmed single-site
  (all ASD records map to the same incumbent pocket). **BCR_ABL1 has a real second
  site**: PDB 5DC4, a monobody at the SH2-kinase interface, 24 contact residues
  (143–239) computed directly, confirmed disjoint from the active site, the incumbent
  myristoyl pocket, and the currently-reported top-5 hit list — so the specific
  already-published hit list needs no correction, but a full whole-protein re-score
  against the union key was **not** done (flagged as the honest remaining gap in that
  task's own Done section, not silently closed).
- **WHY IT MATTERS:** H6.2 attacks the **answer-key design.** A single ground-truth
  pocket per target assumes site uniqueness. A residue scoring high may be a genuine
  allosteric site for a different effector and is being counted as a false positive.
- **REMAINING OPEN VENUE:** H6.1 itself; the full whole-protein re-score against
  BCR_ABL1's union key ([[TASK-0229.003]]'s own flagged gap); extending the ASD audit
  beyond the 4 targets checked.
- **PDB-RETEST:** done for H6.2 on the 4 targets listed; not extended further.

### H4 — Ensemble Allosteric Model (EAM)
*Ref [4] Motlagh, Wrabl, Li & Hilser 2014, Nature 508:331.*

- **H4.1** Allosteric coupling is a partition-function quantity over folded/unfolded
  segment microstates (2^N), **not** a pathway on a contact graph.
- **H4.2** Allostery can occur with **zero mean structural change** — purely entropic
  (Cooper–Dryden dynamic allostery).
- **H4.3** Intrinsic **disorder amplifies** allosteric coupling.
- **H4.4** Coupling free energy does **not decompose onto graph edges.**
- **STATUS:** TESTED (H4.1, two independent measurements), PARTIAL (H4.2), UNTESTED
  (H4.3, H4.4).
  - **Harmonic proxy of H4.1, real-target retest**: [[TASK-0226]] (2026-08-21/22) reran
    the original non-target-structure measurement (|partial ρ|=0.773±0.162) on 5 real
    challenge targets with real annotated active sites and real SASA burial:
    **|partial ρ|=0.795±0.082 — confirms the finding, does not weaken it.** Harmonic
    stiffening is still not unfolding.
  - **Genuine EAM (H4.1's own real target), COREX-style**: [[TASK-0229.006]]
    (2026-08-23) built a sliding-window COREX approximation (`allostery/corex.py`),
    validated it (buried residues show higher κ_f than exposed, both targets,
    p<1e-6), and ran the register's own pre-registered "decisive negative control"
    (does EAM ranking disagree with propagation ranking) on both TASK-0209-VALID
    targets. **Neither closure the task anticipated**: EAM-vs-propagation Spearman
    ρ≈0.5–0.54 (KRAS_G12C 0.542, PTP1B 0.493), highly significant, real correlation
    with propagation — but far short of the ~0.85–0.95 agreement this register's other
    observables show when they turn out to just be distance detectors. A genuinely
    mixed result, not forced into either pre-registered bin.
  - **H4.2** (`dS_vib_global`, Cooper–Dryden proxy): [[TASK-0226]]'s real-target retest
    shows it escapes the proximity confound cleanly (|partial ρ|=0.082±0.050) — but its
    own required negative control (does it detect a real planted signal, not just
    ignore the seed by construction) is a single-condition check that did **not** reach
    significance (p=0.333) — inconclusive on whether the escape corresponds to carrying
    real allosteric signal, not yet a positive result.
- **WHY IT MATTERS:** This was the program's largest reference-level blind spot. The
  harmonic test shows it lands in the same confounded room on real data now, not just
  non-target structures. The genuine EAM is the only route to c-Myc/Max (1NKP) via H4.3,
  and it is the **type-correct quantum target**: partition-function estimation / Gibbs
  state preparation over 2^N, independent of what [[TASK-0229.006]]'s own real numbers
  show — that task's own forward-proposal write-up states this explicitly, with no
  advantage claim (out of scope per its own Intent Contract).
- **REMAINING OPEN VENUE:** H4.3/H4.4 remain fully untested. c-Myc/1NKP has no holo
  structure and was correctly excluded from [[TASK-0229.006]]'s headline as
  unvalidatable, not silently run anyway. H4.2's own negative control needs a proper
  LOD sweep (`scripts/mechanism_discriminating_plant.py` machinery exists,
  [[TASK-0168]]), not just the single strength/patch check [[TASK-0226]] ran.
- **PDB-RETEST:** done for H4.1 (both the proxy and the genuine EAM) and H4.2's escape
  measurement; not done for H4.3/H4.4 or H4.2's own negative-control LOD sweep.

### H5 — MWC / conformational selection; concerted transitions
*Ref [5] Changeux & Edelstein 2005, Science.*

- **H5.1** Pre-existing equilibrium between states; ligand selects rather than induces.
- **H5.2** Allosteric transitions are concerted across subunits in oligomers.
- **STATUS:** **UNTESTED — confirmed genuinely open** (direct search of the [[TASK-0229]]
  family and the wider task history found no task addressing either H5.1 or H5.2; this
  is one of only two hypotheses in this register with zero coverage anywhere, per
  [[TASK-0248]]'s own reconciliation pass, not inherited from this register's original
  framing without checking).
- **WHY IT MATTERS:** H5.2 interacts with the challenge's own Scope ("Included: the
  catalytic domains"). For any target whose mechanism is inter-subunit or inter-domain,
  **scope truncation removes the coupling from the model by construction** — a
  setup-validity failure orthogonal to, and possibly deeper than, the apo/holo contrast
  finding in TASK-0209.
- **HYPOTHESIS (needs verification, not asserted):** Cardiac Myosin may be exactly this
  case — mavacamten stabilises the super-relaxed state, and SRX is associated with the
  interacting-heads motif, a **two-head** arrangement. If so, a single catalytic-domain
  contact graph cannot represent the mechanism at all. **Verify against refs [22][23]
  and the 6C1H entity composition before writing this.**
- **OPEN VENUE:** Add an explicit "mechanism-in-scope?" gate per target, upstream of the
  apo/holo contrast gate. This strengthens TASK-0209 rather than duplicating it. This is
  the clearer of the two genuinely-open hypotheses this register carries forward as the
  input to a follow-up test task.
- **PDB-RETEST:** **YES** — check oligomeric/multi-domain state of 5TBY, 6C1H, 1OPL, 5MO4.

---

## Tier B — untested methods the challenge explicitly road-signs

### H1 — NMA-guided conformational sampling finds cryptic sites
*Ref [1] Zheng 2023, J Chem Phys 158:124127. **Reference number one in the document.***

- **H1.1** Cryptic sites are found by **sampling conformations** along coarse-grained
  normal modes and detecting pockets in the generated conformers — not by scoring
  residues on the apo structure.
- **H1.2** A small number of low-frequency modes spans the pocket-opening deformations.
- **STATUS:** **TESTED** — [[TASK-0229.004]] (2026-08-22) implemented Zheng's own
  pipeline faithfully (per-mode ANM displacement scanning, not the joint-ensemble draw
  this program had used instead) as a scored classical baseline, validated it on
  BCR_ABL1 (real/decoy specificity 92.5% vs. 36.7%), and scored it on both
  TASK-0209-VALID targets. **KRAS_G12C: AUC 0.728, beats this program's own quantum
  observable's point estimate (0.557–0.590) by a wide margin** — reported per this
  register's own "if it outperforms the quantum arm, that must be reported" venue —
  but the corrected compact-patch null (p=0.024) does not clear the program's own
  register-wide multiplicity bar (~0.00022), so it is explicitly **not** counted as a
  new significant positive. PTP1B beats floor but shows an internal disagreement
  between its residue-level and pocket-level statistics, disclosed not resolved.
- **WHY IT MATTERS:** This is the canonical classical method for the *reframed* problem
  the program itself converged on, it is MD-free, and it is the first citation in the
  challenge statement. Its absence was the most conspicuous gap in the baseline set.
- **PDB-RETEST:** done, both VALID targets.

### H2 — Cryptic pockets have a persistent-homology signature
*Ref [2] Koseki et al. 2025, J Chem Inf Model 65:5567 (CrypToth).*

- **H2.1** Cryptic pockets carry a topological signature (persistent cavities)
  separable from noise.
- **H2.2** TDA over an **ensemble** outperforms TDA on a single structure.
- **STATUS:** H2.1 **TESTED** (pre-existing, [[TASK-0142]], 2026-07-22, single apo
  structure — no real void detected above this register's own established noise floor
  on the 3 mandatory targets). H2.2 **TESTED — decisive negative**: [[TASK-0229.005]]
  (2026-08-23) built the ensemble extension (`ensemble_void_score`), and required a
  positive control before trusting it (does the known pocket show a persistent H2 void
  on the already-open **holo** structure, the best case for detecting one). **The
  positive control failed on both TASK-0209-VALID targets** (KRAS_G12C AUC 0.557,
  PTP1B AUC 0.116 — anti-correlated — both confirmed not a filtration-cap artifact).
  Apo-ensemble scoring was therefore gated off as untrusted per the task's own
  pre-registered rule; run anyway as an explicit ungated diagnostic, near chance on
  both targets. Also **decisive on PTP1B**, where [[TASK-0143]]'s own older
  graph-openness proxy (a different observable, not a re-test of this one) was
  INFEASIBLE — no null could even be constructed there.
- **WHY IT MATTERS:** CrypToth uses mixed-solvent MD, which constraint 3 forbids as
  *input* — but the **TDA layer is transferable** to an ENM-generated ensemble. This
  register's own filed framing called [1]+[2] stitched together the "highest-value
  construction in the document" — now tested, not just proposed.
- **PDB-RETEST:** done, both VALID targets, both single-structure and ensemble forms.

### H7 — Allosteric communication is non-equilibrium energy transport
*Ref [7] Stock & Hamm 2018, Phil Trans R Soc B 373.*

- **H7.1** Allosteric communication is a **non-equilibrium** vibrational energy-transport
  process (T-jump / impulse response), not an equilibrium correlation.
- **H7.2** Energy-transport pathways ≠ equilibrium correlation pathways.
- **STATUS:** **TESTED — clean negative.** [[TASK-0229.007]] part (b) (2026-08-23) built
  a closed-form finite-time GNM impulse-response observable (`impulse_response.py`,
  `integrated_response`; verified `C(t=0)` reproduces this program's own existing static
  GNM covariance exactly) and, per this register's own Constraint (must pass an
  independence test before being scored against labels, [[TASK-0211]]'s precedent),
  ran it through [[TASK-0199]]'s own effective-rank pipeline unmodified on all 5 of that
  task's targets. **`new_axis = False` on all 5** — delta_noise exceeds delta_real every
  time, so it is not scored against labels, reported as a clean negative rather than a
  new axis. Separately, [[TASK-0226]] (2026-08-21/22) tested a related but distinct
  steady-state quantity (`transmission_E0`, Landauer transmission, not an impulse
  response) and found it **among the most confounded** observables measured
  (|partial ρ|=0.795) — explicitly flagged there as not a test of ref [7]'s actual
  non-equilibrium claim, a related measurement only.
- **WHY IT MATTERS — REFRAMING OPPORTUNITY:** [7] said the correct comparison class for
  a CTQW might be non-equilibrium impulse transport rather than equilibrium correlation.
  Tested now: it is not a materially different axis from what this register already had.
- **PDB-RETEST:** done — `integrated_response` on 5 targets; `transmission_E0` on 5
  targets (different task, different question).

### H15 — Two-state ANM captures apo↔holo transitions
*Ref [15] Das, Gur, Cheng, Jo, Bahar & Roux 2014, PLoS Comput Biol 10:e1003521.*

- **H15.1** Transitions between two known endpoint structures are modelled by a simple
  two-state ANM.
- **H15.2** The transition is dominated by a few soft modes.
- **STATUS:** **TESTED — mixed, on all 7 of TASK-0209's real-drug-ligand targets.**
  [[TASK-0229.007]] part (a) (2026-08-23) computed whole-structure cumulative overlap
  CO(50) fresh for all 7. **Planned Validation (CO(50), KRAS_G12C > BCR_ABL1) FAILS**
  (0.766 < 0.858) — whole-structure CO is confounded with size/flexibility (BCR_ABL1
  429 residues, CARDIAC_MYOSIN 698), not a clean readout of TASK-0209's contrast rule.
  A pocket-restricted variant, built in direct response, **passes the one specific
  pre-registered comparison** (0.547 > 0.316) but **does not generalize**: GLUCOKINASE
  (TASK-0209-INVALID) scores 0.676, above both VALID targets. CASPASE7's
  pocket-restricted value could not even be computed (zero apo/holo alignment
  correspondence for its labeled pocket, a real data gap, not silently worked around).
- **WHY IT MATTERS:** This was proposed as the **principled instrument for TASK-0209**
  — turning a structural-inspection judgement call into a graded measurement. It
  partially succeeds (the one pre-registered comparison it was built to answer) and
  partially fails (as a general-purpose 7-target instrument) — both halves matter and
  neither should be quoted without the other.
- **PDB-RETEST:** done, all 7 targets, both variants.

### H8 — Markovian random walk on the residue network
*Ref [8] Chennubhotla & Bahar 2007, PLoS Comput Biol 3:1716.*

- **H8.1** Signal propagation is approximated by a Markov random walk on the residue
  affinity network.
- **H8.2** Hitting/commute times identify communication hubs and pathways.
- **STATUS:** **TESTED, on real challenge targets** (this line previously cited
  "TASK-0210" — that was the external drop's own pre-repo filename; the repo-side task
  is [[TASK-0226]], re-indexed on filing to avoid colliding with this repo's own
  unrelated, already-completed TASK-0210). Original non-target-structure estimate:
  |partial ρ(distance | burial)| = 0.711 ± 0.125. **[[TASK-0226]]'s real-PDB retest
  (2026-08-21/22, 5 real targets, real annotated active sites, real SASA burial):
  |partial ρ|=0.755 ± 0.062, ρ_burial=0.610 — confirms and sharpens the finding.**
- **WHY IT MATTERS:** [8] is one of the three references the challenge cites in Section 5
  when it *mandates* the elastic-network assumption. Showing that the mandated classical
  baseline carries the same confound converts the program's proximity finding from
  "our observable is broken" into "the observable class the challenge specifies is
  broken" — and it directly discharges objective 4.2 (comparison to classical analogs).
- **PDB-RETEST:** done, real challenge targets (not the bundled structures the original
  drop used) — this line's own prior "YES" is now satisfied, not still outstanding.

### H16 — GNM slow-mode minima mark functional/binding sites
*Ref [16] Erman 2006, Biophys J 91:3589.*

- **H16.1** GNM reproduces experimental B-factors (per-target model-validity check).
- **H16.2** Binding sites sit at **minima of the slowest modes**.
- **STATUS:** H16.1 **UNTESTED — confirmed genuinely open** (direct search for a
  B-factor-correlation model-validity check across the task history found none; the
  second of the two hypotheses in this register with zero coverage anywhere).
  H16.2 **TESTED, real challenge targets** (same TASK-0210→[[TASK-0226]] re-index note
  as H8 above). Original non-target estimate: |partial ρ|=0.292 ± 0.218.
  **[[TASK-0226]]'s real-PDB retest: |partial ρ|=0.496 ± 0.193** (range [0.01, 0.76])
  — a real, reportable difference from the non-target estimate, not smoothed over:
  slow-mode minima escape the proximity confound **less cleanly on real targets** than
  the original non-target measurement suggested. A follow-up negative control
  ([[TASK-0226]]'s own planted-signal check, KRAS_G12C) found nominal enrichment
  (p=0.028) that does **not** survive even a 2-comparison Bonferroni correction — a
  weak, uncorrected-significant hint, not a confirmed positive.
- **WHY IT MATTERS:** It is a near-free classical baseline this program had not
  reported, and (with `dS_vib_global`) one of only two observable families found so far
  that meaningfully escape the proximity confound. Being **seed-blind**, it cannot
  answer "connectivity to the active site" and addresses objective 4.1 only under the
  "in most cases" qualifier in the challenge text.
- **REMAINING OPEN VENUE:** H16.1 itself (add B-factor correlation as a per-target
  model-validity gate, as this register's own prior text already proposed — still not
  built). A proper LOD sweep for H16.2's own negative control, same gap as H4.2 above.
- **PDB-RETEST:** done for H16.2; H16.1 remains fully open.

---

## Tier C — quantum-side road signs

### H10 — Non-local channels via quasiprobability / circuit cutting
*Ref [10] Mitarai & Fujii 2021, Quantum 5:388.*

- **H10.1** Non-local operations are simulable by local channels at sampling overhead
  exponential in the number of cuts (γ-factor).
- **STATUS:** **TESTED (paper-level, per this register's own original venue framing —
  "cheap, scores under Feasibility").** [[TASK-0229.002]] (2026-08-22) verified the
  citation directly (confirmed O(9ⁿ) overhead without inter-subcircuit classical
  communication, O(4ⁿ) with it) and computed a **real, measured cut count**, not an
  assumed one, by partitioning each mandatory target's actual `H_new` coupling graph
  into NISQ-sized islands: cut counts 159–510 depending on target, sampling overhead
  10²²⁴–10⁴⁸⁷ in the cheaper (4ⁿ) regime — exceeding the observable universe's ~10⁸⁰
  atoms by 15–400+ orders of magnitude on every mandatory target. **Reinforces
  [[TASK-0182]]'s `FAULT_TOLERANT_ONLY` verdict from an independent direction** (a
  different failure mode — sampling overhead, not raw qubit/gate count — reaching the
  same conclusion); no discrepancy to reconcile.
- **WHY IT MATTERS:** This is the organisers' road sign for secondary objective 4.2 —
  "demonstrate a method for coarse-graining the protein structure and prove that this
  compression retains the essential topological signal." Circuit cutting is the
  *named* tool for mapping proteins that exceed qubit count.
- **REMAINING OPEN VENUE:** a size-balanced (non-Louvain) partition might change the
  exact cut count, but not the conclusion — the overhead is astronomical by 100+ orders
  of magnitude either way, explicitly not attempted as out of this task's own
  paper-level scope.

### H11 — Open-system dynamics on quantum hardware via SVD/dilation
*Ref [11] Oh, Krogmeier, Schlimgen & Head-Marsden 2024, ACS Phys Chem Au 4:393.*

- **H11.1** Non-unitary (open-system) dynamics can be implemented on a gate-based device
  via singular-value decomposition / dilation.
- **STATUS:** **TESTED (paper-level).** [[TASK-0229.002]] (2026-08-22) verified the
  citation directly and found it **directly on-topic, not just adjacent**: the paper's
  own worked example is FMO excitonic energy transport, the same physical phenomenon as
  this program's own ENAQT measurements. **This is the one route anywhere in this
  register that clears the qubit-count bar** — 1 ancilla qubit independent of system
  size, gate count O(4^d) — **but only under an amplitude/log-scale-encoded register
  this project has never built or costed** (projected: d≈9-10 system qubits for N up to
  704, ~10⁵-10⁶ gates — honestly labelled as a projection, not a built result).
  [[TASK-0182]]'s own resource table uses one qubit per residue throughout; there is
  nothing to reconcile with H11, only a real, unbuilt, now-disclosed alternative where
  previously there was silence on this citation entirely.
- **WHY IT MATTERS:** This is the **cited hardware implementation path for the ENAQT arm.**
  Without it, the interior-γ dephasing optimum is a classical Lindblad solve with no
  quantum execution story, and constraint 1 ("credible path to execution on near-term or
  fault-tolerant hardware") is not discharged. ENAQT is currently the program's most
  defensible surviving quantum-mechanism claim; this is what makes it a *quantum* claim.
- **REMAINING OPEN VENUE:** actually costing/building the amplitude-encoded register —
  explicitly out of [[TASK-0229.002]]'s own scope (paper-level only).

---

## Tier D — context and target-specific

- **[3] Nussinov & Tsai 2013** — allosteric drugs are more selective; allosteric sites are
  less conserved. **UNTESTED.** *Open venue:* a conservation-only baseline is a strong
  null — if sequence conservation alone predicts as well as the quantum score, the
  quantum arm adds nothing. Also a **label-leakage risk** if conservation enters features.
  Requires MSA; not runnable offline.
- **[14] Lu, Li & Zhang 2014** — allosteric sites are shallower/more polar than orthosteric.
  *Open venue:* a shape/physicochemical-prior baseline, and a possible confound generator.
- **[18][19] Ostrem 2013 / Canon 2019 (KRAS)** — **H18.1:** the switch-II pocket is
  *induced* by covalent ligand and does not pre-exist in apo. **This directly supports
  the TASK-0209 reasoning and the conformational-search reframing, and should be cited
  where that argument is made.**
- **[20][21] Wylie 2017 / Schoepfer 2018 (BCR-ABL1)** — **HYPOTHESIS, verify:** the
  myristoyl pocket is a *physiological* autoinhibitory site normally occupied by the
  N-terminal myristate, i.e. it may not be "cryptic" in the sense the challenge assumes.
  1OPL is the autoinhibited structure. **Check occupancy state before relying on the
  cryptic framing for this target** — this bears directly on TASK-0209's validity call.
  (Already independently addressed by TASK-0209's own MYR-occupancy finding, Finding 2
  of `documentation/PHASE1_SUBMISSION_DRAFT.md` — pre-existing, not a TASK-0229 item.)
- **[22][23] Green 2016 / Anderson 2018 (myosin)** — see H5.2 above, still fully open.
- **[24] Dang 2017** — c-Myc undruggability; disorder. Connects to H4.3, which
  [[TASK-0229.006]] explicitly did not test (c-Myc excluded as unvalidatable, no holo
  structure) — still the only principled handle on 1NKP, still untested.
- **[25] ASD v3.0** — already registered. See H6.2 above — the multi-site audit is now
  done on 4 targets via [[TASK-0229.003]].
- **[12] Scannell, [13] wwPDB, [17] Qiskit** — context/tooling, no testable hypothesis.

---

## Question for the Cleveland Clinic team

The challenge statement contains an **internal tension** worth putting on record before
the submission is written:

> **Section 5 (Scope and Assumptions) mandates the elastic-network hypothesis — "the
> topology of the contact network is the primary driver of signal propagation" — citing
> [8][15][16]. Section 2 cites [4] and [9], which respectively hold that coupling is an
> ensemble/partition-function quantity that does not decompose onto graph edges, and that
> clean non-allosteric negatives may not exist. Which governs for scoring?**

Their answer determines whether a topology-level negative result reads as a failed
submission or as a finding about the problem statement. Get it in writing.

**Status update on this question's own load-bearing citations, per this reconciliation
pass**: [8], [15], and [16] are now all real-target TESTED (see Tier B above); [4] and
[9] are now PARTIAL/TESTED rather than UNTESTED. The tension itself is unresolved (this
is a question for the organisers, not something a repo task can close), but it is no
longer a tension between one tested side and one untested side — both sides now carry
real measurements.
