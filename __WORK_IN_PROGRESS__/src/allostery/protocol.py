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


def get_functional_indices(coords, ligand_groups, target_name: str, target_config: dict, cutoff: float = 4.5):
    """Gated labels.functional_indices."""
    assert_readable(target_name)
    from .labels import functional_indices

    return functional_indices(coords, ligand_groups, target_config, cutoff=cutoff)


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
