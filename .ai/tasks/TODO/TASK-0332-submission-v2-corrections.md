# TASK-0332 — Submission v2: Berke's structural corrections, promote TASK-0318, team §7

- Status: TODO — brief updated 2026-09-06, read the update section before starting
- Owner: **Reviewer thread** (drafting) → **Berke** (structural sign-off) → repo owner
- Priority: High — 9 days to 15 September; one item is a factual error a structural biologist will catch on sight
- Filed: 2026-09-06 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0318]], [[TASK-0307]], [[TASK-0278]], [[TASK-0331]], [[TASK-0329]], [[TASK-0254]]
- Targets: `documentation/PHASE1_SUBMISSION_V1.{md,html}` — both, in the same
  commit, verified with `.ai/tools/doc_parity.py`

## 1. MYR in 1OPL is not an unexplained ligand — it is the mechanism

`PHASE1_SUBMISSION_V1.md:78` reads: *"An unexplained ligand holds the 'apo'
pocket open. BCR-ABL1's `1OPL` carries `MYR` with 75% overlap…"*

`MYR` is **myristate**, the physiological autoinhibitory ligand of that exact
pocket, and the reason the structure was solved (Nagar et al. 2003). It docks
into the C-lobe myristoyl pocket and clamps the αI helix, which reorganises the
SH2–SH3 clamp against the kinase domain and autoinhibits it. **Asciminib is a
myristate mimetic designed for that site.**

So the sentence inverts the case: we cited it as an unexplained contaminant
when it is the textbook example of the exact mechanism we claim to be chasing.
Rewrite so the *measurement* survives — the pocket genuinely is held open in
that structure, which is why the score is confounded ([[TASK-0278]]) — while
the *interpretation* becomes "occupied by its physiological effector", not
"unexplained". Verify the same wording is not repeated elsewhere in either file
or in `REVERSE_CTQW_BRIEF.html`.

## 2. Fix the cryptic / allosteric taxonomy throughout

These are orthogonal axes and the draft conflates them. Berke's classification,
to be applied consistently:

| site | allosteric | cryptic |
|---|---|---|
| BCR-ABL1 myristoyl | yes | **no** |
| KRAS switch-II | yes | **yes** |
| cardiac myosin (mavacamten) | yes | **no** — and not even a single-molecule property |

The mavacamten note matters beyond wording: if its site is not a
single-molecule property, a single-structure contact-graph method **cannot**
represent it, and that belongs in the disclosed-limitations appendix rather
than being quietly carried as a benchmark target.

This also sharpens a finding we already own: the collaborator's benchmark
measures **median hop = 0** for the cryptic datasets — cryptic ≠ distal, now
measured ([[TASK-0331]]). Say it explicitly; it is a real contribution and it
explains why cryptic-pocket predictors were never going to solve our problem.

## 3. Add the clinical paragraph to §4 (Berke's text, adapt lightly)

> Cryptic allosteric sites matter clinically because they are the route to
> targets that orthosteric chemistry cannot reach — proteins whose active sites
> are too polar, too shallow, or too conserved across a family to permit a
> selective ligand. Asciminib is the existence proof: a myristoyl-site
> inhibitor that retains activity against the ATP-site resistance mutations
> that defeated four generations of orthosteric TKIs. The reason there are not
> more asciminibs is not that the sites are absent. It is that we cannot
> currently tell a real one from a scoring artefact, prospectively, on a
> protein where the answer is not already known. That is the capability this
> instrument is meant to certify.

Keep the asciminib sentence adjacent to the corrected MYR text from item 1 —
they are the same story and currently contradict each other.

## 4. Promote [[TASK-0318]] into §2, and caveat its title in the same edit

**Residual AUC 0.5949 mean / 0.6203 median, p = 3.3×10⁻⁶, LOPO over 74 protein
clusters, holding at 0.6017 with proximity features deleted outright.** Drivers:
`V_C`, `chiral_circulation`, `persistent_h2_void`, `degree`. It is the
strongest positive number in the register and it currently sits in a DONE file
while the draft leads with negatives.

