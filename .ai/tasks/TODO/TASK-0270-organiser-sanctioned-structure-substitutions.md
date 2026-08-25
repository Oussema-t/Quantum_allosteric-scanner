# TASK-0270 — Act on the organiser-sanctioned structure substitutions: KRAS `8S8C`, BCR-ABL1 apo

- Status: TODO
- Assignee: **Implementer B** (after [[TASK-0265]] — same structural-validity skillset, and 0265's BCR-ABL1 myristoyl work feeds directly into item 2)
- Priority: **High — an organiser permission with an expiry-free window, but it changes published numbers, so decide deliberately**
- Filed: 2026-08-26 by Reviewer
- Source: `documentation/2026-08-26-organiser-clarifications.md`
- Related: [[TASK-0221]], [[TASK-0222]], [[TASK-0169]], [[TASK-0250]], [[TASK-0257]], [[TASK-0258]], [[TASK-0265]], [[TASK-0184]]

## What the organisers said

Verbatim text and provenance in
`documentation/2026-08-26-organiser-clarifications.md`. Two items require a
decision:

> 2. A nice structure for KRAS G12C would be 8S8C.
> 4. BCR-ABL1 — you may substitute 1OPL with an alternative apo structure that fits your pipeline. Please document the rationale in your submission.

**This was a private reply to us. There is no corresponding public revision of
the Challenge Statement** (checked 2026-08-26). Both items must therefore be
cited to that clarification wherever they appear in the submission.

## Item 1 — KRAS G12C and `8S8C`

**Establish what 8S8C is before doing anything else.** The organisers said "a
nice structure ... would be 8S8C" — a suggestion, not a mandate, and it does
not state whether they mean it as apo, holo, or simply a better reference.
Acting on an assumption here would repeat exactly the [[TASK-0169]] failure
mode (a mandated structure that turned out not to contain the ligand its own
table claimed).

- [ ] Query RCSB live: what is `8S8C` — method, resolution, chains, ligands
      present, mutation status (G12C?). Is it apo or holo?
- [ ] Compare against our current `4OBE` apo on the axes that matter:
      resolution, completeness, missing residues, chain count, and whether the
      Switch-II pocket region is resolved.
- [ ] **Do not substitute silently.** Every KRAS G12C number in the register
      rests on 4OBE: floor, AUC, ENM validity (`r = 0.646`, PASS —
      [[TASK-0250]]), attribution shares, and the pocket taxonomy
      (contact-adjacent, min heavy-atom **1.32 Å** — [[TASK-0258]]).
- [ ] If 8S8C is a viable apo: score **both** and report side by side, the way
      [[TASK-0222]] handled the Cardiac Myosin pair. Do not swap one number
      for another.
- [ ] Re-check the [[TASK-0169]] finding under 8S8C: KRAS's pocket was
      measured at van der Waals contact with the active site. Does a different
      apo change that, or is it a property of the target rather than the
      structure? **This is the scientifically interesting half of the item.**

## Item 2 — BCR-ABL1 apo substitution

Permission granted, **rationale required in the submission** — that is an
explicit instruction, not a courtesy.

- [ ] Enumerate candidate apo structures for ABL1 kinase that fit the
      pipeline, with the [[TASK-0209]] VALID rule applied and live RCSB
      verification of each.
- [ ] Score the strongest candidate alongside `1OPL`; report both.
- [ ] Weigh, explicitly, and write the reasoning down for the submission:
      - **For substituting**: 1OPL's ENM validity is only **MARGINAL**
        (`r = 0.493`, [[TASK-0250]]), so its ENM-derived results are weakly
        interpretable under [[TASK-0257]]'s framing.
      - **For substituting**: 1OPL is the autoinhibited near-full-length
        structure, which entangles the myristoyl/N-cap mechanism
        [[TASK-0265]] is investigating. A cleaner kinase-domain apo may make
        the pocket question tractable — **or may remove the mechanism from the
        model entirely**, which is the [[TASK-0251]] scope-truncation failure
        mode in a new place. Decide knowingly.
      - **Against substituting**: every published BCR-ABL1 number rests on
        1OPL, including the pocket taxonomy (proximal, min heavy-atom 7.96 Å)
        and the [[TASK-0235]]/[[TASK-0241]] ceiling dispute. Substitution
        invalidates that comparison set.
- [ ] Coordinate with [[TASK-0265]]: its BCR-ABL1 myristoyl verification
      should inform this choice, not run in parallel and disagree.

## Item 3 — housekeeping

- [ ] Mark [[TASK-0222]] resolved: 8QYP → 8QYR is sanctioned as primary, on
      the record.
- [ ] Update [[TASK-0221]] §3 with the answers received and the four questions
      that remain open — **(d), (e), (f)**, of which **(f) gates
      [[TASK-0269]]**.
- [ ] Flag to Bartosz that the channel is live and responsive: (e) and (f) are
      both worth re-asking, and (f) would let [[TASK-0269]] proceed on an
      organiser ruling rather than our own permissive reading.

## Acceptance

- [ ] Live RCSB characterisation of `8S8C`, stated before any substitution.
- [ ] Side-by-side scoring for both targets — never a silent swap.
- [ ] A written rationale for the BCR-ABL1 choice, in submission-ready prose,
      since the organisers explicitly require it.
- [ ] [[TASK-0222]] closed, [[TASK-0221]] updated.
- [ ] `RESULTS.md`.

## Constraint

An organiser permission is not an instruction to use it. If 8S8C or a new ABL1
apo makes our numbers *worse*, that is still the honest choice if the
structure is better — and if we decline a permitted substitution, the
submission should say why. **Neither substitution may be adopted because it
improves a result.** Decide on structural grounds, then report whatever the
numbers do.
