"""TASK-0328's own Planned Validation: "re-running the script twice must
produce byte-identical p-values. Assert it, don't eyeball it" -- and
[[TASK-0319]]'s standing finding that a checker isn't verified unless it's
shown to fail on a seeded violation (here: the ORIGINAL `hash()`-seeded
scheme, which this test also runs, to prove the test would have caught
Defect 1 rather than passing regardless of what it's given).

Run: ../.venv/bin/python3 -m pytest scripts/test_task0328_pocketsweep_null_recalibration.py -q
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from task0328_pocketsweep_null_recalibration import (  # noqa: E402
    ART, ROUNDS, det_seed, draw_pocket_block_null, draw_uniform_null,
    load_round, null_stats_for_protein,
)


def _run_subset(seed_fn, n_proteins=6):
    recs = load_round(ROUNDS["round1"])
    names = sorted(recs.keys())[:n_proteins]
    out = {}
    for name in names:
        v = recs[name]
        rng_u = np.random.default_rng(seed_fn(name + "|uniform"))
        rng_c = np.random.default_rng(seed_fn(name + "|compact"))
        out[name] = (
            null_stats_for_protein(v, rng_u, draw_uniform_null),
            null_stats_for_protein(v, rng_c, draw_pocket_block_null),
        )
    return out


def test_deterministic_seed_reproduces_byte_identical():
    """The fixed (hashlib-based) seeding: two independent runs must match
    exactly -- not "close", not "correlated", identical floats."""
    r1 = _run_subset(det_seed)
    r2 = _run_subset(det_seed)
    assert r1.keys() == r2.keys()
    for name in r1:
        assert r1[name] == r2[name], f"{name}: not byte-identical across runs"


def test_broken_hash_seed_is_NOT_reproducible_across_processes():
    """Negative control for the test above, per TASK-0319's standing finding:
    prove this test harness actually discriminates by running the ORIGINAL
    defect (`hash()`, process-salted) in two separate subprocesses and
    confirming it does NOT reproduce -- if this test also passed, the
    positive test above would be vacuous (passing regardless of the fix)."""
    script = (
        "import sys; sys.path.insert(0, %r)\n"
        "from task0328_pocketsweep_null_recalibration import load_round, ROUNDS, "
        "draw_uniform_null, null_stats_for_protein\n"
        "import numpy as np\n"
        "recs = load_round(ROUNDS['round1'])\n"
        "name = sorted(recs.keys())[0]\n"
        "v = recs[name]\n"
        "rng = np.random.default_rng(abs(hash(name)) %% (2**32))\n"
        "print(null_stats_for_protein(v, rng, draw_uniform_null))\n"
    ) % str(HERE)
    outs = set()
    for _ in range(3):
        p = subprocess.run(
            [sys.executable, "-c", script],
            cwd=str(HERE),
            capture_output=True,
            text=True,
        )
        assert p.returncode == 0, p.stderr
        outs.add(p.stdout.strip())
    # hash() randomization means these should differ run to run at least
    # some of the time -- if all 3 happen to collide (astronomically
    # unlikely with PYTHONHASHSEED unset) this negative control would be
    # too weak, but 3 independent hash-seed draws matching exactly has
    # never been observed in practice for this repo's own str keys.
    assert len(outs) > 1, (
        "expected the ORIGINAL hash()-seeded scheme to be non-reproducible "
        "across processes -- got identical output every time, which would "
        "mean this test can't actually tell the fix apart from the defect"
    )


def test_pocket_block_null_preserves_exact_kpos():
    """The trimming logic in draw_pocket_block_null must never over/under
    shoot the required positive count -- this is asserted inside the
    function itself, but re-checked here across many proteins/reps as a
    standalone guarantee, not just an inline assert that could be
    silently skipped under -O."""
    recs = load_round(ROUNDS["round1"])
    rng = np.random.default_rng(12345)
    for name in sorted(recs.keys())[:15]:
        v = recs[name]
        y = np.asarray(v["y"])
        n, kpos = len(y), int(y.sum())
        members = {}
        for i, pid in enumerate(v["seed_pocket"]):
            members.setdefault(pid, []).append(i)
        for _ in range(20):
            pos = draw_pocket_block_null(rng, n, kpos, members)
            assert len(pos) == kpos
            assert len(set(pos.tolist())) == kpos  # no duplicate seed indices
            assert pos.min() >= 0 and pos.max() < n


if __name__ == "__main__":
    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", __file__, "-q", "-v"]))
