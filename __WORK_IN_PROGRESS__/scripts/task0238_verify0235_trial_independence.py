"""Reviewer check on [[TASK-0235]] -- are its "4 trials" four samples, or one
computation repeated four times?

TASK-0235's decisive claim is "BCR_ABL1 flips 0/4 -> 4/4 trials clearing the
druggability bar ... a genuinely decisive, real result, not a noisy
improvement." That reading requires the 4 trials to be independent draws.

But `ceiling_rerun`'s loop (task0235_local_rigid_backbone.py:228-241) varies
NOTHING between iterations: same structure reloaded, same deterministic
`local_rigid_reconstruction`, and `_run_evoef2("SideChainRepack", ...)` which
takes no seed argument at all (task0204_rotamer_repack_baseline.py:147).

So this writes the trial PDBs exactly as the task's own code does and hashes
them. If they are byte-identical, the 4 trials are 4 repeats of one
computation, and the reported spread is downstream tool jitter -- which makes
the effective n = 1, not 4.
"""
from __future__ import annotations
import hashlib, sys, tempfile
from pathlib import Path
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path: sys.path.insert(0, str(_p))
import prody; prody.confProDy(verbosity="none")
from allostery.clean import load_target_config
from allostery.labels import build_labels
from task0235_local_rigid_backbone import (
    local_rigid_reconstruction, _load_apo_holo, _load_full_atom_apo,
    _common_set_and_projection, _target_ca_dicts, _select_window,
    _write_contiguous_window_chain, POCKET_CUTOFF, WINDOW_MAX_SIZE, N_TRIALS)

NAME = sys.argv[1] if len(sys.argv) > 1 else "BCR_ABL1"
cfg = load_target_config(NAME)
apo, holo = _load_apo_holo(NAME, cfg)
labels_obj = build_labels(apo, holo, cfg, cutoff=POCKET_CUTOFF, target_name=NAME)
window = _select_window(apo, labels_obj.pocket, max_size=WINDOW_MAX_SIZE)
chains = cfg.get("apo_chains") or cfg.get("chains")
alignment, full_disp, proj_disp, delta_r, k_used = _common_set_and_projection(apo, holo, cfg)
apo_ca_full, target_ca_full = _target_ca_dicts(apo, alignment, full_disp)

hashes = []
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    for i in range(N_TRIALS):
        struct = _load_full_atom_apo(cfg, chains)
        struct = local_rigid_reconstruction(struct, apo_ca_full, target_ca_full)
        pdb = tmp / f"{NAME.lower()}_trial{i}.pdb"
        _write_contiguous_window_chain(struct, window, pdb)
        # normalise away the filename, which is the only intended per-trial difference
        body = b"".join(l for l in pdb.read_bytes().splitlines(keepends=True)
                        if not l.startswith(b"REMARK"))
        h = hashlib.sha256(body).hexdigest()
        hashes.append(h)
        print(f"  trial {i}: sha256 {h[:16]}  ({pdb.stat().st_size} bytes)")

uniq = len(set(hashes))
print(f"\n{NAME}: {N_TRIALS} trials -> {uniq} distinct input structure(s)")
print("VERDICT: " + ("identical inputs -- the 4 trials are ONE computation repeated; "
                     "reported spread is downstream (EvoEF2/fpocket) jitter, effective n=1"
                     if uniq == 1 else
                     f"{uniq} distinct inputs -- trials do vary at the structure level"))
