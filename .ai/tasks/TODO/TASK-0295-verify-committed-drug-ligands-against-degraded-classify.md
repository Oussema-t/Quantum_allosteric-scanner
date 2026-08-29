# TASK-0295 — Could `classify_ligand`'s degraded mode have already mis-set a committed `drug_ligand`?

- Status: TODO
- Priority: **High — this is the one [[TASK-0294]] finding that can change which pocket is scored ground truth**
- Filed: 2026-08-29 by Reviewer thread (promoting [[TASK-0294]]'s own highest-stakes follow-up out of a DONE file)
- Related: [[TASK-0294]], [[TASK-0290]], [[TASK-0289]], [[TASK-0215]], [[TASK-0278]], [[TASK-0214]]

## Why this is a task and not a bullet

[[TASK-0294]] recorded three remediation recommendations as bullets in its
own Done section, judging separate task files to be process overhead.
That judgement is right for two of them and **wrong for this one**, for a
reason the audit itself states: `classify_ligand` is *"the highest-stakes
instance found in this audit, because it can change which pocket is the
scored ground truth, not just one downstream number."*

A recommendation inside a DONE file is not a work queue. Everything else
in this window was promoted to a task; this should be too.

## The defect ([[TASK-0294]]'s finding, not re-derived)

`backend/rcsb.py` — `classify_ligand` (line 138) is fed by
`_chem_comp_record` → `_get_json` (lines 74/82), whose bare
`except Exception: return None` swallows any RCSB `chemcomp` network or
JSON failure. On `None`, `classify_ligand` silently switches to a **crude
heavy-atom-count-only heuristic** (`("drug", True) if n_atoms >= 30 else
("ligand", False)`) with no access to formula, cross-references, or the
aliphatic/lipid check — **the exact check that caught BCR-ABL1's myristic
acid in [[TASK-0278]]**. The return value is indistinguishable from a
fully-informed classification. Nothing flags degraded mode.

`classify_ligand` drives which ligand becomes a target's committed
`drug_ligand:` in `config/candidate_targets_task0243.yaml`
([[TASK-0215]]'s curation script) and the apo-contents audit
([[TASK-0278]], [[TASK-0214]]).

## The question this task answers

**Did that already happen?** The curation runs are historical; a network
hiccup during one would have left no trace.

## Scope

- [ ] Re-run `classify_ligand` on **every** committed `drug_ligand` in
      `config/candidate_targets_task0243.yaml` and `config/targets.yaml`,
      with the network verified up, and **diff against the committed
      choice**. Any disagreement is a target whose ground truth may be
      wrong.
- [ ] Specifically flag ligands where the informed and degraded paths
      *disagree* — i.e. `n_atoms >= 30` but the full record says
      not-a-drug (or the reverse). Those are the only ones a degraded run
      could have flipped. Report that set explicitly even if the
      committed choice happens to match.
- [ ] Confirm whether `_get_json` was ever reached in degraded mode
      during curation — check for any cached/logged evidence; if none
      exists, say so rather than inferring safety.
- [ ] Then (and only then) implement [[TASK-0294]]'s recommendation:
      propagate a `degraded: true` flag out of `classify_ligand` so a
      curation script can **refuse** to commit a degraded classification.

## Constraints

- **Diagnosis before remediation.** Do not change `classify_ligand`'s
  return shape until the audit of committed values is done — the current
  behaviour is what produced the committed config, and changing it first
  makes the historical question harder to answer.
- Follows [[TASK-0290]]'s pattern: fixing the *named* block may be
  insufficient. The real swallow is in `_get_json` underneath.

## Note

[[TASK-0290]] found the analogous risk was **real but had not corrupted**
the committed taxonomy (0/33 moved). That is the likeliest outcome here
too — and it is worth 30 minutes to be able to say so with evidence
rather than hope, before the Phase 1 write-up rests on these targets.
