# TASK-0203 The PTP1B triangle — the program's one surviving positive was never tested by the two experiments that would explain it

## Context

- ID: TASK-0203
- Title: run [[TASK-0200]]'s conditional-on-fpocket analysis and [[TASK-0168]]'s
  2-mechanism plant grid **on PTP1B** — the one target carrying a
  corrected-null-surviving positive, and the one target neither experiment
  covered.
- Status: Done
- **Thread: Implementer A (science / compute).** Do not split across threads —
  both legs interrogate the same cell and a partial answer is misleading.
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: Reviewer thread, 2026-08-05. Gap found by reading
  `scripts/fpocket_conditional_analysis.py:58` (`TARGETS = ["KRAS_G12C",
  "BCR_ABL1", "CARDIAC_MYOSIN"]`) against [[TASK-0201]]'s result.
- Priority: **P0 — this is the best available use of the remaining compute
  window. It decides whether the program's only positive is a real,
  non-redundant, mechanistically-supported finding or a statistical survival
  inside static geometry.**
- Dependency: [[TASK-0200]], [[TASK-0168]], [[TASK-0201]] (all Done) — this
  task runs their existing, tested code on one more target each.

## Why this matters — three results form a triangle, and PTP1B is the missing vertex

Three findings landed within 48 hours, from three threads, and **none of them
cites the others**:

| Task | Finding | PTP1B covered? |
|---|---|---|
| [[TASK-0201]] | `dcc_low` (k=10) on **PTP1B** survives a corrected null — AUC 1.000, p=0.0027 vs. bar 0.003125. The program's only positive. | **yes — it IS the result** |
| [[TASK-0200]] | Strict subset: dynamics never resolves a residue fpocket is unsure about, on every well-powered cell | **no** — 3 mandatory targets only |
| [[TASK-0168]] | `dcc_low`'s ensemble-mechanism signature holds on KRAS_G12C, **fails to replicate** on BCR_ABL1 | **no** — 2 targets, PTP1B not among them |

The tension is structural, not cosmetic:

- **[[TASK-0200]] vs. [[TASK-0201]]** — "the dynamics signal is contained
  within static cavity geometry" and "`dcc_low` on PTP1B is a real positive"
  cannot both be unqualified claims unless PTP1B's positive lives precisely in
  the region TASK-0200 never looked at. **It does: PTP1B was not in its target
  set.** Right now the program asserts both.
- **[[TASK-0168]] vs. [[TASK-0201]]** — the program's one positive sits on the
  one observable whose mechanistic interpretation is explicitly unreplicated.
  `dcc_low`'s mode-specificity was confirmed on KRAS_G12C and lost on
  BCR_ABL1. Nobody has asked what it does on PTP1B.

**Both questions resolve on the same target with code that already exists and
is already tested.** That is an unusually cheap way to convert the program's
weakest-supported claim into either a real result or a closed one.

## Intent Contract

- Outcome: a single section answering, for PTP1B specifically, (a) does
  `dcc_low`'s positive survive conditioning on fpocket, and (b) does
  `dcc_low` show the ensemble-mechanism signature there — with an explicit
  joint reading of the two against [[TASK-0201]]'s survival.
- Why required, not assumed: the program is about to write a submission
  ([[TASK-0184]]) around either "a rigorous negative" or "a rigorous negative
  with one surviving positive." Which sentence is honest depends on these two
  measurements and on nothing else currently outstanding.
- In Scope:
  - **Leg 1 — conditional analysis on PTP1B.** Add PTP1B (and CASPASE7, for a
    second generalization-set data point, if it completes cheaply) to
    `scripts/fpocket_conditional_analysis.py`'s `TARGETS`. Everything else
    unmodified: same band definitions, same 4-window sweep, same within-band
    floor recomputation, same compact-patch null, same "survives only at one
    band width is not a result" rule. **Update `FAMILY_SIZE` for the
    Bonferroni family** — it is currently hardcoded `18` for 3 targets ×
    3 observables × 2 directions; adding targets changes it, and failing to
    update it silently loosens the bar. State the new family size explicitly.
  - **Leg 2 — mechanism plant on PTP1B.** Run [[TASK-0168]]'s 2-mechanism
    grid (`plant_channel` vs. `plant_mode`, `dcc_low_from_L` + the channel
    family) on PTP1B, same strengths/seeds/certification pipeline. Report the
    point-estimate discrimination table in the same shape TASK-0168 used, so
    the three targets read side by side.
  - **Joint reading, explicitly written.** Four outcome combinations, all
    plausible, all publishable — write the reading rule for each **before
    running**:
    1. Survives conditioning + shows mode signature → the program has a real,
       mechanistically-supported, non-redundant positive. Strongest outcome.
    2. Survives conditioning + no mode signature → real and non-redundant, but
       its mechanism is unexplained. Report as such; do not attribute it to
       the ensemble picture.
    3. Fails conditioning + shows mode signature → the signal is real
       mechanistically but contained in static geometry; TASK-0200's strict-
       subset claim generalizes to the positive too.
    4. Fails conditioning + no mode signature → the positive is a statistical
       survival with no mechanistic or informational support. Report plainly.
  - Cross-link the result into [[TASK-0200]]'s and [[TASK-0168]]'s own Done
    sections, and into [[TASK-0201]]'s `RESULTS.md` section — all three
    currently stand without knowing about each other.
