# TASK-0209 A known-answer cryptic-pocket instance set — verify the closed→open contrast per target, construct only where it fails

## Context

- ID: TASK-0209
- Title: establish, per target, that the apo structure's pocket is genuinely
  *closed* and the holo's genuinely *open* — the contrast every
  cryptic-pocket experiment in this register has assumed and never checked —
  and construct a verified closed instance for targets where it fails.
- Status: Done
- Resolution: done
- Resolution Note: 2/7 real-drug-ligand targets validated (KRAS_G12C, PTP1B). 5/7 INVALID; construction leg blocked -- no INVALID target has a verified-open holo reference. 2/3 mandatory targets (BCR_ABL1, CARDIAC_MYOSIN) are INVALID.
- **Thread: Implementer B (science).** Independent of [[TASK-0208]]; both feed
  [[TASK-0210]].
- Owner: Implementer
- Claimed By: —
- Claimed At: —
- Source: Reviewer thread + orchestrating user, 2026-08-06, following the
  BCR_ABL1 myristate finding; strengthens [[TASK-0169]]'s benchmark-
  discriminability result from an observation into a usable instrument.
- Priority: **P1 — [[TASK-0210]] cannot be evaluated on a benchmark that
  cannot discriminate, and [[TASK-0169]] already showed this one may not.**
- Dependency: [[TASK-0204]]'s positive-control machinery
  (`scripts/task0204_positive_control.py`), Done and reusable.

## Why this matters

Two measurements from 2026-08-06 make this unavoidable:

**1. BCR_ABL1's apo is not a cryptic instance at all.** `1OPL` chain A
contains **`MYR`** — myristic acid — bound in the myristoyl pocket, which is
*the* site this target is about. Verified directly:

```
1OPL (apo)  chain A: 451 res, 81-531   HETATM: MYR, P16
5MO4 (holo) chain A: 429 res, 83-531   HETATM: AY7, NIL
```

This is not a mislabel by the challenge givers — 1OPL is the autoinhibited
form, where ABL1's own myristoylated N-terminus occupies its own pocket to
lock the kinase off. That is the regulatory mechanism. But it means the
"apo" structure has the target pocket **held open by an endogenous lipid**;
`select("protein")` strips MYR and leaves the cavity it carved. It explains,
at a stroke, [[TASK-0169]]'s "pre-formed" finding, fpocket's 0.8618 on this
target, and the apo scoring *higher* druggability than the holo (0.566 vs
0.356). **Every apo→holo pocket-opening experiment run on BCR_ABL1 has been
testing nothing**, and that needs saying beyond [[TASK-0204]].

**2. KRAS_G12C, by contrast, is already a validated known-answer instance** —
measured, not assumed: apo druggability **0.001**, holo **0.886**, same
window, same pipeline, ligand stripped. Nothing needs constructing there. The
contrast is real and large.

So the instance set is not a construction project. It is a **verification**
project, with construction as the fallback for targets that fail.

## Intent Contract

- Outcome: a per-target table of (apo pocket druggability, holo pocket
  druggability, contrast) with an explicit VALID / INVALID / CONSTRUCTED
  verdict, and — for INVALID targets — a verified closed instance built and
  labelled as synthetic.
- Why required, not assumed: this register has scored ~366 cells against
  labels derived from apo/holo pairs whose closed→open contrast was never
  checked. One of them has now been shown to have no contrast at all.
- In Scope:
  - **Verification leg (do this first, it is most of the value).** Reuse
    `task0204_positive_control.py`'s ladder on every target with a usable
    apo/holo pair: score both structures at their own pocket window, ligand
    stripped. Report the contrast. Pre-register what contrast counts as
    VALID.
  - **Endogenous-occupancy audit.** BCR_ABL1's failure was caused by a HETATM
    nobody looked for. Enumerate every non-water HETATM in each apo structure
    and flag any sitting within contact distance of the pocket window. This is
    a grep-level check that would have caught it and should be permanent.
  - **Construction leg, only for INVALID targets.** Take the holo (pocket
    open, answer known) and restore apo-derived backbone/rotamers at the
    window until the pocket is verifiably closed; verify closure with fpocket
    as an **independent** check. Do **not** optimize against fpocket to
    achieve closure — that manufactures an instance fpocket cannot see, which
    is not the same thing as a closed pocket.
  - Record the resulting instance set as a first-class artifact for
    [[TASK-0210]] and [[TASK-0184]].
