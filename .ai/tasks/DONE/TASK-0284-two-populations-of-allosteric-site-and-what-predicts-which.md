# TASK-0284 — Two structurally distinct populations of allosteric site, and no standard descriptor predicts which a protein has

- Status: Done
- Assignee: Implementer B
- Priority: **High — part A is a submission-ready finding; part B is the last untested structural explanation**
- Filed: 2026-08-28 by Reviewer
- Related: [[TASK-0258]], [[TASK-0282]], [[TASK-0265]], [[TASK-0274]], [[TASK-0184]]

## Finding A — the bimodality is real, and sharper than our own bin edges

[[TASK-0258]] classified pockets by minimum heavy-atom distance to the active
site using **bin edges this register chose**. Re-examining the raw
distribution across all 33 scoreable targets, the split is not an artefact of
those edges:

- **1D k-means, k=2: silhouette 0.737** — strong separation for one-dimensional
  data, at a boundary nobody imposed.
- **near cluster: n=24, 1.3–8.3 Å. far cluster: n=9, 11.2–19.7 Å.**
- **A 2.9 Å gap between 8.33 and 11.24 with nothing in it.**
- Shapiro on log(min_A) **p=0.0020** — not one lognormal continuum we bisected.

So the benchmark contains **two structurally distinct populations of
allosteric site**, discovered from the data rather than assumed. That is a
sharper statement than the four-category taxonomy currently quoted, and it
explains directly why [[TASK-0282]]'s sweep found no single selection rule:
KRAS's site (1.32 Å) and BCR-ABL1's (7.96 Å) sit in the near cluster,
CARDIAC_MYOSIN's (11.81 Å) and HCV_NS5B's (17.9–19.7 Å) in the far one, and
the two want opposite orderings.

- [x] Reproduce the clustering as a committed script (currently only in a
      transient probe) with the silhouette, the gap, and the Shapiro test.
      `scripts/task0284_bimodality_and_nulls.py` — reproduces silhouette
      0.737, near n=24 (1.29–8.33 Å), far n=9 (11.24–19.72 Å), gap 2.91 Å,
      Shapiro p=0.0020 **exactly**, against a fresh re-run of
      [[TASK-0258]]'s own `measure()` (not the stored artifact, which
      predates a config fix — negligible difference confirmed, see Done).
