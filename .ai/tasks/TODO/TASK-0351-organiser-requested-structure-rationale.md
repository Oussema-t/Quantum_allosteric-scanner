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
| **KRAS `4LDJ`** | we reported `4OBE` is wild-type; they answered *use 8S8C*; **we RCSB-verified 8S8C live and it is HOLO (MK-1084-bound)** — unusable as apo, so `4LDJ` was found and used ([[TASK-0270]]) | nothing |
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
- For KRAS, state the **verified chain**, which is a strength rather than a
  deviation to excuse: we reported that `4OBE` is wild-type at residue 12
  ([[TASK-0155]], [[TASK-0192]]); the organisers answered *"a nice structure for
  KRAS G12C would be 8S8C"*; **we checked 8S8C against RCSB and it is holo,
  bound to MK-1084**, so it cannot serve as the apo half of an apo/holo contrast;
  we therefore searched and used `4LDJ`, verified as real G12C and genuinely apo
  (`config/targets.yaml`). Every step is recorded and re-checkable. **This is the
  strongest of the three structure passages, not the weakest** — do not write it
  apologetically.
- Constraints:
  - Quote the clarification, do not paraphrase it.
  - This is a compliance passage, not an argument — keep it short; the appendix
    now works ([[TASK-0349]]) and this may belong there rather than in the 6.
- Planned Validation: after drafting, re-read the clarifications file end to end
  and confirm no other organiser request is unmet.

## Updated 2026-09-08 — (e) and (f) are now answered

Recorded verbatim in `documentation/2026-08-26-organiser-clarifications.md`.

**(f) — answered cleanly, in our favour.** *"PocketMiner requires only a static
PDB structure at inference and does not take MD trajectories as an input, so it
does not violate this rule."* The MD-trained / MD-free-inference distinction is
accepted and the operative test is what the tool consumes **at inference**.

- **[[TASK-0269]] is unblocked** — it was gated on exactly this.
- It retrospectively validates that task's own constraint-3 call (*"legal under
  the literal reading… the closest call of the four"*), which was escalated
  rather than self-authorised. Worth noting: the register flagged it instead of
  assuming, and the flag turned out to be the right instinct.
- It legitimises the cryptic-opening veto stage of the pipeline.
- **The submission may now say so**, which removes a disclosed risk from
  Appendix C rather than leaving it open.

**(e) — answered for ENM, but not for what we asked.** We asked whether
*minimisation-based or Monte-Carlo conformational sampling* is excluded. The reply
confirms **closed-form ANM/GNM modes are allowed**, which is welcome and which we
already relied on — but it does not address minimisation or Monte-Carlo directly.

**Do not read this as blanket permission**, because a live proposal component
depends on it: §2 component (c), the screening criterion for the hard regime,
treats side-chain packing as a search/minimisation problem, and the coupled-search
numbers (20% of KRAS_G12C restarts, 0 of 65 for PTP1B) come from exactly that. If
minimisation-based conformational search is out of scope, (c) needs rewording or
removal.

**Action: ask the narrow question again, once, in the same message as the items
below.** Phrase it so it cannot be answered about ENM again — e.g. *"is a
conformational search that minimises an energy function over side-chain rotamers,
with no MD trajectory at any stage, within scope?"*

## Still to send, and it should be one message

- **(e) narrowed**, phrased so it cannot be answered about ENM again.
- **(d)** which reference governs when the bibliography contradicts itself — still
  unanswered.
- **`8S8C` is holo.** Their suggested KRAS replacement is MK-1084-bound
  (RCSB-verified live, [[TASK-0270]]). They offered it in good faith answering our
  own defect report, and **other teams may take the suggestion at face value** and
  use a drug-bound structure as an apo input. This is worth telling them plainly
  and without triumph — it is the same class of service as the Table 1 defects
  below.
- **`6C1H` contains no mavacamten** — found on the `allosteric` branch, checked
  against RCSB.

**Attribution correction, so we do not over-claim in either direction**: the
`4OBE`-is-wild-type finding is **ours and already delivered** — [[TASK-0155]]
found it, [[TASK-0192]] flagged it, and it was reported to the organisers on
2026-08-26, which is what prompted the `8S8C` suggestion. It is not a new
contribution to announce, and an earlier version of this task described it as one
in error. The genuinely new items for the organisers are **`6C1H`** and
**`8S8C`-is-holo**.

The channel is live and has answered within days on both previous occasions.