- Out Of Scope:
  - Re-running any scored cell against the corrected instance set. That is a
    large downstream job; this task produces the instrument and states the
    exposure.
  - Replacing `targets.yaml`'s apo/holo assignments. Flag, do not swap — the
    same discipline [[TASK-0192]] applied to the KRAS genotype finding, and
    for the same reason: every historical number is conditioned on the
    current assignment.
  - Searching RCSB for a replacement ABL1 apo. Worth doing, but it is its own
    task and this one must not block on a database search.
- Constraints And Invariants:
  - **A constructed instance is a control, not a benchmark replacement.** A
    computationally-closed pocket is not a naturally-closed apo state. Label
    it as synthetic everywhere it appears, or a referee will correctly call
    the downstream result circular.
  - Pre-register the VALID contrast threshold before scoring any target.
  - Every verdict is per-target and reported even when inconvenient.
- Planned Validation:
  - KRAS_G12C must come back VALID with roughly the already-measured
    0.001 → 0.886 contrast. If it does not, the harness has drifted and
    nothing else in the run is trustworthy.
  - BCR_ABL1 must come back INVALID, with the MYR audit firing as the stated
    reason. That is the known-answer check for the audit itself.
  - A constructed closed instance must, when its window is restored to the
    holo conformation, score open again — otherwise closure was achieved by
    breaking the structure rather than by closing the pocket.

## In Progress

## Pre-Registered VALID Contrast Threshold (fixed 2026-08-07, before scoring the
remaining 11 targets — Implementer B)

Two targets already have measured numbers (from [[TASK-0204]] (reopened)'s own
`positive_control.json`, produced before this task started): KRAS_G12C
(`apo_native_hit=False`, `holo_native_hit=True`) and BCR_ABL1
(`apo_native_hit=True`, `holo_native_hit=False`). The rule below was designed
against those two only and is fixed **before** running the remaining 11
targets — it is not reverse-engineered from the full 13-target distribution,
satisfying this task's own Open Question ("pick from the measured
distribution... or set it blind... either is defensible; silence is not") by
taking the blind option, using the two known-answer checks only as a sanity
gate on the rule, not as data to fit it to.

