# Draft message to the organisers — 2026-09-09

**Status: DRAFT, not sent.** For the repo owner to review, edit and send. Filed
under [[TASK-0351]]. Two prior exchanges are recorded in
`2026-08-26-organiser-clarifications.md`; both were answered within days.

Three items: one narrow re-ask, one still-open question, and two structure
findings offered as service rather than as complaint. Kept short deliberately —
they have answered promptly twice and a long message is a worse use of that.

---

Dear organisers,

Thank you again for the clarifications of 26 August and the follow-up on scope —
both were promptly answered and both changed what we built.

Three small things before submission.

**1. A narrower version of an earlier question.** Our question about Constraint 3
was answered for closed-form elastic-network modes, which we do use and which is
helpful. The part we are still unsure of is different: **is a conformational
search that minimises an energy function over side-chain rotamers — with no
molecular-dynamics trajectory at any stage, input or training — within scope?**
We ask because one component of our proposal depends on the answer, and we would
rather scope it correctly now than assume.

**2. Still open from our original list.** Where the challenge bibliography cites
two references that disagree on a structure or annotation, which governs? This is
minor and we have proceeded sensibly, but it affects reproducibility for anyone
re-running our work.

**3. Two structure findings, offered in case they are useful to other teams.**
Both are verified against the PDB, and we raise them only because other teams are
working from the same Table 1 and may not check:

- **`8S8C`**, kindly suggested in your reply as a KRAS G12C structure, **is
  holo** — it is bound to MK-1084. It is an excellent G12C structure, but it
  cannot serve as the apo half of an apo/holo comparison. We searched and used
  `4LDJ`, which we verified as genuine G12C (residue 12 is CYS) and ligand-free
  at the site.
- **`6C1H`**, listed for cardiac myosin, **contains no mavacamten.**

Neither affects our own submission — we have documented our structure choices and
their reasons — but a team taking either at face value would be building an
apo/holo contrast on a structure that cannot express one.

With thanks,
Team AuraQu

---

## Notes for the sender, not part of the message

- **Do not re-report that `4OBE` is wild-type.** That was our finding, delivered
  on 2026-08-26, and it is what prompted the `8S8C` suggestion. Raising it again
  would be claiming credit twice for one finding.
- Item 3 is deliberately framed as service and carries no implied criticism. They
  offered `8S8C` in good faith while answering our own defect report.
- If the answer to item 1 is that minimisation-based search is **out** of scope,
  §2 component (c) of the submission needs rewording before we ship — that is the
  only dependency, and it is a wording change rather than a re-run.
- Item 2 is genuinely minor. If dropping it makes the message likelier to be read
  and answered quickly, drop it.
