# INV-0006 Seed/source definition for CTQW/GSR propagation — cross-cutting (`propagators.py`, `select.py`, `ceiling.py`, `run_challenge.py`)

## GAUGE

None. Checked directly against real data (not assumed) — see KNOB below.
This record does **not** classify seed cardinality/coherence as a GAUGE,
despite [[TASK-0118]]'s own Intent Contract originally asking for exactly
that classification (§ "(3) an `.ai/invariants/INV-XXXX` record is filed
classifying seed definition as a GAUGE"). The real sweep below refutes
that framing on at least one mandatory target; recorded as a KNOB instead,
per this project's own evidence-first convention (report what the data
shows, not what the filing hoped for).

## KNOB

| Transformation | Test | Status |
|---|---|---|
| Seed cardinality/coherence (single residue vs. k-subset vs. full active-site array, coherent vs. incoherent) | **KNOB-CHARACTERIZED, real data.** `scripts/seed_convention_sweep.py`, all 3 mandatory targets, `H_new` default config, `time_averaged_ctqw`, `t_max=15`/`n_steps=500` (run_challenge.py's own live defaults — this sweep isolates the seed axis only, does not also vary the clock, TASK-0119's separate job). AUC spread across `{single, k_subset, full_coherent, full_incoherent}`: **KRAS_G12C 0.326**, BCR_ABL1 0.079, CARDIAC_MYOSIN 0.049. | **KNOB, not GAUGE — confirmed on real data.** |

**KRAS_G12C decisively fails the panel's own stated GAUGE criterion**
("AUC spread > 0.1 → it is a SIGNAL, not a gauge, the pipeline has no
defined initial condition") — 0.326, more than 3x the threshold, and
larger than the panel's own synthetic pre-estimate (≈0.3, occupation
Spearman 0.61). This is not merely "confirmed the synthetic estimate
transfers" — it is worse on real data for this target. BCR_ABL1 and
CARDIAC_MYOSIN sit *below* the 0.1 threshold (0.079, 0.049) — seed
cardinality is far less consequential for those two targets specifically,
though still non-zero and not asserted as a coincidence-free gauge either
(3 targets is not enough to claim a stable per-target pattern; recorded as
an observation, not a finding).

**A second, narrower observation**: within the "full active-site array"
cardinality, coherent vs. incoherent alone (holding the residue set fixed)
moves AUC far less than cardinality does — KRAS_G12C: 0.4533
(coherent) vs. 0.4614 (incoherent), a 0.008 difference, dwarfed by the
0.326 single-vs-full spread. **The dominant driver of the seed-gauge
problem is how many residues are seeded, not whether they're seeded
coherently or incoherently** — worth stating plainly since the panel
review's own framing (and this task's own Intent Contract) emphasizes the
coherent/incoherent distinction specifically, which turns out to be the
smaller of the two effects on real data, at least for this operator/clock
combination.

- `t_max`/`n_steps` (interaction with the seed choice above — a wider or
  narrower time window could plausibly change how much the seed choice
  matters) — not characterized here, explicitly [[TASK-0119]]'s own scope,
  not conflated with this record per [[TASK-0118]]'s own Out Of Scope note.

## SIGNAL

- Whether the *chosen* convention (full active-site array, incoherent
  mixture) itself carries real discriminating signal beyond a trivial
  proximity baseline — this is exactly what floor/ceiling/actual
  re-measures under the new convention, not a property of the seed
  definition in isolation. See [[TASK-0118]]'s Done section for the
  re-run numbers; not duplicated here.

## PROVENANCE — not GAUGE, not KNOB (added 2026-08-24, [[TASK-0232]])

Every row above characterizes *how many* residues the seed contains and
*how* they're combined (cardinality, coherence) — real transformations of
one well-defined quantity (the active-site residue set), correctly
classified as KNOB. **This record contained zero mentions of *whether* the
seed is an active site at all** until [[TASK-0216]] found that, on 9 of 13
real targets, `functional_indices` had silently fallen through to its
last-resort tier: the top-5 highest-degree residues, a purely topological
quantity with no relationship to function.

