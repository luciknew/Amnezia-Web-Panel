# syntax=docker/dockerfile:1
# Builds the Telegram WEB proxy relay (tproxy-server) from a pinned commit.
# Upstream ships no release artifacts, so we clone and build.

ARG TPROXY_REPOSITORY=https://github.com/telegramdesktop/tproxy-server.git
# Pinned: 2026-09-03 "Fix websocket-lanes ddos problem." (includes the
# 2026-09-03 active-probing hardening: signed tokens, no reserved-path oracle).
ARG TPROXY_REF=f7a6acc4d536a787d442fd7df3ba4ebfd728f406

FROM golang:1.24-bookworm AS build
ARG TPROXY_REPOSITORY
ARG TPROXY_REF
WORKDIR /src
RUN set -eux; \
    git clone --filter=blob:none "${TPROXY_REPOSITORY}" .; \
    git checkout --detach "${TPROXY_REF}"; \
    go test ./...; \
    CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/tproxy-server ./cmd/tproxy-server

FROM debian:12-slim
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates curl; \
    rm -rf /var/lib/apt/lists/*
COPY --from=build /out/tproxy-server /usr/local/bin/tproxy-server
WORKDIR /etc/tproxy
ENTRYPOINT ["/usr/local/bin/tproxy-server"]
CMD ["-config", "/etc/tproxy/config.json"]
