FROM debian:bookworm-slim

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      busybox-static ca-certificates cpio gzip qemu-system-x86 socat coreutils \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /challenge
COPY rootfs/ /challenge/rootfs/
COPY service/ /challenge/service/
COPY assets/ /challenge/assets/
COPY solver/ /challenge/solver/

RUN chmod +x /challenge/rootfs/init /challenge/service/*.sh \
 && mkdir -p /challenge/assets

ENV PORT=9999 \
    SESSION_TIMEOUT=300 \
    QEMU_MEM=128M \
    USE_KVM=0

EXPOSE 9999/tcp
ENTRYPOINT ["/challenge/service/entrypoint.sh"]
