"""TASK-0284, Part B -- the one structural explanation not yet tested for
the near/far allosteric-site-distance bimodality ([[task0284_bimodality_
and_nulls]]): does the allosteric site sit in a DIFFERENT Pfam domain from
the active site?

Pre-registered prediction (task file, filed before this ran): far-cluster
targets are cross-domain, near-cluster targets are same-domain. Tested as
one 2x2 Fisher exact over the 32/33 scoreable targets a Pfam domain call
could actually be resolved for (SUMO_E1_FHJ excluded -- see below). Not a
sweep -- one source, one rule, one test, per the task's own "do not go
descriptor-fishing" constraint.

**A first pass without the InterPro/SIFTS fallback and asym_id resolution
below (both added after seeing the first result, disclosed not hidden)
resolved only 24/33 and reported HOLDS at p=0.018 -- driven entirely by a
coverage gap that happened to delete all 4 HCV_NS5B rows (the far
cluster's single largest subgroup) because RCSB's own bundled Pfam feature
is empty for that entity, not because those targets lack real domain
annotation.** Caught before trusting it: adding the fallback resolved
HCV_NS5B (RCSB's Pfam feed is empty for 2GIQ/2HAI's entity but InterPro's
own Pfam-by-UniProt lookup finds "Viral RNA dependent RNA polymerase"
directly) and TEM-1 beta-lactamase and HIV-1 RT the same way, taking
resolution to 32/33 -- at which point the result FLIPS to FAILS. The
lesson generalises: an unresolved-target count is not a nuisance
denominator footnote here, it was the entire effect.

SOURCE, verified live: RCSB Data API's own Pfam feature annotation per
polymer entity (`GET /rest/v1/core/polymer_entity/{pdb}/{entity}`, field
`rcsb_polymer_entity_feature` type=="Pfam", positions in ENTITY seq_id),
mapped to author residue numbers via the matching `polymer_entity_instance`
endpoint's own `auth_to_entity_poly_seq_mapping` (index i = entity seq_id
i+1 -> auth_seq_num string, empty for unmodeled positions) -- checked
directly against 4LDJ (KRAS): a single Pfam domain "Ras family (Ras)"
covering nearly the whole 170-residue chain, entity seq_id 6-166 mapping
exactly to auth 5-165 (off-by-one from an N-terminal cloning-tag residue),
confirming the mapping arithmetic before trusting it at scale. CATH was
tried first and abandoned: cathdb.info's REST domain-summary endpoint
returns "page not found" for a 2024+ deposition (8QYP) -- CATH's own
release lags recent PDB entries, unlike RCSB's continuously-updated Pfam
feed -- so Pfam is the one source actually usable live across this
register's targets, not a preference exercised for its own sake.

CAVEAT, stated not hidden: Pfam domains are SEQUENCE-FAMILY boundaries,
coarser than a structural-domain parser for large multi-lobed proteins --
CARDIAC_MYOSIN's own motor domain is one Pfam entry ("Myosin_head",
residues 87-766 of a 780-residue chain) even though the real motor head
has several structurally distinct subdomains (upper/lower 50 kDa,
converter). A same-domain call from this test therefore means "same Pfam
family region", not "same structural lobe" -- reported as such.

Cross-chain pockets (different auth_asym_id from the active site) are
scored cross-domain by construction -- a different chain is definitionally
not the same domain -- using `task0258_allosteric_distance_taxonomy`'s own
`same_chain` field, not re-derived.
"""
from __future__ import annotations
import json, sys, time, warnings
from pathlib import Path
import numpy as np
import requests
warnings.filterwarnings("ignore")
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT / "src", _ROOT / "scripts", _ROOT.parent):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import prody
prody.confProDy(verbosity="none")

from task0255_hop_angstrom_calibration import min_heavy_atom_dist_to_seed  # noqa: F401
from task0242_two_stage_dryrun import prep, CAND
from task0258_allosteric_distance_taxonomy import measure as t0258_measure, MANDATORY

FROZEN = _ROOT / "config" / "candidate_targets_task0243.yaml"
OUT = _ROOT / "results/tasks/0284_two_populations"
BIMODALITY_JSON = OUT / "bimodality_and_nulls.json"
DATA_API = "https://data.rcsb.org/rest/v1/core"

_entity_cache: dict = {}
_instance_cache: dict = {}
_interpro_cache: dict = {}
_entry_asym_cache: dict = {}
INTERPRO_API = "https://www.ebi.ac.uk/interpro/api/entry/pfam/protein/uniprot"


def _get_json(url, timeout=10):
    r = requests.get(url, timeout=timeout)
    if r.status_code != 200:
        return None
    return r.json()


