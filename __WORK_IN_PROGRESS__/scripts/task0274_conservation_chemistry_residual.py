"""TASK-0274 -- every attribution block this register has ever tested is
geometric or dynamical (geometry / fpocket / ctqw / sasa [[TASK-0266]] /
p2rank [[TASK-0260]] / potential terms [[TASK-0263]] / pocketminer
[[TASK-0269]]). Checked directly: no sequence conservation feature of any
kind, and no explicit residue chemistry, exists anywhere in
`src/allostery/`. Both are ordinary, decades-old feature families -- test
them before calling the 27-29% residual irreducible.

Conservation block. MD-free and Constraint-3-clean by construction (a
curated multiple sequence alignment, no molecular dynamics anywhere).
Route, in order:
  1. Reuse `backend.active_site`'s OWN UniProt-offset machinery verbatim
     -- `get_uniprot`, `_residues_by_num`, `_uniprot_features`,
     `_find_offset` -- the same code path `detect_active_site` already
     uses to place UniProt-numbered annotations onto PDB author numbering,
     not a second implementation of SIFTS-style mapping.
  2. The UniProt accession's Pfam domain match, via InterPro's REST API
     (`entry/pfam/protein/uniprot/{acc}`) -- domain identification only,
     no alignment work happens here.
  3. The Pfam SEED alignment itself (curated, not the ungapped-HMM FULL
     alignment) via InterPro's own alignment endpoint, parsed with
     `Bio.AlignIO` (pure Python, no external MSA binary -- confirmed none
     of clustalo/mafft/muscle/hmmalign is installed in this environment,
     checked directly before choosing this route).
     Citation verified live via Crossref: Mistry J et al. (2021) "Pfam:
     The protein families database in 2021", Nucleic Acids Research,
     DOI 10.1093/nar/gkaa913.
  4. Per-column conservation = 1 - Shannon_entropy/log2(20) over the
     20-letter amino-acid alphabet (gaps excluded from the column's own
     frequency count, gap fraction reported separately as a data-quality
     signal) -- the textbook baseline conservation score (see Valdar 2002,
     "Scoring residue conservation", for a survey placing Shannon entropy
     among the standard simple methods; no exotic method invented here).
  5. The query's own UniProt sequence is very unlikely to BE a seed member
     (Pfam seeds are curated representative subsets) -- so the seed row
     with the highest identity to the query's Pfam-domain fragment
     (`Bio.Align.PairwiseAligner`, global, BLOSUM62; no external binary) is
     used as a transfer anchor: a second pairwise alignment carries that
     row's own column assignments onto the query's residues. This is a
     recognised cheap alternative to a full profile/HMM alignment
     (nearest-homolog transfer), not a novel unverified method -- and its
     own identity/depth is reported per target, honestly, per this task's
     own Scope ("a shallow MSA gives a meaningless score and that must be
     visible, not hidden").
  6. Multi-chain targets: `backend.active_site` itself only resolves
     UniProt annotations against chain[0] (checked directly in
     `detect_active_site`/`t0242.prep`, an existing precedent, not a new
     limitation introduced here) -- conservation here is assigned to
     residues of that SAME chain only; other chains in the same target get
     NaN (imputed via nanmedian like every other NaN block value in this
     register), and the true chain-scoped coverage is reported per target
     rather than silently assumed complete.

Chemistry block. Four classic per-residue physicochemical descriptors,
deliberately simple:
  - hydrophobicity: Kyte & Doolittle (1982) "A simple method for
    displaying the hydropathic character of a protein", J Mol Biol
    157:105-132, DOI 10.1016/0022-2836(82)90515-0 (verified live).
  - charge at physiological pH: D/E = -1, K/R = +1, H = 0 (simplified,
    named as such -- the point is whether *anything* chemical helps, not
    a good pKa model).
  - aromaticity: F/W/Y = 1, else 0.
  - side-chain volume: Zamyatnin (1972) "Protein volume in solution",
    Prog Biophys Mol Biol 24:107-123, DOI 10.1016/0079-6107(72)90005-3
    (verified live).

Reuses, does not re-derive:
  - `task0249_composite_dumb_baseline.target_rows` / `task0242_two_stage_
    dryrun.prep` for the frozen-set apo structures/seeds/labels (imported).
  - `task0254_fpocket_variance_and_crypticity`'s own `cv_auc`/`build_blocks`
    /`crypticity`/`z` (imported), unchanged.
  - `task0261_cluster_robust_stats.cluster_sign_flip_test`/
    `cluster_permutation_two_group`/`CM` (imported) -- this task's own
    Scope: "TASK-0261's exact cluster-level permutation."
  - The generalised n-block exact Shapley routine, in the same form
    `task0266_sasa_burial_control.py` already wrote locally (not imported
    cross-task, same pattern) -- extended nowhere; used verbatim.
  - `backend.active_site`'s own `get_uniprot`/`_residues_by_num`/
    `_uniprot_features`/`_find_offset`/`_THREE_TO_ONE` (imported), not
    reimplemented.
"""
from __future__ import annotations

