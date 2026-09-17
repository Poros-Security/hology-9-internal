FROM ubuntu:22.04

RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    --no-install-recommends xinetd ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /usr/sbin/nologin ctf

WORKDIR /home/ctf

COPY d8 /home/ctf/d8
COPY snapshot_blob.bin /home/ctf/snapshot_blob.bin
COPY wrapper.js /home/ctf/wrapper.js
COPY runner.sh /home/ctf/runner.sh
COPY xinetd.conf /etc/xinetd.d/suicar
COPY start.sh /usr/local/bin/suicar-start.sh

RUN chmod 0555 /home/ctf/d8 /home/ctf/runner.sh \
    /usr/local/bin/suicar-start.sh \
    && chmod 0444 /home/ctf/snapshot_blob.bin \
    && chown -R root:root /home/ctf \
    && chmod 0755 /home/ctf

CMD ["/usr/local/bin/suicar-start.sh"]
