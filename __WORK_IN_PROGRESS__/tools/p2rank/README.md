# P2Rank (TASK-0260 external dependency)

Prebuilt release, no build step — `p2rank_2.5.1/` is gitignored (matching
`tools/fpocket`'s own established convention: the binary is never version
controlled, only this fetch recipe is), fetch locally with:

```bash
curl -sL "https://github.com/rdk/p2rank/releases/download/2.5.1/p2rank_2.5.1.tar.gz" -o p2rank.tar.gz
tar xzf p2rank.tar.gz
rm p2rank.tar.gz
```

Requires a JVM (tested against OpenJDK 21) — no other runtime dependency.
Citation-verified (Krivák & Hoksza 2018, *J. Cheminform.* 10:39, DOI
10.1186/s13321-018-0285-8) and confirmed Constraint-3-legal (supervised ML
on labelled bound structures, no MD anywhere, training or inference) in
[[TASK-0260]]'s own Done section before use.

Used by `scripts/task0260_cryptic_predictor_residual.py`
(`P2RANK_BIN = tools/p2rank/p2rank_2.5.1/prank`).

Invocation: `./prank predict -f <apo.pdb> -o <out_dir>` writes
`<pdb>_residues.csv` (per-residue chain/resnum/probability — the per-residue
ligandability score this project's own scoring uses) and
`<pdb>_predictions.csv` (per-pocket-candidate score/probability/residue
list), ~8-15s per real target on this project's own frozen-set structures.

## Docker (TASK-0285)

`p2rank_2.5.1/prank` is now a small Python wrapper, not the native launcher
script — a drop-in replacement at the exact path
`scripts/task0260_cryptic_predictor_residual.py`'s `P2RANK_BIN` already
points to; no caller changes, and a host JVM is no longer required (only
Docker). The original native launcher is kept at
`p2rank_2.5.1/prank.native-backup` (host-local, gitignored, not relied on).

Build:

```bash
cd tools/p2rank
docker build --platform linux/amd64 -t qas-p2rank:2.5.1 .
```

`eclipse-temurin:21-jre-jammy`, matching this README's own already-tested
OpenJDK 21 pin, base image pinned by digest (see
`tools/fpocket/Dockerfile`'s own comment for why). The same pinned
release URL above is fetched once at *image build* time, not per
invocation — the release payload (jars/models) never needs re-downloading
on a machine that has this image.

The wrapper mounts this repository's own root and the system temp root
1:1 (host path == container path), same mechanism as
`tools/fpocket/bin/fpocket`'s own wrapper — see that file's docstring for
why this covers every real call site without argument rewriting.

**A gitignore subtlety, recorded so it isn't "fixed" again by accident**:
`p2rank_2.5.1/` is still the fetched, gitignored release directory (the
jar/model payload is never committed) — `.gitignore` here explicitly
un-ignores the directory itself and then just the one file inside it
(`prank`) that is now a tracked wrapper, not vendored payload. Everything
else fetched into `p2rank_2.5.1/` stays ignored.
