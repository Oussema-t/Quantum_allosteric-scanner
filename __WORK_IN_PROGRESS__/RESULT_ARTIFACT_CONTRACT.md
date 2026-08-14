# Result Artifact Contract v1 (TASK-0083)

The seam between `allostery/` (research) and `backend/` (delivery):
`allostery/`'s pipeline writes one artifact per target; `backend/` reads it.
**No code import in either direction across this boundary** — `backend/`
never imports `allostery`, and this contract is the only thing that
crosses, as two on-disk files.

## Why now, and why this shape

Per `EXECUTION_PLAN.md`'s Architectural premise: "the research package emits
versioned result artifacts; the backend serves artifacts, it never
recomputes science in the request path." This corrects/extends
[[TASK-0018]]'s "port, don't cross-import" verdict — `backend/` still
imports nothing from `allostery/`, but now reads a documented file format
instead of having no relationship to the research results at all.

Every field below already exists as a real, tested function's output
(`allostery.analysis.assemble_verdict_results`, `allostery.report.
assemble_hit_list`, `allostery.pathways.edge_propensity_to_matrix`,
`allostery.superpose.cumulative_overlap_gate`, `allostery.diagnostics.
classify_failure`, and `COMPETENCE_MAP.md`'s floor/ceiling/actual/headroom
convention). This contract is a **shape decision over already-real data**,
not new science — nothing here is computed by this task ([[TASK-0079]] and
[[TASK-0082]] already compute it; this task only defines what gets written).

## File layout

```
results/<TARGET_NAME>/
  artifact_v1.json      # everything except the dense matrix
  connectivity_v1.npz   # the N x N connectivity matrix, one array: "M"
```

`v1` is in both filenames, not just a field inside them — a future
incompatible schema change writes `artifact_v2.json`/`connectivity_v2.npz`
alongside (or instead of) v1, so an old reader never silently misparses a
new shape and a new reader can detect "this target has no v2 yet" by a
plain file-existence check, no version-field parsing required before it
even knows which parser to use.

## Format split: JSON vs NPZ, and why

- **NPZ** for the connectivity matrix only. It is the one genuinely dense,
  large (`N x N`, `N` up to ~950 residues) numeric payload — NPZ (numpy's
  own binary format) is compact and loads with `numpy.load`, no JSON
  float-array parsing overhead, and no int/float precision-string
  round-trip risk for ~900,000 cells at `N=950`.
- **JSON** for everything else: scalars, short lists (hit list is `k<=20`
  residues), small grids (`cumulative_overlap_gate`'s grid is 12-24
  combinations), and metadata. Human-readable, diffable, and small enough
  that JSON's overhead doesn't matter — `backend/` and any human debugging
  a bad run can `cat` it.

## `artifact_v1.json` schema

```jsonc
{
  "schema_version": "1.0",
  "target": "KRAS_G12C",
  "generated_at": "2026-08-14T12:00:00Z",   // ISO 8601 UTC

  "provenance": {
    "pipeline_mode": "frozen",              // "frozen" | "dev" | "ceiling"
    "frozen_verified": true,                // see "Provenance" section below
    "git_commit": "a1b2c3d...",             // best-effort, null if unavailable
    "config_hash": "sha256:...",            // hash of the resolved target config
                                             // used to compute this artifact
    "content_hash": "sha256:..."            // self-integrity hash, see below
  },

  // Verbatim `allostery.report.verdict_template`'s expected flat keys --
  // not renamed, not restructured. A key absent here means that upstream
  // analysis was not available for this target (verdict_template's own
  // "missing key renders N/A" convention), not a schema violation.
  "verdict": {
    "AUC_apo_Hnew_default": 0.xxx,
    "AUC_apo_H10_baseline": 0.xxx,
    "AUC_apo_Hnew_optimised": 0.xxx,
    "AUC_holo_Hnew_optimised": 0.xxx,
    "AUC_ctqw_mean": 0.xxx,
    "AUC_heat_mean": 0.xxx,
    "most_impactful_term": "V_xxx",
    "least_impactful_term": "V_xxx",
    "mean_rho_apo_holo": 0.xxx,
    "mean_jacc20": 0.xxx,
    "coherence_auc_range": 0.xxx,
    "coherence_auc_at_gamma0": 0.xxx,
    "coherence_classification": "..."
  },

  // allostery.diagnostics.classify_failure's own closed-set category,
  // plus its return_ci=True annotation when available. category is one
  // of NO_SIGNAL_IN_APO / LABEL_SUSPECT / OPERATOR_DEGENERATE /
  // INSUFFICIENT_RESOLUTION / BEATS_CHANCE_NOT_FLOOR / NO_FAILURE_DETECTED.
  "diagnosis": {
    "category": "NO_FAILURE_DETECTED",
    "score_ci": [0.xxx, 0.xxx, 0.xxx],      // [auc, lower, upper] or null
    "floor_ci": [0.xxx, 0.xxx, 0.xxx],      // or null
    "ci_overlap": false                     // or null
  },

  // allostery.report.assemble_hit_list's own return shape, verbatim.
  "hit_list": {
    "indices": [12, 45, 88, 3, 190],        // local array indices
    "resnums": [13, 46, 89, 4, 191],        // PDB residue numbers, or null
    "scores": [0.91, 0.87, 0.85, 0.80, 0.77]
  },

  // Either of two existing, related but distinct gate mechanisms this
  // codebase already has -- checked directly, not assumed to be one
  // thing: `superpose.cumulative_overlap_gate` (backbone-mode overlap
  // stability, GO/NO_GO/UNSTABLE, knobs are cutoff/n_modes/reference) or
  // `sites.site_knob_sweep` (top-5 site-clustering stability,
  // STABLE/UNSTABLE, knobs are method/m_frac/linkage_cutoff/
  // min_cluster_size) -- `run_challenge.py`'s own real end-to-end path
  // calls the latter, not the former. "source" names which one produced
  // this block so a consumer doesn't have to guess the vocabulary from
  // the verdict string alone; every other field is that function's own
  // return dict, verbatim, un-renamed (field names therefore differ
  // between the two "source" values -- documented here, not normalized
  // into one artificial shape neither function actually returns).
  "stability_gate": {
    "source": "site_knob_sweep",            // "cumulative_overlap_gate" | "site_knob_sweep"
    "verdict": "UNSTABLE",                  // gate-specific vocabulary, see above
    "n_combos": 42,
    "grid": [ /* gate-specific per-combination records */ ]
    // remaining fields are that gate's own return dict, unchanged
  },

  // COMPETENCE_MAP.md's own floor/ceiling/actual/headroom convention,
  // verbatim formula: headroom = (actual - floor) / (ceiling - floor).
  // "headroom" is a float, OR the literal string "undefined" with
  // "headroom_reason" set -- reusing this project's own established
  // handling of the ceiling<=floor degenerate case (KRAS_G12C's own
  // historical instance, TASK-0082's Done section) rather than emitting
  // a nonsensical or sign-flipped fraction.
  "competence": {
    "floor": 0.xxx,
    "ceiling": 0.xxx,
    "actual": 0.xxx,
    "headroom": 0.xxx,
    "headroom_reason": null                 // e.g. "ceiling <= floor" when headroom is "undefined"
  },

  // General provenance metadata beyond the "provenance" block above.
  "metadata": {
    "apo_pdb": "4OBE",
    "holo_pdb": "6OIM",
    "n_residues": 169
  },

  // Present only when this target has no ground-truth pocket label
  // (allostery.report.no_ground_truth_report's own case, e.g. MYC_MAX) --
  // absent entirely for every target that has a real verdict/hit_list
  // above, not set to null alongside them.
  "no_ground_truth": null
}
```

