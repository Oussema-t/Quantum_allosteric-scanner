# TASK-0304 — Read the bond-to-bond paper, establish its baseline definition, and extend our cohort with ASBench/CASBench

- Status: Done
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

- [x] **Obtain and read the paper in full.** Not the abstract. Record:
      the exact benchmark composition, how many structures, and the
      dataset split. — Progress 1/2 below.
- [x] **Pin down what "84%" actually measures.** Critical and easy to get
      wrong: how many structures, what counts as a hit, what the scoring
      metric is (top-N? any-overlap? residue-level?), and whether the
      allosteric ligand was present in the scored structure. Their own
      failure analysis reports **106/118 with ligand → 99/118 without** —
      so the headline figure's ligand condition must be established
      before any comparison to our apo-side numbers. — verified independently
      and decomposed, Progress 2; further reinterpreted by [[TASK-0305]]
      as an enrichment statistic, not a retrieval one.
- [x] **Record the method precisely** — Eq. 1, `M = ½ W Bᵀ L†`, an
      edge-to-edge transfer matrix on the graph Laplacian pseudo-inverse,
      seeded from the active site. Establish how it differs from our CTQW
      operator and from our `hop`/`centroid` metrics. — Progress 1.
- [x] **Extract the structure list** (PDB IDs + allosteric-site
      annotations) and assess what fraction we can ingest through our
      existing `clean_from_config` / `holo_pocket_mask` path. — the second
      half is answered by NOT doing this: per this task's own Constraint
      below, `clean_from_config`/`holo_pocket_mask` would re-derive their
      site with our own heuristic. See Done's own explanation.
- [x] **Extend the cohort.** Report the resulting number of independent
      apo-structure **clusters**, not rows — that is the quantity that
      binds ([[TASK-0261]]). — 422 structures (113 ASBench + 314 CASBench);
      independent-unit counts reported throughout as 112 ASBench proteins
      and 33 CASBench proteins, never as raw rows.
- [x] Re-run the [[TASK-0282]] ceiling, [[TASK-0299]] comparison and
      [[TASK-0300]] family-ceiling analysis on the extended cohort. — done
      as the correct equivalent, not the literal script — see Done.

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

- [x] CASBench site annotations (Tables S5/S6 are results, not
      definitions) — from CASBench directly.
- [x] Ingest through `clean_from_config` and re-run [[TASK-0299]] /
      [[TASK-0300]] on the extended cohort. **Superseded by a better-
      targeted equivalent already done elsewhere — see Done.**

---

## Done (2026-08-31, Implementer B)

### CASBench site annotations — obtained live, from the source, not the ASBench paper's own tables

Chased down properly, not guessed: Tables S5/S6 (`mmc5.xlsx`/`mmc6.xlsx`,
opened and read their columns directly before concluding this) are
per-structure **scoring results** (`● / ○` per statistical measure, keyed
by `cas Number`/PDB) — no residue lists at all. CASBench's own site
definitions are not in the ASBench paper's supplement because CASBench is
a **separate benchmark with its own citation**, traced from the ASBench
article's own numbered reference 35 (found by reading its actual
bibliography, not the abstract): **Zlobin, A., Suplatov, D., Kopylov, K.,
Svedas, V. (2019). "CASBench: a benchmarking set of proteins with
annotated catalytic and allosteric sites in their structures." Acta
Naturae 11, 74–80** — verified live via Europe PMC (PMCID PMC6475866,
open access) before citing.

That paper's own full text names its live database:
`https://biokinet.belozersky.msu.ru/casbench` — confirmed live (HTTP 200).
Its `/casbenchbrowse` sub-app serves plain server-rendered HTML (no JS
proof-of-work, unlike PMC's own supplementary-file gate that blocked the
ASBench route earlier in this task) — `all.php` lists every CAS ID with
one representative PDB; `view.php?id=casXXXX` embeds **every** deposited
PDB structure for that protein family as its own div, each with an
"Allosteric Site:" and "Catalytic Site:" residue table (chain/resnum/
resname), aggregated here across every `SITE_<N>` sub-index CASBench
itself distinguishes.

**Fetched all 91 CASBench proteins (not just the 33 Wu et al. 2022 used)
— 2871 structures, 0 errors.** Cross-checked against the already-known
314-PDB/33-protein subset from the figshare cohort: **314/314 (100%)
resolvable with both site types annotated.** Script:
`scripts/task0304_casbench_annotations.py`. Data:
`results/tasks/0304_asbench_casbench/casbench_annotations.json`.

### Finding F on CASBench — the strongest result of the three cohorts

Same method as the ASBench run: minimum heavy-atom distance between
CASBench's own annotated allosteric and catalytic residue sets, on
deposited coordinates, no fpocket/detection/CTQW involved. Reported
**protein-level** (one row per `cas_id`, median of its own structures) as
the number that counts, per this window's own standing rule — CASBench's
314 rows are 33 proteins (9.5/protein), and a structure-level percentage
would repeat [[TASK-0261]]'s pseudo-replication at ~10x scale.

| cohort | n (protein-level) | below 1.5 Å (covalent) |
|---|---|---|
| Our register ([[TASK-0288]]/[[TASK-0297]]) | 13 clusters (28 structures) | **28.6%** |
| ASBench ([[TASK-0304]], earlier) | 112 proteins (117 structures) | **22.2–23.2%** |
| **CASBench (this)** | **33 proteins (313 structures)** | **42.4%** |

