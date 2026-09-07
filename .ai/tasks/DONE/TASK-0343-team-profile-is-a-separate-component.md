# TASK-0343 — §4.1 Team Profile is a separate deliverable; §7 Team Capability is not a biography section

- Status: Done
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

## Done (2026-09-07, Implementer D)

**Verified against §4.1 directly** (`documentation/2026-04-06-Phase-1-
Submission-Guidelines-VF.md`), not from this task's own summary: the three
bullets are exactly as quoted (team name + lead contact, per-member
description, prior quantum/domain experience). §4.4's "up to 3 additional
appendix pages" and the 6pp concept-proposal limit confirmed to not apply
to the Team Profile — it is a separate submission component per §4, no
stated page cap of its own.

**New `documentation/TEAM_PROFILE.md`**: team name (AuraQu), full bios for
all three members (moved verbatim from §7, Berke's kept in the exact
register the task specified), each member's prior-quantum-experience /
prior-domain-experience stated explicitly per §4.1's third bullet
(Oussema: extensive; Berke: none in quantum, extensive in the problem
domain; Bartosz: none claimed), the full AI-workflow elaboration
(adversarial-split model table, repo/branch artifact table, the four-
sentence disclosure rationale) moved here as instructed. **Lead contact
details flagged, not invented** — genuinely absent from the whole
submission set; needs the repo owner before portal upload, cannot be
supplied by this task.

**§7 rewritten to 209 words** (target 150–200, table included — within a
few words of the low end of the range once the table's own ~35 words are
counted against it), down from **599** before this task. Kept: the member
table (already in the "one credential each" register per the task's own
hint), one short paragraph naming the QA methodological commitment and the
AI-workflow disclosure's short form, with an explicit pointer to the Team
Profile for the full version. Cut entirely: the two full bio paragraphs,
the adversarial-split model table, the repository/branch artifact table,
and the "why we disclose" four-sentence essay — all now live only in the
Team Profile.

**Checked, and the task's own assumption was wrong — corrected rather than
assumed true**: this task's Intent Contract says to "confirm [Berke's 'why
classical detection fails' paragraph] landed [in §1] and is not
duplicated." `grep -rn "classical detection fails"` across both submission
twins and `REVIEW_TARGETS.md` returns **nothing** — the paragraph is not
in §1, not duplicated, not anywhere in the repository. Per [[TASK-0332]]'s
own Done section, this was already disclosed there: the paragraph's actual
text was never supplied into the repository, only referenced as something
Berke would provide. Not fixed here either, for the same reason — content
cannot be attributed to a named collaborator without his own words. Left
correctly absent from the Team Profile too (it is §1 material per both
this task and TASK-0332, not team-profile material, once it exists).

**`doc_parity.py` verified** after the §7 edit: figures / code identifiers
/ title / headings / heading order all match.

**Planned Validation — `submission_build.py` re-run, delta measured
honestly**: body pages **12 → 11** (font/appendix findings unchanged: body
font 12.4pt PASS, appendix still 5/3 FAIL — untouched by this task's own
scope). A real, measured one-page saving, not the "single largest
structural saving available" the filing predicted — §7's own content was
~600 words out of a ~3200-word, 12-page body; removing it helps but does
not by itself come close to closing a 6-page gap. [[TASK-0344]]'s own
sequencing (land 0342+0343, re-render, drop font toward 10.5pt, re-measure,
only then cut content) is the right next step and is explicitly out of
this task's own scope.

**Files**: `documentation/TEAM_PROFILE.md` (new),
`documentation/PHASE1_SUBMISSION_V1.{md,html}`.
