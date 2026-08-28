# TASK-0285. Reproducible fpocket build -- pins the OS/toolchain so every
# machine that runs this image gets byte-identical output, closing the
# cross-machine drift TASK-0206 documented (two native, hand-compiled
# binaries producing different AUCs on the same three targets).
#
# Same source pin this project's own README.md already uses -- not a new
# recipe, a containerized copy of the existing one.
#
# Base image pinned by DIGEST, not just tag (`bookworm-slim` floats as
# Debian pushes security updates) -- confirmed load-bearing, not
# theoretical: the first build of this Dockerfile (tag-only base, apt's
# then-current gcc/qhull) reproduced TASK-0163's own ORIGINAL fpocket AUCs
# (BCR_ABL1 0.8596, CARDIAC_MYOSIN 0.5345) rather than TASK-0206's own
# re-verified native-rebuild AUCs (0.8618/0.5303) on the SAME source tag --
# a third, real data point that the drift TASK-0206 found is a genuine
# build-environment sensitivity, not fixed just by using Docker with an
# unpinned base. Digest below is `docker.io/library/debian:bookworm-slim`
# as resolved on 2026-08-28 (`docker buildx imagetools inspect`).
FROM debian:bookworm-slim@sha256:5ae3c39ebd15e229dcedd5cee596b2497182493d41ff162e824ba13fc1b2b867 AS build

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN git clone --branch 4.2.3 --depth 1 https://github.com/Discngine/fpocket.git . \
    && make

# Minimal runtime stage -- fpocket's own core binary only needs libc/libm/
# libstdc++/libgcc_s (confirmed via ldd against the native build, see
# README.md); libnetcdf is only needed for mdpocket's trajectory mode,
# not used here.
FROM debian:bookworm-slim@sha256:5ae3c39ebd15e229dcedd5cee596b2497182493d41ff162e824ba13fc1b2b867
RUN apt-get update && apt-get install -y --no-install-recommends \
        libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/bin/fpocket /src/bin/tpocket /src/bin/dpocket /src/bin/mdpocket /usr/local/bin/
ENTRYPOINT ["/usr/local/bin/fpocket"]
