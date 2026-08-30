# Experiment B, arms 2 & 3 — conservation, run at last

Egress to `www.ebi.ac.uk` and `rest.uniprot.org` is live in this container
(verified by fresh calls, real payloads, no `x-deny-reason`). The arms blocked
in `EXPERIMENT_B_RESULT.md` §2 have now been run.

**Result: an informative null. Conservation does not work as a pocket-level
filter on this cohort, in either direction, at either candidate setting. Used as
a negative filter on top of arm 1 it is actively destructive: rank-1 selection
goes 7/11 → 0/11.**

---

## 1. What was measured, and why it is not the register's old test

The register's existing negative result for conservation is a **residue-level**
AUC via added-last Shapley. The pre-registered arms 2/3 ask a different question:
whether conservation works as a **pocket-level negative filter**, on the
reasoning that an allosteric drug site should be *less* conserved than the
catalytic machinery it competes with in the candidate list. That reasoning is
sound and was untested. It is now tested.

Route, exactly as pre-registered:

```
UniProt acc → InterPro Pfam families → Pfam SEED alignment + family HMM
  → hmmalign seed to its own HMM, take match states off the RF line
  → Jensen–Shannon conservation per match state (Capra & Singh 2007),
    Henikoff position-based sequence weights, gap-penalised
  → hmmsearch the chain's entity sequence onto the same HMM
  → score carried back to auth residue numbers
```

All 20 targets, 13 apo-structure clusters, 20 chains scored. Per-chain Pfam
coverage 0.26–0.96 (median 0.83). Residues outside every Pfam domain are left
unscored rather than imputed.

**Truth definition is max-Jaccard, not max-recall** (handover §2), with
detection at Jaccard ≥ 0.3. Overlaps were reconstructed exactly from the cached
`_recall × n_site`, which is integral to 0 error, so nothing was re-run and
nothing is approximated.

Nothing is fitted anywhere below. Every ranker is one fixed field or a
parameter-free Borda sum.

## 2. The measurement works — three controls

**Control 1, textbook catalytic residues.** Every one lands in the top of its
own chain's distribution:

| structure | residue | JSD | percentile | |
|---|---|---|---|---|
| 2GIQ/2HAI A | 318, 319 | 0.848 | **0.990** | HCV NS5B GDD motif |
| 2GIQ/2HAI A | 320 | 0.718 | 0.929 | HCV NS5B GDD motif |
| 1K7X A | 49 | 0.829 | 0.957 | TrpA catalytic Glu |
| 1K7X A | 60 | 0.757 | 0.884 | TrpA catalytic Asp |
| 1K7X B | 86 | 0.406 | 0.831 | TrpB PLP Schiff-base Lys |
| 3DHF A | 247 | 0.795 | 0.898 | NAMPT PRPP-binding Asp |
| 2PBK A | 23 | 0.767 | 0.861 | KSHV protease nucleophile |

**Control 2, residue-level AUC** for membership of the true-site region: mean
0.461 (open), 0.519 (cryptic). Chance — reproducing the sign of the register's
existing negative result, on identical footing. (Positives here are the
max-Jaccard candidate's residues, a proxy for the drug-contact set, since the
exact contact residues are not recoverable from cache.)

**Control 3**, coverage and distribution shape: reported per chain, nothing
degenerate.

So the null below is a null in the signal, not in the instrument.

## 3. Arm 2 — conservation as a pocket-level ranker

Rank of the true pocket by mean pocket conservation, ascending (`r_cons_lo` —
the direction the negative-filter hypothesis predicts):

| stratum | setting | K | n detected | conservation rank-1 | median percentile | Fisher p (low) | Fisher p (high) |
|---|---|---|---|---|---|---|---|
| open | default | 4 | 6 | **0/6** | 0.401 | 0.59 | 0.58 |
| cryptic | default | 5 | 5 | **0/5** | 0.690 | 0.83 | 0.12 |
| open | `-m 2.8` | 4 | 6 | **0/6** | 0.333 | 0.45 | 0.83 |
| cryptic | `-m 2.8` | 6 | 8 | **0/8** | 0.658 | 0.98 | 0.11 |

Cluster-collapsed (one mean percentile per apo structure), so the duplicate
structures cannot inflate anything.