## `connectivity_v1.npz` schema

One array, key `"M"`: `(n, n)` `float64`, symmetric, zero diagonal,
`0.0` for absent edges (not `NaN`) — exactly
`pathways.edge_propensity_to_matrix`'s own return contract, unchanged.
`n` matches `artifact_v1.json`'s own `metadata.n_residues`.

## Provenance: two hashes, two different questions

**`content_hash`** — self-integrity. SHA256 over a canonical
(sorted-keys, no whitespace) JSON serialization of every field in
`artifact_v1.json` *except* `provenance.content_hash` itself, computed at
write time and re-verified at read time. Answers: *"has this file been
hand-edited since it was written?"* A single flipped digit in any AUC, hit
list, or verdict field changes this hash — this is the mechanism behind
this task's own Acceptance Scenario ("given a stale or hand-edited
artifact... a mismatch is detectable").

**`config_hash`** — pipeline-state provenance. SHA256 over a canonical
serialization of `{target config resolved from targets.yaml, git commit
at write time}`. Answers: *"which pipeline/config state produced this
number?"* A consumer holding a live checkout can recompute the current
config's hash and compare against a stored artifact's `config_hash` to
detect drift (the artifact predates a `targets.yaml` edit, an apo/holo
swap, a cutoff change) — the exact "not a stale... run" half of this
task's own Acceptance Scenario, distinct from hand-editing.

**Why not reuse `protocol.stamp_provenance`/`verify_frozen_stamp`
directly**: checked directly before designing this, not assumed reusable.
That mechanism issues a random token into an in-process, in-memory Python
`set` (`protocol._issued_frozen_stamps`) and verifies membership in that
same set — it has no meaning once the process exits, and specifically
**cannot be verified after the artifact is serialized to disk and read
back by a different process** (`backend/`, in a later run, is definitionally
a different process than whatever wrote the artifact). `frozen_verified`
above is still populated *at write time*, from a real `verify_frozen_
stamp` check inside the writer's own process — it records "was this
value produced inside a verified frozen context when written," which is
real and worth keeping — but it is not, and cannot be, what a `backend/`
reader independently re-verifies later. `content_hash`/`config_hash` are
the mechanisms that survive serialization, and are new to this task, not
a repackaging of the existing stamp.

## Reference implementation

- **Writer**: `allostery.artifact.write_result_artifact(...)` — assembles
  the JSON+NPZ pair from already-computed pieces (verdict dict, hit list,
  connectivity matrix, gate result, competence numbers), does not
  recompute any of them. Computes both hashes.
- **Reader**: `backend/artifact_reader.py` — a stub, not the full
  [[TASK-0084]] API surface. Parses `artifact_v1.json` + `connectivity_
  v1.npz`, verifies `content_hash`, returns a plain dict. Zero imports
  from `allostery` (asserted by a test that inspects the module's own
  `import` statements, not just eyeballed).

## Out of scope (per this task's own Intent Contract)

- The actual `backend/` results API endpoints ([[TASK-0084]]).
- The execution/trigger path that produces artifacts on a schedule or on
  demand ([[TASK-0086]]).
- Any new science/computation — every field's value comes from an
  already-existing, already-tested function.
