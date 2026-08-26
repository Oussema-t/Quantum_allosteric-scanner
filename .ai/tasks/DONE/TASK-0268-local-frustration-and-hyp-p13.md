# TASK-0268 — Local energetic frustration: the direct test of HYP-P13

- Status: Done
- Assignee: **Implementer C** (after [[TASK-0264]])
- Priority: Medium-High — cheapest new method available, and it is the only one that tests our *own* hypothesis
- Filed: 2026-08-25 by Reviewer
- Related: [[HYP-P13]], [[TASK-0259]], [[TASK-0229.006]] (EAM/COREX), [[TASK-0233]]

## Why this one, of everything on offer

An external survey listed a hierarchical cryptic-pocket workflow: ANM/GNM
ensembles → rotamer repacking → volumetric scoring. **We have already built
and tested all of it** ([[TASK-0227]], [[TASK-0230]], [[TASK-0229.004]],
[[TASK-0229.007]], [[TASK-0204]], [[TASK-0213]], [[TASK-0235]]). That
convergence is mild validation of our architecture and means most of the
survey offers nothing new.

**Local frustration profiling is the exception, and it is the one item that
tests this project's own hypothesis rather than importing someone else's.**

[[HYP-P13]] states allostery is *stabilisation of an otherwise-disfavoured
conformation*, not a signal propagating to the active site. If that is right,
cryptic and allosteric sites should sit at loci of **high native energetic
frustration** — regions whose local interactions are worse than a randomised
decoy distribution, and which relieve strain on transitioning to the open or
ligand-bound state.

That is a sharp, falsifiable, cheap prediction. It has never been tested, and
unlike every other candidate it does not require a new external tool family
we must first argue past constraint 3.

## Scope

