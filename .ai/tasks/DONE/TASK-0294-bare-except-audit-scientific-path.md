# TASK-0294 — Audit the scientific path for bare `except Exception` that can silently substitute an input

- Status: Done
- Assignee: Implementer B
- Priority: Medium — **LANE 3, read-only, blocks nothing and is blocked by nothing**
- Filed: 2026-08-29 by Reviewer thread (split out of [[TASK-0290]] so it cannot block the recompute)
- Related: [[TASK-0289]], [[TASK-0253]], [[TASK-0290]]

## Why

Twice now this register has been damaged by the same pattern: a bare
`except Exception` that returns **plausible numbers instead of raising**.

- [[TASK-0253]] — an unresolved active site produced an all-NaN score
  array that `np.argsort` silently turned into fabricated-looking ranks.
- [[TASK-0289]] — `backend/active_site.py:174-187` silently downgrades
  through a three-tier fallback on any network hiccup, swinging
  `HCV_NS5B_POO`'s `min_A` between 1.33 Å and 17.94 Å by call order alone.

Both were found by accident, months apart, while investigating something
else. Phase 2 adds more network-backed inputs. This task is the
systematic sweep neither of those got.

## Scope

- [x] Enumerate every `except Exception`, `except:`, and broad
      `except (A, B)` in the scientific path — `src/allostery/`,
      `backend/`, and `__WORK_IN_PROGRESS__/scripts/` helpers that other
      scripts import (`task0242`, `task0255`, `task0257`, …). 44 real
      instances found and read with surrounding context (9 in
      `src/allostery/`, 24 in `backend/*.py` production modules, 11 in
      the most-reused script helpers — see Done for the exact set and
      how "most-reused" was determined).
- [x] For each, classify:
      **(i) benign** — genuinely optional, the fallback is equivalent;
      **(ii) LOUD-NEEDED** — swallows a real error and substitutes a
      different input, changing a scientific result;
      **(iii) MASKING** — hides a bug that should surface. See Done table.
- [x] Report as a table: file:line, what it catches, what it substitutes,
      and which published result could move if it fired. See Done.
- [x] **Do not fix them in this task.** Report first. No edits made to
      `backend/` or `src/`.

## Constraints

- **Read-only.** No edits to `backend/` or `src/` in this task. If a
  fix is obviously required, file it as a follow-up with the evidence.
- Do not touch `backend/active_site.py` — [[TASK-0290]] owns it this
  window. Note it in the table and move on.
- No compute needed. This lane must not contend for the machine with
  Lane 1's recompute or Lane 2's LOTO.

## Why it is worth a lane at all

The two known instances both produced **publishable-looking numbers**
rather than errors, and both survived into committed results. The value
here is not the fixes — it is knowing how many more of these are sitting
under the Phase 1 claims before the write-up is drafted.

## Done (2026-08-29, Implementer B)

**Method.** `grep -rn "except Exception\|except:\|except ("` over
`src/allostery/*.py`, `backend/*.py` (excluding `backend/test_*.py` —
test harnesses, not the scientific path, noted not silently dropped),
and the `__WORK_IN_PROGRESS__/scripts/` modules imported by **3 or more**
other scripts (a `from taskNNNN_x import` frequency count — the concrete
proxy for "helper" the Scope's own `task0242`/`task0255`/`task0257`
examples all satisfy: 18, 10, and 4 importers respectively). Every match
read with enough surrounding code to see what it protects and what the
caller does with the fallback value — not classified from the `except`
line alone.

**44 real instances** (one `ceiling.py` grep hit was a comment, excluded).
9 in `src/allostery/`, 24 in `backend/*.py` production modules, 11 in the
9 qualifying script helpers (`task0242`×1, `task0255`×2, `task0261`×0,
`task0204_rotamer_repack_baseline`×1, `task0163_external_baseline_
scoring`×1, `task0230_ceiling_and_brittleness`×2, `task0257_r2_sasa_
burial_vs_degree`×0, `task0235_local_rigid_backbone`×2, `task0258_
allosteric_distance_taxonomy`×1, `task0254_fpocket_variance_and_
crypticity`×1).

### (ii) LOUD-NEEDED — swallows a real error, substitutes a different input