- Out Of Scope:
  - Re-running CARDIAC_MYOSIN/KRAS_G12C/BCR_ABL1 on either experiment. Their
    numbers stand.
  - Re-litigating [[TASK-0201]]'s survival itself, its bar, or its CI. This
    task explains that result; it does not re-test it.
  - Any new observable. Use the three [[TASK-0199]]'s effective-rank finding
    already justified as representative.
  - The [[TASK-0200]] fpocket-drift question — that is [[TASK-0206]]. Use
    freshly-recomputed fpocket numbers here as TASK-0200 did, and say so.
- Constraints And Invariants:
  - **Write the four-outcome reading rule into this file before running
    anything.** With one positive in the whole program and a submission
    narrative riding on it, the post-hoc-interpretation risk here is the
    highest in the register.
  - Both legs use the existing scripts with a target added — no re-derivation,
    no re-tuning, no new band definitions. If a script needs a real change to
    accept PTP1B, that is a finding worth stating, not a licence to redesign.
  - Report the updated Bonferroni family size and the resulting bar
    explicitly in the write-up. A quietly-changed denominator is the exact
    defect [[TASK-0189]] just fixed elsewhere.
- Planned Validation:
  - Leg 1: reproduce one already-published TASK-0200 cell (any target) as a
    wiring check before trusting the new PTP1B numbers.
  - Leg 2: reproduce one already-published TASK-0168 cell (KRAS_G12C
    `dcc_low_from_L`) as the same kind of check.
  - Leg 2's `dcc_low_from_L` adapter must still be bit-identical to real
    `dcc_low` on the equivalent unweighted graph — TASK-0168's own assertion,
    re-run on PTP1B's topology, not assumed to transfer.
  - Band power: report `n`/`pos` per window. PTP1B is N=298 with a small
    active site (5 residues) — underpowered bands are a live risk and must be
    reported as underpowered, never scored anyway.

## Pre-Registered Reading Rule + Methodology Notes (fixed 2026-08-05, before any run — Implementer A)

**Two real gaps found while surveying, stated up front, not fixed (per this
task's own "no re-derivation, no new null definitions" Constraint):**

1. **Null mismatch.** [[TASK-0201]]'s PTP1B survival (`dcc_low` k=10, AUC
   1.000, p=0.0027 vs. bar 0.003125) was certified under
   `nulls.graph_walk_patch_matched` — the *new* null construction that task
   itself built (Eden-growth on the contact graph, target_rg-matched).
   Both Leg 1 (`fpocket_conditional_analysis.py`) and Leg 2
   (`mechanism_discriminating_plant.py`) use `nulls.compact_patch` — the
   older, register-standard family, confirmed by reading both scripts
   directly. **This task does not rebuild either leg's null** (out of
   scope, per the task's own text) — so "survives/fails conditioning"
   below means *survives/fails under `compact_patch`*, not a re-test of
   the exact null that produced the original survival. Stated as an
   explicit qualifier on every downstream reading, not glossed over.
