# Phase 1 Concept Proposal — structure and page budget

Deadline 15 Sep 2026. Max 6 pages + 3 appendix pages, min 10pt, PDF, <20 MB.
Their tip: "a well-structured 4-page proposal will outperform a rambling 6-page one."
Target: 5 pages + 2 appendix.

| § | section (their required headings) | pages | rubric weight it serves |
|---|---|---|---|
| 1 | Problem Framing | 0.75 | Relevance & Impact 25% |
| 2 | Technical Approach | 1.5 | Technical Approach 25% |
| 3 | Feasibility and Resource Requirements | 0.75 | Feasibility 20% |
| 4 | Expected Impact | 0.5 | Relevance & Impact 25% |
| 5 | Validation Plan | 1.25 | Validation Plan 15% |
| 6 | Hybrid / Cross-Domain Integration | 0.5 | Hybrid 5% |
| 7 | Team Capability | 0.25 | Team 10% |
| A | Appendix: results tables, ablations, honest negatives | 2 | supports 2,3,5 |

## The spine of the argument
1. Distal cryptic pockets are the undruggable problem. Geometry cannot find them --
   we MEASURED a proximity baseline at AUC 0.227, below chance, on distal targets.
2. A continuous-time quantum walk seeded at the active site reaches 0.617 there and
   beats that baseline in 47/53 families, p<1e-8. It works where the classical method fails.
3. The operator is not universal: within one protein a median of 45 of 884
   configurations work, across proteins there are 308 distinct winners. So we learn to
   RECOMMEND configurations from topology, cutting 884 to 6.
4. Validated on 1022 proteins / 630 scored / 399 families with family-level counting,
   permutation nulls and proximity floors -- and on held-out BCR_ABL1 (AUC 0.900, P@5 0.80).
5. Phase 2 delivers the circuit: Trotterised CTQW, coarse-graining, noise/ENAQT.

## Honest negatives to include DELIBERATELY (their tip #2 rewards this)
- overall the walk does NOT beat proximity (0.600 vs 0.574, p=0.45); only distal does
- the recommender's WEIGHTING is unreliable (BCR_ABL1 winner was rank 4)
- merging the shortlist is worse than picking one
- 16-node coarse-graining FAILED (AUC 0.529)
- the veto destroys the answer for 186 of 829 proteins, undetectable at prediction time
- challenge Table 1 defects: 6C1H contains no mavacamten; 4OBE is wild-type, not G12C

## Open decisions
- [ ] scope: joint AuraQu submission covering both tracks, or this track only?
- [ ] team profile details (names, roles, affiliations, prior quantum experience)
- [ ] public repo link? (repo is currently private)
