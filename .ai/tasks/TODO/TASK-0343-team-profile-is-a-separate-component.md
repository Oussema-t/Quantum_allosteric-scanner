# TASK-0343 — §4.1 Team Profile is a separate deliverable; §7 Team Capability is not a biography section

- Status: TODO
- Owner: **Implementer** (drafting) → repo owner sign-off
- Priority: High — structural compliance, and it recovers body pages
- Filed: 2026-09-07 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0332]], [[TASK-0339]], [[TASK-0344]]

## What the Guidelines actually require — both things exist

Read from `documentation/2026-04-06-Phase-1-Submission-Guidelines-VF.md`, §4:

**§4.1 Team Profile** — *a separate submission component*, not part of the
concept proposal:
> • Team name and lead contact details.
> • Brief description of each team member (name, role, affiliation, relevant expertise).
> • Indication of any prior experience with quantum computing, quantum-inspired
>   methods, or the specific problem domain.

**§4.3 item 7 Team Capability** — *is* one of the seven concept-proposal items:
> 7. Team Capability: Why your team is well-positioned to execute this proposal.

**Precision matters here.** The human review said the about-me material is *"not
in the Concept Proposal"* — right about the biographies, but item 7 does legitimately
belong there. The two are different questions:

- §4.1 asks **who these people are** — name, role, affiliation, expertise, prior
  quantum experience. Reference material. Its own page budget, outside the 6.
- §7 asks **why this team can execute this proposal** — a short argument tied to
  *this* work. Repo owner's framing: *"brief, and mention who does what in this
  project."*

## Current state

The full biographies — Oussema's degree/thesis/hackathon record, Berke's PhD,
TREK-2 work, publication status and software stack — are inside §7 of the concept
proposal. [[TASK-0339]] cut §7 from 709 to 522 words but did not question whether
the content belonged there at all. That was the right call for its scope; this
task is the structural question it left alone.

## Intent Contract

- Outcome: a separate **Team Profile** document carrying §4.1's three bullets in
  full — including team name and lead contact details, which the concept proposal
  should not be carrying — and §7 rewritten as a short capability argument.
- §7's target: **~150–200 words**, three or four sentences naming who does what on
  *this* project and the one credential each that makes it credible. Berke's label
  is *"Computational biophysics / structural chemistry"*, role *"target selection
  and mechanistic classification, structural validity auditing, ensemble and
  free-energy methodology, biological interpretation"* — that sentence is close to
  the right register for all three.
- Berke's *"why classical detection fails"* paragraph does **not** go to the Team
  Profile — [[TASK-0332]] already routes it to §1, which is where it earns its
  space. Confirm it landed there and is not duplicated in both.
- Constraints:
  - Verify against §4.1 directly before writing; do not work from this summary.
  - **Lead contact details are required and are currently nowhere in the
    submission set.** Do not invent them — flag for the repo owner.
  - Keep the AI-workflow disclosure decision intact ([[TASK-0184]] §8 item 07); it
    is a deliberate choice. It is also *evidence about how the team works*, which
    makes it §4.1 or §7 material depending on length — put the short version in §7
    and any elaboration in the Team Profile.
- Planned Validation: re-run `submission_build.py` and report the body page delta.
  Moving the bios out is the single largest structural saving available in the body.

## Note

This is worth doing even setting the page limit aside. A panel scoring §4.3 item 7
is asking whether the team can execute; three paragraphs of biography answers a
question they asked somewhere else, and it reads as padding in the section that
carries the **smallest weight (10%)** while §3 — 20% — is currently the thinnest
in the document.
