# TASK-0377 — Compute the thing allostery is actually defined as: ΔΔG coupling on BCR-ABL1, with dasatinib as the discriminative control

- Status: TODO — **UNBLOCKED 2026-09-12 (Team Lead). The 2026-09-15 hold is lifted. First step is the hardware probe below, not Tier 1.**
- Owner: **Architect/Planner** to scope (done); Implementer with GPU access to run
- Priority: **Phase-2 headline candidate. Cleared to start — probe first.**
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

## Scoped, and one premise corrected (2026-09-12, Architect)

Picked up per direct instruction. **Environment check first**: this machine has
no GPU and no MD engine at all (`nvidia-smi`, `gmx`, `sander`, `pmemd.cuda`,
`openmm` all absent) — confirms the task's own "Implementer with **GPU access**"
framing is load-bearing, not a formality. Tier 1+ cannot run here under any
circumstance; that is a resourcing question (where does GPU time come from),
not a blocker to scoping. Respecting **"Not before 2026-09-15"** literally —
nothing below was executed, only verified.

**`5MO4`/the +19 offset — independently corroborated, not just re-derived.**
`targets.yaml:140-182` already carries this exact fact from **TASK-0003,
2026-07-06** — RCSB-reconfirmed title, AY7/NIL ligand identity, and the same
+19 arithmetic (334-315=19, 382-363=19) this filing re-derived from scratch.
Two independent checks agree. Solid.

**The JBC 2022 paper itself, read directly (PMC9386466) — one correction that
changes the Tier-1 gate, not the target choice:**

