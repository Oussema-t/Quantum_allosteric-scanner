# TASK-0348 — The centrality ablation is now mandatory, and we have never run the one that matters

- Status: DONE
- Owner: **Implementer**
- Priority: **Highest — a published JACS result makes this the first thing a reviewer will ask for**
- Filed: 2026-09-08 by Reviewer thread (id via `claim.py reserve-next`)
- Source: Oussema's prior-art audit, `origin/allosteric:submission/phase1/PRIOR_ART.md`
- Related: [[TASK-0277]], [[TASK-0310]], [[TASK-0336]], [[TASK-0318]]

## What changed

**Mohtashim, Sajjan & Kais, "Continuous-Time Quantum-Walk Centrality for Protein Residue
Interaction Networks", *J. Am. Chem. Soc.* 148(27):29206–29219 (2026),
DOI 10.1021/jacs.6c08053** — peer-reviewed, July 2026.

Their construction is essentially ours: CTQW on a weighted residue interaction
network (Cα < 8 Å), weighted adjacency mapped to a Hamiltonian, residues scored
by long-time-averaged occupation, ~150 proteins, plus a 4-qubit hardware
demonstration.

**They report their quantum centrality agrees with classical eigenvector
centrality at Spearman ρ median ≈ 0.95, Kendall τ ≈ 0.87, Overlap@10 0.90–1.00,
and they claim no quantum advantage.**

The "the quantum layer is decorative" objection is therefore **no longer
hypothetical — it is published, in JACS, and citable against us.**

## The gap, verified here

Our stated floor in the submission draft is *"degree, hop distance, Euclidean
distance from the seed"*. Checked what exists in code:

| baseline | present? |
|---|---|
| `degree_centrality` | yes (`baselines.py:62`) |
| `betweenness_centrality` | yes (`baselines.py:68`) |
| **`eigenvector_centrality`** | **no** |
| **closeness centrality** | **no** |
| GNM alone, as a ranking baseline | not as a floor arm |

**The single comparison the published result makes mandatory — CTQW vs
eigenvector centrality — is the one we have never run.** Our proximity floor
tests distance confounds, not centrality confounds; those are different objects
and only the first is covered.

## Intent Contract

- Outcome: CTQW scored against **eigenvector centrality, closeness, betweenness,
  degree, and GNM alone** on the identical residues, identical labels, identical
  cohort. Report the rank correlation between CTQW and each — the JACS number to
  beat or reproduce is ρ ≈ 0.95 against eigenvector centrality.
- **Predicted outcome, stated before the run:** we expect ρ high and the ablation
  to show no CTQW advantage, consistent with [[TASK-0310]] (nothing survives
  residualisation) and [[TASK-0336]] (quantum and classical arms
  indistinguishable). If ρ is high, **that is a result to report, not to hide** —
  it independently reproduces a JACS finding on a different cohort and different
  task, which is worth stating plainly.
- Constraints:
  - Cluster-robust throughout ([[TASK-0337]]).
  - Use the existing cohort and labels; do not construct a new one for this.
  - Add `eigenvector_centrality` and `closeness_centrality` to `baselines.py`
    beside the two that exist — same module, same conventions, not a parallel
    implementation.
- Planned Validation: reproduce the two existing centralities' current numbers
  before trusting the two new ones.

## Consequence for the submission

The draft must **cite the JACS paper and state our delta explicitly**, rather
than leave a reviewer to find that our core construction was published two months
ago. The defensible delta is what that paper explicitly defers — it names
*"allosteric pathway prediction"* as future work — namely: active-site-seeded
pathway scoring, the site potentials, apo/holo blind validation, the
cryptic-opening veto, and the benchmark-validity audit.

Also from the same audit, and equally load-bearing: **the sponsor's own group has
published a quantum result in this domain** (Zhang, … Nussinov, Loscalzo, Guan,
Cheng, *Adv. Sci.* 13(12):e13641, DOI 10.1002/advs.202513641; Feixiong Cheng of
the Cleveland Clinic Genome Center is senior author). Any sentence resembling "no
quantum results exist in this domain" must not appear. **Checked: our current
draft makes no such claim** — but it also cites nothing at all, which is its own
problem in a document whose central argument is about what the field has and has
not measured.