2. **k_modes mismatch.** [[TASK-199]]'s representative-observable choice
   uses `dcc_low` at `k_modes=20` (matching both legs' existing default);
   [[TASK-0201]]'s actual surviving cell is at `k_modes=10` — a different
   point on the same sweep. Using only k=20 would not test the cell being
   explained at all. **Resolution**: both legs run their existing,
   unmodified k=20 family (for cross-target consistency with
   KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN, already-published, untouched) *plus*
   one additional, clearly-separate, explicitly-labeled k=10 cell on
   PTP1B specifically (the actual [[TASK-0201]] replication target) — an
   additive registry entry in each script (a new `dcc_low`-at-k=10 score
   function/observable-registry row), not a change to any existing
   observable, band definition, or null. The k=10 cell is the
   interpretively load-bearing one for the reading rule below; the k=20
   family cells are reported for consistency, not substituted for it.

**Leg 1 mechanics**: add `PTP1B` to `fpocket_conditional_analysis.py`'s
`TARGETS` (CASPASE7 attempted after, per this task's own "if cheap"
hedge — included if it completes without incident, else reported as
attempted-but-deferred). `FAMILY_SIZE` becomes `3 observables x 4 targets
x 2 directions = 24` (`30` if CASPASE7 also lands), `alpha = 0.05/24`
(`0.05/30`) — reported explicitly, per this task's own Constraint. The
k=10 replication cell is compared against this same updated alpha, for
consistency with "no exceptions for a conditional analysis"
([[TASK-0200]]'s own precedent), not a separately-relaxed bar.

**Leg 2 mechanics**: `mechanism_discriminating_plant.py --target PTP1B`
(its own existing `--target` CLI override — KRAS_G12C/BCR_ABL1's stored
`grid.json` entries are never recomputed, protected by the script's own
existing skip-if-present resumability, not a new safeguard). "Shows mode
signature" is read as a **point-estimate trend** (AUC rises with `mode`
strength, flat/falls with `channel` strength on `dcc_low_from_L`) — per
[[TASK-0168]]'s own established convention, since that task's own
certification (gate1-4) rate was low (2/32 curves) even for the KRAS_G12C
signature it still reported as confirmed. Gate certification is reported
alongside for completeness, never required for "shows signature."

**Four-outcome reading rule** (verbatim from this task's own Intent
Contract, operationalized):

| Leg 1 (k=10, `compact_patch` null) | Leg 2 (`dcc_low_from_L`, k=10 and k=20) | Reading |
|---|---|---|
| Survives (clears within-band floor + null at updated alpha) | Mode-strength trend, not channel | **Strongest**: real, mechanistically-supported, non-redundant positive |
| Survives | No mode-vs-channel dissociation | Real, non-redundant, mechanism unexplained — do not attribute to the ensemble picture |
| Fails | Mode-strength trend present | Mechanistically real but contained in static geometry — [[TASK-0200]]'s strict-subset claim generalizes to the positive too (qualified by the null-mismatch caveat above) |
| Fails | No dissociation | Statistical survival, no mechanistic or informational support — report plainly |

**PTP1B's 5-residue active site** ([[TASK-0162]]'s own finding: elevates
reverse-direction floor to 0.90-0.91 elsewhere): checked directly before
trusting any Leg 1 within-band floor on PTP1B, not assumed benign — if the
within-band floor is similarly elevated, a "fails conditioning" reading is
weakened (a very strong floor is hard for anything to beat, mechanically,
independent of whether real signal exists) and this is stated alongside
the result, not silently absorbed into "no information added."

## In Progress

—

## TODO

- [x] Write the four-outcome reading rule into this file. **Before running.**
- [x] Leg 1: add PTP1B (+CASPASE7 — landed cheaply too) to the conditional analysis;
  update `FAMILY_SIZE` (18 -> 30).
- [x] Leg 1 wiring check: reproduce one published TASK-0200 cell — KRAS_G12C/BCR_ABL1/
  CARDIAC_MYOSIN fpocket AUCs reproduced byte-identical (0.7910/0.8618/0.5303).
- [x] Leg 1: report per-window `n`/`pos` power alongside every AUC.
- [x] Leg 2: run the 2-mechanism plant grid on PTP1B — 300 cells, 0 errors.
- [x] Leg 2 wiring check: reproduce KRAS_G12C `dcc_low_from_L` — exact match; re-assert
  adapter identity on PTP1B — bit-identical at both k=20 and k=10.
- [x] Joint reading against the pre-registered rule — see Done section: Leg 1 inconclusive
  (power), Leg 2 decisive (no mode signature; channel-type pattern instead).
- [x] Cross-link into TASK-0200, TASK-0168, TASK-0201 Done sections + `RESULTS.md`.
- [x] Hand the verdict to [[TASK-0184]] — quotable verdict sentence in Done section.

## Dependency

