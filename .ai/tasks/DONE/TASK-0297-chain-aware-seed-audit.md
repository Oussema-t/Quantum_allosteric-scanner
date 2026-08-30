# TASK-0297 — Chain-agnostic residue matching: Finding F corrected 9/28 → 8/28

- Status: Done (diagnosis + Finding F correction). **fpocket-side remediation open → [[TASK-0298]].**
- Assignee: Reviewer thread
- Priority: **Critical — corrects a number in the collaborator brief the day before the submission sync**
- Filed: 2026-08-30 by Reviewer thread, from the external distal-pockets session's HANDOVER v3 §5 defects 6 & 7
- Related: [[TASK-0288]], [[TASK-0291]], [[TASK-0282]], [[TASK-0290]], [[TASK-0298]]

## Credit

Both defects were **found by the external distal-pockets session**, not
here. They are defects in **this** repo, not that session's. Confirmed
independently before acting.

## The two defects

**D1 — fpocket.** `fpocket_candidates` parses pocket residues as
`int(line[22:26])`, discarding the chain. Consumers build
`idx_of = {int(r): i for i, r in enumerate(resn)}`, which for a
multi-chain selection keeps only the **last** chain's index per residue
number.

**D2 — the seed, same class.** `prep()` builds the active site with
`np.isin(apo.resnums, detected_active_site)`, spreading the active site
detected for **one** chain onto **every** configured chain.

## The distinction that matters

**D2 is not uniformly wrong**, and naively "fixing" it would have
corrupted five targets that are currently correct:

- **Homo-oligomer** — every chain genuinely has its own active site at the
  same residue numbers. Spreading is **CORRECT**; restricting to the
  detection chain would *discard a real active site*.
- **Hetero-oligomer** — residue 49 of chain A is a different residue from
  49 of chain B. Spreading is nonsense.

Each exposed target was therefore classified by querying RCSB
polymer-entity descriptions:

| target | apo | collisions | kind | verdict |
|---|---|---|---|---|
| GAC_BPTES / GAC_CPD12 | 7SBN | 406 / 405 | homo | spreading correct |
| PF_ATCASE | 7ZP2 | 328 | homo | spreading correct |
| FBPASE_95S | 5LDZ | 310 | homo | spreading correct |
| PKR_MITAPIVAT / PKR_AG946 | 7FS3 | 422 | homo | spreading correct |
| **SUMO_E1_FHJ** | 9QN5 | 280 | **hetero** (SAE1/SAE2) | wrong, but `min_A` unchanged |
| **TRP_SYNTHASE_F6F / F19** | 1K7X | 253 | **hetero** (α/β) | **wrong — `min_A` moves** |
| DHPS_GC7 | 1RLZ | 0 | chain B **not deposited** | `min_A` unchanged |

**10 of 33 targets are exposed. Exactly one has a wrong `min_A`.**

## Finding F — corrected

`TRP_SYNTHASE`'s `min_A` = 1.29 Å came from matching the **α-subunit's**
active-site residue numbers onto the **β subunit**. Chain-correct value:
**2.88 Å**. It leaves the spike.

| | spike | binomial p |
|---|---|---|
| committed | 9/28 | 2.03×10⁻⁶ |
| **corrected** | **8/28** | **1.51×10⁻⁵** |

**Finding F survives, materially unchanged.** The headline moves from
"~32% of the benchmark" to **"~29%"**. Remaining spike members: KRAS_G12C,
MKK7_IBRUTINIB, GLUK1_BPAM, TEM1_BLA_CBT, DHPS_GC7, FPPS_YF0282,
FBPASE_95S, PF_ATCASE.

**Independent confirmation:** [[TASK-0291]] had already flagged
`TRP_SYNTHASE` as the one spike target whose `min_A` was misleading —
median 14.1 Å, 7 spatial components spanning 38.4 Å. Two unrelated lines
of evidence now agree it does not belong in the spike.

## What this does NOT change

- [[TASK-0288]] Findings A–E — they test scale-free landscape shape
  against scale-free position and do not depend on the absolute seed.
- [[TASK-0290]]'s 0/33 recompute — that tested tier *provenance*, a
  different axis from chain matching. Both hold.
- Homo-oligomer `min_A` values — GAC, PF_ATCASE, FBPASE, PKR all stand.

## Also confirmed from the same handover

- **`DHPS_GC7` is configured for chains A+B but 1RLZ deposits only chain
  A.** Chain B is a silent no-op. DHPS is a homotetramer — same class as
  the KSHV monomer configuration.
- The handover's §6 item 1 ("fix `detect_active_site` to fail loudly —
  now urgent") is **already done** — [[TASK-0290]], committed `b6ee248`
  on 2026-08-29. That session was working from a repo copy predating it
  and should be told.

## Open

D1 (fpocket chain-agnostic parsing) is **not** remediated here. It affects
the *candidate* residue sets for 9 targets, all of which sit in
[[TASK-0282]]'s frozen 20 — so the published ceiling (0.1649) and
[[TASK-0287]]/[[TASK-0292]]/[[TASK-0293]] are all exposed by an
unquantified amount. → **[[TASK-0298]]**.
