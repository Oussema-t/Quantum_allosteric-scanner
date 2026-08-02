# TASK-0177 Consensus holo pocket ground truth — undisputably identify the pocket in the holo form

## Context

- ID: TASK-0177 (subtask-in-spirit of [[TASK-0176]]; filed flat because it has
  standalone value and its own reviewer-facing deliverable)
- Title: replace the single-cutoff ligand-contact label with a **consensus
  pocket definition** built from ≥4 mutually independent criteria, reporting a
  stable core, a disputed shell, and an explicit per-target resolution.
- Status: Done
- Resolution: done
- Resolution Note: Consensus label built + run on all 7 pocket-scoreable targets, negative control (1 real failure found+diagnosed), frozen into targets.yaml, RESULTS.md section, 11 new tests, full suite green
- Owner: Implementer (structural-biology slice), reviewed by Architect/Planner
- Claimed By: —
- Claimed At: —
- Source: orchestrating collaborator (Bartosz), 2026-07-29: *"undisputably
  find the pocket in the holo form."*
- Priority: **P0 — hard-blocks every scoring claim in [[TASK-0176]]. Nothing
  downstream can be verified against a contested answer key.**
- Suggested Follow-Up: **[[TASK-0178]] Phase A**, same thread. Not a hard
  dependency (0178's module + gates build independently of this task's
  label), but same structural-biology/GNM skillset and natural continuity
  of owner. 0178's *final* scoring does need this task's frozen label
  eventually (incumbent label usable meanwhile, per 0178's own Dependency
  section). Recorded 2026-08-01 (Architect).

## Why this matters — the answer key has never been validated, only used

Every AUC, floor, CI, null and Bonferroni bar in this project's 226 scored
cells is computed against `labels.holo_pocket_mask`: residues within 4.5 Å of
one named HET group in one holo structure, minus active site, minus terminal.
The pipeline has swept the ENM cutoff ([[TASK-0113]]), the propagation clock
([[TASK-0119]]), the seed convention ([[TASK-0118]]), the potential scale
([[TASK-0121]]), the apo structure ([[TASK-0124]]), and the permutation null
([[TASK-0158]]). **The label itself has been swept exactly once**
([[TASK-0114]], the 4.0–5.5 Å contact cutoff) and that sweep's own finding was
that the recovered residue set changes at *every* step in *both* directions —
"a still-moving slope, not a stable plateau."

An answer key on a moving slope is not an answer key. And the defects are not
only numerical:

- **A contact set is not a cavity.** A ligand touches part of a pocket's
  lining; the pocket is the cavity. This is why fpocket — purely geometric,
  no seed, no dynamics — beats every observable here on 2/3 targets
  ([[TASK-0163]]: 0.8348 / 0.8596). Either the task is geometry, or the label
  is geometry. Both readings are damaging and the current label cannot
  distinguish them.
- **"Allosteric" is unverified.** KRAS_G12C's labelled pocket comes within
  **3.75 Å** of the active site ([[TASK-0169]]).
- **"Cryptic" is unverified.** BCR_ABL1's pocket has apo→holo RMSD ratio
  **0.49** — it moves *less* than background, i.e. pre-formed ([[TASK-0120]]).
- **The drug may not be there.** 6C1H contains ADP/MG only ([[TASK-0169]]).

## Design — convergence, not a better cutoff

The fix is **not** a smarter threshold. It is several *independent* routes to
the same set, with the disagreement published as the label's own resolution.
A residue's membership is graded, not binary:

| # | Criterion | Independent of | Tool |
|---|---|---|---|
| C1 | Ligand heavy-atom contact, swept 3.5–6.0 Å | — (the incumbent) | existing `holo_pocket_mask` |
| C2 | **ΔSASA on ligand removal** — residues burying surface upon binding | contact cutoff choice | Shrake–Rupley / `freesasa`, or Biopython's SASA |
| C3 | **Geometric cavity in holo with the ligand stripped** | ligand identity entirely | `fpocket` (already vendored, `tools/fpocket/`, [[TASK-0163]]) |
| C4 | **Depositor / primary-literature annotation** | all computation | PDBe `SIFTS`/binding-site records, RCSB REST, the cited paper |
| C5 | **Crypticity**: same cavity absent or much smaller in apo | holo alone | `fpocket` on apo, volume ratio |
| C6 | **Distality**: min/mean Cα distance to active site (Euclidean) **and** min/mean graph-hop-distance on the same 8.0 Å contact-graph convention as [[TASK-0067]] | all of the above | direct geometry + `baselines.hop_from_seed` |