## Done, 2026-09-08

### Citations (live-verified via Crossref before use, per `PAPER_CITATION_PROTOCOL.md`)

Both DOIs from the filing resolved to the claimed papers, checked directly:
- 10.1021/jacs.6c08053 → Mohtashim, Sajjan & Kais, *J Am Chem Soc*
  148(27):29206-29219, published online 2026-06-26 / print 2026-07-15.
- 10.1002/advs.202513641 → Zhang et al. (incl. Nussinov, Loscalzo, Cheng),
  *Advanced Science* 13(12):e13641, 2025-11-28.
Both added to `documentation/REFERENCES.md`'s method/tool-papers table (not
previously indexed there, though already cited inline by an earlier
same-day commit's own `PHASE1_SUBMISSION_V2.md` edit — added here so the
citation is findable outside that one file, per this protocol's own stated
failure mode).

### Baselines added

`eigenvector_centrality`/`closeness_centrality` in `baselines.py`, beside
the existing `degree_centrality`/`betweenness_centrality` (same module,
same `contact_matrix`/cutoff convention). Real bug caught by the unit tests
written alongside them, not assumed away: `nx.eigenvector_centrality_numpy`
*raises* `AmbiguousSolution` outright on a disconnected graph in this
networkx version (an earlier docstring draft claimed it "never raises" —
wrong, corrected once the test failed). Fixed to compute per connected
component (isolated 1-node components get 0.0 — no other node exists for
their centrality to be relative to). 8 new tests in `test_baselines.py`,
full suite passes.

### Ablation run