- [[TASK-0201]] (Done) — the positive being explained.
- [[TASK-0200]] (Done) — Leg 1's script and conventions.
- [[TASK-0168]] (Done) — Leg 2's grid and plants.
- [[TASK-0199]] (Done) — justifies the 3-observable subset.
- Feeds [[TASK-0184]] directly.

## Open Questions

- Is PTP1B's tiny active site (5 residues) a confound for either leg?
  [[TASK-0162]] already found it elevates that target's reverse-direction
  floor to 0.90–0.91. Check whether it distorts the within-band floor here
  before reading any result. **Answered**: checked directly — the
  forward-direction floor (the one that matters for Leg 1's own
  underpowering) was unremarkable (0.36-0.48). The active site does not
  explain Leg 1's inconclusive result; band population size does (see
  Done section).
- If CASPASE7 is included and disagrees with PTP1B, which governs? Neither —
  report both. PTP1B is the target with the positive; CASPASE7 is context.
  **Answered as planned**: CASPASE7 landed cheaply, clean negative on every
  well-powered cell (floor 0.80-0.90, nothing beats it) — reported as
  context in the Leg 1 table, not weighed against PTP1B's own reading.

## Done

**2026-08-06, Implementer A.**

### Verdict: the triangle does not close — Leg 2 rules out the strongest reading; Leg 1 cannot resolve the rest