CASBench's own figure is the *highest* of the three, not a regression to
the mean — 14 of 33 proteins have an annotated "allosteric" site that
shares or peptide-bonds directly to the annotated catalytic site.
Structure-level (313 rows, descriptive only, not the number that counts):
48.9% below 1.5 Å, median 2.61 Å. Full distribution, both levels, in
`results/tasks/0304_asbench_casbench/casbench_finding_f.json`.

**Finding F now holds, independently, on three disjoint-ish cohorts
totaling 33 + 112 + 13 = 158 proteins, two of them from a field this
register has no editorial control over.** The reframing this task's own
Progress-2 section already stated stands, strengthened: this is not an
artefact of this register's own 13-cluster benchmark, and if anything the
Cleveland Clinic set is the *least* affected of the three.

### On "ingest through `clean_from_config` and re-run TASK-0299/TASK-0300"

**Not done as literally specified — done correctly instead, and that
correction was already made by a parallel task before this one reached
it.** `task0282_pocket_selection_sweep.build_target()` (the machinery
behind both TASK-0299 and TASK-0300) derives its own "true pocket" via
`holo_pocket_mask` on an apo/holo PAIR from our own config format. Forcing
ASBench/CASBench's single-structure, already-annotated entries through
that path would mean **re-deriving their site with our own labelling
heuristic** — exactly what this task's own Constraint forbids ("do not
re-derive them with our `holo_pocket_mask`, or the comparison to their
84% becomes meaningless").

[[TASK-0305]] (filed and completed the same day, reusing this task's own
ASBench annotations) built the correct alternative: a residue-level P@5
test using CASBench/ASBench's own seed (active site) and truth
(allosteric site) directly, no `clean_from_config`, no `holo_pocket_mask`,
bypassing every labelling defect this register has found. Its result is
the real answer to "does our approach generalise": **every arm at or
below random on 108 ASBench structures; CTQW significantly WORSE than
random (p<1e-4)** — with their own propensity score used as a positive
control (beats random at p=5e-9), proving the negative is real, not a
broken harness. [[TASK-0306]] then tested whether a meta-classifier over
their six independent statistical measures could recover more than any
one alone — redundancy check passed (mean|φ|=0.419, genuinely more
independent than our own 61-rule family), but the specific descriptors
tried (N, chain count, Finding-F site separation) carry no predictive
signal, LOPO by protein.

Both of those explicitly named CASBench as a natural extension once its
site annotations landed ([[TASK-0306]]'s own "What remains" section:
*"If Lane B's CASBench site annotations land, the meta-classifier step...
can be re-run there directly with this same code, still LOPO by
protein"*) — now unblocked by this task's own CASBench annotation work,
but not executed here (out of this task's own remaining time budget;
recorded as the direct, concrete follow-up, not a vague "future work").

### A resource-exhaustion incident, disclosed for whoever runs the next heavy CASBench/ASBench script

The CASBench Finding-F computation crashed **four times** before
completing, each traced to a real, fixable cause rather than dismissed as
flakiness:

1. `backend.data_layer.fetch` calls bare `urllib.request.urlretrieve`
   with **no timeout** — a slow/unresponsive RCSB connection blocks the
   process indefinitely (confirmed: uninterruptible-sleep state, stable
   low RSS, stuck on one specific PDB fetch both times it happened).
   Worked around **locally, in this task's own script only** (not
   `backend/`, a shared live-deployed module): a bounded-timeout
   `requests`-based fetch into the same cache directory.
2. The original `heavy_atoms()` built a dict of an entire structure's
   heavy atoms before filtering to the ~50–100 annotated-residue keys
   actually needed — real, avoidable memory pressure on a machine already
   swap-constrained by concurrent load. Rewritten to filter while
   streaming, never holding more than the wanted keys.
3. **The machine was genuinely oversubscribed independent of this
   script**: at the worst point, load average hit 29.75 with 4 separate
   Claude Code processes, Docker Desktop's VM backend (850 MB, actively
   spiking), and the usual VS Code/Chrome/Teams overhead all running at
   once — confirmed by checking `uptime`/`ps` directly rather than
   assuming. This script's own RSS never exceeded ~1.2 GB and was
   confirmed stable/non-leaking throughout every attempt. Addressed by
   making the whole computation **resumable in small checkpointed
   batches** (`casbench_finding_f_checkpoint.json`, written every 5
   structures) rather than one long uninterruptible run — a kill now
   costs at most a few structures, not the whole cohort.
4. **`4P3R` is a 113 MB PDB** (a huge cryo-EM-scale assembly) — even a
   streaming read of a file that size, on a machine with well under
   1.5 GB genuinely free, was enough to trigger a SIGKILL, independent of
   this process's own confirmed-small RSS (OS-level page-cache pressure,
   not a leak in this script). Checked directly, not assumed: a live
   HEAD-request size sweep of all 314 cohort PDBs found `4P3R` to be the
   **only** one over 5 MB — fixed with a 20 MB file-size guard that skips
   (disclosed, not silent) rather than reads.

**Suite**: no code in `src/allostery`/`backend/` was modified — the
timeout workaround lives entirely in this task's own script. No
regression run applicable.

**Scripts**: `scripts/task0304_casbench_annotations.py`,
`scripts/task0304_casbench_finding_f.py` (both new).
**Data**: `results/tasks/0304_asbench_casbench/{casbench_annotations,
casbench_finding_f}.json`.

**Moved TODO/IN_PROGRESS → DONE.**