def _resolve_asym(pdb_id: str, auth_chain: str):
    """auth_asym_id (author chain letter, what ProDy/apo.chain_ids use) ->
    (entity_id, label_asym_id) for the RCSB instance endpoint, which keys
    on label_asym_id, NOT auth_asym_id -- the two differ for some entries
    (checked live: 4DEM's only polymer entity has auth_asym_id "F" but
    label_asym_id "A"; a same-string guess 404s there while working by
    coincidence everywhere else). Caches the whole entry's mapping."""
    if pdb_id in _entry_asym_cache:
        m = _entry_asym_cache[pdb_id]
    else:
        entry = _get_json(f"{DATA_API}/entry/{pdb_id}")
        time.sleep(0.15)
        m = {}
        if entry:
            for eid in (entry.get("rcsb_entry_container_identifiers") or {}).get("polymer_entity_ids") or []:
                ent = _entity(pdb_id, eid)
                if ent is None:
                    continue
                ci = ent.get("rcsb_polymer_entity_container_identifiers") or {}
                asym_ids = ci.get("asym_ids") or []
                auth_ids = ci.get("auth_asym_ids") or []
                for a_id, auth_id in zip(asym_ids, auth_ids):
                    m[auth_id] = (eid, a_id)
        _entry_asym_cache[pdb_id] = m
    return m.get(auth_chain)


def _instance(pdb_id: str, chain: str):
    key = (pdb_id, chain)
    if key in _instance_cache:
        return _instance_cache[key]
    resolved = _resolve_asym(pdb_id, chain)
    asym = resolved[1] if resolved else chain
    d = _get_json(f"{DATA_API}/polymer_entity_instance/{pdb_id}/{asym}")
    time.sleep(0.15)
    _instance_cache[key] = d
    return d


def _entity(pdb_id: str, entity_id: str):
    key = (pdb_id, entity_id)
    if key in _entity_cache:
        return _entity_cache[key]
    d = _get_json(f"{DATA_API}/polymer_entity/{pdb_id}/{entity_id}")
    time.sleep(0.15)
    _entity_cache[key] = d
    return d


def _entity_seq_range_to_auth(mapping: list, beg: int, end: int) -> set:
    resnums = set()
    for seq_id in range(int(beg), int(end) + 1):
        idx = seq_id - 1
        if 0 <= idx < len(mapping) and mapping[idx] != "":
            try:
                resnums.add(int(mapping[idx]))
            except ValueError:
                pass
    return resnums


def _interpro_pfam(accession: str):
    key = accession.lower()
    if key in _interpro_cache:
        return _interpro_cache[key]
    d = _get_json(f"{INTERPRO_API}/{accession}/?page_size=100")
    time.sleep(0.25)
    _interpro_cache[key] = d
    return d


def _pfam_via_uniprot_sifts(ent: dict, mapping: list):
    """Fallback for entries where RCSB's own bundled `rcsb_polymer_entity_
    feature` carries no Pfam (checked live: genuinely empty for e.g. TEM-1
    beta-lactamase 1YT4, HCV NS5B 2GIQ/2HAI, HIV-1 RT 1DLO -- not a bug in
    this script, RCSB's own Pfam feature-aggregation coverage gap for these
    entries). Reads the entity's own SIFTS UniProt alignment
    (`rcsb_polymer_entity_align`) already present in `ent`, queries
    InterPro's Pfam-by-UniProt endpoint directly, and converts each
    fragment's UniProt coordinates to entity seq_id via the SIFTS offset
    before reusing the same auth-mapping step as the direct path. Same
    general strategy (UniProt -> InterPro Pfam) [[TASK-0274]] already
    established live for conservation, applied here to domain features
    instead of conservation entropy."""
    aligns = [a for a in (ent.get("rcsb_polymer_entity_align") or [])
              if a.get("provenance_source") == "SIFTS" and a.get("reference_database_name") == "UniProt"]
    if not aligns:
        return []
    accession = aligns[0].get("reference_database_accession")
    regions = aligns[0].get("aligned_regions") or []
    if not accession or not regions:
        return []
    ipr = _interpro_pfam(accession)
    if not ipr or not ipr.get("results"):
        return []
    domains = []
    for entry in ipr["results"]:
        name = entry.get("metadata", {}).get("name") or entry.get("metadata", {}).get("accession")
        resnums = set()
        for prot in entry.get("proteins") or []:
            for loc in prot.get("entry_protein_locations") or []:
                for frag in loc.get("fragments") or []:
                    u_beg, u_end = frag.get("start"), frag.get("end")
                    if u_beg is None or u_end is None:
                        continue
                    for reg in regions:
                        r_beg = reg.get("ref_beg_seq_id"); r_len = reg.get("length")
                        e_beg = reg.get("entity_beg_seq_id")
                        if r_beg is None or r_len is None or e_beg is None:
                            continue
                        r_end = r_beg + r_len - 1
                        lo = max(u_beg, r_beg); hi = min(u_end, r_end)
                        if lo > hi:
                            continue
                        offset = e_beg - r_beg
                        resnums |= _entity_seq_range_to_auth(mapping, lo + offset, hi + offset)
        if resnums:
            domains.append((name, resnums))
    return domains


