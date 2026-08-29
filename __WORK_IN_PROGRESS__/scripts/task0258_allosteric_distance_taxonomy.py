"""Report the orthosteric<->allosteric relationship of every pocket, honestly,
instead of filtering on an arbitrary MIN_HOP.

Motivation. `MIN_HOP >= 2` entered this register as the two-stage design's
"distal" filter and was never justified physically. [[TASK-0255]] showed what
it actually means: hop 2 is a MEDIAN of 7.5 A (minimum 2.09 A) -- van der
Waals contact range, not allosteric separation. A binary filter on an
unjustified threshold also destroys information: it answers "is this pocket
distal enough?" when the useful question is "how far is it, and what KIND of
site is it?"

Allostery is not one thing. A drug binding a cryptic extension of the
catalytic cleft, a drug binding a distinct pocket on the same domain, and a
drug binding an oligomeric interface are three different mechanisms with
different modelling requirements -- and this register has been scoring all of
them against one label and one CTQW seed.

So: measure and report, do not filter.

MEASURES (per pocket, all on the apo structure, all heavy-atom not Ca --
side chains reach several Angstrom closer than Ca does, which is the whole
point of the finding this replaces):

  min_A       minimum heavy-atom distance from any pocket residue to any
              active-site residue. The load-bearing number: it is what
              catches a pocket that is "distal" by centroid but folds
              against the active site in 3D (TASK-0169's KRAS case, 3.75 A).
  centroid_A  centroid-to-centroid distance -- the number most papers quote,
              reported alongside min_A precisely so the two can disagree.
  min_hop     graph-hop distance, kept as a REPORTED COVARIATE so the old
              criterion stays auditable rather than silently dropped.
  contact_frac fraction of pocket residues within 8 A of the active site.
  same_chain  whether the pocket sits on the active site's own chain.

CATEGORY. Bin edges below are THIS REGISTER'S OWN, stated openly, chosen from
physical meaning rather than taken from a source we cannot verify -- do not
cite them as a literature taxonomy:

  orthosteric-overlapping  shares residues with the active site
  contact-adjacent         min < 4.5 A   -- vdW contact; one continuous
                           cavity in practice, an extension of the
                           orthosteric site rather than a separate site
  proximal                 4.5-12 A      -- separated, but one or two residue
                           layers apart; direct packing coupling plausible
  intermediate             12-20 A       -- no direct contact; coupling must
                           be transmitted through the protein
  remote                   > 20 A        -- genuinely long-range
  inter-chain              pocket lies on a different chain (reported
                           separately -- an oligomeric-interface mechanism,
                           which the challenge's catalytic-domain scope may
                           truncate outright, cf. [[TASK-0251]])

[[TASK-0262]], 2026-08-25: a literature "Type I-IV ALLOSTERIC SITE"
taxonomy (second-sphere/intra-domain/inter-domain/inter-subunit) was
sought, live, and NOT FOUND -- confirmed not to exist as a general
classification, and not something ASD itself defines (checked directly
against the ASD site). A real, differently-defined "Type I-IV" taxonomy
DOES exist, but for KINASE INHIBITORS relative to the ATP pocket (Dar &
Shokat 2011, Annu Rev Biochem 80:769-795, doi:10.1146/
annurev-biochem-090308-173656; extended by Gavrin & Saiah 2013,
MedChemComm 4:41-51, doi:10.1039/c2md20180a) -- ATP-competitive vs.
allosteric conformational state, not distance/structural-relationship
categories like these bins. Do not conflate the two under the same
"Type I-IV" label. Two of the four proposed exemplars also don't match
what this pipeline actually measures: BCR_ABL1's cited exemplar (SH2/SH3-
kinase interface, TASK-0229.003's real second site) is a DIFFERENT site
than the myristoyl pocket this script measures (proximal, 7.96 A);
CARDIAC_MYOSIN's cited "inter-subunit" classification doesn't match this
pipeline's own same_chain=True measurement -- the true SRX/IHM mechanism
is inter-subunit (TASK-0251), but the scope-truncated single-chain
construct this project actually scores is not. Our own bins stand,
undecorated. Full verification: [[TASK-0262]]'s own Done section.

[[TASK-0272]], 2026-08-26: this script's own stored KRAS_G12C output
(results/tasks/0258_allosteric_distance_taxonomy/) was last run against
`4OBE`, since found misannotated -- wild-type, not the real G12C mutant
([[TASK-0270]], organiser-sanctioned swap to `4LDJ`). This script calls
`prep()` against live `config/targets.yaml`, already updated to `4LDJ` --
re-running it today would use the corrected structure automatically, no
code change needed -- but the STORED artifact is stale relative to that
config and was not re-run here (a results-generating re-run, out of this
doc-fix task's own scope, not silently claimed as done). Checked, not
assumed: TASK-0270's own re-measured pocket-to-active-site min heavy-atom
distance for KRAS_G12C barely moves (1.32 A -> 1.31 A, both far inside
the 4.5 A BIN_CONTACT edge), so the "contact-adjacent" category label this
script assigns KRAS_G12C does not change even though the stored number
predates the fix.
"""
from __future__ import annotations
import json, sys, warnings
from pathlib import Path
import numpy as np
warnings.filterwarnings("ignore")
_ROOT = Path(__file__).resolve().parent.parent
for _p in (_ROOT/"src", _ROOT/"scripts", _ROOT.parent):
    if str(_p) not in sys.path: sys.path.insert(0, str(_p))
