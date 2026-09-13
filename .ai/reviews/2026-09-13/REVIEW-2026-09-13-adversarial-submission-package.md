# Adversarial review — Phase-1 submission package, 2026-09-13

**Reviewed artefact:** `__WORK_IN_PROGRESS__/documentation/SUBMISSION_PACKAGE/` as shipped in
`Quantum_allosteric-scanner-bartosz.zip`.
**Method:** every structural claim re-derived from RCSB directly (mmCIF fetched live), every
shipped CSV/JSON re-parsed, the PDFs re-measured for page and font compliance. Nothing below is
taken from the register on trust; where the register agrees it is noted as corroboration, not as
evidence.
**Relationship to `REVIEW-2026-09-11`:** that review is good and most of its blockers are fixed.
Section F tracks fix status so you do not re-open closed items. Sections A–E are new.

---

## Verdict

The package is unusually honest and the data integrity is genuinely clean — I tried to break the
matrices four ways and could not. The exposure is not sloppiness. It is that **the submission
never states, in plain language, what its own deliverable actually predicted**, and a reviewer who
spends twenty minutes with PyMOL will state it for them. All fifteen submitted residues across the
three scoreable targets are orthosteric-site residues. Zero of three validated pockets are
recovered, at residue level or site level. The proposal reports this as "AUC 0.514–0.548,
`NO_SIGNAL_IN_APO`", which sounds like a coin flip; the truth is worse and more interesting — the
method is *systematically aimed at the wrong site*, which is exactly what §2's own "distance
measure with extra steps" predicts.

Second exposure: the one priority claim the submission stakes its novelty on — the apo vs
stripped-holo gap, "a gap we have found no report of" — is contradicted by a paper your own
register already knows about (CryptoBench). The *magnitude* is plausibly new. The *existence* is
published, in the abstract, in Bioinformatics.

Third exposure, and the one I would fix before anything else: **the public repository that the
whole verifiability argument depends on contains the organisers' private reply verbatim.**

---

## A. Blockers

### A1. Publishing the repo publishes a private organiser communication

`__WORK_IN_PROGRESS__/documentation/2026-08-26-organiser-clarifications.md` is tracked, is
referenced from 16 other tracked files, and carries its own header: *"OFFICIAL. Private response
to Team AuraQu… This is NOT a public update to the Challenge Statement… Other teams may therefore
be working to Table 1 as originally published."*

The Concept Proposal §7 and the Team Profile both direct reviewers to
`github.com/Oussema-t/Quantum_allosteric-scanner` (branch `bartosz`), published 2026-09-15. On that
date, every competing team gains the Cleveland Clinic team's structure suggestions and format
latitude, unedited, because you published them.