def pfam_domains_for_chain(pdb_id: str, chain: str):
    """Returns list of (name, set_of_auth_resnums) Pfam domains for one
    chain, live-verified against RCSB (falling back to InterPro-by-SIFTS-
    UniProt when RCSB's own bundled feature is empty -- see
    `_pfam_via_uniprot_sifts`). Empty list if no Pfam annotation is found
    via either route; None if the chain/entry could not be resolved at
    all."""
    inst = _instance(pdb_id, chain)
    if inst is None:
        return None  # entry/chain not resolvable -- distinct from "resolvable, no Pfam"
    ci = inst.get("rcsb_polymer_entity_instance_container_identifiers") or {}
    entity_id = ci.get("entity_id")
    mapping = ci.get("auth_to_entity_poly_seq_mapping")
    if entity_id is None or not mapping:
        return None
    ent = _entity(pdb_id, entity_id)
    if ent is None:
        return None
    feats = ent.get("rcsb_polymer_entity_feature") or []
    domains = []
    for f in feats:
        if f.get("type") != "Pfam":
            continue
        name = f.get("name") or f.get("annotation_id")
        resnums = set()
        for pos in f.get("feature_positions") or []:
            beg = pos.get("beg_seq_id"); end = pos.get("end_seq_id", beg)
            if beg is None:
                continue
            resnums |= _entity_seq_range_to_auth(mapping, beg, end)
        if resnums:
            domains.append((name, resnums))
    if not domains:
        domains = _pfam_via_uniprot_sifts(ent, mapping)
    return domains


def _majority_domain(resnums: list, domains: list):
    """Which domain index (or None) holds most of `resnums`. Ties broken by
    first domain in RCSB's own listed order."""
    if not domains:
        return None, 0, 0
    counts = [len(set(resnums) & dom_resnums) for _, dom_resnums in domains]
    total_hit = sum(counts)
    if total_hit == 0:
        return None, 0, 0
    best = int(np.argmax(counts))
    return best, counts[best], total_hit


def classify_target(t: str, tax_row: dict) -> dict:
    cfg, apo, seed, pocket = prep(t)
    resnums = np.asarray(apo.resnums)
    chain_ids = np.asarray(apo.chain_ids)
    seed_chains = sorted(set(chain_ids[seed].tolist()))
    pi = np.where(pocket)[0]
    pocket_chains = sorted(set(chain_ids[pi].tolist()))

    shared_chains = sorted(set(seed_chains) & set(pocket_chains))
    if not tax_row.get("same_chain", True) or not shared_chains:
        return dict(target=t, pdb=cfg["apo_pdb"], cross_domain=True,
                    reason="different chain (oligomeric interface)",
                    n_domains=None, seed_domain=None, pocket_domain=None)

    # the chain shared by seed and pocket (task0258's own same_chain guarantees
    # at least one exists); first in sorted order if more than one
    chain = shared_chains[0]
    domains = pfam_domains_for_chain(cfg["apo_pdb"], chain)
    if domains is None:
        return dict(target=t, pdb=cfg["apo_pdb"], cross_domain=None,
                    reason="RCSB entity/instance not resolvable", n_domains=None,
                    seed_domain=None, pocket_domain=None)
    if len(domains) == 0:
        return dict(target=t, pdb=cfg["apo_pdb"], cross_domain=None,
                    reason="no Pfam annotation for this chain", n_domains=0,
                    seed_domain=None, pocket_domain=None)

    seed_rn = resnums[seed][chain_ids[seed] == chain].tolist()
    pocket_idx = pi[chain_ids[pi] == chain]
    pocket_rn = resnums[pocket_idx].tolist()

    s_dom, s_hit, s_tot = _majority_domain(seed_rn, domains)
    p_dom, p_hit, p_tot = _majority_domain(pocket_rn, domains)
    if s_dom is None or p_dom is None:
        return dict(target=t, pdb=cfg["apo_pdb"], cross_domain=None,
                    reason="active site or pocket residues fall outside annotated Pfam domain(s)",
                    n_domains=len(domains), seed_domain=None, pocket_domain=None)

    cross = bool(s_dom != p_dom)
    return dict(target=t, pdb=cfg["apo_pdb"], chain=chain, cross_domain=cross,
                n_domains=len(domains), domain_names=[n for n, _ in domains],
                seed_domain=domains[s_dom][0], seed_domain_coverage=f"{s_hit}/{len(seed_rn)}",
                pocket_domain=domains[p_dom][0], pocket_domain_coverage=f"{p_hit}/{len(pocket_rn)}",
                reason=None)


