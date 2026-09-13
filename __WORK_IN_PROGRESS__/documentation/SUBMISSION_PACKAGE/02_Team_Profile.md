# Team Profile — Team AuraQu

## Team name and lead contact

**Team name**: AuraQu

**Lead contact**: **Bartosz Chmura**. chmura.quantum@gmail.com, Unaffiliated

## Team members — description, expertise, and prior quantum experience

**Oussema Turki** — Quantum algorithms.
M.Sc. Quantum Computing Technology (Universidad Politécnica de Madrid);
M.Sc. Quantum Engineering in progress (Leibniz Universität Hannover).
Thesis benchmarked VQE and quantum annealing against DFT/CASSCF/HF
references. Toolset: Qiskit, PennyLane, QUBO formulation, hybrid QML. Two
years simulation engineering at Volkswagen R&D. Competition record: 1st
place, PushQuantum; winner, OPUS Challenge; 2nd place, NYUAD; 3rd place,
Braunschweig; honourable mention, IBM Quantum Challenge.
**Prior quantum-computing experience**: direct and extensive — this is his
primary discipline, evidenced by the degree, thesis, and competition record
above.

**Berke Turkaydin** — Computational biophysics / structural chemistry.
PhD, Leibniz-Forschungsinstitut für Molekulare Pharmakologie (FMP) Berlin /
TU Berlin. K2P potassium channel (TREK-2) activation and inhibition via
all-atom molecular dynamics and enhanced sampling (metadynamics, OneOPES),
tracing allosteric coupling from the selectivity filter through the M4
helix to the fenestration sites. Two first-author papers, one currently
under review at *Nature Communications*. Toolset: GROMACS, AMBER, PLUMED,
AlphaFold, RFdiffusion, ProteinMPNN, HPC.
**Prior quantum-computing experience**: none. **Prior experience with the
specific problem domain**: direct and extensive — allosteric-site biology
and structural validity are his research area; this is the expertise behind
every biological correction and target-classification judgement in the
Concept Proposal.

**Bartosz Chmura** — Molecular quantum dynamics / photophysics; software
quality assurance.
PhD, Institute of Physics, Polish Academy of Sciences, Warsaw (2005–2010):
time-dependent quantum wave-packet dynamics of photochemical reactions,
including conical-intersection dynamics of the water dimer (*J. Chem.
Phys.* 2009) and oxo-hydroxy phototautomerism (*J. Phys. Chem. A* 2008).
Postdoc (Wissenschaftlicher Mitarbeiter), Technische Universität München,
Garching (2010–2012): ab-initio quantum chemistry (Molpro, Molcas,
Gaussian, Turbomole) and C++ molecular-quantum-dynamics code for
open-shell systems. Author of a solo quant-ph preprint, *"The Geometry of
Clifford Algorithms: Bernstein-Vazirani as Classical Computation in a
Rotated Basis"* (arXiv:2603.12127, 2026). Since 2012: 14 years in
software quality assurance, currently leading QA engineering and test
automation at Appsfactory (Munich).
**Prior quantum-computing experience**: a PhD and postdoc in quantum
dynamics / ab-initio quantum chemistry (not quantum information), plus
one solo quant-ph preprint. Project role: QA/verification
discipline (separation of the party that builds from the party that
verifies, negative controls, reproducibility discipline) applied
throughout the register cited in the Concept Proposal.

## How the team worked — elaboration on the Concept Proposal's short disclosure

Apart from the human-contributor interactions according to the roles, 
most of the investigation regarding building complete notebooks, operators, 
hamiltonians, observables, building visualisation tools, main effort of analysing
CTQW in various settings are attributable to Oussema; 
the work on validating protein structures, explaining the apo/holo structure 
types, pockets, ortho-/allostery as mechanism, are attributable to Berke; 
the construction of the AI-scaffolding, reviewing process, unit testing, 
formulating and verifying the hypotheses, positive/negative checks, 
null formulation, are attributable to Bartosz.   

*The Concept Proposal (§7) discloses this briefly. This
section is the full version, since a Quantum *and* AI challenge that
permits AI involvement should not have that involvement minimised or
under-documented.*

This is a Quantum *and AI* challenge that permits AI involvement, so
treating our own use of it as something to minimise would be incoherent.
The register behind this submission — 350+ task files, 580+
commits as of `ffcfaca` (2026-09-07) — is too large for one person to
review unaided, and we would rather say so than pretend to a reading
nobody performs. The traces that matter — human-in-the-loop decisions,
team discussions, hypothesis tensions, and how debates were verified and resolved, how conflicts were resolved — are visible in it, which
is the evidence for every capability claim in the Concept Proposal. What
should be judged is whether the verification was real, not how it was
produced, and we have made that checkable by publishing the working
repository rather than asking to be believed.

The register's tasks were produced by a role-separated agent workflow,
with the reviewing role deliberately assigned to a *different model* from
the implementing one, so a defect and its audit do not share a failure
mode:

| Layer | Model | Roles |
|---|---|---|
| Repository | Claude Sonnet 5 | Implementers, Toolsmith, Architect/Planner |
| Repository | Claude Opus 5 | Code Reviewer |
| Project | Claude Opus 5 | **Adversarial Reviewers / Critics** |
| Project | Google Gemini 3.X Pro / 3.X Flash | Critics / Reviewers / Researchers / Brainstormers |

Four of the five retractions the Concept Proposal reports were
produced by the adversarial reviewer role attacking work the implementing
role had just completed and believed correct — catching the proximity
confound, the missing baseline comparison, a symmetry category error, and a
miscalibrated test.

| Artefact | What is in it |
|---|---|
| **Repository** `github.com/Oussema-t/Quantum_allosteric-scanner` | The scanner, the pipeline, the analysis scripts behind every number in the Concept Proposal. |
| **Branch `bartosz`** | 400 task files · 374 done · 687 commits (as of `6ccc5f7`, 2026-09-13) · the full falsification record, including every retraction |
| **Branch `allosteric`** | The seeded-CTQW pipeline and its ensemble sweep: 13 Hamiltonians × 17 scores over 1022 proteins, thirteen classical baselines scored on identical residues at 630-protein scale, and two random-forest models predicting walk configuration from graph topology |
