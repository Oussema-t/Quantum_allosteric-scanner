# TASK-0386 — Name the mechanistic defect: orthosteric exclusion never fires on our own inputs

- Status: TODO
- Owner: Implementer (verification done); Team Lead to decide fix-vs-name
- Priority: High — this is the *cause* of [[TASK-0385]], and naming it is worth more than fixing it silently
- Filed: 2026-09-13 by Reviewer thread
- Source: [[REVIEW-2026-09-13-adversarial-submission-package]] §B6
- Related: [[TASK-0385]], [[TASK-0278]]

## Verified against `config/targets.yaml` and the cached structures

| target | `func_ligand` | what the apo input actually carries | exclusion fires? |
|---|---|---|---|
| BCR_ABL1 | `["NIL"]` (nilotinib, from **holo** 5MO4) | 1OPL: **MYR + P16** | **no** |
| CARDIAC_MYOSIN | `["ADP","ATP"]` | 8QYP: **ADP + VO4 + Mg + M3L** | partially — **VO4 not listed** |
| KRAS_G12C | `["GDP"]` | 4LDJ: GDP + Mg | yes |

`func_ligand` exists precisely to exclude the orthosteric region from the
allosteric label. On BCR-ABL1 the listed code is a ligand **from the holo
structure that is not present in the apo input**, so the machinery never fires
and the walk is free to nominate the ATP site — which is exactly what it did
([[TASK-0385]]: residue 338 is the gatekeeper, 4.2 Å from P16).

Same shape on cardiac myosin: VO4 is part of the ADP·VO₄ transition-state mimic
and is not in the list.

## The decision

Whether or not the code is fixed before the deadline, **naming this is worth
more than fixing it silently**: it is a concrete, mechanistic defect in our own
instrument, found by our own audit standard, in a proposal whose entire thesis is
that instruments in this field are not audited. Fixing it quietly and shipping a
new top-5 would also invalidate every number already in the package with ~36
hours left.

**Reviewer's recommendation: name it, do not fix it before the deadline.**
Re-running changes the hit lists, the matrices, the AUCs and the reports, and
there is no time to re-audit the result. File the fix as Phase-2 work.

## Done when

- One sentence in the Concept Proposal or `Solution_Outputs.pdf` names the defect.
- A follow-up task exists for the actual code fix, explicitly scoped post-deadline.
- `targets.yaml` gains a comment at both entries recording the finding, so the
  next person does not rediscover it.
