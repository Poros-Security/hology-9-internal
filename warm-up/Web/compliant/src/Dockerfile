FROM --platform=linux/amd64 oven/bun:1.3.7

ADD https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb /tmp/chrome.deb

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        /tmp/chrome.deb \
        redis-server \
        tini && \
    rm -f /tmp/chrome.deb && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/compliant

COPY bun.lock package.json ./
RUN bun ci

COPY index.ts start.sh ./
RUN chmod 0555 start.sh

EXPOSE 443

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["./start.sh"]