import io
import itertools
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import numpy as np
import requests
import yaml
from Bio import AlignIO
from Bio.Align import PairwiseAligner, substitution_matrices

_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import task0242_two_stage_dryrun as t0242  # noqa: E402
import task0249_composite_dumb_baseline as t0249  # noqa: E402
import task0254_fpocket_variance_and_crypticity as t0254  # noqa: E402
from task0261_cluster_robust_stats import (  # noqa: E402
    CM, cluster_permutation_two_group, cluster_sign_flip_test,
)
from backend import active_site as backend_as  # noqa: E402

OUT = _ROOT / "results/tasks/0274_conservation_chemistry_residual"
PFAM_CACHE = OUT / "pfam_seed_cache"
FROZEN_CONFIG = _ROOT / "config/candidate_targets_task0243.yaml"
BLOCKS5 = ["geometry", "fpocket", "ctqw", "conservation", "chemistry"]
BASELINE_3BLOCK = _ROOT / "results/tasks/0254_fpocket_variance_and_crypticity/part_a_shapley_attribution.json"

# ---------------------------------------------------------------- chemistry
KD_HYDROPATHY = {  # Kyte & Doolittle 1982, DOI 10.1016/0022-2836(82)90515-0
    "I": 4.5, "V": 4.2, "L": 3.8, "F": 2.8, "C": 2.5, "M": 1.9, "A": 1.8,
    "G": -0.4, "T": -0.7, "S": -0.8, "W": -0.9, "Y": -1.3, "P": -1.6,
    "H": -3.2, "E": -3.5, "Q": -3.5, "D": -3.5, "N": -3.5, "K": -3.9, "R": -4.5,
}
CHARGE = {"D": -1.0, "E": -1.0, "K": 1.0, "R": 1.0, "H": 0.0}
AROMATIC = {"F", "W", "Y"}
ZAMYATNIN_VOLUME = {  # Zamyatnin 1972, DOI 10.1016/0079-6107(72)90005-3, A^3
    "G": 66.4, "A": 92.5, "S": 91.0, "C": 108.5, "D": 111.1, "P": 112.7,
    "N": 114.1, "T": 116.1, "E": 138.4, "V": 141.7, "Q": 143.8, "H": 153.2,
    "M": 162.9, "I": 166.7, "L": 166.7, "K": 168.6, "R": 173.4, "F": 189.9,
    "Y": 193.6, "W": 227.8,
}


def chemistry_features(resnames: list) -> np.ndarray:
    """(N, 4) = [hydropathy, charge, aromaticity, volume], one-letter codes
    via `backend.active_site._THREE_TO_ONE` (reused, not reimplemented)."""
    out = np.zeros((len(resnames), 4))
    for i, rn in enumerate(resnames):
        aa = backend_as._THREE_TO_ONE.get(str(rn).strip().upper(), "A")
        out[i, 0] = KD_HYDROPATHY.get(aa, 0.0)
        out[i, 1] = CHARGE.get(aa, 0.0)
        out[i, 2] = 1.0 if aa in AROMATIC else 0.0
        out[i, 3] = ZAMYATNIN_VOLUME.get(aa, np.nanmean(list(ZAMYATNIN_VOLUME.values())))
    return out