The evaluation criteria make this concrete: criterion 1 (KPI / quantum
advantage) scores badly for a negative-result submission no matter what we
write. **Criterion 2 (evidence and validity of approach) is where we win**, and
0.60 is the one number that reads as a validated approach rather than a
catalogue of closures.

**Same edit, not a later one**: the title *"ceiling of the contact-graph input
space"* overclaims. What was measured is a gradient-boosted fit over **19
hand-built scalar functionals** — an upper bound *within that feature span*,
but a **lower** bound on what arbitrary functions of that graph can achieve. As
a "ceiling" it forecloses the GNN route on evidence that does not bear on it.
The task's own §Constraints already says a ceiling is "only decisive in the
negative direction", so this is a title/scope fix, not a retraction. A referee
who catches the overclaim will discount the surrounding negatives too.

## 5. §7 — team

- **Berke's label** → "Computational biophysics / structural chemistry"; role →
  "target selection and mechanistic classification, structural validity
  auditing, ensemble and free-energy methodology, biological interpretation."
- **Oussema's bio** — supplied (M.Sc. Quantum Computing Technology, UPM;
  M.Sc. Quantum Engineering in progress, Leibniz Hannover; VQE/annealing thesis
  benchmarked against DFT/CASSCF/HF; PushQuantum 1st, OPUS Challenge winner,
  NYUAD 2nd, Braunschweig 3rd, IBM Quantum Challenge honourable mention;
  Qiskit/PennyLane/QUBO/hybrid QML; 2 years simulation engineering at VW R&D).
  **Condense to the submission's own §7 register** — the awards list runs long
  against the other two entries; keep the thesis, the toolset and one or two
  placements.
- **Berke's bio** — supplied (PhD FMP Berlin / TU Berlin, K2P channel
  activation/inhibition by all-atom MD and enhanced sampling; TREK-2 coupling
  from selectivity filter through M4 to the fenestration sites; metadynamics
  and OneOPES; two first-author papers, one under review at Nature
  Communications; GROMACS/AMBER/PLUMED/AlphaFold/RFdiffusion/ProteinMPNN/HPC).
  His "why classical detection fails" paragraph is strong §1 material — lift
  it there rather than burying it in §7.

## Constraints

- **Both files, one commit, parity-checked.** `.ai/tools/doc_parity.py` exists
  precisely for this; a pre-commit hook on these two paths was offered and
  never wired ([[TASK-0307]] follow-up) — wire it here.
- Anything claimed on ASBench carries the ligand-contamination caveat
  ([[TASK-0329]]); anything claimed as a propagation negative carries the
  distal-denominator caveat ([[TASK-0331]]).
- **Do not** put the per-family Hamiltonian table or the "40 proteins / 19
  families" counts in the draft until [[TASK-0327]] and [[TASK-0330]] report.

## Brief update, 2026-09-06 — nine dependencies landed after filing

Read this section together with the items above; where they conflict, this wins.

### The v2 pipeline results must NOT go in the draft. [[TASK-0336]] settled it.