**Leg 1 (conditional-on-fpocket) — inconclusive, not negative.** Added
PTP1B (+CASPASE7, landed cheaply too) to
`fpocket_conditional_analysis.py`'s `TARGETS`; `FAMILY_SIZE` updated
`18 -> 30` (3 observables x 5 targets x 2 directions), `alpha=0.05/30
=0.001667`, both reported explicitly per this task's own Constraint.
Wiring check passed: KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN fpocket AUCs
reproduced byte-identical (0.7910/0.8618/0.5303 — now [[TASK-0206]]'s
own pinned/authoritative values, landed independently this session,
corroborating [[TASK-0200]]'s original call to use fresh numbers).
**The forward-direction test of the actual survival cell (`dcc_low`
k=10, conditioned on fpocket) is underpowered at every one of the 4
pre-registered swept band widths** — band positives 2, 0, 0, 2 — never
reaching `MIN_POS_WELL_POWERED=3`. This is not specific to k=10: all
3 representative observables (`H_new_occ`, `dcc_low` k=20, `R_eff`) show
the identical underpowered pattern in the forward direction on PTP1B,
consistent with fpocket's own weak overall performance there
(AUC=0.4235, barely above chance — a genuinely different regime from
KRAS_G12C/BCR_ABL1's 0.79-0.86, where fpocket was strong). **Cannot
determine survives/fails for Leg 1 — reported as inconclusive, per this
task's own "report power, do not score anyway" instruction, not forced
into either reading.** Reverse direction (fpocket \| dynamics) was
well-powered on most windows and cleanly negative — fpocket adds
nothing beyond dynamics either, on this target.

**Leg 2 (mechanism plant) — decisive, and it rules out the "ensemble
mechanism" story.** `mechanism_discriminating_plant.py --target PTP1B`:
300 cells, 0 errors, `well_vs_channel.double_dissociation=true` (the
apparatus's own sanity control passes on this target). Wiring check:
KRAS_G12C `channel/dcc_low_from_L/0.0/0` reproduced exactly
(`point_auc=0.6751824817518248`, bit-for-bit); `dcc_low_from_L`
re-confirmed bit-identical to real `dcc_low` on PTP1B's own topology at
**both** k=20 and k=10 (max abs diff `0.0`), not assumed to transfer.

At **k=20** (the cross-target-consistent "representative"), `dcc_low`
rises under **both** mechanisms (channel 0.378->0.553, mode
0.378->0.628) — no clean dissociation, mode ending slightly higher.
At **k=10** — the exact cell [[TASK-0201]] found surviving — the
pattern is not just absent, it is **reversed** from the KRAS_G12C
mode-signature: `dcc_low` rises monotonically with **channel** strength
(0.337->0.443->0.714) and **falls** monotonically with **mode**
strength (0.337->0.238->0.176). This is a channel-type response
profile, not an ensemble/mode-type one — directly contradicting
[[TASK-0168]]'s own `"family": "ensemble"` label for this observable,
at the specific k that produced the program's one surviving positive.

### Joint reading against the pre-registered four-outcome table

Leg 2 answers the mechanism axis decisively: **no mode signature** —
rules out outcomes 1 and 3 (both require "shows mode signature"), which
means the "real, mechanistically-supported, ensemble-explained positive"
reading (outcome 1, the strongest possible claim) **is ruled out**, and
so is "mechanistically real but contained in geometry via the ensemble
picture specifically" (outcome 3). What remains live is a choice between
outcome 2 ("real and non-redundant, mechanism unexplained") and outcome 4
("statistical survival, no support") — **and Leg 1's power failure means
this task cannot distinguish between them.** The honest, complete
statement: *if* PTP1B's positive is real, its mechanism is not the
ensemble/mode-coupling picture the observable was named for — it behaves
like the channel/transport family instead, or like nothing distinguishable
at all. Whether it survives conditioning on static cavity geometry remains
open, blocked on power, not on this task's own execution.

### PTP1B's small active site — confound checked, not a clean explanation either way

[[TASK-0162]]'s own finding (elevated reverse-direction floor 0.90-0.91
on PTP1B/CASPASE7) does not explain Leg 1's forward-direction power
failure — the forward floor computations here were unremarkable (0.36-0.48
range, similar to the other targets); the underpowering is a **band
population** problem (too few real-pocket positives land inside fpocket's
own detected-cavity population at all, on a target where fpocket itself
is weak), not a floor-inflation problem. Stated precisely rather than
lumped under the general "small active site" caveat.

### Verdict sentence (for [[TASK-0184]]'s opening paragraph, quotable as-is)

*"The program's one surviving positive — `dcc_low` (k=10) on PTP1B,
significant under a corrected null — was tested by the two experiments
that could explain it. The mechanism test is decisive: at k=10, `dcc_low`
shows a channel-type response to synthetic perturbation (rises with
channel strength, falls with mode strength), not the ensemble/mode
signature the observable was named for and that partially held on
KRAS_G12C — ruling out the strongest possible reading of this positive as
a confirmed, mechanistically-supported, non-redundant finding. Whether it
is nonetheless real and simply unexplained, or a statistical survival with
no independent support, could not be resolved: the conditional-on-fpocket
test is underpowered on PTP1B at every pre-registered band width, because
fpocket itself performs only near chance on this target (AUC 0.42, unlike
0.79-0.86 on the mandatory set). The honest sentence is neither 'a rigorous
negative' nor 'a rigorous negative with one confirmed positive' — it is 'a
rigorous negative, plus one positive whose strongest possible explanation
is now ruled out and whose remaining explanations are underdetermined by
available power.'"*

### Cross-links

Added a short cross-reference note (this task's own name + one-line
pointer to the finding above) to [[TASK-0200]]'s, [[TASK-0168]]'s, and
[[TASK-0201]]'s own Done sections, and a `RESULTS.md` open-questions row
— all three previously stood without knowing about each other or about
PTP1B, per this task's own filing rationale.

### Tests

Existing `test_fpocket_conditional_analysis.py`'s `FAMILY_SIZE`-dependent
test updated (was hardcoded to the pre-TASK-0203 value `18`, now derived
from `len(TARGETS)` — the exact drift-guard [[TASK-0189]] built this
pattern to prevent). No other test changes needed — both legs' underlying
machinery is unmodified; only additive registry entries (`TARGETS`,
`OBSERVABLES["dcc_low_from_L_k10"]`) were added. Full suite: `1138 passed,
1 skipped, 2 xfailed`, no regressions.

### Out of scope, confirmed not needed

KRAS_G12C/BCR_ABL1/CARDIAC_MYOSIN were not re-run on either leg (Leg 1's
own script re-execution reproduced them byte-identical as a side effect
of the wiring check, not a deliberate re-run; Leg 2 used `--target PTP1B`
exclusively, never touching their stored cells). [[TASK-0201]]'s own
survival/bar/CI was not re-litigated — only explained. No new observable
beyond the pre-registered k=10 replication addition, which is not a new
observable but the exact already-existing `dcc_low` at a different,
already-established k-sweep point.

### Not done in this task (named for a follow-up, not built here)

Leg 1's PTP1B power problem is structural (fpocket itself is weak there)
and cannot be fixed by widening the band further within this task's own
"no new band definitions" Constraint. A future task wanting to resolve
outcome 2 vs. 4 would need either a fundamentally different conditioning
variable for PTP1B specifically, or to accept the question stays open.