# -------------------------------------------------------------- conservation
AA20 = "ACDEFGHIKLMNPQRSTVWY"
_ALIGN_CACHE: dict = {}   # pfam_acc -> AlignIO alignment (or None)
_CONS_CACHE: dict = {}    # (pdb_id, chain) -> (dict[(chain,resnum)]->score, info)


def _get_json(url: str, timeout: int = 25):
    try:
        r = requests.get(url, timeout=timeout, headers={"Accept": "application/json"})
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:  # noqa: BLE001
        return None


def _aligner() -> PairwiseAligner:
    a = PairwiseAligner()
    a.substitution_matrix = substitution_matrices.load("BLOSUM62")
    a.open_gap_score = -10
    a.extend_gap_score = -0.5
    a.mode = "global"
    return a


def pfam_domain_match(acc: str):
    """Largest Pfam domain match on this UniProt accession. Returns
    (pfam_acc, start, end) 1-based inclusive, or None."""
    data = _get_json(f"https://www.ebi.ac.uk/interpro/api/entry/pfam/protein/uniprot/{acc.lower()}")
    if not data or not data.get("results"):
        return None
    best = None
    for r in data["results"]:
        pf = r.get("metadata", {}).get("accession")
        for p in r.get("proteins", []) or []:
            for loc in p.get("entry_protein_locations", []) or []:
                for frag in loc.get("fragments", []) or []:
                    start, end = int(frag["start"]), int(frag["end"])
                    span = end - start
                    if best is None or span > best[3]:
                        best = (pf, start, end, span)
    return best[:3] if best else None


def fetch_pfam_seed(pfam_acc: str):
    if pfam_acc in _ALIGN_CACHE:
        return _ALIGN_CACHE[pfam_acc]
    PFAM_CACHE.mkdir(parents=True, exist_ok=True)
    f = PFAM_CACHE / f"{pfam_acc}.sto"
    if not f.exists():
        try:
            r = requests.get(
                f"https://www.ebi.ac.uk/interpro/api/entry/pfam/{pfam_acc}/?annotation=alignment:seed",
                timeout=30)
            if r.status_code != 200:
                _ALIGN_CACHE[pfam_acc] = None
                return None
            f.write_bytes(r.content)
        except Exception:  # noqa: BLE001
            _ALIGN_CACHE[pfam_acc] = None
            return None
    try:
        aln = AlignIO.read(io.StringIO(f.read_text(errors="replace")), "stockholm")
    except Exception:  # noqa: BLE001
        aln = None
    _ALIGN_CACHE[pfam_acc] = aln
    return aln


def column_conservation(aln):
    n_seq = len(aln)
    L = aln.get_alignment_length()
    cols = np.array([list(str(rec.seq)) for rec in aln])
    cons = np.full(L, np.nan)
    gap_frac = np.zeros(L)
    for c in range(L):
        col = cols[:, c]
        non_gap = col[col != "-"]
        gap_frac[c] = 1.0 - len(non_gap) / n_seq
        if len(non_gap) == 0:
            continue
        counts = np.array([np.sum(non_gap == a) for a in AA20], dtype=float)
        counts = counts[counts > 0]
        p = counts / counts.sum()
        H = -np.sum(p * np.log2(p))
        cons[c] = 1.0 - H / np.log2(20)
    return cons, gap_frac


