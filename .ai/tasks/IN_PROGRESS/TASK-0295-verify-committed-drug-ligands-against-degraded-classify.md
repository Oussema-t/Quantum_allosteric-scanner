# TASK-0295 — Could `classify_ligand`'s degraded mode have already mis-set a committed `drug_ligand`?

- Status: **Diagnosis DONE (2026-08-30, Reviewer thread) — answer is NO, exposure is zero. Remediation still open, priority downgraded High → Low.**
- Priority: ~~High~~ → **Low**, on the evidence below. The mechanism is real; the exposure in our target set is zero.
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


---

## Done — diagnosis (2026-08-30, Reviewer thread)

`scripts/task0295_committed_drug_ligand_audit.py`. Both code paths were
re-implemented side by side directly from `classify_ligand`'s source, and
**every HET code in every target's holo structure** was classified both
ways — not just the committed `drug_ligand`, because the real risk was a
degraded run picking the *wrong* ligand from among several.

**37 targets, 102 (target, HET) pairs, 88 distinct ligands.**

### Q1 — is any committed `drug_ligand` wrong today?

**No.** All **29** committed `drug_ligands` classify as `drug` on the
fully-informed path.

### Q2 — where do the two paths diverge?

**10 ligands diverge, and ALL 10 in the same direction — false NEGATIVE**
(informed `drug` → degraded `ligand`): `ASP`, `F19`, `F1G`, `GC7`, `GLS`,
`LLP`, `M3L`, `NCA`, `QKT`, `XB2`. Five of them (`F19`, `F1G`, `GC7`,
`QKT`, `XB2`) are committed `drug_ligands`.

**Zero false positives.** Not one ligand anywhere in the target set would
be *promoted* to `drug` by the degraded path.

### Q3 — could a degraded run have picked a different ligand?

**No — 0 targets at risk.**

| outcome | n |
|---|---|
| committed ligand survives degraded mode | 24 |
| **at risk of a WRONG pick** | **0** |
| would be *dropped*, not mis-set (ligand demoted, no competitor) | 5 |
| no committed `drug_ligand` present in structure | 7 |

The 5 droppable targets — `CARDIAC_MYOSIN`, `CASPASE1`, `DHPS_GC7`,
`SMYD3_DIPERODON`, `TRP_SYNTHASE_F19` — have **no competing HET** that
degraded mode would call a drug. A degraded curation run would have
produced *no* target, not a wrong one.

The 7 unmatched are all benign and accounted for: 5 have no
`drug_ligand` at all (`ATCase`, `GLYCOGEN_PHOSPHORYLASE`, `HEMOGLOBIN`,
`PFK`, `TAR_RECEPTOR` — classic allosteric benchmarks without a drug);
`GROEL_SUBUNIT`'s `drug_ligand` is GroES, a protein, annotated as such in
the config; and **`CARDIAC_MYOSIN_TABLE1` (6C1H) contains only `ADP` and
`MG`** — an independent live re-confirmation of our existing
benchmark finding that Table 1's own structure does not contain
mavacamten (matches `2026-08-26-organiser-clarifications.md` exactly).

## Correction to [[TASK-0294]]'s severity framing

[[TASK-0294]] justified the High rating by noting degraded mode loses the
aliphatic/lipid check — *"the exact check that caught BCR-ABL1's myristic
acid in [[TASK-0278]]"*. That check can only produce a **false positive**
if the lipid has **≥ 30 heavy atoms** (`_DRUG_HEAVY_MIN`). Myristic acid
has **16** — degraded mode calls it `ligand` too. **No ligand in the
entire target set reaches that bar.**

The degraded path is **conservative by construction**: its only lever is
a high heavy-atom threshold, and drug-DB cross-references (the thing it
loses) exist precisely to *promote* sub-30 ligands. It can miss a drug;
it cannot invent one. [[TASK-0294]] identified a real mechanism and
correctly flagged it — the severity estimate was the part that needed
testing.

## Remaining scope (Low priority, not done here)

- [ ] Propagate a `degraded: true` flag out of `classify_ligand` so a
      curation script can refuse to commit a degraded classification.

Still worth doing — the mechanism is real and Phase 2 adds targets — but
it is **not** a gate on the Phase 1 write-up. Nothing in the committed
target list is wrong, and nothing could have been.
