# TASK-0285. P2Rank needs only a JVM (README.md: tested against OpenJDK
# 21) -- no compilation, the release is a prebuilt jar. Containerized so
# a JVM never needs to be a host dependency, and the exact release build
# is pinned once instead of re-fetched per machine.
#
# Base image pinned by digest, matching tools/fpocket/Dockerfile and
# tools/evoef2/Dockerfile's own convention.
FROM eclipse-temurin:21-jre-jammy@sha256:eebd356ad7358b7094758e5787a6726f332917cfd56feab6457c56dab895cdbf

WORKDIR /opt
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
    && curl -sL "https://github.com/rdk/p2rank/releases/download/2.5.1/p2rank_2.5.1.tar.gz" -o p2rank.tar.gz \
    && tar xzf p2rank.tar.gz && rm p2rank.tar.gz \
    && apt-get purge -y curl && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

ENTRYPOINT ["/opt/p2rank_2.5.1/prank"]