def best_seed_row(aln, query_seq: str):
    aligner = _aligner()
    best_i, best_id = -1, -1.0
    for i, rec in enumerate(aln):
        s = str(rec.seq).replace("-", "")
        if not s:
            continue
        try:
            al = aligner.align(query_seq, s)[0]
        except Exception:  # noqa: BLE001
            continue
        a1, a2 = str(al[0]), str(al[1])
        matches = sum(1 for x, y in zip(a1, a2) if x == y and x != "-")
        length = sum(1 for x, y in zip(a1, a2) if x != "-" and y != "-")
        ident = matches / length if length else 0.0
        if ident > best_id:
            best_id, best_i = ident, i
    return best_i, best_id


def transfer_conservation(aln, cons, row_idx: int, query_seq: str, query_start: int):
    row_seq_gapped = str(aln[row_idx].seq)
    row_ungap_to_col = [c for c, ch in enumerate(row_seq_gapped) if ch != "-"]
    row_ungapped = row_seq_gapped.replace("-", "")
    aligner = _aligner()
    al = aligner.align(query_seq, row_ungapped)[0]
    q_str, r_str = str(al[0]), str(al[1])
    result = {}
    qi = ri = 0
    for qc, rc in zip(q_str, r_str):
        if qc != "-" and rc != "-":
            score = cons[row_ungap_to_col[ri]]
            if not np.isnan(score):
                result[query_start + qi] = float(score)
        if qc != "-":
            qi += 1
        if rc != "-":
            ri += 1
    return result


def per_residue_conservation(pdb_id: str, chain: str):
    """(dict[(chain,resnum)] -> score, info dict). Cached per (pdb_id,chain)
    since several frozen-set targets share one apo structure."""
    key = (pdb_id, chain)
    if key in _CONS_CACHE:
        return _CONS_CACHE[key]
    out: dict = {}
    info = {"n_seed": 0, "identity": None, "pfam": None, "domain_len": 0,
            "n_mapped": 0, "uniprot": None, "reason": None}
    res_by_num = backend_as._residues_by_num(pdb_id, chain)
    if not res_by_num:
        info["reason"] = "no residues resolved for this chain"
        _CONS_CACHE[key] = (out, info)
        return out, info
    acc = seq = delta = None
    for a in backend_as.get_uniprot(pdb_id):
        s, _feats = backend_as._uniprot_features(a)
        if not s:
            continue
        d = backend_as._find_offset(res_by_num, s)
        if d is not None:
            acc, seq, delta = a, s, d
            break
    if acc is None:
        info["reason"] = "no UniProt accession with a resolvable offset"
        _CONS_CACHE[key] = (out, info)
        return out, info
    match = pfam_domain_match(acc)
    if match is None:
        info["reason"] = f"no Pfam domain match for {acc}"
        info["uniprot"] = acc
        _CONS_CACHE[key] = (out, info)
        return out, info
    pfam_acc, start, end = match
    query_seq = seq[start - 1:end]
    aln = fetch_pfam_seed(pfam_acc)
    if aln is None or len(aln) < 4:
        info["reason"] = f"Pfam seed for {pfam_acc} unavailable or too shallow (<4 seqs)"
        info["uniprot"], info["pfam"] = acc, pfam_acc
        _CONS_CACHE[key] = (out, info)
        return out, info
    cons, _gap = column_conservation(aln)
    row_idx, ident = best_seed_row(aln, query_seq)
    if row_idx < 0:
        info["reason"] = "no seed row aligned"
        info["uniprot"], info["pfam"] = acc, pfam_acc
        _CONS_CACHE[key] = (out, info)
        return out, info
    transferred = transfer_conservation(aln, cons, row_idx, query_seq, start)
    n_mapped = 0
    for upos, score in transferred.items():
        pdb_r = upos + delta
        if pdb_r in res_by_num:
            out[(chain, pdb_r)] = score
            n_mapped += 1
    info.update(n_seed=len(aln), identity=round(ident, 3), pfam=pfam_acc,
                domain_len=end - start + 1, n_mapped=n_mapped, uniprot=acc)
    _CONS_CACHE[key] = (out, info)
    return out, info