**Rule, reusing an existing bar rather than inventing one**: a target's
apo/holo pair is **VALID** iff `NOT apo_native_hit AND holo_native_hit`,
where `hit` is exactly [[TASK-0204]]'s own `_is_hit` criterion
(`overlap_frac >= 0.5 AND druggability_score >= 0.5`, already established in
this register by `conformational_search_measurement.py`/[[TASK-0185]] and
fpocket's own commonly-cited druggability cutoff) — not a new threshold
invented for this task. Rationale for reuse over invention: any bar picked
specifically for "how big a contrast counts" would be exactly the kind of
internal heuristic this project's own falsification-criteria convention
(TASK-0181 Phase B criterion #3, reused throughout) forbids; the hit
criterion is already load-bearing everywhere else in the register, so
reusing it here means "valid contrast" and "would register as a hit/miss in
every other experiment already run" are the same statement, not two.

All other combinations are **INVALID**:
- `apo_native_hit=True` (apo already druggable — not closed, BCR_ABL1's own
  failure mode).
- `holo_native_hit=False` (holo doesn't clear the bar either — no usable
  positive control at all, regardless of what the apo side shows).
- Both hit or both miss (no directional contrast either way).

**Sanity check against the two known-answer targets, before running anything
else**: KRAS_G12C → `NOT False AND True` = **VALID**. BCR_ABL1 →
`NOT True AND False` = **INVALID**. Both match this task's own Planned
Validation exactly. The rule is adopted as-is.

Continuous `overlap_frac`/`druggability_score` values are reported alongside
the boolean verdict for every target (per this task's own Constraint,
"reported even when inconvenient") so a near-miss can be told from a far one
even where the boolean lands on the expected side.

## TODO

- [x] Pre-register the VALID contrast threshold. **Before scoring.**
- [x] Endogenous-HETATM-near-pocket audit, every target.
- [x] Score apo + holo at each target's own window; build the contrast table.
- [x] VALID / INVALID verdict per target; KRAS and BCR_ABL1 as known-answer checks.
- [x] Construct + verify closed instances for INVALID targets (labelled synthetic). — attempted; blocked, see Done.
- [x] Round-trip validation on every constructed instance. — N/A, nothing was constructed.
- [x] State the register-wide exposure: how many scored cells used an INVALID pair?
- [x] Cross-link to [[TASK-0169]] — this converts its finding into an instrument.

## Dependency

- [[TASK-0204]] (In Progress) — the positive-control ladder, reused directly.
- [[TASK-0169]] (Done) — the benchmark-discriminability finding this extends.
- Feeds [[TASK-0210]], [[TASK-0208]] (target validity), [[TASK-0184]].

## Open Questions

- Does a real ABL1 kinase-domain structure without the N-cap/myristate exist
  in the PDB? If so it is a better BCR_ABL1 apo than any construction. Worth
  a separate task; do not block this one on it.
- What contrast threshold? KRAS's 0.001→0.886 is enormous; a target at
  0.3→0.6 is ambiguous. Pick from the measured distribution, and state that
  the threshold was set after seeing the distribution but before assigning
  verdicts — or set it blind and accept the noise. Either is defensible;
  silence is not.

## Done

### Framing correction 2026-08-19 — "2 of 7" understates the finding and invites the wrong objection

Reporting this as "2 of 7 targets valid" invites a reviewer to ask *"why did
you pick five bad targets?"* That is the wrong question, and the honest
decomposition answers it:

| Set | Source | Valid |
|---|---|---|
| **Challenge-mandated, scoreable** (KRAS_G12C, BCR_ABL1, CARDIAC_MYOSIN) | Challenge Statement Table 1 | **1 of 3** — only KRAS_G12C, and it is validated against a wild-type structure ([[TASK-0155]]) |
| **ASD extension** (PTP1B, GLUCOKINASE, CASPASE1, CASPASE7) | Challenge Statement §6, which *directs* participants to the Allosteric Database | **1 of 4** — only PTP1B |

**We did not select the failing targets — the challenge did.** c-Myc (1NKP)
is the fourth mandated target but has no holo structure, so it cannot carry an
apo-closed/holo-open contrast at all and is excluded from this audit by
construction, not by choice.

The extension was not target-shopping either: §6 states *"participants are
highly encouraged to test the robustness of their quantum approach on
additional targets of their choice… For this purpose, participants may refer
to the Allosteric Database (ASD)."* `config/targets.yaml`'s own block comment
marks these entries **"ASD expansion"**. We followed the challenge's own
instruction and its own named source.

**So the finding is stronger than the raw ratio suggests**: 2 of the 3
mandated scoreable targets fail, and extending into the database the challenge
recommends recovered only one more. The failure is systemic across two
independent target sources, not an artifact of our selection.

**Pointer added 2026-08-25 — three later results all strengthen the paragraph
above; none weakens it.** The 2026-08-19 text stands as written:

- [[TASK-0251]] found CARDIAC_MYOSIN **unscoreable by construction** — its
  mechanism is inter-subunit, and the challenge's own catalytic-domain scope
  removes the coupling before any observable is computed. That is a *third*
  independent defect on that target, on top of [[TASK-0169]]'s ligand finding
  and [[TASK-0222]]'s unscoreable mandated pair.
- [[TASK-0255]] calibrated the distality criterion in Ångströms: `MIN_HOP >= 2`
  corresponds to a median of only **7.5 Å** (minimum 2.09 Å), and **4 of 20**
  frozen-set targets meet a 15 Å separation bar while **0 of 20** meet 20 Å.
  The systemic failure this section describes is broader than target selection
  — it reaches the definition of "distal" itself.
- [[TASK-0254]] found **9 of 20** frozen-set targets already >=80% open in apo,
  with `fpocket_drug` scoring 0.854 on those versus 0.515 on the rest — the
  benchmark bundles static retrieval and cryptic-site discovery into one number.


**Verdict: 2/7 real drug-ligand targets are VALID (KRAS_G12C, PTP1B). 5/7 are
INVALID (BCR_ABL1, CARDIAC_MYOSIN, GLUCOKINASE, CASPASE1, CASPASE7) — and
critically, the construction leg's own precondition (a verified-open holo to
construct a closed instance from) fails for all 5, not just some. This is a
larger exposure than [[TASK-0169]]'s own BCR_ABL1 finding suggested.**

**Scope narrowed before scoring, and why.** Of `targets.yaml`'s 14 entries,
MYC_MAX has no `holo_pdb` (excluded, no pair to contrast). Of the remaining
13, only 7 have a genuine small-molecule `drug_ligand` code: KRAS_G12C,
BCR_ABL1, CARDIAC_MYOSIN, PTP1B, GLUCOKINASE, CASPASE1, CASPASE7. The other
6 (ATCase, HEMOGLOBIN, TAR_RECEPTOR, GLYCOGEN_PHOSPHORYLASE, PFK have no
`drug_ligand` at all; GROEL_SUBUNIT's is GroES, a protein, with its own
config comment stating the drug-contact definition doesn't apply) have no
derivable druggable pocket to be open/closed in the first place — checked
directly against every entry, not assumed from an initial blind run that
threw six "no resolvable pocket label" errors before this was diagnosed.
These six are classical-allostery targets this register uses for other
purposes, not cryptic-druggable-pocket benchmarks; the apo-closed/holo-open
question this task asks does not apply to them. Excluded and reported as
such, not silently dropped.

**Real bug found and fixed along the way (not in a file this task owns).**
`task0204_positive_control.py`'s (TASK-0204, reopened, currently claimed by
`Reviewer-thread (Opus)`) `_write_full_atom_with_window_chain` hardcodes 'B'
as the window's relabeled chain letter, assuming no existing chain in the
selected structure is already called 'B'. True for KRAS_G12C/BCR_ABL1
(`chains: ["A"]`) but false for CARDIAC_MYOSIN, whose holo is
`holo_chains: ["B"]` — relabeling the window to 'B' is then a no-op
collision, `is_window` matches every atom in the structure, and
`struct[~is_window]` is empty (confirmed directly: `IndexError: index 0 is
out of bounds for axis 0 with size 0`, reproduced before diagnosing).
Rather than edit a file under another thread's active claim, fixed locally
in `scripts/task0209_instance_verification.py`
(`_write_full_atom_with_window_chain_fixed`, picks a genuinely unused chain
letter) and monkeypatched into the imported module before calling
`run_target` — `task0204_positive_control.py` itself is untouched. Flagged
here for whoever next works TASK-0204's reopened thread: this bug affects
any future target whose own chain letter is 'B'.

**Full contrast table** (`overlap_frac`/`druggability_score` at each
target's own 12-residue window, ligand stripped, `hit` = TASK-0204's own
`overlap_frac >= 0.5 AND druggability_score >= 0.5`):

| Target | apo overlap | apo drug | apo hit | holo overlap | holo drug | holo hit | Δdrug | Verdict |
|---|---|---|---|---|---|---|---|---|
| KRAS_G12C | 0.750 | 0.001 | miss | 1.000 | 0.886 | **hit** | +0.885 | **VALID** |
| PTP1B | 0.417 | 0.046 | miss | 0.750 | 0.757 | **hit** | +0.711 | **VALID** |
| BCR_ABL1 | 0.917 | 0.566 | **hit** | 1.000 | 0.356 | miss | -0.210 | INVALID |
| GLUCOKINASE | 1.000 | 0.759 | **hit** | 1.000 | 0.229 | miss | -0.530 | INVALID |
| CASPASE1 | 0.667 | 0.679 | **hit** | 0.667 | 0.030 | miss | -0.649 | INVALID |
| CARDIAC_MYOSIN | 0.917 | 0.001 | miss | 1.000 | 0.166 | miss | +0.165 | INVALID |
| CASPASE7 | 0.429 | 0.582 | miss | 0.857 | 0.010 | miss | -0.572 | INVALID |

**Known-answer checks passed, as pre-registered before running the
remaining 11 targets**: KRAS_G12C → VALID, BCR_ABL1 → INVALID. Both match.
The rule was adopted blind (not fit to the full distribution) and held.

**HETATM audit — two of the five INVALID targets have an identified
culprit, three do not.** Every non-water HETATM in each raw apo deposition,
flagged if within `pocket_contact_cutoff` of the pocket window and not a
coordination-range (≤3.0 Å) cofactor of a known ligand:

- **BCR_ABL1**: `MYR` (myristic acid), 3.47 Å from the window, unexplained
  — [[TASK-0169]]'s finding, reused here as the known-answer check, not
  re-discovered.
- **GLUCOKINASE**: `MRK`, 2.45 Å from the window, unexplained — a **new**
  finding, same failure shape as BCR_ABL1's MYR (an endogenous/co-crystallized
  small molecule sitting in the allosteric pocket in the "apo" deposition,
  holding it open). `MRK`'s chemical identity was not looked up beyond its
  RCSB three-letter code (no network lookup available in this environment);
  flagged for whoever picks this up next.
