# Message to the allosteric branch — 2026-09-09

*Draft. Not sent. Written after the tau-scan completed; supersedes the "tau unresolved"
row in the side-by-side comparison.*

---

Your Part 5 item 2 is done — we ran it, and the answer is not the one either of us
expected.

## The tau question is closed on our cohort

We scanned `2·Re⟨r|e^{−iHτ}|a⟩` across **eleven delays spanning five orders of
magnitude**, from deep short-delay (τ ≈ 0.2, interference fully alive) through
convergence (τ ≈ 21000), each set as a fraction of the Hamiltonian's own spectral-gap
timescale. Same 108-structure cohort, same harness, anchored by exact reproduction of
our previously committed numbers to 5 decimals.

**Signed observable — the one your claim reports — 0 of 11 significant.**

| τ (median) | raw AUC | ρ vs proximity | residualised | cluster-p |
|---|---|---|---|---|
| 0.21 | 0.4896 | −0.018 | 0.4928 | 0.619 |
| 2.10 | 0.4894 | 0.015 | 0.4922 | 0.567 |
| 20.99 | 0.4758 | 0.021 | 0.4803 | 0.238 |
| 209.92 | 0.5031 | −0.016 | 0.5018 | 0.919 |
| 2099 | 0.5002 | −0.009 | 0.4997 | 0.984 |
| 20992 | 0.5027 | 0.008 | 0.5007 | 0.968 |

Full range of cluster-p across all eleven: **0.24 to 0.98**. Flat. Not a near-miss.

This also closes our own earlier objection against ourselves: our first attempt tested at
one delay that turned out to be a convergence window used as a point delay — the wrong
place to look. The scan fixes that, and the short-delay end is now covered properly.

**Separately, the unsigned magnitude `|O(r)|` behaves exactly as physics predicts**, which
is a useful check that the implementation is sound: its correlation with proximity falls
monotonically **0.92 → 0.24** as τ grows. At short delay the magnitude simply *is* a
distance measure — raw AUC 0.605, residualised **0.5000**, collapsing to exactly chance
once distance is removed. The magnitude is distance; the phase is noise.

## What this does and does not say about your +0.107

It does **not** refute your number. Different cohort, different candidate set, different
labels.

What it does say is sharper than a refutation, and it is why we are asking rather than
concluding:

> The observable carries no information on our cohort at any delay. If +0.107 is real, it
> is a property of **your cohort or your pipeline** — not of the observable itself.

That changes what the next experiment should be, and it is on your side of the line, not
ours.

## Three requests

**1. Run our scan on your 630.** We will send the script — it is validated and anchored to
reproduce known numbers before it reports anything new. This is now the only experiment
that discriminates between "the observable does something" and "your cohort does
something", and you have the data. We are not asking you to rebuild anything.

**2. Two rows in your own document sit oddly together, and we would like to know which cut
each refers to.**

- §1.4: *CAS0002 dominance — 28 of 91 distal structures are one protein. Without it CTQW
  0.617 → 0.501.*
- §1.5: *two-source phase interference … **survives dropping CAS0002**.*

If one family carries the pipeline result but not the two-source result, that is
interesting and worth stating explicitly. If they are different cuts, the document should
say so, because a reviewer will read them together.

**3. What τ did you use, and how was it chosen?** It is not stated anywhere in the
comparison. If it came from a rule, our scan almost certainly covers it and we can point
at the exact row. If it was selected, that is worth knowing too — and is not a
disqualification, only something to declare.

## Agreeing with your own flagged gap

Your note that the two-source score was never tested against **closeness centrality** is
the single most valuable line in the update, and we would put it above everything else on
your side. Closeness already beats the pipeline at family-level P@5 (29 vs 20) while being
unseeded and parameter-free. A reviewer will ask for that comparison first, and "beats the
pipeline" is not the same claim as "beats the best baseline".

## One correction we owe you