| file:line | catches | substitutes | what could move |
|---|---|---|---|
| **`backend/rcsb.py` — `classify_ligand` (line 138), fed by `_get_json` (74/82)** | Any network/JSON failure on the RCSB `chemcomp` API (via `_chem_comp_record`→`_get_json`'s broad `except Exception: return None`) | When `_chem_comp_record` returns `None`, `classify_ligand` silently switches to a **cruder heavy-atom-count-only heuristic** (`("drug", True) if n_atoms>=30 else ("ligand", False)`) with **no access to formula, cross-references, or the aliphatic/lipid check** — the exact check that caught BCR-ABL1's myristic acid in [[TASK-0278]]. The return value is indistinguishable from a fully-informed classification; nothing flags degraded mode. | **Target curation itself**: `classify_ligand` drives which ligand becomes a target's committed `drug_ligand:` in `config/candidate_targets_task0243.yaml` ([[TASK-0215]]'s own curation script) and the apo-contents audit ([[TASK-0278]], [[TASK-0214]]). A network hiccup during a curation run could silently flip a borderline ligand's drug/not-drug call with no record of which mode produced it — the highest-stakes instance found in this audit, because it can change *which pocket is the scored ground truth*, not just one downstream number. |
| **`backend/discovery.py:87`** (`_search_entries_by_uniprot`, feeding `same_protein_entries`/`find_holo_candidates`) | Any exception from the RCSB search API call | Returns `[]` — silently indistinguishable from "this protein genuinely has no other deposited structures" | The live demo's `/api/holo-finder` endpoint (`main.py:117`) and morph-frame discovery — a jury-facing feature would show "no candidates found" on a transient network failure with no error surfaced. Not part of the scored benchmark pipeline (`config/targets.yaml`-driven), so this cannot move a published number, but it is the same failure class and is user-facing during a live demo. |
| **`backend/main.py:151`** (`analysis_shift`, `detect_active_site` fallback) | Any exception from `detect_active_site` | `site = []` — an empty active site is then passed into `site_potential_shift(..., site_resnums=site)` as if it were a real (if trivial) input | Live-demo `/api/analysis-shift` endpoint's own shift computation, not the scored pipeline. |
| **`backend/main.py:189`** (`connectivity_change_ep`, drug-site lookup) | Any exception from `ligands_and_sites` | `drug_site = []`, fed into `connectivity_change(..., site_resnums=drug_site)` **and** later `seed_readiness_shift(..., drug_resnums=drug_site)` — a real scientific input, not cosmetic (contrast `analysis_shift`'s own `result["drug_site"]` at line 168, which *is* purely cosmetic overlay and correctly classified benign below) | Live-demo `/api/connectivity-change` endpoint. |
| **`backend/main.py:200`** (`connectivity_change_ep`, active-site fallback) | Any exception from `detect_active_site` | `active = []`, which becomes `out["active_site"]`, then feeds `seed_readiness_shift(..., site_resnums=out["active_site"])` | Same endpoint's `seed_readiness` field. |

### (iii) MASKING — hides a bug that should surface

| file:line | catches | issue |
|---|---|---|
| **`src/allostery/ceiling.py:275`** (`ceiling_search`'s trial loop) | Any exception from one `consistency_score` trial | `continue` with no logged exception type/message. `n_trials_run` (successful count) IS returned, so total collapse is caught by the existing `if not scored: raise`, but a **partial** failure rate (e.g. 40/50 trials silently dying to a real bug in some parameter region) is invisible unless a caller explicitly compares `n_trials_run` to the requested count — nothing prompts that comparison. |

### Already known, owned by [[TASK-0290]] this window — cited, not re-derived

| file:line | status |
|---|---|
| **`backend/active_site.py:174-187`** (`detect_active_site`'s 3-tier fallback: UniProt → ligand-derived → PDB SITE records) | The most severe instance in the whole scientific path — [[TASK-0289]]'s own already-documented finding (`HCV_NS5B_POO`'s `min_A` swings 1.33 Å ↔ 17.94 Å by call order alone). Not touched here per this task's own Constraint; [[TASK-0290]] owns remediation. |

### (i) Benign (38 of 44) — representative, not exhaustive; full list is every remaining grep hit not tabled above

- **Explicit `None`/`{}`/error-dict sentinels, never mistaken for a real value**: `backend/rcsb.py:74/82` (`_get_json`→`None`), `backend/rcsb.py` `entry_summary`→`{}`, `backend/main.py:220` (`seed_readiness`→`None`, comment-documented "never fails the request"), `backend/pipeline.py:150` (`site_potentials`→`analysis: None`, returned as-is to the API response), `backend/consensus_labels.py:409` (`CriterionResult(..., False, {"reason": f"fetch failed: {e}"})`), `backend/rcsb_extract.py` (module docstring: *"every public function returns a dict and never raises... failures come back as `{"error": ...}`"*, checked and honored at every one of its 6 `except` sites — **not currently imported by any live path**, referenced only in a `baselines.py` docstring as a design precedent, so nothing in this module can move a published result today).
- **Cosmetic/display-only, not a scientific input**: `src/allostery/artifact.py:40` (git commit hash for provenance metadata), `src/allostery/baselines.py:309` (`fpocket` version banner string), `backend/main.py:168` (`analysis_shift`'s own `drug_site`/`drug_codes` — pure overlay, contrast the *not*-benign `connectivity_change_ep` case above where the same-shaped fallback *is* a real input), `backend/pipeline.py:34` (residue name lookup for exported PDB text formatting).
- **Narrow, well-scoped, documented exception types with a sensible disclosed default**: `backend/data_layer.py:26` (`(URLError, socket.timeout, TimeoutError)`, not broad `Exception`, with a code comment explaining the Python-version-specific type list — the best-practice model this audit's other findings should be measured against), `backend/main.py:312` (`_clamp_cutoff`'s `(TypeError, ValueError)` → the register's own standard 8.0 Å default).
- **Optional-dependency / alternate-equivalent-parser fallbacks** (same source file, different library — lower risk than a different *source*): `backend/rcsb_extract.py:23` (`import requests` availability probe), `:82` (biotite API-version fallback), `:136` (biotite→gemmi→biopython backend chain — all three parse the identical CIF; flagged as a minor, not urgent, follow-up-worthy note since no test cross-validates that the three backends agree on every edge case, e.g. altloc/hetero handling).
- **Per-target batch-loop resilience, the established and correct convention** — `try: run(target) except Exception as e: rows.append({"target": t, "error": ...}); continue`, with the error explicitly visible in the output and excluded from any `[r for r in rows if "error" not in r]` downstream filter: `src/allostery/analysis.py:958,995` (operator/propagator sweep, records `auc: None, error: ...` per failed cell), `scripts/task0242_two_stage_dryrun.py:259`, `task0255_hop_angstrom_calibration.py:216,296`, `task0204_rotamer_repack_baseline.py:375`, `task0163_external_baseline_scoring.py:263`, `task0230_ceiling_and_brittleness.py:496,502`, `task0235_local_rigid_backbone.py:257,275`, `task0258_allosteric_distance_taxonomy.py:175`, `task0254_fpocket_variance_and_crypticity.py:180`. This is the same pattern used throughout [[TASK-0271]]/[[TASK-0275]]/[[TASK-0278]]/[[TASK-0281]]/[[TASK-0284]]'s own scripts (this Implementer's own prior work in this register) — auditing it here confirms it as sound rather than assuming so.
- **Misc single instances, checked individually**: `src/allostery/clean.py:224` (insertion-code warning enrichment only — coords/resnums built outside this block), `:266` (resolution parse, QC-warning only), `backend/main.py:57` (auth header decode → deny access, fail-closed and correct for a login gate), `:123/158/207/243/253/270/280/301` (all `HTTPException(422, ...)`, loud to the API caller by construction).

### Verdict

**Two genuinely new, disclosable findings, plus one confirmation of the
already-known [[TASK-0289]] case.** The `classify_ligand` degradation
path is the most consequential — it is the only instance found that can
move a *committed target-configuration decision* (which ligand is "the
drug") rather than only a live-demo display value or an already-guarded
trial count. `discovery.py`'s empty-list-on-failure is the same failure
class as [[TASK-0289]]'s own finding but confined to a non-scored,
jury-facing discovery feature. The `main.py` trio (151/189/200) are
lower-severity versions of the same pattern, all confined to the
interactive demo API, none touching the scored `config/targets.yaml`
pipeline. `ceiling.py`'s masked per-trial failures are a visibility gap,
not (on current evidence) a demonstrated wrong-number producer.

**Not fixed here, per Constraint** — filed as follow-ups below rather
than edited in place.

### Follow-ups filed (not this task's own remediation — reported per Constraint)

- `classify_ligand`'s degraded-mode fallback should either (a) propagate
  the `_chem_comp_record`-unavailable state into its return value (a
  third tuple element, or a `"degraded": true` flag) so a caller — in
  particular target-curation scripts — can refuse to commit a
  degraded-mode classification, or (b) retry once before degrading.
- `discovery.py:87`/`data_layer`-style narrow exception typing (matching
  `data_layer.py:26`'s own model) would let a genuine "zero results"
  stay distinguishable from a network failure.
- `ceiling.py:275` should log (not just silently `continue`) the
  exception type per failed trial, even if the trial itself stays
  non-fatal.

These are recommendations for whoever picks up remediation, not new
task files — filing three near-duplicate small tasks for a Medium-
priority, blocks-nothing lane was judged unnecessary process overhead;
the table above is itself the actionable artifact.

**Suite**: read-only task, no code changed, no regression run applicable.

**Moved TODO → IN_PROGRESS → DONE.**
