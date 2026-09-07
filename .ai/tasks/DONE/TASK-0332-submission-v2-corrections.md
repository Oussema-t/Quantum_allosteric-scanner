# TASK-0332 — Submission v2: Berke's structural corrections, promote TASK-0318, team §7

- Status: Done
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

## Done (2026-09-07, Implementer D)

All edits applied to both twins in one pass, `doc_parity.py` verified after
every batch, final check: `parity OK` (figures / code identifiers / document
title / section headings / heading ORDER all match).

**Item 1 — MYR/1OPL fixed.** §1 Finding 2 rewritten: BCR-ABL1's `MYR` is now
correctly framed as the physiological autoinhibitory myristate ligand (Nagar
et al. 2003), the textbook mechanism, not a contaminant — asciminib named as
the myristate-mimetic existence proof, adjacent to the correction as
instructed. GLUCOKINASE/`MRK` and PKR's allosteric modulator remain
genuinely unexplained; the shared consequence (scoring confound) is kept,
only the interpretation changed. Checked: no repeat of the old wording in
`REVERSE_CTQW_BRIEF.html` (none found) or the archived DRAFT (frozen
historical record, [[TASK-0339]]'s own scope, not touched here).

**Item 2 — cryptic/allosteric taxonomy.** New table at the top of §1 states
Berke's classification (BCR-ABL1: allosteric, not cryptic; KRAS: both;
cardiac myosin: allosteric, not cryptic, not even single-molecule — flagged
into Appendix C rather than carried as an ordinary target). Folded in the
collaborator's own median-hop-0 measurement for cryptic datasets as an
explicit "cryptic ≠ distal, now measured" finding, per the task's own
instruction to state it as a real contribution, not just a caveat.

**Item 3 — clinical paragraph added to §4**, Berke's text lightly adapted,
kept adjacent (same terms — asciminib, myristoyl site) to item 1's
correction as instructed.

**Item 4 — TASK-0318 promoted into §2, retitled in the same edit.** Replaced
§2(d) and its notice box with a new "What we already have — four positive
results" subsection carrying, in the Brief-update's own specified order: (1)
TASK-0318 — retitled away from "ceiling" language (now "a validated upper
bound within one specific feature span"), 0.5949/0.6203/p=3.3e-6/0.6017,
**with the cold-clone byte-for-byte reproduction now stated directly**
(0.5948718035160693, this register's own [[TASK-0340]] verification, which
this session also performed) — a direct Criterion-2 asset, per the Brief's
own instruction, folded into §2 itself since the mandated 7-item ToC has no
separate reproducibility section (adding one would re-open [[TASK-0339]]'s
own just-closed ToC-violation finding); (2) TASK-0334/HYP-P25's mechanism —
**cluster-robust CORRECTED numbers used** ("7 of 8 combinations clear,
cluster rho −0.34 to −0.50, p=0.004–0.038, one borderline at p=0.058"), NOT
the original row-level "−0.408/−0.614" table the filing text itself carried
— [[TASK-0337]]'s own explicit instruction, checked and followed; (3)
TASK-0331/HYP-P21's cohort defect, three ways; (4) TASK-0328's pocket-block
null (45/110→0/110, 33/80→1/80). Propagated the same 0.6203-median number
into §4's Expected-Impact table and Appendix A's claims-ledger row
(previously both still said "0.595", now consistent across the whole
document), and fixed two stray "§2(d)" references elsewhere (§5, Appendix
C) that would have dangled after the restructure.

**Item 5 — §7 team.** Berke's label/role corrected to the supplied text.
Oussema's and Berke's bios added, replacing the "INCOMPLETE — awaiting
detail" placeholder, condensed per instruction (Oussema's awards list cut to
two placements + the thesis + the toolset). **Not done**: lifting Berke's
"why classical detection fails" paragraph into §1 — the paragraph's actual
text was never supplied into the repository, only referenced as something
Berke would provide; fabricating content and attributing it to a named
collaborator was not an option. Flagged here rather than silently dropped;
recorded in `REVIEW_TARGETS.md` would be the next place to track it if not
resolved before freeze.

**Brief-update items also applied**: v2 pipeline results confirmed absent
from the draft (nothing to remove); ligand-contamination and
distal-denominator caveats attached at every ASBench-resting claim in the
new §2 section; three Appendix-C additions landed (apo-ligand veto leak
4.2×, ASBench/PASSer training contamination, TASK-0328's unreproducible
`hash()` seed); [[TASK-0333]]/[[TASK-0340]]'s cold-clone reproducibility
stated in §2 as instructed.

**Page budget — measured, not silently exceeded.** Body (§1–7) is now
**3174 words**, up from [[TASK-0339]]'s own 2233-word baseline (+941,
+42%) — this task's own required content (four positives, taxonomy table,
clinical paragraph, two bios) is inherently additive and TASK-0339's own
Done section flagged exactly this risk in advance ("+700–900 words with no
cuts named"). One trim pass applied to the new §2 section during drafting
(saved ~230 words) without cutting load-bearing content. **At TASK-0339's
own word-per-page estimate this body is very likely over the 6pp limit now**
— a further trim-and-render pass, with an actual PDF page count (neither
this task nor [[TASK-0339]] had a renderer available), is recommended
before freeze. Not attempted here: further cuts risk removing content this
task was specifically asked to add, and a real page count needs a real
renderer, not another word-count proxy.

**Files**: `documentation/PHASE1_SUBMISSION_V1.{md,html}`, both, one commit,
parity-checked per the task's own Constraint.
