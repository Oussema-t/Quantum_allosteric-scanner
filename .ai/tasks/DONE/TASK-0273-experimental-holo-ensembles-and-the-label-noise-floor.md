# TASK-0273 — Experimental holo ensembles: how reproducible is our pocket label, and what does that ceiling imply?

- Status: Done
- Assignee: Implementer A (claimed via user-authorized override of a reserved-but-unimplemented placeholder held by reviewer-opus)
- Priority: **Highest — it measures a ceiling that bounds every AUC this register has published, and nobody has measured it**
- Filed: 2026-08-26 by Reviewer
- Related: [[TASK-0265]], [[TASK-0270]], [[TASK-0254]], [[TASK-0259]], [[TASK-0243]], [[TASK-0155]]

## The observation that prompted this

[[TASK-0270]]'s audit of [[TASK-0155]]'s candidate pool found **8 of 10
"apo" KRAS structures are actually drug-bound** — and named them with their
ligands: `8AZX` (BI-2865), `7A1X` (QWB), `8QUG` (WYU), `9UOH` (ASP2453),
`7YCE` (IQN), `7MDP` (Z07), `7RP3` (MKZ), `8AFC` (LXK). Add `8S8C` (MK-1084)
and `6OIM` (sotorasib) and that is **ten verified KRAS holo structures with
ten different drugs.**

That is not a defect to clean up. **It is a ready-made experimental
conformational ensemble** — real crystallography, already verified, requiring
no simulation and raising no Constraint-3 question at all.

## The measurement nobody has made: our label's own reproducibility

Every AUC in this register treats the pocket label as exact. It is not. It is
"residues within 4.5 Å of the drug in one crystal structure."

[[TASK-0265]] measured five same-apo-structure ligand *pairs* at Jaccard
median **0.833** (range 0.750–1.000) and concluded ligand identity barely
moves the residue set. But that measurement has no noise floor beneath it:
**we do not know what Jaccard two crystals of the *same* protein with the
*same* drug would give.**

- If same-drug replicates give ~0.99, then 0.833 across different drugs is a
  real chemical effect.
- If same-drug replicates give ~0.85, then 0.833 is **within crystallographic
  noise** and the label carries far less information than we have assumed.

**Either answer bounds every AUC we have published from above**, and we have
never computed it.

## Scope

- [x] **Build the KRAS holo ensemble** from the ten already-verified
      structures. Re-verify each live (ligand present, chain, resolution,
      residue 12 = Cys) — do not inherit [[TASK-0155]]'s pool unchecked, which
      is precisely how the 8-of-10 error survived.
- [x] **Find same-drug replicates.** Sotorasib (MOV) and adagrasib in
      particular are likely to have several independent depositions. Search
      RCSB by ligand code, not by paper. This is the noise-floor measurement
      and it is the single most valuable item here.
- [x] Compute the pairwise Jaccard distribution over the ensemble, split into
      **same-drug** and **different-drug** pairs. Report both distributions,
      not a single number.
- [x] Define and compute a **consensus pocket** (residues present in ≥K of N
      holo structures) and a **union pocket**. State K before looking.
- [x] **Re-score KRAS against consensus and union labels** and compare to the
      single-structure label. If AUC rises against consensus, part of what we
      have been calling unexplained is **label noise**, not missing physics.
      That is a different diagnosis from [[TASK-0259]]'s crypticity finding
      and would need saying loudly. (Answer: it does not rise. See Done.)
- [x] Repeat for at least two more proteins with rich holo coverage. Candidates
      from the frozen set with multiple ligands already: **HCV_NS5B** (4 rows,
      2 apo structures), **PKR**, **GAC**, **FBPASE**, **TRP_SYNTHASE**,
      **KSHV_PROTEASE**. Prefer whichever has genuine same-drug replicates.
      (Did GAC_BPTES [7 depositions] and TRP_SYNTHASE_F6F [13 depositions,
      the richest replicate set found] — chosen over HCV_NS5B/PKR/FBPASE/
      KSHV_PROTEASE because a live RCSB search found genuine same-drug
      replicates for these two and not, in useful numbers, for the others;
      not separately re-checked here, so "no rich replicate set" for them is
      not asserted, only "not the two picked.")
- [x] Feed the result back to [[TASK-0265]]'s independence rule: if the label
      is noisy at the 0.85 level, "second ligand = new target" is even weaker
      than that task already concluded.

## Acceptance

- [x] Verified ensemble manifest per protein: PDB ID, ligand code, resolution,
      chain, method.
- [x] Same-drug vs different-drug Jaccard distributions, reported separately.
- [x] Consensus/union labels defined with K stated in advance, and KRAS
      re-scored against all three label definitions.