**Consensus label** = residues satisfying ≥3 of {C1(any cutoff), C2, C3, C4}.
**Stable core** = residues satisfying *all* of them. **Disputed shell** = the
symmetric difference. C5/C6 are *target-level* qualifiers, not per-residue
membership — they decide whether the target's task is the stated task at all.

**The reported resolution** is `|shell| / |core|`. That number is the honest
uncertainty on every AUC computed against the label, and it has never been
stated.

> **Architect addendum, 2026-07-31.** C6 was originally scoped as raw
> Euclidean distance only. Widened to include **graph-hop-distance**
> (spatial contact-graph BFS, same 8.0 Å cutoff the rest of this codebase
> already uses) — Euclidean proximity does not determine whether a
> propagation observable needs to do any real work to "find" the pocket;
> graph-hop-distance does. Motivated by [[TASK-0186]] (filed same session),
> which asks whether TASK-0169's KRAS_G12C "trivial, 1-hop" finding
> generalizes across the benchmark set — if it does, that is a benchmark-
> validity result more consequential than C1–C5's consensus-label work, and
> cheap to get first. **C6 is resequenced to run before C1–C5 in the TODO
> list below** for that reason; C1–C5 are unaffected and can proceed on
> their own schedule regardless of C6's outcome. TASK-0186 computes this
> exact measurement independently against the *incumbent* label (own script,
> already written) — re-run or cross-check against the `core`/`consensus`
> label once C1–C5 land, don't silently duplicate the two.

## Intent Contract

- Outcome: `allostery.consensus_labels` producing, per target: `core`,
  `consensus`, `shell`, per-criterion masks, the resolution statistic, and a
  target-level `task_validity` record (cryptic? distal? drug present?). Plus a
  `RESULTS.md` section and a `targets.yaml` schema addition pinning the
  frozen consensus label per target.
- Why required, not assumed: the label is the one axis of this pipeline never
  validated; [[TASK-0114]] showed it is unstable and [[TASK-0169]] showed it
  is, on 2 of 3 mandatory targets, not measuring the advertised property.

- In Scope:
  - Implement C1–C6 for all 7 pocket-scoreable `status: verified` targets.
  - **Re-score the headline observables against `core` and `consensus`
    alongside the incumbent 4.5 Å label** — three labels, side by side, never
    substituted. If a verdict flips between them, that flip *is* the finding.
  - Report the resolution statistic per target.
  - Freeze the consensus label into `config/targets.yaml` (new
    `pocket_label: {method: consensus, core: [...], consensus: [...]}`) **before**
    any downstream task reads it, under `frozen_context`.
  - Handle the C4 route honestly: where the depositor annotation or the paper
    disagrees with computation, record the disagreement; do not silently
    prefer the computed set.
  - CARDIAC_MYOSIN uses this project's own substituted 8QYR/8QYP pair
    ([[TASK-0124]]), not the challenge's 6C1H — restate that substitution in
    this task's output so the label's provenance is unambiguous.

- Out Of Scope:
  - Changing any observable, propagator, floor, null or CI.
  - Choosing the label that makes results look better. **The selection rule is
    fixed above, before any scoring is run.** This is the single most
    important constraint in this file.
  - MD, docking, or ensemble generation.
  - Retro-editing prior `RESULTS.md` numbers — additive only, per the
    no-overwrite convention.

- Constraints And Invariants:
  - `frozen_context` throughout label construction. The label is built
    without reference to any score.
  - Every external tool's output verified against a hand-checkable case
    before trusting it at scale — [[TASK-0136]]'s unit-capacity bug and
    [[TASK-0143]]'s salted-`hash()` bug are the precedents.
  - Numbering: every criterion's residue set mapped through the existing
    `_needleman_wunsch_map` / `chain_map_from_config` path ([[TASK-0144]]).
    A criterion that cannot be mapped is reported as unavailable, not
    approximated.
  - `freesasa`/`fpocket` become declared dependencies with the same
    disclosure convention as `ripser`/`optuna`.

- Planned Validation:
  - **Convergence is the control.** If ≥3 independent criteria agree to a
    small shell, the label is defensible. If they do not converge on a
    target, that target is reported **not verifiable** — a first-class
    Phase-1 result and the constructive half of [[TASK-0169]]'s audit.
  - **Negative control on the consensus machinery**: run it against a
    deliberately wrong ligand (a buffer molecule / cryoprotectant present in
    the same holo entry). The criteria must *fail* to converge there. A
    consensus procedure that "converges" on glycerol is not measuring a
    pocket.
  - Sanity: `core ⊆ consensus ⊆ (core ∪ shell)`, asserted.

