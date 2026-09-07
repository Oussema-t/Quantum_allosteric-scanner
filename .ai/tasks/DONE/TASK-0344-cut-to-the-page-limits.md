# TASK-0344 — 17 pages against a 6+3 limit: cut the document, and check the appendices even qualify

- Status: Done
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

## Done (2026-09-07, Implementer D)

**Sequence followed exactly as specified.** (1) Confirmed [[TASK-0342]] and
[[TASK-0343]] already landed. (2) Re-rendered and re-measured first, against
the real post-0343 number, not the stale 9/6·8/3 this task was filed against:
**12/6 body, 5/3 appendix.** (3) Dropped body font toward 10.5pt. (4)
Re-measured after every change, one lever at a time. (5) Only then cut
content, against the real number at each step — never against a stale one.

**Free levers, all in `submission_build.py`'s injected print stylesheet only
— the source HTML (also a published, screen-read artifact) is untouched**:

| Lever | Before | After |
|---|---|---|
| Body font | 12.4pt | 10.5pt (matches TASK-0342's own small-text floor — one size, not two) |
| Line-height | 1.62 | 1.22 |
| Page margins | 16/15/18/15mm | 11/11/12/11mm (still normal print margins) |
| Section spacing | 84px between sections | 8px |
| Paragraph/list margins | 1.05em | 0.6em |
| h2 / h3 size | 1.72rem / (source default) | 1.3rem / 1.0rem (rem-based — the body font-size lever alone does not touch these, confirmed by re-measuring) |

Two real bugs caught by these levers, fixed rather than left as fallout:
`table{font-size:14.6px}` was initially scaled proportionally with body font
and fell to 9.3pt — **under the floor this file exists to enforce** — reverted,
table font left untouched. `h2 .sub` fell under 10pt once h2 itself shrank —
added to the existing small-text floor list rather than given its own
one-off rule.

**Content changes, cut order followed (§7 already handled by 0343 → Appendix
A → tables over prose)**:
- Appendix A/B/C compressed to compact fragments — full methodology stays in
  the linked repository (§4.4 explicitly permits this), not deleted.
- §2's (a)/(b)/(c) converted from three paragraphs to a table — "table rows
  rather than prose" applied literally, not just to existing tables.
- §1/§2/§4/§5/§6 prose tightened throughout, no claim or number dropped.
- **§3 grown, not cut, per this task's own explicit protection**: 153 →
  309 words, adding real content (data/compute/software, per Guidelines
  §4.3 item 3's own three-part ask) rather than padding.
- **A real content bug caught while compressing, not introduced by it**:
  §1's taxonomy table already said "(Appendix C)" for cardiac myosin's
  single-molecule limitation, but no such bullet existed in Appendix C —
  a dangling cross-reference from [[TASK-0332]]'s own edit, never a
  question this task set out to check. Added the missing bullet.

**Planned Validation, both halves, not either**:
- `submission_build.py`: **RESULT: PASS.** Body 6/6, appendix 3/3, body
  font 10.5pt (≥10pt), no horizontal overflow. Small-text WARN unchanged at
  ~200 chars — the same disclosed SVG-label/`<sup>`-exponent residual
  TASK-0342 already accepted, not a new regression (confirmed by diffing
  the reported size list).
- **The human-opens-the-PDF check actually run, not skipped**: rendered
  every page to PNG via `pdfplumber` and read each one. Found two real
  visual defects the compliance checker's own numeric checks cannot see
  (disclosed in its own report note) and fixed both before calling this
  done:
  1. The §6 SVG pipeline diagram's rightmost text ("This report",
     `text-anchor="middle"` at x=750) was placed past its own
     `viewBox="0 0 760 190"` right edge — always marginal, exposed once
     print margins tightened gave it less rounding slack. Widened the
     viewBox to 800; content positions unchanged.
  2. `overflow-wrap:anywhere` (TASK-0342's own fix for a different bug) made
     `table-layout:auto` treat every character as a valid break point,
     so narrow columns lost most of their allocated width: team names
     broke mid-word ("Ousse/ma/Turki"), verdict chips broke mid-word
     ("HOL/DS"), table headers broke mid-word ("ALLOST/ERIC"). Fixed with
     three targeted rules (`td:first-child`/`th:first-child` min-width,
     `.chip` nowrap, `th` nowrap) rather than removing `anywhere` itself,
     which would have reopened the exact clipping bug it was added for.
  Re-rendered and re-viewed after each fix; final PDF (9 pages) read page
  by page, no clipping, no mid-word breaks, no overlap.
- `doc_parity.py`: clean after every batch of changes, both twins.
- `.ai/tools/test_submission_build.py` + `test_doc_parity.py`: 24+14=38
  pass, matching [[TASK-0342]]'s own count — no regression from the CSS
  changes.

**Not resolved, correctly left to the repo owner**: whether Appendix A/B/C
qualify as §4.4 "supplementary material" (technical diagrams, references,
prior work) at all, versus needing to move into §5 or the repo link
proper. This task's own filing named it a scoping question for the repo
owner, not an implementer call — compression alone was enough to reach
compliance without forcing that decision, so it stays open, disclosed
rather than decided by default.

**No confidential/proprietary material check**: grepped the final document
for the collaborator's unpublished work — none present; the only new
mention is "no proprietary or synthetic structures" in §3's own data
paragraph, which is a disclosure, not a leak.

**Files**: `.ai/tools/submission_build.py` (print-CSS levers + bug fixes),
`documentation/PHASE1_SUBMISSION_V1.{md,html}` (content compression + the
cardiac-myosin/Appendix-C fix + the SVG viewBox fix).