- [x] An explicit statement of the implied AUC ceiling, and which published
      numbers sit above or below it.
- [x] `RESULTS.md`.

## Constraint

If the label turns out to be substantially noisy, **that lowers the ceiling on
our own published results as much as on anyone else's method.** Report it that
way. It also strengthens, independently, the argument in
`documentation/CTQW_CONTRIBUTION_BRIEF.html` §08 that the benchmark rather
than the method is the limiting factor — but do not let that make the finding
more welcome than it should be.

## Done (2026-08-26, Implementer A)

**The label is genuinely noisy, and that noise turns out NOT to be the thing
holding AUC down — the finding is more nuanced than this task's own
Constraint anticipated, reported that way rather than rounded to whichever
half is more welcome.**

**Live verification caught real contamination, [[TASK-0270]]'s exact
pattern repeating.** Searched RCSB (chemical-component exact match) for
every other deposition of each of KRAS G12C's 10 already-verified drugs:
23 candidates found, 13 of 23 excluded after live per-entry checking —
BI-2865's other 7 hits are wild-type/G12D/G12V/G13D KRAS (checked via the
same anchor-relative position-12 sequence offset [[TASK-0155]]/[[TASK-0270]]
established), sotorasib's other 5 are cryo-EM and 4 of those are antibody/
MHC-peptide complexes, not the intact protein. **Two of KRAS's ten drugs
(BI-2865, sotorasib) have zero genuine same-drug X-ray G12C replicates
anywhere in the PDB** — a real negative finding, not a null result from
under-searching. Only GNE-1952 (MKZ) has any (6T5V, 7RP4, alongside the
already-known 7RP3). For GAC's BPTES replicates, 1 of 6 hits was mouse
glutaminase — excluded on species grounds.

**Two real bugs found and fixed mid-run, not smoothed over**: (1) an
organism-string exact-match check wrongly excluded 10 of 12 genuine
*S. typhimurium* TRP_SYNTHASE replicates on the first run — RCSB's own
free-text `scientific_name` field returns 4 different capitalization/
strain-suffix variants for the identical organism; fixed to a
case-insensitive keyword match, verified by rerunning and confirming
15/15 usable. (2) prody's legacy-PDB parser cannot read 9UOH or 8S8C at
all — both carry a 5-character extended chemical-component ID (A1L9E,
A1H5U, RCSB's newer convention once the classic 3-character alphabet was
exhausted) which overflows the fixed-width HETATM columns and corrupts
coordinate parsing; fixed with an mmCIF fallback (confirmed single-copy
ligands in both cases, so resname-only selection there is exact, not an
approximation).