**Conservation never ranks the true pocket first, in any stratum, at any
setting.** In the cryptic stratum the median percentile is 0.66–0.69 — the true
pocket is *more* conserved than two-thirds of its competitors, which is the
opposite of the pre-registered direction.

## 4. This null is informative, unlike Experiments A and B arm 1

The register's recurring problem is that its tests cannot reach α=0.05 whatever
happens. This one can, for a strong effect:

| K clusters | largest uniform percentile still reaching p<0.05 |
|---|---|
| 4 | 0.144 — true pocket in the top 14% of candidates |
| 5 | 0.160 |
| 6 | 0.173 |
| 9 | 0.201 |
| 13 | 0.224 |

Observed medians are 0.33–0.69. A filter that reliably placed the true pocket in
the top ~15% of candidates by low conservation **would have been detected**, and
nothing resembling it is present. The test remains underpowered for a *weak*
effect, so the honest claim is: **no moderate-or-strong pocket-level
conservation filter exists on this cohort.**

## 5. Arm 3 — conservation as a filter on top of hydrophobic density

Parameter-free combination: Borda sum of rank-by-hydrophobic-density and
rank-by-ascending-conservation. No weights, no threshold, nothing tuned.

| | rank-1 count |
|---|---|
| hydrophobic density alone | **7/11** |
| Borda(hyd, low conservation) | **0/11** |

Per-target deltas are negative almost everywhere; PF_ATCASE and
TRP_SYNTHASE_F19 each fall 1 → 18. Adding conservation does not dilute a good
signal slightly — it destroys it. Conservation carries no complementary
pocket-level information here, and enough anti-correlated information to wreck a
working ranker.

**The conservation-as-negative-filter prediction is now tested and rejected.**
The register should record it as a measured negative rather than an untested
prior, and should no longer treat the residue-level Shapley result as the reason
it is unsettled — the pocket-level framing was the right objection, it has been
run, and it fails on its own terms.

## 6. A free confirmation of arm 1

These runs re-derive arm 1 under the *new* truth definition. Handover §2 warned
that max-Jaccard truth collapses size-driven results (volume, SASA → chance).
Hydrophobic density does not collapse:

| stratum | setting | hyd rank-1 | druggability rank-1 |
|---|---|---|---|
| open | default | **6/6** | 2/6 |
| open | `-m 2.8` | 3/6 | 1/6 |
| cryptic | default | 1/5 | 0/5 |
| cryptic | `-m 2.8` | 0/8 | 0/8 |

Identical to `EXPERIMENT_B_RESULT.md` §3 and handover §4, but now under
max-Jaccard truth with Jaccard ≥ 0.3 detection, computed from a different code
path. **Arm 1 survives the methodological correction that invalidated the
size-driven results.** That is the strongest thing that can currently be said
for it.

## 7. Incidental findings

- **1RLZ has only chain A deposited.** `DHPS_GC7` is configured for chains
  A + B; chain B is silently a no-op. DHPS is a homotetramer, so this is the
  same class of defect as the KSHV monomer configuration — another argument for
  the biological-assembly switch in handover §3.
- **fpocket residue numbers are chain-agnostic** in the cached runs
  (`int(line[22:26])`, chain ignored). For the two hetero-oligomers — 1K7X
  (α/β subunits) and 9QN5 (SAE1/SAE2) — one residue number carries two different
  conservation values. Handled by averaging and reported; but any future
  per-residue feature inherits this ambiguity, and it should be fixed at source
  by keying on `(chain, resnum)`.
- **PKR_MITAPIVAT's true pocket has zero Pfam coverage** and PKR_AG946's has
  0.20. SMYD3's is 0.32. Pfam does not cover these sites at all, which is itself
  mildly informative: the allosteric sites sit outside the conserved domain
  cores.

## Artifacts

`conservation.py` (build), `expB_cons.py` (arms 2/3), `cons_control.py`
(controls), `cons_power.py` (power), `conservation.json` (per-residue scores,
all 20 chains), `expB_cons.json` (per-target results), `struct_map.json`
(chain → UniProt → sequence → auth numbering), `pfam_cache/` (17 Pfam HMMs and
seed alignments, so this is reproducible without egress).
