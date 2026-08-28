# TASK-0286 — Does a structural (not sequence-family) domain parser change TASK-0284 Part B's verdict?

- Status: Done
- Assignee: Implementer B
- Priority: Medium — follow-up to a disclosed caveat, not a gap in a shipped claim
- Filed: 2026-08-28 by Implementer B (user-directed follow-up to [[TASK-0284]])
- Related: [[TASK-0284]], [[TASK-0258]]

## Why

[[TASK-0284]] Part B tested whether the allosteric-site near/far
bimodality is explained by domain architecture (active site and pocket in
the same vs a different domain), using **Pfam** as the domain source —
verified live, but explicitly caveated as **sequence-family boundaries,
coarser than a real structural-domain parser** for large multi-lobed
proteins. The cited example: CARDIAC_MYOSIN's entire ~700-residue motor
head is ONE Pfam entry ("Myosin_head") despite the real fold having
several distinct structural subdomains (upper/lower 50 kDa, converter).
That caveat was stated but not tested. The result it could affect: Part
B's Fisher exact **FAILED** (p=0.12, n=32) with the far cluster's own
same-domain majority (6/9) driven mainly by targets whose single Pfam
domain may not be a single structural domain.

User-directed: build a structural (contact-graph-based) domain parser and
re-run Part B's same test with it, to see whether the verdict changes.

## Scope

- [x] Build a structural domain assignment from the apo Cα contact graph
      already computed per target (`allostery.potentials.gnm_context`'s
      own binary contact matrix `A`, same `enm_cutoff` as everywhere else
      in this register — no new hyperparameter). Use an established,
      un-tuned community-detection method (e.g. `networkx`'s modularity-
      based `greedy_modularity_communities`) — **not** a fixed k=2 chosen
      to reproduce a desired split. Restrict to the chain shared by seed
      and pocket, matching [[TASK-0284]]'s own Pfam-path scope choice.
      Built three candidate methods (modularity communities; spatial
      k-means; sequence-contiguous split-density scan), not one — see Done.
- [x] Sanity-check the method BEFORE trusting it at scale: does it call
      KRAS_G12C (170-residue, single Ras fold) one domain? Does it split
      CARDIAC_MYOSIN's motor head into >1 community, and does BCR_ABL1's
      kinase domain come out as its well-known bilobed (N-lobe/C-lobe)
      architecture or as one community? Report whichever it finds, not
      whichever confirms the caveat. **All three fail this check** — see
      Done.
- [ ] Re-run the same same-domain/cross-domain classification and the
      same pre-registered 2x2 Fisher exact against [[TASK-0284]]'s own
      near/far split — **not reached**: no candidate method passed its own
      sanity check, so none is trustworthy enough to feed into the 2x2.
      Running the Fisher exact on a method already shown to misclassify
      the single-domain control would manufacture a number, not answer
      the question — see Done and the Constraint below.
- [ ] Report the structural-parser verdict directly against the Pfam
      verdict — **N/A**, no structural-parser verdict was produced (see
      above). TASK-0284's Pfam-based FAILS stands, unmodified.
- [x] `SUMO_E1_FHJ` — moot: no method reached per-target classification at
      all (all three rejected at the control-check stage, before any
      target-specific run).

## Acceptance

- [x] Committed script, reusing `allostery.potentials.gnm_context` (not
      re-derived). `task0284_bimodality_and_nulls.json`'s near/far split
      was not reached (see Scope) — no per-target domain call to join it
      against.
- [ ] Direct side-by-side table: Pfam-based vs structural-parser-based
      domain call, per target. **Not produced** — no structural-parser
      method survived validation to generate one.
- [x] Fisher exact reported under the structural method, either way. —
      reported as **not computed, and why**, which is the honest form of
      "either way" here: no method to compute it from.
- [x] `RESULTS.md` addendum stating whether TASK-0284's FAILS verdict
      survives a finer domain definition — it does, by default (no finer
      definition was achievable), stated in the addendum.

