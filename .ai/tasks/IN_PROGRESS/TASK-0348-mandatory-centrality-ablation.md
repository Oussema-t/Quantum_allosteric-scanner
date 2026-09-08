# TASK-0348 — The centrality ablation is now mandatory, and we have never run the one that matters

- Status: TODO
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