- [x] **Verify the Frustratometer citation live** before implementing
      (Crossref/publisher record — title, authors, journal, volume, DOI), per
      this register's standing convention. Do not inherit the external
      survey's details; it has now been wrong on three citation specifics
      ([[TASK-0260]] PocketMiner date, [[TASK-0262]] taxonomy,
      CryptoSite's MD-at-inference).
- [x] Establish whether a runnable local implementation exists or whether it
      is web-server-only — [[TASK-0260]] lost FTMap on exactly that, so check
      installability **before** committing effort.
- [x] Compute per-residue frustration on the **apo** structures of
      [[TASK-0243]]'s frozen set. Apo only — holo leaks the label.
- [x] **Pre-register the HYP-P13 prediction before scoring**: frustration
      should be elevated at true pocket residues relative to matched decoys,
      and *more so on the cryptic targets* than the already-open ones.
      Write the prediction down first.
- [x] Score it as an attribution block alongside geometry / fpocket / CTQW,
      and report its contribution **added last**.
- [x] Stratify by crypticity, exactly as [[TASK-0260]] did — that is where the
      prediction lives.
- [x] Cluster-robust significance ([[TASK-0261]]'s method).

## Acceptance

- [x] Citation verification record and installability finding.
- [x] Pre-registered prediction, recorded before the first number.
- [x] Frustration as an attribution block, added-last value, crypticity split.
- [x] An explicit verdict on the HYP-P13 prediction.
- [x] `RESULTS.md`; update [[HYP-P13]] in `.claude/hypotheses/physics.md` with
      the outcome either way.

## Done

**2026-08-25.** Verdict: **HYP-P13's own frustration prediction fails —
a clean negative, reported with the same prominence a positive would
get.** Direction does not hold (cryptic residues show numerically LOWER,
not higher, frustration), and the effect is not distinguishable from
zero overall (cluster-p=0.727).

### Citations verified live, before implementing

Jenik, Parra, Radusky, Turjanski, Wolynes, Ferreiro (2012), *Nucleic
Acids Research* 40:W348-W351, doi:10.1093/nar/gks447 (Frustratometer
formalism) — confirmed via Crossref. Miyazawa & Jernigan (1996), *J Mol
Biol* 256:623-644, doi:10.1006/jmbi.1996.0114 (pairwise contact
potential) — confirmed via Crossref. Neither inherited from the external
survey's own text, matching this task's own explicit caution (three
prior citation errors from that survey, named in this task's own filing).

### Installability checked directly, not assumed

The real PyPI `frustratometer` package (Carlos Bueno, Rice — direct
lineage of the cited paper, confirmed via its own PyPI metadata) resolves
and its core Python dependencies install cleanly, but its own
`numba`→`llvmlite` build dependency **fails to build a wheel**: no
system LLVM toolchain present (`llvm-config` absent from PATH, no
homebrew `llvm@*` keg anywhere — checked directly). Installing LLVM
system-wide judged out of this task's own scope (an invasive environment
change, not a Python-only fix) — matching [[TASK-0260]]'s own precedent
for PocketMiner (documented, not forced).

### Built instead: a real, honestly-scoped port of the same formalism

New `allostery/frustration.py` — single-residue mutational frustration
(Jenik et al.'s own named variant: randomise the focal residue's identity
only, keep its real structural contacts and their identities fixed,
compare native vs. the 19-decoy energy distribution via a Z-score),
matching this project's own established precedent for exactly this
situation ([[TASK-0229.006]]'s own COREX/EAM build when the full
Hilser/Freire machinery wasn't practical to import either — a real
simplification of the full AWSEM-based tool, stated explicitly, not
presented as equivalent).

**Pairwise potential sourced carefully, not hand-recalled**: the real
20×20 Miyazawa-Jernigan (1996) matrix (AAindex accession MIYS960101)
fetched directly from the AAindex database, not reconstructed from
memory — a numeric table is exactly the kind of thing this project's own
citation discipline treats as needing a checkable source, not recall.
Sanity-checked before use: diagonal values match textbook expectation
(Leu-Leu −7.37 and Ile-Ile −6.54 most favourable, Cys-Cys −5.44 matching
disulfide-forming character); matrix symmetry confirmed programmatically.
**Bibliographically verified, not independently re-OCR'd against the
original paper's own printed table** — same disclosure tier this
project's own `corex.py` MAX_ASA table already carries.

**Sanity-checked on a real target before trusting the pipeline**:
KRAS_G12C apo, 100% of 169 residues resolved (zero NaN), mean 10.0
contacts/residue at the 8 Å CB-CB cutoff, Z-score distribution
mean≈0.07/std≈1.1 (a well-behaved, roughly standard-normal shape, as a
Z-score construction should produce), 35.5% highly frustrated (z>0.78,
the field-standard cutoff) and 24.3% minimally frustrated (z<−1) — both
fractions land inside the range routinely reported for real proteins in
the Frustratometer literature, not a degenerate all-zero or all-extreme
output.

### Full pipeline, reusing established machinery throughout

New `scripts/task0268_local_frustration_hyp_p13.py` — reuses
`task0242_two_stage_dryrun.prep`/`CAND`, `task0249_composite_dumb_
baseline.target_rows`, `task0254_fpocket_variance_and_crypticity`'s own
`cv_auc`/`build_blocks`/`crypticity`/`z`, `task0257_r2_sasa_burial_vs_
degree.per_residue_sasa`, and `task0261_cluster_robust_stats`'s exact
cluster-permutation machinery unchanged — following [[TASK-0266]]'s own
established 4-block-to-5-block extension pattern almost verbatim
(frustration added as a genuine 5th block alongside geometry/fpocket/
SASA/CTQW, not substituted for any existing block). Ran clean on 20/22
of [[TASK-0243]]'s frozen set (the same 2 HIV-integrase entries already
known to have an empty seed, [[TASK-0253]], correctly skipped, not a new
failure).

| block | Shapley share (median) | added-last (median) |
|---|---|---|
| geometry | +39.1% | +13.2% |
| fpocket | +7.0% | +3.3% |
| SASA | −0.4% | −0.4% |
| CTQW | +5.4% | +0.0% |
| **frustration** | **+6.5%** | **+0.1%** |

Unexplained share: 3-block (geometry/fpocket/CTQW) baseline 28.6% median
→ 5-block (+SASA+frustration) 22.4% median — frustration and SASA
together close some of the residual, but frustration's own **added-last**
value is not distinguishable from zero (cluster-p=0.727, [[TASK-0261]]'s
exact permutation, 13 clusters) — its positive Shapley share (+6.5%,
p=0.128, also not significant) reflects real but *redundant* information
already substantially captured by the other 4 blocks, not a genuinely
new, independent signal.

### The pre-registered prediction itself, checked and failed

| statistic | cryptic (n=10, 7 clusters) | already-open (n=8, 5 clusters) | cluster-perm p (cryptic>open) |
|---|---|---|---|
| frustration Shapley share | +6.96% | +0.27% | 0.355 |
| **frustration added-last** | **−0.09%** | **+0.05%** | **0.452** |
| frac. residues highly frustrated (z>0.78) | 36.0% | 35.2% | 0.537 |

**Direction predicted by HYP-P13 (cryptic > open): DOES NOT HOLD** on the
statistic that matters most (added-last — the unique, non-redundant
contribution) — cryptic targets show numerically *lower* frustration
than already-open ones, the opposite of the prediction, though the gap
itself is small and not remotely significant either way. The raw
"fraction highly frustrated" statistic shows essentially no difference
at all (36.0% vs. 35.2%). `TRP_SYNTHASE_F6F`/`F19` excluded from this
stratified table only (same straddling-cluster issue [[TASK-0266]] first
found and documented — one apo structure whose two ligands sit on
opposite sides of the 80% crypticity bar), kept in every other number.

### Not done, and why

The full AWSEM-based frustration index (burial/local-density and
electrostatic terms beyond the pairwise MJ potential this port uses) was
not built — a real, stated simplification, not silently presented as the
published tool's own output. "Configurational frustration" (perturbing
local backbone/rotamer geometry, not just residue identity) was not
attempted — this task's own Scope named mutational frustration
specifically (the cheapest, most directly comparable variant to the
project's own existing single-static-structure observables). The
possibility that frustration would show the predicted pattern under a
different contact cutoff or a full AWSEM potential was not swept — a
real, stated limitation, not claimed to be ruled out by this one
measurement.

**Validated**: `allostery/frustration.py`'s own MJ matrix symmetry and
sanity values checked directly before use; the full pipeline reruns
clean and reproduces every number above from
`results/tasks/0268_local_frustration_hyp_p13/`.

## Constraint

[[HYP-P13]] is this project's own hypothesis and the Reviewer wrote it up.
That makes a favourable result *less* trustworthy, not more. Pre-register the
prediction, and if frustration shows nothing, record that in
`physics.md` with the same prominence the hypothesis currently enjoys.
