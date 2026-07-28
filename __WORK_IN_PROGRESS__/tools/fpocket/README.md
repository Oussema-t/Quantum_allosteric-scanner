# fpocket (TASK-0163 external dependency)

Built from source, no root/`sudo` needed — `bin/` is gitignored (upstream's own
convention), rebuild locally with:

```bash
git clone --branch 4.2.3 --depth 1 https://github.com/Discngine/fpocket.git src
cd src
make
cp bin/{fpocket,tpocket,dpocket,mdpocket} ../bin/
```

The core `fpocket` binary only needs `libm`/`libstdc++`/`libc`/`libgcc_s`
(confirmed via `ldd`) — the project's own Docker recipe lists `libnetcdf-dev`,
but that's only needed for `mdpocket`'s trajectory-analysis mode, not the
core pocket-detection binary this project's scoring script calls.

Used by `scripts/task0163_external_baseline_scoring.py`
(`FPOCKET_BIN = tools/fpocket/bin/fpocket`).