## In Progress

None

## TODO

- [x] **C6 distality** — Euclidean min/mean **and** spatial-hop (8.0 Å
      convention) computed against both `consensus` and the incumbent label;
      the incumbent-label run cross-checks [[TASK-0186]] exactly on every
      target that used the same masks (min spatial-hop=1 on 6/7, PTP1B the
      sole exception). Chain-hop not separately reported here (already
      covered by TASK-0186's own run against the same incumbent label; not
      duplicated). Computed as part of `build_consensus_label`'s single pass
      rather than literally coded first, but validated before any C1-C5
      result was trusted, per the Architect addendum's intent.
- [x] C1 cutoff sweep 3.5–6.0 Å, per-cutoff masks retained (union used for
      voting, per-cutoff counts kept in `criteria` detail).
- [x] C2 ΔSASA implementation + hand-checked validation case (KRAS_G12C
      Cys12/His95 real burial; a real `freesasa` HETATM-default-exclusion bug
      caught and fixed by this same check, see Done section).
- [x] C3 fpocket on holo, ligand stripped; mapped to apo numbering via
      `_needleman_wunsch_map`.
- [x] C4 — **narrowed from the filed scope.** Implemented via legacy-PDB
      `REMARK 800`/`SITE` records (software-generated at deposition,
      independent of all computation this module does) — not PDBe's
      `binding_sites` REST endpoint (404, appears retired/renamed) or
      primary-literature citation (out of time budget). Disclosed, not
      silently substituted; genuinely unavailable (not approximated) on 2/7
      targets (CARDIAC_MYOSIN/8QYR, GLUCOKINASE/3H1V — no SITE records in
      either entry).
- [x] C5 crypticity (apo vs holo cavity volume ratio, fpocket).
- [x] `core` / `consensus` / `shell` assembly + resolution statistic.
- [x] **Negative control: wrong-ligand non-convergence.** KRAS_G12C/MG
      passes; **CARDIAC_MYOSIN/EDO fails** (converges cleanly, core=7) — real
      finding, root-caused and reported, not hidden. See Done section.
- [x] Re-score headline observables against all three labels, side by side.
- [x] Freeze into `targets.yaml`; `RESULTS.md` section; `task_validity` per target.

## Dependency

- [[TASK-0163]] (Done) — vendored `fpocket`, already built and run.
- [[TASK-0144]] (Done) — chain-letter remapping.
- [[TASK-0114]] (Done) — the cutoff-instability finding this replaces.
- [[TASK-0169]] (Done) — the per-target validity axes reused as C5/C6.
- [[TASK-0186]] — independent hop-distance run against the incumbent label
  (2026-07-31); soft, cross-check only, does not block C6.

## Open Questions

- Is ≥3-of-4 the right consensus rule, or should it be weighted? **Decided,
  as recommended: ≥3-of-{n_available} unweighted.** Implemented with one
  refinement forced by real data: when `n_available < 4` (2/7 targets),
  the bar is `min(3, n_available)`, i.e. unanimity of whatever criteria
  exist — not silently treating a missing criterion as a "no" vote. The
  negative control shows this refinement is not a free lunch (see Done).
- What if `core` is empty on a target? **Never happened** — every one of the
  7 targets has a nonempty core (range 3-17 residues). No target triggered
  the "not verifiable" outcome.