1. **"Nobody has published that split" is not quite right.** The paper
   *does* report both pieces, quantitatively: the conformational/activation
   term (metadynamics, inactive state stabilized **3.7 ± 0.5 kcal/mol** by
   asciminib) and the direct term (**2.7 kcal/mol WT, 6.7 kcal/mol T315I** —
   the task's "~3"/"~7" round these). What is genuinely missing is a
   **self-consistent decomposition from one coherent method with propagated
   error bars** — the paper computed the two pieces with two *different*
   methods (metadynamics; static-cluster DFT) and did not sum or
   cross-validate them. **The deliverable narrows to that, not to a wholly
   unpublished split.** Say this precisely in any write-up — the previous
   framing overclaims what is new here.
2. **The "~7 kcal/mol published number" is a small-cluster DFT estimate, not
   an experimental or full-system value.** Method: "only those residues that
   form hydrogen bonds... with nilotinib," M06/def2-TZVP, on a truncated
   cluster — not the full binding interface, not MM/GBSA, not an alchemical
   calculation of any kind. **Tier 1's own gate — "MM/GBSA... must reproduce
   the published ~7 kcal/mol" — is comparing two different levels of theory
   on two different system definitions, not replicating a method.**
   Agreement would be reassuring; disagreement would not by itself mean the
   MM/GBSA setup is wrong, only that a small H-bond-only DFT cluster and a
   full-system classical free-energy calculation can legitimately differ.
   State this explicitly before running Tier 1, so a miss is diagnosed
   correctly rather than treated as a failed gate.
3. **No direct experimental ΔΔG (Kd/ITC/SPR) exists anywhere in this
   paper for calibration.** The only experimental numbers are cell-based
   IC50 (Table 1: K562 7.0→1.5 nM, KCL-22 9.4→2.3 nM, KCL-22NR 14.6→6.9 nM,
   nilotinib alone vs. + asciminib) — a phenotypic readout confounded by
   permeability, efflux and target occupancy nonlinearity, not a binding
   free energy. Converting these fold-changes naively via RT·ln(fold) at
   298 K (RT ≈ 0.593 kcal/mol) gives **≈0.4–0.9 kcal/mol**, an order of
   magnitude below the 3–7 kcal/mol claimed — expected, given how many
   confounds sit between cellular potency and isolated binding affinity, but
   **worth stating up front so a large gap here is not mistaken for a
   detector failure later.** There is no clean experimental ground truth for
   this system; both the DFT-cluster number and whatever Tier 1/2 produce
   are simulation estimates being cross-checked against each other, not
   against measurement.

**Consequence for the gate, not the plan**: Tier 1 remains the right first
step and BCR-ABL1/dasatinib remains the right system — nothing here changes
the target or the staging. What changes is the **success criterion's own
honesty**: "reproduces the published DFT-cluster estimate" is weaker
evidence than the original framing implied, and the write-up must say so
rather than present a Tier-1 match as validation against a firm number.

### TODO, added

- [ ] State the corrected framing (item 1 above) in whatever document first
      describes this task's deliverable — do not ship "nobody has published
      this."
- [ ] Tier 1's own report must show the MM/GBSA number **alongside** the
      DFT-cluster number and the IC50-derived rough estimate, with the
      difference in method/system size stated plainly, not just a pass/fail
      against "~7 kcal/mol."
- [ ] Resourcing: identify where GPU time for Tier 1 (~10 GPU-days) comes
      from — this environment has none. A question for Bartosz, not an
      assumption, same pattern as [[TASK-0374]]'s IBM-access question.


---

## UNBLOCKED 2026-09-12 — and the first step is a hardware probe, not Tier 1

**The 2026-09-15 hold is lifted (Team Lead).** It was there to protect the
submission's remaining days, and the submission is going out tonight.

The Architect's environment check already answered half the resourcing question:
**this machine has no GPU and no MD engine at all** (`nvidia-smi`, `gmx`,
`sander`, `pmemd.cuda`, `openmm` all absent). Their own open TODO asks where
~10 GPU-days comes from. **The Team Lead has a desktop with a graphics card**, so
the answer is measurable rather than guessable.

### The probe — scoped as a measurement, not a smoke test

**Owner: Architect/Planner. Run on both machines: this one, then the Team Lead's
desktop.**

The point is a **like-for-like effort comparison**, so the probe has to be the
same work on both boxes, and it has to record its own numbers to an artifact.
Two machines compared from memory is not a comparison.

**In scope:**

1. **Inventory, and it must not require the engine to be present.** CPU model,
   physical/logical cores, RAM, OS/arch; GPU model, VRAM, driver and CUDA/Metal
   version; and for each of `openmm`, `gmx`, `pmemd.cuda`, `sander`: present or
   absent, and the version if present. **On this machine every engine is absent
   and the probe must still complete and say so** — a probe that only works where
   the answer is already good measures nothing.
2. **One fixed benchmark, identical on both.** A single solvated-protein system
   with a **fixed step count** (not a fixed wall time), reporting **ns/day** and
   total wall seconds. Use the engine's own published benchmark system if one is
   available for the installed version, so the number is comparable to something
   outside this project too.
3. **Scale the estimate, don't assert it.** From measured ns/day, derive the wall
   time Tier 1 (~10 GPU-days on the reference hardware) and Tier 2 (~2,000 GPU-h)
   would actually take **on each machine**, and state the arithmetic. This is the
   number the resourcing decision needs.
4. **Write it to an artifact**, one JSON per machine under
   `results/tasks/0377_hardware_probe/`, with a hostname/arch key so the two are
   distinguishable, plus a short comparison table in the Done section.

**Out of scope:** any ΔΔG calculation. **The probe must not attempt Tier 0/1/2
work** — it measures capacity, and mixing the two makes a slow probe look like a
failed gate.

**Constraints:**

- **The probe must degrade, never fail.** Missing engine, missing GPU, missing
  driver are all *results*. Report them; do not raise.
- **Do not install an MD engine on this machine as part of the probe.** If Tier 1
  needs one, that is a deliberate dependency decision, not a side effect of
  benchmarking.
- Record **arch** explicitly (this machine has already produced one
  arm64/x86_64 breakage this week, [[TASK-0375]]), and note whether Python was
  running under translation.

**Success criterion:** a table with both machines side by side, the measured
ns/day for each, and the derived Tier-1/Tier-2 wall times — enough to answer
*"where does the GPU time come from"* with a number instead of a guess. **A
result showing the desktop is also insufficient is a perfectly good outcome**, and
is better learned now than after Tier 1 is committed to.

### One thing the probe does not settle

The Architect's finding that **no experimental ΔΔG exists for this system** — only
cell IC50s, which convert to ≈0.4–0.9 kcal/mol against a 3–7 kcal/mol claim —
stands regardless of hardware. **Both the DFT-cluster number and whatever Tier 1/2
produce are simulation estimates cross-checked against each other, not against
measurement.** Their correction is right and the write-up must carry it. Compute
capacity does not create ground truth.

### Probe, machine 1 of 2 (2026-09-12, Architect) — this machine

Script: `scripts/task0377_hardware_probe.py`, stdlib-only per the probe's own
constraint (must run unmodified on a machine with nothing installed). Output:
`results/tasks/0377_hardware_probe/Bartoszs-MacBook-Pro_arm64.json`.

| | this machine |
|---|---|
| Host / arch | Bartoszs-MacBook-Pro / arm64 |
| CPU | Apple M2 Pro, 10 physical / 10 logical cores |
| RAM | 17.18 GB |
| GPU | Apple M2 Pro integrated — **no CUDA, ever**; `pmemd.cuda`/GROMACS-CUDA structurally cannot use it regardless of what gets installed |
| `openmm` / `gmx` / `pmemd.cuda` / `sander` | all **absent** |
| Benchmark | not run — no engine present |
| ns/day, Tier-1/2 wall time | not derivable here |

**Degraded correctly, per spec**: every check completed and reported absence
rather than raising, matching the "must degrade, never fail" constraint.

**One genuine surprise, disclosed rather than resolved in either direction**:
the probe's own Rosetta-translation check (`sysctl.proc_translated`, the
same class of arch issue [[TASK-0375]] hit) returned **inconsistent answers
depending on how it was invoked** — "1" (translated) when called via this
script's `subprocess.run`, but "0" (native) when the identical command was
typed directly in an interactive shell in the same session, and
`platform.machine()` reported `arm64` throughout (genuine Rosetta
translation would show `x86_64`). Most likely an artifact of how this
specific coding-agent sandbox spawns subprocesses, not a fact about the
machine a human sees at a real terminal — recorded as a caveat in the JSON
(`cpu.running_under_translation_caveat`) rather than picking one answer.
**A human should re-check this by hand outside any agent sandbox before it
is trusted either way** — do not cite `running_under_translation` from this
JSON as settled.

**Answers zero of the resourcing question by itself** — this machine was
never going to be the answer; it establishes the honest baseline (nothing
here, and structurally never can be for CUDA-only engines) that the
desktop's probe run is compared against. **Waiting on the Team Lead's
desktop run to complete the comparison** — same script, same command,
`../.venv/bin/python3 -u scripts/task0377_hardware_probe.py` (or plain
`python3`, no venv packages required), output lands in the same
`results/tasks/0377_hardware_probe/` directory keyed by hostname so both
are distinguishable without collision.
