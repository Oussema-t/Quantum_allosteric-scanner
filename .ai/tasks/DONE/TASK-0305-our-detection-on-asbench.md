# TASK-0305 — Our detection on ASBench: every arm at or below random, and CTQW significantly worse

- Status: Done
- Priority: **Critical — the cleanest negative this register has produced, and it reinterprets the field's own headline number**
- Filed: 2026-08-31 by Reviewer thread
- Related: [[TASK-0304]], [[TASK-0299]], [[TASK-0300]], [[TASK-0301]], [[TASK-0184]]

## Why this cohort is the fair test

[[TASK-0304]] gave us 118 ASBench structures with **both** the active site
(a seed) and the allosteric site (ground truth) annotated by the field, not
by us. That bypasses **every** labelling defect this register has found:
no apo/holo pairing, no `detect_active_site` ([[TASK-0289]]), no
`holo_pocket_mask`, no chain-agnostic parsing ([[TASK-0297]]/[[TASK-0298]]).
If our operators fail here, it is the operators.

## Result — 108 structures, residue-level P@5

| arm | mean P@5 | nonzero |
|---|---|---|
| ctqw | **0.0056** | 3/108 = 2.8% |
| hop_far | 0.0037 | 1/108 = 0.9% |
| hop_near | 0.0093 | 4/108 = 3.7% |
| msf | 0.0167 | 8/108 = 7.4% |
| degree | 0.0130 | 7/108 = 6.5% |
| **random** | **0.0171** | — |

**Nothing beats random. CTQW is significantly WORSE than random**
(Wilcoxon p < 1e-4) — anti-correlated, not merely uninformative. The
mechanism is coherent across arms: our operators rank *extremes* (most
distant, most flexible, least packed, highest walk occupation), and an
annotated allosteric site is not an extreme — it is an ordinary buried
pocket that happens to be functionally coupled.

### A design fault I found and fixed before reporting

The first run had **every** arm below random, which is too uniform to be
five independent failures. Cause was mine: our own pipeline excludes
terminal residues (`allostery.labels.terminal_mask`, 5% each end) and my
script did not — so `msf` and `degree`, which rank flexible and loosely
packed residues first, were being handed termini before scoring anything.
Re-run with the same eligibility convention, and with the size cap raised
1500 → 3000 residues (34 of 35 skips were `N > 1500`; the cohort went
83 → 108). The conclusion did not change; the numbers moved slightly.

## The positive control — and what it reveals about "84%"

Scored the **same 108 structures** with **their own** per-residue
propensity quantile scores (`*_propensity_residue_results.csv`, pulled
from the figshare archive by HTTP range request), on the **same P@5
metric**:

| | mean P@5 | nonzero |
|---|---|---|
| **their propensity QS** | **0.0204** | 10/108 = 9.3% |
| random | 0.0176 | — |
| our ctqw | 0.0056 | 3/108 |

- theirs vs random: **p = 5.0×10⁻⁹** — the design HAS power
- ctqw vs random: **p < 1e-4**, in the wrong direction
- theirs vs ctqw: p = 0.046

**The positive control passes, so our negative is real and not a broken
harness.** But look at the size of their win: **0.0204 against 0.0176**,
nonzero on 9.3% of structures. A method reported as **84% accurate**
retrieves a true-site residue in its top 5 on **one structure in eleven**.

## What that means — the key reinterpretation

**Their six measures are set-level ENRICHMENT tests, not top-k RETRIEVAL
tests.** Each asks whether the annotated site's *average* quantile score
exceeds what surrogate sites of the same size achieve. That is a very
different question from "are the highest-scoring residues in the site."

A method can pass the first comfortably while failing the second — and
that is exactly what the numbers show. So:

> **"84% allosteric-site recovery" does not mean "finds the pocket."** It
> means the annotated site is enriched in high-propensity residues
> relative to random same-size sites, under at least one of six tests.

This matters directly for the submission and for tomorrow's framing. The
claim that "the benchmark is connectivity-solved" rests on an enrichment
statistic; a drug-discovery pipeline needs retrieval. **On retrieval, the
published state of the art is 0.0204 against a 0.0176 chance baseline.**

## What this does NOT license

- **Not** "their method is bad." It does what it claims, and it beats
  chance at p=5e-9. The claim being reinterpreted is the *framing* of the
  number, not the work.
- **Not** "CTQW is refuted as a class." This is the time-averaged
  occupation observable on one operator, as the collaborator's own note
  already scoped.

## Consequence for the meta-classifier ([[TASK-0301]])

Back on the table, and now well-posed. Their Tables S3–S6 give the
per-structure ●/○ pattern for all six measures across 118 + 314
structures. The gap between **99/118 by ≥1 measure** and **21/118 by all
six** is 78 structures where some measures fire and others do not —
exactly the signature of "different measures suit different proteins",
with enough labelled examples to actually fit a selector for the first
time. → [[TASK-0306]].