That is a Code of Conduct exposure (T&C §10, "harmful to other Participants… or the integrity of
the Challenge") and it is self-inflicted by a team whose entire pitch is procedural rigour. It is
also trivially fixable — three options, in order of preference:

1. Redact the verbatim block before publication, keep your own consequences section, and cite the
   clarification by date rather than content.
2. Ask the organisers for permission to publish it (the channel is live and has answered you four
   times; they may well say yes, and then it is on the record for everyone).
3. Publish the repo minus that file, and state in the Concept Proposal that one primary-source
   document is withheld at the organisers' discretion.

Do **not** leave it as-is on the theory that T&C §7 only binds finalists. That is a reading that
protects you legally and costs you the reputational thing you are trying to buy.

### A2. The repo is not public yet, and publication date == submission deadline

`github.com/Oussema-t/Quantum_allosteric-scanner` returns 404 today. The Concept Proposal says
"published 2026-09-15", which is the Phase-1 deadline itself. Your own package README flags this as
open item 2.

The residual risk is asymmetric and large: §1, §5, §7 and both READMEs all rest on "we made this
checkable rather than asking to be believed". If a reviewer clicks on 15 Sep at 09:00 UTC and gets
a 404, the sentence reads as a bluff. Publish on **2026-09-14**, before you upload, and change the
proposal's wording from a future date to a plain present-tense statement.

### A3. The deliverable's central number is undocumented in the uploaded files

`artefacts/README.md` now explains beautifully that a matrix entry is the time-averaged transition
probability, that rows sum to 1, that the diagonal is the row maximum in ~78% of rows, and that a
naive heatmap will therefore read as diagonal-dominated. I verified all four claims:

| target | N | symmetric | row sums | diag is row max | diag mass |
|---|---:|---|---|---:|---:|
| KRAS_G12C | 170 | yes (1e-9) | 1.000000 ± 1e-6 | 84% | 0.076 |
| BCR_ABL1 | 451 | yes | 1.000000 ± 1e-6 | 80% | 0.066 |
| CARDIAC_MYOSIN | 704 | yes | 1.000000 ± 1e-6 | 78% | 0.047 |
| MYC_MAX | 171 | yes | 1.000000 ± 1e-6 | 85% | 0.076 |

**But `artefacts/` is not uploaded.** The reviewer receives `Connectivity_Matrices.csv`, whose
four-line header says only "value = time-averaged quantum connectivity strength, dimensionless, 6
significant figures". The fix landed in a file nobody scoring you will see. Move those four
sentences into the CSV header comment block — it costs nothing and it is the only place the
methodological content of output 1 is explained.

---

## B. The hit lists — new, and the most damaging thing a reviewer can compute

The 2026-09-11 review said the BCR-ABL1 five are the ATP site. It is worse than that, and it
generalises to all three targets. I derived truth pockets independently (heavy-atom contact <5 Å
to the validation drug in the holo deposition) and measured every submitted residue against them.

### B1. BCR-ABL1 — 1OPL, myristoyl pocket

Truth pocket (MYR contacts in 1OPL chain A, so this target does not even need the holo):
`356, 359, 360, 363, 448, 451, 452, 454, 481, 482, 483, 484, 487, 512, 521, 525, 529`.

| submitted | residue | → myristoyl pocket | → P16, the ATP-site inhibitor |
|---|---|---:|---:|
| #1 | 402 GLY | 25.2 Å | 6.3 Å |
| #2 | 311 GLU | 27.0 Å | 11.5 Å |
| #3 | 310 LYS | 29.6 Å | 9.3 Å |
| #4 | 301 GLU | 32.6 Å | 9.1 Å |
| #5 | 338 THR | 21.4 Å | **4.2 Å** |

Residue 338 in Abl-1b numbering is the gatekeeper (T315 in 1a). You submitted the gatekeeper
threonine as a predicted *allosteric* site on the target whose stated challenge objective is
"identify the distal Myristoyl pocket used by Asciminib to bypass resistance". A CML reviewer will
recognise it on sight.

### B2. KRAS G12C — 4LDJ, switch-II pocket

Truth pocket (sotorasib/MOV contacts in 6OIM): `9-13, 16, 34, 58-63, 68, 69, 72, 92, 95, 96, 99,
100, 103`. Your own `config/targets.yaml` consensus label agrees closely, which is corroboration.

| submitted | residue | → nearest switch-II pocket residue | → GDP/Mg |
|---|---|---:|---:|
| #1 | 31 GLU | 5.8 Å | **3.9 Å** |
| #2 | 122 SER | 11.5 Å | 7.9 Å |
| #3 | 33 ASP | 1.3 Å | **4.3 Å** |
| #4 | 121 PRO | 14.2 Å | 6.8 Å |
| #5 | 29 VAL | 8.3 Å | **4.3 Å** |

Three of five are within 4.5 Å of GDP/Mg — i.e. they are active-site contact residues under your
own `pocket_contact_cutoff`, and `func_ligand: ["GDP"]` exists precisely to exclude that region
from the allosteric label. The algorithm nominated the site the config excludes.

### B3. Cardiac myosin — 8QYP, mavacamten site

Truth pocket (XB2 contacts in 8QYR): `120, 163, 164, 167, 168, 170, 666, 710-713, 717, 721, 722,
770, 774`.

| submitted | residue | → mavacamten pocket | → ADP/VO4/Mg |
|---|---|---:|---:|
| #1 | 682 GLY | 24.8 Å | 9.9 Å |
| #2 | 683 VAL | 24.4 Å | 11.8 Å |
| #3 | 681 PRO | 26.1 Å | 8.4 Å |
| #4 | 680 SER | 26.1 Å | 9.1 Å |
| #5 | 133 VAL | 16.6 Å | 6.6 Å |

### B4. Site level does not rescue it

Using the `top_sites` blocks in the shipped JSON against the same truth sets:

| target | top site size | overlap | Jaccard |
|---|---:|---:|---:|
| KRAS_G12C | 20 | 3 | 0.077 |
| BCR_ABL1 | 56 | 0 | 0.000 |
| CARDIAC_MYOSIN | 85 | 0 | 0.000 |

Under your own register's detection threshold (Jaccard ≥ 0.3), that is 0/3.

### B5. What to do about it

Not hide it — **lead with it**. Four lines in §1, replacing nothing:

> Where the five actually sit. All fifteen submitted residues lie in or beside the orthosteric
> site: 3–8 Å from GDP/Mg in KRAS, 4–12 Å from the ATP-site ligand in BCR-ABL1, 7–12 Å from
> ADP·VO4 in cardiac myosin. None reaches the validated pocket — 21–33 Å away in BCR-ABL1, 17–26 Å
> in cardiac myosin. This is what the proximity confound looks like in a deliverable, and it is the
> most concrete evidence in this proposal for the claim §1 opens with.

This converts your weakest-looking artefact into your strongest exhibit. Right now the AUC framing
*understates* your own finding — 0.514 reads as "no information", whereas "every hit is at the seed"
reads as a measured, reproducible mechanism, which is what it is.

### B6. A probable cause you can name, and fix

`BCR_ABL1.func_ligand` is `["NIL"]` — nilotinib, from the **holo** 5MO4. The **apo** 1OPL's ATP
site is occupied by P16 (a dichlorophenyl pyridopyrimidinone), which is not in that list. So the
orthosteric-exclusion machinery never fires on the input structure, and the walk is free to
nominate the ATP site. Same shape in cardiac myosin: `func_ligand: ["ADP","ATP"]` but 8QYP carries
**ADP + VO4 + Mg**, and VO4 is not listed.

Whether or not you fix the code before the deadline, naming this is worth more than fixing it
silently: it is a concrete, mechanistic defect in your own instrument, found by your own audit
standard, in a proposal whose thesis is that instruments are not audited.

---

## C. The novelty claim is exposed

§1: *"And ligand-removed holo is measurably easier than apo — **a gap we have found no report
of**."* §5 and the Phase-2 table repeat it.

CryptoBench (Pluskal group, *Bioinformatics* 2025; bioRxiv 2024) says in its abstract that current
methods rely on holo conformations for training and evaluation while overlooking apo states, and
that <cite index="13-1">this is particularly problematic for cryptic binding sites, where holo-based assessment yields unrealistic performance expectations</cite>. That is your claim, in an abstract, with a benchmark
built to fix it. Your own register cites CryptoBench thirteen times — as a dataset you chose not
to fetch (TASK-0345, TASK-0346). Nobody appears to have read the paper's argument.

Two consequences, both fixable in one paragraph:

1. **Rescope the claim to the magnitude, not the existence.** "The direction of this gap is known
   (CryptoBench, 2025); what we have found no quantitative measurement of is its size on a matched
   apo/holo cohort with a single detector and truth definition — we measure +0.199 AUC, CI
   [+0.102, +0.296], n = 63 pairs." That claim survives contact with an expert. The current one
   does not, and a reviewer who catches it will discount §1's other four findings by association.
2. **Differentiate the Phase-2 deliverable.** Component (a) is "a certifying cryptic-pocket
   benchmark". CryptoBench and AHoJ-DB already occupy that ground — 4.68 M apo/holo pocket pairs,
   UniProt-grouped, sequence-clustered. Neither is mentioned anywhere in the submission. A reviewer
   asked to fund a benchmark will ask what yours adds. You have a real answer — the blind validity
   rule, the endogenous-ligand audit, the measured detection limit, the distal/cryptic separation —
   but you have to say it against the named incumbent, not against an unnamed field. One sentence
   in the §5 table's "(a)" row.

---

## D. Package and compliance

| check | result |
|---|---|
| Concept Proposal pages | **7** — body ends cleanly on p6, p7 is "Appendix — References". Within 6 + 3, but a screener counting pages of the file labelled "Concept Proposal" sees 7 |
| Concept Proposal font | A4, 10.5 pt body — compliant |
| Other three PDFs | US Letter, 9 pt in tables (14–22% of glyphs) |
| Total size | ~14.1 MB vs 20 MB cap |
| Build sentinel | removed ✓ |
| Repo link | 404 as of today (see A2) |

- **Page-size mismatch.** File 1 is A4, files 2/3/5 are Letter. Cosmetic, but it is the first thing
  visible when a reviewer flips between them.
- **The 6-page limit and the appendix.** Add one line at the end of p6 — "References: Appendix,
  p7" — so a screener counting pages sees an intentional structure rather than an overflow.
- **`Connectivity_Matrices.csv` is not a CSV a naive reader can open.** Four `#` comment lines
  precede the header, so `pd.read_csv(...)` without `comment='#'` fails. Either drop the comments
  into a header row's trailing field or accept the breakage knowingly — but note that the
  organisers' own answer was "formats accessible with conventional software", and a `#` preamble is
  not that.
- **The "upper triangle only" claim is false.** 7,304 of the 14,706 MYC_MAX rows have
  `residue_i > residue_j`, because chain A numbers 897–984 and chain B numbers 202–284, so array
  order and residue order disagree. Each unordered pair still appears exactly once (I checked: zero
  duplicates across all four targets), so the file is correct — but the header comment "only i <= j
  is listed" and the README's "Upper triangle only" are both wrong, and a reviewer reconstructing
  the matrix by assuming `i <= j` will silently mis-place those rows. Reword to "each unordered
  pair listed once".
- **No `chain` column in the matrix CSV.** `hit_list_all_targets.csv` gained one; the matrix did
  not. MYC_MAX is the two-chain case, and it survives only because the numbering ranges happen not
  to collide. Your own register knows fpocket residue numbers are chain-agnostic — this is the same
  trap one level up.
- **Reconstruction integrity: clean.** The combined CSV reproduces all four per-target artefact
  matrices exactly (max |diff| = 0.0 over 2,000 sampled entries per target), all four are symmetric
  to 1e-9, row counts match the README's 379,327 exactly. This part is airtight and you should say
  so in the README in one line, because it is checkable and most submissions will not survive it.

---

## E. Internal contradictions a reviewer will hit

1. **"We followed it in each case" is contradicted by the table underneath it.** §1: *"Their reply
   of 2026-08-26 answered three points, and we followed it in each case."* The KRAS row then says
   the organisers suggested 8S8C and you rejected it. (I verified you were right to: 8S8C carries
   A1H5U/MK-1084 and is holo.) Being right and describing yourself as compliant when you were not
   is the worst combination. Rewrite: "answered three points; we adopted two and, on the third,
   checked the suggested structure, found it holo, and substituted a verified apo instead."
2. **Deviation count disagrees between files.** `03_Problem_Statement_Selection.md` says "Four
   structure choices deviate from Table 1". The Concept Proposal says "Two rows above are
   deviations, one a retention". The actual count of deviating structures is three: 4LDJ, 8QYP,
   8QYR. Doc 03 also claims the reason is "in Section 1 of the Concept Proposal" — it now is, so
   just fix the number.
3. **Your own inputs are not ligand-free, and you don't say so.** §1's fourth finding is *"'Apo'
   does not mean ligand-free"*. The proposal then labels 4LDJ "(apo)" — GDP + Mg — and 8QYP
   "(apo)" — **ADP + VO4 + Mg**, a transition-state mimic — disclosing only 1OPL's myristate, and
   omitting 1OPL's second ligand entirely. Your register (TASK-0278, "our apo structures are not
   apo") already found all of this. You are under-reporting your own strongest evidence, and you
   are doing it in the one section where a reviewer is primed to check. One sentence:
   *"Our own three inputs are no exception: 4LDJ carries GDP·Mg, 8QYP carries ADP·VO₄·Mg, and 1OPL
   carries both myristate and an ATP-site inhibitor. All three are apo only with respect to the
   scored pocket — which is the strongest form of the point."*
4. **Cardiac myosin is bovine and the Concept Proposal never says so.** 8QYP/8QYR are *Bos taurus*
   Myosin-7 (X-ray, 2.76 Å / 1.80 Å). The artefacts README discloses it; the scored document does
   not. This matters because your stated objection to Table 1's 6C1H is partly a species objection
   (rat myosin-Ib on rabbit actin). The defence is easy and strong — bovine β-cardiac myosin is a
   near-identical orthologue of the human target, whereas myosin-Ib is a different class entirely —
   but you have to make it, or the asymmetry reads as convenient.
5. **The cardiac PDB code is missing from the five-guess table** in the Concept Proposal. KRAS and
   BCR-ABL1 carry theirs. Flagged on 2026-09-11, still open.
6. **`MYC_MAX` config says `allosteric_pocket_exists: false`.** You ship a top-5 for a target your
   own configuration asserts has no folded-state pocket, and the fpocket druggability scores you
   report (max 0.161) sit well under your own 0.5 bar. The "unverified" label is honest but
   incomplete. Say the harder thing: *"Our own configuration records that this target has no
   folded-state allosteric pocket; we supply the five because the challenge requires them, and we
   report that our best candidate site scores 0.161 druggability against our own 0.5 threshold."*
   That is a better answer to §6's "theoretical docking viability" than the current one.
7. **The hit list is not reproducible from the shipped matrix.** §6 claims "a hit list cannot
   disagree with the matrix it came from". I scanned every single-residue seed row of all four
   matrices, plus GDP-contact, P-loop and switch-II seed sets for KRAS, under both seed-inclusive
   and seed-exclusive ranking. None reproduces any shipped top-5. The likely explanation is benign —
   the matrix is the default operator, the hit list is `H_new` with the five potentials — but the
   claim as written is unverifiable by the reader and therefore worth less than the sentence costs.
   Either ship the seed residue set and the operator identity in the CSV header, or soften the claim
   to "emitted in one pass from one runner" without the falsifiable-sounding "cannot disagree".

---

## F. Fix status against `REVIEW-2026-09-11`

| # | item | status |
|---|---|---|
| 1 | repo not public | **open** — see A2 |
| 2 | body spills to p7 | fixed — body ends on p6 |
| 3 | `artefacts/README` labels 8QYR "(apo)" | fixed, with an explicit correction note |
| 4 | cardiac substitution reason absent; Table-1 pair unnamed | fixed in §1; **holo codes 6OIM/5MO4 still absent**, cardiac code still missing from the five-guess table |
| 5 | Team Profile cites nonexistent "Appendix B" | fixed |
| 6 | report.txt contradicts CP ("genuinely helps", "Confidence: high") | fixed — caveats appended, MYC now "unverified" |
| 7 | KRAS "VALID" computed on 4OBE | re-run on 4LDJ; `targets.yaml` records the flip to `NO_SIGNAL_IN_APO`, AUC 0.557→0.514 |
| 8 | coupled search CLOSED vs "survives our own screening" | **open** — §2 still says one route "survives", register row says closed |
| 9 | "169–704 qubits" | fixed → 170–704 |
| 10 | log-encoding qubit count | **open** — §3 still asserts one-qubit-per-residue as "the convention behind every number" without stating the binary-encoding alternative or why unary is kept |
| 11 | apo-draw sensitivity omitted | fixed — now in `Solution_Outputs.md` §2 (0.408–0.595, cardiac swap moved AUC 0.27) |
| 12 | fpocket beats the walk | partially — now in file 5 with re-run numbers (0.860/0.420/0.535), **still absent from the scored Concept Proposal** |
| 13 | `NO_SIGNAL_IN_APO` underpowered | fixed — paired score−floor bootstrap with detection limits now shipped |
| 15 | "0.4960 — below chance" | fixed → "at chance" |
| 19 | BCR-ABL1 five are the ATP site | **open** — see §B, and it is the biggest open item |
| 21 | cardiac five are one cluster | **open** |
| 22 | c-Myc numbering not UniProt | partially — chain column added to the hit CSV, UniProt mapping still absent |
| 23 | matrix formula undocumented | fixed in `artefacts/README` — but that file is not uploaded (A3) |
| 24 | seed not shipped, hit list irreproducible | **open** — independently confirmed, §E7 |
| 26 | README size inconsistency | fixed (~14 MB, matches) |
| 27 | "we followed it in each case" | **open** — §E1 |
| 32 | build sentinel in text layer | fixed |
| 33 | "since 2010" / "Gemini 2.6" | fixed |

---

## G. Verified correct — do not spend time re-checking

Every structural claim in §1 that I could test is right, and several are sharper than the proposal
lets on:

- **4OBE is wild-type.** Chain A and chain B residue 12 are both GLY. The mandated KRAS G12C input
  is not G12C. This is a genuine defect in the challenge's own Table 1 and you found it.
- **4LDJ is genuinely G12C** (residue 12 = CYS), 1.15 Å, single chain, 170 residues numbered 0–169
  with no gaps — so "KRAS is the trap, its two columns coincide" is correct and worth keeping.
- **8S8C is holo** (MK-1084/A1H5U bound), so rejecting the organisers' suggestion was right.
- **5TBY is a homology model at 20.0 Å resolution**, deposited as EM. Exactly as described.
- **6C1H is rabbit α-skeletal actin with rat myosin-Ib, carrying ADP, no mavacamten.** Exactly as
  described.
- **1OPL chain A is 81–531, 451 residues, no gaps**, matching the shipped N exactly; it does carry
  myristate.
- **8QYP chain A is 32–780, 704 residues, 7 gaps**, matching the shipped N and the stated
  index↔residue offsets exactly.
- **1NKP chains A (897–984) + B (202–284) = 171**, matching the shipped N.
- Matrix integrity, symmetry, row sums, row counts, and hit-list/CSV/JSON/PDF agreement: all clean.

Taken together, **every one of Table 1's three mandated pairs has a verifiable defect** — wrong
genotype, double-liganded apo, and a 20 Å homology model paired with the wrong protein. The
proposal now says this. It should say it as one sentence in exactly that form, because it is the
single most defensible claim in the document and it is currently spread across a table and a
footnote.

---

## H. Rubric exposure, and the one change that moves the score

Weighted criteria: Relevance 25 · Technical 25 · Feasibility 20 · Validation 15 · Team 10 · Hybrid 5.

Feasibility, Validation, Team and Hybrid are strong-to-exceptional and largely self-defending. The
risk is concentrated in the two 25% criteria, and it is the same risk twice:

**Relevance (25%).** Challenge §4.1: *"The single most important objective is to maximize the
predictive accuracy of the quantum algorithm in identifying experimentally validated allosteric
sites."* You report accuracy indistinguishable from chance and propose an instrument instead. A
sympathetic reviewer scores that 3 for intellectual honesty; an unsympathetic one scores 2 for
answering a different question. What moves it to 4 is not softening the null — it is making the
null *decision-useful to Cleveland Clinic specifically*. §4's "go/no-go instrument applied before
committing chemistry to a predicted site" is the right argument and it is currently two sentences
in the weakest-positioned section. It should be the close of §1: what a computational biology unit
does differently on Monday morning because of your result.

**Technical (25%).** Challenge §4.1 also says *"Participants must build a quantum circuit."* §5
Constraint 2 penalises circuits that cannot run on near-term hardware. You transpiled against a
real IBM calibration snapshot and got `FAULT_TOLERANT_ONLY` at both resolutions — which is a
measurement, not a failure, but the proposal reports only analytic gate counts and never says you
built and transpiled the circuit. One clause ("we built and transpiled the circuit against
FakeSherbrooke: 538–1486 two-qubit gates at coarse resolution, fidelity ≈0.015") converts a missing
§4.1 requirement into a satisfied one. Similarly, §4.2's noise-resilience requirement is satisfied
in your register (the pre-registered robustness hypothesis, falsified) and absent from the proposal.
These are free points.

The structural tension you cannot fully resolve in Phase 1: **the proposed Phase 2 contains no
quantum execution at all.** That is honest and defensible, and it will still cost you on both 25%
criteria in a quantum challenge. If you can afford the lines, a small pre-registered Braket/Classiq
arm — framed explicitly as a hardware noise measurement and a first test subject for the
instrument, not as an advantage claim — buys credibility on Technical and Feasibility at almost no
scientific cost, because you already know it will not find signal.

---

## I. Priority order

1. Redact or clear the organiser reply before publishing the repo (A1).
2. Publish the repo 2026-09-14 and change the proposal's wording to present tense (A2).
3. Add §B5's four-line "where the five actually sit" paragraph to §1 (B).
4. Rescope the apo/stripped-holo priority claim and name CryptoBench in the Phase-2 (a) row (C).
5. Fix "we followed it in each case" and the four-vs-three deviation count (E1, E2).
6. Disclose your own inputs' ligands and the bovine species in the Concept Proposal (E3, E4).
7. Move the matrix-entry explanation into the uploaded CSV header (A3); fix the "upper triangle"
   wording (D).
8. Add the "we built and transpiled the circuit" clause and one noise-resilience sentence (H).