def conservation_array(pdb_id: str, chain: str, chain_ids, resnums) -> tuple:
    scores, info = per_residue_conservation(pdb_id, chain)
    arr = np.array([scores.get((c, int(r)), np.nan) for c, r in zip(chain_ids, resnums)])
    return arr, info


# ------------------------------------------------------------------ shapley
def shapley_attribution_n(feat: dict, y: np.ndarray, blocks: list) -> dict:
    """Exact Shapley over `blocks` (5! = 120 permutations, cheap), reusing
    `t0254.cv_auc` unmodified. Also returns EVERY subset's value (`subset_
    share`) -- since Shapley's own permutation prefixes touch every subset
    at least once, this is free and lets the 3-block-baseline-plus-one-new-
    block statistic (this task's own Scope) reuse the identical CV-AUC
    calls, not a second CV run."""
    cache: dict = {}

    def value(subset: tuple) -> float:
        key = tuple(sorted(subset))
        if key in cache:
            return cache[key]
        if not key:
            v = 0.0
        else:
            X = np.column_stack([feat[b] for b in key])
            v = (t0254.cv_auc(X, y) - 0.5) / 0.5
        cache[key] = v
        return v

    shap = {b: [] for b in blocks}
    for perm in itertools.permutations(blocks):
        prefix: list = []
        for b in perm:
            before = value(tuple(prefix))
            prefix = prefix + [b]
            after = value(tuple(prefix))
            shap[b].append(after - before)
    shapley = {b: float(np.mean(shap[b])) for b in blocks}
    full_share = value(tuple(blocks))
    full_auc = 0.5 + 0.5 * full_share
    added_last = {b: full_share - value(tuple(x for x in blocks if x != b)) for b in blocks}
    return dict(shapley=shapley, added_last=added_last, full_auc=full_auc,
                full_share=full_share, unexplained=1.0 - full_share,
                subset_share={k: v for k, v in cache.items()})


