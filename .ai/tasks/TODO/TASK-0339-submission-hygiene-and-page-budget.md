# TASK-0339 — Submission hygiene and the page budget: the edits TASK-0332 does not cover

- Status: TODO
- Owner: **Implementer C** — must land **before** [[TASK-0332]]'s drafting starts
- Priority: High — one item is a ToC violation, one is a minimum-set omission
- Filed: 2026-09-07 by Reviewer thread (id via `claim.py reserve-next`)
- Source: `.ai/reviews/2026-09-07/...adversarial-submission-audit.md` §3.5, §3.7–3.9, §3.11–3.12
- Related: [[TASK-0332]], [[TASK-0184]], [[TASK-0307]]

## 1. §8 "Attack these first" must go — it breaks the mandated ToC

Guidelines §4.3 mandates **seven** numbered items. The document has **eight**, and
the eighth is an internal review-solicitation asking for *"a ruling on 01 and
06"*. It is also mis-ordered — §8 sits *after* Appendices A–C.

Together with the front-matter (`Draft | v1 — for adversarial review`,
`## What this document is`, *"circulated for adversarial review"*) that is
**~758 words addressed to an internal reviewer** in a document going to a panel.

Move §8's content to `REVIEW_TARGETS.md`, excluded from the submission. Two of
its open questions — 01 *"what is actually quantum about this"* and 06 *"benchmark
or paper"* — should be **answered inside §1 and §2**, not posed.

## 2. The page budget has never been checked, and every planned edit is additive

Measured word counts, body §1–7 = **2233 words** plus ten tables plus an unbuilt
figure — a realistic 5–6 pages at 10pt against a 6pp limit. [[TASK-0332]] then adds
four §2 positives, a clinical paragraph, two full bios and a lifted paragraph:
**plausibly +700–900 words with no cuts named anywhere.** v2 as specified goes over.

The budget is also inversely correlated with the rubric weights:

| section | words | weight |
|---|---|---|
| §7 Team | **709** (32% of body) | **10%** |
| §3 Feasibility | **107** | **20%** |
| §2 Technical Approach | 468 | 25% |

**The single highest-leverage editorial move available**: cut §7 to ~350 words and
move the space to §2 and §3. The 709 words contain three passages arguing *why*
the team discloses its AI usage — a defensible decision ([[TASK-0184]] §8 item 07),
but three paragraphs of justification reads as anxiety about it. Four sentences;
keep the QA-provenance argument and the cross-model adversarial-split table (both
genuinely differentiating); cut the rest.

**Render to PDF at 10pt and count pages before freeze.** This has never been done.
If over 6, cut §7 first, then Appendix A's QUALIFIED rows.

## 3. c-Myc is entirely absent from V1 — and it is in the mandated minimum set

Challenge Statement §6: *"c-Myc and the targets listed in Table 1 constitute the
**minimum set** required for submission."* V1 mentions `c-Myc` **0** times; the
superseded DRAFT mentions it 3 times. `results/MYC_MAX/` exists — **the work was
done, the restructure dropped it.** [[TASK-0184]]'s own Open Questions predicted
this ("recommend a short dedicated subsection so it is visibly not forgotten").

Two or three sentences plus the artifact reference closes it. While there: add one
sentence on AWS Braket / Classiq (currently 0 mentions each) — *"we evaluated the
provided infrastructure and here is why neither changes the `FAULT_TOLERANT_ONLY`
verdict"* scores better under Feasibility than silence.

## 4. The MYR error has a third copy [[TASK-0332]] does not list

Verified: `PHASE1_SUBMISSION_DRAFT.md` (47.5 KB, larger than V1) still carries
*"unexplained ligand"*. It is also the file the 2026-08-31 evidence pack audited,
so anyone following that pack's line references lands in the stale document.

Rename to `ARCHIVE-PHASE1_SUBMISSION_DRAFT-v0.md` with a superseded-by banner, or
delete. Two files both named like the submission, one wrong, eight days out, is
the [[TASK-0307]] failure mode the parity checker was built to prevent — and
parity only covers the `.md`/`.html` pair, not draft/V1.

## 5. §6 declares itself unbuilt, in place of the section's content

§6 currently ships a boxed admission that the diagram is undrawn and the shipped
demo contradicts the paper. Disclosing defects in Appendix C is a strength;
disclosing them *instead of* a 5%-weighted section's content is not the same move.

Reconcile the `main`-branch demo ([[TASK-0184]]'s TODO, still unchecked — and the
`keepalive.yml` workflow proves the demo is live, so a judge clicking through is
not hypothetical), draw the diagram, delete the box. If it truly cannot be drawn,
three boxes and two arrows in mermaid beats a paragraph saying it does not exist.

## 6. §7's repo statistics are stale — and independently checkable

| | claimed | actual (2026-09-07) |
|---|---|---|
| task files | 338 | **355** |
| done | 310 | **326** |
| commits | 549 | **579** |

This is the one number a referee can check with `ls \| wc -l` after following the
repo link, and it sits inside the paragraph arguing this team audits its own
numbers. **Regenerate at freeze and pin a SHA** — *"as of `<sha>`, 2026-09-14"* —
so it stays true as the register keeps moving.
