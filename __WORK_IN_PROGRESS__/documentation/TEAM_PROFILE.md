# Team Profile — Team AuraQu

*Guidelines §4.1 — a separate submission component, not part of the 6-page
Concept Proposal, and not counted against its page limit. §4.3 item 7 (Team
Capability) is answered inside the Concept Proposal itself, briefly; this
document is the reference material behind that argument.*

## Team name and lead contact

**Team name**: AuraQu

**Lead contact**: **MISSING — flagged, not invented.** §4.1 requires lead
contact details and none exist anywhere in this submission set today. This
needs the repo owner's own name/email/affiliation before the portal upload;
it cannot be supplied by this task.

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

**Bartosz Chmura** — PhD, molecular photophysics; 14 years software quality
assurance. Role on this project: scope and narrative decisions, and the
verification methodology (separation of the party that builds from the
party that verifies, negative controls, reproducibility discipline) applied
throughout the register cited in the Concept Proposal.
**Prior quantum-computing experience**: none claimed here; his contribution
is the QA/verification discipline, not quantum-domain expertise — stated
plainly rather than implied otherwise.

## How the team worked — elaboration on the Concept Proposal's short disclosure

*The Concept Proposal (§7) discloses this briefly, as required there. This
section is the full version, since a Quantum *and* AI challenge that
permits AI involvement should not have that involvement minimised or
under-documented.*

This is a Quantum *and AI* challenge that permits AI involvement, so
treating our own use of it as something to minimise would be incoherent.
The register behind this submission — 359 task files, 328 done, 580
commits as of `ffcfaca` (2026-09-07) — is too large for one person to
review unaided, and we would rather say so than pretend to a reading
nobody performs. The traces that matter — human-in-the-loop decisions,
team disagreement, how conflicts were resolved — are visible in it, which
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
| Repository | Claude Sonnet | Implementers, Toolsmith, Architect/Planner |
| Repository | Claude Opus | Code Reviewer |
| Project | Claude Opus | **Adversarial Reviewer / Critic** |
| Project | Google Gemini 2.6 Pro | Critic / Reviewer / Researcher / Brainstormer |

Four of the five retractions in the Concept Proposal's Appendix B were
produced by the adversarial reviewer role attacking work the implementing
role had just completed and believed correct — catching the proximity
confound, the missing baseline comparison, a symmetry category error, and a
miscalibrated test.

| Artefact | What is in it |
|---|---|
| **Repository** `github.com/Oussema-t/Quantum_allosteric-scanner` | The scanner, the pipeline, the analysis scripts behind every number in the Concept Proposal. |
| **Branch `bartosz`** | 359 task files · 328 done · 580 commits (as of `ffcfaca`, 2026-09-07) · the full falsification record |

---

*This document is §4.1's own component. It is not the Concept Proposal and
is not subject to its 6-page limit. Content parity with the Concept
Proposal's own §7 is not required — this is the fuller version that §7's
short capability argument points to, not a duplicate of it.*