- [x] Re-express [[TASK-0258]]'s taxonomy against the **data-derived ~10 Å
      boundary** alongside our own bins, stating both — see Done (n_far=9
      data-derived vs n_far=5 under TASK-0258's own bin edges).
- [x] Draft the sentence for [[TASK-0184]] — see Done.

## Finding B — eight standard descriptors are all silent

Tested against min_A across 33 targets (Spearman) and near-vs-far
(Mann-Whitney). **Nothing survives Bonferroni at α = 0.0063:**

| property | rho vs min_A | p |
|---|---|---|
| N (chain length) | +0.317 | 0.072 |
| Rg | +0.232 | 0.193 |
| compactness (Rg/N^⅓) | −0.021 | 0.910 |
| helix fraction | +0.047 | 0.797 |
| sheet fraction | −0.195 | 0.277 |
| **GNM λ₁ (global stiffness)** | **+0.070** | **0.697** |
| contact order | −0.108 | 0.551 |
| mean degree (packing) | +0.059 | 0.744 |

**Size, shape, secondary structure, stiffness, fold topology and packing
density are all silent.** Stiffness is a clean null — the two populations are
not "rigid vs floppy proteins", which was the obvious first guess.

**Two caveats, both stated rather than buried**: the far group is n=5 under
[[TASK-0258]]'s labels (n=9 under the data-derived split), so group-difference
power is poor — but the *continuous* correlation uses all 33 and also finds
nothing. And these are eight properties the Reviewer chose; absence of signal
in eight is not absence of signal.

## Part B — the one structural explanation not yet tested: domain architecture

Every descriptor above is **continuous and global**. None captures *"how many
domains does this protein have, and does the allosteric site sit in a
different one from the active site?"* That is a **categorical** fact, and a
site at 11–20 Å may simply be **in another domain** — which no global
continuous measure can see.

This is the cheapest remaining structural hypothesis and the only one with a
clear mechanism behind it.

- [x] Assign domains per target. Prefer an existing annotation (CATH/SCOP/Pfam
      via API, or the PDB's own `struct_ref`/entity decomposition) over a
      geometric domain-parser, and **verify the source live** per standing
      convention. Used Pfam (RCSB Data API + InterPro-by-SIFTS-UniProt
      fallback); CATH tried first and abandoned — its live REST API 404s
      on a 2024+ deposition (checked directly against 8QYP). See Done.
- [x] Per target, record: number of domains; which domain holds the active
      site; which holds the allosteric site; **same-domain or cross-domain**.
      `scripts/task0284_domain_architecture.py`, full per-target table in
      `results/tasks/0284_two_populations/domain_architecture.json`.
- [x] **Pre-registered prediction**: far-cluster targets are cross-domain,
      near-cluster targets same-domain. Test as a 2×2 (Fisher exact), n=33
      → **32/33 resolvable** (SUMO_E1_FHJ excluded, disclosed in Done).
- [ ] If it holds, this is the covariate [[TASK-0282]]'s sweep needed and
      could not find — and a selection rule conditioned on domain architecture
      becomes testable. **Not applicable — it does not hold**, see below.
- [x] If it fails, record that the structural explanations are exhausted and
      the remaining candidates are non-structural: **ligand chemotype**
      ([[TASK-0265]]) or **functional/evolutionary history**, neither of which
      is recoverable from an apo backbone. **It fails** (p=0.12) — recorded
      in Done.

## Acceptance

- [x] Committed clustering script reproducing silhouette 0.737, the 2.9 Å gap,
      and the Shapiro result.
- [x] The eight-descriptor null table in `RESULTS.md`, with the multiple-
      comparison correction and both caveats stated.
- [x] Domain assignment per target with its source cited.
- [x] Fisher exact on the pre-registered 2×2, reported either way.
- [x] A submission sentence for [[TASK-0184]].

## Constraint

**Do not go descriptor-fishing.** Eight properties have already been tested
and corrected for; adding twenty more and reporting whichever clears 0.05
would manufacture a result. Part B is pre-registered with one prediction and
one test. If domain architecture fails, the honest conclusion is that the
split is not predictable from apo structure — which is itself the finding, and
is consistent with everything else this register has measured.

## Done (2026-08-28, Implementer B)

**Finding A independently reproduced, exactly.** New `scripts/task0284_
bimodality_and_nulls.py`, re-running [[TASK-0258]]'s own `measure()` fresh
(not its stored artifact — checked, negligible: the artifact predates
[[TASK-0270]]'s KRAS `4OBE`→`4LDJ` fix but stays inside the same category
either way) plus a fresh 1D k-means. Reproduced **silhouette 0.737, near
n=24 (1.29–8.33 Å), far n=9 (11.24–19.72 Å), gap 2.91 Å between 8.33 and
11.24, Shapiro-on-log(min_A) p=0.0020** — every headline number in the
filing, bit-for-bit. Also computed the bin-derived split side by side per
Scope: [[TASK-0258]]'s own edges (min_A≥12.0 → far) give n_far=5, n_near=28
— the same 4-target gap (CARDIAC_MYOSIN sits at 11.81 Å, inside the
data-derived far cluster but outside the old ≥12 Å bin) already implied by
the filing's own caveat, now reproduced directly rather than taken on
trust.

**Finding B independently recomputed** (not just re-read) on the same 33
targets, reusing [[TASK-0261]]-era conventions (Spearman + Bonferroni)
but new per-target descriptors: N/Rg/compactness from `apo.coords`;
GNM λ₁/mean degree/contact order from `allostery.potentials.gnm_context`
(TASK-0040's shared GNM context, not re-derived); helix/sheet fraction
from a coarse ProDy `calcPhi`/`calcPsi` Ramachandran-region classifier —
**no DSSP binary and no biotite are available in this environment**
(checked directly: `mkdssp`/`dssp` not on PATH; `pip install biotite`
fails to build against numpy 2.5/python3.13, and an unpinned install hung
resolving dependencies and was killed rather than left running). N/Rg/
compactness/mean_degree reproduce the filed rho values to 3 decimals
(+0.317/+0.232/−0.021/+0.059); helix/sheet/λ₁ diverge in magnitude (and
λ₁'s sign) from the filed numbers, attributable to the different SS
method and possibly a different λ₁ convention — **the substantive
conclusion is identical either way: nothing survives Bonferroni
(α=0.00625) under either computation.** Full table, both the data-derived
and TASK-0258-bin-derived Mann-Whitney p-values, in RESULTS.md.

**Part B: a coverage gap produced a false HOLDS, caught before trusting
it.** New `scripts/task0284_domain_architecture.py`. Source: RCSB Data
API's own Pfam feature per polymer entity, resnum-mapped via the matching
`polymer_entity_instance` endpoint's `auth_to_entity_poly_seq_mapping` —
verified live against 4LDJ (KRAS) before trusting it at scale. CATH tried
first, abandoned: `cathdb.info`'s REST domain-summary 404s on a 2024+
deposition (8QYP) — its release lags recent PDB entries.

A first pass resolved only 24/33 targets and reported **HOLDS at
p=0.0184** — but the 9 unresolved were not random: **all 4 HCV_NS5B rows**
(the far cluster's single largest subgroup, 2GIQ/2HAI) dropped out because
RCSB's own bundled Pfam feature list is empty for that entity, alongside
TEM-1 beta-lactamase, HIV-1 RT, and others. Checked directly rather than
accepted: this is a real RCSB coverage gap for these specific entries, not
a bug in the request (InterPro's own Pfam-by-UniProt endpoint has "Viral
RNA dependent RNA polymerase" for HCV NS5B's UniProt P26663 with no
trouble). Fixed with two additions, both disclosed in the script's own
docstring: (1) an InterPro-by-SIFTS-UniProt fallback when RCSB's bundled
feature is empty, converting UniProt fragment coordinates to entity
seq_id via the entity's own SIFTS `aligned_regions` offset before reusing
the same auth-mapping step; (2) correct `auth_asym_id`→`label_asym_id`
resolution via the entry's own container identifiers (found live: 4DEM's
entity has `auth_asym_id="F"` but `label_asym_id="A"` — the instance
endpoint keys on the latter, and a same-string guess 404s). Resolution
went to **32/33** (only `SUMO_E1_FHJ` stays unresolved — its active site
and pocket residues span the SAE1/UBA2 heterodimer interface in a way
neither RCSB's nor InterPro's Pfam coverage fully annotates for chain D;
disclosed, not forced).

**With the coverage gap fixed, the result flips: FAILS.**

| | cross-domain | same-domain |
|---|---|---|
| far-cluster (n=9) | 3 | 6 |
| near-cluster (n=23) | 2 | 21 |

Fisher exact: odds ratio 5.25, **p_two_sided=0.1206** (p_one_sided,
far→cross = 0.1206 also). Direction is consistent with the prediction
(far cluster is more often cross-domain: 33% vs 9%) but does not clear
p<0.05 at this n. The far cluster's own same-domain majority (6/9) is
almost entirely HCV_NS5B (4 of the 6) — its allosteric thumb/palm sites
sit within the SAME single "Viral RNA dependent RNA polymerase" Pfam
domain as the active site, 17.9–19.7 Å away in 3D despite that. The near
cluster's own two cross-domain counter-examples are HIV1_RT (seed in
RNase H, pocket in the RT polymerase domain — a real cross-domain
near-cluster case) and GLUCOKINASE (Hexokinase_1 vs Hexokinase_2, the
classic bilobed hexokinase fold).

**Verdict: Part B's pre-registered prediction FAILS.** Per the task's own
instruction for this branch: the structural explanations tested by this
register (size, shape, secondary structure, GNM stiffness, fold topology,
packing density, and now Pfam domain architecture) are exhausted and none
predicts the near/far split. The remaining candidates are non-structural
— ligand chemotype ([[TASK-0265]]) or functional/evolutionary history —
neither recoverable from an apo backbone alone.

**Caveat on the method, stated not hidden**: Pfam domains are
sequence-family boundaries, coarser than a structural-domain parser for
large multi-lobed proteins — CARDIAC_MYOSIN's entire ~700-residue motor
head is one Pfam entry ("Myosin_head") even though the real fold has
several structurally distinct subdomains (upper/lower 50 kDa, converter).
A same-domain call under this test means "same Pfam family region", not
"same structural lobe" — a finer structural-domain parser might still
find CARDIAC_MYOSIN cross-domain and shift the far-cluster same-domain
count down from 6. Not chased further here — Part B was pre-registered as
one source, one test, not a parser sweep, and the Fisher result is
reported as measured.

**Submission sentence for [[TASK-0184]]** (added to the Load-bearing
findings list, next to the existing "benchmark is not distal" bullet):
*"The benchmark's allosteric-site distances are not one continuum: 1D
k-means splits them into two structurally distinct populations at ≈10 Å
(silhouette 0.737, a 2.9 Å gap with nothing in it) — and nothing we
measured predicts which a protein has. Eight standard descriptors (size,
shape, secondary structure, GNM stiffness, fold topology, packing) are
all silent (Bonferroni-corrected), and the one categorical, mechanistic
candidate — does the allosteric site sit in a different Pfam domain from
the active site — fails too (Fisher exact p=0.12, n=32). The split is real
and currently unexplained by structure alone."*

**Suite**: no code in `src/allostery` was modified; two new scripts only,
no regression run required.

**Data**: `results/tasks/0284_two_populations/{bimodality_and_nulls,
domain_architecture}.json`; regenerated `results/tasks/0258_allosteric_
distance_taxonomy/pocket_taxonomy.json` (fresh re-run against live
config, superseding the pre-[[TASK-0270]] stored artifact — same 33
scoreable targets, same categories).

**Moved TODO → IN_PROGRESS → DONE.**