def _load_targets():
    import yaml
    targets = list(CAND)
    if FROZEN.exists():
        fz = yaml.safe_load(FROZEN.read_text()).get("targets") or {}
        CAND.update(fz)
        targets = list(fz) + [t for t in targets if t not in fz]
    targets = targets + [t for t in MANDATORY if t not in targets]
    return targets


def main():
    from scipy.stats import fisher_exact

    if not BIMODALITY_JSON.exists():
        print(f"ERROR: {BIMODALITY_JSON} missing -- run task0284_bimodality_and_nulls.py first")
        return 1
    bim = json.loads(BIMODALITY_JSON.read_text())
    near_set = set(bim["near_targets"])
    far_set = set(bim["far_targets"])
    tax_by_target = {r["target"]: r for r in bim["rows"] if "error" not in r}

    targets = _load_targets()
    OUT.mkdir(parents=True, exist_ok=True)

    rows = []
    for t in targets:
        if t not in tax_by_target:
            continue
        try:
            rows.append(classify_target(t, tax_by_target[t]))
        except Exception as e:
            rows.append(dict(target=t, error=f"{type(e).__name__}: {e}"))

    print(f"{'target':<24}{'pdb':<7}{'domains':>8}  {'seed_domain':<32}{'pocket_domain':<32}{'cross?':>7}  reason")
    for r in rows:
        if "error" in r:
            print(f"{r['target']:<24}ERROR: {r['error']}")
            continue
        cd = r["cross_domain"]
        cds = "?" if cd is None else ("YES" if cd else "no")
        print(f"{r['target']:<24}{r['pdb']:<7}{str(r.get('n_domains')):>8}  "
              f"{str(r.get('seed_domain'))[:30]:<32}{str(r.get('pocket_domain'))[:30]:<32}{cds:>7}  {r.get('reason') or ''}")

    resolved = [r for r in rows if "error" not in r and r["cross_domain"] is not None]
    unresolved = [r for r in rows if "error" in r or r["cross_domain"] is None]
    print(f"\n  resolved: {len(resolved)}/{len(rows)}  unresolved: {len(unresolved)}")
    for r in unresolved:
        print(f"    unresolved: {r['target']}: {r.get('reason', r.get('error'))}")

    # 2x2: rows = near/far (data-derived split), cols = same-domain/cross-domain
    a = sum(1 for r in resolved if r["target"] in far_set and r["cross_domain"])       # far, cross
    b = sum(1 for r in resolved if r["target"] in far_set and not r["cross_domain"])   # far, same
    c = sum(1 for r in resolved if r["target"] in near_set and r["cross_domain"])      # near, cross
    d = sum(1 for r in resolved if r["target"] in near_set and not r["cross_domain"])  # near, same
    table = [[a, b], [c, d]]
    odds, p_two = fisher_exact(table, alternative="two-sided")
    _, p_greater = fisher_exact(table, alternative="greater")

    print(f"\n### 2x2 (data-derived near/far split, resolved targets only, n={len(resolved)}) ###")
    print(f"                 cross-domain   same-domain")
    print(f"  far-cluster    {a:>12}   {b:>11}")
    print(f"  near-cluster   {c:>12}   {d:>11}")
    print(f"  Fisher exact: odds_ratio={odds:.3f}  p_two_sided={p_two:.4f}  "
          f"p_one_sided(far->cross)={p_greater:.4f}")

    verdict = "HOLDS" if p_two < 0.05 and a >= b and d >= c else "FAILS"
    print(f"\n  pre-registered prediction (far=cross-domain, near=same-domain): {verdict}")

    result = dict(rows=rows, table_far_cross=a, table_far_same=b,
                  table_near_cross=c, table_near_same=d,
                  odds_ratio=float(odds), p_two_sided=float(p_two),
                  p_one_sided_greater=float(p_greater), n_resolved=len(resolved),
                  n_unresolved=len(unresolved), verdict=verdict)
    (OUT / "domain_architecture.json").write_text(json.dumps(result, indent=1))
    print(f"\n  written: {OUT / 'domain_architecture.json'}")


if __name__ == "__main__":
    raise SystemExit(main())