import prody; prody.confProDy(verbosity="none")

# Importing task0255 already leaves prody.parsePDB correctly composed
# (altloc="all" default wrapping allostery's own folder default) as a
# side effect of its own module-level patch dance -- re-assigning
# prody.parsePDB to its bare _parsePDB_all_altloc here (as this line used
# to) clobbers that composition and drops the folder default, since the
# function object's own closure was bound before allostery's patch ran.
# Silently scattered PDB fetches back into this process's cwd; found via
# TASK-0258/0259 sharing the identical bug. Do not re-add the assignment.
from task0255_hop_angstrom_calibration import min_heavy_atom_dist_to_seed
from task0242_two_stage_dryrun import prep, CAND
from allostery.baselines import hop_from_seed

# --- this register's own bin edges, stated not inherited ---
BIN_CONTACT, BIN_PROXIMAL, BIN_INTERMEDIATE = 4.5, 12.0, 20.0
CONTACT_FRAC_CUTOFF = 8.0

FROZEN = _ROOT/"config"/"candidate_targets_task0243.yaml"   # TASK-0243's frozen set
MANDATORY = ["KRAS_G12C", "BCR_ABL1", "CARDIAC_MYOSIN", "PTP1B", "GLUCOKINASE", "CASPASE7"]
OUT = _ROOT/"results/tasks/0258_allosteric_distance_taxonomy"


def categorise(min_A, overlaps, same_chain):
    if overlaps:                    return "orthosteric-overlapping"
    if not same_chain:              return "inter-chain"
    if min_A < BIN_CONTACT:         return "contact-adjacent"
    if min_A < BIN_PROXIMAL:        return "proximal"
    if min_A < BIN_INTERMEDIATE:    return "intermediate"
    return "remote"


