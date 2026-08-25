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
