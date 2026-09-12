# TASK-0377 — Compute the thing allostery is actually defined as: ΔΔG coupling on BCR-ABL1, with dasatinib as the discriminative control

- Status: TODO
- Owner: **Architect/Planner** to scope; Implementer with GPU access to run
- Priority: **Phase-2 headline candidate. Not before 2026-09-15.**
- Filed: 2026-09-12 by Reviewer thread (id via `claim.py reserve-next`)
- Source: external reviewer discussion, 2026-09-12
- Related: [[TASK-0229.006]], [[TASK-0166]], [[TASK-0345]], [[TASK-0374]], [[TASK-0371]]

## The observation this rests on, verified

**Our Phase-1 pipeline computed no free energy anywhere.** Checked directly:
`scripts/run_challenge.py` imports `analysis`, `baselines`, `clean`,
`hamiltonians`, `labels`, `pathways`, `propagators`, `protocol`, `report` — no
thermodynamics in the shipped path. Everything it produced is **rankings over a
graph**.

`src/allostery/corex.py` exists (12.7 KB, COREX/EAM, `dG_unfold = dG_hydrophobic
− T·dS_conf` at 298.15 K, [[TASK-0229.006]]) and **is not in the run path**.

**Allostery is *defined* as ΔΔG coupling** — the change in binding affinity at one
site caused by occupancy at another. That is what ASBench's annotations, the
mutagenesis literature and every allosteric drug programme mean by the word.
**Every arm we ran measured a proxy for a quantity we never computed.** That gap
is larger than the quantum question, and it is the strongest single criticism this
project has received.

## Why BCR-ABL1 and nothing else

- **`5MO4` is the ternary endpoint**: ABL1 (T334I/D382N) with **both asciminib
  (AY7) and nilotinib (NIL)** bound, 2.17 Å, one chain, non-covalent both — and
  it is already in `targets.yaml` as the structure the myristoyl pocket was
  derived from.
- **The mutant matches the published benchmark.** `1OPL`/`5MO4` use Abl-1b
  numbering (1a + 19), so **T334I is T315I** (315+19=334) and D382N is D363N.
  The JBC 2022 figure the reviewer cites — asciminib decreasing nilotinib's
  binding free energy by **~7 kcal/mol in T315I** versus ~3 in wild-type — is
  therefore the figure for *this* structure. **Verified arithmetic, not assumed**;
  this is the same 1a/1b offset that produced [[TASK-0368]]'s item 1.
- **The others are not worth starting.** KRAS G12C's drugs are covalent, which
  breaks alchemical methods. Cardiac myosin is 704 residues with no clean
  ternary. MYC/MAX is disordered — free-energy methods have nothing to converge
  on.

## The best design element in the whole proposal: dasatinib

**Asciminib enhances nilotinib's inhibition but not dasatinib's.** Same protein,
same allosteric site, two ATP-site ligands — **one couples and one does not.**

That is a **within-system discriminative control**, which is stronger than
anything this register has had. Our positive controls have always been planted
signal in a synthetic setting; this is a real drug system that says in advance
what a working detector must and must not find.

**If the method reproduces the asymmetry, it is measuring something real. If it
gives both the same coupling, it is not.** No further argument needed, and the
result is interpretable either way.

## Staging — Tier 1 is a gate, in E0's spirit

| Tier | What | Cost | Gives |
|---|---|---|---|
| 0 | COREX/EAM (already written) | CPU, hours | coupling in model units, not kcal/mol |
| **1** | **MM/GBSA on 3 systems — gate** | ~10 GPU-days | semi-quantitative; must reproduce the published ~7 kcal/mol |
| 2 | ABFE, nilotinib ± asciminib, 3 replicates | ~2,000 GPU-h | ΔΔG_coupling in kcal/mol |
| 3 | Decomposition + QM correction | variable | **which mechanism carries it** |

**Tier 1 is the gate and nothing downstream is funded without it**: if we cannot
reproduce a published number on the structure it was computed for, the setup is
wrong. Then run dasatinib. **Proceed only if the asymmetry reproduces.**

Signal-to-noise, stated up front: ABFE state of the art is ~1.5–2 kcal/mol RMSE
against a 3–7 kcal/mol target. **Comfortable for T315I, marginal for wild-type.**
That ratio is the whole reason this is attemptable.

## The trap, which is also the deliverable

Asciminib's mechanism is **conformational** — it induces the inactive kinase
conformation, and roughly half the effect (~4 kcal/mol on activation) lives in the
**ensemble shift**, not in contacts with nilotinib.

**A standard ABFE run in a fixed conformation computes the direct part and
silently misses the rest.** It returns a converged number with tight error bars
that is wrong by about a factor of two, and nothing in the output says so.
Capturing the ensemble term needs REST2 or metadynamics over the A-loop and αC
coordinates: 5–10× cost, convergence not guaranteed.

**That decomposition is the deliverable, not the obstacle.** Splitting
ΔΔG_coupling into a conformational term and a direct term answers the
"multiple cogwheels" question quantitatively for one protein — **how much of the
coupling is ensemble redistribution and how much is contact-mediated.** Nobody has
published that split for asciminib; the MD papers computed the total and
attributed it qualitatively.

**And it is the only honest place the electronic question enters.** Compute the
direct term with a fixed-charge force field, then again with polarizable or QM
treatment of the interface. **If they agree, that is a clean negative and the
electronic route is done. If they differ, we have located where classical
mechanics is inadequate — inside a thermodynamically defined quantity rather than
beside one.** That is a materially better framing than [[TASK-0374]]'s `ΔH_AB`,
whose connection to allostery is exactly the assumption E0 taught us not to make.

## Routes to close explicitly, so they do not come back

- **Vibrational / phonon treatment of dynamic allostery.** Fails on a thermal
  argument: at 300 K, kT ≈ 200 cm⁻¹, and the collective modes that carry dynamic
  allostery sit at **1–100 cm⁻¹** — deeply classical, where ENM/NMA is the right
  physics rather than an approximation. The modes that *are* quantum (amide I at
  ~1650 cm⁻¹, X–H stretches) are localised and do not propagate signal. **The most
  plausible-sounding wrong idea in this space**; recorded so the next person to
  suggest it finds the answer already here.
- **Quantum optimisation for conformational search** — already closed
  ([[TASK-0213]]). The thermal argument above is a second, independent reason that
  closure was right.

## Constraints

- **Tier 1 gates everything.** No Tier 2 without a reproduced published number and
  a reproduced dasatinib asymmetry.
- **State the conformational/direct split as the deliverable before running**, not
  after — otherwise a converged-but-wrong total is the natural thing to report.
- Every number here is the external reviewer's and **unverified by us** except the
  1a/1b offset, which this file checked. Per `COMMON.md`'s standing rule, read
  what produces each arm before trusting any of it.
- **No quantum-advantage claim.** The QM step here is a *quality* correction at one
  interface, and if it changes nothing we say so.

## The honest scope consequence

**This stops being a quantum-computing project and becomes computational allostery
with a small, well-placed question about whether electronic structure matters at
one interface.** The Team Lead has already accepted that trade explicitly —
*"This is about allostery. Running a QC just to run it is madness."*

Recorded because a later reader will otherwise assume drift rather than a decision.
