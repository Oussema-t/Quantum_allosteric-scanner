# Review targets — internal adversarial-review aim points, not part of the submission

**Not shipped.** This content used to be §8 ("Attack these first") of
`PHASE1_SUBMISSION_V1.md`. Moved out 2026-09-07 ([[TASK-0339]], source:
`.ai/reviews/2026-09-07/REVIEW-2026-09-07-adversarial-submission-audit.md` §3.5):
Guidelines §4.3 mandates seven numbered items and the document had eight, the
eighth being ~758 words of front-matter and this section addressed to an
internal reviewer, not a judging panel — the wrong document for it, not wrong
content. Kept here because it is useful for running the next review round, not
because it belongs in front of a panel.

Two of the seven items below (**01**, **06**) were, per this task's own
instruction, answered directly inside §1/§2 of the submission rather than left
as posed questions — the versions below are the original, unanswered framing,
kept for the record of what was asked, not superseded in place.

---

The seven places we think this document is weakest, with our current answers. An
adversarial review is more useful aimed than unaimed — if you break something not
on this list, that is more valuable still.

**01 — "What is actually quantum about this?"**
Our single weakest point. We propose a benchmark and a classical readout, and we
concede the formalism is classically simulable. Our defence is that §4.1 asks for
advantage *or insight* and we take the second disjunct explicitly. Press on
whether an ideation panel will accept that.
*(Answered in the submission, §1: "the insight, not the advantage," stated
directly rather than left implicit.)*

**02 — "Your one constructive result is a ceiling from a high-capacity model."**
It now clears both controls — the permuted-label null landed while this draft was
being written (0.4993, 0/100 reps, z = 8.69). What remains arguable is that a
gradient-boosted combination of features is an *upper bound*, on a single cohort,
and that we have not shown any deployable ranker achieving it. Press there.

**03 — "You flip-flopped on multimodality twice in three days."**
True. Both reversals were self-caught, and the second found that both available
tests are miscalibrated. Ask whether that reads as rigour or as instability — we
genuinely do not know how it lands on a referee.

**04 — "How much of this is independently reproduced?"**
Honestly: one result. An independent from-scratch harness reproduced the proximity
confound to four decimal places. Most of the rest is single-implementation.

**05 — "No multiplicity control across ~50 analyses."**
Conceded in Appendix C. No survivor below p = 0.019. Ask whether disclosing this
helps us or simply hands a referee the weapon.

**06 — "Is a certifying benchmark a Phase-2 deliverable, or a paper?"**
Unresolved at time of filing, and the most consequential strategic question here.
If the panel wants a quantum PoC, our proposal may be well-argued and off-brief.
*(Answered in the submission, §2: framed as "a benchmark-and-instrument proposal
that uses a quantum-inspired method as its first test subject, not a method
paper with a benchmark attached" — this is [[TASK-0339]]'s own synthesis of
material already in the document, not a new strategic decision from outside it.
**Flagged for human sign-off before freeze**: this is a genuine positioning
call the review itself called "the most consequential strategic question here,"
and it should get an actual answer from the team, not just an implementer's
synthesis, before the document is frozen.)*

**07 — "Heavy AI involvement — won't a panel discount this as machine-generated?"**
**Decided: we disclose fully and open the register.** The counter-argument is that
in a Quantum-and-AI challenge that permits AI use, hiding it would be incoherent —
and that what should be judged is whether the verification was real, which we have
made checkable. Challenge the decision if you disagree; it is deliberate, not an
oversight. The narrower version worth pressing: does opening the register help a
reviewer, or simply give them more places to find something we missed?

### What we specifically want from the next review round

- A ruling on **06** — a positioning call, not a technical one, that determines
  whether the rest of the document is the right document. **01** now has a
  stated answer in the submission itself (see above); **07** is decided; argue
  us out of either if you can.
- Whether Appendix C should ship. It is unusual to volunteer this, and we may be
  wrong that honesty outscores exposure.
- Anything in Appendix A you think we have graded too generously. The QUALIFIED
  rows are where we are least confident of our own calibration.
