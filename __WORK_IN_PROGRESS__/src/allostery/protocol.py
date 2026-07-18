"""Phase 3 -- DEV/FROZEN firewall and leave-one-protein-out protocol.

The single biggest risk this project names for itself
(PLAN-01.07.26.md #2): "Leakage was the core flaw... any per-target knob
touching holo = leakage." This module is the mechanically-enforced
boundary that makes the eventual ceiling-LOPO gap number honest -- not a
docstring convention, a hard runtime raise.

Two phases, two contexts (Constraints And Invariants, TASK-0006):

  ceiling_context()   Phase 2 -- heavy optimizer, answer key in hand.
                      Leakage is explicitly *the goal* here (PLAN.md:
                      "leakage is the goal here"), so nothing is blocked.

  frozen_context(X)   Phase 3 -- LOPO. Reading target(s) in X's holo/pocket
                      label via this module's gated accessors raises
                      LeakageError. Use to bracket only the *selection*
                      step of a LOPO iteration -- exit the `with` block
                      before reading the held-out target's true label to
                      score it (that release, after selection is frozen,
                      is the whole point of LOPO, not a firewall bypass).

Only labels.py's declared outputs (pocket mask, functional indices -- see
that module's own "this module is the only place downstream code may look
at the holo structure" docstring) and superpose.py's holo-informed Phase 1b
report are gated here. Everything else in the package is unaffected by
default (no active context = unguarded) -- this is an opt-in firewall for
Phase-3 pipeline code (select.py, TASK-0007; analysis.py, TASK-0008), not a
retroactive lock on labels.py/superpose.py's own direct callers/tests.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass


class LeakageError(RuntimeError):
    """Raised when FROZEN-path code reads a held-out target's holo/pocket
    label. This is exactly the failure mode the firewall exists to catch
    (PLAN-01.07.26.md #2) -- never caught-and-ignored by calling code."""


@dataclass(frozen=True)
class ProtocolContext:
    mode: str                  # "ceiling" | "frozen"
    blocked_targets: frozenset


_stack: list[ProtocolContext] = []

_UNGUARDED = ProtocolContext(mode="unguarded", blocked_targets=frozenset())


def current_context() -> ProtocolContext:
    """The innermost active context, or an unguarded default if none is
    active (see module docstring for why unguarded, not fail-closed, is
    the default)."""
    return _stack[-1] if _stack else _UNGUARDED


@contextmanager
def ceiling_context():
    """Phase 2: heavy optimizer, answer key in hand -- leakage is the goal.
    Blocks nothing; exists so callers state *which phase* they're running
    as, per this task's Constraints, rather than relying on the absence of
    a frozen_context to mean "ceiling.\""""
    _stack.append(ProtocolContext(mode="ceiling", blocked_targets=frozenset()))
    try:
        yield _stack[-1]
    finally:
        _stack.pop()


@contextmanager
def frozen_context(blocked_targets):
    """Phase 3: FROZEN path. `blocked_targets` is a target name or an
    iterable of names; reading any of them via this module's gated
    accessors raises LeakageError for the duration of this `with` block."""
    if isinstance(blocked_targets, str):
        blocked = frozenset({blocked_targets})
    else:
        blocked = frozenset(blocked_targets)
    _stack.append(ProtocolContext(mode="frozen", blocked_targets=blocked))
    try:
        yield _stack[-1]
    finally:
        _stack.pop()


def assert_readable(target_name: str) -> None:
    """Raise LeakageError if `target_name` is blocked in the currently
    active context. The gated accessors below call this before touching
    labels.py/superpose.py; exposed publicly too, for any future call site
    that reads a holo-derived label some other way."""
    ctx = current_context()
    if target_name in ctx.blocked_targets:
        raise LeakageError(
            f"attempted to read target '{target_name}'s holo/pocket label "
            "while it is held out under a frozen_context -- this is the "
            "leakage this firewall exists to catch."
        )


# ---------------------------------------------------------------------------
# Provenance stamping (TASK-0088, closes SEAM-0004)
# ---------------------------------------------------------------------------
# report.verdict_template renders from an already-assembled results dict,
# almost always *after* the computation's frozen_context has already
# exited -- so verdict_template reading current_context() at render time
# cannot work (see TASK-0088's own "Before implementing" note). Instead,
# stamp_provenance() issues an unforgeable-in-practice token *at
# computation time*, inside the context, that survives into the results
# dict for later verification at render time.

_issued_frozen_stamps: set = set()


def stamp_provenance(results: dict) -> dict:
    """Mark `results` as having been produced from inside an active
    frozen_context. Raises RuntimeError if called when
    `current_context().mode != "frozen"` -- this is the only function
    that can issue a valid stamp, so a caller cannot fake one by hand-
    writing the same dict key (a plain `results["_frozen_stamp"] = "x"`
    produces a token `verify_frozen_stamp` has never issued, so it is
    rejected the same as no stamp at all).

    Returns a shallow copy of `results` with `"_frozen_stamp"` set --
    does not mutate the caller's dict in place.
    """
    ctx = current_context()
    if ctx.mode != "frozen":
        raise RuntimeError(
            "stamp_provenance() called outside an active frozen_context "
            f"(current mode: {ctx.mode!r}) -- a provenance stamp can only "
            "be issued from inside `with frozen_context(...):`, at "
            "computation time, not guessed or asserted after the fact."
        )
    import secrets

    token = secrets.token_hex(16)
    _issued_frozen_stamps.add(token)
    stamped = dict(results)
    stamped["_frozen_stamp"] = token
    return stamped


def verify_frozen_stamp(results: dict) -> bool:
    """True iff `results` carries a stamp actually issued by
    `stamp_provenance` from inside a real `frozen_context` -- not merely
    the presence of a `"_frozen_stamp"` key with any value."""
    token = results.get("_frozen_stamp")
    return token is not None and token in _issued_frozen_stamps


# ---------------------------------------------------------------------------
# Gated accessors -- select.py (TASK-0007) / analysis.py (TASK-0008) must
# call these, not labels.py/superpose.py directly, for FROZEN-path code.
# ---------------------------------------------------------------------------

def get_pocket_mask(apo, holo, target_name: str, target_config: dict, cutoff: float = 4.5):
    """Gated, *assembled* pocket label -- `labels.build_labels(...).pocket`
    (excludes active_site/terminal), not `labels.holo_pocket_mask`'s raw
    ligand-contact mask.

    TASK-0070/SEAM-0003: consuming the raw mask directly (this function's
    previous implementation) was the defect this fixes -- "labels owns
    ingredients, protocol gates them, analysis consumes the raw mask" is
    exactly the failure `SEAM_PROTOCOL.md` uses as its own motivating
    example. Takes `target_config` (not a bare `ligand_code`) so it now
    matches `get_functional_indices`/`get_superpose_report`'s existing
    signature shape -- this function was the odd one out before.
    """
    assert_readable(target_name)
    from .labels import build_labels

    return build_labels(apo, holo, target_config, cutoff=cutoff).pocket


def get_labels(apo, holo, target_name: str, target_config: dict, cutoff: float = 4.5, terminal_fraction: float = 0.05):
    """Gated `labels.build_labels` -- the full assembled `Labels` object
    (pocket, pocket_raw, active_site, terminal, provenance), for callers
    that need more than just the final pocket mask `get_pocket_mask`
    returns."""
    assert_readable(target_name)
    from .labels import build_labels

    return build_labels(apo, holo, target_config, cutoff=cutoff, terminal_fraction=terminal_fraction)


def get_functional_indices(coords, ligand_groups, target_name: str, target_config: dict, cutoff: float = 4.5, **kwargs):
    """Gated labels.functional_indices.

    Forwards **kwargs (e.g. heavy_atom_coords/heavy_atom_seq_index) so a
    FROZEN-path caller can reach every parameter labels.functional_indices
    accepts without ever bypassing this gate -- same **kwargs pass-through
    pattern as get_superpose_report, chosen over an explicit-but-fragile
    parameter list (TASK-0063): functional_indices has already grown once
    since this gate was first written, and **kwargs is immune to that
    class of drift recurring.
    """
    assert_readable(target_name)
    from .labels import functional_indices

    return functional_indices(coords, ligand_groups, target_config, cutoff=cutoff, **kwargs)


def get_superpose_report(apo, holo, target_name: str, target_config: dict, **kwargs):
    """Gated superpose.run_superpose (alignment, pocket cross-map, openness
    gate, CO(m), kappa, mode energetics -- all holo-informed Phase 1b
    output)."""
    assert_readable(target_name)
    from .superpose import run_superpose

    return run_superpose(apo, holo, target_config, **kwargs)


# ---------------------------------------------------------------------------
# DEV/FROZEN roster (config-driven target-set split)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProtocolRoster:
    """The DEV/FROZEN split of the target set.

    Config-driven: built from an explicit {target_name: "dev"|"frozen"}
    mapping the caller supplies -- never a hardcoded list in this module.
    Which targets graduate from DEV (ceiling-eligible, Phase 2) to FROZEN
    (LOPO-only, Phase 3) is a baseline-clearing decision (PLAN.md Phase 3:
    "only on targets whose ceiling clears the baselines") that belongs to
    select.py/analysis.py, not this module -- this is bookkeeping, not
    the decision logic.
    """

    dev: frozenset
    frozen: frozenset

    @classmethod
    def from_mapping(cls, target_phase: dict) -> "ProtocolRoster":
        dev = frozenset(t for t, phase in target_phase.items() if phase == "dev")
        frozen = frozenset(t for t, phase in target_phase.items() if phase == "frozen")
        unknown = {t: p for t, p in target_phase.items() if p not in ("dev", "frozen")}
        if unknown:
            raise ValueError(f"unknown phase value(s), must be 'dev' or 'frozen': {unknown}")
        return cls(dev=dev, frozen=frozen)

    def is_dev(self, target_name: str) -> bool:
        return target_name in self.dev

    def is_frozen(self, target_name: str) -> bool:
        return target_name in self.frozen


# ---------------------------------------------------------------------------
# Leave-one-protein-out
# ---------------------------------------------------------------------------

def leave_one_protein_out(targets):
    """Yield (train_targets, held_out_target) for every target in
    `targets`, each held out exactly once over a full pass.

    Deliberately does NOT itself enter a frozen_context -- composability
    over magic. The caller wraps only their *selection* logic in
    `with frozen_context({held_out}): ...` inside the loop body, then
    reads the held-out target's true label after that `with` block exits
    to score the held-out prediction (the whole point of LOPO). Baking
    context entry into this generator would make that release impossible
    to express.
    """
    targets = list(targets)
    for i, held_out in enumerate(targets):
        yield targets[:i] + targets[i + 1:], held_out


def select_frozen_config(build_candidates, held_out_target: str) -> dict:
    """Pick the best operator/parameter candidate for `held_out_target`
    using `select.unsupervised_score`, inside the `frozen_context` that
    blocks that target -- the concrete FROZEN-loop selection step
    `leave_one_protein_out`'s own docstring describes, and the missing
    connective layer SEAM-0009 names (TASK-0064).

    `build_candidates` is a zero-arg callable returning
    `unsupervised_score`'s own input shape (a list of `{"H", "source",
    "t", ...}` dicts) -- taking a callable rather than an already-built
    list is deliberate: it lets this function hold the `frozen_context`
    open across *both* candidate construction and scoring, so a
    candidate-building routine that accidentally reads
    `held_out_target`'s pocket/holo label via any of this module's gated
    accessors raises `LeakageError` too, not just a direct
    `unsupervised_score` call (which never touches labels at all and so
    could never itself trigger the gate).

    Returns the winning candidate dict (shallow copy, caller's own keys
    intact) with `"index"` (its position in `build_candidates()`'s
    output) and `"score"` (its `unsupervised_score` value) added.
    """
    from .select import unsupervised_score

    with frozen_context({held_out_target}):
        candidates = build_candidates()
        scores = unsupervised_score(candidates)

    best_i = int(scores.argmax())
    winner = dict(candidates[best_i])
    winner["index"] = best_i
    winner["score"] = float(scores[best_i])
    return winner


# ---------------------------------------------------------------------------
# FROZEN-gated per-target verdict pipeline (TASK-0079.003)
# ---------------------------------------------------------------------------

def _finite_or_none(value):
    import numpy as np

    return value if value is not None and np.isfinite(value) else None


def run_frozen_verdict(
    target_name: str,
    candidates_builder,
    coords,
    bfactors,
    source,
    labels,
    *,
    cutoff: float = 10.0,
    alpha: float = 0.3,
    terminal_fraction: float = 0.05,
    n_low_modes: int = 10,
    t_max: float = 15.0,
    n_steps: int = 500,
    floor_scores=None,
    holo_H=None,
    holo_source=None,
    holo_labels=None,
    apo_idx=None,
    holo_idx=None,
    consistency_k: int = 20,
    coherent: bool = True,
    use_converged_limit: bool = False,
) -> dict:
    """Select an operator/parameter config for `target_name` blind to its
    labels, then score and stamp the result -- the safety-critical core of
    the end-to-end run (TASK-0079.003) that wires `select_frozen_config`
    (TASK-0064), `analysis.py`'s scoring functions (TASK-0008) and
    `assemble_verdict_results` (TASK-0079.001), `diagnostics.classify_failure`
    (TASK-0058/0071), and `stamp_provenance` (TASK-0088) together for the
    first time.

    `labels` (the target's true, already-assembled pocket mask) is a plain
    array the caller already holds -- obtaining it is the caller's job
    (typically `labels.build_labels`, called directly and un-gated, per
    this module's own "not a retroactive lock on labels.py's own direct
    callers" boundary). This function never calls a gated accessor itself;
    the only thing its `frozen_context` polices is `candidates_builder` --
    a builder that reads `target_name`'s pocket/holo label via
    `get_pocket_mask`/`get_labels`/`get_functional_indices`/
    `get_superpose_report` raises `LeakageError`, same "poisoned builder"
    pattern `test_protocol.py::TestSelectFrozenConfig` already establishes.

    `benchmark()`/`ablation()` never accept an external H -- both always
    build their own default-parameter operators internally -- so they run
    here as the *default*-parameter comparison
    (`AUC_apo_Hnew_default`/`AUC_apo_H10_baseline`), never "the winning
    config". Only `quantum_vs_classical`, which does accept an H, runs
    against the winning candidate's `H`/`source` (falling back to this
    call's own `source`/`t_max` only if the winning candidate omits
    them) -- its `"ctqw"` AUC becomes `AUC_apo_Hnew_optimised`.

    Holo-side numbers (`AUC_holo_Hnew_optimised`, `mean_rho_apo_holo`,
    `mean_jacc20`) are computed only if the caller supplies `holo_H`
    (built from the same operator recipe as the winning apo candidate --
    reconstructing one here would mean inventing a new search space, out
    of this function's scope per TASK-0079.003's own Intent Contract)
    plus `holo_source`/`holo_labels`; `apo_idx`/`holo_idx` additionally
    gate the apo<->holo consistency computation. Omitted entirely, not
    raised, when holo inputs aren't supplied -- matches
    `assemble_verdict_results`'s own per-key-optional philosophy.

    Returns the stamped, `.001`-assembled `results` dict, plus
    `results["_diagnosis"]` (`diagnostics.classify_failure`'s verdict on
    the winning config's own apo-side score -- a target indistinguishable
    from chance, or worse than `floor_scores` if supplied, is flagged
    here rather than silently rendered as a clean verdict) and
    `results["_winner_index"]`/`results["_winner_score"]` (the winning
    candidate's position and `unsupervised_score` value, for audit).

    `coherent` (TASK-0118): passed straight through to `benchmark`'s and
    every `quantum_vs_classical` call's own `coherent` parameter (apo and
    holo alike) -- does *not* reach `select_frozen_config`/
    `unsupervised_score`'s own internal scoring (`select.py`'s label-free
    selection heuristics stay on the coherent superposition they were
    built and tested against; this parameter only affects the reported
    AUCs, not which candidate wins).

    `use_converged_limit` (TASK-0130): passed straight through to
    `benchmark`'s and every `quantum_vs_classical` call's own
    `use_converged_limit` parameter (apo and holo alike) -- same "affects
    reported AUCs, not candidate selection" boundary as `coherent` above.
    `AUC_apo_Hnew_optimised` (from `qvc["ctqw"]`) is the "actual" score
    this affects most directly.
    """
    from .analysis import (
        ablation,
        apo_holo_consistency,
        assemble_verdict_results,
        benchmark,
        quantum_vs_classical,
    )
    from .diagnostics import classify_failure

    with frozen_context({target_name}):
        winner = select_frozen_config(candidates_builder, target_name)

        bench = benchmark(
            coords, bfactors, source, labels,
            cutoff=cutoff, t_max=t_max, n_steps=n_steps, coherent=coherent,
            use_converged_limit=use_converged_limit,
        )
        abl = ablation(
            coords, bfactors, source, labels,
            cutoff=cutoff, alpha=alpha, terminal_fraction=terminal_fraction,
            n_low_modes=n_low_modes, t_max=t_max, n_steps=n_steps,
        )
        qvc = quantum_vs_classical(
            winner["H"], winner.get("source", source), labels,
            t_max=winner.get("t", t_max), n_steps=n_steps, coherent=coherent,
            use_converged_limit=use_converged_limit,
        )

        # TASK-0112: return_ci=True attaches a block-bootstrap CI to both
        # the scored operator and the winning floor candidate -- `_diagnosis`
        # itself stays a bare str (every existing reader of that key is
        # untouched), the CI rides alongside in three new, additive keys.
        classification = classify_failure(
            qvc["ctqw"]["occ"], labels, H=winner["H"], bfactors=bfactors,
            floor_scores=floor_scores, return_ci=True,
        )
        diagnosis = classification.category

        consistency = None
        auc_holo_optimised = None
        if holo_H is not None and holo_labels is not None:
            holo_qvc = quantum_vs_classical(
                holo_H, holo_source, holo_labels,
                t_max=winner.get("t", t_max), n_steps=n_steps, coherent=coherent,
                use_converged_limit=use_converged_limit,
            )
            auc_holo_optimised = _finite_or_none(holo_qvc["ctqw"]["AUC"])
            if apo_idx is not None and holo_idx is not None:
                consistency = apo_holo_consistency(
                    qvc["ctqw"]["occ"], holo_qvc["ctqw"]["occ"],
                    apo_idx, holo_idx, k=consistency_k,
                )

        assembled = assemble_verdict_results(
            benchmark_out=bench,
            ablation_out=abl,
            qvc_out=qvc,
            consistency_out=consistency,
            auc_apo_optimised=_finite_or_none(qvc["ctqw"]["AUC"]),
            auc_holo_optimised=auc_holo_optimised,
        )
        assembled["_diagnosis"] = diagnosis
        assembled["_diagnosis_score_ci"] = classification.score_ci
        assembled["_diagnosis_floor_ci"] = classification.floor_ci
        assembled["_diagnosis_ci_overlap"] = classification.ci_overlap
        assembled["_winner_index"] = winner["index"]
        assembled["_winner_score"] = winner["score"]

        stamped = stamp_provenance(assembled)

    return stamped