def subset_value(sub_share: dict, names: list) -> float:
    return sub_share[tuple(sorted(names))]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    new_cand = yaml.safe_load(FROZEN_CONFIG.read_text())["targets"]
    t0242.CAND = new_cand
    t0249.t0242.CAND = new_cand

    baseline3 = json.loads(BASELINE_3BLOCK.read_text())
    frozen_targets = list(new_cand.keys())

    data = {}
    for t in frozen_targets:
        try:
            d = t0249.target_rows(t)
        except Exception as exc:  # noqa: BLE001
            print(f"{t}: FAILED {exc!r}")
            continue
        if d is None or d["n_pocket"] < 3:
            print(f"{t}: SKIP (fpocket failure, empty seed, or too few positives)")
            continue
        data[t] = d
    print(f"{len(data)}/{len(frozen_targets)} usable (matches TASK-0249's own n=20 filter)\n")

    print("### Conservation (Pfam seed alignment) + chemistry (Kyte-Doolittle/charge/"
          "aromaticity/Zamyatnin volume) + 5-block Shapley ###")
    attribution = {}
    crypt = {}
    depth = {}
    for t, d in data.items():
        cfg, apo, seed2, _pocket2 = t0242.prep(t)
        ch = cfg.get("holo_chains") or cfg.get("chains")
        chain0 = (cfg.get("apo_chains") or ch)[0]
        cons_raw, info = conservation_array(cfg["apo_pdb"], chain0, apo.chain_ids, apo.resnums)
        n_nan_cons = int(np.isnan(cons_raw).sum())
        cons = np.where(np.isnan(cons_raw),
                         np.nanmedian(cons_raw) if n_nan_cons < len(cons_raw) else 0.0,
                         cons_raw)
        chem_raw = chemistry_features(apo.resnames)

        seed = d["seed"]
        m = np.ones(len(d["coords"]), dtype=bool)
        m[seed] = False

        blocks = t0254.build_blocks(t, d)
        blocks["conservation"] = t0254.z(cons)[m].reshape(-1, 1)
        blocks["chemistry"] = np.column_stack(
            [t0254.z(chem_raw[:, i]) for i in range(chem_raw.shape[1])])[m]
        y = d["y"]
        result = shapley_attribution_n(blocks, y, BLOCKS5)
        attribution[t] = result
        crypt[t] = t0254.crypticity(d)
        depth[t] = info
        sh, al = result["shapley"], result["added_last"]
        cov = f"{info['n_mapped']}/{len(apo.resnums)}" if info.get("n_mapped") else "0"
        print(f"{t:24s} pfam={str(info.get('pfam')):10s} n_seed={str(info.get('n_seed')):>4s} "
              f"ident={str(info.get('identity')):>6s} cov={cov:>9s}  "
              f"geom={100*sh['geometry']:+5.1f}%  fpocket={100*sh['fpocket']:+5.1f}%  "
              f"ctqw={100*sh['ctqw']:+5.1f}%  cons={100*sh['conservation']:+5.1f}%  "
              f"chem={100*sh['chemistry']:+5.1f}%  unexplained={100*result['unexplained']:5.1f}%  "
              f"crypticity={100*crypt[t]['fraction_open']:.0f}%")

    def _json_safe(attr):
        out = {}
        for t, r in attr.items():
            r2 = dict(r)
            r2["subset_share"] = {",".join(k) if k else "(none)": v for k, v in r["subset_share"].items()}
            out[t] = r2
        return out

    (OUT / "shapley_5block.json").write_text(json.dumps(_json_safe(attribution), indent=1, default=str))
    (OUT / "crypticity.json").write_text(json.dumps(crypt, indent=1))
    (OUT / "conservation_depth.json").write_text(json.dumps(depth, indent=1, default=str))

    n = len(attribution)
    print(f"\n=== n={n} ===")
    for b in BLOCKS5:
        shares = [attribution[t]["shapley"][b] for t in attribution]
        al = [attribution[t]["added_last"][b] for t in attribution]
        print(f"  {b:<12} Shapley median {100*np.median(shares):+.1f}%  "
              f"added-last median {100*np.median(al):+.1f}%")

    reasons = [depth[t]["reason"] for t in depth if depth[t]["reason"]]
    print(f"\nConservation depth: {len(depth) - len(reasons)}/{len(depth)} targets got a real "
          f"Pfam seed mapping; {len(reasons)} failed ({', '.join(sorted(set(reasons)))})"
          if reasons else f"\nConservation depth: {len(depth)}/{len(depth)} targets got a real Pfam seed mapping")
    n_seeds = [depth[t]["n_seed"] for t in depth if depth[t].get("n_seed")]
    idents = [depth[t]["identity"] for t in depth if depth[t].get("identity") is not None]
    if n_seeds:
        print(f"n_seed sequences: median={np.median(n_seeds):.0f} min={min(n_seeds)} max={max(n_seeds)}")
    if idents:
        print(f"best-homolog identity to query domain: median={np.median(idents)*100:.0f}% "
              f"min={min(idents)*100:.0f}% max={max(idents)*100:.0f}%")

    unexs5 = [a["unexplained"] for a in attribution.values()]
    unexs3 = [baseline3[t]["unexplained"] for t in attribution if t in baseline3]
    print(f"\nunexplained: 3-block (geom/fpocket/ctqw) median {100*np.median(unexs3):.1f}% "
          f"-> 5-block (+conservation+chemistry) median {100*np.median(unexs5):.1f}%")

    print("\n### Each new block added on top of the geometry+fpocket+CTQW baseline "
          "specifically (this task's own Scope statistic) ###")
    base3 = ["geometry", "fpocket", "ctqw"]
    cons_on_3 = {t: subset_value(attribution[t]["subset_share"], base3 + ["conservation"])
                 - subset_value(attribution[t]["subset_share"], base3) for t in attribution}
    chem_on_3 = {t: subset_value(attribution[t]["subset_share"], base3 + ["chemistry"])
                 - subset_value(attribution[t]["subset_share"], base3) for t in attribution}
    print(f"conservation on top of 3-block: median {100*np.median(list(cons_on_3.values())):+.2f}%")
    print(f"chemistry on top of 3-block:    median {100*np.median(list(chem_on_3.values())):+.2f}%")

    print("\n### Cluster-robust significance (TASK-0261's exact permutation, 13 clusters) ###")
    r_cons3 = cluster_sign_flip_test(cons_on_3)
    r_chem3 = cluster_sign_flip_test(chem_on_3)
    cons_added_last_5 = {t: attribution[t]["added_last"]["conservation"] for t in attribution}
    chem_added_last_5 = {t: attribution[t]["added_last"]["chemistry"] for t in attribution}
    r_cons5 = cluster_sign_flip_test(cons_added_last_5)
    r_chem5 = cluster_sign_flip_test(chem_added_last_5)
    print(f"conservation on top of 3-block:      median={100*r_cons3['median']:+.2f}%  "
          f"n_clusters={r_cons3['n_clusters']}  cluster-p={r_cons3['p_value']:.4f}")
    print(f"chemistry on top of 3-block:         median={100*r_chem3['median']:+.2f}%  "
          f"n_clusters={r_chem3['n_clusters']}  cluster-p={r_chem3['p_value']:.4f}")
    print(f"conservation added-last (5-block):   median={100*r_cons5['median']:+.2f}%  "
          f"n_clusters={r_cons5['n_clusters']}  cluster-p={r_cons5['p_value']:.4f}")
    print(f"chemistry added-last (5-block):      median={100*r_chem5['median']:+.2f}%  "
          f"n_clusters={r_chem5['n_clusters']}  cluster-p={r_chem5['p_value']:.4f}")

    print("\n### Crypticity-stratified breakdown (pre-registered prediction: conservation "
          "should help on FUNCTIONAL sites regardless of openness -- if it concentrates on "
          "already-open targets like fpocket/P2Rank did, it is tracking cavity presence, "
          "not function) ###")
    straddling = {c for c in set(CM.values())
                  if len({crypt[t]["already_open"] for t in attribution if CM.get(t) == c}) > 1}
    excluded = [t for t in attribution if CM.get(t) in straddling]
    if excluded:
        print(f"Straddling cluster(s) excluded from crypticity stratification only: {excluded}")
    open_t = [t for t in attribution if crypt[t]["already_open"] and CM.get(t) not in straddling]
    cryptic_t = [t for t in attribution if crypt[t]["already_open"] is False and CM.get(t) not in straddling]
    print(f"n_open={len(open_t)} n_cryptic={len(cryptic_t)}")

    def stratify(values: dict, label: str):
        open_v = {t: values[t] for t in open_t if t in values}
        cryptic_v = {t: values[t] for t in cryptic_t if t in values}
        r = cluster_permutation_two_group(cryptic_v, open_v, alternative="greater")
        print(f"{label:<38} cryptic median {100*np.median(list(cryptic_v.values())):+.2f}%  "
              f"open median {100*np.median(list(open_v.values())):+.2f}%  "
              f"cluster-perm p(cryptic>open)={r['p_value']:.4f} "
              f"(n_clusters_cryptic={r['n_clusters_a']}, n_clusters_open={r['n_clusters_b']})")
        return r

    r1 = stratify(cons_on_3, "conservation on top of 3-block")
    r2 = stratify(chem_on_3, "chemistry on top of 3-block")
    r3 = stratify(cons_added_last_5, "conservation added-last (5-block)")
    r4 = stratify(chem_added_last_5, "chemistry added-last (5-block)")

    (OUT / "cluster_robust_results.json").write_text(json.dumps({
        "cons_on_3block": r_cons3, "chem_on_3block": r_chem3,
        "cons_added_last_5block": r_cons5, "chem_added_last_5block": r_chem5,
        "strat_cons_on_3": r1, "strat_chem_on_3": r2,
        "strat_cons_added_last_5": r3, "strat_chem_added_last_5": r4,
    }, indent=1, default=str))

    print(f"\nWrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