- **CASPASE1**: no HETATM flagged near the window at all. Apo is hit-True
  (0.679 druggability) with nothing nearby to explain it — a genuinely
  different failure mode from BCR_ABL1/GLUCOKINASE: not an occupied pocket,
  an intrinsically open one. Consistent with CASPASE1's own biology (an
  inflammatory protease with a known constitutively-accessible active-site
  vicinity) but not chased further — out of this task's own scope
  (endogenous-occupancy audit, not a full structural explanation of every
  failure).
- **CARDIAC_MYOSIN / CASPASE7**: no HETATM flagged, and no apo-hit either —
  these two fail for a third, distinct reason (below), not an occupancy
  artifact.

**Construction leg: attempted, blocked by its own stated precondition, for
all 5 INVALID targets — reported, not forced.** The task's own In-Scope
text reads "take the holo (pocket open, answer known) and restore
apo-derived backbone/rotamers... until closed." That wording assumes
`holo_native_hit=True` for whichever targets land INVALID. Checked directly
against the table above: **`holo_native_hit=False` on all 5 INVALID
targets, without exception** — including BCR_ABL1 and GLUCOKINASE, the two
"apo already open" cases. There is no target in this set where the apo side
alone is the problem and the holo side is a clean, verified reference to
build from. Constructing "a closed instance" by grafting apo character onto
a holo structure that the pipeline itself cannot certify as open at this
bar would not be a controlled construction — there would be nothing
verified to round-trip back to, which is exactly the check this task's own
Planned Validation requires ("restored to holo conformation must score open
again"). Forcing it through was rejected as producing an artifact rather
than an instrument. Two structurally different reasons sit under the same
"holo misses" line and are worth separating for whoever picks this up:
  - **BCR_ABL1 / GLUCOKINASE / CASPASE1**: apo scores as *more* druggable
    than holo (Δdrug strongly negative) — an inverted, not merely absent,
    contrast. `holo_optimized_trials` (already run as part of the ladder,
    8 SA-repacking trials per target, ligand-stripped holo) mostly MISS too
    (BCR_ABL1 6/8, GLUCOKINASE 7/8, CASPASE1 8/8) — repacking closes these
    windows further, consistent with [[TASK-0204]]'s own finding that
    energy-minimizing repack trends toward tighter packing, not more open.
    This data exists and is reported in `results/tasks/0209_instance_
    verification/instance_verification.json`'s own `ladder.holo_optimized_
    trials`, but is not labelled a "constructed closed instance" here
    because there is no verified-open state for it to round-trip against.
  - **CARDIAC_MYOSIN / CASPASE7**: near-zero or positive Δdrug (not
    inverted) but holo still misses outright (0.166, 0.010) — the pipeline
    cannot see either state as druggable at this window/bar. Plausible,
    not chased further: the 12-residue nearest-to-centroid window may not
    capture these targets' actual cavity shape well (both have known
    caveats elsewhere in the register — CARDIAC_MYOSIN's `core==consensus`
    is flagged degenerate in its own `targets.yaml` comment), or these
    allosteric sites are genuinely shallow/hard for fpocket regardless of
    ligand-stripping. A window-size or window-selection sweep would be the
    natural next step; out of this task's own scope.

**Register-wide exposure, stated per this task's own Out-Of-Scope (state
it, do not re-run the register).** This register's standing "mandatory
target set" is KRAS_G12C, BCR_ABL1, CARDIAC_MYOSIN, cited as the primary
gate in the large majority of experiments in `RESULTS.md`. **2 of those 3
(BCR_ABL1, CARDIAC_MYOSIN) are INVALID under this audit — only KRAS_G12C is
a validated apo-closed/holo-open cryptic-pocket instance.** Every prior
result phrased as "passes on 2/3 mandatory targets" or "3/3" cannot be read
as "passes on 2 or 3 genuine cryptic-pocket contrasts" without checking
which targets specifically — this does not retroactively invalidate any
individual measured number (most of the register's observables, e.g.
GNM/CTQW-family ones, do not depend on fpocket-druggability contrast at
all), but it does mean the mandatory-3 gate itself is, for druggability-
contrast-dependent claims specifically, running at 1/3 validated coverage,
not 3/3. Of the extended pair used in some later experiments (row 64's
`FAMILY_SIZE` extension, [[TASK-0203]]), PTP1B is VALID and CASPASE7 is
INVALID. Overall: **2/7 (29%) of this register's real-drug-ligand targets
are validated known-answer cryptic-pocket instances** under this project's
own existing hit criterion, reused rather than invented.

Full trial-level data: `results/tasks/0209_instance_verification/
instance_verification.json`. Script:
`scripts/task0209_instance_verification.py` (imports and reuses
`task0204_positive_control.run_target` directly; does not reimplement the
ladder). Cross-links [[TASK-0169]] (the finding this converts into a
reusable instrument) and feeds [[TASK-0210]]/[[TASK-0208]] (target
validity) with a concrete per-target verdict list rather than a single
observation.

---

**Addendum, 2026-08-26 ([[TASK-0278]]) — the HETATM audit's own reusable
classification rule, written down, and its blind spot fixed.**

This task's own `hetatm_audit` already flagged BCR_ABL1's `MYR` as
"unexpected_near_pocket" (`min_dist_to_pocket_window=3.47`) at the time
this file was written — the underlying measurement existed from day one.
What was missing was (a) a *reusable, named* classification rule
distinguishing a legitimate apo occupant from a benchmark-breaking one,
applied consistently across every target, and (b) live verification of
the register's other apo structures by the same standard (this task never
ran that audit on [[TASK-0243]]'s own 22-target config, which did not yet
exist when this task ran).

**The rule, fixed by [[TASK-0278]]:**
1. Enumerate every non-water HETATM group directly from the resolved
   structure (`backend.rcsb.ligands_and_sites` — NOT the RCSB Data API's
   own `nonpolymer_bound_components` summary field, which [[TASK-0270]]
   already found silently omits non-metal-coordinating ligands).
2. Exclude any HETATM group that is **peptide-bonded** to a normal
   neighbouring residue (C-N distance <1.5 Å either side) — a covalently
   modified residue embedded in the chain (e.g. `M3L`/N-trimethyllysine,
   `ACE`/N-terminal acetyl cap), not a free ligand. `Bio.PDB`'s own hetero
   flag does not distinguish these; a real bond-distance check is
   required (found necessary directly — an early resnum-adjacency-only
   version of this check produced false positives).
3. Classify what remains via `backend.rcsb.classify_ligand`
   (cofactor / solvent-ion / ligand / drug), **with one required
   correction**: `classify_ligand`'s own top-level "solvent/ion" bucket
   silently includes lipids/fatty-acid additives via `_is_aliphatic_
   additive` (built for the live app's own display purposes, where most
   surface-bound fatty acids really are inert) — `MYR` itself is the
   exact case this swallows. Re-check every "solvent/ion" verdict against
   `_is_aliphatic_additive` directly and flag a hit separately
   (`broken_lipid_pocket_occupant`), the same correction [[TASK-0214]]'s
   own `_is_buffer_or_water` already made privately for its candidate
   filter, generalised here into a reusable function
   (`task0278_apo_contents_audit.apo_ligand_verdict`).
4. **The decisive check is not "is this ligand natural," it is whether it
   overlaps the SPECIFIC pocket window being scored** — a cognate ligand
   at a *different* site (KRAS's GDP at the nucleotide pocket, BCR_ABL1's
   own `P16` at the ATP site) does not confound the benchmark; the same
   molecule at the *scored* site does. Checked directly, not assumed, via
   heavy-atom/binding-site overlap against each target's own pocket
   window: `BCR_ABL1` (`MYR`, 75% window overlap), `GLUCOKINASE` (`MRK`,
   88%), and — newly found, not in [[TASK-0278]]'s own original filing —
   `PKR_MITAPIVAT`/`PKR_AG946` (`O9I`, an allosteric modulator already
   bound in the shared "apo" `7FS3`, 91–92% window overlap, the single
   worst case found) are genuinely pocket-confounded. `CARDIAC_MYOSIN`'s
   `VO4` (vanadate) does **not** overlap its own scored window at all
   (0%) — this task's own "suspect" classification for `8QYP` is
   corrected: not a pocket confound by this test, whatever its other
   caveats as a chemically-trapped state.

Full per-structure results: `results/tasks/0278_apo_contents_audit/
apo_contents_audit.json`. See [[TASK-0278]]'s own Done section for the
BCR_ABL1 decision and the full register-wide table.