def measure(t):
    cfg, apo, seed, pocket = prep(t)
    if pocket is None or pocket.sum() == 0 or len(seed) == 0:
        return {"target": t, "error": "no pocket or no seed"}
    coords = apo.coords
    cut = float(cfg.get("enm_cutoff", 8.0))
    d = min_heavy_atom_dist_to_seed(cfg, apo, seed)          # per-residue, heavy-atom
    hops = -hop_from_seed(coords, seed, cutoff=cut)
    pi = np.where(pocket)[0]
    dp = d[pi]; dp = dp[np.isfinite(dp)]
    if len(dp) == 0:
        return {"target": t, "error": "no resolved heavy atoms in pocket"}
    overlaps = bool(set(pi.tolist()) & set(seed.tolist()))
    ch = np.asarray(getattr(apo, "chids", None) if getattr(apo, "chids", None) is not None
                    else ["A"]*len(coords))
    same_chain = bool(set(ch[pi]) & set(ch[seed]))
    cen = float(np.linalg.norm(coords[pi].mean(0) - coords[seed].mean(0)))
    min_A = float(dp.min())
    return {
        "target": t, "n_pocket": int(pocket.sum()), "n_seed": int(len(seed)),
        "min_A": min_A, "median_A": float(np.median(dp)), "max_A": float(dp.max()),
        "centroid_A": cen,
        "min_hop": int(hops[pi].min()), "median_hop": float(np.median(hops[pi])),
        "contact_frac": float((dp < CONTACT_FRAC_CUTOFF).mean()),
        "same_chain": same_chain, "overlaps_active_site": overlaps,
        "category": categorise(min_A, overlaps, same_chain),
        "passes_old_min_hop_2": bool(hops[pi].min() >= 2),
        # TASK-0290: provenance of the active-site seed that produced
        # min_A/category above -- `prep()`'s own new `active_site_source`
        # (previously discarded), so a reader can audit which tier
        # answered without re-running anything.
        "active_site_source": cfg.get("active_site_source"),
    }


def main():
    import yaml
    targets = list(CAND)
    if FROZEN.exists():
        fz = yaml.safe_load(FROZEN.read_text()).get("targets") or {}
        CAND.update(fz)
        targets = list(fz) + [t for t in targets if t not in fz]
    # the register's own long-standing targets, scored here for the first time
    # under this measure -- they are the ones every published number rests on
    targets = targets + [t for t in MANDATORY if t not in targets]
    OUT.mkdir(parents=True, exist_ok=True)

    rows = []
    for t in targets:
        try:
            rows.append(measure(t))
        except Exception as e:
            rows.append({"target": t, "error": f"{type(e).__name__}: {e}"})
    ok = [r for r in rows if "error" not in r]

    print(f"{'target':<24}{'min_A':>7}{'cen_A':>7}{'hop':>5}{'ctc%':>6}  {'category':<24}{'old MIN_HOP>=2':>15}")
    for r in sorted(ok, key=lambda r: r["min_A"]):
        print(f"{r['target']:<24}{r['min_A']:>7.2f}{r['centroid_A']:>7.1f}{r['min_hop']:>5}"
              f"{100*r['contact_frac']:>5.0f}%  {r['category']:<24}"
              f"{('PASS' if r['passes_old_min_hop_2'] else 'filtered out'):>15}")

    from collections import Counter
    cnt = Counter(r["category"] for r in ok)
    print(f"\n  n={len(ok)} scoreable ({len(rows)-len(ok)} unusable)")
    for k, v in cnt.most_common():
        print(f"    {k:<26} {v:>3}  ({100*v/len(ok):>4.0f}%)")
    dis = sum(1 for r in ok if r["category"] in ("intermediate", "remote"))
    print(f"\n  genuinely separated (intermediate or remote): {dis}/{len(ok)} = {100*dis/len(ok):.0f}%")
    # what the retired filter was actually doing
    agree = sum(1 for r in ok if r["passes_old_min_hop_2"] ==
                (r["category"] in ("proximal", "intermediate", "remote")))
    kept_contact = sum(1 for r in ok if r["passes_old_min_hop_2"] and r["category"] == "contact-adjacent")
    print(f"  old MIN_HOP>=2 kept {kept_contact} contact-adjacent pocket(s) it should have excluded;"
          f" agrees with the distance categories on {agree}/{len(ok)}")
    (OUT/"pocket_taxonomy.json").write_text(json.dumps(rows, indent=1))
    print(f"\n  written: {OUT/'pocket_taxonomy.json'}")


if __name__ == "__main__":
    raise SystemExit(main())
