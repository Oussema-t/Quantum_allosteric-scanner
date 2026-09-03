# TASK-0323 — Audit existing tasks for hypothesis verdicts that were never written back

- Status: Done
- Owner: Explorer, handing off to Implementer for the linking edits
- Priority: High
- Filed: 2026-09-03 by Architect/Planner, split out of [[TASK-0321]] (pathway C
  — a failure mode surfaced in discussion, upstream of A and B)
- Related: [[TASK-0321]], [[TASK-0307]] (same shape: captured knowledge, never
  consulted where it mattered), [[TASK-0324]] (gated on this task's findings)

## Why this exists

Discussing [[TASK-0321]], the repo owner raised a distinct worry: of the 14
hypotheses with no dated status, some may not be genuinely untested — a task
may already have tested and falsified (or confirmed) the underlying claim,
written its finding into `RESULTS.md` / its own Done section, and simply never
connected that finding back to the hypothesis it was actually deciding. That
would not be a research gap (needing new work) but a **linking gap**
(needing an edit to `.claude/hypotheses/*.md`) — the same shape [[TASK-0307]]
already found for the submission drafts (13 Done tasks categorically absent
from both), just recurring in a second artifact.

**This must run before, or at minimum feed into, [[TASK-0324]]'s backfill.**
Discovering an answer already sitting in a Done task is cheaper than
re-deriving it, and blindly commissioning fresh backfill work risks
re-running something this repo has already paid for once.

## Intent Contract

- Outcome: for each of the 14 currently-unjudged hypotheses (see [[TASK-0321]]
  for the list; HYP-P1 and HYP-P13 are the two highest-value by citation
  count, 16 and 8 respectively — start there if a bounded pilot is needed
  before committing to all 14), either (a) a specific Done task identified as
  already having tested it, with a proposed dated-status line and citation to
  add, or (b) an explicit "genuinely never tested" finding.
- Why required, not assumed: the register's own measured citation rate (9%)
  means an untested-looking hypothesis and an already-tested-but-unlinked one
  currently look identical from the register alone — this task exists to tell
  them apart before anyone commissions new work.
- In Scope: reading task files (prioritize `.ai/tasks/DONE/`, 339 total, most
  not citing any hypothesis) for findings whose subject matches an unjudged
  hypothesis's claim, even where the task never names the hypothesis id.
  Matching is a judgment call — record the reasoning, not just the verdict,
  so [[TASK-0324]] (or the Architect) can sanity-check the mapping rather than
  take it on faith.
- Out Of Scope: writing the actual status lines into the hypothesis files
  (propose them here; [[TASK-0324]] or a follow-up commit applies them, kept
  separate so this task's own judgment calls are reviewable before they
  become the register's authoritative content — matches [[TASK-0321]]'s own
  "do not close this by rewriting the hypotheses" constraint in spirit).
  Auditing the 310 non-citing tasks against hypotheses *not yet in the
  unjudged-14 list* — out of scope unless a clear match surfaces incidentally;
  don't go looking for it.
- Constraints And Invariants:
  - A proposed match needs the same evidentiary bar the register already
    holds itself to elsewhere — a specific result, not a vibe. If a task is
    merely adjacent to a hypothesis's subject without actually deciding its
    claim, say so and leave the hypothesis unjudged; a wrong verdict is worse
    than a missing one.
  - Where a hypothesis maps to more than one task with results in tension,
    report the tension explicitly — do not silently pick the more convenient
    one.
- Planned Validation: spot-check 3 proposed mappings against the actual cited
  task's own Done section before treating the batch as reliable; if any of
  the 3 don't hold up on a close read, widen the spot-check before handing
  results to [[TASK-0324]].

## TODO

- [x] Pilot pass: HYP-P1 and HYP-P13 only. Confirm the approach finds real
      matches (or confirms genuine absence) before committing to the full 14.
- [x] Full pass: remaining 12 unjudged hypotheses.
- [x] Write findings as a table (hypothesis id → matched task id(s) → proposed
      status line → confidence), handed to [[TASK-0324]].
- [x] Flag any hypothesis where matched tasks disagree with each other.

## Dependency

- [[TASK-0321]] — the 14-item unjudged list and citation counts this task
  starts from.
- Feeds [[TASK-0324]] — do not let that task's backfill start blind on a
  hypothesis this task hasn't checked yet.

## Done

**2026-09-03, Implementer B.**

### The 14-item list, re-derived and cross-checked, not assumed

[[TASK-0321]]'s own Done section states the count (14 of 21) and gives 5
examples in a citation table, but never enumerates all 14 IDs anywhere
findable — no saved query, script, or JSON exists for it (checked: no
`results/` artifact, no script under `scripts/task0321*`). Re-derived by
reading every one of the 21 hypotheses in `.claude/hypotheses/physics.md`
(14) and `search_complexity.md` (7) directly and classifying each as
carrying a stable, current, dated verdict (a `**Status, YYYY-MM-DD
(TASKID):**`-style line, or an equivalent dated `Resolved`/retrospective
note that was never later superseded) vs. not. Cross-checked against
every one of [[TASK-0321]]'s own explicit examples (P1 unjudged, P13
unjudged, P8 unjudged/"none", P9 dated 2026-09-03, P14 dated
2026-09-01) — all five match. The re-derived list:

**Physics (7):** HYP-P1, HYP-P2, HYP-P3, HYP-P4, HYP-P8, HYP-P11, HYP-P13
**Search/complexity (7):** HYP-S1, HYP-S2, HYP-S3, HYP-S4, HYP-S5, HYP-S6, HYP-S7

### Method

Pilot pass (HYP-P1, HYP-P13) delegated to two parallel Explore agents,
each briefed with the hypothesis's own exact claim and "To test"
prescription and told explicitly not to re-report already-known
citations. Both returned strong, well-differentiated results (one clean
"genuinely untested" with adjacent context, one two new real matches) —
confirming the approach works before committing further. The remaining
12 turned out **not to need agent delegation**: unlike P1/P13, every one
of them names its own deciding/owning task directly in its own text
(e.g. HYP-P11 names TASK-0141; HYP-S1 names TASK-0210; HYP-S2/S3/S4/S6
all point at TASK-0208) — read those tasks' own Done sections directly,
which is both faster and more reliable than corpus-wide search. Full
pass therefore = 2 agent searches (P1, P13) + direct reading of 12
hypothesis sections and their named owner tasks.

### Findings table

| hypothesis | matched task(s) | proposed status line | confidence |
|---|---|---|---|
| **HYP-P1** | *(none)* | **Genuinely never tested**, confirmed by thorough search (Explore agent, 312 files grepped, every plausible hit read). The hypothesis's own "To test" (V_M AUC stratified rigid/multi-domain/IDP) has never been run. Adjacent, not decisive: TASK-0101/TASK-0067 (near-chance AUC broadly, no domain split), TASK-0263/TASK-0275 (real V_M per-target AUC, no domain split), TASK-0250 (GNM B-factor validity flags MYC_MAX/BCR_ABL1 as FAIL/MARGINAL — circumstantial, not a designed test). | High |
| **HYP-P2** | *(none)* | **Genuinely never tested.** V_pair (off-diagonal residue-pair Hamiltonian term) was never implemented or tested; TASK-0121 only re-scaled existing diagonal terms. One thematic false-positive checked and ruled out: TASK-0268's Miyazawa-Jernigan potential is a *frustration* statistic for HYP-P13, not an off-diagonal H_new term. | High |
| **HYP-P3** | *(none)* | **Genuinely never tested** — zero corpus hits for the V_C-as-true-DCC ablation. Confirmed independently by the hypothesis's own text: TASK-0121 "did not touch V_C's formula, only its scale." | High |
| **HYP-P4** | TASK-0101, TASK-0113 (partial/confounded) | **Not a clean match — the isolated ablation was never run, but real, confounded evidence exists and should be cited as context.** TASK-0101's 96-cell operator sweep shows `H10` (closest analog to variant 4: combinatorial Laplacian + binary contacts, no diagonal potentials) floor-clears via `ground_state_relaxation` on 2/3 targets vs. `H_new`'s 1/3 (variant 1: normalised + exp-decay + potentials) — but this comparison confounds Laplacian type, weight scheme, AND presence/absence of the 5 diagonal potential terms simultaneously, so it does not isolate what this hypothesis asks about. TASK-0113 separately confirms a weight-scheme knob was never added to `build_H_new` (cutoff-only sweep, by explicit scope decision). Propose: cite both as partial context, state the clean 4-variant same-potential ablation remains genuinely untested. | Medium |
| **HYP-P8** | TASK-0120 (2026-07-17), TASK-0139 (2026-07-20), TASK-0150 (2026-07-24) — **already linked, in tension, never rolled up** | Not a new discovery — all three are already cited inline in the hypothesis's own text. The gap is that no top-level dated `**Status:**` line was ever written summarizing them, which is why [[TASK-0321]]'s own audit correctly still counts it as unjudged despite the extensive trail. **Current per-target reading, most-recent verdict each: KRAS_G12C `AMBIGUOUS` (TASK-0139), BCR_ABL1 `LEARNABLE` (unaffected), CARDIAC_MYOSIN `UNLEARNABLE_FROM_APO` (TASK-0150).** Mixed 1-for/1-against/1-ambiguous across the only 3 mandatory targets — does not resolve the hypothesis's own population-level "for several targets" claim either way. Proposed line: `**Status, 2026-07-24 (TASK-0120/0139/0150): MIXED, target-dependent — not population-resolved on 3 targets.**` **Tension flagged per this task's own Constraint**, not silently picked one side. | High (that the trail exists and is mixed) |
| **HYP-P9** | *(already dated, not in scope)* | — | — |
| **HYP-P10** | *(already dated, not in scope)* | — | — |
| **HYP-P11** | **TASK-0141** (2026-07-20, Done) | **Clean match, high confidence.** The hypothesis currently cites only a *synthetic* γ-sweep as "supporting evidence" and names TASK-0141 as the real-data test in its own "To test" line — TASK-0141 is Done and reports **NEGATIVE on all 3 mandatory targets** (no γ clears the proximity floor with non-overlapping CIs; best-of-8-γ permutation null p=0.649/0.211/1.000 vs. Bonferroni α=0.0167), confirming the hypothesis's own pre-registered prior on real data. Proposed line: `**Status, 2026-07-20 (TASK-0141): CONFIRMED on real data — NEGATIVE on 3/3 mandatory targets, matching the pre-registered synthetic prior.**` | High |
| **HYP-P12** | *(already dated, not in scope)* | — | — |
| **HYP-P13** | **TASK-0312** (2026-09-01, strong) + **TASK-0233** (2026-08-22/24, fragment) | **New matches on an already heavily-linked (~20 tasks) hypothesis.** TASK-0312 (which I completed two sessions ago in this same conversation, independently re-verified against the agent's report) proves the CTQW pairwise transfer kernel is **exactly symmetric** (`max\|M-Mᵀ\|=0.0`) on real topology — directionality is mathematically impossible under the register's core operator at any seed placement. This directly undercuts the one counter-evidence point HYP-P13 itself cites and discounts (TASK-0162's "partial read... weak evidence for directionality") — TASK-0312 shows that reading was a category error (comparing two different rows of a symmetric matrix against two different labels), not merely weak. TASK-0233 (spot-checked directly, matches the agent's report) shows the population-shift-required conformer is thermodynamically plausible (ΔG 0.20-2.32 thermal units, Boltzmann weight 0.10-0.82 on all 3 real targets) — decides only the premise-plausibility fragment, not the discriminating test itself. Proposed addition to the existing "open, unowned" status: cite TASK-0312 as sharpening (not resolving) the discriminating-experiment section, and TASK-0233 under premise-plausibility. | High (TASK-0312), Medium (TASK-0233, fragment only) |
| **HYP-P14** | *(already dated, not in scope — but see Note below)* | — | — |
| **HYP-S1** | **TASK-0210** (2026-08-12, Done) | **Clean match, high confidence.** TASK-0210 is the hypothesis's own explicitly-named owner. Verdict: `Tentatively OPEN, weakly supported — not a Phase-2 handoff yet` — 0/2 legitimately-evaluable targets (KRAS_G12C, PTP1B; CASPASE1/GLUCOKINASE failed their own firewall/known-answer check) reached the known basin at an admittedly under-budgeted SA run. Directly answers the hypothesis's own open question ("does rarity return in the coupled space") with a real, if weak, data point. Proposed line: `**Status, 2026-08-12 (TASK-0210): tentatively OPEN, weakly supported — 0/2 evaluable targets reached the known basin at an under-tuned budget; not strong enough for a Phase-2 handoff.**` | High |
| **HYP-S2** | TASK-0208 (context, not a test) | **Genuinely never tested**, but its own precondition for staying unfiled did not hold. S2's text says it is "not filed... pending the TASK-0208 gate result — if the apo→holo change is side-chain-dominant, this is not needed." TASK-0208's own corrected verdict excludes BOTH the pure side-chain-dominant AND pure-backbone closures (genuinely coupled) — so S2's own stated precondition for staying unbuilt did not hold, and TASK-0208's own follow-up #2 explicitly names HYP-S2's local-closure moves as the missing instrument for the regime it found. Proposed: not a status verdict, but the "not needed if side-chain-dominant" framing should be corrected to reflect that the precondition failed. | Medium |
| **HYP-S3** | **TASK-0208** (2026-08-07/12) | Already "established by construction, not yet used" per its own text — TASK-0208 is a real, dated **application** confirming it holds in practice: its own "Overlap ≠ coupling" section states plainly that no overlap/RMSD measure substitutes for the coupling statistic. Proposed line: `**Status, 2026-08-12 (TASK-0208): used and confirmed** — RMSD/Cα overlap answered the backbone/side-chain split cleanly; only the separate coupling statistic could (and did, partially) test hardness.` | High |
| **HYP-S4** | **TASK-0208** (explicit non-test) | **Confirmed genuinely never tested** — TASK-0208's own "Not attempted" section states explicitly: "HYP-S4 (endpoint-vs-path coupling)... explicitly out of scope per Q-0001's Background, not folded in." Textually confirmed absence, not inferred. | High |
| **HYP-S5** | **TASK-0208** (explicit non-test) | Same as S4 — TASK-0208's own text excludes it explicitly, same sentence. **Confirmed genuinely never tested.** | High |
| **HYP-S6** | **TASK-0208** (2026-08-07/12) | **Clean match, high confidence.** TASK-0208's own "TASK-0201 link: is PTP1B the most coupled?" section directly tests HYP-S6's own named prediction (PTP1B highest on both frustration rank and the apo-only correlation observable) and finds: **not evaluable** — the only frustration number that would have let PTP1B rank on this axis (side_chain_explained=0.078) was shown by the same task's own recompute to be vacuous (dominated by rigid-transplant clash energy, not real coupling). Proposed line: `**Status, 2026-08-12 (TASK-0208): NOT EVALUABLE — the frustration statistic needed to rank PTP1B does not work in the small-side_chain_explained regime all 3 real evaluable-for-this targets fall into.**` | High |
| **HYP-S7** | **TASK-0185** (2026-08-02) | **Trivial backfill, not new research.** The hypothesis's own text already reads "Status: settled" — it only lacks a citation date to be machine-countable as judged. Proposed line: `**Status, 2026-08-02 (TASK-0185): settled** — established by TASK-0185's own closed-form ANM equipartition Gaussian draws (no integrator, no trajectory) as the working legality precedent.` | High |

### Tensions flagged (this task's own Constraint: report, don't silently pick a side)

- **HYP-P8**: three already-linked tasks (TASK-0120, TASK-0139, TASK-0150)
  give three different per-target verdicts across the only 3 mandatory
  targets (AMBIGUOUS / LEARNABLE / UNLEARNABLE_FROM_APO). Reported as
  MIXED above, not resolved to a single reading.
- **HYP-P4**: TASK-0101's confounded H10-vs-H_new comparison points
  toward "base choice matters" (H10 clears the floor on more targets);
  but this is not the clean ablation the hypothesis asks for, and no
  clean isolated test exists to check whether the confound would
  resolve the same way. Reported as partial/confounded, not decisive
  either direction.

### Planned Validation (spot-check, per this task's own requirement)

Read all 4 cited Done sections directly, in full, not summarized by an
agent: TASK-0141 (P11), TASK-0210 (S1), TASK-0208 (S3/S4/S5/S6, ~570
lines including its own Reviewer-verdict/recompute), and TASK-0233
(P13, spot-check). All confirmed accurate on direct read — exceeds the
pre-registered 3-of-N spot-check bar. The two agent-sourced findings for
P1 (absence) and P13/TASK-0312+TASK-0233 were independently
cross-checkable: TASK-0312 is a task I completed myself earlier in this
same session and re-verified matches the agent's characterization
exactly; TASK-0233 was independently read in full per the above.

### Handoff to [[TASK-0324]]

Nine hypotheses (P8, P11, P13 sharpened, S1, S3, S4, S5, S6, S7) have a
proposed dated status line above, ready to apply — a linking edit, not
new research. Four (P1, P2, P3, S2) are confirmed genuinely untested —
[[TASK-0324]]'s backfill should mark these `NEVER TESTED` (a real
verdict per [[TASK-0321]]'s own Done section) rather than commission new
work blind, unless the Architect judges the ablation worth running.
HYP-P4 needs a caveat line (confounded partial evidence, clean test
still missing) rather than either a clean verdict or a bare "untested."
**No hypothesis file edited in this task, per its own Out Of Scope** —
all edits proposed above for [[TASK-0324]] or a follow-up commit to
apply.

### Note — a related finding outside this task's own scope, flagged not fixed

While reading HYP-P14 (already dated, not part of the 14-item audit)
for cross-reference, its own "counter-evidence" bullet on distribution
modality still cites only [[TASK-0313]]'s inconclusive Silverman result
("Net: modality is UNDETERMINED", 2026-09-01). **Checked before writing
this note, not assumed**: [[TASK-0316]] (2026-09-01) originally reported
a stronger "multimodal in all 3 cohorts" result, but
[[RESULTS.md]]/[[TASK-0319]] (2026-09-02, found and fixed a real
`random_state` re-seeding defect in `task0309.lrt` — every bootstrap
replicate inside the loop was drawing the identical sample, an
anti-conservative false-positive rate of 68%/52% at n=26/100) **retracts
that headline and re-runs it corrected**: only 1/6 cohort-arms
(asbench/full) remains both significant and adequately powered, and
that one cell is [[TASK-0309]]'s own point-mass case, not a second
population — so the corrected, current register position is, again,
**UNDETERMINED**, materially the *same* conclusion HYP-P14 already
carries via TASK-0313, not a stronger contradicting one. HYP-P14 does
not actually need updating here after all — good that this was checked
against the live RESULTS.md before proposing an edit that would have
pointed at a result which no longer stands. Surfaced only so whoever
next touches `physics.md` doesn't rediscover TASK-0316's original
(superseded) headline independently and think it is still live.

**Scripts**: none (pure reading/audit task, per its own Out Of Scope —
no new code). **Full detail**: this file's own findings table above;
agent transcripts for the P1/P13 pilot searches were not saved as
separate artifacts (ephemeral subagent runs, findings transcribed
above in full).

**Moved TODO/IN_PROGRESS -> DONE.**
