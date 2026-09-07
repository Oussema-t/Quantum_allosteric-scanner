# TASK-0346 — Run the blind validity rule at scale: replace "7 audited, 2 pass" with a real denominator

- Status: TODO
- Owner: **Implementer** — triggerable unattended, runs after or beside [[TASK-0345]]
- Priority: High — it is the evidence behind the submission's central claim
- Filed: 2026-09-07 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0345]], [[TASK-0329]], [[TASK-0305]], [[TASK-0331]]
- Feeds: `PHASE1_SUBMISSION_V2` §1 and the §4 impact table

## Why

The submission's central claim is that the field's benchmarks cannot certify a
cryptic-pocket result. The evidence for it is currently **7 targets audited, 2
pass** — a rate of 1 in 3.5 on a sample of seven. The claim is systemic; the
sample is anecdotal. A reviewer is entitled to say so.

The blind validity rule already exists and is already pre-registered: *apo
closed, holo open, ligand stripped, cavity re-scored*. Running it over the 1042
clean apo→holo pairs turns a 7-target observation into a population statistic,
using machinery [[TASK-0345]] will already have built.

## Intent Contract

- Outcome: the pre-registered rule applied to every available apo/holo pair,
  reported as **n passed / n tested, clustered by protein**, with the failure
  modes broken out — pocket already open in apo, no pocket in either, pocket in
  neither at the annotated site.
- **Do not modify the rule to improve the pass rate.** It was pre-registered; if
  it is too strict, that is a finding about the rule and gets reported as one,
  not silently tuned. Any variant must be reported *alongside* the original, with
  the original as the headline.
- Second output, same pass: the **endogenous-ligand audit** at scale. [[TASK-0329]]
  found 3 of 7 audited targets and 40 of 40 sampled ASBench structures carry a
  ligand at the scored site. Report what fraction of the full cohort's "apo"
  structures are occupied, and — the part that matters — whether occupancy
  correlates with the annotation, since that is what turns contamination into
  bias rather than noise.
- Constraints:
  - Cluster-robust throughout ([[TASK-0337]]).
  - Report the cohort's own provenance per source dataset — the five datasets
    have different curation standards and pooling them hides that.
  - **This changes numbers in a document under review.** Any figure that moves
    must be flagged for the submission draft explicitly, not left for someone to
    notice.
- Planned Validation: the seven already-audited targets must reproduce their
  existing verdicts exactly. If any flips, the scaled implementation differs
  from the one that produced the published numbers, and that must be resolved
  before the population figure is trusted.

## Note

Best case, the rate holds near 1 in 3 across ~1000 pairs and the submission's
central claim goes from an anecdote to a measurement. Worst case, the rate is far
better at scale and the seven targets were unrepresentative — in which case we
need to know that before a reviewer finds it, and the honest framing becomes
"the mandated targets specifically are unrepresentative", which is still a
finding worth having.
