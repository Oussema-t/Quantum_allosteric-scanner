"""Step 2 of the conservation arms: per-residue conservation for every chain of
every apo structure in the frozen-20.

Route (the one Experiment B pre-registered, now that egress permits it):
  UniProt acc -> InterPro Pfam families -> Pfam SEED alignment + family HMM
  -> hmmsearch the chain's entity sequence against the HMM to map residues onto
     match states
  -> Jensen-Shannon conservation (Capra & Singh 2007) per match state, computed
     on the seed with Henikoff position-based sequence weights
  -> score carried back to auth residue numbers.

Residues outside every Pfam domain get no score; coverage is reported, never
silently imputed.
"""
import gzip
import io
import json
import time
import urllib.request
from pathlib import Path

import numpy as np
import pyhmmer

STRUCT = Path("/home/claude/struct_map.json")
OUT = Path("/home/claude/conservation.json")
CACHE = Path("/home/claude/pfam_cache")
CACHE.mkdir(exist_ok=True)

AA = "ACDEFGHIKLMNPQRSTVWY"
AAI = {a: i for i, a in enumerate(AA)}
# BLOSUM62 background frequencies (Capra & Singh's q)
BG = np.array([0.078, 0.019, 0.054, 0.063, 0.039, 0.074, 0.023, 0.052, 0.059,
               0.096, 0.024, 0.042, 0.052, 0.043, 0.051, 0.071, 0.059, 0.066,
               0.014, 0.032])
BG = BG / BG.sum()


def _get(url, binary=False, tries=4):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "expB/1.0"})
            with urllib.request.urlopen(req, timeout=90) as r:
                raw = r.read()
            if binary:
                return raw
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            return raw.decode("utf-8", "replace")
        except Exception:  # noqa: BLE001
            if i == tries - 1:
                raise
            time.sleep(2 * (i + 1))
    return None


def cached(name, url):
    f = CACHE / name
    if f.exists():
        return f.read_text()
    txt = _get(url)
    f.write_text(txt)
    return txt


def pfam_for(acc):
    """Pfam families hit by a UniProt accession, via InterPro."""
    txt = cached(f"ipr_{acc}.json",
                 f"https://www.ebi.ac.uk/interpro/api/entry/pfam/protein/uniprot/{acc}/")
    d = json.loads(txt)
    return [r["metadata"]["accession"] for r in d.get("results", [])]


def read_stockholm(txt):
    """Return (ids, ungapped sequences) from a Stockholm file."""
    seqs = {}
    order = []
    for line in txt.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#") or line == "//":
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        name, chunk = parts
        if name not in seqs:
            seqs[name] = []
            order.append(name)
        seqs[name].append(chunk)
    full = {k: "".join(v) for k, v in seqs.items()}
    out = []
    for n in order:
        s = "".join(c for c in full[n].upper() if c.isalpha())
        if s:
            out.append((n, s))
    return out


def seed_match_matrix(hmm, seed_txt, alph):
    """hmmalign the seed to its own HMM and return the match-state-only column
    matrix (n_seq x M). Reading match states off the RF line is exact, unlike
    guessing from Stockholm case convention."""
    recs = read_stockholm(seed_txt)
    if not recs:
        return None
    ds = [pyhmmer.easel.TextSequence(name=n.encode(), sequence=s).digitize(alph)
          for n, s in recs]
    msa = pyhmmer.hmmer.hmmalign(hmm, ds)
    tm = msa.textize() if hasattr(msa, "textize") else msa
    rf = tm.reference
    if rf is None:
        return None
    keep = [i for i, c in enumerate(rf) if c != "."]
    if len(keep) != hmm.M:
        return None
    rows = [[str(a[i]).upper() for i in keep] for a in tm.alignment]
    return np.array(rows, dtype="U1")


def henikoff_weights(mat):
    """Position-based sequence weights (Henikoff & Henikoff 1994)."""
    n, L = mat.shape
    if n == 0:
        return np.ones(0)
    w = np.zeros(n)
    for j in range(L):
        col = mat[:, j]
        valid = np.array([c in AAI for c in col])
        if not valid.any():
            continue
        vals, counts = np.unique(col[valid], return_counts=True)
        r = len(vals)
        cmap = dict(zip(vals, counts))
        for i in range(n):
            if valid[i]:
                w[i] += 1.0 / (r * cmap[col[i]])
    if w.sum() <= 0:
        return np.ones(n) / n
    return w / w.sum()


