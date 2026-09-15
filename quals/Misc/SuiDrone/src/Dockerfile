FROM rust:1.94.1-bookworm AS build
WORKDIR /src
COPY Cargo.toml Cargo.lock ./
COPY crates ./crates
RUN cargo build --release --locked -p suidrone-completion

FROM debian:bookworm-slim
RUN groupadd --gid 10001 suidrone \
 && useradd --uid 10001 --gid 10001 --no-create-home suidrone \
 && mkdir /data \
 && chown 10001:10001 /data
COPY --from=build /src/target/release/suidrone-completion /usr/local/bin/suidrone-completion
USER suidrone
WORKDIR /data
ENV SUIDRONE_BIND=0.0.0.0:8787 SUIDRONE_DB=/data/attempts.sqlite
EXPOSE 8787
CMD ["/usr/local/bin/suidrone-completion"]