## Constraint

One method, chosen and sanity-checked before the real run, not swept for
whichever gives the desired answer — same discipline [[TASK-0284]] itself
used for the Pfam-based test.

## Done (2026-08-28, Implementer B)

**Three candidate structural-domain-parser methods built and validated
against three known controls (KRAS_G12C = single domain, CARDIAC_MYOSIN =
several real subdomains within one Pfam entry, BCR_ABL1 = textbook
bilobed kinase) before any was trusted at scale — all three failed their
own control check.** New `scripts/task0286_structural_domain_parser.py`,
reusing `allostery.potentials.gnm_context`'s binary contact matrix
unchanged (same `enm_cutoff` per target as every other GNM quantity in
this register). Full method-by-method reasoning and numbers are in the
script's own docstring and printed output (`/tmp/task0286.log`, not
committed — ephemeral run log); summary:

1. **Modularity communities** (`networkx.greedy_modularity_communities`,
   resolution swept 0.3/0.5/0.7/1.0): at every resolution tested, KRAS_G12C
   (the single-domain control) splits into 2-5 communities, never a clean
   1 — closest at resolution=0.3 (2 communities, 158/12, a small
   satellite rather than an unambiguous single domain) but that same
   resolution's own behaviour on the other controls is inconsistent
   across the sweep (non-monotonic community counts as resolution
   increases — an artefact of the greedy heuristic's own order-dependence,
   not a real signal to tune against).
2. **Spatial k-means + silhouette-selected k** (same silhouette-based
   model-selection idea [[TASK-0284]]'s own Finding A used successfully
   on a genuinely bimodal 1-D quantity, applied here to 3-D coordinates):
   KRAS's own best-k silhouette (k=4, 0.302) is not meaningfully lower
   than CARDIAC_MYOSIN's (k=2, 0.371) or BCR_ABL1's (k=3, 0.352) — any
   non-spherical single globular fold gets a moderate-silhouette "split"
   for the mundane geometric reason that few real domains are perfect
   spheres. Cannot separate the single-domain control from the known
   multi-domain ones.
3. **Sequence-contiguous split-density scan** (single-split
   intra-vs-inter contact-density maximisation — the classical PUU/
   DomainParser principle at its simplest level): dominated by a trivial
   edge effect. The best split lands at or within 5 residues of the
   `minseg=20` boundary for 4 of 5 targets tested, **including both**
   the single-domain control (KRAS, split at residue 149/170) **and**
   the known-bilobed kinase (BCR_ABL1, split at 430/451) — a small
   terminal fragment trivially has fewer contacts to the rest of the
   chain regardless of any real domain boundary. Needs a materially more
   careful re-implementation (proper edge exclusion, multi-split search,
   null-model normalisation) to be usable at all.

**None of the three is trustworthy enough to feed into Part B's Fisher
exact.** Per this task's own Constraint, building a fourth method and
tuning it until it "looks right" on the controls would be exactly the
outcome-fishing this task exists to avoid — so this stops here rather
than iterating to a method that happens to confirm or overturn TASK-0284.
A real structural-domain assignment needs a validated tool (PUU,
DomainParser2, or a published ENM/hinge-detection method) not available
in this environment — the same class of gap as no DSSP/biotite
([[TASK-0284]]'s own Finding B).

**Verdict: [[TASK-0284]] Part B's Pfam-based result (FAILS, p=0.1206,
n=32) is neither confirmed nor overturned by a finer structural parser —
none could be built and trusted here.** Pfam remains the best available,
live-verified domain source for this register. Its coarseness caveat is
now resolved as "attempted, and found genuinely hard to do better with
what's available" rather than merely asserted.

**Addendum to [[TASK-0284]]** filed in that task's own DONE file, per
standing convention (dated addendum, not an in-place edit).

**Suite**: no code in `src/allostery` was modified; one new script only,
no regression run required.

**Moved TODO → IN_PROGRESS → DONE.**
