# Additions staging area

Nothing here reaches the PDF until its `status:` is `APPROVED`. The merge tool takes only
APPROVED blocks, inserts each at its `anchor:`, and writes a **new** file — the verbatim copy of
his V4 is never edited in place.

Block format:

    ### ADD-<n> — <short title>
    status: PENDING | APPROVED | REJECTED
    section: <which section of the proposal>
    anchor: <a literal phrase from V4; the block is inserted immediately after that paragraph>
    cost: <approximate lines>
    ---
    <the text to insert, in his register and markdown style>

Rules, from PROVENANCE.md:
- A number that differs from his is a **second measurement on a second cohort**, never a correction.
- Per-structure AUC, averaged. Never pooled across proteins.
- Any best-of-N number carries its search budget in the same sentence, or does not go in.
- Run `python3 submission/tools/check_addition.py submission/phase1/ADDITIONS.md` before merging.

---

## Candidates — awaiting your decision

### ADD-1 — Protein-identity floor, second cohort
status: PENDING
section: 5. Validation Plan
anchor: A pooled figure without this floor is not interpretable, and we have found no report of the check.
cost: 2 lines
---
Re-measured on the second cohort described in Appendix B, the same constant-per-protein score reaches **AUC 0.771** across 630 proteins — above every method either track has tested, and a wider margin than the 0.65 above.

### ADD-2 — Independent replication of the central null
status: PENDING
section: 2. Technical Approach
anchor: because McNemar is a paired test over the same families.
cost: 4 lines
---
A second pipeline, built independently on a different detector and a different candidate filter, reaches the same verdict on a larger cohort: across 630 proteins in 399 families, the seeded walk loses to closeness centrality at every distal filter setting (family-weighted AUC 0.585 / 0.542 / 0.544 / 0.543 against 0.601 / 0.569 / 0.575 / 0.580; Wilcoxon p = 0.001, 0.003, 0.044, 0.258). The two cohorts are not pooled — they differ in detector and in family convention — so this is replication, not an enlarged n. Appendix B reports it in full.

### ADD-3 — A blind model over all 221 observables reproduces distance
status: PENDING
section: 2. Technical Approach
anchor: What it adds is simply not coherence
cost: 3 lines
---
The same conclusion survives combining the observables rather than choosing among them. A logistic regression over all 221 per-residue score vectors, true leave-one-family-out, reaches family-weighted AUC **0.7216** on the distal subset — against 0.5405 for the best single cell selected on the same data, and **0.7219** for the trivial reversed-distance floor. The difference from the floor is -0.0003 (Wilcoxon p = 0.90): optimally combined, the quantum observables reproduce distance and nothing further.

### ADD-4 — Appendix B, the full second-cohort report
status: PENDING
section: Appendix (new B, after references)
anchor: __END__
cost: ~1 page
---
(The full appendix drafted earlier — pipeline description, the four-MIN_HOP table, the LOFO result,
the two-source interference run, the family-provenance audit, the notebook run, and our retractions.
Held until ADD-1..3 are settled, since it must not repeat whatever goes into the body.)

### ADD-5 — Our retractions in the §7 ledger
status: PENDING
section: 7. Team Capability
anchor: It found five of our own errors in seven days, including our headline result.
cost: 2 lines
---
The same register operating on the second branch caught three more: an AUC read backwards in a distal proximity-floor claim, a classical-comparison arm that differed in operator as well as in coherence, and a blind positive filed as a to-do rather than reported. All three are corrected in the public history.

### ADD-6 — The thirteen operators and seventeen scores, named
status: PENDING
section: 2. Technical Approach (Paradigm)
anchor: That measured boundary, not a preference, is what sends the remaining quantum candidates toward many-body objects and conformational ensembles rather than single-structure optimisation.
cost: ~16 lines
---
**What was swept.** Residues are nodes at their C-alpha coordinates, edges within a 10 A cutoff; the walk is `U(t) = exp(-iHt)` seeded at the active site, reported in the converged time-average `p_avg(s->a) = sum_k |v_k(s)|^2 |v_k(a)|^2` — a sum of squares, which is why the converged propagator is phase-free. Every operator is real symmetric, hence Hermitian.

**Thirteen operators** = four edge weightings x three normalisations, plus the challenge-specified `H_new`:

| | adjacency `W` | combinatorial `L = D - W` | symmetric `I - D^{-1/2} W D^{-1/2}` |
|---|---|---|---|
| binary (`d < 10 A`) | `binary/adj` | `binary/comb` | `binary/sym` |
| exponential `exp(-0.3 d)` | `exp/adj` | `exp/comb` | `exp/sym` |
| Gaussian `exp(-d^2/72)` | `gauss/adj` | `gauss/comb` | `gauss/sym` |
| harmonic `1/(d+0.5)^2` | `harm/adj` | `harm/comb` | `harm/sym` |

`H_new` is the thirteenth: `L_sym` of the exponential graph plus a diagonal site potential `0.08 V_B + 0.16 V_T + 0.08 V_R + 0.04 V_C + 0.04 V_M`, each term z-scored and signed so penalties raise the potential and rewards lower it — `V_B` B-factor disorder, `V_T` chain termini and solvent exposure, `V_R` rigidity (degree, clustering, inverse GNM fluctuation), `V_C` GNM covariance with the core, `V_M` participation in the ten slowest GNM modes. Weights pre-registered in the notebook, not fitted here.

**Seventeen scores**, in five families:

| family | scores | what it ranks a residue by |
|---|---|---|
| occupation | `p_avg`, `p_peak`, `R` | converged transfer, its maximum over the time grid, and their ratio |
| proximity-corrected | `residLOG`, `residRAW`, `residLOG_dX`, `residRAW_dX`, `pavg_over_dX` | transfer with distance and degree regressed out, raw or log, optionally focused by walker spread |
| resolvent | `green_zero_0.01`, `green_zero_0.05`, `green_lmax_0.05` | `|<a|(E + i eta - H)^{-1}|s>|^2` at the band edge and band top — a commute-time / communicability analogue |
| dispersion | `neg_dD_mean`, `neg_ED_final`, `QMI` | spread of the walker's distance distribution, its final energy dispersion, and a mutual-information proxy |
| energy-uncertainty | `neg_dE`, `residLOG_dE`, `pavg_over_dE` | the seed state's spectral variance `sqrt(<E^2> - <E>^2)`, alone or combining with the above |

Thirteen times seventeen is the 221 cells per protein quoted above. One qualification belongs with this table rather than buried: `neg_dE`, the strongest single score, is time-independent by construction, and equals `sqrt(sum_j W_ij^2)` to machine precision — a classical local statistic wearing a quantum name. It ranks well and it cannot carry interference, which is one measured reason the coherent and decoherent arms agree.