def jsd_conservation(mat, w):
    """Per-column Jensen-Shannon divergence from background, gap-penalised."""
    n, L = mat.shape
    out = np.full(L, np.nan)
    for j in range(L):
        col = mat[:, j]
        p = np.zeros(20)
        gap_w = 0.0
        for i in range(n):
            c = col[i]
            if c in AAI:
                p[AAI[c]] += w[i]
            else:
                gap_w += w[i]
        tot = p.sum()
        if tot <= 0:
            out[j] = 0.0
            continue
        p = p / tot
        # small pseudocount to keep KL finite
        p = (p + 1e-9) / (1 + 20e-9)
        r = 0.5 * (p + BG)
        jsd = 0.5 * (np.sum(p * np.log2(p / r)) + np.sum(BG * np.log2(BG / r)))
        out[j] = jsd * (1.0 - gap_w)          # gap penalty, as in Capra & Singh
    return out


def load_family(pf):
    """Return (hmm, per-match-state conservation array, n_seed)."""
    hmm_txt = cached(f"{pf}.hmm",
                     f"https://www.ebi.ac.uk/interpro/wwwapi/entry/pfam/{pf}/?annotation=hmm")
    seed_txt = cached(f"{pf}.sto",
                      f"https://www.ebi.ac.uk/interpro/wwwapi/entry/pfam/{pf}/"
                      f"?annotation=alignment:seed")
    with pyhmmer.plan7.HMMFile(io.BytesIO(hmm_txt.encode())) as fh:
        hmm = fh.read()
    alph = pyhmmer.easel.Alphabet.amino()
    mat = seed_match_matrix(hmm, seed_txt, alph)
    if mat is None:
        return hmm, None, 0, 0
    w = henikoff_weights(mat)
    return hmm, jsd_conservation(mat, w), mat.shape[0], mat.shape[1]


def main():
    sm = json.loads(STRUCT.read_text())
    alph = pyhmmer.easel.Alphabet.amino()
    fam_cache = {}
    out = {}

    for pdb, rec in sorted(sm.items()):
        out[pdb] = {}
        for ch, cd in sorted(rec["chains"].items()):
            seq = cd["seq"]
            a2e = cd["auth_to_entity_poly_seq_mapping"]
            cons = np.full(len(seq), np.nan)
            fams_used = []
            for acc in cd["uniprot"]:
                for pf in pfam_for(acc):
                    if pf not in fam_cache:
                        fam_cache[pf] = load_family(pf)
                    hmm, cvec, nseed, ncol = fam_cache[pf]
                    if cvec is None:
                        print(f"    !! {pf} seed cols {ncol} != hmm M {hmm.M}; skipped")
                        continue
                    ds = pyhmmer.easel.DigitalSequence(
                        alph, name=f"{pdb}_{ch}".encode(),
                        sequence=pyhmmer.easel.TextSequence(
                            sequence=seq).digitize(alph).sequence)
                    hits = pyhmmer.hmmer.hmmsearch(
                        [hmm], [ds], alphabet=alph, E=1e-3)
                    nd = 0
                    for th in hits:
                        for hit in th:
                            for dom in hit.domains.included:
                                al = dom.alignment
                                si = al.target_from - 1     # 0-based seq index
                                hi = al.hmm_from - 1        # 0-based match state
                                for tch, hch in zip(al.target_sequence,
                                                    al.hmm_sequence):
                                    t_res = tch != "-"
                                    h_mat = hch != "."
                                    if t_res and h_mat:
                                        if np.isnan(cons[si]):
                                            cons[si] = cvec[hi]
                                        else:
                                            cons[si] = max(cons[si], cvec[hi])
                                    if t_res:
                                        si += 1
                                    if h_mat:
                                        hi += 1
                                nd += 1
                    if nd:
                        fams_used.append({"pfam": pf, "n_seed": nseed,
                                          "n_dom": nd, "M": hmm.M})
            # auth resnum -> conservation
            per_res = {}
            if a2e:
                for ei, auth in enumerate(a2e):
                    if ei < len(cons) and not np.isnan(cons[ei]):
                        try:
                            per_res[int(auth)] = float(cons[ei])
                        except (TypeError, ValueError):
                            pass
            cov = float(np.mean(~np.isnan(cons))) if len(cons) else 0.0
            out[pdb][ch] = {"uniprot": cd["uniprot"], "families": fams_used,
                            "coverage": cov, "n_scored": len(per_res),
                            "cons": per_res}
            print(f"{pdb} {ch}: cov={cov:.2f} scored={len(per_res)} "
                  f"fams={[f['pfam'] for f in fams_used]}")
    Path(OUT).write_text(json.dumps(out))
    print("\nwrote", OUT)


if __name__ == "__main__":
    main()