**Classification: neither GAUGE nor KNOB.** A GAUGE transformation must not
change the answer; a KNOB transformation may change the answer while still
answering the *same question* under a different modeling choice (this
record's own cardinality/coherence rows are exactly that — "how many active-
site residues, combined how" is still a question about the active site).
**Seed provenance does not fit either shape, because a fallback seed is not
a transformation of the active-site quantity at all — it is a silent
substitution of a categorically different quantity (graph-degree centrality)
answering a different question, with no active-site content whatsoever.**
There is no "spread" to report the way a KNOB row reports one, because the
two provenance states are not two settings of one dial — one of them isn't
measuring the thing this record is about.

**Why this matters beyond terminology**: `baselines.degree_centrality` — a
top-5-highest-degree quantity — is independently one of the three
proximity-floor baselines every scored observable is checked against
([[SEAM-0015]] states this circularity explicitly: on a fallback-seeded
target, `seed ⊆ top-degree` and `floor ∋ degree_centrality`, so the
observable and its own floor share a construction and the comparison stops
being independent). A KNOB row would invite "sweep it and report the
spread"; that framing would have been actively misleading here — sweeping
"real seed vs. fallback seed" does not characterize sensitivity to a
modeling choice, it characterizes whether the experiment was run at all.

**Status of this row**: `labels.assert_functional_provenance_allowed`
([[TASK-0231]], wired into `build_labels`) now raises unless a target's own
config explicitly opts into the fallback tier — provenance is enforced at
the code level, not merely documented here. This record exists so a future
reader classifying a new cross-cutting seed-like quantity checks *whether
the quantity is even the one being measured* before reaching for GAUGE/KNOB/
SIGNAL — the register's own failure mode this task ([[TASK-0232]]) diagnosed
was scope selection (measuring the right thing on the wrong axis), not
absence of measurement.

## Status

Mixed: the cardinality/coherence KNOB row is genuinely characterized with
real 3-target data (not a seed record awaiting a follow-up task, unlike
most of this registry's other entries) — a direct answer to the question
this record exists to close. The `t_max` interaction and the
chosen-convention's own signal quality are correctly deferred to
[[TASK-0119]] and [[TASK-0118]]'s own re-run respectively, not force-fit
into this record.

**Declared convention (policy, not a gauge-invariance claim):** per
[[TASK-0118]]'s Done section, the project adopts **the full active-site
residue array, incoherent statistical mixture**
(`propagators.ctqw`/`time_averaged_ctqw`'s `coherent=False`, TASK-0118) as
the one seed convention for every scored call site
(`run_challenge.py`, `ceiling.py`/`ceiling_search_batched.py`,
`select.py`'s FROZEN-loop consumers) — not because it is invariant (it is
not, per the KNOB row above), but because a single declared, physically
defensible convention is required regardless, per the panel review's own
framing, and this is the one with no unphysical relative-phase assumption
and no crash-workaround cardinality reduction.

## Provenance

Seeded and fully populated 2026-07-16 by [[TASK-0118]] (`REVIEW-panel-
2026-07-16-v2` §2.1, §5 P0-1), closing the gap `[[Q-0003]]` and
`EXECUTION_PLAN.md`'s prior note both flagged and left unresolved.

**Numbering note**: this record is `INV-0006`, not the `INV-XXXX` this
task's own filing left as a placeholder, because `INV-0005` was
independently claimed by two concurrent threads in the same working
session ([[TASK-0099]]'s `INV-0005-coherence-sensitivity.md`, committed
`e16fee2`; [[TASK-0109]]'s `INV-0005-propagator-time-parameters.md`,
committed `7defdd4`) — both already landed in git history under the same
numeric ID before this record was filed. Not renumbered here (that would
rewrite already-committed, already-linked history); flagged as a real gap
in this scaffold's tooling (`.ai/invariants/` has no `claim.py reserve-
next`-equivalent atomic ID allocator the way `.ai/tasks/` does) worth a
follow-up if it recurs.