We proposed to you earlier that a sign-inverted finite-delay amplitude might be a distance
proxy in disguise. **That was wrong and our own data killed it** — the signed arm's
correlation with proximity is −0.016 at every delay we scanned. The distance effect is
real but lives on the unsigned magnitude, which is not your observable. Withdrawn.

We also accept, without reservation, that your 53/53 unanimous sign inversion answers the
per-fold sign-fishing objection. That one is closed and should not come back.

## On framing — we think we now agree

Your formulation — *"not 'we found quantum advantage', but 'we measured parity, and
identified one phase-sensitive route that exceeds it'"* — was right when written. After the
scan, the honest version on our data is narrower:

> We measured parity, tested the one phase-sensitive route that could have exceeded it
> across its full delay range, and found nothing at any delay. What remains open is
> whether that null is a property of the observable or of the cohort.

That is still a real open door for Phase 2. It is just a different door than the one in
the current draft, and it is one we can defend line by line.


---

# Addendum — on your joint experiment design

*Written after your grid proposal arrived.*

We accept the design and the decision rule. Running both statistics in one run on
identical residues and labels is exactly right, and pre-registering "must beat
closeness centrality, not just the pipeline" is the honest bar. Three things to add
before it runs, one of which we think is load-bearing.

## 1. The one gap: residualise on proximity, don't only compare against it

Your baselines list proximity in both sign directions as a **comparator**. Our
convention throughout is different and stronger: we **regress distance out** and
score the residual. It is what closed every observable on our side, and the
calibration is built in — proximity residualised against itself scores 0.5000
exactly, so the control cannot silently pass.

Without it, a statistic can beat closeness centrality and still be distance.

**Please add residualised AUC alongside raw AUC for every arm.** It is one extra
column, it costs nothing on a run you are already doing, and without it a
positive result will not survive the first referee who asks.

## 2. A prediction we are willing to be wrong about, registered now

Your range statistic — `max(τ) − min(τ)`, and RMS — is **non-negative and
amplitude-like**. That is structurally the same class of quantity as the unsigned
magnitude `|O(r)|`, which we measured directly: its correlation with proximity is
**0.92 at short delay**, falling monotonically to 0.24 at convergence, with
residualised AUC of **0.5000** — pure distance, nothing else.

**So we predict the range statistic will correlate strongly with proximity at short
delay and collapse under residualisation.** We are writing that down before your
run rather than after it. If it survives residualisation, the prediction is wrong
and the result is considerably more interesting than the point value ever was.

## 3. Two things in your note that change the prior, and should be in the write-up

- *"I only tested that on 138 proteins, not all of them."*
- *"It must hold at more than one MIN_HOP — currently only MIN_HOP=1 works."*

A result that appears on a subset at exactly one MIN_HOP setting is a single cell,
and both facts belong next to the +0.107 wherever it is quoted. Your own
pre-registration already requires ≥2 MIN_HOP settings, which is the right
correction — we are only asking that the current limitation be stated rather than
resolved silently by the new run.

## 4. On "your null doesn't test mine directly"

Agreed, and we said the same thing first: a point value at a delay and a range
across delays are different statistics. Our scan closes the point value on our
cohort. It does not close the range statistic, which nobody has tested anywhere.

That is the experiment. We think it should run.

## 5. Something for the classical side, which is where our submission actually lives

Separately from the quantum arms: nobody has measured how much the **pocket
detectors themselves** disagree. We are running the agreement cascade —
fpocket vs PASSer vs PocketMiner, one structure set, one truth rule — recovered by
at least one, by at least two, by all.

This matters to you directly. If the detectors mostly agree, the PASSer-vs-fpocket
cohort question is a small effect and either choice is defensible. If they do not,
that disagreement is itself the finding, and it is measured rather than argued.

It also repeats, in a second domain, the decomposition already in our draft: the
field's "84% recovery" is 99 of 118 structures found by **at least one of six**
statistical measures; requiring three drops it to 57.6%, requiring all six to
17.8%. The number is correctly computed and is simply not what a reader assumes.
If pocket detectors show the same shape, the certifying benchmark stops being a
proposal and starts being an obvious necessity.