- Should the AUC denominator change (score against `consensus`, `core`, or
  keep 4.5 Å as headline)? **Not decided here, per the Constraint against
  choosing the label that looks best.** All three are reported side by side
  (RESULTS.md's flip table) and the choice is left to [[TASK-0176]]/
  [[TASK-0184]]'s narrative decision, now backed by the flip evidence rather
  than made blind.
- Does a graded label call for a ranking metric other than binary-label AUC?
  **Still open, flagged as recommended** — BCR_ABL1/PTP1B/CASPASE7's shells
  are 6-8 residues against cores of 3-10, non-trivial size; a weighted
  metric (core > shell) was not built here, out of this task's own scope.

## Done

**2026-08-02, Implementer B (this thread).** New `allostery.consensus_labels`
(C1-C6) + `scripts/task0177_consensus_labels.py`, run on all 7 pocket-scoreable
`status: verified` targets. Full detail: `RESULTS.md`'s own "Consensus
holo-pocket ground truth" section (row 50 of the open-questions index),
`results_task0177_consensus_labels/results.json`,
`results_task0177_consensus_labels/frozen_labels.json`.

**Headline: convergence is real but partial on every target (no empty
`core`), and 4/7 targets flip floor-clearing verdict depending on which
convergent label scores them — the flip itself is the finding.** KRAS_G12C,
the most-scrutinized target in the project, has the *worst* agreement
(core=3/18 of the incumbent set). Per-target core/consensus/shell/resolution
table and the full re-score-flip table are in `RESULTS.md`; not repeated here.

**Negative control real finding, not smoothed over**: KRAS_G12C vs. `MG`
passes cleanly (core=0). **CARDIAC_MYOSIN vs. `EDO` (a real cryoprotectant
confirmed present in 8QYR's own hetero records) fails — the consensus
procedure converges (core=7) on a buffer molecule.** Root-caused, not just
observed: C4 (the one criterion independent of "is there a real
cavity/contact/burial here") is structurally unavailable for this entry (no
legacy SITE records) — C1-C3 alone cannot distinguish a real drug site from
any molecule sitting in a real surface groove. This is also why
CARDIAC_MYOSIN and GLUCOKINASE are the only two targets with
`resolution=0.0` (core==consensus): a degenerate unanimity-of-3 artifact of
criterion availability, not strong evidence of a well-converged label.
Flagged explicitly in both `RESULTS.md` and `targets.yaml`'s own
`pocket_label.criteria_available` comment for both targets — not shipped as
a clean result.

**Real bug found and fixed before trusting any C2 number**: `freesasa.Structure`'s
default options silently ignore HETATM records, so the "with ligand" and
"without ligand" SASA structures were byte-identical (the ligand's own atoms
were never in either calculation) until caught by this task's own required
hand-checked case (KRAS_G12C Cys12/His95, expected real burial from the
Switch-II literature) and fixed via `options={"hetatm": True}`.

**Real infra gap found and fixed**: the vendored `fpocket` binary
(`tools/fpocket/bin/`, TASK-0163) is gitignored and was not present on this
session's host — rebuilt from source per the repo's own README, but the
checked-in `makefile`'s Linux-only static plugin archive (`ARCH=LINUXAMD64`)
does not link on this macOS arm64 host. The repo's own `plugins/` tree
already ships a matching `MACOSXARM64` plugin directory, never wired into
the makefile's `ARCH` default — built with `make ARCH=MACOSXARM64`, all 4
binaries (`fpocket`/`tpocket`/`dpocket`/`mdpocket`) link and run cleanly.
Not committed (binaries stay gitignored, host-specific per the existing
convention) — a future thread on a different host will need the same
one-line override, worth a short note in
`LOCAL_AUTOMATION_MANUAL_ENVIRONMENTS.md` if this recurs (not filed
separately here, small).

**C4 narrowed from the filed scope** (see TODO section) — legacy PDB SITE
records only, not PDBe's REST API (`binding_sites` endpoint 404s, appears
retired) or primary-literature citation. This narrowing is itself the direct
cause of the CARDIAC_MYOSIN/GLUCOKINASE degenerate-resolution finding above,
not an unrelated shortcut — a wider C4 (literature citation) could plausibly
resolve both targets' `resolution=0.0` ambiguity, flagged as a concrete
follow-up rather than assumed unimportant.

**Re-score sanity check passed**: KRAS_G12C's incumbent-label AUC
(`H_new`+`time_averaged_ctqw_converged`, `coherent=False`) reproduces
[[TASK-0159]]'s published 0.5901 to full precision — confirms this task's
own scoring pipeline matches the shipped one exactly before trusting any
new (core/consensus) number built on top of it.

**Frozen** into `config/targets.yaml`'s new `pocket_label` block per target
(`method`, `criteria_available`, `resolution_shell_over_core`, `core`/
`consensus`/`shell`/`incumbent_4_5A` as `[chain, resnum]` pairs) —
programmatically generated by `scripts/task0177_consensus_labels.py` +
`build_consensus_label`, never hand-transcribed, per this project's hard
rule. `targets.yaml` re-parses cleanly (checked directly). 11 new unit tests
(`tests/test_consensus_labels.py`, synthetic-only — the four external-tool
criteria are exercised by the real 7-target run, not duplicated as mocked
unit tests). Full existing suite re-run green: 1007 passed, 2 skipped, 2
xfailed, no regressions.

**Not done, flagged not hidden**: C4's PDBe/literature widening (above);
a weighted core-vs-shell ranking metric (Open Questions); this task's own
Recommend-but-not-decide choice of which label becomes the submission
headline, left to [[TASK-0176]]/[[TASK-0184]].