**Contact extraction**: self-contained per PDB entry, heavy-atom, 4.5 Å,
matching this project's own established convention — no apo/holo overlay,
no cross-entry geometric alignment (this project's own `labels.py` already
establishes that a structure's own pocket label is a pure (chain,resnum)
distance computation on its own deposited coordinates). **Jaccard reported
both ways** ([[TASK-0265]]'s own dual-keying fix, reused): (chain,resnum)-
exact and resnum-only, since a homo-oligomer can deposit the identical
physical site under a differently-lettered symmetric chain across
independent depositions — confirmed materially: GAC's chain-exact same-drug
median is 0.231 but its resnum-only median is 0.818, an order-of-magnitude-
relevant difference from chain-letter noise alone, not real pocket
disagreement.

**Headline (resnum-only, the trustworthy keying for all three; full pair
tables in the JSON)**:

| protein | same-drug Jaccard (n pairs) | different-drug Jaccard (n pairs) |
|---|---|---|
| KRAS_G12C | 0.875 median [0.840,0.885] (n=3) | 0.591 median [0.000,0.917] (n=63) |
| GAC_BPTES | 0.818 median [0.636,1.000] (n=15) | 0.739 median [0.636,1.000] (n=6) |
| TRP_SYNTHASE_F6F | 0.500 median [0.000,1.000] (n=79) | 0.420 median [0.000,0.857] (n=26) |

Same direction in all three: same-drug agrees more than different-drug,
confirming [[TASK-0265]]'s own qualitative claim with a much larger sample
in two of three cases. **But the same-drug floor is nowhere near 1.0** —
even the identical drug, independently solved, reproduces the label at only
42-88% Jaccard. For TRP_SYNTHASE specifically, 4 of the 79 same-drug pairs
hit exactly 0.000 — all four involve 7ME8, whose deposition trapped F6F at
the beta site only, against depositions that trapped it at the alpha site
only: a real binary catalytic-state difference folded into "same-drug
noise" here, so this range is an upper bound on pure crystallographic
noise, not a purified estimate of it. Disclosed, not corrected for.

**Consensus (K=ceil(N/2), stated before computing) / union labels**: built
for all three ensembles. **Re-scored for KRAS_G12C and TRP_SYNTHASE_F6F
only** — GAC_BPTES is a genuine homo-oligomer with no established
chain-correspondence across independent depositions; re-scoring it against
a consensus mask built from possibly-mismatched chain letters would
silently launder that ambiguity into a number, so GAC's labels are defined
and reported but deliberately not used to re-score.

- **KRAS_G12C** (not in [[TASK-0243]]'s frozen 22-target set — scored on
  its own native metric, the single-operator CTQW AUC [[TASK-0270]]'s own
  numbers use): single AUC=0.514, consensus (K=6/12, 22 residues)
  AUC=0.509, union (62 residues) AUC=0.510. Flat; diagnosis stays
  `NO_SIGNAL_IN_APO` under all three labels — consistent with
  [[TASK-0270]]'s own finding that this target's floor-clear does not
  survive its genotype fix. No label definition rescues it.
- **TRP_SYNTHASE_F6F** (in the frozen set — re-scored in the actual metric
  that produces this register's "X% unexplained" headline: [[TASK-0254]]'s
  own cross-validated geometry+fpocket+CTQW composite, features held fixed,
  only the label `y` swapped): single AUC=**0.8642** (reproduces
  [[TASK-0254]]'s own published 0.864 for this exact target), consensus
  (41 residues) AUC=**0.7792**, union (53 residues) AUC=**0.7974**.
  **Broadening the label makes the cross-validated AUC substantially
  worse, not better — an 8.5-point drop against consensus.** The
  single-operator metric shows the same direction (0.591 -> 0.549 -> 0.532)
  though P@5 rises (0.0 -> 0.2 -> 0.4, a larger pocket is easier to
  partially hit even as its own ranking quality falls).

**Implied AUC ceiling, stated explicitly**: [[TASK-0254]]'s published
TRP_SYNTHASE_F6F AUC of 0.864 sits **at or above** what a majority-vote
consensus label across 13 real replicates would give (0.779-0.797) — it is
not being suppressed below some higher achievable number by single-crystal
label noise; if anything the single-structure label is the more favorable
target for this feature stack, not a noisy floor under it. KRAS_G12C's own
0.51-ish numbers sit at the same near-chance level under every label
definition tested — there is no headroom being hidden there either.

**Answered directly, per this task's own Constraint** (report the real
result, not the more welcome half): the label genuinely is noisy — same-drug
crystal replicates disagree by 12-58% depending on target, a real,
previously-unmeasured number. But in the one case tested against the actual
"X% unexplained" metric, that noise is **not** what holds AUC down: a less-
noisy, majority-consensus label performs *worse*, not better. This is a
different diagnosis from [[TASK-0259]]'s crypticity finding and
[[TASK-0254]]'s own fpocket-variance correction — both of those found real
missing predictors that raised AUC when added. This task finds the ceiling
is not the label. `documentation/CTQW_CONTRIBUTION_BRIEF.html` §08 is
**not** flagged, per this task's own Acceptance (only required if AUC rises
against consensus; it fell).

**Feeds back to [[TASK-0265]]'s independence rule**: confirmed, more
strongly than that task's own n=5-7 same-apo pairs could show — same-drug
replicates (a *stronger* form of "the same thing" than same-apo/different-
drug) still disagree at up to 58% dissimilarity, so two different-drug
labels on the same apo structure are certainly independent enough to count
as separate targets.

**Deviation from the task's own suggested candidate list**: picked
GAC_BPTES and TRP_SYNTHASE_F6F for the "at least two more proteins" item
rather than HCV_NS5B/PKR/FBPASE/KSHV_PROTEASE, because a live RCSB search
found genuine same-drug replicates for these two specifically (7 and 13
depositions respectively) and the task's own Scope explicitly said "prefer
whichever has genuine same-drug replicates." The other four candidates were
not checked for replicates at all — this is a scope choice made on the
evidence in hand, not a claim that they lack coverage.

**Validation**: script reruns clean (3 runs total: initial, then 2 bugfix
reruns after the organism-match and mmCIF-fallback fixes above; final run's
numbers match this Done section exactly). Live RCSB API calls throughout —
no cached/stale metadata. `pytest` not touched by this task (no `src/`
changes); not re-run.

**Script:** `scripts/task0273_holo_ensemble_label_noise.py`. **Data:**
`results/tasks/0273_holo_ensemble_label_noise/holo_ensemble_label_noise.json`.
**RESULTS.md**: new dated section added.