The filing said "not until [[TASK-0327]] and [[TASK-0330]] report". 0330 was
closed unrun; **[[TASK-0336]] answered it decisively.** Once every arm is put on
one object (round-2's own veto-survivor pockets) with matched multiplicity and a
chance correction:

| arm | ALL (n≈276 fam) | distal (n=48 fam) |
|---|---|---|
| CTQW `hnew\|full\|p_avg` | obs 4, chance 1.25, **excess +2.75**, 95% CI [1.09,10.24] | obs **0**, chance 0.52, **excess −0.52** |
| fpocket_drug / passer_rank / pocket_size | obs 5, **excess +3.75**, 95% CI [1.62,11.67] | obs 0, excess −0.52 |

**Corrected, 2026-09-07 ([[TASK-0338]]) — do not write "classical beats CTQW".**
4 vs 5 is not a real gap: exact Poisson 95% CIs heavily overlap, and the paired
exact test on the identical 276 families (McNemar — this is one paired
comparison, not two independent samples: 1 discordant family total, CTQW-only
0 / classical-only 1) gives p=1.0. **The exclusion sentence for the draft is
methodological, not a scoreboard**: under matched multiplicity, a matched
candidate set and a matched null, *no arm — quantum or classical — clears more
than 5 of 276 families, and the arms are statistically indistinguishable from
each other and barely distinguishable from chance.* Exclude the v2 pipeline
results on that basis (best-of-221-cells selection does not survive
multiplicity matching, 69→4) — a referee can't turn that argument around the
way they can turn around "we lost by one family." Full numbers, both the
original table and the CIs/paired test, are in
`matched_comparison_result.json`'s own `family_table` and
`paired_exact_tests_all_split`.

The CTQW clears zero distal families either way. The README's headline distal margin (19 vs 1) does not
survive matching — 0.52 is less than one family clearing by luck. Do not quote
226/131, 40/19, the per-family Hamiltonian table, or the distal margin.

### The strongest NEW result is [[TASK-0334]] / `HYP-P25` — put it in §2

Pipeline hit-rate vs. drug-pocket distance from the active site, Spearman ρ:

| | pre-veto held-out (n=64) | post-veto held-out (n=44) |
|---|---|---|
| **pipeline** | **−0.408** (p=8.1e-4) | **−0.614** (p=9.3e-6) |
| PASSer (specificity control) | +0.111 (p=0.38) | +0.207 (p=0.18) |
| random arm | +0.307 | +0.306 |

The walk degrades monotonically with distance; the ML baseline on identical
pockets does not. **This is a measured mechanism, not a null** — and it is the
answer to "why does the quantum method fail", which is a far stronger §2 claim
than the failure itself. Note the cohort is entirely `is_distal` (S5's own
restriction), so this is a within-distal dose-response over 2–13 hops, not a
distal-vs-proximal contrast. State that scope.

**Supersedes item 1's open question**: "actively subtracting value" is now
explained and should be replaced by the mechanism, not repeated.

### §2 should carry four positives, in this order

1. **[[TASK-0318]]** — residual AUC 0.5949/0.6203, p=3.3×10⁻⁶, 74 clusters,
   0.6017 with proximity deleted. Retitle in the same edit (item 4 above).
   **The 0.6017 number is now regenerable, not just committed** ([[TASK-0338]]
   Part B, 2026-09-07): `task0318_input_space_ceiling.py --phase-b-only
   --exclude-proximity` reproduces the committed
   `no_proximity_feature_check.json` byte-for-byte from the existing cache —
   safe to cite as a validated, executable number.
2. **[[TASK-0334]]/`HYP-P25`** — the mechanism, with its specificity control.
3. **[[TASK-0331]]/[[HYP-P21]]** — the cohort defect, measured three independent
   ways: distal subset cannot detect proximity itself (p=0.89), ~30% of pairs
   covalently adjacent, 40/40 ASBench structures ligand-open.
4. **[[TASK-0328]]** — methodological: a pocket-block null takes BH-FDR
   survivors from 45/110 to **0/110**. A reusable contribution in its own right.

### Appendix C additions (disclosed defects)

- **[[TASK-0329]]**: the apo-ligand veto exception leaks — the true pocket is
  **4.2×** more likely than an arbitrary candidate to survive *only* via that
  exception (13.5% vs 3.2%, paired within-protein).
- **[[TASK-0327]]**: ASBench is PASSer's training data; CASBench is held out.
  Any ASBench-based comparison against PASSer is contaminated.
- **[[TASK-0328]]**: the upstream null seed was non-reproducible
  (`hash()` with `PYTHONHASHSEED` unset); patch written, not yet landed upstream.

### Already done — inherit, do not redo

[[TASK-0335]] has landed scope corrections on [[TASK-0320]] and [[TASK-0325]];
copy those caveats forward rather than re-deriving them. [[TASK-0333]]'s
container reproduces the §2 headline number byte-for-byte from a cold clone —
state that in the reproducibility section, it is a direct criterion-2 asset.
