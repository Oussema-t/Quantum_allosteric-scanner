# TASK-0284 — Two structurally distinct populations of allosteric site, and no standard descriptor predicts which a protein has

- Status: TODO
- Assignee: unassigned (suggest Explorer for part A, Implementer for part B)
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

- [ ] Reproduce the clustering as a committed script (currently only in a
      transient probe) with the silhouette, the gap, and the Shapiro test.
- [ ] Re-express [[TASK-0258]]'s taxonomy against the **data-derived ~10 Å
      boundary** alongside our own bins, stating both.
- [ ] Draft the sentence for [[TASK-0184]].

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

- [ ] Assign domains per target. Prefer an existing annotation (CATH/SCOP/Pfam
      via API, or the PDB's own `struct_ref`/entity decomposition) over a
      geometric domain-parser, and **verify the source live** per standing
      convention.
- [ ] Per target, record: number of domains; which domain holds the active
      site; which holds the allosteric site; **same-domain or cross-domain**.
- [ ] **Pre-registered prediction**: far-cluster targets are cross-domain,
      near-cluster targets same-domain. Test as a 2×2 (Fisher exact), n=33.
- [ ] If it holds, this is the covariate [[TASK-0282]]'s sweep needed and
      could not find — and a selection rule conditioned on domain architecture
      becomes testable.
- [ ] If it fails, record that the structural explanations are exhausted and
      the remaining candidates are non-structural: **ligand chemotype**
      ([[TASK-0265]]) or **functional/evolutionary history**, neither of which
      is recoverable from an apo backbone.

## Acceptance

- [ ] Committed clustering script reproducing silhouette 0.737, the 2.9 Å gap,
      and the Shapiro result.
- [ ] The eight-descriptor null table in `RESULTS.md`, with the multiple-
      comparison correction and both caveats stated.
- [ ] Domain assignment per target with its source cited.
- [ ] Fisher exact on the pre-registered 2×2, reported either way.
- [ ] A submission sentence for [[TASK-0184]].

## Constraint

**Do not go descriptor-fishing.** Eight properties have already been tested
and corrected for; adding twenty more and reporting whichever clears 0.05
would manufacture a result. Part B is pre-registered with one prediction and
one test. If domain architecture fails, the honest conclusion is that the
split is not predictable from apo structure — which is itself the finding, and
is consistent with everything else this register has measured.
