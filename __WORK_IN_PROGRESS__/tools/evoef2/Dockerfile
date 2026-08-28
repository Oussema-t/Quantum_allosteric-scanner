# TASK-0285. Reproducible EvoEF2 build -- same pinned recipe README.md
# already documents (clone, apply task0204_single_pass_repack.patch,
# g++ -O3), containerized so the compiler/OS is pinned too.
#
# Base image pinned by DIGEST, not just tag, for the same reason recorded
# in tools/fpocket/Dockerfile (a floating tag lets apt's own current
# gcc/libc silently change the build).
FROM debian:bookworm-slim@sha256:5ae3c39ebd15e229dcedd5cee596b2497182493d41ff162e824ba13fc1b2b867 AS build

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
RUN git clone --depth 1 https://github.com/tommyhuangthu/EvoEF2.git .
COPY task0204_single_pass_repack.patch /tmp/task0204_single_pass_repack.patch
RUN git apply /tmp/task0204_single_pass_repack.patch \
    && g++ -O3 -o EvoEF2 src/*.cpp

# Runtime stage. `library/`/`wread/` are NOT baked in here -- this
# project's own scripts stage the input PDB and expect output inside
# `tools/evoef2/` itself (EvoEF2 resolves both via relative paths from its
# own cwd, see the confirmed argv[0]/cwd quirk in README.md and the
# wrapper script's own docstring) -- the bind-mounted host directory
# already has real `library/`/`wread/` data from the existing native
# build recipe, so the container only needs to supply the binary.
FROM debian:bookworm-slim@sha256:5ae3c39ebd15e229dcedd5cee596b2497182493d41ff162e824ba13fc1b2b867
RUN apt-get update && apt-get install -y --no-install-recommends \
        libstdc++6 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/EvoEF2 /usr/local/bin/EvoEF2
ENTRYPOINT ["/usr/local/bin/EvoEF2"]
