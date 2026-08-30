"""Run the freshly built fpocket 4.2.3 on the regenerated apo inputs, keep the
alpha-sphere coordinates (which the cache does not contain), and validate the
build by matching hyd_cache.json's candidate counts exactly.
"""
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

UP = Path("/mnt/user-data/uploads")
HYD = json.loads((UP / "hyd_cache.json").read_text())
APO = Path("/home/claude/apo")
OUT = Path("/home/claude/fp_out")
OUT.mkdir(exist_ok=True)
FPOCKET = "/home/claude/fpocket_src/bin/fpocket"
FIELD_RE = re.compile(r"^\s*(.+?)\s*:\s*([-\d.eE+]+)\s*$")


def parse_vert(path):
    """Alpha-sphere centres from pocketN_vert.pqr."""
    pts = []
    if not path.exists():
        return pts
    for line in path.read_text().splitlines():
        if line.startswith(("ATOM", "HETATM")):
            try:
                pts.append([float(line[30:38]), float(line[38:46]),
                            float(line[46:54])])
            except ValueError:
                pass
    return pts


def run(target, flags, tag):
    src = APO / f"{target}_apo.pdb"
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        shutil.copy(src, tmp / src.name)
        subprocess.run([FPOCKET, "-f", src.name] + flags, cwd=tmp,
                       capture_output=True, timeout=3600)
        od = tmp / f"{src.stem}_out"
        info = od / f"{src.stem}_info.txt"
        if not info.exists():
            return None
        parts = re.split(r"^Pocket (\d+) :\s*$", info.read_text(),
                         flags=re.MULTILINE)[1:]
        out = []
        for pid, body in zip(parts[0::2], parts[1::2]):
            rec = {"id": int(pid)}
            for line in body.splitlines():
                m = FIELD_RE.match(line)
                if m:
                    k = re.sub(r"[^a-z0-9]+", "_",
                               m.group(1).strip().lower()).strip("_")
                    try:
                        rec[k] = float(m.group(2))
                    except ValueError:
                        pass
            res = set()
            f = od / "pockets" / f"pocket{pid}_atm.pdb"
            if f.exists():
                for line in f.read_text().splitlines():
                    if line.startswith(("ATOM", "HETATM")):
                        try:
                            res.add(int(line[22:26]))
                        except ValueError:
                            pass
            if not res:
                continue
            rec["resnums"] = sorted(res)
            rec["vert"] = parse_vert(od / "pockets" / f"pocket{pid}_vert.pqr")
            out.append(rec)
    return out


def main():
    settings = [("", []), ("-m_2.8", ["-m", "2.8"])]
    store = {}
    ok = tot = 0
    print(f"  {'target':<20}{'setting':<9}{'ncand':>6}{'cached':>8}  match")
    for tag, flags in settings:
        for t in HYD:
            t = t.split("|")[0]
            if f"{t}|{tag}" in store:
                continue
            pk = run(t, flags, tag)
            key = f"{t}|apo|{tag}"
            want = len(HYD[key])
            good = pk is not None and len(pk) == want
            ok += good
            tot += 1
            store[f"{t}|{tag}"] = pk
            print(f"  {t:<20}{tag or 'default':<9}{len(pk or []):>6}{want:>8}"
                  f"  {'OK' if good else 'MISMATCH'}", flush=True)
    Path("/home/claude/fp_full.json").write_text(json.dumps(store))
    print(f"\n  {ok}/{tot} runs reproduce the cached candidate counts")
    return 0 if ok == tot else 1


if __name__ == "__main__":
    sys.exit(main())