**Cohort** (per Constraint: reuse, don't reconstruct): TASK-0318's own
`build_structures()`/ASBench cohort, 108 candidate structures. **Planned
Validation**: re-derive degree/GNM-alone(`gnm_msf`)/CTQW via this task's
own graph-construction path (`compute_features_one`, the same call
`task0318_input_space_ceiling.py`'s own Phase A uses) and confirm byte-exact
match against the committed `feature_cache/*.npz` columns those numbers
came from — **passed 105/105** (3 of 108 structures hit a pre-existing
disconnected-contact-graph guard, `superpose.py::
_check_anm_rigid_body_nullspace`, TASK-0005's own regression check, and
were skipped — matching `task0318_input_space_ceiling.py`'s own Phase A
convention for the identical guard, not a new defect).

**Result — the predicted outcome (stated in this filing, before the run:
"rho high, no CTQW advantage") did NOT fully hold, and is reported as such,
not smoothed over:**

Rank correlation, CTQW vs. each classical arm (Spearman rho, cluster-bootstrap
95% CI on the median, n=105 structures / 74 proteins):

| arm | median rho | cluster-bootstrap 95% CI |
|---|---|---|
| eigenvector centrality | **+0.41** | [0.33, 0.49] |
| gnm_msf (GNM-alone) | −0.45 | [−0.50, −0.40] |
| degree | +0.38 | [0.33, 0.41] |
| closeness | +0.34 | [0.31, 0.40] |
| betweenness | +0.30 | [0.27, 0.34] |

The JACS paper's own reported number is rho median≈0.95 against eigenvector
centrality. This project's own construction lands at **0.41** — a genuine
divergence, reported plainly rather than rounded up to "consistent."

AUC of every arm (including CTQW) against the same truth labels, and the
paired (per-structure, same 105 rows) cluster-permutation test on
AUC(ctqw)−AUC(arm):

| arm | AUC mean | AUC median | vs CTQW: p (H0: median delta=0) |
|---|---|---|---|
| CTQW | 0.585 | 0.609 | — |
| closeness | 0.588 | 0.636 | 0.93 (tied; closeness slightly *higher*) |
| betweenness | 0.567 | 0.593 | 0.50 (tied) |
| gnm_msf | 0.499 | 0.512 | **0.031** (CTQW wins) |
| eigenvector centrality | 0.473 | 0.477 | **0.0** (CTQW wins) |
| degree | 0.448 | 0.451 | **0.0** (CTQW wins) |

**Interpretation, consistent with HYP-P13, not contrary to it**: degree,
eigenvector centrality and GNM-alone are seed-BLIND (no information about
where the active site is). CTQW is seed-referencing by construction. It
beats exactly the seed-blind arms and ties the two path/distance-based ones
(betweenness, closeness) — consistent with this register's own
already-established mechanism (TASK-0226: "every seed-referencing
observable is a proximity detector"), now measured on a comparison this
project had never actually run, and sharper than before: CTQW's own
apparent AUC "advantage" is fully accounted for by which baselines happen
to lack seed information, not by anything the walk itself contributes
beyond that. **Not tested directly in this task** (would need a
seed-blind-vs-seed-aware control matched pairwise on the same three
tied/beaten arms) — stated as the working explanation, not confirmed.

### Submission draft

[[TASK-0332]]'s prior landing (commit `5b39d0d`, before this task ran)
already cited the JACS paper and stated the delta in `PHASE1_SUBMISSION_V2.md`
§2, but its sentence — "we take both findings as given; our own measurements
above are consistent with them" — was written before this ablation existed
and is not accurate at the specific-number level once it does. **Corrected**
to state the actual rho (0.41, not ≈0.95) and the actual AUC picture (beats
3/5, ties 2/5), kept to one sentence for page-budget reasons (this document
was fought down to 6/6 pages by [[TASK-0339]]; word-count proxy only, no
PDF re-render performed here — disclosed, not assumed fine).

**Pre-existing gap noticed, not fixed** (out of this task's scope): the
`.html` twin of `PHASE1_SUBMISSION_V2` predates this paragraph entirely
(last touched before the JACS citation was added), and the CI parity
workflow ([[TASK-0340]]) still targets `PHASE1_SUBMISSION_V1.{md,html}`,
not V2 — flagged for whoever owns the V1→V2 transition, not resolved here.

### Process: the 2-hour-blind-run incident

The first run of `scripts/task0348_centrality_ablation.py` produced zero
bytes of stdout for over 2 hours (Python fully-buffers stdout when
redirected to a file; the script printed too little too rarely to ever
flush). Genuinely indistinguishable, from the log, between "healthy but
slow" and "hung" — confirmed only by direct process inspection (`ps`
CPU-time deltas), since `py-spy` needs `sudo` this environment doesn't
have. Killed on explicit instruction and rewritten: `sys.stdout.
reconfigure(line_buffering=True)`, one flushed progress line per structure
(index/N/elapsed/ETA), incremental JSONL checkpointing (resumed cleanly
across two more kills — once deliberate to fix an unhandled exception,
once from the laptop going to sleep mid-run). Also fixed a real
inefficiency the rewrite surfaced: the original version called
`compute_features_one` (19 features, some expensive — persistent homology,
low-mode ANM) **twice** per structure, once to validate and once to score;
fixed to call it once and reuse the result for both, roughly halving the
real compute cost on top of the visibility fix. **New standing rule filed
in `.ai/COMMON.md`'s Current Rules** (unbuffered/flushed output, per-unit
progress with ETA, incremental checkpointing, no repeated expensive calls)
so the next long-running script in this scaffold doesn't repeat this —
the filing states this has now happened more than once.

**Files**: `__WORK_IN_PROGRESS__/src/allostery/baselines.py`,
`__WORK_IN_PROGRESS__/tests/test_baselines.py`,
`__WORK_IN_PROGRESS__/scripts/task0348_centrality_ablation.py` (new),
`__WORK_IN_PROGRESS__/results/tasks/0348_centrality_ablation/{checkpoint.jsonl,centrality_ablation_result.json}`,
`__WORK_IN_PROGRESS__/documentation/REFERENCES.md`,
`__WORK_IN_PROGRESS__/documentation/PHASE1_SUBMISSION_V2.md`,
`.claude/hypotheses/{physics.md,INDEX.md,TASK_CLASSIFICATION_LEDGER.md}`,
`.ai/COMMON.md`, `__WORK_IN_PROGRESS__/RESULTS.md`.

**Constraints honored**: cluster-robust throughout (protein as the
resampling unit, cluster-bootstrap CIs + cluster-permutation p-values, not
raw per-structure ones); existing cohort/labels reused, none constructed;
`eigenvector_centrality`/`closeness_centrality` added to `baselines.py`
itself, not a parallel implementation; Planned Validation run and passed
before trusting the new centralities.
