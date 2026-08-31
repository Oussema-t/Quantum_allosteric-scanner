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

---

## Progress 2 (2026-08-31) — annotations obtained, and **Finding F GENERALISES**

### Annotations solved

PMC's JS proof-of-work blocked the supplementary tables; **Europe PMC's
`supplementaryFiles` endpoint serves them without it**
(`https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8767309/supplementaryFiles`,
4.8 MB zip, all five xlsx). Their own `Filter-checkpoint.ipynb` — recovered
from the figshare archive by range request — confirms Tables S2/S6 are the
site definitions their pipeline reads.

**Table S2 = 118 structures with BOTH `Allosteric Site Residues` AND
`Active Site Residues` explicitly annotated.** 113 distinct PDB codes,
zero empty rows, median allosteric site 12 residues, median active site 22.
Committed as `results/tasks/0304_asbench_casbench/asbench_annotations.json`.

> Two annotation formats, which would corrupt everything if mixed silently:
> allosteric is `"ASP14 A"` (resname+resnum, space, chain); active is
> `"A41"` (chain+resnum). Parsed separately.

### The 84% verified independently — and decomposed

Recomputed from their own Table S3/S4 `Summary` column (● per measure
detecting):

| detected by | with allosteric ligand | **without** |
|---|---|---|
| ≥ 1 of 6 measures | 105/118 = 89.0% | **99/118 = 83.9%** ← the headline |
| ≥ 2 | 94/118 = 79.7% | 82/118 = 69.5% |
| ≥ 3 | 82/118 = 69.5% | 68/118 = 57.6% |
| ≥ 4 | 64/118 = 54.2% | 57/118 = 48.3% |
| ≥ 5 | 49/118 = 41.5% | 38/118 = 32.2% |
| **all 6** | 27/118 = 22.9% | **21/118 = 17.8%** |

The 83.9% reproduces the paper's 84% exactly. The intermediate rows differ
from the paper's text by ±1–2 structures (they report 106, 81, 26 / 99, 69,
19) — within ●/○ transcription tolerance, reported as measured rather than
adjusted to match.

**"84%" is a six-way disjunction. The all-six figure is 17.8%.**

### Finding F generalises — this is the important result

Recomputed [[TASK-0288]] Finding F's statistic on **their** cohort using
**their** annotations. Nothing of our pipeline is involved except the
distance definition itself. 117 of 118 resolved (`3BCR` fetch error).

| min heavy-atom distance, allosteric site → active site | ASBench |
|---|---|
| **exactly 0.00 Å — the two annotated sites SHARE residues** | **12/117 = 10.3%** |
| < 1.5 Å (covalent / peptide bond) | **26/117 = 22.2%** |
| < 4.0 Å (vdW contact or closer) | 33/117 = 28.2% |
| ≥ 8.0 Å (genuinely distal) | **59/117 = 50.4%** |

Deduplicated to 112 distinct PDB codes: 23.2% / 29.5% / 50.0% — unchanged.

**Our register: 8/28 = 28.6% below 1.5 Å.** ASBench: **22.2%**. Same
phenomenon, same order of magnitude, on a 4× larger and almost entirely
disjoint cohort (only 4 structures shared).

**Finding F was not a fluke of 13 clusters.** It is a property of how
allosteric sites are annotated in this field. And **only half of ASBench
is genuinely distal** — 10% of it has allosteric and active sites that
literally share residues (`1OF6`, `2HVW`, `2VVT`, `2W4I`, `3BZ7`, `3HO6`,
`3PTZ`, `3PXF`, …).

This is the strongest external support the register has produced for its
own central claim, and it reframes it: **not "the Cleveland Clinic
benchmark is unusual" but "distal-site benchmarks in this field routinely
contain a large fraction of non-distal sites, and methods are scored on
them anyway."**

### Still to do

- [ ] CASBench site annotations (Tables S5/S6 are results, not
      definitions) — from CASBench directly.
- [ ] Ingest through `clean_from_config` and re-run [[TASK-0299]] /
      [[TASK-0300]] on the extended cohort.
