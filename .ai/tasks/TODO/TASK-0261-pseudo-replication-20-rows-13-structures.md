# TASK-0261 — 20 rows, 13 structures: every p-value in the frozen-set analyses is over-counted

- Status: TODO
- Assignee: unassigned (suggest Implementer — mechanical but touches every headline number)
- Priority: **High — it affects TASK-0249, TASK-0254, TASK-0257, TASK-0259 and the collaborator brief**
- Filed: 2026-08-25 by Reviewer
- Related: [[TASK-0243]] (the frozen set), [[TASK-0249]], [[TASK-0254]], [[TASK-0257]], [[TASK-0259]], `documentation/CTQW_CONTRIBUTION_BRIEF.html`

## The defect

[[TASK-0243]]'s frozen set has **20 scoreable rows but only 13 distinct apo
structures**. Seven rows are a second ligand bound to an apo structure already
counted:

| apo PDB | rows |
|---|---|
| 7SBN | GAC_BPTES, GAC_CPD12 |
| 2PBK | KSHV_PROTEASE_24Q, KSHV_PROTEASE_25G |
| 2GIQ | HCV_NS5B_VRX, HCV_NS5B_VR1 |
| 2HAI | HCV_NS5B_POO, HCV_NS5B_CMF |
| 5LDZ | FBPASE_94D, FBPASE_95S |
| 1K7X | TRP_SYNTHASE_F6F, TRP_SYNTHASE_F19 |
| 7FS3 | PKR_MITAPIVAT, PKR_AG946 |

**Every apo-side score is identical within a pair** — geometry, CTQW, ENM
validity, hop distances, fpocket cavities all derive from the same apo
coordinates. Only the pocket label differs. These are not independent
observations for any apo-side statistic, yet every Wilcoxon and Mann-Whitney
test in the frozen-set analyses treats them as n=20.

Note this is *not* a curation error — two ligands on one target is legitimate
and informative. The error is purely in the **statistics**, which never
accounted for the clustering.

## First-pass measurement (Reviewer, 2026-08-25)

Re-run by averaging within each apo structure, n=13:

| statistic | n=20 (rows) | n=13 (structures) |
|---|---|---|
| CTQW added-last | −0.06%, p=0.5016 | +0.01%, p=0.7354 |
| geometry Shapley | +41.8%, p=0.0001 | +40.9%, p=0.0002 |
| fpocket Shapley | +8.0%, p=0.0032 | +8.0%, **p=0.0266** |
| CTQW Shapley | +11.2%, p=0.0333 | +14.3%, p=0.0327 |
| rho(apo-open, unexplained) | −0.771, p=0.0001 | −0.646, **p=0.0170** |

**No conclusion is overturned.** The headline null (CTQW adds nothing) is a
null either way — pseudo-replication cannot manufacture a null. But note the
direction: **the corrections cut against our own positive claims**, not
against CTQW. fpocket's significance and the crypticity correlation both
weaken materially while surviving.

## Scope

- [ ] Do it properly rather than by averaging. Averaging within a cluster is a
      first pass, not the right method — use a cluster-robust test or a mixed
      model with apo structure as a random effect, and say which and why.
- [ ] Re-run every frozen-set statistic that reports a p-value:
      [[TASK-0249]]'s composite-vs-CTQW (currently p=0.0137, n=20),
      [[TASK-0254]]'s added-last values for all three blocks,
      [[TASK-0257]]'s R2 paired comparison, [[TASK-0259]]'s subgroup tests.
- [ ] Decide and document a standing rule for the register: does a second
      ligand on the same apo structure count as a new target? Our view is that
      it does for label-side questions and does not for apo-side ones — but
      the rule must be written down once and applied everywhere, not decided
      per analysis.
- [ ] Check whether the same clustering exists in [[TASK-0216]]'s candidate
      set and the 15 register targets (CARDIAC_MYOSIN / CARDIAC_MYOSIN_TABLE1
      are a probable case).
- [ ] Update `documentation/CTQW_CONTRIBUTION_BRIEF.html` with the corrected
      values, and add the clustering to its §09 "places your reproduction will
      diverge" list — a reproducing thread will hit exactly this.

## Acceptance

- [ ] Every frozen-set p-value restated under the chosen clustering method,
      old and new side by side.
- [ ] A written rule for what counts as an independent target.
- [ ] Brief updated; §09 gains the clustering item.
- [ ] An explicit statement of which conclusions changed. Current expectation:
      none, but two weaken.

## Constraint

Report this **before** the collaborating thread finds it. It is a real defect
in our statistics, we found it ourselves, and it corrects in their favour on
two of our claims. Volunteering it costs us little and is worth a great deal
to the credibility of everything else in the brief.
