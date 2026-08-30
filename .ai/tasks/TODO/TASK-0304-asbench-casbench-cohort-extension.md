# TASK-0304 — Read the bond-to-bond paper, establish its baseline definition, and extend our cohort with ASBench/CASBench

- Status: IN PROGRESS (started 2026-08-30 by Reviewer thread)
- Priority: **Critical — this is the only route that makes the meta-selector question answerable, and it answers the collaborator's ProteinLens ask in the same move**
- Filed: 2026-08-30 by Reviewer thread, at the repo owner's direction
- Related: [[TASK-0301]], [[TASK-0300]], [[TASK-0299]], [[TASK-0288]], [[TASK-0261]], [[TASK-0184]]

## Why

[[TASK-0301]]'s dominating constraint: **13 apo-structure clusters cannot
validate any selector.** Four selection procedures in this register have
now been destroyed by pseudo-replication ([[TASK-0282]], [[TASK-0293]],
[[TASK-0299]], [[TASK-0300]]). No amount of cleverness fixes a cohort
that small.

The collaborator's cited paper — **Wu, Strömich & Yaliraki 2022,
*Patterns* 3(1):100408, DOI 10.1016/j.patter.2021.100408** — reports
**84% allosteric-site recovery on ASBench/CASBench**, a benchmark family
of roughly 118 structures. That cohort is ~9× our cluster count and comes
with a published classical baseline to measure against.

It also directly answers the collaborator's first ask (add bond-to-bond /
ProteinLens as a named classical baseline).

## Scope

- [ ] **Obtain and read the paper in full.** Not the abstract. Record:
      the exact benchmark composition, how many structures, and the
      dataset split.
- [ ] **Pin down what "84%" actually measures.** Critical and easy to get
      wrong: how many structures, what counts as a hit, what the scoring
      metric is (top-N? any-overlap? residue-level?), and whether the
      allosteric ligand was present in the scored structure. Their own
      failure analysis reports **106/118 with ligand → 99/118 without** —
      so the headline figure's ligand condition must be established
      before any comparison to our apo-side numbers.
- [ ] **Record the method precisely** — Eq. 1, `M = ½ W Bᵀ L†`, an
      edge-to-edge transfer matrix on the graph Laplacian pseudo-inverse,
      seeded from the active site. Establish how it differs from our CTQW
      operator and from our `hop`/`centroid` metrics.
- [ ] **Extract the structure list** (PDB IDs + allosteric-site
      annotations) and assess what fraction we can ingest through our
      existing `clean_from_config` / `holo_pocket_mask` path.
- [ ] **Extend the cohort.** Report the resulting number of independent
      apo-structure **clusters**, not rows — that is the quantity that
      binds ([[TASK-0261]]).
- [ ] Re-run the [[TASK-0282]] ceiling, [[TASK-0299]] comparison and
      [[TASK-0300]] family-ceiling analysis on the extended cohort.

## The question this is really asking

> Does the pattern hold, or were 13 clusters a fluke?

Specifically re-testable at scale: [[TASK-0288]] Finding F (~29% of
pockets covalently adjacent to the active site), [[TASK-0300]]'s
83%-of-achievable family ceiling, and whether **any** selector beats
random once there is enough data to fit one.

## Constraints

- **Their annotations, not ours.** Ingest ASBench/CASBench's own
  allosteric-site definitions; do not re-derive them with our
  `holo_pocket_mask`, or the comparison to their 84% becomes meaningless.
- **Do not merge cohorts for a headline number.** Report our 13 clusters
  and theirs separately as well as pooled — pooling hides whether the
  pattern extends.
- Watch for overlap: some of our targets may already be in ASBench.
  De-duplicate by structure, and report the overlap explicitly.

---

## Progress (2026-08-30, Reviewer thread) — paper read, cohort obtained

### The cohort is in hand — 422 structures, 418 of them new to us

The figshare deposit (DOI `10.6084/m9.figshare.16940317.v1`) is a single
**2.55 GB** zip. Downloading it was unnecessary: an HTTP **range request
for the last 2 MB** returns the zip central directory, whose 10,386
entries are named by **PDB ID**. Extracted without fetching the archive.

| set | unique PDB IDs |
|---|---|
| ASBench | **113** |
| CASBench | **314** |
| union | **422** |

Committed as `results/tasks/0304_asbench_casbench/cohort_pdb_ids.json`,
split by their four analysis arms (ASBench with/without allosteric
ligand; CASBench orthosteric-ligand/orthosteric-residues source).

**Overlap with our register: only 4 of 37 targets** — `CASPASE1` (1ICE,
CASBench), `GAC_BPTES` (holo 3UO9, ASBench), `PFK` (1PFK, ASBench),
`PTP1B` (holo 1T49, ASBench). **418 structures are new to us.**

### What "84%" actually measures — and it is not what the framing implies

**The success criterion is "detected by AT LEAST ONE of SIX statistical
measures."** The paper's own breakdown, ASBench without allosteric ligand:

| criterion | count |
|---|---|
| at least **one** of six measures | **99/118 = 84%** ← the headline |
| at least **three** of six | 69/118 = 58% |
| **all six** | **19/118 = 16%** |

With the allosteric ligand present: 106/118, 81/118, 26/118.

**A six-way disjunction is not a 84% hit rate in the sense our register
uses.** Each measure carries its own threshold (95% CI against 1,000
surrogate sites, or `P(p>0.95)>0.05`, or `p_ref>0.5`). Under our own
standards — Bonferroni across measures, cluster-robust across structures
— the reportable figure is far closer to the all-six **16%**.

### CASBench is severely pseudo-replicated

**314 structures across 33 proteins — 9.5 structures per protein.** Their
308/314 (98%) is really 32/33 proteins. This is exactly the failure mode
that has destroyed four selection procedures in our own register
([[TASK-0261]]), at ~10× the scale. **Any comparison must be
protein-level, not structure-level.**

### Their out-of-scope failure mode IS our Finding F

Verbatim, on PDB `1Z8D`: *"direct interactions, instead of functional
coupling, occur if sites are close to the orthosteric sites, **which is
out of the scope of bond-to-bond propensity analysis**."*

**They exclude contact-adjacent cases as out of scope. [[TASK-0288]]
Finding F measured that ~29% of the Cleveland Clinic benchmark IS those
cases.** So "a classical method already solves this benchmark" needs
qualifying: it solves a benchmark from which our dominant failure class
has been removed by definition.

Their other failure modes also match ours: incomplete multimers where
only one orthosteric site is annotated (6 ASBench, 3 CASBench structures)
— the same defect class as [[TASK-0297]]'s chain handling and
[[TASK-0251]]'s inter-subunit scope truncation.

### Ligand imprint, quantified by them

*"The average residue QS of the allosteric site for **109 of 118**
structures decreased when the allosteric ligand was not present."* A
systematic holo-inflation effect on 92% of structures — independent
confirmation of the apo/holo concern this register has been tracking.

### Still to do

- [ ] Site annotations. The PDB list is in hand; the **orthosteric and
      allosteric residue annotations** are not. Sources: ASD Release 4.10,
      CASBench's own site, or supplementary Tables S2–S7 (PMC serves
      these behind a JS proof-of-work challenge; `curl` gets an
      interstitial, so another route is needed).
- [ ] Ingest through `clean_from_config`; report how many of the 422
      survive, and the resulting **independent protein count**, not rows.
- [ ] Re-run [[TASK-0288]] Finding F, [[TASK-0299]] and [[TASK-0300]] on
      the extended cohort — the fluke-or-tendency question.
