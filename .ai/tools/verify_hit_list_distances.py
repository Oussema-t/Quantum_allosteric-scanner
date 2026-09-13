"""Recompute the shipped hit lists' distances to the validated pockets.

Filed with TASK-0385. Exists because the 2026-09-13 external adversarial review
asked us to PRINT its distance numbers in the Concept Proposal, and two of them
do not reproduce -- so the submission must quote numbers we computed ourselves.

Method: heavy-atom minimum distance, altloc A only, hydrogens excluded.
Truth pocket = residues within 5.0 A of the validation ligand (MYR in 1OPL,
MOV/sotorasib in 6OIM, XB2/mavacamten in 8QYR). Structures from pdb_cache/.

Reproduces the external review's truth pockets residue-for-residue on all three
targets. Diverges on two of its distance claims -- see TASK-0385 section
"TWO CORRECTIONS".

Run:  python3 .ai/tools/verify_hit_list_distances.py
"""
import math, gzip, os
CACHE="/Users/bartoszchmura/DELETE/QAS/Quantum_allosteric-scanner/pdb_cache"
AA=set("ALA ARG ASN ASP CYS GLN GLU GLY HIS ILE LEU LYS MET PHE PRO SER THR TRP TYR VAL MSE".split())

def load(pdb):
    p=os.path.join(CACHE,pdb+".pdb")
    op=gzip.open if p.endswith(".gz") else open
    prot={}; lig={}
    for ln in op(p,'rt',errors='ignore'):
        rec=ln[:6]
        if rec not in ("ATOM  ","HETATM"): continue
        if ln[76:78].strip()=="H": continue
        alt=ln[16]
        if alt not in (" ","A"): continue
        rn=ln[17:20].strip(); ch=ln[21]; rs=ln[22:26].strip()
        xyz=(float(ln[30:38]),float(ln[38:46]),float(ln[46:54]))
        if rn in AA and rec=="ATOM  ":
            prot.setdefault((ch,int(rs)),[]).append(xyz)
        elif rn not in ("HOH","DOD"):
            lig.setdefault(rn,[]).append(xyz)
    return prot,lig

def d(a,b): return math.dist(a,b)
def mind(A,B): return min(d(x,y) for x in A for y in B)

def pocket(prot,ligatoms,chain,cut=5.0):
    return sorted(r for (c,r),ats in prot.items() if c==chain and mind(ats,ligatoms)<cut)

def report(name, apo_pdb, apo_chain, hits, truth_res, truth_src, orth_atoms, orth_name):
    prot,_=load(apo_pdb)
    tp=[prot[(apo_chain,r)] for r in truth_res if (apo_chain,r) in prot]
    print(f"\n=== {name} ({apo_pdb} chain {apo_chain}) ===")
    print(f"truth pocket from {truth_src}: {len(truth_res)} res, {len(tp)} present in apo")
    print(f"{'rank':<5}{'res':<7}{'->pocket':>10}{'->'+orth_name:>14}")
    for i,r in enumerate(hits,1):
        if (apo_chain,r) not in prot: print(f"#{i:<4}{r:<7}{'ABSENT':>10}"); continue
        a=prot[(apo_chain,r)]
        dp=min(mind(a,t) for t in tp) if tp else float('nan')
        do=mind(a,orth_atoms) if orth_atoms else float('nan')
        print(f"#{i:<4}{r:<7}{dp:>10.1f}{do:>14.1f}")

# ---------- BCR-ABL1: truth = MYR contacts in 1OPL itself ----------
prot,lig=load("1OPL")
print("1OPL ligands:", {k:len(v) for k,v in lig.items()})
myr=lig.get("MYR",[])
tp_abl=pocket(prot,myr,"A") if myr else []
print("MYR pocket (1OPL A):", tp_abl)
p16=lig.get("P16",[])
report("BCR_ABL1","1OPL","A",[402,311,310,301,338],tp_abl,"MYR in 1OPL",p16,"P16")

# ---------- KRAS: truth = sotorasib(MOV) contacts in 6OIM ----------
prot6,lig6=load("6OIM")
print("\n6OIM ligands:", {k:len(v) for k,v in lig6.items()})
mov=lig6.get("MOV",[])
ch6=sorted({c for (c,r) in prot6})[0]
tp_kras=pocket(prot6,mov,ch6) if mov else []
print(f"switch-II pocket (6OIM {ch6}):",tp_kras)
prot4,lig4=load("4LDJ")
print("4LDJ ligands:", {k:len(v) for k,v in lig4.items()})
gdpmg=lig4.get("GDP",[])+lig4.get("MG",[])
ch4=sorted({c for (c,r) in prot4})[0]
report("KRAS_G12C","4LDJ",ch4,[31,122,33,121,29],tp_kras,f"MOV in 6OIM",gdpmg,"GDP/Mg")

# ---------- Cardiac: truth = mavacamten contacts in 8QYR ----------
protR,ligR=load("8QYR")
print("\n8QYR ligands:", {k:len(v) for k,v in ligR.items()})
mav=None
for code in ("XB2","MAV"):
    if code in ligR: mav=ligR[code]; mavcode=code; break
chR=sorted({c for (c,r) in protR})[0]
tp_myo=pocket(protR,mav,chR) if mav else []
print(f"mavacamten pocket (8QYR {chR}):",tp_myo)
protP,ligP=load("8QYP")
print("8QYP ligands:", {k:len(v) for k,v in ligP.items()})
nuc=ligP.get("ADP",[])+ligP.get("VO4",[])+ligP.get("MG",[])
chP=sorted({c for (c,r) in protP})[0]
report("CARDIAC_MYOSIN","8QYP",chP,[682,683,681,680,133],tp_myo,"mavacamten in 8QYR",nuc,"ADP/VO4/Mg")
