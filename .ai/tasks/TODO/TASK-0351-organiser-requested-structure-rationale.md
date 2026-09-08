# TASK-0351 — The organisers asked us to document our structure rationale. The draft does not.

- Status: TODO
- Owner: **Reviewer thread / whoever owns the next drafting pass**
- Priority: **High — a direct, explicit organiser instruction we are currently not meeting**
- Filed: 2026-09-08 by Reviewer thread (id via `claim.py reserve-next`)
- Source: `documentation/2026-08-26-organiser-clarifications.md`
- Related: [[TASK-0221]], [[TASK-0332]], [[TASK-0270]]

## What the organisers actually said

Verbatim, from their reply:

> 2. A nice structure for KRAS G12C would be **8S8C**.
> 3. Cardiac Myosin — Your 8QYP–8QYR substitution is **accepted as primary**.
> 4. BCR-ABL1 — you may substitute `1OPL` with an alternative apo structure that
>    fits your pipeline. **Please document the rationale in your submission.**

And our own clarifications file adds the standing warning:

> Any submission claim that depends on a substitution **must cite this
> clarification explicitly**, because a reader holding only the public Challenge
> Statement will otherwise see an unexplained deviation from a mandated
> structure pair.

## The gap, checked against the current draft

`PHASE1_SUBMISSION_V2.md` names `4LDJ`, `1OPL` and `1NKP` and **cites the
clarification nowhere, and gives no rationale for any structure choice.**

Three specific exposures:

| structure | situation | what the draft says |
|---|---|---|
| **KRAS `4LDJ`** | organisers suggested **8S8C**; we use 4LDJ ([[TASK-0270]]: 4OBE is wild-type, not G12C) | nothing |
| **BCR-ABL1 `1OPL`** | substitution explicitly permitted, **rationale explicitly requested**; we kept 1OPL — the one carrying myristate at the scored site | reports the myristate finding, but never says why we kept the structure |
| **Cardiac myosin 8QYP→8QYR** | accepted as primary | substitution not mentioned at all |

**A reader holding only the public Challenge Statement sees three unexplained
deviations from mandated structures** — exactly what our own file warned about a
fortnight ago.

The 1OPL case is the sharpest: we build a whole finding on that structure being
ligand-occupied, while the organisers had already offered us the option to swap
it. Not saying so invites the obvious question of whether we knew.

## Intent Contract

- Outcome: a short passage — a table plus two sentences is enough — stating each
  structure used, whether it deviates from Table 1, and the reason, **citing the
  2026-08-26 clarification explicitly** as the authority for the accepted
  substitutions.
- For BCR-ABL1, answer the question they actually asked: **why we kept `1OPL`
  rather than substituting.** The honest answer is that the myristate occupancy
  is a finding rather than a defect for our purposes — it is what let us measure
  that "apo" depositions are not ligand-free. Say that.
- For KRAS, state why `4LDJ` and not the suggested `8S8C`. If there is no strong
  reason, **consider simply running 8S8C** — it is the organisers' own
  suggestion and declining it silently is the weakest of the three positions.
- Constraints:
  - Quote the clarification, do not paraphrase it.
  - This is a compliance passage, not an argument — keep it short; the appendix
    now works ([[TASK-0349]]) and this may belong there rather than in the 6.
- Planned Validation: after drafting, re-read the clarifications file end to end
  and confirm no other organiser request is unmet.

## Also still open with the organisers, and worth one message

Three of our own questions remain **UNANSWERED** and one gates a task:

- **(d)** which reference governs when the bibliography contradicts itself
- **(e)** does Constraint 3 exclude minimisation / Monte-Carlo sampling?
- **(f)** does Constraint 3 exclude an MD-*trained* tool with MD-free inference?
  — **gates [[TASK-0269]]**

Separately, two verified defects in the challenge's own Table 1 were found on
the `allosteric` branch — `6C1H` contains no mavacamten, and `4OBE` is wild-type
KRAS rather than G12C — both checked against RCSB. **These should go to the
organisers regardless of which submission ships**, and they pair naturally with
re-asking (d)–(f) in one message. The channel is live and has answered within
days twice.
