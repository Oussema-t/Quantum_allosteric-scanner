# TASK-0344 — 17 pages against a 6+3 limit: cut the document, and check the appendices even qualify

- Status: TODO
- Owner: **Implementer** (drafting) → repo owner sign-off on what goes
- Priority: **BLOCKER — over-length may be "returned or assessed only on the first 6 pages"**
- Filed: 2026-09-07 by Reviewer thread (id via `claim.py reserve-next`)
- Related: [[TASK-0332]], [[TASK-0339]], [[TASK-0341]], [[TASK-0342]], [[TASK-0343]]

## Measured, by `submission_build.py` at `9cb3b7e`

```
[FAIL] body pages      9 / 6
[FAIL] appendix pages  8 / 3
[PASS] body font       12.4 pt  (min 10 pt)
```

**17 pages against a 9-page allowance.** The body is 1.5× over; the appendices are
**2.7× over**. Every prior estimate in this register was words × a constant and
every one of them was wrong — [[TASK-0339]] worked from "a realistic 5–6 pages"
while the true figure was 9.

Guidelines §5: *"submissions exceeding the page limit may be returned or assessed
only on the first 6 pages."* At 9 body pages, **§5 Validation — the strongest
section in the document — and §6 and §7 fall outside the assessed range.**

## Free space before any content is cut

- **Body font is 12.4pt against a 10pt minimum.** Dropping toward 10–10.5pt is a
  pure win, costs nothing, and is the first lever to pull. Do this before cutting
  a single sentence, then re-measure — it may move the body 9 → 7 on its own.
- [[TASK-0343]] moves the biographies out of §7 into the separate Team Profile.
- [[TASK-0342]]'s table fix will change pagination in **both** directions (unclipped
  tables are wider and may reflow taller). **Land 0342 and 0343 first, re-render,
  and re-measure before deciding what content to cut.** Cutting against a stale
  page count is how the wrong thing gets deleted.

## The appendices need an eligibility check, not just a trim

§4.4 defines what supplementary material *is*:

> • Up to 3 additional pages of appendices (**technical diagrams, references,
>   prior work**).
> • A link to a public code repository (if relevant).
> Do not include confidential or proprietary information.

Current appendices: **A** — claims ledger; **B** — what we retracted and how fast;
**C** — known defects, disclosed. Against §4.4's three named categories, only parts
of these clearly qualify. That is a scoping question the repo owner should rule on
before anyone trims them to length, because the answer may be "most of this is not
supplementary material at all."

My read, offered as input and not a decision: **Appendix B and C are the most
distinctive things in the submission** — a register that publishes its own
retractions and defects is the evidence behind every claim §5 makes. If they do
not fit §4.4's categories, the answer may be to *compress them into §5* rather than
delete them, since that is where they do their work. **The repo link is explicitly
allowed by §4.4** and is the natural home for the full ledger — the repository is
already public and already the disclosure strategy ([[TASK-0184]] §7).

Also confirm no confidential or proprietary material is present — the collaborator's
unpublished HPC results and the `allosteric` branch's unreleased pipeline are both
referenced in this register; neither should reach a supplementary appendix without
Oussema's agreement.

## Intent Contract

- Outcome: body ≤ 6 pages, appendices ≤ 3, measured by `submission_build.py`
  reporting `RESULT: PASS`, with the sub-10pt warning cleared ([[TASK-0342]]).
- Sequence, and it matters: **(1)** land 0342 and 0343; **(2)** re-render and
  re-measure; **(3)** drop the body font toward 10.5pt; **(4)** re-measure again;
  **(5)** only then cut content, against the real number.
- Cut order, from [[TASK-0339]]'s own analysis and the 2026-09-07 audit: §7 first
  (largest section, smallest weight — largely handled by 0343), then Appendix A's
  QUALIFIED rows, then table rows rather than prose, since tables are the densest
  page consumers here.
- **Protect §3.** At 107 words for a 20%-weighted criterion it is the most
  under-served section in the document. It should *grow* during this task, not
  shrink — the space has to come from elsewhere.
- Constraints:
  - Do not solve the page limit with font size below 10pt. Guidelines §5 is
    explicit and the build already flags sub-10pt text.
  - Do not delete a claim to save space without recording it — if something goes,
    it goes into the repo, which §4.4 permits linking.
  - Re-run `doc_parity.py`; both twins change together ([[TASK-0340]] wired CI).
- Planned Validation: `submission_build.py` reports PASS on both page counts, and
  a human opens the PDF and confirms no table is clipped. Both, not either.

## Note

The organisers confirmed **unlimited cancel-and-reupload until 2026-09-15**
(clarification (g)). So the right move is to get a compliant PDF uploaded as soon
as this task passes, and keep improving it afterwards — a compliant 6-page
document uploaded on the 9th strictly dominates a perfect one that is still 17
pages on the 14th.
